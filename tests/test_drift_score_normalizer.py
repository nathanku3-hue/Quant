"""
Tests for Phase 33A Step 4: Score Normalization Contract

Validates:
1. Consistency: Same input → same output (determinism)
2. Bounded output: All scores in [0, 10] range
3. Semantic correctness: 0=no drift, 5=moderate, 10=severe
4. Per-taxonomy normalization logic
5. Aggregation behavior: Weighted max preserves worst taxonomy
6. Edge case handling: Missing details, extreme values
"""

import pytest

from core.drift_score_normalizer import (
    aggregate_drift_scores,
    normalize_allocation_drift,
    normalize_drift_result,
    normalize_parameter_drift,
    normalize_regime_drift,
    normalize_schedule_drift,
)


# ================================================================================
# Allocation Drift Normalization Tests
# ================================================================================


def test_normalize_allocation_drift_zero():
    """
    Contract: Zero sigma drift → 0.0 normalized score (perfect match).
    """
    score = normalize_allocation_drift(0.0)
    assert score == 0.0


def test_normalize_allocation_drift_threshold():
    """
    Contract: 2.0 sigma drift → 5.0 normalized score (μ + 2σ baseline).

    Critical: This is the actionable warning threshold. 2σ is industry standard
    for statistical significance.
    """
    score = normalize_allocation_drift(2.0)
    assert score == 5.0


def test_normalize_allocation_drift_severe():
    """
    Contract: 4.0 sigma drift → 10.0 normalized score (severe drift).
    """
    score = normalize_allocation_drift(4.0)
    assert score == 10.0


def test_normalize_allocation_drift_extreme_capped():
    """
    Contract: Extreme sigma (>4.0) capped at 10.0 (prevent score explosion).
    """
    score = normalize_allocation_drift(100.0)
    assert score == 10.0


def test_normalize_allocation_drift_linear_scaling():
    """
    Contract: Linear scaling below cap (sigma × 2.5).
    """
    score = normalize_allocation_drift(1.0)
    assert score == 2.5

    score = normalize_allocation_drift(3.0)
    assert score == 7.5


def test_normalize_allocation_drift_consistency():
    """
    Contract: Same input produces same output (determinism).
    """
    score1 = normalize_allocation_drift(2.5)
    score2 = normalize_allocation_drift(2.5)
    assert score1 == score2


# ================================================================================
# Regime Drift Normalization Tests
# ================================================================================


def test_normalize_regime_drift_no_divergence():
    """
    Contract: No regime divergence → 0.0 normalized score.
    """
    details = {"state_divergence_steps": 0, "exposure_divergence": 0.0}
    score = normalize_regime_drift(0.0, details)
    assert score == 0.0


def test_normalize_regime_drift_state_only():
    """
    Contract: State divergence scoring (1 step = 3.0, 2 steps = 6.0).

    State steps represent regime transitions:
    - 1 step: GREEN↔AMBER or AMBER↔RED (3.0 points)
    - 2 steps: GREEN↔RED (6.0 points)
    """
    # One-step transition (e.g., GREEN → AMBER)
    details = {"state_divergence_steps": 1, "exposure_divergence": 0.0}
    score = normalize_regime_drift(1.0, details)
    assert score == 3.0

    # Two-step transition (e.g., GREEN → RED, critical)
    details = {"state_divergence_steps": 2, "exposure_divergence": 0.0}
    score = normalize_regime_drift(3.0, details)
    assert score == 6.0


def test_normalize_regime_drift_exposure_only():
    """
    Contract: Exposure divergence scoring (delta × 10).

    30% exposure deviation → 3.0 points
    """
    details = {"state_divergence_steps": 0, "exposure_divergence": 0.30}
    score = normalize_regime_drift(2.0, details)
    assert score == 3.0


def test_normalize_regime_drift_combined():
    """
    Contract: Combined state + exposure drift.

    Example: GREEN→RED (2 steps = 6.0) + 35% exposure (3.5) = 9.5 total
    """
    details = {"state_divergence_steps": 2, "exposure_divergence": 0.35}
    score = normalize_regime_drift(5.0, details)
    assert score == 9.5


