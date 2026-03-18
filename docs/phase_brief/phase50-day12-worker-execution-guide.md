# Phase 50 Day 12 Worker Execution Guide

**Date**: 2026-03-22
**Round ID**: `P50-D12-RUNWAY-01`
**Scope**: Bounded Day 12 continuation inside the already authorized Phase 50 paper-only runway, plus locked docs-only Phase 51 Factor Algebra carry-forward
**Authorization Source**: CEO disposition dated 2026-03-22 (`CONTINUE PHASE 50 RUNWAY`)
**Do Not Do**: open Phase 51, open any new execution surface, route to any broker, deploy live capital, change thresholds, migrate `permno`, rewrite governed `10` bps cost logic, add sleeves, use vendor workarounds, or implement any Phase 51 code

---

## Mission

Continue the official 30-day Phase 50 paper-only runway by adding the Day 12 artifact set, refreshing the Elite Sovereign dashboard to the latest runway day, capturing a real Day 12 screenshot, publishing the Day 12 CEO checkpoint memo in the exact reply format requested by governance, and carrying the Phase 51 Factor Algebra design forward as the locked docs-only planning artifact.

This is a bounded continuation round inside Phase 50 plus a parallel docs-only planning carry-forward for Phase 51. It is not a new phase opening, not a promotion packet, not an authorization for live execution, and not an authorization to implement any Phase 51 code.

**Frozen runway truth from Day 11**
- Day 11 memo: `docs/handover/phase50_day11_ceo_memo_20260322.md`
- Day 11 runtime SAW closeout: `docs/saw_reports/saw_phase50_day11_runtime_closeout_20260322.md`
- Day 11 proof image: `docs/images/phase50_day11_dashboard_20260322.png`
- Canonical Day 11 curve: `data/processed/phase50_shadow_ship/paper_curve_day11.csv`
- Canonical Day 11 telemetry: `data/processed/phase50_shadow_ship/telemetry_day11.json`
- Canonical Day 11 gate stub: `data/processed/phase50_shadow_ship/gate_recommendation.json`
- Compatibility mirrors:
  - `data/shadow_evidence/paper_curve_day11.csv`
  - `data/shadow_evidence/telemetry_day11.json`
  - `data/processed/phase50_gate/gate_recommendation.json`
- Event log contains 11 canonical entries for Days 1-11
- Zero broker calls validated
- Provenance mode: `demo_only_governance_accepted`
- Latest governed scanner artifact on disk: `data/shadow_evidence/daily_scanner_day6.json`
- Latest governed C3 delta artifact on disk: `data/shadow_evidence/c3_delta_day6.json`
- Locked Phase 51 planning draft: `docs/phase_brief/phase51-factor-algebra-design.md`

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
- `D-265`: Day 9 runway continuation lock and Phase 51 design lock carry-forward
- `D-266`: Day 10 runway continuation lock and Phase 51 design-lock confirmation carry-forward
- `D-267`: separately occupied by the Phase 51 docs-only planning hold; do not overwrite or reinterpret it during this Day 12 continuation round
- `D-268`: Day 11 continuation lock and unchanged Phase 51 design confirmation carry-forward
- `D-269`: reserved for the Day 12 continuation lock and unchanged Phase 51 design confirmation carry-forward

---

## Scope Lock

### Allowed
- Publish this worker guide and point the active Phase 50 brief/context at it
- Create `docs/handover/phase50_day12_ceo_memo_20260323.md` using the corrected Day 11 memo structure
- Keep `docs/phase_brief/phase51-factor-algebra-design.md` unchanged unless explicit CEO feedback requires a clarifying docs-only lock note
- Extend the bounded Phase 50 generator and targeted tests only if needed to support Day 12-specific artifact names or latest-day telemetry behavior
- Refresh the Elite Sovereign telemetry view and targeted tests only if needed to keep latest-day behavior accurate for Day 12
- Emit Day 12 canonical artifacts under `data/processed/phase50_shadow_ship/`
- Emit Day 12 compatibility mirrors under `data/shadow_evidence/` and `data/processed/phase50_gate/`
- Append or upsert the Day 12 paper-curve telemetry event in `data/telemetry/phase50_paper_curve_events.jsonl`
- Capture a real Day 12 screenshot at `docs/images/phase50_day12_dashboard_20260323.png`
- Refresh context and publish SAW closeout for the Day 12 continuation round

