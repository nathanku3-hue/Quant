# V2 PEAD D3 Benchmark Artifact Implementation

Mode: `EXECUTION_PACKET`
Status: `DONE`; D3 artifact and strategy benchmark handoff validated, D4 implementation not authorized
Date: 2026-06-20
RoundID: `ROUND-20260620-V2-D3-BENCHMARK-ARTIFACT-PUBLICATION`
ScopeID: `V2_D3_KEN_FRENCH_BENCHMARK_ARTIFACT_PUBLICATION`
Owner: Data + Docs/Ops

Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Strategy validation, Data, and Docs/Ops; L2 deferred stream Frontend/UI; L3 Final Verification.

## 2026-06-20 strategy benchmark handoff addendum

The bounded D3 strategy benchmark handoff gate is complete. The new
`tests/test_pead_d3_strategy_handoff.py` validates the published D2B and D3
manifest pointers and passes the real benchmark rows through
`summarize_event_windows` without changing production strategy code.

Acceptance evidence:

- D3 SHA and benchmark-only allowed use validated against 2,810 rows;
- D2B-to-D3 left join validated many-to-one with 754,920 rows preserved;
- every non-null D2B return date is covered;
- all 11,450 complete event windows contain 60 benchmark observations;
- real-event CAR/BHAR spot checks match the explicit formulas;
- one missing benchmark observation masks CAR/BHAR but preserves raw cumulative asset return;
- new handoff suite PASS, 5 tests; combined handoff/artifact/strategy suite PASS, 26 tests.
- final Reviewer A/B/C reruns and SAW validators PASS after all High findings were reconciled.

No conditional defect fix was required. D2B/D3 artifacts and
`strategies/pead_event_study.py` remained read-only. This closes the D3 handoff
gate but does not authorize D4 dashboard implementation or alpha interpretation.

SAW evidence: `docs/saw_reports/saw_v2_d3_strategy_benchmark_handoff_20260620.md`.

Next separate decision: approve or hold bounded D4 dashboard-integration
scoping.

## 2026-06-20 publication addendum

The bounded D3 publication gate is complete. The builder published the
hash-named benchmark Parquet and atomic manifest pointer only after validating
the repaired 2,810-session D2B spine against the exact Ken French source bytes
recorded in the D2B manifest.

Published artifact:

- Parquet: `data/processed/pead_d3_ken_french_daily_benchmark.f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589.parquet`
- Manifest: `data/processed/pead_d3_ken_french_daily_benchmark.parquet.manifest.json`
- SHA256: `f7dede990475b4ecf499fbf1dee3c4a81298073f018cc3a1ba1559f3e702c589`
- Rows: 2,810
- Date range: 2015-01-02 through 2026-03-06
- Coverage: 2,810 / 2,810 required D2B sessions, zero missing
- Source release: `This file was created by using the 202604 CRSP database.`
- Source ZIP SHA256: `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`
- Formula: `benchmark_return = mktrf + rf` after percent-to-decimal conversion

Validation evidence:

```text
.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py tests\test_pead_d2b_event_window_contract.py -q
```

Result: PASS, 38 passed.

```text
.venv\Scripts\python scripts\pead_d3_benchmark_artifact.py --build
```

Result: PASS, artifact and manifest written with coverage `2810/2810`.

Independent artifact check: manifest hash matches the Parquet, row count is
2,810, formula max absolute error is `0.0`, numeric fields are finite, duplicate
`return_date` count is zero, and `missing_d2b_sessions` is empty.

SAW evidence: `docs/saw_reports/saw_v2_d3_benchmark_artifact_publication_20260620.md`
records PASS after independent Reviewer A/B/C review and validator checks.

Scope boundary: this publication does not run CAR/BHAR or quintile
interpretation, does not change D1/D2A/D2B semantics, does not add dashboard
integration, ranking/scoring, alerts, broker/order paths, full build, staging,
or commit.

Next separate decision: approve or hold a bounded D3 strategy benchmark handoff
validation round. That round may verify strategy consumption of the published
benchmark, but alpha interpretation and product/dashboard use remain separately
blocked.

## 2026-06-19 upstream repair addendum

The 52-date upstream blocker described below is repaired in the active D2B
manifest. D3 now validates the explicit Ken French source-backed D2B session
spine and can construct 2,810 / 2,810 benchmark rows in memory with zero
missing dates. No D3 benchmark Parquet or manifest was published; publication
still requires a separate approved round. Historical fail-closed evidence
below remains valid for the pre-repair D2B manifest.

## Objective and boundary

Implement the bounded D3 benchmark artifact builder and focused tests for the locked D3 contract:

- canonical source: Ken French daily Fama/French 3 Factors;
- percent-to-decimal conversion;
- `benchmark_return = mktrf + rf`;
- full D2B session coverage before artifact publication;
- immutable hash-named Parquet plus atomic manifest pointer;
- no missing-date fill, interpolation, zero substitution, fallback benchmark, or source-regime splice.

