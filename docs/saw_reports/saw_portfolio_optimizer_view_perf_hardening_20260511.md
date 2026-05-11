# SAW Report - Portfolio Optimizer View Test and Performance Hardening

RoundID: `SAW-PORTFOLIO-OPTIMIZER-VIEW-PERF-20260511`
ScopeID: `PORTFOLIO_OPTIMIZER_VIEW_PERF_HARDENING`
SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

The in-scope round implemented `/portfolio-and-allocation` optimizer view tests and performance hardening without changing optimizer policy or provider authority.

Owned files:

- `.gitignore`
- `core/data_orchestrator.py`
- `views/optimizer_view.py`
- `tests/test_optimizer_view.py`
- `tests/test_optimizer_core_policy.py`
- `tests/test_dash_2_portfolio_ytd.py`
- `tests/test_data_orchestrator_portfolio_runtime.py`
- `docs/phase_brief/phase65-brief.md`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
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

## Acceptance Checks

- CHK-01: Dedicated Streamlit AppTest coverage exists for optimizer view rendering.
- CHK-02: Mean-variance widget path and sector-cap UI path are exercised.
- CHK-03: UI-derived max-weight and risk-free-rate controls are tested through real SLSQP.
- CHK-04: Recent close overlay cache is display-only, Parquet-backed, nonblocking on cold miss, and temp->replace atomic.
- CHK-05: Optimizer reruns are cached by method, selected price frame, max-weight, and risk-free-rate.
- CHK-06: Focused, full, context, compile, and runtime smoke verification pass.
- CHK-07: Independent implementer and Reviewer A/B/C subagent passes complete.

## Subagent Ownership Check

Implementer and reviewers were assigned as different agents in the SAW rerun:

- Implementer: `019e1564-2802-7bf0-97de-54aee88f5e7d` - PASS.
- Reviewer A: `019e1564-3143-7d73-be9f-1073c88fc1bd` - PASS.
- Reviewer B: `019e1564-45e7-7921-a326-a8c94cbf0ab7` - PASS with Low follow-ups.
- Reviewer C: `019e1564-c112-7492-a671-11671093110d` - PASS.

Ownership check: PASS. Implementer and Reviewer A/B/C are distinct agents. The initial Reviewer C fork failed due local thread-history memory pressure and was replaced by the distinct non-forked Reviewer C agent above.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Low | `ThreadPoolExecutor.submit()` could still raise during interpreter shutdown or severe resource pressure before the view falls back. | Future hardening may wrap `_overlay_executor().submit(...)` in `try/except`, clear the inflight key, and keep local-only fallback. | Future runtime hygiene | OPEN |
| Low | Background yfinance failures are intentionally swallowed, leaving limited operator diagnostics beyond local fallback behavior. | Consider lightweight debug logging or a non-blocking status counter in a later observability lane. | Future runtime hygiene | OPEN |
| Low | `.venv` full pytest emits existing warning noise unrelated to this round. | Carry as inherited warning hygiene; no runtime failure. | Future hygiene | OPEN |

## Scope Split Summary

In-scope findings/actions:

- Implementation, focused tests, full regression, context validation, and runtime smoke passed.
- SAW independent Implementer and Reviewer A/B/C rerun passed.
- No in-scope Critical/High findings remain unresolved.

Inherited findings/actions:

- Dashboard-level direct yfinance usage outside the optimizer view remains inherited legacy debt.
- Thesis-anchor, MU conviction, WATCH investability, Black-Litterman, alerts, brokers, ranking, scoring, and candidate-card dashboard merge remain blocked future scope.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `.gitignore` | Ignores `data/runtime_cache/` generated display cache artifacts. | Approved by SAW rerun |
| `core/data_orchestrator.py` | Adds display-only overlay cache, background refresh scheduling, atomic Parquet writes, copy-safe scale cache, and selected-price overlay knobs. | Approved by SAW rerun; Low follow-ups carried |
| `views/optimizer_view.py` | Reconciles render path to helper flow, adds cached optimizer reruns, keeps sector caps post-solver, fixes mixed-type Permno table rendering. | Approved by SAW rerun |
| `tests/test_optimizer_view.py` | Adds Streamlit AppTest render/control coverage and cache behavior tests. | Approved by SAW rerun |
| `tests/test_optimizer_core_policy.py` | Adds UI-derived controls through real SLSQP plus post-solver sector-cap test. | Approved by SAW rerun |
| `tests/test_dash_2_portfolio_ytd.py` | Locks display-only cache/background refresh expectations. | Approved by SAW rerun |
| `tests/test_data_orchestrator_portfolio_runtime.py` | Updates fake downloader to accept cache kwargs. | Approved by SAW rerun |
| `docs/*`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/context/*` | Documents formulas, boundaries, evidence, blocked scope, and planner truth. | Approved by SAW rerun |

## Document Sorting

Document sorting order is maintained in `docs/checklist_milestone_review.md` when that checklist is present. This report follows the repo's SAW report folder convention under `docs/saw_reports/`.

## Verification Evidence

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py strategies\optimizer.py dashboard.py tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_provider_ports.py -q` -> PASS, 46 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Streamlit smoke `http://127.0.0.1:8506/portfolio-and-allocation` -> PASS, HTTP 200.
- Independent SAW Implementer rerun -> PASS.
- Independent Reviewer A strategy correctness/regression pass -> PASS.
- Independent Reviewer B runtime/operational resilience pass -> PASS with Low follow-ups.
- Independent Reviewer C data integrity/performance pass -> PASS.

Open Risks:

- Dashboard-level direct yfinance usage remains inherited legacy debt outside this optimizer-view hardening lane.
- Low runtime hygiene follow-ups remain open for future work: executor submit exception containment and optional background-refresh diagnostics.

Next action:

- Hold, measure the next dashboard runtime bottleneck, or separately approve a follow-up runtime hygiene lane for the Low executor-submit/logging items.

ClosurePacket: RoundID=SAW-PORTFOLIO-OPTIMIZER-VIEW-PERF-20260511; ScopeID=PORTFOLIO_OPTIMIZER_VIEW_PERF_HARDENING; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=InheritedDashboardYfinanceDebtAndLowRuntimeHygieneFollowups; NextAction=HoldOrMeasureNextRuntimeBottleneck

ClosureValidation: PASS
SAWBlockValidation: PASS
