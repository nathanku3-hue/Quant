# Observability Pack - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, candidate validation, provider ingestion, strategy search, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: make drift visible early after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Portfolio Replay Role Contract

## High-Risk Attempts

- Treating `context_role` as UI decoration rather than schema contract.
- Reintroducing a dashboard-only context normalizer that can drift from strategy replay.
- Letting old saved artifacts crash only because role columns are missing.
- Computing diagnostics by rebuilding replay instead of reading `DashboardReplayContext`.

## Drift Signal

- `REPLAY_COLUMNS`, `REPLAY_CONTEXT_COLUMNS`, and `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` should include `context_role` and `row_role`.
- `dashboard._normalize_dashboard_context_frame(...)` should call `normalize_context_frame_for_replay(...)`.
- Latest Snapshot AppTest should look for `Replay Weight`, not generic `Weight`.
- Route smoke should find `Context Role` plus `Current Weight` / `Replay Weight` tables.
- `tests/test_strategy_replay_artifact.py::test_read_selected_method_replay_artifact_hydrates_legacy_role_columns` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_replay_context_diagnostics_use_existing_bundle_identity` should remain in focused verification.

## Evidence Used

- `strategies/strategy_replay.py`
- `dashboard.py`
- `tests/test_strategy_replay.py`
- `tests/test_strategy_replay_artifact.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_policy_target_timeline_apptest.py`

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

## High-Risk Attempts

- Displaying lifecycle/event/decision `weight` as if it were selected-method replay target weight.
- Dropping original aux weights entirely instead of preserving them as audit metadata.
- Treating the stacked timeline as a second replay/performance source.
- Letting partial saved/transitional aux schemas crash Strategy Replay rendering.

## Drift Signal

- `strategies.strategy_replay._normalize_context_frame(...)` should derive context `target_weight` from replay rows.
- `dashboard._align_context_weights_to_replay(...)` should preserve original aux `weight` as `audit_weight` and set visible `weight` to replay `target_weight`.
- `_render_replay_timeline_chart(...)` should use `stackgroup="weights"` and line shape `hv` over replay `target_weight`.
- `tests/test_dash_2_portfolio_ytd.py::test_replay_timeline_stacked_chart_traces_are_allocation_areas` should continue to validate actual Plotly trace semantics, not only source text.
- `_render_strategy_replay_section(...)` should guard partial event/snapshot schemas before chart/table render.
- `tests/test_strategy_replay.py::test_selected_method_aux_context_targets_replay_weights_not_legacy_aux_weights` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_aux_weights_align_to_replay_targets` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_strategy_replay_section_ignores_event_rows_missing_action` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_strategy_replay_section_handles_partial_latest_snapshot` should remain in focused verification.

## Evidence Used

- `dashboard.py`
- `strategies/strategy_replay.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_strategy_replay.py`

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

## High-Risk Attempts

- Loosening `_normalize_context_frame(...)` so context rows can display tickers absent from the replay frame.
- Mutating `PortfolioReplaySelection` to include historical flat tickers, which would widen current allocation semantics.
- Adding a second lifecycle-history panel that bypasses `DashboardReplayContext`.
- Treating NBIS or other thesis names as missing replay history without decision-tape rows.

## Drift Signal

- `_build_dashboard_replay_request(...)` should call `_horizon_replay_assets_for_window(...)`.
- `_current_full_replay_signature(...)` should use the same horizon-aware asset union as request construction.
- `_current_replay_assets_key()` should still return only the signed current selection.
- `_build_dashboard_strategy_replay_context(...)` should pass `request.allocation_assets` to selected PIT loading and per-date input filtering.
- `_dashboard_filter_coverage_plan_to_assets(...)` should keep coverage pre-gate unavailable rows scoped to current allocation assets.
- `_append_context_only_replay_rows(...)` should add history-only tickers as zero-weight `context_only` rows before dashboard context normalization.
- `_strategy_replay_cache_signature(...)` should include `allocation_assets` as well as `replay_assets`.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_replay_request_expands_assets_for_horizon_trade_history` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_context_only_horizon_asset_does_not_enter_real_optimizer` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_coverage_prefilter_uses_allocation_assets_not_full_pit_membership` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_cache_signature_distinguishes_allocation_assets_from_context_assets` should remain in focused verification.

## Evidence Used

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

## High-Risk Attempts

- Filtering PIT membership to selected replay assets before membership proof is built.
- Treating selected-price loading as authorization for watchlist-only replay.
- Using MU/SNDK diagnostic output to alter dashboard replay asset selection.
- Collapsing all exclusions into "data missing" instead of distinguishing data unavailable, PIT membership, factor threshold, technical quality, sizing eligibility, and current-hold state.
- Treating positive price plus non-finite `total_ret` as a valid local price/return row.

## Drift Signal

