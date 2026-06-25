# Unified Opportunity Engine Architecture

Status: Phase 65 G7.1A architecture canon
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Purpose

The Unified Opportunity Engine is Terminal Zero's top-level product architecture.

It unifies:

```text
Supercycle Gem Discovery
  + GodView Market Behavior Intelligence
  + Decision Augmentation
```

The system serves a discretionary investor/operator. It does not execute trades, approve signals, rank candidates, or bypass human review.

## Architecture Map

```text
Research Inputs
  -> Source Quality / Manifest Layer
  -> Primary Alpha: Supercycle Gem Discovery
  -> Secondary Alpha: GodView Market Behavior Intelligence
  -> Unified State Engine
  -> Dashboard States / Paper-Only Prompts
```

## Primary Alpha: Supercycle Gem Discovery

Objective: find de-risked asymmetric upside.

Future evidence categories:

- thesis memo;
- structural demand inflection;
- supply/capacity constraint;
- financial quality and balance-sheet durability;
- catalyst sequence;
- ownership and sponsorship;
- valuation and expectation reset;
- contradiction log;
- source-quality and freshness.

This layer should answer:

```text
Is this a credible supercycle gem, or only a story?
```

## Secondary Alpha: GodView Market Behavior Intelligence

Objective: read how the market behaves around the thesis.

Future signal families:

- IV / volatility surface;
- options whales;
- gamma / dealer map;
- short squeeze;
- CTA/systematic pressure;
- sector rotation;
- ETF/passive flows;
- dark-pool / ATS / block activity;
- ownership whales;
- microstructure / order book;
- catalysts and narrative velocity;
- regime.

This layer should answer:

```text
Is market behavior confirming, contradicting, crowding, squeezing, or de-risking the thesis?
```

## Output Layer: Decision Augmentation

Objective: prevent avoidable operator mistakes.

Mistake 1:

```text
buying too early on the left side
```

Mistake 2:

```text
selling too early while thesis and market behavior remain supportive
```

Future dashboard states:

```text
wait
watch
accumulation
confirmation
buying range
let winner run
trim optional
exit risk
thesis broken
```

## Unified State Engine Concept

Future G7.2 should define a state engine, not a family artifact:

```text
thesis_state
  + market_behavior_state
  + entry_discipline_state
  + hold_discipline_state
  + source_quality_state
-> dashboard_state
```

G7.1A documents this concept only. It does not implement state-machine code.

## Source Metadata Contract

Every future signal must carry:

```text
source_quality
provider
provider_feed
freshness
latency
confidence
observed_vs_estimated
allowed_use
forbidden_use
manifest_uri
```

## Use Boundaries

Allowed later, after explicit approval:

- research capture;
- thesis cards;
- source-quality labeled dashboard context;
- sealed family definitions;
- paper-only prompts.

Forbidden in G7.1A:

- search;
- candidate generation;
- backtest;
- replay;
- proxy run;
- options/provider ingestion;
- signal ranking;
- alerts;
- broker calls;
- live orders;
- new dashboard runtime behavior.

## Relationship To Existing G7 Artifacts

`PEAD_DAILY_V0` remains valid as a tactical family. It is not the product center.

The product center is now:

```text
Unified Opportunity Engine
```

`SUPERCYCLE_GEM_DAILY_V0` is downstream under G7.4, after the state engine and source policy are defined.
