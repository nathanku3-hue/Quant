# SAW Report - Replay Selected Price Loading + MU/SNDK Eligibility Trace

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: 20260515-replay-selected-price-mu-sndk-saw
ScopeID: replay-selected-price-loading-mu-sndk

## Scope

Work round scope: preserve full PIT membership proof, reduce selected-asset price loading, and keep MU/SNDK eligibility tracing as strategy/data diagnostics outside the replay hot path.

Owned files changed in this round:

- `core/data_orchestrator.py`
- `dashboard.py`
- `scripts/pit_lifecycle_replay.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `tests/test_optimizer_view.py`
- `tests/test_pinned_universe.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/prd.md`
- `docs/spec.md`
- `docs/notes.md`
- `docs/lessonss.md`
- `docs/decision log.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/context/*`

Acceptance checks:

- CHK-01: full-window `r3000_pit` membership proof is built before selected price loading.
- CHK-02: dashboard selected-method replay passes signed numeric replay assets into batched price loading.
- CHK-03: MU/SNDK trace is separate from replay hot path and answers pinned/map/PIT/local/history/sizing/hold/gate questions.
- CHK-04: local price/return diagnostic evidence rejects non-finite `total_ret` rows.
- CHK-05: executable tests cover selected price loading, selected-permno handoff, and MU/SNDK trace gates.
- CHK-06: docs/context/evidence are refreshed with the two-track boundary and local evidence.

## Reviewer Ownership

Ownership check: PASS. Implementer pass and Reviewer A/B/C were different agents. Implementer: Gibbs. Reviewer A: Confucius. Reviewer B: Russell. Reviewer C: Wegener.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `_valid_price_return_rows(...)` could count positive price plus non-finite `total_ret` as valid local evidence. | Replaced `inf/-inf` `total_ret` with NA and added a regression that expects `latest_local_price_return=False`. | Parent + Reviewer C recheck | Fixed |
| Medium | Dashboard selected-price behavior had too much source-text coverage. | Strengthened executable dashboard test to record `selected_permnos` passed to the cached loader while a non-selected PIT member remains in membership proof. | Parent + Reviewer C recheck | Fixed |
| Medium | Malformed optional diagnostic files can still raise parser errors. | Carry as non-blocking diagnostic resilience follow-up; not dashboard hot path. | Future Strategy/Data | Inherited/open |
| Low | DuckDB path interpolation can fail on unusual local paths containing a quote. | Carry as non-blocking runtime hardening follow-up for local path escaping or registered scans. | Future Backend/Data | Inherited/open |

## Scope Split Summary

in-scope findings/actions:

- Fixed non-finite `total_ret` validity gap in MU/SNDK local price/return diagnostics.
- Added executable selected-permno handoff proof for dashboard replay loading.
- Re-ran targeted and broader affected checks.

inherited out-of-scope findings/actions:

- Malformed optional diagnostic input resilience and unusual DuckDB local path quoting remain follow-ups outside this performance/trace slice.
- Broad inherited dirty/untracked files remain present and were not reverted.

## Verification Evidence

| EvidenceID | Command / Evidence | Result | Notes |
|---|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile core\data_orchestrator.py dashboard.py scripts\pit_lifecycle_replay.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_pinned_universe.py` | PASS | Focused compile for original slice. |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py::test_batched_pit_loader_keeps_full_membership_proof_while_loading_selected_prices tests\test_optimizer_view.py::test_dashboard_batched_pit_loader_passes_selected_permnos_without_watchlist_shortcut tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_answers_mu_sndk_gates tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_reports_pit_membership_gate -q` | PASS, 4 passed | Original targeted loader/source/trace regressions. |
| EVD-03 | `.venv\Scripts\python -m pytest tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_rejects_non_finite_return_rows tests\test_pinned_universe.py::test_trace_thesis_ticker_eligibility_answers_mu_sndk_gates tests\test_dash_2_portfolio_ytd.py::test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight -q` | PASS, 3 passed | Reconciliation checks for Reviewer C findings. |
| EVD-04 | `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py tests\test_pinned_universe.py tests\test_strategy_replay_coverage.py tests\test_dash_2_portfolio_ytd.py::test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight -q` | PASS, 112 passed | Broader affected suite. |
| EVD-05 | Local evidence JSON refresh at `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json` | PASS | 27 PIT members proved, 2 selected columns loaded, 89 trading dates, refreshed elapsed 0.5015s. |
| EVD-06 | `.venv\Scripts\python scripts\build_context_packet.py` and `.venv\Scripts\python scripts\build_context_packet.py --validate` | PASS | Current context packet refreshed and validated. |
| EVD-07 | Reviewer C focused recheck | PASS | High finding fixed and medium executable-test gap adequately reduced. |

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/prd.md`, `docs/spec.md`, `PRD.md`, `PRODUCT_SPEC.md` | Product/spec notices for selected-price loading and MU/SNDK trace boundary. | PASS |
| `docs/phase_brief/phase65-brief.md` | Phase addendum records performance slice, diagnostic result, non-finite return rule, and evidence. | PASS |
| `docs/notes.md` | Formula/logic notes for PIT proof, selected price loading, and diagnostic validity. | PASS |
| `docs/lessonss.md` | Lesson updated with watchlist-only and non-finite price/return guardrails. | PASS |
| `docs/decision log.md` | Decision record and contract lock updated with reconciled evidence. | PASS |
| `docs/context/*` | Bridge/planner/impact/done/multi-stream/alignment/observability/current-context surfaces refreshed. | PASS |
| `docs/context/e2e_evidence/replay_selected_price_loading_mu_sndk_trace_20260515.json` | Local measurement and MU/SNDK trace evidence refreshed after reconciliation. | PASS |

Document Sorting: maintained per `docs/checklist_milestone_review.md` ordering for report summary.

## SE Executor Closure

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-06
EvidenceRows: EVD-01|20260515-replay-selected-price-mu-sndk-se|2026-05-15T11:16:52Z;EVD-02|20260515-replay-selected-price-mu-sndk-se|2026-05-15T11:16:52Z;EVD-03|20260515-replay-selected-price-mu-sndk-se|2026-05-15T11:16:52Z;EVD-04|20260515-replay-selected-price-mu-sndk-se|2026-05-15T11:16:52Z;EVD-06|20260515-replay-selected-price-mu-sndk-se|2026-05-15T11:16:52Z
EvidenceValidation: PASS
SE closure packet validated separately: RoundID=20260515-replay-selected-price-mu-sndk-se; ScopeID=replay-selected-price-loading-mu-sndk; ChecksTotal=5; ChecksPassed=5; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=parent_saw_reconciliation
SE ClosureValidation: PASS

## Closure

Open Risks: Non-blocking follow-ups remain for malformed optional diagnostic input resilience and unusual DuckDB path quoting. No unresolved in-scope Critical/High findings remain.

Next action: Hold, or run a separate Strategy/Data eligibility investigation for MU/SNDK Rule100 candidate/history behavior.

ClosurePacket: RoundID=20260515-replay-selected-price-mu-sndk-saw; ScopeID=replay-selected-price-loading-mu-sndk; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=non_blocking_diagnostic_input_and_duckdb_path_followups; NextAction=hold_or_run_separate_strategy_data_eligibility_investigation_for_mu_sndk

ClosureValidation: PASS

SAWBlockValidation: PASS
