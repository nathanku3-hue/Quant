# Phase 38: Worker Execution Guide — Active-Days / Coverage Gate (EXECUTION AUTHORIZED)

**Status**: EXECUTION AUTHORIZED (bounded gate run only; no scope expansion authorized)
**Created**: 2026-03-09
**Activation Token**: `approve phase38 execution`
**Round**: Bounded execution run under locked dual-gate contract

---

## 1. Scope and Execution-Authorized Boundary

The explicit in-thread token `approve phase38 execution` has been issued. Execution is authorized ONLY for the bounded gate run defined in this guide.

**What This Guide Does**
- Executes the bounded active-days / coverage gate on the frozen Phase 37 portfolio packet
- Externalizes threshold ownership to CEO memo
- Binds dual-gate rule universally across all methods
- Limits evidence to narrow delta outputs only

**What This Guide Does NOT Do**
- Authorize any Phase 38 code scaffolding
- Authorize any Phase 38 test generation
- Authorize any rerun or mutation of Phase 37 outputs
- Authorize any production-facing work

**Activation Boundary**
- Explicit token `approve phase38 execution` is issued and satisfied for this bounded run
- Authorization is limited to the bounded gate run in this guide only
- Governance disposition options: Continue / Edit / Hold

---

## 2. Frozen Evidence Inputs

Phase 38 inherits the frozen Phase 37 portfolio packet as read-only truth.

**Frozen Phase 37 Packet Truth**
- Portfolio decision: `Continue`
- Method votes: `3 Continue / 0 Pause / 0 Pivot`
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`

**Frozen Source-of-Truth Documents**
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/handover/phase37_governance_review.md`
- `docs/saw_reports/saw_phase37_portfolio_execution_20260309.md`
- `docs/saw_reports/saw_phase37_governance_review_20260309.md`

**Frozen Source-of-Truth Artifacts**
- `data/processed/phase37_portfolio/portfolio_recommendation.json`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.json`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- `data/processed/phase37_portfolio/portfolio_input_manifest.json`

**Locked Comparator Contract**
- Governed comparator artifact: `data/processed/features_phase35_repaired.parquet`
- Governed evaluation windows:
  - Calibration: `2022-01-01` → `2023-06-30`
  - Validation: `2023-07-01` → `2024-03-31`
  - Holdout: `2024-04-01` → `2024-12-31`
- Non-negotiable constraints:
  - Same repaired `permno` path only
  - Same governed windows only
  - Same `10` bps governed cost model only
  - Same simulation path family only (`core.engine.run_simulation`)
  - Same research-only quarantine until a later governance decision explicitly changes state

---

## 3. Universal Dual-Gate Rule

The active-days / coverage gate applies to ALL portfolio methods with NO exceptions.

**Gate Metrics**
- `active_days`: Count of governed days where a method is in a valid investable state (`ready`) rather than `warmup` or `blocked`
- `eligible_days`: Count of governed days inside the target evaluation window for the method under review
- `coverage_ratio`: `active_days / eligible_days`

**Gate Thresholds (CEO-Owned, Governance-Locked)**
- `MIN_ACTIVE_DAYS_THRESHOLD = 252` (loaded from `docs/handover/phase38_execution_gate_ceo_memo.md`)
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80` (loaded from `docs/handover/phase38_execution_gate_ceo_memo.md`)

**Gate Binding Contract**
- One common threshold pair applies to BOTH validation and holdout windows
- Gate checks MUST be applied per validation window AND per holdout window independently
- Both thresholds must be satisfied in BOTH windows for a method to pass
- Gate misses map to `Pause` disposition, NOT `Blocked`
- Execution is authorized for this bounded run only; all out-of-scope work remains blocked

**EXPLICIT: Workers Do NOT Derive Threshold Values**
- Workers load threshold values from `docs/handover/phase38_execution_gate_ceo_memo.md`
- Workers do NOT compute, estimate, or infer thresholds from diagnostics
- Workers do NOT set policy-level constants
- Rationale: Prevents worker-side policy setting; maintains CEO ownership of governance boundaries