def test_normalize_regime_drift_capped():
    """
    Contract: Extreme combined drift capped at 10.0.
    """
    details = {"state_divergence_steps": 3, "exposure_divergence": 0.50}
    score = normalize_regime_drift(10.0, details)
    assert score == 10.0


def test_normalize_regime_drift_fallback():
    """
    Contract: Fallback scaling when details unavailable (raw × 1.2).

    Used when drift_score provided but details missing.
    """
    score = normalize_regime_drift(5.0, details=None)
    assert score == 6.0  # 5.0 × 1.2


def test_normalize_regime_drift_consistency():
    """
    Contract: Same input produces same output (determinism).
    """
    details = {"state_divergence_steps": 1, "exposure_divergence": 0.20}
    score1 = normalize_regime_drift(3.0, details)
    score2 = normalize_regime_drift(3.0, details)
    assert score1 == score2


# ================================================================================
# Parameter Drift Normalization Tests
# ================================================================================


def test_normalize_parameter_drift_zero():
    """
    Contract: No parameter changes → 0.0 normalized score.
    """
    details = {"n_changed": 0}
    score = normalize_parameter_drift(0.0, details)
    assert score == 0.0


def test_normalize_parameter_drift_half_changed():
    """
    Contract: 50% of parameters changed → 5.0 normalized score.

    Assumes 10 total parameters (heuristic).
    """
    details = {"n_changed": 5}
    score = normalize_parameter_drift(5.0, details)
    assert score == 5.0


def test_normalize_parameter_drift_all_changed():
    """
    Contract: 100% of parameters changed → 10.0 normalized score.
    """
    details = {"n_changed": 10}
    score = normalize_parameter_drift(10.0, details)
    assert score == 10.0


def test_normalize_parameter_drift_fallback():
    """
    Contract: Fallback when details missing (1 change = 1.0 point).
    """
    score = normalize_parameter_drift(3.0, details=None)
    assert score == 3.0


def test_normalize_parameter_drift_capped():
    """
    Contract: Extreme parameter changes capped at 10.0.
    """
    details = {"n_changed": 20}
    score = normalize_parameter_drift(20.0, details)
    assert score == 10.0


def test_normalize_parameter_drift_consistency():
    """
    Contract: Same input produces same output (determinism).
    """
    details = {"n_changed": 3}
    score1 = normalize_parameter_drift(3.0, details)
    score2 = normalize_parameter_drift(3.0, details)
    assert score1 == score2


# ================================================================================
# Schedule Drift Normalization Tests
# ================================================================================


def test_normalize_schedule_drift_zero_missed():
    """
    Contract: No missed rebalances → 0.0 normalized score (perfect execution).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 0}
    score = normalize_schedule_drift(0.0, details)
    assert score == 0.0


def test_normalize_schedule_drift_half_missed():
    """
    Contract: 50% missed rebalances → 5.0 normalized score.
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 5}
    score = normalize_schedule_drift(5.0, details)
    assert score == 5.0


def test_normalize_schedule_drift_all_missed():
    """
    Contract: 100% missed rebalances → 10.0 normalized score (complete failure).
    """
    details = {"expected_rebalances": 4, "missed_rebalances": 4}
    score = normalize_schedule_drift(4.0, details)
    assert score == 10.0


def test_normalize_schedule_drift_partial_missed():
    """
    Contract: 20% missed rebalances → 2.0 normalized score.
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 2}
    score = normalize_schedule_drift(2.0, details)
    assert score == 2.0


def test_normalize_schedule_drift_no_rebalances_scheduled():
    """
    Contract: Edge case - no rebalances scheduled → 0.0 (no drift).
    """
    details = {"expected_rebalances": 0, "missed_rebalances": 0}
    score = normalize_schedule_drift(0.0, details)
    assert score == 0.0


def test_normalize_schedule_drift_missing_details_raises():
    """
    Contract: Missing expected_rebalances raises ValueError (fail-closed).

    Cannot compute percentage without baseline - fail explicitly.
    """
    with pytest.raises(ValueError, match="requires 'expected_rebalances'"):
        normalize_schedule_drift(2.0, details=None)


def test_normalize_schedule_drift_consistency():
    """
    Contract: Same input produces same output (determinism).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 3}
    score1 = normalize_schedule_drift(3.0, details)
    score2 = normalize_schedule_drift(3.0, details)
    assert score1 == score2


