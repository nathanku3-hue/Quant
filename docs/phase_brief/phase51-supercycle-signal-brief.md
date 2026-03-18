# Phase 51: Supercycle Signal Calibration

Current Governance State: Phase 51 is the active implementation surface after the completed Phase 50 shipping decision. Runtime surface: `strategies/`, `backtests/`, `tests/`, `docs/`, and bounded `data/processed/phase51_grid/` research outputs for the supercycle slice (pending final disposition after 0 strict survivors result), plus the separately authorized Factor Algebra implementation design surface. Goal: continue bounded Phase 51 implementation while preserving the closed Phase 50 evidence chain as historical audit context.

**Status**: ACTIVE CURRENT GOVERNANCE STATE (Phase 50 shipped; Phase 51 implementation active)
**Created**: 2026-03-27
**Authority**: `D-274` + `D-278`
**Execution Authorization**: Bounded Phase 51 implementation. The supercycle scorer/grid slice remains authorized, and Factor Algebra implementation is now separately authorized from its own design brief. No broker routing or live capital semantics are opened by this Phase 51 brief.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Supercycle Signal Calibration
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Final Verification
- **Planning Gate Boundary**: In = `strategies/supercycle_signal.py`, `backtests/optimize_supercycle_grid.py`, focused tests, survivor-report outputs, and same-round docs updates. Out = `dashboard.py`, `main_bot_orchestrator.py`, live or paper runtime integration, Factor Algebra runtime, lithium expansion, and SanDisk continuity work.
- **Owner/Handoff**: Codex implementer -> SAW Reviewer A/B/C -> CEO/PM review
- **Acceptance Checks**: `CHK-P51-01`..`CHK-P51-11`
- **Primary Next Scope**: Publish same-round evidence, formula notes, lesson entry, and SAW closeout after the bounded grid run and focused verification [90/100: given repo constraints]

## 1. Problem Statement
- **Context**: Phase 51 previously existed as a docs-only planning surface under `D-267`. The CEO later issued an explicit parallel unlock, recorded as `D-274`, for the bounded supercycle scorer/grid slice. After the completed Phase 50 Day 30 gate pass under `D-278`, shipping is authorized, the Phase 50 runway is closed, and the Factor Algebra design surface is now separately implementation-authorized.
- **User Impact**: The repo can continue bounded supercycle implementation and now start Factor Algebra implementation from its design brief, while preserving the closed Phase 50 paper-evidence chain as historical audit context rather than an active runway blocker.

## 2. Goals & Non-Goals
- **Goal**: Implement a pure snapshot supercycle scorer with diagnostics and configurable macro gravity.
- **Goal**: Implement a PIT-safe 225-combo optimizer harness over the bounded 2011/2015/2018 training windows and eight semiconductor tickers.
- **Goal**: Generate raw results, aggregated results, and a top-3 survivor report under `data/processed/phase51_grid/`.
- **Goal**: Update governance/docs-as-code artifacts in the same round, including formulas in `docs/notes.md`.
- **Non-Goal**: No Phase 50 runtime integration or dashboard wiring.
- **Non-Goal**: No broker routing, live capital, or production promotion.
- **Non-Goal**: This brief does not govern the Factor Algebra implementation details; `docs/phase_brief/phase51-factor-algebra-design.md` is the starting point for that separate implementation surface.
- **Non-Goal**: No lithium expansion, SanDisk continuity remediation, or Week 3 validation windows in this round.

## 3. Technical Specs
- **Scorer module**: `strategies/supercycle_signal.py`
- **Optimizer harness**: `backtests/optimize_supercycle_grid.py`
- **Focused tests**:
  - `tests/test_supercycle_signal.py`
  - `tests/test_optimize_supercycle_grid.py`
- **Historical planning references**:
  - `docs/phase_brief/phase51-supercycle-grid-planner-companion.md`
  - `docs/phase_brief/phase51-factor-algebra-design.md`
- **Research basis**:
  - `docs/research/bailey_2015_backtest_probability.pdf`
  - `docs/research/erten_2012_commodity_supercycles.pdf`
  - `docs/research/researches.md`
- **Planned output directory**: `data/processed/phase51_grid/`

