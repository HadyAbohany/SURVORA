"""Separate NASA and game corpora; reproducible BM25 + optional Chroma semantic retrieval."""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import textwrap
import hashlib
import logging
import math
import re
from collections import Counter
from .config import ROOT, EMBED_MODEL, env_bool
from .schemas import Evidence
from .knowledge import MarkdownSource

logger = logging.getLogger(__name__)

WORD_RE = re.compile(r'[a-zA-Z0-9_]+|[\u0600-\u06FF]+')
STOP_WORDS = set('a an are as at be by can do does for from how i in is it me my of on or should that the their there this to was we what when where which who why will with you your'.split())
ALIASES = {
    'o2': 'oxygen', 'أكسجين': 'oxygen', 'الاكسجين': 'oxygen', 'الأكسجين': 'oxygen',
    'اكسجين': 'oxygen', 'الماء': 'water', 'المياه': 'water', 'المريخ': 'mars',
    'مريخ': 'mars', 'شمسي': 'solar', 'الشمس': 'sun sunlight', 'الشمسية': 'solar',
    'الطاقة': 'power', 'كهرباء': 'power', 'كهربا': 'power', 'الألواح': 'panels',
    'عاصفة': 'storm', 'العاصفة': 'storm', 'العواصف': 'storm', 'الترابية': 'dust',
    'التراب': 'dust', 'بطارية': 'battery', 'صخر': 'rock',
}

def tokenize(s):
    base = WORD_RE.findall(s.lower())
    return [term for token in base if token not in STOP_WORDS
            for term in ALIASES.get(token, token).split()]

@dataclass
class Chunk:
    id: str
    text: str
    evidence: Evidence


def split_chunks(text: str, max_chars=1000):
    # Preserve headings; never cut scientific text mid-word.
    sections = re.split(r'(?=^#{1,4} )', text, flags=re.M)
    for section in sections:
        section=section.strip()
        if not section: continue
        paragraphs = re.split(r'\n\s*\n', section)
        buffer=''
        for para in paragraphs:
            for line in textwrap.wrap(para, max_chars, replace_whitespace=False):
                if len(buffer)+len(line)+2 > max_chars and buffer:
                    yield buffer.strip()
                    buffer=''
                buffer += ('\n\n' if buffer else '')+line
        if buffer: yield buffer.strip()


def make_chunks(adapters=None):
    if adapters is None:
        adapters = [MarkdownSource(ROOT / 'data' / layer, layer) for layer in ('nasa', 'game')]
    chunks = {}
    seen_documents = set()
    for adapter in adapters:
        for document in adapter.load():
            evidence = document.evidence
            identity = (evidence.layer, ' '.join(document.text.split()))
            if identity in seen_documents:
                continue
            seen_documents.add(identity)
            for part in split_chunks(document.text):
                if len(part) < 40:
                    continue
                raw = f'{evidence.layer}:{evidence.source_id}:{part}'
                cid = hashlib.sha256(raw.encode()).hexdigest()[:20]
                chunks[cid] = Chunk(cid, part, evidence.model_copy(update={'excerpt': part}))
    return list(chunks.values())


class Retriever:
    def __init__(self, chunks=None, enable_semantic=None):
        self.chunks = chunks if chunks is not None else make_chunks()
        self.by_id = {c.id:c for c in self.chunks}
        self.tokens = [tokenize(c.text) for c in self.chunks]
        self.term_counts = [Counter(tokens) for tokens in self.tokens]
        self.df=Counter()
        for ts in self.tokens: self.df.update(set(ts))
        self.avglen=sum(map(len,self.tokens))/max(len(self.tokens),1)
        self.semantic_enabled = False
        self.collection = None
        if enable_semantic is None: enable_semantic=env_bool('NOVA_ENABLE_SEMANTIC', False)
        if enable_semantic:
            self._init_semantic()

    def _init_semantic(self):
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            if not self.chunks:
                return
            self.encoder = SentenceTransformer(EMBED_MODEL)
            fingerprint = hashlib.sha256(
                (EMBED_MODEL + ':' + ':'.join(c.id for c in self.chunks)).encode()
            ).hexdigest()[:24]
            store=chromadb.PersistentClient(path=str(ROOT/'cache'/'chromadb'))
            self.collection=store.get_or_create_collection(f'nova_v3_{fingerprint}', metadata={'hnsw:space':'cosine'})
            present=set(self.collection.get(include=[])['ids'])
            missing=[c for c in self.chunks if c.id not in present]
            for start in range(0,len(missing),64):
                batch=missing[start:start+64]
                vectors=self.encoder.encode([c.text for c in batch],normalize_embeddings=True).tolist()
                self.collection.upsert(ids=[c.id for c in batch],documents=[c.text for c in batch],embeddings=vectors,metadatas=[{'layer':c.evidence.layer} for c in batch])
            self.semantic_enabled=True
        except Exception as ex:
            # App remains operational without heavyweight model packages/downloads.
            logger.warning('Semantic index unavailable (%s). Using BM25.', type(ex).__name__)

    def _bm25(self, query):
        qt=set(tokenize(query))
        N=len(self.chunks)
        scores=[]
        for c, ts, tf in zip(self.chunks, self.tokens, self.term_counts):
            score = 0.0
            for term in qt:
                n=self.df[term]
                idf=max(0,math.log(1+(N-n+0.5)/(n+0.5)))
                freq=tf[term]
                if freq:
                    score+=idf*(freq*2.2)/(freq+1.2*(0.25+0.75*len(ts)/max(self.avglen,1)))
            if score>0: scores.append((c.id,score))
        return [cid for cid,_ in sorted(scores,key=lambda v:v[1],reverse=True)]

    def search(self, query: str, k=5, layers=('nasa', 'game'), mission_id=None):
        def eligible(cid):
            evidence = self.by_id[cid].evidence
            return evidence.layer in layers and (
                not evidence.mission_ids or mission_id in evidence.mission_ids
            )

        lexical = [cid for cid in self._bm25(query) if eligible(cid)][:40]
        candidates = {cid: 1 / (61 + rank) for rank, cid in enumerate(lexical)}
        if self.semantic_enabled and tokenize(query):
            try:
                vec = self.encoder.encode([query], normalize_embeddings=True).tolist()
                results = self.collection.query(
                    query_embeddings=vec, n_results=min(40, len(self.chunks)),
                    include=['distances'],
                )
                for rank, (cid, distance) in enumerate(zip(results['ids'][0], results['distances'][0])):
                    if distance <= 0.55 and cid in self.by_id and eligible(cid):
                        candidates[cid] = candidates.get(cid, 0) + 1 / (61 + rank)
            except Exception as ex:
                logger.warning('Semantic query unavailable (%s). Using BM25.', type(ex).__name__)
        ranked = sorted(candidates, key=candidates.get, reverse=True)
        selected = ranked[:k]
        # Give scientific evidence room alongside verbose game-design documents.
        if k > 1 and layers == ('nasa', 'game') and not any(
            self.by_id[cid].evidence.layer == 'nasa' for cid in selected
        ):
            science = next((cid for cid in ranked if self.by_id[cid].evidence.layer == 'nasa'), None)
            if science is not None:
                selected[-1:] = [science]
        return [self.by_id[cid] for cid in selected]


@lru_cache(maxsize=1)
def get_retriever():
    return Retriever()
