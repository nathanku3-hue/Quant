# Phase 37 Governance Review Worker Guide

**Round ID**: `P37-GR-01`  
**Date**: `2026-03-09`  
**Scope**: Read-only audit of the frozen Phase 37 portfolio packet plus docs-only governance closeout  
**Status**: ACTIVE

---

## 1. Mission Statement

**Governance review only. No execution changes.**

This round audits the frozen Phase 37 portfolio-construction packet, confirms validator-clean consistency on the repaired `permno` path, and publishes the CEO/PM disposition surface: `Continue / Edit / Hold`.

**Frozen truth to confirm**:
- Portfolio decision: `Continue`
- Method votes: `3 Continue / 0 Pause / 0 Pivot`
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`
- Comparator: `data/processed/features_phase35_repaired.parquet`
- Cost model: locked `10` bps
- Research-only quarantine: still active

**Out of scope**:
- No code changes in `strategies/`, `scripts/`, `tests/`, `core/`, `data/`
- No artifact regeneration with changed parameters
- No production promotion or deployment language
- No new sleeves, methods, or signal discovery
- No runtime-key migration or cost-model rewrites

---

## 2. Inputs (Read-Only Source of Truth)

**Frozen Phase 37 execution packet**:
1. `docs/phase37_portfolio_exec_summary.md`
2. `docs/phase37_portfolio_construction_report.md`
3. `docs/saw_reports/saw_phase37_portfolio_execution_20260309.md`
4. `data/processed/phase37_portfolio/portfolio_input_manifest.json`
5. `data/processed/phase37_portfolio/portfolio_sleeve_inputs.parquet`
6. `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
7. `data/processed/phase37_portfolio/portfolio_regime_diagnostics.csv`
8. `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
9. `data/processed/phase37_portfolio/portfolio_method_comparison.json`
10. `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
11. `data/processed/phase37_portfolio/portfolio_recommendation.json`

**Governance-control docs**:
- `docs/phase_brief/phase37-brief.md`
- `docs/handover/phase37_governance_review.md`
- `docs/saw_reports/saw_phase37_governance_review_20260309.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`

All execution artifacts above are treated as read-only.

---

## 3. Allowed Writes

**Docs-only governance outputs**:
1. `docs/phase_brief/phase37-governance-review-worker-guide.md`
2. `docs/handover/phase37_governance_review.md`
3. `docs/saw_reports/saw_phase37_governance_review_20260309.md`
4. `docs/phase_brief/phase37-brief.md`
5. `docs/context/current_context.json`
6. `docs/context/current_context.md`
7. `docs/lessonss.md`

**Strictly forbidden**:
- Any edits to `strategies/`, `scripts/`, `tests/`, `data/`, `core/`, `views/`
- Any changes to generated CSV, JSON, or parquet execution artifacts
- Any language implying production authorization
- Any reopening of Phase 36/37 execution scope

---

## 4. Governance Questions

Answer these five questions using the frozen packet only.

### Q1: Does the portfolio decision remain `Continue`?
- Does the repaired packet still support the research-only `Continue` recommendation?
- Are the three active sleeves unchanged?
- Is the paused-sleeve boundary still respected?
- **Answer**: `Continue / Edit / Hold`

### Q2: Do the method votes remain `3 Continue / 0 Pause / 0 Pivot`?
- `equal_weight`: `Continue / Pause / Pivot`
- `inverse_vol_63d`: `Continue / Pause / Pivot`
- `capped_risk_budget`: `Continue / Pause / Pivot`
- **Tally**: `X Continue / Y Pause / Z Pivot`

### Q3: Does the frozen packet remain validator-clean without code changes?
- Does the portfolio output validator pass?
- Does the targeted Phase 37 pytest pack pass?
- Do the execution SAW report and closure packet validate cleanly?
- **Answer**: `Pass / Fail` (failure blocks closeout)

### Q4: Is any remaining drift docs-only rather than computational?
- Are all discrepancies limited to wording, references, or governance framing?
- Do any issues require code/data reruns? If yes, block.
- **Answer**: `None / Docs-only / Escalate`

### Q5: How should warmup and active-days semantics be carried forward?
- Keep `warmup != failure` interpretation in the current packet?
- Carry active-days coverage as a future planning constraint instead of changing this round?
- **Answer**: `Keep current interpretation / Edit future policy / Hold`

---

## 5. Exact Commands

Run these commands from repo root with `.venv` only.

### CMD-1: Portfolio Output Validator
```powershell
.venv\Scripts\python scripts\validate_phase37_portfolio_outputs.py --output-dir data\processed\phase37_portfolio
```
**Expected**: PASS

### CMD-2: Targeted Phase 37 Tests
```powershell
.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase37_risk_diagnostics.py tests\test_phase37_portfolio_construction_runner.py tests\test_validate_phase37_portfolio_outputs.py -q
```
**Expected**: PASS (`25/25` or current equivalent if unchanged)

