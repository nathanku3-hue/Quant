# GV-MICRO-PORTFOLIO-VERTICAL-0 Brief

Date: 2026-07-29
Mode: `EXECUTION_PACKET`
Status: `AUTHORIZED_AFTER_ROADMAP_FREEZE_BANK; NOT_STARTED`
Authority: corrected GodView portfolio roadmap and R0 custody-repair acceptance

## Hierarchy

- L1: GodView point-in-time certified portfolio operating system.
- L2 active streams after audit: Truth core, Decision vertical, Product closure, Replay/Certification.
- L2 deferred streams: Bounded Portfolio, Portfolio Scale, Universe Scale, Challenger Promotion, Limited Live Capital.
- L3 stage flow: R0 Final Verification → Independent Audit → Slice 0 Execution → Slice 0 Verification → Slice 1 Replay Certification.

## Recommended next action

After independent audit confirms the banked roadmap authority, create one clean isolated implementation worktree from `ROADMAP_FREEZE_COMMIT` and ship the complete micro-portfolio operator loop. Do not open bounded-portfolio scale work before deterministic replay passes.

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
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
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

- Repaired the roadmap candidate so `R0 — ROADMAP-CUSTODY-REPAIR` is an internal custody step rather than a product slice.
- Removed standalone `GV-CANON-RESET-0` from the product sequence.
- Selected this brief explicitly through `docs/context/ACTIVE_BRIEF`; numerically higher historical briefs cannot override it.
- Preserved released Alpha/FS0 unchanged and defined a new portfolio namespace boundary.
- Replaced seven independent branches with three mergeable work packages.

## What Is Locked

- `ROADMAP_SEQUENCE = GV-MICRO-PORTFOLIO-VERTICAL-0 → GV-DETERMINISTIC-REPLAY-0 → GV-BOUNDED-PORTFOLIO-1 → GV-PORTFOLIO-SCALE-1 → GV-UNIVERSE-SCALE-1 → GV-CHALLENGER-PROMOTION-1 → GV-LIMITED-LIVE-1`.
- `EXECUTION_AUTHORIZED = GV-MICRO-PORTFOLIO-VERTICAL-0, GV-DETERMINISTIC-REPLAY-0`.
- `SHIPPED_PRODUCT_SCORE = 39/100`; observed comparisons remain `0`; no alpha or live-capital claim.
- The root checkout remains untouched and is not execution authority.
- Bounded portfolio work remains blocked until exact deterministic replay passes.

## What Is Next

- Wait for independent audit of the banked R0 roadmap repair.
- After audit PASS, create a clean isolated implementation worktree from `ROADMAP_FREEZE_COMMIT`.
- Ship the complete micro-portfolio operator loop through the three work packages.
- Build replay early but certify it only from real vertical events.

## First Command

```text
git status --short --branch && git rev-parse HEAD && cat docs/context/ACTIVE_BRIEF
```

## Next Phase Roadmap

- `GV-MICRO-PORTFOLIO-VERTICAL-0`;
- `GV-DETERMINISTIC-REPLAY-0`;
- evidence-gated later slices only.
