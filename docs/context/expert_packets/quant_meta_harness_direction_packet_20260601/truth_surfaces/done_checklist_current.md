# Done Checklist - Phase 65 G8.2 System-Scouted Candidate Card

Status: Current with Portfolio Universe Construction PASS and optimizer-core quarantine complete
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, thesis validation, or scope widening by itself.
Purpose: define machine-checkable done criteria for current Phase 65 portfolio universe and candidate-card work.

## Latest Addendum - Governed Data Source Provenance Intake

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`.
- [x] ScopeID recorded: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`.
- [x] Source-provenance intake packet exists at `docs/architecture/governed_data_source_provenance_intake_20260528.md`.
- [x] StartingVerdict recorded as `BLOCK`.
- [x] Current state recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- [x] Packet states it does not close data readiness and does not authorize generation yet.
- [x] Correct sequence recorded: approve source provenance first; then bounded offline regeneration; then manifests/hashes; then strict data-readiness validation; then strict `--require-github`; then regenerate runtime boot status only after strict PASS.
- [x] Intake lines cover prices, ticker/security master, WRDS/R3000 membership, and Rule100 history source/generator.
- [x] Each line requires source location, owner/approval, date/as-of coverage, license/access note, schema, generator command, output path, manifest path, SHA256 policy, validation command, and rollback/removal rule.
- [x] Known static generator state is recorded without approving generation.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no data/processed generation from incomplete provenance; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.
- [ ] Approved source provenance exists for all lines. BLOCKED until user/source authorization.
- [ ] Bounded offline regeneration is approved. BLOCKED and not authorized by this packet.
- [ ] Any required data artifact is generated or intaken. BLOCKED and not approved by this round.
- [ ] Strict data readiness is proven as passing. BLOCKED.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`.
- [x] ScopeID recorded: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`.
- [x] Source-acquisition planning packet exists at `docs/architecture/governed_data_source_acquisition_20260528.md`.
- [x] StartingVerdict recorded as `BLOCK`.
- [x] Current state recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.
- [x] BlockingReason records absent/ignored/local-governed artifacts without approved source manifests or generators.
- [x] Correct next decision records options A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady.
- [x] Recommendation records B unless a trusted governed bundle already exists.
- [x] Packet states planning/source acquisition only, not generation.
- [x] All five artifacts are documented in dependency order with source input, generator/gap status, approval, output schema, manifest/hash, validation command, rollback/removal, storage policy, and blocked-until condition.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.
- [ ] Trusted external governed bundle is approved and accepted. BLOCKED until user/source authorization.
- [ ] Source acquisition + bounded offline regeneration execution is approved. BLOCKED until explicit authorization.
- [ ] Any required data artifact is generated or intaken. BLOCKED and not approved by this round.
- [ ] Strict data readiness is proven as passing. BLOCKED.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Governed Data Artifact Authorization

- [x] RoundID recorded: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`.
- [x] ScopeID recorded: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`.
- [x] Authorization packet exists at `docs/architecture/governed_data_artifact_authorization_20260528.md`.
- [x] Gate truth recorded: GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS/degraded.
- [x] Blocked boot truth recorded: DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.
- [x] Missing artifact paths are explicitly listed: `data/processed/prices_tri.parquet`, `data/processed/prices.parquet`, `data/processed/tickers.parquet`, `data/processed/universe_r3000_daily.parquet`, `data/processed/rule100_softmax_v1_history.csv`.
- [x] Local artifacts and dirty context are recorded as not clean GitHub truth and not BootReady evidence.
- [x] Forbidden actions are recorded: no boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.
- [ ] Governed offline regeneration is approved and executed, or an approved external bundle is accepted. BLOCKED until user authorization.
- [ ] Missing governed artifacts are generated or intaken with manifest/hash/provenance approval. BLOCKED.
- [ ] Strict data readiness is proven through the approved read-only gate path. BLOCKED by missing governed artifacts.
- [ ] Safe boot or boot readiness is claimed as passing. BLOCKED and forbidden for this round.

## Latest Addendum - Research Validity Runner v0 Commit Anchor

- [x] Research-validity runner v0 exists in a local isolated commit.
- [x] Commit SHA recorded: `8716c51781d8524de4147cf42f17e52466913de4`.
- [x] Commit message: `Add research-validity runner v0 evidence gate`.
- [x] No boot-preflight, dashboard, optimizer/lifecycle, packet zip, or unrelated dirty files were staged into that commit.
- [x] Research/engine suite passed with 45 tests.
- [x] Affected replay/lifecycle/optimizer suite passed with 186 tests.
- [x] Context-builder test passed with 21 tests.
- [x] Context rebuild and validation passed.
- [x] SAW report block validation passed.
- [x] Commit is pushed to GitHub and remote branch resolves to `8716c51781d8524de4147cf42f17e52466913de4`.

## Latest Addendum - Portfolio Replay Role Contract

- [x] `REPLAY_COLUMNS` includes `context_role` and `row_role`.
- [x] `REPLAY_CONTEXT_COLUMNS` includes `context_role` and `row_role`.
- [x] `SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS` includes `context_role` and `row_role`.
- [x] Legacy selected-method artifacts missing role columns hydrate default roles on read.
- [x] Unrelated selected-method artifact schema drift still fails closed.
- [x] Dashboard context normalization delegates to `normalize_context_frame_for_replay(...)`.
- [x] Latest snapshot display uses `Replay Weight`, not generic `Weight`.
- [x] Allocation snapshot display uses `Current Weight`, not generic `Weight`.
- [x] Decision tables expose `Context Role` plus replay target and audit weight.
- [x] Diagnostics are computed from existing `DashboardReplayContext`.
- [x] Diagnostic payload includes replay identity and cache-signature hash.
- [x] Scoped compile passes.
- [x] Targeted role/compat/diagnostic hardening regressions pass after reviewer suggestions.
- [x] Affected replay/dashboard suite passes.
- [x] Real dashboard route AppTest smoke passes with role-aware table assertions.
- [x] SAW Implementer and Reviewer A/B/C passes complete.

## Latest Addendum - Optimizer History Diagnostics Split

- [x] Backend fail-closed `insufficient_history` semantics remain unchanged.
- [x] Missing local history is counted separately from stale local endpoints.
- [x] Universe Audit visible metrics include `Missing History`.
- [x] Universe Audit visible metrics include `Stale Endpoint`.
- [x] Universe Audit table includes `Latest Price Date`.
- [x] Allocation explanation uses split price-readiness labels.
- [x] Focused backend/UI regressions pass.
- [ ] Stale local price endpoint repair remains a separate data follow-up.
- [ ] Pre-2025 Rule100 candidate/decision artifact rebuild remains a separate backend/data follow-up.

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

