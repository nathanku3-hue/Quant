# Phase 38 Governance Review Worker Guide

**Round ID**: `P38-GR-01`
**Date**: `2026-03-09`
**Scope**: Docs-only governance closeout for the frozen Phase 38 gate packet plus dormant Phase 39 planning handoff
**Status**: ACTIVE (locked `Continue` closeout; no execution work authorized)

---

## 1. Mission Statement

**Governance closeout only. No execution changes.**

This round no longer opens a fresh `Continue / Edit / Hold` analysis surface. The CEO/PM disposition is now locked to `Continue`, and the worker's job is to convert that locked decision into clean governance artifacts.

**Locked governance conclusions**:
- Phase 38 bounded gate execution is accepted as mathematically clean, frozen, and decision-grade
- The all-`Pause` outcome is valid evidence, not a computational defect
- The detected sequence violation is classified as a **docs/process sequencing breach only**
- That breach is memorialized in governance artifacts and does **not** invalidate the packet
- The next phase is a **narrow dormant Phase 39 planning brief** focused only on threshold-window reachability policy and window-geometry design

**Frozen truth to preserve**:
- Gate decision: `Pause`
- Method votes: `0 Continue / 3 Pause / 0 Pivot`
- Gated methods: `equal_weight`, `inverse_vol_63d`, `capped_risk_budget`
- Locked thresholds: `MIN_ACTIVE_DAYS_THRESHOLD=252`, `MIN_COVERAGE_RATIO_THRESHOLD=0.80`
- Validation window length: `187` trading days
- Holdout window length: `191` trading days
- Phase 37 packet: frozen and unchanged
- Research-only quarantine: still active

**Out of scope**:
- No code changes in `strategies/`, `scripts/`, `tests/`, `core/`, `data/`, `views/`
- No artifact regeneration with changed parameters
- No gate reruns or threshold rewrites
- No Phase 37 packet mutation
- No production promotion or deployment language
- No new sleeves, methods, or signal discovery
- No runtime-key migration or cost-model rewrites
- No portfolio rewrite or re-optimization work

---

## 2. Inputs (Read-Only Source of Truth)

**Frozen Phase 38 gate execution packet**:
1. `docs/phase_brief/phase38-brief.md`
2. `docs/context/current_context.md`
3. `data/processed/phase38_gate/gate_recommendation.json`
4. `data/processed/phase38_gate/gate_diagnostics_delta.csv`
5. `docs/saw_reports/saw_phase38_gate_execution_20260309.md`
6. `docs/notes.md`
7. `docs/decision log.md`

**Governance-control docs**:
- `docs/handover/phase38_execution_gate_ceo_memo.md`
- `docs/handover/phase38_governance_review.md`
- `docs/phase_brief/phase38-worker-execution-guide.md`
- `docs/context/current_context.json`

**Inherited Phase 37 frozen packet**:
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/handover/phase37_governance_review.md`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`

All execution artifacts above are treated as read-only.

---

## 3. Allowed Writes

**Docs-only governance outputs**:
1. `docs/phase_brief/phase38-governance-review-worker-guide.md`
2. `docs/handover/phase38_governance_review.md`
3. `docs/saw_reports/saw_phase38_governance_review_20260309.md`
4. `docs/phase_brief/phase38-brief.md`
5. `docs/context/current_context.json`
6. `docs/context/current_context.md`
7. `docs/decision log.md`
8. `docs/lessonss.md`
9. `docs/phase_brief/phase39-brief.md`

**Strictly forbidden**:
- Any edits to `strategies/`, `scripts/`, `tests/`, `data/`, `core/`, `views/`
- Any changes to generated CSV, JSON, or parquet execution artifacts
- Any language implying production authorization
- Any reopening of Phase 37/38 execution scope
- Any gate reruns or threshold changes
- Any broad Phase 39 implementation or execution scaffolding

---

## 4. Read-Only Commands

Run these commands from repo root with `.venv` only.

### CMD-1: Gate Recommendation Review
```powershell
Get-Content data\processed\phase38_gate\gate_recommendation.json
```
**Expected**: JSON showing portfolio `Pause`, `0 Continue / 3 Pause / 0 Pivot`, and locked thresholds `252 / 0.80`

### CMD-2: Gate Diagnostics Delta Review
```powershell
Get-Content data\processed\phase38_gate\gate_diagnostics_delta.csv
```
**Expected**: CSV showing `Continue->Pause` for all three methods and reachability failure in both governed windows

