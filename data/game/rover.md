# SURVORA — Mars Rover & Scientific Exploration Add-on (v1)

**Audience:** Unity-integrated development agent and game team. **Scope:** ADDITIVE expansion to the existing SURVORA Mars base and EVA game. **Do not redesign or overwrite the existing project.**

## 0. Non-negotiable integration rules
1. Inspect existing Unity scenes, prefabs, scripts, packages, asset folders, save format, building catalog, and mission definitions BEFORE writing code. Existing prefabs made by the team take precedence over downloaded assets or generated placeholders.
2. Never delete, move, rename, retexture, or replace a team's custom 3D model without explicit permission. Preserve transforms, material references, animation controllers and existing interactions. Prefer child components/adapter scripts on existing prefabs.
3. Reuse the existing `B18 Rover Garage`, existing `EVA` scene, `E05 Rescue the Rover`, `Research Lab`, `EventBus`, `MissionController`, `GameState`, `SaveService`, `NovaClient`, `SourceProvenanceUI`. Extend these only where necessary. If code structures differ, adapt to them—do not create duplicate managers.
4. Everything added must work with offline local NASA snapshots. No runtime internet dependency for core mission flow. NASA source attribution in the UI: observed data vs scientific reference vs gameplay-only invented values.
5. Existing base resource simulation, 10 main missions, EVA missions E01–E05, KP, upgrades and progression must keep functioning. Add optional rover objectives to some existing missions; do not silently change their completion conditions.
6. Source links are references for humans/agents; they are NOT permission to scrape arbitrary pages or download assets without checking licenses. Use custom team's models first.
7. Target ages 7–12: short clear actions, forgiving speed and collisions, safe recovery, no combat, no permanently losing samples or rover, legible prompts, gentle coaching.

## 1. Feature summary and player loop
`Base → Rover Garage → Select Exploration Mission → Choose equipment/charge → Drive rover across Mars → Scan locations → Analyze/sample rock/regolith → Decide: collect more vs return with safe battery margin → Drive into Garage → Deliver samples to Research Lab → Earn KP and research progress → Unlock rover/base upgrades → New science missions.`

**Modes:** Base Mode (top-down) retains existing structure; Rover Drive Mode (third-person follow camera) is entered via garage or mission marker, not a new standalone game. EVA walking mode remains available; contextual `E` enter/exit vehicle when stationary and safe. The rover does not consume human suit O2 while the astronaut is inside a pressurized fictional vehicle; if the team's rover is unpressurized, suit O2 continues to deplete. Default prototype: **remotely piloted robotic rover** (no astronaut inside); camera switches from base to rover, removing pressure/suit gameplay contradictions. Make this design choice a `RoverControlMode` enum so art/UX can change later.

## 2. Vehicle: SURVORA Explorer Rover (XR-1)
### Model mapping (no new art required)
- Existing rover model: assign in inspector to `RoverVisualRoot` child of `RoverRoot`, no assumptions about file names.
- `RoverRoot`: Rigidbody + 1–3 simple Colliders; drive physics; do not change imported mesh geometry.
- Child anchors: `CameraFollowTarget`, `SensorAnchor`, `DrillAnchor`, `SampleBayAnchor`, `GarageDockAnchor`, optional `WheelFL/FR/RL/RR`, `HeadlightLeft/Right`.
- If wheels are rigged use wheel animation; otherwise use child-wheel visual rotation only. Never block functionality on absent wheel bones.
- Prefer Rigidbody arcade driving over complex WheelColliders for 24h prototype; stable movement on uneven terrain, controllable inclines; bump/tilt protection; no destructive crashes.

### Controls (keyboard/gamepad/mobile optional)
- `W/S`: forward/reverse; `A/D`: steer; `Space`: gentle brake; `E`: interact/dock; `F`: scan; `R`: sample/drill (if in range and stationary); `Tab`: mission/map panel; `H`: NOVA hint; `Esc`: pause.
- Input System if present; otherwise use compatible existing controls. Never introduce two competing input stacks.
- Follow camera with adjustable pitch and collision avoidance. Camera should not clip through terrain or hide UI.

