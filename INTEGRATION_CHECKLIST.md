# Unity integration — fast text-only NOVA

1. Inspect existing Unity scenes, EventBus, MissionController, GameState and serialized prefab references before adding this script. Keep simulation code untouched.
2. Back up the existing `NovaBridge.cs`; replace it with `unity/NovaBridge.cs` from this release (or merge manually if original differs). Attach/keep TMP_Text subtitle reference. Remove old AudioSource / audio clip assignments if unused; this script does not require them.
3. From actual game events call `PublishEvent(eventType, priority, missionId, stateRevision, currentState)`; all events use **local C# text**, no network needed. Mark critical resource alarms high/critical. Non-urgent low-priority chatter is suppressed.
4. Map the UI **Ask**, **Explain**, or **Hint** buttons to `Ask(question, missionId, revision, currentState, allowedActions, hintLevel)`. This is the **only** method in this Unity bridge that calls Gemini `/chat`.
5. Ensure `stateRevision` advances whenever the relevant game state changes. Critical alerts invalidate pending AI answers, so outdated Gemini text doesn't replace an urgent warning.
6. In Inspector set `baseUrl` to your backend address, e.g. `http://127.0.0.1:8000` for local desktop. For devices on your LAN use the backend machine IP and configure backend binding / firewall accordingly.
7. `OXYGEN_LOW` should render text *immediately* even when backend is stopped. Mission introductions and completion lines should be instant too. No audio or TTS is expected.
8. During an alert do not auto-call `Ask(...)`. `PLAYER_STUCK` displays a predefined text prompting the player to press Hint; only a click calls Gemini.
9. Verify cooldown and high/critical priority behavior with a repeated mission event. Verify no client API key exposure; Gemini keys remain backend-side.
10. `python -m pytest -q` validates Python policies and mock Gemini logic. Unity compilation and actual gameplay integration must be validated in the game's Unity Editor.
