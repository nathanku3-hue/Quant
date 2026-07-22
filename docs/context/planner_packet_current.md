# Planner Packet - Current

## New Context Packet — B0A Closed on Main; B0B Sole Gate (2026-07-23)

## What Was Done
- PR #6 merged (`3e995f1` / head `79c309b`). Exact-head product, protocol, Windows/Linux, and parity green.
- B0A local-source abstention banked and **closed** on canonical main.
- Metrics unchanged: 39 / CERTIFIED_SINGLE_DECISION_OPERABLE / observed 0.

## What Is Locked
- B0A CLOSED — do not leave “merge pending” as active truth.
- Explicit B0A/B0B deviation from original real-source gate is recorded.
- No score uplift; no real external packages; no admission certificates.

## What Is Next
1. Open **GV-V2-B0B-OFFICIAL-SOURCE-INTAKE** only (one official MU package).
2. Detached authorization → exact official bytes → PIT/custody admission → separate claim evaluation → ADVANCE|HOLD|REJECT → certified action.
3. Admission must never auto-advance research. Vacuous contradiction: use `NOT_EVALUATED` in B0B when no admitted facts.

## First Command
```text
.venv\Scripts\python -m pytest -q tests/gv_fs0_product/test_v2_b0_real_block_only.py
```
