# Done Checklist — Current

## Repository custody

- [x] Dirty root checkout identified and left untouched.
- [x] Repair worktree starts from exact remote-equal base `b3d5092`.
- [x] S2 banked locally as isolated commit `92f587d`.
- [x] S3 banked locally as isolated commit `3040a77`.
- [x] S4 banked locally as isolated commit `1f11c0c`.
- [x] Terminal integration commit banked locally.
- [ ] Terminal branch pushed and remote-equal.

## Functional integration

- [x] S2 ignores non-economic `PORTFOLIO_TRANSITION_PLANNED` while preserving strict economic reduction.
- [x] S3 canonical thesis shape replaces the stale product-only `state` field.
- [x] S3 decision snapshot is the sole authority for reviews, cash outcome, competition, and selection.
- [x] S4 emits and validates aim-confirmation, transition, order, and fill lineage.
- [x] `vertical.py` contains no duplicate reducer, strategy validator, or order/fill constructor.
- [x] Certification consumes `build_portfolio_book` and requires explicit costs, reconciled NAV, zero unexplained residual, and valid execution lineage.
- [x] Persisted workspace schema bumped to `gv_portfolio_v0_workspace_v2`.
- [x] Product review state is derived at render time rather than persisted as strategy truth.

## Verification

- [x] Python 3.12.10, pytest 9.0.2, Streamlit 1.54.0 confirmed.
- [x] Portfolio slice: 82/82 PASS.
- [x] Frozen GV-FS0 protocol set: 150/150 PASS.
- [x] Legacy product suite executed read-only: 259/263 PASS.
- [x] Four legacy product failures classified as frozen authority-document drift outside this slice.
- [ ] Full repository suite PASS; blocked at collection by undeclared/incomplete environment dependencies.
- [ ] Independent Reviewer A/B/C PASS against one terminal SHA.

## Scope and claims

- [x] Product and Replay remained read-only during shared integration.
- [x] No provider, optimizer, broker, alpha, score-uplift, or live-capital work added.
- [x] Canonical shipped score remains 39/100; observed comparisons remain 0.
- [ ] Phase accepted and shipped.
