import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 57-F: Macro Score Calibration (Dynamic Dial Tuning) ===")
print("Fetching 10Y Yield, Credit Proxies (VWEHX/VFISX), and QQQ...")

try:
    # 1. The Data
    # HYG/IEI inception is too late (2007) for full history, so we stick to VWEHX / VFISX (High Yield vs Treasury proxy back to 1995)
    tickers = ["QQQ", "^TNX", "VWEHX", "VFISX"]
    df = yf.download(tickers, start="1995-01-01", progress=False)['Close']
    df = df.dropna()
    
    # 2. Factor Distribution Analysis
    # Rate Velocity
    df['Yield_Velocity'] = df['^TNX'] - df['^TNX'].shift(63)
    
    # Credit Distance
    df['Credit_Ratio'] = df['VWEHX'] / df['VFISX']
    df['Ratio_SMA200'] = df['Credit_Ratio'].rolling(window=200).mean()
    df['Credit_Distance'] = ((df['Credit_Ratio'] - df['Ratio_SMA200']) / df['Ratio_SMA200']) * 100
    
    # Clean up NA to run percentiles
    dist_df = df.dropna().copy()
    dist_df = dist_df[dist_df.index >= "2000-01-01"]
    
    # Calculate Percentiles
    rate_90th = np.percentile(dist_df['Yield_Velocity'], 90)
    rate_10th = np.percentile(dist_df['Yield_Velocity'], 10) # Generally negative (rates falling)
    
    cred_90th = np.percentile(dist_df['Credit_Distance'], 90)
    cred_10th = np.percentile(dist_df['Credit_Distance'], 10)
    
    print(f"\n[FACTOR DISTRIBUTIONS (2000-Present)]")
    print(f"Rate Velocity 90th Pct: +{rate_90th:.2f} bps (Max Damage Threshold is likely ~0.50)")
    print(f"Credit Distance 90th Pct: +{cred_90th:.2f}% (Max Safety Threshold)")
    print(f"Credit Distance 10th Pct: {cred_10th:.2f}% (Panic Threshold)")
    
    # 3. Dynamic Scoring Engine Backtest
    # We will use the empirical 90th/10th percentiles to clamp the ranges.
    
    MAX_CREDIT_DIST = cred_90th
    MIN_CREDIT_DIST = max(-2.0, cred_10th) # Let's floor it at -2.0% for absolute panic
    
    MAX_RATE_VEL = 0.50 # proven kill zone
    MIN_RATE_VEL = 0.0  # flattening or falling is good
    
    def calc_score(row):
        # 1. Rate Component (0-50, where 50 is best/safe)
        vel = row['Yield_Velocity']
        if vel <= MIN_RATE_VEL:
            r_score = 50.0
        elif vel >= MAX_RATE_VEL:
            r_score = 0.0
        else:
            # Linear interpolation inverse
            factor = (MAX_RATE_VEL - vel) / (MAX_RATE_VEL - MIN_RATE_VEL)
            r_score = 50.0 * factor
            
        # 2. Credit Component (0-50, where 50 is best/safe)
        cdist = row['Credit_Distance']
        if pd.isna(cdist): return 50.0 # burn in period
        
        if cdist >= MAX_CREDIT_DIST:
            c_score = 50.0
        elif cdist <= MIN_CREDIT_DIST:
            c_score = 0.0
        else:
            # Linear interpolation
            factor = (cdist - MIN_CREDIT_DIST) / (MAX_CREDIT_DIST - MIN_CREDIT_DIST)
            c_score = 50.0 * factor
            
        return r_score + c_score

    df['Macro_Score'] = df.apply(calc_score, axis=1)
    
    # Shift score by 1 to prevent look-ahead
    df['Executing_Score'] = df['Macro_Score'].shift(1).fillna(50)
    
    # Map to exposure
    def map_exposure(score):
        if score >= 80: return 1.25 # All in + leverage
        if score >= 50: return 1.00 # Standard deploy
        if score >= 30: return 0.50 # Defensive
        return 0.0 # Cash
        
    df['Exposure'] = df['Executing_Score'].apply(map_exposure)
    
    # Calculate Strategy Returns
    df_test = df[df.index >= "2000-01-01"].copy()
    df_test['QQQ_Return'] = df_test['QQQ'].pct_change()
    
    # Dynamic Strat
    df_test['Dyn_Strategy_Return'] = df_test['Exposure'] * df_test['QQQ_Return']
    df_test['Dyn_Equity'] = (1 + df_test['Dyn_Strategy_Return']).cumprod()
    
    # Old Binary Strat (Phase 57-C)
    df_test['Binary_Signal'] = np.where((df_test['Yield_Velocity'].shift(1) > 0.50) | (df_test['Credit_Distance'].shift(1) < 0), 0, 1)
    df_test['Bin_Strategy_Return'] = df_test['Binary_Signal'] * df_test['QQQ_Return']
    df_test['Bin_Equity'] = (1 + df_test['Bin_Strategy_Return']).cumprod()
    
    qqq_eq = (1 + df_test['QQQ_Return']).cumprod()
    
    def mdd(eq):
        peak = eq.cummax()
        return ((eq - peak)/peak).min() * 100
        
    print("\n[SCORING BACKTEST RESULTS: 2000 - PRESENT]")
    print(f"Optimal Credit Distance Threshold: +{MAX_CREDIT_DIST:.2f}% (Calibrated Max Score)")
    print(f"Panic Credit Distance Threshold: {MIN_CREDIT_DIST:.2f}% (Calibrated Zero Score)")
    print("-" * 50)
    print(f"Buy & Hold ROI     : {(qqq_eq.iloc[-1]-1)*100:,.1f}% | MDD: {mdd(qqq_eq):.1f}%")
    print(f"Binary Switch ROI  : {(df_test['Bin_Equity'].iloc[-1]-1)*100:,.1f}% | MDD: {mdd(df_test['Bin_Equity']):.1f}%")
    print(f"Dynamic Score ROI  : {(df_test['Dyn_Equity'].iloc[-1]-1)*100:,.1f}% | MDD: {mdd(df_test['Dyn_Equity']):.1f}%")
    
except Exception as e:
    print(f"Error: {e}")
