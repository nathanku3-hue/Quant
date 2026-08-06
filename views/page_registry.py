from __future__ import annotations

from collections.abc import Callable, Mapping

import streamlit as st


COMMAND_CENTER_PAGE_TITLE = "Command Center"
COMMAND_CENTER_PAGE_ROUTE = "command-center"
DECISIONS_THESIS_PAGE_TITLE = "Decisions & Thesis"
DECISIONS_THESIS_PAGE_ROUTE = "decisions-and-thesis"
OPERATIONS_REPLAY_PAGE_TITLE = "Operations & Replay"
OPERATIONS_REPLAY_PAGE_ROUTE = "operations-and-replay"

APPROVED_PAGE_TITLES: tuple[str, ...] = (
    COMMAND_CENTER_PAGE_TITLE,
    DECISIONS_THESIS_PAGE_TITLE,
    OPERATIONS_REPLAY_PAGE_TITLE,
)

PAGE_GROUPS: Mapping[str, tuple[str, ...]] = {
    "GodView": APPROVED_PAGE_TITLES,
}

_PAGE_ROUTES: Mapping[str, str] = {
    COMMAND_CENTER_PAGE_TITLE: COMMAND_CENTER_PAGE_ROUTE,
    DECISIONS_THESIS_PAGE_TITLE: DECISIONS_THESIS_PAGE_ROUTE,
    OPERATIONS_REPLAY_PAGE_TITLE: OPERATIONS_REPLAY_PAGE_ROUTE,
}


def build_dashboard_navigation(
    renderers: Mapping[str, Callable[[], None]],
):
    missing_pages = [title for title in APPROVED_PAGE_TITLES if title not in renderers]
    if missing_pages:
        raise ValueError(f"Missing dashboard renderers: {', '.join(missing_pages)}")
    extra_pages = [title for title in renderers if title not in APPROVED_PAGE_TITLES]
    if extra_pages:
        raise ValueError(f"Unapproved dashboard renderers: {', '.join(extra_pages)}")

    requested_route = str(st.query_params.get("page", "")).strip()
    requested_title = next(
        (title for title, route in _PAGE_ROUTES.items() if route == requested_route),
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
