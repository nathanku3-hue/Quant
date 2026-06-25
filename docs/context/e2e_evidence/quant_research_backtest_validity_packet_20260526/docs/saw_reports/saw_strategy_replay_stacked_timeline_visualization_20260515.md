# SAW Report - Strategy Replay Stacked Timeline Visualization - 2026-05-15

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Frontend/UI, Backend/Strategy, Data, Docs/Ops

RoundID: 20260515-strategy-replay-stacked-timeline-saw
ScopeID: strategy-replay-stacked-timeline-visualization
SAW Verdict: PASS

## Scope And Ownership

Work round scope: make the Strategy Replay Timeline visualization executable and review-gated as a stacked step-area allocation chart over replay `target_weight`.

Owned files changed in this round:

- `tests/test_dash_2_portfolio_ytd.py`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/current_context.json`
- `docs/context/current_context.md`
- `docs/saw_reports/saw_strategy_replay_stacked_timeline_visualization_20260515.md`

Acceptance checks:

- CHK-01: Strategy Replay Timeline renders replay `target_weight` as stacked allocation traces.
- CHK-02: Plotly traces use `stackgroup="weights"` and `line.shape="hv"` with no markers.
- CHK-03: `CASH` is appended last and visually muted when present.
- CHK-04: Timeline display remains separate from Portfolio Performance.
- CHK-05: Executable Plotly trace regression covers the rendered figure, not only source text.
- CHK-06: Focused compile and dashboard timeline tests pass.
- CHK-07: Focused Portfolio/YTD dashboard file passes.
- CHK-08: Independent SAW Implementer and Reviewer A/B/C passes complete with different agents.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| None | No in-scope Critical/High findings. Stacked timeline uses `target_weight`, step-area Plotly traces, and marker-free allocation display. | No fix required. | Implementer | PASS |
| None | Visualization remains display-only and does not alter replay semantics, PIT identity, current allocation semantics, or Portfolio Performance source. | No fix required. | Reviewer A | PASS |
| None | Empty/malformed schemas, non-numeric weights, blank tickers, and malformed dates fail soft or sanitize before Plotly rendering. | No fix required. | Reviewer B | PASS |
| None | Chart path copies input, pivots only for display, keeps `CASH` coherent, and has no material performance regression for sampled timelines. | No fix required. | Reviewer C | PASS |

## Scope Split Summary

In-scope findings/actions:

- Added executable Plotly trace coverage for stacked `hv` allocation traces, marker-free mode, fixed 0-100% y-axis, and `CASH` ordering.
- Refreshed docs/context evidence to call out rendered-figure validation.
- Re-ran focused compile, targeted timeline tests, and full Portfolio/YTD dashboard tests.

Inherited out-of-scope findings/actions:

- Backend artifact producer `dashboard_cache_signature` emission remains a separate saved-artifact policy follow-up.
- Broad inherited dirty/untracked worktree remains present and was not reverted.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/notes.md` | Added rendered Plotly trace validation to stacked timeline evidence. | PASS |
| `docs/lessonss.md` | Added lesson that visualization behavior needs rendered-figure assertions when trace semantics matter. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added latest dashboard-file evidence and executable Plotly trace coverage. | PASS |
| `docs/context/bridge_contract_current.md` | Updated test delta with executable Plotly trace validation and latest focused dashboard result. | PASS |
| `docs/context/done_checklist_current.md` | Added machine-check item for executable Plotly trace regression. | PASS |
| `docs/context/impact_packet_current.md` | Added targeted trace validation and focused dashboard-file evidence. | PASS |
| `docs/context/multi_stream_contract_current.md` | Added Frontend/UI must-deliver trace coverage guardrail. | PASS |
| `docs/context/observability_pack_current.md` | Added drift signal for rendered Plotly trace test. | PASS |
| `docs/context/planner_packet_current.md` | Updated current packet test delta and done summary. | PASS |
| `docs/context/post_phase_alignment_current.md` | Added alignment note for rendered trace coverage. | PASS |
| `docs/context/current_context.json`, `docs/context/current_context.md` | Refreshed generated current-context artifacts after truth-surface updates. | PASS |
| `docs/saw_reports/saw_strategy_replay_stacked_timeline_visualization_20260515.md` | Published SAW report for this visualization QA slice. | PASS |

Document Sorting: maintained according to `docs/checklist_milestone_review.md`.

## Subagent Results

- Implementer: PASS; verified `_render_replay_timeline_chart` uses `target_weight`, stacked `go.Scatter` traces, `hv` line shape, no markers, muted last `CASH`, and executable Plotly trace coverage.
- Reviewer A: PASS; confirmed stacked timeline is display-only and does not alter replay semantics, Portfolio Performance source, PIT/replay identity, or current allocation semantics.
- Reviewer B: PASS; confirmed fail-soft handling for empty/malformed schema, non-numeric weights, blank tickers, malformed dates, and Plotly runtime stability.
- Reviewer C: PASS; confirmed input copy/no mutation, display-only timeline sampling, `CASH` coherence, and no material performance regression.
- Ownership check: PASS; Implementer and Reviewers A/B/C were separate agents.

## Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_replay_timeline_uses_stacked_replay_targets tests\test_dash_2_portfolio_ytd.py::test_replay_timeline_stacked_chart_traces_are_allocation_areas -q` -> PASS, 2 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_replay_timeline_stacked_chart_traces_are_allocation_areas -q` -> PASS, 1 passed.
- `EVD-04`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 66 passed.
- `EVD-05`: Reviewer B runtime resilience check -> PASS, 4 passed.
- `EVD-06`: Reviewer C display-only/performance-path check -> PASS, 4 passed.
- `EVD-07`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `EVD-08`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.

## Closure Packet

ClosurePacket: RoundID=20260515-strategy-replay-stacked-timeline-saw; ScopeID=strategy-replay-stacked-timeline-visualization; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_dashboard_cache_signature_followup_out_of_scope; NextAction=hold_or_continue_backend_dashboard_cache_signature_emission_policy

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Backend artifact producer `dashboard_cache_signature` emission remains future work.
- Broad inherited dirty/untracked worktree remains present.

Next action:

- Hold, or continue backend dashboard_cache_signature emission policy work.
