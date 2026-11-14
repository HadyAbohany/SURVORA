# SURVORA — Unity Master Development Specification (v3)

> **PRIMARY IMPLEMENTATION CONTRACT — Give this file to the coding agent integrated with Unity.**
>
> Version: 3.0 | Date: 2026-11-13 | Platform: Unity 3D (isometric base + third-person EVA) | Audience: ages 7–12 | Language: Arabic Egyptian UX + English IDs | Status: **design specification, not claims of finished functionality**.
>
> **Science honesty:** All `BALANCE_*` example parameters, percentage meters, resource costs, KP rewards, timers, and crisis thresholds are proposed **gameplay values**, NOT measured NASA data. Real data is explicitly cited and tagged by provenance. Do not invent measurements, assets, or API responses. **NASA does not endorse SURVORA.**

## 0. AGENT INSTRUCTIONS — READ FIRST

1. Inspect the existing Unity project, installed packages, render pipeline, scenes, prefabs, scripts and assets **before modifying** anything. Do not destroy/replace a working project or scenes. Prefer additive changes and reusable components.
2. Implement actual working gameplay, not just mock UI or placeholder methods. Every button/action must change authoritative game state and the visuals.
3. Work milestone-by-milestone: A) base+HUD+tick, B) buildings+grid+power/O2, C) mission state machine and M01–M03, D) dust storm and repairs, E) EVA E01/E02, F) NASA snapshot import and evidence UI, G) AI assistant with deterministic fallback, H) remaining systems and missions. Maintain compilation after each milestone.
4. Preserve prefab references, serialization, scene metadata, `.meta` files, and GUIDs. Confirm Unity version/URP vs Built-in. Do not import unverified third-party packages.
5. Keep simulation in local C# domain code, deterministic and unit-testable. AI never calculates or changes resource truth. NASA data is fetched in editor/backend/preprocessing, then parsed into **versioned local snapshots** for offline-first playback; optional live refresh should not block gameplay.
6. Do not attempt to scrape NASA web portals from Unity, fabricate JSON, embed private API keys in client builds, or pretend a source is live when bundled. Implement clear error/fallback UI.
7. Implement **Explorer age 7–9** and **Commander age 10–12**. Children's failures must have recoverable checkpoints and no punitive, irreversible death sequences. Accessibility: readable typography, subtitles, colors+icons, no mandatory reading-heavy mechanics, pause.
8. Asset usage: verify licensing, attribution, geometry, formats, performance; NASA 3D models are often high-poly and may require manual Blender optimization. No automatic assumption that a rover model is a complete runnable Unity character.
9. If actual NASA download/connection is unavailable, create `SourceStatus=Unverified/Unavailable`, data schema and import workflow. Never claim fetched values without evidence.
10. Deliver working scenes, prefabs, data assets, script tests, source attributions, README, explicit known gaps and a playable vertical slice before expanding scope.

### Project acceptance in one sentence

A child can build a small Mars base, experience a dust storm that decreases modeled solar power and causes a genuine electricity/O2 trade-off, repair the base in an EVA, ask NOVA why it happened, and open a traceable NASA-backed science card.


## 1. Game fantasy, modes and the player's minute-to-minute loop

**Pitch:** You are the commander of SURVORA-1, a young exploratory crew on Mars. Your base survives by balancing energy, oxygen, water, food, repairs and radiation protection. Missions grant **Knowledge Points (KP)** used to unlock technology and base levels, not magical supplies. Every action has a cost. Scenario events can use real NASA archival event metadata. NOVA teaches, not plays for the child.

**Mode A — Base:** camera at tilted isometric angle (rotate 90°, zoom; edge pan or WASD), grid-based building placement, select/tap building, inspect/upgrade/repair/toggle, assign production priorities, prepare missions and crisis response. Initially 16×16 tiles; buildable 13×13; obstacles rocky; beginner highlights valid tiles. One command center + habitat preplaced.

**Mode B — EVA:** short third-person playable 60×60m (or similarly bounded) arena, simple camera follow, walk/jog, interact/scan/fix/pickup, one clear waypoint and return marker. Use suit O2 and battery, temperature/radiation only if unlocked; hard caps on EVA time; pause base simulation for Explorer optional.

**Mode C — Mission Control:** dashboard of alerts, queue of missions, NASA Science Log, current scenarios, event history, upgrades, optional AI panel. An expedition must always be started from the airlock/mission console; do not teleport via unrelated UI.

**Daily cycle:** ~1 game sol = 8 real minutes in full sandbox (tunable); guided missions use scripted accelerated segments, e.g., day→night in 60 seconds. The real Martian sol is about 24h 39m; game acceleration is fiction for accessibility. Resource simulation uses `deltaSimMinutes` independent of frame rate. Offline pause and speed toggles; stop ticking during modals in Explorer.

**Actions:** place, rotate, cancel, demolish with partial refund, assign essential/normal/optional energy priority, switch mode ON/OFF, store/withdraw battery reserve, plant/harvest crops, water/LED light adjustment, replace filter, clean panels, research, repair circuits, shelter crew, queue downlink, dispatch EVA, scan sample, rescue rover, review science evidence, obtain hint, unlock upgrade, retry checkpoint.

**Narrative tone:** upbeat, adventurous, visual cause/effect; no medicalized scare tactics. During alerts: "الخطر بيزيد، عندنا فرصة نتصرف!" rather than "طاقمك هيموت".


## 2. Currency, resources, status, KP, progression

### Canonical units

| ID | Meaning | Unit / range | Initial illustrative balance | Owner |
|---|---|---|---|---|
| `energyKWh` | instantaneous available battery energy | kWh, capped by batteries | `BALANCE_INIT=36` | PowerSystem |
| `powerGenerationKW` | power per sim hour from solar | kW | calculated | PowerSystem |
| `powerDemandKW` | demand from active buildings | kW | calculated | PowerSystem |
| `oxygenKg` | breathable oxygen stored | kg | `BALANCE_INIT=40` | AtmosphereSystem |
| `waterL` | potable water | liters | `BALANCE_INIT=80` | WaterSystem |
| `wasteWaterL` | recyclable reservoir | liters | `BALANCE_INIT=20` | WaterSystem |
| `foodPortions` | edible stored meals | portions | `BALANCE_INIT=32` | FoodSystem |
| `spareParts` | repair/build parts | count | `BALANCE_INIT=25` | Inventory |
| `scienceSamples` | gathered/identified samples | count | 0 | Inventory |
| `nutrients` | hydroponic media stock | count | 12 | Inventory |
| `knowledgePoints` | one-time progression rewards | integer | 0 | Progression |
| `crewSafety` | educational composite status | 0–100 | 100 | CrewSystem |
| `radiationRisk` | game scenario risk index | 0–100 | 10 | HazardSystem |
| `panelDustLoad` | accumulated panel dust fraction | 0–1 | 0.05 | DustSystem |
| `crewCount` | simulated crew | people | 3 | CrewSystem |
| `suitO2` / `suitBattery` | EVA reserves | 0–100% (game) | 100 | EVASystem |

**Do not conflate** percentage HUD values with kilograms or measured dose (μSv/h). For main O2 meter: `oxygenKg / oxygenCapacityKg ×100`; for battery: `energyKWh / storageCapacityKWh ×100`; for Safety use named composite index, not inferred medical diagnosis.

### Starting caps and progression values — game design, not science

- Power: generator 9 kW (full clear-day example), battery storage 60 kWh; base load 4.0 kW (habitat 1.0, oxygen 2.0, command 0.5, others optional). Values illustrative: adjust with tests.
- Oxygen capacity 100 kg; when initial O2 40 kg and crew consumes an illustrative `0.6 kg/simHour` total, early missions have a visible runway. **Do not present these as NASA astronaut needs**.
- Water cap 200 L; food cap 80 portions; a crew consumes illustrative 3 meals per sol; scripted time is accelerated so resources do not suddenly evaporate during dialog.
- KP: M01 100, M02 150, M03 200, M04 180, M05 200, M06 250, M07 300, M08 250, M09 350, M10 500. E01 60, E02 150, E03 180, E04 200, E05 250. First completion only; replays zero KP or a capped badge bonus.
- Research unlock gate levels: L1 0 KP, L2 100, L3 250, L4 450, L5 630, L6 830, L7 1080, L8 1380, L9 1630, L10 1980 (cumulative examples, based on completing prior mandatory missions only; optional EVA bonuses are not required). Check mission gates against actual reward timing in tests.

### Progression contract

Building upgrades require **both** KP research unlocks and parts/material costs; spending KP is optional design choice. For simplicity, **KP are cumulative XP, never spent**; upgrades consume Parts and optionally samples, and require current base level. Thus no soft locks. Missions unlock in chapter order; optional EVA can grant upgrade materials, not essential impossible-to-replace items. Campaign progression never depends on querying the live internet.


## 3. Building taxonomy and ALL building actions (implementation inventory)

Each building has: `buildingId`, `displayNameAr`, `category`, `footprint`, `maxLevel`, `baseCostParts`, `maxHealth`, `powerDemandKW`, `outputRate`, `priority`, `onOff`, `storage`, `state`, `requiredBaseLevel`, `upgradeCosts`, `linkedAlerts`, `interactiveButtons`, `visualStates`, `scienceSourceIds`.

**Common actions across buildings:** Select/Open panel; Info; ON/OFF (except essential command/shelter safety); prioritize power (Essential/Normal/Optional); Upgrade (if unlocked and afford cost); Repair (if health <100); View scientific explanation; View connections. No “upgrade” button without effect. Every button must be disabled with a reason when invalid.

### Full base catalog (16 buildables + 4 environmental/mission objects)

