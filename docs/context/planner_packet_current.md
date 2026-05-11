# Planner Packet - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize execution, promotion, live trading, strategy search, candidate ranking, candidate scoring, thesis validation, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: provide the planner with a compact fresh world model after the Portfolio Optimizer View Test and Performance Hardening round.

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
- `CLOSURE_DELTA`: `Focused compile, affected 46-test suite, full pytest, and test-evidence refresh passed.`
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
