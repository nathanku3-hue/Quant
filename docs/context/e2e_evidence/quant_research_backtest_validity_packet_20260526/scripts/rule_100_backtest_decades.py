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
    """Maximum Drawdown from equity curve."""
    peak = eq.cummax()
    dd = (eq - peak) / peak
    return float(dd.min())


def calc_cagr(eq):
    """Annualized CAGR from equity curve."""
    n_years = len(eq) / 252
    if n_years <= 0 or eq.iloc[0] <= 0 or eq.iloc[-1] <= 0:
        return 0.0
    return float((eq.iloc[-1] / eq.iloc[0]) ** (1 / n_years) - 1)


def calc_sharpe(returns, rf=0.0):
    """Annualized Sharpe ratio."""
    excess = returns - rf / 252
    if excess.std() == 0:
        return 0.0
    return float((excess.mean() / excess.std()) * np.sqrt(252))


def write_cache(strategy_name, result):
    """Atomic write to shared backtest_results.json with filelock."""
    lock = FileLock(LOCK_PATH, timeout=10)
    with lock:
        data = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
        data[strategy_name] = result
        tmp = CACHE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CACHE_PATH)


def backtest_decade(era_name, start_dt, end_dt, super_cycle_tickers, tractor_tickers, trade_start):
    print(f"\n=== Phase 62-G/H: Infinity Governor Backtest ({era_name}) ===")
    
    all_tickers = super_cycle_tickers + tractor_tickers
    
    df_raw = yf.download(all_tickers, start=start_dt, end=end_dt, progress=False)['Close']
    df_high = yf.download(all_tickers, start=start_dt, end=end_dt, progress=False)['High']
    df_low = yf.download(all_tickers, start=start_dt, end=end_dt, progress=False)['Low']
    
    total_bh_alpha_super = []
    total_bh_alpha_tractor = []
    all_strat_eq = []
    all_strat_ret = []
    
    for t in all_tickers:
        df = pd.DataFrame()
        if isinstance(df_raw, pd.DataFrame):
            if t not in df_raw.columns:
                print(f"Skipping {t} - no data")
                continue
            df['Close'] = df_raw[t].dropna()
            df['High'] = df_high[t].dropna()
            df['Low'] = df_low[t].dropna()
        else:
            if t != all_tickers[0]: continue
            df['Close'] = df_raw.dropna()
            df['High'] = df_high.dropna()
            df['Low'] = df_low.dropna()
            
        if len(df) < 252:
            print(f"Skipping {t} - insufficient data")
            continue
            
        # ATR Calculation
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift(1)).abs()
        low_close = (df['Low'] - df['Close'].shift(1)).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.ewm(alpha=1/14, adjust=False).mean()
        
        # Determine Kinetic Cluster limits to assign baseline limit
        atr_ratio = (df['ATR'] / df['Close']).tail(252).median()
        if pd.isna(atr_ratio): atr_ratio = 0.03
        if atr_ratio < 0.025:
            limit = 8.2
        elif atr_ratio <= 0.045:
            limit = 8.8
        else:
            limit = 12.3
            
        # Strategy Preparation
        df['Ret'] = df['Close'].pct_change()
        df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
        df['Stretch'] = ((df['Close'] - df['EMA21']) / df['EMA21']) * 100
        
        # Velocity and Convexity
        slope = df['EMA10'].diff()
        avg_slope = slope.rolling(window=20).mean()
        
        df['Prev_Close'] = df['Close'].shift(1)
        df['Prev_EMA21'] = df['EMA21'].shift(1)
        df['Prev_Stretch'] = df['Stretch'].shift(1)
        df['Prev_ATR'] = df['ATR'].shift(1)
        df['Prev_Slope'] = slope.shift(1)
        df['Prev_Avg_Slope'] = avg_slope.shift(1)
        
        # Simple Rolling R^2 (Stability) Proxy for 60 days
        def get_r2(series):
            if len(series) < 60: return 0
            y = series.values
            x = np.arange(len(y))
            slope, intercept = np.polyfit(x, y, 1)
            y_pred = slope * x + intercept
            ss_res = np.sum((y - y_pred)**2)
            ss_tot = np.sum((y - np.mean(y))**2)
            if ss_tot == 0: return 0
            return 1 - (ss_res / ss_tot)
            
        r2_series = df['Close'].rolling(window=60).apply(get_r2, raw=False)
        df['Prev_R2'] = r2_series.shift(1)
        
        df_trade = df.loc[trade_start:].copy()
        if df_trade.empty: continue
        
        pos = []
        curr = 1.0 # start invested
        active_stop = 0.0
        
        # Simulating Infinity Governor
        for idx, row in df_trade.iterrows():
            if pd.isna(row['Prev_Stretch']) or pd.isna(row['Prev_Close']):
                pos.append(curr)
                continue
                
            if curr == 0.0 and row['Prev_Close'] <= row['Prev_EMA21']:
                curr = 1.0
                active_stop = 0.0
                
            pos.append(curr)
            
            if curr == 1.0:
                p_slope = row['Prev_Slope']
                p_avg_slope = row['Prev_Avg_Slope']
                r2 = row['Prev_R2']
                
                # Convexity Calculation
                if pd.isna(p_slope) or pd.isna(p_avg_slope) or pd.isna(r2):
                    convexity = 1.0
                    r2 = 0.0
                elif p_avg_slope <= 0:
                    convexity = 1.0
                else:
                    convexity = p_slope / p_avg_slope
                    
                # The Infinity Governor Formula
                stability_bonus = max(0, r2 - 0.90) * 10
                convexity_penalty = max(0, convexity - 1.5)
                
                is_stretched = row['Prev_Stretch'] >= limit
                
                if is_stretched:
                    multiplier = 3.0 * (1.0 + stability_bonus) * (1.0 / (1.0 + convexity_penalty))
                    multiplier = max(1.5, min(9.0, multiplier))
                else:
                    multiplier = 3.0
                    
                day_stop = row['Prev_Close'] - (multiplier * row['Prev_ATR'])
                if day_stop > active_stop:
                    active_stop = day_stop
                    
                if row['Close'] < active_stop:
                    curr = 0.0
                    active_stop = 0.0
                    
        df_trade['Pos'] = pos
        df_trade['Strat_Ret'] = df_trade['Pos'] * df_trade['Ret']
        
        bh_eq = (1 + df_trade['Ret'].fillna(0)).cumprod()
        strat_eq = (1 + df_trade['Strat_Ret'].fillna(0)).cumprod()
        
        bh_ret = (bh_eq.iloc[-1] - 1) * 100
        strat_ret_pct = (strat_eq.iloc[-1] - 1) * 100
        alpha = strat_ret_pct - bh_ret
        
        cat = "RULE OF 100 SUPERCYCLE" if t in super_cycle_tickers else "TRACTOR (SLOW DRIFT)"
        if t in super_cycle_tickers:
            total_bh_alpha_super.append(alpha)
        else:
            total_bh_alpha_tractor.append(alpha)

        all_strat_eq.append(strat_eq)
        all_strat_ret.append(df_trade['Strat_Ret'].fillna(0))
            
        print(f"[{t:>4s} | {cat}] B&H: {bh_ret:>8.1f}% | Infinity Gov: {strat_ret_pct:>8.1f}% | Alpha: {alpha:>+8.1f}% | MDD: {calc_mdd(strat_eq)*100:>6.1f}%")
        
    print(f"\n--- {era_name} VERDICT ---")
    if total_bh_alpha_super:
        print(f"Average Super Cycle Execution Alpha : {np.mean(total_bh_alpha_super):>+8.1f}%")
    if total_bh_alpha_tractor:
        print(f"Average Tractor Execution Alpha     : {np.mean(total_bh_alpha_tractor):>+8.1f}%")

    # Aggregate metrics across all tickers for this era
    if all_strat_eq:
        avg_eq = pd.concat(all_strat_eq, axis=1).mean(axis=1)
        all_ret = pd.concat(all_strat_ret, axis=1).mean(axis=1)
        return {
            "cagr": calc_cagr(avg_eq),
            "max_dd": calc_mdd(avg_eq),
            "sharpe": calc_sharpe(all_ret),
        }
    return {"cagr": 0.0, "max_dd": 0.0, "sharpe": 0.0}