| ID | Building | Footprint | Start/unlock | Role | Primary player controls |
|---|---|---|---|---|---|
| B01 | Command Center | 3×3 | prebuilt L1 | mission control, tech tree, alerts | mission board, research tree, priorities, pause automation, weather/history |
| B02 | Habitat | 3×3 | prebuilt | crew housing, air and energy demand | inspect crew, emergency conservation, O2 ration, safety report |
| B03 | Solar Array | 2×2 | L1 | power production | build panels, clean, deploy extra array, inspect dust and weather |
| B04 | Battery Bank | 2×2 | M01/L2 | buffer energy | choose charge reserve 10/25/40%, night reserve, switch battery mode |
| B05 | Oxygen Plant | 2×2 | M02/L2 | produce O2 via future scaled MOXIE-inspired unit | normal/eco/boost, inspect output/input, maintenance |
| B06 | Oxygen Tank | 1×2 | L2 | O2 inventory capacity | attach/inspect storage, emergency refill routing |
| B07 | Power Junction | 1×1 | L4 | electrical connectivity | repair damaged node, reroute priorities, inspect connected loads |
| B08 | Maintenance Workshop | 2×2 | L3 | convert collected salvage into repair kits | craft one repair kit, repair queue, dispatch drone |
| B09 | Water Recycler | 2×2 | M05/L5 | reclaim water | eco/normal, replace filter, prioritize water, inspect wastewater |
| B10 | Water Storage Tank | 1×2 | L5 | water cap | inspect water, reserve amount, leak repair |
| B11 | Greenhouse | 3×3 | M06/L6 | grow limited fresh produce | choose crop, plant, irrigate, LED mode, harvest, remove unhealthy crop |
| B12 | Food Storage | 2×2 | L6 | meal inventory | inspect shelf, reserve meals, ration nonessential usage |
| B13 | Research Lab | 2×2 | M02/L2 | analyze samples and unlock science cards | research queue, pause for power, analyze sample, see KP status |
| B14 | Radiation Shelter | 3×3 | M07/L7 | move people under protective shielding | open shelter, move crew, preparedness, shield inspection |
| B15 | Communication Relay | 2×2 | M08/L8 | store and forward uplink batches | queue send, inspect link window, save transmission, pause for energy |
| B16 | EVA Airlock | 2×2 | E01/L2 | expedition access | select EVA, prepare suit, loadout, return/debrief |
| B17 | Weather & Radiation Station | 2×2 | L3 | dust hazard and solar activity cards | inspect forecast, archived NASA event card, calibrate alerts |
| B18 | Rover Garage | 3×2 | E05/L9 | maintain rover and clean solar arrays | dispatch rover, recharge, repair, select cleanup route |
| O01 | Mars rock deposits | 1–3 tiles | world object | sample sites | EVA scan, harvest one-time sample |
| O02 | Faulty sensor beacon | 1 tile | E02 | repair objective | scan, fix, return telemetry |
| O03 | Ice indicator sites | 1 tile | E03 | contextual water-science investigation | compare readings; not guaranteed actual ice extraction |
| O04 | Storm/radiation warning overlay | UI/world | events | visual hazards | warn, inspect source and status |

**Asset fallback:** if no 3D prefab exists for a building, construct a tidy placeholder with Unity primitives/materials + floating icon; NEVER omit functionality because an art asset is missing.


### Precise building panels: levels, actions, inputs, conditions

**Upgrade-cost rule:** use shared `UpgradeCostByTier = {2: 8 Parts, 3: 14 Parts, 4: 22 Parts, 5: 32 Parts}` as default BALANCE values; overrides for big buildings in ScriptableObjects. Upgrade requires `baseLevel >= desiredTier` and no active repair. Show a before/after comparison. All max levels=5 except objects. Values described as +% are illustrative modifiers to balance in playtests. Effects must be implemented and covered by tests.


#### B01 Command Center
- **Player buttons and interactions:** Open mission board, choose next scenario, view KP unlock tree, inspect NASA Data Library, set life-support priority, toggle optional auto-pause, inspect event log.
- **Tier upgrades (L1→L5):** L1 basic notifications; L2 predictive hazard cards (earlier warning); L3 power priority presets; L4 mission control automation (auto-pause research on critical O2); L5 summary analytics and replay comparison.
- **Simulation constraints & failure behavior:** Receives simulated radio/alert requests, consumes small power; losing power delays optional status reports but critical HUD remains available.
- **Mission dependencies:** M01, M03, M09, M10.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B02 Habitat
- **Player buttons and interactions:** Review 3 crew icons, read breathable reserve, see temperature and safety, select conservation mode, request shelter transfer.
- **Tier upgrades (L1→L5):** L1 3 crew; L2 insulated walls reducing heater demand; L3 efficient air cycling; L4 backup emergency atmosphere reserve; L5 comfort/crew efficiency bonus.
- **Simulation constraints & failure behavior:** Always consumes O2 and power; on sustained deficit crewSafety declines after grace period; prevents death imagery.
- **Mission dependencies:** M01, M02, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B03 Solar Array
- **Player buttons and interactions:** Deploy panel, review power graph, clean manually (parts + action time), dispatch rover if unlocked, toggle diagnostic overlay.
- **Tier upgrades (L1→L5):** L1 rated example 9 kW; L2 +25% clear-sky generation; L3 dust-repellent coating reduces accumulation; L4 dual-axis tracking boosts effective daylight harvest; L5 extra panel module, with higher repair footprint.
- **Simulation constraints & failure behavior:** Light curve × atmospheric attenuation × surface dust × health. Storm reduces light; deposition persists until cleaning; no night power.
- **Mission dependencies:** M01, M03, E02, E05.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B04 Battery Bank
- **Player buttons and interactions:** Set emergency reserve, inspect charging/discharging and time-to-empty, enable battery saver, expand cells.
- **Tier upgrades (L1→L5):** L1 60 kWh; L2 +30 kWh; L3 better roundtrip efficiency; L4 emergency priority output; L5 +40 kWh and advanced reserve scheduling.
- **Simulation constraints & failure behavior:** Never creates energy; charge only from surplus; discharge only if available; charge/discharge capped.
- **Mission dependencies:** M01, M03, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B05 Oxygen Plant
- **Player buttons and interactions:** Check INPUT power and OUTPUT oxygen, Eco/Normal/Boost, repair, pause for diagnostics.
- **Tier upgrades (L1→L5):** L1 standard; L2 +20% modeled output per kWh; L3 wear reduction; L4 secondary stage; L5 emergency oxygen burst with cooldown and extra power.
- **Simulation constraints & failure behavior:** Derived from proposed future scalable atmospheric CO2 conversion, not actual MOXIE life-support capacity; partial power lowers generation; no instantaneous O2 when plant off.
- **Mission dependencies:** M02, M04, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B06 Oxygen Tank
- **Player buttons and interactions:** View level, increase capacity, enable emergency-only withdrawal priority.
- **Tier upgrades (L1→L5):** L1 +60kg storage; L2 +40kg; L3 leak-resistant seals; L4 reserve alert; L5 redundant storage.
- **Simulation constraints & failure behavior:** Tank stores O2 and can leak if damaged; no production.
- **Mission dependencies:** M02, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B07 Power Junction
- **Player buttons and interactions:** Inspect network path, repair damaged cable by two-node connection mini-puzzle, activate temporary bypass.
- **Tier upgrades (L1→L5):** L1 junction; L2 stronger cable; L3 alternate route; L4 fault diagnostics; L5 auto reroute.
- **Simulation constraints & failure behavior:** Disconnected buildings have no supply even if power total is positive; if detailed cabling too expensive, represent as a boolean `connected` flag and 2-click repair.
- **Mission dependencies:** M04, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B08 Maintenance Workshop
- **Player buttons and interactions:** Convert 2 salvage into 1 repair kit, queue repair, craft filter, dispatch drone.
- **Tier upgrades (L1→L5):** L1 one queue slot; L2 -1 parts repair costs; L3 2 slots; L4 cleanup drone; L5 auto-repair prioritization.
- **Simulation constraints & failure behavior:** Uses power and parts; cannot mint free parts.
- **Mission dependencies:** M03, M04, E05.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B09 Water Recycler
- **Player buttons and interactions:** Check wastewater reservoir, replace filter, Eco/Normal mode, emergency preservation.
- **Tier upgrades (L1→L5):** L1 example 70% game recovery; L2 80%; L3 reduced energy; L4 90%; L5 95% illustrative (NASA ISS 98% is demonstration in other hardware, not Mars prediction).
- **Simulation constraints & failure behavior:** Recycling requires recoverable wastewater input; never creates extra water from nothing. Filter wear reduces actual recovery.
- **Mission dependencies:** M05, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B10 Water Storage Tank
- **Player buttons and interactions:** Inspect reserves; prioritize drinking; fix leak; adjust farm water access.
- **Tier upgrades (L1→L5):** L1 +100L cap; L2 +50L; L3 lower leak chance; L4 dedicated drinking reserve; L5 +100L.
- **Simulation constraints & failure behavior:** Storage not a source; safety water remains reserved unless emergency.
- **Mission dependencies:** M05, M06.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B11 Greenhouse
- **Player buttons and interactions:** Select lettuce/pea/tomato as abstract game crop types, plant, allocate LED power, choose water flow Low/Normal/High, harvest.
- **Tier upgrades (L1→L5):** L1 one plot; L2 two plots; L3 efficient LEDs; L4 nutrient recirculation; L5 climate control and three plots.
- **Simulation constraints & failure behavior:** Crop stages Seed→Sprout→Growing→Ready; stress if no water/power, recoverable for limited time; greenhouse food supplements but does not replace all meals early.
- **Mission dependencies:** M06, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B12 Food Storage
- **Player buttons and interactions:** View portions, reserve emergency meals, inspect spoilage if power lost, ration optional meals.
- **Tier upgrades (L1→L5):** L1 +60 portions; L2 +40; L3 food preservation lowers waste; L4 emergency allocation; L5 +60.
- **Simulation constraints & failure behavior:** No crop production; spoilage is optional in Commander mode only and clearly telegraphed.
- **Mission dependencies:** M06, M10.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B13 Research Lab
- **Player buttons and interactions:** Choose research job; deposit sample; pause/resume; view tech card; spend samples to unlock scientific discoveries.
- **Tier upgrades (L1→L5):** L1 basic scan; L2 shorter processing; L3 extra queue; L4 lower power demand; L5 bonus science cards, NOT repeatable infinite KP.
- **Simulation constraints & failure behavior:** Needs power and samples; outputs science progress and campaign milestones, but does not override mission-granted KP system.
- **Mission dependencies:** M02, M08, M10.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B14 Radiation Shelter
- **Player buttons and interactions:** Activate precaution, send crew inside, monitor shelter capacity and mission EVA lockout, end only after safe condition.
- **Tier upgrades (L1→L5):** L1 capacity 3; L2 better abstract shielding factor; L3 lower utilities; L4 extra capacity; L5 preparedness indicator.
- **Simulation constraints & failure behavior:** Risk index is game-only; ensure all crew shelter in high-risk tutorial; no claim of precise Mars dose from DONKI events.
- **Mission dependencies:** M07, E04.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B15 Communication Relay
- **Player buttons and interactions:** Queue science packet, check available link, transmit when window available; choose power-saving/offline cache.
- **Tier upgrades (L1→L5):** L1 packet queue; L2 larger queue; L3 shorter transmission duration; L4 battery-safe burst; L5 redundant antenna.
- **Simulation constraints & failure behavior:** Earth/Mars communication has light-time delay; demo uses scripted communication windows, not live DSN availability.
- **Mission dependencies:** M08, M10.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B16 EVA Airlock
- **Player buttons and interactions:** Open mission list, choose loadout (repair kit/scanner/sample case), view O2 and battery, launch expedition, return/debrief.
- **Tier upgrades (L1→L5):** L1 basic 100% suit; L2 +20% battery; L3 improved scanner; L4 emergency waypoint guidance; L5 sample capacity.
- **Simulation constraints & failure behavior:** Cannot launch during dangerous space-weather scenario unless a scripted educational consequence; no infinite suit refill away from base.
- **Mission dependencies:** E01–E05.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B17 Weather & Radiation Station
- **Player buttons and interactions:** View dust forecast, atmospheric transparency card, historical NASA solar event and provenance, calibrate warning radius.
- **Tier upgrades (L1→L5):** L1 basic warning; L2 earlier dust warning; L3 clearer science overlay; L4 alert routing; L5 historical replay library.
- **Simulation constraints & failure behavior:** Dust and solar warnings are separate event types and separate sources.
- **Mission dependencies:** M03, M07.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


