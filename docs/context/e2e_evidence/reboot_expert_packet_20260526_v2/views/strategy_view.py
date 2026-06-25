"""
Entry/Exit Strategy view.

Composes: Modular Strategies matrix + Backtest Lab.
Render functions remain in dashboard.py due to global state dependencies.
This module documents the composition contract for future extraction.
"""
from __future__ import annotations

import streamlit as st


def render_strategy_page(
    render_modular_strategies: callable,
    render_backtest_lab: callable,
) -> None:
    """Compose the Entry/Exit Strategy page from sub-renderers."""
    tab = st.radio(
        "",
        ["Strategy Matrix", "Backtest Lab"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if tab == "Strategy Matrix":
        render_modular_strategies()
    else:
        render_backtest_lab()