### CMD-3: Phase 38 Gate Execution SAW Validator
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase38_gate_execution_20260309.md
```
**Expected**: PASS

### CMD-4: Phase 38 Gate Execution Closure Packet Validator
```powershell
$packet = (Select-String -Path 'docs\saw_reports\saw_phase38_gate_execution_20260309.md' -Pattern '^ClosurePacket:').Line
.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "$packet" --require-open-risks-when-block --require-next-action-when-block
```
**Expected**: PASS

### CMD-5: Phase 37 Frozen Packet Integrity Check
```powershell
.venv\Scripts\python scripts\validate_phase37_portfolio_outputs.py --output-dir data\processed\phase37_portfolio
```
**Expected**: PASS

### CMD-6: Refresh Context Packet From Brief State
```powershell
.venv\Scripts\python scripts\build_context_packet.py
```
**Expected**: PASS

### CMD-7: Validate Refreshed Context Packet
```powershell
.venv\Scripts\python scripts\build_context_packet.py --validate
```
**Expected**: PASS

### CMD-8: Governance-Review SAW Validator
```powershell
.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_phase38_governance_review_20260309.md
```
**Expected**: PASS

### CMD-9: Governance-Review Closure Packet Validator
```powershell
$packet = (Select-String -Path 'docs\saw_reports\saw_phase38_governance_review_20260309.md' -Pattern '^ClosurePacket:').Line
.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "$packet" --require-open-risks-when-block --require-next-action-when-block
```
**Expected**: PASS

---

## 5. Acceptance Checks

- `CHK-P38GR-01`: Frozen Phase 38 gate inputs match the bounded execution packet
- `CHK-P38GR-02`: Gate recommendation JSON shows `Pause` with `0 Continue / 3 Pause / 0 Pivot`
- `CHK-P38GR-03`: Gate diagnostics delta CSV shows all three methods transitioning from `Continue` to `Pause`
- `CHK-P38GR-04`: Locked thresholds remain `252` active days and `0.80` coverage ratio
- `CHK-P38GR-05`: The all-`Pause` outcome is documented as structural window-geometry evidence, not a method-quality defect
- `CHK-P38GR-06`: The sequence violation is documented as a **process-ordering miss only** and explicitly marked non-fatal to packet integrity
- `CHK-P38GR-07`: Phase 37 frozen packet remains unchanged and validator-clean
- `CHK-P38GR-08`: Phase 38 execution SAW report validates cleanly
- `CHK-P38GR-09`: Governance memo records locked `Continue` disposition and CEO rationale verbatim
- `CHK-P38GR-10`: Governance SAW report is semantically aligned and validator-clean
- `CHK-P38GR-11`: Brief/context/log/lessons refresh cleanly to post-closeout state
- `CHK-P38GR-12`: Phase 39 brief is opened in **dormant planning mode** and is scoped only to threshold-window reachability policy
- `CHK-P38GR-13`: Research-only quarantine remains explicit in every governance artifact
- `CHK-P38GR-14`: No code, test, or execution-artifact changes are introduced in this round

---

## 6. Locked CEO Resolutions

These items are no longer open for worker interpretation.

### 6.1 Sequence Violation Classification
- **Locked resolution**: Method A - docs/process sequencing breach only
- **Confidence**: `98/100`
- **Worker implication**: memorialize the ordering miss in the governance memo and SAW, but do not treat it as a computational or data-integrity failure

### 6.2 Next Phase Target
- **Locked resolution**: Method A - narrow Phase 39 planning brief focused solely on threshold-window reachability policy and window-geometry design
- **Confidence**: `96/100`
- **Worker implication**: do not open any broader portfolio, signal, or execution-planning scope

### 6.3 Closeout Formality
- **Locked resolution**: Method A - full disposition memo + governance SAW + context/log/lessons refresh
- **Confidence**: `97/100`
- **Worker implication**: do not stop at memo-only closeout

No delegation is required in this round.

---

## 7. Locked Governance Disposition

### Disposition
- **Locked disposition**: `Continue`

### Locked Rationale
- The all-`Pause` outcome is accepted as valid, decision-grade evidence because the `252`-day active-days floor exceeds the governed validation/holdout window lengths (`187` / `191` days).
- This is a **structural geometry constraint**, not a method or computational flaw.
- The detected sequence violation is memorialized as a **process-ordering miss** that has been remediated by retroactive review artifacts.
- The sequencing miss does **not** compromise packet integrity or invalidate any frozen math.
- Phase 36 sleeves, `10` bps cost model, and `permno` key remain immutable.

### Worker Rule
- Do **not** reopen the `Continue / Edit / Hold` surface in this round.
- Populate the memo and downstream artifacts using `Continue` only.

---

## 8. Required Deliverables

### Deliverable 1: Governance Memo (Populate Locked Disposition)
**File**: `docs/handover/phase38_governance_review.md`

Required content:
- Frozen gate packet truth summary
- Phase 37 frozen packet integrity confirmation
- Validation evidence
- **Locked `Continue` disposition**
- **Locked CEO rationale** from Section 7
- Explicit note that the sequence violation is process-only and non-fatal
- Explicit research-only quarantine

### Deliverable 2: Governance SAW Report
**File**: `docs/saw_reports/saw_phase38_governance_review_20260309.md`

Required content:
- `SAW Verdict`, `Hierarchy Confirmation`, `Open Risks`, `Next action`
- Findings table and ownership check
- Command evidence for validator/context checks
- Explicit note that the sequence violation is process-only and remediated
- `ClosurePacket`, `ClosureValidation`, `SAWBlockValidation`

### Deliverable 3: Brief and Context Refresh
**Files**:
- `docs/phase_brief/phase38-brief.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`

Required content:
- Phase 38 governance review formally closed with `Continue`
- No execution work pending
- Same repaired comparator, same windows, same `10` bps cost model
- Same locked thresholds (`252`, `0.80`)
- Next step routed to dormant Phase 39 planning only

### Deliverable 4: Decision Log and Lessons Entry
**Files**:
- `docs/decision log.md`
- `docs/lessonss.md`

Required content:
- Decision log: governance closeout disposition plus process-ordering memorialization
- Lessons: threshold-window geometry and review-sequencing guardrail

### Deliverable 5: Dormant Phase 39 Planning Brief
**File**: `docs/phase_brief/phase39-brief.md`

Required content:
- Docs-only dormant planning state
- Scope limited to threshold-window reachability policy and window-geometry design
- Explicit exclusion of threshold rewrite, rerun, portfolio rewrite, and production work
- Approval boundary for any later execution

---

## 9. Stop Conditions

Immediate block and escalate if any of the following occurs:
- Any validator command fails
- Phase 37 frozen packet shows mutation or drift
- Gate thresholds (`252`, `0.80`) are changed
- Any discrepancy requires code changes or output regeneration
- Any artifact introduces production or deployment language
- Any attempt is made to rerun the gate, reopen Phase 37, or change sleeve/method/identifier/cost-model assumptions
- Any proposed Phase 39 work expands beyond narrow reachability-policy planning

If blocked, do **not** patch execution code in this round. Publish the blocker in `Open Risks` and stop.

---

## 10. Forbidden Actions

The following actions are explicitly out of boundary for this governance review closeout round:

- **No gate rerun**: The bounded Phase 38 gate execution is complete and frozen
- **No Phase 37 mutation**: The Phase 37 portfolio packet remains read-only
- **No threshold rewrite**: The locked values (`252`, `0.80`) are governance-frozen
- **No sleeve-set change**: The Phase 37 active sleeves remain unchanged
- **No cost-model rewrite**: The governed `10` bps model remains locked
- **No production rollout**: Research-only quarantine remains in force
- **No permno migration**: Runtime key remains `permno` until a separate governance decision
- **No vendor execution**: S&P IQ / BvD procurement remains asynchronous and out of scope
- **No new signal discovery**: Phase 39 is not a research expansion round
- **No portfolio rewrite**: reachability policy planning is the only next-phase target
- **No code scaffolding**: no implementation work is authorized in this closeout

---

## 11. Execution Checklist

- [ ] Confirm frozen inputs match the real Phase 38 gate packet
- [ ] Run CMD-1 through CMD-7 on the frozen packet and context refresh path
- [ ] Confirm Phase 37 frozen packet remains unchanged via CMD-5
- [ ] Populate `docs/handover/phase38_governance_review.md` with locked `Continue` disposition and rationale
- [ ] Publish `docs/saw_reports/saw_phase38_governance_review_20260309.md` with validator-clean closure lines
- [ ] Run CMD-8 and CMD-9 after publishing the governance SAW
- [ ] Refresh `docs/phase_brief/phase38-brief.md`, `docs/context/current_context.json`, `docs/context/current_context.md`, `docs/decision log.md`, and `docs/lessonss.md`
- [ ] Open `docs/phase_brief/phase39-brief.md` in dormant planning mode with narrow reachability-policy scope only
- [ ] Confirm all 14 acceptance checks pass
- [ ] Confirm no code or execution artifacts changed
- [ ] Hold for explicit next governance instruction before any new execution work begins

---

**End of Phase 38 Governance Review Worker Guide**
