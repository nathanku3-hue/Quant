# VOL_SQUEEZE_BREAKOUT_v1 — Fast Family #2 Preregistration

**Date:** 2026-08-10  
**Status:** `PARKED / NO_ACTIVE_ENGINEERING / NO_DEDICATED_WORKER / VSB_CONFIRMATION_v1 / CONFIRMATION_ONLY / W7_GUARDIAN_FROZEN / NO_NEW_PREDICTION_CLOCK_TODAY / NO_UNTOUCHED_RESULT / NO_CAPITAL_AUTHORITY`  
**Family ID:** `VOL_SQUEEZE_BREAKOUT_v1`  
**Risk-set spec:** `VSB_US_PRIMARY_COMMON_DAILY_V1`  
**Primary label:** `VSB_RIGHT_TAIL_10D_TOP5_V1`  
**Secondary label:** `VSB_RIGHT_TAIL_20D_TOP5_V1`  
**Financial Alpha evidence:** `0`  
**Relationship to CYCLE_RESONANCE_v1:** independent Alpha Family; no mutation of CRV1  
**Relationship to AOV Lane-2:** A1/A2 may motivate the mechanism but are discovery-visible historical diagnostics only and cannot accept this family.

---

## 0. Purpose

Test a deliberately simple daily price/volume mechanism:

```text
realized-volatility compression
→ latent range pressure
→ upside range escape
→ above-baseline volume participation
→ multi-week right-tail repricing
```

The objective is evidence velocity on an independent mechanism, not a faster variant of `CYCLE_RESONANCE_v1` and not a repair of frozen AOV Rule100/Parent/Child.

The family is accepted only by new untouched/prospective cross-sectional winner-recall evidence. The already-seen AOV A1/A2 outcomes, including named winners, have zero confirmatory authority for this family. Under the 2026-08-10 methodology freeze, M0 is retained only as `VSB_CONFIRMATION_v1`; it has no pre-breakout authority and may not be retuned in place to answer the pre-breakout question.

---

## 1. Authority boundary

```text
family_id = VOL_SQUEEZE_BREAKOUT_v1
family_wip_slot = FAST_FAMILY_2
m0_trial_budget = 1
financial_alpha_evidence = 0
parent_child_mutation = FORBIDDEN
clock_1_outcome_access = FORBIDDEN
a2_requery = FORBIDDEN
broker_orders = FORBIDDEN
capital_policy_authority = NONE
```

M0 is one frozen implementation, not a parameter search. Any material change to the risk set, windows, feature definitions, trigger signs, feature weights, target horizon, winner definition, or acceptance rule consumes new Trial/Search debt and requires a new implementation/version before outcome inspection.

---

## 2. Minimal `FamilyDataContract`

Family #2 opens the second-consumer recut required by `alpha_pit_data_api_v1`; it does not authorize a registry, plugin system, feature store, or provider framework.

```text
family_id                   VOL_SQUEEZE_BREAKOUT_v1
risk_set_spec_id            VSB_US_PRIMARY_COMMON_DAILY_V1
primary_label_spec_id       VSB_RIGHT_TAIL_10D_TOP5_V1
allowed observation surface market.close, market.total_return_1d, market.volume
allowed expectation surface EMPTY
allowed claim surface       EMPTY
```

The immutable contract is defined in `research/alpha_pit_v1/contracts.py`. Alpha PIT artifact manifests hash-bind the contract, and session boundaries reject cross-family artifacts and disallowed surfaces.

The preregistration originally created no VSB provider adapter or runner. The current implementation now closes the family-specific pre-evaluation mechanics without creating a provider platform: a no-network source-admission producer accepts only already-landed same-day CIQ receipts under the frozen U.S.-primary-common law, closes source-bound daily history into the VSB packet, runs the exact frozen feature/model transform, seals the prediction strictly after the knowledge cutoff, and appends it to a hash-chained exclusive-writer prediction tape. Actual provider/network acquisition and all outcome evaluation remain outside this slice.

---

## 3. Objective risk set — `VSB_US_PRIMARY_COMMON_DAILY_V1`

