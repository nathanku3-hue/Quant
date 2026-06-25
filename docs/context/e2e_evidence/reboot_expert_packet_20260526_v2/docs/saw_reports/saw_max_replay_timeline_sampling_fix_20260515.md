# SAW Report - Max Replay Timeline Sampling Fix - 2026-05-15

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: FallbackSource docs/spec.md + docs/phase_brief/phase65-brief.md | Domains: Frontend/UI, Backend, Data, Docs/Ops

RoundID: 20260515-max-replay-timeline-sampling-saw
ScopeID: max-replay-timeline-sampling-fix
SAW Verdict: PASS

## Scope And Ownership

Work round scope: fix the Strategy Replay max-window timeline crash caused by calling `.normalize()` directly on a pandas `Series` after weekly grouping.

Owned files changed in this round:

- `dashboard.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/context/*`
- `docs/saw_reports/saw_max_replay_timeline_sampling_fix_20260515.md`

Acceptance checks:

- CHK-01: Max-window timeline sampling no longer calls `Series.normalize()` on grouped weekly dates.
- CHK-02: Weekly grouped keep-dates normalize through the pandas Series `.dt` accessor.
- CHK-03: The final daily replay date is retained in the sampled timeline.
- CHK-04: Timeline sampling remains display-only from daily replay rows and cannot feed Portfolio Performance.
- CHK-05: Focused compile and targeted max-window sampler tests pass.
- CHK-06: Focused Portfolio/YTD dashboard test file passes.
- CHK-07: Context packet rebuild and validation pass after docs updates.
- CHK-08: Runtime smoke reaches `/portfolio-and-allocation`.
- CHK-09: Independent SAW Implementer and Reviewer A/B/C passes complete with different agents.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | Mixed timezone-aware date strings could produce object dtype in pandas and make `.dt` unavailable, though current replay/schema paths emit naive dates or ISO date strings. | Carry as future hygiene; not in-scope for this crash fix. | Future Frontend/UI | Open, non-blocking |
| Medium | Backend production artifacts still need `dashboard_cache_signature` emission for saved-artifact UI hits. | Keep transitional build labeled; coordinate backend producer follow-up separately. | Backend | Open, out-of-scope |
| Low | Broad inherited dirty/untracked worktree remains visible. | Do not revert unrelated work; report as inherited state. | Parent | Open, inherited |

## Scope Split Summary

In-scope findings/actions:

- Replaced grouped weekly date normalization with `pd.to_datetime(...).dropna().dt.normalize()`.
- Added a max-window regression with more than 160 business dates.
- Preserved final replay-date retention in the sampled timeline.
- Confirmed sampled rows flow only to Strategy Replay Timeline rendering.

Inherited out-of-scope findings/actions:

- Backend `dashboard_cache_signature` producer emission remains a separate coordination follow-up.
- Mixed timezone replay date hardening is future hygiene because current replay paths use naive dates or ISO date strings.
- Existing broad dirty/untracked files were not reverted.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `docs/prd.md`, `docs/spec.md` | Added max replay timeline sampling fix notices. | PASS |
| `docs/phase_brief/phase65-brief.md` | Added invariant, evidence, and boundary for the max-window sampler repair. | PASS |
| `docs/notes.md` | Added sampling formula and evidence. | PASS |
| `docs/lessonss.md` | Added lesson on pandas container type changes needing executable long-window tests. | PASS |
| `docs/decision log.md` | Added hardcoded contract lock for max replay timeline sampling. | PASS |
| `docs/context/*` | Refreshed current truth surfaces and context packet. | PASS |

Document Sorting: maintained according to `docs/checklist_milestone_review.md`.

## Subagent Results

- Implementer: PASS; verified no `Series.normalize()`, `.dt.normalize()` after grouping, final date retention, and appropriate regression coverage.
- Reviewer A: PASS; confirmed sampled rows remain visualization-only and Portfolio Performance still uses daily `portfolio_return`.
- Reviewer B: PASS; confirmed invalid-date handling and runtime safety, with one non-blocking future timezone hygiene note.
- Reviewer C: PASS; confirmed weekly grouping math, source-copy behavior, final-date retention, and long-window performance sanity.
- Ownership check: PASS; Implementer and Reviewers A/B/C were separate agents.

## Evidence

- `EVD-01`: `.venv\Scripts\python -m py_compile dashboard.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `EVD-02`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay tests\test_dash_2_portfolio_ytd.py::test_dash_2_weekly_sampling_is_display_only_from_daily_replay -q` -> PASS, 2 passed.
- `EVD-03`: `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 53 passed.
- `EVD-04`: `.venv\Scripts\python scripts\build_context_packet.py` -> PASS.
- `EVD-05`: `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `EVD-06`: Streamlit readiness smoke `http://127.0.0.1:8534/portfolio-and-allocation` -> PASS, HTTP 200.

## Closure Packet

ClosurePacket: RoundID=20260515-max-replay-timeline-sampling-saw; ScopeID=max-replay-timeline-sampling-fix; ChecksTotal=9; ChecksPassed=9; ChecksFailed=0; Verdict=PASS; OpenRisks=backend_dashboard_cache_signature_followup_out_of_scope; NextAction=hold_or_coordinate_backend_dashboard_cache_signature_emission

ClosureValidation: PASS

SAWBlockValidation: PASS

Open Risks:

- Backend artifact producer `dashboard_cache_signature` emission remains future work.
- Mixed timezone-aware replay date hardening remains future hygiene.
- Broad inherited dirty/untracked worktree remains present.

Next action:

- Hold, or coordinate backend dashboard_cache_signature emission for production saved-artifact UI hits.
