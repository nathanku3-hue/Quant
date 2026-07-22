# Phase Brief / Preregistration: GV-E0B-DV1 Contradiction Case (G08)

Mode: `EXECUTION_PACKET`
Status: `C1_CANDIDATE_BANKING` (local immutable candidate; hosted/reviewer/SAW closure pending)
Date: 2026-07-22
RoundID: `ROUND-20260722-E0B-DV1-C1-CANDIDATE-BANK`
ScopeID: `GV_E0B_DV1_CONTRADICTION_G08_C1`
Authority: main recovery baseline `accef5c`; candidate base `b7a24d3` (tree `c13b0a08`); donor committed base `e9e9a9a` (read-only; not a b7 descendant claim)

This file is the frozen experiment preregistration for G08 Attempt-1. Its exact committed bytes are bound by the candidate manifest and one-shot authorization.

## Stage frame (locked)

```text
SHIPPED_PRODUCT_SCORE = 39/100 FROZEN
FUNCTIONAL_STAGE = CERTIFIED_SINGLE_DECISION_OPERABLE
OBSERVED_COMPARISON_COUNT = 0
TARGET_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED (not yet earned)
ACTIVE_PRODUCT_SLICE = E0B-DV1 Contradiction Case C1 candidate custody
OBSERVATION_GATE = comparison_observed_eligible
VALUE_GATE = decision_value_disposition: IMPROVED | NOT_IMPROVED
V2_BLOCK_ONLY_REAL_ADMISSION = CLOSED_UNTIL_G08_DISPOSITION
```

## Provenance claim boundary

```text
candidate base: b7a24d3
donor committed base: e9e9a9a
donor working bytes: recovered unstaged patch
candidate construction: explicit b7 → donor-byte transformation
```

Never claim the donor was based on `b7a24d3`. Irrecoverable Phase 2K commits `65bc459a…` and `1a7a5ad9…` remain locked loss. Defensible claim: Git ancestry and explicit provenance dependency on those commits are absent. Do not overclaim that no human ever copied conceptual content from missing history.

## Candidate path model

```text
18 authored/input paths
+ 2 regenerated current-context outputs
+ 1 tracked candidate manifest
= 21 final candidate paths
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

Mapping reveal occurs only after the receipt-bound rubric is durably sealed.

## Rubric items (exact six)

```text
selected_action_defensibility
indispensable_missing_evidence_identification
falsifier_and_contradiction_recognition
supply_demand_business_shareholder_valuation_claim_separation
avoidance_of_claims_beyond_evidence
rationale_traceability
```

## Primary endpoint

```text
total blinded-rubric delta
```

### Targeted dimensions

```text
indispensable_missing_evidence_identification
falsifier_and_contradiction_recognition
```

### Core-safety dimensions

```text
selected_action_defensibility
avoidance_of_claims_beyond_evidence
```

### IMPROVED formula (fail-closed)

```text
IMPROVED iff:
  total_delta > 0
  AND at least one targeted dimension delta > 0
  AND every core-safety dimension delta >= 0
