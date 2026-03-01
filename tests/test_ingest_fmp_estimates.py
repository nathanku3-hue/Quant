from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.ingest_fmp_estimates import _build_processed_estimates
from scripts.ingest_fmp_estimates import _derive_period_fields
from scripts.ingest_fmp_estimates import _fetch_fmp_rows_once
from scripts.ingest_fmp_estimates import _merge_existing_processed
from scripts.ingest_fmp_estimates import _normalize_ntm_for_metric
from scripts.ingest_fmp_estimates import RateLimitExhausted
from scripts.ingest_fmp_estimates import _resolve_target_tickers
from scripts.ingest_fmp_estimates import _save_cache_rows
from scripts.ingest_fmp_estimates import _load_cached_rows


def _local_tmp_dir() -> Path:
    root = Path("data/processed/_tmp_pytest")
    path = root / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_normalize_ntm_for_metric_sums_first_four_quarters():
    g = pd.DataFrame(
        {
            "period_type": ["Q", "Q", "Q", "Q", "Q"],
            "period_end": pd.to_datetime(
                ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"],
                utc=True,
            ),
            "estimatedRevenueAvg": [10.0, 11.0, 12.0, 13.0, 14.0],
            "published_at": pd.to_datetime(["2024-12-24"] * 5, utc=True),
        }
    )
    val = _normalize_ntm_for_metric(g, "estimatedRevenueAvg")
    assert np.isclose(val, 46.0, atol=1e-12)


def test_normalize_ntm_for_metric_uses_fy_when_quarters_insufficient():
    g = pd.DataFrame(
        {
            "period_type": ["Q", "FY"],
            "period_end": pd.to_datetime(["2025-03-31", "2025-12-31"], utc=True),
            "estimatedEpsAvg": [1.2, 5.5],
            "published_at": pd.to_datetime(["2024-12-24", "2024-12-24"], utc=True),
        }
    )
    val = _normalize_ntm_for_metric(g, "estimatedEpsAvg")
    assert np.isclose(val, 5.5, atol=1e-12)


def test_normalize_ntm_for_metric_excludes_periods_on_or_before_published_at():
    g = pd.DataFrame(
        {
            "period_type": ["Q", "Q", "Q", "Q", "Q"],
            "period_end": pd.to_datetime(
                ["2024-09-30", "2024-12-20", "2025-03-31", "2025-06-30", "2025-09-30"],
                utc=True,
            ),
            "estimatedRevenueAvg": [50.0, 60.0, 100.0, 110.0, 120.0],
            "published_at": pd.to_datetime(["2024-12-24"] * 5, utc=True),
        }
    )
    val = _normalize_ntm_for_metric(g, "estimatedRevenueAvg")
    # Future quarters only: 2025Q1+Q2+Q3 => scale by 4/3
    assert np.isclose(val, (100.0 + 110.0 + 120.0) * (4.0 / 3.0), atol=1e-12)


def test_build_processed_estimates_enforces_permno_mapping_and_schema():
    raw = pd.DataFrame(
        {
            "ticker": ["MU", "MU", "AMAT", "UNMAPPED"],
            "date": ["2024-12-24", "2024-12-24", "2024-12-24", "2024-12-24"],
            "period": ["Q1 2025", "Q2 2025", "FY 2025", "FY 2025"],
            "estimatedRevenueAvg": [100.0, 110.0, 450.0, 999.0],
            "estimatedEpsAvg": [1.5, 1.7, 6.2, 9.9],
        }
    )
    crosswalk = pd.DataFrame({"ticker_u": ["MU", "AMAT"], "permno": [12345, 23456]})

    out = _build_processed_estimates(raw=raw, crosswalk=crosswalk)

    assert set(out.columns) == {"permno", "ticker", "published_at", "horizon", "metric", "value"}
    assert set(out["ticker"].unique().tolist()) == {"MU", "AMAT"}
    assert out["permno"].isin([12345, 23456]).all()
    assert out["horizon"].eq("NTM").all()
    assert set(out["metric"].unique().tolist()) == {"estimatedRevenueAvg", "estimatedEpsAvg"}


