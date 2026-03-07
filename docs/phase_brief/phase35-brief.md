# Phase 35: Targeted Feature Engineering

**Status**: Planning - Awaiting Approval
**Created**: 2026-03-06
**Phase 34 Status**: Closed with Conditional Approval (Engineering Complete, Performance Deferred)

---

## Executive Summary

Phase 34 delivered a production-ready attribution pipeline but revealed that current factor definitions have weak predictive power. Phase 35 will improve factor definitions through targeted feature engineering using strict walk-forward evaluation, clean preset architecture, and comprehensive coverage/turnover gates.

**Current Performance** (Phase 34 baseline):
- Mean IC: -0.002 (target: > 0.02)
- Contribution R²: -0.268 (target: > 0.5)
- Regime hit-rates: GREEN 25%, AMBER 0%, RED 50% (target: > 70% each)

**Root Cause**: Factor quality problem, not pipeline bug. Current 4-factor baseline has weak predictive power with only momentum showing positive IC (0.067).

**Phase 35 Objective**: Improve factor definitions to meet quantitative thresholds through controlled iterations: improve candidate columns → reweight factors → enhance regime normalization.

---

## Context & Strategic Value

### Phase 34 Conditional Approval

Phase 34 closed with conditional approval:
- **Engineering Gate**: ✅ APPROVED (pipeline production-ready, accounting identity verified)
- **Performance Gate**: ⚠️ DEFERRED TO PHASE 35 (quantitative targets not met)

Phase 34 provides the measurement infrastructure. Phase 35 will use this infrastructure to validate factor improvements.

### Strategic Value

Factor improvements provide decision leverage for:
- **Position Sizing**: Better IC → more confident position sizes
- **Risk Budget**: Better R² → more efficient risk allocation
- **Rebalancing**: Better regime hit-rates → adaptive rebalancing decisions
- **Downstream Phases**: Phase 36+ depend on Phase 35 factor quality

### Diagnostic Findings

**Critical Issues Identified**:

1. **High Missingness** (46% for momentum/volatility/illiquidity, 33% for quality)
   - Root cause: Wrong candidate columns, fallback resolution not working
   - Impact: Losing half the tradable universe

2. **Regime Effectiveness Failure**
   - AMBER: 0% hit-rate, all ICs are NaN (completely broken)
   - GREEN: 25% hit-rate (terrible)
   - RED: 50% hit-rate (coin flip)

3. **Regime-Dependent Sign Flips** (critical bug)
   - Volatility: Correct in GREEN (IC = -0.0053) but flips POSITIVE in RED (IC = +0.0081)
   - Illiquidity: Correct in GREEN (IC = -0.0061) but flips POSITIVE in RED (IC = +0.0182)
   - Should penalize volatility/illiquidity MORE in crisis, not less

4. **Factor Instability**
   - Near-zero autocorrelation (all factors ~0)
   - ~50% sign consistency (coin flip behavior)
   - High rolling volatility indicating regime-dependent reversals

---

## Regime Taxonomy Resolution

**Decision**: Use 3-state regime model consistently across Phase 35.

**Background**: Phase 34 brief mentioned 4 regimes (GREEN/YELLOW/AMBER/RED) but production `RegimeManager` uses 3 states (GREEN/AMBER/RED). This mismatch made "regime hit-rate > 70%" ambiguous.

**Phase 35 Standard**:
- **GREEN**: Normal market conditions (low volatility, positive momentum)
- **AMBER**: Transitional/uncertain conditions (moderate volatility)
- **RED**: Crisis conditions (high volatility, negative momentum)

## Regime Hit-Rate Gate Specification

### Definition

**Regime hit-rate** = proportion of **factor-date observations** where factor IC has the correct sign for that regime.

**Note**: This counts individual (factor, date, regime) tuples, not unique dates. A single date with 4 factors contributes 4 observations.

### Truth Source Formula

For each regime (GREEN, AMBER, RED):

