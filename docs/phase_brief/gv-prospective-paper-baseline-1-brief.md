# Phase Brief — GV-PROSPECTIVE-PAPER-BASELINE-1

Date: 2026-08-02
Status: `FROZEN_REMOTE_CANDIDATE; LOCAL_GATES_PASS; HOSTED_CI_AND_REAL_PROSPECTIVE_EVIDENCE_PENDING`
Base: `5687a2c2ae61ef8b5de676cffad5b19df9224b01`
Candidate: `9c7e75ac3a7b87f85d505a53e759594dd1d07b9d`
Candidate tree: `20d5eb712799555003b2efcf6aed96ca89db9f67`
Branch: `product/gv-prospective-paper-baseline-1`; local and remote equal at the candidate SHA.
Accepted product score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Objective

Add one genuine runtime portfolio-operating path to the accepted 25-security substrate. An operator supplies new observation content, source locator, UTC timestamp, instrument ownership, explicit review proposals, and rationale. The system produces a deterministic mutation-free preview; only explicit confirmation grants authority. Rejection is append-only and cannot mutate evidence, reviews, decisions, holdings, cash, orders, fills, or the certified book.

This implementation proves capability. Automated tests inject runtime values and therefore do not by themselves constitute prospective evidence. Score remains `62/100` until real operator-supplied episodes are executed and retained.

## Endgame alignment

```text
accepted 25-security certified portfolio
→ runtime observation envelope
→ explicit operator review proposals
→ deterministic preview
→ human confirm or reject
→ append-only event/state projection
→ atomic persist
→ fresh-process reopen
→ exact evidence/review/observation/snapshot/certification/book reconstruction
```

## Delivered slices

### Slice A — no-change confirmation

- Derives a prospective profile from `SCENARIO_25` without copying its instrument catalogue.
- Bootstraps the certified funded 25-security portfolio through the accepted engine.
- Accepts one runtime observation and one explicit review proposal.
- Produces a mutation-free no-change preview.
- Confirms append-only, persists atomically, reopens in a fresh process, and reconstructs full state.
- Preserves holdings, cash, orders, fills, NAV, residual, and book hash.

### Slice B — real capital transition

- Accepts one runtime observation containing explicit proposals for multiple owned instruments.
- Deterministically recomputes capital competition.
- Produces one SELL/REDUCE and one BUY/FUND transition.
- Requires preview and explicit confirmation before execution authority exists.
- Persists and reconstructs evidence, reviews, observation, snapshot, events, execution, certification, and book with residual `0`.

### Slice C — rejection

- Rejects a preview through an explicit operator action.
- Appends a rejection event and recertification.
- Retains the rejected proposal and rationale.
- Does not admit its evidence or mutate reviews, decision snapshots, holdings, cash, orders, fills, or book economics.
- Reconstructs three sequential episodes from the append-only event log.

## Locked semantics

- Instrument review outcomes are exactly `ADMIT`, `REJECT`, or `ABSTAIN`.
- `CASH` is a portfolio capital candidate, never a per-security review outcome.
- Non-`ADMIT` reviews must have target quantity `0`.
- Score, target quantity, thesis, and outcome are operator proposals until deterministic validation and confirmation.
- Preview is non-authoritative and must not modify persisted bytes.
- Runtime observation content is absent from scenario code.
- The event log is the authority for repeated episode reconstruction; fixed scenario-authored status/count branches are not extended.
- One storage implementation, one engine, one app entry point, one book reducer, and one replay/certification path remain in use.

## Operator workload

Each episode requires at most two product actions:

1. Preview.
2. Confirm or reject.

Field entry is not counted as a separate authorization action. No per-security confirmation loop is introduced.

## Validation evidence

- Prospective core tests: `11/11 PASS`.
- Prospective Streamlit product tests: `3/3 PASS`.
- Retained operated/25/App tests: `23/23 PASS`.
- Scale persistence/timestamp repair tests: `13/13 PASS`.
- Shared book/allocation/execution/replay/strategy/vertical tests: `104/104 PASS`.
- Historical bounded/scale/universe/challenger tests: `24/24 PASS`.
- `git diff --check`: PASS before authority synchronization.

Exact-SHA hosted Windows/Linux CI is publication evidence, not a prerequisite for continuing implementation. Independent Reviewer A/B/C is unavailable and was explicitly waived as a blocking prerequisite for this candidate; no claim of independent terminal acceptance is made.

## Product disposition

The implementation candidate closes the main software capability gap: the product can now accept unscripted runtime observations and convert confirmed proposals into deterministic certified portfolio state. It does not yet prove genuine prospective operation because the passing episodes are test-injected.

Accepted score remains `62/100`. A score uplift to approximately `69–72/100` requires retained real operator-supplied episodes under the same flow.

## Revised roadmap

```text
25-security operated terminal
→ scale persistence/timestamp repair
→ prospective paper capability candidate
→ real operator-supplied prospective episodes
→ real shadow challenger on the same certified 25-security opportunity set
→ Universe custody only when broader membership is required
→ separately authorized Limited Live
```

Australian legal review is not a blocker for paper baseline or paper Challenger work. It remains mandatory before broker credentials, automated submission, client assets, advice activity, or real-capital operation.

## Forbidden scope

Do not add providers, optimizer frameworks, broker credentials, autonomous submission, client assets, live capital, a parallel engine, a new database, a second storage path, a new status hierarchy, old Challenger compatibility adapters, or Universe expansion in this phase.

## Remaining acceptance gate

1. Preserve exact remote candidate `9c7e75a`; do not amend or recut it.
2. Run exact-SHA Windows/Linux CI.
3. Execute three real operator-supplied episodes through the product flow, including at least one justified no-change and one real target transition.
4. Retain fresh-process reopen and full reconstruction evidence after every episode.
5. Only then reconsider score uplift and open the real shadow Challenger.

## What Was Done

- Added runtime observation preview, confirmation, transition, rejection, persistence, UI, and exact full-state reconstruction.
- Derived the prospective profile from the accepted 25-security catalogue without duplicating it.
- Preserved the accepted engine, storage, book, replay, certification, and app boundaries.

## What Is Locked

- Accepted foundation `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains immutable.
- Accepted terminal `GV-OPERATED-PORTFOLIO-25-1` and its 25-security identity remain unchanged.
- Base repair `5687a2c` remains immutable and remote-equal.
- Frozen candidate `9c7e75a`, tree `20d5eb7`, is remote-equal on `product/gv-prospective-paper-baseline-1`.
- Accepted score remains `62/100`.
- Test-injected runtime data proves capability only, not prospective evidence.
- Limited Live remains closed.

## What Is Next

- Preserve remote-equal candidate `9c7e75a` and collect hosted CI evidence.
- Collect genuine operator-supplied prospective episodes.
- Replace the obsolete Challenger harness only after prospective baseline evidence is banked.

## First Command

```text
git status --short
```

## Next Todos

- Complete exact-SHA hosted CI.
- Execute and retain three real operator-supplied episodes.
- Open a real independent shadow Challenger on the same 25-security opportunity set.