### Default game-only balancing constants (ScriptableObject adjustable)
- Battery capacity = 100 units; charge dock = +20 units per simulated minute; cruise speed = 6 m/s; reverse = 3 m/s; turn = 90 deg/s; downhill/slope affects consumption; scan cost = 3 units; drilling cost = 8 units; lights cost = 0.2 units/min.
- Driving energy per meter `E = meters * baseCostPerMeter * (1 + slopeFactor + roughnessFactor + dustPenalty)`; tune `baseCostPerMeter` to mission scale, NOT a NASA measurement.
- Battery soft warning at 35%; at 20%, NOVA recommends return; at <10% disable optional drilling and offer `Emergency Tow` (small KP penalty, no catastrophic fail).
- `autonomy`: simple waypoint or follow-guide optional upgrade, not autonomous real scientific navigation.
- Speed cap on steep terrain; disabled drill unless rover is stopped. Stuck detection >5 s offers `Recover Rover` to nearest safe waypoint. Reset must not duplicate rewards.

### Garage upgrades (extend B18 rather than add duplicate)
| Tier | Name | Unlock / player action | Effect (balance value) |
|---|---|---|---|
| L1 | Starter Rover Bay | Assign / deploy / recall / dock / recharge | Base scanner, 2-sample storage, basic map |
| L2 | Sampling Arm | Spend KP + parts; install arm | Drill usable; 4 samples; shorter scan delay |
| L3 | Long-Range Battery | Spend KP + parts; upgrade pack | 140 battery units; 20% lower drive energy |
| L4 | Smart Terrain Scanner | Spend KP + research; install | Highlights traversability risk and candidate geology; display confidence, not guaranteed discovery |
| L5 | Assisted Navigation | Spend KP + research; install | Waypoint assist + optional base solar-panel cleaning dispatch (respect existing E05 unlock) |

Garage buttons: `Inspect Rover`, `Charge`, `Repair`, `Load Sample Tubes`, `Choose Mission`, `Deploy`, `Recall / Emergency Tow`, `Upgrade`, `Read Science`. Garage builds existing rover prefab. Disallow deployment during a specific unsafe radiation-alert scenario if mission rules require shelter; dust restricts visibility/efficiency instead of automatically destroying rover.

## 3. Field science interactions
### 3.1 Scan (default interaction)
Drive to within 4 m; stop; hold F for 2 s; show non-technical sensor animation; reveal `SampleCandidate` info card: rock name/type, why scientists care, evidence level, nearest next waypoint, NASA source button. Deduct scanner battery once. Scanning should *not* automatically award physical sample.

### 3.2 Drill / collect
After scanning, if `sampleCollectible` and tier permits: hold R for 3 s, start drill visual/audio, consume battery and one empty sample tube; store sample in rover inventory. If not upgraded, allow pickup of loose regolith via scoop (starter missions). Wrong-target drilling gives feedback rather than destructive failure. Collection triggers mission event and updates map icon.

### 3.3 Photograph and annotate
Optional photo action records a still from scene camera and attaches in-game `photoId`/marker/label. For MVP use a stock UI thumbnail or icon; don't claim real NASA imagery was recorded by this rover. Capture 1 sample photo for bonus KP; cap rewards and prevent repeat farming.

### 3.4 Bring samples home
Dock in `RoverGarageDockTrigger` → unload via `Deliver Samples` → each sample becomes `SampleRecord` in Research Lab, yields one-time KP, contributes research points, and unlocks optional encyclopedia cards. Sampling never magically generates power/food/water; resulting tech benefits must require research and costs.