This family MUST NOT use either the AOV high-growth current cohort or the frozen Lane-2 94-security cohort as its research universe.

At every decision cut, membership is independently captured and sealed using only information available at that cut.

Required at `as_of`:

```text
U.S.-listed primary common-equity security/trading identity
permanent identity = CIQSEC:<Capital IQ Security ID>
listing identity = exact SP_TRADING_ITEM_ID / provider primary-listing binding
active/tradable research eligibility known at the cut
unique permanent security mapping
>= 60 prior observed daily market sessions for the frozen transforms
finite positive close on the decision date
finite non-negative volume and finite 1d total return on the decision date
no growth/fundamental/Rule100 eligibility screen
no future-membership condition
no current-survivor back-projection
no ticker/entity/PERMNO fallback
no alternate-listing backfill
```

There is **no liquidity/capacity threshold in V1**. If later economics require one, it must be preregistered as a new risk-set-spec version before result inspection. Capacity/liquidity may be reported diagnostically but cannot silently remove difficult winners from the V1 denominator.

For historical discovery, current `Type`/`Status`/`Primary Issue` fields may not be projected backward. Historical membership is usable only when a source-authorized date-local historical membership/identity receipt exists. Otherwise that period is unavailable, not reconstructed from current survivors.

For prospective collection, the current decision-date universe snapshot is sealed before future labels and becomes the denominator for that prediction date.

---

## 4. Decision clock and execution boundary

```text
prediction_frequency = DAILY
information_cut = completed primary-market close t
prediction_seal = after all allowed t observations are available, before t+1 outcome exists
first_outcome_interval = t → next observed session close
primary_horizon = next 10 observed sessions
secondary_horizon = next 20 observed sessions
```

All features use only observations at or before close `t`. Same-day retroactive execution is forbidden. Source admission now enforces a conservative completed-close gate: `decision_date` must equal the New-York-local `as_of` date, the date must be an admitted 2026 NYSE session, `as_of >= 16:00 America/New_York`, and both risk-set and market source receipts must be retrieved at or after that completed-close boundary. This is intentionally conservative on any early-close session; waiting longer is allowed, sealing before the actual close is not. The family currently emits forecasts only; any later P&L simulation must use the canonical execution/cost policy and remains separate from M0 winner-recall acceptance.

---

## 5. Frozen M0 transform

For security `i` on decision date `t`, using observed sessions only:

```text
rv20(i,t) = sample_std(total_return_1d over observed sessions t-19 ... t)
rv60(i,t) = sample_std(total_return_1d over observed sessions t-59 ... t)

compression(i,t) = ln(rv60(i,t) / rv20(i,t))

prior_high20(i,t) = max(close over observed sessions t-20 ... t-1)
breakout(i,t) = ln(close(i,t) / prior_high20(i,t))

prior_volume_median20(i,t) = median(volume over observed sessions t-20 ... t-1)
volume_expansion(i,t) = ln(volume(i,t) / prior_volume_median20(i,t))
```

Required domains:

```text
rv20 > 0
rv60 > 0
prior_high20 > 0
close_t > 0
prior_volume_median20 > 0
volume_t > 0
```

No zero/NA repair is allowed. A non-finite required transform produces a deterministic `INSUFFICIENT_OR_INVALID_M0_HISTORY` exclusion for that prediction date.

### 5.1 Mechanism trigger

```text
M0_TRIGGER(i,t) =
    compression(i,t) > 0
and breakout(i,t) > 0
and volume_expansion(i,t) > 0
```

The zero thresholds encode the mechanism direction and are not tuned.

### 5.2 Cross-sectional forecast score

On each date, percentile-rank each finite component across the sealed risk set using average rank for ties:

```text
rC = pct_rank(compression)
rB = pct_rank(breakout)
rV = pct_rank(volume_expansion)

raw_score = (rC + rB + rV) / 3
forecast_score = raw_score if M0_TRIGGER else 0
```

The three components receive equal weights. There is no fitted coefficient, model class search, top-N parameter, sector override, fundamental overlay, or ticker-specific branch in M0.

