from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

import streamlit as st


@dataclass(frozen=True)
class PageRoute:
    title: str
    slug: str
    default: bool = False


PAGE_ROUTE_CONTRACT: tuple[PageRoute, ...] = (
    PageRoute("Portfolio & Allocation", "portfolio-and-allocation", default=True),
    PageRoute("Discovery & Analysis", "discovery-and-analysis"),
    PageRoute("Strategy Research Replay", "strategy-research-replay"),
)

APPROVED_PAGE_TITLES: tuple[str, ...] = tuple(route.title for route in PAGE_ROUTE_CONTRACT)
APPROVED_PAGE_SLUGS: tuple[str, ...] = tuple(route.slug for route in PAGE_ROUTE_CONTRACT)
PORTFOLIO_ALLOCATION_TITLE = PAGE_ROUTE_CONTRACT[0].title
DISCOVERY_ANALYSIS_TITLE = PAGE_ROUTE_CONTRACT[1].title
STRATEGY_RESEARCH_REPLAY_TITLE = PAGE_ROUTE_CONTRACT[2].title

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "Research Console": APPROVED_PAGE_TITLES,
}

LEGACY_PAGE_MOVEMENT: Mapping[str, str] = {
    "Command Center": "Portfolio & Allocation",
    "Opportunities": "Discovery & Analysis",
    "Thesis Card": "Discovery & Analysis",
    "Market Behavior": "Discovery & Analysis",
    "Entry & Hold Discipline": "Strategy Research Replay",
    "Research Lab": "Strategy Research Replay",
    "Settings & Ops": "Discovery & Analysis",
    "Ticker Pool & Proxies": "Discovery & Analysis",
    "Data Health": "Discovery & Analysis",
    "Drift Monitor": "Discovery & Analysis",
    "Daily Scan": "Strategy Research Replay",
    "Backtest Lab": "Strategy Research Replay",
    "Modular Strategies": "Strategy Research Replay",
    "Portfolio Builder": "Portfolio & Allocation",
    "Shadow Portfolio": "Portfolio & Allocation",
    "Hedge Harvester": "Strategy Research Replay",
}


def build_dashboard_navigation(
    renderers: Mapping[str, Callable[[], None]],
):
    missing_pages = [route.title for route in PAGE_ROUTE_CONTRACT if route.title not in renderers]
    if missing_pages:
        raise ValueError(f"Missing dashboard renderers: {', '.join(missing_pages)}")

    pages = {
        group: [
            st.Page(
                renderers[route.title],
                title=route.title,
                url_path=route.slug,
                default=route.default,
            )
            for route in PAGE_ROUTE_CONTRACT
            if route.title in titles
        ]
        for group, titles in PAGE_GROUPS.items()
    }
    return st.navigation(pages, position="sidebar", expanded=True)
