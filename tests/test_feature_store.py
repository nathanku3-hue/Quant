from __future__ import annotations

import errno
import json
import os
import time

import numpy as np
import pandas as pd
import pytest

from data.feature_store import (
    FeatureStoreConfig,
    UNIVERSE_MODE_YEARLY_UNION,
    _atomic_upsert_features,
    _feature_spec_hash,
    _read_feature_date_bounds,
    compute_feature_frame,
    run_build,
)
from data.feature_specs import FeatureSpec, build_default_feature_specs


def _make_prices_long(n_days: int = 260) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    idx = pd.date_range("2024-01-01", periods=n_days, freq="B")

    # Asset A: stronger trend, lower illiquidity.
    a_close = pd.Series(np.linspace(100.0, 180.0, n_days), index=idx)
    a_ret = a_close.pct_change(fill_method=None).fillna(0.0)
    a_vol = pd.Series(2_000_000.0, index=idx)

    # Asset B: weaker trend, higher illiquidity.
    b_close = pd.Series(np.linspace(100.0, 110.0, n_days), index=idx)
    b_ret = b_close.pct_change(fill_method=None).fillna(0.0)
    b_vol = pd.Series(200_000.0, index=idx)

    prices = pd.DataFrame(
        {
            "date": list(idx) * 2,
            "permno": [101] * n_days + [202] * n_days,
            "adj_close": np.concatenate([a_close.values, b_close.values]),
            "total_ret": np.concatenate([a_ret.values, b_ret.values]),
            "volume": np.concatenate([a_vol.values, b_vol.values]),
        }
    )

    market_close = pd.Series(np.linspace(100.0, 140.0, n_days), index=idx, name="spy_close")
    ticker_map = pd.DataFrame({"permno": [101, 202], "ticker": ["AAA", "BBB"]})
    return prices, market_close, ticker_map


def test_feature_store_schema_and_modes():
    prices, market_close, ticker_map = _make_prices_long()
    cfg = FeatureStoreConfig(top_n=2)

    feats = compute_feature_frame(
        prices_long=prices,
        market_close=market_close,
        ticker_map=ticker_map,
        cfg=cfg,
    )

    required = {
        "date",
        "permno",
        "ticker",
        "rolling_beta_63d",
        "resid_mom_60d",
        "amihud_20d",
        "yz_vol_20d",
        "atr_14d",
        "rsi_14d",
        "dist_sma20",
        "trend_veto",
        "composite_score",
        "z_moat",
        "z_inventory_quality_proxy",
        "z_discipline_cond",
        "z_demand",
        "capital_cycle_score",
        "yz_mode",
        "atr_mode",
    }
    assert required.issubset(set(feats.columns))
    assert set(feats["yz_mode"].dropna().unique()) == {"proxy_close_only"}
    assert set(feats["atr_mode"].dropna().unique()) == {"proxy_close_only"}
    assert feats["trend_veto"].dtype == bool


def test_dist_sma20_is_backward_looking():
    prices, market_close, ticker_map = _make_prices_long(n_days=80)
    cfg = FeatureStoreConfig(sma_short_window=20, top_n=2)
    feats = compute_feature_frame(
        prices_long=prices,
        market_close=market_close,
        ticker_map=ticker_map,
        cfg=cfg,
    )

    a = feats[feats["permno"] == 101].set_index("date").sort_index()
    target_date = a.index[40]
    close_series = (
        prices[prices["permno"] == 101]
        .set_index("date")
        .sort_index()["adj_close"]
    )
    sma20 = close_series.loc[:target_date].tail(20).mean()
    expected = (close_series.loc[target_date] - sma20) / sma20
    got = float(a.loc[target_date, "dist_sma20"])
    assert np.isfinite(got)
    np.testing.assert_allclose(got, expected, rtol=1e-12, atol=1e-12)


def test_residual_momentum_and_composite_rank_direction():
    prices, market_close, ticker_map = _make_prices_long()
    cfg = FeatureStoreConfig(top_n=2)
    feats = compute_feature_frame(
        prices_long=prices,
        market_close=market_close,
        ticker_map=ticker_map,
        cfg=cfg,
    )
    last_date = feats["date"].max()
    last = feats[feats["date"] == last_date].set_index("permno")

    # Asset A has stronger absolute/relative trend and better liquidity in synthetic setup.
    assert float(last.loc[101, "rel_strength_60d"]) > float(last.loc[202, "rel_strength_60d"])
    assert float(last.loc[101, "amihud_20d"]) < float(last.loc[202, "amihud_20d"])
    assert np.isfinite(float(last.loc[101, "composite_score"]))
    assert np.isfinite(float(last.loc[202, "composite_score"]))


