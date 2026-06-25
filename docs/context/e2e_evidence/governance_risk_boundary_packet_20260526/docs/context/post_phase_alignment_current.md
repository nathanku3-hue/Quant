# Post-Phase Alignment - Phase 65 G8.2

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, candidate validation, provider ingestion, strategy search, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: update the multi-stream map after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Portfolio Replay Role Contract

## What Changed This Round

- Replay, context, and selected-method artifact rows now carry `context_role` and `row_role`.
- Dashboard context normalization delegates to `strategies.strategy_replay.normalize_context_frame_for_replay(...)`.
- Saved selected-method artifacts without role columns hydrate defaults instead of crashing.
- Latest Snapshot renders `Replay Weight`; Allocation Snapshot renders `Current Weight`; decision tables render `Context Role`, `Replay Target`, and `Aux Audit Wt`.
- Replay diagnostics are generated from `DashboardReplayContext` and bind to run/source/method/cache identity.

## No Change

- Lifecycle/event `weight` remains audit intent, not allocation truth.
- Portfolio remains one selected-method `DashboardReplayContext`.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Formal SAW closure remains pending for this role-contract hardening round.

## What Should Not Be Done Next

- Do not infer replay semantics from UI copy or `status` alone.
- Do not add a private dashboard context normalizer.
- Do not rebuild replay to compute diagnostics.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

## What Changed This Round

- ENTER/EXIT and Buy/Sell visible weights are aligned to replay `target_weight`.
- Original aux `weight` values are preserved as `audit_weight`.
- Strategy Replay Timeline is now a stacked step-area allocation chart from replay target weights.
- The stacked timeline has executable Plotly trace coverage for `stackgroup="weights"`, `line.shape="hv"`, marker-free traces, and `CASH` ordering.
- Partial saved/transitional event and latest-snapshot schemas fail soft instead of crashing.
- SAW Reviewer B initially blocked on missing-column resilience; the findings were patched and covered by executable regressions.

## No Change

- Portfolio remains one `DashboardReplayContext`.
- Portfolio Performance still uses daily replay `portfolio_return`, not timeline sampling.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend dashboard_cache_signature emission / saved-artifact policy remains the separate replay artifact follow-up.

## What Should Not Be Done Next

- Do not let auxiliary lifecycle/event/decision weights override replay target weights.
- Do not treat `audit_weight` as a current allocation signal.
- Do not add direct lifecycle/trade JSONL render reads.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

## What Changed This Round

- Dashboard replay requests now use current signed allocation assets plus mapped in-window lifecycle/history tickers as context assets.
- Selected PIT loading and coverage pre-gate rows remain scoped to current signed allocation assets.
- History-only tickers are added as zero-weight `context_only` rows after backend bundle construction.
- MU can appear in 1Y replay decisions while remaining flat in the latest allocation snapshot.
- The strict backend context filter is preserved because the replay bundle itself is now horizon-aware.

## No Change

- `PortfolioReplaySelection` remains the current allocation handoff.
- Current allocation is not widened to thesis/history names.
- Saved artifact reads still require exact dashboard cache signature.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Formal SAW closure remains pending for this focused Frontend/UI source-scope repair.

## What Should Not Be Done Next

- Do not loosen `_normalize_context_frame(...)` as a display workaround.
- Do not add a separate full lifecycle panel as a second source for the same page.
- Do not treat historical horizon membership as a current allocation signal.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

## What Changed This Round

- Batched PIT replay loading now accepts selected permnos for price/return reads after building the full `r3000_pit` membership proof.
- Dashboard selected-method replay passes signed numeric replay assets to that selected-price load.
- MU/SNDK investigation moved into `trace_thesis_ticker_eligibility(...)` as a separate strategy/data diagnostic.
- SAW data-integrity review found and the round fixed a non-finite `total_ret` validity gap in local price/return diagnostics.
- Local trace shows MU and SNDK are not disappearing because of pinned-universe, ticker-map, latest PIT membership, or local price/return absence.

## No Change

- Dashboard replay is not watchlist-only.
- Signed replay selection remains the current allocation asset authority.
- PIT membership remains full-window proof.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Separate Strategy/Data analysis is needed only if the team wants to remediate MU/SNDK Rule100 history/candidate-frame exclusion rather than merely trace it.

