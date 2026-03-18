# Phase 50 Day 2 Worker Execution Guide

**Date**: 2026-03-12
**Round ID**: `P50-D2-RUNWAY-01`
**Scope**: Bounded Day 2 continuation inside the already authorized Phase 50 paper-only runway
**Authorization Source**: CEO disposition dated 2026-03-12 02:51 PDT (`CONTINUE - PHASE 50 RUNWAY LOCKED`)
**Do Not Do**: open Phase 51, open any new execution surface, route to any broker, deploy live capital, change thresholds, migrate `permno`, rewrite governed `10` bps cost logic, add sleeves, or use vendor workarounds

---

## Mission

Continue the official 30-day Phase 50 paper-only runway by adding the Day 2 artifact set, refreshing the Elite Sovereign dashboard to the latest runway day, and publishing the Day 2 CEO checkpoint memo in the exact reply format requested by governance.

This is a bounded continuation round inside Phase 50 only. It is not a new phase opening, not a promotion packet, and not an authorization for live execution.

**Frozen runway truth from Day 1**
- Day 1 memo: `docs/handover/phase50_day1_ceo_memo_20260312.md`
- Canonical Day 1 curve: `data/processed/phase50_shadow_ship/paper_curve_day1.csv`
- Canonical Day 1 telemetry: `data/processed/phase50_shadow_ship/telemetry_day1.json`
- Canonical Day 1 gate stub: `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day1.csv`
  - `data/shadow_evidence/telemetry_day1.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Zero broker calls validated
- Provenance mode: `demo_only_governance_accepted`

**Locked governance chain**
- `D-254`: Phase 48 contingent bridge
- `D-255`: Shadow-evidence review / demo-only acceptance lineage
- `D-256`: workers may not open new phases without explicit CEO sign-off
- `D-257`: Phase 50 paper-curve runway authorization
- `D-258`: canonical-vs-compatibility artifact contract alignment

---

## Scope Lock

### Allowed
- Publish this worker guide and point the active Phase 50 brief/context at it
- Create `docs/handover/phase50_day2_ceo_memo_20260313.md` using the Day 1 memo structure
- Extend the bounded Phase 50 generator and targeted tests if needed to support Day 2-specific artifact names
- Extend the Elite Sovereign telemetry view and targeted tests if needed to read the latest available Phase 50 runway day instead of Day 1-only filenames
- Emit Day 2 canonical artifacts under `data/processed/phase50_shadow_ship/`
- Emit Day 2 compatibility mirrors under `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Append Day 2 paper-curve telemetry to `data/telemetry/phase50_paper_curve_events.jsonl`
- Refresh context and publish SAW closeout for the Day 2 continuation round

### Forbidden
- Opening Phase 51 or any other new phase
- Any production promotion, broker routing, or live-capital path
- Reclassifying demo outputs as production or live evidence
- Modifying the canonical bridge `docs/handover/sovereign_promotion_package_20260313.md`
- Rewriting Phase 48 evidence provenance or removing demo-only language
- Changing thresholds, sleeves, `permno`, governed cost-model rules, or vendor scope

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase50-day2-worker-execution-guide.md`
- `docs/handover/phase50_day2_ceo_memo_20260313.md`
- `docs/images/phase50_day2_dashboard_20260313.png`
- `docs/saw_reports/saw_phase50_day2_worker_execution_20260312.md`

### Update
- `docs/phase_brief/phase50-brief.md`
- `docs/phase_brief/phase50-shadow-ship-readiness.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/current_context.json` via `scripts/build_context_packet.py`
- `docs/context/current_context.md` via `scripts/build_context_packet.py`

### Runtime surface authorized for Day 2 execution
- `scripts/run_phase50_paper_curve.py`
- `tests/test_phase50_paper_curve.py`
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `data/processed/phase50_shadow_ship/`
- `data/shadow_evidence/`
- `data/processed/phase50_gate/`
- `data/telemetry/phase50_paper_curve_events.jsonl`

### Read-Only Inputs
- `docs/handover/phase50_day1_ceo_memo_20260312.md`
- `docs/saw_reports/saw_phase50_shadow_ship_readiness_20260311.md`
- `docs/saw_reports/saw_phase50_artifact_contract_alignment_20260311.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- `docs/handover/sovereign_promotion_package_20260313.md`
- `data/processed/phase50_shadow_ship/paper_curve_day1.csv`
- `data/processed/phase50_shadow_ship/telemetry_day1.json`
- `data/shadow_evidence/daily_scanner_day2.json`
- `data/shadow_evidence/c3_delta_day2.json`
- `data/shadow_evidence/telemetry_summary_5day.json`