## 4. Acceptance Criteria (Testable)
- [ ] `CHK-P51-01`: `D-274` is recorded and the active Phase 50 / Phase 51 briefs no longer contradict the parallel unlock.
- [ ] `CHK-P51-02`: `strategies/supercycle_signal.py` implements a pure snapshot scorer plus compatibility wrapper with auditable diagnostics.
- [ ] `CHK-P51-03`: `tests/test_supercycle_signal.py` passes in the repo `.venv`.
- [ ] `CHK-P51-04`: `backtests/optimize_supercycle_grid.py` implements the bounded 225-combo harness, PIT-safe loaders, aggregation, survivor report, and CLI.
- [ ] `CHK-P51-05`: `tests/test_optimize_supercycle_grid.py` passes in the repo `.venv`.
- [ ] `CHK-P51-06`: Training windows and ticker cohort match the locked planner surface (`2011/2015/2018`, eight semiconductors).
- [ ] `CHK-P51-07`: The harness emits bounded raw, aggregated, and survivor artifacts under `data/processed/phase51_grid/`.
- [ ] `CHK-P51-08`: `docs/notes.md` records the explicit scorer and grid formulas plus implementation file references.
- [ ] `CHK-P51-09`: `docs/lessonss.md` records a same-round guardrail entry for the new Phase 51 implementation slice.
- [ ] `CHK-P51-10`: Phase 50 runtime surfaces remain untouched and no new live or broker surface is opened.
- [ ] `CHK-P51-11`: SAW review runs for the Phase 51 round and publishes a bounded closeout report.

## 5. Execution Evidence (2026-03-13)
- **Focused tests**: `.venv\Scripts\python -m pytest tests/test_supercycle_signal.py tests/test_optimize_supercycle_grid.py -q` -> `13 passed`
- **Full training run**: `.venv\Scripts\python backtests/optimize_supercycle_grid.py --output-dir data/processed/phase51_grid --max-workers 1 --top-n 3`
- **Raw results**: `5,400` rows at `data/processed/phase51_grid/grid_search_raw_results.csv`
- **Aggregated results**: `225` rows at `data/processed/phase51_grid/grid_search_aggregated.csv`
- **Survivor report**: `3` ranked rows at `data/processed/phase51_grid/survivor_report_top3.csv`
- **Best ranked parameter set**:
  - `power_law_exponent=2.0`
  - `gravity_multiplier=12.0`
  - `r2_threshold in {0.85, 0.90, 0.95}`
  - `convexity_threshold=1.7`
  - `mean_sharpe=0.449694`
  - `mean_max_dd=-0.126265`
  - `ticker_success_rate=0.125`
  - `window_success_rate=0.333333`
- **Truthful outcome**: no parameter set cleared the strict survivor filter, so the report used `selection_basis=top_ranked_fallback` with `passes_filters=False`.

## 6. Rollback Plan
- **Trigger**: Any change that leaks into Phase 50 runtime surfaces, opens a live-capital path, or fails focused verification for the scorer and grid harness.
- **Action**: Revert the same-round Phase 51 scorer, optimizer, tests, notes/brief/lesson updates, and remove `data/processed/phase51_grid/` artifacts generated by the failed round.

## New Context Packet (Phase 51)

## What Was Done
- Phase 51 Week 2 planning was previously locked as docs-only under `D-267`.
- The CEO later issued an explicit parallel unlock phrase, now recorded as `D-274`, for the bounded supercycle scorer and grid optimizer slice.
- The completed Phase 50 Day 30 gate pass under `D-278` closed the paper runway, authorized shipping, and removed the Factor Algebra docs-only fence.

## What Is Locked
- The historical Phase 50 evidence chain remains preserved read-only for audit.
- Phase 51 remains bounded to governed implementation surfaces under `strategies/`, `backtests/`, `tests/`, `docs/`, and `data/processed/phase51_grid/`, plus the separately authorized Factor Algebra design surface.
- Broker, routing, and live capital semantics are still out of scope for this Phase 51 implementation brief.

## What Is Next
- Continue the bounded supercycle implementation track with normal SAW closeout and reviewer reconciliation.
- Begin Factor Algebra implementation from `docs/phase_brief/phase51-factor-algebra-design.md`.

## First Command
`.venv\Scripts\python -m pytest tests/test_supercycle_signal.py tests/test_optimize_supercycle_grid.py -q`