#### B18 Rover Garage
- **Player buttons and interactions:** Dispatch rover to dust cleanup, inspect charge, run diagnostics, repair rover, choose target.
- **Tier upgrades (L1→L5):** L1 manual dispatch; L2 shorter cleaning time; L3 larger battery; L4 remote rescue; L5 route automation.
- **Simulation constraints & failure behavior:** Rover needs energy and safe route; disabled during certain crisis.
- **Mission dependencies:** E05, M09.
- **UI contract:** building name and image; level/health; input vs output per tick; connected/offline/underpowered/maintenance state; priority toggle; capacity/storage where relevant; Repair and Upgrade cost; NASA Science button showing verified reference or "Based on engineering model". Progress operations with cancel/complete and clear feedback.


## 4. Construction, technology, environment, pathfinding

**Placement:** Unity grid coordinates, snapping, footprint validity, overlap/collision checks, costs checked before confirming. Ghost green/red with text reason. On placement assign GUID (string), building `typeId`, grid position, rotation and level. Starter buildings are preplaced; do not double charge. Salvage on demolish: 50% of initial Parts (BALANCE), no refunds for mission-critical preplaced buildings. Building tiles cannot block EVA airlock access. Provide pathways visually but no elaborate pathfinding unless actual need.

**Electrical model:** choose easy centralized power bus for MVP (all connected by default except junction-fault mission), then add explicit junction connectivity. Each tick allocate generation first then battery by priority category: Essential [Habitat, O2, Command], Normal [Water, Shelter during event], Optional [Lab, Greenhouse extra LEDs, Relay]. If essential load exceeds supply, allocate proportionally or use explicit configurable `lifeSupportFirst` and show consequences, never generate negative storage.

**Tech tree:** Base tier unlock via cumulative KP; building type unlock via mission and tier; upgrades via Parts; map node data: id, label, desc, prerequisites, reward (new building/level/capacity/effect), costs, science card. Example edges: Energy Management→Battery Reserve→Dust Shields; Air Chemistry→Oxygen Efficiency→Emergency O2; Water Recycling→Hydroponics→Farm LEDs; EVA Basics→Sensor Repair→Rover Garage; Solar Weather→Shelter→Safety Automation.

**Map aesthetics:** stylized low-poly Mars, warm orange sand, cool blue UI, clear night lighting; dust storm gradually reduces visibility, but never makes navigation inaccessible for children. Terrain masks and satellite map textures from Mars Trek only when downloaded/processed and attributed. Generated gameplay terrain ≠ exact Mars DEM unless explicitly georeferenced.

**Weather:** exactly two categories: `DustStormScenario` (Mars atmospheric light and panel deposits) and `SolarParticleScenario` (space weather/radiation preparedness). Solar event may cause communication-science discussion but does not automatically reduce solar panels, create dust, or imply Mars location impact.


## 5. Unified simulation model — deterministic C# domain rules

### Tick and flow order

`SimClock` accumulates `Time.deltaTime × timeScale` and ticks every 1 simulated minute (example). Tick order: process scheduled events → compute weather and sun factor → compute load demand and solar generation → battery & power allocation → building outputs (O2/water/food/science) → crew consumption → EVA equipment → wear and failures → check thresholds → update mission triggers → emit state-change events → UI refresh. If paused, no ticking. No duplicate consumption inside `Update()` and missions.

### Formula design (all rates in consistent kW/kWh per simulation hour)

```
solarPowerKW = sum(panelRatedKW * max(0, sunElevationFactor)
    * skyTransmission * (1 - panelDustLoad)
    * healthFraction * upgradeMultiplier)

surplusKW = max(0, solarPowerKW - allocatedDemandKW)
shortfallKW = max(0, allocatedDemandKW - solarPowerKW)
chargeKWh = min(surplusKW*dtHours*chargeEfficiency, freeCapacityKWh)
dischargeKWh = min(shortfallKW*dtHours/dischargeEfficiency,
                   batteryKWh - protectedEmergencyReserveKWh)

oxygenDeltaKg = oxygenPlantOutputKgPerHour * poweredFraction * healthFactor * dtHours
              - crewO2ConsumptionKgPerHour * dtHours

waterDeltaL = min(wasteWaterL, recyclerNominalLPerHour * dtHours)
            * recyclerEfficiency * poweredFraction
            - drinkingUseLPerHour*dtHours - farmIrrigationLPerHour*dtHours

cropGrowth += baseGrowthPerSimHour * min(lightFraction, waterFraction,
              nutrientFraction, climateFraction) * dtHours

foodPortions += harvestedYield - crewFoodUsePerSol * deltaSols

radiationExposureIndex += externalRiskIndex * activityFactor
                        * (1 - shelterEffectivenessFraction)*dtHours
```

Do NOT mistake the example `radiationExposureIndex` for physical measured dose. To show real units in educational cards, use actual source readings and measured instrument/context/unit separately, NEVER re-label gameplay index as mSv. Sensitivity and causality tests are critical.

### Dust weather curve & causality

- `DustStormEvent`: startSol, durationSimHours, peakTauProxy, depositionRate, recoveryRate, warningLead, historicalContextUrl, dataProvenance.
- Stage curves: forecast → approach (transmission=1→0.65) → peak (0.65→0.25) → tail (0.25→0.8) → clear (0.8→1.0). **Values are scenario multipliers, not direct conversion from a verified atmospheric optical depth.**
- `panelDustLoad` rises with deposition and does not reset at storm end; clean action reduces it based on upgrade and parts. Solar panel particle effects and scene volumetric fog are visual response to same `DustStormEvent` state.
- Feedback: lower solar→higher battery discharge→optional systems shed→O2 plant power endangered→O2 declines if net production below use. Each causality arrow is testable.

### Real NASA events vs scenario difficulty

- DONKI flare/CME/SEP entries contain different scientific types. **Do not assert an Earth-directed event impacts Mars**, and do not map flare class to Mars astronaut absorbed dose using an arbitrary multiplier while calling it measured data.
- Event adapter may use verified SEP/CME metadata to select *educational alert theme* and provenance card. Separate scenario risk `LOW/MEDIUM/HIGH` is designer-configured, labeled `TRAINING SCENARIO`, not NASA warning forecast.
- RadLab is mainly orbital/ISS dosimetry and not a Mars field sensor; prefer Curiosity RAD for Mars surface conceptual evidence. Simulated Mars shelter effectiveness is illustrative, do not infer medical outcomes.
- For farming cite NASA Veggie/CSA education and model growth with intentionally simplified rates, not experimental time-to-harvest unless sourced.

### Emergency reserve & softlock prevention

- Automatic rescue threshold when O2 <10% or Safety<20%: freeze scenario and open checkpoint learning panel, do not wipe save.
- No missions require more parts than starting + guaranteed preceding rewards. On retry restore exact mission checkpoint (`Inventory`, `BuildingState`, `SimClock`, `Events`, `Flags`), except completed KP cannot be double claimed.
- Never spawn an impossible event before building unlock. Debounce alerts, cap one major crisis at a time except M09/M10.


## 6. Mission state machine & universal template

