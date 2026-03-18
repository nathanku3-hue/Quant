# Phase 37: Portfolio Construction and Risk Scaling on Surviving Bundles

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: CLOSED (bounded execution complete; CEO/PM disposition recorded: `Continue`; research-only packet remains frozen)
**Created**: 2026-03-09
**Phase 36 Status**: CLOSED on repaired `permno` path; robustness packet frozen at `Continue` with `3 Continue / 1 Pause`
**Activation**: Consumed on 2026-03-09 via `approve phase37 execution`; execution round completed under research-only quarantine
**Disposition**: Recorded on 2026-03-09 via governance memo: `Continue` (`3 Continue / 0 Pause / 0 Pivot`)

---

## Objective

Execute the governed next stage after Phase 36 by building a bounded portfolio-construction and risk-scaling layer over the 3 surviving research bundles without changing the repaired comparator contract, the governed windows, or the research quarantine.

Phase 37 is not a new alpha-discovery round. It is a governed portfolio-construction round that combines the surviving bundles under the same evaluation path and locked cost model, then publishes a decision-grade evidence packet for governance review.

---

## Locked Starting Point

**Surviving bundle set**
- `bundle_quality_vol`
- `bundle_vol_composite`
- `bundle_all_three`

**Paused bundle (excluded from active Phase 37 scope)**
- `bundle_quality_composite`
- Reason: failed the locked `20` bps holdout fail-closed floor in Phase 36 robustness

**Frozen source-of-truth docs**
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/handover/phase36_handover.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`
- `docs/saw_reports/saw_phase36_handover_20260309.md`

**Frozen source-of-truth artifacts**
- `data/processed/phase36_rule100/robustness/bundle_robustness_metrics.csv`
- `data/processed/phase36_rule100/robustness/bundle_robustness_recommendation.json`
- `data/processed/phase36_rule100/robustness/bundle_friction_stress.csv`
- `data/processed/phase36_rule100/robustness/robustness_input_manifest.json`
- `data/processed/phase36_rule100/robustness/robustness_comparator_snapshot.json`

---

## Locked Comparator Contract

**Governed comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed evaluation windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

**Path discipline**
- Same repaired `permno` evidence path only
- Same governed windows only
- Same friction/cost assumptions only
- Same simulation path only (`core.engine.run_simulation`)
- Same research-only quarantine until a later governance decision

---

## Scope Boundary

### In Scope
1. Combine the 3 surviving bundles into a governed portfolio-construction layer
2. Precompute and persist trailing sleeve risk primitives (`vol_63d`, `cov_126d`, `corr_126d`) before runner execution
3. Evaluate the locked portfolio methods (`equal_weight`, `inverse_vol_63d`, `capped_risk_budget`) under the same comparator contract
4. Emit fail-closed diagnostics, guardrail artifacts, and recommendation outputs for governance review
5. Publish Phase 37 execution docs, logs, lessons, context refresh, and SAW closeout

### Explicitly Out of Scope
1. Reopening Phase 36 robustness results or unpausing `bundle_quality_composite`
2. Discovering new signals or new bundle families
3. Production promotion, deployment, or live capital sizing
4. Vendor-enrichment execution (S&P IQ / BvD remains asynchronous)
5. Runtime key migration away from `permno`
6. Governed cost-model rewrites

---

## Execution Contract

### Sleeve Contract
- Active sleeves: exactly `3`
- Active sleeve IDs: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve must remain excluded: `bundle_quality_composite`
- Portfolio exposure model: long-only, fully invested, no leverage
- Rebalance cadence: monthly

### Risk Primitive Contract
- Volatility estimator: trailing `63` trading days
- Covariance / correlation estimator: trailing `126` trading days
- No forward leakage: estimators use only history available strictly before rebalance date
- Risk primitives must be persisted to `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- Warmup due insufficient trailing history is recorded as `warmup`, not treated as a hard governance failure

### Portfolio Method Contract
- Allowed methods only:
  - `equal_weight`
  - `inverse_vol_63d`
  - `capped_risk_budget`
- Optimized methods must obey:
  - `15% <= weight_i <= 50%`
  - `risk_share_i <= 40%`
  - `gross_turnover <= 25%`
  - `HHI <= 0.375`