`forecast_score > 0` defines the nonzero-support set. Selection breadth therefore emerges from the preregistered mechanism; it is not tuned to the AOV ~20% support rate.

---

## 6. Frozen labels

For each sealed risk set on decision date `t`:

```text
F10(i,t) = product(1 + r(i,s)) - 1 over next 10 observed sessions after t
F20(i,t) = product(1 + r(i,s)) - 1 over next 20 observed sessions after t
```

Primary winners are the top:

```text
ceil(0.05 * risk_set_count_t)
```

securities by `F10`, sorted by `forward_total_return DESC, security_id ASC` for deterministic ties.

The 20-session label uses the identical top-5% law and is secondary. Incomplete horizons remain `INCOMPLETE_HORIZON`; they are never imputed or silently removed from a denominator that is already declared mature.

Terminal corporate events must use the source-bound terminal-event/cash law rather than survivor filtering or alternate-listing substitution.

---

## 7. Primary acceptance statistic

For matured decision dates `T`:

```text
winner_recall_10d
= sum_t |winner_set_t ∩ support_t|
  / sum_t |winner_set_t|

support_breadth
= mean_t (|support_t| / |risk_set_t|)

winner_recall_lift_10d
= winner_recall_10d / support_breadth
```

If `support_breadth = 0`, lift is defined as `0` for the gate.

M0 is first evaluated only on a **new untouched/prospective freeze** with at least `20` matured primary decision dates. A1/A2 are excluded from the acceptance calculation.

To advance from M0 mechanism screening:

```text
PIT / identity / custody violations = 0
matured primary decision dates >= 20
winner_recall_lift_10d > 1.0
80% moving-block-bootstrap lower bound of lift_10d > 1.0
```

Bootstrap law is frozen before outcomes:

```text
unit = decision date
block_length = 10 consecutive decision dates
replicates = 10000
seed = 20260810
confidence = 0.80 two-sided percentile interval
```

W7 guardian engineering law is also frozen before any result-bearing evaluation:

```text
role = VSB_CONFIRMATION_v1 only
input = VSB-specific matured 10d evaluation receipts from the untouched/prospective VSB evaluation path
before 20 matured dates = return eligibility count only; lift/CI remain hidden / null
bootstrap = non-circular moving blocks over chronologically ordered decision dates
eligible block starts = 0 .. N-block_length
blocks sampled with replacement until >= N observations, then truncate to N
percentiles = deterministic linear Type-7 interpolation
lower bound = 10th percentile (80% two-sided interval)
retune_authority = NONE
prebreakout_authority = NONE
```

Each matured-date record must be a **VSB-specific matured 10d evaluation receipt** and bind the frozen VSB family/implementation/search/10d-label identities, the exact guardian-contract hash, the sealed VSB prediction-batch hash, the VSB evaluation-receipt hash, `prediction_before_label_open=true`, zero custody violations, and the frozen `ceil(0.05 * risk_set_count)` winner count. **PREBREAKOUT W6 evaluator outputs are not valid W7 inputs.** W7 does **not** fetch outcomes or construct labels; that remains VSB evaluation authority. Prediction seals bind the guardian-contract hash so acceptance-law drift cannot silently remain the same M0 identity.

The 20d winner-recall lift is always reported as secondary and is non-blocking for this first fast M0 screen. A mechanism-screen pass is **not** financial-Alpha promotion, capital authority, pre-breakout authority, or permission to mutate M0. Further evidence remains separately required by the programme.

---

## 8. SNDK / MU smoke probes

`SNDK` and `MU` are named diagnostic smoke probes only:

```text
acceptance_weight = 0
special_case_scoring = FORBIDDEN
special_case_universe_admission = FORBIDDEN
```

The generic prospective pipeline must emit, for any requested smoke symbol, one of:

```text
IN_RISK_SET + feature values + trigger state + forecast_score sealed before outcome
or
DETERMINISTIC_RISK_SET_EXCLUSION(reason_code)
```

