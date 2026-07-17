# Ship-Fast Decision Gate

Status: Template
Purpose: force every expert handoff, approval/request packet, or execution round to answer the one next decision before expanding into governance.

## Repository Identity Gate (required for approval/request packets)

Canonical repository remote:

Repository root:

Payload commit SHA:

Payload tree SHA:

Markdown artifact path:

Markdown artifact SHA-256:

JSON artifact path:

JSON artifact SHA-256:

Detached identity-envelope path:

Envelope lifecycle status:

### Detached-binding rule

A file cannot embed its own final commit or tree identity without changing the bytes being identified. Identity therefore uses a detached two-commit binding:

1. Bank the exact payload bytes in payload commit N.
2. Resolve commit N's canonical remote, repository root, commit, tree, artifact paths, and distinct per-file SHA-256 values.
3. Record those values in a separate tracked identity envelope in commit N+1.
4. Treat the envelope as binding commit N only. The envelope does not bind its own commit/tree; a later detached envelope is required if that identity is needed.

Never use one ambiguous “packet hash” for multiple files. Markdown and JSON paths and hashes must be labeled separately. A lifecycle value such as `PREPARED_NOT_SENT` is not dispatch proof or authority.

Verification evidence:
- Every Git subprocess used for identity verification runs with `GIT_NO_REPLACE_OBJECTS=1`.
- Git identity subprocesses remove inherited Git directory, worktree, common-directory, object-store, index, namespace, and `GIT_CONFIG_*` redirections before resolving the declared repository.
- `refs/replace/*` is empty when enumerated through Git (including packed refs); any present or uninspectable replacement ref denies the packet.
- The payload commit and upstream reference resolve as raw commit objects, not merely SHA-shaped tag/object IDs.
- The payload commit resolves to the declared payload tree.
- Every declared artifact exists at its declared path in that exact payload commit.
- Every artifact's bytes hash to its separately declared SHA-256.
- The detached envelope declares the same canonical repository identity, payload commit, payload tree, artifact paths, and artifact hashes.
- Every authority, evidence, request, and identity-envelope JSON object is parsed with duplicate-member rejection at every nesting level; a duplicate key denies the packet before authorization evaluation or output creation. Ambiguous legacy JSON is invalid and is not grandfathered.

Mismatch rule: deny the packet and perform no authority transfer, dispatch, or execution. Reject legacy, divergent, reconstructed, redirected, cherry-picked, or unbound artifacts; do not synthesize provenance or silently substitute another branch. Replacement-ref presence, Git identity unavailability, self-referential identity, ambiguous hashes, or ambiguous JSON are mismatches.

What is done:

What is blocked:

User order interpreted as:

Recommended next step:

Why this is correct:

Alternatives considered:

Decision needed from user: approve / redirect / hold

Scope limit:

Stop rule:
