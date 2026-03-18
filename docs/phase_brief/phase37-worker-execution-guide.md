# Phase 37 Worker Execution Guide

**Date**: 2026-03-09
**Round ID**: `P37-EDP-01`
**Scope**: Docs-only execution-design planning for Phase 37 portfolio construction on the 3 surviving bundles
**Do Not Do**: write Python code, create tests, scaffold runners, estimate risk primitives, run optimizers, generate portfolio artifacts, unpause `bundle_quality_composite`, change `permno`, rewrite the governed cost model, or imply production readiness

---

## Mission

Translate the already approved Phase 37 constraint surface into an exact file-level execution-design contract so a future engineering round can implement portfolio construction without re-opening governance questions.

This round is still planning only. The worker must define responsibilities, interfaces, artifacts, validators, and acceptance checks for future Phase 37 implementation while keeping execution fully dormant.

**Frozen truth**
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`
- Comparator: `data/processed/features_phase35_repaired.parquet`
- Risk primitives: trailing `vol_63d`, `cov_126d`
- Method set: equal-weight, inverse-vol, capped risk-budget
- Constraint surface: `15%-50%` sleeve bounds, `40%` max risk share, `<=25%` monthly gross turnover, downward-only scaling, fail-closed behavior
- Execution unlock token: `approve phase37 execution`

---

## Scope Lock

### Allowed
- Define exact file ownership and module responsibilities for future Phase 37 implementation
- Define interface contracts for planned scripts, strategy registry, validators, and reports
- Define planned commands, acceptance checks, and evidence expectations for the future execution round
- Update `docs/phase_brief/phase37-brief.md`, `docs/decision log.md`, `docs/lessonss.md`, and context artifacts
- Publish a docs-only SAW report for this planning round

### Forbidden
- Any executable Phase 37 implementation (`.py`, tests, generated data, reports from live computation)
- Any portfolio-construction backtest, optimizer run, or risk-estimation run
- Any relaxation of the locked constraint surface
- Any production, deployment, broker, or live-sizing language
- Any new vendor-dependent scope

---

## File Ownership for the Future Execution Round

These files are design targets only in this round. They must not be created or modified as executable artifacts yet.

### Planned Strategy / Config Surface
- `strategies/phase37_portfolio_registry.py`
  - Owns portfolio-method registry for:
    - `equal_weight`
    - `inverse_vol_63d`
    - `capped_risk_budget`
  - Encodes method metadata, required inputs, constraint hooks, and evaluation labels

### Planned Runtime Scripts
- `scripts/phase37_portfolio_construction_runner.py`
  - Loads frozen sleeve inputs
  - Applies the 3 portfolio methods under the locked constraint surface
  - Emits method comparison outputs and portfolio recommendation surfaces
- `scripts/phase37_risk_diagnostics.py`
  - Computes and validates sleeve-level risk primitives and guardrail diagnostics
  - Produces covariance stability, turnover, concentration, and regime-split diagnostics
- `scripts/validate_phase37_portfolio_outputs.py`
  - Fail-closed validation of all Phase 37 output artifacts
  - Verifies method coverage, guardrail adherence, and recommendation consistency

### Planned Tests
- `tests/test_phase37_portfolio_registry.py`
- `tests/test_phase37_portfolio_construction_runner.py`
- `tests/test_phase37_risk_diagnostics.py`
- `tests/test_validate_phase37_portfolio_outputs.py`

### Planned Docs / Evidence Outputs
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/saw_reports/saw_phase37_portfolio_*.md`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`

---

## Interface Contract to Lock Now

### Strategy Registry Contract
The future registry must define, for each method:
- `method_id`
- `method_label`
- `required_inputs`
- `weight_rule`
- `constraint_surface`
- `diagnostic_fields`
- `promotion_surface`

### Runner Input Contract
The future runner must accept:
- features input: `data/processed/features_phase35_repaired.parquet`
- frozen sleeve source artifacts from Phase 36
- locked window split (calibration / validation / holdout)
- locked cost model and same simulation path family
- explicit `method_id` filters for the 3 approved methods only

### Runner Output Contract
The future runner must emit:
- method-level portfolio metrics
- validation and holdout delta metrics
- turnover and concentration diagnostics
- risk-budget utilization diagnostics
- explicit continue / pause / pivot recommendation payload

### Validator Contract
The future validator must fail on:
- any method outside the approved set
- any relaxed weight / risk-share / turnover / scaling boundary
- any output artifact missing required columns or recommendation fields
- any mismatch between diagnostics and the recommendation payload
- any attempt to treat a blocked or infeasible method as a valid fallback

---

## Design Slices for the Future Execution Round

### Slice 1 — Freeze Registry and Method Metadata
Future implementation owner:
- `strategies/phase37_portfolio_registry.py`

Done condition:
- exactly 3 approved portfolio methods
- no hidden optimizer variants
- no expected-return estimator field

### Slice 2 — Freeze Risk-Diagnostic Contract
Future implementation owners:
- `scripts/phase37_risk_diagnostics.py`
- `tests/test_phase37_risk_diagnostics.py`

Done condition:
- `vol_63d` and `cov_126d` contracts are explicit
- fail-closed behavior for unstable covariance is covered
- turnover and concentration diagnostics are named and bounded

### Slice 3 — Freeze Runner Contract
Future implementation owners:
- `scripts/phase37_portfolio_construction_runner.py`
- `tests/test_phase37_portfolio_construction_runner.py`

Done condition:
- runner accepts only approved methods and frozen inputs
- equal-weight, inverse-vol, and capped risk-budget are comparable side-by-side
- no execution path relaxes the constraint surface

### Slice 4 — Freeze Validation Surface
Future implementation owners:
- `scripts/validate_phase37_portfolio_outputs.py`
- `tests/test_validate_phase37_portfolio_outputs.py`

Done condition:
- output schema is fully specified
- guardrail violations are hard failures
- recommendation payload is machine-checkable

### Slice 5 — Freeze Evidence and Reporting Contract
Future implementation owners:
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/saw_reports/saw_phase37_portfolio_*.md`

