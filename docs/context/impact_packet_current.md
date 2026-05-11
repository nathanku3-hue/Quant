# Impact Packet - Current

Status: Current
Authority: advisory-only integration artifact. This file does not authorize live trading, promotion, strategy search, provider ingestion, alerts, broker calls, dashboard content redesign, signal ranking, macro scoring, factor scoring, candidate ranking, candidate scoring, or scope widening by itself.
Purpose: provide a compact view of the Portfolio Optimizer View Test and Performance Hardening implementation and affected interfaces.

## Latest Addendum - Pinned Strategy Universe Hardening

### Changed Runtime Files

```text
data/universe/pinned_thesis_universe.yml   (manifest: 10 thesis tickers)
data/universe/loader.py                    (fail-closed loader with strict validation)
data/universe/__init__.py
data/feature_store.py                      (unions pinned permnos, aborts on failure unless override)
scripts/pit_lifecycle_replay.py            (defaults to scanner∪pinned, shared eligibility gate)
```

### Changed Test Files

```text
tests/test_pinned_universe.py              (27 tests: loader, gates, union, fail-closed, diagnostics, edge cases)
```

### Changed Data Files

```text
data/processed/yahoo_patch.parquet         (backfilled MU/AMD/AVGO/TSM/INTC/LRCX/SNDK/WDC/AMAT)
data/processed/prices_tri.parquet          (rebuilt through 2026-05-11)
data/processed/macro_features.parquet      (rebuilt through 2026-05-11)
data/processed/macro_features_tri.parquet  (rebuilt through 2026-05-11)
data/processed/features.parquet            (203 permnos = 200 yearly_union + pinned)
data/portfolio_lifecycle_log.jsonl          (103 events, 12 tickers)
```

### Touched Interfaces

- `run_build()` signature: added `allow_missing_pinned_universe: bool = False`
- `load_pinned_manifest()`: raises FileNotFoundError/ValueError (was silent return [])
- `_default_replay_tickers()`: raises on loader failure (was silent fallback to [])
- `is_pit_eligible()` / `is_pit_exit()`: new shared gate functions

### Pinned Universe Formula

```
feature_universe = yearly_top_n(200) ∪ pinned_thesis_universe.yml
replay_tickers   = SCANNER_TICKERS ∪ pinned_thesis_universe.yml
eligibility      = z_demand > 0 AND capital_cycle_score > 0 AND dist_sma20 ≤ 0.05 AND NOT trend_veto
exit_trigger     = dist_sma20 > 0.12 OR trend_veto (on held position)
```

### Failing Checks

None. 102 tests pass (27 pinned + 34 feature_store + 14 lifecycle + 7 dash-1 + 20 dash-2).

## Latest Addendum - Portfolio Lifecycle Current Holds Fix

### Changed Runtime Files

```text
data/portfolio_lifecycle_log.py
strategies/portfolio_universe.py
views/optimizer_view.py
dashboard.py
```

### Changed Test Files

```text
tests/test_position_lifecycle.py
tests/test_portfolio_universe.py
tests/test_optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/phase_brief/phase65-brief.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Lifecycle replay state`: `data.portfolio_lifecycle_log.get_open_lifecycle_positions(...)` reconstructs latest ENTER/EXIT open holdings as of a PIT-safe cutoff.
- `Current position memory`: `strategies.portfolio_universe.load_current_position_memory(...)` prefers lifecycle replay state over stale JSON memory when replay evidence exists.
- `Optimizer universe`: open lifecycle holdings are included as `included_current_hold`, even when today's scanner row is EXIT/KILL.
- `Portfolio allocation UI`: no-fresh-PIT-ENTER with open lifecycle holds renders current holds plus residual cash, not 100% cash.
- `Portfolio performance`: session, ticker-mapped, and aligned weights preserve residual cash unless total weights exceed 100%.
- `Lifecycle data integrity`: JSONL appends use lock + temp + replace, and malformed rows fail closed instead of being skipped.

### Passing Checks

