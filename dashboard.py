"""Terminal Zero / GodView canonical application shell.

AOV authority is intentionally hard-cut: this file imports only the current
Command Center, decision/thesis, and deterministic operations/replay surfaces.
Missing canonical authority must render unavailable or fail closed. Historical
runtime authorities are not imported into the application shell.
"""

from __future__ import annotations

import streamlit as st

from views.command_center import (
    render_command_center,
    render_decisions_and_thesis,
    render_operations_and_replay,
)
from views.page_registry import (
    COMMAND_CENTER_PAGE_TITLE,
    DECISIONS_THESIS_PAGE_TITLE,
    OPERATIONS_REPLAY_PAGE_TITLE,
    build_dashboard_navigation,
)


st.set_page_config(page_title="Terminal Zero GodView", layout="wide", page_icon="🎯")


def _render_command_center() -> None:
    render_command_center(st)


def _render_decisions_thesis() -> None:
    render_decisions_and_thesis(st)


def _render_operations_replay() -> None:
    render_operations_and_replay(st)


page = build_dashboard_navigation(
    {
        COMMAND_CENTER_PAGE_TITLE: _render_command_center,
        DECISIONS_THESIS_PAGE_TITLE: _render_decisions_thesis,
        OPERATIONS_REPLAY_PAGE_TITLE: _render_operations_replay,
    }
)
page.run()
