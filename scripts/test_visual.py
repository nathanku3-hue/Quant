import pandas as pd
import yfinance as yf

# Load Macro Data
macro_df = pd.read_parquet('data/processed/osiris_aligned_macro.parquet')
macro_df.set_index('fiscal_date', inplace=True)
z_score_col = 'median_inv_turnover_z252'

# Load QQQ
qqq = yf.download('QQQ', start='2019-12-01', end='2022-12-31', progress=False)
if isinstance(qqq.columns, pd.MultiIndex):
    if 'QQQ' in qqq.columns.get_level_values(1):
        qqq = qqq.xs('QQQ', axis=1, level=1)
    else:
        qqq.columns = qqq.columns.get_level_values(0)
elif isinstance(qqq, pd.DataFrame) and 'QQQ' in qqq.columns:
     qqq = qqq['QQQ']

qqq.index = pd.to_datetime(qqq.index).tz_localize(None)

common_idx = macro_df.index.intersection(qqq.index)
df = pd.DataFrame({'QQQ': qqq['Close'], 'Z': macro_df[z_score_col]}).loc[common_idx]

# Check 2020-2021 (Pandemic Gap)
df_20_21 = df.loc['2020-03-01':'2021-12-31']
print('\n=== 2020 to 2021 Pandemic Gap ===')
print(f"QQQ Start (March 2020): {df_20_21['QQQ'].iloc[0]:.2f}")
print(f"QQQ End (Dec 2021): {df_20_21['QQQ'].iloc[-1]:.2f}")
red_days = (df_20_21['Z'] < -1).sum()
print(f"How many days were RED (Z < -1): {red_days} / {len(df_20_21)} days")

# Check 2022 Crash (Did Z-Score turn red BEFORE QQQ crashed?)
print('\n=== 2022 Crash Timing ===')
df_crash = df.loc['2021-11-01':'2022-06-30']
df_monthly = df_crash.resample('M').last()
print(df_monthly[['QQQ', 'Z']])

# Find EXACT date Z-Score crossed below -1 before/during the 2022 crash
red_days_df = df_crash[df_crash['Z'] < -1]
if not red_days_df.empty:
    first_red_day = red_days_df.index[0]
    z_val = red_days_df.iloc[0]['Z']
    q_val = red_days_df.iloc[0]['QQQ']
    print(f"\nFirst Red Day (< -1) in late 21/early 22: {first_red_day.date()} at Z={z_val:.2f}, QQQ={q_val:.2f}")
else:
    print('\nNo Red Days in that window.')