Use `MissionDefinition` (ScriptableObject or JSON-backed SO), `MissionRuntime`, `MissionStage`, `MissionCondition`, `MissionAction`, `RewardBundle`, `MissionEvidence`.

Every mission MUST specify: id, tier/chapter, difficulty, age-safe 10-second hook, prerequisite unlocks, starter buildings and inventory overrides or checkpoint delta, guaranteed obtainable tools, visible objective, stage order with game events & choices, failure escalations, complete/retry conditions, reward, debrief, source provenance; mission is **not** a static cutscene.

`StageTypes`: Dialogue, InspectBuilding, PlaceBuilding, ToggleSystem, ChoosePriority, WaitForResourceTrend, Repair, TimedForecast, ManageStorm, ScanObjective, ReturnAirlock, ScienceQuestion, Results. Each stage emits `onEnter`, clear hint, `allowedActions`, `completionPredicate`, `nextStage`, `onFailure`. HUD objective updates continuously. Confirm on click; avoid typing tasks for children.

**Triggers:** `OnBuildingPlaced(type)`, `OnBuildingInspected(id)`, `OnBuildingPowerChanged`, `OnResourceBelow/Above(id,threshold)`, `OnWeatherPhase`, `OnPartSpent`, `OnEVAInteract(objectiveId)`, `OnEVAComplete`, `OnMessageQueued`, `OnCrewSheltered`, `OnDebriefAnswered`. Persistence stores stages and objective counters. Do not use exact UI text as logic identifiers.

**Mission outcome:** pass when all required objectives and safe stability for N ticks; `checkpoint` at start and before event; failure=gentle reset/retry. Grade as **Survived / Clever Planner / Science Explorer** instead of fail/punishment. Extra KP optional only on first clear. `MissionSourceInfo` shows SourceID + date + direct URL + data type + snapshot timestamp.


## 7. FULL BASE CAMPAIGN — TEN implementable missions

For every mission, implement the stage triggers/events in `MissionDefinition` and test 1) nominal clear, 2) both trade-off choices, 3) low-resource retry, 4) replay does not double-reward. A cinematic hook must not replace interactive stages. Dialog should stay <2 sentences at a time and voiced if possible.


### M01 — First Light
- **Chapter / gating:** Welcome to Mars; Level 1; target 3–5 min.
- **Opening cutscene / hook:** Sunset threatens the newly arrived crew: get power before dark.
- **Starting/checkpoint setup:** Prebuilt Command+Habitat, 1 damaged panel or build slot, 16 Parts; night in 80s; oxygen and crew safety safe. Solar energy alone supplies daytime, battery empty.
- **Stage-by-stage playable flow:** 1) NOVA introduces sun+panels. 2) Click unpowered habitat; inspect low power. 3) Place/repair Solar Array at highlighted 2×2 tile. 4) Watch generator rise, open energy flow panel. 5) Sunset forecast alarm; build Battery Bank / connect storage. 6) Nightfall and optional Research load appears; switch optional Lab OFF or choose alternate panel+reserve strategy. 7) Survive 3 ticks with essential loads powered and battery >10%.
- **Real choices and costs:** Choice A: buy a spare array (-Parts), higher production by sunset; choice B: conserve by switching Lab off (less science this sol), preserve Parts. Child sees different graphs.
- **Failure / recovery:** Soft failure: dusk causes 0 generation and battery drains below safety reserve; freeze and highlight battery, retry from before sunset.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** Explain that a solar panel uses sunlight; at night battery supplies stored energy. NASA Mars solar dust context, NOT a live weather API.
- **Clear / rewards:** 100 KP; unlock B04 Battery Bank; research Energy Management.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M02 — Oxygen Mystery
- **Chapter / gating:** Welcome to Mars; Level 2; target 4–6 min.
- **Opening cutscene / hook:** An oxygen alarm sounds although the machine is present.
- **Starting/checkpoint setup:** O2 at illustrative 65%; Oxygen Plant built, lab taking priority power, 3 crew and reserve battery.
- **Stage-by-stage playable flow:** 1) O2 warning with decreasing arrow. 2) Click Oxygen Plant; discover state UNDERPOWERED. 3) Inspect power input/oxygen output. 4) Switch lab OFF OR reassign Essential priority to plant. 5) See production-versus-consumption net becomes positive. 6) Optional prompt: run research for bonus but risk reserve. 7) Maintain positive/stable O2 for 4 ticks.
- **Real choices and costs:** Choice A: shut research down now and save battery; choice B: discharge reserved battery, preserve research but risk night energy.
- **Failure / recovery:** Soft failure: O2 below safe game threshold; freeze at checkpoint and show power load allocation.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** MOXIE made oxygen from CO2 on Mars; game represents a future scaled-up fictional plant. Compare actual small demo with future engineering goal.
- **Clear / rewards:** 150 KP; unlock Oxygen Efficiency I and O2 tank.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M03 — Red Dust Rising
- **Chapter / gating:** Red Planet Strikes; Level 3; target 5–7 min.
- **Opening cutscene / hook:** A giant orange dust wall approaches the colony.
- **Starting/checkpoint setup:** Forecast UI active, installed arrays, 70% battery BALANCE, 12 Parts, optional Lab and basic greenhouse load represented.
- **Stage-by-stage playable flow:** 1) 60s warning and sky tint; store power and set priorities. 2) Dust arrives: transmission gradually drops; watt graph updates. 3) Peak: battery drains; choose stop Lab or dim crop LEDs, O2 Essential. 4) Alert: O2 risk if power below essential load. 5) Storm retreats, light returns but panels still dust-coated. 6) Spend cleaning kit/Parts or complete E02 for better cleaning. 7) Restore panel efficiency and O2 safety.
- **Real choices and costs:** Choice A: save farm growth at battery expense; choice B: pause farm & lab protecting O2; choice C: extra solar panel before storm expensive but more robust. All effects visible.
- **Failure / recovery:** Soft failure: reserve exhausted and O2 dips: checkpoint before peak, NOVA asks which load is optional. Dust cleanup must remain necessary after storm.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** NASA documents Mars dust reducing solar energy; e.g. InSight solar decline, but these specific curves are balanced approximations. NOT DONKI.
- **Clear / rewards:** 200 KP; unlock B17 station, cleaning kit, E02.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M04 — Broken Circuit
- **Chapter / gating:** Red Planet Strikes; Level 4; target 4–6 min.
- **Opening cutscene / hook:** A power junction sparks after the storm; O2 plant has no supply.
- **Starting/checkpoint setup:** B07 power junction damaged; emergency backup route available, limited parts.
- **Stage-by-stage playable flow:** 1) Alert power path disconnected. 2) Inspect junction; highlight fault. 3) Mini-puzzle connect two endpoints OR use temporary bypass. 4) Repair costs Parts, backup costs stored battery. 5) Restore power to plant and see O2 trend normalize. 6) Optional prepare junction upgrade.
- **Real choices and costs:** Choice A: permanent repair costs parts but reliable; choice B: bypass faster but reduces future reserve.
- **Failure / recovery:** Soft failure: wrong connection shows friendly retry, no random irreversible explosion.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** Electrical redundancy is an educational engineering principle; fictional wiring puzzle not a NASA dataset.
- **Clear / rewards:** 180 KP; unlock Power Junction upgrade, Maintenance Workshop.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M05 — Thirsty Colony
- **Chapter / gating:** Life on Mars; Level 5; target 4–6 min.
- **Opening cutscene / hook:** A water warning threatens drinking reserves and tomorrow’s crop.
- **Starting/checkpoint setup:** Water 55% game meter, recycler filter at 40% health, active wastewater reservoir, some spare filters.
- **Stage-by-stage playable flow:** 1) Water trend slopes down. 2) Inspect Recycler, see dirty filter + reduced yield. 3) Distinguish drinking and irrigation. 4) Choose replace filter now OR ration irrigation and postpone repair. 5) View recycled amount versus consumed water; collect water from wastewater (not magic production). 6) Restore reserves for 4 ticks.
- **Real choices and costs:** Choice A: replace filter costing Parts (water recovery, uses power), choice B: reduce farm irrigation (save water, crops grow slower).
- **Failure / recovery:** Soft failure: water below safety threshold stops time and proposes lower irrigation or filter replacement.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** NASA ECLSS recycles wastewater; 98% ISS demonstration is specific to station, not target efficiency asserted for Mars.
- **Clear / rewards:** 200 KP; unlock Water Recycler Tier2 and tank.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M06 — Greenhouse Challenge
- **Chapter / gating:** Life on Mars; Level 6; target 5–7 min.
- **Opening cutscene / hook:** Crew asks: Can we grow lunch on Mars?
- **Starting/checkpoint setup:** Greenhouse at L1, one crop plot, water & LED sliders, 3-sol accelerated mission, enough starter meals.
- **Stage-by-stage playable flow:** 1) Pick lettuce or peas or tomatoes as game profiles. 2) Plant seed, check water and LED power. 3) Small growth time lapse begins. 4) Water scarcity or lamp load alert. 5) Adjust irrigation or LED and compare growth indicators. 6) Allow growth to recover / accept slower yield. 7) Harvest one educational batch, deposit food into storage.
- **Real choices and costs:** Choice A: full LEDs uses extra battery but faster crop progress; choice B: low LEDs saves power but delays harvest. Water also competes with drinking.
- **Failure / recovery:** Soft failure: stressed crop pauses growth and can recover after correct water/light, never harsh permanent crop death for Explorer.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** NASA Veggie + CSA Food Production explain controlled light, water and nutrients. Exact crop yield/time is game fiction.
- **Clear / rewards:** 250 KP; unlock Hydroponics and farming badge.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M07 — Solar Alert
- **Chapter / gating:** Danger from the Sun; Level 7; target 5–7 min.
- **Opening cutscene / hook:** Mission Control receives an archived NASA space-weather case; the crew may face a training radiation event.
- **Starting/checkpoint setup:** B14 shelter accessible, 3 crew, optional expedition queued, one documented NASA DONKI event snapshot.
- **Stage-by-stage playable flow:** 1) Open event card from DONKI (event type/date/source). 2) NOVA says event metadata ≠ Mars radiation forecast; game now runs an illustrative shelter drill. 3) Suspend EVA launch. 4) Click shelter and Move Crew; all 3 slots occupied. 5) Optional labs/science power conflict. 6) Wait for scripted safe interval; review cumulative abstract risk index. 7) Reopen EVA only after safe.
- **Real choices and costs:** Choice A: postpone expedition to shelter everyone, fewer KP now; choice B: finish optional experiment only after making crew safe; unsafe EVA decision triggers coaching/checkpoint (no false medical predictions).
- **Failure / recovery:** Soft failure: missed shelter deadline, freeze with supportive feedback and retry from event warning.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** DONKI SEP/CME/FLR are real solar activity records, not direct measured dose on Mars. Curiosity RAD provides Mars radiation context; shielding is scenario model.
- **Clear / rewards:** 300 KP; unlock Shelter Tier2, E04.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M08 — Silent Signal
- **Chapter / gating:** Danger from the Sun; Level 8; target 4–6 min.
- **Opening cutscene / hook:** Your science packet is ready but Earth has not replied!
- **Starting/checkpoint setup:** Communication Relay installed, lab packet ready, power allocation tight; scripted uplink windows.
- **Stage-by-stage playable flow:** 1) Queue data packet. 2) Inspect relay: unavailable window or underpowered. 3) Decide pause relay and save energy vs reserve a transmission window. 4) Open link window; transmit packet. 5) Notice Earth response has delay; continue local operations instead of awaiting live directions. 6) Receive success confirmation and report.
- **Real choices and costs:** Choice A: store data and keep energy, later reward; choice B: spend power for next available window, earlier KP but less battery.
- **Failure / recovery:** Soft failure: missed window retains data and offers next window; no loss of progress.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** Light-time delay from Mars is real; transmission windows are game-authored (not actual DSN schedule).
- **Clear / rewards:** 250 KP; unlock Relay Buffer and queue upgrade.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M09 — The Domino Effect
- **Chapter / gating:** Survival Test; Level 9; target 6–8 min.
- **Opening cutscene / hook:** Dust, filter failure and falling O2 interact at once!
- **Starting/checkpoint setup:** Start with arrays partly dusty, recycler filter nearing failure, farm active, battery moderately low; 10 Parts and only two repair options at once.
- **Stage-by-stage playable flow:** 1) Warning forecast; prepare. 2) Dust hits solar output. 3) Battery drains, O2 plant reduced. 4) Recycler degrades and clean water drops. 5) Farm irrigation competes with drinking. 6) Choose repair order: solar clean, recycler filter, farm LEDs; remaining problem keeps escalating until priorities corrected. 7) Stabilize O2, clean water and crew safety for 6 ticks. 8) View causal chain.
- **Real choices and costs:** No one scripted "correct" order; choose based on actual current state. Emergency energy first if O2 falling, water first if critical; AI discusses symptoms vs root causes.
- **Failure / recovery:** Soft failure: any vital falls below floor; freeze and replay from phase 2 with easier resources after 2 failures.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** Combines NASA-inspired phenomena: dust/solar mechanics, ECLSS recycling, plant research; event combination is fictional educational scenario.
- **Clear / rewards:** 350 KP; unlock Emergency Automation.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