def test_select_universe_permnos_yearly_union_uses_active_anchor_selector(monkeypatch):
    import data.feature_store as fs_mod

    captured: dict[str, object] = {}

    def _should_not_call_global(_top_n: int) -> list[int]:
        raise AssertionError("global selector should not run in yearly_union mode")

    def _fake_yearly_union(
        yearly_top_n: int,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp | None = None,
    ) -> list[int]:
        captured["yearly_top_n"] = yearly_top_n
        captured["start_date"] = pd.Timestamp(start_date)
        captured["end_date"] = pd.Timestamp(end_date) if end_date is not None else None
        return [202, 101]

    monkeypatch.setattr(fs_mod, "_top_liquid_permnos", _should_not_call_global)
    monkeypatch.setattr(fs_mod, "_top_liquid_permnos_yearly_union", _fake_yearly_union)

    start_date = pd.Timestamp("2024-01-10")
    end_date = pd.Timestamp("2024-12-31")
    cfg = FeatureStoreConfig(
        universe_mode=UNIVERSE_MODE_YEARLY_UNION,
        top_n=999,
        yearly_top_n=2,
    )

    permnos = fs_mod._select_universe_permnos(
        cfg=cfg,
        start_date=start_date,
        end_date=end_date,
    )

    assert permnos == [202, 101]
    assert captured == {
        "yearly_top_n": 2,
        "start_date": start_date,
        "end_date": end_date,
    }


def test_top_liquid_permnos_yearly_union_is_asof_anchored(tmp_path, monkeypatch):
    import data.feature_store as fs_mod

    def _select_with_late_year_spike(spike_permno: int) -> list[int]:
        base_path = tmp_path / f"prices_{spike_permno}.parquet"
        prices = pd.DataFrame(
            {
                "date": pd.to_datetime(
                    [
                        "2023-02-01",
                        "2023-02-01",
                        "2023-07-03",
                        "2023-07-03",
                        "2024-01-03",
                        "2024-01-03",
                        "2024-12-20",
                    ]
                ),
                "permno": [101, 202, 101, 202, 101, 202, spike_permno],
                "adj_close": [10.0, 10.0, 11.0, 11.0, 12.0, 12.0, 12.0],
                "volume": [1_000.0, 700.0, 1_000.0, 700.0, 100.0, 100.0, 50_000_000.0],
            }
        )
        prices.to_parquet(base_path, index=False)
        monkeypatch.setattr(
            fs_mod,
            "_price_source_config",
            lambda: {
                "mode": "legacy",
                "base": str(base_path),
                "patch": None,
                "price_col": "adj_close",
                "legacy_col": "adj_close",
            },
        )
        return fs_mod._top_liquid_permnos_yearly_union(
            yearly_top_n=1,
            start_date=pd.Timestamp("2024-01-10"),
            end_date=pd.Timestamp("2024-12-31"),
        )

    first = _select_with_late_year_spike(spike_permno=101)
    second = _select_with_late_year_spike(spike_permno=202)
    assert first == [101]
    assert second == [101]


def test_top_liquid_permnos_yearly_union_excludes_same_day_spike(tmp_path, monkeypatch):
    import data.feature_store as fs_mod

    base_path = tmp_path / "prices_same_day_spike.parquet"
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(
                [
                    "2024-01-09",
                    "2024-01-09",
                    "2024-01-10",
                ]
            ),
            "permno": [101, 202, 303],
            "adj_close": [10.0, 10.0, 10.0],
            "volume": [2_000.0, 1_000.0, 50_000_000.0],
        }
    )
    prices.to_parquet(base_path, index=False)

    monkeypatch.setattr(
        fs_mod,
        "_price_source_config",
        lambda: {
            "mode": "legacy",
            "base": str(base_path),
            "patch": None,
            "price_col": "adj_close",
            "legacy_col": "adj_close",
        },
    )

    permnos = fs_mod._top_liquid_permnos_yearly_union(
        yearly_top_n=1,
        start_date=pd.Timestamp("2024-01-10"),
        end_date=pd.Timestamp("2024-12-31"),
    )
    assert permnos == [101]


