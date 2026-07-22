## What Was Done
- Canonical E0B product machinery shipped through repair tip `3c404479d9af963f497c889013e078adae68d516` (tree `c808849a492a5138364a1eda00f5c4c502abdda3`): C1 candidate, Attempt-1 sealed evidence, append-only invalidation, provider-authenticated reviewer receipt v2, restored E0A current authority.
- Attempt-1 classified **INVALID_REVIEWER_INDEPENDENCE_NOT_ESTABLISHED**; sealed evidence preserved; observation authority count **0**.
- Invalidation tag `gv-e0b-dv1-g08-attempt-1-invalidated` peels to repair tip. Historical `gv-e0b-dv1-g08-attempt-1-result` -> da55c073… preserved as evidence, **not** observation authority.
- Hosted product+parity green on repair tip; same-case Attempt-2 demoted to deferred external validation.

## What Is Locked
- `SHIPPED_PRODUCT_SCORE = 39/100` frozen. `FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE`. `OBSERVED_COMPARISON_COUNT = 0`.
- Default product current decision = E0A `DECISION_E0A_HOLD_FOR_EVIDENCE_1` / NO_POSITION. E0B G08 current is smoke only under `data/gv_e0b/dv1_g08/smoke/`.
- No valid independent comparison; no IMPROVED; no stage promotion; no alpha.
- FS1, PEAD, optimizer, broker, score uplift, live capital closed.
- Same-case Attempt-2 is **not** the sole product gate.

## What Is Next
- Canonical cutover: fast-forward main to repair lineage.
- Sole functional gate: **GV-V2-B0-REAL-BLOCK-ONLY-ADMISSION** (one real MU PIT evidence package or certified data abstention).
- First valid independent comparison deferred to a fresh real case after admission, not synthetic G08 re-run.

## First Command
`.venv\Scripts\python -m pytest -q tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
