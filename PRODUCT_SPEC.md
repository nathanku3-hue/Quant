# Product Specification: Unified Opportunity Engine

Status: Canonical product/spec surface for Phase 65 Portfolio Universe Construction Fix
Date: 2026-05-10
Owner: PM / Architecture Office
Scope: docs and architecture only

## Current Phase 65 Notices

G8.1A Discovery Drift Correction (2026-05-10):

- Discovery intake items now require origin provenance fields before any later scout work can consume them.
- Current seed labels are `MU = USER_SEEDED`; `DELL`, `INTC`, `AMD`, and `ALB = USER_SEEDED + THEME_ADJACENT`; `LRCX = USER_SEEDED + SUPPLY_CHAIN_ADJACENT`.
- `SYSTEM_SCOUTED` requires a governed scout path and is not used by the current six-name queue.
- `LOCAL_FACTOR_SCOUT` is defined for the later pipeline-first 4-factor scout baseline, but G8.1A does not inspect or wrap factor artifacts.
- Intake origin metadata is not candidate-card promotion, thesis validation, actionability, ranking, scoring, or recommendation authority.

G8.2 System-Scouted Candidate Card (2026-05-10):

- G8.2 converts the sole G8.1B `LOCAL_FACTOR_SCOUT` output, `MSFT`, into one static candidate-card-only research object.
- Required provenance fields are `discovery_origin = LOCAL_FACTOR_SCOUT`, `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`, `source_intake_item_id`, `source_intake_manifest_uri`, and `candidate_card_manifest_uri`.
- The card may carry light official/public source pointers, missing evidence, provider gaps, thesis breakers, and forbidden jumps only.
- The card must not emit or imply factor score, rank, validation, actionability, buy/sell/hold, buying range, alert, broker action, provider ingestion, or dashboard runtime behavior.
- Existing dashboard `MSFT` rows are legacy ticker-list output and are not card-reader integration.

Portfolio Universe Construction Fix (2026-05-10):

- `strategies/portfolio_universe.py` owns optimizer eligibility, ticker-map readiness, local price-history readiness, and max-weight feasibility diagnostics.
- `dashboard.py` must pass `universe.included_permnos`; it must not pass display-sorted `df_scan["Ticker"][:20]`.
- `views/optimizer_view.py` renders Universe Audit and Why This Allocation diagnostics and labels max-Sharpe optimization as thesis-neutral.
- Generic `WATCH` is research-only until a later approved portfolio-ready watch state exists.
- MU hard floors, Black-Litterman, conviction mode, thesis anchors, manual overrides, scanner rewrites, provider ingestion, alerts, broker paths, and new objectives are blocked.

Optimizer Core Structured Diagnostics (2026-05-11):

- `strategies/optimizer_diagnostics.py` owns optimizer feasibility, bound, constraint, solver, fallback, and severity report objects.
- `strategies/optimizer.py` exposes diagnostic-returning optimizer methods while preserving existing weight-returning methods.
- `views/optimizer_view.py` surfaces optimization status, feasibility status, active constraints, assets at max cap, assets at lower bound, equal-weight-forced status, residuals, and fallback labels.
- This is diagnostics-only; it does not approve lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, new objectives, scanner rules, manual overrides, provider ingestion, alerts, broker behavior, or replay behavior.

Portfolio Data Boundary Refactor (2026-05-11):

- `core/data_orchestrator.py` owns portfolio display-refresh close-price extraction, yfinance/provider-port calls, local TRI overlay scaling, selected-price stitching, and strategy metrics parsing from `data/backtest_results.json`.
- `views/optimizer_view.py` consumes those helpers and renders only controls, diagnostics, allocation explanations, charts, and tables.
- The overlay remains display-freshness only: no canonical market-data write, provider ingestion, alert, broker call, rank, score, recommendation, or candidate-card dashboard merge is authorized.

