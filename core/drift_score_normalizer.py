"""
Phase 33A Step 4: Score Normalization Contract

Converts drift scores from different taxonomies into unified [0, 10] scale for
aggregation and comparison. Enables multi-taxonomy drift monitoring with consistent
alert semantics.

Scale Semantics:
- 0.0 = No drift (within expected variance)
- 5.0 = Moderate drift (μ + 2σ threshold, actionable warning)
- 10.0 = Severe drift (critical divergence requiring intervention)

Normalization Rationale:
- Allocation: Chi-squared σ units × 2.5 (2σ → 5.0 baseline)
- Regime: Composite scoring with state steps (×3) + exposure delta (×10)
- Parameter: Percentage of changed parameters × 10
- Schedule: Percentage of missed rebalances × 10

FR-TBD: Multi-taxonomy drift aggregation for unified monitoring dashboard
"""

from typing import Any


def normalize_allocation_drift(
    drift_score_sigma: float,
    details: dict[str, Any] | None = None,
) -> float:
    """
    Normalize allocation drift from sigma units to [0, 10] scale.

    Allocation drift uses chi-squared goodness-of-fit test, returning drift_score
    in sigma units (standard deviations from expected distribution).

    Normalization: sigma × 2.5
    - 0.0σ → 0.0 (perfect match)
    - 2.0σ → 5.0 (threshold: μ + 2σ baseline for actionable warning)
    - 4.0σ → 10.0 (severe drift)

    Args:
        drift_score_sigma: Raw drift score in sigma units from chi-squared test
        details: Optional drift details dict (unused, for API consistency)

    Returns:
        Normalized score in [0, 10] range

    Raises:
        ValueError: If drift_score_sigma is NaN or infinite

    Example:
        >>> normalize_allocation_drift(0.5)  # Minor deviation
        1.25
        >>> normalize_allocation_drift(2.0)  # Threshold breach
        5.0
        >>> normalize_allocation_drift(4.5)  # Critical drift
        10.0
    """
    # Validate input: reject NaN/inf (fail-closed)
    if not isinstance(drift_score_sigma, (int, float)) or not float('-inf') < drift_score_sigma < float('inf'):
        raise ValueError(
            f"Invalid drift_score_sigma: {drift_score_sigma}. "
            "Must be finite numeric value."
        )

    normalized = drift_score_sigma * 2.5
    # Clamp to [0, 10] range (handle negative inputs)
    return max(0.0, min(normalized, 10.0))


def normalize_regime_drift(
    drift_score_raw: float,
    details: dict[str, Any] | None = None,
) -> float:
    """
    Normalize regime drift from composite score to [0, 10] scale.

    Regime drift uses composite scoring:
    - State divergence: RED↔GREEN=3, RED↔AMBER=1, AMBER↔GREEN=1
    - Exposure divergence: >30%=2.0, >15%=1.0
    - BOCPD breach: 1.5
    - VIX spike: sustained=2.0, active=1.0

    Raw range: [0, 8.5] (max: 3 + 2 + 1.5 + 2)

    Normalization Strategy:
    - Extract state_divergence_steps and exposure_divergence from details
    - Formula: state_steps × 3 + exposure_delta × 10
    - Fallback: Use raw_score × 1.2 if details unavailable (approximate scaling)

    Args:
        drift_score_raw: Raw composite drift score from validate_regime_state()
        details: Drift details dict with state_divergence_steps, exposure_divergence

    Returns:
        Normalized score in [0, 10] range

    Returns:
        Normalized score in [0, 10] range

    Raises:
        ValueError: If drift_score_raw is NaN or infinite

    Example:
        >>> details = {"state_divergence_steps": 2, "exposure_divergence": 0.35}
        >>> normalize_regime_drift(5.0, details)  # RED↔GREEN + 35% exposure
        9.5
        >>> normalize_regime_drift(1.0, details={"state_divergence_steps": 1, "exposure_divergence": 0.1})
        4.0
    """
    # Validate input: reject NaN/inf (fail-closed)
    if not isinstance(drift_score_raw, (int, float)) or not float('-inf') < drift_score_raw < float('inf'):
        raise ValueError(
            f"Invalid drift_score_raw: {drift_score_raw}. "
            "Must be finite numeric value."
        )

    if details:
        # Precise normalization using decomposed components
        state_steps = details.get("state_divergence_steps", 0)
        exposure_divergence = details.get("exposure_divergence", 0.0)

        # Validate components are non-negative (drift scores should be >= 0)
        if state_steps < 0:
            raise ValueError(f"Invalid state_divergence_steps: {state_steps}. Must be >= 0.")
        if exposure_divergence < 0:
            raise ValueError(f"Invalid exposure_divergence: {exposure_divergence}. Must be >= 0.")

        # Weight state changes heavily (3 points per step), exposure moderately (10x scale)
        normalized = (state_steps * 3.0) + (exposure_divergence * 10.0)
    else:
        # Fallback: Approximate scaling (raw max 8.5 → 10.0)
        normalized = drift_score_raw * 1.2

    # Clamp to [0, 10] range
    return max(0.0, min(normalized, 10.0))


