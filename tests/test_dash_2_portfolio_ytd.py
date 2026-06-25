"""
DASH-2 Portfolio YTD Slice: Focused Tests

Validates the approved narrow DASH slice:
- PB1-PB3 and PB5 marketing copy removed from dashboard.py
- Portfolio YTD chart function exists and is wired
- Optimizer renders top-level above the YTD comparison
- Portfolio YTD return uses current optimizer weights when available
- Hedge Harvester removed from Research Lab primary flow
- No forbidden runtime scope introduced
"""

from __future__ import annotations
from pathlib import Path

import pandas as pd
import pytest

from core.data_orchestrator import build_benchmark_equity_from_prices
from core.data_orchestrator import BatchedPITReplayData
from strategies.strategy_replay import StrategyReplayBundle
from strategies.strategy_replay import StrategyReplayContext
from strategies.strategy_replay import StrategyReplayRunMetadata

DASHBOARD = Path("dashboard.py")


def _store_dashboard_replay_selection(
    dashboard,
    assets: tuple[object, ...],
    *,
    method: str = "Inverse Volatility",
    max_weight: float = 0.35,
    risk_free_rate: float = 0.0,
) -> None:
    dashboard.st.session_state["optimizer_method"] = method
    dashboard.st.session_state["optimizer_max_weight"] = max_weight
    dashboard.st.session_state["optimizer_risk_free_rate"] = risk_free_rate
    dashboard.st.session_state[dashboard.PORTFOLIO_REPLAY_SELECTION_KEY] = dashboard.PortfolioReplaySelection(
        method=method,
        max_weight=max_weight,
        risk_free_rate=risk_free_rate,
        replay_assets=assets,
        latest_price_date=pd.Timestamp(dashboard.prices_wide.index[-1]).date().isoformat(),
        source="optimizer_controls",
        signature=dashboard.build_portfolio_replay_selection_signature(
            prices_wide=dashboard.prices_wide,
            replay_assets=assets,
            method=method,
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        ),
    )


# ── PB Copy Removal Checks ────────────────────────────────────────────────


def test_dash_2_portfolio_builder_marketing_copy_removed() -> None:
    """PB1-PB3: No marketing subheader/status copy in portfolio section."""
    source = DASHBOARD.read_text(encoding="utf-8")

    # PB1: removed subheader
    assert "Portfolio Builder: Mean-Variance Optimization" not in source

    # PB2: removed description
    assert "Construct optimal portfolios with sector constraints" not in source

    # PB3: removed status badge
    assert "Fundamentals Data Active" not in source


def test_dash_2_portfolio_builder_placeholder_preview_removed() -> None:
    """PB5: 3-column feature preview placeholder removed."""
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "Preview: Portfolio Builder Features" not in source
    assert "Efficient frontier calculation" not in source
    assert "Constraint Management" not in source
    assert "Regime Integration" not in source
    assert "Defensive tilt in RED regime" not in source


# ── YTD Chart Checks ──────────────────────────────────────────────────────


def test_dash_2_ytd_chart_function_exists() -> None:
    """New _render_portfolio_ytd_chart function is defined."""
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "def _render_portfolio_ytd_chart(" in source


def test_dash_2_ytd_chart_wired_into_portfolio_page() -> None:
    """Performance renders from page-level replay orchestration."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    # Find the next function definition after this one
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "_ensure_daily_portfolio_replay_context(" in section_source
    assert "_render_portfolio_ytd_chart(daily_replay_context" in section_source


def test_dash_2_ytd_chart_renders_spy_and_qqq_benchmarks() -> None:
    """YTD chart includes SPY and QQQ benchmark traces."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_ytd_chart(")
    next_def = source.index("\ndef ", start + 1)
    chart_source = source[start:next_def]

    assert '"SPY"' in chart_source
    assert '"QQQ"' in chart_source
    assert "_build_benchmark_equity" in chart_source
    assert "plotly_dark" in chart_source


def test_dash_2_ytd_chart_handles_empty_data_gracefully() -> None:
    """YTD chart has fallback when no data available."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_ytd_chart(")
    next_def = source.index("\ndef ", start + 1)
    chart_source = source[start:next_def]

    # Must have a guard for empty data
    assert "portfolio_equity is None" in chart_source
    assert "benchmark_equity" in chart_source


def test_dash_2_benchmarks_have_local_tri_fallback() -> None:
    """SPY/QQQ benchmarks do not disappear when live yfinance is unavailable."""
    source = DASHBOARD.read_text(encoding="utf-8")
    orchestrator_source = Path("core/data_orchestrator.py").read_text(encoding="utf-8")
    assert "def _local_benchmark_close_prices(" in source
    assert "def _build_benchmark_equity(" in source
    assert "_local_benchmark_close_prices(tickers, ytd_start)" in source
    assert "live_loader=_download_ytd_close_prices" in source
    assert "def build_benchmark_equity_from_prices(" in orchestrator_source
    assert "benchmarks: {benchmark_source}" in source
    assert "timeout=3" in source
    assert '"pytest" in sys.modules' in source


# ── Optimizer Ordering and Return Logic ───────────────────────────────────


def test_dash_2_optimizer_renders_before_ytd_chart() -> None:
    """Optimizer controls render before replay-sourced allocation and performance."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "_render_portfolio_builder_section()" in section_source
    assert "_render_portfolio_ytd_chart(daily_replay_context" in section_source
    assert section_source.index("_render_portfolio_builder_section()") < section_source.index("_render_portfolio_ytd_chart(daily_replay_context")
    assert "st.expander(" not in section_source


def test_dash_2_portfolio_page_separates_optimizer_and_replay_copy() -> None:
    """Portfolio page copy distinguishes optimizer output from replay output."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "Optimizer controls select the method and universe." in fn_source
    assert "one daily replay source" in fn_source
    assert "Strategy Replay" in source


def test_dash_2_optimizer_uses_explicit_universe_builder() -> None:
    """Portfolio optimizer defaults do not inherit display sort or top-20 slicing."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_section()")
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "build_optimizer_universe(" in section_source
    assert "universe.included_permnos" in section_source
    assert "universe_audit=universe" in section_source
    assert "selected_tickers[:20]" not in section_source
    assert 'list(df_scan["Ticker"].values)' not in section_source


def test_dash_2_optimizer_repairs_stale_endpoints_before_rebuilding_universe() -> None:
    """The repair lane is pre-universe, display-only, and not a canonical write."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_section()")
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "repair_stale_price_endpoints_with_live_overlay(" in section_source
    assert "universe.stale_endpoints" in section_source
    assert '"canonical_market_data_write": repair.canonical_market_data_write' in section_source
    assert "optimizer_prices = repair.prices" in section_source
    assert "build_optimizer_universe(" in section_source[section_source.index("if repair.repaired_columns:"):]
    assert "st.caption(" in section_source


def test_dash_2_replay_signature_includes_stale_endpoint_repair_state() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _dashboard_replay_data_signature()")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY" in fn_source
    assert "repair_signature" in fn_source


def test_dash_2_replay_selection_signature_uses_repaired_price_frame() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _current_portfolio_replay_selection(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "_price_frame_for_replay_selection_signature(replay_assets)" in fn_source
    assert "prices_wide=signature_prices" in fn_source


def test_dash_2_replay_inputs_accept_repaired_display_overlay() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _filter_dashboard_replay_inputs_to_assets(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "_portfolio_repair_overlay_frame(replay_assets)" in fn_source
    assert "repair_overlay.index <= pd.Timestamp(inputs.as_of_date).normalize()" in fn_source
    assert "asset in repair_overlay.columns" in fn_source
    assert "combine_first(prices)" in fn_source
    assert "returns.reindex(columns=selected_columns)" in fn_source
    assert '"dashboard_repair_overlay_columns"' in fn_source


def test_dash_2_optimizer_controls_hide_separate_allocation_output() -> None:
    """Top allocation display is the replay snapshot, not separate optimizer output."""
    source = DASHBOARD.read_text(encoding="utf-8")
    builder_start = source.index("def _render_portfolio_builder_section()")
    builder_end = source.index("\ndef ", builder_start + 1)
    builder_source = source[builder_start:builder_end]
    snapshot_start = source.index("def _render_replay_allocation_snapshot(")
    snapshot_end = source.index("\ndef ", snapshot_start + 1)
    snapshot_source = source[snapshot_start:snapshot_end]

    assert "show_allocation_outputs=False" in builder_source
    assert "Allocation (Latest Daily Replay Snapshot)" in snapshot_source
    assert '"target_weight": "Current Weight"' in snapshot_source
    assert "_replay_identity_caption(context)" in snapshot_source

    optimizer_source = Path("views/optimizer_view.py").read_text(encoding="utf-8")
    assert "Controls-only: allocation evidence is rendered from the latest daily replay snapshot below." in optimizer_source


def test_dash_2_placeholder_is_not_toggled() -> None:
    """Placeholder fallback is visible directly when optimizer dependencies are missing."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_placeholder()")
    next_def = source.index("\ndef ", start + 1)
    placeholder_source = source[start:next_def]

    assert "st.expander(" not in placeholder_source
    # Must NOT have the old 3-column preview
    assert "preview_cols" not in placeholder_source


