# SAW — PIT-ALPHA-AUTHORITY-CUT-1 Candidate Publication

Date: 2026-08-05
Mode: `CLOSURE_REPORT`
RoundID: `ROUND-20260805-PIT-ALPHA-AUTHORITY-CUT-1`
ScopeID: `PIT_ALPHA_AUTHORITY_CUT_1_CANDIDATE_PUBLICATION`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: owner-approved authority-cut execution | Domains: Product, Repository Custody, Backend, Frontend/UI, Accounting/Replay, Preservation, Docs/Ops

## Scope

Prepare and validate one candidate branch containing C cleanup plus one P final-state authority transplant, remove the duplicate standalone operator route without compatibility, complete bounded preservation F, and authorize one candidate push while stopping before merge, tag, or main advancement.

## Checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Exact C cleanup | PASS | `a927451` deletes 50 blobs + 41 gitlinks; zero other paths |
| CHK-02 Final-state donor fidelity | PASS | 28 selected paths byte-identical; 7 intentional sole-product/boundary deltas; 0 unexpected mismatches |
| CHK-03 Sole product authority | PASS | `dashboard.py` / Command Center only; app, launchers, prospective workspace, and standalone AppTests absent |
| CHK-04 Local product proof | PASS | 97/97 dashboard/PIT tests |
| CHK-05 Context proof | PASS | 26/26 context tests; generation and validation PASS |
| CHK-06 Fresh-clone proof | PASS | independent short-path clone at `E:\Q`; 58 byte-equivalent P paths; 123/123 combined tests; status match |
| CHK-07 Preservation F | PASS | two named tars; 35 comparison rows; 41 receipt rows; mirrored evidence; `F_PASS=true` |
| CHK-08 Independent reviews | PASS | A/B/C focus reviews all PASS on exact hash manifest |
| CHK-09 Forbidden actions | PASS | no merge, tag, main advancement, broker, or live-capital action |

## Independent review evidence

- Reviewer A — Product/regression: PASS; review `7ec24994984f4559cac64f2d5b262b14ae86c2d9548bd52b1a9fd144d641fb94`; conversation identity `f228fdd5046f26b916571a7cf4a20fa7627e01296470f708c9cf5d9ba0e1aae6`.
- Reviewer B — Runtime/operations: PASS; review `89b6b56ca153cf77a163ab1e291a5d75a5066702eb0f61679b39121058f3ac86`; conversation identity `7aa9e690ff2cc4b25fc9f5b2ba32620deeca925d5a46de0ef20c4e5adf29a578`.
- Reviewer C — Data/reproducibility: PASS; review `a5b87fc42ad17d24edb26a7c0288fb35a97e7d006f7ba7bd1c5ba43a2bef1ca0`; conversation identity `12c573941966f3e9ce56651513d0e2a645cb955c5235df8adb69cfdd1bd742aa`.
- Ownership check: PASS — implementer session and all three fresh external review conversations are distinct.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Command Center initially hardcoded the operated module ID | Moved identity to `core.gv_pit.adapters.REAL_MU_OPERATED_MODULE_ID` | Implementer | RESOLVED |
| Medium | Donor retained a second launchable operator surface | Deleted app, launchers, prospective workspace, standalone AppTests, and positive workflow routes | Implementer | RESOLVED |
| Medium | Fresh clone under long managed path exceeded Windows path limits | Re-ran exact proof from short independent checkout `E:\Q` | Implementer | RESOLVED |
| Advisory | `websockets.legacy` emits a deprecation warning | Carry as dependency-maintenance follow-up; no current behavior failure | Future maintenance | OPEN, NON-BLOCKING |

## Preservation evidence

- `Quant_clickable_nav_apptest.tar`: SHA-256 `928cc55d36b296d733cab9e386b54e88c7b55bd8ba1f1db593ce2b87b5fc87b6`.
- `Quant_current_public_review.tar`: SHA-256 `5b0f2d49dd5597e16090398d2955e960df28f84b5684105c93247a4d88bb0446`.
- 35-row comparison report: SHA-256 `c02e387eb4cf884b957e3ce42f89e2c814ca967bf8d3b8745133a8265c1f4305`.
- 41-row gitlink receipt manifest: SHA-256 `758f509578470349f44305e4d7cf9d3c3171ea7fb6c3e421c85a75bbc721c822`.
- Primary and `.portfolio-custody-copy` evidence hashes match.

## Document Changes Showing

- `.github/workflows/gv-operated-portfolio.yml` — dashboard/PIT-only hosted proof — Reviewer B PASS.
- `core/gv_pit/*` — typed PIT, adapters, governance, read models — Reviewers A/C PASS.
- `gv_portfolio_v0/*` — deterministic entry/rotation/accounting/persistence/replay substrate — Reviewers A/B/C PASS.
- `views/command_center.py`, `views/page_registry.py`, `dashboard.py` — sole product path — Reviewers A/B PASS.
- focused tests — entry, rotation, reject-all, tamper, persistence, replay, context — Reviewers A/B/C PASS.
- current authority surfaces — C/P/F truth, score hold, source-authority next step — Reviewer A PASS.

## Scope split

in-scope: candidate cleanup, single final-state transplant, sole dashboard route, focused/fresh-clone proof, bounded preservation, candidate publication.

inherited out-of-scope: merge, tag, main advancement, cascade, providers, optimizer, historical-suite repair, broker, advice, alpha, realized-value claims, and Limited Live.

## Closure

ChecksTotal: 9
ChecksPassed: 9
ChecksFailed: 0
SAW Verdict: PASS
Open Risks: hosted branch CI remains post-push evidence; `websockets.legacy` deprecation is advisory only.
Next action: create P, push C+P once to `origin/codex/pit-alpha-authority-cut-1`, verify remote equality, and stop before merge.

ClosurePacket: RoundID=ROUND-20260805-PIT-ALPHA-AUTHORITY-CUT-1; ScopeID=PIT_ALPHA_AUTHORITY_CUT_1_CANDIDATE_PUBLICATION; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=hosted_branch_CI_pending_and_websockets_legacy_deprecation; NextAction=commit_and_push_C_plus_P_once_then_stop_before_merge
ClosureValidation: PASS
SAWBlockValidation: PASS
