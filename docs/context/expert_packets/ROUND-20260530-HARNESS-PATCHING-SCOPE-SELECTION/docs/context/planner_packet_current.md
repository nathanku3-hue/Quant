# Planner Packet - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, live trading, strategy search, candidate ranking, candidate scoring, thesis validation, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: provide the planner with a compact fresh world model after the Portfolio Optimizer View Test and Performance Hardening round.

## Latest Addendum - Governed Data Source Provenance Intake

- `CURRENT_DELTA`: `Source-provenance intake packet exists at docs/architecture/governed_data_source_provenance_intake_20260528.md and keeps the next step before generation.`
- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE`
- `ScopeID`: `SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION`
- `STARTING_VERDICT`: `BLOCK`
- `GATE_TRUTH`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; DataSourceAcquisitionPacket PASS; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.`
- `BLOCKING_REASON`: `Strict data readiness still lacks approved source provenance, manifests, hashes, generated artifacts, and validation proof.`
- `INTAKE_LINES`: `prices source -> prices.parquet -> prices_tri.parquet; ticker/security master source -> tickers.parquet; WRDS/R3000 membership source -> universe_r3000_daily.parquet; Rule100 history source/generator -> rule100_softmax_v1_history.csv.`
- `OPEN_DECISION`: `Approve raw/source provenance before any data/processed generation; otherwise keep BootReady quarantined as blocked.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_provenance_first_then_bounded_offline_regeneration_then_strict_data_readiness_and_require_github_boot_proof.`
- `DO_NOT_REDECIDE`: `This packet does not authorize generation yet; no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no runtime/boot_status_current.json edit; no ignored/local-governed data commit unless policy changes; no BootReady claim.`

## New Context Packet - Governed Data Source Provenance Intake

## What Was Done

- Published a docs-only source-provenance intake packet for raw/source approval before any processed artifact generation.
- Recorded required provenance fields for prices, tickers/security master, WRDS/R3000 membership, and Rule100 history source/generator.
- Refreshed current truth surfaces without changing code, tests, runtime, data artifacts, boot preflight, or boot status.

## What Is Locked

- DataReadyStrict remains `BLOCKED_MISSING_GOVERNED_ARTIFACTS`.
- SafeBoot remains `false`.
- BootReady remains `BLOCKED`.
- The packet does not authorize generation yet.
- Local ignored artifacts and runtime boot status are not commit evidence.

## What Is Next

- Approve source provenance first; then approve bounded offline regeneration; then rerun strict data readiness and strict GitHub-aligned boot proof.

## First Command

```text
rg -n "ROUND-20260528-GOVERNED-DATA-SOURCE-PROVENANCE-INTAKE|SCOPE-APPROVE-RAW-SOURCES-BEFORE-ARTIFACT-GENERATION|StartingVerdict: BLOCK|DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS|BootReady: BLOCKED|does not authorize generation yet|Approve source provenance first" docs/architecture/governed_data_source_provenance_intake_20260528.md docs/context/bridge_contract_current.md docs/context/impact_packet_current.md docs/context/done_checklist_current.md docs/context/planner_packet_current.md docs/context/multi_stream_contract_current.md docs/context/post_phase_alignment_current.md docs/context/observability_pack_current.md "docs/decision log.md" docs/notes.md docs/lessonss.md docs/phase_brief/phase65-brief.md
```

## Latest Addendum - Governed Data Source Acquisition / Bounded Regeneration Planning

- `CURRENT_DELTA`: `Source-acquisition planning packet exists at docs/architecture/governed_data_source_acquisition_20260528.md for the five strict-readiness artifacts.`
- `RoundID`: `ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION`
- `ScopeID`: `SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS`
- `STARTING_VERDICT`: `BLOCK`
- `GATE_TRUTH`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; GovernedDataAuthorizationPacket PASS; StrictProof PASS / DEGRADED; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED; RuntimeBootStatus local / ignored / not commit evidence.`
- `BLOCKING_REASON`: `Required canonical data artifacts are absent/ignored/local-governed and not backed by approved source manifests or generators.`
- `DEPENDENCY_ORDER`: `raw prices source -> prices.parquet -> prices_tri.parquet -> tickers.parquet -> universe_r3000_daily.parquet -> rule100_softmax_v1_history.csv.`
- `OPEN_DECISION`: `Choose A trusted external governed bundle, B source acquisition + bounded offline regeneration planning, or C quarantine BootReady.`
- `RECOMMENDED_NEXT_STEP`: `approve_source_acquisition_plus_bounded_offline_regeneration_planning_unless_trusted_bundle_exists_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `This round approves planning/source acquisition only, not generation; no boot_preflight.py patch; no DataReadyStrict weakening; no placeholder parquet/CSV; no generation during boot; no runtime/boot_status_current.json edit; no data/processed commit unless policy changes; no BootReady claim.`

## New Context Packet - Governed Data Source Acquisition / Bounded Regeneration Planning

## What Was Done

- Published a docs-only source-acquisition and bounded-regeneration planning packet for the five strict-readiness artifacts.
- Recorded cautious existing-generator/gap status without approving or running generators.
- Refreshed current truth surfaces without changing code, tests, runtime, data artifacts, boot preflight, or boot status.

## What Is Locked

- DataReadyStrict remains `BLOCKED_MISSING_GOVERNED_ARTIFACTS`.
- SafeBoot remains `false`.
- BootReady remains `BLOCKED`.
- GovernedDataAuthorizationPacket is PASS, but source acquisition and generation remain BLOCK until explicitly approved.
- Local ignored artifacts and runtime boot status are not commit evidence.

## What Is Next

- Approve a trusted external governed bundle, approve source acquisition + bounded offline regeneration planning, or explicitly quarantine BootReady.

## First Command

```text
rg -n "ROUND-20260528-GOVERNED-DATA-SOURCE-ACQUISITION|SCOPE-SOURCE-INPUTS-AND-GENERATORS-FOR-STRICT-DATA-READINESS|StartingVerdict: BLOCK|DataReadyStrict: BLOCKED_MISSING_GOVERNED_ARTIFACTS|BootReady: BLOCKED|planning/source acquisition only|not generation|no BootReady claim" docs/architecture/governed_data_source_acquisition_20260528.md docs/context/bridge_contract_current.md docs/context/impact_packet_current.md docs/context/done_checklist_current.md docs/context/planner_packet_current.md docs/context/multi_stream_contract_current.md docs/context/post_phase_alignment_current.md docs/context/observability_pack_current.md "docs/decision log.md" docs/notes.md docs/lessonss.md docs/phase_brief/phase65-brief.md
```

## Latest Addendum - Governed Data Artifact Authorization

- `CURRENT_DELTA`: `Authorization packet exists at docs/architecture/governed_data_artifact_authorization_20260528.md for strict data-readiness artifact intake or offline regeneration.`
- `RoundID`: `ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION`
- `ScopeID`: `SCOPE-APPROVE-INTAKE-OR-REGENERATION-FOR-STRICT-DATA-READINESS`
- `GATE_TRUTH`: `GovernanceGateV0 PASS; BootStatusPathContract PASS; StrictProof PASS/degraded; DataReadyStrict BLOCKED_MISSING_GOVERNED_ARTIFACTS; SafeBoot false; BootReady BLOCKED.`
- `MISSING_ARTIFACTS`: `data/processed/prices_tri.parquet; data/processed/prices.parquet; data/processed/tickers.parquet; data/processed/universe_r3000_daily.parquet; data/processed/rule100_softmax_v1_history.csv.`
- `BOUNDARY`: `Local artifacts, dirty context, and inherited boot-control diffs are not clean GitHub truth or BootReady evidence; inherited boot-control diffs are out-of-scope and not evidence for or against this docs-only packet.`
- `OPEN_RISK`: `Inherited boot-control diffs remain unresolved outside this packet; BootReady stays BLOCKED and launch preflight must not be used as DataReadyStrict or BootReady proof for this packet.`
- `NEXT_STEP`: `approve_bounded_offline_regeneration_authorization_or_approved_external_bundle_otherwise_quarantine_BootReady.`
- `DO_NOT_REDECIDE`: `No boot_preflight.py patch; no DataReadyStrict weakening; no generation during boot; no placeholder parquet/CSV; no data/processed commit unless policy changes; no runtime/boot_status_current.json edit; no BootReady claim.`

## New Context Packet - Governed Data Artifact Authorization

## What Was Done

- Published an advisory authorization packet for the five missing governed strict-readiness artifacts.
- Refreshed current truth surfaces without changing code, runtime, tests, data artifacts, boot status, or boot preflight.

## What Is Locked

- DataReadyStrict remains `BLOCKED_MISSING_GOVERNED_ARTIFACTS`.
- SafeBoot remains `false`.
- BootReady BLOCKED.
- Local ignored or dirty artifacts are not GitHub truth.
- Inherited boot-control diffs remain out-of-scope and are not packet evidence.

## What Is Next

- Approve bounded offline regeneration authorization or an approved external bundle; otherwise quarantine BootReady.

## First Command

```text
rg -n "ROUND-20260528-GOVERNED-DATA-ARTIFACT-AUTHORIZATION|BootReady BLOCKED|no boot_preflight.py patch|no DataReadyStrict weakening|no generation during boot|no placeholder parquet/CSV|no runtime/boot_status_current.json edit|no BootReady claim" docs/context docs/decision\ log.md docs/notes.md docs/lessonss.md docs/phase_brief/phase65-brief.md docs/architecture/governed_data_artifact_authorization_20260528.md
```

## Latest Addendum - Research Validity Runner v0 Commit Anchor

- `CURRENT_DELTA`: `Research Validity Runner v0 is isolated and pushed in commit 8716c51781d8524de4147cf42f17e52466913de4.`
- `COMMIT_MESSAGE`: `Add research-validity runner v0 evidence gate.`
- `IMPLEMENTATION_ARTIFACTS`: `research/`, `tests/test_research_*.py`, `docs/architecture/research_validity_contract.md`, `docs/saw_reports/saw_research_validity_runner_v0_20260526.md`.
- `TEST_DELTA`: `Research/engine suite PASS with 45 tests; affected replay/lifecycle/optimizer suite PASS with 186 tests; context-builder test PASS with 21 tests; context rebuild/validate PASS.`
- `SAW_DELTA`: `Reviewer A/B/C PASS and staged-diff reviewer PASS; SAWBlockValidation PASS.`
- `GITHUB_DELTA`: `GitHub is aligned through 8716c51781d8524de4147cf42f17e52466913de4 on origin/codex/optimizer-core-structured-diagnostics.`
- `BOUNDARY`: `Inherited dirty/untracked worktree remains outside this commit; boot-preflight staging must not continue until this commit anchor is acknowledged.`
- `NEXT_STEP`: `classify_remaining_dirty_context_then_continue_boot_preflight_staging.`

## Latest Addendum - Portfolio Replay Role Contract

