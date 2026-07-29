# GodView Top-Level Roadmap

Status: `R0_BANKED; INDEPENDENT_AUDIT_PENDING`
Date: 2026-07-29
Canonical detail: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`), release-proof tip `93e7a55`
Shipped score: `39/100`; observed comparisons: `0`; no alpha claim

## Binding state

```text
R0 = ROADMAP-CUSTODY-REPAIR / INTERNAL / BANKED / AUDIT_PENDING
PRODUCT_SEQUENCE = SLICES_0_TO_6
EXECUTION_AUTHORIZED_AFTER_AUDIT = SLICES_0_TO_1
ACTIVE_SLICE = GV-MICRO-PORTFOLIO-VERTICAL-0
NEXT_GATE = GV-DETERMINISTIC-REPLAY-0
ROOT_CHECKOUT = UNSAFE / DO_NOT_USE
```

## Sequence

| Order | Scope | Status | Outcome |
|---:|---|---|---|
| R0 | `ROADMAP-CUSTODY-REPAIR` | banked; audit pending | one checkoutable authority; explicit active brief; stale instructions superseded |
| 0 | `GV-MICRO-PORTFOLIO-VERTICAL-0` | authorized after audit | complete 3–5-security operator loop plus later observation |
| 1 | `GV-DETERMINISTIC-REPLAY-0` | authorized | exact reconstruction from real Slice 0 events |
| 2 | `GV-BOUNDED-PORTFOLIO-1` | blocked by replay | repeated 8–15-security operation |
| 3 | `GV-PORTFOLIO-SCALE-1` | evidence-conditioned | 25–50 operated securities |
| 4 | `GV-UNIVERSE-SCALE-1` | evidence-conditioned | 100–300+ PIT candidate custody |
| 5 | `GV-CHALLENGER-PROMOTION-1` | shadow-first | evidence-based challenger promotion |
| 6 | `GV-LIMITED-LIVE-1` | separate owner gate | small reversible pilot only |

## First product acceptance

```text
launch
→ review 3–5 securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, and rejection
→ confirm portfolio aim
→ deterministic paper order and fill
→ certify
→ persist and reopen
→ admit one later observation
→ explain changed or preserved state
```

## Work topology

- **Package A — Truth core:** identity, evidence, events, book, cash, NAV, replay skeleton.
- **Package B — Decision vertical:** thesis, scenarios, admission, capital competition, aim, transition, order/fill.
- **Package C — Product closure:** operator flow, read models, acceptance fixture, later observation, docs/ops.

Minimum seams freeze first: `InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, `CertificationId`.

Detailed fields freeze only when exercised by the fixture.

## Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## Immediate next action

```text
independent audit ROADMAP_FREEZE_COMMIT
→ branch only from that exact commit
→ ship GV-MICRO-PORTFOLIO-VERTICAL-0
→ certify GV-DETERMINISTIC-REPLAY-0
```

Do not mutate released FS0, use raw `93e7a55` as the implementation base, clean the dirty root checkout, or open provider/optimizer/live-capital scope.