def test_top_liquid_permnos_yearly_union_uses_patch_precedence_before_anchor(tmp_path, monkeypatch):
    import data.feature_store as fs_mod

    base_path = tmp_path / "prices_patch_base.parquet"
    patch_path = tmp_path / "prices_patch_overlay.parquet"
    base_prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2023-06-30", "2023-06-30"]),
            "permno": [101, 202],
            "adj_close": [10.0, 10.0],
            "volume": [1_000.0, 900.0],
        }
    )
    patch_prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2023-06-30", "2024-12-20"]),
            "permno": [202, 101],
            "adj_close": [10.0, 10.0],
            "volume": [3_000.0, 99_000_000.0],
        }
    )
    base_prices.to_parquet(base_path, index=False)
    patch_prices.to_parquet(patch_path, index=False)

    monkeypatch.setattr(
        fs_mod,
        "_price_source_config",
        lambda: {
            "mode": "legacy",
            "base": str(base_path),
            "patch": str(patch_path),
            "price_col": "adj_close",
            "legacy_col": "adj_close",
        },
    )

    permnos = fs_mod._top_liquid_permnos_yearly_union(
        yearly_top_n=1,
        start_date=pd.Timestamp("2024-01-10"),
        end_date=pd.Timestamp("2024-12-31"),
    )
    assert permnos == [202]


def test_compute_feature_frame_plumbs_binding_token_in_strict_mode(monkeypatch):
    import data.feature_store as fs_mod

    prices, market_close, ticker_map = _make_prices_long(n_days=80)
    cfg = FeatureStoreConfig(top_n=2)
    captured: dict[str, str] = {}

    monkeypatch.setenv("T0_STRICT_SIMULATION_TS_BINDING", "1")
    monkeypatch.setenv("T0_SIMULATION_TS_BINDING_SECRET", "unit-test-secret")

    def _fake_token(simulation_ts, secret=None):
        captured["token_input"] = str(simulation_ts)
        captured["secret"] = str(secret or "")
        return "tok-123"

    original_daily = fs_mod.fundamentals_data.build_fundamentals_daily
    original_snapshot = fs_mod.fundamentals_data.load_fundamentals_snapshot

    def _daily_wrapper(*args, **kwargs):
        captured["daily_token"] = str(kwargs.get("simulation_ts_binding_token", ""))
        captured["daily_secret"] = str(kwargs.get("simulation_ts_binding_secret", ""))
        return original_daily(*args, **kwargs)

    def _snapshot_wrapper(*args, **kwargs):
        captured["snap_token"] = str(kwargs.get("simulation_ts_binding_token", ""))
        captured["snap_secret"] = str(kwargs.get("simulation_ts_binding_secret", ""))
        return original_snapshot(*args, **kwargs)

    monkeypatch.setattr(fs_mod.fundamentals_data, "create_simulation_ts_binding_token", _fake_token)
    monkeypatch.setattr(fs_mod.fundamentals_data, "build_fundamentals_daily", _daily_wrapper)
    monkeypatch.setattr(fs_mod.fundamentals_data, "load_fundamentals_snapshot", _snapshot_wrapper)

    out = compute_feature_frame(
        prices_long=prices,
        market_close=market_close,
        ticker_map=ticker_map,
        cfg=cfg,
    )

    assert not out.empty
    assert captured["daily_token"] == "tok-123"
    assert captured["snap_token"] == "tok-123"
    assert captured["daily_secret"] == "unit-test-secret"
    assert captured["snap_secret"] == "unit-test-secret"


def test_execute_feature_specs_fails_closed_on_spec_exception():
    import data.feature_store as fs_mod

    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    base = pd.DataFrame([[1.0, 2.0]], index=idx, columns=[101, 202])

    def _boom(_context, _spec):
        raise ValueError("exploded")

    spec = FeatureSpec(
        name="bad_spec",
        func=_boom,
        category="technical",
        inputs=("signal",),
    )
    status = fs_mod._new_status()
    with pytest.raises(fs_mod.FeatureSpecExecutionError, match="bad_spec"):
        fs_mod._execute_feature_specs(
            specs=[spec],
            feature_context={"signal": base},
            dependency_columns=set(),
            status=status,
        )
    assert any("bad_spec" in msg for msg in status["warnings"])


def test_execute_feature_specs_fails_closed_on_non_dataframe_result():
    import data.feature_store as fs_mod

    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    base = pd.DataFrame([[1.0]], index=idx, columns=[101])
    spec = FeatureSpec(
        name="bad_type_result_spec",
        func=lambda _context, _spec: 1.23,
        category="technical",
        inputs=("signal",),
    )
    with pytest.raises(fs_mod.FeatureSpecExecutionError, match="invalid type"):
        fs_mod._execute_feature_specs(
            specs=[spec],
            feature_context={"signal": base},
            dependency_columns=set(),
            status=fs_mod._new_status(),
        )


