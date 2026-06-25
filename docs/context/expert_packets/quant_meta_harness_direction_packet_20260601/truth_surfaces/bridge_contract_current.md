# Bridge Contract - Current

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file does not authorize live trading, broker automation, promotion, provider ingestion, strategy search, candidate ranking, candidate scoring, candidate validation, alerts, dashboard content redesign, macro scoring, factor scoring, or scope widening.
Purpose: connect Quant's technical state back to product/system truth after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Governed Data Source Provenance Intake

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`
- `ScopeID`: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`
- `SYSTEM_DELTA`: `Source-provenance intake packet exists at docs/architecture/governed_data_source_provenance_intake_20260528.md; it approves raw/source provenance review only and does not authorize generation yet.`
- `PM_DELTA`: `GovernedDataAuthorizationPacket and DataSourceAcquisitionPacket are PASS, but DataReadyStrict remains BLOCKED until source provenance, manifests, hashes, generated artifacts, and validation proof exist.`
- `CURRENT_STATE`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.`
- `BLOCKING_REASON`: `Strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.`
- `OPEN_DECISION`: `Approve source provenance for prices, ticker/security master, WRDS/R3000 membership, and Rule100 history before any data/processed generation.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_provenance_first_then_bounded_offline_regeneration_then_strict_data_readiness_and_require_github_boot_proof.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.`

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`
- `ScopeID`: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`
- `SYSTEM_DELTA`: `Source-acquisition planning packet exists at docs/architecture/governed_data_source_acquisition_20260528.md; it approves planning/source acquisition only, not generation, boot-time generation, or BootReady evidence.`
- `PM_DELTA`: `GovernedDataAuthorizationPacket is PASS, but source acquisition/generation remains BLOCK until trusted sources, approved generators or external bundle, manifests, hashes, and read-only validation are approved.`
- `CURRENT_STATE`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.`
- `BLOCKING_REASON`: `Required canonical data artifacts are absent/ignored/local-governed and not backed by approved source manifests or generators.`
- `OPEN_DECISION`: `Choose A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_acquisition_plus_bounded_offline_regeneration_planning_unless_trusted_bundle_exists_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.`

## Latest Addendum - Governed Data Artifact Authorization

- `RoundID`: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`
- `ScopeID`: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`
- `SYSTEM_DELTA`: `Governed data artifact authorization packet exists at docs/architecture/governed_data_artifact_authorization_20260528.md; it is advisory authorization only, not data generation or BootReady evidence.`
- `PM_DELTA`: `GovernanceGateV0 PASS, BootStatusPathContract PASS, and StrictProof PASS/degraded are preserved while DataReadyStrict remains BLOCKED_MISSING_GOVERNED_ARTIFACTS, SafeBoot false, and BootReady BLOCKED.`
- `LOCAL_TRUTH_DELTA`: `Local artifacts and dirty context are not clean GitHub truth and are not BootReady evidence.`
- `OPEN_DECISION`: `Approve bounded offline regeneration authorization or approve a trusted external bundle for data/processed/prices_tri.parquet, data/processed/prices.parquet, data/processed/tickers.parquet, data/processed/universe_r3000_daily.parquet, and data/processed/rule100_softmax_v1_history.csv.`
- `RECOMMENDED_NEXT_STEP`: `approve_bounded_offline_regeneration_authorization_or_approved_external_bundle_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.`

## Latest Addendum - Research Validity Runner v0 Commit Anchor

- `SYSTEM_DELTA`: `Research-validity evidence gating now exists in pushed commit 8716c51781d8524de4147cf42f17e52466913de4.`
- `PM_DELTA`: `The project now has a committed boundary before any strategy, signal, candidate, replay, optimizer output, or dashboard surface can claim research-valid status.`
- `GIT_DELTA`: `GitHub is aligned through 8716c51781d8524de4147cf42f17e52466913de4 on origin/codex/optimizer-core-structured-diagnostics.`
- `DIRTY_WORKTREE_DELTA`: `Remaining dirty/untracked files are inherited or later local context and are not part of the research-validity commit.`
- `OPEN_DECISION`: `Handle remaining inherited/local dirty context as separate buckets before claiming safe boot.`
- `RECOMMENDED_NEXT_STEP`: `classify_remaining_dirty_context_then_continue_boot_preflight_staging.`
- `DO_NOT_REDECIDE`: `Do not mix boot-preflight, dashboard, optimizer/lifecycle, packet zips, or unrelated dirty files into the research-validity commit.`

## Latest Addendum - Portfolio Replay Role Contract

- `SYSTEM_DELTA`: `Portfolio replay rows now carry explicit context_role and row_role schema fields, making replay exposure truth mechanically distinct from lifecycle/event audit intent.`
- `PM_DELTA`: `A row can now be read as current holding, historical context, flat replay exposure, cash, or unavailable without relying on ambiguous Weight labels or status-only inference.`
- `ARTIFACT_COMPAT_DELTA`: `Selected-method replay artifacts hydrate missing role columns from backward-compatible defaults while unrelated schema drift still fails closed.`
- `CODE_QUALITY_DELTA`: `Dashboard context normalization delegates to strategies.strategy_replay.normalize_context_frame_for_replay(...) instead of maintaining a private duplicate.`
- `DIAGNOSTIC_DELTA`: `Closed-trade returns, exit reason quality, zero-exposure BUY rows, hold-time, and reason-code concentration are computed from the existing DashboardReplayContext and include replay identity/cache hash.`
- `TEST_DELTA`: `Scoped compile PASS; targeted role/compat/diagnostic regressions PASS; affected replay/dashboard/AppTest suite PASS with 169 tests.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C all returned PASS; parent reconciliation added Reviewer C hardening regressions for no diagnostic rebuild and strict legacy-only role hydration.`
- `OPEN_DECISION`: `Hold, or separately continue backend dashboard_cache_signature/saved-artifact policy work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, strategy promotion, or diagnostic-triggered replay rebuild is authorized.`

## Latest Addendum - Optimizer History Diagnostics Split

