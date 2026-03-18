# Phase 50 Day 4 Worker Execution Guide

**Date**: 2026-03-14
**Round ID**: `P50-D4-RUNWAY-01`
**Scope**: Bounded Day 4 continuation inside the already authorized Phase 50 paper-only runway
**Authorization Source**: CEO disposition dated 2026-03-14 03:17 PDT (`CONTINUE - PHASE 50 RUNWAY LOCKED`)
**Do Not Do**: open Phase 51, open any new execution surface, route to any broker, deploy live capital, change thresholds, migrate `permno`, rewrite governed `10` bps cost logic, add sleeves, or use vendor workarounds

---

## Mission

Continue the official 30-day Phase 50 paper-only runway by adding the Day 4 artifact set, refreshing the Elite Sovereign dashboard to the latest runway day, capturing a real Day 4 screenshot, and publishing the Day 4 CEO checkpoint memo in the exact reply format requested by governance.

This is a bounded continuation round inside Phase 50 only. It is not a new phase opening, not a promotion packet, and not an authorization for live execution.

**Frozen runway truth from Day 3**
- Day 3 memo: `docs/handover/phase50_day3_ceo_memo_20260314.md`
- Canonical Day 3 curve: `data/processed/phase50_shadow_ship/paper_curve_day3.csv`
- Canonical Day 3 telemetry: `data/processed/phase50_shadow_ship/telemetry_day3.json`
- Canonical Day 3 gate stub: `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day3.csv`
  - `data/shadow_evidence/telemetry_day3.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Event log contains 3 canonical entries for Days 1-3
- Zero broker calls validated
- Provenance mode: `demo_only_governance_accepted`

**Locked governance chain**
- `D-254`: Phase 48 contingent bridge
- `D-255`: Shadow-evidence review / demo-only acceptance lineage
- `D-256`: workers may not open new phases without explicit CEO sign-off
- `D-257`: Phase 50 paper-curve runway authorization
- `D-258`: canonical-vs-compatibility artifact contract alignment
- `D-259`: Day 2 runway continuation lock
- `D-260`: Day 4 runway continuation lock and worker-guide activation

---

## Scope Lock

### Allowed
- Publish this worker guide and point the active Phase 50 brief/context at it
- Create `docs/handover/phase50_day4_ceo_memo_20260315.md` using the corrected Day 3 memo structure
- Extend the bounded Phase 50 generator and targeted tests only if needed to support Day 4-specific artifact names or screenshot proof capture
- Refresh the Elite Sovereign telemetry view and targeted tests only if needed to keep latest-day behavior accurate for Day 4
- Emit Day 4 canonical artifacts under `data/processed/phase50_shadow_ship/`
- Emit Day 4 compatibility mirrors under `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Append or upsert the Day 4 paper-curve telemetry event in `data/telemetry/phase50_paper_curve_events.jsonl`
- Capture a real Day 4 screenshot at `docs/images/phase50_day4_dashboard_20260315.png`
- Refresh context and publish SAW closeout for the Day 4 continuation round