- [x] Event/decision context rows carry replay-derived `target_weight`.
- [x] Original auxiliary event/decision weight is preserved as `audit_weight`.
- [x] Saved-artifact context rows are aligned to replay target weights before render.
- [x] Transitional backend context rows are aligned to replay target weights before render.
- [x] Strategy Replay Timeline renders stacked step-area allocation from replay `target_weight`.
- [x] Strategy Replay Timeline has an executable Plotly trace regression for stacked `hv` allocation areas.
- [x] Timeline remains display-only and does not feed Portfolio Performance.
- [x] Partial event rows missing `action` render as no trade events instead of crashing.
- [x] Partial latest snapshot rows missing display columns render unavailable instead of crashing.
- [x] Focused compile passes.
- [x] Targeted aux/timeline/fail-soft regressions pass.
- [x] Affected backend replay suite passes.
- [x] Affected frontend replay suite passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

- [x] Current allocation still validates against signed `PortfolioReplaySelection`.
- [x] Dashboard replay request assets include current signed assets.
- [x] Dashboard replay request assets include mapped ENTER/EXIT context tickers inside the selected replay window.
- [x] Dashboard replay request assets include mapped BUY/SELL decision tickers inside the selected replay window.
- [x] Rule100 replay request assets can include mapped Rule100 history tickers inside the selected replay window.
- [x] Dashboard `allocation_assets` remain current signed assets and drive selected PIT price loading.
- [x] Coverage-plan unavailable row emission is filtered to allocation assets before backend replay construction.
- [x] History-only horizon assets are added as zero-weight `context_only` rows after backend bundle construction.
- [x] Replay cache signatures distinguish widened `replay_assets` from current-only `allocation_assets`.
- [x] `_normalize_context_frame(...)` remains strict and is not loosened to display non-replay tickers.
- [x] Regression proves MU BUY/SELL rows stay in the bundle decision context while MU is not a latest positive-weight holding.
- [x] Focused compile passes.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [x] Optimizer/replay follow-up tests pass.
- [ ] Durable saved-artifact horizon-aware superset/subset policy remains a future backend/dashboard coordination follow-up.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

- [x] Batched replay loader builds full-window `r3000_pit` membership index before price loading.
- [x] Batched replay loader accepts `selected_permnos` and limits price/return reads to selected PIT members.
- [x] Batched replay metadata records `pit_membership_proof = "full_window_membership_index"`.
- [x] Dashboard passes signed numeric replay assets into the batched loader.
- [x] Dashboard still filters replay inputs to signed replay assets before backend replay execution.
- [x] MU/SNDK diagnostic is separate from dashboard replay request construction.
- [x] MU/SNDK diagnostic answers pinned universe, ticker-map, PIT membership, local price/return rows, Rule100 history, sizing/current-hold state, and latest gate.
- [x] MU/SNDK local price/return diagnostics reject non-finite `total_ret` rows.
- [x] Executable dashboard regression proves selected numeric replay assets are passed into the batched loader while non-selected PIT members stay out of the raw price load.
- [x] Local evidence JSON records selected-loader metadata and MU/SNDK trace result.
- [x] Focused compile passes.
- [x] Targeted selected-loader/source/trace regressions pass.
- [x] Broader affected suite passes with 112 tests.
- [ ] Separate Strategy/Data remediation for MU/SNDK Rule100 history/candidate-frame gaps remains optional follow-up.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

- [x] `_ensure_daily_portfolio_replay_context(...)` checks existing daily replay cache before entering the build spinner path.
- [x] In-session superset reuse ignores only `replay_dates` while requiring method, cap, controls, signed assets, sampling, and data signature to match.
- [x] Exact cache matches still prove actual replay rows cover requested dates.
- [x] Superset reuse proves requested dates are present in both `context.replay_dates` and `replay_df["date"]`.
- [x] Reused contexts are scoped to the selected horizon before rendering allocation/performance/timeline/events/decisions.
- [x] Saved replay artifacts still require exact `dashboard_cache_signature`.
- [x] Focused compile passes.
- [x] Targeted superset-cache regressions pass.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [x] Optimizer/replay coverage follow-up tests pass.
- [ ] Durable saved-artifact superset/subset policy remains a future backend/dashboard coordination follow-up.

## Latest Addendum - Max Replay Timeline Sampling Fix

- [x] Max-window Strategy Replay timeline sampling does not call `Series.normalize()`.
- [x] Weekly grouped keep-dates normalize through the pandas Series `.dt` accessor.
- [x] The final daily replay date is retained in the sampled timeline.
- [x] Timeline sampling remains display-only from daily replay rows.
- [x] Focused compile passes.
- [x] Targeted max-window sampler regression passes.
- [x] Focused Portfolio/YTD dashboard test file passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Portfolio Replay Selection Identity Hardening

- [x] `PortfolioReplaySelection` exists as the explicit replay-universe handoff.
- [x] Selection signature binds method, max-weight, risk-free rate, typed replay assets, current price-frame identity, and selected price content hash.
- [x] Dashboard replay cache signatures distinguish integer and string asset IDs.
- [x] Dashboard replay request construction validates signed selection before replay build/read.
- [x] Missing signed selection fails closed with `portfolio_replay_selection_unavailable`.
- [x] Stale/mismatched signed selection clears replay selection and replay/YTD caches.
- [x] Optimizer builder errors clear replay selection and replay/YTD caches.
- [x] Runtime replay request no longer reads `optimizer_universe`.
- [x] Runtime replay request no longer falls back to first 10 price columns.
- [x] Focused compile passes.
- [x] Focused replay-selection/advisory regressions pass.
- [x] Focused optimizer-selection AppTests pass.
- [ ] Backend producer ownership for aux event/decision rows remains a follow-up.

## Latest Addendum - Portfolio Single-Source Replay Page

- [x] Portfolio page builds one daily `DashboardReplayContext` before replay-facing surfaces render.
- [x] Top allocation display uses latest daily replay snapshot.
- [x] Optimizer panel is controls-only in the Portfolio single-source page flow.
- [x] Portfolio Performance consumes daily replay `portfolio_return`.
- [x] Portfolio Performance refuses non-daily replay.
- [x] Portfolio Performance does not fall back to optimizer weights, local/live weighted price paths, or equal-weight local performance.
- [x] Strategy Replay Timeline sampling is display-only from daily replay rows.
- [x] ENTER/EXIT Events uses the selected Portfolio horizon.
- [x] Duplicate Trade Event Log table is removed.
- [x] Latest Buys/Sells is derived from `bundle.decision_rows` / Buy/Sell Decision Log.
- [x] Render-path source guard rejects direct JSONL lifecycle/trade reads outside the bundle-building boundary.
- [x] Focused compile passes.
- [x] Focused Portfolio/replay/optimizer suite passes with 178 tests.
- [ ] SAW reviewer gate remains pending for implementation closure.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

- [x] Saved-artifact adapter preserves artifact event rows exactly, including empty frames.
- [x] Saved-artifact adapter preserves artifact decision rows exactly, including empty frames.
- [x] Saved artifacts with daily portfolio rows but empty event/decision rows do not backfill from separately loaded dashboard fallback frames.
- [x] Regression covers non-empty fallback event/decision frames while saved artifact aux frames remain empty.
- [x] Focused saved-artifact regression passes.
- [x] Focused frontend pytest suite passes with 106 tests.
- [x] Frontend/UI SAW report exists at `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md`.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Backend Replay Reader Identity Hardening

