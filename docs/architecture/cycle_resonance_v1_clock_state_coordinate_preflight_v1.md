# CRV1 E3 Clock / State-Coordinate Preflight v1

**Date:** 2026-08-12  
**Slice:** `CRV1-E3-CLOCK-STATE-COORDINATE-PREFLIGHT-1`  
**Family:** `CYCLE_RESONANCE_v1`  
**Programme stage:** `E3`  
**Method obligation satisfied:** `L2_CLOCK_STATE_COORDINATE_DECLARATION`  
**Mode:** outcome-blind / pre-L5 / no provider capture  
**Result:** `CLOCK_CONTRACT_PASS`  
**financial_alpha_evidence:** `0`  
**trial debit:** `0`

## Decision to change

Can the already-preregistered CRV1 causal graph be expressed with one frozen, scientifically non-aliased clock/state-coordinate contract before more source, representation, or model work is spent?

Routes were frozen before the preflight:

```text
PASS
  CLOCK_CONTRACT_PASS
  -> CRV1-E4-STRUCTURED-CLOCK-REPRESENTATION-1

FAIL
  -> SIMPLIFY_CRV1_CLOCK_GRAPH
  or PARK_CRV1

UNRESOLVED
  exact missing clock/source dependency named
  -> HOLD_SOURCE
```

The routes are materially different, so the result-first killer rule does not reduce this slice to `DO_NOT_RUN`.

## Result

`CLOCK_CONTRACT_PASS`.

All eight existing CRV1 clocks can be retained without changing the frozen family identity, provided three boundaries are hard:

1. **availability is not an economic clock** — `available_at <= as_of` is an input gate on every clock, never a state direction or a free lag/horizon parameter;
2. **expectation states are not realized business states** — `EARNINGS_REVISIONS_CLOCK` and `EXPECTATION_GAP_CLOCK` remain separately typed expectation/mispricing states even though the coarse v2 role bucket is `ECONOMIC_STATE`;
3. **market confirmation is downstream action state only** — `MARKET_CONFIRMATION_CLOCK` is `ACTION_EXECUTION` and may not establish, repair, or rescue any upstream causal state.

No ninth availability clock is added. No existing CRV1 clock identity is removed or reordered.

## Frozen graph

Core required order remains exactly the existing CRV1 order:

```text
SUPPLY_CAPACITY
-> INVENTORY
-> PRICING
-> UTILIZATION_MARGIN
-> EARNINGS_REVISIONS
-> EXPECTATION_GAP
```

`DEMAND_CLOCK` remains corroborating/state evidence and is **not** inserted as a new required causal edge by E3.

`MARKET_CONFIRMATION_CLOCK` remains downstream recognition/action confirmation. It has no upstream causal edge.

## Clock declaration

| Clock | `clock_type` | v2 role | Frozen semantic state coordinate | Main anti-aliasing rule |
|---|---|---|---|---|
| `SUPPLY_CAPACITY_CLOCK` | `BUSINESS_ECONOMIC_STATE` | `ECONOMIC_STATE` | `SUPPLY_CAPACITY_DISCIPLINE_STATE` | capex alone is not capacity state |
| `INVENTORY_CLOCK` | `BUSINESS_ECONOMIC_STATE` | `ECONOMIC_STATE` | `INVENTORY_BURDEN_NORMALIZATION_STATE` | denominator/write-down/scope changes cannot fake normalization |
| `PRICING_CLOCK` | `BUSINESS_ECONOMIC_STATE` | `ECONOMIC_STATE` | `PRICING_POWER_MIX_STATE` | margin alone is not pricing power |
| `DEMAND_CLOCK` | `CORROBORATING_BUSINESS_ECONOMIC_STATE` | `ECONOMIC_STATE` | `DEMAND_ORDER_TRAJECTORY_STATE` | revenue alone is not demand when price/mix is unresolved |
| `UTILIZATION_MARGIN_CLOCK` | `BUSINESS_ECONOMIC_STATE` | `ECONOMIC_STATE` | `UTILIZATION_OPERATING_LEVERAGE_MARGIN_STATE` | margin may be observed without claiming utilization |
| `EARNINGS_REVISIONS_CLOCK` | `EXPECTATION_STATE` | `ECONOMIC_STATE`* | `CONSENSUS_REVISION_DIRECTION_STATE` | expectation revision is neither publication latency nor realized economics |
| `EXPECTATION_GAP_CLOCK` | `MISPRICING_STATE` | `ECONOMIC_STATE`* | `ECONOMIC_TRAJECTORY_VS_EXPECTATIONS_GAP_STATE` | price/return cannot define the gap |
| `MARKET_CONFIRMATION_CLOCK` | `DOWNSTREAM_MARKET_ACTION_CONFIRMATION` | `ACTION_EXECUTION` | `MARKET_RECOGNITION_ACTION_CONFIRMATION_STATE` | market action state cannot rescue upstream thesis state |

