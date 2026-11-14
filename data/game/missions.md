# SURVORA — Mission Campaign & Base Crisis Design (v2)

**Language:** Arabic (Egyptian) with English engineering identifiers  
**Audience:** 7–12 years  
**Platform:** Unity — isometric base + bounded third-person expeditions  
**Design status:** Proposed implementation design, not an existing game build  
**Scenario numbers:** Illustrative GAME BALANCE values, not NASA measurements.

## 1. Story and gameplay contract

Player = commander of SURVORA-1, a small crewed Mars base. AI companion = **NOVA** (temporary name). The mission loop is **Notice → Understand → Choose → Observe consequences → Learn → Earn KP**. Each mission teaches **one primary science principle**, introduces at most one new building, offers at least **two viable decisions with costs**, gives warning before major loss, and has a recovery path. The game has no irreversible child-punishing deaths. On critical failure show a friendly replay card: “جرّب تاني: إيه اللي محتاج يتغير؟” with pre-crisis checkpoint.

Base view = grid buildings, power priorities, supplies, toggles, repairs. Third-person view = small mission arena, interact/scan/repair/return; base stores keep simulating on expedition (or sim paused at checkpoint in beginner setting). Three core HUD meters: **O2, POWER, CREW SAFETY**; food, water, parts, radiation shown in panels as needed. All systems share one authoritative simulation state, not separate story scripts that ignore resources.

Difficulty: **Explorer (7–9)**: highlighted interactables, generous countdown, 2 decisions, no negative cascade without hints; **Commander (10–12)**: 3–4 options, denser resource trade-offs, moderate deadlines. Accessibility: no reading-only gameplay; voice or readable short captions, icon + color (not color alone), pause and replay, tooltips.

## 2. Campaign structure

| Chapter | Levels | Base missions | Expeditions | Unlock |
|---|---|---|---|---|
| 1 Welcome to Mars | 1–2 | M01 First Light, M02 Oxygen Mystery | E01 First Footprints (optional short tutorial) | Battery, Oxygen Plant |
| 2 Red Planet Strikes | 3–4 | M03 Red Dust Rising, M04 Broken Circuit | E02 Lost Sensor | Maintenance Kit, Dust Shield |
| 3 Life on Mars | 5–6 | M05 Thirsty Colony, M06 Greenhouse Challenge | E03 Ice Clues | Water Recycler, Hydroponics |
| 4 Danger from the Sun | 7–8 | M07 Solar Alert, M08 Silent Signal | E04 Shelter Run | Radiation Shelter, Relay |
| 5 Survival Test | 9–10 | M09 The Domino Effect, M10 Sol 30 Finale | E05 Rescue the Rover | Command Upgrades, Survivor Badge |

KP rewards are scenario balancing units: early 100–200, middle 200–300, later 300–500. **Mission KP** are awarded for completion; optional science badge rewards are granted for explaining an outcome or trying a second solution. Players can never grind unlimited KP by replaying the same scenario: first clear full KP, replay grants badge/learning but no more than a small capped bonus.

## 3. Base buildings and dependency map

| Building | Input | Output | Failure mode | Interesting player action |
|---|---|---|---|---|
| Command Center | power | alerts, priorities, expedition access | delayed warnings | set automatic priority for life support |
| Solar Array | daylight, panel health, dust transmission | electrical power | storm/cloud dust or coating reduces yield | add spare panels, clean with parts |
| Battery Bank | surplus power | backup power | depletion | reserve charge / discharge threshold |
| Oxygen Plant (fictional crew-scale MOXIE-inspired) | power, atmospheric CO2, functioning hardware | O2 | underpower, wear | emergency/normal mode |
| Life-Support & Habitat | O2, power | crew safety | continuous O2 drain, comfort loss | prioritize habitat |
| Water Recycler | energy, recoverable wastewater | reclaimed water | filter wear | replace filter; ration nonessential use |
| Greenhouse | water, lighting power, nutrients | limited fresh food | crop stress | regulate irrigation/light |
| Storage | supplies | buffer | shortage | keep safety reserve |
| Radiation Shelter | shelter infrastructure, limited power for equipment | protected crew location | insufficient capacity/maintenance | pause EVA and move crew inside |
| Research Lab | power and samples | KP and unlocks | paused progress | defer to life-support |
| Communications Relay | power, visibility/availability | Earth message windows | interruptions | queue data, retry when link available |

**Scientific guardrail:** NASA MOXIE demonstrated production on a small scale, not crew-grade breathing supply. NASA DONKI events are heliophysics event metadata, not an automatic Mars-site radiation forecast. NASA RAD aboard Curiosity is more geographically relevant for Mars surface exposure than ISS-based RadLab data; modeled shielding and surface dose must be clearly labeled simplified. Dust storms come from Mars atmospheric science and historical scenarios, **not** from DONKI.

## 4. Mission template for Unity

Each mission stores: `missionId`, `title`, `chapter`, `audience`, `newConcept`, `openingDialogue`, `prerequisites`, `startingState`, `stages[]`, `triggers[]`, `availableActions[]`, `successConditions`, `checkpoint`, `failureRecovery`, `dataEvidence[]`, `simulationParameters`, `aiHintLevels[3]`, `kpReward`, `unlocks`, `debriefQuestion`. Each stage contains a clear goal, 1–3 current objectives, a state trigger, an escalating visual cue, and feedback. **Do not hardcode exact NASA observations into scripted dialogue unless the associated snapshot is shipped with scenario data.**

## 5. Ten complete base missions

### M01 — First Light | Level 1 | 3–5 min
**Hook:** “Commander! قبل ما الشمس تغرب، لازم نخلي القاعدة تشتغل!”  
**Initial:** command center + habitat, one broken starter panel, O2 reserve safe, battery low; the only resource introduced is electricity.  
**Stages:** (1) inspect command center and discover energy deficit; (2) place/repair solar panel; (3) watch generation meter rise; (4) sunset countdown, add battery; (5) select Research Lab OFF at night so habitat runs.  
**Two choices:** build spare panel now (cost Parts) vs keep parts and cut research load (slower knowledge).  
**Success:** habitat powered through simulated night, battery remains above game-defined safety floor.  
**Setback:** power drops; pause time, show connection/priority hint, replay sunset.  
**NOVA:** “الألواح بتصنع الكهرباء في الضوء، والبطارية بتخزنها؛ مين أهم مبنى ليلًا؟”  
**Data:** NASA Mars solar-flux/dust science; solar generation curve in the game is *modeled*.  
**Reward:** 100 KP, Battery Bank unlocked; debrief: Why does battery matter if solar panels work?

### M02 — Oxygen Mystery | Level 2 | 4–6 min
**Hook:** O2 meter falls even though oxygen plant is built.  
**Initial:** `O2=65%` illustrative, limited spare power, research active.  
**Stages:** (1) low O2 warning; (2) inspect plant status “UNDERPOWERED”; (3) compare production with crew consumption; (4) move power priority away from research or release reserve battery; (5) stable trend; (6) optional research offer creates second trade-off.  
**Choices:** switch Research Lab off → safe O2 / lost research time; consume battery → faster research / weaker nighttime reserve.  
**Success:** net O2 trend positive or stable for a defined number of ticks and reserve above floor.  
**NOVA hint 1:** “المشكلة في التوصيل ولا الإنتاج؟”; hint 2: “شوف Power Allocation”; hint 3: “جرّب توقف Research مؤقتًا”.  
**Data:** MOXIE science-backed **mechanism**, fictional crew-sized plant; do not copy real MOXIE ~12 g/h as sufficient for crew.  
**Reward:** 150 KP, Oxygen Efficiency I.

### M03 — Red Dust Rising | Level 3 | 5–7 min
**Hook:** Weather monitor shows approaching orange dust wall.  
**Initial:** solar panels normal, battery 70% illustrative, crops not yet central.  
**Five phases:** (1) **Forecast**: 60-second readable/game-time alert, player chooses power plan; (2) **Arrival**: sky reddens, modeled solar irradiance multiplier begins dropping; (3) **Peak**: batteries deplete, player chooses lab OFF vs greenhouse OFF vs backup battery; (4) **Aftermath**: sunlight returns but deposited dust keeps panel efficiency suppressed; (5) **Recovery**: maintenance crew/rover cleans panels and restores generation.  
**Choices:** save greenhouse growth at energy cost vs pause crops to preserve O2; clean immediately using Parts vs wait for resource shipment/expedition to acquire parts.  
**NOVA:** Ask child to predict which system loses power first. Highlight dependencies.  
**Data:** archived NASA dust-storm cases, NASA solar-power impact, not DONKI; `dustOpacity` and `panelDustFactor` illustrative scenario curves.  
**Reward:** 200 KP, Dust Cleaning Kit, opens E02.

### M04 — Broken Circuit | Level 4 | 4–6 min
**Hook:** “الـOxygen Plant شغال، لكن الطاقة مش واصلة!” A cable/relay power fault after storm.  
**Phases:** (1) warning on power network; (2) inspect three paths; (3) use repair part to reconnect life support OR re-route through backup consuming battery; (4) lab request conflicts with reserve; (5) restore stable supply and document fault.  
**Choices:** fix primary route (Parts cost; enduring benefit) vs backup bypass (quick, depletes battery).  
**Gameplay:** click broken segment + simple 2-step wiring puzzle, no complex electrical quiz.  
**Data:** educational engineering/game mechanic; do not imply sourced from NASA observations.  
**Reward:** 180 KP, Remote Repair I.

### M05 — Thirsty Colony | Level 5 | 4–6 min
**Hook:** water tank falls as first greenhouse starts needing irrigation.  
**Phases:** (1) water alert; (2) diagnose worn recycler filter; (3) choose crew/habitat water priority vs farm watering; (4) repair filter, cost Parts and power; (5) observe recycling improve while crop recovers.  
**Choices:** keep water for crew, slower plants vs use emergency tank for plants, shorter safety margin. Crew drinking water cannot be permanently cut to zero.  
**NOVA:** “الميّه بتنفعنا أكتر من مرة لو نضفناها، لكن إعادة التدوير محتاجة طاقة.”  
**Data:** NASA life-support / water-recovery concepts; numerical efficiencies scenario-tuned unless cited and adapted precisely.  
**Reward:** 220 KP, Filter Efficiency I.

### M06 — Greenhouse Challenge | Level 6 | 5–7 min
**Hook:** “أول سلطة مريخية!” Seedling appears, later leaves turn weak.  
**Phases:** (1) choose crop (one default fast-growing lettuce; others cosmetic first); (2) adjust light/water sliders within 3 safe presets; (3) see growth over accelerated sols; (4) sudden low power forces reduction of grow lights or temporary battery use; (5) repair plant conditions, harvest; (6) show each choice’s cost.  
**Choices:** run high-intensity LEDs → faster growth + higher power use; economy lighting → slower production + higher emergency reserve. Too little/too much water are both bad.  
**NOVA:** “النبات محتاج نور وميّه ومغذيات؛ مش أي كمية زيادة تبقى أحسن.”  
**Data:** NASA Veggie / Advanced Plant Habitat + CSA space food toolkit. Crop-growth coefficients are educational game tuning, not a genuine agronomic prediction.  
**Reward:** 250 KP, Hydroponics I.

### M07 — Solar Alert | Level 7 | 5–7 min
**Hook:** yellow/orange mission-control alert based on an archived DONKI record, no unsupported prediction of precise Mars arrival.  
**Phases:** (1) record appears with actual event timestamp/type and “NASA event” label; (2) scenario engine classifies *training challenge* separately from official event; (3) player cancels planned EVA and sends crew to shelter; (4) shield power / communications / research compete; (5) protective response scored; (6) debrief shows real record and fictionalized response assumptions.  
**Choices:** postpone EVA (forgo KP) vs complete essential instrument retrieval only if tutor/game marks conditions safe; prioritize shelter equipment vs research. Never reward unsafe risk-taking disproportionately.  
**Data:** DONKI FLR/SEP/CME event metadata; Mars radiation background from Curiosity RAD study. Earth geomagnetic storm `GST` cannot directly stand in for Martian surface dose.  
**Reward:** 300 KP, Shielding I.

### M08 — Silent Signal | Level 8 | 4–6 min
**Hook:** Message for Earth queued, but relay outage hides it; crew gets nervous.  
**Phases:** (1) transmit fails; (2) player sees relay requires power and contact window; (3) queue messages locally; (4) reduce noncritical load or wait for next link window; (5) send when window returns; (6) explain communication delay, not live chat with Earth.  
**Choices:** expend backup power now but still respect contact window vs conserve energy and transmit later.  
**Data:** educational orbital communication timing; scenario windows are modeled unless sourced from orbit tool. **Do not imply NASA DONKI solar flare automatically means radio blackout on Mars.**  
**Reward:** 250 KP, Relay Buffer.

### M09 — The Domino Effect | Level 9 | 6–8 min
**Hook:** dust warning, water filter fault and battery low appear in staggered order.  
**Phases:** (1) dust warning gives prep opportunity; (2) storm cuts solar, player manages battery; (3) recycler filter stops and crop starts stressing; (4) O2 goes below comfortable buffer if player kept lab on; (5) player reprioritizes life-support, repairs filter after storm, cleans panels; (6) interactive report: “Your power choice saved oxygen but delayed the crop.”  
**Choices:** several viable strategies; every one sacrifices something, but none forces permanent mission failure if player follows warnings.  
**Data:** mixture of NASA-informed subsystem behavior, **composite fictional scenario**.  
**Reward:** 350 KP, Emergency Automation (rule-based, not machine learning required).

### M10 — Sol 30: Survival Test | Level 10 | 7–10 min
**Hook:** “القاعدة وصلت يومها التلاتين. تقدر تخليها مستقلة لمدة 3 أيام؟”  
**Phases:** (1) briefing and select 2 of 3 preparatory upgrades; (2) simulate day 1 power shortage; (3) day 2 greenhouse/habitat resource competition; (4) day 3 choose research vs crew safety in a forecast event; (5) maintain safety for three accelerated sols; (6) NASA Science Debrief with achieved badges and alternate plans.  
**Success:** maintain critical life support, show stable supplies, address warnings.  
**Failure:** checkpoint at beginning of day; explain and retry.  
**Reward:** 500 KP, “Mars Mission Commander” badge, Sandbox Mode.

## 6. Expedition missions (third-person)

### E01 — First Footprints (Level 2, 2–4 min)
Short EVA training: exit airlock → check suit O2/battery → scan 3 nearby objects → return before low reserve; demonstrate that suit O2 is separate from habitat O2. Discover mission icon and 60 KP. No adversaries.

### E02 — The Lost Sensor (Level 4, 4–6 min)
After dust storm, solar/atmosphere sensor stops sending data. Follow marker → scan terrain → choose shorter rocky path (low O2 use, slows movement) or longer safe path (more O2) → repair using one component → obtain storm-observation card → return. Unlock weather warning buffer and 150 KP. Mars Trek can inspire scene placement/terrain but not guarantee game mesh readiness.

### E03 — Ice Clues (Level 6, 5–7 min)
Scout for subsurface-water clues: navigate three candidate scanning points, analyze sample indicators, collect a science card; no magical instantly extractable drinkable water. Longer survey gives more KP but raises suit consumption and battery cost. New base *research* unlock for water processing, not unlimited water supply. Mars Trek terrain data can inform layout.

### E04 — Shelter Run (Level 8, 4–6 min)
Player begins short safe planned EVA; a training solar alert emerges after scan. Choose stop task and return to pressurized shelter; optional place emergency relay only if enough time/resources. If unsafe, AI recommends aborting. Reward for following safety protocols, not gambling. Use DONKI archived metadata as scenario anchor only, not real Mars arrival calculation.

### E05 — Rescue the Rover (Level 9, 5–7 min)
Rover stuck beyond ridgeline before forecast dust; choose to retrieve science module with rover rescue tool or abandon sample and return safely. Base needs rover for cleaning panels after storm. Trade-off: use spare power/parts to rescue rover or save supplies and lose extra KP. No combat; rescue and engineering puzzle.

## 7. Crisis escalation ladder — reusable incident phases

Every base incident has **A Detection → B Diagnosis → C Decision → D Escalation → E Recovery → F Debrief**. Base incidents and their linked effects:

| Incident | Detect | Primary effect | Secondary effect | Third-order effect | Recovery |
|---|---|---|---|---|---|
| Dust storm | sky/weather alert | solar generation declines | battery drains | O2/lighting threatened | power triage, clean panels |
| Night/fading sunlight | sunset forecast | solar output 0 | batteries discharge | research must pause | battery + priority plan |
| O2 underproduction | downward O2 trend | reserve declines | crew safety margin shrinks | emergency pause science | repair / reallocate power |
| Water recycler fault | filter alarm | reuse drops | tank depletion | crop stress | new filter + power |
| Greenhouse stress | yellow crop leaves | slow biomass production | food forecast drops | extra resupply need | light/water adjustment |
| Power grid break | disconnected node | chosen building loses power | system output falls | reserve depletion | bypass vs repair |
| Solar particle training alert | NASA event banner | EVA risk scenario | shelter needed | research postponed | safe haven, reschedule EVA |
| Comms window miss | queued messages | data not delivered | research reporting delay | lost optional KP | store and retry |
| Suit leak / EVA equipment problem | suit warning | O2 use rises in simplified model | EVA time falls | abandon samples | return / seal patch (tutorial) |
| Spare-part shortage | inventory low | repair delayed | degraded efficiency persists | harder next crisis | optional retrieval mission |

**Never stack more than two new threats at once before Level 9.** Use warning/diagnosis phases to teach causal links. Make failures reversible via checkpoints and understandable debriefs.

## 8. NASA data integration — event sourcing

1. **Static curated `nasa_events.json`** (best reliable hackathon MVP) with original source URL, event ID, observed UTC time, raw fields, retrieval time, science interpretation, and `scenarioAssumptions` separately. Add UI “Archived NASA event — educational scenario”.
2. Optional backend `GET /api/nasa/events` fetches DONKI `FLR`, `SEP`, `CME`, caches response and validates records. NASA DEMO_KEY should not be exposed in public WebGL client; prefer backend proxy/secret. If offline use packaged cached JSON and label it.
3. **DONKI does not produce Mars dust-storm conditions.** Use NASA dust papers/historical reports or planetary weather archives. Design `dustOpacity` trajectories as *scenario model assumptions*.
4. **Mars radiation:** Curiosity RAD provides Mars-surface measurement context; RadLab/OSDR space-station measurements provide non-Mars comparative science, not direct dose on Mars. Separate `SolarEvent` from `MarsDoseEstimate`.
5. **O2:** NASA MOXIE demonstrates technology; production/consumption in SURVORA is crew-scale fictional model tuned for ages 7–12 and clearly labeled.
6. **Plants:** NASA Veggie/CSA evidence maps to meaningful control inputs (light, water, nutrients). Yield and growth durations are pedagogical.
7. **Mars Trek:** choose terrain and landmark references; check source usage/credit and processing requirements; game-ready meshes require creation/optimization.

## 9. Simulation systems & game-tuned equations

For each tick (`dt` hours), run deterministic updates. **All coefficients below are placeholders to be playtested, not NASA measurements**:

- `solarPower = panelRatedPower * daylightFactor * (1-dustOpacity) * panelCleanliness * panelHealth`
- `netPower = solarPower + allowedBatteryDischarge - sum(allocatedLoads)`; ensure not to count battery twice; update battery energy from `generation - demand`, subject to charge/discharge caps and efficiency.
- `oxygenReserveNext = clamp(O2 + O2PlantProduction(powerFraction,plantHealth)*dt - crewO2Consumption*dt - expeditionRefill*dt,0,O2Capacity)`.
- `waterNext = clamp(water + recyclerRecoveredWater - habitatWaterUse - irrigationWaterUse,0,capacity)`.
- `cropGrowthNext = cropGrowth + dt * normalizedLight * irrigationFitness * nutrientFitness * greenhouseHealth` (educational proxy only).
- `crewSafety` should be an abstract 0–100 warning/comfort score, not a fake clinical prediction.
- `radiationThreatTier` from curated scenario labels (training-only), NOT fabricated real physical dose from DONKI flare class.
- `batteryReserveWarning = estimatedHoursRemaining < chosenSafeHorizon`.

**Crisis scheduling:** `EventDirector` chooses authored events based on level and player readiness; no random catastrophic event before setup and recovery affordance. Max one new system per mission; M09 deliberately combines mastered systems.

## 10. AI companion — model vs deterministic engine

**No training a custom ML model is needed for simulation.** Unity C# modules handle scientific/game rules and simulation state. A pretrained LLM with curated NASA RAG supplies educational explanations. The companion must never directly change oxygen/power numbers, declare a player safe without rules confirmation, or invent NASA citations.

**RAG content collections:** (A) NASA documents on dust/solar power, MOXIE, ECLSS, RAD, DONKI definitions, Veggie; (B) GAME RULES and unit assumptions; (C) mission guides + hints, (D) optional NASA event snapshot cards. Retrieval returns source, citation URL, relevant fragment; answers in simple Arabic (or English based on game locale).

**Input example**:
```json
{
  "playerAgeBand": "7-9",
  "missionId": "M03",
  "stageId": "peak",
  "intent": "hint",
  "gameState": {
    "oxygenPct": 54,
    "batteryPct": 24,
    "solarOutputPct": 18,
    "greenhouseEnabled": true,
    "researchEnabled": true,
    "dustEvent": {"type":"historical-inspired","source":"NASA Mars dust science"}
  },
  "question": "أعمل إيه عشان الأكسجين ميفصلش؟"
}
```
**LLM output format**: `message`, `questionForChild`, `sourceCards[]`, `suggestedActionIds[]`, `confidenceTag`. The backend validates IDs against an allowlist; engine validates actual preconditions. **Three hint levels:** curious question → directional hint → explicit suggested safe action if child is stuck. Example: “بص على المباني اللي تقدر توقفها شوية؛ هل المعمل أهم دلوقتي من جهاز الأكسجين؟”

**Do not fine-tune on NASA raw API logs**; live events are structured JSON for the simulator and citations, not useful model weight training data. If a small intent classifier becomes necessary later, label intents `explain`, `hint`, `define`, `compareOptions`, `nasaSource`, `status` and use rules or a basic model.

## 11. Unity technical breakdown

`GameState` (single source of truth) → `SimulationClock` → `PowerSystem`, `OxygenSystem`, `WaterSystem`, `FoodSystem`, `RadiationScenarioSystem`, `MaintenanceSystem`, `ExpeditionSystem`; `EventDirector` injects scenario changes; `MissionManager` reads success conditions and grants KP; `UIController` reacts to state; `AIChatController` sends *sanitized snapshots* to backend and renders hints/source cards. `GameState` persists when switching Base ↔ Expedition scenes. Use ScriptableObjects for building data + mission definitions or JSON for easy content iteration.

**Example core events**: `OnPowerBelowThreshold`, `OnOxygenTrendNegative`, `OnDustWarning`, `OnSolarAlertScenario`, `OnFilterFailed`, `OnExpeditionReturned`, `OnRepairCompleted`. Keep each mission deterministic in tests.

**Scenario schema sketch**:
```json
{
  "id":"M03",
  "title":"Red Dust Rising",
  "type":"base",
  "requiredLevel":3,
  "educationalObjective":"Dust can reduce sunlight and solar electricity",
  "scienceSourceType":"NASA_MARS_DUST_STUDY",
  "isArchivedScenario":true,
  "gameBalanceValuesAreMeasurements":false,
  "stages":[
    {"id":"warning","trigger":"mission_start","objective":"set_emergency_power_plan"},
    {"id":"arrival","trigger":"plan_set","objective":"observe_solar_drop"},
    {"id":"peak","trigger":"dustOpacity>=0.65","objective":"keep_oxygen_active"},
    {"id":"aftermath","trigger":"storm_ended","objective":"repair_or_clean_panels"},
    {"id":"recovery","trigger":"solarOutputPct>=70","objective":"complete_debrief"}
  ]
}
```

## 12. Upgrades, unlocks and rewards

| Level | Unlock | Player-facing benefit | Cost/trade-off |
|---|---|---|---|
| 1 | Solar + battery | first power resilience | Parts + charging time |
| 2 | O2 Efficiency I | reduced plant energy per unit O2 | KP + Parts |
| 3 | Dust Cleaning | regain panel cleanliness | repair parts and action time |
| 4 | Remote Repair | fewer expedition risks for routine fixes | higher upfront parts |
| 5 | Filter Efficiency I | more reclaimed water | power & consumables |
| 6 | Hydroponics I | faster / steadier crop production | power or parts |
| 7 | Shielding I | safer radiation-scenario response | material investment |
| 8 | Relay Buffer | queue messages through interruptions | standby power |
| 9 | Emergency Automation | if power low, pause noncritical labs automatically | KP + lower research throughput |
| 10 | Sandbox Mode | repeat crises and explore designs | no survival advantage |

Upgrade formula concept: `NewEffect = baseEffect*(1+upgradeBonus)` with bonus assigned explicitly in balancing config. **Upgrades should not remove trade-offs entirely**; even better batteries have finite capacity and occupy construction budget.

## 13. Practical build order for a 24-hour hackathon

**Minimum impressive playable vertical slice:** First Light (M01) → Oxygen Mystery (M02) → Red Dust Rising (M03) → one Lost Sensor EVA (E02), plus one optional archived DONKI Solar Alert preview (M07 lite). Base buildings: Solar, Battery, Oxygen, Lab, Habitat. Resource HUD: O2/Power/Safety; maintenance/Parts represented minimally. AI: 6–10 curated NASA knowledge chunks and level-aware hints, with offline scripted fallback. Render a **source label in-game** when a NASA-derived event is shown.

**Priorities:**
1. Playable game loop and persistence between modes.
2. Working physical/resource consequence (power→O2).
3. Dust event with warning/peak/recovery.
4. One third-person EVA connected to base repair.
5. AI explanation from actual state and citations.
6. Polish, voiceover, additional chapters only after first five work.

**Acceptance tests:** turning research off raises available power; solar reduction drains battery before O2; zero power stops plant; returning from EVA reduces suit O2 and grants parts; a solar flare metadata record never silently maps to a fabricated Mars dose; no stage locks player out without checkpoint; NASA source card clearly distinguishes historical observation from simulated assumptions; no children asked to enter personal data.

## 14. References used in design

- NASA DONKI documentation: https://ccmc.gsfc.nasa.gov/tools/DONKI/ and https://api.nasa.gov/
- NASA Mars dust storm report: https://science.nasa.gov/resource/mars-report-dust-storms-on-mars/
- NASA Mars dust storm science: https://www.nasa.gov/solar-system/the-fact-and-fiction-of-martian-dust-storms/
- NASA MOXIE: https://www.nasa.gov/missions/mars-2020-perseverance/perseverance-rover/nasas-oxygen-generating-experiment-moxie-completes-mars-mission/
- NASA Mars radiation (Curiosity RAD): https://science.nasa.gov/resource/radiation-measurements-on-mars/
- NASA Growing Plants in Space: https://www.nasa.gov/exploration-research-and-technology/growing-plants-in-space/
- NASA Mars Trek: https://trek.nasa.gov/mars/
- NASA OSDR: https://osdr.nasa.gov/bio/repo/
- CSA Food Production: https://www.asc-csa.gc.ca/eng/youth-educators/toolkits/food-production/

---

**Core design rule:** The child should always understand **what went wrong, what choices they had, and why their choice changed the base**.
