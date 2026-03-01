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

    print("Downloading Market Data (QQQ, XLE)...")
    # Load Market Data starting from 2014 to allow for MA200 calculation before 2015
    tickers = ["QQQ", "XLE"]
    market_data = yf.download(tickers, start="2014-01-01", progress=False)
    
    if isinstance(market_data.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in market_data.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        qqq = market_data[col_name]['QQQ']
        xle = market_data[col_name]['XLE']
    else:
        print("Error: Expected MultiIndex dataframe from yfinance")
        return

    qqq_index = pd.to_datetime(qqq.index)
    if qqq_index.tz is not None:
        qqq_index = qqq_index.tz_localize(None)
    
    df = pd.DataFrame({
        'QQQ': qqq.values,
        'XLE': xle.values
    }, index=qqq_index)

    # Join Signal
    df = df.join(df_signal[['median_inv_turnover_z252']], how='left')
    df['median_inv_turnover_z252'] = df['median_inv_turnover_z252'].ffill()
    
    # Calculate MAs
    df['QQQ_MA200'] = df['QQQ'].rolling(window=200).mean()
    df['XLE_MA200'] = df['XLE'].rolling(window=200).mean()

    z_score = pd.to_numeric(df['median_inv_turnover_z252'], errors='coerce').fillna(0.0)

    # Calculate returns for each asset
    df['QQQ_Return'] = df['QQQ'].pct_change()
    df['XLE_Return'] = df['XLE'].pct_change()

    # 1. Target allocation (Today's Signal)
    # State 1 (Efficiency/Ice): Z > 0 -> QQQ
    # State 2 (Friction/Fire): Z <= 0 -> XLE
    target_qqq = z_score > 0
    target_xle = z_score <= 0
    
    # 2. Trend override / Safety Valve (Today's Signal)
    qqq_cash = df['QQQ'] < df['QQQ_MA200']
    xle_cash = df['XLE'] < df['XLE_MA200']
    
    # 3. Position decision (1.0 in Target, or 0.0)
    pos_qqq = np.where(target_qqq & ~qqq_cash, 1.0, 0.0)
    pos_xle = np.where(target_xle & ~xle_cash, 1.0, 0.0)
    
    df['Pos_QQQ'] = pos_qqq
    df['Pos_XLE'] = pos_xle
    
    # 4. Shift positions for execution to avoid lookahead sum(Position[t-1] * Asset_Return[t])
    df['Exec_Pos_QQQ'] = df['Pos_QQQ'].shift(1)
    df['Exec_Pos_XLE'] = df['Pos_XLE'].shift(1)
    
    # Execute Strategy return based on shifted positions
    df['Strategy_Return'] = (df['Exec_Pos_QQQ'] * df['QQQ_Return']) + (df['Exec_Pos_XLE'] * df['XLE_Return'])
    
    # Filter for 2015 onwards
    df = df.loc['2015-01-01':]
    df = df.dropna(subset=['QQQ_Return', 'Strategy_Return'])

    # Calculate Cumulative Returns
    df['Cum_Bench'] = (1 + df['QQQ_Return']).cumprod()
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
        'Benchmark (B&H QQQ)': [calc_sharpe(df['QQQ_Return']), calc_cagr(df['Cum_Bench']), calc_max_drawdown(df['Cum_Bench'])],
        'Strategy (Fire&Ice)': [calc_sharpe(df['Strategy_Return']), calc_cagr(df['Cum_Strat']), calc_max_drawdown(df['Cum_Strat'])]
    }
    
    print("\n--- Osiris Fire & Ice Strategy Backtest ---")
    print(f"{'Metrics':<16} | {'Benchmark (B&H QQQ)':<20} | {'Strategy (Fire&Ice)':<20}")
    print("-" * 65)
    
    print(f"{'CAGR':<16} | {metrics['Benchmark (B&H QQQ)'][1]*100:19.2f}% | {metrics['Strategy (Fire&Ice)'][1]*100:19.2f}%")
    print(f"{'Sharpe Ratio':<16} | {metrics['Benchmark (B&H QQQ)'][0]:20.2f} | {metrics['Strategy (Fire&Ice)'][0]:20.2f}")
    print(f"{'Max Drawdown':<16} | {metrics['Benchmark (B&H QQQ)'][2]*100:19.2f}% | {metrics['Strategy (Fire&Ice)'][2]*100:19.2f}%")

if __name__ == "__main__":
    main()
