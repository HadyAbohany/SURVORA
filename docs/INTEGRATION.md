# NOVA game integration

## Run the backend

From the NOVA directory, use its existing virtual environment or create one with `python3 -m venv .venv`. Activate it with `source .venv/bin/activate`, then run:

```sh
python -m pip install -r requirements-core.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For Gemini, set `GEMINI_API_KEY` or `GEMINI_API_KEY_1` server-side using the existing `.env` or `.env.example`. Restart after configuration changes. With no key, the backend offers deterministic mission clues and event dialogue. Use HTTPS and a trusted server-side relay for a distributed game. Configure exact browser origins and enforce rate, concurrency and request deadlines at the relay. Keep provider keys and private access tokens out of shipped game builds.

## API contract

Use the existing unversioned routes with optional request `schema_version: "1.0"`. Full schemas and an interactive client are served at `/docs` and `/openapi.json`.

| Route | Input | Output |
| --- | --- | --- |
| GET /health | None | Corpus size, retrieval mode, provider configuration and backend version. Provider availability is not probed. |
| POST /chat | Chat request | Player dialogue, grounding status and optional suggestion. |
| POST /hint | Chat request | Dialogue instructed to use the supplied hint level. |
| POST /mission/briefing | Chat request | Mission introduction. |
| POST /mission/debrief | Chat request | One mission lesson. |
| POST /sample/explain | Chat request | Explanation based on available observations and references. |
| POST /events | Event request | Deterministic event dialogue or a silent outcome. |

```sh
curl -fsS http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why is my oxygen decreasing?","language":"en","mission_id":"M02_OXYGEN_MYSTERY","hint_level":1,"game_state":{"oxygen":20,"power":15,"oxygen_generator_status":"underpowered","research_lab_on":true},"allowed_actions":["Inspect oxygen plant","Change power priority"]}'
curl -fsS http://127.0.0.1:8000/events \
  -H 'Content-Type: application/json' \
  -d '{"event_id":"oxygen-1","event_type":"OXYGEN_LOW","session_id":"example-session","state_revision":2,"priority":"high","mission_id":"M02_OXYGEN_MYSTERY","language":"en","game_state":{"oxygen":20,"power":15}}'
```

If you set `NOVA_CLIENT_TOKEN`, send it as `X-Nova-Token` on POST requests. Chat requires a 1–500 character question. Use `en` or `ar`, `Explorer` or `Commander`, hint level 0–3, and up to 30 action labels. Mission IDs accept letters, digits, underscores and hyphens so new missions require no backend release. Resource values are HUD percentages in [0,100]. Leave unknown values absent. Free-form state maps are preserved for existing callers and excluded from the provider payload.

Example offline chat response:

```json
{
  "answer": "The oxygen plant has too little power. Where else is power going?",
  "voice_text": "The oxygen plant has too little power. Where else is power going?",
  "language": "en",
  "suggested_action": null,
  "sources": [],
  "grounding_status": "llm_unavailable",
  "response_origin": "deterministic_fallback",
  "relevant_game_context": {
    "schema_version": "1.0", "oxygen": 20, "power": 15,
    "oxygen_generator_status": "underpowered", "research_lab_on": true,
    "active_emergencies": [], "buildings": {}, "extra": {}
  },
  "audio_ref": null,
  "response_mode": "TEXT_ONLY"
}
```

Show `answer` for chat and `text` for events. Use `voice_text` for optional game-owned TTS. Sources are available separately with their corpus layer and provenance. A non-null `suggested_action` must still be revalidated by the engine and presented as a player choice. The game owns all execution.

Expected errors are 401 for a required token, 413 for bodies over 32 KiB, and 422 for invalid input. Retrieval or model failures return HTTP 200 with a fallback and a diagnostic `grounding_status`. Treat other HTTP errors or connection failures as a temporary dialogue failure.

## Wire the event bus and UI

1. Generate an opaque session ID per play session. Increment `state_revision` across mission changes. Start a fresh session ID when the counter resets.
2. Let the engine apply mission-configured resource thresholds and recovery thresholds. Emit on entry or recovery, with unique IDs, rather than on every frame. The backend accepts the event as an engine fact and does not infer a warning from a raw percentage. The example oxygen value of 20 is a test snapshot.
3. Unity uses local `PublishEvent` for immediate subtitles. Set its TMP subtitle and base URL in the Inspector. Other clients can POST to `/events`. Skip rendering silent outcomes and prioritize urgent dialogue over ordinary lines.
4. Route deliberate Ask, Hint and Explain interactions to chat or the matching route. Send the current snapshot and authorized action labels. Discard replies after a newer ask, newer state revision or urgent alert. Give an urgent local alert priority for its display window.
5. For progressive hints, maintain level 0–3 in the game. Increase it for deliberate requests after the same obstacle, then reset it at the next objective.

The HTTP event response includes `trigger_id`, `should_speak`, `text`, `voice_text`, `response_mode`, `priority`, `response_origin`, and echoed `state_revision`. Audio and educational explanation are nullable. Priorities are low, normal, high and critical. Recognized urgent events are at least high. Event IDs deduplicate per session for up to ten minutes. Optional dialogue of the same type is throttled for 30 seconds per session and mission. Positive revisions reject older snapshots. Omitted or zero revisions support legacy clients. Optional timezone-aware ISO timestamps allow up to 120 seconds of age and 30 seconds of clock skew. Unknown valid event names return silent. Server event state is bounded and process-local. Use one worker if you rely on server-side deduplication.

Representative event names include `OXYGEN_LOW`, `OXYGEN_RESTORED`, `POWER_LOW`, `POWER_CRITICAL`, `WATER_SHORTAGE`, `FOOD_SHORTAGE`, `RESOURCE_CONSUMPTION_ABNORMAL`, `BUILDING_MALFUNCTION_CRITICAL`, `MISSION_STARTED`, `MISSION_OBJECTIVE_UPDATED`, `MISSION_STAGE_COMPLETED`, `MISSION_CHECKPOINT`, `OBJECTIVE_FAILED`, `OBJECTIVE_RETRIED`, `MISSION_COMPLETED`, `SAMPLE_DISCOVERED`, `PHENOMENON_DISCOVERED`, `NASA_ASSET_APPROACHED`, `TECHNOLOGY_UNLOCKED`, `REPEATED_FAILED_ACTION`, `CLUE_IGNORED` and `EFFECTIVE_DECISION`. The full backend catalog is in `app/events.py`. The Unity local switch supports its original subset and defaults to English. Route new or Arabic event dialogue through the HTTP endpoint for clients that need it.

Run `python -m pytest -q` and `python -m scripts.verify_local`. The second command starts and stops a temporary loopback server and runs executable examples with keys disabled.
