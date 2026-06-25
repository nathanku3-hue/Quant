# Product Specification: Unified Opportunity Engine

Status: Canonical product/spec surface for Phase 65 Portfolio Universe Construction Fix
Date: 2026-05-10
Owner: PM / Architecture Office
Scope: docs and architecture only

## Current Phase 65 Notices

Portfolio Replay Role Contract (2026-05-15):

- `strategies.strategy_replay.REPLAY_COLUMNS`, `REPLAY_CONTEXT_COLUMNS`, and `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` carry `context_role` / `row_role`.
- `context_role` separates `current_holding`, `historical_context`, `flat_in_replay`, `cash`, and `unavailable` semantics.
- `row_role` separates `daily_portfolio`, `event_annotation`, and `buy_sell_decision` artifact rows.
- `dashboard.py::_normalize_dashboard_context_frame(...)` delegates to `strategies.strategy_replay.normalize_context_frame_for_replay(...)`.
- Older selected-method artifacts without role columns hydrate default roles on read; unrelated schema mismatches still fail closed.
- Diagnostics are generated from `DashboardReplayContext` and bind run/source/method/cache identity.
- No provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Dashboard Replay Aux Weight Semantics + Stacked Timeline (2026-05-15):

- `strategies.strategy_replay._normalize_context_frame(...)` emits replay-derived `target_weight` for event/decision context rows by joining normalized `(date, ticker)` back to replay output.
- `dashboard.py` aligns saved-artifact and transitional event/decision rows with `_align_context_weights_to_replay(...)`; `audit_weight` preserves the original auxiliary `weight` value.
- `dashboard.py::_render_replay_timeline_chart(...)` renders a stacked step-area allocation view from replay `target_weight`; `CASH` is muted and display-only.
- `dashboard.py::_render_strategy_replay_section(...)` fails soft when partial saved/transitional rows lack latest-snapshot display fields or event `action` fields.
- Tests cover backend aux alignment, dashboard aux alignment, MU context-only zero replay weight with preserved audit weight, stacked timeline source guards, and partial-schema render regressions.
- No provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Replay Selected Price Loading + MU/SNDK Eligibility Trace (2026-05-15):

- `load_batched_pit_replay_data(..., selected_permnos=...)` records full-window PIT membership metadata while limiting price/return columns to selected PIT members.
- Dashboard selected-method replay passes signed replay assets as numeric permnos into the batched loader and still filters the returned matrix to signed assets before backend replay execution.
- `trace_thesis_ticker_eligibility(...)` is the separate MU/SNDK diagnostic surface for pinned thesis universe, ticker-map, `r3000_pit`, local price/return, Rule100 history, current-hold/sizing, and failed gate truth.
- No watchlist-only replay, provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Max Replay Timeline Sampling Fix (2026-05-15):

- `dashboard.py::_sample_replay_timeline_from_daily(...)` uses `pd.to_datetime(weekly_index, errors="coerce").dropna().dt.normalize()` for weekly grouped keep-dates.
- The sampler keeps the last replay date per ISO year/week plus the final daily replay date.
- `tests.test_dash_2_portfolio_ytd::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay` covers a max-window branch with more than 160 daily replay dates.
- Weekly timeline sampling remains display-only and cannot feed Portfolio Performance or replace the daily replay source.

Portfolio Single-Source Replay Page (2026-05-14):

- `/portfolio-and-allocation` now coordinates one daily `DashboardReplayContext` for Portfolio Performance, allocation snapshot, Strategy Replay Timeline, ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log.
- `views.optimizer_view.render_optimizer_view(..., show_allocation_outputs=False)` leaves the top optimizer area as controls-only; the visible allocation evidence is `Allocation (Latest Daily Replay Snapshot)`.
- Portfolio Performance rejects non-daily replay and no longer falls back to optimizer weights or local/live/equal-weight price paths for replay-facing output.
- Strategy Replay Timeline uses display sampling only after daily replay rows exist.
- Latest Buys/Sells is a filtered view of `bundle.decision_rows`; no separate latest trade source is allowed in the render path.
- Focused source-guard tests cover the no-second-source render path; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Saved Artifact Single-Source Aux Surface Fix (2026-05-14):

- `dashboard.py::_dashboard_context_from_artifact_read(...)` preserves saved artifact `event_rows` and `decision_rows` exactly, including empty DataFrames.
- `tests.test_dash_2_portfolio_ytd::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows` covers daily saved rows with empty saved aux rows and non-empty fallback frames.
- `source_mode="saved_artifact"` now means replay rows, latest snapshot, ENTER/EXIT rows, and Buy/Sell rows are all artifact-owned.
- Focused compile and the focused frontend suite pass; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Backend Replay Reader Identity Hardening (2026-05-14):

