# Optimizer Core Policy Audit

RoundID: `OPTIMIZER_CORE_POLICY_AUDIT_20260510`
ScopeID: `OPTIMIZER_LOWER_BOUNDS_SLSQP_POLICY_ONLY`
Date: 2026-05-10
Status: Audit PASS; structured diagnostics implementation approved separately on 2026-05-11

## Structured Diagnostics Implementation Addendum

RoundID: `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_20260510`
ScopeID: `OPTIMIZER_DIAGNOSTICS_ONLY`
Date: 2026-05-11
Status: Implementation approved for diagnostics only

The approved follow-up implementation adds structured diagnostics without accepting the quarantined lower-bound/SLSQP diff as-is and without changing the optimizer objective.

Implemented surfaces:

- `strategies/optimizer_diagnostics.py` owns diagnostic report objects and formulas.
- `strategies/optimizer.py` exposes diagnostic-returning optimizer methods and labels fallback allocations.
- `views/optimizer_view.py` renders UI-safe optimizer status, feasibility, active-bound, residual, and fallback explanations.
- `tests/test_optimizer_core_policy.py` converts the prior strict xfail debt into passing implementation checks.

Still not approved:

- MU conviction policy;
- WATCH investability expansion;
- Black-Litterman;
- simple tilt or conviction optimizer;
- new objective;
- scanner rules;
- manual override;
- provider, alert, broker, or replay behavior.

## Mission

Audit whether the quarantined `strategies/optimizer.py` lower-bound/SLSQP handling should be accepted, revised, or rejected as a separate optimizer-policy change.

## Audit Verdict

Reject accepting the quarantined diff as-is.

The lower-bound/SLSQP diff is not accepted.

Preferred disposition: revise under a future implementation round only after policy acceptance. The diff changes optimizer-core feasible-set math, fallback behavior, and SLSQP bound handling. It needs explicit infeasibility diagnostics and active-bound reporting before it can be considered safe.

## Scope

Included:

- policy docs;
- tests that lock current non-approval and mark known optimizer-core debt;
- quarantine traceability;
- SAW audit report.

Excluded:

- optimizer implementation changes;
- MU hard floor;
- conviction mode;
- WATCH investability;
- Black-Litterman;
- scanner rewrite;
- universe eligibility change;
- provider ingestion, broker calls, or alerts.

## Audit Questions

| Question | Finding |
| --- | --- |
| What lower bounds currently exist? | None are approved in the optimizer public API. |
| Are lower bounds user-facing, policy-facing, or implementation fallback? | None of the above. They are held until separate approval. |
| Does SLSQP receive bounds and constraints consistently? | Baseline sends `(0.0, max_weight)` bounds and `sum(weights) == 1.0`; lower-bound support is not accepted. |
| Are min weights allowed at all? | No. |
| Can lower bounds make the problem infeasible? | Yes; lower-bound sum, per-asset lower > upper, and remaining-capacity checks are required. |
| Does the optimizer detect infeasibility before SLSQP? | Partially for upper bounds; lower bounds are unsupported; fallback status reporting is still weak. |
| Are constraint failures reported clearly? | No. Future patch must surface structured diagnostics. |
| Can optimizer output silently violate policy? | It must not; tests mark current silent-fallback behavior as policy debt. |
| Are bound-active cases explained to the UI? | Partially for max-weight boundary pressure; optimizer-core active-bound reporting is not implemented. |

## Source-Based Rationale

SciPy `minimize` exposes `bounds` and `constraints` as solver inputs, so changing bound construction changes the optimization problem. SLSQP is the constrained minimization path used for combinations of bounds and equality/inequality constraints. SciPy also documents that SLSQP result multipliers do not include bound inequalities; Terminal Zero must detect active bounds directly when the UI needs to explain them.

The Federal Reserve SR 26-2 letter emphasizes risk-based model risk management principles and updates legacy SR 11-7 guidance. Terminal Zero is not a bank model-governance program, but the separation principle applies: optimizer-model behavior changes should have distinct development, validation, and governance artifacts rather than being bundled into a universe-construction patch.

## Required Future Implementation Evidence

- `test_optimizer_rejects_infeasible_lower_bounds`
- `test_optimizer_rejects_infeasible_upper_bounds`
- `test_optimizer_detects_min_weight_sum_exceeds_one`
- `test_optimizer_detects_max_weight_sum_below_one`
- `test_optimizer_reports_active_lower_bound`
- `test_optimizer_reports_active_upper_bound`
- `test_optimizer_does_not_silently_fallback_to_equal_weight`
- `test_optimizer_slsqp_failure_is_reported`
- `test_optimizer_policy_change_not_allowed_without_contract_update`

Current test file:

- `tests/test_optimizer_core_policy.py`

## Decision

Do not merge `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch` as-is.

Next action:

```text
hold_optimizer_core_implementation_until_policy_approval
```

## Sources

- SciPy `minimize`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
- SciPy SLSQP: https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html
- Federal Reserve SR 26-2: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