Portfolio Optimizer View Test and Performance Hardening (2026-05-11):

- `tests/test_optimizer_view.py` uses Streamlit `AppTest` to exercise optimizer view rendering, mean-variance selection, and sector-cap controls.
- `tests/test_optimizer_core_policy.py` now validates UI-derived max-weight/risk-free-rate bounds through the real SLSQP optimizer and validates sector caps as post-solver constraints.
- `core/data_orchestrator.py` owns the display-only Parquet cache for recent close-price overlays and schedules background refresh on cold/stale cache misses.
- `views/optimizer_view.py` caches optimizer runs by selected price frame and user parameters without changing the approved optimizer objective.
- No canonical provider ingestion, lower-bound allocation policy, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker path, score, rank, or candidate-card dashboard merge is authorized.

Dashboard Architecture Safety Slice (2026-05-11):

- `utils/process.py` owns `pid_is_running`, including the Windows `OpenProcess` / `GetExitCodeProcess` liveness probe.
- `dashboard.py`, `data/updater.py`, `scripts/parameter_sweep.py`, `scripts/release_controller.py`, and `backtests/optimize_phase16_parameters.py` must delegate process liveness to that shared helper or compatibility wrappers over it.
- `dashboard.py::spawn_backtest` must fail closed when an existing PID file is live; it must not terminate an unverified PID-file owner.
- `dashboard.py` owns a single strategy-matrix builder/initializer path for Modular Strategies and Portfolio Builder fallback.
- `dashboard.py::_clean_portfolio_price_frame` must delegate to `core.data_orchestrator.clean_price_frame` so display cleanup semantics stay canonical.
- No canonical provider ingestion, market-data write, dashboard content redesign, ranking, scoring, alert, broker path, or strategy-search behavior is authorized.

DASH-0 Dashboard IA Plan (2026-05-10):

- Future dashboard IA is state-first and organized as Command Center, Opportunities, Thesis Card, Market Behavior, Entry & Hold Discipline, Portfolio & Allocation, Research Lab, and Settings & Ops.
- The future shell should use a page registry/sidebar model after DASH-1 approval.
- Full Drift Monitor and Data Health workflows belong in Settings & Ops; only compact status badges belong on Command Center.
- Backtests, Modular Strategies, Daily Scan, and experiments belong in Research Lab.
- No runtime implementation is authorized by DASH-0.

## 1. System Purpose

The Unified Opportunity Engine is the product layer of Terminal Zero.

It combines:

```text
Supercycle Gem Discovery
  + GodView Market Behavior Intelligence
  + Decision Augmentation States
= Unified Opportunity Engine
```

The product helps a human operator identify de-risked asymmetric upside and read market behavior around that opportunity. It does not trade.

## 2. Product Pillars

### 2.1 Primary Alpha: Supercycle Gem Discovery

Goal: find MU/SNDK-style structural winners before they are obvious, while avoiding low-quality left-side speculation.

Required future evidence categories:

- thesis summary;
- structural demand driver;
- supply constraint or capacity bottleneck;
- financial quality / balance-sheet context;
- catalyst path;
- ownership and sponsorship context;
- valuation and expectation reset context;
- contradiction log;
- source-quality and freshness metadata.

G7.1A does not define a family artifact and does not create candidates.

### 2.2 Secondary Alpha: GodView Market Behavior Intelligence

Goal: read how the market is behaving around the thesis.

Signal families to document and later source-policy:

- IV / volatility surface;
- options whales;
- gamma / dealer map;
- short squeeze context;
- CTA/systematic pressure;
- sector rotation;
- ETF/passive flows;
- dark-pool / ATS / block activity;
- ownership whales;
- microstructure / order book;
- catalysts and narrative velocity;
- regime.

GodView signals are context. They do not approve trades or override source-quality rules.

### 2.3 Output Layer: Decision Augmentation

Goal: turn evidence into human-readable states:

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