- `load_batched_pit_replay_data(...)` metadata should keep `pit_membership_proof = "full_window_membership_index"`.
- `price_load_scope` should be `selected_pit_membership_intersection` only after full `union_permnos` is known.
- `_build_dashboard_strategy_replay_context(...)` should pass `_numeric_replay_permnos(request.replay_assets)` to the cached batched loader.
- `trace_thesis_ticker_eligibility(...)` should remain outside dashboard replay request construction.
- `_valid_price_return_rows(...)` should reject `inf`, `-inf`, and `NaN` returns before declaring local price/return evidence present.
- `tests/test_data_orchestrator_portfolio_runtime.py::test_batched_pit_loader_keeps_full_membership_proof_while_loading_selected_prices` should remain in focused verification.
- `tests/test_pinned_universe.py::test_trace_thesis_ticker_eligibility_answers_mu_sndk_gates` should remain in focused verification.
- `tests/test_pinned_universe.py::test_trace_thesis_ticker_eligibility_rejects_non_finite_return_rows` should remain in focused verification.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight` should keep proving selected-permno loader handoff with a non-selected PIT member.

## Evidence Used

- `core/data_orchestrator.py`
- `dashboard.py`
- `scripts/pit_lifecycle_replay.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_optimizer_view.py`
- `tests/test_pinned_universe.py`
- `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json`

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

## High-Risk Attempts

- Treating any different `replay_dates` signature as stale even when the cached daily replay is a wider in-session superset.
- Reusing a wider context without checking actual `replay_df["date"]` row coverage.
- Reusing a wider context without scoping replay rows, latest snapshot, events, decisions, and date window back to the selected horizon.
- Extending this in-session policy to durable saved artifacts without separate reader/subset validation.

## Drift Signal

- `_ensure_daily_portfolio_replay_context(...)` should call `_valid_cached_ytd_replay_context(...)` before the spinner/build path.
- `_valid_cached_ytd_replay_context(...)` should compare signatures without `replay_dates` only for in-session superset reuse and should require actual requested-date row coverage.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_cached_ytd_replay_context_reuses_superset_for_shorter_horizon` should remain in the focused suite.
- Saved-artifact reads should continue requiring exact `dashboard_cache_signature` until a separate policy exists.

## Evidence Used

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Latest Addendum - Max Replay Timeline Sampling Fix

## High-Risk Attempts

- Calling `.normalize()` directly on a pandas `Series` returned by grouped weekly replay dates.
- Treating weekly sampled timeline rows as replay evidence for Portfolio Performance.
- Removing the executable long-window sampler regression and relying only on source-guard tests.

## Drift Signal

- `_sample_replay_timeline_from_daily(...)` should use `.dt.normalize()` after grouping dates into a Series.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay` should remain in the focused suite.
- The sampler should continue returning `weekly_display_from_daily` for long display windows only.

## Evidence Used

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Latest Addendum - Portfolio Replay Selection Identity Hardening

## High-Risk Attempts

- Reusing `optimizer_universe` as replay asset identity.
- Reintroducing `prices_wide.columns[:10]` or equivalent first-N fallback for replay requests.
- Keeping stale signed selection after optimizer builder failures or skipped data paths.
- Dropping selected price content or typed asset identity from replay signatures.
- Treating dashboard-loaded aux event/decision rows as final backend replay ownership.

## Drift Signal

- `_build_dashboard_replay_request(...)` should call `_current_portfolio_replay_selection(...)`.
- Runtime replay selection should not contain `optimizer_universe` or first-10 column fallback.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_replay_request_fails_closed_without_signed_selection` should remain in the focused suite.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_builder_error_clears_signed_replay_selection` should remain in the focused suite.

## Evidence Used

- `dashboard.py`
- `views/optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

## High-Risk Attempts

- Backfilling empty saved-artifact ENTER/EXIT or Buy/Sell rows from separately loaded dashboard frames while still labeling the context `source_mode="saved_artifact"`.
- Treating daily portfolio rows as sufficient proof that all replay-facing saved-artifact surfaces are artifact-owned.
- Leaving SAW evidence only under `docs/context/` where normal report discovery misses it.

## Drift Signal

- `_dashboard_context_from_artifact_read(...)` should not replace empty artifact `event_rows` or `decision_rows` with `event_annotations` / `buy_sell_decisions`.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows` should remain in the saved-artifact regression set.
- `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md` should remain referenced by current truth surfaces.

## Evidence Used

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md`

## Latest Addendum - Backend Replay Reader Identity Hardening

## High-Risk Attempts

- Treating blank manifest `run_id`, `source_id`, or `method_id` as valid because parquet rows carry the same blank values.
- Relying on optional caller-supplied expected `run_id` / `source_id` as the only saved artifact identity guard.
- Moving manifest identity checks after parquet reads or bundle reconstruction.
- Claiming backend SAW closure without a concrete report artifact under `docs/saw_reports/`.

