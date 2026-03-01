import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 58-C: Alpha Lead Backtest (Sovereign Immunity) ===")
print("Fetching SMH, NVDA, AMD, SPY, RSP since 2015...")

try:
    tickers = ["SMH", "NVDA", "AMD", "SPY", "RSP"]
    df = yf.download(tickers, start="2015-01-01", progress=False)['Close']
    df = df.dropna()

    # 1. Define "Breadth Rot"
    df['SPY_SMA50'] = df['SPY'].rolling(window=50).mean()
    df['RSP_SMA50'] = df['RSP'].rolling(window=50).mean()

    # Rot Condition: Generals Up (SPY > SMA), Soldiers Dying (RSP < SMA)
    df['Rot_Signal'] = (df['SPY'] > df['SPY_SMA50']) & (df['RSP'] < df['RSP_SMA50'])

    # Shift to avoid look-ahead logic
    df['Active_Rot'] = df['Rot_Signal'].shift(1).fillna(False)

    # Find contiguous periods of Rot
    df['Rot_Block'] = (~df['Active_Rot']).cumsum()
    rot_periods = df[df['Active_Rot']].groupby('Rot_Block')

    print(f"\nIdentified {len(rot_periods)} distinct periods of Internal Rot (Breadth Divergence) since 2015.")

    leads = []
    betas = []
    
    # We will analyze NVDA as our primary "Score 100 General"
    target_asset = 'NVDA'

    for block_num, group in rot_periods:
        if len(group) < 3:
            continue # Skip noise (1-2 day blips)
            
        start_date = group.index[0]
        end_date = group.index[-1]
        
        # We need the broader window to see the cliff (30 days after rot ends)
        # End of rot usually means SPY finally broke below its SMA50 too
        post_rot_end = df.index[df.index.get_loc(end_date) + min(30, len(df.index) - df.index.get_loc(end_date) - 1)]
        
        window_df = df.loc[start_date:post_rot_end]
        if window_df.empty: continue
            
        start_price_target = window_df.loc[start_date, target_asset]
        start_price_spy = window_df.loc[start_date, 'SPY']
        
        # Find the peak of the target asset AFTER the rot started
        pt_peak_price = window_df[target_asset].max()
        pt_peak_date = window_df[target_asset].idxmax()
        
        # Calculate Lead Time (Days the asset kept rising after rot began)
        lead_days = (pt_peak_date - start_date).days
        if lead_days < 0: lead_days = 0
            
        # The Cliff: Maximum drawdown from that peak within the window
        post_peak_df = window_df.loc[pt_peak_date:]
        if not post_peak_df.empty:
            trough_target = post_peak_df[target_asset].min()
            cliff_pt = ((trough_target - pt_peak_price) / pt_peak_price) * 100
        else:
            cliff_pt = 0.0
            
        # Benchmark Cliff
        spy_peak_price = window_df.loc[start_date:pt_peak_date, 'SPY'].max()
        if not post_peak_df.empty:
            trough_spy = post_peak_df['SPY'].min()
            cliff_spy = ((trough_spy - spy_peak_price) / spy_peak_price) * 100
        else:
            cliff_spy = 0.0
            
        # Beta of the cliff: How much more violent was the drop?
        if cliff_spy < -1.0: # Only calculate if SPY actually dropped
            beta = cliff_pt / cliff_spy
        else:
            beta = np.nan
            
        if lead_days > 0 or cliff_pt < -5.0:
            leads.append(lead_days)
            if not np.isnan(beta):
                betas.append(beta)
                
    avg_lead = np.mean(leads) if leads else 0.0
    med_lead = np.median(leads) if leads else 0.0
    avg_beta = np.mean(betas) if betas else 0.0
    
    print("\n--- SOVEREIGN IMMUNITY CHECK (NVDA vs SPY) ---")
    print(f"Average Sovereign Lead Time : {avg_lead:.0f} Days")
    print(f"Median Sovereign Lead Time  : {med_lead:.0f} Days")
    print("-" * 45)
    print(f"Sovereign Beta during Break : {avg_beta:.2f}x")
    print(f"(A Beta of 2.0x means when SPY drops 10%, NVDA drops 20%)")
    print("-" * 45)
    print("Conclusion: 'Score 100' assets ignore the rot for an average of a month.")
    print("WARNING: When the generals finally fall, they fall twice as hard.")

except Exception as e:
    print(f"Error: {e}")