### CMD-3: Execution SAW Validator
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase37_portfolio_execution_20260309.md
```
**Expected**: PASS

### CMD-4: Execution Closure Packet Validator
```powershell
$packet = (Select-String -Path 'docs\saw_reports\saw_phase37_portfolio_execution_20260309.md' -Pattern '^ClosurePacket:').Line
.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "$packet" --require-open-risks-when-block --require-next-action-when-block
```
**Expected**: PASS

### CMD-5: Refresh Context Packet From Brief State
```powershell
.venv\Scripts\python scripts\build_context_packet.py
```
**Expected**: PASS

### CMD-6: Validate Refreshed Context Packet
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```
**Expected**: PASS

### CMD-7: Governance-Review SAW Validator
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase37_governance_review_20260309.md
```
**Expected**: PASS

### CMD-8: Governance-Review Closure Packet Validator
```powershell
$packet = (Select-String -Path 'docs\saw_reports\saw_phase37_governance_review_20260309.md' -Pattern '^ClosurePacket:').Line
.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "$packet" --require-open-risks-when-block --require-next-action-when-block
```
**Expected**: PASS

---

## 6. Acceptance Checks

- `CHK-P37-GR-01`: Frozen packet inputs match the real Phase 37 portfolio stack
- `CHK-P37-GR-02`: Portfolio output validator passes with no code changes
- `CHK-P37-GR-03`: Targeted Phase 37 pytest pack passes with no code changes
- `CHK-P37-GR-04`: Execution SAW report validates cleanly
- `CHK-P37-GR-05`: Execution closure packet validates cleanly
- `CHK-P37-GR-06`: Governance memo matches repaired packet truth
- `CHK-P37-GR-07`: Governance SAW report is semantically aligned and validator-clean
- `CHK-P37-GR-08`: Phase 37 brief state is refreshed to governance-disposition-ready status
- `CHK-P37-GR-09`: Context packet refreshes cleanly from the brief and validates
- `CHK-P37-GR-10`: Research-only quarantine remains explicit in every governance artifact
- `CHK-P37-GR-11`: No code, test, or execution-artifact changes were introduced
- `CHK-P37-GR-12`: CEO/PM disposition surface remains `Continue / Edit / Hold` only

---

## 7. Required Deliverables

### Deliverable 1: Governance Memo
**File**: `docs/handover/phase37_governance_review.md`

Required content:
- Frozen packet truth summary
- Validation evidence
- Continue / Edit / Hold decision surface
- Explicit research-only quarantine
- Warmup / active-days interpretation note

### Deliverable 2: Governance SAW Report
**File**: `docs/saw_reports/saw_phase37_governance_review_20260309.md`

Required content:
- `SAW Verdict`, `Hierarchy Confirmation`, `Open Risks`, `Next action`
- Findings table and ownership check
- Command evidence for validator/test/context checks
- `ClosurePacket`, `ClosureValidation`, `SAWBlockValidation`

### Deliverable 3: Brief and Context Refresh
**Files**:
- `docs/phase_brief/phase37-brief.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`

Required content:
- Governance packet ready for CEO/PM disposition
- No execution work pending until disposition is recorded
- Same repaired comparator, same windows, same 10 bps cost model

### Deliverable 4: Lessons Entry
**File**: `docs/lessonss.md`

Required content:
- Governance-doc drift root cause
- Context-source dependency on the brief
- Guardrail for future governance-close rounds

---

## 8. Decision Surface

### Option A: `Continue`
- Frozen packet remains validator-clean
- Governance artifacts align to repaired truth
- Research-only quarantine stays active
- **Next step**: CEO/PM records `Continue` and opens the next planning artifact under the same governed contracts

### Option B: `Edit`
- Frozen packet is computationally clean
- Docs-only wording or routing fixes are still needed
- No code/data reruns required
- **Next step**: perform docs-only reconciliation and revalidate governance closeout

### Option C: `Hold`
- Validator failure or non-docs defect is found
- Any required code/data change falls outside governance review
- **Next step**: keep Phase 37 frozen and escalate for a separate engineering or governance decision

---

## 9. Stop Conditions

Immediate block and escalate if any of the following occurs:
- Any validator or targeted test command fails
- Any discrepancy requires code changes or output regeneration
- Any artifact introduces production or deployment language
- Any attempt is made to reopen sleeves, methods, identifiers, or cost-model assumptions

If blocked, do **not** patch execution code in this round. Publish the blocker in `Open Risks` and stop.

---

## 10. Execution Checklist

- [ ] Confirm frozen inputs match the real Phase 37 portfolio packet
- [ ] Run CMD-1 through CMD-6 on the frozen packet and context refresh path
- [ ] Reconcile docs-only drift in the governance worker guide, memo, SAW, and brief/context state
- [ ] Publish governance memo with `Continue / Edit / Hold` surface only
- [ ] Publish governance SAW report with validator-clean closure lines
- [ ] Run CMD-7 and CMD-8 after publishing the governance SAW
- [ ] Confirm all 12 acceptance checks pass
- [ ] Confirm no code or execution artifacts changed
- [ ] Hold for explicit CEO/PM disposition

---

**End of Phase 37 Governance Review Worker Guide**
