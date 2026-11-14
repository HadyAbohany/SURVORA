import asyncio
import json
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.events import EventPolicy
from app.schemas import EventRequest, ChatRequest
from app.gemini import GeminiGateway, GeminiUnavailable
from app.retrieval import Retriever
from app.assistant import answer

client=TestClient(app)

def ev(id, type='OXYGEN_LOW', priority='critical'):
    return EventRequest(event_id=id,event_type=type,priority=priority,mission_id='M02_OXYGEN_MYSTERY')

def test_health_text_only():
    r=client.get('/health'); assert r.status_code==200
    data=r.json()
    assert data['tts_enabled'] is False
    assert '/tts' not in client.get('/openapi.json').json()['paths']
    assert '/audio/{filename}' not in client.get('/openapi.json').json()['paths']

def test_urgent_instant_predefined_text():
    result=client.post('/events',json=ev('test-urgent').model_dump()).json()
    assert result['response_origin']=='predefined'
    assert result['response_mode']=='TEXT_ONLY'
    assert result['audio_ref'] is None
    assert result['followup_hint_recommended'] is False

def test_urgent_cooldown_bypass():
    p=EventPolicy(clock=lambda:100)
    assert p.handle(ev('a')).should_speak
    assert p.handle(ev('b')).should_speak
    assert not p.handle(ev('b')).should_speak

def test_optional_event_cooldown():
    p=EventPolicy(clock=lambda:100)
    assert p.handle(ev('a','MISSION_STARTED','normal')).should_speak
    assert not p.handle(ev('b','MISSION_STARTED','normal')).should_speak

def test_low_priority_noise_suppression():
    p=EventPolicy()
    assert p.handle(ev('x','MISSION_STAGE_COMPLETED','low')).response_mode=='SILENT'

def test_missing_event_silent():
    assert not client.post('/events',json=ev('z','MADE_UP').model_dump()).json()['should_speak']

def test_bm25_fast():
    retriever=Retriever(enable_semantic=False)
    assert not retriever.semantic_enabled
    assert any(c.evidence.source_id=='MOXIE' for c in retriever.search('MOXIE Mars oxygen carbon dioxide',k=10))

def test_gemini_mock_short():
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(200,json={'candidates':[{'content':{'parts':[{'text':'Check the oxygen plant power.'}]}}]})
    gw=GeminiGateway(api_keys=['test'],transport=httpx.MockTransport(handler))
    assert asyncio.run(gw.text('system','question'))=='Check the oxygen plant power.'
    assert len(calls)==1
    assert calls[0].headers['x-goog-api-key']=='test'

def test_no_serial_retries_default(monkeypatch):
    monkeypatch.delenv('NOVA_GEMINI_MAX_ATTEMPTS',raising=False)
    calls=[]
    def handler(request):
        calls.append(request)
        return httpx.Response(429,json={})
    gw=GeminiGateway(api_keys=['key1','key2'],transport=httpx.MockTransport(handler))
    with pytest.raises(GeminiUnavailable):
        asyncio.run(gw.text('system','question'))
    assert len(calls)==1
    assert gw.cursor==1  # rotate to next slot for a subsequent request

def test_answer_rag_model_only_on_chat():
    class Fake:
        def __init__(self):self.calls=0
        async def text(self,system,prompt):
            self.calls+=1
            return json.dumps({'message': 'Check power allocation on the oxygen plant.',
                               'reference_ids': [], 'suggested_action': None})
    gw=Fake()
    req=ChatRequest(question='Why is oxygen decreasing?',game_state={'oxygen_generator_status':'underpowered'})
    reply=asyncio.run(answer(req,gw))
    assert reply.response_origin=='gemini_rag' and gw.calls==1
    assert len(reply.sources)<=3

def test_unity_not_auto_calling_llm():
    from app.config import ROOT
    script=(ROOT/'unity'/'NovaBridge.cs').read_text()
    block=script.split('public void PublishEvent(')[1].split('static bool IsUrgent')[0]
    assert 'PostChat' not in block and 'Ask(' not in block and 'PostEvent' not in block
    assert 'AudioSource' not in script and 'DynamicAudio' not in script