These states are paper-only prompts after future approval. In G7.1A they are product vocabulary only.

## 3. Unified State Engine

The future state engine should merge primary and secondary alpha:

```text
thesis_state
  + market_behavior_state
  + entry_discipline_state
  + hold_discipline_state
  + source_quality_state
-> dashboard_state
```

Example future state mapping:

| Thesis state | Market behavior | Entry/hold discipline | Output state |
| --- | --- | --- | --- |
| intact | supportive | left-side risk high | wait |
| intact | improving | base forming | watch |
| strengthening | supportive | entry window improving | accumulation |
| strengthening | confirming | price/flow confirmation | confirmation |
| intact | supportive but volatile | price near defined range | buying range |
| intact | momentum supportive | crowding acceptable | let winner run |
| intact | mixed/crowded | risk rising but thesis alive | trim optional |
| weakening | hostile | exit conditions emerging | exit risk |
| broken | unsupported | invalidation confirmed | thesis broken |

This table is product design, not executable logic.

## 4. Source Metadata Contract

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

Allowed-use examples:

- research context;
- dashboard context;
- paper-only prompt context after approval;
- promotion evidence only if Tier 0/canonical policy is satisfied.

Forbidden-use examples:

- live order trigger;
- broker instruction;
- alpha evidence without validation;
- canonical write without manifest;
- source-quality bypass;
- unreviewed signal approval.

## 5. Observed Facts vs Estimates

The product must distinguish:

- observed facts: reported price/volume, reported short interest, published filings, official exchange/OCC/CFTC/FINRA/SEC reports;
- vendor transforms: vendor-calculated IV, unusual options flags, ETF flow fields, dark-pool aggregations;
- model estimates: dealer gamma maps, CTA pressure proxies, squeeze probability, narrative velocity scores.

Estimated fields may be useful, but they must be labeled and cannot masquerade as observed truth.

## 6. Current Infrastructure Fit

Current infrastructure is enough for:

- canonical daily price governance;
- manifest/provenance checks;
- Candidate Registry;
- V1/V2 mechanical replay discipline;
- dashboard smoke checks;
- minimal validation lab;
- paper-alert readiness foundations.

Current infrastructure is not enough for full GodView until future provider layers exist:

- `data/providers/options_provider.py`
- `data/providers/short_interest_provider.py`
- `data/providers/cftc_provider.py`
- `data/providers/sec_filings_provider.py`
- `data/providers/etf_flow_provider.py`
- `data/providers/news_research_provider.py`
- `signals/source_registry.py`
- `signals/freshness_policy.py`
- `signals/confidence_policy.py`
- `signals/godview_state_machine.py`

These are future upgrades. G7.1A does not create them.

## 7. Dashboard Product Surface

Future dashboard areas:

- opportunity watchlist;
- thesis card;
- GodView market-behavior panel;
- entry discipline panel;
- hold discipline panel;
- source-quality and freshness rail;
- paper-only prompt state.

The dashboard must not show automatic buy/sell orders, broker actions, unqualified rankings, or unreviewed signal approvals.

## 8. Roadmap

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

Immediate next action:

```text
approve_g7_1b_data_infra_gap_or_g7_2_state_machine
```

## 9. G7.1A Boundary

G7.1A may change docs, architecture docs, phase brief, current truth surfaces, handover, SAW report, decision log, notes, and lessons.

G7.1A must not add:

- candidate generation;
- alpha search;
- backtest;
- replay;
- proxy run;
- options ingestion;
- signal ranking;
- buy/sell alerts;
- broker calls;
- Alpaca live behavior;
- OpenClaw notification;
- new runtime dashboard behavior.

## 10. Acceptance Status

This spec is complete for G7.1A when the root PRD/spec, architecture package, phase brief, current truth surfaces, handover, and SAW report all describe the Unified Opportunity Engine as the product center and keep G7.2/G8 held.
