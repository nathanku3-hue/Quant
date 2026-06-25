from __future__ import annotations

import pandas as pd
import pytest

from data import fundamentals
from data import fundamentals_panel


def _restatement_fixture() -> pd.DataFrame:
    base_metrics = {
        "operating_margin_q": 0.10,
        "operating_margin_delta_q": 0.01,
        "gross_margin_q": 0.40,
        "gm_accel_q": 0.00,
        "capex_sales_q": 0.08,
        "delta_capex_sales": 0.00,
        "book_to_bill_proxy_q": 1.05,
        "dso_q": 32.0,
        "delta_dso_q": -1.0,
        "revenue_inventory_q": 3.0,
        "delta_revenue_inventory": 0.05,
        "sales_growth_q": 0.04,
        "sales_accel_q": 0.01,
        "op_margin_accel_q": 0.005,
        "bloat_q": -0.02,
        "net_investment_q": 0.03,
        "cogs_q": 60.0,
        "receivables_q": 35.0,
        "deferred_revenue_q": 12.0,
        "delta_deferred_revenue_q": 1.0,
        "asset_growth_yoy": 0.07,
        "roe_q": 0.12,
        "eps_ttm": 4.0,
        "eps_growth_yoy": 0.10,
        "ev_ebitda": 11.0,
        "leverage_ratio": 1.2,
        "rd_intensity": 0.09,
        "oancf_ttm": 10.0,
        "ebitda_ttm": 12.0,
    }
    return pd.DataFrame(
        [
            {
                "permno": 10001,
                "ticker": "CSCO",
                # Q1 original.
                "fiscal_period_end": "2021-03-31",
                "release_date": "2021-05-10",
                "filing_date": "2021-05-10",
                "published_at": "2021-05-10T08:00:00",
                "roic": 0.22,
                "revenue_growth_yoy": 0.15,
                "eps_q": 1.0,
                "ingested_at": "2021-05-10T12:00:00",
                **base_metrics,
            },
            {
                # Same quarter, Q3 restatement published with timestamp precision.
                "permno": 10001,
                "ticker": "CSCO",
                "fiscal_period_end": "2021-03-31",
                "release_date": "2021-05-10",
                "filing_date": "2021-08-20",
                "published_at": "2021-08-20T09:30:00",
                "roic": 0.21,
                "revenue_growth_yoy": 0.10,
                "eps_q": 0.8,
                "ingested_at": "2021-08-20T12:00:00",
                **base_metrics,
            },
            {
                # Synthetic anomaly to prove valid-time guard:
                # published_at is earlier than release_date, so it must be hidden until release_date.
                "permno": 10002,
                "ticker": "FUTR",
                "fiscal_period_end": "2021-06-30",
                "release_date": "2021-08-21",
                "filing_date": "2021-08-20",
                "published_at": "2021-08-20T09:00:00",
                "roic": 0.18,
                "revenue_growth_yoy": 0.08,
                "eps_q": 2.0,
                "ingested_at": "2021-08-20T12:00:00",
                **base_metrics,
            },
        ]
    )


