# V2 PEAD Calendar-Time Inference M1B

Mode: `EXECUTION_PACKET`
Status: `DONE; NUMBERS-ONLY EVIDENCE PUBLISHED; TERMINAL SAW PASS; NO ALPHA OR PRODUCT ACTION AUTHORIZED.`
Date: 2026-06-21
RoundID: `ROUND-20260621-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B`
ScopeID: `V2_PEAD_CALENDAR_TIME_INFERENCE_IMPLEMENTATION`
Owner: Strategy + Data + Docs/Ops

## Terminal closure recovery addendum

RoundID: `ROUND-20260621-V2-PEAD-M1B-DASHBOARD-MARKER-CLOSURE`

The inherited full-suite blocker was repaired in a bounded Frontend/UI closure
round by restoring the event-ledger Plotly trace names in `dashboard.py` to
`ENTER` and `EXIT`. The lifecycle hover wording remains explicit and the
existing `ENTER`/`EXIT` filters, marker symbols, and marker colors are
unchanged.

Closure evidence:

- Focused lifecycle regression:
  `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py::test_event_ledger_chart_unchanged_enter_exit_markers -q`
  PASS.
- `dashboard.py` compile: PASS.
- Full repository pytest: `.venv\Scripts\python -m pytest -q` PASS.
- Reviewer A/B/C dashboard closure reviews: PASS.
- M1B JSON hash remains
  `c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`.
- Protected validation JSON hash remains
  `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.

This closure does not authorize alpha interpretation, strategy promotion,
ranking/scoring, alerts, recommendations, broker/order paths, PIT/full-universe
claims, or dashboard action surfaces.

## Hierarchy confirmation

- L1: Terminal Zero local-first quantitative research console.
- L2 active streams: Strategy, Data, Docs/Ops.
- L2 deferred stream: Frontend/UI and all product/action surfaces.
- L3 stage: M1B calendar-time inference implementation in final verification.
- Hierarchy Confirmation: Approved | Session: current-thread | Trigger:
  inherited-explicit-user-go-M1 | Domains: quantitative-research,
  econometrics,data-integrity,docs-ops.

## Objective and authority

Implement the bounded M1B calendar-time PEAD inference contract after terminal
Reviewer C passed the corrected M1A count/data-integrity recheck. This round
adds estimator code, tests, and one deterministic evidence JSON. It does not
authorize an alpha verdict, strategy promotion, ranking/scoring, alerts,
recommendations, broker/order paths, provider access, or D1/D2B/D3 mutation.

## Implemented files

- `strategies/pead_event_study.py`
- `scripts/pead_real_data_validation.py`
- `tests/test_pead_event_study.py`
- `tests/test_pead_real_data_validation.py`
- `docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`

Required closure docs and context surfaces were updated separately. The
protected validation JSON
`docs/context/e2e_evidence/pead_real_data_validation_20260620.json` remained at
SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.

## Method contract

The primary estimator is the daily calendar-time high-minus-low portfolio:

```text
R_HL,t = EW(raw asset return of active Q5 securities at t)
         - EW(raw asset return of active Q1 securities at t)

R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t
```

- Signal assignment uses only event-date SUE cohorts via
  `signal_bucket_eligible`.
- Active sessions use the authoritative D2B/D3 `+1..+60` rows.
- Every non-null D2B `return_date` must exist on the authoritative D3 session
  spine; off-spine rows fail closed before estimation.
- Overlap resolution runs across all assigned quantiles before Q1/Q5 filtering.
- Latest event wins by `(security_id, return_date)`; tied latest event IDs fail
  closed.
- A newer Q2-Q4 event closes an older Q1/Q5 exposure.
- Missing latest returns and no-eligible-security extreme rows remain expected
  missing rows; no older-event fallback, fill, imputation, interpolation, or
  delisting substitution is allowed.
- Each leg requires at least 10 finite distinct securities per retained session.
- Primary inference uses Newey-West HAC with `maxlags=59` and
  `use_correction=true`.
- Paired stationary block bootstrap uses expected block length 60, 10,000
  replications, seed 20260621, and max batch size 256 as robustness-only
  evidence.
- The M1B CLI output is fixed to the resolved canonical evidence path. Count
  fields must be nonnegative and arithmetically reconciled; a zero-retained
  result uses null date endpoints and null inference.

## Published evidence

Artifact:
`docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`

Artifact SHA256:
`c80bb7ed583a933dae664251ffe1fc56a0bcaf5f9a086b1e42740047a5018b76`

Key evidence fields:

- `session_coverage.null_return_date_rows_excluded`: `19,812`
- `session_coverage.extreme_expected_rows`: `226,772`
- `session_coverage.extreme_missing_rows`: `1,519`
- `session_coverage.q1`: expected `96,310`, finite `95,465`, missing `845`
- `session_coverage.q5`: expected `130,462`, finite `129,788`, missing `674`
- `session_coverage.retained_sessions`: `2,539`
- `session_coverage.retained_date_min`: `2016-02-01`
- `session_coverage.retained_date_max`: `2026-03-06`
- `session_coverage.internal_gap_count`: `0`
- `primary_inference.status`: `valid`
- `primary_inference.observations`: `2,539`
- `primary_inference.hac_maxlags_used`: `59`
- `robustness.status`: `valid`
- `robustness.replications`: `10,000`
- `evidence_policy.interpretation_performed`: `false`

Numeric inference values are evidence for bounded methodology review only. They
are not an alpha verdict.

## Acceptance evidence

- Independent Reviewer C terminal recheck: PASS. Reproduced 19,812 null-date
  rows excluded, 226,772 expected rows, 1,519 missing rows, and 2,539 retained
  sessions; no Critical/High findings.
- `.venv\Scripts\python -m pytest tests\test_pead_event_study.py tests\test_pead_real_data_validation.py tests\test_pead_validation_evidence.py -q`
  PASS, 50 tests after Reviewer B/C hardening.
- `.venv\Scripts\python scripts\pead_real_data_validation.py --calendar-time-m1b`
  PASS; artifact written atomically.
- M1B schema validation: PASS via
  `scripts.pead_real_data_validation.validate_calendar_time_evidence_schema`.
- Protected JSON hash check: PASS at
  `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Reviewer A PASS; Reviewer B PASS after output/schema fixes; Reviewer C
  technical PASS after spine/null/count fixes.
- Bounded dashboard marker closure repaired the inherited full-suite failure;
  full repository pytest now passes.
- Terminal dashboard closure Reviewer A/B/C PASS, so terminal SAW is PASS.

## Rollback baseline

Before edits, byte-for-byte backups were captured under ignored
`tmp/m1b_baseline/`:

| File | Baseline SHA256 |
|---|---|
| `strategies/pead_event_study.py` | `ff4b3d95b11027a22005e039002e9ea7aaa37e471eb07b82c8f3cdedcbe66729` |
| `scripts/pead_real_data_validation.py` | `e17c78c92c2b12816d4f2d3fff9e8db6f2b68716a0a97444b2e8f3529ec27fce` |
| `tests/test_pead_event_study.py` | `9bb95570e0273d883fb4308bed7d02530aee145526d167c2e78b6c2f04b7c136` |
| `tests/test_pead_real_data_validation.py` | `3966e238cabbe4b2111741655f8eb818afa5e78c3f71f3a2ff631184af9ec3e7` |

Rollback path: restore those four files from `tmp/m1b_baseline/`, remove only
`docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`, and revert
M1B closure-doc addenda. Preserve the protected 20260620 validation JSON.

## Boundaries

Still blocked: alpha interpretation, strategy promotion, PIT EPS, CRSP/delisting
repair, full-universe expansion, net/tradable performance claims,
ranking/scoring, alerts, recommendations, and broker/order paths.
