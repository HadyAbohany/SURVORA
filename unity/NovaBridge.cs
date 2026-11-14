// NOVA Fast Text-Only Bridge (Unity 2021+). Add to existing GameObject.
// Unity remains authoritative for simulation, missions and event detection.
// No audio, network-trigger requests, automatic LLM follow-up or background prompts.
using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;

[Serializable] public class NovaState {
    public string schema_version = "1.0";
    public float oxygen, power, oxygen_trend, rover_battery;
    public string oxygen_generator_status, current_objective, current_stage, selected_sample_id;
    public bool research_lab_on;
}
[Serializable] public class NovaChatPayload {
    public string schema_version = "1.0", question, session_id, language, mission_id, age_mode;
    public int hint_level = 1;
    public NovaState game_state;
    public string[] allowed_actions;
}
[Serializable] public class NovaChatResult { public string answer, response_origin, grounding_status, response_mode; }

public class NovaBridge : MonoBehaviour {
    [Header("NOVA Backend (only used when player asks)")]
    [SerializeField] string baseUrl = "http://127.0.0.1:8000";
    [SerializeField] string clientToken = ""; // Do not embed private keys in a public build.
    [SerializeField] string sessionId = "";
    [SerializeField] TMP_Text subtitle;
    [SerializeField] float displaySeconds = 3.5f;
    [SerializeField] int chatTimeoutSeconds = 6;
    [SerializeField] float optionalEventCooldownSeconds = 30f;
    readonly Dictionary<string,float> lastEvent = new Dictionary<string,float>();
    int latestRevision;
    int alertGeneration;
    int questionGeneration;
    bool urgentVisible;
    string lastText = "";
    Coroutine displayRoutine;

    void Awake() {
        if (string.IsNullOrWhiteSpace(sessionId)) sessionId = Guid.NewGuid().ToString("N");
    }

    // Existing EventBus calls this after validating events in the actual simulation.
    // ALL event text is local and immediate. No HTTP request or Gemini invocation.
    public void PublishEvent(string eventType, string priority, string missionId, int stateRevision, NovaState state) {
        if (stateRevision < latestRevision) return;
        latestRevision = stateRevision;
        bool urgent = IsUrgent(eventType) || priority == "critical";
        if (!urgent) {
            if (priority == "low") return;
            float previous;
            if (lastEvent.TryGetValue(eventType, out previous) && Time.unscaledTime - previous < optionalEventCooldownSeconds) return;
        }
        lastEvent[eventType] = Time.unscaledTime;
        string line = LocalEventText(eventType, missionId);
        if (!string.IsNullOrEmpty(line)) { if (urgent) alertGeneration++; Show(line, urgent); }
    }

    static bool IsUrgent(string t) {
        switch(t) {
            case "OXYGEN_LOW": case "POWER_CRITICAL": case "BATTERY_DEPLETED":
            case "BUILDING_MALFUNCTION_CRITICAL": case "RADIATION_ALERT":
            case "EXPLORATION_UNSAFE": case "ROVER_BATTERY_LOW": return true;
            default: return false;
        }
    }

