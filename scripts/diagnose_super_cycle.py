import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def process_financials(t):
    try:
        tkr = yf.Ticker(t)
        inc = tkr.quarterly_income_stmt
        if inc is None or inc.empty:
            inc = tkr.quarterly_financials
            
        if inc is None or inc.empty:
            return None
            
        # Revenue
        if 'Total Revenue' in inc.index:
            rev = inc.loc['Total Revenue'].dropna()
        elif 'Operating Revenue' in inc.index:
            rev = inc.loc['Operating Revenue'].dropna()
        else:
            return None
            
        # Operating Income
        if 'Operating Income' in inc.index:
            op_inc = inc.loc['Operating Income'].dropna()
        else:
            # Fallback to Net Income
            if 'Net Income' in inc.index:
                op_inc = inc.loc['Net Income'].dropna()
            else:
                return None
                
        if len(rev) < 3 or len(op_inc) < 3:
            return None
            
        # Revenue Acceleration: YoY Growth
        # Safely try YoY (compare to 4 quarters ago), else fallback to QoQ
        if len(rev) >= 6:
            q1_growth = (rev.iloc[0] / rev.iloc[4]) - 1
            q2_growth = (rev.iloc[1] / rev.iloc[5]) - 1
        else:
            q1_growth = (rev.iloc[0] / rev.iloc[1]) - 1
            q2_growth = (rev.iloc[1] / rev.iloc[2]) - 1
            
        accel = q1_growth - q2_growth
        
        # Margin Expansion
        q1_margin = op_inc.iloc[0] / rev.iloc[0] if rev.iloc[0] != 0 else 0
        q2_margin = op_inc.iloc[1] / rev.iloc[1] if rev.iloc[1] != 0 else 0
        margin_delta = q1_margin - q2_margin
        
        return {
            'Ticker': t,
            'Accel': accel,
            'Margin_Delta': margin_delta
        }
    except Exception as e:
        return None

def main():
    print("Initiating Targeted Audit for AI Supply Chain Assets...")
    tickers = ['MU', 'CIEN', 'COHR', 'TER', 'VRT', 'GLW', 'ANET', 'BE']
    
    print("Fetching Daily Price Data (1 Year)...")
    fetch_list = tickers + ['SPY']
    prices = yf.download(fetch_list, period="1y", progress=False)
    
    if isinstance(prices.columns, pd.MultiIndex):
        has_adj_close = 'Adj Close' in prices.columns.get_level_values(0)
        col_name = 'Adj Close' if has_adj_close else 'Close'
        closes = prices[col_name]
    else:
        closes = prices['Close'] if 'Close' in prices.columns else prices
        
    closes = closes.dropna(how='all', axis=1)
    
    # 1 Year Return (Close / Start)
    ret_1y = (closes.iloc[-1] / closes.iloc[0]) - 1
    
    spy_ret = ret_1y.get('SPY', float('nan'))
    if pd.isna(spy_ret): spy_ret = 0.0
        
    rs_returns = ret_1y - spy_ret
    rs_returns = rs_returns.drop('SPY', errors='ignore').dropna()
    
    # Rank 0-100 specifically within this cohort, or globally?
    # Globally ranking requires pulling the whole S&P. We will just rank within this group for the audit 
    # to maintain simplicity (100 = best in group, 0 = worst). 
    rs_rank = rs_returns.rank(pct=True) * 100
    
    print("Fetching Quarterly Financials...")
    results = []
    for t in tickers:
        res = process_financials(t)
        if res is not None:
            res['RS_Rank'] = rs_rank.get(t, 0) # Fallback to 0 if missing (shouldn't happen)
            results.append(res)
        else:
            print(f"Warning: Financial data incomplete for {t}")
            
    df = pd.DataFrame(results)
    if df.empty:
        print("Failed to fetch financials.")
        return
        
    df['Accel_Rank'] = df['Accel'].rank(pct=True) * 100
    df['Margin_Delta_Rank'] = df['Margin_Delta'].rank(pct=True) * 100
    
    df['Super_Cycle_Score'] = (df['RS_Rank'] * 0.4) + (df['Accel_Rank'] * 0.3) + (df['Margin_Delta_Rank'] * 0.3)
    
    # Find Weakest Links
    df['Weak_Link'] = ""
    for idx, row in df.iterrows():
        ranks = {
            'Price Action (RS)': row['RS_Rank'],
            'Revenue Accel': row['Accel_Rank'],
            'Margin Delta': row['Margin_Delta_Rank']
        }
        weakest_metric = min(ranks, key=ranks.get)
        df.at[idx, 'Weak_Link'] = weakest_metric
    
    # Sort and output
    df = df.sort_values(by='Super_Cycle_Score', ascending=False)
    
    print("\n--- Targeted Audit: AI Supply Chain Scorecard ---")
    print(f"{'Ticker':<8} | {'Score':<8} | {'RS Rank':<8} | {'Rev Accel':<12} | {'Margin Delta':<14} | {'Weak Link Flag':<25}")
    print("-" * 85)
    
    for index, row in df.iterrows():
        accel_str = f"{row['Accel']*100:+.2f}%"
        margin_str = f"{row['Margin_Delta']*100:+.2f}%"
        
        flag = f"Low {row['Weak_Link']}"
        
        # Add descriptive context if it's glaring
        if row['Weak_Link'] == 'Margin Delta' and row['Margin_Delta'] < 0:
            flag = "Negative Margin Delta"
        elif row['Weak_Link'] == 'Revenue Accel' and row['Accel'] < 0:
            flag = "Slowing Revenue Accel"
        elif row['Weak_Link'] == 'Price Action (RS)' and row['RS_Rank'] < 50:
            flag = "Weak Price Momentum"
            
        print(f"{row['Ticker']:<8} | {row['Super_Cycle_Score']:<8.2f} | {row['RS_Rank']:<8.2f} | {accel_str:<12} | {margin_str:<14} | {flag:<25}")

if __name__ == '__main__':
    main()