- `.venv\Scripts\python -m py_compile data\portfolio_lifecycle_log.py strategies\portfolio_universe.py views\optimizer_view.py dashboard.py tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_position_lifecycle.py tests\test_portfolio_universe.py tests\test_optimizer_view.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 58 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke at `http://127.0.0.1:8509/portfolio-and-allocation` -> PASS; Universe Audit shows included lifecycle holds and the residual-cash message renders.
- Local lifecycle state check -> open holdings are `AMAT`, `AVGO`, and `TSLA`, not sell-all.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_closure_packet.py --packet "<lifecycle ClosurePacket>" --require-open-risks-when-block --require-next-action-when-block` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_saw_report_blocks.py --report-file docs\saw_reports\saw_portfolio_lifecycle_current_holds_20260512.md` -> PASS.
- `.venv\Scripts\python .codex\skills\_shared\scripts\validate_se_evidence.py ...` -> PASS.

### Failing / Incomplete Checks

- None in current focused verification.

### Open Risks

- Existing lifecycle replay weights are simple replay weights and not a full execution ledger with fills, quantities, realized P&L, or slippage.
- Hard-crash stale lifecycle `.lock` recovery is a future Ops hardening follow-up; current behavior fails closed by timeout.
- Broader dirty worktree contains inherited dashboard/navigation and governance edits outside this focused fix.

## Latest Addendum - Dashboard Unified Data Cache Performance Fix

### Changed Runtime Files

```text
dashboard.py
core/data_orchestrator.py
```

### Changed Test Files

```text
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dashboard_sprint_a.py
```

### Changed Governance / Evidence Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_status.txt
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_stdout.txt
docs/context/e2e_evidence/dashboard_unified_data_cache_8507_stderr.txt
```

### Touched Interfaces

- `Dashboard unified data load`: `dashboard.py` calls `_load_unified_data_cached(...)` instead of loading the institutional parquet package directly on every Streamlit rerun.
- `Unified data cache invalidation`: `core.data_orchestrator.build_unified_data_cache_signature(...)` fingerprints relevant processed/static parquet source files by resolved path, mtime_ns, and size.

### Passing Checks

- `.venv\Scripts\python -m py_compile dashboard.py core\data_orchestrator.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py tests\test_optimizer_view.py -q` -> PASS, 22 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Streamlit HTTP smoke at `http://127.0.0.1:8507` -> PASS, HTTP 200.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Independent SAW Implementer and Reviewer A/B/C passes -> PASS after reconciling stale full-pytest evidence.
- SAW closure packet validation and report block validation -> PASS.

### Failing / Incomplete Checks

- None in current focused/full verification.

### Open Risks

- Cached package is returned as a mutable resource; current dashboard consumers treat the package as read-mostly, but future in-place mutation should switch this path to `st.cache_data` or copy before mutation.
- Alpha-engine daily-loop optimization and scanner raw-financials cache remain separate follow-ups.

## Latest Addendum - Dashboard Scanner Testability Hardening

### Changed Runtime Files

```text
strategies/scanner.py
dashboard.py
```

### Changed Test Files