def test_execute_feature_specs_fails_closed_on_missing_inputs():
    import data.feature_store as fs_mod

    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    base = pd.DataFrame([[1.0]], index=idx, columns=[101])
    spec = FeatureSpec(
        name="needs_missing_input",
        func=lambda context, _spec: context["missing_input"],
        category="fundamental",
        inputs=("missing_input",),
    )
    with pytest.raises(fs_mod.FeatureSpecExecutionError, match="missing required context inputs"):
        fs_mod._execute_feature_specs(
            specs=[spec],
            feature_context={"signal": base},
            dependency_columns=set(),
            status=fs_mod._new_status(),
        )


def test_execute_feature_specs_fails_closed_on_missing_fundamental_dependencies():
    import data.feature_store as fs_mod

    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    base = pd.DataFrame([[1.0]], index=idx, columns=[101])
    spec = FeatureSpec(
        name="z_moat_missing_snapshot_dep",
        func=lambda context, _spec: context["roic"],
        category="fundamental",
        inputs=("roic",),
    )
    with pytest.raises(fs_mod.FeatureSpecExecutionError, match="missing dependency columns"):
        fs_mod._execute_feature_specs(
            specs=[spec],
            feature_context={"roic": base},
            dependency_columns=set(),
            status=fs_mod._new_status(),
        )


def test_execute_feature_specs_allows_fundamental_inputs_from_prior_spec_outputs():
    import data.feature_store as fs_mod

    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-02")])
    base = pd.DataFrame([[1.0]], index=idx, columns=[101])
    spec_seed = FeatureSpec(
        name="z_inventory_quality_proxy",
        func=lambda context, _spec: context["roic"] * 2.0,
        category="fundamental",
        inputs=("roic",),
    )
    spec_consumer = FeatureSpec(
        name="capital_cycle_score",
        func=lambda context, _spec: context["z_inventory_quality_proxy"],
        category="fundamental",
        inputs=("z_inventory_quality_proxy",),
    )
    out = fs_mod._execute_feature_specs(
        specs=[spec_seed, spec_consumer],
        feature_context={"roic": base},
        dependency_columns={"roic"},
        status=fs_mod._new_status(),
    )
    assert float(out["z_inventory_quality_proxy"].iloc[0, 0]) == pytest.approx(2.0)
    assert float(out["capital_cycle_score"].iloc[0, 0]) == pytest.approx(2.0)


def test_read_feature_date_bounds(tmp_path):
    path = tmp_path / "features.parquet"
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"]),
            "permno": [1, 1, 1],
            "composite_score": [0.1, 0.2, 0.3],
        }
    )
    df.to_parquet(path, index=False)
    min_ts, max_ts = _read_feature_date_bounds(str(path))
    assert min_ts == pd.Timestamp("2024-01-01")
    assert max_ts == pd.Timestamp("2024-01-03")


def test_atomic_upsert_features_prefers_new_rows(tmp_path):
    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)
    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
            "permno": [10001, 10001],
            "composite_score": [9.9, 0.3],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))
    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert len(out) == 3
    assert float(out.loc[out["date"] == pd.Timestamp("2024-01-02"), "composite_score"].iloc[0]) == pytest.approx(9.9)


def test_atomic_upsert_features_recovers_missing_live_dataset_from_backup(tmp_path, monkeypatch):
    import data.feature_store as fs_mod
    from data import updater as updater_mod

    path = tmp_path / "features.parquet"
    backup_path = tmp_path / "features.parquet.bak.crash"
    lock_path = tmp_path / ".update.lock"
    monkeypatch.setattr(updater_mod, "UPDATE_LOCK_PATH", str(lock_path))
    lock_path.write_text(
        f"pid={os.getpid()} ts={int(time.time())} token=self-owner",
        encoding="utf-8",
    )

    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"]),
            "permno": [10001],
            "composite_score": [0.1],
        }
    )
    fs_mod._write_partitioned_feature_dataset(existing, str(path), expected_lock_token="self-owner")
    os.replace(path, backup_path)
    assert not path.exists()
    assert backup_path.exists()

    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"]),
            "permno": [10001],
            "composite_score": [0.2],
        }
    )
    _atomic_upsert_features(
        existing_path=str(path),
        new_rows=new_rows,
        output_path=str(path),
        expected_lock_token="self-owner",
    )

    assert path.is_dir()
    assert not backup_path.exists()
    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert len(out) == 2
    assert float(out.iloc[0]["composite_score"]) == pytest.approx(0.1)
    assert float(out.iloc[1]["composite_score"]) == pytest.approx(0.2)


