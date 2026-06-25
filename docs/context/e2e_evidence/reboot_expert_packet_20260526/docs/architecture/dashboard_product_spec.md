# Dashboard Product Spec: Unified Opportunity Engine

Status: Phase 65 G7.1A dashboard product spec
Date: 2026-05-09
Authority: G7.1A starter docs / product-spec rewrite

## Purpose

The dashboard is the operator cockpit for the Unified Opportunity Engine.

It should help the user understand:

- what opportunity is being watched;
- whether the thesis is intact;
- whether market behavior is supportive or hostile;
- whether entry is premature or improving;
- whether holding is still justified;
- whether trimming or thesis-break review is needed.

The dashboard is not a trading terminal, broker interface, or automatic alert engine in G7.1A.

## DASH-0 Information Architecture Update

Phase 65 DASH-0 approves a future state-first page map:

```text
Command Center
Opportunities
Thesis Card
Market Behavior
Entry & Hold Discipline
Portfolio & Allocation
Research Lab
Settings & Ops
```

The current Sovereign Cockpit runtime remains unchanged in DASH-0. The redo sequence starts with planning, then a later DASH-1 may implement a page registry/sidebar shell with no new data, metrics, product claims, alerts, providers, broker calls, rankings, or scores.

## First-Class Dashboard States

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

These states are future product vocabulary only until a later implementation phase.

## Legacy Future Dashboard Areas Superseded By DASH-0

The section below is retained for historical continuity. DASH-0 supersedes it as the first-class dashboard structure with:

```text
Command Center
Opportunities
Thesis Card
Market Behavior
Entry & Hold Discipline
Portfolio & Allocation
Research Lab
Settings & Ops
```

Any runtime implementation must follow the DASH-0 IA unless a later signed decision changes it.

### 1. Opportunity Watchlist

Shows watched opportunities and their current dashboard state.

Expected future fields:

- ticker/name;
- thesis label;
- current state;
- source-quality badge;
- freshness badge;
- last reviewed time;
- open contradiction count.

### 2. Thesis Card

Shows the supercycle thesis.

Expected future fields:

- thesis summary;
- structural driver;
- catalyst path;
- evidence log;
- contradiction log;
- operator notes;
- source-quality state.

### 3. GodView Market Behavior Panel

Shows market-behavior context:

- IV / volatility surface;
- options whales;
- gamma / dealer map;
- short squeeze;
- CTA/systematic pressure;
- sector rotation;
- ETF/passive flows;
- dark-pool / block activity;
- ownership whales;
- microstructure;
- catalysts/news/narrative;
- regime.

Each tile must label observed vs estimated status and freshness.

### 4. Entry Discipline Panel

Answers:

```text
Is buying now premature, acceptable, or improving?
```

Future context:

- left-side risk;
- stabilization;
- confirmation;
- buying range;
- liquidity/spread sanity;
- source freshness.

### 5. Hold Discipline Panel

Answers:

```text
Is the operator at risk of selling a winner too early?
```

Future context:

- thesis intact or weakening;
- momentum supportive or deteriorating;
- flows supportive or crowded;
- trim optional vs exit risk;
- thesis broken markers.

### 6. Source-Quality Rail

Every future dashboard state must expose:

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

## Forbidden Dashboard Behavior

G7.1A does not add or authorize:

- new runtime dashboard behavior;
- automatic buy/sell signals;
- live alerts;
- broker buttons;
- Alpaca live behavior;
- OpenClaw notifications;
- candidate rankings;
- strategy search results;
- backtest rankings;
- provider ingestion status promises that do not exist.

## Relationship To Existing Dashboard

The already-completed dashboard drift-monitor dependency fix/test remains valid. G7.1A does not expand that code path.

This document describes future product structure only.

## Future Implementation Sequence

- G7.2: define Unified Opportunity Engine state machine.
- G7.3: define GodView signal source policy.
- G10: build dashboard prototype for watchlist state view.
- Future signed decision only: consider paper-only buying-range / hold-discipline review prompts after source and state gates are ready. This is not authorized by DASH-0.
