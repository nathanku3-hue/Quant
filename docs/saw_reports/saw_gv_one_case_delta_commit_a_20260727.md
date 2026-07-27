# SAW Report — GV One-Case Evidence-Gap Triage Commit A

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Decision Value Observation, Product Runtime, Data Custody, Human Identity, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/gv-one-case-decision-delta-brief.md

RoundID: ROUND-20260727-GV-ONE-CASE-DELTA-COMMIT-A
ScopeID: GV_ONE_CASE_EVIDENCE_GAP_TRIAGE_COMMIT_A

## Scope

Implement only the audited pre-human Commit A machinery for one `EVIDENCE_GAP_TRIAGE_ONLY` observation, prove it locally, push one exact candidate, require hosted Windows/Linux green, and stop before human exposure. Commit B publication, score/stage/count promotion, provider work, and any human session are excluded.

## Ownership Check

Implementer: current assistant session.

Independent implementation Reviewer A/B/C agents are not available in this execution environment. The user supplied an independent plan audit PASS before implementation, but that does not substitute for independent review of the implemented bytes. Mechanical strategy, runtime, and data-integrity checks are complete and green; terminal SAW remains BLOCK until independent implementation reviewers examine the candidate.

## Acceptance Checks

- CHK-01: Preserve `OBSERVATION_CLASS = EVIDENCE_GAP_TRIAGE_ONLY`; no full-E0, investment-value, portfolio-value, or alpha claim.
- CHK-02: Generate deterministic answer-free projection from exactly nine positive allowlisted path/hash inputs.
- CHK-03: Reject forbidden direct, relative, mutated, symlink, junction, hard-link, alias, and outside-repository source access before admission.
- CHK-04: Keep candidate SHA/tree out of static binding and require post-hosted-green `session_manifest.json` binding.
- CHK-05: Require separately signed operator/reviewer credential challenges plus pinned-issuer verified-human bindings; unequal principal strings alone are insufficient.
- CHK-06: Retain blinded current-arm action/rationale while excluding prior Alpha/portfolio answers and origin metadata.
- CHK-07: Enforce equal maximum 3,600-second budgets, early submission, no latency endpoint, and exact pre-exposure/consumed abort semantics.
- CHK-08: Detect seal-chain mutation, omission, reorder, aliasing, candidate mismatch, identity substitution, and attestation mismatch.
- CHK-09: Preserve current Alpha authority bytes, score 39, stage `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`, observed 0, and no alpha claim.
- CHK-10: Pass the hosted-product local test matrix, context validation, deterministic artifact replay, AppTest/current-decision smoke, and `git diff --check`.
- CHK-11: Independent Reviewer A strategy/regression pass.
- CHK-12: Independent Reviewer B runtime/operational-resilience pass.
- CHK-13: Independent Reviewer C data-integrity/performance-path pass.
- CHK-14: Push one exact candidate and require hosted Windows/Linux product green before any human exposure.

## Implementer Pass

PASS.

Delivered:

- `core/gv_one_case_delta.py`: source custody, deterministic projection, session binding, one-shot capture, seals/replay, blinding, signed-human identity validation, detached attestation, rubric/disposition.
- `scripts/gv_one_case_delta_capture.py`: deterministic build, hosted-green session-manifest creation, and identity preflight; no automatic human exposure or publication command.
- `data/gv_one_case_delta/case_1/*`: static experiment binding, answer-free artifacts, projection manifest, and operator/reviewer instructions.
- three focused test modules plus existing Windows/Linux product workflow coverage.
- post-merge truth correction across active roadmap, README, current context, formula register, lesson register, and current-truth surfaces.

## Reviewer A — Strategy and Regression Risks

Status: Unavailable for independent ownership.

Mechanical pass: PASS.

- Audited observation class and claim boundary remain explicit.
- Commit A/Commit B separation is enforced in code, tests, CLI, workflow paths, and active truth.
- No current-authority publisher, comparison UI, provider ingestion, price path, portfolio mutation, or stage/count promotion was added.
- Static binding is non-self-referential; runtime candidate binding requires a pinned-provider signed hosted-proof receipt and binds the exact evidence bundle, projection, projection manifest, schema, and instructions. Untrusted, tampered, mismatched, non-green, or substituted evidence fails closed.

