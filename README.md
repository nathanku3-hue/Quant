# Terminal Zero / GodView Certified Portfolio OS

Status: `GV-OPERATED-PORTFOLIO-25-1 AUTHORIZED; IMPLEMENTATION_ACTIVE; NOT_FROZEN; LIVE CLOSED`
Date: 2026-08-01
Authority base: terminal `main` `2349e1b`
Accepted operated terminal: `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` at candidate `0d15e9c`, closure `2349e1b`, terminal tag preserved
Slice 0: accepted product foundation `85e6601`
Replay 0: accepted integrity foundation `0e4b93f`
Portfolio Scale `c37abf0`: deterministic multi-session harness; original 25–50-security objective remains incomplete until the active phase passes terminal review
Universe Scale `dca67e3`: deterministic multi-cell harness; original 100–300+ custody objective incomplete
Challenger `3e4dc95`: shadow-custody separation primitive; original promotion objective incomplete
Accepted endgame progress: `62/100`; no active-phase uplift claimed
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
| Repair | `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` | **accepted terminal product** `0d15e9c` / `2349e1b` |
| Scale repair | `GV-OPERATED-PORTFOLIO-25-1` | **only active product phase; implementation checkpoint; not frozen** |
| 6 | `GV-LIMITED-LIVE-1` | **CLOSED; NOT_AUTHORIZED** |

Do not resume automatic phase-label progression. Preserve prior terminals as immutable evidence and run the active 25-security result through the same operated engine, persistence path, application, and view as the retained ten-security regression scenario.

## Build × Learn model

Use three mergeable packages rather than seven automatic branches:

- Truth core — identity, evidence, immutable events, book, cash, NAV, replay skeleton;
- Decision vertical — thesis, scenarios, admission, capital competition, aim, transition, order/fill;
- Product closure — launch/review/confirm/persist/reopen, read models, later observation, docs/ops.

Freeze minimum identity/event seams first. Freeze detailed fields only when the operator fixture exercises them. Learning remains shadow-only and cannot mutate certified history or block the vertical without a P0/P1 correctness failure.

## Immediate product target

`GV-OPERATED-PORTFOLIO-25-1` must ship one scalable operator loop:

```text
review exactly 25 distinct permanent identities across at least two meaningful clusters
→ inspect owned evidence/thesis state and one competition across all 25
→ confirm one portfolio and fund multiple positions with classified residual cash
→ persist and reopen
→ record one explicit no-change observation
→ persist and reopen
→ authorize at least one SELL/REDUCE plus one BUY/FUND from exact target deltas
→ reconcile positions, cash, costs, NAV, and zero residual
→ persist, restart, reopen, correct append-only, and explain changed why
→ prove exact replay and complete the flow within four required actions
```

The shared product entrypoint is `operated_portfolio_app.py`; `launch_operated_portfolio.py` retains the ten-security regression and `launch_operated_portfolio_25.py` selects the 25-security scenario. One engine, storage path, application, and view serve both scenarios. The phase is not accepted until one frozen SHA passes exact-head Windows/Linux, controlled base/candidate comparison, and independent A/B/C.

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
