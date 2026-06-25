# SAW Report - V2 PEAD M6a PIT Walk-Forward Equity Framework

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-project-session | Domains: quantitative-research, data-engineering, governance

## Scope

Round scope: Review M5a evidence boundary and implement M6a as a fail-closed PIT input-contract plus walk-forward equity-curve framework.

- `RoundID`: `ROUND-20260624-V2-PEAD-M6A-PIT-WALK-FORWARD-EQUITY-FRAMEWORK`
- `ScopeID`: `V2_PEAD_M6A_PIT_WALK_FORWARD_EQUITY_FRAMEWORK_FAIL_CLOSED`

## Owned files changed in this round

- `scripts/pead_m6_pit_walk_forward_equity_curve.py`
- `tests/test_pead_m6_pit_walk_forward_equity_curve.py`
- `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json`
- `docs/phase_brief/v2-pead-m6-pit-walk-forward-equity-curve.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/saw_reports/saw_v2_pead_m6a_pit_walk_forward_equity_curve_20260624.md`

## Acceptance checks

- `CHK-01`: M5a evidence boundary reviewed and zero-cost net limitation recorded.
- `CHK-02`: M6a/M6b split recorded in docs and current truth surfaces.
- `CHK-03`: PIT contract distinguishes timing-PIT from EPS vintage/unrestated PIT.
- `CHK-04`: Current artifacts fail closed with `pit_vintage_blocked`, `delisting_missing`, `tradable_return_missing`, and `tradability_liquidity_screen_missing`.
- `CHK-05`: Nonzero explicit cost model is required.
- `CHK-06`: Synthetic strict-input portfolio/equity/fold engine tests pass.
- `CHK-07`: CLI `--validate-inputs` writes blocked evidence.
- `CHK-08`: CLI `--run` writes blocked evidence and exits non-zero.
- `CHK-09`: Focused/broader PEAD regression checks pass.
- `CHK-10`: Independent Reviewer A/B/C terminal pass is available.

## Evidence summary

- M5a gross FF3 intercept is `0.0006992875170429098` per day with HAC t-stat `8.975032890536228`.
- M5a net FF3 equals gross because `spread_cost_bps_per_day = 0.0`; M5a remains diagnostic-only.
- M6a evidence path `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json` records `workflow_status = blocked_fail_closed`.
- M6a flags record `timing_pit_release_date_or_rdq_aligned = true`, `strict_pit_eps_vintage = false`, and `eps_vintage = release_date_aligned_but_restated`.
- M6a emits no daily return parquet and no equity curve under current data.

## Validation commands

```text
.venv\Scripts\python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py -q
```

Result: PASS, 7/7.

```text
.venv\Scripts\python.exe -m pytest tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q
```

Result: PASS, 11/11.

```text
.venv\Scripts\python.exe -m pytest tests/test_pead_d1_sue.py tests/test_pead_d2_returns.py tests/test_pead_d2b_event_window_contract.py tests/test_pead_d3_benchmark_artifact.py tests/test_pead_event_study.py tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q
```

Result: PASS, 104/104.

```text
.venv\Scripts\python.exe -m py_compile scripts/pead_m6_pit_walk_forward_equity_curve.py
```

Result: PASS.

```text
.venv\Scripts\python.exe scripts\pead_m6_pit_walk_forward_equity_curve.py --validate-inputs --output docs\context\e2e_evidence\pead_m6_pit_walk_forward_equity_curve.json
```

Result: PASS; evidence status `blocked_fail_closed`.

```text
.venv\Scripts\python.exe scripts\pead_m6_pit_walk_forward_equity_curve.py --run --output docs\context\e2e_evidence\pead_m6_pit_walk_forward_equity_curve.json
```

Result: intended fail-closed; exit code `2`.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | High | Current artifacts cannot support a true M6 curve because strict EPS vintage, delisting-adjusted tradable returns, and full as-of tradability screen are missing. | Implemented fail-closed input contract and blocked equity curve emission. | M6a | Resolved in scope |
| F-02 | Medium | M5a net output can be misread because its cost was zero. | Recorded M5a as diagnostic-only and carried zero-cost limitation into M6a claim boundary. | M6a | Resolved in scope |
| F-03 | High | Full independent Reviewer A/B/C terminal pass was not run through separate reviewer agents in current tooling. | Mark SAW terminal closure as BLOCK despite local tests passing; next action is independent review or explicit owner risk acceptance. | Governance | Open |

## Scope split summary

### in-scope

- M6a framework implementation.
- M6a synthetic strict-input engine tests.
- M6a current-artifact fail-closed evidence.
- M5a evidence-boundary review.
- Current truth/doc registry updates.

### inherited

- The repository was already very dirty before this round; unrelated tracked/untracked changes were not cleaned or reverted.
- Earlier 28-commit to `main` PR remains unresolved and was not opened here.
- Provider/WRDS, true EPS vintage, CRSP/delisting return data, alpha/promotion/action surfaces remain blocked.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `scripts/pead_m6_pit_walk_forward_equity_curve.py` | New fail-closed M6a CLI, input contract, cost model, walk-forward/portfolio/equity engine. | Local checks PASS; terminal independent review missing |
| `tests/test_pead_m6_pit_walk_forward_equity_curve.py` | New contract/engine/CLI regressions. | Local checks PASS; terminal independent review missing |
| `docs/context/e2e_evidence/pead_m6_pit_walk_forward_equity_curve.json` | New M6a blocked evidence artifact. | Local checks PASS; terminal independent review missing |
| `docs/phase_brief/v2-pead-m6-pit-walk-forward-equity-curve.md` | M6a/M6b scope, formulas, acceptance evidence, forbidden boundary. | Local checks PASS; terminal independent review missing |
| `docs/notes.md` | Added formula registry and PIT boundary. | Local checks PASS; terminal independent review missing |
| `docs/decision log.md` | Added M6a decision and contract locks. | Local checks PASS; terminal independent review missing |
| `docs/lessonss.md` | Added guardrail for timing-PIT vs vintage-PIT overclaim risk. | Local checks PASS; terminal independent review missing |
| `docs/context/*.md` current truth surfaces | Added M6a fail-closed status and M6b next step. | Local checks PASS; terminal independent review missing |

## Document Sorting

Canonical ordering followed for governance-visible artifacts: implementation/test first, evidence JSON, phase brief, formula/decision/lesson docs, current context packets, SAW report.

## Closure packet

ClosurePacket: RoundID=ROUND-20260624-V2-PEAD-M6A-PIT-WALK-FORWARD-EQUITY-FRAMEWORK; ScopeID=V2_PEAD_M6A_PIT_WALK_FORWARD_EQUITY_FRAMEWORK_FAIL_CLOSED; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=Independent_Reviewer_A_B_C_terminal_pass_not_run_in_current_tooling; NextAction=Run_independent_reviewer_A_B_C_or_accept_local_M6a_evidence_before_M6b_data_prep

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Independent Reviewer A/B/C terminal pass has not run in current tooling; strict SAW closure is BLOCK even though local tests pass.
- True M6 curve remains blocked until M6b data dependencies close.
- Dirty worktree and unresolved main PR remain inherited risks.

Next action:

Run independent Reviewer A/B/C on M6a, or explicitly accept the local fail-closed M6a evidence and start M6b data-prep.

SAW Verdict: BLOCK