    static string LocalEventText(string t, string missionId) {
        switch(t) {
            case "MISSION_STARTED": return missionId == "M02_OXYGEN_MYSTERY" ? "Welcome to Oxygen Mystery! Let's inspect the oxygen plant." : "Mission started! Find your first clue.";
            case "MISSION_COMPLETED": return "Mission complete! Great investigating, Commander!";
            case "MISSION_FAILED": return "Good try! Review the clues and try again.";
            case "OXYGEN_LOW": return "Oxygen is low. Check the oxygen plant and its power.";
            case "OXYGEN_RESTORED": return "Great! Oxygen production is stable again.";
            case "POWER_CRITICAL": return "Power is critical. Prioritize life support.";
            case "BATTERY_DEPLETED": return "Backup battery is empty. Check power generation.";
            case "WATER_SHORTAGE": return "Water is low. Check the recycler.";
            case "FOOD_SHORTAGE": return "Food is low. Check the greenhouse.";
            case "BUILDING_MALFUNCTION_CRITICAL": return "A critical building needs repair. Check its status.";
            case "DUST_STORM_APPROACHING": return "Dust storm approaching. Plan your power reserve.";
            case "DUST_STORM_STARTED": return "Dust blocks sunlight. Check solar power.";
            case "DUST_STORM_ENDED": return "Storm passed. Check dust on the panels.";
            case "RADIATION_ALERT": return "Radiation alert. Stop exploring and check shelter plans.";
            case "EXPLORATION_UNSAFE": return "This area is unsafe now. Check your map.";
            case "ROVER_BATTERY_LOW": return "Rover battery is low. Plan a safe return.";
            case "ROVER_DAMAGED": return "The rover needs repair. Check its status.";
            case "NEW_AREA_DISCOVERED": return "New area discovered! Explore the clues.";
            case "SAMPLE_DISCOVERED": return "New sample! Scan it first.";
            case "SAMPLE_ANALYZED": return "Sample analyzed! Check the research card.";
            case "NEW_RESEARCH_UNLOCKED": return "New research unlocked! Check the lab.";
            case "PLAYER_STUCK": return "Need a clue? Check your current objective, or press Hint.";
            case "REPEATED_FAILED_ACTION": return "That didn't work yet. Try another approach, or press Hint.";
            case "FIRST_SCIENCE_INTERACTION": return "What do you think this scientific system does?";
            case "TECHNOLOGY_UNLOCKED": return "New technology unlocked!";
            case "MISSION_OBJECTIVE_UPDATED": return "New objective. Check the mission panel.";
            case "MISSION_STAGE_COMPLETED": return "Stage complete. Keep going!";
            default: return "";
        }
    }

    // ONLY call this from a player Ask/Explain/Hint button, never from PublishEvent.
    public void Ask(string question, string missionId, int revision, NovaState snapshot, string[] allowedActions, int hintLevel = 1) {
        latestRevision = Math.Max(latestRevision, revision);
        if (string.IsNullOrWhiteSpace(question)) return;
        NovaChatPayload body = new NovaChatPayload {
            question = question, mission_id = string.IsNullOrWhiteSpace(missionId) ? null : missionId, session_id = sessionId,
            language = "en", age_mode = "Explorer", hint_level = hintLevel,
            game_state = snapshot, allowed_actions = allowedActions ?? new string[0]
        };
        StartCoroutine(RequestAnswer(body, revision, alertGeneration, ++questionGeneration));
    }

    IEnumerator RequestAnswer(NovaChatPayload body, int revision, int capturedAlertGeneration, int requestGeneration) {
        Show("Thinking of a clue...", false);
        var req = new UnityWebRequest(baseUrl.TrimEnd('/') + "/chat", "POST");
        req.uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(JsonUtility.ToJson(body)));
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        if (!string.IsNullOrEmpty(clientToken)) req.SetRequestHeader("X-Nova-Token", clientToken);
        req.timeout = Mathf.Max(1, chatTimeoutSeconds);
        using(req) {
            yield return req.SendWebRequest();
            if (revision < latestRevision || capturedAlertGeneration != alertGeneration || requestGeneration != questionGeneration) yield break;
            if (req.result != UnityWebRequest.Result.Success) {
                Show("Check your mission panel for the next clue.", false); yield break;
            }
            NovaChatResult result = JsonUtility.FromJson<NovaChatResult>(req.downloadHandler.text);
            Show(result != null && !string.IsNullOrEmpty(result.answer) ? result.answer : "Try inspecting the mission objective.", false);
        }
    }
    void Show(string text, bool urgent) {
        if (subtitle == null || (urgentVisible && !urgent)) return;
        urgentVisible = urgent;
        if (displayRoutine != null) StopCoroutine(displayRoutine);
        subtitle.richText = false;
        subtitle.text = lastText = text;
        displayRoutine = StartCoroutine(ClearAfter(displaySeconds));
    }
    IEnumerator ClearAfter(float seconds) {
        yield return new WaitForSecondsRealtime(seconds);
        urgentVisible = false;
        if (subtitle != null) subtitle.text = "";
    }
    public void ReplayLastLine() { if (subtitle != null) subtitle.text = lastText; }
}
