# Phase 53: Canonical Data Kernel and Expert-Gate Integration Roadmap

Current Governance State: The Phase 53 research-v0 data-kernel closeout is complete for the repo-local scope. The Phase 53-61+ roadmap remains the planning SSOT, no further in-scope Phase 53 execution is required in this round, and allocator/meta/event/shadow execution remains blocked.

**Status**: COMPLETE (Phase 53 Research-v0 Closeout)
**Created**: 2026-03-14
**Authority**: `D-285` (planning SSOT) | `D-288` (execution authorization)
**Execution Authorization**: Approved on 2026-03-15 via the exact token `approve next phase`. Scope is limited to Phase 53 Data Kernel (research-v0) implementation only; allocator/meta/event/shadow execution remains blocked until explicitly authorized.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Multi-Sleeve Research Kernel + Governance Stack
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Data
- **Active Stage Level**: L3
- **Current Stage**: Final Verification (Complete)
- **Execution Gate Boundary**: In = `data/research_connector.py`, `allocator_cpcv.sql`, `scripts/build_phase53_allocator_state.py`, `scripts/build_phase53_cpcv_shards.py`, `scripts/run_allocator_cpcv.py`, `scripts/benchmark_phase53_data_kernel.py`, execution evidence, and same-round docs updates. Out = allocator/meta/event/shadow execution, new strategy logic, dashboard enablement, and any post-Phase-53 scope expansion.
- **Owner/Handoff**: Codex implementer -> PM/CEO review
- **Acceptance Checks**: `CHK-P53-DK-01`..`CHK-P53-DK-08`
- **Primary Next Scope**: Hold the Phase 53 data-kernel closeout, refresh the context packet, and keep Phase 54+ work behind explicit approval [90/100: given repo constraints]

## 1. Problem Statement
- **Context**: `D-284` closed Phase 52 at the Week 3 SMA200 endpoint and explicitly deferred any sector-cap or modular expansion to a separately scoped future phase. You requested a codebase walk-through and a documented Phase 53-61+ roadmap before any new implementation begins; that roadmap now governs the Phase 53 execution scope.
- **User Impact**: The repo now needs execution-grade data-kernel artifacts plus an updated SSOT that preserves the holdout/search-control contract and prevents Phase 53 scope drift beyond research-v0.

## 2. Goals & Non-Goals
- **Goal**: Execute the Phase 53 research-v0 data-kernel contracts (allocator_state + CPCV shards + research guard) and capture evidence for `CHK-P53-DK-01..08`.
- **Goal**: Preserve the layered Phase 53-61+ roadmap as the planning SSOT and map each future workstream to existing repo hooks plus explicit missing hooks.
- **Goal**: Preserve the Phase 52 lock, approval token discipline, holdout quarantine, same-window/same-cost evidence gate, and trial-cap governance.
- **Non-Goal**: No execution beyond Phase 53 research-v0 data-kernel scope.
- **Non-Goal**: Do not reopen Phase 52 Week 4 from this kickoff.
- **Non-Goal**: Do not treat `MIGRATE` as an execution token unless governance is later updated explicitly.