### Do Not Touch Unless a Validator Fails First
- `docs/handover/sovereign_promotion_package_20260313.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- Day 1 canonical artifacts and Day 1 CEO memo

---

## Execution Order

### Step 1 — Reconfirm Day 1 Baseline
Before any Day 2 extension, validate that the Day 1 bounded surface is still intact.

Targeted suite:
```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
```

Context validator:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

If the Day 1 baseline is drifting, stop and publish `BLOCK` before touching the Day 2 runtime surface.

### Step 2 — Harper: Publish the Day 2 CEO Memo Template
Create:
- `docs/handover/phase50_day2_ceo_memo_20260313.md`

Template rules:
- mirror the Day 1 memo structure
- keep the decision scope as `Continue / Edit / Hold` inside Phase 50 only
- include updated `active_days_observed / 150`
- include an updated C3 delta table with explicit demo-only provenance
- keep the reply contract restricted to the current phase
- preserve the no-new-phase language from `D-256`

### Step 3 — Benjamin: Execute the Day 2 Paper-Curve Run
If the current generator is Day 1-only, extend it only inside the authorized Day 2 runtime surface.

Required Day 2 artifact contract:

Canonical outputs:
- `data/processed/phase50_shadow_ship/paper_curve_day2.csv`
- `data/processed/phase50_shadow_ship/telemetry_day2.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`

Allowed supporting output if needed:
- `data/processed/phase50_shadow_ship/paper_curve_positions_day2.csv`

Compatibility mirrors:
- `data/shadow_evidence/paper_curve_day2.csv`
- `data/shadow_evidence/telemetry_day2.json`
- `data/processed/phase50_gate/gate_recommendation.json`

Telemetry/event log:
- append Day 2 entry to `data/telemetry/phase50_paper_curve_events.jsonl`

Runtime rules:
- preserve Day 1 artifacts; do not overwrite them with Day 2 filenames
- keep `core.engine.run_simulation` as the PnL source of truth
- keep `status=SIMULATED`, `broker_calls_detected=0`, and explicit demo provenance
- update `active_days_observed` to the truthful Day 2 count
- keep canonical and compatibility Day 2 mirrors content-equivalent

Planned command contract for the Day 2 round:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 2 --c3-delta data/shadow_evidence/c3_delta_day2.json
```

If a fresh `c3_delta_day2.json` is not available, stop and escalate rather than fabricating a Day 2 delta refresh.

### Step 4 — Lucas: Refresh the Dashboard Telemetry Surface
If the dashboard is still bound to Day 1-only filenames, update it only inside:
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`

Required behavior:
- load the latest available Phase 50 runway day
- preserve the canonical runtime directory as the dashboard source of truth
- show Day 2 daily PnL, turnover, crisis-turnover, and active-days state
- keep the zero-broker-call and demo-provenance banners explicit

### Step 5 — Prepare the Acceptance Proof Reply
Reply format is locked by governance.

The final reply for the Day 2 round must contain only:
- Day 2 memo path
- acceptance proof summary with:
  - one screenshot
  - one telemetry excerpt
  - one updated C3 delta table

No extra narrative, no phase-opening language, and no production implication is allowed in the reply.

---

## Acceptance Checks for This Round

- `CHK-P50-D2-01`: `docs/phase_brief/phase50-day2-worker-execution-guide.md` exists and keeps the scope inside Phase 50 only.
- `CHK-P50-D2-02`: Day 2 owned file surface is explicit for docs, script, dashboard, tests, canonical outputs, compatibility mirrors, and event log.
- `CHK-P50-D2-03`: The guide preserves all hard quarantines and explicitly forbids any worker-opened new phase.
- `CHK-P50-D2-04`: The Day 2 artifact contract is explicit for canonical outputs, compatibility mirrors, latest-day dashboard behavior, and proof reply format.
- `CHK-P50-D2-05`: `docs/phase_brief/phase50-brief.md` points to this guide as the active next-step handoff.
- `CHK-P50-D2-06`: `docs/decision log.md` records the CEO Day 2 continuation disposition and the worker-guide activation.
- `CHK-P50-D2-07`: `docs/lessonss.md` records the daily-runway guidance guardrail.
- `CHK-P50-D2-08`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the updated Phase 50 brief.
- `CHK-P50-D2-09`: Docs-only SAW report is published and validator-clean.

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase50-brief.md` so:
- Day 1 approval is reflected as complete
- Day 2 is the active next-step continuation surface
- this worker guide is listed as the immediate handoff
- the New Context Packet points to Day 2 execution and proof packaging only

### Decision Log
Add a new decision entry that records:
- CEO disposition `CONTINUE - PHASE 50 RUNWAY LOCKED` dated 2026-03-12 02:51 PDT
- Day 1 evidence is accepted as the baseline for the continued runway
- Day 2 worker guidance is the active contract
- no new phase is opened by this continuation

### Lessons
Add one entry that records:
- once a phase is already open, the next worker guide must lock the daily artifact contract and exact reply shape rather than restating a phase-opening memo

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
- **Reviewer C**: data integrity, artifact naming, and canonical-vs-compatibility parity

Ownership rule:
- implementer and reviewers must be distinct agents

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- Day 2 work requires a file surface outside the authorized Day 2 runtime/docs contract
- a worker attempts to open Phase 51 or imply any new execution surface
- a broker-capable or live-capital path appears anywhere in the Day 2 round
- Day 2 artifacts drop demo provenance or zero-broker-call guarantees
- the requested proof package cannot include a real Day 2 screenshot, telemetry excerpt, and updated C3 delta table

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

- `docs/phase_brief/phase50-day2-worker-execution-guide.md`
- `docs/handover/phase50_day2_ceo_memo_20260313.md`
- `docs/images/phase50_day2_dashboard_20260313.png`
- Day 2 canonical artifacts:
  - `data/processed/phase50_shadow_ship/paper_curve_day2.csv`
  - `data/processed/phase50_shadow_ship/telemetry_day2.json`
  - `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Day 2 compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day2.csv`
  - `data/shadow_evidence/telemetry_day2.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Day 2 event-log append in `data/telemetry/phase50_paper_curve_events.jsonl`
- Elite Sovereign dashboard showing latest Phase 50 runway day
- Final reply containing only the Day 2 memo path plus the acceptance proof summary
- `docs/saw_reports/saw_phase50_day2_worker_execution_20260312.md`
