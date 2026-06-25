# V2 PEAD Alpha Inference Methodology Gate

Mode: `APPROVAL_GATE`
Status: `CONTRACT SELECTED; TERMINAL SAW BLOCKED PENDING REVIEWER C COUNT RECHECK; M1B not executed.`
Date: 2026-06-21
RoundID: `ROUND-20260621-V2-PEAD-ALPHA-INFERENCE-METHODOLOGY-GATE`
ScopeID: `V2_PEAD_CALENDAR_TIME_INFERENCE_METHOD_CONTRACT`
Owner: Strategy + Data + Docs/Ops

## Objective and authority

Select one bounded methodology contract for future M1B implementation of PEAD
calendar-time inference. This M1A round changes methodology and required
governance documentation only. It does not execute M1B, change code or tests,
access a provider, read or write data artifacts, mutate locked evidence JSON,
stage files, or commit. Terminal approval is blocked until independent Reviewer
C reruns the corrected count/data-integrity check.

## Ship-Fast Decision Gate

Reference: `docs/templates/ship_fast_decision_gate.md`.

- What is done: the primary estimator, event assignment, overlap handling,
  missingness, HAC settings, robustness method, claim boundary, acceptance
  tests, and future file allowlist are selected and reconciled.
- What is blocked: any alpha claim or M1B output until the bounded
  implementation and its acceptance checks pass; M1B itself is blocked until
  terminal Reviewer C recheck passes.
- User order interpreted as: approve the methodology contract in M1A only; do
  not execute M1B.
- Recommended next step: rerun independent Reviewer C on the corrected
  feasibility/count contract; only after PASS, implement exactly this contract
  in one bounded M1B round.
- Why this is correct: calendar-time portfolios resolve overlapping event
  exposures without treating overlapping event observations as independent,
  while preserving the existing authoritative session and signal-assignment
  contracts.
- Alternatives considered: observed-event-date HAC as the primary estimator;
  rejected. Calendar-month or quarterly formal inference; rejected. Stationary
  block bootstrap as the primary estimator; rejected and retained only as a
  robustness check.
- Decision: `PROVISIONAL_CONTRACT_SELECTED` - use the primary calendar-time
  portfolio regression as the sole M1B formal-inference method if terminal
  Reviewer C recheck passes.
- Scope limit: the four allowlisted future code/test files plus one new M1B
  evidence artifact whose exact path is selected and recorded in M1B.
- Stop rule: return null inference on any contract, lineage, overlap,
  completeness, leg-count, deterministic-output, or existing-JSON-integrity
  failure.

This gate contains one decision only. It does not approve strategy promotion or
any product or execution action.

## Candidate matrix

| Candidate | Role | Gate result |
|---|---|---|
| Observed-event-date HAC | Primary formal inference | Rejected |
| Calendar-month or quarterly aggregation | Formal inference | Rejected |
| Paired stationary block bootstrap | Robustness only | Selected only as secondary evidence |
| Daily calendar-time portfolio regression | Primary formal inference | Selected; terminal approval pending Reviewer C |

## Primary formation contract

- Assign events using the existing event-date signal rule based on
  `signal_bucket_eligible`; future outcome availability or window completeness
  must not affect signal assignment.
- Form only Q1 and Q5 legs.
- An event is active only on its authoritative D2B/D3 market sessions `+1..+60`.
- Resolve overlap across **all** `signal_bucket_eligible` events before filtering
  to Q1/Q5. For each `(security_id, return_date)`, retain at most one active
  exposure and let the latest `event_date` win. A newer Q2-Q4 event therefore
  closes an older Q1/Q5 exposure rather than leaving a stale extreme signal
  active.
- If multiple event IDs remain tied on that latest `event_date`, fail closed for
  that security/date; do not choose an event ID arbitrarily.
- If the retained latest event has a missing or non-finite asset return, record
  it as missing. Do not fall back to an older active event.
- Only after overlap resolution, retain latest-event exposures assigned to Q1
  or Q5 for portfolio formation.

## Daily leg and completeness contract

- Each leg is the equal-weight mean of finite observed raw asset returns for
  distinct securities after overlap resolution.
- For every authoritative session and each leg, report the expected distinct
  security count, finite distinct security count, and missing distinct security
  count.
- Do not fill, impute, interpolate, substitute a delisting return, or otherwise
  manufacture a missing asset return.
- Each leg requires at least 10 finite distinct securities on a session.
- Trim leading and trailing dates using only the per-leg minimum-count rule.
  After trimming, every authoritative session inside the retained interval must
  satisfy the rule for both legs. Any internal failing session makes primary
  inference null; internal dates must not be dropped.
- Publish per-leg aggregate and daily expected, finite, missing, and missing-rate
  diagnostics. Missingness asymmetry must remain visible.
- Publish a descriptive missingness sensitivity using only events with complete
  60-session asset-return windows. Label it
  `ex_post_missingness_sensitivity_only=true`; it cannot replace or override the
  primary signal-only available-return estimator.

## Primary model and HAC contract

For each retained authoritative session `t`:

```text
R_HL,t = EW(raw asset return of active Q5 securities at t)
         - EW(raw asset return of active Q1 securities at t)

R_HL,t = alpha_CT + beta_M * mktrf_t + epsilon_t
```

- `R_HL,t` is a zero-investment high-minus-low return. Do not subtract `rf` from
  it.
- Bind D3 `mktrf_t` to the published D3 manifest and immutable artifact hash;
  missing, duplicate, non-finite, or lineage-mismatched factor rows fail closed.
- Label `alpha_CT` only as the **single-factor calendar-time intercept**. It is
  not a full-factor alpha or a strategy-performance claim.
- Use Newey-West HAC with `maxlags=59` and `use_correction=true` exactly. No lag
  search, tuning, fallback, or significance-driven reconfiguration is allowed.
- Require at least 60 retained sessions. If fewer are available, return null
  inference. `maxlags` must never be clipped below 59.

## Robustness contract

- Run a paired stationary block bootstrap over complete daily
  `(R_HL, mktrf)` pairs so each resampled day preserves the joint pair.
- Expected block length: `60` days.
- Replications: exactly `10,000`; fixed seed: `20260621`.
- For each replication, sample a length-`T` paired series with circular indexing:
  start from a uniform random source index, continue to the next source index
  modulo `T` with probability `59/60`, and restart at a new uniform source index
  with probability `1/60`.
- Refit the same `R_HL ~ 1 + mktrf` OLS model on every resample and record only
  `alpha_CT*`. Any non-finite or rank-deficient replication fails the robustness
  output; do not discard or redraw it.
- Report an uncentered 95% percentile interval at the 2.5th and 97.5th
  percentiles. For the two-sided null p-value, subtract observed `alpha_CT` from
  `R_HL`, resample the centered paired series, refit the model, and report
  `(1 + count(abs(alpha_CT_null*) >= abs(alpha_CT))) / 10001`.
- Use NumPy arrays with bootstrap batches of at most 256 replications; do not
  construct a DataFrame per replication or allocate a full `10000 x T` matrix.
  The current-sample runtime check must finish within 120 seconds.
- Bootstrap evidence is robustness-only. It cannot replace, rescue, override,
  or promote a null or adverse primary HAC result.

## Descriptive and claim boundaries

- Quarterly output remains `ex_post_descriptive_only=true`; it is not formal
  inference and cannot replace the primary daily calendar-time result.
- The maximum permitted claim is limited to the fixed 500-GVKEY,
  current-vintage, Compustat-return, no-delisting sample and a single-factor,
  gross, equal-weight calendar-time Q5-minus-Q1 difference.
- Do not claim population validity, strict point-in-time validity, causality,
  tradability, net performance, or full-factor alpha.
- Do not promote a strategy or add ranking/scoring, alerts, recommendations, or
  broker/order behavior.

## Feasibility diagnostics

Parent read-only analysis reported:

- `signal_bucket` events: `9,939`.
- Latest-event ambiguity cells after all-quantile overlap resolution: `0`.
- Null-`return_date` insufficient-future-session rows excluded before portfolio
  formation: `19,812` across `379` signal-eligible events.
- Extreme-leg authoritative-session expected rows after all-quantile overlap
  resolution: `226,772`.
- Missing asset rows after authoritative-session filtering, all-quantile
  latest-event deduplication, and Q1/Q5 filtering: `1,519`
  (`845 / 96,310` Q1; `674 / 130,462` Q5).
- With the 10-security threshold, a contiguous `2,539`-session interval runs
  from `2016-02-01` through `2026-03-06`.
- Median finite leg counts in that interval are Q1 `38` and Q5 `51`.

These values are parent-side feasibility diagnostics only. They are not M1B
results, inference output, acceptance evidence, or an alpha claim, and the
terminal independent Reviewer C recheck remains pending.

## M1B implementation, closure, and evidence contract

After terminal M1A SAW passes, the only runtime/test implementation files M1B
may change are:

- `strategies/pead_event_study.py`
- `scripts/pead_real_data_validation.py`
- `tests/test_pead_event_study.py`
- `tests/test_pead_real_data_validation.py`

Required Docs/Ops closure files are separately allowed: one M1B phase brief,
PRD/product-spec addenda, `docs/notes.md`, `docs/decision log.md`,
`docs/lessonss.md`, the seven current truth surfaces, builder-generated compact
context, and one M1B SAW report. No other runtime/test file is authorized.

The exact new evidence path is
`docs/context/e2e_evidence/pead_calendar_time_inference_m1b.json`. Required root
keys are `schema_version`, `round_id`, `scope_id`, `method_id`, `lineage`,
`formation`, `session_coverage`, `daily_summary`, `primary_inference`,
`missingness_sensitivity`, `robustness`, `limitations`, and `evidence_policy`.
Serialize UTF-8 JSON with sorted keys, two-space indentation, `allow_nan=false`,
and one trailing newline. Publish with a same-directory temporary file, flush,
`fsync`, atomic replace, and temporary-file cleanup on `BaseException`; add an
interruption regression proving the prior artifact remains intact.

The JSON schema is closed: no additional root or nested fields are allowed;
object keys are serialized in sorted order; arrays are deterministically sorted
and deduplicated; date strings use `YYYY-MM-DD`. Exact fields and types:

| Object | Exact fields |
|---|---|
| root | `schema_version="1.0"`; `round_id="ROUND-20260621-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B"`; `scope_id="V2_PEAD_CALENDAR_TIME_INFERENCE_IMPLEMENTATION"`; `method_id="calendar_time_q5_q1_single_factor_hac59_v1"`; and the nine objects listed below |
| `lineage` | `d1`, `d2b`, `d3` artifact objects; `protected_validation_json` object |
| each artifact object | `manifest_path:string`, `manifest_sha256:string`, `parquet_path:string`, `parquet_sha256:string`, `rows:integer` |
| `protected_validation_json` | `path:string`, `sha256:string` |
| `formation` | `quantiles:integer=5`, `low_quantile:integer=1`, `high_quantile:integer=5`, `cohort_frequency:string="D"`, `eligibility:string="signal_bucket_eligible"`, `start_day:integer=1`, `end_day:integer=60`, `overlap_order:string="all_quantiles_before_extreme_filter"`, `overlap_key:array[string]`, `overlap_winner:string="latest_event_date"`, `tie_policy:string="fail_closed"`, `missing_latest_policy:string="no_fallback"`, `weighting:string="equal_weight_distinct_security"`, `minimum_finite_per_leg:integer=10` |
| `session_coverage` | `authoritative_sessions:integer`, `authoritative_date_min:string`, `authoritative_date_max:string`, `null_return_date_rows_excluded:integer`, `retained_sessions:integer`, `retained_date_min:string`, `retained_date_max:string`, `internal_gap_count:integer`, `latest_event_ambiguity_cells:integer`, `extreme_expected_rows:integer`, `extreme_finite_rows:integer`, `extreme_missing_rows:integer`, `q1:leg_counts`, `q5:leg_counts` |
| each `leg_counts` | `expected:integer`, `finite:integer`, `missing:integer`, `missing_rate:number` |
| `daily_summary` | `sessions:integer`, `q1:daily_leg_summary`, `q5:daily_leg_summary`, `spread:return_summary`, `factor:return_summary` |
| each `daily_leg_summary` | `minimum_finite:integer`, `median_finite:number`, `maximum_finite:integer`, `total_expected:integer`, `total_finite:integer`, `total_missing:integer`, `missing_rate:number` |
| each `return_summary` | `observations:integer`, `mean:number`, `standard_deviation:number`, `minimum:number`, `maximum:number` |
| `primary_inference` | `status:string[valid|null]`, `dependent_variable:string="R_HL"`, `regressor:string="mktrf"`, `observations:integer`, `alpha_ct:number|null`, `beta_m:number|null`, `alpha_hac_standard_error:number|null`, `alpha_hac_t_stat:number|null`, `alpha_hac_two_sided_p_value:number|null`, `hac_maxlags_requested:integer=59`, `hac_maxlags_used:integer`, `use_correction:boolean=true`, `failure_reasons:array[string]` |
| `missingness_sensitivity` | `ex_post_missingness_sensitivity_only:boolean=true`, `population_rule:string="complete_60_session_asset_window"`, `observations:integer`, `alpha_ct:number|null`, `beta_m:number|null`, `alpha_hac_standard_error:number|null`, `alpha_hac_t_stat:number|null`, `failure_reasons:array[string]` |
| `robustness` | `status:string[valid|null]`, `method_id:string="paired_stationary_block_bootstrap_alpha_ct_v1"`, `expected_block_length:integer=60`, `replications:integer=10000`, `seed:integer=20260621`, `interval_level:number=0.95`, `alpha_percentile_lower:number|null`, `alpha_percentile_upper:number|null`, `alpha_centered_null_two_sided_p_value:number|null`, `invalid_replications:integer`, `max_batch_size:integer=256`, `failure_reasons:array[string]` |
| `limitations` | `sample_universe:string`, `eps_vintage:string`, `return_source:string`, `delisting_adjustment:string`, `factor_model:string` |
| `evidence_policy` | `allowed_use:string="bounded_methodology_review_only"`, `interpretation_performed:boolean=false`, `strategy_promotion_authorized:boolean=false`, `ranking_or_scoring_authorized:boolean=false`, `alerts_or_recommendations_authorized:boolean=false`, `broker_or_order_path_authorized:boolean=false`, `forbidden_use:array[string]` |

For `primary_inference`, `missingness_sensitivity`, and `robustness`, inferential
numeric fields may be null only when `status="null"` or the sensitivity has a
non-empty `failure_reasons` array. A valid primary or robustness result requires
all corresponding numeric fields finite, exact configured counts, and an empty
`failure_reasons` array. JSON Schema-equivalent validation and rejection of
unknown fields are mandatory tests.