### 3.5 Scanner results and honesty
- `observed`: rover simulation's result within this game, with predefined category/certainty; not a NASA measurement at the fictional location.
- `NASA_reference`: references real Perseverance sample categories and selected examples.
- `historical_mission`: if matching actual NASA sample, show NASA's factual name/sol/site; do not assign it to a fictional site.

## 4. Sample library: 8 types and interactions
All samples spawn as *candidate science targets* in a curated playable zone, with game-defined coordinates. Distribution must not be claimed to be a real Mars geological survey unless using verified georeferenced records.

| ID | Player-facing name | Scientific concept | Interaction | Gameplay use | NASA evidence |
|---|---|---|---|---|---|
| S01 | Basalt / Volcanic Rock | Igneous rock records volcanic history | scan + drill | 80 KP first return; Unlock Geology Card | Perseverance igneous cores |
| S02 | Layered Sedimentary Rock | Layers may preserve environmental history | scan + drill | 110 KP; Research Lab Geology | Perseverance sedimentary cores |
| S03 | Regolith (Martian Soil) | Loose dust/grains can vary and complicate equipment | scoop + analyze | 45 KP; Dust Filter research progress | Perseverance regolith samples |
| S04 | Carbonate-bearing Rock | Carbonates can preserve clues about water-related processes | scan + drill | 120 KP; water-history science card | Perseverance carbonate-bearing sample descriptions |
| S05 | Clay-bearing Outcrop | Some clays form through water-rock interaction | scan + optional drill | 120 KP; hydration clue card | NASA Mars minerals science (requires source review) |
| S06 | Iron-rich Red Dust | Iron oxides contribute to Mars's appearance | scoop + analyze | 40 KP; solar dust cleaning tutorial | NASA Mars environmental science |
| S07 | Pebble Field | Mixed rounded/fragmented material offers transport clues | photo + scan | 50 KP; unlock route | NASA rover geologic descriptions |
| S08 | Ice/Hydration Candidate | Signal consistent with possible water-related material, **not confirmed drinkable water or exposed ice** | remote scan only | 140 KP; unlock optional Water Research | NASA Mars water/ice science; need confirmation |

KP above are *balancing*, not scientific findings. Example NASA real sample names may appear on optional museum-style cards: **Montdenier** (igneous), **Melyn** (sedimentary), **Crosswind Lake** (regolith), **Comet Geyser** (silica-cemented carbonate); do not make player collect the actual named NASA sample in a fictional location.

## 5. Exploration map and sites
Start with ONE existing Mars terrain, 150–250 m across if performance allows, with 5 points of interest. Prefer site-inspired layout, never describe as an exact-scale reconstruction without DEM/georeferencing.
- POI-A **Rover Garage / Base**: safe docking, repairs, samples delivery.
- POI-B **Red Ridge**: easier volcanic sample, tutorial line-of-sight.
- POI-C **Ancient Layers**: layered sedimentary outcrop, 2 candidate scan targets.
- POI-D **Dust Flats**: soil/regolith + lower traction + one weather sensor to repair.
- POI-E **Hidden Basin**: harder slopes + water-history clue; optional mission finale.
- Two routes from base: Safe Route (longer, lower roughness) and Shortcut (shorter, higher roughness and energy cost). Add on-map labels and slope hazard highlights.
- Dust event intensity may be fed from existing Mars weather **scenario system**; **DONKI solar event data must not drive dust opacity**.

## 6. New missions — complete objective/state transitions
Each stage: objective marker, interactable trigger, NOVA line, completion event, fallback route. Rewards once per mission first-clear; repeat attempts can award capped bonus science points if desired. Existing campaign missions remain intact; these are side missions.