```
hit_rate = (count of factor-date observations where IC sign matches expected) / (total factor-date observations in regime with non-NaN IC)

Expected signs by factor:
- momentum_normalized: positive (IC > 0)
- quality_normalized: positive (IC > 0)
- volatility_normalized: negative (IC < 0)
- illiquidity_normalized: negative (IC < 0)
```

### In-Scope Windows

- **Calibration**: 2022-01-01 to 2023-06-30
- **Validation**: 2023-07-01 to 2024-03-31
- **Holdout**: 2024-04-01 to 2024-12-31

Only dates within these windows are counted. Dates outside evaluation windows are excluded.

### Computation

From `phase34_factor_ic.csv` (factor-date level IC observations):

```python
import pandas as pd

# Load factor-date level IC data
factor_ic = pd.read_csv('data/processed/phase34_factor_ic.csv')
factor_ic['date'] = pd.to_datetime(factor_ic['date'])

# Load regime history
regime_history = pd.read_csv('data/processed/regime_history.csv')
regime_history['date'] = pd.to_datetime(regime_history['date'])
regime_history = regime_history.set_index('date')

# Merge regime labels
factor_ic = factor_ic.merge(
    regime_history[['governor_state']],
    left_on='date',
    right_index=True,
    how='left'
)

# Expected signs
expected_signs = {
    'momentum_normalized': 'positive',
    'quality_normalized': 'positive',
    'volatility_normalized': 'negative',
    'illiquidity_normalized': 'negative',
}

# Compute hit rate per regime (factor-date level)
for regime in ['GREEN', 'AMBER', 'RED']:
    regime_data = factor_ic[factor_ic['governor_state'] == regime]

    hits = 0
    total = 0
    for _, row in regime_data.iterrows():
        factor = row['factor']
        ic = row['ic']

        if pd.isna(ic):
            continue  # Skip NaN ICs

        expected = expected_signs.get(factor)
        if expected == 'positive' and ic > 0:
            hits += 1
        elif expected == 'negative' and ic < 0:
            hits += 1

        total += 1

    hit_rate = hits / total if total > 0 else 0.0
    print(f'{regime} hit-rate: {hit_rate:.1%} ({hits}/{total} factor-date observations)')
```

### Gate

**Target**: Hit-rate > 70% for **each** of GREEN, AMBER, RED regimes.

**Failure Mode**: If any single regime has hit-rate ≤ 70%, the gate fails (even if aggregate is > 70%).

---

## Walk-Forward Evaluation Protocol

**No in-sample optimization**. All experiments follow strict walk-forward discipline:

### Window Definitions

| Window | Start | End | Duration | Purpose |
|--------|-------|-----|----------|---------|
| **Calibration** | 2022-01-01 | 2023-06-30 | 18 months | Factor candidate selection |
| **Validation** | 2023-07-01 | 2024-03-31 | 9 months | Out-of-sample confirmation |
| **Holdout** | 2024-04-01 | 2024-12-31 | 9 months | Final success criteria (untouched) |

### Evaluation Rules

1. **Calibration Window**: Select factor candidates, tune weights (if needed)
2. **Validation Window**: Confirm improvements out-of-sample, no re-optimization
3. **Holdout Window**: Final gate, completely untouched until all waves complete
4. **Wave Promotion**: Only proceed to next wave if validation confirms improvement
5. **Final Success**: All hard targets must be met on holdout window only

---

## Experiment Design: Clean Preset Architecture

### Preset Naming Convention

All Phase 35 experiments use named presets registered in `strategies/factor_specs.py`:

- `PHASE35_W1_CANDIDATES`: Wave 1 - Pure candidate column improvement
- `PHASE35_W2_MOMENTUM_HEAVY`: Wave 2 - Momentum-heavy reweighting
- `PHASE35_W3_REGIME_PENALTY`: Wave 3 - Enhanced regime normalization

### Preset Loader Integration

Presets wired through `CompanyScorecard.from_factor_preset()` for reproducibility:

