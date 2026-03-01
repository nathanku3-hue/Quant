"""
Terminal Zero — Dashboard (The "Transparent Advisor")

Implements the updated visualization for the 3-Regime Logic.
  - Regimes: Attack (Green), Caution (Yellow), Defense (Red)
  - Explainability: Sidebar shows "Why" the system is in its current state.
"""

import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go

import time
from core import optimizer
from core.dashboard_control_plane import get_watchlist_tickers
from core.dashboard_control_plane import plan_auto_update
from data import updater
from data.dashboard_data_loader import load_dashboard_data
from data import fundamentals as fundamentals_data
from data import fundamentals_updater
from data import calendar_updater
from data import macro_loader
from data import liquidity_loader
from strategies.investor_cockpit import InvestorCockpitStrategy
from strategies.regime_manager import RegimeManager, GovernorState
from views.auto_backtest_view import render_auto_backtest_view
from views.scanner_view import render_scanner_view
from views.detail_view import render_detail_view
from views.optimizer_view import render_optimizer_view

# ── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Terminal Zero",
    page_icon="🎯",
)

PROCESSED_DIR = "./data/processed"
STATIC_DIR = "./data/static"
SECTOR_MAP_PATH = f"{STATIC_DIR}/sector_map.parquet"
CALENDAR_PATH = f"{PROCESSED_DIR}/earnings_calendar.parquet"
MACRO_FEATURES_PATH = f"{PROCESSED_DIR}/macro_features.parquet"
MACRO_FEATURES_TRI_PATH = f"{PROCESSED_DIR}/macro_features_tri.parquet"
LIQUIDITY_FEATURES_PATH = f"{PROCESSED_DIR}/liquidity_features.parquet"
UNIVERSE_R3000_DAILY_PATH = f"{PROCESSED_DIR}/universe_r3000_daily.parquet"
PRICES_TRI_PATH = f"{PROCESSED_DIR}/prices_tri.parquet"
WATCHLIST_FILE = "./data/watchlist.json"
QUALITY_BYPASS_TICKERS = {"SPY", "QQQ", "IWM", "DIA", "GLD", "TLT"}
REGIME_MANAGER = RegimeManager()


def _get_watchlist_tickers() -> list[str]:
    return get_watchlist_tickers(WATCHLIST_FILE)


def _patch_hot_fundamentals_if_needed(fundamentals_wide: dict | None):
    """
    Hot/Cold architecture:
      - Cold universe uses snapshot.
      - Hot names (watchlist) auto-refresh fundamentals when older than 95 days.
    """
    if not isinstance(fundamentals_wide, dict):
        return

    if st.session_state.get("_hot_fundamentals_checked", False):
        return
    st.session_state["_hot_fundamentals_checked"] = True

    latest = fundamentals_wide.get("latest")
    watchlist = _get_watchlist_tickers()
    stale = fundamentals_data.get_stale_hot_tickers(
        latest_snapshot=latest,
        hot_tickers=watchlist,
        max_age_days=fundamentals_data.HOT_STALE_DAYS,
        skip_tickers=QUALITY_BYPASS_TICKERS,
    )
    if not stale:
        return

    preview = ", ".join(stale[:5])
    suffix = "..." if len(stale) > 5 else ""
    st.toast(
        f"⚠️ Refreshing stale fundamentals ({len(stale)}): {preview}{suffix}",
        icon="🔄",
    )
    try:
        result = fundamentals_updater.run_update(scope="Custom", custom_list=",".join(stale))
    except Exception as e:
        st.warning(f"Fundamentals auto-refresh failed for hot list: {e}")
        return
    if result.get("success"):
        st.cache_data.clear()
        st.rerun()
    st.warning("Fundamentals auto-refresh failed for hot list. Use Data Manager or Detail refresh button.")


# ── Data Loading (Memory Optimized) ─────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_data(top_n=2000, start_year=2000, universe_mode="top_liquid", asof_date=None):
    return load_dashboard_data(
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
        asof_date=asof_date,
        processed_dir=PROCESSED_DIR,
        static_dir=STATIC_DIR,
    )


# ── Session State [FR-026] ──────────────────────────────────────────────────
if "cockpit_view" not in st.session_state:
    st.session_state.cockpit_view = "scanner"
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "update_attempted" not in st.session_state:
    st.session_state.update_attempted = False
if "update_attempted_for_date" not in st.session_state:
    st.session_state.update_attempted_for_date = None


def _go_detail(permno):
    st.session_state.cockpit_view = "detail"
    st.session_state.selected_ticker = permno


def _go_scanner():
    st.session_state.cockpit_view = "scanner"
    st.session_state.selected_ticker = None


