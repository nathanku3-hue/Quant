import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 58-B: Breadth Divergence Backtest ===")
print("Fetching QQQ, SPY, RSP from 2003 to Present...")

try:
    # RSP Inception is approximately April 2003
    df = yf.download(['QQQ', 'SPY', 'RSP'], start='2003-05-01', progress=False)['Close']
    df = df.dropna()

    # Calculate Trends
    df['SPY_SMA50'] = df['SPY'].rolling(window=50).mean()
    df['RSP_SMA50'] = df['RSP'].rolling(window=50).mean()

    def determine_breadth(row):
        spy = row['SPY']
        spy_sma = row['SPY_SMA50']
        rsp = row['RSP']
        rsp_sma = row['RSP_SMA50']
        
        if pd.isna(spy_sma) or pd.isna(rsp_sma):
            return "HEALTHY"
            
        if rsp > rsp_sma:
            return "HEALTHY"
        elif (spy > spy_sma) and (rsp < rsp_sma):
            return "DIVERGENCE"
        else:
            return "WEAK"

    df['Breadth_Status'] = df.apply(determine_breadth, axis=1)

    # Shift signal to avoid look-ahead bias
    df['Exec_Breadth'] = df['Breadth_Status'].shift(1).fillna("HEALTHY")

    # The Execution Rule
    def map_exposure(status):
        if status == "HEALTHY":
            return 1.0
        elif status == "DIVERGENCE":
            return 0.8 # Trim
        else: # WEAK
            return 0.5 # Defensive

    df['Exposure'] = df['Exec_Breadth'].apply(map_exposure)

    # Calculate Returns
    df_test = df.dropna().copy()
    df_test['QQQ_Ret'] = df_test['QQQ'].pct_change().fillna(0)

    # Strategy Return
    df_test['Strat_Ret'] = df_test['Exposure'] * df_test['QQQ_Ret']

    # Equities
    df_test['QQQ_Equity'] = (1 + df_test['QQQ_Ret']).cumprod()
    df_test['Strat_Equity'] = (1 + df_test['Strat_Ret']).cumprod()

    def mdd(eq):
        peak = eq.cummax()
        return ((eq - peak) / peak).min() * 100

    qqq_mdd = mdd(df_test['QQQ_Equity'])
    strat_mdd = mdd(df_test['Strat_Equity'])

    qqq_ret = (df_test['QQQ_Equity'].iloc[-1] - 1) * 100
    strat_ret = (df_test['Strat_Equity'].iloc[-1] - 1) * 100

    print("\n[PERFORMANCE RESULTS: 2003 - PRESENT]")
    print(f"Buy & Hold QQQ Return : {qqq_ret:,.1f}% | MDD: {qqq_mdd:.1f}%")
    print(f"Breadth Governor Ret  : {strat_ret:,.1f}% | MDD: {strat_mdd:.1f}%")
    
    # Let's also check the specific cyclical drawdowns
    def eval_crisis(name, start, end):
        mask = (df_test.index >= start) & (df_test.index <= end)
        crisis = df_test.loc[mask].copy()
        if not crisis.empty:
            qqq_eq = (1 + crisis['QQQ_Ret']).cumprod()
            strat_eq = (1 + crisis['Strat_Ret']).cumprod()
            q_ret = (qqq_eq.iloc[-1] - 1) * 100
            s_ret = (strat_eq.iloc[-1] - 1) * 100
            print(f"[{name}] QQQ: {q_ret:>6.1f}% | Strategy: {s_ret:>6.1f}%")
            
    print("\n[CYCLICAL CRASHES (The Slow Bleeds)]")
    eval_crisis("2011 Downgrade (Jul-Oct)", "2011-07-01", "2011-10-31")
    eval_crisis("2015 China/Oil (Jul-Sep)", "2015-07-01", "2015-09-30")
    eval_crisis("2018 Volmageddon (Oct-Dec)", "2018-10-01", "2018-12-31")

except Exception as e:
    print(f"Error: {e}")
