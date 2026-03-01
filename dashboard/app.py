import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Osiris Command Center")

# --- CUSTOM THEME / PAGE CONFIG ---
# We already used set_page_config above, but we can't do it twice, 
# so we ensure it's at the very top.
st.title("Phase 26: Osiris Alpha & Execution Dashboard")

# --- TAB SETUP ---
tab1, tab2 = st.tabs(["Alpha Diagnostic (The Brain)", "Live Execution (The Hands)"])

# --- TAB 1: THE ALPHA DIAGNOSTIC ---
with tab1:
    st.header("Global Supply Chain vs. QQQ")
    
    # 1. Load Macro Data (Osiris)
    try:
        macro_df = pd.read_parquet("data/processed/osiris_aligned_macro.parquet")
        # Ensure datetime index is set
        if 'fiscal_date' in macro_df.columns:
            macro_df.set_index('fiscal_date', inplace=True)
        elif 'closdate' in macro_df.columns:
            macro_df.set_index('closdate', inplace=True)
            
        # Ensure the Z-Score column exists (rename if needed based on your parquet file)
        # We look for 'z252' instead of 'zscore' based on the dataframe columns
        z_col = [c for c in macro_df.columns if 'z252' in c.lower() or 'zscore' in c.lower()]
        if z_col:
            z_score_col = z_col[0]
        else:
            st.error(f"Z-Score column not found. Available columns: {macro_df.columns}")
            st.stop()
            
    except Exception as e:
        st.error(f"Macro data error: {e}. Run the Osiris pipeline first.")
        st.stop()

    # 2. Load Market Data (QQQ)
    # Get range from macro data to match
    start_date = macro_df.index.min().strftime('%Y-%m-%d')
    end_date = datetime.today().strftime('%Y-%m-%d')
    
    with st.spinner("Downloading QQQ Data..."):
        qqq = yf.download("QQQ", start=start_date, end=end_date, progress=False)
        if isinstance(qqq.columns, pd.MultiIndex):
            if "QQQ" in qqq.columns.get_level_values(1):
                qqq = qqq.xs("QQQ", axis=1, level=1)
            else:
                qqq.columns = qqq.columns.get_level_values(0)
        elif isinstance(qqq, pd.DataFrame) and "QQQ" in qqq.columns:
             qqq = qqq["QQQ"]
    
    # 3. Create Dual-Axis Plot
    fig = go.Figure()
    
    # trace 1: QQQ Price (Left Axis)
    fig.add_trace(go.Scatter(
        x=qqq.index, 
        y=qqq['Close'], 
        name="QQQ Price", 
        line=dict(color='white', width=1.5),
        yaxis='y1'
    ))
    
    # trace 2: Osiris Z-Score (Right Axis)
    # We filter macro_df to match QQQ dates roughly
    common_idx = macro_df.index.intersection(qqq.index)
    aligned_macro = macro_df.loc[common_idx]
    
    colors = ['red' if pd.notna(v) and v < -1 else 'green' for v in aligned_macro[z_score_col]]
    
    fig.add_trace(go.Bar(
        x=aligned_macro.index, 
        y=aligned_macro[z_score_col],
        name="Inventory Z-Score (60d Lag)",
        marker_color=colors,
        yaxis='y2', 
        opacity=0.4
    ))
    
    # Layout with Dual Axis
    fig.update_layout(
        yaxis=dict(title="QQQ Price ($)", side='left', showgrid=False),
        yaxis2=dict(title="Z-Score", overlaying='y', side='right', range=[-3, 3], showgrid=True),
        template="plotly_dark",
        height=600,
        title="Visualizing the Failure: Where did the Z-Score fight the Bull Market?",
        legend=dict(x=0, y=1.1, orientation='h')
    )
    
    # Add Threshold Line
    fig.add_shape(type="line",
        x0=macro_df.index.min(), y0=-1, x1=macro_df.index.max(), y1=-1,
        line=dict(color="orange", width=2, dash="dash"),
        yref='y2'
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Diagnostic Metrics
    col1, col2, col3 = st.columns(3)
    latest_z = macro_df[z_score_col].iloc[-1]
    
    col1.metric("Latest Z-Score", f"{latest_z:.2f}", delta_color="normal")
    col2.metric("Regime", "BEARISH (Glut)" if latest_z < -1 else "BULLISH (Healthy)")
    col3.info(f"Data as of: {macro_df.index[-1].date()}")

# --- TAB 2: LIVE EXECUTION ---
with tab2:
    st.header("Paper Trading Control")
    st.info("Live Broker Connection Pending... Focus on Tab 1 Diagnosis first.")
    
    # Placeholder for future connection
    if st.button("Check Connection (Placeholder)"):
        st.write("Connecting to Alpaca...")
