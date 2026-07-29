"""GV Portfolio V0 broker-free Streamlit entrypoint."""

from __future__ import annotations

import streamlit as st

from gv_portfolio_v0.storage import default_workspace_root
from gv_portfolio_v0.vertical import PortfolioV0Error
from views.gv_portfolio_v0_workspace import render_portfolio_workspace

st.set_page_config(
    page_title="GV Micro-Portfolio V0",
    page_icon="P",
    layout="wide",
)

st.sidebar.markdown("**GV Portfolio V0**")
st.sidebar.caption(
    "Local deterministic paper portfolio. No provider, network, broker, or live-capital path."
)
workspace_root = default_workspace_root()
st.sidebar.caption(f"Workspace: `{workspace_root}`")

try:
    render_portfolio_workspace(st, root=workspace_root)
except PortfolioV0Error:
    pass
