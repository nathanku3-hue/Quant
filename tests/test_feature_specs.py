from __future__ import annotations

import pandas as pd

from data.feature_specs import (
    FeatureSpec,
    build_default_feature_specs,
    compute_registry_hash,
    compute_spec_hash,
    spec_inventory_quality_proxy,
    spec_discipline_conditional,
)


def test_inventory_quality_proxy_prefers_acceleration_and_low_bloat():
    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    cols = [101, 202]
    sales_accel = pd.DataFrame([[0.20, -0.20]], index=idx, columns=cols)
    op_margin_accel = pd.DataFrame([[0.10, -0.10]], index=idx, columns=cols)
    bloat = pd.DataFrame([[-0.10, 0.10]], index=idx, columns=cols)
    net_investment = pd.DataFrame([[0.02, 0.20]], index=idx, columns=cols)

    context = {
        "sales_accel_q": sales_accel,
        "op_margin_accel_q": op_margin_accel,
        "bloat_q": bloat,
        "net_investment_q": net_investment,
    }
    spec = FeatureSpec(
        name="z_inventory_quality_proxy",
        func=spec_inventory_quality_proxy,
        category="fundamental",
        inputs=(
            "sales_accel_q",
            "op_margin_accel_q",
            "bloat_q",
            "net_investment_q",
        ),
        params={
            "sales_accel_weight": 1.0,
            "op_margin_accel_weight": 1.0,
            "bloat_weight": -1.0,
            "net_investment_weight": -0.5,
        },
    )
    out = spec_inventory_quality_proxy(context, spec)

    assert out.shape == (1, 2)
    assert float(out.iloc[0, 0]) > float(out.iloc[0, 1])


def test_discipline_conditional_waives_penalty_when_proxy_positive():
    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    cols = [101, 202]
    asset_growth = pd.DataFrame([[0.30, 0.30]], index=idx, columns=cols)
    z_inventory_quality_proxy = pd.DataFrame([[0.25, -0.25]], index=idx, columns=cols)
    op_margin_delta = pd.DataFrame([[0.00, 0.00]], index=idx, columns=cols)

    context = {
        "asset_growth_yoy": asset_growth,
        "z_inventory_quality_proxy": z_inventory_quality_proxy,
        "operating_margin_delta_q": op_margin_delta,
    }
    spec = FeatureSpec(
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
    )
    out = spec_discipline_conditional(context, spec)
    assert out.shape == (1, 2)
    assert float(out.iloc[0, 0]) > float(out.iloc[0, 1])


def test_feature_spec_hash_api_is_deterministic():
    specs = build_default_feature_specs()
    first = compute_spec_hash(specs[0])
    second = compute_spec_hash(build_default_feature_specs()[0])
    assert first == second
    assert compute_registry_hash(specs) == compute_registry_hash(build_default_feature_specs())
