# W5 — PREBREAKOUT Trial-1 M0 Candidate Freeze

> **FINAL EXECUTION CLOSE — supersedes all uncharged/incomplete wording below.** Trial #1 opened exactly once at `2026-08-10T20:00:50.847608Z`, permanently consumes `1/8`, and closed exactly once at `2026-08-10T21:55:46.709318Z` with ledger status `FAILED` / scientific status `FAIL`. W5 completed 4/4 informative folds with median temporal-OOS recall lift `0.71570953472408605 < 1`; final W4 was sealed and fresh-process verified with Atlas SHA-256=`c471bf11fbca068edbd3e5084cc7121cd6339a3f6fd0852055f015be411b6e68`, finding no PIT/custody invalidation and median effective TTFLD miss=0=`0`. MU/SNDK smoke was explicitly **not** used for close. W6 remains untouched. No Trial #2 is authorized before the `ECONPHYSICS_PREBREAKOUT_v1` causal contract freeze. Current handover=`docs/handover/prebreakout_trial1_close_econphysics_handover_20260810.md`.

**Date:** 2026-08-10
**Disposition:** `TRIAL1_CLOSED_FAILED / MARKET_BEHAVIOR_DISCOVERY_BRANCH_CLOSED / SUCCESSOR_CAUSAL_CONTRACT_NOT_YET_FROZEN`
**Family:** `PREBREAKOUT_DISCOVERY_v1`
**Trial:** `PREBREAKOUT_TRIAL_1_M0`
**Implementation:** `PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1`
**Authority:** `DEVELOPMENT_CANDIDATE_ONLY / FINANCIAL_ALPHA_EVIDENCE_0 / CAPITAL_AUTHORITY_NONE`
**W6:** `CLOSED / FORBIDDEN`
**Trial budget consumed:** `1 / 8`

## Decision

Close the generic W5 mechanics round and freeze the next result-bearing candidate as **Trial-1 M0**, but do **not** append W2 `TRIAL_OPEN` and do **not** inspect development labels yet.

Trial-1 is a deterministic, pre-fit, market-only early-warning rule. Its exact feature representation, transforms, scoring law, split plan, cross-sectional holdout, primary objective and control definition are frozen now. The only unresolved charge-bearing field is the exact real W3/W4-bound source manifest SHA-256.

Changing the feature rule, threshold, model, training-window mode, fold plan, holdout, ranking or control definition after development-label visibility is a new material variant and requires a later charged trial. Trial-1 itself costs exactly one of W2's eight trials once opened, irrespective of PASS / FAIL / NULL / ABORTED outcome.

## Frozen candidate identity

```text
trial_id                         = PREBREAKOUT_TRIAL_1_M0
implementation_id                = PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1
feature_spec_id                  = PREBREAKOUT_TRIAL1_M0_MARKET_20_60_5_15_V1
transform_spec_id                = PREBREAKOUT_TRIAL1_M0_FIXED_COMPONENT_TRANSFORMS_V1
model_spec_id                    = PREBREAKOUT_TRIAL1_M0_DETERMINISTIC_AND_GATE_V1
training_window_spec_id          = PREBREAKOUT_TRIAL1_M0_EXPANDING_126_V1
calibration_spec_id              = PREBREAKOUT_TRIAL1_M0_NO_CALIBRATION_V1
ranking_spec_id                  = PREBREAKOUT_TRIAL1_M0_TRIGGERED_SCORE_DESC_SECURITY_ID_ASC_V1
control_spec_id                  = PREBREAKOUT_TRIAL1_M0_DATE_LOCAL_FULL_ORDINARY_CONTROL_V1
cross_sectional_holdout_spec_id  = PREBREAKOUT_TRIAL1_M0_CIQSEC_HASH_MOD5_REM0_V1
temporal_fold_plan_id            = PREBREAKOUT_TRIAL1_M0_EXPANDING_126_20E_4X20OOS_V1
primary_objective_id             = PREBREAKOUT_TRIAL1_M0_RIGHT_TAIL_LIFT_THEN_TTFLD_V1
```

Frozen uncharged declaration SHA-256:

```text
02b0e07445bb91ab7fd4c192abbd26b112facf75cf4923d4ddd8778ea5a062c1
```

Frozen W5 walk-forward spec SHA-256:

```text
7a0b77fbb95fc39a86723fd3f79d69d6fd88c12f73db65fd3224ff2723fcc9af
```

Frozen Trial-1 W4 control-definition SHA-256:

```text
144f3c08ba5ff576cd1d4a702129893f9b08f9b58b4d4a6e21ad385a7d7c44ba
```

## Market-only feature law

Allowed model inputs are exactly:

```text
market.close
market.total_return_1d
market.volume
```

No fundamentals, estimates, claims, sector map, ticker identity, current-survivor state, named winner identity, MU/SNDK branch, or fitted coefficient enters Trial-1.

Minimum market history is 60 observed sessions per exact W3 CIQSEC + Trading Item identity. Invalid/insufficient market history produces deterministic abstention (`forecast_score=0`) and is not imputed.

### 1. Pre-breakout proximity

```text
prior_high20_t = max(close[t-20 : t-1])
near_high_gate = 0.95 * prior_high20_t <= close_t <= prior_high20_t
near_high_component = clip((close_t / prior_high20_t - 0.95) / 0.05, 0, 1)
```

The upper bound is deliberate: W2 defines breakout B as `close_t > prior 20-session high`. A row already above that high is post-breakout and receives no Trial-1 early-warning flag.

### 2. Volatility compression

Using sample standard deviation (`ddof=1`) on provider total-return observations through session `t`:

```text
rv20_t = std(total_return_1d[t-19:t])
rv60_t = std(total_return_1d[t-59:t])
compression_gate = rv20_t < rv60_t
compression_component = clip(log(rv60_t / rv20_t) / log(2), 0, 1)
```

### 3. Volume pressure

```text
recent_volume5_t = median(volume[t-4:t])
prior_volume15_t = median(volume[t-19:t-5])
volume_pressure_gate = recent_volume5_t > prior_volume15_t
volume_pressure_component = clip(log(recent_volume5_t / prior_volume15_t) / log(2), 0, 1)
```

### M0 flag and score

```text
trigger = near_high_gate AND compression_gate AND volume_pressure_gate
forecast_score =
  if trigger:
      mean(near_high_component,
           compression_component,
           volume_pressure_component)
  else:
      0
```

There are **zero fitted parameters** and **no calibration**. `forecast_score > 0` is the frozen Trial-1 flag. Ordering, when needed, is score descending then canonical security ID ascending.

## Exact development split

Trial-1 uses **one expanding split definition**. A rolling variant is not an automatic robustness read; changing the training-window mode is material and would consume another trial if inspected.

```text
mode                       = EXPANDING
minimum_training_sessions  = 126
embargo_sessions           = 20
fold_count                 = 4
oos_sessions_per_fold      = 20
```

Required admitted decision-spine length is therefore at least:

```text
126 training + 20 embargo + 4*20 OOS = 226 sessions
```

If real W3/W4 development coverage cannot support the exact plan, Trial-1 does not silently shrink or re-split. The run remains blocked and the coverage fact returns to research governance before any label inspection.

## Deterministic cross-sectional holdout

```text
holdout assignment = hash(
  cross_sectional_holdout_spec_id,
  fixed seed,
  canonical CIQSEC security_id
) mod 5

holdout remainder = 0
```

This is approximately 20% of securities, deterministically assigned without ticker, sector, label, outcome or later membership.

Positive-weight holdout securities:

- never enter fit (Trial-1 has no fit anyway);
- never enter the W5 tuning objective;
- remain scoreable so prediction bytes exist;
- have labels excluded from tuning.

MU/SNDK, if present in W3/W4 traces, remain generic exact identities with `statistical_weight=0`; they may be scored but cannot affect fit, objective, control denominator, or promotion denominator.

## Frozen control definition

Trial-1 does not add a sampled-control or matching hyperparameter.

Primary development control is the full positive-weight, non-holdout, W3-eligible date-local denominator. For each date:

```text
flag_breadth_d = flagged_count_d / eligible_count_d
```

That breadth is the right-tail recall base rate.

For W4 matched-control compatibility, every eligible row carries one constant preregistered stratum:

```text
trial1_control_stratum = ALL_W3_ELIGIBLE
match_columns = (trial1_control_stratum,)
```

Thus W4 emits **all same-session positive-weight ordinary controls**. There is no sector/size matching, old sector map, nearest-neighbor fallback, sampled control count, or post-label rematch.

## Frozen primary development objective

CAGR and Sharpe are not primary Trial-1 search objectives.

Population:

```text
positive-weight
AND non-holdout
AND temporal OOS
```

Right-tail label is W2's frozen 20-session date-local top-5% label.

Per temporal fold:

```text
winner_recall = SUM(flagged_winners) / SUM(winners)
expected_recall_at_breadth =
    SUM(date_winner_count * flag_breadth_date) / SUM(winners)
recall_lift = winner_recall / expected_recall_at_breadth
```

Primary right-tail read is the median `recall_lift` across informative OOS folds.

Lead read is W2/W4 effective TTFLD, with misses fixed at zero:

```text
median_effective_ttfld_sessions
```

Frozen comparison order is lexicographic:

```text
1. maximize right-tail recall lift
2. then maximize median effective TTFLD
```

If fewer than two OOS folds are informative or there are no eligible winner episodes, result status is `NULL`; the charged trial is still consumed.

## Exact source-manifest gate before W2 TRIAL_OPEN

Trial-1 cannot be charged against a placeholder source hash.

The real source manifest must be W3/W4-bound and hash-exact before `TRIAL_OPEN`. Required source-manifest bindings include:

```text
W2 contract SHA-256
W2/W3 risk-set spec ID
W2 primary label spec ID
real market-history payload SHA-256
W3 PIT-authority bundle SHA-256
Trial-1 W4 control-definition SHA-256
W4 development-label custody SHA-256
W4 episode/TTFLD custody SHA-256
decision-spine SHA-256
source-receipt bundle SHA-256
```

At source-manifest construction time:

```text
development_label_visibility_at_manifest = HASHED_NOT_INSPECTED
smoke_statistical_weight                  = 0
holdout_label_tuning_authority            = FORBIDDEN
w6_lockbox_included                       = false
financial_alpha_evidence                  = 0
capital_authority                         = NONE
```

Only after that exact manifest verifies may `prepare_trial1_m0_for_trial_open(...)` materialize the exact W2 variant bytes. That function **does not append** the ledger entry. The actual W2 `append_trial_open(...)` remains a separate explicit action and will consume `1/8`.

## Code freeze for later charge

Current Trial-1 code bundle SHA-256:

```text
92f51a098f2420fd5d76b7307d0aad75a76d0cf10a81934aa48a15a20f43b2bd
```

Bundle members at this freeze:

```text
research/prebreakout_discovery_v1/trial1_m0.py
  2473cd5266b73dda8fe62c9e603959291db70e6a2a4ff30a7ca775ad0e9280d8
research/prebreakout_discovery_v1/contracts.py
  0d736c25496f3263d56a6e903273f0535ee3623992f57e6cb373529d413c1106
research/prebreakout_discovery_v1/walk_forward.py
  32b7707bd073daada11dd52a16e5076c22b17c7a0607b9674ff992df298dad7f
research/prebreakout_discovery_v1/preregistration.py
  3df15dce6e0c14ccf5e8ab65ecf66cadd212f28bc134f5c50ec7790ea9583214
```

When the source manifest arrives, W2 `TRIAL_OPEN.code_sha256` must use this bundle hash **only if every member hash is unchanged**. Any implementation-byte change before opening requires a new code-bundle hash and a refreshed pre-charge candidate receipt. Any scientific change is a material variant.

## Current execution state

```text
mechanics_closed                 = true
trial1_candidate_frozen          = true
exact_real_source_manifest_exists= false
trial_open_appended              = false
material_trials_consumed         = 0
labels_inspected_for_trial1      = false
development_run_performed        = false
w6_lockbox_accessed              = false
financial_alpha_evidence         = 0
capital_authority                = NONE
```

## Validation

- Trial-1 candidate tests: `7/7 PASS`.
- Full current PREBREAKOUT discovery package: `26/26 PASS`.
- Adjacent W3 + W4 + W6 package: `43/43 PASS` on the final current-byte gate.
- Selected Trial-1/W5 compile: PASS.
- Persistent repository scan: no Trial-1 ledger entry / prebreakout Trial JSONL exists.

These are mechanical/custody tests only. No real development result was produced.

## Reopen condition

**Do not run development now.**

Reopen W5 for the Trial-1 result-bearing action only when:

1. real W3 date-local PIT market/risk-set authority exists for the full required development spine;
2. exact W4-bound development-label and episode/TTFLD custody exists without researcher inspection;
3. the exact source manifest above is sealed and verified;
4. current Trial-1 code bytes still match the frozen code bundle (or are re-frozen before label visibility);
5. W2 `TRIAL_OPEN` is appended **before** result inspection and binds the exact implementation, source manifest, feature/transform/model representation, split, holdout and control definition;
6. the ledger then records Trial-1 as consuming one material trial regardless of outcome.

W6 remains closed throughout Trial-1 development.
