import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Initializing Non-Linear Sniper (Phase 34)...")
    
    # 1. Define the Assets and Physics Multipliers
    tickers = {
        'NVDA': {'Multiplier': 1.5, 'Type': 'Semiconductors'},
        'MU': {'Multiplier': 1.5, 'Type': 'Semiconductors'},
        'AMD': {'Multiplier': 1.5, 'Type': 'Semiconductors'},
        'XLE': {'Multiplier': 1.5, 'Type': 'Energy'},
        'MSFT': {'Multiplier': 0.8, 'Type': 'Software'},
        'XLRE': {'Multiplier': 0.8, 'Type': 'Real Estate'}
    }
    
    # 2. Load Osiris Z-Score
    try:
        df_signal = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
        df_signal['fiscal_date'] = pd.to_datetime(df_signal['fiscal_date'])
        if df_signal['fiscal_date'].dt.tz is not None:
            df_signal['fiscal_date'] = df_signal['fiscal_date'].dt.tz_localize(None)
        df_signal = df_signal.set_index('fiscal_date').sort_index()
        z_col = [c for c in df_signal.columns if 'zscore' in c.lower() or 'z252' in c.lower()][0]
        osiris_series = df_signal[z_col]
        # Calculate Derivative (1 month change roughly 21 trading days)
        osiris_roc = osiris_series - osiris_series.shift(21)
    except Exception as e:
        print(f"Error loading Osiris signal: {e}")
        return

    # 3. Fetch Daily Data
    start_date = "2019-01-01"
    end_date = "2024-12-31"
    
    print("Downloading Market Data...")
    data = yf.download(list(tickers.keys()), start=start_date, end=end_date, progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in data.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        closes = data[col_name]
    else:
        print("Expected MultiIndex from yfinance")
        return

    # Pre-calculate Indicators
    high52w = closes.rolling(window=252).max()
    ma50 = closes.rolling(window=50).mean()
    ma200 = closes.rolling(window=200).mean()
    
    dates = closes.loc['2020-01-01':].index
    
    portfolio = {}
    cash = 100000.0
    equity_history = []
    trades = []
    
    osiris_series = osiris_series.reindex(closes.index).ffill().fillna(0.0)
    osiris_roc = osiris_roc.reindex(closes.index).ffill().fillna(0.0)
    
    print("Running Non-Linear Simulation Loop...")
    
    for i in range(len(dates) - 1):
        current_date = dates[i]
        
        # Current Macro
        z_score = osiris_series.loc[current_date]
        z_roc = osiris_roc.loc[current_date]
        
        # Calculate current equity
        current_equity = cash
        for t, pos in portfolio.items():
            if not pd.isna(closes.loc[current_date, t]):
                current_equity += pos['shares'] * closes.loc[current_date, t]
                
        equity_history.append({'Date': current_date, 'Equity': current_equity})
        
        # 1. Process Exits (Trend break or Macro flush)
        tickers_to_remove = []
        for t in list(portfolio.keys()):
            pos = portfolio[t]
            if pd.isna(closes.loc[current_date, t]) or pd.isna(ma200.loc[current_date, t]): 
                continue
                
            curr_price = closes.loc[current_date, t]
            curr_ma200 = ma200.loc[current_date, t]
            
            # The Non-Linear flush logic
            sell_condition = (z_score < -1.0) or (curr_price < curr_ma200)
            
            if sell_condition:
                proceeds = pos['shares'] * curr_price
                cash += proceeds
                profit = proceeds - (pos['shares'] * pos['entry_price'])
                pct_profit = (curr_price / pos['entry_price']) - 1
                
                trades.append({
                    'Ticker': t,
                    'Entry_Date': pos['entry_date'],
                    'Exit_Date': current_date,
                    'Entry_Price': pos['entry_price'],
                    'Exit_Price': curr_price,
                    'Profit': profit,
                    'Pct_Profit': pct_profit,
                    'Reason': 'Non-Linear Stop'
                })
                tickers_to_remove.append(t)
                
        for t in tickers_to_remove:
            del portfolio[t]
            
        # 2. Process Entries (The Fat Pitch Hunt)
        # We only look for entries if we have cash
        if cash > 100:
            candidates = []
            for t, props in tickers.items():
                if t in portfolio:
                    continue
                if pd.isna(closes.loc[current_date, t]) or pd.isna(ma50.loc[current_date, t]):
                    continue
                    
                curr_price = closes.loc[current_date, t]
                high_52 = high52w.loc[current_date, t]
                ma_50 = ma50.loc[current_date, t]
                
                # --- The Non-Linear Scoring Formula ---
                score = 0
                
                # 1. Fundamental (Osiris)
                if z_score > 0:
                    score += 40
                elif z_score < 0:
                    score -= 100 # Kill it
                    
                # 3. Derivative Boost
                if z_roc > 0:
                    score += (z_roc * 50)
                    
                # 2. Physics Multiplier
                score = score * props['Multiplier']
                
                # 4. Technical (Deep Value)
                if (curr_price < 0.85 * high_52) and (curr_price < 1.02 * ma_50):
                    score += 40
                    
                # The Guillotine
                if score >= 100:
                    candidates.append((t, score, curr_price))
                    
            # Allocate to all candidates that pass the guillotine
            if candidates:
                # 5. Convex Sizing
                total_convex_score = sum([c[1]**2 for c in candidates])
                
                for t, score, curr_price in candidates:
                    alloc_pct = (score**2) / total_convex_score
                    # Cap at max size to avoid putting 100% in one trade instantly
                    alloc_pct = min(alloc_pct, 0.40) 
                    
                    alloc_dollars = current_equity * alloc_pct
                    if alloc_dollars > cash:
                        alloc_dollars = cash
                        
                    if alloc_dollars < 100:
                        continue
                        
                    shares = alloc_dollars / curr_price
                    cash -= alloc_dollars
                    
                    portfolio[t] = {
                        'shares': shares,
                        'entry_price': curr_price,
                        'entry_date': current_date,
                        'score_at_entry': score
                    }
                    
    # Final cleanup
    end_date_actual = dates[-1]
    final_equity = cash
    for t, pos in portfolio.items():
        curr_price = closes.loc[end_date_actual, t]
        final_equity += pos['shares'] * curr_price
        proceeds = pos['shares'] * curr_price
        profit = proceeds - (pos['shares'] * pos['entry_price'])
        pct_profit = (curr_price / pos['entry_price']) - 1
        trades.append({
            'Ticker': t,
            'Entry_Date': pos['entry_date'],
            'Exit_Date': end_date_actual,
            'Entry_Price': pos['entry_price'],
            'Exit_Price': curr_price,
            'Profit': profit,
            'Pct_Profit': pct_profit,
            'Reason': 'End of Test'
        })
        
    equity_history.append({'Date': end_date_actual, 'Equity': final_equity})
    df_history = pd.DataFrame(equity_history).set_index('Date')
    
    # Calculate Metrics
    strat_returns = df_history['Equity'].pct_change().dropna()
    strat_cum = (1 + strat_returns).cumprod()
    
    def calc_cagr(cum_returns_series):
        if len(cum_returns_series) == 0: return 0
        total_return = cum_returns_series.iloc[-1]
        years = len(cum_returns_series) / 252.0
        return (total_return ** (1 / years)) - 1 if total_return > 0 else -1

    def calc_max_drawdown(cum_returns_series):
        if len(cum_returns_series) == 0: return 0
        roll_max = cum_returns_series.cummax()
        drawdown = cum_returns_series / roll_max - 1.0
        return drawdown.min()
        
    strat_cagr = calc_cagr(strat_cum)
    strat_dd = calc_max_drawdown(strat_cum)
    
    gross_profit = sum(t['Profit'] for t in trades if t['Profit'] > 0)
    gross_loss = abs(sum(t['Profit'] for t in trades if t['Profit'] < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    win_rate = sum(1 for t in trades if t['Profit'] > 0) / len(trades) if trades else 0
    
    print("\n--- Phase 34: The Non-Linear Super-Cycle Backtest ---")
    print(f"{'Metric':<25} | {'Strategy (Non-Linear Sniper)':<30}")
    print("-" * 58)
    print(f"{'CAGR':<25} | {strat_cagr*100:29.2f}%")
    print(f"{'Max Drawdown':<25} | {strat_dd*100:29.2f}%")
    print(f"{'Profit Factor':<25} | {profit_factor:29.2f}")
    print(f"{'Total Trades Executed':<25} | {len(trades):<29}")
    print(f"{'Win Rate':<25} | {win_rate*100:29.2f}%")
    
    print("\n--- The Fat Pitches Caught ---")
    sorted_trades = sorted(trades, key=lambda x: x['Entry_Date'])
    for i, t in enumerate(sorted_trades):
        entry_d = t['Entry_Date'].strftime('%Y-%m-%d')
        exit_d = t['Exit_Date'].strftime('%Y-%m-%d')
        pct = t['Pct_Profit'] * 100
        print(f"Caught {t['Ticker']:<4} | En: {entry_d} @ ${t['Entry_Price']:<7.2f} | Ex: {exit_d} | Score: +{pct:.2f}%")

if __name__ == '__main__':
    main()
