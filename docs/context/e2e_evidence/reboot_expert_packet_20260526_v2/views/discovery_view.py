"""
Discovery & Analysis view.

Composes: Opportunities table + Confluence Scan (daily scan).
Render functions remain in dashboard.py due to global state dependencies.
This module documents the composition contract for future extraction.
"""
from __future__ import annotations

import streamlit as st


def render_discovery_page(
    render_opportunities: callable,
    render_confluence_scan: callable,
) -> None:
    """Compose the Discovery & Analysis page from sub-renderers."""
    tab = st.radio(
        "",
        ["Opportunities", "Confluence Scan"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if tab == "Opportunities":
        render_opportunities()
    else:
        render_confluence_scan()
