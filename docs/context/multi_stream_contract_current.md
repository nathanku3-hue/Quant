# Multi-Stream Contract - Quant Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, strategy search, provider ingestion, alerts, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, or scope widening by itself.
Purpose: coordinate streams after the Portfolio Optimizer View Test and Performance Hardening round.

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
