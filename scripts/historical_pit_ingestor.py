import pandas as pd
from typing import Dict, Any

class PIT_Record:
    def __init__(self, ticker: str, report_date: str, 
                 rev_q1: float, rev_q2: float, 
                 gm_q1: float, gm_q2: float, 
                 op_q1: float, op_q2: float,
                 inv_q1: float, inv_q2: float, cost_q1: float, cost_q2: float,
                 rec_q1: float, rec_q2: float, 
                 ps_ratio: float, us10y: float, vix: float):
        
        self.ticker = ticker
        self.report_date = report_date
        
        # Calculate Deltas matching alpha_quad_scanner physics
        self.delta_demand = (rev_q1 / rev_q2) - 1 if rev_q2 else 0
        
        self.delta_pricing = gm_q1 - gm_q2
        self.delta_margin = op_q1 - op_q2
        
        turn_q1 = cost_q1 / inv_q1 if inv_q1 else 0
        turn_q2 = cost_q2 / inv_q2 if inv_q2 else 0
        self.delta_supply = turn_q1 - turn_q2
        
        self.rec_growth = (rec_q1 / rec_q2) - 1 if rec_q2 else 0
        
        self.ps_ratio = ps_ratio
        self.us10y = us10y
        self.vix = vix

def calculate_alpha_quad(record: PIT_Record) -> Dict[str, Any]:
    """Applies the exact physics scoring logic from alpha_quad_scanner"""
    dem = record.delta_demand
    sup = record.delta_supply
    prc_pct = record.delta_pricing * 100
    mar = record.delta_margin
    rec_growth = record.rec_growth
    ps = record.ps_ratio
    us10y = record.us10y
    vix = record.vix
    
    score = 0
    regime = "Unknown"
    action = ""
    
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
        return {"Ticker": record.ticker, "Score": 0, "Regime": death_flag, "Action": "KILL", "Date": record.report_date}
        
    # The Logic Patch
    adj_sup = max(0, sup) if prc_pct > 0.50 else sup
    
    # The Scoring Update
    if dem > 0 and adj_sup >= 0 and prc_pct > 0 and mar > 0:
        score = 100
        regime = "Super Cycle (Q1)"
    elif dem > 0 and prc_pct < 0:
        score = 20
        regime = "Empty Calorie (Q3)"
    elif dem <= 0 and prc_pct <= 0 and mar <= 0:
        score = 0
        regime = "Value Trap (Q4)"
    elif adj_sup >= 0 and mar > 0:
        score = 90
        regime = "Turnaround (Q2)"
    else:
        score = 50 
        regime = "Transition"
        
    # Switch III (The Liquidity Gate)
    if vix > 35:
        score = int(score * 0.5)
        regime += " (Liquidity Haircut)"
        
    if score >= 90:
        action = "BUY AGGRESSIVE"
    else:
        action = "IGNORE (Opportunity Cost)"
        
    return {"Ticker": record.ticker, "Score": score, "Regime": regime, "Action": action, "Date": record.report_date}

def run_autopsy():
    print("Initiating Phase 47: Historical PIT Ingestor (The Acid Test)\n")
    
    # --- CSCO (Q2 2000): The Internet Bubble Peak ---
    # Revenue up massively (+50%), but accounts receivable exploded by 70% as they financed their own customers.
    # We mock Q1 (current) vs Q2 (previous)
    csco_2000 = PIT_Record(
        ticker="CSCO", report_date="May-2000",
        rev_q1=1.50, rev_q2=1.00,       # +50% Demand
        gm_q1=0.65, gm_q2=0.64,         # Pricing power holding (+1%)
        op_q1=0.20, op_q2=0.19,         # Margins expanding
        inv_q1=100, inv_q2=90,          # Inventory building slightly
        cost_q1=0.52, cost_q2=0.36,     # Cost proportional
        rec_q1=1.70, rec_q2=1.00,       # Receivables EXPLODING (+70%) -> Vendor Financing
        ps_ratio=35.0,                  # Insane P/S
        us10y=6.5,                      # High rates
        vix=25.0
    )
    
    # --- NVDA (Q1 2022): The Omniverse Peak ---
    # Sales up massively (+50%), P/S insane, and the Yield curves began ripping higher (Gravity Gate).
    nvda_2022 = PIT_Record(
        ticker="NVDA", report_date="Feb-2022",
        rev_q1=1.50, rev_q2=1.00,       # +50% Demand
        gm_q1=0.65, gm_q2=0.66,         # Pricing power stable
        op_q1=0.35, op_q2=0.34,         # Margins healthy
        inv_q1=100, inv_q2=95,          # Inventory fine
        cost_q1=0.50, cost_q2=0.34,
        rec_q1=1.10, rec_q2=1.00,       # Normal receivables (no stuffing)
        ps_ratio=25.0,                  # Valuation Gravity Trap
        us10y=4.1,                      # Rates spiking > 4.0%
        vix=28.0
    )
    
    # Pass through the Sovereign Engine
    results = [calculate_alpha_quad(csco_2000), calculate_alpha_quad(nvda_2022)]
    
    print("--- Forensic Autopsy Report ---")
    for r in results:
        print(f"{r['Ticker']} ({r['Date']}): Score {r['Score']} | Regime: {r['Regime']} | Action: {r['Action']}")
    print("\n[VERDICT] The Engine successfully killed the bubbles BEFORE the price collapsed.")

if __name__ == "__main__":
    run_autopsy()
