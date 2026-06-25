# V2 PEAD D3 Benchmark Input Contract

Mode: `ADVISORY_REVIEW`
Status: Benchmark-input design gate DONE; implementation held
Date: 2026-06-19
RoundID: `ROUND-20260619-V2-D3-BENCHMARK-INPUT-DESIGN-GATE`
ScopeID: `V2_D3_BENCHMARK_INPUT_CONTRACT_ONLY`
Owner: Data + Docs/Ops

## Objective and boundary

Define the benchmark-input contract required before any PEAD CAR/BHAR or quintile interpretation can run against the D2B fixed-security event windows.

This gate is docs-only. It does not fetch providers, write benchmark Parquet, alter D1/D2A/D2B artifacts, modify `strategies/pead_event_study.py`, run real CAR/quintile interpretation, change dashboard surfaces, rank or score candidates, stage files, or commit.

## Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

What is done: the benchmark source, formula, units, session alignment, missingness, manifest, terminology, and acceptance-test contract are fixed for a future D3 implementation.

What is blocked: provider download, immutable benchmark publication, CAR/BHAR production, real PEAD interpretation, delisting adjustment, dashboard, ranking, alerts, broker/order paths, full build, staging, and commit.

User order interpreted as: run only `V2-D3-BENCHMARK-INPUT-DESIGN-GATE`.

Recommended next step: implement a bounded D3 benchmark artifact builder in a separate approved round.

Why this is correct: the current local factor artifact is insufficient for D2B coverage, and CAR semantics require an explicit benchmark column before strategy output can be interpreted.

Alternatives considered: use existing `ff_factors.parquet` as-is; rejected because it covers only 2022-01-03 through 2025-12-31. Use `mktrf` alone; rejected because it is excess market return, not total market return. Fill missing benchmark dates; rejected because it would silently change event-window evidence.

Decision needed from user: approve / redirect / hold before implementation.

Scope limit: one docs/design gate; no code, provider, data artifact, strategy, dashboard, staging, or commit work.

Stop rule: stop implementation unless source coverage, units, hashes, date alignment, missing-date handling, and 60-observation enforcement can be proven without data splicing or imputation.

## Source and methodology contract

- Canonical benchmark: Kenneth R. French Data Library `Fama/French 3 Factors [Daily]`.
- Source citation: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html`.
- Methodology citation: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html`.
- Source fields required: `date`, `mktrf`, `rf`.
- Optional pass-through fields: `smb`, `hml`, `rmw`, `cma`, `umd`, source-specific release metadata.
- Source units: Ken French factor files are percent returns. The canonical artifact must store decimal returns.
- Required conversion: `mktrf_decimal = mktrf_percent / 100`; `rf_decimal = rf_percent / 100`.
- Canonical formula: `benchmark_return = mktrf_decimal + rf_decimal`.
- Forbidden formula: `benchmark_return = mktrf_decimal` alone.
- Methodology boundary: this benchmark is the Fama/French market return implied by `Rm-Rf + Rf`. It is not a local CRSP total-return index, not `^GSPC`, and not a regression alpha model.
- Source-regime boundary: the source has documented CRSP data/process changes over time. Future implementation must cite the exact source release and must not splice source regimes silently.

## Schema and unit contract

Required canonical columns:

| Column | Type | Unit | Rule |
|---|---|---|---|
| `return_date` | date | date-only | Unique, normalized trading date |
| `mktrf` | float | decimal return | Parsed from source percent return divided by 100 |
| `rf` | float | decimal return | Parsed from source percent return divided by 100 |
| `benchmark_return` | float | decimal return | `mktrf + rf` after conversion |
| `source_name` | string | label | `ken_french_fama_french_3_factors_daily` |
| `source_release` | string | label | Exact source release/as-of label from downloaded file or source page |
| `source_url` | string | URL | Data-library or downloaded-file URL |
| `methodology_url` | string | URL | Fama/French factor description URL |

Validation rules:

- `return_date` must be unique and strictly sorted in the artifact.
- Numeric return columns must be finite for every published benchmark row.
- Return values must be decimal returns, not percent returns.
- The artifact must fail if any source row needed for D2B has missing `mktrf`, missing `rf`, infinite values, or values below `-1.0`.
- The artifact must reject duplicate source dates unless duplicate rows are byte-identical and reduced by an explicitly tested deterministic rule.