If a name is in the risk set but has no signal, the generic M0 reason vector must explain it, e.g. `NO_VOL_COMPRESSION`, `NO_BREAKOUT`, `NO_VOLUME_EXPANSION`, or invalid-history/missing-data state. No code may branch on the literal tickers.

Historical AOV evidence that MU repeatedly failed technical eligibility and SNDK had zero Rule100-eligible feature dates remains diagnostic-only and has no VSB pass/fail weight.

---

## 9. Search / Trial Ledger

```text
search_family_id = VSB_M0_SEARCH_v1
implementation_id = VSB_M0_EQUAL_RANK_20_60_20_v1
trial_budget_max = 1
actual_material_trials_allowed_before first untouched result = 1
prediction_ledger_scope = VSB_V1_PREDICTION_LEDGER
trial_ledger_scope = VSB_V1_TRIAL_LEDGER
artifact_namespace = vol_squeeze_breakout_v1/
```

The following each require a new charged implementation/version before evaluation:

- changing `20/60/20` windows;
- changing any trigger sign/threshold;
- changing equal feature weights;
- adding momentum, sector, fundamentals, news, short-interest, options, or market-state inputs;
- adding a liquidity threshold;
- changing 10d primary or top-5% winner law;
- changing the risk-set definition;
- changing the acceptance statistic or bootstrap after result inspection.

---

## 10. Stop / fail-closed conditions

Stop the family evaluation rather than repair evidence when:

```text
risk-set snapshot was not sealed before outcome
family/risk-set/label artifact identity crosses CRV1 or AOV namespaces
provider receipt/hash does not reconcile
identity requires ticker/entity/PERMNO fallback
historical membership would require current-survivor back-projection
required market field is provider NA/non-finite
future horizon is incomplete
M0 implementation hash changed after prediction sealing
Trial Ledger shows undeclared material variants
```

No result under those conditions may count as confirmatory/prospective evidence.

---

## 11. Current execution state

As of preregistration:

```text
Family #2 identity              FROZEN
FamilyDataContract              IMPLEMENTED
M0 formulas                     FROZEN
risk-set semantics              FROZEN
primary/secondary labels        FROZEN
M0 search budget                FROZEN = 1
acceptance rule                 FROZEN
SNDK/MU smoke role              FROZEN / ZERO ACCEPTANCE WEIGHT
VSB source-admission producer   IMPLEMENTED / COMPLETED-CLOSE GATED / NO NETWORK ACQUISITION
VSB PIT packet validator        IMPLEMENTED / PROVIDER-BLIND
VSB 20/60/20 features           IMPLEMENTED / FROZEN M0
VSB deterministic M0 ranker     IMPLEMENTED / ONE MATERIAL TRIAL
VSB prediction runner           IMPLEMENTED / STRICTLY POST-CUT SEAL
append-only prediction tape     IMPLEMENTED / HASH-CHAINED / EXCLUSIVE WRITER
W7 confirmation guardian        FROZEN / FIXTURE-VALIDATED / PARKED / NO OUTCOME ACCESS
W7 active engineering worker    NONE
first real CIQ VSB prediction   NOT YET SEALED / NO NEW PREDICTION CLOCK TODAY
new untouched/prospective data  NOT YET EVALUATED
financial_alpha_evidence        0
capital authority               NONE
```

The 2026-08-10 07:30 ET real-close preflight correctly failed closed because the 16:00 ET primary close had not completed; no provider call or prediction append occurred. Evidence=`docs/context/e2e_evidence/vsb_real_close_preflight_20260810T113026Z.json`. The later methodology freeze supersedes the earlier “capture next” instruction for W7. **Disposition is PARK / NO ACTIVE ENGINEERING:** do not capture, append, rescue, retune, or use VSB for PREBREAKOUT, and assign no dedicated W7 worker. Product/runtime mechanics are parked. Only a future VSB-specific matured-10d evaluation feed may activate the frozen guardian; PREBREAKOUT W6 output cannot. The first result-bearing read remains blocked until at least 20 primary 10d decision dates exist, then uses only the frozen lift/bootstrap gate. A2 and named smoke cases have zero acceptance weight.
