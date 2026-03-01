import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 58-A: The Crash Autopsy (Finding the Exhaustion Signal) ===")

target_windows = {
    "2011 US Downgrade": {"start": "2011-04-01", "crash_start": "2011-07-22", "end": "2011-10-31"},
    "2015 China/Oil": {"start": "2015-04-01", "crash_start": "2015-08-15", "end": "2015-09-30"},
    "2018 Volmageddon/QT": {"start": "2018-07-01", "crash_start": "2018-10-01", "end": "2018-12-31"},
}

try:
    # yfinance often struggles with ^PCR and ^ADD (CBOE/NYSE specific indices). 
    # We will use universally reliable proxies to measure the exact same physical phenomena:
    # 1. DX-Y.NYB = Dollar Index (Liquidity)
    # 2. RSP / SPY = Breadth Divergence (Equal Weight vs Cap Weight)
    
    tickers = ["QQQ", "DX-Y.NYB", "SPY", "RSP"]
    print(f"Fetching Data: {tickers} from 2010 to Present...")
    df = yf.download(tickers, start="2010-01-01", progress=False)['Close']
    df = df.dropna()
    
    # --- Feature Engineering ---
    # 1. Breadth Proxy (Equal Weight vs Cap Weight)
    # If RSP/SPY is falling while SPY is rising, breadth is dying (rotting from inside)
    df['Breadth_Ratio'] = df['RSP'] / df['SPY']
    df['Breadth_SMA50'] = df['Breadth_Ratio'].rolling(50).mean()
    df['Breadth_Diverging'] = df['Breadth_Ratio'] < df['Breadth_SMA50']
    
    # 2. Dollar Index (Global Liquidity Constriction)
    df['DXY_Level'] = df['DX-Y.NYB']
    df['DXY_Velocity'] = df['DX-Y.NYB'].pct_change(63) * 100 # ~3 month % change
    
    print("\n--- AUTOPSY RESULTS ---")
    
    for name, dates in target_windows.items():
        print(f"\n[{name}]")
        mask = (df.index >= dates["start"]) & (df.index <= dates["end"])
        window_df = df.loc[mask]
        
        if window_df.empty:
            continue
            
        pre_crash_mask = (window_df.index < dates["crash_start"])
        pre_crash_df = window_df.loc[pre_crash_mask]
        
        if pre_crash_df.empty:
            continue
            
        # Find the exact local top of the market
        peak_date = pre_crash_df['QQQ'].idxmax()
        peak_qqq = pre_crash_df.loc[peak_date, 'QQQ']
        
        # Snapshot the indicators on the exact day of the market top
        breadth_at_peak_diverging = pre_crash_df.loc[peak_date, 'Breadth_Diverging']
        breadth_status = "LEAD [RED] (Diverged before top)" if breadth_at_peak_diverging else "LAG (Missed)"
        
        dxy_vel_at_peak = pre_crash_df.loc[peak_date, 'DXY_Velocity']
        # Historically, a >4% 90-day spike in DXY signals global liquidity drying up
        dxy_status = f"LEAD [RED] (Spiked +{dxy_vel_at_peak:.1f}%)" if dxy_vel_at_peak > 4.0 else f"LAG (Flat/Down +{dxy_vel_at_peak:.1f}%)"
        
        # Calculate actual crash drawdown
        crash_df = window_df.loc[window_df.index >= peak_date]
        trough_qqq = crash_df['QQQ'].min()
        drawdown = ((trough_qqq - peak_qqq) / peak_qqq) * 100
            
        print(f"QQQ Peak Date: {peak_date.strftime('%Y-%m-%d')} | Crash Drawdown: {drawdown:.1f}%")
        print(f"Breadth (A/D Proxy): {breadth_status}")
        print(f"Dollar Index (DXY):  {dxy_status}")
        
    print("\n[CONCLUSION]")
    print("Select the Exhastion Sensor that consistently led the market top.")

except Exception as e:
    print(f"Error: {e}")
