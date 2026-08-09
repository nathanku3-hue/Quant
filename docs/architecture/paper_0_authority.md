# PAPER-0 Authority — Thin Broker Vertical

**Date:** 2026-08-09  
**Status:** `AUTHORIZED_FOR_IMPLEMENTATION / FIRST_ORDER_MINIMUM_GATES_REQUIRED / STRATEGY_LIVE_CAPITAL_CLOSED`  
**Strategic lock:** `docs/architecture/aov_strategic_direction_lock_20260809.md`  
**Roadmap authority:** `docs/architecture/aov_endgame_generalization_spec_current.md`  
**Runtime effect of this document alone:** `NONE` — implementation, tests and receipts still required  
**financial_alpha_evidence:** `0`  
**Strategy live capital:** `CLOSED`

---

## 0. Purpose

Authorize the smallest lineage-correct real PAPER vertical through the existing Alpaca path so the programme can learn broker lifecycle, restart, fencing and reconciliation **without** waiting for a production OMS or claiming Alpha evidence.

PAPER-0 proves **operational authority**, not real-market impact, queue position, capacity or financial alpha.

---

## 1. PAPER-0 vs PAPER-1

### PAPER-0 — first usable vertical (authorized now)

```text
frozen promoted target
→ live_rebalance_id
→ ExecutionIntentV1
→ CIQSEC ↔ broker instrument/account map
→ MOC_CLOSE_AUCTION_V1 = market + cls
→ broker submit / ack / open orders / fills
→ canonical PAPER state (incl. residual open risk)
→ positions / cash reconciliation
→ restart reconciliation
→ FREEZE_NEW_RISK on discrepancy
```

Unsupported broker states may **fail closed**.

### PAPER-1 — production-hardening tail (may defer)

```text
trade bust normalization
trade correction normalization
every replacement edge
extended implementation-shortfall attribution
complete early-close / calendar generalization
rare brokerage lifecycle expansion
elaborate operator UI
optimizer integration
```

These must close before bounded live capital where relevant. They need not block the first PAPER learning event **if** PAPER-0 first-order calendar gates below are met.

---

## 2. First-order admission gates (CRO)

Before the first PAPER order:

1. **Identity / intent**
   - one promoted policy/seal bound to one `live_rebalance_id`
   - `ExecutionIntentV1` binds at minimum:
     - `account_id`
     - `live_rebalance_id`
     - `promoted_policy_id` / `promoted_seal_id`
     - `execution_map_hash`
     - `instrument_id`
     - `side` / `quantity`
     - `execution_policy_id`
     - `time_in_force`
     - `rebalance_epoch`
   - intent hash / signed envelope / `client_order_id` derive from that exact object

2. **TIF / close path**
   - end-to-end proof: promoted rebalance → broker payload `time_in_force = cls` for `MOC_CLOSE_AUCTION_V1`
   - no silent broker TIF defaulting on the promoted path

3. **Broker → canonical state**
   - actual broker lifecycle projects into canonical PAPER events/book
   - committed live state includes open orders and partial-fill residual risk
   - no second OMS; reuse existing broker/recovery/replay/book primitives where valid

4. **Restart / fencing**
   - every process restart begins `FREEZE_NEW_RISK = true`
   - reconcile broker account / positions / cash / open orders / recent executions against local intent/event/book/`rebalance_epoch`
   - ambiguity preserves freeze
   - stale/zombie epochs may not create new-risk intents

5. **Session-close truth (non-negotiable for first order)**
   - resolve the **actual** session close (including early closes), **or**
   - explicitly restrict the order to a **verified regular full-session day** and **fail closed** otherwise
   - **Forbidden:** “calendar deferred” ⇒ assume every session closes at 16:00

---

## 3. Destructive ExecutionIntent authority

When `ExecutionIntentV1` becomes current authority, remove in the same slice:

```text
legacy trade-day / symbol / side / qty CID authority
duplicated orchestrator CID generation
duplicated execution semantics
silent broker TIF defaulting
```

No compatibility adapter. Historical execution receipts remain historical evidence under their pinned identity.

---

## 4. Broker truth ≠ deterministic simulated fill truth

Historical deterministic Portfolio V0 / `EXECUTION_MODE = DETERMINISTIC_PAPER` remains valid historical/mechanical authority. It is **not** PAPER live-state authority.

Actual Alpaca authority produces accepted / pending / open / partial / filled / canceled / rejected (and related) states. Do not mutate historical execution receipts to look live.

---

## 5. Performance law

Complete before the close auction window:

```text
research computation
target generation
policy/seal validation
execution-map validation
pricing snapshot (batch / bounded-batch, timestamped + hash-bound)
risk calculations
ExecutionIntent construction
```

Final hot path only:

```text
immutable ExecutionIntentV1
→ small synchronous risk gate
→ broker submit
→ acknowledgement
```

Full certification/replay/reconciliation continues outside the latency-critical submit path. No GPU/distributed programme is authorized for PAPER-0.

---

## 6. What PAPER-0 does not authorize

```text
strategy live capital
financial_alpha_evidence uplift
A1 / A2 / A3 claims
leverage / shorting / options / derivatives
second OMS / broad execution platform
generic optimizer programme
```

PAPER operational success is a management KPI, not Alpha evidence.

---

## 7. Minimum tests before first rebalance

**T1 — promoted target → broker payload**

Assert exact binding of account, `live_rebalance_id`, policy/seal, execution map, instrument, side/qty, execution policy, `time_in_force = cls`, `rebalance_epoch`, `client_order_id`. Mutation of authority-bearing fields must change identity or fail closed.

**T2 — broker lifecycle → canonical PAPER state + restart**

Paths: accepted → partial → open residual → final fill; accepted → partial → canceled residual; plus restart. Assert residual exact, open order exact, replay idempotent, broker/local discrepancy detected, freeze persists on mismatch.

---

## 8. Authority links

| Surface | Role |
|---|---|
| `aov_strategic_direction_lock_20260809.md` | Strategic authorization |
| `aov_endgame_generalization_spec_current.md` | Roadmap / change authority |
| `gv_endgame_authority_current.md` | Current runtime meaning + claim boundary |
| this document | PAPER-0 execution authority contract |