`*` The v2 method has only `DATA_AVAILABILITY | ECONOMIC_STATE | ACTION_EXECUTION`. For the two expectation-side clocks, `ECONOMIC_STATE` is only the coarse state-role bucket. Their `clock_type` is binding and prevents them from being interpreted as realized business-state clocks.

## Global availability law

For every clock:

```text
contributing datum/claim is legal only if available_at <= as_of
max_available_at binds the clock evidence
period_end != available_at
filing_date != automatically available_at
retrieval time cannot backdate source knowledge
crossing the decision cut -> UNOBSERVED / ABSTAIN
```

A data-availability timestamp may never choose a state direction or become a free economic horizon.

## Per-clock scientific declarations

### `SUPPLY_CAPACITY_CLOCK`

- **Coordinate:** relevant supply/capacity discipline as known at the cut.
- **Allowed surfaces:** `fund.capex_q`; source claims `SUPPLY_CAPACITY`, `COMPETITION`, `OTHER_RELEVANT_CYCLE`.
- **Aliasing risk:** capex spend can mean maintenance, growth, timing, or accounting classification rather than actual capacity addition/discipline.
- **Invariance:** the sign has stable meaning only when the evidence actually refers to relevant supply/capacity scope.
- **Falsifier:** capex-only or scope-mismatched evidence cannot establish a capacity state; route that clock to `PARTIAL/MISSING`, not a guessed direction.

### `INVENTORY_CLOCK`

- **Coordinate:** inventory burden / normalization relative to economically relevant business scale and channel context.
- **Allowed surfaces:** `fund.inventory_q`, `fund.revenue_q`; `INVENTORY_CHANNEL` claims.
- **Aliasing risk:** denominator growth, write-downs, reclassifications, or owned-vs-channel scope can mimic normalization.
- **Invariance:** improvement means lower excess inventory burden under compatible units/scope.
- **Falsifier:** denominator-only or accounting/scope-only apparent normalization cannot support the ordered sequence.

### `PRICING_CLOCK`

- **Coordinate:** pricing power / mix direction.
- **Allowed surfaces:** direct `PRICING` / `COMPETITION` claims; margins only as supporting evidence.
- **Aliasing risk:** FX, costs, product mix, or utilization can move margins without a pricing inflection.
- **Invariance:** direct source-bound pricing/mix direction keeps the same sign semantics across industries.
- **Falsifier:** margin/revenue alone cannot be promoted to a pricing state when direct pricing/mix evidence is absent.

### `DEMAND_CLOCK`

- **Coordinate:** demand/order/volume trajectory.
- **Allowed surfaces:** `fund.revenue_q`; `DEMAND`, `GUIDANCE`, `INVENTORY_CHANNEL` claims.
- **Aliasing risk:** revenue can move from price/mix, acquisitions, shipment timing, or recognition timing.
- **Invariance:** a signed demand state requires evidence interpretable as demand/order/volume under stable scope.
- **Falsifier:** if demand cannot be separated from price/mix or recognition effects, remain `PARTIAL/UNOBSERVED`.
- **Graph role:** corroborating only; missing demand does not rewrite the existing core sequence.

### `UTILIZATION_MARGIN_CLOCK`

