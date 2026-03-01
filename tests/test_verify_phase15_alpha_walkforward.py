from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = ROOT / "backtests" / "verify_phase15_alpha_walkforward.py"


def _load_verifier():
    assert VERIFIER_PATH.exists(), f"Missing verifier script: {VERIFIER_PATH}"
    spec = importlib.util.spec_from_file_location("verify_phase15_alpha_walkforward", VERIFIER_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_feature_history_selects_top_liquidity(tmp_path: Path):
    mod = _load_verifier()
    idx = pd.date_range("2025-01-01", periods=5, freq="B")
    rows = []
    for d in idx:
        rows.append(
            {
                "date": d,
                "permno": 101,
                "adj_close": 100.0,
                "volume": 2_000_000.0,
                "sma200": 95.0,
                "dist_sma20": -0.01,
                "rsi_14d": 25.0,
                "atr_14d": 1.0,
                "yz_vol_20d": 0.2,
                "composite_score": 2.0,
                "trend_veto": False,
            }
        )
        rows.append(
            {
                "date": d,
                "permno": 202,
                "adj_close": 50.0,
                "volume": 10_000.0,
                "sma200": 45.0,
                "dist_sma20": -0.01,
                "rsi_14d": 25.0,
                "atr_14d": 1.0,
                "yz_vol_20d": 0.3,
                "composite_score": 1.0,
                "trend_veto": False,
            }
        )
    df = pd.DataFrame(rows)
    p = tmp_path / "features.parquet"
    df.to_parquet(p, index=False)

    out = mod._load_feature_history(
        features_path=p,
        start=pd.Timestamp("2025-01-01"),
        end=pd.Timestamp("2025-12-31"),
        top_n=1,
    )
    assert not out.empty
    assert set(out["permno"].unique().tolist()) == {101}


def test_metrics_helper_contract():
    mod = _load_verifier()
    mod13 = mod._load_phase13_module()

    idx = pd.date_range("2025-01-01", periods=20, freq="B")
    ret = pd.Series(np.linspace(0.0, 0.001, len(idx)), index=idx)
    curve = (1.0 + ret).cumprod()

    m = mod._metrics(mod13, ret, curve)
    assert {"cagr", "sharpe", "max_dd", "ulcer"}.issubset(set(m.keys()))
