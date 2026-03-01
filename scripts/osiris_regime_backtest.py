import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Loading signal data...")
    # Load Signal Data
    df_signal = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
    df_signal['fiscal_date'] = pd.to_datetime(df_signal['fiscal_date'])
    if df_signal['fiscal_date'].dt.tz is not None:
        df_signal['fiscal_date'] = df_signal['fiscal_date'].dt.tz_localize(None)
    df_signal.set_index('fiscal_date', inplace=True)

    print("Downloading Market Data (QQQ, HYG, LQD)...")
    # Load Market Data starting from 2014
    tickers = ["QQQ", "HYG", "LQD"]
    market_data = yf.download(tickers, start="2014-01-01", progress=False)
    
    if isinstance(market_data.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in market_data.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        qqq = market_data[col_name]['QQQ']
        hyg = market_data[col_name]['HYG']
        lqd = market_data[col_name]['LQD']
    else:
        print("Error: Expected MultiIndex dataframe from yfinance")
        return

    qqq_index = pd.to_datetime(qqq.index)
    if qqq_index.tz is not None:
        qqq_index = qqq_index.tz_localize(None)
    
    df = pd.DataFrame({
        'QQQ': qqq.values,
        'HYG': hyg.values,
        'LQD': lqd.values
    }, index=qqq_index)

    # Join 
    df = df.join(df_signal[['median_inv_turnover_z252']], how='left')
    df['median_inv_turnover_z252'] = df['median_inv_turnover_z252'].ffill()
    
    # Calculate Indicators
    df['MA200'] = df['QQQ'].rolling(window=200).mean()
    df['Liquidity'] = df['HYG'] / df['LQD']
    df['Liquidity_Trend'] = df['Liquidity'] > df['Liquidity'].rolling(window=50).mean()

    z_score = pd.to_numeric(df['median_inv_turnover_z252'], errors='coerce').fillna(0.0)

    # Apply Trinity Rules
    cond_long = (df['QQQ'] > df['MA200']) | (df['Liquidity_Trend'] == True)
    cond_crash = (df['QQQ'] < df['MA200']) & (df['Liquidity_Trend'] == False)
    cond_glut = z_score < -1.0

    positions = np.zeros(len(df))
    
    # Base Case (Though Long and Crash cover all possibilities logically)
    # If Condition Long: 1.0
    positions = np.where(cond_long, 1.0, positions)
    
    # If Condition Crash:
    # If Glut: -0.5, Else: 0.0
    crash_positions = np.where(cond_glut, -0.5, 0.0)
    positions = np.where(cond_crash, crash_positions, positions)

    df['Signal_Trinity'] = positions

    # Shift positions by 1 day to execute on the day AFTER the signal is known
    df['Position_Trinity'] = df['Signal_Trinity'].shift(1)

    df['Benchmark_Return'] = df['QQQ'].pct_change()
    df['Strategy_Return'] = df['Position_Trinity'] * df['Benchmark_Return']
    
    # Filter for 2015 onwards to match previous backtest exactly
    df = df.loc['2015-01-01':]
    df = df.dropna(subset=['median_inv_turnover_z252', 'Benchmark_Return', 'Strategy_Return'])

    # Calculate Cumulative Returns
    df['Cum_Bench'] = (1 + df['Benchmark_Return']).cumprod()
    df['Cum_Strat'] = (1 + df['Strategy_Return']).cumprod()

    # Metrics
    def calc_cagr(cum_returns_series):
        if len(cum_returns_series) == 0: return 0
        total_return = cum_returns_series.iloc[-1]
        years = len(cum_returns_series) / 252.0
        return (total_return ** (1 / years)) - 1 if total_return > 0 else -1

    def calc_sharpe(returns_series):
        if returns_series.std() == 0: return 0
        return (returns_series.mean() / returns_series.std()) * (252 ** 0.5)

    def calc_max_drawdown(cum_returns_series):
        if len(cum_returns_series) == 0: return 0
        roll_max = cum_returns_series.cummax()
        drawdown = cum_returns_series / roll_max - 1.0
        return drawdown.min()

    metrics = {
        'Benchmark (B&H QQQ)': [calc_sharpe(df['Benchmark_Return']), calc_cagr(df['Cum_Bench']), calc_max_drawdown(df['Cum_Bench'])],
        'Strategy (Trinity)': [calc_sharpe(df['Strategy_Return']), calc_cagr(df['Cum_Strat']), calc_max_drawdown(df['Cum_Strat'])]
    }
    
    print("\n--- Osiris Trinity Strategy Backtest ---")
    print(f"{'Metrics':<16} | {'Benchmark (B&H QQQ)':<20} | {'Strategy (Trinity)':<20}")
    print("-" * 63)
    
    print(f"{'CAGR':<16} | {metrics['Benchmark (B&H QQQ)'][1]*100:19.2f}% | {metrics['Strategy (Trinity)'][1]*100:19.2f}%")
    print(f"{'Sharpe Ratio':<16} | {metrics['Benchmark (B&H QQQ)'][0]:20.2f} | {metrics['Strategy (Trinity)'][0]:20.2f}")
    print(f"{'Max Drawdown':<16} | {metrics['Benchmark (B&H QQQ)'][2]*100:19.2f}% | {metrics['Strategy (Trinity)'][2]*100:19.2f}%")

if __name__ == "__main__":
    main()
