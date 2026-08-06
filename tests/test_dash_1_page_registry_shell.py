from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from views.page_registry import (
    APPROVED_PAGE_TITLES,
    COMMAND_CENTER_PAGE_ROUTE,
    COMMAND_CENTER_PAGE_TITLE,
    DECISIONS_THESIS_PAGE_ROUTE,
    DECISIONS_THESIS_PAGE_TITLE,
    OPERATIONS_REPLAY_PAGE_ROUTE,
    OPERATIONS_REPLAY_PAGE_TITLE,
    PAGE_GROUPS,
)


DASHBOARD = Path("dashboard.py")
ROOT_DUPLICATE_ENTRYPOINTS = (
    Path("alpha_app.py"),
    Path("launch_alpha.py"),
    Path("portfolio_app.py"),
    Path("launch_portfolio.py"),
)


def test_dashboard_has_only_three_canonical_pages() -> None:
    assert APPROVED_PAGE_TITLES == (
        COMMAND_CENTER_PAGE_TITLE,
        DECISIONS_THESIS_PAGE_TITLE,
        OPERATIONS_REPLAY_PAGE_TITLE,
    )
    grouped = tuple(page for pages in PAGE_GROUPS.values() for page in pages)
    assert grouped == APPROVED_PAGE_TITLES


def test_dashboard_routes_are_explicit_and_command_center_default() -> None:
    assert APPROVED_PAGE_TITLES[0] == COMMAND_CENTER_PAGE_TITLE
    assert COMMAND_CENTER_PAGE_ROUTE == "command-center"
    assert DECISIONS_THESIS_PAGE_ROUTE == "decisions-and-thesis"
    assert OPERATIONS_REPLAY_PAGE_ROUTE == "operations-and-replay"


def test_duplicate_root_product_entrypoints_are_absent() -> None:
    assert all(not path.exists() for path in ROOT_DUPLICATE_ENTRYPOINTS)
    assert Path("launch.py").is_file()
    assert DASHBOARD.is_file()


def test_dashboard_shell_has_no_legacy_authority_or_fallback_imports() -> None:
    source = DASHBOARD.read_text(encoding="utf-8")
    assert "build_dashboard_navigation(" in source
    assert "page.run()" in source
    forbidden = (
        "yfinance",
        "optimizer",
        "backtest",
        "macro_loader",
        "data_orchestrator",
        "strategy_replay",
        "legacy",
        "transitional",
        "fallback",
    )
    lowered = source.lower()
    for token in forbidden:
        # Documentation in the module docstring may state that a fallback is absent;
        # executable imports/calls must not carry the old authority.
        if token in {"legacy", "transitional", "fallback"}:
            continue
        assert token not in lowered
    assert "import yfinance" not in source
    assert "views.optimizer_view" not in source
    assert "render_auto_backtest_view" not in source
    assert "_selected_legacy_page_title" not in source
    assert "allow_transitional_fallback" not in source


def test_default_route_renders_real_command_center(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    app = AppTest.from_file("dashboard.py").run(timeout=120)
    assert not app.exception, app.exception
    assert any(header.value == COMMAND_CENTER_PAGE_TITLE for header in app.header)

    tables = [element.value for element in app.table]
    active_authority = next(
        table for table in tables if "certification_lineage_depth" in table.columns
    )
    identity_table = next(table for table in tables if "market_context" in table.columns)
    assert active_authority.loc[0, "scenario_id"] == "GV_PAIR_DECISION_SERIES_1_EPISODE_1"
    assert int(active_authority.loc[0, "sealed_series_episode_count"]) == 0
    assert int(active_authority.loc[0, "opened_outcome_episode_count"]) == 0
    assert active_authority.loc[0, "unexplained_residual"] == "0"
    assert identity_table.loc[0, "market_context"] == "NO_MARKET_DEPENDENCY_CASH_ONLY_V1"


def test_decisions_route_renders_canonical_evidence() -> None:
    app = AppTest.from_file("dashboard.py")
    app.query_params["page"] = DECISIONS_THESIS_PAGE_ROUTE
    app = app.run(timeout=60)
    assert not app.exception, app.exception
    assert any(header.value == DECISIONS_THESIS_PAGE_TITLE for header in app.header)
    table = app.table[0].value
    operated = table.loc[table["module"] == "GV_REAL_MU_OPERATED"].iloc[0]
    provenance = operated["supporting_evidence"]
    assert "MU_CLAIM_EVALUATION | sha256=" in provenance
    assert "NVDA_FACT_SET | sha256=" in provenance


def test_operations_route_is_deterministic_replay_only() -> None:
    app = AppTest.from_file("dashboard.py")
    app.query_params["page"] = OPERATIONS_REPLAY_PAGE_ROUTE
    app = app.run(timeout=60)
    assert not app.exception, app.exception
    assert any(header.value == OPERATIONS_REPLAY_PAGE_TITLE for header in app.header)
    assert app.table[0].value.loc[0, "event_count"] == 7
    lineage = app.table[1].value
    assert list(lineage["sequence"]) == list(range(7))
    assert lineage.loc[0, "type"] == "DECISION_EPISODE_OPENED"


def test_command_center_runtime_failure_is_fail_closed() -> None:
    app = AppTest.from_string(
        """
import streamlit as st
import views.command_center as command_center

def fail():
    raise RuntimeError("synthetic-runtime-failure")

original = command_center.build_command_center_read_model
try:
    command_center.build_command_center_read_model = fail
    command_center.render_command_center(st)
finally:
    command_center.build_command_center_read_model = original
"""
    ).run(timeout=30)
    assert not app.exception, app.exception
    assert any("authority unavailable" in element.value for element in app.error)
    assert "FAILED_CLOSED" in app.table[0].value.to_string()
    assert "synthetic-runtime-failure" in "\n".join(element.value for element in app.caption)
