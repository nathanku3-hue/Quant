from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from research.aov0.contracts import DEFAULT_CONTRACT, validate_contract
from research.aov0.cube import build_vertical_cube
from research.aov0.dag import HashDagCache, run_policy_dag
from research.aov0.policy import (
    DEFAULT_MUTATION,
    assert_rule100_equivalence,
    build_child_weights,
    build_parent_weights,
)


COMPUTED_AT = "2026-08-06T18:00:00Z"


def test_frozen_contract_closes_p0_defaults() -> None:
    validate_contract(DEFAULT_CONTRACT)
    assert DEFAULT_CONTRACT.permanent_id_type == "permno"
    assert DEFAULT_CONTRACT.universe_rule == "RULE100_DATE_LOCAL_ELIGIBLE_UNIVERSE"
    assert DEFAULT_CONTRACT.total_return_authority == "PIT_TOTAL_RETURN_MATRIX_ONLY"
    assert DEFAULT_CONTRACT.f_proxy_formula.startswith("robust_z(")
    assert DEFAULT_CONTRACT.c_proxy_formula == "ewma20(abs(F_proxy))"
    assert DEFAULT_CONTRACT.cvar_level == 0.95
    assert DEFAULT_CONTRACT.insurance_materiality_floor_ratio == 0.05
    assert DEFAULT_CONTRACT.insurance_premium_ceiling_annual_return == 0.005
    assert DEFAULT_CONTRACT.economic_cash_source == "OFFICIAL_SOFR"
    assert DEFAULT_CONTRACT.economic_cash_quote_convention == "SOFR_PERCENT_MINUS_25BP_ACT_360_SIMPLE_ACCRUAL"
    assert DEFAULT_CONTRACT.sleeve_horizon_calendar_days == 30
    assert len(DEFAULT_CONTRACT.contract_hash) == 64


def test_cube_is_pit_content_addressed_and_dimensionally_bounded(aov_primitives: pd.DataFrame) -> None:
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    assert set(("Q", "M", "F_proxy", "C_proxy", "L", "R", "U")).issubset(cube.frame.columns)
    assert np.isfinite(cube.frame[["Q", "M", "F_proxy", "C_proxy", "L", "R", "U"]]).all().all()
    assert (cube.frame["C_proxy"] >= 0).all()
    assert cube.frame["L"].between(0, 1).all()
    assert cube.frame["U"].between(0, 1).all()
    assert cube.frame["contract_hash"].nunique() == 1
    assert cube.frame["formula_hash"].nunique() == 1

    mutated = aov_primitives.copy()
    mutated.loc[0, "dollar_volume"] += 1.0
    second = build_vertical_cube(mutated, computed_at=COMPUTED_AT)
    assert cube.source_hash != second.source_hash
    assert cube.cube_hash != second.cube_hash


def test_cube_rejects_future_knowledge_and_missing_permanent_id(aov_primitives: pd.DataFrame) -> None:
    future = aov_primitives.copy()
    future.loc[0, "known_at"] = "2026-08-07T00:00:00Z"
    with pytest.raises(ValueError, match="aov0_cube_future_knowledge"):
        build_vertical_cube(future, computed_at=COMPUTED_AT)

    missing_id = aov_primitives.copy()
    missing_id.loc[0, "permno"] = None
    with pytest.raises(ValueError, match="aov0_cube_permno_required"):
        build_vertical_cube(missing_id, computed_at=COMPUTED_AT)


def test_rule100_parent_child_preserve_budget_and_child_only_reduces_risk(aov_primitives, rule100_weights) -> None:
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    assert_rule100_equivalence(rule100_weights, cube)
    parent = build_parent_weights(rule100_weights, cube)
    child = build_child_weights(parent, cube)

    pd.testing.assert_series_equal(parent.sum(axis=1), rule100_weights.sum(axis=1), check_names=False, atol=1e-12, rtol=0)
    assert (parent <= DEFAULT_CONTRACT.single_name_cap + 1e-12).all().all()
    assert (child <= parent + 1e-12).all().all()
    assert (child.sum(axis=1) <= parent.sum(axis=1) + 1e-12).all()
    assert parent.ne(parent.shift()).any(axis=1).tolist() == rule100_weights.ne(rule100_weights.shift()).any(axis=1).tolist()
    assert child.ne(child.shift()).any(axis=1).tolist() == parent.ne(parent.shift()).any(axis=1).tolist()


def test_dag_recomputes_only_child_when_mutation_changes(aov_primitives, rule100_weights) -> None:
    cube = build_vertical_cube(aov_primitives, computed_at=COMPUTED_AT)
    cache = HashDagCache()
    first = run_policy_dag(rule100_weights, cube, cache=cache)
    changed_mutation = replace(DEFAULT_MUTATION, mutation_id="AOV0_REVERSAL_INSURANCE_EDGE_V1B", eta=0.25)
    second = run_policy_dag(rule100_weights, cube, mutation=changed_mutation, cache=cache)
    assert first.cache_hits == 0
    assert first.cache_misses == 3
    assert second.cache_hits == 2
    assert second.cache_misses == 1
    assert second.node_hashes["rule100"] == first.node_hashes["rule100"]
    assert second.node_hashes["parent"] == first.node_hashes["parent"]
    assert second.node_hashes["child"] != first.node_hashes["child"]
