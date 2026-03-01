import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def run_black_swan_test(ticker, start_date, end_date, name):
    print(f"\n--- Black Swan Survival Test: {name} ({ticker}) ---")
    print(f"Period: {start_date} to {end_date}")
    
    # 1. Fetch Price Data
    data = yf.download(ticker, start=start_date, end=end_date, interval="1mo", progress=False)
    if data.empty:
        print(f"Failed to fetch {ticker}")
        return
        
    prices = data['Close'].dropna()
    if isinstance(prices, pd.DataFrame): prices = prices.iloc[:, 0]
    
    # Fetch 10-Year Treasury Yield
    tnx_data = yf.download("^TNX", start=start_date, end=end_date, interval="1mo", progress=False)
    if tnx_data.empty:
        print("Failed to fetch ^TNX")
        return
        
    tnx = tnx_data['Close'].dropna()
    if isinstance(tnx, pd.DataFrame): tnx = tnx.iloc[:, 0]
    
    # Align data
    df = pd.DataFrame({'Price': prices, 'US10Y': tnx}).dropna()
    if len(df) < 4:
        print("Not enough complete data for the requested period.")
        return
        
    # Calculate Macro Gravity (50bps rise per quarter = -15 penalty)
    # Using a 3-month (quarterly) lookback for yield change
    df['Yield_Change_3M'] = df['US10Y'] - df['US10Y'].shift(3)
    
    # Assume base Alpha Quad Score is 100 (Perfect Physics) for robust assets like NVDA/QQQ going into the crash
    df['Base_Score'] = 100
    
    # Gravity Haircut Calculation
    # For every 50bps (0.50) rise, subtract 15 points.
    df['Gravity_Penalty'] = np.where(df['Yield_Change_3M'] > 0, (df['Yield_Change_3M'] / 0.50) * 15, 0)
    df['Adjusted_Score'] = df['Base_Score'] - df['Gravity_Penalty']
    
    df['Action_With_Gravity'] = np.where(df['Adjusted_Score'] >= 90, "LONG", "CASH/EXIT")
    
    # Track Drawdowns
    cummax = df['Price'].cummax()
    dd_bh = (df['Price'] - cummax) / cummax
    max_dd_bh = dd_bh.min() * 100
    
    # Track Gravity Avoided Drawdown
    # If action is CASH/EXIT, our equity is flat.
    df['Strat_Ret'] = np.where(df['Action_With_Gravity'].shift(1) == "LONG", df['Price'].pct_change(), 0.0)
    # Rebuild equity curve
    strat_cum = (1 + df['Strat_Ret'].fillna(0)).cumprod()
    s_cummax = strat_cum.cummax()
    s_dd = (strat_cum - s_cummax) / s_cummax
    max_dd_strat = s_dd.min() * 100
    
    # Output timeline around the crash apex
    print(f"\nTimeline Leading into and Exiting the Crash:")
    print(f"{'Date':<12} | {'Price':<8} | {'US10Y':<7} | {'Yield \\Delta':<12} | {'Adj Score':<10} | {'Action':<15}")
    print("-" * 75)
    
    for i in range(3, len(df), 2): # print every 2 months to save space
        date_str = df.index[i].strftime('%Y-%m')
        prc = f"${df['Price'].iloc[i]:.2f}"
        yld = f"{df['US10Y'].iloc[i]:.2f}%"
        d_yld = f"{df['Yield_Change_3M'].iloc[i]:+.2f}%"
        scr = f"{df['Adjusted_Score'].iloc[i]:.0f}"
        act = df['Action_With_Gravity'].iloc[i]
        
        print(f"{date_str:<12} | {prc:<8} | {yld:<7} | {d_yld:<12} | {scr:<10} | {act:<15}")

    print("\n--- Survivor Report ---")
    print(f"Buy & Hold Max Drawdown: {max_dd_bh:.2f}%")
    print(f"Gravity Filter Max Drawdown: {max_dd_strat:.2f}%")
    print(f"Drawdown Avoided: {abs(max_dd_bh) - abs(max_dd_strat):.2f}%")
    
    if abs(max_dd_bh) - abs(max_dd_strat) < 10.0:
         print("[Conclusion]: Model still suffered a massive drawdown. The Gravity Filter needs heavier weighting.")
    else:
         print("[Conclusion]: [SUCCESS] The Macro Gravity Filter successfully detected the Liquidity Vacuum and protected capital BEFORE the physics broke.")

def main():
    print("Initiating Priority 1: Macro Gravity Cache & Black Swan Survival Test")
    
    # 2022 (The Gravity Crash): Rising Rates vs Stable Earnings
    run_black_swan_test("NVDA", "2021-06-01", "2023-01-01", "2022 Fed Rate Hike Cycle")
    
    # 2008 (GFC): The Yield Curve / Liquidity freeze 
    run_black_swan_test("QQQ", "2007-06-01", "2009-06-01", "2008 Global Financial Crisis")

if __name__ == '__main__':
    main()
