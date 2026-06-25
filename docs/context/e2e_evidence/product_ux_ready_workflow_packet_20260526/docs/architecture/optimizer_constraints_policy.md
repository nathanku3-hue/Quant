# Optimizer Constraints Policy

Date: 2026-05-10
Status: Structured diagnostics approved on 2026-05-11; optimizer objective and lower-bound policy unchanged

## Structured Diagnostics Addendum

The optimizer now reports structured diagnostics for the currently approved long-only, fully invested, upper-bound-constrained policy. This is a reporting and fail-visibility layer, not a new allocation objective and not an approval of lower-bound investment policy.

Diagnostic ownership:

- `strategies/optimizer_diagnostics.py`: feasibility, bound, constraint, solver, fallback, and severity objects.
- `strategies/optimizer.py`: diagnostic-returning optimization methods and explicit fallback labels.
- `views/optimizer_view.py`: UI-safe status rows for feasibility, active constraints, assets at caps/floors, equal-weight boundary pressure, and fallback status.

Diagnostic formulas:

```text
upper_bound_feasible = n_assets > 0 and max_weight * n_assets >= 1.0
min_feasible_max_weight = 1 / n_assets
equal_weight_forced = upper_bound_feasible and max_weight <= min_feasible_max_weight + tolerance
active_lower_i = weight_i <= lower_bound + tolerance
active_upper_i = weight_i >= max_weight - tolerance
cash_residual = 1 - sum(weights)
full_investment_constraint_residual = sum(weights) - 1
```

Fallback rule:

```text
fallback allocation may be shown only when fallback_used = true,
fallback_reason is visible, and result_is_optimized = false.
```

## Current Approved Constraints

The current `PortfolioOptimizer` contract is long-only, fully invested, and upper-bound constrained:

- `sum(weights) == 1.0`
- `0.0 <= weight_i <= max_weight`
- no user-facing minimum-weight or lower-bound policy is approved
- no MU hard floor, WATCH investability promotion, conviction mode, Black-Litterman mode, manual override, scanner rewrite, or new objective is approved

Current implementation owner:

- `strategies/optimizer.py`

Current UI/diagnostic owners:

- `strategies/portfolio_universe.py`
- `views/optimizer_view.py`
- `dashboard.py`

## Infeasibility Policy

An optimizer constraint set is infeasible when there is no vector that can satisfy the full-investment and per-asset bound rules at the same time.

Upper-bound feasibility formula:

```text
upper_bound_feasible = n_assets > 0 and max_weight > 0 and max_weight * n_assets >= 1.0
```

Future lower-bound feasibility formula, if lower bounds are ever approved:

```text
lower_bounds_valid = all(lower_i >= 0)
lower_sum_feasible = sum(lower_i) <= 1.0
per_asset_feasible = all(lower_i <= max_weight)
remaining_capacity_feasible = sum(max_weight - lower_i) >= 1.0 - sum(lower_i)
```

## Required Behavior

Future optimizer-core changes must:

1. reject infeasible lower-bound and upper-bound configurations before SLSQP;
2. avoid silently returning equal weight when that fallback violates configured bounds;
3. expose SLSQP failure as a diagnostic status, not as a hidden success;
4. report active upper-bound and lower-bound constraints when a policy requires explanations;
5. update `docs/architecture/optimizer_lower_bound_slsqp_policy.md` and tests in the same round.

## Current Audit Finding

The quarantined diff attempts to introduce lower-bound handling and changes SLSQP bounds/fallback paths. It is not accepted by the Portfolio Universe Construction Fix.

Current baseline has known policy gaps around explicit failure reporting. Those gaps are audit findings, not approval for the quarantined diff.

## Sources

- SciPy `minimize` API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
- SciPy SLSQP notes: https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html
- Federal Reserve SR 26-2 model-risk guidance: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
