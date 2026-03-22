from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from scripts import validate_data_layer as mod


def _write_parquet(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def test_freshness_status_text_reports_lag_and_lead():
    lag_days, lag_msg = mod._freshness_status_text(
        features_max_date=pd.Timestamp("2026-02-13"),
        price_max_date=pd.Timestamp("2026-02-27"),
    )
    lead_days, lead_msg = mod._freshness_status_text(
        features_max_date=pd.Timestamp("2026-02-13"),
        price_max_date=pd.Timestamp("2024-12-31"),
    )

    assert lag_days == 14
    assert "Freshness gap" in lag_msg
    assert lead_days == -409
    assert "extends 409 day(s) beyond" in lead_msg


def test_validate_feature_store_layer_uses_feature_builder_price_surface(tmp_path, monkeypatch):
    features_path = tmp_path / "features.parquet"
    prices_path = tmp_path / "prices.parquet"
    tri_path = tmp_path / "prices_tri.parquet"

    _write_parquet(
        features_path,
        pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-02-13"]),
                "permno": [1],
                "composite_score": [1.0],
            }
        ),
    )
    _write_parquet(
        prices_path,
        pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-02-27"]),
                "permno": [1],
                "raw_close": [10.0],
            }
        ),
    )
    _write_parquet(
        tri_path,
        pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-12-31"]),
                "permno": [1],
                "tri": [1.0],
            }
        ),
    )

    monkeypatch.setattr(mod, "FEATURES_PATH", str(features_path))
    monkeypatch.setattr(mod, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(mod, "_price_source_config", lambda: {"base": str(tri_path), "patch": None})

    assert mod._validate_feature_store_layer() is True


def test_validate_feature_store_layer_rejects_positive_freshness_gap(tmp_path, monkeypatch):
    features_path = tmp_path / "features.parquet"
    prices_path = tmp_path / "prices.parquet"

    _write_parquet(
        features_path,
        pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-12-20"]),
                "permno": [1],
                "composite_score": [1.0],
            }
        ),
    )
    _write_parquet(
        prices_path,
        pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-12-31"]),
                "permno": [1],
                "raw_close": [10.0],
            }
        ),
    )

    monkeypatch.setattr(mod, "FEATURES_PATH", str(features_path))
    monkeypatch.setattr(mod, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(mod, "_price_source_config", lambda: {"base": str(prices_path), "patch": None})

    assert mod._validate_feature_store_layer() is False
