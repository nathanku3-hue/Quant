"""Deterministic AOV-0.5A Parent/Child review kernel."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import (
    AOV0Contract,
    DEFAULT_CONTRACT,
    validate_prospective_contract,
)


REVIEW_SCHEMA = "aov0_review_packet_v1"
ACCOUNTING_TOLERANCE = 1e-12


def build_review_packet(
    *,
    parent_simulation: pd.DataFrame,
    child_simulation: pd.DataFrame,
    experiment_id: str,
    parent_node_hash: str,
    child_node_hash: str,
    contract: AOV0Contract = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    validate_prospective_contract(contract)
    required = {"gross_ret", "net_ret", "turnover", "cost"}
    for name, frame in (("parent", parent_simulation), ("child", child_simulation)):
        if not required.issubset(frame.columns):
            raise ValueError(f"aov0_review_missing_simulation_columns:{name}")
        if frame.empty:
            raise ValueError(f"aov0_review_empty_simulation:{name}")
        if not frame.index.equals(parent_simulation.index):
            raise ValueError("aov0_review_calendar_mismatch")
        numeric = frame[list(required)].astype(float)
        if not np.isfinite(numeric.to_numpy(dtype=float)).all():
            raise ValueError(f"aov0_review_non_finite:{name}")

    gross_delta = child_simulation["gross_ret"].astype(float) - parent_simulation["gross_ret"].astype(float)
    cost_delta = child_simulation["cost"].astype(float) - parent_simulation["cost"].astype(float)
    net_delta = child_simulation["net_ret"].astype(float) - parent_simulation["net_ret"].astype(float)
    residual = net_delta - (gross_delta - cost_delta)
    max_abs_residual = float(residual.abs().max())
    accounting_ok = max_abs_residual <= ACCOUNTING_TOLERANCE

    parent_es = expected_shortfall_loss(parent_simulation["net_ret"].astype(float), level=contract.cvar_level)
    child_es = expected_shortfall_loss(child_simulation["net_ret"].astype(float), level=contract.cvar_level)
    es_improvement = parent_es - child_es
    es_improvement_ratio = es_improvement / parent_es if parent_es > 1e-15 else 0.0
    annualized_premium = max(
        0.0,
        float(parent_simulation["net_ret"].mean() - child_simulation["net_ret"].mean()) * 252.0,
    )

    if not accounting_ok:
        status = "ACCOUNTING_FAILURE"
    elif child_es > parent_es + 1e-15:
        status = "HAZARD_HURT_THIS_EPISODE"
    elif (
        es_improvement_ratio >= contract.insurance_materiality_floor_ratio
        and annualized_premium <= contract.insurance_premium_ceiling_annual_return
    ):
        status = "HAZARD_HELPED_THIS_EPISODE"
    elif (
        float(gross_delta.sum()) > ACCOUNTING_TOLERANCE
        and float(net_delta.sum()) <= ACCOUNTING_TOLERANCE
    ):
        status = "COST_DOMINATED"
    else:
        status = "INSUFFICIENT_EVIDENCE"

    payload = {
        "schema_version": REVIEW_SCHEMA,
        "experiment_id": experiment_id,
        "parent_node_hash": parent_node_hash,
        "child_node_hash": child_node_hash,
        "accounting": {
            "max_abs_reconciliation_residual": max_abs_residual,
            "tolerance": ACCOUNTING_TOLERANCE,
            "status": "PASS" if accounting_ok else "FAIL",
            "gross_delta_sum": float(gross_delta.sum()),
            "cost_delta_sum": float(cost_delta.sum()),
            "net_delta_sum": float(net_delta.sum()),
        },
        "insurance": {
            "endpoint": f"CVaR_{contract.cvar_level:.2f}",
            "parent_expected_shortfall_loss": parent_es,
            "child_expected_shortfall_loss": child_es,
            "improvement": es_improvement,
            "improvement_ratio": es_improvement_ratio,
            "materiality_floor_ratio": contract.insurance_materiality_floor_ratio,
            "annualized_premium": annualized_premium,
            "premium_ceiling_annual_return": contract.insurance_premium_ceiling_annual_return,
        },
        "status": status,
        "mutation_authority": "NONE_SINGLE_EPISODE_CANNOT_TRIGGER_STRUCTURAL_MUTATION",
        "financial_alpha_evidence": 0,
    }
    payload["review_packet_hash"] = domain_hash(
        "AOV0:REVIEW_PACKET:V1", _canonical_hash_value(payload)
    )
    return payload


def verify_review_packet(payload: dict[str, Any]) -> None:
    packet_hash = payload.get("review_packet_hash")
    body = {key: value for key, value in payload.items() if key != "review_packet_hash"}
    expected = domain_hash("AOV0:REVIEW_PACKET:V1", _canonical_hash_value(body))
    if packet_hash != expected:
        raise ValueError("aov0_review_packet_hash_mismatch")
    accounting = payload.get("accounting") or {}
    if accounting.get("status") != "PASS":
        raise ValueError("aov0_review_accounting_not_reconciled")


def _canonical_hash_value(value: Any) -> Any:
    if isinstance(value, float):
        return format(value, ".17g")
    if isinstance(value, dict):
        return {str(key): _canonical_hash_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_hash_value(item) for item in value]
    return value


def expected_shortfall_loss(net_returns: pd.Series, *, level: float) -> float:
    values = np.sort(pd.to_numeric(net_returns, errors="raise").to_numpy(dtype=float))
    if values.size == 0:
        raise ValueError("aov0_review_returns_empty")
    tail_count = max(1, int(np.ceil(values.size * (1.0 - level))))
    worst = values[:tail_count]
    return max(0.0, float(-worst.mean()))