- `CURRENT_DELTA`: `Portfolio replay rows now carry explicit context_role and row_role semantics across replay rows, aux context rows, and selected-method artifacts.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/strategy_replay.py`, `dashboard.py`, `tests/test_strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_policy_target_timeline_apptest.py`.
- `SCHEMA_DELTA`: `REPLAY_COLUMNS, REPLAY_CONTEXT_COLUMNS, and SELECTED_METHOD_REPLAY_ARTIFACT_COLUMNS include role fields; legacy artifacts hydrate missing roles rather than crashing.`
- `UI_DELTA`: `Latest Snapshot uses Replay Weight and allocation snapshot uses Current Weight; decision rows expose Context Role, Replay Target, and Aux Audit Wt.`
- `DIAGNOSTIC_DELTA`: `Replay diagnostics are computed from DashboardReplayContext and bind run/source/method/cache identity.`
- `TEST_DELTA`: `Scoped compile PASS; targeted role/compat/diagnostic regressions PASS; affected replay/dashboard/AppTest suite PASS with 169 tests.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C PASS; Reviewer C hardening suggestions were added and rechecked.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, strategy promotion, or diagnostic-triggered replay rebuild was added.`
- `NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_policy.`

## New Context Packet - Portfolio Replay Role Contract

## What Was Done

- Added explicit role schema fields to replay, context, and selected-method artifact outputs.
- Centralized context normalization in strategy replay and made dashboard call the shared contract.
- Hydrated role defaults for older saved artifacts while preserving fail-closed behavior for unrelated schema drift.
- Renamed replay-facing visible weights to role-aware labels.
- Added diagnostics from the existing DashboardReplayContext.

## What Is Locked

- Lifecycle/event `weight` is audit intent; replay `target_weight` is exposure truth.
- `context_role` is the durable row-semantics field.
- Dashboard must not maintain a private replay/context normalization copy.
- Diagnostics must not rebuild replay.

## What Is Next

- Hold, or continue the separate backend dashboard_cache_signature / saved-artifact policy work.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q
```

## Latest Addendum - Optimizer History Diagnostics Split

- `CURRENT_DELTA`: `Portfolio Optimizer diagnostics now distinguish Missing History from Stale Endpoint while keeping stale endpoints fail-closed.`
- `IMPLEMENTATION_ARTIFACTS`: `views/optimizer_view.py`, `tests/test_portfolio_universe.py`, `tests/test_optimizer_view.py`.
- `UI_DELTA`: `Universe Audit no longer shows the mixed History Fail bucket; it shows Missing History and Stale Endpoint plus Latest Price Date.`
- `TEST_DELTA`: `Scoped compile PASS; focused optimizer universe/view suite PASS with 62 tests.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, price repair, Rule100 artifact rebuild, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `repair_stale_price_endpoints_or_build_rule100_pre2025_evidence_artifacts_or_hold.`

## New Context Packet - Optimizer History Diagnostics Split

## What Was Done

- Split visible optimizer price-readiness diagnostics into Missing History and Stale Endpoint.
- Added Latest Price Date to Universe Audit display rows.
- Added regressions for split summary and AppTest-visible metrics.

## What Is Locked

- Stale endpoint assets remain optimizer-ineligible.
- True missing history and stale endpoint data repair are separate operational causes.
- Pre-2025 Rule100 replay remains cash-closed until candidate/decision evidence exists.

## What Is Next

- Repair stale local price columns, build pre-2025 Rule100 evidence artifacts, or hold.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_optimizer_view.py -q
```

## Latest Addendum - Dashboard Replay Aux Weight Semantics + Stacked Timeline

- `CURRENT_DELTA`: `Portfolio & Allocation replay-facing aux surfaces now display replay-derived target_weight semantics; original event/decision weights are preserved as audit_weight only.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `strategies/strategy_replay.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_strategy_replay.py`.
- `UI_DELTA`: `Strategy Replay Timeline now renders a stacked step-area allocation chart from replay target_weight, with CASH muted and equities ordered by latest weight/active days.`
- `RESILIENCE_DELTA`: `Partial saved/transitional schemas fail soft when event rows lack action or latest snapshots lack display columns.`
- `TEST_DELTA`: `Scoped compile PASS; targeted aux/timeline/fail-soft regressions PASS including executable Plotly trace validation; affected backend replay suite PASS with 80 tests; affected frontend replay suite PASS with 134 tests; latest focused dashboard file PASS with 66 tests.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, promotion claim, or saved-artifact superset policy was added.`
- `NEXT_STEP`: `hold_or_continue_backend_dashboard_cache_signature_emission_policy.`

## New Context Packet - Dashboard Replay Aux Weight Semantics + Stacked Timeline

## What Was Done

- Added replay-weight lookup/alignment for event and decision context rows.
- Set visible aux `target_weight`/`weight` from matching replay `target_weight`.
- Preserved original aux `weight` as `audit_weight`.
- Converted Strategy Replay Timeline to stacked step-area allocation composition with executable Plotly trace coverage.
- Added fail-soft guards for partial saved/transitional schemas.

## What Is Locked

- Replay-facing Portfolio weights use daily selected-method replay target-weight truth.
- Auxiliary lifecycle/event/decision weights are audit metadata only.
- Portfolio page remains one `DashboardReplayContext`.
- Partial aux/snapshot schemas must not crash the page.

## What Is Next

- Hold, or continue the separate backend/dashboard saved-artifact cache-signature policy work.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q
```

## Next Todos

- Keep aux `target_weight` joined from replay rows, not lifecycle/event/decision weight fields.
- Keep `audit_weight` visibly secondary and non-actionable.
- Keep stacked timeline display-only; Portfolio Performance still consumes daily replay `portfolio_return`.
- Do not add direct lifecycle/trade JSONL reads into render paths.

## Latest Addendum - Dashboard Replay Horizon-Aware Asset Universe Fix

- `CURRENT_DELTA`: `Portfolio & Allocation replay requests now separate current allocation assets from horizon-aware replay context assets; optimizer/PIT loading uses current signed assets while historical lifecycle tickers can appear as zero-weight context-only rows in the same bundle.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `INTEGRITY_DELTA`: `Current allocation remains signed-current-selection only; horizon trade history stays in the same DashboardReplayContext because the replay frame adds historical assets such as MU as zero-weight context-only rows before strict context normalization, and cache signatures bind both replay_assets and allocation_assets.`
- `TEST_DELTA`: `Scoped compile PASS; targeted MU/context/coverage/cache regressions PASS with 4 tests; focused Portfolio/YTD dashboard file PASS with 61 tests; optimizer/replay follow-up PASS with 71 tests.`
- `BOUNDARY`: `No current-allocation universe widening, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, promotion claim, or durable saved-artifact superset policy was added.`
- `NEXT_STEP`: `hold_or_run_saw_gate_for_horizon_asset_universe_fix.`

## New Context Packet - Dashboard Replay Horizon-Aware Asset Universe Fix

## What Was Done

- Added a horizon-aware replay asset union for dashboard replay requests.
- Kept `PortfolioReplaySelection` and `DashboardReplayRequest.allocation_assets` as the current allocation source while widening `DashboardReplayRequest.replay_assets` only for bundle context identity.
- Added zero-weight `context_only` rows for history-only tickers after backend bundle construction.
- Added regressions proving MU BUY/SELL rows remain in the bundle decision context and MU does not become a latest positive-weight holding.

## What Is Locked

- Single-source Portfolio replay remains one `DashboardReplayContext`.
- Context normalization remains strict to replay tickers.
- Current allocation is not widened by historical trade names.
- Coverage pre-gate rows are filtered to current allocation assets, not full PIT membership.
- Cache signatures distinguish context-only horizon assets from current allocatable assets.

## What Is Next

- Hold, or run the formal SAW gate for this focused replay source-scope repair.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q
```

## Next Todos

- Keep horizon-aware request assets aligned between `_build_dashboard_replay_request(...)` and `_current_full_replay_signature(...)`.
- Keep selected PIT loading and coverage pre-gate emission on `allocation_assets`, not widened context assets.
- Do not loosen `_normalize_context_frame(...)` to display out-of-bundle tickers.
- Treat saved-artifact horizon supersets/subsets as a separate explicit backend/dashboard policy.

## Latest Addendum - Replay Selected Price Loading + MU/SNDK Eligibility Trace

- `CURRENT_DELTA`: `Dashboard replay optimization is split from thesis-ticker diagnostics: the batched PIT loader keeps full-window membership proof while loading prices only for signed selected permnos, and MU/SNDK eligibility is traced separately.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `dashboard.py`, `scripts/pit_lifecycle_replay.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_optimizer_view.py`, `tests/test_pinned_universe.py`.
- `PERFORMANCE_DELTA`: `Local probe for 2026-01-02..2026-05-11 proved 27 PIT members but loaded only MU/SNDK price/return matrices, shape 89 x 2, refreshed elapsed 0.5015s.`
- `INTEGRITY_DELTA`: `BatchedPITReplayData.metadata.pit_membership_proof remains full_window_membership_index; selected price loading is selected_permnos intersect PIT membership union, not watchlist-only replay.`
- `DIAGNOSTIC_DELTA`: `MU latest: pinned, permno 53613, PIT-present, local row present, Rule100 history has historical rows but latest gate is technical quality. SNDK latest: pinned, permno 82618, PIT-present, local row present, no Rule100 history rows, latest gate is factor threshold.`
- `TEST_DELTA`: `Focused compile PASS; targeted loader/source/trace regressions PASS, including non-finite return rejection and executable selected-permno handoff; broader affected data-orchestrator/optimizer-view/pinned-universe/strategy-replay/dashboard guard PASS with 112 tests.`
- `BOUNDARY`: `Do not make replay watchlist-only; do not use MU/SNDK trace to alter dashboard replay asset selection; no provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_run_separate_strategy_data_eligibility_investigation_for_mu_sndk.`

## New Context Packet - Replay Selected Price Loading + MU/SNDK Eligibility Trace

## What Was Done

- Added optional `selected_permnos` to `load_batched_pit_replay_data(...)`.
- Preserved full replay-window `r3000_pit` membership index and expected-member proof while shrinking raw price/return loading to selected PIT members.
- Wired dashboard selected-method replay to pass numeric signed replay assets into the batched loader.
- Added `trace_thesis_ticker_eligibility(...)` as a separate strategy/data diagnostic for MU/SNDK gates.
- Reconciled SAW data-integrity feedback by rejecting non-finite `total_ret` rows from local price/return diagnostic evidence.
- Strengthened the dashboard replay test with an executable selected-permno handoff guard, including a non-selected PIT member.
- Wrote local evidence to `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json`.

## What Is Locked