## What Should Not Be Done Next

- Do not feed MU/SNDK diagnostic output into replay request construction.
- Do not shrink PIT membership proof to selected assets.
- Do not hide downstream gate failures by making replay watchlist-only.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

## What Changed This Round

- Portfolio & Allocation checks ready in-session daily replay context before rebuilding the daily replay source.
- A wider daily context can serve a shorter selected horizon only after non-date replay identity and actual daily row coverage are proven.
- Reused contexts are scoped to the selected horizon before rendering replay-facing surfaces.

## No Change

- Saved replay artifacts still require exact `dashboard_cache_signature`.
- PIT membership and selected-asset filtering semantics are unchanged.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Durable saved-artifact superset/subset policy remains a backend/dashboard coordination follow-up.

## What Should Not Be Done Next

- Do not extend in-session superset reuse to saved artifacts without separate reader validation and tests.
- Do not reuse a wider context without scoping rows and date window to the selected horizon.

## Latest Addendum - Max Replay Timeline Sampling Fix

## What Changed This Round

- Strategy Replay max-window weekly display sampling no longer calls `.normalize()` on a pandas `Series`.
- The sampler keeps weekly display rows from daily replay output and retains the final daily replay date.
- A focused executable regression now covers the long-window branch.

## No Change

- Daily replay context ownership, saved-artifact selection rules, and Portfolio Performance daily-only behavior are unchanged.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend producers still need dashboard_cache_signature emission for production saved-artifact UI hits.

## What Should Not Be Done Next

- Do not let display-sampled timeline rows drive Portfolio Performance.
- Do not create a second sampled replay request.
- Do not remove the long-window regression.

## Latest Addendum - Portfolio Replay Selection Identity Hardening

## What Changed This Round

- Frontend/UI now publishes an explicit signed `PortfolioReplaySelection` from optimizer controls.
- Dashboard replay request construction validates the signed selection and fails closed when it is missing or stale.
- Hidden `optimizer_universe` and first-10 column fallback no longer produce replay asset identity.

## No Change

- Backend artifact producer ownership for event/decision aux rows was not moved in this slice.
- Transitional backend build and source labels remain intact.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend producers still need dashboard_cache_signature emission for fully artifact-owned aux event/decision surfaces.

## What Should Not Be Done Next

- Do not use hidden session mirrors as replay source truth.
- Do not revive first-10 price-column fallback.
- Do not move aux producers without backend-owned artifact tests and SAW.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

## What Changed This Round

- Saved-artifact `DashboardReplayContext` construction now keeps artifact event and decision rows exactly as saved.
- Empty saved-artifact event/decision rows remain empty even when separately loaded dashboard fallback frames are non-empty.
- The Frontend/UI saved replay source-selector SAW report is mirrored under `docs/saw_reports/` for normal discoverability.
- Implementer and Reviewer A/B/C returned PASS for the single-source repair.

## No Change

- Backend reader internals were not modified in this repair.
- Transitional backend build remains labeled and only runs when allowed.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend artifact producers still need to emit `dashboard_cache_signature` before production saved artifacts can avoid the labeled transitional fallback.

## What Should Not Be Done Next

- Do not fill empty saved-artifact aux surfaces from separately loaded dashboard event/decision frames.
- Do not accept backend-valid saved artifacts for dashboard UI without dashboard cache-signature proof.
- Do not remove the transitional-build label while fallback remains possible.

## Latest Addendum - Backend Replay Reader Identity Hardening

## What Changed This Round

- Saved selected-method replay manifest validation now rejects blank `run_id`, `source_id`, and `method_id`.
- The blank-identity check runs before optional caller expected-ID matching, parquet reads, parquet/manifest equality, or bundle reconstruction.
- Regression coverage blanks both manifest and parquet identity while omitting expected `run_id` / `source_id`.
- The missing backend reader hardening SAW report is now published under `docs/saw_reports/`.

## No Change

- Dashboard runtime wiring was not changed.
- Saved artifact UI consumption still requires `dashboard_cache_signature`.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend artifact producers still need to emit `dashboard_cache_signature` before production saved artifacts can avoid the labeled transitional fallback.

