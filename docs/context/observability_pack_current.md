# Observability Pack — Current

Date: 2026-08-07
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

All seven outputs from `scripts/aov_zero_compat_scan.py` must remain zero:

- root duplicate apps;
- AOV ticker/asset aliases;
- legacy book projection;
- transitional authority fallback;
- mutable evidence-manifest bypass;
- unnamed benchmark selection;
- archived/release executable-source imports outside the explicit historical receipt-integrity test.

Any nonzero value blocks advancement.

## AOV authority sentinels

- Permanent active AOV identity = `CIQSEC:<Capital IQ Security ID>`; ticker, company `SP_ENTITY_ID`, legacy PERMNO, and dual-provider aliases must fail closed.
- S&P Capital IQ Pro primary-security total-return matrix is sole risky-asset P&L authority.
- Parent preserves Rule100 budget/cap/schedule/cash semantics.
- Child may reduce risk only.
- Economic cash = official SOFR minus 25 bp, ACT/360, post-publication only, no proxy substitution.
- Production insurance V0 is frozen at materiality `0.05` and annual premium ceiling `0.0015`; changing either creates a new contract/model family.
- Real seal/review classification must use those exact frozen V0 values; no result-driven calibration in place.
- Evidence manifests bind actual component bytes and cannot overwrite an existing run identity.
- Mandatory benchmarks are named; PIT-EW follows the strategy decision schedule.

## First-seal sentinels

The real seal requires five admitted current AOV artifacts, but direct `official_sofr.parquet` is already present; four current files remain. The risky-asset source family is S&P Capital IQ Pro rather than CRSP. Historical equal-weight, ticker/company-entity/PERMNO aliases, synthetic inputs, zero-return cash, WRDS-mirrored SOFR, or mixed-provider substitutes are invalid. `aov0_ciq_decision_cut_v2` must bind the exact four Parquet SHA-256 values, frozen CIQ contract hash, mechanically recomputed date-local CIQ-security universe hash, and four required source receipts/retrieval times for `SPCIQPRO:QUARTERLY_FUNDAMENTALS`, `SPCIQPRO:PRIMARY_SECURITY_MASTER`, `SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA`, and NY Fed SOFR, plus `knowledge_cutoff`, `cut_built_at`, target date, frozen `NYSE_2026_CORE_OPEN_0930_ET` calendar identity, and exact first eligible execution bar. The entrypoint re-hashes before and after experiment execution; the prospective v2 seal independently stamps actual `sealed_at`, binds `aov0_executable_byte_manifest_v1` plus five target hashes/vectors, and must be reopened by a fresh Python process that verifies the complete executable/seal/cut/Parquet/experiment/evidence/target chain. The single hash-bound `run_4.xlsx` receipt owns both the frozen 109-company universe and current-cut fundamentals; `run_2.xlsx` is historical evidence only.

Before admission, the expected command state is:

```text
status = BLOCKED_MISSING_ADMITTED_INPUTS
prospective_clock_started = false
financial_alpha_evidence = 0
```

## Review sentinels

- Accounting residual outside tolerance blocks review authority.
- Single-episode review has no structural mutation authority.
- Test-fixture experiment/seal/review output is mechanical evidence only, not A1/A3.
- Full score→target→executed-weight→P&L lineage remains an explicit next review deliverable.

## Stop signals

Stop on compatibility reintroduction, mutable evidence identity, unnamed benchmarks, non-finite cost acceptance, unadmitted current data, in-place insurance-V0 changes, substituted official cash source, early outcome opening, or alpha/live claims before mature replicated evidence.
