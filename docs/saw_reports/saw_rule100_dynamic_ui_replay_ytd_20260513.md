# SAW Report - Rule100 Dynamic UI/Replay Sizing + Benchmark Stale Overlay

SAW Verdict: PASS

RoundID: 20260513-rule100-ytd-visible-correctness
ScopeID: rule100-dynamic-ui-replay-sizing-benchmark-stale-overlay
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Strategy, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

Fix visible Rule of 100 allocation and YTD benchmark behavior without rewriting frozen audit/history artifacts. The round keeps `Rule100SoftmaxConfig()` audit defaults stable, adds a dynamic UI/replay config derived from `controls.max_weight`, wires direct Rule100 allocation to that config, and makes benchmark YTD freshness stale-aware per ticker.

## Acceptance Checks

- CHK-01: `Rule100SoftmaxConfig()` audit defaults remain `gross_budget_per_name=0.10` and `max_single_name_weight=0.15`.
- CHK-02: `rule100_config_from_max_weight(max_weight)` sets UI/replay `gross_budget_per_name=max_weight`, `max_single_name_weight=max_weight`, and `gross_budget_cap=1.0`.
- CHK-03: one eligible Rule100 name at `max_weight=0.35` can target `35%`.
- CHK-04: two equal eligible Rule100 names at `max_weight=0.35` target `35% / 35% / 30% cash`.
- CHK-05: direct Rule100 UI state and Strategy Replay agree for the same candidate frame and cap.
- CHK-06: frozen Rule100 history/audit artifact is not regenerated as a 35% UI-policy artifact.
- CHK-07: benchmark freshness is evaluated per ticker; stale/missing QQQ can live-overlay while fresh SPY remains local.
- CHK-08: stale benchmark columns do not forward-fill into visible curves past their own stale cutoff without a live overlay attempt.
- CHK-09: focused Rule100/replay/YTD/AppTest suite, broader affected suite, full pytest, context validation, and Streamlit readiness smoke pass.
- CHK-10: docs-as-code surfaces, lesson loop, truth surfaces, and SAW report are refreshed.

## Subagent Passes

| Role | Agent | Status | Notes |
|---|---|---|---|
| Implementer | SAW Implementer subagent | PASS | Validated dynamic UI/replay sizing, preserved frozen audit defaults, direct UI/replay agreement, and required behavior tests. |
| Reviewer A | SAW Reviewer A subagent | PASS | Strategy correctness PASS: sizing math, cash residuals, and audit-default separation are sound. |
| Reviewer B | SAW Reviewer B subagent | PASS | Runtime resilience PASS: bounded display fallback, deterministic AppTest replay cap, and truthful source labels accepted. |
| Reviewer C | SAW Reviewer C subagent | PASS | Data/performance PASS with non-blocking Medium carried for production replay cold-start cost. |

Ownership Check: PASS. Implementer and Reviewer A/B/C were different review roles and the reviewer ownership did not overlap the implementer pass.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Regenerating frozen Rule100 history at 35% would corrupt audit-baseline semantics. | Kept `Rule100SoftmaxConfig()` frozen and introduced `rule100_config_from_max_weight(...)` for UI/replay callers only. | Backend/Strategy | Fixed |
| Medium | Direct Rule100 UI could disagree with Strategy Replay if `controls.max_weight` did not reach the softmax path. | `views/optimizer_view.py` passes max weight into `_rule100_softmax_weights_for_ui(...)`; Strategy Replay uses the same helper. | Frontend/UI | Fixed |
| Medium | Benchmark YTD could mark all local benchmarks stale or forward-fill stale QQQ while SPY was fresh. | `build_benchmark_equity_from_prices(...)` evaluates stale/missing tickers per column, overlays only those tickers, and drops stale columns that cannot refresh. | Data | Fixed |
| Medium | Streamlit AppTest could hang on full YTD Strategy Replay cold-start. | Test mode caps replay dates while production replay horizon remains unchanged. | Runtime/UI | Fixed |
| Low | Production dashboard replay remains cold-start expensive over long horizons. | Carried as future performance work; current full regression and readiness smoke pass. | Frontend/UI | Carried |

## Scope Split Summary

In-scope findings/actions:

- All in-scope Critical/High/Medium findings were fixed and rechecked PASS.
- No remaining in-scope Critical/High findings.

Inherited out-of-scope findings/actions:

- Broad inherited dirty/untracked worktree remains and was not reverted.
- Creating a versioned/labeled 35% Rule100 UI-policy history artifact remains a separate approval.
- Canonical benchmark backfill/provider ingestion remains a separate data decision.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/prd.md` | Product notice for visible Rule100 sizing and benchmark freshness boundaries. | PASS |
| `docs/spec.md` | Spec notice for dynamic UI/replay config and stale-aware benchmark helper. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added Rule100/YTD approved scope, held scope, contract, and acceptance checks. | PASS |
| `docs/handover/phase65_rule100_dynamic_ui_replay_ytd_handover.md` | Added PM handover and new-context bootstrap packet for this round. | PASS |
| `docs/notes.md` | Added explicit Rule100 UI/replay formula and benchmark stale-overlay formula. | PASS |
| `docs/lessonss.md` | Added guardrail on separating frozen audit artifacts from UI-policy replay. | PASS |
| `docs/decision log.md` | Added decision record and contract locks for Rule100 visible sizing and benchmark YTD freshness. | PASS |
| `docs/context/bridge_contract_current.md` | Added PM/planner deltas and do-not-redecide boundary. | PASS |
| `docs/context/impact_packet_current.md` | Added changed files, touched interfaces, evidence, and residual risks. | PASS |
| `docs/context/done_checklist_current.md` | Added and completed machine-checkable criteria for this round. | PASS |
| `docs/context/planner_packet_current.md` | Added compact planner addendum and next step. | PASS |
| `docs/context/multi_stream_contract_current.md` | Added Backend/UI/Data/Docs stream map for Rule100/YTD work. | PASS |
| `docs/context/post_phase_alignment_current.md` | Added stream alignment and bottleneck summary for Rule100/YTD. | PASS |
| `docs/context/observability_pack_current.md` | Added drift signals for audit-default rewrites, UI/replay disagreement, and stale benchmark forward-fill. | PASS |

Document Sorting: PASS. Changed docs are shown in the checklist order for repo-local docs.

## Verification Evidence

- EVD-01: `.venv\Scripts\python -m py_compile core\data_orchestrator.py strategies\rule100_softmax.py strategies\strategy_replay.py views\optimizer_view.py dashboard.py tests\test_rule100_softmax.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- EVD-02: `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_strategy_replay.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 89 passed.
- EVD-03: `.venv\Scripts\python -m pytest tests\test_rule100_softmax.py tests\test_rule100_softmax_v1_1.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 151 passed.
- EVD-04: `.venv\Scripts\python -m pytest -q` -> PASS.
- EVD-05: `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- EVD-06: Streamlit readiness on `http://127.0.0.1:8514/portfolio-and-allocation` -> PASS, HTTP 200.
- EVD-07: SAW Implementer and Reviewer A/B/C passes -> PASS; Reviewer C carried only a non-blocking Medium on production replay cold-start cost.

## Top-Down Snapshot

L1: Terminal Zero Portfolio & Allocation Correctness
L2 Active Streams: Backend/Strategy, Frontend/UI, Data, Docs/Ops
L2 Deferred Streams: versioned UI-policy history artifact, canonical benchmark ingestion, broker/alerts
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Frontend/UI
Active Stage Level: L3

+--------------------+----------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope        | Rating | Next Scope                                                   |
+--------------------+----------------------+--------+--------------------------------------------------------------+
| Planning           | B:UI/YTD/OH:PM/AC:10 | 100/100| 1) hold_or_manual_audit [86/100]: scope fixed and verified   |
| Executing          | dynamic config+YTD   | 100/100| 1) no in-scope blockers [94/100]: code/tests pass            |
| Iterate Loop       | SAW clean            | 100/100| 1) carry cold-start risk [82/100]: non-blocking              |
| Final Verification | pytest+smoke+context | 100/100| 1) publish report [94/100]: validators pass                  |
| CI/CD              | not requested        | 0/100  | 1) no git sync in this round [70/100]: not phase close       |
+--------------------+----------------------+--------+--------------------------------------------------------------+

## Open Risks:

- Production Strategy Replay over long YTD horizons can still be cold-start expensive; this is a performance follow-up, not an execution defect in the visible Rule100/YTD fix.
- Frozen Rule100 history still shows 10% audit semantics by design; a 35% historical UI-policy trace requires a separate versioned/labeled artifact.
- Live benchmark overlay remains display-only and provider-dependent; canonical QQQ backfill remains a separate ingestion decision.
- Broad inherited dirty/untracked worktree remains and was not reverted.

## Rollback Note:

Revert the Rule100/YTD changes in `strategies/rule100_softmax.py`, `strategies/strategy_replay.py`, `views/optimizer_view.py`, `core/data_orchestrator.py`, `dashboard.py`, the Rule100/replay/YTD tests, and matching docs/context updates. No canonical market-data artifact or frozen Rule100 history artifact needs rollback because none was rewritten for this scope.

Next action: manual_audit_rule100_visible_weights_and_qqq_ytd_then_hold_or_versioned_history_artifact

SAWBlockValidation: PASS
ClosureValidation: PASS
ClosurePacket: RoundID=20260513-rule100-ytd-visible-correctness; ScopeID=rule100-dynamic-ui-replay-sizing-benchmark-stale-overlay; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=production_replay_cold_start_cost_versioned_history_artifact_optional_canonical_benchmark_ingestion_deferred; NextAction=manual_audit_rule100_visible_weights_and_qqq_ytd_then_hold_or_versioned_history_artifact
