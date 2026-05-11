from __future__ import annotations

import pandas as pd
from streamlit.testing.v1 import AppTest

from core import data_orchestrator
from strategies.optimizer import OptimizationMethod


OPTIMIZER_VIEW_APP = r"""
import pandas as pd

from views.optimizer_view import render_optimizer_view

prices = pd.DataFrame(
    {
        1: [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
        2: [20.0, 22.0, 21.0, 23.0, 24.0, 25.0],
        3: [30.0, 29.0, 32.0, 31.0, 34.0, 33.0],
    },
    index=pd.date_range("2026-01-01", periods=6),
)
render_optimizer_view(
    prices_wide=prices,
    ticker_map={},
    sector_map={1: "Tech", 2: "Tech", 3: "Health"},
    selected_permnos=[1, 2, 3],
)
"""


def test_optimizer_view_renders_with_streamlit_testing() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)

    assert not app.exception
    assert any("Portfolio Optimizer" in header.value for header in app.header)
    assert app.multiselect[0].label == "Select assets"
    assert app.selectbox[0].label == "Method"
    assert any(subheader.value == "Optimizer Diagnostics" for subheader in app.subheader)
    assert any(subheader.value == "Allocation Table" for subheader in app.subheader)


def test_optimizer_view_exercises_mean_variance_and_sector_cap_controls() -> None:
    app = AppTest.from_string(OPTIMIZER_VIEW_APP).run(timeout=15)
    app.selectbox[0].select(OptimizationMethod.MEAN_VARIANCE_MAX_RETURN)
    app.checkbox[0].check()
    app.slider[1].set_value(0.50)
    app.run(timeout=15)

    assert not app.exception
    assert any(
        caption.value == "Optimization Method: Mean-Variance (SLSQP)"
        for caption in app.caption
    )
    assert any("Sector cap applied: max 50%" in caption.value for caption in app.caption)
    assert any(subheader.value == "Sector Exposure" for subheader in app.subheader)


def test_recent_close_prices_use_display_only_parquet_cache(
    tmp_path,
    monkeypatch,
) -> None:
    calls: list[tuple[tuple[str, ...], str]] = []

    class FakeProvider:
        def download_daily_bars(self, tickers, start, threads=True):
            calls.append((tuple(tickers), start))
            index = pd.date_range("2026-01-01", periods=3)
            columns = pd.MultiIndex.from_product([["Adj Close"], tickers])
            return pd.DataFrame(
                [[10.0, 20.0], [11.0, 21.0], [12.0, 22.0]],
                index=index,
                columns=columns,
            )

    monkeypatch.setattr(
        data_orchestrator,
        "build_market_data_provider",
        lambda name: FakeProvider(),
    )

    first = data_orchestrator.download_recent_close_prices(
        ("bbb", "AAA"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=False,
    )

    assert calls == [(("AAA", "BBB"), "2026-01-01")]
    assert list(first.columns) == ["AAA", "BBB"]
    assert len(list(tmp_path.glob("*.parquet"))) == 1

    def _fail_provider(name):
        raise AssertionError("provider should not be called for fresh cache")

    monkeypatch.setattr(data_orchestrator, "build_market_data_provider", _fail_provider)
    cached = data_orchestrator.download_recent_close_prices(
        ("AAA", "BBB"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=False,
    )

    pd.testing.assert_frame_equal(cached, first, check_freq=False)


def test_cold_recent_close_cache_schedules_background_refresh(
    tmp_path,
    monkeypatch,
) -> None:
    scheduled: list[tuple[tuple[str, ...], str]] = []

    def _record_schedule(tickers, start_iso, cache_path, cache_key):
        scheduled.append((tuple(tickers), start_iso))

    monkeypatch.setattr(data_orchestrator, "_schedule_overlay_refresh", _record_schedule)
    result = data_orchestrator.download_recent_close_prices(
        ("BBB", "aaa"),
        "2026-01-01",
        cache_dir=tmp_path,
        schedule_background=True,
    )

    assert result.empty
    assert scheduled == [(("AAA", "BBB"), "2026-01-01")]


def test_scaled_live_overlay_cache_returns_copy_safe_results() -> None:
    data_orchestrator._scaled_overlay_cache.clear()
    local = pd.DataFrame(
        {"AAA": [100.0, 110.0]},
        index=pd.to_datetime(["2026-01-02", "2026-01-03"]),
    )
    live = pd.DataFrame(
        {"AAA": [50.0, 55.0]},
        index=pd.to_datetime(["2026-01-03", "2026-01-04"]),
    )

    scaled = data_orchestrator.scale_live_overlay_to_local(local, live)
    assert len(data_orchestrator._scaled_overlay_cache) == 1
    assert abs(float(scaled.loc[pd.Timestamp("2026-01-04"), "AAA"]) - 121.0) <= 1e-9

    scaled.iloc[0, 0] = -999.0
    cached = data_orchestrator.scale_live_overlay_to_local(local, live)

    assert len(data_orchestrator._scaled_overlay_cache) == 1
    assert abs(float(cached.loc[pd.Timestamp("2026-01-03"), "AAA"]) - 110.0) <= 1e-9
