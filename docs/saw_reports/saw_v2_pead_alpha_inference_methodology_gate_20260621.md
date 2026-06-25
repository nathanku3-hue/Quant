# SAW Report - V2 PEAD Alpha Inference Methodology Gate

Mode: `CLOSURE_REPORT`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: explicit-user-go-M1 | Domains: quantitative-research,econometrics,data-integrity,docs-ops

RoundID: `ROUND-20260621-V2-PEAD-ALPHA-INFERENCE-METHODOLOGY-GATE`
ScopeID: `V2_PEAD_CALENDAR_TIME_INFERENCE_METHOD_CONTRACT`

Ship-Fast Decision Gate: the single decision was whether M1A can terminally
approve a future PEAD formal-inference contract. It cannot close as PASS yet:
the calendar-time contract is selected and locally reconciled, but final
independent Reviewer C could not rerun after the corrected count contract due
subagent usage limits.

## Scope and Ownership

In-scope: select one formal-inference methodology for future M1B, document the
formation/overlap/missingness/HAC/bootstrap/evidence contract, preserve
quarterly as descriptive-only, validate primary-source support, and reconcile
current truth surfaces.

Forbidden scope: estimator implementation, Python/test edits, provider access,
D1/D2B/D3 artifact mutation, locked validation JSON mutation, dashboard alpha
verdicts, ranking/scoring, alerts, recommendations, broker/order paths,
staging, and commit.

Owned files changed or produced:

- `docs/phase_brief/v2-pead-alpha-inference-methodology-gate.md`
- `docs/research/pead_inference_methodology_claims_20260621.json`
- `docs/research/fama_1998_market_efficiency_long_term_returns.pdf`
- `docs/research/fama_1998_market_efficiency_long_term_returns.txt`
- `docs/research/researches.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/*_current.md`
- `docs/context/current_context.md`
- `docs/context/current_context.json`
- `docs/saw_reports/saw_v2_pead_alpha_inference_methodology_gate_20260621.md`

## Acceptance Checks

| Check | Acceptance condition | Result |
|---|---|---|
| CHK-01 | Scope remains M1A methodology only; no M1B runtime/test/provider/data/dashboard/staging/commit action. | PASS |
| CHK-02 | Exactly one primary method is selected and quarterly remains descriptive-only. | PASS |
| CHK-03 | Formation, overlap, missingness, HAC(59), bootstrap, claim boundary, and future M1B allowlist are explicit. | PASS |
| CHK-04 | Primary-source research support is present and claim validation passes. | PASS |
| CHK-05 | Reviewer A strategy/methodology recheck passes after literature, overlap, bootstrap, and HAC fixes. | PASS |
| CHK-06 | Reviewer B schema/ops recheck passes after allowlist, evidence path, atomicity, rollback, and protected-JSON fixes. | PASS |
| CHK-07 | Parent-side corrected count check records exact row semantics for null dates and missingness. | PASS |
| CHK-08 | Focused existing PEAD regression passes. | PASS |
| CHK-09 | Current truth surfaces are reconciled to PARTIAL/BLOCK status and no alpha/product action is authorized. | PASS |
| CHK-10 | Final independent Reviewer C recheck after the count correction is available. | FAIL |

ChecksTotal: 10
ChecksPassed: 9
ChecksFailed: 1

## Evidence

| EvidenceID | Evidence | Result | Notes |
|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m pytest tests\test_pead_event_study.py tests\test_pead_real_data_validation.py tests\test_pead_validation_evidence.py -q` | PASS | 37 passed. |
| EVD-02 | `.venv\Scripts\python .codex/skills/_shared/scripts/validate_research_claims.py --claims-json docs/research/pead_inference_methodology_claims_20260621.json` | PASS | `VALID: claims_total=2 claims_cited=2`. |
| EVD-03 | Fama (1998) local PDF and text extraction | PASS | PDF SHA256 `1be1c965437bb3dcea46056e45d1c744082d75a26205c8274b8e259164169184`; journal page 295 / PDF page 13 supports rolling calendar-time portfolios for cross-event correlation. |
| EVD-04 | Parent-side corrected feasibility/count command | PASS | 19,812 null-`return_date` rows excluded; ambiguity cells 0; expected rows 226,772; missing rows 1,519; Q1 `845 / 96,310`; Q5 `674 / 130,462`; sessions 2,539; first 2016-02-01; last 2026-03-06; internal gaps 0; medians Q1 38, Q5 51. |
| EVD-05 | Protected validation JSON hash check | PASS | `docs/context/e2e_evidence/pead_real_data_validation_20260620.json` remains protected at SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`. |
| EVD-06 | Strategy Method Reviewer A terminal recheck | PASS | Literature, overlap order, bootstrap, and HAC checks passed after reconciliation. |
| EVD-07 | Runtime/Ops Reviewer B terminal recheck | PASS | Schema/constants/nested fields/nullability/no-additional-fields/deterministic arrays/dates/mandatory schema tests passed. |
| EVD-08 | Data Integrity Reviewer C terminal recheck | BLOCK | Original Reviewer C flagged count correction; final recheck after local count fix was unavailable due subagent usage limit. Replacement Reviewer C also failed to start due the same limit. |

