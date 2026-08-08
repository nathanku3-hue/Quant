from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd
import pytest

import research.aov0.ciq_fundamentals as ciq
from strategies.rule100_softmax_v1_1 import compute_factor_group_counts


def _synthetic_export_rows() -> list[dict[str, str]]:
    headers = {"A": "SP_ENTITY_NAME", "B": "SP_ENTITY_ID", "C": "MI_PRIMARY_INDUSTRY", "D": "SP_EXCHANGE"}
    periods = {"A": "", "B": "", "C": "", "D": ""}
    data = {"A": "Example Co", "B": "123", "C": "Software", "D": "NYSE"}
    col_idx = 0
    quarter_values = {
        "FQ12025": 1.0,
        "FQ22025": 2.0,
        "FQ32025": 3.0,
        "FQ42025": 4.0,
        "FQ12026": 5.0,
    }
    period_ends = {
        "FQ12025": 45747,
        "FQ22025": 45838,
        "FQ32025": 45930,
        "FQ42025": 46022,
        "FQ12026": 46112,
    }
    for source_name in ciq._METRICS:
        relative_key = f"R{col_idx}"
        headers[relative_key] = source_name
        periods[relative_key] = "FQ0"
        data[relative_key] = "999999"
        col_idx += 1
        for quarter, base in quarter_values.items():
            key = f"Q{col_idx}"
            headers[key] = source_name
            periods[key] = quarter
            multiplier = 100.0 if source_name == "IQ_TOTAL_REV" else 10.0
            if source_name == "IQ_INVENTORY":
                multiplier = 5.0
            if source_name == "IQ_OPER_INC":
                multiplier = 10.0
            data[key] = str(base * multiplier)
            col_idx += 1
    headers["PE0"] = "IQ_PERIOD_END"
    periods["PE0"] = "FQ0"
    data["PE0"] = "46203"
    for quarter, serial in period_ends.items():
        key = f"PE{quarter}"
        headers[key] = "IQ_PERIOD_END"
        periods[key] = quarter
        data[key] = str(serial)
    headers["__row__"] = "5"
    periods["__row__"] = "6"
    data["__row__"] = "8"
    return [{"__row__": "4"}, headers, periods, {"__row__": "7"}, data]


def test_normalize_excludes_relative_fq0(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ciq, "_xlsx_rows", lambda _path: _synthetic_export_rows())
    panel, metadata = ciq.normalize_run4(
        "ignored.xlsx",
        admission_time=datetime(2026, 8, 7, 16, 0, tzinfo=UTC),
    )
    assert len(panel) == 5
    assert metadata["relative_fq0_excluded"] is True
    assert metadata["quarter_reference_mode"] == "ABSOLUTE_FQqYYYY_ONLY"
    assert panel["total_revenue_q"].max() == 500.0
    assert not panel.select_dtypes(include=["number"]).eq(999999.0).any().any()


def test_derive_metrics_matches_locked_formulas() -> None:
    dates = pd.date_range("2024-03-31", periods=8, freq="QE")
    revenue = pd.Series([100.0, 110.0, 121.0, 133.1, 159.72, 175.692, 193.2612, 212.58732])
    panel = pd.DataFrame(
        {
            "source_entity_id": ["1"] * 8,
            "period_end": dates,
            "total_revenue_q": revenue,
            "total_assets_q": [200, 210, 220, 230, 250, 260, 270, 280],
            "inventory_q": [20, 21, 22, 23, 24, 25, 26, 27],
            "depreciation_q": [2.0] * 8,
            "equity_q": [100.0] * 8,
            "current_debt_q": [5.0] * 8,
            "total_liabilities_q": [100.0] * 8,
            "total_debt_q": [40.0] * 8,
            "cash_q": [10.0] * 8,
            "operating_income_q": [10, 11, 12, 13, 20, 22, 24, 26],
            "capex_q": [5.0] * 8,
        }
    )
    out = ciq.derive_metrics(panel)
    last = out.iloc[-1]
    expected_op_income_ttm = 20 + 22 + 24 + 26
    expected_invested_capital = 100 + 40 - 10
    assert last["roic"] == pytest.approx(expected_op_income_ttm / expected_invested_capital)
    assert last["asset_growth_yoy"] == pytest.approx(280 / 230 - 1)
    assert last["net_investment_q"] == pytest.approx((5 - 2) / 270)
    assert np.isfinite(last["sales_accel_q"])
    assert np.isfinite(last["op_margin_accel_q"])
    assert np.isfinite(last["bloat_q"])


