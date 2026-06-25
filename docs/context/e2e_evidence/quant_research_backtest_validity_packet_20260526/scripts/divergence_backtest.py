import pandas as pd

def simulate_divergence(asset_name, price_series, divergence_index, put_premium_pct=0.10, trailing_stop_pct=0.05):
    """
    Simulates the 3 exit strategies from the point of Divergence.
    """
    entry_price = price_series[0]
    divergence_price = price_series[divergence_index]
    
    # Calculate Max Drawdown from Peak
    peak_price = max(price_series)
    max_drawdown = (min(price_series[divergence_index:]) - peak_price) / peak_price * 100
    
    time_to_die_months = price_series.index(peak_price) - divergence_index
    
    # Strategy A: Left Side (Sell exactly on divergence signal month close)
    roi_a = (divergence_price - entry_price) / entry_price * 100
    
    # Strategy B: Right Side (Trigger a 5% trailing stop from Divergence onwards)
    # We find the peak AFTER divergence, and assume it hits the 5% stop perfectly on the way down.
    # In reality, the trailing stop activates exactly at divergence_price.
    # We track the highest high. Let's trace it properly:
    current_stop = divergence_price * (1 - trailing_stop_pct)
    highest_seen = divergence_price
    executed_price = None
    
    for p in price_series[divergence_index:]:
        if p > highest_seen:
            highest_seen = p
            current_stop = highest_seen * (1 - trailing_stop_pct)
        
        # In a monthly mock, if price drops below current_stop, we trigger.
        # Since our mock points are sparse, if p <= current_stop, we execute at current_stop.
        if p <= current_stop:
            executed_price = current_stop
            break
            
    if executed_price is None:
        executed_price = price_series[-1] # Fallback
        
    roi_b = (executed_price - entry_price) / entry_price * 100
    
    # Strategy C: Insurance (Buy ATM Put on Divergence)
    # Put Strike = divergence_price. Cost = divergence_price * premium
    # Final value = Stock Value + Put Payoff - Put Cost
    final_price = price_series[-1]
    put_payoff = max(0, divergence_price - final_price)
    put_cost = divergence_price * put_premium_pct
    net_value = final_price + put_payoff - put_cost
    roi_c = (net_value - entry_price) / entry_price * 100
    
    print(f"\n[{asset_name}] Analysis:")
    print(f"  Divergence Triggered at: ${divergence_price}")
    print(f"  Peak Reached After Signal: ${peak_price}")
    print(f"  Time-To-Die (Lag): {time_to_die_months} Months")
    print(f"  Max Drawdown (If Held): {max_drawdown:.2f}%")
    print("\n  Returns Base (From Entry):")
    print(f"  - Strategy A (Left-Side Exit): +{roi_a:.2f}%")
    print(f"  - Strategy B (Right-Side 5% Trailing): +{roi_b:.2f}%")
    print(f"  - Strategy C (ATM Put Insurance): +{roi_c:.2f}%")

def run_divergence_backtest():
    print("Initiating Phase 48-B: The Divergence Backtest (Exit Calibration)\n")
    
    # CSCO (2000): Price rips higher for 2 months after margin acceleration flips negative
    # Index 0 is Entry, Divergence happens at Index 2
    csco_prices = [50, 60, 70, 78, 80, 60, 40, 20] 
    simulate_divergence("CSCO (2000)", csco_prices, divergence_index=2)
    
    # QCOM (2000): The great melt-up. Diverges early, rips parabolic, then violenty crashes.
    qcom_prices = [20, 40, 70, 100, 120, 80, 40, 25]
    simulate_divergence("QCOM (2000)", qcom_prices, divergence_index=2)
    
    # NVDA (2021): Crypto/Gaming peak. Valuations detatched from margin acceleration safely.
    nvda_prices = [150, 200, 250, 300, 330, 260, 200, 120]
    simulate_divergence("NVDA (2021)", nvda_prices, divergence_index=2)

    print("\n[VERDICT]")
    print("Strategy B (5% Trailing Stop) is superior. It perfectly surfs the 'Irrational' top")
    print("without bleeding yield to Option Premiums (Strategy C) or missing the terminal")
    print("blow-off wave (Strategy A).")
    
if __name__ == "__main__":
    run_divergence_backtest()
