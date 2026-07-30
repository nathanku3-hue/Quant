# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `PORTFOLIO_SCALE_1_ACCEPTED; GV-UNIVERSE-SCALE-1 OPEN`
Last updated: 2026-07-30
Authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/phase4-gv-universe-scale-1-brief.md`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)

## Immutable pins

| Pin | Exact SHA | Tag |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | `gv-replay-0-base` |
| Replay 0 code terminal | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` |
| Bounded Portfolio 1 terminal | `abaa814ce99ea78afadc33dd40506f4e13a742ef` | `gv-bounded-portfolio-1-terminal` |
| **Portfolio Scale 1 terminal** | **`c37abf00293937b9b99eb6e560f6b5b77a92ea1f`** | **`gv-portfolio-scale-1-terminal`** |

## Queue law

1. Product sequence is fixed; only the active open slice may take implementation work.
2. **Only `GV-UNIVERSE-SCALE-1` is open** after Portfolio Scale 1 acceptance.
3. Scale code base remains exact `c37abf0`; Bounded pin remains exact `abaa814`; Replay pin remains exact `0e4b93f` (do not squash those identities).
4. Slice 0 at `85e6601` remains immutable.
5. Work occurs only in a clean isolated worktree descended from the Universe Scale promotion tip with Scale pin `c37abf0`.
6. The dirty root checkout is not execution or publication authority.
7. Challenger Promotion and Live stay blocked until universe-scale PASS.

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
- **Module:** `gv_portfolio_v0/bounded.py` + `tests/gv_portfolio_v0/test_bounded.py`

## Slice 3 — `GV-PORTFOLIO-SCALE-1`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `c37abf00293937b9b99eb6e560f6b5b77a92ea1f`
- **Tag:** `gv-portfolio-scale-1-terminal`
- **Proof:** concurrent multi-session scale (N×4 > Bounded V1); path-free economic determinism; Replay/Bounded frozen byte-identical; true candidate-only = 0; A/B/C PASS; PR #13 merged as exact SHA (FF, no squash).
- **Module:** `gv_portfolio_v0/scale.py` + `tests/gv_portfolio_v0/test_scale.py`

## Slice 4 — `GV-UNIVERSE-SCALE-1`

- **Status:** `IMPLEMENTATION_IN_PROGRESS`
- **Promotion tip / branch base:** exact `133b6326b74af35388730662206a6495125d4474`
- **Scale code pin (immutable, not branch point):** exact `c37abf00293937b9b99eb6e560f6b5b77a92ea1f`
- **Bounded code pin:** exact `abaa814ce99ea78afadc33dd40506f4e13a742ef`
- **Replay code pin:** exact `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`
- **Implementation branch:** `codex/gv-universe-scale-1`
- **Module:** `gv_portfolio_v0/universe.py` + `tests/gv_portfolio_v0/test_universe.py`
- **Brief:** `docs/phase_brief/phase4-gv-universe-scale-1-brief.md`
- **Objective:** scale paper portfolio operation across a larger declared security universe while keeping exact replay, residual zero, and session custody green.
- **Gate law:** every cycle re-verify Scale multi-session + Bounded multi-cycle + exact Replay; stop on any event/cert/reopen/book/ledger/hash drift.

## Evidence-gated later slices

| Order | Slice | Gate |
|---:|---|---|
| 5 | `GV-CHALLENGER-PROMOTION-1` | universe-scale PASS + prospective challenger evidence |
| 6 | `GV-LIMITED-LIVE-1` | explicit owner authorization |

## Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         1/1
Portfolio scale                    1/1
Universe scale                     0/1
```

## Forbidden critical-path scope

providers · WRDS · broad historical loaders · optimizer · copula/MES · adaptive intraday · tactical capital · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · squash of audited terminals · Slice 0 rewrite

## Immediate next action

```text
clean isolated worktree from Universe Scale promotion tip
→ pin Scale terminal c37abf0 + Bounded abaa814 + Replay 0e4b93f
→ implement only GV-UNIVERSE-SCALE-1
→ keep Scale multi-session + Bounded multi-cycle + exact Replay green
→ do not open Challenger/Live until universe-scale PASS
```
