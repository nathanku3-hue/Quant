# V2 PEAD M6b Request Artifact Identity Repair V1

Status: `TECHNICAL_REPAIR_COMPLETE__TERMINAL_OWNERSHIP_BLOCKED`
Mode: `EXECUTION_PACKET`
RoundID: `ROUND-20260711-REQUEST-ARTIFACT-IDENTITY-REPAIR-V1`
ScopeID: `REQUEST_ARTIFACT_IDENTITY_REPAIR_V1`

## Decision

The bounded two-commit repair is authorized. Preserve the exact four current 20260701 request artifacts, reject divergent or legacy/unbound substitutes, quarantine the false dispatch outputs, and keep dispatch denied.

## Hierarchy

- L1: Terminal Zero quantitative research console.
- L2 active: Docs/Ops artifact identity and governance truth repair.
- L2 held: Data, Strategy, Frontend/UI, provider/source access, publication, and remote operations.
- L3: Commit 1 banks exact payload bytes and restores BLOCK truth; Commit 2 adds a detached identity envelope and terminal verification.

## Commit 1 acceptance checks

- [x] Active truth says dispatch is denied and no message is proven sent.
- [x] False dispatch Markdown, JSON, and dependent PASS report are quarantined with their exact, separately labeled SHA-256 values.
- [x] The exact four current 20260701 request artifacts are tracked without byte changes.
- [x] The canonical decision template states that commit/tree identity must be supplied by a detached envelope, not embedded self-referentially in the payload.
- [x] Commit 1 contains docs-only bounded repair files; unrelated workspace changes remain unstaged.

## Commit 2 acceptance checks

- [x] A tracked Gate A/B/C identity envelope binds Commit 1's canonical remote, repository root, commit, tree, four artifact paths, and four distinct SHA-256 values.
- [x] Envelope status is `PREPARED_NOT_SENT`; it grants no dispatch, source access, validation, readiness, Gate D, publication, or data-output authority.
- [x] Governance preflight PASS with 0 findings and planning boot preflight PASS.
- [x] Fresh Reviewer A, B, and C technical check sets PASS against semantics, Git/blob identity, and fail-closed integrity/scope.
- [ ] Distinct-agent ownership check; unavailable in this tool session, therefore terminal SAW remains BLOCK.
- [x] Final truth remains fail-closed for dispatch and strict M6b readiness.

## Detached-binding rule

A payload cannot contain its own final commit or tree identity without changing the bytes being identified. Therefore:

1. Bank the unchanged payload files in Commit 1.
2. Resolve Commit 1's remote, repository root, commit, tree, artifact paths, and artifact hashes.
3. Record those values in a separate tracked envelope in Commit 2.
4. Never treat the envelope as self-binding; a later detached envelope is required if the envelope itself needs commit/tree attestation.

## Forbidden scope

No remotes, dispatch, source or provider access, credentials, export, archive inspection, factual gate validation, strict readiness promotion, Gate D, publication, strategy/UI work, or data output. Do not redirect to or cherry-pick the divergent `51b1471ff93741fd339d506399413c928479db5a` lineage.

## Next action

Reserve distinct implementer and Reviewer A/B/C agents and rerun terminal ownership review against the unchanged detached envelope. Do not dispatch.
