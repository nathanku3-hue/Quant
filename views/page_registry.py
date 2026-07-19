from __future__ import annotations

from collections.abc import Callable, Mapping

import streamlit as st


PORTFOLIO_PAGE_TITLE = "Certified Portfolio"
PORTFOLIO_PAGE_ROUTE = "portfolio"
DISCOVERY_PAGE_TITLE = "Discovery & Analysis"
STRATEGY_PAGE_TITLE = "Strategy Research Replay"

APPROVED_PAGE_TITLES: tuple[str, ...] = (
    PORTFOLIO_PAGE_TITLE,
    DISCOVERY_PAGE_TITLE,
    STRATEGY_PAGE_TITLE,
)

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "Views": (
        PORTFOLIO_PAGE_TITLE,
        DISCOVERY_PAGE_TITLE,
        STRATEGY_PAGE_TITLE,
    ),
}

LEGACY_PAGE_MOVEMENT: Mapping[str, str] = {
    "Command Center": PORTFOLIO_PAGE_TITLE,
    "Ticker Pool & Proxies": DISCOVERY_PAGE_TITLE,
    "Opportunities": DISCOVERY_PAGE_TITLE,
    "Thesis Card": DISCOVERY_PAGE_TITLE,
    "Market Behavior": DISCOVERY_PAGE_TITLE,
    "Data Health": PORTFOLIO_PAGE_TITLE,
    "Drift Monitor": PORTFOLIO_PAGE_TITLE,
    "Daily Scan": DISCOVERY_PAGE_TITLE,
    "Backtest Lab": STRATEGY_PAGE_TITLE,
    "Modular Strategies": STRATEGY_PAGE_TITLE,
    "Portfolio Builder": PORTFOLIO_PAGE_TITLE,

    "Options Scenario Research": STRATEGY_PAGE_TITLE,
    "Entry & Hold Discipline": STRATEGY_PAGE_TITLE,
    "Research Lab": STRATEGY_PAGE_TITLE,
    "Settings & Ops": PORTFOLIO_PAGE_TITLE,
}


def _url_path(title: str) -> str:
    return title.lower().replace("&", "and").replace("/", "-").replace(" ", "-")


def build_dashboard_navigation(
    renderers: Mapping[str, Callable[[], None]],
):
    missing_pages = [title for title in APPROVED_PAGE_TITLES if title not in renderers]
    if missing_pages:
        raise ValueError(f"Missing dashboard renderers: {', '.join(missing_pages)}")

    pages = [
        st.Page(
            renderers[PORTFOLIO_PAGE_TITLE],
            title=PORTFOLIO_PAGE_TITLE,
            url_path=PORTFOLIO_PAGE_ROUTE,
            default=True,
        ),
        *[
            st.Page(
                renderers[title],
                title=title,
                url_path=_url_path(title),
                default=False,
            )
            for title in APPROVED_PAGE_TITLES
            if title != PORTFOLIO_PAGE_TITLE
        ],
    ]
    return st.navigation(pages, position="sidebar", expanded=True)
