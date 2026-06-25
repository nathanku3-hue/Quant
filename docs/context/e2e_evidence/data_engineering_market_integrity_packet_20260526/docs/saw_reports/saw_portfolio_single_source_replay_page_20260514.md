# SAW Report - Portfolio Single-Source Replay Page - 2026-05-14

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Frontend/UI, Backend, Data, Docs/Ops

RoundID: 20260514-portfolio-single-source-replay-page-saw
ScopeID: portfolio-single-source-replay-page
SAW Verdict: BLOCK

## Scope And Ownership

Work round scope: make Portfolio & Allocation consume one daily forward-walk replay context across allocation snapshot, performance, timeline, ENTER/EXIT visualization, latest buys/sells, and Buy/Sell Decision Log.

Owned files changed in this round:

- `dashboard.py`
- `views/optimizer_view.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_optimizer_view.py`
- `tests/test_policy_target_timeline_apptest.py`
- `tests/test_position_lifecycle.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/*`

Acceptance checks:

- CHK-01: Portfolio page builds one daily `DashboardReplayContext` before replay-facing surfaces render.
- CHK-02: Portfolio Performance refuses non-daily replay and optimizer/local/live/equal-weight fallback.
- CHK-03: Strategy Replay Timeline sampling is display-only from daily replay rows.
- CHK-04: Allocation snapshot, performance, timeline, ENTER/EXIT Events, Latest Buys/Sells, and Buy/Sell Decision Log share replay identity.
- CHK-05: Duplicate Trade Event Log table is removed while ENTER/EXIT hover exposes date/ticker/action/weight/reason.
- CHK-06: Latest Buys/Sells is filtered from `bundle.decision_rows`, with no separate render-path loader/cache.
- CHK-07: Docs-as-code and context artifacts are updated.
- CHK-08: Runtime smoke reaches `/portfolio-and-allocation`.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Independent Reviewer A/B/C passes were not run as separate agents in this turn. | Carry as governance blocker; implementation evidence is passing but SAW cannot claim independent reviewer PASS. | Parent | Open |
| Medium | Backend production artifacts still need `dashboard_cache_signature` emission for saved-artifact UI hits. | Keep transitional build labeled; coordinate backend producer follow-up separately. | Backend | Open, out-of-scope |
| Low | Broad inherited dirty/untracked worktree remains visible. | Do not revert unrelated work; report as inherited state. | Parent | Open, inherited |

## Scope Split Summary

In-scope findings/actions:

- Implemented page-level daily replay coordinator.
- Removed Portfolio Performance fallback to optimizer/local/live/equal-weight evidence.
- Converted weekly timeline sampling to a display transform from daily rows.
- Replaced visible allocation evidence with latest daily replay snapshot.
- Removed duplicate Trade Event Log table.
- Added source-guard tests for render-path second-source reads.

Inherited out-of-scope findings/actions:

- Backend `dashboard_cache_signature` producer emission remains a separate coordination follow-up.
- Existing broad dirty/untracked files were not reverted.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/prd.md`, `docs/spec.md` | Added Portfolio single-source replay page notice. | Local evidence PASS; independent review pending |
| `docs/phase_brief/phase65-brief.md` | Added implementation invariant, evidence, and boundary. | Local evidence PASS; independent review pending |
| `docs/notes.md` | Added formulas/rules for daily replay page, sampling, and latest buys/sells. | Local evidence PASS; independent review pending |
| `docs/lessonss.md` | Added lesson on sampled views not being replay sources. | Local evidence PASS; independent review pending |
| `docs/decision log.md` | Added hardcoded contract lock for Portfolio single-source replay page. | Local evidence PASS; independent review pending |
| `docs/context/*` | Refreshed current truth surfaces and context packet. | Local evidence PASS; independent review pending |

Document Sorting: maintained according to `docs/checklist_milestone_review.md`.

## Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py tests\test_policy_target_timeline_apptest.py tests\test_position_lifecycle.py tests\test_strategy_replay.py tests\test_strategy_replay_artifact.py -q` -> PASS, 178 passed.
- `EVD-03`: Streamlit readiness smoke `http://127.0.0.1:8526/portfolio-and-allocation` -> PASS, HTTP 200.
- `EVD-04`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `EVD-05`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

## Closure Packet

ClosurePacket: RoundID=20260514-portfolio-single-source-replay-page-saw; ScopeID=portfolio-single-source-replay-page; ChecksTotal=8; ChecksPassed=7; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent_reviewer_A_B_C_passes_not_run; NextAction=run_independent_saw_reviewer_gate_or_accept_governance_risk

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Independent SAW reviewer passes are not complete, so formal SAW closure remains BLOCK.
- Backend artifact producer `dashboard_cache_signature` emission remains future work.
- Broad inherited dirty/untracked worktree remains present.

Next action:

- Run independent SAW Reviewer A/B/C gate, or explicitly accept governance risk for this implementation round before treating it as milestone-closed.
