# GV-MICRO-PORTFOLIO-VERTICAL-0 Brief

Date: 2026-07-29
Mode: `EXECUTION_PACKET`
Status: `ACCEPTED_IMMUTABLE`
Authority: corrected GodView portfolio roadmap; clean-clone acceptance 2026-07-30
Terminal SHA: `85e6601742710f03e6cced7377b4be426cd4892f`

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 phase: `GV-MICRO-PORTFOLIO-VERTICAL-0` — **accepted immutable** at `85e6601`.
- L2 active phase: `GV-DETERMINISTIC-REPLAY-0` (see `docs/context/ACTIVE_BRIEF`).
- L2 deferred: Bounded Portfolio, Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.

## Recommended next action

Do not reopen Slice 0 product feature work. Execute only `GV-DETERMINISTIC-REPLAY-0` from Replay 0 base `03a5c922d250d615380bbd0d60e8fd636e4ec1c6`.

## Product target

```text
launch
→ review 3–5 securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, and rejection
→ confirm portfolio aim
→ generate deterministic paper order and fill
→ certify book
→ persist
→ reopen
→ admit one later observation
→ explain what changed and why
```

## Minimum cross-layer seams

Freeze before parallel implementation:

- `InstrumentId`;
- `EventId`;
- `EvidenceReference`;
- `PortfolioBookEvent`;
- `DecisionSnapshotId`;
- `PortfolioAimId`;
- `OrderId`;
- `FillId`;
- `CertificationId`.

Freeze field-level detail only when the acceptance fixture exercises it.

## Three mergeable work packages

### Package A — Truth core

Owns permanent IDs, immutable events, content-addressed evidence, book reduction, classified cash, NAV reconciliation, and replay API skeleton.

### Package B — Decision vertical

Owns Living Thesis Lite, Bull/Base/Bear ranges, admit/reject/abstain/cash outcomes, deterministic capital competition, portfolio aim, transition, paper order, and fill.

### Package C — Product closure

Owns launch/review/confirm/persist/reopen, read models, acceptance-fixture orchestration, later-observation explanation, and authority synchronization.

## Acceptance

- one new portfolio namespace; released `gv_fs0_v1` remains unchanged;
- permanent instrument identity and content-addressed evidence references;
- one actually exercised corporate action;
- multi-position book with classified cash and NAV reconciliation;
- Living Thesis Lite and Bull/Base/Bear ranges;
- explicit admit, reject, abstain, and cash outcomes;
- deterministic capital competition, one transition, one paper order, and one fill;
- immutable original decision snapshot;
- one complete operator workspace;
- persist/reopen plus one later prospective observation explaining changed or preserved state;
- no optimizer, provider programme, broad tax/FX/derivatives/shorting framework, alpha claim, or live capital.

## Expected score after acceptance

Canonical shipped score remains `39/100` until acceptance evidence is banked. Nonbinding forecast after this vertical:

- Product capability: `60–65`;
- User flow: `70–75`;
- Portfolio completeness: `65–70`;
- Integrity and replay: `70–75`;
- Prospective evidence: `20–30`;
- Shipping and custody: `85–90`;
- Weighted audit maturity: `62–66`.

Operational gates remain binary:

```text
Roadmap custody banked             1/1
Micro-portfolio candidate built    1/1
Terminal remote custody            1/1
Independent candidate audit        1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## P0/P1 risks

| Risk | Severity | Control |
|---|---|---|
| implementation branches from stale ancestry | P0 | exact `ROADMAP_FREEZE_COMMIT` base only |
| package seams diverge | P1 | freeze minimum IDs/events before parallel work |
| schema catalogue delays user loop | P1 | fields exist only when exercised by the fixture |
| released FS0 mutates into a portfolio system | P1 | new `gv_portfolio_v0` namespace; no adapter on critical path |
| replay is postponed | P1 | build replay skeleton from real vertical events; certify immediately next |

## Forbidden scope

providers · WRDS acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax · multi-currency · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim

## Stop rules

1. Stop if a minimum seam cannot represent the full operator loop without contradiction.
2. Stop if the implementation worktree is not descended from the banked roadmap authority.
3. Stop if a proposed gate does not protect PIT validity, accounting integrity, mandatory actions, mandate safety, or deterministic replay.

## New Context Packet

## What Was Done

- Banked S2 Accounting, S3 Strategy, and S4 Execution as isolated local commits from exact base `b3d5092`.
- Integrated the three streams through canonical Strategy records, immutable Execution lineage, and the reconciled PortfolioBook.
- Removed duplicate reducer, decision-validator, and order/fill authority from `vertical.py`.
- Preserved the complete review → confirm → transition → order/fill → certify → persist/reopen → later WATCH operator loop.
- Bumped persisted bytes to `gv_portfolio_v0_workspace_v2` instead of silently reusing the incompatible v1 label.
- Verified portfolio 82/82 and frozen protocol 150/150; classified four unrelated legacy product-document failures.

## What Is Locked

- `ROADMAP_SEQUENCE = GV-MICRO-PORTFOLIO-VERTICAL-0 → GV-DETERMINISTIC-REPLAY-0 → GV-BOUNDED-PORTFOLIO-1 → GV-PORTFOLIO-SCALE-1 → GV-UNIVERSE-SCALE-1 → GV-CHALLENGER-PROMOTION-1 → GV-LIMITED-LIVE-1`.
- `EXECUTION_AUTHORIZED = GV-MICRO-PORTFOLIO-VERTICAL-0, GV-DETERMINISTIC-REPLAY-0`.
- `SHIPPED_PRODUCT_SCORE = 39/100`; observed comparisons remain `0`; no alpha or live-capital claim.
- The root checkout remains untouched and is not execution authority.
- Bounded portfolio work remains blocked until exact deterministic replay passes.

## What Is Next

- Repair the repository dependency declaration/environment before claiming a full pinned-suite PASS.
- Run independent Reviewer A/B/C audit against the exact remote terminal SHA.
- Keep Product and Replay read-only until that audit passes.

## First Command

```text
git status --short --branch && git rev-parse HEAD && cat docs/context/ACTIVE_BRIEF
```

## Next Phase Roadmap

- `GV-MICRO-PORTFOLIO-VERTICAL-0`;
- `GV-DETERMINISTIC-REPLAY-0`;
- evidence-gated later slices only.

## Terminal repair update — 2026-07-30

The remote-equal integration candidate at `9ebc973a8cc3cfbd4899ed724733cc22c606fbbf` required a bounded terminal repair before independent acceptance.

Closed: certification lineage, persisted operator truth, registry cross-binding, dangling observation evidence, later-observation event source/instrument binding, contiguous event order, four stale legacy authority assertions, and cross-platform fixture line-ending custody.

Evidence: portfolio 94/94 after independent Reviewer A repair; context + protocol 175/175; legacy product 263/263. The prior matched full-suite comparison showed base 54 failures, candidate 50, intersection 50, and candidate-only 0; this comparison and independent A/B/C must rerun against the superseding terminal SHA.

The phase remains `NOT_ACCEPTED`. Product and Replay implementation stay closed. The next gate is matched failure-node comparison plus independent A/B/C against the superseding terminal SHA; repository-environment/custody repair remains separate.