def test_atomic_upsert_features_migrates_file_and_rewrites_only_touched_partition(tmp_path):
    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-15", "2024-02-05"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)

    new_feb = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-05", "2024-02-20"]),
            "permno": [10001, 10001],
            "composite_score": [9.9, 0.3],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_feb, output_path=str(path))
    assert path.is_dir()
    jan_dir = path / "year=2024" / "month=01"
    feb_dir = path / "year=2024" / "month=02"
    assert jan_dir.exists()
    assert feb_dir.exists()

    jan_files = sorted(jan_dir.glob("*.parquet"))
    assert jan_files
    jan_mtime_before = max(f.stat().st_mtime_ns for f in jan_files)

    time.sleep(0.01)
    new_feb_only = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-28"]),
            "permno": [10001],
            "composite_score": [0.4],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_feb_only, output_path=str(path))

    jan_files_after = sorted(jan_dir.glob("*.parquet"))
    assert jan_files_after
    jan_mtime_after = max(f.stat().st_mtime_ns for f in jan_files_after)
    assert jan_mtime_after == jan_mtime_before

    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert len(out) == 4
    assert float(out.loc[out["date"] == pd.Timestamp("2024-02-05"), "composite_score"].iloc[0]) == pytest.approx(9.9)
    assert float(out.loc[out["date"] == pd.Timestamp("2024-02-28"), "composite_score"].iloc[0]) == pytest.approx(0.4)


def test_atomic_upsert_features_batches_partition_reads_with_single_connection(tmp_path, monkeypatch):
    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-15", "2024-02-05"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)

    import data.feature_store as fs_mod

    real_connect = fs_mod.duckdb.connect
    connect_calls = {"count": 0}

    def counted_connect(*args, **kwargs):
        connect_calls["count"] += 1
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(fs_mod.duckdb, "connect", counted_connect)

    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-15", "2024-02-20"]),
            "permno": [10001, 10001],
            "composite_score": [1.1, 0.3],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))

    assert connect_calls["count"] == 1
    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert len(out) == 3
    assert float(out.loc[out["date"] == pd.Timestamp("2024-01-15"), "composite_score"].iloc[0]) == pytest.approx(1.1)
    assert float(out.loc[out["date"] == pd.Timestamp("2024-02-20"), "composite_score"].iloc[0]) == pytest.approx(0.3)


def test_atomic_upsert_features_reads_partitions_in_chunks(tmp_path, monkeypatch):
    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-15", "2024-02-05", "2024-03-06"]),
            "permno": [10001, 10001, 10001],
            "composite_score": [0.1, 0.2, 0.3],
        }
    )
    existing.to_parquet(path, index=False)

    import data.feature_store as fs_mod

    call_count = {"n": 0}
    real_loader = fs_mod._load_feature_partition_slices

    def counted_loader(*args, **kwargs):
        call_count["n"] += 1
        return real_loader(*args, **kwargs)

    monkeypatch.setattr(fs_mod, "_load_feature_partition_slices", counted_loader)

    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-15", "2024-02-20", "2024-03-28"]),
            "permno": [10001, 10001, 10001],
            "composite_score": [1.1, 0.25, 0.35],
        }
    )
    _atomic_upsert_features(
        existing_path=str(path),
        new_rows=new_rows,
        output_path=str(path),
        upsert_chunk_size=1,
    )
    assert call_count["n"] == 3
    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert float(out.loc[out["date"] == pd.Timestamp("2024-01-15"), "composite_score"].iloc[0]) == pytest.approx(1.1)
    assert float(out.loc[out["date"] == pd.Timestamp("2024-02-20"), "composite_score"].iloc[0]) == pytest.approx(0.25)
    assert float(out.loc[out["date"] == pd.Timestamp("2024-03-28"), "composite_score"].iloc[0]) == pytest.approx(0.35)


def test_atomic_upsert_features_writes_manifest_v2_with_sha256_seals(tmp_path):
    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)

    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))

    current_path = path / "_manifests" / "CURRENT"
    assert current_path.exists()
    commit_id = current_path.read_text(encoding="utf-8").strip()
    assert commit_id

    manifest_path = path / "_manifests" / f"{commit_id}.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest.get("version") == "v2"
    partitions = manifest.get("partitions")
    assert isinstance(partitions, dict)
    assert partitions
    for entry in partitions.values():
        assert isinstance(entry, dict)
        assert len(str(entry.get("sha256") or "")) == 64
        file_path = str(entry.get("file") or "")
        assert file_path
        assert os.path.exists(file_path)