### R01 — Wake Up, Explorer! (recommended first playable vertical slice, Level 2)
- Hook: "Commander, our new rover is ready! Can you drive it to the red ridge and bring back your first sample?"
- Prerequisites: Garage constructed or present; no drilling upgrade needed.
- S0 Brief: click Garage → Inspect → Charge to at least 65 battery → Deploy.
- S1 Training: drive through 3 simple ring waypoints (brake and steering tips); no fail timer.
- S2 Locate: go to Red Ridge, stop at glowing target, scan (F).
- S3 Sample: collect loose regolith via scoop; sample bay inventory 1/2.
- S4 Return: follow safe route home; if battery low, NOVA guides to a shorter *safe* return; allow emergency tow.
- S5 Dock/Deliver: dock, press Deliver Samples; Research Lab card unlocked.
- Win: dock + sample delivered; Reward 100 KP + `Mars Soil Explorer` badge + R02 unlocked.
- Problems: early departure without charge → garage hint; drive off-route → boundary warning & turnback marker; sample bay full → unload first; low battery → rescue option.
- NASA card: NASA Perseverance collects regolith and rock samples; our XR-1 is fictional educational rover.

### R02 — Secrets in the Layers (Level 3)
- Hook: "These rocks have stripes! Can their layers tell us something about ancient Mars?"
- Prerequisites: R01; drilling arm L2 **OR** allow a non-destructive scan-only completion with reduced KP (avoid progression softlock).
- S0 Select: choose `Ancient Layers` from mission map; load 1 tube if drilling.
- S1 Travel: choose Safe Route vs Rocky Shortcut; visible predicted energy cost is gameplay estimate.
- S2 Scan: scan three rock targets; compare `Volcanic`, `Layered`, `Loose Soil` cards using big simple icons.
- S3 Decide: choose sedimentary candidate and photograph; optionally drill sample if unlocked.
- S4 Return: dock and submit data/sample.
- Win: correct category selected + returned; 140 KP; unlock `Ancient Mars` museum card and incremental Research Lab progress.
- Retry: wrong candidate → NOVA prompts to compare layers; do not fail mission entirely.

### R03 — Rover vs Red Dust (Level 4, reuses existing M03 and E02)
- Hook: "Dust is covering the instruments. Before the storm gets worse, can you inspect our weather sensor?"
- Prerequisites: dust crisis or M03 completed; mission can run as historical training scenario even with clear weather.
- S0 Garage: check charge, equip repair kit (existing Parts inventory).
- S1 Navigate to Dust Flats; low visibility/light dust VFX, short route, no sudden damage.
- S2 Scan weather sensor; interact `Repair` mini-task: click two colored connectors + use 1 repair kit.
- S3 Optional sample: one dust scoop (costs 4 battery, yields dust science card).
- S4 Return; Garage repairs or cleans rover sensor if dusty.
- Win: weather sensor working and docked; 170 KP; Weather Station gets `Calibrated Sensor` + earlier scenario warning (game-balance only).
- Integration: E02 mission completion flags should not be duplicated; if E02 already repaired sensor, spawn an alternative sensor for rover mission or mark it as inspection/calibration. Do not retroactively undo repairs.

### R04 — Water Clues, Not Water Tanks (Level 6)
- Hook: "Our instruments found an interesting sign. Does it prove there's ice nearby? Let's investigate!"
- Prerequisites: R02 + Smart Scanner OR allow a basic scan and make advanced confidence overlay optional.
- S0 Scan map of Hidden Basin; choose candidate A, B or C; each differs in terrain difficulty and evidence-card rating.
- S1 Drive to first candidate, scan and record clue (NOT potable water claim).
- S2 Decide: safer return with 1 finding vs use battery to reach another candidate to increase research confidence.
- S3 Optional second scan; no guarantee ice; NOVA explains uncertainty.
- S4 Return and submit findings; Lab unlocks Water Research card but no free water generated.
- Win: deliver >=1 verified in-game scan; 190 KP; +Water Research progress.
- Safety: if battery projected below return reserve, UI displays return suggestion and optional emergency tow.