- **Coordinate:** utilization / operating-leverage / margin state with explicit partial-state semantics.
- **Allowed surfaces:** `fund.gross_margin_q`, `fund.operating_margin_q`, `fund.cash_from_ops_q`; `UTILIZATION`, `MARGIN`, `SUPPLY_CAPACITY` claims.
- **Aliasing risk:** pricing, input costs, accounting timing, or cash-flow timing can mimic utilization effects.
- **Invariance:** margin is a valid observed sub-state; utilization attribution requires its own support.
- **Falsifier:** margin evidence may not be relabeled as utilization when utilization evidence is absent or contradictory.

### `EARNINGS_REVISIONS_CLOCK`

- **Coordinate:** historical source-bound consensus revision direction.
- **Allowed surfaces:** frozen EPS/revenue levels and 30d/90d revision measures; `GUIDANCE` as source-bound supporting evidence.
- **Aliasing risk:** current consensus backfill, coverage changes, or publication latency can masquerade as revision state.
- **Invariance:** revision sign has stable expectation-state meaning only under fixed historical-vintage/source semantics.
- **Falsifier:** unbound/non-PIT consensus semantics make the real clock `UNOBSERVED -> HOLD_SOURCE`; no current-consensus reconstruction is legal.

### `EXPECTATION_GAP_CLOCK`

- **Coordinate:** signed relation between upstream economic trajectory and current observable expectation/guidance trajectory.
- **Inputs:** upstream economic-state clocks + `EARNINGS_REVISIONS_CLOCK` / frozen expectation levels / guidance.
- **Aliasing risk:** price performance, missing expectation state, or different knowledge cuts can fake a gap.
- **Invariance:** positive means economics stronger than the currently observable expectation trajectory under the same cut; negative means weaker.
- **Falsifier:** if either side is missing/contradictory, or market return is needed to assign the sign, the gap is `UNOBSERVED`.

### `MARKET_CONFIRMATION_CLOCK`

- **Coordinate:** completed-market recognition / action-confirmation state.
- **Role:** `ACTION_EXECUTION` only.
- **Allowed surfaces:** completed `market.close`, `market.total_return_1d`, `market.volume`, `market.adv20`, `market.realized_vol20`, `market.sma20`, `market.sma200` available at the cut.
- **Aliasing risk:** momentum can masquerade as causal proof; future/partial-session rows can leak; confirmation can be used as an outcome-like rescue.
- **Invariance:** confirmation changes only downstream action readiness under fixed completed-market semantics.
- **Falsifier:** any implementation that needs this clock to establish/repair an upstream thesis violates E3 and must simplify/reject that edge.

## Missingness law

CRV1 still does **not** require every security to observe all eight clocks.

```text
PRESENT / PARTIAL / MISSING / NOT_APPLICABLE remain explicit
no imputation
no neutral fill
no current-survivor repair
no risk-set shrink to improve observability
no hidden coverage threshold
```

Missingness affects the affected clock and derived state only. A later frozen `CoveragePolicyV1` may decide representation eligibility, but it cannot rewrite `CRV1_US_PRIMARY_COMMON_V1`.

## What E3 does not freeze

E3 freezes meaning, role, source/state coordinates, and scientific anti-aliasing boundaries. It deliberately does **not** choose:

```text
numeric clock transforms
state-score thresholds
inflection thresholds
edge-lag numbers
H / K
model class or hyperparameters
ranking rule
claim-interpreter prompt/model
coverage threshold
```

Those are E4/later implementation choices and must be frozen outcome-blind under the existing search-budget law.

There is no lag/horizon grid or multi-clock bake-off under this family version.

## Next legal slice

```text
CRV1-E4-STRUCTURED-CLOCK-REPRESENTATION-1
```

E4 may encode deterministic `LEVEL / DELTA / INFLECTION / ORDERED_SEQUENCE` representations for these semantic coordinates and freeze one outcome-blind sequence/lag law where needed. It may not open outcomes, capture a standalone W9 source round, silently add a new clock, change the core order, or auto-authorize L5.

The dormant source branch remains separate:

```text
future explicit shared W3/W9 raw CIQ authorization
-> CRV1-E1E2-RISKSET-CUSTODY-ADMIT-1
-> consume already-frozen W9 semantics
```

E3 does not reopen or rerun CRV1 risk-set semantics.
