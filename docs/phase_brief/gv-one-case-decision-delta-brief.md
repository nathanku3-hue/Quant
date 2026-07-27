# Phase Brief: GV One-Case Decision Delta — Evidence-Gap Triage

Mode: `APPROVAL_GATE`
Status: `AUDIT_PASS; COMMIT_A_IMPLEMENTED; HOSTED_GREEN_REQUIRED_BEFORE_HUMAN_EXPOSURE`
Date: 2026-07-27
RoundID: `ROUND-20260727-GV-ONE-CASE-DELTA-PLAN-REDLINE`
ScopeID: `GV_ONE_CASE_EVIDENCE_GAP_TRIAGE_PLAN`
Hierarchy: L1 GodView certified portfolio OS; L2 active stream Decision Value Observation; L2 deferred streams Full E0 Economics, Replication, Prospective Economics, and Live Capital; L3 flow Plan Audit → Commit A → Hosted Proof → One Human Run → Commit B.
Branch: `codex/gv-one-case-delta-1`
Base: `origin/main@48a43b99350465202f8bcd09113a34fa724580af`
Authorization: `CONFIRM A received — Commit A only; stop before human exposure`

## Decision

Choose Option A.

```text
redlined Commit A
→ hosted green
→ one uncontaminated two-human run
→ Commit B imports immutable result
→ observed count 0→1 only when eligibility holds
→ publish sign-independent finding
```

Audit approval was received before implementation. Commit A must stop after exact-candidate hosted Windows/Linux green and before human exposure.

## Verified Local State

- The branch base remains `origin/main = gv-alpha0-close^{}` at `48a43b99350465202f8bcd09113a34fa724580af`.
- Commit A candidate `313c2aa9eae44d0f5c90fd6a6509feea9110d47c` was committed and pushed after the complete local matrix passed.
- Hosted run `30277303768` proved Linux green but Windows failed closed because Git checkout converted the new canonical JSON files from LF to CRLF; no human exposure occurred.
- The current additive repair pins `data/gv_one_case_delta/**/*.json` and instructions to LF in `.gitattributes` and adds an explicit checkout-custody regression.
- The ignored local Python 3.12.10 `.venv` contains the pinned repository requirements and is used for all local validation.
- The root checkout is unsafe and must remain untouched: local `main` is stale at `accef5c6be62f63cfc57f0118e0b6b7ae46fad4f` with massive staged deletions and unrelated untracked files.
- Alpha current authority remains `DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1`, CDR `889cc831fe405e5aad1f13225f06fe666036390defeff6652b39d0d656225376`, score 39, observed 0, no alpha claim.
- Active current-truth surfaces now state that Alpha is merged on `main@48a43b9` and that Commit A is pre-human machinery only.

## Endgame Intent and Explicit Deviation

Original E0 proposition:

```text
physical supply condition
→ industry economics
→ MU business capture
→ shareholder cash-flow capture
→ relationship to the decision-time price envelope
```

The existing Alpha case does not evaluate that full chain. Its banked state includes:

```text
physical_supply_telemetry = FAIL
business_capture = NOT_EVALUATED
price_consistent_expectations = NOT_EVALUATED
economics = NOT_EVALUATED
claim_outcome = CLAIM_INSUFFICIENT
```

Therefore:

```text
OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY
```

This slice may test whether GodView improves:

- evidence-gap research triage;
- indispensable missing-evidence identification;
- falsifier and contradiction recognition;
- separation of claim dimensions;
- avoidance of claims beyond evidence;
- rationale traceability.

It may not establish:

- physical supply identification;
- industry economics;
- MU business capture;
- shareholder capture;
- price-envelope inconsistency;
- investment value;
- portfolio value;
- financial alpha.

An `IMPROVED` result authorizes one next full E0 vertical. It does not satisfy that vertical.

## Standing Metrics

Before a valid run:

```text
SHIPPED_PRODUCT_SCORE = 39/100
FUNCTIONAL_STAGE = CERTIFIED_MULTI_SOURCE_CASE_OPERABLE
OBSERVED_COMPARISON_COUNT = 0
OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY
ALPHA_CLAIM = false
FINANCIAL_ALPHA = not demonstrated
```

After one valid eligible run, regardless of sign:

```text
SHIPPED_PRODUCT_SCORE = 39/100
FUNCTIONAL_STAGE = ONE_CASE_DECISION_DELTA_OBSERVED
OBSERVED_COMPARISON_COUNT = 1
OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY
DECISION_VALUE_DISPOSITION = IMPROVED | NOT_IMPROVED
ALPHA_CLAIM = false
FINANCIAL_ALPHA = not demonstrated
```

A completed but contaminated or ineligible run is retained as usability dogfood and does not change stage or observed count.

## Experimental Question

Under identical fixed human-analysis budgets and the same sealed admissible MU/NVDA evidence, does adding an answer-free GodView evidence-gap projection improve one operator's research-triage decision quality according to a blinded, different human reviewer?

This is a within-case observational comparison. It does not establish causal superiority or general effectiveness.

## Frozen Case Binding

```text
case_id = V2_ALPHA0_MU_G_SUPPLY_CLOSE_1
subject_case = MU_G_SUPPLY
module = G_supply
cutoff_at = 2026-07-23T00:00:00.000000Z
case_manifest_hash = 356df2011791415d29d0fe1e5d6d8b516092434a819f4f22fed11ed63350805c
family_one = SEC:0000723125-26-000015
family_one_package_manifest_hash = a8a35cf0ec0d205101e7dce6b4c25574605c20fb1c1454af7ea7ca678839d347
family_two = SEC:0001045810-26-000052
family_two_package_manifest_hash = f0853047f7406be439d3fb42f768c50e73af2fbc1228253e618372fc8e33f5c2
maximum_budget_per_arm = 60 minutes
early_submission = allowed
latency_endpoint = none
```

Reuse the banked bytes. Do not re-ingest providers or copy a new evidence corpus.

## Arm Inputs

### Baseline arm

Receives one sealed admissible-evidence bundle containing only evidence available at the cutoff:

- exact admitted excerpts or objects from both source families;
- source-family identities;
- source locators and byte locators;
- evidence object hashes needed for replay;
- neutral task instructions and frozen action set.

The baseline bundle must not contain Alpha adjudication, prior action, prior result, prior operator identity, or GodView claim-state analysis.

### Post arm

Receives the exact same sealed admissible-evidence bundle plus one newly generated answer-free GodView projection.

No evidence bytes may differ between arms. Only the projection is added.

## Answer-Free GodView Projection

Commit A must generate and freeze a new projection from the banked evidence. The existing `export_bundle.json` is prohibited because it contains prior adjudication, prior operator confirmation, `HOLD_FOR_EVIDENCE`, certified `NO_POSITION`, and result identities.

### Projection may contain

- admissible evidence and exact source locators;
- coverage and overlap analysis;
- non-overlap analysis;
- claim-state analysis, including `CLAIM_INSUFFICIENT` where mechanically derived;
- missing indispensable evidence;
- contradictions and falsifiers;
- explicit dimension states, including `FAIL`, `UNKNOWN`, and `NOT_EVALUATED`;
- clear distinction among supply, demand, business capture, shareholder capture, and valuation dimensions;
- schema version and projection content hash.

### Projection must exclude

- `adjudication.json` and any adjudication fields;
- `operator_confirmation.json` and any operator identity or notes;
- `research_decision.json`;
- `result.json`;
- `certified_decision_result.json`;
- prior selected research action;
- prior selected portfolio action;
- prior decision ID, CDR ID, CDR hash, certification identity, portfolio book identity, or presentation rows;
- `HOLD_FOR_EVIDENCE`, `NO_POSITION`, or any recommended action;
- previous product-stage names, score, observed count, receipt identity, or dogfood status;
- timestamps or hashes that reveal which arm received the projection to the reviewer.

### Positive source-custody allowlist

Projection generation may read only the following path-and-hash-bound inputs:

```text
data/gv_v2_alpha0/case_mu_g_supply_close_1/case_manifest.json
data/gv_v2_alpha0/case_mu_g_supply_close_1/coverage.json
data/gv_v2_alpha0/case_mu_g_supply_close_1/evidence_panel.json
data/gv_v2_b0b/mu_0000723125-26-000015/package_manifest.json
data/gv_v2_b0b/mu_0000723125-26-000015/source_manifest.json
data/gv_v2_b0b/mu_0000723125-26-000015/raw/mu-20260528.htm
data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/package_manifest.json
data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/fact_set.json
data/gv_v2_alpha0/family_two_nvda_0001045810-26-000052/raw/nvda-20260426.htm
```

