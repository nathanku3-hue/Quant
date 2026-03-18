# Phase 50 Day 6 Worker Execution Guide

**Date**: 2026-03-16
**Round ID**: `P50-D6-RUNWAY-01`
**Scope**: Bounded Day 6 continuation inside the already authorized Phase 50 paper-only runway
**Authorization Source**: CEO disposition dated 2026-03-16 20:07 PDT (`CONTINUE - PHASE 50 RUNWAY LOCKED`)
**Do Not Do**: open Phase 51, open any new execution surface, route to any broker, deploy live capital, change thresholds, migrate `permno`, rewrite governed `10` bps cost logic, add sleeves, or use vendor workarounds

---

## Mission

Continue the official 30-day Phase 50 paper-only runway by adding the Day 6 artifact set, refreshing the Elite Sovereign dashboard to the latest runway day, capturing a real Day 6 screenshot, and publishing the Day 6 CEO checkpoint memo in the exact reply format requested by governance.

This is a bounded continuation round inside Phase 50 only. It is not a new phase opening, not a promotion packet, and not an authorization for live execution.

**Frozen runway truth from Day 5**
- Day 5 memo: `docs/handover/phase50_day5_ceo_memo_20260316.md`
- Day 5 runtime SAW closeout: `docs/saw_reports/saw_phase50_day5_runtime_closeout_20260316.md`
- Day 5 proof image: `docs/images/phase50_day5_dashboard_20260316.png`
- Canonical Day 5 curve: `data/processed/phase50_shadow_ship/paper_curve_day5.csv`
- Canonical Day 5 telemetry: `data/processed/phase50_shadow_ship/telemetry_day5.json`
- Canonical Day 5 gate stub: `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day5.csv`
  - `data/shadow_evidence/telemetry_day5.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Event log contains 5 canonical entries for Days 1-5
- Zero broker calls validated
- Provenance mode: `demo_only_governance_accepted`

**Locked governance chain**
- `D-254`: Phase 48 contingent bridge
- `D-255`: Shadow-evidence review / demo-only acceptance lineage
- `D-256`: workers may not open new phases without explicit CEO sign-off
- `D-257`: Phase 50 paper-curve runway authorization
- `D-258`: canonical-vs-compatibility artifact contract alignment
- `D-260`: Day 4 runway continuation lock and worker-guide activation
- `D-261`: Day 5 runway continuation lock and worker-guide activation
- `D-262`: Day 6 runway continuation lock and worker-guide activation

---

## Scope Lock

### Allowed
- Publish this worker guide and point the active Phase 50 brief/context at it
- Create `docs/handover/phase50_day6_ceo_memo_20260317.md` using the corrected Day 5 memo structure
- Extend the bounded Phase 50 generator and targeted tests only if needed to support Day 6-specific artifact names or latest-day telemetry behavior
- Refresh the Elite Sovereign telemetry view and targeted tests only if needed to keep latest-day behavior accurate for Day 6
- Emit Day 6 canonical artifacts under `data/processed/phase50_shadow_ship/`
- Emit Day 6 compatibility mirrors under `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Append or upsert the Day 6 paper-curve telemetry event in `data/telemetry/phase50_paper_curve_events.jsonl`
- Capture a real Day 6 screenshot at `docs/images/phase50_day6_dashboard_20260317.png`
- Refresh context and publish SAW closeout for the Day 6 continuation round

