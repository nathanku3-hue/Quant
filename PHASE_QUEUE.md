# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `BOUNDED_PORTFOLIO_1_ACCEPTED; GV-PORTFOLIO-SCALE-1 OPEN`
Last updated: 2026-07-30
Authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/phase3-gv-portfolio-scale-1-brief.md`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)

## Immutable pins

| Pin | Exact SHA | Tag |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | `gv-replay-0-base` |
| Replay 0 code terminal | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` |
| **Bounded Portfolio 1 terminal** | **`abaa814ce99ea78afadc33dd40506f4e13a742ef`** | **`gv-bounded-portfolio-1-terminal`** |

## Queue law

1. Product sequence is fixed; only the active open slice may take implementation work.
2. **Only `GV-PORTFOLIO-SCALE-1` is open** after Bounded Portfolio 1 acceptance.
3. Bounded code base remains exact `abaa814`; Replay pin remains exact `0e4b93f` (do not squash those identities).
4. Slice 0 at `85e6601` remains immutable.
5. Work occurs only in a clean isolated worktree descended from the Portfolio Scale promotion tip with Bounded pin `abaa814`.
6. The dirty root checkout is not execution or publication authority.
7. Universe Scale and later slices stay blocked until portfolio-scale PASS.

## R0 — `ROADMAP-CUSTODY-REPAIR`

- **Status:** `CLOSED`

## Slice 0 — `GV-MICRO-PORTFOLIO-VERTICAL-0`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `85e6601742710f03e6cced7377b4be426cd4892f`

## Slice 1 — `GV-DETERMINISTIC-REPLAY-0`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`
- **Tag:** `gv-replay-0-terminal`
- **Carried Medium debt:** R0-D1 multi-hop reopen; R0-D2 residual vs `book_hash`

## Slice 2 — `GV-BOUNDED-PORTFOLIO-1`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `abaa814ce99ea78afadc33dd40506f4e13a742ef`
- **Tag:** `gv-bounded-portfolio-1-terminal`
- **Proof:** persisted multi-cycle session ledger; explicit AIM_UNCHANGED disposition; Replay frozen; true candidate-only = 0; A/B/C PASS; PR #12 merged as exact SHA (FF, no squash). Intermediate `4f3bc6b` independent-fixture shape rejected/superseded.
- **Module:** `gv_portfolio_v0/bounded.py` + `tests/gv_portfolio_v0/test_bounded.py`

## Slice 3 — `GV-PORTFOLIO-SCALE-1`

- **Status:** `IMPLEMENTATION_IN_PROGRESS`
- **Promotion tip / branch base:** exact `eedf853566d009dc6a5af74397c316013b87a853`
- **Bounded code pin (immutable, not branch point):** exact `abaa814ce99ea78afadc33dd40506f4e13a742ef`
- **Replay code pin:** exact `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`
- **Implementation branch:** `codex/gv-portfolio-scale-1`
- **Module:** `gv_portfolio_v0/scale.py` + `tests/gv_portfolio_v0/test_scale.py`
- **Brief:** `docs/phase_brief/phase3-gv-portfolio-scale-1-brief.md`
- **Objective:** scale repeated paper portfolio operation with custody/replay stability.
- **Gate law:** every cycle re-verify Bounded multi-cycle + exact Replay; stop on any event/cert/reopen/book/ledger/hash drift.

## Evidence-gated later slices

| Order | Slice | Gate |
|---:|---|---|
| 4 | `GV-UNIVERSE-SCALE-1` | portfolio-scale PASS |
| 5 | `GV-CHALLENGER-PROMOTION-1` | prospective challenger evidence |
| 6 | `GV-LIMITED-LIVE-1` | explicit owner authorization |

## Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         1/1
Portfolio scale                    0/1
```

## Forbidden critical-path scope

providers · WRDS · broad historical loaders · optimizer · copula/MES · adaptive intraday · tactical capital · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · squash of audited terminals · Slice 0 rewrite

## Immediate next action

```text
branch codex/gv-portfolio-scale-1 from exact eedf853
→ pin Bounded abaa814 + Replay 0e4b93f (immutable)
→ pytest tests/gv_portfolio_v0 --ignore=test_bounded.py --ignore=test_scale.py  # Replay freeze
→ pytest tests/gv_portfolio_v0/test_bounded.py
→ pytest tests/gv_portfolio_v0/test_scale.py
→ stop on any Replay/Bounded drift
→ do not open Universe Scale until portfolio-scale PASS + A/B/C
```
