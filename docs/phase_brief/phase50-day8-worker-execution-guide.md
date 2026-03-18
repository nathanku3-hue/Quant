# Phase 50 Day 8 Worker Execution Guide

**Date**: 2026-03-18
**Round ID**: `P50-D8-RUNWAY-01`
**Scope**: Bounded Day 8 continuation inside the already authorized Phase 50 paper-only runway, plus docs-only Phase 51 Factor Algebra design drafting
**Authorization Source**: CEO disposition dated 2026-03-18 22:51 PDT (`CONTINUE - PHASE 50 RUNWAY LOCKED`)
**Do Not Do**: open Phase 51, open any new execution surface, route to any broker, deploy live capital, change thresholds, migrate `permno`, rewrite governed `10` bps cost logic, add sleeves, use vendor workarounds, or implement any Phase 51 code

---

## Mission

Continue the official 30-day Phase 50 paper-only runway by adding the Day 8 artifact set, refreshing the Elite Sovereign dashboard to the latest runway day, capturing a real Day 8 screenshot, publishing the Day 8 CEO checkpoint memo in the exact reply format requested by governance, and drafting the Phase 51 Factor Algebra API skeleton as a docs-only planning artifact.

This is a bounded continuation round inside Phase 50 plus a parallel docs-only planning note for Phase 51. It is not a new phase opening, not a promotion packet, not an authorization for live execution, and not an authorization to implement any Phase 51 code.

**Frozen runway truth from Day 7**
- Day 7 memo: `docs/handover/phase50_day7_ceo_memo_20260318.md`
- Day 7 runtime SAW closeout: `docs/saw_reports/saw_phase50_day7_runtime_closeout_20260318.md`
- Day 7 proof image: `docs/images/phase50_day7_dashboard_20260318.png`
- Canonical Day 7 curve: `data/processed/phase50_shadow_ship/paper_curve_day7.csv`
- Canonical Day 7 telemetry: `data/processed/phase50_shadow_ship/telemetry_day7.json`
- Canonical Day 7 gate stub: `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day7.csv`
  - `data/shadow_evidence/telemetry_day7.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Event log contains 7 canonical entries for Days 1-7
- Zero broker calls validated
- Provenance mode: `demo_only_governance_accepted`
- Latest governed scanner artifact on disk: `data/shadow_evidence/daily_scanner_day6.json`
- Latest governed C3 delta artifact on disk: `data/shadow_evidence/c3_delta_day6.json`

**Locked governance chain**
- `D-254`: Phase 48 contingent bridge
- `D-255`: Shadow-evidence review / demo-only acceptance lineage
- `D-256`: workers may not open new phases without explicit CEO sign-off
- `D-257`: Phase 50 paper-curve runway authorization
- `D-258`: canonical-vs-compatibility artifact contract alignment
- `D-260`: Day 4 runway continuation lock and worker-guide activation
- `D-261`: Day 5 runway continuation lock and worker-guide activation
- `D-262`: Day 6 runway continuation lock and worker-guide activation
- `D-263`: Day 7 runway continuation lock and worker-guide activation
- `D-264`: Day 8 runway continuation lock and Phase 51 docs-only planning reminder

---

## Scope Lock

### Allowed
- Publish this worker guide and point the active Phase 50 brief/context at it
- Create `docs/handover/phase50_day8_ceo_memo_20260319.md` using the corrected Day 7 memo structure
- Create `docs/phase_brief/phase51-factor-algebra-design.md` as an interface-only, docs-only planning draft
- Extend the bounded Phase 50 generator and targeted tests only if needed to support Day 8-specific artifact names or latest-day telemetry behavior
- Refresh the Elite Sovereign telemetry view and targeted tests only if needed to keep latest-day behavior accurate for Day 8
- Emit Day 8 canonical artifacts under `data/processed/phase50_shadow_ship/`
- Emit Day 8 compatibility mirrors under `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Append or upsert the Day 8 paper-curve telemetry event in `data/telemetry/phase50_paper_curve_events.jsonl`
- Capture a real Day 8 screenshot at `docs/images/phase50_day8_dashboard_20260319.png`
- Refresh context and publish SAW closeout for the Day 8 continuation round

