"""Deterministic Rule100 control, Parent, and one frozen Child mutation."""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import AOV0Contract, DEFAULT_CONTRACT, validate_contract
from research.aov0.cube import VerticalCube


@dataclass(frozen=True)
class MutationManifest:
    mutation_id: str = "AOV0_REVERSAL_INSURANCE_EDGE_V1"
    changed_edge: str = "PARENT_WEIGHT -> CROWDING_X_ILLIQUIDITY_X_ADVERSE_REGIME_RISK_REDUCTION"
    eta: float = DEFAULT_CONTRACT.child_eta
    hazard_cap: float = DEFAULT_CONTRACT.child_hazard_cap
    can_increase_risk: bool = False

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        return {
            key: (format(value, ".17g") if isinstance(value, float) else value)
            for key, value in payload.items()
        }

    @property
    def manifest_hash(self) -> str:
        return domain_hash("AOV0:MUTATION_MANIFEST:V1", self.to_dict())


DEFAULT_MUTATION = MutationManifest()


def normalize_rule100_control(target_weights: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(target_weights, pd.DataFrame) or target_weights.empty:
        raise ValueError("aov0_rule100_control_missing")
    out = target_weights.copy().astype(float)
    try:
        columns = pd.Index([int(column) for column in out.columns], dtype="int64", name="permno")
    except (TypeError, ValueError) as exc:
        raise ValueError("aov0_rule100_permno_columns_required") from exc
    if len(set(columns)) != len(columns):
        raise ValueError("aov0_rule100_duplicate_permno_columns")
    out.columns = columns
    out.index = pd.DatetimeIndex(pd.to_datetime(out.index)).normalize()
    if not out.index.is_monotonic_increasing or not out.index.is_unique:
        raise ValueError("aov0_rule100_date_index_invalid")
    values = out.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < -1e-12).any():
        raise ValueError("aov0_rule100_weights_invalid")
    if (out.sum(axis=1) > 1.0 + 1e-12).any():
        raise ValueError("aov0_rule100_gross_gt_one")
    return out


def build_parent_weights(
    rule100_weights: pd.DataFrame,
    cube: VerticalCube,
    *,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    dynamic_enabled: bool = True,
) -> pd.DataFrame:
    validate_contract(contract)
    base = normalize_rule100_control(rule100_weights)
    if not dynamic_enabled or contract.parent_strength == 0:
        return base.copy()
    state = _aligned_state(base, cube)
    score = (
        0.10 * state["Q"]
        + 0.20 * state["M"]
        + 0.15 * np.tanh(state["F_proxy"] / 3.0)
        - 0.15 * np.tanh(state["C_proxy"] / 3.0)
        + 0.10 * (2.0 * state["L"] - 1.0)
        + 0.10 * state["R"]
        - 0.10 * state["U"]
    )
    raw = base * np.exp(contract.parent_strength * score)
    raw = raw.where(base > 0.0, 0.0)
    projected = pd.DataFrame(np.nan, index=base.index, columns=base.columns)
    rebalance_mask = base.ne(base.shift(1)).any(axis=1)
    rebalance_mask.iloc[0] = True
    for date in base.index[rebalance_mask]:
        budget = float(base.loc[date].sum())
        projected.loc[date] = _project_budget_with_cap(
            raw.loc[date],
            budget=budget,
            cap=contract.single_name_cap,
        )
    return projected.ffill().fillna(0.0).astype(float)


def build_child_weights(
    parent_weights: pd.DataFrame,
    cube: VerticalCube,
    *,
    mutation: MutationManifest = DEFAULT_MUTATION,
) -> pd.DataFrame:
    if mutation.can_increase_risk:
        raise ValueError("aov0_mutation_may_not_increase_risk")
    parent = normalize_rule100_control(parent_weights)
    state = _aligned_state(parent, cube)
    crowding = np.tanh(state["C_proxy"].clip(lower=0.0) / 3.0)
    illiquidity = 1.0 - state["L"].clip(0.0, 1.0)
    adverse_regime = 1.0 + (-state["R"]).clip(lower=0.0, upper=1.0)
    hazard = (mutation.eta * crowding * illiquidity * adverse_regime).clip(0.0, mutation.hazard_cap)
    child = pd.DataFrame(np.nan, index=parent.index, columns=parent.columns)
    rebalance_mask = parent.ne(parent.shift(1)).any(axis=1)
    rebalance_mask.iloc[0] = True
    for date in parent.index[rebalance_mask]:
        child.loc[date] = parent.loc[date] * (1.0 - hazard.loc[date])
    child = child.ffill().fillna(0.0)
    if (child - parent > 1e-12).any().any():
        raise ValueError("aov0_child_increased_exposure")
    return child.astype(float)


def assert_rule100_equivalence(
    rule100_weights: pd.DataFrame,
    cube: VerticalCube,
    *,
    contract: AOV0Contract = DEFAULT_CONTRACT,
) -> None:
    base = normalize_rule100_control(rule100_weights)
    disabled = build_parent_weights(base, cube, contract=contract, dynamic_enabled=False)
    if not np.allclose(
        base.to_numpy(dtype=float),
        disabled.to_numpy(dtype=float),
        rtol=0.0,
        atol=contract.rule100_equivalence_tolerance,
    ):
        raise ValueError("aov0_rule100_equivalence_failed")


def _aligned_state(weights: pd.DataFrame, cube: VerticalCube) -> dict[str, pd.DataFrame]:
    frame = cube.frame.copy()
    frame["date"] = pd.DatetimeIndex(pd.to_datetime(frame["date"])).normalize()
    result: dict[str, pd.DataFrame] = {}
    for column in ("Q", "M", "F_proxy", "C_proxy", "L", "R", "U"):
        pivot = frame.pivot(index="date", columns="permno", values=column)
        pivot = pivot.reindex(index=weights.index, columns=weights.columns)
        if pivot.isna().any().any():
            raise ValueError(f"aov0_cube_state_missing:{column}")
        result[column] = pivot.astype(float)
    return result


def _project_budget_with_cap(raw: pd.Series, *, budget: float, cap: float) -> pd.Series:
    if budget <= 1e-15:
        return pd.Series(0.0, index=raw.index, dtype=float)
    active = raw[raw > 0.0].copy()
    if active.empty:
        raise ValueError("aov0_parent_no_active_support_for_budget")
    if budget > cap * len(active) + 1e-12:
        raise ValueError("aov0_parent_budget_infeasible_under_cap")

    out = pd.Series(0.0, index=raw.index, dtype=float)
    remaining = active.index.tolist()
    remaining_budget = budget
    scores = active.astype(float)
    while remaining:
        subset = scores.loc[remaining]
        total = float(subset.sum())
        if total <= 0:
            proposed = pd.Series(remaining_budget / len(remaining), index=remaining)
        else:
            proposed = subset / total * remaining_budget
        capped = proposed[proposed > cap + 1e-12]
        if capped.empty:
            out.loc[remaining] = proposed
            break
        for asset in capped.index:
            out.loc[asset] = cap
            remaining_budget -= cap
            remaining.remove(asset)
        if remaining_budget < -1e-12:
            raise ValueError("aov0_parent_projection_negative_budget")
    return out.clip(lower=0.0, upper=cap)