```text
tests/conftest.py
tests/test_scanner.py
tests/test_strategy.py
tests/test_adaptive_trend.py
tests/test_production_config.py
tests/test_core_etl.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Dashboard scanner`: `dashboard.py` still owns yfinance fetch/cache/payload persistence; deterministic enrichment delegates to `strategies.scanner.enrich_scan_frame`.
- `Scanner formulas`: macro score, breadth status, technicals, entry/support math, tactics, proxy signal, rating, and leverage are importable pure helpers.
- `Scanner data quality`: non-finite macro and breadth inputs fail closed to `None` / `UNKNOWN` instead of optimistic labels.
- `Test fixtures`: `tests/conftest.py` now exposes common synthetic price, return, macro, and ticker-map fixtures.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_scanner.py tests\test_strategy.py tests\test_phase15_integration.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\test_process_utils.py -q` -> PASS, 49 passed.
- `.venv\Scripts\python -m py_compile strategies\scanner.py dashboard.py tests\test_scanner.py tests\test_strategy.py tests\test_adaptive_trend.py tests\test_production_config.py tests\test_core_etl.py tests\conftest.py` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS after non-finite scanner reconciliation.
- `.venv\Scripts\python -m pytest --collect-only -q` -> PASS; collection includes scanner, adaptive-trend, production-config, core-ETL, and process-guardrail tests.
- SAW Reviewer C final recheck -> PASS; latest raw `VWEHX`/`VFISX` fail-closed behavior verified.

### Failing / Incomplete Checks

- None for this addendum.

### Open Risks

- `dashboard.py` remains large; this round extracted scanner math only and did not redesign the dashboard runtime.

## Latest Addendum - Dashboard Architecture Safety Slice

### Changed Runtime Files

```text
utils/process.py
dashboard.py
data/updater.py
scripts/parameter_sweep.py
scripts/release_controller.py
backtests/optimize_phase16_parameters.py
```

### Changed Test Files

```text
tests/test_process_utils.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/spec.md
docs/prd.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/saw_reports/saw_dashboard_architecture_safety_20260511.md
```

### Touched Interfaces

- `Process liveness`: shared `utils.process.pid_is_running` replaces local direct PID-probe logic while preserving local wrapper names.
- `Backtest single-flight`: `dashboard.py::spawn_backtest` refuses to spawn another job when the PID file points to a live process.
- `Dashboard strategy matrix`: `_build_strategy_matrix` and `_ensure_modular_strategy_state` own one initialization path.
- `Dashboard price cleanup`: `_clean_portfolio_price_frame` delegates to `core.data_orchestrator.clean_price_frame`.

### Passing Checks

- `.venv\Scripts\python -m py_compile utils\process.py dashboard.py data\updater.py scripts\parameter_sweep.py scripts\release_controller.py backtests\optimize_phase16_parameters.py tests\test_process_utils.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_process_utils.py tests\test_parameter_sweep.py tests\test_updater_parallel.py tests\test_release_controller.py tests\test_optimize_phase16_parameters.py tests\test_dash_1_page_registry_shell.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_optimizer_view.py -q` -> PASS, 103 passed.
- `rg -n "os\.kill\(pid,\s*0\)|os\.kill\(int\(pid\),\s*0\)" -g "*.py"` -> no unsafe runtime caller outside shared utility comment.
- `Invoke-WebRequest http://127.0.0.1:8501` after launch smoke -> PASS, HTTP 200.

### Failing / Incomplete Checks

- `.venv\Scripts\python -m pytest -q` -> timed out after 304 seconds.
- `.venv\Scripts\python launch.py` -> long-running app boot timed out after 184 seconds; HTTP readiness was checked successfully and the spawned process tree was stopped.

### Open Risks

- Full regression needs a longer explicit window if phase closure is requested.
- `dashboard.py` remains large and still has broader module-split debt outside this safety slice.

## Latest Addendum - Portfolio Optimizer View Test and Performance Hardening

### Changed Runtime Files

```text
core/data_orchestrator.py
views/optimizer_view.py
.gitignore
tests/test_optimizer_view.py
tests/test_optimizer_core_policy.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
```

### Touched Interfaces

- `Portfolio Optimizer UI`: render body uses helper path, Streamlit AppTest coverage exists, optimizer runs are cached by selected price frame and parameters.
- `Portfolio Data Orchestration`: display-only recent-close overlays use Parquet cache, background refresh scheduling, atomic cache writes, and copy-safe overlay scaling cache.
- `Optimizer Core Policy Tests`: UI-derived max-weight/risk-free-rate values flow through the real SLSQP path; sector caps remain post-solver soft constraints.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 39 passed.
- `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py strategies\optimizer.py dashboard.py tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_optimizer_view.py tests\test_optimizer_core_policy.py tests\test_dash_2_portfolio_ytd.py tests\test_data_orchestrator_portfolio_runtime.py tests\test_provider_ports.py -q` -> PASS, 46 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Streamlit smoke at `http://127.0.0.1:8506/portfolio-and-allocation` -> PASS, HTTP 200.
- SAW independent Implementer and Reviewer A/B/C rerun -> PASS.
- SAW report block validation and closure packet validation -> PASS.

### Open Risks

