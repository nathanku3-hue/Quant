import pandas as pd
import yfinance as yf
import pandas_datareader as pdr
import datetime
import numpy as np

def fetch_data(start_date, end_date):
    print("Fetching data (5-Year History)...")
    
    # FRED Proxies
    try:
        ppi = pdr.get_data_fred('PCU334413334413', start_date, end_date)
        ppi.columns = ['PPI_Semi']
    except:
        ppi = pd.DataFrame()
        
    try:
        infra = pdr.get_data_fred('TLPWRCONS', start_date, end_date)
        infra.columns = ['TLPWRCONS']
    except:
        infra = pd.DataFrame()

    # YFinance Proxies & Assets
    tickers = ['EWY', 'MU', 'VRT', 'AMD']
    try:
        yf_data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    except:
        yf_data = pd.DataFrame()

    return ppi, infra, yf_data

def calculate_lagged_correlations(proxy_series, asset_series, lags, proxy_name, asset_name):
    # Ensure both are numeric and drop NAs
    df = pd.concat([proxy_series, asset_series], axis=1).dropna()
    if df.empty:
        return {}
    
    proxy_col = df.columns[0]
    asset_col = df.columns[1]
    
    # Calculate % change
    df_pct = df.pct_change().dropna()
    
    results = {}
    for lag in lags:
        # We want to see if Proxy at t predicts Asset at t + lag
        # So we shift the Asset backwards by 'lag' periods comparing Asset_t to Proxy_{t-lag}
        # Actually using shift: df_pct[asset_col].shift(-lag) aligns Asset(t+lag) with Proxy(t).
        
        shifted_asset = df_pct[asset_col].shift(-lag)
        corr_df = pd.concat([df_pct[proxy_col], shifted_asset.rename(f"{asset_col}_Lead_{lag}")], axis=1).dropna()
        if not corr_df.empty and len(corr_df) > 10:
            corr = corr_df.corr().iloc[0, 1]
            results[lag] = corr
        else:
            results[lag] = float('nan')
            
    return results

def main():
    print("Initiating Phase 43-C: The 'Truth Serum' (Proxy Validation)")
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=5*365) # 5 years
    
    ppi, infra, yf_data = fetch_data(start_date, end_date)
    
    # Resample to monthly ('ME' for Month End) to smooth out daily noise
    # FRED provides monthly data on the 1st
    ppi_monthly = ppi.resample('ME').last() if not ppi.empty else pd.DataFrame()
    infra_monthly = infra.resample('ME').last() if not infra.empty else pd.DataFrame()
    yf_monthly = yf_data.resample('ME').last() if not yf_data.empty else pd.DataFrame()
    
    correlations = []
    
    # 1. Semi PPI -> MU (Lags: 1, 3, 6)
    if not ppi_monthly.empty and 'MU' in yf_monthly.columns:
        res = calculate_lagged_correlations(ppi_monthly['PPI_Semi'], yf_monthly['MU'], [1, 3, 6], "PPI", "MU")
        correlations.append(("PPI -> MU", res))
        
    # 2. Construction -> VRT (Lags: 1, 3, 6)
    if not infra_monthly.empty and 'VRT' in yf_monthly.columns:
        res = calculate_lagged_correlations(infra_monthly['TLPWRCONS'], yf_monthly['VRT'], [1, 3, 6], "Construction", "VRT")
        correlations.append(("Construction -> VRT", res))
        
    # 3. EWY -> AMD (Lags: 1, 3, 6)
    if 'EWY' in yf_monthly.columns and 'AMD' in yf_monthly.columns:
        res = calculate_lagged_correlations(yf_monthly['EWY'], yf_monthly['AMD'], [1, 3, 6], "EWY", "AMD")
        correlations.append(("EWY -> AMD", res))
        
    print("\n--- Predictive Power Matrix ---")
    print(f"{'Relationship':<22} | {'Lag 1 (1 Mo)':<12} | {'Lag 3 (3 Mo)':<12} | {'Lag 6 (6 Mo)':<12} | {'Verdict'}")
    print("-" * 80)
    
    for name, lags in correlations:
        lag1 = lags.get(1, float('nan'))
        lag3 = lags.get(3, float('nan'))
        lag6 = lags.get(6, float('nan'))
        
        lag1_str = f"{lag1:.3f}" if not np.isnan(lag1) else "N/A"
        lag3_str = f"{lag3:.3f}" if not np.isnan(lag3) else "N/A"
        lag6_str = f"{lag6:.3f}" if not np.isnan(lag6) else "N/A"
        
        # Verdict logic based on max correlation across tested lags
        max_corr = max([v for v in lags.values() if not np.isnan(v)] or [0])
        if max_corr > 0.3:
            verdict = "PASS (Predictive)"
        elif max_corr < 0.1:
            if max_corr > 0:
                verdict = "FAIL (Noise/Delete)"
            else:
                verdict = "FAIL (Negative/Inverse)"
        else:
            verdict = "WEAK (Keep Watch)"
            
        print(f"{name:<22} | {lag1_str:<12} | {lag3_str:<12} | {lag6_str:<12} | {verdict}")

if __name__ == "__main__":
    main()
