# Optimizer Lower-Bound / SLSQP Policy

Date: 2026-05-10
Status: Lower-bound policy still held; structured diagnostics approved separately on 2026-05-11

## Structured Diagnostics Addendum

The 2026-05-11 implementation round adds lower-bound feasibility diagnostics and lower-bound-active reporting as explanation primitives only. It does not approve a public lower-bound optimizer policy, MU floor, thesis anchor, or conviction mode.

The runtime optimizer remains approved for:

```text
0.0 <= weight_i <= max_weight
sum(weights) == 1.0
```

SLSQP bound multipliers are still not treated as available explanation data. Active bounds are diagnosed directly from final weights and tolerances in `strategies/optimizer_diagnostics.py`.

## Decision

Lower bounds are not currently approved for runtime portfolio optimization.

The dirty `strategies/optimizer.py` lower-bound/SLSQP diff is preserved in:

```text
docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch
```

It must not be merged until a separate optimizer-core policy round approves the behavior and ships implementation, tests, docs, and SAW together.

## Why This Is Optimizer-Core Math

SciPy `minimize` treats `bounds` and `constraints` as part of the optimization problem definition. SLSQP specifically handles bounds plus equality and inequality constraints for constrained minimization. Changing lower bounds therefore changes the feasible set and can change the optimal portfolio.

SciPy SLSQP returns KKT multipliers for equality and inequality constraints, but not for bound inequalities. If the UI needs to explain bound-active behavior, Terminal Zero must diagnose active bounds itself.

## Current Policy Answers

What lower bounds currently exist?

- None are approved in the public optimizer API.

Are lower bounds user-facing, policy-facing, or implementation fallback?

- Not user-facing.
- Not policy-facing.
- Not approved as fallback.

Does SLSQP receive bounds and constraints consistently?

- Current baseline passes long-only upper bounds `(0.0, max_weight)` and a full-investment equality constraint.
- Lower-bound support is not accepted.

Are min weights allowed at all?

- No, not until policy approval.

Can lower bounds make the problem infeasible?

- Yes. `sum(lower_i) > 1.0`, any `lower_i > max_weight`, or insufficient remaining capacity makes the problem infeasible.

Does the optimizer detect infeasibility before SLSQP?

- Upper-bound cardinality is checked by `_is_feasible`.
- Lower-bound infeasibility is not applicable because lower bounds are not accepted.
- Current fallback status reporting remains insufficient and is tracked as audit debt.

Are constraint failures reported clearly?

- Not sufficiently. Future implementation must return or surface structured diagnostics.

Can optimizer output silently violate policy?

- It must not. Current audit tests mark silent fallback behavior as policy debt until implementation is approved.

Are bound-active cases explained to the UI?

- Upper-bound boundary pressure is partially explained by portfolio-universe diagnostics.
- Optimizer-core active-bound reporting is not yet implemented.
- Lower-bound-active reporting: not available until accepted and implemented in a separate optimizer-core round.

## Acceptance Gate For Future Patch

A future lower-bound/SLSQP patch may be accepted only when:

- it has its own branch;
- it updates this policy and `docs/architecture/optimizer_constraints_policy.md`;
- it adds infeasibility tests;
- it explains lower-bound and upper-bound behavior;
- it reports active bounds without relying on SLSQP bound multipliers;
- it does not introduce MU conviction, WATCH investability, Black-Litterman, universe eligibility changes, scanner behavior changes, provider ingestion, alerts, broker behavior, or new objectives.

## Sources

- SciPy `minimize` API: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
- SciPy SLSQP notes: https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html