- `SYSTEM_DELTA`: `Portfolio Optimizer universe diagnostics now split true missing local price history from stale local price endpoints while preserving the fail-closed insufficient_history gate.`
- `PM_DELTA`: `GOOGL-style rows with thousands of observations but stale local endpoints no longer read like short-history cases in the UI.`
- `UI_DELTA`: `Universe Audit metrics show Missing History and Stale Endpoint separately, and rows include Latest Price Date.`
- `TEST_DELTA`: `Scoped compile PASS; focused optimizer universe/view suite PASS with 62 tests.`
- `OPEN_DECISION`: `Repairing stale local price columns and rebuilding pre-2025 Rule100 evidence artifacts remain separate Data/Backend follow-ups.`
- `RECOMMENDED_NEXT_STEP`: `repair_stale_price_endpoints_or_build_rule100_pre2025_evidence_artifacts_or_hold.`
- `DO_NOT_REDECIDE`: `Do not relax stale endpoint gating, synthesize BUY/SELL history from prices alone, add provider ingestion, canonical writes, broker behavior, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

- `SYSTEM_DELTA`: `Portfolio & Allocation now aligns ENTER/EXIT and Buy/Sell displayed weights to the same daily selected-method replay target_weight used by the timeline and latest snapshot.`
- `PM_DELTA`: `The page is now not only one-bundle by identity; its visible replay weights also use one semantic source, while original lifecycle/event weights remain audit metadata.`
- `UI_DELTA`: `Strategy Replay Timeline now displays portfolio composition as a stacked step-area allocation chart rather than many independent zero-heavy lines.`
- `FAIL_CLOSED_DELTA`: `Partial saved/transitional event or snapshot schemas render empty/unavailable states instead of crashing the Strategy Replay section.`
- `TEST_DELTA`: `Scoped compile PASS; targeted aux/timeline/fail-soft regressions PASS with executable Plotly trace validation; affected backend replay suite PASS with 80 tests; affected frontend replay suite PASS with 134 tests; latest focused dashboard file PASS with 66 tests.`
- `OPEN_DECISION`: `Backend producers still need dashboard_cache_signature policy work for production saved-artifact UI hits; this round does not change that policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_emission_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now builds replay requests with separate allocation_assets and horizon-aware replay_assets: optimizer/PIT loading uses current signed assets, while the replay bundle can carry zero-weight context-only rows for mapped lifecycle/history tickers inside the selected replay window.`
- `PM_DELTA`: `MU can stay absent from current positive-weight allocation after its SELL while still appearing in the 1Y replay decision history when its BUY/SELL rows are in the horizon.`
- `INTEGRITY_DELTA`: `_normalize_context_frame(...) remains strict; context-only rows are added after backend bundle construction and cache signatures include both replay_assets and allocation_assets, so historical flat tickers are not reused as allocatable holdings.`
- `TEST_DELTA`: `Scoped compile PASS; targeted MU/context/coverage/cache regressions PASS with 4 tests; focused Portfolio/YTD dashboard file PASS with 61 tests; optimizer/replay follow-up PASS with 71 tests.`
- `OPEN_DECISION`: `Saved artifact producers/readers still need separate policy if durable artifacts should serve horizon-aware supersets or subsets beyond exact dashboard_cache_signature matching.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_run_saw_gate_for_horizon_asset_universe_fix.`
- `DO_NOT_REDECIDE`: `No current-allocation universe widening, provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

- `SYSTEM_DELTA`: `Dashboard selected-method replay now builds full-window r3000_pit membership proof first, then limits price/return loading to signed selected permnos that intersect that PIT window.`
- `PM_DELTA`: `Replay performance is improved without making the replay watchlist-only; MU/SNDK disappearance is explained by a separate strategy/data eligibility trace.`
- `PERFORMANCE_DELTA`: `load_batched_pit_replay_data(..., selected_permnos=...) loaded 2 selected price columns across 89 trading dates while preserving proof of 27 PIT members in the local 2026-01-02..2026-05-11 probe; refreshed local elapsed was 0.5015s.`
- `DIAGNOSTIC_DELTA`: `trace_thesis_ticker_eligibility(("MU","SNDK"), ...) reports pinned universe, ticker-map permno, PIT membership, local price/return rows, Rule100 history, sizing/current-hold state, and latest failed gate.`
- `TRACE_RESULT`: `Through 2026-05-11, MU is pinned/mapped/PIT-present/locally priced and latest fails technical quality; SNDK is pinned/mapped/PIT-present/locally priced, has no Rule100 history rows, and latest fails factor threshold.`
- `TEST_DELTA`: `Focused compile PASS; selected-price loader regression PASS; executable dashboard selected-permno guard PASS; MU/SNDK fixture trace regressions including non-finite return rejection PASS; broader affected suite PASS with 112 tests.`
- `OPEN_DECISION`: `Continue strategy/data diagnosis for MU/SNDK separately from replay performance if product wants deeper Rule100 history/candidate-frame remediation.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_run_separate_strategy_data_eligibility_investigation_for_mu_sndk.`
- `DO_NOT_REDECIDE`: `Do not make dashboard replay watchlist-only; no provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now reuses a wider ready in-session daily replay for a shorter selected horizon when the cached context is a proven superset, instead of immediately rebuilding the transitional replay source.`
- `PM_DELTA`: `A user switching from Max to 1Y should no longer pay another PIT replay build when the Max daily replay already contains the 1Y dates and identity is unchanged.`
- `PERFORMANCE_DELTA`: `_ensure_daily_portfolio_replay_context(...) checks `_valid_cached_ytd_replay_context(...)` before entering the Building daily portfolio replay source path.`
- `FAIL_CLOSED_DELTA`: `Reuse requires matching method/cap/controls/signed assets/sampling/data signature after excluding replay_dates and actual requested-date rows in replay_df; missing rows clear replay/YTD cache rather than carrying stale evidence.`
- `TEST_DELTA`: `Scoped compile PASS; targeted superset-cache regressions PASS with 3 tests; focused Portfolio/YTD dashboard file PASS with 56 tests; optimizer/replay coverage PASS with 50 tests.`
- `OPEN_DECISION`: `Backend producers should still emit dashboard_cache_signature for production saved-artifact UI hits; accepting durable saved-artifact supersets for shorter windows remains a separate explicit policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_and_saved_artifact_superset_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Max Replay Timeline Sampling Fix

- `SYSTEM_DELTA`: `Strategy Replay max-window timeline sampling now normalizes grouped weekly keep-dates through the pandas Series .dt accessor, preventing the Portfolio page AttributeError on long replay windows.`
- `PM_DELTA`: `Selecting Max can render the display-sampled timeline without breaking the single daily replay source used by allocation and Portfolio Performance.`
- `FAIL_CLOSED_DELTA`: `Timeline sampling remains display-only from daily replay rows and cannot become a second replay request or Portfolio Performance source.`
- `TEST_DELTA`: `Scoped compile PASS; targeted max-window sampler regression PASS with 2 tests; focused Portfolio/YTD dashboard file PASS with 53 tests.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Replay Selection Identity Hardening

- `SYSTEM_DELTA`: `Portfolio & Allocation now uses explicit signed PortfolioReplaySelection state for replay asset identity instead of hidden optimizer_universe session state; signatures include typed assets and selected price content hash.`
- `PM_DELTA`: `A skipped, failed, or stale optimizer-control render can no longer silently drive a coherent replay for the first 10 price columns or an old universe.`
- `FAIL_CLOSED_DELTA`: `Missing, stale, mismatched, or unavailable selection returns portfolio_replay_selection_unavailable and clears replay/YTD caches.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay-selection/advisory regressions PASS with 6 tests; focused optimizer-selection AppTests PASS with 6 tests.`
- `OPEN_DECISION`: `Transitional dashboard aux event/decision loading remains a backend producer follow-up tied to dashboard_cache_signature emission.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_for_aux_rows.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Single-Source Replay Page

- `SYSTEM_DELTA`: `Portfolio & Allocation now coordinates one daily replay context before rendering allocation, performance, timeline, ENTER/EXIT events, latest buys/sells, and decision log surfaces.`
- `PM_DELTA`: `The page no longer presents optimizer fallback allocation/performance as if it belongs to the replay result; visible allocation and performance are both daily replay evidence.`
- `FAIL_CLOSED_DELTA`: `If daily replay is unavailable, Portfolio Performance renders unavailable instead of falling back to optimizer weights/local-live/equal-weight price paths.`
- `UI_DELTA`: `Duplicate Trade Event Log table is removed; ENTER/EXIT Events remains the event visualization, and Latest Buys/Sells is a filtered view of Buy/Sell Decision Log rows.`
- `TEST_DELTA`: `Scoped compile PASS; focused Portfolio/replay/optimizer suite PASS with 178 tests; context build/validation PASS.`
- `OPEN_DECISION`: `SAW reviewer gate remains pending for implementation closure; backend dashboard_cache_signature emission remains a separate coordination follow-up.`
- `RECOMMENDED_NEXT_STEP`: `run_saw_reviewer_gate_or_hold_for_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