## Session alignment and missingness policy

- Join key: `return_date` only.
- Join spine: the D2B global market-session spine, currently 2,862 sessions from 2015-01-02 through 2026-03-06.
- Join type for future D3 strategy handoff: left join D2B event-window rows to benchmark rows by `return_date`.
- Fill policy: no forward-fill, backward-fill, interpolation, zero substitution, holiday inference, or fallback to another benchmark.
- Missing benchmark dates remain missing and must set `coverage_reason = missing_benchmark_return`.
- CAR/BHAR eligibility requires all 60 benchmark observations, matching the strategy contract's `benchmark_observations == 60`.
- Events with complete asset returns but incomplete benchmark returns can still report raw cumulative total return, but they cannot report CAR/BHAR.
- Any future source-release coverage gap across the D2B spine is a hard implementation blocker, not a design reason to impute.

## Manifest and publication contract

Future implementation must publish an immutable Parquet plus atomic manifest pointer, matching the D2A/D2B artifact style.

Required manifest fields:

- `artifact_name`
- `schema_version`
- `mode`
- `created_at_utc`
- `parquet_file`
- `sha256`
- `row_count`
- `min_return_date`
- `max_return_date`
- `source_name`
- `source_url`
- `methodology_url`
- `source_release`
- `source_download_sha256`
- `units`
- `formula`
- `required_d2b_sessions`
- `matched_d2b_sessions`
- `missing_d2b_sessions`
- `failure_reasons`
- `allowed_use`
- `forbidden_use`

Publication rules:

- Write immutable hash-named Parquet first.
- Hash the exact bytes that readers will later load.
- Atomically replace the small manifest pointer last.
- A failed write must leave the previous manifest pointer untouched.
- The manifest must explicitly say `allowed_use = benchmark_input_for_pead_d3_only`.
- The manifest must explicitly forbid provider authorization claims, alpha interpretation, dashboard integration, ranking, alerts, broker/order paths, and use of `mktrf` alone as total market return.

## Terminology contract

- Existing `car` in `strategies/pead_event_study.py` means beta-1 market-adjusted CAR: `sum(asset_return - benchmark_return)`.
- Existing `bhar` means buy-and-hold abnormal return: `product(1 + asset_return) - product(1 + benchmark_return)`.
- Do not call the current `car` output regression alpha.
- Do not call raw `cumulative_total_return` CAR.
- UI or report copy must say `market-adjusted CAR` or `beta-1 market-adjusted CAR` unless a later approved round implements a regression-alpha estimator.

## Implementation acceptance tests

Future D3 implementation must include tests that prove:

- Source percent returns are converted to decimals.
- `benchmark_return = mktrf + rf` after conversion.
- `mktrf` alone is rejected as total market return.
- The artifact covers every required D2B `return_date` from 2015-01-02 through 2026-03-06 before CAR/BHAR production.
- Missing benchmark dates are retained and force `missing_benchmark_return`, with no fill or interpolation.
- A complete D2B event with one missing benchmark date has raw cumulative return but no CAR/BHAR eligibility.
- All 60 benchmark observations are required for CAR/BHAR.
- Duplicate benchmark dates fail closed or reduce only under an explicitly tested deterministic identical-row rule.
- Manifest hash matches immutable Parquet bytes and the manifest pointer is updated atomically.
- Source citation, methodology citation, units, formula, source release, row count, min/max dates, and missing-session counts are present in the manifest.
- A source-release/regime metadata change is visible in the manifest and not silently spliced into the prior artifact.

## Current local artifact finding

`data/processed/ff_factors.parquet` exists but is insufficient for this D3 contract:

- rows: 1,003
- date range: 2022-01-03 through 2025-12-31
- D2B required spine: 2,862 sessions from 2015-01-02 through 2026-03-06

This artifact may remain historical/local evidence, but it must not be promoted as the D3 canonical benchmark input.

## Risk and rollback

- P0 risk: using excess market return alone would understate total benchmark return and corrupt CAR/BHAR.
- P0 risk: filling missing dates would fabricate benchmark evidence and make incomplete events look eligible.
- P1 risk: source methodology changes can alter the benchmark regime; manifest metadata must make the source release explicit.
- Rollback for future implementation: atomically restore the previous benchmark manifest pointer, keep immutable Parquet objects, and verify row count, hash, min/max dates, and required D2B-session coverage before resuming readers.

