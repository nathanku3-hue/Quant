# Impact Packet - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, strategy search, provider ingestion, alerts, broker calls, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, or scope widening by itself.
Purpose: provide a compact view of the Portfolio Optimizer View Test and Performance Hardening implementation and affected interfaces.

## Latest Addendum - Portfolio Replay Role Contract

### Changed Runtime Files

```text
strategies/strategy_replay.py
dashboard.py
```

### Changed Test Files

```text
tests/test_strategy_replay.py
tests/test_strategy_replay_artifact.py
tests/test_dash_2_portfolio_ytd.py
tests/test_dash_1_page_registry_shell.py
tests/test_policy_target_timeline_apptest.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `REPLAY_COLUMNS`: now carries `row_role` and `context_role`.
- `REPLAY_CONTEXT_COLUMNS`: now carries `row_role` and `context_role`.
- `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS`: now carries `row_role` and `context_role`, with legacy hydration for older saved artifacts.
- `normalize_context_frame_for_replay(...)`: public shared context-normalization contract for dashboard adapters.
- `_normalize_dashboard_context_frame(...)`: delegates to strategy replay instead of private duplicate logic.
- `_build_replay_context_diagnostics(...)`: computes closure diagnostics from `DashboardReplayContext`.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\strategy_replay.py dashboard.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- Targeted role/compat/diagnostic hardening regressions -> PASS, 3 passed after SAW Reviewer C suggestions.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 169 passed.

### Open Risks

- Backend dashboard_cache_signature/saved-artifact policy remains a separate follow-up.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Optimizer History Diagnostics Split

### Changed Runtime Files

```text
views/optimizer_view.py
```

### Changed Test Files

```text
tests/test_portfolio_universe.py
tests/test_optimizer_view.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `strategies.portfolio_universe.optimizer_universe_health_summary(...)`: reused by UI to split missing history from stale endpoints.
- `views.optimizer_view._render_universe_audit(...)`: visible metrics now show `Missing History` and `Stale Endpoint`.
- `views.optimizer_view._render_allocation_explanation(...)`: explanation rows use split price-readiness labels.

### Passing Checks

- `.venv\Scripts\python -m py_compile views\optimizer_view.py strategies\portfolio_universe.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` -> PASS, 62 passed.

### Open Risks

- Stale local price columns are only diagnosed here; data repair remains a separate follow-up.
- Pre-2025 Rule100 candidate/decision artifacts remain absent and still cause `candidate_coverage_not_started` before coverage begins.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

### Changed Runtime Files

```text
dashboard.py
strategies/strategy_replay.py
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_strategy_replay.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `strategies.strategy_replay.REPLAY_CONTEXT_COLUMNS`: now carries `target_weight` for aux context rows.
- `strategies.strategy_replay._normalize_context_frame(...)`: derives aux `target_weight` from matching replay rows and preserves legacy aux `weight`.
- `dashboard._align_context_weights_to_replay(...)`: stores original aux `weight` as `audit_weight` and sets visible `weight` to replay `target_weight`.
- `dashboard._dashboard_context_from_artifact_read(...)` and `_dashboard_context_from_backend_bundle(...)`: align saved/transitional event and decision rows before render/cache.
- `dashboard._render_replay_timeline_chart(...)`: renders stacked step-area replay target weights.
- `dashboard._render_strategy_replay_section(...)`: fails soft for partial latest snapshot or event schemas.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py strategies\strategy_replay.py tests\test_dash_2_portfolio_ytd.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py` -> PASS.
- Targeted aux/timeline/fail-soft regressions -> PASS, including executable Plotly trace assertions for stacked `hv` allocation areas.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q` -> PASS, 80 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 134 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 66 passed.

### Open Risks

- Broad inherited dirty/untracked files remain present and were not reverted.
- Durable saved-artifact horizon-aware superset/subset matching remains future policy work.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

### Changed Runtime Files

```text
dashboard.py (horizon-aware replay asset union plus current-only allocation asset split and context-only replay rows)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `_build_dashboard_replay_request(...)`: builds `DashboardReplayRequest.replay_assets` from the current signed selection plus mapped in-window event/decision/history tickers, while `allocation_assets` remains the current signed selection.
- `_current_full_replay_signature(...)`: uses the same horizon-aware asset union so in-session cache reuse compares against the widened replay source identity.
- `_filter_dashboard_replay_inputs_to_assets(...)`: filters PIT inputs to allocation assets only so history-only context names cannot become optimizer assets.
- `_dashboard_filter_coverage_plan_to_assets(...)`: filters unavailable coverage rows to allocation assets before backend replay construction.
- `_append_context_only_replay_rows(...)`: appends zero-weight rows for historical context tickers after backend bundle construction.
- `_strategy_replay_cache_signature(...)`: binds both widened `replay_assets` and current-only `allocation_assets`.
- `PortfolioReplaySelection`: remains the current allocation handoff and is not mutated by horizon history expansion.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- Targeted MU/context/coverage/cache regressions -> PASS, 4 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 61 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay.py tests\test_strategy_replay_coverage.py -q` -> PASS, 71 passed.

### Open Risks

- Durable saved artifacts still require exact dashboard cache signatures; horizon-aware saved-artifact superset/subset matching remains a future backend/dashboard policy.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

### Changed Runtime Files

```text
core/data_orchestrator.py   (selected_permnos support in batched PIT loader after full membership proof)
dashboard.py                (passes signed numeric replay assets into batched PIT price loading)
scripts/pit_lifecycle_replay.py (MU/SNDK thesis eligibility trace diagnostic)
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_optimizer_view.py
tests/test_pinned_universe.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json
```

### Touched Interfaces

- `load_batched_pit_replay_data(..., selected_permnos=...)`: still builds full replay-window membership index, then narrows price/return parquet reads to selected PIT members.
- `_load_dashboard_batched_pit_replay_data_cached(...)`: includes selected permnos in the Streamlit cached loader call.
- `_build_dashboard_strategy_replay_context(...)`: passes `_numeric_replay_permnos(request.replay_assets)` into the batched loader.
- `trace_thesis_ticker_eligibility(...)`: diagnostic-only gate trace for pinned thesis tickers; local price/return evidence rejects non-finite returns.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py scripts\pit_lifecycle_replay.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_pinned_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py::test_batched_pit_loader_keeps_full_membership_proof_while_loading_selected_prices tests\test_optimizer_view.py::test_dashboard_batched_pit_loader_passes_selected_permnos_without_watchlist_shortcut tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_answers_mu_sndk_gates tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_reports_pit_membership_gate -q` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_pinned_universe.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py::test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight -q` -> PASS, 112 passed.

### Open Risks

- MU/SNDK may still require a separate Strategy/Data investigation into Rule100 history/candidate-frame inclusion; this round only traces the gate truth.
- Malformed optional diagnostic input files remain a non-blocking resilience follow-up.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

### Changed Runtime Files

```text
dashboard.py (in-session daily replay superset validation, horizon-scoped reused contexts, exact-cache row-coverage guard)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `_ensure_daily_portfolio_replay_context(...)`: checks `_valid_cached_ytd_replay_context(...)` before the spinner/build path when a horizon is supplied.
- `_valid_cached_ytd_replay_context(...)`: accepts in-session daily replay superset reuse only when non-date signature identity matches and requested dates are present in actual replay rows.
- `_scope_dashboard_replay_context_to_dates(...)`: returns a selected-horizon view of a reused daily replay context.
- Saved artifact selector remains exact `dashboard_cache_signature` only.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- Targeted superset-cache regressions -> PASS, 3 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 56 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay_coverage.py -q` -> PASS, 50 passed.

### Open Risks

- Durable saved artifacts still require exact dashboard cache signatures; serving shorter windows from saved supersets remains a future backend/dashboard policy.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Max Replay Timeline Sampling Fix

### Changed Runtime Files

```text
dashboard.py (weekly display sampler normalizes grouped date Series with .dt.normalize)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `_sample_replay_timeline_from_daily(...)`: max-window weekly grouping now converts the grouped `Series` through `pd.to_datetime(...).dropna().dt.normalize()`.
- Strategy Replay Timeline remains a display-only sample from daily replay rows.
- Portfolio Performance still requires daily replay rows and does not consume sampled timeline rows.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_is_display_only_from_daily_replay -q` -> PASS, 2 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 53 passed.

### Open Risks

- Backend artifact producer still owns final dashboard_cache_signature emission for saved-artifact UI hits.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Portfolio Replay Selection Identity Hardening

### Changed Runtime Files

```text
dashboard.py             (validates signed replay selection; fail-closed selection-unavailable path; builder-error cache clear)
views/optimizer_view.py  (PortfolioReplaySelection state/signature publisher; removes optimizer_universe writer)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `PortfolioReplaySelection`: explicit replay-universe handoff with method, cap, risk-free rate, assets, latest price date, source, and signature.
- `build_portfolio_replay_selection_signature(...)`: binds typed replay assets to current control values, price-frame identity, and selected price content hash.
- `_build_dashboard_replay_request(...)`: consumes signed selection and returns `portfolio_replay_selection_unavailable` when missing/stale.
- `_render_portfolio_builder_section(...)`: clears signed selection and replay/YTD caches on optimizer builder errors or skipped data.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py` -> PASS.
- Focused replay-selection/advisory regressions -> PASS, 6 passed.
- Focused optimizer-selection AppTests -> PASS, 6 passed.

### Open Risks

- Backend artifact producer still owns final dashboard_cache_signature emission for aux event/decision rows.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Portfolio Single-Source Replay Page

### Changed Runtime Files

```text
dashboard.py          (page-level daily replay coordinator; replay allocation snapshot; performance daily-only gate; timeline display sampling; UI dedup)
views/optimizer_view.py (controls-only mode for Portfolio page)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
tests/test_policy_target_timeline_apptest.py
tests/test_position_lifecycle.py
```

### Changed Governance Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/context/*
```

