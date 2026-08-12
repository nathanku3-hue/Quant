"""Zero-authority prediction sealing for SECTOR_ROTATION_ALPHA_v1 M0."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import utc_datetime
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import (
    ARTIFACT_NAMESPACE,
    FAMILY_ID,
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
from research.sector_rotation_alpha_v1.features import compute_m0_features
from research.sector_rotation_alpha_v1.model import score_m0_features
from research.sector_rotation_alpha_v1.pit_packet import verify_sector_rotation_input_packet
from research.sector_rotation_alpha_v1.trial_ledger import verify_code_manifest, verify_trial_receipt


def run_and_seal_sector_rotation_m0(
    input_packet: Mapping[str, Any],
    *,
    trial_receipt: Mapping[str, Any],
    prediction_made_at: datetime,
) -> dict[str, Any]:
    """Run frozen ETF M0 and seal one immutable future-directed prediction batch."""

    verify_sector_rotation_input_packet(input_packet)
    verify_trial_receipt(trial_receipt)
    code_manifest = trial_receipt.get("code_manifest")
    if not isinstance(code_manifest, Mapping):
        raise ValueError("sra_runner_code_manifest_required")
    verify_code_manifest(code_manifest, repo_root=Path(__file__).resolve().parents[2])
    if input_packet.get("implementation_id") != IMPLEMENTATION_ID:
        raise ValueError("sra_runner_implementation_id_invalid")
    if trial_receipt.get("implementation_id") != IMPLEMENTATION_ID:
        raise ValueError("sra_runner_trial_implementation_mismatch")

    made_at = utc_datetime(prediction_made_at)
    knowledge_cutoff = datetime.fromisoformat(str(input_packet["as_of"]).replace("Z", "+00:00"))
    if made_at <= knowledge_cutoff:
        raise ValueError("sra_prediction_must_be_after_knowledge_cutoff")

    features = compute_m0_features(input_packet)
    model_output = score_m0_features(features)
    prediction_time = made_at.isoformat(timespec="microseconds").replace("+00:00", "Z")
    decision_date = str(input_packet.get("decision_date") or input_packet["decision_session_date"])

    rows: list[dict[str, Any]] = []
    for row in model_output["rows"]:
        row_prediction_id = domain_hash(
            "SECTOR_ROTATION_ALPHA_V1:SECURITY_PREDICTION_ID",
            canonical_value(
                {
                    "family_id": FAMILY_ID,
                    "implementation_id": IMPLEMENTATION_ID,
                    "input_packet_sha256": input_packet["input_packet_sha256"],
                    "security_id": row["security_id"],
                    "sector_key": row["sector_key"],
                    "prediction_made_at": prediction_time,
                }
            ),
        )
        rows.append(
            {
                "prediction_id": row_prediction_id,
                "security_id": row["security_id"],
                "sector_key": row["sector_key"],
                "support": bool(row["support"]),
                "trigger": bool(row["trigger"]),
                "forecast_score": row["forecast_score"],
                "incumbent_support": bool(row["incumbent_support"]),
                "incumbent_score": row["incumbent_score"],
                "reason_codes": list(row["reason_codes"]),
            }
        )

    identity_body = {
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "decision_context_id": input_packet["decision_context_id"],
        "decision_date": decision_date,
        "risk_set_id": input_packet["risk_set_id"],
        "input_packet_sha256": input_packet["input_packet_sha256"],
        "trial_receipt_sha256": trial_receipt["trial_receipt_sha256"],
        "prediction_made_at": prediction_time,
    }
    prediction_id = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:PREDICTION_ID",
        canonical_value(identity_body),
    )
    body = {
        "schema_version": PREDICTION_SCHEMA,
        "prediction_id": prediction_id,
        "family_id": FAMILY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "search_family_id": SEARCH_FAMILY_ID,
        "trial_budget_max": TRIAL_BUDGET_MAX,
        "material_trials_consumed": 1,
        "trial_receipt_sha256": trial_receipt["trial_receipt_sha256"],
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
        "incumbent_support_count": model_output["incumbent_support_count"],
        "incumbent_support_breadth": model_output["incumbent_support_breadth"],
        "outcome_status": "UNMATURED_NOT_EVALUATED",
        "authority_class": "SEALED_RESEARCH_PREDICTION_ZERO_FINANCIAL_AUTHORITY",
        "stock_sector_map_used": False,
        "stock_breadth_used": False,
        "underlying_stock_membership_used": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
        "broker_orders": "FORBIDDEN",
        "parent_child_mutation": "FORBIDDEN",
    }
    prediction_sha256 = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:PREDICTION",
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
    trial_receipt: Mapping[str, Any],
    prediction_made_at: datetime,
) -> dict[str, Any]:
    return run_and_seal_sector_rotation_m0(
        input_packet,
        trial_receipt=trial_receipt,
        prediction_made_at=prediction_made_at,
    )


def verify_prediction_batch(batch: Mapping[str, Any]) -> None:
    if not isinstance(batch, Mapping):
        raise ValueError("sra_prediction_mapping_required")
    if batch.get("schema_version") != PREDICTION_SCHEMA or batch.get("family_id") != FAMILY_ID:
        raise ValueError("sra_prediction_identity_invalid")
    if batch.get("implementation_id") != IMPLEMENTATION_ID or batch.get("search_family_id") != SEARCH_FAMILY_ID:
        raise ValueError("sra_prediction_search_identity_invalid")
    if batch.get("trial_budget_max") != 1 or batch.get("material_trials_consumed") != 1:
        raise ValueError("sra_prediction_trial_budget_invalid")
    if batch.get("prediction_ledger_scope") != PREDICTION_LEDGER_SCOPE or batch.get("trial_ledger_scope") != TRIAL_LEDGER_SCOPE:
        raise ValueError("sra_prediction_ledger_scope_invalid")
    if batch.get("outcome_status") != "UNMATURED_NOT_EVALUATED":
        raise ValueError("sra_prediction_outcome_status_invalid")
    if (
        batch.get("financial_alpha_evidence") != 0
        or batch.get("capital_authority") != "NONE"
        or batch.get("broker_orders") != "FORBIDDEN"
        or batch.get("parent_child_mutation") != "FORBIDDEN"
    ):
        raise ValueError("sra_prediction_authority_invalid")
    for field in ("stock_sector_map_used", "stock_breadth_used", "underlying_stock_membership_used"):
        if batch.get(field) is not False:
            raise ValueError("sra_prediction_stock_dependency_forbidden:" + field)
    rows = batch.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("sra_prediction_rows_required")
    if len(rows) != int(batch.get("risk_set_count", -1)):
        raise ValueError("sra_prediction_risk_set_count_invalid")
    if sum(bool(row.get("support")) for row in rows) != int(batch.get("support_count", -1)):
        raise ValueError("sra_prediction_support_count_invalid")
    if sum(bool(row.get("incumbent_support")) for row in rows) != int(batch.get("incumbent_support_count", -1)):
        raise ValueError("sra_prediction_incumbent_support_count_invalid")

    identity_body = {
        "family_id": batch["family_id"],
        "implementation_id": batch["implementation_id"],
        "decision_context_id": batch["decision_context_id"],
        "decision_date": batch["decision_date"],
        "risk_set_id": batch["risk_set_id"],
        "input_packet_sha256": batch["input_packet_sha256"],
        "trial_receipt_sha256": batch["trial_receipt_sha256"],
        "prediction_made_at": batch["prediction_made_at"],
    }
    expected_id = domain_hash("SECTOR_ROTATION_ALPHA_V1:PREDICTION_ID", canonical_value(identity_body))
    if batch.get("prediction_id") != expected_id:
        raise ValueError("sra_prediction_id_mismatch")

    sealed = str(batch.get("prediction_sha256") or "")
    batch_sealed = str(batch.get("prediction_batch_sha256") or sealed)
    body = {
        key: value
        for key, value in batch.items()
        if key not in {"prediction_sha256", "prediction_batch_sha256"}
    }
    expected = domain_hash("SECTOR_ROTATION_ALPHA_V1:PREDICTION", canonical_value(body))
    if sealed != expected or batch_sealed != expected:
        raise ValueError("sra_prediction_batch_hash_mismatch")
