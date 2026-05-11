# Portfolio Construction Contract

Date: 2026-05-10

## Approved Scope

This contract governs the approved portfolio universe construction fix:

1. Separate optimizer universe construction from dashboard display order.
2. Exclude `EXIT`, `KILL`, `AVOID`, and `IGNORE` states from the optimizer by default.
3. Treat generic `WATCH` as research-only by default.
4. Report ticker-map and local price-history readiness failures before optimization.
5. Diagnose max-weight feasibility before allocation.

## Held Scope

The following are not approved in this patch:

- MU hard floor or `MU >= 20%` policy.
- Endgame, conviction, Black-Litterman, or thesis-anchor optimizer mode.
- MU expected-return tilt or thesis confidence parameter.
- Manual override for excluded names.
- Sovereign / Alpha Quad scanner rewrite.
- New portfolio objective or new allocation math.

## Ownership Boundary

Scanner output finds opportunities and danger states.

Dashboard display shows scanner state to the operator.

Portfolio universe construction decides which scanner rows are eligible for capital allocation.

Portfolio optimizer allocates only across the audited eligible universe.

Risk and future thesis policy must approve any conviction-aware sizing before it can affect allocation.

## Runtime Pipeline

```text
scanner output
-> explicit optimizer universe builder
-> eligibility filter
-> ticker-map readiness check
-> local price-history readiness check
-> optimizer candidate universe
-> thesis-neutral optimizer
-> allocation explanation
```

Forbidden pipeline:

```text
df_scan display sort
-> selected_tickers[:20]
-> optimizer
```

## Eligibility Policy

Default eligible ratings:

- `ENTER STRONG BUY`
- `ENTER BUY`

Default research-only ratings:

- `WATCH`

Default excluded ratings/actions:

- `EXIT`
- `KILL`
- `AVOID`
- `IGNORE`

Generic `WATCH` is not investable until a later product policy defines an approved portfolio-ready watch state.

## Readiness Checks

Each scanner ticker is audited for:

- policy status: included, research-only, excluded, missing mapping, or insufficient history;
- resolved local `permno`;
- local ticker-map presence;
- local price-history observation count.

Rows with missing local map or insufficient local price history are not passed to the optimizer.

## Max-Weight Feasibility

Formula:

```text
min_feasible_max_weight = 1 / n_assets
is_feasible = max_weight * n_assets >= 1
is_boundary_forced = is_feasible and max_weight <= min_feasible_max_weight + tolerance
```

If `is_feasible` is false, the optimizer must fail closed.

If `is_boundary_forced` is true, the UI must warn that allocation freedom is effectively zero and the result is forced toward equal weight.

## Thesis-Neutral Boundary

The current optimizer is thesis-neutral.

It uses historical prices, expected returns, covariance, inverse volatility, and configured constraints. It does not know MU conviction, memory supercycle status, GodView state, or endgame portfolio preference.

Future mode note:

- Possible future mode: `Endgame / Conviction Optimizer`.
- Possible implementation: Black-Litterman or governed tilt model.
- Required first: thesis-anchor policy, confidence labels, allowed tilt ranges, risk budgets, and compare-against-thesis-neutral evidence.

No conviction tilt is approved by this contract.