## Drift Signal

- `_validate_manifest_bundle_fields(...)` should reject blank/non-string `run_id`, `source_id`, and `method_id`.
- `read_selected_method_replay_artifact(...)` should keep manifest bundle validation before `_validate_replay_context_match(...)`, `pd.read_parquet(...)`, and `_bundle_from_selected_method_artifact(...)`.
- Tests should keep the case where both manifest and parquet identities are blank and expected IDs are omitted.
- `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md` should remain referenced by current truth surfaces.

## Evidence Used

- `strategies/strategy_replay.py`
- `tests/test_strategy_replay_artifact.py`
- `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`

## Latest Addendum - Frontend/UI Saved Replay Source Selector

## High-Risk Attempts

- Treating a backend-valid saved artifact as dashboard-current without exact `dashboard_cache_signature`.
- Silently rebuilding replay without labeling the source as transitional.
- Reusing prior `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY` or cached YTD context after a stale/unavailable artifact.
- Moving ENTER/EXIT annotations or Buy/Sell Decision Log back to direct render-path JSONL reads.

## Drift Signal

- `_build_dashboard_replay_request(...)` should remain free of artifact reads and backend build calls.
- `_read_dashboard_saved_replay_artifact(...)` should keep calling backend `read_selected_method_replay_artifact(...)`.
- Saved-artifact context should require dashboard cache signature matching method, cap, controls, assets, dates, sampling, and data signature.
- UI captions should say saved artifact, transitional build, or unavailable; they should not use promotion/action/trading language.

## Evidence Used

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`
- `tests/test_position_lifecycle.py`
- `tests/test_policy_target_timeline_apptest.py`

## Latest Addendum - Overlay Overlap Anchor Fix

## High-Risk Attempts

- Reintroducing first-live-to-last-local scaling when there is no same-ticker overlap date.
- Treating a live overlay row as selected-price, benchmark, optimizer, or YTD evidence before an overlap anchor exists.
- Adding a new cache key or helper flag that bypasses the overlap-anchor invariant.

## Drift Signal

- `scale_live_overlay_to_local(...)` should not expose a public permissive no-overlap flag.
- Benchmark and selected-price overlay tests should keep no-overlap drop regressions.
- Source labels may say overlay unavailable/dropped, but must not imply synthetic continuity is evidence.

## Evidence Used

- `core/data_orchestrator.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/saw_reports/saw_overlay_overlap_anchor_fix_20260514.md`

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

## High-Risk Attempts

- Reintroducing repeated `price_latest_dates_by_column(prices_wide, all_columns)` scans inside dashboard render branches.
- Calling `price_frame_latest_date(prices_wide)` repeatedly in optimizer/universe paths when a dashboard-supplied `PriceEndpointFreshness` exists.
- Treating snapshot reuse as a freshness-policy relaxation.
- Letting a cache key ignore loader shape if future dashboard code changes `top_n` or universe mode.

## Drift Signal

- New Portfolio & Allocation freshness consumers should accept `PriceEndpointFreshness` or build one local snapshot once.
- Dashboard endpoint cache should remain keyed by source signatures, loader arguments, and matrix shape.
- Tests should keep at least one monkeypatch/source guard proving supplied snapshots are reused.

## Evidence Used

- `core/data_orchestrator.py`
- `dashboard.py`
- `views/optimizer_view.py`
- `strategies/portfolio_universe.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_optimizer_view.py`
- `tests/test_portfolio_universe.py`
- actual local performance probe `(2857, 2000)`

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

## High-Risk Attempts

- Treating a wide matrix max date as proof that every selected or weighted asset is fresh.
- Reintroducing private endpoint/tolerance helpers in `strategies.portfolio_universe.py`.
- Forward-filling stale local portfolio legs into current YTD evidence.
- Letting stale overlay cache data make one stale selected asset look covered by another asset's fresh endpoint.
- Letting no-overlap live overlay scaling bridge stale selected local history into a fresh-looking allocation input.
- Reintroducing any no-overlap scaling path or cache mode for live overlays.
- Ranking stale endpoint assets by their own old trailing return as if the return were current.
- Passing optimizer universe eligibility on history count alone.

## Drift Signal

- Every selected/weighted asset must have its own endpoint checked against the required endpoint.
- `portfolio_universe.py` should import endpoint helpers from `core.data_orchestrator`; a source guard rejects local helper clones.
- Benchmark YTD should either live-overlay stale tickers or drop them; it must not present stale unresolved columns as current.
- Portfolio YTD local fallback should be unavailable if any nonzero weighted local leg is stale.
- Selected optimizer live overlay should require same-column local/live overlap; if local ends `2026-02-27` and live starts `2026-05-01`, that selected asset is non-evidence and must be dropped.
- Universe audit should report stale endpoint assets as price-history failures.
- SAW governance for the fail-closed freshness round is PASS after independent Implementer and Reviewer A/B/C rerun; future replay artifact-reader/performance-budget work remains separate.

## Evidence Used

- `core/data_orchestrator.py`
- `dashboard.py`
- `views/optimizer_view.py`
- `strategies/portfolio_universe.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`
- `tests/test_portfolio_universe.py`

## Latest Addendum - Dashboard Backend Bundle Integration Verification

## High-Risk Attempts

- Reopening the stale claim that dashboard replay bypasses `build_selected_method_replay(...)` without checking `_build_dashboard_strategy_replay_context(...)`.
- Treating the transitional build path as a saved artifact-reader path.
- Treating runtime smoke/full pytest as promotion evidence.

## Drift Signal

- `_build_dashboard_strategy_replay_context(...)` must continue to call `build_selected_method_replay(...)`.
- The dashboard backend-bundle call must keep using a per-date PIT `input_loader` with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- Saved artifact-reader consumption remains open until a separate reader/staleness/performance-budget path is implemented and tested.

## Evidence Used

- `dashboard.py`
- `strategies/strategy_replay.py`
- `core/data_orchestrator.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `.venv\Scripts\python -m pytest -q`
- `docs/context/e2e_evidence/backend_bundle_integration_streamlit_8520_status.json`

