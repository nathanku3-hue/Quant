# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, or scope widening by itself.
Purpose: coordinate streams after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Portfolio Replay Role Contract

### Backend/Strategy

- **Status**: replay, context, and artifact schemas now include `context_role` and `row_role`.
- **Must Deliver**: keep `normalize_context_frame_for_replay(...)` as the single normalization authority and keep legacy artifact role hydration backward-compatible.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: Portfolio tables render role-aware labels and dashboard context normalization delegates to backend/strategy.
- **Must Deliver**: do not reintroduce generic replay `Weight` labels or private dashboard context-normalization logic.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_dash_1_page_registry_shell.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: no canonical data write; diagnostics are generated from the existing `DashboardReplayContext`.
- **Must Deliver**: diagnostic artifacts must include run/source/method/cache identity and must not rebuild replay.

### Docs/Ops

- **Status**: product/spec surfaces, phase brief, notes, decision log, lessons, and context packets record the role contract.
- **Must Deliver**: run SAW gate before claiming closure.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, and diagnostic-triggered replay rebuilds remain blocked.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

### Backend/Strategy

- **Status**: selected-method replay context normalization now exposes replay-derived `target_weight` for aux rows while retaining legacy `weight` as audit metadata.
- **Must Deliver**: keep daily replay rows as the only target-weight authority for event/decision display semantics.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: Portfolio Strategy Replay surfaces align saved/transitional aux rows to replay target weights and timeline displays stacked allocation composition.
- **Must Deliver**: keep partial saved/transitional schemas fail-soft, keep timeline display-only, and retain executable Plotly trace coverage for stacked allocation semantics.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added; saved-artifact schema compatibility is preserved through existing selected-method replay artifact columns.
- **Must Deliver**: legacy aux weight remains audit-only and must not override replay target weights.

### Docs/Ops

- **Status**: notes, decision log, product/spec surfaces, phase brief, lessons, and current truth surfaces record the replay-weight invariant and SAW reconciliation.
- **Must Deliver**: keep aux-weight and partial-schema regressions in focused verification.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, and durable saved-artifact superset/subset policy remain blocked.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

### Backend/Strategy

- **Status**: backend replay/context filtering remains strict to replay rows; no strategy engine semantic change.
- **Must Deliver**: keep context normalization tied to replay tickers and do not add a separate lifecycle-history display source.

### Frontend/UI

- **Status**: dashboard replay request assets now expand from signed current assets to horizon-aware context assets when in-window lifecycle/history tickers exist; selected PIT loading still uses current-only allocation assets.
- **Must Deliver**: keep current allocation signed-current-only while replay history uses zero-weight context-only rows in the widened bundle.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added; ticker-to-permno mapping uses loaded local ticker map and price columns.
- **Must Deliver**: unresolved or unpriced history tickers remain excluded; full PIT membership rows must not leak through coverage pre-gate into dashboard replay evidence.

### Docs/Ops

- **Status**: notes, decision log, lesson, phase brief, and current truth surfaces record the current-allocation vs horizon-history split.
- **Must Deliver**: keep MU regression coverage in focused verification.

### Blocked

- Current-allocation universe widening, durable saved-artifact horizon supersets/subsets, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

### Backend/Strategy

- **Status**: batched selected-method replay input loading preserves full PIT membership proof and shrinks only price/return loading for selected permnos.
- **Must Deliver**: keep membership proof and replay asset selection separate; do not let selected-price narrowing become watchlist-only replay.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `dashboard.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`
  - `tests/test_optimizer_view.py`

### Frontend/UI

- **Status**: dashboard passes signed numeric replay assets into the cached batched PIT loader while retaining signed-selection validation and final asset filtering.
- **Must Deliver**: keep replay request construction signed-selection driven and fail-closed when selection is unavailable.

### Data

- **Status**: MU/SNDK trace shows both names are pinned, mapped, PIT-present on latest replay date, and locally priced; latest exclusions are downstream gates, not missing local data.
- **Must Deliver**: investigate Rule100 candidate/history inclusion separately if requested.
- **Owned Files Referenced**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Docs/Ops

- **Status**: product/spec/notes/decision/lesson/phase/context surfaces record the two-track boundary and local evidence path.
- **Must Deliver**: preserve the "not watchlist-only" boundary in future replay performance work.

### Blocked

- Watchlist-only replay, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

### Backend/Strategy

- **Status**: no backend replay engine or saved artifact reader change in this frontend cache repair.
- **Must Deliver**: keep saved-artifact acceptance exact until a separate superset/subset policy is designed and tested.

### Frontend/UI

- **Status**: `_ensure_daily_portfolio_replay_context(...)` now reuses a wider ready in-session daily replay for shorter covered horizons before rebuilding.
- **Must Deliver**: prove non-date replay identity and actual requested-date row coverage before reuse; return a horizon-scoped context.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: maintain PIT source semantics and signed-asset filtering; no provider ingestion or canonical write.

### Docs/Ops

- **Status**: notes, decision log, phase brief, and current truth surfaces record the in-session-only superset reuse rule.
- **Must Deliver**: keep superset-cache regressions in focused verification.

### Blocked

- Durable saved-artifact superset/subset reads, provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Max Replay Timeline Sampling Fix

### Backend/Strategy

- **Status**: no backend replay engine changes in this frontend display repair.
- **Must Deliver**: keep daily replay rows as the source for display sampling.

### Frontend/UI

- **Status**: max-window Strategy Replay Timeline sampling now normalizes grouped weekly date Series correctly.
- **Must Deliver**: keep sampled rows display-only and out of Portfolio Performance.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: no sampled replay artifact or canonical market-data write is created by timeline display sampling.

### Docs/Ops

- **Status**: notes, decision log, phase brief, lesson, and current truth surfaces record the max-window sampler fix.
- **Must Deliver**: keep the long-window regression in focused verification.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

### Backend/Strategy

- **Status**: no backend reader internals changed in this frontend repair.
- **Must Deliver**: backend producers still need to emit `dashboard_cache_signature` for production saved-artifact UI hits.

### Frontend/UI

- **Status**: saved-artifact adapter now preserves artifact event/decision rows exactly, including empty frames.
- **Must Deliver**: keep `source_mode="saved_artifact"` artifact-owned for replay rows, latest snapshot, event rows, and decision rows.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Data

- **Status**: no data-write path added.
- **Must Deliver**: empty artifact event/decision row sets remain valid saved evidence and must not be mixed with direct fallback frames.

### Docs/Ops

- **Status**: Frontend/UI saved replay source-selector SAW report is mirrored to `docs/saw_reports/`.
- **Must Deliver**: keep the single-source aux-surface regression and report path discoverable from current truth surfaces.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Backend Replay Reader Identity Hardening

### Backend/Strategy

- **Status**: saved replay manifest identity now rejects blank `run_id`, `source_id`, and `method_id` before optional expected-ID checks.
- **Must Deliver**: keep manifest identity validation ahead of parquet equality, context matching, and bundle reconstruction.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: no dashboard runtime changes in this backend hardening slice.
- **Must Deliver**: keep requiring exact `dashboard_cache_signature` before saved-artifact UI consumption can replace the labeled transitional fallback.

### Data

- **Status**: blank manifest+parquet identity now fails closed instead of reconstructing replay evidence.
- **Must Deliver**: selected-method replay artifacts must carry non-empty run/source/method identity and remain display-only evidence under runtime cache.

### Docs/Ops

- **Status**: backend SAW report published at `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`.
- **Must Deliver**: keep the prior reader/budget closure auditable from `docs/saw_reports/` and current truth surfaces.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Overlay Overlap Anchor Fix

### Backend/Strategy

- **Status**: scaled overlay helper now requires same-column local/live overlap.
- **Must Deliver**: do not add a permissive no-overlap evidence mode.

### Frontend/UI

- **Status**: selected-price and benchmark YTD evidence drops unanchored stale live overlays.
- **Must Deliver**: keep UI captions tied to available/dropped evidence rather than synthetic continuity.

### Data

- **Status**: live overlay remains display-only and non-canonical.
- **Must Deliver**: stale local ending dates cannot be scaled to fresh live rows without a same-ticker anchor date.

### Docs/Ops

- **Status**: SAW Implementer and Reviewer A/B/C all passed.
- **Must Deliver**: carry adjacent replay/YTD session-state advisory as future hygiene only.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

### Backend/Strategy

- **Status**: `PriceEndpointFreshness` snapshot and snapshot-aware endpoint helpers implemented.
- **Must Deliver**: keep endpoint snapshot as a reuse/performance layer only; freshness policy remains explicit and fail-closed.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: dashboard and optimizer view consume a cached endpoint snapshot for YTD, selected-price prep, and default ordering.
- **Must Deliver**: do not reintroduce render-path full-matrix scans when adding new Portfolio & Allocation consumers.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Data

