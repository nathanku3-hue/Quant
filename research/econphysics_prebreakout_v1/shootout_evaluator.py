"""Side-by-side M0 vs low-SNR M1 economic transition shootout.

This evaluator deliberately does not expose winner/equity labels.  It reuses
the exact S0 adjacent economic targets, temporal folds and deterministic
cross-sectional holdout, then adds only minimum-N/coverage checks and an
explicit PARTIAL_SUPPORT state.  There is no bootstrap and no "any target
passes => overall PASS" rule.
"""

from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Mapping, Sequence

from research.econphysics_prebreakout_v1.contracts import (
    TEMPORAL_FOLD_COUNT,
    StructuredSnapshot,
    build_structured_snapshots,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.low_snr_m1 import M1_IMPLEMENTATION_ID, build_low_snr_states
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
    _summarize,
    _temporal_fold_map,
)


SHOOTOUT_SCHEMA = "econphysics_prebreakout_s0_m0_m1_shootout_v2"
M0_IMPLEMENTATION_ID = "ECONPHYSICS_PREBREAKOUT_S0_STRUCTURED_STATE_v1"
MINIMUM_INFORMATIVE_TEMPORAL_FOLDS = 3
DEFAULT_MINIMUM_FOLD_N = 30
DEFAULT_MINIMUM_FOLD_COVERAGE = 0.20


def evaluate_m0_m1_shootout_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    minimum_fold_n: int = DEFAULT_MINIMUM_FOLD_N,
    minimum_fold_coverage: float = DEFAULT_MINIMUM_FOLD_COVERAGE,
    predecessor_period_end_by_snapshot: Mapping[tuple[str, str, str], str] | None = None,
) -> dict[str, Any]:
    return evaluate_m0_m1_shootout(
        build_structured_snapshots(rows),
        minimum_fold_n=minimum_fold_n,
        minimum_fold_coverage=minimum_fold_coverage,
        predecessor_period_end_by_snapshot=predecessor_period_end_by_snapshot,
    )


