from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "backtests" / "inspect_data_coverage.py"


def _load_script():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("inspect_data_coverage", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_compute_valid_mask_ignores_identifier_columns():
    mod = _load_script()
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "permno": [10001, 10001, 10002],
            "ticker": ["AAA", "AAA", None],
            "feature_a": [np.nan, 1.5, np.nan],
            "feature_b": [np.nan, np.nan, 0.0],
        }
    )

    feature_columns = mod.infer_feature_columns(list(df.columns))
    assert feature_columns == ["feature_a", "feature_b"]

    valid_mask = mod.compute_valid_mask(df, feature_columns)
    assert valid_mask.tolist() == [False, True, True]


def test_build_yearly_coverage_rollup_contract():
    mod = _load_script()
    daily = pd.DataFrame(
        {
            "date": pd.to_datetime(["2023-01-02", "2023-01-03", "2024-01-02", "2024-01-03", "2024-01-04"]),
            "valid_tickers": [10, 14, 20, 16, 18],
            "valid_rows": [10, 14, 20, 16, 18],
        }
    )

    yearly = mod.build_yearly_coverage(daily)
    assert list(yearly.columns) == [
        "year",
        "min_valid_tickers",
        "median_valid_tickers",
        "max_valid_tickers",
        "first_date",
        "last_date",
    ]
    assert yearly["year"].tolist() == [2023, 2024]
    assert yearly.loc[0, "min_valid_tickers"] == 10
    assert yearly.loc[0, "median_valid_tickers"] == pytest.approx(12.0)
    assert yearly.loc[0, "max_valid_tickers"] == 14
    assert yearly.loc[1, "min_valid_tickers"] == 16
    assert yearly.loc[1, "median_valid_tickers"] == pytest.approx(18.0)
    assert yearly.loc[1, "max_valid_tickers"] == 20
    assert yearly.loc[0, "first_date"] == pd.Timestamp("2023-01-02")
    assert yearly.loc[1, "last_date"] == pd.Timestamp("2024-01-04")


def test_compute_hockey_stick_ratio_uses_first_and_last_two_year_windows():
    mod = _load_script()
    dates = pd.date_range("2018-01-31", "2023-12-31", freq="ME")
    year = dates.year
    coverage = np.where(year <= 2019, 10, np.where(year >= 2022, 30, 20))
    daily = pd.DataFrame(
        {
            "date": dates,
            "valid_tickers": coverage.astype(float),
            "valid_rows": coverage.astype(float),
        }
    )

    ratio = mod.compute_hockey_stick_ratio(daily)
    assert ratio == pytest.approx(3.0)


def test_compute_hockey_stick_ratio_handles_empty_input():
    mod = _load_script()
    empty = pd.DataFrame(columns=["date", "valid_tickers", "valid_rows"])
    assert mod.compute_hockey_stick_ratio(empty) is None