# ================================================================================
# Aggregation Tests
# ================================================================================


def test_aggregate_drift_scores_single_taxonomy():
    """
    Contract: Single taxonomy → returns that score.
    """
    scores = {"ALLOCATION_DRIFT": 7.5}
    aggregated = aggregate_drift_scores(scores)
    assert aggregated == 7.5


def test_aggregate_drift_scores_max_dominates():
    """
    Contract: Weighted max strategy - worst taxonomy dominates.

    Rationale: Single critical drift (e.g., ALLOCATION=9.0) should trigger RED
    even if other taxonomies are GREEN.
    """
    scores = {
        "ALLOCATION_DRIFT": 9.0,  # Critical
        "REGIME_DRIFT": 2.0,      # Green
        "PARAMETER_DRIFT": 0.0,   # Green
        "SCHEDULE_DRIFT": 1.0,    # Green
    }
    aggregated = aggregate_drift_scores(scores)
    assert aggregated == 9.0  # Max (9.0×1.0, 2.0×0.8, 0.0×0.6, 1.0×0.5) = 9.0


def test_aggregate_drift_scores_weighted():
    """
    Contract: Weights applied before max selection.

    Example: REGIME=5.0 with weight=1.2 → 6.0 weighted score
    """
    scores = {
        "ALLOCATION_DRIFT": 4.0,  # 4.0 × 1.0 = 4.0
        "REGIME_DRIFT": 5.0,      # 5.0 × 1.2 = 6.0 (wins)
    }
    weights = {
        "ALLOCATION_DRIFT": 1.0,
        "REGIME_DRIFT": 1.2,
    }
    aggregated = aggregate_drift_scores(scores, weights)
    assert aggregated == 6.0


def test_aggregate_drift_scores_capped():
    """
    Contract: Aggregated score capped at 10.0 when weights push above bound.

    Note: After hardening, aggregate_drift_scores validates inputs are in [0, 10].
    This test validates clamping when weights > 1.0 push weighted score above 10.
    """
    scores = {"ALLOCATION_DRIFT": 9.0}  # Valid normalized score
    weights = {"ALLOCATION_DRIFT": 1.5}  # Weight pushes to 13.5
    aggregated = aggregate_drift_scores(scores, weights)
    assert aggregated == 10.0  # Clamped from 13.5


def test_aggregate_drift_scores_empty():
    """
    Contract: Empty scores dict → 0.0 (no drift).
    """
    aggregated = aggregate_drift_scores({})
    assert aggregated == 0.0


def test_aggregate_drift_scores_default_weights():
    """
    Contract: Default weights prioritize allocation > regime > parameter > schedule.

    Default weights:
    - ALLOCATION_DRIFT: 1.0
    - REGIME_DRIFT: 0.8
    - PARAMETER_DRIFT: 0.6
    - SCHEDULE_DRIFT: 0.5
    """
    scores = {
        "ALLOCATION_DRIFT": 5.0,
        "REGIME_DRIFT": 6.0,
        "PARAMETER_DRIFT": 7.0,
        "SCHEDULE_DRIFT": 8.0,
    }
    aggregated = aggregate_drift_scores(scores)
    # Max of: 5.0×1.0=5.0, 6.0×0.8=4.8, 7.0×0.6=4.2, 8.0×0.5=4.0
    assert aggregated == 5.0


# ================================================================================
# Convenience Function Tests
# ================================================================================


def test_normalize_drift_result_allocation():
    """
    Contract: Convenience function dispatches to correct normalizer.
    """
    score = normalize_drift_result("ALLOCATION_DRIFT", 2.0)
    assert score == 5.0


def test_normalize_drift_result_regime():
    """
    Contract: Regime normalization with details.
    """
    details = {"state_divergence_steps": 1, "exposure_divergence": 0.10}
    score = normalize_drift_result("REGIME_DRIFT", 2.0, details)
    assert score == 4.0  # 1×3 + 0.10×10 = 4.0