## Latest Addendum - Replay Coverage Contract Audit Fix

## High-Risk Attempts

- Regressing uncovered-date replay back to one DataFrame/performance attach per date.
- Collapsing specific coverage reasons back to generic `input_unavailable`.
- Crediting weights generated from date `t` data with the return ending at `t`.
- Letting loader-based replay attach performance per date/chunk so `portfolio_equity` resets inside a run.
- Reintroducing duplicate tests that pytest silently shadows.
- Calling SLSQP for inverse-volatility targets that are already bound feasible in high-frequency replay loops.
- Letting the context bootstrap validate while `current_context.*` points at an older same-phase handover instead of the latest current truth packet.

## Drift Signal

- Daily all-uncovered coverage routing should remain below the tested Windows-safe 10s budget without loader or optimizer calls.
- Row-heavy `no_priced_members` coverage routing should remain below the tested Windows-safe 10s budget while preserving explicit per-member rows.
- The 4-asset 5Y monthly replay coverage path should remain below the 5s budget.
- `coverage_segments` must remain present in replay metadata when a coverage plan is supplied.
- Unavailable replay reasons should retain `input_unavailable:<coverage_reason>`.
- A replay date's generated weights should earn only the next tradable return.
- `docs/context/current_context.md` should start from the Replay Coverage Contract Audit Fix packet until a newer complete current-truth packet is published.

## Evidence Used

- `strategies/strategy_replay.py`
- `strategies/optimizer.py`
- `tests/test_strategy_replay_coverage.py`
- `tests/test_optimizer_core_policy.py`
- `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q --durations=12`
- `tests/test_build_context_packet.py`
- `docs/saw_reports/saw_replay_coverage_contract_audit_fix_20260514.md`
- `.venv\Scripts\python -m pytest -q`

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

## High-Risk Attempts

- Claiming full replay-architecture PASS because artifact, backend, dashboard focused suites, and transitional backend-bundle consumption pass while saved artifact-reader/performance-budget work remains open.
- Letting Portfolio Performance display horizons imply looser replay PIT boundaries.
- Letting future dashboard-local `build_strategy_replay(...)` calls bypass backend `build_selected_method_replay(...)` semantics.
- Reading latest Buy/Sell rows as live orders, trade signals, alerts, rankings, recommendations, or candidate scores.

## Drift Signal

