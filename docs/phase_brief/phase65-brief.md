# Phase 65 Brief

## Portfolio Optimizer View Test and Performance Hardening Addendum

Status: PORTFOLIO OPTIMIZER VIEW TEST AND PERFORMANCE HARDENING APPROVED
Authority: tests/performance hardening round for `/portfolio-and-allocation`
Date: 2026-05-11
Owner: PM / Architecture Office

Approved scope:

- add dedicated Streamlit `AppTest` coverage for optimizer view rendering, mean-variance control selection, and sector-cap UI paths;
- add UI-to-solver integration coverage that pipes synthetic max-weight and risk-free-rate controls into the real SLSQP optimizer;
- move recent close-price display refresh to a non-canonical Parquet cache with background refresh on cold/stale cache misses;
- cache overlay scaling output and optimizer run output for equivalent rerenders.

Held scope:

- no canonical provider ingestion, canonical market-data writes, lower-bound allocation policy, new optimizer objective, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker behavior, score, rank, recommendation, or candidate-card dashboard merge.

Contract:

```text
local TRI prices -> display-only overlay cache -> cached optimizer run -> post-solver sector cap -> UI diagnostics
```

Acceptance checks:

- `tests/test_optimizer_view.py` exists and uses Streamlit `AppTest`.
- cold display-overlay cache misses do not block render on synchronous provider calls.
- Parquet cache writes use temp-file then replace.
- optimizer run cache is keyed by method, selected price frame, max-weight, and risk-free-rate.
- focused optimizer/dashboard tests pass.
- independent SAW Implementer and Reviewer A/B/C rerun passes.

## Portfolio Data Boundary Refactor Addendum

Status: PORTFOLIO DATA BOUNDARY REFACTOR APPROVED
Authority: architecture hygiene round for `/portfolio-and-allocation`
Date: 2026-05-11
Owner: PM / Architecture Office

Approved scope:

- move selected-stock live display overlay fetching out of `views/optimizer_view.py`;
- move local TRI scaling, stitching, forward-fill readiness, and freshness-source classification into `core/data_orchestrator.py`;
- move `data/backtest_results.json` strategy-metrics parsing into `core/data_orchestrator.py`;
- keep Portfolio & Allocation behavior, optimizer diagnostics, current objective set, and display-freshness labels unchanged.

Held scope:

- no canonical provider ingestion, market-data writes, alert, broker call, ranking, scoring, recommendation, candidate-card dashboard merge, optimizer objective change, MU conviction, WATCH investability expansion, Black-Litterman, or thesis-anchor math.

Contract:

```text
local TRI prices + ticker map -> core data orchestration display overlay -> optimizer view rendering
```

Acceptance checks:

- `views/optimizer_view.py` does not import yfinance or parse `data/backtest_results.json` directly.
- focused portfolio/DASH/provider-port tests pass.
- scoped compile passes for touched runtime/test files.

## Optimizer Core Structured Diagnostics Addendum

Status: OPTIMIZER CORE STRUCTURED DIAGNOSTICS IMPLEMENTATION APPROVED
Authority: separate optimizer diagnostics-only implementation round
Date: 2026-05-11
Owner: PM / Architecture Office

Approved scope:

- add a diagnostics layer outside UI code at `strategies/optimizer_diagnostics.py`;
- report pre-solver feasibility failures, max-weight boundary pressure, SLSQP status, active bounds, constraint residuals, and labeled fallback status;
- convert optimizer audit strict xfail debt into passing diagnostics tests;
- update Portfolio & Allocation UI with optimization status, feasibility status, active constraints, max-cap/lower-bound assets, equal-weight-forced status, and fallback labeling.

Held scope:

- no MU conviction policy, MU floor, WATCH investability expansion, Black-Litterman, simple tilt, conviction optimizer, new objective, new scanner rule, manual override, provider ingestion, alert, broker, or replay behavior.

Contract:

```text
optimizer inputs -> structured feasibility diagnostics -> existing optimizer objective -> structured solver/bound/constraint diagnostics -> UI-safe explanation
```

Closure target:

```text
OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_20260510 / OPTIMIZER_DIAGNOSTICS_ONLY
```

## Optimizer Core Policy Audit Addendum

Status: OPTIMIZER CORE POLICY AUDIT OPENED - IMPLEMENTATION HELD
Authority: separate optimizer lower-bound/SLSQP policy audit
Date: 2026-05-10
Owner: PM / Architecture Office

Approved scope:

- document current optimizer constraints policy;
- audit lower-bound/SLSQP behavior separately from universe construction;
- add policy tests that reject unapproved lower bounds and mark future implementation debt;
- preserve the quarantined patch as evidence only.

Held scope:

- no `strategies/optimizer.py` implementation change;
- no MU hard floor, conviction mode, WATCH investability, Black-Litterman, manual override, scanner rewrite, provider ingestion, alert, broker behavior, or new portfolio objective.

Immediate next action:

```text
hold_optimizer_core_implementation_until_policy_approval
```

## Portfolio Universe Construction Current Addendum

Status: PORTFOLIO UNIVERSE CONSTRUCTION FIX PASS - OPTIMIZER CORE LOWER-BOUND DIFF QUARANTINED
Authority: Phase 65 Portfolio & Allocation runtime correction
Date: 2026-05-10
Owner: PM / Architecture Office

Approved scope:

- separate optimizer universe from dashboard display order;
- default-exclude `EXIT`, `KILL`, `AVOID`, and `IGNORE`;
- treat generic `WATCH` as research-only by default;
- report ticker-map and local price-history readiness failures;
- add max-weight feasibility diagnostics;
- rename misleading Sharpe labels as thesis-neutral/historical.

Held scope:

- MU hard floor or `MU >= 20%`;
- Black-Litterman or conviction optimizer;
- thesis anchors, anchor sizing, confidence tilts, and manual override;
- Sovereign / Alpha Quad scanner rewrite;
- new portfolio objective.

Quarantine result:

- dirty `strategies/optimizer.py` lower-bound / SLSQP handling changes were discovered during closure;
- the diff is preserved at `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`;
- `strategies/optimizer.py` was reverted to baseline for this closure;
- optimizer-core math remains unaccepted until a separate optimizer-policy audit approves, revises, or rejects it.

Contract:

```text
scanner output -> explicit optimizer universe builder -> eligibility/readiness checks -> thesis-neutral optimizer
```

Immediate next action:

```text
open_optimizer_core_policy_audit_or_hold
```

## G8.2 Current Addendum - System-Scouted Candidate Card

Status: G8.2 SYSTEM-SCOUTED CANDIDATE CARD PASS - G9/G8.3/DASH CARD READER HELD UNTIL SEPARATE APPROVAL
Authority: Phase 65 G8.2 Data + Docs/Ops candidate-card-only work
Date: 2026-05-10
Owner: PM / Architecture Office

G8.2 converts exactly one governed system-scouted intake item into a candidate-card-only research object. The only eligible ticker is `MSFT`, because G8.1B emitted exactly one `LOCAL_FACTOR_SCOUT` output item.

Approved G8.2 scope:

- create `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`;
- create `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`;
- reuse the existing candidate-card schema and validator;
- reference `data/discovery/local_factor_scout_output_tiny_v0.json` and its manifest;
- record light official/public evidence pointers as research orientation only;
- keep missing evidence, thesis breakers, provider gaps, and forbidden jumps visible;
- ensure `not_validated`, `not_actionable`, `no_score`, `no_rank`, `no_buy_sell_signal`, `no_alert`, and `no_broker_action` remain true.

G8.2 deliverables:

- `opportunity_engine/candidate_card_schema.py`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`
- `docs/saw_reports/saw_phase65_g8_2_system_scouted_candidate_card_20260510.md`

G8.2 lock:

```text
Pipeline-scouted does not mean validated.
Candidate-card-only does not mean actionable.
The existing dashboard MSFT row is legacy runtime output, not the G8.2 card.
```

Immediate next action after G8.2 closeout:

```text
approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold
```

## G8.1B Current Addendum - Pipeline-First Discovery Scout Baseline

Status: G8.1B PIPELINE-FIRST DISCOVERY SCOUT PASS - G8.2/G9/DASH-1 HELD UNTIL SEPARATE APPROVAL
Authority: Phase 65 G8.1B backend/governance work
Date: 2026-05-10
Owner: PM / Architecture Office

G8.1B proves the first governed system-scouted intake item without claiming alpha, rank, score, validation, actionability, candidate-card authority, dashboard runtime behavior, provider ingestion, alerts, or broker behavior.

Approved G8.1B scope:

- inspect `data/processed/phase34_factor_scores.parquet` metadata only;
- wrap the existing local artifact as `LOCAL_FACTOR_SCOUT`;
- name the wrapper `4-Factor Equal-Weight Scout Baseline`;
- assign `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`;
- record source artifact row count, date range, universe count, factor names, equal factor weights, input manifest metadata, output manifest references, and as-of date;
- emit exactly one tiny intake-only scout output item;
- select the fixture row deterministically by latest date, local metadata eligibility, and ascending `permno`, not by factor ordering;
- keep `not_alpha_evidence = true`, `no_rank = true`, `no_score_display = true`, and `no_buy_sell_signal = true`.

G8.1B deliverables:

- `opportunity_engine/factor_scout_schema.py`
- `opportunity_engine/factor_scout.py`
- `data/discovery/local_factor_scout_baseline_v0.json`
- `data/discovery/local_factor_scout_baseline_v0.manifest.json`
- `data/discovery/local_factor_scout_output_tiny_v0.json`
- `data/discovery/local_factor_scout_output_tiny_v0.manifest.json`
- `tests/test_g8_1b_pipeline_first_discovery_scout.py`
- `docs/architecture/pipeline_first_discovery_scout_policy.md`
- `docs/architecture/local_factor_scout_baseline_policy.md`
- `docs/architecture/factor_scout_output_contract.md`
- `docs/handover/phase65_g81b_pipeline_first_scout_handover.md`
- `docs/saw_reports/saw_phase65_g8_1b_pipeline_first_scout_20260510.md`

G8.1B lock:

```text
System-scouted does not mean validated.
System-scouted does not mean recommended.
System-scouted only means the deterministic scout pipeline surfaced the name for research intake.
```

SAW status:

```text
Independent SAW Implementer and Reviewers A/B/C reran successfully in G8.1B-R.
SAW Verdict: PASS.
ClosureValidation: PASS.
SAWBlockValidation: PASS.
EvidenceValidation: PASS.
```

Immediate next action after G8.1B closeout:

```text
approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_dash1_or_hold
```

## DASH-0 Current Addendum - GodView Dashboard IA Redesign Plan

Status: DASH-0 DASHBOARD IA PLAN COMPLETE - DASH-1 HELD
Authority: Phase 65 DASH-0 planning-only work
Date: 2026-05-10
Owner: PM / Architecture Office

DASH-0 approves the dashboard information architecture before any runtime rewrite. The live dashboard remains the older Sovereign Cockpit runtime; DASH-0 only plans the future state-first GodView page structure.

Approved DASH-0 page map:

- Command Center
- Opportunities
- Thesis Card
- Market Behavior
- Entry & Hold Discipline
- Portfolio & Allocation
- Research Lab
- Settings & Ops

DASH-0 deliverables:

- `docs/architecture/dashboard_information_architecture.md`
- `docs/architecture/dashboard_page_registry_plan.md`
- `docs/architecture/dashboard_redesign_migration_plan.md`
- `docs/architecture/dashboard_ops_relocation_policy.md`
- `docs/handover/dashboard_ia_handover_20260510.md`
- `docs/saw_reports/saw_dashboard_ia_redesign_plan_20260510.md`

Optional doc-only updates:

- `docs/architecture/godview_dashboard_wireframe.md`
- `docs/architecture/dashboard_product_spec.md`

Hard holds:

- no `dashboard.py` edits;
- no `views/` edits;
- no `optimizer_view.py` edits;
- no Streamlit runtime shell;
- no factor-scout code or `phase34_factor_scores.parquet` touch;
- no discovery-intake output changes;
- no candidate-card changes;
- no provider, backtest, alert, or broker changes.

Immediate next action after DASH-0 closeout:

```text
approve_dash_1_page_registry_shell_or_hold
```

## G8.1A Current Addendum - Discovery Drift Correction

Status: G8.1A DISCOVERY DRIFT CORRECTION CURRENT - G8.1B/G8.2/G9 HELD
Authority: Phase 65 G8.1A policy/schema-only work
Date: 2026-05-10
Owner: PM / Architecture Office

G8.1A corrects the discovery-origin drift in the G8.1 queue. The six-name queue remains useful, but it is user-seeded and theme/supply-chain-adjacent, not pure system-scouted output.

Approved G8.1A scope:

- add a discovery-origin taxonomy;
- add required origin fields to discovery intake items;
- relabel `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB` as user-seeded with theme or supply-chain adjacency where applicable;
- keep all six names `is_system_scouted = false`, `is_validated = false`, and `is_actionable = false`;
- define `LOCAL_FACTOR_SCOUT` for G8.1B but keep it unused in G8.1A;
- document the intake-vs-candidate-card boundary.

G8.1A deliverables:

- `docs/architecture/discovery_drift_policy.md`
- `docs/architecture/discovery_origin_taxonomy.md`
- `docs/architecture/supercycle_scout_protocol.md`
- `docs/architecture/discovery_intake_vs_candidate_card.md`
- `docs/handover/phase65_g81a_discovery_drift_handover.md`
- `docs/saw_reports/saw_phase65_g8_1a_discovery_drift_20260510.md`
- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `data/discovery/supercycle_candidate_intake_queue_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json`
- `tests/test_g8_1a_discovery_drift_policy.py`

Immediate next action after G8.1A closeout:

```text
approve_g8_1b_pipeline_first_discovery_scout_or_hold
```

## G8.1 Current Addendum - Supercycle Discovery Intake

Status: G8.1 SUPERCYCLE DISCOVERY INTAKE CURRENT - G8.2/G9 HELD
Authority: Phase 65 G8.1 intake-only work
Date: 2026-05-10
Owner: PM / Architecture Office

G8.1 supersedes the prior immediate G9 recommendation for this round. The new product bottleneck is whether Terminal Zero can structure names the user does not already know well into a candidate discovery queue without creating alpha search, ranking, scoring, validation, recommendations, provider ingestion, dashboard runtime behavior, alerts, or broker behavior.

Approved G8.1 scope:

- define `AI_COMPUTE_INFRA`, `AI_SERVER_SUPPLY_CHAIN`, `MEMORY_STORAGE_SUPERCYCLE`, `SEMICAP_EQUIPMENT`, `POWER_COOLING_GRID`, `CRITICAL_MINERALS_LITHIUM`, `RESHORING_FOUNDRY`, `DEFENSE_INDUSTRIAL`, and `BIOTECH_PLATFORM`;
- create one static candidate intake queue seeded exactly with `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`;
- keep `MU = candidate_card_exists`;
- keep `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB = intake_only`;
- require evidence needed, official source needs, thesis breakers, provider gaps, and relevant market-behavior modules;
- validate no score, no rank, no buy/sell/hold call, no validated status, no action-state promotion, and no yfinance canonical evidence.

G8.1 deliverables:

- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `data/discovery/supercycle_discovery_themes_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json`
- `tests/test_g8_1_supercycle_discovery_intake.py`
- `docs/architecture/g8_1_supercycle_discovery_intake_policy.md`
- `docs/architecture/supercycle_discovery_theme_taxonomy.md`
- `docs/architecture/supercycle_candidate_intake_schema.md`
- `docs/handover/phase65_g81_supercycle_discovery_intake_handover.md`
- `docs/saw_reports/saw_phase65_g8_1_supercycle_discovery_intake_20260510.md`

Immediate next action after G8.1 closeout:

```text
approve_g8_2_one_additional_candidate_card_or_g9_one_market_behavior_signal_card_or_hold
```

Status: G8 ONE SUPERCYCLE GEM CANDIDATE CARD COMPLETE - G9 HELD
Authority: Phase 65 G8 candidate-card-only work
Date: 2026-05-10
Owner: PM / Architecture Office

## Goal

Answer one question before G7.2 design work:

```text
Can the current repo/data layer actually support the GodView Opportunity Engine,
and what must be upgraded later?
```

G7.1B makes the data reality explicit. It maps what is ready, what is missing, what is delayed, what is estimated, what requires licensed providers, and what remains forbidden from driving decisions.

G7.1C extends that reality map with an open-source repository and data/API availability survey. It records what can be learned from OpenBB, LEAN, Qlib, vectorbt, FinRL, pandas-datareader, Freqtrade, Hummingbot, and CCXT, then completes the official public source audit for SEC, FINRA, CFTC, FRED/ALFRED, and Ken French while holding implementation.

G7.1D executes the first approved public-source proof: one tiny static SEC data.sec.gov fixture for one company, with manifests and validation tests only.

G7.1E executes the second approved public-source proof: one tiny static FINRA Equity Short Interest fixture for one settlement date, with a manifest, validation tests, and explicit short-interest-vs-short-sale-volume policy.

G7.1F executes the third approved public-source proof: one tiny static CFTC Commitments of Traders / Traders in Financial Futures fixture for one report date, with a manifest, validation tests, and explicit broad-regime-only CFTC usage policy.

G7.1G executes the fourth approved public-source proof: one tiny static FRED macro fixture and one tiny static Ken French factor fixture, each with a manifest, validation tests, and explicit macro/factor-context-only policy.

G7.2 defines the Unified Opportunity State Machine: finite opportunity states, transition schemas, forbidden jumps, source-class requirements, and validator tests. It creates no scoring, ranking, search, alert, broker, provider, ingestion, or dashboard runtime behavior.

G7.3 defines the Signal-to-State Source Eligibility Map: source classes, signal-family policies, freshness/confidence labels, and forbidden state influence. It creates no provider, live API, source registry, ranking, alert, broker, or dashboard runtime behavior.

G7.4 defines the Dashboard Wireframe / Product-State Spec: state-first dashboard sections, watchlist card fields, daily brief structure, and blocked-action language. It creates no dashboard runtime code and no candidate card.

G8 creates exactly one human-nominated Supercycle Gem Candidate Card for MU. It proves the research-object workflow without alpha search, candidate screening, ranking, scoring, backtest, replay, provider ingestion, dashboard runtime behavior, buy/sell alerts, or broker calls.

## Product Truth

G7.1A locked Terminal Zero as the Unified Opportunity Engine:

```text
Primary Alpha: Supercycle Gem Discovery
Secondary Alpha: GodView Market Behavior Intelligence
Output Layer: Decision Augmentation
```

G7.1B does not change this product truth. It deepens the GodView data and infrastructure assessment so later G7.2 state-machine design is grounded in real source constraints.

G7.2-G7.4 sealed the state-machine, source-eligibility, and product-state dashboard logic needed before any G8 candidate card.

G8 now proves one structured research object can sit inside that framework as `candidate_card_only`, with source-quality labels, missing-evidence fields, provider-gap labels, and forbidden state jumps.

## Boundary

Approved:

- docs and architecture only;
- source mapping against current repo/provider/readiness surfaces;
- GodView signal-source matrix;
- future provider roadmap documentation;
- freshness policy documentation;
- observed-vs-estimated policy documentation;
- Codex/Chrome research SOP documentation;
- current truth-surface refresh;
- handover and SAW report.
- official source audit against SEC, FINRA, CFTC, FRED/ALFRED, and Ken French docs;
- source terms matrix;
- tiny fixture schema plan only;
- public provider priority note.
- one static SEC companyfacts fixture for one CIK;
- one static SEC submissions fixture for one CIK;
- SEC fixture manifests;
- fixture-only validation tests;
- SEC tiny fixture policy and fixture plan.
- one static FINRA short-interest fixture for one settlement date;
- one FINRA short-interest manifest;
- FINRA fixture-only validation tests;
- FINRA short-interest policy, short-interest-vs-short-volume policy, and fixture plan.
- one static CFTC COT/TFF fixture for one report date;
- one CFTC TFF manifest;
- CFTC fixture-only validation tests;
- CFTC TFF fixture policy, CFTC COT/TFF usage policy, and fixture plan.
- one static FRED macro fixture with three series;
- one FRED macro manifest;
- one static Ken French factor-return fixture with one factor dataset;
- one Ken French factor manifest;
- FRED / Ken French fixture-only validation tests;
- FRED / Ken French fixture policy, macro/factor usage policy, and fixture plan.
- G7.2 opportunity state enums, reason codes, transition schemas, transition validator, and focused tests;
- G7.2 state-machine architecture, transition policy, forbidden-jump register, handover, and SAW report;
- G7.3 source classes, signal-family policies, confidence labels, source eligibility docs, focused tests, handover, and SAW report;
- G7.4 dashboard wireframe, watchlist card spec, daily brief spec, focused docs tests, handover, and SAW report.
- G8 one MU Supercycle Gem Candidate Card as a structured research object;
- G8 candidate-card schema and validator;
- one static G8 card manifest;
- focused G8 candidate-card tests;
- G8 policy, schema, handover, context refresh, and SAW report.

Blocked:

- G9 market behavior signal card unless explicitly approved;
- any second candidate card unless explicitly approved;
- G7.5 family definitions unless separately approved;
- candidate generation;
- alpha search;
- candidate screening;
- signal ranking or scoring;
- alpha search;
- backtest;
- replay;
- proxy run;
- provider implementation;
- ingestion;
- options feed;
- SEC/CFTC/FINRA ingestion;
- CFTC/FRED/Ken French provider proof;
- any additional physical tiny fixture creation beyond the approved G7.1G FRED / Ken French two-file proof;
- SEC live provider or broad downloader;
- FINRA live provider, API call, or bulk downloader;
- CFTC live provider, API call, or bulk downloader;
- FRED live provider, API call, API-key handling, or bulk downloader;
- Ken French live provider, downloader, or bulk retrieval;
- CTA score or single-name CTA inference;
- macro regime score or factor regime score;
- Reg SHO ingestion;
- OTC / ATS ingestion;
- squeeze score or short-squeeze ranking;
- source registry implementation;
- microstructure feed;
- alerts;
- broker calls;
- Alpaca live behavior;
- OpenClaw notification;
- new dashboard runtime behavior.

## Roadmap

```text
G7.1A - Starter Docs / PRD / Product Spec Rewrite (closed)
G7.1B - Data + Infra Gap Assessment for GodView signals (closed)
G7.1C - Open-source repo + data/API availability survey; official public source audit complete, provider work held
G7.1D - SEC data.sec.gov one-company tiny fixture proof (closed)
G7.1E - FINRA short-interest tiny fixture proof (closed)
G7.1F - CFTC COT/TFF tiny fixture (closed)
G7.1G - FRED/Ken French macro/factor fixture (closed)
G7.2  - Unified Opportunity Engine State Machine (closed)
G7.3  - GodView Signal Source Policy (closed)
G7.4  - Dashboard Wireframe / Product-State Spec (closed)
G7.5  - Market Behavior Signal Family Definitions, no search (held)
G8    - One Supercycle Gem Candidate Card, no search (closed)
G9    - One Market Behavior Signal Card, no search (held)
G10   - Dashboard Prototype: watchlist state view
G11   - Bounded discovery under sealed families
G12   - Paper-only buying-range / hold-discipline alerts
```

Immediate next action after G8 candidate-card closeout:

```text
approve_g9_one_market_behavior_signal_card_or_hold
```

## Core Assessment

Current infrastructure is sufficient for:

- governance foundations;
- canonical daily price/volume;
- manifest/provenance checks;
- provider-port conventions;
- readiness auditing;
- Candidate Registry and family-definition governance;
- V1/V2 mechanical replay discipline;
- dashboard smoke and validation-lab discipline.

Current infrastructure is not sufficient for full GodView:

- OPRA/options tape and IV surface;
- options OI/volume and unusual-options classification;
- gamma/dealer-positioning estimates;
- FINRA short interest;
- borrow/stock-loan;
- CFTC COT/TFF provider/ingestion beyond the G7.1F tiny fixture;
- FRED / Ken French provider/ingestion beyond the G7.1G tiny fixtures;
- SEC 13F/13D/13G/Form 4 ownership intelligence;
- ETF/passive holdings and flows;
- FINRA ATS/OTC or vendor block/dark-pool feeds;
- TAQ/order-book microstructure;
- governed news/narrative evidence.

## Acceptance Checks

- [x] CHK-G71B-01: GodView data-source matrix exists.
- [x] CHK-G71B-02: Every signal family has readiness, provider need, freshness, trust level, and build priority.
- [x] CHK-G71B-03: Docs state current infra is sufficient for governance but not full GodView.
- [x] CHK-G71B-04: Future provider ports are documented only and not implemented.
- [x] CHK-G71B-05: Signal metadata contract includes `signal_id`, `signal_family`, `ticker_or_theme`, `source_quality`, `provider`, `provider_feed`, `observed_vs_estimated`, `freshness`, `latency`, `asof_ts`, `confidence`, `allowed_use`, `forbidden_use`, and `manifest_uri`.
- [x] CHK-G71B-06: Observed, estimated, and inferred labels are defined.
- [x] CHK-G71B-07: Codex/Chrome research agents are allowed only for research capture/docs, not alpha evidence or trading actions.
- [x] CHK-G71B-08: G7.2 and G8 remain held.
- [x] CHK-G71B-09: No provider code, ingestion, backtest, replay, candidate generation, ranking, alert, broker, or dashboard runtime behavior is added.
- [x] CHK-G71B-10: Context rebuild and validation pass.
- [x] CHK-G71B-11: Dashboard drift regression passes.
- [x] CHK-G71B-12: Full pytest passes.
- [x] CHK-G71B-13: `pip check` passes.
- [x] CHK-G71B-14: Scoped compile checks pass; broad compileall inherited hygiene debt remains documented if it fails.
- [x] CHK-G71B-15: Data readiness and minimal validation lab pass.
- [x] CHK-G71B-16: Forbidden-scope scan, secret scan, and artifact hash audit pass.
- [x] CHK-G71B-17: SAW report, closure packet validation, and SAW block validation pass.

G7.1C checks:

- [x] CHK-G71C-01: Open-source repository survey is captured as `docs/research`; source audit is now complete in the G7.1C audit-only extension.
- [x] CHK-G71C-02: Architecture summary records what to borrow from open-source repos and what not to borrow.
- [x] CHK-G71C-03: API availability matrix separates current-ready, no-cost/public, paid/licensed, operational, and delayed/context sources.
- [x] CHK-G71C-04: Provider selection policy requires audit before implementation.
- [x] CHK-G71C-05: Build-vs-borrow decision names SEC, FINRA, CFTC, and public macro as no-cost candidates after audit.
- [x] CHK-G71C-06: Options, IV, whales, gamma, dark-pool, and microstructure remain held behind provider/license decisions.
- [x] CHK-G71C-07: No provider code, ingestion, state machine, candidate generation, ranking, dashboard runtime behavior, alerts, broker calls, or trading actions are added.
- [x] CHK-G71C-AUD-01: SEC EDGAR / data.sec.gov official docs are audited for auth, key, freshness, fair access, raw locator, CIK/accession keys, and allowed/forbidden use.
- [x] CHK-G71C-AUD-02: FINRA short interest, Reg SHO daily short-sale-volume, and OTC/ATS transparency are audited with short-interest vs Reg SHO distinction preserved.
- [x] CHK-G71C-AUD-03: CFTC COT/TFF is audited as broad regime/futures positioning only, not direct single-name CTA buying evidence.
- [x] CHK-G71C-AUD-04: FRED/ALFRED is audited with API-key and third-party series-rights caveats.
- [x] CHK-G71C-AUD-05: Ken French Data Library is audited with public-download/citation/copyright caveats.
- [x] CHK-G71C-AUD-06: Tiny fixture schemas are documented as plan-only with primary keys, date fields, duplicate checks, row-count checks, and manifest fields.
- [x] CHK-G71C-AUD-07: No data download, physical fixture, provider code, ingestion, state machine, ranking, alerts, dashboard runtime behavior, broker calls, or provider proof is added.

G7.1D checks:

- [x] CHK-G71D-01: SEC tiny fixture policy exists and states fixture-only authority.
- [x] CHK-G71D-02: SEC public provider fixture plan exists and holds live provider work.
- [x] CHK-G71D-03: Static companyfacts fixture exists for exactly one CIK.
- [x] CHK-G71D-04: Static submissions fixture exists for exactly one CIK.
- [x] CHK-G71D-05: Both SEC fixtures have sidecar manifests with required fields.
- [x] CHK-G71D-06: Manifest SHA-256 values reconcile to artifact bytes.
- [x] CHK-G71D-07: Manifest row counts reconcile to fixture rows.
- [x] CHK-G71D-08: Date fields parse and CIK is zero-padded 10 digits.
- [x] CHK-G71D-09: Duplicate primary keys and non-finite numeric facts are rejected by tests.
- [x] CHK-G71D-10: `source_quality`, `allowed_use`, `forbidden_use`, and observed label are enforced.
- [x] CHK-G71D-11: No live provider, broad downloader, ingestion, canonical lake write, score, candidate generation, state machine, alert, broker call, or dashboard runtime behavior is added.
- [x] CHK-G71D-12: Final context rebuild, validation matrix, SAW report validation, and closure packet validation pass.

G7.1E checks:

- [x] CHK-G71E-01: FINRA short-interest tiny fixture policy exists and states fixture-only authority.
- [x] CHK-G71E-02: FINRA short-interest-vs-short-sale-volume policy exists.
- [x] CHK-G71E-03: FINRA public provider fixture plan exists and holds live provider work.
- [x] CHK-G71E-04: Static FINRA short-interest CSV exists for one settlement date.
- [x] CHK-G71E-05: FINRA fixture has a sidecar manifest with required fields.
- [x] CHK-G71E-06: Manifest SHA-256 value reconciles to artifact bytes.
- [x] CHK-G71E-07: Manifest row count reconciles to fixture rows.
- [x] CHK-G71E-08: Settlement date parses and ticker is present.
- [x] CHK-G71E-09: Short interest, average daily volume, and days to cover are finite and non-negative.
- [x] CHK-G71E-10: Duplicate primary keys are rejected by tests.
- [x] CHK-G71E-11: `source_quality`, `allowed_use`, `forbidden_use`, and observed label are enforced.
- [x] CHK-G71E-12: Reg SHO fields are not mixed into the short-interest fixture.
- [x] CHK-G71E-13: No live provider, bulk downloader, Reg SHO ingestion, OTC/ATS ingestion, squeeze score, candidate generation, state machine, alert, broker call, or dashboard runtime behavior is added.
- [x] CHK-G71E-14: Final context rebuild, validation matrix, SAW report validation, and closure packet validation pass.

G7.1F checks:

- [x] CHK-G71F-01: CFTC TFF tiny fixture policy exists and states fixture-only authority.
- [x] CHK-G71F-02: CFTC COT/TFF usage policy exists and states broad-regime-only use.
- [x] CHK-G71F-03: CFTC public provider fixture plan exists and holds live provider work.
- [x] CHK-G71F-04: Static CFTC TFF CSV exists for one report date and two broad financial futures markets.
- [x] CHK-G71F-05: CFTC fixture has a sidecar manifest with required fields.
- [x] CHK-G71F-06: Manifest SHA-256 value reconciles to artifact bytes.
- [x] CHK-G71F-07: Manifest row count reconciles to fixture rows.
- [x] CHK-G71F-08: `report_date` and `asof_position_date` parse.
- [x] CHK-G71F-09: `market_name`, `contract_market_code`, and allowed `trader_category` values are present.
- [x] CHK-G71F-10: Long, short, spreading, and open-interest values are finite and non-negative.
- [x] CHK-G71F-11: Duplicate primary keys are rejected by tests.
- [x] CHK-G71F-12: `source_quality`, `allowed_use`, `forbidden_use`, and observed label are enforced.
- [x] CHK-G71F-13: Single-name inference is forbidden and ticker/single-name columns are rejected.
- [x] CHK-G71F-14: No live provider, bulk downloader, CTA score, single-name inference, candidate generation, state machine, alert, broker call, or dashboard runtime behavior is added.
- [x] CHK-G71F-15: Final context rebuild, validation matrix, SAW report validation, and closure packet validation pass.

G7.1G checks:

- [x] CHK-G71G-01: FRED / Ken French tiny fixture policy exists and states fixture-only authority.
- [x] CHK-G71G-02: Macro / factor context usage policy exists and states context-only use.
- [x] CHK-G71G-03: FRED / Ken French public provider fixture plan exists and holds live provider work.
- [x] CHK-G71G-04: Static FRED macro CSV exists for three macro series and three dates per series.
- [x] CHK-G71G-05: Static Ken French factor CSV exists for one factor dataset and four monthly dates.
- [x] CHK-G71G-06: Both fixtures have sidecar manifests with required fields.
- [x] CHK-G71G-07: Manifest SHA-256 values reconcile to artifact bytes.
- [x] CHK-G71G-08: Manifest row counts and date ranges reconcile to fixture rows.
- [x] CHK-G71G-09: Date fields parse and `series_id` / `dataset_id` values are present.
- [x] CHK-G71G-10: Macro values and factor returns are finite numeric values.
- [x] CHK-G71G-11: Duplicate primary keys are rejected by tests.
- [x] CHK-G71G-12: `source_quality`, `allowed_use`, `forbidden_use`, and observed label are enforced.
- [x] CHK-G71G-13: FRED live API-key requirement is labeled `true_for_live_api` and no key is used.
- [x] CHK-G71G-14: Macro/factor score, ranking, alert, candidate, state-machine, and runtime columns are rejected.
- [x] CHK-G71G-15: No FRED provider, Ken French provider, live API call, API key handling, bulk downloader, macro regime score, factor regime score, candidate generation, state machine, alert, broker call, or dashboard runtime behavior is added.
- [x] CHK-G71G-16: Final context rebuild, validation matrix, SAW report validation, evidence validation, and closure packet validation pass.

G7.2 checks:

- [x] CHK-G72-01: Unified Opportunity State Machine architecture exists.
- [x] CHK-G72-02: Opportunity state transition policy exists.
- [x] CHK-G72-03: Forbidden-jump register exists.
- [x] CHK-G72-04: `opportunity_engine/states.py`, `schemas.py`, and `transitions.py` exist.
- [x] CHK-G72-05: State enum includes all required states.
- [x] CHK-G72-06: Required reason-code categories are implemented.
- [x] CHK-G72-07: Direct `THESIS_CANDIDATE -> BUYING_RANGE` jump is blocked.
- [x] CHK-G72-08: `LEFT_SIDE_RISK` must pass through accumulation or confirmation before `BUYING_RANGE`.
- [x] CHK-G72-09: `THESIS_BROKEN` overrides behavior strength.
- [x] CHK-G72-10: Estimated-only evidence cannot create `BUYING_RANGE`.
- [x] CHK-G72-11: Inferred-only evidence cannot create `LET_WINNER_RUN`.
- [x] CHK-G72-12: No state emits alert, broker action, score, or ranking fields.
- [x] CHK-G72-13: G7.2 focused tests, scoped compile, SAW validation, evidence validation, and closure packet validation pass.

G7.3 checks:

- [x] CHK-G73-01: Signal-to-state source map exists.
- [x] CHK-G73-02: Source eligibility policy exists.
- [x] CHK-G73-03: Signal confidence policy exists.
- [x] CHK-G73-04: `opportunity_engine/source_classes.py` and `signal_policy.py` exist.
- [x] CHK-G73-05: Source class enum includes `OBSERVED_OFFICIAL`, `OBSERVED_CANONICAL`, `OBSERVED_LICENSED`, `ESTIMATED_MODEL`, `INFERRED_RESEARCH`, `TIER2_DISCOVERY`, and `REJECTED`.
- [x] CHK-G73-06: All required signal families are mapped.
- [x] CHK-G73-07: SEC/FINRA/CFTC/FRED/KF fixtures support context and reason codes only.
- [x] CHK-G73-08: Estimated signals cannot alone move to `BUYING_RANGE`.
- [x] CHK-G73-09: Tier 2/yfinance cannot move states toward `BUYING_RANGE` or `LET_WINNER_RUN`.
- [x] CHK-G73-10: Options/IV/gamma/whales remain provider-gap signals.
- [x] CHK-G73-11: G7.3 focused tests, scoped compile, SAW validation, evidence validation, and closure packet validation pass.

G7.4 checks:

- [x] CHK-G74-01: Dashboard wireframe exists.
- [x] CHK-G74-02: Watchlist card spec exists.
- [x] CHK-G74-03: Daily brief spec exists.
- [x] CHK-G74-04: Dashboard sections include commander view, watchlist opportunity states, thesis health, entry discipline, hold discipline, GodView market behavior, risk and invalidation, what changed today, why not buy yet, and why not sell yet.
- [x] CHK-G74-05: Watchlist card fields include ticker, theme, current/previous state, reason, thesis/entry/hold/market/risk/freshness/source breakdown, blocked actions, and monitoring questions.
- [x] CHK-G74-06: Specs forbid buy/sell orders, alerts, scores, rankings, provider calls, broker calls, and runtime dashboard code.
- [x] CHK-G74-07: No `dashboard.py` or `views/*` runtime behavior is changed.
- [x] CHK-G74-08: G7.4 focused tests, SAW validation, evidence validation, and closure packet validation pass.

G8 checks:

- [x] CHK-G8-01: `opportunity_engine/candidate_card_schema.py` exists.
- [x] CHK-G8-02: `opportunity_engine/candidate_card.py` exists.
- [x] CHK-G8-03: `data/candidate_cards/MU_supercycle_candidate_card_v0.json` exists.
- [x] CHK-G8-04: `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json` exists.
- [x] CHK-G8-05: Candidate card requires ticker, theme, manifest, and source-quality summary.
- [x] CHK-G8-06: Initial state is limited to `THESIS_CANDIDATE` or `EVIDENCE_BUILDING`.
- [x] CHK-G8-07: Card cannot contain score, rank, buy/sell signal, alert, broker action, or buying-range claim.
- [x] CHK-G8-08: yfinance cannot be a canonical source.
- [x] CHK-G8-09: Estimated signals cannot be presented as observed.
- [x] CHK-G8-10: Options/IV/gamma/whales provider gap is explicit.
- [x] CHK-G8-11: G8 focused tests and G7.2/G7.3/G7.4 regression tests pass.
- [x] CHK-G8-12: Context rebuild, SAW validation, evidence validation, and closure packet validation pass.

## Delivered Artifacts

G7.1B deliverables:

- `docs/architecture/godview_data_infra_gap_assessment.md`
- `docs/architecture/godview_signal_source_matrix.md`
- `docs/architecture/godview_provider_roadmap.md`
- `docs/architecture/godview_signal_freshness_policy.md`
- `docs/architecture/godview_observed_vs_estimated_policy.md`
- `docs/architecture/codex_chrome_research_sop.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/handover/phase65_g71b_handover.md`
- `docs/saw_reports/saw_phase65_g7_1b_data_infra_gap_20260509.md`

G7.1C deliverables:

- `docs/research/g7_1c_open_source_repo_data_api_availability_survey_20260509.md`
- `docs/architecture/open_source_data_source_survey.md`
- `docs/architecture/godview_api_availability_matrix.md`
- `docs/architecture/godview_provider_selection_policy.md`
- `docs/architecture/godview_build_vs_borrow_decision.md`
- `docs/handover/phase65_g71-0c_handover.md`
- `docs/saw_reports/saw_phase65_g7_1c_open_source_api_survey_20260509.md`
- `docs/architecture/godview_public_source_audit.md`
- `docs/architecture/godview_source_terms_matrix.md`
- `docs/architecture/godview_tiny_fixture_schema_plan.md`
- `docs/architecture/godview_public_provider_priority.md`
- `docs/handover/phase65_g71c_source_audit_handover.md`
- `docs/saw_reports/saw_phase65_g7_1c_public_source_audit_20260509.md`

G7.1D deliverables:

- `docs/architecture/sec_tiny_fixture_policy.md`
- `docs/architecture/sec_public_provider_fixture_plan.md`
- `data/fixtures/sec/sec_companyfacts_tiny.json`
- `data/fixtures/sec/sec_companyfacts_tiny.json.manifest.json`
- `data/fixtures/sec/sec_submissions_tiny.json`
- `data/fixtures/sec/sec_submissions_tiny.json.manifest.json`
- `tests/test_g7_1d_sec_tiny_fixture.py`
- `docs/handover/phase65_g71d_sec_tiny_fixture_handover.md`
- `docs/saw_reports/saw_phase65_g7_1d_sec_tiny_fixture_20260509.md`

G7.1E deliverables:

- `docs/architecture/finra_short_interest_tiny_fixture_policy.md`
- `docs/architecture/finra_short_interest_vs_short_volume_policy.md`
- `docs/architecture/finra_public_provider_fixture_plan.md`
- `data/fixtures/finra/finra_short_interest_tiny.csv`
- `data/fixtures/finra/finra_short_interest_tiny.manifest.json`
- `tests/test_g7_1e_finra_short_interest_tiny_fixture.py`
- `docs/handover/phase65_g71e_finra_tiny_fixture_handover.md`
- `docs/saw_reports/saw_phase65_g7_1e_finra_tiny_fixture_20260509.md`

G7.1F deliverables:

- `docs/architecture/cftc_tff_tiny_fixture_policy.md`
- `docs/architecture/cftc_cot_tff_usage_policy.md`
- `docs/architecture/cftc_public_provider_fixture_plan.md`
- `data/fixtures/cftc/cftc_tff_tiny.csv`
- `data/fixtures/cftc/cftc_tff_tiny.manifest.json`
- `tests/test_g7_1f_cftc_tff_tiny_fixture.py`
- `docs/handover/phase65_g71f_cftc_tiny_fixture_handover.md`
- `docs/saw_reports/saw_phase65_g7_1f_cftc_tiny_fixture_20260509.md`

G7.1G deliverables:

- `docs/architecture/fred_ken_french_tiny_fixture_policy.md`
- `docs/architecture/macro_factor_context_usage_policy.md`
- `docs/architecture/fred_ken_french_public_provider_fixture_plan.md`
- `data/fixtures/fred/fred_macro_tiny.csv`
- `data/fixtures/fred/fred_macro_tiny.manifest.json`
- `data/fixtures/ken_french/ken_french_factor_tiny.csv`
- `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json`
- `tests/test_g7_1g_fred_ken_french_tiny_fixture.py`
- `docs/handover/phase65_g71g_fred_ken_french_tiny_fixture_handover.md`
- `docs/saw_reports/saw_phase65_g7_1g_fred_ken_french_tiny_fixture_20260509.md`

G7.2 deliverables:

- `docs/architecture/unified_opportunity_state_machine.md`
- `docs/architecture/opportunity_state_transition_policy.md`
- `docs/architecture/opportunity_state_forbidden_jumps.md`
- `opportunity_engine/__init__.py`
- `opportunity_engine/states.py`
- `opportunity_engine/schemas.py`
- `opportunity_engine/transitions.py`
- `tests/test_g7_2_opportunity_state_machine.py`
- `docs/handover/phase65_g72_state_machine_handover.md`
- `docs/saw_reports/saw_phase65_g7_2_state_machine_20260509.md`

G7.3 deliverables:

- `docs/architecture/godview_signal_to_state_map.md`
- `docs/architecture/godview_source_eligibility_policy.md`
- `docs/architecture/godview_signal_confidence_policy.md`
- `opportunity_engine/source_classes.py`
- `opportunity_engine/signal_policy.py`
- `tests/test_g7_3_signal_to_state_source_map.py`
- `docs/handover/phase65_g73_signal_to_state_handover.md`
- `docs/saw_reports/saw_phase65_g7_3_signal_to_state_map_20260509.md`

G7.4 deliverables:

- `docs/architecture/godview_dashboard_wireframe.md`
- `docs/architecture/godview_watchlist_card_spec.md`
- `docs/architecture/godview_daily_brief_spec.md`
- `tests/test_g7_4_dashboard_state_spec.py`
- `docs/handover/phase65_g74_dashboard_wireframe_handover.md`
- `docs/saw_reports/saw_phase65_g7_4_dashboard_wireframe_20260509.md`

G8 deliverables:

- `opportunity_engine/candidate_card_schema.py`
- `opportunity_engine/candidate_card.py`
- `data/candidate_cards/MU_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json`
- `tests/test_g8_supercycle_candidate_card.py`
- `docs/architecture/g8_supercycle_candidate_card_policy.md`
- `docs/architecture/supercycle_candidate_card_schema.md`
- `docs/handover/phase65_g8_supercycle_candidate_card_handover.md`
- `docs/saw_reports/saw_phase65_g8_supercycle_candidate_card_20260510.md`

## Explicitly Not Fixed Now

- yfinance migration;
- stale S&P sidecar;
- OPRA/options ingestion;
- SEC filing ingestion;
- CFTC ingestion;
- FRED / Ken French ingestion;
- FINRA short-interest ingestion;
- Reg SHO ingestion;
- FINRA squeeze score;
- microstructure feed;
- dashboard runtime behavior;
- state machine;
- candidate generation;
- signal ranking;
- inherited broad `compileall .` null-byte / ACL traversal debt.

## G7.1C Source Audit Result

The immediate no-cost implementation path is audited but not authorized:

1. SEC, FINRA, CFTC, FRED/ALFRED, and Ken French can support future public-source GodView modules.
2. Audit approval does not authorize ingestion.
3. Tiny fixture schemas are documented only; no physical fixtures were created.
4. Provider code requires explicit later approval.
5. The recommended next decision is `approve_g7_1d_one_tiny_public_provider_fixture_or_hold`.

G7.2 remains held. Any later G7.2 state machine must treat source availability as explicit constraints, not implemented facts.

## G7.1D SEC Tiny Fixture Result

The approved G7.1D SEC proof is materialized as static fixture data only:

1. `data/fixtures/sec/sec_companyfacts_tiny.json` stores two observed Apple Inc. company facts from the SEC companyfacts endpoint.
2. `data/fixtures/sec/sec_submissions_tiny.json` stores five Apple Inc. filing metadata rows from the SEC submissions endpoint.
3. Each fixture has a manifest recording source rights, raw locator, CIK, form types, as-of timestamp, row count, date range, SHA-256 hash, allowed use, forbidden use, rate-limit policy, and observed label.
4. `tests/test_g7_1d_sec_tiny_fixture.py` validates the static fixtures and negative failure paths.
5. No SEC provider class, downloader, ingestion path, canonical data write, signal score, candidate generator, state machine, alert, broker call, or dashboard runtime behavior is added.

Next recommended sequence:

```text
G7.1E FINRA short-interest tiny fixture -> G7.1F CFTC COT/TFF tiny fixture -> G7.1G FRED/Ken French macro fixture -> G7.2 state machine
```

Required source-label policy:

```text
Observed:
official filings, official short interest, Reg SHO volume, CFTC reported positioning,
FRED macro series, Ken French factor returns.

Estimated:
CTA pressure, squeeze pressure, whale intent, dark-pool accumulation,
dealer/gamma pressure.

Inferred:
thesis health, market regime state, entry discipline, hold discipline.
```

CFTC-specific lock:

```text
CFTC data may support broad regime / futures positioning.
It must not be used as direct single-name CTA buying evidence.
```

## G7.1E FINRA Short Interest Tiny Fixture Result

The approved G7.1E FINRA proof is materialized as static fixture data only:

1. `data/fixtures/finra/finra_short_interest_tiny.csv` stores three observed short-interest rows from FINRA Equity Short Interest file `shrt20260415.csv`.
2. `data/fixtures/finra/finra_short_interest_tiny.manifest.json` records source rights, official source URL, delayed freshness policy, settlement date, row count, date range, SHA-256 hash, allowed use, forbidden use, and observed label.
3. `tests/test_g7_1e_finra_short_interest_tiny_fixture.py` validates the static fixture and negative failure paths.
4. No FINRA provider, live API call, bulk download, Reg SHO ingestion, OTC/ATS ingestion, squeeze score, candidate generator, state machine, alert, broker call, or dashboard runtime behavior is added.

FINRA interpretation lock:

```text
Short interest = slow squeeze base.
Reg SHO short-sale volume = daily trading context.
Neither one alone = squeeze signal.

FINRA short interest may say "short base exists."
It may not say "forced covering is happening now."
```

Next recommended sequence:

```text
G7.1F CFTC COT/TFF tiny fixture -> G7.1G FRED/Ken French macro fixture -> G7.2 state machine
```

## G7.1F CFTC COT/TFF Tiny Fixture Result

The approved G7.1F CFTC proof is materialized as static fixture data only:

1. `data/fixtures/cftc/cftc_tff_tiny.csv` stores eight observed TFF rows from the CFTC current futures-only report for report date `2026-05-08` and as-of position date `2026-05-05`.
2. The fixture covers `E-Mini S&P 500` and `UST 10Y Note` with four TFF categories: `Dealer/Intermediary`, `Asset Manager/Institutional`, `Leveraged Funds`, and `Other Reportables`.
3. `data/fixtures/cftc/cftc_tff_tiny.manifest.json` records source rights, official source URL, weekly freshness policy, report/as-of dates, row count, date range, SHA-256 hash, allowed use, forbidden use, and observed label.
4. `tests/test_g7_1f_cftc_tff_tiny_fixture.py` validates the static fixture and negative failure paths.
5. No CFTC provider, live API call, bulk download, CTA score, single-name CTA inference, candidate generator, state machine, alert, broker call, or dashboard runtime behavior is added.

CFTC interpretation lock:

```text
CFTC TFF = broad regime / systematic-positioning context.
CFTC TFF != single-name CTA buying evidence.
CFTC TFF alone != buy/sell/hold state.

CFTC TFF may say "systematic/regime positioning context is supportive or hostile."
It may not say "CTAs are buying this stock today."
```

Next recommended sequence:

```text
G7.1G FRED/Ken French macro fixture -> G7.2 state machine
```

## G7.1G FRED / Ken French Tiny Fixture Result

The approved G7.1G macro/factor proof is materialized as static fixture data only:

1. `data/fixtures/fred/fred_macro_tiny.csv` stores nine observed FRED macro rows: `DGS10`, `M2SL`, and `BAA10Y`, with three dates each.
2. `data/fixtures/fred/fred_macro_tiny.manifest.json` records source rights, official source URL, live API key requirement, row count, date range, SHA-256 hash, allowed use, forbidden use, and observed label.
3. `data/fixtures/ken_french/ken_french_factor_tiny.csv` stores twelve observed Ken French factor-return rows for the Fama-French 3 factors monthly dataset across four dates.
4. `data/fixtures/ken_french/ken_french_factor_tiny.manifest.json` records source rights, official source URL, frequency, row count, date range, SHA-256 hash, allowed use, forbidden use, and observed label.
5. `tests/test_g7_1g_fred_ken_french_tiny_fixture.py` validates both static fixtures and negative failure paths.
6. No FRED provider, Ken French provider, live API call, API key handling, bulk download, macro regime score, factor regime score, candidate generator, state machine, alert, broker call, or dashboard runtime behavior is added.

Macro/factor interpretation lock:

```text
FRED = macro liquidity / rates / credit context.
Ken French = factor-return / benchmark context.
FRED + Ken French != macro score, factor score, alpha proof, ranking signal, or alert.

FRED fixture may support macro context and future regime panels.
It may not produce a macro regime score in this phase.
It may not use live API keys in this phase.

Ken French fixture may support factor/regime context and later benchmark comparison.
It may not be used to claim alpha or rank candidates in this phase.
```

Next recommended sequence:

```text
G7.2 Unified Opportunity State Machine -> G7.3 Signal-to-State Source Eligibility Map -> G7.4 Dashboard Wireframe / Product-State Spec
```

## G7.2 Unified Opportunity State Machine Result

The approved G7.2 state machine is implemented as definition-only logic:

1. `opportunity_engine/states.py` defines the required opportunity states and reason codes.
2. `opportunity_engine/schemas.py` defines transition evidence schemas with reason codes and source classes.
3. `opportunity_engine/transitions.py` validates allowed transitions and forbidden jumps.
4. `tests/test_g7_2_opportunity_state_machine.py` validates state completeness, forbidden jumps, thesis-broken override, estimated/inferred-only guards, crowded/frothy add-on gating, evidence requirements, and no score/ranking/action fields.
5. No candidate generation, search, score, ranking, alert, broker call, provider code, live API call, ingestion, or dashboard runtime behavior is added.

State-machine lock:

```text
State labels describe opportunity status.
They do not create buy/sell orders, alerts, scores, rankings, candidates, or broker actions.
```

## G7.3 Signal-to-State Source Eligibility Result

The approved G7.3 source map is implemented as policy-only logic:

1. `opportunity_engine/source_classes.py` defines source classes, signal families, and confidence labels.
2. `opportunity_engine/signal_policy.py` maps each signal family to source class, observed/estimated/inferred label, allowed influence, forbidden influence, freshness requirement, and confidence label.
3. `tests/test_g7_3_signal_to_state_source_map.py` validates source-map completeness and action-state blocks.
4. SEC/FINRA/CFTC/FRED/KF fixtures may support context and reason codes, not rankings or alerts.
5. Options, IV, gamma, whales, ETF, dark-pool, and microstructure remain provider/license-gap families.

Source-map lock:

```text
Estimated signals may modify confidence, but cannot alone create BUYING_RANGE.
Tier 2/yfinance cannot move any state toward BUYING_RANGE or LET_WINNER_RUN.
FRED/Ken French remain macro/factor context only, not alpha evidence.
```

## G7.4 Dashboard Wireframe / Product-State Spec Result

The approved G7.4 dashboard state spec is docs/product-only:

1. `docs/architecture/godview_dashboard_wireframe.md` defines ten state-first dashboard sections.
2. `docs/architecture/godview_watchlist_card_spec.md` defines required watchlist card fields.
3. `docs/architecture/godview_daily_brief_spec.md` defines daily brief sections and wording rules.
4. `tests/test_g7_4_dashboard_state_spec.py` validates spec completeness and no-score/no-ranking/no-alert/no-order boundaries.
5. No `dashboard.py`, `views/*`, Streamlit runtime, candidate card, alert, score, ranking, provider call, or broker path is added.

Dashboard-state lock:

```text
The dashboard spec is state-first, not score-first.
It explains what state an opportunity is in, why, what changed, and what remains blocked.
```

## DASH-1 Page Registry Shell Result

The approved DASH-1 runtime shell is implemented as a navigation/relocation-only change:

1. `views/page_registry.py` defines the approved page order, page groups, and legacy movement map.
2. `dashboard.py` now builds a Streamlit page registry/sidebar shell via `st.Page` / `st.navigation` and executes the selected page with `page.run()`.
3. Existing legacy content remains reachable under the new IA buckets:
   - Ticker Pool & Proxies -> Opportunities.
   - Data Health and Drift Monitor -> Settings & Ops.
   - Daily Scan, Backtest Lab, Modular Strategies, and Hedge Harvester -> Research Lab.
   - Portfolio Builder and Shadow Portfolio -> Portfolio & Allocation.
4. Command Center is placeholder-only; status badges are deferred to DASH-2.
5. Thesis Card, Market Behavior, and Entry & Hold Discipline are placeholders only.
6. No new data, metrics, product claims, provider calls, alerts, broker behavior, factor-scout integration, candidate generation, ranking, scoring, or buy/sell/hold output is added.

DASH-1 lock:

```text
DASH-1 = runtime shell and legacy relocation only.
DASH-1 != visual redesign, page redesign, new metrics, scoring, ranking, alerts, brokers, providers, factor scout, candidate generation, or buy/sell/hold output.
```

## G8 Supercycle Candidate Card Result

The approved G8 card is implemented as a definition/evidence-card-only research object:

1. `opportunity_engine/candidate_card_schema.py` defines the required card fields, allowed initial states, forbidden output flags, source-quality buckets, and provider-gap requirements.
2. `opportunity_engine/candidate_card.py` loads card/manifest JSON and validates the card bundle.
3. `data/candidate_cards/MU_supercycle_candidate_card_v0.json` stores one human-nominated MU candidate card.
4. `data/candidate_cards/MU_supercycle_candidate_card_v0.manifest.json` records the static card hash, allowed use, forbidden use, and source-policy boundary.
5. `tests/test_g8_supercycle_candidate_card.py` validates required fields, state limits, no-score/no-rank/no-signal/no-alert/no-broker boundaries, yfinance canonical rejection, estimated-vs-observed separation, and options/IV/gamma/whale provider-gap visibility.
6. No search, screening, ranking, score, backtest, replay, provider ingestion, dashboard runtime, alert, broker call, or investment recommendation is added.

Candidate-card lock:

```text
G8 card = structured research object.
G8 card != alpha search, score, rank, buying range, alert, trade, or promotion packet.
```

## Open Risks

- yfinance migration remains future debt.
- Primary S&P sidecar freshness remains stale through `2023-11-27`.
- Full GodView requires future licensed/provider decisions.
- Several GodView concepts are estimated or inferred and must never masquerade as observed facts.
- Broad workspace `compileall .` may continue to fail on inherited null bytes and ACL traversal outside G7.1G scope.
- FINRA API credentials/terms and FRED API key/third-party series-rights handling remain future provider-policy work.
- SEC fixture proof does not close the broader GodView provider gap or authorize SEC live ingestion.
- FINRA fixture proof does not authorize Reg SHO ingestion, squeeze scoring, alerts, or FINRA live provider work.
- CFTC fixture proof does not authorize CFTC provider work, CTA scoring, single-name inference, alerts, or G7.2 state-machine work.
- FRED / Ken French fixture proof does not authorize live providers, macro/factor scoring, ranking, alerts, or G7.2 state-machine work.
- G7.2 state-machine definition can be overread as trading advice if no-order/no-alert labels are removed.
- G7.3 provider-gap families still need future source/licensing decisions.
- G7.4 dashboard runtime remains future work and will require visual/runtime validation.

## Rollback Note

Revert only G8 candidate-card code, static card data, focused tests, policy docs, context, handover, and SAW report if rejected.

Do not revert G7.1G FRED/Ken French fixtures, G7.1F CFTC fixture docs, G7.1E FINRA fixture docs, G7.1D SEC fixture docs, G7.1A product canon, G7.1 roadmap realignment, G7 family artifacts, dashboard drift-monitor fix, or prior G phases.

## New Context Packet

## What Was Done
- Preserved D-353, R64.1, Candidate Registry, G0-G7, G7.1, G7.1A, G7.1B, G7.1C, G7.1D, G7.1E, and G7.1F as inherited baseline truth.
- Preserved G7.1G FRED / Ken French macro-factor fixture proof as context-only public-source truth.
- Completed G7.2 Unified Opportunity State Machine as definition-only schemas, transitions, docs, tests, handover, and SAW.
- Completed G7.3 Signal-to-State Source Eligibility Map as policy-only source classes, signal-family mapping, docs, tests, handover, and SAW.
- Completed G7.4 Dashboard Wireframe / Product-State Spec as docs/product-only dashboard sections, card spec, daily brief spec, tests, handover, and SAW.
- Completed G8 One Supercycle Gem Candidate Card for `MU` as candidate-card-only schema, validator, static JSON card, manifest, docs, tests, handover, and SAW.
- Added no provider code, live API call, API key handling, ingestion, source registry implementation, candidate generation, alpha search, screening, scoring, ranking, backtest, replay, alerts, broker calls, or dashboard runtime behavior.

## What Is Locked
- Terminal Zero remains the Unified Opportunity Engine.
- G7.1G is fixture-only.
- G7.2-G7.4 are definition/spec only.
- FRED is macro liquidity / rates / credit context, not a macro regime score.
- Ken French is factor-return / benchmark context, not alpha proof or candidate ranking.
- FRED live API use requires a registered API key and separate future provider approval; G7.1G uses no key.
- `source_quality`, `dataset_type`, and `observed_estimated_or_inferred = observed` are required for both fixture proofs.
- State labels do not create buy/sell orders, alerts, scores, rankings, candidates, or broker actions.
- Tier 2/yfinance cannot move states toward `BUYING_RANGE` or `LET_WINNER_RUN`.
- Provider-gap signal families remain held until licensed/provider decisions.
- G8 is one structured research object, not an investment recommendation.
- `MU_SUPERCYCLE_CANDIDATE_CARD_V0` may start only as `THESIS_CANDIDATE` or `EVIDENCE_BUILDING`.
- `BUYING_RANGE`, `ADD_ON_SETUP`, `LET_WINNER_RUN`, and `TRIM_OPTIONAL` remain forbidden for G8.
- Reg SHO, ATS/dark-pool, options/IV/gamma/whale data, signal scoring, candidate generation, dashboard runtime behavior, alerts, and broker calls remain held.

## What Is Next
- Recommended next action: `approve_g9_one_market_behavior_signal_card_or_hold`.
- Recommended G9 candidate: `FINRA_SHORT_INTEREST_SIGNAL_CARD_V0`.
- Alternative: hold with one MU candidate card sealed.
- ConfirmationRequired: YES
- Prompt: Reply "approve G9 one market behavior signal card" or "hold" to choose the next step.
- NextPhaseApproval: PENDING

## First Command
```text
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g7_2_opportunity_state_machine.py tests\test_g7_3_signal_to_state_source_map.py tests\test_g7_4_dashboard_state_spec.py -q
```

## Next Todos
- G8 validation and SAW are complete.
- Keep alpha search, screening, ranking, scoring, backtest, replay, providers, live calls, API key handling, ingestion, alerts, broker calls, and dashboard runtime behavior held.
- Hold for explicit G9 approval.

## DASH-2 Addendum - Portfolio Allocation Runtime Slice

- Current user-approved runtime slice: keep Portfolio Optimizer top-level, render YTD Performance below it, calculate YTD portfolio return from optimizer weights, and show SPY/QQQ YTD metrics.
- Freshness path: selected stocks and benchmarks use an in-memory yfinance adjusted-close overlay for display only.
- Boundary: no canonical provider ingestion, alert, broker call, candidate scoring/ranking, factor-scout integration, or candidate-card dashboard merge.
- Evidence:
  - `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 15 passed.
  - `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` -> PASS, 7 passed.
  - `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py` -> PASS.
  - Browser check at `http://127.0.0.1:8502/portfolio-and-allocation` -> optimizer before YTD, SPY/QQQ present, prices through `2026-05-08`.

## Dashboard Architecture Safety Slice Addendum

- Current user-approved architecture fix: centralize PID liveness, remove unsafe/unverified dashboard PID-file process control, collapse duplicated strategy-matrix initialization, and delegate dashboard price cleanup to data orchestration.
- Runtime safety:
  - `utils/process.py::pid_is_running` owns Windows-safe process liveness probing.
  - Dashboard, updater, parameter-sweep, release-controller, and phase16 optimizer lock/probe wrappers delegate to the shared helper.
  - `dashboard.py::spawn_backtest` refuses to start a second backtest when the PID file points to a live process rather than terminating an unverified PID.
- Dashboard helper boundary:
  - `_build_strategy_matrix` / `_ensure_modular_strategy_state` own strategy matrix initialization.
  - `_clean_portfolio_price_frame` delegates to `core.data_orchestrator.clean_price_frame`.
- Boundary: no canonical provider ingestion, market-data write, strategy search, ranking, scoring, alert, broker call, dashboard content redesign, or candidate-card dashboard merge.
- Evidence:
  - `.venv\Scripts\python -m py_compile utils\process.py dashboard.py data\updater.py scripts\parameter_sweep.py scripts\release_controller.py backtests\optimize_phase16_parameters.py tests\test_process_utils.py` -> PASS.
  - `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q` -> PASS, 103 passed.
  - HTTP smoke at `http://127.0.0.1:8501` -> PASS, HTTP 200.
  - SAW PASS in `docs/saw_reports/saw_dashboard_architecture_safety_20260511.md`.
  - Full pytest timed out after 304 seconds; longer full-regression window is required before phase-close proof.