- `capped_risk_budget` must fail closed on infeasibility or solver instability; no silent fallback
- Downward-only scaling remains locked
- Governed cost model remains locked at `10` bps for the baseline execution path

---

## Bounded Implementation Delivered

### Code Artifacts
- `strategies/phase37_portfolio_registry.py`
- `scripts/phase37_risk_diagnostics.py`
- `scripts/phase37_portfolio_construction_runner.py`
- `scripts/validate_phase37_portfolio_outputs.py`

### Test Artifacts
- `tests/test_phase37_portfolio_registry.py`
- `tests/test_phase37_risk_diagnostics.py`
- `tests/test_phase37_portfolio_construction_runner.py`
- `tests/test_validate_phase37_portfolio_outputs.py`

### Output Artifacts
- `data/processed/phase37_portfolio/portfolio_input_manifest.json`
- `data/processed/phase37_portfolio/portfolio_sleeve_inputs.parquet`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- `data/processed/phase37_portfolio/portfolio_regime_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.json`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`

### Evidence Docs
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/saw_reports/saw_phase37_portfolio_execution_20260309.md`

---

## Execution Results

**Portfolio recommendation**
- `Continue`
- Vote split: `3 Continue / 0 Pause / 0 Pivot`

**Method outcomes**
- `equal_weight`: `Continue`
- `inverse_vol_63d`: `Continue`
- `capped_risk_budget`: `Continue`

**Observed validation / holdout metrics**
- `equal_weight`: validation CAGR `41.41%`, holdout CAGR `8.57%`, validation Sharpe `1.63`, holdout Sharpe `0.44`
- `inverse_vol_63d`: validation CAGR `24.82%`, holdout CAGR `7.19%`, validation Sharpe `1.75`, holdout Sharpe `0.57`
- `capped_risk_budget`: validation CAGR `24.84%`, holdout CAGR `7.15%`, validation Sharpe `1.75`, holdout Sharpe `0.57`

**Guardrail observations**
- `equal_weight`: max HHI `0.333333`, max turnover `0.000000`
- `inverse_vol_63d`: max risk share `0.366918`, max HHI `0.345220`, max turnover `0.026954`
- `capped_risk_budget`: max risk share `0.333338`, max HHI `0.340196`, max turnover `0.037091`
- All observed values stayed within the locked guardrails

**Execution notes**
- `inverse_vol_63d` and `capped_risk_budget` each recorded `397` warmup days due trailing-risk lookback requirements
- Warmup rows are intentional and are not equivalent to a hard guardrail failure
- Baseline deltas were reconciled after canonical `permno` normalization between baseline target weights and return columns; current delta metrics are safe to read directly as relative performance versus the corrected baseline

---

## Acceptance Criteria

### Round 1 — Planning Skeleton
- `docs/phase_brief/phase37-brief.md` exists - PASS
- dormant planning state was explicit before activation - PASS
- scope was limited to the 3 surviving bundles only - PASS
- out-of-scope quarantines were explicit - PASS
- activation gate was explicit - PASS

### Round 2 — Execution-Design Planning
- `docs/phase_brief/phase37-worker-execution-guide.md` exists - PASS
- file-level ownership and acceptance checks were frozen before implementation - PASS
- `docs/context/current_context.json` and `docs/context/current_context.md` refreshed from brief state - PASS

### Round 3 — Portfolio Construction Execution
- Activation token `approve phase37 execution` was consumed before implementation - PASS
- Locked sleeves only (`bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`) - PASS
- Locked methods only (`equal_weight`, `inverse_vol_63d`, `capped_risk_budget`) - PASS
- Risk primitives were precomputed and persisted before the main runner - PASS
- The governed engine path stayed on `core.engine.run_simulation` with the locked `10` bps cost model - PASS
- Targeted Phase 37 pytest pack passed - PASS
- Runtime output validator passed on generated artifacts - PASS
- Execution docs, decision log, lessons, formula notes, context refresh, and SAW report were published - PASS

---

## Target Artifacts

### Delivered Code
- `strategies/phase37_portfolio_registry.py`
- `scripts/phase37_risk_diagnostics.py`
- `scripts/phase37_portfolio_construction_runner.py`
- `scripts/validate_phase37_portfolio_outputs.py`
- `tests/test_phase37_portfolio_registry.py`
- `tests/test_phase37_risk_diagnostics.py`
- `tests/test_phase37_portfolio_construction_runner.py`
- `tests/test_validate_phase37_portfolio_outputs.py`