def test_resolve_target_tickers_union_and_cap():
    tmp = _local_tmp_dir()
    tf = tmp / "tickers.txt"
    tf.write_text("AMAT\nLRCX\nMU\n", encoding="utf-8")
    try:
        out = _resolve_target_tickers("MU,KLAC", tf, max_tickers=3)
        assert out == ["MU", "KLAC", "AMAT"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cache_roundtrip_for_single_ticker():
    tmp = _local_tmp_dir()
    cache_file = tmp / "MU.json"
    rows = [{"date": "2024-12-24", "estimatedRevenueAvg": 10.0, "estimatedEpsAvg": 1.2}]
    try:
        _save_cache_rows(cache_file, rows)
        loaded = _load_cached_rows(cache_file, "MU")
        assert len(loaded) == 1
        assert loaded[0]["ticker"] == "MU"
        assert float(loaded[0]["estimatedRevenueAvg"]) == 10.0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cache_roundtrip_redacts_api_key_from_api_url():
    tmp = _local_tmp_dir()
    cache_file = tmp / "NVDA.json"
    rows = [
        {
            "date": "2024-12-24",
            "estimatedRevenueAvg": 10.0,
            "estimatedEpsAvg": 1.2,
            "api_url": "https://financialmodelingprep.com/stable/analyst-estimates?symbol=NVDA&period=annual&apikey=SECRET123",
        }
    ]
    try:
        _save_cache_rows(cache_file, rows)
        raw_text = cache_file.read_text(encoding="utf-8")
        assert "SECRET123" not in raw_text
        assert "apikey=" not in raw_text
        loaded = _load_cached_rows(cache_file, "NVDA")
        assert len(loaded) == 1
        assert "apikey=" not in str(loaded[0].get("api_url", ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_cache_roundtrip_redacts_api_key_from_alternate_url_fields():
    tmp = _local_tmp_dir()
    cache_file = tmp / "ALT.json"
    rows = [
        {
            "date": "2024-12-24",
            "estimatedRevenueAvg": 9.0,
            "estimatedEpsAvg": 1.0,
            "url": "https://financialmodelingprep.com/stable/analyst-estimates?symbol=MU&apikey=SECRET456",
            "request_url": "https://financialmodelingprep.com/stable/analyst-estimates?symbol=MU&period=annual&apikey=SECRET456",
        }
    ]
    try:
        _save_cache_rows(cache_file, rows)
        raw_text = cache_file.read_text(encoding="utf-8")
        assert "SECRET456" not in raw_text
        assert "apikey=" not in raw_text
        loaded = _load_cached_rows(cache_file, "MU")
        assert len(loaded) == 1
        assert "apikey=" not in str(loaded[0].get("url", ""))
        assert "apikey=" not in str(loaded[0].get("request_url", ""))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_derive_period_fields_prefers_fetch_time_over_estimate_horizon_date():
    raw = pd.DataFrame(
        {
            "ticker": ["NVDA"],
            "date": ["2030-01-26"],
            "fetched_at_utc": ["2026-02-22T03:42:11.830883+00:00"],
            "estimatedRevenueAvg": [100.0],
            "estimatedEpsAvg": [1.0],
        }
    )
    out = _derive_period_fields(raw)
    assert len(out) == 1
    published_at = pd.to_datetime(out.loc[0, "published_at"], utc=True)
    assert str(published_at.date()) == "2026-02-22"


def test_fetch_fmp_rows_once_raises_on_string_error_payload(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"\"daily request limit reached\""

    monkeypatch.setattr("scripts.ingest_fmp_estimates.urlopen", lambda *_args, **_kwargs: _Resp())
    with pytest.raises(RateLimitExhausted):
        _fetch_fmp_rows_once("NVDA", "demo", 5.0)


def test_fetch_fmp_rows_once_raises_value_error_on_dict_non_rate_limit_payload(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"message":"upstream request failed"}'

    monkeypatch.setattr("scripts.ingest_fmp_estimates.urlopen", lambda *_args, **_kwargs: _Resp())
    with pytest.raises(ValueError, match="upstream request failed"):
        _fetch_fmp_rows_once("NVDA", "demo", 5.0)


def test_fetch_fmp_rows_once_raises_value_error_on_unexpected_scalar_payload(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"123"

    monkeypatch.setattr("scripts.ingest_fmp_estimates.urlopen", lambda *_args, **_kwargs: _Resp())
    with pytest.raises(ValueError, match="Unexpected payload type from FMP API: int"):
        _fetch_fmp_rows_once("NVDA", "demo", 5.0)


def test_fetch_fmp_rows_once_raises_on_invalid_json_payload(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b"not valid json"

    monkeypatch.setattr("scripts.ingest_fmp_estimates.urlopen", lambda *_args, **_kwargs: _Resp())
    with pytest.raises(json.JSONDecodeError):
        _fetch_fmp_rows_once("NVDA", "demo", 5.0)


def test_merge_existing_processed_dedup_prefers_new():
    tmp = _local_tmp_dir()
    existing_path = tmp / "estimates.parquet"
    old = pd.DataFrame(
        {
            "permno": [10001],
            "ticker": ["MU"],
            "published_at": pd.to_datetime(["2024-12-24T00:00:00Z"], utc=True),
            "horizon": ["NTM"],
            "metric": ["estimatedRevenueAvg"],
            "value": [100.0],
        }
    )
    try:
        old.to_parquet(existing_path, index=False)
        new = pd.DataFrame(
            {
                "permno": [10001],
                "ticker": ["MU"],
                "published_at": pd.to_datetime(["2024-12-24T00:00:00Z"], utc=True),
                "horizon": ["NTM"],
                "metric": ["estimatedRevenueAvg"],
                "value": [110.0],
            }
        )
        merged = _merge_existing_processed(new, existing_path)
        assert len(merged) == 1
        assert float(merged.iloc[0]["value"]) == 110.0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
