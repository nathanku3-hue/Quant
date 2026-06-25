# SAW Report - Dashboard Replay Horizon-Aware Asset Universe Fix

SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: SAW-DASH-REPLAY-HORIZON-ASSET-20260515
ScopeID: dashboard-replay-horizon-aware-asset-universe-fix

Scope: keep Portfolio & Allocation single-source while separating current allocation assets from selected-horizon historical replay context assets.

Acceptance Checks:

- CHK-01: Replay request keeps current allocation assets separate from horizon context assets.
- CHK-02: MU BUY/SELL history remains in the single bundle without becoming a latest positive-weight holding.
- CHK-03: Selected PIT loading and coverage pre-gate rows use allocation assets only.
- CHK-04: Cache signatures distinguish context-only replay assets from allocatable assets.
- CHK-05: Focused dashboard/replay tests and context validation pass.

Findings Table:

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | History-only MU could enter non-Rule100 optimizer allocation when widened replay assets were also used for PIT/optimizer inputs. | Added `DashboardReplayRequest.allocation_assets`, used it for selected PIT loading and input filtering, and appended history names only as zero-weight `context_only` rows after bundle construction. | Codex | Closed |
| High | Coverage pre-gate could emit full PIT membership rows before dashboard asset filtering. | Added `_dashboard_filter_coverage_plan_to_assets(...)` and regression proving extra PIT member `99999` is excluded. | Codex | Closed |
| High | Cache signatures could reuse the same widened replay union after a context-only ticker became allocatable. | Added `allocation_assets` to `_strategy_replay_cache_signature(...)` and regression for same `replay_assets` union with different allocation assets. | Codex | Closed |
| Low | Durable saved-artifact horizon superset/subset matching remains exact-signature only. | Carried as future backend/dashboard policy. | Backend/Dashboard future | Open |

Scope Split Summary:

- In-scope actions: dashboard request construction, allocation/context asset split, context-only replay rows, coverage filtering, cache signature identity, focused regressions, docs/truth surfaces.
- Inherited out-of-scope actions: durable saved-artifact superset/subset policy and production artifact producer `dashboard_cache_signature` coordination.

Document Changes Showing:

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `dashboard.py` | Added allocation/context asset split, context-only rows, coverage filtering, and cache identity. | PASS after Reviewer A/C recheck |
| `tests/test_dash_2_portfolio_ytd.py` | Added MU history retention, real optimizer exclusion, coverage prefilter, and cache-signature regressions. | PASS |
| `tests/test_optimizer_view.py` | Updated source guard to require selected PIT loading from `request.allocation_assets`. | PASS |
| `docs/notes.md` | Recorded formula/contract and evidence. | PASS |
| `docs/decision log.md` | Added contract lock for horizon-aware replay asset universe. | PASS |
| `docs/lessonss.md` | Added self-learning guardrail for separating allocation and horizon context identities. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added phase addendum and evidence. | PASS |
| `docs/context/*` | Refreshed planner, bridge, impact, done, alignment, observability, current context. | PASS |

Document Sorting:

- Runtime/test changes first: `dashboard.py`, `tests/test_dash_2_portfolio_ytd.py`, `tests/test_optimizer_view.py`.
- Governance/docs changes after runtime evidence: `docs/notes.md`, `docs/decision log.md`, `docs/lessonss.md`, `docs/phase_brief/phase65-brief.md`, `docs/context/*`.
- SAW report stored under `docs/saw_reports/` for GitHub discoverability.

Evidence:

- `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_replay_request_expands_assets_for_horizon_trade_history tests\test_dash_2_portfolio_ytd.py::test_dash_2_context_only_horizon_asset_does_not_enter_real_optimizer tests\test_dash_2_portfolio_ytd.py::test_dash_2_coverage_prefilter_uses_allocation_assets_not_full_pit_membership tests\test_dash_2_portfolio_ytd.py::test_dash_2_cache_signature_distinguishes_allocation_assets_from_context_assets -q` -> PASS, 4 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 61 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_strategy_replay.py tests\test_strategy_replay_coverage.py -q` -> PASS, 71 passed.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Implementer PASS; Reviewer B PASS; Reviewer C PASS after recheck; Reviewer A PASS after cache-signature recheck.

Open Risks:

- Durable saved-artifact horizon superset/subset reuse remains future policy and still requires exact `dashboard_cache_signature` today.
- Broad inherited dirty/untracked worktree remains present and was not reverted.

Next action: hold_or_saved_artifact_policy_followup

ClosurePacket: RoundID=SAW-DASH-REPLAY-HORIZON-ASSET-20260515; ScopeID=dashboard-replay-horizon-aware-asset-universe-fix; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS; OpenRisks=durable_saved_artifact_superset_subset_policy_future_followup; NextAction=hold_or_saved_artifact_policy_followup

ClosureValidation: PASS
SAWBlockValidation: PASS

