# SAW Report - Portfolio Market-Data Freshness Fail-Closed Fix

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Data, Frontend/UI, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: SAW-20260514-MARKET-DATA-FRESHNESS
ScopeID: portfolio_market_data_freshness_fail_closed

## Scope

Fix stale partial market-data handling across benchmark YTD, portfolio YTD, optimizer selected-price prep, optimizer default ordering, and optimizer universe eligibility.

## Acceptance Checks

- CHK-01: Per-column price endpoint helpers exist and are used for freshness filtering.
- CHK-02: Benchmark YTD drops unresolved stale benchmark columns and reports a common endpoint.
- CHK-03: Portfolio YTD local fallback fails closed when a nonzero weighted leg is stale.
- CHK-04: Optimizer selected-price prep drops stale selected assets that cannot be refreshed.
- CHK-05: Optimizer default ordering demotes stale endpoint assets.
- CHK-06: Optimizer universe eligibility rejects stale endpoints even with sufficient history observations.
- CHK-07: Focused and broader affected tests pass.
- CHK-08: SAW Implementer and Reviewer A/B/C passes complete with different agents.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | Rerun completed with Implementer, Reviewer A, Reviewer B, and Reviewer C all PASS; no in-scope Critical/High findings remain. | No fix required. | Parent SAW reconciler | PASS |
| Low | Broad inherited dirty/untracked worktree remains present, so reviewers preserved scope split and did not claim clean-diff attribution. | Carry as advisory only; do not revert unrelated files. | Repo owners | Open advisory |
| Low | Saved replay artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work. | Keep deferred outside this non-phase-close freshness fix. | Future replay/perf owner | Open advisory |

## Scope Split Summary

In-scope actions completed:

- Added endpoint freshness helpers and filters.
- Dropped unresolved stale benchmark columns.
- Made weighted local portfolio YTD unavailable on stale nonzero legs.
- Dropped stale selected optimizer assets before optimization.
- Added no-overlap live-overlay regression coverage so stale selected history ending `2026-02-27` cannot be scaled to live data starting `2026-05-01` as evidence.
- Demoted stale endpoint assets in default ordering.
- Excluded stale endpoint assets in universe eligibility.
- Reran independent SAW Implementer and Reviewer A/B/C passes after provider capacity returned.

Inherited out-of-scope findings/actions:

- Saved replay artifact-reader consumption and explicit cold-start/rerun performance budget remain future work.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Document Changes Showing

- `PRD.md` - added freshness fail-closed product notice - reviewer status: PASS after rerun.
- `PRODUCT_SPEC.md` - added implementation contract notice - reviewer status: PASS after rerun.
- `docs/prd.md` - mirrored product notice - reviewer status: PASS after rerun.
- `docs/spec.md` - added endpoint freshness technical contract - reviewer status: PASS after rerun.
- `docs/phase_brief/phase65-brief.md` - added current addendum and evidence - reviewer status: PASS after rerun.
- `docs/notes.md` - added formula/logic notes - reviewer status: PASS after rerun.
- `docs/lessonss.md` - added self-learning entry - reviewer status: PASS after rerun.
- `docs/decision log.md` - added decision/contract lock - reviewer status: PASS after rerun.
- `docs/context/*.md` - refreshed planner, bridge, impact, done, stream, alignment, and observability surfaces - reviewer status: PASS after rerun.

## Document Sorting

1. `docs/prd.md`, `docs/spec.md`
2. `docs/phase_brief/phase65-brief.md`
3. `docs/notes.md`, `docs/lessonss.md`, `docs/decision log.md`
4. `docs/context/bridge_contract_current.md`
5. `docs/context/done_checklist_current.md`
6. `docs/context/impact_packet_current.md`
7. `docs/context/multi_stream_contract_current.md`
8. `docs/context/post_phase_alignment_current.md`
9. `docs/context/observability_pack_current.md`
10. `docs/context/planner_packet_current.md`

## Verification Evidence

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py views\optimizer_view.py strategies\portfolio_universe.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py::test_scale_live_overlay_to_local_requires_overlap tests\test_data_orchestrator_portfolio_runtime.py::test_refresh_selected_prices_drops_no_overlap_live_overlay_asset -q` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py --disable-warnings` -> PASS, 110 passed.
- Parent reconciliation rerun: `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py --disable-warnings` -> PASS, 112 passed.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_portfolio_universe.py tests\test_position_lifecycle.py tests\test_policy_target_timeline_apptest.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_replay_non_cash_closed.py -q` -> PASS, 171 passed.

## Independent SAW Rerun

- Implementer: Newton (`019e2614-c0f8-7f61-917b-95fc5fce8196`) -> PASS; affected suite PASS, 112 passed.
- Reviewer A: Russell (`019e2614-c156-73d2-8da1-a250a46850c2`) -> PASS; no in-scope Critical/High strategy correctness findings.
- Reviewer B: Leibniz (`019e2614-c1ab-7642-b415-0dd2274cce94`) -> PASS; no in-scope Critical/High runtime/ops findings.
- Reviewer C: Maxwell (`019e2614-c205-7671-8c92-6facb0e4ee46`) -> PASS; no in-scope Critical/High data integrity/performance findings.
- Ownership check: PASS; implementer and reviewers were different agents.

## Closure

ChecksTotal: 8
ChecksPassed: 8
ChecksFailed: 0

Open Risks:

- Advisory: broad inherited dirty/untracked worktree remains present and was not reverted.
- Advisory: saved replay artifact-reader consumption and explicit cold-start/rerun performance budget remain future architecture work.
- Full repository pytest/runtime smoke are not claimed as phase-close evidence for this non-phase-close fix.

Next action:

- Hold, or separately approve replay-state hygiene / saved replay artifact-reader performance-budget work.

ClosurePacket: RoundID=SAW-20260514-MARKET-DATA-FRESHNESS; ScopeID=portfolio_market_data_freshness_fail_closed; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=advisory_dirty_worktree_and_future_saved_artifact_reader_performance_budget; NextAction=hold_or_separately_approve_replay_state_hygiene_or_saved_replay_artifact_reader_budget

ClosureValidation: PASS
SAWBlockValidation: PASS
