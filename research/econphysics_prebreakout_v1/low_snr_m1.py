"""Outcome-blind low-SNR challenger for ECONPHYSICS S0.

M0 remains the frozen sign-only control in ``structured_state.py``.  M1 keeps
continuous magnitude, measures surprise against own PIT history and same-cut
PIT peers, accumulates the most recent legal economic observations, retains
conflict as disagreement rather than deleting the prediction, and exposes one
simple equal-rank causal aggregate.  No winner/equity outcome is imported.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
import math
from statistics import median
from typing import Iterable, Mapping, Sequence

from research.econphysics_prebreakout_v1.contracts import NodeState, NodeTransition, StructuredSnapshot
from research.econphysics_prebreakout_v1.structured_state import (
    DEMAND_NODE_ID,
    INVENTORY_NODE_ID,
    MARGIN_NODE_ID,
)


M1_IMPLEMENTATION_ID = "ECONPHYSICS_PREBREAKOUT_S0_LOW_SNR_M1_v1"
TEMPORAL_ACCUMULATION_OBSERVATIONS = 3
ROBUST_Z_MIN_REFERENCE_COUNT = 2
PEER_Z_MIN_REFERENCE_COUNT = 3

INVENTORY_LEVEL_EVIDENCE = "INVENTORY_LEVEL_CONTINUOUS_V1"
INVENTORY_RATIO_EVIDENCE = "INVENTORY_TO_REVENUE_CONTINUOUS_V1"
REVENUE_EVIDENCE = "REVENUE_CONTINUOUS_V1"
OPERATING_MARGIN_EVIDENCE = "OPERATING_MARGIN_CONTINUOUS_V1"


@dataclass(frozen=True)
class ContinuousEvidence:
    evidence_id: str
    raw_delta: float | None
    log_delta: float | None
    measurement_delta: float | None
    own_history_robust_z: float | None
    pit_peer_residual_z: float | None
    economic_strength: float | None
    internal_disagreement: float
    staleness_days: int
    freshness_score: float
    reliability: float
    positive_when_up: bool
    coverage_reason: str | None = None


@dataclass(frozen=True)
class LowSnrNodeResult:
    node_id: str
    state: NodeState
    transition: NodeTransition
    prediction_direction: int | None
    instantaneous_strength: float | None
    accumulated_strength: float | None
    cross_sectional_rank_strength: float | None
    disagreement: float
    confidence: float
    temporal_observation_count: int
    latest_observation_steps_ago: int | None
    evidence: tuple[ContinuousEvidence, ...]
    reason: str | None = None


@dataclass(frozen=True)
class LowSnrStructuredState:
    security_id: str
    source_entity_id: str
    as_of_date: str
    fq0_period_end: str
    inventory_channel: LowSnrNodeResult
    demand_order: LowSnrNodeResult
    margin_cash: LowSnrNodeResult
    causal_state_strength: float | None
    causal_disagreement: float
    causal_confidence: float
    observed_node_count: int


@dataclass
class _Measurement:
    snapshot_key: tuple[str, str, str]
    evidence_id: str
    positive_when_up: bool
    raw_delta: float | None
    log_delta: float | None
    measurement_delta: float | None
    own_history_robust_z: float | None
    staleness_days: int
    peer_residual_z: float | None = None
    freshness_score: float = 1.0


@dataclass(frozen=True)
class _NodeInstant:
    node_id: str
    strength: float | None
    disagreement: float
    confidence: float
    evidence: tuple[ContinuousEvidence, ...]


def build_low_snr_states(snapshots: Sequence[StructuredSnapshot]) -> dict[tuple[str, str, str], LowSnrStructuredState]:
    """Build M1 states using only information inside/before each PIT snapshot."""

    if not snapshots:
        return {}
    ordered = sorted(snapshots, key=lambda item: (item.as_of_date, item.security_id))
    measurements = _build_measurements(ordered)
    _attach_peer_residuals(measurements)
    _attach_freshness_scores(measurements)

    by_snapshot: dict[tuple[str, str, str], dict[str, ContinuousEvidence]] = {}
    for item in measurements:
        by_snapshot.setdefault(item.snapshot_key, {})[item.evidence_id] = _finalize_measurement(item)

    instants: dict[tuple[str, str, str], dict[str, _NodeInstant]] = {}
    for snapshot in ordered:
        key = _key(snapshot)
        evidence = by_snapshot[key]
        instants[key] = {
            INVENTORY_NODE_ID: _aggregate_instant(
                INVENTORY_NODE_ID,
                (evidence[INVENTORY_LEVEL_EVIDENCE], evidence[INVENTORY_RATIO_EVIDENCE]),
            ),
            DEMAND_NODE_ID: _aggregate_instant(DEMAND_NODE_ID, (evidence[REVENUE_EVIDENCE],)),
            MARGIN_NODE_ID: _aggregate_instant(MARGIN_NODE_ID, (evidence[OPERATING_MARGIN_EVIDENCE],)),
        }

    raw_states: dict[tuple[str, str, str], LowSnrStructuredState] = {}
    by_security: dict[str, list[StructuredSnapshot]] = {}
    for snapshot in ordered:
        by_security.setdefault(snapshot.security_id, []).append(snapshot)
    for security_id, group in by_security.items():
        chronological = sorted(group, key=lambda item: item.as_of_date)
        for index, snapshot in enumerate(chronological):
            key = _key(snapshot)
            window = chronological[max(0, index - TEMPORAL_ACCUMULATION_OBSERVATIONS + 1) : index + 1]
            inventory = _accumulate_node(
                INVENTORY_NODE_ID,
                current=instants[key][INVENTORY_NODE_ID],
                window=[instants[_key(item)][INVENTORY_NODE_ID] for item in window],
            )
            demand = _accumulate_node(
                DEMAND_NODE_ID,
                current=instants[key][DEMAND_NODE_ID],
                window=[instants[_key(item)][DEMAND_NODE_ID] for item in window],
            )
            margin = _accumulate_node(
                MARGIN_NODE_ID,
                current=instants[key][MARGIN_NODE_ID],
                window=[instants[_key(item)][MARGIN_NODE_ID] for item in window],
            )
            raw_states[key] = LowSnrStructuredState(
                security_id=security_id,
                source_entity_id=snapshot.source_entity_id,
                as_of_date=snapshot.as_of_date.isoformat(),
                fq0_period_end=snapshot.fq0_period_end.isoformat(),
                inventory_channel=inventory,
                demand_order=demand,
                margin_cash=margin,
                causal_state_strength=None,
                causal_disagreement=0.0,
                causal_confidence=0.0,
                observed_node_count=0,
            )

    return _attach_cross_sectional_aggregation(raw_states)


def _build_measurements(snapshots: Sequence[StructuredSnapshot]) -> list[_Measurement]:
    output: list[_Measurement] = []
    for snapshot in snapshots:
        key = _key(snapshot)
        staleness = (snapshot.as_of_date - snapshot.fq0_period_end).days
        if staleness < 0:
            raise ValueError("econphysics_m1_negative_staleness")
        output.extend(
            (
                _measurement_from_series(
                    snapshot_key=key,
                    evidence_id=INVENTORY_LEVEL_EVIDENCE,
                    values=_metric_series(snapshot, "inventory"),
                    positive_when_up=False,
                    prefer_log=True,
                    staleness_days=staleness,
                ),
                _measurement_from_series(
                    snapshot_key=key,
                    evidence_id=INVENTORY_RATIO_EVIDENCE,
                    values=_ratio_series(snapshot, "inventory", "total_revenue"),
                    positive_when_up=False,
                    prefer_log=False,
                    staleness_days=staleness,
                ),
                _measurement_from_series(
                    snapshot_key=key,
                    evidence_id=REVENUE_EVIDENCE,
                    values=_metric_series(snapshot, "total_revenue"),
                    positive_when_up=True,
                    prefer_log=True,
                    staleness_days=staleness,
                ),
                _measurement_from_series(
                    snapshot_key=key,
                    evidence_id=OPERATING_MARGIN_EVIDENCE,
                    values=_ratio_series(snapshot, "operating_income", "total_revenue"),
                    positive_when_up=True,
                    prefer_log=False,
                    staleness_days=staleness,
                ),
            )
        )
    return output


def _measurement_from_series(
    *,
    snapshot_key: tuple[str, str, str],
    evidence_id: str,
    values: Mapping[str, Decimal | None],
    positive_when_up: bool,
    prefer_log: bool,
    staleness_days: int,
) -> _Measurement:
    current = _float(values.get("FQ0"))
    prior = _float(values.get("FQ-1"))
    raw_delta = _difference(current, prior)
    log_delta = _log_change(current, prior)
    use_log_scale = bool(prefer_log and log_delta is not None)
    measurement_delta = log_delta if use_log_scale else raw_delta

    historical_changes: list[float] = []
    history_pairs = (("FQ-1", "FQ-2"), ("FQ-2", "FQ-3"), ("FQ-3", "FQ-4"))
    for latest_period, prior_period in history_pairs:
        latest = _float(values.get(latest_period))
        comparison = _float(values.get(prior_period))
        change = _log_change(latest, comparison) if use_log_scale else _difference(latest, comparison)
        if change is not None and math.isfinite(change):
            historical_changes.append(change)
    own_z = _robust_z(measurement_delta, historical_changes, minimum=ROBUST_Z_MIN_REFERENCE_COUNT)
    return _Measurement(
        snapshot_key=snapshot_key,
        evidence_id=evidence_id,
        positive_when_up=positive_when_up,
        raw_delta=raw_delta,
        log_delta=log_delta,
        measurement_delta=measurement_delta,
        own_history_robust_z=own_z,
        staleness_days=staleness_days,
    )


def _attach_peer_residuals(measurements: Sequence[_Measurement]) -> None:
    groups: dict[tuple[str, str], list[_Measurement]] = {}
    for item in measurements:
        groups.setdefault((item.snapshot_key[2], item.evidence_id), []).append(item)
    for group in groups.values():
        reference = [
            float(item.measurement_delta)
            for item in group
            if item.measurement_delta is not None and math.isfinite(item.measurement_delta)
        ]
        for item in group:
            item.peer_residual_z = _robust_z(
                item.measurement_delta,
                reference,
                minimum=PEER_Z_MIN_REFERENCE_COUNT,
            )


def _attach_freshness_scores(measurements: Sequence[_Measurement]) -> None:
    groups: dict[str, list[_Measurement]] = {}
    for item in measurements:
        groups.setdefault(item.snapshot_key[2], []).append(item)
    for group in groups.values():
        by_snapshot: dict[tuple[str, str, str], int] = {}
        for item in group:
            by_snapshot[item.snapshot_key] = item.staleness_days
        ranks = _normalized_average_ranks({key: -float(value) for key, value in by_snapshot.items()})
        if len(set(by_snapshot.values())) == 1:
            ranks = {key: 1.0 for key in by_snapshot}
        else:
            ranks = {key: (value + 1.0) / 2.0 for key, value in ranks.items()}
        for item in group:
            item.freshness_score = ranks[item.snapshot_key]


def _finalize_measurement(item: _Measurement) -> ContinuousEvidence:
    direction = 1.0 if item.positive_when_up else -1.0
    components = [
        direction * value
        for value in (item.own_history_robust_z, item.peer_residual_z)
        if value is not None and math.isfinite(value)
    ]
    strength = sum(components) / len(components) if components else None
    disagreement = _sign_disagreement(components)
    component_coverage = len(components) / 2.0
    reliability = component_coverage * item.freshness_score
    if item.measurement_delta is None:
        reason = "CURRENT_DELTA_UNOBSERVED"
    elif not components:
        reason = "ROBUST_REFERENCE_UNOBSERVED"
    elif len(components) == 1:
        reason = "PARTIAL_ROBUST_REFERENCE"
    else:
        reason = None
    return ContinuousEvidence(
        evidence_id=item.evidence_id,
        raw_delta=item.raw_delta,
        log_delta=item.log_delta,
        measurement_delta=item.measurement_delta,
        own_history_robust_z=item.own_history_robust_z,
        pit_peer_residual_z=item.peer_residual_z,
        economic_strength=strength,
        internal_disagreement=disagreement,
        staleness_days=item.staleness_days,
        freshness_score=item.freshness_score,
        reliability=reliability,
        positive_when_up=item.positive_when_up,
        coverage_reason=reason,
    )


def _aggregate_instant(node_id: str, evidence: Iterable[ContinuousEvidence]) -> _NodeInstant:
    items = tuple(evidence)
    observed = [item for item in items if item.economic_strength is not None]
    if not observed:
        return _NodeInstant(node_id=node_id, strength=None, disagreement=0.0, confidence=0.0, evidence=items)
    weights = [item.reliability for item in observed]
    if sum(weights) > 0:
        strength = sum(float(item.economic_strength) * weight for item, weight in zip(observed, weights)) / sum(weights)
    else:
        strength = sum(float(item.economic_strength) for item in observed) / len(observed)
    cross_sensor = _sign_disagreement([float(item.economic_strength) for item in observed])
    internal = sum(item.internal_disagreement for item in observed) / len(observed)
    disagreement = 1.0 - (1.0 - cross_sensor) * (1.0 - internal)
    reliability = sum(item.reliability for item in observed) / len(items)
    confidence = reliability * (1.0 - disagreement)
    return _NodeInstant(
        node_id=node_id,
        strength=strength,
        disagreement=disagreement,
        confidence=confidence,
        evidence=items,
    )


def _accumulate_node(
    node_id: str,
    *,
    current: _NodeInstant,
    window: Sequence[_NodeInstant],
) -> LowSnrNodeResult:
    observed = [(index, item) for index, item in enumerate(window) if item.strength is not None]
    if not observed:
        return LowSnrNodeResult(
            node_id=node_id,
            state=NodeState.UNOBSERVED,
            transition=NodeTransition.UNOBSERVED,
            prediction_direction=None,
            instantaneous_strength=current.strength,
            accumulated_strength=None,
            cross_sectional_rank_strength=None,
            disagreement=0.0,
            confidence=0.0,
            temporal_observation_count=0,
            latest_observation_steps_ago=None,
            evidence=current.evidence,
            reason="NO_CONTINUOUS_EVIDENCE_IN_TEMPORAL_WINDOW",
        )
    strengths = [float(item.strength) for _, item in observed]
    accumulated = sum(strengths) / len(strengths)
    temporal_disagreement = _sign_disagreement(strengths)
    current_disagreement = current.disagreement if current.strength is not None else 0.0
    disagreement = 1.0 - (1.0 - temporal_disagreement) * (1.0 - current_disagreement)
    base_confidence = sum(item.confidence for _, item in observed) / len(observed)
    confidence = base_confidence * (1.0 - temporal_disagreement)
    prediction = _sign(accumulated)
    if disagreement > 0:
        state = NodeState.MIXED
        reason = "MIXED_EVIDENCE_RETAINED_WITH_CONTINUOUS_STRENGTH"
    else:
        state = _state_from_sign(prediction)
        reason = None
    transition = _transition_from_sign(prediction)
    last_index = max(index for index, _ in observed)
    latest_steps_ago = len(window) - 1 - last_index
    return LowSnrNodeResult(
        node_id=node_id,
        state=state,
        transition=transition,
        prediction_direction=prediction,
        instantaneous_strength=current.strength,
        accumulated_strength=accumulated,
        cross_sectional_rank_strength=None,
        disagreement=disagreement,
        confidence=confidence,
        temporal_observation_count=len(observed),
        latest_observation_steps_ago=latest_steps_ago,
        evidence=current.evidence,
        reason=reason,
    )


def _attach_cross_sectional_aggregation(
    states: Mapping[tuple[str, str, str], LowSnrStructuredState]
) -> dict[tuple[str, str, str], LowSnrStructuredState]:
    by_date: dict[str, list[tuple[str, str, str]]] = {}
    for key, state in states.items():
        by_date.setdefault(state.as_of_date, []).append(key)
    output = dict(states)
    node_attributes = ("inventory_channel", "demand_order", "margin_cash")
    for keys in by_date.values():
        node_ranks: dict[str, dict[tuple[str, str, str], float]] = {}
        for attribute in node_attributes:
            values = {
                key: float(getattr(output[key], attribute).accumulated_strength)
                for key in keys
                if getattr(output[key], attribute).accumulated_strength is not None
            }
            node_ranks[attribute] = _normalized_average_ranks(values)
        for key in keys:
            state = output[key]
            nodes: list[LowSnrNodeResult] = []
            ranks: list[float] = []
            strengths: list[float] = []
            confidences: list[float] = []
            for attribute in node_attributes:
                node = getattr(state, attribute)
                rank = node_ranks[attribute].get(key)
                node = replace(node, cross_sectional_rank_strength=rank)
                nodes.append(node)
                if rank is not None:
                    ranks.append(rank)
                if node.accumulated_strength is not None:
                    strengths.append(float(node.accumulated_strength))
                    confidences.append(node.confidence)
            causal_strength = sum(ranks) / len(ranks) if ranks else None
            causal_disagreement = _sign_disagreement(strengths)
            causal_confidence = (
                (sum(confidences) / len(confidences)) * (1.0 - causal_disagreement)
                if confidences
                else 0.0
            )
            output[key] = replace(
                state,
                inventory_channel=nodes[0],
                demand_order=nodes[1],
                margin_cash=nodes[2],
                causal_state_strength=causal_strength,
                causal_disagreement=causal_disagreement,
                causal_confidence=causal_confidence,
                observed_node_count=len(ranks),
            )
    return output


def _metric_series(snapshot: StructuredSnapshot, metric: str) -> dict[str, Decimal | None]:
    return {period: getattr(row, metric) for period, row in snapshot.by_period().items()}


def _ratio_series(snapshot: StructuredSnapshot, numerator: str, denominator: str) -> dict[str, Decimal | None]:
    output: dict[str, Decimal | None] = {}
    for period, row in snapshot.by_period().items():
        num = getattr(row, numerator)
        den = getattr(row, denominator)
        if row.period_end is None or num is None or den is None or den <= 0:
            output[period] = None
        else:
            output[period] = num / den
    return output


def _robust_z(
    value: float | None,
    reference: Sequence[float],
    *,
    minimum: int,
) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    clean = [float(item) for item in reference if math.isfinite(float(item))]
    if len(clean) < minimum:
        return None
    center = float(median(clean))
    scale = _robust_scale(clean, center=center)
    if scale is None:
        return 0.0 if math.isclose(value, center, rel_tol=0.0, abs_tol=1e-15) else None
    return (value - center) / scale


def _robust_scale(values: Sequence[float], *, center: float) -> float | None:
    deviations = [abs(value - center) for value in values]
    mad = float(median(deviations))
    if mad > 0:
        return 1.4826 * mad
    if len(values) >= 4:
        ordered = sorted(values)
        q25 = _quantile(ordered, 0.25)
        q75 = _quantile(ordered, 0.75)
        iqr_scale = (q75 - q25) / 1.349
        if iqr_scale > 0:
            return iqr_scale
    mean_abs = sum(deviations) / len(deviations)
    if mean_abs > 0:
        return 1.2533141373155 * mean_abs
    return None


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("econphysics_m1_quantile_values_required")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower]) * (1.0 - weight) + float(sorted_values[upper]) * weight


def _normalized_average_ranks(values: Mapping[object, float]) -> dict[object, float]:
    if not values:
        return {}
    if len(values) == 1:
        key = next(iter(values))
        return {key: 0.0}
    ordered = sorted(values.items(), key=lambda item: (item[1], str(item[0])))
    output: dict[object, float] = {}
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and math.isclose(ordered[end][1], ordered[index][1], rel_tol=0.0, abs_tol=1e-15):
            end += 1
        average_position = (index + end - 1) / 2.0
        normalized = 2.0 * average_position / (len(ordered) - 1) - 1.0
        for cursor in range(index, end):
            output[ordered[cursor][0]] = normalized
        index = end
    return output


def _sign_disagreement(values: Sequence[float]) -> float:
    signs = [_sign(value) for value in values if _sign(value) != 0]
    if len(signs) < 2:
        return 0.0
    pairs = 0
    conflicts = 0
    for left_index in range(len(signs)):
        for right_index in range(left_index + 1, len(signs)):
            pairs += 1
            conflicts += int(signs[left_index] != signs[right_index])
    return conflicts / pairs if pairs else 0.0


def _float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _difference(latest: float | None, prior: float | None) -> float | None:
    if latest is None or prior is None:
        return None
    return latest - prior


def _log_change(latest: float | None, prior: float | None) -> float | None:
    if latest is None or prior is None or latest <= 0 or prior <= 0:
        return None
    return math.log(latest / prior)


def _sign(value: float | None) -> int:
    if value is None or not math.isfinite(value):
        return 0
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def _state_from_sign(direction: int) -> NodeState:
    if direction > 0:
        return NodeState.POSITIVE
    if direction < 0:
        return NodeState.NEGATIVE
    return NodeState.NEUTRAL


def _transition_from_sign(direction: int) -> NodeTransition:
    if direction > 0:
        return NodeTransition.IMPROVING
    if direction < 0:
        return NodeTransition.DETERIORATING
    return NodeTransition.STABLE


def _key(snapshot: StructuredSnapshot) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()