Before edits, M1B must capture byte-for-byte backups of the four currently
untracked implementation/test files under ignored `tmp/m1b_baseline/`, record
their SHA256 values in the M1B phase brief, and verify them before rollback.
The protected pre-existing JSON is exactly
`docs/context/e2e_evidence/pead_real_data_validation_20260620.json` at SHA256
`96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
Builder-generated `docs/context/current_context.json` is excluded from that
byte-identity rule. D1/D2B/D3 manifest and artifact hashes remain protected by
their published lineage contracts.

M1B acceptance tests must prove:

- Formation uses `signal_bucket_eligible`, Q1/Q5 only, and authoritative
  `+1..+60` D2B/D3 sessions without future outcome/window-completeness leakage.
- Overlap resolution occurs across all assigned quantiles before Q1/Q5
  filtering; it is unique by `(security_id, return_date)`, latest event wins,
  equal-date event-ID ambiguity fails closed, a newer middle-quintile event
  closes an older extreme exposure, and a missing latest return never falls
  back to an older event.
- Daily expected, finite, and missing distinct-security counts reconcile; equal
  weighting uses only finite observed raw returns; no fill, imputation, or
  delisting substitution occurs.
- The 10-security rule controls endpoint trimming, and any internal leg-count
  failure makes inference null without dropping the date.
- Real-sample regression locks the feasibility counts above and publishes
  per-leg missing rates plus the descriptive complete-window sensitivity.
- Null `return_date` skeleton rows are counted as insufficient future sessions
  and excluded before authoritative-session portfolio counts; they are never
  classified as missing asset returns.
- The H-L formula, zero-investment `rf` treatment, D3 manifest/hash binding,
  single-factor regression, and `alpha_CT` label match this contract.
- HAC is exactly `maxlags=59` with `use_correction=true` and no tuning path.
- Retained `T >= 60`; HAC uses exactly 59 lags without clipping.
- The paired stationary block bootstrap matches the exact resampling, refit,
  interval, centered-null p-value, invalid-replication, seed, batching, and
  runtime rules above and cannot override the primary result.
- Quarterly remains `ex_post_descriptive_only=true`, claim/forbidden-use labels
  are present, and the exact protected JSON/hash remains byte-identical before
  and after the run.
- Focused tests in both allowlisted test modules and the bounded validation CLI
  pass before the new evidence artifact is accepted.
- Exact-schema tests cover required fields, types, nullability, enum/constants,
  date format, sorted/deduplicated arrays, and unknown-field rejection.

## Research evidence status

Primary source: Eugene F. Fama, "Market efficiency, long-term returns, and
behavioral finance," *Journal of Financial Economics* 49 (1998), 283-306,
`docs/research/fama_1998_market_efficiency_long_term_returns.pdf`.
Source URL: `http://www.e-m-h.org/Fama98.pdf`. Local PDF SHA256:
`1be1c965437bb3dcea46056e45d1c744082d75a26205c8274b8e259164169184`.

- Journal page 295 (PDF page 13) states that a rolling calendar-time portfolio's
  time-series variation captures cross-event return correlation missed by the
  expected-return model. This directly supports the primary calendar-time
  aggregation choice.
- Journal pages 293-295 (PDF pages 11-13) warn that long-horizon BHAR inference
  and ignored cross-correlation are problematic. This supports keeping CAR/BHAR
  and quarterly outputs descriptive rather than promoting their current
  t-statistics.
- Fama's example is monthly and long-horizon; this contract's daily frequency,
  60-session horizon, HAC bandwidth, overlap rule, and bootstrap specification
  are explicit repo-policy adaptations, not claims that the paper prescribes
  these exact parameters.

Claim evidence and extracted source text are recorded in
`docs/research/pead_inference_methodology_claims_20260621.json` and
`docs/research/fama_1998_market_efficiency_long_term_returns.txt`.

## Risks, forbidden scope, and rollback

- P0: future-aware formation, silent overlap fallback, internal-date deletion,
  or missing-return substitution would invalidate inference and must fail
  closed.
- P0: changing HAC settings or allowing robustness results to override the
  primary result would create specification-driven significance search.
- P1: the bounded sample and single-factor gross model materially limit any
  claim even when implementation succeeds.
- Forbidden in M1A: code, tests, provider access, data artifacts, JSON mutation,
  staging, and commit. M1B has not been executed. Terminal M1A approval remains
  blocked pending independent Reviewer C recheck of the corrected count contract.
- Forbidden in M1B: files outside the allowlist and one new evidence artifact;
  provider ingestion; D1/D2B/D3 artifact mutation; existing JSON mutation;
  signal/formula tuning; population, PIT, causal, tradable, net, or full-factor
  claims; product promotion; ranking/scoring; alerts; recommendations; and
  broker/order paths.
- M1A rollback: remove only this new contract file.
- Future M1B rollback: verify and restore the four implementation/test files
  from `tmp/m1b_baseline/`, remove only the new M1B evidence artifact, and
  revert M1B closure-doc addenda. Preserve the exact protected validation JSON
  and immutable D1/D2B/D3 artifacts byte-for-byte.
