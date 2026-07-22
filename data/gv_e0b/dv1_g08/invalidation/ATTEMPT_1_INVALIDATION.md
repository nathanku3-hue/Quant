# G08 Attempt-1 Invalidation (append-only)

**Classification:** INVALID_REVIEWER_INDEPENDENCE_NOT_ESTABLISHED

**Authoritative state restored:**
- SHIPPED_PRODUCT_SCORE = 39
- FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
- OBSERVED_COMPARISON_COUNT = 0
- comparison_observed_eligible = false
- decision_value_disposition = null

## Accepted
- Remote Attempt-1 custody (auth tag, session seals, result bytes)
- Hosted-green code path on result branch
- Certified synthetic NO_POSITION decision as **product smoke** (archived under smoke/)
- Product-surface rendering of sealed comparison as smoke

## Rejected (do not claim)
- comparison_observed_eligible = true
- IMPROVED
- observed count = 1
- stage promotion to ONE_CASE_DECISION_DELTA_OBSERVED

## Why
Same process authored baseline/post and reviewer scores. Receipt commit \859a00ad…\ has GitHub \uthor.login=null\ / \committer.login=null\; \REV_BLINDED_EXTERNAL\ is free-text Git metadata, not provider-authenticated separation. Sealed stage_claim already recorded eligible=false / count=0 while top-level observation fields claimed true/1/IMPROVED.

## Preservation
Sealed Attempt-1 evidence under \data/gv_e0b/dv1_g08/**\ is **not rewritten**.
Invalidation SHA-256 of result.json: \8fa17258162b5ddeff330f9705a60ff0582eea7771bb1b861724d2a028b6b065
## Code repair (forward)
GitHub rubric receipts must be schema v2 with \github_author_login\ and \github_committer_login\; submitter id must equal author login and differ from operator.

## Next
Attempt-2 only: fresh operator (not exposed to packet/result) + separate real reviewer GitHub account. No preferred-sign reuse of Attempt-1.
