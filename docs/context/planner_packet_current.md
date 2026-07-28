# Planner Packet - Current

## Active — GV-ALPHA0-SHIP repaired local candidate ready for re-audit (2026-07-28)

- Branch `codex/gv-alpha0-ship` was opened clean at exact accepted `main@48a43b9`; entry was `0 ahead / 0 behind`.
- One complete workflow is implemented: launch → deterministic sealed sample → review → confirm paper `NO_POSITION` → persist → reopen certified state.
- Native Windows focused product suite: **38/38 PASS**, including two real Windows-junction regressions and two tampered-package regressions. Fresh extracted Windows package smoke: PASS.
- Native Windows/Linux builders produced exact repaired-candidate ZIP parity: 18,666,057 bytes, SHA-256 `1fee91f0e7880fe5070c252649408fc7ad90246e3a1f1a214895fd6d706a9f00`.
- Candidate hash is dirty-worktree evidence only; final commit-bound artifact hash remains open.
- Product score remains **39**; observed remains **0**; stage remains `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`; release-readiness estimate is held at **65/100** planning-only pending independent re-audit.
- P1 repair: package bytes are validated against `RELEASE_MANIFEST.json` before initialization; runtime/seed paths are canonicalized and linked escapes or package-entry routes fail closed.
- Immediate gate: independent re-audit → accepted commit/push → hosted Windows/Linux green → clean artifact → fresh machines → pilot → release.
- Do not open trust anchors, receipts, identities, human comparison, providers, formal score uplift, live capital, or research redesign.

## New Context Packet — GV-ALPHA0-CLOSE complete on branch (2026-07-25)

## What Was Done
- Alpha close vertical complete on branch `codex/gv-alpha0-rc2` (base `origin/main@06ce68f`).
- Commit A selective Alpha import (no dashboard/page-registry); Commit B dogfood import + guarded publish-current + truth cut; Commit C docs-only current-truth sync.
- Stage **CERTIFIED_MULTI_SOURCE_CASE_OPERABLE**; current decision **DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1** (paper NO_POSITION); CDR `889cc831…` published.
- Receipt v3 + human attestation v1 bound to Commit A tip `6747d6a`; tag `gv-alpha0-close-rc2` immutable on RC2 ancestry.
- Metrics locked: score **39**; observed **0**; no alpha claim.

## What Is Locked
- Alpha product shipment is ready on branch; **merge to main is pending** (merge-commit only; preserve `gv-alpha0-close-rc2` ancestry).
- `FUNCTIONAL_STAGE = CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`.
- Current decision authority: `DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1` → paper `NO_POSITION`.
- Score **39** frozen; observed **0**; formal comparison still deferred; no live capital / score uplift.
- Broker-free entry: `python launch_alpha.py` (Case Workspace).

## What Is Next
```text
immediate gate: merge Alpha to main (merge commit, not squash/rebase)
→ after hosted green: merge
→ fresh-clone 25-test + verify/replay/current-receipt smoke
→ final tag gv-alpha0-close on accepted main commit (RC2 tag stays immutable)
→ first post-merge product gate: one fresh real ONE_CASE_DECISION_DELTA_OBSERVED comparison
   (not another custody/governance/provider phase)
```

## First Command
```text
.venv\Scripts\python -m pytest -q tests/gv_fs0_product/test_v2_alpha0_case_close.py tests/gv_fs0_product/test_v2_alpha0_alpha_app.py
```
