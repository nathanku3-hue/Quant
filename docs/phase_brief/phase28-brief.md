# Phase 28 Brief: Entrypoint Contract Remediation (Step 1)
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
- Planning Gate Boundary: in-scope = production entrypoint wiring hardening (atomic payload gate, CID lineage, strict intent parity, fail-closed runtime). out-of-scope = feature/UI work, strategy optimization, live-unlock changes.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-15 (below).

## 1. Objective
- Execute approved Step 1 remediation bundle for broader production entrypoint wiring.
- Close SAW BLOCK findings on:
  - partial malformed payload fail-open behavior,
  - CID lineage drop at local-submit seam,
  - intent/contract drift across local payload -> orchestrator -> broker submit path.
- Preserve paper-trading lock as absolute boundary.

## 2. Implementation Summary
- `main_console.py` hardening:
  - added atomic `execution_orders` validator (`all-or-nothing` row contract),
  - enforced required fields per row:
    - `ticker/symbol`, `target_weight`, `action|side`, `order_type`, `limit_price`, `client_order_id`, `trade_day`,
  - enforced `trade_day` semantic calendar validity (`YYYYMMDD` + valid date),
  - enforced batch cap at helper entry (`MAX_ORDERS_PER_BATCH`),
  - enforced payload/calculated symbol-set parity (fail on missing/extra symbol drift),
  - seeded `client_order_id/order_type/limit_price/trade_day` into orders passed to idempotent helper,
  - enforced strict seeded parity check (`symbol/side/qty/order_type/limit_price/client_order_id`),
  - enforced strict helper result CID reconciliation (unknown/duplicate/missing CID rows fail closed),
  - tightened integer guard (`qty` must be positive integral, no truncation of non-integral values).
- `execution/rebalancer.py` hardening:
  - accepts validated optional order intent (`order_type`, `limit_price`) and passes to broker for limit orders,
  - validates limit-order `limit_price` as finite positive numeric,
  - preserves backward compatibility by omitting market default `order_type` kwarg for legacy brokers.
- `execution/broker_api.py` hardening:
  - submit path supports strict `order_type/limit_price` contract for market/limit,
  - explicit bool-qty rejection at submit boundary,
  - recovery intent matcher upgraded to enforce:
    - `symbol/side/qty/order_type/client_order_id` parity,
    - strict market limit semantics (`limit_price` must be null-like only),
  - recovery lookup now preserves raw `limit_price` for consistent null-semantics matching.
- `main_bot_orchestrator.py` hardening:
  - normalization/parity upgraded to include `order_type/limit_price` intent checks in recovery matching.
- test expansion:
  - `tests/test_main_console.py`:
    - malformed row atomic fail,
    - duplicate payload CID fail,
    - invalid order type fail,
    - missing/non-calendar trade_day fail,
    - non-integral calculated qty fail,
    - local-submit post-submit notify failure fail-closed.
  - `tests/test_execution_controls.py`:
    - limit order passthrough to broker,
    - limit missing price reject,
    - bool qty reject,
    - market recovery with numeric/non-null limit fails closed,
    - market recovery with text-null limit recovers,
    - recovery missing CID fails closed.
  - `tests/test_main_bot_orchestrator.py`:
    - limit recovery parity success/mismatch coverage.

## 3. Artifacts
- `main_console.py`
- `execution/rebalancer.py`
- `execution/broker_api.py`
- `main_bot_orchestrator.py`
- `tests/test_main_console.py`
- `tests/test_execution_controls.py`
- `tests/test_main_bot_orchestrator.py`
- `docs/phase_brief/phase28-brief.md`
- `docs/runbook_ops.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/saw_reports/saw_phase28_round1.md`

## 4. Acceptance Checks
- CHK-01: `execution_orders` malformed row causes whole-batch abort (no partial execution) -> PASS
- CHK-02: payload duplicate ticker rejected at entrypoint -> PASS
- CHK-03: payload duplicate `client_order_id` rejected at entrypoint -> PASS
- CHK-04: payload `trade_day` required and calendar-valid -> PASS
- CHK-05: payload/calculated symbol drift rejected fail-closed -> PASS
- CHK-06: local-submit seeds payload `client_order_id` through submit path -> PASS
- CHK-07: local-submit parity enforces `symbol/side/qty/order_type/limit_price/client_order_id` -> PASS
- CHK-08: rebalancer propagates limit intent (`order_type/limit_price`) to broker submit -> PASS
- CHK-09: broker submit rejects bool `qty` -> PASS
- CHK-10: broker recovery requires CID parity and strict market null-limit semantics -> PASS
- CHK-11: market recovery with text-null limit is accepted; numeric/non-null limit fails closed -> PASS
- CHK-12: post-submit notification failure in local-submit mode aborts with non-zero -> PASS
- CHK-13: targeted suite (`main_console` + `execution_controls` + `main_bot_orchestrator`) passes -> PASS
- CHK-14: impacted matrix passes (`109 passed`) -> PASS
- CHK-15: SAW reviewer A/B/C final clearance reports PASS (no in-scope Critical/High) -> PASS

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py -q` -> PASS.
- `.venv\Scripts\python -m pytest tests/test_main_bot_orchestrator.py tests/test_test_rebalance_script.py tests/test_main_console.py tests/test_execution_controls.py tests/test_auto_backtest_view.py tests/test_auto_backtest_control_plane.py` -> PASS (`109 passed in 5.03s`).
- `.venv\Scripts\python -m py_compile main_console.py main_bot_orchestrator.py execution/broker_api.py execution/rebalancer.py tests/test_main_console.py tests/test_execution_controls.py tests/test_main_bot_orchestrator.py` -> PASS.
- SAW rechecks:
  - Reviewer A: PASS,
  - Reviewer B: PASS (prior null-semantics BLOCK cleared),
  - Reviewer C: PASS.

## 6. Open Notes
- Paper-trading lock remains unchanged and enforced by broker init guardrails.
- Residual low operational sensitivity: unknown broker null sentinel encodings beyond `{None, "", "none", "null"}` for market-order `limit_price` will fail closed as `recovery_mismatch` (safer false-negative behavior).
- Residual low test debt: permutation-complete recovery mismatch matrix can be expanded in follow-up hardening.

## 7. Rollback Note
- If this round is rejected:
  - revert `main_console.py`,
  - revert `execution/rebalancer.py`,
  - revert `execution/broker_api.py`,
  - revert `main_bot_orchestrator.py`,
  - revert `tests/test_main_console.py`,
  - revert `tests/test_execution_controls.py`,
  - revert `tests/test_main_bot_orchestrator.py`,
  - revert Phase 28 docs.
