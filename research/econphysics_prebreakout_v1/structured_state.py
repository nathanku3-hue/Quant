"""Deterministic structured economic-state construction for S0.

No fitted weights or thresholds are present.  The only transforms are the
frozen latest-vs-prior and year-over-year directions plus two explicitly named
same-period ratios whose unit/period compatibility is mechanically checked.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from research.econphysics_prebreakout_v1.contracts import (
    NodeState,
    NodeTransition,
    StructuredSnapshot,
)


INVENTORY_NODE_ID = "INVENTORY_CHANNEL_STATE"
DEMAND_NODE_ID = "DEMAND_ORDER_STATE"
SUPPLY_NODE_ID = "SUPPLY_CAPACITY_STATE"
MARGIN_NODE_ID = "MARGIN_CASH_STATE"


@dataclass(frozen=True)
class DirectionalEvidence:
    evidence_id: str
    latest_vs_prior: int | None
    yoy_direction: int | None
    positive_when_up: bool
    coverage_reason: str | None = None


@dataclass(frozen=True)
class NodeResult:
    node_id: str
    state: NodeState
    transition: NodeTransition
    prediction_direction: int | None
    evidence: tuple[DirectionalEvidence, ...]
    reason: str | None = None


@dataclass(frozen=True)
class StructuredState:
    security_id: str
    source_entity_id: str
    as_of_date: str
    fq0_period_end: str
    inventory_channel: NodeResult
    demand_order: NodeResult
    supply_capacity: NodeResult
    margin_cash: NodeResult
    capex_cycle_evidence: DirectionalEvidence


def build_structured_state(snapshot: StructuredSnapshot) -> StructuredState:
    inventory_level = directional_evidence(
        snapshot,
        evidence_id="INVENTORY_LEVEL_DIRECTION_V1",
        metric="inventory",
        positive_when_up=False,
    )
    inventory_ratio = ratio_directional_evidence(
        snapshot,
        evidence_id="INVENTORY_TO_REVENUE_RATIO_DIRECTION_V1",
        numerator="inventory",
        denominator="total_revenue",
        positive_when_up=False,
    )
    inventory = aggregate_evidence(INVENTORY_NODE_ID, (inventory_level, inventory_ratio))

    revenue = directional_evidence(
        snapshot,
        evidence_id="REVENUE_DIRECTION_V1",
        metric="total_revenue",
        positive_when_up=True,
    )
    demand = aggregate_evidence(DEMAND_NODE_ID, (revenue,))

    operating_margin = ratio_directional_evidence(
        snapshot,
        evidence_id="OPERATING_MARGIN_DIRECTION_V1",
        numerator="operating_income",
        denominator="total_revenue",
        positive_when_up=True,
    )
    margin = aggregate_evidence(MARGIN_NODE_ID, (operating_margin,))

    capex = directional_evidence(
        snapshot,
        evidence_id="CAPEX_CYCLE_EVIDENCE_V1",
        metric="capex",
        positive_when_up=True,
    )
    supply = NodeResult(
        node_id=SUPPLY_NODE_ID,
        state=NodeState.UNOBSERVED,
        transition=NodeTransition.UNOBSERVED,
        prediction_direction=None,
        evidence=(capex,),
        reason="CAPEX_IS_CYCLE_EVIDENCE_NOT_CAPACITY_STATE",
    )

    return StructuredState(
        security_id=snapshot.security_id,
        source_entity_id=snapshot.source_entity_id,
        as_of_date=snapshot.as_of_date.isoformat(),
        fq0_period_end=snapshot.fq0_period_end.isoformat(),
        inventory_channel=inventory,
        demand_order=demand,
        supply_capacity=supply,
        margin_cash=margin,
        capex_cycle_evidence=capex,
    )


def directional_evidence(
    snapshot: StructuredSnapshot,
    *,
    evidence_id: str,
    metric: str,
    positive_when_up: bool,
) -> DirectionalEvidence:
    values = _metric_series(snapshot, metric)
    latest = values.get("FQ0")
    prior = values.get("FQ-1")
    yoy = values.get("FQ-4")
    latest_vs_prior = _direction(latest, prior)
    yoy_direction = _direction(latest, yoy)
    if latest is None:
        reason = "LATEST_UNOBSERVED"
    elif latest_vs_prior is None and yoy_direction is None:
        reason = "PRIOR_AND_YOY_UNOBSERVED"
    elif latest_vs_prior is None:
        reason = "PRIOR_UNOBSERVED"
    elif yoy_direction is None:
        reason = "YOY_UNOBSERVED"
    else:
        reason = None
    return DirectionalEvidence(
        evidence_id=evidence_id,
        latest_vs_prior=latest_vs_prior,
        yoy_direction=yoy_direction,
        positive_when_up=positive_when_up,
        coverage_reason=reason,
    )


def ratio_directional_evidence(
    snapshot: StructuredSnapshot,
    *,
    evidence_id: str,
    numerator: str,
    denominator: str,
    positive_when_up: bool,
) -> DirectionalEvidence:
    ratios: dict[str, Decimal | None] = {}
    rows = snapshot.by_period()
    for period, row in rows.items():
        numerator_value = getattr(row, numerator)
        denominator_value = getattr(row, denominator)
        # Both values live on the same validated CIQ quarter row and share the
        # frozen USD-thousands unit.  A nonpositive denominator has no lawful
        # ratio interpretation for S0 and remains unobserved.
        if (
            row.period_end is None
            or numerator_value is None
            or denominator_value is None
            or denominator_value <= 0
        ):
            ratios[period] = None
        else:
            ratios[period] = numerator_value / denominator_value
    latest = ratios.get("FQ0")
    prior = ratios.get("FQ-1")
    yoy = ratios.get("FQ-4")
    latest_vs_prior = _direction(latest, prior)
    yoy_direction = _direction(latest, yoy)
    if latest is None:
        reason = "LATEST_RATIO_UNOBSERVED_OR_DENOMINATOR_NONPOSITIVE"
    elif latest_vs_prior is None and yoy_direction is None:
        reason = "PRIOR_AND_YOY_RATIO_UNOBSERVED"
    elif latest_vs_prior is None:
        reason = "PRIOR_RATIO_UNOBSERVED"
    elif yoy_direction is None:
        reason = "YOY_RATIO_UNOBSERVED"
    else:
        reason = None
    return DirectionalEvidence(
        evidence_id=evidence_id,
        latest_vs_prior=latest_vs_prior,
        yoy_direction=yoy_direction,
        positive_when_up=positive_when_up,
        coverage_reason=reason,
    )


def aggregate_evidence(node_id: str, evidence: Iterable[DirectionalEvidence]) -> NodeResult:
    items = tuple(evidence)
    classified = [_classify(item) for item in items]
    observed = [item for item in classified if item[0] not in {NodeState.UNOBSERVED, NodeState.NOT_APPLICABLE}]
    if not observed:
        return NodeResult(
            node_id=node_id,
            state=NodeState.UNOBSERVED,
            transition=NodeTransition.UNOBSERVED,
            prediction_direction=None,
            evidence=items,
            reason="NO_LAWFUL_DIRECTIONAL_EVIDENCE",
        )
    nonneutral = {state for state, _, _ in observed if state in {NodeState.POSITIVE, NodeState.NEGATIVE}}
    if nonneutral == {NodeState.POSITIVE, NodeState.NEGATIVE}:
        return NodeResult(
            node_id=node_id,
            state=NodeState.MIXED,
            transition=NodeTransition.UNOBSERVED,
            prediction_direction=None,
            evidence=items,
            reason="MATERIAL_DIRECTIONAL_CONFLICT",
        )
    predictions = {direction for _, _, direction in observed if direction is not None}
    if 1 in predictions and -1 in predictions:
        return NodeResult(
            node_id=node_id,
            state=NodeState.MIXED,
            transition=NodeTransition.UNOBSERVED,
            prediction_direction=None,
            evidence=items,
            reason="MATERIAL_TRANSITION_CONFLICT",
        )
    preferred = _preferred_classification(observed)
    return NodeResult(
        node_id=node_id,
        state=preferred[0],
        transition=preferred[1],
        prediction_direction=preferred[2],
        evidence=items,
        reason=None,
    )


def _preferred_classification(
    observed: list[tuple[NodeState, NodeTransition, int | None]],
) -> tuple[NodeState, NodeTransition, int | None]:
    priority = {
        NodeTransition.INFLECTING_POSITIVE: 5,
        NodeTransition.INFLECTING_NEGATIVE: 5,
        NodeTransition.IMPROVING: 4,
        NodeTransition.DETERIORATING: 4,
        NodeTransition.STABLE: 3,
        NodeTransition.UNOBSERVED: 1,
        NodeTransition.NOT_APPLICABLE: 0,
    }
    return max(observed, key=lambda item: priority[item[1]])


def _classify(evidence: DirectionalEvidence) -> tuple[NodeState, NodeTransition, int | None]:
    lp = _economic_sign(evidence.latest_vs_prior, positive_when_up=evidence.positive_when_up)
    yoy = _economic_sign(evidence.yoy_direction, positive_when_up=evidence.positive_when_up)
    if lp is None and yoy is None:
        return NodeState.UNOBSERVED, NodeTransition.UNOBSERVED, None
    if lp is None:
        state = _state_from_sign(yoy)
        return state, NodeTransition.UNOBSERVED, None
    if yoy is None:
        return _state_from_sign(lp), _transition_from_sign(lp), lp
    if lp > 0 and yoy <= 0:
        return NodeState.POSITIVE, NodeTransition.INFLECTING_POSITIVE, 1
    if lp < 0 and yoy >= 0:
        return NodeState.NEGATIVE, NodeTransition.INFLECTING_NEGATIVE, -1
    if lp > 0 and yoy > 0:
        return NodeState.POSITIVE, NodeTransition.IMPROVING, 1
    if lp < 0 and yoy < 0:
        return NodeState.NEGATIVE, NodeTransition.DETERIORATING, -1
    if lp == 0 and yoy == 0:
        return NodeState.NEUTRAL, NodeTransition.STABLE, 0
    # Current-quarter direction is flat while the YoY sign remains coherent;
    # state carries the long comparison but no change-direction forecast is
    # invented from a flat latest transition.
    return _state_from_sign(yoy), NodeTransition.STABLE, 0


def _metric_series(snapshot: StructuredSnapshot, metric: str) -> dict[str, Decimal | None]:
    if metric not in {"total_revenue", "inventory", "operating_income", "capex"}:
        raise ValueError(f"econphysics_s0_unknown_metric:{metric}")
    return {period: getattr(row, metric) for period, row in snapshot.by_period().items()}


def _direction(latest: Decimal | None, comparison: Decimal | None) -> int | None:
    if latest is None or comparison is None:
        return None
    delta = latest - comparison
    return 1 if delta > 0 else (-1 if delta < 0 else 0)


def _economic_sign(direction: int | None, *, positive_when_up: bool) -> int | None:
    if direction is None:
        return None
    return direction if positive_when_up else -direction


def _state_from_sign(direction: int | None) -> NodeState:
    if direction is None:
        return NodeState.UNOBSERVED
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