- `SYSTEM_DELTA`: `Saved-artifact replay context construction now preserves artifact event/decision surfaces exactly; valid empty saved artifact aux rows stay empty instead of being filled from separately loaded dashboard frames.`
- `PM_DELTA`: `When Portfolio & Allocation says replay source is saved artifact, replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log rows are all from the saved artifact rather than a hidden mixed source.`
- `FAIL_CLOSED_DELTA`: `A saved artifact with daily portfolio rows but no event/decision rows renders empty event/decision surfaces instead of silently borrowing fallback rows.`
- `TEST_DELTA`: `Scoped compile PASS; focused saved-artifact regression PASS; focused frontend suite PASS with 106 tests; SAW Implementer and Reviewer A/B/C PASS.`
- `SAW_DELTA`: `Frontend/UI saved replay source-selector report is now discoverable at docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Backend Replay Reader Identity Hardening

- `SYSTEM_DELTA`: `Saved selected-method replay manifests now reject blank top-level run_id, source_id, and method_id before optional expected-ID checks or parquet/manifest equality can validate a bundle.`
- `PM_DELTA`: `A saved replay artifact can no longer be treated as valid just because both manifest and parquet carry the same blank identity while the UI/backend caller omits expected run/source ids.`
- `FAIL_CLOSED_DELTA`: `Blank identity fails closed with manifest_identity_blank:<field> and returns unavailable empty replay output.`
- `TEST_DELTA`: `Scoped compile PASS; targeted blank manifest+parquet identity regression PASS with 3 tests; focused backend replay suite PASS with 79 tests.`
- `SAW_DELTA`: `Backend identity hardening SAW report is published at docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md.`
- `OPEN_DECISION`: `Backend artifact producers should still emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Frontend/UI Saved Replay Source Selector

- `SYSTEM_DELTA`: `Portfolio & Allocation now builds a pure DashboardReplayRequest, prefers a backend-valid saved replay artifact only when the dashboard cache signature also matches, and otherwise uses an explicitly labeled transitional backend build only when fallback is allowed.`
- `PM_DELTA`: `YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log now come from one DashboardReplayContext selected by saved-artifact vs transitional-build source mode.`
- `FAIL_CLOSED_DELTA`: `Unavailable, stale, mismatched, or over-budget saved artifacts clear replay/YTD session state when fallback is disabled and cannot reuse prior latest weights.`
- `TEST_DELTA`: `Scoped compile PASS; requested frontend suite PASS with 105 tests; executable saved-artifact context test PASS.`
- `OPEN_DECISION`: `Backend artifact producers should emit dashboard_cache_signature for production saved-artifact UI hits; until then dashboard falls back to labeled transitional build when allowed.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Saved Replay Artifact Reader + Budget

- `SYSTEM_DELTA`: `Backend selected-method replay can now read saved replay-output parquet+manifest bundles only when run/source/method, controls, date window, input signatures, source-file signatures, schema, row/status counts, and timing match the requested context.`
- `PERFORMANCE_DELTA`: `ReplayBudgetPolicy now makes cold-start seconds, rerun/cache seconds, max rows, max dates, and max elapsed ms explicit for saved reads and budget-wrapped builds.`
- `FAIL_CLOSED_DELTA`: `Invalid, stale, mismatched, or over-budget artifact reads/builds return unavailable typed results with empty replay output; prior weights are not stale-carried forward.`
- `INTEGRITY_DELTA`: `DataFrame controls now include content hashes, parquet rows require exact non-null identity fields, and malformed timing fails closed.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay suites PASS with 76 tests and durations under budget.`
- `OPEN_DECISION`: `Frontend/UI can separately choose when to consume the saved reader; this backend slice does not rewire dashboard.py.`
- `RECOMMENDED_NEXT_STEP`: `coordinate_frontend_saved_reader_consumption_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim is authorized.`

## Latest Addendum - Overlay Overlap Anchor Fix

- `SYSTEM_DELTA`: `Scaled live overlays now require same-ticker overlap; unanchored selected-price or benchmark live rows are unavailable/dropped instead of stitched into current evidence.`
- `PM_DELTA`: `A stale local asset ending in February can no longer be bridged to fresh May live data without a same-ticker anchor date.`
- `TEST_DELTA`: `Scoped compile PASS; affected stale-data suite PASS with 112 tests after SAW rerun reconciliation.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C all returned PASS; SAW report is PASS.`
- `OPEN_DECISION`: `Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

- `SYSTEM_DELTA`: `Endpoint freshness now has a reusable PriceEndpointFreshness snapshot computed once per loaded prices_wide signature and reused across Portfolio YTD, optimizer selected-price prep/default ordering, and optimizer universe eligibility.`
- `PERFORMANCE_DELTA`: `Actual local (2857, 2000) matrix: snapshot 0.2966s vs legacy loop 0.9555s, exact endpoint match, and downstream 50 lookup reuse 0.001531s.`
- `RECONCILIATION_DELTA`: `Reviewer High findings were patched: weighted YTD now rejects partial live provider frames missing positive-weight assets, replay-derived YTD weights are signature-bound, and cached full replay/YTD contexts are signature-bound before chart reuse.`
- `PM_DELTA`: `The stale-data fail-closed layer keeps its correctness semantics without paying repeated multi-path full-matrix freshness scans on Streamlit reruns.`
- `TEST_DELTA`: `Focused data-orchestrator/optimizer/universe/dashboard suite PASS, 113 tests; scoped compile PASS.`
- `OPEN_DECISION`: `Complete targeted Reviewer A/B rechecks for this performance slice, then hold or proceed to saved replay artifact-reader/performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `finish_targeted_rechecks_for_endpoint_cache_then_hold_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `Do not relax fail-closed stale asset behavior, do not reintroduce shared-date proof as per-asset coverage, and do not add provider ingestion, canonical writes, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now treats freshness per asset endpoint rather than shared matrix date across benchmark YTD, portfolio YTD, optimizer price prep/order, and universe eligibility; scaled live overlays require same-ticker overlap.`
- `CONTRACT_DELTA`: `Endpoint/tolerance semantics are centralized in core.data_orchestrator via price_column_latest_date(...) and price_endpoint_is_fresh(...); portfolio_universe passes OptimizerUniversePolicy.max_endpoint_staleness_days instead of reimplementing helpers.`
- `PM_DELTA`: `Stale partial market data no longer appears as current evidence; stale weighted legs fail closed and stale selected assets are dropped/excluded with diagnostics.`
- `TEST_DELTA`: `Affected stale-data suite PASS with 112 tests after SAW rerun reconciliation; broader affected dashboard/replay suite PASS with 171 tests; scoped compile PASS.`
- `SAW_DELTA`: `Independent SAW rerun completed: Implementer and Reviewer A/B/C all returned PASS with no in-scope Critical/High findings.`
- `OPEN_DECISION`: `Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.`

## Latest Addendum - Dashboard Backend Bundle Integration Verification

- `SYSTEM_DELTA`: `Dashboard selected-method replay now consumes the backend build_selected_method_replay(...) bundle through _build_dashboard_strategy_replay_context(...), with a per-date r3000_pit input_loader instead of a dashboard-local direct build_strategy_replay(...) path.`
- `TEST_DELTA`: `Focused replay/dashboard suite PASS; scoped compile PASS; full pytest PASS; Streamlit readiness smoke PASS on http://127.0.0.1:8520/portfolio-and-allocation with HTTP 200.`
- `PM_DELTA`: `The previously open dashboard backend-bundle consumption risk is closed for the transitional build path; saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.`
- `OPEN_DECISION`: `Hold, or separately approve saved artifact-reader consumption plus performance-budget enforcement.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `This verification does not authorize provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Replay Coverage Contract Audit Fix

