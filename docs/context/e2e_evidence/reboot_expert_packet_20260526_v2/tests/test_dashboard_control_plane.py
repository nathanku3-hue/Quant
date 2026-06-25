from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from core import dashboard_control_plane as cp


def test_load_watchlist_missing_file_returns_default(tmp_path: Path):
    watchlist_file = tmp_path / "missing_watchlist.json"
    data = cp.load_watchlist(str(watchlist_file))
    assert data["defaults"] == ["AAPL", "MSFT", "SPY"]
    assert data["user_added"] == []


def test_load_watchlist_invalid_json_returns_default(tmp_path: Path):
    watchlist_file = tmp_path / "watchlist.json"
    watchlist_file.write_text("{not valid json", encoding="utf-8")

    data = cp.load_watchlist(str(watchlist_file))
    assert data["defaults"] == ["AAPL", "MSFT", "SPY"]
    assert data["user_added"] == []


def test_save_user_selections_persists_non_default_user_set(tmp_path: Path):
    watchlist_file = tmp_path / "watchlist.json"
    cp.save_user_selections(
        ["AAPL", "MSFT", "NVDA", "TSLA", "TSLA"],
        str(watchlist_file),
    )

    data = cp.load_watchlist(str(watchlist_file))
    assert set(data["defaults"]) == {"AAPL", "MSFT", "SPY"}
    assert data["user_added"] == ["NVDA", "TSLA"]

    tickers = cp.get_watchlist_tickers(str(watchlist_file))
    assert tickers == ["AAPL", "MSFT", "NVDA", "SPY", "TSLA"]


def test_save_user_selections_atomic_replace_and_parent_creation(tmp_path: Path, monkeypatch):
    watchlist_file = tmp_path / "nested" / "watchlists" / "watchlist.json"
    replace_calls: list[tuple[Path, Path]] = []
    real_replace = cp.os.replace

    def _tracking_replace(src: str, dst: str) -> None:
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(cp.os, "replace", _tracking_replace)

    cp.save_user_selections(
        ["AAPL", "MSFT", "NVDA"],
        str(watchlist_file),
    )

    assert watchlist_file.exists()
    assert len(replace_calls) == 1
    tmp_src, target_dst = replace_calls[0]
    assert target_dst == watchlist_file
    assert tmp_src != watchlist_file
    assert tmp_src.parent == watchlist_file.parent

    data = cp.load_watchlist(str(watchlist_file))
    assert data["user_added"] == ["NVDA"]


def test_is_data_stale_handles_weekday_and_monday_cutoff():
    monday = dt.date(2026, 2, 23)  # Monday
    friday = pd.Timestamp("2026-02-20")
    thursday = pd.Timestamp("2026-02-19")

    assert cp.is_data_stale(friday, today=monday) is False
    assert cp.is_data_stale(thursday, today=monday) is True


def test_plan_auto_update_resets_attempt_on_new_db_date_and_requests_stale_update():
    plan = cp.plan_auto_update(
        last_db_date=pd.Timestamp("2026-02-20"),
        update_attempted=True,
        update_attempted_for_date="2026-02-19",
        today=dt.date(2026, 2, 24),  # Tuesday, cutoff Monday (2026-02-23)
    )
    assert plan.update_attempted_for_date == "2026-02-20"
    assert plan.update_attempted is False
    assert plan.is_stale is True
    assert plan.should_attempt_update is True
    assert plan.show_already_attempted_caption is False
    assert plan.status == cp.PLAN_STATUS_READY
    assert plan.is_invalid_state is False
    assert plan.reason == "stale_threshold_exceeded:update_required"


def test_plan_auto_update_shows_caption_when_stale_and_already_attempted():
    plan = cp.plan_auto_update(
        last_db_date=pd.Timestamp("2026-02-20"),
        update_attempted=True,
        update_attempted_for_date="2026-02-20",
        today=dt.date(2026, 2, 24),
    )
    assert plan.update_attempted is True
    assert plan.is_stale is True
    assert plan.should_attempt_update is False
    assert plan.show_already_attempted_caption is True
    assert plan.status == cp.PLAN_STATUS_READY
    assert plan.is_invalid_state is False
    assert plan.reason == "stale_threshold_exceeded:already_attempted"


def test_derive_hf_proxy_data_health_all_healthy():
    health = cp.derive_hf_proxy_data_health(
        {
            "cloud_growth_yoy": {"val": 0.30, "span": "YoY"},
            "energy_price_trend": {"val": 0.01, "span": "Trend"},
        }
    )

    assert health["status"] == cp.DATA_HEALTH_HEALTHY
    assert health["degraded_count"] == 0
    assert health["total_signals"] == 2
    assert health["degraded_ratio"] == 0.0
    assert all(x["status"] == cp.DATA_HEALTH_HEALTHY for x in health["signals"])


