# SAW — PREBREAKOUT W5 Trial-1 M0 Candidate Freeze — 2026-08-10

Mode: `CLOSURE_REPORT_NON_PHASE_END`

RoundID: `PREBREAKOUT_W5_TRIAL1_M0_20260810`
ScopeID: `PREBREAKOUT-W5-TRIAL1-M0-UNCHARGED-CANDIDATE`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: explicit-user-W5-scope | Domains: Quant Research, Data/PIT Custody, Research Governance

## Scope

Close the generic W5 mechanics round and prepare the next result-bearing PREBREAKOUT candidate as deterministic market-only Trial-1 M0 **without running development and without charging W2 Trial/Search budget before an exact real W3/W4-bound source manifest exists**.

Owned W5 files changed/created in this round:

- `research/prebreakout_discovery_v1/trial1_m0.py`
- `research/prebreakout_discovery_v1/__init__.py`
- `tests/prebreakout_discovery_v1/test_trial1_m0.py`
- `docs/phase_brief/prebreakout_w5_trial1_m0_20260810.md`
- `docs/phase_brief/prebreakout_w5_walkforward_20260810.md` status-only mechanics closure marker
- `docs/context/e2e_evidence/prebreakout_w5_trial1_m0_candidate_20260810.json`
- W5 lines in `docs/context/done_checklist_current.md`, `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`
- this SAW report

No provider/network access, development-label inspection, development run, W2 `TRIAL_OPEN`, Trial/Search ledger append, W6 lockbox access, prospective clock start, A2 query, Parent/Child mutation, VSB retune, broker order, capital action, commit, push, or publication occurred.

## Implementer task/evidence map

| TaskID | Task | Artifact | Acceptance check | Status | EvidenceID |
| --- | --- | --- | --- | --- | --- |
| TSK-01 | Freeze Trial-1 deterministic market-only scientific rule | `trial1_m0.py` | exact fixed close/return/volume formulas; zero fit/calibration; post-breakout cannot trigger; no named smoke branch | PASS | EVD-01,EVD-03 |
| TSK-02 | Freeze Trial-1 temporal split and cross-sectional holdout | `trial1_m0.py`, W5 mechanics | expanding 126; 20-session embargo; 4×20 OOS; deterministic CIQSEC mod-5 holdout; insufficient coverage blocks | PASS | EVD-01,EVD-03 |
| TSK-03 | Freeze control and right-tail/lead objective | `trial1_m0.py`, phase brief | full date-local ordinary control; constant W4 stratum; lift→TTFLD objective; CAGR/Sharpe non-primary | PASS | EVD-01,EVD-03 |
| TSK-04 | Prevent premature Trial-1 charge/result access | source-manifest verifier + preparation seam | exact W3/W4 source manifest required; label visibility hashed/uninspected; W6 absent; preparation never appends W2 ledger | PASS | EVD-01,EVD-02,EVD-03 |
| TSK-05 | Reconcile W5 docs/current truth without widening authority | candidate receipt + brief + current-truth/docs | 0/8, no result, reopen only on real W3/W4 source manifest then exact W2 TRIAL_OPEN | PASS | EVD-04 |
| TSK-06 | Obtain mandatory independent SAW role coverage | Reviewer A/B/C | distinct strategy/runtime/data reviewers required by repo SAW policy | BLOCK | EVD-05 |

TaskEvidenceMap: TSK-01:EVD-01,EVD-03;TSK-02:EVD-01,EVD-03;TSK-03:EVD-01,EVD-03;TSK-04:EVD-01,EVD-02,EVD-03;TSK-05:EVD-04;TSK-06:EVD-05
EvidenceRows: EVD-01|PREBREAKOUT_W5_TRIAL1_M0_20260810|2026-08-10T15:10:38Z;EVD-02|PREBREAKOUT_W5_TRIAL1_M0_20260810|2026-08-10T15:10:38Z;EVD-03|PREBREAKOUT_W5_TRIAL1_M0_20260810|2026-08-10T15:19:39Z;EVD-04|PREBREAKOUT_W5_TRIAL1_M0_20260810|2026-08-10T15:10:38Z;EVD-05|PREBREAKOUT_W5_TRIAL1_M0_20260810|2026-08-10T15:19:39Z
EvidenceValidation: PASS

Rollback note: Trial-1 is uncharged and has produced no result/data/ledger/capital state. A rollback is limited to the W5 candidate code/tests/docs/receipt; no W1/W2/W3/W4/W6/W7/W8/W9/W10 authority artifact requires reversal.

## Acceptance checks

