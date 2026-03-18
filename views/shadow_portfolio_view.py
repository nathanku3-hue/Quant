from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from data.phase59_shadow_portfolio import DEFAULT_DELTA_PATH
from data.phase59_shadow_portfolio import DEFAULT_EVIDENCE_PATH
from data.phase59_shadow_portfolio import DEFAULT_SUMMARY_PATH
from data.phase59_shadow_portfolio import load_shadow_monitor_artifacts


def render_shadow_portfolio_view(
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    evidence_path: Path = DEFAULT_EVIDENCE_PATH,
    delta_path: Path = DEFAULT_DELTA_PATH,
) -> None:
    st.subheader("Shadow Portfolio")
    summary, evidence, delta = load_shadow_monitor_artifacts(
        summary_path=summary_path,
        evidence_path=evidence_path,
        delta_path=delta_path,
    )
    if summary is None or evidence.empty or delta.empty:
        st.info("No Phase 59 shadow monitor artifacts available yet.")
        return

    selected_variant = summary.get("selected_variant", {})
    reference = summary.get("shadow_reference", {})
    review_hold = bool(summary.get("review_hold", True))
    alert_level = str(reference.get("alert_level", "GREEN")).upper()
    status_line = (
        f"Reference alert: {alert_level} | "
        f"Review hold: {review_hold} | "
        f"Selected variant: {selected_variant.get('variant_id', 'N/A')}"
    )
    if alert_level == "RED":
        st.error(status_line)
    elif alert_level == "YELLOW":
        st.warning(status_line)
    else:
        st.success(status_line)

    st.caption(
        "Read-only Phase 59 surface built from allocator_state research data plus "
        "historical phase50_shadow_ship reference artifacts."
    )
    st.metric("Research Sharpe", _fmt_num(selected_variant.get("sharpe")))
    st.metric("Research CAGR", _fmt_pct(selected_variant.get("cagr")))
    st.metric("Holdings Overlap", _fmt_pct(reference.get("holdings_overlap")))
    st.metric("Gross Exposure Delta", _fmt_num(reference.get("gross_exposure_delta")))
    st.metric("Turnover Delta Rel", _fmt_pct(reference.get("turnover_delta_rel")))

    research = evidence.loc[evidence["surface_id"] == "phase59_shadow_research"].copy()
    reference_curve = evidence.loc[evidence["surface_id"] == "phase50_shadow_reference"].copy()
    fig = go.Figure()
    if not research.empty:
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(research["date"], errors="coerce"),
                y=pd.to_numeric(research["equity"], errors="coerce"),
                mode="lines",
                name="Phase59 Research Equity",
            )
        )
    if not reference_curve.empty:
        fig.add_trace(
            go.Scatter(
                x=pd.to_datetime(reference_curve["date"], errors="coerce"),
                y=pd.to_numeric(reference_curve["equity"], errors="coerce"),
                mode="lines",
                name="Phase50 Shadow Reference Equity",
            )
        )
    fig.update_layout(
        title="Shadow Research vs Reference Equity",
        xaxis_title="Date",
        yaxis_title="Equity",
    )
    st.plotly_chart(fig, use_container_width=True)

    alert_rows = pd.DataFrame(reference.get("alert_rows", []))
    if not alert_rows.empty:
        st.markdown("**Alert Contract**")
        st.dataframe(alert_rows, use_container_width=True, hide_index=True)

    delta_view = delta.copy()
    if "reference_only" in delta_view.columns:
        delta_view["reference_only"] = delta_view["reference_only"].fillna(False)
    st.markdown("**Comparator Snapshot**")
    st.dataframe(delta_view, use_container_width=True, hide_index=True)


def _fmt_num(value: object) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(num):
        return "N/A"
    return f"{num:.4f}"


def _fmt_pct(value: object) -> str:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if pd.isna(num):
        return "N/A"
    return f"{num:.2%}"
