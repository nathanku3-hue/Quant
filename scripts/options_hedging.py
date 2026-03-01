import yfinance as yf
import pandas as pd
import datetime
import numpy as np

def calculate_optimal_hedge(ticker_symbol):
    print(f"--- Calculating Dynamic Hedge for {ticker_symbol} ---")
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Get Current Price
    hist = ticker.history(period="1mo")
    if hist.empty:
        return {"Action": "ERROR", "Reason": "No price data"}
        
    current_price = hist['Close'].iloc[-1]
    
    # Calculate a proxy for IV (30-day historical volatility annualized)
    returns = hist['Close'].pct_change().dropna()
    hist_vol = returns.std() * np.sqrt(252)
    
    # 2. Find closest expiration to 30 days
    exps = ticker.options
    if not exps:
        return {"Action": "ERROR", "Reason": "No options chain available"}
        
    target_date = datetime.datetime.now() + datetime.timedelta(days=30)
    
    best_exp = exps[0]
    min_diff = float('inf')
    for exp in exps:
        exp_date = datetime.datetime.strptime(exp, '%Y-%m-%d')
        diff = abs((exp_date - target_date).days)
        if diff < min_diff:
            min_diff = diff
            best_exp = exp
            
    days_to_exp = (datetime.datetime.strptime(best_exp, '%Y-%m-%d') - datetime.datetime.now()).days
    if days_to_exp <= 0:
        days_to_exp = 1 # Fallback to prevent division by zero if needed

    # 3. Get Options Chain for that expiration
    chain = ticker.option_chain(best_exp)
    calls = chain.calls
    
    if calls.empty:
        return {"Action": "ERROR", "Reason": "No call options available"}
        
    # Find ATM call to get baseline IV
    calls['strike_diff'] = abs(calls['strike'] - current_price)
    atm_call = calls.sort_values('strike_diff').iloc[0]
    atm_iv = atm_call['impliedVolatility']
    
    # Use ATM IV if reasonable, else historical vol
    iv_to_use = atm_iv if atm_iv > 0.01 else hist_vol
    iv_pct = iv_to_use * 100 # Convert to percentage (e.g., 50.0)
    
    # 4. Calculate Target Strike ($K$)
    # Logic: If IV is 50%, we sell a Call 5% out of the money. -> 50 / 10 = 5%.
    otm_pct = (iv_pct / 10.0) / 100.0
    target_strike_exact = current_price * (1 + otm_pct)
    
    # Find closest actual strike to the target_strike_exact
    calls['target_diff'] = abs(calls['strike'] - target_strike_exact)
    optimal_call = calls.sort_values('target_diff').iloc[0]
    
    optimal_strike = optimal_call['strike']
    premium = optimal_call['lastPrice'] 
    
    # Fallback to bid/ask mid if lastPrice is stale or 0
    if pd.isna(premium) or premium == 0:
        premium = (optimal_call['bid'] + optimal_call['ask']) / 2.0
        
    if premium == 0:
         return {"Action": "ERROR", "Reason": "Zero premium available"}
         
    # 5. The Yield Check
    # Premium Yield must be > 1.5% (Monthly)
    premium_yield = premium / current_price
    
    print(f"Current Price: ${current_price:.2f}")
    print(f"Implied Volatility: {iv_pct:.1f}%")
    print(f"Target Strike (Calculated): ${target_strike_exact:.2f}")
    print(f"Selected Option: {best_exp} ${optimal_strike} Call")
    print(f"Premium: ${premium:.2f} (Yield: {premium_yield*100:.2f}%)")
    
    if premium_yield < 0.015:
        return {
            "Action": "DO NOT SELL",
            "Ticker": ticker_symbol,
            "Strike": optimal_strike,
            "Exp": days_to_exp,
            "Est_Yield": premium_yield,
            "Reason": "Yield < 1.5%. Not worth capping the upside."
        }
        
    return {
        "Action": "SELL CALL",
        "Ticker": ticker_symbol,
        "Strike": optimal_strike,
        "Exp": days_to_exp,
        "Est_Yield": premium_yield
    }

if __name__ == "__main__":
    print("Initiating Priority 4: Dynamic Options Hedging\n")
    result = calculate_optimal_hedge("MU")
    print("\n--- HEDGE PAYLOAD ---")
    
    if result["Action"] == "ERROR":
        print(f"Error: {result['Reason']}")
    elif result["Action"] == "DO NOT SELL":
        print(f"Action: {result['Action']} | Ticker: {result['Ticker']} | Reason: {result['Reason']}")
    else:
        print(f"Action: {result['Action']} | Ticker: {result['Ticker']} | Strike: ${result['Strike']} | Exp: {result['Exp']} Days | Est. Yield: {result['Est_Yield']*100:.1f}%")
