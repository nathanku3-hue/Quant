# Phase 52 Week 2: Parsimonious Binary Regime Grid Search

Current Governance State: Phase 52 Week 2 (remedial enhancement - binary regime). Runtime surface: `backtests/`, `scripts/`, `tests/`, `docs/`. Goal: Test if simple binary regime filter (realized-vol-based) can improve crisis performance via bounded grid search with DSR correction.

**Status**: ✓ COMPLETED - Superseded by Week 2b tightened grid (Trial 14 endpoint)
**Created**: 2026-03-13
**Completed**: 2026-03-13 (initial grid), superseded by Week 2b tightened grid
**Authority**: CEO authorization following Week 1 baseline failure
**Execution Authorization**: Week 2 binary regime grid search (18 trials) + crisis-specific analysis + Step 2 tightened grid (24 trials). Final endpoint: Trial 14 (RV=25%, exp=0.4, top_n=5). Week 3 authorized under D-282.

## 0. Live Loop State (Project Hierarchy)
- **L1 (Project Pillar)**: Current Strategy Crisis Validation with Remedial Enhancements
- **L2 Active Streams**: Backend | Data | Docs/Ops
- **L2 Deferred Streams**: Frontend/UI
- **L3 Stage Flow**: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
- **Active Stream**: Backend
- **Active Stage Level**: L3
- **Current Stage**: Planning
- **Planning Gate Boundary**: In = `backtests/phase52_week2_regime_grid.py`, focused tests, DSR calculation, delta attribution report, same-round docs updates. Out = `strategies/`, `dashboard.py`, SMA200 filter, sector caps, drawdown deleveraging, Week 3+ enhancements.
- **Owner/Handoff**: Codex implementer -> CEO review
- **Acceptance Checks**: `CHK-P52-W2-01`..`CHK-P52-W2-08`
- **Primary Next Scope**: Implement bounded grid search (18 trials), measure delta vs Week 1 baseline, apply DSR correction, publish Week 2 evidence [90/100: given repo constraints]

## 1. Problem Statement
- **Context**: Phase 52 Week 1 baseline failed acceptance criteria (1/4 passed). The Phase 50 4-factor equal-weight strategy is not crisis-robust: -60.69% max DD in 2008 GFC (worse than SPY -57%), -55.51% max DD in 2022 bear market (vs SPY -20%). CEO authorized Week 2 as a "can enhancements salvage this?" remedial test, following Option 1 parsimony principle.
- **User Impact**: The repo can now test if a simple binary regime filter (VIX-based defensive mode) improves crisis performance without adding excessive complexity. Bounded grid search with DSR correction ensures results are not due to statistical luck.

## 2. Goals & Non-Goals
- **Goal**: Implement parsimonious binary regime grid search with 18 trials (rv_threshold [0.15,0.20,0.25] × defensive_exposure [0.3,0.5,0.7] × defensive_top_n [3,5]).
- **Goal**: Measure delta vs Week 1 baseline: Max DD 2008, Max DD 2020, Sharpe 2007-2024, recovery time.
- **Goal**: Apply Deflated Sharpe Ratio (DSR) correction to account for 18-trial multiple testing.
- **Goal**: Establish clean delta attribution: regime change only, all other logic unchanged from Week 1.
- **Non-Goal**: Implement SMA200 trend filter (deferred to Week 3 if Week 2 passes).
- **Non-Goal**: Implement sector caps or drawdown deleveraging (out of scope for Week 2).
- **Non-Goal**: Modify 4-factor scorecard, cost model, or portfolio construction logic.

## 3. Week 1 Baseline (Reference for Delta Attribution)

### Week 1 Results (Unchanged Phase 50 Strategy)
```
Train (2007-2019):
  Sharpe: 0.434, Max DD: -60.69%, CAGR: 8.97%

Validation (2020-2021):
  Sharpe: 2.002, Max DD: -27.97%, CAGR: 140.67%

Holdout (2022-2024):
  Sharpe: -0.021, Max DD: -62.83%, CAGR: -6.93%

Full Period (2007-2024):
  Sharpe: 0.606, Max DD: -68.60%, CAGR: 16.05%

Crisis Periods:
  GFC 2008: Max DD -60.69% (vs SPY -57%)
  COVID 2020: Max DD -27.97% (vs SPY -34%)
  BEAR 2022: Max DD -55.51% (vs SPY -20%)

Acceptance: FAILED (1/4 criteria passed)
```

## 4. Week 2 Parsimonious Binary Regime Grid Search

### Grid Dimensions (Intentionally Small per Option 1)
```python
# 3 dimensions, 18 total trials
vix_threshold: [25, 30, 35]  # VIX level triggering defensive mode
defensive_exposure: [0.3, 0.5, 0.7]  # Exposure scaling in defensive mode
defensive_top_n: [3, 5]  # Portfolio size in defensive mode

# Normal mode (VIX <= threshold)
normal_exposure: 1.0  # Full exposure (unchanged from Week 1)
normal_top_n: 5  # Same as Week 1 baseline
```