- [x] Manifest-level `run_id` must be a non-empty string after trimming.
- [x] Manifest-level `source_id` must be a non-empty string after trimming.
- [x] Manifest-level `method_id` must be a non-empty string after trimming.
- [x] Blank manifest identity is rejected before optional caller expected `run_id` / `source_id` checks.
- [x] Regression covers matching blank manifest and parquet identity with no expected IDs supplied by the caller.
- [x] Valid saved artifact reads remain accepted.
- [x] Focused compile passes.
- [x] Focused replay artifact/strategy/coverage suite passes with 79 tests and durations under budget.
- [x] Backend SAW report artifact exists at `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Frontend/UI Saved Replay Source Selector

- [x] Pure dashboard replay request construction is extracted from `_build_dashboard_strategy_replay_context(...)`.
- [x] Saved artifact read path uses backend `read_selected_method_replay_artifact(...)`.
- [x] Saved artifact UI consumption requires exact `dashboard_cache_signature`.
- [x] Dashboard cache signature binds method, max-weight cap, controls, assets, replay dates, sampling, and dashboard data signature.
- [x] Valid saved artifact maps to `DashboardReplayContext.source_mode = "saved_artifact"`.
- [x] Transitional backend build remains available only as labeled fallback when allowed.
- [x] Unavailable/stale/over-budget saved artifacts can return unavailable without rebuilding when fallback is disabled.
- [x] Stale saved artifact clears replay/YTD latest weights and cached replay context.
- [x] YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log consume one `DashboardReplayContext`.
- [x] `_render_strategy_replay_section()` does not directly call `read_lifecycle_log()`.
- [x] `_render_strategy_replay_section()` does not directly read `data/portfolio_lifecycle_buy_sell_log.jsonl`.
- [x] Executable saved-artifact context test asserts replay rows, latest snapshot, event rows, decision rows, source mode, and cache signature.
- [x] Focused compile passes.
- [x] Requested focused frontend pytest suite passes.
- [ ] Backend producers emitting `dashboard_cache_signature` for production saved-artifact UI hits remains a coordination follow-up.

## Latest Addendum - Saved Replay Artifact Reader + Budget

- [x] Saved selected-method replay artifact reader exists.
- [x] Reader validates parquet and manifest as one bundle.
- [x] Reader validates `run_id`, `source_id`, `method_id`, `artifact_type`, row counts, status counts, date window, input signatures, timing, and schema.
- [x] Reader rejects stale method context.
- [x] Reader rejects stale controls context.
- [x] Reader rejects same-shape/date Rule100 candidate-frame content drift.
- [x] Reader rejects stale replay date/window context.
- [x] Reader rejects stale input signatures.
- [x] Reader rejects stale source file signatures when supplied.
- [x] Reader rejects schema and manifest field drift.
- [x] Reader rejects null/blank parquet identity fields for run id, source id, artifact scope, method, and row type.
- [x] Reader rejects malformed timing payloads.
- [x] Manifest/parquet row/status/date-window mismatches fail closed.
- [x] `ReplayBudgetPolicy` exists with cold-start, rerun/cache, max rows, max dates, and max elapsed fields.
- [x] Saved reads enforce row/date/elapsed/cache budgets.
- [x] Budget-wrapped builds enforce cold-start/row/date/elapsed budgets.
- [x] Over-budget reads/builds return unavailable typed results with empty replay output.
- [x] Existing `build_selected_method_replay(...)` semantics and `REPLAY_COLUMNS` are preserved.
- [x] Selected-method output CLI exposes budget row/date/elapsed flags and uses the budget wrapper.
- [x] Focused compile passes.
- [x] Focused replay artifact/strategy/coverage suite passes with durations under budget.
- [ ] Frontend/dashboard saved-reader consumption remains a separate coordination slice.

## Latest Addendum - Overlay Overlap Anchor Fix

- [x] `scale_live_overlay_to_local(...)` has no public permissive no-overlap evidence flag.
- [x] Selected-price live overlays require same-column local/live overlap.
- [x] Selected no-overlap stale assets are dropped before optimizer evidence.
- [x] Benchmark live overlays require same-ticker local/live overlap.
- [x] Benchmark no-overlap stale tickers are dropped while fresh peers remain available.
- [x] Focused affected stale-data suite passes.
- [x] SAW Implementer and Reviewer A/B/C passes complete.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

- [x] `PriceEndpointFreshness` exists as a reusable endpoint snapshot.
- [x] `build_price_endpoint_freshness(...)` computes per-column endpoints and required endpoint in one chunked pass.
- [x] Dashboard computes one cached snapshot for loaded `prices_wide`.
- [x] Snapshot cache key includes unified data source signatures, loader arguments, and matrix shape.
- [x] Portfolio YTD uses the cached required endpoint instead of rescanning all columns.
- [x] Optimizer default ordering reuses the supplied per-column endpoints.
- [x] Optimizer selected-price prep reuses the supplied required endpoint.
- [x] Optimizer universe construction reuses the supplied snapshot for endpoint checks.
- [x] Direct callers without a supplied snapshot build one fallback snapshot.
- [x] Weighted portfolio YTD fails closed when live fallback omits a nonzero weighted asset.
- [x] Replay latest weights are signature-bound to current method/cap/assets/data before YTD can reuse them.
- [x] Cached full replay/YTD contexts are signature-bound before Portfolio Performance can reuse them.
- [x] Failed or non-ready replay contexts clear stale replay/YTD session weights.
- [x] Focused correctness regressions pass.
- [x] Actual local performance probe records endpoint match and reduced scan cost.
- [x] Reviewer A targeted recheck passes after weighted-YTD reconciliation.
- [ ] Reviewer B second targeted recheck passes after full-context signature reconciliation.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

- [x] Per-column price endpoint helper exists.
- [x] Generic endpoint/tolerance predicate is centralized in `core.data_orchestrator`.
- [x] `strategies.portfolio_universe` imports shared endpoint helpers and passes policy tolerance explicitly.
- [x] Source guard rejects private endpoint/tolerance helper clones in `strategies.portfolio_universe`.
- [x] Price-frame freshness filtering keeps only columns that reach the required endpoint.
- [x] Benchmark YTD drops stale benchmark columns that cannot be refreshed.
- [x] Benchmark YTD reports a common endpoint for remaining benchmark curves.
- [x] Portfolio YTD local fallback returns unavailable when a nonzero weighted leg is stale.
- [x] Optimizer selected-price prep passes the global price endpoint into live-overlay stitching.
- [x] Optimizer selected-price prep drops stale selected assets that cannot be refreshed.
- [x] Optimizer selected-price overlay requires same-column local/live overlap before treating live rows as allocation evidence.
- [x] Scaled overlays require same-column local/live overlap; no permissive no-overlap evidence mode remains.
- [x] Optimizer default ordering demotes stale endpoint assets before trailing-return ranking.
- [x] Optimizer universe eligibility checks endpoint freshness in addition to history observation count.
- [x] Focused stale-data regressions pass.
- [x] Broader affected dashboard/replay suite passes.
- [x] Formal SAW Implementer and Reviewer A/B/C rerun passes; governance PASS is claimed for this endpoint-centralization round.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

- [x] Dashboard consumes backend `build_selected_method_replay(...)` through `_build_dashboard_strategy_replay_context(...)`.
- [x] Dashboard backend-bundle call uses a per-date PIT `input_loader` backed by `load_strategy_replay_inputs(..., end_date=as_of_date, universe_mode="r3000_pit")`.
- [x] Dashboard Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log rows, and YTD latest-weight preference share `DashboardReplayContext`.
- [x] Source-guard tests prove the dashboard context calls `build_selected_method_replay(...)` and does not pass raw `prices_wide` replay frames.
- [x] Focused replay/dashboard suite passes.
- [x] Full repository pytest passes.
- [x] Runtime smoke passes for `/portfolio-and-allocation` on a fresh Streamlit process.
- [x] No promotion claim is made; same-window/same-cost/same-engine baseline delta evidence remains required before any future promotion claim.
- [ ] Saved artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.

## Latest Addendum - Replay Coverage Contract Audit Fix

- [x] Replay metadata writes contiguous `coverage_segments`.
- [x] Uncovered replay rows preserve specific `input_unavailable:<coverage_reason>` values.
- [x] Adapter fallback metadata includes coverage warnings for pre-coverage replay rows.
- [x] Uncovered-date replay emission is batched before performance attachment.
- [x] Duplicate shadowed coverage/perf test definitions are removed.
- [x] Row-heavy `no_priced_members` unavailable windows stay under the daily-scale budget with explicit per-member rows.
- [x] Replay performance aligns allocation-date weights to next tradable returns, not same-date returns.
- [x] Loader-based replay performance is recomputed once after combined output so portfolio equity is run-level continuous.
- [x] Tiny PIT replay frames avoid stack/merge performance attachment overhead.
- [x] Bound-feasible inverse-volatility targets skip SLSQP with diagnostics.
- [x] Context bootstrap selects replay-audit current truth instead of the older Rule100/YTD handover.
- [x] Context validation fails if the selected current truth packet drifts after bootstrap generation.
- [x] Focused replay coverage suite passes.
- [x] Affected replay/optimizer suite passes.
- [x] Full pytest passes.
- [x] Formal SAW Implementer and Reviewer A/B/C rechecks pass.
- [x] Dashboard consumes backend `build_selected_method_replay(...)` through the transitional dashboard bundle builder.
- [x] Runtime smoke passes for phase-close proof on `/portfolio-and-allocation`.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

- [x] Backend `build_selected_method_replay(...)` bundle API exists.
- [x] Backend replay bundle uses `build_strategy_replay(...)` as the shared target-weight frame source.
- [x] Rule of 100 and optimizer methods share the `REPLAY_COLUMNS` schema.
- [x] Replay output includes a `CASH` row per replay date.
- [x] Replay output includes `asset_return`, `weight_for_return`, `return_contribution`, `portfolio_return`, and `portfolio_equity`.
- [x] Backend event annotation and decision contexts filter to replay window/method/tickers or return explicit empty status/reason.
- [x] Dashboard `DashboardReplayContext` feeds Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell Decision Log rows.
- [x] Portfolio Performance primes latest selected-method replay weights before legacy optimizer fallback.
- [x] Timeframe/PIT rule is documented: UI horizons do not weaken per-date PIT loading with `end_date=as_of_date` and `universe_mode="r3000_pit"`.
- [x] Latest-trades-default UX rule is documented: Buy/Sell Decision Log sorts latest first and remains replay-audit-only.
- [x] Durable saved replay-output artifact/run id is implemented for selected-method replay output.
- [x] Saved replay-output artifact writes parquet rows plus manifest with run id, method id, source id, input signatures, date window, row/status counts, and timing.
- [x] Selected-method replay artifact path is confined to `data/runtime_cache/strategy_replay` for repo data writes.
- [x] Selected-method replay artifact parquet+manifest promotion is rollback-safe; manifest promotion failure cannot leave orphan parquet evidence.
- [x] Focused backend replay suite passes.
- [x] Focused dashboard replay/YTD/optimizer/lifecycle suite passes.
- [x] Dashboard consumes backend `build_selected_method_replay(...)` end to end through the transitional dashboard context builder rather than a dashboard-local direct `build_strategy_replay(...)` call.
- [x] Full repository pytest and runtime smoke pass for phase-close proof.
- [x] No promotion claim is made; same-window/same-cost/same-engine baseline delta evidence remains required before any future promotion claim.

## Latest Addendum - Frontend/UI Shared Replay Bundle

- [x] Dashboard has one selected-method `DashboardReplayContext` for Strategy Replay surfaces.
- [x] Strategy Replay latest snapshot reads from `DashboardReplayContext.latest_snapshot`.
- [x] Portfolio YTD primes and prefers the latest selected-method replay snapshot before legacy optimizer fallback.
- [x] ENTER/EXIT annotations are supplied by replay context, not direct calls in `_render_strategy_replay_section()`.
- [x] Buy/Sell Decision Log is supplied by replay context, not direct JSONL reads in `_render_strategy_replay_section()`.
- [x] Cheap Buy/Sell audit display remains before heavy full replay build.
- [x] Source-guard tests prove no direct split-source calls remain in the main replay render path.
- [x] Focused dashboard/optimizer replay suite passes.
- [x] Durable backend replay-output artifact/run id is implemented.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

- [x] Docs state the non-negotiable invariant: one selected-method replay run/source feeds YTD, current allocation/latest snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence.
- [x] Docs state that independent recomputation, stale allocation-state reuse, separate overlay artifacts, and separate decision tapes cannot be treated as the selected-method replay source.
- [x] Docs distinguish the architecture goal from temporary transitional bridges.
- [x] Docs state transitional bridges must be labeled, bounded, non-canonical, and forbidden from becoming a second replay stack.
- [x] Guardrails include no future-data leakage.
- [x] Guardrails include no stale-data carry-forward.
- [x] Guardrails include no fake improvements without same-window/same-cost/same-engine baseline deltas and saved evidence.
- [x] Guardrails include no overfitting or unchecked promotion.
- [x] Guardrails include no broker/live trading.
- [x] Guardrails include no alerts, rankings, recommendations, candidate scoring, or autonomous capital allocation.
- [x] Shared replay source implemented with one run/artifact identifier per selected method.
- [ ] Selected-method adapters use the shared replay source for all in-scope methods.
- [ ] Shared YTD/performance consumes shared daily portfolio output.
- [ ] Current allocation/latest snapshot consumes the same latest daily portfolio row used by YTD.
- [ ] Strategy Replay rows and ENTER/EXIT annotations consume the shared event/annotation source.
- [ ] Buy/Sell Decision Log consumes the same shared event/annotation source.
- [x] Saved evidence artifact records run id, method id, input signatures, date window, output row counts, status counts, and timing.
- [ ] Performance budget documented and enforced for cold-start replay, rerun/cache path, max rows/dates, and fail-closed timeout behavior.
- [x] SAW-style report exists for the docs-only enforcement round.
- [x] This Worker 3 round edits docs only and no code files.

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

- [x] Default Portfolio Optimizer method is `Rule of 100`.
- [x] Default optimizer asset ordering uses trailing 1-year return rather than YTD.
- [x] Backend benchmark builder returns both SPY and QQQ for current YTD display.
- [x] Runtime browser DOM shows SPY and QQQ metrics together.
- [x] Buy/Sell Decision Log is visible before heavy forward-walk replay output.
- [x] Buy/Sell Decision Log is labeled replay audit only, not live orders or trade signals.
- [x] Focused YTD/optimizer/portfolio/lifecycle/policy timeline tests pass.
- [x] Context packet validation passes.
- [ ] Full YTD forward-walk replay cold-start optimization completed.

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

- [x] Current focused patch is documented as visible Portfolio & Allocation QQQ/YTD/default-method/Rule100 parity work.
- [x] Larger urgent ultra-modular replay architecture milestone is documented as separate next-step work.
- [x] Milestone note states the loop is endless AI-assisted research evidence generation, not unchecked optimization.
- [x] Target contract names one replay engine.
- [x] Target contract names one strategy plug-in contract.
- [x] Target contract names one daily portfolio output format.
- [x] Target contract names one event/annotation format.
- [x] Target contract names one YTD/performance path.
- [x] Target contract names one saved evidence artifact.
- [x] Guardrails include no future-data leakage.
- [x] Guardrails include stale data handling / fail-closed behavior.
- [x] Guardrails include overfitting controls.
- [x] Guardrails include fake improvement rejection.
- [x] Guardrails include no broker/live trading.
- [x] Rule100 visible sizing fixes remain acceptance tests.
- [x] QQQ/YTD stale-overlay fixes remain acceptance tests.
- [x] Planner/bridge next step points to the modular replay milestone after QQQ/default-method visible fixes.
- [x] This architecture note makes no code changes.

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- [x] `Rule100SoftmaxConfig()` audit defaults remain `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- [x] `rule100_config_from_max_weight(max_weight)` exists.
- [x] Dynamic Rule100 UI/replay config sets `gross_budget_per_name=max_weight`.
- [x] Dynamic Rule100 UI/replay config sets `max_single_name_weight=max_weight`.
- [x] Direct Rule100 UI path passes `controls.max_weight` into softmax sizing.
- [x] Strategy Replay Rule100 path uses the same dynamic config as direct UI.
- [x] One eligible Rule100 name at 35% can target 35%.
- [x] Two equal eligible Rule100 names at 35% target 35%/35%/30% cash.
- [x] Direct Rule100 UI state and Strategy Replay agree for the same candidate frame and cap.
- [x] Frozen audit default still produces 10%/10%/80% cash for two equal names.
- [x] Benchmark freshness is evaluated per ticker.
- [x] Stale/missing QQQ attempts live overlay while fresh local SPY remains local.
- [x] Stale QQQ does not forward-fill into a visible fresh curve when live overlay returns empty.
- [x] Dashboard benchmark source can report `local+live_overlay`.
- [x] Focused Rule100/replay/YTD/AppTest suite passes.
- [x] Broader affected replay/data/dashboard/lifecycle suite passes.
- [x] Full pytest passes.
- [x] Streamlit readiness smoke passes.
- [x] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

