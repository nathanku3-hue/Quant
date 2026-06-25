from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from data import dashboard_data_loader as loader


def _write_minimal_prices_tri(path: Path) -> None:
    pd.DataFrame(
        {
            "date": [
                pd.Timestamp("2024-01-02"),
                pd.Timestamp("2024-01-02"),
                pd.Timestamp("2024-01-03"),
                pd.Timestamp("2024-01-03"),
            ],
            "permno": [1, 2, 1, 2],
            "total_ret": [0.01, -0.02, 0.03, 0.01],
            "tri": [100.0, 50.0, 103.0, 50.5],
            "volume": [1_000_000, 750_000, 1_200_000, 700_000],
        }
    ).to_parquet(path, index=False)


def test_load_dashboard_data_minimal_tri_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir(parents=True)
    static.mkdir(parents=True)

    _write_minimal_prices_tri(processed / "prices_tri.parquet")
    pd.DataFrame({"permno": [1, 2], "ticker": ["AAA", "BBB"]}).to_parquet(
        processed / "tickers.parquet",
        index=False,
    )

    def _fundamentals_stub(prices_index, permnos):
        idx = pd.Index([int(p) for p in permnos], name="permno")
        return {"latest": pd.DataFrame(index=idx)}

    monkeypatch.setattr(
        loader.fundamentals_data,
        "build_fundamentals_snapshot_context",
        _fundamentals_stub,
    )

    returns_wide, prices_wide, macro, ticker_map, fundamentals_wide = loader.load_dashboard_data(
        top_n=2,
        start_year=2024,
        processed_dir=str(processed),
        static_dir=str(static),
    )

    assert returns_wide.shape == (2, 2)
    assert prices_wide.shape == (2, 2)
    assert set(int(c) for c in returns_wide.columns) == {1, 2}
    assert set(int(c) for c in prices_wide.columns) == {1, 2}
    assert ticker_map == {1: "AAA", 2: "BBB"}
    assert not macro.empty
    assert "regime_scalar" in macro.columns
    assert isinstance(fundamentals_wide.get("earnings_calendar"), pd.DataFrame)
    assert list(fundamentals_wide["earnings_calendar"].index) == [1, 2]


def test_load_dashboard_data_r3000_mode_requires_universe_file(tmp_path: Path):
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir(parents=True)
    static.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="universe_mode='r3000_pit' requested"):
        loader.load_dashboard_data(
            universe_mode="r3000_pit",
            processed_dir=str(processed),
            static_dir=str(static),
        )
