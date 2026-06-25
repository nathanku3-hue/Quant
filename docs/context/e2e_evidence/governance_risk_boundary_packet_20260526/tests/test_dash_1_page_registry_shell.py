from __future__ import annotations

from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from views.page_registry import APPROVED_PAGE_TITLES, LEGACY_PAGE_MOVEMENT, PAGE_GROUPS


DASHBOARD = Path("dashboard.py")


def test_dash_1_approved_pages_are_registered() -> None:
    assert APPROVED_PAGE_TITLES == (
        "Portfolio & Allocation",
        "Discovery & Analysis",
        "Entry/Exit Strategy",
    )

    grouped_pages = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped_pages == APPROVED_PAGE_TITLES


def test_dash_1_legacy_content_maps_to_approved_pages() -> None:
    assert LEGACY_PAGE_MOVEMENT["Opportunities"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Data Health"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Drift Monitor"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Daily Scan"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Backtest Lab"] == "Entry/Exit Strategy"
    assert LEGACY_PAGE_MOVEMENT["Modular Strategies"] == "Entry/Exit Strategy"
    assert LEGACY_PAGE_MOVEMENT["Portfolio Builder"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Hedge Harvester"] == "Entry/Exit Strategy"
    assert LEGACY_PAGE_MOVEMENT["Command Center"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Entry & Hold Discipline"] == "Entry/Exit Strategy"
    # Shadow Portfolio removed from live page — must not be in registry
    assert "Shadow Portfolio" not in LEGACY_PAGE_MOVEMENT


def test_dash_1_uses_page_registry_not_flat_tabs() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "build_dashboard_navigation(" in source
    assert "page.run()" in source
    assert "st.tabs(" not in source


def test_dash_1_old_tabs_are_not_top_level_navigation_labels() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    navigation_start = source.index("page = build_dashboard_navigation(")
    navigation_source = source[navigation_start:]

    forbidden_top_level = [
        "Ticker Pool & Proxies",
        "Data Health",
        "Drift Monitor",
        "Daily Scan",
        "Backtest Lab",
        "Modular Strategies",
        "Portfolio Builder",
        "Shadow Portfolio",
        "Hedge Harvester",
        "Command Center",
        "Research Lab",
        "Settings & Ops",
    ]
    for label in forbidden_top_level:
        assert label not in navigation_source


def test_dash_1_three_page_renderers_wired() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")

    assert '"Portfolio & Allocation": _render_portfolio_allocation_page' in source
    assert '"Discovery & Analysis": _render_discovery_page' in source
    assert '"Entry/Exit Strategy": _render_strategy_page' in source


def test_dash_1_portfolio_route_has_explicit_default_path() -> None:
    source = Path("views/page_registry.py").read_text(encoding="utf-8")

    assert 'title="Portfolio & Allocation"' in source
    assert 'default=True' in source
    assert 'url_path=_url_path("Portfolio & Allocation")' in source
    assert 'renderers["Portfolio & Allocation"]' in source


def test_dash_1_portfolio_allocation_route_renders_without_overlay() -> None:
    app = AppTest.from_file("dashboard.py")
    app.query_params["page"] = "portfolio-and-allocation"
    app = app.run(timeout=90)

    assert not app.exception
    assert any(header.value == "Portfolio & Allocation" for header in app.header)
    dataframe_values = [
        element.value
        for element in app.dataframe
        if isinstance(element.value, pd.DataFrame)
    ]
    assert any(
        {"Ticker", "Replay Weight", "Context Role"}.issubset(frame.columns)
        for frame in dataframe_values
    )
    assert any(
        {"Ticker", "Current Weight", "Context Role"}.issubset(frame.columns)
        for frame in dataframe_values
    )


def test_dash_1_legacy_sections_remain_reachable_inside_new_pages() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "_render_data_health_section()" in source
    assert "_render_drift_monitor_section()" in source
    assert "_render_backtest_lab_section()" in source
    assert "_render_modular_strategies_section()" in source
    assert "_render_portfolio_builder_section()" in source
    # Shadow Portfolio removed from live page — function no longer exists
    assert "_render_shadow_portfolio_section()" not in source
    assert "_render_opportunities_page()" in source or "_render_opportunities_page," in source
    assert "_render_daily_scan_section()" in source or "_render_daily_scan_section," in source


def test_dash_1_forbidden_runtime_scope_is_not_added() -> None:
    source = DASHBOARD.read_text(encoding="utf-8") + "\n" + Path("views/page_registry.py").read_text(encoding="utf-8")
    forbidden_tokens = [
        "submit_order",
        "buy_sell_hold",
        "factor_scout",
        "local_factor_scout",
        "phase34_factor_scores",
    ]
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered
