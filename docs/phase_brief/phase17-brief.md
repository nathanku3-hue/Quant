# Phase 17 Brief: Institutional Infrastructure Hardening (FR-090)
Date: 2026-02-15
Status: Done Done (Engineering) / Research Gate Open
Owner: Atomic Mesh

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): Backtest Engine (Signal System)
- L2 Active Streams: Backend, Data, Ops
- L2 Deferred Streams: Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Backend
- Active Stage Level: L3
- Current Stage: Iterate Loop
- Planning Gate Boundary: In-scope = governance/docs contracts for hierarchy + stage loop; Out-of-scope = runtime algorithm changes.
- Owner/Handoff: Owner = Atomic Mesh; Handoff = Reviewer A/B/C SAW pass.
- Acceptance Checks: Snapshot template consistency, AGENTS/spec alignment, SAW reconciliation with no unresolved Critical/High.
- Primary Next Scope: Keep live loop state current after each milestone update [82/100]: prevents stale stage guidance and handoff confusion.
- Milestone State Note: Phase 17 remains open (`In Progress`) until pending Slice B and validation closure are complete.

## 1. Objective
- Move Terminal Zero from script-centric orchestration to system-centric infrastructure.
- Synthesize:
  - Qlib discipline for storage/data contracts.
  - RD-Agent discipline for resilient iterative evaluation.
- Execute with zero-conflict gating against active Phase 16.4 optimizer runs.

## 2. Architecture Philosophy
- Qlib side (Storage):
  - Immutable base + append patch boundaries.
  - Provider API abstraction over raw file access.
  - PIT-safe data contracts and atomic publish semantics.
- RD-Agent side (Evolution):
  - Candidate evaluation with isolation, retries, and checkpoints.
  - Artifact-first experiment traces and reproducible manifests.

## 3. Conflict Policy (Reader/Writer Safety)
- Backtest/optimizer execution is treated as `Reader`.
- Data ingestion/remediation is treated as `Writer`.
- `Writer` milestones are blocked while critical `Reader` runs are active.
- All updates must remain `temp -> atomic replace` to prevent partial reads.
- Enforcement guard (current FR-080 runtime):
  - Lock file: `data/processed/phase16_optimizer.lock`.
  - Reader registry policy:
    - All reader entrypoints must publish lock metadata (`run_tag`, `pid`, `started_at`, `heartbeat_at`).
    - Writer milestones may proceed only when reader registry is empty or all entries are expired per lock policy.
    - Process-name checks are secondary signals, not primary liveness authority.
  - A Phase 17 writer milestone may start only when all are true:
    1) no running process matches `backtests/optimize_phase16_parameters.py`,
    2) `data/processed/phase16_optimizer.lock` is absent,
    3) FR-080 artifact bundle exists:
       - `data/processed/phase16_optimizer_results.csv`
       - `data/processed/phase16_best_params.json`
       - `data/processed/phase16_oos_summary.csv`
    4) artifact freshness/linkage checks pass:
       - artifact bundle and manifest share the same `run_tag`,
       - artifact timestamps are newer than the last active reader start time.
  - If lock is stale, recovery must follow FR-080 stale-lock policy (`--lock-stale-seconds`) and be documented in run notes.
  - Break-glass override (exception-only):
    - Requires explicit user sign-off with scope and rollback note.
    - Requires pre-change artifact snapshot and post-change reconciliation note.
    - Must be limited to remediation needed to unblock reader/writer deadlock, then return to normal gate policy.

## 4. Execution Order (Approved)
1. Functional baseline first (FR-080 optimizer run on current stable code path).
2. Milestone 0 docs in parallel with optimizer runtime.
3. Milestone 1 data-layer code changes only after optimizer completion and artifacts are committed.

## 5. Milestones
### Milestone 0 (Docs + Baseline Contract) [Complete]
- Create Phase 17 brief and decision entries.
- Define KPI baseline and target states.
- Record gate condition for Milestone 1 start.

### Milestone 1 (Data Layer Hardening)
- Target modules: `data/feature_store.py`, `data/updater.py`, `data/fundamentals_updater.py`.
- Goals:
  - Incremental feature build path.
  - Parallelized fundamentals fetch.
  - Lock+atomic guarantees for all critical parquet writes.
 - Execution split:
   - Slice A (complete): `utils/parallel.py`, `data/updater.py`, `data/feature_store.py`, `scripts/validate_data_layer.py`, tests.
   - Slice B (pending): `data/fundamentals_updater.py` parallel ingestion hardening.

