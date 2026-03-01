import pandas as pd
import numpy as np
import os

def load_crisis_db(filepath="data/historical_crisis_db.csv"):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return pd.DataFrame()
    
    df = pd.read_csv(filepath)
    return df

def analyze_dotcom(df):
    print("--- 2000 Dot-Com Bubble (The Divergence of Margins & Channel Stuffing) ---")
    dotcom = df[df['crisis_id'] == 'dotcom_2000'].copy()
    
    for ticker in dotcom['ticker'].unique():
        tdf = dotcom[dotcom['ticker'] == ticker].copy()
        tdf = tdf.sort_values('quarter')
        tdf['rev_growth_qoq'] = tdf['revenue'].pct_change()
        tdf['ar_growth_qoq'] = tdf['accounts_receivable'].pct_change()
        tdf['gm_delta'] = tdf['gross_margin'].diff()
        
        # Channel Stuffing Delta (AR growing faster than Revenue)
        tdf['channel_stuff_delta'] = tdf['ar_growth_qoq'] - tdf['rev_growth_qoq']
        
        print(f"\n[{ticker}]")
        for idx, row in tdf.iterrows():
            if pd.isna(row['rev_growth_qoq']): continue
            
            warning = ""
            if row['gm_delta'] < 0 and row['rev_growth_qoq'] > 0:
                warning += "[DIVERGENCE OF DOOM] "
            if row['channel_stuff_delta'] > 0.05: # AR growing 5% faster than rev
                warning += "[CHANNEL STUFFING FLAG] "
                
            # Formatting
            prc = f"${row['price']:.2f}"
            rev = f"{row['revenue']}"
            gm = f"{row['gm_delta']:+.3f}"
            cs = f"{row['channel_stuff_delta']:+.3f}"
            print(f"{row['quarter']}: Prc {prc:<7} | Rev {rev:<5} | d(GM) {gm:<6} | d(AR)-d(Rev) {cs:<6} | {warning}")

def analyze_covid(df):
    print("\n--- 2020-2022 COVID Shock (Price/Sales Multiple Compression vs Real Rates) ---")
    covid = df[df['crisis_id'] == 'covid_2020'].copy()
    
    for ticker in covid['ticker'].unique():
        tdf = covid[covid['ticker'] == ticker].copy()
        tdf = tdf.sort_values('quarter')
        
        print(f"\n[{ticker}]")
        for idx, row in tdf.iterrows():
            ps = f"{row['price_sales']:.1f}" if pd.notna(row['price_sales']) else "N/A"
            rates = row['real_rate_tips']
            if pd.isna(rates): continue
            
            warning = ""
            if pd.notna(row['price_sales']) and float(row['price_sales']) > 20:
                # If Real Yield is positive or rising and P/S > 20
                if rates > 0:
                    warning = "[LETHAL: High P/S & Positive Real Rates]"
                elif rates > -0.005: # Real rates approaching 0/positive
                    warning = "[WARNING: Real Yields Rising vs High P/S]"
                
            print(f"{row['quarter']}: Prc ${row['price']:<5} | P/S: {ps:<4} | TIPS (Real Yield): {rates:>+6.3f} | {warning}")

def main():
    print("Initiating Priority 1: Historical Crisis Data Extraction & Ingestion...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    csv_path = os.path.join(project_root, "data", "historical_crisis_db.csv")
    
    df = load_crisis_db(filepath=csv_path)
    if df.empty:
         return
         
    analyze_dotcom(df)
    analyze_covid(df)

if __name__ == "__main__":
    main()
