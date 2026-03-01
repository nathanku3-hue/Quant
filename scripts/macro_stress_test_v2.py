import yfinance as yf
import pandas as pd
import numpy as np

print("=== Phase 57-C: The Dual-Factor Macro Stress Test ===")
print("Fetching Data (QQQ, ^TNX, VWEHX, VFISX) since 1995...")

try:
    # 1. The Data
    tickers = ["QQQ", "^TNX", "VWEHX", "VFISX"]
    df = yf.download(tickers, start="1995-01-01", progress=False)['Close']
    df = df.dropna()
    
    print("\nData retrieved successfully. Calculating Dual Signals...")
    
    # 2. The Logic
    
    # Signal A: The Valuation Kill Switch (Rates Spiking)
    # Velocity over ~90 calendar days = ~63 trading days
    df['Yield_Velocity'] = df['^TNX'] - df['^TNX'].shift(63)
    df['Signal_A'] = df['Yield_Velocity'] > 0.50

    # Signal B: The Solvency Kill Switch (Credit Freezing)
    # High Yield vs Treasuries Ratio
    df['Credit_Ratio'] = df['VWEHX'] / df['VFISX']
    df['Ratio_SMA200'] = df['Credit_Ratio'].rolling(window=200).mean()
    # If ratio is below 200-day moving average, Credit is underperforming Treasuries
    df['Signal_B'] = df['Credit_Ratio'] < df['Ratio_SMA200']
    
    # Shift signals by 1 day to prevent look-ahead bias
    # We can only act tomorrow on today's closing signals
    df['Active_Signal_A'] = df['Signal_A'].shift(1).fillna(False)
    df['Active_Signal_B'] = df['Signal_B'].shift(1).fillna(False)
    
    # 3. The Combined Kill Switch
    # IF (Signal A is Active) OR (Signal B is Active) -> GO TO CASH (0)
    # ELSE -> BUY QQQ (1)
    df['Position'] = np.where((df['Active_Signal_A']) | (df['Active_Signal_B']), 0, 1)
    
    # Restrict to Year 2000 onwards for reporting
    df = df[df.index >= "2000-01-01"].copy()
    
    # Calculate Returns
    df['QQQ_Return'] = df['QQQ'].pct_change()
    df['Strategy_Return'] = df['Position'] * df['QQQ_Return']
    
    # Cumulative Equity Curves
    df['QQQ_Equity'] = (1 + df['QQQ_Return']).cumprod()
    df['Strategy_Equity'] = (1 + df['Strategy_Return']).cumprod()
    
    # 4. The Output Metrics
    def calc_max_drawdown(equity_curve):
        peak = equity_curve.cummax()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min() * 100

    buy_hold_ret = (df['QQQ_Equity'].iloc[-1] - 1) * 100
    strat_ret = (df['Strategy_Equity'].iloc[-1] - 1) * 100
    
    buy_hold_dd = calc_max_drawdown(df['QQQ_Equity'])
    strat_dd = calc_max_drawdown(df['Strategy_Equity'])
    
    print("\n[PERFORMANCE RESULTS: 2000 - PRESENT]")
    print(f"Buy & Hold QQQ Return   : {buy_hold_ret:,.1f}%")
    print(f"Dual-Factor Kill Switch : {strat_ret:,.1f}%")
    print("-" * 45)
    print(f"Buy & Hold Max Drawdown : {buy_hold_dd:.1f}%")
    print(f"Sovereign Max Drawdown  : {strat_dd:.1f}%")
    print("-" * 45)
    
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
            
            # Additional detail: Time spent in Cash during the crisis
            time_in_cash = (crisis_df['Position'] == 0).mean() * 100
            
            print(f"[{name}]")
            print(f"QQQ Return: {bh_ret:>6.1f}% | Strategy: {st_ret:>6.1f}% | Cash Raised: {time_in_cash:.1f}%")
        except Exception as e:
            pass
            
    # Evaluation of specific crash periods
    evaluate_crisis("2000 Dot-com Crash (2000-03 to 2002-10)", "2000-03-01", "2002-10-01")
    evaluate_crisis("2008 GFC Liquidity Drain (2007-10 to 2009-03)", "2007-10-01", "2009-03-01")
    evaluate_crisis("2022 Fed Rate Vacuum (2021-11 to 2022-12)", "2021-11-01", "2022-12-31")

except Exception as e:
    print(f"Failed to execute backtest: {e}")