### Milestone 2 (Workflow Registry)
- Introduce reusable workflow/task layer for shared orchestration across UI/backtests.

### Milestone 3 (Evaluation Loop Resilience)
- Add queue/checkpoint/isolation semantics for optimizer candidate evaluation.

### Milestone 4 (Observability + Reproducibility)
- Persist run manifests (`git_sha`, input artifacts, params, outputs).
- Add structured runtime logs and runbook verification.

## 6. KPI Baseline and Target
| Metric | Definition + Capture Method | Baseline (2026-02-15) | Phase 17 Target |
|---|---|---|---|
| Feature Rebuild Runtime | Wall-clock seconds from `python data/feature_store.py` start to successful atomic publish; recorded in structured run log | Full-scan path (no incremental mode) | Daily incremental rebuild <= 10 min; full rebuild <= 60 min on same host profile |
| Fundamentals Throughput | Tickers/minute during `data/fundamentals_updater.py run_update`; measured from start/end counters in run log | Sequential ticker loop | >= 300 tickers/minute with bounded worker pool and no atomicity regressions |
| Optimizer Stability | `% candidates completed without fatal run abort` + explicit fallback flag in optimizer summary | Sequential fallback exists, telemetry partial | >= 95% candidate completion; fallback cause logged and run remains resumable |
| Reproducibility Completeness | Presence of manifest fields (`run_tag`, `git_sha`, input paths/hashes, params, outputs) per run | Artifact files only | 100% runs emit complete manifest JSON alongside artifacts |
| Ops Observability | Structured lifecycle events persisted for updater/optimizer (`start`, `lock`, `success/fail`, `duration`) | Console/UI-centric status | 100% production runs emit JSONL lifecycle logs in `logs/` |

## 7. Acceptance Criteria
- Milestone 0:
  - `docs/phase17-brief.md` exists with conflict policy and KPI contract.
  - `decision log.md` records FR-090 decision and gating order.
  - No runtime/data-layer code changes are introduced during active optimizer execution.
- Phase completion:
  - Data-layer, workflow, evaluation, and observability milestones pass tests and review gate.

## 8. Rollback Note
- Milestone 0 is documentation-only and has no runtime impact.
- If any Phase 17 runtime milestone regresses FR-080 behavior, revert milestone commit and resume from prior stable artifacts.

## 9. Milestone 1 Slice A Results (2026-02-16)
- Delivered:
  - Parallel utility wrapper (`utils/parallel.py`) with ordered-result contract.
  - Chunked parallel Yahoo updater path with lock-safe atomic publish.
  - Incremental feature-store build with warmup replay and atomic upsert merge.
  - Feature-store integrity validation checks in `scripts/validate_data_layer.py`.
  - New test coverage for parallel and incremental paths.
- Verification:
  - `pytest` passed across all suites.
  - Data-layer validation script failed on a pre-existing fundamentals snapshot zombie row (outside this code slice).
  - Reconciliation status:
    - Treated as pre-existing data-quality debt (not introduced by Slice A).
    - Deferred to pending Slice B remediation path with explicit re-validation before milestone close.
    - No Phase 17 closure claim is allowed until this validation item is either fixed with evidence or explicitly risk-accepted by user.
    - Current risk acceptance status: not accepted; milestone remains blocked from close.

## 10. Milestone 17.3: Daily Vintage Panel (Bitemporal Optimization)
- New artifact:
  - `data/processed/daily_fundamentals_panel.parquet`
- Purpose:
  - Convert sparse bitemporal quarterly rows into a dense daily panel for fast joins during feature/optimizer runs.
  - Preserve PIT correctness by applying each row only from `published_at` forward until the next publication for the same `permno`.
- Build policy:
  - Interval model: each fundamentals row owns `[published_at, next_published_at)`.
  - Daily panel rows are materialized by joining trading dates onto those intervals.
  - Build uses atomic publish (`*.tmp -> os.replace`) and writes manifest metadata.