- `SYSTEM_DELTA`: `The v6 selected-method replay coverage contract audit BLOCK findings are fixed: coverage_segments metadata, specific input_unavailable reasons, uncovered-date batch emission, duplicate-test cleanup, next-return performance alignment, and covered/unavailable perf hardening are implemented.`
- `PERFORMANCE_DELTA`: `Uncovered replay dates now batch cash-closed rows before performance attachment; row-heavy no_priced_members windows use fast explicit-row emission; tiny PIT replay frames use direct return lookup; inverse-volatility skips SLSQP when the closed-form target already satisfies max_weight.`
- `TEST_DELTA`: `Focused replay coverage PASS with 11 tests; durations show row-heavy no_priced_members daily-scale 1.21s under the 10s budget, CASH-only daily-scale 0.30s, and 4-asset 5Y 1.20s under the 5s budget; affected replay/optimizer PASS with 68 tests; context bootstrap/hygiene PASS; full pytest PASS.`
- `BOOTSTRAP_DELTA`: `scripts/build_context_packet.py now discovers current truth surfaces and selects a complete New Context Packet from planner_packet_current.md before older handovers, so docs/context/current_context.* no longer validates while pointing at the Rule100/YTD packet.`
- `SAW_DELTA`: `Formal SAW Implementer and Reviewer A/B/C rechecks completed after resume and all passed; SAW report is PASS.`
- `PM_DELTA`: `The daily-scale replay audit path is now genuinely faster rather than only less tightly tested, and unavailable coverage reasons remain planner-readable.`
- `OPEN_DECISION`: `Dashboard backend-bundle integration/runtime smoke is now verified; hold or approve the saved artifact-reader/performance-budget follow-up.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `This audit fix does not authorize provider ingestion, live trading, broker automation, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims.`

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

- `SYSTEM_DELTA`: `Backend build_selected_method_replay(...) and dashboard DashboardReplayContext now provide focused tested selected-method replay evidence for replay rows, latest snapshot, YTD weight preference, ENTER/EXIT annotations, and Buy/Sell audit rows.`
- `PM_DELTA`: `The replay architecture has moved from docs-only invariant to a bounded implemented source path with durable saved replay-output artifact/run id support, and the dashboard transitional build now consumes the backend bundle end to end.`
- `ARTIFACT_DELTA`: `write_selected_method_replay_artifact_atomic(...) writes a display-only replay-output parquet plus manifest with run_id, source_id, method_id, input signatures, date window, row/status counts, and timing under data/runtime_cache/strategy_replay.`
- `ATOMICITY_DELTA`: `The selected-method replay artifact writer stages parquet and manifest first, then promotes with rollback so manifest failure after parquet promotion does not leave orphan saved evidence.`
- `TIMEFRAME_PIT_RULE`: `Portfolio Performance display horizons may be YTD/1Y/3Y/5Y/Max, but replay evidence must load each date as PIT input with end_date=as_of_date and universe_mode=r3000_pit; failed dates must be cash_closed/unavailable, not stale carry-forward.`
- `LATEST_TRADES_UX`: `Buy/Sell Decision Log defaults to latest trades first, renders before heavy replay output, and remains collapsed replay-audit-only context, not live orders or trade signals.`
- `PERFORMANCE_DELTA`: `Replay rows carry asset_return, return_contribution, portfolio_return, and portfolio_equity so YTD/performance can be derived from replay output instead of optimizer session weights.`
- `ROLLBACK_NOTE`: `If the dashboard context regresses, disable the replay-context/YTD preference and return to legacy optimizer weights; do not rewrite canonical market data, lifecycle ledgers, or frozen audit history.`
- `OPEN_DECISION`: `Hold, or separately approve saved artifact-reader consumption plus performance-budget enforcement.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`
- `DO_NOT_REDECIDE`: `Do not treat focused backend/dashboard tests as strategy promotion, live trading, alerts, rankings, recommendations, or autonomous allocation.`

## Latest Addendum - Frontend/UI Shared Replay Bundle

- `SYSTEM_DELTA`: `Portfolio & Allocation Strategy Replay now has a dashboard-level selected-method replay context feeding replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell audit rows.`
- `UI_DELTA`: `The Strategy Replay surface no longer calls read_lifecycle_log() or reads data/portfolio_lifecycle_buy_sell_log.jsonl directly; both are supplied through DashboardReplayContext.`
- `YTD_DELTA`: `Portfolio Performance primes the latest selected-method replay snapshot before YTD and prefers those weights before legacy optimizer_weights fallback.`
- `BOUNDARY`: `This is a minimal frontend adapter around the current backend replay API; no saved replay-output artifact, provider ingestion, canonical write, alert, broker behavior, ranking, scoring, or recommendation was added.`
- `OPEN_DECISION`: `Backend integration still needs a durable replay-output artifact/run id for the full ultra-modular replay architecture.`
- `RECOMMENDED_NEXT_STEP`: `backend_replay_output_artifact_or_hold.`
- `DO_NOT_REDECIDE`: `Do not treat Buy/Sell audit rows as live orders or trade signals, and do not add broker/live trading, alerts, rankings, recommendations, provider ingestion, or unchecked optimizer behavior.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

- `SYSTEM_DELTA`: `Docs/Ops has hardened the next milestone contract: for any selected method, one replay run/source must feed YTD, current allocation/latest snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence.`
- `PM_DELTA`: `The product goal is a human-reviewed AI research evidence loop with one replay source of truth, not multiple UI bridges that appear consistent while reading different artifacts.`
- `ARCHITECTURE_GOAL`: `selected-method adapter -> one replay run -> daily portfolio output -> event/annotation output -> YTD/performance -> decision log -> saved evidence artifact.`
- `TRANSITIONAL_BRIDGE_BOUNDARY`: `Temporary bridges may keep visible UI usable during migration, but they must be labeled transitional, bounded to a source, non-canonical, and unable to claim final replay evidence.`
- `GUARDRAILS`: `No future-data leakage, no stale-data carry-forward, no fake improvements, no overfitting, no broker/live trading, no alerts/rankings/recommendations/candidate scoring/autonomous allocation.`
- `DONE_GATE`: `PASS requires shared replay source, selected-method adapters, shared YTD/performance, shared latest allocation snapshot, shared annotation source, shared decision-log source, saved evidence artifact, and explicit performance budget.`
- `OPEN_DECISION`: `Approve the first implementation slice for the single selected-method replay source, or hold.`
- `RECOMMENDED_NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice_with_single_selected_method_replay_source.`
- `DO_NOT_REDECIDE`: `Do not treat current UI/YTD bridges, frozen Rule100 history, compact Buy/Sell tape, or separate overlays as the canonical selected-method replay source.`

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