### M10 — Sol 30 — Final Survival Test
- **Chapter / gating:** Survival Test; Level 10; target 7–10 min.
- **Opening cutscene / hook:** Can SURVORA survive three fictional accelerated sols independently?
- **Starting/checkpoint setup:** Choose 2 of 3 available upgrades: extra battery, water filter, O2 efficiency; use saved game inventory or balanced isolated campaign checkpoint.
- **Stage-by-stage playable flow:** 1) Preparation card: select two upgrades and explain one trade-off. 2) Sol1 dust lowers generation: manage battery. 3) Sol2 water vs food pressure: adjust recycler/farm. 4) Sol3 solar event case: move crew shelter and defer optional research. 5) Respond to optional lost relay; send data when safe. 6) Stabilize at least crewSafety>=50, O2>=20%, water>=20% with no unresolved Critical status. 7) Debrief scientific cards and achievements.
- **Real choices and costs:** Choice is constrained upgrade budget; different viable build strategies give different after-action summaries; challenge is stewardship, not score-chasing.
- **Failure / recovery:** Soft failure: return to start of the current sol, preserving educational learning; no restart of whole campaign mandatory.
- **NOVA Level-1 hint:** Ask child to identify which resource changed first, or what building is involved (do not spoil).
- **NOVA Level-2 hint:** Highlight exact relevant panel, trend, or interactable and restate trade-off.
- **NOVA Level-3 hint:** Offer one safe actionable example, allowing other viable choices.
- **Science mapping & attribution:** Blend of cited NASA sources; each generated event points to evidence and prominently states TRAINING SCENARIO.
- **Clear / rewards:** 500 KP; open Sandbox, Mission Commander badge.
- **Unity acceptance:** A mission marker, stage progress, updated authoritative resources, animation/VFX, appropriate source info, three-tier hints, win/retry and reward-once save flag are observable in Play Mode.


## 8. FULL EVA MISSIONS — third person, objective scripts and returns

**Universal EVA runtime:** `PlayerMotor` (walk 4 m/s BALANCE, sprint 6), `Cinemachine` only if already installed else simple camera, `IInteractable` interaction range 2.5 m, `WaypointMarker`, `SuitResources`, `MissionObjectiveMarker`, `AirlockReturnZone`, no health-based combat, no oxygen jumpscare. On leaving base, snapshot safe return point; on reaching 20% suit O2 highlight route; under 10% freeze & offer emergency retrieval. Each scan has animation and source context (real vs imagined).


### E01 — First Footprints (Level 2)
- **Hook:** Launch from airlock, walk to three labeled samples and return.
- **Map/stages:** 2 close scan nodes and one optional farther bonus node; display distance + suit reserve. Scanner uses 3 battery units per use.
- **Trade-off:** One-way shortcut rocky path saves suit energy but excludes optional science scan; safe path longer.
- **Effect on base and AI:** Teach suit O2 usage and return reserve; gear UI and airlock handoff.
- **NASA attribution:** NASA Mars Trek geographical reference only if selected and labeled; samples otherwise generic illustration.
- **Completion/retry:** Must return to airlock or finish scripted rescue, show debrief; auto-return checkpoint after equipment expiry; mark once-only first-clear KP.
- **Reward:** 60 KP; unlock scanner Tier2.
- **Unity triggers:** OnEVAStarted(E01), OnWaypointReached, OnScanCompleted, OnInteractCompleted, OnReturnAirlock, OnEVAEnded. Always support abandon mission with checkpoint restore.


### E02 — The Lost Sensor (Level 4)
- **Hook:** A weather sensor stopped transmitting after dust; fix it.
- **Map/stages:** Find waypoint, scan faulty beacon, solve rotate/align two connector icons, spend repair kit, return to airlock.
- **Trade-off:** Direct rocky route shorter vs longer safer; bring repair kit vs extra sample case.
- **Effect on base and AI:** Repairing it unlocks better base warning lead time; give immediate visible effect in Weather Station.
- **NASA attribution:** Mars weather studies + invented sensor malfunction; do not pretend NASA live monitor.
- **Completion/retry:** Must return to airlock or finish scripted rescue, show debrief; auto-return checkpoint after equipment expiry; mark once-only first-clear KP.
- **Reward:** 150 KP; unlock Weather Monitor improvement.
- **Unity triggers:** OnEVAStarted(E02), OnWaypointReached, OnScanCompleted, OnInteractCompleted, OnReturnAirlock, OnEVAEnded. Always support abandon mission with checkpoint restore.


### E03 — Ice Clues (Level 6)
- **Hook:** Find promising subsurface water clues, not guaranteed drinking water.
- **Map/stages:** Reach 3 candidate scan locations, scan soil/ice proxy, review scanner result and choose site to sample; return.
- **Trade-off:** Scan extra sites for more confidence but consume suit battery; withdraw early with less info.
- **Effect on base and AI:** Unlock optional water research card; do NOT spawn extractable water magically.
- **NASA attribution:** Mars Trek terrain; Curiosity DAN instrument searches hydrogen as water clue.
- **Completion/retry:** Must return to airlock or finish scripted rescue, show debrief; auto-return checkpoint after equipment expiry; mark once-only first-clear KP.
- **Reward:** 180 KP; unlock Water Research card.
- **Unity triggers:** OnEVAStarted(E03), OnWaypointReached, OnScanCompleted, OnInteractCompleted, OnReturnAirlock, OnEVAEnded. Always support abandon mission with checkpoint restore.


### E04 — Shelter Run (Level 8)
- **Hook:** Solar-alert drill interrupts a planned outside science task.
- **Map/stages:** Leave airlock with sample objective. Midway show NASA-backed case alert; safe play requires abandoning optional sample and returning to airlock/shelter before training timer ends.
- **Trade-off:** Optional scan vs time reserve; real safe decision prioritizes shelter.
- **Effect on base and AI:** Replay under safe, non-frightening conditions; fail gracefully.
- **NASA attribution:** DONKI archived event is scenario trigger inspiration; not an actual Mars-site real-time alert.
- **Completion/retry:** Must return to airlock or finish scripted rescue, show debrief; auto-return checkpoint after equipment expiry; mark once-only first-clear KP.
- **Reward:** 200 KP; EVA safety badge.
- **Unity triggers:** OnEVAStarted(E04), OnWaypointReached, OnScanCompleted, OnInteractCompleted, OnReturnAirlock, OnEVAEnded. Always support abandon mission with checkpoint restore.


