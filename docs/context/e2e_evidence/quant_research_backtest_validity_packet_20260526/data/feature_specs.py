"""
Terminal Zero — Declarative Feature Specs

Defines a lightweight FeatureSpec registry used by the feature store executor.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
import pandas as pd

SpecContext = dict[str, pd.DataFrame]
SpecFunc = Callable[[SpecContext, "FeatureSpec"], pd.DataFrame]


def cross_sectional_z(wide: pd.DataFrame) -> pd.DataFrame:
    mu = wide.mean(axis=1, skipna=True)
    sigma = wide.std(axis=1, skipna=True).replace(0.0, np.nan)
    return wide.sub(mu, axis=0).div(sigma, axis=0)


def _base_frame(context: SpecContext) -> pd.DataFrame:
    for value in context.values():
        if isinstance(value, pd.DataFrame):
            return pd.DataFrame(np.nan, index=value.index, columns=value.columns, dtype=float)
    return pd.DataFrame()


def _sigmoid(df: pd.DataFrame, smooth_factor: float) -> pd.DataFrame:
    scale = max(float(smooth_factor), 1e-6)
    x = (df.astype(float) / scale).clip(lower=-60.0, upper=60.0)
    return 1.0 / (1.0 + np.exp(-x))


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    func: SpecFunc
    category: str
    inputs: tuple[str, ...]
    params: dict[str, Any] = field(default_factory=dict)
    smooth_factor: float = 1.0

    def signature(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "func": self.func.__name__,
            "category": self.category,
            "inputs": list(self.inputs),
            "params": {str(k): self.params[k] for k in sorted(self.params)},
            "smooth_factor": float(self.smooth_factor),
        }


def compute_spec_hash(spec: FeatureSpec) -> str:
    payload = spec.signature()
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def compute_registry_hash(specs: list[FeatureSpec]) -> str:
    payload = [spec.signature() for spec in specs]
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def spec_cross_sectional_z(context: SpecContext, spec: FeatureSpec) -> pd.DataFrame:
    source = str(spec.params.get("source") or (spec.inputs[0] if spec.inputs else ""))
    wide = context.get(source)
    if wide is None or wide.empty:
        return _base_frame(context)
    return cross_sectional_z(wide)


def spec_linear_combo(context: SpecContext, spec: FeatureSpec) -> pd.DataFrame:
    terms = spec.params.get("terms", [])
    acc: pd.DataFrame | None = None
    for term in terms:
        name = str(term.get("name", ""))
        weight = float(term.get("weight", 0.0))
        wide = context.get(name)
        if wide is None or wide.empty:
            continue
        piece = wide * weight
        acc = piece if acc is None else acc.add(piece, fill_value=0.0)
    if acc is None:
        return _base_frame(context)
    return acc


def spec_inventory_quality_proxy(context: SpecContext, spec: FeatureSpec) -> pd.DataFrame:
    if len(spec.inputs) < 4:
        return _base_frame(context)
    sales_accel = context.get(spec.inputs[0])
    op_margin_accel = context.get(spec.inputs[1])
    bloat = context.get(spec.inputs[2])
    net_investment = context.get(spec.inputs[3])
    if (
        sales_accel is None
        or op_margin_accel is None
        or bloat is None
        or net_investment is None
    ):
        return _base_frame(context)

    z_sales = cross_sectional_z(sales_accel.apply(pd.to_numeric, errors="coerce"))
    z_margin = cross_sectional_z(op_margin_accel.apply(pd.to_numeric, errors="coerce"))
    z_bloat = cross_sectional_z(bloat.apply(pd.to_numeric, errors="coerce"))
    z_net_inv = cross_sectional_z(net_investment.apply(pd.to_numeric, errors="coerce"))

    sales_w = float(spec.params.get("sales_accel_weight", 1.0))
    margin_w = float(spec.params.get("op_margin_accel_weight", 1.0))
    bloat_w = float(spec.params.get("bloat_weight", -1.0))
    net_inv_w = float(spec.params.get("net_investment_weight", -0.5))
    return (
        sales_w * z_sales.fillna(0.0)
        + margin_w * z_margin.fillna(0.0)
        + bloat_w * z_bloat.fillna(0.0)
        + net_inv_w * z_net_inv.fillna(0.0)
    )


def spec_discipline_conditional(context: SpecContext, spec: FeatureSpec) -> pd.DataFrame:
    if not spec.inputs:
        return _base_frame(context)
    asset_growth = context.get(spec.inputs[0])
    if asset_growth is None:
        return _base_frame(context)
    asset_growth = asset_growth.apply(pd.to_numeric, errors="coerce")

    # Base conditional penalty:
    # penalty = asset_growth * (1 - operating_leverage_score)
    # where leverage score is a smooth function of profitability momentum.
    leverage_source = str(spec.params.get("leverage_source", "operating_margin_delta_q"))
    leverage_input = context.get(leverage_source)
    if leverage_input is None and len(spec.inputs) >= 3:
        leverage_input = context.get(spec.inputs[2])
    if leverage_input is None:
        leverage_input = _base_frame(context)

    leverage_score = _sigmoid(leverage_input, smooth_factor=spec.smooth_factor)
    penalty = asset_growth * (1.0 - leverage_score)

    proxy_source = str(spec.params.get("proxy_source", spec.inputs[1] if len(spec.inputs) >= 2 else ""))
    proxy_input = context.get(proxy_source)
    if proxy_input is not None:
        proxy_gate_threshold = float(spec.params.get("proxy_gate_threshold", 0.0))
        proxy_wide = proxy_input.apply(pd.to_numeric, errors="coerce")
        gate_open = proxy_wide.gt(proxy_gate_threshold)
        penalty = penalty.where(~gate_open, 0.0)

    discipline_raw = -penalty
    return cross_sectional_z(discipline_raw)


def build_default_feature_specs() -> list[FeatureSpec]:
    return [
        FeatureSpec(
            name="z_resid_mom",
            func=spec_cross_sectional_z,
            category="technical",
            inputs=("resid_mom_60d",),
            params={"source": "resid_mom_60d"},
        ),
        FeatureSpec(
            name="z_flow_proxy",
            func=spec_cross_sectional_z,
            category="technical",
            inputs=("flow_proxy",),
            params={"source": "flow_proxy"},
        ),
        FeatureSpec(
            name="z_vol_penalty",
            func=spec_cross_sectional_z,
            category="technical",
            inputs=("yz_vol_20d",),
            params={"source": "yz_vol_20d"},
        ),
        FeatureSpec(
            name="composite_score",
            func=spec_linear_combo,
            category="technical",
            inputs=("z_resid_mom", "z_flow_proxy", "z_vol_penalty"),
            params={
                "terms": [
                    {"name": "z_resid_mom", "weight": 1.0},
                    {"name": "z_flow_proxy", "weight": 1.0},
                    {"name": "z_vol_penalty", "weight": -1.0},
                ]
            },
        ),
        FeatureSpec(
            name="z_moat",
            func=spec_cross_sectional_z,
            category="fundamental",
            inputs=("roic",),
            params={"source": "roic"},
        ),
        FeatureSpec(
            name="z_inventory_quality_proxy",
            func=spec_inventory_quality_proxy,
            category="fundamental",
            inputs=("sales_accel_q", "op_margin_accel_q", "bloat_q", "net_investment_q"),
            params={
                "sales_accel_weight": 1.0,
                "op_margin_accel_weight": 1.0,
                "bloat_weight": -1.0,
                "net_investment_weight": -0.5,
            },
        ),
        FeatureSpec(
            name="z_discipline_cond",
            func=spec_discipline_conditional,
            category="fundamental",
            inputs=(
                "asset_growth_yoy",
                "z_inventory_quality_proxy",
                "operating_margin_delta_q",
            ),
            params={
                "proxy_source": "z_inventory_quality_proxy",
                "proxy_gate_threshold": 0.0,
                "leverage_source": "operating_margin_delta_q",
            },
            smooth_factor=0.02,
        ),
        FeatureSpec(
            name="z_demand",
            func=spec_cross_sectional_z,
            category="fundamental",
            inputs=("delta_revenue_inventory",),
            params={"source": "delta_revenue_inventory"},
        ),
        FeatureSpec(
            name="capital_cycle_score",
            func=spec_linear_combo,
            category="fundamental",
            inputs=("z_moat", "z_discipline_cond", "z_demand"),
            params={
                "terms": [
                    {"name": "z_moat", "weight": 0.4},
                    {"name": "z_discipline_cond", "weight": 0.4},
                    {"name": "z_demand", "weight": 0.2},
                ]
            },
            smooth_factor=0.02,
        ),
    ]
