from __future__ import annotations

import logging

import pandas as pd

from data import fundamentals as fundamentals_data


def test_build_fundamentals_daily_logs_panel_fallback(monkeypatch, caplog):
    idx = pd.date_range("2024-01-02", periods=3, freq="B")

    def fail_panel(*args, **kwargs):
        raise RuntimeError("panel unavailable")

    monkeypatch.setattr(
        fundamentals_data.fundamentals_panel_data,
        "load_daily_fundamentals_panel",
        fail_panel,
    )

    qdf = pd.DataFrame(
        {
            "permno": [10001],
            "published_at": [pd.Timestamp("2024-01-02")],
            "release_date": [pd.Timestamp("2023-12-31")],
        }
    )
    monkeypatch.setattr(
        fundamentals_data,
        "load_quarterly_fundamentals",
        lambda permnos=None, as_of_date=None, **kwargs: qdf,
    )

    def fake_broadcast(_qdf, _metric, idx_arg, permnos_arg, event_col="published_at"):
        cols = list(permnos_arg) if permnos_arg else [10001]
        return pd.DataFrame(1.0, index=idx_arg, columns=cols)

    monkeypatch.setattr(fundamentals_data, "_broadcast_metric", fake_broadcast)

    with caplog.at_level(logging.WARNING):
        payload = fundamentals_data.build_fundamentals_daily(idx, permnos=[10001])

    assert payload["roic"].shape == (3, 1)
    messages = [record.getMessage() for record in caplog.records]
    assert any("panel load failed" in msg for msg in messages)
    assert any("fallback active mode=quarterly_published_at" in msg for msg in messages)
