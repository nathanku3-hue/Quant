# Post-Phase Alignment - Phase 65 G8.2

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, broker automation, promotion, candidate validation, provider ingestion, strategy search, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, or scope widening by itself.
Purpose: update the multi-stream map after the Portfolio Optimizer View Test and Performance Hardening round.

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
