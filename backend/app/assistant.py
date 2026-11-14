"""Assemble bounded context and validate dialogue before returning it to the game."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from pydantic import ValidationError

from .gemini import GeminiUnavailable
from .retrieval import get_retriever
from .schemas import ChatRequest, ChatReply, ModelDialogue

SYSTEM = Path(__file__).with_name('system_prompt.md').read_text(encoding='utf-8')
PRIVATE = re.compile(r'[\w.+-]+@[\w.-]+\.\w+|(?:\+?\d[ ().-]*){7,}\d|https?://\S+', re.I)
ROUTE_INTENT = {
    'hint': 'Give a hint at the requested level.',
    'briefing': 'Introduce the current mission briefly without revealing solutions.',
    'debrief': 'Explain one lesson without claiming unseen success.',
    'sample': 'Explain the sample using supplied observations and references.',
}
STATE_FIELDS = {
    'oxygen', 'power', 'water', 'food', 'oxygen_generator_status', 'oxygen_trend',
    'research_lab_on', 'rover_battery', 'active_emergencies', 'current_objective',
    'current_stage', 'selected_sample_id',
}


def safe_text(text: str) -> str:
    return PRIVATE.sub('[redacted]', text)


def voice_text(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)|\[[^\]]+\]', lambda m: m[1] or '', text)
    return ' '.join(re.sub(r'[`*_#<>]', '', text).split())


def fallback(req: ChatRequest, status: str) -> ChatReply:
    state = req.game_state
    arabic = req.language == 'ar'
    oxygen = re.search(r'\boxygen\b|\bo2\b|[أا]كسجين', req.question, re.I)
    if oxygen and (state.oxygen_generator_status or '').lower() in ('underpowered', 'low_power'):
        lines = [
            ('Look at the oxygen plant’s power reading.', 'بص على قراءة الكهرباء في محطة الأكسجين.'),
            ('The oxygen plant has too little power. Where else is power going?', 'الكهرباء اللي واصلة لمحطة الأكسجين قليلة. يا ترى الكهربا رايحة فين كمان؟'),
            ('In this mission, the plant needs power to make oxygen. What else is using electricity?', 'في المهمة دي، المحطة محتاجة كهربا عشان تنتج أكسجين. إيه كمان بيستخدم الكهربا؟'),
        ]
        message = lines[min(req.hint_level, 2)][arabic]
    else:
        message = ('I’m missing a clue. What does your mission panel show?',
                   'ناقصني دليل. لوحة المهمة بتقول إيه؟')[arabic]
    return ChatReply(answer=message, voice_text=message, language=req.language,
                     grounding_status=status, response_origin='deterministic_fallback',
                     relevant_game_context=state.model_dump(exclude_none=True))


async def answer(req: ChatRequest, gateway, intent: str = 'question') -> ChatReply:
    question = safe_text(req.question)
    state = req.game_state.model_dump(exclude_none=True)
    context = {key: safe_text(value) if isinstance(value, str) else value
               for key, value in state.items() if key in STATE_FIELDS}
    context['active_emergencies'] = [safe_text(item) for item in req.game_state.active_emergencies]
    if not getattr(gateway, 'api_keys', True):
        return fallback(req, 'llm_unavailable')
    query = question
    if intent == 'briefing' or intent == 'debrief':
        query += ' ' + (req.mission_id or '').replace('_', ' ')
    try:
        chunks = await asyncio.wait_for(asyncio.to_thread(
            lambda: get_retriever().search(query, k=3, mission_id=req.mission_id)), timeout=1.0)
    except TimeoutError:
        return fallback(req, 'retrieval_timeout')
    except (OSError, RuntimeError):
        return fallback(req, 'retrieval_unavailable')

    evidence = {ch.id: ch.evidence.model_copy(update={'excerpt': ch.text}) for ch in chunks}
    actions = [label for label in req.allowed_actions if safe_text(label) == label]
    prompt = json.dumps({
        'language': req.language, 'age_mode': req.age_mode, 'mission_id': req.mission_id,
        'hint_level': req.hint_level, 'question': question, 'game_state': context,
        'allowed_actions': actions,
        'references': [{'reference_id': key, 'layer': ev.layer, 'source_name': ev.source_name, 'excerpt': ev.excerpt}
                       for key, ev in evidence.items()],
    }, ensure_ascii=False)
    system = SYSTEM + ('\nRequest intent: ' + ROUTE_INTENT[intent] if intent in ROUTE_INTENT else '')
    try:
        raw = await gateway.text(system, prompt)
        dialogue = ModelDialogue.model_validate_json(raw)
    except GeminiUnavailable:
        return fallback(req, 'llm_unavailable')
    except ValidationError:
        return fallback(req, 'invalid_model_output')

    if any(ref not in evidence for ref in dialogue.reference_ids):
        return fallback(req, 'invalid_model_references')
    action = dialogue.suggested_action
    if action is not None and (req.hint_level != 3 or action not in actions):
        return fallback(req, 'invalid_model_action')
    message = voice_text(safe_text(dialogue.message))
    if not message:
        return fallback(req, 'invalid_model_output')
    sources = [evidence[ref] for ref in dict.fromkeys(dialogue.reference_ids)]
    status = 'retrieved_references_reported' if sources else 'no_references_reported'
    return ChatReply(answer=message, voice_text=message, language=req.language, sources=sources,
                     suggested_action=action, grounding_status=status, response_origin='gemini_rag',
                     relevant_game_context=state)