- DASH YTD benchmark refresh still has dashboard-level direct yfinance legacy debt.
- Low runtime hygiene follow-ups remain open for future work: executor submit exception containment and optional background-refresh diagnostics.
- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Portfolio Data Boundary Refactor

### Changed Runtime Files

```text
core/data_orchestrator.py
views/optimizer_view.py
data/providers/legacy_allowlist.py
tests/test_data_orchestrator_portfolio_runtime.py
tests/test_dashboard_sprint_a.py
tests/test_dash_2_portfolio_ytd.py
```

### Changed Governance Files

```text
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
```

### Touched Interfaces

- `Portfolio Data Orchestration`: owns selected-stock display-refresh close extraction, duplicate-safe local TRI scaling/stitching, stale-while-revalidate display cache, scheduler fail-soft handling, and strategy metrics parsing.
- `Portfolio Optimizer UI`: consumes orchestrator helpers, no longer owns direct yfinance or direct backtest-results JSON parsing, and clears stale optimizer session weights on no-result paths.
- `Provider-Port Guard`: `views/optimizer_view.py` is removed from direct-yfinance allowlist expectations.

### Passing Checks

- `.venv\Scripts\python -m py_compile core\data_orchestrator.py views\optimizer_view.py dashboard.py data\providers\legacy_allowlist.py tests\test_dash_2_portfolio_ytd.py tests\test_dashboard_sprint_a.py tests\test_data_orchestrator_portfolio_runtime.py` -> PASS.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py -q` -> PASS, 8 passed.
- `.venv\Scripts\python -m pytest tests\test_data_orchestrator_portfolio_runtime.py tests\test_dashboard_sprint_a.py tests\test_dash_2_portfolio_ytd.py tests\test_provider_ports.py tests\test_portfolio_universe.py -q` -> PASS, 47 passed.
- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS, 17 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py` and `--validate` -> PASS.
- Runtime smoke at `http://localhost:8505/portfolio-and-allocation` -> PASS, HTTP 200.
- SAW Implementer and Reviewer A/B/C rechecks -> PASS.

### Open Risks

- DASH YTD benchmark refresh still has dashboard-level direct yfinance legacy debt.
- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Optimizer Core Structured Diagnostics Implementation

### Changed Runtime Files

```text
strategies/optimizer_diagnostics.py
strategies/optimizer.py
views/optimizer_view.py
tests/test_optimizer_core_policy.py
```

### Changed Governance Files

```text
docs/architecture/optimizer_core_policy_audit.md
docs/architecture/optimizer_constraints_policy.md
docs/architecture/optimizer_lower_bound_slsqp_policy.md
docs/notes.md
docs/decision log.md
docs/phase_brief/phase65-brief.md
docs/prd.md
docs/spec.md
PRD.md
PRODUCT_SPEC.md
```

### Touched Interfaces

- `Optimizer Diagnostics`: new structured report objects for feasibility, solver, bound, constraint, severity, and fallback status.
- `Portfolio Optimizer Core`: existing objectives preserved; diagnostic-returning methods expose status without adding lower-bound policy or conviction math.
- `Portfolio & Allocation UI`: renders optimization status, feasibility status, active constraints, assets at max/lower bounds, equal-weight forced status, and fallback labels.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m py_compile strategies\optimizer.py strategies\optimizer_diagnostics.py views\optimizer_view.py dashboard.py` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- Browser smoke at `http://localhost:8505/portfolio-and-allocation` -> PASS.
- SAW report validation, closure packet validation, and evidence validation -> PASS.

### Open Risks

- Thesis-anchor, MU conviction, WATCH investability, and Black-Litterman policy remain future planning items.

## Latest Addendum - Optimizer Core Policy Audit

### Changed Governance Files

```text
docs/architecture/optimizer_core_policy_audit.md
docs/architecture/optimizer_constraints_policy.md
docs/architecture/optimizer_lower_bound_slsqp_policy.md
docs/saw_reports/saw_optimizer_core_policy_audit_20260510.md
tests/test_optimizer_core_policy.py
```

### Touched Interfaces

