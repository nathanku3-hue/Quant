"""Deterministic ETF-relative M0 model for SECTOR_ROTATION_ALPHA_v1."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.sector_rotation_alpha_v1.contracts import FAMILY_ID, MODEL_OUTPUT_SCHEMA
from research.sector_rotation_alpha_v1.features import verify_m0_features


_OVERLAY_COMPONENTS = (
    "relative_strength_20",
    "relative_strength_60",
    "dollar_volume_participation",
)
_INCUMBENT_COMPONENTS = (
    "relative_strength_20",
    "relative_strength_60",
)


def score_m0_features(features: Mapping[str, Any]) -> dict[str, Any]:
    """Score ETF sector leadership with equal-rank relative strength + participation."""

    verify_m0_features(features)
    rows = features.get("rows")
    if not isinstance(rows, list):
        raise ValueError("sra_feature_rows_required")
    ready_rows = [row for row in rows if row.get("feature_status") == "READY"]

    ranks: dict[str, dict[str, float]] = {}
    for component in _OVERLAY_COMPONENTS:
        values = [(str(row["security_id"]), float(row[component])) for row in ready_rows]
        ranks[component] = _percentile_ranks(values)

    output_rows: list[dict[str, Any]] = []
    support_count = 0
    incumbent_support_count = 0
    for row in sorted(rows, key=lambda item: str(item.get("sector_key") or "")):
        security_id = str(row.get("security_id") or "")
        sector_key = str(row.get("sector_key") or "")
        if row.get("feature_status") != "READY":
            output_rows.append(
                {
                    "security_id": security_id,
                    "sector_key": sector_key,
                    "trigger": False,
                    "support": False,
                    "raw_score": "0",
                    "forecast_score": "0",
                    "incumbent_support": False,
                    "incumbent_score": "0",
                    "reason_codes": ["INSUFFICIENT_OR_INVALID_M0_HISTORY", *list(row.get("invalid_reasons") or [])],
                }
            )
            continue

        rel20 = float(row["relative_strength_20"])
        rel60 = float(row["relative_strength_60"])
        participation = float(row["dollar_volume_participation"])
        incumbent_support = rel20 > 0 and rel60 > 0
        trigger = incumbent_support and participation > 0
        raw_score = sum(ranks[component][security_id] for component in _OVERLAY_COMPONENTS) / len(_OVERLAY_COMPONENTS)
        incumbent_score = sum(ranks[component][security_id] for component in _INCUMBENT_COMPONENTS) / len(_INCUMBENT_COMPONENTS)
        forecast_score = raw_score if trigger else 0.0
        reasons: list[str] = []
        if rel20 <= 0:
            reasons.append("NO_RELATIVE_STRENGTH_20")
        if rel60 <= 0:
            reasons.append("NO_RELATIVE_STRENGTH_60")
        if participation <= 0:
            reasons.append("NO_ETF_DOLLAR_VOLUME_PARTICIPATION")
        if incumbent_support:
            incumbent_support_count += 1
        if trigger:
            reasons.append("M0_TRIGGER")
            support_count += 1
        output_rows.append(
            {
                "security_id": security_id,
                "sector_key": sector_key,
                "trigger": trigger,
                "support": trigger and forecast_score > 0,
                "raw_score": format(raw_score, ".17g"),
                "forecast_score": format(forecast_score, ".17g"),
                "incumbent_support": incumbent_support,
                "incumbent_score": format(incumbent_score, ".17g"),
                "reason_codes": reasons,
            }
        )

    risk_set_count = len(output_rows)
    support_breadth = support_count / risk_set_count if risk_set_count else 0.0
    incumbent_support_breadth = incumbent_support_count / risk_set_count if risk_set_count else 0.0
    body = {
        "schema_version": MODEL_OUTPUT_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": features["implementation_id"],
        "decision_session_date": features["decision_session_date"],
        "feature_packet_sha256": features["feature_packet_sha256"],
        "percentile_rank_rule": "AVERAGE_ONE_BASED_RANK_DIVIDED_BY_FINITE_CROSS_SECTION_COUNT",
        "overlay_definition": "I_PLUS_X_EQUALS_RELSTR20_RELSTR60_PLUS_ETF_DOLLAR_VOLUME_PARTICIPATION",
        "incumbent_definition": "I_EQUALS_RELSTR20_RELSTR60_ONLY",
        "rows": output_rows,
        "risk_set_count": risk_set_count,
        "support_count": support_count,
        "support_breadth": format(support_breadth, ".17g"),
        "incumbent_support_count": incumbent_support_count,
        "incumbent_support_breadth": format(incumbent_support_breadth, ".17g"),
        "stock_sector_map_used": False,
        "stock_breadth_used": False,
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    model_output_sha256 = domain_hash(
        "SECTOR_ROTATION_ALPHA_V1:M0_MODEL_OUTPUT",
        canonical_value(body),
    )
    return {**body, "model_output_sha256": model_output_sha256}


def verify_m0_model_output(model_output: Mapping[str, Any]) -> None:
    if not isinstance(model_output, Mapping):
        raise ValueError("sra_model_output_mapping_required")
    if model_output.get("schema_version") != MODEL_OUTPUT_SCHEMA or model_output.get("family_id") != FAMILY_ID:
        raise ValueError("sra_model_output_identity_invalid")
    if model_output.get("financial_alpha_evidence") != 0 or model_output.get("capital_authority") != "NONE":
        raise ValueError("sra_model_output_authority_invalid")
    if model_output.get("stock_sector_map_used") is not False or model_output.get("stock_breadth_used") is not False:
        raise ValueError("sra_model_output_stock_dependency_forbidden")
    rows = model_output.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("sra_model_output_rows_required")
    if len(rows) != int(model_output.get("risk_set_count", -1)):
        raise ValueError("sra_model_output_risk_set_count_invalid")
    if sum(bool(row.get("support")) for row in rows) != int(model_output.get("support_count", -1)):
        raise ValueError("sra_model_output_support_count_invalid")
    if sum(bool(row.get("incumbent_support")) for row in rows) != int(model_output.get("incumbent_support_count", -1)):
        raise ValueError("sra_model_output_incumbent_support_count_invalid")
    sealed = str(model_output.get("model_output_sha256") or "")
    body = {key: value for key, value in model_output.items() if key != "model_output_sha256"}
    expected = domain_hash("SECTOR_ROTATION_ALPHA_V1:M0_MODEL_OUTPUT", canonical_value(body))
    if sealed != expected:
        raise ValueError("sra_model_output_hash_mismatch")


def _percentile_ranks(values: Sequence[tuple[str, float]]) -> dict[str, float]:
    if not values:
        return {}
    grouped: dict[float, list[str]] = defaultdict(list)
    for security_id, value in values:
        grouped[value].append(security_id)
    result: dict[str, float] = {}
    position = 1
    count = len(values)
    for value in sorted(grouped):
        security_ids = sorted(grouped[value])
        first = position
        last = position + len(security_ids) - 1
        average_rank = (first + last) / 2.0
        percentile = average_rank / count
        for security_id in security_ids:
            result[security_id] = percentile
        position = last + 1
    return result
