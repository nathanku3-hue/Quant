import pandas as pd
import yfinance as yf
import numpy as np
import concurrent.futures
import warnings

warnings.filterwarnings('ignore')

def get_tickers():
    try:
        # Fetch S&P 500
        sp500_tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        sp500 = sp500_tables[0]['Symbol'].tolist()
    except Exception as e:
        sp500 = ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'META', 'GOOGL', 'TSLA', 'AVGO', 'JPM', 'UNH', 'LLY', 'V', 'XOM', 'JNJ', 'PG']
        
    try:
        # Fetch NASDAQ 100
        ndx_tables = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')
        # Ticker column varies by page format, looking for 'Ticker', 'Symbol'
        ndx_df = ndx_tables[4] if len(ndx_tables) > 4 else ndx_tables[3]
        col = [c for c in ndx_df.columns if 'Ticker' in c or 'Symbol' in c][0]
        ndx = ndx_df[col].tolist()
    except Exception as e:
        ndx = ['AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'GOOGL', 'TSLA', 'AVGO', 'PEP', 'COST', 'CSCO', 'TMUS', 'ADBE']

    tickers = list(set(sp500 + ndx))
    tickers = [t.replace('.', '-') for t in tickers]
    return tickers

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
    print("Initializing Phase 35: The Super-Cycle Scanner...")
    tickers = get_tickers()
    print(f"Loaded {len(tickers)} tickers from S&P 500 and NASDAQ 100.")

    print("Fetching Daily Price Data (1 Year)...")
    # 1. Price RS: Calculate 12-month return relative to SPY
    fetch_list = tickers + ['SPY']
    # Use yfinance download
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
    if pd.isna(spy_ret):
        spy_ret = 0.0
        
    rs_returns = ret_1y - spy_ret
    rs_returns = rs_returns.drop('SPY', errors='ignore').dropna()
    
    # Rank 0-100
    rs_rank = rs_returns.rank(pct=True) * 100
    
    # To avoid 500+ individual financial API calls (which takes 10+ minutes and hits rate limits),
    # we filter the universe to the top 150 assets by Relative Strength. 
    # An asset with low RS won't win the Super-Cycle equation anyway.
    top_candidates = rs_rank.sort_values(ascending=False).head(150)
    top_tickers = top_candidates.index.tolist()
    
    print(f"Fetching Quarterly Financials for {len(top_tickers)} high-RS candidates...")
    
    results = []
    # Threading for faster fetching
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_financials, t): t for t in top_tickers}
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            res = future.result()
            if res is not None:
                # Add RS Rank
                res['RS_Rank'] = rs_rank.loc[res['Ticker']]
                results.append(res)
                
    df = pd.DataFrame(results)
    if df.empty:
        print("Failed to fetch financials for candidates.")
        return
        
    df = df.dropna()
    
    # 3. The Super-Cycle Score
    # Normalize Accel and Margin_Delta to Rank (0-100) to match RS Rank mathematically
    df['Accel_Rank'] = df['Accel'].rank(pct=True) * 100
    df['Margin_Delta_Rank'] = df['Margin_Delta'].rank(pct=True) * 100
    
    df['Super_Cycle_Score'] = (df['RS_Rank'] * 0.4) + (df['Accel_Rank'] * 0.3) + (df['Margin_Delta_Rank'] * 0.3)
    
    # Sort and output
    top_10 = df.sort_values(by='Super_Cycle_Score', ascending=False).head(10)
    
    print("\n--- The Emerging Super-Cycles (Top 10) ---")
    print(f"{'Ticker':<8} | {'RS Rank':<10} | {'Rev Accel':<12} | {'Margin Delta':<14} | {'Total Score':<12}")
    print("-" * 65)
    for index, row in top_10.iterrows():
        # Display underlying values, but rank is used for the score
        accel_str = f"{row['Accel']*100:+.2f}%"
        margin_str = f"{row['Margin_Delta']*100:+.2f}%"
        print(f"{row['Ticker']:<8} | {row['RS_Rank']:<10.2f} | {accel_str:<12} | {margin_str:<14} | {row['Super_Cycle_Score']:<10.2f}")

if __name__ == "__main__":
    main()
