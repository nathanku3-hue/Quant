# Reviewer Instructions — One-Case Evidence-Gap Triage

Observation class: `EVIDENCE_GAP_TRIAGE_ONLY`.

Score two randomized, scrubbed arms labelled only `ARM_A` and `ARM_B`. Do not attempt to infer which arm received additional product support. The package intentionally excludes timestamps, hashes, case/product-stage names, file paths, prior Alpha answers, portfolio actions, and origin metadata.

Each arm retains its newly authored current research action and rationale because `selected_action_defensibility` and `rationale_traceability` must be scoreable.

## Identity evidence

Use the frozen `OPENSSH_SSHSIG_V1` adapter. A preflight signature proves only reviewer identity viability. The final reviewer credential signature must bind the exact `session_manifest_hash`, `review_package_hash`, and `rubric_hash`, and the credential must be linked by a separately pinned issuer to a verified human subject at `IN_PERSON_OR_LIVE_VIDEO_GOVERNMENT_ID_MATCH` level. The reviewer must be a different verified human, principal, and credential from the operator. Account-name inequality alone is insufficient.

## Frozen rubric

Score each item from 0 to 2 with equal weight:

1. `selected_action_defensibility`
2. `indispensable_missing_evidence_identification`
3. `falsifier_and_contradiction_recognition`
4. `supply_demand_business_shareholder_valuation_claim_separation`
5. `avoidance_of_claims_beyond_evidence`
6. `rationale_traceability`

Use only the submitted arm text and the neutral source locator references present in the review package. Do not use current prices, post-cutoff events, outside research, prior Alpha knowledge, portfolio outcomes, or certification outputs.

Seal the complete rubric before the private arm mapping is revealed. Missing, malformed, or out-of-range scores make the consumed run ineligible rather than `NOT_IMPROVED`.

The disposition is computed mechanically after reveal:

- `IMPROVED` only when total delta is positive, at least one targeted evidence-gap/falsifier dimension improves, and neither selected-action defensibility nor avoidance of unsupported claims worsens;
- every other complete eligible result is `NOT_IMPROVED`.

Either sign leaves score 39 and establishes no economics, investment value, portfolio value, causal superiority, or alpha.
