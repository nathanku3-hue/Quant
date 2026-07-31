"""Broker-free Streamlit entrypoint for GV Operated Portfolio 10."""

from __future__ import annotations

import streamlit as st

from gv_portfolio_v0.operated import OperatedPortfolioError
from gv_portfolio_v0.operated_storage import default_workspace_root
from views.gv_operated_portfolio_workspace import render_operated_portfolio_workspace

st.set_page_config(
    page_title="GV Operated Portfolio 10",
    page_icon="P",
    layout="wide",
)

st.sidebar.markdown("**GV Operated Portfolio 10**")
st.sidebar.caption(
    "Local deterministic paper portfolio. No provider, network, broker, or live-capital path."
)
workspace_root = default_workspace_root()
st.sidebar.caption(f"Workspace: `{workspace_root}`")

try:
    render_operated_portfolio_workspace(st, root=workspace_root)
except OperatedPortfolioError:
    pass