- [x] `build_strategy_replay_cache_signature(...)` defaults to `universe_mode="r3000_pit"`.
- [x] `build_strategy_replay_cache_signature(...)` rejects non-`r3000_pit` universe modes.
- [x] `load_strategy_replay_inputs(...)` rejects non-`r3000_pit` universe modes.
- [x] `write_strategy_replay_artifact_atomic(...)` rejects repo `data/` output paths outside `data/runtime_cache/strategy_replay`.
- [x] `write_strategy_replay_artifact_atomic(...)` rejects `cache_dir=data/processed`.
- [x] Dashboard Strategy Replay loads per-date `StrategyReplayInputs`.
- [x] Dashboard Strategy Replay passes `prices=replay_inputs` to `build_strategy_replay(...)`.
- [x] Empty PIT selected-asset slices render explicit cash-closed rows instead of dropping dates.
- [x] Per-date PIT input failures render explicit cash-closed rows instead of aborting the full replay section.
- [x] Focused replay/data/dashboard suite passes.
- [x] Broader affected replay/portfolio/lifecycle/DASH suite passes.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

- [x] `scripts/rule100_softmax_v1_1_audit.py` active artifact contract is comparison CSV + summary JSON only.
- [x] `data/processed/rule100_softmax_v1_1_history.csv` is absent after audit refresh.
- [x] Stale v1.1 history bytes are retained only as `data/processed/rule100_softmax_v1_1_history.retired.csv`.
- [x] `factor_present_count` and `factor_positive_count` count approved factor groups, not raw columns.
- [x] `capital_cycle_score` and `quality_composite` cannot double-count the capital-discipline group.
- [x] Missing v1.1 factor strength shrinks toward neutral `0.50` by coverage.
- [x] Real dashboard `AppTest.from_file("dashboard.py")` captures the Policy Target Timeline TSM 2026-05-11 regression.
- [x] Focused v1.1, v1 history, lifecycle renderer, and route tests pass.
- [x] Full pytest passes after the v1.1 contract fix.
- [x] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule of 100 Method Label

