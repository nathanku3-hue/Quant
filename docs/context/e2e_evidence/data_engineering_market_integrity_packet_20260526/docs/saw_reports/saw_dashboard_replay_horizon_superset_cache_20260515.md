# SAW Report - Dashboard Replay Horizon Superset Cache - 2026-05-15

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Frontend/UI, Backend, Data, Docs/Ops

RoundID: 20260515-dashboard-replay-horizon-superset-cache
ScopeID: frontend-ui-replay-cache
SAW Verdict: PASS

## Scope And Ownership

Work round scope: diagnose and fix why switching Portfolio replay from a wider horizon such as `Max` to a shorter horizon such as `1Y` rebuilt the daily portfolio replay source instead of reusing the already-built daily replay rows.

Owned files changed in this round:

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/*`
- `docs/saw_reports/saw_dashboard_replay_horizon_superset_cache_20260515.md`

Acceptance checks:

- CHK-01: `_ensure_daily_portfolio_replay_context(...)` checks valid cached daily replay before entering the spinner/build path.
- CHK-02: In-session superset reuse ignores only `replay_dates` while requiring method, cap, controls, signed assets, sampling, and data signature to match.
- CHK-03: Exact and superset cache reuse both prove requested dates exist in actual `replay_df["date"]` rows.
- CHK-04: Reused contexts are scoped to the selected horizon before rendering replay rows, latest snapshot, events, decisions, and date window.
- CHK-05: Saved replay artifacts remain exact `dashboard_cache_signature` consumers.
- CHK-06: Focused compile and targeted superset-cache regressions pass.
- CHK-07: Focused Portfolio/YTD dashboard file and optimizer/replay coverage follow-up tests pass.
- CHK-08: Context packet rebuild and validation pass after docs updates.
- CHK-09: Independent SAW Implementer and Reviewer A/B/C passes complete with different agents.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Cache validation scans cached replay dates and replay frame dates on reuse; this is linear in cached rows but replaces a much heavier PIT replay rebuild. | Keep helper scans bounded to in-session daily contexts; revisit if Max replay row counts become visibly slow. | Frontend/UI | Accepted |
| Medium | Durable saved artifacts still require exact `dashboard_cache_signature`, so a 5Y/Max artifact cannot yet satisfy shorter windows across sessions. | Carry as a separate backend/dashboard saved-artifact superset/subset policy with reader tests. | Backend + Frontend/UI | Open, out-of-scope |
| Low | Broad inherited dirty/untracked worktree remains visible. | Do not revert unrelated work; report as inherited state. | Parent | Open, inherited |

## Scope Split Summary

In-scope findings/actions:

- Added cache validation before `_ensure_daily_portfolio_replay_context(...)` enters `Building daily portfolio replay source...`.
- Added non-date replay signature comparison for in-session superset reuse.
- Required requested dates to exist in both cached context metadata and actual daily replay rows.
- Returned a horizon-scoped `DashboardReplayContext` so a shorter UI horizon does not render the wider replay timeline.
- Added focused regressions for superset reuse, missing requested dates, and no-build cache return.

Inherited out-of-scope findings/actions:

- Durable saved-artifact superset/subset acceptance remains future backend/dashboard policy.
- Backend `dashboard_cache_signature` producer emission remains a separate coordination follow-up.
- Existing broad dirty/untracked files were not reverted.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/phase_brief/phase65-brief.md` | Added invariant, evidence, and boundary for in-session replay horizon superset cache reuse. | PASS |
| `docs/notes.md` | Added diagnosis, cache reuse rule, scoping rule, boundary, and evidence. | PASS |
| `docs/lessonss.md` | Added lesson separating durable artifact identity from in-session superset reuse. | PASS |
| `docs/decision log.md` | Added hardcoded contract lock for dashboard replay horizon superset cache. | PASS |
| `docs/context/*` | Refreshed current truth surfaces and generated current context packet. | PASS |
| `docs/saw_reports/saw_dashboard_replay_horizon_superset_cache_20260515.md` | Published SAW reconciliation report for this round. | PASS |

Document Sorting: maintained according to `docs/checklist_milestone_review.md`.

## Subagent Results

- Implementer: PASS; confirmed cache check before spinner/build, date-stripped identity matching, actual row coverage, horizon scoping, and saved-artifact exact boundary.
- Reviewer A: PASS; confirmed PIT correctness, method/control/asset identity, stale replay risk, and scoped-context semantics.
- Reviewer B: PASS; confirmed runtime resilience, stale cache clearing, exact/superset branch behavior, and no-build test coverage.
- Reviewer C: PASS; confirmed data integrity, event/decision scoping, daily-source-only behavior, and performance tradeoff.
- Ownership check: PASS; Implementer and Reviewers A/B/C were separate agents.

## Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `EVD-02`: targeted superset-cache regressions -> PASS, 3 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 56 passed.
- `EVD-04`: `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay_coverage.py -q` -> PASS, 50 passed.
- `EVD-05`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_strategy_replay_coverage.py -q` -> PASS, 106 passed.
- `EVD-06`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `EVD-07`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

## Closure Packet

ClosurePacket: RoundID=20260515-dashboard-replay-horizon-superset-cache; ScopeID=frontend-ui-replay-cache; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=durable_saved_artifact_superset_policy_future_followup; NextAction=hold_or_coordinate_backend_dashboard_cache_signature_emission_and_saved_artifact_superset_policy

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Durable saved-artifact superset/subset acceptance remains future backend/dashboard policy.
- Backend artifact producer `dashboard_cache_signature` emission remains future work.
- Broad inherited dirty/untracked worktree remains present.

Next action:

- Hold, or coordinate backend `dashboard_cache_signature` emission plus a separate durable saved-artifact superset/subset policy.