### Forbidden
- Opening Phase 51 or any other new phase
- Implementing any Phase 51 runtime, parser, evaluator, or operator-overloading code
- Any production promotion, broker routing, or live-capital path
- Reclassifying demo outputs as production or live evidence
- Modifying the canonical bridge `docs/handover/sovereign_promotion_package_20260313.md`
- Rewriting Phase 48 evidence provenance or removing demo-only language
- Accepting screenshot deferral for Day 8 without explicit new CEO authorization
- Fabricating a new `daily_scanner_day8.json` or `c3_delta_day8.json` if governance has not produced them
- Changing thresholds, sleeves, `permno`, governed cost-model rules, or vendor scope

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase50-day8-worker-execution-guide.md`
- `docs/handover/phase50_day8_ceo_memo_20260319.md`
- `docs/images/phase50_day8_dashboard_20260319.png`
- `docs/saw_reports/saw_phase50_day8_runtime_closeout_20260319.md`
- `docs/phase_brief/phase51-factor-algebra-design.md`

### Update
- `docs/phase_brief/phase50-brief.md`
- `docs/phase_brief/phase50-shadow-ship-readiness.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json` via `scripts/build_context_packet.py`
- `docs/context/current_context.md` via `scripts/build_context_packet.py`
- `scripts/capture_dashboard_screenshot.py` only if a validator fails first
- `tests/test_elite_sovereign_view.py` only if a validator fails first
- `scripts/run_phase50_paper_curve.py` only if a validator fails first
- `tests/test_phase50_paper_curve.py` only if a validator fails first

### Runtime surface authorized for Day 8 execution
- `scripts/run_phase50_paper_curve.py`
- `tests/test_phase50_paper_curve.py`
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `scripts/capture_dashboard_screenshot.py`
- `data/processed/phase50_shadow_ship/`
- `data/shadow_evidence/`
- `data/processed/phase50_gate/`
- `data/telemetry/phase50_paper_curve_events.jsonl`

### Read-Only Inputs
- `docs/handover/phase50_day7_ceo_memo_20260318.md`
- `docs/saw_reports/saw_phase50_day7_runtime_closeout_20260318.md`
- `docs/images/phase50_day7_dashboard_20260318.png`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- `docs/handover/sovereign_promotion_package_20260313.md`
- `data/processed/phase50_shadow_ship/paper_curve_day7.csv`
- `data/processed/phase50_shadow_ship/telemetry_day7.json`
- `data/shadow_evidence/daily_scanner_day6.json`
- `data/shadow_evidence/c3_delta_day6.json`
- `data/shadow_evidence/telemetry_summary_5day.json`

### Do Not Touch Unless a Validator Fails First
- `docs/handover/sovereign_promotion_package_20260313.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- Day 1-Day 7 canonical artifacts and Day 1-Day 7 CEO memos
- Any file under a future Phase 51 implementation surface outside the design draft

---

## Execution Order

### Step 1 - Reconfirm Day 7 Baseline
Before any Day 8 extension, validate that the corrected Day 7 bounded surface is still intact.

Targeted suite:
```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
```

Context validator:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

If the Day 7 baseline is drifting, stop and publish `BLOCK` before touching the Day 8 runtime surface.

### Step 2 - Harper: Publish the Day 8 CEO Memo + Phase 51 Design Draft
Create:
- `docs/handover/phase50_day8_ceo_memo_20260319.md`
- `docs/phase_brief/phase51-factor-algebra-design.md`

Template rules for the Day 8 memo:
- mirror the corrected Day 7 memo structure
- keep the decision scope as `Continue / Edit / Hold` inside Phase 50 only
- include updated `active_days_observed / 150`
- include updated cumulative equity through Day 8
- include an updated C3 delta table sourced from the latest governed delta artifact actually used
- state scanner provenance explicitly if the generator reuses the latest accepted governed scanner file
- keep the reply contract restricted to the current phase
- preserve the no-new-phase language from `D-256`
- do not claim a screenshot unless the file is actually attached on disk and visibly usable

