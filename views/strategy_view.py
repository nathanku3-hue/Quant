"""
Strategy Research Replay view.

Composes: Modular Strategies matrix + Backtest Lab + read-only evidence status.
Render functions remain in dashboard.py due to global state dependencies.
This module documents the composition contract for future extraction.
"""
from __future__ import annotations

from collections.abc import Callable

import streamlit as st


PEAD_EVIDENCE_STATUS_TAB = "PEAD Evidence Status"


def render_strategy_page(
    render_modular_strategies: Callable[[], None],
    render_backtest_lab: Callable[[], None],
    render_pead_validation_evidence: Callable[[], None] | None = None,
) -> None:
    """Compose the Strategy Research Replay page from sub-renderers."""
    tab_names = ["Strategy Matrix", "Backtest Lab"]
    if render_pead_validation_evidence is not None:
        tab_names.append(PEAD_EVIDENCE_STATUS_TAB)
    tab = st.radio(
        "",
        tab_names,
        horizontal=True,
        label_visibility="collapsed",
    )
    if tab == "Strategy Matrix":
        render_modular_strategies()
    elif tab == "Backtest Lab":
        render_backtest_lab()
    elif tab == PEAD_EVIDENCE_STATUS_TAB and render_pead_validation_evidence is not None:
        render_pead_validation_evidence()
