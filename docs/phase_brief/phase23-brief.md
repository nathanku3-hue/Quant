# Phase 23 Brief: 3-Pillar Hybrid SDM Ingestion (Round 3)
Date: 2026-02-22
Status: Execution Complete (SAW PASS)
Owner: Codex

## 0. Live Loop State (Project Hierarchy)
- L1 (Project Pillar): SDM Ingestion Engine
- L2 Active Streams: Data, Ops
- L2 Deferred Streams: Backend, Frontend/UI
- L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- Active Stream: Data
- Active Stage Level: L3
- Current Stage: Final Verification
- Planning Gate Boundary: in-scope = `scripts/ingest_compustat_sdm.py`, `scripts/ingest_frb_macro.py`, `scripts/ingest_ff_factors.py`, `scripts/assemble_sdm_features.py`, targeted tests, and docs updates; out-of-scope = scorecard/ranking logic changes.
- Owner/Handoff: Owner = Codex implementer; Handoff = SAW Reviewer A/B/C.
- Acceptance Checks: CHK-01..CHK-10 (listed below).

## 1. Objective
- Complete and verify the 4-script SDM data slice:
  - Pillar 1/2 fundamentals (`comp.fundq` + `totalq.total_q`)
  - Pillar 3a macro rates (`frb.rates_daily`)
  - Pillar 3b factors (`ff.fivefactors_daily`)
  - PIT-safe final assembly into `features_sdm.parquet`.

## 2. Implementation Summary
- Fixed `merge_asof` blocker in `scripts/ingest_compustat_sdm.py` by enforcing global timeline-key sorting and explicit sortedness assertions.
- Added dynamic `totalq.total_q` column probing and graceful fallback to stable minimal fields if optional columns are absent.
- Enforced allow+audit identifier policy for unmapped `permno`:
  - retain rows,
  - write audit CSV to `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`.
- Confirmed Pillar 3b source is hardwired to `ff.fivefactors_daily` with all five factors and momentum.
- Added `scripts/assemble_sdm_features.py` for PIT-safe asof joins with strict 14-day stale-data tolerance and atomic output write.
- Added tests:
  - `tests/test_ingest_compustat_sdm.py`
  - `tests/test_assemble_sdm_features.py`

## 3. Artifacts
- `data/processed/fundamentals_sdm.parquet`
- `data/processed/macro_rates.parquet`
- `data/processed/ff_factors.parquet`
- `data/processed/features_sdm.parquet`
- `data/processed/fundamentals_sdm_unmapped_permno_audit.csv`

## 4. Acceptance Checks
- CHK-01: `merge_asof` sort bug fixed with timeline-first ordering and assertions -> PASS.
- CHK-02: `totalq.total_q` dynamic schema probing + graceful fallback implemented -> PASS.
- CHK-03: allow+audit unmapped `permno` policy implemented without row drops -> PASS.
- CHK-04: Pillar 3b source fixed to `ff.fivefactors_daily` with 5 factors + momentum -> PASS.
- CHK-05: `assemble_sdm_features.py` implemented with PIT-safe asof joins -> PASS.
- CHK-06: atomic writes preserved for all output artifacts -> PASS.
- CHK-07: dry-run validation passes on all 4 scripts -> PASS.
- CHK-08: non-dry execution writes all 4 target parquets -> PASS.
- CHK-09: targeted pytest coverage for new logic passes -> PASS.
- CHK-10: docs-as-code updates completed (brief/notes/decision/lessons) -> PASS.

