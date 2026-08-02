# Phase Brief — GV-PROSPECTIVE-PAPER-BASELINE-1

Date: 2026-08-02
Status: `EXECUTABLE_REMOTE_CANDIDATE; DATE_REPAIR_PRESENT; HOSTED_CI_AND_REAL_EVIDENCE_SEAM_PENDING`
Base capability candidate: `9c7e75ac3a7b87f85d505a53e759594dd1d07b9d`
Executable candidate: `147397f669c81eb2ab3bfd5054d676d9d0c9c77f`
Executable tree: `a43a6a83549c7824b99f3db171451075a871f289`
Branch: `repair/gv-prospective-paper-baseline-1-r1`; local and remote equal at the executable SHA.
Accepted product score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Objective

Add one genuine runtime portfolio-operating path to the accepted 25-security substrate. An operator supplies new observation content, source locator, UTC timestamp, instrument ownership, explicit review proposals, and rationale. The system produces a deterministic mutation-free preview; only explicit confirmation grants authority. Rejection is append-only and cannot mutate evidence, reviews, decisions, holdings, cash, orders, fills, or the certified book.

This implementation proves capability. Automated tests inject runtime values and therefore do not by themselves constitute prospective evidence. The synthetic 25-security profile is a regression and usability fixture, not the forward product milestone. Score remains `62/100` until real source evidence enters a real instrument decision and survives operator confirmation, persistence, and replay.

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

- Historical broader test receipts belong to capability candidate `9c7e75a`: retained operated/25/App `23/23`, scale repair `13/13`, shared book/allocation/execution/replay/strategy/vertical `104/104`, and historical bounded/scale/universe/challenger `24/24`.
- Executable candidate `147397f` repairs the future-dated September bootstrap and has a reported current-tip prospective subset result of `15/15 PASS` (`12` core plus `3` Streamlit product tests).
- This authority correction does not relabel the historical broader receipts as current-tip execution.
- Exact-SHA hosted Windows/Linux proof is absent and remains required before terminal publication.

Hosted CI is not a prerequisite for operating the paper product or running the non-authoritative Learn lane. No independent terminal-acceptance claim is made.

## Product disposition

The implementation candidate closes the main software capability gap: the product can now accept unscripted runtime observations and convert confirmed proposals into deterministic certified portfolio state. It does not yet prove genuine prospective operation because the passing episodes are test-injected.

Accepted score remains `62/100`. One synthetic operator smoke episode strengthens operability evidence but adds no capability and therefore adds no score. A real MU evidence → real identity → portfolio outcome → confirmation → replay slice would support a nonbinding `66–68/100` reassessment; repeated real-identity operation plus an independent comparison is required for `70+`.

## Revised roadmap

```text
147397f executable date repair
→ minimal authority synchronization
→ one synthetic operator smoke episode
→ concurrent MU/NVDA reconciliation in a non-authoritative lane
→ one real-source, real-MU-identity, replayable ABSTAIN/NO_POSITION or ADMIT decision
→ independent shadow proposal on the same evidence
→ repeated 3–5 real-security prospective operation
→ broader Universe custody only when required
→ separately authorized Limited Live
```

Australian legal review is not a blocker for paper baseline or paper Challenger work. It remains mandatory before broker credentials, automated submission, client assets, advice activity, or real-capital operation.

## Forbidden scope

Do not add providers, optimizer frameworks, broker credentials, autonomous submission, client assets, live capital, a parallel engine, a new database, a second storage path, a new status hierarchy, old Challenger compatibility adapters, or Universe expansion in this phase.

## Remaining acceptance gate

1. Preserve executable candidate `147397f`; do not rewrite its test history.
2. Bank one fresh-home synthetic no-change smoke proving preview immutability, confirmation, append-only lineage, and fresh-process reconstruction. This proves operability only.
3. Reconcile the banked MU and NVDA packages without network access, score/rank output, portfolio mutation, or alpha/investability claims.
4. Route that reconciliation into one real MU identity with classified cash, deterministic `ABSTAIN/NO_POSITION` or `ADMIT`, explicit preview/confirmation, append-only persistence, and fresh-process replay.
5. Collect exact-SHA Windows/Linux proof before terminal publication.
6. Open a replacement shadow proposal only after the real-evidence seam works; do not adapt the obsolete slot/cell Challenger.

## What Was Done

- Added runtime observation preview, confirmation, transition, rejection, persistence, UI, and exact full-state reconstruction.
- Derived the prospective profile from the accepted 25-security catalogue without duplicating it.
- Preserved the accepted engine, storage, book, replay, certification, and app boundaries.

## What Is Locked

- Accepted foundation `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains immutable.
- Accepted terminal `GV-OPERATED-PORTFOLIO-25-1` and its 25-security identity remain unchanged.
- Base repair `5687a2c` remains immutable and remote-equal.
- Capability candidate `9c7e75a` retains its historical broader receipts.
- Executable candidate `147397f`, tree `a43a6a8`, is remote-equal on `repair/gv-prospective-paper-baseline-1-r1` and repairs the September bootstrap defect.
- Accepted score remains `62/100`.
- Test-injected runtime data proves capability only, not prospective evidence.
- Limited Live remains closed.

## What Is Next

- Use `147397f` as executable authority and collect hosted CI concurrently.
- Bank one synthetic operator smoke, then stop treating repeated synthetic episodes as the product milestone.
- Reconcile MU/NVDA evidence and ship the one-real-identity source-to-portfolio seam.
- Replace the obsolete Challenger harness only after that seam works.

## First Command

```text
git status --short
```

## Next Todos

- Complete exact-SHA hosted CI for `147397f` before publication.
- Retain one synthetic no-change smoke as usability evidence only.
- Produce a bounded MU/NVDA reconciliation and one real-MU-identity replayable portfolio decision.
- Open an independent shadow proposal on the exact same evidence only after the real-evidence seam passes.
