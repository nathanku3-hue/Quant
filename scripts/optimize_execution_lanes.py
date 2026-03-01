import pandas as pd
import yfinance as yf
import numpy as np
import json
import os
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def run_strategy_a(df):
    """
    Sprinter/Momentum
    Entry: Price > 20-Day High (Breakout).
    Exit: Trailing Stop 5%.
    """
    in_pos = False
    entry_price = 0
    highest_price = 0
    daily_returns = []
    
    # Pre-calculate indicators to avoid lookahead
    high_20 = df['High'].rolling(20).max().shift(1)
    
    for i in range(len(df)):
        if pd.isna(high_20.iloc[i]):
            daily_returns.append(0.0)
            continue
            
        price = df['Close'].iloc[i]
        
        if in_pos:
            ret = (price - df['Close'].iloc[i-1]) / df['Close'].iloc[i-1]
            daily_returns.append(ret)
            if price > highest_price:
                highest_price = price
        else:
            daily_returns.append(0.0)
            
        if not in_pos:
            if price > high_20.iloc[i]:
                in_pos = True
                entry_price = price
                highest_price = price
        else:
            if price <= highest_price * 0.95: # 5% trailing stop
                in_pos = False
                
    returns_series = pd.Series(daily_returns)
    sharpe = (returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0.0
    return sharpe

def run_strategy_b(df):
    """
    Sniper/Mean Reversion
    Entry: Price < 20-Day Low (Dip).
    Exit: Price > 20-Day SMA (Reversion).
    """
    in_pos = False
    entry_price = 0
    daily_returns = []
    
    low_20 = df['Low'].rolling(20).min().shift(1)
    sma_20 = df['Close'].rolling(20).mean().shift(1)
    
    for i in range(len(df)):
        if pd.isna(low_20.iloc[i]) or pd.isna(sma_20.iloc[i]):
            daily_returns.append(0.0)
            continue
            
        price = df['Close'].iloc[i]
        
        if in_pos:
            ret = (price - df['Close'].iloc[i-1]) / df['Close'].iloc[i-1]
            daily_returns.append(ret)
        else:
            daily_returns.append(0.0)
            
        if not in_pos:
            if price < low_20.iloc[i]:
                in_pos = True
                entry_price = price
        else:
            if price > sma_20.iloc[i]:
                in_pos = False
                
    returns_series = pd.Series(daily_returns)
    sharpe = (returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0.0
    return sharpe

def main():
    tickers = ['NVDA', 'TSM', 'AMD', 'MU', 'CIFR', 'MARA', 'COIN', 'QQQ', 'SPY', 'IWM', 'SMH']
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*3)
    
    print("Downloading 3 Years of Daily Data...")
    
    strategy_map = {}
    results = []
    
    for t in tickers:
        df = yf.download(t, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
        if df.empty:
            continue
            
        # Handle yfinance multiindex
        if isinstance(df.columns, pd.MultiIndex):
            has_adj_close = 'Adj Close' in df.columns.get_level_values(0)
            col_name = 'Adj Close' if has_adj_close else 'Close'
            close = df[col_name][t]
            high = df['High'][t]
            low = df['Low'][t]
        else:
            close = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
            high = df['High']
            low = df['Low']
            
        df_clean = pd.DataFrame({'Close': close, 'High': high, 'Low': low}).dropna()
        
        sharpe_A = run_strategy_a(df_clean)
        sharpe_B = run_strategy_b(df_clean)
        
        # We give Momentum a slight penalty (Sharpe_B must win by > 0.1)
        if sharpe_B > sharpe_A + 0.1:
            winner = 'SNIPER'
        else:
            winner = 'SPRINTER'
            
        delta = sharpe_B - sharpe_A
        
        strategy_map[t] = winner
        results.append({
            'Ticker': t,
            'Best Strategy': winner,
            'Sharpe (B: Sniper)': sharpe_B,
            'Sharpe (A: Sprinter)': sharpe_A,
            'Sharpe Delta': delta
        })

    # Output table
    print("\n--- Execution Lane Tournament Results ---")
    print(f"{'Ticker':<10} | {'Best Strategy':<15} | {'Sharpe A (Sprint)':<18} | {'Sharpe B (Sniper)':<18} | {'Delta':<10}")
    print("-" * 85)
    for r in results:
        print(f"{r['Ticker']:<10} | {r['Best Strategy']:<15} | {r['Sharpe (A: Sprinter)']:<18.2f} | {r['Sharpe (B: Sniper)']:<18.2f} | {r['Sharpe Delta']:<10.2f}")
        
    # Save to JSON
    os.makedirs('execution', exist_ok=True)
    json_path = 'execution/strategy_map.json'
    with open(json_path, 'w') as f:
        json.dump(strategy_map, f, indent=4)
        
    print(f"\nSaved execution map to {json_path}")

if __name__ == '__main__':
    main()
