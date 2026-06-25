from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "parameter_sweep.py"


def _load_script_module():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("parameter_sweep", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_cfg(mod):
    return mod.SweepConfig(
        panel_path="panel.parquet",
        prices_path="prices.parquet",
        features_path="features.parquet",
        sector_map_path="sector_map.parquet",
        start_date=None,
        end_date=None,
        horizon_days=21,
        high_asset_growth_pct=0.30,
        min_high_group_size=2,
        nw_lags=None,
        cscv_blocks=6,
        seed=42,
        coarse_sales_weights=(0.0, 1.0),
        coarse_margin_weights=(0.0, 1.0),
        coarse_bloat_weights=(-1.0, 0.0),
        coarse_netinv_weights=(-1.0, 0.0),
        coarse_gate_thresholds=(-0.5, 0.0),
        fine_step_sales=0.25,
        fine_step_margin=0.25,
        fine_step_bloat=0.25,
        fine_step_netinv=0.25,
        fine_step_gate=0.10,
        max_coarse_combos=200,
        max_fine_combos=96,
        checkpoint_every=0,
        resume=True,
        keep_checkpoint=False,
        output_dir="out",
        output_prefix="test_sweep",
    )


def test_parse_float_list_and_coarse_grid_size_contract():
    mod = _load_script_module()
    parsed = mod._parse_float_list("-1,0,1")
    assert parsed == (-1.0, 0.0, 1.0)

    cfg = _make_cfg(mod)
    grid = mod._build_coarse_grid(cfg)
    expected = (
        len(cfg.coarse_sales_weights)
        * len(cfg.coarse_margin_weights)
        * len(cfg.coarse_bloat_weights)
        * len(cfg.coarse_netinv_weights)
        * len(cfg.coarse_gate_thresholds)
    )
    assert len(grid) == expected


def test_fine_grid_is_centered_around_best_point():
    mod = _load_script_module()
    cfg = _make_cfg(mod)
    best = {
        "w_sales": 0.5,
        "w_margin": 0.25,
        "w_bloat": -0.5,
        "w_netinv": -0.25,
        "gate_threshold": 0.1,
    }
    grid = mod._build_fine_grid(best=best, cfg=cfg)
    assert len(grid) == 243  # 3^5 neighborhood
    assert any(
        (g["w_sales"] == best["w_sales"])
        and (g["w_margin"] == best["w_margin"])
        and (g["w_bloat"] == best["w_bloat"])
        and (g["w_netinv"] == best["w_netinv"])
        and (g["gate_threshold"] == best["gate_threshold"])
        for g in grid
    )


def test_sample_grid_is_deterministic_for_fixed_seed():
    mod = _load_script_module()
    grid = [{"x": float(i)} for i in range(20)]
    a = mod._sample_grid(grid=grid, max_count=5, seed=123)
    b = mod._sample_grid(grid=grid, max_count=5, seed=123)
    assert len(a) == 5
    assert a == b


def test_variant_id_hash_is_stable_across_key_order():
    mod = _load_script_module()
    params_a = {
        "w_sales": 1.0,
        "w_margin": 0.0,
        "w_bloat": -1.0,
        "w_netinv": -0.5,
        "gate_threshold": 0.5,
    }
    params_b = {
        "gate_threshold": 0.5,
        "w_netinv": -0.5,
        "w_bloat": -1.0,
        "w_margin": 0.0,
        "w_sales": 1.0,
    }
    assert mod._variant_id_from_params(params_a) == mod._variant_id_from_params(params_b)


def test_dedupe_grid_is_idempotent_when_variant_id_key_already_present():
    mod = _load_script_module()
    grid = [
        {"w_sales": 1.0, "w_margin": 0.0, "w_bloat": -1.0, "w_netinv": -0.5, "gate_threshold": 0.5},
        {"w_sales": 1.0, "w_margin": 0.0, "w_bloat": -1.0, "w_netinv": -0.5, "gate_threshold": 0.5},
    ]
    once = mod._dedupe_grid_by_variant_id(grid)
    twice = mod._dedupe_grid_by_variant_id(once)
    assert len(once) == 1
    assert len(twice) == 1
    assert once[0]["variant_id"] == twice[0]["variant_id"]


def test_best_row_prefers_dsr_then_tstat_then_mean():
    mod = _load_script_module()
    df = pd.DataFrame(
        [
            {"variant_id": "v1", "dsr": 0.10, "t_stat_nw": 2.0, "period_mean": 0.02},
            {"variant_id": "v2", "dsr": 0.20, "t_stat_nw": 1.0, "period_mean": 0.01},
            {"variant_id": "v3", "dsr": 0.20, "t_stat_nw": 1.5, "period_mean": 0.005},
        ]
    )
    best = mod._best_row(df, primary_metric="dsr")
    assert str(best["variant_id"]) == "v3"


def test_resolve_checkpoint_every_auto_policy():
    mod = _load_script_module()
    assert mod._resolve_checkpoint_every(total_variants=50, requested=0) == 10
    assert mod._resolve_checkpoint_every(total_variants=120, requested=0) == 20
    assert mod._resolve_checkpoint_every(total_variants=500, requested=0) == 50
    assert mod._resolve_checkpoint_every(total_variants=500, requested=7) == 7


def test_sweep_lock_rejects_live_pid(tmp_path):
    mod = _load_script_module()
    lock_path = mod._sweep_lock_path(str(tmp_path), "lock_live")
    payload = {
        "pid": int(os.getpid()),
        "created_at_utc": pd.Timestamp.utcnow().isoformat(),
        "output_prefix": "lock_live",
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    with pytest.raises(RuntimeError):
        mod._acquire_sweep_lock(str(tmp_path), "lock_live", stale_lock_seconds=3600)


def test_sweep_lock_recovers_dead_pid(monkeypatch, tmp_path):
    mod = _load_script_module()
    lock_path = mod._sweep_lock_path(str(tmp_path), "lock_dead")
    payload = {
        "pid": 999999,
        "created_at_utc": pd.Timestamp.utcnow().isoformat(),
        "output_prefix": "lock_dead",
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    monkeypatch.setattr(mod, "_pid_is_running", lambda _pid: False)
    acquired = mod._acquire_sweep_lock(str(tmp_path), "lock_dead", stale_lock_seconds=3600)
    assert acquired == lock_path
    assert os.path.exists(acquired)
    mod._release_sweep_lock(acquired)
    assert not os.path.exists(acquired)


def test_sweep_lock_ttl_fallback_recovers_invalid_pid_lock(tmp_path):
    mod = _load_script_module()
    lock_path = mod._sweep_lock_path(str(tmp_path), "lock_ttl")
    payload = {
        "pid": "bad",
        "created_at_utc": pd.Timestamp("2000-01-01", tz="UTC").isoformat(),
        "output_prefix": "lock_ttl",
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    acquired = mod._acquire_sweep_lock(str(tmp_path), "lock_ttl", stale_lock_seconds=10)
    assert acquired == lock_path
    mod._release_sweep_lock(acquired)


def test_sweep_lock_ttl_fallback_recovers_corrupt_lock_by_file_mtime(tmp_path):
    mod = _load_script_module()
    lock_path = mod._sweep_lock_path(str(tmp_path), "lock_corrupt")
    with open(lock_path, "w", encoding="utf-8") as f:
        f.write("{not-json")
    old_ts = pd.Timestamp("2000-01-01", tz="UTC").timestamp()
    os.utime(lock_path, (old_ts, old_ts))

    acquired = mod._acquire_sweep_lock(str(tmp_path), "lock_corrupt", stale_lock_seconds=10)
    assert acquired == lock_path
    mod._release_sweep_lock(acquired)


def test_sweep_lock_recovery_is_bounded_when_remove_fails(monkeypatch, tmp_path):
    mod = _load_script_module()
    lock_path = mod._sweep_lock_path(str(tmp_path), "lock_stuck")
    payload = {
        "pid": 999999,
        "created_at_utc": pd.Timestamp.utcnow().isoformat(),
        "output_prefix": "lock_stuck",
    }
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    monkeypatch.setattr(mod, "_pid_is_running", lambda _pid: False)
    monkeypatch.setattr(mod, "_safe_remove", lambda _path: None)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="Unable to remove stale sweep lock"):
        mod._acquire_sweep_lock(str(tmp_path), "lock_stuck", stale_lock_seconds=3600)


def test_prepare_proxy_components_emits_expected_columns():
    mod = _load_script_module()
    dates = pd.date_range("2024-01-01", periods=8, freq="D")
    frame = pd.DataFrame(
        {
            "date": list(dates) * 2,
            "permno": [10001] * len(dates) + [10002] * len(dates),
            "delta_revenue_inventory": np.linspace(-1.0, 1.0, 16),
            "operating_margin_delta_q": np.linspace(0.2, 0.8, 16),
            "revenue_inventory_q": np.linspace(1.0, 2.0, 16),
            "asset_growth_yoy": np.linspace(-0.3, 0.3, 16),
        }
    )
    out = mod._prepare_proxy_components(frame)
    assert set(["date", "permno", "sales_z", "margin_z", "bloat_z", "netinv_z"]).issubset(set(out.columns))
    assert len(out) == len(frame)


def test_variant_spread_timeseries_positive_for_monotonic_proxy_and_returns():
    mod = _load_script_module()
    rows = []
    dt = pd.Timestamp("2024-03-29")
    for i in range(1, 31):
        rows.append(
            {
                "date": dt,
                "industry": "Semiconductors",
                "permno": i,
                "fwd_return": float(i) / 1000.0,
                "sales_z": float(i),
                "margin_z": 0.0,
                "bloat_z": 0.0,
                "netinv_z": 0.0,
            }
        )
    high_base = pd.DataFrame(rows)
    spread = mod._variant_spread_timeseries(
        high_base=high_base,
        w_sales=1.0,
        w_margin=0.0,
        w_bloat=0.0,
        w_netinv=0.0,
        gate_threshold=0.0,
        min_high_group_size=1,
    )
    assert not spread.empty
    assert float(spread["spread"].iloc[0]) > 0.0


def test_evaluate_grid_resume_only_path_keeps_existing_state_and_triggers_checkpoint():
    mod = _load_script_module()
    params = {
        "w_sales": 1.0,
        "w_margin": 0.0,
        "w_bloat": -1.0,
        "w_netinv": -0.5,
        "gate_threshold": 0.5,
    }
    variant_id = mod._variant_id_from_params(params)
    existing_results = pd.DataFrame(
        [
            {
                "variant_id": variant_id,
                "stage": "coarse",
                **params,
                "period_mean": 0.01,
                "period_vol": 0.02,
                "annualized_sharpe": 1.0,
                "t_stat_nw": 2.0,
            }
        ]
    )
    existing_streams = pd.DataFrame(
        {variant_id: [0.01, 0.02]},
        index=pd.to_datetime(["2024-01-31", "2024-02-29"]),
    )
    callback_rows: list[dict[str, object]] = []

    def _checkpoint_cb(stage, stage_results, stage_streams, completed, total, stage_completed):
        callback_rows.append(
            {
                "stage": stage,
                "completed": completed,
                "total": total,
                "stage_completed": stage_completed,
                "n_results": int(len(stage_results)),
                "stream_cols": list(stage_streams.columns),
            }
        )

    out_results, out_streams = mod._evaluate_grid(
        stage="coarse",
        grid=[params],
        high_base=pd.DataFrame(),
        horizon_days=21,
        nw_lags=None,
        min_high_group_size=2,
        existing_results=existing_results,
        existing_streams=existing_streams,
        checkpoint_every=10,
        checkpoint_callback=_checkpoint_cb,
        summarize_spread_fn=lambda **_kwargs: {},
    )

    assert len(callback_rows) == 1
    assert callback_rows[0]["stage"] == "coarse"
    assert callback_rows[0]["completed"] == 1
    assert callback_rows[0]["total"] == 1
    assert callback_rows[0]["stage_completed"] is True
    assert callback_rows[0]["n_results"] == 1
    assert callback_rows[0]["stream_cols"] == [variant_id]
    assert list(out_results["variant_id"].astype(str)) == [variant_id]
    assert list(out_streams.columns) == [variant_id]