### E05 — Rescue the Rover (Level 9)
- **Hook:** Rover stops on rocky ridge as dust approaches.
- **Map/stages:** Load repair kit; navigate to rover with 2 waypoints, inspect broken wheel or depleted battery, choose salvage data vs full repair, return.
- **Trade-off:** Full rescue uses more parts/time; collect memory pack safer and quicker but rover unavailable until later repair.
- **Effect on base and AI:** Rover recovery unlocks automatic Solar Array cleaning in base.
- **NASA attribution:** NASA rover designs as visual references; story and rescue condition fictional.
- **Completion/retry:** Must return to airlock or finish scripted rescue, show debrief; auto-return checkpoint after equipment expiry; mark once-only first-clear KP.
- **Reward:** 250 KP; unlock Rover Garage automation.
- **Unity triggers:** OnEVAStarted(E05), OnWaypointReached, OnScanCompleted, OnInteractCompleted, OnReturnAirlock, OnEVAEnded. Always support abandon mission with checkpoint restore.


## 9. Crisis catalog: severity, escalation phases, notifications, response

`CrisisController` handles one major crisis at a time by default; M09/M10 explicitly allow overlaps. Maintain phases `Forecast → Emerging → Critical → Stabilizing → Resolved`; no random lethal or untelegraphed crisis. Each crisis has `sourceId`, `dataMode`, `gameplayCurve`, `affectedBuildings`, `leadTime`, `successExitConditions`, `teachableMoment`.

| ID | Incident | Forecast / early sign | Stage 2 | Stage 3 escalation | Response | Recovery |
|---|---|---|---|---|---|---|
| C01 | Dust storm | orange horizon + forecast | solar output lowers | battery and O2 underpower risk | shed loads, protect O2 | clean panels post storm |
| C02 | Panel dust | daily production drops slowly | dust accumulation > threshold | battery run time falls | clean using kit or rover | restore efficiency |
| C03 | Night power | sunset warning | generation→0 | reserve drops | battery + load priority | sunrise charge |
| C04 | O2 deficit | negative O2 trend | 65% example | 25% critical | repower oxygen plant | stable O2 trend |
| C05 | Cable failure | panel shows disconnected | plant input missing | O2 declines | repair junction/bypass | restore load connectivity |
| C06 | Recycler filter | efficiency falls | storage declines | farm competes with drink | replace filter/ration irrigation | restored water trend |
| C07 | Greenhouse stress | leaf yellow icon | crop growth halts | harvest delayed | adjust LED/water | gradual recovery |
| C08 | Solar radiation drill | DONKI evidence case shown | training risk rises | EVA unsafe, crew must shelter | cancel EVA, shelter | end scripted drill |
| C09 | Communication outage | lost signal icon | packet queued | research confirmation postponed | schedule downlink, prioritize power | send later window |
| C10 | Rover stranded | sensor beacon offline | cleanup no longer possible | future dust accumulation persists | E05 rescue | rover online |
| C11 | Storage leak | capacity/storage down | water or O2 bleed | safety buffer shrinks | repair tank, ration | stop loss |
| C12 | Multi-system domino | 2 warnings | cascading deficits | 3-asset conflict | prioritize root cause | stable all vital resources |

**Hazard spawning and escalation:** at most one minor failure per 2 simulated sols in sandbox (BALANCE), no repeating alert in 5 real minutes, scripted missions override random spawner; major critical alert only when player already has required repair/unlock. If `Explorer`, cap simultaneous alerts at 2 and freeze sim while crisis tutorial open.

**Issue presentation:** stage 1 sound + pictogram, stage 2 building glow + resource trend, stage 3 highlighted choices with trade-off previews and a retry option, stage 4 confetti/crew smile only after actual stabilized state.

**Example C01 precise events:** `OnStormForecast(tMinus=60s)` sets UI; `OnStormPhase(approach)` sky transmission→0.65; `(peak)`→0.25; `(fade)`→0.8; `(cleared)`→1 while surface dust persists; `OnPanelsCleaned` subtracts dustLoad; `OnEmergencyPowerPrioritySet` makes essential powered. Rates are designer-authored curves. Storm outcome has at least two viable strategies, and data evidence card explains archived science vs modeled values.


## 10. NOVA AI Companion — architecture, model data, intent and safeguards

**Recommended:** use a hosted existing instruction-tuned LLM via your own FastAPI backend, plus grounded retrieval (RAG) over curated NASA/CSA docs, **not train a new large language model** during a 24h hackathon. Do not confuse RAG with model training; no weights need to change. If fine-tuning later, only consider small answer-style pairs after testing, permission and child-safety checks.

### Game state contract passed by Unity (minimal, allowlisted, no personal data)

```json
{
  "sessionId": "random-ephemeral-id",
  "ageMode": "Explorer",
  "missionId": "M03",
  "missionStage": "PeakStorm",
  "question": "ليه الأكسجين بيقل؟",
  "simulation": {
    "batteryPct": 18, "oxygenPct": 47,
    "solarPowerKW": 1.8, "essentialDemandKW": 3.2,
    "panelDustLoad": 0.5, "weatherType": "DustStormScenario",
    "oxygenPlantStatus": "UNDERPOWERED", "researchLabOn": true
  },
  "allowedActions": ["InspectOxygenPlant", "SetPowerPriority", "ToggleResearchLab"],
  "sourceContextIds": ["NASA_INSIGHT_SOLAR_DUST", "NASA_ECLSS", "NASA_MOXIE"]
}
```

**Example values above are synthetic game state**; never represent them as a NASA reading.

### Backend interfaces

- `POST /ai/ask` request as above; response `{replyAr, hintLevel, evidence:[{sourceId,title,url,observationDate,kind}], suggestedUiTarget, safetyMode, noEvidence}`. Answer ≤65 Arabic words for Explorer, ≤110 for Commander; give one actionable hint; invite child to predict before providing a direct step unless critical safety.
- `GET /ai/health` returns status; if unavailable, use deterministic local hint library from mission definitions. No cloud dependency for mission completion.
- `GET /science/sources` returns curated source registry; `GET /science/cards/{id}` static approved accessible summaries. Cached and signed-off narrative entries.
- Unity client should call via `UnityWebRequest` (HTTPS) with cancellation/timeouts. Never put provider LLM key or NASA API secrets in shipped client. Backend stores secrets in environment variables.
- For action tool-calling: **read-only** tools `get_game_state`, `get_mission_objectives`, `search_science_cards`, `list_available_actions`, `explain_tradeoff`. LLM may suggest `allowedActions` IDs but **never call state-mutating commands**. Unity alone executes player taps.

### Knowledge base and indexing plan

Curated records (not raw broad scraping): NASA Open APIs DONKI endpoint docs, official DONKI CCMC description, NASA ECLSS overview and ISS water achievements, MOXIE results, NASA InSight dust power, Curiosity RAD descriptions, NASA Veggie plant science, CSA food toolkit, NASA Mars Trek guide, NASA OSDR biological studies, NASA RadLab definitions. Each chunk: sourceId, canonicalURL, docTitle, author/agency, publication date, retrieval date, textExcerpt with permission check, contentType, scienceTopic, Mars/ISS/Earth context, trustType, verification status.

Retrieval: semantic topK=5 + keyword/BM25 fallback; rerank by relevance/authority. Filter by applicable planet/context; refuse to infer Mars surface dose from ISS RadLab, real-time Mars dust from DONKI, or medical outcomes. If sources unavailable, answer game-rule question only and say source card unavailable. Citation UI must link actual URLs. Curated hardcoded facts must have source IDs.

### NOVA behavior policy and hint ladder

- Level 1: Socratic question: "أنهي مؤشر اتغير الأول؟"; Level 2: identify panel "افتح Power Dashboard وشوف استهلاك المعمل"; Level 3: safe option "جرّب توقف Research مؤقتًا علشان تحافظ على Oxygen Plant".
- When urgent, avoid slow Socratic loop: give direct safety alert. No unsupervised medical, psychological, or personal advice. No collecting child name, contact details or chat history beyond transient session. Backend moderation, short context retention, no personalized tracking.
- Never praise a risky radiation exposure as a learning opportunity. NASA evidence remains science facts, mission policies remain game design. Explain ambiguity when unavailable.

### Train what, exactly?

1. **RAG index**: ingest verified NASA content chunks and approved mission documentation; no model weights are trained.
2. **Optional supervised intent classifier** (only if necessary after playtesting): intents `AskWhyResource`, `AskBuilding`, `AskNextAction`, `AskScienceFact`, `AskMission`, `OutOfScope`. Use manually authored QA/utterance examples (~20–50 per intent) and unit tests; can be rules/embeddings instead of trained ML.
3. **Optional hint preference model** (later, not MVP): estimate child's hint level from only gameplay context without collecting personal identity. Not necessary for prototype.
4. **NO ML model to run oxygen/power/water**. The simulation is explicit physics-inspired math and config. Avoid unsupported claims of "AI-trained NASA storm prediction".

### Example NOVA answers

- M03: "العاصفة الترابية خلت ضوء الشمس أضعف، فالألواح بتولد كهرباء أقل. البطارية بتساعدنا مؤقتًا. تفتكر نوقف المعمل ولا جهاز الأكسجين؟" [NASA_INSIGHT_SOLAR_DUST]
- M05: "المياه اللي بنستخدمها ممكن ننقي جزء منها ونعيد استعماله. افتح Water Recycler وشوف الفلتر!" [NASA_ECLSS]
- M07: "ده سيناريو تدريب مستوحى من نشاط شمسي حقيقي. مهمتنا نحمي الطاقم وندخل المأوى؛ الحدث ده مش قراءة مباشرة لإشعاع المريخ." [NASA_DONKI, NASA_RAD]


