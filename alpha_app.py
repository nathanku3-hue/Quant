"""Broker-free Alpha product entrypoint (GV-ALPHA0-CLOSE Case Workspace).

No dashboard, no broker client, no trading-SDK import path.
Launch via: python launch_alpha.py
"""

from __future__ import annotations

import streamlit as st

from views.gv_alpha0_case_workspace import (
    GvAlpha0CaseWorkspaceError,
    render_case_workspace,
)

st.set_page_config(
    page_title="GV-ALPHA0 Case Workspace",
    page_icon="α",
    layout="wide",
)

st.sidebar.markdown("**GV-ALPHA0**")
st.sidebar.caption(
    "Broker-free Alpha surface. No APCA/ALPACA env required. "
    "Publish/truth/tag gated post dogfood."
)

try:
    # Product path always verifies seal from raw before any confirm action.
    render_case_workspace(st, verify=True)
except GvAlpha0CaseWorkspaceError:
    # Error already rendered inside workspace; keep page alive.
    pass
