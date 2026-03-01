import pandas as pd
import yfinance as yf
from scipy.stats import spearmanr
import warnings

def run_orbis_signal_generation():
    warnings.simplefilter('ignore')

    # 1. Load Orbis Data
    orbis = pd.read_parquet('data/processed/orbis_daily_aligned.parquet')
    orbis.set_index('fiscal_date', inplace=True)
    orbis.index = pd.to_datetime(orbis.index).tz_localize(None)

    # 2. Calculate Rolling Z-Scores (1 trading year = 252 days)
    # The trial data is extremely sparse (only 3 unique values over 10 years).
    # To prevent division by zero in the Z-score calculation when rolling_std is 0
    # (caused by forward filling the exact same data point for >252 days), we add a tiny epsilon.
    for col in ['median_inventory_turnover', 'median_acquisition_yield']:
        rolling_mean = orbis[col].rolling(window=252, min_periods=60).mean()
        rolling_std = orbis[col].rolling(window=252, min_periods=60).std()
        
        # Add epsilon to prevent NaN from division by exactly 0.0
        orbis[f'{col}_zscore'] = (orbis[col] - rolling_mean) / (rolling_std + 1e-8)

    # 3. Load QQQ History
    qqq = yf.download('QQQ', start='2015-01-01', end='2024-12-31', progress=False)
    if isinstance(qqq.columns, pd.MultiIndex):
        qqq.columns = qqq.columns.droplevel(1)
    qqq.index = pd.to_datetime(qqq.index).tz_localize(None)

    # 4. Calculate Forward Returns
    for days in [20, 60, 120]:
        qqq[f'fwd_ret_{days}d'] = qqq['Close'].shift(-days) / qqq['Close'] - 1

    # 5. Merge and Align
    merged = orbis.join(qqq[['fwd_ret_20d', 'fwd_ret_60d', 'fwd_ret_120d']], how='inner')
    merged = merged.dropna(subset=[
        'median_inventory_turnover_zscore', 
        'median_acquisition_yield_zscore', 
        'fwd_ret_20d', 'fwd_ret_60d', 'fwd_ret_120d'
    ])

    # 6. Information Coefficient (IC) Test
    print('--- ORBIS MACRO IC TEST vs QQQ ---')
    print(f'N = {len(merged)} trading days aligned')
    
    for signal in ['median_inventory_turnover_zscore', 'median_acquisition_yield_zscore']:
        print(f'\nSignal: {signal}')
        for days in [20, 60, 120]:
            target = f'fwd_ret_{days}d'
            ic, pval = spearmanr(merged[signal], merged[target])
            print(f'  {target:>12}: IC = {ic:7.4f}  (p-value = {pval:.4f})')

if __name__ == "__main__":
    run_orbis_signal_generation()
