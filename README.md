# Terminal Zero / GodView Certified Portfolio OS

Status: `REPLAY_0_ACCEPTED; GV-BOUNDED-PORTFOLIO-1 OPEN`
Date: 2026-07-30
Slice 0 immutable: `85e6601`
Replay 0 terminal: `0e4b93f` (tag `gv-replay-0-terminal`)
Released substrate: `gv-alpha0-paper-decision-v0.1.0` (`a88ed05`)
Release-proof tip: `93e7a55`
Shipped product score: `39/100` unchanged
Observed comparisons: `0`

GodView is a local-first, point-in-time certified portfolio operating system. Its product unit is a complete portfolio decision and operating loop, not an isolated stock case and not an optimizer-first research platform.

```text
one declared PIT opportunity set
→ complete portfolio including classified cash and abstentions
→ prospective operation
→ deterministic accounting and replay
→ lifecycle-based review
```

## Current authority

- [Corrected Build × Learn roadmap](docs/architecture/godview_v2_frozen_build_learn_roadmap.md) — seven-slice product sequence, R0 custody repair, and three-package execution law
- [Top-level roadmap](docs/architecture/top_level_roadmap.md) — compact active canon
- [PRD](PRD.md) — current product requirements
- [Product specification](PRODUCT_SPEC.md) — product contract and historical notices
- [Phase queue](PHASE_QUEUE.md) — active slice pickup and dependency map
- [Planner packet](docs/context/planner_packet_current.md) — compact current truth

If another document conflicts with these active surfaces, the corrected roadmap and `docs/context/ACTIVE_BRIEF` win.

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

| Slice | Name | Status |
|---|---|---|
| 0 | `GV-MICRO-PORTFOLIO-VERTICAL-0` | **accepted immutable** `85e6601` |
| 1 | `GV-DETERMINISTIC-REPLAY-0` | **ACCEPTED** `0e4b93f` |
| 2 | `GV-BOUNDED-PORTFOLIO-1` | **OPEN** (pin Replay `0e4b93f`) |
| 3 | `GV-PORTFOLIO-SCALE-1` | evidence-conditioned |
| 4 | `GV-UNIVERSE-SCALE-1` | evidence-conditioned |
| 5 | `GV-CHALLENGER-PROMOTION-1` | shadow-first |
| 6 | `GV-LIMITED-LIVE-1` | separate owner gate required |

Only `GV-BOUNDED-PORTFOLIO-1` is implementation-authorized. Later boundaries remain evidence-gated so delivery does not return to open-ended architecture discovery.

## Build × Learn model

Use three mergeable packages rather than seven automatic branches:

- Truth core — identity, evidence, immutable events, book, cash, NAV, replay skeleton;
- Decision vertical — thesis, scenarios, admission, capital competition, aim, transition, order/fill;
- Product closure — launch/review/confirm/persist/reopen, read models, later observation, docs/ops.

Freeze minimum identity/event seams first. Freeze detailed fields only when the operator fixture exercises them. Learning remains shadow-only and cannot mutate certified history or block the vertical without a P0/P1 correctness failure.

## Immediate product target

`GV-MICRO-PORTFOLIO-VERTICAL-0` will operate:

- 3–5 declared securities;
- one reference benchmark;
- classified cash;
- one principal thesis, substitute, competing opportunity, and rejection;
- Living Thesis Lite;
- Bull/Base/Bear scenarios;
- conservative dollar capacity;
- simultaneous capital competition;
- deterministic paper execution;
- one later prospective update.

It will then feed `GV-DETERMINISTIC-REPLAY-0`, which must reconstruct the exact book, cash, quantities, corporate actions, fills, and thesis state before portfolio expansion opens.

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
