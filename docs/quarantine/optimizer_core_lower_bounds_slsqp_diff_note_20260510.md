# Optimizer Core Lower-Bounds / SLSQP Diff Quarantine

Date: 2026-05-10

This diff was discovered during `PORTFOLIO_UNIVERSE_CONSTRUCTION_FIX`.

It affects optimizer-core lower-bound / SLSQP handling.

It is out of scope for the universe-construction closure.

It is preserved for a separate optimizer policy audit.

## Quarantined Artifact

- `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`

## Boundary

Do not accept this diff into the universe-construction closure.

Do not use this quarantine as approval for lower-bound policy, SLSQP fallback behavior, MU conviction mode, WATCH investability, Black-Litterman, scanner behavior, or universe eligibility changes.