Template rules for the Phase 51 design draft:
- docs-only planning artifact; no code and no implementation instructions
- include interface examples, type boundaries, and operator-overloading spec only
- state explicitly that Phase 51 is not open and implementation remains blocked until the Phase 50 curve gate passes
- do not prescribe data migrations, broker surfaces, or runtime activation work

### Step 3 - Benjamin: Execute the Day 8 Paper-Curve Run
If the current generator is not yet Day 8-clean, extend it only inside the authorized Day 8 runtime surface.

Required Day 8 artifact contract:

Canonical outputs:
- `data/processed/phase50_shadow_ship/paper_curve_day8.csv`
- `data/processed/phase50_shadow_ship/telemetry_day8.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`

Allowed supporting output if needed:
- `data/processed/phase50_shadow_ship/paper_curve_positions_day8.csv`

Compatibility mirrors:
- `data/shadow_evidence/paper_curve_day8.csv`
- `data/shadow_evidence/telemetry_day8.json`
- `data/processed/phase50_gate/gate_recommendation.json`

Telemetry/event log:
- append or upsert Day 8 entry in `data/telemetry/phase50_paper_curve_events.jsonl`

Runtime rules:
- preserve Day 1-Day 7 artifacts; do not overwrite them with Day 8 filenames
- keep `core.engine.run_simulation` as the PnL source of truth
- keep `status=SIMULATED`, `broker_calls_detected=0`, and explicit demo provenance
- update `active_days_observed` to the truthful Day 8 count
- keep canonical and compatibility Day 8 mirrors content-equivalent
- if no governed `daily_scanner_day8.json` exists, rely on the approved generator fallback to the latest accepted governed scanner artifact
- if no governed `c3_delta_day8.json` exists, use `data/shadow_evidence/c3_delta_day6.json` as the latest accepted governed delta artifact

Preferred command if a governed Day 8 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 8 --c3-delta data/shadow_evidence/c3_delta_day8.json
```

Fallback command if no governed Day 8 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 8 --c3-delta data/shadow_evidence/c3_delta_day6.json
```

If the fallback is used, the Day 8 memo and reply must state that the C3 delta table uses the latest accepted governed artifact rather than a fabricated Day 8 file. If the generator reuses the Day 6 scanner file, the memo and reply must state that scanner provenance explicitly.

### Step 4 - Lucas: Refresh the Dashboard Telemetry Surface
If the dashboard is still drifting, update it only inside:
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `scripts/capture_dashboard_screenshot.py`

Required behavior:
- load the latest available Phase 50 runway day
- preserve the canonical runtime directory as the dashboard source of truth
- show Day 8 daily PnL, turnover, crisis-turnover, and active-days state
- keep the zero-broker-call and demo-provenance banners explicit
- capture a real screenshot at `docs/images/phase50_day8_dashboard_20260319.png`

### Step 5 - Prepare the Acceptance Proof Reply
Reply format is locked by governance.

The final reply for the Day 8 round must contain only:
- Day 8 memo path
- acceptance proof summary with:
  - one screenshot
  - one telemetry excerpt with `2026-03-19` realized date
  - one updated C3 delta table
- Phase 51 design draft path

No extra narrative, no phase-opening language, and no production implication is allowed in the reply.

---

## Acceptance Checks for This Round