def test_dash_2_portfolio_return_uses_replay_weights_before_optimizer_fallback() -> None:
    """Portfolio Performance consumes daily replay and does not fall back to optimizer weights."""
    source = DASHBOARD.read_text(encoding="utf-8")

    start = source.index("def _render_portfolio_ytd_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "STRATEGY_REPLAY_LATEST_WEIGHTS_KEY" in source
    assert "optimizer_weights" in source
    assert "_build_portfolio_ytd_equity_from_replay(" in fn_source
    assert "_build_portfolio_ytd_equity(" not in fn_source
    assert "_current_optimizer_weights()" not in fn_source
    assert "Daily replay performance unavailable" in fn_source


def test_dash_2_portfolio_ytd_prefers_local_history_before_live_overlay() -> None:
    """YTD chart must not shrink to a partial live-download window."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_portfolio_ytd_equity(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert fn_source.index('"optimized local fresh"') < fn_source.index('"optimized live"')


def test_dash_2_benchmark_ytd_prefers_local_history_before_live_overlay() -> None:
    """SPY/QQQ should stay visible from local TRI when live fetch is partial/rate-limited."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_benchmark_equity(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert fn_source.index("_local_benchmark_close_prices") < fn_source.index("_download_ytd_close_prices")


def test_dash_2_stale_local_qqq_gets_live_overlay_while_spy_stays_local(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    local = pd.DataFrame(
        {
            "SPY": [100.0, 101.0, 102.0],
            "QQQ": [200.0, 201.0, None],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-06"]),
    )
    live = pd.DataFrame(
        {"QQQ": [201.0, 204.0]},
        index=pd.to_datetime(["2026-01-03", "2026-01-06"]),
    )
    calls: list[tuple[tuple[str, ...], str]] = []

    def _download(tickers: tuple[str, ...], start_iso: str) -> pd.DataFrame:
        calls.append((tuple(tickers), start_iso))
        return live

    benchmark_equity, latest, source = build_benchmark_equity_from_prices(
        tickers=("SPY", "QQQ"),
        ytd_start=pd.Timestamp("2026-01-01"),
        local_prices=local,
        live_loader=_download,
    )

    assert calls == [(("QQQ",), "2026-01-01")]
    assert source == "local+live_overlay"
    assert latest == pd.Timestamp("2026-01-06")
    assert set(benchmark_equity) == {"SPY", "QQQ"}
    assert benchmark_equity["QQQ"].index.max() == pd.Timestamp("2026-01-06")
    assert benchmark_equity["QQQ"].iloc[-1] > benchmark_equity["QQQ"].iloc[0]


def test_dash_2_benchmark_does_not_forward_fill_stale_column_without_live_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    local = pd.DataFrame(
        {
            "SPY": [100.0, 101.0, 102.0],
            "QQQ": [200.0, 202.0, None],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"]),
    )
    calls: list[tuple[str, ...]] = []

    def _download(tickers: tuple[str, ...], start_iso: str) -> pd.DataFrame:
        calls.append(tuple(tickers))
        return pd.DataFrame()

    benchmark_equity, latest, source = build_benchmark_equity_from_prices(
        tickers=("SPY", "QQQ"),
        ytd_start=pd.Timestamp("2026-01-01"),
        local_prices=local,
        live_loader=_download,
    )

    assert calls == [("QQQ",)]
    assert source == "local_stale_dropped"
    assert latest == pd.Timestamp("2026-01-06")
    assert set(benchmark_equity) == {"SPY"}
    assert benchmark_equity["SPY"].index.max() == pd.Timestamp("2026-01-06")


def test_dash_2_benchmark_drops_no_overlap_live_overlay() -> None:
    local = pd.DataFrame(
        {
            "SPY": [100.0, 101.0, 102.0],
            "QQQ": [200.0, 202.0, None],
        },
        index=pd.to_datetime(["2026-01-02", "2026-02-27", "2026-05-02"]),
    )
    live = pd.DataFrame(
        {"QQQ": [210.0, 220.0]},
        index=pd.to_datetime(["2026-05-01", "2026-05-02"]),
    )

    benchmark_equity, latest, source = build_benchmark_equity_from_prices(
        tickers=("SPY", "QQQ"),
        ytd_start=pd.Timestamp("2026-01-01"),
        local_prices=local,
        live_loader=lambda *args: live,
    )

    assert source == "local_overlay_unavailable"
    assert latest == pd.Timestamp("2026-05-02")
    assert set(benchmark_equity) == {"SPY"}
    assert benchmark_equity["SPY"].index.max() == pd.Timestamp("2026-05-02")


def test_dash_2_weighted_ytd_fails_closed_when_weighted_asset_is_stale() -> None:
    import dashboard

    prices = pd.DataFrame(
        {
            "FRESH": [100.0, 110.0, 121.0],
            "STALE": [100.0, 150.0, None],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-03", "2026-05-11"]),
    )
    weights = pd.Series({"FRESH": 0.5, "STALE": 0.5})

    equity = dashboard._weighted_equity_curve(
        prices,
        weights,
        "Portfolio",
        required_latest=pd.Timestamp("2026-05-11"),
    )

    assert equity is None


def test_dash_2_weighted_ytd_fails_closed_when_live_prices_omit_weighted_asset() -> None:
    import dashboard

    prices = pd.DataFrame(
        {"AAA": [100.0, 110.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    weights = pd.Series({"AAA": 0.5, "BBB": 0.5})

    equity = dashboard._weighted_equity_curve(
        prices,
        weights,
        "Portfolio",
    )

    assert equity is None


def test_dash_2_replay_weights_require_matching_signature() -> None:
    import dashboard

    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1,))
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] = {1: 0.5}
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY] = {"method": "Rule of 100"}
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={"method": "Inverse Volatility"},
        source_label="test",
        replay_df=pd.DataFrame(),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=[],
        sampling="daily",
        status="ready",
        reason="",
    )

    assert dashboard._valid_strategy_replay_latest_weights() is None
    assert dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()


def test_dash_2_cached_ytd_replay_context_requires_current_signature() -> None:
    import dashboard

    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0], 2: [200.0, 202.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1,))
    stale_signature = dashboard._strategy_replay_cache_signature(
        method="Rule of 100",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        replay_assets=("2",),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        data_signature=dashboard._dashboard_replay_data_signature(),
    )
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] = {2: 0.5}
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Rule of 100",
        max_weight=0.35,
        controls={},
        cache_signature=stale_signature,
        source_label="stale",
        replay_df=pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-05-10", "2026-05-11"]),
                "portfolio_return": [0.01, 0.01],
            }
        ),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        status="ready",
        reason="",
    )

    assert dashboard._valid_cached_ytd_replay_context(pd.Timestamp("2026-05-10")) is None
    assert dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY not in dashboard.st.session_state
    assert dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()


def test_dash_2_cached_ytd_replay_context_reuses_superset_for_shorter_horizon() -> None:
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0, 102.0, 103.0]},
        index=pd.to_datetime(["2025-05-09", "2025-05-10", "2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1,))
    data_signature = dashboard._dashboard_replay_data_signature()
    superset_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        replay_assets=(1,),
        replay_dates=["2025-05-09", "2025-05-10", "2026-05-10", "2026-05-11"],
        sampling="daily",
        data_signature=data_signature,
    )
    replay_df = pd.DataFrame(
        {
            "date": ["2025-05-09", "2025-05-10", "2026-05-10", "2026-05-11"],
            "method": ["Inverse Volatility"] * 4,
            "ticker": ["AAA"] * 4,
            "permno": [1] * 4,
            "target_weight": [0.25, 0.30, 0.35, 0.40],
            "portfolio_return": [0.0, 0.01, 0.02, 0.03],
            "status": ["ok"] * 4,
            "reason": ["fixture"] * 4,
        }
    )
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        cache_signature=superset_signature,
        source_label="superset",
        replay_df=replay_df,
        latest_snapshot=replay_df.tail(1).copy(),
        event_annotations=pd.DataFrame({"date": ["2025-05-10", "2026-05-11"], "action": ["ENTER", "EXIT"]}),
        buy_sell_decisions=pd.DataFrame({"date": ["2025-05-10", "2026-05-11"], "action": ["BUY", "SELL"]}),
        replay_dates=["2025-05-09", "2025-05-10", "2026-05-10", "2026-05-11"],
        sampling="daily",
        status="ready",
        reason="",
        source_mode="transitional_build",
        date_window={"replay_start": "2025-05-09", "replay_end": "2026-05-11"},
    )

    scoped = dashboard._valid_cached_ytd_replay_context(pd.Timestamp("2026-05-01"))

    assert isinstance(scoped, dashboard.DashboardReplayContext)
    assert scoped is not dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY]
    assert scoped.replay_dates == ["2026-05-10", "2026-05-11"]
    assert set(scoped.replay_df["date"].astype(str)) == {"2026-05-10", "2026-05-11"}
    assert scoped.latest_snapshot["date"].astype(str).tolist() == ["2026-05-11"]
    assert scoped.event_annotations["action"].tolist() == ["EXIT"]
    assert scoped.buy_sell_decisions["action"].tolist() == ["SELL"]
    assert scoped.date_window["replay_start"] == "2026-05-10"
    assert scoped.date_window["replay_end"] == "2026-05-11"
    assert scoped.cache_signature["replay_dates"] == ["2026-05-10", "2026-05-11"]

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_cached_ytd_replay_context_rejects_superset_missing_requested_dates() -> None:
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1,))
    data_signature = dashboard._dashboard_replay_data_signature()
    cached_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        replay_assets=(1,),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        data_signature=data_signature,
    )
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        cache_signature=cached_signature,
        source_label="partial",
        replay_df=pd.DataFrame({"date": ["2026-05-11"], "portfolio_return": [0.01]}),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        status="ready",
        reason="",
    )

    assert dashboard._valid_cached_ytd_replay_context(pd.Timestamp("2026-05-10")) is None
    assert dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_ensure_daily_portfolio_replay_context_returns_cached_superset(monkeypatch: pytest.MonkeyPatch) -> None:
    import dashboard

    cached = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={},
        source_label="cached",
        replay_df=pd.DataFrame({"date": ["2026-05-11"], "portfolio_return": [0.01]}),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-11"],
        sampling="daily",
        status="ready",
        reason="",
    )
    monkeypatch.setattr(dashboard, "_valid_cached_ytd_replay_context", lambda horizon_start: cached)

    def _unexpected_build(*_args, **_kwargs):
        raise AssertionError("covered horizon should not rebuild daily replay")

    monkeypatch.setattr(dashboard, "_build_dashboard_strategy_replay_context", _unexpected_build)

    assert dashboard._ensure_daily_portfolio_replay_context(pd.Timestamp("2026-05-01")) is cached