### Delivered Reporting
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/saw_reports/saw_phase37_portfolio_execution_20260309.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/notes.md`

### Delivered Data / Outputs
- `data/processed/phase37_portfolio/portfolio_input_manifest.json`
- `data/processed/phase37_portfolio/portfolio_sleeve_inputs.parquet`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- `data/processed/phase37_portfolio/portfolio_regime_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.json`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`

---

## Execution Order

1. Freeze the 3-sleeve contract from Phase 36 robustness
2. Precompute sleeve inputs and risk primitives
3. Run all 3 approved portfolio methods on the same governed engine path
4. Validate guardrails, manifests, and recommendation outputs
5. Publish execution evidence docs and governance trail
6. Refresh the context packet and hold for governance review

---

## Operational Guardrails

- Use `.venv\Scripts\python` only for the approved bounded execution path
- Treat all Phase 36 robustness artifacts as read-only
- Keep `bundle_quality_composite` paused unless a later governance decision explicitly changes scope
- Do not introduce new alpha factors or sleeves into this phase
- Do not change runtime key contracts (`permno` stays governed)
- Do not rewrite the governed cost model
- Do not interpret this execution brief as production approval
- Do not start the next Phase 37 round until governance reviews this packet

---

## Approval State

**Current State**
- Phase 36: closed
- Phase 37: closed (execution frozen after `Continue` disposition)
- Governance: disposition recorded from `docs/handover/phase37_governance_review.md`

**Explicit Boundary**
- Allowed now: docs-only carry-forward into a dormant planning skeleton at `docs/phase_brief/phase38-brief.md`
- Forbidden now: any new Phase 37 execution, reruns, production promotion, vendor-dependent execution, runtime-key migration, governed cost-model rewrites, or sleeve-set changes

**Execution Boundary After This Round**
- The Phase 37 packet is final and frozen
- No additional Phase 37 coding or data regeneration is pending
- Research quarantine remains in force

---

## Live Loop State

**Current state**
- Data layer: closed and trusted
- Phase 35: closed/no-go on repaired reruns
- Phase 36: closed with robustness and handoff packets frozen
- Phase 37: bounded execution round complete with portfolio recommendation `Continue`

**Immediate next milestone**
- Create or refresh `docs/phase_brief/phase38-brief.md` as a dormant planning brief for the active-days/coverage gate plus governance carry-forward, with no execution activation in this round

---

## New Context Packet

### What Was Done
- Completed and validated the bounded Phase 37 execution round on the 3 active sleeves only.
- Confirmed the repaired Phase 37 packet at `3 Continue / 0 Pause / 0 Pivot` across `equal_weight`, `inverse_vol_63d`, and `capped_risk_budget`.
- Recorded CEO/PM governance disposition as `Continue` and closed Phase 37 as a frozen research packet.

### What Is Locked
- Active sleeves remain `bundle_quality_vol`, `bundle_vol_composite`, and `bundle_all_three`; `bundle_quality_composite` remains paused.
- Comparator remains `data/processed/features_phase35_repaired.parquet` with the same governed windows and the same `10` bps governed cost model.
- Method set remains equal-weight, inverse-vol, and capped risk-budget with `15%-50%` sleeve bounds, `40%` risk-share cap, `<=25%` gross turnover, `HHI<=0.375`, and fail-closed infeasibility handling.
- Production promotion, vendor execution, runtime-key migration, cost-model rewrites, and new sleeve discovery remain out of scope.

### What Is Next
- Start a planning-only handoff to `docs/phase_brief/phase38-brief.md` in dormant state.
- Keep Phase 37 frozen; do not reopen execution in this round.
- Preserve comparator `data/processed/features_phase35_repaired.parquet`, governed windows, and locked `10` bps cost model as inherited constraints for planning context.

### First Command
```text
Get-Content docs/phase_brief/phase38-brief.md
```

### Next Todos
- Draft or refresh `docs/phase_brief/phase38-brief.md` as a dormant planning skeleton (`Status: DORMANT`, execution blocked pending explicit activation token).
- Regenerate `docs/context/current_context.{json,md}` from updated brief state.
- Keep research quarantine explicit in all follow-up docs.


