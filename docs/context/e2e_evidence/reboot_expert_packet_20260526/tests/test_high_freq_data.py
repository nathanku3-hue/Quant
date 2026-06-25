from __future__ import annotations

import scripts.high_freq_data as high_freq_mod


def test_fetch_tsmc_yoy_returns_neutral_degraded_metric_when_egress_blocked(
    monkeypatch,
):
    monkeypatch.setattr(high_freq_mod, "_allow_egress_or_none", lambda *_args, **_kwargs: False)
    fetcher = high_freq_mod.AutoFetcher()
    out = fetcher.fetch_tsmc_yoy()
    assert out["val"] == 0.0
    assert out["degraded"] is True
    assert out["reason"] == "egress_blocked"


def test_fetch_cloud_growth_returns_neutral_degraded_metric_when_egress_blocked(
    monkeypatch,
):
    monkeypatch.setattr(high_freq_mod, "_allow_egress_or_none", lambda *_args, **_kwargs: False)
    fetcher = high_freq_mod.AutoFetcher()
    out = fetcher.fetch_cloud_growth()
    assert out["val"] == 0.0
    assert out["degraded"] is True
    assert out["reason"] == "egress_blocked"