- **Status**: local matrix endpoint measurement recorded; no data writes performed.
- **Must Deliver**: preserve exact endpoint semantics for finite positive price values; NaN/inf/zero remain non-endpoints.

### Docs/Ops

- **Status**: truth surfaces updated; SAW implementer PASS received and reviewer reconciliation pending.
- **Must Deliver**: publish final SAW PASS/BLOCK for this performance slice before claiming governance closure.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

### Backend/Strategy

- **Status**: endpoint freshness helpers, shared tolerance predicate, and universe endpoint gate implemented.
- **Must Deliver**: keep history count separate from endpoint freshness; stale endpoints remain ineligible until refreshed unless an explicit policy tolerance permits them.
- **Owned Files Referenced**:
  - `core/data_orchestrator.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: dashboard YTD and optimizer view now fail closed/drop stale selected assets instead of presenting stale columns as current.
- **Must Deliver**: keep captions and metrics tied to assets that pass endpoint checks.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Data

- **Status**: live overlay remains display-only and non-canonical.
- **Must Deliver**: endpoint/tolerance semantics stay centralized in `core.data_orchestrator`; unresolved stale columns must be dropped/unavailable rather than forward-filled; scaled overlays require same-column local/live overlap before live rows can become allocation or benchmark evidence.

### Docs/Ops

- **Status**: docs/truth surfaces refreshed; independent SAW Implementer and Reviewer A/B/C rerun completed PASS.
- **Must Deliver**: carry saved replay artifact-reader consumption and explicit performance-budget work as separate future scope.

### Blocked

- Provider ingestion, canonical market-data writes, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

### Backend/Strategy

- **Status**: backend selected-method bundle consumer verified through dashboard transitional build.
- **Must Deliver**: keep `build_selected_method_replay(...)` as the only selected-method replay bundle API for dashboard replay consumption.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`

### Frontend/UI

- **Status**: dashboard consumption verified with full pytest and runtime smoke.
- **Must Deliver**: keep `_build_dashboard_strategy_replay_context(...)` wired to `build_selected_method_replay(...)` with `_dashboard_input_loader`; saved artifact-reader consumption remains future work.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: PIT input-loader boundary verified for dashboard bundle consumption.
- **Must Deliver**: maintain `end_date=as_of_date` and `universe_mode="r3000_pit"` for dashboard replay inputs.

### Docs/Ops

- **Status**: stale open-risk text refreshed; runtime smoke and full pytest evidence captured.
- **Must Deliver**: keep saved artifact-reader/performance-budget work separate from verified transitional bundle consumption.

### Blocked

- Provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Replay Coverage Contract Audit Fix

### Backend/Strategy

- **Status**: audit fix implemented and full pytest PASS.
- **Must Deliver**: preserve batched uncovered-date emission, row-heavy unavailable fast rows, next-tradable-return performance alignment, run-level loader equity, small-frame performance lookup, and inverse-volatility bound-feasible diagnostics fast path.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `strategies/optimizer.py`
  - `tests/test_strategy_replay_coverage.py`
  - `tests/test_optimizer_core_policy.py`

### Frontend/UI

- **Status**: no UI behavior changed in this audit fix.
- **Must Deliver**: dashboard backend-bundle consumption/runtime smoke are now verified; saved artifact-reader consumption remains future work.

### Data

- **Status**: replay coverage reasons, segments, PIT return alignment, and row-heavy unavailable performance are now preserved in tested outputs.
- **Must Deliver**: keep uncovered dates explicit as `input_unavailable:*` / `cash_closed`, never stale carry-forward.

### Docs/Ops

- **Status**: docs and context surfaces refreshed for the audit fix.
- **Must Deliver**: keep `current_context.*` bootstrapped from the latest current truth packet, and carry saved artifact-reader/performance-budget work as open phase-close work.

### Blocked

- Provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims remain blocked.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

### Backend/Strategy

- **Status**: focused implementation passed.
- **Must Deliver**: keep `build_selected_method_replay(...)` as the backend selected-method replay bundle API, preserve shared `REPLAY_COLUMNS`, CASH rows, context filtering, and performance fields, and keep `write_selected_method_replay_artifact_atomic(...)` rollback-safe for parquet+manifest evidence.
- **Owned Files Referenced**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`
  - `tests/test_strategy_replay_artifact.py`
  - `tests/test_replay_non_cash_closed.py`

### Frontend/UI

- **Status**: implementation verified with backend bundle consumption, full pytest, and runtime smoke.
- **Must Deliver**: keep `DashboardReplayContext` as the dashboard context for Strategy Replay rows, latest snapshot, annotations, Buy/Sell rows, and YTD latest-weight preference; keep saved artifact-reader consumption separate until approved.
- **Owned Files Referenced**:
  - `dashboard.py`
  - `tests/test_dash_2_portfolio_ytd.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: PIT rule and durable artifact writer locked.
- **Must Deliver**: every replay date uses `end_date=as_of_date` and `universe_mode="r3000_pit"`; failed or empty dates must emit explicit `cash_closed` context; saved replay evidence stays under `data/runtime_cache/strategy_replay` with run id and manifest metadata.

### Docs/Ops

- **Status**: evidence handoff refreshed after dashboard backend-bundle integration, full regression, and runtime smoke passed.
- **Must Deliver**: keep saved artifact-reader consumption and performance-budget risks visible until separately implemented and tested.

### Blocked

- Saved-evidence PASS claims without dashboard backend-bundle traceability, stale carry-forward, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and promotion claims without same-window/same-cost/same-engine deltas remain blocked.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

### Backend/Strategy

- **Status**: pending implementation approval.
- **Must Deliver**: selected-method adapters call one shared replay run/source and return a run/artifact identifier instead of independent UI/YTD computations.
- **Owned Files**: TBD by implementation worker; Worker 3 makes no code edits.

### Frontend/UI

- **Status**: pending implementation approval.
- **Must Deliver**: Portfolio & Allocation YTD, latest allocation snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log must render from the same selected-method replay source.
- **Owned Files**: TBD by implementation worker; current bridges remain transitional.

### Data

- **Status**: pending implementation approval.
- **Must Deliver**: saved evidence artifact records run id, method id, input signatures, date window, costs, baseline id, row/status counts, and timing.
- **Owned Files**: TBD by implementation worker.

### Docs/Ops

- **Status**: guardrail refreshed; docs-only SAW report maintained.
- **Must Deliver**: keep the invariant and performance budget in the done checklist until implementation proves it.

### Blocked

- Second replay stacks, stale allocation carry-forward, fake improvement claims, overfit promotion, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, and unlabeled transitional bridges remain blocked.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

### Backend/Strategy

- **Status**: implemented; focused and full tests PASS.
- **Must Deliver**: Rule100 visible allocation and Strategy Replay derive per-name budget and cap from `controls.max_weight` through `rule100_config_from_max_weight(...)`.
- **Owned Files**:
  - `strategies/rule100_softmax.py`
  - `strategies/strategy_replay.py`
  - `tests/test_rule100_softmax.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: implemented; direct UI and Strategy Replay agreement tests PASS.
- **Must Deliver**: direct Rule100 UI passes `controls.max_weight` into the softmax path and never rewrites frozen history to make current UI targets appear historical.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `dashboard.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: implemented; stale-aware benchmark behavior tests PASS.
- **Must Deliver**: benchmark freshness is evaluated per ticker; stale/missing QQQ can be live-overlaid while fresh SPY stays local, and stale columns are dropped if overlay fails.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Docs/Ops

- **Status**: refreshed; SAW PASS.
- **Must Deliver**: preserve the boundary that frozen Rule100 history/audit defaults remain 10%/15% unless a separate versioned/labeled UI-policy artifact is approved.

### Blocked

- Frozen history rewrite, canonical provider ingestion, benchmark backfill promotion, alerts, broker behavior, live trading, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

### Backend/Strategy

- **Status**: implemented; focused and affected tests PASS.
- **Must Deliver**: `build_strategy_replay(...)` consumes `StrategyReplayInputs` from the dashboard path; target-weight output is generated from per-date PIT slices.
- **Owned Files**:
  - `strategies/strategy_replay.py`
  - `tests/test_strategy_replay.py`

### Frontend/UI

- **Status**: implemented; source guards PASS.
- **Must Deliver**: Portfolio & Allocation Strategy Replay loads one PIT input per replay date and no longer passes raw `prices_wide[replay_assets]`.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_optimizer_view.py`
  - `tests/test_position_lifecycle.py`
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: implemented; path/signature guards PASS.
- **Must Deliver**: cache signatures require `r3000_pit`; repo-local replay input artifacts stay under `data/runtime_cache/strategy_replay`.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`
  - `tests/test_strategy_replay_artifact.py`

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: keep explicit boundary that input artifacts are not replay output artifacts.

### Blocked

