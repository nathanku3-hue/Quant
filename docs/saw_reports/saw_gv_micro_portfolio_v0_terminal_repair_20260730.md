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

## Independent review of superseded terminal SHA `4ee0b4a`

- Reviewer A: **BLOCK**. Found that `LATER_OBSERVATION_ADMITTED` validated only its payload; forged `source_identity` and `instrument_id` values were accepted after valid event rehashing and recertification.
- Reviewer B: **PASS**. No unresolved Critical/High runtime or operational finding.
- Reviewer C: **PASS**. No unresolved Critical/High data-integrity or checkout-custody finding.
- Parent reproduction: both forged source and forged instrument were accepted.
- Repair: bind event source to the validated observation evidence ID and event instrument to the principal review instrument; add two recertified adversarial regressions.
- Result: portfolio **94/94 PASS**.

Because the repair changes code and tests, the matched full-suite comparison and independent Reviewer A/B/C must rerun against the superseding terminal SHA.

## Evidence

- `pip check`: PASS.
- Collection: 2664 tests / 201 files.
- Portfolio: 94/94 PASS after independent Reviewer A repair.
- Context + protocol: 175/175 PASS.
- Legacy product: 263/263 PASS.
- Matched superseded-SHA comparison: base 54 failures; candidate 50; intersection 50; candidate-only 0; four stale authority failures removed.
- GitHub status checks on the base candidate: none exposed.

## Acceptance decision

Do not accept yet. Publish the superseding repair candidate, rerun the matched base/candidate failure-node comparison and independent A/B/C on its exact SHA, and keep repository-environment/custody repair separate. Do not reopen Product or Replay feature work from this branch.
