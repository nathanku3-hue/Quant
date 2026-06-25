from __future__ import annotations

import datetime as dt
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from core import auto_backtest_control_plane as cp


def _fresh_state() -> cp.AutoBacktestCacheState:
    fingerprint = cp.compute_config_fingerprint(cp.DEFAULT_CONFIG)
    return cp.AutoBacktestCacheState(
        config=cp.DEFAULT_CONFIG,
        config_fingerprint=fingerprint,
        last_run_key=None,
        run_attempted=False,
        run_attempted_for_key=None,
        status="idle",
        last_started_at=None,
        last_finished_at=None,
    )


def test_normalize_config_clamps_and_converts_inputs():
    config = cp.normalize_config(
        {
            "ma_lookback": "47",
            "stop_lookback": "90",
            "atr_period": 5,
            "vol_target": 35,
            "max_positions": 1,
            "cost_bps": 15,
            "cost_bps_unit": "bps",
            "min_price": -1,
        }
    )

    assert config.ma_lookback == 50
    assert config.stop_lookback == 60
    assert config.atr_period == 10
    assert config.vol_target == 0.30
    assert config.max_positions == 10
    assert config.cost_bps == 0.0015
    assert config.min_price == 1.0

    high_cost_config = cp.normalize_config({"cost_bps": 10000, "cost_bps_unit": "bps"})
    assert high_cost_config.cost_bps == 1.0

    fractional_bps_config = cp.normalize_config({"cost_bps": 0.5 / 10_000})
    assert fractional_bps_config.cost_bps == 0.00005

    explicit_rate_config = cp.normalize_config({"cost_bps": 2.0, "cost_bps_unit": "rate"})
    assert explicit_rate_config.cost_bps == 2.0


def test_load_cache_fail_closed_reasons(tmp_path: Path):
    missing = tmp_path / "missing_cache.json"
    missing_result = cp.load_cache(str(missing))
    assert missing_result.ok is False
    assert missing_result.reason == "missing_file"
    assert missing_result.state is None

    invalid_json = tmp_path / "invalid_json_cache.json"
    invalid_json.write_text("{not-valid-json", encoding="utf-8")
    invalid_json_result = cp.load_cache(str(invalid_json))
    assert invalid_json_result.ok is False
    assert invalid_json_result.reason == "invalid_json"
    assert invalid_json_result.state is None

    invalid_payload = tmp_path / "invalid_payload_cache.json"
    invalid_payload.write_text('{"config": "bad-shape"}', encoding="utf-8")
    invalid_payload_result = cp.load_cache(str(invalid_payload))
    assert invalid_payload_result.ok is False
    assert invalid_payload_result.reason == "invalid_payload"
    assert invalid_payload_result.state is None

    invalid_version = tmp_path / "invalid_version_cache.json"
    invalid_version.write_text(
        '{"version": 99, "config": {"ma_lookback": 200, "stop_lookback": 22, "atr_period": 20, "vol_target": 0.15, "max_positions": 50, "cost_bps": 0.001, "min_price": 5.0}, "config_fingerprint": "x", "run_attempted": false, "status": "idle"}',
        encoding="utf-8",
    )
    invalid_version_result = cp.load_cache(str(invalid_version))
    assert invalid_version_result.ok is False
    assert invalid_version_result.reason == "invalid_payload"
    assert invalid_version_result.state is None


def test_load_cache_reset_policy_returns_default_state(tmp_path: Path):
    cache_path = tmp_path / "missing_cache.json"
    load_result = cp.load_cache(str(cache_path), error_policy="reset")

    assert load_result.ok is True
    assert load_result.reason == "missing_file"
    assert load_result.state is not None
    assert load_result.state.config == cp.DEFAULT_CONFIG
    assert load_result.state.status == "idle"


