import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 57-G: The Weight Optimizer (Climate vs. Weather) ===")
print("Fetching ^TNX, VWEHX, VFISX, ^VIX, and QQQ since 1995...")

try:
    tickers = ["QQQ", "^TNX", "VWEHX", "VFISX", "^VIX"]
    df = yf.download(tickers, start="1995-01-01", progress=False)['Close']
    df = df.dropna()

    # --- Step 1: Calculate Macro Score (Phase 57-F Calibration) ---
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

    # --- Step 2: Calculate VIX Score ---
    # Map VIX 12 -> 100, VIX 35 -> 0
    def calc_vix(row):
        v = row['^VIX']
        if pd.isna(v): return 50.0
        if v <= 12.0: return 100.0
        if v >= 35.0: return 0.0
        return 100.0 * ((35.0 - v) / (35.0 - 12.0))

    df['VIX_Score'] = df.apply(calc_vix, axis=1)

    # Shift scores by 1 day
    df['Exec_Macro'] = df['Macro_Score'].shift(1).fillna(50)
    df['Exec_VIX'] = df['VIX_Score'].shift(1).fillna(50)

    df_test = df[df.index >= "2000-01-01"].copy()
    df_test['QQQ_Ret'] = df_test['QQQ'].pct_change().fillna(0)

    weights = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    results = []

    def calc_drawdown(eq):
        peak = eq.cummax()
        return ((eq - peak) / peak).min() * 100

    def calc_sharpe(ret):
        if ret.std() == 0: return 0
        return (ret.mean() / ret.std()) * np.sqrt(252)

    base_ret = 0

    for w in weights:
        v_w = 1.0 - w
        # Step 3: Composite Score
        comp = (df_test['Exec_Macro'] * w) + (df_test['Exec_VIX'] * v_w)
        
        # Kill Gate Constraint: If Macro < 40, Composite = 0
        comp = np.where(df_test['Exec_Macro'] < 40, 0.0, comp)
        
        # Exposure
        exposure = comp / 100.0
        
        strat_ret = exposure * df_test['QQQ_Ret']
        equity = (1 + strat_ret).cumprod()
        
        total_r = (equity.iloc[-1] - 1) * 100
        mdd = calc_drawdown(equity)
        sharpe = calc_sharpe(strat_ret)
        
        if w == 1.0:
            base_ret = total_r
            
        results.append({
            'Macro_W': w,
            'VIX_W': v_w,
            'Return(%)': total_r,
            'MDD(%)': mdd,
            'Sharpe': sharpe
        })

    res_df = pd.DataFrame(results)
    print("\n[SWEEP RESULTS]")
    print(res_df.to_string(index=False, float_format="%.2f"))

    best_idx = res_df['Return(%)'].idxmax()
    best_res = res_df.loc[best_idx]
    opt_w_macro = best_res['Macro_W']
    opt_w_vix = best_res['VIX_W']

    improvement = best_res['Return(%)'] - base_ret
    pct_improvement = (improvement / base_ret) * 100 if base_ret != 0 else 0

    print(f"\nOptimal Weight Split: Macro {opt_w_macro:.2f} / VIX {opt_w_vix:.2f}")
    if pct_improvement > 0:
        print(f"Improvement over Macro-Only: +{pct_improvement:.1f}%")
    else:
        print(f"Improvement over Macro-Only: {pct_improvement:.1f}% (No improvement)")

except Exception as e:
    print(f"Error: {e}")
