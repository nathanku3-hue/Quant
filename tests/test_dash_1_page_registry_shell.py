from __future__ import annotations

import ast
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.gv_e0a_operable import publish_e0a_current_decision
from core.gv_fs0_publish import (
    DEFAULT_CURRENT_DECISION_LOCK,
    DEFAULT_CURRENT_DECISION_TARGET,
)
from views.page_registry import (
    APPROVED_PAGE_TITLES,
    COMMAND_CENTER_PAGE_ROUTE,
    COMMAND_CENTER_PAGE_TITLE,
    DECISIONS_THESIS_PAGE_TITLE,
    DISCOVERY_PAGE_TITLE,
    LEGACY_PAGE_MOVEMENT,
    OPERATIONS_REPLAY_PAGE_TITLE,
    PAGE_GROUPS,
    PORTFOLIO_PAGE_ROUTE,
    PORTFOLIO_PAGE_TITLE,
    STRATEGY_PAGE_TITLE,
)


DASHBOARD = Path("dashboard.py")


def _app_status_text(app: AppTest) -> str:
    values: list[str] = []
    for group_name in ("info", "warning", "error"):
        for element in getattr(app, group_name):
            value = getattr(element, "value", "")
            if value:
                values.append(str(value))
    return "\n".join(values)


def test_dash_1_approved_pages_are_registered_in_frozen_order() -> None:
    assert APPROVED_PAGE_TITLES == (
        COMMAND_CENTER_PAGE_TITLE,
        DISCOVERY_PAGE_TITLE,
        DECISIONS_THESIS_PAGE_TITLE,
        PORTFOLIO_PAGE_TITLE,
        STRATEGY_PAGE_TITLE,
        OPERATIONS_REPLAY_PAGE_TITLE,
    )
    grouped_pages = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped_pages == APPROVED_PAGE_TITLES


def test_dash_1_legacy_content_maps_to_final_pages() -> None:
    assert LEGACY_PAGE_MOVEMENT["Command Center"] == COMMAND_CENTER_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Opportunities"] == DISCOVERY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Thesis Card"] == DECISIONS_THESIS_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Data Health"] == OPERATIONS_REPLAY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Drift Monitor"] == OPERATIONS_REPLAY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Daily Scan"] == DISCOVERY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Backtest Lab"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Modular Strategies"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Portfolio Builder"] == PORTFOLIO_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Options Scenario Research"] == STRATEGY_PAGE_TITLE
    assert LEGACY_PAGE_MOVEMENT["Entry & Hold Discipline"] == STRATEGY_PAGE_TITLE
    assert "Shadow Portfolio" not in LEGACY_PAGE_MOVEMENT


def test_dash_1_uses_page_registry_not_flat_tabs() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "build_dashboard_navigation(" in source
    assert "page.run()" in source
    assert "st.tabs(" not in source


def test_dash_1_old_tools_are_not_top_level_navigation_labels() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    navigation_start = source.index("page = build_dashboard_navigation(")
    navigation_source = source[navigation_start:]
    forbidden_top_level = (
        "Ticker Pool & Proxies",
        "Data Health",
        "Drift Monitor",
        "Daily Scan",
        "Backtest Lab",
        "Modular Strategies",
        "Portfolio Builder",
        "Shadow Portfolio",
        "Hedge Harvester",
        "Research Lab",
        "Settings & Ops",
    )
    for label in forbidden_top_level:
        assert label not in navigation_source


def test_dash_1_six_page_renderers_are_wired() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    expected = (
        "COMMAND_CENTER_PAGE_TITLE: _render_command_center_page",
        "DISCOVERY_PAGE_TITLE: _render_discovery_page",
        "DECISIONS_THESIS_PAGE_TITLE: _render_decisions_thesis_page",
        "PORTFOLIO_PAGE_TITLE: _render_portfolio_allocation_page",
        "STRATEGY_PAGE_TITLE: _render_strategy_page",
        "OPERATIONS_REPLAY_PAGE_TITLE: _render_settings_ops_page",
    )
    for binding in expected:
        assert binding in source


def test_dash_1_command_center_is_default_and_portfolio_route_is_preserved() -> None:
    assert APPROVED_PAGE_TITLES[0] == COMMAND_CENTER_PAGE_TITLE
    assert COMMAND_CENTER_PAGE_ROUTE == "command-center"
    assert PORTFOLIO_PAGE_ROUTE == "portfolio"
    source = Path("views/page_registry.py").read_text(encoding="utf-8")
    assert "COMMAND_CENTER_PAGE_TITLE" in source
    assert "requested_title" in source
    assert "default=title == requested_title" in source


def test_dash_1_default_route_renders_real_command_center() -> None:
    app = AppTest.from_file("dashboard.py").run(timeout=120)
    assert not app.exception, app.exception
    assert any(header.value == COMMAND_CENTER_PAGE_TITLE for header in app.header)

    identity_table = app.table[0].value
    proposal_table = app.table[1].value
    assert identity_table.loc[0, "market_context"] == (
        "NO_MARKET_DEPENDENCY_CASH_ONLY_V1"
    )
    assert set(proposal_table["module"]) == {
        "GV_REAL_MU_OPERATED",
        "GV_MU_NVDA_SHADOW",
        "GV_CERTIFIED_CASH_BASELINE",
    }
    assert any(metric.label == "Proposal rows" and metric.value == "3" for metric in app.metric)


def test_dash_1_legacy_portfolio_route_renders_current_decision() -> None:
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


def test_dash_1_portfolio_rotation_keeps_legacy_tools_non_authoritative() -> None:
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
    source = DASHBOARD.read_text(encoding="utf-8") + "\n" + Path(
        "views/page_registry.py"
    ).read_text(encoding="utf-8")
    forbidden_tokens = (
        "submit_order",
        "buy_sell_hold",
        "factor_scout",
        "local_factor_scout",
        "phase34_factor_scores",
    )
    lowered = source.lower()
    for token in forbidden_tokens:
        assert token not in lowered
