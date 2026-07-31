# GV Operated Portfolio 10 Transition 1R — Terminal Evidence

Mode: `CLOSURE_REPORT`
Date: 2026-08-01
Authority base: `3e4dc957f475945169ddf33ed359254bd98dc64d`
Certified executable candidate: `0d15e9c59c6b3ca051b3aa815018889d1e94857f`
Certified candidate tree: `4dc013e2b50da8c22456719f8fba75d7de0dfa41`
Terminal tag: `gv-operated-portfolio-10-transition-1r-terminal`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Product result

The certified candidate lets an operator review ten permanent instruments across two economic clusters, confirm one deterministic portfolio, fund four positions with classified residual cash, persist and reopen, record a separately justified no-change observation, execute a real `SELL/REDUCE HARBOR 4` plus `BUY/FUND MERID 5` transition, reconcile cash/costs/positions/NAV, explain changed-why, append a non-economic correction, and reopen the corrected state in a fresh process.

Terminal economics remain:

```text
DRAFT_REVIEW NAV 5000
→ FUNDED_CERTIFIED NAV 4992
→ OBSERVED_NO_CHANGE_CERTIFIED NAV 4992
→ TRANSITION_CERTIFIED NAV 4988
→ CORRECTED_CERTIFIED NAV 4988
```

Total explicit costs are `12`; unexplained residual is `0`; cash and positions remain nonnegative.

## Exact-head hosted proof

GitHub Actions run `30640915560` executed exact PR head `0d15e9c` through the operated workflow.

| Hosted lane | Exact-head checkout | Clean checkout | Full operated + FS0 package | Context validation | Post-test tracked-byte check | Verdict |
|---|---|---|---|---|---|---|
| `windows-latest` | PASS | PASS | PASS | PASS | PASS | PASS |
| `ubuntu-latest` | PASS | PASS | PASS | PASS | PASS | PASS |

Additional exact-head runs passed:

- GV-FS0 Product: `30640915001`;
- GV-FS0 Protocol Freeze: `30640915046`;
- operated push run: `30640910377`.

## Controlled full-suite comparison

The complete candidate-only suite ran once in a clean detached exact-SHA checkout with Windows Python 3.12.10 and an explicit `PATH`, `COMSPEC`, `SystemRoot`, Git, SHA, tree, and clean-status preflight.

| Metric | Base `3e4dc95` | Candidate `0d15e9c` |
|---|---:|---:|
| Executed tests | 2702 | 2718 |
| Failures | 23 | 19 |
| Errors | 0 | 0 |
| Skips | 16 | 16 |
| Candidate-only failures | n/a | 0 |

All 19 candidate failures are members of the retained 23-node base failset. Four inherited context failures are fixed. The complete `tests/gv_fs0_product` package is green in hosted CI and in the prior exact-byte candidate proof.

Retained local evidence:

- `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/full-suite.xml`;
- `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/failset-comparison.json`;
- `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/failset-comparison-receipt.md`;
- `.worktree-lifecycle/gv-operated-0d15e9c-terminal-evidence/hosted-ci-receipt.md`.

## Independent terminal review

| Reviewer | Ownership | Verdict |
|---|---|---|
| A | original product result, user flow, semantic non-weakening | PASS |
| B | hosted runtime, dependency execution boundary, Windows/Linux exact-head custody | PASS |
| C | clean checkout, full-suite failset identity, reproducibility and publication boundary | PASS |

No in-scope Critical or High finding remains.

## Closure law

The terminal closure commit may modify documentation only. Before publication, every path outside `docs/` must be byte-identical to certified candidate `0d15e9c`. `main` may move only by fast-forward, and the terminal tag may be created only after that identity proof. No provider, broker, optimizer, score-uplift, live-capital, or Limited Live authority is opened.
