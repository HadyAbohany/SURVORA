# NOVA companion audit

**PARTIALLY READY** for a local hackathon integration. HTTP offline behavior and the mocked model path passed. Release to children requires a real provider evaluation, deployment controls and verification in the actual game.

## Architecture

The engine owns resources, missions, event thresholds and actions. Chat sends a read-only snapshot. FastAPI validates input, filters the provider context, retrieves up to three game/science references and sends context to Gemini separately from the stable instructions in `app/system_prompt.md`. The backend validates the returned JSON, reference IDs and exact action labels before sending dialogue. Referenced excerpts are attributed to curated material. Checking reference membership does not establish that the model's claims follow from the cited text.

Engine events take an independent deterministic path. Unity renders immediate local alerts, while external clients can call `/events`. No event invokes the provider. The client controls UI priority and decides whether to use TTS.

## Findings and changes

| Severity | Finding | Implemented change |
| --- | --- | --- |
| High | Chat was gated on keyword matches even when the engine snapshot could answer the question. | Model path accepts empty retrieval and relies on explicit evidence and snapshot rules. |
| High | Structured actions and citation claims were unchecked. | Require JSON output with allowlisted reference IDs and an exact permitted action at hint level 3. Fallback on invalid output. Model-generated prose still needs safety and accuracy evaluation. |
| High | Chat lacked a total Gemini deadline, malformed responses could surface as errors, and synchronous retrieval blocked the request loop. | Enforce a provider deadline, normalize provider errors and move retrieval off the event loop with a reply timeout. A timed-out thread may finish in the background. |
| High | Stale events and stale Unity replies could replace current dialogue. The event cooldown dictionary grew unbounded. | Bound event bookkeeping, reject stale positive revisions and optional timestamps, and guard Unity's subtitle against stale asks and nonurgent interruptions. Unity Editor remains untested. |
| High | Large input and arbitrary state text could be forwarded to the provider, and validation errors echoed input. | Cap POST bodies, validate known fields, redact recognizable contact patterns, exclude arbitrary state maps and omit input values from validation errors. Prompt rules and pattern redaction do not remove all personal information or guarantee safety. |
| Medium | Common words and unconditional state terms weakened BM25 relevance. Chroma reused one collection across model and corpus changes. | Use question-centered BM25 with stop-word filtering, Arabic aliases, source/mission filtering and a corpus/model collection fingerprint. Default to BM25. |
| Medium | Async tests failed because their plugin was absent from the installed environment. | Use standard-library asyncio runners and deterministic mocked transport. |
| Medium | Deployment and dataset extension contracts were incomplete. | Document the API, offline event wiring, adapter lifecycle, and static versus dynamic provenance. |

Existing routes and legacy response fields remain available. Added fields include `voice_text`, `suggested_action` and evidence metadata. The status string values give narrower diagnostics. Inputs with invalid resource percentages, whitespace-only questions and oversized bodies now return validation errors.

## Verification

Original baseline: 8 passed and 3 failed because the async test plugin was missing. Revised suite: 42 passed, 0 failed, 0 skipped. The installed Starlette emitted one TestClient/httpx deprecation warning. Tests cover adapter deduplication and reload, mission filtering, event order and concurrency, provider timeout and errors, request validation and CORS, Arabic request forwarding, the stable instruction boundary, and output IDs/actions. In a five-query retrieval check, all four expected sources appeared in the top three, and the nonsense query returned no chunks. One query used mixed Arabic/English. This is a small fixture set, with no claim of general multilingual accuracy.

Loopback Uvicorn smoke test covered `/health`, English and Arabic offline chat, urgent event priority and duplicate and stale event suppression. The local corpus yielded 323 chunks. HTTP measurements are from the final build with provider keys disabled:

| Measurement | Result |
| --- | --- |
| Start to first healthy HTTP response | 301.9 ms |
| Cold BM25 build | 27.37 ms |
| Warm BM25, 500 identical queries | 0.308 ms median, 0.349 ms p95 |
| Warm offline chat, 50 requests | 0.39 ms median, 0.58 ms p95 |
| Warm event, 50 requests | 0.39 ms median, 0.61 ms p95 |
| Offline chat, 80 requests at concurrency 8 | 3.31 ms median, 6.07 ms p95 |

Live Gemini latency, token usage and cost, peak memory, semantic persistence with real embeddings, model safety and scientific factuality, live NASA ingestion, and Unity compilation and scene integration remain unverified. The project contains a Unity bridge but no playable Unity project. Client-facing traffic needs application authentication and rate limits at the deployment boundary. Event revisions and deduplication are local to a single worker. Cross-turn chat history is absent.

## Files

Backend changes are in `app/assistant.py`, `app/config.py`, `app/events.py`, `app/gemini.py`, `app/main.py`, `app/retrieval.py`, `app/schemas.py`, and the new `app/knowledge.py`, `app/limits.py` and `app/system_prompt.md`. Integration changes are in `unity/NovaBridge.cs`, `.env.example`, `README.md`, `tests/test_fast.py`, and the new `tests/test_integration.py`, `scripts/smoke_http.py`, `scripts/verify_local.py`, and three documents under `docs/`.