## What Should Not Be Done Next

- Do not treat parquet/manifest equality as sufficient if manifest identity is blank.
- Do not accept backend-valid saved artifacts for dashboard UI without dashboard cache-signature proof.
- Do not remove the transitional-build label while fallback remains possible.

## Latest Addendum - Frontend/UI Saved Replay Source Selector

## What Changed This Round

- Frontend/UI added a pure dashboard replay request and source selector.
- Saved-artifact UI consumption now calls the backend saved reader and additionally requires `dashboard_cache_signature`.
- Transitional backend build remains labeled and only runs when fallback is allowed.
- Stale/unavailable saved artifacts clear replay/YTD session state instead of carrying prior latest weights.
- One `DashboardReplayContext` feeds YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log.

## No Change

- Backend reader internals were not modified in this frontend slice.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Backend artifact producers need to emit `dashboard_cache_signature` before production saved artifacts can avoid the labeled transitional fallback.

## What Should Not Be Done Next

- Do not accept backend-valid saved artifacts for dashboard UI without dashboard cache-signature proof.
- Do not remove the transitional-build label while fallback remains possible.
- Do not reintroduce direct lifecycle or compact Buy/Sell JSONL reads into `_render_strategy_replay_section()`.

## Latest Addendum - Overlay Overlap Anchor Fix

## What Changed This Round

- Scaled selected-price overlays require same-column local/live overlap.
- Scaled benchmark overlays require same-ticker local/live overlap.
- No-overlap stale selected assets and benchmark tickers are dropped/unavailable rather than stitched into current evidence.
- SAW Implementer and Reviewer A/B/C all passed.

## No Change

- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.

## What Should Not Be Done Next

- Do not reintroduce no-overlap overlay scaling as allocation, optimizer, benchmark, or YTD evidence.
- Do not treat display-only live overlays as canonical ingestion.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

## What Changed This Round

- Endpoint freshness now has one reusable snapshot for the loaded price matrix.
- Dashboard caches the snapshot by data source signatures, loader arguments, and matrix shape.
- Portfolio YTD, optimizer selected-price prep/default ordering, and universe eligibility reuse the snapshot.
- Actual local matrix probe showed exact endpoint parity with the legacy loop and lower scan cost.

## No Change

- Fail-closed stale asset behavior remains unchanged.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- SAW Reviewer A/B/C reconciliation remains open for governance closure.

## What Should Not Be Done Next

- Do not add new render-path callers that recompute full price endpoints when a `PriceEndpointFreshness` snapshot is already available.
- Do not treat endpoint caching as permission to loosen stale endpoint exclusion/drop behavior.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

## What Changed This Round

- Market-data freshness now uses per-asset endpoints across benchmark YTD, portfolio YTD, optimizer selected-price prep/order, and optimizer universe eligibility.
- Endpoint/tolerance semantics are centralized in `core.data_orchestrator`; universe eligibility passes policy tolerance explicitly.
- Benchmark YTD drops stale unresolved columns and reports a common endpoint for remaining curves.
- Portfolio YTD local fallback fails closed when any nonzero weighted leg is stale at the required endpoint.
- Optimizer selected assets and default ordering now respect endpoint freshness.
- Optimizer selected-price overlay requires same-column local/live overlap, so no-overlap stale-to-live stitching is non-evidence.
- Universe eligibility checks endpoint freshness in addition to observation count.

## No Change

- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Independent SAW rerun completed for endpoint freshness centralization; governance PASS is now claimed for that round.

## What Should Not Be Done Next

- Do not reintroduce shared-date freshness captions as proof of per-asset coverage.
- Do not reintroduce private endpoint/tolerance helper clones outside `core.data_orchestrator`.
- Do not reintroduce no-overlap overlay scaling as allocation or benchmark evidence.
- Do not treat display-only live overlays as canonical ingestion.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

## What Changed This Round

- Verified the dashboard selected-method replay path consumes backend `build_selected_method_replay(...)` through `_build_dashboard_strategy_replay_context(...)`.
- Verified the dashboard backend-bundle path uses per-date PIT replay inputs with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- Re-ran focused replay/dashboard checks, full repository pytest, and runtime smoke on `/portfolio-and-allocation`.
- Refreshed current truth surfaces to remove stale backend-bundle integration blockers.

