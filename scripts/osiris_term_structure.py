import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr
import numpy as np
import warnings

warnings.filterwarnings('ignore')

def main():
    print("Loading data...")
    # Load Data
    try:
        df_signal = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
    except Exception as e:
        print(f"Error loading parquet: {e}")
        return

    # Ensure fiscal_date is datetime and tz-naive
    df_signal['fiscal_date'] = pd.to_datetime(df_signal['fiscal_date'])
    if df_signal['fiscal_date'].dt.tz is not None:
        df_signal['fiscal_date'] = df_signal['fiscal_date'].dt.tz_localize(None)
    df_signal.set_index('fiscal_date', inplace=True)

    print("Downloading QQQ data (2015-Present)...")
    # Market Data
    qqq = yf.download("QQQ", start="2015-01-01", progress=False)['Close']
    
    # Handle yfinance multi-index/dataframe variations
    if isinstance(qqq, pd.DataFrame):
        if "QQQ" in qqq.columns:
            qqq = qqq["QQQ"]
        else:
            qqq = qqq.iloc[:, 0]
            
    qqq_index = pd.to_datetime(qqq.index)
    if qqq_index.tz is not None:
        qqq_index = qqq_index.tz_localize(None)
    qqq.index = qqq_index

    df_qqq = pd.DataFrame({'QQQ': qqq})

    # Merge: Align the daily median_inv_turnover Z-Score with QQQ close prices
    df_merged = df_qqq.join(df_signal[['median_inv_turnover_z252']], how='inner').dropna()

    results = []
    # Loop: For each horizon h
    horizons = [10, 20, 30, 40, 50, 60, 90, 120]
    for h in horizons:
        future_return_col = f'Future_Return_{h}'
        df_merged[future_return_col] = df_merged['QQQ'].shift(-h) / df_merged['QQQ'] - 1
        
        valid_data = df_merged[['median_inv_turnover_z252', future_return_col]].dropna()
        if len(valid_data) > 0:
            corr, p_val = spearmanr(valid_data['median_inv_turnover_z252'], valid_data[future_return_col])
        else:
            corr, p_val = np.nan, np.nan
            
        results.append({
            'Horizon (Days)': h,
            'IC (Correlation)': corr,
            'P-Value': p_val
        })
        
    df_results = pd.DataFrame(results)
    
    # Output: Print a clean table
    print("\nHorizon (Days) | IC (Correlation) | P-Value")
    print("-" * 50)
    for idx, row in df_results.iterrows():
        print(f"{int(row['Horizon (Days)']):14d} | {row['IC (Correlation)']:16.4f} | {row['P-Value']:.4e}")

if __name__ == "__main__":
    main()
