import yfinance as yf
import pandas as pd

try:
    hist = yf.download('MSFT', period='3mo', progress=False)['Close']
    if hasattr(hist, 'iloc'):
        hist = hist.squeeze()
        
    volatility_3m = hist.pct_change().std().item() * (252 ** 0.5)
    current = hist.iloc[-1].item()
    
    if volatility_3m > 0.40:
        support_price = hist.ewm(span=10, adjust=False).mean().iloc[-1].item()
        label = "10-Day EMA (Hyper)"
    elif volatility_3m > 0.25:
        support_price = hist.ewm(span=21, adjust=False).mean().iloc[-1].item()
        label = "21-Day EMA (Fast)"
    else:
        support_price = hist.rolling(window=50, min_periods=10).mean().iloc[-1].item()
        label = "50-Day SMA (Base)"
        
    print(f"MSFT Current Price: ${current:.2f}")
    print(f"MSFT 3-Month Volatility: {volatility_3m*100:.2f}%")
    print(f"Selected Support Band: {label}")
    print(f"Evaluated Support Price (Entry Price): ${support_price:.2f}")

except Exception as e:
    print("Error:", e)
