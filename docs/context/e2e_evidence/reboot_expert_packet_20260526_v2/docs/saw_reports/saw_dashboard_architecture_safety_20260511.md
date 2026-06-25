# SAW Report - Dashboard Architecture Safety Slice

RoundID: `SAW-DASHBOARD-ARCH-SAFETY-20260511`
ScopeID: `DASHBOARD_ARCHITECTURE_SAFETY_SLICE`
SAW Verdict: PASS
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

## Scope

The in-scope round centralized process-liveness checks, removed unsafe dashboard PID-file termination behavior, collapsed duplicate dashboard strategy-matrix initialization, and delegated dashboard price cleanup to data orchestration.

Owned files:

- `utils/process.py`
- `dashboard.py`
- `data/updater.py`
- `scripts/parameter_sweep.py`
- `scripts/release_controller.py`
- `backtests/optimize_phase16_parameters.py`
- `tests/test_process_utils.py`
- `docs/notes.md`
- `docs/decision log.md`
- `docs/lessonss.md`
- `docs/spec.md`
- `docs/prd.md`
- `PRD.md`
- `PRODUCT_SPEC.md`
- `docs/context/bridge_contract_current.md`
- `docs/context/impact_packet_current.md`
- `docs/context/done_checklist_current.md`
- `docs/context/planner_packet_current.md`
- `docs/context/multi_stream_contract_current.md`
- `docs/context/post_phase_alignment_current.md`
- `docs/context/observability_pack_current.md`
- `docs/context/current_context.md`
- `docs/saw_reports/saw_dashboard_architecture_safety_20260511.md`

## Acceptance Checks

- CHK-01: `utils/process.py` owns shared Windows-safe PID liveness probing.
- CHK-02: Dashboard, updater, parameter-sweep, release-controller, and phase16 optimizer callers delegate through shared helper or compatibility wrappers.
- CHK-03: `dashboard.py::spawn_backtest` does not terminate an unverified PID-file owner and fails closed when a live PID file exists.
- CHK-04: Dashboard strategy-matrix initialization uses one helper path.
- CHK-05: Dashboard portfolio price cleanup delegates to `core.data_orchestrator.clean_price_frame`.
- CHK-06: Focused compile, affected tests, source guard, HTTP smoke, and independent SAW passes complete.

## Subagent Ownership Check

Ownership check: PASS. Implementer and Reviewers A/B/C were distinct agents.

- Implementer: Banach (`019e15c6-97a3-76f2-9866-52c697c0d5f3`) - PASS.
- Reviewer A: Pascal (`019e15c6-982d-7a43-b6c1-97888f59be96`) - PASS.
- Reviewer B: Linnaeus (`019e15c6-9878-7401-873a-40833cbba447`) - BLOCK on first pass, PASS after reconciliation.
- Reviewer C: Singer (`019e15c6-98d6-7e81-bcc4-ce41de4b253d`) - PASS with Low future test suggestion.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `spawn_backtest` could terminate a stale/reused PID-file owner before ownership verification. | Removed unconditional `os.kill(old_pid, signal.SIGTERM)`; live PID files now make spawn fail closed with a warning path. | Parent Codex | Closed |
| Low | YTD/portfolio display inherits duplicate timestamp `keep=last` behavior from shared cleaner, but dashboard-level duplicate-row YTD coverage is source-oriented rather than behavioral. | Carry a focused YTD duplicate-row test as optional future hardening. | Future dashboard hygiene | Open |
| Low | `dashboard.py` remains large and still has broader module-split debt. | Keep as separate Code Quality / architecture milestone. | Future dashboard hygiene | Open |
| Low | Full pytest did not complete in the local 304-second window. | Require longer explicit full-regression window for phase-close proof. | Future verification | Open |

## Scope Split Summary

In-scope findings/actions:

- Added `utils.process.pid_is_running` with Windows `OpenProcess` / `GetExitCodeProcess` liveness probing and conservative fallback.
- Routed local PID wrappers through the shared helper while preserving monkeypatch-compatible wrapper names.
- Removed direct unsafe PID-probe patterns from runtime lock callers.
- Removed unverified dashboard PID-file-owner termination from `spawn_backtest`.
- Added `tests/test_process_utils.py` guardrails for invalid/current PID behavior, unsafe probe source drift, and fail-closed spawn behavior.
- Collapsed dashboard strategy-matrix initialization behind `_build_strategy_matrix` and `_ensure_modular_strategy_state`.
- Delegated `dashboard.py::_clean_portfolio_price_frame` to `core.data_orchestrator.clean_price_frame`.