- `strategies.strategy_replay._validate_manifest_bundle_fields(...)` rejects blank or non-string top-level manifest `run_id`, `source_id`, and `method_id`.
- `read_selected_method_replay_artifact(...)` performs that manifest bundle validation before optional expected-ID matching, parquet reads, or bundle reconstruction.
- `tests.test_strategy_replay_artifact` covers matching blank manifest+parquet identity with no expected `run_id` / `source_id` supplied by the caller.
- Focused replay artifact/strategy/coverage tests pass; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Portfolio Market-Data Freshness Endpoint Cache (2026-05-14):

- `core.data_orchestrator.PriceEndpointFreshness` is the reusable endpoint snapshot for a loaded price matrix.
- `core.data_orchestrator.build_price_endpoint_freshness(...)` computes per-column endpoints and the matrix required endpoint in one chunked pass.
- `dashboard.py` caches the endpoint snapshot by unified source file signatures, loader arguments, and matrix shape before passing it to portfolio YTD, optimizer rendering, and universe construction.
- `views.optimizer_view` and `strategies.portfolio_universe` accept the snapshot and avoid repeated full-matrix scans on render paths.
- Focused regressions prove stale assets still fail closed/drop while callers reuse supplied endpoint snapshots.

Portfolio Market-Data Freshness Fail-Closed Fix (2026-05-14):

- `core.data_orchestrator.price_latest_dates_by_column(...)`, `price_frame_latest_date(...)`, and `filter_price_frame_to_fresh_columns(...)` define the per-column endpoint freshness contract for display price frames.
- `core.data_orchestrator.price_column_latest_date(...)` and `price_endpoint_is_fresh(..., max_staleness_days=0)` define the shared endpoint/tolerance predicate; strict freshness is the default, and callers must pass tolerance explicitly.
- `core.data_orchestrator.build_benchmark_equity_from_prices(...)` drops stale benchmark columns that cannot be live-overlaid and reports a shared benchmark endpoint for remaining curves.
- `dashboard.py::_weighted_equity_curve(...)` accepts a required endpoint and returns unavailable when any nonzero weighted local leg is stale.
- `core.data_orchestrator.refresh_selected_prices_with_live_overlay(...)` accepts `required_latest`; `views.optimizer_view._prepare_selected_prices(...)` supplies the global price endpoint so stale selected assets are dropped instead of captioned as fresh.
- Selected optimizer overlays must pass the shared endpoint freshness filter after stitching; unresolved stale selected assets are dropped instead of treated as current evidence.
- `views.optimizer_view._order_assets_by_trailing_one_year_return(...)` demotes assets whose own endpoint is stale against the global endpoint.
- `strategies.portfolio_universe.build_optimizer_universe(...)` imports the shared core endpoint helpers and excludes assets whose price endpoint is older than `OptimizerUniversePolicy.max_endpoint_staleness_days`, even when history observation count is sufficient.
- Focused stale-data regressions and affected replay/dashboard tests pass; no provider ingestion, canonical write, broker behavior, alerts, ranking, scoring, recommendation, or promotion claim is authorized.

Dashboard Backend Bundle Integration Verification (2026-05-14):

- `dashboard.py::_build_dashboard_strategy_replay_context(...)` consumes `strategies.strategy_replay.build_selected_method_replay(...)`.
- The dashboard backend-bundle call uses `_dashboard_input_loader(...)` for per-date PIT inputs with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- `DashboardReplayContext` carries replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log rows, and the latest replay weights used by Portfolio Performance.
- The current consumer is a `transitional_build` path, not the saved artifact-reader path.
- Full pytest and runtime smoke passed for this verification; no provider ingestion, market-data write, broker behavior, alerts, ranking, scoring, recommendations, or promotion claim is authorized.

Replay Coverage Contract Audit Fix (2026-05-14):