### Forbidden
- Opening Phase 51 or any other new phase
- Implementing any Phase 51 runtime, parser, evaluator, or operator-overloading code
- Any production promotion, broker routing, or live-capital path
- Reclassifying demo outputs as production or live evidence
- Modifying the canonical bridge `docs/handover/sovereign_promotion_package_20260313.md`
- Rewriting Phase 48 evidence provenance or removing demo-only language
- Accepting screenshot deferral for Day 12 without explicit new CEO authorization
- Fabricating a new `daily_scanner_day12.json` or `c3_delta_day12.json` if governance has not produced them
- Changing thresholds, sleeves, `permno`, governed cost-model rules, or vendor scope

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase50-day12-worker-execution-guide.md`
- `docs/handover/phase50_day12_ceo_memo_20260323.md`
- `docs/images/phase50_day12_dashboard_20260323.png`
- `docs/saw_reports/saw_phase50_day12_runtime_closeout_20260323.md`

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

### Runtime surface authorized for Day 12 execution
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
- `docs/handover/phase50_day11_ceo_memo_20260322.md`
- `docs/saw_reports/saw_phase50_day11_runtime_closeout_20260322.md`
- `docs/images/phase50_day11_dashboard_20260322.png`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- `docs/handover/sovereign_promotion_package_20260313.md`
- `data/processed/phase50_shadow_ship/paper_curve_day11.csv`
- `data/processed/phase50_shadow_ship/telemetry_day11.json`
- `data/shadow_evidence/daily_scanner_day6.json`
- `data/shadow_evidence/c3_delta_day6.json`
- `data/shadow_evidence/telemetry_summary_5day.json`
- `docs/phase_brief/phase51-factor-algebra-design.md`

### Do Not Touch Unless a Validator Fails First
- `docs/handover/sovereign_promotion_package_20260313.md`
- `docs/handover/phase48_shadow_evidence_review_20260311.md`
- Day 1-Day 11 canonical artifacts and Day 1-Day 11 CEO memos
- Any file under a future Phase 51 implementation surface outside the design draft

---

## Execution Order

### Step 1 - Reconfirm Day 11 Baseline
Before any Day 12 extension, validate that the corrected Day 11 bounded surface is still intact.

Targeted suite:
```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
```

Context validator:
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```

If the Day 11 baseline is drifting, stop and publish `BLOCK` before touching the Day 12 runtime surface.

### Step 2 - Harper: Publish the Day 12 CEO Memo + Carry Forward the Phase 51 Design Draft
Create:
- `docs/handover/phase50_day12_ceo_memo_20260323.md`

Update only if needed:
- `docs/phase_brief/phase51-factor-algebra-design.md`

Template rules for the Day 12 memo:
- mirror the corrected Day 11 memo structure
- keep the decision scope as `Continue / Edit / Hold` inside Phase 50 only
- include updated `active_days_observed / 150`
- include updated cumulative equity through Day 12
- include an updated C3 delta table sourced from the latest governed delta artifact actually used
- state scanner provenance explicitly if the generator reuses the latest accepted governed scanner file
- keep the reply contract restricted to the current phase
- preserve the no-new-phase language from `D-256`
- do not claim a screenshot unless the file is actually attached on disk and visibly usable
- treat the Phase 51 design draft as unchanged unless explicit CEO clarification is provided

### Step 3 - Benjamin: Execute the Day 12 Paper-Curve Run
If the current generator is not yet Day 12-clean, extend it only inside the authorized Day 12 runtime surface.

Required Day 12 artifact contract:

Canonical outputs:
- `data/processed/phase50_shadow_ship/paper_curve_day12.csv`
- `data/processed/phase50_shadow_ship/telemetry_day12.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`

Allowed supporting output if needed:
- `data/processed/phase50_shadow_ship/paper_curve_positions_day12.csv`

Compatibility mirrors:
- `data/shadow_evidence/paper_curve_day12.csv`
- `data/shadow_evidence/telemetry_day12.json`
- `data/processed/phase50_gate/gate_recommendation.json`

Telemetry/event log:
- append or upsert Day 12 entry in `data/telemetry/phase50_paper_curve_events.jsonl`

Runtime rules:
- preserve Day 1-Day 11 artifacts; do not overwrite them with Day 12 filenames
- keep `core.engine.run_simulation` as the PnL source of truth
- keep `status=SIMULATED`, `broker_calls_detected=0`, and explicit demo provenance
- update `active_days_observed` to the truthful Day 12 count
- keep canonical and compatibility Day 12 mirrors content-equivalent
- if no governed `daily_scanner_day12.json` exists, rely on the approved generator fallback to the latest accepted governed scanner artifact
- if no governed `c3_delta_day12.json` exists, use `data/shadow_evidence/c3_delta_day6.json` as the latest accepted governed delta artifact

