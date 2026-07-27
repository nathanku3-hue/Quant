# Hosted Proof Receipt — Candidate 14b3773

This directory is detached evidence for runtime candidate:

```text
candidate_sha  = 14b37734b4ea0d5b4cb61f6bcea56accbd52ff87
candidate_tree = 54d24cf15a7f27f5399e2ac07ea603e4accf4738
```

It is intentionally committed after the candidate. A commit cannot contain authoritative proof of its own future hosted run without self-reference.

## Bound hosted evidence

Product workflow `GV-FS0 Product`, run `30285531998`:

- Windows job `90042256003`: `SUCCESS`
- Ubuntu job `90042256059`: `SUCCESS`
- Windows/Linux byte-parity job `90043281214`: `SUCCESS`

Protocol workflow `GV-FS0 Protocol Freeze`, run `30285532512`:

- Windows job `90042257227`: `SUCCESS`
- Ubuntu job `90042257211`: `SUCCESS`
- Windows/Linux byte-parity job `90042562009`: `SUCCESS`

`hosted_proof.json` is signed under namespace `gv-one-case-hosted-proof-v1` using the public key pinned in `trusted_proof_issuers.json`. The runtime function `verify_hosted_proof()` validates the signature, exact candidate SHA/tree, Product workflow name, and successful Windows/Linux conclusions. The focused receipt test additionally requires both parity jobs and Protocol Freeze jobs to be successful.

This receipt does not create `session_manifest.json`, open `BASELINE_OPEN`, validate human eligibility, publish a result, or change current authority.

The candidate worktree and the root checkout are separate custody domains. The candidate branch is clean at `14b3773`; the root checkout `main@accef5c` is massively dirty and must not be used as candidate evidence.
