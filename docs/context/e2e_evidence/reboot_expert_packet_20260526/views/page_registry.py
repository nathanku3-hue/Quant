from __future__ import annotations

from collections.abc import Callable, Mapping

import streamlit as st


APPROVED_PAGE_TITLES: tuple[str, ...] = (
    "Portfolio & Allocation",
    "Discovery & Analysis",
    "Entry/Exit Strategy",
)

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "Views": (
        "Portfolio & Allocation",
        "Discovery & Analysis",
        "Entry/Exit Strategy",
    ),
}

LEGACY_PAGE_MOVEMENT: Mapping[str, str] = {
    "Command Center": "Portfolio & Allocation",
    "Ticker Pool & Proxies": "Discovery & Analysis",
    "Opportunities": "Discovery & Analysis",
    "Thesis Card": "Discovery & Analysis",
    "Market Behavior": "Discovery & Analysis",
    "Data Health": "Portfolio & Allocation",
    "Drift Monitor": "Portfolio & Allocation",
    "Daily Scan": "Discovery & Analysis",
    "Backtest Lab": "Entry/Exit Strategy",
    "Modular Strategies": "Entry/Exit Strategy",
    "Portfolio Builder": "Portfolio & Allocation",

    "Hedge Harvester": "Entry/Exit Strategy",
    "Entry & Hold Discipline": "Entry/Exit Strategy",
    "Research Lab": "Entry/Exit Strategy",
    "Settings & Ops": "Portfolio & Allocation",
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
            renderers["Portfolio & Allocation"],
            title="Portfolio & Allocation",
            url_path=_url_path("Portfolio & Allocation"),
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
            if title != "Portfolio & Allocation"
        ],
    ]
    return st.navigation(pages, position="sidebar", expanded=True)