- `strategies.strategy_replay._build_run_metadata(...)` records contiguous replay coverage segments in `date_window["coverage_segments"]`.
- `strategies.strategy_replay._build_replay_from_input_loader(...)` preserves specific unavailable causes as `input_unavailable:<coverage_reason>` and batches uncovered-date cash-closed rows before attaching performance.
- `strategies.strategy_replay._build_replay_from_input_loader(...)` preserves row-heavy explicit-member unavailable windows under the daily-scale budget.
- `strategies.strategy_replay._attach_replay_performance(...)` aligns allocation-date weights to next tradable returns and uses a small-frame lookup for tiny PIT frames while preserving the vectorized path for larger replay frames.
- `strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics(...)` can return the closed-form inverse-volatility target without SLSQP when that target already satisfies max-weight bounds.
- `scripts.build_context_packet.build_context_packet(...)` selects complete New Context Packets from current truth surfaces before older same-phase handovers.
- The replay coverage/performance tests and full pytest suite pass after the audit fix.

Data/PIT Strategy Replay Hardening (2026-05-13):

- `core.data_orchestrator.build_strategy_replay_cache_signature(...)` has `universe_mode="r3000_pit"` as the default and rejects any other mode.
- `core.data_orchestrator.load_strategy_replay_inputs(...)` loads local parquet matrices with `asof_date` and clamps rows to `date <= as_of_date`.
- `core.data_orchestrator.write_strategy_replay_artifact_atomic(...)` rejects repo-local `data/` writes outside `data/runtime_cache/strategy_replay`.
- `dashboard.py::_render_strategy_replay_section()` loads one `StrategyReplayInputs` object per replay date and calls `strategies.strategy_replay.build_strategy_replay(..., prices=replay_inputs, as_of_range=None)`.
- Input artifacts contain price/return matrices; target-weight output is generated by `build_strategy_replay(...)` and displayed only.

Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay (2026-05-13):

- `strategies.rule100_softmax.Rule100SoftmaxConfig()` remains the frozen audit default with `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- `strategies.rule100_softmax.rule100_config_from_max_weight(max_weight)` is the dynamic visible allocation helper and sets `gross_budget_per_name=max_weight`, `max_single_name_weight=max_weight`, and `gross_budget_cap=1.0`.
- `views.optimizer_view.render_optimizer_view(...)` passes the optimizer `Max weight` control into the direct `Rule of 100` allocation path.
- `strategies.strategy_replay.build_strategy_replay(...)` uses the same dynamic Rule100 config for `OptimizationMethod.RULE_OF_100`.
- `core.data_orchestrator.build_benchmark_equity_from_prices(...)` detects stale/missing benchmark columns per ticker and calls live overlay only for those tickers; columns that cannot be refreshed are not forward-filled into fresh benchmark curves.
- `dashboard.py::_build_benchmark_equity(...)` delegates to that helper and labels blended benchmark sources as `local+live_overlay`.

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

Portfolio Lifecycle Replay Churn + Weight Policy (2026-05-12):

- `scripts/pit_lifecycle_replay.py` owns replay entry sizing, lifecycle factor confirmation, entry/exit confirmation, minimum-hold, hard-exit, and cooldown state.
- `replay_entry_weight()` returns `0.10` by default from `DEFAULT_MAX_POSITIONS = 10`.
- `lifecycle_factor_confirmation(...)` requires at least 3 present and positive values across `z_demand`, `z_moat`, `z_inventory_quality_proxy`, and `z_discipline_cond`.
- ENTER needs raw PIT eligibility plus 3 consecutive confirmed days and no active 10-day post-exit cooldown.
- EXIT needs either `dist_sma20 > 0.20` or a raw exit after 20 holding days with 2 consecutive exit confirmations.
- This is replay/current-hold state discipline only; it does not approve the rejected Phase 54 Rule-of-100 sleeve, ranking, scoring, optimizer objective changes, alerts, broker behavior, provider ingestion, or live trading.

Rule of 100 Method Label (2026-05-12):

- `strategies.optimizer.OptimizationMethod.RULE_OF_100` exposes the exact dropdown label `Rule of 100`.
- `views.optimizer_view.render_optimizer_view(...)` routes `Rule of 100` directly to Rule100 softmax v1 target weights plus residual cash and does not call the cached optimizer run.
- Empty or all-ineligible softmax state under `Rule of 100` renders cash-only session state instead of stale lifecycle weights.
- This is a UI label for the concrete lifecycle policy, not a new optimizer objective, ranking model, alert, broker path, or live recommendation.

Rule100 Softmax v1 Audit (2026-05-12):
- `strategies/rule100_softmax.py` owns the pure softmax sizing helpers and the Kelly comparator shim.
- `scripts/rule100_softmax_v1_audit.py` owns the shared PIT replay/audit harness and writes versioned audit artifacts.
- Softmax v1 is the primary sizing path for both audit artifacts and the explicit `Rule of 100` UI method; Kelly is comparator-only on the same frame.
- Current live target is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%.
- `data/processed/rule100_softmax_v1_history.csv` is the historical v1 target-weight overlay; it keeps v0 lifecycle event weights separate from `softmax_v1_target_weight`.
- `dashboard.py` Position Lifecycle Replay transaction log must label the original ledger weight as `Event Weight` and the overlay as `Softmax v1 Target`.
- This does not change the lifecycle replay log or any broker/alert/ranking/scoring behavior.

Rule100 Softmax v1.1 Research Contract (2026-05-12):

- `strategies/rule100_softmax_v1_1.py` owns the research-only v1.1 scoring helper; `scripts/rule100_softmax_v1_1_audit.py` owns the audit artifact writer.
- The active artifact set is `data/processed/rule100_softmax_v1_1_comparison.csv` and `data/processed/rule100_softmax_v1_1_summary.json`; `rule100_softmax_v1_1_history.csv` is not an active v1.1 artifact.
- `factor_present_count` and `factor_positive_count` count approved groups only: demand, inventory/supply, moat/pricing, and capital discipline.
- Factor strength uses group percentile ranks and neutral missing-group shrinkage: `mean_available_rank * coverage + 0.50 * (1 - coverage)`.
- `tests/test_policy_target_timeline_apptest.py` must exercise `AppTest.from_file("dashboard.py")`, not copied mini-apps, for the Policy Target Timeline regression.

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

## Portfolio Lifecycle Current Holds Addendum

- Current holdings are reconstructed from latest lifecycle ENTER/EXIT events at or before the current as-of timestamp.
- A later EXIT closes a holding; future-dated replay rows do not affect today's current portfolio.
- Portfolio & Allocation renders open lifecycle holdings plus residual cash when replay is not sell-all and there are no fresh PIT ENTER candidates.
- JSON position memory is a fallback only when lifecycle replay evidence is empty.
- Residual cash is preserved in both allocation display and live ticker performance paths for sub-100% lifecycle holdings.
- No provider ingestion, broker behavior, alert, ranking, scoring, or new optimizer objective is added.

## Portfolio Replay Selection Identity Addendum

- Portfolio & Allocation publishes `PortfolioReplaySelection` from optimizer controls before replay surfaces render.
- Replay request construction validates the signed selection against method, cap, risk-free rate, typed replay assets, current price-frame identity, and selected price content.
- Missing or stale selection renders replay unavailable; hidden `optimizer_universe` and first-10 column fallback are forbidden replay sources.
- Dashboard-loaded aux event/decision rows remain a labeled transitional bridge until backend artifacts own dashboard cache signature emission.

## Lifecycle Decision Export Addendum

- `scripts/pit_lifecycle_replay.py --export-only` writes a full PIT decision tape and compact buy/sell tape without mutating lifecycle event state.
- BUY/SELL export rows must exactly match replay ENTER/EXIT events.
- Each export row includes reason codes, factor/gate state, streaks, hold days, cooldown state, and Rule-of-100 proxy fields.
- BUY/SELL fields are audit labels only and do not create recommendations, broker orders, alerts, rankings, scores, or dashboard action labels.

## Rule100 Lifecycle Policy v0 Addendum

- `Rule100State` owns the v0 factor adapter and exposes proxy provenance for demand, supply, pricing, and margin.
- Runtime lifecycle events remain ENTER/EXIT for dashboard compatibility.
- Decision tape lifecycle actions are BUY, HOLD, TRIM, TIGHTEN, EXIT, and NO_ACTION.
- TRIM has `suggested_weight_delta = -0.025`; TIGHTEN has `suggested_weight_delta = 0.0`; neither changes actual v0 weights.
- Entry sizing formula is `min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
- No generic replay framework, provider ingestion, broker behavior, alert, ranking, scoring, or dashboard recommendation label is added.

## Optimizer History Diagnostics Split Addendum

- `OptimizerUniverseResult.insufficient_history` remains the fail-closed backend bucket for local price-readiness failures.
- The Portfolio Optimizer UI splits that bucket into:
  - `Missing History`: no local price column or fewer than the policy minimum observations.
  - `Stale Endpoint`: sufficient observations exist, but the column endpoint is older than the required local matrix endpoint tolerance.
- The Universe Audit table includes `Latest Price Date` so stale endpoint rows are diagnosable without implying short history.
- `History Fail` must not be used as the visible aggregate label for this mixed condition.
- No provider ingestion, canonical write, broker behavior, alert, ranking, scoring, recommendation, or live trading is added.