def test_build_auto_backtest_plan_handles_stale_and_attempt_gating():
    cache_state = _fresh_state()

    config = cp.DEFAULT_CONFIG
    plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-27",
        config=config,
        cache_state=cache_state,
    )
    assert plan.is_stale is True
    assert plan.run_attempted is False
    assert plan.should_run is True
    assert plan.show_already_attempted_caption is False

    attempted_state = replace(
        cache_state,
        run_attempted=True,
        run_attempted_for_key=plan.run_key,
    )
    attempted_plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-27",
        config=config,
        cache_state=attempted_state,
    )
    assert attempted_plan.is_stale is True
    assert attempted_plan.run_attempted is True
    assert attempted_plan.should_run is False
    assert attempted_plan.show_already_attempted_caption is True

    finished_state = replace(
        attempted_state,
        last_run_key=plan.run_key,
        status="finished",
    )
    finished_plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-27",
        config=config,
        cache_state=finished_state,
    )
    assert finished_plan.is_stale is False
    assert finished_plan.should_run is False
    assert finished_plan.show_already_attempted_caption is False

    changed_day_plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-28",
        config=config,
        cache_state=attempted_state,
    )
    assert changed_day_plan.run_attempted is False
    assert changed_day_plan.should_run is True

    failed_state = replace(
        attempted_state,
        status="failed",
        run_attempted=True,
        run_attempted_for_key=plan.run_key,
        last_run_key=plan.run_key,
    )
    failed_plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-27",
        config=config,
        cache_state=failed_state,
    )
    assert failed_plan.is_stale is True
    assert failed_plan.run_attempted is False
    assert failed_plan.should_run is True

    failed_other_key_state = replace(
        failed_state,
        run_attempted_for_key="2026-02-28:other",
        last_run_key=plan.run_key,
        status="failed",
    )
    failed_other_key_plan = cp.build_auto_backtest_plan(
        latest_prices_date="2026-02-27",
        config=config,
        cache_state=failed_other_key_state,
    )
    assert failed_other_key_plan.is_stale is False
    assert failed_other_key_plan.should_run is False


def test_mark_started_and_finished_update_state_transitions():
    initial_state = _fresh_state()

    latest_prices_date = "2026-02-28"
    now_start = dt.datetime(2026, 2, 28, 12, 0, 0, tzinfo=dt.timezone.utc)
    started_state = cp.mark_started(
        initial_state,
        latest_prices_date=latest_prices_date,
        config=cp.DEFAULT_CONFIG,
        now=now_start,
    )

    expected_fingerprint = cp.compute_config_fingerprint(cp.DEFAULT_CONFIG)
    expected_run_key = cp.compute_run_key(latest_prices_date, expected_fingerprint)
    assert started_state.status == "running"
    assert started_state.run_attempted is True
    assert started_state.run_attempted_for_key == expected_run_key
    assert started_state.last_started_at == "2026-02-28T12:00:00Z"
    assert started_state.last_run_key is None

    now_finish = dt.datetime(2026, 2, 28, 12, 1, 0, tzinfo=dt.timezone.utc)
    finished_state = cp.mark_finished(
        started_state,
        latest_prices_date=latest_prices_date,
        now=now_finish,
    )
    assert finished_state.status == "finished"
    assert finished_state.last_run_key == expected_run_key
    assert finished_state.run_attempted is True
    assert finished_state.run_attempted_for_key == expected_run_key
    assert finished_state.last_started_at == "2026-02-28T12:00:00Z"
    assert finished_state.last_finished_at == "2026-02-28T12:01:00Z"

    failed_state = cp.mark_finished(
        started_state,
        latest_prices_date=latest_prices_date,
        status="failed",
        now=now_finish,
    )
    assert failed_state.status == "failed"

    with pytest.raises(ValueError):
        cp.mark_finished(
            started_state,
            latest_prices_date=latest_prices_date,
            status="unknown",
            now=now_finish,
        )


def test_load_cache_rejects_non_bool_run_attempted(tmp_path: Path):
    config = cp.DEFAULT_CONFIG
    payload = {
        "version": cp.CACHE_SCHEMA_VERSION,
        "config": {
            "ma_lookback": config.ma_lookback,
            "stop_lookback": config.stop_lookback,
            "atr_period": config.atr_period,
            "vol_target": config.vol_target,
            "max_positions": config.max_positions,
            "cost_bps": config.cost_bps,
            "min_price": config.min_price,
        },
        "config_fingerprint": cp.compute_config_fingerprint(config),
        "last_run_key": None,
        "run_attempted": "false",
        "run_attempted_for_key": None,
        "status": "idle",
        "last_started_at": None,
        "last_finished_at": None,
    }
    path = tmp_path / "bad_bool.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    result = cp.load_cache(str(path))
    assert result.ok is False
    assert result.reason == "invalid_payload"


def test_persist_cache_atomic_retries_permission_error_and_cleans_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    state = _fresh_state()

    cache_path = tmp_path / "auto_backtest_cache.json"
    replace_calls = {"count": 0}
    real_replace = os.replace

    def _flaky_replace(src: os.PathLike[str] | str, dst: os.PathLike[str] | str):
        replace_calls["count"] += 1
        if replace_calls["count"] == 1:
            raise PermissionError("file locked")
        return real_replace(src, dst)

    monkeypatch.setattr(cp.os, "replace", _flaky_replace)

    cp.persist_cache_atomic(
        str(cache_path),
        state,
        permission_error_retries=3,
        retry_delay_seconds=0.0,
    )

    assert replace_calls["count"] == 2
    assert cache_path.exists()
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    assert payload["status"] == "idle"
    assert payload["config"]["ma_lookback"] == 200
    assert payload["config"]["cost_bps"] == 0.001
    assert list(tmp_path.glob("*.tmp")) == []