def normalize_parameter_drift(
    drift_score_count: float,
    details: dict[str, Any] | None = None,
) -> float:
    """
    Normalize parameter drift from changed parameter count to [0, 10] scale.

    Parameter drift counts number of strategy parameters that differ between
    backtest config and live config.

    Normalization: Compute percentage of changed parameters × 10
    - If details available: (n_changed / total_params) × 10
    - Fallback heuristic: Assume ~10 total parameters → count × 1.0

    Scale Interpretation:
    - 0 changed → 0.0 (no drift)
    - 5 of 10 changed → 5.0 (moderate drift)
    - 10 of 10 changed → 10.0 (complete config mutation)

    Args:
        drift_score_count: Raw count of changed parameters from detect_parameter_drift()
        details: Optional dict with 'n_changed' and 'total_params' (optional)

    Returns:
        Normalized score in [0, 10] range

    Raises:
        ValueError: If drift_score_count is NaN, infinite, or negative

    Example:
        >>> normalize_parameter_drift(3.0, {"n_changed": 3, "total_params": 10})
        3.0
        >>> normalize_parameter_drift(5.0)  # Fallback heuristic
        5.0
    """
    # Validate input: reject NaN/inf/negative (fail-closed)
    if not isinstance(drift_score_count, (int, float)) or not float('-inf') < drift_score_count < float('inf'):
        raise ValueError(
            f"Invalid drift_score_count: {drift_score_count}. "
            "Must be finite numeric value."
        )
    if drift_score_count < 0:
        raise ValueError(f"Invalid drift_score_count: {drift_score_count}. Must be >= 0.")

    if details and "n_changed" in details:
        n_changed = details["n_changed"]

        # Validate n_changed is non-negative
        if n_changed < 0:
            raise ValueError(f"Invalid n_changed: {n_changed}. Must be >= 0.")

        # Use total_params from details if provided, otherwise fallback to heuristic
        total_params = details.get("total_params", 10.0)

        # Validate total_params is positive
        if total_params <= 0:
            raise ValueError(f"Invalid total_params: {total_params}. Must be > 0.")

        # Compute percentage changed
        percent_changed = (n_changed / total_params) * 100.0
        normalized = (percent_changed / 100.0) * 10.0
    else:
        # Fallback: Assume count directly maps (1 change = 1.0 on scale)
        normalized = drift_score_count

    # Clamp to [0, 10] range
    return max(0.0, min(normalized, 10.0))


def normalize_schedule_drift(
    drift_score_count: float,
    details: dict[str, Any] | None = None,
) -> float:
    """
    Normalize schedule drift from missed rebalance count to [0, 10] scale.

    Schedule drift counts number of missed rebalances (trades not executed within
    tolerance window of scheduled time).

    Normalization: Compute percentage of missed rebalances × 10
    - (missed / expected_rebalances) × 10
    - Requires details dict with 'expected_rebalances' and 'missed_rebalances'

    Scale Interpretation:
    - 0% missed → 0.0 (perfect execution)
    - 50% missed → 5.0 (moderate schedule degradation)
    - 100% missed → 10.0 (complete execution failure)

    Args:
        drift_score_count: Raw count of missed rebalances from track_rebalance_compliance()
        details: Drift details dict with 'expected_rebalances', 'missed_rebalances'

    Returns:
        Normalized score in [0, 10] range

    Raises:
        ValueError: If details missing required fields (expected_rebalances) or invalid values

    Example:
        >>> details = {"expected_rebalances": 10, "missed_rebalances": 2}
        >>> normalize_schedule_drift(2.0, details)
        2.0
        >>> details = {"expected_rebalances": 4, "missed_rebalances": 3}
        >>> normalize_schedule_drift(3.0, details)
        7.5
    """
    # Validate input: reject NaN/inf/negative (fail-closed)
    if not isinstance(drift_score_count, (int, float)) or not float('-inf') < drift_score_count < float('inf'):
        raise ValueError(
            f"Invalid drift_score_count: {drift_score_count}. "
            "Must be finite numeric value."
        )
    if drift_score_count < 0:
        raise ValueError(f"Invalid drift_score_count: {drift_score_count}. Must be >= 0.")

    if not details or "expected_rebalances" not in details:
        raise ValueError(
            "Schedule drift normalization requires 'expected_rebalances' in details dict. "
            "Cannot compute percentage without baseline."
        )

    expected = details["expected_rebalances"]
    missed = details.get("missed_rebalances", int(drift_score_count))

    # Validate expected and missed are non-negative
    if expected < 0:
        raise ValueError(f"Invalid expected_rebalances: {expected}. Must be >= 0.")
    if missed < 0:
        raise ValueError(f"Invalid missed_rebalances: {missed}. Must be >= 0.")

    if expected == 0:
        # No rebalances scheduled - interpret as no drift (edge case)
        return 0.0

    # Compute percentage missed
    percent_missed = (missed / expected) * 100.0
    normalized = (percent_missed / 100.0) * 10.0

    # Clamp to [0, 10] range
    return max(0.0, min(normalized, 10.0))


