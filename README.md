# SURVORA

SURVORA is an educational Mars colony survival and exploration game for NASA Space Apps. NOVA, its FastAPI companion, uses curated NASA and Canadian Space Agency references to explain science in English and Egyptian Arabic. It supports optional Gemini dialogue and deterministic gameplay event responses.

| Directory | Contents |
| --- | --- |
| [backend/](backend/) | NOVA service, tests, knowledge corpus, and sample Unity bridge in `backend/unity/`. |
| [unity/](unity/) | Reserved for the Unity project. Add `Assets/`, `Packages/`, and `ProjectSettings/` here. |
| [docs/](docs/) | API integration, knowledge sources, and verification. |

## Run NOVA

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-core.txt
cp -n .env.example .env
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Configure Gemini credentials in the server environment. Unity calls NOVA through `/chat`, `/events`, and `/health`. The backend supports deterministic fallback dialogue and event responses without a Gemini key. The game owns state and actions.

## Tests and deployment

From `backend/`, run `NOVA_ENABLE_SEMANTIC=false NOVA_CLIENT_TOKEN='' python -m pytest -q`. Run `python -m scripts.verify_local` for a loopback HTTP smoke test.

See the [backend setup, environment and deployment guide](backend/README.md), [API contract](docs/INTEGRATION.md), [knowledge inventory](docs/NASA_DATA_INVENTORY.md), and [Unity Editor verification](docs/UNITY_EDITOR_VERIFICATION.md). NOVA rebuilds its 334-chunk corpus from checked-in documents. The optional Chroma index is stored under `backend/cache/chromadb/`. The backend guide explains how to rebuild or restore it.