### Forbidden
- Opening Phase 51 or any other new phase
- Any production promotion, broker routing, or live-capital path
- Reclassifying demo outputs as production or live evidence
- Modifying the canonical bridge `docs/handover/sovereign_promotion_package_20260313.md`
- Rewriting Phase 48 evidence provenance or removing demo-only language
- Accepting image deferral for Day 4 without explicit new CEO authorization
- Changing thresholds, sleeves, `permno`, governed cost-model rules, or vendor scope

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase50-day4-worker-execution-guide.md`
- `docs/handover/phase50_day4_ceo_memo_20260315.md`
- `docs/images/phase50_day4_dashboard_20260315.png`
- `docs/saw_reports/saw_phase50_day4_worker_execution_20260314.md`

### Update
- `docs/phase_brief/phase50-brief.md`
- `docs/phase_brief/phase50-shadow-ship-readiness.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json` via `scripts/build_context_packet.py`
- `docs/context/current_context.md` via `scripts/build_context_packet.py`

### Runtime surface authorized for Day 4 execution
- `scripts/run_phase50_paper_curve.py`
- `tests/test_phase50_paper_curve.py`
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `data/processed/phase50_shadow_ship/`
- `data/shadow_evidence/`
- `data/processed/phase50_gate/`
- `data/telemetry/phase50_paper_curve_events.jsonl`

### Read-Only Inputs
- `docs/handover/phase50_day3_ceo_memo_20260314.md`
- `docs/saw_reports/saw_phase50_day2_worker_execution_20260312.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- `docs/handover/sovereign_promotion_package_20260313.md`
- `data/processed/phase50_shadow_ship/paper_curve_day3.csv`
- `data/processed/phase50_shadow_ship/telemetry_day3.json`
- `data/shadow_evidence/daily_scanner_day4.json`
- `data/shadow_evidence/c3_delta_day4.json`
- `data/shadow_evidence/telemetry_summary_5day.json`

### Do Not Touch Unless a Validator Fails First
- `docs/handover/sovereign_promotion_package_20260313.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- Day 1-Day 3 canonical artifacts and Day 1-Day 3 CEO memos

---

## Execution Order

### Step 1 - Reconfirm Day 3 Baseline
Before any Day 4 extension, validate that the Day 3 bounded surface is still intact.

Targeted suite:
```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
```

Context validator:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

If the Day 3 baseline is drifting, stop and publish `BLOCK` before touching the Day 4 runtime surface.

### Step 2 - Harper: Publish the Day 4 CEO Memo Template
Create:
- `docs/handover/phase50_day4_ceo_memo_20260315.md`

Template rules:
- mirror the corrected Day 3 memo structure
- keep the decision scope as `Continue / Edit / Hold` inside Phase 50 only
- include updated `active_days_observed / 150`
- include updated cumulative equity through Day 4
- include an updated C3 delta table with explicit demo-only provenance
- keep the reply contract restricted to the current phase
- preserve the no-new-phase language from `D-256`
- do not claim a screenshot unless the file is actually attached on disk

### Step 3 - Benjamin: Execute the Day 4 Paper-Curve Run
If the current generator is not yet Day 4-clean, extend it only inside the authorized Day 4 runtime surface.

Required Day 4 artifact contract:

Canonical outputs:
- `data/processed/phase50_shadow_ship/paper_curve_day4.csv`
- `data/processed/phase50_shadow_ship/telemetry_day4.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`

Allowed supporting output if needed:
- `data/processed/phase50_shadow_ship/paper_curve_positions_day4.csv`

Compatibility mirrors:
- `data/shadow_evidence/paper_curve_day4.csv`
- `data/shadow_evidence/telemetry_day4.json`
- `data/processed/phase50_gate/gate_recommendation.json`

Telemetry/event log:
- append or upsert Day 4 entry in `data/telemetry/phase50_paper_curve_events.jsonl`

Runtime rules:
- preserve Day 1-Day 3 artifacts; do not overwrite them with Day 4 filenames
- keep `core.engine.run_simulation` as the PnL source of truth
- keep `status=SIMULATED`, `broker_calls_detected=0`, and explicit demo provenance
- update `active_days_observed` to the truthful Day 4 count
- keep canonical and compatibility Day 4 mirrors content-equivalent

Planned command contract for the Day 4 round:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 4 --c3-delta data/shadow_evidence/c3_delta_day4.json
```

If a fresh `c3_delta_day4.json` is not available, stop and escalate rather than fabricating a Day 4 delta refresh.

