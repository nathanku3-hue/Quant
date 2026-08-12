# CYCLE_RESONANCE_v1 — E4 Structured Clock Representation Freeze

**Date:** 2026-08-12  
**Slice:** `CRV1-E4-STRUCTURED-CLOCK-REPRESENTATION-1`  
**Mode:** outcome-blind / pre-L5  
**Status:** `REPRESENTATION_CONTRACT_PASS`  
**Financial alpha evidence:** `0`  
**Trial debit:** `0`

## Decision to change

Can the six-clock CRV1 causal core be expressed with one minimal deterministic representation and one fixed ordered-sequence/lag law before claim/model engineering, or should CRV1 be simplified/parked?

Routes were preregistered before the freeze:

```text
PASS       REPRESENTATION_CONTRACT_PASS
           -> preferred next slice CRV1-E5-CLAIM-INTERPRETER-CONTRACT-PREFLIGHT-1
           -> not auto-opened

FAIL       SIMPLIFY_CRV1_CLOCK_GRAPH_OR_PARK_CRV1

UNRESOLVED name exact missing representation/source dependency
           -> HOLD_SOURCE
```

The routes differ, so the result-first killer rule does not zero the slice.

## What E4 freezes

E3 already froze what each clock means. E4 closes only the representation degrees of freedom that the existing CRV1 build spec intentionally leaves without defaults:

- one primary representation for each required six-clock core node;
- the graph-level `ORDERED_SEQUENCE` representation;
- required versus skipped core edges;
- contradiction handling;
- missing-clock behavior;
- one fixed adjacent sequence-lag law.

E4 does **not** freeze a model, ranking rule, outcome threshold, provider route, risk-set rebind, or L5 run.

## Minimal six-clock representation

| Core clock | Frozen primary representation | Why it is the minimum |
|---|---|---|
| `SUPPLY_CAPACITY_CLOCK` | `LEVEL` | Supply/capacity discipline is the causal starting condition; requiring an observed turn would incorrectly exclude already-disciplined states. |
| `INVENTORY_CLOCK` | `DELTA` | Normalization is directional change in inventory burden, not an absolute inventory level. |
| `PRICING_CLOCK` | `INFLECTION` | The preregistered mechanism explicitly calls for a pricing inflection. |
| `UTILIZATION_MARGIN_CLOCK` | `INFLECTION` | The mechanism explicitly calls for utilization/operating-leverage and margin inflection. |
| `EARNINGS_REVISIONS_CLOCK` | `DELTA` | Revisions are changes in expectation state; a level would collapse current consensus with the revision process. |
| `EXPECTATION_GAP_CLOCK` | `INFLECTION` | The core ends in gap resolution; categorical inflection can express `UPSTREAM_AHEAD -> ALIGNED` without inventing a fitted continuous gap. |

`ORDERED_SEQUENCE` is **not** a seventh competing node transform. It is the one graph-level composite over the six frozen node representations.

No LEVEL/DELTA/INFLECTION bake-off remains open under this E4 identity. A later alternative is a new representation version/search-budget entry before any result inspection.

## Per-clock deterministic semantics

### Supply / capacity — LEVEL

Favorable state is `POSITIVE_DISCIPLINE_LEVEL`: lawfully source-bound evidence indicates disciplined/tightening relevant supply or capacity. Generic capex direction cannot establish this state.

The core event time is the first decision cut where the state is `PRESENT` and favorable. This is a decision-time detection stamp, not a backdated economic-occurrence estimate.

### Inventory — DELTA

Favorable state is `POSITIVE_NORMALIZATION_DELTA`: inventory burden is improving under consistent period, units, business scale, and channel scope.

Where numeric inventory/revenue evidence is lawful, direction may be formed from the comparable burden pair. Denominator-only changes, write-downs, or incompatible scope do not count as normalization. Future claim interpretation may corroborate only after its own bytes/procedure are frozen.

### Pricing — INFLECTION

Favorable state is `POSITIVE_PRICING_INFLECTION`: source-bound pricing/mix state moves from `NEGATIVE|NEUTRAL` to `POSITIVE` on sequential lawful cuts.

Margin, FX, input-cost, or product-mix movement alone cannot create the pricing turn.

### Utilization / margin — INFLECTION

Favorable state is `POSITIVE_UTILIZATION_MARGIN_INFLECTION`: the joint E3 utilization/operating-leverage/margin state moves from `NEGATIVE|NEUTRAL` to `POSITIVE` with `PRESENT` coverage.

E3 remains controlling: margin-only or utilization-only evidence is `PARTIAL`, not a fabricated joint clock. A partial joint clock cannot satisfy an `ESTABLISHED` core sequence.

