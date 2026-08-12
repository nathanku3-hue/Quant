"""Confirmation-only W7 guardian for frozen VOL_SQUEEZE_BREAKOUT_v1 M0.

This module consumes already-matured evaluator receipts. It never fetches outcomes,
constructs labels, mutates M0, or grants financial/capital authority.
"""

from __future__ import annotations

from datetime import date
import math
import random
import string
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.vol_squeeze_breakout_v1.contracts import (
    ACCEPTANCE_LIFT_THRESHOLD,
    BOOTSTRAP_BLOCK_LENGTH,
    BOOTSTRAP_CONFIDENCE,
    BOOTSTRAP_LOWER_TAIL_PROBABILITY,
    BOOTSTRAP_METHOD_ID,
    BOOTSTRAP_REPLICATES,
    BOOTSTRAP_SEED,
    CONFIRMATION_RESULT_SCHEMA,
    CONFIRMATION_ROLE_ID,
    FAMILY_ID,
    GUARDIAN_CONTRACT_SHA256,
    IMPLEMENTATION_ID,
    MATURED_DATE_RECORD_SCHEMA,
    MATURITY_STATUS,
    MIN_MATURED_PRIMARY_DECISION_DATES,
    OUTCOME_AUTHORITY_CLASS,
    PRIMARY_LABEL_SPEC_ID,
    SEARCH_FAMILY_ID,
    WINNER_FRACTION,
    validate_vsb_contract,
)


_HEX_DIGITS = frozenset(string.hexdigits.lower())


