# ECONPHYSICS × WINNER_SELECTION Integration Lock — 2026-08-10

**Lock ID:** `PREBREAKOUT_ECONPHYSICS_WINNER_SELECTION_INTEGRATION_LOCK_v1`

**Status:** `LOCKED`

**Scope:** local destructive recut of the PREBREAKOUT research path only. This does not reopen the broader endgame, Clock #1, Parent/Child, VSB confirmation, W6, replication, PAPER, or capital authority.

**financial_alpha_evidence:** `0`

**capital_authority:** `NONE`

## 1. Governing rule

> **Forecast winners through causal economic state, not by fitting winner outcomes directly.**

More precisely:

> **Economic physics generates the state representation; winner selection converts that state into cross-sectional capital priority; market outcomes falsify and calibrate confidence boundaries, but do not invent the causal mechanism.**

The prohibited behavior is adaptive outcome-fitting of the mechanism. Cross-sectional winner selection itself is required: without a ranking/allocation layer, the system is economic research rather than an Alpha system.

## 2. Integrated Alpha chain

```text
economic physics
→ causal economic state
→ expectation gap
→ cross-sectional winner selection
→ market confirmation / execution timing
→ continuation / exit
→ realized right-tail capture
```

Each layer has separate authority and may not silently absorb the role of another layer.

### 2.1 `ECON_STATE_v1` — cause model

Purpose: estimate the real economic state and state transition of each company/industry using information that was PIT-available at the decision cut.

Canonical causal domains include, where economically applicable:

```text
capacity / capacity additions / closures
inventory / inventory digestion / channel stock
pricing / price realization / mix
utilization / throughput
input costs / unit economics
margin / operating leverage
orders / backlog / bookings / cancellations
revisions / guidance / estimate trajectory
capital cycle / supply response
```

The graph may include industry-specific branches, but every edge must be justified by an ex-ante economic mechanism and mapped to an explicit PIT observable or explicit `UNOBSERVED` state. Outcome-visible market winners may falsify the graph; they may not create an edge, choose a sign, choose a lag, or choose a threshold.

### 2.2 `EXPECTATION_GAP_v1` — mispricing model

Purpose: compare the trajectory implied by the causal economic state with the trajectory already embedded in consensus/market expectations.

Core Alpha object:

```text
economic_reality_improvement - priced_expectation_improvement
```

A strong business state with no expectation gap is not automatically high Alpha priority. A moderate state transition with a large positive expectation gap may rank higher.

### 2.3 `WINNER_SELECTION_v1` — decision model

Purpose: rank the complete PIT-eligible cross-section by capital/attention priority using only representations lawfully produced upstream.

Primary output:

```text
alpha_priority_score
```

Conceptual composition:

```text
alpha_priority_score = f(
    econ_state,
    state_transition_strength,
    expectation_gap,
    persistence,
    downside_asymmetry,
    confidence / observability
)
```

This is a cross-sectional ranking/selection layer. It is allowed and required. It must not use top-5% winner labels, MU/SNDK outcomes, W4/W5 winner decompositions, or post-hoc market-pattern enrichment to invent upstream economic features.

### 2.4 `MARKET_CONFIRMATION_v1` — recognition / timing model

Purpose: determine whether the market has begun to recognize the economic transition and whether entry is currently capturable.

Price, volume, volatility, breadth, and VSB-style signals are legal here as measurement/confirmation/execution-timing inputs. They are not permitted to substitute for the economic cause model or to re-enter `ECON_STATE_v1` as hindsight-discovered discovery features.

`VSB_CONFIRMATION_v1` remains a separate frozen confirmation component. It is not PREBREAKOUT discovery authority and is not retuned by this lock.

### 2.5 `CONTINUATION_EXIT_v1` — hold / exit model

Purpose: decide whether the causal state and expectation gap remain open after entry.

Hold/exit questions include:

```text
Is the favorable economic transition still active?
Is the expectation gap closing or closed?
Has supply response / capacity response invalidated the thesis?
Has price moved beyond the remaining economic gap?
Has a preregistered economic falsifier fired?
```

This layer prevents early clipping of right-tail winners without granting price action authority to invent the original thesis.

## 3. Outcome boundary

### 3.1 Allowed uses of market outcomes

Top-5% winner labels, Recall/Lift@K, Precision@K, TTFLD, false winners, missed winners, catastrophic false winners, right-tail wealth capture, and `I vs I+X` are external falsification and selection-quality measurements.

They answer:

```text
Did the causal state representation identify economically important transitions?
Did the ranking convert those states into useful cross-sectional priority?
Was the signal early enough to matter?
How many wrong names were prioritized?
Did confirmation/timing improve capturability?
Did continuation/exit preserve the right tail?
```

They do not answer:

```text
Which causal variable should exist?
Which direction an economic edge should have?
Which lag/window/threshold should be chosen because it caught past winners?
Which famous winner should be special-cased?
```

### 3.2 Trial #1 interpretation

`PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1` is a legitimate preregistered experiment and remains permanently charged `1/8`, but it is closed as a failed **market-behavior discovery branch**.

Its W5 median recall lift of `0.71570953472408605` means:

> A price/volume market-state proxy, used by itself as the PREBREAKOUT winner-selection representation, did not outperform its breadth baseline on the frozen development test.

It does **not** imply that winner selection is invalid. It implies that winner selection needs causal economic inputs rather than a market-pattern proxy standing in for the economic state.

No Trial #1/W4/W5 decomposition may be used to choose the causal graph, state variables, signs, transition laws, lags, or thresholds of the successor mechanism.

## 4. MU / SNDK boundary

MU and SNDK remain integration smoke only:

```text
statistical_weight = 0
promotion_denominator_weight = 0
special-case feature / threshold / branch = FORBIDDEN
```

The legal integration question becomes:

> Given only information available at the time, did the causal economic state + expectation-gap + selection system place MU/SNDK into the appropriate activation/attention region before their algorithmic breakout reference event?

Their answers may expose an integration defect or observability gap. They may not define the mechanism.

## 5. Evaluation law retained externally

The following remain legal external evaluation/falsification constructs for the PREBREAKOUT programme unless separately changed by an explicit future scientific contract:

```text
exact PIT date-local universe
exact CIQSEC + Trading Item identity
algorithmic breakout reference B
B-1 exact-listing clock
TTFLD
20d top-5% primary winner label
10d top-5% secondary winner label
Precision / Recall / Lift@K
false / missed / catastrophic false winners
right-tail wealth capture
I vs I+X incremental value
```

They are downstream measuring devices. They are not upstream feature generators.

## 6. New mechanism freeze required before any new material trial

**The next correct action is not Trial #2.**

Before any new material PREBREAKOUT trial/search charge, freeze a successor causal contract for `ECONPHYSICS_PREBREAKOUT_v1` containing at minimum:

1. causal graph and economic rationale for every edge;
2. PIT observable manifest with source, field, unit, release/availability clock, revision/vintage law, missingness state, and identity binding;
3. state definitions and state-transition laws;
4. expectation-gap definition and consensus/market-expectation observables;
5. cross-sectional winner-selection mapping from state representation to `alpha_priority_score`;
6. invariance assumptions — what must remain stable across time/industry/regime for the mechanism to be meaningful;
7. explicit economic falsifiers and invalidation falsifiers;
8. market-confirmation boundary and forbidden feedback from market outcomes into the cause model;
9. continuation/exit boundary;
10. Trial/Search custody, with no refund/reset of the already consumed Trial #1 charge.

Until that freeze is complete:

```text
new PREBREAKOUT material trial = FORBIDDEN
Trial #2 open = FORBIDDEN
new adaptive winner-pattern search = FORBIDDEN
W6 open = FORBIDDEN
provider spend to test an unfrozen mechanism = FORBIDDEN
```

The existing `1/8` Trial #1 charge remains permanent. This lock does not reset the budget or authorize a new budget. Any successor budget semantics must be explicit in the causal-contract freeze before another open is possible.

## 7. Destructive recut

Current PREBREAKOUT authority is recut as follows:

```text
PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1
  → historical failed market-behavior branch / no-rescue / 1-of-8 permanently charged

PREBREAKOUT_DISCOVERY_v1 as market-pattern search identity
  → superseded for new mechanism design

ECONPHYSICS_PREBREAKOUT_v1
  → next causal research identity; NOT YET TRIAL-AUTHORIZED

ECON_STATE_v1
EXPECTATION_GAP_v1
WINNER_SELECTION_v1
MARKET_CONFIRMATION_v1
CONTINUATION_EXIT_v1
  → required integrated component decomposition for the successor contract
```

Old Trial #1 artifacts remain immutable evidence and custody. They are not deleted, rewritten, relabeled as econphysics evidence, or used to seed a new technical-feature search.

## 8. W6 / capital boundary

```text
W6 consumed = false
W6 label surface opened = false
Trial #1 may not access W6
financial_alpha_evidence = 0
capital_authority = NONE
broker orders = FORBIDDEN on this path
```

Trial #1 failed development and therefore has no W6 authorization. The local causal recut creates no exception.

## 9. Final lock statement

> **Econphysics defines why. Expectation gap defines mispricing. Winner selection defines where to allocate attention/capital. Market state defines when. Continuation defines how long. Right-tail evidence decides whether the integrated system survives. Outcome data may falsify the system and measure selection quality, but may not invent the causal mechanism.**