- `SYSTEM_DELTA`: `The focused visible Portfolio & Allocation patch is runtime-audited: default method is Rule of 100, QQQ is visible beside SPY, and the buy/sell decision log is visible before heavy replay output.`
- `UI_DELTA`: `Browser DOM on http://localhost:8509/ shows selected Rule of 100, max_weight=0.35, SPY +11.07%, QQQ +15.50%, and Buy/Sell Decision Log (29 trades, replay audit only) with BUY 16 / SELL 13.`
- `DATA_DELTA`: `QQQ benchmark display is sourced through local+live_overlay and is no longer dropped when SPY has fresher local data.`
- `OPEN_DECISION`: `Start the first urgent ultra-modular replay architecture slice, or hold.`
- `RECOMMENDED_NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice.`
- `DO_NOT_REDECIDE`: `Do not reinterpret the buy/sell replay tape as live orders/trade signals, and do not add broker/live trading, alerts, rankings, recommendations, provider ingestion, or unchecked optimizer behavior.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

- `SYSTEM_DELTA`: `A separate urgent ultra-modular replay architecture milestone is now queued after the current visible Portfolio & Allocation QQQ/YTD/default-method patch.`
- `PM_DELTA`: `The next architecture direction is an endless AI auto-research loop that proposes, replays, annotates, compares, and saves evidence for human review; it is not an unchecked optimizer or autonomous trading loop.`
- `SCOPE_SPLIT`: `Current patch = focused UI/YTD visibility fixes. Larger milestone = one replay engine, one strategy plug-in contract, one daily portfolio output format, one event/annotation format, one YTD/performance path, and one saved evidence artifact.`
- `GUARDRAILS`: `No future-data leakage, stale inputs fail closed, overfitting controls require same-window/same-cost/same-engine baseline deltas, fake improvements are rejected without replayable evidence, and no broker/live trading/alerts/rankings/recommendations are authorized.`
- `ACCEPTANCE_TESTS`: `Rule100 visible sizing parity and QQQ/YTD stale-overlay fixes remain acceptance tests before the modular replay milestone starts.`
- `OPEN_DECISION`: `After QQQ/default-method visible fixes are manually audited, approve the first ultra-modular replay architecture slice or hold.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_qqq_ytd_and_default_method_visible_fixes_then_start_urgent_ultra_modular_replay_architecture.`
- `DO_NOT_REDECIDE`: `Do not widen the current focused UI/YTD patch into code architecture work before visible fixes are verified; do not add broker/live trading, provider ingestion, ranking/scoring, alerts, or autonomous optimizer behavior.`

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- `SYSTEM_DELTA`: `Rule of 100 visible allocation and Strategy Replay now use controls.max_weight as both the per-name budget and single-name cap through rule100_config_from_max_weight(...).`
- `DATA_DELTA`: `Frozen Rule100 audit/history defaults remain unchanged; rule100_softmax_v1_history.csv was not rewritten as a 35% UI-policy artifact.`
- `UI_DELTA`: `Direct Rule of 100 UI allocation now agrees with Strategy Replay; at max_weight=35%, two equal eligible names target 35%/35% with 30% cash.`
- `YTD_DELTA`: `Benchmark YTD fallback is stale-aware per ticker: fresh local SPY can remain local while stale/missing QQQ attempts live overlay and is not forward-filled into a fresh curve if overlay fails.`
- `RUNTIME_DELTA`: `Dashboard YTD live fallback uses a bounded timeout, and AppTest route coverage caps replay dates for deterministic test runtime without changing production replay horizon.`
- `OPEN_DECISION`: `Hold, or separately approve a versioned/labeled Rule100 UI-policy history artifact if historical 35% target traces are required.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_rule100_visible_weights_and_qqq_ytd_then_hold_or_versioned_history_artifact.`
- `DO_NOT_REDECIDE`: `Do not rewrite frozen Rule100 history/audit artifacts, promote provider data to canonical market data, add ranking/scoring, alerts, broker behavior, live trading, or a new optimizer objective.`

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

- `SYSTEM_DELTA`: `Strategy Replay input caching now fails closed on r3000_pit membership and dashboard replay consumes per-date StrategyReplayInputs before generating target weights.`
- `DATA_DELTA`: `Display-only replay artifacts are confined to data/runtime_cache/strategy_replay; custom cache_dir values under data/processed are rejected.`
- `UI_DELTA`: `Portfolio & Allocation Strategy Replay no longer passes a raw prices_wide replay matrix; it loads one PIT input slice per replay date and calls build_strategy_replay(..., prices=replay_inputs).`
- `RECONCILIATION_DELTA`: `SAW Medium findings were reconciled by preserving empty/failed replay dates as explicit cash_closed rows.`
- `OPEN_DECISION`: `Hold, or separately approve a longer replay output artifact/evidence window.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_collect_strategy_replay_multi_date_output_evidence.`
- `DO_NOT_REDECIDE`: `Do not treat replay input artifacts as target-weight output, canonical market data, provider ingestion, ranking/scoring, alerting, broker behavior, live trading, or a new optimizer objective.`

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

- `SYSTEM_DELTA`: `Rule100 softmax v1.1 research audit now matches its comparison/summary-only artifact contract; stale history is retired instead of treated as current.`
- `DATA_DELTA`: `data/processed/rule100_softmax_v1_1_history.csv is absent; stale bytes were moved to data/processed/rule100_softmax_v1_1_history.retired.csv.`
- `SCORING_DELTA`: `v1.1 factor coverage counts approved factor groups, not raw columns, and missing factor strength shrinks toward neutral 0.50 by coverage.`
- `TEST_DELTA`: `tests/test_policy_target_timeline_apptest.py now uses AppTest.from_file("dashboard.py") and proves TSM 2026-05-11 renders target 0%, event weight 10%, cash 80%.`
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and SAW Implementer/Reviewer A/B/C passes completed.`
- `OPEN_DECISION`: `Hold, or separately approve a longer v1.1 promotion evidence window.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_collect_v1_1_multi_date_shadow_evidence.`
- `DO_NOT_REDECIDE`: `Do not promote v1.1 to runtime, recreate v1.1 history, mutate the lifecycle log, or add broker/alert/ranking/scoring behavior.`

## Latest Addendum - Rule of 100 Method Label

- `SYSTEM_DELTA`: `Position Lifecycle Replay history now has an additive Rule100 softmax v1 target-weight overlay instead of showing only stale v0 event weights.`
- `DATA_DELTA`: `data/processed/rule100_softmax_v1_history.csv records event_weight, softmax_v1_target_weight, softmax_v1_cash_residual, eligibility reason, and score by PIT date/ticker.`
- `UI_DELTA`: `Transaction Log labels the immutable ledger weight as Event Weight and the derived v1 sizing as Softmax v1 Target / Softmax v1 Cash.`
- `CURRENT_STATE_DELTA`: `On 2026-05-11, TSM remains event weight 10% but softmax v1 target is 0%, with AMAT 10%, LRCX 10%, and CASH 80%.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if visible >10% single-name sizing is required.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_lifecycle_history_overlay_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `Do not overwrite the v0 lifecycle event log or turn Kelly into a second stack.`

## Previous Addendum - Rule of 100 Method Label

- `SYSTEM_DELTA`: `The Portfolio Optimizer method registry now exposes Rule of 100 as a user-facing lifecycle allocation mode.`
- `PM_DELTA`: `Users can choose the concrete Rule100 lifecycle policy from the existing Method dropdown without introducing a generic strategy framework.`
- `UI_DELTA`: `Rule of 100 now renders PIT softmax v1 target weights for eligible lifecycle holds, stores source=rule100_softmax_v1, and still bypasses optimizer execution.`
- `CURRENT_STATE_DELTA`: `Current softmax v1 target is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%; TSM is excluded from sizing because it is tighten_below_hold_threshold.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if visible >10% single-name sizing is required.`
- `RECOMMENDED_NEXT_STEP`: `review_rule100_softmax_v1_live_weights_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, live trading, or Phase 54 sleeve reopen.`

## Latest Addendum - Rule100 Softmax v1 Audit

- `SYSTEM_DELTA`: `Rule100 now has a dedicated softmax v1 sizing helper module plus a shared replay/audit harness; Kelly is comparator-only.`
- `PM_DELTA`: `The same PIT lifecycle frame can now emit a softmax-first comparison artifact set without multiplying full solution stacks.`
- `DATA_DELTA`: `Artifacts are versioned under data/processed/rule100_softmax_v1* and include summary, comparison, sample, and cash outputs.`
- `UI_DELTA`: `The explicit Rule of 100 UI path now computes softmax v1 targets at render time from the PIT candidate frame instead of replay last_weight.`
- `OPEN_DECISION`: `Hold, or separately approve richer continuous score inputs if v1 should produce more visible concentration than 10%/10% in the current equal-score state.`
- `RECOMMENDED_NEXT_STEP`: `review_rule100_softmax_v1_live_weights_then_decide_score_richness.`
- `DO_NOT_REDECIDE`: `Do not turn Kelly into a second full stack or change lifecycle replay log semantics.`

## Latest Addendum - Rule100 Lifecycle Policy v0

- `SYSTEM_DELTA`: `The concrete PIT lifecycle strategy is now Rule100 Lifecycle Policy v0; no generic replay/audit framework was introduced.`
- `PM_DELTA`: `The replay now distinguishes BUY, HOLD, TRIM, TIGHTEN, EXIT, and NO_ACTION in the audit tape while preserving dashboard-compatible ENTER/EXIT runtime events.`
- `POLICY_DELTA`: `Rule100State wraps proxy demand/supply/pricing/margin with explicit provenance; entry requires 3/4 factors, technical entry zone, and multi-observation confirmation; hold tolerates 2/4; trim/tighten are audit-only; full exit requires >20% hard stop or confirmed trend veto.`
- `DATA_DELTA`: `Promoted runtime lifecycle log now has 29 events vs the 33-event baseline; open holds remain AMAT/LRCX/TSM.`
- `AUDIT_DELTA`: `V0 decision tape has BUY=16, SELL=13, HOLD=739, TRIM=55, TIGHTEN=257, NO_ACTION=4344, no <=5-day round trips, and trade_event_delta=-4 vs baseline.`
- `OPEN_DECISION`: `Audit whether TRIM/TIGHTEN should later change weights, or hold v0 as audit-only.`
- `RECOMMENDED_NEXT_STEP`: `audit_rule100_v0_delta_then_decide_whether_trim_tighten_should_affect_weights.`
- `DO_NOT_REDECIDE`: `No generic strategy contract, provider ingestion, canonical writes, broker orders, alerts, ranking, scoring, dashboard recommendation labels, or Phase 54 Rule-of-100 sleeve reopen.`

## Latest Addendum - Lifecycle Decision Export

- `SYSTEM_DELTA`: `Lifecycle replay now exports a PIT-safe decision tape for audit before further Rule-of-100 lifecycle work.`
- `PM_DELTA`: `The system can inspect why it bought, sold, held, or did nothing on each ticker-date instead of judging only emitted ENTER/EXIT markers.`
- `DATA_DELTA`: `Export artifacts are data/portfolio_lifecycle_decision_log.jsonl, data/portfolio_lifecycle_buy_sell_log.jsonl, and docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json.`
- `AUDIT_DELTA`: `Current export has 5424 decision rows, 18 BUY, 15 SELL, open AMAT/LRCX/TSM, no <=5-day round trips, and audit flags for factor-deterioration holds and suppressed raw exits.`
- `CLOSURE_DELTA`: `Focused export tests and compile pass; independent SAW subagent ownership remains pending unless explicitly authorized.`
- `OPEN_DECISION`: `Audit the decision tape, then approve or revise the true Rule-of-100 lifecycle policy.`
- `RECOMMENDED_NEXT_STEP`: `audit_decision_tape_then_design_true_rule100_lifecycle_policy.`
- `DO_NOT_REDECIDE`: `BUY/SELL fields are replay-analysis labels only; no broker order, alert, ranking, scoring, provider ingestion, canonical write, or dashboard recommendation is authorized.`

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

- `SYSTEM_DELTA`: `Position Lifecycle Replay now uses max-10 10% ENTER weights, 3-day entry confirmation, 3-of-4 PIT lifecycle factor confirmation, 20-day minimum hold, 2-day exit confirmation, 20% hard-exit override, and 10-day post-exit cooldown.`
- `PM_DELTA`: `If replay is not sell-all, Portfolio & Allocation remains invested in current lifecycle holds; the final log is calmer and not 100% cash. Current open holds are AMAT, LRCX, and TSM at 10% each, with residual cash.`
- `DATA_DELTA`: `Pre-fix replay evidence had 103 events and 0.04 ENTER weights; drop-in evidence had 69 events and 0.10 weights; optimal evidence has 33 events, 0.10 weights, and no <=5-day churn round trips.`
- `UI_DELTA`: `Port 8509 smoke shows AMAT/LRCX/TSM/CASH, does not show 100% cash, and restores SPY/QQQ YTD traces through local benchmark fallback when live yfinance is rate-limited.`
- `YTD_FIX_DELTA`: `The visible +7645112.18% portfolio return was caused by swapped prices/returns in core.data_orchestrator. UnifiedDataPackage.prices now holds TRI levels, returns holds daily returns, and Portfolio YTD uses local TRI history first. Port 8509 smoke now shows Portfolio +14.25%.`
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and headless browser smoke passed; independent SAW subagent ownership is recorded as pending/BLOCK unless the user explicitly authorizes a subagent rerun.`
- `OPEN_DECISION`: `Hold, or separately approve a broader lifecycle execution-ledger/accounting model.`
- `RECOMMENDED_NEXT_STEP`: `manual_audit_portfolio_allocation_on_8509_then_hold_or_lifecycle_ledger_policy.`
- `DO_NOT_REDECIDE`: `Do not reopen the rejected Phase 54 Rule-of-100 sleeve, add ranking/scoring, provider ingestion, canonical writes, broker calls, alerts, new optimizer objectives, conviction mode, or Black-Litterman.`

## Latest Addendum - Pinned Strategy Universe Hardening

- `SYSTEM_DELTA`: `Thesis tickers are explicitly pinned into feature generation via manifest. Feature store unions pinned permnos after yearly_top_n. PIT replay defaults to scanner ∪ pinned. Shared eligibility gate used by both replay and diagnostics. Loader raises on missing/broken manifest.`
- `PM_DELTA`: `Strategy-universe inclusion is now explicit, auditable, and impossible to silently drop. 103 lifecycle events across 12 tickers. NVDA explicitly FAILED_GATE.`
- `OPEN_DECISION`: `Evaluate NVDA fundamental gate or proceed to Stream 2 strategy review.`
- `RECOMMENDED_NEXT_STEP`: `evaluate_nvda_fundamental_gate_or_stream2_strategy_review_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, optimizer objective change, or scanner rule change is authorized.`

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

