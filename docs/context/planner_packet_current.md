# Planner Packet - Current

## Active — GV-ALPHA0-SHIP hosted-cleanliness repair pending commit (2026-07-28)

- Accepted shipment commit `ec5c1ea71dd4f87dc1b2b09adbefe7775028c392` is pushed on `codex/gv-alpha0-ship`; local and remote were clean and `0/0` before the hosted run.
- One complete workflow remains implemented: launch → deterministic sealed sample → review → confirm paper `NO_POSITION` → persist → reopen certified state.
- Hosted run `30343141406`: Windows and Linux full product suites PASS; both deterministic package builds FAIL with `GV_ALPHA0_RELEASE_DIRTY_WORKTREE_REFUSED`; byte parity is skipped.
- Root cause: the workflow wrote `gv-fs0-environment-custody.json` inside the Git checkout before invoking the clean-tree release builder.
- Bounded repair: write/upload custody evidence from `${{ runner.temp }}` / `RUNNER_TEMP`; no builder exception or scope expansion. Native Windows focused suite is now **39/39 PASS**, workflow YAML and diff checks PASS.
- Product score remains **39**; observed remains **0**; stage remains `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`; release readiness remains **65/100** pending a green hosted rerun.
- Immediate gate: commit/push this two-file workflow repair → hosted Windows/Linux/package/parity green → clean artifact → fresh machines → pilot → release.
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