- Full PIT membership proof happens before selected price loading.
- Dashboard replay must stay signed-selection and PIT-governed, not watchlist-only.
- MU/SNDK diagnosis is diagnostic-only and does not change replay universe construction.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or run a separate Strategy/Data eligibility investigation into why MU/SNDK fail Rule100 candidate/history gates.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_pinned_universe.py tests\test_strategy_replay_coverage.py -q
```

## Next Todos

- Keep `metadata["pit_membership_proof"] == "full_window_membership_index"` in the batched loader.
- Keep selected-price narrowing after PIT window membership proof.
- Keep local price/return diagnostics rejecting non-finite return rows.
- Do not route MU/SNDK trace output into dashboard replay request construction.

## Latest Addendum - Dashboard Replay Horizon Superset Cache Fix

- `CURRENT_DELTA`: `Portfolio & Allocation now checks the existing in-session daily replay context before rebuilding, allowing a wider ready daily replay such as Max to serve shorter horizons such as 1Y when it is a proven superset.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `PERFORMANCE_DELTA`: `Switching from a wider replay horizon to a shorter covered horizon avoids the transitional PIT replay rebuild and the Building daily portfolio replay source spinner path.`
- `INTEGRITY_DELTA`: `Superset reuse requires matching method/cap/controls/signed assets/sampling/data signature after excluding replay_dates, and requested dates must exist in both context.replay_dates and replay_df date rows; returned contexts are horizon-scoped.`
- `TEST_DELTA`: `Scoped compile PASS; targeted superset-cache regressions PASS with 3 tests; focused Portfolio/YTD dashboard file PASS with 56 tests; optimizer/replay coverage follow-up PASS with 50 tests.`
- `BOUNDARY`: `Saved artifacts still require exact dashboard_cache_signature; no backend artifact producer change, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_and_saved_artifact_superset_policy.`

## New Context Packet - Dashboard Replay Horizon Superset Cache Fix

## What Was Done

- Added in-session daily replay superset validation before `_ensure_daily_portfolio_replay_context(...)` enters the replay build path.
- Added horizon scoping so reused replay rows, latest snapshot, event rows, decision rows, and date window match the shorter selected horizon.
- Tightened exact-cache reuse to prove actual replay rows cover requested dates.
- Added regressions for superset reuse, missing requested dates, and no-build cache return.

## What Is Locked

- In-session superset reuse is valid only for ready daily contexts with matching non-date replay identity and actual requested-date row coverage.
- Saved replay artifact matching remains exact-signature only.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend `dashboard_cache_signature` emission plus a separate durable saved-artifact superset/subset policy.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q
```

## Next Todos

- Keep `_ensure_daily_portfolio_replay_context(...)` checking `_valid_cached_ytd_replay_context(...)` before the spinner/build path.
- Keep saved artifacts exact until a backend/dashboard subset policy has explicit tests.
- Do not let scoped replay contexts render a wider timeline than the selected horizon.

## Latest Addendum - Max Replay Timeline Sampling Fix

- `CURRENT_DELTA`: `Strategy Replay max-window timeline sampling now uses the pandas Series .dt accessor when normalizing weekly grouped keep-dates.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `INTEGRITY_DELTA`: `Weekly timeline sampling remains display-only from daily replay rows; sampled rows do not feed Portfolio Performance or become a second replay source.`
- `TEST_DELTA`: `Scoped compile PASS; targeted max-window sampler regression PASS with 2 tests; focused Portfolio/YTD dashboard file PASS with 53 tests.`
- `BOUNDARY`: `No backend artifact producer change, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`

## New Context Packet - Max Replay Timeline Sampling Fix

## What Was Done

- Fixed `_sample_replay_timeline_from_daily(...)` so grouped weekly keep-dates are normalized with `.dt.normalize()`.
- Added an executable max-window regression with more than 160 business dates.
- Rechecked the focused Portfolio/YTD dashboard test file.

## What Is Locked

- Strategy Replay Timeline sampling is only a visualization transform over daily replay rows.
- Portfolio Performance must continue to consume daily replay `portfolio_return`, not sampled timeline rows.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend dashboard_cache_signature emission for production saved-artifact UI hits.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q
```

## Next Todos

- Keep the max-window sampler regression in the focused Portfolio/YTD suite.
- Do not reintroduce direct `Series.normalize()` after pandas grouping.
- Keep sampled replay rows out of Portfolio Performance.

## Latest Addendum - Portfolio Replay Selection Identity Hardening

- `CURRENT_DELTA`: `Portfolio replay asset identity is now an explicit signed PortfolioReplaySelection published by optimizer controls and validated by dashboard before replay request construction; signatures include typed asset IDs and selected price content hash.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `views/optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`.
- `INTEGRITY_DELTA`: `Hidden optimizer_universe and first-10 price-column fallback no longer drive replay assets; missing/stale selection fails closed and clears replay/YTD caches.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay-selection/advisory regressions PASS with 6 tests; focused optimizer-selection AppTests PASS with 6 tests.`
- `BOUNDARY`: `No backend artifact producer move, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission_for_aux_rows.`

## New Context Packet - Portfolio Replay Selection Identity Hardening

## What Was Done

- Added `PortfolioReplaySelection` and a signature over controls, typed replay assets, price-frame identity, and selected price content hash.
- Replaced dashboard replay asset lookup from hidden optimizer session state with signed selection validation.
- Removed first-10 price-column fallback from runtime replay request construction.
- Cleared selection/replay caches on optimizer builder error/skipped-data paths.
- Added regressions for missing signed selection, stale signature, builder-error clearing, and optimizer AppTest selection publication.

## What Is Locked

- Replay assets must come from a current signed selection or fail closed.
- `optimizer_universe` is not a replay source.
- First-10 price-column fallback is forbidden for replay identity.
- Aux event/decision producer ownership remains a backend artifact follow-up, not a UI render-surface source split.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend dashboard_cache_signature emission for aux event/decision artifact production.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q
```

## Next Todos

- Keep signed selection as the only replay-universe handoff.
- Do not reintroduce `optimizer_universe` or first-10 fallback as replay source.
- Move aux event/decision producer ownership only in a backend-owned artifact slice.

## Latest Addendum - Portfolio Single-Source Replay Page

- `CURRENT_DELTA`: `Portfolio & Allocation now builds one daily DashboardReplayContext before replay-facing surfaces render; allocation snapshot, Portfolio Performance, Strategy Replay Timeline, ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log consume that one context.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `views/optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_policy_target_timeline_apptest.py`, `tests/test_position_lifecycle.py`.
- `INTEGRITY_DELTA`: `Portfolio Performance refuses non-daily replay and no longer falls back to optimizer weights/local-live/equal-weight paths; weekly timeline sampling is display-only from daily replay rows.`
- `UI_DELTA`: `Top allocation display is latest daily replay snapshot; optimizer panel is controls-only; duplicate Trade Event Log table is removed; Latest Buys/Sells is filtered from bundle.decision_rows.`
- `TEST_DELTA`: `Scoped compile PASS; focused Portfolio/replay/optimizer suite PASS with 178 tests; context build/validation PASS.`
- `BOUNDARY`: `No backend artifact producer change, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `run_saw_reviewer_gate_or_hold_for_backend_dashboard_cache_signature_emission.`

## New Context Packet - Portfolio Single-Source Replay Page

## What Was Done

- Re-orchestrated Portfolio & Allocation so one daily replay context is built before allocation/performance/replay surfaces.
- Replaced the visible allocation panel with the latest daily replay snapshot and made optimizer controls input-only in this page flow.
- Made Portfolio Performance render only from daily replay `portfolio_return`; missing/non-daily replay now shows unavailable.
- Converted weekly Strategy Replay Timeline sampling into a display transform over daily replay rows.
- Removed the duplicate Trade Event Log table while keeping ENTER/EXIT visualization and Buy/Sell Decision Log.
- Added source guards proving latest buys/sells is a filtered view of `bundle.decision_rows` and render paths do not directly read lifecycle JSONL/trade JSONL sources.

## What Is Locked

- Replay-facing Portfolio evidence must share `run_id`, `source_id`, `method_id`, and `date_window`.
- No sampled replay build may drive Portfolio Performance or become a second replay source.
- No optimizer/local/live/equal-weight fallback may masquerade as replay performance.
- Missing event/decision aux rows render empty/unavailable instead of fallback rows.
- No provider ingestion, canonical market-data write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Run/complete SAW reviewer gate if closure is required, then hold or coordinate backend artifact emission of `dashboard_cache_signature`.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q
```

## Next Todos

- Preserve one daily context across all replay-facing Portfolio surfaces.
- Do not reintroduce Trade Event Log table or latest-trades direct loaders.
- Keep transitional build labeled until production saved artifacts carry dashboard cache signatures.

## Latest Addendum - Saved Artifact Single-Source Aux Surface Fix

- `CURRENT_DELTA`: `Saved-artifact DashboardReplayContext construction now preserves artifact event and decision rows exactly, including valid empty frames, instead of backfilling from separately loaded dashboard frames.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `docs/saw_reports/saw_frontend_ui_saved_replay_source_selector_20260514.md`.
- `INTEGRITY_DELTA`: `source_mode="saved_artifact" now means replay rows, latest snapshot, ENTER/EXIT rows, and Buy/Sell rows are all artifact-owned; empty artifact aux surfaces remain empty.`
- `TEST_DELTA`: `Scoped compile PASS; saved-artifact empty aux regression PASS; focused frontend suite PASS with 106 tests.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C returned PASS after the repair; SAW report is mirrored under docs/saw_reports for discoverability.`
- `BOUNDARY`: `No backend reader internals, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`

## New Context Packet - Saved Artifact Single-Source Aux Surface Fix

## What Was Done

- Removed the saved-artifact adapter fallback that filled empty artifact event/decision rows from separately loaded dashboard frames.
- Added a regression where a saved bundle has daily portfolio rows but empty event/decision rows while fallback event/decision frames are non-empty.
- Mirrored the Frontend/UI saved replay source-selector SAW report from `docs/context/` to `docs/saw_reports/`.
- Revalidated scoped compile, focused saved-artifact regressions, the focused frontend suite, context build/validation, and SAW block/closure validation.

## What Is Locked

- `source_mode="saved_artifact"` preserves saved artifact event rows and decision rows exactly, even when empty.
- Empty saved-artifact aux surfaces are not silently mixed with direct dashboard event/decision loads.
- Transitional fallback remains labeled and only applies when the saved artifact itself is unavailable/stale/over-budget and fallback is allowed.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend artifact emission of `dashboard_cache_signature` so production saved artifacts can satisfy the dashboard selector.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact tests\test_dash_2_portfolio_ytd.py::test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows tests\test_dash_2_portfolio_ytd.py::test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback -q
```

## Next Todos

- Keep `source_mode="saved_artifact"` artifact-owned for every replay-facing surface.
- Do not relax dashboard artifact matching to backend-only validation.
- Keep transitional fallback labeled until saved artifacts carry dashboard cache signatures.

## Latest Addendum - Backend Replay Reader Identity Hardening

- `CURRENT_DELTA`: `Saved selected-method replay manifests now reject blank run_id, source_id, and method_id before optional expected IDs or parquet equality can make a bundle look valid.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/strategy_replay.py`, `tests/test_strategy_replay_artifact.py`, `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md`.
- `INTEGRITY_DELTA`: `Manifest identity must be a non-empty string after trimming; matching blank manifest+parquet identity fails closed with manifest_identity_blank:<field>.`
- `TEST_DELTA`: `Scoped compile PASS; targeted blank-identity regression PASS, 3 tests; focused replay suites PASS, 79 tests and durations under budget.`
- `SAW_DELTA`: `Backend SAW report artifact is published so the reader/budget hardening closure is auditable from docs/saw_reports.`
- `BOUNDARY`: `No dashboard.py or optimizer_view.py rewiring, provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`

