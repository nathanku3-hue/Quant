from __future__ import annotations

from collections.abc import Callable, Mapping

import streamlit as st


APPROVED_PAGE_TITLES: tuple[str, ...] = (
    "Command Center",
    "Opportunities",
    "Thesis Card",
    "Market Behavior",
    "Entry & Hold Discipline",
    "Portfolio & Allocation",
    "Research Lab",
    "Settings & Ops",
)

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "Operate": (
        "Command Center",
        "Opportunities",
        "Thesis Card",
        "Market Behavior",
        "Entry & Hold Discipline",
    ),
    "Portfolio": ("Portfolio & Allocation",),
    "Research": ("Research Lab",),
    "System": ("Settings & Ops",),
}

LEGACY_PAGE_MOVEMENT: Mapping[str, str] = {
    "Ticker Pool & Proxies": "Opportunities",
    "Data Health": "Settings & Ops",
    "Drift Monitor": "Settings & Ops",
    "Daily Scan": "Research Lab",
    "Backtest Lab": "Research Lab",
    "Modular Strategies": "Research Lab",
    "Portfolio Builder": "Portfolio & Allocation",
    "Shadow Portfolio": "Portfolio & Allocation",
    "Hedge Harvester": "Research Lab",
}


def _url_path(title: str) -> str:
    return title.lower().replace("&", "and").replace(" ", "-")


def build_dashboard_navigation(
    renderers: Mapping[str, Callable[[], None]],
):
    missing_pages = [title for title in APPROVED_PAGE_TITLES if title not in renderers]
    if missing_pages:
        raise ValueError(f"Missing dashboard renderers: {', '.join(missing_pages)}")

    pages = {
        group: [
            st.Page(
                renderers[title],
                title=title,
                url_path=_url_path(title),
                default=title == "Command Center",
            )
            for title in titles
        ]
        for group, titles in PAGE_GROUPS.items()
    }
    return st.navigation(pages, position="sidebar", expanded=True)
