# Done Checklist - Phase 65 G8.2 System-Scouted Candidate Card

Status: Current with Portfolio Universe Construction PASS and optimizer-core quarantine complete
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, thesis validation, or scope widening by itself.
Purpose: define machine-checkable done criteria for current Phase 65 portfolio universe and candidate-card work.

## Latest Addendum - Dashboard Scanner Testability Hardening

- [x] `strategies/scanner.py` exists and owns deterministic scanner math.
- [x] `dashboard.py` preserves yfinance/provider calls and delegates scanner enrichment to `strategies.scanner.enrich_scan_frame`.
- [x] Macro score, breadth, price technicals, cluster, entry/support, tactics, proxy signal, rating, leverage, and scan-frame enrichment have focused tests.
- [x] `tests/conftest.py` includes shared price/return/macro/ticker-map fixtures.
- [x] `InvestorCockpitStrategy` quality-cap coverage exists.
- [x] `AdaptiveTrendStrategy` regime transition coverage exists.
- [x] `ProductionConfig` invariant coverage exists.
- [x] `core.etl` temp-directory parquet build coverage exists.
- [x] Process guardrail test still passes.
- [x] Focused affected pytest passes.
- [x] Scoped compile passes.
- [x] Full pytest completed for this scanner hardening addendum.

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