def _render_score_badge(score):
    """Return HTML for a conviction score badge."""
    if score >= 9:
        return f"<span style='color:#00ff88;font-weight:bold;'>🔥 {score}/10</span>"
    elif score >= 7:
        return f"<span style='color:#FFD700;font-weight:bold;'>✅ {score}/10</span>"
    elif score >= 5:
        return f"<span style='color:#aaa;'>⚠️ {score}/10</span>"
    else:
        return f"<span style='color:#666;'>{score}/10</span>"


def _dim_icon(pts, max_pts):
    if pts >= max_pts:
        return "✅"
    elif pts > 0:
        return "⚠️"
    return "❌"


def _governor_snapshot(macro: pd.DataFrame, index: pd.Index) -> dict:
    try:
        result = REGIME_MANAGER.evaluate(macro, index).latest()
    except Exception:
        result = {
            "governor_state": GovernorState.AMBER.value,
            "reason": "Fallback: FR-041 unavailable",
            "target_exposure": 0.5,
            "matrix_exposure": 0.5,
            "throttle_score": 1.0,
            "composite_z": 0.0,
            "bocpd_prob": float("nan"),
        }

    state = str(result.get("governor_state", GovernorState.AMBER.value)).upper()
    if state not in {GovernorState.RED.value, GovernorState.AMBER.value, GovernorState.GREEN.value}:
        state = GovernorState.AMBER.value
    result["governor_state"] = state
    return result