def test_normalize_drift_result_parameter():
    """
    Contract: Parameter normalization.
    """
    details = {"n_changed": 2}
    score = normalize_drift_result("PARAMETER_DRIFT", 2.0, details)
    assert score == 2.0


def test_normalize_drift_result_schedule():
    """
    Contract: Schedule normalization with details.
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 3}
    score = normalize_drift_result("SCHEDULE_DRIFT", 3.0, details)
    assert score == 3.0


def test_normalize_drift_result_unknown_taxonomy_raises():
    """
    Contract: Unknown taxonomy raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Unknown drift taxonomy"):
        normalize_drift_result("INVALID_TAXONOMY", 5.0)


# ================================================================================
# Cross-Taxonomy Consistency Tests
# ================================================================================


def test_all_normalizers_bounded():
    """
    Contract: All normalizers produce scores in [0, 10] range.
    """
    # Test allocation
    for sigma in [0, 0.5, 1.0, 2.0, 5.0, 10.0]:
        score = normalize_allocation_drift(sigma)
        assert 0.0 <= score <= 10.0, f"Allocation score {score} out of bounds"

    # Test regime
    for raw in [0, 2, 5, 10]:
        for state_steps in [0, 1, 2, 3]:
            for exposure in [0.0, 0.2, 0.5, 1.0]:
                details = {"state_divergence_steps": state_steps, "exposure_divergence": exposure}
                score = normalize_regime_drift(raw, details)
                assert 0.0 <= score <= 10.0, f"Regime score {score} out of bounds"

    # Test parameter
    for count in [0, 3, 5, 10, 20]:
        score = normalize_parameter_drift(count, {"n_changed": count})
        assert 0.0 <= score <= 10.0, f"Parameter score {score} out of bounds"

    # Test schedule
    for missed in [0, 2, 5, 10]:
        details = {"expected_rebalances": 10, "missed_rebalances": missed}
        score = normalize_schedule_drift(missed, details)
        assert 0.0 <= score <= 10.0, f"Schedule score {score} out of bounds"


def test_all_normalizers_zero_drift():
    """
    Contract: Zero drift input → 0.0 normalized score across all taxonomies.
    """
    assert normalize_allocation_drift(0.0) == 0.0
    assert normalize_regime_drift(0.0, {"state_divergence_steps": 0, "exposure_divergence": 0.0}) == 0.0
    assert normalize_parameter_drift(0.0, {"n_changed": 0}) == 0.0
    assert normalize_schedule_drift(0.0, {"expected_rebalances": 10, "missed_rebalances": 0}) == 0.0


# ================================================================================
# Adversarial Input Tests (Hardening for Finding #1)
# ================================================================================


def test_normalize_allocation_drift_negative_clamped():
    """
    Contract: Negative sigma inputs clamped to 0.0 (fail-safe, not fail-closed).

    Rationale: Chi-squared test should never produce negative sigma, but if
    upstream bug occurs, clamp to 0.0 rather than propagate negative score.
    """
    score = normalize_allocation_drift(-1.0)
    assert score == 0.0


def test_normalize_allocation_drift_nan_raises():
    """
    Contract: NaN input raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_sigma.*finite"):
        normalize_allocation_drift(float('nan'))


def test_normalize_allocation_drift_inf_raises():
    """
    Contract: Infinite input raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_sigma.*finite"):
        normalize_allocation_drift(float('inf'))

    with pytest.raises(ValueError, match="Invalid drift_score_sigma.*finite"):
        normalize_allocation_drift(float('-inf'))


def test_normalize_regime_drift_negative_exposure_raises():
    """
    Contract: Negative exposure_divergence raises ValueError (fail-closed).

    Exposure divergence is absolute difference, should never be negative.
    """
    details = {"state_divergence_steps": 1, "exposure_divergence": -0.2}
    with pytest.raises(ValueError, match="Invalid exposure_divergence.*Must be >= 0"):
        normalize_regime_drift(2.0, details)