Independent candidate review remains required.

## Reviewer B — Runtime and Operational Resilience

Status: Unavailable for independent ownership.

Mechanical pass: PASS.

- Focused state-machine and SSHSIG tests pass on Windows Python 3.12.10.
- One-shot consumption begins exactly at `BASELINE_OPEN`.
- Exact elapsed duration is checked before integer reporting; one microsecond over budget fails.
- Canonical SSHSIG messages are verified through binary stdin, avoiding Windows newline rewriting.
- Event replay rejects mutation, omission, reorder, duplicate alias, and broken previous-hash links.
- `BASELINE_OPEN` verifies and binds the complete operator signed-identity record before exposure; terminal replay rejects operator substitution.
- Reviewer preflight evidence cannot authorize a final result; final evidence binds exact package/rubric.
- Terminal eligibility replays signed identities, event hashes, rubric, package, detached attestation, and mapping order before emitting a non-publishing result.
- AppTest/current-decision smoke remains green.

Independent candidate review remains required.

## Reviewer C — Data Integrity and Performance Path

Status: Unavailable for independent ownership.

Mechanical pass: PASS.

- Projection reads exactly nine path/hash-bound files and records the complete read set.
- Direct forbidden-source reads fail before bytes are admitted; mutation and path alias classes fail closed.
- Tracked bundle, projection, and manifest exactly equal a fresh deterministic rebuild.
- Current certified bundle and current decision have no diff; current decision remains SHA-256 `d939cd67e247b4f25c254cbec515b9f15e2e1d6efd2b9c87f023a86d5b249e13`, 23,942 bytes.
- The slice is one-case bounded and adds no provider, broad data transform, or performance-critical portfolio loop.

Independent candidate review remains required.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High | Independent implementation Reviewer A/B/C ownership is unavailable, so mechanical green cannot produce terminal SAW PASS. | Push the exact tested candidate, require hosted parity, then obtain independent A/B/C candidate review before human exposure. | Product owner / independent reviewers | Open |
| Medium | Initial budget check truncated elapsed time before comparison and admitted a one-microsecond overrun. | Compare exact duration before integer reporting; focused boundary test added. | Implementer | Fixed |
| Medium | Initial Windows SSHSIG verification used text stdin, which could rewrite canonical line endings. | Verify canonical document bytes through binary stdin; real OpenSSH key/sign/verify tests added. | Implementer | Fixed |
| Medium | Initial CLI direct execution failed because repository root was not placed on `sys.path` before importing `core`. | Added the standard repository-root bootstrap and a direct-entrypoint regression test. | Implementer | Fixed |
| High | Reviewer identity initially proved session/role control but did not bind the exact review package and rubric; terminal eligibility initially accepted caller-supplied authority hashes. | Split reviewer preflight from final package/rubric-bound evidence; terminal sealing now replays both signed identities, complete sealed event hashes, rubric, package, and detached attestation before mapping reveal. | Implementer | Fixed |
| High | Session creation initially accepted self-asserted hosted-green strings from a local JSON file. | Require a pinned-provider SSHSIG receipt binding exact candidate SHA/tree, workflow, separate Windows/Linux run IDs and SUCCESS conclusions, proof ID, and verification timestamp. | Implementer | Fixed |
| High | Initial exposure state did not bind the exact bundle/projection artifacts and accepted an operator identity hash without verifying the signed record. | Bind bundle/projection/manifest/schema hashes in the session, replay hosted proof on state creation, verify full operator identity before `BASELINE_OPEN`, and reject post-exposure substitution. | Implementer | Fixed |
| Low | One all-in-one CI-equivalent local command hit two DevSpace transport 502 responses. | Executed the identical test matrix in deterministic segments; all 425 collected tests passed. Hosted CI remains the exact-candidate parity authority. | Environment | Mitigated |

## Scope Split Summary

In-scope findings/actions:

- static experiment custody;
- positive source allowlist and answer-free deterministic projection;
- minimal pre-human session/seal/blinding/replay machinery;
- provider-neutral signed identity adapter and detached attestation;
- focused tests and existing product workflow extension;
- post-merge truth correction and implementation evidence.

Inherited out-of-scope findings/actions:

- one materially case/outcome-naive operator and a different blinded reviewer are not yet supplied;
- actual signed identity records and `session_manifest.json` require an exact hosted-green candidate;
- human exposure, terminal result, UI, current publication, and stage/count promotion belong after this stop gate and to Commit B where applicable;
- full original E0 economics remains deferred.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
| --- | --- | --- |
| `core/gv_one_case_delta.py` | Narrow source/session/identity/seal/replay/rubric machinery with no publication authority. | Mechanical PASS; independent review pending |
| `scripts/gv_one_case_delta_capture.py` | Pre-human deterministic build, session-manifest, and identity-preflight CLI. | Mechanical PASS; independent review pending |
| `data/gv_one_case_delta/case_1/*` | Frozen binding, instructions, evidence bundle, answer-free projection, projection manifest. | Mechanical PASS; independent review pending |
| `tests/gv_fs0_product/test_one_case_delta_*.py` | 25 focused projection, state, artifact-binding, identity, attestation, and mutation tests. | PASS |
| `.github/workflows/gv-fs0-product.yml` | Existing Windows/Linux product gate includes Commit A paths and custody hashes. | Static PASS; hosted pending |
| `docs/phase_brief/gv-one-case-decision-delta-brief.md` | Audit authority and live Commit A state. | PASS |
| `docs/context/*`, `docs/architecture/top_level_roadmap.md`, `README.md` | Alpha merge correction and pre-human stop gate. | PASS |
| `docs/notes.md`, `docs/lessonss.md` | Formula/identity registry and implementation lessons. | PASS |

## Document Sorting

Canonical review order:

1. `docs/phase_brief/gv-one-case-decision-delta-brief.md`
2. `core/gv_one_case_delta.py`
3. `data/gv_one_case_delta/case_1/experiment_binding.json`
4. `data/gv_one_case_delta/case_1/projection_manifest.json`
5. `scripts/gv_one_case_delta_capture.py`
6. focused tests
7. workflow
8. active truth and registries
9. this SAW report

## Validation Evidence

- Focused Commit A suite: 25 passed.
- Existing product core/authority group: 89 passed.
- E0B/B0/Alpha custody group: 147 passed.
- Streamlit/AppTest/current-decision group: 14 passed.
- Frozen protocol/external GV-FS0 group: 150 passed.
- Total hosted-product matrix: 425 passed; one existing websockets deprecation warning only.
- Deterministic tracked pre-human artifact replay: PASS.
- Current-context generation/validation: PASS.
- Current decision: unchanged SHA-256 `d939cd67e247b4f25c254cbec515b9f15e2e1d6efd2b9c87f023a86d5b249e13`, 23,942 bytes.
- Active merge-pending drift scan: PASS.
- Python compile: PASS.
- `git diff --check`: PASS.
- No human exposure, result, current publication, score change, observed-count change, or stage promotion exists.

## Open Risks

Open Risks:

- independent implementation Reviewer A/B/C candidate review is unavailable in this environment and remains mandatory before human exposure;
- exact-candidate hosted Windows/Linux proof is pending until the one authorized push;
- two eligible separately verified humans and their signed identity evidence have not been supplied;
- the current user is exposed to the Alpha case and implementation context and therefore cannot serve as the materially case/outcome-naive operator.

Next action: freeze one commit, push the exact candidate once, require hosted Windows/Linux green, then stop for independent candidate audit and two-human preflight without opening `BASELINE_OPEN`.

ClosureValidation: PASS
SAWBlockValidation: PASS

ClosurePacket: RoundID=ROUND-20260727-GV-ONE-CASE-DELTA-COMMIT-A; ScopeID=GV_ONE_CASE_EVIDENCE_GAP_TRIAGE_COMMIT_A; ChecksTotal=14; ChecksPassed=10; ChecksFailed=4; Verdict=BLOCK; OpenRisks=independent_reviewer_a_b_c_unavailable_hosted_candidate_pending_two_eligible_humans_not_supplied; NextAction=commit_push_once_require_hosted_windows_linux_green_then_stop_for_independent_candidate_audit