### R05 — The Missing Data Drive (Level 8–9, connects existing E05)
- Hook: "The rover's memory pack holds valuable science data, but a wheel sensor stopped responding!"
- Prerequisites: existing E05 enabled or preconditions met; choose either EVA rescue or garage maintenance version. Do not create duplicate competing rover objects.
- S0 Diagnose: garage or field diagnostics show `wheel sensor fault` (fictional scenario).
- S1 If field mission: drive support rover/astronaut to fault location; if same XR-1 is stranded, use EVA walking repair route instead.
- S2 Choose `Retrieve Data` (faster, rover stays offline until repair) or `Repair Vehicle` (costs Parts, unlocks automated return).
- S3 Return to garage; submit data to Research Lab.
- Win: data saved + player safe; 220 KP; optional Solar Panel cleaning route unlocked if the existing E05 unlock condition is satisfied.
- Do not offer an impossible scenario in which the only rover drives to repair itself.

### R06 — The Great Mars Field Trip (Level 9–10; optional finale)
- Hook: "Explore three geology zones and bring your best evidence back before a dust event reaches the base."
- S0 Preparation: mission map shows 3 sample sites, rough forecast, base power and rover battery.
- S1 Scan two required types (regolith + sedimentary); optional third sample in Hidden Basin.
- S2 Weather warning begins: visibility and travel energy penalty rise based on a local dust **scenario**, not DONKI.
- S3 Choose stop and return vs bonus sample; safe return is a full-credit decision if base or rover is endangered.
- S4 Dock; Lab report explains how geology, energy, weather and resource priorities connected.
- Win: return with 2 recorded scans, no emergency tow; 300 KP. With tow, partial credit + educational debrief; cannot become irrecoverably stuck.

## 7. Connect to existing missions & base economy
- B18 Rover Garage: sole owner of XR-1 vehicle lifecycle (build/deploy/charge/repair/upgrades). Keep existing building IDs and save IDs.
- B13 Research Lab: `DeliverSample(sampleRecord)` updates research points and shows 3D sample display/cards; no sample duplicates on repeat.
- B17 Weather Station: R03 calibration influences *warning lead time only*, not NASA data itself.
- M03 Red Dust Rising: rover may be deployed to inspect or clean Solar Array after storm if B18/L5 and E05 unlock conditions satisfied; optional bonus objective, never required for original M03 clear.
- M05 Thirsty Colony / E03 Ice Clues: R04 unlocks a **research option** with future upgrade cost, not instant extracted water.
- E01 First Footprints: player learns to scan on foot; R01 revisits same mechanic with rover controls.
- E02 Lost Sensor: R03 cross-links repaired flag safely and respects previous player progress.
- E05 Rescue the Rover: repair/recovery storyline should use same XR-1 model/entity and garage state.
- M09 Domino Effect: if rover available, deploy for maintenance at an electricity/opportunity cost. Optional alternate action; never one free best solution.
- KP/level: new side missions reward KP once each; progression must not require all six missions. Avoid economy inflation by configurable rewards and cap repeated rewards.
- Garage charging drains existing base electricity. Example: transfer `kWh` from Battery Bank; NEVER create rover battery from nothing. If base power insufficient, queued charge shows estimated delay.

## 8. NASA data / scientific provenance: exact allowed usage
The rover story is fictional. Mars terrain from Mars Trek can inform look/slope; actual historic Perseverance samples inform cards/classes; rover payloads are **inspired by** real instrumentation. NASA has not supplied physical sample data for the arbitrary invented in-game POI coordinates.

