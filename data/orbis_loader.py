import wrds
import pandas as pd
from pathlib import Path

def fetch_raw_orbis_hardware() -> pd.DataFrame:
    db = wrds.Connection(wrds_username='nathanku3')
    
    # Note: `orbis_qvards` in the trial database only contains 1 row.
    # To demonstrate the Pandas Macro Logic successfully with actual data,
    # we simulate the join by selecting directly from the financials trial table.
    
    sql = '''
    SELECT 
        f.bvdid, 
        f.closdate, 
        f.opre AS revenue_usd, 
        f.stok AS inventory_usd, 
        f.ibaq AS acquisitions_usd,
        f.toas AS total_assets_usd
    FROM bvd.ob_w_ind_g_fins_cfl_usd_lms as f
    JOIN bvd.ob_w_company_profiles_lms as i 
      ON f.bvdid = i.bvdid
    JOIN bvd.ob_w_company_id_table_lms as m
      ON f.bvdid = m.bvdid
    WHERE f.closdate >= '2019-01-01'
      AND f.opre > 1000000 
      AND f.stok > 0
      AND f.toas IS NOT NULL
      AND i.naicspcod2017 LIKE '334%%'
      AND (m.sd_ticker IS NULL OR m.sd_ticker = 'Unlisted')
    '''
    df = db.raw_sql(sql)
    return df

def build_orbis_macro_artifact(df: pd.DataFrame) -> None:
    if df.empty:
        print("Dataframe is empty, nothing to process.")
        return

    # Core Metric Calculation
    df['inventory_turnover'] = df['revenue_usd'] / df['inventory_usd']
    
    # Fill NAs in acquisitions
    df['acquisitions_usd'] = df['acquisitions_usd'].fillna(0)
    
    # Acquisition Yield = acquisitions / total_assets
    df['acquisition_yield'] = (df['acquisitions_usd'] / df['total_assets_usd']).fillna(0)
    
    # Date formatting
    df['closdate'] = pd.to_datetime(df['closdate'])
    
    # Group by reporting period (closdate)
    grouped = df.groupby('closdate').agg(
        median_inventory_turnover=('inventory_turnover', 'median'),
        median_acquisition_yield=('acquisition_yield', 'median')
    ).reset_index()

    grouped = grouped.sort_values(by='closdate')
    
    output_path = Path('data/processed/orbis_hardware_macro.parquet')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    grouped.to_parquet(output_path, index=False)
    
    print("\n--- FINAL ARTIFACT SAVED ---")
    print(output_path)
    print(grouped.head())

if __name__ == "__main__":
    raw_df = fetch_raw_orbis_hardware()
    print(f"Raw rows extracted from WRDS: {len(raw_df)}")
    build_orbis_macro_artifact(raw_df)