def test_dash_2_cached_ytd_replay_context_requires_daily_sampling() -> None:
    import dashboard

    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1,))
    signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        replay_assets=("1",),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="weekly",
        data_signature=dashboard._dashboard_replay_data_signature(),
    )
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature=signature,
        source_label="sampled",
        replay_df=pd.DataFrame({"date": ["2026-05-10", "2026-05-11"], "portfolio_return": [0.0, 0.01]}),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="weekly",
        status="ready",
        reason="",
    )

    assert dashboard._valid_cached_ytd_replay_context(pd.Timestamp("2026-05-10")) is None
    assert dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_dashboard_replay_context_prefers_valid_saved_artifact(monkeypatch: pytest.MonkeyPatch) -> None:
    """Executable guard: one saved artifact feeds replay rows, snapshot, events, decisions, source, and signature."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0], 2: [200.0, 202.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1, 2))

    event_rows = pd.DataFrame(
        {
            "row_type": ["event_annotation"],
            "date": ["2026-05-11"],
            "ticker": ["AAA"],
            "action": ["ENTER"],
            "weight": [0.35],
            "reason": ["fixture_event"],
            "method": ["Inverse Volatility"],
        }
    )
    decision_rows = pd.DataFrame(
        {
            "row_type": ["buy_sell_decision"],
            "date": ["2026-05-11"],
            "ticker": ["AAA"],
            "action": ["BUY"],
            "weight": [0.35],
            "reason": ["fixture_decision"],
            "method": ["Inverse Volatility"],
        }
    )
    replay_rows = pd.DataFrame(
        {
            "row_type": ["daily_portfolio", "daily_portfolio", "daily_portfolio", "daily_portfolio"],
            "date": ["2026-05-10", "2026-05-10", "2026-05-11", "2026-05-11"],
            "method": ["Inverse Volatility"] * 4,
            "ticker": ["AAA", "CASH", "AAA", "CASH"],
            "permno": [1, "CASH", 1, "CASH"],
            "target_weight": [0.30, 0.70, 0.35, 0.65],
            "cash_residual": [0.70, 0.70, 0.65, 0.65],
            "portfolio_return": [0.0, 0.0, 0.01, 0.01],
            "source": ["saved_fixture"] * 4,
            "status": ["ok"] * 4,
            "reason": ["fixture"] * 4,
        }
    )
    request, _events, _decisions, unavailable = dashboard._build_dashboard_replay_request(
        replay_dates_override=["2026-05-10", "2026-05-11"]
    )
    assert unavailable == ""
    run_metadata = StrategyReplayRunMetadata(
        run_id="saved_run",
        method_id="Inverse Volatility",
        source_id="selected_method_replay:inverse_volatility:saved_run",
        input_signatures=(),
        date_window={
            "requested_start": "2026-05-10",
            "requested_end": "2026-05-11",
            "replay_start": "2026-05-10",
            "replay_end": "2026-05-11",
        },
        row_counts={
            "daily_portfolio": int(len(replay_rows)),
            "event_annotations": int(len(event_rows)),
            "buy_sell_decisions": int(len(decision_rows)),
            "total": int(len(replay_rows) + len(event_rows) + len(decision_rows)),
        },
        status_counts={"daily_portfolio": {"ok": 4}, "event_annotations": {"ok": 1}, "buy_sell_decisions": {"ok": 1}},
        timing={"started_at_utc": "2026-05-11T00:00:00Z", "completed_at_utc": "2026-05-11T00:00:01Z", "elapsed_ms": 1.0},
        input_coverage_start="2026-05-10",
    )
    bundle = StrategyReplayBundle(
        replay=replay_rows.drop(columns=["row_type"]),
        event_context=StrategyReplayContext(
            context_type="event_annotations",
            frame=event_rows.drop(columns=["row_type"]),
            status="ok",
            reason="fixture_event",
            source="fixture",
        ),
        decision_context=StrategyReplayContext(
            context_type="decision_context",
            frame=decision_rows.drop(columns=["row_type"]),
            status="ok",
            reason="fixture_decision",
            source="fixture",
        ),
        run_metadata=run_metadata,
    )
    manifest = {
        "artifact_type": "selected_method_replay_output",
        "display_only": True,
        "canonical_market_data_write": False,
        "method_id": "Inverse Volatility",
        "source_id": "selected_method_replay:inverse_volatility:saved_run",
        "row_count": int(run_metadata.row_counts["total"]),
        "row_counts": {
            "daily_portfolio": run_metadata.row_counts["daily_portfolio"],
            "event_annotations": run_metadata.row_counts["event_annotations"],
            "buy_sell_decisions": run_metadata.row_counts["buy_sell_decisions"],
            "total": run_metadata.row_counts["total"],
        },
        "date_window": {"replay_start": "2026-05-10", "replay_end": "2026-05-11"},
        "run_metadata": {"input_coverage_start": "2026-05-10"},
        "dashboard_cache_signature": request.cache_signature,
    }

    monkeypatch.setattr(
        dashboard,
        "_read_dashboard_saved_replay_artifact",
        lambda req: dashboard.DashboardReplayArtifactRead(
            status="ready",
            reason="ok",
            bundle=bundle,
            manifest=manifest,
        ),
    )

    def _unexpected_backend_build(*_args, **_kwargs):
        raise AssertionError("valid saved artifact should not rebuild replay")

    import strategies.strategy_replay as strat_replay

    monkeypatch.setattr(strat_replay, "build_selected_method_replay", _unexpected_backend_build)

    context = dashboard._build_dashboard_strategy_replay_context(
        replay_dates_override=["2026-05-10", "2026-05-11"]
    )

    assert context.status == "ready"
    assert context.source_mode == "saved_artifact"
    assert context.run_id == "saved_run"
    assert context.source_id == "selected_method_replay:inverse_volatility:saved_run"
    assert context.method_id == "Inverse Volatility"
    assert context.cache_signature == request.cache_signature
    assert set(context.replay_df["date"].astype(str)) == {"2026-05-10", "2026-05-11"}
    assert context.latest_snapshot["date"].astype(str).eq("2026-05-11").all()
    assert context.event_annotations["action"].tolist() == ["ENTER"]
    assert context.buy_sell_decisions["action"].tolist() == ["BUY"]
    assert dashboard.st.session_state[dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY] == request.cache_signature
    assert dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] == {1: 0.35}

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_saved_artifact_context_preserves_empty_event_and_decision_rows() -> None:
    """Saved-artifact mode must not fill empty artifact surfaces from fallback frames."""
    import dashboard

    request = dashboard._make_dashboard_replay_request(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"max_weight": 0.35, "risk_free_rate": 0.0},
        data_signature=(("prices_wide", "fixture"),),
        replay_assets=("1",),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        full_history_start="2026-05-10",
        include_replay=True,
    )
    replay_rows = pd.DataFrame(
        {
            "date": ["2026-05-10", "2026-05-11"],
            "method": ["Inverse Volatility", "Inverse Volatility"],
            "ticker": ["AAA", "AAA"],
            "permno": [1, 1],
            "target_weight": [0.30, 0.35],
            "cash_residual": [0.70, 0.65],
            "portfolio_return": [0.0, 0.01],
            "source": ["saved_fixture", "saved_fixture"],
            "status": ["ok", "ok"],
            "reason": ["fixture", "fixture"],
        }
    )
    run_metadata = StrategyReplayRunMetadata(
        run_id="saved_run_empty_aux",
        method_id="Inverse Volatility",
        source_id="selected_method_replay:inverse_volatility:saved_run_empty_aux",
        input_signatures=(),
        date_window={
            "requested_start": "2026-05-10",
            "requested_end": "2026-05-11",
            "replay_start": "2026-05-10",
            "replay_end": "2026-05-11",
        },
        row_counts={
            "daily_portfolio": int(len(replay_rows)),
            "event_annotations": 0,
            "buy_sell_decisions": 0,
            "total": int(len(replay_rows)),
        },
        status_counts={"daily_portfolio": {"ok": 2}, "event_annotations": {}, "buy_sell_decisions": {}},
        timing={"started_at_utc": "2026-05-11T00:00:00Z", "completed_at_utc": "2026-05-11T00:00:01Z", "elapsed_ms": 1.0},
        input_coverage_start="2026-05-10",
    )
    bundle = StrategyReplayBundle(
        replay=replay_rows,
        event_context=StrategyReplayContext(
            context_type="event_annotations",
            frame=pd.DataFrame(),
            status="ok",
            reason="artifact_empty",
            source="saved_fixture",
        ),
        decision_context=StrategyReplayContext(
            context_type="decision_context",
            frame=pd.DataFrame(),
            status="ok",
            reason="artifact_empty",
            source="saved_fixture",
        ),
        run_metadata=run_metadata,
    )
    fallback_events = pd.DataFrame(
        {"date": ["2026-05-11"], "ticker": ["AAA"], "action": ["ENTER"], "source": ["fallback"]}
    )
    fallback_decisions = pd.DataFrame(
        {"date": ["2026-05-11"], "ticker": ["AAA"], "action": ["BUY"], "source": ["fallback"]}
    )

    context = dashboard._dashboard_context_from_artifact_read(
        dashboard.DashboardReplayArtifactRead(
            status="ready",
            reason="ok",
            bundle=bundle,
            manifest={
                "source_id": "selected_method_replay:inverse_volatility:saved_run_empty_aux",
                "run_metadata": {"input_coverage_start": "2026-05-10"},
                "dashboard_cache_signature": request.cache_signature,
            },
        ),
        request,
        event_annotations=fallback_events,
        buy_sell_decisions=fallback_decisions,
    )

    assert context.status == "ready"
    assert context.source_mode == "saved_artifact"
    assert set(context.replay_df["date"].astype(str)) == {"2026-05-10", "2026-05-11"}
    assert context.event_annotations.empty
    assert context.buy_sell_decisions.empty


def test_dash_2_stale_saved_artifact_clears_replay_state_when_no_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stale saved artifacts must not reuse prior replay/YTD latest weights."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0], 2: [200.0, 202.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1, 2))
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY] = {"stale": True}
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] = {2: 0.90}
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY] = dashboard.DashboardReplayContext(
        method="Rule of 100",
        max_weight=0.35,
        controls={},
        cache_signature={"stale": True},
        source_label="old",
        replay_df=pd.DataFrame({"date": ["2026-05-10"], "portfolio_return": [0.01]}),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10"],
        sampling="daily",
        status="ready",
        reason="",
    )

    monkeypatch.setattr(
        dashboard,
        "_read_dashboard_saved_replay_artifact",
        lambda req: dashboard.DashboardReplayArtifactRead(status="unavailable", reason="dashboard_cache_signature_mismatch"),
    )

    context = dashboard._build_dashboard_strategy_replay_context(
        replay_dates_override=["2026-05-10", "2026-05-11"],
        allow_transitional_fallback=False,
    )

    assert context.status == "stale"
    assert context.source_mode == "unavailable"
    assert "dashboard_cache_signature_mismatch" in context.reason
    assert dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY not in dashboard.st.session_state
    assert dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY not in dashboard.st.session_state
    assert dashboard.STRATEGY_REPLAY_YTD_CONTEXT_KEY not in dashboard.st.session_state
    assert dashboard.STRATEGY_REPLAY_CONTEXT_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_dashboard_batched_replay_loader_keeps_signed_assets_only() -> None:
    """Batched PIT source data must still be limited to signed replay assets."""
    import dashboard
    from core.data_orchestrator import StrategyReplayInputs

    inputs = StrategyReplayInputs(
        as_of_date=pd.Timestamp("2026-05-11"),
        prices=pd.DataFrame(
            {
                1: [100.0, 101.0],
                2: [200.0, 202.0],
                3: [300.0, 303.0],
            },
            index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
        ),
        returns=pd.DataFrame(
            {
                1: [0.0, 0.01],
                2: [0.0, 0.01],
                3: [0.0, 0.01],
            },
            index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
        ),
        ticker_map={1: "AAA", 2: "BBB", 3: "CCC"},
        cache_signature={"universe_mode": "r3000_pit", "batched": True},
        cache_key="batched_pit_2026-05-11",
        metadata={"source": "batched_pit_replay"},
    )

    filtered = dashboard._filter_dashboard_replay_inputs_to_assets(inputs, (2, "3"))

    assert list(filtered.prices.columns) == [2, 3]
    assert list(filtered.returns.columns) == [2, 3]
    assert filtered.ticker_map == inputs.ticker_map
    assert filtered.cache_signature["dashboard_replay_assets"] == ["int:2", "str:3"]
    assert filtered.cache_signature["dashboard_selected_columns"] == ["int:2", "int:3"]
    assert filtered.cache_key.startswith("batched_pit_2026-05-11:dashboard_selected:")


def test_dash_2_replay_request_fails_closed_without_signed_selection() -> None:
    """Stale optimizer_universe cannot drive a valid-looking replay request."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {
            1: [100.0, 101.0],
            2: [200.0, 202.0],
            3: [300.0, 303.0],
        },
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    dashboard.st.session_state["optimizer_universe"] = [1, 2]  # legacy/stale key should be ignored

    request, _events, _decisions, unavailable = dashboard._build_dashboard_replay_request(
        replay_dates_override=["2026-05-10", "2026-05-11"]
    )

    assert unavailable == "portfolio_replay_selection_unavailable"
    assert request.replay_assets == ()
    assert dashboard._current_replay_assets_key() == ()
    assert dashboard.PORTFOLIO_REPLAY_SELECTION_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_replay_request_expands_assets_for_horizon_trade_history(monkeypatch: pytest.MonkeyPatch) -> None:
    """A flat current-hold ticker with in-window trades stays inside the single replay bundle."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.ticker_map_parquet = {14702: "AMAT", 48486: "LRCX", 85442: "TSM", 53613: "MU", 99999: "EXTRA"}
    dashboard.prices_wide = pd.DataFrame(
        {
            14702: [100.0, 101.0, 102.0],
            48486: [200.0, 201.0, 202.0],
            85442: [300.0, 301.0, 302.0],
            53613: [400.0, 401.0, 402.0],
            99999: [500.0, 501.0, 502.0],
        },
        index=pd.to_datetime(["2026-04-24", "2026-04-27", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Rule of 100"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(
        dashboard,
        (14702, 48486, 85442),
        method="Rule of 100",
        max_weight=0.35,
        risk_free_rate=0.0,
    )
    decisions = pd.DataFrame(
        {
            "date": ["2026-04-24", "2026-04-27"],
            "ticker": ["MU", "MU"],
            "action": ["BUY", "SELL"],
            "weight": [0.10, 0.0],
            "reason": ["fixture_buy", "fixture_sell"],
            "method": ["Rule of 100", "Rule of 100"],
        }
    )
    events = decisions.assign(action=["ENTER", "EXIT"])
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_event_annotations_cached", lambda _sig: events)
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_buy_sell_decisions_cached", lambda _sig: decisions)
    monkeypatch.setattr(dashboard, "_load_rule100_softmax_v1_history", lambda: pd.DataFrame(
        {
            "date": ["2026-04-24"],
            "ticker": ["MU"],
            "factor_positive_count": [3],
            "technical_quality": [0.5],
        }
    ))

    request, _events, _decisions, unavailable = dashboard._build_dashboard_replay_request(
        replay_dates_override=["2026-04-24", "2026-04-27", "2026-05-11"]
    )

    assert unavailable == ""
    assert request.replay_assets == (14702, 48486, 85442, 53613)
    assert request.allocation_assets == (14702, 48486, 85442)
    assert request.cache_signature["replay_assets"] == ["int:14702", "int:48486", "int:85442", "int:53613"]
    assert request.cache_signature["allocation_assets"] == ["int:14702", "int:48486", "int:85442"]
    assert dashboard._current_replay_assets_key() == (14702, 48486, 85442)

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.ticker_map_parquet = {}
    dashboard.st.session_state.clear()


def test_dash_2_single_bundle_keeps_mu_decisions_without_current_weight(monkeypatch: pytest.MonkeyPatch) -> None:
    """Expanded horizon assets retain MU decisions without making MU a latest holding."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.ticker_map_parquet = {14702: "AMAT", 48486: "LRCX", 85442: "TSM", 53613: "MU"}
    dashboard.prices_wide = pd.DataFrame(
        {
            14702: [100.0, 101.0, 102.0],
            48486: [200.0, 201.0, 202.0],
            85442: [300.0, 301.0, 302.0],
            53613: [400.0, 401.0, 402.0],
        },
        index=pd.to_datetime(["2026-04-24", "2026-04-27", "2026-05-11"]),
    )
    _store_dashboard_replay_selection(dashboard, (14702, 48486, 85442))
    decisions = pd.DataFrame(
        {
            "date": ["2026-04-24", "2026-04-27"],
            "ticker": ["MU", "MU"],
            "action": ["BUY", "SELL"],
            "weight": [0.10, 0.0],
            "reason": ["fixture_buy", "fixture_sell"],
            "method": ["Inverse Volatility", "Inverse Volatility"],
        }
    )
    events = decisions.assign(action=["ENTER", "EXIT"])
    loader_calls: list[tuple[int, ...] | None] = []
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_event_annotations_cached", lambda _sig: events)
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_buy_sell_decisions_cached", lambda _sig: decisions)
    monkeypatch.setattr(
        dashboard,
        "_read_dashboard_saved_replay_artifact",
        lambda _request: dashboard.DashboardReplayArtifactRead(status="unavailable", reason="fixture_no_artifact"),
    )

    def _fake_batched_loader(**kwargs):
        loader_calls.append(kwargs.get("selected_permnos"))
        selected_columns = list(kwargs.get("selected_permnos") or dashboard.prices_wide.columns)
        raw_prices = dashboard.prices_wide.reindex(columns=selected_columns)
        raw_returns = raw_prices.pct_change(fill_method=None).fillna(0.0)
        return BatchedPITReplayData(
            raw_prices=raw_prices,
            raw_returns=raw_returns,
            membership_dates=["2026-04-24", "2026-04-27", "2026-05-11"],
            membership_index={
                "2026-04-24": {14702, 48486, 85442, 53613, 99999},
                "2026-04-27": {14702, 48486, 85442, 53613, 99999},
                "2026-05-11": {14702, 48486, 85442, 53613, 99999},
            },
            ticker_map=dashboard.ticker_map_parquet,
            trading_dates=list(dashboard.prices_wide.index),
            metadata={
                "fixture": "batched",
                "selected_columns": selected_columns,
            },
        )

    monkeypatch.setattr(
        dashboard,
        "_load_dashboard_batched_pit_replay_data_cached",
        _fake_batched_loader,
    )

    def _fake_build_selected_method_replay(**kwargs):
        assert kwargs["input_loader"](as_of_date="2026-04-27", start_date="", end_date="", method="", controls={}).prices.columns.tolist() == [
            14702,
            48486,
            85442,
        ]
        replay = pd.DataFrame(
            {
                "date": [
                    "2026-04-24", "2026-04-24", "2026-04-24", "2026-04-24",
                    "2026-04-27", "2026-04-27", "2026-04-27", "2026-04-27",
                    "2026-05-11", "2026-05-11", "2026-05-11", "2026-05-11",
                ],
                "method": ["Inverse Volatility"] * 12,
                "ticker": ["AMAT", "LRCX", "TSM", "CASH"] * 3,
                "permno": [14702, 48486, 85442, "CASH"] * 3,
                "target_weight": [
                    0.30, 0.30, 0.30, 0.10,
                    0.30, 0.30, 0.30, 0.10,
                    0.30, 0.30, 0.30, 0.10,
                ],
                "cash_residual": [0.10] * 12,
                "portfolio_return": [0.0, 0.0, 0.0, 0.0] * 3,
                "source": ["fixture_bundle"] * 12,
                "status": ["ok"] * 12,
                "reason": ["fixture"] * 12,
            }
        )
        metadata = StrategyReplayRunMetadata(
            run_id="fixture_run",
            method_id="Inverse Volatility",
            source_id="fixture_source",
            input_signatures=(),
            date_window={
                "requested_start": "2026-04-24",
                "requested_end": "2026-05-11",
                "replay_start": "2026-04-24",
                "replay_end": "2026-05-11",
            },
            row_counts={"daily_portfolio": len(replay), "event_annotations": 0, "buy_sell_decisions": 0, "total": len(replay)},
            status_counts={"daily_portfolio": {"ok": len(replay)}, "event_annotations": {"empty": 1}, "buy_sell_decisions": {"empty": 1}},
            timing={"started_at_utc": "2026-05-11T00:00:00Z", "completed_at_utc": "2026-05-11T00:00:01Z", "elapsed_ms": 1.0},
        )
        return StrategyReplayBundle(
            replay=replay,
            event_context=StrategyReplayContext(
                context_type="event_annotations",
                frame=pd.DataFrame(),
                status="empty",
                reason="fixture_events",
                source="fixture",
            ),
            decision_context=StrategyReplayContext(
                context_type="decision_context",
                frame=pd.DataFrame(),
                status="empty",
                reason="fixture_decisions",
                source="fixture",
            ),
            run_metadata=metadata,
        )

    import strategies.strategy_replay as strat_replay

    monkeypatch.setattr(strat_replay, "build_selected_method_replay", _fake_build_selected_method_replay)

    context = dashboard._build_dashboard_strategy_replay_context(
        replay_dates_override=["2026-04-24", "2026-04-27", "2026-05-11"]
    )

    assert loader_calls == [(14702, 48486, 85442)]
    assert 99999 not in loader_calls[0]
    assert context.status == "ready"
    assert context.cache_signature["replay_assets"] == ["int:14702", "int:48486", "int:85442", "int:53613"]
    assert context.buy_sell_decisions["ticker"].tolist() == ["MU", "MU"]
    assert context.buy_sell_decisions["target_weight"].astype(float).tolist() == pytest.approx([0.0, 0.0])
    assert context.buy_sell_decisions["audit_weight"].astype(float).tolist() == pytest.approx([0.10, 0.0])
    assert context.buy_sell_decisions["context_role"].tolist() == ["flat_in_replay", "flat_in_replay"]
    latest_weights = (
        context.latest_snapshot.set_index("ticker")["target_weight"].astype(float).to_dict()
    )
    assert latest_weights["MU"] == pytest.approx(0.0)
    assert context.latest_snapshot.set_index("ticker").loc["MU", "status"] == "context_only"
    assert context.latest_snapshot.set_index("ticker").loc["MU", "context_role"] == "historical_context"
    assert latest_weights["AMAT"] == pytest.approx(0.30)
    assert dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] == {
        14702: 0.30,
        48486: 0.30,
        85442: 0.30,
    }

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.ticker_map_parquet = {}
    dashboard.st.session_state.clear()


