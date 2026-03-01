import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=== Phase 64-B: Derivative Engine + Macro Gate Backtest ===")

# Decades and their rule of 100 (Forward looking testing)
decades = {
    "1990-2000 (Dot-Com)": ("1990-01-01", "2000-12-31", ["MSFT", "CSCO"]),
    "2000-2010 (Lost Decade)": ("2000-01-01", "2010-12-31", ["AAPL", "AMZN"]),
    "2010-2020 (Quantitative Easing)": ("2010-01-01", "2020-12-31", ["NVDA", "TSLA"])
}

LEAP_LEVERAGE = 2.5 

try:
    print("Fetching Macro Data (^TNX, VWEHX, VFISX)...")
    macro_df = yf.download(["^TNX", "VWEHX", "VFISX"], start="1988-01-01", progress=False)['Close']
    
    # Pre-calculate Macro Score
    macro_df['TNX_Vel'] = macro_df['^TNX'] - macro_df['^TNX'].shift(63)
    macro_df['Credit_Ratio'] = macro_df['VWEHX'] / macro_df['VFISX']
    macro_df['Ratio_SMA200'] = macro_df['Credit_Ratio'].rolling(200).mean()
    macro_df['Credit_Dist'] = ((macro_df['Credit_Ratio'] - macro_df['Ratio_SMA200']) / macro_df['Ratio_SMA200']) * 100
    
    def get_macro_score(row):
        vel = row['TNX_Vel']
        if pd.isna(vel): r_val = 50.0
        elif vel <= 0.0: r_val = 50.0
        elif vel >= 0.50: r_val = 0.0
        else: r_val = 50.0 * ((0.50 - vel) / 0.50)
            
        cdist = row['Credit_Dist']
        if pd.isna(cdist): c_val = 50.0
        elif cdist >= 4.65: c_val = 50.0
        elif cdist <= -2.0: c_val = 0.0
        else: c_val = 50.0 * ((cdist - (-2.0)) / (4.65 - (-2.0)))
            
        return r_val + c_val
        
    macro_df['Macro_Score'] = macro_df.apply(get_macro_score, axis=1)
    
except Exception as e:
    print("Macro fetch failed:", e)

for era, (start_dt, end_dt, tickers) in decades.items():
    print(f"\n--- {era} ERA ---")
    
    try:
        df_raw = yf.download(tickers, start=start_dt, end=end_dt, progress=False)['Close']
        if df_raw.empty: continue
        
        for t in tickers:
            df = pd.DataFrame()
            if isinstance(df_raw, pd.DataFrame):
                if t not in df_raw.columns: continue
                df['Close'] = df_raw[t].dropna()
            else:
                if t != tickers[0]: continue
                df['Close'] = df_raw.dropna()
                
            if len(df) < 100: continue
            
            # Align macro score
            df = df.join(macro_df['Macro_Score'])
            df['Macro_Score'] = df['Macro_Score'].ffill().fillna(50)
            
            df['Ret'] = df['Close'].pct_change()
            df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
            
            # Velocity and Convexity
            slope = df['EMA10'].diff()
            avg_slope = slope.rolling(window=20).mean()
            
            df['Prev_Close'] = df['Close'].shift(1)
            df['Prev_Slope'] = slope.shift(1)
            df['Prev_Avg_Slope'] = avg_slope.shift(1)
            df['Prev_Macro'] = df['Macro_Score'].shift(1)
            
            df_trade = df.loc[start_dt:].dropna().copy()
            if df_trade.empty: continue
            
            pos_mult = []
            
            for idx, row in df_trade.iterrows():
                p_slope = row['Prev_Slope']
                p_avg_slope = row['Prev_Avg_Slope']
                macro = row['Prev_Macro']
                
                if pd.isna(p_avg_slope) or p_avg_slope <= 0:
                    convexity = 1.0
                else:
                    convexity = p_slope / p_avg_slope
                    
                # 3-Pillar Constraint
                if macro >= 80 and convexity <= 1.5:
                    geo_mult = LEAP_LEVERAGE
                elif macro >= 50:
                    geo_mult = 1.0 # Stock fallback
                else:
                    geo_mult = 0.0 # Cash
                    
                pos_mult.append(geo_mult)
                
            df_trade['Leverage'] = pos_mult
            theta_decay = 0.10 / 252
            
            # Returns
            df_trade['Strat_Ret'] = (df_trade['Leverage'] * df_trade['Ret']) - (theta_decay * (df_trade['Leverage'] > 1))
            
            bh_eq = (1 + df_trade['Ret'].fillna(0)).cumprod()
            strat_eq = (1 + df_trade['Strat_Ret'].fillna(0)).cumprod()
            
            bh_ret = (bh_eq.iloc[-1] - 1) * 100
            strat_ret = (strat_eq.iloc[-1] - 1) * 100
            
            def calc_mdd(eq):
                peak = eq.cummax()
                return ((eq - peak) / peak).min() * 100
                
            bh_mdd = calc_mdd(bh_eq)
            strat_mdd = calc_mdd(strat_eq)
            
            print(f"[{t}] Stock B&H: {bh_ret:>8.1f}% (MDD: {bh_mdd:>6.1f}%) | 3-Pillar LEAP Strat: {strat_ret:>8.1f}% (MDD: {strat_mdd:>6.1f}%) | Alpha: {strat_ret - bh_ret:>+8.1f}%")
            
    except Exception as e:
        print(f"Error for {era}: {e}")