## No Change

- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion evidence was added.

## Current Bottleneck

- Saved replay artifact-reader consumption and explicit cold-start/rerun performance-budget enforcement remain the next replay-architecture bottleneck.

## What Should Not Be Done Next

- Do not relabel the transitional build path as saved artifact-reader evidence.
- Do not treat full pytest/runtime smoke as strategy promotion evidence.

## Latest Addendum - Replay Coverage Contract Audit Fix

## What Changed This Round

- Uncovered coverage-plan replay dates now batch cash-closed rows instead of building one replay frame per date.
- Replay metadata keeps contiguous `coverage_segments`, and row reasons keep concrete `input_unavailable:<coverage_reason>` values.
- Row-heavy `no_priced_members` unavailable windows preserve explicit per-member rows while staying under the daily-scale budget.
- Replay performance now aligns generated weights to next tradable returns and recomputes loader-based equity once after output is combined.
- Tiny PIT replay frames use direct return lookup rather than long-form stack/merge overhead.
- Bound-feasible inverse-volatility targets return directly with diagnostics instead of invoking SLSQP.
- Duplicate shadowed coverage/perf tests were removed.
- Context bootstrap now selects the replay-audit New Context Packet from current truth surfaces before older same-phase handovers.
- Formal SAW Implementer and Reviewer A/B/C rechecks passed after resume.

## No Change

- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, or promotion evidence was added.

## Current Bottleneck

- Dashboard backend-bundle end-to-end consumption and runtime smoke are now verified; saved artifact-reader consumption remains the next integration bottleneck.

## What Should Not Be Done Next

- Do not relax replay performance tests without first preserving the batching/fast-path implementation evidence and PIT return-alignment regressions.
- Do not let `docs/context/current_context.*` validate against an older handover when `planner_packet_current.md` carries a newer complete New Context Packet.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

## What Changed This Round

- Backend now exposes `build_selected_method_replay(...)` as the selected-method replay bundle API with shared replay frame, context objects, CASH rows, and performance fields.
- Backend now persists selected-method replay evidence through `write_selected_method_replay_artifact_atomic(...)`, including run id, source id, method id, manifest metadata, and rollback-safe parquet+manifest promotion.
- Dashboard now uses `DashboardReplayContext` to feed Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell audit rows, and latest replay weights for Portfolio Performance.
- Portfolio Performance has display horizons (`YTD`, `1Y`, `3Y`, `5Y`, `Max`), but replay evidence remains PIT-governed per date with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- Buy/Sell Decision Log is latest-first and audit-only by default.

## No Change

- No provider ingestion, no canonical market-data write, no broker/live trading, no alerts, no rankings, no recommendations, and no strategy-promotion evidence were added.

## Current Bottleneck

- Saved replay artifact-reader consumption and explicit cold-start/rerun performance-budget enforcement remain after transitional backend-bundle consumption, full regression, and runtime smoke passed.

## What Should Not Be Done Next

- Do not claim full ultra-modular replay architecture PASS from focused backend/dashboard tests alone.
- Do not treat latest Buy/Sell audit rows as trade instructions.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

## What Changed This Round

- Added `rule100_config_from_max_weight(max_weight)` so visible Rule100 UI and Strategy Replay can use the user's cap without mutating frozen audit defaults.
- Wired direct Rule100 allocation and Strategy Replay to the same dynamic config; at `max_weight=0.35`, two equal eligible names target `35% / 35% / 30% cash`.
- Moved stale-aware benchmark construction to `core.data_orchestrator.build_benchmark_equity_from_prices(...)`.
- Benchmark YTD now decides freshness per ticker, overlays stale/missing tickers only, and does not forward-fill stale benchmark columns into a fresh-looking curve if overlay fails.

## No Change

- No frozen Rule100 history rewrite, no canonical market-data write, no provider ingestion, no broker behavior, no alerting, no ranking/scoring, no live trading, and no new optimizer objective.

## Current Bottleneck

- Manual product audit can now inspect visible Rule100 weights and QQQ YTD behavior; a 35% historical trace still requires a separate versioned/labeled artifact approval.

