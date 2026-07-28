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
- Native Windows focused product tests: `39/39 PASS`, including real Windows-junction, tampered-package, and hosted custody-path regressions.
- Deterministic package test: two local builds byte-identical.
- Fresh extracted Windows package smoke: PASS.
- Hosted-cleanliness repair commit `a88ed05bbd360d8cc053f9ed835992c48958e7f5` is pushed; branch is clean and synchronized.
- Hosted run `30346381138`: Windows/Linux full product suites, clean package builds, isolated extracted-package smokes, uploads, authority parity, and exact archive parity PASS.
- Clean Windows and Linux artifacts are byte-identical: 18,666,047 bytes, SHA-256 `67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57`, source tree state `clean`.
- Independent local rebuild matches the hosted hash; a newly created Windows venv completes initialize → confirm → persist → reopen smoke PASS.
- Clean-package Chromium pilot PASS: a fresh Streamlit server opened sealed state, `PILOT_BROWSER_OPERATOR_001` confirmed through the real UI, `CASE_WORKSPACE_UI` certification persisted, and a restarted server reopened certified-only in 4.435 seconds. No P0/P1 was found.
- Workflow YAML parse: PASS.
- `git diff --check`: PASS.

The artifact hash above is the clean commit-bound release candidate hash for `a88ed05`.

## Score and claim boundary

Canonical product score remains **39/100**. Observed comparison count remains **0**. Stage remains `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`. No decision-improvement, alpha, provider, live-capital, or score-uplift claim is added.

Release-readiness planning estimate:

| Dimension | Before | Candidate | Evidence |
|---|---:|---:|---|
| Primary user flow | 70 | 90 | launch-review-confirm-persist-reopen tested |
| Startup resilience | 40 | 85 | manifest-first validation and canonical path confinement pass locally and hosted |
| Persistence/data safety | 55 | 85 | user-writable root plus junction/symlink escape refusal accepted and packaged-smoked |
| Packaging | 10 | 90 | clean commit-bound deterministic artifact and exact SHA proven on both OS families |
| Cross-platform proof | 40 | 90 | hosted Windows/Linux builds, isolated smokes, and exact byte parity PASS |
| Onboarding/rollback | 25 | 75 | packaged runbooks and wrappers |
| Pilot evidence | 0 | 85 | real-browser packaged workflow completed; no P0/P1 found |
| **Overall release readiness** | **45** | **87** | hosted, clean-machine, and browser-pilot proof closed |

This is a shipment-planning estimate, not a product score uplift.

## Forbidden scope

- Trust anchors, receipts, identity systems, session manifests, human comparison, or A/B/C release machinery.
- Experimental commits `14b3773` and `e582136`.
- Providers, network data, broker/order paths, live capital, real-price expansion, scoring/ranking, formal comparison, or research-platform redesign.
- Automatic migration or overwrite of an existing user workspace.

## Remaining gates

1. Tag the clean `a88ed05` release candidate.
2. Publish the release artifact and minimal onboarding/rollback notes.
