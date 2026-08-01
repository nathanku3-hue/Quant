# Done Checklist — Current

Date: 2026-08-01
Phase: `GV-OPERATED-PORTFOLIO-25-1`
Status: `TERMINAL_ACCEPTED`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Authority and scope

- [x] `ACTIVE_BRIEF` selects `GV-OPERATED-PORTFOLIO-25-1`.
- [x] Prior terminal `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` remains immutable.
- [x] Exactly one operated 25-security portfolio is proved; sessions, cells, runs, slots, and copies do not count as securities.
- [x] One shared engine, persistence implementation, schema family, application, and view serve retained 10 and accepted 25 scenarios.
- [x] Limited Live, providers, optimizer, broker, Universe, Challenger compatibility, alpha/score uplift, and live capital remain closed.

## Product result

- [x] Exactly 25 unique permanent instrument identities and keys.
- [x] Every instrument retains owned evidence and thesis identity; cross-instrument rebinding fails closed.
- [x] One deterministic candidate row per identity and one all-instrument capital competition.
- [x] Multiple positive positions plus classified residual cash.
- [x] Explicit no-change preserves orders, fills, positions, cash, NAV, and book hash.
- [x] Real SELL/REDUCE and BUY/FUND legs derive from target deltas.
- [x] Positions and cash remain nonnegative; costs and NAV reconcile; unexplained residual is `0`.
- [x] Exact replay, idempotence, certification-history replay, append-only correction, and changed-why pass.
- [x] Scenario-bound atomic persistence, linked-ancestor confinement, restart, and fresh-process reopen pass.
- [x] Summary-first and exceptions-first flow requires at most four actions and no per-security confirmations.
- [x] Retained ten-security behavior remains green through the same path.

## Candidate custody and terminal evidence

- [x] Certified executable candidate is `7ce85c41e9c3b6492ec884a69dc7857538386ba2` with tree `548d6365d6355c709186aef00835219bfa30c387`.
- [x] Candidate branch `codex/gv-operated-portfolio-25-1` is clean, remote-equal, and immutable.
- [x] Exact-head operated CI passes on Windows and Ubuntu in runs `30697940370` and `30697901204`.
- [x] Exact-head FS0 authority CI and byte parity pass in runs `30697940369` and `30697901213`.
- [x] Controlled base/candidate complete-suite comparison has zero candidate-only failures.
- [x] Reviewer A passes product result, bounded workload, and retained behavior.
- [x] Reviewer B passes accounting, execution, replay, certification, correction, hosted runtime, and fresh-process reopen.
- [x] Reviewer C passes custody, reproducibility, failset identity, atomic persistence, and data integrity.
- [x] No in-scope Critical/High finding remains.

## Documentation-only closure

- [x] Terminal evidence packet added.
- [x] SAW closure report added and reconciles existing A/B/C evidence without rerunning it.
- [x] PM handover added.
- [x] Current truth surfaces and active phase brief record terminal acceptance.
- [x] Generated context is rebuilt and validated.
- [x] Context and authority validation pass.
- [x] Diff from `7ce85c4` contains no production, test, workflow, dependency, or configuration change.
- [x] `main` publication is fast-forward only.
- [x] Terminal tag is `gv-operated-portfolio-25-1-terminal` and targets the documentation-only closure commit.
- [x] Accepted score was reconsidered and remains `62/100`; closure alone does not authorize uplift.

## Stop condition

Hold after publication. No successor phase starts without explicit owner authorization and a new active brief. Do not rerun implementation, complete tests, hosted CI, failset comparison, or Reviewer A/B/C unless later work changes executable, test, workflow, dependency, or configuration bytes.
