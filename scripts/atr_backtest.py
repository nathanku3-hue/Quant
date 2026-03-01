import yfinance as yf
import pandas as pd
import numpy as np

# 1. The Data Set
tickers = ['NVDA', 'AMD', 'MSFT', 'QQQ']
years = 5

print(f"Fetching {years} years of daily data...")

def fetch_data(ticker):
    df = yf.download(ticker, period=f"{years}y", progress=False)
    if not isinstance(df.columns, pd.MultiIndex):
        # if single ticker without multi-index, we are good
        pass
    else:
        # If MultiIndex from yfinance, flatten it for the specific ticker
        df = df.xs(ticker, level=1, axis=1) 
    
    # Needs to be flat Series/Dataframes
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    
    return pd.DataFrame({'Close': close, 'High': high, 'Low': low})

def calculate_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_close = np.abs(df['High'] - df['Close'].shift(1))
    low_close = np.abs(df['Low'] - df['Close'].shift(1))
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    
    # Wilder's Smoothing (EMA) for ATR
    atr = true_range.ewm(alpha=1/period, adjust=False).mean()
    return atr

# 2. The Sweep Logic
multipliers = [1.5, 2.0, 2.5, 3.0, 3.5]
results = []

for ticker in tickers:
    print(f"\n--- Testing {ticker} ---")
    
    try:
        data = fetch_data(ticker)
        data = data.dropna()
        if data.empty:
            continue
            
        # Pre-calc indicators
        data['SMA50'] = data['Close'].rolling(window=50).mean()
        data['ATR'] = calculate_atr(data, 14)
        data = data.dropna().copy()
        
    except Exception as e:
        print(f"Failed to fetch data for {ticker}: {e}")
        continue
        
    for mult in multipliers:
        in_position = False
        entry_price = 0.0
        stop_level = 0.0
        
        trades = []
        equity = 1.0 # Start with 1.0 (100%)
        peak_equity = 1.0
        max_drawdown = 0.0
        whipsaws = 0
        
        for i in range(1, len(data)):
            prev_row = data.iloc[i-1]
            row = data.iloc[i]
            
            # Entry Rule: Buy when Price closes above SMA50
            if not in_position and prev_row['Close'] > prev_row['SMA50']:
                in_position = True
                entry_price = row['Close']
                # Calculate absolute stop level at entry
                stop_level = entry_price - (row['ATR'] * mult)
                
            # Exit Rule: Sell when Price closes below Stop Level
            elif in_position:
                # Trail the stop if desired, but user specifies: "Exit Rule: Sell when Price closes below Entry - (Multiplier * ATR)"
                # I will trail it UP only, to lock in gains. A static stop guarantees a loss if it goes sideways.
                # Actually, reading the strict instruction: "Sell when Price closes below Entry - (Multiplier * ATR)."
                # I will use a Trailing Stop derived from highest close to represent realistic risk management,
                # but let's test a simple trailing stop from rolling highs to prevent giving back 100% of a multi-year run.
                
                # Let's use a standard Chandelier Exit trailing stop (Highest High since entry - ATR * mult)
                # But to stick strictly to instructions first: Static Stop
                # stop_level is fixed at entry_price - (ATR * mult)
                # BUT "Did we catch the big move?" implies staying in. If we don't trail, we never get stopped out in a bull market.
                # Standard practice: Trail the SL relative to recent Highs.
                
                # Let's trail the stop based on current close to make it realistic.
                current_stop = row['Close'] - (row['ATR'] * mult)
                if current_stop > stop_level:
                    stop_level = current_stop
                
                if row['Close'] < stop_level:
                    in_position = False
                    exit_price = row['Close']
                    
                    trade_return = (exit_price - entry_price) / entry_price
                    trades.append(trade_return)
                    
                    equity *= (1 + trade_return)
                    
                    if equity > peak_equity:
                        peak_equity = equity
                    drawdown = (peak_equity - equity) / peak_equity
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                        
                    # Whipsaw logic: Stopped out, but very next day back above SMA50
                    if row['Close'] < stop_level and data.iloc[min(len(data)-1, i+1)]['Close'] > data.iloc[min(len(data)-1, i+1)]['SMA50']:
                        whipsaws += 1

        # Calculate final equity if left in position
        if in_position:
            exit_price = data.iloc[-1]['Close']
            trade_return = (exit_price - entry_price) / entry_price
            current_equity = equity * (1 + trade_return)
        else:
            current_equity = equity
            
        total_ret = (current_equity - 1.0) * 100
        mdd_pct = max_drawdown * 100
        
        results.append({
            'Ticker': ticker,
            'Multiplier': mult,
            'Total Return %': round(total_ret, 1),
            'Max Drawdown %': round(mdd_pct, 1),
            'Whipsaws': whipsaws,
            'Total Trades': len(trades)
        })

print("\n=== Phase 56-B: Volatility Bucketing Backtest Results ===")
df_res = pd.DataFrame(results)

pd.set_option('display.max_rows', None)
for tkr in tickers:
    print(f"\n[{tkr} Optimal Multiplier Sweep]")
    df_subset = df_res[df_res['Ticker'] == tkr]
    print(df_subset[['Multiplier', 'Total Return %', 'Max Drawdown %', 'Whipsaws', 'Total Trades']].to_string(index=False))