## What Should Not Be Done Next

- Do not regenerate `data/processed/rule100_softmax_v1_history.csv` as a 35% UI-policy artifact.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

## What Changed This Round

- Tightened replay input cache signatures so `r3000_pit` is the default and only accepted universe mode.
- Tightened replay artifact path validation so repo-local writes stay under `data/runtime_cache/strategy_replay`.
- Wired Portfolio & Allocation Strategy Replay to load one local PIT input slice per replay date before calling `build_strategy_replay(...)`.
- Added source guards proving dashboard replay uses `prices=replay_inputs` and not raw `prices_wide` slices.

## No Change

- No provider ingestion, canonical market-data write, target-weight artifact persistence, broker behavior, alerting, ranking/scoring, live trading, or new optimizer objective.

## Current Bottleneck

- SAW reconciliation and any separately requested full-regression/runtime-smoke window remain before phase-close proof.

## What Should Not Be Done Next

- Do not treat display-only price/return replay input artifacts as target-weight replay output artifacts.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

## What Changed This Round

- Aligned v1.1 with its research artifact contract: active outputs are comparison CSV and summary JSON only.
- Retired the stale `data/processed/rule100_softmax_v1_1_history.csv` to `.retired.csv`.
- Changed v1.1 coverage to count approved factor groups rather than raw columns.
- Added neutral missing-factor shrinkage toward `0.50`.
- Replaced copied mini-app AppTest coverage with real `AppTest.from_file("dashboard.py")` Policy Target Timeline proof.

## No Change

- No v1.1 runtime promotion, lifecycle log mutation, provider ingestion, broker behavior, alerting, ranking, scoring, or new optimizer objective.

## Current Bottleneck

- v1.1 still needs multi-date shadow evidence before any promotion decision.

## What Should Not Be Done Next

- Do not recreate active v1.1 history or treat retired history as current evidence.

## Latest Addendum - Rule of 100 Method Label

## What Changed This Round

- Added a PIT softmax v1 historical target-weight overlay at `data/processed/rule100_softmax_v1_history.csv`.
- Updated Position Lifecycle Replay transaction history to show `Event Weight` separately from `Softmax v1 Target` and `Softmax v1 Cash`.
- Preserved the original v0 lifecycle event ledger; no historical event weights were rewritten.
- Added regressions proving current TSM keeps event weight 10% but has softmax v1 target 0% and cash 80%.

## No Change

- No lifecycle log mutation, broker behavior, alert, ranking, scoring, provider ingestion, new optimizer objective, or Kelly stack expansion.

## Current Bottleneck

- Decide whether v1 should keep ordinal/equal-score 10% BUY entries or add richer continuous score inputs for visible >10% concentration.

## What Should Not Be Done Next

- Do not overwrite `data/portfolio_lifecycle_log.jsonl` to make history look like v1; use the overlay column.

## Previous Addendum - Rule of 100 Method Label

## What Changed This Round

- Added `Rule of 100` to the Portfolio Optimizer `Method` dropdown.
- Routed `Rule of 100` to Rule100 softmax v1 target weights over current lifecycle holds plus residual cash.
- Added focused AppTest coverage that proves `Rule of 100` bypasses optimizer execution even when fresh entry candidates exist.
- Added focused AppTest coverage that proves TSM drops from stale 10% lifecycle weight to 0% softmax target and cash rises to 80%.

## No Change

- No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, live trading, or generic strategy framework.

## Current Bottleneck

- Decide whether v1 should keep ordinal/equal-score 10%/10% behavior or add richer continuous score inputs for visible >10% concentration.

## What Should Not Be Done Next

- Do not interpret the dropdown label as a Phase 54 Rule-of-100 sleeve reopen or a new allocation optimizer.
- Do not fall back to lifecycle `last_weight` for explicit Rule of 100 sizing.

## Latest Addendum - Rule100 Lifecycle Policy v0

## What Changed This Round

- Promoted the concrete lifecycle strategy to Rule100 Lifecycle Policy v0.
- Added `Rule100State` proxy adapter for demand/supply/pricing/margin with explicit provenance.
- Added conviction entry sizing, v0 TRIM/TIGHTEN audit actions, and full-exit rules for hard stop or confirmed trend veto.
- Promoted runtime lifecycle log to 29 ENTER/EXIT events and regenerated the decision/audit tapes.
- Compared v0 against the prior 33-event baseline.

