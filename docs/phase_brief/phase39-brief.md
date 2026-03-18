# Phase 39: Threshold-Window Reachability Policy (Dormant Planning)

Current Governance State: Phase 47 (Coverage Remedy Planning - Docs-Only). Runtime surface: Sovereign Cockpit (dashboard.py). Goal: Alpha Sovereign Engine live selector.


**Status**: DORMANT (planning-only; reachability policy locked; execution not authorized)
**Created**: 2026-03-09
**Predecessor**: Phase 38 closed on governance `Continue` with bounded gate evidence frozen
**Governance Disposition**: `Continue` (policy packet sealed; no execution token issued in this round)
**Execution Authorization**: Not granted in this brief; no Phase 39 execution token exists

---

## Objective

Lock a fail-closed governance policy for threshold-window reachability after the Phase 38 bounded gate outcome (`0 Continue / 3 Pause / 0 Pivot`) under the frozen `252 / 0.80` dual-gate contract.

Phase 39 is policy design and carry-forward only. It does not execute or re-execute any data, strategy, simulation, or portfolio-construction workflow.

---

## Frozen Inputs (Read-Only)

- `data/processed/phase38_gate/gate_diagnostics_delta.csv`
- `data/processed/phase38_gate/gate_recommendation.json`
- `docs/saw_reports/saw_phase38_gate_execution_20260309.md`
- `docs/handover/phase38_governance_review.md`
- `docs/handover/phase38_execution_gate_ceo_memo.md`
- `docs/phase_brief/phase38-brief.md`
- `data/processed/phase37_portfolio/portfolio_guardrail_diagnostics.csv`
- `data/processed/phase37_portfolio/portfolio_method_comparison.csv`
- `data/processed/phase37_portfolio/portfolio_recommendation.json`
- `data/processed/phase37_portfolio/portfolio_risk_primitives.parquet`

---

## Locked Contracts (Carry-Forward)

- Comparator remains `data/processed/features_phase35_repaired.parquet`
- Runtime key remains `permno`
- Governed cost model remains `10` bps
- Dual gate remains the frozen policy family
- Locked constants remain `MIN_ACTIVE_DAYS_THRESHOLD = 252` and `MIN_COVERAGE_RATIO_THRESHOLD = 0.80`
- Research-only quarantine remains in force
- Phase 37 and Phase 38 evidence packets remain immutable

---

## Locked Policy Surface

1. A pre-lock reachability check is required before any future threshold approval can be proposed.
2. The dual gate is preserved, but future threshold proposals must first prove the active-days floor is geometrically reachable across both governed windows.
3. Impossible geometry is classified as governance `Hold` before execution is ever authorized.
4. Future approval evidence is limited to docs-only reachability memo + explicit acceptance matrix until a separate governance step says otherwise.

---

## Locked Formulas and Binding Rules

### Core Definitions
- `active_days_window = count(governed trading days in the window where the method is in a valid investable state)`
- `eligible_days_window = count(governed trading days available inside the governed window)`
- `coverage_ratio_window = active_days_window / eligible_days_window`

### Reachability Precheck
- `threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)`

### Preserved Dual Gate Family
- `dual_gate_window_pass = (active_days_window >= MIN_ACTIVE_DAYS_THRESHOLD) and (coverage_ratio_window >= MIN_COVERAGE_RATIO_THRESHOLD)`

### Future Authorization Rule
- `future_gate_proposal_allowed = threshold_reachable`
- `future_execution_authorized = threshold_reachable and explicit_future_governance_instruction`

### Binding Interpretation
- If `threshold_reachable = false`, the policy disposition is governance `Hold` before any threshold lock, worker guide, or execution proposal can advance.
- If `threshold_reachable = true`, governance may review a future proposal that keeps the same dual-gate family, but execution still remains blocked until a separate explicit instruction is issued in-thread.
- Impossible geometry is a policy/window-design issue, not a method-quality failure and not a reason to mutate frozen Phase 37/38 evidence.

---

## Approval-Readiness Acceptance Matrix

A future Phase 39 proposal is not approval-ready unless all of the following are true:

1. `docs/phase_brief/phase39-brief.md` contains the locked reachability formulas and blocking rules.
2. `docs/notes.md` mirrors the formulas and governance interpretation verbatim.
3. `docs/context/current_context.json` and `docs/context/current_context.md` reflect the pre-execution reachability screen and dormant state.
4. `docs/decision log.md` records the dormant Phase 39 charter with explicit no-rerun / no-rewrite / no-execution clauses.
5. `docs/lessonss.md` records the new guardrail requiring a separate next-phase dormant charter record.
6. `docs/saw_reports/saw_phase39_reachability_policy_20260309.md` is published and validator-clean.
7. No Phase 39 execution token exists anywhere in the packet.

---

## Explicitly Out of Scope (Hard Block)

- Threshold rewrites (`252 / 0.80` remains unchanged in this phase)
- Any rerun or recompute of Phase 37 or Phase 38 outputs
- Any mutation of frozen Phase 37 or Phase 38 evidence packets
- Portfolio method rewrites or sleeve-set changes
- Production promotion, deployment, or live-capital actions
- Vendor bypass (S&P IQ / BvD remains asynchronous)
- Runtime-key migration away from `permno`
- Governed cost-model rewrite
- Code scaffolding, script creation, test execution, or artifact generation
- Any execution activity before future explicit governance approval

---

## Approval Boundary

This brief does **not** authorize execution.

Any future Phase 39 execution requires:
- `threshold_reachable = true` under the locked precheck
- Explicit future governance instruction issued in-thread
- A separate execution contract document
- Clear confirmation that out-of-scope hard blocks remain intact

---

## Immediate Next Milestone

Keep the Phase 39 planning packet sealed and dormant.

Any future proposal must first pass the reachability precheck and then receive explicit governance direction before any execution surface can be opened.

---

## New Context Packet (Phase 39)

### What Was Done
- Locked the fail-closed Phase 39 reachability policy as a docs-only planning packet.
- Preserved frozen Phase 37 and Phase 38 evidence without rerun, recompute, or mutation.
- Classified impossible geometry as governance `Hold` before any future execution authorization.

### What Is Locked
- `252 / 0.80` thresholds remain unchanged.
- `threshold_reachable = MIN_ACTIVE_DAYS_THRESHOLD <= min(eligible_days_validation, eligible_days_holdout)` is required before any future threshold approval.
- Frozen Phase 37 and Phase 38 packets remain immutable.
- Comparator/runtime-key/cost/quarantine contracts remain unchanged.
- No Phase 39 execution token exists in this packet.

### What Is Next
- Maintain the sealed docs-only Phase 39 policy packet.
- Require any future proposal to prove reachability before asking for a new threshold or gate round.
- Keep all execution paths blocked until future explicit governance approval.

### First Command
```text
Get-Content docs/phase_brief/phase39-brief.md
```

### Next Todos
- Keep the reachability precheck explicit in all Phase 39 follow-up docs.
- Preserve frozen Phase 37 and Phase 38 evidence with no reruns or recomputation.
- Keep research quarantine and all hard blocks unchanged.


