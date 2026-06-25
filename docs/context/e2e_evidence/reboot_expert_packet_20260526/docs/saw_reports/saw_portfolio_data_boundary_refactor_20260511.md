# SAW Report - Portfolio Data Boundary Refactor

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: `PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511`
ScopeID: `PORTFOLIO_DATA_BOUNDARY_REFACTOR`

## Scope

Work round scope: move selected-stock live display overlay fetching, adjusted-close extraction, local TRI scaling/stitching, and `data/backtest_results.json` metrics parsing out of `views/optimizer_view.py` into `core/data_orchestrator.py`; update tests and docs to preserve the approved DASH-2 behavior.

Owned files changed in this round:
- `core/data_orchestrator.py`
- `views/optimizer_view.py`
- `data/providers/legacy_allowlist.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_dashboard_sprint_a.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/prd.md`
- `docs/spec.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/saw_reports/saw_portfolio_data_boundary_refactor_20260511.md`

Acceptance checks:
- CHK-01: `views/optimizer_view.py` does not import yfinance or parse `data/backtest_results.json` directly.
- CHK-02: `core/data_orchestrator.py` owns selected-stock live overlay fetching, scaling, stitching, metrics parsing, and display-only cache behavior.
- CHK-03: Partial live overlays preserve local TRI cells and duplicate anchor dates are deduped before scaling.
- CHK-04: Stale overlay cache behavior and scheduler-submit failure path fail soft and are test-locked.
- CHK-05: Focused runtime, dashboard, provider-port, portfolio, optimizer-core, full regression, context validation, and runtime smoke checks pass.
- CHK-06: Docs-as-code surfaces, lessons, decision log, and context packets are updated.
- CHK-07: Distinct Implementer and Reviewer A/B/C SAW passes complete with no unresolved in-scope Critical/High/Medium findings.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High | Partial live overlays could wipe local prices for assets missing from overlapping live rows. | Replaced row-level duplicate-date override with `scaled_live_overlay.combine_first(local_TRI_prices)` and added a two-asset regression. | Parent Codex | Closed |
| High | Duplicate local/live anchor dates could produce ambiguous Series anchors during overlay scaling. | `clean_price_frame` now dedupes duplicate timestamps before scaling, and `scale_live_overlay_to_local` normalizes both local/live frames before anchor selection. | Parent Codex | Closed |
| Medium | Empty/no-result optimizer paths could leave stale `optimizer_weights` for DASH-2 YTD. | Verified no eligible assets, no selection, unusable prices, empty input, empty weights, non-positive weights, and empty allocation all clear optimizer session state. | Parent Codex | Closed |
| Medium | Background overlay scheduler submit failure could bubble into the Streamlit render path and leave an inflight key stuck. | Wrapped scheduler submit in fail-soft handling and clear the inflight key on submit failure; added regression coverage. | Parent Codex | Closed |
| Medium | Stale cache behavior needed to be explicit because the overlay intentionally returns stale display cache while refreshing. | Documented stale-while-revalidate display-only behavior and added stale-cache plus future-mtime tests. | Parent Codex | Closed |
| Low | The DASH-2 live display overlay remains a yfinance-based runtime freshness path, though now it is owned by `core/data_orchestrator.py` rather than the view. | Documented as display-only/non-canonical and kept dashboard-level legacy yfinance debt in Open Risks. | Parent Codex | Carried |

## Subagent Passes

Ownership check: PASS. Implementer and Reviewers A/B/C were distinct agents.

| Role | Agent | Verdict | Status |
| --- | --- | --- | --- |
| Implementer | Descartes (`019e1561-668d-70c0-8623-77b80fc056c9`) | PASS | Confirmed 1A/2A/3A and reviewer-finding fixes remain implemented. |
| Reviewer A | Turing (`019e1561-66c0-7283-9770-3f3bee6e392b`) | PASS | Partial-overlay and stale-session findings resolved. |
| Reviewer B | Herschel (`019e1561-66fd-7412-9a31-72fc156c1dc8`) | PASS | Scheduler-submit resilience finding resolved; no in-scope runtime Critical/High remains. |
| Reviewer C | Anscombe (`019e1561-6749-7330-9306-293e4ccc31c8`) | PASS | Duplicate-anchor handling and stale-while-revalidate semantics resolved/locked. |

## Scope Split Summary

in-scope findings/actions:
- Moved live display overlay fetching, adjusted-close extraction, local TRI scaling/stitching, and `backtest_results.json` metrics parsing into `core/data_orchestrator.py`.
- Updated `views/optimizer_view.py` to consume orchestrator helpers only.
- Removed `views/optimizer_view.py` from direct-yfinance allowlist expectations.
- Fixed sparse live-overlay stitching so live values update cell-wise without erasing local TRI values.
- Fixed duplicate-date anchor handling before overlay scaling.
- Locked stale-while-revalidate display-cache behavior, future-mtime invalidation, and scheduler-submit fail-soft behavior with tests.
- Updated docs-as-code surfaces and lessons.

inherited out-of-scope findings/actions:
- Direct yfinance usage still exists elsewhere in the repo, including dashboard-level YTD freshness and broader legacy scripts.
- Thesis-anchor, MU conviction, WATCH investability, Black-Litterman, lower-bound allocation policy, alerts, broker calls, ranking, scoring, and candidate-card dashboard merge remain separate future scopes.

