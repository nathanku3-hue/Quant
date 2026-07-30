# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `REPLAY_0_BASE_PROMOTED; GV-DETERMINISTIC-REPLAY-0 OPEN`
Last updated: 2026-07-30
Authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/phase1-gv-deterministic-replay-0-brief.md`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)

## Immutable pins

| Pin | Exact SHA |
|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` |

## Queue law

1. `R0 — ROADMAP-CUSTODY-REPAIR` was internal repository repair, not a product slice; closed under Slice 0 + custody supersede.
2. The seven-slice product sequence is fixed at boundary and gate level.
3. **Only `GV-DETERMINISTIC-REPLAY-0` is open for implementation** on base `03a5c92`.
4. Bounded portfolio work remains blocked until exact deterministic replay passes.
5. Released `gv_fs0_v1` remains immutable; portfolio work uses `gv_portfolio_v0`.
6. Work occurs only in a clean isolated worktree descended from Replay 0 base `03a5c92`.
7. The dirty root checkout is not execution or publication authority.
8. Slice 0 at `85e6601` is immutable; do not rewrite it to absorb custody fixes.

## R0 — `ROADMAP-CUSTODY-REPAIR`

- **Status:** `CLOSED_VIA_SLICE0_AND_CUSTODY_SUPERSEDE`
- **Product slice:** no

## Slice 0 — `GV-MICRO-PORTFOLIO-VERTICAL-0`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `85e6601742710f03e6cced7377b4be426cd4892f`
- **Audit:** matched clean-clone comparison — candidate-only failures = 0 vs integration base; independent acceptance banked 2026-07-30.

## Custody supersede — relocatable manifests (not a product slice)

- **Status:** `PROMOTED_AS_REPLAY_0_BASE`
- **SHA:** `03a5c922d250d615380bbd0d60e8fd636e4ec1c6`
- **Parent chain:** `85e6601` → `bd07f61` → `03a5c92`
- **Delivered:** G4 relative path + `repo_root` resolve; MSFT hash hygiene; V2-B0 MU historical non-binding restored; explicit G8 MU same-path hash-match retirement; gate doc.
- **Proof:** focused 149/149; full suite candidate-only = 0 vs `85e6601`; independent A/B/C PASS; remote-equal.

## Slice 1 — `GV-DETERMINISTIC-REPLAY-0`

- **Status:** `OPEN; IMPLEMENTATION_AUTHORIZED`
- **Base:** exact `03a5c922d250d615380bbd0d60e8fd636e4ec1c6`
- **Objective:** exactly reconstruct the operated Slice 0 portfolio rather than merely reproduce plausible output.
- **Acceptance:** exact cash, quantities, costs, NAV, and thesis state; byte-stable prior certification; idempotence; correction lineage; partial-fill residual state; valuation-pending without fabricated prices; one split or equivalent value transfer; zero unexplained residual at declared precision.
- **Brief:** `docs/phase_brief/phase1-gv-deterministic-replay-0-brief.md`

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
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         0/1
Bounded repeated portfolio         0/1
```

## Forbidden critical-path scope

providers · WRDS acquisition · broad historical loaders · optimizer · copula/MES production · automated graph propagation · adaptive intraday execution · tactical capital · broad tax/FX · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · Slice 0 rewrite · MU hash “repair” that breaks V2-B0 non-binding

## Immediate next action

```text
clean isolated worktree from exact 03a5c92
→ implement only GV-DETERMINISTIC-REPLAY-0
→ certify exact reconstruction from Slice 0 events
→ do not open GV-BOUNDED-PORTFOLIO-1 until replay PASS
```
