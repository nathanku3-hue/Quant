# Phase 35: Closure Report - Candidate/Reweight Branch

**Status**: CLOSED - BLOCKED
**Closure Date**: 2026-03-07
**Reason**: Invalid experiments, missing data, model misspecification

---

## Executive Summary

Phase 35 (candidate column improvement + momentum-heavy reweighting) is **closed and blocked** due to three critical issues that prevent meaningful experimentation:

1. **Invalid Experiments**: Candidate resolution failure made Wave 1 identical to baseline
2. **Missing Data**: 4 critical columns unavailable in `features.parquet`
3. **Model Misspecification**: Attribution decomposition produces catastrophic residuals

**Verdict**: Wave 3 (turnover-constrained) is not worth running. Phase 35 requires data engineering and model fixes before resuming.

---

## Blockers

### Blocker #1: Invalid Experiments (CRITICAL)

**Issue**: All experiments use identical resolved candidates due to missing columns.

**Evidence**:
- 4 columns missing from `features.parquet`: `mom_12m`, `quality_composite`, `realized_vol_21d`, `illiq_21d`
- Fallback resolution silently unified all experiments to: `resid_mom_60d`, `capital_cycle_score`, `yz_vol_20d`, `amihud_20d`
- Wave 1 vs Baseline: **NOT testing different candidates** (intended to test, but fallback made them identical)
- Wave 2 vs Wave 1: **Only testing reweighting** (not "reweight on top of Wave 1 improvements")

**Impact**:
- Wave 1 calibration results are invalid (not testing what we think)
- Ablation matrix is invalid (assumes Wave 1 changed candidates)
- Cannot make causal inferences about candidate column improvements

**Resolution Required**:
- Add missing columns to `features.parquet` via data engineering
- Re-run Wave 1 with correct candidate availability
- Add `_source` columns to factor score artifacts for verification
- Add fallback resolution logging (warn when fallback occurs)

### Blocker #2: Model Misspecification (CRITICAL)

**Issue**: Attribution decomposition produces catastrophic residuals.

**Evidence**:
- Wave 1: R² = -17.85, residuals up to ±200% (vs returns ±10%)
- Wave 2: R² = -0.47, residuals up to ±78% (improved but still negative)
- Factor contributions wildly unstable (18.85× worse than mean baseline in Wave 1)
- Accounting identity holds (error = 0.0), so calculation is correct

**Root Cause**:
- Factor regression instability (multicollinearity, outliers, ill-conditioning)
- Cross-sectional regressions produce unstable betas
- Factor exposures amplify small estimation errors into massive swings

**Impact**:
- Cannot trust attribution metrics for decision-making
- R² gate (> 0.5) is unachievable with current model
- Factor contributions are noise, not signal

**Resolution Required**:
- Investigate factor correlation matrix (diagnose multicollinearity)
- Add regularization to factor regression (ridge, lasso)
- Consider alternative attribution methods (Brinson-Fachler, holdings-based)
- Validate on holdout period (current R² may be in-sample overfitting)

### Blocker #3: Turnover Crisis (HIGH)

**Issue**: 90-100% daily turnover across all configurations.

**Evidence**:
- Baseline: 100.58% one-way (50.29% two-way)
- Wave 1: 94.17% one-way (47.09% two-way)
- Wave 2: 96.03% one-way (48.02% two-way)
- P95 turnover: 188-198% (extreme instability)

**Impact**:
- Transaction costs would destroy any alpha
- Strategy is operationally unimplementable
- Gate ambiguity: "< 50%" unclear (one-way or two-way?)

**Resolution Required**:
- Clarify turnover gate definition (recommend: 50% two-way = 100% one-way)
- Add turnover constraints to weight generation
- Implement signal smoothing or leaky integrators
- Test if turnover reduction degrades IC

---

## Wave Results Summary

### Wave 1: Candidate Column Improvement (INVALID)