def _render_governor_banner(snapshot: dict, title: str = "FR-041 Governor"):
    state = str(snapshot.get("governor_state", GovernorState.AMBER.value))
    reason = str(snapshot.get("reason", "No explainability available"))
    target = float(snapshot.get("target_exposure", 0.5))
    throttle = float(snapshot.get("throttle_score", 1.0))
    matrix_exp = float(snapshot.get("matrix_exposure", target))
    bocpd = pd.to_numeric(snapshot.get("bocpd_prob", np.nan), errors="coerce")

    if state == GovernorState.RED.value:
        icon, color, label = "🔴", "#ff4444", "RED"
    elif state == GovernorState.GREEN.value:
        icon, color, label = "🟢", "#00c57a", "GREEN"
    else:
        icon, color, label = "🟠", "#ffb020", "AMBER"

    bocpd_label = f"{float(bocpd):.2f}" if pd.notna(bocpd) else "N/A"
    st.markdown(
        f"""
        <div style='border: 1px solid {color}; border-left: 6px solid {color};
                    border-radius: 10px; padding: 14px 16px; margin: 8px 0 14px 0;
                    background: linear-gradient(135deg, rgba(15,22,35,0.95), rgba(20,30,45,0.75));'>
            <div style='display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;'>
                <div>
                    <div style='font-size:0.75rem; color:#9aa4b2; letter-spacing:0.08em;'>{title}</div>
                    <div style='font-size:1.25rem; font-weight:700; color:{color};'>{icon} {label}</div>
                    <div style='font-size:0.92rem; color:#d8dee9; margin-top:4px;'>{reason}</div>
                </div>
                <div style='display:flex; gap:18px;'>
                    <div>
                        <div style='font-size:0.72rem; color:#9aa4b2;'>Target Exposure</div>
                        <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{target:.2f}x</div>
                    </div>
                    <div>
                        <div style='font-size:0.72rem; color:#9aa4b2;'>Matrix</div>
                        <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{matrix_exp:.2f}x</div>
                    </div>
                    <div>
                        <div style='font-size:0.72rem; color:#9aa4b2;'>Throttle</div>
                        <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{throttle:.2f}</div>
                    </div>
                    <div>
                        <div style='font-size:0.72rem; color:#9aa4b2;'>BOCPD</div>
                        <div style='font-size:1.10rem; color:#ffffff; font-weight:700;'>{bocpd_label}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Dashboard UI ────────────────────────────────────────────────────────────

def render_investor_cockpit(prices_wide, macro, ticker_map, fundamentals_wide):
    st.header("✈️ Terminal Zero: Investor Cockpit")

    # ── [F1] Adaptive Toggle ────────────────────────────────────────────────
    use_adaptive = st.sidebar.checkbox(
        "🧬 Dynamic Volatility Mapping (Adaptive k/z)", value=True
    )
    use_alpha_engine = st.sidebar.checkbox(
        "🧠 Phase 15 Alpha Engine (FR-070)",
        value=False,
        help="Enable hysteresis + ratchet alpha routing in cockpit paths.",
    )

    if use_adaptive:
        st.sidebar.info(
            "**Adaptive Mode**: k and z are auto-calculated per stock "
            "based on 60-day volatility rank.\n\n"
            "High Vol → k=4.0 (loose), z=-1.0 (shallow)\n\n"
            "Low Vol → k=2.5 (tight), z=-3.0 (deep)"
        )
        k_stop = 3.5  # fallback for chart labels
        z_entry = -2.5
    else:
        k_stop = st.sidebar.slider(
            "Chandelier Stop Multiplier (k)", 2.0, 5.0, 3.5, step=0.1
        )
        z_entry = st.sidebar.slider(
            "Dip Entry Threshold (z)", -4.0, -1.0, -2.5, step=0.1
        )

    # ── Latest date ─────────────────────────────────────────────────────────
    latest_date = prices_wide.index[-1]

    # ── 1. MACRO ADVISOR ────────────────────────────────────────────────────
    governor_snapshot = _governor_snapshot(macro, prices_wide.index)
    _render_governor_banner(governor_snapshot, title="Cockpit Governor (FR-041)")

    if not isinstance(macro, pd.DataFrame) or macro.empty or macro.index.max() < latest_date:
        st.caption("Macro/liquidity data is not fully aligned to the latest price date; governor used forward-filled context.")

    if use_alpha_engine:
        try:
            rev = {str(v).upper(): int(k) for k, v in ticker_map.items()}
            wl_tickers = _get_watchlist_tickers()
            wl_permnos = [rev[t.upper()] for t in wl_tickers if t.upper() in rev and rev[t.upper()] in prices_wide.columns]
            if wl_permnos:
                prices_alpha = prices_wide[wl_permnos].dropna(how="all")
                alpha_strat = InvestorCockpitStrategy(
                    k_stop=k_stop,
                    z_entry=z_entry,
                    use_dynamic_params=use_adaptive,
                    green_candle=True,
                    use_alpha_engine=True,
                )
                _, _, alpha_details = alpha_strat.generate_weights(prices_alpha, fundamentals_wide, macro)
                top_alpha = alpha_details.get("top_alpha_candidates", [])
                active_stops = alpha_details.get("active_stop_losses", [])

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("#### 🧠 Top Alpha Candidates")
                    if top_alpha:
                        top_df = pd.DataFrame(top_alpha)
                        top_df["ticker"] = top_df["permno"].apply(lambda p: ticker_map.get(int(p), str(p)))
                        cols = [c for c in ["ticker", "alpha_score", "price", "stop_price"] if c in top_df.columns]
                        st.dataframe(top_df[cols], width="stretch", hide_index=True)
                    else:
                        st.caption("No active alpha candidates.")

                with c2:
                    st.markdown("#### 🛑 Active Stop-Loss (Ratchet)")
                    if active_stops:
                        stop_df = pd.DataFrame(active_stops)
                        stop_df["ticker"] = stop_df["permno"].apply(lambda p: ticker_map.get(int(p), str(p)))
                        cols = [c for c in ["ticker", "stop_loss_level"] if c in stop_df.columns]
                        st.dataframe(stop_df[cols], width="stretch", hide_index=True)
                    else:
                        st.caption("No active stop levels.")
        except Exception as e:
            st.caption(f"Alpha panel unavailable: {e}")

    # ── 2. VIEW ROUTER [FR-026] ─────────────────────────────────────────────
    if st.session_state.cockpit_view == "detail" and st.session_state.selected_ticker is not None:
        render_detail_view(
            prices_wide,
            macro,
            ticker_map,
            fundamentals_wide,
            k_stop,
            z_entry,
            use_adaptive,
            use_alpha_engine,
        )
    else:
        render_scanner_view(
            prices_wide,
            macro,
            ticker_map,
            fundamentals_wide,
            k_stop,
            z_entry,
            use_adaptive,
            use_alpha_engine,
        )
    return


def render_optimizer(prices_wide, returns_wide, macro):
    """Render the 2D Parameter Sweep Heatmap."""
    st.header("🎯 Parameter Optimizer")
    st.markdown(
        "Find the mathematical **Sweet Spot** between Return and Pain. "
        "The system will test all combinations of Stop Multiplier (k) and Entry Threshold (z)."
    )

    # ── Sweep Controls ──────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        k_start = st.number_input("k Start", value=2.0, step=0.5)
        k_end = st.number_input("k End", value=5.0, step=0.5)
    with col2:
        z_start = st.number_input("z Start", value=-1.5, step=0.5)
        z_end = st.number_input("z End", value=-4.0, step=0.5)
    with col3:
        step_size = st.selectbox("Step Size", [0.25, 0.5, 1.0], index=1)
        cost_bps_opt = st.number_input("Cost (bps)", value=10, min_value=0) / 10_000

    k_range = np.arange(k_start, k_end + 0.01, step_size)
    z_range = np.arange(z_start, z_end - 0.01, -step_size)
    n_combos = len(k_range) * len(z_range)

    st.info(f"Grid: {len(k_range)} k values × {len(z_range)} z values = **{n_combos} combinations**")

    metric_choice = st.selectbox("Heatmap Metric", ["upi", "sharpe", "cagr", "max_dd"], index=0)
    metric_labels = {
        "upi": "Ulcer Performance Index (Higher=Better)",
        "sharpe": "Sharpe Ratio (Higher=Better)",
        "cagr": "CAGR (Higher=Better)",
        "max_dd": "Max Drawdown (Closer to 0=Better)",
    }

    run_sweep = st.button("🚀 Run Parameter Sweep", width="stretch", type="primary")

    if run_sweep:
        with st.spinner(f"⏳ Simulating {n_combos} parameter combinations..."):
            df_results = optimizer.run_parameter_sweep(
                prices_wide, returns_wide, macro,
                k_range=k_range, z_range=z_range, cost_bps=cost_bps_opt,
            )

        if df_results.empty or df_results[metric_choice].isna().all():
            st.error("No valid results. Try a different parameter range.")
            return

        # ── Find Golden Parameters ──────────────────────────────────────────
        if metric_choice == "max_dd":
            best_idx = df_results[metric_choice].idxmax()  # Closest to 0
        else:
            best_idx = df_results[metric_choice].idxmax()

        best = df_results.loc[best_idx]
        st.success(
            f"🏆 **Golden Parameters**: k={best['k']:.2f}, z={best['z']:.2f} "
            f"| CAGR={best['cagr']:.2%} | MaxDD={best['max_dd']:.1%} "
            f"| Sharpe={best['sharpe']:.2f} | UPI={best['upi']:.2f}"
        )

        # ── 2D Heatmap ──────────────────────────────────────────────────────
        heat_data = df_results.pivot(index="k", columns="z", values=metric_choice)

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=heat_data.values,
                x=[f"{c:.1f}" for c in heat_data.columns],
                y=[f"{r:.1f}" for r in heat_data.index],
                colorscale="Viridis",
                colorbar=dict(title=metric_labels[metric_choice]),
                hovertemplate="k=%{y}<br>z=%{x}<br>Value=%{z:.4f}<extra></extra>",
            )
        )

        # Mark the Golden Cell
        fig_heat.add_trace(
            go.Scatter(
                x=[f"{best['z']:.1f}"],
                y=[f"{best['k']:.1f}"],
                mode="markers+text",
                marker=dict(size=18, color="#ff4444", symbol="star"),
                text=["★ BEST"],
                textposition="top center",
                textfont=dict(color="white", size=12),
                name="Optimal",
            )
        )

        fig_heat.update_layout(
            title=f"Parameter Sweep: {metric_labels[metric_choice]}",
            xaxis_title="Entry Threshold (z) — more negative = deeper dip required",
            yaxis_title="Stop Multiplier (k) — higher = looser stop",
            template="plotly_dark",
            height=500,
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
        )
        st.plotly_chart(fig_heat, width="stretch")

        # ── Results Table ───────────────────────────────────────────────────
        st.markdown("### 📊 Top 10 Parameter Combinations")
        top10 = df_results.nlargest(10, metric_choice if metric_choice != "max_dd" else "upi")
        st.dataframe(
            top10.style.format({
                "total_return": "{:.2%}",
                "cagr": "{:.2%}",
                "max_dd": "{:.1%}",
                "sharpe": "{:.2f}",
                "ulcer_index": "{:.4f}",
                "upi": "{:.2f}",
                "avg_turnover": "{:.2%}",
            }),
            width="stretch",
        )

        # ── "Apply to Cockpit" ──────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            f"💡 To use these parameters in the **Investor Cockpit**, switch to that tab "
            f"and set **k={best['k']:.1f}** and **z={best['z']:.1f}** in the sidebar sliders."
        )

        # ── [F2] Compare Fixed vs Adaptive ──────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧬 Fixed vs Adaptive Comparison")
        with st.spinner("Running Adaptive benchmark..."):
            adaptive_result = optimizer.run_adaptive_benchmark(
                prices_wide, returns_wide, macro, cost_bps=cost_bps_opt
            )

        comp1, comp2 = st.columns(2)
        with comp1:
            st.markdown(
                f"""
                <div style='border: 2px solid #FFD700; padding: 15px; border-radius: 8px;
                            background: rgba(255,215,0,0.05);'>
                    <h4 style='color:#FFD700; margin:0;'>🏆 Best Fixed (k={best['k']:.1f}, z={best['z']:.1f})</h4>
                    <p style='margin:5px 0;'>CAGR: <b>{best['cagr']:.2%}</b></p>
                    <p style='margin:5px 0;'>Max DD: <b>{best['max_dd']:.1%}</b></p>
                    <p style='margin:5px 0;'>Sharpe: <b>{best['sharpe']:.2f}</b></p>
                    <p style='margin:5px 0;'>UPI: <b>{best['upi']:.2f}</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with comp2:
            a = adaptive_result
            st.markdown(
                f"""
                <div style='border: 2px solid #00ff88; padding: 15px; border-radius: 8px;
                            background: rgba(0,255,136,0.05);'>
                    <h4 style='color:#00ff88; margin:0;'>🧬 Adaptive (Dynamic k/z)</h4>
                    <p style='margin:5px 0;'>CAGR: <b>{a['cagr']:.2%}</b></p>
                    <p style='margin:5px 0;'>Max DD: <b>{a['max_dd']:.1%}</b></p>
                    <p style='margin:5px 0;'>Sharpe: <b>{a['sharpe']:.2f}</b></p>
                    <p style='margin:5px 0;'>UPI: <b>{a['upi']:.2f}</b></p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Verdict
        if a["upi"] > best["upi"]:
            st.success("✅ **Adaptive mode outperforms the best fixed parameters!** Use 🧬 Dynamic Mapping.")
        else:
            st.info(f"📌 Fixed (k={best['k']:.1f}, z={best['z']:.1f}) slightly edges Adaptive on UPI. Consider using Fixed params.")


# ── Data Manager Tab ────────────────────────────────────────────────────────


def render_data_manager(prices_wide, macro, ticker_map, fundamentals_wide=None):
    st.header("💾 Data Lake Manager")

    # ── System Status ───────────────────────────────────────────────────────
    last_date = prices_wide.index.max().date()
    ticker_count = len(ticker_map)
    has_macro = isinstance(macro, pd.DataFrame) and len(macro.index) > 0
    vix_now = float(macro["vix_proxy"].ffill().iloc[-1]) if has_macro and "vix_proxy" in macro.columns else float("nan")
    spy_now = float(macro["spy_close"].ffill().iloc[-1]) if has_macro and "spy_close" in macro.columns else float("nan")

    today = datetime.date.today()
    days_stale = (today - last_date).days
    freshness_color = "#00ff88" if days_stale <= 1 else "#FFD700" if days_stale <= 5 else "#ff4444"
    freshness_label = "LIVE" if days_stale <= 1 else f"{days_stale}d STALE"

    st.markdown(
        f"""
        <div style='display: flex; gap: 15px; margin-bottom: 20px;'>
            <div style='flex:1; border: 1px solid #333; border-radius: 8px; padding: 15px;
                        border-top: 3px solid {freshness_color};'>
                <div style='color: #888; font-size: 0.75em;'>DATA CURRENT TO</div>
                <div style='font-size: 1.5em; font-weight: bold;'>{last_date}</div>
                <div style='color: {freshness_color}; font-weight: bold;'>{freshness_label}</div>
            </div>
            <div style='flex:1; border: 1px solid #333; border-radius: 8px; padding: 15px;
                        border-top: 3px solid #00aaff;'>
                <div style='color: #888; font-size: 0.75em;'>UNIVERSE SIZE</div>
                <div style='font-size: 1.5em; font-weight: bold;'>{ticker_count:,}</div>
                <div style='color: #888;'>tickers mapped</div>
            </div>
            <div style='flex:1; border: 1px solid #333; border-radius: 8px; padding: 15px;
                        border-top: 3px solid #FFD700;'>
                <div style='color: #888; font-size: 0.75em;'>SPY</div>
                <div style='font-size: 1.5em; font-weight: bold;'>{f"${spy_now:.2f}" if pd.notna(spy_now) else "N/A"}</div>
                <div style='color: #888;'>VIX Proxy: {f"{vix_now:.1f}" if pd.notna(vix_now) else "N/A"}</div>
            </div>
            <div style='flex:1; border: 1px solid #333; border-radius: 8px; padding: 15px;
                        border-top: 3px solid #aa44ff;'>
                <div style='color: #888; font-size: 0.75em;'>PATCHED TICKERS</div>
                <div style='font-size: 1.5em; font-weight: bold;'>
                    {len([p for p in prices_wide.columns if p in ticker_map])}
                </div>
                <div style='color: #888;'>in active universe</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    governor_snapshot = _governor_snapshot(macro, prices_wide.index)
    _render_governor_banner(governor_snapshot, title="Data Manager Governor (FR-041)")

    st.divider()

    # ── Update Controls ─────────────────────────────────────────────────────
    st.subheader("🚀 Live Update (Yahoo Finance)")

    col_scope, col_action = st.columns([2, 1])

    with col_scope:
        scope = st.selectbox(
            "Update Scope:",
            ["Top 50 Liquid", "Top 100 Liquid", "Top 200 Liquid", "Top 500 Liquid", "Top 3000 Liquid", "Custom Watchlist"],
            help="How many tickers to download from Yahoo Finance."
        )

        custom_list = ""
        if scope == "Custom Watchlist":
            custom_list = st.text_area(
                "Enter tickers (comma separated):",
                "AAPL, NVDA, TSLA, MSFT, AMZN, GOOG, META, SOFI, NBIS, PLTR",
                help="These tickers will be fetched from Yahoo Finance."
            )

    with col_action:
        st.markdown("<br>", unsafe_allow_html=True)
        run_update = st.button(
            "🔄 Run Update Now",
            width="stretch",
            type="primary",
        )

    if run_update:
        with st.status("📡 Downloading from Yahoo Finance...", expanded=True) as sts:
            # Map scope label to updater param
            scope_map = {
                "Top 50 Liquid": "Top 50",
                "Top 100 Liquid": "Top 100",
                "Top 200 Liquid": "Top 200",
                "Top 500 Liquid": "Top 500",
                "Top 3000 Liquid": "Top 3000",
                "Custom Watchlist": "Custom",
            }
            try:
                result = updater.run_update(
                    scope=scope_map.get(scope, "Top 50"),
                    custom_list=custom_list if scope == "Custom Watchlist" else None,
                )
            except Exception as e:
                result = {
                    "success": False,
                    "log": [f"❌ Update crashed: {e}"],
                }

            # Display logs
            for line in result.get("log", []):
                st.write(line)

            if result.get("success"):
                sts.update(label="✅ Update Complete!", state="complete", expanded=False)
                st.success(
                    f"Patched **{result.get('tickers_updated', 0)}** tickers to **{result.get('last_date', 'N/A')}**. "
                    f"Refreshing dashboard..."
                )
                # Clear cache so dashboard picks up new data
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                sts.update(label="❌ Update Failed", state="error")
                st.error("Yahoo update failed. Check logs above and retry.")

    st.divider()
    st.subheader("📅 Earnings Calendar (Catalyst Radar)")

    calendar_ctx = None
    if isinstance(fundamentals_wide, dict):
        calendar_ctx = fundamentals_wide.get("earnings_calendar")

    if isinstance(calendar_ctx, pd.DataFrame) and not calendar_ctx.empty:
        now = pd.Timestamp.utcnow().tz_localize(None).normalize()
        next_dates = pd.to_datetime(calendar_ctx.get("next_earnings_date"), errors="coerce")
        fetched_at = pd.to_datetime(calendar_ctx.get("fetched_at"), errors="coerce")
        coverage = int(next_dates.notna().sum())
        upcoming_7d = int(((next_dates - now).dt.days.between(0, 7, inclusive="both")).sum())
        last_fetch = fetched_at.max()
        last_fetch_label = str(last_fetch.date()) if pd.notna(last_fetch) else "N/A"

        c1, c2, c3 = st.columns(3)
        c1.metric("Calendar Coverage", f"{coverage:,}")
        c2.metric("Earnings Next 7D", f"{upcoming_7d:,}")
        c3.metric("Last Calendar Fetch", last_fetch_label)
    else:
        st.caption("No earnings calendar loaded yet.")

    cscope, caction = st.columns([2, 1])
    with cscope:
        cal_scope = st.selectbox(
            "Calendar Scope:",
            ["Top 20 Liquid", "Top 50 Liquid", "Top 100 Liquid", "Top 200 Liquid", "Top 500 Liquid", "Top 3000 Liquid", "Custom Watchlist"],
            help="Fetch earnings dates for selected scope.",
        )
        cal_custom = ""
        if cal_scope == "Custom Watchlist":
            cal_custom = st.text_area(
                "Calendar tickers (comma separated):",
                ",".join(_get_watchlist_tickers()),
                help="Custom symbols for earnings date refresh.",
            )
    with caction:
        st.markdown("<br>", unsafe_allow_html=True)
        run_calendar = st.button("📅 Refresh Calendar", width="stretch")

    if run_calendar:
        with st.status("📡 Fetching Yahoo earnings calendar...", expanded=True) as sts:
            scope_map = {
                "Top 20 Liquid": "Top 20",
                "Top 50 Liquid": "Top 50",
                "Top 100 Liquid": "Top 100",
                "Top 200 Liquid": "Top 200",
                "Top 500 Liquid": "Top 500",
                "Top 3000 Liquid": "Top 3000",
                "Custom Watchlist": "Custom",
            }
            try:
                result = calendar_updater.run_update(
                    scope=scope_map.get(cal_scope, "Top 100"),
                    custom_list=cal_custom if cal_scope == "Custom Watchlist" else None,
                )
            except Exception as e:
                result = {
                    "success": False,
                    "log": [f"❌ Calendar refresh crashed: {e}"],
                }

            for line in result.get("log", []):
                st.write(line)

            if result.get("success"):
                sts.update(label="✅ Calendar Update Complete!", state="complete", expanded=False)
                st.success(
                    f"Updated earnings calendar for **{result.get('tickers_fetched', 0)}** symbols. Refreshing dashboard..."
                )
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                sts.update(label="❌ Calendar Update Failed", state="error")
                st.error("Calendar refresh failed. Check logs above and retry.")

    st.divider()
    st.subheader("🧠 Macro Layer (FR-035)")
    m1, m2, m3 = st.columns(3)
    regime_now = float(macro["regime_scalar"].ffill().iloc[-1]) if "regime_scalar" in macro.columns and len(macro) else float("nan")
    stress_now = (
        int(macro["stress_count"].iloc[-1])
        if "stress_count" in macro.columns and len(macro)
        else None
    )
    macro_last = str(macro.index.max().date()) if len(macro.index) else "N/A"
    m1.metric("Macro Last Date", macro_last)
    m2.metric("Regime Scalar", f"{regime_now:.2f}" if pd.notna(regime_now) else "N/A")
    m3.metric("Stress Count", f"{stress_now}" if stress_now is not None else "N/A")

    build_col, run_col = st.columns([2, 1])
    with build_col:
        macro_start_year = st.number_input(
            "Macro Build Start Year",
            min_value=1990,
            max_value=int(datetime.date.today().year),
            value=2000,
            step=1,
            help="Rebuild macro feature history from this year.",
        )
    with run_col:
        st.markdown("<br>", unsafe_allow_html=True)
        run_macro = st.button("🧠 Rebuild Macro Layer", width="stretch")

    if run_macro:
        with st.status("⚙️ Building macro_features.parquet...", expanded=True) as sts:
            try:
                result = macro_loader.run_build(start_year=int(macro_start_year))
            except Exception as e:
                result = {
                    "success": False,
                    "log": [f"❌ Macro build crashed: {e}"],
                }
            for line in result.get("log", []):
                st.write(line)
            for warn in result.get("warnings", []):
                st.warning(warn)
            if result.get("success"):
                sts.update(label="✅ Macro Build Complete", state="complete", expanded=False)
                st.success(f"Built macro layer with {result.get('rows_written', 0):,} rows. Refreshing dashboard...")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                sts.update(label="❌ Macro Build Failed", state="error")

    st.divider()
    st.subheader("💧 Liquidity Layer (FR-040)")
    liq_last = str(macro.index.max().date()) if "us_net_liquidity_mm" in macro.columns and len(macro) else "N/A"
    liq_impulse_now = (
        float(macro["liquidity_impulse"].ffill().iloc[-1])
        if "liquidity_impulse" in macro.columns and len(macro)
        else float("nan")
    )
    repo_now = (
        float(macro["repo_spread_bps"].ffill().iloc[-1])
        if "repo_spread_bps" in macro.columns and len(macro)
        else float("nan")
    )
    l1, l2, l3 = st.columns(3)
    l1.metric("Liquidity Last Date", liq_last)
    l2.metric("Liquidity Impulse", f"{liq_impulse_now:.2f}" if pd.notna(liq_impulse_now) else "N/A")
    l3.metric("Repo Spread (bps)", f"{repo_now:.1f}" if pd.notna(repo_now) else "N/A")

    liq_build_col, liq_run_col = st.columns([2, 1])
    with liq_build_col:
        liq_start_year = st.number_input(
            "Liquidity Build Start Year",
            min_value=1990,
            max_value=int(datetime.date.today().year),
            value=2000,
            step=1,
            key="liquidity_build_start_year",
        )
    with liq_run_col:
        st.markdown("<br>", unsafe_allow_html=True)
        run_liquidity = st.button("💧 Rebuild Liquidity Layer", width="stretch")

    if run_liquidity:
        with st.status("⚙️ Building liquidity_features.parquet...", expanded=True) as sts:
            try:
                result = liquidity_loader.run_build(start_year=int(liq_start_year))
            except Exception as e:
                result = {
                    "success": False,
                    "log": [f"❌ Liquidity build crashed: {e}"],
                }
            for line in result.get("log", []):
                st.write(line)
            for warn in result.get("warnings", []):
                st.warning(warn)
            if result.get("success"):
                sts.update(label="✅ Liquidity Build Complete", state="complete", expanded=False)
                st.success(
                    f"Built liquidity layer with {result.get('rows_written', 0):,} rows. Refreshing dashboard..."
                )
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                sts.update(label="❌ Liquidity Build Failed", state="error")

    # ── Architecture Info ───────────────────────────────────────────────────
    st.divider()
    st.subheader("🏗️ Data Architecture")
    st.markdown(
        """
        | Layer | File | Description |
        |---|---|---|
        | **Base** | `prices.parquet` | WRDS CRSP 2000-2024 (47M rows, read-only) |
        | **Patch** | `yahoo_patch.parquet` | Yahoo Finance 2025+ (auto-updated) |
        | **Macro** | `macro_features.parquet` | Regime feature superset (FR-035 SSOT) |
        | **Macro Gates** | `macro_gates.parquet` | Daily hard-gate labels (QQQ drawdown/MA200 + VIX term) |
        | **Liquidity** | `liquidity_features.parquet` | Net-liquidity, repo stress, and flow features (FR-040) |
        | **Map** | `tickers.parquet` | Permno ↔ Ticker lookup (auto-expanded) |
        | **Calendar** | `earnings_calendar.parquet` | Upcoming/recent earnings dates for Catalyst Radar |

        The dashboard reads **Base + Patch** via DuckDB `UNION ALL`.
        The base file is never modified — only the patch layer grows.
        """
    )


def main():
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style='text-align: center; padding: 1rem 0 0.5rem 0;'>
            <h1 style='margin-bottom: 0; letter-spacing: 0.15em; color: #00ff88;
                        font-family: monospace; font-size: 2.5rem;'>
                ⟨ TERMINAL ZERO ⟩
            </h1>
            <p style='color: #888; font-family: monospace; font-size: 0.9rem;'>
                Regime-Adaptive Quantitative Research Console (Transparent Advisor)
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Load Data ───────────────────────────────────────────────────────────
    with st.spinner("⏳ Loading Data Lake (Top 2000 Liquid Stocks) ..."):
        try:
            returns_wide, prices_wide, macro, ticker_map, fundamentals_wide = load_data()
        except Exception as e:
            st.error(f"Data Load Failed: {e}")
            st.stop()

    _patch_hot_fundamentals_if_needed(fundamentals_wide)

    # ── Auto-Update Check [FR-025] ──────────────────────────────────────────
    last_db_date = prices_wide.index.max()
    auto_update_plan = plan_auto_update(
        last_db_date=last_db_date,
        update_attempted=bool(st.session_state.update_attempted),
        update_attempted_for_date=st.session_state.update_attempted_for_date,
    )
    st.session_state.update_attempted = bool(auto_update_plan.update_attempted)
    st.session_state.update_attempted_for_date = auto_update_plan.update_attempted_for_date

    if auto_update_plan.is_invalid_state:
        st.error(f"Auto-update planner INVALID STATE: {auto_update_plan.message}")
        st.caption(f"Reason: {auto_update_plan.reason}")
    elif auto_update_plan.should_attempt_update:
        st.session_state.update_attempted = True
        st.toast("⏳ Data is stale. Auto-updating watchlist...", icon="🔄")
        last_data_label = auto_update_plan.update_attempted_for_date or "unknown"
        with st.spinner(f"📡 Auto-updating (last data: {last_data_label})..."):
            target_list = _get_watchlist_tickers()
            try:
                result = updater.run_update(
                    scope="Custom",
                    custom_list=",".join(target_list),
                )
            except Exception as e:
                st.error(f"Auto-update failed: {e}")
                result = {"success": False}
            if result.get("success"):
                st.cache_data.clear()
                st.rerun()
            else:
                st.warning("Auto-update failed. Skipping further auto-retries this session.")
    elif auto_update_plan.show_already_attempted_caption:
        st.caption("⏸️ Auto-update already attempted this session. Use Data Manager to retry.")

    # ── Sidebar Mode Selection ──────────────────────────────────────────────
    page = st.sidebar.radio(
        "Console Mode",
        ["✈️ Investor Cockpit", "📦 Portfolio Optimizer", "🎯 Optimizer", "🔄 Data Manager", "🔬 Lab / Backtest"],
    )

    if page == "✈️ Investor Cockpit":
        render_investor_cockpit(prices_wide, macro, ticker_map, fundamentals_wide)
        return
    elif page == "📦 Portfolio Optimizer":
        render_optimizer_view(
            prices_wide=prices_wide,
            ticker_map=ticker_map,
            sector_map=fundamentals_wide.get("sector_map") if isinstance(fundamentals_wide, dict) else None,
            selected_tickers=_get_watchlist_tickers(),
        )
        return
    elif page == "🎯 Optimizer":
        render_optimizer(prices_wide, returns_wide, macro)
        return
    elif page == "🔄 Data Manager":
        render_data_manager(prices_wide, macro, ticker_map, fundamentals_wide)
        return

    render_auto_backtest_view(prices_wide, returns_wide, macro)


# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    html, body, [class*="stApp"] { font-family: 'JetBrains Mono', monospace; background-color: #0e1117; }
    .stMetric label { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #888; }
    .stMetric [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace; }
    .stButton>button { background: linear-gradient(135deg, #00ff88, #00cc66); color: #000; font-weight: bold; }
    </style>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    main()