## New Context Packet - Backend Replay Reader Identity Hardening

## What Was Done

- Added manifest-level non-empty string validation for saved replay `run_id`, `source_id`, and `method_id`.
- Added regressions where manifest and parquet both contain blank identity values and the reader caller omits expected `run_id` / `source_id`.
- Preserved valid artifact reads, replay schema, budget enforcement, and existing selected-method replay semantics.
- Published `docs/saw_reports/saw_backend_replay_reader_identity_hardening_20260514.md` for backend SAW auditability.

## What Is Locked

- Blank manifest identity is invalid even when parquet identity also matches the blank value.
- Optional caller `run_id` / `source_id` checks cannot be the only guard for saved artifact identity.
- Saved replay reads remain display-only and fail closed to unavailable empty replay output.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend artifact emission of `dashboard_cache_signature` so production saved artifacts can satisfy the dashboard selector.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12
```

## Next Todos

- Do not relax manifest identity validation to parquet-only equality.
- Keep saved-reader validation intact before any UI consumption.
- Keep transitional dashboard fallback labeled until saved artifacts carry dashboard cache signatures.

## Latest Addendum - Frontend/UI Saved Replay Source Selector

- `CURRENT_DELTA`: `Dashboard Portfolio & Allocation now selects one DashboardReplayContext from a valid saved artifact when dashboard_cache_signature matches, otherwise from a labeled transitional backend build when fallback is allowed.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`.
- `TEST_DELTA`: `Scoped compile PASS; focused frontend suite PASS with 105 tests.`
- `BOUNDARY`: `No backend reader internals were edited; no provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_coordinate_backend_dashboard_cache_signature_emission.`

## New Context Packet - Frontend/UI Saved Replay Source Selector

## What Was Done

- Extracted pure dashboard replay request construction from `_build_dashboard_strategy_replay_context(...)`.
- Added saved-artifact and backend-bundle adapters into `DashboardReplayContext`.
- Added source selection: valid saved artifact -> `source_mode="saved_artifact"`; unavailable/stale/over-budget artifact -> unavailable when fallback is disabled or labeled `source_mode="transitional_build"` when fallback is allowed.
- Kept YTD latest weights, latest snapshot, Strategy Replay rows, ENTER/EXIT annotations, and Buy/Sell Decision Log on one `DashboardReplayContext`.
- Added executable dashboard-context tests that monkeypatch saved/backend paths and assert replay rows, latest snapshot, event rows, decision rows, source mode, cache signature, and stale state clearing.

## What Is Locked

- Dashboard saved-artifact UI consumption requires exact `dashboard_cache_signature`.
- Cache signatures bind method, max-weight cap, controls, assets, replay dates, sampling, and dashboard data signature.
- Stale saved artifacts cannot reuse prior replay/YTD latest weights.
- Transitional build remains visibly labeled and non-canonical.
- No direct lifecycle JSONL or compact Buy/Sell JSONL reads return to `_render_strategy_replay_section()`.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or coordinate backend artifact emission of `dashboard_cache_signature` so production saved artifacts can satisfy the dashboard selector.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q
```

## Next Todos

- Do not relax dashboard artifact matching to backend-only validation.
- Keep transitional fallback labeled until saved artifacts carry dashboard cache signatures.

## Latest Addendum - Saved Replay Artifact Reader + Budget

- `CURRENT_DELTA`: `Backend selected-method replay now has a saved artifact reader with strict parquet+manifest bundle validation and explicit performance-budget enforcement.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/strategy_replay.py`, `scripts/build_strategy_replay_artifact.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_strategy_replay_coverage.py`.
- `INTEGRITY_DELTA`: `Reader rejects Rule100 candidate content drift, null/blank parquet identity fields, malformed timing, source-signature drift, and manifest/parquet mismatch.`
- `TEST_DELTA`: `Scoped compile PASS; focused replay suites PASS with 76 tests and durations under budget.`
- `BOUNDARY`: `No dashboard.py or optimizer_view.py rewiring in this backend slice; no provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `coordinate_frontend_saved_reader_consumption_or_hold.`

## New Context Packet - Saved Replay Artifact Reader + Budget

## What Was Done

- Added `ReplayBudgetPolicy` and `SelectedMethodReplayResult`.
- Added `read_selected_method_replay_artifact(...)` for saved selected-method replay parquet+manifest bundles.
- Added strict stale-context validation for method, controls, replay dates/window, input signatures, source file signatures, schema, manifest fields, row/status counts, and timing.
- Added DataFrame control content hashing so same-shape/date Rule100 candidate edits invalidate saved artifacts.
- Tightened parquet identity validation for run id, source id, artifact scope, method id, and row type.
- Added `build_selected_method_replay_with_budget(...)` so over-budget builds fail closed without changing `build_selected_method_replay(...)`.
- Updated the selected-output artifact CLI to enforce row/date/elapsed/cold-start budgets.
- Added regressions for valid reads, stale mismatches, manifest/parquet drift, schema drift, source signature drift, and over-budget read/build failures.

## What Is Locked

- Existing replay semantics and `REPLAY_COLUMNS` remain unchanged.
- Saved replay artifacts are display-only evidence under `data/runtime_cache/strategy_replay`.
- Over-budget or invalid artifact reads/builds return unavailable typed results with empty replay output.
- Stale selected-method weights must not be carried forward after unavailable saved reads.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Coordinate a separate frontend/UI slice if dashboard consumption should prefer the saved reader.
- Keep dashboard transitional build behavior unchanged until that slice is explicitly owned.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py -q --durations=12
```

## Next Todos

- Do not reuse prior replay/YTD weights when `SelectedMethodReplayResult.available` is false.
- Preserve saved reader validation before any UI consumption.

## Latest Addendum - Overlay Overlap Anchor Fix

- `CURRENT_DELTA`: `Scaled live overlays now require same-ticker local/live overlap before selected-price or benchmark evidence can use live rows.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `TEST_DELTA`: `Scoped compile PASS; affected stale-data suite PASS with 112 tests after SAW rerun reconciliation.`
- `SAW_DELTA`: `Implementer and Reviewer A/B/C all returned PASS; SAW report is PASS.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`

## New Context Packet - Overlay Overlap Anchor Fix

## What Was Done

- Removed the permissive no-overlap scaled-overlay evidence path from `scale_live_overlay_to_local(...)`.
- Made selected-price live overlays drop live columns that lack same-column local/live overlap.
- Made benchmark live overlays use the same same-ticker overlap anchor before scaling.
- Added regressions for selected no-overlap stale asset dropping and benchmark no-overlap stale ticker dropping.
- Published SAW PASS after Implementer and Reviewer A/B/C all passed.

## What Is Locked

- No overlap anchor means no scaled overlay evidence.
- Stale selected or benchmark assets with local ending `2026-02-27` and live starting `2026-05-01` are unavailable/dropped, not stitched.
- Live overlay remains display-only and non-canonical.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q
```

## Next Todos

- Do not reintroduce no-overlap scaling as allocation, benchmark, or optimizer evidence.
- Preserve no-promotion/no-broker/no-alert boundaries.

## Latest Addendum - Portfolio Market-Data Freshness Endpoint Cache

- `CURRENT_DELTA`: `The fail-closed per-asset freshness layer now has a reusable PriceEndpointFreshness snapshot computed once per loaded prices_wide signature and passed to dashboard YTD, optimizer selected-price prep/default ordering, and optimizer universe eligibility.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `dashboard.py`, `views/optimizer_view.py`, `strategies/portfolio_universe.py`.
- `PERFORMANCE_DELTA`: `Actual local prices_wide shape (2857, 2000): snapshot 0.2966s vs legacy loop 0.9555s, exact endpoint match, downstream 50 lookup reuse 0.001531s.`
- `RECONCILIATION_DELTA`: `Reviewer High findings patched: partial live YTD provider responses missing positive-weight assets now fail closed, replay/YTD latest weights are signature-bound, and cached full replay/YTD contexts are signature-bound before reuse.`
- `TEST_DELTA`: `Focused data-orchestrator/optimizer/universe/dashboard suite PASS with 113 tests; scoped compile PASS.`
- `SAW_DELTA`: `Implementer, Reviewer A recheck, and Reviewer C returned PASS; Reviewer B second targeted recheck is pending after full-context signature fix.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `finish_saw_reviewer_reconciliation_then_hold_or_saved_replay_artifact_reader_budget.`

## New Context Packet - Portfolio Market-Data Freshness Endpoint Cache

## What Was Done

- Added `PriceEndpointFreshness` and `build_price_endpoint_freshness(...)`.
- Made dashboard cache one endpoint snapshot for the loaded local price matrix.
- Passed the snapshot into portfolio YTD, optimizer rendering, and universe construction.
- Made optimizer selected-price prep/default ordering and universe eligibility reuse endpoint data instead of rescanning the full matrix.
- Tightened weighted YTD live fallback so every positive-weight asset must be present before returns are computed.
- Added replay context signatures so stale replay-derived latest weights and full replay/YTD contexts cannot survive method/cap/assets/data drift.
- Added focused regressions proving snapshot reuse and preserved stale fail-closed behavior.

## What Is Locked

- Per-asset endpoint freshness remains fail-closed.
- Cached endpoint snapshots are a performance layer, not a stale-data tolerance change.
- Shared matrix max date is still not proof every selected or weighted asset is fresh.
- Partial provider responses are not valid portfolio performance evidence for nonzero weighted assets that are missing.
- Replay-derived latest weights are valid only under a matching current replay signature.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Complete targeted Reviewer A/B rechecks for this performance slice.
- Then hold, or separately approve saved replay artifact-reader consumption and explicit performance-budget enforcement.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q
```

## Next Todos

- Do not reintroduce repeated full-matrix endpoint scans on render paths.
- Keep `PriceEndpointFreshness` wired through new freshness consumers.
- Preserve no-promotion/no-broker/no-alert boundaries.

## Latest Addendum - Portfolio Market-Data Freshness Fail-Closed Fix

- `CURRENT_DELTA`: `Portfolio & Allocation now gates market-data freshness per asset endpoint across benchmark YTD, portfolio YTD, optimizer selected-price prep, default ordering, and optimizer universe eligibility.`
- `CONTRACT_DELTA`: `Endpoint/tolerance semantics now have one owner: core.data_orchestrator. Universe eligibility imports shared endpoint helpers and passes policy tolerance explicitly.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `dashboard.py`, `views/optimizer_view.py`, `strategies/portfolio_universe.py`.
- `TEST_DELTA`: `Affected stale-data suite PASS with 112 tests after SAW rerun reconciliation; broader affected dashboard/replay suite PASS with 171 tests; scoped compile PASS.`
- `SAW_DELTA`: `Independent SAW rerun completed: Implementer and Reviewer A/B/C all returned PASS with no in-scope Critical/High findings.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion claim was added.`
- `NEXT_STEP`: `hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget.`