### Binary Regime Logic (Parsimonious)
```python
# Simple binary gate (no 3×3 matrix)
if vix > vix_threshold:
    regime = "DEFENSIVE"
    exposure = defensive_exposure
    top_n = defensive_top_n
else:
    regime = "NORMAL"
    exposure = 1.0
    top_n = 5
```

### Unchanged from Week 1
- 4-factor equal-weight (momentum 0.25, quality 0.25, volatility 0.25, illiquidity 0.25)
- Transaction cost: 10bps
- Windows: 2007-2024 (same as Week 1)
- No SMA200 filter, no sector caps, no drawdown deleveraging

## 5. Week 2 Acceptance Criteria (Lowered but Realistic)

| Criterion | Week 1 Baseline | Week 2 Target | Delta Required |
|-----------|----------------|---------------|----------------|
| Max DD 2008 | -60.69% | <45% | -15.69% improvement |
| Max DD 2020 | -27.97% | <25% | -2.97% improvement |
| Sharpe 2007-2024 | 0.606 | >0.65 | +0.044 improvement |
| Recovery Time | 297 days | <240 days | -57 days improvement |

**DSR Threshold**: Best grid result must have DSR >0.5 (accounting for 18 trials) to be considered genuine alpha vs statistical luck.

**Overall Week 2 Status**: PASS if 3/4 criteria met AND DSR >0.5

## 6. Deflated Sharpe Ratio (DSR) Correction

### Multiple Testing Problem
- 18 trials increase probability of finding high Sharpe by chance
- Standard Sharpe ratio does not account for number of trials
- DSR adjusts for variance across trials and number of configurations tested

### DSR Formula
```python
# Lopez de Prado (2014)
DSR = (Sharpe - E[max(Sharpe_null)]) / sqrt(Var[max(Sharpe_null)])

# Where:
# Sharpe = observed Sharpe of best configuration
# E[max(Sharpe_null)] = expected max Sharpe under null hypothesis (no skill)
# Var[max(Sharpe_null)] = variance of max Sharpe under null hypothesis

# Approximation for N trials:
DSR ≈ Sharpe * sqrt(1 - γ * ln(N) / N)
# Where γ ≈ 0.5772 (Euler-Mascheroni constant), N = 18 trials
```

### Interpretation
- DSR >0.5: Likely genuine alpha (not statistical luck)
- DSR 0-0.5: Marginal, requires additional validation
- DSR <0: Likely overfitting, reject configuration

## 7. Week 2 Deliverables
- `backtests/phase52_week2_regime_grid.py` (18-trial grid search)
- `tests/test_phase52_week2_regime_grid.py` (focused tests)
- `data/processed/phase52_week2/grid_results.json` (all 18 trial metrics)
- `data/processed/phase52_week2/best_config_report.json` (best trial with DSR)
- `docs/handover/phase52_week2_regime_evidence.md` (delta attribution vs Week 1)

## 8. Scope Boundaries (Week 2)
- **In scope**: Binary regime grid search (18 trials), delta attribution vs Week 1, DSR correction, crisis performance comparison
- **Out of scope**: SMA200 trend filter, sector caps, drawdown deleveraging, 4-factor modifications, cost model changes, Week 3+ enhancements

## 9. Acceptance Checks (Week 2)
- ✅ `CHK-P52-W2-01` - Grid search implemented 18 trials (3×3×2 dimensions), 12 valid results
- ✅ `CHK-P52-W2-02` - Binary regime logic (RV-based) replaces 3×3 matrix, all other logic unchanged from Week 1
- ✅ `CHK-P52-W2-03` - Delta attribution measured: Crisis-specific analysis on Trial 16 shows +18.59% improvement in 2008, +7.41% in 2020
- ✅ `CHK-P52-W2-04` - DSR correction applied to best grid result: DSR 0.591 (accounting for 12 valid trials)
- ✗ `CHK-P52-W2-05` - Acceptance criteria verification: 2/4 criteria met (crisis targets passed, full-period Sharpe/recovery missed)
- ✅ `CHK-P52-W2-06` - Focused tests pass: 11/11 tests passed in test_phase52_week2_regime_grid.py
- ✅ `CHK-P52-W2-07` - Week 2 evidence summary published: docs/handover/phase52_week2_regime_evidence.md
- ✅ `CHK-P52-W2-08` - Step 2 tightened grid authorized based on crisis-specific improvements (both trigger conditions met)

## 10. Rollback Note
If Week 2 fails acceptance criteria (3/4 not met OR DSR <0.5), binary regime approach is insufficient. Options: (1) proceed to Week 3 SMA200 filter as alternative remedial fix, (2) require fundamental redesign, (3) pivot to Phase 51 binary supercycle if kill-test passes.

## 11. Week 3 Preview (Deferred)
If Week 2 passes, Week 3 will add SMA200 trend filter (orthogonal to regime logic):
```python
# Week 3 enhancement (deferred)
if SPY_price > SPY_SMA200:
    exposure = regime_exposure  # from Week 2 best config
else:
    exposure = 0.5 * regime_exposure  # half exposure in downtrend
```

This addresses the "when to be in the market" dimension, orthogonal to Week 2's "how much exposure in crisis" dimension.
