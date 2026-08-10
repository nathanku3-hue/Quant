# ECONPHYSICS_PREBREAKOUT_v1 — Causal Methodology Contract

**Contract ID:** `ECONPHYSICS_PREBREAKOUT_v1_CAUSAL_CONTRACT`

**Date frozen:** 2026-08-10

**Status:** `FROZEN / METHODOLOGY_ONLY / NO_CAPTURE / NO_EMPIRICAL_TRIAL_AUTHORITY`

**Scientific identity:** `ECONPHYSICS_PREBREAKOUT_v1`

**Predecessor evidence:** `PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1 = CLOSED / FAIL / 1-of-8 permanently charged`

**W6:** `HOLD / UNTOUCHED`

**financial_alpha_evidence:** `0`

**capital_authority:** `NONE`

**Related lock:** `docs/architecture/econphysics_winner_selection_integration_lock_20260810.md`

**PIT observable manifest:** `docs/architecture/econphysics_prebreakout_v1_pit_observable_manifest.json`

---

## 0. Binding board interpretation

Trial #1 is a valid scientific failure of the market-only PREBREAKOUT representation. It is not a data/PIT/custody failure and it is not evidence that winner selection is impossible.

The successor therefore keeps the winner-selection problem and replaces the upstream information engine:

```text
ECON_STATE_v1
→ EXPECTATION_GAP_v1
→ WINNER_SELECTION_v1
→ MARKET_CONFIRMATION_v1
→ CONTINUATION_EXIT_v1
→ right-tail / incremental falsification
```

The contract is frozen before any new provider capture, material trial, W6 access, or successor outcome join.

No result from Trial #1, W4/W5 decomposition, MU, or SNDK may be used to choose a causal variable, edge, sign, lag, threshold, or special case in this contract.

---

## 1. Authority reuse and separation

The fastest lawful path reuses the existing CRV1 causal vocabulary and Alpha-PIT observable semantics while keeping family authority separate.

### Reused

```text
CRV1 causal vocabulary:
  supply / capacity discipline
  inventory normalization
  pricing / mix
  utilization / throughput
  margin / operating leverage
  revisions / guidance
  expectation gap

Alpha-PIT row semantics:
  exact permanent identity
  observed_at
  available_at
  source receipt binding
  unit
  vintage / revision law
  explicit missingness
  source-bound claims
  observed consensus expectations
```

### Not reused

```text
CRV1 252d winner/outcome authority
CRV1 risk-set authority
CRV1 search ledger
CRV1 prediction ledger
CRV1 empirical model weights
Trial #1 market features as economic-state primitives
AOV-109/current-primary membership as PREBREAKOUT authority
```

Physical raw bytes may later be shared only when the exact provider request and custody identity are legitimately identical. Admission, family identity, horizon, search ledger, prediction ledger, and outcome authority remain separate.

---

## 2. Frozen causal graph

The common PREBREAKOUT causal spine is:

```text
SUPPLY_CAPACITY_STATE
        ↓
INVENTORY_CHANNEL_STATE
        ↓
PRICING_MIX_STATE
        ↓
UTILIZATION_COST_STATE
        ↓
MARGIN_CASH_STATE
        ↓
REVISION_GUIDANCE_STATE
        ↓
EXPECTATION_GAP_STATE
        ↓
WINNER_SELECTION_v1
```

`DEMAND_ORDER_STATE` is a corroborating/causal branch that may affect inventory, pricing, utilization and revenue capture:

```text
DEMAND_ORDER_STATE ─┬→ INVENTORY_CHANNEL_STATE
                    ├→ PRICING_MIX_STATE
                    └→ UTILIZATION_COST_STATE
```

`MARKET_CONFIRMATION_STATE` is downstream only:

```text
WINNER_SELECTION_v1
→ MARKET_CONFIRMATION_STATE
→ capturable entry state
```

Market price/volume/volatility may not feed backward into `ECON_STATE_v1` to repair a missing economic observable.

---

## 3. Edge rationale