- The transitional dashboard backend-bundle path is verified; a saved artifact-reader implementation is not complete until reader staleness policy, full regression/runtime smoke, and performance budget pass.
- For any display horizon, replay input must still be PIT-limited to `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- The Buy/Sell audit table must remain latest-first, collapsed/audit-only, and visibly non-actionable.
- Any failed, stale, partial, or over-budget replay date must emit unavailable/cash-closed state rather than stale carry-forward.

## Evidence Used

- `strategies/strategy_replay.py`
- `dashboard.py`
- `tests/test_strategy_replay.py`
- `tests/test_strategy_replay_artifact.py`
- `tests/test_replay_non_cash_closed.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`
- `tests/test_position_lifecycle.py`
- `tests/test_policy_target_timeline_apptest.py`
- `docs/saw_reports/saw_backend_shared_replay_source_20260513.md`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

## High-Risk Attempts

- Letting YTD, latest allocation, Strategy Replay rows, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence read from different replay artifacts while appearing synchronized.
- Treating current UI/YTD bridges, frozen Rule100 history, or compact buy/sell logs as canonical selected-method replay evidence.
- Carrying forward a prior successful allocation, annotation, or decision row when the current replay date fails or goes stale.
- Claiming performance/risk improvement without same-window, same-cost, same-engine baseline deltas and a saved evidence artifact.
- Turning replay-analysis rows into broker/live trading, alerts, rankings, recommendations, or candidate scores.

## Drift Signal

- A selected method is not implementation-complete until one replay run/source id can be traced into YTD, current allocation/latest snapshot, Strategy Replay, annotations, decision log, and saved evidence.
- Transitional bridges must be labeled non-canonical and must not write final evidence artifacts.
- Failed/stale/over-budget replay dates must emit explicit unavailable/cash-closed status instead of stale-data carry-forward.
- First implementation PASS requires a stated cold-start, rerun/cache, max-row/date, and timeout budget.

## Evidence Used

- `docs/phase_brief/phase65-brief.md`
- `docs/context/done_checklist_current.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/saw_reports/saw_ultra_modular_replay_architecture_note_20260513.md`

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

## High-Risk Attempts

- Mutating `Rule100SoftmaxConfig()` defaults to match current UI policy.
- Regenerating frozen Rule100 history/audit artifacts as if they were live UI-policy artifacts.
- Letting direct Rule100 UI and Strategy Replay use different caps or budgets.
- Forward-filling stale benchmark columns past their own cutoff without a live overlay attempt.

## Drift Signal

- `Rule100SoftmaxConfig()` must remain `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- `rule100_config_from_max_weight(0.35)` must set both `gross_budget_per_name` and `max_single_name_weight` to `0.35`.
- Direct Rule100 UI state and Strategy Replay must agree for the same candidate frame and `controls.max_weight`.
- `build_benchmark_equity_from_prices(...)` must call the live loader only for stale/missing tickers when local benchmark data exists.
- A stale QQQ local column must not be rendered as fresh via blind forward-fill if live overlay returns empty.

## Evidence Used

- `strategies/rule100_softmax.py`
- `strategies/strategy_replay.py`
- `views/optimizer_view.py`
- `core/data_orchestrator.py`
- `dashboard.py`
- `tests/test_rule100_softmax.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/saw_reports/saw_rule100_dynamic_ui_replay_ytd_20260513.md`

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

## High-Risk Attempts

- Letting a public replay cache-signature helper default to full-history `top_liquid` membership.
- Treating caller-provided `cache_dir` as authority to write display-only replay artifacts under canonical data paths.
- Treating price/return input artifacts as target-weight replay output artifacts.
- Passing raw global `prices_wide` directly into dashboard replay output generation.

## Drift Signal

- `build_strategy_replay_cache_signature(...)` must default to and require `r3000_pit`.
- Strategy replay artifacts under repo `data/` must resolve under `data/runtime_cache/strategy_replay`.
- Dashboard Strategy Replay source must include `_load_dashboard_strategy_replay_inputs_cached(...)` and `prices=replay_inputs`, with no `prices=replay_prices`.
- Dashboard Strategy Replay must not contain `if replay_inputs.prices.empty: continue`; missing PIT selected assets must remain visible as `cash_closed`.

## Evidence Used

- `core/data_orchestrator.py`
- `dashboard.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_strategy_replay_artifact.py`
- `tests/test_optimizer_view.py`
- `tests/test_position_lifecycle.py`
- `tests/test_policy_target_timeline_apptest.py`

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

## High-Risk Attempts

- Treating `rule100_softmax_v1_1_history.csv` as current after v1.1 moved to comparison/summary-only artifacts.
- Counting alternate columns as separate Rule100 factor groups.
- Letting copied miniature AppTests stand in for dashboard route coverage.

## Drift Signal

- `data/processed/rule100_softmax_v1_1_history.csv` must be absent after the v1.1 audit run.
- v1.1 comparison `factor_present_count` must not exceed the four approved groups.
- Missing factor strength must shrink toward neutral `0.50`, not fill to `0.0`.
- Policy Target Timeline regression must use `AppTest.from_file("dashboard.py")`.

## Evidence Used

- `strategies/rule100_softmax_v1_1.py`
- `scripts/rule100_softmax_v1_1_audit.py`
- `tests/test_rule100_softmax_v1_1.py`
- `tests/test_policy_target_timeline_apptest.py`
- `data/processed/rule100_softmax_v1_1_summary.json`

## Latest Addendum - Rule of 100 Method Label

## High-Risk Attempts

- Overwriting v0 lifecycle event weights to make historical rows look like softmax v1.
- Treating the compact BUY/SELL log as the v1 target-weight source.
- Hiding the distinction between `Event Weight` and `Softmax v1 Target`.

## Drift Signal

- Position Lifecycle Replay transaction log must include `Softmax v1 Target` and `Softmax v1 Cash` when the overlay artifact exists.
- `data/processed/rule100_softmax_v1_history.csv` must remain additive and derived from the decision tape; it must not replace the lifecycle log.
- Current 2026-05-11 TSM row must show event weight 10%, softmax v1 target 0%, and cash residual 80%.