```python
# In strategies/company_scorecard.py
PHASE35_PRESETS = {
    "PHASE35_W1_CANDIDATES": build_phase35_wave1_candidate_specs(),
    "PHASE35_W2_MOMENTUM_HEAVY": build_phase35_wave2_momentum_heavy_specs(),
    "PHASE35_W3_REGIME_PENALTY": build_phase35_wave3_regime_penalty_specs(),
}

def from_factor_preset(preset_name: str, ...) -> CompanyScorecard:
    if preset_name in PHASE35_PRESETS:
        specs = PHASE35_PRESETS[preset_name]
    # ... (existing Phase 19.5 and DEFAULT_DAY4 handling)
```

### Wave Isolation Principle

**Wave 1**: Only swap candidate columns (no leaky integrators, no rank norm, no regime penalties)
**Wave 2**: Only reweight factors (use Wave 1 candidates, no normalization changes)
**Wave 3**: Only enhance regime normalization (use best Wave 2 config)

This ensures ablation matrix isolates what actually caused improvements.

---

## Wave 1: Improve Candidate Columns

### Objective

Replace weak candidate columns with stronger alternatives based on diagnostic analysis. This is the **main lever** for Phase 35.

### Current vs. Proposed Candidates

| Factor | Phase 34 Candidates | Phase 35 Wave 1 Candidates | Rationale |
|--------|---------------------|---------------------------|-----------|
| **momentum** | `resid_mom_60d`, `mom_12m` | `resid_mom_60d`, `rel_strength_60d`, `rsi_14d` | Keep `resid_mom_60d` first, add `rel_strength_60d` and `rsi_14d` as pure momentum signals (no aggregate signals) |
| **quality** | `quality_composite`, `capital_cycle_score`, `z_moat` | `capital_cycle_score`, `z_inventory_quality_proxy`, `z_moat` | Replace `quality_composite` with `z_inventory_quality_proxy` (better fundamental quality) |
| **volatility** | `realized_vol_21d`, `yz_vol_20d` | `yz_vol_20d`, `atr_14d` | Replace `realized_vol_21d` with `atr_14d` (better volatility measure) |
| **illiquidity** | `illiq_21d`, `amihud_20d` | `amihud_20d`, `z_flow_proxy` | Add `z_flow_proxy` (captures flow dynamics) |

### Implementation

**File**: `strategies/factor_specs.py`

```python
def build_phase35_wave1_candidate_specs() -> list[FactorSpec]:
    """
    Phase 35 Wave 1: Pure candidate column improvement.

    NO aggregate signals (composite_score removed for clean ablation).
    NO other changes: equal weights (0.25), zscore norm, no leaky integrators.
    """
    return [
        FactorSpec(
            name="momentum",
            candidate_columns=("resid_mom_60d", "rel_strength_60d", "rsi_14d"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="quality",
            candidate_columns=("capital_cycle_score", "z_inventory_quality_proxy", "z_moat"),
            direction="positive",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="volatility",
            candidate_columns=("yz_vol_20d", "atr_14d"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
        FactorSpec(
            name="illiquidity",
            candidate_columns=("amihud_20d", "z_flow_proxy"),
            direction="negative",
            weight=0.25,
            normalization="zscore",
        ),
    ]
```

### Expected Improvements

| Metric | Phase 34 Baseline | Wave 1 Target | Improvement |
|--------|------------------|---------------|-------------|
| Mean IC | -0.002 | 0.02-0.04 | 10-20x |
| Contribution R² | -0.268 | 0.10-0.20 | Positive explanatory power |
| Coverage | ~50% | ≥50% | Maintain universe |
| Momentum IC | 0.067 | 0.08-0.12 | 1.2-1.8x (conservative without composite_score) |
| Quality IC | -0.035 | +0.03-0.06 | Sign flip + 0.9-1.7x |
| Volatility IC | -0.062 | -0.08 to -0.12 | 1.3-1.9x stronger |
| Illiquidity IC | -0.074 | -0.10 to -0.15 | 1.4-2.0x stronger |

