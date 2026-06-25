import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=== Phase 63-A: Tighten vs. Sell Backtest ===")
print("Fetching NVDA and PLTR since 2023...")

try:
    assets = {
        "NVDA": {"Cluster": "Sprinter", "Kinetic_Exit": 8.8},
        "PLTR": {"Cluster": "Scout", "Kinetic_Exit": 12.3}
    }
    
    df_raw = yf.download(list(assets.keys()), start="2023-01-01", progress=False)['Close']
    df_high = yf.download(list(assets.keys()), start="2023-01-01", progress=False)['High']
    df_low = yf.download(list(assets.keys()), start="2023-01-01", progress=False)['Low']
    
    for t, config in assets.items():
        print(f"\nEvaluating {t} ({config['Cluster']}) - Kinetic Limit: {config['Kinetic_Exit']}%")
        
        df = pd.DataFrame()
        if isinstance(df_raw, pd.DataFrame) and t in df_raw.columns:
            df['Close'] = df_raw[t]
            df['High'] = df_high[t]
            df['Low'] = df_low[t]
        elif isinstance(df_raw, pd.Series):
            df['Close'] = df_raw
            df['High'] = df_high
            df['Low'] = df_low
            
        df['Ret'] = df['Close'].pct_change()
        
        # EMA21 and Stretch
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['Stretch'] = ((df['Close'] - df['EMA21']) / df['EMA21']) * 100
        
        # ATR (14-day)
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()
        
        # Shift features
        df['Prev_Close'] = df['Close'].shift(1)
        df['Prev_EMA21'] = df['EMA21'].shift(1)
        df['Prev_Stretch'] = df['Stretch'].shift(1)
        df['Prev_ATR'] = df['ATR'].shift(1)
        
        df_trade = df.loc["2023-04-01":].copy()
        kin_limit = config['Kinetic_Exit']
        
        # STRATEGY A (Hard Sell)
        pos_a = []
        curr_a = 1.0 # Assume start long
        for idx, row in df_trade.iterrows():
            if pd.isna(row['Prev_Stretch']):
                pos_a.append(curr_a)
                continue
                
            if curr_a == 1.0 and row['Prev_Stretch'] >= kin_limit:
                curr_a = 0.0
            elif curr_a == 0.0 and row['Prev_Close'] <= row['Prev_EMA21']:
                curr_a = 1.0
                
            pos_a.append(curr_a)
            
        df_trade['Pos_A'] = pos_a
        df_trade['Ret_A'] = df_trade['Pos_A'] * df_trade['Ret']
        
        # STRATEGY B (The Sovereign Trail)
        pos_b = []
        curr_b = 1.0
        tight_mode = False
        active_stop = 0.0
        
        for idx, row in df_trade.iterrows():
            if pd.isna(row['Prev_Stretch']):
                pos_b.append(curr_b)
                continue
                
            # Morning Entry Check
            if curr_b == 0.0 and row['Prev_Close'] <= row['Prev_EMA21']:
                curr_b = 1.0
                tight_mode = False
                active_stop = 0.0
                
            # Record today's exposure
            pos_b.append(curr_b)
            
            # EOD Stop/Exit Check
            if curr_b == 1.0:
                if row['Prev_Stretch'] >= kin_limit:
                    tight_mode = True
                    
                atr_mult = 1.5 if tight_mode else 3.0
                day_stop = row['Prev_Close'] - (atr_mult * row['Prev_ATR'])
                if day_stop > active_stop:
                    active_stop = day_stop
                    
                # Did we breach the stop today?
                if row['Close'] < active_stop:
                    curr_b = 0.0 # Will be out tomorrow
                    tight_mode = False
                    active_stop = 0.0
                    
        df_trade['Pos_B'] = pos_b
        df_trade['Ret_B'] = df_trade['Pos_B'] * df_trade['Ret']
        
        eq_a = (1 + df_trade['Ret_A']).cumprod()
        eq_b = (1 + df_trade['Ret_B']).cumprod()
        
        ret_a = (eq_a.iloc[-1] - 1) * 100
        ret_b = (eq_b.iloc[-1] - 1) * 100
        
        def calc_mdd(eq):
            peak = eq.cummax()
            return ((eq - peak) / peak).min() * 100
            
        mdd_a = calc_mdd(eq_a)
        mdd_b = calc_mdd(eq_b)
        
        print(f"Strategy A (Hard Sell) Return : {ret_a:>7.1f}% | MDD: {mdd_a:>5.1f}%")
        print(f"Strategy B (Trailing) Return  : {ret_b:>7.1f}% | MDD: {mdd_b:>5.1f}%")
        print(f"Alpha Captured (B over A)     : {ret_b - ret_a:>+7.1f}%")
        
except Exception as e:
    print(f"Error: {e}")