## Evidence Used

- `scripts/rule100_softmax_v1_audit.py`
- `dashboard.py`
- `tests/test_rule100_softmax.py`
- `tests/test_position_lifecycle.py`
- `data/processed/rule100_softmax_v1_history.csv`

## Previous Addendum - Rule of 100 Method Label

## High-Risk Attempts

- Treating `Rule of 100` as a new optimizer objective or ranked alpha model.
- Letting selected non-held assets get optimized when `Rule of 100` is selected.
- Treating empty or all-ineligible softmax state as a reason to reuse stale lifecycle `last_weight`.

## Drift Signal

- `Rule of 100` must bypass `_run_optimizer_cached(...)` and render softmax v1 target weights for eligible lifecycle holds plus residual cash, or cash-only when no holds are eligible.
- `portfolio_allocation_state.source` must be `rule100_softmax_v1` after selecting the explicit Rule of 100 method.
- `OptimizationMethod.RULE_OF_100.is_mean_variance` must remain false.

## Evidence Used

- `strategies/optimizer.py`
- `views/optimizer_view.py`
- `tests/test_optimizer_view.py`
- `tests/test_portfolio_universe.py`
- `tests/test_rule100_softmax.py`
- `docs/context/e2e_evidence/rule100_method_label_8509_smoke.json`

## Latest Addendum - Rule100 Lifecycle Policy v0

## High-Risk Attempts

- Treating audit-only TRIM/TIGHTEN rows as portfolio weight changes.
- Treating proxy Rule100 fields as literal demand/supply/pricing/margin columns.
- Expanding the concrete v0 policy into a generic replay framework before a second strategy exists.
- Reading the 29-event v0 replay as production/live promotion.

## Drift Signal

- V0 is valid only if runtime ENTER/EXIT remains dashboard-compatible and decision-tape BUY/SELL still matches replay events.
- Any future change that lets TRIM/TIGHTEN change weights must produce a new delta against this v0 baseline.

## Evidence Used

- `scripts/pit_lifecycle_replay.py`
- `tests/test_pinned_universe.py`
- `data/portfolio_lifecycle_log.jsonl`
- `data/portfolio_lifecycle_decision_log.jsonl`
- `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

## Latest Addendum - Lifecycle Decision Export

## High-Risk Attempts

- Treating replay-analysis `BUY` / `SELL` fields as broker orders, alerts, recommendations, or dashboard action labels.
- Letting the decision export diverge from `run_pit_replay(...)` event semantics.
- Treating proxy-mapped supply/pricing/margin fields as literal Rule-of-100 columns.

## Drift Signal

- The export is audit-only and must match emitted lifecycle ENTER/EXIT rows for BUY/SELL decisions.
- Any future optimal lifecycle policy should first explain the current audit flags: factor-deterioration holds, suppressed raw exits, and delayed entries.

## Evidence Used

- `scripts/pit_lifecycle_replay.py`
- `tests/test_pinned_universe.py`
- `data/portfolio_lifecycle_decision_log.jsonl`
- `data/portfolio_lifecycle_buy_sell_log.jsonl`
- `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

## High-Risk Attempts

- Treating the old 4% replay weight as a portfolio intent instead of a stale `1 / replay_universe` artifact.
- Letting one-day raw gate flips create ENTER/EXIT churn without confirmation or cooldown state.
- Reopening the rejected Phase 54 Rule-of-100 sleeve under the label of a lifecycle fix.
- Treating current scanner labels as sell-all portfolio state while lifecycle replay still has open holds.
- Compounding daily return rows as if they were price levels in Portfolio YTD.

## Drift Signal

- This round changes replay state discipline only: current holds, lifecycle event cadence, and replay weights.
- It does not approve ranking, scoring, optimizer objectives, provider ingestion, canonical market-data writes, alerts, broker behavior, or live trading.

## Evidence Used

- `scripts/pit_lifecycle_replay.py`
- `tests/test_pinned_universe.py`
- `data/portfolio_lifecycle_log.jsonl`
- `docs/context/e2e_evidence/portfolio_lifecycle_log_pre_dropin_20260512.jsonl`
- `docs/context/e2e_evidence/dropin_lifecycle_replay_tmp.jsonl`
- `docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl`
- `docs/context/e2e_evidence/lifecycle_churn_weight_8509_smoke.json`
- `docs/context/e2e_evidence/portfolio_ytd_return_fix_8509_smoke.json`

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

## High-Risk Attempts

- Treating today's scanner EXIT/KILL label as a current sell-all event when lifecycle replay still has open ENTER positions.
- Letting stale JSON position memory override lifecycle replay sell-all state.
- Allowing future-dated replay rows to leak into today's current portfolio.
- Re-optimizing current holds as fresh entries when the correct state is hold plus residual cash.

## Drift Signal

- The current portfolio is sell-all only when lifecycle replay has no open positions as of the current PIT-safe timestamp.
- This bug fix is position-state reconciliation only; it is not an execution ledger, broker workflow, alert, ranking, scoring, conviction mode, or optimizer-objective change.

## Evidence Used

- `data/portfolio_lifecycle_log.py`
- `strategies/portfolio_universe.py`
- `views/optimizer_view.py`
- `dashboard.py`
- `tests/test_position_lifecycle.py`
- `tests/test_portfolio_universe.py`
- `tests/test_optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

## High-Risk Attempts

- Treating `st.cache_resource` as safe for future mutating consumers without defensive copies or switching to `st.cache_data`.
- Letting source-text cache tests replace full regression and runtime smoke evidence.
- Treating the cache signature as provider freshness or canonical ingestion.
- Expanding this performance slice into alpha-engine loop rewrites or scanner financial-statement caching.

## Drift Signal

- This round is dashboard runtime performance hardening only. The product behavior, data authority, scanner semantics, optimizer policy, ranking/scoring, alerts, and broker scope are unchanged.
- Full pytest and SAW now pass after stale quick-slice evidence was reconciled.

## Evidence Used

- `dashboard.py`
- `core/data_orchestrator.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_dashboard_sprint_a.py`
- `docs/saw_reports/saw_dashboard_unified_data_cache_performance_20260511.md`

## Latest Addendum - Dashboard Scanner Testability Hardening

## High-Risk Attempts

- Changing scanner rating semantics while presenting the work as pure testability extraction.
- Moving yfinance/provider calls into strategy code.
- Letting scanner formula tests replace full dashboard/runtime smoke for phase closure.
- Re-coupling entry, tactic, proxy, rating, and leverage rules into inline dashboard closures.
- Letting non-finite macro or breadth inputs coerce to optimistic scores or labels.

## Drift Signal

- This round is testability and regression hardening only. Dashboard scanner labels should remain behavior-preserving, provider authority is unchanged, and no action/ranking/scoring policy is approved.
- Reviewer-driven non-finite macro/breadth regressions now fail closed through `tests/test_scanner.py`.
- SAW Reviewer C rerun verified latest raw `VWEHX`/`VFISX` fail-closed behavior after the final macro-denominator fix.

## Evidence Used

- `strategies/scanner.py`
- `dashboard.py`
- `tests/test_scanner.py`
- `tests/test_strategy.py`
- `tests/test_phase15_integration.py`
- `tests/test_adaptive_trend.py`
- `tests/test_production_config.py`
- `tests/test_core_etl.py`
- `tests/test_process_utils.py`

## Latest Addendum - Dashboard Architecture Safety Slice

## High-Risk Attempts

- Reintroducing local `os.kill(pid, 0)` probes in Windows-reachable runtime paths.
- Terminating PID-file owners without a stronger ownership guarantee than a stale PID file.
- Treating dashboard helper cleanup as authorization for broader dashboard redesign.
- Letting `clean_price_frame` duplicate again between dashboard and data orchestration.

## Drift Signal

- This round is architecture safety/hygiene only. Product behavior, provider authority, optimizer policy, ranking/scoring, alerts, and broker scope are unchanged.

## Evidence Used

- `utils/process.py`
- `dashboard.py`
- `tests/test_process_utils.py`
- `tests/test_parameter_sweep.py`
- `tests/test_updater_parallel.py`
- `tests/test_release_controller.py`
- `tests/test_optimize_phase16_parameters.py`

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

## High-Risk Attempts

- Treating the display-only Parquet overlay cache as canonical market-data ingestion.
- Assuming sector caps are SLSQP constraints instead of post-solver soft constraints.
- Letting optimizer-run caching hide changed user parameters or stale price-frame inputs.
- Reintroducing source-text-only tests for a Streamlit view that needs real widget-tree coverage.

## Drift Signal

- The round is tests/performance hardening only: same optimizer objective set, same product semantics, faster/nonblocking display refresh path, and stronger route/view regression coverage.
- SAW rerun passed independently; Low runtime follow-ups are executor-submit exception containment and optional background-refresh diagnostics, not product-policy blockers.

## Evidence Used

- `core/data_orchestrator.py`
- `views/optimizer_view.py`
- `tests/test_optimizer_view.py`
- `tests/test_optimizer_core_policy.py`
- `tests/test_dash_2_portfolio_ytd.py`

## Latest Addendum - Portfolio Data Boundary Refactor

## High-Risk Attempts

- Treating data-orchestrator ownership of the display overlay as canonical provider ingestion.
- Reintroducing direct yfinance imports into `views/optimizer_view.py`.
- Letting backtest-result metrics parsing in the UI become an unguarded disk-access pattern.
- Using row-level duplicate-date replacement for sparse live overlay rows instead of cell-wise merge.
- Treating stale display overlay cache as fresh canonical market data.

## Drift Signal

- The round is architecture hygiene only: same Portfolio & Allocation behavior, cleaner boundary, no new data authority.

## Evidence Used

- `core/data_orchestrator.py`
- `views/optimizer_view.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_provider_ports.py`

## Latest SAW Recheck Addendum - Portfolio Data Boundary Refactor

- Implementer recheck: PASS.
- Reviewer A recheck: PASS; partial-live overlay and stale session-state findings resolved.
- Reviewer B recheck: PASS; scheduler submit failure now fails soft.
- Reviewer C recheck: PASS; duplicate anchor dates and stale-while-revalidate semantics are locked.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

## High-Risk Attempts

- Treating structured diagnostics as approval for lower-bound allocation policy.
- Treating labeled equal-weight fallback as an optimized result.
- Letting UI active-bound explanations become MU conviction, WATCH investability, Black-Litterman, simple tilt, scanner, or manual override scope.

## Drift Signal

- The implementation is `OPTIMIZER_DIAGNOSTICS_ONLY`; it explains optimizer state and failure modes but does not add a new objective or allocation policy.

## Evidence Used

- `strategies/optimizer_diagnostics.py`
- `strategies/optimizer.py`
- `views/optimizer_view.py`
- `tests/test_optimizer_core_policy.py`

## Latest Addendum - Optimizer Core Policy Audit

## High-Risk Attempts

- Treating strict xfail audit tests as implementation acceptance.
- Reusing the quarantined patch without adding structured diagnostics and passing non-xfail implementation tests.
- Letting optimizer policy audit become conviction or Black-Litterman scope.

## Drift Signal

- The audit outcome is `reject_as_is_and_hold_implementation`, not merge.

## Evidence Used

- `docs/architecture/optimizer_core_policy_audit.md`
- `docs/architecture/optimizer_constraints_policy.md`
- `docs/architecture/optimizer_lower_bound_slsqp_policy.md`
- `tests/test_optimizer_core_policy.py`

## Latest Addendum - Portfolio Universe Quarantine Closure

## High-Risk Attempts

- Treating quarantined `strategies/optimizer.py` lower-bound/SLSQP math as accepted because the universe patch passed.
- Letting optimizer-core fallback, infeasibility, or active-bound explanation drift into UI copy without policy tests.
- Reopening MU conviction, WATCH investability, or Black-Litterman under the optimizer-core audit name.

## Drift Signal

- The next action is `open_optimizer_core_policy_audit_or_hold`, not implementation of lower bounds or conviction math.

## Evidence Used

- `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`
- `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md`
- `docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md`
- `strategies/optimizer.py` has no active diff.

## Latest Addendum - Portfolio Universe Construction Fix

## High-Risk Attempts

- Reintroducing `df_scan["Ticker"][:20]` or any display-order slice as optimizer input.
- Treating generic `WATCH` as investable without a separate product policy.
- Adding an MU hard floor, expected-return tilt, conviction slider, Black-Litterman mode, or thesis anchor sizing before governance exists.
- Adding manual override without audit metadata and expiry.
- Treating max-weight as a harmless UI setting when it can force equal weight.

## Drift Signal

- The next action is `approve_thesis_anchor_policy_or_hold`, not conviction math or MU sizing.

## Evidence Used

- `strategies/portfolio_universe.py`
- `views/optimizer_view.py`
- `dashboard.py`
- `tests/test_portfolio_universe.py`
- `docs/architecture/portfolio_construction_contract.md`

## Header

- `PACK_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-obs`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `OWNER`: `PM / Architecture Office`

## High-Risk Attempts

- Treating `LOCAL_FACTOR_SCOUT` as factor-model validation.
- Treating MSFT's card as a rank, score, buy/sell/hold, buying range, or recommendation.
- Creating cards for DELL/AMD/LRCX/ALB before G8.3 approval.
- Adding more scout output.
- Merging the MSFT card into the existing dashboard ticker list or old action labels.
- Treating official/public evidence pointers as thesis validation.
- Adding alert, broker, provider, or buy/sell/hold wording.

## Drift Signal

- The immediate next action is `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`, not ranking, scoring, provider ingestion, alerts, broker work, or dashboard action integration.

## Skill Activation / Under-Triggering

- `se-executor`: used because G8.2 is a multi-file data/docs/test change with governance and handoff risk.
- `saw`: required for closeout reporting and reviewer pass.
- `browser-use`: attempted because the user referenced a running local dashboard in Chrome, but browser-control tool access was not exposed in this turn; code/runtime inspection was used instead.

## Recommendations

- Close G8.2 after SAW.
- If dashboard integration is approved later, implement a status-only card reader rather than mixing with legacy action-shaped labels.
- Next choose G9, G8.3, dashboard card reader, or hold.

## Evidence Used

- `dashboard.py` legacy MSFT strings and action labels.
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