| Edge | Ex-ante economic rationale | Invalid shortcut |
|---|---|---|
| Supply/capacity → inventory | Supply growth/discipline changes the rate at which stock accumulates or clears relative to demand. | Treating price strength as proof of capacity discipline. |
| Demand → inventory | Sell-through/order demand changes stock-flow pressure and inventory digestion. | Treating revenue growth alone as complete channel-demand truth. |
| Supply/inventory → pricing | Tightening available supply / normalized channel stock can improve realized pricing or mix; excess stock can pressure price. | Using stock price as product pricing. |
| Demand → pricing | Demand strength/weakness can alter price realization and mix where market structure permits. | Assuming demand strength always implies pricing power. |
| Pricing → utilization/cost | Price/mix and production economics affect economically viable throughput and unit-cost absorption. | Relabeling accounting margin as direct utilization evidence. |
| Inventory/demand → utilization/cost | Inventory digestion and order flow can change production/throughput needs and fixed-cost absorption. | Inferring utilization solely from market volume. |
| Pricing/utilization/cost → margin/cash | Realized price, mix, throughput and unit cost affect gross/operating margin and cash conversion. | Treating one-quarter margin movement as proof of the full upstream mechanism. |
| Margin/cash + revenue → revisions/guidance | Persistent operating inflection changes plausible earnings/revenue trajectory and management/consensus revisions. | Backfilling revision state from realized future earnings. |
| Revisions/guidance + causal trajectory → expectation gap | Alpha requires a divergence between economic trajectory and what consensus currently embeds. | Equating company quality with mispricing or using price momentum when consensus is absent. |
| Expectation gap + persistence + downside + observability → winner selection | Cross-sectional capital priority should favor economically improving, under-recognized, persistent, observable transitions with bounded downside. | Fitting a technical pattern directly to winner labels. |
| Winner selection → market confirmation | After an economic thesis exists, market recognition can improve entry timing/capturability. | Letting confirmation create the thesis. |

The graph is a causal hypothesis contract, not a claim that every edge is empirically true. Subsequent state-transition validation may falsify an edge or node. It may not redefine the edge after winner outcomes are opened under this version.

---

## 4. Applicability law

Every node at every security/date must be classified before scoring as one of:

```text
APPLICABLE
NOT_APPLICABLE
UNOBSERVED
```

`NOT_APPLICABLE` is an economic statement about the business model, not a missing-data convenience. It must be set by a frozen `ApplicabilityProfileV1` based on PIT-safe business-model/industry evidence before winner outcomes are opened.

`UNOBSERVED` means the node is economically applicable but no lawful PIT observable is available with the required identity, source, vintage and availability clock.

Rules:

1. `UNOBSERVED` never becomes neutral/zero evidence.
2. `UNOBSERVED` never authorizes market price to proxy the missing economic node.
3. A node may be `NOT_APPLICABLE` only under a predeclared applicability profile; outcome-visible per-name exceptions are forbidden.
4. A security with insufficient observability for the selection contract must `ABSTAIN`; it is not silently dropped from the full-census denominator.
5. Industry-specific branches require a new frozen applicability/edge manifest before result-bearing use; they may not be added because a historical winner was missed.

---

## 5. PIT observable constitution

The canonical observable manifest is `docs/architecture/econphysics_prebreakout_v1_pit_observable_manifest.json`.

Every accepted economic observation must bind:

```text
source
field / claim / expectation identity
unit
security identity
observed_at
available_at
vintage / revision law
coverage / missingness state
source receipt hash
```

Family-level missingness maps non-present Alpha-PIT states to `UNOBSERVED` except legitimate `NOT_APPLICABLE`.

No forward fill crosses an information-publication boundary unless an explicit field contract permits it. Later revisions are new PIT observations; they never overwrite or backdate prior vintages.

The first implementation preferentially reuses existing Alpha-PIT logical domains:

```text
fund.revenue_q
fund.inventory_q
fund.capex_q
fund.gross_margin_q
fund.operating_margin_q
fund.cash_from_ops_q

EPS_FY1 / EPS_FY2
REVENUE_FY1 / REVENUE_FY2
30d / 90d EPS and revenue revisions

SUPPLY_CAPACITY
INVENTORY_CHANNEL
PRICING
DEMAND
UTILIZATION
MARGIN
GUIDANCE
COMPETITION
```

No new provider capture is authorized by this contract.

---

## 6. Deterministic M0 transform law

M0 is intentionally monotonic and non-fitted.

For structured quarterly observables, when PIT history permits, the only default directional transforms are:

```text
latest_vs_prior = sign(latest PIT-available quarter - immediately prior PIT-available quarter)
yoy_direction   = sign(latest PIT-available quarter - comparable quarter four periods earlier)
```

Ratios such as inventory/revenue may be formed only when units, period semantics and transform identity are explicitly compatible and frozen. No magnitude threshold is learned from winner outcomes.

