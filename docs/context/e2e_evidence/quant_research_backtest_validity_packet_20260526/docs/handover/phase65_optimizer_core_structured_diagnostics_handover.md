# Phase 65 Optimizer Core Structured Diagnostics Handover

RoundID: `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_20260510`
ScopeID: `OPTIMIZER_DIAGNOSTICS_ONLY`
Date: 2026-05-11
Audience: PM / Planner

## Executive Summary

The optimizer diagnostics-only implementation is complete and SAW PASS. The round adds structured feasibility, solver, bound, constraint, severity, and fallback diagnostics without adding a new optimizer objective or approving lower-bound investment policy.

## Delivered Scope vs Deferred Scope

Delivered:

- pre-solver feasibility checks for zero assets, infeasible max caps, infeasible minimum diagnostics, required-minimum sums, out-of-range bounds, and fully invested impossibility;
- equal-weight boundary warning when max weight sits at the minimum feasible cap;
- post-solver active lower/upper bound counts and labels;
- cash and full-investment residual diagnostics;
- SLSQP status/message reporting;
- explicit equal-weight fallback labels that state fallback is not optimized;
- Portfolio & Allocation UI status rows for optimizer diagnostics.

Deferred:

- MU conviction policy;
- WATCH investability expansion;
- Black-Litterman;
- simple tilt / conviction optimizer;
- new optimizer objective;
- scanner rules;
- manual override;
- provider ingestion, alerts, broker behavior, or replay behavior.

## Derivation and Formula Register

```text
upper_bound_feasible = n_assets > 0 and max_weight * n_assets >= 1.0
min_feasible_max_weight = 1 / n_assets
equal_weight_forced = upper_bound_feasible and max_weight <= min_feasible_max_weight + tolerance
lower_sum_feasible = min_weight * n_assets <= 1.0
required_min_sum_feasible = sum(required_min_weights) <= 1.0
active_lower_i = weight_i <= lower_bound + tolerance
active_upper_i = weight_i >= max_weight - tolerance
cash_residual = 1 - sum(weights)
full_investment_constraint_residual = sum(weights) - 1
fallback_valid = fallback_used and result_is_optimized == false and fallback_reason is visible
non_finite_weight_valid = false
non_finite_weight_result = ERROR and constraints_satisfied == false and result_is_optimized == false
```

Source paths:

- `strategies/optimizer_diagnostics.py`
- `strategies/optimizer.py`
- `views/optimizer_view.py`
- `tests/test_optimizer_core_policy.py`

## Logic Chain

```text
Optimizer inputs -> feasibility report -> approved objective path -> solver status -> final weight diagnostics -> UI-safe explanation
```

## Evidence Matrix

| Check | Result | Evidence |
| --- | --- | --- |
| Focused optimizer diagnostics tests | PASS | `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> 16 passed |
| Portfolio/DASH regression | PASS | `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py -q` -> 33 passed |
| Scoped compile | PASS | `.venv\Scripts\python -m py_compile strategies\optimizer.py strategies\optimizer_diagnostics.py views\optimizer_view.py dashboard.py` |
| Context validation | PASS | `.venv\Scripts\python scripts\build_context_packet.py --validate` |
| Browser smoke | PASS | `http://localhost:8505/portfolio-and-allocation` |
| Full pytest | PASS | `.venv\Scripts\python -m pytest -q` |

## Open Risks / Assumptions / Rollback

Open risks:

- inherited yfinance display refresh and YTD equal-weight fallback remain carried as prior DASH-2 behavior;
- thesis-anchor policy remains future planning and must not be smuggled into diagnostics.

Assumptions:

- equal-weight fallback is allowed only when it is explicitly labeled as fallback and not optimized;
- lower-bound feasibility diagnostics are explanation primitives only, not a public lower-bound allocation policy.

Rollback:

- revert `strategies/optimizer_diagnostics.py`, diagnostics method additions in `strategies/optimizer.py`, optimizer diagnostics UI in `views/optimizer_view.py`, and optimizer diagnostics tests/docs from this round.

## Next Phase Roadmap

- diagnostics closure is PASS;
- either hold or plan `PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING`;
- thesis-anchor planning must answer evidence requirements, max weight, WATCH eligibility, and whether any future conviction method is simple tilt or Black-Litterman.

## New Context Packet

## What Was Done

- Implemented the Dashboard Architecture Safety Slice.
- Added `utils/process.py::pid_is_running` and routed Windows-reachable runtime PID probes through it.
- Removed dashboard backtest spawn's unverified PID-file-owner termination path; live PID files now fail closed.
- Collapsed dashboard strategy-matrix initialization into one helper path.
- Delegated dashboard portfolio price cleanup to `core.data_orchestrator.clean_price_frame`.
- Implemented Dashboard Scanner Testability Hardening.
- Added `strategies/scanner.py` for deterministic scanner macro, breadth, technical, entry, tactic, proxy, rating, and leverage math.
- Updated `dashboard.py` to preserve provider/cache/payload ownership while delegating scanner enrichment to `strategies.scanner.enrich_scan_frame`.
- Added scanner boundary tests plus direct `AdaptiveTrendStrategy`, `ProductionConfig`, `core.etl`, and InvestorCockpit quality-cap coverage.
- Refreshed `tests/pytest_out.txt` from the stale two-test artifact to the current full-suite PASS summary.
- Preserved D-353 provenance gates and R64.1 dependency hygiene as closed baseline truth.
- Implemented optimizer structured diagnostics as a diagnostics-only round.
- Added `strategies/optimizer_diagnostics.py` with feasibility, bound, constraint, solver, severity, and fallback report objects.
- Updated `strategies/optimizer.py` with diagnostic-returning optimizer methods while preserving existing weight-returning methods.
- Updated `views/optimizer_view.py` to show optimization status, feasibility status, active constraints, assets at max cap, assets at lower bound, equal-weight-forced status, residuals, and fallback labels.
- Converted optimizer audit strict xfail debt into passing diagnostics tests.
- Reconciled SAW data-integrity review by making non-finite diagnostic weights fail closed as errors.
- Published SAW PASS for `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_20260510`.

## What Is Locked

- Direct runtime `os.kill(pid, 0)` PID liveness probes remain blocked outside `utils/process.py`.
- Dashboard backtest spawn must not terminate unverified PID-file owners.
- Dashboard architecture safety changes do not authorize provider ingestion, canonical writes, strategy search, ranking, scoring, alerts, brokers, or dashboard redesign.
- Scanner extraction is behavior-preserving testability work; it does not authorize scanner semantic changes, provider ingestion, canonical writes, ranking/scoring policy changes, alerts, brokers, dashboard redesign, or candidate-card dashboard integration.
- Scanner formula changes must land in `strategies/scanner.py` with `tests/test_scanner.py` boundary coverage.
- The quarantined lower-bound/SLSQP diff remains rejected as-is.
- The approved optimizer objective remains unchanged.
- Lower-bound feasibility diagnostics do not approve lower-bound allocation policy.
- MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new objectives, scanner rules, manual overrides, providers, alerts, brokers, and replay behavior remain blocked.

## What Is Next

- Continue review or hold.
- Diagnostics closure is PASS; either hold or plan `PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING`.
- Do not approve conviction, Black-Litterman, MU policy, or WATCH investability without a separate planning round.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_scanner.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\test_process_utils.py -q
```

## Next Todos

- Hold or approve a separate thesis-anchor planning round.
- Full pytest passed for the scanner hardening addendum; keep using focused tests for formula changes and full pytest for closure claims.
- Keep inherited yfinance display refresh and YTD equal-weight fallback visible as future policy/hygiene items.