**Configuration**:
- Candidates: resid_mom_60d, capital_cycle_score, yz_vol_20d, amihud_20d (fallback-resolved, identical to baseline)
- Weights: 0.25 / 0.25 / 0.25 / 0.25

**Results**:
- Mean IC: -0.001830 (baseline: -0.002, delta: +0.00017)
- R²: -17.8459 (baseline: -0.268, delta: -17.578)
- Turnover: 94.17% one-way (baseline: 100.58%, delta: -6.41pp)
- Coverage: 48.59% (gate: ≥50%, **FAIL**)

**Gate Status**: ❌ FAIL (IC improved slightly, but R² catastrophic, coverage below gate, turnover excessive)

**Validity**: ❌ INVALID (not testing intended candidates due to fallback resolution)

### Wave 2: Momentum-Heavy Reweighting (PARTIALLY VALID)

**Configuration**:
- Candidates: resid_mom_60d, capital_cycle_score, yz_vol_20d, amihud_20d (same as Wave 1)
- Weights: 0.70 / 0.10 / 0.10 / 0.10 (momentum-heavy)

**Results**:
- Mean IC: -0.001008 (baseline: -0.002, delta: +0.000992)
- R²: -0.4702 (baseline: -0.268, delta: -0.202)
- Turnover: 96.03% one-way (baseline: 100.58%, delta: -4.55pp)
- Coverage: 44.48% (gate: ≥50%, **FAIL**)

**Gate Status**: ❌ FAIL (IC improved 49%, but R² still negative, coverage below gate, turnover excessive)

**Validity**: ⚠️ PARTIALLY VALID (tests reweighting, but not on top of Wave 1 improvements as intended)

### Wave 3: Not Executed

**Reason**: Blockers #1 and #2 make Wave 3 (turnover-constrained) not worth running.

---

## Diagnostic Findings

### Turnover Definition

**Finding**: Codebase uses **one-way turnover** (`sum(abs(dw))`).

**Interpretation**:
- 96% one-way = 48% two-way
- If gate is 50% two-way: Wave 2 **PASSES** (48.02% < 50%)
- If gate is 50% one-way: Wave 2 **FAILS** (96.03% > 50%)

**Recommendation**: Clarify gate as "50% two-way = 100% one-way" for consistency with baseline (100.58%).

### Candidate Resolution

**Finding**: Fallback resolution silently unified all experiments.

**Missing Columns**:
1. `mom_12m` (momentum)
2. `quality_composite` (quality)
3. `realized_vol_21d` (volatility)
4. `illiq_21d` (illiquidity)

**Impact**: Wave 1 and baseline use identical candidates, making comparison invalid.

### R² Calculation

**Finding**: R² calculation is mathematically correct.

**Validation**:
- Wave 1: Reported -17.85, manual calculation -17.85 ✅
- Wave 2: Reported -0.47, manual calculation -0.47 ✅
- Accounting identity holds (error = 0.0) ✅