- `SYSTEM_DELTA`: `Portfolio & Allocation now reconstructs current open holdings from PIT-safe Position Lifecycle Replay state before declaring sell-all cash.`
- `PM_DELTA`: `If replay has open ENTER positions without later EXIT events, the current allocation shows held names plus residual cash rather than 100% cash.`
- `DATA_DELTA`: `Lifecycle JSONL is read locally; future-dated replay rows are ignored; JSON position memory is fallback only when lifecycle evidence is empty.`
- `UI_DELTA`: `Open lifecycle holdings enter the universe as included_current_hold and render as Allocation (Lifecycle Holds) when no fresh PIT ENTER candidate exists.`
- `CLOSURE_DELTA`: `Focused compile, 58-test portfolio/lifecycle suite, full pytest, browser smoke, context validation, SAW report validation, closure packet validation, and SE evidence validation passed; latest local replay check is not sell-all and has open AMAT, AVGO, and TSLA positions.`
- `OPEN_DECISION`: `Hold or separately approve a broader lifecycle transaction model / current-position accounting policy.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_review_lifecycle_position_accounting_policy.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, broker call, alert, ranking, scoring, new optimizer objective, conviction mode, or Black-Litterman is authorized.`

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- `SYSTEM_DELTA`: `Dashboard unified parquet data load is now wrapped in st.cache_resource and keyed by processed/static parquet file signatures.`
- `PM_DELTA`: `Normal Streamlit widget reruns should no longer pay the verified ~8s DuckDB/parquet wide-frame load when source data has not changed.`
- `DATA_DELTA`: `Cache invalidation tracks source parquet resolved path, mtime_ns, and size for price, patch, macro/liquidity, ticker, fundamentals, calendar, and sector-map inputs.`
- `CLOSURE_DELTA`: `Focused compile/tests, portfolio regressions, full pytest, Streamlit HTTP smoke, context validation, and independent SAW Implementer/Reviewer A/B/C passes completed.`
- `OPEN_DECISION`: `Hold or separately measure the alpha-engine daily loop and scanner financial-statement cache follow-ups.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_alpha_backtest_runtime_or_scanner_financial_cache.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, optimizer objective change, or scanner rule change is authorized.`

## Latest Addendum - Dashboard Scanner Testability Hardening

- `SYSTEM_DELTA`: `Dashboard scanner deterministic math now lives in strategies/scanner.py with focused boundary-value tests; dashboard.py preserves provider/cache/persistence ownership and delegates enrichment.`
- `PM_DELTA`: `Scanner labels and tactical fields are more regression-resistant without changing product semantics or authorizing new recommendations.`
- `TEST_DELTA`: `Scanner formula tests, strategy/config/ETL coverage, and the process guardrail passed in the focused suite.`
- `CLOSURE_DELTA`: `Focused compile, 49-test affected suite, full pytest, and SAW Reviewer C final recheck passed.`
- `OPEN_DECISION`: `Hold, run longer full regression, or continue the next review section.`
- `RECOMMENDED_NEXT_STEP`: `continue_review_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring policy change, alert, broker call, dashboard redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Dashboard Architecture Safety Slice

- `SYSTEM_DELTA`: `PID liveness probing is centralized in utils.process.pid_is_running; dashboard/updater/parameter-sweep/release-controller/phase16 wrappers delegate to it.`
- `PM_DELTA`: `The dashboard and runtime lock paths are safer on Windows without changing product behavior.`
- `UI_DELTA`: `dashboard.py now uses one modular-strategy matrix initializer, delegates portfolio price cleanup to core.data_orchestrator.clean_price_frame, and refuses to spawn a second backtest when a PID file points to a live process.`
- `CLOSURE_DELTA`: `Focused compile/tests and HTTP smoke passed; full pytest was attempted but timed out after 304 seconds, so closure relies on affected-suite evidence plus SAW review.`
- `OPEN_DECISION`: `Hold or continue to Section 2 Code Quality review.`
- `RECOMMENDED_NEXT_STEP`: `continue_code_quality_review_section_or_hold.`
- `DO_NOT_REDECIDE`: `No provider ingestion, canonical market-data write, strategy search, ranking, scoring, alert, broker call, dashboard content redesign, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- `SYSTEM_DELTA`: `/portfolio-and-allocation` optimizer rendering now has Streamlit AppTest coverage, UI-to-SLSQP bound coverage, display-only Parquet overlay cache, copy-safe overlay scaling cache, and cached optimizer reruns.`
- `PM_DELTA`: `The Portfolio & Allocation surface is more reliable and responsive without changing product semantics or allocation policy.`
- `DATA_DELTA`: `Recent close overlays are cached under data/runtime_cache/optimizer_live_overlay as display-only Parquet files with temp->replace writes; cold misses schedule background refresh and return local TRI prices.`
- `CLOSURE_DELTA`: `Implementation evidence and independent SAW rerun are PASS; Low runtime hygiene follow-ups are carried without blocking closure.`
- `OPEN_DECISION`: `Hold, measure next dashboard runtime bottleneck, or separately approve portfolio thesis-anchor policy planning.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck_or_approve_portfolio_thesis_anchor_policy_planning.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, lower-bound allocation policy, new optimizer objective, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Portfolio Data Boundary Refactor

- `SYSTEM_DELTA`: `Portfolio Optimizer selected-stock display freshness and strategy-metrics parsing are now data-orchestrator responsibilities rather than Streamlit view responsibilities.`
- `PM_DELTA`: `The product keeps the same Portfolio & Allocation behavior while reducing UI/provider coupling on the approved DASH-2 freshness path.`
- `DATA_DELTA`: `core/data_orchestrator.py owns close extraction, duplicate-safe local TRI overlay scaling/stitching, stale-while-revalidate display cache behavior, scheduler fail-soft handling, and data/backtest_results.json metrics parsing; views/optimizer_view.py no longer imports yfinance or parses that JSON file.`
- `CLOSURE_DELTA`: `SAW rerun is PASS after reconciling partial live overlay preservation, stale session-state clearing, duplicate anchor dates, stale cache semantics, and scheduler submit failure.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more hygiene, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `No canonical provider ingestion, market-data write, optimizer objective change, MU conviction, WATCH investability expansion, Black-Litterman, alert, broker call, ranking, scoring, or candidate-card dashboard merge is authorized.`

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- `SYSTEM_DELTA`: `Optimizer-core diagnostics are now implemented as a structured reporting layer without changing the approved objective or accepting lower-bound policy.`
- `PM_DELTA`: `The product can now explain infeasible caps, forced equal weight, SLSQP failures, active bounds, and fallback allocations without silently treating fallback as optimized output.`
- `CLOSURE_DELTA`: `SAW PASS after reconciling the data-integrity finding: non-finite diagnostic weights now fail closed as errors and cannot be reported as optimized.`
- `OPEN_DECISION`: `Approve PORTFOLIO_THESIS_ANCHOR_POLICY_PLANNING, request more diagnostics, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold.`
- `DO_NOT_REDECIDE`: `MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new optimizer objective, scanner rules, manual override, provider ingestion, broker calls, alerts, and replay behavior remain blocked.`

## Latest Addendum - Optimizer Core Policy Audit

- `SYSTEM_DELTA`: `Optimizer-core lower-bound/SLSQP policy is now separated from the universe-construction closure into its own audit artifacts.`
- `PM_DELTA`: `The quarantined diff is rejected as-is; the product can discuss optimizer constraints without silently accepting model math.`
- `OPEN_DECISION`: `Approve a future optimizer-core implementation round, request revisions, or hold.`
- `RECOMMENDED_NEXT_STEP`: `hold_optimizer_core_implementation_until_policy_approval.`
- `DO_NOT_REDECIDE`: `Universe eligibility, WATCH investability, MU conviction, Black-Litterman, scanner behavior, provider ingestion, broker calls, alerts, and new objectives remain blocked.`

## Latest Addendum - Portfolio Universe Closure Quarantine

- `SYSTEM_DELTA`: `Portfolio Universe Construction Fix is closed as PASS with optimizer-core lower-bound/SLSQP math quarantined out of scope.`
- `PM_DELTA`: `The allocation-universe patch remains mechanical: universe construction, eligibility, diagnostics, labels, tests, audit UI, and contract docs only.`
- `QUARANTINE_DELTA`: `Dirty strategies/optimizer.py lower-bound/SLSQP changes were saved to docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch and reverted from the active closure.`
- `OPEN_DECISION`: `Open OPTIMIZER_CORE_POLICY_AUDIT or hold; do not accept optimizer-core math changes without separate policy, tests, and SAW.`
- `RECOMMENDED_NEXT_STEP`: `open_optimizer_core_policy_audit_or_hold.`
- `DO_NOT_REDECIDE`: `No MU hard floor, conviction mode, WATCH investability, Black-Litterman, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective is authorized.`
- `PROVENANCE_ANCHOR`: `D-353 / Phase 64 provenance and validation gates remain closed; evidence anchor includes docs/phase_brief/phase64-brief.md and R64.1 dependency hygiene.`

## Latest Addendum - Portfolio Universe Construction Fix

- `PORTFOLIO_DELTA`: `Portfolio Optimizer defaults now come from build_optimizer_universe(...) rather than df_scan display order or selected_tickers[:20].`
- `ELIGIBILITY_DELTA`: `ENTER STRONG BUY and ENTER BUY are eligible; WATCH is research-only; EXIT/KILL/AVOID/IGNORE are excluded by default.`
- `DIAGNOSTIC_DELTA`: `Universe Audit now reports included/excluded rows, missing ticker mappings, local price-history failures, and max-weight feasibility or equal-weight-boundary risk.`
- `NO_CHANGE`: `No MU hard floor, Black-Litterman, conviction mode, thesis anchor sizing, manual override, scanner rewrite, provider ingestion, broker call, alert, or new objective was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` PASS; scoped compile PASS for `strategies/portfolio_universe.py`, `views/optimizer_view.py`, and `dashboard.py`; browser smoke PASS on port `8503`.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- `DASHBOARD_DELTA`: `Portfolio & Allocation now keeps Portfolio Optimizer top-level, renders YTD Performance below it, calculates portfolio YTD from current optimizer weights, and shows SPY/QQQ comparison metrics.`
- `DATA_DELTA`: `Selected stock and benchmark prices use an in-memory yfinance adjusted-close freshness overlay for runtime display only; no canonical provider ingestion or file write was added.`
- `NO_CHANGE`: `No broker call, alert, candidate ranking, candidate scoring, factor-scout integration, candidate-card merge, or canonical evidence change was added.`
- `EVIDENCE`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` PASS; `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` PASS; scoped compile PASS; browser check at `http://127.0.0.1:8502/portfolio-and-allocation` showed optimizer before YTD and prices through `2026-05-08`.

