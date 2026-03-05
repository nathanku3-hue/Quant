import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import sys
import json
import signal
import subprocess
import datetime
import atexit
from pathlib import Path
from functools import reduce
from filelock import FileLock
from core.release_metadata import build_release_cache_fingerprint
from core.dashboard_control_plane import coerce_proxy_numeric
from core.dashboard_control_plane import derive_hf_proxy_data_health
from core.dashboard_control_plane import ensure_payload_data_health
from core.data_orchestrator import get_macro_features
from views.regime_view import render_regime_banner_from_macro
from views.auto_backtest_view import render_auto_backtest_view
from views.optimizer_view import render_optimizer_view
from views.drift_monitor_view import render_drift_monitor_view
from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector
from core.dashboard_escalation import initialize_escalation_manager
# st_autorefresh removed in V3.10 — replaced by @st.fragment(run_every=)

# --- Phase 2: Backtest Cache + PID Infrastructure ---
BT_CACHE_PATH = Path("data/backtest_results.json")
BT_LOCK_PATH = str(BT_CACHE_PATH) + ".lock"
BT_PID_FILE = Path("data/.backtest_pid")


def _release_bound_cache_version(version: str) -> str:
    """
    Bind UI cache invalidation to both schema version and deployed release digest.

    Release controllers should inject TZ_RELEASE_DIGEST so UI cache state cannot
    drift across artifact promotions/rollbacks.
    """
    digest = str(os.getenv("TZ_RELEASE_DIGEST", "")).strip().lower()
    return build_release_cache_fingerprint(version, digest)

def read_bt_cache() -> dict:
    """Read backtest results with filelock protection."""
    lock = FileLock(BT_LOCK_PATH, timeout=5)
    try:
        with lock:
            return json.loads(BT_CACHE_PATH.read_text()) if BT_CACHE_PATH.exists() else {}
    except Exception:
        return {}

def is_backtest_running() -> tuple:
    """Probe PID file to check if a backtest subprocess is alive.
    Cross-checks the result cache: if results exist with a timestamp
    after the start time, the backtest is done regardless of PID state.
    Returns (running: bool, name: str, start_time: float).
    """
    if not BT_PID_FILE.exists():
        return False, "", 0.0
    try:
        content = BT_PID_FILE.read_text().strip()
        parts = content.split("|", 2)
        pid = int(parts[0])
        name = parts[1] if len(parts) > 1 else ""
        start_ts = float(parts[2]) if len(parts) > 2 else 0.0

        # Cross-check: if cache already has results newer than start, it's done
        cache = read_bt_cache()
        cached = cache.get(name, {})
        if cached.get("timestamp"):
            from datetime import datetime as _dt
            try:
                result_ts = _dt.fromisoformat(cached["timestamp"]).timestamp()
                if result_ts >= start_ts > 0:
                    BT_PID_FILE.unlink(missing_ok=True)
                    return False, "", 0.0
            except (ValueError, TypeError):
                pass

        os.kill(pid, 0)  # probe only, no signal
        return True, name, start_ts
    except (ProcessLookupError, ValueError, OSError):
        BT_PID_FILE.unlink(missing_ok=True)
        return False, "", 0.0

