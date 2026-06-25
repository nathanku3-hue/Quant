# SAW Report - V2 PEAD M6b Best-Available Option 1 Reviewer C

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: user requested Reviewer C takeover | Domains: data-integrity, performance-path, artifact-isolation, governance

## Scope

Round scope: Reviewer C data-integrity and performance-path review of the Option 1 B implementation only. This review checks the read-only data gate, standalone flagged B output, parquet/content consistency, 2015-2019 coverage claims, replay determinism, runtime isolation from strict M6/M5 alpha paths, and artifact/data claim boundaries. No implementation logic, provider ingestion, strict M6b readiness flag, M6a evidence flag, UI, alpha interpretation, ranking/scoring, alert, recommendation, live/paper path, broker/order path, or strict data artifact was changed by this review.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-C`
- `ScopeID`: `V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_C_DATA_INTEGRITY_PERFORMANCE`

NoChangeReason: Reviewer C inspected and replayed the existing Option 1 B artifacts; this report records review findings only.

## Acceptance checks

- `CHK-01`: Data-gate artifact is policy-only and emits no curve/parquet.
- `CHK-02`: Standalone run artifact carries all eight claim-ceiling flags and keeps `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`.
- `CHK-03`: Daily parquet exists, hash matches JSON, row count matches JSON, dates are bounded to 2015-2019, dates are unique, and gross/net daily returns are finite.
- `CHK-04`: Gate replay occurs before standalone B replay and replayed artifact hashes remain stable.
- `CHK-05`: Focused B isolation tests plus existing M6 sparse-engine tests pass.
- `CHK-06`: Standalone script compiles.
- `CHK-07`: B artifact names are not unexpectedly referenced by runtime/data/UI/strict strategy paths outside the standalone script.
- `CHK-08`: Selected events have complete 60-session coverage inside the declared 2015-2019 B return calendar before reported metrics are treated as a coherent 60-session diagnostic curve.
- `CHK-09`: The standalone script is invocable as a standalone script or its supported invocation boundary is explicitly documented and tested.
- `CHK-10`: Reviewer C evidence is complete for this rerun.

## Reviewer C evidence

- Data-gate artifact inspection: PASS. `mode=data_gate_read_only_policy_decision`; `curve_emitted=false`; `daily_return_parquet_emitted=false`; `m6b_strict_readiness=false`; `usable_for_alpha_inference=false`.
- Standalone run artifact inspection: PASS. `mode=standalone_best_available_illustrative_run`; claim-ceiling flags are `illustrative_only`, `restated_vintage`, `no_delisting`, `survivorship_biased`, `coverage_2015_2019`, `provider_limited`, `not_alpha`, and `not_tradable_claim`; strict/alpha usability flags are false.
- Daily parquet check: PASS. JSON path points to `data/processed/pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet`; SHA256 matches JSON; rows match JSON at 997; date range is `2016-01-15` through `2019-12-31`; duplicate return dates are 0; `daily_gross_return` and `daily_net_return` are finite.
- Replay order: PASS via supported import invocation. `--data-gate` replay wrote `docs/context/e2e_evidence/pead_m6b_data_gate_bestavail_policy_20260625.json`; `--run-bestavail` replay wrote `docs/context/e2e_evidence/pead_m6b_bestavail_illustrative_2015_2019.json`. Content hashes after replay remained stable: gate JSON `0a0f8c4dcf9e68ef6d587efda441e5f480bbf51bcf7090365377f3972e6f448b`; run JSON `54f6f622070e038c20c8666ec7e67edc0d4065086669a5b482e74772b0456d56`; daily parquet `69da85dca6adb2ac81e2d0a0d76a7e2f94ce97d1ad5a30b481df80aa12ee4ca6`.
- Focused combined pytest: PASS, 14/14 via `.venv/Scripts/python.exe -m pytest tests/test_pead_m6b_bestavail_illustrative_2015_2019.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q`.
- Compile: PASS via `.venv/Scripts/python.exe -m py_compile scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Runtime isolation scan: PASS. No unexpected B JSON/parquet artifact references were found in `scripts`, `strategies`, `views`, `core`, or `data` outside `scripts/pead_m6b_bestavail_illustrative_2015_2019.py`.
- Session-completeness check: BLOCK. `load_bestavail_frames()` loaded 78,348 events and 7,508,048 returns; M6 sparse selection produced 29,737 selected events over a 1,278-session calendar from `2015-01-05` through `2019-12-31`. Of those selected events, 1,796 have `exit_idx` beyond the calendar max index 1,277; max observed `exit_idx` is 1,330. These events cannot complete the configured 60-session holding rule inside the declared B return calendar.
- Direct script invocation check: BLOCK. `.venv/Scripts/python.exe scripts/pead_m6b_bestavail_illustrative_2015_2019.py --data-gate` fails with `ModuleNotFoundError: No module named 'scripts'`. Import invocation works, but direct standalone execution is not currently reliable.

## Data integrity and performance review

