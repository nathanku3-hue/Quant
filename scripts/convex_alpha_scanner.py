import pandas as pd
import yfinance as yf
import warnings
import concurrent.futures

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
            if 'Net Income' in inc.index:
                op_inc = inc.loc['Net Income'].dropna()
            else:
                return None
                
        if len(rev) < 3 or len(op_inc) < 3:
            return None
            
        # Revenue Acceleration: YoY Growth
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
    print("Initiating Phase 37: The Convex Alpha Scanner...")
    tickers = ['NVDA', 'AVGO', 'MU', 'TER', 'AMD', 'TSM', 'AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN', 'TSLA', 'SMCI', 'VRT', 'CIEN', 'COHR']
    
    print("Fetching Quarterly Financials for precision analysis...")
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_financials, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                results.append(res)
                
    df = pd.DataFrame(results)
    
    if df.empty:
        print("Failed to fetch financials.")
        return
        
    # The Convex Logic
    df['Raw_Excellence'] = (df['Margin_Delta'] * 100) + (df['Accel'] * 100)
    
    # Step A (The Guillotine)
    df['Convex_Score'] = 0.0
    for idx, row in df.iterrows():
        if row['Margin_Delta'] < 0 or row['Accel'] < 0:
            df.at[idx, 'Convex_Score'] = 0.0
        else:
            # Step B (The Power Law) - Cubed
            df.at[idx, 'Convex_Score'] = row['Raw_Excellence'] ** 3
            
    df = df.sort_values(by='Convex_Score', ascending=False)
    
    print("\n--- The Convex Elite: Super-Cycle Power Law Ranking ---")
    print(f"{'Ticker':<8} | {'Margin Delta':<14} | {'Rev Accel':<12} | {'Convex Score':<15}")
    print("-" * 55)
    
    for index, row in df.iterrows():
        margin_str = f"{row['Margin_Delta']*100:+.2f}%"
        accel_str = f"{row['Accel']*100:+.2f}%"
        score_str = f"{row['Convex_Score']:,.0f}" if row['Convex_Score'] > 0 else "0 (Killed)"
        
        print(f"{row['Ticker']:<8} | {margin_str:<14} | {accel_str:<12} | {score_str:<15}")

if __name__ == '__main__':
    main()
