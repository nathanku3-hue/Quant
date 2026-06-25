# SAW Report - V2 PEAD M6b Best-Available Option 1 Reviewer A

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: user requested Reviewer A takeover | Domains: quantitative-research, strategy-correctness, regression-risk, governance

## Scope

Round scope: Reviewer A strategy-correctness and regression-risk review of the Option 1 B implementation only. This review checks that the standalone best-available path preserves portfolio semantics, coverage boundaries, and the A/B firewall. No implementation logic, provider ingestion, strict M6b readiness flag, M6a evidence flag, UI, alpha interpretation, ranking/scoring, alert, recommendation, live/paper path, broker/order path, or strict data artifact was changed by this review.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-A`
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_A_STRATEGY_CORRECTNESS`

NoChangeReason: Reviewer A inspected the existing Option 1 B implementation and evidence; this report records review findings only.

## Acceptance checks

- `CHK-01`: The B path remains standalone and separate from strict M6b/M6a artifact names.
- `CHK-02`: The data-gate artifact emits no curve and no daily-return parquet.
- `CHK-03`: The standalone run artifact carries all eight claim-ceiling flags and keeps `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`.
- `CHK-04`: Focused B isolation tests plus existing M6 sparse-engine tests pass.
- `CHK-05`: The standalone script compiles.
- `CHK-06`: Strategy holding-period semantics remain consistent with the advertised 60-session M6 engine rule under the 2015-2019 coverage cap.
- `CHK-07`: Reviewer A evidence is complete for this rerun.

## Reviewer A evidence

- Data-gate replay: PASS via import invocation; wrote `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`.
- Standalone B run: PASS via import invocation; wrote `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json` and `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`.
- Focused combined pytest: PASS, 14/14 via `./.venv/Scripts/python.exe -m pytest tests/test_pead_m6b_bestavail_illustrative_2015_2019.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q`.
- Compile: PASS via `./.venv/Scripts/python.exe -m py_compile scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Flag check: PASS. Run artifact carries `illustrative_only`, `restated_vintage`, `no_delisting`, `survivorship_biased`, `coverage_2015_2019`, `provider_limited`, `not_alpha`, and `not_tradable_claim`; it also sets `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`.
- Coverage observation: `load_bestavail_frames()` includes events through `2019-12-31` while return rows are capped at `2019-12-31`. Therefore late-2019 cohorts cannot complete the advertised 60-session holding window inside the B coverage cap.

## Strategy correctness review

- The standalone file is separate from `scripts/pead_m6_pit_walk_forward_equity_curve.py` and writes separate artifact names, preserving the A/B firewall at the artifact-name level.
- The gate mode writes policy evidence only and sets `curve_emitted=false` plus `daily_return_parquet_emitted=false`, matching the required M6b-DATA-GATE boundary.
- The run mode reuses M6a.1 in-memory engine functions rather than wiring a reusable strict M6b input adapter, matching the selected Option 1 architecture.
- The run artifact is properly labelled as standalone best-available and not alpha/tradable evidence.
- Blocking issue: event selection accepts any `event_date` through `2019-12-31`, but the return universe is capped through `2019-12-31`. The M6 engine is configured with `holding_period_sessions=60`. Events near the right edge of 2019 necessarily receive truncated post-event windows. This violates the stated 60-session holding semantics for the reported 2015-2019 diagnostic curve and can distort the terminal segment, turnover, and equity summary.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | High | Late-2019 events are eligible even though the local B return frame ends on 2019-12-31, so those cohorts cannot complete the 60-session holding rule inside the declared coverage window. This undermines strategy-correctness parity for the terminal portion of the illustrative curve. | Before Reviewer A PASS, either exclude events whose 60-session exit is after 2019-12-31, or explicitly emit a separate terminal-truncation flag and remove incomplete-window days/events from reported curve metrics. Preferred fix: derive the last eligible decision date from the 2015-2019 trading calendar and enforce full 60-session coverage before the engine call. | Implementer | Open |
| F-02 | Info | The A/B firewall is preserved at the module and artifact-name level: strict M6a/M6 paths do not read `pead_m6b_bestavail_illustrative_2015_2019.json`, and output paths differ from strict M6 paths. | Keep the standalone diagnostic isolated; do not import this script from strict M6b code. | Reviewer A | Closed |
| F-03 | Info | Required B flags are present in the run artifact and strict/alpha usability flags are false. | Keep every chart/table/report labelled with the full claim ceiling. | Reviewer A | Closed |
| F-04 | Info | B remains no-alpha/no-tradable and cannot be used for strict M6b readiness, even after the terminal-window issue is repaired. | Preserve `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`. | Governance | Open inherited |
| F-05 | Low | Checkout remains heavily dirty with many inherited unrelated changes; Reviewer A did not stage, commit, or revert anything. | Reconcile repo hygiene in a separate approved Git round. | Repo hygiene | Open inherited |

## Scope split summary

Scope tokens: in-scope; out-of-scope.

### In scope

- Strategy correctness of event eligibility, holding-window semantics, claim boundary, standalone B artifact isolation, and regression risk against strict M6 paths.

### Inherited / out of scope

- Runtime/operational Reviewer B.
- Data-integrity/performance Reviewer C.
- Strict Path A data authorization.
- Provider ingestion, CRSP delisting returns, Compustat PIT/unrestated EPS, IBES, 2020-2026 return pulls, dashboard/UI, alpha interpretation, ranking/scoring, alerts, recommendations, live/paper, or broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_a_20260625.md` | New Reviewer A report; no implementation logic changed by this review. | Reviewer A BLOCK |

## Document Sorting

Reviewer evidence is a terminal review artifact for this reviewer-only pass. No product, strategy, data, provider, or UI document changed by this report.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-A; ScopeID=V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_A_STRATEGY_CORRECTNESS; ChecksTotal=7; ChecksPassed=5; ChecksFailed=2; Verdict=BLOCK; OpenRisks=Late_2019_events_can_have_truncated_60_session_windows_under_2015_2019_return_cap; NextAction=Repair_or_explicitly_remove_terminal_truncated_B_windows_then_rerun_Reviewer_A

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Late-2019 cohorts can be included without a complete 60-session holding window inside the 2015-2019 B return frame.
- B remains illustrative-only and cannot support alpha, tradable, or strict-readiness claims.
- Independent Reviewer B and Reviewer C are still required after Reviewer A is repaired.
- The checkout remains heavily dirty; no unrelated file was reverted, staged, or committed.

Next action:

Repair the terminal-window eligibility defect by enforcing full 60-session coverage inside the 2015-2019 B frame, regenerate the standalone B artifact, rerun focused tests and flag checks, then rerun Reviewer A.

SAW Verdict: BLOCK
