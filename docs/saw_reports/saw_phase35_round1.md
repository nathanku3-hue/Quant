# SAW Report: Phase 35 Round 1 - Candidate/Reweight Branch

**Date**: 2026-03-07
**Phase**: Phase 35 (Targeted Feature Engineering)
**Scope**: Wave 1 (Candidate Column Improvement) + Wave 2 (Momentum-Heavy Reweighting)
**Verdict**: 🚫 **BLOCK** - Invalid experiments, missing data, model misspecification

---

## Executive Summary

Phase 35 candidate/reweight branch is **blocked and closed** due to three critical issues that prevent meaningful experimentation:

1. **Invalid Experiments**: Candidate resolution failure made Wave 1 identical to baseline (4 columns missing from features.parquet)
2. **Model Misspecification**: Attribution decomposition produces catastrophic residuals (R² = -17.85 in Wave 1, -0.47 in Wave 2)
3. **Turnover Crisis**: 90-100% daily turnover across all configurations (operationally unimplementable)

**Recommendation**: Abort current wave path. Requires data engineering (add missing columns) and model fixes (regularization, alternative attribution methods) before Phase 35 v2.

---

## Strengths ✅

### 1. Pipeline Infrastructure
- **Preset-based factor engineering framework is sound**: Clean separation between factor definitions (FactorSpec) and execution (CompanyScorecard)
- **Wave-specific artifact generation works**: `--preset` and `--output` arguments enable reproducible experiments
- **Causality fixes successful**: Pipeline now correctly uses `--factor-scores` argument (merge logic implemented)

### 2. Diagnostic Rigor
- **C root cause analysis**: 3 parallel diagnostic agents identified turnover definition, candidate resolution failure, and R² calculation validity
- **Fallback resolution bug discovered**: Missing columns (mom_12m, quality_composite, realized_vol_21d, illiq_21d) caused silent unification of all experiments
- **Metric integrity validated**: R² calculation mathematically correct, accounting identity holds (error < 1e-14)

### 3. Walk-Forward Protocol Design
- **Calibration/validation/holdout framework well-designed**: 18-month calibration, 9-month validation, 9-month holdout (untouched)
- **Interim gates defined**: IC improvement, coverage ≥50%, turnover <50%, resolved source columns documented
- **Ablation matrix structured**: Tracks candidates, weights, regime norm, window, IC, R², coverage, turnover per experiment

### 4. Corrected Pipeline Bugs
- **Fixed `--factor-scores` not being used**: generate_phase34_weights.py now merges factor scores with technical features
- **Fixed missing composite_score column**: generate_phase34_factor_scores.py renames 'score' → 'composite_score' for AlphaEngine compatibility
- **Causality now valid**: Different factor scores produce different weights → different attribution

---

## Areas for Improvement 🔧

### 1. Data Availability (CRITICAL)
**Issue**: 4 baseline columns missing from features.parquet prevent candidate experiments

**Missing Columns**:
- `mom_12m` (momentum)
- `quality_composite` (quality)
- `realized_vol_21d` (volatility)
- `illiq_21d` (illiquidity)

**Impact**: Fallback resolution silently unified all experiments to same candidates (resid_mom_60d, capital_cycle_score, yz_vol_20d, amihud_20d), making Wave 1 vs Baseline comparison invalid.

**Recommendation**:
- Add missing columns to features.parquet via data engineering (2-4 weeks)
- Validate column availability across full date range (2022-2024)
- Add data quality checks (missingness, outliers, staleness)

### 2. Attribution Model Stability (CRITICAL)
**Issue**: Factor regression produces catastrophic residuals

**Evidence**:
- Wave 1: R² = -17.85, residuals up to ±200% (vs returns ±10%)
- Wave 2: R² = -0.47, residuals up to ±78% (improved but still negative)
- Factor contributions wildly unstable (18.85× worse than mean baseline in Wave 1)

**Root Cause**: Factor regression instability (multicollinearity, outliers, ill-conditioning)

**Recommendation**:
- Diagnose factor multicollinearity (correlation matrix, VIF scores)
- Add regularization to factor regression (ridge, lasso, elastic net)
- Test alternative attribution methods (Brinson-Fachler, holdings-based)
- Validate on holdout period (2024 Q2-Q4)

### 3. Turnover Constraints (HIGH)
**Issue**: 90-100% daily turnover across all configurations

**Evidence**:
- Baseline: 100.58% one-way (50.29% two-way)
- Wave 1: 94.17% one-way (47.09% two-way)
- Wave 2: 96.03% one-way (48.02% two-way)
- P95 turnover: 188-198% (extreme instability)

