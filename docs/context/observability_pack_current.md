# Observability Pack - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, candidate validation, provider ingestion, strategy search, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: make drift visible early after the Portfolio Optimizer View Test and Performance Hardening round.

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