### Forbidden
- Opening Phase 51 or any other new phase
- Any production promotion, broker routing, or live-capital path
- Reclassifying demo outputs as production or live evidence
- Modifying the canonical bridge `docs/handover/sovereign_promotion_package_20260313.md`
- Rewriting Phase 48 evidence provenance or removing demo-only language
- Accepting screenshot deferral for Day 6 without explicit new CEO authorization
- Fabricating a new `c3_delta_day6.json` if governance has not produced one
- Changing thresholds, sleeves, `permno`, governed cost-model rules, or vendor scope

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase50-day6-worker-execution-guide.md`
- `docs/handover/phase50_day6_ceo_memo_20260317.md`
- `docs/images/phase50_day6_dashboard_20260317.png`
- `docs/saw_reports/saw_phase50_day6_worker_execution_20260316.md`

### Update
- `docs/phase_brief/phase50-brief.md`
- `docs/phase_brief/phase50-shadow-ship-readiness.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json` via `scripts/build_context_packet.py`
- `docs/context/current_context.md` via `scripts/build_context_packet.py`

### Runtime surface authorized for Day 6 execution
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
- `docs/handover/phase50_day5_ceo_memo_20260316.md`
- `docs/saw_reports/saw_phase50_day5_runtime_closeout_20260316.md`
- `docs/images/phase50_day5_dashboard_20260316.png`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- `docs/handover/sovereign_promotion_package_20260313.md`
- `data/processed/phase50_shadow_ship/paper_curve_day5.csv`
- `data/processed/phase50_shadow_ship/telemetry_day5.json`
- `data/shadow_evidence/c3_delta_day5.json`
- `data/shadow_evidence/telemetry_summary_5day.json`

### Do Not Touch Unless a Validator Fails First
- `docs/handover/sovereign_promotion_package_20260313.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- Day 1-Day 5 canonical artifacts and Day 1-Day 5 CEO memos

---

## Execution Order

### Step 1 - Reconfirm Day 5 Baseline
Before any Day 6 extension, validate that the corrected Day 5 bounded surface is still intact.

Targeted suite:
```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
```

Context validator:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

If the Day 5 baseline is drifting, stop and publish `BLOCK` before touching the Day 6 runtime surface.

### Step 2 - Harper: Publish the Day 6 CEO Memo Template
Create:
- `docs/handover/phase50_day6_ceo_memo_20260317.md`

Template rules:
- mirror the corrected Day 5 memo structure
- keep the decision scope as `Continue / Edit / Hold` inside Phase 50 only
- include updated `active_days_observed / 150`
- include updated cumulative equity through Day 6
- include an updated C3 delta table sourced from the latest governed delta artifact actually used
- keep the reply contract restricted to the current phase
- preserve the no-new-phase language from `D-256`
- do not claim a screenshot unless the file is actually attached on disk and visibly usable

### Step 3 - Benjamin: Execute the Day 6 Paper-Curve Run
If the current generator is not yet Day 6-clean, extend it only inside the authorized Day 6 runtime surface.

Required Day 6 artifact contract:

Canonical outputs:
- `data/processed/phase50_shadow_ship/paper_curve_day6.csv`
- `data/processed/phase50_shadow_ship/telemetry_day6.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`

Allowed supporting output if needed:
- `data/processed/phase50_shadow_ship/paper_curve_positions_day6.csv`

Compatibility mirrors:
- `data/shadow_evidence/paper_curve_day6.csv`
- `data/shadow_evidence/telemetry_day6.json`
- `data/processed/phase50_gate/gate_recommendation.json`

Telemetry/event log:
- append or upsert Day 6 entry in `data/telemetry/phase50_paper_curve_events.jsonl`

Runtime rules:
- preserve Day 1-Day 5 artifacts; do not overwrite them with Day 6 filenames
- keep `core.engine.run_simulation` as the PnL source of truth
- keep `status=SIMULATED`, `broker_calls_detected=0`, and explicit demo provenance
- update `active_days_observed` to the truthful Day 6 count
- keep canonical and compatibility Day 6 mirrors content-equivalent

Preferred command if a governed Day 6 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 6 --c3-delta data/shadow_evidence/c3_delta_day6.json
```

Fallback command if no governed Day 6 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 6 --c3-delta data/shadow_evidence/c3_delta_day5.json
```

If the fallback is used, the Day 6 memo and reply must state that the C3 delta table is carried forward unchanged from the latest accepted governed artifact rather than refreshed with a fabricated Day 6 file.

### Step 4 - Lucas: Refresh the Dashboard Telemetry Surface
If the dashboard is still drifting, update it only inside:
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `scripts/capture_dashboard_screenshot.py`

Required behavior:
- load the latest available Phase 50 runway day
- preserve the canonical runtime directory as the dashboard source of truth
- show Day 6 daily PnL, turnover, crisis-turnover, and active-days state
- keep the zero-broker-call and demo-provenance banners explicit
- capture a real screenshot at `docs/images/phase50_day6_dashboard_20260317.png`

