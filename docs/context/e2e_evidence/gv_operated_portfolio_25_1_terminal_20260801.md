# GV Operated Portfolio 25-1 — Terminal Evidence

Date: 2026-08-01
Phase: `GV-OPERATED-PORTFOLIO-25-1`
Disposition: `TERMINAL_ACCEPTED`
Certified executable candidate: `7ce85c41e9c3b6492ec884a69dc7857538386ba2`
Candidate tree: `548d6365d6355c709186aef00835219bfa30c387`
Candidate branch: `codex/gv-operated-portfolio-25-1`
Closure branch: `codex/gv-operated-portfolio-25-1-terminal-closure`
Terminal tag: `gv-operated-portfolio-25-1-terminal`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Decision

Terminally accept the exact executable candidate `7ce85c4`. Do not recut, amend, squash, rebase, or rerun implementation evidence. Publish one documentation-only closure commit by fast-forward and tag that closure commit after remote equality is proved.

## Product result

The accepted candidate operates one portfolio containing exactly 25 distinct permanent securities through the same product path as the retained ten-security terminal.

```text
25 permanent identities with instrument-owned evidence and theses
→ one deterministic all-instrument competition
→ multiple funded positions plus classified residual cash
→ explicit no-change
→ real SELL/REDUCE plus BUY/FUND transition
→ deterministic positions, cash, costs, NAV, and unexplained residual 0
→ persist, restart, reopen, changed-why
→ append-only correction and fresh-process exact reopen
```

No session, cell, run, slot, or copied portfolio is counted as a security. The visible operator flow remains bounded to at most four required actions and requires no per-security confirmation.

## Candidate custody

| Check | Result |
|---|---|
| Local candidate HEAD | `7ce85c41e9c3b6492ec884a69dc7857538386ba2` |
| Remote candidate branch | same exact SHA |
| Candidate tree | `548d6365d6355c709186aef00835219bfa30c387` |
| Candidate worktree | clean |
| Prior `main` | `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e` before closure |
| Prior terminal tag | `gv-operated-portfolio-10-transition-1r-terminal^{}` remains `2349e1b` |
| New terminal tag before closure | absent |

## Exact-head hosted evidence

### GV Operated Portfolio

| Event | Run | Ubuntu | Windows | Exact head |
|---|---:|---|---|---|
| pull request | `30697940370` | PASS, job `91363882177` | PASS, job `91363882191` | `7ce85c4` |
| push | `30697901204` | PASS, job `91363783157` | PASS, job `91363783189` | `7ce85c4` |

### GV-FS0 Product

| Event | Run | Ubuntu | Windows | Byte parity | Exact head |
|---|---:|---|---|---|---|
| pull request | `30697940369` | PASS, job `91363882213` | PASS, job `91363882197` | PASS, job `91364631495` | `7ce85c4` |
| push | `30697901213` | PASS, job `91363783276` | PASS, job `91363783290` | PASS, job `91364240565` | `7ce85c4` |

These runs prove exact-head checkout, cross-platform operated behavior, FS0 authority behavior, dependency coverage, clean-checkout custody, and byte parity for the certified executable candidate.

## Controlled complete-suite comparison

The retained controlled base/candidate comparison is bound to `7ce85c4` and reports:

- complete base and candidate failure-node comparison performed;
- candidate-only failures: `0`;
- no terminal acceptance rule weakened;
- no additional complete-suite rerun required for a documentation-only closure.

The earlier environment-invalid detached execution is not evidence. Only the environment-proven controlled comparison is accepted.

## Fresh-process and product-boundary evidence

- Fresh-process restart and corrected-state reopen: PASS.
- Scenario-bound persistence and linked-ancestor confinement: PASS.
- Exact replay, certification-history replay, correction lineage, and data-integrity checks: PASS.
- Retained ten-security behavior through the shared path: PASS.
- No parallel engine, storage implementation, schema family, application, or view: PASS.

## Independent terminal review

| Reviewer | Scope | Final result |
|---|---|---|
| A | product result, 25-security breadth, bounded workload, retained behavior, semantic non-weakening | PASS; no remaining Critical/High |
| B | accounting, execution, replay, certification, correction, hosted runtime, fresh-process restart/reopen | PASS; prior restart/hosted blockers closed |
| C | custody, reproducibility, complete-suite failset identity, atomic persistence, data integrity | PASS; prior terminal data-integrity blocker closed |

Implementation and Reviewer A/B/C were separate executions. This closure reconciles those final results and does not rerun them.

## Documentation-only closure law

The closure commit may change only documentation and generated context. It must prove an empty diff from `7ce85c4` for:

- production/runtime code;
- tests and fixtures;
- `.github/workflows/**`;
- dependency and lock files;
- executable configuration.

`main` may move only by fast-forward from `2349e1b` through `7ce85c4` to the closure commit. After remote equality is verified, `gv-operated-portfolio-25-1-terminal^{}` must resolve to that same closure commit. The previous terminal tag must remain unchanged.

## Residual boundaries

Inherited repository failures remain owned outside this phase and are non-blocking because the candidate-only set is zero. Provider acquisition, optimizer, broker, Universe, Challenger compatibility, alpha/score uplift, Limited Live, and live capital remain unauthorized.

## Verdict

`GV-OPERATED-PORTFOLIO-25-1` is terminally accepted at executable candidate `7ce85c4`. The next valid operation after closure publication is to hold pending explicit owner authorization for a new phase.
