import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Initializing Infinite Sniper Backtest...")
    tickers = ['NVDA', 'MSFT', 'AAPL', 'AMZN', 'GOOGL', 'META', 'TSLA', 'AVGO', 'ASML', 'COST', 'PEP', 'ADBE', 'NFLX', 'AMD', 'TXN', 'QCOM', 'INTC', 'HON', 'AMGN', 'SBUX', 'GILD', 'ISRG', 'MDLZ', 'BKNG', 'LRCX', 'ADP', 'ADI', 'MU', 'CSCO', 'INTU', 'AMAT', 'KLAC']
    
    # 1. Load Osiris Z-Score
    try:
        df_signal = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
        df_signal['fiscal_date'] = pd.to_datetime(df_signal['fiscal_date'])
        if df_signal['fiscal_date'].dt.tz is not None:
            df_signal['fiscal_date'] = df_signal['fiscal_date'].dt.tz_localize(None)
        df_signal = df_signal.set_index('fiscal_date').sort_index()
        z_col = [c for c in df_signal.columns if 'zscore' in c.lower() or 'z252' in c.lower()][0]
        osiris_series = df_signal[z_col]
    except Exception as e:
        print(f"Error loading Osiris signal: {e}")
        return

    # 2. Fetch Daily Data (2019 to allow 252-day lookback for 2020 start)
    start_date = "2019-01-01"
    end_date = "2024-12-31"
    
    print("Downloading Market Data...")
    all_tickers = tickers + ['QQQ']
    data = yf.download(all_tickers, start=start_date, end=end_date, progress=False)
    
    if isinstance(data.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in data.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        closes = data[col_name]
        volumes = data['Volume']
    else:
        print("Expected MultiIndex from yfinance")
        return

    # Pre-calculate Indicators
    print("Pre-calculating Indicators...")
    
    high52w = closes.rolling(window=252).max()
    ma50 = closes.rolling(window=50).mean()
    ma200 = closes.rolling(window=200).mean()
    mavol20 = volumes.rolling(window=20).mean()
    
    # Shift indicators to avoid lookahead (signal is calculated on yesterday's close/indicators to execute today, or calculate today's close to execute tomorrow)
    # We will assume we buy/sell AT THE CLOSE of the day the signal is triggered, or at the OPEN of the next day. 
    # For simplicity, calculate signals based on t-1, execute at close of t.
    
    # Actually wait, we can just step through the dates and say "at day t close" we use day t data. The returns will be calculated from day t to day t+1. 
    
    dates = closes.loc['2020-01-01':].index
    
    portfolio = {}
    cash = 100000.0
    equity = 100000.0
    max_positions = 10
    
    portfolio_history = []
    trades = []
    
    # Fill NA Osiris forward
    osiris_series = osiris_series.reindex(closes.index).ffill().fillna(0.0)
    
    print("Running Simulation Loop...")
    
    for i in range(len(dates) - 1):
        current_date = dates[i]
        next_date = dates[i+1] # We buy today close, get return tomorrow
        
        # Current state
        z_score = osiris_series.loc[current_date]
        
        fund_score = 0
        if z_score > 0:
            fund_score = 50
        elif z_score > -1.0:
            fund_score = 25
            
        current_equity = cash
        for t, pos in portfolio.items():
            current_equity += pos['shares'] * closes.loc[current_date, t]
            
        # Update trailing max for drawdown ? No, we can just record equity
        portfolio_history.append({'Date': current_date, 'Equity': current_equity})
        
        # 1. Process Exits
        tickers_to_remove = []
        for t in list(portfolio.keys()):
            pos = portfolio[t]
            curr_price = closes.loc[current_date, t]
            curr_ma200 = ma200.loc[current_date, t]
            
            sell_macro = z_score < -1.0
            sell_trend = curr_price < curr_ma200
            
            if sell_macro or sell_trend:
                # Sell
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
                    'Reason': 'Macro Stop' if sell_macro else 'Trend Stop'
                })
                tickers_to_remove.append(t)
                
        for t in tickers_to_remove:
            del portfolio[t]
            
        # 2. Process Entries
        if len(portfolio) < max_positions:
            # Score all available
            candidates = []
            for t in tickers: # Exclude QQQ
                if t in portfolio:
                    continue
                
                if pd.isna(closes.loc[current_date, t]) or pd.isna(ma50.loc[current_date, t]):
                    continue
                    
                curr_price = closes.loc[current_date, t]
                high_52 = high52w.loc[current_date, t]
                ma_50 = ma50.loc[current_date, t]
                curr_vol = volumes.loc[current_date, t]
                ma_vol = mavol20.loc[current_date, t]
                
                tech_score = 0
                if curr_price < 0.85 * high_52:
                    tech_score += 20
                if curr_price <= 1.02 * ma_50:
                    tech_score += 20
                if curr_vol < 0.8 * ma_vol:
                    tech_score += 10
                    
                total_score = fund_score + tech_score
                
                if total_score >= 80:
                    candidates.append((t, total_score, curr_price))
                    
            # Sort heavily by score, maybe random or by price? By score desc.
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            for t, score, curr_price in candidates:
                if len(portfolio) >= max_positions:
                    break
                if cash <= 0:
                    break
                    
                # Standard slot is 10% of CURRENT equity
                alloc = min(cash, current_equity * 0.10)
                if alloc < 100: # avoid dust
                    continue
                    
                shares = alloc / curr_price
                cash -= alloc
                
                portfolio[t] = {
                    'shares': shares,
                    'entry_price': curr_price,
                    'entry_date': current_date
                }
                
    # Final cleanup (liquidate at end of backtest)
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
        
    portfolio_history.append({'Date': end_date_actual, 'Equity': final_equity})
    
    df_history = pd.DataFrame(portfolio_history).set_index('Date')
    
    # Calculate Metrics
    bm_closes = closes['QQQ'].loc['2020-01-01':'2024-12-31']
    bm_returns = bm_closes.pct_change().dropna()
    bm_cum = (1 + bm_returns).cumprod()
    
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
        
    bm_cagr = calc_cagr(bm_cum)
    strat_cagr = calc_cagr(strat_cum)
    
    bm_dd = calc_max_drawdown(bm_cum)
    strat_dd = calc_max_drawdown(strat_cum)
    
    win_rate = sum(1 for t in trades if t['Profit'] > 0) / len(trades) if trades else 0
    time_in_market = sum(1 for ret in strat_returns if abs(ret) > 1e-6) / len(strat_returns)
    
    print("\n--- Phase 33: Infinite Sniper Universe Rotation ---")
    print(f"{'Metric':<25} | {'Strategy (Infinite Sniper)':<30} | {'Benchmark (QQQ)':<20}")
    print("-" * 80)
    print(f"{'CAGR':<25} | {strat_cagr*100:29.2f}% | {bm_cagr*100:19.2f}%")
    print(f"{'Max Drawdown':<25} | {strat_dd*100:29.2f}% | {bm_dd*100:19.2f}%")
    print(f"{'Win Rate':<25} | {win_rate*100:29.2f}% | {'N/A':<20}")
    print(f"{'Time in Market (Active)':<25} | {time_in_market*100:29.2f}% | {'100.00%':<20}")
    
    print("\n--- Top 3 Most Profitable Trades ---")
    sorted_trades = sorted(trades, key=lambda x: x['Pct_Profit'], reverse=True)
    for i, t in enumerate(sorted_trades[:3]):
        entry_d = t['Entry_Date'].strftime('%Y-%m-%d')
        exit_d = t['Exit_Date'].strftime('%Y-%m-%d')
        en_p = t['Entry_Price']
        ex_p = t['Exit_Price']
        pct = t['Pct_Profit'] * 100
        print(f"{i+1}. {t['Ticker']:<5} | Bought: {entry_d} @ ${en_p:<7.2f} | Sold: {exit_d} @ ${ex_p:<7.2f} | Return: +{pct:.2f}%")

if __name__ == '__main__':
    main()
