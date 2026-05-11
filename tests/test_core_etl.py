from __future__ import annotations

import duckdb
import pandas as pd

from core import etl


def test_core_etl_builds_prices_and_macro_parquet(tmp_path, monkeypatch) -> None:
    raw_csv = tmp_path / "raw.csv"
    processed = tmp_path / "processed"
    processed.mkdir()

    dates = pd.date_range("2026-01-01", periods=25, freq="B")
    rows = []
    for idx, dt in enumerate(dates):
        rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "PERMNO": 101,
                "PRC": -100.0 - idx,
                "RET": 0.01,
                "DLRET": "" if idx else -0.05,
                "VOL": 1000 + idx,
            }
        )
        rows.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "PERMNO": etl.SPY_PERMNO,
                "PRC": 400.0 + idx,
                "RET": 0.001,
                "DLRET": "",
                "VOL": 10_000 + idx,
            }
        )
    pd.DataFrame(rows).to_csv(raw_csv, index=False)

    monkeypatch.setattr(etl, "RAW_CSV", str(raw_csv).replace("\\", "/"))
    monkeypatch.setattr(etl, "PROCESSED_DIR", str(processed).replace("\\", "/"))

    con = duckdb.connect(":memory:")
    try:
        etl.build_prices(con)
        etl.build_macro(con)
    finally:
        con.close()

    prices = pd.read_parquet(processed / "prices.parquet")
    macro = pd.read_parquet(processed / "macro.parquet")

    assert {"date", "permno", "raw_close", "adj_close", "total_ret", "volume"}.issubset(prices.columns)
    assert prices.loc[prices["permno"] == 101, "raw_close"].iloc[0] == 100.0
    assert prices.loc[prices["permno"] == 101, "total_ret"].iloc[0] == -0.04
    assert len(macro) == len(dates)
    assert {"date", "spy_close", "vix_proxy"}.issubset(macro.columns)
    assert macro["spy_close"].iloc[-1] == 424.0
    assert macro["vix_proxy"].notna().all()