Done condition:
- CEO/PM summary and technical appendix are named
- SAW closeout requirements are explicit
- no production language leaks into research evidence docs

---

## Commands to Stage for the Future Execution Round

These commands are design placeholders only. Do not run them in this round.

```powershell
.venv\Scripts\python -m pytest tests/test_phase37_portfolio_registry.py tests/test_phase37_risk_diagnostics.py tests/test_phase37_portfolio_construction_runner.py tests/test_validate_phase37_portfolio_outputs.py -q
```

```powershell
.venv\Scripts\python scripts/phase37_portfolio_construction_runner.py --features-path data/processed/features_phase35_repaired.parquet --output-dir data/processed/phase37_portfolio
```

```powershell
.venv\Scripts\python scripts/validate_phase37_portfolio_outputs.py --output-dir data/processed/phase37_portfolio
```

---

## Acceptance Checks for This Planning Round

- `CHK-P37-WG-01`: `docs/phase_brief/phase37-worker-execution-guide.md` exists and remains docs-only
- `CHK-P37-WG-02`: Future file ownership is explicit for registry, runner, diagnostics, validator, tests, and reporting
- `CHK-P37-WG-03`: Interface contracts are explicit for inputs, outputs, and fail-closed validation
- `CHK-P37-WG-04`: The 3 approved methods remain the only allowed future portfolio methods
- `CHK-P37-WG-05`: The locked constraint surface is preserved without relaxation
- `CHK-P37-WG-06`: `docs/phase_brief/phase37-brief.md` points to this guide as the immediate next milestone
- `CHK-P37-WG-07`: `docs/context/current_context.json` and `docs/context/current_context.md` refresh from the Phase 37 brief
- `CHK-P37-WG-08`: `docs/decision log.md` and `docs/lessonss.md` are updated for this planning round
- `CHK-P37-WG-09`: Docs-only SAW report is published and validator-clean

---

## Required Governance Updates

### Brief
Update `docs/phase_brief/phase37-brief.md` so:
- Round 2 reflects this execution-design planning round
- the immediate next milestone points to this worker guide
- the New Context Packet reflects this guide as the current next-step contract

### Decision Log
Add a new entry that records:
- the worker execution guide is now the active next-step contract
- file-level execution responsibilities are locked before implementation
- execution remains blocked until `approve phase37 execution`

### Lessons
Add one entry that records:
- when portfolio-construction constraints are approved, the next step is file-level execution design, not code
- context artifacts must be refreshed from the latest approved phase brief as soon as the planning contract changes

### Context Refresh
Run:
```powershell
.venv\Scripts\python scripts/build_context_packet.py
```

Then validate:
```powershell
.venv\Scripts\python scripts/build_context_packet.py --validate
```

Done when both are current and valid:
- `docs/context/current_context.json`
- `docs/context/current_context.md`

---

## Reviewer Mapping (Mandatory)

- **Reviewer A**: strategy correctness and method-boundary discipline
- **Reviewer B**: runtime / operational boundary discipline and no-execution enforcement
- **Reviewer C**: data-boundary discipline on comparator, windows, cost model, and fail-closed surfaces

Ownership rule:
- implementer and reviewers must be distinct agents

---

## SAW Closeout

Create `docs/saw_reports/saw_phase37_worker_execution_guide_20260309.md`.

The SAW report must include:
- `SAW Verdict: PASS/BLOCK`
- `Hierarchy Confirmation:`
- `Ownership Check:`
- findings table
- scope split summary
- document changes showing
- `Open Risks:`
- `Next action:`
- `ClosurePacket:`
- `ClosureValidation:`
- `SAWBlockValidation:`

Validator commands:
```powershell
.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase37_worker_execution_guide_20260309.md
```

```powershell
$packet = Select-String -Path "docs/saw_reports/saw_phase37_worker_execution_guide_20260309.md" -Pattern '^ClosurePacket:' | Select-Object -ExpandProperty Line
.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet $packet --require-open-risks-when-block --require-next-action-when-block
```

---

## Definition of Done

All of the following must be true:
1. `docs/phase_brief/phase37-worker-execution-guide.md` exists and stays docs-only
2. Future module responsibilities and interface contracts are explicit
3. `docs/phase_brief/phase37-brief.md` is updated to point to this guide
4. `docs/context/current_context.json` and `docs/context/current_context.md` refresh successfully from the Phase 37 brief
5. `docs/decision log.md` and `docs/lessonss.md` are updated
6. `docs/saw_reports/saw_phase37_worker_execution_guide_20260309.md` exists and validates cleanly
7. No executable Phase 37 artifacts are created in this round

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- any executable Phase 37 file is created or modified outside docs/context refresh
- the guide introduces a portfolio method outside equal-weight, inverse-vol, and capped risk-budget
- the guide softens the weight / risk-share / turnover / scaling constraints
- context refresh still resolves to stale Phase 36 handover state instead of the Phase 37 brief
- the SAW validators fail
