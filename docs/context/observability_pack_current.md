# Observability Pack — Current

Date: 2026-08-06
Gate: `FIRST REAL AOV-0 FIVE-ARM PROSPECTIVE SEAL`
Status: `ACTIVE`

## Product / custody sentinels

- Sole current root product path: `launch.py` → `dashboard.py`.
- Root duplicate app count must remain `0`.
- Published `9af5259` remains untouched.
- Episode-2 local candidate is `39f7be3`; exact selected result is `115/115 PASS`.
- `142/142` is stale and must not be reported as current evidence.
- AOV local executable lineage before docs closure ends at `dca69fc`.
- Portfolio-alpha evidence remains `0`; Limited Live remains closed.

## ZERO-COMPAT sentinels

All six outputs from `scripts/aov_zero_compat_scan.py` must remain zero:

- root duplicate apps;
- AOV ticker/asset aliases;
- legacy book projection;
- transitional authority fallback;
- mutable evidence-manifest bypass;
- unnamed benchmark selection.

Any nonzero value blocks advancement.

## AOV authority sentinels

- Permanent identity = `permno`.
- PIT total-return matrix is sole P&L authority.
- Parent preserves Rule100 budget/cap/schedule/cash semantics.
- Child may reduce risk only.
- Economic cash = official SOFR minus 25 bp, ACT/360, post-publication only, no proxy substitution.
- Production insurance materiality floor and annual premium ceiling remain owner-open.
- Real seal/review classification must refuse unresolved owner insurance values.
- Evidence manifests bind actual component bytes and cannot overwrite an existing run identity.
- Mandatory benchmarks are named; PIT-EW follows the strategy decision schedule.

## First-seal sentinels

The real seal requires the owner insurance values plus all five admitted current AOV artifacts. Historical equal-weight, ticker-based, synthetic, zero-return-cash, or other substitutes are invalid.

Before admission, the expected command state is:

```text
status = BLOCKED_OWNER_DECISION_AND_ADMITTED_INPUTS
prospective_clock_started = false
alpha_evidence = 0
```

## Review sentinels

- Accounting residual outside tolerance blocks review authority.
- Single-episode review has no structural mutation authority.
- Test-fixture experiment/seal/review output is mechanical evidence only, not A1/A3.
- Full score→target→executed-weight→P&L lineage remains an explicit next review deliverable.

## Stop signals

Stop on compatibility reintroduction, mutable evidence identity, unnamed benchmarks, non-finite cost acceptance, unadmitted current data, invented owner insurance values, substituted official cash source, early outcome opening, or alpha/live claims before mature replicated evidence.
