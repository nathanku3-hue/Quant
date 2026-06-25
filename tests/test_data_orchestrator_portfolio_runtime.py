from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import pytest

from core import data_orchestrator as data_orch


def test_price_endpoint_helpers_default_to_strict_freshness() -> None:
    prices = pd.DataFrame(
        {101: [10.0, 11.0, 0.0], 202: [20.0, 21.0, 22.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
    )

    assert data_orch.price_column_latest_date(prices, 101) == pd.Timestamp("2026-05-02")
    assert data_orch.price_frame_latest_date(prices) == pd.Timestamp("2026-05-03")
    assert data_orch.price_endpoint_is_fresh(
        pd.Timestamp("2026-05-02"),
        pd.Timestamp("2026-05-03"),
    ) is False
    assert data_orch.price_endpoint_is_fresh(
        pd.Timestamp("2026-05-02"),
        pd.Timestamp("2026-05-03"),
        max_staleness_days=1,
    ) is True


def test_price_endpoint_freshness_snapshot_reuses_per_column_endpoints() -> None:
    prices = pd.DataFrame(
        {101: [10.0, 11.0, None], 202: [20.0, 21.0, 22.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
    )

    freshness = data_orch.build_price_endpoint_freshness(prices)

    assert freshness.required_latest == pd.Timestamp("2026-05-03")
    assert freshness.latest_for(101) == pd.Timestamp("2026-05-02")
    assert freshness.latest_for(202) == pd.Timestamp("2026-05-03")
    assert data_orch.price_column_latest_date(pd.DataFrame(), 101, freshness=freshness) == pd.Timestamp("2026-05-02")
    assert data_orch.price_frame_latest_date(pd.DataFrame(), freshness=freshness) == pd.Timestamp("2026-05-03")

    fresh, target, stale = data_orch.filter_price_frame_to_fresh_columns(
        prices,
        [101, 202],
        freshness=freshness,
    )

    assert target == pd.Timestamp("2026-05-03")
    assert list(fresh.columns) == [202]
    assert stale == (101,)


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


def test_scale_live_overlay_to_local_requires_overlap() -> None:
    data_orch._scaled_overlay_cache.clear()
    local = pd.DataFrame(
        {101: [100.0, 110.0]},
        index=pd.to_datetime(["2026-02-26", "2026-02-27"]),
    )
    live = pd.DataFrame(
        {101: [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )

    scaled = data_orch.scale_live_overlay_to_local(local, live)

    assert scaled.empty
    assert len(data_orch._scaled_overlay_cache) == 1


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

    assert source == "live_stale_dropped"
    assert latest == pd.Timestamp("2026-05-03")
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-02"), 101]), 6) == 110.0
    assert 202 not in refreshed.columns
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_refresh_selected_prices_with_partial_overlay_drops_stale_endpoint(monkeypatch) -> None:
    local = pd.DataFrame(
        {
            101: [100.0, 110.0],
            202: [200.0, None],
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

    assert source == "live_stale_dropped"
    assert latest == pd.Timestamp("2026-05-03")
    assert list(refreshed.columns) == [101]
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0


def test_refresh_selected_prices_drops_no_overlap_live_overlay_asset(monkeypatch) -> None:
    local = pd.DataFrame(
        {
            101: [None, None, 100.0, 110.0],
            202: [200.0, 210.0, None, None],
        },
        index=pd.to_datetime(["2026-02-26", "2026-02-27", "2026-05-01", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {
            "AAA": [50.0, 55.0],
            "BBB": [105.0, 110.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )
    monkeypatch.setattr(
        data_orch,
        "download_recent_close_prices",
        lambda *args, **kwargs: live,
    )

    refreshed, latest, source = data_orch.refresh_selected_prices_with_live_overlay(
        local,
        {101: "AAA", 202: "BBB"},
        required_latest=pd.Timestamp("2026-05-02"),
    )

    assert source == "live_stale_dropped"
    assert latest == pd.Timestamp("2026-05-02")
    assert list(refreshed.columns) == [101]
    assert round(float(refreshed.loc[pd.Timestamp("2026-05-02"), 101]), 6) == 110.0


def test_repair_stale_price_endpoints_is_display_only_and_anchored() -> None:
    local = pd.DataFrame(
        {
            101: [100.0, 110.0, None],
            202: [200.0, 210.0, 220.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-03"]),
    )
    live = pd.DataFrame(
        {"AAA": [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-03"]),
    )

    result = data_orch.repair_stale_price_endpoints_with_live_overlay(
        local,
        {101: "AAA", 202: "BBB"},
        stale_columns=(101,),
        required_latest=pd.Timestamp("2026-05-03"),
        live_loader=lambda *_args, **_kwargs: live,
    )

    assert result.display_only is True
    assert result.canonical_market_data_write is False
    assert result.source == "display_live_overlay"
    assert result.repaired_columns == (101,)
    assert result.unrepaired_columns == ()
    assert result.freshness.latest_for(101) == pd.Timestamp("2026-05-03")
    assert round(float(result.prices.loc[pd.Timestamp("2026-05-03"), 101]), 6) == 120.0
    assert result.diagnostics[0]["status"] == "repaired"
    assert result.diagnostics[0]["reason"] == "anchored_display_overlay"


def test_repair_stale_price_endpoint_requires_same_column_overlap() -> None:
    local = pd.DataFrame(
        {
            101: [100.0, 110.0, None, None],
            202: [200.0, 210.0, 220.0, 230.0],
        },
        index=pd.to_datetime(["2026-02-26", "2026-02-27", "2026-05-02", "2026-05-03"]),
    )
    live = pd.DataFrame(
        {"AAA": [55.0, 60.0]},
        index=pd.to_datetime(["2026-05-02", "2026-05-03"]),
    )

    result = data_orch.repair_stale_price_endpoints_with_live_overlay(
        local,
        {101: "AAA", 202: "BBB"},
        stale_columns=(101,),
        required_latest=pd.Timestamp("2026-05-03"),
        live_loader=lambda *_args, **_kwargs: live,
    )

    assert result.repaired_columns == ()
    assert result.unrepaired_columns == (101,)
    assert result.source == "display_live_overlay_unanchored"
    assert result.freshness.latest_for(101) == pd.Timestamp("2026-02-27")
    assert result.diagnostics[0]["reason"] == "overlay_anchor_unavailable"


def test_batched_pit_loader_drops_selected_permno_when_endpoint_is_stale() -> None:
    from core.data_orchestrator import BatchedPITReplayData, build_batched_pit_input_loader

    raw_prices = pd.DataFrame(
        {
            101: [100.0, 110.0, None],
            202: [200.0, 210.0, 220.0],
        },
        index=pd.to_datetime(["2026-05-01", "2026-05-02", "2026-05-10"]),
    )
    raw_returns = raw_prices.pct_change(fill_method=None)
    batched = BatchedPITReplayData(
        raw_prices=raw_prices,
        raw_returns=raw_returns,
        membership_dates=["2026-05-10"],
        membership_index={"2026-05-10": {101, 202}},
        ticker_map={101: "AAA", 202: "BBB"},
        trading_dates=list(raw_prices.index),
    )

    loader = build_batched_pit_input_loader(batched, max_price_endpoint_gap_days=5)
    inputs = loader(as_of_date="2026-05-10")

    assert list(inputs.prices.columns) == [202]
    assert inputs.metadata["priced_members_before_endpoint_gate"] == [101, 202]
    assert inputs.metadata["price_endpoint_by_member"][101] == "2026-05-02"
    assert inputs.metadata["max_price_endpoint_gap_days"] == 5


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


def test_strategy_replay_signature_tracks_source_files_and_controls(tmp_path) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()
    prices_path = processed / "prices_tri.parquet"
    prices_path.write_bytes(b"old")

    base_signature = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": False},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )
    base_key = data_orch.strategy_replay_cache_key(base_signature)

    prices_path.write_bytes(b"newer")
    source_changed = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": False},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )
    controls_changed = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": True},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )
    method_changed = data_orch.build_strategy_replay_cache_signature(
        method="inverse_volatility",
        controls={"sector_cap": False},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )
    max_weight_changed = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": False},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.25,
        processed_dir=processed,
        static_dir=static,
    )

    assert data_orch.strategy_replay_cache_key(source_changed) != base_key
    assert data_orch.strategy_replay_cache_key(controls_changed) != base_key
    assert data_orch.strategy_replay_cache_key(method_changed) != base_key
    assert data_orch.strategy_replay_cache_key(max_weight_changed) != base_key


def test_strategy_replay_signature_defaults_to_pit_universe(tmp_path: Path) -> None:
    signature = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={},
        start_date="2026-01-01",
        end_date="2026-01-31",
        as_of_date="2026-01-15",
        max_weight=0.35,
        processed_dir=tmp_path / "processed",
        static_dir=tmp_path / "static",
    )

    assert signature["universe_mode"] == "r3000_pit"


def test_strategy_replay_signature_rejects_non_pit_universe(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="r3000_pit"):
        data_orch.build_strategy_replay_cache_signature(
            method="rule_of_100",
            controls={},
            start_date="2026-01-01",
            end_date="2026-01-31",
            as_of_date="2026-01-15",
            max_weight=0.35,
            universe_mode="top_liquid",
            processed_dir=tmp_path / "processed",
            static_dir=tmp_path / "static",
        )


def test_load_strategy_replay_inputs_clamps_future_rows_and_uses_no_provider(
    tmp_path: Path,
    monkeypatch,
) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()
    (processed / "prices_tri.parquet").write_bytes(b"signature-only")

    idx = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-05"])
    returns = pd.DataFrame({101: [0.0, 0.02, 0.03]}, index=idx)
    prices = pd.DataFrame({101: [100.0, 102.0, 105.0]}, index=idx)
    macro = pd.DataFrame({"spy_close": [1.0, 1.1, 1.2]}, index=idx)

    def _fake_provider(*args, **kwargs):
        raise AssertionError("replay input loader must not call live providers")

    def _fake_load_dashboard_data(**kwargs):
        assert kwargs["asof_date"] == pd.Timestamp("2026-01-02")
        return returns, prices, macro, {101: "AAA"}, {"sector_map": {101: "Technology"}}

    monkeypatch.setattr(data_orch, "build_market_data_provider", _fake_provider)
    monkeypatch.setattr(data_orch, "load_dashboard_data", _fake_load_dashboard_data)

    inputs = data_orch.load_strategy_replay_inputs(
        as_of_date="2026-01-02",
        start_date="2026-01-01",
        end_date="2026-01-31",
        method="rule_of_100",
        controls={"sector_cap": False},
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )

    assert inputs.prices.index.max() == pd.Timestamp("2026-01-02")
    assert inputs.returns.index.max() == pd.Timestamp("2026-01-02")
    assert pd.Timestamp("2026-01-05") not in inputs.prices.index
    assert inputs.metadata["price_matrix_path"] == str((processed / "prices_tri.parquet").resolve(strict=False))
    assert inputs.metadata["future_rows_excluded"] is True
    assert inputs.metadata["canonical_market_data_write"] is False


def test_load_strategy_replay_inputs_rejects_non_pit_universe(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="r3000_pit"):
        data_orch.load_strategy_replay_inputs(
            as_of_date="2026-01-02",
            universe_mode="top_liquid",
            processed_dir=tmp_path / "processed",
            static_dir=tmp_path / "static",
        )


def test_strategy_replay_source_metadata_records_patch_precedence(
    tmp_path: Path,
    monkeypatch,
) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()
    (processed / "prices.parquet").write_bytes(b"base")
    (processed / "yahoo_patch.parquet").write_bytes(b"patch")

    idx = pd.to_datetime(["2026-01-02"])
    returns = pd.DataFrame({101: [0.0]}, index=idx)
    prices = pd.DataFrame({101: [100.0]}, index=idx)
    macro = pd.DataFrame(index=idx)
    monkeypatch.setattr(
        data_orch,
        "load_dashboard_data",
        lambda **kwargs: (returns, prices, macro, {101: "AAA"}, {}),
    )

    inputs = data_orch.load_strategy_replay_inputs(
        as_of_date="2026-01-02",
        processed_dir=processed,
        static_dir=static,
    )

    assert inputs.metadata["source_merge_mode"] == "base_prices_with_yahoo_patch"
    assert inputs.metadata["source_precedence"] == "yahoo_patch_overrides_prices"
    assert inputs.metadata["source_matrix_paths"] == [
        str((processed / "prices.parquet").resolve(strict=False)),
        str((processed / "yahoo_patch.parquet").resolve(strict=False)),
    ]


def test_historical_unified_data_keeps_prices_and_returns_in_correct_slots(monkeypatch) -> None:
    idx = pd.to_datetime(["2026-01-02", "2026-01-05"])
    returns = pd.DataFrame({101: [0.0, 0.02]}, index=idx)
    prices = pd.DataFrame({101: [100.0, 102.0]}, index=idx)
    macro = pd.DataFrame({"spy_close": [100.0, 101.0]}, index=idx)

    def _fake_load_dashboard_data(**kwargs):
        return returns, prices, macro, {101: "AAA"}, {"sector_map": {101: "Technology"}}

    monkeypatch.setattr(data_orch, "load_dashboard_data", _fake_load_dashboard_data)

    package = data_orch._load_historical_data(
        top_n=1,
        start_year=2026,
        universe_mode="top_liquid",
        asof_date=None,
        processed_dir="unused",
        static_dir="unused",
    )

    assert float(package.prices.loc[idx[-1], 101]) == 102.0
    assert float(package.returns.loc[idx[-1], 101]) == 0.02
    assert package.metadata["prices_shape"] == prices.shape
    assert package.metadata["returns_shape"] == returns.shape


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


def test_batched_pit_loader_keeps_full_membership_proof_while_loading_selected_prices(tmp_path) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()

    universe = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-02"]),
            "permno": [101, 202, 303],
            "ticker": ["AAA", "BBB", "CCC"],
            "gvkey": ["", "", ""],
            "provenance": ["test", "test", "test"],
        }
    )
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-02"]),
            "permno": [101, 202, 303],
            "ticker": ["AAA", "BBB", "CCC"],
            "tri": [100.0, 200.0, 300.0],
            "total_ret": [0.01, 0.02, 0.03],
            "raw_close": [10.0, 20.0, 30.0],
            "volume": [1.0, 1.0, 1.0],
        }
    )
    tickers = pd.DataFrame({"permno": [101, 202, 303], "ticker": ["AAA", "BBB", "CCC"]})
    universe.to_parquet(processed / "universe_r3000_daily.parquet", index=False)
    prices.to_parquet(processed / "prices_tri.parquet", index=False)
    tickers.to_parquet(processed / "tickers.parquet", index=False)

    batched = data_orch.load_batched_pit_replay_data(
        processed_dir=processed,
        static_dir=static,
        start_date="2026-01-02",
        end_date="2026-01-02",
        selected_permnos=(202, 999),
    )

    assert batched.membership_index["2026-01-02"] == {101, 202, 303}
    assert list(batched.raw_prices.columns) == [202]
    assert list(batched.raw_returns.columns) == [202]
    assert batched.metadata["permnos_loaded"] == 3
    assert batched.metadata["price_permnos_loaded"] == 1
    assert batched.metadata["price_load_scope"] == "selected_pit_membership_intersection"
    assert batched.metadata["selected_permnos_requested"] == [202, 999]
    assert batched.metadata["selected_permnos_in_pit_window"] == [202]
    assert batched.metadata["pit_membership_proof"] == "full_window_membership_index"