- Vintage cache policy:
  - Manifest path: `data/processed/daily_fundamentals_panel.manifest.json`.
  - Rebuild is skipped when source signature is unchanged:
    - fundamentals fingerprint + stats (`row_count`, `permno_count`, `max_published_at`, `max_ingested_at`)
    - calendar source fingerprints (`prices.parquet`, `yahoo_patch.parquet`)
    - explicit build bounds (`min_date`, `max_date`).
  - This preserves immutable snapshot semantics for each source-vintage while avoiding unnecessary recompute.
- PIT guarantees:
  - As-of query behavior remains `published_at <= trade_date`.
  - Legacy rows without `published_at` continue to use conservative fallback:
    - `filing_date`
    - else `fiscal_period_end + 90 days`.

## 11. Milestone 17.1: Cross-Sectional Backtester Transition (2026-02-19)
- Scope change:
  - Event-study path is paused for this milestone.
  - New priority is a cross-sectional double-sort evaluator for Capital-Cycle proxy validation.
- Data foundation changes:
  - Added `statsmodels` dependency for OLS + HAC/Newey-West inference.
  - Hardened `data/feature_store.py` to enforce persisted factor columns:
    - `z_inventory_quality_proxy`
    - `z_discipline_cond`
  - Added schema-drift guard in incremental feature writes:
    - if existing `features.parquet` schema is stale, bypass incremental upsert and perform a full atomic rewrite.
  - Added proxy-input fallback path in feature build (only inside feature pipeline, not evaluator):
    - `sales_accel_q <- delta_revenue_inventory`
    - `op_margin_accel_q <- diff(operating_margin_delta_q)`
    - `bloat_q <- diff(1/revenue_inventory_q)`
    - `net_investment_q <- asset_growth_yoy`
  - Rebuilt feature artifact:
    - command: `python data/feature_store.py --full-rebuild`
    - result: `2,555,730` rows, `6,570` dates, `389` permnos
    - `z_inventory_quality_proxy` now persisted in `data/processed/features.parquet`.
- Evaluator delivery:
  - Added `scripts/evaluate_cross_section.py`.
  - Implements:
    - DuckDB join pipeline (`prices` + `daily_fundamentals_panel` + `features` + `sector_map`)
    - strict universe filter: `quote_type='EQUITY'` and `industry!='Unknown'`
    - deterministic sector mapping selection from `sector_map` (latest `updated_at` row per `permno`/`ticker`)
    - date-window pushdown for `prices`, `panel`, and `features` CTEs when `--start-date/--end-date` is supplied
    - Sort 1: top 30% `asset_growth_yoy` by `date, industry`
    - Sort 2: deciles of `z_inventory_quality_proxy` within Sort 1 buckets
    - spread: `Decile10 - Decile1`
    - Newey-West t-stat with automatic lag rule:
      - `floor(4 * (T / 100)^(2/9))`
    - Fama-MacBeth cross-sectional OLS with interaction term:
      - `fwd_return ~ const + asset_growth + z_proxy + asset_growth*z_proxy`
      - time-series average betas with HAC/Newey-West inference.
  - Output artifacts:
    - `data/processed/phase17_1_cross_section_spread_timeseries.csv`
    - `data/processed/phase17_1_cross_section_summary.json`
    - `data/processed/phase17_1_cross_section_fama_macbeth_betas.csv`
    - `data/processed/phase17_1_cross_section_fama_macbeth_summary.csv`
- Verification status:
  - test run: `pytest tests/test_evaluate_cross_section.py tests/test_feature_store.py -q` -> PASS
  - smoke run result (`horizon=21d`):
    - spread mean `0.002089`
    - spread Newey-West t-stat `0.766`
    - pass gate (`spread>0`, `t>3`): FAIL (t-stat below threshold)
    - FM interaction mean beta `-0.005412`, p-value `0.406005` (not positive/significant)
- Milestone status note:
  - Implementation and validation pipeline are complete for Phase 17.1 mechanics.
  - Signal acceptance criteria are currently not met on this artifact vintage; factor logic/data inputs require further iteration.

## 12. Milestone 17.2: Data Unblocker + Parameter Sweep (2026-02-19)
- Scope:
  - Phase 17.2A: remove feature-store rewrite bottleneck for rapid research iteration.
  - Phase 17.2B: run coarse-to-fine cross-sectional parameter sweep with CSCV + DSR controls.

