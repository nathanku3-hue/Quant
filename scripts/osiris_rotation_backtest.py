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

    print("Downloading Market Data (QQQ, SMH)...")
    # Load Market Data starting from 2014 to allow for MA200 calculation before 2015
    tickers = ["QQQ", "SMH"]
    market_data = yf.download(tickers, start="2014-01-01", progress=False)
    
    if isinstance(market_data.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in market_data.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        qqq = market_data[col_name]['QQQ']
        smh = market_data[col_name]['SMH']
    else:
        print("Error: Expected MultiIndex dataframe from yfinance")
        return

    qqq_index = pd.to_datetime(qqq.index)
    if qqq_index.tz is not None:
        qqq_index = qqq_index.tz_localize(None)
    
    df = pd.DataFrame({
        'QQQ': qqq.values,
        'SMH': smh.values
    }, index=qqq_index)

    # Join Signal
    df = df.join(df_signal[['median_inv_turnover_z252']], how='left')
    df['median_inv_turnover_z252'] = df['median_inv_turnover_z252'].ffill()
    
    # Calculate MAs
    df['QQQ_MA200'] = df['QQQ'].rolling(window=200).mean()
    df['SMH_MA200'] = df['SMH'].rolling(window=200).mean()

    z_score = pd.to_numeric(df['median_inv_turnover_z252'], errors='coerce').fillna(0.0)

    # Calculate returns for each asset
    df['QQQ_Return'] = df['QQQ'].pct_change()
    df['SMH_Return'] = df['SMH'].pct_change()

    # Determine desired asset
    # State 1 (Efficiency Boom): Z > 0 -> SMH
    # State 2 (Inventory Glut): Z <= 0 -> QQQ
    desired_asset = np.where(z_score > 0, 'SMH', 'QQQ')
    
    # Check Safety Valve (Trend Filter)
    # If desired asset is SMH and SMH < SMH_MA200 -> Cash
    # If desired asset is QQQ and QQQ < QQQ_MA200 -> Cash
    
    # Initialize daily returns array
    strategy_returns = np.zeros(len(df))
    
    for i in range(len(df)):
        asset = desired_asset[i]
        if asset == 'SMH':
            if df['SMH'].iloc[i] < df['SMH_MA200'].iloc[i]:
                strategy_returns[i] = 0.0 # Cash
            else:
                strategy_returns[i] = df['SMH_Return'].iloc[i]
        else: # QQQ
            if df['QQQ'].iloc[i] < df['QQQ_MA200'].iloc[i]:
                strategy_returns[i] = 0.0 # Cash
            else:
                strategy_returns[i] = df['QQQ_Return'].iloc[i]

    # Shift positions logically implies the return WE get TOMORROW is based on the signal from TODAY. 
    # The loop above calculates what *would* be the active return today if we decided today based on today's close, 
    # which is lookahead bias if not shifted. We must shift the target asset and safety check.
    
    # Let's vectorize it safely:
    # 1. Target allocation (Today's Signal)
    target_smh = z_score > 0
    target_qqq = z_score <= 0
    
    # 2. Trend override (Today's Signal)
    smh_cash = df['SMH'] < df['SMH_MA200']
    qqq_cash = df['QQQ'] < df['QQQ_MA200']
    
    # 3. Position decision (1.0 in SMH, 1.0 in QQQ, or 0.0)
    pos_smh = np.where(target_smh & ~smh_cash, 1.0, 0.0)
    pos_qqq = np.where(target_qqq & ~qqq_cash, 1.0, 0.0)
    
    df['Pos_SMH'] = pos_smh
    df['Pos_QQQ'] = pos_qqq
    
    # 4. Shift positions for execution to avoid lookahead sum(Position[t-1] * Asset_Return[t])
    df['Exec_Pos_SMH'] = df['Pos_SMH'].shift(1)
    df['Exec_Pos_QQQ'] = df['Pos_QQQ'].shift(1)
    
    df['Strategy_Return'] = (df['Exec_Pos_SMH'] * df['SMH_Return']) + (df['Exec_Pos_QQQ'] * df['QQQ_Return'])
    
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
        'Strategy (Rotation)': [calc_sharpe(df['Strategy_Return']), calc_cagr(df['Cum_Strat']), calc_max_drawdown(df['Cum_Strat'])]
    }
    
    print("\n--- Osiris Sector Rotation Strategy Backtest ---")
    print(f"{'Metrics':<16} | {'Benchmark (B&H QQQ)':<20} | {'Strategy (Rotation)':<20}")
    print("-" * 65)
    
    print(f"{'CAGR':<16} | {metrics['Benchmark (B&H QQQ)'][1]*100:19.2f}% | {metrics['Strategy (Rotation)'][1]*100:19.2f}%")
    print(f"{'Sharpe Ratio':<16} | {metrics['Benchmark (B&H QQQ)'][0]:20.2f} | {metrics['Strategy (Rotation)'][0]:20.2f}")
    print(f"{'Max Drawdown':<16} | {metrics['Benchmark (B&H QQQ)'][2]*100:19.2f}% | {metrics['Strategy (Rotation)'][2]*100:19.2f}%")

if __name__ == "__main__":
    main()
