"""
Terminal Zero — Scanner View [FR-026 v3]
Toggle between Top Market Candidates and My Watchlist.
Type-to-Search bar with popularity-sorted results (latest price proxy).
"""
import streamlit as st
import json, os
import pandas as pd

from strategies.investor_cockpit import InvestorCockpitStrategy

WATCHLIST_FILE = "./data/watchlist.json"


def _load_wl():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            return json.load(f)
    return {"defaults": ["AAPL", "MSFT", "SPY"], "user_added": []}


def _get_wl_tickers():
    d = _load_wl()
    return sorted(set(d.get("defaults", []) + d.get("user_added", [])))


def _score_badge(score):
    if score >= 9:
        return f"<span style='color:#00ff88;font-weight:bold'>🔥 {score}/10</span>"
    elif score >= 7:
        return f"<span style='color:#FFD700;font-weight:bold'>✅ {score}/10</span>"
    elif score >= 5:
        return f"<span style='color:#aaa'>⚠️ {score}/10</span>"
    return f"<span style='color:#666'>💤 {score}/10</span>"


def _go_detail(permno):
    st.session_state.cockpit_view = "detail"
    st.session_state.selected_ticker = permno


def render_scanner_view(
    prices_wide,
    macro,
    ticker_map,
    fundamentals_wide,
    k_stop,
    z_entry,
    use_adaptive,
    use_alpha_engine=False,
):
    """Scanner view: toggle + type-to-search + tables."""

    strat = InvestorCockpitStrategy(
        k_stop=k_stop, z_entry=z_entry,
        use_dynamic_params=use_adaptive, green_candle=True, use_alpha_engine=use_alpha_engine,
    )

    # ── Top bar: Toggle + Search ────────────────────────────────────────────
    top_left, top_right = st.columns([2, 1])

    with top_left:
        view_mode = st.radio(
            "View",
            ["📈 Top Market Candidates", "📋 My Watchlist"],
            horizontal=True,
            label_visibility="collapsed",
        )

    with top_right:
        _render_search_bar(ticker_map, prices_wide)

    # ── Render selected view ────────────────────────────────────────────────
    if view_mode == "📈 Top Market Candidates":
        _render_scan_table(strat, prices_wide, macro, ticker_map, fundamentals_wide)
    else:
        _render_watchlist_table(strat, prices_wide, macro, ticker_map, fundamentals_wide)


# ── Type-to-Search Bar [FR-026 v3] ─────────────────────────────────────────

def _render_search_bar(ticker_map, prices_wide):
    """Dropdown search sorted by popularity (latest price)."""
    # Invert map: ticker -> permno
    t2p = {v: k for k, v in ticker_map.items()}

    # Get latest prices for sorting (Forward fill to handle ragged end dates)
    latest = prices_wide.ffill().iloc[-1]
    
    # Validation: ensure latest.index and t2p values are compatible types for lookup
    # Convert index to native python ints to be safe
    # (Assuming permnos are integers)
    latest_dict = latest.to_dict() # {permno: price} - robust type handling

    # Filter tickers that are in the data
    valid_tickers = [t for t in t2p if t2p[t] in latest_dict and pd.notna(latest_dict[t2p[t]])]
    
    # Sort by Price Descending (Popularity Proxy)
    # AAPL ($250) > A ($130) > AG ($6)
    valid_tickers.sort(key=lambda t: latest_dict.get(t2p[t], 0), reverse=True)

    # Use native selectbox (fixed layout) with placeholder
    # Setting index=None makes it empty by default (acts like a search input)
    placeholder = "— Search ticker —"
    options = [placeholder] + valid_tickers
    selection = st.selectbox(
        "🔍 Search",
        options=options,
        # format_func removed as requested ("I don't desire the price") 
        index=0,
        label_visibility="collapsed",
        key="search_dropdown"
    )

    if selection and selection != placeholder:
        # Navigate to detail view
        permno = t2p[selection]
        _go_detail(permno)
        st.session_state["search_dropdown"] = placeholder
        st.rerun()


# ── Scan Table ──────────────────────────────────────────────────────────────