Source claims retain their observed claim direction and source-bound horizon. Any interpretation procedure is versioned and hash-bound; it may map observed claims to an ordinal economic direction but may not invent an observed fact.

Consensus revisions retain provider-observed sign/direction. Market prices are excluded from M0 economic-state construction.

---

## 7. State and transition definitions

Every economic node emits:

```text
state = NEGATIVE | NEUTRAL | POSITIVE | MIXED | UNOBSERVED | NOT_APPLICABLE
transition = DETERIORATING | STABLE | IMPROVING | INFLECTING_NEGATIVE | INFLECTING_POSITIVE | UNOBSERVED | NOT_APPLICABLE
```

### Evidence classes

```text
OBSERVED_STRUCTURED
OBSERVED_SOURCE_CLAIM
OBSERVED_CONSENSUS
INFERRED_FEATURE
```

Inferred features never masquerade as observations.

### M0 node aggregation

For each applicable node:

- consistent positive observed evidence → `POSITIVE` / `IMPROVING`;
- consistent negative observed evidence → `NEGATIVE` / `DETERIORATING`;
- explicit directional reversal from negative/non-positive to positive → `INFLECTING_POSITIVE`;
- explicit directional reversal from positive/non-negative to negative → `INFLECTING_NEGATIVE`;
- materially conflicting observed evidence → `MIXED`;
- no lawful observation → `UNOBSERVED`.

No fitted weights resolve conflicts in M0. Conflict remains visible.

### Ordered causal progress

`causal_sequence_progress` is the count of satisfied forward edges in the frozen graph, computed only where both adjacent applicable nodes are observed. Missing edges are not assumed satisfied.

A later implementation may use a richer state-space model only under a charged, preregistered successor implementation; it cannot retroactively redefine M0.

---

## 8. Economic-state validation before winner labels

The causal engine must first be tested on its own economic transition targets before any top-5% winner label is used for variable, sign, lag, threshold or model choice.

Legal targets include, where observable:

```text
inventory normalization / deterioration at the next legitimate PIT observation
margin / cash inflection at the next legitimate PIT observation
consensus revision trajectory after the decision cut
revenue/demand capture direction
subsequent source-claim confirmation or contradiction of supply/pricing/utilization state
```

For every node/edge, the state-transition report must publish:

```text
eligible observation count
UNOBSERVED / NOT_APPLICABLE count
transition base rate
directional hit rate / lift versus declared no-information baseline
temporal-fold stability
contradiction count
coverage by industry/applicability profile
```

If a node cannot forecast its declared economic transition target, it cannot be kept merely because it improves winner selection later. The lawful action is `ABSTAIN`, disable that node in a new preregistered version, or close the mechanism/version.

Winner labels remain sealed during this layer.

---

## 9. Expectation-gap law

`EXPECTATION_GAP_v1` compares the direction of the frozen economic trajectory with currently observable consensus/guidance trajectory. It is not a company-quality score.

Canonical state:

```text
POSITIVE_GAP
NONE_OR_PRICED
NEGATIVE_GAP
MIXED
UNOBSERVED
```

M0 rules are ordinal and deterministic:

```text
POSITIVE_GAP:
  economic trajectory = improving / positive inflection
  AND consensus/guidance trajectory is not comparably positive

NONE_OR_PRICED:
  economic and consensus trajectories are directionally aligned
  OR no material divergence is established

NEGATIVE_GAP:
  economic trajectory = deteriorating / negative inflection
  AND consensus/guidance is not comparably negative

MIXED:
  lawful economic or expectation evidence conflicts materially

UNOBSERVED:
  economic trajectory or expectation surface lacks the minimum lawful observability
```

No market-price appreciation/depreciation may substitute for missing consensus in M0. `FORWARD_PE` may be reported as a secondary valuation context only until a separate market-implied expectation transform is preregistered.

---

## 10. Winner-selection mapping

Winner selection remains mandatory and operates over the complete date-local PIT-eligible cross-section.

M0 uses no fitted selection weights.

### Eligibility closure

A security is selection-eligible only when:

```text
at least one applicable upstream causal node is OBSERVED
AND MARGIN_CASH_STATE or REVISION_GUIDANCE_STATE is OBSERVED
AND EXPECTATION_GAP_STATE is not UNOBSERVED
AND no hard economic/custody falsifier is TRIGGERED
```