def evaluate_m0_m1_shootout(
    snapshots: Sequence[StructuredSnapshot],
    *,
    minimum_fold_n: int = DEFAULT_MINIMUM_FOLD_N,
    minimum_fold_coverage: float = DEFAULT_MINIMUM_FOLD_COVERAGE,
    predecessor_period_end_by_snapshot: Mapping[tuple[str, str, str], str] | None = None,
) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("econphysics_s0_shootout_snapshots_required")
    if minimum_fold_n < 1:
        raise ValueError("econphysics_s0_shootout_minimum_fold_n_positive")
    if not 0.0 < minimum_fold_coverage <= 1.0:
        raise ValueError("econphysics_s0_shootout_minimum_fold_coverage_range")

    m0_states = {_key(snapshot): build_structured_state(snapshot) for snapshot in snapshots}
    m1_states = build_low_snr_states(snapshots)
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
        raise ValueError("econphysics_s0_shootout_adjacent_pairs_required")
    feature_dates = sorted({left.as_of_date.isoformat() for left, _ in pairs})
    fold_map = _temporal_fold_map(feature_dates)

    m0_observations: dict[str, list[TransitionObservation]] = defaultdict(list)
    m1_observations: dict[str, list[TransitionObservation]] = defaultdict(list)
    for left, right in pairs:
        key = _key(left)
        m0 = m0_states[key]
        m1 = m1_states[key]
        fold = fold_map[left.as_of_date.isoformat()]
        holdout = deterministic_xs_holdout(left.security_id)
        actuals = {
            INVENTORY_TARGET_ID: _inventory_normalization_target(left, right),
            DEMAND_TARGET_ID: _revenue_target(left, right),
            MARGIN_TARGET_ID: _operating_margin_target(left, right),
        }
        m0_predictions = {
            INVENTORY_TARGET_ID: (INVENTORY_NODE_ID, m0.inventory_channel.prediction_direction),
            DEMAND_TARGET_ID: (DEMAND_NODE_ID, m0.demand_order.prediction_direction),
            MARGIN_TARGET_ID: (MARGIN_NODE_ID, m0.margin_cash.prediction_direction),
        }
        m1_predictions = {
            INVENTORY_TARGET_ID: (INVENTORY_NODE_ID, m1.inventory_channel.prediction_direction),
            DEMAND_TARGET_ID: (DEMAND_NODE_ID, m1.demand_order.prediction_direction),
            MARGIN_TARGET_ID: (MARGIN_NODE_ID, m1.margin_cash.prediction_direction),
        }
        for target_id in CORE_TARGETS:
            m0_node, m0_prediction = m0_predictions[target_id]
            m1_node, m1_prediction = m1_predictions[target_id]
            common = {
                "target_id": target_id,
                "security_id": left.security_id,
                "source_entity_id": left.source_entity_id,
                "feature_as_of_date": left.as_of_date.isoformat(),
                "feature_period_end": left.fq0_period_end.isoformat(),
                "target_as_of_date": right.as_of_date.isoformat(),
                "target_period_end": right.fq0_period_end.isoformat(),
                "actual_direction": actuals[target_id],
                "xs_holdout": holdout,
                "temporal_fold": fold,
            }
            m0_observations[target_id].append(
                TransitionObservation(node_id=m0_node, prediction_direction=m0_prediction, **common)
            )
            m1_observations[target_id].append(
                TransitionObservation(node_id=m1_node, prediction_direction=m1_prediction, **common)
            )

    target_reports: dict[str, Any] = {}
    for target_id in CORE_TARGETS:
        m0_report = _evaluate_model_target(
            m0_observations[target_id],
            minimum_fold_n=minimum_fold_n,
            minimum_fold_coverage=minimum_fold_coverage,
        )
        m1_report = _evaluate_model_target(
            m1_observations[target_id],
            minimum_fold_n=minimum_fold_n,
            minimum_fold_coverage=minimum_fold_coverage,
        )
        target_reports[target_id] = {
            "node_id": m0_observations[target_id][0].node_id if m0_observations[target_id] else None,
            "m0": m0_report,
            "m1": m1_report,
            "comparison": _compare_target(m0_report, m1_report),
        }

    integrated_status = _integrated_status(target_reports)
    causal_aggregate_observed = [
        state for state in m1_states.values() if state.causal_state_strength is not None
    ]
    return {
        "schema_version": SHOOTOUT_SCHEMA,
        "evaluation_id": "ECONPHYSICS_PREBREAKOUT_S0_M0_VS_LOW_SNR_M1_v2",
        "control_implementation_id": M0_IMPLEMENTATION_ID,
        "challenger_implementation_id": M1_IMPLEMENTATION_ID,
        "snapshot_count": len(snapshots),
        "candidate_adjacent_transition_pair_count": len(candidate_pairs),
        "adjacent_transition_pair_count": len(pairs),
        "predecessor_period_end_gate_used": predecessor_period_end_by_snapshot is not None,
        "predecessor_gate_dropped_pair_count": len(candidate_pairs) - len(pairs),
        "security_count": len({snapshot.security_id for snapshot in snapshots}),
        "temporal_fold_count": TEMPORAL_FOLD_COUNT,
        "minimum_informative_temporal_folds": MINIMUM_INFORMATIVE_TEMPORAL_FOLDS,
        "minimum_fold_n": minimum_fold_n,
        "minimum_fold_coverage": minimum_fold_coverage,
        "xs_holdout_rule": "sha256(ECONPHYSICS_S0_XS_HOLDOUT_V1|CIQSEC) mod 5 == 0",
        "targets": target_reports,
        "integrated_state_transition_status": integrated_status,
        "integrated_pass_boolean": None,
        "m1_causal_aggregate_observed_snapshot_count": len(causal_aggregate_observed),
        "m1_representation": {
            "continuous_measurement": True,
            "own_history_robust_z": True,
            "pit_peer_residual": True,
            "temporal_accumulation_observations": 3,
            "mixed_evidence_zeroed": False,
            "simple_cross_sectional_aggregation": "EQUAL_MEAN_OF_MONOTONIC_NODE_RANKS",
            "lexicographic_selection_used": False,
            "fit_or_tuning_performed": False,
        },
        "pit_violations": 0,
        "market_data_access_performed": False,
        "equity_outcome_access_performed": False,
        "winner_selection_access_performed": False,
        "w6_access_performed": False,
        "bootstrap_performed": False,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
    }


def _evaluate_model_target(
    observations: Sequence[TransitionObservation],
    *,
    minimum_fold_n: int,
    minimum_fold_coverage: float,
) -> dict[str, Any]:
    development = [row for row in observations if not row.xs_holdout]
    holdout = [row for row in observations if row.xs_holdout]
    folds: list[dict[str, Any]] = []
    qualifying = 0
    supporting = 0
    for fold in range(TEMPORAL_FOLD_COUNT):
        summary = _summarize([row for row in development if row.temporal_fold == fold])
        coverage = summary["coverage_rate"]
        meets_minimum = bool(
            summary["N"] >= minimum_fold_n
            and coverage is not None
            and coverage >= minimum_fold_coverage
        )
        lift = summary["lift_vs_no_information_baseline"]
        association = summary["directional_association"]
        supports = bool(
            meets_minimum
            and lift is not None
            and lift > 1.0
            and association is not None
            and association > 0.0
        )
        summary["fold"] = fold + 1
        summary["meets_minimum_n_and_coverage"] = meets_minimum
        summary["supports_mechanism"] = supports
        qualifying += int(meets_minimum)
        supporting += int(supports)
        folds.append(summary)

    if qualifying < MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        status = "UNOBSERVED"
        reason = "INSUFFICIENT_MINIMUM_N_OR_COVERAGE_ACROSS_TEMPORAL_FOLDS"
    elif supporting >= MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        status = "PASS"
        reason = None
    elif supporting > 0:
        status = "PARTIAL_SUPPORT"
        reason = "POSITIVE_MECHANISM_EVIDENCE_NOT_STABLE_IN_THREE_OF_FOUR_FOLDS"
    else:
        status = "FAILED"
        reason = "NO_POSITIVE_LIFT_WITH_POSITIVE_DIRECTIONAL_ASSOCIATION_IN_QUALIFYING_FOLDS"
    return {
        "overall_development": _summarize(development),
        "temporal_folds": folds,
        "qualifying_temporal_fold_count": qualifying,
        "supporting_temporal_fold_count": supporting,
        "xs_holdout": _summarize(holdout),
        "mechanism_status": status,
        "mechanism_status_reason": reason,
        "xs_holdout_is_corroboration_not_tuning": True,
    }


