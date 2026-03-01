# Phase 26 Brief: Runtime Hardening Debt Burn-Down (Process Tree + CID Seed + Entrypoint Wiring)
Date: 2026-02-28
Status: SAW PASS
Owner: Codex

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Backtest Engine (Signal System)
- L2 Active Streams: Ops, Backend
- L2 Deferred Streams: Data, Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Ops
- Active Stage Level: L3
- Current Stage: Final Verification
- Planning Gate Boundary: in-scope = process-tree timeout termination hardening, CID seed boundary enforcement, and entrypoint wiring for idempotent execution helper; out-of-scope = live-trading unlock and strategy changes.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-12 (listed below).

## 1. Objective
- Close accepted operational debt from Phase 25 open-risk ledger:
  - process-tree termination robustness on scanner timeout,
  - strict CID seed enforcement at execution boundary,
  - outer-loop wiring to idempotent execution helper.

## 2. Implementation Summary
- Hardened scanner process lifecycle in `main_bot_orchestrator.py`:
  - introduced process-group/session-aware spawn path,
  - introduced explicit tree termination helper,
  - timeout branch now terminates process tree before re-raising timeout,
  - Windows branch now validates `taskkill` return code and logs failure details.
- Hardened execution boundary semantics in `main_bot_orchestrator.py`:
  - require canonical seed (`client_order_id` or `trade_day`) before normalization,
  - normalize null-like string seeds (`None`/`null`/`nan`) as missing,
  - guard non-list `batch_results` and treat as unobserved for fail-closed reconciliation,
  - guard malformed dict results missing `ok` and route through missing-CID fail-closed path.
- Hardened orchestrator runtime loop:
  - scheduled scanner exceptions are now contained per iteration (daemon does not fail-dead on one run failure).
- Wired entrypoint loop in `scripts/test_rebalance.py`:
  - seeds `trade_day` before helper call,
  - routes submissions through `execute_orders_with_idempotent_retry(...)`,
  - exits non-zero when any submitted order result is failed.
- Added/expanded test coverage:
  - new scanner/scheduler/process-tree tests and malformed-batch edge tests in `tests/test_main_bot_orchestrator.py`,
  - new script-level integration coverage in `tests/test_test_rebalance_script.py`.

## 3. Artifacts
- `main_bot_orchestrator.py`
- `tests/test_main_bot_orchestrator.py`
- `scripts/test_rebalance.py`
- `tests/test_test_rebalance_script.py`
- `docs/phase_brief/phase26-brief.md`
- `docs/saw_reports/saw_phase26_round1.md`

## 4. Acceptance Checks
- CHK-01: scanner spawn path is process-group/session aware -> PASS.
- CHK-02: timeout branch invokes process-tree termination before re-raising timeout -> PASS.
- CHK-03: Windows tree-kill path validates `taskkill` return code and logs failures -> PASS.
- CHK-04: scheduler loop contains per-run exceptions and continues looping -> PASS.
- CHK-05: execution entrypoint enforces seed requirement (`client_order_id` or `trade_day`) -> PASS.
- CHK-06: null-like CID values are treated as missing seeds -> PASS.
- CHK-07: non-list `batch_results` are fail-closed via missing-CID reconciliation -> PASS.
- CHK-08: malformed dict results missing `ok` are fail-closed via missing-CID reconciliation -> PASS.
- CHK-09: rebalance outer loop is wired through idempotent helper -> PASS.
- CHK-10: rebalance script exits non-zero on failed order results -> PASS.
- CHK-11: SAW reviewer A/B/C rechecks report no in-scope Critical/High -> PASS.
- CHK-12: targeted regression + compile matrix passes in `.venv` -> PASS.

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest -q tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS.
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py tests/test_main_bot_orchestrator.py scripts/test_rebalance.py tests/test_test_rebalance_script.py` -> PASS.
- Final SAW reviewer rechecks:
  - Reviewer A -> PASS (no in-scope Critical/High),
  - Reviewer B -> PASS (no in-scope Critical/High),
  - Reviewer C -> PASS (no in-scope Critical/High).

## 6. Open Notes
- Paper-trading lock remains active and unchanged; no live unlock behavior was modified.
- Residual medium risk: full production entrypoint coverage beyond `scripts/test_rebalance.py` remains a follow-up integration task.

## 7. Rollback Note
- If this round is rejected:
  - revert `main_bot_orchestrator.py`,
  - revert `scripts/test_rebalance.py`,
  - revert `tests/test_main_bot_orchestrator.py` and remove `tests/test_test_rebalance_script.py`,
  - revert associated docs updates.
