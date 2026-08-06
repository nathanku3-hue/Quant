from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pandas as pd
import pytest

from research.aov0.contracts import DEFAULT_CONTRACT
from research.aov0.review import build_review_packet, verify_review_packet


DEVELOPMENT_CONTRACT = replace(
    DEFAULT_CONTRACT,
    insurance_materiality_floor_ratio=0.05,
    insurance_premium_ceiling_annual_return=0.005,
)


def _simulation(gross: list[float], cost: list[float], net: list[float] | None = None) -> pd.DataFrame:
    index = pd.date_range("2026-01-02", periods=len(gross), freq="B")
    gross_s = pd.Series(gross, index=index, dtype=float)
    cost_s = pd.Series(cost, index=index, dtype=float)
    net_s = gross_s - cost_s if net is None else pd.Series(net, index=index, dtype=float)
    return pd.DataFrame(
        {
            "gross_ret": gross_s,
            "net_ret": net_s,
            "turnover": [0.0] * len(index),
            "cost": cost_s,
        },
        index=index,
    )


def _review(parent: pd.DataFrame, child: pd.DataFrame) -> dict[str, object]:
    return build_review_packet(
        parent_simulation=parent,
        child_simulation=child,
        experiment_id="e" * 64,
        parent_node_hash="p" * 64,
        child_node_hash="c" * 64,
        contract=DEVELOPMENT_CONTRACT,
    )


def test_review_classifies_material_insurance_help() -> None:
    parent = _simulation([-0.10, 0.01, 0.01, 0.01, 0.01], [0.0] * 5)
    child = _simulation([-0.05, 0.01, 0.01, 0.01, 0.01], [0.0] * 5)
    packet = _review(parent, child)
    assert packet["status"] == "HAZARD_HELPED_THIS_EPISODE"
    assert packet["accounting"]["status"] == "PASS"
    assert packet["mutation_authority"] == "NONE_SINGLE_EPISODE_CANNOT_TRIGGER_STRUCTURAL_MUTATION"
    verify_review_packet(packet)


def test_review_classifies_harmful_insurance() -> None:
    parent = _simulation([-0.05, 0.01, 0.01, 0.01, 0.01], [0.0] * 5)
    child = _simulation([-0.10, 0.01, 0.01, 0.01, 0.01], [0.0] * 5)
    packet = _review(parent, child)
    assert packet["status"] == "HAZARD_HURT_THIS_EPISODE"
    verify_review_packet(packet)


def test_review_classifies_cost_dominated_when_gross_improves_but_net_does_not() -> None:
    parent = _simulation([-0.01] * 5, [0.0] * 5)
    child = _simulation([-0.009] * 5, [0.001] * 5)
    packet = _review(parent, child)
    assert packet["status"] == "COST_DOMINATED"
    verify_review_packet(packet)


def test_accounting_failure_blocks_review_authority() -> None:
    parent = _simulation([0.0, 0.0], [0.0, 0.0])
    child = _simulation([0.01, 0.01], [0.0, 0.0], net=[0.0, 0.0])
    packet = _review(parent, child)
    assert packet["status"] == "ACCOUNTING_FAILURE"
    assert packet["accounting"]["status"] == "FAIL"
    with pytest.raises(ValueError, match="accounting_not_reconciled"):
        verify_review_packet(packet)


def test_review_packet_hash_tamper_fails_closed() -> None:
    parent = _simulation([-0.05, 0.01], [0.0, 0.0])
    child = _simulation([-0.04, 0.01], [0.0, 0.0])
    packet = _review(parent, child)
    tampered = deepcopy(packet)
    tampered["insurance"]["parent_expected_shortfall_loss"] = 999.0
    with pytest.raises(ValueError, match="hash_mismatch"):
        verify_review_packet(tampered)


def test_review_rejects_nonfinite_or_missing_simulation_evidence() -> None:
    parent = _simulation([0.0, 0.0], [0.0, 0.0])
    child = _simulation([0.0, 0.0], [0.0, 0.0])
    child.loc[child.index[0], "net_ret"] = float("nan")
    with pytest.raises(ValueError, match="non_finite:child"):
        _review(parent, child)

    missing = parent.drop(columns=["cost"])
    with pytest.raises(ValueError, match="missing_simulation_columns:parent"):
        _review(missing, parent)
