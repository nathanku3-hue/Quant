from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def render_discovery_analysis_view(
    render_opportunities: Callable[[], None],
    render_data_health: Callable[[], None],
    render_drift_monitor: Callable[[], None],
) -> None:
    st.header("Discovery & Analysis")
    selected_section = st.radio(
        "Discovery workflow",
        ["Opportunities", "Data Health", "Drift Monitor"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_section == "Opportunities":
        render_opportunities()
    elif selected_section == "Data Health":
        render_data_health()
    else:
        render_drift_monitor()
