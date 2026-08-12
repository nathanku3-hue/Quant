"""Zero-authority prediction sealing for VOL_SQUEEZE_BREAKOUT_v1 M0."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import utc_datetime
from research.alpha_pit_v1.manifests import canonical_value
from research.vol_squeeze_breakout_v1.contracts import (
    ARTIFACT_NAMESPACE,
    CONFIRMATION_ROLE_ID,
    FAMILY_ID,
    GUARDIAN_CONTRACT_SHA256,
    IMPLEMENTATION_ID,
    PREDICTION_LEDGER_SCOPE,
    PREDICTION_SCHEMA,
    PRIMARY_HORIZON_SESSIONS,
    PRIMARY_LABEL_SPEC_ID,
    SEARCH_FAMILY_ID,
    SECONDARY_HORIZON_SESSIONS,
    SECONDARY_LABEL_SPEC_ID,
    TRIAL_BUDGET_MAX,
    TRIAL_LEDGER_SCOPE,
)
from research.vol_squeeze_breakout_v1.features import compute_m0_features
from research.vol_squeeze_breakout_v1.model import score_m0_features
from research.vol_squeeze_breakout_v1.pit_packet import verify_vsb_input_packet


def run_and_seal_vsb_m0(
    input_packet: Mapping[str, Any],
    *,
    prediction_made_at: datetime,
) -> dict[str, Any]:
    """Run the frozen M0 transform/ranker and seal one immutable research prediction."""

    verify_vsb_input_packet(input_packet)
    if input_packet.get("implementation_id") != IMPLEMENTATION_ID:
        raise ValueError("vsb_runner_implementation_id_invalid")
    made_at = utc_datetime(prediction_made_at)
    knowledge_cutoff = datetime.fromisoformat(str(input_packet["as_of"]).replace("Z", "+00:00"))
    if made_at <= knowledge_cutoff:
        raise ValueError("vsb_prediction_must_be_after_knowledge_cutoff")

    features = compute_m0_features(input_packet)
    model_output = score_m0_features(features)
    prediction_time = made_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
    decision_date = str(input_packet.get("decision_date") or input_packet["decision_session_date"])

    rows: list[dict[str, Any]] = []
    for row in model_output["rows"]:
        support = bool(row["trigger"]) and float(row["forecast_score"]) > 0
        row_prediction_id = domain_hash(
            "VOL_SQUEEZE_BREAKOUT_V1:SECURITY_PREDICTION_ID",
            canonical_value(
                {
                    "family_id": FAMILY_ID,
                    "implementation_id": IMPLEMENTATION_ID,
                    "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
                    "input_packet_sha256": input_packet["input_packet_sha256"],
                    "security_id": row["security_id"],
                    "prediction_made_at": prediction_time,
                }
            ),
        )
        rows.append(
            {
                "prediction_id": row_prediction_id,
                "security_id": row["security_id"],
                "support": support,
                "trigger": bool(row["trigger"]),
                "forecast_score": row["forecast_score"],
                "reason_codes": list(row["reason_codes"]),
            }
        )

    identity_body = {
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
        "decision_context_id": input_packet["decision_context_id"],
        "decision_date": decision_date,
        "risk_set_id": input_packet["risk_set_id"],
        "input_packet_sha256": input_packet["input_packet_sha256"],
        "prediction_made_at": prediction_time,
    }
    prediction_id = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:PREDICTION_ID",
        canonical_value(identity_body),
    )
    body = {
        "schema_version": PREDICTION_SCHEMA,
        "prediction_id": prediction_id,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "confirmation_role_id": CONFIRMATION_ROLE_ID,
        "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
        "trial_budget_max": TRIAL_BUDGET_MAX,
        "material_trials_consumed": 1,
        "prediction_ledger_scope": PREDICTION_LEDGER_SCOPE,
        "trial_ledger_scope": TRIAL_LEDGER_SCOPE,
        "artifact_namespace": ARTIFACT_NAMESPACE,
        "research_mode": input_packet["research_mode"],
        "decision_context_id": input_packet["decision_context_id"],
        "decision_date": decision_date,
        "decision_session_date": input_packet["decision_session_date"],
        "knowledge_cutoff": input_packet["as_of"],
        "prediction_made_at": prediction_time,
        "risk_set_id": input_packet["risk_set_id"],
        "primary_label_spec_id": PRIMARY_LABEL_SPEC_ID,
        "secondary_label_spec_id": SECONDARY_LABEL_SPEC_ID,
        "primary_horizon_sessions": PRIMARY_HORIZON_SESSIONS,
        "secondary_horizon_sessions": SECONDARY_HORIZON_SESSIONS,
        "input_packet_sha256": input_packet["input_packet_sha256"],
        "feature_packet_sha256": features["feature_packet_sha256"],
        "model_output_sha256": model_output["model_output_sha256"],
        "rows": rows,
        "risk_set_count": model_output["risk_set_count"],
        "support_count": model_output["support_count"],
        "support_breadth": model_output["support_breadth"],
        "outcome_status": "UNMATURED_NOT_EVALUATED",
        "authority_class": "SEALED_RESEARCH_PREDICTION_ZERO_FINANCIAL_AUTHORITY",
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "broker_orders": "FORBIDDEN",
        "parent_child_mutation": "FORBIDDEN",
        "retune_authority": "NONE",
        "prebreakout_authority": "NONE",
    }
    prediction_sha256 = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:PREDICTION",
        canonical_value(body),
    )
    return {
        **body,
        "prediction_sha256": prediction_sha256,
        "prediction_batch_sha256": prediction_sha256,
    }


def seal_m0_predictions(
    *,
    input_packet: Mapping[str, Any],
    prediction_made_at: datetime,
) -> dict[str, Any]:
    return run_and_seal_vsb_m0(input_packet, prediction_made_at=prediction_made_at)


def verify_vsb_prediction(prediction: Mapping[str, Any]) -> None:
    if not isinstance(prediction, Mapping):
        raise ValueError("vsb_prediction_mapping_required")
    if prediction.get("schema_version") != PREDICTION_SCHEMA or prediction.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_prediction_identity_invalid")
    if prediction.get("implementation_id") != IMPLEMENTATION_ID or prediction.get("search_family_id") != SEARCH_FAMILY_ID:
        raise ValueError("vsb_prediction_search_identity_invalid")
    if prediction.get("confirmation_role_id") != CONFIRMATION_ROLE_ID:
        raise ValueError("vsb_prediction_confirmation_role_invalid")
    if prediction.get("guardian_contract_sha256") != GUARDIAN_CONTRACT_SHA256:
        raise ValueError("vsb_prediction_guardian_contract_invalid")
    if prediction.get("trial_budget_max") != 1 or prediction.get("material_trials_consumed") != 1:
        raise ValueError("vsb_prediction_trial_budget_invalid")
    if prediction.get("outcome_status") != "UNMATURED_NOT_EVALUATED":
        raise ValueError("vsb_prediction_outcome_status_invalid")
    if (
        prediction.get("financial_alpha_evidence") != 0
        or prediction.get("capital_authority") != "NONE"
        or prediction.get("broker_orders") != "FORBIDDEN"
        or prediction.get("parent_child_mutation") != "FORBIDDEN"
        or prediction.get("retune_authority") != "NONE"
        or prediction.get("prebreakout_authority") != "NONE"
    ):
        raise ValueError("vsb_prediction_authority_invalid")
    rows = prediction.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("vsb_prediction_rows_required")
    if len(rows) != int(prediction.get("risk_set_count", -1)):
        raise ValueError("vsb_prediction_risk_set_count_invalid")
    if sum(bool(row.get("support")) for row in rows) != int(prediction.get("support_count", -1)):
        raise ValueError("vsb_prediction_support_count_invalid")

    identity_body = {
        "family_id": prediction["family_id"],
        "implementation_id": prediction["implementation_id"],
        "guardian_contract_sha256": prediction["guardian_contract_sha256"],
        "decision_context_id": prediction["decision_context_id"],
        "decision_date": prediction["decision_date"],
        "risk_set_id": prediction["risk_set_id"],
        "input_packet_sha256": prediction["input_packet_sha256"],
        "prediction_made_at": prediction["prediction_made_at"],
    }
    expected_id = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:PREDICTION_ID",
        canonical_value(identity_body),
    )
    if prediction.get("prediction_id") != expected_id:
        raise ValueError("vsb_prediction_id_mismatch")

    sealed = str(prediction.get("prediction_sha256") or "")
    batch_sealed = str(prediction.get("prediction_batch_sha256") or sealed)
    body = {
        key: value
        for key, value in prediction.items()
        if key not in {"prediction_sha256", "prediction_batch_sha256"}
    }
    expected = domain_hash("VOL_SQUEEZE_BREAKOUT_V1:PREDICTION", canonical_value(body))
    if sealed != expected or batch_sealed != expected:
        raise ValueError("vsb_prediction_batch_hash_mismatch")


def verify_prediction_batch(batch: Mapping[str, Any]) -> None:
    try:
        verify_vsb_prediction(batch)
    except ValueError as exc:
        if str(exc) == "vsb_prediction_hash_mismatch":
            raise ValueError("vsb_prediction_batch_hash_mismatch") from exc
        raise
