"""Source adapters for static local records and separately timestamped observations."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Protocol

from .schemas import Evidence


@dataclass(frozen=True)
class Document:
    evidence: Evidence
    text: str


class SourceAdapter(Protocol):
    def load(self) -> Iterable[Document]: ...


@dataclass(frozen=True)
class Observation:
    record_id: str
    observed_at: datetime
    retrieved_at: datetime
    source_url: str
    description: str

    def __post_init__(self):
        if any(dt.utcoffset() is None for dt in (self.observed_at, self.retrieved_at)):
            raise ValueError('Observation timestamps require a timezone')
        if self.observed_at > self.retrieved_at:
            raise ValueError('Observation cannot follow retrieval')


class MarkdownSource:
    def __init__(self, directory: Path, layer):
        self.directory = directory
        self.layer = layer

    def load(self):
        for path in sorted(self.directory.glob('*.md')):
            try:
                raw = path.read_text(encoding='utf-8')
            except (OSError, UnicodeError):
                continue
            info, text = frontmatter(raw)
            if not text.strip():
                continue
            provenance = (info.get('provenance', info.get('content_type', 'curated_educational_summary'))
                          if self.layer == 'nasa' else 'SURVORA_proposed_game_design_not_implemented')
            yield Document(Evidence(
                source_id=info.get('source_id', path.stem), title=info.get('title', path.stem),
                url=info.get('source_url', ''), provenance=provenance, layer=self.layer,
                mission_ids=tuple(info.get('mission_ids', '').replace(',', ' ').split()),
                document_version=info.get('document_version'), publication_date=info.get('publication_date'),
                source_name=info.get('source_name', 'NASA') if self.layer == 'nasa' else None,
                source_modified_date=info.get('source_modified_date'),
            ), text)


def frontmatter(text):
    if not text.startswith('---\n'):
        return {}, text
    parts = text.split('---\n', 2)
    if len(parts) < 3:
        return {}, text
    info = {}
    for line in parts[1].splitlines():
        key, sep, value = line.partition(':')
        if sep:
            info[key.strip()] = value.strip()
    return info, parts[2]
