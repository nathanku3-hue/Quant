import pandas as pd
import yfinance as yf
import numpy as np
from sklearn.cluster import KMeans
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def get_hurst(ts):
    """Estimate Hurst exponent using simple R/S variance scaling."""
    lags = range(2, 20)
    tau = []
    prices = ts.values
    for lag in lags:
        # Standard deviation of log price difference
        diff = np.subtract(prices[lag:], prices[:-lag])
        tau.append(np.std(diff))
    
    # Fit line to log-log plot to get exponent H. (sigma scales as k^H)
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0]

def main():
    tickers = ['MU', 'TSM', 'AMD', 'NVDA', 'CIFR', 'MARA', 'COIN', 'QQQ', 'SPY']
    print("Fetching 1-Year trailing data...")
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    
    try:
        data = yf.download(tickers, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)['Close']
        if isinstance(data, pd.Series):
            data = pd.DataFrame(data, columns=tickers)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return
        
    prices = data.ffill().dropna(how='all')
    
    if 'SPY' not in prices.columns:
        print("Error: SPY data is missing.")
        return
        
    returns = prices.pct_change().dropna()
    var_spy = returns['SPY'].var()
    
    results = []
    for t in tickers:
        if t not in returns.columns or t == 'SPY' or t == 'QQQ': # Include QQQ in the dataset just for reference, or leave it out of clustering? The prompt included QQQ. Let's include everything except SPY, which is the benchmark.
            if t == 'SPY':
                pass # Still, we can cluster QQQ. Let's process every ticker except SPY? Actually let's include all.
        
        # We need SPY to find Beta
        if t not in prices.columns:
            continue
            
        ret = returns[t]
        log_p = np.log(prices[t])
        
        # Beta
        beta = ret.cov(returns['SPY']) / var_spy
        
        # Volatility
        vol = ret.std() * np.sqrt(252)
        
        # Hurst Exponent
        hurst = get_hurst(log_p)
        
        results.append({
            'Ticker': t,
            'Beta': beta,
            'Volatility': vol,
            'Hurst': hurst
        })
        
    df_res = pd.DataFrame(results).set_index('Ticker')
    
    print("\nApplying K-Means Clustering (n=2)...")
    # Normalize features
    features = df_res[['Volatility', 'Hurst', 'Beta']] 
    features_z = (features - features.mean()) / features.std()
    
    kmeans = KMeans(n_clusters=2, random_state=42)
    df_res['Cluster'] = kmeans.fit_predict(features_z)
    
    # Identify which cluster is Sprinter (High Vol/Hurst) and which is Sniper (Lower Vol)
    # The primary delineator asked is Volatility
    cluster_vols = df_res.groupby('Cluster')['Volatility'].mean()
    sprinter_c = cluster_vols.idxmax()
    
    df_res['Type'] = np.where(df_res['Cluster'] == sprinter_c, 'Sprinter', 'Sniper')
    df_res['Strategy'] = np.where(df_res['Type'] == 'Sprinter', 'Market Buy (Immediate)', 'Limit Buy @ Support (Patience)')
    
    print("\n--- Phase 28: Asset Execution Lane Classification ---")
    output_df = df_res[['Beta', 'Volatility', 'Hurst', 'Type', 'Strategy']].sort_values('Volatility', ascending=False)
    
    print(output_df.to_string(float_format="%.3f"))
    
    if 'NVDA' in df_res.index:
        nvda_type = df_res.loc['NVDA', 'Type']
        print(f"\nConclusion: NVDA is a {nvda_type}.")
    else:
        print("\nNVDA not found in data.")

if __name__ == '__main__':
    main()
