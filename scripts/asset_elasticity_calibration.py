import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 61-C: Asset Elasticity Calibration (Terminal Stretch Engine) ===")
print("Fetching Data: NVDA, VRT, AMD, PLTR, ^VIX, ^TNX, VWEHX, VFISX since 2022...")

try:
    tickers = ["NVDA", "VRT", "AMD", "PLTR", "^VIX", "^TNX", "VWEHX", "VFISX"]
    # 2 Year History (2022-Present covers the entire structural AI bull and 2022 bear)
    df = yf.download(tickers, start="2022-01-01", progress=False)['Close']
    df = df.dropna()
    
    # 1. Macro Safety Check (Phase 57-F)
    df['Yield_Velocity'] = df['^TNX'] - df['^TNX'].shift(63)
    df['Credit_Ratio'] = df['VWEHX'] / df['VFISX']
    df['Ratio_SMA200'] = df['Credit_Ratio'].rolling(window=200).mean()
    df['Credit_Distance'] = ((df['Credit_Ratio'] - df['Ratio_SMA200']) / df['Ratio_SMA200']) * 100

    def calc_macro(row):
        vel = row['Yield_Velocity']
        if pd.isna(vel): r_score = 50.0
        elif vel <= 0.0: r_score = 50.0
        elif vel >= 0.50: r_score = 0.0
        else: r_score = 50.0 * ((0.50 - vel) / 0.50)
            
        cdist = row['Credit_Distance']
        if pd.isna(cdist): c_score = 50.0
        elif cdist >= 4.65: c_score = 50.0
        elif cdist <= -2.0: c_score = 0.0
        else: c_score = 50.0 * ((cdist - (-2.0)) / (4.65 - (-2.0)))
            
        return r_score + c_score

    df['Macro_Score'] = df.apply(calc_macro, axis=1)

    assets = ["NVDA", "VRT", "AMD", "PLTR"]
    results = []

    print("\n--- TERMINAL STRETCH CONSTANTS (95th Pct) ---")
    
    # We will test trading strategy on data from 2023-01-01 to give 1 year for rolling means/volatility burn-in
    trade_start = "2023-01-01"
    
    for t in assets:
        df_t = df[[t, "^VIX", "Macro_Score"]].copy()
        df_t['Ret'] = df_t[t].pct_change()
        
        # Calculate trailing 3-month volatility to assign the Dynamic Rail
        df_t['Vol_3M'] = df_t['Ret'].rolling(63).std() * np.sqrt(252)
        
        # Assign Dynamic Rail based on Dashboard Phase 56 logic
        def assign_rail(row):
            v = row['Vol_3M']
            # We can't use current row for EWM cleanly row-by-row in pandas without iterrows or custom rolling.
            # Instead we calculate all rails and select.
            return v
            
        # Calc all rails
        df_t['EMA10'] = df_t[t].ewm(span=10, adjust=False).mean()
        df_t['EMA21'] = df_t[t].ewm(span=21, adjust=False).mean()
        df_t['SMA50'] = df_t[t].rolling(50).mean()
        
        df_t['Dynamic_Rail'] = np.where(df_t['Vol_3M'] > 0.40, df_t['EMA10'],
                               np.where(df_t['Vol_3M'] > 0.25, df_t['EMA21'], df_t['SMA50']))
                               
        df_t['Stretch_Pct'] = ((df_t[t] - df_t['Dynamic_Rail']) / df_t['Dynamic_Rail']) * 100
        
        # Calculate 95th Percentile Stretch (Using 2-year history)
        p95_stretch = np.percentile(df_t['Stretch_Pct'].dropna(), 95)
        print(f"{t:>5s}: {p95_stretch:>5.1f}%")
        
        # --- Backtest: Max Alpha Logic ---
        # Shift data to avoid lookahead
        df_t['Prev_Stretch'] = df_t['Stretch_Pct'].shift(1)
        df_t['Prev_VIX'] = df_t['^VIX'].shift(1)
        df_t['Prev_Macro'] = df_t['Macro_Score'].shift(1)
        df_t['Prev_Price'] = df_t[t].shift(1)
        df_t['Prev_Rail'] = df_t['Dynamic_Rail'].shift(1)
        
        # Filter for trading period
        df_trade = df_t[df_t.index >= trade_start].copy()
        
        # Execution Rules
        # Exit: Current_Stretch >= Terminal_Stretch AND VIX < 14 -> Cash (0 exposure)
        # Entry: Price <= Dynamic_Rail AND Macro_Score > 70 -> Buy (1 exposure)
        # Else: Hold previous state
        
        positions = []
        curr_pos = 1.0 # Start fully invested
        
        for idx, row in df_trade.iterrows():
            stretch = row['Prev_Stretch']
            vix = row['Prev_VIX']
            macro = row['Prev_Macro']
            price = row['Prev_Price']
            rail = row['Prev_Rail']
            
            # Exit Logic (Local Top)
            if stretch >= p95_stretch and vix < 14.0:
                curr_pos = 0.0
            # Entry Logic (Local Dip)
            elif price <= rail and macro > 70.0:
                curr_pos = 1.0
                
            positions.append(curr_pos)
            
        df_trade['Position'] = positions
        
        # Calculate Returns
        df_trade['Strat_Ret'] = df_trade['Position'] * df_trade['Ret']
        
        bh_eq = (1 + df_trade['Ret']).cumprod()
        strat_eq = (1 + df_trade['Strat_Ret']).cumprod()
        
        bh_total = (bh_eq.iloc[-1] - 1) * 100
        strat_total = (strat_eq.iloc[-1] - 1) * 100
        
        def calc_mdd(eq):
            peak = eq.cummax()
            return ((eq - peak) / peak).min() * 100
            
        bh_mdd = calc_mdd(bh_eq)
        strat_mdd = calc_mdd(strat_eq)
        
        time_in_mkt = (df_trade['Position'] == 1.0).mean() * 100
        
        results.append({
            'Asset': t,
            'Stretch_Const': p95_stretch,
            'B&H_Ret': bh_total,
            'B&H_MDD': bh_mdd,
            'Strat_Ret': strat_total,
            'Strat_MDD': strat_mdd,
            'Time_In_Mkt': time_in_mkt
        })
        
    print("\n--- MAX ALPHA EXECUTION BACKTEST (2023-2026) ---")
    res_df = pd.DataFrame(results)
    
    for idx, row in res_df.iterrows():
        alpha = row['Strat_Ret'] - row['B&H_Ret']
        print(f"[{row['Asset']}] Return: Strat {row['Strat_Ret']:>6.1f}% vs B&H {row['B&H_Ret']:>6.1f}% | Alpha: {alpha:>+6.1f}% | Exposure: {row['Time_In_Mkt']:.0f}% | MDD: Strat {row['Strat_MDD']:.1f}% vs B&H {row['B&H_MDD']:.1f}%")

except Exception as e:
    print(f"Error: {e}")
