from datetime import datetime, timezone
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.gemini import GeminiGateway
from app.knowledge import MarkdownSource
from app.observations import DonkiSource, RadLabSource
from app.retrieval import ROOT, Retriever, make_chunks

FIXTURES = Path(__file__).with_name('fixtures')
RETRIEVED = datetime(2026, 11, 14, tzinfo=timezone.utc)

CASES = [
    ('hydroponics greenhouse roots', 'M06_GREENHOUSE_CHALLENGE', 'CSA_INTERPLANETARY_FARMING'),
    ('الزراعة المائية جذور النبات', 'M06_GREENHOUSE_CHALLENGE', 'CSA_INTERPLANETARY_FARMING'),
    ('الحماية من الإشعاع الدرع', 'M07_SOLAR_ALERT', 'NASA_SRAG_SHIELDING'),
    ('MOLA elevation and slope on Mars', 'E01_FIRST_FOOTPRINTS', 'NASA_MARSTREK_ROVER_ROUTE'),
    ('microgravity muscles and bones exercise', 'ASTRONAUT_HEALTH', 'CSA_PHYSICAL_ACTIVITY'),
    ('station brine processor urine', 'M05_THIRSTY_COLONY', 'NASA_ISS_WATER_MILESTONE'),
    ('DosTel absorbed dose rate ISS', 'M07_SOLAR_ALERT', 'NASA_RADLAB_SCOPE'),
    ('DONKI flare CME SEP timestamp', 'M07_SOLAR_ALERT', 'NASA_DONKI_CATALOG'),
    ('OSD-104 mouse soleus muscle', 'ASTRONAUT_HEALTH', 'NASA_OSD104'),
    ('ISS electricity solar arrays station life support', 'M02_OXYGEN_MYSTERY', 'NASA_ISS_SYSTEMS'),
]


@pytest.mark.parametrize(('query', 'mission', 'source'), CASES)
def test_mission_retrieval(query, mission, source):
    retriever = Retriever(enable_semantic=False)
    hits = retriever.search(query, k=3, mission_id=mission)
    evidence = next(chunk.evidence for chunk in hits if chunk.evidence.source_id == source)
    assert evidence.source_name and evidence.url.startswith('https://')
    assert 'SURVORA paraphrase' in evidence.provenance
    other = retriever.search(query, k=5, mission_id='UNRELATED')
    assert source not in {chunk.evidence.source_id for chunk in other}


def test_ingestion_deduplicates_new_corpus():
    source = MarkdownSource(ROOT / 'data' / 'nasa', 'nasa')
    single = make_chunks([source])
    assert [c.id for c in single] == [c.id for c in make_chunks([source, source])]


@pytest.mark.parametrize('kind', ['FLR', 'CME', 'SEP'])
def test_donki_fixture(kind):
    rows = json.loads((FIXTURES / f'donki_{kind.lower()}.json').read_text())
    record, = DonkiSource.parse(kind, rows * 2, RETRIEVED)
    assert record.observed_at < record.retrieved_at
    assert record.source_url == rows[0]['link']


def test_radlab_fixture_and_missing_value():
    payload = json.loads((FIXTURES / 'radlab_iss.json').read_text())
    records = RadLabSource.parse(payload, RETRIEVED)
    assert len(records) == 2
    assert records[0].unit == 'μGy/hour' and records[0].spacecraft == 'ISS'
    assert records[0].absorbed_dose_rate == payload['data'][0][2]
    payload['data'][0][2] = None
    assert len(RadLabSource.parse(payload, RETRIEVED)) == 1
    payload['data'][1][4] = 'Mars surface'
    with pytest.raises(ValueError, match='scope'):
        RadLabSource.parse(payload, RETRIEVED)


def test_csa_chat_attribution_and_event_compatibility(monkeypatch):
    def model(request):
        body = json.loads(request.content)
        prompt = json.loads(body['contents'][0]['parts'][0]['text'])
        ref = next(r for r in prompt['references'] if r['source_name'] == 'Canadian Space Agency')
        assert 'جذور' in ref['excerpt']
        answer = json.dumps({'message': 'الميه بتوصل الغذاء للجذور من غير تربة.',
                             'reference_ids': [ref['reference_id']], 'suggested_action': None})
        return httpx.Response(200, json={'candidates': [{'content': {'parts': [{'text': answer}]}}]})

    monkeypatch.setattr(main, 'gateway', GeminiGateway(['test'], httpx.MockTransport(model)))
    client = TestClient(main.app)
    result = client.post('/chat', json={'question': 'الزراعة المائية جذور النبات',
                                      'mission_id': 'M06_GREENHOUSE_CHALLENGE', 'language': 'ar'})
    assert result.status_code == 200
    citation, = result.json()['sources']
    assert citation['source_id'] == 'CSA_INTERPLANETARY_FARMING'
    assert citation['source_modified_date'] == '2019-09-26'
    assert citation['source_name'] == 'Canadian Space Agency'
    event = client.post('/events', json={'event_type': 'FOOD_SHORTAGE', 'event_id': 'csa-test',
                                         'mission_id': 'M06_GREENHOUSE_CHALLENGE'})
    assert event.json()['should_speak']
