# PHASE_QUEUE.md — GodView Portfolio Product Queue

Status: `GV-OPERATED-PORTFOLIO-25-1 ACTIVE; NOT_FROZEN; LIVE CLOSED`
Last updated: 2026-08-01
Canonical authority: `docs/context/gv_endgame_authority_current.md`
Frozen roadmap: `docs/architecture/godview_v2_frozen_build_learn_roadmap.md`
Active brief: `docs/context/ACTIVE_BRIEF` → `docs/phase_brief/gv-operated-portfolio-25-1-brief.md`

## Queue law

1. One active product phase only: `GV-OPERATED-PORTFOLIO-25-1`.
2. The accepted ten-security terminal remains immutable custody; current shared source may evolve under regression protection.
3. The active phase must use one shared engine, persistence implementation, application, and view for retained 10- and new 25-security scenarios.
4. Genericization cannot be accepted, reviewed as progress, banked, or frozen independently from the executable 25-security checkpoint.
5. Distinct-security quantities may not be replaced by sessions, cells, runs, slots, portfolio copies, or repeated executions.
6. Streams are logical ownership boundaries, not a requirement for six workers.
7. `GV-LIMITED-LIVE-1` remains closed and unauthorized.
8. The dirty operator root is not execution, test, commit, or publication authority.

## Immutable custody and truthful classification

| Artifact | Terminal SHA | Tag | Classification | Original gate |
|---|---|---|---|---|
| Slice 0 | `85e6601742710f03e6cced7377b4be426cd4892f` | `gv-slice-0-terminal` | Accepted product foundation | Accepted |
| Replay 0 | `0e4b93fb370f67956502edc02e9c6f56ceb2eba3` | `gv-replay-0-terminal` | Accepted integrity foundation | Accepted |
| Bounded Portfolio 1 | `abaa814ce99ea78afadc33dd40506f4e13a742ef` | `gv-bounded-portfolio-1-terminal` | Persisted multi-cycle substrate | Historical lower-level gate |
| Portfolio Scale 1 | `c37abf00293937b9b99eb6e560f6b5b77a92ea1f` | `gv-portfolio-scale-1-terminal` | Deterministic multi-session harness | One real 25–50-security portfolio incomplete |
| Universe Scale 1 | `dca67e36edc02dddf8c7ba446ac34f22562ee165` | `gv-universe-scale-1-terminal` | Deterministic multi-cell harness | Incomplete |
| Challenger Promotion 1 | `3e4dc957f475945169ddf33ed359254bd98dc64d` | `gv-challenger-promotion-1-terminal` | Shadow/certified-custody primitive | Incomplete |
| Operated Portfolio 10 | `0d15e9c` executable / `2349e1b` closure | `gv-operated-portfolio-10-transition-1r-terminal` | Accepted terminal product | Accepted |

## Active product phase — `GV-OPERATED-PORTFOLIO-25-1`

- **Status:** `AUTHORIZED; IMPLEMENTATION_ACTIVE; NOT_FROZEN; NOT_TERMINAL`
- **Base:** terminal `main` `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e`
- **Product result:** one real 25-security portfolio with deterministic books, exact replay, bounded four-action workload, persistence, correction, restart, and summary-first UX.
- **Shared engine:** `gv_portfolio_v0/operated.py`
- **Scenarios:** `gv_portfolio_v0/operated_scenarios.py`
- **Shared persistence:** `gv_portfolio_v0/operated_storage.py`
- **Shared product:** `operated_portfolio_app.py`, `views/gv_operated_portfolio_workspace.py`
- **Thin launcher:** `launch_operated_portfolio_25.py`
- **Tests:** retained `test_operated.py` and `test_operated_app.py`; active `test_operated_25.py`.

### Non-weakenable acceptance

```text
one portfolio
+ exactly 25 permanent identities
+ >=2 meaningful clusters
+ owned evidence and thesis state
+ one competition covering every identity exactly once
+ multiple funded positions and classified residual cash
+ explicit no-change
+ >=1 SELL/REDUCE and >=1 BUY/FUND
+ deterministic accounting and residual 0
+ exact replay, certification and correction
+ atomic persist/restart/reopen
+ summary-first and exceptions-first UI
+ <=4 required actions; zero per-security confirmations
+ retained ten-security flow green through the same path
```

Five clusters, eight funded positions, and transition-leg count are fixture parameters, not product authority.

## Current checkpoint

Local focused and package-level tests are green. No candidate SHA, hosted exact-head evidence, controlled failset comparison, or independent terminal A/B/C exists yet. Accepted score remains `62/100`.

## Pre-freeze gate

```text
changed-path test ownership
+ CI path triggers
+ exact-head checkout
+ dependency coverage and pip check
+ base/candidate failset method
+ evidence destination outside checkout
+ broad local validation
→ freeze exactly one candidate
```

## Terminal gate

```text
exact-head Windows/Linux CI
+ controlled full base/candidate comparison with zero candidate-only failures
+ independent Reviewer A/B/C
+ documentation-only closure preserving tested executable tree
```

## Forbidden critical-path scope

providers · external ingestion · optimizer expansion · broker · Universe · Challenger · Limited Live · live capital · shorting · leverage · derivatives · alpha/score uplift · historical harness compatibility · general frameworks · repository-wide dependency repair · unrelated cleanup

## Immediate next action

Complete current-context regeneration and pre-freeze receipts, run broad local validation, then freeze one candidate only if all stop rules remain clear.