## New Context Packet - Portfolio Market-Data Freshness Fail-Closed Fix

## What Was Done

- Added per-column price endpoint helpers and freshness filtering in `core/data_orchestrator.py`.
- Centralized the generic endpoint/tolerance predicate in `core/data_orchestrator.py` and rewired `strategies/portfolio_universe.py` to pass policy tolerance explicitly.
- Made benchmark YTD drop stale benchmark columns that cannot be live-overlaid and report a shared endpoint for remaining curves.
- Made portfolio YTD local fallback unavailable when a nonzero weighted local leg is stale at the required endpoint.
- Made optimizer selected-price prep drop stale selected assets that cannot be refreshed, and made default ordering demote stale endpoint assets.
- Made optimizer universe eligibility exclude stale endpoints even when history observation count is sufficient.
- Added focused regressions for stale benchmark, weighted YTD, overlay, default ordering, selected-price prep, and universe eligibility.

## What Is Locked

- Freshness is per asset: `endpoint_i = max(valid positive price date for asset i)`.
- Endpoint freshness predicate lives in `core.data_orchestrator`; strict callers use default tolerance `0`, policy callers pass tolerance explicitly.
- Shared matrix max dates cannot prove selected/weighted assets are fresh.
- Stale weighted portfolio legs fail closed; stale selected optimizer assets are dropped/excluded with diagnostics.
- Stale selected or benchmark assets with no local/live overlap, for example local ending `2026-02-27` and live starting `2026-05-01`, are dropped rather than scaled from first live to last local as evidence.
- Live overlay remains display-only and non-canonical.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.
- Keep saved replay artifact-reader consumption and performance-budget enforcement as separate future work.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py -q
```

## Next Todos

- Do not re-open shared-date freshness in benchmark, portfolio, optimizer, or universe paths.
- Do not reintroduce private endpoint/tolerance helper clones in `portfolio_universe.py`.
- Preserve no-promotion/no-broker/no-alert boundaries.

## Latest Addendum - Dashboard Backend Bundle Integration Verification

- `CURRENT_DELTA`: `The previously open dashboard backend-bundle consumption risk is closed for the transitional build path: dashboard.py::_build_dashboard_strategy_replay_context(...) calls build_selected_method_replay(...) with a per-date r3000_pit input_loader.`
- `TEST_DELTA`: `Focused replay/dashboard suite PASS; scoped compile PASS; full pytest PASS; Streamlit readiness smoke PASS at http://127.0.0.1:8520/portfolio-and-allocation.`
- `BOUNDARY`: `This is verification/docs closure for backend-bundle consumption only; saved artifact-reader consumption and cold-start/rerun performance budget remain future architecture work. No provider ingestion, broker, alert, ranking, recommendation, scoring, autonomous allocation, or promotion was added.`
- `NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`

## New Context Packet - Dashboard Backend Bundle Integration Verification

## What Was Done

- Verified the dashboard selected-method replay context consumes backend `build_selected_method_replay(...)`.
- Verified the dashboard bundle path uses per-date PIT inputs through `load_strategy_replay_inputs(..., end_date=as_of_date, universe_mode="r3000_pit")`.
- Re-ran focused replay/dashboard checks, full repository pytest, and a fresh Streamlit readiness smoke on `/portfolio-and-allocation`.
- Refreshed truth surfaces to remove stale claims that dashboard backend-bundle integration was still open.

## What Is Locked

- Dashboard Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log, and YTD latest-weight preference share `DashboardReplayContext`.
- Failed or empty replay dates must remain explicit cash/unavailable rows; stale carry-forward is forbidden.
- The current path is still labeled transitional build, not saved artifact-reader consumption.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Hold, or approve saved replay artifact-reader consumption and explicit cold-start/rerun performance-budget enforcement.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_replay_non_cash_closed.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q
```

## Next Todos

- Keep the saved artifact-reader path and performance budget separate from the already verified transitional backend-bundle consumption.
- Preserve no-promotion/no-broker/no-alert boundaries.

## Latest Addendum - Replay Coverage Contract Audit Fix

- `CURRENT_DELTA`: `The SAW audit BLOCK items for v6 replay coverage are resolved in code/tests: coverage_segments metadata, specific unavailable reasons, uncovered-date batch emission, row-heavy no_priced_members performance, duplicate test cleanup, next-return performance alignment, and covered-path performance hardening.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/strategy_replay.py`, `strategies/optimizer.py`, `tests/test_strategy_replay_coverage.py`, `tests/test_optimizer_core_policy.py`.
- `PERFORMANCE_DELTA`: `Daily all-uncovered replay routing no longer builds/attaches/concats one frame per date; row-heavy unavailable rows use fast explicit emission; tiny PIT frames avoid stack/merge overhead; inverse-volatility uses a deterministic feasible-target fast path.`
- `TEST_DELTA`: `Replay coverage PASS 11 tests, affected replay/optimizer PASS 68 tests, context bootstrap PASS 21 tests, context hygiene PASS 24 tests, exact microstructure reviewer line PASS, full pytest PASS.`
- `BOOTSTRAP_DELTA`: `Context bootstrap now treats current truth surfaces as selectable packet sources when they include a complete New Context Packet, so docs/context/current_context.* selects this replay-audit truth instead of the older Rule100/YTD handover.`
- `SAW_DELTA`: `Formal SAW Implementer and Reviewer A/B/C rechecks completed after resume and all passed; SAW report is PASS.`
- `BOUNDARY`: `No provider ingestion, canonical write, broker/live trading, alert, ranking, scoring, recommendation, autonomous allocation, or promotion was added.`
- `NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`

## New Context Packet - Replay Coverage Contract Audit Fix

## What Was Done

- Fixed the replay coverage contract audit findings in `strategies/strategy_replay.py` and `strategies/optimizer.py`.
- Preserved `coverage_segments`, specific `input_unavailable:*` reasons, batched uncovered-date rows, row-heavy `no_priced_members` rows, next-tradable-return performance alignment, run-level loader equity, real `0.0` returns, and inverse-volatility fast-path diagnostics.
- Added context bootstrap selection for current truth surfaces and regressions proving `planner_packet_current.md` can supersede older phase handovers.
- Completed formal SAW Implementer and Reviewer A/B/C rechecks with PASS.
- Rebuilt `docs/context/current_context.*` from this replay-audit packet.
- Preserved D-353 provenance gates and R64.1 dependency hygiene as closed baseline truth.

## What Is Locked

- Replay weights generated from date `t` data earn only the next tradable return, not the return ending at `t`.
- Uncovered or unavailable replay dates remain explicit `cash_closed` / `input_unavailable:*` rows; stale carry-forward is forbidden.
- Current truth surfaces with complete New Context Packets outrank older handovers for bootstrap selection.
- No provider ingestion, canonical write, broker/live trading, alerts, rankings, recommendations, candidate scoring, autonomous allocation, or promotion claims are authorized.

## What Is Next

- Dashboard backend-bundle integration plus full regression/runtime smoke are now verified.
- Hold, or approve saved replay artifact-reader consumption and explicit cold-start/rerun performance-budget enforcement.

## First Command

```text
.venv\Scripts\python -m pytest tests\test_build_context_packet.py tests\test_strategy_replay_coverage.py tests\test_optimizer_core_policy.py -q
```

## Next Todos

- Keep planner, bridge, impact, done, alignment, and observability surfaces aligned to the replay audit truth.
- Preserve saved artifact-reader consumption and performance-budget enforcement as the next product/phase bottleneck.

## Latest Addendum - Selected-Method Replay Source Evidence Handoff

- `CURRENT_DELTA`: `Focused backend and dashboard patches now implement a bounded selected-method replay source path: build_selected_method_replay(...) for backend bundle evidence and DashboardReplayContext for dashboard replay surfaces.`
- `IMPLEMENTED_INVARIANT`: `For focused tested paths, Strategy Replay rows, latest snapshot, ENTER/EXIT annotations, Buy/Sell Decision Log, and Portfolio Performance weight preference share selected-method replay context instead of independent surface reads.`
- `ARTIFACT_DELTA`: `Durable selected-method replay-output artifact/run id support now exists through write_selected_method_replay_artifact_atomic(...), including rollback-safe parquet+manifest promotion under data/runtime_cache/strategy_replay.`
- `TIMEFRAME_PIT_RULE`: `Time horizons are display horizons only; replay evidence must load each date through r3000_pit PIT slices with end_date=as_of_date and explicit cash_closed/unavailable states on failure.`
- `LATEST_TRADES_DEFAULT`: `Buy/Sell Decision Log is latest-first by date and remains replay-audit-only UI context before heavy replay output.`
- `TEST_DELTA`: `Selected-method artifact suite PASS with 16 tests; strategy replay suite PASS with 21 tests; dashboard replay/YTD/optimizer/lifecycle suite PASS with 89 tests.`
- `BOUNDARY`: `Dashboard backend-bundle consumption plus full regression/runtime smoke are now verified; no provider ingestion, broker, alert, ranking, recommendation, or promotion.`
- `NEXT_STEP`: `hold_or_approve_saved_replay_artifact_reader_and_performance_budget.`

## Latest Addendum - Frontend/UI Shared Replay Bundle

- `CURRENT_DELTA`: `Dashboard Strategy Replay surfaces now consume one selected-method DashboardReplayContext for replay rows, latest snapshot, ENTER/EXIT annotations, and Buy/Sell audit rows.`
- `YTD_DELTA`: `Portfolio Performance primes the latest selected-method replay snapshot and prefers those weights before legacy optimizer fallback.`
- `TEST_DELTA`: `Focused dashboard/optimizer replay suite passes: 89 tests.`
- `BOUNDARY`: `Frontend adapter only at the time; the later backend artifact/run-id handoff closed durable output support, and 2026-05-14 verification closed transitional dashboard backend-bundle consumption. No provider ingestion, canonical write, broker, alert, ranking, scoring, or recommendation was added.`
- `NEXT_STEP`: `backend_replay_output_artifact_or_hold.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Enforcement

- `CURRENT_DELTA`: `Docs/Ops now treats the ultra-modular replay milestone as a strict selected-method replay-source invariant, not just a planning note.`
- `NON_NEGOTIABLE_INVARIANT`: `For any selected method, YTD, current allocation/latest snapshot, Strategy Replay, ENTER/EXIT annotations, Buy/Sell Decision Log, and saved evidence must come from one replay run/source.`
- `ARCHITECTURE_GOAL`: `selected-method adapter -> one replay run -> daily portfolio output -> event/annotation output -> YTD/performance -> decision log -> saved evidence artifact.`
- `TRANSITIONAL_BRIDGE_DELTA`: `Temporary UI/data bridges are allowed only as labeled, bounded, non-canonical migration aids; they cannot become a second replay stack or evidence source.`
- `GUARDRAIL_DELTA`: `No future-data leakage, stale-data carry-forward, fake improvements, overfitting, broker/live trading, alerts, rankings, recommendations, candidate scoring, or autonomous allocation.`
- `DONE_GATE_DELTA`: `Machine-checkable implementation closure must prove shared replay source, selected-method adapters, shared YTD/performance, shared annotation source, shared decision log source, saved evidence artifact, and performance budget.`
- `BOUNDARY`: `This Worker 3 slice is docs-only and does not implement the shared replay source.`
- `NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice_with_single_selected_method_replay_source.`

