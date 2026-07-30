# SAW Report — GV Micro-Portfolio V0 Terminal Repair — 2026-07-30

## Verdict

`REPAIR_COMPLETE_LOCALLY; NOT_ACCEPTED`

The bounded portfolio candidate is materially stronger and all affected gates pass, but repository-wide closure and genuinely independent review remain open.

## Base and scope

- Base: `9ebc973a8cc3cfbd4899ed724733cc22c606fbbf`.
- Branch: `codex/gv-micro-portfolio-v0-repair`.
- Product runtime: read-only.
- Replay implementation: read-only.
- Modified authority: Integrator, Accounting, Strategy, stale tests, checkout attributes, and current truth surfaces.

## Local role-separated audit

These lanes were performed in one assistant session and are **not independent reviewers**.

### Reviewer A — functional and accounting

Found and repaired:

- non-contiguous declared event sequences were accepted;
- certification validated a filtered event list that could not satisfy a strict contiguous ledger;
- prior certification history was not recomputed from pre-observation events;
- certification-record events were not bound to certification identity.

### Reviewer B — product truth and strategy

Found and repaired:

- forged persisted explanation and claim boundary were accepted;
- instrument and benchmark registries could be substituted or mislabeled independently of Strategy reviews and Portfolio Aim;
- certified state could carry a later-observation projection;
- a later WATCH observation could reference evidence absent from the workspace evidence set.

### Reviewer C — adversarial custody and environment

Found and repaired:

- the lock already contained all reported packages; no dependency edit was justified;
- Windows `core.autocrlf=true` corrupted hash-bound fixture bytes;
- four legacy failures were stale authority assertions.

Remaining blockers discovered:

- historical G4/G5/G6 Replay manifests are non-relocatable because a manifest embeds `E:\Code\Quant`;
- required generated parquet/evidence artifacts are absent from a clean clone;
- historical dashboard/Phase 59–61 authority tests are stale against the current roadmap;
- two candidate-card manifests contain stale artifact hashes;
- historical Feature Store and Rule100 tests remain red.

## Evidence

- `pip check`: PASS.
- Collection: 2664 tests / 201 files.
- Portfolio: 92/92 PASS.
- Context + protocol: 175/175 PASS.
- Legacy product: 263/263 PASS.
- Full LF suite: 2598 passed, 16 skipped, 50 failed.
- GitHub status checks on the base candidate: none exposed.

## Acceptance decision

Do not accept. Publish the repair candidate, then require independent A/B/C on its exact terminal SHA and a separate bounded repository-environment/custody repair. Do not reopen Product or Replay feature work from this branch.