def test_normalize_regime_drift_negative_state_steps_raises():
    """
    Contract: Negative state_divergence_steps raises ValueError (fail-closed).
    """
    details = {"state_divergence_steps": -1, "exposure_divergence": 0.1}
    with pytest.raises(ValueError, match="Invalid state_divergence_steps.*Must be >= 0"):
        normalize_regime_drift(2.0, details)


def test_normalize_regime_drift_nan_raises():
    """
    Contract: NaN raw score raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_raw.*finite"):
        normalize_regime_drift(float('nan'))


def test_normalize_regime_drift_inf_raises():
    """
    Contract: Infinite raw score raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_raw.*finite"):
        normalize_regime_drift(float('inf'))


def test_normalize_parameter_drift_negative_raises():
    """
    Contract: Negative parameter count raises ValueError (fail-closed).

    Changed parameter count cannot be negative.
    """
    with pytest.raises(ValueError, match="Invalid drift_score_count.*Must be >= 0"):
        normalize_parameter_drift(-3.0)


def test_normalize_parameter_drift_negative_n_changed_raises():
    """
    Contract: Negative n_changed in details raises ValueError (fail-closed).
    """
    details = {"n_changed": -2}
    with pytest.raises(ValueError, match="Invalid n_changed.*Must be >= 0"):
        normalize_parameter_drift(2.0, details)


def test_normalize_parameter_drift_zero_total_params_raises():
    """
    Contract: Zero or negative total_params raises ValueError (fail-closed).

    Cannot compute percentage with zero denominator.
    """
    details = {"n_changed": 3, "total_params": 0}
    with pytest.raises(ValueError, match="Invalid total_params.*Must be > 0"):
        normalize_parameter_drift(3.0, details)

    details = {"n_changed": 3, "total_params": -5}
    with pytest.raises(ValueError, match="Invalid total_params.*Must be > 0"):
        normalize_parameter_drift(3.0, details)


def test_normalize_parameter_drift_nan_raises():
    """
    Contract: NaN count raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_count.*finite"):
        normalize_parameter_drift(float('nan'))


def test_normalize_parameter_drift_inf_raises():
    """
    Contract: Infinite count raises ValueError (fail-closed).
    """
    with pytest.raises(ValueError, match="Invalid drift_score_count.*finite"):
        normalize_parameter_drift(float('inf'))


def test_normalize_parameter_drift_respects_total_params():
    """
    Contract: Uses total_params from details when provided (Finding #2 fix).

    Example: Strategy with 24 params, 12 changed → 50% → 5.0 score
    """
    details = {"n_changed": 12, "total_params": 24}
    score = normalize_parameter_drift(12.0, details)
    assert score == 5.0  # 12/24 = 50% → 5.0


def test_normalize_schedule_drift_negative_raises():
    """
    Contract: Negative missed count raises ValueError (fail-closed).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 2}
    with pytest.raises(ValueError, match="Invalid drift_score_count.*Must be >= 0"):
        normalize_schedule_drift(-2.0, details)


def test_normalize_schedule_drift_negative_expected_raises():
    """
    Contract: Negative expected_rebalances raises ValueError (fail-closed).
    """
    details = {"expected_rebalances": -10, "missed_rebalances": 2}
    with pytest.raises(ValueError, match="Invalid expected_rebalances.*Must be >= 0"):
        normalize_schedule_drift(2.0, details)


def test_normalize_schedule_drift_negative_missed_raises():
    """
    Contract: Negative missed_rebalances raises ValueError (fail-closed).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": -2}
    with pytest.raises(ValueError, match="Invalid missed_rebalances.*Must be >= 0"):
        normalize_schedule_drift(2.0, details)


def test_normalize_schedule_drift_nan_raises():
    """
    Contract: NaN count raises ValueError (fail-closed).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 2}
    with pytest.raises(ValueError, match="Invalid drift_score_count.*finite"):
        normalize_schedule_drift(float('nan'), details)