def spawn_backtest(script_path: str, strategy_name: str) -> int:
    """Spawn backtest subprocess with single-flight guard.
    Uses CREATE_NEW_PROCESS_GROUP to prevent child KeyboardInterrupt
    from propagating to the parent Streamlit process on Windows.
    """
    # Kill existing zombie first
    if BT_PID_FILE.exists():
        try:
            old_pid = int(BT_PID_FILE.read_text().strip().split("|")[0])
            os.kill(old_pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError, OSError):
            pass
    # Detach from parent console to prevent KeyboardInterrupt propagation
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen(
        [sys.executable, script_path, "--json"],
        cwd=str(Path(".").resolve()),
        creationflags=flags,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    BT_PID_FILE.write_text(f"{proc.pid}|{strategy_name}|{datetime.datetime.now().timestamp()}")
    return proc.pid

try:
    from scripts.alpha_quad_scanner import run_alpha_sovereign_scan
    from scripts.high_freq_data import AutoFetcher
    from scripts.options_hedging import calculate_optimal_hedge
except ImportError:
    st.error("Engine modules not found. Please run from the root directory.")
    st.stop()

st.set_page_config(page_title="Sovereign Cockpit", layout="wide", page_icon="🎯")

# --- Persistence Layer ---
CACHE_DIR = "data"
CACHE_FILE = os.path.join(CACHE_DIR, "last_scan_state.json")
os.makedirs(CACHE_DIR, exist_ok=True)


def _atomic_json_write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(datetime.datetime.now().timestamp() * 1000)}.tmp")
    try:
        tmp.write_text(json.dumps(payload), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _load_cached_scan_payload(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    data_rows = payload.get("data")
    proxy = payload.get("proxy")
    if not isinstance(data_rows, list):
        return None
    if not isinstance(proxy, dict):
        return None
    return payload


def _coerce_weight_series(raw_weights) -> pd.Series | None:
    if raw_weights is None:
        return None

    if isinstance(raw_weights, pd.Series):
        series = raw_weights.copy()
    elif isinstance(raw_weights, dict):
        series = pd.Series(raw_weights, dtype="float64")
    elif isinstance(raw_weights, list):
        tmp: dict[str, float] = {}
        for row in raw_weights:
            if isinstance(row, dict):
                asset = row.get("ticker") or row.get("asset") or row.get("symbol")
                weight = row.get("weight")
                if asset is not None and weight is not None:
                    tmp[str(asset)] = weight
        series = pd.Series(tmp, dtype="float64")
    else:
        return None

    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty:
        return None

    total = float(series.sum())
    if abs(total) < 1e-12:
        return None

    return (series / total).sort_index()


def _load_weight_series_from_json(path: Path) -> pd.Series | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

    candidates = []
    if isinstance(payload, dict):
        candidates.extend(
            [
                payload.get("weights"),
                payload.get("baseline_weights"),
                payload.get("live_weights"),
                payload.get("expected_allocation"),
                payload.get("allocation"),
                payload.get("latest"),
                payload,
            ]
        )
    else:
        candidates.append(payload)

    for candidate in candidates:
        series = _coerce_weight_series(candidate)
        if series is not None:
            return series
    return None


def _load_baseline_from_latest_pointer() -> tuple[pd.Series | None, dict | None]:
    """
    Load baseline weights and metadata from latest pointer.

    Phase 33A Step 7: Loads baseline from pointer-based registry structure.

    Returns:
        (weights, metadata) tuple
        - weights: pd.Series of expected allocation (normalized)
        - metadata: dict with baseline_id, strategy_name, created_at
    """
    latest_path = Path("data/backtest_baselines/latest.json")
    if not latest_path.exists():
        return None, None

    try:
        pointer = json.loads(latest_path.read_text())
        baseline_id = pointer.get("baseline_id")
        if not baseline_id:
            return None, None

        # Load expected allocation from parquet
        allocation_path = Path(f"data/backtest_baselines/{baseline_id}/expected_allocation.parquet")
        if not allocation_path.exists():
            return None, None

        allocation_df = pd.read_parquet(allocation_path)

        # Get latest allocation (last row)
        if allocation_df.empty:
            return None, None

        latest_weights = allocation_df.iloc[-1]  # Last rebalance
        weights = _coerce_weight_series(latest_weights)

        # Load metadata
        metadata_path = Path(f"data/backtest_baselines/{baseline_id}/metadata.json")
        metadata = None
        if metadata_path.exists():
            raw_metadata = json.loads(metadata_path.read_text())
            # Map execution_timestamp -> created_at for drift monitor view compatibility
            metadata = {
                "baseline_id": raw_metadata.get("baseline_id"),
                "strategy_name": raw_metadata.get("strategy_name"),
                "strategy_version": raw_metadata.get("strategy_version"),
                "created_at": raw_metadata.get("execution_timestamp"),  # Key mapping
            }

        return weights, metadata

    except Exception as e:
        import logging
        logging.warning(f"Failed to load baseline from latest pointer: {e}")
        return None, None

# --- Sector & Proxy Mapping ---
SECTOR_MAP = {
    'NVDA': 'Compute', 'AMD': 'Compute', 'TSM': 'Compute', 'INTC': 'Compute',
    'MU': 'Memory', 'WDC': 'Memory', 'SNDK': 'Memory', 
    'LRCX': 'Semicap', 'AMAT': 'Semicap', 'TER': 'Semicap',
    'AVGO': 'Networking', 'MRVL': 'Networking',
    'SMCI': 'AI Infra', 'VRT': 'AI Infra',
    'CEG': 'Energy', 'ETN': 'Energy',
    'MSFT': 'Cloud', 'AMZN': 'Cloud', 'GOOGL': 'Cloud', 
    'META': 'Software', 'RBRK': 'Data Sec',
    'CLS': 'EMS', 'CIEN': 'Optical', 'COHR': 'Optical',
    'NBIS': 'Biotech', 'TSLA': 'Auto/Robot'
}

PROXY_DB = {
    'Compute': { 'type': 'Sector Only', 'conf': 'p=82%', 'name': 'TSMC', 'span': 'YoY', 'key': 'tsmc_monthly_yoy' },
    'Memory': { 'type': 'Individual + Sector', 'conf': 'p=75%', 'name': 'DRAM', 'span': 'Trend', 'key': 'dram_spot_trend', 'sec_name': 'Semi PPI', 'sec_span': 'MoM', 'sec_key': 'semi_ppi' },
    'Semicap': { 'type': 'Sector Only', 'conf': 'p=64%', 'name': 'Semi PPI', 'span': 'MoM', 'key': 'semi_ppi' }, 
    'Networking': { 'type': 'Sector Only', 'conf': 'p=55%', 'name': 'EWY Exports', 'span': 'YoY', 'key': 'ewy_exports' },
    'AI Infra': { 'type': 'Sector Only', 'conf': 'p=60%', 'name': 'Power Const.', 'span': 'YoY', 'key': 'power_const' },
    'Energy': { 'type': 'Sector Only', 'conf': 'p=70%', 'name': 'URA', 'span': 'Trend', 'key': 'energy_price_trend' },
    'Cloud': { 'type': 'Sector Only', 'conf': 'p=85%', 'name': 'AWS/Azure', 'span': 'YoY', 'key': 'cloud_growth_yoy' },
    'Biotech': { 'type': 'Sector Only', 'conf': 'p=60%', 'name': 'XBI Funding', 'span': 'Trend', 'key': 'xbi_funding_trend' },
    'Optical': { 'type': 'None', 'conf': 'NA', 'name': '[NO PROXY]', 'span': '', 'key': None },
    'Software': { 'type': 'None', 'conf': 'NA', 'name': '[NO PROXY]', 'span': '', 'key': None },
    'Data Sec': { 'type': 'None', 'conf': 'NA', 'name': '[NO PROXY]', 'span': '', 'key': None },
    'EMS': { 'type': 'None', 'conf': 'NA', 'name': '[NO PROXY]', 'span': '', 'key': None },
    'Auto/Robot': { 'type': 'None', 'conf': 'NA', 'name': '[NO PROXY]', 'span': '', 'key': None }
}

def fetch_auto_data():
    auto = AutoFetcher()
    return {
        "tsmc_monthly_yoy": auto.fetch_tsmc_yoy() or {"val": 0.20, "span": "YoY"},
        "energy_price_trend": auto.fetch_energy_trend() or {"val": 0.0, "span": "Trend"},
        "cloud_growth_yoy": auto.fetch_cloud_growth() or {"val": 0.30, "span": "YoY"},
        "dram_spot_trend": auto.fetch_dram_trend() or {"val": 0.05, "span": "Trend"},
        "xbi_funding_trend": {"val": 0.10, "span": "Trend"}
    }

@st.cache_data(ttl=3600*4) # cache for 4 hours
def fetch_macro_score():
    try:
        # Fetch data robustly
        df = yf.download(["^TNX", "VWEHX", "VFISX"], period="2y", progress=False)['Close']
        if df.empty or len(df) < 200:
            return None
            
        tnx = df['^TNX'].dropna()
        vwehx = df['VWEHX'].dropna()
        vfisx = df['VFISX'].dropna()
        
        # 1. Rate Velocity (Max pain at +0.50)
        rate_val = 50.0 # Default max
        if len(tnx) >= 63:
            vel = tnx.iloc[-1] - tnx.iloc[-63]
            if vel <= 0.0:
                rate_val = 50.0
            elif vel >= 0.50:
                rate_val = 0.0
            else:
                rate_val = 50.0 * ((0.50 - vel) / 0.50)
                
        # 2. Credit Solvency (Calibrated Phase 57-F: Max +4.65%, Panic -2.0%)
        credit_val = 50.0 # Default max
        common_idx = vwehx.index.intersection(vfisx.index)
        if len(common_idx) >= 200:
            ratio = vwehx.loc[common_idx] / vfisx.loc[common_idx]
            sma200 = ratio.rolling(200).mean().iloc[-1]
            curr_ratio = ratio.iloc[-1]
            
            cdist = ((curr_ratio - sma200) / sma200) * 100
            
            if cdist >= 4.65:
                credit_val = 50.0
            elif cdist <= -2.0:
                credit_val = 0.0
            else:
                credit_val = 50.0 * ((cdist - (-2.0)) / (4.65 - (-2.0)))
                
        total_score = round(rate_val + credit_val)
        return {
            "score": total_score,
            "rate_score": round(rate_val),
            "credit_score": round(credit_val)
        }
    except Exception:
        return None


@st.cache_data(ttl=3600*4) # cache for 4 hours
def get_breadth_status():
    """
    Detects Internal Rot (RSP vs SPY Divergence).
    Returns: status_label, status_color
    """
    try:
        data = yf.download(['RSP', 'SPY'], period='6mo', progress=False)['Close']
        if data.empty or len(data) < 50:
            return "UNKNOWN (No Data)", "#888"
            
        spy = data['SPY']
        rsp = data['RSP']
        
        spy_now = spy.iloc[-1].item() if not isinstance(spy.iloc[-1], float) else spy.iloc[-1]
        spy_sma50 = spy.rolling(window=50).mean().iloc[-1].item() if not isinstance(spy.rolling(window=50).mean().iloc[-1], float) else spy.rolling(window=50).mean().iloc[-1]
        
        rsp_now = rsp.iloc[-1].item() if not isinstance(rsp.iloc[-1], float) else rsp.iloc[-1]
        rsp_sma50 = rsp.rolling(window=50).mean().iloc[-1].item() if not isinstance(rsp.rolling(window=50).mean().iloc[-1], float) else rsp.rolling(window=50).mean().iloc[-1]
        
        if rsp_now > rsp_sma50:
            return "HEALTHY (Broad)", "#00FFAA"
        elif (spy_now > spy_sma50) and (rsp_now < rsp_sma50):
            return "DIVERGENCE (Thinning)", "#FFD700"
        else:
            return "WEAK (Correction)", "#ff4444"
    except Exception:
        return "UNKNOWN (Error)", "#888"


def get_prices_and_technicals(tickers):
    data = {}
    if not tickers:
        return data
    try:
        # Batch fetch all tickers at once to save massive API latency
        hist_all = yf.download(tickers, period="1y", progress=False)
        for t in tickers:
            try:
                if isinstance(hist_all.columns, pd.MultiIndex):
                    # Multi-tickers
                    hist = hist_all.xs(t, level=1, axis=1).dropna()
                else:
                    # Single ticker
                    hist = hist_all.dropna()
                    
                if len(hist) >= 14:
                    close = hist['Close']
                    volatility_3m = close.pct_change().std() * (252 ** 0.5)
                    current = close.iloc[-1].item()
                    
                    ema21 = close.ewm(span=21, adjust=False).mean().iloc[-1].item()
                    sma50 = close.rolling(window=50, min_periods=10).mean().iloc[-1].item()
                    sma200 = close.rolling(window=200, min_periods=10).mean().iloc[-1].item()
                    # Calculate 14-Day ATR
                    high_low = hist['High'] - hist['Low']
                    high_close = (hist['High'] - close.shift(1)).abs()
                    low_close = (hist['Low'] - close.shift(1)).abs()
                    ranges = pd.concat([high_low, high_close, low_close], axis=1)
                    true_range = ranges.max(axis=1)
                    atr = true_range.ewm(alpha=1/14, adjust=False).mean().iloc[-1].item()
                    
                    # Calculate Convexity (Acceleration)
                    ema10 = close.ewm(span=10, adjust=False).mean()
                    slope = ema10.diff()
                    avg_slope = slope.rolling(window=20).mean().iloc[-1].item() if not pd.isna(slope.rolling(window=20).mean().iloc[-1].item()) else 1.0
                    curr_slope = slope.iloc[-1].item() if not pd.isna(slope.iloc[-1].item()) else 1.0
                    
                    if avg_slope <= 0:
                        convexity = 1.0
                    else:
                        convexity = curr_slope / avg_slope
                        
                    data[t] = {"price": current, "ema21": ema21, "sma50": sma50, "sma200": sma200, "atr": atr, "convexity": convexity}
                else:
                    current = hist['Close'].iloc[-1].item() if ('Close' in hist and not hist.empty) else 0.0
                    data[t] = {"price": current, "ema21": current, "sma50": current, "sma200": current, "atr": 0.0, "convexity": 1.0}
            except Exception:
                data[t] = {"price": 0.0, "ema21": 0.0, "sma50": 0.0, "sma200": 0.0, "atr": 0.0, "convexity": 1.0}
    except Exception:
        # Fallback if bulk fetch completely fails
        for t in tickers:
            data[t] = {"price": 0.0, "ema21": 0.0, "sma50": 0.0, "sma200": 0.0, "atr": 0.0, "convexity": 1.0}
    return data

def run_and_save_scan():
    with st.spinner("Booting Sensors & Firing Physics Engine..."):
        proxy_data = fetch_auto_data()
        data_health = derive_hf_proxy_data_health(proxy_data)
        df_scan = run_alpha_sovereign_scan(manual_inputs=proxy_data)
        
        if df_scan is not None and not df_scan.empty:
            technicals = get_prices_and_technicals(df_scan['Ticker'].tolist())
            
            df_scan['Current_Price'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('price', 0.0))
            df_scan['EMA21'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('ema21', 0.0))
            df_scan['SMA50'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('sma50', 0.0))
            df_scan['SMA200'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('sma200', 0.0))
            df_scan['ATR'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('atr', 0.0))
            df_scan['Convexity'] = df_scan['Ticker'].apply(lambda x: technicals.get(x, {}).get('convexity', 1.0))
            
            df_scan['Sector'] = df_scan['Ticker'].map(SECTOR_MAP).fillna('Unknown')
            
            macro = fetch_macro_score()
            macro_score = macro['score'] if macro else 50
            macro_risk = (macro_score < 50)
            
            def calc_cluster(row):
                if row['Current_Price'] <= 0: return "Unknown"
                atr_ratio = row['ATR'] / row['Current_Price']
                if atr_ratio < 0.025: return "I. Heavy"
                elif atr_ratio <= 0.045: return "II. Sprinter"
                else: return "III. Scout"
            
            df_scan['Cluster_Type'] = df_scan.apply(calc_cluster, axis=1)
            
            def get_sovereign_entry_price(row):
                curr = row['Current_Price']
                ema21 = row['EMA21']
                sma50 = row['SMA50']
                sma200 = row['SMA200']
                ms = macro_score
                ase = row['Score']
                conv = row['Convexity']
                ctype = str(row['Cluster_Type']).upper()
                
                if curr <= 0: return 0.0, "N/A"
                
                base_support = sma50
                rationale = "50-SMA (Standard)"
                
                if ms >= 80 and ase >= 95 and conv <= 1.5:
                    base_support = ema21
                    rationale = "21-EMA (God Mode)"
                
                if conv > 1.5:
                    base_support = sma50
                    rationale = "50-SMA (Mania Protection)"
                    
                if ms < 50:
                    base_support = sma50
                    rationale = "50-SMA (Macro Defense)"
                    
                if curr < base_support:
                    if base_support == ema21:
                        base_support = sma50
                        rationale = "50-SMA (21 Broken)"
                    elif base_support == sma50:
                        base_support = sma200
                        rationale = "200-Day (Deep Value)"
                    else:
                        return 0.0, "NO SUPPORT"
                        
                # Phase 52-F: Max Flush Logic
                if "SCOUT" in ctype:
                    max_flush = 0.16
                elif "SPRINTER" in ctype:
                    max_flush = 0.11
                else:
                    max_flush = 0.05
                    
                # Phase 52-F: Quality Premium Logic
                if ase >= 95:
                    premium = 0.05
                elif ase >= 90:
                    premium = 0.03
                else:
                    premium = 0.00
                    
                net_buffer = max(0, max_flush - premium)
                final_entry_price = base_support * (1 - net_buffer)
                
                return pd.Series([final_entry_price, rationale, max_flush, premium, base_support])

            entries = df_scan.apply(get_sovereign_entry_price, axis=1)
            df_scan[['Entry_Price', 'Support_Label', 'Max_Flush', 'Premium', 'Base_Support']] = entries
            df_scan['Support_Price'] = df_scan['Entry_Price']
            
            def calc_dist(row):
                if row['Entry_Price'] <= 0: return 0.0
                return ((row['Current_Price'] / row['Entry_Price']) - 1) * 100
            df_scan['Tech_Support_Dist'] = df_scan.apply(calc_dist, axis=1)
            
            def calc_tactics(row):
                atr = row['ATR']
                price = row['Current_Price']
                dist_pct = row['Tech_Support_Dist']
                entry = row['Entry_Price']
                score = row['Score']
                convexity = row['Convexity']
                cluster = row['Cluster_Type']
                
                if atr <= 0 or price <= 0:
                    return entry * 0.95, "N/A", cluster, 3.0
                    
                if "I. HEAVY" in str(cluster).upper():
                    limit = 8.2
                elif "II. SPRINTER" in str(cluster).upper():
                    limit = 8.8
                else:
                    limit = 12.3
                
                active_limit = 6.0 if macro_risk else limit
                
                if score >= 90:
                    # Phase 62-F Adaptive Governor
                    accel_factor = max(0, convexity - 1.0)
                    stretch_factor = max(0, dist_pct) / limit if limit > 0 else 0
                    penalty_weight = 0.5 * accel_factor * stretch_factor
                    multiplier = 3.0 / (1.0 + penalty_weight)
                    
                    # Hard Clamps
                    multiplier = max(1.5, min(3.0, multiplier))
                    
                    if dist_pct > active_limit and multiplier < 2.5: # Consider it tight if < 2.5
                        return price - (multiplier * atr), f"🚀 SUPER CYCLE | ⚠️ PARABOLIC MANIA -> TRAIL ({multiplier:.1f}x)", cluster, multiplier
                    else:
                        return entry - (multiplier * atr), f"🚀 SUPER CYCLE | LINEAR TREND -> KINETIC TRAIL ({multiplier:.1f}x)", cluster, multiplier
                else:
                    return entry - (3.0 * atr), "🛡️ STANDARD TREND | WIDE STOP ONLY (3.0x)", cluster, 3.0
            
            tactics = df_scan.apply(calc_tactics, axis=1)
            df_scan['Stop_Loss'] = tactics.apply(lambda x: x[0])
            df_scan['Tactical_Warning'] = tactics.apply(lambda x: x[1])
            df_scan['Cluster'] = tactics.apply(lambda x: x[2])
            df_scan['Multiplier'] = tactics.apply(lambda x: x[3])
            
            # Risk Distance calculation (use abs to prevent negative targets on trailing stops)
            df_scan['Risk_Dist'] = abs(df_scan['Entry_Price'] - df_scan['Stop_Loss'])
            
            # 3:1 Asymmetric Return Target (3R Milestone)
            df_scan['Target_Price'] = df_scan['Entry_Price'] + (3.0 * df_scan['Risk_Dist'])
            
            # --- Generate Tri-Column Proxy Data ---
            def generate_tri_column(row):
                sector = row['Sector']
                score = row['Score']
                price_dist = row['Tech_Support_Dist']
                
                proxy_info = PROXY_DB.get(sector, PROXY_DB['Software'])
                
                # 1. Type (Confidence)
                p_type = proxy_info['type'] if proxy_info['type'] != 'None' else "[NO PROXY]"
                p_conf = proxy_info['conf'] if proxy_info['type'] != 'None' else ""
                
                # 2. Content (Live Data)
                p_content = "[NO DATA]"
                actual_val = 0.0
                if proxy_info['key'] and proxy_info['key'] in proxy_data:
                    proxy_val_data = proxy_data[proxy_info['key']]
                    raw_proxy_val = proxy_val_data.get('val') if isinstance(proxy_val_data, dict) else proxy_val_data
                    actual_val = coerce_proxy_numeric(raw_proxy_val, default=0.0)
                    span = proxy_val_data.get('span', proxy_info.get('span', '')) if isinstance(proxy_val_data, dict) else proxy_info.get('span', '')
                    
                    p_content = f"{proxy_info['name']} ({span}): {actual_val*100:+.1f}%"
                    
                    if proxy_info['type'] == 'Individual + Sector' and 'sec_name' in proxy_info:
                        sec_key = proxy_info['sec_key']
                        if sec_key in proxy_data:
                            sec_val_data = proxy_data[sec_key]
                            raw_sec_val = sec_val_data.get('val') if isinstance(sec_val_data, dict) else sec_val_data
                            sec_val = coerce_proxy_numeric(raw_sec_val, default=0.0)
                            sec_span = sec_val_data.get('span', proxy_info.get('sec_span', '')) if isinstance(sec_val_data, dict) else proxy_info.get('sec_span', '')
                            p_content += f" | {proxy_info['sec_name']} ({sec_span}): {sec_val*100:+.1f}%"
                        else:
                            p_content += f" | {proxy_info['sec_name']} ({proxy_info.get('sec_span', '')}): Syncing"
                elif proxy_info['name'] != '[NO PROXY]':
                    p_content = f"{proxy_info['name']}: Awaiting Sync"
                    
                # 3. Signal (The Truth Table)
                p_signal = "N/A"
                if proxy_info['type'] != 'None':
                    proxy_is_strong = actual_val > 0.02 # Generally up
                    proxy_is_weak = actual_val <= 0.02  # Flat or down
                    price_is_strong = price_dist > 5.0  # Ripping above MA50
                    price_is_weak = price_dist <= 5.0   # Flat or below
                    
                    if proxy_is_strong and price_is_weak:
                        p_signal = "COILED SPRING"
                    elif proxy_is_strong and price_is_strong:
                        p_signal = "CORRELATED"
                    elif proxy_is_weak and price_is_strong:
                        p_signal = "DIVERGING"
                    elif proxy_is_weak and price_is_weak and score > 0:
                        p_signal = "CORRECTING"
                    elif proxy_is_weak and price_is_strong and score == 0:
                        p_signal = "MISPRICED"
                        
                return pd.Series([p_type, p_conf, p_content, p_signal])

            df_scan[['Proxy_Type', 'P_Value', 'Proxy_Content', 'Proxy_Signal']] = df_scan.apply(generate_tri_column, axis=1)

            def generate_rating(row):
                action = str(row['Action'])
                score = row['Score']
                dist = row['Tech_Support_Dist']
                support = row['Support_Price']
                label = row['Support_Label']
                proxy_type = str(row['Proxy_Type'])
                has_proxy = "[NO PROXY]" not in proxy_type
                warning = str(row.get('Tactical_Warning', ''))
                signal = str(row.get('Proxy_Signal', ''))
                
                if "KILL" in action:
                    return "EXIT (Macro/Sector Rot)"
                
                if "PARABOLIC" in warning:
                    return "EXIT / TRAIL TIGHT (Mania Top)"
                
                if "STRETCH" in warning:
                    return "WAIT (Terminal Stretch)"
                
                elif score == 100:
                    if not has_proxy:
                        return "WATCH (Miss Proxy Cap)"
                    elif dist > 5.0:
                        label_short = label.split(" (")[0]
                        return f"WATCH (Wait for {label_short}: ${support:.2f})"
                    elif signal == "COILED SPRING":
                        return "ENTER: STRONG BUY (Coiled)"
                    elif dist >= -2.0:
                        return "ENTER: BUY (Baseline)"
                    else:
                        return "ENTER: BUY"
                        
                elif score >= 90:
                    return "WATCH / HOLD"
                        
                else:
                    return "IGNORE"

            df_scan['Rating'] = df_scan.apply(generate_rating, axis=1)
            
            # --- Leverage logic ---
            def calc_leverage(row):
                rating = str(row.get('Rating', ''))
                convexity = row.get('Convexity', 1.0)
                current_macro = macro['score'] if macro else 50
                
                if "STRONG BUY" in rating:
                    if current_macro >= 80 and convexity <= 1.5:
                        return "LEAPs"
                    else:
                        return "Avoid"
                else:
                    return ""
            df_scan['Leverage'] = df_scan.apply(calc_leverage, axis=1)
            
            # Save state
            payload = {
                "timestamp": datetime.datetime.now().isoformat(),
                "proxy": proxy_data,
                "data_health": data_health,
                "data": df_scan.to_dict(orient="records")
            }
            _atomic_json_write(Path(CACHE_FILE), payload)
            return payload
    return None

# --- Load State ---
payload = _load_cached_scan_payload(Path(CACHE_FILE))
if payload is None:
    payload = run_and_save_scan()

if not payload:
    st.error("Engine failed to boot and no cache available.")
    st.stop()

# --- Load Institutional-Grade Parquet Data (for Tabs 3 & 5) ---
# Dashboard uses custom yfinance scanning for alpha discovery (Tabs 1,2,4)
# But Tab 3 (Backtest) and Tab 5 (Portfolio) require TRI-based institutional data
parquet_data_available = False
prices_wide = pd.DataFrame()
returns_wide = pd.DataFrame()
ticker_map_parquet = {}
sector_map_parquet = None
fundamentals_wide = None

try:
    from core.data_orchestrator import load_unified_data

    # Attempt to load historical parquet data
    unified_package = load_unified_data(
        mode="historical",
        top_n=2000,
        start_year=2000,
        universe_mode="top_liquid",
    )

    prices_wide = unified_package.prices
    returns_wide = unified_package.returns
    ticker_map_parquet = unified_package.ticker_map
    sector_map_parquet = unified_package.sector_map
    fundamentals_wide = unified_package.fundamentals

    # Check if data loaded successfully
    if not prices_wide.empty and not returns_wide.empty:
        parquet_data_available = True
        st.sidebar.success(f"✅ Parquet TRI data loaded: {prices_wide.shape[1]} tickers")
    else:
        st.sidebar.warning("⚠️ Parquet data empty - Tabs 3 & 5 in placeholder mode")

except Exception as e:
    st.sidebar.warning(f"⚠️ Parquet data unavailable: {type(e).__name__}")
    st.sidebar.caption("Tabs 3 & 5 will display placeholders. Custom alpha scanning (Tabs 1,2,4) unaffected.")
    # Continue with yfinance-only mode

# Process Payload
df_scan = pd.DataFrame(payload.get("data", []))
proxy_data = payload.get("proxy", {})
if not isinstance(proxy_data, dict):
    proxy_data = {}
data_health = ensure_payload_data_health(payload)

# Schema Mismatch Check (Force refresh if legacy cache missing Phase 56 tactical execution columns)
required_cols = ['Proxy_Type', 'P_Value', 'Proxy_Content', 'Proxy_Signal', 'Tech_Support_Dist', 'Entry_Price', 'Stop_Loss', 'Target_Price', 'Leverage', 'Cluster', 'Tactical_Warning', 'Max_Flush', 'Premium']
is_legacy_data = not isinstance(proxy_data.get('energy_price_trend', {}), dict)

if is_legacy_data or not all(col in df_scan.columns for col in required_cols):
    refreshed_payload = run_and_save_scan()
    if refreshed_payload:
        payload = refreshed_payload
        df_scan = pd.DataFrame(payload.get("data", []))
        proxy_data = payload.get("proxy", {})
        if not isinstance(proxy_data, dict):
            proxy_data = {}
        data_health = ensure_payload_data_health(payload)
    else:
        if is_legacy_data and all(col in df_scan.columns for col in required_cols):
            st.warning("Engine refresh failed. Using previous cached payload for this session.")
        else:
            st.error("Engine refresh failed and cached schema is not runnable. Retry with Force Engine Refresh.")
            st.stop()

last_updated_raw = str(payload.get("timestamp", "")).strip()
try:
    last_updated = datetime.datetime.fromisoformat(last_updated_raw) if last_updated_raw else datetime.datetime.now()
except ValueError:
    last_updated = datetime.datetime.now()

# Time ago string
now = datetime.datetime.now()
diff = now - last_updated
mins_ago = int(diff.total_seconds() / 60)
if mins_ago == 0:
    time_str = "just now"
elif mins_ago < 60:
    time_str = f"{mins_ago} min ago"
else:
    hours = mins_ago // 60
    time_str = f"{hours} hours ago"

# --- Sidebar ---
# --- Calculate health status for sidebar badge ---
health_status = str(data_health.get("status", "DEGRADED")).upper()
health_ratio = data_health.get("degraded_count", 0) / max(data_health.get("total_signals", 1), 1)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"**Last Sync:** {time_str}")
    if st.button("🔄 Force Engine Refresh", type="primary"):
        run_and_save_scan()
        st.rerun()

    # Compact health badge
    badge_color = "#00cc66" if health_status == "HEALTHY" else "#ffb020"
    st.markdown(
        f'<span style="color:{badge_color};">● {health_status}</span>',
        unsafe_allow_html=True
    )

    st.divider()
    st.header("🛡️ Hedge Harvester")
    hedge_ticker = st.text_input("Enter Ticker for Collar:", value="MU").upper()
    if st.button("Generate Option Yield"):
        with st.spinner(f"Pricing vol for {hedge_ticker}..."):
            res = calculate_optimal_hedge(hedge_ticker)
            if "Action" not in res:
                st.error("Engine error retrieving chain.")
            elif res.get("Action") in ["SELL CALL", "DO NOT SELL"]:
                st.success(f"Strike: ${res.get('Strike')} | Exp: {res.get('Exp')} Days")
                if 'Est_Yield' in res:
                    st.write(f"**Premium Yield:** {res['Est_Yield']*100:.2f}%")
            else:
                st.error(str(res))

# --- Load Drone Intel (Fresh Finds) ---
FRESH_FINDS_FILE = "data/fresh_finds.json"
drone_finds = []
drone_count = 0
drone_timestamp = ""
if os.path.exists(FRESH_FINDS_FILE):
    try:
        with open(FRESH_FINDS_FILE, "r") as f:
            drone_data = json.load(f)
            drone_count = drone_data.get("count", 0)
            drone_finds = drone_data.get("assets", [])
            if "timestamp" in drone_data:
                dt_obj = datetime.datetime.fromisoformat(drone_data["timestamp"])
                drone_timestamp = dt_obj.strftime("%H:%M")
    except Exception:
        pass

# --- Header ---
st.title("🎯 The Sovereign Cockpit")
st.markdown(f"Full Auto Execution Mode | Proxy Integrity Lock <span style='color:#888;font-size:0.9em;'>(Updated: {time_str})</span>", unsafe_allow_html=True)
health_ratio = float(data_health.get("degraded_ratio", 1.0))
health_ratio = max(0.0, min(1.0, health_ratio))

macro = fetch_macro_score()
breadth, breadth_color = get_breadth_status()

# --- FR-041 Governor: Persistent Regime Banner (Institutional Standard) ---
# Load institutional-grade macro features for RegimeManager
try:
    macro_features = get_macro_features(prefer_tri=True)
    # Use most recent date from available data
    if not macro_features.empty and 'date' in macro_features.columns:
        macro_features = macro_features.set_index('date')
    render_regime_banner_from_macro(
        macro=macro_features,
        index=macro_features.index,
        title="FR-041 Governor",
        simplified=True,  # Progressive disclosure: 3 visible metrics
    )
except Exception as e:
    # Fallback: Show legacy macro gravity score if RegimeManager unavailable
    st.warning(f"⚠️ FR-041 Governor unavailable ({type(e).__name__}). Displaying legacy macro score.")
    if macro:
        score = macro['score']

        # Execution Rule (Legacy)
        if score >= 80:
            if "HEALTHY" not in breadth:
                regime = "1.00x (Margin Restricted)"
                color = "#00cc66"
            else:
                regime = "1.25x (Leveraged Expansion)"
                color = "#00FFAA"
        elif score >= 50:
            if "HEALTHY" not in breadth:
                regime = "0.80x (Breadth Trim)"
                color = "#00cc66"
            else:
                regime = "1.00x (Strategic Deploy)"
                color = "#00cc66"
        elif score >= 30:
            regime = "0.50x (Defensive Core)"
            color = "#FFD700"
        else:
            regime = "0.00x (Liquidity Vacuum)"
            color = "#ff4444"

        st.markdown(f"""
        <div style="padding:15px; border:1px solid {color}; border-radius:5px; background-color:rgba(0,0,0,0.2); margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <h4 style="margin:0; color:#aaa; font-size:0.9rem; text-transform:uppercase;">MACRO GRAVITY SCORE (LEGACY)</h4>
                    <div style="font-size: 2.5rem; font-weight: 800; color:{color}; line-height: 1;">{score} <span style="font-size:1rem; color:#888;">/ 100</span></div>
                    <div style="margin-top: 5px; font-size: 0.9rem;">
                        <b>BREADTH (Internal):</b> <span style="color:{breadth_color}; font-weight:bold;">{breadth}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <h4 style="margin:0; color:#aaa; font-size:0.9rem; text-transform:uppercase;">ALLOWABLE EXPOSURE</h4>
                    <div style="font-size: 1.5rem; font-weight: 600; color:{color};">{regime}</div>
                    <div style="font-size: 0.8rem; color:#888; margin-top:5px;">
                        Rates: {macro['rate_score']}/50 | Credit: {macro['credit_score']}/50
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if drone_count > 0:
    st.info(f"🛸 **DRONE INTEL:** {drone_count} New Targets Detected dynamically by Scout Drone (Last Sweep: {drone_timestamp})")

# Custom Sort: Prioritize Actionable Ratings
def rate_weight(val):
    v = str(val).upper()
    if "ENTER: STRONG BUY" in v: return 1
    if "ENTER: BUY" in v: return 2
    if "EXIT" in v: return 3
    if "WATCH (" in v and "Miss" not in v and "No" not in v: return 4
    if "WATCH" in v or "HOLD" in v: return 5
    if "IGNORE" in v: return 6
    if "AVOID" in v: return 7
    return 8

df_scan['SortWeight'] = df_scan['Rating'].apply(rate_weight)
df_scan = df_scan.sort_values(by=['SortWeight', 'Score'], ascending=[True, False]).drop(columns=['SortWeight'])

# --- Drift Monitor setup (shared across sidebar + Tab 6) ---
drift_alert_manager = None
drift_detector = None
baseline_weights, baseline_metadata = _load_baseline_from_latest_pointer()
live_weights = _load_weight_series_from_json(Path("data/live_positions/latest.json"))

if live_weights is None:
    live_candidate = st.session_state.get("live_weights")
    if live_candidate is None:
        live_candidate = st.session_state.get("optimizer_weights")
    live_weights = _coerce_weight_series(live_candidate)

try:
    drift_alert_manager = DriftAlertManager(db_path=Path("data/drift_alerts.duckdb"))
    drift_detector = DriftDetector(sigma_threshold=2.0)

    # Phase 33B Slice 4.3: Escalation manager initialization (extracted to shared function)
    initialize_escalation_manager(
        alert_manager=drift_alert_manager,
        session_state=st.session_state,
    )

except Exception as exc:
    with st.sidebar:
        st.warning(f"⚠️ Drift monitor disabled: {type(exc).__name__}")

if drift_alert_manager is not None:
    try:
        sidebar_alerts = drift_alert_manager.get_active_alerts()
        sidebar_level = "GREEN"
        if sidebar_alerts:
            level_rank = {"GREEN": 0, "YELLOW": 1, "RED": 2}
            sidebar_level = max(
                (str(alert.alert_level).upper() for alert in sidebar_alerts),
                key=level_rank.get,
            )
        with st.sidebar:
            if sidebar_level == "RED":
                st.error(f"🔴 Drift: {len(sidebar_alerts)} active")
            elif sidebar_level == "YELLOW":
                st.warning(f"🟡 Drift: {len(sidebar_alerts)} active")
            else:
                st.success("🟢 Drift: clear")
    except Exception:
        # Keep optional sidebar indicator fail-safe.
        pass

# --- Layout: TABS (Phase 3: Unified Command Center) ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Ticker Pool & Proxies",
    "🏥 Data Health",           # NEW
    "🔍 Drift Monitor",          # PROMOTED
    "🔬 Daily Scan",
    "📈 Backtest Lab",           # KEEP (moved to tab5)
    "🧩 Modular Strategies",
    "💼 Portfolio Builder",
])

# ==========================================
# TAB 1: TICKER POOL & PROXY MONITOR
# ==========================================
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("The Sovereign Pool (Proxy Gated)")
    with col2:
        st.markdown("<div style='text-align: right; margin-top: 15px;'><span style='background-color: rgba(255,255,255,0.1); padding: 5px 10px; border-radius: 5px; font-size: 0.85em; color: #88ccff;'>⚙️ Active Engine: <b>🌊 Sovereign Alpha (Phase 65)</b></span></div>", unsafe_allow_html=True)
    
    display_cols = ['Ticker', 'Leverage', 'Cluster', 'Current_Price', 'Entry_Price', 'Stop_Loss', 'Target_Price', 'Tactical_Warning', 'Proxy_Type', 'P_Value', 'Proxy_Content', 'Proxy_Signal', 'Rating', 'Score']
    view_df = df_scan[display_cols].copy()
    
    # Currency formatting
    view_df['Current_Price'] = view_df['Current_Price'].map("${:.2f}".format)
    
    def format_entry(row):
        ep = row.get('Entry_Price', 0.0)
        flush = row.get('Max_Flush', 0.0)
        prem = row.get('Premium', 0.0)
        if ep > 0:
            return f"${ep:.2f}\n(Flush -{flush*100:.0f}% | Prem +{prem*100:.0f}%)"
        return "N/A"
        
    view_df['Entry_Price'] = df_scan.apply(format_entry, axis=1)
    
    def format_stop(row):
        sl = row['Stop_Loss']
        entry = row['Entry_Price']
        price = row['Current_Price']
        warning = str(row.get('Tactical_Warning', ''))
        rating = str(row.get('Rating', '')).upper()
        
        if not ("HOLD" in rating or "ENTER:" in rating):
            return ""
            
        if "TRAIL" in warning and "PARABOLIC" in warning:
            if price > 0:
                pct = ((price - sl) / price) * 100
                return f"${sl:.2f} (Trail -{pct:.1f}%)"
            return f"${sl:.2f}"
            
        if entry > 0:
            pct = ((entry - sl) / entry) * 100
            if pct < 0: pct = 0 # safety
            return f"${sl:.2f} (-{pct:.1f}%)"
        return f"${sl:.2f}"
        
    def format_target(row):
        tp = row['Target_Price']
        rating = str(row.get('Rating', '')).upper()
        if "HOLD" in rating or "ENTER:" in rating:
            return f"${tp:.2f}"
        return ""
        
    view_df['Stop_Loss'] = df_scan.apply(format_stop, axis=1)
    view_df['Target_Price'] = df_scan.apply(format_target, axis=1)
        
    view_df = view_df.rename(columns={'Proxy_Content': f'Proxy_Content (Updated: {time_str})'})
    
    def highlight_dataframe(row):
        cols = [''] * len(row)
        
        # Color coding Rating
        rating_col = view_df.columns.get_loc('Rating')
        v = str(row['Rating']).upper()
        if "ENTER:" in v:
            cols[rating_col] = 'color: #00ff88; font-weight: bold;'
        elif "WATCH" in v or "HOLD" in v:
            if "NO PROXY" in v or "MISS PROXY" in v:
                cols[rating_col] = 'color: #ffb020; font-weight: bold;' # Amber
            else:
                cols[rating_col] = 'color: #FFD700; font-weight: bold;' # Gold
        elif "EXIT" in v or "AVOID" in v or "KILL" in v:
            cols[rating_col] = 'color: #ff4444; font-weight: bold;'
            
        # Color coding Wide Stop (Position Size Warning)
        stop_col = view_df.columns.get_loc('Stop_Loss')
        sl_str = str(row['Stop_Loss'])
        if "Trail" in sl_str:
            cols[stop_col] = 'color: #ffb020; font-weight: bold;' # Amber warning for tightening stop
        elif "(-" in sl_str:
            try:
                pct_val = float(sl_str.split("(-")[1].split("%")[0])
                if pct_val > 12.0:
                    cols[stop_col] = 'color: #ffb020; font-weight: bold;' # Amber
            except Exception:
                pass
            
        warn_col = view_df.columns.get_loc('Tactical_Warning')
        score_val = row.get('Score', 0)
        warning_str = str(row['Tactical_Warning'])
        
        if score_val < 90:
            cols[warn_col] = 'color: #555555; font-style: italic;' # Grey out
        elif "PARABOLIC" in warning_str:
            cols[warn_col] = 'color: #ff4444; font-weight: bold;' # Red tight
        elif "LINEAR TREND" in warning_str:
            cols[warn_col] = 'color: #00ff88; font-weight: bold;' # Green Linear
        elif "SUPER CYCLE" in warning_str:
            cols[warn_col] = 'color: #00ff88; font-weight: bold;'
            
        # Color coding Leverage
        if 'Leverage' in view_df.columns:
            veh_col = view_df.columns.get_loc('Leverage')
            veh_val = str(row.get('Leverage', ''))
            if "LEAP" in veh_val:
                cols[veh_col] = 'color: #DDAAFF; font-weight: bold; background-color: rgba(221,170,255,0.1);' # Purple 
            elif "Avoid" in veh_val:
                cols[veh_col] = 'color: #ffb020; font-weight: bold;' # Amber
                
        # Color coding Proxy Type and P_Value
        type_col = view_df.columns.get_loc('Proxy_Type')
        if "NO PROXY" in str(row['Proxy_Type']):
            cols[type_col] = 'color: #ff4444;'
        else:
            cols[type_col] = 'color: #88ccff;'
            
        if 'P_Value' in view_df.columns:
            pval_col = view_df.columns.get_loc('P_Value')
            cols[pval_col] = 'color: #aaa; font-style: italic;'
            
        # Color coding Proxy Signal (The Truth Table)
        sig_col = view_df.columns.get_loc('Proxy_Signal')
        sig = str(row['Proxy_Signal'])
        if sig == "COILED SPRING":
            cols[sig_col] = 'color: #00ff88; font-weight: bold; background-color: rgba(0,255,136,0.1);'
        elif sig == "CORRELATED":
            cols[sig_col] = 'color: #aaddaa;'
        elif sig == "DIVERGING":
            cols[sig_col] = 'color: #ffb020; font-weight: bold; background-color: rgba(255,176,32,0.1);' # Flashing Orange
        elif sig == "MISPRICED" or sig == "UNDERVALUED":
            cols[sig_col] = 'color: #ff4444; font-weight: bold;'
        elif sig == "CORRECTING":
            cols[sig_col] = 'color: #888888;'
            
        return cols
    
    st.dataframe(
        view_df.style.apply(highlight_dataframe, axis=1), 
        use_container_width=True,
        hide_index=True
    )

# ==========================================
# TAB 2: DATA HEALTH MONITOR
# ==========================================
with tab2:
    st.header("🏥 Data Health Monitor")

    # Move Data Health content here (was lines 870-901)
    health_pct = int(round(health_ratio * 100))
    badge_color = "#00cc66" if health_status == "HEALTHY" else "#ffb020"
    badge_background = "rgba(0,204,102,0.12)" if health_status == "HEALTHY" else "rgba(255,176,32,0.12)"
    st.markdown(
        f"""
        <div style="display:inline-flex; align-items:center; gap:8px; border:1px solid {badge_color}; border-radius:999px; padding:4px 10px; margin: 0 0 8px 0; background:{badge_background};">
            <span style="font-size:0.78rem; color:#888; text-transform:uppercase;">Data Health</span>
            <span style="font-size:0.82rem; font-weight:700; color:{badge_color};">{health_status}</span>
            <span style="font-size:0.78rem; color:#aaa;">Degraded: {health_pct}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    degraded_count = int(data_health.get("degraded_count", 0))
    total_signals = int(data_health.get("total_signals", 0))
    st.caption(f"Signals degraded: {degraded_count}/{total_signals}")

    signal_rows = []
    for signal in data_health.get("signals", []):
        signal_rows.append(
            {
                "Signal": str(signal.get("signal", "")),
                "Status": str(signal.get("status", "")),
                "Reason": str(signal.get("reason", "")),
                "Span": str(signal.get("span", "")),
            }
        )
    if signal_rows:
        st.dataframe(pd.DataFrame(signal_rows), hide_index=True, use_container_width=True)
    else:
        st.caption("No proxy signals available.")

# ==========================================
# TAB 3: DRIFT MONITOR (PROMOTED)
# ==========================================
with tab3:
    from views.drift_monitor_view import render_drift_monitor_view
    render_drift_monitor_view()

# ==========================================
# TAB 4: DAILY SCAN (CONFLUENCE)
# ==========================================
with tab4:
    st.subheader("Confluence Grid (Fundamental Resonance vs. Technical Extension)")
    
    lens_view = st.radio("Toggle Lens:", ["🌍 Macro View (Decluttered)", "🎯 Sniper View (High-Alpha Dispersion)"], horizontal=True)

    def get_plot_category(score, dist):
        if score == 100:
            if dist > 5.0: return "Wait (Extended)"
            elif dist >= -2.0: return "Strong Buy (Max Alpha)"
            else: return "Buy"
        elif score >= 90: return "Watch / Hold"
        return "Ignore"

    plot_records = []
    
    # 1. Process Core Sovereign Pool
    for _, row in df_scan[df_scan['Score'] > 0].iterrows():
        plot_records.append({
            "Ticker": row["Ticker"],
            "Score": row["Score"],
            "Delta_Demand": row.get("Delta_Demand", 0.0),
            "Delta_Margin": row.get("Delta_Margin", 0.0),
            "Tech_Support_Dist": row.get("Tech_Support_Dist", 0.0),
            "Support_Label": str(row.get("Support_Label", "N/A")),
            "Plot_Category": get_plot_category(row["Score"], row.get("Tech_Support_Dist", 0.0)),
            "Source": "Sovereign Pool"
        })

    # 2. Process Drone Intel
    if drone_finds:
        drone_tickers = [x['Ticker'] for x in drone_finds]
        drone_tech = get_prices_and_technicals(drone_tickers)
        for d in drone_finds:
            t = d["Ticker"]
            tData = drone_tech.get(t, {})
            price = tData.get("price", 0.0)
            sma50 = tData.get("sma50", 1.0)
            if price > 0 and sma50 > 0:
                dist_pct = ((price / sma50) - 1.0) * 100.0
                support_label = "50-SMA (Drone)"
            else:
                dist_pct = 0.0
                support_label = "N/A"
            score = d.get("Score", 0)
            dem = d.get("Delta_Demand", 0.0)
            mar = d.get("Delta_Margin", 0.0)
            if score > 0:
                plot_records.append({
                    "Ticker": t,
                    "Score": score,
                    "Delta_Demand": dem,
                    "Delta_Margin": mar,
                    "Tech_Support_Dist": dist_pct,
                    "Support_Label": support_label,
                    "Plot_Category": get_plot_category(score, dist_pct),
                    "Source": "Scout Drone"
                })

    if plot_records:
        combined_df = pd.DataFrame(plot_records)
        # Deduplicate to prevent double-plotting if Sovereign Pool overlaps with Drone Finds (e.g., MU, CIEN, SNDK)
        combined_df = combined_df.drop_duplicates(subset=['Ticker'], keep='first')
        
        if "Sniper" in lens_view:
            combined_df = combined_df.sort_values(['Score', 'Delta_Margin'], ascending=[False, False]).reset_index(drop=True)
            
            def calculate_plot_y_deterministic(df):
                """
                Calculate Y positions with deterministic jitter.

                Prevents label flicker across Streamlit reruns by using
                ticker hash + date seed for stable positioning.

                Returns:
                    display_y: List of Y positions
                    labels: List of ticker labels
                """
                import hashlib
                from datetime import datetime as dt

                display_y = []
                placed_points = []
                labels = []

                # Deterministic seed from date (stable within day)
                date_seed = dt.now().strftime("%Y-%m-%d")

                for _, r in df.iterrows():
                    ticker = r['Ticker']
                    base_y = r['Score']
                    fund_bonus = (r.get('Delta_Margin', 0) * 100) + (r.get('Delta_Demand', 0) * 20)
                    target_y = base_y + fund_bonus

                    x_pos = float(r['Tech_Support_Dist'])

                    # Deterministic jitter from ticker hash
                    ticker_hash = int(hashlib.md5(f"{ticker}{date_seed}".encode()).hexdigest(), 16)
                    x_jitter = (ticker_hash % 100) / 100.0 - 0.5  # Range: [-0.5, 0.5]

                    # Reduced collision detection (prevent tall stacking)
                    max_iter = 10  # Was 30
                    collision_threshold = 1.5
                    vertical_bump = 1.5

                    for _ in range(max_iter):
                        collision = False
                        for (px, py) in placed_points:
                            if abs(px - x_pos) < collision_threshold and abs(py - target_y) < collision_threshold:
                                collision = True
                                target_y += vertical_bump
                                x_pos += x_jitter * 0.3  # Horizontal spread on collision
                                break
                        if not collision:
                            break

                    placed_points.append((x_pos, target_y))
                    display_y.append(target_y)
                    labels.append(ticker)

                return display_y, labels

            display_ys, text_labels = calculate_plot_y_deterministic(combined_df)
            combined_df['Display_Score'] = display_ys
            combined_df['Text_Label'] = text_labels
            y_range = [80, max(120, combined_df['Display_Score'].max() + 5)]
            
        else:
            # Force Sovereign Pool (Source='Sovereign Pool') to be processed first for priority
            combined_df = combined_df.sort_values(['Source', 'Score'], ascending=[False, False]).reset_index(drop=True)
            
            # Sovereign Pool is the allow-list for text labels AND for the main scatter plot
            sovereign_tickers = set(SECTOR_MAP.keys())
            sovereign_plot_df = combined_df[combined_df['Ticker'].isin(sovereign_tickers)].copy()
            drone_plot_df = combined_df[~combined_df['Ticker'].isin(sovereign_tickers)].copy()

            def filter_labels_and_jitter(df):
                """Assign Display_Score (with collision avoidance) and Text_Label."""
                placed = []  # (x, y) placed so far
                display_ys = []
                labels = []
                
                # Quota per column in the crowded Y>90 band
                col_quota = {}
                
                for _, r in df.iterrows():
                    ticker = r['Ticker']
                    score = float(r['Score'])
                    x = float(r['Tech_Support_Dist'])
                    target_y = score
                    
                    # Collision avoidance: nudge vertically if overlapping
                    max_iter = 20
                    for _ in range(max_iter):
                        collision = False
                        for (px_val, py_val) in placed:
                            if abs(px_val - x) < 1.2 and abs(py_val - target_y) < 2.5:
                                collision = True
                                target_y += 2.5
                                break
                        if not collision:
                            break
                    
                    placed.append((x, target_y))
                    display_ys.append(target_y)
                    
                    # Label Logic
                    if score > 90:
                        col_key = round(x / 5.0) * 5
                        in_max_alpha = -2.0 <= x <= 5.0
                        quota = 3 if in_max_alpha else 1
                        if col_quota.get(col_key, 0) < quota:
                            labels.append(ticker)
                            col_quota[col_key] = col_quota.get(col_key, 0) + 1
                        else:
                            labels.append("")
                    else:
                        # Below 90: always label sovereign tickers
                        labels.append(ticker)
                
                return display_ys, labels

            display_ys, text_labels = filter_labels_and_jitter(sovereign_plot_df)
            sovereign_plot_df['Display_Score'] = display_ys
            sovereign_plot_df['Text_Label'] = text_labels
            drone_plot_df['Display_Score'] = drone_plot_df['Score']
            y_range = [15, 108]
        
        color_discrete_map = {
            "Strong Buy (Max Alpha)": "#00FFAA",
            "Buy": "#00cc66",
            "Wait (Extended)": "#FFB020",
            "Watch / Hold": "#FFD700",
            "Ignore": "#888888"
        }
        
        # Determine main plot dataframe based on view
        main_plot_df = sovereign_plot_df if "Macro" in lens_view else combined_df
        
        fig = px.scatter(
            main_plot_df,
            x="Tech_Support_Dist", 
            y="Display_Score", 
            text="Text_Label",
            color="Plot_Category",
            color_discrete_map=color_discrete_map,
            hover_data=["Ticker", "Score", "Source", "Support_Label"],
            labels={
                "Tech_Support_Dist": "Distance from Dynamic Support (%)",
                "Display_Score": "Fundamental Physics Score",
                "Plot_Category": "Action Status",
                "Support_Label": "Active Rail",
                "Source": "Intel Source"
            }
        )
        
        # Apply circle markers to main scatter traces FIRST (before adding any go.Scatter traces)
        for trace in fig.data:
            trace.update(
                textposition='top center',
                marker=dict(size=14, symbol="circle", line=dict(width=1, color='DarkSlateGrey'))
            )
        
        # Draw Max Alpha Zone
        fig.add_shape(
            type="rect",
            x0=-2, y0=90, x1=5, y1=102,
            line=dict(color="#00FFAA", width=2, dash="dash"),
            fillcolor="#00FFAA",
            opacity=0.15,
            layer="below"
        )
        fig.add_annotation(x=1.5, y=96, text="MAX ALPHA ZONE", showarrow=False, font=dict(color="#00FFAA", size=14))
        
        # Draw Extended Zone (Wait for Support)
        fig.add_shape(
            type="rect",
            x0=5, y0=90, x1=15, y1=102,
            line=dict(color="#FFB020", width=1, dash="dot"),
            fillcolor="#FFB020",
            opacity=0.05,
            layer="below"
        )
        fig.add_annotation(x=10, y=96, text="EXTENDED (WAIT)", showarrow=False, font=dict(color="#FFB020", size=12))
        

        
        # --- ETF RADAR + Drone Density dots (Macro View only) ---
        if "Macro" in lens_view:
            # Drone density dots (tiny, no text) so breadth is visible without noise
            if not drone_plot_df.empty:
                fig.add_trace(go.Scatter(
                    x=drone_plot_df["Tech_Support_Dist"],
                    y=drone_plot_df["Display_Score"],
                    mode="markers",
                    marker=dict(symbol="circle", size=6, color="rgba(100,100,100,0.5)"),
                    name="Drone Breadth",
                    hovertemplate="<b>%{customdata[0]}</b><br>Score: %{customdata[1]}<extra>Drone Find</extra>",
                    customdata=drone_plot_df[["Ticker", "Score"]].values
                ))

            # --- The Look-Through Engine ---
            def get_etf_fundamental_score(ticker):
                etf_map = {
                    'SMH': {'NVDA': 0.20, 'TSM': 0.15, 'AVGO': 0.10, 'AMD': 0.05},
                    'XLK': {'MSFT': 0.22, 'AAPL': 0.19, 'NVDA': 0.06},
                    'QQQ': {'MSFT': 0.09, 'AAPL': 0.09, 'NVDA': 0.08, 'META': 0.05, 'AMZN': 0.05},
                    'XBI': {'AMGN': 0.08, 'VRTX': 0.08, 'REGN': 0.07},
                    'XLE': {'XOM': 0.23, 'CVX': 0.16, 'COP': 0.08},
                }

                if ticker not in etf_map:
                    return 50

                holdings = etf_map[ticker]
                total_weight = 0
                weighted_score = 0
                score_dict = dict(zip(combined_df['Ticker'], combined_df['Score']))
                
                for holding, weight in holdings.items():
                    holding_score = score_dict.get(holding, 50) 
                    weighted_score += (holding_score * weight)
                    total_weight += weight
                    
                if total_weight > 0:
                    return weighted_score / total_weight
                return 50

            # ETF Radar — dynamically score based on technical resonance (proximity to dynamic support)
            ETF_RADAR = ["SMH", "XBI", "QQQ", "XLK", "XLE", "IWM"]
            try:
                etf_tech = get_prices_and_technicals(ETF_RADAR)
                etf_records = []
                for etf in ETF_RADAR:
                    tData = etf_tech.get(etf, {})
                    dist = tData.get("dist_pct", None)
                    if dist is not None:
                        # Technical Resonance: peaks at 95 when perfectly on support, degrades as it extends
                        etf_score = min(100, max(20, round(95 - abs(dist) * 2.5)))
                        
                        # Apply Look-Through Quality
                        qual_score = get_etf_fundamental_score(etf)
                        if qual_score >= 90:
                            marker_color = "#00FFAA" # Strong
                        elif qual_score >= 80:
                            marker_color = "#00cc66" # Good
                        elif qual_score >= 60:
                            marker_color = "#FFD700" # Watch
                        else:
                            marker_color = "#888888" # Grey/Poor
                            
                        etf_records.append({"ticker": etf, "x": dist, "y": etf_score, "color": marker_color, "quality": round(qual_score)})
                
                if etf_records:
                    fig.add_trace(go.Scatter(
                        x=[r["x"] for r in etf_records],
                        y=[r["y"] for r in etf_records],
                        mode="markers+text",
                        text=[r["ticker"] for r in etf_records],
                        textposition="bottom center",
                        marker=dict(symbol="square", size=12, color=[r["color"] for r in etf_records],
                                    line=dict(color="#aaaaaa", width=1)),
                        name="ETF Radar",
                        customdata=[[r["quality"]] for r in etf_records],
                        hovertemplate="<b>%{text}</b><br>Dist: %{x:.1f}%<br>Timing (Resonance): %{y}<br>Quality (Look-Through): %{customdata[0]}<extra>ETF Radar</extra>"
                    ))

            except Exception:
                pass
        # Clean up hover labels (skip ETF/Drone traces which have custom templates)
        for trace in fig.data:
            if trace.name not in ("ETF Radar", "Drone Breadth") and trace.hovertemplate:
                trace.hovertemplate = trace.hovertemplate.replace("Text_Label=", "").replace("Display_Score=", "")
            
        fig.update_layout(height=600, template="plotly_dark", yaxis=dict(range=y_range), xaxis=dict(range=[-8, 15]))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No viable assets currently scoring > 0 to plot on the Confluence Grid.")

def _render_legacy_backtest_table():
    """Render legacy static backtest table (fallback when parquet unavailable)."""
    st.markdown("### Historical Phase Reversal Evidence (Static)")
    backtest_data = {
        "Asset": ["CSCO (2000)", "QCOM (2000)", "NVDA (2021)"],
        "Lag (Months)": [2, 2, 2],
        "Max drawdown if Held (%)": [-75.0, -79.17, -63.64],
        "Strategy A (Left-Side Sell)": [40.0, 250.0, 66.67],
        "Strategy B (Right-Side 5% Stop)": [52.0, 470.0, 109.0],
        "Strategy C (Put Hedging)": [26.0, 215.0, 50.0]
    }
    bt_df = pd.DataFrame(backtest_data)

    st.dataframe(bt_df.style.format({
        "Max drawdown if Held (%)": "{:.2f}%",
        "Strategy A (Left-Side Sell)": "+{:.2f}%",
        "Strategy B (Right-Side 5% Stop)": "+{:.2f}%",
        "Strategy C (Put Hedging)": "+{:.2f}%"
    }), use_container_width=True, hide_index=True)

    bt_melted = bt_df.melt(
        id_vars="Asset",
        value_vars=["Strategy A (Left-Side Sell)", "Strategy B (Right-Side 5% Stop)", "Strategy C (Put Hedging)"],
        var_name="Strategy",
        value_name="ROI (%)"
    )

    fig_bar = px.bar(
        bt_melted,
        x="Asset",
        y="ROI (%)",
        color="Strategy",
        barmode="group",
        title="Exit Execution ROI Comparison (Historical Evidence)",
        color_discrete_sequence=["#555555", "#00ff88", "#ff4444"]
    )
    fig_bar.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig_bar, use_container_width=True)


# ==========================================
# TAB 5: BACKTEST LAB (Interactive Runner)
# ==========================================
with tab5:
    st.subheader("📈 Backtest Lab: Interactive Strategy Validation")
    st.markdown("Run backtests with PID tracking and live result display. "
                "Uses institutional-grade TRI data for accurate performance measurement.")

    # Check if parquet data available for interactive backtest
    if parquet_data_available and not prices_wide.empty and not returns_wide.empty:
        try:
            # Load macro features for backtest context
            macro_features = get_macro_features(prefer_tri=True)

            # Activate interactive backtest runner
            st.success("✅ **Institutional TRI Data Active** - Interactive backtest runner enabled")
            render_auto_backtest_view(prices_wide, returns_wide, macro_features)

        except Exception as e:
            st.error(f"⚠️ Backtest Lab activation failed: {type(e).__name__}: {e}")
            st.caption("Falling back to static backtest results...")

            # Fallback to static results
            _render_legacy_backtest_table()
    else:
        # Placeholder mode (parquet data not loaded)
        st.info("🔧 **Backtest Lab: Data Dependency Not Met**\n\n"
                "Interactive backtest runner requires historical TRI data from parquet files.\n\n"
                "**Current Status:** Parquet data unavailable (check sidebar for details).\n\n"
                "**Showing:** Legacy static backtest results below.")

        _render_legacy_backtest_table()

# ==========================================
# TAB 4: MODULAR STRATEGIES (V3.1 — Notion-Like Matrix)
# ==========================================

# --- Strategy Registry: Config-Driven Catalog ---
STRATEGY_REGISTRY = {
    "The Infinity Governor": {
        "type": "Risk Manager",
        "ticker_pool": "Score ≥ 90 (Super Cycle)",
        "entry": "Adaptive Governor: M × ATR trail",
        "exit": "Price < Dynamic Stop",
        "time_horizon": "Indefinite (kinetic trail)",
        "rotation_criteria": "Macro < 50 or C penalty",
        "rules": "Max 10 pos · Single ≤25%",
        "core_math": r"Stop\_Multiplier = 3.0 \times (1 + Bonus(R^2)) \times \frac{1}{1 + Penalty(\mathcal{C})}",
        "mask_fn": lambda df, ms: (df["Score"] >= 90) & (df["Current_Price"] > df["Stop_Loss"]),
        "backtest": {"cagr": None, "max_dd": None, "script": "rule_100_backtest_decades.py", "sufficient": True},
    },
    "The Derivatives Trinity": {
        "type": "Entry Filter",
        "ticker_pool": "Score 100 (Flawless only)",
        "entry": "80Δ LEAP: Macro≥80, C≤1.5",
        "exit": "LEAP→Spot on C breach",
        "time_horizon": "6–12mo LEAP cycle",
        "rotation_criteria": "C > 1.5 or Macro < 80",
        "rules": "LEAP alloc ≤15% · Sector ≤60%",
        "core_math": r"Command = f(\text{Score} = 100,\ \mathcal{C} \le 1.5,\ \text{Macro} \ge 80) \rightarrow 80\Delta\ \text{LEAP}",
        "mask_fn": lambda df, ms: (df["Score"] == 100) & (df["Convexity"] <= 1.5) & (ms >= 80),
        "backtest": {"cagr": None, "max_dd": None, "script": "derivative_backtest.py", "sufficient": True},
    },
    "Empirical Stink Bid": {
        "type": "Entry Filter",
        "ticker_pool": "Sovereign Pool (flush-adj)",
        "entry": "Support×(1−(Flush−Prem))",
        "exit": "Entry − 3.0×ATR",
        "time_horizon": "Day Limit (no GTC)",
        "rotation_criteria": "Wick fill or support broken",
        "rules": "Day limit only · No GTC",
        "core_math": r"P_{entry} = \text{Support} \times (1 - (\text{Max\_Flush} - \text{Quality\_Premium}))",
        "mask_fn": lambda df, ms: (df["Current_Price"] <= df["Entry_Price"]) & (df["Entry_Price"] > 0),
        "backtest": {"cagr": None, "max_dd": None, "script": "smart_entry_backtest.py", "sufficient": True},
    },
    "Rule of 100": {
        "type": "Entry Filter",
        "ticker_pool": "Global (all sectors)",
        "entry": "All 4 Quad vectors firing",
        "exit": "Any quad flips → Score<100",
        "time_horizon": "Full Super Cycle",
        "rotation_criteria": "Score < 100",
        "rules": "Max 10 pos · Sector ≤60%",
        "core_math": r"\text{IF}\ (\Delta D > 0) \land (\Delta S \ge 0 \lor \Delta P > 0.5\%) \land (\Delta P > 0) \land (\Delta M > 0)",
        "mask_fn": lambda df, ms: df["Score"] == 100,
        "backtest": {"cagr": "+51.6%", "max_dd": "-22.4%", "script": "rule_100_backtest_decades.py", "sufficient": True},
    },
    "High Margin Gate": {
        "type": "Entry Filter",
        "ticker_pool": "Score ≥ 90, ΔM > 0",
        "entry": "Score≥90 ∧ ΔMargin>0",
        "exit": "ΔMargin flips negative",
        "time_horizon": "Quarterly review",
        "rotation_criteria": "ΔMargin ≤ 0",
        "rules": "Single ≤25% · Quarterly rebal",
        "core_math": r"\text{Score} \ge 90 \land \Delta\text{Margin} > 0",
        "mask_fn": lambda df, ms: (df["Score"] >= 90) & (df["Delta_Margin"].fillna(0) > 0 if "Delta_Margin" in df.columns else True),
        "backtest": {"cagr": None, "max_dd": None, "script": None, "sufficient": False},
    },
}

with tab6:
    st.header("🧩 Modular Strategies Matrix")
    st.markdown("Click a strategy row to view its physics. Edit below. All rows filter with implicit AND.")

    # Cache formula strings only (not st.latex renders)
    @st.cache_data
    def get_strategy_formulas() -> dict[str, str]:
        """Cache formula strings from STRATEGY_REGISTRY."""
        return {name: strat["core_math"] for name, strat in STRATEGY_REGISTRY.items()}

    # Load once per session
    if "formulas_loaded" not in st.session_state:
        st.session_state.formula_cache = get_strategy_formulas()
        st.session_state.formulas_loaded = True

    # --- Version guard: force rebuild on schema or release digest change ---
    _V3_VERSION = "3.9"
    _V3_CACHE_VERSION = _release_bound_cache_version(_V3_VERSION)
    ALL_RULES = list({s.get("rules", "") for s in STRATEGY_REGISTRY.values() if s.get("rules")})
    UNIVERSES = ["Global (All Sectors)", "S&P 500", "US Tech Sector", "Sovereign Pool", "LEAP Eligible"]
    # Map ticker_pool descriptions to Universe options
    _POOL_TO_UNIVERSE = {
        "Score \u2265 90 (Super Cycle)": "Sovereign Pool",
        "Score 100 (Flawless only)": "Sovereign Pool",
        "Sovereign Pool (flush-adj)": "Sovereign Pool",
        "Global (all sectors)": "Global (All Sectors)",
        "Score \u2265 90 (2nd tier)": "Sovereign Pool",
    }
    if st.session_state.get("_v3_ver") != _V3_CACHE_VERSION:
        st.session_state.pop("strat_matrix_v3", None)
        st.session_state["_v3_ver"] = _V3_CACHE_VERSION

    # --- Phase 2: Load cache + PID probe ---
    bt_cache = read_bt_cache()
    running, running_name, bt_start_ts = is_backtest_running()

    # --- 1. Build DataFrame from registry ---
    if 'strat_matrix_v3' not in st.session_state:
        rows = []
        first_pending_assigned = False
        for name, s in STRATEGY_REGISTRY.items():
            bt_reg = s.get("backtest", {})
            cached = bt_cache.get(name, {})
            cagr_raw = cached.get("cagr") or bt_reg.get("cagr")
            dd_raw = cached.get("max_dd") or bt_reg.get("max_dd")
            if isinstance(cagr_raw, (int, float)) and cagr_raw != 0:
                cagr_val = f"+{cagr_raw*100:.1f}%" if cagr_raw > 0 else f"{cagr_raw*100:.1f}%"
            elif isinstance(cagr_raw, str):
                cagr_val = cagr_raw
            else:
                cagr_val = ""
            if isinstance(dd_raw, (int, float)) and dd_raw != 0:
                dd_val = f"{dd_raw*100:.1f}%"
            elif isinstance(dd_raw, str):
                dd_val = dd_raw
            else:
                dd_val = ""
            has_results = bool(cagr_raw)
            if running and running_name == name:
                bt_status = "Running..."
            elif has_results:
                bt_status = "Done"
            elif bt_reg.get("sufficient"):
                if not first_pending_assigned:
                    bt_status = "Next"
                    first_pending_assigned = True
                else:
                    bt_status = "Pending"
            else:
                bt_status = "Insufficient"
            rows.append({
                "Strategy": name,
                "Universe": _POOL_TO_UNIVERSE.get(s.get("ticker_pool", ""), "Global (All Sectors)"),
                "Entry": s["entry"], "Exit": s["exit"],
                "Rules": s.get("rules", ""),
                "CAGR": cagr_val, "Max DD": dd_val, "BT": bt_status,
                "Core Math": s["core_math"],
            })
        st.session_state.strat_matrix_v3 = pd.DataFrame(rows)

    base_df = st.session_state.strat_matrix_v3
    display_cols = ["Strategy", "Universe", "Entry", "Exit", "Rules", "CAGR", "Max DD", "BT"]

    # --- Run Next Backtest: fragment-based polling (no fog) ---
    @st.fragment(run_every="5s" if running else None)
    def _bt_control_fragment():
        _running, _name, _start_ts = is_backtest_running()
        if _running:
            # Elapsed time + progress bar
            import time as _time
            elapsed = _time.time() - _start_ts if _start_ts > 0 else 0
            est_duration = 120  # ~2 min typical
            pct = min(elapsed / est_duration, 0.95)  # cap at 95% until done
            mins, secs = divmod(int(elapsed), 60)
            st.info(f"🔄 Running: **{_name}** — {mins}m {secs}s elapsed")
            st.progress(pct, text=f"{pct*100:.0f}% (est. ~{est_duration}s)")
            st.session_state["_bt_was_running"] = True
        else:
            # Backtest just finished → one full rerun to refresh table
            if st.session_state.get("_bt_was_running"):
                st.session_state["_bt_was_running"] = False
                st.session_state.pop("strat_matrix_v3", None)
                st.rerun()
            if st.button("▶️ Run Next Backtest", key="run_next_bt", type="primary"):
                _bt_cache = read_bt_cache()
                next_name = None
                next_script = None
                for sname, sdata in STRATEGY_REGISTRY.items():
                    bt_info = sdata.get("backtest", {})
                    cached = _bt_cache.get(sname, {})
                    if not cached.get("cagr") and not bt_info.get("cagr") and bt_info.get("sufficient") and bt_info.get("script"):
                        next_name = sname
                        next_script = f"scripts/{bt_info['script']}"
                        break
                if next_name and next_script:
                    pid = spawn_backtest(next_script, next_name)
                    st.session_state["_bt_was_running"] = True
                    st.session_state.pop("strat_matrix_v3", None)
                    st.rerun()
                else:
                    st.warning("No pending backtests to run.")

    _bt_control_fragment()

    # --- 2. Display table: st.dataframe with row selection ---
    event = st.dataframe(
        base_df[display_cols],
        column_config={
            "Strategy": st.column_config.TextColumn("Strategy", width="medium"),
            "Universe": st.column_config.TextColumn("\ud83c\udf10 Universe", width="small"),
            "Entry": st.column_config.TextColumn("Entry"),
            "Exit": st.column_config.TextColumn("Exit"),
            "Rules": st.column_config.TextColumn("Rules"),
            "CAGR": st.column_config.TextColumn("CAGR", width="small"),
            "Max DD": st.column_config.TextColumn("Max DD", width="small"),
            "BT": st.column_config.TextColumn("BT", width="small"),
        },
        selection_mode=["single-row", "single-column"],
        on_select="rerun",
        hide_index=True,
        use_container_width=True,
        key="strat_display_v39",
    )

    # --- 2a. Add / Remove Row Buttons ---
    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 4])
    with btn_c1:
        if st.button("➕ Add Strategy", key="add_strat"):
            default_name = list(STRATEGY_REGISTRY.keys())[0]
            s = STRATEGY_REGISTRY[default_name]
            new_row = pd.DataFrame([{
                "Strategy": default_name,
                "Universe": _POOL_TO_UNIVERSE.get(s.get("ticker_pool", ""), "Global (All Sectors)"),
                "Entry": s["entry"], "Exit": s["exit"],
                "Rules": s.get("rules", ""),
                "CAGR": "", "Max DD": "", "BT": "Insufficient",
                "Core Math": s["core_math"],
            }])
            st.session_state.strat_matrix_v3 = pd.concat(
                [base_df, new_row], ignore_index=True
            )
            st.rerun()
    with btn_c2:
        selected_rows = event.selection.rows if hasattr(event, 'selection') and event.selection else []
        if selected_rows and len(base_df) > 0:
            if st.button("🗑 Remove Selected", key="rm_strat"):
                st.session_state.strat_matrix_v3 = base_df.drop(
                    index=selected_rows[0]
                ).reset_index(drop=True)
                st.rerun()

    # --- 3. Contextual Panel: Multi-level formula display ---
    sel_rows = event.selection.rows if hasattr(event, 'selection') and event.selection else []
    sel_cols = event.selection.columns if hasattr(event, 'selection') and event.selection else []
    # Edge case: column-only click without row → ignore
    if sel_rows and sel_rows[0] < len(base_df):
        sel_idx = sel_rows[0]
        sel_strat = base_df.at[sel_idx, "Strategy"]
        s = STRATEGY_REGISTRY.get(sel_strat)

        if s:
            icon = "🛡️" if s["type"] == "Risk Manager" else "🎯"
            st.markdown(f"### 📐 {icon} {sel_strat} — _{s['ticker_pool']}_")

            # Determine which column was clicked (if any)
            FORMULA_COLS = {"Strategy", "Entry", "Exit", "Rules"}
            clicked_col = sel_cols[0] if sel_cols and sel_cols[0] in FORMULA_COLS else None
            show_all = clicked_col is None  # No formula column clicked → show all

            if show_all or clicked_col == "Strategy":
                st.markdown("**🎯 Strategy — Core Math:**")
                formula = st.session_state.formula_cache.get(sel_strat, "")
                if formula:
                    st.latex(formula)  # Render fresh (not cached)
                else:
                    st.caption("No formula available")
            if show_all or clicked_col == "Entry":
                st.markdown(f"**📥 Entry:** `{s['entry']}`")
            if show_all or clicked_col == "Exit":
                st.markdown(f"**📤 Exit:** `{s['exit']}`")
            if show_all or clicked_col == "Rules":
                st.markdown(f"**📏 Rules:** `{s.get('rules', '')}`")

            # --- Inline Edit Controls ---
            st.caption("✏️ **Edit selected row:**")
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                new_strat = st.selectbox(
                    "Strategy", list(STRATEGY_REGISTRY.keys()),
                    index=list(STRATEGY_REGISTRY.keys()).index(sel_strat),
                    key=f"edit_strat_{sel_idx}",
                )
            with ec2:
                current_universe = base_df.at[sel_idx, "Universe"]
                uni_idx = UNIVERSES.index(current_universe) if current_universe in UNIVERSES else 0
                new_universe = st.selectbox(
                    "🌐 Universe", UNIVERSES,
                    index=uni_idx,
                    key=f"edit_uni_{sel_idx}",
                )
            with ec3:
                current_rules = base_df.at[sel_idx, "Rules"]
                rules_idx = ALL_RULES.index(current_rules) if current_rules in ALL_RULES else 0
                new_rules = st.selectbox(
                    "Rules", ALL_RULES,
                    index=rules_idx,
                    key=f"edit_rules_{sel_idx}",
                )

            # Apply edits if changed
            changed = False
            if new_strat != sel_strat:
                ns = STRATEGY_REGISTRY.get(new_strat, {})
                if ns:
                    bt_reg = ns.get("backtest", {})
                    cached = bt_cache.get(new_strat, {})
                    cagr_raw = cached.get("cagr") or bt_reg.get("cagr")
                    dd_raw = cached.get("max_dd") or bt_reg.get("max_dd")
                    base_df.at[sel_idx, "Strategy"] = new_strat
                    base_df.at[sel_idx, "Entry"] = ns.get("entry", "")
                    base_df.at[sel_idx, "Exit"] = ns.get("exit", "")
                    base_df.at[sel_idx, "Rules"] = ns.get("rules", "")
                    base_df.at[sel_idx, "Core Math"] = ns.get("core_math", "")
                    base_df.at[sel_idx, "Universe"] = _POOL_TO_UNIVERSE.get(ns.get("ticker_pool", ""), "Global (All Sectors)")
                    base_df.at[sel_idx, "CAGR"] = f"+{cagr_raw*100:.1f}%" if isinstance(cagr_raw, (int, float)) and cagr_raw != 0 else ""
                    base_df.at[sel_idx, "Max DD"] = f"{dd_raw*100:.1f}%" if isinstance(dd_raw, (int, float)) and dd_raw != 0 else ""
                    changed = True
            if new_universe != current_universe:
                base_df.at[sel_idx, "Universe"] = new_universe
                changed = True
            if new_rules != current_rules:
                base_df.at[sel_idx, "Rules"] = new_rules
                changed = True
            if changed:
                st.rerun()

    elif len(base_df) == 0:
        st.info("No logic blocks in matrix. Engine is in observation mode.")
    else:
        st.caption("👆 Click a row to view all formulas, or click a specific column cell to focus.")