## No Change

- No generic strategy replay framework, provider ingestion, canonical write, alert, broker, ranking, scoring, dashboard recommendation label, or new optimizer objective.

## Current Bottleneck

- Decide after audit whether TRIM/TIGHTEN should stay audit-only or become actual weight changes in a future v1.

## What Should Not Be Done Next

- Do not extract a generic strategy contract until a second concrete strategy exists.
- Do not treat TRIM/TIGHTEN as portfolio weight changes in v0.

## Latest Addendum - Lifecycle Decision Export

## What Changed This Round

- Added export-only lifecycle decision logging for every PIT ticker-date row.
- Wrote `data/portfolio_lifecycle_decision_log.jsonl` and compact `data/portfolio_lifecycle_buy_sell_log.jsonl`.
- Wrote `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json` with action counts, reason counts, current open holds, round trips, and audit flags.
- Added regression coverage that exported BUY/SELL rows match `run_pit_replay(...)` emitted ENTER/EXIT events.

## No Change

- No runtime portfolio state mutation, UI action-label change, provider ingestion, canonical write, broker order, alert, ranking, scoring, or optimizer objective change.

## Current Bottleneck

- Audit the exported decision tape before implementing the true Rule-of-100 lifecycle policy.

## What Should Not Be Done Next

- Do not treat replay-analysis BUY/SELL labels as live recommendations or broker/execution instructions.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

## What Changed This Round

- Replaced stale `1 / replay_universe` lifecycle ENTER sizing with 10% max-10 sizing.
- Added PIT four-vector lifecycle confirmation using `z_demand`, `z_moat`, `z_inventory_quality_proxy`, and `z_discipline_cond`.
- Added 3-day entry confirmation, 20-day minimum hold, 2-day exit confirmation, 20% hard-exit override, and 10-day re-entry cooldown.
- Regenerated the runtime lifecycle log from the final policy: 33 events, no same-week round trips, open AMAT/LRCX/TSM holds.

## No Change

- No Phase 54 Rule-of-100 sleeve reopen, ranking, scoring, optimizer objective change, provider ingestion, alert, broker, conviction mode, Black-Litterman, or live trading.

## Current Bottleneck

- SAW closure/report validation remains before the round can be called fully closed.

## What Should Not Be Done Next

- Do not interpret the four-vector lifecycle confirmation as an approved ranking/scoring model or resurrected Rule-of-100 core sleeve.

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

## What Changed This Round

- Position Lifecycle Replay now drives current open holdings on Portfolio & Allocation.
- Open lifecycle ENTER positions without later PIT-safe EXIT events enter the universe as `included_current_hold`.
- No fresh PIT ENTER candidates with open lifecycle holds now renders held positions plus residual cash instead of 100% cash.

## No Change

- No provider ingestion, canonical write, alert, broker, ranking, scoring, conviction mode, Black-Litterman, or new optimizer objective.

## Current Bottleneck

- Focused bug round is closed as PASS; remaining work is optional lifecycle accounting policy review.

## What Should Not Be Done Next

- Do not treat today's scanner EXIT/KILL labels as a sell-all portfolio state unless lifecycle replay emits closing EXIT events.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

## What Changed This Round

- Added `dashboard._load_unified_data_cached(...)` with `st.cache_resource` around the expensive unified historical parquet package load.
- Added `core.data_orchestrator.build_unified_data_cache_signature(...)` to key the cache by processed/static source parquet resolved path, `mtime_ns`, and size.
- Added focused tests for cache-signature mutation and dashboard cache wiring.
- Updated truth surfaces, decision log, notes, lessons, and SAW report after full pytest and independent SAW reconciliation.

## Current Bottleneck

- The cache fix is closed with full pytest, runtime smoke, context validation, and SAW PASS. Remaining follow-ups are optional: behavior-level rerun-counter coverage and future copy discipline if a mutating dashboard consumer appears.

## What Should Not Be Done Next

