from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from scripts.phase20_full_backtest import _load_features_window


def _write_base_features(path: Path) -> None:
    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
            "permno": [10101, 20202],
            "ticker": ["AAA", "BBB"],
            "adj_close": [100.0, 101.5],
            "dist_sma20": [0.01, -0.02],
            "sma200": [95.0, 96.0],
            # Intentional overlap to validate SDM-preferred overlay.
            "q_tot": [9.9, 9.8],
        }
    ).to_parquet(path, index=False)


def _write_sdm_features(path: Path) -> None:
    pd.DataFrame(
        {
            "date": [pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-03")],
            "permno": [10101, 20202],
            "rev_accel": [0.10, 0.20],
            "inv_vel_traj": [0.05, -0.01],
            "gm_traj": [0.03, 0.01],
            "op_lev": [0.02, -0.04],
            "intang_intensity": [0.60, 0.40],
            "q_tot": [1.2, 0.9],
            "rmw": [0.01, 0.02],
            "cma": [0.03, 0.01],
            "yield_slope_10y2y": [0.50, 0.45],
            "CycleSetup": [0.00015, 0.00009],
        }
    ).to_parquet(path, index=False)


def test_load_features_window_dual_read_merges_sdm(tmp_path: Path) -> None:
    features_path = tmp_path / "features.parquet"
    sdm_path = tmp_path / "features_sdm.parquet"
    _write_base_features(features_path)
    _write_sdm_features(sdm_path)

    out = _load_features_window(
        features_path=features_path,
        start_date=pd.Timestamp("2024-01-01"),
        end_date=pd.Timestamp("2024-01-10"),
        extra_columns=["adj_close", "dist_sma20", "sma200"],
        sdm_features_path=sdm_path,
    )
    assert len(out) == 2
    assert {"rev_accel", "q_tot", "CycleSetup"}.issubset(set(out.columns))
    row = out[out["permno"] == 10101].iloc[0]
    assert np.isclose(float(row["rev_accel"]), 0.10)
    assert np.isclose(float(row["q_tot"]), 1.2)


def test_load_features_window_without_sdm_keeps_base(tmp_path: Path) -> None:
    features_path = tmp_path / "features.parquet"
    _write_base_features(features_path)

    out = _load_features_window(
        features_path=features_path,
        start_date=pd.Timestamp("2024-01-01"),
        end_date=pd.Timestamp("2024-01-10"),
        extra_columns=["adj_close", "dist_sma20", "sma200"],
        sdm_features_path=tmp_path / "missing_sdm.parquet",
    )
    assert len(out) == 2
    assert "adj_close" in out.columns
    assert "rev_accel" not in out.columns