---

## Wave 2: Reweight Factors

### Objective

Test if reweighting alone improves performance. Treat as **baseline comparison**, not victory condition.

### Rationale

Momentum is the only positive factor (IC = 0.067). Overweighting momentum may improve aggregate IC even if individual factors remain weak. However, this doesn't fix the underlying factor quality problem.

### Implementation

**File**: `strategies/factor_specs.py`

```python
def build_phase35_wave2_momentum_heavy_specs() -> list[FactorSpec]:
    """
    Phase 35 Wave 2: Momentum-heavy reweighting (70/10/10/10).

    Uses Wave 1 candidate columns.
    """
    base = build_phase35_wave1_candidate_specs()
    return [
        replace(base[0], weight=0.70),  # momentum
        replace(base[1], weight=0.10),  # quality
        replace(base[2], weight=0.10),  # volatility
        replace(base[3], weight=0.10),  # illiquidity
    ]
```

### Expected Improvements

| Metric | Wave 1 | Wave 2 Target | Improvement |
|--------|--------|---------------|-------------|
| Mean IC | 0.02-0.04 | 0.04-0.06 | 2x (if momentum dominates) |
| Contribution R² | 0.10-0.20 | 0.20-0.35 | Moderate |

**Note**: If Wave 2 meets all targets, great. But if not, it confirms that fixing factor definitions (Wave 1) is more important than reweighting.

---

## Wave 3: Enhanced Regime Normalization

### Objective

Fix regime-dependent sign flips where volatility/illiquidity become POSITIVE in RED regime (should be MORE negative).

### Root Cause

Current `regime_adaptive_norm()` applies rank percentile normalization in AMBER/RED but doesn't scale by factor direction. High volatility gets high rank (positive) instead of being penalized more in crisis.

### Solution

Add `factor_direction` parameter to `regime_adaptive_norm()` and apply crisis penalty scaling:
- GREEN: zscore (unchanged)
- AMBER: rank percentile × 1.5 for negative factors
- RED: rank percentile × 2.0 for negative factors

### Implementation

**File 1**: `strategies/factor_specs.py`

Update `regime_adaptive_norm()` signature:

```python
def regime_adaptive_norm(
    values: pd.Series,
    date_index: pd.Series,
    regime_by_date: pd.Series | None,
    factor_direction: str = "positive",  # NEW parameter
) -> pd.Series:
    """
    Regime-adaptive normalization with crisis penalty scaling.

    Fixes sign flip bug where volatility/illiquidity became positive in RED.
    """
    # ... (GREEN: standard zscore)

    # AMBER/RED: rank percentile with crisis penalty
    if bool(stress_mask.any()):
        rank_pct = vs.groupby(ds).rank(pct=True, method="average")
        normalized = (rank_pct - 0.5) * 2.0

        # Apply crisis penalty for negative factors
        if factor_direction == "negative":
            amber_mask = rs.eq("AMBER")
            red_mask = rs.eq("RED")
            normalized.loc[amber_mask] *= 1.5
            normalized.loc[red_mask] *= 2.0

        out.loc[stress_mask] = normalized

    return out
```

**File 2**: `strategies/company_scorecard.py`

Update `_normalize()` to pass `factor_direction`:

```python
def _normalize(self, values, date_index, normalization, factor_direction):
    if normalization == "regime_adaptive":
        return regime_adaptive_norm(
            values, date_index, self.regime_by_date,
            factor_direction=factor_direction,  # Pass direction
        )
    # ... (other normalizations)
```

Update caller in `run()`:

```python
normalized = self._normalize(
    raw_values, work["date"], spec.normalization,
    factor_direction=spec.direction,  # Pass from spec
)
```

**File 3**: `tests/test_factor_specs.py`

Add test for negative factors staying negative:

```python
def test_regime_adaptive_norm_negative_factors_stress_penalty():
    """Test that negative factors remain negative and amplified in stress."""
    # ... (test implementation)
    assert high_vol_red < high_vol_amber, "RED should be more negative than AMBER"
    assert high_vol_red < -0.8, "High volatility in RED should be very negative"
```

### Expected Improvements

| Metric | Wave 2 | Wave 3 Target | Improvement |
|--------|--------|---------------|-------------|
| Mean IC | 0.04-0.06 | 0.08-0.12 | 2x (sign flips fixed) |
| Contribution R² | 0.20-0.35 | 0.50-0.70 | Meets target |
| Regime hit-rate | 50%/40%/60% | 70%/70%/70% | Meets target |

---

## Success Criteria

### Interim Wave Gates (Directional Improvement)

Must pass to proceed to next wave:

- [ ] Mean IC improvement vs baseline (calibration window)
- [ ] Coverage ≥ 50% (no universe shrinkage)
- [ ] IC consistency improvement
- [ ] Turnover < 50% daily (implementable)
- [ ] Resolved source columns documented
- [ ] Validation window confirms improvement (no re-optimization)

### Final Phase Gate (Hard Targets on Holdout Window)

All must be met:

- [ ] Mean IC > 0.02
- [ ] Contribution R² > 0.5
- [ ] Regime hit-rate > 70% for each of GREEN, AMBER, RED
- [ ] IC consistency > 0.3
- [ ] Accounting identity preserved (error < 1e-8)
- [ ] All 17 tests pass (regression protection)
- [ ] Coverage ≥ 50%
- [ ] Turnover < 50% daily

---

## Coverage & Source Column Gates

### Rationale

Phase 34 diagnostic revealed 46% missingness. Must ensure factor improvements don't shrink tradable universe.

### Coverage Metrics

Every experiment must report:

1. **Coverage**: `% rows with score_valid=True`
2. **Resolved Sources**: Which candidate column was actually used per factor
3. **Missingness by Factor**: `% null values per factor`

### Gates

- Coverage must not decrease vs baseline (≥50%)
- If coverage < 50%, investigate fallback resolution
- Document which candidate columns are actually being used

### Implementation

`CompanyScorecard` already emits `score_valid` and `{factor}_source` columns. Phase 35 experiments will track these in ablation matrix.

---

## End-to-End Portfolio Metrics Pipeline

### Critical Requirement

Wave experiments must generate **wave-specific weights** and **wave-specific attribution reports** to measure portfolio-level metrics (R², turnover, regime hit-rate).

### Pipeline Flow

For each wave/window combination:

1. **Generate Factor Scores** (wave-specific preset)
   ```bash
   python scripts/generate_phase34_factor_scores.py \
     --preset PHASE35_W1_CANDIDATES \
     --start-date 2022-01-01 \
     --end-date 2023-06-30 \
     --output data/processed/phase35_w1_calibration_factor_scores.parquet
   ```

2. **Generate Target Weights** (wave-specific factor scores)
   ```bash
   python scripts/generate_phase34_weights.py \
     --factor-scores data/processed/phase35_w1_calibration_factor_scores.parquet \
     --start-date 2022-01-01 \
     --end-date 2023-06-30 \
     --output data/processed/phase35_w1_calibration_target_weights.parquet
   ```

3. **Generate Attribution Report** (wave-specific weights)
   ```bash
   python scripts/attribution_report.py \
     --factor-scores-path data/processed/phase35_w1_calibration_factor_scores.parquet \
     --target-weights-path data/processed/phase35_w1_calibration_target_weights.parquet \
     --start-date 2022-01-01 \
     --end-date 2023-06-30 \
     --output-dir data/processed/phase35_w1_calibration
   ```

4. **Compute Turnover** (wave-specific weights)
   ```python
   import pandas as pd
   weights = pd.read_parquet('data/processed/phase35_w1_calibration_target_weights.parquet')
   weights = weights.set_index('date').sort_index()
   turnover = weights.diff().abs().sum(axis=1)
   print(f'Mean turnover: {turnover.mean():.2%}')
   ```

