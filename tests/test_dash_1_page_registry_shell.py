from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from core.gv_e0a_operable import publish_e0a_current_decision
from core.gv_fs0_publish import (
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
)
from views.page_registry import (
    APPROVED_PAGE_TITLES,
    DISCOVERY_PAGE_TITLE,
    LEGACY_PAGE_MOVEMENT,
    PAGE_GROUPS,
    PORTFOLIO_PAGE_ROUTE,
    PORTFOLIO_PAGE_TITLE,
    STRATEGY_PAGE_TITLE,
)


DASHBOARD = Path("dashboard.py")


def _app_dataframe_values(app: AppTest) -> list[pd.DataFrame]:
    frames: list[pd.DataFrame] = []
    for element in app.dataframe:
        value = element.value
        if isinstance(value, pd.DataFrame):
            frames.append(value)
            continue
        data = getattr(value, "data", None)
        if isinstance(data, pd.DataFrame):
            frames.append(data)
    return frames


def _app_status_text(app: AppTest) -> str:
    values: list[str] = []
    for group_name in ("info", "warning", "error"):
        for element in getattr(app, group_name):
            value = getattr(element, "value", "")
            if value:
                values.append(str(value))
    return "\n".join(values)


def test_dash_1_approved_pages_are_registered() -> None:
    assert APPROVED_PAGE_TITLES == (
        PORTFOLIO_PAGE_TITLE,
        DISCOVERY_PAGE_TITLE,
        STRATEGY_PAGE_TITLE,
    )

    grouped_pages = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped_pages == APPROVED_PAGE_TITLES


def test_dash_1_legacy_content_maps_to_approved_pages() -> None:
    assert LEGACY_PAGE_MOVEMENT["Opportunities"] == DISCOVERY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Data Health"] == PORTFOLIO_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Drift Monitor"] == PORTFOLIO_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Daily Scan"] == DISCOVERY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Backtest Lab"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Modular Strategies"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Portfolio Builder"] == PORTFOLIO_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Options Scenario Research"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Command Center"] == PORTFOLIO_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Entry & Hold Discipline"] == STRATEGY_PAGE_TITLE
    # Shadow Portfolio removed from live page; must not be in registry
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

    assert "PORTFOLIO_PAGE_TITLE: _render_portfolio_allocation_page" in source
    assert "DISCOVERY_PAGE_TITLE: _render_discovery_page" in source
    assert "STRATEGY_PAGE_TITLE: _render_strategy_page" in source


def test_dash_1_portfolio_route_has_explicit_default_path() -> None:
    source = Path("views/page_registry.py").read_text(encoding="utf-8")

    assert "title=PORTFOLIO_PAGE_TITLE" in source
    assert 'default=True' in source
    assert "url_path=PORTFOLIO_PAGE_ROUTE" in source
    assert "renderers[PORTFOLIO_PAGE_TITLE]" in source
    assert PORTFOLIO_PAGE_TITLE == "Certified Portfolio"
    assert PORTFOLIO_PAGE_ROUTE == "portfolio"


def test_dash_1_default_portfolio_route_renders_current_decision() -> None:
    prior_target = (
        DEFAULT_CURRENT_DECISION_TARGET.read_bytes()
        if DEFAULT_CURRENT_DECISION_TARGET.exists()
        else None
    )
    prior_lock = (
        DEFAULT_CURRENT_DECISION_LOCK.read_bytes()
        if DEFAULT_CURRENT_DECISION_LOCK.exists()
        else None
    )
    try:
        if DEFAULT_CURRENT_DECISION_LOCK.exists():
            DEFAULT_CURRENT_DECISION_LOCK.unlink()
        publish_e0a_current_decision()
        app = AppTest.from_file("dashboard.py")
        app.query_params["page"] = PORTFOLIO_PAGE_ROUTE
        app = app.run(timeout=90)

        assert not app.exception
        assert any(header.value == PORTFOLIO_PAGE_TITLE for header in app.header)
        subheaders = [element.value for element in app.subheader]
        assert "GV-FS0 Certified Paper Portfolio — NO_POSITION" in subheaders
        assert len(app.table) >= 1
        caption_text = "\n".join(element.value for element in app.caption)
        assert caption_text.count("CERTIFIED") >= 1
        assert "Replay selection unavailable" not in _app_status_text(app)
        if "GV-E0B-DV1 Decision Delta — G08 Contradiction Case" in subheaders:
            assert "observed-comparison count = 0" in caption_text
    finally:
        if prior_target is None:
            DEFAULT_CURRENT_DECISION_TARGET.unlink(missing_ok=True)
        else:
            DEFAULT_CURRENT_DECISION_TARGET.write_bytes(prior_target)
        if prior_lock is None:
            DEFAULT_CURRENT_DECISION_LOCK.unlink(missing_ok=True)
        else:
            DEFAULT_CURRENT_DECISION_LOCK.write_bytes(prior_lock)


def test_dash_1_legacy_portfolio_sections_are_not_default_authority() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_render_portfolio_allocation_page"
    )
    body = ast.unparse(function)

    assert "render_gv_fs0_current_decision(st)" in body
    assert "render_gv_fs0_certified_bundle(st)" not in body
    for forbidden in (
        "_render_portfolio_builder_section",
        "_ensure_daily_portfolio_replay_context",
        "_render_replay_allocation_snapshot",
        "_render_portfolio_ytd_chart",
        "_render_strategy_replay_section",
        "_render_data_health_section",
        "_render_drift_monitor_section",
    ):
        assert forbidden not in body
    assert "_render_backtest_lab_section()" in source
    assert "_render_modular_strategies_section()" in source


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
