# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `R0_BANKED; INDEPENDENT_AUDIT_PENDING`
Last updated: 2026-07-29
Authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)

## Queue law

1. `R0 — ROADMAP-CUSTODY-REPAIR` is an internal repository repair, not a product slice.
2. The seven-slice product sequence is fixed at boundary and gate level.
3. Only `GV-MICRO-PORTFOLIO-VERTICAL-0` and `GV-DETERMINISTIC-REPLAY-0` are implementation-authorized, and implementation waits for independent R0 audit PASS.
4. Bounded portfolio work remains blocked until exact deterministic replay passes.
5. Released `gv_fs0_v1` remains immutable; portfolio work uses a new namespace.
6. Work occurs only in a clean isolated worktree descended from `ROADMAP_FREEZE_COMMIT`.
7. The dirty root checkout is not execution or publication authority.

## R0 — `ROADMAP-CUSTODY-REPAIR`

- **Status:** `BANKED_AUDIT_PENDING`
- **Product slice:** no
- **Delivered:** semantic contradiction repair; explicit active-brief selection; Phase 66 bridge retired; stale SAW superseded; three-package topology; minimum seam definition; corrected context and authority chain.
- **Exit gate:** independent audit confirms exact commit, remote presence, clean worktree, passing selector tests/validation, and untouched root.

## Slice 0 — `GV-MICRO-PORTFOLIO-VERTICAL-0`

- **Status:** `AUTHORIZED_AFTER_R0_AUDIT`
- **Objective:** ship one complete prospective multi-security portfolio operator loop.

```text
launch
→ review 3–5 securities, benchmark, and classified cash
→ inspect principal thesis, substitute, competitor, and rejection
→ confirm portfolio aim
→ deterministic paper order and fill
→ certify book
→ persist and reopen
→ admit one later observation
→ explain what changed and why
```

### Minimum scope

- permanent instrument identity and aliases;
- content-addressed evidence references and immutable events;
- one actually exercised corporate action;
- multi-position book, classified cash, NAV reconciliation;
- Living Thesis Lite and Bull/Base/Bear ranges;
- admit/reject/abstain/cash outcomes;
- deterministic capital competition, aim, transition, order, and fill;
- immutable original decision snapshot;
- one operator workspace.

### Work packages

| Package | Owns | Hard output |
|---|---|---|
| A — Truth core | identity, evidence, events, book, cash, NAV, replay skeleton | reconciled replayable event log |
| B — Decision vertical | thesis, scenarios, admission, capital competition, aim, transition, order/fill | certified aim and fill events |
| C — Product closure | launch/review/confirm/persist/reopen, read models, later observation, docs | operator-complete vertical |

### Minimum frozen seams

`InstrumentId`, `EventId`, `EvidenceReference`, `PortfolioBookEvent`, `DecisionSnapshotId`, `PortfolioAimId`, `OrderId`, `FillId`, `CertificationId`.

Detailed fields freeze only when exercised by the acceptance fixture.

## Slice 1 — `GV-DETERMINISTIC-REPLAY-0`

- **Status:** `AUTHORIZED; CERTIFICATION_REQUIRES_SLICE_0_EVENTS`
- **Objective:** exactly reconstruct the operated portfolio rather than merely reproduce plausible output.
- **Acceptance:** exact cash, quantities, costs, NAV, and thesis state; byte-stable prior certification; idempotence; correction lineage; partial-fill residual state; valuation-pending without fabricated prices; one split or equivalent value transfer; zero unexplained residual at declared precision.

## Evidence-gated later slices

| Order | Slice | Gate |
|---:|---|---|
| 2 | `GV-BOUNDED-PORTFOLIO-1` | exact replay PASS |
| 3 | `GV-PORTFOLIO-SCALE-1` | repeated bounded operation |
| 4 | `GV-UNIVERSE-SCALE-1` | portfolio-scale custody/replay stability |
| 5 | `GV-CHALLENGER-PROMOTION-1` | prospective challenger evidence and independent replication |
| 6 | `GV-LIMITED-LIVE-1` | repeated paper operation, exact replay, stable custody, explicit owner authorization |

## Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      0/1
Prospective later observation      0/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## Forbidden critical-path scope

providers · WRDS acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax/FX · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim

## Immediate next action

```text
independent audit ROADMAP_FREEZE_COMMIT
→ create clean isolated worktree from that exact commit
→ ship GV-MICRO-PORTFOLIO-VERTICAL-0
→ certify GV-DETERMINISTIC-REPLAY-0
```
