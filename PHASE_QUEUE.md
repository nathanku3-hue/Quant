# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `REPLAY_0_ACCEPTED; GV-BOUNDED-PORTFOLIO-1 OPEN`
Last updated: 2026-07-30
Authority: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/phase2-gv-bounded-portfolio-1-brief.md`
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)

## Immutable pins

| Pin | Exact SHA | Tag |
|---|---|---|
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` |
| Replay 0 custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | `gv-replay-0-base` |
| **Replay 0 code terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | **`gv-replay-0-terminal`** |

## Queue law

1. Product sequence is fixed; only the active open slice may take implementation work.
2. **Only `GV-BOUNDED-PORTFOLIO-1` is open** after Replay 0 acceptance.
3. Replay code base remains exact `0e4b93f` (do not squash/rebase that identity away).
4. Slice 0 at `85e6601` remains immutable.
5. Work occurs only in a clean isolated worktree descended from the Bounded Portfolio promotion tip (docs open) with Replay code pin `0e4b93f`.
6. The dirty root checkout is not execution or publication authority.
7. Portfolio Scale and later slices stay blocked until bounded portfolio PASS.

## R0 — `ROADMAP-CUSTODY-REPAIR`

- **Status:** `CLOSED`

## Slice 0 — `GV-MICRO-PORTFOLIO-VERTICAL-0`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `85e6601742710f03e6cced7377b4be426cd4892f`

## Slice 1 — `GV-DETERMINISTIC-REPLAY-0`

- **Status:** `ACCEPTED_IMMUTABLE`
- **Terminal SHA:** `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`
- **Tag:** `gv-replay-0-terminal`
- **Proof:** focused portfolio/replay green; true candidate-only vs `9bee439` = 0 after serial Alpha0 re-run; independent A/B/C PASS; PR #11 merged as exact SHA (FF, no squash).
- **Carried Medium debt:** multi-hop reopen parent handling (R0-D1); residual excluded from `book_hash` (R0-D2) — field/ledger authoritative.

## Slice 2 — `GV-BOUNDED-PORTFOLIO-1`

- **Status:** `IMPLEMENTATION_IN_PROGRESS`
- **Promotion tip / branch base:** exact `5fc2e4c01aa98ffe6ad9fcce4d1f9299c4aee6e4`
- **Replay code pin (immutable, not branch point):** exact `0e4b93fb370f67956502edc02e9c6f56ceb2eba3`
- **Implementation branch:** `codex/gv-bounded-portfolio-1`
- **Module:** `gv_portfolio_v0/bounded.py` + `tests/gv_portfolio_v0/test_bounded.py`
- **Brief:** `docs/phase_brief/phase2-gv-bounded-portfolio-1-brief.md`
- **Objective:** repeated bounded multi-security paper portfolio operation with exact replay remaining green.
- **Cycle law:** Replay suite excluding `test_bounded.py` stays **105 pass / 1 skip**; stop on Replay drift.

## Evidence-gated later slices

| Order | Slice | Gate |
|---:|---|---|
| 3 | `GV-PORTFOLIO-SCALE-1` | bounded repeated portfolio PASS |
| 4 | `GV-UNIVERSE-SCALE-1` | portfolio-scale custody/replay stability |
| 5 | `GV-CHALLENGER-PROMOTION-1` | prospective challenger evidence |
| 6 | `GV-LIMITED-LIVE-1` | explicit owner authorization |

## Binary gate score

```text
Roadmap custody banked             1/1
Micro-portfolio operator loop      1/1
Independent Slice 0 audit          1/1
Relocatable Replay 0 base          1/1
Exact deterministic replay         1/1
Bounded repeated portfolio         0/1
```

## Forbidden critical-path scope

providers · WRDS · broad historical loaders · optimizer · copula/MES · adaptive intraday execution · tactical capital · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · squash of audited Replay terminal · Slice 0 rewrite

## Immediate next action

```text
branch codex/gv-bounded-portfolio-1 from exact 5fc2e4c
→ pin Replay code base 0e4b93f (immutable)
→ pytest tests/gv_portfolio_v0 --ignore=test_bounded.py  # expect 105 pass / 1 skip
→ pytest tests/gv_portfolio_v0/test_bounded.py
→ stop on any Replay byte/hash/cert drift
→ do not open Portfolio Scale until bounded PASS + A/B/C
```