### Artifact Naming Convention

```
data/processed/phase35_{wave}_{window}_factor_scores.parquet
data/processed/phase35_{wave}_{window}_target_weights.parquet
data/processed/phase35_{wave}_{window}/phase34_*.csv
```

Where:
- `{wave}` = `w1`, `w2`, `w3`
- `{window}` = `calibration`, `validation`, `holdout`

### Script Updates Required

**File**: `scripts/generate_phase34_factor_scores.py`

Add `--preset` argument:
```python
parser.add_argument('--preset', default='DEFAULT_DAY4', help='Factor preset name')
parser.add_argument('--output', default='data/processed/phase34_factor_scores.parquet', help='Output path')
```

**File**: `scripts/generate_phase34_weights.py`

Add `--factor-scores` argument:
```python
parser.add_argument('--factor-scores', default='data/processed/phase34_factor_scores.parquet', help='Input factor scores')
parser.add_argument('--output', default='data/processed/phase34_target_weights.parquet', help='Output path')
```

**File**: `scripts/attribution_report.py`

Already supports `--factor-scores-path`, `--target-weights-path`, `--output-dir` (verified in Phase 34).

## Evidence Gate Contract

### Operational Requirements

All Phase 35 experiments must use:

1. **Same Simulation Engine**: `engine.run_simulation()` path (if applicable) or equivalent portfolio construction logic
2. **Same Cost/Friction Assumptions**:
   - Transaction costs: 10 bps per trade
   - Slippage: 5 bps market impact
   - No leverage constraints (long-only)
3. **Same Baseline Window**: Phase 34 full window (2022-01-01 to 2024-12-31) for baseline comparison
4. **Same Attribution Protocol**: `scripts/attribution_report.py` with identical IC/R²/regime computation logic

### Delta Comparison Protocol

For each wave, report delta vs Phase 34 baseline:

```
Delta IC = Wave_IC - Baseline_IC
Delta R² = Wave_R² - Baseline_R²
Delta Regime Hit-Rate = Wave_Hit_Rate - Baseline_Hit_Rate
Delta Turnover = Wave_Turnover - Baseline_Turnover
```

### Baseline Anchoring

Phase 34 baseline metrics (full window 2022-2024):
- Mean IC: -0.002
- Contribution R²: -0.268
- Regime hit-rates: GREEN 25%, AMBER 0%, RED 50%
- Turnover: 100.58% daily mean (median: 98.62%, p95: 188.15%)

**Note**: Turnover computed as `sum(abs(w_t - w_{t-1}))` where weights sum to 1.0. High baseline turnover (>100%) indicates frequent rebalancing in Phase 34.

All wave experiments report absolute metrics AND deltas vs this baseline.

### Evidence Artifacts

Each wave/window must produce:
- `phase35_{wave}_{window}/phase34_summary.json` (IC, R², regime hit-rate)
- `phase35_{wave}_{window}/phase34_attribution.csv` (portfolio returns, contributions, residual)
- `phase35_{wave}_{window}_target_weights.parquet` (for turnover computation)
- Ablation matrix row with absolute + delta metrics

| Experiment | Candidates | Weights | Regime Norm | Window | Mean IC | R² | Coverage | Turnover | Status |
|------------|-----------|---------|-------------|--------|---------|-----|----------|----------|--------|
| **Baseline (Phase 34)** | Current | 0.25 each | zscore | Full | -0.002 | -0.268 | ~50% | - | Complete |
| **Wave 1 - Calibration** | Improved | 0.25 each | zscore | 2022-2023H1 | TBD | TBD | ≥50% | <50% | Pending |
| **Wave 1 - Validation** | Improved | 0.25 each | zscore | 2023H2-2024Q1 | TBD | TBD | ≥50% | <50% | Pending |
| **Wave 2 - Calibration** | Improved | 0.70/0.10/0.10/0.10 | zscore | 2022-2023H1 | TBD | TBD | ≥50% | <50% | Pending |
| **Wave 2 - Validation** | Improved | 0.70/0.10/0.10/0.10 | zscore | 2023H2-2024Q1 | TBD | TBD | ≥50% | <50% | Pending |
| **Wave 3 - Calibration** | Improved | 0.70/0.10/0.10/0.10 | regime_adaptive | 2022-2023H1 | TBD | TBD | ≥50% | <50% | Pending |
| **Wave 3 - Validation** | Improved | 0.70/0.10/0.10/0.10 | regime_adaptive | 2023H2-2024Q1 | TBD | TBD | ≥50% | <50% | Pending |
| **Final - Holdout** | Best Wave | Best Weights | Best Norm | 2024Q2-Q4 | >0.02 | >0.5 | ≥50% | <50% | Gate |

