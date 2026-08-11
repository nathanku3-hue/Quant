"""Deterministic S0 evaluator for adjacent point-in-time economic transitions."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence

from research.econphysics_prebreakout_v1.contracts import (
    TEMPORAL_FOLD_COUNT,
    TRANSITION_REPORT_SCHEMA,
    StructuredSnapshot,
    build_structured_snapshots,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.structured_state import (
    DEMAND_NODE_ID,
    INVENTORY_NODE_ID,
    MARGIN_NODE_ID,
    build_structured_state,
)

INVENTORY_TARGET_ID = "NEXT_PIT_INVENTORY_TO_REVENUE_NORMALIZATION_DIRECTION"
DEMAND_TARGET_ID = "NEXT_PIT_REVENUE_DIRECTION"
MARGIN_TARGET_ID = "NEXT_PIT_OPERATING_MARGIN_DIRECTION"
CORE_TARGETS = (INVENTORY_TARGET_ID, DEMAND_TARGET_ID, MARGIN_TARGET_ID)
MAJORITY_TEMPORAL_FOLDS = 3


@dataclass(frozen=True)
class TransitionObservation:
    target_id: str
    node_id: str
    security_id: str
    source_entity_id: str
    feature_as_of_date: str
    feature_period_end: str
    target_as_of_date: str
    target_period_end: str
    prediction_direction: int | None
    actual_direction: int | None
    xs_holdout: bool
    temporal_fold: int


def evaluate_structured_transition_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return evaluate_structured_transitions(build_structured_snapshots(rows))


def evaluate_structured_transitions(snapshots: Sequence[StructuredSnapshot]) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("econphysics_s0_snapshots_required")
    states = {_key(snapshot): build_structured_state(snapshot) for snapshot in snapshots}
    pairs = _adjacent_pairs(snapshots)
    feature_dates = sorted({left.as_of_date.isoformat() for left, _ in pairs})
    fold_map = _temporal_fold_map(feature_dates)
    observations: list[TransitionObservation] = []
    for left, right in pairs:
        state = states[_key(left)]
        fold = fold_map[left.as_of_date.isoformat()]
        holdout = deterministic_xs_holdout(left.security_id)
        targets = (
            (INVENTORY_TARGET_ID, INVENTORY_NODE_ID, state.inventory_channel.prediction_direction, _inventory_normalization_target(left, right)),
            (DEMAND_TARGET_ID, DEMAND_NODE_ID, state.demand_order.prediction_direction, _revenue_target(left, right)),
            (MARGIN_TARGET_ID, MARGIN_NODE_ID, state.margin_cash.prediction_direction, _operating_margin_target(left, right)),
        )
        for target_id, node_id, prediction, actual in targets:
            observations.append(
                TransitionObservation(
                    target_id=target_id,
                    node_id=node_id,
                    security_id=left.security_id,
                    source_entity_id=left.source_entity_id,
                    feature_as_of_date=left.as_of_date.isoformat(),
                    feature_period_end=left.fq0_period_end.isoformat(),
                    target_as_of_date=right.as_of_date.isoformat(),
                    target_period_end=right.fq0_period_end.isoformat(),
                    prediction_direction=prediction,
                    actual_direction=actual,
                    xs_holdout=holdout,
                    temporal_fold=fold,
                )
            )

    by_target: dict[str, list[TransitionObservation]] = defaultdict(list)
    for observation in observations:
        by_target[observation.target_id].append(observation)
    target_reports = {target_id: _evaluate_target(by_target.get(target_id, [])) for target_id in CORE_TARGETS}
    passing = [target_id for target_id, report in target_reports.items() if report["mechanism_status"] == "PASS"]
    return {
        "schema_version": TRANSITION_REPORT_SCHEMA,
        "evaluation_id": "ECONPHYSICS_PREBREAKOUT_S0_STRUCTURED_TRANSITION_PROOF_v1",
        "snapshot_count": len(snapshots),
        "adjacent_transition_pair_count": len(pairs),
        "security_count": len({snapshot.security_id for snapshot in snapshots}),
        "temporal_fold_count": TEMPORAL_FOLD_COUNT,
        "majority_temporal_fold_requirement": MAJORITY_TEMPORAL_FOLDS,
        "xs_holdout_rule": "sha256(ECONPHYSICS_S0_XS_HOLDOUT_V1|CIQSEC) mod 5 == 0",
        "targets": target_reports,
        "passing_core_targets": passing,
        "s0_mechanism_status": "PASS" if passing else "FAIL",
        "pit_violations": 0,
        "fit_or_tuning_performed": False,
        "market_data_access_performed": False,
        "equity_outcome_access_performed": False,
        "w6_access_performed": False,
        "selection_performed": False,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
    }


def _evaluate_target(observations: Sequence[TransitionObservation]) -> dict[str, Any]:
    development = [row for row in observations if not row.xs_holdout]
    holdout = [row for row in observations if row.xs_holdout]
    fold_reports: list[dict[str, Any]] = []
    passing_folds = 0
    informative_folds = 0
    for fold in range(TEMPORAL_FOLD_COUNT):
        report = _summarize([row for row in development if row.temporal_fold == fold])
        report["fold"] = fold + 1
        lift = report["lift_vs_no_information_baseline"]
        association = report["directional_association"]
        informative = report["N"] > 0 and lift is not None
        supports = bool(informative and lift > 1.0 and association is not None and association > 0.0)
        report["supports_mechanism"] = supports
        informative_folds += int(informative)
        passing_folds += int(supports)
        fold_reports.append(report)

    if informative_folds < MAJORITY_TEMPORAL_FOLDS:
        status = "UNOBSERVED"
        reason = "INSUFFICIENT_TEMPORAL_FOLD_COVERAGE_FOR_MAJORITY_TEST"
    elif passing_folds >= MAJORITY_TEMPORAL_FOLDS:
        status = "PASS"
        reason = None
    else:
        status = "FAILED"
        reason = "LIFT_OR_DIRECTION_NOT_STABLE_IN_MAJORITY_OF_TEMPORAL_FOLDS"
    return {
        "overall_development": _summarize(development),
        "temporal_folds": fold_reports,
        "informative_temporal_fold_count": informative_folds,
        "supporting_temporal_fold_count": passing_folds,
        "xs_holdout": _summarize(holdout),
        "mechanism_status": status,
        "mechanism_status_reason": reason,
        "xs_holdout_is_corroboration_not_tuning": True,
    }


def _summarize(observations: Sequence[TransitionObservation]) -> dict[str, Any]:
    pair_count = len(observations)
    target_observed = [row for row in observations if row.actual_direction is not None]
    evaluable = [row for row in target_observed if row.prediction_direction is not None]
    target_counts = Counter(row.actual_direction for row in evaluable)
    n = len(evaluable)
    hit_count = sum(row.prediction_direction == row.actual_direction for row in evaluable)
    contradiction_count = sum(
        int(row.prediction_direction) * int(row.actual_direction) < 0
        for row in evaluable
        if row.prediction_direction is not None and row.actual_direction is not None
    )
    nonzero = [
        row
        for row in evaluable
        if row.prediction_direction not in (None, 0) and row.actual_direction not in (None, 0)
    ]
    association = (
        sum(int(row.prediction_direction) * int(row.actual_direction) for row in nonzero) / len(nonzero)
        if nonzero
        else None
    )
    base_rates = {
        "negative": _ratio(target_counts.get(-1, 0), n),
        "stable": _ratio(target_counts.get(0, 0), n),
        "positive": _ratio(target_counts.get(1, 0), n),
    }
    no_information = max(target_counts.values()) / n if n else None
    hit_rate = hit_count / n if n else None
    lift = hit_rate / no_information if hit_rate is not None and no_information not in (None, 0) else None
    return {
        "pair_count": pair_count,
        "N": n,
        "target_observed_count": len(target_observed),
        "prediction_observed_count": sum(row.prediction_direction is not None for row in observations),
        "base_rate": base_rates,
        "no_information_baseline_hit_rate": no_information,
        "directional_hit_count": hit_count,
        "directional_hit_rate": hit_rate,
        "lift_vs_no_information_baseline": lift,
        "contradiction_count": contradiction_count,
        "contradiction_rate": _ratio(contradiction_count, n),
        "directional_association": association,
        "missing_prediction_count": len(target_observed) - n,
        "missing_target_count": pair_count - len(target_observed),
        "missingness_rate": _ratio(pair_count - n, pair_count),
        "coverage_rate": _ratio(n, pair_count),
    }


def _adjacent_pairs(snapshots: Sequence[StructuredSnapshot]) -> list[tuple[StructuredSnapshot, StructuredSnapshot]]:
    by_security: dict[str, list[StructuredSnapshot]] = defaultdict(list)
    for snapshot in snapshots:
        by_security[snapshot.security_id].append(snapshot)
    pairs: list[tuple[StructuredSnapshot, StructuredSnapshot]] = []
    for security_id, group in sorted(by_security.items()):
        ordered = sorted(group, key=lambda snapshot: snapshot.as_of_date)
        for left, right in zip(ordered, ordered[1:]):
            if right.as_of_date <= left.as_of_date:
                raise ValueError(f"econphysics_s0_nonadvancing_asof:{security_id}")
            if right.available_at <= left.available_at:
                raise ValueError(f"econphysics_s0_nonadvancing_available_at:{security_id}")
            if right.fq0_period_end <= left.fq0_period_end:
                raise ValueError(f"econphysics_s0_nonadvancing_target_period:{security_id}")
            pairs.append((left, right))
    return sorted(pairs, key=lambda pair: (pair[0].as_of_date, pair[0].security_id))


def _temporal_fold_map(feature_dates: Sequence[str]) -> dict[str, int]:
    unique = sorted(set(feature_dates))
    if not unique:
        return {}
    return {
        value: min(TEMPORAL_FOLD_COUNT - 1, (index * TEMPORAL_FOLD_COUNT) // len(unique))
        for index, value in enumerate(unique)
    }


def _inventory_normalization_target(left: StructuredSnapshot, right: StructuredSnapshot) -> int | None:
    current = _fq0_ratio(left, "inventory", "total_revenue")
    following = _fq0_ratio(right, "inventory", "total_revenue")
    raw = _direction(following, current)
    return -raw if raw is not None else None


def _revenue_target(left: StructuredSnapshot, right: StructuredSnapshot) -> int | None:
    return _direction(_fq0_value(right, "total_revenue"), _fq0_value(left, "total_revenue"))


def _operating_margin_target(left: StructuredSnapshot, right: StructuredSnapshot) -> int | None:
    return _direction(
        _fq0_ratio(right, "operating_income", "total_revenue"),
        _fq0_ratio(left, "operating_income", "total_revenue"),
    )


def _fq0_value(snapshot: StructuredSnapshot, metric: str) -> Decimal | None:
    return getattr(snapshot.by_period()["FQ0"], metric)


def _fq0_ratio(snapshot: StructuredSnapshot, numerator: str, denominator: str) -> Decimal | None:
    row = snapshot.by_period()["FQ0"]
    numerator_value = getattr(row, numerator)
    denominator_value = getattr(row, denominator)
    if row.period_end is None or numerator_value is None or denominator_value is None or denominator_value <= 0:
        return None
    return numerator_value / denominator_value


def _direction(latest: Decimal | None, prior: Decimal | None) -> int | None:
    if latest is None or prior is None:
        return None
    delta = latest - prior
    return 1 if delta > 0 else (-1 if delta < 0 else 0)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _key(snapshot: StructuredSnapshot) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()