| Check | Result | Evidence |
| --- | --- | --- |
| CHK-01 — Trial-1 remains uncharged before exact source manifest | PASS | persistent repository scan found no `PREBREAKOUT_TRIAL_1_M0` entry and no PREBREAKOUT/trial JSONL under `data`; candidate receipt says `material_trials_consumed=0`, `trial_open_appended=false` |
| CHK-02 — Deterministic pre-fit market-only rule is frozen | PASS | close/1d-return/volume exact input schema; fixed 20-high proximity + 20/60 vol compression + 5/15 volume pressure; zero fitted parameters/calibration; post-breakout score=0 |
| CHK-03 — No MU/SNDK/ticker/sector/fundamental special case | PASS | forbidden-code scan returned zero matches for named smoke literals, yfinance, submit order, PERMNO, sector map and selected fundamental tokens; extra ticker column test fails closed |
| CHK-04 — Exact temporal split/holdout frozen before labels | PASS | expanding min train 126; embargo 20; four OOS folds×20; minimum spine 226; deterministic CIQSEC hash mod5 remainder0; no silent resplit |
| CHK-05 — Control/objective are right-tail/lead, not CAGR/Sharpe | PASS | full same-session W3-eligible ordinary-control denominator + constant `ALL_W3_ELIGIBLE` W4 stratum; primary comparison=20d recall lift then effective TTFLD; CAGR/Sharpe primary flags false |
| CHK-06 — Exact W3/W4 source gate precedes Trial-1 preparation | PASS | source manifest binds W2/W3 law, market payload, W3 PIT bundle, exact W4 control hash, W4 development-label/episode custody, spine/receipts; label visibility must be `HASHED_NOT_INSPECTED`; holdout tuning forbidden; W6 false |
| CHK-07 — Predictions/holdout/zero-weight/W6 W5 mechanics remain sealed | PASS | W5 package keeps prediction-before-development-OOS-label join; holdout and zero-weight trace labels excluded from tuning; W6 authority absent |
| CHK-08 — Final current-byte deterministic validation | PASS | Trial-1 `7/7`; PREBREAKOUT discovery `26/26`; adjacent W3+W4+W6 `43/43`; selected compile PASS; candidate JSON parse PASS |
| CHK-09 — Independent scientific PRODUCT review | PASS | review `a11bbaff3ca21afcbb6eefe70fe3958fe6ecffdb3b845e571c64cf796e5e60d3`: PASS; advisory only that review is manifest-level |
| CHK-10 — Independent custody/leakage PRODUCT review | PASS | review `bba2cbfb8dc5df670ae4276ad7b1578a98d1024666c95fa5f16d65f8da508e82`: PASS; advisory only that review is manifest-level |
| CHK-11 — Independent engineering/data-integrity PRODUCT review | PASS | review `4cbdc7b03c59de3d190a9176b40f8ebdfc19b2766eb59e7489bf3d287e5274e5`: PASS; advisory only that underlying test logs are not directly exposed to PRODUCT reviewer |
| CHK-12 — Distinct mandatory SAW Reviewer A/B/C roles | FAIL / UNAVAILABLE | current DevSpace review surface exposes one independent `PRODUCT` role only. Three independent PRODUCT conversations passed, but they are not relabeled as Reviewer A/B/C |

ChecksTotal: 12
ChecksPassed: 11
ChecksFailed: 1

## Frozen candidate custody

```text
trial_id                         = PREBREAKOUT_TRIAL_1_M0
implementation_id                = PREBREAKOUT_TRIAL1_M0_MARKET_EARLY_WARNING_V1
uncharged_declaration_sha256     = 02b0e07445bb91ab7fd4c192abbd26b112facf75cf4923d4ddd8778ea5a062c1
walk_forward_spec_sha256         = 7a0b77fbb95fc39a86723fd3f79d69d6fd88c12f73db65fd3224ff2723fcc9af
w4_control_definition_sha256     = 144f3c08ba5ff576cd1d4a702129893f9b08f9b58b4d4a6e21ad385a7d7c44ba
code_bundle_sha256               = 92f51a098f2420fd5d76b7307d0aad75a76d0cf10a81934aa48a15a20f43b2bd
candidate_receipt_sha256         = d333bd284f6affddebe63b5df2e26439d653a79189f88fd33c9facbace994d79
trial_open_appended              = false
material_trials_consumed         = 0/8
development_labels_inspected     = false
development_run_performed        = false
w6_lockbox_accessed              = false
financial_alpha_evidence         = 0
capital_authority                = NONE
```

Candidate code bundle members:

- `research/prebreakout_discovery_v1/trial1_m0.py` — `2473cd5266b73dda8fe62c9e603959291db70e6a2a4ff30a7ca775ad0e9280d8`
- `research/prebreakout_discovery_v1/contracts.py` — `0d736c25496f3263d56a6e903273f0535ee3623992f57e6cb373529d413c1106`
- `research/prebreakout_discovery_v1/walk_forward.py` — `32b7707bd073daada11dd52a16e5076c22b17c7a0607b9674ff992df298dad7f`
- `research/prebreakout_discovery_v1/preregistration.py` — `3df15dce6e0c14ccf5e8ab65ecf66cadd212f28bc134f5c50ec7790ea9583214`

## Reviewer passes