- [x] `data/processed/rule100_softmax_v1_history.csv` exists as a derived v1 history overlay.
- [x] Historical overlay preserves immutable lifecycle `event_weight`.
- [x] Historical overlay writes `softmax_v1_target_weight` and `softmax_v1_cash_residual`.
- [x] Position Lifecycle Replay transaction log labels Event Weight separately from Softmax v1 Target.
- [x] Regression proves 2026-05-11 TSM remains event weight 10% but softmax v1 target is 0% and cash is 80%.
- [x] Focused softmax/history/lifecycle renderer tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Previous Addendum - Rule of 100 Method Label

- [x] `OptimizationMethod.RULE_OF_100` exists.
- [x] Dropdown label is exactly `Rule of 100`.
- [x] `Rule of 100` is included in `OPTIMIZATION_METHOD_OPTIONS`.
- [x] `Rule of 100` is not a mean-variance method.
- [x] Selecting `Rule of 100` routes to lifecycle holdings plus residual cash.
- [x] Empty lifecycle state under `Rule of 100` renders cash-only session state.
- [x] Focused compile passes.
- [x] Focused optimizer view and portfolio universe tests pass.
- [x] Runtime manual audit on port 8509 confirms visible dropdown label after restart.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Softmax v1 Audit

- [x] `strategies/rule100_softmax.py` exists and exposes pure softmax v1 sizing helpers.
- [x] `kelly_ablation_weights(...)` stays comparator-only and does not become a second stack.
- [x] `scripts/rule100_softmax_v1_audit.py` exists and writes versioned summary/comparison/sample/cash artifacts.
- [x] `Rule of 100` UI writes `portfolio_allocation_state.source = rule100_softmax_v1`.
- [x] Explicit `Rule of 100` UI target weights come from softmax v1 rather than lifecycle `last_weight`.
- [x] Regression proves TSM drops from stale 10% current weight to 0% target and residual cash rises to 80%.
- [x] Regression proves all-ineligible Rule100 candidate state renders cash-only instead of stale lifecycle weights.
- [x] Focused softmax/Kelly/audit harness tests pass.
- [x] Shared audit script runs successfully on the current PIT lifecycle state.
- [x] Full pytest completed after the audit harness round.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Rule100 Lifecycle Policy v0

