import yfinance as yf
import pandas as pd
import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from filelock import FileLock
import warnings
warnings.filterwarnings("ignore")

CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "backtest_results.json"
LOCK_PATH = str(CACHE_PATH) + ".lock"


def calc_mdd(eq):
    peak = eq.cummax()
    return float(((eq - peak) / peak).min())


def calc_cagr(eq):
    n_years = len(eq) / 252
    if n_years <= 0 or eq.iloc[0] <= 0 or eq.iloc[-1] <= 0:
        return 0.0
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / n_years) - 1)


def calc_sharpe(returns, rf=0.0):
    excess = returns - rf / 252
    if excess.std() == 0:
        return 0.0
    return float((excess.mean() / excess.std()) * np.sqrt(252))


def write_cache(strategy_name, result):
    lock = FileLock(LOCK_PATH, timeout=10)
    with lock:
        data = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
        data[strategy_name] = result
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CACHE_PATH)


def run_backtest():
    print("=== Phase 64: Derivative Engine Backtest (The Physics of LEAPs) ===")

    decades = {
        "1990-2000 (Dot-Com)": ("1990-01-01", "2000-12-31", ["MSFT", "CSCO"]),
        "2000-2010 (Lost Decade)": ("2000-01-01", "2010-12-31", ["AAPL", "AMZN"]),
        "2010-2020 (Quantitative Easing)": ("2010-01-01", "2020-12-31", ["NVDA", "TSLA"])
    }

    LEAP_LEVERAGE = 2.5
    all_strat_eq = []
    all_strat_ret = []

    for era, (start_dt, end_dt, tickers) in decades.items():
        print(f"\n--- {era} ERA ---")
        
        try:
            df_raw = yf.download(tickers, start=start_dt, end=end_dt, progress=False)['Close']
            if df_raw.empty: 
                continue
            
            for t in tickers:
                df = pd.DataFrame()
                if isinstance(df_raw, pd.DataFrame):
                    if t not in df_raw.columns: continue
                    df['Close'] = df_raw[t].dropna()
                else:
                    if t != tickers[0]: continue
                    df['Close'] = df_raw.dropna()
                    
                if len(df) < 100: continue
                
                df['Ret'] = df['Close'].pct_change()
                df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                
                slope = df['EMA10'].diff()
                avg_slope = slope.rolling(window=20).mean()
                
                df['Prev_Close'] = df['Close'].shift(1)
                df['Prev_Slope'] = slope.shift(1)
                df['Prev_Avg_Slope'] = avg_slope.shift(1)
                
                df_trade = df.loc[start_dt:].dropna().copy()
                if df_trade.empty: continue
                
                pos_mult = []
                
                for idx, row in df_trade.iterrows():
                    p_slope = row['Prev_Slope']
                    p_avg_slope = row['Prev_Avg_Slope']
                    
                    if pd.isna(p_avg_slope) or p_avg_slope <= 0:
                        convexity = 1.0
                    else:
                        convexity = p_slope / p_avg_slope
                        
                    if convexity > 1.5:
                        geo_mult = 1.0
                    else:
                        geo_mult = LEAP_LEVERAGE
                        
                    pos_mult.append(geo_mult)
                    
                df_trade['Leverage'] = pos_mult
                
                theta_decay = 0.10 / 252
                
                df_trade['Strat_Ret'] = (df_trade['Leverage'] * df_trade['Ret']) - (theta_decay * (df_trade['Leverage'] > 1))
                
                bh_eq = (1 + df_trade['Ret']).cumprod()
                strat_eq = (1 + df_trade['Strat_Ret']).cumprod()
                
                bh_ret = (bh_eq.iloc[-1] - 1) * 100
                strat_ret = (strat_eq.iloc[-1] - 1) * 100
                
                bh_mdd = calc_mdd(bh_eq)
                strat_mdd = calc_mdd(strat_eq)

                all_strat_eq.append(strat_eq)
                all_strat_ret.append(df_trade['Strat_Ret'].fillna(0))
                
                print(f"[{t}] Stock B&H: {bh_ret:>8.1f}% (MDD: {bh_mdd*100:>6.1f}%) | Geo-Derivative Strat: {strat_ret:>8.1f}% (MDD: {strat_mdd*100:>6.1f}%) | Alpha: {strat_ret - bh_ret:>+8.1f}%")
                
        except Exception as e:
            print(f"Error for {era}: {e}")

    # Aggregate
    if all_strat_eq:
        avg_eq = pd.concat(all_strat_eq, axis=1).mean(axis=1)
        combined_ret = pd.concat(all_strat_ret, axis=1).mean(axis=1)
        return {
            "cagr": round(calc_cagr(avg_eq), 6),
            "max_dd": round(calc_mdd(avg_eq), 6),
            "sharpe": round(calc_sharpe(combined_ret), 4),
            "timestamp": datetime.now().isoformat(),
            "script": "derivative_backtest.py",
        }
    return {"cagr": 0.0, "max_dd": 0.0, "sharpe": 0.0, "timestamp": datetime.now().isoformat(), "script": "derivative_backtest.py"}


if __name__ == "__main__":
    result = run_backtest()
    print(f"\n=== AGGREGATE: CAGR={result['cagr']*100:.1f}% | MDD={result['max_dd']*100:.1f}% | Sharpe={result['sharpe']:.2f} ===")

    if "--json" in sys.argv:
        write_cache("The Derivatives Trinity", result)
        print(f"Results written to {CACHE_PATH}")

