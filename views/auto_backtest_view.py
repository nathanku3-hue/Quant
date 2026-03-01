from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from core import auto_backtest_control_plane as control_plane
from core import engine
from strategies.adaptive_trend import AdaptiveTrendStrategy


def _cost_bps_input_to_decimal(cost_bps_input: float) -> float:
    return max(0.0, float(cost_bps_input)) / 10_000.0


def render_auto_backtest_view(
    prices_wide,
    returns_wide,
    macro,
    *,
    cache_path: str = control_plane.DEFAULT_CACHE_PATH,
) -> None:
    cache_load = control_plane.load_cache(cache_path, error_policy="fail")
    if not cache_load.ok:
        if cache_load.reason == "missing_file":
            cache_state = control_plane.create_default_state()
            try:
                control_plane.persist_cache_atomic(cache_path, cache_state)
            except OSError as e:
                st.error(f"Auto-backtest cache bootstrap failed: {e}")
                return
        else:
            st.error(
                "Auto-backtest cache is invalid or unreadable. "
                "Reset the cache explicitly before running simulations."
            )
            if st.button("Reset Auto-Backtest Cache", type="primary"):
                reset_state = control_plane.create_default_state()
                try:
                    control_plane.persist_cache_atomic(cache_path, reset_state)
                except OSError as e:
                    st.error(f"Auto-backtest cache reset failed: {e}")
                    return
                st.success("Auto-backtest cache reset complete.")
                st.rerun()
            return
    else:
        cache_state = cache_load.state

    if cache_state is None:
        st.error("Auto-backtest cache unavailable after load/bootstrap.")
        return

    defaults = cache_state.config
    date_range = prices_wide.index
    n_assets = prices_wide.shape[1]
    latest_prices_date = date_range.max()

    # ── Sidebar Controls ────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Strategy Parameters")

        st.markdown("### Trend")
        ma_lookback = st.slider(
            "MA Lookback (days)",
            50,
            300,
            int(defaults.ma_lookback),
            step=10,
        )
        stop_lookback = st.slider(
            "Stop Lookback (days)",
            10,
            60,
            int(defaults.stop_lookback),
        )
        atr_period = st.slider(
            "ATR Period",
            10,
            40,
            int(defaults.atr_period),
        )

        st.markdown("### Sizing")
        default_vol_target_pct = int(round(float(defaults.vol_target) * 100))
        vol_target = st.slider(
            "Vol Target (%)",
            5,
            30,
            default_vol_target_pct,
        ) / 100.0
        max_positions = st.slider(
            "Max Positions",
            10,
            100,
            int(defaults.max_positions),
        )

        st.markdown("### Costs")
        default_cost_input_bps = round(float(defaults.cost_bps) * 10_000, 4)
        cost_bps_input = st.number_input(
            "Transaction Cost (bps)",
            value=default_cost_input_bps,
            min_value=0.0,
        )

        st.markdown("### Universe")
        min_price = st.number_input(
            "Min Price ($)",
            value=float(defaults.min_price),
            min_value=1.0,
        )

        st.markdown("---")
        run_btn = st.button("🚀 Run Simulation", width="stretch", type="primary")

    normalized_config = control_plane.normalize_config(
        {
            "ma_lookback": ma_lookback,
            "stop_lookback": stop_lookback,
            "atr_period": atr_period,
            "vol_target": vol_target,
            "max_positions": max_positions,
            "cost_bps": _cost_bps_input_to_decimal(float(cost_bps_input)),
            "cost_bps_unit": "rate",
            "min_price": min_price,
        }
    )
    auto_plan = control_plane.build_auto_backtest_plan(
        latest_prices_date=latest_prices_date,
        config=normalized_config,
        cache_state=cache_state,
    )

    # ── Info Bar ─────────────────────────────────────────────────────────────
    col_info1, col_info2, col_info3 = st.columns(3)
    col_info1.metric("📅 Date Range", f"{date_range.min().strftime('%Y-%m-%d')}  →  {date_range.max().strftime('%Y-%m-%d')}")
    col_info2.metric("📊 Universe Size", f"{n_assets:,} permnos")
    col_info3.metric("📈 Trading Days", f"{len(date_range):,}")
    if auto_plan.is_stale:
        st.caption("Auto-backtest cache is stale for current date/config; run simulation to refresh cache state.")
    else:
        st.caption("Auto-backtest cache is in sync with current date/config.")
    if auto_plan.show_already_attempted_caption:
        st.caption("Auto-backtest already attempted for the current date/config in this cache state.")

    # ── Simulation ──────────────────────────────────────────────────────────
    if run_btn:
        started_state = control_plane.mark_started(
            cache_state,
            latest_prices_date=latest_prices_date,
            config=normalized_config,
        )
        try:
            control_plane.persist_cache_atomic(cache_path, started_state)
        except OSError as e:
            st.error(f"Backtest cache start-state write failed: {e}")
            return

        try:
            with st.spinner("🔬 Running Strategy + Engine ..."):
                # Strategy Layer
                strategy = AdaptiveTrendStrategy(
                    atr_period=normalized_config.atr_period,
                    stop_lookback=normalized_config.stop_lookback,
                    vol_target=normalized_config.vol_target,
                    vol_lookback=20,
                    ma_lookback=normalized_config.ma_lookback,
                    max_positions=normalized_config.max_positions,
                    min_price=normalized_config.min_price,
                )

                # UNPACK TRIPLE RETURN (Weights, Regime, Reason)
                weights, regime_history, details = strategy.generate_weights(prices_wide, None, macro)

                # Engine Layer
                results = engine.run_simulation(weights, returns_wide, cost_bps=normalized_config.cost_bps)

            finished_state = control_plane.mark_finished(
                started_state,
                latest_prices_date=latest_prices_date,
                config=normalized_config,
                status="finished",
            )
            try:
                control_plane.persist_cache_atomic(cache_path, finished_state)
            except OSError as e:
                st.warning(f"Backtest cache completion write skipped: {e}")
        except Exception as e:
            failed_state = control_plane.mark_finished(
                started_state,
                latest_prices_date=latest_prices_date,
                config=normalized_config,
                status="failed",
            )
            try:
                control_plane.persist_cache_atomic(cache_path, failed_state)
            except OSError as write_err:
                st.warning(f"Backtest cache failure-state write skipped: {write_err}")
            st.error(f"Simulation failed: {e}")
            return

        # ── EXPLAINABILITY PANEL (The "Why") ───────────────────────────────
        st.markdown(
            f"""
            <div style='background: linear-gradient(135deg, #1a1a2e, #16213e);
                        border: 1px solid {details["color"]}; border-radius: 10px;
                        padding: 1rem; margin: 1rem 0;
                        display: flex; justify-content: space-around; align-items: center;'>
                <div style='text-align: center;'>
                    <span style='color: #888; font-size: 0.8rem; font-family: monospace;'>ADVISOR STATE</span><br/>
                    <span style='color: {details["color"]}; font-size: 1.2rem; font-weight: bold;
                                  font-family: monospace;'>{details["status"]}</span>
                </div>
                <div style='text-align: center;'>
                    <span style='color: #888; font-size: 0.8rem; font-family: monospace;'>REGIME MULTIPLIER</span><br/>
                    <span style='color: {details["color"]}; font-size: 1.4rem; font-weight: bold;
                                  font-family: monospace;'>{details["multiplier"]}x</span>
                </div>
                <div style='text-align: center;'>
                    <span style='color: #888; font-size: 0.8rem; font-family: monospace;'>REASON</span><br/>
                    <span style='color: #fff; font-size: 1.0rem; font-family: monospace;'>{details["reason"]}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Metrics ─────────────────────────────────────────────────────────
        cumulative = (1 + results["net_ret"]).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak

        # ── Equity Curve with Regime Overlay ────────────────────────────────
        st.markdown("### 📈 Equity Curve & Regime History")

        fig_eq = go.Figure()

        # Plot Regime Bands (Background)
        # We shade regions relative to the regime scalar (0.5=Red, 0.7=Yellow, 1.0=None)
        # To do this efficiently in Plotly efficiently without 6000 shapes, we plot a heatmap or colored lines
        # Here we overlay a small "Regime Strip" at the bottom
        fig_eq.add_trace(go.Heatmap(
            x=regime_history.index,
            y=[cumulative.min()] * len(regime_history),  # Position at bottom
            z=regime_history.values,
            colorscale=[[0, "#ff4444"], [0.5, "#ffaa00"], [1, "#00ff88"]],
            showscale=False,
            name="Regime",
            hoverinfo="skip",
            opacity=0.3,
        ))

        fig_eq.add_trace(go.Scatter(
            x=cumulative.index,
            y=cumulative.values,
            name="Net (after costs)",
            line=dict(color="#00ff88", width=2),
            fill="tozeroy",
            fillcolor="rgba(0,255,136,0.05)",
        ))
        fig_eq.update_layout(
            yaxis_type="log",
            yaxis_title="Cumulative Return (Log)",
            xaxis_title="Date",
            template="plotly_dark",
            height=450,
            title="Equity Curve (Green=Attack, Yellow=Caution, Red=Defense)",
            margin=dict(l=60, r=20, t=30, b=40),
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0.5)"),
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
        )
        st.plotly_chart(fig_eq, width="stretch")

        # ── Drawdown ────────────────────────────────────────────────────────
        st.markdown("### 🌊 Drawdown")
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown.values * 100,
            name="Drawdown %",
            line=dict(color="#ff4444", width=1),
            fill="tozeroy",
            fillcolor="rgba(255,68,68,0.15)",
        ))
        fig_dd.update_layout(
            yaxis_title="Drawdown %",
            template="plotly_dark",
            height=250,
            margin=dict(l=60, r=20, t=30, b=40),
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
        )
        st.plotly_chart(fig_dd, width="stretch")

        # 📊 Stats
        st.markdown("### 📊 Performance")
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Total Return", f"{(cumulative.iloc[-1] - 1):.1%}")
        mc2.metric("CAGR", f"{(cumulative.iloc[-1] ** (252 / len(cumulative)) - 1):.1%}")
        mc3.metric("Max DD", f"{drawdown.min():.1%}")
        mc4.metric("Turnover", f"{results['turnover'].mean():.1%}")
        mc5.metric("Total Cost", f"{results['cost'].sum() * 10000:.0f} bps")
    else:
        st.info("👈 Click **Run Simulation** to see the Advisor logic in action.")
