# SAW Report - DASH-2 Portfolio Allocation Runtime Slice

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: 20260510-dash2-portfolio-return-saw  
ScopeID: DASH2-portfolio-allocation-runtime

## Scope

Work round scope: keep Portfolio Optimizer top-level on `Portfolio & Allocation`, place YTD Performance below it, calculate portfolio YTD return from optimizer weights, refresh selected stock and SPY/QQQ display prices, and update docs/tests.

Owned files changed in this round:
- `dashboard.py`
- `views/optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/saw_reports/saw_dash_2_portfolio_return_20260510.md`

Acceptance checks:
- CHK-01: Optimizer is top-level and appears before YTD.
- CHK-02: Portfolio YTD return uses current optimizer weights.
- CHK-03: Selected stock and benchmark prices refresh in-memory for display freshness.
- CHK-04: Focused tests, DASH-1 regression, compile, and browser check pass.
- CHK-05: Independent subagent implementer/reviewer ownership check passes.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| Medium | Independent SAW ownership could not be satisfied because this session forbids spawning subagents unless the user explicitly asks for them. | Published this BLOCK report with passing implementation evidence and explicit next action. | Parent Codex | Open |
| Low | yfinance freshness overlay is runtime display-only and could be overread as canonical ingestion. | Documented boundary in notes, decision log, truth surfaces, PRD, and spec. | Parent Codex | Closed |

## Scope Split Summary

in-scope findings/actions:
- Implemented optimizer-first ordering and removed optimizer expander/toggle.
- Added weighted portfolio return logic from current optimizer weights.
- Added in-memory adjusted-close freshness overlay for selected stocks and SPY/QQQ.
- Updated focused tests and docs-as-code surfaces.

inherited out-of-scope findings/actions:
- Broad dirty worktree remains inherited.
- Candidate-card dashboard reader, ranking/scoring, alerts, broker behavior, and provider ingestion remain out of scope.

## Document Changes Showing

| Path | Change summary | Reviewer status |
| --- | --- | --- |
| `dashboard.py` | YTD chart now follows optimizer and calculates weighted optimizer YTD return with SPY/QQQ comparison. | Locally reviewed |
| `views/optimizer_view.py` | Optimizer refreshes selected prices and stores current weights for downstream YTD logic. | Locally reviewed |
| `tests/test_dash_2_portfolio_ytd.py` | Updated tests for top-level optimizer, weighted return plumbing, and freshness helpers. | Locally reviewed |
| `docs/notes.md` | Added explicit return and freshness formulas. | Locally reviewed |
| `docs/decision log.md` | Added DASH-2 decision record and contract lock. | Locally reviewed |
| `docs/lessonss.md` | Added guardrail that primary workflows should not be hidden during cleanup. | Locally reviewed |
| `docs/prd.md` | Added product delta for Portfolio Allocation runtime slice. | Locally reviewed |
| `docs/spec.md` | Added runtime ordering, return formula, and freshness boundary. | Locally reviewed |
| `docs/context/*.md` | Added current DASH-2 runtime addenda. | Locally reviewed |

## Evidence

| Check | Evidence |
| --- | --- |
| CHK-01 | Browser snapshot: `Portfolio Optimizer` index 2141, `YTD Performance` index 5048, expander label absent. |
| CHK-02 | `tests/test_dash_2_portfolio_ytd.py` validates `_current_optimizer_weights`, `_build_portfolio_ytd_equity`, and `_weighted_equity_curve`. |
| CHK-03 | Browser snapshot shows SPY, QQQ, and `Stock prices refreshed through 2026-05-08 (optimized live)`. |
| CHK-04 | `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py -q` -> PASS, 22 passed; `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py` -> PASS. |
| CHK-05 | BLOCK: independent subagent ownership check not run due current tool policy. |

## Open Risks:

- Independent subagent SAW review did not run in this round because the current tool policy allows spawning only when the user explicitly asks for subagents.
- yfinance overlay is display freshness only and must not be promoted to canonical provider ingestion without a separate provider phase.

## Next action:

Request explicit subagent SAW review if milestone closure is required, or accept the local-review risk for this narrow runtime slice.

ClosurePacket: RoundID=20260510-dash2-portfolio-return-saw; ScopeID=DASH2-portfolio-allocation-runtime; ChecksTotal=5; ChecksPassed=4; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_subagent_review_not_run_due_tool_policy; NextAction=request_explicit_subagent_SAW_or_accept_local_review_risk

ClosureValidation: PASS
SAWBlockValidation: PASS