### Step 4 - Lucas: Refresh the Dashboard Telemetry Surface
If the dashboard is still drifting, update it only inside:
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`

Required behavior:
- load the latest available Phase 50 runway day
- preserve the canonical runtime directory as the dashboard source of truth
- show Day 4 daily PnL, turnover, crisis-turnover, and active-days state
- keep the zero-broker-call and demo-provenance banners explicit
- capture a real screenshot at `docs/images/phase50_day4_dashboard_20260315.png`

### Step 5 - Prepare the Acceptance Proof Reply
Reply format is locked by governance.

The final reply for the Day 4 round must contain only:
- Day 4 memo path
- acceptance proof summary with:
  - one screenshot
  - one telemetry excerpt with `2026-03-15` realized date
  - one updated C3 delta table

No extra narrative, no phase-opening language, and no production implication is allowed in the reply.

---

## Acceptance Checks for This Round

- `CHK-P50-D4-01`: `docs/phase_brief/phase50-day4-worker-execution-guide.md` exists and keeps the scope inside Phase 50 only.
- `CHK-P50-D4-02`: Day 4 owned file surface is explicit for docs, script, dashboard, tests, canonical outputs, compatibility mirrors, screenshot, and event log.
- `CHK-P50-D4-03`: The guide preserves all hard quarantines and explicitly forbids any worker-opened new phase.
- `CHK-P50-D4-04`: The Day 4 artifact contract is explicit for canonical outputs, compatibility mirrors, latest-day dashboard behavior, screenshot requirement, and proof reply format.
- `CHK-P50-D4-05`: `docs/phase_brief/phase50-brief.md` points to this guide as the active next-step handoff.
- `CHK-P50-D4-06`: `docs/decision log.md` records the CEO Day 4 continuation disposition without opening a new phase.
- `CHK-P50-D4-07`: `docs/lessonss.md` records the Day 4 screenshot/no-overclaim guardrail.
- `CHK-P50-D4-08`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the updated Phase 50 brief.
- `CHK-P50-D4-09`: Docs-only SAW report is published and validator-clean.

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase50-brief.md` so:
- Day 3 approval is reflected as complete
- Day 4 is the active next-step continuation surface
- this worker guide is listed as the immediate handoff
- the New Context Packet points to Day 4 execution and proof packaging only

### Decision Log
Add a new decision entry that records:
- CEO disposition `CONTINUE - PHASE 50 RUNWAY LOCKED` dated 2026-03-14 03:17 PDT
- Day 3 evidence is accepted as the baseline for the continued runway
- Day 4 worker guidance is the active contract
- no new phase is opened by this continuation

### Lessons
Add one entry that records:
- once image deferral is accepted for one checkpoint, the next guide must say explicitly whether screenshot capture is optional or mandatory before the next worker starts

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
- **Reviewer C**: data integrity, artifact naming, screenshot presence, and canonical-vs-compatibility parity

Ownership rule:
- implementer and reviewers must be distinct agents

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- Day 4 work requires a file surface outside the authorized Day 4 runtime/docs contract
- a worker attempts to open Phase 51 or imply any new execution surface
- a broker-capable or live-capital path appears anywhere in the Day 4 round
- Day 4 artifacts drop demo provenance or zero-broker-call guarantees
- the requested proof package cannot include a real Day 4 screenshot, telemetry excerpt, and updated C3 delta table

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

- `docs/phase_brief/phase50-day4-worker-execution-guide.md`
- `docs/handover/phase50_day4_ceo_memo_20260315.md`
- `docs/images/phase50_day4_dashboard_20260315.png`
- Day 4 canonical artifacts:
  - `data/processed/phase50_shadow_ship/paper_curve_day4.csv`
  - `data/processed/phase50_shadow_ship/telemetry_day4.json`
  - `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Day 4 compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day4.csv`
  - `data/shadow_evidence/telemetry_day4.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Day 4 event-log upsert in `data/telemetry/phase50_paper_curve_events.jsonl`
- Elite Sovereign dashboard showing latest Phase 50 runway day
- Final reply containing only the Day 4 memo path plus the acceptance proof summary
- `docs/saw_reports/saw_phase50_day4_worker_execution_20260314.md`
