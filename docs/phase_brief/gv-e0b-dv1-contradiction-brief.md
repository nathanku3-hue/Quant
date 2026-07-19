# Phase Brief: GV-E0B-DV1 Contradiction Case (G08)

Mode: `EXECUTION_PACKET`
Status: `AUTHORIZED_ACTIVE_PRODUCT_SLICE`
Date: 2026-07-19
RoundID: `ROUND-20260719-E0B-DV1-CONTRADICTION`
ScopeID: `GV_E0B_DV1_CONTRADICTION_G08`
Authority: post-merge main `2653eb1`; `e0_acceptance_tests.md` G08; frozen six-item rubric in `e0_preregistration.yaml`

## Stage frame

```text
SHIPPED_PRODUCT_SCORE = 39/100 FROZEN (low-confidence; no uplift)
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE (E0A banked)
TARGET_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED
ACTIVE_PRODUCT_SLICE = E0B-DV1 Contradiction Case
```

## Why not empty-card missing-evidence

An empty MU candidate card predictably yields missing evidence and may show no advantage over a cheap human baseline. G08 forces a nontrivial triage: contradictory indispensable evidence must **block without averaging**.

## Vertical

```text
sealed adversarial synthetic bundle (contradictory indispensable evidence)
→ sealed 60-minute human baseline
→ deterministic BLOCKED: CONTRADICTORY_INDISPENSABLE_EVIDENCE packet
→ post-packet human decision
→ frozen six-item rubric delta
→ bind comparison hash to existing NO_POSITION certification
→ one visible comparison
```

## Acceptance

1. Bundle contains ≥2 indispensable claims that disagree on one fact_key.
2. Packet `run_state=BLOCKED`, `block_reason=CONTRADICTORY_INDISPENSABLE_EVIDENCE`.
3. Engine does not average or majority-vote values.
4. Baseline sealed before packet; post-packet action differs with better contradiction triage.
5. Six rubric items scored 0–2; total delta and item deltas recorded.
6. Comparison bound to banked `certified_decision_result_hash` for E0A NO_POSITION.
7. Visible presentation rows for action / missing-evidence / falsifier delta.
8. Score remains 39; no alpha / general-effectiveness claim.

## Forbidden

providers · full valuation lattice · FS1 · PEAD · broker · score uplift · empty-card theatre as primary case · dirty-root work

## Module

- `core/gv_e0b_dv1_contradiction.py`
- `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