Inherited out-of-scope findings/actions:

- Legacy dashboard direct yfinance paths remain display/runtime debt, not canonical ingestion.
- `dashboard.py` module splitting remains future Code Quality work.
- Provider ingestion, canonical market-data writes, strategy search, ranking, scoring, alerts, brokers, and candidate-card dashboard merge remain blocked.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `utils/process.py` | Added shared `pid_is_running` with Windows-safe liveness probe and non-Windows fallback. | Implementer PASS; Reviewer B PASS |
| `dashboard.py` | Uses shared PID helper, fail-closed backtest spawn, one strategy-matrix initializer, and core price cleaner delegation. | Reviewer A/B/C PASS |
| `data/updater.py` | Local `_pid_is_running` wrapper delegates to shared helper. | Implementer PASS; Reviewer B PASS |
| `scripts/parameter_sweep.py` | Local `_pid_is_running` wrapper delegates to shared helper. | Implementer PASS; Reviewer B PASS |
| `scripts/release_controller.py` | Local `_pid_is_alive` wrapper delegates to shared helper. | Implementer PASS; Reviewer B PASS |
| `backtests/optimize_phase16_parameters.py` | Local `_is_pid_alive` wrapper delegates to shared helper. | Implementer PASS; Reviewer B PASS |
| `tests/test_process_utils.py` | Added PID helper and source-regression guard tests. | Reviewer B recheck PASS |
| `docs/*`, `PRD.md`, `PRODUCT_SPEC.md`, `docs/context/*` | Documents formulas, boundaries, evidence, blocked scope, and next planner truth. | Parent reconciled |

## Document Sorting

Document sorting order is maintained in `docs/checklist_milestone_review.md` when present. This report follows the repository SAW report convention under `docs/saw_reports/`.

## Verification Evidence

| EvidenceID | Command | Result |
|---|---|---|
| EVD-01 | `.venv\Scripts\python -m py_compile utils\process.py dashboard.py data\updater.py scripts\parameter_sweep.py scripts\release_controller.py backtests\optimize_phase16_parameters.py tests\test_process_utils.py` | PASS |
| EVD-02 | `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q` | PASS, 103 passed |
| EVD-03 | `rg -n "os\.kill\(pid,\s*0\)\|os\.kill\(int\(pid\),\s*0\)" -g "*.py"` | PASS, no unsafe runtime caller outside shared utility comment |
| EVD-04 | `Invoke-WebRequest http://127.0.0.1:8501` after `.venv\Scripts\python launch.py` smoke start | PASS, HTTP 200; spawned smoke process tree stopped |
| EVD-05 | Independent SAW Implementer and Reviewer A/B/C passes | PASS after Reviewer B reconciliation |
| EVD-06 | `.venv\Scripts\python -m pytest -q` | Timed out after 304 seconds; not used as phase-close proof |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-02,TSK-04:EVD-02,TSK-05:EVD-02,TSK-06:EVD-05

EvidenceRows: EVD-01|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z;EVD-02|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z;EVD-03|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z;EVD-04|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z;EVD-05|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z;EVD-06|SAW-DASHBOARD-ARCH-SAFETY-20260511|2026-05-11T06:53:36Z

EvidenceValidation: PASS

Open Risks:

- Full pytest timed out in this local window; run a longer full-regression window before claiming phase-close proof.
- Optional future dashboard behavioral test can cover duplicate YTD rows through `_weighted_equity_curve`.
- Larger `dashboard.py` module split remains future Code Quality work.

Next action:

- Continue Section 2 Code Quality review or hold.

ClosurePacket: RoundID=SAW-DASHBOARD-ARCH-SAFETY-20260511; ScopeID=DASHBOARD_ARCHITECTURE_SAFETY_SLICE; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=FullPytestTimeoutNeedsLongerPhaseCloseWindowAndLowFutureDashboardHygiene; NextAction=ContinueCodeQualityReviewOrHold

ClosureValidation: PASS
SAWBlockValidation: PASS
