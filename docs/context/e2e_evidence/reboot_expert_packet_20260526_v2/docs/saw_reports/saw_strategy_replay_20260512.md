# SAW Strategy Replay 2026-05-12

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: reviewer-only-recheck | Domains: Backend, Strategy | FallbackSource=docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: R-20260512-strategy-replay
ScopeID: backend-strategy-replay

## Scope

Work round scope: Backend/Strategy method-aware PIT allocation replay for every `OPTIMIZATION_METHOD_OPTIONS` method.

Owned files changed in this round:

- `strategies/strategy_replay.py`
- `tests/test_strategy_replay.py`
- `docs/lessonss.md`
- `docs/saw_reports/saw_strategy_replay_20260512.md`

Acceptance checks:

- CHK-01: `build_strategy_replay(...)` emits required columns and one asset row plus CASH per replay date.
- CHK-02: every `OPTIMIZATION_METHOD_OPTIONS` method returns replay rows.
- CHK-03: replay uses only data available at or before each replay date.
- CHK-04: CASH residual equals `1 - gross target_weight`.
- CHK-05: `max_weight=0.35` flows to supported optimizer methods and Rule100 replay cap while Rule100 frozen audit cap remains separate.
- CHK-06: optimizer fallback/exception fails closed to CASH per date and does not reuse stale weights.
- CHK-07: Rule100 replay rejects undated candidate frames and requires price availability as of replay date.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Rule100 undated candidate frame could leak current/future candidate state into historical replay. | Required `date` in Rule100 candidate frames and added cash-closed regression. | Backend/Strategy worker | Fixed; Reviewer A/B/C PASS |
| High | Rule100 could allocate to a name with no price history available as of replay date. | Restricted Rule100 asset lookup to non-null price history at or before each replay date and added regression. | Backend/Strategy worker | Fixed; Reviewer C PASS |
| High | Optimizer exceptions propagated instead of producing `cash_closed` rows. | Wrapped per-date optimizer calls and added exception-to-cash regression. | Backend/Strategy worker | Fixed; Implementer/Reviewer B PASS |
| Medium | Near-overallocated accepted optimizer vectors could create tiny negative CASH. | Normalized tiny `gross > 1.0` vectors and clamped cash residual non-negative. | Backend/Strategy worker | Fixed; Reviewer A PASS |
| Medium | Malformed `as_of_range` tuple could raise and scalar strings were treated as iterables. | Added fail-closed tuple parsing and single-string date handling with regressions. | Backend/Strategy worker | Fixed; Reviewer B PASS |
| Low | CASH row could hide failure reason behind `cash_residual`. | Preserved failure reason when row status is `cash_closed`. | Backend/Strategy worker | Fixed; Reviewer B PASS |

## Scope Split Summary

in-scope findings/actions:

- Implemented `strategies.strategy_replay.build_strategy_replay(...)`.
- Added focused replay tests for method coverage, PIT slicing, CASH residuals, cap propagation, failure-to-cash, malformed inputs, and Rule100 PIT guards.
- Appended a self-learning guardrail entry to `docs/lessonss.md`.

inherited out-of-scope findings/actions:

- Broad dirty/untracked worktree predates this worker round and was not reverted.
- No provider ingestion, live trading, broker calls, alerts, ranking/scoring, or new optimizer objective was added.
- Phase-level PRD/Product Spec/decision-log refresh remains parent-orchestrator scope because this worker was assigned backend/test ownership only.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `strategies/strategy_replay.py` | New method-aware PIT replay API with optimizer routing, Rule100 replay, required CASH rows, cap metadata, and fail-closed statuses. | PASS |
| `tests/test_strategy_replay.py` | New focused unit coverage for all methods, PIT slicing, CASH residuals, cap flow, Rule100 date/price guards, optimizer fallback/exception, malformed dates, and negative-cash prevention. | PASS |
| `docs/lessonss.md` | Added replay guardrail entry for per-date fail-closed behavior. | PASS |
| `docs/saw_reports/saw_strategy_replay_20260512.md` | SAW reconciliation and validation artifact for this worker round. | PASS |

## Document Sorting

GitHub-optimized document order maintained for reported docs:

1. `docs/lessonss.md`
2. `docs/saw_reports/saw_strategy_replay_20260512.md`

## Evidence

- EVD-01: `.venv\Scripts\python -m py_compile strategies\strategy_replay.py tests\test_strategy_replay.py` -> PASS.
- EVD-02: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_optimizer_core_policy.py -q` -> PASS, 29 passed.
- EVD-03: SAW Implementer recheck -> PASS, 7/7.
- EVD-04: SAW Reviewer A recheck -> PASS, 6/6.
- EVD-05: SAW Reviewer B recheck -> PASS, 5/5.
- EVD-06: SAW Reviewer C recheck -> PASS, 6/6.
- EVD-07: SE evidence validator -> VALID.
- EVD-08: Closure packet validator -> VALID.

## Closure

ChecksTotal: 7
ChecksPassed: 7
ChecksFailed: 0
Open Risks: none in current worker scope. Inherited dirty/untracked files remain out of scope.
Next action: parent_orchestrator_review

ClosurePacket: RoundID=R-20260512-strategy-replay; ScopeID=backend-strategy-replay; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=None; NextAction=parent_orchestrator_review

ClosureValidation: PASS

SAWBlockValidation: PASS