## 5. Verification Evidence
- `.venv\Scripts\python -m pytest tests/test_ingest_compustat_sdm.py tests/test_assemble_sdm_features.py tests/test_ingest_fmp_estimates.py -q` -> PASS (`13 passed`).
- Dry-runs:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31 --dry-run` -> PASS.
  - `.venv\Scripts\python scripts/assemble_sdm_features.py --dry-run` -> PASS.
- Writes:
  - `.venv\Scripts\python scripts/ingest_compustat_sdm.py --tickers NVDA,MU,AMAT,LRCX,KLAC,COHR,TER,CIEN --start-date 2022-01-01 --end-date 2025-12-31` -> PASS.
  - `.venv\Scripts\python scripts/ingest_frb_macro.py --start-date 2022-01-01 --end-date 2025-12-31` -> PASS.
  - `.venv\Scripts\python scripts/ingest_ff_factors.py --start-date 2022-01-01 --end-date 2025-12-31` -> PASS.
  - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS.

## 6. Open Notes
- `frb.rates_daily` in this environment currently ends at 2025-02-13; post-cutoff fundamentals rows are expected to have macro nulls under strict 14-day backward asof tolerance.
- SAW report: `docs/saw_phase23_round3.md` (PASS).

## 7. Rollback Note
- If this round is rejected:
  - remove `scripts/assemble_sdm_features.py`,
  - revert edits in `scripts/ingest_compustat_sdm.py`,
  - remove new tests `tests/test_ingest_compustat_sdm.py`, `tests/test_assemble_sdm_features.py`,
  - regenerate prior artifacts from pre-round scripts.

---

## 8. Action 2 (Manifold Swap) — Execution Record
Date: 2026-02-22  
Status: Execution Complete (SAW PASS)

### Scope
- Daily-cadence SDM expansion and precompute in assembler.
- Dual-read feature adapter (`features.parquet` + `features_sdm.parquet` on `[permno,date]`).
- BGM geometry swap to SDM/macro-only manifold.
- Explicit risk-feature isolation asserts for geometry path.

### Implementation
- `scripts/assemble_sdm_features.py`
  - Added daily forward-fill expansion per `gvkey`.
  - Added precomputed industry medians (`ind_*`) and `CycleSetup`.
  - Preserved strict 14-day tolerance gate and stale-null telemetry.
- `scripts/phase20_full_backtest.py`
  - Added dual-read loader merge with timezone-normalized merge keys.
  - Added migration-safe SDM column overlay.
- `strategies/company_scorecard.py`
  - Added SDM/macro-cycle columns to conviction-frame feature bridge.
  - Routed lagged SDM/macro fields for ticker-pool geometry input.
- `strategies/ticker_pool.py`
  - Replaced default geometry features with SDM/macro-only set.
  - Added explicit assert-based risk-feature leak guards.

### Validation
- Unit tests:
  - `.venv\Scripts\python -m pytest tests/test_assemble_sdm_features.py tests/test_phase20_full_backtest_loader.py tests/test_ticker_pool.py tests/test_company_scorecard.py -q` -> PASS (`40 passed`).
- Smoke:
  - `.venv\Scripts\python scripts/phase21_1_ticker_pool_slice.py --start-date 2024-01-01 --as-of-date 2024-12-24 --top-longs 5 --short-excerpt 5 --dictatorship-mode on --output-csv data/processed/phase23_action2_smoke_sample.csv --output-summary-json data/processed/phase23_action2_smoke_summary.json` -> PASS.
- Output refresh:
  - `.venv\Scripts\python scripts/assemble_sdm_features.py` -> PASS, wrote `data/processed/features_sdm.parquet` (`11254` rows, `82` cols).

### Action 2 Artifacts
- `data/processed/features_sdm.parquet`
- `data/processed/phase23_action2_smoke_sample.csv`
- `data/processed/phase23_action2_smoke_summary.json`
- `tests/test_phase20_full_backtest_loader.py`
- `docs/saw_phase23_round5.md`

---

## 9. Final Closure (Approved and Locked)
Date: 2026-02-22  
Status: APPROVED and CLOSED (User Sign-off)

### Locked State
- `strategies/ticker_pool.py` geometry manifold, centroid ranker, and covariance/hyperparameter settings are now locked for Phase 23 closure.
- No further edits are allowed in this phase to:
  - BGM/geometry feature list,
  - cluster ranker formula,
  - covariance mode/hyperparameters.

### Final Stability Decisions
- Outlier-robust peer neutralization uses cross-sectional medians (industry granularity preferred; sector fallback).
- Covariance mode is locked to diagonal for the clustering distance path.
- Final lean geometry is orthogonal and cycle-aware.

### Closing Evidence (Dictatorship OFF, 2024-12-01 to 2024-12-24)
- `data/processed/phase22_separability_summary_action2_outlierskewfix.json`:
  - `silhouette_score.mean = 0.009045008492558893` (positive),
  - `silhouette_single_class_days = 0`,
  - memory-cycle archetype detection recovered (`MU` top-30 hit-rate > 0 in this closeout run).

---

## 10. Phase 20 Backtest Handoff (Prepared, Not Executed)
Date: 2026-02-22  
Status: Ready for PM approval

### Wiring Confirmation
- `scripts/phase20_full_backtest.py` now explicitly supports SDM adapter input via:
  - `--input-sdm-features` (default: `data/processed/features_sdm.parquet`).
- Loader path remains migration-safe:
  - base `features.parquet` + SDM overlay `features_sdm.parquet` on `[date, permno]`.

### Proposed Full Historical Run Command (3-year window)
```powershell
.\.venv\Scripts\python scripts/phase20_full_backtest.py `
  --input-features data/processed/features.parquet `
  --input-sdm-features data/processed/features_sdm.parquet `
  --start-date 2021-01-01 `
  --end-date 2024-12-31 `
  --cost-bps 5 `
  --top-n-green 20 `
  --top-n-amber 12 `
  --max-gross-exposure 1.0 `
  --output-delta-csv data/processed/phase20_round4_delta_vs_c3.csv `
  --output-equity-png data/processed/phase20_round4_equity_curves.png `
  --output-cash-csv data/processed/phase20_round4_cash_allocation.csv `
  --output-top20-csv data/processed/phase20_round4_top20_exposure.csv `
  --output-summary-json data/processed/phase20_round4_summary.json `
  --output-sample-csv data/processed/phase20_round4_sample_output.csv `
  --output-crisis-csv data/processed/phase20_round4_crisis_turnover.csv
```

