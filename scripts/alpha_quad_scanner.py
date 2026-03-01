import pandas as pd
import yfinance as yf
import concurrent.futures
import warnings
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from high_freq_data import get_commodity_scalar

warnings.filterwarnings('ignore')

def process_financials(t):
    try:
        tkr = yf.Ticker(t)
        
        inc = tkr.quarterly_income_stmt
        if inc is None or inc.empty:
            inc = tkr.quarterly_financials
            
        bs = tkr.quarterly_balance_sheet
        if bs is None or bs.empty:
            bs = tkr.quarterly_balancesheet
            
        if inc is None or inc.empty or bs is None or bs.empty:
            return None
            
        # 1. Revenue
        rev_key = 'Total Revenue' if 'Total Revenue' in inc.index else 'Operating Revenue'
        if rev_key not in inc.index:
            return None
        rev = inc.loc[rev_key].dropna()
        if len(rev) < 2: return None
        
        # Demand (Rev Growth)
        demand_growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
        # 2. Operating Margin & Gross Margin
        op_inc_key = 'Operating Income' if 'Operating Income' in inc.index else 'Net Income'
        if op_inc_key not in inc.index: return None
        op_inc = inc.loc[op_inc_key].dropna()
        if len(op_inc) < 2: return None
        
        op_margin_q1 = op_inc.iloc[0] / rev.iloc[0]
        op_margin_q2 = op_inc.iloc[1] / rev.iloc[1]
        delta_margin = op_margin_q1 - op_margin_q2
        
        if 'Gross Profit' in inc.index:
            gross = inc.loc['Gross Profit'].dropna()
            if len(gross) >= 2:
                gm_q1 = gross.iloc[0] / rev.iloc[0]
                gm_q2 = gross.iloc[1] / rev.iloc[1]
                delta_pricing = gm_q1 - gm_q2
            else:
                delta_pricing = 0.0 # fallback
        else:
            delta_pricing = 0.0 # fallback

        # 3. Supply (Inventory Turnover)
        cost_key = 'Cost Of Revenue' if 'Cost Of Revenue' in inc.index else 'Cost of Goods Sold'
        if cost_key not in inc.index and 'Cost Of Goods And Services Sold' in inc.index:
            cost_key = 'Cost Of Goods And Services Sold'
            
        inv_key = 'Inventory' if 'Inventory' in bs.index else 'Total Inventory'
        if inv_key not in bs.index and 'Net Inventory' in bs.index:
            inv_key = 'Net Inventory'
            
        delta_supply = 0.0
        if inv_key in bs.index and cost_key in inc.index:
            inv = bs.loc[inv_key].dropna()
            cost = inc.loc[cost_key].dropna()
            if len(inv) >= 2 and len(cost) >= 2:
                turn_q1 = cost.iloc[0] / inv.iloc[0] if inv.iloc[0] != 0 else 0
                turn_q2 = cost.iloc[1] / inv.iloc[1] if inv.iloc[1] != 0 else 0
                delta_supply = turn_q1 - turn_q2
        
        # 4. Receivables Growth
        rec_key = 'Accounts Receivable' if 'Accounts Receivable' in bs.index else 'Net Receivables'
        rec_growth = 0.0
        if rec_key in bs.index:
            rec = bs.loc[rec_key].dropna()
            if len(rec) >= 2 and rec.iloc[1] != 0:
                rec_growth = (rec.iloc[0] / rec.iloc[1]) - 1

        # 5. Price to Sales
        try:
            ps = tkr.info.get('priceToSalesTrailing12Months', 0.0)
            if ps is None:
                ps = 0.0
        except Exception:
            ps = 0.0
        
        return {
            'Ticker': t,
            'Delta_Demand': demand_growth,
            'Delta_Supply': delta_supply,
            'Delta_Pricing': delta_pricing,
            'Delta_Margin': delta_margin,
            'Receivables_Growth': rec_growth,
            'Price_to_Sales': ps
        }
    except Exception as e:
        return None