### Touched Interfaces

- `DashboardReplayContext`: carries `run_id`, `source_id`, `method_id`, and `date_window`.
- `_render_portfolio_allocation_page(...)`: builds one daily context and passes it to allocation snapshot, Portfolio Performance, and Strategy Replay.
- `_render_portfolio_ytd_chart(...)`: requires daily replay context and no longer uses optimizer/local/live/equal-weight fallback for replay-facing performance.
- `_sample_replay_timeline_from_daily(...)`: derives weekly display sampling from daily rows using `(ISO year, ISO week)`.
- `_render_strategy_replay_section(...)`: consumes the passed context, removes duplicate Trade Event Log table, filters latest buys/sells from bundle decision rows, and applies selected horizon to ENTER/EXIT Events.
- `render_optimizer_view(..., show_allocation_outputs=False)`: lets Portfolio render controls without a separate optimizer allocation panel.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q` -> PASS, 178 passed.
- Streamlit readiness smoke `http://127.0.0.1:8526/portfolio-and-allocation` -> PASS, HTTP 200.
- `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

### Open Risks

- SAW reviewer gate remains pending for formal implementation closure.
- Backend production artifacts still need `dashboard_cache_signature` emission for saved-artifact UI hits.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

### Changed Runtime Files

```text
dashboard.py (saved-artifact adapter preserves artifact event/decision rows exactly, including empty frames)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/context/*
docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md
```

### Touched Interfaces

- `_dashboard_context_from_artifact_read(...)`: no longer falls back from empty saved artifact event/decision rows to separately loaded dashboard frames.
- `DashboardReplayContext.source_mode="saved_artifact"`: preserves artifact ownership for replay rows, latest snapshot, event rows, and decision rows, even when aux rows are empty.
- `tests/test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows`: covers daily saved rows plus empty saved aux rows while fallback frames are non-empty.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact tests\test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows tests\test_dash_2_portfolio_ytd.py::test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback -q` -> PASS, 3 passed.
- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 106 passed.

### Open Risks

- Existing backend artifacts without `dashboard_cache_signature` remain unavailable for saved-artifact UI hits and fall back to labeled transitional build when allowed.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Backend Replay Reader Identity Hardening

### Changed Runtime Files

```text
strategies/strategy_replay.py (manifest non-empty identity validation for saved selected-method replay reader)
```

### Changed Test Files

```text
tests/test_strategy_replay_artifact.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md
```

### Touched Interfaces

- `_validate_manifest_bundle_fields(...)`: rejects blank/non-string top-level manifest `run_id`, `source_id`, and `method_id`.
- `read_selected_method_replay_artifact(...)`: continues to run manifest bundle validation before optional expected-ID matching, parquet read, budget check, or bundle reconstruction.
- `tests/test_strategy_replay_artifact.py`: covers matching blank manifest+parquet identity when caller does not supply expected `run_id` / `source_id`.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\strategy_replay.py scripts\build_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py::test_read_selected_method_replay_artifact_rejects_blank_manifest_identity_without_expected_ids -q` -> PASS, 3 passed.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12` -> PASS, 79 passed.

### Open Risks

- Backend artifacts still need `dashboard_cache_signature` emission for production saved-artifact UI hits.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Frontend/UI Saved Replay Source Selector

### Changed Runtime Files

```text
dashboard.py (pure replay request, saved-artifact selector, DashboardReplayContext adapters, source labels)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
tests/test_position_lifecycle.py
tests/test_policy_target_timeline_apptest.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `DashboardReplayRequest`: pure dashboard request for method, cap, controls, assets, dates, sampling, and data signature.
- `_read_dashboard_saved_replay_artifact(...)`: calls backend `read_selected_method_replay_artifact(...)` and requires matching `dashboard_cache_signature`.
- `_dashboard_context_from_artifact_read(...)`: adapts saved artifact bundles to `DashboardReplayContext`.
- `_dashboard_context_from_backend_bundle(...)`: adapts transitional backend builds to `DashboardReplayContext`.
- `_build_dashboard_strategy_replay_context(...)`: source selector preferring saved artifact and falling back to labeled transitional build only when allowed.
- `_render_strategy_replay_section()`: labels saved artifact vs transitional build vs unavailable and continues to consume one context for rows, snapshot, events, and decisions.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact tests\test_dash_2_portfolio_ytd.py::test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback tests\test_optimizer_view.py::test_dashboard_replay_request_constructor_is_pure tests\test_optimizer_view.py::test_dashboard_strategy_replay_calls_build_strategy_replay -q` -> PASS, 4 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 105 passed.

### Open Risks

- Existing backend artifacts without `dashboard_cache_signature` remain unavailable for saved-artifact UI hits and fall back to labeled transitional build when allowed.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Saved Replay Artifact Reader + Budget

### Changed Runtime Files

```text
strategies/strategy_replay.py        (selected-method artifact reader, typed result, budget wrapper)
scripts/build_strategy_replay_artifact.py (selected-output CLI budget flags and wrapper use)
```

### Changed Test Files

```text
tests/test_strategy_replay_artifact.py
tests/test_strategy_replay_coverage.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
```

### Touched Interfaces

- `ReplayBudgetPolicy`: explicit cold-start, rerun/cache, row, date, and elapsed-ms budget contract.
- `SelectedMethodReplayResult`: typed available/unavailable result for saved reads and budget-wrapped builds.
- `read_selected_method_replay_artifact(...)`: validates saved parquet+manifest as one bundle and reconstructs `StrategyReplayBundle` only when fresh.
- `build_selected_method_replay_with_budget(...)`: preserves existing build semantics but returns unavailable on budget/build failure.
- `write_selected_method_replay_artifact_atomic(...)`: manifest now duplicates input signatures, controls signature, and timing at top level for reader validation.
- `_metadata_json_safe(pd.DataFrame)`: includes deterministic content hash for DataFrame controls such as Rule100 candidate frames.
- `_validate_artifact_against_manifest(...)`: requires exact non-null parquet identity fields for artifact scope, run id, source id, method id, and row type.
- `scripts/build_strategy_replay_artifact.py`: selected-method-output path uses budget wrapper and exposes row/date/elapsed limits.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\strategy_replay.py scripts\build_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12` -> PASS, 76 passed.

### Open Risks

- Frontend/dashboard saved-reader consumption is intentionally not wired in this backend slice.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Overlay Overlap Anchor Fix

### Changed Runtime Files

```text
core/data_orchestrator.py (scaled overlay anchor invariant for selected prices and benchmarks)
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dash_2_portfolio_ytd.py
```

### Touched Interfaces

- `scale_live_overlay_to_local(...)`: requires same-column local/live overlap and drops unanchored live columns.
- `refresh_selected_prices_with_live_overlay(...)`: selected-price overlays use the strict scaler and fail through freshness filtering.
- `merge_benchmark_live_overlay(...)`: benchmark overlays require same-ticker local/live overlap.
- `build_benchmark_equity_from_prices(...)`: drops stale benchmark tickers when live data is available but unanchored.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q` -> PASS, 112 passed after SAW rerun reconciliation.
- SAW Implementer and Reviewer A/B/C -> PASS.

### Open Risks

- Adjacent replay/YTD session-state advisory is out of scope and carried as future hygiene.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

### Changed Runtime Files

```text
core/data_orchestrator.py        (PriceEndpointFreshness snapshot; chunked endpoint builder; snapshot-aware helper APIs)
dashboard.py                     (cached endpoint snapshot keyed by unified load signature and matrix shape; snapshot passed downstream)
views/optimizer_view.py          (snapshot-aware default ordering and selected-price prep)
strategies/portfolio_universe.py (snapshot-aware universe endpoint checks)
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_optimizer_view.py
tests/test_portfolio_universe.py
```

### Touched Interfaces

- `PriceEndpointFreshness`: reusable endpoint snapshot with `latest_by_column`, `required_latest`, `latest_for(...)`, and `required_latest_for(...)`.
- `build_price_endpoint_freshness(...)`: chunked one-pass endpoint snapshot builder.
- `price_column_latest_date(...)`, `price_frame_latest_date(...)`, `filter_price_frame_to_fresh_columns(...)`: accept optional freshness snapshots.
- `dashboard._price_endpoint_freshness_cached(...)`: Streamlit cache for the loaded `prices_wide` endpoint snapshot.
- `DashboardReplayContext.cache_signature`, `STRATEGY_REPLAY_CACHE_SIGNATURE_KEY`: signature-bound replay/YTD session cache.
- `dashboard._valid_cached_ytd_replay_context(...)`: rejects stale full replay contexts before Portfolio Performance can render them.
- `dashboard._weighted_equity_curve(...)`: fails closed when any positive-weight column is missing from a price frame.
- `render_optimizer_view(...)`, `_prepare_selected_prices(...)`, `_order_assets_by_trailing_one_year_return(...)`: accept/reuse snapshot.
- `build_optimizer_universe(...)`: accepts/reuses snapshot.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py views\optimizer_view.py strategies\portfolio_universe.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q` -> PASS, 113 passed.
- Actual local performance probe `(2857, 2000)`: snapshot `0.2966s`, legacy loop `0.9555s`, endpoint maps matched, 50 downstream lookups `0.001531s`.

### Open Risks

- Reviewer A targeted recheck passed; Reviewer B second targeted recheck is pending after full-context signature fix.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

### Changed Runtime Files

```text
core/data_orchestrator.py       (per-column endpoint helpers; benchmark/overlay freshness filtering)
dashboard.py                    (portfolio YTD required-endpoint fail-closed behavior)
views/optimizer_view.py         (selected-price endpoint gate; stale default-order demotion)
strategies/portfolio_universe.py (shared endpoint freshness eligibility gate)
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
tests/test_portfolio_universe.py
```

### Touched Interfaces

- `price_latest_dates_by_column(...)`, `price_column_latest_date(...)`, `price_frame_latest_date(...)`, `price_endpoint_is_fresh(...)`, `filter_price_frame_to_fresh_columns(...)`: shared per-asset endpoint freshness helpers and tolerance predicate.
- `scale_live_overlay_to_local(...)`: scaled overlays require same-column local/live overlap and drop unanchored live columns before selected-price or benchmark evidence can use them.
- `build_benchmark_equity_from_prices(...)`: drops stale unresolved benchmark columns and reports common benchmark endpoint.
- `_weighted_equity_curve(...)`: fails closed when a nonzero weighted local leg is stale at required endpoint.
- `refresh_selected_prices_with_live_overlay(...)`: accepts `required_latest` and drops unresolved stale selected assets.
- `_order_assets_by_trailing_one_year_return(...)`: demotes stale endpoint assets before trailing-return ranking.
- `build_optimizer_universe(...)`: excludes stale endpoint assets even with enough history observations by importing shared core endpoint helpers and passing policy tolerance explicitly.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py strategies\portfolio_universe.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_portfolio_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py::test_price_endpoint_helpers_default_to_strict_freshness tests\test_data_orchestrator_portfolio_runtime.py::test_price_endpoint_freshness_snapshot_reuses_per_column_endpoints tests\test_portfolio_universe.py::test_stale_price_endpoint_is_reported_even_with_enough_history tests\test_portfolio_universe.py::test_endpoint_freshness_uses_universe_policy_tolerance tests\test_portfolio_universe.py::test_portfolio_universe_uses_shared_endpoint_freshness_contract -q` -> PASS, 5 passed.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py --disable-warnings` -> PASS, 112 passed after SAW rerun reconciliation.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py -q` -> PASS, 171 passed.

### Open Risks

- Independent SAW rerun completed: Implementer and Reviewer A/B/C all returned PASS with no in-scope Critical/High findings.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

### Changed Governance Files

```text
docs/phase_brief/phase65-brief.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/planner_packet_current.md
docs/context/done_checklist_current.md
docs/context/impact_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_dashboard_backend_bundle_integration_verification_20260514.md
```

### Runtime Files Verified

```text
dashboard.py
strategies/strategy_replay.py
core/data_orchestrator.py
```

### Touched Interfaces

- `_build_dashboard_strategy_replay_context(...)`: imports and calls backend `build_selected_method_replay(...)`.
- `_dashboard_input_loader(...)`: supplies per-date PIT replay inputs through `load_strategy_replay_inputs(..., end_date=as_of_date, universe_mode="r3000_pit")`.
- `DashboardReplayContext`: carries replay rows, latest snapshot, event annotations, Buy/Sell decisions, and YTD latest-weight preference from the backend bundle.
- `/portfolio-and-allocation`: boots under Streamlit and returns HTTP 200 on a fresh runtime smoke.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py strategies\strategy_replay.py core\data_orchestrator.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_replay_non_cash_closed.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Streamlit readiness smoke `http://127.0.0.1:8520/portfolio-and-allocation` -> PASS, HTTP 200.

### Open Risks

- Saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Replay Coverage Contract Audit Fix

### Changed Runtime Files

```text
strategies/strategy_replay.py   (batch uncovered rows; fast unavailable rows; next-return performance; small-frame return lookup)
strategies/optimizer.py         (bound-feasible inverse-volatility fast path)
scripts/build_context_packet.py (current truth surfaces are selectable context packet sources)
```

### Changed Test Files

```text
tests/test_strategy_replay_coverage.py   (duplicate cleanup; canonical perf/coverage tests)
tests/test_optimizer_core_policy.py      (inverse-volatility fast-path regression)
tests/test_build_context_packet.py       (current truth selection and drift validation regressions)
```

### Touched Interfaces

- `_build_replay_from_input_loader(...)`: uncovered coverage-plan dates batch `input_unavailable:*` cash-closed rows before performance attachment and preserve row-heavy explicit-member unavailable windows.
- `_attach_replay_performance(...)`: allocation-date rows earn next tradable returns; tiny PIT frames use direct return lookup; larger frames keep long-form vectorized merge.
- `PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics(...)`: returns deterministic inverse-vol target when already bound feasible.
- `build_context_packet(...)`: current truth surfaces with a complete New Context Packet outrank older handovers during bootstrap selection and validation.
- `tests/test_strategy_replay_coverage.py`: one canonical coverage segment test, one CASH-only daily-scale performance test, and one row-heavy no-priced-members daily-scale performance test remain.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q` -> PASS, 11 passed.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay_coverage.py -q --durations=12` -> PASS; row-heavy no-priced-members daily-scale 1.21s, 4-asset 5Y 1.20s, CASH-only daily-scale 0.30s.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py tests\test_strategy_replay_coverage.py tests\test_optimizer_core_policy.py -q` -> PASS, 68 passed.
- `.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_phase61_context_hygiene.py -q` -> PASS, 24 passed.
- `.venv\Scripts\python -m py_compile strategies\strategy_replay.py strategies\optimizer.py tests\test_strategy_replay_coverage.py tests\test_optimizer_core_policy.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_execution_microstructure.py::test_shutdown_execution_microstructure_spoolers_fails_closed_when_sink_error_present -q` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Formal SAW Implementer and Reviewer A/B/C rechecks -> PASS.

### Open Risks

- Dashboard backend-bundle end-to-end consumption and runtime smoke are now verified in the dashboard integration verification addendum above.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

### Changed Governance Files

```text
docs/phase_brief/phase65-brief.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/planner_packet_current.md
docs/context/done_checklist_current.md
docs/context/impact_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_backend_shared_replay_source_20260513.md
```

### Runtime/Test Evidence Referenced

```text
strategies/strategy_replay.py
dashboard.py
tests/test_strategy_replay.py
tests/test_strategy_replay_artifact.py
tests/test_replay_non_cash_closed.py
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
tests/test_position_lifecycle.py
tests/test_policy_target_timeline_apptest.py
```

### Touched Interfaces

- `build_selected_method_replay(...)`: backend bundle API for selected-method replay output and context.
- `write_selected_method_replay_artifact_atomic(...)`: durable selected-method replay-output artifact writer with run id, manifest metadata, path confinement, and rollback-safe parquet+manifest promotion.
- `DashboardReplayContext`: dashboard selected-method replay context for replay rows, latest snapshot, annotations, and buy/sell audit rows.
- `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY`: latest selected-method replay weights preferred by Portfolio Performance before legacy optimizer fallback.
- `Portfolio Performance timeframe controls`: display horizons only; replay evidence still uses PIT slices by as-of date.
- `Buy/Sell Decision Log`: latest-first audit table; not live orders or trade signals.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\strategy_replay.py dashboard.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_replay_non_cash_closed.py -q` -> PASS, 21 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 89 passed.

### Open Risks

- Dashboard backend-bundle consumption, full repository pytest, and runtime smoke are now verified in the dashboard integration verification addendum above.
- Saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.

## Latest Addendum - Frontend/UI Shared Replay Bundle

### Changed Runtime Files

```text
dashboard.py   (DashboardReplayContext; Strategy Replay annotations/audit/latest snapshot/YTD use selected-method context)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_policy_target_timeline_apptest.py
tests/test_position_lifecycle.py
tests/test_optimizer_view.py
```

### Touched Interfaces

- `DashboardReplayContext`: selected-method UI replay bundle for replay rows, latest snapshot, event annotations, and Buy/Sell audit rows.
- `STRATEGY_REPLAY_LATEST_WEIGHTS_KEY`: latest selected-method replay weights preferred by Portfolio YTD before legacy optimizer fallback.
- `_render_strategy_replay_section()`: consumes context fields instead of direct lifecycle/compact JSONL reads.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py -q` -> PASS, 89 passed.

### Open Risks

- Full backend replay-output artifact/run-id integration remains required for the complete ultra-modular replay architecture.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

### Changed Governance Files

```text
docs/phase_brief/phase65-brief.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/planner_packet_current.md
docs/context/done_checklist_current.md
docs/context/impact_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_ultra_modular_replay_architecture_note_20260513.md
```

### Changed Runtime Files

```text
None. Worker 3 scope is docs-only.
```

### Touched Interfaces

- `Selected-method replay source`: planned single source that must feed YTD, latest allocation snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence.
- `Transitional bridges`: current UI/YTD/replay bridges are explicitly non-canonical until the shared replay source is implemented.
- `Performance guardrail`: first implementation slice must define cold-start replay, rerun/cache, max rows/dates, and fail-closed timeout budget before PASS.

### Acceptance Checks Captured

- Non-negotiable one-source invariant is documented.
- Architecture goal is distinguished from temporary transitional bridges.
- Guardrails cover PIT, stale carry-forward, fake improvements, overfitting, broker/live trading, alerts/rankings/recommendations, and autonomous allocation.
- Done checklist has machine-checkable items for shared replay source, adapters, shared YTD/performance, annotation source, decision-log source, saved evidence, and performance budget.
- SAW-style report exists with PASS/BLOCK criteria.

### Open Risks

- Implementation is partial by design; shared replay source, selected-method adapters, shared output consumers, saved evidence artifact, and performance budget enforcement still need code/tests in a separate slice.
- Concurrent runtime edits may exist outside this Docs/Ops lane and were not reverted or modified.

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

### Changed Runtime Files

```text
core/data_orchestrator.py   (per-ticker benchmark equity curves keep stale local QQQ visible without future flat fill)
strategies/optimizer.py     (Rule of 100 default method)
views/optimizer_view.py     (default selection ordered by trailing 1-year return)
dashboard.py                (Buy/Sell Decision Log renders before heavy replay loop)
```

### Changed Test Files

```text
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
tests/test_portfolio_universe.py
tests/test_policy_target_timeline_apptest.py
tests/test_position_lifecycle.py
```

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py -q` -> PASS.
- `.venv\Scripts\python -m py_compile core\data_orchestrator.py strategies\optimizer.py views\optimizer_view.py dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Browser DOM on `http://localhost:8509/` -> PASS for visible Rule of 100, SPY, QQQ, and Buy/Sell Decision Log.

### Open Risks

- Full YTD forward-walk replay cold-start cost remains an architecture/performance target.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

### Changed Governance Files

```text
docs/phase_brief/phase65-brief.md
docs/notes.md
docs/decision log.md
docs/context/bridge_contract_current.md
docs/context/planner_packet_current.md
docs/context/done_checklist_current.md
docs/context/impact_packet_current.md
```

### Changed Runtime Files

```text
None. This is a docs-only architecture planning note.
```

### Touched Interfaces

- `Current patch boundary`: QQQ/YTD/default-method/Rule100 visible fixes remain separate from the larger architecture milestone.
- `Ultra-modular replay target`: one replay engine, one strategy plug-in contract, one daily portfolio output format, one event/annotation format, one YTD/performance path, and one saved evidence artifact.
- `AI auto-research loop boundary`: endless research evidence loop only; no unchecked optimizer, broker/live trading, alerting, ranking, scoring, recommendation, or autonomous capital allocation.

### Acceptance Checks Captured

- Rule100 visible sizing parity remains an acceptance test before architecture work starts.
- QQQ/YTD stale-overlay behavior remains an acceptance test before architecture work starts.
- Planner/bridge next step points to the modular replay milestone after QQQ/default-method visible fixes.

### Open Risks

- The architecture milestone is not implemented yet; first implementation slice still needs explicit approval and code/tests.
- Concurrent runtime edits may exist outside this docs-only ownership lane and were not reverted or modified.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

### Changed Runtime Files

```text
strategies/rule100_softmax.py     (dynamic UI/replay config helper)
strategies/strategy_replay.py     (Rule100 replay uses dynamic max-weight config)
views/optimizer_view.py           (direct Rule100 UI passes controls.max_weight)
core/data_orchestrator.py         (per-ticker benchmark stale overlay helper)
dashboard.py                      (benchmark builder delegation, bounded YTD fallback, deterministic AppTest replay cap)
```

### Changed Test Files

```text
tests/test_rule100_softmax.py
tests/test_strategy_replay.py
tests/test_optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
tests/test_policy_target_timeline_apptest.py
```

### Touched Interfaces

- `rule100_config_from_max_weight(max_weight)`: dynamic visible Rule100 UI/replay sizing config.
- `softmax_v1_weights(...)`: unchanged audit default behavior when no config is provided.
- `views.optimizer_view._rule100_softmax_weights_for_ui(...)`: now accepts `max_weight`.
- `strategies.strategy_replay._build_rule100_weights_for_date(...)`: uses the same dynamic config as the direct UI path.
- `build_benchmark_equity_from_prices(...)`: builds benchmark curves from local data plus stale-only live overlay.
- `dashboard.py::_build_benchmark_equity(...)`: delegates to data orchestration and labels blended sources `local+live_overlay`.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py strategies\rule100_softmax.py strategies\strategy_replay.py views\optimizer_view.py dashboard.py tests\test_rule100_softmax.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 89 passed.
- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_rule100_softmax_v1_1.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 151 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Streamlit readiness on `http://127.0.0.1:8514/portfolio-and-allocation` -> PASS, HTTP 200.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

### Open Risks

- Frozen Rule100 history still shows historical 10% audit-target semantics by design; if a 35% historical UI-policy trace is needed, create a separate versioned/labeled artifact.
- Production live benchmark overlay remains display-only and provider-dependent; canonical QQQ backfill remains a separate data-ingestion decision.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

### Changed Runtime Files

```text
core/data_orchestrator.py        (r3000_pit signature guard, runtime-cache path guard)
dashboard.py                     (per-date StrategyReplayInputs dashboard replay wiring)
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_strategy_replay_artifact.py
tests/test_optimizer_view.py
tests/test_position_lifecycle.py
tests/test_policy_target_timeline_apptest.py
```

### Touched Interfaces

- `build_strategy_replay_cache_signature(...)`: default and required `universe_mode` is `r3000_pit`.
- `write_strategy_replay_artifact_atomic(...)`: repo-local artifacts are confined to `data/runtime_cache/strategy_replay`.
- `dashboard.py::_render_strategy_replay_section(...)`: consumes per-date `StrategyReplayInputs` and passes them into `build_strategy_replay(...)`.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py strategies\strategy_replay.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 93 passed.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_portfolio_universe.py tests\test_pinned_universe.py -q` -> PASS, 179 passed.

### Open Risks

- Full repository pytest and runtime browser smoke are still pending for phase-close proof.
- Replay input artifacts remain input slices; target-weight output persistence is a separate future approval.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

### Changed Runtime / Audit Files

```text
strategies/rule100_softmax_v1_1.py       (group-count factor helpers + neutral missing-factor shrinkage)
scripts/rule100_softmax_v1_1_audit.py    (retires stale v1.1 history artifact; writes comparison/summary only)
data/processed/rule100_softmax_v1_1_comparison.csv (refreshed; factor counts are approved-group counts)
data/processed/rule100_softmax_v1_1_summary.json    (records retired history artifact)
data/processed/rule100_softmax_v1_1_history.retired.csv (retired stale artifact)
```

### Changed Test Files

```text
tests/test_rule100_softmax_v1_1.py        (group count, neutral shrinkage, stale-history retirement)
tests/test_policy_target_timeline_apptest.py (real dashboard AppTest.from_file regression)
```

### Touched Interfaces

- `compute_factor_group_values(...)`: one numeric signal per approved v1.1 factor group.
- `compute_factor_group_counts(...)`: group-based present/positive counts.
- `compute_factor_strength_continuous(...)`: coverage-weighted shrinkage toward neutral `0.50`.
- `run_v1_1_audit(...)`: active artifacts are comparison CSV and summary JSON only; stale history is retired.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\rule100_softmax_v1_1.py scripts\rule100_softmax_v1_1_audit.py tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `.venv\Scripts\python scripts\rule100_softmax_v1_1_audit.py --as-of-date 2026-05-12` -> PASS; no active v1.1 history CSV remains.
- `.venv\Scripts\python -m pytest tests\test_rule100_softmax_v1_1.py tests\test_policy_target_timeline_apptest.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_1_page_registry_shell.py -q` -> PASS, 61 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- HTTP readiness on `http://127.0.0.1:8509` -> PASS, HTTP 200.

### Open Risks

- v1.1 remains research-only and still lacks multi-date return/risk/turnover promotion evidence.
- Independent SAW subagent review closed PASS for this contract-fix round.

## Latest Addendum - Rule of 100 Method Label

### Changed Runtime / Data Files

```text
scripts/rule100_softmax_v1_audit.py       (adds PIT historical softmax v1 target-weight overlay writer)
dashboard.py                              (merges v1 history overlay into Position Lifecycle Replay transaction log)
data/processed/rule100_softmax_v1_history.csv (derived v1 historical target-weight artifact)
```

### Changed Test Files

```text
tests/test_rule100_softmax.py             (history overlay and current TSM drop-to-cash regressions)
tests/test_position_lifecycle.py          (renderer source guard for Event Weight vs Softmax v1 Target columns)
```

### Touched Interfaces

- `build_rule100_softmax_v1_history(...)`: builds PIT date/ticker target-weight overlay from the decision tape.
- `write_rule100_softmax_v1_history(...)`: atomically writes `data/processed/rule100_softmax_v1_history.csv`.
- `dashboard.py::_merge_rule100_softmax_v1_history(...)`: read-only UI overlay; does not mutate lifecycle events.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py scripts\rule100_softmax_v1_audit.py tests\test_rule100_softmax.py tests\test_position_lifecycle.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_position_lifecycle.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_pinned_universe.py -q` -> PASS.
- `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12` -> PASS and writes history CSV.

### Open Risks

- Historical BUY rows remain 10% under v1 because all historical BUY confirmations are equal 3/4 score; richer continuous inputs are required for visible >10% concentration.
- Independent SAW subagent review is pending unless explicitly authorized.

## Previous Addendum - Rule of 100 Method Label

### Changed Runtime Files

```text
strategies/optimizer.py                    (adds OptimizationMethod.RULE_OF_100 label and registry option)
views/optimizer_view.py                    (routes Rule of 100 to lifecycle holdings plus residual cash)
```

### Changed Test Files

```text
tests/test_optimizer_view.py               (AppTest coverage for Rule of 100 lifecycle routing)
tests/test_portfolio_universe.py           (method registry label and non-mean-variance assertions)
```

### Changed Governance / Evidence Files

```text
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/phase_brief/phase65-brief.md
docs/notes.md
docs/decision log.md
docs/context/*
```

### Touched Interfaces

- `OptimizationMethod.RULE_OF_100`: user-facing dropdown label `Rule of 100`.
- `render_optimizer_view(...)`: method branch bypasses `_run_optimizer_cached(...)` and renders lifecycle holds/cash.

### Passing Checks

- `.venv\Scripts\python -m py_compile strategies\optimizer.py views\optimizer_view.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_portfolio_universe.py -q` -> PASS, 25 passed.
- Browser smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; dropdown options include `Rule of 100` after restart.

### Open Risks

- Independent SAW subagent review is pending unless explicitly authorized.

## Latest Addendum - Rule100 Softmax v1 Audit

### Changed Runtime Files

```text
strategies/rule100_softmax.py             (pure softmax v1 sizing helpers + thin Kelly comparator)
scripts/rule100_softmax_v1_audit.py       (shared PIT audit harness and artifact writer)
views/optimizer_view.py                   (Rule of 100 UI uses softmax v1 targets instead of lifecycle last_weight)
data/processed/rule100_softmax_v1_*       (summary, comparison, sample, cash outputs)
```

### Changed Test Files

```text
tests/test_rule100_softmax.py             (softmax score, cap, Kelly comparator, audit harness coverage)
tests/test_optimizer_view.py              (Rule of 100 softmax source, TSM drop-to-cash, no stale last_weight fallback)
```

### Touched Interfaces

- `softmax_v1_weights(...)`: primary Rule100 sizing helper.
- `kelly_ablation_weights(...)`: comparator-only Kelly shim on the same frame.
- `run_rule100_softmax_v1_audit(...)`: shared PIT replay/audit harness and artifact writer.
- `render_optimizer_view(...)`: explicit Rule of 100 branch stores `source=rule100_softmax_v1` and writes softmax target weights to allocation state/YTD.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py -q` -> PASS, 11 passed.
- `.venv\Scripts\python scripts\rule100_softmax_v1_audit.py --as-of-date 2026-05-12` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_rule100_softmax.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke on `http://127.0.0.1:8509/` -> PASS; selecting Rule of 100 shows `Rule of 100 softmax v1 sizing output` and no lifecycle replay copy.

### Open Risks

- Kelly comparator stays intentionally thin and may leave more cash than the softmax primary path.
- Current ordinal score ties AMAT and LRCX at 10% each; richer continuous score inputs are needed if visible >10% concentration is desired.

## Latest Addendum - Rule100 Lifecycle Policy v0

### Changed Runtime / Data Files

```text
scripts/pit_lifecycle_replay.py            (Rule100State adapter, v0 lifecycle actions, conviction entry sizing)
data/portfolio_lifecycle_log.jsonl         (promoted v0 runtime replay; 29 events)
data/portfolio_lifecycle_decision_log.jsonl (v0 decision tape; BUY/HOLD/TRIM/TIGHTEN/EXIT/NO_ACTION)
data/portfolio_lifecycle_buy_sell_log.jsonl (v0 compact BUY/SELL tape; 29 rows)
```

### Changed Test Files

```text
tests/test_pinned_universe.py              (Rule100 provenance, conviction sizing, exit guard, export/replay equivalence)
```

### Changed Governance / Evidence Files

```text
docs/context/e2e_evidence/portfolio_lifecycle_log_pre_rule100_v0_20260512.jsonl
docs/context/e2e_evidence/lifecycle_decision_audit_pre_rule100_v0_20260512.json
docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl
docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json
docs/saw_reports/saw_rule100_lifecycle_policy_v0_20260512.md
```

### Touched Interfaces

- `Rule100State`: explicit PIT proxy adapter for demand/supply/pricing/margin with provenance.
- `rule100_target_weight(...)`: conviction entry sizing, capped at 15%.
- `should_emit_exit(...)`: full exits only on hard stop `dist_sma20 > 0.20` or confirmed trend veto.
- Decision export: adds audit-only `TRIM` and `TIGHTEN` lifecycle actions plus suggested weight deltas.

### Passing Checks

- `.venv\Scripts\python -m py_compile scripts\pit_lifecycle_replay.py tests\test_pinned_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_pinned_universe.py -q` -> PASS, 36 passed.
- `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 61 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Runtime HTTP smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS, HTTP 200 after Streamlit restart.
- V0 export -> PASS; runtime events=29, BUY=16, SELL=13, TRIM=55, TIGHTEN=257, open `AMAT`, `LRCX`, `TSM`.

### Open Risks

- `TRIM` and `TIGHTEN` are audit-only in v0; they do not yet reduce actual allocation weights.
- Literal Rule-of-100 columns remain absent; proxy provenance is explicit.
- Independent SAW subagent review is pending if this promotion is treated as milestone closure.

## Latest Addendum - Lifecycle Decision Export

### Changed Runtime / Data Files

```text
scripts/pit_lifecycle_replay.py            (export-only decision tape, buy/sell tape, audit summary)
data/portfolio_lifecycle_decision_log.jsonl (5424 PIT ticker-date decision rows)
data/portfolio_lifecycle_buy_sell_log.jsonl (33 replay BUY/SELL rows with reasons)
```

### Changed Test Files

```text
tests/test_pinned_universe.py              (decision export writes reasons; export buy/sell matches event replay)
```

### Changed Governance / Evidence Files

```text
docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/saw_reports/saw_lifecycle_decision_export_20260512.md
```

### Touched Interfaces

- `export_lifecycle_decision_log(...)`: exports PIT-safe daily `BUY`/`SELL`/`HOLD`/`NO_ACTION` analysis rows without mutating lifecycle events.
- CLI: `scripts/pit_lifecycle_replay.py --export-only --decision-log-path ... --buy-sell-log-path ... --audit-summary-path ...`.
- `build_lifecycle_decision_audit(...)`: summarizes actions, reasons, current open holds, round trips, and audit flags.

### Passing Checks

- `.venv\Scripts\python -m py_compile scripts\pit_lifecycle_replay.py tests\test_pinned_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_pinned_universe.py -q` -> PASS, 34 passed.
- Export run -> PASS; 5424 decision rows, 33 BUY/SELL rows, open `AMAT`, `LRCX`, `TSM`.

### Open Risks

- The export is an audit tape, not a fill/quantity/cost execution ledger.
- Supply/pricing/margin remain explicit proxy mappings until literal Rule-of-100 feature columns exist.
- Independent SAW subagent review is pending if this export round is treated as milestone closure.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

### Changed Runtime / Data Files

```text
scripts/pit_lifecycle_replay.py            (10% sizing, 3-of-4 factor confirmation, entry/exit state guards)
core/data_orchestrator.py                  (correct prices/returns assignment from dashboard loader)
dashboard.py                               (local TRI history first for portfolio and benchmark YTD)
data/portfolio_lifecycle_log.jsonl         (33-event final replay; open AMAT/LRCX/TSM at 10%)
```

### Changed Test Files

```text
tests/test_pinned_universe.py              (drop-in sizing, factor confirmation, exit guard, cooldown coverage)
tests/test_data_orchestrator_portfolio_runtime.py (price/return slot regression coverage)
tests/test_dash_2_portfolio_ytd.py         (local-first YTD/benchmark fallback source guards)
```

### Changed Governance / Evidence Files

```text
docs/notes.md
docs/decision log.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/phase_brief/phase65-brief.md
docs/context/e2e_evidence/portfolio_lifecycle_log_pre_dropin_20260512.jsonl
docs/context/e2e_evidence/dropin_lifecycle_replay_tmp.jsonl
docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl
```

### Touched Interfaces

- `replay_entry_weight()`: default ENTER weight is `0.10`.
- `lifecycle_factor_confirmation(...)`: confirms at least 3 present and positive vectors among `z_demand`, `z_moat`, `z_inventory_quality_proxy`, and `z_discipline_cond`.
- `run_pit_replay(...)`: tracks `entry_streak`, `exit_streak`, and `cooldown_until` before emitting lifecycle events.
- CLI: `scripts/pit_lifecycle_replay.py --log-path ...` now runs from repo root and accepts replay date/path arguments.
- `UnifiedDataPackage.prices`: now holds price/TRI levels rather than daily returns.
- `Portfolio YTD`: uses local TRI history first and preserves residual cash in weighted returns.

### Passing Checks

- `.venv\Scripts\python -m py_compile scripts\pit_lifecycle_replay.py tests\test_pinned_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_pinned_universe.py -q` -> PASS, 32 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_pinned_universe.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py -q` -> PASS, 91 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Final lifecycle replay verification -> 33 events, ENTER=18, EXIT=15, all ENTER weights=0.10, open `AMAT`, `LRCX`, `TSM`, no `<=5` day holds.
- Browser smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; visible holds include `AMAT`, `LRCX`, `TSM`, `CASH`; no `100.0% Cash`; YTD chart traces include `Portfolio`, `SPY`, and `QQQ` with local benchmark fallback.
- Portfolio YTD return fix smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; Portfolio metric `+14.25%`, chart starts in January, SPY/QQQ traces present, no `7645112.18%`.

### Open Risks

- Final replay is still a reconstruction log, not a full fill/quantity/cost execution ledger.
- The 3-of-4 PIT vector filter uses currently available feature-store columns; literal Rule-of-100 margin/supply/pricing columns are not in `features.parquet`.
- Independent SAW subagent review is pending if this round is treated as milestone closure under the repo governance contract.

## Latest Addendum - Pinned Strategy Universe Hardening

### Changed Runtime Files

```text
data/universe/pinned_thesis_universe.yml   (manifest: 10 thesis tickers)
data/universe/loader.py                    (fail-closed loader with strict validation)
data/universe/__init__.py
data/feature_store.py                      (unions pinned permnos, aborts on failure unless override)
scripts/pit_lifecycle_replay.py            (defaults to scanner∪pinned, shared eligibility gate)
```

### Changed Test Files

```text
tests/test_pinned_universe.py              (27 tests: loader, gates, union, fail-closed, diagnostics, edge cases)
```

### Changed Data Files

```text
data/processed/yahoo_patch.parquet         (backfilled MU/AMD/AVGO/TSM/INTC/LRCX/SNDK/WDC/AMAT)
data/processed/prices_tri.parquet          (rebuilt through 2026-05-11)
data/processed/macro_features.parquet      (rebuilt through 2026-05-11)
data/processed/macro_features_tri.parquet  (rebuilt through 2026-05-11)
data/processed/features.parquet            (203 permnos = 200 yearly_union + pinned)
data/portfolio_lifecycle_log.jsonl          (103 events, 12 tickers)
```

### Touched Interfaces

- `run_build()` signature: added `allow_missing_pinned_universe: bool = False`
- `load_pinned_manifest()`: raises FileNotFoundError/ValueError (was silent return [])
- `_default_replay_tickers()`: raises on loader failure (was silent fallback to [])
- `is_pit_eligible()` / `is_pit_exit()`: new shared gate functions

### Pinned Universe Formula

```
feature_universe = yearly_top_n(200) ∪ pinned_thesis_universe.yml
replay_tickers   = SCANNER_TICKERS ∪ pinned_thesis_universe.yml
eligibility      = z_demand > 0 AND capital_cycle_score > 0 AND dist_sma20 ≤ 0.05 AND NOT trend_veto
exit_trigger     = dist_sma20 > 0.12 OR trend_veto (on held position)
```

### Failing Checks

None. 102 tests pass (27 pinned + 34 feature_store + 14 lifecycle + 7 dash-1 + 20 dash-2).

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

### Changed Runtime Files

```text
data/portfolio_lifecycle_log.py
strategies/portfolio_universe.py
views/optimizer_view.py
dashboard.py
```

### Changed Test Files

```text
tests/test_position_lifecycle.py
tests/test_portfolio_universe.py
tests/test_optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/phase_brief/phase65-brief.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Lifecycle replay state`: `data.portfolio_lifecycle_log.get_open_lifecycle_positions(...)` reconstructs latest ENTER/EXIT open holdings as of a PIT-safe cutoff.
- `Current position memory`: `strategies.portfolio_universe.load_current_position_memory(...)` prefers lifecycle replay state over stale JSON memory when replay evidence exists.
- `Optimizer universe`: open lifecycle holdings are included as `included_current_hold`, even when today's scanner row is EXIT/KILL.
- `Portfolio allocation UI`: no-fresh-PIT-ENTER with open lifecycle holds renders current holds plus residual cash, not 100% cash.
- `Portfolio performance`: session, ticker-mapped, and aligned weights preserve residual cash unless total weights exceed 100%.
- `Lifecycle data integrity`: JSONL appends use lock + temp + replace, and malformed rows fail closed instead of being skipped.

### Passing Checks

- `.venv\Scripts\python -m py_compile data\portfolio_lifecycle_log.py strategies\portfolio_universe.py views\optimizer_view.py dashboard.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 58 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; Universe Audit shows included lifecycle holds and the residual-cash message renders.
- Local lifecycle state check -> open holdings are `AMAT`, `AVGO`, and `TSLA`, not sell-all.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "<lifecycle ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_portfolio_lifecycle_current_holds_20260512.md` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` -> PASS.

### Failing / Incomplete Checks

- None in current focused verification.

### Open Risks

- Existing lifecycle replay weights are simple replay weights and not a full execution ledger with fills, quantities, realized P&L, or slippage.
- Hard-crash stale lifecycle `.lock` recovery is a future Ops hardening follow-up; current behavior fails closed by timeout.
- Broader dirty worktree contains inherited dashboard/navigation and governance edits outside this focused fix.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

### Changed Runtime Files

```text
dashboard.py
core/data_orchestrator.py
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dashboard_sprint_a.py
```

### Changed Governance / Evidence Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_status.txt
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_stdout.txt
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_stderr.txt
```

### Touched Interfaces

- `Dashboard unified data load`: `dashboard.py` calls `_load_unified_data_cached(...)` instead of loading the institutional parquet package directly on every Streamlit rerun.
- `Unified data cache invalidation`: `core.data_orchestrator.build_unified_data_cache_signature(...)` fingerprints relevant processed/static parquet source files by resolved path, mtime_ns, and size.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py core\data_orchestrator.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q` -> PASS, 22 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Streamlit HTTP smoke at `http://127.0.0.1:8507` -> PASS, HTTP 200.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Independent SAW Implementer and Reviewer A/B/C passes -> PASS after reconciling stale full-pytest evidence.
- SAW closure packet validation and report block validation -> PASS.

### Failing / Incomplete Checks

- None in current focused/full verification.

### Open Risks

- Cached package is returned as a mutable resource; current dashboard consumers treat the package as read-mostly, but future in-place mutation should switch this path to `st.cache_data` or copy before mutation.
- Alpha-engine daily-loop optimization and scanner raw-financials cache remain separate follow-ups.

## Latest Addendum - Dashboard Scanner Testability Hardening

### Changed Runtime Files

```text
strategies/scanner.py
dashboard.py
```

### Changed Test Files

```text
tests/conftest.py
tests/test_scanner.py
tests/test_strategy.py
tests/test_adaptive_trend.py
tests/test_production_config.py
tests/test_core_etl.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Dashboard scanner`: `dashboard.py` still owns yfinance fetch/cache/payload persistence; deterministic enrichment delegates to `strategies.scanner.enrich_scan_frame`.
- `Scanner formulas`: macro score, breadth status, technicals, entry/support math, tactics, proxy signal, rating, and leverage are importable pure helpers.
- `Scanner data quality`: non-finite macro and breadth inputs fail closed to `None` / `UNKNOWN` instead of optimistic labels.
- `Test fixtures`: `tests/conftest.py` now exposes common synthetic price, return, macro, and ticker-map fixtures.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_scanner.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\test_process_utils.py -q` -> PASS, 49 passed.
- `.venv\Scripts\python -m py_compile strategies\scanner.py dashboard.py tests\test_scanner.py tests\test_strategy.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\conftest.py` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS after non-finite scanner reconciliation.
- `.venv\Scripts\python -m pytest --collect-only -q` -> PASS; collection includes scanner, adaptive-trend, production-config, core-ETL, and process-guardrail tests.
- SAW Reviewer C final recheck -> PASS; latest raw `VWEHX`/`VFISX` fail-closed behavior verified.

### Failing / Incomplete Checks

- None for this addendum.

### Open Risks

- `dashboard.py` remains large; this round extracted scanner math only and did not redesign the dashboard runtime.

## Latest Addendum - Dashboard Architecture Safety Slice

### Changed Runtime Files

```text
utils/process.py
dashboard.py
data/updater.py
scripts/parameter_sweep.py
scripts/release_controller.py
backtests/optimize_phase16_parameters.py
```

### Changed Test Files

```text
tests/test_process_utils.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/spec.md
docs/prd.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_dashboard_architecture_safety_20260511.md
```

### Touched Interfaces

- `Process liveness`: shared `utils.process.pid_is_running` replaces local direct PID-probe logic while preserving local wrapper names.
- `Backtest single-flight`: `dashboard.py::spawn_backtest` refuses to spawn another job when the PID file points to a live process.
- `Dashboard strategy matrix`: `_build_strategy_matrix` and `_ensure_modular_strategy_state` own one initialization path.
- `Dashboard price cleanup`: `_clean_portfolio_price_frame` delegates to `core.data_orchestrator.clean_price_frame`.

### Passing Checks

- `.venv\Scripts\python -m py_compile utils\process.py dashboard.py data\updater.py scripts\parameter_sweep.py scripts\release_controller.py backtests\optimize_phase16_parameters.py tests\test_process_utils.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q` -> PASS, 103 passed.
- `rg -n "os\.kill\(pid,\s*0\)|os\.kill\(int\(pid\),\s*0\)" -g "*.py"` -> no unsafe runtime caller outside shared utility comment.
- `Invoke-WebRequest http://127.0.0.1:8501` after launch smoke -> PASS, HTTP 200.

### Failing / Incomplete Checks

- `.venv\Scripts\python -m pytest -q` -> timed out after 304 seconds.
- `.venv\Scripts\python launch.py` -> long-running app boot timed out after 184 seconds; HTTP readiness was checked successfully and the spawned process tree was stopped.

### Open Risks

- Full regression needs a longer explicit window if phase closure is requested.
- `dashboard.py` remains large and still has broader module-split debt outside this safety slice.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

### Changed Runtime Files

```text
core/data_orchestrator.py
views/optimizer_view.py
.gitignore
tests/test_optimizer_view.py
tests/test_optimizer_core_policy.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Portfolio Optimizer UI`: render body uses helper path, Streamlit AppTest coverage exists, optimizer runs are cached by selected price frame and parameters.
- `Portfolio Data Orchestration`: display-only recent-close overlays use Parquet cache, background refresh scheduling, atomic cache writes, and copy-safe overlay scaling cache.
- `Optimizer Core Policy Tests`: UI-derived max-weight/risk-free-rate values flow through the real SLSQP path; sector caps remain post-solver soft constraints.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 39 passed.
- `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py strategies\optimizer.py dashboard.py tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_provider_ports.py -q` -> PASS, 46 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Streamlit smoke at `http://127.0.0.1:8506/portfolio-and-allocation` -> PASS, HTTP 200.
- SAW independent Implementer and Reviewer A/B/C rerun -> PASS.
- SAW report block validation and closure packet validation -> PASS.

### Open Risks

- DASH YTD benchmark refresh still has dashboard-level direct yfinance legacy debt.
- Low runtime hygiene follow-ups remain open for future work: executor submit exception containment and optional background-refresh diagnostics.
- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Portfolio Data Boundary Refactor

### Changed Runtime Files

```text
core/data_orchestrator.py
views/optimizer_view.py
data/providers/legacy_allowlist.py
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dashboard_sprint_a.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
```

### Touched Interfaces

- `Portfolio Data Orchestration`: owns selected-stock display-refresh close extraction, duplicate-safe local TRI scaling/stitching, stale-while-revalidate display cache, scheduler fail-soft handling, and strategy metrics parsing.
- `Portfolio Optimizer UI`: consumes orchestrator helpers, no longer owns direct yfinance or direct backtest-results JSON parsing, and clears stale optimizer session weights on no-result paths.
- `Provider-Port Guard`: `views/optimizer_view.py` is removed from direct-yfinance allowlist expectations.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py dashboard.py data\providers\legacy_allowlist.py tests\test_dash_2_portfolio_ytd.py tests\test_dashboard_sprint_a.py tests\test_data_orchestrator_portfolio_runtime.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q` -> PASS, 8 passed.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py tests\test_dash_2_portfolio_ytd.py tests\test_provider_ports.py tests\test_portfolio_universe.py -q` -> PASS, 47 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS, 17 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py` and `--validate` -> PASS.
- Runtime smoke at `http://localhost:8505/portfolio-and-allocation` -> PASS, HTTP 200.
- SAW Implementer and Reviewer A/B/C rechecks -> PASS.

### Open Risks

- DASH YTD benchmark refresh still has dashboard-level direct yfinance legacy debt.
- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

### Changed Runtime Files

```text
strategies/optimizer_diagnostics.py
strategies/optimizer.py
views/optimizer_view.py
tests/test_optimizer_core_policy.py
```

### Changed Governance Files

```text
docs/architecture/optimizer_core_policy_audit.md
docs/architecture/optimizer_constraints_policy.md
docs/architecture/optimizer_lower_bound_slsqp_policy.md
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
```

### Touched Interfaces

- `Optimizer Diagnostics`: new structured report objects for feasibility, solver, bound, constraint, severity, and fallback status.
- `Portfolio Optimizer Core`: existing objectives preserved; diagnostic-returning methods expose status without adding lower-bound policy or conviction math.
- `Portfolio & Allocation UI`: renders optimization status, feasibility status, active constraints, assets at max/lower bounds, equal-weight forced status, and fallback labels.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m py_compile strategies\optimizer.py strategies\optimizer_diagnostics.py views\optimizer_view.py dashboard.py` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke at `http://localhost:8505/portfolio-and-allocation` -> PASS.
- SAW report validation, closure packet validation, and evidence validation -> PASS.

### Open Risks

- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Optimizer Core Policy Audit

### Changed Governance Files

```text
docs/architecture/optimizer_core_policy_audit.md
docs/architecture/optimizer_constraints_policy.md
docs/architecture/optimizer_lower_bound_slsqp_policy.md
docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md
tests/test_optimizer_core_policy.py
```

### Touched Interfaces

- `Optimizer Core Policy`: lower-bound/SLSQP behavior is documented as held, not implemented.
- `Optimizer Tests`: tests lock non-approval and mark known future implementation debt with strict `xfail` cases.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS with expected strict xfails for known policy debt.

### Open Risks

- Current optimizer still lacks structured infeasibility/fallback diagnostics; this is audit debt and not fixed in this docs/tests-first round.

## Latest Addendum - Portfolio Universe Quarantine Closure

### Changed Governance Files

```text
docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch
docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md
docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md
data/providers/legacy_allowlist.py
```

### Touched Interfaces

- `Portfolio Optimizer Core`: no active diff remains in `strategies/optimizer.py`; lower-bound/SLSQP math is quarantined for separate audit only.
- `Universe Closure`: SAW now closes PASS with 9/9 focused checks after quarantine.

### Passing Checks

- `git diff -- strategies/optimizer.py` -> empty.
- `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py -q` -> PASS, 33 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python -m py_compile strategies\portfolio_universe.py views\optimizer_view.py dashboard.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Browser smoke at `http://127.0.0.1:8503/portfolio-and-allocation` -> Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render.

### Open Risks

- Optimizer lower-bound/SLSQP policy remains undecided until `OPTIMIZER_CORE_POLICY_AUDIT`.

## Latest Addendum - Portfolio Universe Construction Fix

### Changed Runtime Files

```text
dashboard.py
views/optimizer_view.py
strategies/portfolio_universe.py
tests/test_portfolio_universe.py
tests/test_dash_2_portfolio_ytd.py
docs/architecture/portfolio_construction_contract.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/prd.md
docs/spec.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
```

### Touched Interfaces

- `Portfolio Optimizer`: receives audited candidate permnos instead of display-sorted scan tickers.
- `Universe Audit`: reports included/excluded rows, missing ticker mappings, and local price-history failures.
- `Allocation Explanation`: reports thesis-neutral status and max-weight feasibility diagnostics.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 26 passed.
- `.venv\Scripts\python -m py_compile strategies\portfolio_universe.py views\optimizer_view.py dashboard.py` -> PASS.
- Browser smoke at `http://127.0.0.1:8503/portfolio-and-allocation` -> Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render.

### Open Risks

- Current cached scan has no optimizer-eligible rows under the conservative policy; this is a fail-closed outcome, not a conviction optimizer.
- MU conviction, WATCH investability, thesis-anchor sizing, Black-Litterman, and manual override remain future approval items.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

### Changed Runtime Files

```text
dashboard.py
views/optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
```

### Touched Interfaces

- `Portfolio & Allocation`: optimizer is top-level again; YTD Performance renders below optimizer and uses current optimizer weights.
- `Portfolio Optimizer`: selected price series are refreshed in-memory from adjusted-close yfinance data for current display freshness before optimization/allocation rendering.
- `YTD Comparison`: SPY/QQQ benchmarks and selected stock prices are refreshed through the latest available market date without canonical data writes.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 15 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` -> PASS, 7 passed.
- `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py` -> PASS.
- Browser check -> optimizer appears before YTD, SPY/QQQ metrics render, freshness reports `2026-05-08`.

### Open Risks

- yfinance overlay remains a display freshness path, not canonical ingestion.
- Broad dirty worktree remains inherited and out of this narrow runtime slice.

## Header

- `PACKET_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-impact`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `OWNER`: `PM / Architecture Office`

## Changed Files

```text
opportunity_engine/candidate_card_schema.py
data/candidate_cards/MSFT_supercycle_candidate_card_v0.json
data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json
tests/test_g8_2_system_scouted_candidate_card.py
scripts/build_context_packet.py
tests/test_build_context_packet.py
docs/architecture/g8_2_system_scouted_candidate_card_policy.md
docs/handover/phase65_g82_system_scouted_candidate_card_handover.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/decision log.md
docs/notes.md
docs/lessonss.md
docs/prd.md
docs/spec.md
README.md
```

Inherited dirty/untracked files from earlier or parallel work remain present in the worktree and are not G8.2-owned unless listed above.

## Touched Interfaces

### Interface 1: Candidate Card Schema

- **Type**: static JSON research-object validator.
- **Owner**: Data + Docs/Ops.
- **Changed**: rejects `factor_score` / `factor_scores` leakage and validates optional governance flags when present.
- **Consumers**: G8 and G8.2 focused tests, future card readers.

### Interface 2: Candidate Card Artifacts

- **Type**: static card and manifest bundle.
- **Owner**: Data.
- **Changed**: added one MSFT card from `LOCAL_FACTOR_SCOUT`.
- **Consumers**: planner/context and future dashboard card reader.

### Interface 3: Context Selection

- **Type**: deterministic context-builder handover selection.
- **Owner**: Docs/Ops.
- **Changed**: G8.2 handover sorts after DASH-1 but before future G9.
- **Consumers**: planner/context bootstrap.

## Failing Checks

- None in current focused verification.
- Broad dirty worktree and inherited broad compileall hygiene remain out of scope.

## Passing Checks

- Focused G8.2 tests: PASS, 13 passed.
- G8/G8.1B/G8.2 regression: PASS, 45 passed.
- Context-builder tests: PASS, 16 passed.
- Scoped compile: PASS.

## Stream Impact

### Backend

- Candidate-card validator updated only for forbidden factor-score leakage and optional governance flags.
- No provider, scoring, ranking, alert, broker, backtest, or dashboard runtime behavior changed.

### Frontend/UI

- No dashboard runtime files changed by G8.2.
- Existing dashboard MSFT rows remain legacy runtime output and are not connected to the MSFT card.
- Future dashboard card reader remains a separate approval.

### Data

- Added one static MSFT card and one manifest.
- No canonical market-data write, no provider call, no ingestion, and no new scout output.

### Docs/Ops

- Policy, handover, current truth surfaces, decision log, notes, lessons, and SAW are G8.2-owned.

## Risks

1. MSFT appearing in the dashboard can be overread as G8.2 card integration.
2. Local factor scout provenance can be overread as factor-model validation.
3. Official/public evidence pointers can be overread as thesis validation.
4. Future dashboard work could accidentally mix candidate-card status with legacy action labels.

## Evidence

- `.venv\Scripts\python -m pytest tests\test_g8_2_system_scouted_candidate_card.py -q` -> PASS, 13 passed.
- `.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q` -> PASS, 45 passed.
- `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m py_compile opportunity_engine\candidate_card_schema.py opportunity_engine\candidate_card.py tests\test_g8_2_system_scouted_candidate_card.py` -> PASS.

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

### Changed Runtime Files

```text
dashboard.py
views/page_registry.py
views/optimizer_view.py
```

### Changed Test Files

```text
tests/test_dash_1_page_registry_shell.py
tests/test_dash_2_portfolio_ytd.py
tests/test_optimizer_view.py
```

### Touched Interfaces

- `portfolio_allocation_state`: explicit state object for optimizer, cash-only, current-hold replay, and Rule of 100 replay output.
- `portfolio-and-allocation` route: visible Portfolio page remains default and direct route resolves through explicit `url_path`.
- `Portfolio copy`: optimizer output and replay output are described separately in the UI.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py views\page_registry.py tests\test_optimizer_view.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_portfolio_universe.py -q` -> PASS.
- `AppTest.from_file("dashboard.py")` with `query_params["page"]="portfolio-and-allocation"` -> PASS, no exception, Portfolio page and current-hold replay output rendered.