def aggregate_drift_scores(
    normalized_scores: dict[str, float],
    weights: dict[str, float] | None = None,
) -> float:
    """
    Aggregate multiple taxonomy drift scores into single unified drift metric.

    Uses weighted maximum strategy (not mean) to ensure worst taxonomy dominates.
    Rationale: Single critical taxonomy drift (e.g., ALLOCATION_DRIFT=9.0) should
    trigger RED alert even if other taxonomies are GREEN.

    Default Weights (if not provided):
    - ALLOCATION_DRIFT: 1.0 (highest priority - portfolio composition)
    - REGIME_DRIFT: 0.8 (high priority - market environment)
    - PARAMETER_DRIFT: 0.6 (medium priority - config mutation)
    - SCHEDULE_DRIFT: 0.5 (lower priority - execution timing)

    Aggregation Formula:
        max(normalized_score_i × weight_i for all taxonomies)

    Args:
        normalized_scores: Dict mapping taxonomy name to normalized score [0, 10]
        weights: Optional dict mapping taxonomy name to weight multiplier (must be >= 0)

    Returns:
        Aggregated drift score in [0, 10] range

    Raises:
        ValueError: If any normalized score is invalid (NaN, inf, or out of bounds)
        ValueError: If any weight is invalid (NaN, inf, or negative)

    Example:
        >>> scores = {
        ...     "ALLOCATION_DRIFT": 7.5,
        ...     "REGIME_DRIFT": 3.0,
        ...     "PARAMETER_DRIFT": 0.0,
        ...     "SCHEDULE_DRIFT": 2.0,
        ... }
        >>> aggregate_drift_scores(scores)
        7.5
        >>> aggregate_drift_scores(scores, weights={"ALLOCATION_DRIFT": 1.0, "REGIME_DRIFT": 1.2})
        7.5
    """
    if not normalized_scores:
        return 0.0

    # Validate all normalized scores are in [0, 10] range and finite
    for taxonomy, score in normalized_scores.items():
        if not isinstance(score, (int, float)) or not float('-inf') < score < float('inf'):
            raise ValueError(
                f"Invalid normalized score for {taxonomy}: {score}. "
                "Must be finite numeric value."
            )
        if not 0.0 <= score <= 10.0:
            raise ValueError(
                f"Normalized score for {taxonomy} out of bounds: {score}. "
                "Must be in [0, 10] range."
            )

    # Default weights prioritize allocation > regime > parameter > schedule
    default_weights = {
        "ALLOCATION_DRIFT": 1.0,
        "REGIME_DRIFT": 0.8,
        "PARAMETER_DRIFT": 0.6,
        "SCHEDULE_DRIFT": 0.5,
    }

    weights = weights or default_weights

    # Validate all weights are finite and non-negative
    for taxonomy, weight in weights.items():
        if not isinstance(weight, (int, float)) or not float('-inf') < weight < float('inf'):
            raise ValueError(
                f"Invalid weight for {taxonomy}: {weight}. "
                "Must be finite numeric value."
            )
        if weight < 0:
            raise ValueError(
                f"Invalid weight for {taxonomy}: {weight}. "
                "Must be non-negative (>= 0)."
            )

    # Compute weighted scores
    weighted_scores = [
        normalized_scores[taxonomy] * weights.get(taxonomy, 1.0)
        for taxonomy in normalized_scores
    ]

    # Return maximum (worst taxonomy dominates)
    aggregated = max(weighted_scores) if weighted_scores else 0.0

    # Clamp to [0, 10] range (in case weights > 1.0 push score above 10)
    return max(0.0, min(aggregated, 10.0))


# Module-level convenience function
def normalize_drift_result(taxonomy: str, drift_score: float, details: dict[str, Any] | None = None) -> float:
    """
    Convenience function to normalize drift score based on taxonomy.

    Args:
        taxonomy: Drift taxonomy name (e.g., "ALLOCATION_DRIFT")
        drift_score: Raw drift score from detector
        details: Optional details dict from DriftResult

    Returns:
        Normalized score in [0, 10] range

    Raises:
        ValueError: If taxonomy unknown

    Example:
        >>> normalize_drift_result("ALLOCATION_DRIFT", 2.0)
        5.0
        >>> normalize_drift_result("REGIME_DRIFT", 5.0, {"state_divergence_steps": 2, "exposure_divergence": 0.2})
        8.0
    """
    normalizers = {
        "ALLOCATION_DRIFT": normalize_allocation_drift,
        "REGIME_DRIFT": normalize_regime_drift,
        "PARAMETER_DRIFT": normalize_parameter_drift,
        "SCHEDULE_DRIFT": normalize_schedule_drift,
    }

    normalizer = normalizers.get(taxonomy)
    if not normalizer:
        raise ValueError(f"Unknown drift taxonomy: {taxonomy}")

    return normalizer(drift_score, details)
