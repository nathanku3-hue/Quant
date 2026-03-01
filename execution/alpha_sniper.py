import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def calculate_sniper_score(ticker, df, latest_z):
    # Fundamental Score
    fund_score = 0
    if latest_z > 0:
        fund_score = 50
    elif latest_z > -1.0:
        fund_score = 25
    else:
        fund_score = 0
        
    # Latest technical indicators
    current_price = df['Close'].iloc[-1]
    current_vol = df['Volume'].iloc[-1]
    
    high_52w = df['Close'].rolling(window=252, min_periods=1).max().iloc[-1]
    ma_50 = df['Close'].rolling(window=50, min_periods=1).mean().iloc[-1]
    ma_20_vol = df['Volume'].rolling(window=20, min_periods=1).mean().iloc[-1]
    
    tech_score = 0
    
    # The Pullback (Deep Value)
    if current_price < 0.85 * high_52w:
        tech_score += 20
        
    # The Support (At Institutional Support)
    if current_price <= 1.02 * ma_50:
        tech_score += 20
        
    # The Exhaustion (Sellers tired)
    if current_vol < 0.8 * ma_20_vol:
        tech_score += 10
        
    total_score = fund_score + tech_score
    
    # Execution Logic
    if total_score >= 80:
        action = "LIMIT BUY"
        target_entry = min(ma_50, current_price)
    elif total_score >= 60:
        action = "WAIT"
        target_entry = min(ma_50, current_price) # Just for display
    else:
        action = "IGNORE"
        target_entry = np.nan
        
    return {
        'Ticker': ticker,
        'Fundamental': fund_score,
        'Technical': tech_score,
        'Total Score': total_score,
        'Action': action,
        'Target Entry': target_entry,
        'Current Price': current_price
    }

def main():
    print("Initializing Alpha Sniper...")
    tickers = ['NVDA', 'MU', 'TSM', 'AMD', 'CIFR', 'QQQ']
    
    # 1. Load Osiris Z-Score
    try:
        df_signal = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
        df_signal['fiscal_date'] = pd.to_datetime(df_signal['fiscal_date'])
        # Sort values just in case
        df_signal = df_signal.sort_values('fiscal_date')
        
        # Get the latest known z-score
        z_col = [c for c in df_signal.columns if 'zscore' in c.lower() or 'z252' in c.lower()][0]
        latest_z = df_signal[z_col].dropna().iloc[-1]
    except Exception as e:
        print(f"Error loading Osiris signal: {e}")
        return

    print(f"Latest Foundational Macro Z-Score: {latest_z:.2f}")

    # 2. Fetch Daily Data (Last 1 Year)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    try:
        data = yf.download(tickers, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
    except Exception as e:
        print(f"Error downloading market data: {e}")
        return
        
    results = []
    
    for t in tickers:
        if isinstance(data.columns, pd.MultiIndex):
            has_adj_close = 'Adj Close' in data.columns.get_level_values(0)
            col_name = 'Adj Close' if has_adj_close else 'Close'
            close = data[col_name][t]
            volume = data['Volume'][t]
        else:
            close = data['Close']
            volume = data['Volume']
            
        df = pd.DataFrame({'Close': close, 'Volume': volume}).dropna()
        if df.empty:
            continue
            
        res = calculate_sniper_score(t, df, latest_z)
        results.append(res)
        
    results_df = pd.DataFrame(results)
    
    # 3. Output Table
    print("\n--- The Alpha Sniper Execution Targets ---")
    print(f"{'Ticker':<8} | {'Score':<5} | {'Action':<12} | {'Current':<10} | {'Target Entry':<12}")
    print("-" * 57)
    for index, row in results_df.sort_values(by='Total Score', ascending=False).iterrows():
        target_str = f"${row['Target Entry']:.2f}" if not pd.isna(row['Target Entry']) else "N/A"
        current_str = f"${row['Current Price']:.2f}"
        print(f"{row['Ticker']:<8} | {row['Total Score']:<5} | {row['Action']:<12} | {current_str:<10} | {target_str:<12}")

if __name__ == '__main__':
    main()
