"""Frozen custody contracts for PREBREAKOUT untouched evaluation.

This package is intentionally separate from discovery/model code.  It can bind
already-produced prediction rows before labels are opened, then later verify an
explicit label-open record and score the immutable rows.  It never exposes an
outcome data source or a prediction/model fitting surface.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import assert_sha256, domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.aov0.contracts import normalize_security_id


EVALUATOR_ID = "PREBREAKOUT_UNTOUCHED_EVALUATOR_v1"
EVALUATION_CONTRACT_SCHEMA = "prebreakout_untouched_evaluation_contract_v1"
PREDICTION_ROW_SCHEMA = "prebreakout_untouched_prediction_row_v1"
LABEL_ROW_SCHEMA = "prebreakout_untouched_label_row_v1"
UTILITY_ROW_SCHEMA = "prebreakout_untouched_utility_row_v1"
PREDICTION_FREEZE_SCHEMA = "prebreakout_prediction_freeze_record_v1"
LABEL_OPEN_SCHEMA = "prebreakout_label_open_record_v1"
EVALUATION_REPORT_SCHEMA = "prebreakout_untouched_evaluation_report_v1"

SCORE_DIRECTION = "HIGHER_IS_BETTER"
ELIGIBILITY_STATUSES = ("ELIGIBLE", "EXCLUDED")
ZERO_WEIGHT_REASON = "ENGINEERING_SMOKE_ZERO_STATISTICAL_WEIGHT"


class UntouchedEvaluationContractError(ValueError):
    """Fail-closed untouched-evaluation contract violation."""


def identity_key(security_id: str, trading_item_id: str) -> str:
    security = normalize_security_id(security_id)
    trading_item = str(trading_item_id or "").strip()
    if not trading_item:
        raise UntouchedEvaluationContractError("untouched_trading_item_id_required")
    return f"{security}|{trading_item}"


def build_evaluation_contract(
    *,
    family_id: str,
    implementation_id: str,
    primary_label_spec_id: str,
    lockbox_ids: Sequence[str],
    k_values: Sequence[int],
    min_legitimate_lead_sessions: int,
    zero_weight_identity_keys: Sequence[str],
    prediction_ledger_sha256: str,
    implementation_manifest_sha256: str,
    search_ledger_sha256: str,
    evaluator_code_sha256: str,
) -> dict[str, Any]:
    """Build one content-addressed, preregistered evaluation contract."""

    body = {
        "schema_version": EVALUATION_CONTRACT_SCHEMA,
        "evaluator_id": EVALUATOR_ID,
        "family_id": str(family_id),
        "implementation_id": str(implementation_id),
        "primary_label_spec_id": str(primary_label_spec_id),
        "lockbox_ids": [str(value) for value in lockbox_ids],
        "k_values": [int(value) for value in k_values],
        "min_legitimate_lead_sessions": int(min_legitimate_lead_sessions),
        "score_direction": SCORE_DIRECTION,
        "zero_weight_identity_keys": sorted(str(value) for value in zero_weight_identity_keys),
        "zero_weight_reason": ZERO_WEIGHT_REASON,
        "prediction_ledger_sha256": str(prediction_ledger_sha256),
        "implementation_manifest_sha256": str(implementation_manifest_sha256),
        "search_ledger_sha256": str(search_ledger_sha256),
        "evaluator_code_sha256": str(evaluator_code_sha256),
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    contract = {
        **body,
        "contract_sha256": domain_hash(
            "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:CONTRACT",
            canonical_value(body),
        ),
    }
    verify_evaluation_contract(contract)
    return contract


def verify_evaluation_contract(contract: Mapping[str, Any]) -> None:
    if not isinstance(contract, Mapping):
        raise UntouchedEvaluationContractError("untouched_contract_mapping_required")
    if contract.get("schema_version") != EVALUATION_CONTRACT_SCHEMA:
        raise UntouchedEvaluationContractError("untouched_contract_schema_invalid")
    if contract.get("evaluator_id") != EVALUATOR_ID:
        raise UntouchedEvaluationContractError("untouched_evaluator_id_invalid")
    for field in ("family_id", "implementation_id", "primary_label_spec_id"):
        if not str(contract.get(field) or "").strip():
            raise UntouchedEvaluationContractError(f"untouched_contract_{field}_required")
    lockbox_ids = [str(value) for value in contract.get("lockbox_ids") or []]
    if not lockbox_ids:
        raise UntouchedEvaluationContractError("untouched_at_least_one_lockbox_required")
    if len(lockbox_ids) != len(set(lockbox_ids)) or any(not value.strip() for value in lockbox_ids):
        raise UntouchedEvaluationContractError("untouched_lockbox_ids_invalid")
    k_values = [int(value) for value in contract.get("k_values") or []]
    if not k_values or any(value <= 0 for value in k_values):
        raise UntouchedEvaluationContractError("untouched_k_values_invalid")
    if k_values != sorted(set(k_values)):
        raise UntouchedEvaluationContractError("untouched_k_values_must_be_unique_sorted")
    if int(contract.get("min_legitimate_lead_sessions", 0)) < 1:
        raise UntouchedEvaluationContractError("untouched_min_lead_must_be_at_least_one_session")
    if contract.get("score_direction") != SCORE_DIRECTION:
        raise UntouchedEvaluationContractError("untouched_score_direction_invalid")
    if contract.get("zero_weight_reason") != ZERO_WEIGHT_REASON:
        raise UntouchedEvaluationContractError("untouched_zero_weight_reason_invalid")
    zero_weight_keys = [str(value) for value in contract.get("zero_weight_identity_keys") or []]
    if zero_weight_keys != sorted(set(zero_weight_keys)):
        raise UntouchedEvaluationContractError("untouched_zero_weight_identity_keys_invalid")
    for key in zero_weight_keys:
        if "|" not in key:
            raise UntouchedEvaluationContractError("untouched_zero_weight_identity_key_invalid")
        security_id, trading_item_id = key.split("|", 1)
        if identity_key(security_id, trading_item_id) != key:
            raise UntouchedEvaluationContractError("untouched_zero_weight_identity_key_noncanonical")
    for field in (
        "prediction_ledger_sha256",
        "implementation_manifest_sha256",
        "search_ledger_sha256",
        "evaluator_code_sha256",
    ):
        try:
            assert_sha256(str(contract.get(field) or ""))
        except ValueError as exc:
            raise UntouchedEvaluationContractError(f"untouched_{field}_invalid") from exc
    if contract.get("financial_alpha_evidence") != 0 or contract.get("capital_authority") != "NONE":
        raise UntouchedEvaluationContractError("untouched_contract_authority_invalid")
    sealed = str(contract.get("contract_sha256") or "")
    body = {key: value for key, value in contract.items() if key != "contract_sha256"}
    expected = domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:CONTRACT",
        canonical_value(body),
    )
    if sealed != expected:
        raise UntouchedEvaluationContractError("untouched_contract_hash_mismatch")


def validate_prediction_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    verify_evaluation_contract(contract)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise UntouchedEvaluationContractError("untouched_prediction_rows_required")
    lockboxes = set(str(value) for value in contract["lockbox_ids"])
    zero_weight = set(str(value) for value in contract["zero_weight_identity_keys"])
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_keys: set[tuple[str, str, str, str]] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise UntouchedEvaluationContractError("untouched_prediction_row_mapping_required")
        row = dict(raw)
        if row.get("schema_version") != PREDICTION_ROW_SCHEMA:
            raise UntouchedEvaluationContractError("untouched_prediction_row_schema_invalid")
        if row.get("family_id") != contract["family_id"] or row.get("implementation_id") != contract["implementation_id"]:
            raise UntouchedEvaluationContractError("untouched_prediction_identity_invalid")
        lockbox_id = str(row.get("lockbox_id") or "")
        if lockbox_id not in lockboxes:
            raise UntouchedEvaluationContractError("untouched_prediction_lockbox_invalid")
        prediction_id = str(row.get("prediction_id") or "")
        if not prediction_id or prediction_id in seen_ids:
            raise UntouchedEvaluationContractError("untouched_prediction_id_invalid_or_duplicate")
        seen_ids.add(prediction_id)
        security_id = normalize_security_id(str(row.get("security_id") or ""))
        trading_item_id = str(row.get("trading_item_id") or "").strip()
        key_text = identity_key(security_id, trading_item_id)
        decision_date = str(row.get("decision_session_date") or "")
        if not decision_date:
            raise UntouchedEvaluationContractError("untouched_prediction_decision_session_date_required")
        decision_ordinal = _nonnegative_int(row.get("decision_session_ordinal"), "prediction_decision_session_ordinal")
        decision_listing_ordinal = _nonnegative_int(
            row.get("decision_listing_session_ordinal"),
            "prediction_decision_listing_session_ordinal",
        )
        join_key = (lockbox_id, decision_date, security_id, trading_item_id)
        if join_key in seen_keys:
            raise UntouchedEvaluationContractError("untouched_prediction_join_key_duplicate")
        seen_keys.add(join_key)
        score = _finite_float(row.get("score"), "prediction_score")
        if type(row.get("flagged")) is not bool:
            raise UntouchedEvaluationContractError("untouched_prediction_flagged_bool_required")
        eligibility = str(row.get("eligibility_status") or "")
        if eligibility not in ELIGIBILITY_STATUSES:
            raise UntouchedEvaluationContractError("untouched_prediction_eligibility_status_invalid")
        exclusion_reason = str(row.get("exclusion_reason") or "").strip()
        if eligibility == "EXCLUDED":
            if bool(row["flagged"]):
                raise UntouchedEvaluationContractError("untouched_excluded_prediction_cannot_be_flagged")
            if not exclusion_reason:
                raise UntouchedEvaluationContractError("untouched_excluded_prediction_reason_required")
        elif exclusion_reason:
            raise UntouchedEvaluationContractError("untouched_eligible_prediction_exclusion_reason_forbidden")
        knowledge_cutoff = _timestamp(row.get("knowledge_cutoff"), "prediction_knowledge_cutoff")
        prediction_made_at = _timestamp(row.get("prediction_made_at"), "prediction_made_at")
        prediction_recorded_at = _timestamp(row.get("prediction_recorded_at"), "prediction_recorded_at")
        if knowledge_cutoff > prediction_made_at:
            raise UntouchedEvaluationContractError("untouched_prediction_before_knowledge_cutoff")
        if prediction_made_at > prediction_recorded_at:
            raise UntouchedEvaluationContractError("untouched_prediction_recorded_before_made")
        weight = _binary_weight(row.get("statistical_weight"), "prediction_statistical_weight")
        expected_weight = 0 if key_text in zero_weight else 1
        if weight != expected_weight:
            raise UntouchedEvaluationContractError("untouched_prediction_statistical_weight_not_preregistered")
        zero_reason = str(row.get("zero_weight_reason") or "").strip()
        if weight == 0:
            if zero_reason != ZERO_WEIGHT_REASON:
                raise UntouchedEvaluationContractError("untouched_prediction_zero_weight_reason_invalid")
        elif zero_reason:
            raise UntouchedEvaluationContractError("untouched_prediction_zero_weight_reason_forbidden")
        normalized.append(
            {
                **row,
                "lockbox_id": lockbox_id,
                "prediction_id": prediction_id,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
                "decision_session_date": decision_date,
                "decision_session_ordinal": decision_ordinal,
                "decision_listing_session_ordinal": decision_listing_ordinal,
                "score": score,
                "statistical_weight": weight,
                "knowledge_cutoff": _timestamp_text(knowledge_cutoff),
                "prediction_made_at": _timestamp_text(prediction_made_at),
                "prediction_recorded_at": _timestamp_text(prediction_recorded_at),
                "exclusion_reason": exclusion_reason or None,
                "zero_weight_reason": zero_reason or None,
            }
        )
    return sorted(normalized, key=_prediction_sort_key)


def validate_label_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    verify_evaluation_contract(contract)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise UntouchedEvaluationContractError("untouched_label_rows_required")
    lockboxes = set(str(value) for value in contract["lockbox_ids"])
    zero_weight = set(str(value) for value in contract["zero_weight_identity_keys"])
    normalized: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str, str]] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise UntouchedEvaluationContractError("untouched_label_row_mapping_required")
        row = dict(raw)
        if row.get("schema_version") != LABEL_ROW_SCHEMA:
            raise UntouchedEvaluationContractError("untouched_label_row_schema_invalid")
        if row.get("family_id") != contract["family_id"] or row.get("implementation_id") != contract["implementation_id"]:
            raise UntouchedEvaluationContractError("untouched_label_identity_invalid")
        if row.get("label_spec_id") != contract["primary_label_spec_id"]:
            raise UntouchedEvaluationContractError("untouched_label_spec_invalid")
        lockbox_id = str(row.get("lockbox_id") or "")
        if lockbox_id not in lockboxes:
            raise UntouchedEvaluationContractError("untouched_label_lockbox_invalid")
        security_id = normalize_security_id(str(row.get("security_id") or ""))
        trading_item_id = str(row.get("trading_item_id") or "").strip()
        key_text = identity_key(security_id, trading_item_id)
        decision_date = str(row.get("decision_session_date") or "")
        if not decision_date:
            raise UntouchedEvaluationContractError("untouched_label_decision_session_date_required")
        decision_ordinal = _nonnegative_int(row.get("decision_session_ordinal"), "label_decision_session_ordinal")
        decision_listing_ordinal = _nonnegative_int(
            row.get("decision_listing_session_ordinal"),
            "label_decision_listing_session_ordinal",
        )
        join_key = (lockbox_id, decision_date, security_id, trading_item_id)
        if join_key in seen_keys:
            raise UntouchedEvaluationContractError("untouched_label_join_key_duplicate")
        seen_keys.add(join_key)
        if type(row.get("winner_label")) is not bool:
            raise UntouchedEvaluationContractError("untouched_winner_label_bool_required")
        if type(row.get("catastrophic_outcome_label")) is not bool:
            raise UntouchedEvaluationContractError("untouched_catastrophic_label_bool_required")
        winner = bool(row["winner_label"])
        catastrophic = bool(row["catastrophic_outcome_label"])
        if winner and catastrophic:
            raise UntouchedEvaluationContractError("untouched_winner_cannot_be_catastrophic_outcome")
        realized = _finite_float(row.get("realized_total_return"), "label_realized_total_return")
        wealth = _finite_float(row.get("right_tail_wealth"), "label_right_tail_wealth")
        if wealth < 0:
            raise UntouchedEvaluationContractError("untouched_right_tail_wealth_negative")
        if not winner and wealth != 0:
            raise UntouchedEvaluationContractError("untouched_nonwinner_right_tail_wealth_must_be_zero")
        episode_id = str(row.get("effective_episode_id") or "").strip()
        if not episode_id:
            raise UntouchedEvaluationContractError("untouched_effective_episode_id_required")
        breakout_date_raw = row.get("breakout_session_date")
        breakout_ordinal_raw = row.get("breakout_session_ordinal")
        breakout_listing_ordinal_raw = row.get("breakout_listing_session_ordinal")
        if winner:
            breakout_date = str(breakout_date_raw or "").strip()
            if not breakout_date:
                raise UntouchedEvaluationContractError("untouched_winner_breakout_session_date_required")
            breakout_ordinal: int | None = _nonnegative_int(
                breakout_ordinal_raw,
                "winner_breakout_session_ordinal",
            )
            breakout_listing_ordinal: int | None = _nonnegative_int(
                breakout_listing_ordinal_raw,
                "winner_breakout_listing_session_ordinal",
            )
        else:
            if (
                breakout_date_raw not in (None, "")
                or breakout_ordinal_raw is not None
                or breakout_listing_ordinal_raw is not None
            ):
                raise UntouchedEvaluationContractError("untouched_nonwinner_breakout_fields_forbidden")
            breakout_date = None
            breakout_ordinal = None
            breakout_listing_ordinal = None
        weight = _binary_weight(row.get("statistical_weight"), "label_statistical_weight")
        expected_weight = 0 if key_text in zero_weight else 1
        if weight != expected_weight:
            raise UntouchedEvaluationContractError("untouched_label_statistical_weight_not_preregistered")
        zero_reason = str(row.get("zero_weight_reason") or "").strip()
        if weight == 0:
            if zero_reason != ZERO_WEIGHT_REASON:
                raise UntouchedEvaluationContractError("untouched_label_zero_weight_reason_invalid")
        elif zero_reason:
            raise UntouchedEvaluationContractError("untouched_label_zero_weight_reason_forbidden")
        normalized.append(
            {
                **row,
                "lockbox_id": lockbox_id,
                "security_id": security_id,
                "trading_item_id": trading_item_id,
                "decision_session_date": decision_date,
                "decision_session_ordinal": decision_ordinal,
                "decision_listing_session_ordinal": decision_listing_ordinal,
                "winner_label": winner,
                "catastrophic_outcome_label": catastrophic,
                "realized_total_return": realized,
                "right_tail_wealth": wealth,
                "effective_episode_id": episode_id,
                "breakout_session_date": breakout_date,
                "breakout_session_ordinal": breakout_ordinal,
                "breakout_listing_session_ordinal": breakout_listing_ordinal,
                "statistical_weight": weight,
                "zero_weight_reason": zero_reason or None,
            }
        )
    return sorted(normalized, key=_label_sort_key)


def validate_utility_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
) -> list[dict[str, Any]]:
    verify_evaluation_contract(contract)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise UntouchedEvaluationContractError("untouched_utility_rows_required")
    lockboxes = set(str(value) for value in contract["lockbox_ids"])
    seen: set[tuple[str, str]] = set()
    normalized: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, Mapping):
            raise UntouchedEvaluationContractError("untouched_utility_row_mapping_required")
        row = dict(raw)
        if row.get("schema_version") != UTILITY_ROW_SCHEMA:
            raise UntouchedEvaluationContractError("untouched_utility_row_schema_invalid")
        if row.get("family_id") != contract["family_id"] or row.get("implementation_id") != contract["implementation_id"]:
            raise UntouchedEvaluationContractError("untouched_utility_identity_invalid")
        lockbox_id = str(row.get("lockbox_id") or "")
        if lockbox_id not in lockboxes:
            raise UntouchedEvaluationContractError("untouched_utility_lockbox_invalid")
        period_id = str(row.get("evaluation_period_id") or "").strip()
        if not period_id or (lockbox_id, period_id) in seen:
            raise UntouchedEvaluationContractError("untouched_utility_period_invalid_or_duplicate")
        seen.add((lockbox_id, period_id))
        incumbent = _finite_float(row.get("incumbent_net_utility"), "incumbent_net_utility")
        combined = _finite_float(
            row.get("incumbent_plus_candidate_net_utility"),
            "incumbent_plus_candidate_net_utility",
        )
        normalized.append(
            {
                **row,
                "lockbox_id": lockbox_id,
                "evaluation_period_id": period_id,
                "incumbent_net_utility": incumbent,
                "incumbent_plus_candidate_net_utility": combined,
            }
        )
    return sorted(normalized, key=lambda row: (row["lockbox_id"], row["evaluation_period_id"]))


def prediction_snapshot_sha256(
    rows: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
) -> str:
    normalized = validate_prediction_rows(rows, contract=contract)
    return domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:PREDICTION_SNAPSHOT",
        canonical_value(normalized),
    )


def label_snapshot_sha256(
    labels: Sequence[Mapping[str, Any]],
    utility_rows: Sequence[Mapping[str, Any]],
    *,
    contract: Mapping[str, Any],
) -> str:
    normalized_labels = validate_label_rows(labels, contract=contract)
    normalized_utility = validate_utility_rows(utility_rows, contract=contract)
    return domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:LABEL_SNAPSHOT",
        canonical_value({"labels": normalized_labels, "utility_rows": normalized_utility}),
    )


def build_prediction_freeze_record(
    *,
    contract: Mapping[str, Any],
    lockbox_id: str,
    prediction_rows: Sequence[Mapping[str, Any]],
    sealed_at: datetime | str,
    custody_authority: str,
    custody_evidence_sha256: str,
) -> dict[str, Any]:
    verify_evaluation_contract(contract)
    lockbox = str(lockbox_id)
    if lockbox not in contract["lockbox_ids"]:
        raise UntouchedEvaluationContractError("untouched_freeze_lockbox_invalid")
    rows = [row for row in validate_prediction_rows(prediction_rows, contract=contract) if row["lockbox_id"] == lockbox]
    if not rows:
        raise UntouchedEvaluationContractError("untouched_freeze_prediction_rows_required")
    if len(rows) != len(prediction_rows):
        raise UntouchedEvaluationContractError("untouched_freeze_cross_lockbox_rows_forbidden")
    sealed_time = _timestamp(sealed_at, "prediction_freeze_sealed_at")
    latest_recorded = max(_timestamp(row["prediction_recorded_at"], "prediction_recorded_at") for row in rows)
    if latest_recorded > sealed_time:
        raise UntouchedEvaluationContractError("untouched_prediction_recorded_after_freeze")
    authority = str(custody_authority or "").strip()
    if not authority:
        raise UntouchedEvaluationContractError("untouched_freeze_custody_authority_required")
    try:
        assert_sha256(str(custody_evidence_sha256))
    except ValueError as exc:
        raise UntouchedEvaluationContractError("untouched_freeze_custody_evidence_hash_invalid") from exc
    snapshot_sha = prediction_snapshot_sha256(rows, contract=contract)
    body = {
        "schema_version": PREDICTION_FREEZE_SCHEMA,
        "evaluator_id": EVALUATOR_ID,
        "family_id": contract["family_id"],
        "implementation_id": contract["implementation_id"],
        "contract_sha256": contract["contract_sha256"],
        "lockbox_id": lockbox,
        "prediction_snapshot_sha256": snapshot_sha,
        "prediction_row_count": len(rows),
        "sealed_at": _timestamp_text(sealed_time),
        "custody_authority": authority,
        "custody_evidence_sha256": str(custody_evidence_sha256),
    }
    return {
        **body,
        "freeze_record_sha256": domain_hash(
            "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:PREDICTION_FREEZE_RECORD",
            canonical_value(body),
        ),
    }


def verify_prediction_freeze_record(
    record: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
    prediction_rows: Sequence[Mapping[str, Any]],
) -> None:
    verify_evaluation_contract(contract)
    if not isinstance(record, Mapping) or record.get("schema_version") != PREDICTION_FREEZE_SCHEMA:
        raise UntouchedEvaluationContractError("untouched_freeze_record_schema_invalid")
    lockbox = str(record.get("lockbox_id") or "")
    if (
        record.get("evaluator_id") != EVALUATOR_ID
        or record.get("family_id") != contract["family_id"]
        or record.get("implementation_id") != contract["implementation_id"]
        or record.get("contract_sha256") != contract["contract_sha256"]
        or lockbox not in contract["lockbox_ids"]
    ):
        raise UntouchedEvaluationContractError("untouched_freeze_record_binding_invalid")
    rows = [row for row in validate_prediction_rows(prediction_rows, contract=contract) if row["lockbox_id"] == lockbox]
    if not rows or int(record.get("prediction_row_count", -1)) != len(rows):
        raise UntouchedEvaluationContractError("untouched_freeze_record_row_count_invalid")
    expected_snapshot = prediction_snapshot_sha256(rows, contract=contract)
    if record.get("prediction_snapshot_sha256") != expected_snapshot:
        raise UntouchedEvaluationContractError("untouched_prediction_snapshot_hash_mismatch")
    sealed_at = _timestamp(record.get("sealed_at"), "prediction_freeze_sealed_at")
    latest_recorded = max(_timestamp(row["prediction_recorded_at"], "prediction_recorded_at") for row in rows)
    if latest_recorded > sealed_at:
        raise UntouchedEvaluationContractError("untouched_prediction_recorded_after_freeze")
    if not str(record.get("custody_authority") or "").strip():
        raise UntouchedEvaluationContractError("untouched_freeze_custody_authority_required")
    try:
        assert_sha256(str(record.get("custody_evidence_sha256") or ""))
    except ValueError as exc:
        raise UntouchedEvaluationContractError("untouched_freeze_custody_evidence_hash_invalid") from exc
    sealed = str(record.get("freeze_record_sha256") or "")
    body = {key: value for key, value in record.items() if key != "freeze_record_sha256"}
    expected = domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:PREDICTION_FREEZE_RECORD",
        canonical_value(body),
    )
    if sealed != expected:
        raise UntouchedEvaluationContractError("untouched_freeze_record_hash_mismatch")


def build_label_open_record(
    *,
    contract: Mapping[str, Any],
    lockbox_id: str,
    prediction_freeze_record: Mapping[str, Any],
    label_rows: Sequence[Mapping[str, Any]],
    utility_rows: Sequence[Mapping[str, Any]],
    opened_at: datetime | str,
    custody_authority: str,
    custody_evidence_sha256: str,
) -> dict[str, Any]:
    verify_evaluation_contract(contract)
    lockbox = str(lockbox_id)
    if prediction_freeze_record.get("lockbox_id") != lockbox:
        raise UntouchedEvaluationContractError("untouched_label_open_freeze_lockbox_mismatch")
    labels = [row for row in validate_label_rows(label_rows, contract=contract) if row["lockbox_id"] == lockbox]
    utility = [row for row in validate_utility_rows(utility_rows, contract=contract) if row["lockbox_id"] == lockbox]
    if not labels or not utility:
        raise UntouchedEvaluationContractError("untouched_label_open_rows_required")
    if len(labels) != len(label_rows) or len(utility) != len(utility_rows):
        raise UntouchedEvaluationContractError("untouched_label_open_cross_lockbox_rows_forbidden")
    opened = _timestamp(opened_at, "label_opened_at")
    sealed = _timestamp(prediction_freeze_record.get("sealed_at"), "prediction_freeze_sealed_at")
    if opened <= sealed:
        raise UntouchedEvaluationContractError("untouched_label_open_must_be_after_prediction_freeze")
    authority = str(custody_authority or "").strip()
    if not authority:
        raise UntouchedEvaluationContractError("untouched_label_open_custody_authority_required")
    try:
        assert_sha256(str(custody_evidence_sha256))
    except ValueError as exc:
        raise UntouchedEvaluationContractError("untouched_label_open_custody_evidence_hash_invalid") from exc
    snapshot_sha = label_snapshot_sha256(labels, utility, contract=contract)
    body = {
        "schema_version": LABEL_OPEN_SCHEMA,
        "evaluator_id": EVALUATOR_ID,
        "family_id": contract["family_id"],
        "implementation_id": contract["implementation_id"],
        "contract_sha256": contract["contract_sha256"],
        "lockbox_id": lockbox,
        "prediction_freeze_record_sha256": prediction_freeze_record["freeze_record_sha256"],
        "label_snapshot_sha256": snapshot_sha,
        "label_row_count": len(labels),
        "utility_row_count": len(utility),
        "opened_at": _timestamp_text(opened),
        "custody_authority": authority,
        "custody_evidence_sha256": str(custody_evidence_sha256),
    }
    return {
        **body,
        "label_open_record_sha256": domain_hash(
            "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:LABEL_OPEN_RECORD",
            canonical_value(body),
        ),
    }


def verify_label_open_record(
    record: Mapping[str, Any],
    *,
    contract: Mapping[str, Any],
    prediction_freeze_record: Mapping[str, Any],
    label_rows: Sequence[Mapping[str, Any]],
    utility_rows: Sequence[Mapping[str, Any]],
) -> None:
    verify_evaluation_contract(contract)
    if not isinstance(record, Mapping) or record.get("schema_version") != LABEL_OPEN_SCHEMA:
        raise UntouchedEvaluationContractError("untouched_label_open_record_schema_invalid")
    lockbox = str(record.get("lockbox_id") or "")
    if (
        record.get("evaluator_id") != EVALUATOR_ID
        or record.get("family_id") != contract["family_id"]
        or record.get("implementation_id") != contract["implementation_id"]
        or record.get("contract_sha256") != contract["contract_sha256"]
        or prediction_freeze_record.get("lockbox_id") != lockbox
        or record.get("prediction_freeze_record_sha256") != prediction_freeze_record.get("freeze_record_sha256")
    ):
        raise UntouchedEvaluationContractError("untouched_label_open_record_binding_invalid")
    labels = [row for row in validate_label_rows(label_rows, contract=contract) if row["lockbox_id"] == lockbox]
    utility = [row for row in validate_utility_rows(utility_rows, contract=contract) if row["lockbox_id"] == lockbox]
    if not labels or not utility:
        raise UntouchedEvaluationContractError("untouched_label_open_rows_required")
    if int(record.get("label_row_count", -1)) != len(labels) or int(record.get("utility_row_count", -1)) != len(utility):
        raise UntouchedEvaluationContractError("untouched_label_open_record_row_count_invalid")
    expected_snapshot = label_snapshot_sha256(labels, utility, contract=contract)
    if record.get("label_snapshot_sha256") != expected_snapshot:
        raise UntouchedEvaluationContractError("untouched_label_snapshot_hash_mismatch")
    opened = _timestamp(record.get("opened_at"), "label_opened_at")
    sealed = _timestamp(prediction_freeze_record.get("sealed_at"), "prediction_freeze_sealed_at")
    if opened <= sealed:
        raise UntouchedEvaluationContractError("untouched_label_open_must_be_after_prediction_freeze")
    if not str(record.get("custody_authority") or "").strip():
        raise UntouchedEvaluationContractError("untouched_label_open_custody_authority_required")
    try:
        assert_sha256(str(record.get("custody_evidence_sha256") or ""))
    except ValueError as exc:
        raise UntouchedEvaluationContractError("untouched_label_open_custody_evidence_hash_invalid") from exc
    sealed_hash = str(record.get("label_open_record_sha256") or "")
    body = {key: value for key, value in record.items() if key != "label_open_record_sha256"}
    expected = domain_hash(
        "PREBREAKOUT_UNTOUCHED_EVALUATOR_V1:LABEL_OPEN_RECORD",
        canonical_value(body),
    )
    if sealed_hash != expected:
        raise UntouchedEvaluationContractError("untouched_label_open_record_hash_mismatch")


def _prediction_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["lockbox_id"]),
        int(row["decision_session_ordinal"]),
        str(row["decision_session_date"]),
        str(row["security_id"]),
        str(row["trading_item_id"]),
        str(row["prediction_id"]),
    )


def _label_sort_key(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["lockbox_id"]),
        int(row["decision_session_ordinal"]),
        str(row["decision_session_date"]),
        str(row["security_id"]),
        str(row["trading_item_id"]),
        str(row["effective_episode_id"]),
    )


def _timestamp(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        except ValueError as exc:
            raise UntouchedEvaluationContractError(f"untouched_{field}_invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise UntouchedEvaluationContractError(f"untouched_{field}_timezone_required")
    return parsed.astimezone(timezone.utc)


def _timestamp_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _finite_float(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise UntouchedEvaluationContractError(f"untouched_{field}_numeric_required") from exc
    if not math.isfinite(parsed):
        raise UntouchedEvaluationContractError(f"untouched_{field}_finite_required")
    return parsed


def _nonnegative_int(value: Any, field: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise UntouchedEvaluationContractError(f"untouched_{field}_integer_required") from exc
    if parsed < 0:
        raise UntouchedEvaluationContractError(f"untouched_{field}_nonnegative_required")
    return parsed


def _binary_weight(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise UntouchedEvaluationContractError(f"untouched_{field}_binary_integer_required")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise UntouchedEvaluationContractError(f"untouched_{field}_binary_integer_required") from exc
    if parsed not in (0, 1):
        raise UntouchedEvaluationContractError(f"untouched_{field}_must_be_zero_or_one")
    return parsed