Otherwise the output is `ABSTAIN` with a deterministic reason. Abstentions remain in coverage reporting and cannot disappear from the denominator.

### Deterministic priority key

Eligible names are ordered lexicographically by:

```text
1. expectation_gap_tier               descending
2. positive downstream confirmation   descending
3. causal_sequence_progress           descending
4. persistence_count                  descending
5. economic_falsifier_burden          ascending
6. observability_ratio                descending
7. permanent security_id              ascending (deterministic tie-break only)
```

`alpha_priority_score` is the date-local cross-sectional percentile rank implied by this frozen priority ordering. It is not a calibrated probability and not a portfolio weight.

A future fitted selector requires a separately charged implementation/search variant. Winner labels may train only that downstream selection layer after the upstream economic representation has independently survived state-transition validation; fitted winner selection may not alter the upstream graph or observables.

### Selection breadth / K

This contract freezes the ranking law but deliberately does not outcome-optimize K. Before the first historical winner-label join, a separate immutable `SelectionBudgetV1` must freeze K/breadth from capital/attention capacity, not from whichever historical K looks best. There is no runtime default K.

---

## 11. Market-confirmation boundary

`MARKET_CONFIRMATION_v1` answers only whether an already-prioritized economic thesis has begun to receive market recognition and whether entry is currently capturable.

Legal inputs may include:

```text
close / total return
volume / ADV20
realized volatility
SMA/trend state
VSB-style frozen confirmation evidence
```

Forbidden:

```text
using market state to create an ECON_STATE node
using Trial #1 feature decomposition to select causal variables
retuning VSB into PREBREAKOUT discovery
post-breakout rescue counted as ex-ante discovery
```

The integrated system must report both `I` (econphysics + winner selection) and `I+X` (plus market confirmation) so confirmation earns its place incrementally rather than by narrative.

---

## 12. Continuation / exit law

`CONTINUATION_EXIT_v1` is a separate downstream component. It may hold or exit only from the frozen thesis state:

```text
causal transition still active?
expectation gap still open?
supply/capacity response now invalidating the thesis?
inventory/pricing/utilization/margin trajectory reversing?
consensus caught up / gap closed?
preregistered economic falsifier triggered?
```

Unrealized P&L alone is not an Alpha input. A continuation component does not inherit discovery authority merely because it improved backtest CAGR.

---

## 13. Invariance assumptions

The following are frozen invariants for v1:

1. information must be PIT-available at the decision cut;
2. permanent security/listing identity is exact and date-local;
3. the direction of each causal edge is economic, not outcome-selected;
4. missingness remains explicit and cannot be repaired by market proxies;
5. the common causal ordering does not change across temporal folds because a winner was missed;
6. applicability may differ by business model only through a frozen pre-outcome profile;
7. winner selection ranks representations produced upstream; it does not rewrite them;
8. market confirmation is downstream and may not feed backward into causal-state construction;
9. Trial/Search debt is append-only and failed attempts are never refunded;
10. W6 and prospective outcomes remain unavailable until the exact frozen successor implementation earns that gate.

If an industry requires a materially different causal order, that is a new explicit branch/version, not a hidden exception.

---

## 14. Falsifiers

### Mechanism falsifiers

```text
STATE_TRANSITION_NO_LIFT
CAUSAL_ORDER_NOT_STABLE
EXPECTATION_GAP_NOT_OBSERVABLE
EXPECTATION_GAP_NOT_INCREMENTAL
SELECTION_NO_RIGHT_TAIL_ENRICHMENT
NO_POSITIVE_EX_ANTE_TTFLD
FALSE_WINNER_BURDEN_UNUSABLE
CATASTROPHIC_FALSE_WINNER_BURDEN_UNUSABLE
MARKET_CONFIRMATION_NOT_INCREMENTAL
CONTINUATION_NOT_INCREMENTAL
INDEPENDENT_REPLICATION_FAIL
PROSPECTIVE_FAIL
NONMONETIZABLE_AFTER_COST_CAPACITY
```

A triggered falsifier closes or demotes the affected version/component. It never authorizes outcome-driven redefinition under the same identity.

### Custody invalidators

```text
PIT_VIOLATION
PREDICTION_AFTER_LABEL
SOURCE_RECEIPT_OR_HASH_DRIFT
IDENTITY_AMBIGUITY_OR_FALLBACK
SURVIVOR_CURRENT_PRIMARY_BACKPROJECTION
SILENT_MISSINGNESS_DROP
OUTCOME_TO_MECHANISM_FEEDBACK
SEARCH_LEDGER_MISSING_OR_RESET
W6_EARLY_ACCESS
```