if __name__ == "__main__":
    PID_FILE = Path(__file__).resolve().parent.parent / "data" / ".backtest_pid"
    results = []
    try:
        r1 = backtest_decade("1990 - 2000 (Dot-Com Boom)", "1989-01-01", "2000-12-31", 
                        ["CSCO", "MSFT", "INTC", "ORCL", "QCOM"], 
                        ["GE", "KO", "XOM", "PG", "IBM"], 
                        "1990-01-01")
        results.append(r1)
                        
        r2 = backtest_decade("2000 - 2010 (Lost Decade / Housing Bubble)", "1999-01-01", "2010-12-31", 
                        ["AAPL", "AMZN", "EBAY", "NVDA", "ATVI"], 
                        ["XOM", "WMT", "PG", "JNJ", "PFE"], 
                        "2000-01-01")
        results.append(r2)

    except Exception as e:
        print(f"Error: {e}")

    # Aggregate across all eras
    if results:
        avg_cagr = np.mean([r["cagr"] for r in results])
        avg_mdd = np.mean([r["max_dd"] for r in results])
        avg_sharpe = np.mean([r["sharpe"] for r in results])
        final = {
            "cagr": round(avg_cagr, 6),
            "max_dd": round(avg_mdd, 6),
            "sharpe": round(avg_sharpe, 4),
            "timestamp": datetime.now().isoformat(),
            "script": "rule_100_backtest_decades.py",
        }
        print(f"\n=== AGGREGATE: CAGR={avg_cagr*100:.1f}% | MDD={avg_mdd*100:.1f}% | Sharpe={avg_sharpe:.2f} ===")

        if "--json" in sys.argv:
            write_cache("The Infinity Governor", final)
            print(f"Results written to {CACHE_PATH}")

    # Clean up PID file so dashboard stops showing "Running"
    PID_FILE.unlink(missing_ok=True)
