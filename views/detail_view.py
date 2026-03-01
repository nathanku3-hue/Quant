"""
Terminal Zero — Detail View [FR-026 + D-28 JIT Patch]
Renders: Chart + Action Report card for a single ticker drill-down.
Auto-patches stale data from Yahoo before rendering.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data import fundamentals_updater
from strategies.investor_cockpit import InvestorCockpitStrategy
from views.jit_patch import is_ticker_stale, jit_patch_ticker


def _go_scanner():
    st.session_state.cockpit_view = "scanner"
    st.session_state.selected_ticker = None


def render_detail_view(
    prices_wide,
    macro,
    ticker_map,
    fundamentals_wide,
    k_stop,
    z_entry,
    use_adaptive,
    use_alpha_engine=False,
):
    """Detail view: single-ticker chart + action report card."""

    permno = st.session_state.selected_ticker
    tkr_name = ticker_map.get(permno, f"Permno {permno}")

    # ── Back button ─────────────────────────────────────────────────────────
    st.button("← Back to Scanner", on_click=_go_scanner)
    st.subheader(f"🔬 Signal Monitor: {tkr_name}")

    if permno not in prices_wide.columns:
        st.error(f"Ticker {tkr_name} ({permno}) not found in loaded data.")
        return

    # ── Fundamentals freshness indicator + manual refresh (95-day rule) ─────
    latest_row = None
    latest_df = fundamentals_wide.get("latest") if isinstance(fundamentals_wide, dict) else None
    if hasattr(latest_df, "index") and permno in latest_df.index:
        row = latest_df.loc[permno]
        latest_row = row.iloc[0] if hasattr(row, "iloc") and getattr(row, "ndim", 1) > 1 else row

    ticker_upper = str(tkr_name).upper()
    is_quality_bypass = ticker_upper in InvestorCockpitStrategy.SKIP_QUALITY_CHECK

    if is_quality_bypass:
        st.caption("ℹ️ ETF/Index instrument: fundamentals quality gate is bypassed.")
    else:
        rel = pd.NaT
        days_old = None
        if latest_row is not None:
            rel = pd.to_datetime(latest_row.get("release_date"), errors="coerce")
            days_old = pd.to_numeric(latest_row.get("days_since_release"), errors="coerce")
            if pd.notna(rel) and pd.notna(days_old) and days_old <= 95:
                st.caption(f"✅ Fundamentals fresh as of {rel.date()} ({int(days_old)} days old).")
            else:
                if pd.notna(rel) and pd.notna(days_old):
                    st.warning(f"⚠️ Fundamentals may be stale: last release {rel.date()} ({int(days_old)} days old).")
                else:
                    st.warning("⚠️ Fundamentals missing for this ticker.")
        else:
            st.warning("⚠️ Fundamentals snapshot missing for this ticker.")

        if st.button("🔄 Check for New Earnings", key=f"fund_refresh_{permno}"):
            with st.spinner(f"Fetching fundamentals for {tkr_name}..."):
                result = fundamentals_updater.run_update(scope="Custom", custom_list=tkr_name)
            if result.get("success"):
                st.success(f"Fundamentals updated for {tkr_name}. Reloading...")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Fundamentals refresh failed for {tkr_name}.")

    # ── JIT Patch: auto-fetch if stale [D-28] ──────────────────────────────
    if is_ticker_stale(prices_wide, permno):
        prices_wide = jit_patch_ticker(tkr_name, permno, prices_wide)

    prices_one = prices_wide[[permno]].dropna(how="all")
    if prices_one.empty:
        st.error(f"No price data for {tkr_name}.")
        return

    fundamentals_one = None
    if isinstance(fundamentals_wide, dict):
        fundamentals_one = {}
        for k in ("quality_pass", "roic", "revenue_growth_yoy"):
            v = fundamentals_wide.get(k)
            if hasattr(v, "reindex"):
                fundamentals_one[k] = v.reindex(index=prices_one.index, columns=[permno])
        fundamentals_one["ticker_map"] = {int(permno): tkr_name}

    # ── Run strategy ────────────────────────────────────────────────────────
    strat = InvestorCockpitStrategy(
        k_stop=k_stop, z_entry=z_entry,
        use_dynamic_params=use_adaptive, green_candle=True, use_alpha_engine=use_alpha_engine,
    )
    _, _, details = strat.generate_weights(prices_one, fundamentals_one, macro)

    chart_col, card_col = st.columns([2, 1])

    # ═══════════════ CARD ═══════════════
    with card_col:
        _render_card(permno, tkr_name, prices_wide, details,
                     k_stop, z_entry, use_adaptive)

    # ═══════════════ CHART ══════════════
    with chart_col:
        _render_chart(permno, tkr_name, prices_wide, strat, details,
                      k_stop, z_entry, use_adaptive)


def _render_card(t, tkr_name, prices_wide, details, k_stop, z_entry, use_adaptive):
    series = prices_wide[t].dropna()
    price = series.iloc[-1]

    k_val = details["k_values"].get(t, k_stop)
    z_val = details["z_values"].get(t, z_entry)
    stop_price = details["stop_prices"].get(t, 0)
    buy_val = details["buy_thresholds"].get(t, 0)

    # Vol rank badge
    vol_badge = ""
    if use_adaptive and details.get("vol_rank"):
        vr = details["vol_rank"].get(t, 0.5)
        if vr > 0.75:
            vol_badge = f"<span style='color:#ff6b6b;font-size:0.7em'>HIGH VOL ({vr:.0%})</span>"
        elif vr < 0.25:
            vol_badge = f"<span style='color:#69db7c;font-size:0.7em'>LOW VOL ({vr:.0%})</span>"
        else:
            vol_badge = f"<span style='color:#aaa;font-size:0.7em'>MID VOL ({vr:.0%})</span>"

    # State
    sd = details.get("states", {}).get(t, {
        "state": "HOLD", "desc": "🛡️ Trend Healthy",
        "color": "#00ff88", "support": stop_price,
    })
    action, reason, color, support = sd["state"], sd["desc"], sd["color"], sd["support"]

    if action in ("HOLD", "BUY", "WATCH"):
        buf = (price / stop_price - 1) if stop_price > 0 else 0
        line1 = f"🛡️ Floor: ${stop_price:.2f} ({buf:+.1%} buffer)"
        if action == "BUY":
            line2 = "✅ <span style='color:#00ff88'>Buy Zone confirmed.</span>"
        elif action == "WATCH":
            line2 = f"👀 <span style='color:#FFD700'>Dip near ${buy_val:.2f}. Wait for green candle.</span>"
        else:
            line2 = f"💎 Buy Zone: ${buy_val:.2f} <span style='color:#888'>(z={z_val:.2f})</span>"
    elif action == "AVOID":
        line1 = f"⛔ Broken Stop: ${stop_price:.2f} <span style='color:#888'>(k={k_val:.2f})</span>"
        line2 = f"📍 <span style='color:#FFD700'>Wait for ${support:.2f} support</span>"
    else:
        line1 = f"⛔ Broken Stop: ${stop_price:.2f} <span style='color:#888'>(k={k_val:.2f})</span>"
        line2 = f"📍 <span style='color:#aaa'>Support near ${support:.2f}.</span>"

    # Conviction
    cv = int(details.get("conviction", {}).get(t, 0))
    q_pass = int(details.get("quality_pass", {}).get(t, 1))
    q_cap = bool(details.get("quality_cap_applied", {}).get(t, False))
    ct = int(details.get("cv_trend", {}).get(t, 0))
    cvl = int(details.get("cv_value", {}).get(t, 0))
    cm = int(details.get("cv_macro", 0))
    cmo = int(details.get("cv_mom", {}).get(t, 0))

    cv_label, cv_color = ("🔥 HIGH", "#00ff88") if cv >= 8 else \
        ("✅ MOD", "#FFD700") if cv >= 5 else ("⚠️ LOW", "#ff6b6b")

    rz_v = details.get("metrics", {}).get("rz_score", {}).get(t, 0)
    er_v = details.get("metrics", {}).get("er_score", {}).get(t, 0)

    dims = [
        f"{'✅' if ct == 3 else '❌'} Trend",
        f"{'✅' if cvl == 3 else '⚠️' if cvl == 1 else '❌'} Val(RZ:{rz_v:.1f})",
        f"{'✅' if cm == 2 else '⚠️' if cm == 1 else '❌'} Macro",
        f"{'✅' if cmo == 2 else '⚠️' if cmo == 1 else '❌'} Mom(ER:{er_v:.2f})",
    ]
    bp = cv * 10
    if q_cap:
        q_line = "<span style='color:#ff6b6b'>⚠️ Quality: FAIL (Score Capped)</span>"
        q_cap_line = (
            "<div style='font-size:0.68em;color:#ff6b6b'>Quality gate failed. "
            "Conviction is capped at 5/10.</div>"
        )
    elif q_pass == 1:
        q_line = "<span style='color:#69db7c'>✅ Quality: PASS (Profitable & Growing)</span>"
        q_cap_line = ""
    else:
        q_line = "<span style='color:#ff6b6b'>⚠️ Quality: FAIL (Unprofitable or Shrinking)</span>"
        q_cap_line = ""

    st.markdown("#### 📋 Action Report")
    st.markdown(f"""
    <div style='border:1px solid #333;padding:10px;margin-bottom:5px;
                border-radius:5px;border-left:3px solid {color}'>
        <div style='display:flex;justify-content:space-between'>
            <b>{tkr_name}</b>
            <span style='color:{color};font-weight:bold'>{action}</span>
        </div>
        <div style='font-size:0.9em;color:#aaa'>Price: ${price:.2f} {vol_badge}</div>
        <div style='font-size:0.8em;margin-top:5px'>
           {line1}<br/>{line2}<br/>
           <i style='color:{color}'>{reason}</i>
        </div>
        <div style='margin-top:6px;padding-top:6px;border-top:1px solid #333'>
            <div style='display:flex;justify-content:space-between;font-size:0.75em'>
                <span style='color:{cv_color};font-weight:bold'>{cv_label} ({cv}/10)</span>
                <span style='color:#666'>Conviction</span>
            </div>
            <div style='background:#222;border-radius:3px;height:6px;margin:3px 0'>
                <div style='background:{cv_color};width:{bp}%;height:100%;
                            border-radius:3px;transition:width 0.3s'></div>
            </div>
            <div style='font-size:0.65em;color:#777'>{' · '.join(dims)}</div>
            <div style='margin-top:4px;font-size:0.72em'>{q_line}</div>
            {q_cap_line}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_chart(permno, tkr_name, prices_wide, strat, details,
                  k_stop, z_entry, use_adaptive):
    k_t = details["k_values"].get(permno, k_stop)
    z_t = details["z_values"].get(permno, z_entry)
    lbl = "Adaptive" if use_adaptive else "Fixed"
    st.markdown(
        f"#### Signal Visualizer: {tkr_name}  "
        f"<span style='font-size:0.8em;color:#888'>({lbl}: k={k_t:.2f}, z={z_t:.2f})</span>",
        unsafe_allow_html=True,
    )

    signals = strat.get_signals(prices_wide[[permno]])
    sp = prices_wide[permno].dropna().iloc[-252:]
    ss = signals["stop_level"][permno].reindex(sp.index)
    sb = signals["buy_zone"][permno].reindex(sp.index)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sp.index, y=sp.values, name="Price",
        line=dict(color="white", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=ss.index, y=ss.values, name=f"Stop (k={k_t:.1f})",
        line=dict(color="#ff4444", width=1, dash="dash"),
    ))
    fig.add_trace(go.Scatter(
        x=sb.index, y=sb.values, name=f"Buy Zone (z={z_t:.1f})",
        line=dict(color="#00ff88", width=1, dash="dot"),
    ))
    fig.update_layout(
        template="plotly_dark", height=500,
        xaxis_title="Date", yaxis_title="Price ($)",
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(x=0, y=1, orientation="h"),
    )
    st.plotly_chart(fig, width="stretch")