### Optional Extended Run Command (5-year window)
```powershell
.\.venv\Scripts\python scripts/phase20_full_backtest.py `
  --input-features data/processed/features.parquet `
  --input-sdm-features data/processed/features_sdm.parquet `
  --start-date 2020-01-01 `
  --end-date 2024-12-31
```

### Compute/Memory Warnings (Pre-Run)
- The 5-year run will materially increase runtime and memory due to:
  - larger union of `permno` columns in wide return matrices,
  - multiple full-frame pivots/joins in the validation path,
  - crisis-window and allocation artifact generation.
- Keep at least ~16 GB free RAM for safer execution; prefer ~32 GB for the 5-year run.
- Disk usage can spike from large CSV/PNG outputs; ensure several GB free in `data/processed/`.

---

## 11. Round 7 (Macro Hard Gates Data Slice)
Date: 2026-02-23  
Status: Execution Complete (Data/Ops scope)

### Scope
- Build a dedicated daily hard-gate artifact from PIT-safe macro features.
- Keep Layer 1 fundamentals/ranker logic unchanged.
- Constrain integration to Data/Ops: no strategy-execution coupling changes in this round.

### Implementation
- `data/macro_loader.py`
  - Added QQQ source (`qqq_close`) and VIX term-structure ratio/backwardation (`vix_term_ratio`, `vix_backwardation`).
  - Added adaptive stress labeling:
    - `slow_bleed_label` from 21d return z + 252d drawdown z.
    - `sharp_shock_label` from 5d return z or drawdown-acceleration z.
  - Added `build_macro_gates(...)` to emit `macro_gates.parquet` with:
    - `state` (`RED/AMBER/GREEN`),
    - `scalar`,
    - `cash_buffer`,
    - `momentum_entry`,
    - `reasons` plus diagnostics.
  - Updated `run_build(...)` to atomically write both:
    - `data/processed/macro_features.parquet`
    - `data/processed/macro_gates.parquet`
- `scripts/validate_macro_layer.py`
  - Extended validation to include `macro_gates.parquet` schema/date/state/range checks.
- `app.py`
  - Data Architecture panel now lists `macro_gates.parquet`.

### Validation
- `.venv\Scripts\python -m pytest tests/test_macro_loader.py -q` -> PASS (`2 passed`).
- `.venv\Scripts\python -m pytest tests/test_updater_parallel.py tests/test_regime_manager.py -q` -> PASS (`7 passed`).

### Artifacts
- `data/processed/macro_features.parquet` (extended schema)
- `data/processed/macro_gates.parquet` (new hard-gate artifact)
- `tests/test_macro_loader.py`

---

## 12. Round 8 (Strategy Consumption + 5Y Baseline)
Date: 2026-02-23  
Status: Execution Complete (Data/Strategy handoff slice)

### Scope
- Wire centralized `macro_gates.parquet` into strategy consumption.
- Enforce strict `t signal -> t+1 execution` for gate control bundle.
- Run 5-year Phase 20 baseline with centralized L2 macro gates.

### Implementation
- `scripts/phase20_full_backtest.py`
  - Added `--macro-gates-path` CLI input.
  - `_load_regime_states(..., return_controls=True)` now consumes `state/scalar/cash_buffer/momentum_entry` from `macro_gates.parquet` and shifts all controls by one day.
  - `_build_phase20_plan(...)` now consumes shifted gate controls:
    - `selected = entry_gate & macro_momentum_entry & rank<=n_target`
    - `risk_budget = min(1-cash_pct, gate_scalar)`
  - Added summary fields:
    - `macro_gate_source`,
    - `macro_gate_source_exists`,
    - `deferred_open_risk`.
- `strategies/regime_manager.py`
  - Added direct macro-gate consumption path when gate columns are present in context.
- Tests:
  - `tests/test_phase20_macro_gates_consumption.py` (new)
  - `tests/test_regime_manager.py` (gate-consumption path coverage)

### 5-Year Baseline Run (Centralized Gates)
- Command:
  - `.venv\Scripts\python scripts/phase20_full_backtest.py --start-date 2020-01-01 --end-date 2024-12-31 --cost-bps 5 --top-n-green 20 --top-n-amber 12 --max-gross-exposure 1.0 --allow-missing-returns --macro-gates-path data/processed/macro_gates.parquet --output-summary-json data/processed/phase23_baseline_macro_summary.json ...`
- Outcome:
  - `Decision = ABORT_PIVOT (3/6 gates)` (script exits non-zero by design when promotion gates fail).
- Phase20 metrics (`data/processed/phase23_baseline_macro_summary.json`):
  - `Total Return = 20.84%` (derived from `CAGR` and `1258` trading days)
  - `CAGR = 3.8648%`
  - `Sharpe = 0.5624`
  - `Max Drawdown = -7.9715%`

### Deferred Risk Confirmation
- Medium Open Risk remains intentionally deferred:
  - hard-gate state transitions still do **not** include `liquidity_air_pocket`, `credit_freeze`, `momentum_crowding`.
  - deferred marker persisted in summary JSON (`deferred_open_risk`).