- [x] `Rule100State` adapter exists and exposes demand/supply/pricing/margin with proxy provenance.
- [x] v0 BUY requires Rule100 3/4 confirmation, technical entry zone, and 3-day confirmation.
- [x] v0 HOLD tolerates one weak factor with 2/4 positives.
- [x] v0 TIGHTEN emits audit-only lifecycle rows for <2/4 factor state.
- [x] v0 TRIM emits audit-only lifecycle rows for `0.12 < dist_sma20 <= 0.20`.
- [x] v0 EXIT requires hard stop `dist_sma20 > 0.20` or confirmed trend veto.
- [x] v0 entry sizing uses `min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15)`.
- [x] Runtime lifecycle log promoted to v0 and has 29 events with open AMAT/LRCX/TSM.
- [x] Decision audit compares v0 against the 33-event baseline.
- [x] Focused Rule100/lifecycle/portfolio tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Lifecycle Decision Export

- [x] `export_lifecycle_decision_log(...)` exports PIT daily decision rows without mutating the lifecycle event log.
- [x] Export rows include `BUY`/`SELL`/`HOLD`/`NO_ACTION`, `primary_reason`, `reason_codes`, gate state, streaks, hold days, cooldown, and Rule-of-100 proxy fields.
- [x] Compact buy/sell JSONL exists at `data/portfolio_lifecycle_buy_sell_log.jsonl`.
- [x] Full decision JSONL exists at `data/portfolio_lifecycle_decision_log.jsonl`.
- [x] Audit summary exists at `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`.
- [x] Export buy/sell rows match `run_pit_replay(...)` emitted ENTER/EXIT events in regression coverage.
- [x] Export run shows 5424 decision rows, 33 BUY/SELL rows, 18 BUY, 15 SELL, and open AMAT/LRCX/TSM.
- [x] Focused export tests pass.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

- [x] `scripts.pit_lifecycle_replay.replay_entry_weight()` defaults to `0.10`.
- [x] ENTER weights no longer use `1 / len(replay_tickers)`.
- [x] `lifecycle_factor_confirmation(...)` exists and requires at least 3 present and positive PIT vectors.
- [x] ENTER requires a 3-day confirmation streak.
- [x] EXIT requires 20-day minimum hold plus 2-day confirmation unless `dist_sma20 > 0.20`.
- [x] Re-entry cooldown blocks a ticker until 10 calendar days after EXIT.
- [x] Replay CLI accepts `--log-path` and runs from repo root.
- [x] Final lifecycle log has 33 events, all ENTER weights at 0.10, and open AMAT/LRCX/TSM positions.
- [x] Final lifecycle log has no `<=5` day round trips.
- [x] Focused lifecycle/portfolio/YTD test suite passes.
- [x] Full pytest passes.
- [x] Browser smoke completed after reboot on port 8509 for this final replay.
- [x] `UnifiedDataPackage.prices` holds TRI/price levels, not daily returns.
- [x] Portfolio YTD uses local TRI history before live overlay.
- [x] Port 8509 smoke shows Portfolio `+14.25%` and does not show `7645112.18%`.
- [x] SAW report exists and validates for this churn/weight policy round.
- [ ] Independent SAW subagent Implementer and Reviewer A/B/C passes complete for PASS governance closure.

## Latest Addendum - Pinned Strategy Universe Hardening

- [x] `data/universe/pinned_thesis_universe.yml` exists with ≥10 thesis tickers.
- [x] `data/universe/loader.py` raises FileNotFoundError on missing manifest.
- [x] `data/universe/loader.py` raises ValueError on empty/malformed/duplicate entries.
- [x] `data/feature_store.py run_build()` aborts when pinned loader fails (unless `allow_missing_pinned_universe=True`).
- [x] `data/feature_store.py run_build()` unions pinned permnos into feature universe.
- [x] `scripts/pit_lifecycle_replay._default_replay_tickers()` raises on loader failure (no silent fallback).
- [x] `scripts/pit_lifecycle_replay.is_pit_eligible()` is the single shared gate for replay and diagnostics.
- [x] `scripts/pit_lifecycle_replay.diagnose_pinned_exclusions()` reports every pinned ticker with status OK/DATA_BLOCKED/FAILED_GATE.
- [x] All 10 pinned tickers have yahoo_patch coverage from 2025-01-02.
- [x] All 10 pinned tickers have features.parquet rows with non-null price-derived columns.
- [x] 27 regression tests in `tests/test_pinned_universe.py` pass.

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

- [x] `data.portfolio_lifecycle_log.get_open_lifecycle_positions` exists.
- [x] Open lifecycle positions use latest ENTER/EXIT event at or before `as_of`.
- [x] Future-dated lifecycle rows are ignored for current holdings.
- [x] Malformed lifecycle JSONL rows fail closed with a visible error.
- [x] Lifecycle JSONL appends use temp-file replacement instead of direct append.
- [x] Lifecycle sell-all overrides stale JSON position memory.
- [x] `strategies.portfolio_universe.load_current_position_memory` prefers lifecycle replay state when replay evidence exists.
- [x] `build_optimizer_universe` includes open lifecycle holdings as `included_current_hold`.
- [x] Open lifecycle holdings can remain included even when today's scanner row is EXIT/KILL.
- [x] Portfolio Optimizer renders lifecycle holds plus residual cash when there are open holds and no fresh PIT ENTER candidates.
- [x] Portfolio performance session weights preserve residual cash unless weights exceed 100%.
- [x] Live ticker-mapped YTD weights preserve residual cash unless mapped weights exceed 100%.
- [x] Focused compile passes.
- [x] Focused lifecycle/universe/optimizer/YTD tests pass.
- [x] Browser smoke completed for `/portfolio-and-allocation` after this fix.
- [x] Full pytest completed for this focused bug round.
- [x] SAW report exists and validates for this focused bug round.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- [x] `dashboard.py::_load_unified_data_cached` exists.
- [x] `_load_unified_data_cached` is decorated with `st.cache_resource`.
- [x] Dashboard unified package load includes `data_signature=build_unified_data_cache_signature(...)`.
- [x] `core.data_orchestrator.build_unified_data_cache_signature` exists.
- [x] Cache signature tracks source parquet path, mtime_ns, and size.
- [x] File add/remove/rewrite changes signature in focused tests.
- [x] Dashboard source guard confirms cached unified load path.
- [x] Focused compile passes.
- [x] Focused data-orchestrator/dashboard tests pass.
- [x] Portfolio YTD and optimizer view regressions pass.
- [x] Streamlit HTTP smoke reaches dashboard with status 200.
- [x] Context validation passes.
- [x] Full pytest completed in this round.
- [x] SAW independent Implementer and Reviewer A/B/C passes completed in this round.
- [x] Stale quick-slice closure evidence reconciled after full pytest.
- [x] `docs/saw_reports/saw_dashboard_unified_data_cache_performance_20260511.md` exists and records SAW PASS.
- [x] SAW closure packet validation passes.
- [x] SAW report block validation passes.