def test_dash_2_dashboard_aux_weights_align_to_replay_targets() -> None:
    """Dashboard-side aux normalization uses replay target_weight and preserves legacy weight as audit."""
    import dashboard

    replay = pd.DataFrame(
        {
            "date": ["2026-04-24", "2026-04-24"],
            "ticker": ["AAA", "CASH"],
            "target_weight": [0.35, 0.65],
        }
    )
    aux = pd.DataFrame(
        {
            "date": ["2026-04-24"],
            "ticker": ["AAA"],
            "method": ["Inverse Volatility"],
            "action": ["ENTER"],
            "weight": [0.10],
            "reason": ["legacy_event_weight"],
        }
    )

    normalized = dashboard._normalize_dashboard_context_frame(
        aux,
        context_type="event_annotations",
        method="Inverse Volatility",
        replay=replay,
    )
    aligned = dashboard._align_context_weights_to_replay(normalized, replay)

    assert float(normalized["target_weight"].iloc[0]) == pytest.approx(0.35)
    assert float(normalized["weight"].iloc[0]) == pytest.approx(0.10)
    assert normalized["row_role"].iloc[0] == "event_annotations"
    assert normalized["context_role"].iloc[0] == "current_holding"
    assert float(aligned["target_weight"].iloc[0]) == pytest.approx(0.35)
    assert float(aligned["audit_weight"].iloc[0]) == pytest.approx(0.10)
    assert float(aligned["weight"].iloc[0]) == pytest.approx(0.35)
    assert aligned["context_role"].iloc[0] == "current_holding"