- `Optimizer Core Policy`: lower-bound/SLSQP behavior is documented as held, not implemented.
- `Optimizer Tests`: tests lock non-approval and mark known future implementation debt with strict `xfail` cases.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_optimizer_core_policy.py -q` -> PASS with expected strict xfails for known policy debt.

### Open Risks

- Current optimizer still lacks structured infeasibility/fallback diagnostics; this is audit debt and not fixed in this docs/tests-first round.

## Latest Addendum - Portfolio Universe Quarantine Closure

### Changed Governance Files

```text
docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_20260510.patch
docs/quarantine/optimizer_core_lower_bounds_slsqp_diff_note_20260510.md
docs/saw_reports/saw_portfolio_universe_construction_fix_20260510.md
data/providers/legacy_allowlist.py
```

### Touched Interfaces

- `Portfolio Optimizer Core`: no active diff remains in `strategies/optimizer.py`; lower-bound/SLSQP math is quarantined for separate audit only.
- `Universe Closure`: SAW now closes PASS with 9/9 focused checks after quarantine.

### Passing Checks

- `git diff -- strategies/optimizer.py` -> empty.
- `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py tests\test_dash_1_page_registry_shell.py -q` -> PASS, 33 passed.
- `.venv\Scripts\python -m pytest -q` -> PASS.
- `.venv\Scripts\python -m py_compile strategies\portfolio_universe.py views\optimizer_view.py dashboard.py` -> PASS.
- `.venv\Scripts\python scripts\build_context_packet.py --validate` -> PASS.
- Browser smoke at `http://127.0.0.1:8503/portfolio-and-allocation` -> Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render.

### Open Risks

- Optimizer lower-bound/SLSQP policy remains undecided until `OPTIMIZER_CORE_POLICY_AUDIT`.

## Latest Addendum - Portfolio Universe Construction Fix

### Changed Runtime Files

```text
dashboard.py
views/optimizer_view.py
strategies/portfolio_universe.py
tests/test_portfolio_universe.py
tests/test_dash_2_portfolio_ytd.py
docs/architecture/portfolio_construction_contract.md
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/prd.md
docs/spec.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
```

### Touched Interfaces

- `Portfolio Optimizer`: receives audited candidate permnos instead of display-sorted scan tickers.
- `Universe Audit`: reports included/excluded rows, missing ticker mappings, and local price-history failures.
- `Allocation Explanation`: reports thesis-neutral status and max-weight feasibility diagnostics.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_portfolio_universe.py tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 26 passed.
- `.venv\Scripts\python -m py_compile strategies\portfolio_universe.py views\optimizer_view.py dashboard.py` -> PASS.
- Browser smoke at `http://127.0.0.1:8503/portfolio-and-allocation` -> Portfolio Optimizer, Universe Audit, fail-closed no-eligible message, and YTD Performance render.

### Open Risks

- Current cached scan has no optimizer-eligible rows under the conservative policy; this is a fail-closed outcome, not a conviction optimizer.
- MU conviction, WATCH investability, thesis-anchor sizing, Black-Litterman, and manual override remain future approval items.

## Latest Addendum - DASH-2 Portfolio Allocation Runtime Slice

### Changed Runtime Files

```text
dashboard.py
views/optimizer_view.py
tests/test_dash_2_portfolio_ytd.py
docs/notes.md
docs/decision log.md
docs/lessonss.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
```

### Touched Interfaces

- `Portfolio & Allocation`: optimizer is top-level again; YTD Performance renders below optimizer and uses current optimizer weights.
- `Portfolio Optimizer`: selected price series are refreshed in-memory from adjusted-close yfinance data for current display freshness before optimization/allocation rendering.
- `YTD Comparison`: SPY/QQQ benchmarks and selected stock prices are refreshed through the latest available market date without canonical data writes.

### Passing Checks

- `.venv\Scripts\python -m pytest tests\test_dash_2_portfolio_ytd.py -q` -> PASS, 15 passed.
- `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py -q` -> PASS, 7 passed.
- `.venv\Scripts\python -m py_compile dashboard.py views\optimizer_view.py` -> PASS.
- Browser check -> optimizer appears before YTD, SPY/QQQ metrics render, freshness reports `2026-05-08`.

