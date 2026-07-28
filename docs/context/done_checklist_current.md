# Done Checklist - Current

## Active — GV-ALPHA0-SHIP (2026-07-28)

- [x] Named isolated branch at exact accepted `main@48a43b9`; clean and `0/0` before implementation.
- [x] One reliable launch path with fail-closed diagnostics and explicit `--data-dir` support.
- [x] Deterministic sealed first-run sample; no prior confirmation or certified result copied.
- [x] User-writable persistence outside package/repository.
- [x] Complete review → confirm paper `NO_POSITION` → persist → reopen workflow.
- [x] Native Windows focused suite **39/39 PASS**.
- [x] Canonical runtime confinement rejects Windows-junction routes into the bundle and linked seed paths escaping runtime.
- [x] Extracted package validates the complete `RELEASE_MANIFEST.json` before initialization; modified seed bytes and missing/fake-manifest fallback fail closed.
- [x] Deterministic versioned allowlisted ZIP, manifest, artifact hash, onboarding, and rollback.
- [x] Fresh extracted Windows package smoke PASS.
- [x] Native Windows/Linux package build byte parity PASS.
- [x] Hosted Windows/Linux workflow updated for tests, package, smoke, upload, and byte parity.
- [x] Independent re-audit accepted the repaired shipment diff.
- [x] Accepted shipment commit `ec5c1ea` pushed on `codex/gv-alpha0-ship`.
- [x] Hosted-cleanliness repair committed and pushed at `a88ed05`; branch is clean and synchronized.
- [x] Hosted run `30346381138` passes Windows/Linux product suites, clean package builds, isolated extracted smokes, artifact uploads, authority parity, and exact byte parity.
- [x] Clean commit-bound artifact is 18,666,047 bytes with SHA-256 `67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57`.
- [x] Clean-machine smoke passes on ephemeral hosted Windows/Linux runners and an independent new Windows venv.
- [x] Clean-package Chromium pilot completes sealed review → UI confirm → persist → server restart → certified-only reopen with `PILOT_BROWSER_OPERATOR_001`.
- [x] Pilot P0/P1 review found no release-blocking or materially confusing defects; no repair code is needed.
- [ ] Tag and publish release.
- [ ] Formal comparison, score uplift, providers, and live capital remain deferred.

## Active — GV-ALPHA0-CLOSE complete on branch (2026-07-25)

- [x] Source family one (B0B) banked; source family two banked; multi-source close vertical implemented.
- [x] Commit A selective Alpha import on `06ce68f` (exclude dashboard/page-registry).
- [x] Receipt v3 browser UI dogfood + human attestation v1 on Commit A tip (not donor dfb63ff).
- [x] Commit B: import exact dogfood artifacts; guarded publish-current; atomic truth cut (roadmap/README/current decision).
- [x] Stage **CERTIFIED_MULTI_SOURCE_CASE_OPERABLE**; decision **DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1**; score **39**; observed **0**; no alpha claim.
- [x] Tag `gv-alpha0-close-rc2` immutable on RC2 ancestry.
- [ ] **Merge Alpha to main** (merge commit, not squash/rebase) — **immediate gate**.
- [ ] Post-merge: fresh-clone 25-test + verify/replay/current-receipt smoke; final tag `gv-alpha0-close` on accepted main commit.
- [ ] First post-merge product gate: one fresh real **ONE_CASE_DECISION_DELTA_OBSERVED** comparison (not custody/governance/provider phase).
- [ ] Formal multi-case comparison / score uplift / live capital: deferred.

## Banked substrate

| Slice | Classification | Role |
|---|---|---|
| B0A | `GV-V2-B0A-LOCAL-SOURCE-ABSTENTION` | Immutable local abstention |
| B0B | `GV-V2-B0B-OFFICIAL-SOURCE-INTAKE` | Source family one |
| Family two | banked NVDA package | Source family two |
| Alpha close | `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE` | Current published decision authority |
