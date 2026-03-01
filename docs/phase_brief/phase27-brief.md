# Phase 27 Brief: Conditional-Block Remediation (Strict OK + Terminal Kill + Parity + Containment)
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
- Planning Gate Boundary: in-scope = remediation of strict `ok` typing, terminate-confirmed-or-fail semantics, universal success parity enforcement, startup diagnostic containment, and regression expansion; out-of-scope = feature work, UI work, strategy optimization, live-trading unlock.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-14 (listed below).

## 1. Objective
- Resolve the conditional AMBER block by neutralizing newly surfaced High/Medium execution risks in orchestrator control paths.
- Maintain strict paper-trading lock posture and avoid any feature/UI changes.

## 2. Implementation Summary
- Hardened strict typing and parity in `main_bot_orchestrator.py`:
  - enforced strict boolean typing for downstream `result.ok`,
  - enforced universal payload parity on all `ok=True` rows,
  - added fallback parity source from row-order payload (`row.order`) to avoid false negatives when success payload is sparse,
  - hardened quantity typing by rejecting boolean `qty` in both request normalization and recovery matching.
- Hardened terminal timeout contract in `main_bot_orchestrator.py`:
  - scanner timeout now remains terminate-confirmed-or-fail with terminal `ScannerTerminationError` on unconfirmed kill.
- Hardened orchestrator containment behavior:
  - startup diagnostic run now uses same containment policy as scheduler loop for non-terminal failures,
  - terminal scanner kill-failure remains critical + re-raised (daemon stop).
- Extended strictness downstream at entry script/log layer:
  - `scripts/test_rebalance.py` now counts success only for `ok is True`.
  - `execution/rebalancer.py` acceptance logging now keys on `ok is True`.
- Expanded regression tests:
  - added explicit negative guards for duplicate CID, invalid `max_attempts`, non-dict order input, empty list fast-path,
  - added strict-typing tests (`ok` non-bool fail-closed, bool `qty` rejection),
  - added parity regression tests for sparse `ok=True` payload fallback acceptance and mismatched payload rejection,
  - added startup/scheduled terminal containment re-raise assertions.

## 3. Artifacts
- `main_bot_orchestrator.py`
- `execution/rebalancer.py`
- `scripts/test_rebalance.py`
- `tests/test_main_bot_orchestrator.py`
- `tests/test_test_rebalance_script.py`
- `docs/phase_brief/phase27-brief.md`
- `docs/saw_reports/saw_phase27_round1.md`

## 4. Acceptance Checks
- CHK-01: strict boolean `result.ok` enforced (non-bool rows treated unobserved) -> PASS.
- CHK-02: universal parity enforced for all `ok=True` rows -> PASS.
- CHK-03: sparse `ok=True` payload accepted only when row-order fallback matches intent -> PASS.
- CHK-04: bool `qty` rejected in request normalization -> PASS.
- CHK-05: bool `qty` rejected in recovery/success parity matcher -> PASS.
- CHK-06: terminate-confirmed-or-fail contract preserved on scanner timeout path -> PASS.
- CHK-07: timeout + kill-not-confirmed escalates as terminal `ScannerTerminationError` -> PASS.
- CHK-08: startup non-terminal failure is contained/logged and scheduler still arms -> PASS.
- CHK-09: startup terminal scanner failure is critical + re-raised -> PASS.
- CHK-10: scheduled terminal scanner failure is critical + re-raised -> PASS.
- CHK-11: script entrypoint success accounting requires `ok is True` -> PASS.
- CHK-12: explicit negative matrix expansion (duplicate CID, max_attempts, non-dict input, empty orders) -> PASS.
- CHK-13: targeted regression matrix and compile checks pass in `.venv` -> PASS.
- CHK-14: SAW implementer + reviewer A/B/C rechecks report no in-scope unresolved Critical/High -> PASS.

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS (`78 passed`).
- `.venv\Scripts\python -m py_compile main_bot_orchestrator.py execution/rebalancer.py scripts/test_rebalance.py tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py` -> PASS.
- SAW validator checks:
  - `validate_closure_packet.py` -> `VALID`,
  - `validate_saw_report_blocks.py` -> `VALID`.
- Final SAW reviewer rechecks:
  - Implementer: PASS,
  - Reviewer A: PASS (no in-scope Critical/High),
  - Reviewer B: PASS (no in-scope Critical/High),
  - Reviewer C: PASS (no in-scope Critical/High).

## 6. Open Notes
- Paper-trading lock remains active and unchanged; no live unlock behavior was modified.
- Residual medium risk: process-tree confirmation still relies on parent process liveness checks (descendant-level enumeration not independently verified in unit tests).
- Residual medium risk: POSIX kill-path and Windows fallback-after-success branch have limited direct unit coverage.

## 7. Rollback Note
- If this round is rejected:
  - revert `main_bot_orchestrator.py`,
  - revert `execution/rebalancer.py`,
  - revert `scripts/test_rebalance.py`,
  - revert `tests/test_main_bot_orchestrator.py`,
  - revert `tests/test_test_rebalance_script.py`,
  - revert associated docs updates for Phase 27.
