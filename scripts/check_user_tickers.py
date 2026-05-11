import pandas as pd
import yfinance as yf
from scipy.signal import savgol_filter
import concurrent.futures
import warnings
import numpy as np

warnings.filterwarnings('ignore')

tickers = ['CEG', 'NBIS', 'CLS', 'MRVL', 'RBRK', 'ANET']

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
            
        rev_key = 'Total Revenue' if 'Total Revenue' in inc.index else 'Operating Revenue'
        if rev_key not in inc.index: return None
        rev = inc.loc[rev_key].dropna()
        if len(rev) < 2: return None
        
        demand_growth = (rev.iloc[0] / rev.iloc[1]) - 1
        
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
                delta_pricing = 0.0
        else:
            delta_pricing = 0.0

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
        
        return {
            'Ticker': t,
            'Delta_Demand': demand_growth,
            'Delta_Supply': delta_supply,
            'Delta_Pricing': delta_pricing,
            'Delta_Margin': delta_margin
        }
    except Exception as e:
        return None

def calculate_second_derivative(series, window=5):
    if len(series) < window:
        return np.zeros(len(series))
    try:
        d2 = savgol_filter(series, window, polyorder=3, deriv=2)
        return d2
    except:
        return np.zeros(len(series))

def analyze_current_phase(ticker):
    data = yf.download(ticker, period="3y", interval="1mo", progress=False)
    prices = data['Close'].dropna()
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0]
    
    if len(prices) < 12:
        return "Not enough data"
        
    price_d2 = calculate_second_derivative(prices, window=7)
    pseudo_margin = prices.pct_change(12).fillna(0)
    margin_d2 = calculate_second_derivative(pseudo_margin, window=7)
    
    divergence_signal = margin_d2 - price_d2
    
    current_p_d2 = price_d2[-1]
    current_m_d2 = margin_d2[-1]
    current_sig = divergence_signal[-1]
    
    if current_m_d2 < 0 and current_p_d2 > 0:
        return "Phase Reversal Approaching"
    elif current_m_d2 > 0 and current_p_d2 > 0:
        return "Main Ramping Wave"
    elif current_m_d2 > 0 and current_p_d2 < 0:
        return "Stealth Accumulation"
    else:
        return "Cyclical Trough"

def main():
    print("Fetching Financial Matrix...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_financials, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                results.append(res)
                
    df = pd.DataFrame(results)
    if not df.empty:
        df['Score'] = 0
        df['Regime'] = "Unknown"
        df['Action'] = ""
        df['Fourier_Phase'] = ""
        
        for idx, row in df.iterrows():
            dem = row['Delta_Demand']
            sup = row['Delta_Supply']
            prc_pct = row['Delta_Pricing'] * 100
            mar = row['Delta_Margin']
            
            adj_sup = max(0, sup) if prc_pct > 0.50 else sup
            
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
                
            score = df.at[idx, 'Score']
            if score >= 90:
                df.at[idx, 'Action'] = "BUY AGGRESSIVE"
            else:
                df.at[idx, 'Action'] = "IGNORE"
                
            df.at[idx, 'Fourier_Phase'] = analyze_current_phase(row['Ticker'])
            
        df = df.sort_values(by='Score', ascending=False)
        print("\n--- The Final 'Opportunity Gate' Matrix ---")
        print(f"{'Ticker':<8} | {'Regime':<20} | {'Score':<6} | {'Fourier Phase':<28} | {'Demand':<10} | {'Pricing':<10} | {'Margin':<10}")
        print("-" * 115)
        for index, row in df.iterrows():
            dem_str = f"{row['Delta_Demand']*100:+.2f}%"
            prc_str = f"{row['Delta_Pricing']*100:+.2f}%"
            mar_str = f"{row['Delta_Margin']*100:+.2f}%"
            print(f"{row['Ticker']:<8} | {row['Regime']:<20} | {row['Score']:<6} | {row['Fourier_Phase']:<28} | {dem_str:<10} | {prc_str:<10} | {mar_str:<10}")

if __name__ == '__main__':
    main()