## Latest Addendum - Visible Rule100 / QQQ / Buy-Sell Replay Audit

- `CURRENT_DELTA`: `Focused visible Portfolio & Allocation fixes are implemented and runtime-audited.`
- `VISIBLE_AUDIT`: `http://localhost:8509/ shows Rule of 100 selected, max_weight=0.35, SPY +11.07%, QQQ +15.50%, and Buy/Sell Decision Log (29 trades, replay audit only) with BUY 16 / SELL 13.`
- `SORT_DELTA`: `Default optimizer asset ordering uses trailing 1-year return instead of YTD/current display order.`
- `BOUNDARY`: `Buy/Sell Decision Log is replay/audit context only; no live orders, trade signals, alerts, rankings, recommendations, provider ingestion, broker behavior, or autonomous optimizer behavior.`
- `OPEN_RISK`: `Full YTD forward-walk replay cold-start cost remains; address under the ultra-modular replay architecture milestone.`
- `NEXT_STEP`: `start_urgent_ultra_modular_replay_architecture_slice.`

## Latest Addendum - Urgent Ultra-Modular Replay Architecture Milestone Note

- `CURRENT_DELTA`: `The current work remains a focused Portfolio & Allocation visible patch for QQQ/YTD/default-method/Rule100 parity; the ultra-modular replay architecture is queued as the next milestone, not blended into this patch.`
- `ARCHITECTURE_DELTA`: `Target contract is one replay engine, one strategy plug-in contract, one daily portfolio output format, one event/annotation format, one YTD/performance path, and one saved evidence artifact.`
- `RESEARCH_LOOP_DELTA`: `The loop is endless AI-assisted research evidence generation and review, not unchecked optimization, live trading, broker automation, alerting, ranking, or recommendation output.`
- `GUARDRAIL_DELTA`: `No future-data leakage; stale data fails closed; overfitting controls require same-window/same-cost/same-engine deltas vs latest baseline; fake improvement claims are rejected without replayable artifact evidence.`
- `ACCEPTANCE_DELTA`: `Rule100 dynamic UI/replay sizing and QQQ/YTD stale-overlay fixes are acceptance tests for starting the modular replay milestone.`
- `BOUNDARY`: `No code files are changed by this architecture note; no provider ingestion, broker behavior, alerts, live trading, ranking/scoring, or autonomous optimizer behavior is authorized.`
- `NEXT_STEP`: `manual_audit_qqq_ytd_and_default_method_visible_fixes_then_start_urgent_ultra_modular_replay_architecture.`

## Latest Addendum - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

- `CURRENT_DELTA`: `The visible Rule of 100 path now uses a dynamic UI/replay config derived from controls.max_weight instead of the frozen 10% audit budget.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/rule100_softmax.py`, `strategies/strategy_replay.py`, `views/optimizer_view.py`, `core/data_orchestrator.py`, `dashboard.py`, `tests/test_rule100_softmax.py`, `tests/test_strategy_replay.py`, `tests/test_optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_policy_target_timeline_apptest.py`.
- `SIZING_DELTA`: `rule100_config_from_max_weight(0.35)` gives `gross_budget_per_name=0.35`, `max_single_name_weight=0.35`, and `gross_budget_cap=1.0`; two equal eligible names become 35%/35%/30% cash.
- `AUDIT_DELTA`: `Rule100SoftmaxConfig()` remains frozen at 10% budget / 15% cap; no frozen history artifact was rewritten.
- `YTD_DELTA`: `build_benchmark_equity_from_prices(...)` checks benchmark freshness per ticker, live-overlays stale/missing tickers only, and drops stale columns that cannot be refreshed instead of forward-filling them flat.
- `TEST_DELTA`: `Focused Rule100/replay/YTD/AppTest suite, broader affected suite, full pytest, context validation, and Streamlit readiness pass.`
- `BOUNDARY`: `No canonical market-data write, provider ingestion, history artifact rewrite, ranking/scoring, alert, broker behavior, live trading, or new optimizer objective.`
- `NEXT_STEP`: `manual_audit_rule100_visible_weights_and_qqq_ytd_then_hold_or_versioned_history_artifact.`

## Latest Addendum - Data/PIT Strategy Replay Hardening + UI Wiring

- `CURRENT_DELTA`: `Strategy Replay inputs now fail closed on r3000_pit universe membership at the cache-signature and loader boundaries.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `dashboard.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_strategy_replay_artifact.py`, `tests/test_optimizer_view.py`, `tests/test_position_lifecycle.py`, `tests/test_policy_target_timeline_apptest.py`.
- `DATA_DELTA`: `Display-only replay input artifacts are confined to data/runtime_cache/strategy_replay; data/processed cache-dir escapes are rejected.`
- `UI_DELTA`: `Portfolio & Allocation Strategy Replay now builds target weights from per-date StrategyReplayInputs instead of a raw global prices_wide matrix.`
- `RECONCILIATION_DELTA`: `Empty PIT slices and per-date PIT input exceptions now emit visible cash_closed rows rather than dropping dates or aborting the full replay section.`
- `TEST_DELTA`: `Focused 93-test suite and broader 179-test affected suite pass.`
- `BOUNDARY`: `Input artifacts are not replay output artifacts; no provider ingestion, canonical market-data write, ranking/scoring, alert, broker behavior, live trading, or new optimizer objective.`
- `NEXT_STEP`: `hold_or_collect_strategy_replay_multi_date_output_evidence.`

## Latest Addendum - Rule100 Softmax v1.1 Contract Fix

- `CURRENT_DELTA`: `Rule100 softmax v1.1 is now aligned to the approved research contract: comparison/summary only, no active v1.1 history artifact.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/rule100_softmax_v1_1.py`, `scripts/rule100_softmax_v1_1_audit.py`, `tests/test_rule100_softmax_v1_1.py`, `tests/test_policy_target_timeline_apptest.py`.
- `DATA_DELTA`: `data/processed/rule100_softmax_v1_1_comparison.csv` and summary were refreshed; stale history moved to `data/processed/rule100_softmax_v1_1_history.retired.csv`.
- `SCORING_DELTA`: `factor_present_count` is now 4-group coverage; missing factor strength shrinks toward neutral 0.50.
- `TEST_DELTA`: `AppTest.from_file("dashboard.py")` proves the real dashboard renders TSM 2026-05-11 target 0%, event weight 10%, cash 80%, reason `tighten_below_hold_threshold`.
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and SAW Implementer/Reviewer A/B/C passes completed.`
- `BOUNDARY`: `v1.1 remains research-only; no runtime promotion, lifecycle log mutation, provider ingestion, ranking, scoring, alert, broker, or new optimizer objective.`
- `NEXT_STEP`: `hold_or_collect_v1_1_multi_date_shadow_evidence.`

## Latest Addendum - Rule of 100 Method Label

- `CURRENT_DELTA`: `Position Lifecycle Replay history now shows a Rule100 softmax v1 target-weight overlay beside immutable v0 event weights.`
- `IMPLEMENTATION_ARTIFACTS`: `scripts/rule100_softmax_v1_audit.py`, `dashboard.py`, `tests/test_rule100_softmax.py`, `tests/test_position_lifecycle.py`, `data/processed/rule100_softmax_v1_history.csv`.
- `UI_DELTA`: `Transaction Log columns are Event Weight, Softmax v1 Target, Softmax v1 Cash, V1 Eligibility, Rating, and Reason.`
- `STATE_DELTA`: `History overlay source is rule100_softmax_v1_history; lifecycle log and compact buy/sell log are not overwritten.`
- `CURRENT_STATE_DELTA`: `2026-05-11 TSM has event weight 10%, softmax v1 target 0%, and cash residual 80%.`
- `BOUNDARY`: `No lifecycle log mutation, broker behavior, alert, ranking, provider ingestion, new optimizer objective, or Kelly stack expansion.`
- `NEXT_STEP`: `manual_audit_lifecycle_history_overlay_then_decide_score_richness.`

## Previous Addendum - Rule of 100 Method Label

- `CURRENT_DELTA`: `Portfolio Optimizer Method dropdown now includes the exact label Rule of 100.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/optimizer.py`, `views/optimizer_view.py`, `tests/test_optimizer_view.py`, `tests/test_portfolio_universe.py`.
- `UI_DELTA`: `Selecting Rule of 100 routes to PIT softmax v1 target weights for eligible lifecycle holds, not lifecycle last_weight.`
- `STATE_DELTA`: `portfolio_allocation_state.source is rule100_softmax_v1 for the explicit Rule of 100 path; YTD consumes those weights through the existing allocation state.`
- `CURRENT_STATE_DELTA`: `Current live target is AMAT 10%, LRCX 10%, TSM 0%, CASH 80%; TSM remains visible in candidate context but is not sizing_eligible.`
- `EMPTY_STATE_DELTA`: `If no lifecycle holds are softmax-eligible, Rule of 100 renders cash-only state rather than falling back to stale last_weight.`
- `BOUNDARY`: `This is a label/routing fix only; no new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, live trading, or generic strategy framework.`
- `RUNTIME_DELTA`: `Port 8509 was restarted and a headless browser smoke confirmed the Method dropdown options include Rule of 100.`
- `NEXT_STEP`: `review_rule100_softmax_v1_live_weights_then_decide_score_richness.`

## Latest Addendum - Portfolio Allocation State Split + Route Smoke

- `CURRENT_DELTA`: `Portfolio & Allocation now stores explicit allocation state for optimizer output, cash-only fallback, current-hold replay, and Rule of 100 replay output.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `views/page_registry.py`, `views/optimizer_view.py`, `tests/test_dash_1_page_registry_shell.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`.
- `UI_DELTA`: `Optimizer output and lifecycle replay output are labeled separately; the visible Portfolio page remains the default page while the explicit portfolio-and-allocation path resolves directly.`
- `STATE_DELTA`: `portfolio_allocation_state carries mode/source/weights/cash_only/latest_price_date; legacy optimizer_* mirrors remain for compatibility.`
- `RUNTIME_DELTA`: `AppTest.from_file("dashboard.py")` with `query_params["page"]="portfolio-and-allocation"` renders the Portfolio page and current-hold replay output without exception.`
- `BOUNDARY`: `No new optimizer objective, ranking, scoring, alert, broker behavior, provider ingestion, or live trading is authorized.`
- `NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck.`

## Latest Addendum - Rule100 Lifecycle Policy v0

