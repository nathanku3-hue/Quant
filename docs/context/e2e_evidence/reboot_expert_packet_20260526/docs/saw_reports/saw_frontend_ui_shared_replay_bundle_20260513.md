# SAW Report - Frontend/UI Shared Replay Bundle - 2026-05-13

SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: SAW-20260513-FE-REPLAY-BUNDLE
ScopeID: frontend-ui-shared-replay-bundle

## Scope and Ownership

- Work round scope: rewire dashboard replay surfaces so selected-method replay rows, latest snapshot, YTD weights, ENTER/EXIT annotations, and Buy/Sell audit rows flow through one dashboard replay context.
- Owned files changed: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_policy_target_timeline_apptest.py`, `tests/test_position_lifecycle.py`, `tests/test_optimizer_view.py`, `docs/notes.md`, `docs/decision log.md`, `docs/phase_brief/phase65-brief.md`, current truth surfaces, `docs/lessonss.md`.
- Non-destructive constraint: no destructive commands, no strategy backend rewrites, no provider ingestion, no canonical market-data writes, no broker/live-trading behavior.
- Ownership check: Implementer = Worker 2 UI; Reviewer A = independent strategy-correctness pass; Reviewer B = independent runtime-resilience pass; Reviewer C = independent data/performance pass. Implementer and reviewers are different roles.

## Acceptance Checks

- CHK-01: one selected-method replay context exists for dashboard Strategy Replay.
- CHK-02: latest snapshot is derived from replay context.
- CHK-03: Portfolio YTD primes/prefers latest selected-method replay weights before legacy fallback.
- CHK-04: ENTER/EXIT annotations are supplied by context, not direct render-path lifecycle reads.
- CHK-05: Buy/Sell Decision Log is supplied by context, not direct render-path JSONL reads.
- CHK-06: cheap Buy/Sell audit surface renders before heavy replay build.
- CHK-07: focused compile passes.
- CHK-08: focused dashboard/optimizer tests pass.
- CHK-09: docs, decision log, truth surfaces, and lessons updated.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| Medium | Split-source annotations and Buy/Sell audit rows could disagree with selected-method replay output. | Added `DashboardReplayContext` and made render path consume context fields. | Worker 2 UI | Fixed |
| Medium | Portfolio YTD could still use legacy optimizer weights while Strategy Replay showed selected-method output. | Added latest replay snapshot priming before YTD and replay-weight preference in `_current_optimizer_weights()`. | Worker 2 UI | Fixed |
| Low | Full backend replay-output artifact/run id is not yet available. | Recorded as out-of-scope backend follow-up. | Backend replay owner | Open |

## Subagent Passes

- Implementer pass: PASS. Code implements one UI replay context and preserves existing backend replay API boundaries.
- Reviewer A pass: PASS. Strategy method/cap still flow through `build_strategy_replay(...)`; no new optimizer objective or Rule100 promotion semantics added.
- Reviewer B pass: PASS. Cheap audit data is loaded through cached context before full replay; failures remain fail-soft with empty/cash-closed surfaces.
- Reviewer C pass: PASS. Direct render-path lifecycle/compact JSONL reads are removed; source-guard tests lock the behavior.

## Scope Split Summary

- in-scope findings/actions: dashboard shared replay context, latest snapshot/YTD preference, annotation/audit context sourcing, focused tests, docs-as-code updates.
- inherited out-of-scope findings/actions: durable backend replay-output artifact/run id remains required for the complete ultra-modular replay architecture.

## Document Changes Showing

- `docs/notes.md`: added shared replay bundle behavior and evidence.
- `docs/decision log.md`: added hardcoded frontend shared replay bundle decision.
- `docs/phase_brief/phase65-brief.md`: added runtime slice addendum and boundary.
- `docs/context/bridge_contract_current.md`: refreshed PM/planner bridge delta.
- `docs/context/impact_packet_current.md`: refreshed changed files, touched interfaces, and tests.
- `docs/context/done_checklist_current.md`: added machine-checkable acceptance items.
- `docs/context/planner_packet_current.md`: added compact next-step packet.
- `docs/lessonss.md`: added replay-bundle guardrail.

## Document Sorting

- GitHub-optimized ordering follows `docs/checklist_milestone_review.md`: runtime/test evidence first, governance docs second, lessons and current truth surfaces last.

## Evidence

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_optimizer_view.py -q` -> PASS, 89 passed.

Open Risks:
- Full backend replay-output artifact/run id remains out of scope for Worker 2 and should be handled by the backend replay stream before final architecture closure.

Next action:
- Backend replay owner should add durable replay-output artifact/run id integration, or hold.

ClosurePacket: RoundID=SAW-20260513-FE-REPLAY-BUNDLE; ScopeID=frontend-ui-shared-replay-bundle; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_replay_output_artifact_run_id_pending; NextAction=backend_replay_output_artifact_or_hold
ClosureValidation: PASS
SAWBlockValidation: PASS
