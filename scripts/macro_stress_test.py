import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 57-B: The Macro Stress Test (Quantitative Validation) ===")
print("Fetching ^TNX (US 10-Year Yield) and QQQ (Tech Benchmark) since 2000...")

try:
    # 1. The Data
    df = yf.download(["^TNX", "QQQ"], start="2000-01-01", progress=False)['Close']
    df = df.dropna()
    
    # Needs to be a dataframe with QQQ and ^TNX as columns
    print("\nData retrieved successfully. Calculating Yield Velocity...")
    
    # 2. The Logic
    # Calculate Yield_Velocity = TNX - TNX (90 days ago) (~63 trading days)
    # The prompt actually specifies "TNX - TNX (90 days ago)" which means calendar days. 
    # 90 calendar days is approx 63 trading days.
    df['Yield_Velocity'] = df['^TNX'] - df['^TNX'].shift(63)
    
    # Shift signals to avoid look-ahead bias (we can only trade on today's close tomorrow)
    # Actually, we can just shift the signal by 1 day
    # Signal:
    # IF Yield_Velocity > 0.50 (Rates spiking): GO TO CASH (0 exposure)
    # IF Yield_Velocity <= 0.50: BUY QQQ (1 exposure)
    df['Signal'] = np.where(df['Yield_Velocity'] > 0.50, 0, 1)
    df['Position'] = df['Signal'].shift(1).fillna(1) # Default fully invested
    
    # Calculate Returns
    df['QQQ_Return'] = df['QQQ'].pct_change()
    df['Strategy_Return'] = df['Position'] * df['QQQ_Return']
    
    # Cumulative Equity Curves
    df['QQQ_Equity'] = (1 + df['QQQ_Return']).cumprod()
    df['Strategy_Equity'] = (1 + df['Strategy_Return']).cumprod()
    
    # 3. The Output Metrics
    def calc_max_drawdown(equity_curve):
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min() * 100

    buy_hold_ret = (df['QQQ_Equity'].iloc[-1] - 1) * 100
    strat_ret = (df['Strategy_Equity'].iloc[-1] - 1) * 100
    
    buy_hold_dd = calc_max_drawdown(df['QQQ_Equity'])
    strat_dd = calc_max_drawdown(df['Strategy_Equity'])
    
    # Calculate specific crisis periods drawdowns and returns
    # 2000 Dot Com Crash (2000-03-01 to 2002-10-01)
    # 2008 GFC (2007-10-01 to 2009-03-01)
    # 2022 Fed Hike (2021-11-01 to 2022-12-31)
    
    print("\n[PERFORMANCE RESULTS: 2000 - PRESENT]")
    print(f"Buy & Hold QQQ Return : {buy_hold_ret:,.1f}%")
    print(f"Sovereign Kill Switch : {strat_ret:,.1f}%")
    print("-" * 40)
    print(f"Buy & Hold Max Drawdown : {buy_hold_dd:.1f}%")
    print(f"Sovereign Max Drawdown  : {strat_dd:.1f}%")
    print("-" * 40)
    
    time_in_market = (df['Position'] == 1).mean() * 100
    print(f"Time in Market (QQQ Exposure): {time_in_market:.1f}%\n")
    
    def evaluate_crisis(name, start_date, end_date):
        try:
            mask = (df.index >= start_date) & (df.index <= end_date)
            crisis_df = df.loc[mask].copy()
            if crisis_df.empty:
                return
            
            bh_eq = (1 + crisis_df['QQQ_Return']).cumprod()
            st_eq = (1 + crisis_df['Strategy_Return']).cumprod()
            
            bh_ret = (bh_eq.iloc[-1] - 1) * 100
            st_ret = (st_eq.iloc[-1] - 1) * 100
            
            print(f"[{name}]")
            print(f"QQQ Return: {bh_ret:>6.1f}% | Strategy: {st_ret:>6.1f}%")
        except Exception as e:
            pass
            
    evaluate_crisis("2000 Dot-com Crash (2000-03 to 2002-10)", "2000-03-01", "2002-10-01")
    evaluate_crisis("2008 GFC Liquidity Drain (2007-10 to 2009-03)", "2007-10-01", "2009-03-01")
    evaluate_crisis("2022 Fed Rate Vacuum (2021-11 to 2022-12)", "2021-11-01", "2022-12-31")

except Exception as e:
    print(f"Failed to execute backtest: {e}")
