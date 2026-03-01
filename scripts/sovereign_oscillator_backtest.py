import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 58-D: Sovereign Oscillator Backtest (The Annual Panic) ===")
print("Fetching Data: QQQ, ^VIX, ^TNX, VWEHX, VFISX since 1995...")

try:
    tickers = ["QQQ", "^VIX", "^TNX", "VWEHX", "VFISX"]
    df = yf.download(tickers, start="1995-01-01", progress=False)['Close']
    df = df.dropna()
    
    # 1. Macro Score Calculation (Phase 57-F Thresholds)
    df['Yield_Velocity'] = df['^TNX'] - df['^TNX'].shift(63)
    df['Credit_Ratio'] = df['VWEHX'] / df['VFISX']
    df['Ratio_SMA200'] = df['Credit_Ratio'].rolling(window=200).mean()
    df['Credit_Distance'] = ((df['Credit_Ratio'] - df['Ratio_SMA200']) / df['Ratio_SMA200']) * 100

    MAX_CREDIT_DIST = 4.65
    MIN_CREDIT_DIST = -2.0
    MAX_RATE_VEL = 0.50
    MIN_RATE_VEL = 0.0

    def calc_macro(row):
        vel = row['Yield_Velocity']
        if pd.isna(vel): r_score = 50.0
        elif vel <= MIN_RATE_VEL: r_score = 50.0
        elif vel >= MAX_RATE_VEL: r_score = 0.0
        else: r_score = 50.0 * ((MAX_RATE_VEL - vel) / (MAX_RATE_VEL - MIN_RATE_VEL))
            
        cdist = row['Credit_Distance']
        if pd.isna(cdist): c_score = 50.0
        elif cdist >= MAX_CREDIT_DIST: c_score = 50.0
        elif cdist <= MIN_CREDIT_DIST: c_score = 0.0
        else: c_score = 50.0 * ((cdist - MIN_CREDIT_DIST) / (MAX_CREDIT_DIST - MIN_CREDIT_DIST))
            
        return r_score + c_score

    df['Macro_Score'] = df.apply(calc_macro, axis=1)
    
    # 2. RSI (14-day) on QQQ
    delta = df['QQQ'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI_14'] = 100 - (100 / (1 + rs))
    
    # 3. State Management
    # State A (The Top): VIX < 13 AND RSI > 70 -> Sell 20% to Cash (Exposure 0.8)
    # State B (The Dip): VIX > 30 AND RSI < 35 AND Macro_Score > 70 -> Buy 125% Leverage (Exposure 1.25)
    # Default: 1.0 (assuming baseline 100% long)
    
    # Shift to prevent lookahead
    df_eval = df.copy()
    df_eval['VIX_Prev'] = df_eval['^VIX'].shift(1)
    df_eval['RSI_Prev'] = df_eval['RSI_14'].shift(1)
    df_eval['Macro_Prev'] = df_eval['Macro_Score'].shift(1)
    
    df_test = df_eval[df_eval.index >= "2000-01-01"].copy()
    df_test['QQQ_Ret'] = df_test['QQQ'].pct_change().fillna(0)
    
    def determine_exposure(row):
        v = row['VIX_Prev']
        rsi = row['RSI_Prev']
        macro = row['Macro_Prev']
        
        if pd.isna(v) or pd.isna(rsi):
            return 1.0
            
        if v < 13.0 and rsi > 70.0:
            return 0.80
        elif v > 30.0 and rsi < 35.0 and macro > 70.0:
            return 1.25
        else:
            return 1.00

    df_test['Exposure'] = df_test.apply(determine_exposure, axis=1)
    
    # Analyze Buy Triggers (State B)
    # Forward 20-day return metric for success rate
    df_test['Fwd_20d_Ret'] = df_test['QQQ'].shift(-20) / df_test['QQQ'] - 1
    
    buy_signals = df_test[df_test['Exposure'] == 1.25]
    total_buys = len(buy_signals)
    success_buys = len(buy_signals[buy_signals['Fwd_20d_Ret'] > 0])
    success_rate = (success_buys / total_buys * 100) if total_buys > 0 else 0
    
    # Calculate returns
    df_test['Strat_Ret'] = df_test['Exposure'] * df_test['QQQ_Ret']
    
    df_test['QQQ_Equity'] = (1 + df_test['QQQ_Ret']).cumprod()
    df_test['Strat_Equity'] = (1 + df_test['Strat_Ret']).cumprod()

    qqq_ret = (df_test['QQQ_Equity'].iloc[-1] - 1) * 100
    strat_ret = (df_test['Strat_Equity'].iloc[-1] - 1) * 100
    
    alpha = strat_ret - qqq_ret
    
    def calc_mdd(eq):
        peak = eq.cummax()
        return ((eq - peak) / peak).min() * 100
        
    print("\n[PERFORMANCE RESULTS: 2000 - PRESENT]")
    print(f"Buy & Hold QQQ Return : {qqq_ret:,.1f}% | MDD: {calc_mdd(df_test['QQQ_Equity']):.1f}%")
    print(f"Oscillator Strategy   : {strat_ret:,.1f}% | MDD: {calc_mdd(df_test['Strat_Equity']):.1f}%")
    print("-" * 50)
    print(f"Total Alpha Generated vs. Buy & Hold: {alpha:+,.1f}%")
    print("-" * 50)
    print(f"Number of 'VIX > 30' Dip Buys Triggered : {total_buys}")
    print(f"Success Rate of the 'VIX > 30' Trigger  : {success_rate:.1f}% (Positive 20d Forward Return)")

except Exception as e:
    print(f"Error: {e}")
