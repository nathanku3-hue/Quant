"""Diagnostic-only economic dynamics operator identification for ECONPHYSICS S0.

This module does not alter M0 or M1.  It reuses the exact admitted PIT
structured snapshots, predecessor-period gate, four temporal folds and
cross-sectional holdout to answer one narrower question: which low-freedom
operator, if any, maps the current economic state into the next PIT transition?

The operator family is fixed and outcome-blind with respect to equity/winner
surfaces:

* LEVEL_STATE_PERSISTENCE: sign(FQ0 - FQ-4) predicts the next delta sign.
* DELTA_PERSISTENCE: sign(FQ0 - FQ-1) predicts the next delta sign.
* DELTA_MEAN_REVERSION: -sign(FQ0 - FQ-1) predicts the next delta sign.
* DELTA2_ACCELERATION: sign((FQ0-FQ-1) - (FQ-1-FQ-2)) predicts next delta.

Inventory is oriented economically by negating inventory/revenue, so a positive
sign means normalization/improvement.  Revenue and operating margin retain
their natural orientation.  No threshold, fitted parameter, winner label,
market data, W6 surface, or selector is available here.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

from research.econphysics_prebreakout_v1.contracts import (
    TEMPORAL_FOLD_COUNT,
    StructuredSnapshot,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.low_snr_m1 import build_low_snr_states
from research.econphysics_prebreakout_v1.shootout_evaluator import (
    DEFAULT_MINIMUM_FOLD_COVERAGE,
    DEFAULT_MINIMUM_FOLD_N,
    _evaluate_model_target,
)
from research.econphysics_prebreakout_v1.structured_state import (
    DEMAND_NODE_ID,
    INVENTORY_NODE_ID,
    MARGIN_NODE_ID,
    build_structured_state,
)
from research.econphysics_prebreakout_v1.transition_evaluator import (
    CORE_TARGETS,
    DEMAND_TARGET_ID,
    INVENTORY_TARGET_ID,
    MARGIN_TARGET_ID,
    TransitionObservation,
    _adjacent_pairs,
    _inventory_normalization_target,
    _operating_margin_target,
    _revenue_target,
    _temporal_fold_map,
)


DYNAMICS_DIAGNOSTIC_SCHEMA = "econphysics_prebreakout_s0_economic_dynamics_diagnostic_v2"
DIAGNOSTIC_ID = "ECONPHYSICS_PREBREAKOUT_S0_ECONOMIC_DYNAMICS_DIAGNOSTIC_v2"
MINIMUM_SUPPORTING_TEMPORAL_FOLDS = 3

LEVEL_STATE_PERSISTENCE = "LEVEL_STATE_PERSISTENCE"
DELTA_PERSISTENCE = "DELTA_PERSISTENCE"
DELTA_MEAN_REVERSION = "DELTA_MEAN_REVERSION"
DELTA2_ACCELERATION = "DELTA2_ACCELERATION"
M0_STATE_MEAN_REVERSION = "M0_STATE_MEAN_REVERSION"
M1_STATE_MEAN_REVERSION = "M1_STATE_MEAN_REVERSION"
PRIMITIVE_OPERATOR_IDS = (
    LEVEL_STATE_PERSISTENCE,
    DELTA_PERSISTENCE,
    DELTA_MEAN_REVERSION,
    DELTA2_ACCELERATION,
)
REPRESENTATION_CONDITIONED_OPERATOR_IDS = (
    M0_STATE_MEAN_REVERSION,
    M1_STATE_MEAN_REVERSION,
)
OPERATOR_IDS = (*PRIMITIVE_OPERATOR_IDS, *REPRESENTATION_CONDITIONED_OPERATOR_IDS)

_TARGET_NODE = {
    INVENTORY_TARGET_ID: INVENTORY_NODE_ID,
    DEMAND_TARGET_ID: DEMAND_NODE_ID,
    MARGIN_TARGET_ID: MARGIN_NODE_ID,
}

_TARGET_ACTUAL: dict[str, Callable[[StructuredSnapshot, StructuredSnapshot], int | None]] = {
    INVENTORY_TARGET_ID: _inventory_normalization_target,
    DEMAND_TARGET_ID: _revenue_target,
    MARGIN_TARGET_ID: _operating_margin_target,
}


def evaluate_economic_dynamics_diagnostic(
    snapshots: Sequence[StructuredSnapshot],
    *,
    predecessor_period_end_by_snapshot: Mapping[tuple[str, str, str], str] | None = None,
    minimum_fold_n: int = DEFAULT_MINIMUM_FOLD_N,
    minimum_fold_coverage: float = DEFAULT_MINIMUM_FOLD_COVERAGE,
) -> dict[str, Any]:
    """Evaluate the fixed low-freedom operator family on the S0 PIT corpus."""

    if not snapshots:
        raise ValueError("econphysics_dynamics_diagnostic_snapshots_required")
    if minimum_fold_n < 1:
        raise ValueError("econphysics_dynamics_diagnostic_minimum_fold_n_positive")
    if not 0.0 < minimum_fold_coverage <= 1.0:
        raise ValueError("econphysics_dynamics_diagnostic_minimum_fold_coverage_range")

    candidate_pairs = _adjacent_pairs(snapshots)
    if predecessor_period_end_by_snapshot is None:
        pairs = candidate_pairs
    else:
        pairs = [
            (left, right)
            for left, right in candidate_pairs
            if predecessor_period_end_by_snapshot.get(_key(right)) == left.fq0_period_end.isoformat()
        ]
    if not pairs:
        raise ValueError("econphysics_dynamics_diagnostic_adjacent_pairs_required")

    feature_dates = sorted({left.as_of_date.isoformat() for left, _ in pairs})
    fold_map = _temporal_fold_map(feature_dates)
    observations: dict[str, dict[str, list[TransitionObservation]]] = {
        target_id: {operator_id: [] for operator_id in OPERATOR_IDS}
        for target_id in CORE_TARGETS
    }
    lag_rows: dict[str, list[TransitionObservation]] = defaultdict(list)

    m0_states = {_key(snapshot): build_structured_state(snapshot) for snapshot in snapshots}
    m1_states = build_low_snr_states(snapshots)

    for left, right in pairs:
        fold = fold_map[left.as_of_date.isoformat()]
        holdout = deterministic_xs_holdout(left.security_id)
        key = _key(left)
        m0 = m0_states[key]
        m1 = m1_states[key]
        m0_predictions = {
            INVENTORY_TARGET_ID: m0.inventory_channel.prediction_direction,
            DEMAND_TARGET_ID: m0.demand_order.prediction_direction,
            MARGIN_TARGET_ID: m0.margin_cash.prediction_direction,
        }
        m1_predictions = {
            INVENTORY_TARGET_ID: m1.inventory_channel.prediction_direction,
            DEMAND_TARGET_ID: m1.demand_order.prediction_direction,
            MARGIN_TARGET_ID: m1.margin_cash.prediction_direction,
        }

        for target_id in CORE_TARGETS:
            actual = _TARGET_ACTUAL[target_id](left, right)
            operator_predictions = _operator_predictions(left, target_id)
            common = {
                "target_id": target_id,
                "node_id": _TARGET_NODE[target_id],
                "security_id": left.security_id,
                "source_entity_id": left.source_entity_id,
                "feature_as_of_date": left.as_of_date.isoformat(),
                "feature_period_end": left.fq0_period_end.isoformat(),
                "target_as_of_date": right.as_of_date.isoformat(),
                "target_period_end": right.fq0_period_end.isoformat(),
                "actual_direction": actual,
                "xs_holdout": holdout,
                "temporal_fold": fold,
            }
            operator_predictions[M0_STATE_MEAN_REVERSION] = _negate_prediction(m0_predictions[target_id])
            operator_predictions[M1_STATE_MEAN_REVERSION] = _negate_prediction(m1_predictions[target_id])
            for operator_id, prediction in operator_predictions.items():
                observations[target_id][operator_id].append(
                    TransitionObservation(prediction_direction=prediction, **common)
                )
            lag_rows[target_id].append(
                TransitionObservation(
                    prediction_direction=operator_predictions[DELTA_PERSISTENCE],
                    **common,
                )
            )

    targets: dict[str, Any] = {}
    for target_id in CORE_TARGETS:
        operator_reports = {
            operator_id: _evaluate_model_target(
                rows,
                minimum_fold_n=minimum_fold_n,
                minimum_fold_coverage=minimum_fold_coverage,
            )
            for operator_id, rows in observations[target_id].items()
        }
        surviving = [
            operator_id
            for operator_id, report in operator_reports.items()
            if int(report["supporting_temporal_fold_count"]) >= MINIMUM_SUPPORTING_TEMPORAL_FOLDS
        ]
        qualifying_counts = [int(report["qualifying_temporal_fold_count"]) for report in operator_reports.values()]
        if surviving:
            routing = "DYNAMICS_SIGNAL_PRESENT"
        elif max(qualifying_counts, default=0) < MINIMUM_SUPPORTING_TEMPORAL_FOLDS:
            routing = "UNOBSERVED"
        else:
            routing = "NO_LOW_FREEDOM_DYNAMICS_SIGNAL"

        targets[target_id] = {
            "node_id": _TARGET_NODE[target_id],
            "operator_reports": operator_reports,
            "surviving_operator_ids": surviving,
            "node_routing": routing,
            "lag1_transition": _lag_transition_report(lag_rows[target_id]),
        }

    surviving_nodes = [
        target_id
        for target_id, report in targets.items()
        if report["node_routing"] == "DYNAMICS_SIGNAL_PRESENT"
    ]
    if surviving_nodes:
        routing = "NODE_SPECIFIC_DYNAMICS_SURVIVORS"
        observable_insufficiency = False
    elif all(report["node_routing"] == "NO_LOW_FREEDOM_DYNAMICS_SIGNAL" for report in targets.values()):
        routing = "OBSERVABLE_INSUFFICIENCY_CANDIDATE"
        observable_insufficiency = True
    else:
        routing = "INSUFFICIENT_COVERAGE_FOR_OBSERVABLE_INSUFFICIENCY"
        observable_insufficiency = False

    return {
        "schema_version": DYNAMICS_DIAGNOSTIC_SCHEMA,
        "diagnostic_id": DIAGNOSTIC_ID,
        "diagnostic_only": True,
        "fixed_operator_family": list(OPERATOR_IDS),
        "primitive_operator_ids": list(PRIMITIVE_OPERATOR_IDS),
        "representation_conditioned_operator_ids": list(REPRESENTATION_CONDITIONED_OPERATOR_IDS),
        "operator_definitions": {
            LEVEL_STATE_PERSISTENCE: "sign(economic_level[FQ0] - economic_level[FQ-4]) -> next_delta_sign",
            DELTA_PERSISTENCE: "sign(economic_level[FQ0] - economic_level[FQ-1]) -> next_delta_sign",
            DELTA_MEAN_REVERSION: "-sign(economic_level[FQ0] - economic_level[FQ-1]) -> next_delta_sign",
            DELTA2_ACCELERATION: "sign((FQ0-FQ-1) - (FQ-1-FQ-2)) in economic orientation -> next_delta_sign",
            M0_STATE_MEAN_REVERSION: "-frozen_M0_state_prediction -> next_delta_sign; M0 bytes unchanged",
            M1_STATE_MEAN_REVERSION: "-frozen_M1_continuous_state_prediction -> next_delta_sign; M1 bytes unchanged",
        },
        "inventory_economic_orientation": "economic_level = -(inventory / revenue); positive delta means normalization",
        "snapshot_count": len(snapshots),
        "candidate_adjacent_transition_pair_count": len(candidate_pairs),
        "adjacent_transition_pair_count": len(pairs),
        "predecessor_period_end_gate_used": predecessor_period_end_by_snapshot is not None,
        "predecessor_gate_dropped_pair_count": len(candidate_pairs) - len(pairs),
        "temporal_fold_count": TEMPORAL_FOLD_COUNT,
        "minimum_supporting_temporal_folds": MINIMUM_SUPPORTING_TEMPORAL_FOLDS,
        "minimum_fold_n": minimum_fold_n,
        "minimum_fold_coverage": minimum_fold_coverage,
        "xs_holdout_rule": "sha256(ECONPHYSICS_S0_XS_HOLDOUT_V1|CIQSEC) mod 5 == 0",
        "xs_holdout_role": "CORROBORATION_NOT_OPERATOR_SELECTION",
        "targets": targets,
        "surviving_target_ids": surviving_nodes,
        "routing": routing,
        "observable_insufficiency_supported": observable_insufficiency,
        "operator_selection_performed": False,
        "fit_or_tuning_performed": False,
        "market_data_access_performed": False,
        "equity_outcome_access_performed": False,
        "winner_selection_access_performed": False,
        "w6_access_performed": False,
        "bootstrap_performed": False,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
    }


def _operator_predictions(snapshot: StructuredSnapshot, target_id: str) -> dict[str, int | None]:
    levels = _economic_levels(snapshot, target_id)
    current = levels.get("FQ0")
    prior = levels.get("FQ-1")
    prior2 = levels.get("FQ-2")
    yoy = levels.get("FQ-4")
    current_delta = _difference(current, prior)
    prior_delta = _difference(prior, prior2)
    return {
        LEVEL_STATE_PERSISTENCE: _sign(_difference(current, yoy)),
        DELTA_PERSISTENCE: _sign(current_delta),
        DELTA_MEAN_REVERSION: _negate_prediction(_sign(current_delta)),
        DELTA2_ACCELERATION: _sign(_difference(current_delta, prior_delta)),
    }


def _economic_levels(snapshot: StructuredSnapshot, target_id: str) -> dict[str, Decimal | None]:
    rows = snapshot.by_period()
    if target_id == DEMAND_TARGET_ID:
        return {period: row.total_revenue for period, row in rows.items()}
    if target_id == MARGIN_TARGET_ID:
        return {
            period: _ratio(row.operating_income, row.total_revenue)
            for period, row in rows.items()
        }
    if target_id == INVENTORY_TARGET_ID:
        return {
            period: (-ratio if ratio is not None else None)
            for period, row in rows.items()
            for ratio in (_ratio(row.inventory, row.total_revenue),)
        }
    raise ValueError(f"econphysics_dynamics_diagnostic_unknown_target:{target_id}")


def _ratio(numerator: Decimal | None, denominator: Decimal | None) -> Decimal | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def _difference(latest: Decimal | None, prior: Decimal | None) -> Decimal | None:
    if latest is None or prior is None:
        return None
    return latest - prior


def _sign(value: Decimal | None) -> int | None:
    if value is None:
        return None
    return 1 if value > 0 else (-1 if value < 0 else 0)


def _negate_prediction(value: int | None) -> int | None:
    return -value if value is not None else None


def _lag_transition_report(rows: Sequence[TransitionObservation]) -> dict[str, Any]:
    development = [row for row in rows if not row.xs_holdout]
    holdout = [row for row in rows if row.xs_holdout]
    return {
        "overall_development": _lag_transition_summary(development),
        "temporal_folds": [
            {"fold": fold + 1, **_lag_transition_summary([row for row in development if row.temporal_fold == fold])}
            for fold in range(TEMPORAL_FOLD_COUNT)
        ],
        "xs_holdout": _lag_transition_summary(holdout),
        "xs_holdout_is_corroboration_not_tuning": True,
    }


def _lag_transition_summary(rows: Sequence[TransitionObservation]) -> dict[str, Any]:
    evaluable = [
        row
        for row in rows
        if row.prediction_direction is not None and row.actual_direction is not None
    ]
    matrix: dict[str, dict[str, int]] = {
        str(left): {str(right): 0 for right in (-1, 0, 1)}
        for left in (-1, 0, 1)
    }
    for row in evaluable:
        matrix[str(int(row.prediction_direction))][str(int(row.actual_direction))] += 1
    nonzero = [
        row for row in evaluable if row.prediction_direction not in (0, None) and row.actual_direction not in (0, None)
    ]
    reversal = sum(int(row.prediction_direction) * int(row.actual_direction) < 0 for row in nonzero)
    persistence = sum(int(row.prediction_direction) == int(row.actual_direction) for row in nonzero)
    return {
        "N": len(evaluable),
        "nonzero_transition_N": len(nonzero),
        "transition_matrix_current_delta_to_next_delta": matrix,
        "reversal_count": reversal,
        "reversal_rate": reversal / len(nonzero) if nonzero else None,
        "persistence_count": persistence,
        "persistence_rate": persistence / len(nonzero) if nonzero else None,
        "current_delta_sign_counts": dict(sorted(Counter(int(row.prediction_direction) for row in evaluable).items())),
        "next_delta_sign_counts": dict(sorted(Counter(int(row.actual_direction) for row in evaluable).items())),
    }


def _key(snapshot: StructuredSnapshot) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()
