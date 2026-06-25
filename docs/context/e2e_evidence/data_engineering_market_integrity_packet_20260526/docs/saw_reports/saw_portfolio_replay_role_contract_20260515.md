# SAW Report - Portfolio Replay Role Contract - 2026-05-15

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Backend/Strategy, Frontend/UI, Data, Docs/Ops

RoundID: 20260515-portfolio-replay-role-contract-saw
ScopeID: portfolio-replay-role-contract
SAW Verdict: PASS

## Scope And Ownership

Work round scope: make replay exposure truth mechanically distinguishable from lifecycle/event audit intent on Portfolio & Allocation.

Owned files changed in this round:

- `strategies/strategy_replay.py`
- `dashboard.py`
- `tests/test_strategy_replay.py`
- `tests/test_strategy_replay_artifact.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_dash_1_page_registry_shell.py`
- `tests/test_policy_target_timeline_apptest.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/*`
- `docs/saw_reports/saw_portfolio_replay_role_contract_20260515.md`

Acceptance checks:

- CHK-01: Replay, context, and selected-method artifact schemas carry `context_role` and `row_role`.
- CHK-02: Legacy role-less selected-method artifacts hydrate roles, while unrelated schema drift still fails closed.
- CHK-03: Dashboard context normalization delegates to `strategies.strategy_replay.normalize_context_frame_for_replay(...)`.
- CHK-04: Portfolio replay tables use role-aware labels and expose `Context Role`.
- CHK-05: Replay diagnostics are computed from `DashboardReplayContext`, bind replay identity, and do not rebuild/reread replay.
- CHK-06: Focused compile, affected replay/dashboard/AppTest suite, context validation, and SAW reviewer passes complete.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | No in-scope Critical/High findings after Implementer and Reviewer A/B/C review. | No fix required. | Implementer + Reviewers | PASS |
| Low | Reviewer C suggested extra tests proving diagnostics do not rebuild/reread replay and legacy compatibility only hydrates missing role columns. | Added targeted regressions and reran affected suite. | Codex | Closed |
| Low | Reviewer B noted route smoke should be rerun by parent because diagnostics can write an evidence JSON. | Parent reran AppTest route smoke in the affected suite; it passed with role-aware table assertions. | Codex | Closed |

## Scope Split Summary

In-scope findings/actions:

- Added durable role fields to replay/context/artifact schemas.
- Added backward-compatible hydration for older role-less selected-method artifacts.
- Kept unrelated artifact schema drift fail-closed.
- Centralized context normalization in strategy replay and made dashboard delegate to it.
- Renamed replay-facing visible weights to `Replay Weight`, `Current Weight`, `Replay Target`, and `Aux Audit Wt`.
- Added diagnostics from the existing `DashboardReplayContext` and role/diagnostic regressions.

Inherited out-of-scope findings/actions:

- Backend dashboard_cache_signature production and durable saved-artifact superset/subset policy remain separate follow-ups.
- Broad inherited dirty/untracked worktree remains present and was not reverted.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `PRD.md`, `PRODUCT_SPEC.md` | Added product/spec notice for durable replay role contract. | PASS |
| `docs/prd.md`, `docs/spec.md` | Added canonical product/spec notices for context-role semantics, shared normalization, and diagnostics boundary. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added role-contract phase addendum and final evidence. | PASS |
| `docs/notes.md` | Recorded schema, normalization, artifact compatibility, and diagnostic contract. | PASS |
| `docs/lessonss.md` | Added lesson that replay rows need durable role fields, not UI-copy semantics. | PASS |
| `docs/decision log.md` | Added hardcoded contract lock and evidence. | PASS |
| `docs/context/*` | Refreshed bridge, done checklist, impact, planner, multi-stream, alignment, observability, and current context. | PASS |

Document Sorting:

- Runtime/test changes first: `strategies/strategy_replay.py`, `dashboard.py`, and focused tests.
- Product/spec notices next: `PRD.md`, `PRODUCT_SPEC.md`, `docs/prd.md`, `docs/spec.md`.
- Phase brief and governance notes after runtime evidence.
- Context packets and SAW report last for GitHub discoverability.

## Subagent Results

- Implementer: PASS; validated implementation completeness and docs with no file edits.
- Reviewer A: PASS; confirmed strategy semantics and no policy drift.
- Reviewer B: PASS; confirmed runtime fail-soft behavior, old artifact compatibility, diagnostic write safety, and parent route-smoke need.
- Reviewer C: PASS; confirmed diagnostics are post-processing, no diagnostic rebuild/reread, and artifact fail-closed behavior.
- Ownership check: PASS; Implementer and Reviewers A/B/C were different agents.

## Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile strategies\strategy_replay.py dashboard.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_strategy_replay_artifact.py::test_read_selected_method_replay_artifact_hydrates_legacy_role_columns tests\test_strategy_replay_artifact.py::test_read_selected_method_replay_artifact_rejects_legacy_plus_unrelated_missing_column tests\test_dash_2_portfolio_ytd.py::test_dash_2_replay_context_diagnostics_do_not_rebuild_or_reread -q` -> PASS, 3 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py tests\test_policy_target_timeline_apptest.py -q` -> PASS, 169 passed.
- `EVD-04`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `EVD-05`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `EVD-06`: SE evidence validation -> PASS.
- `EVD-07`: Implementer and Reviewer A/B/C passes -> PASS.

## Closure Packet

ClosurePacket: RoundID=20260515-portfolio-replay-role-contract-saw; ScopeID=portfolio-replay-role-contract; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_dashboard_cache_signature_saved_artifact_policy_followup_out_of_scope; NextAction=hold_or_continue_backend_dashboard_cache_signature_policy

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Backend dashboard_cache_signature/saved-artifact policy remains future work.
- Broad inherited dirty/untracked worktree remains present.

Next action:

- Hold, or continue backend dashboard_cache_signature / saved-artifact policy work.
