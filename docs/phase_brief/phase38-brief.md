# Phase 38: Active-Days / Coverage Gate on the Frozen Phase 37 Portfolio Packet

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: CLOSED (bounded gate run + governance review closed on `Continue`; handoff to dormant Phase 39 planning only; research-only quarantine intact)
**Created**: 2026-03-09
**Phase 37 Status**: CLOSED with CEO/PM disposition `Continue`; repaired research packet remains frozen
**Activation Rule**: Explicit in-thread token `approve phase38 execution` is issued; authorization is limited to one bounded Phase 38 gate run and a single final packet

---

## Objective

Carry the repaired Phase 37 portfolio packet through one bounded dual-gate execution that applies the locked active-days / coverage contract to portfolio methods with warmup periods, using frozen Phase 37 evidence only.

Phase 38 is not a new signal-discovery phase, not a broad portfolio-construction implementation phase, and not a deployment phase. It is a bounded execution round that applies one locked operational guardrail:
- minimum active-days / coverage treatment for methods that require lookback history before they become investable.

The bounded run is now complete. The final packet shows that all three frozen Phase 37 methods transition from `Continue` to `Pause` under the locked `252 / 0.80` dual gate, while the frozen Phase 37 evidence itself remains unchanged.

---

## Inherited Frozen Truth

**Frozen Phase 37 packet truth**
- Portfolio decision: `Continue`
- Method votes: `3 Continue / 0 Pause / 0 Pivot`
- Active sleeves: `bundle_quality_vol`, `bundle_vol_composite`, `bundle_all_three`
- Paused sleeve: `bundle_quality_composite`

**Frozen source-of-truth docs**
- `docs/phase37_portfolio_exec_summary.md`
- `docs/phase37_portfolio_construction_report.md`
- `docs/handover/phase37_governance_review.md`
- `docs/saw_reports/saw_phase37_portfolio_execution_20260309.md`
- `docs/saw_reports/saw_phase37_governance_review_20260309.md`

**Frozen source-of-truth artifacts**
- `data/processed/phase37_portfolio/portfolio_recommendation.json`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.json`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`
- `data/processed/phase37_portfolio/portfolio_input_manifest.json`

These documents and artifacts are inherited read-only inputs for Phase 38 gate execution and governance review.

---

## Locked Comparator Contract

**Governed comparator artifact**
- `data/processed/features_phase35_repaired.parquet`

**Governed evaluation windows**
- Calibration: `2022-01-01` -> `2023-06-30`
- Validation: `2023-07-01` -> `2024-03-31`
- Holdout: `2024-04-01` -> `2024-12-31`

**Non-negotiable carry-forward constraints**
- Same repaired `permno` path only
- Same governed windows only
- Same `10` bps governed cost model only
- Same simulation path family only (`core.engine.run_simulation`)
- Same research-only quarantine until a later governance decision explicitly changes state

---

## Scope Boundary

### In Scope
1. Execute one bounded Phase 38 dual-gate run on frozen Phase 37 packet inputs using locked thresholds
2. Deliver one final packet with narrow gate-specific evidence outputs only
3. Preserve warmup interpretation and `Pause` mapping without rewriting frozen Phase 37 evidence
4. Carry forward all Phase 37/38 governance boundaries and quarantine constraints unchanged
5. Refresh docs/context to reflect completed bounded-run state and governance-review handoff

### Explicitly Out of Scope
1. Reopening or rerunning Phase 37 execution
2. Changing the Phase 37 portfolio methods or sleeve set
3. Unpausing `bundle_quality_composite`
4. Production promotion, deployment, or live capital sizing
5. Vendor-enrichment execution (S&P IQ / BvD remains asynchronous)
6. Runtime key migration away from `permno`
7. Governed cost-model rewrites
8. New sleeve discovery or new portfolio methods
9. Any Phase 38 code scaffolding, test generation, or artifact regeneration outside the bounded execution contract

---

## Planning Contract

### Gate Purpose
The active-days / coverage gate exists to prevent optimization-aware methods from being treated as decision-grade during periods where they are still warming up or materially under-covered by valid history.

### Metric Definitions
**`active_days`**
- Count of governed days where a method is in a valid investable state (`ready`) rather than `warmup` or `blocked`

**`eligible_days`**
- Count of governed days inside the target evaluation window for the method under review

**`coverage_ratio`**
- `active_days / eligible_days`

### Warmup Interpretation
- `warmup` remains distinct from `failure`
- A warmup period is not retroactively treated as a Phase 37 defect
- Phase 38 may add a future minimum active-days / coverage gate for decisioning, but that gate must not rewrite the frozen Phase 37 evidence packet

### Threshold Discipline
- Threshold policy is now governance-locked in `docs/handover/phase38_execution_gate_ceo_memo.md`
- Locked values are common across both validation and holdout windows
- Explicit token `approve phase38 execution` is issued; execution is authorized only for the bounded gate run
- No worker-side threshold derivation, estimation, or override is authorized

### Dual Gate Specification (Governance-Locked Constants)
**Locked threshold constants (CEO memo)**
- `MIN_ACTIVE_DAYS_THRESHOLD = 252`
- `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`

**Gate binding contract**
- One common threshold pair applies across both windows
- Gate checks must be applied per validation window AND per holdout window independently
- Gate misses map to `Pause` disposition, not `Blocked`
- Scope remains bounded to one authorized gate run and single final packet; no broader execution expansion is authorized

---

## Planned Evidence Surface

If Phase 38 is later activated, the future execution/evidence round must remain bound to the frozen Phase 37 packet and should prove any gate decision against the inherited artifacts below:
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`

**Phase 38 execution contract (when authorized)**
Future Phase 38 execution must:
- Load the frozen Phase 37 portfolio packet without recomputation
- Apply the dual gate (active-days and coverage-ratio) per validation AND per holdout
- Emit only narrow gate-specific diagnostics and transition delta report
- Avoid recomputing the frozen Phase 37 portfolio packet
- Map gate misses to `Pause` disposition only

**Inherited validator/test commands to preserve**
- `.venv\Scripts\python scripts\validate_phase37_portfolio_outputs.py --output-dir data\processed\phase37_portfolio`
- `.venv\Scripts\python -m pytest tests\test_phase37_portfolio_registry.py tests\test_phase37_risk_diagnostics.py tests\test_phase37_portfolio_construction_runner.py tests\test_validate_phase37_portfolio_outputs.py -q`

These commands remain evidence anchors for the frozen packet; they do not authorize Phase 38 execution by themselves.

---

## Acceptance Criteria

### Round 1 — Threshold Lock + Bounded Execution Authorization
- `docs/phase_brief/phase38-brief.md` exists - PASS when created
- Bounded execution-authorization state is explicit - PASS when status/activation rule are present
- Phase 37 frozen packet truth is listed accurately - PASS when inherited packet fields match the repaired evidence packet
- Locked comparator/cost/runtime-key constraints are explicit - PASS when carry-forward constraints are written verbatim
- In-scope boundary is limited to active-days / coverage gate plus governance carry-forward - PASS when no broader portfolio work is included
- Hard-blocked out-of-boundary items are explicit - PASS when production/vendor/key/cost/sleeve boundaries are listed
- `active_days`, `eligible_days`, and `coverage_ratio` are explicitly defined - PASS when formulas are written in the brief
- Thresholds are governance-locked and sourced from CEO memo - PASS when constants are explicit and unchanged from memo
- Execution token `approve phase38 execution` is issued and bounded scope is explicit - PASS when activation facts and scope limits are present
- Bootstrap context can be regenerated from the brief without ambiguity - PASS when the final context block is complete

---

## Target Artifacts

### Delivered In This Round
- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`
- `docs/phase_brief/phase38-brief.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/notes.md`
- `docs/saw_reports/saw_phase38_gate_execution_20260309.md`

### Retained Governance Inputs
- `docs/phase_brief/phase38-worker-execution-guide.md`
- `docs/handover/phase38_execution_gate_ceo_memo.md`