```

Every other complete valid observed comparison is `NOT_IMPROVED`.

### Outcome classes

| Condition | Disposition |
|---|---|
| IMPROVED formula true | `IMPROVED` (positive outcome) |
| total_delta = 0 with all required scores present | `NOT_IMPROVED` (zero outcome; valid) |
| total_delta < 0 with all required scores present | `NOT_IMPROVED` (negative outcome; valid) |
| tie on total with all required scores present | `NOT_IMPROVED` (valid; not invalid) |
| positive total with no targeted gain | `NOT_IMPROVED` (valid) |
| positive total with any core-safety regression | `NOT_IMPROVED` (valid) |
| missing required score | **invalid** (fail closed; comparison not observed-eligible) |
| malformed or incomplete rubric | **invalid** (fail closed) |

Tie or zero is `NOT_IMPROVED`, not invalid, when all required scores are present. Missing required scores fail closed and make the comparison invalid.

## Timing and ordering (frozen)

```text
60-minute maximum per decision arm (BASELINE, POST)
early submission permitted
exact elapsed seconds recorded
late submission rejected
baseline sealed before packet generation
packet generated only after baseline seal
post arm opened only after packet
rubric has no 60-minute decision-arm limit unless separately specified
```

## Randomization and blinding (frozen)

```text
random ARM_A / ARM_B label generation
mapping commitment created before reviewer scoring
reviewer receives only blinded export (review_package.json + rubric_authoring.json)
mapping remains unavailable until receipt-bound rubric is durably sealed
mapping reveal occurs after rubric seal
```

## Operational reviewer separation (not personhood)

Required production flow:

```text
reviewer receives only blinded export
→ reviewer submits rubric through a separately authenticated account
→ external submission produces immutable receipt identity and artifact hash
→ operator imports the exact submitted bytes
→ receipt identity and artifact hash enter the sealed rubric and session manifest
→ mapping reveal occurs only after the receipt-bound rubric is durably sealed
```

Preferred mechanism: reviewer-controlled GitHub submission from a different authenticated account, with exact commit SHA and rubric blob SHA-256.

Receipt structure (minimum):

```text
provider = GITHUB
repository identity
authenticated submitter identity
submission commit SHA
rubric path
rubric blob OID where available
rubric SHA-256
receipt URL or immutable API identity
submitted timestamp from provider metadata
review package hash
candidate commit
candidate tree
case_id
attempt
```

Local import must recompute rubric SHA-256, require equality with the external receipt, require exact candidate commit/tree, expected case/attempt, expected blinded review-package hash, reject operator-authored replacement bytes, reject mismatched submitter identity, reject missing or mutable receipt fields, reject mapping reveal before receipt-bound rubric sealing, bind the receipt into the sealed rubric and session path, and carry the receipt into final result verification.

**Claim limit:** GitHub proves operational authenticated-account separation only. It does **not** prove natural-person identity or cryptographic personhood.

## One-shot Attempt-1 authorization (later session; design required now)

Session open for production G08 must bind a remotely retained one-shot authorization identity:

```text
case_id = GV_E0B_DV1_G08
attempt = 1
authorization_tag_object
authorization_artifact_sha256
candidate_commit
candidate_tree
preregistration_sha256
```

Code must reject: missing authorization; wrong case; attempt other than `1`; candidate commit/tree mismatch; preregistration hash mismatch; mutable or unverifiable tag object identity; second attempt claiming to be first; authorization artifact hash mismatch.

Production authorization tag creation and session opening are **not** authorized in the C1 banking round. They remain for later approval `GV-E0B-DV1-G08-ATTEMPT-1`.

## Publication and rerun rules (frozen)

```text
all valid positive, zero, and negative comparisons are retained and publishable
valid NOT_IMPROVED evidence may not be suppressed
the same case may not be rerun merely because the outcome is unfavourable
no rerun from another checkout may claim another first attempt
production-code change after session opening invalidates the attempt
```

## Claim boundary (frozen)

```text
within-case observational comparison only
one operator performs baseline and post
order/familiarity effects are not removed
the design does not establish causal superiority
the design does not establish cryptographic personhood
authenticated account separation establishes operational separation only
```

## Vertical

```text
synthetic G08 sealed bundle
→ sealed arm-open events (system timestamp; append-only event journal)
→ baseline within equal 60m max budget (early submit allowed)
→ packet reveal
→ post within equal 60m max budget
→ mechanical REVIEW_PACKAGE (ARM_A/ARM_B random; mapping withheld)
→ blinded reviewer rubric via external receipt-bound import
→ bound chain + full seal replay
→ fail-closed path-identity proof + pairwise alias rejection
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
- Fixtures never increment observed count. A real operator + different blinded reviewer with receipt-bound import may establish `comparison_observed_eligible=true`.
- `run_e0b_dv1_case()` is the sole official E0B publication entry point.
- Observation eligibility and product-value success are separate authority fields.
- Ledger is tamper-evident under capture-process custody only.
- Capture runner: `scripts/gv_e0b_g08_capture.py` (narrow local workflow, not a platform).

## Forbidden (this round and until later authorization)

```text
open-session for production G08
human baseline / post / rubric capture
participant recruitment
result publication
score or stage uplift
FS1 · V2-B0 · providers · PEAD · broker/order/alpha/live-capital
generic Meta-Harness work · compatibility aliases · unrelated cleanup
```

## Next gate (after local C1 bank)

1. Hosted Ubuntu + Windows product proof with exact runner image/version and full package inventory.
2. Independent Reviewer A/B/C + terminal SAW on exact candidate commit/tree/tag.
3. Remote one-shot Attempt-1 authorization retained before any session open.
4. Real G08 from clean checkout of the hosted-green candidate only.
5. Publish every valid disposition; score remains 39 until a separate owner decision.

## Module surface

- `core/gv_e0b_dv1_contradiction.py`
- `scripts/gv_e0b_g08_capture.py`
- `tests/gv_fs0_product/test_e0b_dv1_contradiction.py`
- `validation/gv_fs0_reconstruction.py`
- `docs/candidate_manifests/gv_e0b_dv1_c1_candidate.json` (tracked after bank)