def test_dash_2_dashboard_context_normalization_delegates_to_strategy_contract() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _normalize_dashboard_context_frame(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "normalize_context_frame_for_replay(" in fn_source
    assert "work = frame.copy()" not in fn_source
    assert "work.merge(replay_weights" not in fn_source


def test_dash_2_context_only_horizon_asset_does_not_enter_real_optimizer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-Rule100 replay optimizes only signed allocation assets, then adds MU as context-only."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.ticker_map_parquet = {14702: "AMAT", 48486: "LRCX", 85442: "TSM", 53613: "MU"}
    dashboard.prices_wide = pd.DataFrame(
        {
            14702: [100.0, 101.0, 102.0],
            48486: [200.0, 201.0, 202.0],
            85442: [300.0, 301.0, 302.0],
            53613: [400.0, 401.0, 402.0],
        },
        index=pd.to_datetime(["2026-04-24", "2026-04-27", "2026-05-11"]),
    )
    _store_dashboard_replay_selection(dashboard, (14702, 48486, 85442))
    decisions = pd.DataFrame(
        {
            "date": ["2026-04-24", "2026-04-27"],
            "ticker": ["MU", "MU"],
            "action": ["BUY", "SELL"],
            "weight": [0.10, 0.0],
            "reason": ["fixture_buy", "fixture_sell"],
            "method": ["Inverse Volatility", "Inverse Volatility"],
        }
    )
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_event_annotations_cached", lambda _sig: decisions.assign(action=["ENTER", "EXIT"]))
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_buy_sell_decisions_cached", lambda _sig: decisions)
    monkeypatch.setattr(
        dashboard,
        "_read_dashboard_saved_replay_artifact",
        lambda _request: dashboard.DashboardReplayArtifactRead(status="unavailable", reason="fixture_no_artifact"),
    )

    def _fake_batched_loader(**kwargs):
        selected_columns = list(kwargs.get("selected_permnos") or ())
        raw_prices = dashboard.prices_wide.reindex(columns=selected_columns)
        return BatchedPITReplayData(
            raw_prices=raw_prices,
            raw_returns=raw_prices.pct_change(fill_method=None).fillna(0.0),
            membership_dates=["2026-04-24", "2026-04-27", "2026-05-11"],
            membership_index={
                "2026-04-24": {14702, 48486, 85442, 53613},
                "2026-04-27": {14702, 48486, 85442, 53613},
                "2026-05-11": {14702, 48486, 85442, 53613},
            },
            ticker_map=dashboard.ticker_map_parquet,
            trading_dates=list(dashboard.prices_wide.index),
            metadata={"fixture": "batched"},
        )

    monkeypatch.setattr(dashboard, "_load_dashboard_batched_pit_replay_data_cached", _fake_batched_loader)

    optimizer_columns: list[tuple[object, ...]] = []

    def _inverse(self, prices_df: pd.DataFrame, max_weight: float):
        optimizer_columns.append(tuple(prices_df.columns))
        return type(
            "Result",
            (),
            {
                "weights": pd.Series({14702: 0.30, 48486: 0.30, 85442: 0.30}),
                "status": "optimized",
                "message": "fixture",
            },
        )()

    monkeypatch.setattr(
        "strategies.optimizer.PortfolioOptimizer.optimize_inverse_volatility_with_diagnostics",
        _inverse,
    )

    context = dashboard._build_dashboard_strategy_replay_context(
        replay_dates_override=["2026-04-24", "2026-04-27", "2026-05-11"]
    )

    assert context.status == "ready"
    assert optimizer_columns
    assert all(53613 not in columns for columns in optimizer_columns)
    latest = context.latest_snapshot.set_index("ticker")
    assert latest.loc["MU", "status"] == "context_only"
    assert float(latest.loc["MU", "target_weight"]) == pytest.approx(0.0)
    assert latest.loc["MU", "context_role"] == "historical_context"
    assert 53613 not in dashboard.st.session_state[dashboard.STRATEGY_REPLAY_LATEST_WEIGHTS_KEY]
    assert context.buy_sell_decisions["ticker"].tolist() == ["MU", "MU"]

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.ticker_map_parquet = {}
    dashboard.st.session_state.clear()


def test_dash_2_coverage_prefilter_uses_allocation_assets_not_full_pit_membership(monkeypatch: pytest.MonkeyPatch) -> None:
    """Coverage pre-gate cannot emit unrequested PIT members into dashboard replay rows."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.ticker_map_parquet = {14702: "AMAT", 53613: "MU", 99999: "ZZZ"}
    dashboard.prices_wide = pd.DataFrame(
        {
            14702: [100.0],
            53613: [400.0],
            99999: [900.0],
        },
        index=pd.to_datetime(["2026-04-24"]),
    )
    _store_dashboard_replay_selection(dashboard, (14702,))
    decisions = pd.DataFrame(
        {
            "date": ["2026-04-24"],
            "ticker": ["MU"],
            "action": ["BUY"],
            "weight": [0.10],
            "method": ["Inverse Volatility"],
        }
    )
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_event_annotations_cached", lambda _sig: decisions.assign(action=["ENTER"]))
    monkeypatch.setattr(dashboard, "_load_dashboard_replay_buy_sell_decisions_cached", lambda _sig: decisions)
    monkeypatch.setattr(
        dashboard,
        "_read_dashboard_saved_replay_artifact",
        lambda _request: dashboard.DashboardReplayArtifactRead(status="unavailable", reason="fixture_no_artifact"),
    )

    selected_permnos_seen: list[tuple[int, ...] | None] = []

    def _fake_batched_loader(**kwargs):
        selected_permnos_seen.append(kwargs.get("selected_permnos"))
        return BatchedPITReplayData(
            raw_prices=pd.DataFrame(index=dashboard.prices_wide.index),
            raw_returns=pd.DataFrame(index=dashboard.prices_wide.index),
            membership_dates=["2026-04-24"],
            membership_index={"2026-04-24": {14702, 53613, 99999}},
            ticker_map=dashboard.ticker_map_parquet,
            trading_dates=list(dashboard.prices_wide.index),
            metadata={"fixture": "batched"},
        )

    monkeypatch.setattr(dashboard, "_load_dashboard_batched_pit_replay_data_cached", _fake_batched_loader)

    context = dashboard._build_dashboard_strategy_replay_context(
        replay_dates_override=["2026-04-24"]
    )

    assert selected_permnos_seen == [(14702,)]
    assert context.status == "ready"
    assert set(context.replay_df["permno"].astype(str)) <= {"14702", "53613", "CASH"}
    assert "99999" not in set(context.replay_df["permno"].astype(str))
    assert context.replay_df[context.replay_df["permno"].astype(str) == "53613"]["status"].eq("context_only").all()

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.ticker_map_parquet = {}
    dashboard.st.session_state.clear()


def test_dash_2_replay_selection_signature_rejects_stale_asset_set() -> None:
    """Selection signatures bind the replay assets to the current price frame and controls."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0], 2: [200.0, 202.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    stale_signature = dashboard.build_portfolio_replay_selection_signature(
        prices_wide=dashboard.prices_wide,
        replay_assets=(1,),
        method="Inverse Volatility",
        max_weight=0.35,
        risk_free_rate=0.0,
    )
    dashboard.st.session_state[dashboard.PORTFOLIO_REPLAY_SELECTION_KEY] = dashboard.PortfolioReplaySelection(
        method="Inverse Volatility",
        max_weight=0.35,
        risk_free_rate=0.0,
        replay_assets=(1, 2),
        latest_price_date="2026-05-11",
        source="optimizer_controls",
        signature=stale_signature,
    )

    assert dashboard._current_replay_assets_key() == ()
    assert dashboard.PORTFOLIO_REPLAY_SELECTION_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_replay_selection_signature_rejects_price_content_drift() -> None:
    """Same-shape same-asset price edits must invalidate replay selection."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    original = pd.DataFrame(
        {1: [100.0, 101.0], 2: [200.0, 202.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    dashboard.prices_wide = original.copy()
    dashboard.st.session_state["optimizer_method"] = "Inverse Volatility"
    dashboard.st.session_state["optimizer_max_weight"] = 0.35
    dashboard.st.session_state["optimizer_risk_free_rate"] = 0.0
    _store_dashboard_replay_selection(dashboard, (1, 2))
    signature = dashboard.st.session_state[dashboard.PORTFOLIO_REPLAY_SELECTION_KEY].signature

    dashboard.prices_wide = original.copy()
    dashboard.prices_wide.loc[pd.Timestamp("2026-05-11"), 2] = 203.0
    dashboard.st.session_state[dashboard.PORTFOLIO_REPLAY_SELECTION_KEY] = dashboard.PortfolioReplaySelection(
        method="Inverse Volatility",
        max_weight=0.35,
        risk_free_rate=0.0,
        replay_assets=(1, 2),
        latest_price_date="2026-05-11",
        source="optimizer_controls",
        signature=signature,
    )

    assert dashboard._current_replay_assets_key() == ()
    assert dashboard.PORTFOLIO_REPLAY_SELECTION_KEY not in dashboard.st.session_state

    dashboard.parquet_data_available = False
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_replay_cache_signature_preserves_asset_types() -> None:
    """Dashboard replay signatures must distinguish integer and string asset IDs."""
    import dashboard

    int_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"risk_free_rate": 0.0},
        replay_assets=(1,),
        replay_dates=["2026-05-11"],
        sampling="daily",
        data_signature=(("fixture", "same"),),
    )
    str_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"risk_free_rate": 0.0},
        replay_assets=("1",),
        replay_dates=["2026-05-11"],
        sampling="daily",
        data_signature=(("fixture", "same"),),
    )

    assert int_signature["replay_assets"] == ["int:1"]
    assert str_signature["replay_assets"] == ["str:1"]
    assert int_signature != str_signature


def test_dash_2_cache_signature_distinguishes_allocation_assets_from_context_assets() -> None:
    """Same horizon union but different current allocation assets must not reuse cached replay."""
    import dashboard

    context_only_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"risk_free_rate": 0.0},
        replay_assets=(1, 2),
        allocation_assets=(1,),
        replay_dates=["2026-05-11"],
        sampling="daily",
        data_signature=(("fixture", "same"),),
    )
    allocatable_signature = dashboard._strategy_replay_cache_signature(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={"risk_free_rate": 0.0},
        replay_assets=(1, 2),
        allocation_assets=(1, 2),
        replay_dates=["2026-05-11"],
        sampling="daily",
        data_signature=(("fixture", "same"),),
    )

    assert context_only_signature["replay_assets"] == allocatable_signature["replay_assets"]
    assert context_only_signature["allocation_assets"] == ["int:1"]
    assert allocatable_signature["allocation_assets"] == ["int:1", "int:2"]
    assert context_only_signature != allocatable_signature


def test_dash_2_builder_error_clears_signed_replay_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Optimizer builder failures cannot leave a stale replay selection behind."""
    import dashboard

    dashboard.st.session_state.clear()
    dashboard.parquet_data_available = True
    dashboard.fundamentals_wide = pd.DataFrame({"x": [1]})
    dashboard.prices_wide = pd.DataFrame(
        {1: [100.0, 101.0]},
        index=pd.to_datetime(["2026-05-10", "2026-05-11"]),
    )
    _store_dashboard_replay_selection(dashboard, (1,))
    dashboard.st.session_state[dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY] = {"stale": True}
    dashboard.st.session_state["portfolio_allocation_state"] = {
        "mode": "optimizer",
        "source": "optimizer",
        "weights": {1: 0.75},
        "cash_only": False,
        "latest_price_date": "2026-05-11",
    }
    dashboard.st.session_state["optimizer_weights"] = {1: 0.75}

    monkeypatch.setattr(dashboard, "load_current_position_memory", lambda: {})

    def _raise_builder(*_args, **_kwargs):
        raise RuntimeError("fixture builder error")

    monkeypatch.setattr(dashboard, "build_optimizer_universe", _raise_builder)
    monkeypatch.setattr(dashboard.st, "error", lambda *_args, **_kwargs: None)

    dashboard._render_portfolio_builder_section()

    assert dashboard.PORTFOLIO_REPLAY_SELECTION_KEY not in dashboard.st.session_state
    assert dashboard.STRATEGY_REPLAY_CACHE_SIGNATURE_KEY not in dashboard.st.session_state
    assert dashboard.st.session_state["portfolio_allocation_state"]["mode"] == "unavailable"
    assert dashboard.st.session_state["optimizer_weights"] == {}
    assert dashboard._current_optimizer_weights().empty

    dashboard.parquet_data_available = False
    dashboard.fundamentals_wide = None
    dashboard.prices_wide = pd.DataFrame()
    dashboard.st.session_state.clear()


