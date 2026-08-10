# PREBREAKOUT FailurePacketV1 — Negative-Knowledge Stage

Date: 2026-08-10
Family: `PREBREAKOUT_DISCOVERY_v1`
Stage: `FailurePacketV1`
Authority: `DEVELOPMENT_NEGATIVE_KNOWLEDGE_ONLY_ZERO_FINANCIAL_AUTHORITY`
Trial cost: `0`

## Purpose

`FailurePacketV1` exists so a failed charged development trial can continue to produce lawful negative knowledge without escalating authority. It consumes only evidence that was already legally opened by Trial #1 plus retained historical diagnostics and the already-frozen successor observable manifest.

The stage is not a successor trial, not a model-selection loop, not an acceptance gate, and not a data-acquisition authorization. It may diagnose why Trial #1 failed and what data would be required to validate the already-frozen successor causal states. It may not use those outcomes to change any causal edge, sign, lag, threshold, `SelectionBudgetV1`, or successor model definition.

## Authority boundary

The following remain fixed for the entire stage:

```text
CAPTURE                         = NO-GO
SUCCESSOR_EMPIRICAL_TRIAL       = NO-GO
SUCCESSOR_PREDICTION_CLOCK      = NO-GO
W6                              = HOLD_UNTOUCHED
TRIAL_COST                      = 0
FINANCIAL_ALPHA_EVIDENCE        = 0
CAPITAL_AUTHORITY               = NONE
CAUSAL_EDGE/SIGN/LAG_MUTATION   = FORBIDDEN
THRESHOLD_MUTATION              = FORBIDDEN
SELECTION_BUDGET_MUTATION       = FORBIDDEN
SUCCESSOR_MODEL_MUTATION        = FORBIDDEN
```

The stop applies to authority escalation, not to development-only learning from already-opened bytes. Trial #1 can never be refunded, reopened, rescued, or relabeled as a successful discovery trial.

If the Trial #1 market signal is ever tested later as a downstream market-confirmation variable, that use requires a separately preregistered experiment. The defensive result discovered here is outcome-visible development evidence and is therefore never untouched evidence for that future test.

## Admitted inputs

The stage may read only:

- the closed Trial #1 development result and W5 temporal-OOS predictions;
- the already-opened development label and flag projection bytes;
- W4 winner/false-winner statistical staging bytes;
- the W3 MU/SNDK B-minus-1 proof bundle and admitted pre-W6 market history used by the existing independent smoke checker;
- retained A2 and Winner Capture Diagnostic v0 bytes for cross-system diagnosis only;
- frozen `ECONPHYSICS_PREBREAKOUT_v1` PIT observable manifest for a demand/observability map only.

It may not read W6, call a provider, append a trial/search ledger, start a new prediction tape, alter the sealed Trial #1 Atlas bytes, or change the successor methodology freeze.

## MU/SNDK smoke correction

The W4 statistical Atlas remains immutable evidence. Its 2,381 statistical winner episodes, 909 detections, 1,472 misses, matched-control census, and Trial #1 statistical close are not reopened.

One smoke-only field is superseded. The original Atlas implementation computed `smoke_traces.any_legitimate_prebreakout_flag` with an extra `winner_label=True` condition. That violates the engineering-smoke law: every PIT-eligible MU/SNDK breakout-B episode must be evaluated at zero statistical and promotion weight regardless of its winner label.

The corrected law is:

```text
eligible smoke episode
= exact MU/SNDK identity
AND W3 PIT-eligible breakout-B / B-minus-1 proof
AND candidate flag session <= B-minus-1

winner_label is not an input
statistical_weight = 0
promotion_denominator_weight = 0
```

The independent checker is the superseding smoke truth. On the Trial #1 development range it has 19 checkable episodes: 3 with a legitimate pre-B flag and 16 without one; four later episodes remain deferred. The sealed Atlas smoke numbers must not be used as acceptance truth.

## Required diagnostics

### 1. Temporal-OOS ranking and monotonicity

Reuse the exact W5 temporal-OOS prediction keys and matured-label denominator. Define a trigger as `forecast_score > 0` and retain the original fold boundaries. Report:

- winner rate in the full matured temporal-OOS universe;
- winner rate and lift inside triggers;
- each of the four fold lifts;
- monthly trigger lift;
- five pooled trigger-score quintiles, including winner rate and lift versus the same OOS base rate.

This is a diagnosis of ranking information. It cannot be used to choose a new threshold or score transformation.

### 2. Winner miss taxonomy

For every W4 statistical `MISSED_WINNER`, inspect only the already-opened `B-20...B-1` feature rows and assign exactly one hierarchical leaf:

1. `NO_READY_MARKET_HISTORY`;
2. `NEVER_NEAR_HIGH` among episodes with READY history;
3. `NO_COMPRESSION_COMPONENT` after near-high exists;
4. `NO_VOLUME_PRESSURE_COMPONENT` after near-high + compression exist;
5. `COMPONENTS_PRESENT_SEPARATELY_NO_COMPONENT_SYNC` when all three component types occur somewhere in the window but never on the same row;
6. `COMPONENT_SYNC_BUT_NO_LEGAL_TRIGGER` when all three are positive on at least one same row but the frozen legal trigger is still absent.

The taxonomy is descriptive only. A leaf count may create a data/representation demand, never a post-result rule change.

### 3. Lead shape and winner convexity

For detected statistical winners, report the exact lead distribution from first legitimate pre-B flag to breakout B.

For all 2,381 statistical winner episodes, attach the already-opened B-minus-1 20-session forward return, form four payoff quartiles, and report detection rate by payoff quartile plus detected-versus-missed winner medians. This tests whether the representation systematically under-captures the largest economic transitions; it does not redefine the winner label.

### 4. False-winner persistence and catastrophic downside

For positive-weight W4 false-winner rows, report identity persistence, consecutive-session streaks, and identity/date concentration.

For matured temporal-OOS nonwinners, compare triggered versus ordinary rows on 20-session forward mean/median and catastrophic downside rates. Date-local bottom-tail labels are formed on the complete eligible matured development population first, then projected into the temporal-OOS rows. For bottom 5%, use `K=ceil(0.05*N_date)` with deterministic return-ascending/security/trading-item ordering. Also report bottom 1% and fixed `<=-20%` / `<=-40%` rates.

These quantities are allowed to establish a defensive-quality diagnostic, not a winner-discovery success.

### 5. Cross-A2 / Trial #1 right-tail clipping audit

Compare only retained evidence:

- Trial #1 winner-payoff capture and downside diagnostics;
- A2 Parent-versus-Child return/Sharpe dilution, drawdown/CVaR improvement, 20d clipped-winner rate, winner gross give-up, and the retained largest-winner contribution gap.

The only permitted conclusion class is a system-level diagnostic hypothesis such as `CONVERGENT_DIAGNOSTIC_RIGHT_TAIL_CLIPPING_RISK_NOT_SYSTEM_PROOF`. It cannot tune Parent/Child or the successor.

### 6. `ECONPHYSICS_PREBREAKOUT_v1` observability demand map

Map each already-frozen causal node into one of:

- existing PIT authority/capability;
- partial capability with direct state still unobserved;
- source-level missing/unobserved;
- downstream-only market state.

The map may identify which missing observables block state-transition validation. It may not authorize capture or add/delete/rewrite a node. Market confirmation is explicitly downstream-only and cannot substitute for missing economic state.

## Role split

The result must preserve both statements simultaneously:

```text
DISCOVERY          = FAIL
DEFENSIVE_QUALITY  = DIAGNOSTIC_POSITIVE
```

A useful defensive residual does not rescue Trial #1 as a winner-discovery model. Conversely, a discovery failure does not require discarding lawful information about downside/market quality.

## Current retained result

The 2026-08-10 packet reproduces the closed Trial #1 development truth:

- matured temporal-OOS rows: `280,198`;
- winner rate: `5.7120%`; trigger winner rate: `3.9365%`; trigger lift: `0.6892`;
- fold lifts: `0.7586 / 0.8133 / 0.5293 / 0.6728`; median `0.7157`;
- every observed month has trigger lift below `1`;
- all five trigger-score quintiles are below base rate and the highest-score quintile is the worst;
- 1,472 misses: `63 / 526 / 178 / 50 / 610 / 45` across the six hierarchical leaves above;
- payoff-quartile detection: `43.79% / 45.04% / 36.30% / 27.56%`;
- detected winner 20d median `44.49%`; missed winner median `51.54%`;
- triggered nonwinner 20d mean/median `-1.26% / +0.10%` versus ordinary nonwinner `-3.12% / -1.18%`;
- date-local bottom-5% rate `2.27%` versus `5.56%`, ratio approximately `0.408`.

This result supports the diagnosis that the frozen market-only representation lacks winner-ranking information and is anti-convex, while retaining useful defensive/market-quality information.

## Mechanical surface

Implementation:

- `research/prebreakout_discovery_v1/failure_packet_v1.py`
- `scripts/prebreakout_failure_packet_v1.py`

Evidence:

- `docs/context/e2e_evidence/prebreakout_failure_packet_v1_20260810.json`

Focused regression covers the smoke-law correction and FailurePacket authority/demand-map sentinels. The script writes only the diagnostic packet and otherwise operates read-only over retained evidence.
