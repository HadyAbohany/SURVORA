"""Gemini REST client with bounded project-aware key failover; no quota bypass guarantees."""
from __future__ import annotations
import asyncio
import os
import httpx
from .config import keys, TEXT_MODEL
from .schemas import ModelDialogue

class GeminiUnavailable(Exception): pass

class GeminiGateway:
    def __init__(self, api_keys=None, transport=None):
        self.api_keys = keys() if api_keys is None else list(dict.fromkeys(api_keys))
        self.transport=transport
        self.cursor=0
        self._lock=asyncio.Lock()

    async def _generate(self, model: str, payload: dict):
        if not self.api_keys:
            raise GeminiUnavailable('No GEMINI_API_KEY configured')
        # Finite attempts only; do not retry endlessly or spin through shared-project quotas.
        async with self._lock:
            start=self.cursor
        retryable={429,500,502,503,504}
        failures=[]
        for step in range(min(len(self.api_keys),max(1,int(os.getenv('NOVA_GEMINI_MAX_ATTEMPTS','1'))))):
            index=(start+step)%len(self.api_keys)
            key=self.api_keys[index]
            url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
            try:
                async with httpx.AsyncClient(timeout=float(os.getenv('NOVA_GEMINI_TIMEOUT_SECONDS','5')), transport=self.transport) as client:
                    resp=await client.post(url,json=payload,headers={'x-goog-api-key':key})
                if resp.status_code == 200:
                    async with self._lock:
                        self.cursor=index
                    return resp.json()
                if resp.status_code in (400,401,403,404):
                    failures.append(f'key slot {index+1}: HTTP {resp.status_code}')
                    # 403 may be a permissions/model error; changing keys is unlikely to help.
                    if resp.status_code in (400,404): break
                    continue
                if resp.status_code not in retryable:
                    failures.append(f'HTTP {resp.status_code}')
                    break
                failures.append(f'key slot {index+1}: HTTP {resp.status_code}')
                # Rotate to the next key for the NEXT request; no slow retries on this request.
                async with self._lock:
                    self.cursor=(index+1)%len(self.api_keys)
                # Google applies quota per project. Failover may not help on same project.
            except (httpx.TimeoutException,httpx.TransportError) as ex:
                failures.append(type(ex).__name__)
        raise GeminiUnavailable('; '.join(failures) or 'Gemini unavailable')

    async def text(self, system: str, prompt: str):
        # Leave room for Arabic tokenization and the JSON reference/action fields.
        output_budget = max(512, int(os.getenv('NOVA_MAX_OUTPUT_TOKENS', '512')))
        payload = {
            'systemInstruction':{'parts':[{'text':system}]},
            'contents':[{'role':'user','parts':[{'text':prompt}]}],
            'generationConfig': {
                'responseMimeType': 'application/json',
                'responseJsonSchema': ModelDialogue.model_json_schema(),
                'temperature': 0.25,
                'maxOutputTokens': output_budget,
            }
        }
        try:
            raw = await asyncio.wait_for(
                self._generate(TEXT_MODEL, payload),
                timeout=float(os.getenv('NOVA_GEMINI_TIMEOUT_SECONDS', '5')),
            )
        except (TimeoutError, ValueError) as ex:
            raise GeminiUnavailable('Gemini request failed or returned invalid JSON') from ex
        try:
            return ''.join(p.get('text','') for p in raw['candidates'][0]['content']['parts'] if not p.get('thought')).strip()
        except (KeyError,IndexError,TypeError,AttributeError) as ex:
            raise GeminiUnavailable('Gemini returned no usable text') from ex

