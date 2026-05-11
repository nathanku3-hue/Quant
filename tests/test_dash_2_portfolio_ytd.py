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


DASHBOARD = Path("dashboard.py")


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
    assert "def _render_portfolio_ytd_chart()" in source


def test_dash_2_ytd_chart_wired_into_portfolio_page() -> None:
    """YTD chart is called from _render_portfolio_builder_section."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_section()")
    # Find the next function definition after this one
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "_render_portfolio_ytd_chart()" in section_source


def test_dash_2_ytd_chart_renders_spy_and_qqq_benchmarks() -> None:
    """YTD chart includes SPY and QQQ benchmark traces."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_ytd_chart()")
    next_def = source.index("\ndef ", start + 1)
    chart_source = source[start:next_def]

    assert '"SPY"' in chart_source
    assert '"QQQ"' in chart_source
    assert "_download_ytd_close_prices" in chart_source
    assert "plotly_dark" in chart_source


def test_dash_2_ytd_chart_handles_empty_data_gracefully() -> None:
    """YTD chart has fallback when no data available."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_ytd_chart()")
    next_def = source.index("\ndef ", start + 1)
    chart_source = source[start:next_def]

    # Must have a guard for empty data
    assert "portfolio_equity is None" in chart_source
    assert "benchmark_equity" in chart_source


# ── Optimizer Ordering and Return Logic ───────────────────────────────────


def test_dash_2_optimizer_renders_before_ytd_chart() -> None:
    """Optimizer is rendered top-level before the YTD comparison."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_section()")
    next_def = source.index("\ndef ", start + 1)
    section_source = source[start:next_def]

    assert "render_optimizer_view(" in section_source
    assert "_render_portfolio_ytd_chart()" in section_source
    assert section_source.index("render_optimizer_view(") < section_source.index("_render_portfolio_ytd_chart()")
    assert "st.expander(" not in section_source


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


def test_dash_2_placeholder_is_not_toggled() -> None:
    """Placeholder fallback is visible directly when optimizer dependencies are missing."""
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_portfolio_builder_placeholder()")
    next_def = source.index("\ndef ", start + 1)
    placeholder_source = source[start:next_def]

    assert "st.expander(" not in placeholder_source
    # Must NOT have the old 3-column preview
    assert "preview_cols" not in placeholder_source


def test_dash_2_portfolio_return_uses_optimizer_weights() -> None:
    """Portfolio YTD return is based on optimizer weights when available."""
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "def _current_optimizer_weights()" in source
    assert "def _build_portfolio_ytd_equity(" in source
    assert "optimizer_weights" in source
    assert "_weighted_equity_curve(" in source


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
    assert "pd.Timestamp(latest_local).normalize() - pd.Timedelta(days=10)" in orchestrator_source


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
    start = source.index("def _render_research_lab_page()")
    next_def = source.index("\ndef ", start + 1)
    research_source = source[start:next_def]

    assert "Hedge Harvester" not in research_source
    assert "_render_hedge_harvester_section" not in research_source


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
        "_render_research_lab_page",
        "_render_settings_ops_page",
        "_render_data_health_section",
        "_render_drift_monitor_section",
        "_render_backtest_lab_section",
        "_render_modular_strategies_section",
        "_render_portfolio_builder_section",
        "_render_shadow_portfolio_section",
    ]
    for fn in required:
        assert fn in source, f"Required function '{fn}' missing from dashboard.py"
