import pandas as pd
import yfinance as yf
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from filelock import FileLock
import warnings

warnings.filterwarnings('ignore')

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "backtest_results.json"
LOCK_PATH = str(CACHE_PATH) + ".lock"


def calc_mdd(returns_series):
    eq = (1 + returns_series).cumprod()
    peak = eq.cummax()
    dd = (eq - peak) / peak
    return float(dd.min())


def calc_cagr(returns_series):
    eq = (1 + returns_series).cumprod()
    n_years = len(eq) / 252
    if n_years <= 0 or eq.iloc[-1] <= 0:
        return 0.0
    return float(eq.iloc[-1] ** (1 / n_years) - 1)


def write_cache(strategy_name, result):
    lock = FileLock(LOCK_PATH, timeout=10)
    with lock:
        data = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
        data[strategy_name] = result
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CACHE_PATH)

def get_support_resistance(prices, window=20):
    support = prices.rolling(window).min()
    resistance = prices.rolling(window).max()
    return support, resistance

def run_backtest(df, lane, impatient=False):
    in_pos = False
    entry_price = 0
    highest_price = 0
    trades = []
    daily_returns = []
    
    for i in range(len(df)):
        # Skip NaNs to make sure we have valid indicators
        if pd.isna(df['Support'].iloc[i]) or pd.isna(df['Resistance'].iloc[i]):
            daily_returns.append(0.0)
            continue
            
        price = df['Close'].iloc[i]
        support = df['Support'].iloc[i]
        resistance = df['Resistance'].iloc[i]
        ma20 = df['MA20'].iloc[i]
        
        # Calculate daily return if in position
        if in_pos:
            ret = (price - df['Close'].iloc[i-1]) / df['Close'].iloc[i-1]
            daily_returns.append(ret)
            if price > highest_price:
                highest_price = price
        else:
            daily_returns.append(0.0)
            
        # Trading Logic
        if not in_pos:
            enter = False
            if impatient:
                # "Buy immediately when signal says Long"
                # For this test, Fundamental Signal is assumed uniformly "Long" during the test period.
                enter = True
            else:
                if lane == 'A':
                    # Lane A (Left Side): Wait for dip to support
                    if price <= support * 1.02:
                        enter = True
                elif lane == 'B':
                    # Lane B (Right Side): Wait for momentum confirmation
                    if price > support and price > ma20:
                        enter = True
            
            if enter:
                in_pos = True
                entry_price = price
                highest_price = price
        else:
            exit_trade = False
            if lane == 'A':
                # Exit at Resistance
                if price >= resistance:
                    exit_trade = True
            elif lane == 'B':
                # Trailing Stop (5%)
                if price <= highest_price * 0.95:
                    exit_trade = True
                    
            if exit_trade:
                in_pos = False
                profit = (price - entry_price) / entry_price
                trades.append({
                    'entry_price': entry_price,
                    'profit': profit,
                    'win': profit > 0
                })
                
    win_rate = sum([1 for t in trades if t['win']]) / len(trades) if trades else 0.0
    avg_entry = sum([t['entry_price'] for t in trades]) / len(trades) if trades else 0.0
    
    returns_series = pd.Series(daily_returns)
    sharpe = (returns_series.mean() / returns_series.std()) * np.sqrt(252) if returns_series.std() > 0 else 0.0
    cagr = calc_cagr(returns_series)
    mdd = calc_mdd(returns_series)
    
    return {
        'Count': len(trades),
        'WinRate': win_rate,
        'AvgEntry': avg_entry,
        'Sharpe': sharpe,
        'CAGR': cagr,
        'MDD': mdd,
        'AvgMarketPrice': df['Close'].mean()
    }

def main():
    print("Downloading Market Data...")
    # 1. Download data
    mu_df = yf.download("MU", start="2020-01-01", end="2024-12-31", progress=False)
    cifr_df = yf.download("CIFR", start="2023-01-01", end="2024-12-31", progress=False)

    # Handle multi-index columns from yfinance
    if isinstance(mu_df.columns, pd.MultiIndex):
        mu = pd.DataFrame({'Close': mu_df['Close']['MU']})
    else:
        mu = pd.DataFrame({'Close': mu_df['Close']})
        
    if isinstance(cifr_df.columns, pd.MultiIndex):
        cifr = pd.DataFrame({'Close': cifr_df['Close']['CIFR']})
    else:
        cifr = pd.DataFrame({'Close': cifr_df['Close']})
        
    # 2. Add indicators (shift(1) to prevent lookahead)
    sup, res = get_support_resistance(mu['Close'])
    mu['Support'] = sup.shift(1)
    mu['Resistance'] = res.shift(1)
    mu['MA20'] = mu['Close'].rolling(20).mean().shift(1)
    
    sup, res = get_support_resistance(cifr['Close'])
    cifr['Support'] = sup.shift(1)
    cifr['Resistance'] = res.shift(1)
    cifr['MA20'] = cifr['Close'].rolling(20).mean().shift(1)
    
    # 3. Run Comparisons
    print("\n--- Lane A: Micron (MU) Type A Compounder [2020-2024] ---")
    mu_imp = run_backtest(mu, lane='A', impatient=True)
    mu_pat = run_backtest(mu, lane='A', impatient=False)
    
    print(f"{'Metric':<20} | {'Strategy 1 (Impatient)':<25} | {'Strategy 2 (Patience)':<25}")
    print("-" * 76)
    print(f"{'Sharpe Ratio':<20} | {mu_imp['Sharpe']:<25.2f} | {mu_pat['Sharpe']:<25.2f}")
    print(f"{'Win Rate':<20} | {mu_imp['WinRate']*100:<24.1f}% | {mu_pat['WinRate']*100:<24.1f}%")
    print(f"{'Avg Entry Price':<20} | ${mu_imp['AvgEntry']:<24.2f} | ${mu_pat['AvgEntry']:<24.2f}")
    print(f"{'Avg Market Price':<20} | ${mu_imp['AvgMarketPrice']:<24.2f} | ${mu_pat['AvgMarketPrice']:<24.2f}")
    print(f"{'Trades Executed':<20} | {mu_imp['Count']:<25} | {mu_pat['Count']:<25}")


    print("\n--- Lane B: Cipher (CIFR) Type B High Beta [2023-2024] ---")
    cifr_imp = run_backtest(cifr, lane='B', impatient=True)
    cifr_pat = run_backtest(cifr, lane='B', impatient=False)
    
    print(f"{'Metric':<20} | {'Strategy 1 (Impatient)':<25} | {'Strategy 2 (Patience)':<25}")
    print("-" * 76)
    print(f"{'Sharpe Ratio':<20} | {cifr_imp['Sharpe']:<25.2f} | {cifr_pat['Sharpe']:<25.2f}")
    print(f"{'Win Rate':<20} | {cifr_imp['WinRate']*100:<24.1f}% | {cifr_pat['WinRate']*100:<24.1f}%")
    print(f"{'Avg Entry Price':<20} | ${cifr_imp['AvgEntry']:<24.2f} | ${cifr_pat['AvgEntry']:<24.2f}")
    print(f"{'Avg Market Price':<20} | ${cifr_imp['AvgMarketPrice']:<24.2f} | ${cifr_pat['AvgMarketPrice']:<24.2f}")
    print(f"{'Trades Executed':<20} | {cifr_imp['Count']:<25} | {cifr_pat['Count']:<25}")

if __name__ == '__main__':
    main()

    if "--json" in sys.argv:
        # Run a representative backtest and cache results
        mu_df = yf.download("MU", start="2020-01-01", end="2024-12-31", progress=False)
        if isinstance(mu_df.columns, pd.MultiIndex):
            mu = pd.DataFrame({'Close': mu_df['Close']['MU']})
        else:
            mu = pd.DataFrame({'Close': mu_df['Close']})
        sup = mu['Close'].rolling(20).min().shift(1)
        res = mu['Close'].rolling(20).max().shift(1)
        mu['Support'] = sup
        mu['Resistance'] = res
        mu['MA20'] = mu['Close'].rolling(20).mean().shift(1)
        result = run_backtest(mu, lane='A', impatient=False)
        final = {
            "cagr": round(result['CAGR'], 6),
            "max_dd": round(result['MDD'], 6),
            "sharpe": round(result['Sharpe'], 4),
            "timestamp": datetime.now().isoformat(),
            "script": "smart_entry_backtest.py",
        }
        write_cache("Empirical Stink Bid", final)
        print(f"Results written to {CACHE_PATH}")
