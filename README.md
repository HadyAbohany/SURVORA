# NOVA AI Companion

NOVA is the FastAPI companion backend for SURVORA, an educational Mars colony game. It answers player questions in English or Egyptian Arabic, uses a read-only Unity game snapshot, and can cite curated NASA and Canadian Space Agency references. The game owns simulation state and decides which actions are available.

## Architecture

- **FastAPI and Pydantic** validate requests and responses.
- **Retrieval** loads versioned Markdown from `data/nasa/` and `data/game/`. BM25 is the default. Optional hybrid retrieval adds ChromaDB and multilingual MiniLM sentence embeddings.
- **Google Gemini** receives the question, relevant state and selected excerpts. NOVA validates citation IDs and checks structured action suggestions against the submitted allowlist.
- **Event dialogue** uses localized templates independently of Gemini. The included Unity sample bridge posts chat and can display local alerts. The backend also exposes an event endpoint for clients that use it.
- **NASA observations** can be fetched explicitly with the DONKI and RadLab adapters. Chat and gameplay events do not consume observation feeds.

## Local setup

Use Python 3.11 or newer. Check optional ML wheel availability for your Python version and platform before enabling hybrid retrieval.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
cp -n .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set `GEMINI_API_KEY` or `GEMINI_API_KEY_1` in the server environment for live dialogue. Slots 1–10 are optional. Without a configured key, Chat returns deterministic fallback dialogue. Events remain available. Review `GEMINI_TEXT_MODEL` for a model available to your Google project. Set `NOVA_CLIENT_TOKEN` to require `X-Nova-Token` on POST requests. Keep secrets on the server or behind an authenticated relay. For browser clients, set `NOVA_CORS_ORIGINS` to the exact allowed origins. See `.env.example` for timeout, model and index settings.

## Unity API

| Method and route | Purpose |
| --- | --- |
| GET `/health` | Corpus size, retrieval mode and configuration. |
| POST `/chat` | Player question with optional game snapshot, mission, language, hint level and allowed actions. |
| POST `/hint` | Player-requested hint using the chat schema. |
| POST `/events` | Engine-triggered deterministic dialogue or a silent suppression response. |
| POST `/mission/briefing`, `/mission/debrief`, `/sample/explain` | Specialized chat intents. |

Visit `/docs` or `/openapi.json` for schemas. See [game integration](docs/INTEGRATION.md) for payloads and [Unity verification](docs/UNITY_EDITOR_VERIFICATION.md) for Editor checks.

## Tests

```sh
NOVA_ENABLE_SEMANTIC=false NOVA_CLIENT_TOKEN='' python -m pytest -q
python -m scripts.verify_local
```

The regression suite mocks model calls. The local smoke script starts a temporary loopback server with provider credentials disabled.

## Deploy and rebuild the index

For a small cloud instance, install `requirements-core.txt` and start one worker with `python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"`. Configure runtime secrets through the host. Use `/health` as a health check and check the response body for status and retrieval mode. BM25 rebuilds its in-memory index on startup from the same **334 chunks** (73 science and 261 game design). It is the lower-memory option for free-tier hosts. Deployment has not been tested on a specific cloud provider.

To build the optional Chroma index on a new server:

```sh
python -m pip install -r requirements-semantic.txt
NOVA_ENABLE_SEMANTIC=true python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
```

Allow the first boot to download or access the configured embedding model and build `cache/chromadb/`. Confirm `knowledge_chunks=334`, `semantic_enabled=true` and `retrieval_mode=hybrid_rrf` in `/health`. A semantic initialization failure can fall back to BM25. Inspect server logs when health reports BM25 unexpectedly. Use a writable persistent volume mounted at the repository's `cache/chromadb/` path to retain the database across releases. To restore an existing index, stop writers, restore the **entire** directory from a compatible backup, and use the same corpus, embedding model revision, and compatible semantic dependencies. A changed corpus or model name selects a new fingerprinted collection. If a compatible backup is unavailable, rebuild from the committed Markdown.

## Knowledge and provenance

The reproducible corpus includes project-authored summaries and source links. Official publications and map assets remain with their original publishers. Small public archived API excerpts are kept as test fixtures. See the [data inventory](docs/NASA_DATA_INVENTORY.md) and [knowledge extension guide](docs/KNOWLEDGE.md).
