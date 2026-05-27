from __future__ import annotations

import math
from typing import Any

import pandas as pd


ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS = frozenset(
    {
        "Rating",
        "Entry_Price",
        "Stop_Loss",
        "Target_Price",
        "Score",
        "Leverage",
        "Tactical_Warning",
    }
)

RESEARCH_STATE_ORDER = {
    "Setup evidence review": 1,
    "Evidence gap review": 2,
    "Risk review only": 3,
    "Insufficient evidence": 4,
    "Unclassified research state": 5,
}


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return float(parsed)


def _raw_rating_to_research_state(value: Any) -> str:
    rating = str(value or "").upper()
    if "ENTER:" in rating or "STRONG BUY" in rating:
        return "Setup evidence review"
    if "WATCH" in rating or "HOLD" in rating or "WAIT" in rating:
        return "Evidence gap review"
    if "EXIT" in rating or "KILL" in rating or "AVOID" in rating:
        return "Risk review only"
    if "IGNORE" in rating:
        return "Insufficient evidence"
    return "Unclassified research state"


def _research_state_order(value: Any) -> int:
    return RESEARCH_STATE_ORDER.get(str(value), max(RESEARCH_STATE_ORDER.values()) + 1)


def _format_price(value: Any) -> str:
    price = _coerce_float(value)
    if price <= 0:
        return "N/A"
    return f"${price:.2f}"


def _format_support_reference(row: pd.Series) -> str:
    support = _coerce_float(row.get("Entry_Price"))
    if support <= 0:
        return "N/A"
    flush = _coerce_float(row.get("Max_Flush"))
    premium = _coerce_float(row.get("Premium"))
    return f"${support:.2f} (support ref; flush -{flush * 100:.0f}%; premium +{premium * 100:.0f}%)"


def _risk_context_from_warning(value: Any) -> str:
    warning = str(value or "").upper()
    if not warning or warning == "N/A":
        return "No technical risk context"
    if "PARABOLIC" in warning:
        return "Extension risk review"
    if "LINEAR TREND" in warning:
        return "Trend context observed"
    if "SUPER CYCLE" in warning:
        return "Research trend context"
    return "Technical context review"


def _column(frame: pd.DataFrame, name: str, default: Any = "") -> pd.Series:
    if name in frame.columns:
        return frame[name]
    return pd.Series([default] * len(frame), index=frame.index)


def build_scanner_research_display_frame(df_scan: pd.DataFrame, *, time_label: str) -> pd.DataFrame:
    """Build the research-only scanner table shown in Streamlit."""
    source = df_scan.copy()
    proxy_content_col = f"Proxy_Content (Updated: {time_label})" if time_label else "Proxy_Content"

    view_df = pd.DataFrame(index=source.index)
    view_df["Ticker"] = _column(source, "Ticker").astype(str)
    view_df["Research_State"] = _column(source, "Rating").map(_raw_rating_to_research_state)
    view_df["Research_Cluster"] = _column(source, "Cluster").astype(str)
    view_df["Current_Price"] = _column(source, "Current_Price").map(_format_price)
    view_df["Support_Reference"] = source.apply(_format_support_reference, axis=1)
    view_df["Research_Risk_Context"] = _column(source, "Tactical_Warning").map(_risk_context_from_warning)
    view_df["Proxy_Type"] = _column(source, "Proxy_Type").astype(str)
    view_df["P_Value"] = _column(source, "P_Value").astype(str)
    view_df[proxy_content_col] = _column(source, "Proxy_Content").astype(str)
    view_df["Proxy_Signal"] = _column(source, "Proxy_Signal").astype(str)

    view_df["_ResearchDisplayOrder"] = view_df["Research_State"].map(_research_state_order)
    view_df = view_df.sort_values(["_ResearchDisplayOrder", "Ticker"], kind="stable")
    view_df = view_df.drop(columns=["_ResearchDisplayOrder"]).reset_index(drop=True)

    leaked = ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS.intersection(view_df.columns)
    if leaked:
        raise ValueError(f"action-shaped scanner columns leaked into display frame: {sorted(leaked)}")
    return view_df


def _highlight_research_display_row(row: pd.Series) -> list[str]:
    styles = [""] * len(row)
    columns = list(row.index)

    def set_style(column: str, style: str) -> None:
        if column in columns:
            styles[columns.index(column)] = style

    state = str(row.get("Research_State", ""))
    if state == "Setup evidence review":
        set_style("Research_State", "color: #00ff88; font-weight: bold;")
    elif state == "Evidence gap review":
        set_style("Research_State", "color: #FFD700; font-weight: bold;")
    elif state == "Risk review only":
        set_style("Research_State", "color: #ff4444; font-weight: bold;")
    elif state == "Insufficient evidence":
        set_style("Research_State", "color: #888888;")

    risk_context = str(row.get("Research_Risk_Context", ""))
    if "Extension risk" in risk_context:
        set_style("Research_Risk_Context", "color: #ffb020; font-weight: bold;")
    elif "Trend context" in risk_context:
        set_style("Research_Risk_Context", "color: #00ff88; font-weight: bold;")

    proxy_type = str(row.get("Proxy_Type", ""))
    if "NO PROXY" in proxy_type:
        set_style("Proxy_Type", "color: #ff4444;")
    else:
        set_style("Proxy_Type", "color: #88ccff;")
    set_style("P_Value", "color: #aaa; font-style: italic;")

    proxy_signal = str(row.get("Proxy_Signal", ""))
    if proxy_signal == "COILED SPRING":
        set_style("Proxy_Signal", "color: #00ff88; font-weight: bold; background-color: rgba(0,255,136,0.1);")
    elif proxy_signal == "CORRELATED":
        set_style("Proxy_Signal", "color: #aaddaa;")
    elif proxy_signal == "DIVERGING":
        set_style("Proxy_Signal", "color: #ffb020; font-weight: bold; background-color: rgba(255,176,32,0.1);")
    elif proxy_signal in {"MISPRICED", "UNDERVALUED"}:
        set_style("Proxy_Signal", "color: #ff4444; font-weight: bold;")
    elif proxy_signal == "CORRECTING":
        set_style("Proxy_Signal", "color: #888888;")

    return styles


def style_scanner_research_display_frame(view_df: pd.DataFrame) -> pd.io.formats.style.Styler:
    return view_df.style.apply(_highlight_research_display_row, axis=1)


__all__ = [
    "ACTION_SHAPED_SCANNER_DISPLAY_COLUMNS",
    "build_scanner_research_display_frame",
    "style_scanner_research_display_frame",
]
