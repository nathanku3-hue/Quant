# Planner Packet - Current

## New Context Packet — GV-ALPHA0_ACTIVE (2026-07-23)

## What Was Done
- PR #8 merged to main at `2c7f32c` (tip substrate `29cfeff`). B0B banked as **source family one** inside Alpha — not a phase-stop.
- ALPHA0 authority repairs on tip: strict duplicate-key JSON rejection; true byte locators; result-last fail-closed case promote (not full rollback atomicity).
- Metrics locked: score **39**; stage **CERTIFIED_SINGLE_DECISION_OPERABLE**; observed **0**.

## What Is Locked
- Active product train: **GV-ALPHA0_ACTIVE** (not B0B-closure / not B0C-as-phase / not formal comparison gate).
- B0A CLOSED/BANKED; B0B = source family one (`SEC:0000723125-26-000015`).
- ADMITTED never auto-ADVANCE; formal human comparison deferred until after Alpha.
- Case promote is result-last fail-closed, not multi-file rollback transaction.

## What Is Next
```text
exact authorized source family two (bank before reconciliation machinery)
→ 3–5 case-specific facts + operator capture + certified result (one vertical)
→ independent-source reconciliation (later car on same train)
→ export/replay → fresh-clone proof → non-author dogfood
```

## First Command
```text
.venv\Scripts\python -m pytest -q tests/gv_fs0_product/test_v2_b0b_official_source_intake.py
```