## Reviewer Reconciliation

Implementer: Worker Ptolemy created the methodology gate file and first
contract draft.

Reviewer A: PASS after reconciliation. Calendar-time daily Q5-minus-Q1
portfolio regression is the selected primary method; stationary block bootstrap
is robustness-only; observed-event-date HAC and calendar-month/quarterly formal
inference remain rejected.

Reviewer B: PASS after reconciliation. Future M1B has a strict four-file
runtime/test allowlist, exact evidence path/schema, atomic publication rules,
protected existing JSON hash, and untracked-file backup/rollback rules.

Reviewer C: BLOCK. Reviewer C found the draft count issue; parent local rerun
corrected the contract, but the required independent terminal recheck could not
run due subagent usage limits.

Ownership check: BLOCK for terminal closure because the final Reviewer C verdict
is missing. Implementer, Reviewer A, Reviewer B, and the original Reviewer C
were distinct where usable review results exist.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Draft feasibility text used stale/null-date count semantics and would have mismatched the future `null_return_date_rows_excluded` schema field. | Reran parent-side exact count check and corrected the contract to 19,812 null-date rows, 226,772 expected rows, and 1,519 missing rows. | Docs/Ops + Data | RESOLVED LOCALLY; Reviewer C recheck pending |
| High / Process | Terminal independent Reviewer C could not rerun after the corrected count contract, so M1A cannot close as approved. | Rerun independent Reviewer C when subagent capacity returns. | Docs/Ops | OPEN, BLOCKING |
| Info | Quarterly output could be misread as formal inference because it has non-null descriptive statistics. | Contract keeps quarterly `ex_post_descriptive_only=true` and rejects quarterly as primary formal inference. | Strategy | RESOLVED |
| Info | Primary-source support was initially insufficient for the calendar-time rationale. | Added and validated Fama (1998) PDF/text and cited the calendar-time cross-correlation support. | Research | RESOLVED |

## Scope Split Summary

In-scope resolved actions: method selection, primary formula, HAC bandwidth,
robustness method, overlap rule, missingness rule, claim boundary, future M1B
schema/allowlist, research claims, parent corrected count validation, and
PARTIAL/BLOCK truth-surface reconciliation.

Inherited or out-of-scope actions: M1B estimator implementation, M1B JSON
publication, PIT EPS, full universe expansion, CRSP/delisting, dashboard alpha
verdicts, product ranking/scoring, alerts, recommendations, broker/order paths,
staging, and commit.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/phase_brief/v2-pead-alpha-inference-methodology-gate.md` | Records selected calendar-time contract, corrected counts, strict future M1B schema, and terminal Reviewer C blocker. | A/B PASS; C terminal recheck unavailable |
| `docs/research/pead_inference_methodology_claims_20260621.json` | Stores two directly cited primary-source claims. | ClaimValidation PASS |
| `docs/research/fama_1998_market_efficiency_long_term_returns.pdf` | Local primary-source PDF for calendar-time portfolio support. | Research PASS |
| `docs/research/fama_1998_market_efficiency_long_term_returns.txt` | Extracted text used for claim grounding. | Research PASS |
| `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md` | Product/spec addenda preserve terminal-blocked M1A status and no-alpha/no-product-action boundaries. | Docs/Ops reconciled |
| `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md` | Formula registry, decision lock, and lesson updated with corrected count and reviewer-capacity guardrail. | Docs/Ops reconciled |
| `docs/context/*_current.md` | Current truth surfaces moved from M1A approved to PARTIAL/BLOCK pending Reviewer C. | Context validation PASS |
| `docs/saw_reports/saw_v2_pead_alpha_inference_methodology_gate_20260621.md` | Publishes terminal SAW BLOCK evidence. | SAW validators PASS |

## Skill Closure Evidence

- Scope selector: PASS. Bounded scope was M1A methodology gate only.
- Boundary gate: PASS. Quarterly promotion, product action, provider, data, runtime, and M1B execution remained blocked.
- Research analysis: PASS. ClaimValidation PASS with two directly cited claims from Fama (1998).
- SAW: BLOCK. Terminal Reviewer C recheck remains unavailable.

## Open Risks

Open Risks: reviewer_C_terminal_count_recheck_unavailable; M1B_not_authorized_until_reviewer_C_PASS; data_quality_limits_500_GVKEY_current_vintage_Compustat_returns_no_delisting.

Next action: rerun_reviewer_C_terminal_count_recheck_then_decide_M1B_implementation

ClosurePacket: RoundID=ROUND-20260621-V2-PEAD-ALPHA-INFERENCE-METHODOLOGY-GATE; ScopeID=V2_PEAD_CALENDAR_TIME_INFERENCE_METHOD_CONTRACT; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=reviewer_C_terminal_count_recheck_unavailable; NextAction=rerun_reviewer_C_terminal_count_recheck_then_decide_M1B_implementation

ClosureValidation: PASS

SAWBlockValidation: PASS
