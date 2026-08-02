"""Broker-free Streamlit entrypoint for the shared operated-portfolio product."""

from __future__ import annotations

import streamlit as st

from gv_portfolio_v0.operated import OperatedPortfolioError
from gv_portfolio_v0.operated_scenarios import get_scenario
from gv_portfolio_v0.operated_storage import (
    default_workspace_root,
    selected_scenario_id,
)
from views.gv_operated_portfolio_workspace import render_operated_portfolio_workspace
from views.gv_prospective_paper_workspace import render_prospective_paper_workspace

scenario_id = selected_scenario_id()
scenario = get_scenario(scenario_id)

st.set_page_config(
    page_title=scenario["title"],
    page_icon="P",
    layout="wide",
)

st.sidebar.markdown(f"**{scenario['title']}**")
st.sidebar.caption(
    "Local deterministic paper portfolio. No provider, network, broker, or live-capital path."
)
workspace_root = default_workspace_root(scenario_id=scenario_id)
st.sidebar.caption(f"Scenario: `{scenario_id}`")
st.sidebar.caption(f"Workspace: `{workspace_root}`")

try:
    if scenario.get("runtime_observation_mode") is True:
        render_prospective_paper_workspace(
            st, root=workspace_root, scenario_id=scenario_id
        )
    else:
        render_operated_portfolio_workspace(
            st, root=workspace_root, scenario_id=scenario_id
        )
except OperatedPortfolioError:
    pass