## 3. Phase Boundary Checklist
- **Phase 52 close lock**: `D-284` remains the authority; Week 3 is the endpoint and Week 4 is not reopened here.
- **Phase 53 state**: execution authorized for research-v0 data-kernel scope only; allocator/meta/event/shadow execution remains blocked.
- **Phase 53 execution**: authorized on 2026-03-15 (exact `approve next phase` token); research-v0 data-kernel scope only.
- **Execution predicate**: `phase53_execution_authorized = 1[(reply contains exact 'approve next phase') and (NextPhaseApproval == APPROVED)]`.
- **NextPhaseApproval**: `APPROVED`.
- **Context predicate**: `active_phase = 53` is a context label only; it is not an execution token by itself.
- **Variant-budget precedence**: `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.

## 4. Codebase Walk-Through and Reusable Hooks

### 4.1 Governance / Multiple-Testing Reuse
- **Existing hooks**:
  - `utils/statistics.py` implements `effective_number_of_trials`, `cscv_analysis`, `expected_max_sharpe`, and `deflated_sharpe_ratio`.
  - `scripts/parameter_sweep.py` operationalizes CSCV/PBO/DSR/N_eff with checkpointing and deterministic variant IDs.
  - `tests/test_statistics.py` and `tests/test_parameter_sweep.py` cover the reusable governance math.
- **Missing hooks**:
  - No nested allocator CPCV wrapper exists.
  - No SPA or White Reality Check helper exists in-tree.

### 4.2 Core Sleeve / Rule-of-100 Reuse
- **Existing hooks**:
  - `strategies/supercycle_signal.py` already computes `score_100`.
  - `docs/phase36_rule100_registry.md` records the Rule-of-100 research-track registry.
  - `scripts/rule_100_backtest_decades.py` and the modular registry block in `dashboard.py` contain historical Rule-of-100 framing.
- **Missing hooks**:
  - No governed bridge ties Rule of 100 into a Phase 53 core-sleeve lattice.
  - No locked `15%-20%` pass-rate controller exists for `f(margin, supply, demand, pricing_power)`.

### 4.3 Event / PEAD Reuse
- **Existing hooks**:
  - `data/calendar_updater.py`, `data/dashboard_data_loader.py`, and `strategies/investor_cockpit.py` already load and consume `earnings_calendar.parquet`.
  - `backtests/event_study_csco.py` provides a bounded event-study scaffold.
- **Missing hooks**:
  - No vectorized PEAD sleeve exists.
  - No corporate-actions sleeve exists.
  - No governed net-of-cost PEAD IR/turnover report exists.

### 4.4 Portfolio / Shadow Reuse
- **Existing hooks**:
  - `strategies/phase37_portfolio_registry.py`, `scripts/phase37_risk_diagnostics.py`, and `scripts/phase37_portfolio_construction_runner.py` already define sleeve inputs, risk primitives, and atomic output paths.
  - `scripts/build_shadow_monthly.py` and `scripts/build_shadow_feature_artifact.py` provide atomic shadow-artifact builders.
  - `views/elite_sovereign_view.py` already reads shadow/paper outputs in a dashboard surface.
- **Missing hooks (Shadow-v1)**:
  - No dedicated read-only DuckDB shadow NAV query surface exists.
  - No monitoring/alert query contract built on `allocator_state` exists yet.
- **Research-v0 contract boundary (Phase 53)**:
  - `allocator_state` parquet + DuckDB view contract implemented in Phase 53 execution; Shadow-v1 consumes it later.
  - `connect_research()` guard implemented in Phase 53 execution; Shadow-v1 reuses it.

### 4.5 Data Kernel / DuckDB Reuse
- **Existing hooks**:
  - `data/dashboard_data_loader.py` already runs DuckDB directly over parquet and enforces fail-closed macro/liquidity reads.
  - `data/feature_store.py` and multiple script runners already use temp -> replace atomic write patterns.
- **Execution status (Phase 53)**:
  - `scripts/derive_phase53_sources_from_phase17.py` now derives repo-local in-sample source contracts from `phase17_3_parameter_sweep_return_streams.csv`, `phase17_3_parameter_sweep_grid_results.csv`, and `phase17_3_parameter_sweep_cscv_summary.json`.
  - Sleeve-state cube parquet writer is implemented and evidenced from `data/processed/phase53_allocator_state_source.parquet` into `research_data/allocator_state_cube`.
  - CPCV fold/year/month shard materialization is implemented and evidenced from `data/processed/phase53_cpcv_source.parquet` into `research_data/alloc_cpcv_splits`.
  - Persisted read-only research catalog (`research_data/catalog.duckdb`) + `allocator_state` view are implemented and evidenced; `connect_research()` now also publishes a session-local absolute `allocator_state` temp view so queries remain cwd-independent without mutating the quarantined catalog.
  - Benchmark harness now records sampled 8-thread peak working-set memory + elapsed time on Windows; current repo-local evidence is `45.769531 MB` peak and `0.206855 s` total elapsed with `within_memory_limit=true`.
  - CPCV SQL runner now hard-rejects `max_date > 2022-12-31`; current evidence records `guard_predicate = snapshot_date <= DATE '2022-12-31'` and `row_count = 105081`.
  - Research root quarantine is evidenced with a Windows ACL that denies `WriteData/AddFile` and `AppendData/AddSubdirectory` on the `research_data` root while preserving read traversal for the catalog and parquet tree.
  - Directory overwrite publication for the research artifacts is now fail-closed: the builders require a fresh `--output-dir` because canonical directory replacement cannot guarantee atomic overwrite semantics.

### 4.6 Meta-Layer Gap
- **Existing hooks**:
  - Phase 37 sleeves and risk primitives provide the nearest sleeve-level input surface.
  - Phase 17 governance math provides the nearest reusable search-control path.
- **Missing hooks**:
  - No BPPP-style meta-weighter exists.
  - No sleeve-feature matrix or meta-layer trial runner exists.

## 5. Hook Traceability Matrix
| Hook Family | Path / Symbol | State | Notes |
| --- | --- | --- | --- |
| Governance reuse | `utils/statistics.py::effective_number_of_trials`, `deflated_sharpe_ratio`, `cscv_analysis` | Existing | Reusable Phase 17 search-control math already in-tree. |
| Governance runner | `scripts/parameter_sweep.py` checkpoint + CSCV/DSR flow | Existing | Current bounded sweep surface; nearest allocator-governance reuse point. |
| Rule-of-100 lineage | `strategies/supercycle_signal.py::score_100` | Existing | Current Rule-of-100 score anchor for future lattice integration. |
| Rule-of-100 registry | `docs/phase36_rule100_registry.md`, `scripts/rule_100_backtest_decades.py`, `dashboard.py` | Existing | Historical research lineage and UI framing already documented. |
| Earnings calendar | `data/calendar_updater.py`, `data/dashboard_data_loader.py`, `strategies/investor_cockpit.py` | Existing | Current calendar loader/consumer surface for PEAD work. |
| Event-study scaffold | `backtests/event_study_csco.py::run_event_study` | Existing | Bounded event-study scaffold, not yet a governed PEAD sleeve. |
| Shadow/risk primitives | `strategies/phase37_portfolio_registry.py`, `scripts/phase37_risk_diagnostics.py`, `scripts/phase37_portfolio_construction_runner.py`, `scripts/build_shadow_monthly.py`, `views/elite_sovereign_view.py` | Existing | Atomic writes and shadow-view surfaces already present. |
| Allocator CPCV SQL | `allocator_cpcv.sql` | Implemented + evidenced | Guarded run evidence captured in `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json`. |
| Allocator state contract (research-v0) | `scripts/build_phase53_allocator_state.py` + `allocator_state` view | Implemented + evidenced | Materialized from Phase 17.3-derived source rows into `research_data/catalog.duckdb`; Shadow-v1 consumes it later. |
| Research connector guard (research-v0) | `data/research_connector.py::connect_research` | Implemented + evidenced | Read-only quarantine guard is live against the repo-local `research_data` root; Shadow-v1 reuses it. |
| SPA / White Reality Check helper | allocator governance helper | Missing | No repo-local allocator SPA/WRC helper exists today. |
| Meta-layer runner | BPPP sleeve weighter runner | Missing | Future Phase 61-only execution surface. |

## 6. Missing Hook Delivery Map
| Missing Hook | Owner | Target Phase | Acceptance Evidence |
| --- | --- | --- | --- |
| `allocator_cpcv.sql` + CPCV split materialization | Backend/Data implementer | Phase 53 | Implemented + evidenced (`CHK-P53-DK-02`, `CHK-P53-DK-05`). |
| allocator CPCV / SPA wrapper | Backend/Governance implementer | Phase 55 | Same-window, same-cost CPCV + DSR/PBO/SPA evidence on active-alpha series. |
| `allocator_state` parquet + view (research-v0) | Backend/Data implementer | Phase 53 | Implemented + evidenced (`CHK-P53-DK-03`, `CHK-P53-DK-06`). |
| `connect_research()` guard (research-v0) | Backend/Ops implementer | Phase 53 | Implemented + evidenced (`CHK-P53-DK-04`). |
| Shadow NAV/alert surface (shadow-v1) | Backend/Ops implementer | Phase 59 | Read-only query/alert contract documented plus dashboard evidence. |
| PEAD sleeve runner + cost-aware report | Strategy/Data implementer | Phase 56 | Net-of-cost IR/turnover evidence on governed PEAD family. |
| corporate-actions taxonomy | Strategy/Data implementer | Phase 57 | Eligible-denominator and confirmation logic documented after Phase 56 OOS clearance. |
| BPPP sleeve-feature matrix + runner | Backend/Strategy implementer | Phase 61 | Pre-2023-only meta run with governed variant lattice and audit evidence. |

## 7. Phase 53-61+ Roadmap Summary
- **Phase 53 - Canonical Data Kernel**: build monthly snapshots and sleeve-state cube on DuckDB/parquet foundations; reuse atomic parquet + DuckDB patterns; new CPCV materialization contracts required.
- **Phase 54 - Core Sleeve 2.0**: integrate Rule of 100 into the core sleeve using existing `score_100` research lineage; new governed pass-rate and lattice checks required.
- **Phase 55 - Opportunity-Set Controller**: apply nested CPCV + DSR/PBO/SPA to allocator rules; reuse Phase 17 math; new allocator wrapper and SPA helper required.
- **Phase 56 - Event Sleeve 1 (PEAD)**: build a vectorized PEAD sleeve on top of earnings/calendar infrastructure and event-study learnings.
- **Phase 57 - Event Sleeve 2 (Corporate Actions)**: defer until PEAD OOS validation clears; use the same eligible denominator and confirmation logic family.
- **Phase 58 - Governance Layer**: propagate the same DSR/PBO/SPA and one-shot post-2022 audit to every allocator/meta family.
- **Phase 59 - Shadow Portfolio**: extend shadow builders and dashboard surfaces into a read-only DuckDB/Polars monitoring stack with explicit holdout quarantine.
- **Phase 60 - Stable Shadow Portfolio**: run the multi-sleeve + allocator book as a paper-only shadow stack and execute the one-shot post-2022 audit on all gates.
- **Phase 61 - Meta-Layer**: add the BPPP shrinkage weighter on pre-2023 sleeve-state data only; preserve the same trial budget and holdout rules.

## 8. Execution Guardrails (Locked)
- **Variant-budget interpretation**: `global_active_variants <= 18` is the default governance ceiling; only an explicit execution packet may narrow or override it.
- **Approval token precedence**: Phase 53 execution is now authorized; future scope expansion remains blocked until explicitly approved.
- **Evidence gate**: any risk/execution/meta layer must prove deltas versus the latest baseline in the same window, at the same costs, on the same `core.engine.run_simulation` path.
- **Research-v0 boundary**: Phase 53 data-kernel scope includes the research-only `allocator_state` parquet+view contract and the `connect_research()` quarantine guard; Shadow-v1 monitoring/UI surfaces remain Phase 59.
- **DuckDB contract**: use a persisted read-only research catalog at `research_data/catalog.duckdb` with a registered `allocator_state` view over hive-partitioned parquet.

## 9. Acceptance Criteria (Phase 53 Data Kernel Execution Packet - Active)
- [x] `CHK-P53-DK-01`: Research-v0 boundary documented (allocator_state + connect_research in Phase 53; Shadow-v1 monitoring in Phase 59).
- [x] `CHK-P53-DK-02`: `allocator_cpcv.sql` exists with documented CPCV split inputs and fold/year/month shard contract; evidence captured in `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json`.
- [x] `CHK-P53-DK-03`: Sleeve-state cube persisted as hive-partitioned parquet (`variant_id=...`) with `allocator_state` view registered in `research_data/catalog.duckdb`; evidence captured in `research_data/allocator_state_cube/allocator_state_manifest.json`.
- [x] `CHK-P53-DK-04`: `connect_research()` guard specified with temp-write probe, symlink scan, and read-only DuckDB connect to the research catalog; repo-local live query now passes against the quarantined `research_data` root.
- [x] `CHK-P53-DK-05`: CPCV materialization path documented as fold/year/month parquet shards with bounded memory read strategy; evidence captured in `research_data/alloc_cpcv_splits/cpcv_splits_manifest.json`.
- [x] `CHK-P53-DK-06`: 8-thread benchmark evidence shows peak process memory <2GB and scan-time recorded for the data-kernel paths (`overall_peak_memory_mb = 45.769531`, `within_memory_limit = true`).
- [x] `CHK-P53-DK-07`: SQL runner wrapper includes date-bound assertion to block post-2022 leakage, rejects `max_date > 2022-12-31`, and records evidence in `docs/context/e2e_evidence/phase53_allocator_cpcv_run.json`.
- [x] `CHK-P53-DK-08`: Context packet build + validate ran after the evidenced DK execution packet was finalized.

## 10. Acceptance Criteria (Docs-Only Kickoff - Closed)
- [x] `CHK-P53-PLAN-01`: This brief recorded the Phase 53 planning kickoff and preserved `D-284` as the locked Phase 52 endpoint.
- [x] `CHK-P53-PLAN-02`: `docs/handover/phase53_kickoff_memo_20260314.md` records the full Phase 53-61+ layered roadmap plus repo-hook mapping.
- [x] `CHK-P53-PLAN-03`: `docs/decision log.md` recorded the planning-only Phase 53 open and the approval gate later satisfied by `approve next phase`.
- [x] `CHK-P53-PLAN-04`: `docs/notes.md` records the explicit planning formulas; runtime-enabled items are now tracked under Phase 53 execution.
- [x] `CHK-P53-PLAN-05`: `docs/lessonss.md` records the same-round guardrail for planning-only phase opens.
- [x] `CHK-P53-PLAN-06`: `.venv\Scripts\python scripts\build_context_packet.py` and `--validate` both pass after the docs update.

## 11. Rollback Plan
- **Trigger**: Any Phase 53 data-kernel change that violates the research quarantine, exceeds the memory guardrails, or reopens Phase 52.
- **Action**: Revert Phase 53 data-kernel scripts/docs only. Do not alter the locked Phase 52 artifacts or `D-284`.

## 12. New Context Packet (Phase 53 Execution)

## What Was Done
- Executed the Phase 53 research-v0 data-kernel implementation plan and captured repo-local evidence for allocator_state, CPCV shards, the research guard, the date-bound SQL wrapper, and the 8-thread benchmark.
- Derived the Phase 53 source-contract parquets from Phase 17.3 sweep artifacts via `scripts/derive_phase53_sources_from_phase17.py` on the in-sample window `snapshot_date <= 2022-12-31`.
- Refreshed and validated the context packet after the evidence-bearing SSOT updates.
- Preserved the Phase 52 `D-284` endpoint, holdout/search-control contract, and approval-token discipline.

## What Is Locked
- `D-284` remains the governing decision for Phase 52: Week 3 is the endpoint and Week 4 is not reopened here.
- Phase 53 execution is limited to research-v0 data-kernel scope only.
- Future execution layers must keep same-window, same-cost, same-`core.engine.run_simulation` evidence and the holdout quarantine.
- NextPhaseApproval: APPROVED.

## What Is Next
- Phase 53 data-kernel closeout is complete for the repo-local research-v0 scope; no further in-scope execution is required in this round.
- Keep `global_active_variants <= 18` unless a later execution packet explicitly replaces it with tighter scheduling rules.
- Phase 54+ remains blocked until a later roadmap packet is explicitly approved.

## Next Phase Roadmap Summary
- Phase 53: Canonical Data Kernel and sleeve-state cube.
- Phase 54: Core Sleeve 2.0 / Rule of 100 integration.
- Phase 55: Opportunity-Set Controller with nested CPCV + DSR/PBO/SPA.
- Phase 56-57: PEAD then corporate-actions event sleeves.
- Phase 58-61: governance propagation, shadow stack, stable shadow, and BPPP meta-layer.

## First Command
```text
.venv\Scripts\python scripts\build_phase53_allocator_state.py --input <in_sample_allocator_state.parquet> --output-dir <fresh_allocator_state_cube_dir>
```