def test_feature_store_scan_fails_closed_on_manifest_hash_mismatch(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)
    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    commit_id = str(manifest.get("commit_id") or "")
    assert commit_id
    manifest_path = path / "_manifests" / f"{commit_id}.json"
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = dict(obj.get("partitions") or {})
    first_key = next(iter(parts))
    parts[first_key]["sha256"] = "0" * 64
    obj["partitions"] = parts
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeError, match="hash mismatch"):
        fs_mod._feature_store_scan_sql(str(path))


def test_feature_store_scan_fails_closed_on_manifest_version_downgrade(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)
    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    commit_id = str(manifest.get("commit_id") or "")
    assert commit_id
    manifest_path = path / "_manifests" / f"{commit_id}.json"
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    obj["version"] = "v1"
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeError, match="manifest v2 is required"):
        fs_mod._feature_store_scan_sql(str(path))


def test_feature_store_scan_fails_closed_on_manifest_partition_mismatch(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-02-01"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)
    new_rows = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=new_rows, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    commit_id = str(manifest.get("commit_id") or "")
    assert commit_id
    manifest_path = path / "_manifests" / f"{commit_id}.json"
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = dict(obj.get("partitions") or {})
    first_key = next(iter(parts))
    first_entry = dict(parts.pop(first_key))
    parts["year=1900/month=01"] = first_entry
    obj["partitions"] = parts
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeError, match="partition/file mismatch"):
        fs_mod._feature_store_scan_sql(str(path))


def test_atomic_upsert_features_requires_lock_token_when_lock_file_exists(tmp_path, monkeypatch):
    import data.feature_store as fs_mod
    from data import updater as updater_mod

    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01", "2024-01-02"]),
            "permno": [10001, 10001],
            "composite_score": [0.1, 0.2],
        }
    )
    existing.to_parquet(path, index=False)

    lock_path = tmp_path / ".update.lock"
    monkeypatch.setattr(updater_mod, "UPDATE_LOCK_PATH", str(lock_path))
    token = updater_mod._acquire_update_lock(timeout_sec=1)
    try:
        new_rows = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-02", "2024-01-03"]),
                "permno": [10001, 10001],
                "composite_score": [1.1, 0.3],
            }
        )
        with pytest.raises(RuntimeError, match="missing lock token"):
            fs_mod._atomic_upsert_features(
                existing_path=str(path),
                new_rows=new_rows,
                output_path=str(path),
            )
        with pytest.raises(RuntimeError, match="lock token mismatch"):
            fs_mod._atomic_upsert_features(
                existing_path=str(path),
                new_rows=new_rows,
                output_path=str(path),
                expected_lock_token="invalid-token",
            )
        fs_mod._atomic_upsert_features(
            existing_path=str(path),
            new_rows=new_rows,
            output_path=str(path),
            expected_lock_token=token,
        )
    finally:
        updater_mod._release_update_lock(expected_token=token)

    out = pd.read_parquet(path).sort_values(["date", "permno"]).reset_index(drop=True)
    assert len(out) == 3
    assert float(out.loc[out["date"] == pd.Timestamp("2024-01-02"), "composite_score"].iloc[0]) == pytest.approx(1.1)


def test_ensure_partitioned_feature_store_fails_closed_when_manifest_missing(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    part_dir = path / "year=2024" / "month=01"
    part_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"]),
            "permno": [10001],
            "composite_score": [0.1],
        }
    ).to_parquet(part_dir / "part-000.parquet", index=False)
    assert not (path / "_manifests" / "CURRENT").exists()

    with pytest.raises(fs_mod.AmbiguousFeatureStoreStateError, match="missing CURRENT pointer/manifest lineage"):
        fs_mod._ensure_partitioned_feature_store(str(path))


def test_bootstrap_feature_manifest_v2_fails_on_ambiguous_partition_files(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    part_dir = path / "year=2024" / "month=01"
    part_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"]),
            "permno": [10001],
            "composite_score": [0.1],
        }
    )
    frame.to_parquet(part_dir / "part-000.parquet", index=False)
    frame.to_parquet(part_dir / "part-001.parquet", index=False)

    with pytest.raises(fs_mod.AmbiguousFeatureStoreStateError, match="Ambiguous feature-store partition state"):
        fs_mod._bootstrap_feature_manifest_v2(str(path), allow_unsealed_bootstrap=True)


