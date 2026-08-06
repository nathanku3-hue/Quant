# Impact Packet — Current

Date: 2026-08-06
Gate: `FIRST REAL AOV-0 FIVE-ARM PROSPECTIVE SEAL`
Status: `HARD CUT + MECHANICAL VERTICAL IMPLEMENTED LOCALLY; REAL SEAL BLOCKED`

## Executable impact

Local commits created:

- `39f7be3894623c095994066b8f0ea2895b968643` — immutable Episode-2 executable/data/test candidate;
- `4b14846015c952242d4bf17819bc615435bda091` — destructive compatibility hard cut + AOV mechanical vertical;
- `dca69fc72dd3192913aa921323ff48f68610a925` — production insurance owner-decision boundary restored.

No push/hosted CI/main/tag/publication occurred.

## Hard-cut impact

Removed from current root authority:

- `alpha_app.py`;
- `launch_alpha.py`;
- `portfolio_app.py`;
- `launch_portfolio.py`;
- live root Alpha release build/smoke scripts;
- compatibility-only AppTests;
- legacy book projection;
- legacy/transitional dashboard authority.

Historical source was retained under `docs/archive/legacy_runtime_source/`; Alpha release truth is receipt integrity under `release/gv-alpha0/RECEIPT.json`.

## AOV/research impact

Touched authoritative executable interfaces:

- `dashboard.py`, `views/page_registry.py`;
- `gv_portfolio_v0/book.py`;
- `research/backtest_runner.py`, `benchmarks.py`, `strategy_cartridge.py`, `evidence_schema.py`;
- `research/adapters/rule100_replay_adapter.py`;
- new `research/aov0/*`;
- `scripts/aov_zero_compat_scan.py`;
- `scripts/aov0_first_seal.py`;
- AOV/research/product regression tests;
- future local/hosted workflow definitions.

Research behavior changed incompatibly by design: permanent IDs only, named benchmarks only, finite costs only, immutable evidence manifests, schedule-consistent PIT equal weight, no cash inconsistency tolerance.

## Current blocker impact

No current market/provider output was generated. The real prospective seal is blocked by:

- owner insurance materiality floor + annual premium ceiling;
- five admitted current AOV input files.

Provider access was explicitly outside authorization, so missing data was not fetched or approximated.

## Validation impact

- E2 exact `39f7be3`: `115/115 PASS` from archived commit bytes.
- AOV: `17/17 PASS`.
- Hardened research: `33/33 PASS`.
- Current dashboard/book/historical receipt: `33/33 PASS`.
- Hard-cut E2 regression: `107/107 PASS`.
- Historical Alpha runtime live checkout: `7/7 PASS`.
- ZERO-COMPAT: all six counters zero.
- Compile/YAML/`pip check`/whitespace: PASS.

## Claim boundary

Canonical maturity remains `70/100`; portfolio-alpha evidence remains `0`; no real A1/A3, provider, broker, or live claim.
