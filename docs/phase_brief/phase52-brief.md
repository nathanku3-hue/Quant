# Phase 52: Current Strategy Crisis Validation Baseline

Current Governance State: Phase 52 Week 1 (baseline extension only). Runtime surface: `backtests/`, `scripts/`, `tests/`, `docs/`. Goal: extend Phase 50 4-factor equal-weight strategy to 2007-2024 unchanged, measure crisis performance (2008 GFC, 2020 COVID, 2022 drawdowns), establish clean baseline for future incremental enhancements.

**Status**: ACTIVE CURRENT GOVERNANCE STATE (Week 1 baseline extension only, no logic changes)
**Created**: 2026-03-13
**Authority**: `D-280`
**Execution Authorization**: Week 1 baseline extension only. No binary regime changes, no sector caps, no drawdown deleveraging, no supercycle logic, no new factor formulations. Week 2+ enhancements explicitly deferred until Week 1 baseline evidence exists and passes acceptance.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Current Strategy Crisis Validation Baseline
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Planning
- **Planning Gate Boundary**: In = `backtests/phase52_baseline_2007_2024.py`, focused tests, crisis performance report, comparison table vs Phase 50 baseline, same-round docs updates. Out = `strategies/`, `dashboard.py`, `main_bot_orchestrator.py`, regime changes, sector caps, drawdown deleveraging, Week 2+ enhancements.
- **Owner/Handoff**: Codex implementer -> CEO review
- **Acceptance Checks**: `CHK-P52-W1-01`..`CHK-P52-W1-08`
- **Primary Next Scope**: Implement unchanged baseline extension, measure 2008/2020/2022 crisis performance, compare vs Phase 50 baseline, publish Week 1 evidence [92/100: given repo constraints]

## 1. Problem Statement
- **Context**: Phase 50 closed with 30-day paper curve validation on 2022-2024 holdout only. Phase 51 complex supercycle formulation failed (0 strict survivors, mean_sharpe 0.45). Expert consensus recommends extending the current working strategy to earlier crisis periods first, establishing an unchanged baseline, then layering enhancements incrementally with causal attribution.
- **User Impact**: The repo can now validate whether the Phase 50 4-factor equal-weight strategy is crisis-robust on 2008 GFC and 2020 COVID periods before investing effort in enhancements. Clean baseline enables defensible delta attribution for future Week 2+ enhancements.

## 2. Goals & Non-Goals
- **Goal**: Extend Phase 50 4-factor equal-weight strategy to 2007-2024 unchanged (same engine, same cost, same logic).
- **Goal**: Measure crisis performance: 2008 max DD, 2020 max DD, 2022 max DD, Sharpe ratio (2007-2024 full period), recovery time from max DD, Ulcer index by regime.
- **Goal**: Compare extended baseline vs Phase 50 baseline (2022-2024 holdout) to verify consistency.
- **Goal**: Establish clean baseline for future incremental enhancements (Week 2: binary regime, Week 3: sector caps, Week 4: drawdown deleveraging).
- **Non-Goal**: Implement any logic changes in Week 1 (no regime changes, no sector caps, no drawdown deleveraging, no supercycle logic).
- **Non-Goal**: Open Week 2+ enhancements before Week 1 baseline evidence exists and passes acceptance.
- **Non-Goal**: Create new parallel scorer modules or bundled enhancement packages.

## 3. Locked Phase 50 Baseline (Week 1 Reference)

### Current Strategy (Unchanged for Week 1)
```python
# 4-factor equal-weight (Phase 50)
momentum: 0.25 (resid_mom_60d)
quality: 0.25 (quality_composite)
volatility: 0.25 (realized_vol_21d, negative)
illiquidity: 0.25 (amihud_20d, negative)

# Selection
top_n = 5 (enter ≤5, hold ≤20)

# Regime (3×3 matrix)
RED/AMBER/GREEN × NEG/NEUT/POS → exposure 0.0-1.3×

# Cost
transaction_cost = 10bps (unchanged)
```

### Extended Windows (Week 1)
```python
train: 2007-01-01 to 2019-12-31  # Includes 2008 GFC
validation: 2020-01-01 to 2021-12-31  # COVID crash
holdout: 2022-01-01 to 2024-12-31  # Current (Phase 50 paper curve)
```

