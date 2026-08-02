# Done Checklist — Current

Date: 2026-08-02
Phase: `GV-REAL-EVIDENCE-MU-PORTFOLIO-1`
Status: `HOSTED_GREEN_D84C675; HUMAN_SMOKE_AND_INDEPENDENT_REVIEW_PENDING`
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
- [x] Executable candidate `147397f`, tree `a43a6a8`, repairs the September bootstrap defect.
- [x] Documentation-only authority synchronization `dc6b022`, tree `a9735c2`, preserves `147397f` as date-repair authority and keeps historical broader receipts bound to `9c7e75a`; its hosted tests pass, but generated-context validation is stale.
- [x] Exact-SHA `147397f` Windows/Linux proof passes in runs `30740333853` and `30748842695`.
- [x] Real-evidence candidate `ae615a2`, tree `4bc827a`, is immutable and pushed; hosted product/tests pass in run `30750230766`.
- [x] Generated-context closure `d84c675`, tree `63206de`, is fully green on Ubuntu and Windows in run `30750709296`, including tracked-byte immutability.
- [x] One machine-executed fresh-home synthetic no-change smoke with preview-byte immutability, episode count `1`, authorization actions `2`, unchanged economics/book hash, exact source/rationale reconstruction, and fresh-process reopen.
- [ ] One genuine human-operated synthetic smoke episode; no machine or assistant execution may satisfy this item.
- [x] Bounded MU/NVDA reconciliation with `PARTIAL_INDIRECT` corroboration, no direct contradiction, `HOLD_FOR_EVIDENCE`, `NO_POSITION`, and one explicit missing discriminator.
- [x] Reconciliation hash `89cc062783ae367c1bf259cfb7b355e0812ca162995b7ce05743a39e99592017` is bound to real MU identity `SEC_CIK:0000723125:NASDAQ:MU:COMMON_STOCK`.
- [x] One real MU identity plus classified cash reaches deterministic `ABSTAIN/NO_POSITION`, preview/confirmation, append-only persistence, and fresh-process exact replay.
- [x] Real MU economics: NAV `11000`, positions `0`, orders `0`, fills `0`, residual `0`, stable book hash `074a47c7cdb7755a34c1d257e4e2ff99552cf9419033828b304cc5cf16016c22`.
- [x] Exact reconstructed workspace hash: `59f75a10875add2dcd8d4018f6c3952955a33da4c20da56e9769b3df1abec980`; certification `CRT_c8e44e6fc1c18de406eefd5f076b4bdc2a5e14d2424306a0a2df456b80153ada`.
- [x] Targeted real/reconciliation/prospective/UI tests `24/24`; full operated-portfolio tests `185/185`; full FS0 tests `268/268`; context/hygiene tests `33/33`; compile and diff check pass.
- [x] New immutable functional candidate `ae615a2`.
- [ ] Independent terminal review.

## Product disposition

- [x] Software capability gap is implemented.
- [x] Test-injected runtime values and synthetic operator entry are explicitly classified as capability/usability proof, not market-facing prospective evidence.
- [x] Three synthetic human episodes are withdrawn as the forward milestone.
- [x] The forward milestone is real evidence entering a real instrument decision and surviving the certified portfolio/replay path.
- [x] Accepted score remains `62/100`.
- [x] Nonbinding expected score is updated to `66–68/100` after completion of the real-evidence seam; no accepted uplift before genuine human operation and independent review.
- [x] Australian legal review is removed as a paper Challenger blocker and preserved before broker credentials, automated submission, client assets, advice activity, or real capital.
- [x] Universe custody is removed as a mandatory predecessor to paper Challenger comparison.
- [x] Limited Live remains closed.

## Stop condition

Do not claim accepted score uplift from automated fixtures, machine-executed smoke, or hosted-green bytes alone. The real MU evidence-to-portfolio-and-replay seam is immutable at `ae615a2` and hosted-green through `d84c675`; the next boundary is one genuine human smoke and independent review. Keep the accepted score at `62/100`, the nonbinding expectation at `66–68/100`, old Challenger compatibility prohibited, and Limited Live closed.
