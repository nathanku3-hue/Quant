import pandas as pd
import numpy as np

def run_stress_test(ticker, data):
    print(f"\n--- Stress Test: {ticker} Super Cycle ---")
    df = pd.DataFrame(data)
    
    # Calculate Deltas
    df['Delta_Demand'] = df['Rev_Growth'] - df['Rev_Growth'].shift(1) # Acceleration
    df['Delta_Pricing'] = df['GM'] - df['GM'].shift(1)
    df['Delta_Supply'] = df['Turnover'] - df['Turnover'].shift(1)
    
    # Track actions
    df['Score'] = 0
    df['Action'] = ""
    df['Signal'] = ""
    
    for i in range(1, len(df)):
        dem = df.loc[i, 'Rev_Growth'] > 0 # Absolute demand growing
        d_dem = df.loc[i, 'Delta_Demand']
        d_prc = df.loc[i, 'Delta_Pricing']
        d_sup = df.loc[i, 'Delta_Supply']
        
        # The Grave Signal (Divergence of Doom)
        # Demand is still (+) but Pricing (GM) turns (-)
        grave_signal = dem and (d_prc < 0)
        
        score = 50 # Default middle
        
        # Proper scoring logic
        if dem and d_prc > 0 and d_sup >= 0:
            score = 100
            signal = "Super Cycle (Q1)"
        elif grave_signal and d_dem > 0:
            score = 20
            signal = "Divergence of Doom (Q3)"
        elif not dem and d_prc < 0:
            score = 0
            signal = "Value Trap (Q4)"
        elif grave_signal:
            score = 20
            signal = "Divergence of Doom (Q3)"
        else:
            score = 50
            signal = "Transition"
            
        df.at[i, 'Score'] = score
        df.at[i, 'Signal'] = signal
        
        if score == 100:
            df.at[i, 'Action'] = "LONG (Hold)"
        elif score >= 90:
            df.at[i, 'Action'] = "COVERED CALL"
        else:
            # Yield Barrier Risk Free
            df.at[i, 'Action'] = "CASH / SHORT"
            
    # Output the Timeline
    print(f"{'Quarter':<10} | {'Price':<6} | {'GM':<6} | {'Prc_Dlt':<8} | {'Signal':<25} | {'Action':<15}")
    print("-" * 80)
    for i in range(1, len(df)):
        row = df.iloc[i]
        gm_pct = f"{row['GM']*100:.1f}%"
        prc_str = f"{row['Delta_Pricing']*100:+.1f}%"
        print(f"{row['Quarter']:<10} | ${row['Price']:<5.0f} | {gm_pct:<6} | {prc_str:<8} | {row['Signal']:<25} | {row['Action']:<15}")
        
    # Analyze Top Detection
    peak_price = df['Price'].max()
    peak_idx = df['Price'].idxmax()
    peak_qtr = df.loc[peak_idx, 'Quarter']
    
    # Find the first "Divergence of Doom"
    doom_frames = df[df['Signal'] == 'Divergence of Doom (Q3)']
    if not doom_frames.empty:
        first_doom = doom_frames.iloc[0]
        doom_qtr = first_doom['Quarter']
        doom_price = first_doom['Price']
        
        print(f"\n[Diagnosis]: Absolute Peak was {peak_qtr} at ${peak_price}")
        if df[df['Quarter'] == doom_qtr].index[0] <= peak_idx:
            print(f"[Success]: Model fired 'Divergence of Doom' in {doom_qtr} at ${doom_price} BEFORE/AT the peak!")
        else:
            print(f"[Warning]: Model fired 'Divergence of Doom' in {doom_qtr} at ${doom_price} AFTER the peak.")
    else:
        print("\n[Failure]: Model never detected the top.")

def main():
    print("Initiating Phase 40: The 'Top-Detection' Stress Test...")
    
    csco_data = [
        {'Quarter': '1999-Q1', 'Price': 25, 'Rev_Growth': 0.40, 'GM': 0.650, 'Turnover': 8.0},
        {'Quarter': '1999-Q2', 'Price': 30, 'Rev_Growth': 0.45, 'GM': 0.655, 'Turnover': 8.2},
        {'Quarter': '1999-Q3', 'Price': 35, 'Rev_Growth': 0.48, 'GM': 0.660, 'Turnover': 8.5},
        {'Quarter': '1999-Q4', 'Price': 45, 'Rev_Growth': 0.50, 'GM': 0.650, 'Turnover': 8.0}, 
        {'Quarter': '2000-Q1', 'Price': 65, 'Rev_Growth': 0.55, 'GM': 0.630, 'Turnover': 7.0}, 
        {'Quarter': '2000-Q2', 'Price': 75, 'Rev_Growth': 0.60, 'GM': 0.600, 'Turnover': 6.0}, # PEAK PRICE
        {'Quarter': '2000-Q3', 'Price': 60, 'Rev_Growth': 0.40, 'GM': 0.550, 'Turnover': 5.0}, 
        {'Quarter': '2000-Q4', 'Price': 30, 'Rev_Growth': 0.10, 'GM': 0.500, 'Turnover': 3.0}, 
        {'Quarter': '2001-Q1', 'Price': 15, 'Rev_Growth': -0.10, 'GM': 0.450, 'Turnover': 2.0}
    ]
    
    alb_data = [
        {'Quarter': '2021-Q3', 'Price': 200, 'Rev_Growth': 0.10, 'GM': 0.350, 'Turnover': 4.0},
        {'Quarter': '2021-Q4', 'Price': 250, 'Rev_Growth': 0.20, 'GM': 0.400, 'Turnover': 4.2},
        {'Quarter': '2022-Q1', 'Price': 220, 'Rev_Growth': 0.36, 'GM': 0.450, 'Turnover': 4.5},
        {'Quarter': '2022-Q2', 'Price': 250, 'Rev_Growth': 0.91, 'GM': 0.500, 'Turnover': 5.0},
        {'Quarter': '2022-Q3', 'Price': 300, 'Rev_Growth': 1.52, 'GM': 0.550, 'Turnover': 5.5}, 
        {'Quarter': '2022-Q4', 'Price': 320, 'Rev_Growth': 1.93, 'GM': 0.450, 'Turnover': 4.5}, # PEAK PRICE
        {'Quarter': '2023-Q1', 'Price': 250, 'Rev_Growth': 1.20, 'GM': 0.350, 'Turnover': 4.0}, 
        {'Quarter': '2023-Q2', 'Price': 200, 'Rev_Growth': 0.60, 'GM': 0.250, 'Turnover': 3.5},
        {'Quarter': '2023-Q3', 'Price': 150, 'Rev_Growth': 0.10, 'GM': 0.200, 'Turnover': 3.0},
        {'Quarter': '2023-Q4', 'Price': 120, 'Rev_Growth': -0.10, 'GM': 0.150, 'Turnover': 2.5}
    ]

    run_stress_test("CSCO (1999-2001)", csco_data)
    run_stress_test("ALB (2021-2024)", alb_data)
    
if __name__ == "__main__":
    main()