def _render_scan_table(strat, prices_wide, macro, ticker_map, fundamentals_wide):
    """Top Market Candidates — best available names from full universe."""
    ctrl1, ctrl2, ctrl3 = st.columns([1.4, 1.2, 1.2])
    with ctrl1:
        mode_label = st.radio(
            "Scanner Mode",
            ["Top Market Candidates", "Fresh Catalysts"],
            horizontal=True,
            label_visibility="collapsed",
            key="scanner_mode",
        )
    with ctrl2:
        hide_risk = st.checkbox("Hide earnings risk (<5d)", value=False, key="scanner_hide_risk")
    with ctrl3:
        blackout_days = st.selectbox("Blackout days", [3, 5, 7, 10], index=1, key="scanner_blackout_days")

    scan_mode = "fresh_catalysts" if mode_label == "Fresh Catalysts" else "default"
    with st.spinner("🔭 Scanning universe..."):
        scan_df, gate = strat.scan_universe(
            prices_wide,
            macro,
            fundamentals_wide=fundamentals_wide,
            top_n=5,
            mode=scan_mode,
            earnings_blackout_days=int(blackout_days),
            return_metrics=True,
        )

    if hide_risk and not scan_df.empty and "earnings_risk" in scan_df.columns:
        scan_df = scan_df[~scan_df["earnings_risk"].fillna(False)].copy()

    st.caption(
        f"Scanning {gate['universe_size']:,} stocks... "
        f"Trend: {gate['trend_pass']:,} pass | "
        f"Quality: {gate['quality_pass']:,} pass | "
        f"Catalyst: {gate.get('catalyst_pass', 0):,} pass | "
        f"Candidates: {gate['final_survivors']:,} | "
        f"Earnings Risk: {gate.get('earnings_risk', 0):,} | "
        f"Showing: {len(scan_df):,}"
    )

    if scan_df.empty:
        if scan_mode == "fresh_catalysts":
            st.info("💤 No fresh catalysts in the current universe window.")
        else:
            st.info("💤 No data available for scanning.")
        return

    sector_map = fundamentals_wide.get("sector_map", {}) if isinstance(fundamentals_wide, dict) else {}

    h = st.columns([1, 1.2, 1.4, 1, 1, 1, 1, 1.4, 0.6])
    for col, lbl in zip(
        h,
        ["**Score**", "**Ticker**", "**Sector**", "**Price**", "**Δ1D**", "**RZ**", "**ER**", "**Earnings**", ""],
    ):
        col.markdown(lbl)

    for _, row in scan_df.iterrows():
        pm = row["permno"]
        tkr = ticker_map.get(pm, str(pm))
        sector = sector_map.get(int(pm), "Unknown")
        sc = int(row["score"])
        pct = row["pct_1d"]
        pc = "#00ff88" if pct >= 0 else "#ff4444"
        dte = pd.to_numeric(row.get("days_to_earnings"), errors="coerce")
        dse = pd.to_numeric(row.get("days_since_earnings"), errors="coerce")
        erisk_raw = row.get("earnings_risk", False)
        erisk = bool(erisk_raw) if pd.notna(erisk_raw) else False
        if pd.notna(dte) and dte >= 0:
            if erisk:
                earnings_txt = f"<span style='color:#ff6b6b;font-weight:bold'>⚠️ {int(dte)}d</span>"
            else:
                earnings_txt = f"T-{int(dte)}d"
        elif pd.notna(dse) and dse >= 0:
            earnings_txt = f"+{int(dse)}d ago"
        else:
            earnings_txt = "N/A"

        c = st.columns([1, 1.2, 1.4, 1, 1, 1, 1, 1.4, 0.6])
        c[0].markdown(_score_badge(sc), unsafe_allow_html=True)
        c[1].markdown(f"**{tkr}**")
        c[2].markdown(sector)
        c[3].markdown(f"${row['price']:.2f}")
        c[4].markdown(f"<span style='color:{pc}'>{pct:+.1%}</span>", unsafe_allow_html=True)
        c[5].markdown(f"{row['rz']:.1f}")
        c[6].markdown(f"{row['er']:.2f}")
        c[7].markdown(earnings_txt, unsafe_allow_html=True)
        c[8].button("🔍", key=f"scan_{pm}", on_click=_go_detail, args=(pm,))