| Source | URL | Agent should use it for | Restrictions |
|---|---|---|---|
| Perseverance rover components | https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/ | drill, sample handling, rover arm | No copying exact parameters unless confirmed |
| Perseverance science instruments | https://science.nasa.gov/mission/mars-2020-perseverance/science-instruments/ | scanner educational analogies (PIXL, SHERLOC, SuperCam) | Game scan outcomes simulated |
| NASA Mars rock sample catalog | https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/ | factual example sample names, type, sol, place | Preserve cited context; don't transplant named samples into fictitious map |
| Mars Trek | https://trek.nasa.gov/mars/ | Mars geography/elevation/terrain reference | Validate export/download/license; no unsupported live map assumption |
| Perseverance mission home | https://science.nasa.gov/mission/mars-2020-perseverance/ | mission narrative/education | credit NASA and JPL appropriately |
| NASA 3D Resources | https://science.nasa.gov/3d-resources/ | optional reference images or asset library | Team custom 3D assets have priority; check license per asset |
| NASA Open APIs | https://api.nasa.gov/ | space weather DONKI where relevant | **Mars Rover Photos API is archived**; don't rely on it |
| NASA DONKI | https://ccmc.gsfc.nasa.gov/tools/DONKI/ | separate solar weather safety events | Not a dust storm feed |
| Mars science geology | https://science.nasa.gov/mars/ | general science facts and checks | NASA science cards only with explicit references |

**Source manifest fields:** `sourceId, title, url, accessedAt, dataKind (real_observation | scientific_reference | gameplay_simulation), actualSampleId?, narrativeDisclaimer, attributionText`. UI must make the data kind visible via a `NASA Science` button or badge.

## 9. Data schemas and Unity architecture
### C# / SO deliverables (adapt paths to existing structure)
```
Assets/_Survora/Scripts/Rover/RoverController.cs
Assets/_Survora/Scripts/Rover/RoverBattery.cs
Assets/_Survora/Scripts/Rover/RoverGarageAdapter.cs
Assets/_Survora/Scripts/Rover/RoverScanner.cs
Assets/_Survora/Scripts/Rover/RoverSampleCollector.cs
Assets/_Survora/Scripts/Rover/RoverInventory.cs
Assets/_Survora/Scripts/Rover/RoverDockZone.cs
Assets/_Survora/Scripts/Rover/RoverCameraController.cs
Assets/_Survora/Scripts/Rover/RoverStuckRecovery.cs
Assets/_Survora/Scripts/Science/SampleDefinition.cs
Assets/_Survora/Scripts/Science/SampleRecord.cs
Assets/_Survora/Scripts/Science/ResearchSampleDelivery.cs
Assets/_Survora/Scripts/Missions/RoverMissionAdapter.cs
Assets/_Survora/Data/Rover/RoverConfig.asset
Assets/_Survora/Data/Samples/S01-S08.asset
Assets/_Survora/Data/Missions/R01-R06.asset
Assets/_Survora/Prefabs/Rover/RoverRoot.prefab [REFERENCE EXISTING TEAM MODEL]
Assets/_Survora/Prefabs/Science/ScanNode.prefab
Assets/_Survora/Prefabs/UI/RoverHUD.prefab
Assets/_Survora/Tests/EditMode/RoverEnergyTests.cs
Assets/_Survora/Tests/EditMode/SampleRewardTests.cs
Assets/_Survora/Tests/PlayMode/RoverMissionFlowTests.cs
```

### Canonical record shape
```json
{
  "sampleId": "S02_AncientLayers_001",
  "definitionId": "S02",
  "displayName": "Layered Sedimentary Rock",
  "mapPointId": "POI-C",
  "scanState": "scanned",
  "collected": true,
  "delivered": false,
  "firstClearKp": 110,
  "provenance": {
    "dataKind": "gameplay_simulation",
    "referenceUrl": "https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/"
  }
}
```

### Event names (use EventBus or existing equivalents)
`RoverDeployed`, `RoverEnteredZone`, `RoverStopped`, `RoverScanCompleted`, `RoverSampleCollected`, `RoverBatteryLow`, `RoverDocked`, `SampleDelivered`, `RoverRepaired`, `RoverMissionCompleted`. Missions subscribe/unsubscribe safely. Use unique mission/run IDs and immutable delivered sample IDs to prevent KP farming and save/load duplication.

