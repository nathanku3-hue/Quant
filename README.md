# Terminal Zero / GodView Certified Portfolio OS

Status: `REPLAN_ACTIVE; GV-OPERATED-PORTFOLIO-10-TRANSITION-1R IMPLEMENTATION_CANDIDATE; LIVE CLOSED`
Date: 2026-07-30
Authority base: Challenger terminal `3e4dc95` (tag `gv-challenger-promotion-1-terminal`)
Slice 0: accepted product slice `85e6601`
Replay 0: accepted integrity slice `0e4b93f`
Bounded `abaa814`: persisted multi-cycle substrate; original breadth incomplete
Portfolio Scale `c37abf0`: deterministic multi-session harness; original 25–50-security objective incomplete
Universe Scale `dca67e3`: deterministic multi-cell harness; original 100–300+ custody objective incomplete
Challenger `3e4dc95`: shadow-custody separation primitive; original promotion objective incomplete
Endgame progress assessment before current candidate: `52/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

GodView is a local-first, point-in-time certified portfolio operating system. Its product unit is a complete portfolio decision and operating loop, not an isolated stock case and not an optimizer-first research platform.

```text
one declared PIT opportunity set
→ complete portfolio including classified cash and abstentions
→ prospective operation
→ deterministic accounting and replay
→ lifecycle-based review
```

## Current authority

- [Canonical endgame authority](docs/context/gv_endgame_authority_current.md) — terminal classifications, non-weakenable acceptance, active result, score, and next gate
- [Frozen Build × Learn roadmap](docs/architecture/godview_v2_frozen_build_learn_roadmap.md) — controlling original quantities and outcomes
- [PRD](PRD.md) — current product requirements
- [Phase queue](PHASE_QUEUE.md) — one active product slice
- [Active brief](docs/context/ACTIVE_BRIEF) — fail-closed selector for the current slice
- [Planner packet](docs/context/planner_packet_current.md) — compact execution truth

If another document conflicts, `docs/context/gv_endgame_authority_current.md`, the frozen roadmap, and `docs/context/ACTIVE_BRIEF` control in that order. A lower-level brief cannot weaken the roadmap without an explicit owner scope decision.

## Released substrate

Alpha-0 proves one narrow broker-free workflow:

```text
launch
→ review sealed multi-source case
→ confirm paper NO_POSITION
→ persist certified result
→ reopen certified state
```

The deterministic package passed hosted Windows/Linux builds, extracted-package smoke, exact archive parity, an independent Windows rebuild, and a browser-operated restart pilot. It remains banked substrate.

Alpha-0 does **not** prove:

- portfolio operation;
- decision improvement;
- alpha;
- calibrated probabilities;
- live-capital readiness.

## Delivery sequence

`R0 — ROADMAP-CUSTODY-REPAIR` is an internal repository repair, not a product slice.

| Slice | Name | Truthful current status |
|---|---|---|
| 0 | `GV-MICRO-PORTFOLIO-VERTICAL-0` | **accepted product slice** `85e6601` |
| 1 | `GV-DETERMINISTIC-REPLAY-0` | **accepted integrity slice** `0e4b93f` |
| 2 | `GV-BOUNDED-PORTFOLIO-1` | **persisted substrate; original gate incomplete** `abaa814` |
| 3 | `GV-PORTFOLIO-SCALE-1` | **multi-session harness; original gate incomplete** `c37abf0` |
| 4 | `GV-UNIVERSE-SCALE-1` | **multi-cell harness; original gate incomplete** `dca67e3` |
| 5 | `GV-CHALLENGER-PROMOTION-1` | **shadow-custody primitive; original gate incomplete** `3e4dc95` |
| Repair | `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` | **only active product slice; candidate not terminal** |
| 6 | `GV-LIMITED-LIVE-1` | **CLOSED; NOT_AUTHORIZED** |

Do not resume automatic phase-label progression. Preserve prior tags as evidence, use their code as substrate, and ship the one active end-to-end result before choosing another gate.

## Build × Learn model

Use three mergeable packages rather than seven automatic branches:

- Truth core — identity, evidence, immutable events, book, cash, NAV, replay skeleton;
- Decision vertical — thesis, scenarios, admission, capital competition, aim, transition, order/fill;
- Product closure — launch/review/confirm/persist/reopen, read models, later observation, docs/ops.

Freeze minimum identity/event seams first. Freeze detailed fields only when the operator fixture exercises them. Learning remains shadow-only and cannot mutate certified history or block the vertical without a P0/P1 correctness failure.

## Immediate product target

`GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` must ship one operator loop:

```text
review ten distinct permanent identities across two clusters
→ confirm and fund at least three positions with classified residual cash
→ persist and reopen
→ record one explicit no-change observation
→ persist and reopen
→ authorize one SELL/REDUCE plus BUY/FUND transition
→ reconcile positions, cash, costs, NAV, and zero residual
→ persist, restart, reopen, and explain changed why
→ prove exact replay, idempotence, and correction lineage
```

The product entrypoint is `operated_portfolio_app.py`; `launch_operated_portfolio.py` launches it. The candidate is not accepted until focused tests, fresh-checkout AppTest, full terminal regression, and independent A/B/C pass on one immutable SHA.

## Forbidden on the current path

- provider acquisition programmes;
- broad historical loaders;
- optimizer-first allocation;
- empirical copula or MES production authority;
- automated graph contagion;
- adaptive intraday execution;
- tactical production capital;
- shorting, leverage, derivatives, or broker routing;
- live capital;
- alpha claims.

## Existing local entry points

Alpha-0 released product:

```text
python launch_alpha.py
```

Legacy development console:

```text
.venv\Scripts\python -m pytest
.venv\Scripts\python launch.py
# or
.venv\Scripts\streamlit run app.py
```

Use Python 3.12+ and the project `.venv`.
