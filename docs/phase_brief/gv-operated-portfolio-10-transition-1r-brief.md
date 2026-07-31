# Phase Brief — GV-OPERATED-PORTFOLIO-10-TRANSITION-1R

Mode: `EXECUTION_PACKET`
Status: `IMPLEMENTATION_CANDIDATE; NOT TERMINAL`
Date: 2026-07-31
Base: Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`
Canonical authority: `docs/context/gv_endgame_authority_current.md`

## Product result

An operator can review, confirm, operate, persist, reopen, and explain one deterministic ten-instrument paper portfolio across multiple cycles, including one genuine reduce-and-fund transition and one separately justified no-change observation.

## Why this slice

The next unresolved product bottleneck is not another scale wrapper. It is actual portfolio transition semantics across heterogeneous instruments: multi-position funding, SELL/REDUCE, changed evidence, capital recompetition, reconciled cash/costs/NAV, and operator-visible changed-why.

## Verbatim inherited roadmap bounds

The frozen roadmap states:

- `GV-BOUNDED-PORTFOLIO-1`: "Operate 8–15 securities across at least two economic clusters repeatedly without custody, accounting, or review collapse."
- `GV-PORTFOLIO-SCALE-1`: "Scale the operated portfolio to 25–50 securities while preserving deterministic books, replay, and bounded operator workload."
- `GV-UNIVERSE-SCALE-1`: "Scale candidate custody to 100–300+ securities with survivorship-safe membership, permanent identity, corporate actions, corrections, and reproducible universe snapshots."
- `GV-CHALLENGER-PROMOTION-1`: "Promote challengers only through baseline → shadow → prospective challenger → independent replication → bounded authority."

This repair slice closes only the first real operated-portfolio seam. It does not claim Portfolio Scale, Universe Scale, Challenger Promotion, or Live.

## Acceptance contract

The slice passes only when all are proven on one immutable candidate:

1. Exactly ten distinct permanent instrument identities.
2. At least two economically distinct clusters.
3. Instrument-specific evidence and Living Thesis Lite state; copied fixture payloads fail.
4. Exactly one portfolio book; sessions, cells, runs, or slots cannot count as breadth.
5. At least three simultaneously funded positions plus classified residual cash.
6. Deterministic capital competition across all ten instruments.
7. One separately justified no-change observation with no order, fill, holdings, cash, or NAV change.
8. One later authorized transition that:
   - reduces or closes one funded position;
   - funds or increases another;
   - emits SELL/REDUCE and BUY orders/fills;
   - updates positions, cash, costs, and NAV.
9. Exact reconstruction, idempotence, correction lineage, and zero unexplained residual.
10. Atomic persistence, restart, verified reopen, and operator-visible changed-why.
11. Fresh-checkout black-box Streamlit execution with network denied.
12. No provider, broker, optimizer, alpha, score-uplift, or live-capital path.

## Functional flow

```text
review 10 distinct instruments and two clusters
→ inspect one deterministic capital competition
→ confirm one portfolio aim
→ fund four positions and preserve classified cash
→ persist and reopen
→ admit one explicit no-change observation
→ persist and reopen
→ admit one transition-triggering observation
→ SELL/REDUCE Harbor and BUY/FUND Meridian
→ reconcile cash, costs, positions, and NAV
→ certify exact replay
→ persist, restart, reopen, and show changed why
→ append one non-economic correction without changing economics
```

## Parallel streams

| Stream | Owned result | Primary files |
|---|---|---|
| Instrument/thesis | ten identities, clusters, unique evidence/theses, dispositions | `gv_portfolio_v0/operated.py` |
| Allocation | full-universe deterministic competition and target changes | `gv_portfolio_v0/operated.py` |
| Execution/accounting | BUY and SELL/REDUCE order/fill semantics, costs, positions, cash, NAV | `gv_portfolio_v0/execution.py`, `gv_portfolio_v0/book.py` |
| Persistence/replay | atomic envelope, restart/reopen, exact replay, correction lineage | `gv_portfolio_v0/operated_storage.py`, existing `gv_portfolio_v0/replay.py` |
| Product | review → confirm → no-change → transition → changed-why | `operated_portfolio_app.py`, `views/gv_operated_portfolio_workspace.py`, `launch_operated_portfolio.py` |
| Integrator | one fixture, focused tests, AppTest, terminal evidence | `tests/gv_portfolio_v0/test_operated.py`, `tests/gv_portfolio_v0/test_operated_app.py` |

## Current candidate evidence

Windows Python 3.12.10 with diagnostic pytest 9.1.0 and Streamlit 1.58.0 passes the complete domain and persistence flow:

```text
DRAFT_REVIEW 5000
FUNDED_CERTIFIED 4992 4 orders
OBSERVED_NO_CHANGE_CERTIFIED 4992 4 orders
TRANSITION_CERTIFIED 4988 SELL+BUY
CORRECTED_CERTIFIED 4988 one correction
```

The repaired acceptance kernel now proves:

- deterministic selected funded IDs are execution authority;
- each review retains its instrument-owned initial evidence lineage;
- orders, fills, trade-authority chains, observations, changed-why, cash, and costs equal event-derived projections;
- transition legs equal exact before/after target deltas;
- every historical certification object is replayed at its original event prefix;
- correction history contains derived links only, not self-asserted stability booleans;
- persistence rejects symlink and Windows-junction ancestors before creation, write, replace, and load;
- AppTest completes confirmation, no-change, transition, correction, and fresh-process corrected reopen with network denied.

Pinned narrow verification using `requirements-alpha.txt`:

- Windows Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0;
- `pip check PASS`;
- operated domain + AppTest: `15/15 PASS`;
- book/execution/replay/operated focused set: `70/70 PASS`;
- context/authority set: `33/33 PASS`;
- complete `tests/gv_portfolio_v0`: `145/145 PASS`;
- combined operated/context gate: `178/178 PASS`;
- `git diff --check PASS`.

The monorepo `requirements.lock` is not part of this acceptance. It covers unrelated broker/data stacks and is not used by the operated-product workflow.

## Open gates

- `.github/workflows/gv-operated-portfolio.yml` is added but has not yet run on a pushed immutable SHA.
- Hosted Windows/Linux parity is not yet proven.
- Fresh-checkout execution against one immutable candidate SHA is not yet run.
- Full repository regression/failset comparison is not yet run.
- Independent Reviewer A/B/C are not yet run against one immutable candidate SHA.
- One locally frozen candidate commit exists at current branch HEAD; push, hosted parity, `origin/main` fast-forward, and terminal tag remain open.

## Terminal verification

Focused during implementation:

```text
python -m pytest tests/gv_portfolio_v0/test_operated.py -q
python -m pytest tests/gv_portfolio_v0/test_operated_app.py -q
python -m pytest tests/gv_portfolio_v0/test_book.py tests/gv_portfolio_v0/test_execution.py tests/gv_portfolio_v0/test_replay.py -q
```

Once, at frozen terminal candidate:

```text
python -m pytest -q
fresh checkout → operated_portfolio_app.py AppTest with network denied
base/candidate failure-node comparison
independent Reviewer A/B/C against exact SHA
```

Reviewer A must compare this brief and implementation to the verbatim frozen roadmap, not merely to lower-level tests.

## Forbidden scope

Scale/Universe/Challenger compatibility adapters; repeated fixture slots as breadth; provider acquisition; broad loaders; optimizer-first allocation; shorting; leverage; derivatives; broker routing; live capital; Limited Live opening; immutable tag rewriting; dirty operator-root development.

## Stop conditions

Stop and repair the current slice if:

- any identity/evidence/thesis is duplicated;
- capital competition omits an instrument;
- one session/cell/run is counted as a security;
- SELL/REDUCE can overdraw a position;
- cash or positions become negative;
- replay differs, residual is nonzero, or prior certification mutates;
- UI cannot complete and reopen the flow from a fresh checkout;
- Reviewer A finds any weakened original quantity or product behavior.

## What Was Done

- Reconciled terminal classifications without rewriting immutable commits or tags.
- Restored the frozen roadmap's distinct-security quantities and challenger-outcome chain as controlling acceptance.
- Implemented one ten-instrument, two-cluster portfolio state machine with unique evidence and theses.
- Added shared deterministic SELL order/fill and accounting semantics.
- Added multi-position funding, explicit no-change, reduce-and-fund transition, changed-why, exact replay, correction lineage, atomic persistence, reopen, and Streamlit product entrypoints.
- Added focused domain/persistence tests and a black-box AppTest specification.

## What Is Locked

- `ACTIVE_PRODUCT_PHASE = GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` only.
- Authority base remains exact Challenger terminal `3e4dc957f475945169ddf33ed359254bd98dc64d`.
- Slice 0 and Replay 0 are accepted; Bounded/Scale/Universe/Challenger are substrates with original semantic gates incomplete.
- Exactly ten distinct instruments, at least two clusters, one book, at least three funded positions, classified cash, no-change, SELL/REDUCE plus BUY/FUND, replay, correction lineage, persistence/reopen, and changed-why are non-weakenable.
- Limited Live remains closed and unauthorized.
- Accepted endgame progress remains `52/100` until terminal evidence passes.

## What Is Next

- Bank the product repair, authority reconciliation, narrow CI workflow, and `.worktree-lifecycle/` exclusion in one immutable candidate SHA.
- Push that exact SHA and run hosted Windows/Linux parity, fresh-checkout correction/reopen AppTest, full repository regression/failset comparison, and independent Reviewer A/B/C concurrently.
- Fast-forward `origin/main` and create a terminal tag only after every exact-SHA gate passes.

## First Command

`.venv\\Scripts\\python -m pytest -q tests/gv_portfolio_v0 tests/test_build_context_packet.py tests/test_phase60_d343_hygiene.py tests/test_phase60_d345_closeout.py tests/test_phase61_context_hygiene.py`

Expected current result: `178/178 PASS` under the narrow pinned environment.

## Next Todos

- push the locally frozen candidate SHA;
- prove hosted Windows/Linux parity;
- run fresh-checkout/full failset/A/B/C against the exact SHA;
- main fast-forward and tag only after PASS.
