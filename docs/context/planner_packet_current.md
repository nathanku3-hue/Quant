# Planner Packet - Current

## Active — GV-ALPHA0-SHIP browser pilot closed; release next (2026-07-28)

- Ship branch `codex/gv-alpha0-ship` is clean and synchronized at `a88ed05bbd360d8cc053f9ed835992c48958e7f5`.
- One complete workflow is implemented: launch → deterministic sealed sample → review → confirm paper `NO_POSITION` → persist → reopen certified state.
- Hosted run `30346381138` is fully green: Windows/Linux product suites, clean commit-bound package builds, isolated extracted-package smokes, artifact uploads, and exact byte parity PASS.
- Windows and Linux produced the same clean artifact: 18,666,047 bytes, SHA-256 `67f5b154182be5d9cecf050934a81b107a8d38e9ea072f0df565dd6b24fe2d57`, source commit `a88ed05`, tree state `clean`.
- Independent local rebuild matched the hosted hash exactly; a newly created Windows venv completed initialize → confirm → persist → reopen smoke PASS. Native Windows focused suite remains **39/39 PASS**.
- Clean-package browser pilot PASS: a fresh Streamlit server was operated through Chromium, confirmed with `PILOT_BROWSER_OPERATOR_001`, persisted `CASE_WORKSPACE_UI` certification, then restarted against the same user-data root and reopened certified-only in 4.435 seconds. No P0/P1 was found.
- Product score remains **39**; observed remains **0**; stage remains `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`; release readiness advances to **87/100** planning-only.
- Immediate gate: tag and publish the clean `a88ed05` artifact; no repair commit is needed.
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
