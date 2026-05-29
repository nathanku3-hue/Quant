from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def render_strategy_research_replay_view(
    render_daily_scan: Callable[[], None],
    render_backtest_lab: Callable[[], None],
    render_modular_strategies: Callable[[], None],
) -> None:
    st.header("Strategy Research Replay")
    selected_section = st.radio(
        "Strategy workflow",
        ["Modular Strategies", "Backtest Lab", "Daily Scan"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_section == "Modular Strategies":
        render_modular_strategies()
    elif selected_section == "Backtest Lab":
        render_backtest_lab()
    else:
        render_daily_scan()
