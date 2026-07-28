# Impact Packet - Current

## Active Addendum — GV-ALPHA0-SHIP local candidate (2026-07-28)

- **Runtime boundary:** `core/gv_alpha0_ship_runtime.py`, `alpha_app.py`, `launch_alpha.py` now separate immutable packaged sample bytes from mutable user state.
- **Workflow:** fresh initialize → verified review → confirm paper `NO_POSITION` → atomic persistence → certified reopen.
- **Release surface:** deterministic allowlisted ZIP builder, extracted-package smoke, Windows/Linux run wrappers, onboarding, rollback, and hosted matrix/package parity updates.
- **Tests:** two focused shipment test modules plus existing Alpha product tests; native Windows combined result **38/38 PASS**, including actual Windows junction routing and tampered-package startup refusal.
- **P1 repair:** all packaged files are checked against `RELEASE_MANIFEST.json` before initialization; package/runtime/seed paths are canonicalized; junction/symlink escapes and runtime routes entering the bundle fail closed.
- **Cross-platform:** native Windows/Linux archive bytes match exactly; full local Linux runtime smoke unavailable because the OS Python lacks pip/venv, so hosted Linux remains open.
- **Authority unchanged:** score 39, observed 0, `CERTIFIED_MULTI_SOURCE_CASE_OPERABLE`, no alpha or decision-improvement claim.
- **Not performed:** commit/push, hosted CI, clean commit-bound artifact, clean-machine runtime smoke, pilot, tag, or release.

## Active Addendum — GV-ALPHA0-CLOSE complete on branch (2026-07-25)

- **Owned runtime:** `core/gv_v2_alpha0_case_close.py`, `views/gv_alpha0_case_workspace.py`, `alpha_app.py` / `launch_alpha.py`; source families one+two banked substrates.
- **Custody:** branch tip on `codex/gv-alpha0-rc2` (Commit A–C); base main `06ce68f`; published current decision CDR `889cc831fe405e5aad1f13225f06fe666036390defeff6652b39d0d656225376`.
- **Public authority:** default current decision is Alpha close certified paper **NO_POSITION** (`DECISION_V2_ALPHA0_CLOSE_MU_G_SUPPLY_1`).
- **Roadmap impact:** Alpha complete on branch; **merge pending**. Stage **CERTIFIED_MULTI_SOURCE_CASE_OPERABLE**. Immediate gate = merge Alpha. First post-merge product gate = one fresh real **ONE_CASE_DECISION_DELTA_OBSERVED** comparison (not custody/governance/provider phase).
- **Score/stage:** 39 / CERTIFIED_MULTI_SOURCE_CASE_OPERABLE / observed 0; no alpha claim.
- **Not performed:** merge to main; formal comparison; score uplift; live capital.

## Prior — family-two / B0B substrate (banked history)

Source family one (B0B) and source family two remain banked substrates under the closed Alpha vertical; not open gates.