- Target-weight artifact persistence, provider ingestion, canonical market-data writes, alerts, broker behavior, live trading, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: v1.1 factor strength and coverage use approved groups with neutral missing-value shrinkage.
- **Owned Files**:
  - `strategies/rule100_softmax_v1_1.py`
  - `tests/test_rule100_softmax_v1_1.py`

### Frontend/UI

- **Status**: implemented; real dashboard AppTest PASS.
- **Must Deliver**: Policy Target Timeline proof uses `AppTest.from_file("dashboard.py")`, not copied mini-app code.
- **Owned Files**:
  - `tests/test_policy_target_timeline_apptest.py`

### Data

- **Status**: refreshed; stale artifact retired.
- **Must Deliver**: v1.1 active artifacts are comparison CSV and summary JSON only; no active v1.1 history CSV.

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: carry boundary that v1.1 is research-only and not promoted runtime sizing.

### Blocked

- v1.1 runtime promotion, recreated v1.1 history, lifecycle log mutation, broker behavior, alerts, provider ingestion, ranking/scoring, and new optimizer objectives remain blocked.

## Latest Addendum - Rule of 100 Method Label

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: softmax v1 history overlay uses the same sizing helper as current UI and does not fork Kelly into a second stack.
- **Owned Files**:
  - `scripts/rule100_softmax_v1_audit.py`
  - `tests/test_rule100_softmax.py`

### Frontend/UI

- **Status**: implemented; renderer source guard PASS.
- **Must Deliver**: transaction history distinguishes immutable event weights from derived softmax v1 targets.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_position_lifecycle.py`

### Data

- **Status**: implemented; artifact regenerated.
- **Must Deliver**: `data/processed/rule100_softmax_v1_history.csv` is additive and must not overwrite `data/portfolio_lifecycle_log.jsonl`.

### Docs/Ops

- **Status**: refreshed.
- **Must Deliver**: carry boundary that v0 event ledger and v1 target overlay are separate audit surfaces.

### Blocked

- Lifecycle log mutation, broker behavior, alerts, provider ingestion, ranking/scoring, new optimizer objective, and Kelly stack expansion remain blocked.

## Previous Addendum - Rule of 100 Method Label

### Backend/Strategy

- **Status**: implemented; focused registry tests PASS.
- **Must Deliver**: `Rule of 100` method label exists without becoming a mean-variance optimizer objective.
- **Owned Files**:
  - `strategies/optimizer.py`
  - `tests/test_portfolio_universe.py`

### Frontend/UI

- **Status**: implemented; focused AppTest PASS.
- **Must Deliver**: selecting `Rule of 100` renders Rule100 softmax v1 target weights plus residual cash and bypasses cached optimizer execution.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `tests/test_optimizer_view.py`

### Data

- **Status**: unchanged.
- **Must Deliver**: continue using PIT current lifecycle holds as the softmax candidate source; no provider ingestion or canonical data writes.

### Docs/Ops

- **Status**: context and spec surfaces refreshed; runtime manual audit PASS on port 8509.
- **Must Deliver**: record that the label is softmax sizing over lifecycle holds, not a new optimizer objective.

### Blocked

- New optimizer objective, ranking, scoring, broker behavior, alerting, provider ingestion, live trading, and generic strategy framework remain blocked.

## Latest Addendum - Rule100 Lifecycle Policy v0

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: concrete Rule100 lifecycle v0, not a generic replay framework.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: v0 runtime and audit artifacts promoted.
- **Must Deliver**: 29-event runtime replay, v0 decision tape, baseline comparison.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.jsonl`
  - `data/portfolio_lifecycle_decision_log.jsonl`
  - `data/portfolio_lifecycle_buy_sell_log.jsonl`
  - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

### Frontend/UI

- **Status**: unchanged; focused portfolio tests PASS.
- **Must Deliver**: dashboard remains compatible with ENTER/EXIT runtime lifecycle log and must not render TRIM/TIGHTEN as live recommendations.

### Docs/Ops

- **Status**: docs/context updates in progress; SAW remains BLOCK without independent subagent passes.
- **Must Deliver**: carry Rule100 proxy/literal-column limitation and audit-only TRIM/TIGHTEN boundary.

### Blocked

- Generic replay framework, provider ingestion, canonical writes, broker orders, alerts, ranking, scoring, dashboard action-label changes, Phase 54 Rule-of-100 sleeve reopen, and live trading remain blocked.

## Latest Addendum - Lifecycle Decision Export

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: export-only PIT decision tape that matches replay events and preserves reason codes.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: analysis artifacts published.
- **Must Deliver**: full decision JSONL, compact buy/sell JSONL, and audit summary.
- **Owned Files**:
  - `data/portfolio_lifecycle_decision_log.jsonl`
  - `data/portfolio_lifecycle_buy_sell_log.jsonl`
  - `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`