- Do not expand this closure into provider ingestion, canonical market-data writes, alpha-engine loop rewrite, scanner financial-statement cache, scanner semantic changes, ranking, scoring, alerts, brokers, optimizer objective changes, or candidate-card dashboard integration.

## Latest Addendum - Dashboard Scanner Testability Hardening

## What Changed This Round

- Added `strategies/scanner.py` for deterministic dashboard scanner formulas.
- Updated `dashboard.py` so provider calls and payload persistence remain in the dashboard while enrichment delegates to the scanner module.
- Added focused tests for scanner macro/breadth/technical/entry/tactics/proxy/rating/leverage logic.
- Added direct coverage for adaptive trend regimes, production config invariants, core ETL parquet output, and the InvestorCockpit quality cap.
- Added shared synthetic price/return/macro/ticker-map fixtures in `tests/conftest.py`.

## Current Bottleneck

- Focused compile, affected tests, and full pytest pass. Remaining work is optional review continuation or hold.

## What Should Not Be Done Next

- Do not treat scanner extraction as approval for new scanner semantics, provider ingestion, canonical writes, ranking/scoring policy changes, alerts, brokers, dashboard redesign, or candidate-card runtime integration.

## Latest Addendum - Dashboard Architecture Safety Slice

## What Changed This Round

- Added `utils/process.py` as the shared process-liveness probe.
- Routed dashboard, updater, parameter-sweep, release-controller, and phase16 optimizer liveness wrappers through the shared helper.
- Removed dashboard backtest spawn's unconditional PID-file-owner termination path; live PID files now fail closed.
- Added source-level guard tests for unsafe runtime PID probes and unverified spawn termination.
- Collapsed dashboard strategy-matrix initialization into one helper path.
- Delegated dashboard portfolio price cleanup to `core.data_orchestrator.clean_price_frame`.

## Current Bottleneck

- Full pytest exceeded the local timeout; phase-close proof would need a longer test window. The architecture safety slice itself has focused tests, HTTP smoke, and SAW PASS evidence.

## What Should Not Be Done Next

- Do not expand this safety slice into dashboard module redesign, provider ingestion, canonical market-data writes, ranking, scoring, alerts, brokers, or candidate-card dashboard integration.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

## What Changed This Round

- Added `tests/test_optimizer_view.py` with Streamlit AppTest coverage for optimizer view rendering, mean-variance selection, and sector-cap UI paths.
- Added UI-to-SLSQP handoff coverage in `tests/test_optimizer_core_policy.py`.
- Added display-only Parquet overlay cache, background refresh scheduling, atomic cache writes, and copy-safe scale cache to `core/data_orchestrator.py`.
- Updated `views/optimizer_view.py` to use cached optimizer runs and the helper-based render path.

## Current Bottleneck

- Full regression, runtime smoke, and SAW now pass; only Low future runtime-hygiene follow-ups remain outside closure.

## What Should Not Be Done Next

- Do not turn the display overlay cache into canonical provider ingestion or canonical market-data writes.
- Do not start lower-bound policy, MU conviction, WATCH investability, Black-Litterman, alert, broker, ranking, scoring, or candidate-card dashboard merge work inside this hardening lane.

## Latest Addendum - Portfolio Data Boundary Refactor

## What Changed This Round

- Moved selected-stock display-refresh close extraction, local TRI scaling/stitching, and strategy metrics parsing into `core/data_orchestrator.py`.
- Updated `views/optimizer_view.py` to consume orchestrator helpers and stop importing yfinance or parsing `data/backtest_results.json` directly.
- Added data-orchestrator runtime tests and tightened DASH/provider-port tests.

## Current Bottleneck

- SAW rerun, context validation, full regression, and runtime smoke passed; inherited dashboard-level YTD yfinance debt remains future hygiene.

## What Should Not Be Done Next

- Do not turn the display freshness path into canonical provider ingestion or data writes.
- Do not start thesis-anchor, MU conviction, WATCH investability, Black-Litterman, alert, broker, ranking, scoring, or candidate-card dashboard merge work inside this hygiene lane.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

## What Changed This Round

