# Phase Brief: GV-E0B-DV1 Contradiction Case (G08) — Authority Repair

Mode: `EXECUTION_PACKET`
Status: `CANDIDATE_SAW_PASS_REAL_G08_PENDING` (code pin=`43dce24f806908f1a80f017f9d9b4125d908eb54`; tree=`9db1243e110015082216a7fa31fd56616c383d97`; local 98 focused + 191 product + 137 protocol = 329/329; hosted run `29777518085` PASS; Reviewer A/B/C PASS; real G08 not run)
Date: 2026-07-21
RoundID: `ROUND-20260721-E0B-DV1-C1-CUSTODY`
ScopeID: `GV_E0B_DV1_CONTRADICTION_G08_REPAIR`
Authority: main `2653eb1` (PR #4); PR #5 hosted-green candidate `43dce24` descending from C0 `b7a24d3`; frozen endgame + real G08 next

## Stage frame

```text
SHIPPED_PRODUCT_SCORE = 39/100 FROZEN
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
OBSERVED_COMPARISON_COUNT = 0
TARGET_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED (not yet earned)
ACTIVE_PRODUCT_SLICE = E0B-DV1 Contradiction Case repair
OBSERVATION_GATE = comparison_observed_eligible
VALUE_GATE = decision_value_disposition: IMPROVED | NOT_IMPROVED
V2_BLOCK_ONLY_REAL_ADMISSION = CLOSED_UNTIL_G08_DISPOSITION
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
→ fail-closed path-identity proof + pairwise alias rejection across all capture/output/lock paths
→ staged result.json + decision_packet.md with paired rollback on replacement failure
→ reload and verify result.json identity + complete seal-derived comparison
→ private certification bound to the result's embedded comparison hash
→ publish only if comparison_observed_eligible=true and observed count=1
→ assign IMPROVED or NOT_IMPROVED from the frozen rubric
→ Streamlit surface recomputes seals and shows both observation and value disposition
```

## Pass bar

- Equal **configured** budgets (60m max); actual elapsed may differ; late submit rejected.
- Mechanical blinding required; third attestor removed.
- Positive / zero / negative results may all be methodologically valid and must be retained; score stays 39.
- Fixtures never increment observed count. A real operator + different blinded reviewer may establish `comparison_observed_eligible=true`.
- `IMPROVED` requires total blinded-rubric delta `> 0`, at least one targeted gain (`indispensable_missing_evidence_identification` or `falsifier_and_contradiction_recognition`), and no regression in either core safety dimension (`selected_action_defensibility`, `avoidance_of_claims_beyond_evidence`).
- Every other valid observed result is `NOT_IMPROVED`: publish/retain as honest falsification, do not close S-009X as product PASS, and do not rerun G08 to manufacture a preferred sign.
- `run_e0b_dv1_case()` is the sole official E0B publication entry point.
- Comparison-only E0B book/decision/certification/publication helpers are private and absent from the public module surface; the generic publisher is imported only under a private alias.
- Publication authority comes only from the object returned by `load_verified_result()` with pinned result schema/case/run class, a complete comparison reconstructed from verified sealed records, `comparison_observed_eligible=true`, exact integer count `1`, and certificate rationale bound to that result's embedded comparison hash.
- Observation eligibility and product-value success are separate authority fields; no `e0b_close_eligible` compatibility alias exists.
- Fixture, close-false, count-zero/wrong-type, result-identity tamper, fully re-sealed comparison-mismatch, uncertain path identity, and pairwise path-alias paths (including hard links) must fail before any evidence or current-decision write.
- Canonical result and decision-packet writes stage both payloads first and restore both prior paths if either replacement fails.
- Result/packet payload bytes are fsynced before atomic replacement; directory metadata fsync is best-effort where the host supports it, matching the canonical publisher's Windows portability boundary.
- Ledger is tamper-evident under capture-process custody only.
- This repair closes the official E0B module bypass; it does not claim to prevent a privileged repository operator from manually invoking lower-level infrastructure.
- Capture runner: `scripts/gv_e0b_g08_capture.py` (narrow local workflow, not a platform).

## Forbidden

providers · FS1 · PEAD · broker · score uplift · third attestor ceremony ·
forced exact 60m elapsed · generic capture platform · fabricated humans · merge of unrepaired tip

## Next gate

1. Fresh-clone or standalone-checkout C0 `b7a24d3` under the approved project root; transfer exactly the 15 source-of-truth files, regenerate current context, exclude stale SAW, and bank one intentional C1 SHA.
2. Prove exact C1 locally with focused E0B, full product, frozen protocol, AppTest, context validation, parent=`b7a24d3`, clean-tree and tree-identity checks.
3. Push immediately, then run hosted Ubuntu/Windows/byte parity and independent Reviewer A/B/C concurrently.
4. Conduct real G08 from a fresh clean checkout of the exact hosted-green SHA (1 operator + 1 different blinded reviewer), with no production-code change after capture begins.
5. Replay/verify/publish, move count 0→1, assign `IMPROVED` or `NOT_IMPROVED`, commit only result-bearing evidence/publication/truth, rerun hosted parity, and perform a narrow evidence audit.
6. `IMPROVED`: merge as S-009X PASS. `NOT_IMPROVED`: merge or retain the valid falsification evidence, no maturity uplift, replan the product hypothesis. V2-B0 remains closed until this disposition.

## Module

- `core/gv_e0b_dv1_contradiction.py`
- `scripts/gv_e0b_g08_capture.py`
- `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
- `tests/gv_fs0_product/test_e0b_dv1_streamlit_apptest.py`
- `views/gv_fs0_portfolio_adapter.py`