### Step 5 - Prepare the Acceptance Proof Reply
Reply format is locked by governance.

The final reply for the Day 6 round must contain only:
- Day 6 memo path
- acceptance proof summary with:
  - one screenshot
  - one telemetry excerpt with `2026-03-17` realized date
  - one updated C3 delta table

No extra narrative, no phase-opening language, and no production implication is allowed in the reply.

---

## Acceptance Checks for This Round

- `CHK-P50-D6-01`: `docs/phase_brief/phase50-day6-worker-execution-guide.md` exists and keeps the scope inside Phase 50 only.
- `CHK-P50-D6-02`: Day 6 owned file surface is explicit for docs, script, dashboard, tests, canonical outputs, compatibility mirrors, screenshot, and event log.
- `CHK-P50-D6-03`: The guide preserves all hard quarantines and explicitly forbids any worker-opened new phase.
- `CHK-P50-D6-04`: The Day 6 artifact contract is explicit for canonical outputs, compatibility mirrors, latest-day dashboard behavior, screenshot requirement, reply format, and governed C3 delta sourcing.
- `CHK-P50-D6-05`: `docs/phase_brief/phase50-brief.md` points to this guide as the active next-step handoff.
- `CHK-P50-D6-06`: `docs/decision log.md` records the CEO Day 6 continuation disposition without opening a new phase.
- `CHK-P50-D6-07`: `docs/lessonss.md` records the Day 6 baseline-inheritance / delta-source guardrail.
- `CHK-P50-D6-08`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the updated Phase 50 brief.
- `CHK-P50-D6-09`: Docs-only SAW report is published and validator-clean.

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase50-brief.md` so:
- Day 5 approval is reflected as complete
- Day 6 is the active next-step continuation surface
- this worker guide is listed as the immediate handoff
- the New Context Packet points to Day 6 execution and proof packaging only

### Decision Log
Add a new decision entry that records:
- CEO disposition `CONTINUE - PHASE 50 RUNWAY LOCKED` dated 2026-03-16 20:07 PDT
- Day 5 evidence plus Day 5 runtime SAW closeout and Day 5 screenshot are accepted as the baseline for the continued runway
- Day 6 worker guidance is the active contract
- no new phase is opened by this continuation

### Lessons
Add one entry that records:
- once a daily packet is corrected by a runtime reconciliation round, the next worker guide must inherit the corrected memo, runtime SAW closeout, and screenshot as the frozen baseline and must state whether the C3 delta table is fresh or carried forward from the latest governed artifact

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

- **Reviewer A**: strategy correctness and runway-metric continuity
- **Reviewer B**: runtime / operational boundary discipline and no-broker enforcement
- **Reviewer C**: data integrity, artifact naming, screenshot usability, and canonical-vs-compatibility parity

Ownership rule:
- implementer and reviewers must be distinct agents

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- Day 6 work requires a file surface outside the authorized Day 6 runtime/docs contract
- a worker attempts to open Phase 51 or imply any new execution surface
- a broker-capable or live-capital path appears anywhere in the Day 6 round
- Day 6 artifacts drop demo provenance or zero-broker-call guarantees
- the requested proof package cannot include a real usable Day 6 screenshot, telemetry excerpt, and governed C3 delta table

---

## Hard Blocks

- No Phase 51 or other new phase opening
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

- `docs/phase_brief/phase50-day6-worker-execution-guide.md`
- `docs/handover/phase50_day6_ceo_memo_20260317.md`
- `docs/images/phase50_day6_dashboard_20260317.png`
- Day 6 canonical artifacts:
  - `data/processed/phase50_shadow_ship/paper_curve_day6.csv`
  - `data/processed/phase50_shadow_ship/telemetry_day6.json`
  - `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Day 6 compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day6.csv`
  - `data/shadow_evidence/telemetry_day6.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Day 6 event-log upsert in `data/telemetry/phase50_paper_curve_events.jsonl`
- Elite Sovereign dashboard showing latest Phase 50 runway day
- Final reply containing only the Day 6 memo path plus the acceptance proof summary
- `docs/saw_reports/saw_phase50_day6_worker_execution_20260316.md`