## Header

- `BRIDGE_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-bridge`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `D-353/R64.1/F/G0/G1/G2/G3/G4/G5/G6/G7/G7.1/G7.1A/G7.1B/G7.1C/G7.1D/G7.1E/G7.1F/G7.1G/G7.2/G7.3/G7.4/G8/G8.1/G8.1A/G8.1B-R/DASH-1 complete + G8.2 current`
- `STATUS`: `phase65-g8-2-system-scouted-candidate-card-current`
- `OWNER`: `PM / Architecture Office`

## Live Truth Now

- `SYSTEM_NOW`: `Quant has two candidate-card-only research objects: MU from human nomination and MSFT from the governed LOCAL_FACTOR_SCOUT output.`
- `ACTIVE_SCOPE`: `G8.2 is candidate-card-only Data + Docs/Ops work: one MSFT static card, manifest, policy, handover, focused tests, truth surfaces, and SAW.`
- `BLOCKED_SCOPE`: `New scout outputs, DELL/AMD/LRCX/ALB cards, rankings, scores, thesis validation, buy/sell/hold, buying range, dashboard merge, provider ingestion, alerts, and broker behavior remain blocked.`

## What Changed This Round

- `SYSTEM_DELTA`: `MSFT can now move from governed LOCAL_FACTOR_SCOUT intake to a structured candidate-card-only research object without becoming validated alpha.`
- `PRODUCT_DELTA`: `Terminal Zero now proves both intake-to-card paths: human-nominated MU and pipeline-scouted MSFT.`
- `DATA_DELTA`: `Added one static MSFT candidate card and manifest; no canonical market-data write or provider ingestion occurred.`
- `GOVERNANCE_DELTA`: `Candidate-card validation now rejects factor-score leakage and optional governance flags must remain true when present.`
- `DASHBOARD_DELTA`: `No dashboard runtime change. Existing MSFT dashboard rows are legacy runtime output, not the G8.2 card.`
- `NO_CHANGE`: `No new scout output, no score, no rank, no actionability, no buying range, no alert, no broker call, no provider call, no dashboard merge, and no cards for user-seeded tickers.`

## PM / Product Delta

- `STRONGER_NOW`: `The discovery proof is more complete because a system-scouted intake item can become a governed research object.`
- `WEAKER_NOW`: `Dashboard semantics are still split: legacy runtime rows can show action-shaped labels while candidate cards remain file-backed status objects only.`
- `STILL_UNKNOWN`: `Whether the next move should be G9 market-behavior signal card, G8.3 user-seeded candidate card, a dashboard card reader, or hold.`

## Planner Bridge

- `OPEN_DECISION`: `Approve G9 one market-behavior signal card, approve G8.3 one user-seeded candidate card, approve dashboard card reader/status shell, or hold.`
- `RECOMMENDED_NEXT_STEP`: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold.`
- `WHY_THIS_NEXT`: `G8.2 completed the system-scouted intake-to-card proof; the next safe choices either add one evidence signal, test the user-seeded card path, or expose cards as status-only dashboard objects.`
- `NOT_RECOMMENDED_NEXT`: `Do not start ranking, scoring, buying range, provider ingestion, alerts, broker paths, or merge MSFT into legacy dashboard action labels.`

## Locked Boundaries

- `DO_NOT_REDECIDE`:
  - `MSFT is the only G8.2 ticker because it is the sole governed LOCAL_FACTOR_SCOUT output.`
  - `MU and MSFT are the only candidate cards after G8.2.`
  - `Candidate-card-only does not mean validated, actionable, ranked, scored, or recommended.`
  - `The existing dashboard MSFT row at runtime is not the G8.2 candidate card.`
  - `Future dashboard integration must be status-only unless separately approved.`
  - `No live trading, broker automation, alerting, ranking, scoring, recommendation, or provider ingestion is authorized.`

## Evidence Used

- `opportunity_engine/candidate_card_schema.py`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- `data/discovery/local_factor_scout_output_tiny_v0.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`

## Open Risks

- `Inherited dirty dashboard runtime worktree remains visible in git status.`
- `Legacy dashboard rows still use action-shaped labels that are separate from candidate cards.`
- `Factor model validation remains future debt before predictive or ranked use.`
- `GodView provider, options-license, ownership, insider, and market-behavior gaps remain open.`

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

- `SYSTEM_DELTA`: `Portfolio & Allocation now stores explicit allocation state for optimizer output, cash-only fallback, current-hold replay, and Rule of 100 replay instead of inferring state only from legacy session keys.`
- `PM_DELTA`: `The visible Portfolio page stays the default route while the explicit Portfolio & Allocation url path resolves cleanly and replay output is labeled as replay output, not optimizer output.`
- `DATA_DELTA`: `portfolio_allocation_state now carries mode/source/weights/cash_only/latest_price_date, with legacy mirrors retained for compatibility and a separate current-hold replay payload when replay is active.`
- `OPEN_DECISION`: `Hold, or continue the next dashboard-runtime hygiene slice.`
- `RECOMMENDED_NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck.`
- `DO_NOT_REDECIDE`: `No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, or live trading is authorized.`
