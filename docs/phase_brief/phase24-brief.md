# Phase 24 Brief: P2 Auto-Backtest Infrastructure UI (Round 1)
Date: 2026-02-28
Status: Execution Complete (SAW PASS)
Owner: Codex

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Backtest Engine (Signal System)
- L2 Active Streams: Frontend/UI, Backend, Ops
- L2 Deferred Streams: Data
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Frontend/UI
- Active Stage Level: L3
- Current Stage: Final Verification
- Planning Gate Boundary: in-scope = `app.py` Lab/Backtest routing split, `views/auto_backtest_view.py`, `core/auto_backtest_control_plane.py`, `tests/test_auto_backtest_control_plane.py`, and docs updates; out-of-scope = execution broker paths, orchestrator submit-timeout E2E proof, and strategy math/model changes.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-08 (listed below).

## 1. Objective
- Decouple Lab/Backtest UI from monolithic `app.py` into a dedicated view.
- Add a dedicated Auto-Backtest control-plane service for normalized config + JSON cache state.
- Preserve existing simulation behavior parity (manual run path, same strategy/engine contracts).

## 2. Implementation Summary
- Added new control-plane module:
  - `core/auto_backtest_control_plane.py`
  - dataclasses for config/cache/plan contracts,
  - deterministic config normalization and config fingerprint,
  - run-key generation (`date + fingerprint`),
  - fail-closed cache loader (`missing_file`, `invalid_json`, `invalid_payload`, `io_error`) with explicit `reset` policy,
  - cache state transitions (`mark_started`, `mark_finished`),
  - atomic JSON persist with bounded `PermissionError` retry.
- Added extracted view module:
  - `views/auto_backtest_view.py`
  - moved Lab/Backtest UI block out of `app.py`,
  - wired control-plane cache load/normalize/persist,
  - retained manual simulation trigger semantics,
  - added failure-state cache write on simulation exception.
- Updated app routing:
  - `app.py` now routes `"🔬 Lab / Backtest"` to `render_auto_backtest_view(...)`.
  - removed now-unused inline Lab/Backtest imports in `app.py`.
- Added targeted tests:
  - `tests/test_auto_backtest_control_plane.py`.
  - `tests/test_auto_backtest_view.py`.

## 3. Artifacts
- `core/auto_backtest_control_plane.py`
- `views/auto_backtest_view.py`
- `tests/test_auto_backtest_control_plane.py`
- `data/auto_backtest_cache.json` (runtime artifact path)

## 4. Acceptance Checks
- CHK-01: Lab/Backtest UI extracted from `app.py` into dedicated view with behavior parity -> PASS.
- CHK-02: Dedicated Auto-Backtest control-plane service added in `core/` -> PASS.
- CHK-03: Config normalization contract (bounds/type coercion) implemented and tested -> PASS.
- CHK-04: Cache loader fail-closed semantics implemented with explicit reset option -> PASS.
- CHK-05: Atomic JSON cache writes implemented with retry + cleanup -> PASS.
- CHK-06: Simulation start/finish cache-state transitions implemented -> PASS.
- CHK-07: Targeted control-plane tests pass in `.venv` -> PASS.
- CHK-08: Impacted control-plane regression matrix + compile gate pass -> PASS.

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest -q tests/test_auto_backtest_control_plane.py tests/test_auto_backtest_view.py` -> PASS (`8 passed`).
- `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py tests/test_main_console.py tests/test_main_bot_orchestrator.py tests/test_execution_controls.py` -> PASS (`38 passed`, 4 non-blocking deprecation warnings from `pandas_datareader`).
- `.venv\Scripts\python -m py_compile core/auto_backtest_control_plane.py views/auto_backtest_view.py app.py` -> PASS.

## 6. Open Notes
- Auto-backtest cache runtime path: `data/auto_backtest_cache.json`.
- Cache loader default is fail-closed (`error_policy="fail"`); extracted view now:
  - auto-bootstraps only when cache file is missing,
  - blocks execution on corrupted/unreadable cache until operator-triggered reset.
- Inherited out-of-scope risk remains unchanged:
  - orchestrator-level submit-timeout + CID recovery E2E proof is still pending and paper-lock remains mandatory until proven.

## 7. Rollback Note
- If this round is rejected:
  - remove `core/auto_backtest_control_plane.py`,
  - remove `views/auto_backtest_view.py`,
  - restore pre-split Lab/Backtest block in `app.py`,
  - remove `tests/test_auto_backtest_control_plane.py`.