## 11. Source Registry — authoritative direct links and exact permitted role

**All links below are canonical source/directory/documentation entry points verified as existing web resources on 2026-11-13, not proof every linked dataset has been successfully downloaded.** Agent must verify individual downloadable files and licensing before ingestion. NASA and CSA resources are not automatically interchangeable with local game values.

| `sourceId` | URL | Best application | Availability / caution |
|---|---|---|---|
| NASA_OPEN_APIS | https://api.nasa.gov/ | free NASA API portal and key registration | key and limits; use proxy/cache |
| NASA_DONKI_API | https://api.nasa.gov/ | solar flare/CME/SEP historic API | event metadata; **not Mars forecast** |
| NASA_CCMC_DONKI | https://ccmc.gsfc.nasa.gov/tools/DONKI/ | context of space weather | factual descriptions only |
| NASA_DONKI_FLR | https://api.nasa.gov/DONKI/FLR?startDate=2024-05-01&endDate=2024-05-15&api_key=DEMO_KEY | archived solar flares example query | dynamic endpoint; DEMO_KEY limits, check runtime |
| NASA_DONKI_CME | https://api.nasa.gov/DONKI/CME?startDate=2024-05-01&endDate=2024-05-15&api_key=DEMO_KEY | CMEs example query | occurrence ≠ Mars impact |
| NASA_DONKI_SEP | https://api.nasa.gov/DONKI/SEP?startDate=2024-05-01&endDate=2024-05-15&api_key=DEMO_KEY | SEP case search | optional; no fake hazard conversion |
| NASA_INSIGHT_SOLAR_DUST | https://science.nasa.gov/resource/insights-power-generation-after-landing-and-spring-2022/ | historical power loss from dust, C01/C02 | dated observational comparison, not dynamic storm feed |
| NASA_MOXIE | https://www.nasa.gov/solar-system/nasas-oxygen-generating-experiment-moxie-completes-mars-mission/ | oxygen conversion mechanism | experimental 12g/h, **not crew-grade** |
| NASA_MOXIE_INSTRUMENT | https://science.nasa.gov/mission/mars-2020-perseverance/science-instruments/ | rover technology specifics | check differing spec vs actual achieved max |
| NASA_ECLSS | https://www.nasa.gov/reference/environmental-control-and-life-support-systems-eclss/ | life support air/water loop | ISS technology as reference; model Mars separately |
| NASA_ISS_WATER | https://www.nasa.gov/missions/station/iss-research/nasa-achieves-water-recovery-milestone-on-international-space-station/ | 98% ISS system demonstration | not future Mars-specific efficiency |
| NASA_RAD | https://science.nasa.gov/mission/msl-curiosity/science-instruments/ | Curiosity RAD Mars surface radiation instrument | docs describe sensor; not live time series |
| NASA_RAD_COMPARE | https://science.nasa.gov/resource/radiation-exposure-comparisons-with-mars-trip-calculation/ | explanatory radiation comparison | explicit historical date/mission assumption |
| NASA_OSDR_REPOSITORY | https://osdr.nasa.gov/bio/repo/ | astronaut health / plant studies | publications not simulator numeric coefficients |
| NASA_OSDR_SEARCH_API | https://osdr.nasa.gov/osdr/data/search?term=plant | search relevant biological datasets | verify metadata and context before claim |
| NASA_OSDR_API_DOCS | https://www.nasa.gov/osdr-api/ | OSDR programmatic access | metadata retrieval and documentation |
| NASA_RADLAB_API | https://visualization.osdr.nasa.gov/radlab/gui/data-api/ | ISS radiation measurements, data-field definitions | ISS ≠ Mars; units μGy/h vs μSv/h not interchangeable |
| NASA_MARS_TREK | https://trek.nasa.gov/mars/ | surface imagery, terrain, science sites | export/import to Unity as offline files |
| NASA_TREK_HUB | https://trek.jpl.nasa.gov/ | Trek platform features | don't fetch raster tiles indiscriminately |
| NASA_TREK_WMTS_DOC | https://api.nasa.gov/ | Mars Trek WMTS entry documentation | check specific service GetCapabilities URL before code |
| NASA_PDS | https://pds.nasa.gov/ | archive of Mars mission environmental data | more integration effort, not single convenient game API |
| NASA_VEGGIE | https://www.nasa.gov/missions/station/iss-research/growing-plants-in-space/ | NASA plant-growing research entry point | verify article/page before relying on it; fallback to CSA |
| CSA_FOOD | https://www.asc-csa.gc.ca/eng/youth-educators/toolkits/food-production/ | game farming pedagogy and trade-offs | CSA, not NASA; acknowledge separately |
| NASA_3D_RESOURCES | https://science.nasa.gov/3d-resources/ | NASA 3D models, Mars rovers, spacecraft, textures | check model-specific license, format, polycount |
| NASA_MEDIA_USAGE | https://www.nasa.gov/nasa-brand-center/images-and-media/ | NASA image / model attribution & usage | no endorsement; trademark and third-party exceptions |
| UNITY_MANUAL | https://docs.unity3d.com/Manual/index.html | Unity game systems | version-specific |
| UNITY_ADDRESSABLES | https://docs.unity.cn/6000.1/Documentation/Manual/com.unity.addressables | optional runtime asset management | only if used and package installed |
| UNITY_SCRIPTABLE_OBJECTS | https://docs.unity3d.com/Manual/class-ScriptableObject.html | mission/config authoring | check Unity version |
| UNITY_INPUT_SYSTEM | https://docs.unity3d.com/Packages/com.unity.inputsystem@1.11/manual/index.html | player actions | if package version differs adjust |

### File acquisition workflow

1. Check URLs and returned status/format using a trusted backend/editor importer; review user agents, terms, key and rate limits.
2. Store exact `sourceUrl`, `retrievedAtUtc`, `observedAtUtc` (if known), `agency`, `siteContext`, units, raw downloaded blob SHA256, and derived fields in `source_manifest.json`.
3. Normalize NASA event JSON into **your own simple schema**; preserve raw observations. Label data `HISTORICAL_SNAPSHOT`, `CURRENT_VERIFIED` only if actually fetched with timestamp, `SCIENTIFIC_REFERENCE`, `GAME_BALANCE`.
4. Create verified offline JSON snapshots in `Assets/StreamingAssets/NasaSnapshots/` (or Addressables if already enabled). Shipping an empty fallback educational case is acceptable **only if labeled synthetic training data**; do not include fabricated "NASA readings".
5. Never let LLM itself invent a download URL, parse the first article it sees as a measurement, or silently fill missing fields with guessed NASA numbers.
6. Maintain attribution UI and a Credits screen listing NASA/CSA source, access date, document title; explicitly say "NASA does not endorse SURVORA". Avoid restricted NASA insignia as game brand identity.

### Example NASA events → Unity schema (illustrative shape, values deliberately omitted)

```json
{
  "eventId": "imported-source-event-id",
  "sourceId": "NASA_DONKI_SEP",
  "sourceType": "HISTORICAL_SNAPSHOT",
  "eventType": "SEP",
  "eventStartUtc": null,
  "sourceUrl": "https://api.nasa.gov/",
  "retrievedAtUtc": null,
  "marsImpactVerified": false,
  "gameTrainingScenarioId": "C08",
  "riskIndexSource": "GAME_BALANCE",
  "validationStatus": "PENDING_REAL_IMPORT"
}
```

### Art/texture/environment sourcing plan

- NASA 3D hub: actual spacecraft, rovers, landing components, planets and mission educational props (where available); not guaranteed prefabs for habitats/greenhouse/solar batteries.
- Build fictional **low-poly** habitat, oxygen generator, greenhouse, solar panels, batteries and radiation shelter with primitives/Blender/custom licensed assets. Do not imply NASA supplied a made-up base design.
- Mars Trek: select one region, document coordinates/source layer and license; use map/elevation to inspire one small EVA arena, or use a labeled visually-inspired procedural map if import time insufficient.
- UI icons: create with Unity primitives/vector/UI Toolkit or properly licensed set. Audio: self-created/appropriately licensed, not automatically from NASA.
- 3D conversion: download original → inspect license → clean topology → convert to FBX/GLB where supported → reduce polygons → collider LOD and texture compression → import prefab → attribution entry.


## 12. Unity project folder and scenes — actual deliverables

```
Assets/
  _Survora/
    Scenes/Boot.unity
    Scenes/Base.unity
    Scenes/EVA.unity
    Scripts/Core/{GameBootstrap,GameState,SimClock,SaveService,EventBus}.cs
    Scripts/Simulation/{PowerSystem,AtmosphereSystem,WaterSystem,FoodSystem,CrewSystem,DustSystem,SpaceWeatherScenarioSystem,RadiationRiskSystem}.cs
    Scripts/Buildings/{BuildingDefinition,BuildingInstance,BuildingManager,ConstructionGrid,BuildingPanel,UpgradeService}.cs
    Scripts/Missions/{MissionDefinition,MissionController,MissionCondition,MissionRewards,MissionCheckpoint,CrisisController}.cs
    Scripts/EVA/{EVAController,SuitResources,WaypointMarker,EVAInteractable,AirlockGateway}.cs
    Scripts/Nasa/{NasaSourceRecord,NasaSnapshotImporter,SourceProvenanceUI}.cs
    Scripts/AI/{NovaClient,NovaFallbackHints,NovaPanel,GameContextBuilder}.cs
    Scripts/UI/{HUDController,BuildingCardUI,ResourceTrendUI,AlertsUI,TechTreeUI,MissionLogUI,ScienceCardUI}.cs
    Data/Buildings/*.asset
    Data/Missions/M*.asset
    Data/Missions/E*.asset
    Data/Scenarios/*.asset
    Data/KnowledgeCards/*.asset
    Prefabs/Buildings/*
    Prefabs/EVA/*
    Prefabs/UI/*
    Materials/*
    Tests/EditMode/*
    Tests/PlayMode/*
StreamingAssets/NasaSnapshots/{source_manifest.json,*.json}
Documentation/{IMPLEMENTATION_STATUS.md,ATTRIBUTIONS.md,DATA_PROVENANCE.md,TEST_PLAN.md}
```