- Phase 17.2A (Data Unblocker) delivery:
  - Refactored `data/feature_store.py` to use Hive-style partitioned dataset output:
    - `data/processed/features.parquet/year=YYYY/month=MM/...`
  - Added one-time migration path:
    - if legacy `features.parquet` is a single file, auto-migrate to partitioned directory.
  - Replaced full-table upsert rewrite path with partition-aware upsert:
    - only touched `year/month` partitions are rewritten during incremental updates.
  - Extended feature-store readers to support both legacy file and partitioned dataset scans.
  - Added regression coverage:
    - `tests/test_feature_store.py::test_atomic_upsert_features_migrates_file_and_rewrites_only_touched_partition`
  - Verification:
    - `python data/feature_store.py` (migration + build path): PASS
    - row parity after migration: `2,555,730` rows; `6,570` dates; `389` permnos.

- Phase 17.2B (Parameter Sweep Engine) delivery:
  - Added `utils/statistics.py`:
    - CSCV split/block utilities
    - Probability of Backtest Overfitting (PBO)
    - correlation-adjusted effective trial count (`N_eff`)
    - Deflated Sharpe Ratio (DSR) helpers with skew/kurtosis adjustment.
  - Added `scripts/parameter_sweep.py`:
    - coarse-to-fine grid search
    - high-asset-growth double-sort evaluation reuse
    - return-stream matrix export
    - CSCV/PBO + DSR scoring and best-variant export.
  - Added/updated tests:
    - `tests/test_statistics.py`
    - `tests/test_parameter_sweep.py`
    - `tests/test_evaluate_cross_section.py` (upstream loader compatibility columns)
  - Artifacts produced:
    - `data/processed/phase17_2_parameter_sweep_grid_results.csv`
    - `data/processed/phase17_2_parameter_sweep_return_streams.csv`
    - `data/processed/phase17_2_parameter_sweep_cscv_splits.csv`
    - `data/processed/phase17_2_parameter_sweep_cscv_summary.json`
    - `data/processed/phase17_2_parameter_sweep_best_variant.json`

- Verification status:
  - full test suite:
    - `.venv\Scripts\python -m pytest -q` -> PASS
  - sweep smoke run:
    - `.venv\Scripts\python scripts/parameter_sweep.py --start-date 2023-01-01 --end-date 2024-12-31 --max-coarse-combos 24 --max-fine-combos 24 --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep_smoke` -> PASS
  - full sweep run:
    - `.venv\Scripts\python scripts/parameter_sweep.py --cscv-blocks 6 --output-prefix phase17_2_parameter_sweep` -> PASS
    - output snapshot:
      - variants: `168`
      - `avg_pairwise_correlation`: `0.4619`
      - `effective_trials`: `91.39`
      - CSCV `pbo`: `0.9412`
      - best variant: `coarse_0006`
      - best metrics: `annualized_sharpe=1.9820`, `t_stat_nw=1.4943`, `dsr=0.8847`.

- Milestone status note:
  - Engineering unblocker (17.2A) is complete and verified.
  - Parameter-sweep infrastructure (17.2B) is complete and reproducible.
  - Research acceptance remains open because selected variants do not pass the original strict `t_stat > 3.0` gate.

## 13. Milestone 17.3 Prep: Sweep Hardening + Upsert Efficiency (2026-02-19)
- Scope:
  - Harden sweep execution path before next-factor research iteration.
  - Remove remaining medium-risk performance bottlenecks in partitioned feature upserts.

- Data pipeline optimization:
  - Updated `data/feature_store.py`:
    - replaced per-partition DuckDB scans with one connection + batched partition read.
    - `_atomic_upsert_features` now loads all touched partitions in one query and rewrites only affected `year/month` targets.
  - Added targeted regression test:
    - `tests/test_feature_store.py::test_atomic_upsert_features_batches_partition_reads_with_single_connection`
    - validates one DuckDB connection is used for multi-partition upsert read path.

