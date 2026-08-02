# Done Checklist — Current

Date: 2026-08-02
Phase: `GV-PROSPECTIVE-PAPER-BASELINE-1`
Status: `IMPLEMENTED_CANDIDATE; LOCAL_GATES_PASS; REAL_PROSPECTIVE_EVIDENCE_PENDING`
Accepted score: `62/100`
Limited Live: `CLOSED; NOT_AUTHORIZED`

## Scope and custody

- [x] Accepted 10-security and 25-security terminal identities remain immutable.
- [x] Repair base `5687a2c` remains the exact implementation base.
- [x] Prospective profile derives from the accepted 25-security catalogue without copying its instrument catalogue.
- [x] One engine, storage implementation, schema family, app entry point, book reducer, replay path, and certification path remain in use.
- [x] No provider, optimizer, broker, legal-review dependency, client asset, or live-capital path was added.

## Runtime authority

- [x] Operator supplies observation content, locator, observed-at, instrument ownership, explicit review proposals, and rationale at runtime.
- [x] Observation content is not embedded in scenario code.
- [x] Preview is mutation-free and non-authoritative.
- [x] Outcome, score, target quantity, and thesis changes become authority only after deterministic validation and explicit confirmation.
- [x] Per-security outcomes are `ADMIT`, `REJECT`, or `ABSTAIN`.
- [x] `CASH` remains a portfolio-level capital candidate.
- [x] Non-`ADMIT` reviews require target quantity `0`.
- [x] Unknown instruments, duplicate ownership updates, stale timestamps, invalid outcomes, invalid quantities, and one-sided transitions fail closed.

## Functional slices

- [x] Slice A: runtime no-change episode confirms append-only and preserves economics.
- [x] Slice B: runtime observation produces a deterministic SELL/REDUCE plus BUY/FUND transition.
- [x] Slice C: explicit rejection appends custody and certification without admitting evidence or mutating authoritative state.
- [x] Three sequential test-injected episodes reconstruct through one append-only event/state projector.
- [x] Every episode uses at most two operator actions: preview and confirm/reject.
- [x] Fresh-process reopen reconstructs evidence, reviews, observations, snapshots, execution, certification, rejection history, and book.
- [x] Accounting residual remains `0`.

## Validation

- [x] Prospective core tests: `11/11 PASS`.
- [x] Prospective UI tests: `3/3 PASS`.
- [x] Retained operated/25/App tests: `23/23 PASS`.
- [x] Scale repair tests: `13/13 PASS`.
- [x] Shared accounting/allocation/execution/replay/strategy/vertical tests: `104/104 PASS`.
- [x] Historical bounded/scale/universe/challenger tests: `24/24 PASS`.
- [ ] FS0 authority and generated-context validation after documentation synchronization.
- [ ] Exact candidate commit and remote branch publication.
- [ ] Exact-SHA Windows/Linux hosted CI.
- [ ] Three genuine operator-supplied prospective episodes.

## Product disposition

- [x] Software capability gap is implemented.
- [x] Test-injected runtime values are explicitly classified as capability proof, not prospective evidence.
- [x] Accepted score remains `62/100`.
- [x] Australian legal review is removed as a paper Challenger blocker and preserved before broker credentials, automated submission, client assets, advice activity, or real capital.
- [x] Universe custody is removed as a mandatory predecessor to paper Challenger comparison.
- [x] Limited Live remains closed.

## Stop condition

Do not claim prospective product acceptance or score uplift from automated fixtures. Freeze and push the implementation candidate only after FS0/context validation and exact diff review. Then collect three genuine operator-supplied episodes before opening the real shadow Challenger or changing the score.