| Pass | Role | Status | Evidence |
| --- | --- | --- | --- |
| Implementer | current W5 execution agent | PASS | candidate code/tests/docs/receipt complete; no forbidden result-bearing action taken |
| Reviewer A | strategy correctness / regression risk | UNAVAILABLE AS DISTINCT ROLE | no A-specific reviewer tool is exposed |
| Reviewer B | runtime / operational resilience | UNAVAILABLE AS DISTINCT ROLE | no B-specific reviewer tool is exposed |
| Reviewer C | data integrity / performance path | UNAVAILABLE AS DISTINCT ROLE | no C-specific reviewer tool is exposed |
| Supplemental independent review 1 | PRODUCT — scientific packet | PASS | `a11bbaff3...60d3`; no blocking/material finding |
| Supplemental independent review 2 | PRODUCT — custody/leakage packet | PASS | `bba2cbfb...8e82`; no blocking/material finding |
| Supplemental independent review 3 | PRODUCT — engineering/data packet | PASS | `4cbdc7b0...274e5`; no blocking/material finding |

Ownership check: the three PRODUCT reviews are independent fresh conversations and are independent from the implementer, but the role policy is PRODUCT for all three. They are supplemental evidence and are not mislabeled as mandatory Reviewer A/B/C.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High (governance closure only) | Full SAW PASS cannot be claimed under repo policy without distinct Reviewer A/B/C coverage | Run role-specific strategy/runtime/data reviews against these same frozen bytes when the required reviewer surface is available, or obtain explicit owner review-risk acceptance | Review tooling / Owner | OPEN / BLOCKING SAW PASS |
| Advisory | PRODUCT reviews inspect exact manifests/hashes and reported validation, not raw repository code/test logs | Retain local deterministic test evidence and repeat final review if a future reviewer surface can inspect repository bytes directly | Review tooling | OPEN / NON-BLOCKING PRODUCT |
| Expected gate | Exact real W3/W4 source manifest does not yet exist | Keep Trial-1 uncharged and labels uninspected. Reopen only after real source/data custody is ready | W3/W4→W5 join | OPEN / INTENTIONAL |

No in-scope Critical/High scientific, runtime, data-integrity, or custody defect was found by local validation or the three independent PRODUCT reviews. The open High item is reviewer-role coverage only.

## Scope split summary

In scope: Trial-1 deterministic M0 definition, scientific hashes, expanding walk-forward split, deterministic holdout, fixed control/objective, exact pre-charge source-manifest verifier, no-auto-charge preparation seam, focused/integrated tests, candidate receipt and W5 current-truth/docs.

Inherited/out-of-scope and untouched: W1 Clock #1 outcomes/custody; W2 scientific contract mutation; W3 real provider capture; W4 real Atlas run/label open; W6 lockbox/evaluator result; W7 VSB confirmation; W8 Sector Rotation; W9 CRV1; W10 replication/PAPER; A2 re-query; Parent/Child; broker/capital actions.

## Document Changes Showing

| Path group | What changed | Reviewer status |
| --- | --- | --- |
| `trial1_m0.py` + package export | frozen uncharged deterministic M0, exact source gate, zero-fit scorer | local PASS + 3 supplemental PRODUCT PASS |
| Trial-1 tests | formula, split, holdout, source gate, no-charge, no-special-case regressions | `7/7 PASS` |
| W5 mechanics regression | existing walk-forward/search custody preserved | PREBREAKOUT discovery `26/26 PASS` |
| W3/W4/W6 adjacency | upstream PIT/Atlas/untouched boundaries preserved | `43/43 PASS` |
| Trial-1 phase brief + receipt | exact hashes, 0/8 state, reopen gate, no outcome authority | JSON parse/hash PASS; supplemental PRODUCT PASS |
| done/notes/decision/lessons | current truth and formula/decision/guardrail synchronized | scope review PASS |

## Open Risks

Open Risks: distinct mandatory Reviewer A/B/C roles are unavailable; exact real W3/W4-bound source manifest is intentionally absent; Trial-1 must remain uncharged and labels uninspected until that source gate is true.

## Next action

Operational next action: **none inside W5 now.** Reopen only when the exact real W3/W4-bound source manifest exists. Then reverify the frozen code bundle, call the separate W2 `TRIAL_OPEN` before any result inspection (consuming `1/8`), freeze OOS predictions before development-label joins, and run Trial-1 with W6 still closed.

Governance next action: obtain distinct Reviewer A/B/C coverage against the unchanged candidate bytes before claiming full SAW PASS.

SAW Verdict: BLOCK
ClosurePacket: RoundID=PREBREAKOUT_W5_TRIAL1_M0_20260810; ScopeID=PREBREAKOUT-W5-TRIAL1-M0-UNCHARGED-CANDIDATE; ChecksTotal=12; ChecksPassed=11; ChecksFailed=1; Verdict=BLOCK; OpenRisks=Distinct_Reviewer_A_B_C_roles_unavailable_and_real_W3_W4_source_manifest_intentionally_absent; NextAction=Keep_Trial1_uncharged_until_exact_W3_W4_source_manifest_then_append_exact_W2_TRIAL_OPEN_before_result_inspection
ClosureValidation: PASS
SAWBlockValidation: PASS
