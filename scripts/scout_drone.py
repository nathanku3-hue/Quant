import os
import sys
import json
import logging
import datetime
import requests
import pandas as pd
import yfinance as yf
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [DRONE] - %(message)s')

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.getcwd())

from scripts.alpha_quad_scanner import process_financials
from scripts.high_freq_data import get_commodity_scalar

DATA_DIR = "data"
FRESH_FINDS_FILE = os.path.join(DATA_DIR, "fresh_finds.json")

def get_universe():
    logging.info("Generating Search Universe (Mid-Cap / Large-Cap Proxy)...")
    # Using Wikipedia's S&P 500 and S&P 400 MidCap lists as a high-liquidity, > $2B market cap proxy
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        sp500_html = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies', headers=headers).text
        sp400_html = requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_400_companies', headers=headers).text
        
        sp500 = pd.read_html(sp500_html)[0]
        sp400 = pd.read_html(sp400_html)[0]
        
        # Filter for our preferred sectors (Tech, Industrials, Energy) roughly based on GICS
        target_sectors = ['Information Technology', 'Industrials', 'Energy', 'Communication Services']
        
        sp500_filtered = sp500[sp500['GICS Sector'].isin(target_sectors)]['Symbol'].tolist()
        sp400_filtered = sp400[sp400['GICS Sector'].isin(target_sectors)]['Symbol'].tolist()
        
        raw_tickers = list(set(sp500_filtered + sp400_filtered))
        # Clean tickers
        tickers = [t.replace('.', '-') for t in raw_tickers]
        logging.info(f"Target Universe locked: {len(tickers)} assets.")
        return tickers
    except Exception as e:
        logging.error(f"Failed to fetch universe: {e}")
        return []

def filter_technicals(tickers):
    logging.info("Initiating Technical Fast-Filter Line (Price > MA50)...")
    survivors = []
    
    # Batch grab 3mo data to calculate MA50 quickly using thread pools or yfinance bulk
    try:
        # In chunks of 100 to prevent API throttling
        chunk_size = 100
        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i:min(i + chunk_size, len(tickers))]
            data = yf.download(chunk, period="3mo", progress=False)['Close']
            
            for t in chunk:
                try:
                    if isinstance(data, pd.Series):
                        hist = data.dropna()
                    else:
                        hist = data[t].dropna() if t in data.columns else pd.Series()
                        
                    if len(hist) >= 50:
                        ma50 = hist.rolling(50).mean().iloc[-1]
                        current = hist.iloc[-1]
                        if current > ma50:
                            survivors.append(t)
                except Exception:
                    pass
    except Exception as e:
        logging.error(f"Technical filter failed: {e}")
        
    logging.info(f"Technical Filter Complete. {len(survivors)} assets remain in Super Trend.")
    return survivors

def run_physics_engine(tickers):
    logging.info(f"Igniting Heavy Physics Engine for {len(tickers)} assets...")
    
    # We only care if Score >= 90
    gems = []
    
    # Fetch Macro
    try:
        macro_df = yf.download("^TNX", period="5d", progress=False)['Close']
        us10y = float(macro_df['^TNX'].dropna().iloc[-1].item()) if '^TNX' in macro_df.columns else 4.1
    except:
        us10y = 4.1

    def evaluate_target(t):
        res = process_financials(t)
        if not res: return None
        
        dem = res['Delta_Demand']
        sup = res['Delta_Supply']
        prc_pct = res['Delta_Pricing'] * 100
        mar = res['Delta_Margin']
        rec_growth = res.get('Receivables_Growth', 0)
        ps = res.get('Price_to_Sales', 0)
        
        # Gates
        if dem > 0 and prc_pct < -2.0: return None
        if rec_growth > (dem + 0.10): return None
        if ps > 20.0 and us10y > 4.0: return None
        
        adj_sup = max(0, sup) if prc_pct > 0.50 else sup
        
        score = 50
        if dem > 0 and adj_sup >= 0 and prc_pct > 0 and mar > 0:
            score = 100
        elif dem <= 0 and prc_pct <= 0 and mar <= 0:
            score = 0
        elif dem > 0 and prc_pct < 0:
            score = 20
        elif adj_sup >= 0 and mar > 0:
            score = 90
            
        if score >= 90:
            return {
                "Ticker": t,
                "Score": score,
                "Delta_Demand": dem,
                "Delta_Supply": sup,
                "Delta_Margin": mar
            }
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(evaluate_target, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res is not None:
                gems.append(res)
                logging.info(f"GEM DETECTED: {res['Ticker']} (Score: {res['Score']})")
                
    return gems

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    targets = get_universe()
    if not targets:
        return
        
    tech_survivors = filter_technicals(targets)
    if not tech_survivors:
        logging.info("No targets survived the technical filter.")
        return
        
    gems = run_physics_engine(tech_survivors)
    
    # Load existing finds to avoid overwriting unless needed, or just overwrite with fresh list.
    # We will overwrite so the dashboard only sees active finds.
    output = {
        "timestamp": datetime.datetime.now().isoformat(),
        "count": len(gems),
        "assets": gems
    }
    
    with open(FRESH_FINDS_FILE, "w") as f:
        json.dump(output, f, indent=4)
        
    logging.info(f"Drone Mission Complete. {len(gems)} targets extracted and written to JSON.")

if __name__ == "__main__":
    main()