# ── Watchlist Table ─────────────────────────────────────────────────────────

def _render_watchlist_table(strat, prices_wide, macro, ticker_map, fundamentals_wide):
    """My Watchlist — top 5 by conviction from watchlist tickers."""
    rev = {v: k for k, v in ticker_map.items()}
    wl_tickers = _get_wl_tickers()
    wl_permnos = [rev[t] for t in wl_tickers if t in rev]
    wl_permnos = [p for p in wl_permnos if p in prices_wide.columns]

    if not wl_permnos:
        st.info("No watchlist tickers found in loaded universe.")
        return

    prices_wl = prices_wide[wl_permnos].dropna(how="all")
    fundamentals_wl = None
    if isinstance(fundamentals_wide, dict):
        fundamentals_wl = {}
        for k in ("quality_pass", "roic", "revenue_growth_yoy"):
            v = fundamentals_wide.get(k)
            if isinstance(v, pd.DataFrame):
                fundamentals_wl[k] = v.reindex(index=prices_wl.index, columns=wl_permnos)
        fundamentals_wl["ticker_map"] = {int(p): ticker_map.get(p, str(p)) for p in wl_permnos}

    with st.spinner("📋 Scoring watchlist..."):
        _, _, wl_det = strat.generate_weights(prices_wl, fundamentals_wl, macro)

    sector_map = fundamentals_wide.get("sector_map", {}) if isinstance(fundamentals_wide, dict) else {}
    items = []
    for p in wl_permnos:
        cv = int(wl_det.get("conviction", {}).get(p, 0))
        si = wl_det.get("states", {}).get(p, {})
        s = prices_wide[p].dropna()
        if s.empty:
            continue
        px = s.iloc[-1]
        prev = s.iloc[-2] if len(s) >= 2 else px
        pct = (px - prev) / prev if prev else 0
        q_pass = int(wl_det.get("quality_pass", {}).get(p, 1))
        items.append({
            "permno": p, "score": cv, "price": px, "pct_1d": pct,
            "state": si.get("state", "—"), "color": si.get("color", "#888"),
            "quality_pass": q_pass,
            "sector": sector_map.get(int(p), "Unknown"),
        })

    items.sort(key=lambda x: x["score"], reverse=True)
    top5 = items[:5]

    st.caption(f"Watchlist: {len(wl_permnos)} tickers · Top 5 by conviction")

    h = st.columns([1, 1.2, 1.6, 1, 1, 1.2, 1.2, 0.6])
    for col, lbl in zip(h, ["**Score**", "**Ticker**", "**Sector**", "**Price**", "**Δ1D**", "**Quality**", "**State**", ""]):
        col.markdown(lbl)

    for it in top5:
        pm = it["permno"]
        tkr = ticker_map.get(pm, str(pm))
        pc = "#00ff88" if it["pct_1d"] >= 0 else "#ff4444"

        c = st.columns([1, 1.2, 1.6, 1, 1, 1.2, 1.2, 0.6])
        c[0].markdown(_score_badge(it["score"]), unsafe_allow_html=True)
        c[1].markdown(f"**{tkr}**")
        c[2].markdown(it["sector"])
        c[3].markdown(f"${it['price']:.2f}")
        c[4].markdown(f"<span style='color:{pc}'>{it['pct_1d']:+.1%}</span>", unsafe_allow_html=True)
        q_badge = (
            "<span style='color:#69db7c;font-weight:bold'>PASS</span>"
            if it["quality_pass"] == 1
            else "<span style='color:#ff6b6b;font-weight:bold'>FAIL</span>"
        )
        c[5].markdown(q_badge, unsafe_allow_html=True)
        c[6].markdown(
            f"<span style='color:{it['color']};font-weight:bold'>{it['state']}</span>",
            unsafe_allow_html=True,
        )
        c[7].button("🔍", key=f"wl_{pm}", on_click=_go_detail, args=(pm,))
