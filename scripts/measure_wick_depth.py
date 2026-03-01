import yfinance as yf
import pandas as pd
import numpy as np

# 1. The Universe
clusters = {
    "I (Heavies)": ["MSFT", "KO", "JPM"],
    "II (Sprinters)": ["NVDA", "AMD", "COST"],
    "III (Scouts)": ["PLTR", "COIN", "MSTR"]
}

print("=== Phase 62-G: Empirical Wick Depth Measurement ===")
print("Iterating through 3 years of daily data...\n")

def get_wick_depths(tickers):
    depths = []
    
    # Fetch 3 years of daily data
    hist = yf.download(tickers, period="3y", progress=False)
    
    for t in tickers:
        try:
            if isinstance(hist.columns, pd.MultiIndex):
                df = hist.xs(t, level=1, axis=1).dropna()
            else:
                df = hist.dropna() if len(tickers) == 1 else pd.DataFrame() # Fallback, should use multiindex
                
            if df.empty or 'Close' not in df or 'Low' not in df:
                continue
                
            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            
            # Find triggers: Close crosses below 50-SMA (Support Fracture)
            # To ensure it's a fresh fracture, previous close should be above or equal to prev SMA_50
            df['Prev_Close'] = df['Close'].shift(1)
            df['Prev_SMA_50'] = df['SMA_50'].shift(1)
            
            fractures = df[(df['Close'] < df['SMA_50']) & (df['Prev_Close'] >= df['Prev_SMA_50'])]
            
            for index, row in fractures.iterrows():
                # Find the index of the fracture
                idx = df.index.get_loc(index)
                
                # Ensure we have 5 days ahead to look at
                if idx + 5 < len(df):
                    next_5_days = df.iloc[idx : idx + 6] # includes fracture day + 5 next days
                    lowest_low = next_5_days['Low'].min()
                    sma_at_trigger = row['SMA_50']
                    
                    if sma_at_trigger > 0:
                        wick_depth = (lowest_low - sma_at_trigger) / sma_at_trigger
                        depths.append(wick_depth * 100) # Store as percentage
        except Exception as e:
            pass
            
    return depths

# 2. & 3. Measure & Output
for cluster_name, tickers in clusters.items():
    depths = get_wick_depths(tickers)
    
    if depths:
        # We want the 90th percentile of the *negative* depth, which means the 10th percentile of the raw values (since they are negative, e.g. -5% vs -1%)
        # lowest_low is smaller than sma, so wick_depth is negative. 
        # A deeper drop means a more negative number. The 90th percentile of drop depth implies we sort by magnitude of drop.
        # Let's take absolute values to represent "Drop Depth"
        abs_depths = [abs(d) for d in depths if d < 0] # Only consider actual drops below SMA
        
        if abs_depths:
            p90_wick = np.percentile(abs_depths, 90)
            print(f"Cluster {cluster_name} 90th Percentile Wick: -{p90_wick:.2f}%")
        else:
             print(f"Cluster {cluster_name} 90th Percentile Wick: No meaningful drops found.")
    else:
        print(f"Cluster {cluster_name} 90th Percentile Wick: Insufficient Data")