Preferred command if a governed Day 12 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 12 --c3-delta data/shadow_evidence/c3_delta_day12.json
```

Fallback command if no governed Day 12 delta file exists:
```powershell
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 12 --c3-delta data/shadow_evidence/c3_delta_day6.json
```

If the fallback is used, the Day 12 memo and reply must state that the C3 delta table uses the latest accepted governed artifact rather than a fabricated Day 12 file. If the generator reuses the Day 6 scanner file, the memo and reply must state that scanner provenance explicitly.

### Step 4 - Lucas: Refresh the Dashboard Telemetry Surface
If the dashboard is still drifting, update it only inside:
- `views/elite_sovereign_view.py`
- `tests/test_elite_sovereign_view.py`
- `scripts/capture_dashboard_screenshot.py`

Required behavior:
- load the latest available Phase 50 runway day
- preserve the canonical runtime directory as the dashboard source of truth
- show Day 12 daily PnL, turnover, crisis-turnover, and active-days state
- keep the zero-broker-call and demo-provenance banners explicit
- capture a real screenshot at `docs/images/phase50_day12_dashboard_20260323.png`

### Step 5 - Prepare the Acceptance Proof Reply
Reply format is locked by governance.

The final reply for the Day 12 round must contain only:
- Day 12 memo path
- acceptance proof summary with:
  - one screenshot
  - one telemetry excerpt with `2026-03-23` realized date
  - one updated C3 delta table
- Phase 51 design draft path or explicit confirmation that the locked draft remains unchanged

No extra narrative, no phase-opening language, and no production implication is allowed in the reply.

---

## Acceptance Checks for This Round

- `CHK-P50-D12-01`: `docs/phase_brief/phase50-day12-worker-execution-guide.md` exists and keeps the runtime scope inside Phase 50 only.
- `CHK-P50-D12-02`: Day 12 owned file surface is explicit for docs, scripts, dashboard, tests, canonical outputs, compatibility mirrors, screenshot, event log, and the Phase 51 docs-only draft or confirmation.
- `CHK-P50-D12-03`: The guide preserves all hard quarantines, explicitly forbids worker-opened new phases, and keeps Phase 51 work docs-only.
- `CHK-P50-D12-04`: The Day 12 artifact contract is explicit for canonical outputs, compatibility mirrors, latest-day dashboard behavior, screenshot requirement, reply format, governed scanner fallback, and governed C3 delta sourcing.
- `CHK-P50-D12-05`: `docs/phase_brief/phase50-brief.md` points to this guide as the active next-step handoff and notes the locked Phase 51 docs-only draft.
- `CHK-P50-D12-06`: `docs/decision log.md` records the CEO Day 12 continuation disposition plus the Phase 51 unchanged-draft carry-forward without opening a new phase and without colliding with existing IDs.
- `CHK-P50-D12-07`: `docs/lessonss.md` records the Day 12 subagent-review availability guardrail.
- `CHK-P50-D12-08`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the updated Phase 50 brief.
- `CHK-P50-D12-09`: Day 12 runtime artifacts, memo, screenshot, and SAW closeout are published with explicit reviewer-availability status.
- `CHK-P50-D12-10`: `docs/phase_brief/phase51-factor-algebra-design.md` remains interface-only and explicitly states that Phase 51 Factor Algebra remains unopened.

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase50-brief.md` so:
- Day 11 approval is reflected as complete
- Day 12 is the active next-step continuation surface
- Phase 51 remains unchanged and docs-only

### Historical Readiness Guide
Update `docs/phase_brief/phase50-shadow-ship-readiness.md` so the historical note points at the Day 12 guide as the active handoff while preserving the original Day 1 activation record.

### Decision Log
Append the Day 12 continuation disposition as a new decision-log entry using the next free identifier on disk. `D-269` is free at the start of this round and must be used for the Day 12 continuation lock.

### Lessons
Append one lesson entry capturing the subagent-review availability guardrail for runtime closeout.

### Context
Refresh:
```powershell
.venv\Scripts\python scripts\build_context_packet.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

---

## Validation Commands

```powershell
.venv\Scripts\python -m pytest tests\test_phase50_paper_curve.py tests\test_elite_sovereign_view.py -q
.venv\Scripts\python -m py_compile dashboard.py views\elite_sovereign_view.py scripts\capture_dashboard_screenshot.py scripts\run_phase50_paper_curve.py
.venv\Scripts\python scripts\run_phase50_paper_curve.py --curve-day 12 --c3-delta data/shadow_evidence/c3_delta_day6.json
.venv\Scripts\python scripts\build_context_packet.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

Optional screenshot capture sequence:
```powershell
Start-Process -FilePath .venv\Scripts\python -ArgumentList '-m','streamlit','run','dashboard.py','--server.headless','true','--server.port','8501' -PassThru
.venv\Scripts\python scripts\capture_dashboard_screenshot.py docs/images/phase50_day12_dashboard_20260323.png
```

---

## Deliverables

- `docs/phase_brief/phase50-day12-worker-execution-guide.md`
- `data/processed/phase50_shadow_ship/paper_curve_day12.csv`
- `data/processed/phase50_shadow_ship/paper_curve_positions_day12.csv`
- `data/processed/phase50_shadow_ship/telemetry_day12.json`
- `data/processed/phase50_shadow_ship/gate_recommendation.json`
- `data/shadow_evidence/paper_curve_day12.csv`
- `data/shadow_evidence/telemetry_day12.json`
- `data/processed/phase50_gate/gate_recommendation.json`
- `docs/images/phase50_day12_dashboard_20260323.png`
- `docs/handover/phase50_day12_ceo_memo_20260323.md`
- `docs/saw_reports/saw_phase50_day12_runtime_closeout_20260323.md`

Progress: 100/100
Confidence: 8/10
Critical Mission: Extend the bounded Day 12 paper-only runway with truthful fallback provenance, zero broker calls, a usable dashboard proof image, and no expansion beyond the already authorized Phase 50 surface.