def _compare_target(m0: Mapping[str, Any], m1: Mapping[str, Any]) -> dict[str, Any]:
    fold_rows: list[dict[str, Any]] = []
    m1_better = 0
    m0_better = 0
    comparable = 0
    lift_deltas: list[float] = []
    for m0_fold, m1_fold in zip(m0["temporal_folds"], m1["temporal_folds"]):
        can_compare = bool(
            m0_fold["meets_minimum_n_and_coverage"] and m1_fold["meets_minimum_n_and_coverage"]
        )
        m0_lift = m0_fold["lift_vs_no_information_baseline"]
        m1_lift = m1_fold["lift_vs_no_information_baseline"]
        lift_delta = (
            float(m1_lift) - float(m0_lift)
            if can_compare and m0_lift is not None and m1_lift is not None
            else None
        )
        m1_assoc = m1_fold["directional_association"]
        m0_assoc = m0_fold["directional_association"]
        m1_supports = bool(m1_fold["supports_mechanism"])
        m0_supports = bool(m0_fold["supports_mechanism"])
        # Relative improvement is not support if the challenger is still below
        # the no-information baseline or directionally wrong.  A fold win must
        # first satisfy the same absolute mechanism condition used by the
        # target evaluator; only then do we compare M1 against M0.
        m1_wins = bool(
            can_compare
            and m1_supports
            and (not m0_supports or (lift_delta is not None and lift_delta > 0.0))
        )
        m0_wins = bool(
            can_compare
            and m0_supports
            and (not m1_supports or (lift_delta is not None and lift_delta < 0.0))
        )
        comparable += int(can_compare and lift_delta is not None)
        m1_better += int(m1_wins)
        m0_better += int(m0_wins)
        if lift_delta is not None:
            lift_deltas.append(lift_delta)
        fold_rows.append(
            {
                "fold": m0_fold["fold"],
                "comparable": can_compare and lift_delta is not None,
                "m0_N": m0_fold["N"],
                "m1_N": m1_fold["N"],
                "m0_coverage": m0_fold["coverage_rate"],
                "m1_coverage": m1_fold["coverage_rate"],
                "m0_lift": m0_lift,
                "m1_lift": m1_lift,
                "lift_delta_m1_minus_m0": lift_delta,
                "m0_directional_association": m0_assoc,
                "m1_directional_association": m1_assoc,
                "m0_supports_mechanism": m0_supports,
                "m1_supports_mechanism": m1_supports,
                "m1_better": m1_wins,
                "m0_better": m0_wins,
            }
        )

    median_delta = median(lift_deltas) if lift_deltas else None
    if comparable < MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        status = "INSUFFICIENT_COVERAGE"
    elif m1_better >= MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        status = "M1_STABLE_LIFT"
    elif m0_better >= MINIMUM_INFORMATIVE_TEMPORAL_FOLDS:
        status = "M0_STABLE_LIFT"
    elif m1_better > 0 and m1_better > m0_better:
        status = "PARTIAL_SUPPORT"
    else:
        status = "NO_CLEAR_M1_LIFT"
    return {
        "status": status,
        "comparable_temporal_fold_count": comparable,
        "m1_better_fold_count": m1_better,
        "m0_better_fold_count": m0_better,
        "median_lift_delta_m1_minus_m0": median_delta,
        "temporal_folds": fold_rows,
    }


def _integrated_status(target_reports: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = [str(report["comparison"]["status"]) for report in target_reports.values()]
    comparable = [status for status in statuses if status != "INSUFFICIENT_COVERAGE"]
    if len(comparable) < 2:
        return "INSUFFICIENT_COVERAGE"
    m1_wins = statuses.count("M1_STABLE_LIFT")
    m0_wins = statuses.count("M0_STABLE_LIFT")
    partial = statuses.count("PARTIAL_SUPPORT")
    if m1_wins >= 2 and m0_wins == 0:
        return "M1_STABLE_EXTRACTION_LIFT"
    if m1_wins >= 1 or partial >= 1:
        return "PARTIAL_SUPPORT"
    return "NO_EXTRACTION_LIFT"


def _key(snapshot: StructuredSnapshot) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()