The frozen `experiment_binding.json` records the exact hash of every allowed input. Canonical realpath resolution must remain repository-confined and must reject lexical aliases, symlinks, junctions, hard-link aliases where detectable, or any resolved path outside this allowlist.

All other case, family, dogfood, decision, certification, result, receipt, and current-authority files are forbidden inputs. In particular, projection code must never open `case_claim.json`, `adjudication.json`, `operator_confirmation.json`, `research_decision.json`, `result.json`, `certified_decision_result.json`, `decision_packet.md`, `case_workspace_view.json`, or `export_bundle.json`.

### Required projection tests

- Instrument every file open during projection generation and prove the complete read set is a subset of the positive allowlist.
- Attempt direct, relative, case-variant, symlink/junction, and alias access to every forbidden case path; each attempt must fail before bytes are read.
- Mutation of an allowlisted path or hash must fail closed.
- A recursive forbidden-field/value scan remains defense in depth and must fail if any prohibited field or prior answer-bearing value appears anywhere in the projection or post-arm review text.

Output scanning alone is insufficient: reading a forbidden source and filtering it later is a protocol failure.

## Human Eligibility

### Operator

The same real human completes baseline and post. Before baseline, the operator must attest:

- no prior exposure to the Alpha claim, adjudication, result, or selected action;
- no participation in Alpha implementation, dogfood, audit, or review;
- no material post-cutoff MU/NVDA information;
- no current-price or subsequent-event use;
- no outside research during either arm;
- no access to the projection before the baseline is sealed.

Failure of any condition makes the run ineligible for observed count. The records remain retained as dogfood.

### Reviewer

A different real human scores the two arms. The reviewer receives only randomized scrubbed arm texts and the frozen rubric.

Each blinded arm must retain the operator's current-arm research submission:

- `current_research_action`, using the frozen three-action set;
- current-arm rationale;
- identified indispensable missing evidence;
- identified falsifiers or contradictions;
- claim-separation statements;
- evidence locators cited by that arm.

These fields are required so `selected_action_defensibility` and `rationale_traceability` are scoreable. They are the operator's newly authored arm answers, not prior Alpha answers.

The review package must exclude:

- arm timestamps and elapsed times;
- hashes, commit IDs, case IDs, decision IDs, and receipt IDs;
- product-stage, Alpha, baseline, post, GodView, or packet labels;
- prior Alpha research action, prior portfolio action, prior adjudication, prior result, or prior operator identity;
- any portfolio action or certification output;
- file paths or schema names that reveal arm origin.

Neutral labels `ARM_A` and `ARM_B` are permitted. The mapping remains sealed until the rubric is durably bound.

## Frozen Action Set and Rubric

Research action set:

```text
ADVANCE_TO_FULL_RESEARCH
HOLD_FOR_EVIDENCE
REJECT_THESIS
```

Portfolio authority remains unchanged until Commit B and is not shown as an arm answer.

Frozen rubric, each scored 0–2 with equal weight:

```text
selected_action_defensibility
indispensable_missing_evidence_identification
falsifier_and_contradiction_recognition
supply_demand_business_shareholder_valuation_claim_separation
avoidance_of_claims_beyond_evidence
rationale_traceability
```

Disposition rule:

```text
IMPROVED iff:
  total_delta > 0
  AND at least one targeted dimension delta > 0
  AND each core-safety dimension delta >= 0
```

Targeted dimensions:

```text
indispensable_missing_evidence_identification
falsifier_and_contradiction_recognition
```

Core-safety dimensions:

```text
selected_action_defensibility
avoidance_of_claims_beyond_evidence
```

Every other complete valid observed comparison is `NOT_IMPROVED`. Missing or malformed required scores make the run ineligible, not `NOT_IMPROVED`.

## Provider-Neutral Signed Human Identity Evidence

Human separation is product semantics. Unequal strings, two accounts, or one replayable attestation do not prove two separate humans.

The core protocol must consume two separately verifiable signed identity records:

```text
operator_identity_evidence
reviewer_identity_evidence
```

Each record must contain or bind:

```text
verified_human_subject_commitment
role = OPERATOR | REVIEWER
principal_id
credential_or_public_key_fingerprint
identity_evidence_issuer
identity_evidence_id
identity_verification_level
session_nonce
session_manifest_hash
role_specific_challenge
signature
signed_at
```

Required predicates:

- each signature independently verifies against its bound credential and role-specific challenge;
- each identity issuer record is independently replay-verifiable and links the credential to a verified human subject, not merely an unverified account label;
- operator and reviewer `verified_human_subject_commitment` values are present and unequal;
- operator and reviewer credentials are distinct;
- neither identity record may be generated, countersigned, or substituted by the other role;
- the reviewer identity signature additionally binds `review_package_hash` and `rubric_hash`;
- mapping reveal occurs only after both identity records, the rubric, and the detached session attestation are durably sealed.

A separate detached session attestation binds:

```text
session_manifest_hash
session_nonce
sealed_record_hashes
review_package_hash
rubric_hash
operator_identity_evidence_hash
reviewer_identity_evidence_hash
attestation_statements
attestation_id
attestation_provider
```

A GitHub signed commit, WebAuthn assertion, SSH/PGP-signed challenge, or another provider may be an adapter only when it supplies the required signed identity and issuer evidence. GitHub login inequality alone is never sufficient and GitHub-specific fields must not be embedded in core comparison semantics.

The protocol may use privacy-preserving subject commitments, but it must not downgrade the claim to principal-string inequality.

## Redlined Commit A — Pre-Human Machinery Only

Commit A is intentionally narrow. It contains no human result and no current-decision publication.

### A1. Complete post-merge truth correction

Correct every active current-truth surface that still says Alpha is unmerged or merge-pending:

```text
docs/context/planner_packet_current.md
docs/context/impact_packet_current.md
docs/context/bridge_contract_current.md
docs/context/done_checklist_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/context/current_context.md
docs/context/current_context.json
docs/architecture/top_level_roadmap.md
README.md, only where stale current direction exists
docs/notes.md, append-only decision/formula register
```

Truth after Commit A:

```text
Alpha merged on main at 48a43b9; tag gv-alpha0-close
ACTIVE_SLICE = ONE_CASE_EVIDENCE_GAP_TRIAGE_MACHINERY
FUNCTIONAL_STAGE = CERTIFIED_MULTI_SOURCE_CASE_OPERABLE
SHIPPED_PRODUCT_SCORE = 39
OBSERVED_COMPARISON_COUNT = 0
OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY
CURRENT_DECISION = DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1
NEXT = hosted-green Commit A → one uncontaminated run → Commit B
G08 Attempt-1 = INVALID, preserved as history
same-case synthetic Attempt-2 = not default
```

### A2. Freeze experiment and instructions

Expected new files:

```text
docs/phase_brief/gv-one-case-decision-delta-brief.md
data/gv_one_case_delta/case_1/experiment_binding.json
data/gv_one_case_delta/case_1/instructions_operator.md
data/gv_one_case_delta/case_1/instructions_reviewer.md
```

`experiment_binding.json` binds only static experiment custody: case, cutoff, positive input-file allowlist and hashes, equal maximum budget, action set, rubric version, observation class, identity-evidence schema, and projection schema.

It must not contain the SHA of the commit that contains `experiment_binding.json`; that would be a self-referential impossible binding.

After Commit A is pushed and hosted Windows/Linux proof is green, session creation generates immutable `session_manifest.json` from the exact checked-out candidate. The session manifest binds:

```text
candidate_sha
candidate_tree
experiment_binding_hash
evidence_bundle_hash
projection_hash
projection_manifest_hash
projection_schema_hash
operator_instruction_hash
reviewer_instruction_hash
hosted_proof_identity
hosted_proof_hash
session_nonce
one_shot_state
```

`hosted_proof_identity` must be a provider-neutral `OPENSSH_SSHSIG_V1` receipt signed by a pinned proof issuer. Its signed payload binds the exact candidate SHA/tree, workflow name, separate Windows/Linux run IDs and successful conclusions, proof ID, and verification timestamp. Self-asserted green strings or an untrusted/tampered receipt block session creation.

`create_session_state()` re-verifies the pinned-provider hosted-proof signature and copies the bound bundle/projection hashes into the sealed state. `BASELINE_OPEN` verifies the complete signed operator identity record and its session challenge before the first evidence exposure. Projection release fails unless the exact session-bound evidence-bundle and projection hashes are supplied.

Every arm seal, signed identity record, detached attestation, review package, and terminal result binds `session_manifest_hash`. A candidate, artifact, operator-identity, or hosted-proof mismatch blocks exposure.

### A3. Generate the answer-free projection

Expected implementation surface:

```text
core/gv_one_case_delta.py
scripts/gv_one_case_delta_capture.py
```

The module may implement only:

- admissible-evidence bundle assembly from existing banked bytes;
- answer-free projection generation and forbidden-content validation;
- post-hosted-green `session_manifest.json` generation binding candidate, exact pre-human artifacts, instructions, and signed hosted proof;
- pre-exposure operator signed-identity verification, session nonce, and one-shot state transitions;
- equal maximum baseline/post time-budget enforcement with early submission allowed;
- canonical sealing and replay;
- mechanical randomization and scrubbed review-package export;
- detached-attestation validation;
- rubric sealing, mapping reveal, eligibility, and disposition computation.

It must not import, fork, or generalize the 4,600-line synthetic G08 module. Frozen rubric constants or exact result logic may be copied into a small shared specification only when byte-for-byte semantics are preserved and tests prove parity.

### A4. Minimal capture surface

Use a CLI or minimal local form sufficient for one run.

Commit A must not add:

- a comparison-result Streamlit panel;
- current-decision publication;
- stage/count promotion;
- a new global authority manifest;
- a general comparison platform.

### A5. Focused tests and CI filters

Expected test surface:

```text
tests/gv_fs0_product/test_one_case_delta_projection.py
tests/gv_fs0_product/test_one_case_delta_capture.py
tests/gv_fs0_product/test_one_case_delta_attestation.py
.github/workflows/gv-fs0-product.yml
```

Minimum checks:

- clean base and unchanged Alpha current authority;
- baseline/post evidence-byte equality;
- projection includes required analysis and excludes every forbidden answer-bearing field/value;
- baseline cannot open after projection release;
- equal maximum 60-minute budgets; early submission accepted; late arm rejected; actual elapsed times may differ and no latency improvement is inferred;
- pre-exposure abort does not consume the one-shot authorization; any abort or violation after baseline evidence exposure is a consumed terminal ineligible run;
- operator naivete attestation is mandatory for eligibility;
- reviewer package is scrubbed and mapping-blind while retaining each arm's current research action and rationale;
- two separately signed identity records prove distinct verified human-subject commitments and reject same-subject, same-credential, unsigned, self-asserted, or cross-role-substituted evidence;
- detached attestation binds the exact session manifest, seals, package, rubric, and both identity-evidence hashes;
- session creation rejects unsigned, untrusted, candidate-mismatched, tree-mismatched, workflow-mismatched, tampered, or non-green hosted-proof receipts;
- GitHub adapter, when present, is optional and maps into the provider-neutral signed-evidence schema;
- full seal-chain replay detects mutation, omission, reorder, aliasing, or mismatched candidate;
- valid positive, zero, and negative results are retained;
- only an eligible complete result may report observed count 1;
- no Commit A path can mutate `gv_fs0/gv_fs0_current_decision.json` or publish a comparison result.

Necessary CI path filters may be extended for the new core, script, tests, experiment files, and corrected truth surfaces. Do not redesign current authority in Commit A.

### A6. Commit A stop gate

Before push:

```text
focused one-case tests
pytest tests/gv_fs0_product -q
git diff --check
current-context generation and validation
launch_alpha current-decision smoke
```

Then push the exact candidate and require hosted Windows/Linux product green. Stop. Do not open a human session before hosted green.

## One Human Run — Exactly Once

Pinned through `session_manifest.json` to the hosted-green Commit A candidate:

```text
PRE_EXPOSURE_SESSION_PREP
→ generate and seal session_manifest.json
→ verify operator signed identity evidence
→ verify operator eligibility attestation
→ BASELINE_OPEN (first evidence exposure; one-shot becomes consumed)
→ BASELINE_SEAL
→ answer-free projection release
→ POST_OPEN
→ POST_SEAL
→ randomized scrubbed REVIEW_PACKAGE
→ verify different reviewer signed identity evidence
→ different reviewer rubric
→ detached session attestation import
→ rubric, identities, and attestation seal
→ mapping reveal
→ full replay
→ eligibility + disposition
```

Budget semantics:

```text
baseline_maximum = 60 minutes
post_maximum = 60 minutes
early_submission = allowed
actual_elapsed_times = may differ
latency_endpoint = none
latency_improvement_inference = prohibited
```

Abort semantics:

- Before `BASELINE_OPEN`, when no participant has received case evidence, arm instructions, or the projection, a technical or participant-availability abort is `PRE_EXPOSURE_ABORT`; it is retained in an administrative log but does not consume the one-shot run.
- At `BASELINE_OPEN`, evidence exposure begins and the one-shot authorization is irrevocably consumed.
- Any later withdrawal, timeout, identity failure, contamination discovery, protocol violation, or incomplete rubric is sealed as a terminal ineligible consumed run. It does not authorize a replacement run on the same case.

No code or plan changes during the run. Do not repair scores or rerun the case for a preferred sign.

## Commit B — Immutable Result Import and Product Publication

Commit B begins only after one terminal run exists.

Commit B may contain:

- immutable sealed records and terminal result import;
- result replay and publication from the imported authority-bearing result only;
- user-visible comparison panel;
- comparison-bound certified paper `NO_POSITION` publication, if the existing authority chain can be safely rebound;
- stage/count truth cut only when eligibility is true;
- sign-independent finding publication;
- focused hosted proof and independent A/B/C review.

A global authority-manifest redesign is not presumed. It is permitted only if an audit proves the existing narrow publication chain cannot safely bind the comparison result; otherwise retain current authority architecture and add the minimum comparison binding.

### Commit B state rules

Eligible result:

```text
OBSERVED_COMPARISON_COUNT: 0 → 1
FUNCTIONAL_STAGE: CERTIFIED_MULTI_SOURCE_CASE_OPERABLE → ONE_CASE_DECISION_DELTA_OBSERVED
SHIPPED_PRODUCT_SCORE: remains 39
OBSERVATION_CLASS: EVIDENCE_GAP_TRIAGE_ONLY
DECISION_VALUE_DISPOSITION: IMPROVED | NOT_IMPROVED
```

Ineligible result:

```text
retain records as usability dogfood
OBSERVED_COMPARISON_COUNT remains 0
FUNCTIONAL_STAGE remains CERTIFIED_MULTI_SOURCE_CASE_OPERABLE
no current-decision publication from the comparison
```

## Disposition Branching

### `IMPROVED`

Authorize one full original E0 vertical containing:

```text
physical supply identification
→ industry economics
→ MU business capture
→ shareholder capture
→ decision-time price envelope
→ comparison on the same certified portfolio path
```

Do not claim that the triage observation itself established any of those dimensions.

### `NOT_IMPROVED`

- retain and publish the falsification;
- replan packet information architecture;
- do not add more providers, evidence, UI, governance, or infrastructure by default;
- never rerun this case to seek `IMPROVED`.

## Forbidden Scope

```text
provider ingestion or refresh
current price or post-cutoff event use
full E0 economics inside Commit A
comparison UI inside Commit A
current-decision publication inside Commit A
score uplift
FS1 or policy comparison
PEAD reopening
broker, orders, or live capital
synthetic G08 Attempt-2
G08 module generalization
global governance or authority-manifest redesign without a demonstrated Commit B blocker
dirty-root cleanup
```

## Audit Acceptance Checklist

- [ ] Option A deviation explicitly accepted.
- [ ] `OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY` accepted.
- [ ] Existing Alpha export prohibited from the post arm.
- [ ] Answer-free projection include/exclude contract and positive source-file allowlist accepted.
- [ ] Forbidden-path access tests accepted; output scanning alone is insufficient.
- [ ] Operator is materially case/outcome-naive, not merely packet-naive.
- [ ] Reviewer scrub removes timestamps, hashes, product labels, and arm-revealing metadata while retaining current-arm action and rationale.
- [ ] Two separately verifiable signed human identity records accepted; unequal principal strings are insufficient.
- [ ] Candidate SHA moved from static binding to post-hosted-green `session_manifest.json` and gated by a pinned-provider signed Windows/Linux proof receipt.
- [ ] Provider-neutral detached session attestation accepted; GitHub only an adapter.
- [ ] Equal maximum budget, early submission, no-latency-inference, and pre-exposure/consumed-abort semantics accepted.
- [ ] Commit A excludes comparison UI, publication, stage/count promotion, and global authority redesign.
- [ ] Commit B owns immutable result import and product publication.
- [ ] Score remains 39 for either sign.
- [ ] No implementation before audit approval.

## Confirmation Required

```text
CONFIRM A — implement the redlined evidence-gap triage Commit A
```

Alternative:

```text
CONFIRM B — skip triage and build the complete original E0 price/business/shareholder packet first
```
