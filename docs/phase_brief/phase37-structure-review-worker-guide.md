# Phase 37 Structure Review Worker Guide

**Date**: 2026-03-09
**Round ID**: `P37-SR-01`
**Scope**: Section-by-section structure review only for the dormant Phase 37 planning brief
**Do Not Do**: start Phase 37 code scaffolding, write portfolio-construction scripts/tests, unpause `bundle_quality_composite`, change `permno`, rewrite the governed cost model, add vendor-dependent scope, or imply production readiness

---

## Mission

Tighten and review `docs/phase_brief/phase37-brief.md` section-by-section so the portfolio-construction structure is explicit, bounded, and fail-closed before any activation token is considered.

This round is review-and-spec work only. The worker must keep Phase 37 dormant, make the optimization constraints and risk-budget boundaries explicit, and stop before any execution-design or code work begins.

**Frozen truth from Phase 36**
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`
- Comparator: `data/processed/features_phase35_repaired.parquet`
- Windows: `2022-01-01` -> `2024-12-31` via the locked calibration / validation / holdout split
- Research quarantine: still in force

---

## Scope Lock

### Allowed
- Review and tighten `docs/phase_brief/phase37-brief.md`
- Create this worker guide
- Update `docs/decision log.md` and `docs/lessonss.md`
- Publish a docs-only SAW report for the structure-review round
- Repoint Phase 37 immediate-next-step language if needed to reflect section-by-section review

### Forbidden
- Any new Python, strategy, runner, validator, or test file for Phase 37 execution
- Any optimizer implementation or backtest execution
- Any new factor/signal discovery
- Any change to the frozen comparator, windows, or friction assumptions
- Any production promotion, live-sizing, or deployment language
- Any dependency on S&P IQ / BvD procurement

---

## File Ownership for This Round

### Create
- `docs/phase_brief/phase37-structure-review-worker-guide.md`
- `docs/saw_reports/saw_phase37_structure_review_20260309.md`

### Update
- `docs/phase_brief/phase37-brief.md`
- `docs/decision log.md`
- `docs/lessonss.md`

### Read-Only Inputs
- `docs/handover/phase36_handover.md`
- `docs/phase36_bundle_robustness_exec_summary.md`
- `docs/phase36_bundle_robustness_report.md`
- `docs/saw_reports/saw_phase36_robustness_20260308.md`
- `docs/saw_reports/saw_phase36_handover_20260309.md`
- `docs/phase_brief/phase36-brief.md`

---

## Section-by-Section Review Order

### Step 1 — Lock Objective, Survivors, and Comparator
Review these sections first:
- `Objective`
- `Locked Starting Point`
- `Locked Comparator Contract`

Required outcomes:
- exactly `3` active sleeves remain in scope
- `bundle_quality_composite` remains paused
- repaired `permno` comparator stays frozen
- same windows and same governed cost path remain explicit

### Step 2 — Lock Sleeve Contract
Review `Workstream A — Freeze Bundle Sleeves`.

Required outcomes:
- portfolio layer is explicitly long-only and fully invested
- `gross_exposure<=1.0` and `weights>=0` are stated
- rebalance cadence is monthly for the first governed round
- no hidden cash sleeve, leverage sleeve, or paused-bundle leakage is allowed

### Step 3 — Lock Risk-Primitive Defaults
Review `Workstream B — Estimate Risk Primitives`.

Required outcomes:
- `vol_63d` and `cov_126d` are the review-target defaults
- all estimators are trailing-only and PIT-safe
- unstable covariance or insufficient history is fail-closed
- no forward leakage or same-day lookahead wording remains

### Step 4 — Lock Portfolio-Construction Candidates
Review `Workstream C — Portfolio Construction Candidates`.

Required outcomes:
- the first execution-design round compares all `3` candidate methods together:
  1. equal-weight
  2. inverse-vol
  3. capped risk-budget
- no expected-return optimizer or mean-variance alpha fitting is authorized
- all methods are reviewed under identical windows, costs, and diagnostics

### Step 5 — Lock Optimization Constraints and Risk Budgets
Review `Workstream D — Risk Scaling and Guardrails` and `Proposed Constraint Locks for Structure Review`.

Required outcomes:
- hard weight bounds stay `15%` to `50%` for optimized methods
- risk-share cap stays `40%` max per sleeve
- turnover boundary stays `<=25%` gross per monthly rebalance
- scaling remains downward-only with no leverage
- constraint failure remains fail-closed rather than auto-relaxed

### Step 6 — Lock Evidence Gate Inputs
Review `Workstream E — Evidence Gate Design`.

Required outcomes:
- evidence gate remains on the same repaired comparator path
- regime diagnostics use existing Phase 35 behavior-ledger daily labels
- continue / pause / pivot recommendation remains at the portfolio-construction layer only

### Step 7 — Lock Approval Boundary
Review `Approval State` and `Live Loop State`.

Required outcomes:
- Phase 37 remains dormant after this round
- canonical unlock token remains `approve phase37 execution`
- no wording implies that structure review alone authorizes code or experiments

---

## Acceptance Checks

- `CHK-P37-SR-01`: Phase 37 remains dormant and limited to the 3 surviving sleeves only
- `CHK-P37-SR-02`: Comparator, windows, and governed cost path remain frozen
- `CHK-P37-SR-03`: Sleeve contract is long-only, fully invested, and monthly-rebalanced
- `CHK-P37-SR-04`: Risk-primitive defaults and fail-closed behavior are explicit
- `CHK-P37-SR-05`: Equal-weight, inverse-vol, and capped risk-budget are bounded side-by-side
- `CHK-P37-SR-06`: Weight bounds, risk-share cap, turnover boundary, and downward-only scaling are explicit
- `CHK-P37-SR-07`: Approval boundary is explicit and still blocks execution without `approve phase37 execution`
- `CHK-P37-SR-08`: Decision log and lessons are updated for this round
- `CHK-P37-SR-09`: Docs-only SAW report is published and validator-clean

---

## Required Governance Updates

### Decision Log
Add a new entry that records:
- Phase 37 structure review is now the active next-step contract
- optimization constraints and risk-budget boundaries are tightened before activation
- no Phase 37 code work is authorized from this round

### Lessons
Add one entry that records:
- structure-review rounds must lock optimization boundaries before worker-guide-to-code transition
- portfolio-construction planning must not silently drift into optimizer implementation

---

## Reviewer Mapping (Mandatory)

- **Reviewer A**: strategy correctness and regression risk for portfolio-construction scope
- **Reviewer B**: runtime / operational boundary discipline and no-execution contract
- **Reviewer C**: data-boundary discipline on comparator, windows, and cost-model freeze

Ownership rule:
- implementer and reviewers must be distinct agents

---

## SAW Closeout

Create `docs/saw_reports/saw_phase37_structure_review_20260309.md`.

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
.venv\Scripts\python .codex/skills/_shared/scripts/validate_saw_report_blocks.py --report-file docs/saw_reports/saw_phase37_structure_review_20260309.md
```

```powershell
$packet = Select-String -Path "docs/saw_reports/saw_phase37_structure_review_20260309.md" -Pattern '^ClosurePacket:' | Select-Object -ExpandProperty Line
.venv\Scripts\python .codex/skills/_shared/scripts/validate_closure_packet.py --packet $packet --require-open-risks-when-block --require-next-action-when-block
```

---

## Definition of Done

All of the following must be true:
1. `docs/phase_brief/phase37-brief.md` is tightened section-by-section around optimization constraints and risk-budget boundaries
2. `docs/phase_brief/phase37-structure-review-worker-guide.md` exists and is current
3. `docs/decision log.md` and `docs/lessonss.md` are updated
4. `docs/saw_reports/saw_phase37_structure_review_20260309.md` exists and validates cleanly
5. Phase 37 remains dormant with no code or execution artifacts created

---

## Stop Conditions

Stop and publish `BLOCK` if any of the following occur:
- the brief drifts into code implementation or execution planning beyond structure review
- the paused bundle is reintroduced into active scope
- comparator / windows / cost-model freeze is softened
- the worker proposes leverage, production deployment, or vendor-dependent constraints
- the SAW validators fail
