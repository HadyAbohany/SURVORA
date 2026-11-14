"""NOVA game companion: English-first, offline-first alerts, Gemini and hybrid RAG."""
from __future__ import annotations
import asyncio
import hmac
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from . import config
from .assistant import answer
from .events import EventPolicy
from .gemini import GeminiGateway
from .limits import RequestLimit
from .retrieval import get_retriever
from .schemas import ChatRequest, ChatReply, EventRequest, EventReply

@asynccontextmanager
async def lifespan(app):
    await asyncio.to_thread(get_retriever)
    yield


app = FastAPI(title='NOVA - SURVORA Mission Companion', version='3.1.0', lifespan=lifespan)
app.add_middleware(RequestLimit)


@app.exception_handler(RequestValidationError)
async def invalid_request(request, error):
    return JSONResponse({'detail': [
        {key: issue[key] for key in ('loc', 'msg', 'type')} for issue in error.errors()
    ]}, status_code=422)

origins=[s.strip() for s in os.getenv('NOVA_CORS_ORIGINS','').split(',') if s.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['GET','POST'],allow_headers=['Content-Type','X-Nova-Token'])
policy=EventPolicy()
gateway=GeminiGateway()

async def auth(x_nova_token: str | None=Header(None)):
    required=os.getenv('NOVA_CLIENT_TOKEN','')
    if required and not hmac.compare_digest((x_nova_token or '').encode(), required.encode()):
        raise HTTPException(401,'Invalid NOVA client token')

@app.get('/health')
async def health():
    r=await asyncio.to_thread(get_retriever)
    return {'status':'ok' if r.chunks else 'degraded','version':app.version,'knowledge_chunks':len(r.chunks),'semantic_enabled':r.semantic_enabled,'retrieval_mode':'hybrid_rrf' if r.semantic_enabled else 'bm25_only','configured_keys':len(gateway.api_keys),'llm_enabled':bool(gateway.api_keys),'tts_enabled':False,'text_model':config.TEXT_MODEL}

@app.post('/events',response_model=EventReply,dependencies=[Depends(auth)])
async def events(request:EventRequest):
    # No network calls or TTS blocking. Unity must also show local alert immediately.
    reply=policy.handle(request)
    return reply

@app.post('/chat',response_model=ChatReply,dependencies=[Depends(auth)])
async def chat(request:ChatRequest):
    return await answer(request,gateway)

@app.post('/hint',response_model=ChatReply,dependencies=[Depends(auth)])
async def hint(request:ChatRequest):
    return await answer(request, gateway, 'hint')

@app.post('/mission/briefing',response_model=ChatReply,dependencies=[Depends(auth)])
async def mission_briefing(request:ChatRequest):
    return await answer(request, gateway, 'briefing')

@app.post('/mission/debrief',response_model=ChatReply,dependencies=[Depends(auth)])
async def mission_debrief(request:ChatRequest):
    return await answer(request, gateway, 'debrief')

@app.post('/sample/explain',response_model=ChatReply,dependencies=[Depends(auth)])
async def sample_explain(request:ChatRequest):
    return await answer(request, gateway, 'sample')

# Voice endpoints intentionally removed: fast text-only game companion.