- `CHK-P50-D8-01`: `docs/phase_brief/phase50-day8-worker-execution-guide.md` exists and keeps the runtime scope inside Phase 50 only.
- `CHK-P50-D8-02`: Day 8 owned file surface is explicit for docs, scripts, dashboard, tests, canonical outputs, compatibility mirrors, screenshot, event log, and the Phase 51 docs-only draft.
- `CHK-P50-D8-03`: The guide preserves all hard quarantines, explicitly forbids worker-opened new phases, and keeps Phase 51 work docs-only.
- `CHK-P50-D8-04`: The Day 8 artifact contract is explicit for canonical outputs, compatibility mirrors, latest-day dashboard behavior, screenshot requirement, reply format, governed scanner fallback, and governed C3 delta sourcing.
- `CHK-P50-D8-05`: `docs/phase_brief/phase50-brief.md` points to this guide as the active next-step handoff and notes the parallel Phase 51 docs-only draft.
- `CHK-P50-D8-06`: `docs/decision log.md` records the CEO Day 8 continuation disposition plus the docs-only Phase 51 planning reminder without opening a new phase.
- `CHK-P50-D8-07`: `docs/lessonss.md` records the Day 8 parallel-planning boundary guardrail.
- `CHK-P50-D8-08`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the updated Phase 50 brief.
- `CHK-P50-D8-09`: Day 8 runtime artifacts, memo, screenshot, and SAW closeout are published and validator-clean.
- `CHK-P50-D8-10`: `docs/phase_brief/phase51-factor-algebra-design.md` exists, stays interface-only, and explicitly states that Phase 51 remains unopened.

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase50-brief.md` so:
- Day 7 approval is reflected as complete
- Day 8 is the active next-step continuation surface
- this worker guide is listed as the immediate handoff
- the New Context Packet points to Day 8 execution plus the Phase 51 docs-only design draft only

### Shadow Readiness Brief
Update `docs/phase_brief/phase50-shadow-ship-readiness.md` so:
- the active next-step handoff points to the Day 8 worker guide
- the historical note states that Phase 51 parallel work remains docs-only

### Decision Log
Add a new decision entry that records:
- CEO disposition `CONTINUE - PHASE 50 RUNWAY LOCKED` dated 2026-03-18 22:51 PDT
- Day 7 evidence plus Day 7 runtime SAW closeout and Day 7 screenshot are accepted as the baseline for the continued runway
- Day 8 worker guidance is the active runtime contract
- `docs/phase_brief/phase51-factor-algebra-design.md` is authorized as a docs-only planning artifact only
- no new phase is opened by this continuation

### Lessons
Add one entry that records:
- when a current-phase runtime round and a future-phase planning draft coexist, the worker guide must keep the future phase fenced to docs-only and must state that the current runtime scope does not expand

### Context Refresh
Build:
```powershell
.venv\Scripts\python scripts\build_context_packet.py
```

Validate:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

Done when both are current and valid:
- `docs/context/current_context.json`
- `docs/context/current_context.md`

---

## Reviewer Mapping (Mandatory)

- **Reviewer A**: strategy correctness, runway-metric continuity, and Phase 51 design-boundary correctness
- **Reviewer B**: runtime / operational boundary discipline and no-broker enforcement
- **Reviewer C**: data integrity, artifact naming, screenshot usability, and canonical-vs-compatibility parity

Ownership rule:
- implementer and reviewers must be distinct agents

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- Day 8 work requires a file surface outside the authorized Day 8 runtime/docs contract
- a worker attempts to open Phase 51, implement Phase 51 code, or imply any new execution surface
- a broker-capable or live-capital path appears anywhere in the Day 8 round
- Day 8 artifacts drop demo provenance or zero-broker-call guarantees
- the requested proof package cannot include a real usable Day 8 screenshot, telemetry excerpt, governed C3 delta table, and the Phase 51 design draft path

---

## Hard Blocks

- No Phase 51 or other new phase opening
- No Phase 51 code implementation
- No broker submission
- No live capital
- No production promotion
- No threshold changes
- No `permno` migration
- No governed `10` bps rewrite
- No new sleeves
- No vendor workaround
- No reinterpretation of paper outputs as production authorization

---

## Deliverables

- `docs/phase_brief/phase50-day8-worker-execution-guide.md`
- `docs/handover/phase50_day8_ceo_memo_20260319.md`
- `docs/images/phase50_day8_dashboard_20260319.png`
- `docs/phase_brief/phase51-factor-algebra-design.md`
- Day 8 canonical artifacts:
  - `data/processed/phase50_shadow_ship/paper_curve_day8.csv`
  - `data/processed/phase50_shadow_ship/telemetry_day8.json`
  - `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Day 8 compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day8.csv`
  - `data/shadow_evidence/telemetry_day8.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Day 8 event-log upsert in `data/telemetry/phase50_paper_curve_events.jsonl`
- Elite Sovereign dashboard showing latest Phase 50 runway day
- Final reply containing only the Day 8 memo path plus the acceptance proof summary and the Phase 51 design draft path
- `docs/saw_reports/saw_phase50_day8_runtime_closeout_20260319.md`
