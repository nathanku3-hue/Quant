"""Deterministic untouched-lockbox evaluator for PREBREAKOUT research.

The evaluator consumes only immutable normalized prediction rows plus explicit
post-freeze label-open records.  It has no provider, discovery-outcome, model,
training, refit, or prediction-writing capability.
"""

from __future__ import annotations

from collections import defaultdict
import math
import statistics
from typing import Any, Iterable, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.prebreakout_untouched_evaluator_v1.contracts import (
    EVALUATION_REPORT_SCHEMA,
    EVALUATOR_ID,
    UntouchedEvaluationContractError,
    validate_label_rows,
    validate_prediction_rows,
    validate_utility_rows,
    verify_evaluation_contract,
    verify_label_open_record,
    verify_prediction_freeze_record,
)


def evaluate_untouched_lockboxes(
    *,
    contract: Mapping[str, Any],
    prediction_rows: Sequence[Mapping[str, Any]],
    label_rows: Sequence[Mapping[str, Any]],
    utility_rows: Sequence[Mapping[str, Any]],
    prediction_freeze_records: Sequence[Mapping[str, Any]],
    label_open_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate one or more preregistered untouched lockboxes, fail closed.

    Every lockbox must have exactly one prediction-freeze record and one later
    label-open record.  Prediction and label rows must form an exact date-local
    listing-identity join; no row is silently dropped from the denominator.
    """

    verify_evaluation_contract(contract)
    predictions = validate_prediction_rows(prediction_rows, contract=contract)
    labels = validate_label_rows(label_rows, contract=contract)
    utilities = validate_utility_rows(utility_rows, contract=contract)
    lockbox_ids = tuple(str(value) for value in contract["lockbox_ids"])

    freezes = _records_by_lockbox(
        prediction_freeze_records,
        lockbox_ids=lockbox_ids,
        record_name="prediction_freeze",
    )
    opens = _records_by_lockbox(
        label_open_records,
        lockbox_ids=lockbox_ids,
        record_name="label_open",
    )

    for lockbox_id in lockbox_ids:
        lockbox_predictions = [row for row in predictions if row["lockbox_id"] == lockbox_id]
        lockbox_labels = [row for row in labels if row["lockbox_id"] == lockbox_id]
        lockbox_utilities = [row for row in utilities if row["lockbox_id"] == lockbox_id]
        if not lockbox_predictions or not lockbox_labels or not lockbox_utilities:
            raise UntouchedEvaluationContractError("untouched_lockbox_rows_missing")
        verify_prediction_freeze_record(
            freezes[lockbox_id],
            contract=contract,
            prediction_rows=lockbox_predictions,
        )
        verify_label_open_record(
            opens[lockbox_id],
            contract=contract,
            prediction_freeze_record=freezes[lockbox_id],
            label_rows=lockbox_labels,
            utility_rows=lockbox_utilities,
        )

    joined = _exact_join(predictions, labels)
    episodes = _build_episode_diagnostics(
        joined,
        min_lead_sessions=int(contract["min_legitimate_lead_sessions"]),
    )
    weighted_rows = [row for row in joined if row["statistical_weight"] == 1]
    zero_weight_rows = [row for row in joined if row["statistical_weight"] == 0]
    weighted_episodes = [episode for episode in episodes if episode["statistical_weight"] == 1]
    zero_weight_episodes = [episode for episode in episodes if episode["statistical_weight"] == 0]
    if not weighted_rows:
        raise UntouchedEvaluationContractError("untouched_no_statistical_rows_after_preregistered_zero_weight")

    top_k, selected_keys = _top_k_metrics(
        weighted_rows,
        k_values=tuple(int(value) for value in contract["k_values"]),
    )
    average_precision = _average_precision(weighted_rows)
    detection = _detection_metrics(weighted_rows, weighted_episodes)
    wealth = _right_tail_wealth_metrics(
        weighted_episodes,
        weighted_rows,
        selected_keys=selected_keys,
        min_lead_sessions=int(contract["min_legitimate_lead_sessions"]),
    )
    utility = _incremental_utility_metrics(utilities, lockbox_ids=lockbox_ids)

    lockbox_summary = []
    for lockbox_id in lockbox_ids:
        lockbox_summary.append(
            {
                "lockbox_id": lockbox_id,
                "prediction_row_count": sum(row["lockbox_id"] == lockbox_id for row in predictions),
                "label_row_count": sum(row["lockbox_id"] == lockbox_id for row in labels),
                "utility_row_count": sum(row["lockbox_id"] == lockbox_id for row in utilities),
                "prediction_freeze_record_sha256": freezes[lockbox_id]["freeze_record_sha256"],
                "prediction_snapshot_sha256": freezes[lockbox_id]["prediction_snapshot_sha256"],
                "prediction_sealed_at": freezes[lockbox_id]["sealed_at"],
                "label_open_record_sha256": opens[lockbox_id]["label_open_record_sha256"],
                "label_snapshot_sha256": opens[lockbox_id]["label_snapshot_sha256"],
                "label_opened_at": opens[lockbox_id]["opened_at"],
            }
        )

    body = {
        "schema_version": EVALUATION_REPORT_SCHEMA,
        "evaluator_id": EVALUATOR_ID,
        "family_id": contract["family_id"],
        "implementation_id": contract["implementation_id"],
        "primary_label_spec_id": contract["primary_label_spec_id"],
        "contract_sha256": contract["contract_sha256"],
        "lockbox_count": len(lockbox_ids),
        "lockbox_ids": list(lockbox_ids),
        "lockboxes": lockbox_summary,
        "raw_security_observation_count": len(joined),
        "statistical_security_observation_count": len(weighted_rows),
        "zero_weight_security_observation_count": len(zero_weight_rows),
        "effective_episode_count": len(weighted_episodes),
        "zero_weight_effective_episode_count": len(zero_weight_episodes),
        "decision_date_count": len(
            {(row["lockbox_id"], row["decision_session_date"]) for row in weighted_rows}
        ),
        "security_listing_count": len(
            {(row["security_id"], row["trading_item_id"]) for row in weighted_rows}
        ),
        "precision_recall_lift_at_k": top_k,
        "pr_auc_average_precision": _number_or_none(average_precision),
        "detection_and_false_winners": detection,
        "right_tail_wealth_capture": wealth,
        "i_vs_i_plus_x_incremental_net_utility": utility,
        "episode_diagnostics": episodes,
        "zero_weight_episode_diagnostics": zero_weight_episodes,
        "dependence_accounting": {
            "raw_statistical_observation_count": len(weighted_rows),
            "effective_independent_episode_count": len(weighted_episodes),
            "effective_to_raw_ratio": _ratio(len(weighted_episodes), len(weighted_rows)),
            "note": "effective_episode_id is supplied by the frozen upstream episode/clustering contract; W6 counts it and does not re-cluster after label open",
        },
        "authority_class": "UNTOUCHED_LOCKBOX_EVALUATION_ZERO_FINANCIAL_AUTHORITY",
        "research_mode": "UNTOUCHED_HISTORICAL_LOCKBOX_EVALUATION",
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "capital_authority": "NONE",
        "parent_child_mutation": "FORBIDDEN",
        "broker_orders": "FORBIDDEN",
        "refit_or_rescue": "FORBIDDEN",
    }
    report_sha256 = domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:REPORT",
        canonical_value(body),
    )
    return {**body, "report_sha256": report_sha256}


def verify_evaluation_report(report: Mapping[str, Any]) -> None:
    """Verify report closure and zero-authority status without reopening inputs."""

    if not isinstance(report, Mapping) or report.get("schema_version") != EVALUATION_REPORT_SCHEMA:
        raise UntouchedEvaluationContractError("untouched_report_schema_invalid")
    if report.get("evaluator_id") != EVALUATOR_ID:
        raise UntouchedEvaluationContractError("untouched_report_evaluator_invalid")
    if int(report.get("lockbox_count", 0)) < 1:
        raise UntouchedEvaluationContractError("untouched_report_lockbox_count_invalid")
    if (
        report.get("financial_alpha_evidence") != 0
        or report.get("promotion_authority") != "NONE"
        or report.get("capital_authority") != "NONE"
        or report.get("parent_child_mutation") != "FORBIDDEN"
        or report.get("broker_orders") != "FORBIDDEN"
        or report.get("refit_or_rescue") != "FORBIDDEN"
    ):
        raise UntouchedEvaluationContractError("untouched_report_authority_invalid")
    sealed = str(report.get("report_sha256") or "")
    body = {key: value for key, value in report.items() if key != "report_sha256"}
    expected = domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:REPORT",
        canonical_value(body),
    )
    if sealed != expected:
        raise UntouchedEvaluationContractError("untouched_report_hash_mismatch")


def _records_by_lockbox(
    records: Sequence[Mapping[str, Any]],
    *,
    lockbox_ids: Sequence[str],
    record_name: str,
) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        raise UntouchedEvaluationContractError(f"untouched_{record_name}_records_required")
    expected = set(lockbox_ids)
    by_id: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise UntouchedEvaluationContractError(f"untouched_{record_name}_record_mapping_required")
        lockbox_id = str(record.get("lockbox_id") or "")
        if lockbox_id not in expected or lockbox_id in by_id:
            raise UntouchedEvaluationContractError(f"untouched_{record_name}_lockbox_invalid_or_duplicate")
        by_id[lockbox_id] = record
    if set(by_id) != expected:
        raise UntouchedEvaluationContractError(f"untouched_{record_name}_lockbox_set_not_exact")
    return by_id


def _exact_join(
    predictions: Sequence[Mapping[str, Any]],
    labels: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    prediction_map = {_join_key(row): row for row in predictions}
    label_map = {_join_key(row): row for row in labels}
    if set(prediction_map) != set(label_map):
        missing_labels = sorted(set(prediction_map) - set(label_map))
        missing_predictions = sorted(set(label_map) - set(prediction_map))
        if missing_labels:
            raise UntouchedEvaluationContractError("untouched_exact_join_missing_label:" + _key_text(missing_labels[0]))
        raise UntouchedEvaluationContractError(
            "untouched_exact_join_missing_prediction:" + _key_text(missing_predictions[0])
        )

    joined: list[dict[str, Any]] = []
    for key in sorted(prediction_map):
        prediction = prediction_map[key]
        label = label_map[key]
        for field in (
            "decision_session_ordinal",
            "decision_listing_session_ordinal",
            "security_id",
            "trading_item_id",
            "statistical_weight",
            "zero_weight_reason",
        ):
            if prediction.get(field) != label.get(field):
                raise UntouchedEvaluationContractError(f"untouched_prediction_label_{field}_mismatch")
        joined.append(
            {
                "lockbox_id": prediction["lockbox_id"],
                "prediction_id": prediction["prediction_id"],
                "decision_session_date": prediction["decision_session_date"],
                "decision_session_ordinal": prediction["decision_session_ordinal"],
                "decision_listing_session_ordinal": prediction["decision_listing_session_ordinal"],
                "security_id": prediction["security_id"],
                "trading_item_id": prediction["trading_item_id"],
                "score": float(prediction["score"]),
                "flagged": bool(prediction["flagged"]),
                "eligibility_status": prediction["eligibility_status"],
                "exclusion_reason": prediction["exclusion_reason"],
                "knowledge_cutoff": prediction["knowledge_cutoff"],
                "prediction_made_at": prediction["prediction_made_at"],
                "prediction_recorded_at": prediction["prediction_recorded_at"],
                "statistical_weight": int(prediction["statistical_weight"]),
                "zero_weight_reason": prediction["zero_weight_reason"],
                "winner_label": bool(label["winner_label"]),
                "catastrophic_outcome_label": bool(label["catastrophic_outcome_label"]),
                "realized_total_return": float(label["realized_total_return"]),
                "right_tail_wealth": float(label["right_tail_wealth"]),
                "effective_episode_id": label["effective_episode_id"],
                "breakout_session_date": label["breakout_session_date"],
                "breakout_session_ordinal": label["breakout_session_ordinal"],
                "breakout_listing_session_ordinal": label["breakout_listing_session_ordinal"],
            }
        )
    return joined


def _build_episode_diagnostics(
    joined: Sequence[Mapping[str, Any]],
    *,
    min_lead_sessions: int,
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in joined:
        grouped[(str(row["lockbox_id"]), str(row["effective_episode_id"]))].append(row)

    diagnostics: list[dict[str, Any]] = []
    for (lockbox_id, episode_id), rows in sorted(grouped.items()):
        ordered = sorted(
            rows,
            key=lambda row: (
                int(row["decision_listing_session_ordinal"]),
                int(row["decision_session_ordinal"]),
                str(row["decision_session_date"]),
            ),
        )
        first = ordered[0]
        invariant_fields = (
            "security_id",
            "trading_item_id",
            "winner_label",
            "catastrophic_outcome_label",
            "right_tail_wealth",
            "breakout_session_date",
            "breakout_session_ordinal",
            "breakout_listing_session_ordinal",
            "statistical_weight",
            "zero_weight_reason",
        )
        for row in ordered[1:]:
            for field in invariant_fields:
                if row.get(field) != first.get(field):
                    raise UntouchedEvaluationContractError(
                        f"untouched_effective_episode_invariant_drift:{episode_id}:{field}"
                    )
        winner = bool(first["winner_label"])
        breakout_ordinal = first["breakout_session_ordinal"]
        breakout_listing_ordinal = first["breakout_listing_session_ordinal"]
        if winner:
            assert breakout_ordinal is not None
            assert breakout_listing_ordinal is not None
            if any(
                int(row["decision_listing_session_ordinal"]) >= int(breakout_listing_ordinal)
                for row in ordered
            ):
                raise UntouchedEvaluationContractError(
                    f"untouched_winner_prediction_not_prebreakout:{episode_id}"
                )
            cutoff_listing = int(breakout_listing_ordinal) - min_lead_sessions
            prebreakout = [
                row
                for row in ordered
                if int(row["decision_listing_session_ordinal"]) <= cutoff_listing
            ]
            legitimate_flags = [
                row
                for row in prebreakout
                if row["eligibility_status"] == "ELIGIBLE" and bool(row["flagged"])
            ]
        else:
            prebreakout = []
            legitimate_flags = [
                row
                for row in ordered
                if row["eligibility_status"] == "ELIGIBLE" and bool(row["flagged"])
            ]
        first_detection = legitimate_flags[0] if legitimate_flags else None
        lead_sessions = (
            int(breakout_listing_ordinal) - int(first_detection["decision_listing_session_ordinal"])
            if winner and first_detection is not None
            else None
        )
        exclusion_reasons = sorted(
            {
                str(row["exclusion_reason"])
                for row in (prebreakout if winner else ordered)
                if row["eligibility_status"] == "EXCLUDED" and row.get("exclusion_reason")
            }
        )
        diagnostics.append(
            {
                "lockbox_id": lockbox_id,
                "effective_episode_id": episode_id,
                "security_id": first["security_id"],
                "trading_item_id": first["trading_item_id"],
                "statistical_weight": int(first["statistical_weight"]),
                "zero_weight_reason": first["zero_weight_reason"],
                "winner_label": winner,
                "catastrophic_outcome_label": bool(first["catastrophic_outcome_label"]),
                "decision_row_count": len(ordered),
                "breakout_session_date": first["breakout_session_date"],
                "breakout_session_ordinal": breakout_ordinal,
                "breakout_listing_session_ordinal": breakout_listing_ordinal,
                "eligible_prebreakout_row_count": sum(
                    row["eligibility_status"] == "ELIGIBLE" for row in prebreakout
                ) if winner else None,
                "prebreakout_flag_count": len(legitimate_flags) if winner else None,
                "first_legitimate_detection_session_date": (
                    first_detection["decision_session_date"] if first_detection is not None else None
                ),
                "first_legitimate_detection_session_ordinal": (
                    first_detection["decision_session_ordinal"] if first_detection is not None else None
                ),
                "first_legitimate_detection_listing_session_ordinal": (
                    first_detection["decision_listing_session_ordinal"]
                    if first_detection is not None
                    else None
                ),
                "ttfld_sessions": lead_sessions,
                "detected_prebreakout": bool(winner and first_detection is not None),
                "missed_winner": bool(winner and first_detection is None),
                "false_winner_detected": bool((not winner) and first_detection is not None),
                "catastrophic_false_winner_detected": bool(
                    (not winner)
                    and bool(first["catastrophic_outcome_label"])
                    and first_detection is not None
                ),
                "exclusion_reasons": exclusion_reasons,
                "right_tail_wealth": _number(float(first["right_tail_wealth"])),
            }
        )
    return diagnostics


def _top_k_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    k_values: Sequence[int],
) -> tuple[dict[str, Any], dict[int, set[tuple[str, str, str, str]]]]:
    by_date: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_date[(str(row["lockbox_id"]), str(row["decision_session_date"]))].append(row)

    metrics: dict[str, Any] = {}
    selected_keys: dict[int, set[tuple[str, str, str, str]]] = {int(k): set() for k in k_values}
    for k in k_values:
        date_precision: list[float] = []
        date_recall: list[float] = []
        date_lift: list[float] = []
        total_selected = 0
        total_true_positive = 0
        total_winners = 0
        total_risk_rows = 0
        dates_with_winners = 0
        for date_key in sorted(by_date):
            date_rows = by_date[date_key]
            winners = sum(bool(row["winner_label"]) for row in date_rows)
            risk_count = len(date_rows)
            eligible = [row for row in date_rows if row["eligibility_status"] == "ELIGIBLE"]
            ranked = sorted(
                eligible,
                key=lambda row: (
                    -float(row["score"]),
                    str(row["security_id"]),
                    str(row["trading_item_id"]),
                    str(row["prediction_id"]),
                ),
            )
            selected = ranked[: min(int(k), len(ranked))]
            selected_count = len(selected)
            true_positive = sum(bool(row["winner_label"]) for row in selected)
            precision = true_positive / selected_count if selected_count else 0.0
            base_rate = winners / risk_count if risk_count else 0.0
            recall = true_positive / winners if winners else None
            lift = precision / base_rate if base_rate > 0 else None
            date_precision.append(precision)
            if recall is not None:
                date_recall.append(recall)
                dates_with_winners += 1
            if lift is not None:
                date_lift.append(lift)
            total_selected += selected_count
            total_true_positive += true_positive
            total_winners += winners
            total_risk_rows += risk_count
            for row in selected:
                selected_keys[int(k)].add(_join_key(row))

        micro_precision = total_true_positive / total_selected if total_selected else 0.0
        micro_recall = total_true_positive / total_winners if total_winners else None
        micro_base_rate = total_winners / total_risk_rows if total_risk_rows else None
        micro_lift = (
            micro_precision / micro_base_rate
            if micro_base_rate is not None and micro_base_rate > 0
            else None
        )
        metrics[str(k)] = {
            "k": int(k),
            "decision_date_count": len(by_date),
            "dates_with_at_least_one_winner": dates_with_winners,
            "selected_count": total_selected,
            "true_positive_count": total_true_positive,
            "winner_count": total_winners,
            "risk_set_row_count": total_risk_rows,
            "macro_precision": _number_or_none(_mean(date_precision)),
            "macro_recall": _number_or_none(_mean(date_recall)),
            "macro_lift": _number_or_none(_mean(date_lift)),
            "micro_precision": _number_or_none(micro_precision),
            "micro_recall": _number_or_none(micro_recall),
            "micro_base_rate": _number_or_none(micro_base_rate),
            "micro_lift": _number_or_none(micro_lift),
            "tie_break": "score_desc_then_security_id_then_trading_item_id_then_prediction_id",
            "excluded_rows_rankable": False,
        }
    return metrics, selected_keys


def _average_precision(rows: Sequence[Mapping[str, Any]]) -> float | None:
    total_winners = sum(bool(row["winner_label"]) for row in rows)
    if total_winners == 0:
        return None
    ranked = sorted(
        rows,
        key=lambda row: (
            0 if row["eligibility_status"] == "ELIGIBLE" else 1,
            -float(row["score"]) if row["eligibility_status"] == "ELIGIBLE" else 0.0,
            str(row["lockbox_id"]),
            int(row["decision_session_ordinal"]),
            str(row["security_id"]),
            str(row["trading_item_id"]),
        ),
    )
    true_positive = 0
    precision_sum = 0.0
    for rank, row in enumerate(ranked, start=1):
        if bool(row["winner_label"]):
            true_positive += 1
            precision_sum += true_positive / rank
    return precision_sum / total_winners


def _detection_metrics(
    rows: Sequence[Mapping[str, Any]],
    episodes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    winner_episodes = [episode for episode in episodes if bool(episode["winner_label"])]
    detected_winners = [episode for episode in winner_episodes if bool(episode["detected_prebreakout"])]
    missed_winners = [episode for episode in winner_episodes if bool(episode["missed_winner"])]
    false_winners = [episode for episode in episodes if bool(episode["false_winner_detected"])]
    catastrophic_false = [
        episode for episode in episodes if bool(episode["catastrophic_false_winner_detected"])
    ]
    flagged_episodes = [
        episode
        for episode in episodes
        if bool(episode["detected_prebreakout"]) or bool(episode["false_winner_detected"])
    ]
    leads = [int(episode["ttfld_sessions"]) for episode in detected_winners]
    raw_false_flags = sum(
        bool(row["flagged"]) and not bool(row["winner_label"])
        for row in rows
        if row["eligibility_status"] == "ELIGIBLE"
    )
    raw_catastrophic_false_flags = sum(
        bool(row["flagged"])
        and not bool(row["winner_label"])
        and bool(row["catastrophic_outcome_label"])
        for row in rows
        if row["eligibility_status"] == "ELIGIBLE"
    )
    return {
        "winner_effective_episode_count": len(winner_episodes),
        "detected_winner_effective_episode_count": len(detected_winners),
        "missed_winner_effective_episode_count": len(missed_winners),
        "prebreakout_detection_recall_by_effective_episode": _ratio(
            len(detected_winners), len(winner_episodes)
        ),
        "false_winner_effective_episode_count": len(false_winners),
        "catastrophic_false_winner_effective_episode_count": len(catastrophic_false),
        "flagged_effective_episode_count": len(flagged_episodes),
        "false_winner_rate_by_flagged_effective_episode": _ratio(
            len(false_winners), len(flagged_episodes)
        ),
        "catastrophic_false_winner_rate_by_flagged_effective_episode": _ratio(
            len(catastrophic_false), len(flagged_episodes)
        ),
        "raw_false_flag_count": int(raw_false_flags),
        "raw_catastrophic_false_flag_count": int(raw_catastrophic_false_flags),
        "ttfld_sessions": {
            "detected_episode_count": len(leads),
            "mean": _number_or_none(_mean(leads)),
            "median": _number_or_none(statistics.median(leads) if leads else None),
            "minimum": min(leads) if leads else None,
            "maximum": max(leads) if leads else None,
        },
    }


def _right_tail_wealth_metrics(
    episodes: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    *,
    selected_keys: Mapping[int, set[tuple[str, str, str, str]]],
    min_lead_sessions: int,
) -> dict[str, Any]:
    winner_episodes = [episode for episode in episodes if bool(episode["winner_label"])]
    total_wealth = sum(float(episode["right_tail_wealth"]) for episode in winner_episodes)
    flagged_wealth = sum(
        float(episode["right_tail_wealth"])
        for episode in winner_episodes
        if bool(episode["detected_prebreakout"])
    )
    rows_by_episode: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_episode[(str(row["lockbox_id"]), str(row["effective_episode_id"]))].append(row)

    top_k_capture: dict[str, Any] = {}
    for k, selected in sorted(selected_keys.items()):
        captured = 0.0
        captured_count = 0
        for episode in winner_episodes:
            breakout_listing_ordinal = episode["breakout_listing_session_ordinal"]
            assert breakout_listing_ordinal is not None
            cutoff_listing = int(breakout_listing_ordinal) - min_lead_sessions
            episode_rows = rows_by_episode[(
                str(episode["lockbox_id"]),
                str(episode["effective_episode_id"]),
            )]
            caught = any(
                row["eligibility_status"] == "ELIGIBLE"
                and int(row["decision_listing_session_ordinal"]) <= cutoff_listing
                and _join_key(row) in selected
                for row in episode_rows
            )
            if caught:
                captured += float(episode["right_tail_wealth"])
                captured_count += 1
        top_k_capture[str(k)] = {
            "captured_winner_effective_episode_count": captured_count,
            "captured_right_tail_wealth": _number(captured),
            "right_tail_wealth_capture_ratio": _ratio(captured, total_wealth),
        }
    return {
        "winner_effective_episode_count": len(winner_episodes),
        "total_right_tail_wealth": _number(total_wealth),
        "flagged_prebreakout_captured_right_tail_wealth": _number(flagged_wealth),
        "flagged_prebreakout_right_tail_wealth_capture_ratio": _ratio(flagged_wealth, total_wealth),
        "top_k_prebreakout_capture": top_k_capture,
        "minimum_legitimate_lead_sessions": min_lead_sessions,
        "capital_weighted": False,
        "note": "signal-level right-tail wealth capture only; capital-weighted shadow economics remain a separate frozen-policy layer",
    }


def _incremental_utility_metrics(
    utility_rows: Sequence[Mapping[str, Any]],
    *,
    lockbox_ids: Sequence[str],
) -> dict[str, Any]:
    if set(row["lockbox_id"] for row in utility_rows) != set(lockbox_ids):
        raise UntouchedEvaluationContractError("untouched_utility_lockbox_set_not_exact")
    incumbent = [float(row["incumbent_net_utility"]) for row in utility_rows]
    combined = [float(row["incumbent_plus_candidate_net_utility"]) for row in utility_rows]
    deltas = [candidate - base for base, candidate in zip(incumbent, combined)]
    by_lockbox: list[dict[str, Any]] = []
    for lockbox_id in lockbox_ids:
        selected = [row for row in utility_rows if row["lockbox_id"] == lockbox_id]
        base = [float(row["incumbent_net_utility"]) for row in selected]
        candidate = [float(row["incumbent_plus_candidate_net_utility"]) for row in selected]
        delta = [candidate_value - base_value for base_value, candidate_value in zip(base, candidate)]
        by_lockbox.append(
            {
                "lockbox_id": lockbox_id,
                "period_count": len(selected),
                "incumbent_net_utility_sum": _number(sum(base)),
                "incumbent_plus_candidate_net_utility_sum": _number(sum(candidate)),
                "incremental_net_utility_sum": _number(sum(delta)),
                "incremental_net_utility_mean": _number_or_none(_mean(delta)),
                "positive_incremental_period_fraction": _ratio(sum(value > 0 for value in delta), len(delta)),
            }
        )
    return {
        "period_count": len(utility_rows),
        "incumbent_net_utility_sum": _number(sum(incumbent)),
        "incumbent_plus_candidate_net_utility_sum": _number(sum(combined)),
        "incremental_net_utility_sum": _number(sum(deltas)),
        "incremental_net_utility_mean": _number_or_none(_mean(deltas)),
        "positive_incremental_period_fraction": _ratio(sum(value > 0 for value in deltas), len(deltas)),
        "by_lockbox": by_lockbox,
    }


def _join_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row["lockbox_id"]),
        str(row["decision_session_date"]),
        str(row["security_id"]),
        str(row["trading_item_id"]),
    )


def _key_text(key: Sequence[str]) -> str:
    return "|".join(str(value) for value in key)


def _mean(values: Iterable[float | int]) -> float | None:
    materialized = [float(value) for value in values]
    return sum(materialized) / len(materialized) if materialized else None


def _ratio(numerator: float | int, denominator: float | int) -> str | None:
    if float(denominator) == 0:
        return None
    return _number(float(numerator) / float(denominator))


def _number(value: float | int) -> str:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise UntouchedEvaluationContractError("untouched_nonfinite_metric")
    return format(parsed, ".17g")


def _number_or_none(value: float | int | None) -> str | None:
    return None if value is None else _number(value)