### Wave Promotion Rules

- **Wave 1 → Wave 2**: If calibration IC improves AND validation confirms
- **Wave 2 → Wave 3**: If Wave 2 beats Wave 1 on validation
- **Wave 3 → Holdout**: If Wave 3 beats Wave 2 on validation
- **Final Gate**: Holdout window must meet all hard targets

---

## Testing Strategy

### Regression Protection

All 17 existing tests must continue to pass:

```bash
pytest tests/test_factor_attribution.py \
       tests/test_behavior_ledger.py \
       tests/test_attribution_validation.py \
       tests/test_attribution_integration.py -v
```

### New Tests for Wave 3

Add `tests/test_factor_specs.py::test_regime_adaptive_norm_negative_factors_stress_penalty()` to verify negative factors remain negative in stress regimes.

### Accounting Identity Verification

After each wave/window, verify accounting identity on wave-specific attribution:

```bash
# Replace {wave} and {window} with actual values (e.g., w1, calibration)
python -c "
import pandas as pd
attr = pd.read_csv('data/processed/phase35_{wave}_{window}/phase34_attribution.csv', index_col=0)
contrib_cols = [c for c in attr.columns if c.endswith('_contribution')]
total_contrib = attr[contrib_cols].sum(axis=1)
reconstructed = total_contrib + attr['residual']
error = (reconstructed - attr['portfolio_return']).abs()
assert (error < 1e-8).all(), 'Accounting identity violated'
print('✓ Accounting identity holds for phase35_{wave}_{window}')
"
```

---

## Leakage Prevention

### PIT-Safety

All features from `data/processed/features.parquet` are point-in-time safe:
- Fundamentals keyed by `release_date`
- Technical indicators use only past data
- No future-informed normalization (cross-sectional only)

### Explicit Lagging

Feature computation already implements explicit lagging (verified in Phase 34).

### Cross-Sectional Normalization Only

All normalization (zscore, rank, regime_adaptive) is cross-sectional (grouped by date). No time-series normalization that could leak future information.

---

## Rollback Plan

### If Targets Not Met After All Waves

1. Revert `strategies/factor_specs.py` to Phase 34 baseline
2. Document learnings in `docs/decision log.md`
3. Consider alternative approaches:
   - New data sources (alternative fundamental providers)
   - Different factor families (value, growth, size, carry)
   - Revisit regime classification logic (may be adding noise)
   - Consult Phase 34 SAW report for additional opportunities

### Partial Success Scenarios

- **Wave 1 succeeds, Wave 2/3 fail**: Keep Wave 1 improvements, document that reweighting/regime norm didn't help
- **Wave 1/2 succeed, Wave 3 fails**: Keep Wave 1/2, document that regime norm didn't help or introduced bugs
- **All waves fail**: Full rollback to Phase 34 baseline, escalate to research team

---

## Implementation Checklist

### Phase 1: Brief & Setup
- [x] Create Phase 35 brief (this document)
- [ ] Review and approve brief
- [ ] Create `PHASE35_PRESETS` dict in `strategies/factor_specs.py`
- [ ] Wire presets through `CompanyScorecard.from_factor_preset()`