## Document Changes Showing

| Path | Change summary | Reviewer status |
| --- | --- | --- |
| `core/data_orchestrator.py` | Added portfolio display-refresh helpers, overlay cache, duplicate-safe scaling, cell-wise stitching, scheduler fail-soft handling, and metrics parsing. | Reviewer A/B/C rechecked PASS |
| `views/optimizer_view.py` | Removed direct yfinance import and direct backtest-result JSON parsing; consumes orchestrator helpers and clears stale session weights on no-result paths. | Reviewer A rechecked PASS |
| `data/providers/legacy_allowlist.py` | Removed `views/optimizer_view.py` from the direct-yfinance allowlist. | Implementer rechecked PASS |
| `tests/test_data_orchestrator_portfolio_runtime.py` | Added tests for overlay scaling/stitching, duplicate anchors, partial overlays, stale cache, scheduler fail-soft handling, future-mtime invalidation, and metrics coercion. | Reviewer A/B/C rechecked PASS |
| `tests/test_dashboard_sprint_a.py` | Updated metrics-source import to the data orchestrator. | Implementer rechecked PASS |
| `tests/test_dash_2_portfolio_ytd.py` | Tightened boundary assertions for the new orchestration owner. | Implementer rechecked PASS |
| `docs/notes.md` | Added formulas and source-path registry entries for stale cache, duplicate-date cleanup, and cell-wise overlay merge. | Parent reconciled |
| `docs/decision log.md` | Added/refreshed the portfolio data boundary refactor decision record and evidence. | Parent reconciled |
| `docs/lessonss.md` | Added lessons for view-boundary freshness and sparse display overlay merge discipline. | Parent reconciled |
| `docs/phase_brief/phase65-brief.md` | Added the hygiene refactor addendum and acceptance checks. | Parent reconciled |
| `docs/prd.md`, `docs/spec.md`, `PRD.md`, `PRODUCT_SPEC.md` | Added product/spec notices for the new boundary. | Parent reconciled |
| `docs/context/*.md` | Refreshed current truth surfaces for the round. | Parent reconciled |

## Document Sorting

GitHub-optimized document order follows `docs/checklist_milestone_review.md`: runtime/code, tests, architecture/policy, handover, context surfaces, governance logs, SAW.

## Verification Evidence

| EvidenceID | Command | Result |
| --- | --- | --- |
| EVD-01 | `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py dashboard.py data\providers\legacy_allowlist.py tests\test_dash_2_portfolio_ytd.py tests\test_dashboard_sprint_a.py tests\test_data_orchestrator_portfolio_runtime.py` | PASS |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q` | PASS, 8 passed |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py tests\test_dash_2_portfolio_ytd.py tests\test_provider_ports.py tests\test_portfolio_universe.py -q` | PASS, 47 passed |
| EVD-04 | `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` | PASS, 17 passed |
| EVD-05 | `.venv\Scripts\python -m pytest -q` | PASS |
| EVD-06 | `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS |
| EVD-07 | `Invoke-WebRequest http://localhost:8505/portfolio-and-allocation` | PASS, HTTP 200 |
| EVD-08 | Independent Implementer and Reviewer A/B/C recheck passes | PASS |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-01,TSK-03:EVD-02,TSK-04:EVD-02,TSK-05:EVD-05,TSK-06:EVD-06,TSK-07:EVD-08

EvidenceRows: EVD-01|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-02|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-03|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-04|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-05|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-06|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-07|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z;EVD-08|PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511|2026-05-11T05:59:37Z

## Open Risks

Open Risks:

- Dashboard-level YTD live refresh still has inherited direct-yfinance legacy debt outside this selected-stock optimizer-view boundary refactor.
- The selected-stock overlay remains display freshness only and must not be treated as canonical provider ingestion or candidate evidence.

## Next Action

Next action: `approve_portfolio_thesis_anchor_policy_planning_or_hold`

## Closure

ClosureValidation: PASS

SAWBlockValidation: PASS

EvidenceValidation: PASS

ClosurePacket: RoundID=PORTFOLIO_DATA_BOUNDARY_REFACTOR_20260511; ScopeID=PORTFOLIO_DATA_BOUNDARY_REFACTOR; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=dashboard_ytd_legacy_yfinance_debt_and_display_overlay_noncanonical; NextAction=approve_portfolio_thesis_anchor_policy_planning_or_hold

Evidence:

- Focused runtime, dashboard, provider-port, portfolio, optimizer-core, full regression, context validation, and runtime smoke checks passed.
- Independent Implementer and Reviewer A/B/C rechecks passed after reconciliation.
- Closure, SAW block, and evidence validators passed.

Assumptions:

- The approved DASH-2 overlay behavior remains display-freshness only.
- Dashboard-level YTD yfinance cleanup is a separate future hygiene scope.

Open Risks:

- Inherited dashboard-level direct-yfinance YTD path remains outside this round.

Rollback Note:

- Revert `core/data_orchestrator.py`, `views/optimizer_view.py`, `data/providers/legacy_allowlist.py`, the new runtime tests, docs/context notes, and this SAW report if the boundary refactor is rejected.