def evaluate_vsb_confirmation(
    matured_date_records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate the frozen VSB confirmation gate without opening outcomes.

    Records must come from an upstream untouched/prospective evaluator and bind the
    prediction batch plus the evaluator receipt. Before 20 matured primary dates,
    the guardian returns only an eligibility block and does not calculate lift or
    bootstrap statistics, preventing early confirmatory peeking.
    """

    validate_vsb_contract()
    records = [_validate_matured_date_record(record) for record in matured_date_records]
    records.sort(key=lambda item: item["decision_session_date"])
    decision_dates = [str(record["decision_session_date"]) for record in records]
    if len(decision_dates) != len(set(decision_dates)):
        raise ValueError("vsb_confirmation_duplicate_decision_date")

    count = len(records)
    common: dict[str, Any] = {
        "schema_version": CONFIRMATION_RESULT_SCHEMA,
        "confirmation_role_id": CONFIRMATION_ROLE_ID,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
        "matured_primary_decision_dates": count,
        "minimum_matured_primary_decision_dates": MIN_MATURED_PRIMARY_DECISION_DATES,
        "evaluation_date_start": decision_dates[0] if decision_dates else None,
        "evaluation_date_end": decision_dates[-1] if decision_dates else None,
        "bootstrap_method_id": BOOTSTRAP_METHOD_ID,
        "bootstrap_block_length": BOOTSTRAP_BLOCK_LENGTH,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_confidence": format(BOOTSTRAP_CONFIDENCE, ".17g"),
        "acceptance_lift_threshold": format(ACCEPTANCE_LIFT_THRESHOLD, ".17g"),
        "retune_authority": "NONE",
        "prebreakout_authority": "NONE",
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }

    if count < MIN_MATURED_PRIMARY_DECISION_DATES:
        body = {
            **common,
            "gate_status": "BLOCKED_INSUFFICIENT_MATURED_PRIMARY_DATES",
            "gate_passed": None,
            "winner_recall_10d": None,
            "support_breadth": None,
            "winner_recall_lift_10d": None,
            "bootstrap_lower_bound_80pct": None,
            "bootstrap_upper_bound_80pct": None,
        }
        return _seal_confirmation_result(body)

    winner_recall, support_breadth, observed_lift = _lift_statistics(records)
    bootstrap_lifts = _moving_block_bootstrap_lifts(records)
    lower_bound = _type7_percentile(bootstrap_lifts, BOOTSTRAP_LOWER_TAIL_PROBABILITY)
    upper_bound = _type7_percentile(bootstrap_lifts, 1.0 - BOOTSTRAP_LOWER_TAIL_PROBABILITY)
    gate_passed = observed_lift > ACCEPTANCE_LIFT_THRESHOLD and lower_bound > ACCEPTANCE_LIFT_THRESHOLD
    body = {
        **common,
        "gate_status": "CONFIRMATION_GATE_PASS" if gate_passed else "CONFIRMATION_GATE_FAIL",
        "gate_passed": gate_passed,
        "winner_recall_10d": _number_text(winner_recall),
        "support_breadth": _number_text(support_breadth),
        "winner_recall_lift_10d": _number_text(observed_lift),
        "bootstrap_lower_bound_80pct": _number_text(lower_bound),
        "bootstrap_upper_bound_80pct": _number_text(upper_bound),
    }
    return _seal_confirmation_result(body)


def verify_confirmation_result(result: Mapping[str, Any]) -> None:
    """Verify an immutable W7 guardian result and its zero-authority boundary."""

    if not isinstance(result, Mapping):
        raise ValueError("vsb_confirmation_result_mapping_required")
    if result.get("schema_version") != CONFIRMATION_RESULT_SCHEMA:
        raise ValueError("vsb_confirmation_result_schema_invalid")
    if result.get("confirmation_role_id") != CONFIRMATION_ROLE_ID or result.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_confirmation_result_identity_invalid")
    if result.get("implementation_id") != IMPLEMENTATION_ID or result.get("search_family_id") != SEARCH_FAMILY_ID:
        raise ValueError("vsb_confirmation_result_frozen_implementation_invalid")
    if result.get("primary_label_spec_id") != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("vsb_confirmation_result_primary_label_invalid")
    if result.get("guardian_contract_sha256") != GUARDIAN_CONTRACT_SHA256:
        raise ValueError("vsb_confirmation_result_guardian_contract_invalid")
    if (
        result.get("retune_authority") != "NONE"
        or result.get("prebreakout_authority") != "NONE"
        or result.get("financial_alpha_evidence") != 0
        or result.get("capital_authority") != "NONE"
    ):
        raise ValueError("vsb_confirmation_result_authority_invalid")

    if result.get("bootstrap_method_id") != BOOTSTRAP_METHOD_ID:
        raise ValueError("vsb_confirmation_result_bootstrap_method_invalid")
    if _positive_int(result.get("bootstrap_block_length"), "bootstrap_block_length") != BOOTSTRAP_BLOCK_LENGTH:
        raise ValueError("vsb_confirmation_result_bootstrap_block_length_invalid")
    if _positive_int(result.get("bootstrap_replicates"), "bootstrap_replicates") != BOOTSTRAP_REPLICATES:
        raise ValueError("vsb_confirmation_result_bootstrap_replicates_invalid")
    if _nonnegative_int(result.get("bootstrap_seed"), "bootstrap_seed") != BOOTSTRAP_SEED:
        raise ValueError("vsb_confirmation_result_bootstrap_seed_invalid")
    if _finite_float(result.get("bootstrap_confidence"), "bootstrap_confidence") != BOOTSTRAP_CONFIDENCE:
        raise ValueError("vsb_confirmation_result_bootstrap_confidence_invalid")
    if _finite_float(result.get("acceptance_lift_threshold"), "acceptance_lift_threshold") != ACCEPTANCE_LIFT_THRESHOLD:
        raise ValueError("vsb_confirmation_result_acceptance_threshold_invalid")

    count = _nonnegative_int(result.get("matured_primary_decision_dates"), "matured_primary_decision_dates")
    if _positive_int(
        result.get("minimum_matured_primary_decision_dates"),
        "minimum_matured_primary_decision_dates",
    ) != MIN_MATURED_PRIMARY_DECISION_DATES:
        raise ValueError("vsb_confirmation_result_minimum_dates_invalid")
    if count < MIN_MATURED_PRIMARY_DECISION_DATES:
        if result.get("gate_status") != "BLOCKED_INSUFFICIENT_MATURED_PRIMARY_DATES" or result.get("gate_passed") is not None:
            raise ValueError("vsb_confirmation_early_gate_status_invalid")
        for field in (
            "winner_recall_10d",
            "support_breadth",
            "winner_recall_lift_10d",
            "bootstrap_lower_bound_80pct",
            "bootstrap_upper_bound_80pct",
        ):
            if result.get(field) is not None:
                raise ValueError("vsb_confirmation_early_metric_exposure_forbidden")
    else:
        winner_recall = _finite_float(result.get("winner_recall_10d"), "winner_recall_10d")
        support_breadth = _finite_float(result.get("support_breadth"), "support_breadth")
        lift = _finite_float(result.get("winner_recall_lift_10d"), "winner_recall_lift_10d")
        lower_bound = _finite_float(result.get("bootstrap_lower_bound_80pct"), "bootstrap_lower_bound_80pct")
        upper_bound = _finite_float(result.get("bootstrap_upper_bound_80pct"), "bootstrap_upper_bound_80pct")
        if not 0.0 <= winner_recall <= 1.0 or not 0.0 <= support_breadth <= 1.0:
            raise ValueError("vsb_confirmation_result_rate_domain_invalid")
        if lift < 0.0 or lower_bound < 0.0 or upper_bound < lower_bound:
            raise ValueError("vsb_confirmation_result_lift_domain_invalid")
        expected_pass = lift > ACCEPTANCE_LIFT_THRESHOLD and lower_bound > ACCEPTANCE_LIFT_THRESHOLD
        if result.get("gate_passed") is not expected_pass:
            raise ValueError("vsb_confirmation_result_gate_boolean_invalid")
        expected_status = "CONFIRMATION_GATE_PASS" if expected_pass else "CONFIRMATION_GATE_FAIL"
        if result.get("gate_status") != expected_status:
            raise ValueError("vsb_confirmation_gate_status_invalid")

    sealed = _sha256_text(result.get("confirmation_evaluation_sha256"), "confirmation_evaluation_sha256")
    body = {key: value for key, value in result.items() if key != "confirmation_evaluation_sha256"}
    expected = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:CONFIRMATION_GUARDIAN_RESULT",
        canonical_value(body),
    )
    if sealed != expected:
        raise ValueError("vsb_confirmation_result_hash_mismatch")


def _validate_matured_date_record(record: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError("vsb_confirmation_matured_record_mapping_required")
    normalized = dict(record)
    if normalized.get("schema_version") != MATURED_DATE_RECORD_SCHEMA:
        raise ValueError("vsb_confirmation_matured_record_schema_invalid")
    if normalized.get("family_id") != FAMILY_ID or normalized.get("confirmation_role_id") != CONFIRMATION_ROLE_ID:
        raise ValueError("vsb_confirmation_matured_record_family_invalid")
    if normalized.get("implementation_id") != IMPLEMENTATION_ID or normalized.get("search_family_id") != SEARCH_FAMILY_ID:
        raise ValueError("vsb_confirmation_matured_record_implementation_invalid")
    if normalized.get("primary_label_spec_id") != PRIMARY_LABEL_SPEC_ID:
        raise ValueError("vsb_confirmation_matured_record_label_invalid")
    if normalized.get("guardian_contract_sha256") != GUARDIAN_CONTRACT_SHA256:
        raise ValueError("vsb_confirmation_matured_record_guardian_contract_invalid")
    if normalized.get("maturity_status") != MATURITY_STATUS:
        raise ValueError("vsb_confirmation_matured_record_not_matured")
    if normalized.get("outcome_authority_class") != OUTCOME_AUTHORITY_CLASS:
        raise ValueError("vsb_confirmation_matured_record_outcome_authority_invalid")
    if normalized.get("prediction_before_label_open") is not True:
        raise ValueError("vsb_confirmation_prediction_before_label_proof_required")
    if _nonnegative_int(normalized.get("custody_violation_count"), "custody_violation_count") != 0:
        raise ValueError("vsb_confirmation_custody_violation")
    if normalized.get("financial_alpha_evidence") != 0 or normalized.get("capital_authority") != "NONE":
        raise ValueError("vsb_confirmation_matured_record_authority_invalid")

    decision_date = str(normalized.get("decision_session_date") or "")
    try:
        date.fromisoformat(decision_date)
    except ValueError as exc:
        raise ValueError("vsb_confirmation_decision_date_invalid") from exc
    normalized["decision_session_date"] = decision_date
    normalized["prediction_batch_sha256"] = _sha256_text(
        normalized.get("prediction_batch_sha256"),
        "prediction_batch_sha256",
    )
    normalized["outcome_evaluation_receipt_sha256"] = _sha256_text(
        normalized.get("outcome_evaluation_receipt_sha256"),
        "outcome_evaluation_receipt_sha256",
    )

    risk_set_count = _positive_int(normalized.get("risk_set_count"), "risk_set_count")
    support_count = _nonnegative_int(normalized.get("support_count"), "support_count")
    winner_count = _positive_int(normalized.get("winner_count"), "winner_count")
    hit_count = _nonnegative_int(normalized.get("winner_support_hit_count"), "winner_support_hit_count")
    if support_count > risk_set_count:
        raise ValueError("vsb_confirmation_support_count_exceeds_risk_set")
    expected_winners = math.ceil(WINNER_FRACTION * risk_set_count)
    if winner_count != expected_winners:
        raise ValueError("vsb_confirmation_winner_count_not_frozen_top5")
    if hit_count > winner_count or hit_count > support_count:
        raise ValueError("vsb_confirmation_winner_support_hit_count_invalid")
    normalized["risk_set_count"] = risk_set_count
    normalized["support_count"] = support_count
    normalized["winner_count"] = winner_count
    normalized["winner_support_hit_count"] = hit_count
    return normalized


def _lift_statistics(records: Sequence[Mapping[str, Any]]) -> tuple[float, float, float]:
    total_winners = sum(int(record["winner_count"]) for record in records)
    total_hits = sum(int(record["winner_support_hit_count"]) for record in records)
    winner_recall = total_hits / total_winners if total_winners else 0.0
    support_breadth = sum(
        int(record["support_count"]) / int(record["risk_set_count"])
        for record in records
    ) / len(records)
    lift = winner_recall / support_breadth if support_breadth > 0 else 0.0
    return winner_recall, support_breadth, lift


def _moving_block_bootstrap_lifts(records: Sequence[Mapping[str, Any]]) -> list[float]:
    count = len(records)
    if count < BOOTSTRAP_BLOCK_LENGTH:
        raise ValueError("vsb_confirmation_bootstrap_insufficient_dates")
    starts = count - BOOTSTRAP_BLOCK_LENGTH + 1
    blocks_needed = math.ceil(count / BOOTSTRAP_BLOCK_LENGTH)
    rng = random.Random(BOOTSTRAP_SEED)
    lifts: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled: list[Mapping[str, Any]] = []
        for _block in range(blocks_needed):
            start = rng.randrange(starts)
            sampled.extend(records[start : start + BOOTSTRAP_BLOCK_LENGTH])
        sampled = sampled[:count]
        lifts.append(_lift_statistics(sampled)[2])
    lifts.sort()
    return lifts


def _type7_percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("vsb_confirmation_percentile_values_required")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("vsb_confirmation_percentile_probability_invalid")
    rank = (len(sorted_values) - 1) * probability
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return float(sorted_values[lower])
    weight = rank - lower
    return float(sorted_values[lower]) * (1.0 - weight) + float(sorted_values[upper]) * weight


def _seal_confirmation_result(body: Mapping[str, Any]) -> dict[str, Any]:
    canonical_body = canonical_value(dict(body))
    sealed = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:CONFIRMATION_GUARDIAN_RESULT",
        canonical_body,
    )
    result = {**dict(body), "confirmation_evaluation_sha256": sealed}
    verify_confirmation_result(result)
    return result


def _positive_int(value: Any, field: str) -> int:
    parsed = _nonnegative_int(value, field)
    if parsed <= 0:
        raise ValueError(f"vsb_confirmation_{field}_must_be_positive")
    return parsed


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"vsb_confirmation_{field}_integer_required")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"vsb_confirmation_{field}_integer_required") from exc
    if str(parsed) != str(value) and not isinstance(value, int):
        raise ValueError(f"vsb_confirmation_{field}_integer_required")
    if parsed < 0:
        raise ValueError(f"vsb_confirmation_{field}_must_be_nonnegative")
    return parsed


def _finite_float(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"vsb_confirmation_{field}_finite_number_required") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"vsb_confirmation_{field}_finite_number_required")
    return parsed


def _sha256_text(value: Any, field: str) -> str:
    text = str(value or "")
    if len(text) != 64 or any(character not in _HEX_DIGITS for character in text.lower()):
        raise ValueError(f"vsb_confirmation_{field}_invalid")
    return text.lower()


def _number_text(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("vsb_confirmation_nonfinite_metric")
    return format(value, ".17g")