These retained governance inputs continue to define the bounded contract that produced the final packet.

### Review Surface
- Final packet review is now bounded to the gate delta artifact, the gate recommendation JSON, and the execution-round SAW closeout.

Research-only quarantine remains unchanged during this review surface.

---

## Approval State

**Current State**
- Phase 37: closed and frozen after `Continue` disposition
- Phase 38: bounded gate run executed on the frozen packet; governance review closed on `Continue`
- Gate outcome: `Pause` with `0 Continue / 3 Pause / 0 Pivot`
- Threshold lock: complete (`MIN_ACTIVE_DAYS_THRESHOLD=252`, `MIN_COVERAGE_RATIO_THRESHOLD=0.80`)
- Execution token: issued and consumed for the bounded run (`approve phase38 execution`)

**Allowed Now**
- Keep Phase 38 evidence frozen as governance-closed reference state
- Open dormant Phase 39 planning focused only on threshold-window reachability policy and window-geometry design
- Maintain docs/context alignment while preserving all hard-blocked boundaries
- Keep the frozen Phase 37 evidence packet immutable

**Forbidden Now**
- Any rerun or mutation of Phase 37 outputs
- Any regeneration of Phase 38 gate artifacts without new governance approval
- Any Phase 38 code scaffolding or test generation beyond the bounded run
- Any production-facing work

**Activation Boundary**
- D-236 token issuance applied only to the completed bounded run; any further execution requires a fresh governance instruction

---

## Live Loop State

**Current state**
- Data layer: closed and trusted
- Phase 35: closed/no-go on repaired reruns
- Phase 36: closed with robustness and handoff packets frozen
- Phase 37: closed with `Continue` disposition on the repaired portfolio packet
- Phase 38: bounded execution complete; locked dual gate pauses all three methods without mutating Phase 37

**Immediate next milestone**
- Start dormant Phase 39 planning for threshold-window reachability policy and window-geometry design only (no execution authorization)

---

## New Context Packet

### What Was Done
- Executed the bounded dual-gate run against the frozen Phase 37 packet using locked thresholds (`252`, `0.80`) and no worker-side policy changes.
- Published `data/processed/phase38_gate/gate_diagnostics_delta.csv` and `data/processed/phase38_gate/gate_recommendation.json` as the only new execution artifacts.
- Recorded the gate outcome: `0 Continue / 3 Pause / 0 Pivot`; all three Phase 37 methods transition from `Continue` to `Pause` under the locked contract.
- Preserved the frozen Phase 37 evidence packet and all research-only quarantines while completing the bounded run.

### What Is Locked
- Active sleeve contract remains `bundle_quality_vol`, `bundle_vol_composite`, and `bundle_all_three`; `bundle_quality_composite` remains paused.
- Comparator remains `data/processed/features_phase35_repaired.parquet` with locked windows and locked `10` bps governed cost model.
- Locked gate thresholds remain `MIN_ACTIVE_DAYS_THRESHOLD=252` and `MIN_COVERAGE_RATIO_THRESHOLD=0.80`, applied identically to validation and holdout.
- Research-only quarantine remains in force: no production promotion, vendor execution, runtime-key migration, cost-model rewrites, or new sleeve discovery.

### What Is Next
- Open `docs/phase_brief/phase39-brief.md` in dormant planning mode focused only on threshold-window reachability policy and window-geometry design.
- Keep Phase 38 and frozen Phase 37 packets immutable; do not rerun bounded gate execution without fresh governance authorization.
- Keep all research-only quarantine and out-of-boundary hard blocks unchanged.

### First Command
```text
Get-Content data/processed/phase38_gate/gate_recommendation.json
```

### Next Todos
- Draft/maintain `docs/phase_brief/phase39-brief.md` as dormant policy-planning only.
- Keep Phase 38 and Phase 37 packets frozen with no reruns or recomputation.
- Keep research quarantine explicit in every follow-up artifact.
- Await explicit future governance approval before any new execution work.