def test_bitemporal_snapshot_hides_future_restatement_until_exact_timestamp(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    snapshot_path = tmp_path / "fundamentals_snapshot.parquet"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_SNAPSHOT_PATH", str(snapshot_path))

    asof_before = fundamentals.load_fundamentals_snapshot(as_of_date="2021-08-20T09:29:59")
    asof_exact = fundamentals.load_fundamentals_snapshot(as_of_date="2021-08-20T09:30:00")
    asof_after = fundamentals.load_fundamentals_snapshot(as_of_date="2021-08-20T09:30:01")

    assert int(asof_before.index[0]) == 10001
    assert float(asof_before.loc[10001, "eps_q"]) == 1.0
    assert float(asof_exact.loc[10001, "eps_q"]) == pytest.approx(0.8, rel=1e-6)
    assert float(asof_after.loc[10001, "eps_q"]) == pytest.approx(0.8, rel=1e-6)


def test_quarterly_loader_enforces_release_date_valid_time_guard(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(fundamentals_path))

    asof_midday = fundamentals.load_quarterly_fundamentals(as_of_date="2021-08-20T12:00:00")
    assert 10001 in set(asof_midday["permno"].astype(int).tolist())
    # release_date=2021-08-21 is still in the future at 2021-08-20T12:00:00
    assert 10002 not in set(asof_midday["permno"].astype(int).tolist())


def test_snapshot_binding_token_validation_fail_closed(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    snapshot_path = tmp_path / "fundamentals_snapshot.parquet"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_SNAPSHOT_PATH", str(snapshot_path))

    simulation_ts = "2021-08-20T09:30:00"
    secret = "unit-test-secret"
    good_token = fundamentals.create_simulation_ts_binding_token(simulation_ts=simulation_ts, secret=secret)
    bad_token = fundamentals.create_simulation_ts_binding_token(simulation_ts="2021-08-20T09:29:59", secret=secret)

    snap = fundamentals.load_fundamentals_snapshot(
        as_of_date=simulation_ts,
        simulation_ts_binding_token=good_token,
        simulation_ts_binding_secret=secret,
    )
    assert float(snap.loc[10001, "eps_q"]) == pytest.approx(0.8, rel=1e-6)

    with pytest.raises(ValueError, match="binding token mismatch"):
        fundamentals.load_fundamentals_snapshot(
            as_of_date=simulation_ts,
            simulation_ts_binding_token=bad_token,
            simulation_ts_binding_secret=secret,
        )


def test_snapshot_binding_strict_mode_requires_token(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    snapshot_path = tmp_path / "fundamentals_snapshot.parquet"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_SNAPSHOT_PATH", str(snapshot_path))
    monkeypatch.setenv(fundamentals.SIMULATION_TS_BINDING_STRICT_ENV, "1")

    with pytest.raises(ValueError, match="binding token is required"):
        fundamentals.load_fundamentals_snapshot(as_of_date="2021-08-20T09:30:00")


def test_build_fundamentals_daily_fallback_honors_release_date_valid_time(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)
    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(fundamentals_path))

    def _force_panel_failure(**_kwargs):
        raise RuntimeError("forced panel failure")

    monkeypatch.setattr(
        fundamentals.fundamentals_panel_data,
        "load_daily_fundamentals_panel",
        _force_panel_failure,
    )

    idx = pd.date_range("2021-08-19", "2021-08-24", freq="B")
    payload = fundamentals.build_fundamentals_daily(
        prices_index=idx,
        permnos=[10002],
    )

    roic = payload["roic"]
    quality = payload["quality_pass"]
    assert pd.isna(roic.loc[pd.Timestamp("2021-08-20"), 10002])
    assert bool(quality.loc[pd.Timestamp("2021-08-20"), 10002]) is False
    assert float(roic.loc[pd.Timestamp("2021-08-23"), 10002]) == pytest.approx(0.18, rel=1e-6)


def test_quarterly_dedupe_is_deterministic_when_ingested_ties(tmp_path, monkeypatch):
    row_a = {
        "permno": 42424,
        "ticker": "TIE1",
        "fiscal_period_end": "2021-03-31",
        "release_date": "2021-05-10",
        "filing_date": "2021-05-10",
        "published_at": "2021-05-10T09:00:00",
        "roic": 0.11,
        "revenue_growth_yoy": 0.05,
        "eps_q": 1.0,
        "ingested_at": "2021-05-11T12:00:00",
    }
    row_b = dict(row_a)
    row_b["roic"] = 0.99

    path_a = tmp_path / "fundamentals_a.parquet"
    path_b = tmp_path / "fundamentals_b.parquet"
    pd.DataFrame([row_a, row_b]).to_parquet(path_a, index=False)
    pd.DataFrame([row_b, row_a]).to_parquet(path_b, index=False)

    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(path_a))
    out_a = fundamentals.load_quarterly_fundamentals(as_of_date="2021-05-20")
    monkeypatch.setattr(fundamentals, "FUNDAMENTALS_PATH", str(path_b))
    out_b = fundamentals.load_quarterly_fundamentals(as_of_date="2021-05-20")

    roic_a = float(out_a.loc[out_a["permno"] == 42424, "roic"].iloc[0])
    roic_b = float(out_b.loc[out_b["permno"] == 42424, "roic"].iloc[0])
    assert roic_a == pytest.approx(roic_b, rel=0.0, abs=0.0)


def test_daily_panel_respects_restatement_publish_time(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    prices_path = tmp_path / "prices.parquet"
    panel_path = tmp_path / "daily_fundamentals_panel.parquet"
    manifest_path = tmp_path / "daily_fundamentals_panel.manifest.json"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    dates = pd.date_range("2021-05-03", "2021-09-30", freq="B")
    prices = pd.DataFrame(
        {
            "date": dates,
            "permno": [10001] * len(dates),
            "adj_close": 100.0,
            "total_ret": 0.0,
            "volume": 1_000_000.0,
        }
    )
    prices.to_parquet(prices_path, index=False)

    monkeypatch.setattr(fundamentals_panel, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals_panel, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(fundamentals_panel, "PATCH_PATH", str(tmp_path / "missing_patch.parquet"))
    monkeypatch.setattr(fundamentals_panel, "PANEL_PATH", str(panel_path))
    monkeypatch.setattr(fundamentals_panel, "MANIFEST_PATH", str(manifest_path))

    build_status = fundamentals_panel.build_daily_fundamentals_panel(
        output_path=str(panel_path),
        manifest_path=str(manifest_path),
        force_rebuild=True,
    )
    assert build_status["success"] is True
    assert build_status["row_count"] > 0

    panel = pd.read_parquet(panel_path)
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")

    eps_pre = panel.loc[
        (panel["permno"] == 10001) & (panel["date"] == pd.Timestamp("2021-08-19")),
        "eps_q",
    ]
    eps_post = panel.loc[
        (panel["permno"] == 10001) & (panel["date"] == pd.Timestamp("2021-08-23")),
        "eps_q",
    ]

    assert len(eps_pre) == 1
    assert len(eps_post) == 1
    # Pre-restatement query must not see the future value.
    assert float(eps_pre.iloc[0]) == 1.0
    assert float(eps_post.iloc[0]) == pytest.approx(0.8, rel=1e-6)

    probe_prices = pd.DataFrame(
        {
            "date": [pd.Timestamp("2021-08-19"), pd.Timestamp("2021-08-23")],
            "permno": [10001, 10001],
            "adj_close": [100.0, 100.0],
        }
    )
    joined = fundamentals_panel.join_prices_with_daily_fundamentals(
        prices=probe_prices,
        panel_path=str(panel_path),
        panel_columns=["eps_q", "quality_pass"],
    )
    assert float(joined.loc[joined["date"] == pd.Timestamp("2021-08-19"), "eps_q"].iloc[0]) == 1.0
    assert float(joined.loc[joined["date"] == pd.Timestamp("2021-08-23"), "eps_q"].iloc[0]) == pytest.approx(0.8, rel=1e-6)

    cache_status = fundamentals_panel.build_daily_fundamentals_panel(
        output_path=str(panel_path),
        manifest_path=str(manifest_path),
        force_rebuild=False,
    )
    assert cache_status["success"] is True
    assert cache_status["cache_hit"] is True


def test_daily_panel_failure_returns_status_and_cleans_tmp(tmp_path, monkeypatch):
    fundamentals_path = tmp_path / "fundamentals.parquet"
    prices_path = tmp_path / "prices.parquet"
    panel_path = tmp_path / "daily_fundamentals_panel.parquet"
    manifest_path = tmp_path / "daily_fundamentals_panel.manifest.json"
    _restatement_fixture().to_parquet(fundamentals_path, index=False)

    prices = pd.DataFrame(
        {
            "date": pd.date_range("2022-01-03", periods=5, freq="B"),
            "permno": [10001] * 5,
            "adj_close": 100.0,
            "total_ret": 0.0,
            "volume": 1_000_000.0,
        }
    )
    prices.to_parquet(prices_path, index=False)

    monkeypatch.setattr(fundamentals_panel, "FUNDAMENTALS_PATH", str(fundamentals_path))
    monkeypatch.setattr(fundamentals_panel, "PRICES_PATH", str(prices_path))
    monkeypatch.setattr(fundamentals_panel, "PATCH_PATH", str(tmp_path / "missing_patch.parquet"))
    monkeypatch.setattr(fundamentals_panel, "PANEL_PATH", str(panel_path))
    monkeypatch.setattr(fundamentals_panel, "MANIFEST_PATH", str(manifest_path))
    monkeypatch.setattr(
        fundamentals_panel,
        "_build_panel_sql",
        lambda stage_path, min_date, max_date: "SELECT * FROM missing_relation_forced_failure",
    )

    status = fundamentals_panel.build_daily_fundamentals_panel(
        output_path=str(panel_path),
        manifest_path=str(manifest_path),
        force_rebuild=True,
    )
    assert status["success"] is False
    assert "error" in status and status["error"]
    assert panel_path.exists() is False
    assert manifest_path.exists() is False
    assert list(tmp_path.glob("daily_fundamentals_panel.parquet.*.tmp")) == []