- `CURRENT_DELTA`: `Rule100 Lifecycle Policy v0 is promoted in the PIT replay path without introducing a generic strategy framework.`
- `IMPLEMENTATION_ARTIFACTS`: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_log.jsonl`, `data/portfolio_lifecycle_decision_log.jsonl`, `data/portfolio_lifecycle_buy_sell_log.jsonl`, `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`, `docs/context/e2e_evidence/rule100_v0_lifecycle_replay_tmp.jsonl`.
- `POLICY_DELTA`: `Rule100State adapter exposes demand/supply/pricing/margin proxies with provenance; BUY requires 3/4 factors + technical zone + 3-day confirmation; HOLD tolerates 2/4; TIGHTEN and TRIM are audit-only; EXIT requires hard stop >20% or confirmed trend veto.`
- `SIZING_DELTA`: `Entry target weight = min(0.10 + 0.025 * max(0, factor_positive_count - 3), 0.15); current data has no 4/4 entries, so promoted ENTER weights remain 0.10.`
- `AUDIT_DELTA`: `Runtime events changed from 33 to 29; BUY 18->16; SELL 15->13; HOLD 993->739; new TRIM=55 and TIGHTEN=257 audit rows; open holds remain AMAT/LRCX/TSM; no <=5-day round trips.`
- `BOUNDARY`: `No generic strategy contract, provider ingestion, canonical writes, broker orders, alerts, ranking, scoring, dashboard recommendation labels, or Phase 54 Rule-of-100 sleeve reopen.`
- `NEXT_STEP`: `audit_rule100_v0_delta_then_decide_whether_trim_tighten_should_affect_weights.`

## Latest Addendum - Lifecycle Decision Export

- `CURRENT_DELTA`: `PIT lifecycle replay now has an enriched decision export for audit before the real Rule-of-100 policy build.`
- `IMPLEMENTATION_ARTIFACTS`: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_decision_log.jsonl`, `data/portfolio_lifecycle_buy_sell_log.jsonl`, `docs/context/e2e_evidence/lifecycle_decision_audit_20260512.json`.
- `BEHAVIOR_DELTA`: `Export-only mode records BUY/SELL/HOLD/NO_ACTION analysis rows without appending duplicate ENTER/EXIT events to the current lifecycle log.`
- `AUDIT_DELTA`: `Decision tape has 5424 ticker-date rows, 33 BUY/SELL rows, 18 BUY, 15 SELL, open AMAT/LRCX/TSM, and no <=5-day round trips.`
- `RISK_DELTA`: `Audit flags 389 held ticker-days with factor deterioration but no full exit, 33 raw exits suppressed by hold/confirmation guards, and 45 entry days delayed by confirmation.`
- `BOUNDARY`: `BUY/SELL fields are replay-analysis labels only; no broker order, alert, ranking, scoring, provider ingestion, canonical write, or dashboard recommendation is authorized.`
- `NEXT_STEP`: `audit_decision_tape_then_design_true_rule100_lifecycle_policy.`

## Latest Addendum - Lifecycle Replay Churn + Weight Policy

- `CURRENT_DELTA`: `PIT lifecycle replay now has both the drop-in 10% sizing fix and the optimal PIT four-vector confirmation/state-machine fix.`
- `IMPLEMENTATION_ARTIFACTS`: `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`, `data/portfolio_lifecycle_log.jsonl`, `docs/context/e2e_evidence/optimal_lifecycle_replay_tmp.jsonl`.
- `BEHAVIOR_DELTA`: `Current Portfolio & Allocation state is not sell-all: open lifecycle holds are AMAT, LRCX, and TSM, each at 10%, with residual cash preserved.`
- `FORMULA_DELTA`: `ENTER = raw PIT entry gate + 3-of-4 present-positive lifecycle factors + 3-day confirmation + no cooldown; EXIT = hard 20% stretch OR raw exit with 20-day min hold and 2-day confirmation; cooldown = 10 days.`
- `EVIDENCE_DELTA`: `Events reduced from 103 pre-fix to 69 drop-in to 33 optimal; ENTER weights changed from 0.04 to 0.10; no <=5-day round trips in final replay.`
- `UI_DELTA`: `Port 8509 smoke shows AMAT/LRCX/TSM/CASH current holdings and YTD traces for Portfolio/SPY/QQQ via local benchmark fallback.`
- `YTD_FIX_DELTA`: `core.data_orchestrator price/return slot order is fixed; Portfolio YTD no longer compounds daily returns as prices and now displays +14.25% instead of +7645112.18%.`
- `CLOSURE_DELTA`: `Focused tests, full pytest, context validation, HTTP readiness, and headless browser smoke passed; independent SAW subagent ownership remains pending unless explicitly authorized.`
- `BOUNDARY`: `No Phase 54 Rule-of-100 sleeve reopen, ranking, scoring, optimizer objective change, provider ingestion, canonical write, alert, broker, conviction mode, or Black-Litterman.`
- `NEXT_STEP`: `manual_audit_portfolio_allocation_on_8509_then_hold_or_lifecycle_ledger_policy.`

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