def test_assert_same_filesystem_for_replace_fails_closed_on_cross_device(tmp_path, monkeypatch):
    import data.feature_store as fs_mod

    src_file = tmp_path / "src" / "part.stage"
    dst_file = tmp_path / "dst" / "part.parquet"
    src_dir = os.path.abspath(str(src_file.parent))
    dst_dir = os.path.abspath(str(dst_file.parent))
    real_stat = fs_mod.os.stat

    class _Stat:
        def __init__(self, st_dev: int):
            self.st_dev = int(st_dev)

    def fake_stat(target):
        abs_target = os.path.abspath(str(target))
        if abs_target == src_dir:
            return _Stat(1001)
        if abs_target == dst_dir:
            return _Stat(2002)
        return real_stat(target)

    monkeypatch.setattr(fs_mod.os, "stat", fake_stat)
    with pytest.raises(RuntimeError, match="same filesystem"):
        fs_mod._assert_same_filesystem_for_replace(str(src_file), str(dst_file))


def test_set_feature_current_commit_fails_closed_on_exdev_and_preserves_pointer(tmp_path, monkeypatch):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    manifests_dir = path / "_manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    old_commit = "a1b2c3d4e5f60718"
    new_commit = "f0e1d2c3b4a59687"
    (manifests_dir / f"{old_commit}.json").write_text(json.dumps({"commit_id": old_commit}), encoding="utf-8")
    (manifests_dir / f"{new_commit}.json").write_text(json.dumps({"commit_id": new_commit}), encoding="utf-8")
    current_path = manifests_dir / "CURRENT"
    current_path.write_text(f"{old_commit}\n", encoding="utf-8")

    real_replace = fs_mod.os.replace

    def fake_replace(src, dst):
        if os.path.abspath(str(dst)) == os.path.abspath(str(current_path)):
            raise OSError(errno.EXDEV, "Invalid cross-device link")
        return real_replace(src, dst)

    monkeypatch.setattr(fs_mod, "_assert_same_filesystem_for_replace", lambda src, dst: None)
    monkeypatch.setattr(fs_mod.os, "replace", fake_replace)

    with pytest.raises(OSError) as exinfo:
        fs_mod._set_feature_current_commit(str(path), new_commit)
    assert int(exinfo.value.errno or -1) == int(errno.EXDEV)
    assert current_path.read_text(encoding="utf-8").strip() == old_commit


def test_manifest_tombstones_include_retention_window(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [0.2],
        }
    ).to_parquet(path, index=False)
    rows_a = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    rows_b = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [2.2],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_a, output_path=str(path))
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_b, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    committed = pd.Timestamp(str(manifest.get("committed_at_utc")))
    tombstones = list(manifest.get("tombstones") or [])
    assert tombstones
    for row in tombstones:
        retained = pd.Timestamp(str(row.get("retained_until_utc") or ""))
        assert isinstance(retained, pd.Timestamp)
        assert not pd.isna(retained)
        assert retained >= committed + pd.Timedelta(hours=23)


def test_feature_store_scan_fails_closed_on_missing_tombstone_retention(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [0.2],
        }
    ).to_parquet(path, index=False)
    rows_a = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    rows_b = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [2.2],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_a, output_path=str(path))
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_b, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    commit_id = str(manifest.get("commit_id") or "")
    manifest_path = path / "_manifests" / f"{commit_id}.json"
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    obj_tombstones = list(obj.get("tombstones") or [])
    assert obj_tombstones
    obj_tombstones[0].pop("retained_until_utc", None)
    obj["tombstones"] = obj_tombstones
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeError, match="retained_until_utc"):
        fs_mod._feature_store_scan_sql(str(path))


