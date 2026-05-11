from __future__ import annotations

from pathlib import Path

from views.page_registry import APPROVED_PAGE_TITLES, LEGACY_PAGE_MOVEMENT, PAGE_GROUPS


DASHBOARD = Path("dashboard.py")


def test_dash_1_approved_pages_are_registered() -> None:
    assert APPROVED_PAGE_TITLES == (
        "Command Center",
        "Opportunities",
        "Thesis Card",
        "Market Behavior",
        "Entry & Hold Discipline",
        "Portfolio & Allocation",
        "Research Lab",
        "Settings & Ops",
    )

    grouped_pages = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped_pages == APPROVED_PAGE_TITLES


def test_dash_1_legacy_content_maps_to_approved_pages() -> None:
    assert LEGACY_PAGE_MOVEMENT["Ticker Pool & Proxies"] == "Opportunities"
    assert LEGACY_PAGE_MOVEMENT["Data Health"] == "Settings & Ops"
    assert LEGACY_PAGE_MOVEMENT["Drift Monitor"] == "Settings & Ops"
    assert LEGACY_PAGE_MOVEMENT["Daily Scan"] == "Research Lab"
    assert LEGACY_PAGE_MOVEMENT["Backtest Lab"] == "Research Lab"
    assert LEGACY_PAGE_MOVEMENT["Modular Strategies"] == "Research Lab"
    assert LEGACY_PAGE_MOVEMENT["Portfolio Builder"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Shadow Portfolio"] == "Portfolio & Allocation"
    assert LEGACY_PAGE_MOVEMENT["Hedge Harvester"] == "Research Lab"


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
    ]
    for label in forbidden_top_level:
        assert label not in navigation_source


def test_dash_1_legacy_sections_remain_reachable_inside_new_pages() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")

    assert '"Opportunities": _render_opportunities_page' in source
    assert '"Portfolio & Allocation": _render_portfolio_allocation_page' in source
    assert '"Research Lab": _render_research_lab_page' in source
    assert '"Settings & Ops": _render_settings_ops_page' in source
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

    assert '_render_placeholder_page("Command Center")' in command_center_source
    assert "st.metric" not in command_center_source
    assert "get_active_alerts" not in command_center_source


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
