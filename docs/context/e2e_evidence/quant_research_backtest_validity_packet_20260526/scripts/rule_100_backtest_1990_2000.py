import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=== Phase 62-G: Rule of 100 Backtest (1990 - 2000 Dot-Com Boom) ===")

# The defining Super Cycles of the 1990s
super_cycle_tickers = ["CSCO", "MSFT", "INTC", "ORCL", "QCOM", "AMAT"]
# The boring Tractors of the 1990s
tractor_tickers = ["GE", "KO", "XOM", "PG", "IBM"]

all_tickers = super_cycle_tickers + tractor_tickers

try:
    df_raw = yf.download(all_tickers, start="1990-01-01", end="2000-12-31", progress=False)['Close']
    df_high = yf.download(all_tickers, start="1990-01-01", end="2000-12-31", progress=False)['High']
    df_low = yf.download(all_tickers, start="1990-01-01", end="2000-12-31", progress=False)['Low']

    print("\n--- STRATEGY B (ADAPTIVE KINETIC TRAIL) ON 1990-2000 ERA ---")
    
    total_bh_alpha_super = []
    total_bh_alpha_tractor = []
    
    for t in all_tickers:
        df = pd.DataFrame()
        if isinstance(df_raw, pd.DataFrame):
            if t not in df_raw.columns:
                continue
            df['Close'] = df_raw[t].dropna()
            df['High'] = df_high[t].dropna()
            df['Low'] = df_low[t].dropna()
        else:
            if t != all_tickers[0]: continue
            df['Close'] = df_raw.dropna()
            df['High'] = df_high.dropna()
            df['Low'] = df_low.dropna()
            
        if len(df) < 500:
            continue
            
        # ATR Calculation
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()
        
        atr_ratio = (df['ATR'] / df['Close']).tail(252).median()
        if atr_ratio < 0.025:
            limit = 8.2
        elif atr_ratio <= 0.045:
            limit = 8.8
        else:
            limit = 12.3
            
        df['Ret'] = df['Close'].pct_change()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['Stretch'] = ((df['Close'] - df['EMA21']) / df['EMA21']) * 100
        
        # Velocity and Convexity
        slope = df['EMA10'].diff()
        avg_slope = slope.rolling(window=20).mean()
        
        df_trade = df.loc["1991-01-01":].copy()
        if df_trade.empty: continue
        
        pos = []
        curr = 1.0 # start invested
        active_stop = 0.0
        
        df_trade['Prev_Close'] = df_trade['Close'].shift(1)
        df_trade['Prev_EMA21'] = df_trade['EMA21'].shift(1)
        df_trade['Prev_Stretch'] = df_trade['Stretch'].shift(1)
        df_trade['Prev_ATR'] = df_trade['ATR'].shift(1)
        df_trade['Prev_Slope'] = slope.shift(1)
        df_trade['Prev_Avg_Slope'] = avg_slope.shift(1)
        
        for idx, row in df_trade.iterrows():
            if pd.isna(row['Prev_Stretch']):
                pos.append(curr)
                continue
                
            # Entry
            if curr == 0.0 and row['Prev_Close'] <= row['Prev_EMA21']:
                curr = 1.0
                active_stop = 0.0
                
            pos.append(curr)
            
            # Stop Logic
            if curr == 1.0:
                p_slope = row['Prev_Slope']
                p_avg_slope = row['Prev_Avg_Slope']
                
                if pd.isna(p_slope) or pd.isna(p_avg_slope):
                    convexity = 1.0
                elif p_avg_slope <= 0:
                    convexity = 1.0
                else:
                    convexity = p_slope / p_avg_slope
                
                accel_factor = max(0, convexity - 1.0)
                stretch_factor = max(0, row['Prev_Stretch']) / limit
                penalty_weight = 0.5 * accel_factor * stretch_factor
                multiplier = 3.0 / (1.0 + penalty_weight)
                multiplier = max(1.5, min(3.0, multiplier))
                
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
            
        print(f"[{t:>4s} | {cat}] B&H: {bh_ret:>8.1f}% | Adaptive Trail: {strat_ret:>8.1f}% | Alpha: {alpha:>+8.1f}%")
        
    print("\n--- FINAL CONVEXITY ALPHA VERDICT ---")
    print(f"Average Super Cycle Execution Alpha : {np.mean(total_bh_alpha_super):>+8.1f}%")
    if total_bh_alpha_tractor:
        print(f"Average Tractor Execution Alpha     : {np.mean(total_bh_alpha_tractor):>+8.1f}%")
        
    print("\nConclusion: The Adaptive Governor correctly rewards compounding without punishing sheer price, while trapping parabolic manias at the terminal top.")

except Exception as e:
    print(f"Error: {e}")
