# GV Operated Portfolio 25 — Pre-Freeze Evidence

Mode: `EXECUTION_PACKET`
Date: 2026-08-01
Phase: `GV-OPERATED-PORTFOLIO-25-1`
Base: `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e`
Status: `PREFREEZE_PRODUCT_AND_OWNERSHIP_PASS; CANDIDATE_CUSTODY_OPEN`

## Product checkpoint

One shared operated engine, persistence implementation, application, and view serve:

- retained `GV-OPERATED-PORTFOLIO-10-TRANSITION-1R` regression scenario;
- active `GV-OPERATED-PORTFOLIO-25-1` scenario.

The 25-security fixture exercises:

```text
25 permanent identities across 5 fixture clusters
→ one competition covering all 25 exactly once
→ 8 funded positions and classified residual cash
→ explicit no-change
→ SELL + BUY target-delta transition
→ deterministic book and residual 0
→ append-only non-economic correction
→ fresh-process reopen
```

Five clusters, eight funded positions, and transition-leg count remain fixture parameters, not product authority.

## Stop-rule inspection

- parallel domain engine: none;
- parallel persistence implementation: none;
- parallel schema family: none;
- parallel view/application stack: none;
- fixture symbols in shared engine/storage/view/app: none;
- retained ten-security regression: PASS;
- required actions: four;
- per-security confirmations: zero;
- cross-instrument evidence rebinding: fails closed;
- sessions/cells/runs/slots counted as securities: none.

## Changed-path ownership

| Changed path | Owning checks |
|---|---|
| `gv_portfolio_v0/operated_scenarios.py` | `test_operated.py`, `test_operated_25.py` |
| `gv_portfolio_v0/operated.py` | retained/new operated domain tests; book/execution/replay package |
| `gv_portfolio_v0/operated_storage.py` | retained/new persistence, tamper, link-escape, reopen tests |
| `views/gv_operated_portfolio_workspace.py` | retained/new AppTests |
| `operated_portfolio_app.py` | retained/new network-denied AppTests |
| `launch_operated_portfolio_25.py` | entrypoint import/forbidden-import test |
| `.github/workflows/gv-operated-portfolio.yml` | static trigger assertions and FS0/context authority package |
| authority/current-context documents | build-context, phase60/61 hygiene, FS0 authority tests |

## CI preflight

The operated workflow:

- triggers on `gv_portfolio_v0/**`, the shared view/app, both launchers, operated tests, FS0 tests, current authority surfaces, and the active phase brief;
- checks out `${{ github.event.pull_request.head.sha || github.sha }}`;
- asserts actual `HEAD` equals the expected SHA;
- asserts a clean checkout before setup;
- runs operated, FS0, and context packages on Windows and Linux;
- validates generated context;
- requires tracked bytes unchanged after tests.

No new dependency was added. Local environment receipt:

```text
Python 3.12.10
pytest 9.1.0
Streamlit 1.58.0
pip check: PASS
```

The hosted workflow continues to install the existing tracked dependency authority required by the combined operated and FS0 package. This phase does not authorize repository-wide dependency repair.

## Retained local test receipts

Destination: `C:\Users\Lenovo\AppData\Local\Temp\gv25_prefreeze_*.xml`.

| Receipt | Tests | Failures | Errors | Skips |
|---|---:|---:|---:|---:|
| `gv25_prefreeze_operated_core.xml` | 129 | 0 | 0 | 0 |
| `gv25_prefreeze_operated_substrates.xml` | 24 | 0 | 0 | 0 |
| `gv25_prefreeze_fs0_a1.xml` | 43 | 0 | 0 | 0 |
| `gv25_prefreeze_fs0_a2.xml` | 114 | 0 | 0 | 0 |
| `gv25_prefreeze_fs0_b1.xml` | 51 | 0 | 0 | 0 |
| `gv25_prefreeze_fs0_b2.xml` | 55 | 0 | 0 | 0 |
| `gv25_prefreeze_context.xml` | 33 | 0 | 0 | 0 |
| **Total** | **449** | **0** | **0** | **0** |

The attempted single-command combined gate returned DevSpace HTTP 502 without a test result. It is not counted as evidence. The same logical package was executed as bounded, externally retained runs.

## Base/candidate failset method

After candidate freeze:

1. pin base `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e` and exact candidate SHA;
2. prove interpreter, shell, PATH, Git, temp, commit, tree, and cleanliness before pytest;
3. run the same complete suite and environment against base and candidate;
4. retain JUnit/XML outside both checkouts;
5. normalize failing node IDs and classify inherited versus candidate-only failures;
6. require zero candidate-only failures;
7. discard any environment-invalid run before defect classification.

## Evidence retention after freeze

Local terminal evidence destination:

```text
%TEMP%\terminal-zero\gv-operated-portfolio-25-1\<candidate-sha>\
```

Hosted evidence destination:

```text
${{ runner.temp }}/gv-operated-portfolio-25-1/${EXPECTED_SHA}/
```

The checkout must remain clean; evidence must be uploaded from runner-temporary storage.

## Open custody blocker

The managed worktree creator could not create a new worktree because repository discovery traversed inaccessible and overlong legacy paths outside the clean checkout. Work proceeded in the already isolated, initially clean terminal worktree at exact base `2349e1b`; `main` and the terminal tag were not moved.

Current changes are uncommitted and the worktree still names the historical closure branch. Therefore:

- no phase candidate is frozen;
- no branch publication is authorized from the current identity;
- no exact-head CI or failset comparison can start;
- no terminal score or acceptance claim is permitted.

Correct next custody operation: attach the current bytes to dedicated branch `codex/gv-operated-portfolio-25-1`, then freeze one candidate only after diff review and checkpoint audit. Do not modify `main` or any terminal tag.