def test_normalize_schedule_drift_inf_raises():
    """
    Contract: Infinite count raises ValueError (fail-closed).
    """
    details = {"expected_rebalances": 10, "missed_rebalances": 2}
    with pytest.raises(ValueError, match="Invalid drift_score_count.*finite"):
        normalize_schedule_drift(float('inf'), details)


def test_aggregate_drift_scores_negative_score_raises():
    """
    Contract: Negative normalized score raises ValueError (fail-closed).

    All normalized scores must be in [0, 10] range.
    """
    scores = {"ALLOCATION_DRIFT": -2.0}
    with pytest.raises(ValueError, match="Normalized score.*out of bounds"):
        aggregate_drift_scores(scores)


def test_aggregate_drift_scores_out_of_bounds_raises():
    """
    Contract: Score > 10.0 raises ValueError (fail-closed).
    """
    scores = {"ALLOCATION_DRIFT": 12.0}
    with pytest.raises(ValueError, match="Normalized score.*out of bounds"):
        aggregate_drift_scores(scores)


def test_aggregate_drift_scores_nan_raises():
    """
    Contract: NaN score raises ValueError (fail-closed).
    """
    scores = {"ALLOCATION_DRIFT": float('nan')}
    with pytest.raises(ValueError, match="Invalid normalized score.*finite"):
        aggregate_drift_scores(scores)


def test_aggregate_drift_scores_inf_raises():
    """
    Contract: Infinite score raises ValueError (fail-closed).
    """
    scores = {"ALLOCATION_DRIFT": float('inf')}
    with pytest.raises(ValueError, match="Invalid normalized score.*finite"):
        aggregate_drift_scores(scores)


def test_aggregate_drift_scores_weight_above_one_clamped():
    """
    Contract: Weights > 1.0 can push score above 10, but result is clamped (Finding #3 mitigation).

    Example: REGIME=10.0 with weight=1.2 → 12.0 weighted → clamped to 10.0
    """
    scores = {"REGIME_DRIFT": 10.0}
    weights = {"REGIME_DRIFT": 1.2}
    aggregated = aggregate_drift_scores(scores, weights)
    assert aggregated == 10.0  # Clamped from 12.0


def test_aggregate_drift_scores_negative_weight_raises():
    """
    Contract: Negative weight raises ValueError (fail-closed).

    Rationale: Negative weights can suppress severe drift (e.g., 10.0 × -1.0 = -10.0).
    This is a misconfiguration that must be rejected.
    """
    scores = {"ALLOCATION_DRIFT": 10.0}
    weights = {"ALLOCATION_DRIFT": -1.0}
    with pytest.raises(ValueError, match="Invalid weight.*Must be non-negative"):
        aggregate_drift_scores(scores, weights)


def test_aggregate_drift_scores_nan_weight_raises():
    """
    Contract: NaN weight raises ValueError (fail-closed).
    """
    scores = {"ALLOCATION_DRIFT": 5.0}
    weights = {"ALLOCATION_DRIFT": float('nan')}
    with pytest.raises(ValueError, match="Invalid weight.*finite"):
        aggregate_drift_scores(scores, weights)


def test_aggregate_drift_scores_inf_weight_raises():
    """
    Contract: Infinite weight raises ValueError (fail-closed).
    """
    scores = {"ALLOCATION_DRIFT": 5.0}
    weights = {"ALLOCATION_DRIFT": float('inf')}
    with pytest.raises(ValueError, match="Invalid weight.*finite"):
        aggregate_drift_scores(scores, weights)


def test_aggregate_drift_scores_zero_weight_allowed():
    """
    Contract: Zero weight is valid (suppresses taxonomy completely).

    Use case: Temporarily disable a taxonomy without removing it from monitoring.
    """
    scores = {
        "ALLOCATION_DRIFT": 10.0,  # Severe
        "REGIME_DRIFT": 5.0,        # Moderate
    }
    weights = {
        "ALLOCATION_DRIFT": 0.0,  # Suppress allocation
        "REGIME_DRIFT": 1.0,
    }
    aggregated = aggregate_drift_scores(scores, weights)
    assert aggregated == 5.0  # Only regime contributes (10.0 × 0.0 = 0, 5.0 × 1.0 = 5.0)


