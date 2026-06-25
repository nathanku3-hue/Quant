import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Initializing Elite Sniper Backtest (Phase 35)...")
    tickers = ['NVDA', 'AMD', 'TSM', 'AVGO', 'MU', 'LRCX', 'AMAT', 'COIN', 'MSTR', 'LLY', 'NVO', 'VRT', 'SMCI', 'FCX', 'CCJ']
    
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

    # 2. Fetch Daily Data
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
    high52w = closes.rolling(window=252).max()
    ma50 = closes.rolling(window=50).mean()
    ma200 = closes.rolling(window=200).mean()
    mavol20 = volumes.rolling(window=20).mean()
    
    dates = closes.loc['2020-01-01':].index
    osiris_series = osiris_series.reindex(closes.index).ffill().fillna(0.0)
    
    # --- Strategy A: Elite Sniper (Active Timing) ---
    portfolio_A = {}
    cash_A = 100000.0
    equity_history_A = []
    max_positions = 10
    
    # --- Strategy B: Buy & Hold Elite 20 (Passive Equal Weight) ---
    # We will simulate rebalancing daily or just buy and hold? "Passive Equal Weight" usually means buy at start.
    # Let's do daily rebalanced equal weight of available tickers, or just buy at start and hold.
    # Let's do equal weight daily rebalance for simplicity of comparison.
    b_h_returns = closes[tickers].pct_change().loc['2020-01-01':].mean(axis=1)
    bm_cum_B = (1 + b_h_returns).cumprod() * 100000.0
    
    print("Running Elite Sniper Simulation Loop...")
    
    for i in range(len(dates) - 1):
        current_date = dates[i]
        
        z_score = osiris_series.loc[current_date]
        fund_score = 0
        if z_score > 0:
            fund_score = 50
        elif z_score > -1.0:
            fund_score = 25
            
        current_equity_A = cash_A
        for t, pos in portfolio_A.items():
            if not pd.isna(closes.loc[current_date, t]):
                current_equity_A += pos['shares'] * closes.loc[current_date, t]
                
        equity_history_A.append({'Date': current_date, 'Equity': current_equity_A})
        
        # 1. Process Exits
        tickers_to_remove = []
        for t in list(portfolio_A.keys()):
            pos = portfolio_A[t]
            if pd.isna(closes.loc[current_date, t]) or pd.isna(ma200.loc[current_date, t]): 
                continue
                
            curr_price = closes.loc[current_date, t]
            curr_ma200 = ma200.loc[current_date, t]
            
            sell_condition = (curr_price < curr_ma200) or (z_score < -1.5)
            
            if sell_condition:
                proceeds = pos['shares'] * curr_price
                cash_A += proceeds
                tickers_to_remove.append(t)
                
        for t in tickers_to_remove:
            del portfolio_A[t]
            
        # 2. Process Entries
        if len(portfolio_A) < max_positions and cash_A > 100:
            candidates = []
            for t in tickers:
                if t in portfolio_A: continue
                if pd.isna(closes.loc[current_date, t]) or pd.isna(ma50.loc[current_date, t]): continue
                    
                curr_price = closes.loc[current_date, t]
                high_52 = high52w.loc[current_date, t]
                ma_50 = ma50.loc[current_date, t]
                curr_vol = volumes.loc[current_date, t]
                ma_vol = mavol20.loc[current_date, t]
                
                tech_score = 0
                if curr_price < 0.85 * high_52: tech_score += 20
                if curr_price <= 1.02 * ma_50: tech_score += 20
                if curr_vol < 0.8 * ma_vol: tech_score += 10
                    
                total_score = fund_score + tech_score
                
                if total_score >= 80:
                    candidates.append((t, total_score, curr_price))
                    
            candidates.sort(key=lambda x: x[1], reverse=True)
            
            for t, score, curr_price in candidates:
                if len(portfolio_A) >= max_positions: break
                if cash_A <= 0: break
                    
                alloc = min(cash_A, current_equity_A * 0.10)
                if alloc < 100: continue
                    
                shares = alloc / curr_price
                cash_A -= alloc
                
                portfolio_A[t] = {
                    'shares': shares, 'entry_price': curr_price, 'entry_date': current_date
                }
                
    # Final cleanup
    end_date_actual = dates[-1]
    final_equity_A = cash_A
    for t, pos in portfolio_A.items():
        curr_price = closes.loc[end_date_actual, t]
        final_equity_A += pos['shares'] * curr_price
        
    equity_history_A.append({'Date': end_date_actual, 'Equity': final_equity_A})
    df_history_A = pd.DataFrame(equity_history_A).set_index('Date')

    # Metrics Calc
    def calc_metrics(equity_series):
        rets = equity_series.pct_change().dropna()
        cum = (1 + rets).cumprod()
        
        cagr = 0
        if len(cum) > 0:
            t_ret = cum.iloc[-1]
            yrs = len(cum) / 252.0
            if t_ret > 0:
                cagr = (t_ret ** (1 / yrs)) - 1
            else:
                cagr = -1
                
        r_max = cum.cummax()
        dd = (cum / r_max - 1.0).min() if len(cum) > 0 else 0
        
        sharpe = (rets.mean() / rets.std()) * np.sqrt(252) if rets.std() > 0 else 0
        return cagr, dd, sharpe

    # Strategy A
    cagr_A, dd_A, sharpe_A = calc_metrics(df_history_A['Equity'])
    
    # Strategy B (Passive Equal Weight)
    cagr_B, dd_B, sharpe_B = calc_metrics(bm_cum_B)
    
    # Benchmark QQQ
    qqq_eq = closes['QQQ'].loc['2020-01-01':'2024-12-31']
    cagr_Q, dd_Q, sharpe_Q = calc_metrics(qqq_eq)
    
    print("\n--- Phase 35: The Elite Sniper Super-Cycle Backtest ---")
    print(f"{'Metric':<18} | {'Elite Sniper (Active)':<22} | {'Elite 20 (Passive)':<22} | {'Benchmark (QQQ)':<20}")
    print("-" * 90)
    print(f"{'CAGR':<18} | {cagr_A*100:21.2f}% | {cagr_B*100:21.2f}% | {cagr_Q*100:19.2f}%")
    print(f"{'Sharpe Ratio':<18} | {sharpe_A:22.2f} | {sharpe_B:22.2f} | {sharpe_Q:20.2f}")
    print(f"{'Max Drawdown':<18} | {dd_A*100:21.2f}% | {dd_B*100:21.2f}% | {dd_Q*100:19.2f}%")

if __name__ == '__main__':
    main()