A custody invalidation is not an economic failure and must be reported separately.

---

## 15. Historical evaluation law retained externally

The successor keeps the existing PREBREAKOUT external measuring devices so the programme does not move the goalposts after Trial #1:

```text
full date-local PIT universe
exact CIQSEC + Trading Item identity
algorithmic breakout reference B
B-1 exact-listing clock
20d top-5% primary winner label
10d top-5% secondary winner label
TTFLD
Precision@K / Recall@K / Lift@K / PR-AUC
missed winners / false winners / catastrophic false winners
right-tail wealth capture
I vs I+X incremental value
```

These outcomes can falsify the frozen integrated system. They cannot define the causal graph.

CAGR/Sharpe remain secondary diagnostics.

MU/SNDK remain zero-weight engineering smoke only. For each PIT-eligible algorithmic B episode, the integration trace must report:

```text
econ-state activation
→ expectation-gap state
→ first alpha-priority inclusion
→ market confirmation
→ B
```

No pre-B inclusion is a `MISS`; invalid input is a deterministic exclusion. Neither outcome permits mechanism rescue.

---

## 16. Development walk-forward and W6 boundary

After lawful PIT data exists and after the economic-state layer is validated:

```text
~4 temporal OOS folds
+ deterministic cross-sectional holdout
```

The causal graph remains fixed. Only preregistered selection/calibration choices may consume successor search budget.

Development reporting must include at minimum:

```text
PIT violations = 0
right-tail lift versus breadth/control
median effective TTFLD
false / catastrophic-false burden
I versus I+X
fold stability
coverage / abstention
```

CAGR/Sharpe are secondary.

Only one frozen survivor may approach W6. W6 remains the existing untouched lockbox and is opened once, only after successor contract/data/implementation/search/prediction bytes are frozen. W6 failure closes that version; no rescue.

---

## 17. Search / Trial custody

Historical debt is immutable:

```text
PREBREAKOUT_SEARCH_v1 Trial #1 consumed = 1/8
refund/reset = FORBIDDEN
```

Successor scientific identity is separate:

```text
successor_search_family_id = ECONPHYSICS_PREBREAKOUT_SEARCH_v1
successor_prediction_scope = ECONPHYSICS_PREBREAKOUT_PREDICTIONS_v1
authorized_successor_material_trials_today = 0
successor_trial_open_today = FORBIDDEN
```

No implicit successor budget ceiling is invented in code or this document. Any future nonzero successor material-trial budget requires a separate owner/CRO authority record before the first `TRIAL_OPEN` and must preserve programme-level disclosure of the predecessor `1/8` failed debt.

M0 methodology work today consumes no material empirical trial because no outcome-bearing search is run and no provider capture is opened.

---

## 18. Frozen pre-production sequence

```text
1. causal contract freeze                           [THIS DOCUMENT]
2. demand-pulled PIT data constitution / capture   [NO-GO TODAY]
3. economic-state transition validation            [winner labels sealed]
4. freeze expectation-gap + selection budget       [no historical K optimization]
5. full-census historical winner evaluation
6. MU/SNDK zero-weight engineering acceptance
7. ~4-fold development walk-forward
8. freeze one survivor
9. W6 once
10. prospective forward test
11. shadow economics
12. PAPER-0 capturability
13. independent replication
14. production/live-capital approval
```

CRV1, Sector Rotation and VSB do not block this critical path. CRV1 supplies reusable causal vocabulary/PIT semantics only; VSB stays in market confirmation; Sector Rotation remains orthogonal.

---

## 19. Today stop line

After this methodology freeze and current-truth synchronization:

```text
CAPTURE = NO-GO
NEW PROVIDER CAPTURE = FORBIDDEN
OLD-FAMILY TRIAL #2 = FORBIDDEN
SUCCESSOR EMPIRICAL TRIAL = FORBIDDEN TODAY
W6 = HOLD / UNTOUCHED
NEW PREDICTION CLOCK = FORBIDDEN TODAY
FINANCIAL ALPHA CLAIM = 0
CAPITAL AUTHORITY = NONE
```

The next lawful PREBREAKOUT action after today is demand-pulled PIT data constitution/capture for the observables required by this frozen contract, under a separately authorized round.
