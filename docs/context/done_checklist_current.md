# Done Checklist — Current

Date: 2026-08-02
Phase: `GV-PROSPECTIVE-PAPER-BASELINE-1`
Status: `EXECUTABLE_REMOTE_CANDIDATE; DATE_REPAIR_PRESENT; HOSTED_CI_AND_REAL_EVIDENCE_SEAM_PENDING`
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
- [x] Three sequential test-injected episodes reconstruct through one append-only event/state projector; they remain regression coverage, not a forward milestone.
- [x] Every episode uses at most two operator actions: preview and confirm/reject.
- [x] Fresh-process reopen reconstructs evidence, reviews, observations, snapshots, execution, certification, rejection history, and book.
- [x] Accounting residual remains `0`.

## Validation

- [x] Historical broader receipts remain bound to `9c7e75a`: retained operated/25/App `23/23`, scale repair `13/13`, shared accounting/allocation/execution/replay/strategy/vertical `104/104`, and historical bounded/scale/universe/challenger `24/24`.
- [x] Executable candidate `147397f`, tree `a43a6a8`, is remote-equal and repairs the September bootstrap defect.
- [x] Current-tip prospective subset is reported `15/15 PASS` (`12` core plus `3` UI); no broader current-tip rerun is claimed.
- [ ] Exact-SHA Windows/Linux hosted CI.
- [ ] One fresh-home synthetic no-change smoke with preview-byte immutability, episode count `1`, operator actions `2`, unchanged economics/book hash, exact source/rationale reconstruction, and fresh-process reopen.
- [ ] Bounded MU/NVDA reconciliation with explicit corroboration, contradiction, disposition, and missing discriminator.
- [ ] One real MU identity plus classified cash reaches deterministic portfolio outcome, preview/confirmation, append-only persistence, and fresh-process exact replay.

## Product disposition

- [x] Software capability gap is implemented.
- [x] Test-injected runtime values and synthetic operator entry are explicitly classified as capability/usability proof, not market-facing prospective evidence.
- [x] Three synthetic human episodes are withdrawn as the forward milestone.
- [x] The forward milestone is real evidence entering a real instrument decision and surviving the certified portfolio/replay path.
- [x] Accepted score remains `62/100`.
- [x] Australian legal review is removed as a paper Challenger blocker and preserved before broker credentials, automated submission, client assets, advice activity, or real capital.
- [x] Universe custody is removed as a mandatory predecessor to paper Challenger comparison.
- [x] Limited Live remains closed.

## Stop condition

Do not claim market-facing prospective evidence or score uplift from automated fixtures or a synthetic operator smoke. Use remote-equal executable candidate `147397f`; collect hosted proof before publication; keep the accepted score at `62/100`; and do not open the replacement shadow Challenger until the real MU evidence-to-portfolio-and-replay seam works.