### Open Risks

- yfinance overlay remains a display freshness path, not canonical ingestion.
- Broad dirty worktree remains inherited and out of this narrow runtime slice.

## Header

- `PACKET_ID`: `20260510-d383-phase65-g8-2-system-scouted-candidate-card-impact`
- `DATE_UTC`: `2026-05-10`
- `SCOPE`: `Phase 65 G8.2 System-Scouted Candidate Card`
- `OWNER`: `PM / Architecture Office`

## Changed Files

```text
opportunity_engine/candidate_card_schema.py
data/candidate_cards/MSFT_supercycle_candidate_card_v0.json
data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json
tests/test_g8_2_system_scouted_candidate_card.py
scripts/build_context_packet.py
tests/test_build_context_packet.py
docs/architecture/g8_2_system_scouted_candidate_card_policy.md
docs/handover/phase65_g82_system_scouted_candidate_card_handover.md
docs/phase_brief/phase65-brief.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/planner_packet_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/decision log.md
docs/notes.md
docs/lessonss.md
docs/prd.md
docs/spec.md
README.md
```

Inherited dirty/untracked files from earlier or parallel work remain present in the worktree and are not G8.2-owned unless listed above.

## Touched Interfaces

### Interface 1: Candidate Card Schema

- **Type**: static JSON research-object validator.
- **Owner**: Data + Docs/Ops.
- **Changed**: rejects `factor_score` / `factor_scores` leakage and validates optional governance flags when present.
- **Consumers**: G8 and G8.2 focused tests, future card readers.

### Interface 2: Candidate Card Artifacts

- **Type**: static card and manifest bundle.
- **Owner**: Data.
- **Changed**: added one MSFT card from `LOCAL_FACTOR_SCOUT`.
- **Consumers**: planner/context and future dashboard card reader.

### Interface 3: Context Selection

- **Type**: deterministic context-builder handover selection.
- **Owner**: Docs/Ops.
- **Changed**: G8.2 handover sorts after DASH-1 but before future G9.
- **Consumers**: planner/context bootstrap.

## Failing Checks

- None in current focused verification.
- Broad dirty worktree and inherited broad compileall hygiene remain out of scope.

## Passing Checks

- Focused G8.2 tests: PASS, 13 passed.
- G8/G8.1B/G8.2 regression: PASS, 45 passed.
- Context-builder tests: PASS, 16 passed.
- Scoped compile: PASS.

## Stream Impact

### Backend

- Candidate-card validator updated only for forbidden factor-score leakage and optional governance flags.
- No provider, scoring, ranking, alert, broker, backtest, or dashboard runtime behavior changed.

### Frontend/UI

- No dashboard runtime files changed by G8.2.
- Existing dashboard MSFT rows remain legacy runtime output and are not connected to the MSFT card.
- Future dashboard card reader remains a separate approval.

### Data

- Added one static MSFT card and one manifest.
- No canonical market-data write, no provider call, no ingestion, and no new scout output.

### Docs/Ops

- Policy, handover, current truth surfaces, decision log, notes, lessons, and SAW are G8.2-owned.

## Risks

1. MSFT appearing in the dashboard can be overread as G8.2 card integration.
2. Local factor scout provenance can be overread as factor-model validation.
3. Official/public evidence pointers can be overread as thesis validation.
4. Future dashboard work could accidentally mix candidate-card status with legacy action labels.

## Evidence

- `.venv\Scripts\python -m pytest tests\test_g8_2_system_scouted_candidate_card.py -q` -> PASS, 13 passed.
- `.venv\Scripts\python -m pytest tests\test_g8_supercycle_candidate_card.py tests\test_g8_1b_pipeline_first_discovery_scout.py tests\test_g8_2_system_scouted_candidate_card.py -q` -> PASS, 45 passed.
- `.venv\Scripts\python -m pytest tests\test_build_context_packet.py -q` -> PASS, 16 passed.
- `.venv\Scripts\python -m py_compile opportunity_engine\candidate_card_schema.py opportunity_engine\candidate_card.py tests\test_g8_2_system_scouted_candidate_card.py` -> PASS.