**Interpretation**: Very negative R² indicates model misspecification (factor contributions don't explain returns), not calculation bug.

---

## Lessons Learned

### What Worked ✅

1. **Pipeline Infrastructure**: Preset-based factor engineering framework is sound
2. **Corrected Bugs**: Fixed `--factor-scores` argument and `composite_score` column generation
3. **Diagnostic Rigor**: Comprehensive diagnostics identified root causes
4. **Walk-Forward Protocol**: Calibration/validation/holdout framework is well-designed

### What Failed ❌

1. **Data Availability**: Missing baseline columns prevented candidate experiments
2. **Attribution Model**: Factor regression produces unstable contributions
3. **Turnover**: No constraints or smoothing, resulting in 90-100% daily churn
4. **Validation**: No `_source` columns to verify candidate resolution

### What to Improve 🔧

1. **Data Engineering**: Add missing columns to `features.parquet` before Phase 35 v2
2. **Model Stability**: Regularize factor regression, consider alternative attribution methods
3. **Turnover Constraints**: Add explicit turnover penalties or signal smoothing
4. **Instrumentation**: Preserve `_source` columns, add fallback warnings, log resolved candidates

---

## Pivot: Rule of 100 Integration

**Phase 35 candidate/reweight branch is closed.** Future work will pivot to **Rule of 100 integration** as a separate governed workstream.

**Rule of 100** (currently in `derivative_macro_backtest.py`):
- Separate script path, not integrated with Phase 35 scorecard/alpha pipeline
- Requires explicit integration design and Evidence Gate contract
- New brief required: "Rule of 100 Integration" with walk-forward evaluation

**Not a direct continuation** of Phase 35 wave sequence. Requires new governance and design.

---

## Artifacts

### Generated Files

**Wave 1 Calibration**:
- `data/processed/phase35_w1_calibration_factor_scores.parquet`
- `data/processed/phase35_w1_calibration_target_weights_v2.parquet`
- `data/processed/phase35_w1_calibration_v2/phase34_*.csv`
- `data/processed/phase35_w1_calibration_v2/phase34_summary.json`

**Wave 2 Calibration**:
- `data/processed/phase35_w2_calibration_factor_scores.parquet`
- `data/processed/phase35_w2_calibration_target_weights.parquet`
- `data/processed/phase35_w2_calibration/phase34_*.csv`
- `data/processed/phase35_w2_calibration/phase34_summary.json`

**Documentation**:
- `docs/phase_brief/phase35-brief.md` (approved specification)
- `docs/PHASE35_CLOSURE.md` (this document)
- `docs/saw_reports/saw_phase35_round1.md` (mandatory SAW report)

### Code Changes

**Commits**:
1. `f4fe341` - Phase 35 Wave 1 infrastructure (preset-based factor engineering)
2. `ccc6d08` - Pipeline fixes (make `--factor-scores` functional)

**Modified Files**:
- `strategies/factor_specs.py` (Wave 1 & 2 presets)
- `strategies/company_scorecard.py` (preset loader)
- `scripts/generate_phase34_factor_scores.py` (--preset, --output, composite_score)
- `scripts/generate_phase34_weights.py` (--factor-scores merge logic)

---

## Recommendations

### Immediate Actions

1. ✅ **Close Phase 35 candidate/reweight branch** (this document)
2. ✅ **Create mandatory SAW report** with BLOCK verdict
3. ✅ **Commit diagnostic findings** and closure documentation
4. ✅ **Update README** as "Phase 35 closed and pivoted"

### Before Phase 35 v2

**Data Engineering** (2-4 weeks):
1. Add missing columns to `features.parquet`: `mom_12m`, `quality_composite`, `realized_vol_21d`, `illiq_21d`
2. Validate column availability across full date range
3. Add data quality checks (missingness, outliers, staleness)

**Model Fixes** (2-4 weeks):
1. Diagnose factor multicollinearity (correlation matrix, VIF scores)
2. Add regularization to factor regression (ridge, lasso, elastic net)
3. Test alternative attribution methods (Brinson-Fachler, holdings-based)
4. Validate on holdout period (2024 Q2-Q4)

**Turnover Solution** (1-2 weeks):
1. Add turnover constraints to weight generation
2. Implement signal smoothing (leaky integrators, exponential moving average)
3. Test IC/turnover trade-off (does smoothing degrade predictive power?)

### Strategic Pivot

**Rule of 100 Integration** (new workstream):
1. Create new brief: "Rule of 100 Integration"
2. Design integration with scorecard/alpha pipeline
3. Define Evidence Gate contract (walk-forward, ablation, leakage controls)
4. Estimate: 4-6 weeks for design + implementation + validation

---

## Sign-Off

**Phase 35 (candidate/reweight branch) is formally closed and blocked.**

**Closure Reason**: Invalid experiments, missing data, model misspecification

**Next Steps**: Data engineering + model fixes before Phase 35 v2, or pivot to Rule of 100 integration

**Approved By**: _Pending_
**Closure Date**: 2026-03-07

---

**Document Version**: 1.0
**Last Updated**: 2026-03-07
