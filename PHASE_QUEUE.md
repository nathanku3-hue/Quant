# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `REPLAN_ACTIVE; GV-OPERATED-PORTFOLIO-10-TRANSITION-1R ONLY; LIVE CLOSED`
Last updated: 2026-07-30
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Frozen roadmap: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/gv-operated-portfolio-10-transition-1r-brief.md`

## Queue law

1. One active product phase only: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`.
2. Do not resume automatic Bounded → Scale → Universe → Challenger → Live label progression.
3. Immutable terminals and tags remain unchanged; classifications are corrected below.
4. Distinct-security quantities may not be replaced by sessions, cells, runs, or slots.
5. Any weakened quantity, user behavior, or outcome requires an explicit owner scope decision before implementation.
6. `GV-LIMITED-LIVE-1` remains closed and unauthorized.
7. The dirty operator root is not execution, test, commit, or publication authority.

## Immutable custody and truthful classification

| Artifact | Terminal SHA | Tag | Classification | Original gate |
|---|---|---|---|---|
| Slice 0 | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` | Accepted product slice | Accepted |
| Replay 0 | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` | Accepted integrity slice | Accepted |
| Bounded Portfolio 1 | `abaa814ce99ea78afadc33dd40506f4e13a742ef` | `gv-bounded-portfolio-1-terminal` | Persisted multi-cycle substrate | Incomplete |
| Portfolio Scale 1 | `c37abf00293937b9b99eb6e560f6b5b77a92ea1f` | `gv-portfolio-scale-1-terminal` | Deterministic multi-session harness | Incomplete |
| Universe Scale 1 | `dca67e36edc02dddf8c7ba446ac34f22562ee165` | `gv-universe-scale-1-terminal` | Deterministic multi-cell harness | Incomplete |
| Challenger Promotion 1 | `3e4dc957f475945169ddf33ed359254bd98dc64d` | `gv-challenger-promotion-1-terminal` | Shadow/certified-custody separation primitive | Incomplete |

## Original semantic gates still controlling

- Bounded: 8–15 distinct securities, at least two economic clusters, repeated operation.
- Portfolio Scale: one operated 25–50-security portfolio with deterministic books, replay, and bounded operator workload.
- Universe Scale: custody of 100–300+ distinct securities with survivorship-safe membership, permanent identity, corporate actions, corrections, and reproducible snapshots.
- Challenger: baseline → shadow → prospective challenger → independent replication → bounded authority.

## Active product repair — `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R`

- **Status:** `IMPLEMENTATION_CANDIDATE; NOT TERMINAL`
- **Base:** exact Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`
- **Product result:** one ten-instrument, two-cluster portfolio that funds multiple positions, records a justified no-change cycle, performs one real reduce-and-fund transition, persists, reopens, replays exactly, and explains changed why.
- **Product entrypoint:** `operated_portfolio_app.py`
- **Launcher:** `launch_operated_portfolio.py`
- **Domain:** `gv_portfolio_v0/operated.py`
- **Persistence:** `gv_portfolio_v0/operated_storage.py`
- **Shared repaired seams:** `gv_portfolio_v0/execution.py`, `gv_portfolio_v0/book.py`
- **Focused tests:** `tests/gv_portfolio_v0/test_operated.py`, `tests/gv_portfolio_v0/test_operated_app.py`

### Required terminal gates

```text
10 distinct permanent identities
+ >=2 economic clusters
+ unique evidence and thesis state
+ one portfolio book
+ >=3 funded positions and classified residual cash
+ competition across all 10 instruments
+ explicit no-change observation
+ SELL/REDUCE one position and BUY/FUND another
+ exact replay and idempotence
+ correction lineage and zero residual
+ atomic persist/restart/reopen
+ changed-why UI
+ fresh-checkout black-box AppTest
+ full terminal regression
+ independent A/B/C on exact SHA
```

## Limited Live — `GV-LIMITED-LIVE-1`

- **Status:** `CLOSED; NOT_AUTHORIZED`
- **Reason:** original Bounded, Portfolio Scale, Universe Scale, and Challenger Promotion outcomes remain incomplete.
- **Opening rule:** separate explicit owner authorization only after repeated prospective paper operation and all frozen prerequisites.

## Score

Pre-candidate endgame progress assessment: `52/100`.

The current uncommitted candidate does not change accepted score. Re-score only after one immutable candidate passes focused tests, fresh-checkout AppTest, full terminal regression, and independent A/B/C.

## Forbidden critical-path scope

providers · WRDS · broad loaders · optimizer-first allocation · copied fixture slots · scale/universe/challenger compatibility adapters · shorting · leverage · derivatives · broker · live capital · score uplift · alpha claim · immutable tag rewriting · dirty-root development

## Immediate next action

```text
locate or provision the pinned Python 3.12 + pytest environment
→ run focused operated/accounting/execution/replay tests
→ repair current slice only
→ freeze one candidate SHA
→ run fresh-checkout AppTest + full regression/failset once
→ independent A/B/C against exact SHA
→ reconcile and fast-forward origin/main only after terminal PASS
→ Limited Live remains CLOSED
```
