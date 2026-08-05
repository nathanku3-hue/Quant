from __future__ import annotations

from collections.abc import Callable, Mapping

import streamlit as st


COMMAND_CENTER_PAGE_TITLE = "Command Center"
COMMAND_CENTER_PAGE_ROUTE = "command-center"
DISCOVERY_PAGE_TITLE = "Discovery & Analysis"
DECISIONS_THESIS_PAGE_TITLE = "Decisions & Thesis"
PORTFOLIO_ROTATION_PAGE_TITLE = "Portfolio & Rotation"
PORTFOLIO_PAGE_TITLE = PORTFOLIO_ROTATION_PAGE_TITLE
PORTFOLIO_PAGE_ROUTE = "portfolio"
STRATEGY_MODULES_PAGE_TITLE = "Strategy Modules"
STRATEGY_PAGE_TITLE = STRATEGY_MODULES_PAGE_TITLE
OPERATIONS_REPLAY_PAGE_TITLE = "Operations & Replay"

APPROVED_PAGE_TITLES: tuple[str, ...] = (
    COMMAND_CENTER_PAGE_TITLE,
    DISCOVERY_PAGE_TITLE,
    DECISIONS_THESIS_PAGE_TITLE,
    PORTFOLIO_ROTATION_PAGE_TITLE,
    STRATEGY_MODULES_PAGE_TITLE,
    OPERATIONS_REPLAY_PAGE_TITLE,
)

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "GodView": APPROVED_PAGE_TITLES,
}

LEGACY_PAGE_MOVEMENT: Mapping[str, str] = {
    "Command Center": COMMAND_CENTER_PAGE_TITLE,
    "Ticker Pool & Proxies": DISCOVERY_PAGE_TITLE,
    "Opportunities": DISCOVERY_PAGE_TITLE,
    "Thesis Card": DECISIONS_THESIS_PAGE_TITLE,
    "Market Behavior": DISCOVERY_PAGE_TITLE,
    "Data Health": OPERATIONS_REPLAY_PAGE_TITLE,
    "Drift Monitor": OPERATIONS_REPLAY_PAGE_TITLE,
    "Daily Scan": DISCOVERY_PAGE_TITLE,
    "Backtest Lab": STRATEGY_MODULES_PAGE_TITLE,
    "Modular Strategies": STRATEGY_MODULES_PAGE_TITLE,
    "Portfolio Builder": PORTFOLIO_ROTATION_PAGE_TITLE,
    "Options Scenario Research": STRATEGY_MODULES_PAGE_TITLE,
    "Entry & Hold Discipline": STRATEGY_MODULES_PAGE_TITLE,
    "Research Lab": STRATEGY_MODULES_PAGE_TITLE,
    "Settings & Ops": OPERATIONS_REPLAY_PAGE_TITLE,
}

_PAGE_ROUTES: Mapping[str, str] = {
    COMMAND_CENTER_PAGE_TITLE: COMMAND_CENTER_PAGE_ROUTE,
    DISCOVERY_PAGE_TITLE: "discovery-and-analysis",
    DECISIONS_THESIS_PAGE_TITLE: "decisions-and-thesis",
    PORTFOLIO_ROTATION_PAGE_TITLE: PORTFOLIO_PAGE_ROUTE,
    STRATEGY_MODULES_PAGE_TITLE: "strategy-modules",
    OPERATIONS_REPLAY_PAGE_TITLE: "operations-and-replay",
}


def build_dashboard_navigation(
    renderers: Mapping[str, Callable[[], None]],
):
    missing_pages = [title for title in APPROVED_PAGE_TITLES if title not in renderers]
    if missing_pages:
        raise ValueError(f"Missing dashboard renderers: {', '.join(missing_pages)}")

    requested_route = str(st.query_params.get("page", "")).strip()
    requested_title = next(
        (
            title
            for title, route in _PAGE_ROUTES.items()
            if route == requested_route
        ),
        COMMAND_CENTER_PAGE_TITLE,
    )
    pages = [
        st.Page(
            renderers[title],
            title=title,
            url_path=_PAGE_ROUTES[title],
            default=title == requested_title,
        )
        for title in APPROVED_PAGE_TITLES
    ]
    return st.navigation(pages, position="sidebar", expanded=True)
