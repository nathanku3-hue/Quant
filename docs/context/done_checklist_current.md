# Done Checklist — Current

## Authority and scope

- [x] Owner issued exact authorization token `approve next phase`.
- [x] `ACTIVE_BRIEF` selects `GV-OPERATED-PORTFOLIO-25-1`.
- [x] Base is terminal `main` at `2349e1bd91d9b4036f3956c52ce7bbf66a9c2c1e`.
- [x] Ten-security candidate, closure, and terminal tag remain immutable custody.
- [x] Limited Live, providers, optimizer, broker, Universe, and Challenger remain closed.
- [ ] First candidate frozen on a dedicated phase branch.

## Architecture

- [x] One operated engine serves retained 10-security and new 25-security scenarios.
- [x] One persistence implementation serves both scenarios.
- [x] One application and one view stack serve both scenarios.
- [x] Scenario definitions are declarative.
- [x] Genericization was not accepted or frozen independently.
- [x] No parallel domain engine, storage implementation, schema family, or view stack was created.

## Product capability

- [x] Exactly 25 distinct permanent identities in one portfolio.
- [x] At least two meaningful clusters; fixture exercises five.
- [x] Every identity appears exactly once in capital competition.
- [x] Evidence and thesis state remain instrument-owned.
- [x] Cross-instrument rebinding fails closed.
- [x] Multiple positions are funded and residual cash remains classified.
- [x] One explicit no-change cycle preserves economics.
- [x] At least one SELL/REDUCE and one BUY/FUND occur from target deltas.
- [x] Orders, fills, costs, positions, cash, NAV, and zero residual reconcile.
- [x] Replay, certification history, correction lineage, persistence, and reopen pass locally.
- [x] Summary-first and exceptions-first UI completes within four required actions.
- [x] Retained ten-security full flow remains green.

## Local verification

- [x] Focused shared 10/25 domain and AppTest: `23/23 PASS`.
- [x] Complete `tests/gv_portfolio_v0` passed in bounded groups.
- [x] Complete `tests/gv_fs0_product` passed in bounded groups.
- [x] Context/authority tests passed before regenerated current-context validation.
- [x] `pip check` receipt retained for the current pre-freeze environment.
- [x] Generated current context rebuilt and validated after authority reconciliation.
- [x] Broad candidate-local logical gate retained as seven external JUnit receipts: `449/449 PASS`.

## Pre-freeze completeness

- [x] Changed-path to focused-test ownership recorded.
- [x] CI triggers cover every changed authoritative path.
- [x] Exact-head checkout contract reviewed and retained.
- [x] Dependency coverage recorded.
- [x] Base/candidate failset method recorded.
- [x] Evidence-retention destination recorded outside the candidate checkout.

## Terminal verification

- [ ] One candidate SHA frozen.
- [ ] Exact-head Windows CI passes.
- [ ] Exact-head Linux CI passes.
- [ ] Controlled base/candidate full-suite comparison has zero candidate-only failures.
- [ ] Reviewer A passes product result, bounded workload, and retained behavior.
- [ ] Reviewer B passes accounting, replay, certification, and correction.
- [ ] Reviewer C passes custody, restart, reproducibility, and failset identity.
- [ ] Documentation-only terminal closure preserves the tested executable tree.
- [ ] Accepted score reconsidered only after all terminal gates pass.