- Added `strategies/optimizer_diagnostics.py` for feasibility, bound, constraint, solver, fallback, and severity reports.
- Updated `strategies/optimizer.py` to expose diagnostic-returning optimizer methods while preserving existing objectives and weight-returning compatibility methods.
- Updated `views/optimizer_view.py` to show optimizer status, feasibility, active constraints, active bounds, residuals, equal-weight pressure, and fallback labels.
- Converted optimizer audit strict xfail debt into passing implementation tests.

## Current Bottleneck

- Final validation and SAW must pass before the diagnostics round can close.

## What Should Not Be Done Next

- Do not start MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new optimizer objective, scanner rule, provider, alert, broker, or replay work inside this diagnostics lane.

## Latest Addendum - Optimizer Core Policy Audit

## What Changed This Round

- Opened optimizer-core lower-bound/SLSQP audit as policy-only work.
- Added docs and tests that keep the quarantined diff rejected as-is.
- No optimizer implementation or allocation math changed.

## Current Bottleneck

- Decide whether a future implementation round should fix infeasibility/fallback diagnostics and active-bound reporting.

## What Should Not Be Done Next

- Do not merge the quarantined optimizer diff without a future implementation approval and SAW.

## Latest Addendum - Portfolio Universe Quarantine Closure

## What Changed This Round

- Dirty optimizer-core lower-bound/SLSQP changes were quarantined and reverted out of the universe-construction closure.
- `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch` preserves the candidate optimizer-core diff for separate audit.
- `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md` now closes PASS with 9/9 checks.

## Current Bottleneck

- Decide whether to open `OPTIMIZER_CORE_POLICY_AUDIT` or hold; do not proceed to lower-bound implementation inside the universe lane.

## What Should Not Be Done Next

- Do not accept optimizer lower-bound/SLSQP math into the universe-construction patch.
- Do not start MU conviction, WATCH investability, Black-Litterman, scanner rewrite, broker, alert, or provider work.

## Latest Addendum - Portfolio Universe Construction Fix

## What Changed This Round

- `strategies/portfolio_universe.py` now separates optimizer eligibility from dashboard display order.
- `dashboard.py` passes audited included permnos and universe audit data into the optimizer view.
- `views/optimizer_view.py` shows Universe Audit and Why This Allocation diagnostics and no longer labels the Sharpe path as thesis-aware.
- Max-weight feasibility diagnostics now warn/fail before optimization when the cap creates infeasible or equal-weight-boundary behavior.

## No Change

- No MU hard floor, conviction optimizer, Black-Litterman view, thesis anchor sizing, manual override, scanner rewrite, provider ingestion, alert, broker behavior, or new portfolio objective.

## Current Bottleneck

- Decide whether to approve a thesis-anchor policy; until then the optimizer remains thesis-neutral.

## Header

- `ALIGNMENT_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-alignment`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `PREVIOUS_PHASE`: `G8.1B-R reviewer rerun and DASH-1 page registry shell`
- `NEXT_PHASE`: `G9 market-behavior signal card, G8.3 user-seeded candidate card, dashboard card reader, or hold`
- `OWNER`: `PM / Architecture Office`

## What Changed This Round

- G8.2 added one static MSFT candidate card and manifest from the existing `LOCAL_FACTOR_SCOUT` output.
- Candidate-card validation now rejects factor-score leakage.
- Context selection now recognizes the G8.2 handover after DASH-1 and before future G9.
- Dashboard runtime was inspected for the user-observed MSFT row, and G8.2 explicitly keeps that row separate from candidate-card status.

## No Change

- No new scout output.
- No DELL/AMD/LRCX/ALB card.
- No candidate ranking, scoring, validation, actionability, buy/sell/hold, buying range, alert, broker, provider, or dashboard runtime behavior.
- No legacy dashboard action label was changed.

## Current Bottleneck

- Choose whether to approve G9, G8.3, a dashboard card reader/status shell, or hold.

## What Should Not Be Done Next

- Do not merge the MSFT card into legacy dashboard action labels.
- Do not use the local factor scout as model validation.
- Do not turn public evidence pointers into thesis validation.
- Do not start provider ingestion or action-state work.

## Open Risks

- Legacy dashboard rows can visually resemble action guidance.
- Factor model validation remains future debt.
- Ownership/insider/options/market-behavior evidence remains missing.
- Broad dirty worktree remains inherited.