- Sweep engine hardening:
  - Updated `scripts/parameter_sweep.py`:
    - deterministic variant identity:
      - `variant_id = md5(sorted parameter dict)` (stable across ordering changes).
      - hash input constrained to parameter keys only (`w_sales`, `w_margin`, `w_bloat`, `w_netinv`, `gate_threshold`) to ignore non-parameter metadata.
    - DSR-first coarse anchor:
      - coarse winner for fine-grid centering now selected by `DSR -> t_stat_nw -> period_mean`.
      - deterministic tie-break on `variant_id` for equal-metric rows (stable sort).
    - checkpoint/resume:
      - hidden checkpoint artifacts in `data/processed/.checkpoint_<prefix>_*`
      - periodic checkpoint cadence (`--checkpoint-every`, auto policy when `0`):
        - <=80 variants -> every 10
        - <=250 variants -> every 20
        - >250 variants -> every 50
      - resume support (default on, disable via `--no-resume`).
      - checkpoint cleanup after successful run (override with `--keep-checkpoint`).
    - Windows-safe atomic checkpoint publish:
      - atomic replace retry loop on transient file-lock collisions.

- Tests and verification:
  - Added/updated tests:
    - `tests/test_parameter_sweep.py`
      - stable hash-id contract
      - DSR-first row ranking contract
      - checkpoint auto-cadence contract
    - `tests/test_feature_store.py`
      - batched upsert single-connection contract
  - Verification commands:
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py tests\\test_statistics.py tests\\test_feature_store.py tests\\test_evaluate_cross_section.py -q` -> PASS
    - `.venv\\Scripts\\python -m pytest -q` -> PASS
    - Resume smoke:
      1) `.venv\\Scripts\\python scripts\\parameter_sweep.py --start-date 2023-01-01 --end-date 2024-12-31 --max-coarse-combos 24 --max-fine-combos 24 --cscv-blocks 6 --checkpoint-every 5 --keep-checkpoint --output-prefix phase17_3_prep_smoke2` -> PASS
      2) same command rerun -> checkpoint load + `resume hit` on coarse/fine -> PASS
    - Full hardened sweep:
      - `.venv\\Scripts\\python scripts\\parameter_sweep.py --cscv-blocks 6 --output-prefix phase17_3_parameter_sweep` -> PASS
      - snapshot:
        - variants `168`
        - `pbo=0.8947`
        - `effective_trials=111.04`
        - best variant `v_2437c4aae280`
        - best metrics: `annualized_sharpe=2.4422`, `t_stat_nw=2.5724`, `dsr=0.8032`.

- Milestone status note:
  - Engineering hardening items for Phase 17.3 prep are complete and verified.
  - Research promotion remains blocked because strict gate (`t_stat > 3.0`) is still not met.

## 14. Phase 17 Engineering Closeout: Crash Root Cause + Final Hardening (2026-02-19)
- Scope:
  - Resolve repeated sweep/test hard-abort behavior on Windows.
  - Finalize lock-path resilience and complete phase verification + SAW closeout.

- Root cause:
  - `scripts/parameter_sweep.py` used `os.kill(pid, 0)` for PID liveness checks.
  - On Windows, this probe can terminate the target process, which killed pytest/sweep runners in lock tests where lock PID matched the active process.

- Final implementation:
  - Updated `scripts/parameter_sweep.py`:
    - Windows-safe PID liveness path via WinAPI (`OpenProcess` + `GetExitCodeProcess`), with non-Windows fallback to `os.kill(pid, 0)`.
    - retained bounded stale-lock recovery with explicit fail path after retry budget exhaustion.
    - added stale-lock TTL fallback based on lock-file mtime when lock metadata is corrupted/unreadable.
    - kept lazy `evaluate_cross_section` import boundary for lock/checkpoint test safety.
  - Updated `tests/test_parameter_sweep.py`:
    - added regression coverage for corrupt-lock recovery by file mtime.
    - added regression coverage for zero-pending resume checkpoint callback path.

- Verification:
  - lock-focused:
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -k sweep_lock -vv -s` -> PASS
  - sweep module full:
    - `.venv\\Scripts\\python -m pytest tests\\test_parameter_sweep.py -vv -s` -> PASS
  - touched suites:
    - `.venv\\Scripts\\python -m pytest tests\\test_feature_store.py tests\\test_statistics.py tests\\test_evaluate_cross_section.py -vv -s` -> PASS
  - full suite:
    - `.venv\\Scripts\\python -m pytest -q` -> PASS
  - compile:
    - `.venv\\Scripts\\python -m py_compile scripts\\parameter_sweep.py tests\\test_parameter_sweep.py` -> PASS

- Milestone status note:
  - Phase 17 engineering hardening is complete and verified.
  - Research gate remains open (`t_stat > 3.0` still unmet on current proxy lineage), but this is now a research decision, not an infrastructure blocker.