### Metrics to Measure (Week 1)
- Max DD in 2008 (vs SPY -57%)
- Max DD in 2020 (vs SPY -34%)
- Max DD in 2022 (vs SPY -20%)
- Sharpe ratio (2007-2024 full period)
- Recovery time from max DD
- Ulcer index by regime
- Comparison: Phase 50 baseline (2022-2024) vs extended baseline (2007-2024)

### Acceptance Criteria (Week 1)
- Max DD 2008 <30% (vs SPY -57%)
- Max DD 2020 <20% (vs SPY -34%)
- Sharpe >0.6 on full period (2007-2024)
- Recovery time <6 months from max DD
- Evidence: same engine as Phase 50, same cost (10bps), same logic

## 4. Week 1 Deliverables
- `backtests/phase52_baseline_2007_2024.py` (reuse existing engine, extend windows only)
- Crisis performance report (2008/2020/2022 metrics)
- Comparison table: Phase 50 baseline vs extended baseline
- Evidence: same engine, same cost (10bps), same logic
- Focused tests: `tests/test_phase52_baseline_2007_2024.py`
- Week 1 evidence summary: `docs/handover/phase52_week1_baseline_evidence.md`

## 5. Week 2+ Enhancements (Deferred Until Week 1 Passes)

### Week 2: Binary Regime (Single Enhancement)
- Replace 3×3 matrix with binary VIX >30 gate
- Measure: Delta max DD 2008/2020 vs Week 1 baseline
- Attribution: Regime change only (all other logic unchanged)

### Week 3: SMA200 Trend Filter (Single Enhancement)
- Add SPY SMA200 half-exposure rule (0.5× when SPY < MA200, 1.0× when SPY ≥ MA200)
- Measure: Delta Sharpe/max DD vs Week 2 Trial 14 state
- Attribution: Trend filter only (regime from Week 2 unchanged)
- Note: Sector caps deferred (out of scope for current remedial enhancement sequence)

### Week 4: Drawdown Deleveraging (Single Enhancement)
- Add drawdown-triggered deleveraging (10%/15%/20% thresholds)
- Measure: Delta max DD vs Week 3 state
- Final comparison: Phase 52 final vs Phase 50 baseline

## 6. Scope Boundaries (Week 1)
- **In scope**: Extend Phase 50 strategy to 2007-2024 unchanged, measure crisis performance, compare vs Phase 50 baseline, publish Week 1 evidence
- **Out of scope**: Binary regime changes, sector caps, drawdown deleveraging, supercycle logic, new factor formulations, portfolio construction changes, cost model changes, Week 2+ enhancements

## 7. Acceptance Checks (Week 1)
- `CHK-P52-W1-01` PENDING - `backtests/phase52_baseline_2007_2024.py` implements unchanged Phase 50 strategy with extended windows (2007-2024)
- `CHK-P52-W1-02` PENDING - Crisis performance metrics measured: 2008 max DD, 2020 max DD, 2022 max DD, Sharpe ratio (2007-2024), recovery time, Ulcer index
- `CHK-P52-W1-03` PENDING - Comparison table: Phase 50 baseline (2022-2024) vs extended baseline (2007-2024) shows consistency
- `CHK-P52-W1-04` PENDING - Acceptance criteria met: Max DD 2008 <30%, Max DD 2020 <20%, Sharpe >0.6, recovery time <6 months
- `CHK-P52-W1-05` PENDING - Focused tests pass: `tests/test_phase52_baseline_2007_2024.py`
- `CHK-P52-W1-06` PENDING - Week 1 evidence summary published: `docs/handover/phase52_week1_baseline_evidence.md`
- `CHK-P52-W1-07` PENDING - No logic changes introduced: same engine, same cost (10bps), same factor weights, same regime matrix
- `CHK-P52-W1-08` PENDING - Week 2+ enhancements remain deferred until Week 1 baseline evidence passes acceptance

## 8. Rollback Note
If Week 1 baseline fails acceptance criteria, current strategy is not crisis-robust and requires fundamental redesign before any enhancements. Week 2+ enhancements are blocked until Week 1 baseline evidence exists and passes acceptance.