### Phase 2: Wave 1
- [ ] Implement `build_phase35_wave1_candidate_specs()` (revised: no composite_score)
- [ ] Update `scripts/generate_phase34_factor_scores.py` to accept `--preset` and `--output` args
- [ ] Update `scripts/generate_phase34_weights.py` to accept `--factor-scores` and `--output` args
- [ ] Generate Wave 1 factor scores on calibration window
- [ ] Generate Wave 1 target weights on calibration window
- [ ] Run Wave 1 attribution report on calibration window
- [ ] Compute Wave 1 turnover on calibration window
- [ ] Check interim gates (IC, coverage, turnover)
- [ ] Generate Wave 1 artifacts on validation window
- [ ] Update ablation matrix with Wave 1 results
- [ ] Decision: Proceed to Wave 2 or iterate Wave 1?

### Phase 3: Wave 2
- [ ] Implement `build_phase35_wave2_momentum_heavy_specs()`
- [ ] Generate Wave 2 factor scores on calibration window
- [ ] Generate Wave 2 target weights on calibration window
- [ ] Run Wave 2 attribution report on calibration window
- [ ] Compute Wave 2 turnover on calibration window
- [ ] Check interim gates
- [ ] Generate Wave 2 artifacts on validation window
- [ ] Update ablation matrix with Wave 2 results
- [ ] Decision: Proceed to Wave 3 or revert to Wave 1?

### Phase 4: Wave 3
- [ ] Update `regime_adaptive_norm()` signature (add `factor_direction` parameter)
- [ ] Update `CompanyScorecard._normalize()` caller (pass `factor_direction`)
- [ ] Add test for negative factors in stress (`test_regime_adaptive_norm_negative_factors_stress_penalty`)
- [ ] Implement `build_phase35_wave3_regime_penalty_specs()`
- [ ] Generate Wave 3 factor scores on calibration window
- [ ] Generate Wave 3 target weights on calibration window
- [ ] Run Wave 3 attribution report on calibration window
- [ ] Compute Wave 3 turnover on calibration window
- [ ] Check interim gates
- [ ] Generate Wave 3 artifacts on validation window
- [ ] Update ablation matrix with Wave 3 results
- [ ] Decision: Proceed to holdout or revert?

### Phase 5: Holdout Evaluation
- [ ] Generate best wave artifacts on holdout window (2024Q2-Q4)
- [ ] Verify all hard targets met on holdout:
  - [ ] Mean IC > 0.02
  - [ ] Contribution R² > 0.5
  - [ ] Regime hit-rate > 70% for each of GREEN, AMBER, RED
  - [ ] IC consistency > 0.3
  - [ ] Coverage ≥ 50%
  - [ ] Turnover < 50% daily
- [ ] Run all 17 regression tests
- [ ] Verify accounting identity (error < 1e-8)
- [ ] Document final results in ablation matrix

### Phase 6: Closure
- [ ] Run all 17 regression tests
- [ ] Verify accounting identity
- [ ] Create `docs/PHASE35_CLOSURE.md` (mandatory)
- [ ] Create Phase 35 SAW report (mandatory - Strengths, Areas for improvement, Warnings)
- [ ] Update `docs/decision log.md`
- [ ] Update `README.md` with Phase 35 status
- [ ] Commit changes locally
- [ ] Request user approval for GitHub push
- [ ] Push to GitHub (only after explicit user approval)

---

## Approval

**Awaiting Approval**: This brief must be approved before implementation begins.

**Approval Criteria**:
- Regime taxonomy resolution accepted (3-state model)
- Walk-forward protocol accepted (calibration/validation/holdout)
- Clean preset architecture accepted (no collision with Phase 19.5)
- Coverage/turnover gates accepted
- Two-level gates accepted (interim + final)

**Approved By**: _Pending_
**Approval Date**: _Pending_
**Implementation Start**: _After approval_

---

**Document Version**: 1.0
**Last Updated**: 2026-03-06
**Next Review**: After Wave 1 completion
