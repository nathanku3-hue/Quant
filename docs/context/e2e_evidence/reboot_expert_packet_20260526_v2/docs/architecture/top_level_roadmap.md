# Top-Level Roadmap: Unified Opportunity Engine

Status: Phase 65 G7.1A roadmap canon
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Product Center

Terminal Zero is the Unified Opportunity Engine:

```text
Primary Alpha: Supercycle Gem Discovery
Secondary Alpha: GodView Market Behavior Intelligence
Output Layer: Decision Augmentation
```

The product is not a trading bot. It is a discretionary augmentation cockpit for finding de-risked asymmetric upside and reading market behavior.

## Roadmap

```text
G7.1A - Starter Docs / PRD / Product Spec Rewrite
G7.1B - Data + Infra Gap Assessment for GodView signals
G7.1C - Codex/Chrome Research Agent SOP
G7.2  - Unified Opportunity Engine State Machine
G7.3  - GodView Signal Source Policy
G7.4  - Supercycle Gem Family Definition, no search
G7.5  - Market Behavior Signal Family Definitions, no search
G8    - One Supercycle Gem Candidate Card, no search
G9    - One Market Behavior Signal Card, no search
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

## Why G7.1A Comes Before G7.2

G7.1 realigned the product away from generic quant alpha search, but it still left a risk: if the next phase jumps directly into `SUPERCYCLE_GEM_DAILY_V0`, the repo can make the product look like a single research family.

That is too narrow.

The actual product has three merged parts:

1. Supercycle gem discovery: the primary alpha layer.
2. GodView market-behavior intelligence: the secondary alpha layer.
3. Decision augmentation: the output layer for buying, holding, trimming, and thesis-break discipline.

G7.1A locks that product truth before any family definition.

## Immediate Next Action

```text
approve_g7_1b_data_infra_gap_or_g7_2_state_machine
```

This means the next approval should choose either:

- G7.1B, to deepen the data/infra gap assessment for GodView signals; or
- G7.2, to define the Unified Opportunity Engine state machine.

It does not approve G7.4 Supercycle Gem Family Definition and does not approve G8 candidate generation.

## Held Work

- G7.2 is not approved yet.
- G7.4 Supercycle Gem Family Definition is downstream and not started.
- G7.5 Market Behavior Signal Family Definitions are downstream and not started.
- G8 PEAD generation remains held.
- No search, candidate generation, backtest, replay, proxy run, ranking, alert, broker, provider-ingestion, or dashboard-runtime implementation is authorized by this roadmap.

## Product Vocabulary

| Old drift-prone framing | G7.1A framing |
| --- | --- |
| Trading bot | Discretionary augmentation cockpit |
| Generic alpha search | De-risked asymmetric upside discovery |
| One family definition as product center | Unified Opportunity Engine |
| Buy/sell signal | Dashboard state or paper-only prompt |
| PEAD as default next product | Tactical family only |
| Options/flow as trigger | GodView context with source policy |

## Acceptance Lock

The roadmap is valid only if:

- PRD and product spec name the Unified Opportunity Engine;
- PEAD is not the roadmap center;
- GodView is included as a core product layer;
- output states include entry discipline and hold discipline;
- immediate next action is `approve_g7_1b_data_infra_gap_or_g7_2_state_machine`;
- no implementation work is smuggled into G7.1A.