def test_all_normalizers_moderate_drift():
    """
    Contract: Moderate drift (threshold crossing) → ~5.0 normalized score.

    Threshold semantics:
    - Allocation: 2.0σ → 5.0
    - Regime: 1 state step + 20% exposure → 5.0
    - Parameter: 50% changed → 5.0
    - Schedule: 50% missed → 5.0
    """
    # Allocation: 2σ → 5.0
    assert normalize_allocation_drift(2.0) == 5.0

    # Regime: 1 step + 20% exposure → 3.0 + 2.0 = 5.0
    details = {"state_divergence_steps": 1, "exposure_divergence": 0.20}
    assert normalize_regime_drift(3.0, details) == 5.0

    # Parameter: 5 of 10 → 5.0
    assert normalize_parameter_drift(5.0, {"n_changed": 5}) == 5.0

    # Schedule: 5 of 10 → 5.0
    details = {"expected_rebalances": 10, "missed_rebalances": 5}
    assert normalize_schedule_drift(5.0, details) == 5.0


def test_all_normalizers_severe_drift():
    """
    Contract: Severe drift → 10.0 normalized score (or close to it).
    """
    # Allocation: 4σ → 10.0
    assert normalize_allocation_drift(4.0) == 10.0

    # Regime: 2 steps + 40% exposure → 6.0 + 4.0 = 10.0
    details = {"state_divergence_steps": 2, "exposure_divergence": 0.40}
    assert normalize_regime_drift(8.0, details) == 10.0

    # Parameter: 10 of 10 → 10.0
    assert normalize_parameter_drift(10.0, {"n_changed": 10}) == 10.0

    # Schedule: 10 of 10 → 10.0
    details = {"expected_rebalances": 10, "missed_rebalances": 10}
    assert normalize_schedule_drift(10.0, details) == 10.0


# ================================================================================
# Integration Test: End-to-End Normalization + Aggregation
# ================================================================================


def test_integration_multi_taxonomy_drift():
    """
    Integration test: Simulate multi-taxonomy drift detection scenario.

    Scenario: Live strategy shows:
    - Allocation drift: 2.5σ (moderate deviation)
    - Regime drift: GREEN→AMBER transition + 25% exposure delta
    - Parameter drift: 2 of 10 parameters changed
    - Schedule drift: 1 of 10 rebalances missed

    Expected:
    - Allocation: 2.5 × 2.5 = 6.25
    - Regime: 1×3 + 0.25×10 = 5.5
    - Parameter: 2.0
    - Schedule: 1.0
    - Aggregated: max(6.25×1.0, 5.5×0.8, 2.0×0.6, 1.0×0.5) = 6.25
    """
    # Normalize each taxonomy
    allocation_normalized = normalize_allocation_drift(2.5)
    regime_normalized = normalize_regime_drift(
        3.5,
        {"state_divergence_steps": 1, "exposure_divergence": 0.25},
    )
    parameter_normalized = normalize_parameter_drift(2.0, {"n_changed": 2})
    schedule_normalized = normalize_schedule_drift(
        1.0,
        {"expected_rebalances": 10, "missed_rebalances": 1},
    )

    # Verify individual scores
    assert allocation_normalized == 6.25
    assert regime_normalized == 5.5
    assert parameter_normalized == 2.0
    assert schedule_normalized == 1.0

    # Aggregate
    normalized_scores = {
        "ALLOCATION_DRIFT": allocation_normalized,
        "REGIME_DRIFT": regime_normalized,
        "PARAMETER_DRIFT": parameter_normalized,
        "SCHEDULE_DRIFT": schedule_normalized,
    }
    aggregated = aggregate_drift_scores(normalized_scores)

    # Max weighted score should be allocation (6.25 × 1.0)
    assert aggregated == 6.25

    # Alert level interpretation (from drift_detector.py):
    # - GREEN: < 5.0
    # - YELLOW: 5.0 - 10.0
    # - RED: >= 10.0 (note: aggregated won't reach 10 unless single taxonomy severe)
    # In this case: 6.25 → YELLOW (warning level)
    assert 5.0 <= aggregated < 10.0  # YELLOW range
