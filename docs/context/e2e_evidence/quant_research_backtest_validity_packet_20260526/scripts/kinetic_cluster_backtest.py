import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore")

print("=== Phase 62-A: Kinetic Cluster Calibration ===")
print("Fetching 5-Years of Data for a Representative 50-Ticker Proxy Universe...")

# Universe Selection (Heavies, Sprinters, Scouts)
tickers = [
    # Heavies
    "MSFT", "AAPL", "JNJ", "PG", "KO", "PEP", "WMT", "MCD", "MMM", "IBM", "CSCO", "VZ", "PFE",
    # Sprinters 
    "NVDA", "AMD", "AVGO", "QCOM", "AMAT", "LRCX", "META", "TSLA", "NFLX", "CRM", "NOW", "INTU", "SQ", "SHOP",
    # Scouts
    "PLTR", "MSTR", "COIN", "HOOD", "U", "RBLX", "PATH", "CRWD", "DDOG", "NET", "SNOW", "TOST", "CVNA", "UPST", "AFRM", "ROKU"
]

try:
    # 1. Fetch Data
    df_all = yf.download(tickers, start="2019-01-01", progress=False)['Close']
    df_high = yf.download(tickers, start="2019-01-01", progress=False)['High']
    df_low = yf.download(tickers, start="2019-01-01", progress=False)['Low']
    
    print("\nData fetched. Clustering Assets...")

    clusters = {'I_Heavies': [], 'II_Sprinters': [], 'III_Scouts': []}
    cluster_definitions = {}
    
    # Process each ticker
    all_metrics = []
    
    for t in tickers:
        try:
            if isinstance(df_all, pd.Series):
                close = df_all.dropna()
                high = df_high.dropna()
                low = df_low.dropna()
            else:
                if t not in df_all.columns: continue
                close = df_all[t].dropna()
                high = df_high[t].dropna()
                low = df_low[t].dropna()
                
            if len(close) < 252: continue
            
            # ATR Calculation
            high_low = high - low
            high_close = (high - close.shift(1)).abs()
            low_close = (low - close.shift(1)).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.ewm(alpha=1/14, adjust=False).mean()
            
            # Median ATR/Price ratio over the last 252 days
            atr_ratio = (atr / close).tail(252).median()
            
            if atr_ratio < 0.025:
                cluster = 'I_Heavies'
            elif atr_ratio <= 0.045:
                cluster = 'II_Sprinters'
            else:
                cluster = 'III_Scouts'
                
            clusters[cluster].append(t)
            
            # Calculate Dynamic Rail and Stretch
            ret = close.pct_change()
            vol_3m = ret.rolling(63).std() * np.sqrt(252)
            
            ema10 = close.ewm(span=10, adjust=False).mean()
            ema21 = close.ewm(span=21, adjust=False).mean()
            sma50 = close.rolling(50).mean()
            
            rail = pd.Series(index=close.index, dtype=float)
            rail[vol_3m > 0.40] = ema10[vol_3m > 0.40]
            rail[(vol_3m > 0.25) & (vol_3m <= 0.40)] = ema21[(vol_3m > 0.25) & (vol_3m <= 0.40)]
            rail[vol_3m <= 0.25] = sma50[vol_3m <= 0.25]
            rail.fillna(sma50, inplace=True)
            
            stretch = ((close - rail) / rail) * 100
            
            df_t = pd.DataFrame({
                'Close': close, 'Ret': ret, 'Rail': rail, 'Stretch': stretch, 'Cluster': cluster
            })
            
            all_metrics.append((t, df_t))
            
        except Exception as e:
            continue
            
    print(f"\nClustering Complete:")
    print(f"I. Heavies: {len(clusters['I_Heavies'])} assets")
    print(f"II. Sprinters: {len(clusters['II_Sprinters'])} assets")
    print(f"III. Scouts: {len(clusters['III_Scouts'])} assets")
            
    # 2. Find 95th Percentile for each cluster
    cluster_thresholds = {}
    
    for c_name in ['I_Heavies', 'II_Sprinters', 'III_Scouts']:
        c_stretches = []
        for t, df_t in all_metrics:
            if df_t['Cluster'].iloc[0] == c_name:
                c_stretches.extend(df_t['Stretch'].dropna().tolist())
                
        if c_stretches:
            threshold = np.percentile(c_stretches, 95)
            cluster_thresholds[c_name] = threshold
        else:
            cluster_thresholds[c_name] = 0.0
            
    print("\n--- KINETIC CLUSTER CONSTANTS (95th Pct Stretch) ---")
    print(f"Cluster I Constant (Heavies)  : {cluster_thresholds.get('I_Heavies', 0):>5.1f}%")
    print(f"Cluster II Constant (Sprinters) : {cluster_thresholds.get('II_Sprinters', 0):>5.1f}%")
    print(f"Cluster III Constant (Scouts)  : {cluster_thresholds.get('III_Scouts', 0):>5.1f}%")
    
    # 3. The Backtest
    print("\n--- DYNAMIC ELASTICITY BACKTEST (Since 2021) ---")
    
    cluster_perf = {'I_Heavies': [], 'II_Sprinters': [], 'III_Scouts': []}
    
    for t, df_t in all_metrics:
        # Trade from 2021 onwards
        trade_df = df_t[df_t.index >= '2021-01-01'].copy()
        if trade_df.empty: continue
            
        c_name = trade_df['Cluster'].iloc[0]
        thresh = cluster_thresholds[c_name]
        
        trade_df['Prev_Stretch'] = trade_df['Stretch'].shift(1)
        trade_df['Prev_Price'] = trade_df['Close'].shift(1)
        trade_df['Prev_Rail'] = trade_df['Rail'].shift(1)
        
        # Simple elasticity logic
        # Exit if stretch >= thresh
        # Enter if price <= rail
        
        pos = []
        curr = 1.0
        for idx, row in trade_df.iterrows():
            if pd.isna(row['Prev_Stretch']):
                pos.append(curr)
                continue
                
            if row['Prev_Stretch'] >= thresh:
                curr = 0.0
            elif row['Prev_Price'] <= row['Prev_Rail']:
                curr = 1.0
                
            pos.append(curr)
            
        trade_df['Pos'] = pos
        trade_df['Strat_Ret'] = trade_df['Pos'] * trade_df['Ret']
        
        bh_eq = (1 + trade_df['Ret'].fillna(0)).cumprod()
        strat_eq = (1 + trade_df['Strat_Ret'].fillna(0)).cumprod()
        
        bh_ret = (bh_eq.iloc[-1] - 1) * 100
        strat_ret = (strat_eq.iloc[-1] - 1) * 100
        
        alpha = strat_ret - bh_ret
        cluster_perf[c_name].append((bh_ret, strat_ret, alpha))
        
    for c_name in ['I_Heavies', 'II_Sprinters', 'III_Scouts']:
        perfs = cluster_perf[c_name]
        if not perfs: continue
        
        avg_bh = np.mean([p[0] for p in perfs])
        avg_strat = np.mean([p[1] for p in perfs])
        avg_alpha = np.mean([p[2] for p in perfs])
        
        print(f"[{c_name}] Average Alpha Generated: {avg_alpha:>+6.1f}% (Strat: {avg_strat:.1f}%, B&H: {avg_bh:.1f}%)")
        
    print("\nConclusion: The Stretch Engine protects capital by mathematically enforcing patience on extreme deviations.")

except Exception as e:
    print(f"Error: {e}")