### Frontend/UI

- **Status**: unchanged.
- **Must Deliver**: no UI action-label change; dashboard continues to render ENTER/EXIT lifecycle vocabulary.

### Docs/Ops

- **Status**: docs/context updates in progress; SAW remains BLOCK without independent subagent passes.
- **Must Deliver**: carry export as audit-only until user approves policy implementation.

### Blocked

- Broker orders, alerts, recommendations, ranking, scoring, provider ingestion, canonical writes, dashboard action-label changes, and full execution-ledger semantics remain blocked.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

### Backend/Strategy

- **Status**: implemented; focused tests PASS.
- **Must Deliver**: replay ENTER sizing, PIT factor confirmation, entry/exit confirmation, cooldown, and CLI repeatability.
- **Owned Files**:
  - `scripts/pit_lifecycle_replay.py`
  - `tests/test_pinned_universe.py`

### Data

- **Status**: final replay published to runtime JSONL after evidence verification.
- **Must Deliver**: open current holds must reflect lifecycle state, not full-cash fallback.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.jsonl`
  - `docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl`

### Frontend/UI

- **Status**: implemented; reboot/browser smoke PASS on port 8509.
- **Must Deliver**: Portfolio & Allocation shows lifecycle holds plus residual cash, not 100% cash.

### Docs/Ops

- **Status**: docs/context updates and context validation complete; closure/SAW handling in progress.
- **Must Deliver**: closure/SAW handling.

### Blocked

- Phase 54 Rule-of-100 sleeve reopen, ranking, scoring, optimizer objective changes, provider ingestion, canonical writes, broker calls, alerts, conviction mode, Black-Litterman, and live trading remain blocked.

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

### Backend

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: PIT-safe lifecycle open-position reconstruction and lifecycle-first current position memory.
- **Owned Files**:
  - `data/portfolio_lifecycle_log.py`
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: no-fresh-PIT-ENTER with open lifecycle holds renders holds plus residual cash instead of 100% cash.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `dashboard.py`

### Docs/Ops

- **Status**: SAW PASS; context validation and validator checks complete.
- **Must Deliver**: carry Low stale-lock recovery and inherited execution-ledger limits as future follow-ups.

### Blocked

- Provider ingestion, canonical writes, execution ledger, broker calls, alerts, ranking, scoring, conviction mode, Black-Litterman, and new optimizer objectives remain blocked.

## Latest Addendum - Frontend 3-Page Navigation Refactor

### Frontend/UI

- **Status**: implemented; 24 DASH tests + 70 broader tests PASS.
- **Must Deliver**: 3-page navigation model (Portfolio & Allocation, Discovery & Analysis, Entry/Exit Strategy) replacing 8-page shell.
- **Owned Files**:
  - `dashboard.py`
  - `views/page_registry.py`
  - `views/discovery_view.py`
  - `views/strategy_view.py`
  - `tests/test_dash_1_page_registry_shell.py`
  - `tests/test_dash_2_portfolio_ytd.py`

### Backend

- **Status**: no changes.
- **Must Deliver**: N/A.

### Docs/Ops

- **Status**: truth surfaces updated.
- **Must Deliver**: multi-stream contract addendum, planner packet refresh.

### Blocked

- Provider ingestion, canonical writes, scanner semantic changes, strategy search, ranking, scoring, alerts, brokers, optimizer objective changes, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

### Frontend/UI

- **Status**: dashboard unified parquet package load is cached across Streamlit reruns; full pytest and SAW PASS.
- **Must Deliver**: keep top-level dashboard load responsive without changing page behavior or data authority.
- **Owned Files**:
  - `dashboard.py`
  - `tests/test_dashboard_sprint_a.py`

### Data/Ops

- **Status**: source parquet cache signature implemented and tested.
- **Must Deliver**: invalidate cached package when relevant processed/static parquet source files are added, removed, or rewritten.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_data_orchestrator_portfolio_runtime.py`

### Docs/Ops

- **Status**: bridge, impact, done checklist, planner packet, notes, decision log, lessons, SAW report, post-phase alignment, and observability pack updated.
- **Must Deliver**: carry mutable `st.cache_resource` residual risk as a future dashboard-owner guardrail.

### Blocked

- Provider ingestion, canonical market-data writes, alpha-engine loop rewrite, scanner financial-statement cache, scanner semantic changes, ranking, scoring, alerts, brokers, optimizer objective changes, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Scanner Testability Hardening