### Mission persistence
Store `garageLevel, roverBattery, roverHealth, roverDocked, roverCurrentWaypoint, roverUpgradeIds, collectedSampleIds, deliveredSampleIds, roverMissionStates, roverMissionRewardClaimedFlags, roverLastSafeCheckpoint`. Migration: if existing saves don't contain rover fields, initialize defaults without deleting old data.

### NOVA context and prompt guardrails
Send structured, allowlisted values: `activeMissionId, roverBatteryPct, estimatedReturnCost, roverHealth, sampleBaySlotsFree, lastScannedSampleType, dustEventSeverity, nearestSafeWaypoint, baseEnergyReserve, currentObjective`. NOVA should be short, friendly, give hints not play automatically, cite actual source titles for science explanations, never invent measurements or promise ice/life found. Offline fallback messages required for every mission phase.

## 10. User interface and visual feedback
- `Rover HUD`: top-left mini-map + destination arrow; bottom-left speed/traction; bottom-center battery bar + sample bay slots; right contextual F Scan/R Drill/E Dock; top-right mission objective.
- `Scan Card`: sample icon + two lines child-readable facts + optional `What NASA Learned` expand link.
- `Garage Panel`: 6 actions, upgrade tier table, battery transfer amount; disabled states explain why.
- `Research Lab`: delivered samples gallery, unlocked knowledge cards, next tech progress.
- `Mission Board`: new `Rover Exploration` tab. Old Base/EVA mission tabs unchanged.
- Low battery: yellow at 35%, red at 20%, safe recovery always reachable. No flashing panic effect or jumpscare.
- All new HUD elements should use current game's UI style; no unrelated new visual theme.

## 11. Prioritized implementation plan
**P0 (playable):** Inspect project, map custom rover model to existing garage, drivable controller/camera, 3 POIs, scan regolith, collect, return/dock, Research Lab delivery, R01 complete, NASA provenance card, saves, automated smoke tests.

**P1:** Add 8 sample types, 6 POIs/scan variants, scanner/drill upgrades, R02/R03, dust scenario integration, NOVA dynamic context, base power charging.

**P2:** R04–R06, assisted navigation, advanced map overlays, camera/photo log, optional scene transitions, polish and performance.

### Acceptance checklist
- [ ] Existing base and old missions function without regression.
- [ ] Custom team rover mesh used; no team asset deleted/replaced.
- [ ] Rover can deploy/drive/brake/scan/scoop/return/dock.
- [ ] Research Lab receives exactly one sample per unique sample record.
- [ ] Garage charge draws from existing base electricity.
- [ ] One successful R01 playthrough from start to returned sample, including save/load.
- [ ] Low battery cannot hard-lock game.
- [ ] Science card links show genuine NASA source and mark fictional game results.
- [ ] Local offline mission flow works even if NASA websites are down.
- [ ] E05 Rescue the Rover does not create a contradictory second rover.
- [ ] No Unity compile errors; log tested Unity version and any missing packages/assets.

## 12. Ready-to-paste implementation instruction
> Implement this as an **additive Rover & Samples feature** inside the EXISTING SURVORA Unity project. Inspect current scenes/assets/scripts first; preserve all custom 3D models and current systems. Extend the existing Rover Garage (B18), EVA exploration, Research Lab, KP, NOVA, dust/weather simulation and E05 rescue mission; do not create redundant parallel managers. Build P0 end-to-end first: existing rover model → drivable rover → scan regolith → collect sample → return and dock → deliver to Research Lab → KP + NASA source card → save/load, with actual PlayMode verification. Then do P1/P2. If the project lacks a needed asset, use a clearly labeled temporary primitive without modifying team assets, and record the dependency. Never claim fictional scan results are live NASA measurements. Before finalizing, report files changed, test outcomes, incomplete features and actual playable status.
