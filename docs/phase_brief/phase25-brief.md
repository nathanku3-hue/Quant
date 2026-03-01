# Phase 25 Brief: Operational Hardening Cycle (Orchestrator E2E + UX + Warning Cleanup)
Date: 2026-02-28
Status: SAW PASS
Owner: Codex

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Backtest Engine (Signal System)
- L2 Active Streams: Ops, Backend, Frontend/UI
- L2 Deferred Streams: Data
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Ops
- Active Stage Level: L3
- Current Stage: Final Verification
- Planning Gate Boundary: in-scope = orchestrator-level idempotent retry proof, Streamlit cache-reset UX integration tests, and deprecation-noise cleanup in high-frequency data import path; out-of-scope = live-trading unlock and strategy/performance model changes.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-13 (listed below).

## 1. Objective
- Close inherited operational risk by proving orchestrator-level submit timeout + CID recovery semantics with static idempotency keys.
- Harden UI cache-corruption/reset behavior with integration-style view tests.
- Reduce CI/log noise by removing unconditional `pandas_datareader` import side effects.

## 2. Implementation Summary
- Added orchestrator-level execution retry contract in `main_bot_orchestrator.py`:
  - `execute_orders_with_idempotent_retry(...)`,
  - retryable-error classifier,
  - static `client_order_id` normalization across retries,
  - strict recovery payload parity checks (`symbol/side/qty`) before accepting recovered/duplicate state.
- Reconciliation hardening after independent SAW reviewer findings:
  - enforced batch-result completeness by CID (missing rows are retried and fail closed as `batch_result_missing`),
  - enforced preflight duplicate-symbol rejection before any submission side effects,
  - anchored recovery/retry intent to original `pending_by_cid` payload (not downstream echoed row order),
  - treated malformed/non-dict result rows as unobserved and routed them through missing-CID fail-closed path,
  - normalized terminal retryable failures at max attempts to explicit `retry_exhausted`.
- Added phantom-fill E2E tests in `tests/test_main_bot_orchestrator.py`:
  - timeout first attempt -> retry with same CID -> recovered success path,
  - `already exists` strict-match acceptance path,
  - strict mismatch rejection path,
  - retry exhaustion and non-retryable terminal-fail paths,
  - partial/malformed batch-row reconciliation paths and duplicate-symbol preflight path.
- Added Streamlit view integration-style tests in `tests/test_auto_backtest_view.py`:
  - corrupted cache blocks execution unless explicit reset,
  - reset button path persists default state + rerun,
  - start-state cache write failure aborts simulation (fail closed).
- Performed deprecation cleanup:
  - moved `pandas_datareader` import in `scripts/high_freq_data.py` to local function scope (`get_construction_scalar`) to avoid unrelated import-time warnings.
  - aligned dependency manifests by explicitly adding `pandas-datareader==0.10.0` to `pyproject.toml` and `requirements.txt`.

## 3. Artifacts
- `main_bot_orchestrator.py`
- `tests/test_main_bot_orchestrator.py`
- `tests/test_auto_backtest_view.py`
- `scripts/high_freq_data.py`
- `pyproject.toml`
- `requirements.txt`
- `docs/saw_reports/saw_phase25_round1.md`

## 4. Acceptance Checks
- CHK-01: Orchestrator-level idempotent retry helper implemented -> PASS.
- CHK-02: Static `client_order_id` preserved across retries -> PASS.
- CHK-03: Phantom-fill E2E timeout/retry/recovery path tested -> PASS.
- CHK-04: `already exists` accepted only on strict payload parity -> PASS.
- CHK-05: Recovery payload mismatch is fail-closed -> PASS.
- CHK-06: Streamlit cache-corruption/reset UX integration-style tests added -> PASS.
- CHK-07: Start-state cache write failure path aborts simulation in test coverage -> PASS.
- CHK-08: `pandas_datareader` deprecation-noise cleanup implemented with import-scope hardening -> PASS.
- CHK-09: Batch-result completeness guard prevents silent CID loss and fails closed on unresolved rows -> PASS.
- CHK-10: Duplicate-symbol preflight rejection blocks partial-submit side effects -> PASS.
- CHK-11: Recovery/retry intent is anchored to original pending payload by CID -> PASS.
- CHK-12: Malformed non-dict result rows are ignored and reconciled through missing-CID fail-closed path -> PASS.
- CHK-13: Targeted regression + compile matrix passes in `.venv` -> PASS.

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_auto_backtest_control_plane.py tests/test_auto_backtest_view.py tests/test_main_console.py tests/test_execution_controls.py` -> PASS (`54 passed`).
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py` -> PASS (`16 passed`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py scripts/high_freq_data.py views/auto_backtest_view.py core/auto_backtest_control_plane.py tests/test_main_bot_orchestrator.py tests/test_auto_backtest_view.py` -> PASS.
- `.venv\Scripts\python -m pytest -q tests/test_dashboard_control_plane.py` -> PASS (`6 passed`).
- SAW reviewer rechecks:
  - Reviewer A -> PASS (no in-scope Critical/High),
  - Reviewer B -> PASS (no in-scope Critical/High),
  - Reviewer C -> PASS (no in-scope Critical/High).

## 6. Open Notes
- Paper-trading lock remains active and unchanged; no live unlock path was modified.
- Orchestrator helper currently provides the E2E proof contract and can be wired into broader production execution entrypoints in follow-up ops slices.
- Medium carried risk: subprocess hard-stop uses `subprocess.run(..., timeout=...)` and does not yet enforce process-tree kill semantics for child/grandchild process fan-out.
- Medium carried risk: deterministic CID fallback still depends on runtime date when both `trade_day` and `client_order_id` are absent; production entrypoints should continue to pass explicit `client_order_id` or canonical `trade_day`.

## 7. Rollback Note
- If this round is rejected:
  - revert `main_bot_orchestrator.py`,
  - remove added tests in `tests/test_main_bot_orchestrator.py` and `tests/test_auto_backtest_view.py`,
  - restore top-level `pandas_datareader` import in `scripts/high_freq_data.py`,
  - revert `pyproject.toml` and `requirements.txt` dependency updates.
