"""Deterministic equal-rank M0 model for VOL_SQUEEZE_BREAKOUT_v1."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping, Sequence

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.manifests import canonical_value
from research.vol_squeeze_breakout_v1.contracts import FAMILY_ID, MODEL_OUTPUT_SCHEMA
from research.vol_squeeze_breakout_v1.features import verify_m0_features


_COMPONENTS = ("compression", "breakout", "volume_expansion")


def score_m0_features(features: Mapping[str, Any]) -> dict[str, Any]:
    """Percentile-rank finite M0 components with equal weights and zero thresholds."""

    verify_m0_features(features)
    rows = features.get("rows")
    if not isinstance(rows, list):
        raise ValueError("vsb_feature_rows_required")

    ready_rows = [row for row in rows if row.get("feature_status") == "READY"]
    ranks: dict[str, dict[str, float]] = {}
    for component in _COMPONENTS:
        values = [(str(row["security_id"]), float(row[component])) for row in ready_rows]
        ranks[component] = _percentile_ranks(values)

    output_rows: list[dict[str, Any]] = []
    support_count = 0
    for row in sorted(rows, key=lambda item: str(item.get("security_id") or "")):
        security_id = str(row.get("security_id") or "")
        if row.get("feature_status") != "READY":
            output_rows.append(
                {
                    "security_id": security_id,
                    "trigger": False,
                    "raw_score": "0",
                    "forecast_score": "0",
                    "reason_codes": ["INSUFFICIENT_OR_INVALID_M0_HISTORY", *list(row.get("invalid_reasons") or [])],
                }
            )
            continue

        compression = float(row["compression"])
        breakout = float(row["breakout"])
        volume_expansion = float(row["volume_expansion"])
        trigger = compression > 0 and breakout > 0 and volume_expansion > 0
        raw_score = sum(ranks[component][security_id] for component in _COMPONENTS) / len(_COMPONENTS)
        forecast_score = raw_score if trigger else 0.0
        reasons: list[str] = []
        if compression <= 0:
            reasons.append("NO_VOL_COMPRESSION")
        if breakout <= 0:
            reasons.append("NO_BREAKOUT")
        if volume_expansion <= 0:
            reasons.append("NO_VOLUME_EXPANSION")
        if trigger:
            reasons.append("M0_TRIGGER")
            support_count += 1
        output_rows.append(
            {
                "security_id": security_id,
                "trigger": trigger,
                "raw_score": format(raw_score, ".17g"),
                "forecast_score": format(forecast_score, ".17g"),
                "reason_codes": reasons,
            }
        )

    risk_set_count = len(output_rows)
    support_breadth = support_count / risk_set_count if risk_set_count else 0.0
    body = {
        "schema_version": MODEL_OUTPUT_SCHEMA,
        "family_id": FAMILY_ID,
        "implementation_id": features["implementation_id"],
        "decision_session_date": features["decision_session_date"],
        "feature_packet_sha256": features["feature_packet_sha256"],
        "percentile_rank_rule": "AVERAGE_ONE_BASED_RANK_DIVIDED_BY_FINITE_CROSS_SECTION_COUNT",
        "rows": output_rows,
        "risk_set_count": risk_set_count,
        "support_count": support_count,
        "support_breadth": format(support_breadth, ".17g"),
        "financial_alpha_evidence": 0,
        "capital_authority": "NONE",
    }
    model_output_sha256 = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:M0_MODEL_OUTPUT",
        canonical_value(body),
    )
    return {**body, "model_output_sha256": model_output_sha256}


def verify_m0_model_output(model_output: Mapping[str, Any]) -> None:
    if not isinstance(model_output, Mapping):
        raise ValueError("vsb_model_output_mapping_required")
    if model_output.get("schema_version") != MODEL_OUTPUT_SCHEMA or model_output.get("family_id") != FAMILY_ID:
        raise ValueError("vsb_model_output_identity_invalid")
    if model_output.get("financial_alpha_evidence") != 0 or model_output.get("capital_authority") != "NONE":
        raise ValueError("vsb_model_output_authority_invalid")
    sealed = str(model_output.get("model_output_sha256") or "")
    body = {key: value for key, value in model_output.items() if key != "model_output_sha256"}
    expected = domain_hash("VOL_SQUEEZE_BREAKOUT_V1:M0_MODEL_OUTPUT", canonical_value(body))
    if sealed != expected:
        raise ValueError("vsb_model_output_hash_mismatch")


def _percentile_ranks(values: Sequence[tuple[str, float]]) -> dict[str, float]:
    """Return average one-based tie rank divided by N, matching frozen pct-rank semantics."""

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