- `CURRENT_DELTA`: `Portfolio & Allocation now treats Position Lifecycle Replay as the authority for current open holdings before rendering sell-all cash.`
- `IMPLEMENTATION_ARTIFACTS`: `data/portfolio_lifecycle_log.py`, `strategies/portfolio_universe.py`, `views/optimizer_view.py`, `dashboard.py`, `tests/test_position_lifecycle.py`, `tests/test_portfolio_universe.py`, `tests/test_optimizer_view.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `BEHAVIOR_DELTA`: `Open lifecycle ENTER positions without later PIT-safe EXIT events render as lifecycle holds plus residual cash when there are no fresh PIT ENTER candidates today.`
- `PIT_DELTA`: `Future-dated lifecycle rows are ignored; lifecycle replay overrides stale JSON position memory when replay evidence exists.`
- `CLOSURE_DELTA`: `Focused compile, 58-test portfolio/lifecycle suite, full pytest, browser smoke, context validation, SAW report validation, closure packet validation, and SE evidence validation passed.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, broker call, alert, ranking, scoring, new optimizer objective, conviction mode, or Black-Litterman.`
- `NEXT_STEP`: `hold_or_review_lifecycle_position_accounting_policy.`

## Latest Addendum - Pinned Strategy Universe Hardening

- `CURRENT_DELTA`: `PINNED_STRATEGY_UNIVERSE_HARDENING enforces explicit thesis-ticker inclusion in feature generation and PIT replay with fail-closed loader, shared eligibility gate, and regression tests.`
- `IMPLEMENTATION_ARTIFACTS`: `data/universe/pinned_thesis_universe.yml`, `data/universe/loader.py`, `data/feature_store.py`, `scripts/pit_lifecycle_replay.py`, `tests/test_pinned_universe.py`.
- `DATA_DELTA`: `10 thesis tickers (MU, AMD, AVGO, TSM, INTC, LRCX, SNDK, WDC, NVDA, AMAT) are pinned into feature universe regardless of liquidity ranking. yahoo_patch backfilled for all. PIT replay produces 103 events across 12 tickers. NVDA explicitly FAILED_GATE (not silently dropped).`
- `INVARIANT_DELTA`: `Manifest missing/broken → build aborts (not warning). Replay raises on loader failure (not fallback). Unresolved permno → ValueError. Incremental no-op checks pinned coverage before returning. Shared is_pit_eligible()/is_pit_exit() used by both replay and diagnostics. 27 regression tests enforce no-silent-exclusion.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring, alert, broker, optimizer objective change, or candidate-card dashboard merge.`
- `NEXT_STEP`: `evaluate_nvda_fundamental_gate_or_stream2_strategy_review_or_hold.`

## Latest Addendum - Frontend 3-Page Navigation Refactor

- `CURRENT_DELTA`: `FRONTEND_3_PAGE_NAV_REFACTOR replaces 8-page shell with 3 views: Portfolio & Allocation, Discovery & Analysis, Entry/Exit Strategy.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `views/page_registry.py`, `views/discovery_view.py`, `views/strategy_view.py`, `tests/test_dash_1_page_registry_shell.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `NAVIGATION_DELTA`: `Sidebar now shows 3 pages. Portfolio includes optimizer+shadow+YTD+data-health+drift. Discovery composes opportunities+confluence. Strategy composes modular-strategies+backtest-lab.`
- `CLOSURE_DELTA`: `24 DASH tests and 70 broader tests pass; no regressions.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring, alert, broker, optimizer objective change, or candidate-card dashboard merge.`
- `NEXT_STEP`: `hold_or_approve_dead_code_cleanup_or_next_phase.`

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

- `CURRENT_DELTA`: `DASHBOARD_UNIFIED_DATA_CACHE_PERFORMANCE_FIX caches the expensive dashboard unified parquet package across Streamlit reruns.`
- `IMPLEMENTATION_ARTIFACTS`: `dashboard.py`, `core/data_orchestrator.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dashboard_sprint_a.py`.
- `PERFORMANCE_DELTA`: `Pre-fix direct load measured 8.802s and 8.393s; reruns now reuse st.cache_resource unless source parquet path/mtime/size signatures change.`
- `CLOSURE_DELTA`: `Focused compile/tests, portfolio regressions, full pytest, Streamlit HTTP smoke, context validation, and independent SAW Implementer/Reviewer A/B/C passes completed.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, scanner semantic change, alpha-engine loop rewrite, ranking, scoring, alert, broker, optimizer objective change, or candidate-card dashboard merge.`
- `NEXT_STEP`: `hold_or_measure_alpha_backtest_runtime_or_scanner_financial_cache.`

## Latest Addendum - Dashboard Scanner Testability Hardening

- `CURRENT_DELTA`: `DASHBOARD_SCANNER_TESTABILITY_HARDENING extracts deterministic scanner math into strategies/scanner.py and adds focused boundary tests.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/scanner.py`, `dashboard.py`, `tests/test_scanner.py`, `tests/test_adaptive_trend.py`, `tests/test_production_config.py`, `tests/test_core_etl.py`, `tests/test_strategy.py`, `tests/conftest.py`.
- `BOUNDARY_DELTA`: `dashboard.py keeps provider/cache/persistence ownership; scanner enrichment is importable and testable without Streamlit.`
- `CLOSURE_DELTA`: `Focused compile, affected 49-test suite, full pytest, SAW Reviewer C final recheck, and test-evidence refresh passed.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, scanner semantic change, strategy search, ranking, scoring policy change, alert, broker, dashboard redesign, or candidate-card dashboard merge.`
- `NEXT_STEP`: `continue_review_or_hold`.

## Latest Addendum - Dashboard Architecture Safety Slice

- `CURRENT_DELTA`: `DASHBOARD_ARCHITECTURE_SAFETY_SLICE is implemented as runtime safety and duplication cleanup.`
- `IMPLEMENTATION_ARTIFACTS`: `utils/process.py`, `dashboard.py`, `data/updater.py`, `scripts/parameter_sweep.py`, `scripts/release_controller.py`, `backtests/optimize_phase16_parameters.py`, `tests/test_process_utils.py`.
- `BOUNDARY_DELTA`: `Process liveness has one shared Windows-safe helper; dashboard backtest spawn fails closed on live PID file; dashboard matrix init has one helper path; dashboard portfolio price cleanup delegates to data orchestration.`
- `CLOSURE_DELTA`: `Focused compile/tests, HTTP smoke, and independent SAW Implementer/Reviewer A/B/C passes completed; full pytest timed out and is not phase-close proof.`
- `BOUNDARY`: `No provider ingestion, canonical market-data write, dashboard content redesign, strategy search, ranking, scoring, alert, broker, or candidate-card dashboard merge.`
- `NEXT_STEP`: `continue_code_quality_review_section_or_hold`.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

- `CURRENT_DELTA`: `PORTFOLIO_OPTIMIZER_VIEW_PERF_HARDENING is implemented for /portfolio-and-allocation as tests/performance work.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `views/optimizer_view.py`, `tests/test_optimizer_view.py`, `tests/test_optimizer_core_policy.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `TEST_DELTA`: `Streamlit AppTest now covers optimizer view render, mean-variance control selection, and sector-cap UI paths; optimizer policy tests cover UI-derived bounds through real SLSQP.`
- `PERFORMANCE_DELTA`: `Recent close overlays load from display-only Parquet cache and refresh in background on cold/stale misses; optimizer runs are cached by selected price frame and user parameters.`
- `CLOSURE_DELTA`: `Focused/full/context/runtime verification passed; independent SAW Implementer and Reviewer A/B/C rerun passed.`
- `BOUNDARY`: `No canonical provider ingestion, market-data write, lower-bound policy, new objective, MU conviction, WATCH investability, Black-Litterman, alert, broker, ranking, scoring, or candidate-card dashboard merge.`
- `NEXT_STEP`: `hold_or_measure_next_dashboard_runtime_bottleneck_or_approve_portfolio_thesis_anchor_policy_planning`.

## Latest Addendum - Portfolio Data Boundary Refactor

- `CURRENT_DELTA`: `PORTFOLIO_DATA_BOUNDARY_REFACTOR is implemented for /portfolio-and-allocation as architecture hygiene.`
- `IMPLEMENTATION_ARTIFACTS`: `core/data_orchestrator.py`, `views/optimizer_view.py`, `tests/test_data_orchestrator_portfolio_runtime.py`, `tests/test_dashboard_sprint_a.py`, `tests/test_dash_2_portfolio_ytd.py`.
- `BOUNDARY_DELTA`: `views/optimizer_view.py no longer imports yfinance or parses data/backtest_results.json; data orchestration owns selected-stock display-refresh overlay, duplicate-safe cell-wise stitching, stale-while-revalidate display cache behavior, scheduler fail-soft handling, and metrics parsing.`
- `CLOSURE_DELTA`: `Focused compile, data-orchestrator/dashboard/DASH/provider-port tests, portfolio regression, optimizer diagnostics regression, full pytest, context validation, runtime smoke, and SAW Implementer/Reviewer A/B/C rechecks passed.`
- `BOUNDARY`: `No canonical provider ingestion, market-data write, optimizer objective change, MU conviction, WATCH investability, Black-Litterman, alert, broker, ranking, scoring, or candidate-card dashboard merge.`
- `NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold`.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

- `CURRENT_DELTA`: `OPTIMIZER_CORE_STRUCTURED_DIAGNOSTICS_IMPLEMENTATION is approved and implemented as diagnostics-only optimizer-core work.`
- `IMPLEMENTATION_ARTIFACTS`: `strategies/optimizer_diagnostics.py`, `strategies/optimizer.py`, `views/optimizer_view.py`, `tests/test_optimizer_core_policy.py`.
- `DIAGNOSTIC_DELTA`: `Pre-solver feasibility, equal-weight boundary warnings, SLSQP failure status, active-bound counts, full-investment residuals, and labeled fallback status are now structured and UI-safe.`
- `CLOSURE_DELTA`: `SAW PASS after non-finite diagnostic weights were made fail-closed.`
- `BOUNDARY`: `No MU conviction, WATCH investability expansion, Black-Litterman, simple tilt, new optimizer objective, scanner rule, manual override, provider ingestion, alert, broker, or replay behavior.`
- `NEXT_STEP`: `approve_portfolio_thesis_anchor_policy_planning_or_hold`.

## Latest Addendum - Optimizer Core Policy Audit

- `CURRENT_DELTA`: `OPTIMIZER_CORE_POLICY_AUDIT was opened as docs/tests-first policy work; no optimizer implementation changes were made.`
- `AUDIT_ARTIFACTS`: `docs/architecture/optimizer_core_policy_audit.md`, `docs/architecture/optimizer_constraints_policy.md`, `docs/architecture/optimizer_lower_bound_slsqp_policy.md`, `tests/test_optimizer_core_policy.py`.
- `AUDIT_DECISION`: `Quarantined lower-bound/SLSQP diff is rejected as-is; future revision requires policy approval, infeasibility tests, diagnostics, and separate SAW.`
- `BOUNDARY`: `Do not merge lower-bound implementation, MU conviction, WATCH investability, Black-Litterman, universe eligibility, scanner behavior, provider ingestion, alerts, or broker paths.`
- `NEXT_STEP`: `hold_optimizer_core_implementation_until_policy_approval`.

## Latest Addendum - Portfolio Universe Quarantine Closure

- `CURRENT_RUNTIME_DELTA`: `Portfolio Universe Construction Fix is PASS after quarantining and reverting the out-of-scope strategies/optimizer.py lower-bound/SLSQP diff.`
- `QUARANTINE_ARTIFACT`: `docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch`
- `CLOSURE_STATUS`: `SAW Verdict PASS; ClosurePacket 9/9; strategies/optimizer.py has no active diff.`
- `BOUNDARY`: `Optimizer-core math is not accepted; lower bounds, SLSQP fallback policy, active-bound reporting, MU conviction, WATCH investability, and Black-Litterman remain separate audit/future work.`
- `NEXT_STEP`: `Open OPTIMIZER_CORE_POLICY_AUDIT or hold.`

## Latest Addendum - Portfolio Universe Construction Fix

- `CURRENT_RUNTIME_DELTA`: `Portfolio Optimizer defaults are now built by strategies/portfolio_universe.py rather than dashboard display order.`
- `ELIGIBILITY_LOGIC`: `ENTER STRONG BUY and ENTER BUY are optimizer-eligible; WATCH is research-only; EXIT/KILL/AVOID/IGNORE are default-excluded.`
- `DIAGNOSTIC_LOGIC`: `Universe Audit and Why This Allocation panels expose included/excluded names, missing mappings, price-history failures, thesis-neutral status, and max-weight feasibility.`
- `BOUNDARY`: `No MU hard floor, conviction mode, Black-Litterman, thesis anchor sizing, manual override, scanner rewrite, provider ingestion, broker call, alert, or new portfolio objective is authorized.`
- `NEXT_STEP`: `Approve thesis-anchor policy or hold; do not implement conviction math until that policy exists.`

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

- `CURRENT_RUNTIME_DELTA`: `Portfolio & Allocation now renders Portfolio Optimizer first, then YTD Performance vs SPY/QQQ.`
- `RETURN_LOGIC`: `Portfolio YTD uses current optimizer weights when available; equal-weight local TRI remains fallback only.`
- `FRESHNESS_LOGIC`: `Selected stock and benchmark prices use in-memory adjusted-close yfinance overlay for display freshness; latest browser-observed date was 2026-05-08.`
- `BOUNDARY`: `This does not authorize provider ingestion, canonical evidence changes, broker calls, alerts, ranking/scoring, or candidate-card dashboard merge.`
- `NEXT_STEP`: `Run SAW/report closeout for DASH-2 slice or proceed to the next explicitly approved dashboard runtime slice.`

## Header

- `PACKET_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-planner`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `D-353 A-E complete + R64.1 closed + Phase F/G0/G1/G2/G3/G4/G5/G6/G7/G7.1/G7.1A/G7.1B/G7.1C/G7.1D/G7.1E/G7.1F/G7.1G/G7.2/G7.3/G7.4/G8/G8.1/G8.1A/G8.1B-R/DASH-1 complete + G8.2 current`
- `OWNER`: `PM / Architecture Office`

## Current Context

### What System Exists Now

- Quant has executable provenance gates, provider-port conventions, public-source fixture pillars, G7.2 state machine, G7.3 source eligibility map, G7.4 dashboard product-state spec, one MU human-nominated candidate card, one G8.1 static user-seeded discovery intake queue, G8.1A origin-governance discipline, one MSFT `LOCAL_FACTOR_SCOUT` output, DASH-1 page registry/sidebar shell, and one MSFT system-scouted candidate card.

### Active Scope

- G8.2 is Data + Docs/Ops candidate-card-only work: MSFT static card, manifest, validator guardrail, policy, handover, focused tests, truth surfaces, and SAW.

### Blocked Scope

- New scout output, DELL/AMD/LRCX/ALB cards, G9 signal card, dashboard card reader, provider ingestion, alerts, broker calls, candidate ranking, candidate scoring, buy/sell/hold output, factor-model validation, and dashboard runtime merge remain blocked.

## Active Brief

### Current Phase/Round

- Phase 65 G8.2 System-Scouted Candidate Card (`PH65_G8_2_ONE_CARD_ONLY`)
- Authority: `G8.2`
- Active brief: `docs/phase_brief/phase65-brief.md`
- Canonical handover: `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`

### Goal

- Convert exactly one system-scouted intake item into a non-promotional candidate card.

### Non-Goals

- No new scout output, no DELL/AMD/LRCX/ALB card, no ranking, no scoring, no buy/sell/hold, no buying range, no thesis validation, no dashboard runtime behavior, no provider ingestion, no alerts, no broker calls.

### Owned Files

- `opportunity_engine/candidate_card_schema.py`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- `tests/test_g8_2_system_scouted_candidate_card.py`
- `scripts/build_context_packet.py`
- `tests/test_build_context_packet.py`
- `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`
- Current truth surfaces and governance logs.

### Bridge Truth

- `SYSTEM_DELTA`: MSFT can now move from governed `LOCAL_FACTOR_SCOUT` intake to a structured candidate-card-only research object.
- `PM_DELTA`: The discovery proof now covers both human-nominated MU and pipeline-scouted MSFT cards, while keeping both non-actionable.
- `OPEN_DECISION`: approve G9 one market-behavior signal card, approve G8.3 one user-seeded candidate card, approve dashboard card reader/status shell, or hold.
- `RECOMMENDED_NEXT_STEP`: `approve_g9_one_market_behavior_signal_card_or_g8_3_one_user_seeded_candidate_card_or_dash_card_reader_or_hold`.
- `DO_NOT_REDECIDE`: G8.2 creates no score, rank, buy/sell/hold, buying range, validation, alert, broker action, provider ingestion, or dashboard runtime merge.

## Active Bottleneck

- Decide whether to add one market-behavior evidence object, test the user-seeded card path, expose cards in dashboard as status-only objects, or hold.

## Evidence

- MSFT card -> `data/candidate_cards/MSFT_supercycle_candidate_card_v0.json`
- MSFT manifest -> `data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json`
- G8.2 tests -> `tests/test_g8_2_system_scouted_candidate_card.py`
- Policy -> `docs/architecture/g8_2_system_scouted_candidate_card_policy.md`
- Handover -> `docs/handover/phase65_g82_system_scouted_candidate_card_handover.md`
- Scout source -> `data/discovery/local_factor_scout_output_tiny_v0.json`
