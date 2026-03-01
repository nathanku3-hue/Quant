import pandas as pd
from pathlib import Path
import os

def align_orbis_macro():
    input_path = Path("data/processed/orbis_hardware_macro.parquet")
    if not input_path.exists():
        print(f"Error: Could not find {input_path}")
        return
        
    df = pd.read_parquet(input_path)
    
    # Simulate a 90 day reporting lag before the data is publically "known"
    df['knowledge_date'] = df['closdate'] + pd.Timedelta(days=90)
    
    # Build complete daily business calendar from 2015-01-01 to 2024-12-31
    # We use a broad range to ensure we cover the current timeline logic.
    start_date = "2015-01-01"
    end_date = "2024-12-31"
    
    calendar = pd.date_range(start=start_date, end=end_date, freq='B')
    cal_df = pd.DataFrame({'date': calendar})
    
    # Merge using merge_asof exactly like the main engine handles alignments
    # A merge_asof requires the alignment keys to be sorted
    df = df.sort_values(by="knowledge_date")
    cal_df = cal_df.sort_values(by="date")

    # Align the quarterly macro signal onto the daily calendar
    aligned = pd.merge_asof(
        cal_df,
        df,
        left_on="date",
        right_on="knowledge_date",
        direction="backward"
    )

    # Some early dates will be missing logic before the first knowledge_date
    aligned.fillna(method='ffill', inplace=True)
    
    # Final cleanup to keep the standard date index format
    aligned = aligned.rename(columns={'date': 'fiscal_date'})
    aligned = aligned.drop(columns=['closdate', 'knowledge_date'])
    
    output_path = Path("data/processed/orbis_daily_aligned.parquet")
    aligned.to_parquet(output_path, index=False)
    
    print("--- ORBIS DAILY ALIGNER ---")
    print(f"Artifact created: {output_path}")
    print(aligned.head())

if __name__ == "__main__":
    align_orbis_macro()