def test_derive_hf_proxy_data_health_any_degraded_forces_degraded_status():
    health = cp.derive_hf_proxy_data_health(
        {
            "cloud_growth_yoy": {"val": 0.30, "span": "YoY"},
            "dram_spot_trend": {"val": None, "span": "Trend"},
            "energy_price_trend": {"val": float("nan"), "span": "Trend"},
        }
    )

    assert health["status"] == cp.DATA_HEALTH_DEGRADED
    assert health["degraded_count"] == 2
    assert health["total_signals"] == 3
    assert health["degraded_ratio"] == pytest.approx(2 / 3)
    by_signal = {x["signal"]: x for x in health["signals"]}
    assert by_signal["dram_spot_trend"]["reason"] == "missing value"
    assert by_signal["energy_price_trend"]["reason"] == "non-finite value"


def test_derive_hf_proxy_data_health_empty_proxy_payload_is_degraded():
    health = cp.derive_hf_proxy_data_health({})
    assert health["status"] == cp.DATA_HEALTH_DEGRADED
    assert health["degraded_count"] == 1
    assert health["total_signals"] == 1
    assert health["degraded_ratio"] == 1.0
    assert health["signals"][0]["signal"] == "__payload__"
    assert health["signals"][0]["reason"] == "no signals"


def test_ensure_payload_data_health_derives_for_legacy_cache_payload():
    payload = {
        "timestamp": "2026-03-01T12:00:00",
        "proxy": {
            "cloud_growth_yoy": {"val": 0.25, "span": "YoY"},
            "energy_price_trend": {"val": 0.0, "span": "Trend"},
        },
        "data": [],
    }

    health = cp.ensure_payload_data_health(payload)
    assert health["status"] == cp.DATA_HEALTH_HEALTHY
    assert payload["data_health"] == health


def test_coerce_proxy_numeric_returns_default_for_invalid_values():
    assert cp.coerce_proxy_numeric("0.25") == pytest.approx(0.25)
    assert cp.coerce_proxy_numeric(None) == 0.0
    assert cp.coerce_proxy_numeric("bad", default=0.5) == pytest.approx(0.5)
    assert cp.coerce_proxy_numeric(float("nan"), default=0.2) == pytest.approx(0.2)


def test_plan_auto_update_null_last_db_date_returns_invalid_state():
    plan = cp.plan_auto_update(
        last_db_date=None,
        update_attempted=True,
        update_attempted_for_date="2026-02-20",
        today=dt.date(2026, 2, 24),
    )
    assert plan.status == cp.PLAN_STATUS_INVALID_STATE
    assert plan.is_invalid_state is True
    assert plan.reason == "invalid_last_db_date:null"
    assert plan.should_attempt_update is False
    assert plan.show_already_attempted_caption is False
    assert plan.update_attempted is False
    assert plan.update_attempted_for_date == cp.INVALID_STATE_DATE_KEY


def test_plan_auto_update_nat_last_db_date_returns_invalid_state():
    plan = cp.plan_auto_update(
        last_db_date=pd.NaT,
        update_attempted=True,
        update_attempted_for_date="2026-02-20",
        today=dt.date(2026, 2, 24),
    )
    assert plan.status == cp.PLAN_STATUS_INVALID_STATE
    assert plan.is_invalid_state is True
    assert plan.reason == "invalid_last_db_date:null_like"
    assert plan.should_attempt_update is False
    assert plan.show_already_attempted_caption is False
    assert plan.update_attempted is False
    assert plan.update_attempted_for_date == cp.INVALID_STATE_DATE_KEY


def test_plan_auto_update_invalid_date_format_returns_invalid_state():
    plan = cp.plan_auto_update(
        last_db_date="2026/02/24",
        update_attempted=False,
        update_attempted_for_date=None,
        today=dt.date(2026, 2, 24),
    )
    assert plan.status == cp.PLAN_STATUS_INVALID_STATE
    assert plan.is_invalid_state is True
    assert plan.reason == "invalid_last_db_date:invalid_format"
    assert plan.should_attempt_update is False
    assert plan.update_attempted_for_date == cp.INVALID_STATE_DATE_KEY


def test_plan_auto_update_future_last_db_date_returns_invalid_state():
    plan = cp.plan_auto_update(
        last_db_date=pd.Timestamp("2026-02-25"),
        update_attempted=False,
        update_attempted_for_date=None,
        today=dt.date(2026, 2, 24),
    )
    assert plan.status == cp.PLAN_STATUS_INVALID_STATE
    assert plan.is_invalid_state is True
    assert plan.reason == "invalid_last_db_date:future_date"
    assert plan.should_attempt_update is False
    assert plan.update_attempted_for_date == cp.INVALID_STATE_DATE_KEY


def test_plan_auto_update_uses_deterministic_tn_threshold_reason():
    plan = cp.plan_auto_update(
        last_db_date=pd.Timestamp("2026-02-19"),
        update_attempted=False,
        update_attempted_for_date=None,
        today=dt.date(2026, 2, 23),  # Monday -> T-3 cutoff on previous Friday.
    )
    assert plan.status == cp.PLAN_STATUS_READY
    assert plan.is_invalid_state is False
    assert plan.stale_threshold_label == "T-3"
    assert plan.stale_cutoff_date == "2026-02-20"
    assert plan.reason == "stale_threshold_exceeded:update_required"
    assert "T-3 cutoff 2026-02-20" in plan.message