def test_current_state_keeps_missing_entity_without_faking_security_identity() -> None:
    known = pd.Timestamp("2026-08-07T16:00:00Z")
    latest = pd.DataFrame(
        {
            "source_entity_id": [str(i) for i in range(1, 21)],
            "source_entity_name": [f"Co {i}" for i in range(1, 21)],
            "period_end": [pd.Timestamp("2026-06-30")] * 20,
            "known_at": [known] * 20,
            "pit_mode": [ciq.PIT_MODE] * 20,
            "identity_status": [ciq.IDENTITY_STATUS] * 20,
            "is_latest_known_quarter": [True] * 20,
            "roic": np.linspace(-0.1, 0.3, 20),
            "asset_growth_yoy": np.linspace(-0.2, 0.4, 20),
            "sales_accel_q": np.linspace(-0.3, 0.5, 20),
            "op_margin_accel_q": np.linspace(-0.2, 0.2, 20),
            "bloat_q": np.linspace(0.3, -0.3, 20),
            "net_investment_q": np.linspace(0.2, -0.1, 20),
            "operating_margin_delta_q": np.linspace(-0.05, 0.08, 20),
            "delta_revenue_inventory": np.linspace(-1.0, 1.0, 20),
        }
    )
    state, _metadata = ciq.build_current_state(latest, all_entity_ids={str(i) for i in range(1, 22)})
    missing = state.loc[state["source_entity_id"].eq("21")].iloc[0]
    assert len(state) == 21
    assert missing["fundamental_state_status"] == "NO_ABSOLUTE_QUARTER_HISTORY"
    assert missing["factor_present_count"] == 0
    assert missing["factor_positive_count"] == 0
    assert "security_id" not in state.columns
    assert "permno" not in state.columns
    assert state["identity_status"].eq(ciq.IDENTITY_STATUS).all()


def test_factor_positive_count_uses_rule100_v11_group_semantics() -> None:
    known = pd.Timestamp("2026-08-07T16:00:00Z")
    latest = pd.DataFrame(
        {
            "source_entity_id": [str(i) for i in range(1, 21)],
            "period_end": [pd.Timestamp("2026-06-30")] * 20,
            "known_at": [known] * 20,
            "pit_mode": [ciq.PIT_MODE] * 20,
            "identity_status": [ciq.IDENTITY_STATUS] * 20,
            "is_latest_known_quarter": [True] * 20,
            "roic": np.arange(20, dtype=float),
            "asset_growth_yoy": np.linspace(0.4, -0.4, 20),
            "sales_accel_q": np.arange(20, dtype=float),
            "op_margin_accel_q": np.arange(20, dtype=float),
            "bloat_q": np.arange(20, 0, -1, dtype=float),
            "net_investment_q": np.arange(20, 0, -1, dtype=float),
            "operating_margin_delta_q": np.linspace(-0.1, 0.1, 20),
            "delta_revenue_inventory": np.arange(20, dtype=float),
        }
    )
    state, _metadata = ciq.build_current_state(latest)
    expected = compute_factor_group_counts(state)
    pd.testing.assert_series_equal(
        state["factor_positive_count"].reset_index(drop=True),
        expected["factor_positive_count"].astype(int).reset_index(drop=True),
        check_names=False,
    )
    assert state["factor_positive_count"].between(0, 4).all()
