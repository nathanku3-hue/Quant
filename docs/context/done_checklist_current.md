# Done Checklist — GV-OPERATED-ROTATION-1

Date: 2026-08-05
Status: `DONE — SEALED VALIDATION PASS; PUBLICATION AUTHORIZED`
Canonical brief: `docs/phase_brief/gv-operated-rotation-1-brief.md`

## Product path

- [x] Episode-one MU authority remains the starting book.
- [x] One governed MERID companion is derived without widening the scenario registry.
- [x] Default Command Center displays and binds the eligible `GV_REAL_MU_OPERATED` proposal.
- [x] Rotation request binds full PIT identity, book hash, certification ID, event count, and two market observations.
- [x] Preview requires one source reduction and one non-zero companion funding target.
- [x] Preview produces complete-fill SELL then BUY legs.
- [x] Shared preview/confirm/reject UI path is reused for entry and rotation.
- [x] Confirmation uses existing persistence, certification, and replay authorities.
- [x] Reject-all preserves economics and does not add the companion.
- [x] Stale/tampered proposal bindings and buy-only top-ups fail closed.

## Operated result

- [x] Episode one remains MU `7 @ 101.25`, cost `2`, residual `0`.
- [x] Rotation target is MU `4`, MERID `5`.
- [x] Transition legs are SELL MU `3`, BUY MERID `5`.
- [x] Existing fee path applies to both fills.
- [x] Confirmed unexplained residual is `0`.
- [x] Episode count and certification lineage depth are both `2` after confirmation.
- [x] Separate-process reopen is byte-identical to persisted authority.

## Automated evidence

- [x] Mutation-free proposal-binding core test.
- [x] Confirmation, persistence, certification, reconstruction, and separate-process replay test.
- [x] Reject-all preservation test.
- [x] Stale binding, buy-only, and tampered proposal negative tests.
- [x] Default Command Center AppTest for displayed proposal → preview → confirm → reopened MU/MERID book.
- [x] Legacy post-entry one-update request retains `PROSPECTIVE_TRANSITION_SELL_REQUIRED` behavior.
- [x] Sealed exact validation passed all 31 declared tests.

## Publication

- [x] Retained native task outcome is `DONE`.
- [ ] Exact authorized path set committed and pushed to `origin/codex/gv-operated-rotation-1`.

## Holds

- [x] No provider-quality claim.
- [x] No strategy-generated-target claim.
- [x] No sizing-quality or alpha claim.
- [x] No realized-value claim.
- [x] No broker or live-capital authority.
- [x] Accepted score remains canonical `62/100`; `69–71/100` is a non-canonical post-PASS assessment only.