### Backend/Strategy

- **Status**: scanner formula extraction implemented; focused tests PASS.
- **Must Deliver**: deterministic scanner math must be importable and tested outside Streamlit.
- **Owned Files**:
  - `strategies/scanner.py`
  - `tests/test_scanner.py`

### Frontend/UI

- **Status**: dashboard provider/cache/persistence boundary preserved; enrichment delegates to strategy module.
- **Must Deliver**: no dashboard product redesign or semantic expansion inside this testability lane.
- **Owned Files**:
  - `dashboard.py`

### Data/Ops

- **Status**: ETL/config/process guardrail coverage added or preserved; focused tests PASS.
- **Must Deliver**: keep canonical market-data writes and provider ingestion blocked.
- **Owned Files**:
  - `core/etl.py`
  - `tests/test_core_etl.py`
  - `tests/test_process_utils.py`

### Blocked

- Provider ingestion, canonical writes, scanner semantic changes, strategy search, ranking, scoring policy changes, alerts, brokers, dashboard redesign, and candidate-card dashboard merge.

## Latest Addendum - Dashboard Architecture Safety Slice

### Backend/Ops

- **Status**: shared process liveness helper implemented; focused tests PASS.
- **Must Deliver**: Windows-safe PID liveness and fail-closed backtest spawn behavior for live PID files.
- **Owned Files**:
  - `utils/process.py`
  - `data/updater.py`
  - `scripts/parameter_sweep.py`
  - `scripts/release_controller.py`
  - `backtests/optimize_phase16_parameters.py`

### Frontend/UI

- **Status**: dashboard helper cleanup implemented; focused tests PASS.
- **Must Deliver**: one strategy matrix initializer and canonical portfolio price cleanup delegation.
- **Owned Files**:
  - `dashboard.py`

### Docs/Ops

- **Status**: docs/context updated; independent SAW Implementer and Reviewer A/B/C passes complete.
- **Must Deliver**: longer full-regression window only if phase-close proof is requested.

### Blocked

- Provider ingestion, canonical writes, dashboard redesign, strategy search, ranking, scoring, alerts, brokers, and candidate-card dashboard merge.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

### Backend

- **Status**: display-only overlay cache and optimizer-run cache implemented; focused tests PASS.
- **Must Deliver**: non-canonical Parquet cache, background refresh scheduling, atomic temp->replace cache writes, copy-safe overlay scaling cache.
- **Owned Files**:
  - `core/data_orchestrator.py`
  - `tests/test_optimizer_view.py`

### Frontend/UI

- **Status**: optimizer render path reconciled and AppTest coverage added; focused tests PASS.
- **Must Deliver**: view render coverage, mean-variance dropdown coverage, sector-cap control coverage, cached optimizer reruns.
- **Owned Files**:
  - `views/optimizer_view.py`
  - `tests/test_optimizer_view.py`

### Docs/Ops

- **Status**: docs/context refreshed; runtime smoke, full/focused validation, and SAW PASS complete.
- **Must Deliver**: completed for this hardening round; future work may address Low executor-submit containment and background-refresh diagnostics.

### Blocked

- Canonical provider ingestion, market-data writes, optimizer objective changes, lower-bound policy, MU conviction, WATCH investability, Black-Litterman, alerts, brokers, ranking, scoring, and candidate-card dashboard merge.

## Latest Addendum - Portfolio Data Boundary Refactor

### Backend

- **Status**: data-boundary refactor implemented; focused tests PASS.
- **Must Deliver**: selected-stock display overlay fetching, local TRI scaling/stitching, and strategy metrics parsing in `core/data_orchestrator.py`.
- **Owned Files**:
  - `core/data_orchestrator.py`

### Frontend/UI

- **Status**: optimizer view consumes orchestrator helpers; focused tests PASS.
- **Must Deliver**: no direct yfinance import and no direct `data/backtest_results.json` parsing in `views/optimizer_view.py`.
- **Owned Files**:
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: data-boundary docs/context refresh and SAW PASS complete.
- **Must Deliver**: completed for that architecture hygiene round.

### Blocked

- Canonical provider ingestion, market-data writes, optimizer objective changes, MU conviction, WATCH investability, Black-Litterman, alerts, brokers, ranking, scoring, and candidate-card dashboard merge.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

### Backend