This round does not publish a benchmark artifact because coverage failed closed. It does not change D1/D2A/D2B artifacts, run CAR/BHAR or quintile interpretation, change dashboard surfaces, rank or score candidates, emit alerts, touch broker/order paths, stage files, or commit. A narrow strategy-summary correction was made after review so complete asset-return windows still report raw cumulative return when only benchmark coverage is missing, while CAR/BHAR and eligibility remain blocked.

## Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

What is done: executable builder and focused tests now exist for D3 benchmark source parsing, unit conversion, formula enforcement, D2B coverage validation, and atomic publication behavior.

What is blocked: canonical benchmark artifact publication, CAR/BHAR production, real PEAD interpretation, dashboard integration, ranking/scoring, alerts, broker/order paths, full build, staging, and commit.

User order interpreted as: run only bounded D3 benchmark artifact implementation, stopping before artifact publication if source or coverage cannot be proven.

Decision result: stop before publishing a benchmark artifact because the current D2B session spine includes 52 dates that are absent from the official Ken French daily source.

Recommended next step: repair or reconcile the upstream D2B/D2A market-session spine so it represents actual tradable sessions only, then rerun the D3 builder.

Why this is correct: the D3 contract explicitly forbids filling missing benchmark dates. The missing dates are market holidays and special closures present in the current D2B-required spine, so publishing would silently convert a D2B upstream calendar issue into fabricated benchmark coverage.

Scope limit: builder/tests/docs only; no benchmark Parquet manifest was published.

Stop rule triggered: missing required benchmark dates fail closed.

## Implementation artifacts

- `scripts/pead_d3_benchmark_artifact.py`
- `tests/test_pead_d3_benchmark_artifact.py`- `strategies/pead_event_study.py` (narrow summary semantics repair only)

The builder:

- fetches the official Ken French daily ZIP from `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip`, or reads a local ZIP if supplied;
- parses source release metadata from the CSV header;
- converts source percent fields to decimal returns;
- computes `benchmark_return = mktrf + rf`;
- validates the D2B manifest and derives the required session spine from the D2A input recorded by the D2B manifest;
- refuses publication if any D2B-required session is missing from Ken French daily factors;
- writes immutable Parquet first and atomically replaces the manifest pointer only after hash validation.

## Coverage evidence

Command:

```text
.venv\Scripts\python scripts\pead_d3_benchmark_artifact.py --build
```

Result: failed closed before artifact publication.

Evidence:

- required D2B sessions: 2,862
- official Ken French source rows: 26,233
- official source date range: 1926-07-01 through 2026-04-30
- source release: `This file was created by using the 202604 CRSP database.`
- source download SHA256: `4b384ddeed3ba5541c433071272aece0734129ff5a016790333632eee8eac518`
- missing D2B-required benchmark sessions: 52
- first missing examples: `2015-01-19`, `2015-05-25`, `2015-07-03`, `2015-11-26`, `2016-01-18`, `2016-05-30`, `2016-07-04`, `2016-11-24`, `2017-01-16`, `2017-05-29`
- last missing examples: `2024-11-28`, `2025-01-09`, `2025-01-20`, `2025-05-26`, `2025-06-19`, `2025-07-04`, `2025-11-27`, `2026-01-19`

Interpretation: D3 source coverage is not the blocker; the current D2B/D2A session spine contains non-Ken-French trading dates and must be corrected or explicitly reconciled upstream.

## Validation

Passed:

```text
.venv\Scripts\python -m py_compile scripts\pead_d3_benchmark_artifact.py tests\test_pead_d3_benchmark_artifact.py
.venv\Scripts\python -m pytest tests\test_pead_d3_benchmark_artifact.py -q
```

Focused tests cover:

- source percent-to-decimal conversion;
- `benchmark_return = mktrf + rf`;
- rejection of `mktrf` alone;
- missing required D2B session failure with no fill/interpolation;
- duplicate source-date failure;
- D2B manifest/session hash validation;
- immutable Parquet plus atomic manifest publication behavior;
- strategy behavior when benchmark observations are incomplete: raw cumulative asset return is preserved for complete asset windows, while benchmark return, CAR, BHAR, and eligibility fail closed.

## Risk and rollback

No D3 benchmark Parquet or manifest was published, so there is no D3 data artifact rollback.

Rollback for code/docs is standard file removal or revision of:

- `scripts/pead_d3_benchmark_artifact.py`
- `tests/test_pead_d3_benchmark_artifact.py`- `strategies/pead_event_study.py` (narrow summary semantics repair only)
- this implementation brief and current-truth addenda.

## Next round recommendation

Run a bounded D2B/D2A market-session spine audit and repair:

- identify why market holidays and special closures appear in the D2A/D2B global session spine;
- remove or classify non-trading dates without compressing event-security windows incorrectly;
- republish D2B only if its own fixed-security and no-imputation guarantees still pass;
- rerun D3 builder after the D2B session spine matches official benchmark availability.
