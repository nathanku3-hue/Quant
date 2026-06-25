# SAW Report - V2 PEAD M6a.1 Reviewer C Rerun

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: reviewer-only rerun | Domains: quantitative-research, data-engineering, performance, governance

## Scope

Round scope: Reviewer C terminal rerun for M6a.1 data integrity and performance path only. This rerun reviewed the completed sparse-engine implementation, fail-closed evidence, test coverage, and runtime behavior. No source code, provider access, data artifact publication, UI, alpha interpretation, ranking/scoring, alert, recommendation, broker/order path, or daily-return parquet publication was added.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-1-REVIEWER-C-RERUN`
- `ScopeID`: `V2_PEAD_M6A_1_REVIEWER_C_DATA_INTEGRITY_AND_PERFORMANCE_RERUN`

NoChangeReason: This round created reviewer-only evidence for the existing M6a.1 implementation and did not alter implementation logic or canonical PEAD data artifacts.

## Acceptance checks

- `CHK-01`: Focused M6a.1 test suite passes.
- `CHK-02`: M5a plus M6a.1 focused regression passes.
- `CHK-03`: Broader PEAD D1/D2/D2B/D3/event-study/M5a/M6 regression slice passes.
- `CHK-04`: M6a.1 module compiles.
- `CHK-05`: CLI fail-closed behavior is independently rerun without mutating the canonical evidence path.
- `CHK-06`: Sparse engine uses a sorted global `return_idx:int32` calendar, numeric-only projected relations, object-dtype guards, and direct DuckDB daily aggregation with no wide position matrix.
- `CHK-07`: Turnover and data-integrity tests cover entry, overlap, exit, final trade-to-zero, deterministic hash parity, and duplicate/invalid input guards.
- `CHK-08`: Full-universe synthetic smoke covers 196,638 events x 60 sessions within the configured 1024MB cap and 60-second latency budget.

## Reviewer C evidence

- `CHK-01`: PASS. `.venv/Scripts/python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` returned `12 passed`.
- `CHK-02`: PASS. `.venv/Scripts/python.exe -m pytest tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` returned `16 passed`.
- `CHK-03`: PASS. `.venv/Scripts/python.exe -m pytest tests/test_pead_d1_sue.py tests/test_pead_d2_returns.py tests/test_pead_d2b_event_window_contract.py tests/test_pead_d3_benchmark_artifact.py tests/test_pead_event_study.py tests/test_pead_m5a_multifactor_alpha_test.py tests/test_pead_m6_pit_walk_forward_equity_curve.py -q` returned `109 passed` with inherited ArrowStringArray warnings only.
- `CHK-04`: PASS. `.venv/Scripts/python.exe -m py_compile scripts/pead_m6_pit_walk_forward_equity_curve.py` returned exit 0.
- `CHK-05`: PASS. A temporary-output CLI replay returned `--validate-inputs` exit 0 and `--run` exit 2; the run evidence reported `workflow_status=blocked_fail_closed`, failure reasons `delisting_missing,pit_vintage_blocked,tradability_liquidity_screen_missing,tradable_return_missing`, `daily_return_summary.status=not_emitted`, `equity_curve_summary.status=not_emitted`, and no temporary daily-return parquet was created.
- `CHK-06`: PASS. `scripts/pead_m6_pit_walk_forward_equity_curve.py:397-493` rejects object-dtype DuckDB relations after projecting event, return, and calendar relations to numeric identifiers; `:557-719` executes the sparse DuckDB interval plan and direct daily aggregation.
- `CHK-07`: PASS. `tests/test_pead_m6_pit_walk_forward_equity_curve.py:265-309` locks the no-dense-pivot source guard and int32 relation contract; `:241-258` covers entry/overlap/rebalance/final trade-to-zero turnover; `:311-326` covers deterministic shuffled-input daily output hash parity.
- `CHK-08`: PASS. `.venv/Scripts/python.exe -m pytest tests/test_pead_m6_pit_walk_forward_equity_curve.py::test_m6_sparse_engine_full_universe_smoke_stays_under_memory_cap_and_latency_budget -q --durations=5` returned PASS; the smoke call duration was `4.04s` for 196,638 events x 60 sessions under the 60-second budget.

## Data-integrity and performance review

- Calendar integrity: PASS. `entry_idx` is computed with `searchsorted(..., side="right")`, so portfolio entry starts after the decision date; `exit_idx` is derived from the configured holding-period bound.
- Relation projection: PASS. Event identifiers and security identifiers are mapped to `int32` categories before DuckDB registration, and object dtype columns are rejected for all registered relations.
- Duplicate return protection: PASS. The engine rejects duplicate `(security_idx, return_idx)` rows before aggregation.
- Aggregation path: PASS. DuckDB uses sparse `event.security_idx = ret.security_idx AND ret.return_idx BETWEEN event.entry_idx AND event.exit_idx`, direct daily `fsum` aggregation, single-thread execution, and no persisted position-day or wide security-by-date matrix.
- Turnover path: PASS. The engine accounts for current weight changes, previous-only exits, and final trade-to-zero liquidation, with tests covering overlapping cohort parity.
- Determinism path: PASS. Canonical daily output SHA-256 and shuffled-input equality are tested; engine runtime evidence records single-thread compensated aggregates and canonical hashing.
- Fail-closed data boundary: PASS. Current evidence SHA256 is `d55da0ec4ed551b763f0f445f5397a3014181bfaa04e2eae96378db303924dee`; `workflow_status=blocked_fail_closed`, `m6a_scale_engine_ready=true`, `m6b_real_run_wiring_allowed=true`, `m6b_data_contract_ready=false`, `daily_returns_emitted=false`, and `equity_curve_emitted=false` remain the correct boundary.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | Info | Reviewer C found no in-scope data-integrity or performance-path blocker in the M6a.1 sparse-engine implementation. | No code change required. Preserve fail-closed evidence and keep M6b data gates separate. | Reviewer C | Closed |
| F-02 | Info | Reviewer B terminal rerun is still required before full M6a.1 terminal SAW closure can be claimed. | Run independent Reviewer B or reconcile with an existing terminal B artifact if one is produced elsewhere. | Governance | Open |
| F-03 | Info | Strict EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity screen remain unavailable; real M6 equity output remains blocked. | Preserve `m6b_data_contract_ready=false` and do not emit daily-return parquet or CAGR until M6b closes its data contract. | M6b data-prep | Open inherited |
| F-04 | Low | The checkout remains heavily dirty and M6a.1 files/evidence are untracked, so Git provenance remains unresolved. | Reconcile/stage/commit only in a separate approved Git round; no unrelated file was reverted or staged here. | Repo hygiene | Open inherited |

## Scope split summary

### In scope

- M6a.1 data-integrity and performance-path validation for the sparse DuckDB engine.
- Calendar-index, numeric projection, dtype guard, duplicate return rejection, turnover parity, deterministic hash parity, full-universe smoke, and fail-closed data boundary.

### Inherited / out of scope

- Reviewer A/B reruns not performed by this Reviewer C round.
- Dirty worktree and prior main-PR reconciliation.
- EPS vintage decision, delisting-adjusted returns, as-of tradability/liquidity screen, M6b data-prep, real equity curve, daily-return parquet, provider access, UI, alpha claims, ranking/scoring, alerts, recommendations, and broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_v2_pead_m6a_1_reviewer_c_rerun_20260625.md` | New reviewer-only terminal evidence artifact for M6a.1 Reviewer C; no implementation logic or canonical data artifact changed. | Reviewer C PASS |

## Document Sorting

Reviewer evidence is a terminal review artifact for this reviewer-only rerun. No product, strategy, data, provider, or UI document changed by this report.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6A-1-REVIEWER-C-RERUN; ScopeID=V2_PEAD_M6A_1_REVIEWER_C_DATA_INTEGRITY_AND_PERFORMANCE_RERUN; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=Reviewer_B_terminal_rerun_and_M6b_data_gates_still_pending; NextAction=Run_independent_Reviewer_B_or_reconcile_terminal_B_before_M6b_data_prep

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Reviewer B terminal rerun is still required before full M6a.1 terminal SAW closure, unless a valid independent Reviewer B artifact exists outside this round.
- Strict PIT EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity data still block any M6 real-run curve.
- The checkout remains heavily dirty; no unrelated file was reverted, staged, or committed.

Next action:

Run or reconcile independent Reviewer B on the M6a.1 sparse-engine change. After terminal review PASS, M6b may begin only as data-prep for the independent strict data gates.

SAW Verdict: PASS