- **Status**: diagnostics implemented; focused tests PASS.
- **Must Deliver**: structured diagnostics module, diagnostic-returning optimizer methods, no objective/policy expansion.
- **Owned Files**:
  - `strategies/optimizer_diagnostics.py`
  - `strategies/optimizer.py`

### Frontend/UI

- **Status**: diagnostics UI implemented; focused tests PASS.
- **Must Deliver**: optimizer status, feasibility, active constraints, max-cap/lower-bound assets, equal-weight forced status, and fallback labels.
- **Owned Files**:
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: final validation and SAW PASS complete.
- **Must Deliver**: completed for that diagnostics round.

### Blocked

- MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new objective, scanner changes, manual override, providers, alerts, brokers, and replay behavior.

## Latest Addendum - Optimizer Core Policy Audit

### Backend

- **Status**: audit-only; no implementation changes.
- **Must Deliver**: optimizer constraints policy, lower-bound/SLSQP audit, and focused policy tests.

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no new active-bound UI until optimizer-core diagnostics are approved.

### Docs/Ops

- **Status**: active SAW closeout.
- **Must Deliver**: audit docs, tests, SAW report, closure/evidence validation.

### Blocked

- Runtime lower-bound support, conviction mode, WATCH investability, Black-Litterman, scanner changes, universe eligibility changes, providers, alerts, and brokers.

## Latest Addendum - Portfolio Universe Quarantine Closure

### Backend

- **Status**: universe fix PASS; optimizer-core diff quarantined.
- **Must Deliver**: no active `strategies/optimizer.py` diff in this closure.
- **Owned Files**:
  - `strategies/portfolio_universe.py`
  - `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`

### Frontend/UI

- **Status**: implemented, focused/browser checks PASS.
- **Must Deliver**: Universe Audit, fail-closed messaging, YTD below optimizer, no optimizer-core math acceptance.

### Docs/Ops

- **Status**: PASS closeout.
- **Must Deliver**: SAW PASS, quarantine note, current truth-surface refresh, separate optimizer audit branch when opened.

### Blocked

- Optimizer lower-bound/SLSQP policy, MU conviction mode, WATCH investability, Black-Litterman, thesis anchors, manual override, scanner rewrite, provider ingestion, alerts, and broker calls remain blocked.

## Latest Addendum - Portfolio Universe Construction Fix

### Backend

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: explicit optimizer universe builder, eligibility policy, ticker-map readiness, price-history readiness, max-weight feasibility diagnostics.
- **Owned Files**:
  - `strategies/portfolio_universe.py`

### Frontend/UI

- **Status**: implemented, focused tests PASS.
- **Must Deliver**: Universe Audit, Why This Allocation, thesis-neutral optimizer labels, no display-order default leakage.
- **Owned Files**:
  - `dashboard.py`
  - `views/optimizer_view.py`

### Docs/Ops

- **Status**: active-final-refresh.
- **Must Deliver**: portfolio construction contract, decision/notes/lessons/truth-surface updates, SAW report.

### Blocked

- MU hard floor, conviction mode, Black-Litterman, thesis anchors, manual override, scanner rewrite, provider ingestion, alerts, and broker calls remain blocked.

## Header

- `CONTRACT_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-streams`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Stream Map

### Backend

- **Status**: scoped-complete pending SAW.
- **Must Deliver**: candidate-card validator guardrail only.
- **Owned Files**:
  - `opportunity_engine/candidate_card_schema.py`

### Frontend/UI

- **Status**: held.
- **Must Deliver**: no G8.2 dashboard runtime work.
- **Notes**: existing MSFT rows in the running dashboard are legacy runtime output, not the G8.2 card.

### Data

- **Status**: scoped-complete pending SAW.
- **Must Deliver**: exactly one MSFT candidate card and manifest from the existing scout output.
- **Owned Files**:
  - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
  - `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`

### Docs/Ops

- **Status**: active-final-refresh.
- **Must Deliver**: G8.2 policy, handover, truth surfaces, governance logs, validation, and SAW.

## Blocked Streams

- G9 market-behavior signal card remains blocked until explicit approval.
- G8.3 user-seeded candidate card remains blocked until explicit approval.
- Dashboard card reader/status shell remains blocked until explicit approval.
- Provider ingestion, alerts, broker calls, rankings, scores, factor-model validation, buy/sell/hold output, and buying-range claims remain blocked.

## Governance Status

- G8.1B-R reviewer rerun: Complete, PASS.
- DASH-1 Page Registry Shell: Complete, shell-only PASS.
- G8.2 System-Scouted Candidate Card: Current, candidate-card-only pending SAW.
- Next action: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.