def test_dash_2_stale_replay_context_renders_specific_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stale replay source reasons should be visible instead of falling through to empty-data copy."""
    import dashboard

    warnings: list[str] = []
    monkeypatch.setattr(dashboard.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "warning", lambda message, *_args, **_kwargs: warnings.append(str(message)))
    monkeypatch.setattr(dashboard.st, "info", lambda *_args, **_kwargs: None)

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={},
        source_label="fixture",
        replay_df=pd.DataFrame(),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10", "2026-05-11"],
        sampling="daily",
        status="stale",
        reason="saved_artifact_unavailable:dashboard_cache_signature_mismatch",
        source_mode="unavailable",
    )

    dashboard._render_strategy_replay_section(context)

    assert warnings == ["saved_artifact_unavailable:dashboard_cache_signature_mismatch"]


def test_dash_2_strategy_replay_section_ignores_event_rows_missing_action(monkeypatch: pytest.MonkeyPatch) -> None:
    """Partial event frames should render empty events instead of raising KeyError."""
    import dashboard

    info_messages: list[str] = []
    monkeypatch.setattr(dashboard.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "warning", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "info", lambda message, *_args, **_kwargs: info_messages.append(str(message)))
    monkeypatch.setattr(dashboard.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "dataframe", lambda *_args, **_kwargs: None)

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={},
        source_label="fixture",
        replay_df=pd.DataFrame(
            {
                "date": ["2026-05-10"],
                "ticker": ["AAA"],
                "target_weight": [0.35],
                "status": ["ok"],
                "reason": ["fixture"],
            }
        ),
        latest_snapshot=pd.DataFrame(
            {
                "date": ["2026-05-10"],
                "ticker": ["AAA"],
                "target_weight": [0.35],
            }
        ),
        event_annotations=pd.DataFrame({"date": ["2026-05-10"], "ticker": ["AAA"], "weight": [0.10]}),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10"],
        sampling="daily",
        status="ready",
        reason="",
    )

    dashboard._render_strategy_replay_section(context)

    assert "No replay lifecycle events in this replay window." in info_messages


def test_dash_2_strategy_replay_section_handles_partial_latest_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Latest snapshot display should fail soft when optional replay metadata is absent."""
    import dashboard

    info_messages: list[str] = []
    monkeypatch.setattr(dashboard.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "warning", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "info", lambda message, *_args, **_kwargs: info_messages.append(str(message)))
    monkeypatch.setattr(dashboard.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "dataframe", lambda *_args, **_kwargs: None)

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={},
        source_label="fixture",
        replay_df=pd.DataFrame(
            {
                "date": ["2026-05-10"],
                "ticker": ["AAA"],
                "target_weight": [0.35],
                "status": ["ok"],
                "reason": ["fixture"],
            }
        ),
        latest_snapshot=pd.DataFrame({"date": ["2026-05-10"], "ticker": ["AAA"]}),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(),
        replay_dates=["2026-05-10"],
        sampling="daily",
        status="ready",
        reason="",
    )

    dashboard._render_strategy_replay_section(context)

    assert "Latest replay snapshot unavailable for this source schema." in info_messages