# ==========================================
# TAB 7: PORTFOLIO BUILDER (Optional PM Tools)
# ==========================================
with tab7:
    st.subheader("💼 Portfolio Builder: Mean-Variance Optimization")
    st.markdown("Construct optimal portfolios with sector constraints and regime-aware allocation.")

    # Check if parquet data + fundamentals available
    if parquet_data_available and fundamentals_wide is not None:
        try:
            # Extract selected tickers from current scan results
            selected_tickers = list(df_scan["Ticker"].values) if 'Ticker' in df_scan.columns else []

            st.success("✅ **Fundamentals Data Active** - Portfolio Builder enabled")

            # Activate Portfolio Builder
            render_optimizer_view(
                prices_wide=prices_wide,
                ticker_map=ticker_map_parquet,
                sector_map=sector_map_parquet,
                selected_tickers=selected_tickers[:20],  # Limit to top 20 for performance
            )

        except Exception as e:
            st.error(f"⚠️ Portfolio Builder activation failed: {type(e).__name__}: {e}")
            st.caption("Falling back to placeholder mode...")
            _render_portfolio_builder_placeholder()

    else:
        # Placeholder mode (fundamentals not available)
        _render_portfolio_builder_placeholder()


def _render_portfolio_builder_placeholder():
    """Render Portfolio Builder placeholder when fundamentals unavailable."""
    st.info("🔧 **Portfolio Builder: Data Dependency Not Met**\n\n"
            "Portfolio optimization requires fundamentals data (sector classifications, "
            "market cap, financial ratios). \n\n"
            "**Current Status:** "
            + ("Parquet data loaded but fundamentals missing. " if parquet_data_available else "Parquet data unavailable. ")
            + "Run fundamentals updater to enable.\n\n"
            "**Alternative:** Use Tab 4 (Modular Strategies) for signal-based allocation.")

    # Placeholder preview
    st.divider()
    st.caption("**Preview: Portfolio Builder Features (Available When Fundamentals Loaded)**")

    preview_cols = st.columns(3)
    with preview_cols[0]:
        st.markdown("**📊 Mean-Variance Optimization**")
        st.caption("- Efficient frontier calculation\n- Max Sharpe / Min Vol portfolios\n- Custom risk tolerance slider")

    with preview_cols[1]:
        st.markdown("**🎯 Constraint Management**")
        st.caption("- Sector exposure limits\n- Position size caps\n- Long-only / long-short toggle")

    with preview_cols[2]:
        st.markdown("**🧬 Regime Integration**")
        st.caption("- Auto-scale exposure by FR-041 state\n- Defensive tilt in RED regime\n- Leverage boost in GREEN regime")



    # --- 5. Combined Execution Logic ---
    st.divider()
    st.subheader("⚙️ Combined Execution Logic")

    if len(base_df) == 0:
        st.warning("No logic blocks in matrix. Engine is currently in observation mode.")
        df_scan["Sovereign_Command"] = False
    else:
        names = list(base_df["Strategy"].values)

        # Build AND-chained logic string
        logic_str = " **AND** ".join(f"({n})" for n in names)
        st.markdown(f"**EXECUTE IF:** {logic_str}")

        # AND compounding warning
        if len(names) >= 3:
            st.warning("⚠️ Compounding 3+ filters with implicit **AND** may return an empty matrix.")

        # --- 6. Vectorized Signal Compiler (implicit AND) ---
        macro_score = macro["score"] if macro else 50
        try:
            masks = []
            for _, row in base_df.iterrows():
                s = STRATEGY_REGISTRY.get(row["Strategy"])
                if s:
                    masks.append(s["mask_fn"](df_scan, macro_score))
            if masks:
                result = masks[0]
                for i in range(1, len(masks)):
                    result = result & masks[i]
                df_scan["Sovereign_Command"] = result
            else:
                df_scan["Sovereign_Command"] = False
        except Exception as e:
            st.error(f"Signal compiler error: {e}")
            df_scan["Sovereign_Command"] = False

        # --- 7. Qualifying Tickers Readout ---
        st.divider()
        st.subheader("🎯 Qualifying Tickers")
        qualifying = df_scan[df_scan.get("Sovereign_Command", pd.Series(False, index=df_scan.index)) == True]

        if qualifying.empty:
            st.info("No tickers qualify under the current filter combination. Matrix is empty.")
        else:
            st.success(f"**{len(qualifying)}** ticker(s) pass the combined gate.")
            qual_cols = ["Ticker", "Score", "Rating", "Current_Price"]
            for opt_col in ["Convexity", "Tech_Support_Dist", "Multiplier"]:
                if opt_col in qualifying.columns:
                    qual_cols.append(opt_col)
            qual_view = qualifying[qual_cols].copy()
            qual_view["Current_Price"] = qual_view["Current_Price"].map("${:.2f}".format)
            st.dataframe(qual_view, use_container_width=True, hide_index=True)

