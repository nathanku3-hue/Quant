# Phase Brief — CRV1 E4 Structured Clock Representation

**Date:** 2026-08-12  
**Mode:** `EXECUTION_PACKET`  
**Owner direction:** open `CRV1-E4-STRUCTURED-CLOCK-REPRESENTATION-1` strictly outcome-blind  
**Execution effect:** scientific representation freeze only; no provider/outcome/model/ranking/L5 authority  
**financial_alpha_evidence:** `0`

## Hierarchy

| Field | Expertise Level | Rationale |
|---|---|---|
| L1 Terminal Zero quantitative research console | Owner / system | Product, Clock #1, and capital authority remain unchanged |
| L2 CRV1 Alpha Family + Research Method | Quant research / architecture | E4 closes scientific representation degrees of freedom under the E3 clock contract |
| L3 E4 Structured Clock Representation Freeze | Scientific representation / PIT governance | One representation per core node, one sequence/lag law, contradiction and missingness semantics |

No new domain is introduced relative to the approved result-first/CRV1 research hierarchy.

## Decision to change

Can the six-clock causal core be represented without leaving a LEVEL/DELTA/INFLECTION/ORDERED_SEQUENCE menu that could later be selected from results?

```text
PASS       representation frozen -> E5 claim-interpreter preflight may later be considered
FAIL       simplify/park CRV1
UNRESOLVED name exact dependency -> HOLD_SOURCE
```

## Cheapest discriminating test

Use only E3 semantic coordinates and the frozen build-spec causal wording to select one representation per required core clock plus one graph-level ordered-sequence law. Do not inspect provider bytes, labels, returns, outcomes, empirical diagnostics, model scores, or ranking.

## Frozen E4 result

```text
SUPPLY_CAPACITY     LEVEL
INVENTORY           DELTA
PRICING             INFLECTION
UTILIZATION_MARGIN  INFLECTION
EARNINGS_REVISIONS  DELTA
EXPECTATION_GAP     INFLECTION

GRAPH               ORDERED_SEQUENCE
```

Core sequence:

```text
SUPPLY_CAPACITY
-> INVENTORY
-> PRICING
-> UTILIZATION_MARGIN
-> EARNINGS_REVISIONS
-> EXPECTATION_GAP
```

All five adjacent edges are required for `ESTABLISHED`. `allowed_skipped_edges=[]`. Missing core clocks create `PARTIAL`; they do not remove a security from the risk set.

One fixed adjacent lag law:

```text
0 <= core_event_at(B) - core_event_at(A) <= 183 calendar days
```

`core_event_at` is first lawful decision-time detection, not a backdated period/event estimate. Same-cut transitions are allowed. No lag grid exists.

`DEMAND_CLOCK` stays corroborating and cannot repair the core. `MARKET_CONFIRMATION_CLOCK` stays downstream `ACTION_EXECUTION` and is excluded from core sequence status.

## Acceptance checks

- [x] One primary representation is selected for each of six required core clocks.
- [x] `ORDERED_SEQUENCE` is graph-level only, not a competing per-clock representation.
- [x] Required edges, skipped-edge law, contradiction law, missing-clock law, and one fixed lag law are explicit.
- [x] No all-eight-observed requirement; missing core clocks remain `PARTIAL` without risk-set rewrite.
- [x] Demand remains corroborating; market confirmation remains downstream-only.
- [x] No provider capture, W9 reopen, outcome/return/label read, model fit, ranking, automatic L5, trial debit, broker action, or capital authority.
- [x] External validation is green: both E4 JSONs + loop JSON parse; `tests/cycle_resonance_v1`=`6/6 PASS`; scoped `git diff --check` PASS.
- [x] Thin SAW evidence published in the same round.

## Forbidden scope

```text
representation or lag grid
outcome-selected transform
W9 reopen / provider capture
model fitting / ranking
returns or labels
automatic L5
capital / broker action
CRV1 risk-set or 252d outcome rewrite
```
