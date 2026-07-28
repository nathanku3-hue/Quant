# Done Checklist - Current

## Active — GV-ALPHA0-SHIP (2026-07-28)

- [x] Named isolated branch at exact accepted `main@48a43b9`; clean and `0/0` before implementation.
- [x] One reliable launch path with fail-closed diagnostics and explicit `--data-dir` support.
- [x] Deterministic sealed first-run sample; no prior confirmation or certified result copied.
- [x] User-writable persistence outside package/repository.
- [x] Complete review → confirm paper `NO_POSITION` → persist → reopen workflow.
- [x] Native Windows focused suite **38/38 PASS**.
- [x] Canonical runtime confinement rejects Windows-junction routes into the bundle and linked seed paths escaping runtime.
- [x] Extracted package validates the complete `RELEASE_MANIFEST.json` before initialization; modified seed bytes and missing/fake-manifest fallback fail closed.
- [x] Deterministic versioned allowlisted ZIP, manifest, artifact hash, onboarding, and rollback.
- [x] Fresh extracted Windows package smoke PASS.
- [x] Native Windows/Linux package build byte parity PASS.
- [x] Hosted Windows/Linux workflow updated for tests, package, smoke, upload, and byte parity.
- [ ] Independent re-audit of repaired candidate diff.
- [ ] Accepted commit and push on `codex/gv-alpha0-ship`.
- [ ] Hosted Windows/Linux green.
- [ ] Clean commit-bound release artifact and hashes.
- [ ] Clean Windows and Linux machine smoke.
- [ ] One pilot user completes the workflow; fix P0/P1 only.
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
