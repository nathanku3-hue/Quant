# GV-ALPHA0 Two-Week Ship Slice

Date: 2026-07-28
Branch: `codex/gv-alpha0-ship`
Base: `main@48a43b99350465202f8bcd09113a34fa724580af`
Mode: product shipment reliability

## Endgame intent

Ship one usable, broker-free, certified paper-decision product. Preserve the existing Alpha decision engine and Case Workspace; improve only the path from installation to completed and reopened workflow.

## Complete user workflow

```text
launch
-> fail-closed startup diagnostics
-> initialize deterministic sealed sample in user-writable storage
-> review both-source evidence
-> confirm paper NO_POSITION
-> persist certified result
-> reopen the same certified state
```

## Implemented candidate scope

- Platform user-data root, overridable with `GV_ALPHA0_HOME` or `--data-dir`.
- Deterministic first-run seed containing only the two immutable source families and five sealed pre-adjudication artifacts.
- Exact `RELEASE_MANIFEST.json` validation of every packaged file before initialization, followed by exact seeded-byte verification; tamper, missing bytes, invalid/missing manifests, seed-version mismatch, and unmanaged nonempty roots fail closed.
- Canonical package/runtime/seed confinement rejects Windows junctions or symlinks that route storage into the bundle or seed paths outside the runtime root.
- Operator writes remain outside the installed package/repository.
- Deterministic versioned ZIP with fixed metadata, exact packaged-file manifest, commit identity, artifact SHA-256, Windows/Linux wrappers, onboarding, rollback, and fresh-extraction smoke.
- Hosted Windows/Linux workflow prepared to run product tests, build, smoke, upload, and compare exact release bytes.

## Evidence

- Entry custody: exact base, clean named branch, `0 ahead / 0 behind` before edits.
- Native Windows focused product tests: `38/38 PASS`, including two real Windows-junction regressions and two tampered-package regressions.
- Deterministic package test: two local builds byte-identical.
- Fresh extracted Windows package smoke: PASS.
- Native Windows/Linux package parity: exact same 18,666,057-byte repaired-candidate ZIP, SHA-256 `1fee91f0e7880fe5070c252649408fc7ad90246e3a1f1a214895fd6d706a9f00`.
- Workflow YAML parse: PASS.
- `git diff --check`: PASS.

The artifact hash above is a dirty-worktree candidate hash, not a releasable commit-bound hash. A clean commit changes the embedded release manifest and therefore produces the final artifact hash.

## Score and claim boundary

Canonical product score remains **39/100**. Observed comparison count remains **0**. Stage remains `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`. No decision-improvement, alpha, provider, live-capital, or score-uplift claim is added.

Release-readiness planning estimate:

| Dimension | Before | Candidate | Evidence |
|---|---:|---:|---|
| Primary user flow | 70 | 90 | launch-review-confirm-persist-reopen tested |
| Startup resilience | 40 | 75 | manifest-first validation and canonical path confinement pass locally; re-audit pending |
| Persistence/data safety | 55 | 80 | user-writable root plus junction/symlink escape refusal; re-audit pending |
| Packaging | 10 | 75 | deterministic narrow ZIP, complete file manifest, and SHA sidecars; re-audit pending |
| Cross-platform proof | 40 | 72 | local archive parity; hosted runtime pending |
| Onboarding/rollback | 25 | 75 | packaged runbooks and wrappers |
| Pilot evidence | 0 | 0 | not yet performed |
| **Overall release readiness** | **45** | **65** | intentionally held pending independent re-audit |

Expected readiness after independent acceptance, hosted Windows/Linux green, and clean fresh-machine smoke: **80/100**. Expected after one successful pilot and P0/P1 usability repair: **87/100**. These are shipment-planning estimates, not product score uplifts.

## Forbidden scope

- Trust anchors, receipts, identity systems, session manifests, human comparison, or A/B/C release machinery.
- Experimental commits `14b3773` and `e582136`.
- Providers, network data, broker/order paths, live capital, real-price expansion, scoring/ranking, formal comparison, or research-platform redesign.
- Automatic migration or overwrite of an existing user workspace.

## Remaining gates

1. Independent re-audit of the repaired candidate diff.
2. Commit the accepted slice and push the ship branch.
3. Hosted Windows/Linux product, package, smoke, and byte-parity green.
4. Build clean commit-bound release artifact.
5. Smoke on clean Windows and Linux machines.
6. One real pilot user completes the workflow.
7. Fix P0/P1 usability failures only; tag and publish.