## Latest Addendum - Dashboard Scanner Testability Hardening

- [x] `strategies/scanner.py` exists and owns deterministic scanner math.
- [x] `dashboard.py` preserves yfinance/provider calls and delegates scanner enrichment to `strategies.scanner.enrich_scan_frame`.
- [x] Macro score, breadth, price technicals, cluster, entry/support, tactics, proxy signal, rating, leverage, and scan-frame enrichment have focused tests.
- [x] Non-finite macro and breadth inputs fail closed to unknown/neutral behavior with regression coverage.
- [x] `tests/conftest.py` includes shared price/return/macro/ticker-map fixtures.
- [x] `InvestorCockpitStrategy` quality-cap coverage exists.
- [x] `AdaptiveTrendStrategy` regime transition coverage exists.
- [x] `ProductionConfig` invariant coverage exists.
- [x] `core.etl` temp-directory parquet build coverage exists.
- [x] Process guardrail test still passes.
- [x] Focused affected pytest passes.
- [x] Scoped compile passes.
- [x] Full pytest completed for this scanner hardening addendum.
- [x] SAW Reviewer C final recheck passes after latest invalid credit denominator reconciliation.
- [x] `docs/saw_reports/saw_dashboard_scanner_testability_hardening_20260511.md` records SAW PASS.

## Latest Addendum - Dashboard Architecture Safety Slice

- [x] `utils/process.py` exists and exposes `pid_is_running`.
- [x] Dashboard backtest PID probing delegates to `pid_is_running`.
- [x] Updater, parameter-sweep, release-controller, and phase16 optimizer lock probes delegate through shared helper or compatibility wrappers.
- [x] Source guard test rejects `os.kill(pid, 0)` and `os.kill(int(pid), 0)` in runtime lock callers.
- [x] `dashboard.py::spawn_backtest` does not terminate an unverified PID-file owner.
- [x] Dashboard strategy matrix initialization uses `_build_strategy_matrix` / `_ensure_modular_strategy_state`.
- [x] `dashboard.py::_clean_portfolio_price_frame` delegates to `core.data_orchestrator.clean_price_frame`.
- [x] Focused compile passes.
- [x] Affected focused tests pass.
- [x] HTTP smoke reaches dashboard with status 200.
- [ ] Full pytest completed in this round. It timed out after 304 seconds and requires a longer follow-up window for phase closure.
- [x] SAW independent Implementer and Reviewer A/B/C passes complete.
- [x] Reviewer B High finding on unverified PID termination was fixed and rechecked PASS.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- [x] `tests/test_optimizer_view.py` exists.
- [x] `tests/test_optimizer_view.py` uses `streamlit.testing.v1.AppTest`.
- [x] Optimizer view renders without Streamlit exceptions in focused AppTest coverage.
- [x] Mean-variance selection and sector-cap controls are exercised in AppTest coverage.
- [x] UI-derived max-weight and risk-free-rate controls are tested through the real SLSQP optimizer path.
- [x] Sector caps remain post-solver soft constraints and are tested as such.
- [x] Recent close display overlays use a display-only Parquet cache in `core/data_orchestrator.py`.
- [x] Cold display-overlay cache misses schedule background refresh and return without synchronous provider blocking.
- [x] Parquet cache writes use temp-file then `os.replace`.
- [x] Overlay scaling cache returns copy-safe dataframes.
- [x] Optimizer runs are cached by method, selected price frame, max-weight, and risk-free-rate.
- [x] Focused optimizer view, optimizer core policy, and DASH-2 tests pass.
- [x] Full pytest passes after implementation.
- [x] Runtime smoke passes for `/portfolio-and-allocation`.
- [x] `docs/saw_reports/saw_portfolio_optimizer_view_perf_hardening_20260511.md` exists and records SAW PASS.
- [x] Independent Implementer and Reviewer A/B/C SAW passes complete.

## Latest Addendum - Portfolio Data Boundary Refactor

- [x] `core/data_orchestrator.py` owns selected-stock display-refresh close extraction.
- [x] `core/data_orchestrator.py` owns local TRI overlay scaling and selected-price stitching.
- [x] `core/data_orchestrator.py` owns `data/backtest_results.json` strategy-metrics parsing.
- [x] `views/optimizer_view.py` does not import yfinance.
- [x] `views/optimizer_view.py` does not parse `data/backtest_results.json` directly.
- [x] `data/providers/legacy_allowlist.py` does not require `views/optimizer_view.py`.
- [x] Partial live overlays merge cell-wise and preserve local TRI values for missing live cells.
- [x] Duplicate local/live anchor dates are deduped before overlay scaling.
- [x] Stale display overlay cache behavior is explicit stale-while-revalidate and display-only.
- [x] Background overlay scheduler submit failures fail soft and clear the inflight key.
- [x] Focused data-orchestrator, dashboard sprint, DASH-2, provider-port, and portfolio regression tests pass.
- [x] Scoped compile passes for touched runtime/test files.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- [x] `strategies/optimizer_diagnostics.py` exists.
- [x] `OptimizerFeasibilityReport`, `OptimizerBoundDiagnostics`, `OptimizerConstraintDiagnostics`, `OptimizerSolverDiagnostics`, and `OptimizerDiagnosticSeverity` exist outside UI code.
- [x] Pre-solver upper-bound infeasibility is rejected without fallback.
- [x] Lower-bound and required-minimum infeasibility diagnostics exist without approving lower-bound allocation policy.
- [x] Equal-weight boundary pressure is reported.
- [x] Active upper and lower bounds are diagnosed directly from weights.
- [x] SLSQP failure reports solver status/message and labels equal-weight fallback as not optimized.
- [x] Optimizer UI includes status, feasibility, active constraints, assets at max cap/lower bound, equal-weight forced, and fallback labels.
- [x] Non-finite diagnostic weights fail closed as errors and cannot be reported as optimized.
- [x] Focused optimizer policy tests pass with no strict xfails.
- [x] Scoped compile passes for optimizer diagnostics, optimizer core, optimizer UI, and dashboard.
- [x] Full pytest passes after SAW reconciliation.
- [x] Browser smoke passes on `/portfolio-and-allocation`.
- [x] `docs/saw_reports/saw_optimizer_core_structured_diagnostics_20260511.md` exists and records SAW PASS.

## Latest Addendum - Optimizer Core Policy Audit

- [x] `docs/architecture/optimizer_core_policy_audit.md` exists.
- [x] `docs/architecture/optimizer_constraints_policy.md` exists.
- [x] `docs/architecture/optimizer_lower_bound_slsqp_policy.md` exists.
- [x] `tests/test_optimizer_core_policy.py` exists.
- [x] `docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md` exists.
- [x] Audit rejects the quarantined lower-bound/SLSQP diff as-is.
- [x] No optimizer implementation changes are made in this audit round.
- [x] Focused optimizer policy tests pass with expected strict xfails for known policy debt.

## Latest Addendum - Portfolio Universe Quarantine Closure

- [x] Dirty `strategies/optimizer.py` lower-bound/SLSQP diff was inspected.
- [x] Dirty optimizer-core diff was saved to `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`.
- [x] Quarantine note exists at `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md`.
- [x] `strategies/optimizer.py` was reverted to baseline for this closure.
- [x] `git diff -- strategies/optimizer.py` is empty.
- [x] Focused portfolio universe, DASH-2, and DASH-1 tests pass.
- [x] Full pytest passes after quarantine and hygiene repair.
- [x] Scoped compile passes.
- [x] Context validation passes.
- [x] Browser smoke confirms Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render on port `8503`.
- [x] SAW closure packet records `ChecksTotal=9`, `ChecksPassed=9`, `ChecksFailed=0`, `Verdict=PASS`.

## Latest Addendum - Portfolio Universe Construction Fix

- [x] `strategies/portfolio_universe.py` exists and owns optimizer universe eligibility.
- [x] `dashboard.py` no longer passes `selected_tickers[:20]` from display-sorted `df_scan` into the optimizer.
- [x] `EXIT`, `KILL`, `AVOID`, and `IGNORE` are excluded by default.
- [x] Generic `WATCH` is research-only by default.
- [x] Missing local ticker mapping is reported.
- [x] Insufficient local price history is reported.
- [x] Max-weight feasibility and equal-weight boundary diagnostics exist.
- [x] Misleading `Auto (Best Sharpe)` label is removed from runtime.
- [x] MU hard floor and conviction mode remain absent.
- [x] Focused portfolio universe and DASH-2 tests pass.
- [x] Scoped compile passes.
- [x] Browser smoke confirms Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render on port `8503`.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- [x] Portfolio Optimizer renders top-level on `Portfolio & Allocation`.
- [x] Optimizer expander/toggle is removed from the Portfolio page.
- [x] YTD Performance renders below the optimizer.
- [x] Portfolio YTD return uses current optimizer weights when available.
- [x] SPY/QQQ YTD comparison metrics render.
- [x] Selected stock and benchmark prices refresh in-memory for display freshness without canonical writes.
- [x] Focused DASH-2 tests pass.
- [x] DASH-1 navigation regression passes.
- [x] Scoped compile passes.
- [x] Browser check confirms optimizer-before-YTD order and prices through `2026-05-08`.

## Header

- `CHECKLIST_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `STATUS`: `current`
- `OWNER`: `PM / Architecture Office`

## Done Criteria

### Artifact Completeness

- [x] `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json` exists.
- [x] `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json` exists.
- [x] `tests/test_g8_2_system_scouted_candidate_card.py` exists.
- [x] `docs/architecture/g8_2_system_scouted_candidate_card_policy.md` exists.
- [x] `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md` exists.
- [x] `docs/saw_reports/saw_phase65_g8_2_system_scouted_candidate_card_20260510.md` exists after SAW publication.

### Source-Intake Completeness

- [x] Existing `LOCAL_FACTOR_SCOUT` output exists.
- [x] Existing scout output contains exactly one item.
- [x] Existing scout output ticker is `MSFT`.
- [x] MSFT card ticker matches the scout output ticker.
- [x] MSFT card references `data/discovery/local_factor_scout_output_tiny_v0.manifest.json`.
- [x] MSFT card manifest hash matches card bytes.

### Card Completeness

- [x] `candidate_status = candidate_card_only`.
- [x] `discovery_origin = LOCAL_FACTOR_SCOUT`.
- [x] `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`.
- [x] `source_intake_item_id` is present.
- [x] `source_intake_manifest_uri` is present.
- [x] `candidate_card_manifest_uri` is present.
- [x] `primary_alpha` records thesis summary, driver, present evidence, missing evidence, and thesis breakers.
- [x] `secondary_alpha` records relevant modules, observed signal availability, later estimated signals, and provider gaps.
- [x] `state_mapping` forbids action states and direct action jumps.
- [x] `governance` records not validated, not actionable, no score, no rank, no buy/sell signal, no alert, and no broker action.

### Scope Completeness

- [x] No card is created for `DELL`, `AMD`, `LRCX`, `ALB`, or any other user-seeded intake item.
- [x] No new `LOCAL_FACTOR_SCOUT` output is added.
- [x] No factor score is displayed.
- [x] No rank is displayed.
- [x] No buy/sell/hold output is emitted.
- [x] No thesis validation is claimed.
- [x] No actionability is claimed.
- [x] No buying range is claimed.
- [x] No alert or broker action is emitted.
- [x] No dashboard runtime behavior is added.

### Validation Status

- [x] Focused G8.2 tests: PASS.
- [x] G8/G8.1B/G8.2 regression: PASS.
- [x] Scoped compile: PASS.
- [x] Context-builder tests: PASS.
- [x] Context rebuild and validation: PASS.
- [x] SAW report validation: PASS.
- [x] Closure packet validation: PASS.

## Machine-Checkable Rules

```text
.venv\Scripts\python -m pytest tests\test_g8_2_system_scouted_candidate_card.py -q
.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q
.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q
.venv\Scripts\python -m py_compile opportunity_engine\candidate_card_schema.py opportunity_engine\candidate_card.py tests\test_g8_2_system_scouted_candidate_card.py
.venv\Scripts\python scripts\build_context_packet.py --validate
```

## Open Risks

- yfinance migration remains future debt.
- S&P sidecar freshness remains stale.
- Reg SHO policy gap remains future work.
- GodView provider, options license, ownership, insider, and market-behavior gaps remain open.
- Dashboard runtime list still contains legacy action-shaped labels; G8.2 does not merge into that runtime surface.
- Factor model validation remains open before any predictive or ranked use.
- Broad dirty worktree and inherited compileall hygiene remain out of scope.

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

- [x] `portfolio_allocation_state` exists and records mode/source/weights/cash_only/latest_price_date.
- [x] Legacy mirrors `optimizer_weights`, `optimizer_cash_only`, and `optimizer_price_latest_date` remain available.
- [x] `Rule of 100` and current-hold replay write explicit replay state instead of blending into optimizer output.
- [x] Portfolio page copy separates optimizer output from replay output.
- [x] `views.page_registry.build_dashboard_navigation(...)` keeps `Portfolio & Allocation` as the default visible page and assigns the explicit `portfolio-and-allocation` url path.
- [x] Focused compile passes for dashboard, page registry, optimizer view, and route/smoke tests.
- [x] Focused dashboard/navigation/optimizer/universe tests pass.
- [x] AppTest smoke for `dashboard.py` with `query_params["page"]="portfolio-and-allocation"` passes without exception and renders Portfolio + current-hold replay output.