### Scenes

**Boot:** main menu Play, Explorer/Commander, Credits/Sources, load save. Initialize services once, then load Base.
**Base:** camera, terrain/grid, starter Command + Habitat, player-built prefabs, resource UI, mission objective panel, NOVA toggle, day/night, dust VFX, station science source panel.
**EVA:** third person controller+camera, suited astronaut, trigger zones, interactables, safe boundary, suit HUD, return airlock and context; base simulation paused in Explorer, optionally continues in Commander under rules.

### UI interaction details

- HUD top: Solar power bar with generation/demand arrow; O2 reserve with +/− trend; Crew Safety face. Below: selectable Water/Food/Parts, KP, clock, event warning, single current objective.
- Building click: tab Overview, Actions, Upgrades, Science. Shows rates and budget before click. Disabled action reasons (not just gray button).
- Build catalog tabs: Life Support, Energy, Resources, Science & Safety; unlock silhouette and needed level.
- Mission panel: chapter nodes, rewards, prerequisites, Start/EVA/Retry; 1–3 goals only visible per moment.
- NOVA panel: 3 preapproved quick suggestions + text question, evidence footnote; can collapse and run completely offline fallback.
- Science Log: badges for `NASA observation / scientific reference / training scenario / hypothetical balance`. Link out via trusted URL open action; show source date.
- Accessibility: 44px+ target sizing for touch, beginner reading guide optional, subtitles, symbols with text, reduced motion toggle.

### Save data

Versioned JSON save records `schemaVersion=1`, save slot, chapterLevel, completedMissions, claimedRewards, techUnlocks, all building instances and modes, inventory, resource state, simulation time, event queues, weather stage, open mission checkpoint, settings. Atomic save replace and graceful migration/ignore corrupt file. Do not store any child's personally identifying data.


## 13. Minimal JSON and C# interface contracts

```json
{
  "missionId": "M03",
  "displayTitle": "Red Dust Rising",
  "recommendedLevel": 3,
  "requiredMissionIds": ["M02"],
  "rewardKP": 200,
  "stages": [
    {"stageId":"warn", "objectiveAr":"جهز الطاقة قبل العاصفة", "trigger":"OnStormForecast", "nextStageId":"approach"},
    {"stageId":"approach", "objectiveAr":"راقب إنتاج الكهرباء", "trigger":"OnWeatherPhase:APPROACH", "nextStageId":"peak"},
    {"stageId":"peak", "objectiveAr":"حافظ على تشغيل الأكسجين", "trigger":"EssentialLoadPoweredForTicks:4", "nextStageId":"cleanup"},
    {"stageId":"cleanup", "objectiveAr":"نضف الألواح الشمسية", "trigger":"PanelDustBelow:0.2", "nextStageId":"debrief"},
    {"stageId":"debrief", "objectiveAr":"راجع سبب انخفاض الكهرباء", "trigger":"ScienceCardViewed", "nextStageId":null}
  ],
  "sourceIds":["NASA_INSIGHT_SOLAR_DUST"],
  "provenance":"SCIENTIFIC_REFERENCE_PLUS_GAME_BALANCE"
}
```

**C# high-level API (signatures are interface requirements, not completed source code):**

```csharp
public interface ISimulationSystem { void Tick(float simHours, GameState state); }
public interface IBuildingAction { bool CanExecute(GameState state, out string reason); void Execute(GameState state); }
public interface IMissionCondition { bool IsSatisfied(GameState state, MissionRuntime runtime); }
public interface IScienceDataProvider { bool TryGetSource(string sourceId, out SourceRecord source); }
public interface INovaHintProvider { Task<NovaReply> GetHintAsync(NovaRequest context); }

public enum SourceEvidenceKind { NASAObservation, ScientificReference, TrainingScenario, GameBalance }
public enum BuildingRunState { Running, Off, Underpowered, Damaged, Disconnected, Upgrading }
public enum CrisisPhase { Forecast, Emerging, Critical, Stabilizing, Resolved }
```

**Mission condition engine:** prefer explicit typed condition objects over parsing ad-hoc strings from JSON at runtime; typed enums and payloads; event bus emits typed events; preserve robust save serialization. In JSON example strings are authoring shorthand only.

**Simulation reference snapshot** structure should include test seed, exact tick intervals, and source provenance so identical state+actions produce identical results across runs.


## 14. Test matrix & exact definition of done

### Simulation tests (EditMode)

- No night solar power; dusty panels produce less than clean with other inputs constant.
- A storm changes sky transmission and persists `panelDustLoad` after event end.
- Cleaning panels consumes required parts and improves output; cannot clean with negative parts.
- Battery energy never <0 or >capacity and energy balance conserved subject to explicit efficiencies.
- Turning research OFF lowers demand and can free life-support power.
- Oxygen mass declines if consumption > production and rises if production > consumption; oxygen never >tank cap.
- Water recycling cannot generate more clean water than source wastewater after efficiency; farm irrigation uses actual water.
- Greenhouse at zero light or water does not grow, but recoverable in Explorer.
- Radiation index ≠ measured dose; no unsafe labeling. Shelter moving crew changes only modeled risk.
- Mission prerequisites and threshold awards possible from mandatory missions alone.
- No KP duplication after replay or save/load; save/load preserves current crisis and remaining Parts.

### PlayMode / user journey tests

1. Fresh Explorer → Base → place panel → night with battery → M01 completed and 100 KP once.
2. M02 underpowered O2 plant → pause Lab → oxygen trend improves and clear.
3. M03 start → visually see sky/dust/solar reduction → player turns off optional load → O2 survives → clean panels, science card contains URL and truthful provenance.
4. E02 launch → walk+scan+repair beacon → return → earlier warning visible in Weather station.
5. NOVA request M03 → grounded game-state hint with NASA evidence URL when backend online; local hint when disconnected.
6. M07 event shows historical date + NASA source, never claims measured Mars dose; moving crew to shelter is interactive.
7. Pause/retry after failure; no broken states; two difficulty levels; 7–12 text length accessible.
8. Build without external API internet access; all scripted missions playable using cached/scenario data with clearly labeled source status.

### Milestone checklist (realistic 24h hackathon order)

- **P0 (must):** Boot, Base, grid, HUD, B01–B05, two resource systems, M01, M02, one interactive storm M03, dust VFX, science card, save, NOVA local hints.
- **P1 (strong demo):** EVA airlock, 3rd-person simple E02, NASA snapshot importer, B07 maintenance, M04, NOVA backend RAG, accurate evidence handling.
- **P2 (extended):** water/greenhouse M05/M06, radiation shelter M07, comms M08, M09/M10, E01/E03/E04/E05, all B01–B18 building upgrades and analytics.

**Critical developer boundary:** full design is **not feasible to polish at 24h**. Implement a vertical slice first, never mark unimplemented content as done; expose stretch goals as locked/coming soon and keep README honest.

### Deliverable status report required from coding model

After each milestone produce `IMPLEMENTATION_STATUS.md` with `Completed`, `Partially implemented`, `Blocked`, `Tested`, `Failed`, source URLs integrated, assets and license status, Unity compile status, screenshot/demo path if available; never claim completion without running Unity or equivalent tests.


## 15. Design decisions, edge cases and honest disclosures

- NASA source links are scientific support, not a declaration that NASA designed or validated SURVORA's numeric simulation.
- Weather/space events are not interchangeable: **Dust ≠ CME ≠ solar flare ≠ SEP ≠ geomagnetic storm**. Earth's Kp geomagnetic storm value is not a Mars radiation dosage.
- NASA InSight power reduction is a concrete measured example of dust impact **specific to InSight**, not automatically a universal storm transfer function.
- Water recovered aboard ISS ≠ same rate in Mars water system; O2 produced by MOXIE ≠ full human respiration system.
- Mars terrain imagery is geographically real only if source location, projection and imported layer are preserved; fictional scenes should say "inspired by Mars".
- Child under 13 design: do not require login, real name, geolocation, user profiling or recording private conversations. Keep chat optional and use ephemeral state only.
- All encounter designs need at least two viable paths and an instructive cost; **one obvious free choice is not a real trade-off**.
- After completion, offer **Replay with Alternate Strategy** to learn consequences. Use lighthearted badge system; no paid loot boxes or dark patterns.
- If background music/art dependencies missing, gameplay should work with placeholder assets. Use no copyrighted third-party media without appropriate permission.
- Real-life scientific citations: display under the child-friendly explanation and in Credits, not overburdening the primary HUD.

## 16. Final instruction to the Unity-integrated coding agent

**Start by auditing the current project and reporting detected Unity version, scenes, installed input/render packages and existing code. Then implement the P0 vertical slice end-to-end.** Once P0 compiles and is playable, continue according to P1/P2 with tested incremental commits/changes. Treat the specific proposed names, layouts, rates and costs as editable BALANCE parameters and document changes. Do not allow the LLM to mutate simulation truth. Every NASA-backed card must contain its provenance record. All 18 building types, 10 base missions, five EVA missions, 12 crisis types, and all five building upgrade tiers are the target full roadmap—not a claim that every item is already present in Unity.


---

## Appendix A — Earlier narrative concept (non-normative)

The following is the prior v2 narrative design supplied as creative reference only. **When differences exist, the MASTER v3 specification above is authoritative**. The coding model should avoid implementing duplicate conflicting mission definitions from this appendix.


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

