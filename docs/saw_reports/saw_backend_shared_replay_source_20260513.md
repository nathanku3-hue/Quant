# SAW Backend Shared Replay Source + Evidence Docs - 2026-05-13

RoundID: R20260513-selected-method-replay-evidence-docs
ScopeID: selected-method-replay-source-evidence-docs
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

SAW Verdict: PASS

## Scope

Work round scope: backend shared replay source plus Evidence/Docs handoff for selected-method replay output, dashboard context consumption, timeframe/PIT rule, latest-trades UX rule, performance/rollback notes, and open risks.

Owned files changed in this round:
- `strategies/strategy_replay.py`
- `dashboard.py`
- `tests/test_strategy_replay.py`
- `tests/test_strategy_replay_artifact.py`
- `tests/test_replay_non_cash_closed.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`
- `tests/test_position_lifecycle.py`
- `tests/test_policy_target_timeline_apptest.py`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/saw_reports/saw_backend_shared_replay_source_20260513.md`

Acceptance checks:
- CHK-01: Single backend public API exists for selected-method replay output.
- CHK-02: Replay output returns target-weight rows plus CASH for every replay date.
- CHK-03: Replay bundle exposes PIT-filtered event/annotation and buy/sell/decision context, or explicit empty context with status/reason.
- CHK-04: Performance/YTD can be derived from replay output without optimizer session weights.
- CHK-05: Rule100 and non-Rule100 methods share one output schema.
- CHK-06: Missing/failed replay dates emit `cash_closed` and do not carry stale weights.
- CHK-07: Dashboard replay surfaces consume one `DashboardReplayContext` for replay rows, latest snapshot, annotations, and Buy/Sell audit rows.
- CHK-08: Portfolio Performance primes latest selected-method replay weights before legacy optimizer fallback.
- CHK-09: Timeframe/PIT rule is documented: UI horizons do not weaken per-date PIT loading.
- CHK-10: Latest-trades-default UX rule is documented: Buy/Sell audit rows sort latest-first and remain non-actionable.
- CHK-11: Performance and rollback notes are documented.
- CHK-12: Durable selected-method replay-output artifact/run id is implemented with rollback-safe parquet+manifest promotion.
- CHK-13: Open risks are carried without claiming full architecture/phase PASS.

## Subagent Passes

Implementer pass: PASS. `build_selected_method_replay(...)` wraps `build_strategy_replay(...)`, returns a typed bundle with one shared replay frame, and the Evidence/Docs handoff records the implemented invariant without claiming full phase closure.

Reviewer A - strategy correctness and regression risks: PASS. Rule100 remains an adapter, optimizer methods still route through existing diagnostics, and failed replay dates remain `cash_closed` instead of stale carried-forward weights.

Reviewer B - runtime and operational resilience: PASS. Focused backend tests, dashboard replay/YTD tests, and scoped compile pass after source guards were aligned to delegated replay context construction.

Reviewer C - data integrity and performance path: PASS. Replay rows include per-date return/equity fields derived from PIT price/return inputs; docs preserve the requirement for `end_date=as_of_date`, `universe_mode="r3000_pit"`, latest-first audit display, and rollback-safe saved-artifact output.

Ownership check: PASS. Implementer and Reviewer A/B/C are recorded as distinct SAW roles; Evidence/Docs did not revert or overwrite unrelated dirty work.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| Low | Dashboard context still calls `build_strategy_replay(...)` directly rather than consuming `build_selected_method_replay(...)` end to end. | Carry as next integration slice or explicitly accept as bounded bridge. | Frontend/UI + Backend | open |
| Low | Full repository pytest and runtime smoke were not rerun by Evidence/Docs. | Keep focused evidence only; require full regression/smoke before phase-close. | QA/Ops | open |

## Scope Split Summary

In-scope findings/actions: replay bundle API, shared schema, CASH rows, PIT context filtering, performance fields, durable artifact/run id, rollback-safe parquet+manifest promotion, dashboard shared context, latest snapshot/YTD preference, timeframe/PIT documentation, latest-trades UX documentation, rollback notes, and focused tests are complete.

Inherited out-of-scope findings/actions: end-to-end dashboard consumption of backend bundle API, full repository regression, runtime smoke, and same-window/same-cost/same-engine promotion deltas remain outside this Evidence/Docs ownership.

## Document Changes Showing

- `docs/phase_brief/phase65-brief.md`: added combined selected-method replay evidence handoff, timeframe/PIT rule, latest-trades UX rule, rollback, and risks. Reviewer status: PASS.
- `docs/notes.md`: added formulas and implementation paths for backend bundle, dashboard context, performance derivation, PIT loading, latest snapshot/YTD, and latest-trades UX. Reviewer status: PASS.
- `docs/decision log.md`: recorded selected-method replay source evidence handoff and open risks. Reviewer status: PASS.
- `docs/lessonss.md`: added lesson for fragmented replay evidence docs after parallel workers. Reviewer status: PASS.
- `docs/context/bridge_contract_current.md`: added PM/planner bridge for implemented bounded source path and next step. Reviewer status: PASS.
- `docs/context/impact_packet_current.md`: added changed governance files, touched interfaces, checks, and risks. Reviewer status: PASS.
- `docs/context/done_checklist_current.md`: added machine-checkable implemented/open replay-source items. Reviewer status: PASS.
- `docs/context/planner_packet_current.md`: added compact next-entry truth for replay source handoff. Reviewer status: PASS.
- `docs/context/multi_stream_contract_current.md`: added stream status for Backend/Strategy, Frontend/UI, Data, and Docs/Ops. Reviewer status: PASS.
- `docs/context/post_phase_alignment_current.md`: added multi-stream alignment and bottleneck update. Reviewer status: PASS.
- `docs/context/observability_pack_current.md`: added drift signals for artifact/run-id, display horizons, latest-trades UX, and stale carry-forward. Reviewer status: PASS.
- `docs/saw_reports/saw_backend_shared_replay_source_20260513.md`: updated SAW result to include Evidence/Docs handoff. Reviewer status: PASS.

## Document Sorting

Canonical ordering follows `docs/checklist_milestone_review.md`: runtime/API changes, tests/evidence, docs/decision, lessons, context surfaces, SAW report.

## Evidence

- EVD-01: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q` -> PASS, 27 passed.
- EVD-02: `.venv\Scripts\python -m pytest tests\test_replay_non_cash_closed.py -q` -> PASS, 2 passed.
- EVD-03: `.venv\Scripts\python -m py_compile strategies\strategy_replay.py core\data_orchestrator.py scripts\build_strategy_replay_artifact.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py` -> PASS.
- EVD-04: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- EVD-05: `.venv\Scripts\python -m py_compile strategies\strategy_replay.py dashboard.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- EVD-06: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py -q` -> PASS, 29 passed.
- EVD-07: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 89 passed.
- EVD-08: `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py -q` -> PASS, 16 passed, including manifest-failure rollback regression.
- EVD-09: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_replay_non_cash_closed.py -q` -> PASS, 21 passed.

## Open Risks:

- Dashboard context still does not consume backend `build_selected_method_replay(...)` end to end.
- Full repository pytest and runtime smoke remain pending for phase-close proof.
- Same-window/same-cost/same-engine baseline deltas are still required before any promotion claim.

Next action: Frontend/UI should consume the backend selected-method bundle end to end, followed by full regression and runtime smoke.

ClosurePacket: RoundID=R20260513-selected-method-replay-evidence-docs; ScopeID=selected-method-replay-source-evidence-docs; ChecksTotal=13; ChecksPassed=13; ChecksFailed=0; Verdict=PASS; OpenRisks=dashboard_backend_bundle_integration_pending,full_regression_runtime_smoke_pending; NextAction=dashboard_backend_bundle_integration_then_full_regression_runtime_smoke

ClosureValidation: PASS

SAWBlockValidation: PASS