def test_feature_store_scan_blocks_tombstoned_active_file(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [0.2],
        }
    ).to_parquet(path, index=False)
    rows_a = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    rows_b = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [2.2],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_a, output_path=str(path))
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_b, output_path=str(path))

    manifest = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest, dict)
    commit_id = str(manifest.get("commit_id") or "")
    manifest_path = path / "_manifests" / f"{commit_id}.json"
    obj = json.loads(manifest_path.read_text(encoding="utf-8"))
    tombstones = list(obj.get("tombstones") or [])
    assert tombstones
    zombie = tombstones[0]
    partition = str(zombie.get("partition") or "")
    zombie_file = str(zombie.get("file") or "")
    assert partition in obj.get("partitions", {})
    assert os.path.exists(zombie_file)
    obj["partitions"][partition]["file"] = zombie_file
    obj["partitions"][partition]["sha256"] = fs_mod._compute_file_sha256(zombie_file)
    obj["partitions"][partition]["size_bytes"] = int(os.path.getsize(zombie_file))
    manifest_path.write_text(json.dumps(obj, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(RuntimeError, match="tombstone_priority"):
        fs_mod._feature_store_scan_sql(str(path))


def test_set_feature_current_commit_rolls_back_manifest_view(tmp_path):
    import data.feature_store as fs_mod

    path = tmp_path / "features.parquet"
    existing = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [0.2],
        }
    )
    existing.to_parquet(path, index=False)

    rows_a = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [1.1],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_a, output_path=str(path))
    manifest_a = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest_a, dict)
    commit_a = str(manifest_a.get("commit_id") or "")
    assert commit_a

    rows_b = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-02-01"]),
            "permno": [10001],
            "composite_score": [2.2],
        }
    )
    _atomic_upsert_features(existing_path=str(path), new_rows=rows_b, output_path=str(path))
    manifest_b = fs_mod._read_feature_manifest(str(path))
    assert isinstance(manifest_b, dict)
    commit_b = str(manifest_b.get("commit_id") or "")
    assert commit_b and commit_b != commit_a

    con = fs_mod.duckdb.connect()
    try:
        fs_mod._set_feature_current_commit(str(path), commit_a)
        sql_a = fs_mod._feature_store_scan_sql(str(path))
        val_a = con.execute(
            f"SELECT composite_score FROM {sql_a} WHERE permno=10001 AND CAST(date AS DATE)=DATE '2024-02-01'"
        ).fetchone()
        assert val_a is not None
        assert float(val_a[0]) == pytest.approx(1.1)

        fs_mod._set_feature_current_commit(str(path), commit_b)
        sql_b = fs_mod._feature_store_scan_sql(str(path))
        val_b = con.execute(
            f"SELECT composite_score FROM {sql_b} WHERE permno=10001 AND CAST(date AS DATE)=DATE '2024-02-01'"
        ).fetchone()
        assert val_b is not None
        assert float(val_b[0]) == pytest.approx(2.2)
    finally:
        con.close()


def test_run_build_incremental_noop_when_features_ahead_of_today(tmp_path, monkeypatch):
    feature_path = tmp_path / "features.parquet"
    now_utc = pd.Timestamp.utcnow()
    today = (now_utc.tz_localize(None) if now_utc.tzinfo is not None else now_utc).normalize()
    existing = pd.DataFrame(
        {
            "date": [today],
            "permno": [10001],
            "ticker": ["AAA"],
            "adj_close": [100.0],
            "tri": [100.0],
            "volume": [1_000_000.0],
            "rolling_beta_63d": [np.nan],
            "resid_mom_60d": [np.nan],
            "rel_strength_60d": [np.nan],
            "amihud_20d": [np.nan],
            "illiq_21d": [np.nan],
            "yz_vol_20d": [np.nan],
            "realized_vol_21d": [np.nan],
            "atr_14d": [np.nan],
            "rsi_14d": [np.nan],
            "dist_sma20": [np.nan],
            "sma200": [np.nan],
            "trend_veto": [False],
            "z_resid_mom": [np.nan],
            "z_flow_proxy": [np.nan],
            "z_vol_penalty": [np.nan],
            "composite_score": [np.nan],
            "z_moat": [np.nan],
            "z_inventory_quality_proxy": [np.nan],
            "z_discipline_cond": [np.nan],
            "z_demand": [np.nan],
            "capital_cycle_score": [np.nan],
            "quality_composite": [np.nan],
            "yz_mode": ["proxy_close_only"],
            "atr_mode": ["proxy_close_only"],
            "year": [today.year],
            "month": [today.month],
        }
    )
    existing.to_parquet(feature_path, index=False)

    import data.feature_store as fs_mod

    monkeypatch.setattr(fs_mod, "FEATURES_PATH", str(feature_path))
    monkeypatch.setattr(fs_mod.updater, "UPDATE_LOCK_PATH", str(tmp_path / ".update.lock"))

    result = run_build(start_year=int(today.year - 1), incremental=True, allow_missing_pinned_universe=True)
    assert result["success"] is True
    assert result["rows_written"] == 0


def test_feature_spec_hash_is_deterministic():
    specs_a = build_default_feature_specs()
    specs_b = build_default_feature_specs()
    assert _feature_spec_hash(specs_a) == _feature_spec_hash(specs_b)