**Impact**: Transaction costs would destroy any alpha, strategy operationally unimplementable

**Recommendation**:
- Clarify turnover gate definition (recommend: 50% two-way = 100% one-way)
- Add turnover constraints to weight generation
- Implement signal smoothing (leaky integrators, exponential moving average)
- Test IC/turnover trade-off (does smoothing degrade predictive power?)

### 4. Instrumentation (MEDIUM)
**Issue**: No `_source` columns to verify candidate resolution

**Impact**: Cannot verify which candidate column was actually used per factor (fallback resolution is silent)

**Recommendation**:
- Preserve `_source` columns in factor score artifacts (e.g., momentum_source, quality_source)
- Add fallback resolution logging (warn when fallback occurs)
- Log resolved candidates in experiment metadata
- Add coverage diagnostics (% rows with score_valid=True by factor)

---

## Warnings ⚠️

### 1. Experiments Are Invalid (BLOCKER)
**All Wave 1 and Wave 2 experiments use identical resolved candidates due to missing columns.**

- Wave 1 intended to test: resid_mom_60d → (resid_mom_60d, rel_strength_60d, rsi_14d)
- Wave 1 actually tested: resid_mom_60d → resid_mom_60d (no change, fallback)
- Wave 2 intended to test: reweighting on top of Wave 1 improvements
- Wave 2 actually tested: reweighting on baseline candidates (not Wave 1)

**Ablation matrix is invalid. Cannot make causal inferences about candidate column improvements.**

### 2. Model Misspecification (BLOCKER)
**Attribution R² is catastrophically negative (-17.85 in Wave 1, -0.47 in Wave 2).**

- Factor contributions don't explain returns (residuals 18.85× larger than signal)
- R² gate (> 0.5) is unachievable with current model
- Factor contributions are noise, not signal

**Cannot trust attribution metrics for decision-making until model is fixed.**

### 3. Turnover Crisis (HIGH)
**90-100% daily turnover makes strategy operationally unimplementable.**

- Even if IC/R² targets were met, transaction costs would destroy alpha
- Gate ambiguity: "< 50%" unclear (one-way or two-way?)
- No turnover constraints or signal smoothing in current pipeline

**Strategy requires turnover solution before production deployment.**

### 4. Coverage Below Gate (MEDIUM)
**Wave 1: 48.59%, Wave 2: 44.48% (gate: ≥50%)**

- Losing half the universe due to missing factor values
- Coverage decreasing from baseline (~50%) to Wave 2 (44.48%)
- May indicate data quality issues or overly strict score_valid logic

**Coverage gate failure indicates universe shrinkage, reducing diversification.**

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

## Recommendations

### Immediate Actions (This Week)

1. ✅ **Close Phase 35 candidate/reweight branch** (PHASE35_CLOSURE.md created)
2. ✅ **Create mandatory SAW report** (this document)
3. ⏳ **Commit diagnostic findings** and closure documentation
4. ⏳ **Update README** as "Phase 35 closed and pivoted"

### Before Phase 35 v2 (2-4 Weeks Per Workstream)

**Data Engineering** (2-4 weeks):
1. Add missing columns to features.parquet: mom_12m, quality_composite, realized_vol_21d, illiq_21d
2. Validate column availability across full date range (2022-2024)
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

### Strategic Pivot (4-6 Weeks)

**Rule of 100 Integration** (new workstream):
1. Create new brief: "Rule of 100 Integration"
2. Design integration with scorecard/alpha pipeline
3. Define Evidence Gate contract (walk-forward, ablation, leakage controls)
4. Estimate: 4-6 weeks for design + implementation + validation

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

1. **Data Engineering**: Add missing columns to features.parquet before Phase 35 v2
2. **Model Stability**: Regularize factor regression, consider alternative attribution methods
3. **Turnover Constraints**: Add explicit turnover penalties or signal smoothing
4. **Instrumentation**: Preserve `_source` columns, add fallback warnings, log resolved candidates

---

## Verdict

**🚫 BLOCK - Phase 35 candidate/reweight branch is closed and blocked.**

**Closure Reason**: Invalid experiments, missing data, model misspecification

**Next Steps**: Data engineering + model fixes before Phase 35 v2, or pivot to Rule of 100 integration

**Approved By**: _Pending_
**SAW Date**: 2026-03-07

---

**Document Version**: 1.0
**Last Updated**: 2026-03-07
