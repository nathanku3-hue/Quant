from __future__ import annotations

from pathlib import Path

import pytest

from views.page_registry import APPROVED_PAGE_SLUGS
from views.page_registry import APPROVED_PAGE_TITLES
from views.page_registry import DISCOVERY_ANALYSIS_TITLE
from views.page_registry import LEGACY_PAGE_MOVEMENT
from views.page_registry import PAGE_GROUPS
from views.page_registry import PAGE_ROUTE_CONTRACT
from views.page_registry import PORTFOLIO_ALLOCATION_TITLE
from views.page_registry import STRATEGY_RESEARCH_REPLAY_TITLE
from views.page_registry import build_dashboard_navigation


DASHBOARD = Path("dashboard.py")


def test_dash_1_approved_pages_are_registered() -> None:
    assert APPROVED_PAGE_TITLES == (
        "Portfolio & Allocation",
        "Discovery & Analysis",
        "Strategy Research Replay",
    )
    assert PORTFOLIO_ALLOCATION_TITLE == "Portfolio & Allocation"
    assert DISCOVERY_ANALYSIS_TITLE == "Discovery & Analysis"
    assert STRATEGY_RESEARCH_REPLAY_TITLE == "Strategy Research Replay"
    assert APPROVED_PAGE_SLUGS == (
        "portfolio-and-allocation",
        "discovery-and-analysis",
        "strategy-research-replay",
    )
    assert tuple(route.default for route in PAGE_ROUTE_CONTRACT) == (True, False, False)

    grouped_pages = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped_pages == APPROVED_PAGE_TITLES


def test_dash_1_legacy_content_maps_to_approved_pages() -> None:
    assert LEGACY_PAGE_MOVEMENT["Command Center"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Opportunities"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Thesis Card"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Market Behavior"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Entry & Hold Discipline"] == "Strategy Research Replay"
    assert LEGACY_PAGE_MOVEMENT["Ticker Pool & Proxies"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Data Health"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Drift Monitor"] == "Discovery & Analysis"
    assert LEGACY_PAGE_MOVEMENT["Daily Scan"] == "Strategy Research Replay"
    assert LEGACY_PAGE_MOVEMENT["Backtest Lab"] == "Strategy Research Replay"
    assert LEGACY_PAGE_MOVEMENT["Modular Strategies"] == "Strategy Research Replay"
    assert LEGACY_PAGE_MOVEMENT["Portfolio Builder"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Shadow Portfolio"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Hedge Harvester"] == "Strategy Research Replay"


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
        "Command Center",
        "Opportunities",
        "Thesis Card",
        "Market Behavior",
        "Entry & Hold Discipline",
        "Research Lab",
        "Settings & Ops",
        "Ticker Pool & Proxies",
        "Data Health",
        "Drift Monitor",
        "Daily Scan",
        "Backtest Lab",
        "Modular Strategies",
        "Portfolio Builder",
        "Shadow Portfolio",
        "Hedge Harvester",
    ]
    for label in forbidden_top_level:
        assert label not in navigation_source


def test_dash_1_legacy_sections_remain_reachable_inside_new_pages() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")

    assert "PORTFOLIO_ALLOCATION_TITLE: _render_portfolio_allocation_page" in source
    assert "DISCOVERY_ANALYSIS_TITLE: _render_discovery_analysis_page" in source
    assert "STRATEGY_RESEARCH_REPLAY_TITLE: _render_strategy_research_replay_page" in source
    assert "_render_data_health_section()" in source
    assert "_render_drift_monitor_section()" in source
    assert "_render_backtest_lab_section()" in source
    assert "_render_modular_strategies_section()" in source
    assert "_render_portfolio_builder_section()" in source
    assert "_render_shadow_portfolio_section()" in source


def test_dash_1_command_center_is_placeholder_only_until_dash_2() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    start = source.index("def _render_command_center_page()")
    end = source.index("\ndef _render_placeholder_page", start)
    command_center_source = source[start:end]

    assert "_render_portfolio_allocation_page()" in command_center_source
    assert "st.metric" not in command_center_source
    assert "get_active_alerts" not in command_center_source


def test_dash_1_missing_renderer_fails_closed() -> None:
    renderers = {
        "Portfolio & Allocation": lambda: None,
        "Discovery & Analysis": lambda: None,
    }

    with pytest.raises(ValueError, match="Strategy Research Replay"):
        build_dashboard_navigation(renderers)


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