---

## 4. CEO-Owned Threshold Constants

Threshold values are declared in `docs/handover/phase38_execution_gate_ceo_memo.md` and owned by the CEO/PM.

**Worker Responsibilities**
- Load threshold values from the CEO memo at execution time
- Apply thresholds as written without modification
- Do NOT compute thresholds from Phase 37 diagnostics
- Do NOT estimate thresholds from historical coverage patterns
- Do NOT propose threshold values in worker outputs

**CEO/PM Responsibilities**
- Review Phase 37 guardrail diagnostics
- Keep `MIN_ACTIVE_DAYS_THRESHOLD` and `MIN_COVERAGE_RATIO_THRESHOLD` as the locked policy constants (`252`, `0.80`) unless superseded by a new governance round
- Maintain rationale in the execution gate memo
- Authorize Phase 38 execution only via explicit in-thread token `approve phase38 execution`

**Rationale**
- Prevents worker-side policy setting
- Maintains governance discipline
- Ensures threshold decisions are explicit and auditable

---

## 5. Allowed Evidence Outputs (Execution-Authorized Bounded Run)

Phase 38 execution is authorized for this bounded round and must remain bound to the frozen Phase 37 packet, emitting only narrow delta outputs.

**Allowed Execution Steps**
1. Load frozen Phase 37 portfolio packet without recomputation
2. Load threshold constants from `docs/handover/phase38_execution_gate_ceo_memo.md`
3. Apply dual gate (active-days and coverage-ratio) per validation AND per holdout
4. Emit gate-specific diagnostics delta report
5. Emit updated recommendation JSON with gate disposition
6. Publish SAW closeout report

**Allowed Evidence Artifacts**
- `data/processed/phase38_gate/gate_diagnostics_delta.csv` (gate-specific metrics only)
- `data/processed/phase38_gate/gate_recommendation.json` (updated disposition with gate results)
- `docs/saw_reports/saw_phase38_gate_execution_YYYYMMDD.md` (SAW closeout)

**Forbidden Actions**
- Do NOT recompute Phase 37 portfolio math
- Do NOT regenerate Phase 37 artifacts
- Do NOT mutate frozen Phase 37 outputs
- Do NOT create new portfolio methods or sleeves
- Do NOT change the Phase 37 method votes or dispositions retroactively

---

## 6. Forbidden Actions

The following actions are explicitly forbidden in Phase 38:

**Worker-Side Policy Setting**
- No worker-side threshold estimation
- No threshold inference from diagnostics
- No threshold proposals in worker outputs

**Out-of-Bounds Execution**
- No Phase 38 code scaffolding in this round; execution is limited to the existing bounded gate-run contract
- No Phase 38 test generation in this round; use the locked execution path only
- No Phase 38 artifact generation outside the allowed deliverables in Section 5

**Phase 37 Mutation**
- No rerun of Phase 37 portfolio construction
- No mutation of frozen Phase 37 outputs
- No retroactive changes to Phase 37 method votes

**Out-of-Scope Work**
- No production promotion or deployment
- No vendor-enrichment execution (S&P IQ / BvD remains asynchronous)
- No runtime key migration away from `permno`
- No governed cost-model rewrites
- No new sleeve discovery or new portfolio methods
- No unpausing of `bundle_quality_composite`

---

## 7. Acceptance Checks for Authorized Execution Round

For the authorized bounded Phase 38 execution run, the following acceptance checks must pass:

**Threshold Loading**
- Thresholds loaded from `docs/handover/phase38_execution_gate_ceo_memo.md` - PASS when values are read from memo, not computed
- No worker-side threshold estimation - PASS when no threshold inference logic exists

**Gate Application**
- Gate applied to ALL methods with no exceptions - PASS when all 3 active methods are evaluated
- Gate applied per validation AND per holdout independently - PASS when both windows are checked separately
- Gate misses map to `Pause` disposition only - PASS when no method is auto-failed

**Evidence Discipline**
- Evidence limited to delta report + recommendation + SAW - PASS when no Phase 37 artifacts are regenerated
- Phase 37 packet remains frozen - PASS when no Phase 37 outputs are mutated
- No new portfolio math - PASS when only gate logic is executed

**Validator Commands**
- Inherited Phase 37 validators still pass:
  - `.venv\Scripts\python scripts\validate_phase37_portfolio_outputs.py --output-dir data\processed\phase37_portfolio`
  - `.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase37_risk_diagnostics.py tests\test_phase37_portfolio_construction_runner.py tests\test_validate_phase37_portfolio_outputs.py -q`

---

## 8. Execution Authorization Boundary

Phase 38 execution authorization is now active for the bounded run defined in this guide.

**Activation Token**
- `approve phase38 execution`

**Authorization Conditions (Satisfied)**
- `docs/handover/phase38_execution_gate_ceo_memo.md` exists with locked threshold values (`252`, `0.80`)
- Threshold-lock docs refresh + SAW publication is complete
- Explicit in-thread token `approve phase38 execution` is issued

**Governance Disposition Options**
- `Continue`: Proceed with Phase 38 execution under locked thresholds
- `Edit`: Revise thresholds or gate contract before execution
- `Hold`: Defer Phase 38 execution pending further review

**Post-Activation Workflow**
1. Worker loads thresholds from CEO memo
2. Worker applies dual gate to frozen Phase 37 packet
3. Worker emits narrow delta outputs only
4. Worker publishes SAW closeout
5. CEO/PM reviews gate results and issues final disposition

---

## 9. Acceptance Checks for This Guide Round

This worker execution guide must satisfy the following acceptance checks:

**Threshold Externalization**
- Guide explicitly externalizes thresholds to CEO memo - PASS when threshold ownership is clear
- Guide forbids worker-side threshold estimation - PASS when forbidden actions list includes threshold inference
- Guide requires threshold loading from memo - PASS when execution steps include memo read

**Universal Gate Binding**
- Guide binds dual gate universally to all methods - PASS when no exceptions are listed
- Guide requires gate checks per validation AND per holdout - PASS when dual-window requirement is explicit
- Guide maps gate misses to `Pause` only - PASS when disposition is locked

**Evidence Discipline**
- Guide limits evidence to narrow delta outputs - PASS when allowed artifacts list is minimal
- Guide preserves Phase 37 packet as frozen - PASS when mutation is forbidden
- Guide forbids Phase 37 recomputation - PASS when forbidden actions list includes rerun

**Execution Authorization Status**
- Guide reflects explicit token issuance for bounded run only - PASS when activation boundary marks token as satisfied
- Guide preserves strict scope boundary with no expansion - PASS when forbidden actions remain explicit
- Guide keeps quarantines intact while authorized run executes - PASS when out-of-scope guardrails remain explicit

---

## 10. First Command (Authorized Run)

For the authorized bounded run, the first command is:

```powershell
Get-Content docs/handover/phase38_execution_gate_ceo_memo.md
```

This command loads the CEO-owned threshold constants required for gate execution.

---

## Summary

Phase 38 is execution-authorized for one bounded gate run only under the explicit token `approve phase38 execution`. The dual gate applies universally to all methods, with thresholds owned by the CEO/PM and externalized to a dedicated memo (`252` active days, `0.80` coverage ratio) using one common pair across validation and holdout. Workers load thresholds from the memo and do not derive or estimate values. Evidence remains limited to delta report + recommendation JSON + SAW, and all quarantines remain in force.

**Status**: EXECUTION AUTHORIZED (bounded run only)
**Governance Disposition (docs-only)**: `Continue` (threshold-lock round complete)
**Next Milestone**: Complete bounded gate execution and publish the final packet (`gate_diagnostics_delta.csv` + `gate_recommendation.json` + `saw_phase38_gate_execution_YYYYMMDD.md`)
**Activation Boundary**: `approve phase38 execution` token required