def test_dash_2_strategy_replay_section_labels_replay_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Renderer exposes role-aware replay labels instead of generic weight semantics."""
    import dashboard

    dataframe_payloads: list[pd.DataFrame] = []
    monkeypatch.setattr(dashboard.st, "subheader", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "warning", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dashboard.st, "plotly_chart", lambda *_args, **_kwargs: None)

    def _capture_dataframe(data, *_args, **_kwargs):
        dataframe_payloads.append(getattr(data, "data", data).copy())

    monkeypatch.setattr(dashboard.st, "dataframe", _capture_dataframe)

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={"fixture": "roles"},
        source_label="fixture",
        replay_df=pd.DataFrame(
            {
                "date": ["2026-05-10", "2026-05-10", "2026-05-10"],
                "ticker": ["AMAT", "MU", "CASH"],
                "target_weight": [0.35, 0.0, 0.65],
                "context_role": ["current_holding", "historical_context", "cash"],
                "status": ["ok", "context_only", "ok"],
                "reason": ["fixture", "historical_context_asset_not_current_allocation", "cash_residual"],
            }
        ),
        latest_snapshot=pd.DataFrame(
            {
                "date": ["2026-05-10", "2026-05-10", "2026-05-10"],
                "ticker": ["AMAT", "MU", "CASH"],
                "target_weight": [0.35, 0.0, 0.65],
                "context_role": ["current_holding", "historical_context", "cash"],
                "status": ["ok", "context_only", "ok"],
            }
        ),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(
            {
                "date": ["2026-05-10"],
                "ticker": ["MU"],
                "action": ["BUY"],
                "reason": ["fixture_buy"],
                "target_weight": [0.0],
                "audit_weight": [0.10],
                "context_role": ["flat_in_replay"],
            }
        ),
        replay_dates=["2026-05-10"],
        sampling="daily",
        status="ready",
        reason="",
    )

    dashboard._render_strategy_replay_section(context)

    assert any("Replay Weight" in df.columns for df in dataframe_payloads)
    assert any("Context Role" in df.columns for df in dataframe_payloads)
    decision_tables = [df for df in dataframe_payloads if "Aux Audit Wt" in df.columns]
    assert decision_tables
    assert decision_tables[0].loc[0, "Context Role"] == "flat_in_replay"


def test_dash_2_replay_context_diagnostics_use_existing_bundle_identity() -> None:
    """Diagnostic evidence is post-processing over DashboardReplayContext, not a second replay."""
    import dashboard

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={"fixture": "diagnostics"},
        source_label="fixture",
        replay_df=pd.DataFrame(
            {
                "date": ["2026-05-01", "2026-05-02", "2026-05-03"],
                "ticker": ["MU", "MU", "MU"],
                "target_weight": [0.0, 0.0, 0.0],
                "portfolio_return": [0.01, -0.02, 0.03],
            }
        ),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(
            {
                "date": ["2026-05-01", "2026-05-03"],
                "ticker": ["MU", "MU"],
                "action": ["BUY", "SELL"],
                "reason": ["entry_reason", "exit_reason"],
                "target_weight": [0.0, 0.0],
                "audit_weight": [0.10, 0.0],
                "context_role": ["flat_in_replay", "flat_in_replay"],
            }
        ),
        replay_dates=["2026-05-01", "2026-05-02", "2026-05-03"],
        sampling="daily",
        status="ready",
        reason="",
        run_id="run_fixture",
        source_id="source_fixture",
        method_id="Inverse Volatility",
    )

    diagnostics = dashboard._build_replay_context_diagnostics(context)

    assert diagnostics["identity"]["run_id"] == "run_fixture"
    assert diagnostics["identity"]["source_id"] == "source_fixture"
    assert diagnostics["zero_exposure_buy_rows"]["count"] == 1
    assert diagnostics["closed_trade_return_summary"]["closed_trades"] == 1
    assert diagnostics["hold_time_summary"]["max_days"] == 2
    assert diagnostics["exit_reason_quality"]["missing_reason_rows"] == 0
    assert diagnostics["reason_code_concentration"]["unique_reasons"] == 2


def test_dash_2_replay_context_diagnostics_do_not_rebuild_or_reread(monkeypatch: pytest.MonkeyPatch) -> None:
    import dashboard
    import strategies.strategy_replay as strat_replay

    def _forbidden(*_args, **_kwargs):
        raise AssertionError("diagnostics must not rebuild or reread replay")

    monkeypatch.setattr(strat_replay, "build_selected_method_replay", _forbidden, raising=False)
    monkeypatch.setattr(strat_replay, "read_selected_method_replay_artifact", _forbidden, raising=False)
    monkeypatch.setattr(pd, "read_json", _forbidden)

    context = dashboard.DashboardReplayContext(
        method="Inverse Volatility",
        max_weight=0.35,
        controls={},
        cache_signature={"fixture": "no_rebuild"},
        source_label="fixture",
        replay_df=pd.DataFrame(
            {
                "date": ["2026-05-01"],
                "ticker": ["AMAT"],
                "target_weight": [0.35],
                "portfolio_return": [0.01],
            }
        ),
        latest_snapshot=pd.DataFrame(),
        event_annotations=pd.DataFrame(),
        buy_sell_decisions=pd.DataFrame(
            {
                "date": ["2026-05-01"],
                "ticker": ["AMAT"],
                "action": ["BUY"],
                "reason": ["entry_reason"],
                "target_weight": [0.35],
            }
        ),
        replay_dates=["2026-05-01"],
        sampling="daily",
        status="ready",
        reason="",
    )

    diagnostics = dashboard._build_replay_context_diagnostics(context)

    assert diagnostics["zero_exposure_buy_rows"]["count"] == 0


def test_dash_2_live_ticker_weights_preserve_residual_cash() -> None:
    """Live ticker YTD path preserves residual cash for sub-100% lifecycle holds."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _weights_by_ticker(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "map_permno_weights_to_ticker_weights(weights, ticker_map_parquet)" in fn_source
    assert "return out / float(out.sum())" not in fn_source


