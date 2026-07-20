# Phase Brief: GV-E0B-DV1 Contradiction Case (G08) — Authority Repair

Mode: `EXECUTION_PACKET`
Status: `ENGINE_SEAL_REPAIR_ACTIVE` (not closed; no stage promotion; no merge of 7c6e19c)
Date: 2026-07-20
RoundID: `ROUND-20260720-E0B-DV1-AUTHORITY-REPAIR`
ScopeID: `GV_E0B_DV1_CONTRADICTION_G08_REPAIR`
Authority: main `2653eb1` (PR #4); PR #5 authority repair; frozen endgame + G08

## Stage frame

```text
SHIPPED_PRODUCT_SCORE = 39/100 FROZEN
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
OBSERVED_COMPARISON_COUNT = 0
TARGET_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED (not yet earned)
ACTIVE_PRODUCT_SLICE = E0B-DV1 Contradiction Case repair
V2_BLOCK_ONLY_REAL_ADMISSION = RECOMMENDED_NEXT_PROTOCOL
```

## Capture chain (exact)

```text
SESSION_OPEN
→ BASELINE_OPEN
→ BASELINE_CLOSE
→ PACKET
→ POST_OPEN
→ POST_CLOSE
→ REVIEW_PACKAGE
→ RUBRIC_CLOSE
```

## Vertical

```text
synthetic G08 sealed bundle
→ sealed arm-open events (system timestamp; append-only event journal)
→ baseline within equal 60m max budget (early submit allowed)
→ packet reveal
→ post within equal 60m max budget
→ mechanical REVIEW_PACKAGE (ARM_A/ARM_B random; mapping withheld)
→ blinded reviewer rubric (no 60m gate)
→ bound chain + full seal replay
→ atomic result.json + decision_packet.md
→ publish only if two-human close eligible
→ Streamlit surface recomputes seals
```

## Pass bar

- Equal **configured** budgets (60m max); actual elapsed may differ; late submit rejected.
- Mechanical blinding required; third attestor removed.
- Positive / zero / negative delta all valid; score stays 39.
- Fixtures do not close E0B; real operator + different real reviewer do.
- Ledger is tamper-evident under capture-process custody only.
- Capture runner: `scripts/gv_e0b_g08_capture.py` (narrow local workflow, not a platform).

## Forbidden

providers · FS1 · PEAD · broker · score uplift · third attestor ceremony ·
forced exact 60m elapsed · generic capture platform · fabricated humans · merge of unrepaired tip

## Next gate (after green hosted CI on this repair tip)

1. Real G08 capture (1 operator + 1 different blinded reviewer) via capture runner  
2. Full replay → publish if eligible → count 0→1 → stage promote  
3. Merge PR #5 → open minimal V2-B0 protocol artifact + first real block-only admission  

## Module

- `core/gv_e0b_dv1_contradiction.py`
- `scripts/gv_e0b_g08_capture.py`
- `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
- `tests/gv_fs0_product/test_e0b_dv1_streamlit_apptest.py`
- `views/gv_fs0_portfolio_adapter.py`
