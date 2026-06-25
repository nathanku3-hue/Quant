# SAW Report - V2 PEAD M6a.1 Reviewer A Rerun

Hierarchy Confirmation: Approved | Session: inherited-project-session | Trigger: inherited reviewer-only rerun | Domains: quantitative-research, strategy-correctness, governance

## Scope

Round scope: Reviewer A terminal rerun of M6a.1 strategy correctness and regression-risk evidence only. No source code, provider access, data artifact publication, UI, alpha interpretation, ranking/scoring, alert, recommendation, broker/order path, or daily-return parquet publication was added.

- `RoundID`: `ROUND-20260625-V2-PEAD-M6A-REVIEWER-A-RERUN`
- `ScopeID`: `V2_PEAD_M6A_REVIEWER_A_STRATEGY_CORRECTNESS_RERUN`

NoChangeReason: This round reviewed the existing M6a.1 sparse-engine implementation and fail-closed evidence; it did not alter implementation logic.

## Acceptance checks

- `CHK-01`: Focused M6a.1 test suite passes.
- `CHK-02`: M5a plus M6a.1 focused regression passes.
- `CHK-03`: Broader PEAD D1/D2/D2B/D3/event-study/M5a/M6 regression passes.
- `CHK-04`: M6a.1 module compiles.
- `CHK-05`: Strategy construction semantics are correct: deterministic decision-date quantiles, tradability/liquidity filtering, high-signal long leg, low-signal short leg, next-session entry, bounded holding window, and minimum-leg gating.
- `CHK-06`: Return/cost semantics are correct: daily sparse leg normalization, long/short contribution split, entry/overlap/exit/final trade-to-zero turnover, explicit nonzero costs, deterministic daily output hash, and blocked real-run boundary.
- `CHK-07`: Reviewer A terminal evidence is complete for this rerun.

## Reviewer A evidence

- Focused M6a.1 tests: PASS, 12/12.
- M5a plus M6a.1 tests: PASS, 16/16.
- Broader PEAD slice: PASS, 109/109 with inherited ArrowStringArray warnings only.
- Module compile: PASS.
- `--validate-inputs`: PASS, exit 0, writes blocked fail-closed evidence.
- `--run`: PASS as fail-closed behavior, exit 2, emits no daily returns or equity curve.
- Evidence replay: PASS. Current evidence SHA256 is `d55da0ec4ed551b763f0f445f5397a3014181bfaa04e2eae96378db303924dee`; `workflow_status=blocked_fail_closed`; `m6a_scale_engine_ready=true`; `m6b_real_run_wiring_allowed=true`; `m6b_data_contract_ready=false`; `daily_returns_emitted=false`; `equity_curve_emitted=false`.

## Strategy correctness review

- `scripts/pead_m6_pit_walk_forward_equity_curve.py:347` assigns quantiles per `decision_date`; `:355` filters `tradable` and `liquidity_pass`; side assignment remains high-signal long and low-signal short.
- `scripts/pead_m6_pit_walk_forward_equity_curve.py:457` uses the sorted trading-calendar `searchsorted(..., side="right")`, so entries begin on the first return session after the decision date, not on the signal date.
- `scripts/pead_m6_pit_walk_forward_equity_curve.py:601` and `:609` count active long/short events by return session and normalize weights only when both legs satisfy `min_leg_count`.
- `scripts/pead_m6_pit_walk_forward_equity_curve.py:677` and `:701` preserve the final trade-to-zero liquidation in addition to sparse previous/current security-weight turnover.
- `scripts/pead_m6_pit_walk_forward_equity_curve.py:497` provides canonical daily output hashing for repeated-run and shuffled-input parity.
- `scripts/pead_m6_pit_walk_forward_equity_curve.py:222` and `:908` preserve the strict input-contract boundary: engine readiness does not become strict EPS-vintage, delisting-adjusted return, or tradability/liquidity readiness.

## Findings table

| ID | Severity | Impact | Fix / Disposition | Owner | Status |
|---|---:|---|---|---|---|
| F-01 | Info | Reviewer A found no in-scope strategy-correctness or regression-risk blocker in the M6a.1 sparse-engine implementation. | No code change required. Keep M6a.1 fail-closed until B/C terminal review and M6b data gates complete. | Reviewer A | Closed |
| F-02 | Info | Reviewer B and Reviewer C terminal reruns for the changed M6a.1 implementation are still required before full SAW closure. | Run Reviewer B and Reviewer C reruns independently. | Governance | Open |
| F-03 | Info | Strict EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity screen remain unavailable, so real M6 equity output remains blocked. | Preserve `m6b_data_contract_ready=false` and do not emit daily-return parquet or CAGR until M6b closes. | M6b data-prep | Open inherited |
| F-04 | Low | M6a.1 files and evidence are still untracked in the dirty checkout, so Git provenance remains unresolved. | Reconcile/stage/commit only in a separate approved Git round. | Repo hygiene | Open inherited |

## Scope split summary

### In scope

- Strategy correctness, regression-risk, cost/turnover semantics, deterministic daily-output parity, and fail-closed claim boundary for the M6a.1 sparse engine.

### Inherited / out of scope

- Runtime/operational resilience Reviewer B.
- Data-integrity/performance-path Reviewer C.
- Dirty worktree and prior main-PR reconciliation.
- EPS vintage decision, delisting-adjusted returns, as-of tradability/liquidity screen, M6b data-prep, real equity curve, daily-return parquet, provider access, UI, alpha claims, ranking/scoring, alerts, recommendations, and broker/order paths.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_v2_pead_m6a_reviewer_a_rerun_20260625.md` | New reviewer-only terminal evidence artifact; no implementation logic changed. | Reviewer A PASS |

## Document Sorting

Reviewer evidence is a terminal review artifact for this reviewer-only rerun. No product, strategy, data, provider, or UI document changed by this report.

## Closure packet

ClosurePacket: RoundID=ROUND-20260625-V2-PEAD-M6A-REVIEWER-A-RERUN; ScopeID=V2_PEAD_M6A_REVIEWER_A_STRATEGY_CORRECTNESS_RERUN; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=Reviewer_B_C_terminal_reruns_and_M6b_data_gates_still_pending; NextAction=Run_independent_Reviewer_B_and_Reviewer_C_terminal_reruns_before_M6b_data_prep

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Reviewer B and Reviewer C terminal reruns are still required for full M6a.1 SAW closure.
- Strict PIT EPS vintage, delisting-adjusted tradable returns, and full as-of tradability/liquidity data still block any M6 real-run curve.
- The checkout remains heavily dirty; no unrelated file was reverted, staged, or committed.

Next action:

Run independent Reviewer B and Reviewer C on the M6a.1 sparse-engine change. After terminal review PASS, M6b may begin only as data-prep for the independent strict data gates.

SAW Verdict: PASS