def test_dash_2_cash_only_optimizer_ytd_is_flat_cash_not_equal_weight() -> None:
    """Cash-only optimizer state renders a flat 0% cash curve, not EW fallback."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_portfolio_ytd_equity(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert "_current_optimizer_is_cash_only()" in fn_source
    assert "_cash_equity_curve(ytd_start)" in fn_source
    assert '"cash-only"' in fn_source
    assert fn_source.index("_current_optimizer_is_cash_only()") < fn_source.index('"equal-weight local"')


def test_dash_2_ytd_rejects_non_finite_return_math() -> None:
    """YTD return path cannot leak inf into chart or metric values."""
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "filter_price_frame_to_fresh_columns(" in source
    assert "min_count=len(cols)" in source
    assert "daily_returns = daily_returns.replace([np.inf, -np.inf], np.nan)" in source
    assert "equity = equity.replace([np.inf, -np.inf], np.nan).dropna()" in source
    assert "if not np.isfinite(pf_ret):" in source
    assert "if not np.isfinite(ret):" in source


def test_dash_2_price_freshness_refreshes_live_prices() -> None:
    """Portfolio slice refreshes prices through data orchestration helpers."""
    dashboard_source = DASHBOARD.read_text(encoding="utf-8")
    view_source = Path("views/optimizer_view.py").read_text(encoding="utf-8")
    orchestrator_source = Path("core/data_orchestrator.py").read_text(encoding="utf-8")

    assert "_download_ytd_close_prices" in dashboard_source
    assert "Stock prices refreshed through" in dashboard_source
    assert "refresh_selected_prices_with_live_overlay" in view_source
    assert "Price data through" in view_source
    assert "import yfinance" not in view_source
    assert "yf.download(" not in view_source
    assert "def download_recent_close_prices(" in orchestrator_source
    assert "def scale_live_overlay_to_local(" in orchestrator_source
    assert "OPTIMIZER_LIVE_OVERLAY_CACHE_DIR" in orchestrator_source
    assert "schedule_background" in orchestrator_source
    assert "to_parquet" in orchestrator_source
    assert "pd.Timestamp(local_endpoint).normalize() - pd.Timedelta(days=10)" in orchestrator_source


def test_dash_2_optimizer_defaults_match_endgame_risk_controls() -> None:
    """Optimizer defaults use 35% max weight without forcing MU."""
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "DEFAULT_MAX_WEIGHT = 0.35" in source
    assert 'help="Default is 35%; 33% is the intended operating target."' in source
    assert '"MU minimum"' not in source
    assert "DEFAULT_MICRON_MIN_WEIGHT" not in source


# ── Hedge Harvester Archived ──────────────────────────────────────────────


def test_dash_2_hedge_harvester_removed_from_research_lab() -> None:
    """Hedge Harvester is no longer in the Research Lab radio options."""
    source = DASHBOARD.read_text(encoding="utf-8")
    # Research Lab is now dead code but still exists; verify hedge harvester
    # is not wired into any active page renderer
    start = source.index("def _render_discovery_page()")
    next_def = source.index("\ndef ", start + 1)
    discovery_source = source[start:next_def]

    assert "Hedge Harvester" not in discovery_source
    assert "_render_hedge_harvester_section" not in discovery_source


def test_dash_2_hedge_harvester_function_still_exists() -> None:
    """Hedge Harvester function is preserved in source (archived, not deleted)."""
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "def _render_hedge_harvester_section()" in source


# ── No Forbidden Runtime Scope ────────────────────────────────────────────


def test_dash_2_no_forbidden_runtime_scope() -> None:
    """DASH-2 did not introduce forbidden execution/signal scope."""
    source = DASHBOARD.read_text(encoding="utf-8")
    forbidden_tokens = [
        "submit_order",
        "buy_sell_hold",
        "factor_scout",
        "local_factor_scout",
        "phase34_factor_scores",
    ]
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered, f"Forbidden token '{token}' found in dashboard.py"


# ── Existing DASH-1 Invariants Still Hold ─────────────────────────────────


def test_dash_2_page_registry_navigation_preserved() -> None:
    """Page registry navigation pattern preserved."""
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "build_dashboard_navigation(" in source
    assert "page.run()" in source
    assert "st.tabs(" not in source


def test_dash_2_key_render_functions_preserved() -> None:
    """Key render functions from DASH-1 still exist."""
    source = DASHBOARD.read_text(encoding="utf-8")

    required = [
        "_render_opportunities_page",
        "_render_portfolio_allocation_page",
        "_render_discovery_page",
        "_render_strategy_page",
        "_render_data_health_section",
        "_render_drift_monitor_section",
        "_render_backtest_lab_section",
        "_render_modular_strategies_section",
        "_render_portfolio_builder_section",
    ]
    for fn in required:
        assert fn in source, f"Required function '{fn}' missing from dashboard.py"
    # Shadow Portfolio removed from live page
    assert "_render_shadow_portfolio_section" not in source



def test_shadow_portfolio_absent_from_portfolio_page() -> None:
    """Shadow Portfolio must not appear in the research portfolio page flow."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    page_source = source[start:next_def]
    assert "shadow" not in page_source.lower()
    assert "render_shadow_portfolio_view" not in source


def test_coverage_gap_warning_renders() -> None:
    """Coverage-gap note must appear when horizon starts before replay data."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    assert "input coverage starts" in fn_source
    assert "earlier dates are cash/input unavailable" in fn_source


def test_trade_event_log_uses_bundle_events_not_derivation() -> None:
    """Lifecycle visualization must use bundle event rows, not transition derivation."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    assert "_derive_replay_trade_events" not in fn_source
    assert "full_context.event_annotations" in fn_source
    assert "ENTER" in fn_source
    assert "EXIT" in fn_source
    assert "ADJUST" in fn_source
    assert "Trade Event Log" not in fn_source
    assert "_portfolio_horizon_start" in fn_source


def test_replay_source_mode_is_transitional() -> None:
    """DashboardReplayContext must label saved artifacts and transitional fallback explicitly."""
    source = DASHBOARD.read_text(encoding="utf-8")
    assert 'source_mode: str = "transitional_build"' in source
    assert '"saved_artifact"' in source
    assert "allow_transitional_fallback" in source
    # Transitional caption must render
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    assert "transitional build" in fn_source
    assert "saved artifact unavailable or stale" in fn_source
    assert "Replay source: saved artifact." in fn_source


def test_dash_2_replay_request_uses_explicit_selection_not_first_ten_fallback() -> None:
    """Replay identity must come from PortfolioReplaySelection, not hidden optimizer state."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _build_dashboard_replay_request(")
    next_def = source.index("\ndef _valid_cached_ytd_replay_context", start + 1)
    fn_source = source[start:next_def]

    assert "_current_portfolio_replay_selection(" in fn_source
    assert "portfolio_replay_selection_unavailable" in fn_source
    assert "optimizer_universe" not in fn_source
    assert "prices_wide.columns[:10]" not in fn_source


def test_buy_sell_decision_log_and_latest_trades_share_bundle_decisions() -> None:
    """Latest replay decision-code changes must be filtered from the same bundle decision rows."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_strategy_replay_section(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    assert "Replay Decision-Code Audit Log" in fn_source
    assert "Latest Replay Decision-Code Changes" in fn_source
    assert "full_context.buy_sell_decisions" in fn_source
    assert "pd.read_json" not in fn_source
    assert "LIFECYCLE_BUY_SELL_LOG_PATH" not in fn_source


def test_replay_timeline_uses_stacked_replay_targets() -> None:
    """Timeline visual should be a stacked allocation view of replay target_weight."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_replay_timeline_chart(")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]
    assert "stackgroup=\"weights\"" in fn_source
    assert "line=dict(shape=\"hv\"" in fn_source
    assert "Replay Target" in fn_source
    assert "lines+markers" not in fn_source


def test_replay_timeline_stacked_chart_traces_are_allocation_areas(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rendered replay timeline uses stacked step areas rather than marker-heavy lines."""
    import dashboard

    captured: dict[str, object] = {}
    monkeypatch.setattr(dashboard.st, "plotly_chart", lambda fig, **kwargs: captured.setdefault("fig", fig))

    replay_df = pd.DataFrame(
        {
            "date": [
                "2026-01-02",
                "2026-01-02",
                "2026-01-02",
                "2026-01-05",
                "2026-01-05",
                "2026-01-05",
            ],
            "ticker": ["AMAT", "LRCX", "CASH", "AMAT", "LRCX", "CASH"],
            "target_weight": [0.35, 0.30, 0.35, 0.0, 0.35, 0.65],
        }
    )

    dashboard._render_replay_timeline_chart(replay_df)

    fig = captured["fig"]
    assert [trace.name for trace in fig.data] == ["LRCX", "AMAT", "CASH"]
    assert {trace.stackgroup for trace in fig.data} == {"weights"}
    assert {trace.mode for trace in fig.data} == {"lines"}
    assert {trace.line.shape for trace in fig.data} == {"hv"}
    assert fig.data[-1].name == "CASH"
    assert fig.layout.yaxis.range == (0, 1)


def test_dash_2_portfolio_render_path_builds_one_daily_replay_context() -> None:
    """Portfolio page builds one daily context and passes it to all replay-facing surfaces."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    fn_source = source[start:next_def]

    assert fn_source.count("_ensure_daily_portfolio_replay_context(") == 1
    assert "_render_replay_allocation_snapshot(daily_replay_context)" in fn_source
    assert "_render_portfolio_ytd_chart(daily_replay_context" in fn_source
    assert "_render_strategy_replay_section(daily_replay_context)" in fn_source


def test_dash_2_portfolio_render_path_has_no_direct_second_source_reads() -> None:
    """Render orchestration must not read lifecycle JSONL or latest-trades caches directly."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_allocation_page()")
    next_def = source.index("\ndef ", start + 1)
    page_source = source[start:next_def]
    replay_start = source.index("def _render_strategy_replay_section(")
    replay_next = source.index("\ndef ", replay_start + 1)
    replay_source = source[replay_start:replay_next]
    snapshot_start = source.index("def _render_replay_allocation_snapshot(")
    snapshot_next = source.index("\ndef ", snapshot_start + 1)
    snapshot_source = source[snapshot_start:snapshot_next]
    render_path = "\n".join([page_source, replay_source, snapshot_source])

    forbidden = [
        "pd.read_json",
        "read_lifecycle_log",
        "LIFECYCLE_BUY_SELL_LOG_PATH",
        "portfolio_lifecycle_buy_sell_log",
        "latest_trades_cache",
    ]
    for token in forbidden:
        assert token not in render_path


def test_dash_2_weekly_sampling_is_display_only_from_daily_replay() -> None:
    """Timeline sampling must not create a second weekly replay request."""
    source = DASHBOARD.read_text(encoding="utf-8")
    request_start = source.index("def _build_dashboard_replay_request(")
    request_end = source.index("\ndef ", request_start + 1)
    request_source = source[request_start:request_end]
    sampler_start = source.index("def _sample_replay_timeline_from_daily(")
    sampler_end = source.index("\ndef ", sampler_start + 1)
    sampler_source = source[sampler_start:sampler_end]

    assert 'sampling="daily"' in request_source
    assert "weekly_idx" not in request_source
    assert "weekly_display_from_daily" in sampler_source
    assert "groupby([iso.year, iso.week])" in sampler_source


def test_dash_2_weekly_sampling_normalizes_grouped_dates_for_max_replay() -> None:
    """Regression: max-window replay must not call Series.normalize()."""
    import dashboard

    dates = pd.date_range("2025-01-02", periods=220, freq="B")
    replay_df = pd.DataFrame(
        {
            "date": dates,
            "ticker": "CASH",
            "target_weight": 1.0,
            "status": "cash_closed",
        }
    )

    sampled, sampling = dashboard._sample_replay_timeline_from_daily(replay_df)

    assert sampling == "weekly_display_from_daily"
    assert not sampled.empty
    assert pd.Timestamp(sampled["date"].max()).normalize() == pd.Timestamp(dates[-1]).normalize()
    assert len(sampled["date"].dt.normalize().unique()) < len(dates)