- The B gate/run outputs are isolated from strict M6 path names and retain the required hard false strict/alpha flags.
- The emitted parquet and JSON agree on path, SHA256, row count, and date range; daily returns are finite and date-unique.
- The B replay is deterministic by content hash when run through the supported import invocation.
- Blocking issue: the B event eligibility does not require a full 60-session post-decision window before `2019-12-31`. The current sparse engine silently joins only available returns, so late-2019 selected events contribute truncated terminal windows rather than being excluded or flagged. This is a data-integrity blocker for treating the output as a coherent 60-session diagnostic curve, even though the artifact remains illustrative-only and not alpha/tradable.
- Blocking issue: the script is described as standalone, but direct script execution fails before argument handling because the repo root is not inserted into `sys.path` before importing from `scripts`.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | High | 1,796 / 29,737 selected B events have `exit_idx` beyond the 2015-2019 return calendar, so terminal cohorts cannot complete the 60-session holding rule and the reported terminal curve segment is truncated. | Before Reviewer C PASS, enforce full 60-session coverage inside the B calendar, or explicitly exclude/flag terminal-truncated cohorts and regenerate JSON/parquet. Preferred fix: derive a last eligible decision/entry index from the return calendar and require `exit_idx <= max(return_idx)` before the engine call. | Implementer | Open |
| F-02 | Medium | Direct standalone script execution fails with `ModuleNotFoundError: No module named 'scripts'`; evidence replay currently depends on import invocation. | Add the repo root to `sys.path` before importing sibling modules, or document/test `python -m`/import invocation as the only supported CLI. | Implementer | Open |
| F-03 | Info | Data-gate artifact correctly emits no curve/parquet and sets strict/alpha usability flags false. | Preserve this boundary. | Reviewer C | Closed |
| F-04 | Info | Standalone run JSON and daily parquet are internally consistent: 997 rows, `2016-01-15` through `2019-12-31`, matching parquet SHA256, date-unique rows, finite gross/net returns. | Keep these checks in the B isolation test suite after repair. | Reviewer C | Closed |
| F-05 | Info | No unexpected runtime-path references to B JSON/parquet were found outside the standalone script in the scanned runtime/data/UI/strict strategy areas. | Keep B unimported from strict M6, M5a alpha, UI, ranking/scoring, alerts, recommendations, and broker/order paths. | Reviewer C | Closed |
| F-06 | Info | Checkout remains heavily dirty with many inherited unrelated changes; Reviewer C did not stage, commit, revert, or clean unrelated files. | Reconcile repo hygiene in a separate approved Git round. | Repo hygiene | Open inherited |
| F-07 | Info | B remains illustrative-only and cannot support alpha, tradable, or strict-readiness claims, even after the data-integrity defects are repaired. | Preserve `m6b_strict_readiness=false` and `usable_for_alpha_inference=false`. | Governance | Open inherited |

## Scope split summary

Scope tokens: in-scope; out-of-scope.

### In scope

- Data-gate and run-artifact JSON/parquet consistency.
- Daily parquet row/date/hash/finite-value checks.
- 2015-2019 return-calendar completeness under the configured 60-session holding rule.
- Supported replay path, direct standalone invocation behavior, compile, focused pytest, and B runtime isolation from strict paths.

### Inherited / out of scope

- Reviewer A strategy-correctness repair and Reviewer B runtime/operational review.
- Strict Path A data authorization.
- Provider ingestion, CRSP delisting returns, Compustat PIT/unrestated EPS, IBES, 2020-2026 return pulls, dashboard/UI, alpha interpretation, ranking/scoring, alerts, recommendations, live/paper, or broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_v2_pead_m6b_bestavail_option1_reviewer_c_20260625.md` | New Reviewer C report; no implementation logic changed by this review. | Reviewer C BLOCK |

## Document Sorting

Reviewer evidence is a terminal review artifact for this reviewer-only pass. No product, strategy, data, provider, or UI document changed by this report.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1-REVIEWER-C; ScopeID=V2_PEAD_M6B_BESTAVAIL_OPTION1_REVIEWER_C_DATA_INTEGRITY_PERFORMANCE; ChecksTotal=10; ChecksPassed=7; ChecksFailed=3; Verdict=BLOCK; OpenRisks=Terminal_60_session_B_windows_are_truncated_and_direct_standalone_script_invocation_fails; NextAction=Repair_B_terminal_window_completeness_and_direct_invocation_then_regenerate_artifacts_and_rerun_Reviewer_A_C

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Terminal B cohorts can be included without a complete 60-session holding window inside the 2015-2019 B return frame.
- Direct standalone script invocation fails; only import invocation replay is currently proven.
- B remains illustrative-only and cannot support alpha, tradable, or strict-readiness claims.
- Independent Reviewer B is still required after repair; Reviewer A is already BLOCK on the same terminal-window issue.
- The checkout remains heavily dirty; no unrelated file was reverted, staged, committed, or cleaned.

Next action:

Repair the terminal-window eligibility defect and direct standalone invocation defect, regenerate the standalone B JSON/parquet, rerun focused tests and flag checks, then rerun Reviewer A and Reviewer C before any closure language.

SAW Verdict: BLOCK
