# Phase Brief: GV-E0B-DV1 Contradiction Case (G08) — Repair In Place

Mode: `EXECUTION_PACKET`
Status: `ENGINE_SEAL_REPAIR_ACTIVE` (not closed; no stage promotion)
Date: 2026-07-19
RoundID: `ROUND-20260719-E0B-DV1-REPAIR`
ScopeID: `GV_E0B_DV1_CONTRADICTION_G08_REPAIR`
Authority: main `2653eb1` (PR #4); PR #5 in-place repair; frozen endgame + G08

## Stage frame

```text
SHIPPED_PRODUCT_SCORE = 39/100 FROZEN
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
OBSERVED_COMPARISON_COUNT = 0
TARGET_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED (not yet earned)
ACTIVE_PRODUCT_SLICE = E0B-DV1 Contradiction Case repair
```

Unofficial decision-value / conjunctive maturity percentages are **retired**.
Report **observed-comparison count** only.

## Vertical (one case — no capture platform)

```text
synthetic G08 sealed bundle (evidence may be synthetic)
→ real human baseline seal (same operator later)
→ generate G08 packet BLOCKED:CONTRADICTORY_INDISPENSABLE_EVIDENCE
→ real human post-packet seal (same operator)
→ independent reviewer rubric (different identity)
→ recompute every hash
→ atomic result.json + decision_packet.md
→ new E0B DecisionEnvelope rationale_ref = E0B:CMP:<comparison_hash>
→ certify / publish (run_class = SYNTHETIC_DEV_RUN)
→ Streamlit surface + AppTest
→ minimal truth refresh
```

## Pass bar

- Protocol-valid comparison: **positive, zero, or negative** total delta all pass.
- Observed within-case difference only. **No** causal superiority / general-effectiveness claim.
- Engine fixtures validate seals/hash/cert only; **fixtures do not close E0B**.
- E0B close requires:
  - baseline + post authored by the **same real human operator**
  - rubric authored by a **different real human reviewer**
  - all seals and hashes recompute clean
- If real human records are unavailable: ship engine/seal repair only; **do not** promote stage or close E0B.

## Forbidden

providers · FS1 · PEAD · broker · score uplift · hardcoded baseline/post/rubric ·
required positive/causal improvement · unofficial maturity scores · generic capture platform ·
fabricated human outcomes · empty-card theatre as primary case

## Next gate (after one valid observed comparison)

1. One independently replicated comparison on a second nontrivial terminal case
2. First real evidence admission  
Not FS1, providers-by-default, PEAD, or more certification infrastructure.

## Module

- `core/gv_e0b_dv1_contradiction.py`
- `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
- `tests/gv_fs0_product/test_e0b_dv1_streamlit_apptest.py`
- `views/gv_fs0_portfolio_adapter.py` (`render_e0b_dv1_surface`)
