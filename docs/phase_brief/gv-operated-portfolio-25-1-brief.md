# Phase Brief — GV-OPERATED-PORTFOLIO-25-1

Date: 2026-08-01
Status: `TERMINAL_ACCEPTED`
Certified executable candidate: `7ce85c41e9c3b6492ec884a69dc7857538386ba2`
Candidate tree: `548d6365d6355c709186aef00835219bfa30c387`
Terminal tag: `gv-operated-portfolio-25-1-terminal`
Primary authority: `docs/context/gv_endgame_authority_current.md`

## Objective

Prove one genuinely operated portfolio containing exactly 25 distinct permanent securities while preserving deterministic competition, accounting, replay, bounded operator workload, persistence, restart, correction, fresh-process reopen, and the accepted ten-security behavior through the same product path.

## Accepted product contract

```text
25 permanent identities with instrument-owned evidence and theses
→ one all-instrument competition
→ multiple funded positions and classified residual cash
→ explicit no-change
→ SELL/REDUCE plus BUY/FUND transition
→ deterministic accounting and unexplained residual 0
→ persist, restart, reopen, and changed-why explanation
→ append-only correction and fresh-process exact reopen
```

Acceptance requires:

- exactly 25 unique permanent instrument identities;
- one portfolio book, not 25 sessions, cells, runs, slots, or copied portfolios;
- one deterministic candidate row per identity and one capital competition;
- instrument-owned evidence and thesis identity with cross-instrument rebinding rejected;
- multiple positive positions plus classified residual cash;
- no-change with no mutation to orders, fills, holdings, cash, NAV, or book hash;
- at least one real SELL/REDUCE and one real BUY/FUND derived from target deltas;
- nonnegative positions and cash, explicit costs, exact NAV reconciliation, and unexplained residual `0`;
- exact replay, idempotence, certification-history replay, correction lineage, atomic persistence, restart, and fresh-process reopen;
- summary-first and exceptions-first Streamlit flow within four required actions and without per-security confirmations;
- retained ten-security behavior through the same engine, persistence implementation, application, and view.

## Architecture boundary

One engine, one persistence implementation, one schema family, one application, and one view serve the retained ten-security and accepted 25-security scenarios. Scenario declarations own fixture identities, evidence, reviews, observations, and transition targets. The shared engine owns selection, allocation, execution legs, books, certifications, replay, correction, and product projections.

Genericization has no independent acceptance status. It earns authority only because the 25-security product executes through it while the ten-security regression remains intact.

## Terminal evidence

- Exact candidate custody: branch `codex/gv-operated-portfolio-25-1`, local and remote at `7ce85c4`, clean and immutable.
- Hosted operated CI: runs `30697940370` and `30697901204`, Windows PASS and Ubuntu PASS.
- Hosted FS0 authority CI: runs `30697940369` and `30697901213`, Windows PASS, Ubuntu PASS, and byte-parity PASS.
- Controlled complete-suite comparison: zero candidate-only failures.
- Fresh-process restart and corrected-state reopen: PASS.
- Independent terminal Reviewer A/B/C: PASS/PASS/PASS; no remaining in-scope Critical/High finding.
- Terminal closure: documentation and generated context only; no production, test, workflow, dependency, or configuration change.

## Terminal disposition

`GV-OPERATED-PORTFOLIO-25-1` is accepted at executable candidate `7ce85c4`. The documentation-only closure commit containing this brief is the publication commit. `main` may move only by fast-forward, and `gv-operated-portfolio-25-1-terminal` must resolve to that closure commit.

Accepted endgame progress remains `62/100`; terminal closure does not independently authorize a score uplift. Limited Live remains closed and unauthorized.

## Forbidden scope

Do not open provider acquisition, optimizer work, broker integration, Universe, Challenger compatibility, alpha/score uplift, Limited Live, live capital, a parallel engine/storage/view path, compatibility adapters, repository-wide dependency repair, or unrelated cleanup.

## New Context Packet

## What Was Done

- Terminally accepted `GV-OPERATED-PORTFOLIO-25-1` at exact executable candidate `7ce85c41e9c3b6492ec884a69dc7857538386ba2`.
- Proved one real 25-security operated portfolio through the shared product path while preserving the accepted ten-security terminal.
- Bound exact-head Windows/Linux operated CI, FS0 authority CI, byte parity, controlled zero-candidate-only comparison, fresh-process reopen, and independent Reviewer A/B/C to the same SHA.
- Preserved the accepted `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` terminal and its tag unchanged.
- Published one documentation-only terminal closure with no production, test, workflow, dependency, or configuration change.

## What Is Locked

- `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains an immutable accepted foundation.
- `GV-OPERATED-PORTFOLIO-25-1` is terminally accepted at `7ce85c4` through one shared product path.
- Accepted endgame progress remains `62/100`.
- Limited Live, providers, optimizer, broker, Universe, Challenger compatibility, alpha/score uplift, and live capital remain closed.

## What Is Next

- Hold after terminal publication.
- Open no successor phase until the owner explicitly authorizes one bounded product result.
- Do not rerun implementation, complete tests, hosted CI, failset comparison, or Reviewer A/B/C unless a later change alters executable, test, workflow, dependency, or configuration bytes.

## First Command

```text
git status --short
```

## Next Todos

- Verify clean custody before any future phase.
- Require explicit owner authorization and a new active brief before execution resumes.