def run_alpha_sovereign_scan(manual_inputs=None):
    if manual_inputs is None: manual_inputs = {}
    print("Initiating Phase 39: The 'Opportunity Gate' Final Matrix with Crisis Gates & Cyborg Sensing...")
    tickers = ['NVDA', 'MU', 'AMD', 'TSM', 'AVGO', 'INTC', 'TSLA', 'MSFT', 'META', 'AMZN', 'GOOGL', 'SMCI', 'VRT', 'CEG', 'ETN', 'CLS', 'TER', 'LRCX', 'AMAT', 'SNDK', 'WDC', 'CIEN', 'COHR', 'RBRK', 'NBIS']
    
    print("Fetching Macro Crisis data (VIX & US10Y)...")
    try:
        # Batch fetch macro context
        macro_df = yf.download("^TNX ^VIX", period="5d", progress=False)['Close']
        if '^TNX' in macro_df.columns:
            us10y = float(macro_df['^TNX'].dropna().iloc[-1].item())
        else:
            us10y = 4.1
        if '^VIX' in macro_df.columns:
            vix = float(macro_df['^VIX'].dropna().iloc[-1].item())
        else:
            vix = 15.0
    except Exception as e:
        us10y = 4.1
        vix = 15.0
        
    print(f"Fetching Financial Matrix for the {len(tickers)} targeted assets...")
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(process_financials, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                results.append(res)
                
    df = pd.DataFrame(results)
    
    if df.empty:
        print("Failed to fetch matrix data.")
        return
        
    # The Physics Logic Ratings
    df['Score'] = 0
    df['Regime'] = "Unknown"
    df['Action'] = ""
    df['HF_Scalar'] = 0
    
    for idx, row in df.iterrows():
        tkr = row['Ticker']
        dem = row['Delta_Demand']
        sup = row['Delta_Supply']
        prc_pct = row['Delta_Pricing'] * 100 # Converting to percentage points to match '0.50' logic
        mar = row['Delta_Margin']
        rec_growth = row.get('Receivables_Growth', 0)
        ps = row.get('Price_to_Sales', 0)
        
        # CRISIS GATE CHECKS
        death_flag = None
        
        # Switch I (The Forensic Gate)
        if dem > 0 and prc_pct < -2.0:
            death_flag = "[DEATH: PROFITLESS GROWTH]"
        elif rec_growth > (dem + 0.10):
            death_flag = "[DEATH: CHANNEL STUFFING]"
            
        # Switch II (The Gravity Gate)
        elif ps > 20.0 and us10y > 4.0:
            death_flag = "[DEATH: VALUATION GRAVITY]"
            
        if death_flag:
            df.at[idx, 'Score'] = 0
            df.at[idx, 'Regime'] = death_flag
            df.at[idx, 'Action'] = "KILL"
            continue
            
        # 1. The Logic Patch (Ramp Exception)
        # If Pricing_GM_Delta > 0.50, Supply_Score = max(0, Supply_Score)
        adj_sup = max(0, sup) if prc_pct > 0.50 else sup
        
        # 2. The Scoring Update
        if dem > 0 and adj_sup >= 0 and prc_pct > 0 and mar > 0:
            df.at[idx, 'Score'] = 100
            df.at[idx, 'Regime'] = "Super Cycle (Q1)"
            
        elif dem > 0 and prc_pct < 0:
            df.at[idx, 'Score'] = 20
            df.at[idx, 'Regime'] = "Empty Calorie (Q3)"
            
        elif dem <= 0 and prc_pct <= 0 and mar <= 0:
            df.at[idx, 'Score'] = 0
            df.at[idx, 'Regime'] = "Value Trap (Q4)"
            
        elif adj_sup >= 0 and mar > 0:
            df.at[idx, 'Score'] = 90
            df.at[idx, 'Regime'] = "Turnaround (Q2)"
            
        else:
            df.at[idx, 'Score'] = 50 
            df.at[idx, 'Regime'] = "Transition"
            
        # Switch III (The Liquidity Gate)
        if vix > 35:
            df.at[idx, 'Score'] = int(df.at[idx, 'Score'] * 0.5)
            df.at[idx, 'Regime'] += " (Liquidity Haircut)"
            
        # 3. Running HF Afterburner (Only applies if alive)
        base_score = df.at[idx, 'Score']
        
        # Apply Individual Commodity Scalar
        custom_boost = get_commodity_scalar(tkr, manual_inputs)
        df.at[idx, 'HF_Scalar'] = custom_boost
        
        final_score = min(100, max(0, base_score + custom_boost))
        df.at[idx, 'Score'] = final_score
            
        # The Opportunity Gate Output
        score = df.at[idx, 'Score']
        if score >= 90:
            df.at[idx, 'Action'] = "BUY AGGRESSIVE"
        else:
            df.at[idx, 'Action'] = "IGNORE (Opportunity Cost)"
            
    # Sort the table by Score (Descending)
    df = df.sort_values(by='Score', ascending=False)
    
    print("\n--- The Final 'Opportunity Gate' Matrix ---")
    print(f"{'Ticker':<8} | {'Regime':<30} | {'Score':<6} | {'Action':<26} | {'Demand':<10} | {'Supply':<10} | {'Pricing':<10} | {'Margin':<10}")
    print("-" * 135)
    
    for index, row in df.iterrows():
        dem_str = f"{row['Delta_Demand']*100:+.2f}%"
        sup_str = f"{row['Delta_Supply']:+.3f}x"
        prc_str = f"{row['Delta_Pricing']*100:+.2f}%"
        mar_str = f"{row['Delta_Margin']*100:+.2f}%"
        
        print(f"{row['Ticker']:<8} | {row['Regime']:<30} | {row['Score']:<6} | {row['Action']:<26} | {dem_str:<10} | {sup_str:<10} | {prc_str:<10} | {mar_str:<10}")
        
    return df

if __name__ == '__main__':
    run_alpha_sovereign_scan()
