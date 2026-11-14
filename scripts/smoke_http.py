"""Run against an isolated NOVA server with no Gemini key configured."""
from concurrent.futures import ThreadPoolExecutor
import os
from statistics import median, quantiles
from time import perf_counter
from uuid import uuid4

import httpx

BASE = os.getenv('NOVA_BASE_URL', 'http://127.0.0.1:8000')
TOKEN = os.getenv('NOVA_CLIENT_TOKEN', '')
STATE = {'oxygen': 20, 'power': 15, 'oxygen_generator_status': 'underpowered'}
CHAT = {'question': 'Why is my oxygen decreasing?', 'hint_level': 1,
        'mission_id': 'M02_OXYGEN_MYSTERY', 'game_state': STATE,
        'allowed_actions': ['Inspect oxygen plant']}
SESSION = uuid4().hex


def request(client, route, payload):
    start = perf_counter()
    result = client.post(route, json=payload)
    result.raise_for_status()
    return result.json(), (perf_counter() - start) * 1000


def report(label, samples):
    p95 = quantiles(samples, n=20)[18]
    print(f'{label}: n={len(samples)} median={median(samples):.2f}ms p95={p95:.2f}ms')


def main():
    with httpx.Client(base_url=BASE, headers={'X-Nova-Token': TOKEN}, timeout=10) as client:
        health = client.get('/health')
        health.raise_for_status()
        info = health.json()
        assert info['status'] == 'ok' and not info['llm_enabled'], info
        print(info)
        event = {'event_id': 'oxygen-1', 'event_type': 'OXYGEN_LOW', 'state_revision': 2,
                 'session_id': SESSION, 'game_state': STATE}
        first, first_ms = request(client, '/events', event)
        assert first['should_speak'] and first['priority'] == 'high'
        assert request(client, '/events', event)[0]['response_origin'] == 'suppressed_duplicate'
        stale = {**event, 'event_id': 'stale', 'state_revision': 1}
        assert request(client, '/events', stale)[0]['response_origin'] == 'suppressed_stale_revision'
        reply, chat_ms = request(client, '/chat', CHAT)
        assert reply['response_origin'] == 'deterministic_fallback' and reply['answer'] == reply['voice_text']
        arabic, _ = request(client, '/chat', {**CHAT, 'language': 'ar', 'question': 'ليه الأكسجين بيقل؟'})
        assert arabic['language'] == 'ar' and 'الأكسجين' in arabic['answer']
        print(f'First event {first_ms:.2f}ms, first chat {chat_ms:.2f}ms')
        print('Example event:', first['text'])
        print('Example chat:', reply['answer'])
        report('Warm events', [request(client, '/events', {**event, 'event_id': str(i)})[1] for i in range(50)])
        report('Warm offline chat', [request(client, '/chat', CHAT)[1] for _ in range(50)])
        with ThreadPoolExecutor(max_workers=8) as pool:
            report('Offline chat, 8 concurrent', list(pool.map(lambda _: request(client, '/chat', CHAT)[1], range(80))))


if __name__ == '__main__':
    main()
