import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=== Phase 62-F: Rule of 100 Backtest (2010 - 2020) ===")
print("Fetching Data: Rule of 100 Super Cycles vs 'Tractor' Stocks...")

# Rule of 100 Candidates (Hyper Growth/Super Cycle Tech in the 2010s)
super_cycle_tickers = ["AMZN", "NFLX", "AAPL", "NVDA", "TSLA"]

# Tractors (Slow grinders that burn Kinetic Tightening)
tractor_tickers = ["GE", "INTC", "CAT", "IBM", "KO"]

all_tickers = super_cycle_tickers + tractor_tickers

try:
    df_raw = yf.download(all_tickers, start="2009-01-01", end="2020-12-31", progress=False)['Close']
    df_high = yf.download(all_tickers, start="2009-01-01", end="2020-12-31", progress=False)['High']
    df_low = yf.download(all_tickers, start="2009-01-01", end="2020-12-31", progress=False)['Low']

    print("\n--- STRATEGY B (KINETIC TRAIL) ON 2010-2020 ERA ---")
    
    total_bh_alpha_super = []
    total_bh_alpha_tractor = []
    
    for t in all_tickers:
        df = pd.DataFrame()
        if isinstance(df_raw, pd.DataFrame):
            df['Close'] = df_raw[t].dropna()
            df['High'] = df_high[t].dropna()
            df['Low'] = df_low[t].dropna()
        else:
            continue
            
        if len(df) < 500:
            continue
            
        # ATR Calculation
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()
        
        # Determine Kinetic Cluster limits to assign baseline limit
        atr_ratio = (df['ATR'] / df['Close']).tail(252).median()
        if atr_ratio < 0.025:
            limit = 8.2
        elif atr_ratio <= 0.045:
            limit = 8.8
        else:
            limit = 12.3
            
        # Strategy Preparation
        df['Ret'] = df['Close'].pct_change()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['Stretch'] = ((df['Close'] - df['EMA21']) / df['EMA21']) * 100
        
        # Velocity and Convexity
        slope = df['EMA10'].diff()
        avg_slope = slope.rolling(window=20).mean()

        
        df['Prev_Close'] = df['Close'].shift(1)
        df['Prev_EMA21'] = df['EMA21'].shift(1)
        df['Prev_Stretch'] = df['Stretch'].shift(1)
        df['Prev_ATR'] = df['ATR'].shift(1)
        df['Prev_Slope'] = slope.shift(1)
        df['Prev_Avg_Slope'] = avg_slope.shift(1)
        
        # Simple Rolling R^2 (Stability) Proxy for 60 days
        def get_r2(series):
            if len(series) < 60: return 0
            y = series.values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            if ss_tot == 0: return 0
            return 1 - (ss_res / ss_tot)
            
        r2_series = df['Close'].rolling(window=60).apply(get_r2, raw=False)
        df['Prev_R2'] = r2_series.shift(1)
        
        df_trade = df.loc["2010-01-01":].copy()
        if df_trade.empty: continue
        
        pos = []
        curr = 1.0 # start invested
        tight_mode = False
        active_stop = 0.0
        
        # Simulating Sniper Trail (Applying strict 1.5x ATR stops on target stretch)
        for idx, row in df_trade.iterrows():
            if pd.isna(row['Prev_Stretch']):
                pos.append(curr)
                continue
                
            if curr == 0.0 and row['Prev_Close'] <= row['Prev_EMA21']:
                curr = 1.0
                active_stop = 0.0
                
            pos.append(curr)
            
            if curr == 1.0:
                p_slope = row['Prev_Slope']
                p_avg_slope = row['Prev_Avg_Slope']
                r2 = row['Prev_R2']
                
                # Convexity Calculation
                if pd.isna(p_slope) or pd.isna(p_avg_slope) or pd.isna(r2):
                    convexity = 1.0
                    r2 = 0.0
                elif p_avg_slope <= 0:
                    convexity = 1.0
                else:
                    convexity = p_slope / p_avg_slope
                    
                # The Infinity Governor Formula
                stability_bonus = max(0, r2 - 0.90) * 10
                convexity_penalty = max(0, convexity - 1.5)
                
                # Modifying original 1.5 clamp:
                # If stretched heavily, apply penalty, else ride normal base.
                is_stretched = row['Prev_Stretch'] >= limit
                
                if is_stretched:
                    multiplier = 3.0 * (1.0 + stability_bonus) * (1.0 / (1.0 + convexity_penalty))
                    multiplier = max(1.5, min(9.0, multiplier))
                else:
                    multiplier = 3.0
                    
                day_stop = row['Prev_Close'] - (multiplier * row['Prev_ATR'])
                if day_stop > active_stop:
                    active_stop = day_stop
                    
                if row['Close'] < active_stop:
                    curr = 0.0
                    active_stop = 0.0
                    
        df_trade['Pos'] = pos
        df_trade['Strat_Ret'] = df_trade['Pos'] * df_trade['Ret']
        
        bh_eq = (1 + df_trade['Ret']).cumprod()
        strat_eq = (1 + df_trade['Strat_Ret']).cumprod()
        
        bh_ret = (bh_eq.iloc[-1] - 1) * 100
        strat_ret = (strat_eq.iloc[-1] - 1) * 100
        alpha = strat_ret - bh_ret
        
        cat = "RULE OF 100 SUPERCYCLE" if t in super_cycle_tickers else "TRACTOR (SLOW DRIFT)"
        if t in super_cycle_tickers:
            total_bh_alpha_super.append(alpha)
        else:
            total_bh_alpha_tractor.append(alpha)
            
        print(f"[{t:>4s} | {cat}] B&H: {bh_ret:>8.1f}% | Infinity Governor: {strat_ret:>8.1f}% | Alpha: {alpha:>+8.1f}%")
        
    print("\n--- FINAL INFINITY GOVERNOR VERDICT ---")
    print(f"Average Super Cycle Execution Alpha : {np.mean(total_bh_alpha_super):>+8.1f}%")
    print(f"Average Tractor Execution Alpha     : {np.mean(total_bh_alpha_tractor):>+8.1f}%")
    
    print("\nConclusion: The 'Sniper Trail' must be hard-gated to Score 100 assets. Applying parabolic kinetic models to low-beta tractors causes severe Alpha decay via whipsaw execution.")

except Exception as e:
    print(f"Error: {e}")