### Earnings revisions — DELTA

Favorable state is `POSITIVE_CONSENSUS_REVISION_DELTA` under exact PIT historical-vintage semantics.

E4 deliberately does **not** choose a 30d versus 90d winner or EPS versus revenue winner. For the allowed revision measures, all observed non-zero directions must agree for a signed core state; opposing non-zero directions are `MIXED/CONTRADICTED`; all-zero is neutral; no lawful revision observations is unknown. There are no weights and no outcome-selected subset.

### Expectation gap — INFLECTION

Favorable state is `POSITIVE_GAP_RESOLUTION_INFLECTION`: a lawful prior `UPSTREAM_AHEAD` state moves to `ALIGNED` using same-cut-compatible upstream economic and expectation states.

E4 does not infer within-category gap magnitude. Market price, return, or market-confirmation state is forbidden as an expectation-gap input.

## Ordered-sequence law

Frozen graph:

```text
SUPPLY_CAPACITY LEVEL
-> INVENTORY DELTA
-> PRICING INFLECTION
-> UTILIZATION_MARGIN INFLECTION
-> EARNINGS_REVISIONS DELTA
-> EXPECTATION_GAP INFLECTION
```

All five adjacent core edges are required for `ESTABLISHED` status:

```text
SUPPLY_CAPACITY -> INVENTORY
INVENTORY -> PRICING
PRICING -> UTILIZATION_MARGIN
UTILIZATION_MARGIN -> EARNINGS_REVISIONS
EARNINGS_REVISIONS -> EXPECTATION_GAP
```

`allowed_skipped_edges = []` for `ESTABLISHED` status. Missing intermediate clocks do not create shortcut edges; they produce `PARTIAL` sequence state.

### One fixed lag law

Sequence identity:

```text
CRV1_CORE6_DETECTION_ORDER_MAX183D_V1
```

For every required edge `A -> B`:

```text
0 <= core_event_at(B) - core_event_at(A) <= 183 calendar days
```

`core_event_at` is the first decision cut where the frozen favorable representation is lawfully detectable with `available_at <= cut`. Same-cut transitions are allowed.

`183 calendar days` is one preregistered approximately two-quarter mechanistic prior per adjacent edge. It is **not** the 252-trading-day outcome horizon and was not selected from outcomes. There is no lag grid. Changing the lag requires a new representation version/search-budget entry before result inspection.

## Sequence states

```text
ESTABLISHED
  all six favorable core events PRESENT
  all five required edges ordered and <=183d
  no contradiction

PARTIAL
  at least one core event MISSING/PARTIAL/UNKNOWN
  OR an otherwise ordered edge is >183d
  AND no observed causal reversal/contradiction exists

CONTRADICTED
  observed downstream favorable event precedes its observed predecessor
  OR predecessor reverses unfavorable before downstream detection
  OR a required core clock is internally CONTRADICTED

NOT_ESTABLISHED
  lawful observed states exist but no favorable sequence progress exists
```

Missingness alone is never negative evidence.

## Demand and market confirmation

`DEMAND_CLOCK` remains corroborating only. It cannot satisfy a missing core node, create a shortcut edge, repair a contradiction, or promote `PARTIAL` to `ESTABLISHED`. E4 does not choose a required demand transform because demand is not part of the six-clock required core.

`MARKET_CONFIRMATION_CLOCK` remains downstream `ACTION_EXECUTION` only. It is excluded from core sequence status and cannot establish, reorder, repair, or rescue the six-clock causal core. E4 does not choose a core market-confirmation transform.

## Missingness and risk-set law

A security is not required to observe all eight canonical clocks. E4 is stricter only about the meaning of `ESTABLISHED` six-clock sequence status: all six required core events must be lawfully present for that label.

If any required core clock is missing/partial, the security stays in the CRV1 risk set and the sequence is `PARTIAL`. There is no imputation, survivor repair, denominator shrink, neutral fill, or hidden coverage threshold.

## Disposition

```text
terminal = REPRESENTATION_CONTRACT_PASS
```

The core can be represented without changing CRV1 family identity, risk-set semantics, primary outcome, or primary horizon. The freeze uses no provider capture, outcome/return/label read, result-bearing diagnostic, model fitting, ranking, L5 authorization, trial debit, broker action, or capital authority.

Preferred next scientific slice, **not automatically authorized**:

```text
CRV1-E5-CLAIM-INTERPRETER-CONTRACT-PREFLIGHT-1
```

That future slice should freeze only the smallest deterministic source-claim interpretation procedure needed to supply the E4 clock representations. W9 remains closed unless a separately authorized shared W3/W9 raw CIQ round occurs.
