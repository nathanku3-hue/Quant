from __future__ import annotations

import json
import os
import time

import pandas as pd

from core import data_orchestrator as data_orch


def test_scale_live_overlay_to_local_anchors_on_overlap() -> None:
    local = pd.DataFrame(
        {101: [100.0, 110.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {101: [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-03"]),
    )

    scaled = data_orch.scale_live_overlay_to_local(local, live)

    assert round(float(scaled.loc[pd.Timestamp("2026-05-02"), 101]), 6) == 110.0
    assert round(float(scaled.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_scale_live_overlay_to_local_dedupes_anchor_dates() -> None:
    local = pd.DataFrame(
        {101: [100.0, 105.0, 110.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {101: [54.0, 55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-02", "2026-05-03"]),
    )

    scaled = data_orch.scale_live_overlay_to_local(local, live)

    assert scaled.index.is_unique
    assert round(float(scaled.loc[pd.Timestamp("2026-05-02"), 101]), 6) == 110.0
    assert round(float(scaled.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_refresh_selected_prices_with_live_overlay_stitches_by_permno(monkeypatch) -> None:
    local = pd.DataFrame(
        {101: [100.0, 110.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {"AAA": [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-03"]),
    )

    def _fake_download(tickers: tuple[str, ...], start_iso: str, **kwargs):
        assert tickers == ("AAA",)
        assert start_iso == "2026-04-22"
        assert kwargs["schedule_background"] is True
        return live

    monkeypatch.setattr(data_orch, "download_recent_close_prices", _fake_download)

    refreshed, latest, source = data_orch.refresh_selected_prices_with_live_overlay(
        local,
        {101: "AAA"},
    )

    assert source == "live"
    assert latest == pd.Timestamp("2026-05-03")
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_refresh_selected_prices_with_partial_live_overlay_preserves_local_cells(monkeypatch) -> None:
    local = pd.DataFrame(
        {
            101: [100.0, 110.0],
            202: [200.0, 210.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {"AAA": [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-03"]),
    )
    monkeypatch.setattr(
        data_orch,
        "download_recent_close_prices",
        lambda *args, **kwargs: live,
    )

    refreshed, latest, source = data_orch.refresh_selected_prices_with_live_overlay(
        local,
        {101: "AAA", 202: "BBB"},
    )

    assert source == "live"
    assert latest == pd.Timestamp("2026-05-03")
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-02"), 101]), 6) == 110.0
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-02"), 202]), 6) == 210.0
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_download_recent_close_prices_returns_stale_cache_while_refreshing(
    tmp_path,
    monkeypatch,
) -> None:
    cache_dir = tmp_path / "overlay"
    tickers = ("AAA",)
    start_iso = "2026-04-22"
    cache_path = data_orch._overlay_cache_path(tickers, start_iso, cache_dir)
    stale = pd.DataFrame(
        {"AAA": [10.0]},
        index=pd.to_datetime(["2026-05-01"]),
    )
    data_orch._write_overlay_cache_atomic(cache_path, stale)
    old_mtime = time.time() - 3600
    os.utime(cache_path, (old_mtime, old_mtime))
    monkeypatch.setattr(data_orch.time, "time", lambda: old_mtime + 3600)
    scheduled = []
    monkeypatch.setattr(
        data_orch,
        "_schedule_overlay_refresh",
        lambda *args: scheduled.append(args),
    )

    cached = data_orch.download_recent_close_prices(
        tickers,
        start_iso,
        cache_ttl_seconds=1,
        cache_dir=cache_dir,
        schedule_background=True,
    )

    assert float(cached.loc[pd.Timestamp("2026-05-01"), "AAA"]) == 10.0
    assert len(scheduled) == 1


def test_download_recent_close_prices_fails_soft_when_scheduler_submit_fails(
    tmp_path,
    monkeypatch,
) -> None:
    cache_dir = tmp_path / "overlay"
    tickers = ("AAA",)
    start_iso = "2026-04-22"
    normalized = data_orch._normalize_recent_close_tickers(tickers)
    cache_path = data_orch._overlay_cache_path(normalized, start_iso, cache_dir)
    cache_key = data_orch._overlay_cache_key(normalized, start_iso)
    stale = pd.DataFrame(
        {"AAA": [10.0]},
        index=pd.to_datetime(["2026-05-01"]),
    )
    data_orch._write_overlay_cache_atomic(cache_path, stale)
    old_mtime = time.time() - 3600
    os.utime(cache_path, (old_mtime, old_mtime))
    monkeypatch.setattr(data_orch.time, "time", lambda: old_mtime + 3600)

    class BrokenExecutor:
        def submit(self, *args, **kwargs):
            raise RuntimeError("executor unavailable")

    data_orch._overlay_inflight_keys.discard(cache_key)
    monkeypatch.setattr(data_orch, "_overlay_executor", lambda: BrokenExecutor())

    cached = data_orch.download_recent_close_prices(
        tickers,
        start_iso,
        cache_ttl_seconds=1,
        cache_dir=cache_dir,
        schedule_background=True,
    )

    assert float(cached.loc[pd.Timestamp("2026-05-01"), "AAA"]) == 10.0
    assert cache_key not in data_orch._overlay_inflight_keys


def test_overlay_cache_future_mtime_is_not_fresh(tmp_path, monkeypatch) -> None:
    cache_path = tmp_path / "future.parquet"
    cached_frame = pd.DataFrame(
        {"AAA": [10.0]},
        index=pd.to_datetime(["2026-05-01"]),
    )
    data_orch._write_overlay_cache_atomic(cache_path, cached_frame)
    now = time.time()
    cache_path.touch()
    monkeypatch.setattr(data_orch.time, "time", lambda: now - 60)

    cached, is_fresh = data_orch._read_overlay_cache(cache_path, cache_ttl_seconds=900)

    assert float(cached.loc[pd.Timestamp("2026-05-01"), "AAA"]) == 10.0
    assert is_fresh is False


def test_unified_data_cache_signature_tracks_source_file_changes(tmp_path) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()

    missing_signature = data_orch.build_unified_data_cache_signature(
        processed_dir=processed,
        static_dir=static,
    )

    prices_path = processed / "prices_tri.parquet"
    prices_path.write_bytes(b"old")
    first_signature = data_orch.build_unified_data_cache_signature(
        processed_dir=processed,
        static_dir=static,
    )

    prices_path.write_bytes(b"newer")
    second_signature = data_orch.build_unified_data_cache_signature(
        processed_dir=processed,
        static_dir=static,
    )

    assert missing_signature != first_signature
    assert first_signature != second_signature
    assert (str(prices_path.resolve(strict=False)), None, None) in missing_signature
    assert any(
        entry[0] == str(prices_path.resolve(strict=False)) and entry[2] == len(b"newer")
        for entry in second_signature
    )


def test_load_strategy_metrics_from_results_coerces_valid_rows(tmp_path) -> None:
    results_path = tmp_path / "backtest_results.json"
    results_path.write_text(
        json.dumps(
            {
                "valid": {"cagr": "0.2", "sharpe": "1.5", "max_dd": "-0.1", "timestamp": "2026-05-11"},
                "invalid": {"cagr": "not-a-number"},
                "ignored": "bad-row",
            }
        ),
        encoding="utf-8",
    )

    metrics = data_orch.load_strategy_metrics_from_results(results_path)

    assert metrics == {
        "valid": {
            "cagr": 0.2,
            "sharpe": 1.5,
            "max_dd": -0.1,
            "timestamp": "2026-05-11",
        }
    }
