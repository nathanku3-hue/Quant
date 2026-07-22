import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import sys
import json
import hashlib
import subprocess
import datetime
import atexit
from pathlib import Path
from dataclasses import dataclass, field, replace
from functools import reduce
from filelock import FileLock
from core.release_metadata import build_release_cache_fingerprint
from core.dashboard_control_plane import derive_hf_proxy_data_health
from core.dashboard_control_plane import ensure_payload_data_health
from core.data_orchestrator import build_unified_data_cache_signature
from core.data_orchestrator import build_batched_pit_input_loader
from core.data_orchestrator import build_benchmark_equity_from_prices
from core.data_orchestrator import build_price_endpoint_freshness
from core.data_orchestrator import clean_price_frame
from core.data_orchestrator import filter_price_frame_to_fresh_columns
from core.data_orchestrator import get_macro_features
from core.data_orchestrator import load_batched_pit_replay_data
from core.data_orchestrator import load_strategy_replay_inputs
from core.data_orchestrator import load_unified_data
from core.data_orchestrator import repair_stale_price_endpoints_with_live_overlay
from views.regime_view import render_regime_banner_from_macro
from views.auto_backtest_view import render_auto_backtest_view
from views.optimizer_view import (
    PORTFOLIO_ALLOCATION_STATE_KEY,
    PORTFOLIO_CURRENT_HOLD_REPLAY_KEY,
    PORTFOLIO_REPLAY_SELECTION_KEY,
    PortfolioReplaySelection,
    build_portfolio_replay_selection_signature,
    portfolio_replay_asset_identity,
    render_optimizer_view,
)
from views.drift_monitor_view import render_drift_monitor_view

from views.page_registry import build_dashboard_navigation
from views.page_registry import DISCOVERY_PAGE_TITLE
from views.page_registry import PORTFOLIO_PAGE_TITLE
from views.page_registry import STRATEGY_PAGE_TITLE
from views.discovery_view import render_discovery_page
from views.gv_fs0_portfolio_adapter import (
    GvFs0PresentationError,
    render_e0b_dv1_surface,
    render_gv_fs0_current_decision,
    render_v2_b0_surface,
)
from views.pead_validation_evidence import render_pead_validation_evidence
from views.strategy_view import render_strategy_page
from strategies.portfolio_universe import (
    DEFAULT_OPTIMIZER_UNIVERSE_POLICY,
    build_optimizer_universe,
    load_current_position_memory,
    map_permno_weights_to_ticker_weights,
)
from strategies.scanner import build_price_technicals
from strategies.scanner import calculate_macro_score
from strategies.scanner import classify_breadth_status
from strategies.scanner import enrich_scan_frame
from strategies.strategy_replay import REPLAY_CONTEXT_COLUMNS
from strategies.strategy_replay import normalize_context_frame_for_replay
from core.drift_alert_manager import DriftAlertManager
from core.drift_detector import DriftDetector
from core.dashboard_escalation import initialize_escalation_manager
from utils.process import pid_is_running
# st_autorefresh removed in V3.10 — replaced by @st.fragment(run_every=)

# --- Phase 2: Backtest Cache + PID Infrastructure ---
BT_CACHE_PATH = Path("data/backtest_results.json")
BT_LOCK_PATH = str(BT_CACHE_PATH) + ".lock"
BT_PID_FILE = Path("data/.backtest_pid")
RULE100_SOFTMAX_V1_HISTORY_PATH = Path("data/processed/rule100_softmax_v1_history.csv")
LIFECYCLE_BUY_SELL_LOG_PATH = Path("data/portfolio_lifecycle_buy_sell_log.jsonl")
SELECTED_METHOD_REPLAY_CACHE_DIR = Path("data/runtime_cache/strategy_replay")
DASHBOARD_REPLAY_ARTIFACT_MAX_ROWS = 250_000
DASHBOARD_REPLAY_ARTIFACT_MAX_DATES = 3_000
STRATEGY_REPLAY_CONTEXT_KEY = "strategy_replay_context"
STRATEGY_REPLAY_LATEST_WEIGHTS_KEY = "strategy_replay_latest_weights"
STRATEGY_REPLAY_CACHE_SIGNATURE_KEY = "strategy_replay_cache_signature"
STRATEGY_REPLAY_YTD_CONTEXT_KEY = "_replay_context_for_ytd"
PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY = "portfolio_stale_endpoint_repair"
PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY = "portfolio_stale_endpoint_repair_frame"


def _stable_json_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DashboardReplayContext:
    method: str
    max_weight: float
    controls: dict
    cache_signature: dict
    source_label: str
    replay_df: pd.DataFrame
    latest_snapshot: pd.DataFrame
    event_annotations: pd.DataFrame
    buy_sell_decisions: pd.DataFrame
    replay_dates: list[str]
    sampling: str  # "daily" or "weekly"
    status: str  # "building", "ready", "stale", "failed", "input_unavailable"
    reason: str
    source_mode: str = "transitional_build"  # "saved_artifact" | "transitional_build" | "unavailable"
    input_coverage_start: str = ""  # from run_metadata; empty means unknown
    run_id: str = ""
    source_id: str = ""
    method_id: str = ""
    date_window: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class DashboardReplayRequest:
    method: str
    max_weight: float
    controls: dict
    cache_signature: dict
    replay_assets: tuple[object, ...]
    replay_dates: list[str]
    sampling: str
    data_signature: tuple
    full_history_start: str
    include_replay: bool
    allocation_assets: tuple[object, ...] = ()


@dataclass(frozen=True)
class DashboardReplayArtifactRead:
    status: str
    reason: str
    bundle: object | None = None
    artifact_path: Path | None = None
    manifest_path: Path | None = None
    manifest: dict | None = None
    frame: pd.DataFrame | None = None


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

        if not pid_is_running(pid):
            BT_PID_FILE.unlink(missing_ok=True)
            return False, "", 0.0
        return True, name, start_ts
    except (ProcessLookupError, ValueError, OSError):
        BT_PID_FILE.unlink(missing_ok=True)
        return False, "", 0.0

def spawn_backtest(script_path: str, strategy_name: str) -> int:
    """Spawn backtest subprocess with single-flight guard.
    Uses CREATE_NEW_PROCESS_GROUP to prevent child KeyboardInterrupt
    from propagating to the parent Streamlit process on Windows.
    """
    # Fail closed on a live PID file. A stale file can point at a reused PID, so
    # the dashboard must never terminate a process it cannot prove it owns.
    if BT_PID_FILE.exists():
        running, running_name, _start_ts = is_backtest_running()
        if running:
            label = f" for {running_name}" if running_name else ""
            raise RuntimeError(f"Backtest already running{label}; refusing to spawn another.")
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

st.set_page_config(page_title="Terminal Zero GodView", layout="wide", page_icon="🎯")

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


def _load_rule100_softmax_v1_history(path: Path | None = None) -> pd.DataFrame:
    """Load the additive v1 sizing history artifact for lifecycle audit display."""

    history_path = path or RULE100_SOFTMAX_V1_HISTORY_PATH
    if not history_path.exists() or history_path.stat().st_size == 0:
        return pd.DataFrame()
    history = pd.read_csv(history_path)
    if history.empty:
        return history
    history["date"] = pd.to_datetime(history.get("date"), errors="coerce")
    if "ticker" in history.columns:
        history["ticker"] = history["ticker"].astype(str).str.upper().str.strip()
    return history


def _ensure_rule100_softmax_v1_history() -> pd.DataFrame:
    """Load history, building the additive artifact on a local miss."""

    try:
        history = _load_rule100_softmax_v1_history()
    except Exception:
        history = pd.DataFrame()
    if not history.empty:
        return history
    try:
        from scripts.rule100_softmax_v1_audit import write_rule100_softmax_v1_history

        write_rule100_softmax_v1_history(output_path=RULE100_SOFTMAX_V1_HISTORY_PATH)
        return _load_rule100_softmax_v1_history()
    except Exception:
        return pd.DataFrame()


def _merge_rule100_softmax_v1_history(df_events: pd.DataFrame) -> pd.DataFrame:
    """Attach PIT v1 target weights without mutating lifecycle event weights."""

    if not isinstance(df_events, pd.DataFrame) or df_events.empty:
        return df_events
    out = df_events.copy()
    try:
        history = _load_rule100_softmax_v1_history()
    except Exception:
        history = pd.DataFrame()
    out["rule100_softmax_v1_target_weight"] = pd.NA
    out["rule100_softmax_v1_cash_residual"] = pd.NA
    out["rule100_softmax_v1_eligibility"] = ""
    if history.empty:
        history = _ensure_rule100_softmax_v1_history()
        if history.empty:
            return out

    key_frame = out[["date", "ticker"]].copy()
    key_frame["_event_row"] = out.index
    key_frame["date_key"] = pd.to_datetime(key_frame["date"], errors="coerce").dt.normalize()
    key_frame["ticker_key"] = key_frame["ticker"].astype(str).str.upper().str.strip()

    hist_cols = [
        "date",
        "ticker",
        "softmax_v1_target_weight",
        "softmax_v1_cash_residual",
        "eligibility_reason",
    ]
    missing = [col for col in hist_cols if col not in history.columns]
    if missing:
        return out
    hist = history[hist_cols].copy()
    hist["date_key"] = pd.to_datetime(hist["date"], errors="coerce").dt.normalize()
    hist["ticker_key"] = hist["ticker"].astype(str).str.upper().str.strip()
    hist = (
        hist.dropna(subset=["date_key"])
        .sort_values(["date_key", "ticker_key"], kind="mergesort")
        .drop_duplicates(["date_key", "ticker_key"], keep="last")
    )
    merged = key_frame.merge(
        hist[[
            "date_key",
            "ticker_key",
            "softmax_v1_target_weight",
            "softmax_v1_cash_residual",
            "eligibility_reason",
        ]],
        on=["date_key", "ticker_key"],
        how="left",
    ).set_index("_event_row")
    out.loc[merged.index, "rule100_softmax_v1_target_weight"] = merged["softmax_v1_target_weight"]
    out.loc[merged.index, "rule100_softmax_v1_cash_residual"] = merged["softmax_v1_cash_residual"]
    out.loc[merged.index, "rule100_softmax_v1_eligibility"] = merged["eligibility_reason"].fillna("")
    return out


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
        df = yf.download(["^TNX", "VWEHX", "VFISX"], period="2y", progress=False)["Close"]
        return calculate_macro_score(df)
    except Exception:
        return None


@st.cache_data(ttl=3600*4) # cache for 4 hours
def get_breadth_status():
    """
    Detects Internal Rot (RSP vs SPY Divergence).
    Returns: status_label, status_color
    """
    try:
        data = yf.download(["RSP", "SPY"], period="6mo", progress=False)["Close"]
        return classify_breadth_status(data)
    except Exception:
        return "UNKNOWN (Error)", "#888"


@st.cache_resource(show_spinner=False)
def _load_unified_data_cached(
    *,
    mode: str,
    top_n: int,
    start_year: int,
    universe_mode: str,
    asof_date,
    processed_dir: str,
    static_dir: str,
    data_signature: tuple[tuple[str, int | None, int | None], ...],
):
    # data_signature is part of the Streamlit cache key and invalidates on parquet updates.
    return load_unified_data(
        mode=mode,
        top_n=top_n,
        start_year=start_year,
        universe_mode=universe_mode,
        asof_date=asof_date,
        processed_dir=processed_dir,
        static_dir=static_dir,
    )


@st.cache_resource(show_spinner=False)
def _price_endpoint_freshness_cached(
    _prices: pd.DataFrame,
    matrix_signature: tuple,
):
    # matrix_signature keeps this endpoint snapshot tied to the loaded parquet package and loader shape.
    return build_price_endpoint_freshness(_prices)


def get_prices_and_technicals(tickers):
    if not tickers:
        return {}
    try:
        hist_all = yf.download(tickers, period="1y", progress=False)
        return build_price_technicals(hist_all, tickers)
    except Exception:
        return {
            t: {"price": 0.0, "ema21": 0.0, "sma50": 0.0, "sma200": 0.0, "atr": 0.0, "convexity": 1.0}
            for t in tickers
        }

def run_and_save_scan():
    with st.spinner("Booting Sensors & Firing Physics Engine..."):
        proxy_data = fetch_auto_data()
        data_health = derive_hf_proxy_data_health(proxy_data)
        df_scan = run_alpha_sovereign_scan(manual_inputs=proxy_data)
        
        if df_scan is not None and not df_scan.empty:
            technicals = get_prices_and_technicals(df_scan['Ticker'].tolist())
            macro = fetch_macro_score()
            df_scan = enrich_scan_frame(
                df_scan,
                technicals=technicals,
                sector_map=SECTOR_MAP,
                proxy_db=PROXY_DB,
                proxy_data=proxy_data,
                macro=macro,
            )

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
price_endpoint_freshness = None

try:
    # Attempt to load historical parquet data
    unified_data_signature = build_unified_data_cache_signature(
        processed_dir="./data/processed",
        static_dir="./data/static",
    )
    unified_package = _load_unified_data_cached(
        mode="historical",
        top_n=2000,
        start_year=2000,
        universe_mode="top_liquid",
        asof_date=None,
        processed_dir="./data/processed",
        static_dir="./data/static",
        data_signature=unified_data_signature,
    )

    prices_wide = unified_package.prices
    returns_wide = unified_package.returns
    ticker_map_parquet = unified_package.ticker_map
    sector_map_parquet = unified_package.sector_map
    fundamentals_wide = unified_package.fundamentals

    # Check if data loaded successfully
    if not prices_wide.empty and not returns_wide.empty:
        price_matrix_signature = (
            unified_data_signature,
            "historical",
            2000,
            2000,
            "top_liquid",
            None,
            tuple(prices_wide.shape),
        )
        price_endpoint_freshness = _price_endpoint_freshness_cached(
            prices_wide,
            price_matrix_signature,
        )
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

def _render_hedge_harvester_section() -> None:
    st.subheader("Options Scenario Research")
    hedge_ticker = st.text_input("Ticker for collar scenario:", value="MU").upper()
    if st.button("Estimate Scenario Premium"):
        with st.spinner(f"Pricing vol for {hedge_ticker}..."):
            res = calculate_optimal_hedge(hedge_ticker)
            if "Action" not in res:
                st.error("Engine error retrieving chain.")
            else:
                st.success(f"Strike: ${res.get('Strike')} | Exp: {res.get('Exp')} Days")
                if 'Est_Yield' in res:
                    st.write(f"**Scenario premium:** {res['Est_Yield']*100:.2f}%")
                if res.get("Reason"):
                    st.caption(str(res["Reason"]))

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
st.title("Terminal Zero GodView")
st.markdown(f"Page Registry Shell | Proxy Integrity Lock <span style='color:#888;font-size:0.9em;'>(Updated: {time_str})</span>", unsafe_allow_html=True)
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

# Custom Sort: Prioritize legacy scanner research buckets
def rate_weight(val):
    v = str(val).upper()
    if "ENTER:" in v and "STRONG" in v and "BUY" in v: return 1
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
        portfolio_state = st.session_state.get("portfolio_allocation_state")
        if isinstance(portfolio_state, dict):
            live_candidate = portfolio_state.get("weights")
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

# --- DASH-1 page registry shell: new top-level pages, legacy content preserved below. ---

# ==========================================
# TAB 1: TICKER POOL & PROXY MONITOR
# ==========================================
def _render_opportunities_page() -> None:
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
def _render_data_health_section() -> None:
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
def _render_drift_monitor_section() -> None:
    from views.drift_monitor_view import render_drift_monitor_view
    if drift_alert_manager is None or drift_detector is None:
        st.info("Drift monitor unavailable.")
    else:
        render_drift_monitor_view(
            alert_manager=drift_alert_manager,
            drift_detector=drift_detector,
            baseline_weights=baseline_weights,
            baseline_metadata=baseline_metadata,
            live_weights=live_weights,
            macro=macro_features if "macro_features" in globals() else pd.DataFrame(),
        )

# ==========================================
# TAB 4: DAILY SCAN (CONFLUENCE)
# ==========================================
def _render_daily_scan_section() -> None:
    st.subheader("Confluence Grid (Fundamental Resonance vs. Technical Extension)")
    
    lens_view = st.radio("Toggle Lens:", ["🌍 Macro View (Decluttered)", "🎯 Sniper View (High-Alpha Dispersion)"], horizontal=True)

    def get_plot_category(score, dist):
        if score == 100:
            if dist > 5.0: return "Wait (Extended)"
            elif dist >= -2.0: return "Research focus (support zone)"
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
            "Research focus (support zone)": "#00FFAA",
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
                "Plot_Category": "Research Bucket",
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
        
        # Draw Research Support Zone
        fig.add_shape(
            type="rect",
            x0=-2, y0=90, x1=5, y1=102,
            line=dict(color="#00FFAA", width=2, dash="dash"),
            fillcolor="#00FFAA",
            opacity=0.15,
            layer="below"
        )
        fig.add_annotation(x=1.5, y=96, text="RESEARCH SUPPORT ZONE", showarrow=False, font=dict(color="#00FFAA", size=14))
        
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
def _render_backtest_lab_section() -> None:
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

_POOL_TO_UNIVERSE = {
    "Score \u2265 90 (Super Cycle)": "Sovereign Pool",
    "Score 100 (Flawless only)": "Sovereign Pool",
    "Sovereign Pool (flush-adj)": "Sovereign Pool",
    "Global (all sectors)": "Global (All Sectors)",
    "Score \u2265 90 (2nd tier)": "Sovereign Pool",
}


def _format_backtest_percent(value: object, *, signed: bool) -> str:
    if isinstance(value, (int, float)) and value != 0:
        if signed:
            return f"+{value*100:.1f}%" if value > 0 else f"{value*100:.1f}%"
        return f"{value*100:.1f}%"
    if isinstance(value, str):
        return value
    return ""


def _build_strategy_matrix(
    bt_cache: dict,
    *,
    running: bool,
    running_name: str,
) -> pd.DataFrame:
    rows = []
    first_pending_assigned = False
    for name, strategy in STRATEGY_REGISTRY.items():
        bt_reg = strategy.get("backtest", {})
        cached = bt_cache.get(name, {})
        cagr_raw = cached.get("cagr") or bt_reg.get("cagr")
        dd_raw = cached.get("max_dd") or bt_reg.get("max_dd")
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
            "Universe": _POOL_TO_UNIVERSE.get(
                strategy.get("ticker_pool", ""),
                "Global (All Sectors)",
            ),
            "Entry": strategy["entry"],
            "Exit": strategy["exit"],
            "Rules": strategy.get("rules", ""),
            "CAGR": _format_backtest_percent(cagr_raw, signed=True),
            "Max DD": _format_backtest_percent(dd_raw, signed=False),
            "BT": bt_status,
            "Core Math": strategy["core_math"],
        })
    return pd.DataFrame(rows)


def _ensure_strategy_formula_cache() -> None:
    if "formulas_loaded" not in st.session_state:
        st.session_state.formula_cache = {
            name: strat["core_math"] for name, strat in STRATEGY_REGISTRY.items()
        }
        st.session_state.formulas_loaded = True


def _ensure_modular_strategy_state(
    bt_cache: dict | None = None,
    running: bool | None = None,
    running_name: str | None = None,
) -> pd.DataFrame:
    _ensure_strategy_formula_cache()
    cache = bt_cache if bt_cache is not None else read_bt_cache()
    if running is None or running_name is None:
        running, running_name, _bt_start_ts = is_backtest_running()
    if "strat_matrix_v3" not in st.session_state:
        st.session_state.strat_matrix_v3 = _build_strategy_matrix(
            cache,
            running=bool(running),
            running_name=str(running_name or ""),
        )
    return st.session_state.strat_matrix_v3


def _render_modular_strategies_section() -> None:
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
    if st.session_state.get("_v3_ver") != _V3_CACHE_VERSION:
        st.session_state.pop("strat_matrix_v3", None)
        st.session_state["_v3_ver"] = _V3_CACHE_VERSION

    # --- Phase 2: Load cache + PID probe ---
    bt_cache = read_bt_cache()
    running, running_name, bt_start_ts = is_backtest_running()

    # --- 1. Build DataFrame from registry ---
    base_df = _ensure_modular_strategy_state(
        bt_cache,
        running=running,
        running_name=running_name,
    )
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
                    try:
                        pid = spawn_backtest(next_script, next_name)
                        st.session_state["_bt_was_running"] = True
                        st.session_state.pop("strat_matrix_v3", None)
                        st.rerun()
                    except RuntimeError as exc:
                        st.warning(str(exc))
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
def _clean_portfolio_price_frame(prices: pd.DataFrame) -> pd.DataFrame:
    return clean_price_frame(prices)


def _extract_yfinance_close(raw: pd.DataFrame, tickers: tuple[str, ...]) -> pd.DataFrame:
    if not isinstance(raw, pd.DataFrame) or raw.empty:
        return pd.DataFrame()
    close = pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        levels_0 = set(raw.columns.get_level_values(0))
        levels_1 = set(raw.columns.get_level_values(1))
        if "Close" in levels_0:
            close = raw["Close"]
        elif "Adj Close" in levels_0:
            close = raw["Adj Close"]
        elif "Close" in levels_1:
            close = raw.xs("Close", axis=1, level=1)
        elif "Adj Close" in levels_1:
            close = raw.xs("Adj Close", axis=1, level=1)
    elif "Close" in raw.columns:
        close = raw["Close"]
    elif "Adj Close" in raw.columns:
        close = raw["Adj Close"]

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0] if tickers else "Close")
    if not isinstance(close, pd.DataFrame) or close.empty:
        return pd.DataFrame()
    close.columns = [str(col).upper() for col in close.columns]
    return _clean_portfolio_price_frame(close)


@st.cache_data(ttl=900, show_spinner=False)
def _download_ytd_close_prices(tickers: tuple[str, ...], start_iso: str) -> pd.DataFrame:
    if not tickers:
        return pd.DataFrame()
    if "pytest" in sys.modules:
        return pd.DataFrame()
    raw = yf.download(
        list(tickers),
        start=start_iso,
        progress=False,
        auto_adjust=True,
        threads=True,
        timeout=3,
    )
    return _extract_yfinance_close(raw, tickers)


def _local_benchmark_close_prices(tickers: tuple[str, ...], ytd_start: pd.Timestamp) -> pd.DataFrame:
    """Fallback benchmark close prices from the local TRI parquet package."""
    if not tickers or not parquet_data_available or not ticker_map_parquet or prices_wide.empty:
        return pd.DataFrame()
    ticker_to_permno = {str(ticker).upper(): permno for permno, ticker in ticker_map_parquet.items()}
    selected = {
        ticker: ticker_to_permno[ticker]
        for ticker in [str(t).upper() for t in tickers]
        if ticker in ticker_to_permno and ticker_to_permno[ticker] in prices_wide.columns
    }
    if not selected:
        return pd.DataFrame()
    local_prices = prices_wide.loc[prices_wide.index >= ytd_start, list(selected.values())].copy()
    local_prices = local_prices.rename(columns={permno: ticker for ticker, permno in selected.items()})
    return _clean_portfolio_price_frame(local_prices)


def _build_benchmark_equity(
    tickers: tuple[str, ...],
    ytd_start: pd.Timestamp,
) -> tuple[dict[str, pd.Series], pd.Timestamp | None, str]:
    """Build benchmark curves with local TRI plus per-ticker stale live overlay."""
    return build_benchmark_equity_from_prices(
        tickers=tickers,
        ytd_start=ytd_start,
        local_prices=_local_benchmark_close_prices(tickers, ytd_start),
        live_loader=_download_ytd_close_prices,
    )


def _current_optimizer_weights() -> pd.Series:
    state = _portfolio_allocation_state()
    replay_raw = _valid_strategy_replay_latest_weights()
    raw = replay_raw if replay_raw is not None else (state.get("weights") if state else st.session_state.get("optimizer_weights"))
    if isinstance(raw, pd.Series):
        weights = raw.copy()
    elif isinstance(raw, dict):
        weights = pd.Series(raw, dtype="float64")
    else:
        return pd.Series(dtype="float64")
    weights = pd.to_numeric(weights, errors="coerce").replace([np.inf, -np.inf], np.nan)
    weights = weights.dropna()
    weights = weights[weights > 0]
    total = float(weights.sum()) if not weights.empty else 0.0
    if weights.empty or total <= 0:
        return pd.Series(dtype="float64")
    if total > 1.0:
        return weights / total
    return weights


def _clear_portfolio_allocation_session_state() -> None:
    st.session_state[PORTFOLIO_ALLOCATION_STATE_KEY] = {
        "mode": "unavailable",
        "source": "optimizer",
        "weights": {},
        "cash_only": False,
        "latest_price_date": "",
    }
    st.session_state["portfolio_allocation_mode"] = "unavailable"
    st.session_state["portfolio_allocation_source"] = "optimizer"
    st.session_state["portfolio_allocation_weights"] = {}
    st.session_state["portfolio_allocation_cash_only"] = False
    st.session_state["portfolio_allocation_price_latest_date"] = ""
    st.session_state["optimizer_weights"] = {}
    st.session_state["optimizer_price_latest_date"] = ""
    st.session_state["optimizer_cash_only"] = False
    st.session_state.pop(PORTFOLIO_CURRENT_HOLD_REPLAY_KEY, None)


def _current_optimizer_is_cash_only() -> bool:
    replay_raw = _valid_strategy_replay_latest_weights()
    if isinstance(replay_raw, dict) and not replay_raw:
        return True
    state = _portfolio_allocation_state()
    if state and "cash_only" in state:
        return bool(state.get("cash_only", False))
    return bool(st.session_state.get("optimizer_cash_only", False))


def _portfolio_allocation_state() -> dict[str, object]:
    state = st.session_state.get("portfolio_allocation_state")
    return state if isinstance(state, dict) else {}


def _weights_by_ticker(weights: pd.Series) -> pd.Series:
    return map_permno_weights_to_ticker_weights(weights, ticker_map_parquet)


def _weighted_equity_curve(
    prices: pd.DataFrame,
    weights: pd.Series,
    name: str,
    required_latest: pd.Timestamp | None = None,
    price_freshness=None,
) -> pd.Series | None:
    prices = _clean_portfolio_price_frame(prices)
    if prices.empty or weights.empty:
        return None
    positive_weights = pd.to_numeric(weights, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    positive_weights = positive_weights[positive_weights > 0]
    if positive_weights.empty:
        return None
    missing_cols = [col for col in positive_weights.index if col not in prices.columns]
    if missing_cols:
        return None
    cols = list(positive_weights.index)
    if not cols:
        return None
    aligned_prices, _target_latest, stale_cols = filter_price_frame_to_fresh_columns(
        prices,
        cols,
        required_latest=required_latest,
        freshness=price_freshness,
    )
    if stale_cols:
        return None
    aligned_prices = aligned_prices.reindex(columns=cols).where(aligned_prices > 0)
    aligned_prices = aligned_prices.dropna(how="all")
    if aligned_prices.shape[0] < 2:
        return None
    aligned_weights = positive_weights.reindex(cols).fillna(0.0)
    aligned_total = float(aligned_weights.sum())
    if aligned_total <= 0:
        return None
    if aligned_total > 1.0:
        aligned_weights = aligned_weights / aligned_total
    daily_returns = aligned_prices.pct_change(fill_method=None).iloc[1:]
    daily_returns = daily_returns.replace([np.inf, -np.inf], np.nan)
    weighted_returns = daily_returns.mul(aligned_weights, axis=1).sum(axis=1, min_count=len(cols))
    weighted_returns = weighted_returns.replace([np.inf, -np.inf], np.nan).dropna()
    if weighted_returns.empty:
        return None
    equity = (1 + weighted_returns).cumprod()
    equity = equity.replace([np.inf, -np.inf], np.nan).dropna()
    if equity.empty:
        return None
    equity.name = name
    return equity


def _cash_equity_curve(ytd_start: pd.Timestamp) -> pd.Series:
    start = pd.Timestamp(ytd_start).normalize()
    end = pd.Timestamp.now().normalize()
    if end <= start:
        index = pd.DatetimeIndex([start])
        values = [1.0]
    else:
        index = pd.DatetimeIndex([start, end])
        values = [1.0, 1.0]
    equity = pd.Series(values, index=index, dtype="float64", name="Portfolio (Cash)")
    return equity


def _build_portfolio_ytd_equity(
    weights: pd.Series,
    ytd_start: pd.Timestamp,
) -> tuple[pd.Series | None, pd.Timestamp | None, str]:
    if _current_optimizer_is_cash_only():
        cash_equity = _cash_equity_curve(ytd_start)
        return cash_equity, cash_equity.index.max(), "cash-only"

    if not weights.empty and parquet_data_available and not prices_wide.empty:
        ytd_prices = prices_wide.loc[prices_wide.index >= ytd_start]
        ytd_prices = ytd_prices.reindex(columns=weights.index)
        required_latest = (
            price_endpoint_freshness.required_latest
            if price_endpoint_freshness is not None
            else None
        )
        local_equity = _weighted_equity_curve(
            prices=ytd_prices,
            weights=weights,
            name="Portfolio",
            required_latest=required_latest,
            price_freshness=price_endpoint_freshness,
        )
        if local_equity is not None:
            return local_equity, local_equity.index.max(), "optimized local fresh"

    ticker_weights = _weights_by_ticker(weights)
    if not ticker_weights.empty:
        live_prices = _download_ytd_close_prices(tuple(ticker_weights.index), ytd_start.strftime("%Y-%m-%d"))
        live_equity = _weighted_equity_curve(
            prices=live_prices,
            weights=ticker_weights,
            name="Portfolio",
        )
        if live_equity is not None:
            return live_equity, live_prices.index.max(), "optimized live"

    if parquet_data_available and not prices_wide.empty:
        ytd_prices = prices_wide.loc[prices_wide.index >= ytd_start].copy()
        if not ytd_prices.empty and ytd_prices.shape[1] > 0:
            ew = pd.Series(1.0 / ytd_prices.shape[1], index=ytd_prices.columns)
            ew_equity = _weighted_equity_curve(ytd_prices, ew, "Portfolio (EW)")
            if ew_equity is not None:
                return ew_equity, _clean_portfolio_price_frame(ytd_prices).index.max(), "equal-weight local"

    return None, None, "unavailable"


def _build_portfolio_ytd_equity_from_replay(
    context: DashboardReplayContext,
    horizon_start: pd.Timestamp,
) -> tuple[pd.Series | None, pd.Timestamp | None, str]:
    """Compound daily portfolio_return from replay_df into a cumulative equity curve."""
    if context.status != "ready" or context.sampling != "daily":
        return None, None, "daily replay performance unavailable"
    replay_df = context.replay_df
    if not isinstance(replay_df, pd.DataFrame) or replay_df.empty:
        return None, None, "replay unavailable"
    if "portfolio_return" not in replay_df.columns or "date" not in replay_df.columns:
        return None, None, "replay missing columns"

    df = replay_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df[df["date"] >= horizon_start]
    if df.empty:
        return None, None, "no replay data in window"

    # portfolio_return is the same for all asset rows on a given date; take one per date
    daily_ret = (
        df.drop_duplicates(subset=["date"])
        .set_index("date")
        .sort_index()["portfolio_return"]
    )
    daily_ret = pd.to_numeric(daily_ret, errors="coerce").fillna(0.0)
    if daily_ret.empty:
        return None, None, "replay returns empty"

    # Compound daily returns into cumulative equity starting at 1.0
    equity = (1 + daily_ret).cumprod()
    equity.name = "Portfolio (Replay)"
    return equity, equity.index.max(), f"replay:{context.method}"


def _replay_identity_caption(context: DashboardReplayContext) -> str:
    run_id = str(context.run_id or "unknown")
    source_id = str(context.source_id or context.source_mode or "unknown")
    method_id = str(context.method_id or context.method or "unknown")
    window = context.date_window if isinstance(context.date_window, dict) else {}
    start = window.get("replay_start") or window.get("requested_start") or (
        context.replay_dates[0] if context.replay_dates else "unknown"
    )
    end = window.get("replay_end") or window.get("requested_end") or (
        context.replay_dates[-1] if context.replay_dates else "unknown"
    )
    return (
        f"run_id={run_id} | source_id={source_id} | method_id={method_id} | "
        f"date_window={start}..{end}"
    )


def _portfolio_horizon_start(horizon: str, now: datetime.datetime) -> pd.Timestamp:
    if horizon == "1Y":
        return pd.Timestamp(now) - pd.DateOffset(years=1)
    if horizon == "3Y":
        return pd.Timestamp(now) - pd.DateOffset(years=3)
    if horizon == "5Y":
        return pd.Timestamp(now) - pd.DateOffset(years=5)
    if horizon == "Max":
        return pd.Timestamp("2000-01-01")
    return pd.Timestamp(now.year, 1, 1)


def _render_portfolio_horizon_control() -> tuple[str, pd.Timestamp]:
    now = datetime.datetime.now()
    horizon = st.radio(
        "Time horizon",
        ["YTD", "1Y", "3Y", "5Y", "Max"],
        horizontal=True,
        label_visibility="collapsed",
        key="portfolio_replay_horizon",
    )
    horizon_start = _portfolio_horizon_start(horizon, now)
    st.session_state["_portfolio_horizon_start"] = horizon_start
    return horizon, horizon_start


def _render_portfolio_ytd_chart(
    replay_context: DashboardReplayContext | None = None,
    *,
    horizon: str,
    ytd_start: pd.Timestamp,
) -> None:
    """Render Portfolio YTD performance vs SPY and QQQ benchmarks."""
    st.subheader("📈 Portfolio Performance")

    portfolio_equity = None
    portfolio_latest = None
    portfolio_source = "unavailable"
    cached_context = replay_context if replay_context is not None else _valid_cached_ytd_replay_context(ytd_start)
    if cached_context is not None and cached_context.sampling == "daily":
        portfolio_equity, portfolio_latest, portfolio_source = _build_portfolio_ytd_equity_from_replay(
            cached_context, ytd_start
        )

    if portfolio_equity is None:
        portfolio_source = "daily replay performance unavailable"
        st.info("Daily replay performance unavailable for this method/window.")

    benchmark_equity, benchmark_latest, benchmark_source = _build_benchmark_equity(("SPY", "QQQ"), ytd_start)

    if not benchmark_equity and portfolio_equity is None:
        st.info("No YTD data available yet. Benchmarks and portfolio data will appear once market data is loaded.")
        return

    # --- Build Plotly chart ---
    fig = go.Figure()

    if portfolio_equity is not None:
        fig.add_trace(go.Scatter(
            x=portfolio_equity.index,
            y=(portfolio_equity - 1) * 100,
            mode="lines",
            name=portfolio_equity.name,
            line=dict(color="#00FFAA", width=2.5),
        ))

    color_map = {"SPY": "#6366F1", "QQQ": "#F59E0B"}
    for ticker, eq in benchmark_equity.items():
        trace_name = ticker if benchmark_latest is None or eq.index.max() >= benchmark_latest else f"{ticker} (stale)"
        fig.add_trace(go.Scatter(
            x=eq.index,
            y=(eq - 1) * 100,
            mode="lines",
            name=trace_name,
            line=dict(color=color_map.get(ticker, "#888888"), width=1.8, dash="dot"),
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="#555555", line_width=0.8)

    fig.update_layout(
        template="plotly_dark",
        height=420,
        yaxis_title=f"{horizon} Return (%)",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=30, b=30),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    metric_cols = st.columns(3 if portfolio_equity is not None else 2)
    col_idx = 0
    if portfolio_equity is not None:
        pf_ret = float(portfolio_equity.iloc[-1] - 1) * 100 if len(portfolio_equity) > 0 else 0.0
        if not np.isfinite(pf_ret):
            pf_ret = 0.0
        with metric_cols[col_idx]:
            st.metric(portfolio_equity.name, f"{pf_ret:+.2f}%")
        col_idx += 1
    for ticker in ["SPY", "QQQ"]:
        if ticker in benchmark_equity and col_idx < len(metric_cols):
            eq = benchmark_equity[ticker]
            if benchmark_latest is not None and eq.index.max() < benchmark_latest:
                continue
            ret = float(eq.iloc[-1] - 1) * 100 if len(eq) > 0 else 0.0
            if not np.isfinite(ret):
                ret = 0.0
            with metric_cols[col_idx]:
                st.metric(ticker, f"{ret:+.2f}%")
            col_idx += 1

    latest_dates = [d for d in [portfolio_latest, benchmark_latest] if d is not None]
    if latest_dates:
        latest_date = max(latest_dates)
        st.caption(
            f"Stock prices refreshed through {latest_date.date()} "
            f"(portfolio: {portfolio_source}; benchmarks: {benchmark_source})."
        )
    if cached_context is not None and portfolio_equity is not None:
        st.caption(f"Replay identity: {_replay_identity_caption(cached_context)}")


def _render_portfolio_builder_section() -> None:
    if parquet_data_available and fundamentals_wide is not None:
        try:
            position_memory = load_current_position_memory()
            universe = build_optimizer_universe(
                df_scan=df_scan,
                ticker_map=ticker_map_parquet,
                prices_wide=prices_wide,
                policy=DEFAULT_OPTIMIZER_UNIVERSE_POLICY,
                position_memory=position_memory,
                price_freshness=price_endpoint_freshness,
            )
            st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY, None)
            st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY, None)
            optimizer_prices = prices_wide
            optimizer_freshness = price_endpoint_freshness
            stale_columns = tuple(
                record.permno
                for record in universe.stale_endpoints
                if record.permno is not None and record.permno in prices_wide.columns
            )
            if stale_columns:
                repair = repair_stale_price_endpoints_with_live_overlay(
                    prices_wide,
                    ticker_map_parquet,
                    stale_columns,
                    required_latest=price_endpoint_freshness.required_latest if price_endpoint_freshness is not None else None,
                    price_freshness=price_endpoint_freshness,
                    max_staleness_days=DEFAULT_OPTIMIZER_UNIVERSE_POLICY.max_endpoint_staleness_days,
                )
                st.session_state[PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY] = {
                    "source": repair.source,
                    "display_only": repair.display_only,
                    "canonical_market_data_write": repair.canonical_market_data_write,
                    "repaired_columns": [portfolio_replay_asset_identity(col) for col in repair.repaired_columns],
                    "unrepaired_columns": [portfolio_replay_asset_identity(col) for col in repair.unrepaired_columns],
                    "required_latest": repair.required_latest.date().isoformat() if repair.required_latest is not None else "",
                    "diagnostics": list(repair.diagnostics),
                }
                if repair.repaired_columns:
                    st.session_state[PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY] = repair.prices.reindex(
                        columns=list(repair.repaired_columns)
                    )
                    optimizer_prices = repair.prices
                    optimizer_freshness = repair.freshness
                    universe = build_optimizer_universe(
                        df_scan=df_scan,
                        ticker_map=ticker_map_parquet,
                        prices_wide=optimizer_prices,
                        policy=DEFAULT_OPTIMIZER_UNIVERSE_POLICY,
                        position_memory=position_memory,
                        price_freshness=optimizer_freshness,
                    )
                    repaired_labels = [
                        str(ticker_map_parquet.get(col, col)).upper()
                        for col in repair.repaired_columns
                    ]
                    st.caption(
                        "Display-only stale endpoint repair applied for: "
                        + ", ".join(repaired_labels)
                        + "."
                    )
            render_optimizer_view(
                prices_wide=optimizer_prices,
                ticker_map=ticker_map_parquet,
                sector_map=sector_map_parquet,
                selected_permnos=universe.included_permnos,
                universe_audit=universe,
                position_memory=position_memory,
                price_freshness=optimizer_freshness,
                show_allocation_outputs=False,
            )
        except Exception as e:
            st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY, None)
            st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY, None)
            st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
            _clear_strategy_replay_session_cache(include_context=True)
            _clear_portfolio_allocation_session_state()
            st.error(f"Optimizer unavailable: {type(e).__name__}: {e}")
    else:
        st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY, None)
        st.session_state.pop(PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY, None)
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        _clear_strategy_replay_session_cache(include_context=True)
        _clear_portfolio_allocation_session_state()
        _render_portfolio_builder_placeholder()

def _render_replay_allocation_snapshot(context: DashboardReplayContext) -> None:
    st.subheader("Allocation Snapshot")
    if context.status != "ready" or context.sampling != "daily":
        st.info("Daily replay allocation snapshot unavailable for this method/window.")
        return
    latest_rows = context.latest_snapshot.copy()
    if latest_rows.empty:
        st.info("Daily replay allocation snapshot unavailable for this method/window.")
        return
    if "target_weight" not in latest_rows.columns:
        st.info("Daily replay allocation snapshot missing target weights.")
        return
    display = latest_rows.copy()
    display["target_weight"] = pd.to_numeric(display["target_weight"], errors="coerce").fillna(0.0)
    display = display[display["target_weight"] > 0].copy()
    if display.empty:
        st.info("Daily replay allocation snapshot is cash-only for this method/window.")
        return
    if "date" in display.columns:
        display["date"] = pd.to_datetime(display["date"], errors="coerce")
        latest_date = display["date"].max()
    else:
        latest_date = pd.NaT
    title_date = latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "latest"
    st.caption(f"Latest daily replay snapshot ({title_date}). {_replay_identity_caption(context)}")

    chart_df = display.copy()
    if "ticker" not in chart_df.columns:
        chart_df["ticker"] = chart_df.get("permno", "").astype(str)
    fig = go.Figure(
        data=[
            go.Pie(
                labels=chart_df["ticker"].astype(str),
                values=chart_df["target_weight"],
                hole=0.35,
                sort=False,
                textinfo="label+percent",
                hovertemplate="%{label}<br>Weight: %{value:.2%}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="Allocation (Latest Daily Replay Snapshot)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
    )
    st.plotly_chart(fig, use_container_width=True)

    preferred_cols = ["date", "ticker", "permno", "context_role", "target_weight", "cash_residual", "status", "reason"]
    cols = [col for col in preferred_cols if col in display.columns]
    table = display[cols].copy()
    if "date" in table.columns:
        table["date"] = table["date"].dt.strftime("%Y-%m-%d")
    table = table.rename(
        columns={
            "date": "Date",
            "ticker": "Ticker",
            "permno": "Permno",
            "context_role": "Context Role",
            "target_weight": "Current Weight",
            "cash_residual": "Cash Residual",
            "status": "Status",
            "reason": "Reason",
        }
    )
    format_cols = {col: "{:.2%}" for col in ["Current Weight", "Cash Residual"] if col in table.columns}
    st.dataframe(table.style.format(format_cols), use_container_width=True, hide_index=True)


# ==========================================
# STRATEGY REPLAY
# ==========================================


def _get_replay_source_label(method_value: str, max_weight: float, source: str) -> str:
    """Build structured source label: method | cap_used | cap_source | artifact."""
    return (
        f"method={method_value} | cap_used={max_weight:.0%} | "
        f"cap_source=controls.max_weight | source={source}"
    )


def _dashboard_file_signature(path: Path) -> tuple[str, int | None, int | None]:
    resolved = path.resolve(strict=False)
    try:
        stat = resolved.stat()
    except OSError:
        return (str(resolved), None, None)
    return (str(resolved), int(stat.st_mtime_ns), int(stat.st_size))


def _dashboard_replay_data_signature() -> tuple:
    repair_state = st.session_state.get(PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY)
    repair_signature = (
        repair_state
        if isinstance(repair_state, dict)
        else {"source": "none", "repaired_columns": [], "required_latest": ""}
    )
    return (
        build_unified_data_cache_signature(
            processed_dir="./data/processed",
            static_dir="./data/static",
        ),
        _dashboard_file_signature(Path("data/portfolio_lifecycle_log.jsonl")),
        _dashboard_file_signature(LIFECYCLE_BUY_SELL_LOG_PATH),
        _dashboard_file_signature(RULE100_SOFTMAX_V1_HISTORY_PATH),
        repair_signature,
    )


@st.cache_data(ttl=900, show_spinner=False)
def _load_dashboard_replay_event_annotations_cached(data_signature: tuple) -> pd.DataFrame:
    """Load ENTER/EXIT annotations for the shared dashboard replay context."""
    del data_signature
    try:
        from data.portfolio_lifecycle_log import read_lifecycle_log

        events = read_lifecycle_log()
    except Exception:
        return pd.DataFrame()
    if not isinstance(events, pd.DataFrame) or events.empty:
        return pd.DataFrame()
    events = _merge_rule100_softmax_v1_history(events)
    events["date"] = pd.to_datetime(events.get("date"), errors="coerce")
    return events.dropna(subset=["date"]).reset_index(drop=True)


@st.cache_data(ttl=900, show_spinner=False)
def _load_dashboard_replay_buy_sell_decisions_cached(data_signature: tuple) -> pd.DataFrame:
    """Load compact BUY/SELL audit rows for the shared dashboard replay context."""
    del data_signature
    if not LIFECYCLE_BUY_SELL_LOG_PATH.exists():
        return pd.DataFrame()
    try:
        decisions = pd.read_json(LIFECYCLE_BUY_SELL_LOG_PATH, lines=True)
    except Exception:
        return pd.DataFrame()
    if not isinstance(decisions, pd.DataFrame) or decisions.empty:
        return pd.DataFrame()
    decisions["date"] = pd.to_datetime(decisions.get("date"), errors="coerce")
    return (
        decisions.dropna(subset=["date"])
        .sort_values("date", ascending=False)
        .reset_index(drop=True)
    )


@st.cache_data(ttl=900, show_spinner=False)
def _load_dashboard_strategy_replay_inputs_cached(
    *,
    as_of_date: str,
    start_date: str,
    method: str,
    controls_json: str,
    max_weight: float,
    replay_assets: tuple[object, ...],
    data_signature: tuple,
):
    """Load one local PIT replay slice for the dashboard replay section."""
    del data_signature  # cache invalidation key; consumed by Streamlit hashing
    controls = json.loads(controls_json or "{}")
    inputs = load_strategy_replay_inputs(
        as_of_date=as_of_date,
        start_date=start_date,
        end_date=as_of_date,
        method=method,
        controls=controls,
        max_weight=max_weight,
        universe_mode="r3000_pit",
        processed_dir="./data/processed",
        static_dir="./data/static",
    )
    selected_columns: list[object] = []
    for asset in replay_assets:
        candidate = asset
        if candidate in inputs.prices.columns and candidate not in selected_columns:
            selected_columns.append(candidate)
    if selected_columns:
        prices = inputs.prices.reindex(columns=selected_columns)
        returns = inputs.returns.reindex(columns=selected_columns)
    else:
        prices = inputs.prices.iloc[:, 0:0]
        returns = inputs.returns.iloc[:, 0:0]
    return type(inputs)(
        as_of_date=inputs.as_of_date,
        prices=prices,
        returns=returns,
        ticker_map=inputs.ticker_map,
        cache_signature=inputs.cache_signature,
        cache_key=inputs.cache_key,
        metadata=inputs.metadata,
    )


@st.cache_data(ttl=900, show_spinner=False)
def _load_dashboard_batched_pit_replay_data_cached(
    *,
    start_date: str,
    end_date: str,
    selected_permnos: tuple[int, ...] | None,
    data_signature: tuple,
):
    """Load PIT replay source data once for a dashboard replay window."""

    del data_signature  # cache invalidation key; consumed by Streamlit hashing
    return load_batched_pit_replay_data(
        processed_dir="./data/processed",
        static_dir="./data/static",
        start_date=start_date,
        end_date=end_date,
        start_year=2000,
        selected_permnos=selected_permnos,
    )


def _numeric_replay_permnos(replay_assets: tuple[object, ...]) -> tuple[int, ...] | None:
    """Return selected replay assets that can be represented as permnos."""

    permnos: list[int] = []
    for asset in replay_assets:
        parsed = pd.to_numeric(pd.Series([asset]), errors="coerce").iloc[0]
        if pd.notna(parsed) and np.isfinite(float(parsed)):
            permnos.append(int(parsed))
    return tuple(dict.fromkeys(permnos)) or None


def _price_frame_for_replay_selection_signature(replay_assets: tuple[object, ...]) -> pd.DataFrame:
    repair_overlay = _portfolio_repair_overlay_frame(replay_assets)
    if repair_overlay.empty:
        return prices_wide
    combined = repair_overlay.combine_first(prices_wide)
    return clean_price_frame(combined.reindex(columns=list(prices_wide.columns)))


def _portfolio_repair_overlay_frame(replay_assets: tuple[object, ...]) -> pd.DataFrame:
    repair_state = st.session_state.get(PORTFOLIO_STALE_ENDPOINT_REPAIR_KEY)
    if not isinstance(repair_state, dict):
        return pd.DataFrame()
    repaired_identities = set(repair_state.get("repaired_columns") or ())
    if not repaired_identities:
        return pd.DataFrame()
    selected = [
        asset
        for asset in replay_assets
        if portfolio_replay_asset_identity(asset) in repaired_identities
        and asset in prices_wide.columns
    ]
    if not selected:
        return pd.DataFrame()
    repair_frame = st.session_state.get(PORTFOLIO_STALE_ENDPOINT_REPAIR_FRAME_KEY)
    if not isinstance(repair_frame, pd.DataFrame) or repair_frame.empty:
        return pd.DataFrame()
    return clean_price_frame(repair_frame.reindex(columns=selected))


def _filter_dashboard_replay_inputs_to_assets(
    inputs,
    replay_assets: tuple[object, ...],
):
    """Limit batched PIT inputs to the signed dashboard replay assets."""

    selected_columns: list[object] = []
    column_lookup = {str(col): col for col in inputs.prices.columns}
    repair_overlay = _portfolio_repair_overlay_frame(replay_assets)
    if not repair_overlay.empty:
        repair_overlay = repair_overlay.loc[repair_overlay.index <= pd.Timestamp(inputs.as_of_date).normalize()]
    for asset in replay_assets:
        candidate = asset if asset in inputs.prices.columns else column_lookup.get(str(asset))
        if candidate is None and asset in repair_overlay.columns:
            candidate = asset
        if (
            candidate is not None
            and (candidate in inputs.prices.columns or candidate in repair_overlay.columns)
            and candidate not in selected_columns
        ):
            selected_columns.append(candidate)
    if selected_columns:
        prices = inputs.prices.reindex(columns=selected_columns)
        returns = inputs.returns.reindex(columns=selected_columns)
    else:
        prices = inputs.prices.iloc[:, 0:0]
        returns = inputs.returns.iloc[:, 0:0]
    overlay_columns = [col for col in repair_overlay.columns if col in selected_columns]
    if overlay_columns:
        prices = clean_price_frame(repair_overlay.reindex(columns=overlay_columns).combine_first(prices))
        returns = prices.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
        returns = returns.reindex(columns=selected_columns)
    metadata = dict(inputs.metadata) if isinstance(inputs.metadata, dict) else {}
    metadata["dashboard_replay_assets"] = [
        portfolio_replay_asset_identity(asset) for asset in replay_assets
    ]
    metadata["dashboard_selected_columns"] = [
        portfolio_replay_asset_identity(asset) for asset in selected_columns
    ]
    metadata["dashboard_repair_overlay_columns"] = [
        portfolio_replay_asset_identity(asset) for asset in overlay_columns
    ]
    signature = dict(inputs.cache_signature) if isinstance(inputs.cache_signature, dict) else {"cache_signature": inputs.cache_signature}
    signature["dashboard_replay_assets"] = metadata["dashboard_replay_assets"]
    signature["dashboard_selected_columns"] = metadata["dashboard_selected_columns"]
    signature["dashboard_repair_overlay_columns"] = metadata["dashboard_repair_overlay_columns"]
    return type(inputs)(
        as_of_date=inputs.as_of_date,
        prices=prices,
        returns=returns,
        ticker_map=inputs.ticker_map,
        cache_signature=signature,
        cache_key=f"{inputs.cache_key}:dashboard_selected:{_stable_json_hash(metadata['dashboard_selected_columns'])}",
        metadata=metadata,
    )


def _context_replay_ticker_map(
    *,
    replay_assets: tuple[object, ...],
    allocation_assets: tuple[object, ...],
    ticker_map: dict | None,
) -> dict[object, str]:
    out: dict[object, str] = {}
    source_map = ticker_map if isinstance(ticker_map, dict) else {}
    allocation_set = set(allocation_assets)
    for asset in replay_assets:
        if asset in allocation_set or asset == "CASH":
            continue
        ticker = source_map.get(asset)
        if ticker is None:
            try:
                ticker = source_map.get(int(asset))
            except Exception:
                ticker = None
        if ticker:
            out[asset] = str(ticker).upper().strip()
    return out


def _append_context_only_replay_rows(
    replay_df: pd.DataFrame,
    *,
    replay_assets: tuple[object, ...],
    allocation_assets: tuple[object, ...],
    ticker_map: dict | None,
    method: str,
    max_weight: float,
) -> pd.DataFrame:
    """Add zero-weight rows for historical context tickers without making them allocatable."""

    context_map = _context_replay_ticker_map(
        replay_assets=replay_assets,
        allocation_assets=allocation_assets,
        ticker_map=ticker_map,
    )
    if not context_map or not isinstance(replay_df, pd.DataFrame) or replay_df.empty or "date" not in replay_df.columns:
        return replay_df
    dates = pd.to_datetime(replay_df["date"], errors="coerce").dropna().dt.date.astype(str).drop_duplicates()
    if dates.empty:
        return replay_df
    existing = set()
    if {"date", "permno"}.issubset(replay_df.columns):
        existing = {
            (pd.Timestamp(row["date"]).date().isoformat(), row["permno"])
            for _, row in replay_df[["date", "permno"]].dropna(subset=["date"]).iterrows()
        }
    rows: list[dict[str, object]] = []
    for date_value in dates:
        for asset, ticker in context_map.items():
            if (date_value, asset) in existing:
                continue
            rows.append(
                {
                    "date": date_value,
                    "method": method,
                    "ticker": ticker,
                    "permno": asset,
                    "target_weight": 0.0,
                    "cash_residual": np.nan,
                    "asset_return": 0.0,
                    "weight_for_return": 0.0,
                    "return_contribution": 0.0,
                    "portfolio_return": np.nan,
                    "portfolio_equity": np.nan,
                    "cap_used": float(max_weight),
                    "cap_source": "context_only",
                    "source": "strategy_replay:context_only_asset",
                    "row_role": "daily_portfolio",
                    "context_role": "historical_context",
                    "status": "context_only",
                    "reason": "historical_context_asset_not_current_allocation",
                }
            )
    if not rows:
        return replay_df
    combined = pd.concat([replay_df, pd.DataFrame(rows)], ignore_index=True, sort=False)
    return combined


def _normalize_dashboard_context_frame(
    frame: pd.DataFrame,
    *,
    context_type: str,
    method: str,
    replay: pd.DataFrame,
) -> pd.DataFrame:
    """Dashboard adapter for the shared strategy replay context contract."""

    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame(columns=REPLAY_CONTEXT_COLUMNS)
    normalized = normalize_context_frame_for_replay(
        frame,
        context_type=context_type,
        method=method,
        replay=replay,
    )
    return normalized.reindex(columns=REPLAY_CONTEXT_COLUMNS).reset_index(drop=True)


def _replay_context_weight_lookup(replay: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(replay, pd.DataFrame) or replay.empty:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    if "date" not in replay.columns or "ticker" not in replay.columns or "target_weight" not in replay.columns:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    lookup = replay[["date", "ticker", "target_weight"]].copy()
    lookup["date"] = pd.to_datetime(lookup["date"], errors="coerce").dt.normalize()
    lookup["ticker"] = lookup["ticker"].astype(str).str.upper().str.strip()
    lookup["replay_target_weight"] = pd.to_numeric(lookup["target_weight"], errors="coerce").fillna(0.0).clip(lower=0.0)
    lookup = lookup[(lookup["date"].notna()) & (lookup["ticker"] != "") & (lookup["ticker"] != "CASH")]
    if lookup.empty:
        return pd.DataFrame(columns=["date", "ticker", "replay_target_weight"])
    lookup = lookup.sort_values(["date", "ticker"], kind="mergesort")
    return lookup.drop_duplicates(["date", "ticker"], keep="last")[["date", "ticker", "replay_target_weight"]]


def _align_context_weights_to_replay(frame: pd.DataFrame, replay: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return pd.DataFrame() if not isinstance(frame, pd.DataFrame) else frame.copy()
    if "date" not in frame.columns or "ticker" not in frame.columns:
        return frame.copy()
    context_type = "decision_context"
    if "context_type" in frame.columns:
        non_empty = frame["context_type"].dropna().astype(str).str.strip()
        if not non_empty.empty and non_empty.iloc[0]:
            context_type = non_empty.iloc[0]
    method_value = str(frame["method"].dropna().astype(str).iloc[0]) if "method" in frame.columns and not frame["method"].dropna().empty else ""
    if method_value.strip().lower() in {"", "all", "nan", "none"}:
        method_values = replay["method"].dropna().astype(str) if "method" in replay.columns else pd.Series(dtype=object)
        method_value = method_values.iloc[0] if not method_values.empty else ""
    normalized = normalize_context_frame_for_replay(
        frame,
        context_type=context_type,
        method=method_value,
        replay=replay,
    )
    out = normalized.copy()
    original_weight = frame[["date", "ticker", "weight"]].copy() if "weight" in frame.columns else pd.DataFrame()
    if not original_weight.empty:
        original_weight["date"] = pd.to_datetime(original_weight["date"], errors="coerce").dt.date.astype(str)
        original_weight["ticker"] = original_weight["ticker"].astype(str).str.upper().str.strip()
        original_weight["audit_weight"] = pd.to_numeric(original_weight["weight"], errors="coerce")
        out = out.merge(original_weight[["date", "ticker", "audit_weight"]], on=["date", "ticker"], how="left")
    if "audit_weight" not in out.columns:
        out["audit_weight"] = pd.to_numeric(out.get("weight", pd.Series(pd.NA, index=out.index)), errors="coerce")
    out["weight"] = out["target_weight"]
    return out


def _dashboard_filter_coverage_plan_to_assets(
    coverage_plan: list[object] | None,
    replay_assets: tuple[object, ...],
) -> list[object] | None:
    if coverage_plan is None:
        return None
    selected_permnos = set(_numeric_replay_permnos(replay_assets) or ())
    if not selected_permnos:
        return coverage_plan
    filtered: list[object] = []
    for entry in coverage_plan:
        expected = [int(value) for value in getattr(entry, "expected_members", []) if int(value) in selected_permnos]
        try:
            filtered.append(replace(entry, expected_members=expected))
        except TypeError:
            filtered.append(entry)
    return filtered


def _strategy_replay_cache_signature(
    *,
    method: str,
    max_weight: float,
    controls: dict,
    replay_assets: tuple[object, ...],
    allocation_assets: tuple[object, ...] | None = None,
    replay_dates: list[str],
    sampling: str,
    data_signature: tuple,
) -> dict:
    controls_for_signature = {
        key: value
        for key, value in controls.items()
        if not isinstance(value, pd.DataFrame)
    }
    return {
        "method": str(method),
        "max_weight": float(max_weight),
        "risk_free_rate": float(controls_for_signature.get("risk_free_rate", 0.0)),
        "controls": controls_for_signature,
        "replay_assets": [portfolio_replay_asset_identity(asset) for asset in replay_assets],
        "allocation_assets": [
            portfolio_replay_asset_identity(asset)
            for asset in (allocation_assets if allocation_assets is not None else replay_assets)
        ],
        "replay_dates": list(replay_dates),
        "sampling": str(sampling),
        "data_signature": list(data_signature),
    }


def _make_dashboard_replay_request(
    *,
    method: str,
    max_weight: float,
    controls: dict,
    data_signature: tuple,
    replay_assets: tuple[object, ...],
    allocation_assets: tuple[object, ...] | None = None,
    replay_dates: list[str],
    sampling: str,
    full_history_start: str,
    include_replay: bool,
) -> DashboardReplayRequest:
    """Return a replay request value without touching artifact or backend sources."""

    return DashboardReplayRequest(
        method=method,
        max_weight=max_weight,
        controls=controls,
        cache_signature=_strategy_replay_cache_signature(
            method=method,
            max_weight=max_weight,
            controls=controls,
            replay_assets=replay_assets,
            allocation_assets=allocation_assets,
            replay_dates=replay_dates,
            sampling=sampling,
            data_signature=data_signature,
        ),
        replay_assets=replay_assets,
        replay_dates=list(replay_dates),
        sampling=sampling,
        data_signature=data_signature,
        full_history_start=full_history_start,
        include_replay=include_replay,
        allocation_assets=tuple(allocation_assets if allocation_assets is not None else replay_assets),
    )


def _dashboard_request_with_sampling(
    request: DashboardReplayRequest,
    *,
    replay_dates: list[str],
    sampling: str,
) -> DashboardReplayRequest:
    return _make_dashboard_replay_request(
        method=request.method,
        max_weight=request.max_weight,
        controls=request.controls,
        data_signature=request.data_signature,
        replay_assets=request.replay_assets,
        allocation_assets=request.allocation_assets,
        replay_dates=replay_dates,
        sampling=sampling,
        full_history_start=request.full_history_start,
        include_replay=request.include_replay,
    )


def _replay_signatures_match(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return False
    return json.dumps(left, sort_keys=True, default=str) == json.dumps(right, sort_keys=True, default=str)


def _replay_signature_without_dates(signature: dict | None) -> dict | None:
    if not isinstance(signature, dict):
        return None
    out = dict(signature)
    out.pop("replay_dates", None)
    return out


def _normalized_replay_date_strings(values: list[object] | tuple[object, ...] | pd.Series) -> list[str]:
    dates = pd.to_datetime(pd.Series(list(values), dtype=object), errors="coerce").dropna()
    return [pd.Timestamp(value).date().isoformat() for value in dates]


def _frame_date_strings(frame: pd.DataFrame) -> set[str]:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "date" not in frame.columns:
        return set()
    dates = pd.to_datetime(frame["date"], errors="coerce").dropna()
    return {pd.Timestamp(value).date().isoformat() for value in dates}


def _filter_frame_to_replay_dates(frame: pd.DataFrame, replay_dates: list[str]) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "date" not in frame.columns:
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    requested = set(replay_dates)
    out = frame.copy()
    normalized = pd.to_datetime(out["date"], errors="coerce")
    mask = normalized.dt.date.astype(str).isin(requested)
    return out[mask].copy()


def _filter_frame_to_replay_window(frame: pd.DataFrame, replay_dates: list[str]) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "date" not in frame.columns or not replay_dates:
        return frame.copy() if isinstance(frame, pd.DataFrame) else pd.DataFrame()
    out = frame.copy()
    normalized = pd.to_datetime(out["date"], errors="coerce")
    start = pd.Timestamp(replay_dates[0])
    end = pd.Timestamp(replay_dates[-1])
    return out[(normalized >= start) & (normalized <= end)].copy()


def _dashboard_context_covers_replay_dates(
    context: DashboardReplayContext,
    replay_dates: list[str],
) -> bool:
    requested_dates = set(_normalized_replay_date_strings(replay_dates))
    if not requested_dates:
        return False
    context_dates = set(_normalized_replay_date_strings(context.replay_dates))
    if not requested_dates.issubset(context_dates):
        return False
    replay_frame_dates = _frame_date_strings(context.replay_df)
    return requested_dates.issubset(replay_frame_dates)


def _scope_dashboard_replay_context_to_dates(
    context: DashboardReplayContext,
    *,
    replay_dates: list[str],
    cache_signature: dict,
) -> DashboardReplayContext:
    scoped_replay = _filter_frame_to_replay_dates(context.replay_df, replay_dates)
    scoped_events = _filter_frame_to_replay_window(context.event_annotations, replay_dates)
    scoped_decisions = _filter_frame_to_replay_window(context.buy_sell_decisions, replay_dates)
    latest_snapshot = _strategy_replay_latest_snapshot(scoped_replay)
    date_window = dict(context.date_window) if isinstance(context.date_window, dict) else {}
    actual_dates = sorted(_frame_date_strings(scoped_replay))
    date_window.update(
        {
            "requested_start": replay_dates[0] if replay_dates else None,
            "requested_end": replay_dates[-1] if replay_dates else None,
            "replay_start": actual_dates[0] if actual_dates else None,
            "replay_end": actual_dates[-1] if actual_dates else None,
        }
    )
    return replace(
        context,
        cache_signature=cache_signature,
        replay_df=scoped_replay,
        latest_snapshot=latest_snapshot,
        event_annotations=scoped_events,
        buy_sell_decisions=scoped_decisions,
        replay_dates=list(replay_dates),
        date_window=date_window,
    )


def _current_portfolio_replay_selection(
    *,
    method: str,
    max_weight: float,
    risk_free_rate: float,
) -> PortfolioReplaySelection | None:
    if not parquet_data_available or prices_wide.empty:
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        return None
    selection = st.session_state.get(PORTFOLIO_REPLAY_SELECTION_KEY)
    if not isinstance(selection, PortfolioReplaySelection):
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        return None
    replay_assets = tuple(selection.replay_assets)
    if not replay_assets:
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        return None
    available = set(prices_wide.columns)
    if any(asset not in available for asset in replay_assets):
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        _clear_strategy_replay_session_cache(include_context=True)
        return None
    signature_prices = _price_frame_for_replay_selection_signature(replay_assets)
    expected_signature = build_portfolio_replay_selection_signature(
        prices_wide=signature_prices,
        replay_assets=replay_assets,
        method=method,
        max_weight=max_weight,
        risk_free_rate=risk_free_rate,
    )
    if not _replay_signatures_match(selection.signature, expected_signature):
        st.session_state.pop(PORTFOLIO_REPLAY_SELECTION_KEY, None)
        _clear_strategy_replay_session_cache(include_context=True)
        return None
    return selection


def _current_replay_assets_key() -> tuple[str, ...]:
    main_method = st.session_state.get("optimizer_method", "Inverse Volatility")
    main_max_weight = float(st.session_state.get("optimizer_max_weight", 0.35))
    risk_free_rate = float(st.session_state.get("optimizer_risk_free_rate", 0.0))
    selection = _current_portfolio_replay_selection(
        method=main_method,
        max_weight=main_max_weight,
        risk_free_rate=risk_free_rate,
    )
    if selection is None:
        return ()
    return tuple(selection.replay_assets)


def _ticker_to_dashboard_permno(ticker: object) -> object | None:
    ticker_key = str(ticker).upper().strip()
    if not ticker_key or not ticker_map_parquet:
        return None
    for permno, mapped_ticker in ticker_map_parquet.items():
        if str(mapped_ticker).upper().strip() == ticker_key and permno in prices_wide.columns:
            return permno
    return None


def _context_tickers_for_replay_window(
    frame: pd.DataFrame,
    *,
    replay_dates: list[str],
    actions: set[str],
) -> set[str]:
    if not isinstance(frame, pd.DataFrame) or frame.empty or "date" not in frame.columns or "ticker" not in frame.columns:
        return set()
    dates = pd.to_datetime(pd.Series(replay_dates), errors="coerce").dropna()
    if dates.empty:
        return set()
    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce").dt.normalize()
    work["ticker"] = work["ticker"].astype(str).str.upper().str.strip()
    work = work.dropna(subset=["date"])
    work = work[(work["date"] >= dates.min().normalize()) & (work["date"] <= dates.max().normalize())]
    if actions:
        action_values = pd.Series("", index=work.index, dtype=object)
        if "action" in work.columns:
            action_values = work["action"]
        elif "buy_sell" in work.columns:
            action_values = work["buy_sell"]
        action_values = action_values.astype(str).str.upper().str.strip()
        work = work[action_values.isin(actions)]
    return {ticker for ticker in work["ticker"].dropna().unique() if ticker and ticker != "CASH"}


def _horizon_replay_assets_for_window(
    *,
    current_assets: tuple[object, ...],
    replay_dates: list[str],
    event_annotations: pd.DataFrame,
    buy_sell_decisions: pd.DataFrame,
    rule100_history: pd.DataFrame | None,
) -> tuple[object, ...]:
    """Return current signed assets plus mapped lifecycle assets active in the replay window."""

    assets: list[object] = []
    for asset in current_assets:
        if asset in prices_wide.columns and asset not in assets:
            assets.append(asset)

    tickers = set()
    tickers.update(
        _context_tickers_for_replay_window(
            event_annotations,
            replay_dates=replay_dates,
            actions={"ENTER", "EXIT"},
        )
    )
    tickers.update(
        _context_tickers_for_replay_window(
            buy_sell_decisions,
            replay_dates=replay_dates,
            actions={"BUY", "SELL", "ENTER", "EXIT"},
        )
    )
    if isinstance(rule100_history, pd.DataFrame):
        tickers.update(
            _context_tickers_for_replay_window(
                rule100_history,
                replay_dates=replay_dates,
                actions=set(),
            )
        )

    for ticker in sorted(tickers):
        permno = _ticker_to_dashboard_permno(ticker)
        if permno is not None and permno not in assets:
            assets.append(permno)
    return tuple(assets)


def _current_latest_replay_signature() -> dict | None:
    if not parquet_data_available or prices_wide.empty:
        return None
    latest_date = pd.Timestamp(prices_wide.index[-1]).date().isoformat()
    main_method = st.session_state.get("optimizer_method", "Inverse Volatility")
    main_max_weight = float(st.session_state.get("optimizer_max_weight", 0.35))
    risk_free_rate = float(st.session_state.get("optimizer_risk_free_rate", 0.0))
    selection = _current_portfolio_replay_selection(
        method=main_method,
        max_weight=main_max_weight,
        risk_free_rate=risk_free_rate,
    )
    if selection is None:
        return None
    controls = {
        "max_weight": main_max_weight,
        "risk_free_rate": risk_free_rate,
    }
    return _strategy_replay_cache_signature(
        method=main_method,
        max_weight=main_max_weight,
        controls=controls,
        replay_assets=tuple(selection.replay_assets),
        allocation_assets=tuple(selection.replay_assets),
        replay_dates=[latest_date],
        sampling="daily",
        data_signature=_dashboard_replay_data_signature(),
    )


def _current_full_replay_signature(
    *,
    horizon_start: pd.Timestamp,
    sampling: str = "daily",
) -> dict | None:
    if not parquet_data_available or prices_wide.empty:
        return None
    main_method = st.session_state.get("optimizer_method", "Inverse Volatility")
    main_max_weight = float(st.session_state.get("optimizer_max_weight", 0.35))
    risk_free_rate = float(st.session_state.get("optimizer_risk_free_rate", 0.0))
    selection = _current_portfolio_replay_selection(
        method=main_method,
        max_weight=main_max_weight,
        risk_free_rate=risk_free_rate,
    )
    if selection is None:
        return None
    replay_dates = [
        pd.Timestamp(value).date().isoformat()
        for value in prices_wide.index[prices_wide.index >= pd.Timestamp(horizon_start)]
    ]
    data_signature = _dashboard_replay_data_signature()
    event_annotations = _load_dashboard_replay_event_annotations_cached(data_signature)
    buy_sell_decisions = _load_dashboard_replay_buy_sell_decisions_cached(data_signature)
    controls = {
        "max_weight": main_max_weight,
        "risk_free_rate": risk_free_rate,
    }
    rule100_hist = None
    if main_method == "Rule of 100":
        rule100_hist = _load_rule100_softmax_v1_history()
        controls["rule100_candidate_frame"] = rule100_hist
    replay_assets = _horizon_replay_assets_for_window(
        current_assets=tuple(selection.replay_assets),
        replay_dates=replay_dates,
        event_annotations=event_annotations,
        buy_sell_decisions=buy_sell_decisions,
        rule100_history=rule100_hist,
    )
    return _strategy_replay_cache_signature(
        method=main_method,
        max_weight=main_max_weight,
        controls=controls,
        replay_assets=replay_assets,
        allocation_assets=tuple(selection.replay_assets),
        replay_dates=replay_dates,
        sampling=sampling,
        data_signature=data_signature,
    )


def _build_dashboard_replay_request(
    *,
    replay_dates_override: list[str] | None = None,
    include_replay: bool = True,
    horizon_start: pd.Timestamp | None = None,
) -> tuple[DashboardReplayRequest, pd.DataFrame, pd.DataFrame, str]:
    """Build a pure selected-method replay request and cheap context frames."""

    main_method = st.session_state.get("optimizer_method", "Inverse Volatility")
    main_max_weight = float(st.session_state.get("optimizer_max_weight", 0.35))
    controls: dict = {
        "max_weight": main_max_weight,
        "risk_free_rate": float(st.session_state.get("optimizer_risk_free_rate", 0.0)),
    }
    data_signature = _dashboard_replay_data_signature()
    event_annotations = _load_dashboard_replay_event_annotations_cached(data_signature)
    buy_sell_decisions = _load_dashboard_replay_buy_sell_decisions_cached(data_signature)

    if main_method == "Rule of 100":
        rule100_hist = _load_rule100_softmax_v1_history()
        required_cols = {"date", "ticker", "factor_positive_count", "technical_quality"}
        if required_cols.issubset(rule100_hist.columns):
            controls["rule100_candidate_frame"] = rule100_hist
        else:
            request = _make_dashboard_replay_request(
                method=main_method,
                max_weight=main_max_weight,
                controls=controls,
                data_signature=data_signature,
                replay_assets=(),
                allocation_assets=(),
                replay_dates=[],
                sampling="daily",
                full_history_start="",
                include_replay=include_replay,
            )
            missing = required_cols - set(rule100_hist.columns)
            return request, event_annotations, buy_sell_decisions, f"Rule100 history missing required columns: {missing}"

    if not include_replay:
        request = _make_dashboard_replay_request(
            method=main_method,
            max_weight=main_max_weight,
            controls=controls,
            data_signature=data_signature,
            replay_assets=(),
            allocation_assets=(),
            replay_dates=[],
            sampling="daily",
            full_history_start="",
            include_replay=False,
        )
        return request, event_annotations, buy_sell_decisions, ""

    if not parquet_data_available or prices_wide.empty:
        request = _make_dashboard_replay_request(
            method=main_method,
            max_weight=main_max_weight,
            controls=controls,
            data_signature=data_signature,
            replay_assets=(),
            allocation_assets=(),
            replay_dates=[],
            sampling="daily",
            full_history_start="",
            include_replay=True,
        )
        return request, event_annotations, buy_sell_decisions, "price_data_unavailable"

    selection = _current_portfolio_replay_selection(
        method=main_method,
        max_weight=main_max_weight,
        risk_free_rate=float(controls.get("risk_free_rate", 0.0)),
    )
    if selection is None:
        request = _make_dashboard_replay_request(
            method=main_method,
            max_weight=main_max_weight,
            controls=controls,
            data_signature=data_signature,
            replay_assets=(),
            allocation_assets=(),
            replay_dates=[],
            sampling="daily",
            full_history_start=pd.Timestamp(prices_wide.index.min()).date().isoformat(),
            include_replay=True,
        )
        return request, event_annotations, buy_sell_decisions, "portfolio_replay_selection_unavailable"

    replay_assets_key = tuple(asset for asset in selection.replay_assets if asset in prices_wide.columns)
    if not replay_assets_key:
        request = _make_dashboard_replay_request(
            method=main_method,
            max_weight=main_max_weight,
            controls=controls,
            data_signature=data_signature,
            replay_assets=(),
            allocation_assets=(),
            replay_dates=[],
            sampling="daily",
            full_history_start=pd.Timestamp(prices_wide.index.min()).date().isoformat(),
            include_replay=True,
        )
        return request, event_annotations, buy_sell_decisions, "no_assets_selected_for_replay"

    latest_ts = pd.Timestamp(prices_wide.index[-1])
    ytd_start = horizon_start if horizon_start is not None else pd.Timestamp(f"{latest_ts.year}-01-01")
    replay_dates = [
        pd.Timestamp(value).date().isoformat()
        for value in prices_wide.index[prices_wide.index >= pd.Timestamp(ytd_start)]
    ]
    if replay_dates_override is not None:
        replay_dates = list(replay_dates_override)
    elif "pytest" in sys.modules:
        replay_dates = replay_dates[-1:]
    replay_assets_for_window = _horizon_replay_assets_for_window(
        current_assets=replay_assets_key,
        replay_dates=replay_dates,
        event_annotations=event_annotations,
        buy_sell_decisions=buy_sell_decisions,
        rule100_history=controls.get("rule100_candidate_frame") if main_method == "Rule of 100" else None,
    )
    request = _make_dashboard_replay_request(
        method=main_method,
        max_weight=main_max_weight,
        controls=controls,
        data_signature=data_signature,
        replay_assets=replay_assets_for_window,
        allocation_assets=replay_assets_key,
        replay_dates=replay_dates,
        sampling="daily",
        full_history_start=pd.Timestamp(prices_wide.index.min()).date().isoformat(),
        include_replay=True,
    )
    return request, event_annotations, buy_sell_decisions, ""


def _valid_cached_ytd_replay_context(horizon_start: pd.Timestamp) -> DashboardReplayContext | None:
    cached_context = st.session_state.get(STRATEGY_REPLAY_YTD_CONTEXT_KEY)
    if not isinstance(cached_context, DashboardReplayContext):
        return None
    if cached_context.status != "ready" or cached_context.sampling != "daily" or len(cached_context.replay_dates) < 2:
        _clear_strategy_replay_session_cache(include_context=True)
        return None
    current_signature = _current_full_replay_signature(
        horizon_start=horizon_start,
        sampling=cached_context.sampling,
    )
    if current_signature is None:
        _clear_strategy_replay_session_cache(include_context=True)
        return None
    requested_dates = list(current_signature.get("replay_dates") or [])
    if _replay_signatures_match(cached_context.cache_signature, current_signature):
        if _dashboard_context_covers_replay_dates(cached_context, requested_dates):
            return cached_context
        st.session_state.pop(STRATEGY_REPLAY_YTD_CONTEXT_KEY, None)
        st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
        return None
    if _replay_signatures_match(
        _replay_signature_without_dates(cached_context.cache_signature),
        _replay_signature_without_dates(current_signature),
    ):
        if _dashboard_context_covers_replay_dates(cached_context, requested_dates):
            return _scope_dashboard_replay_context_to_dates(
                cached_context,
                replay_dates=requested_dates,
                cache_signature=current_signature,
            )
    st.session_state.pop(STRATEGY_REPLAY_YTD_CONTEXT_KEY, None)
    st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
    return None


def _clear_strategy_replay_session_cache(*, include_context: bool = False) -> None:
    if include_context:
        st.session_state.pop(STRATEGY_REPLAY_CONTEXT_KEY, None)
    st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
    st.session_state.pop(STRATEGY_REPLAY_CACHE_SIGNATURE_KEY, None)
    st.session_state.pop(STRATEGY_REPLAY_YTD_CONTEXT_KEY, None)


def _valid_strategy_replay_latest_weights() -> dict | None:
    raw = st.session_state.get(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY)
    if not isinstance(raw, dict):
        return None
    stored_signature = st.session_state.get(STRATEGY_REPLAY_CACHE_SIGNATURE_KEY)
    if not _replay_signatures_match(stored_signature, _current_latest_replay_signature()):
        st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
        return None
    return raw


def _dashboard_replay_cash_closed_frame(
    *,
    replay_date: str,
    method: str,
    max_weight: float,
    reason: str,
) -> pd.DataFrame:
    """Return a visible cash-closed row for one failed dashboard replay date."""
    return pd.DataFrame(
        [
            {
                "date": replay_date,
                "method": method,
                "ticker": "CASH",
                "permno": "CASH",
                "target_weight": 1.0,
                "cash_residual": 1.0,
                "cap_used": float(max_weight),
                "cap_source": "controls.max_weight",
                "source": "strategy_replay:dashboard_pit_loader",
                "status": "cash_closed",
                "reason": reason,
            }
        ]
    )


def _strategy_replay_latest_snapshot(replay_df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(replay_df, pd.DataFrame) or replay_df.empty or "date" not in replay_df.columns:
        return pd.DataFrame()
    out = replay_df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    latest_date = out["date"].max()
    if pd.isna(latest_date):
        return pd.DataFrame()
    latest = out[out["date"] == latest_date].copy()
    if "row_role" not in latest.columns:
        latest["row_role"] = "daily_portfolio"
    if "context_role" not in latest.columns:
        ticker = latest["ticker"].astype(str).str.upper().str.strip() if "ticker" in latest.columns else pd.Series("", index=latest.index)
        status = latest["status"].astype(str).str.lower().str.strip() if "status" in latest.columns else pd.Series("", index=latest.index)
        target = pd.to_numeric(latest.get("target_weight", pd.Series(0.0, index=latest.index)), errors="coerce").fillna(0.0)
        role = pd.Series("flat_in_replay", index=latest.index, dtype=object)
        role.loc[target > 0.0] = "current_holding"
        role.loc[ticker == "CASH"] = "cash"
        role.loc[status == "context_only"] = "historical_context"
        role.loc[status.str.contains("unavailable|missing", na=False)] = "unavailable"
        latest["context_role"] = role
    return latest


def _build_replay_context_diagnostics(context: DashboardReplayContext) -> dict[str, object]:
    """Compute audit diagnostics from the already-selected dashboard replay context."""

    replay = context.replay_df.copy() if isinstance(context.replay_df, pd.DataFrame) else pd.DataFrame()
    decisions = context.buy_sell_decisions.copy() if isinstance(context.buy_sell_decisions, pd.DataFrame) else pd.DataFrame()
    events = context.event_annotations.copy() if isinstance(context.event_annotations, pd.DataFrame) else pd.DataFrame()
    identity = {
        "run_id": context.run_id,
        "source_id": context.source_id,
        "method_id": context.method_id or context.method,
        "source_mode": context.source_mode,
        "cache_signature_hash": _stable_json_hash(context.cache_signature),
    }
    diagnostics: dict[str, object] = {
        "identity": identity,
        "closed_trade_return_summary": {"closed_trades": 0, "mean_return": 0.0, "median_return": 0.0},
        "exit_reason_quality": {"exit_rows": 0, "missing_reason_rows": 0, "missing_reason_rate": 0.0},
        "zero_exposure_buy_rows": {"count": 0, "rows": []},
        "hold_time_summary": {"closed_trades": 0, "mean_days": 0.0, "median_days": 0.0, "max_days": 0},
        "reason_code_concentration": {"top_reason": "", "top_reason_share": 0.0, "unique_reasons": 0},
    }
    if decisions.empty:
        return diagnostics

    decisions["date"] = pd.to_datetime(decisions.get("date"), errors="coerce")
    decisions["ticker"] = decisions.get("ticker", pd.Series("", index=decisions.index)).astype(str).str.upper().str.strip()
    decisions["action"] = decisions.get("action", decisions.get("buy_sell", pd.Series("", index=decisions.index))).astype(str).str.upper().str.strip()
    decisions["target_weight"] = pd.to_numeric(decisions.get("target_weight", pd.Series(np.nan, index=decisions.index)), errors="coerce")
    decisions["reason"] = decisions.get("reason", pd.Series("", index=decisions.index)).fillna("").astype(str)
    buys = decisions[decisions["action"].isin(["BUY", "ENTER"])].copy()
    sells = decisions[decisions["action"].isin(["SELL", "EXIT"])].copy()
    zero_buys = buys[(buys["target_weight"].fillna(0.0) == 0.0)].copy()
    diagnostics["zero_exposure_buy_rows"] = {
        "count": int(len(zero_buys)),
        "rows": zero_buys[["date", "ticker", "target_weight", "reason"]]
        .assign(date=lambda df: df["date"].dt.date.astype(str))
        .head(50)
        .to_dict("records"),
    }

    if not sells.empty:
        missing_reason = sells["reason"].str.strip().eq("")
        diagnostics["exit_reason_quality"] = {
            "exit_rows": int(len(sells)),
            "missing_reason_rows": int(missing_reason.sum()),
            "missing_reason_rate": float(missing_reason.mean()) if len(sells) else 0.0,
        }

    reasons = decisions["reason"].replace("", "missing_reason")
    if not reasons.empty:
        counts = reasons.value_counts(dropna=False)
        diagnostics["reason_code_concentration"] = {
            "top_reason": str(counts.index[0]),
            "top_reason_share": float(counts.iloc[0] / max(1, counts.sum())),
            "unique_reasons": int(len(counts)),
        }

    closed_rows: list[dict[str, object]] = []
    if not buys.empty and not sells.empty:
        replay_work = replay.copy()
        if not replay_work.empty and {"date", "ticker"}.issubset(replay_work.columns):
            replay_work["date"] = pd.to_datetime(replay_work["date"], errors="coerce")
            replay_work["ticker"] = replay_work["ticker"].astype(str).str.upper().str.strip()
            replay_daily = (
                replay_work.dropna(subset=["date"])
                .groupby(["date", "ticker"], as_index=False)["portfolio_return"]
                .last()
                if "portfolio_return" in replay_work.columns
                else pd.DataFrame(columns=["date", "ticker", "portfolio_return"])
            )
        else:
            replay_daily = pd.DataFrame(columns=["date", "ticker", "portfolio_return"])
        for ticker, ticker_buys in buys.dropna(subset=["date"]).groupby("ticker", sort=False):
            ticker_sells = sells[(sells["ticker"] == ticker) & sells["date"].notna()].sort_values("date")
            for _, buy_row in ticker_buys.sort_values("date").iterrows():
                later_sells = ticker_sells[ticker_sells["date"] >= buy_row["date"]]
                if later_sells.empty:
                    continue
                sell_row = later_sells.iloc[0]
                hold_days = int((sell_row["date"] - buy_row["date"]).days)
                window = replay_daily[
                    (replay_daily["date"] >= buy_row["date"])
                    & (replay_daily["date"] <= sell_row["date"])
                ]
                returns = pd.to_numeric(window.get("portfolio_return", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
                closed_return = float((1.0 + returns).prod() - 1.0) if not returns.empty else 0.0
                closed_rows.append({"ticker": ticker, "hold_days": hold_days, "return": closed_return})
        if closed_rows:
            returns = pd.Series([row["return"] for row in closed_rows], dtype="float64")
            holds = pd.Series([row["hold_days"] for row in closed_rows], dtype="float64")
            diagnostics["closed_trade_return_summary"] = {
                "closed_trades": int(len(closed_rows)),
                "mean_return": float(returns.mean()),
                "median_return": float(returns.median()),
            }
            diagnostics["hold_time_summary"] = {
                "closed_trades": int(len(closed_rows)),
                "mean_days": float(holds.mean()),
                "median_days": float(holds.median()),
                "max_days": int(holds.max()),
            }
    if not events.empty and not {"BUY", "SELL", "ENTER", "EXIT"}.intersection(set(decisions["action"])):
        diagnostics["exit_reason_quality"] = {
            "exit_rows": int((events.get("action", pd.Series(dtype=object)).astype(str).str.upper() == "EXIT").sum()),
            "missing_reason_rows": 0,
            "missing_reason_rate": 0.0,
        }
    return diagnostics


def _write_replay_context_diagnostic_artifact(
    context: DashboardReplayContext,
    *,
    output_path: Path = Path("docs/context/e2e_evidence/portfolio_replay_context_diagnostics_current.json"),
) -> Path:
    payload = _build_replay_context_diagnostics(context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = output_path.with_name(f".{output_path.name}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temp_path, output_path)
    return output_path


def _store_strategy_replay_context(context: DashboardReplayContext) -> None:
    st.session_state[STRATEGY_REPLAY_CONTEXT_KEY] = {
        "method": context.method,
        "max_weight": context.max_weight,
        "cache_signature": context.cache_signature,
        "source_label": context.source_label,
        "status": context.status,
        "reason": context.reason,
        "run_id": context.run_id,
        "source_id": context.source_id,
        "method_id": context.method_id,
        "date_window": context.date_window,
    }
    if context.status != "ready":
        _clear_strategy_replay_session_cache()
        return
    # Legacy replay diagnostics are never auto-published during dashboard startup.
    # The certified default portfolio route must be read-only and must not mutate
    # unrelated evidence merely because Streamlit evaluates the module.
    latest = context.latest_snapshot
    if isinstance(latest, pd.DataFrame) and not latest.empty:
        positive = latest[pd.to_numeric(latest.get("target_weight"), errors="coerce").fillna(0.0) > 0].copy()
        if not positive.empty:
            positive_assets = positive[positive["permno"].astype(str).str.upper() != "CASH"].copy()
            if positive_assets.empty:
                _clear_strategy_replay_session_cache()
                return
            weights = pd.Series(
                pd.to_numeric(positive_assets["target_weight"], errors="coerce").values,
                index=positive_assets["permno"].values,
                dtype="float64",
            ).dropna()
            weights = weights[weights > 0]
            if not weights.empty:
                st.session_state[STRATEGY_REPLAY_CACHE_SIGNATURE_KEY] = context.cache_signature
                st.session_state[STRATEGY_REPLAY_LATEST_WEIGHTS_KEY] = weights.to_dict()
                return
    _clear_strategy_replay_session_cache()


def _has_cached_replay_artifact(cache_signature: dict | None = None) -> bool:
    """True when a full daily replay context is already cached in session state."""
    ctx = st.session_state.get(STRATEGY_REPLAY_YTD_CONTEXT_KEY)
    if not isinstance(ctx, DashboardReplayContext) or ctx.status != "ready" or ctx.sampling != "daily":
        return False
    if cache_signature is None:
        return True
    return _replay_signatures_match(ctx.cache_signature, cache_signature)


def _sample_replay_timeline_from_daily(replay_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Return a display-only weekly sample from daily replay rows."""
    if not isinstance(replay_df, pd.DataFrame) or replay_df.empty or "date" not in replay_df.columns:
        return pd.DataFrame(), "daily"
    out = replay_df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date"])
    if out.empty:
        return out, "daily"
    unique_dates = pd.DatetimeIndex(sorted(out["date"].dt.normalize().unique()))
    if len(unique_dates) <= 160:
        return out, "daily"
    iso = unique_dates.isocalendar()
    weekly_index = unique_dates.to_series().groupby([iso.year, iso.week]).last()
    keep_dates = set(pd.to_datetime(weekly_index, errors="coerce").dropna().dt.normalize())
    keep_dates.add(pd.Timestamp(unique_dates[-1]).normalize())
    sampled = out[out["date"].dt.normalize().isin(keep_dates)].copy()
    return sampled, "weekly_display_from_daily"


def _dashboard_saved_replay_artifact_paths(cache_dir: Path | None = None) -> list[Path]:
    root = cache_dir or SELECTED_METHOD_REPLAY_CACHE_DIR
    if not root.exists():
        return []
    return sorted(
        root.glob("*.selected_method_replay.parquet.manifest.json"),
        key=lambda path: path.stat().st_mtime_ns if path.exists() else 0,
        reverse=True,
    )


def _dashboard_saved_replay_manifest_matches(
    manifest: dict,
    request: DashboardReplayRequest,
) -> tuple[bool, str]:
    dashboard_signature = manifest.get("dashboard_cache_signature")
    if not isinstance(dashboard_signature, dict):
        return False, "missing_dashboard_cache_signature"
    if not _replay_signatures_match(dashboard_signature, request.cache_signature):
        return False, "dashboard_cache_signature_mismatch"
    if len(request.replay_dates) > DASHBOARD_REPLAY_ARTIFACT_MAX_DATES:
        return False, "request_over_date_budget"
    return True, "ok"


def _read_dashboard_saved_replay_artifact(
    request: DashboardReplayRequest,
    *,
    cache_dir: Path | None = None,
) -> DashboardReplayArtifactRead:
    """Read a saved selected-method replay artifact only when backend and dashboard signatures match."""

    from strategies.strategy_replay import ReplayBudgetPolicy, read_selected_method_replay_artifact

    last_reason = "saved_artifact_not_found"
    for manifest_path in _dashboard_saved_replay_artifact_paths(cache_dir):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            last_reason = f"manifest_read_failed:{type(exc).__name__}"
            continue
        matches, reason = _dashboard_saved_replay_manifest_matches(manifest, request)
        if not matches:
            last_reason = reason
            continue
        artifact_path = manifest_path.with_name(manifest_path.name.removesuffix(".manifest.json"))
        result = read_selected_method_replay_artifact(
            artifact_path,
            method=request.method,
            controls=request.controls,
            start_date=request.full_history_start,
            end_date=request.replay_dates[-1] if request.replay_dates else None,
            as_of_range=request.replay_dates,
            expected_date_window={
                "replay_start": request.replay_dates[0] if request.replay_dates else None,
                "replay_end": request.replay_dates[-1] if request.replay_dates else None,
            },
            budget_policy=ReplayBudgetPolicy(
                max_rows=DASHBOARD_REPLAY_ARTIFACT_MAX_ROWS,
                max_dates=DASHBOARD_REPLAY_ARTIFACT_MAX_DATES,
            ),
            cache_dir=cache_dir or SELECTED_METHOD_REPLAY_CACHE_DIR,
        )
        if not result.available:
            return DashboardReplayArtifactRead(
                status="unavailable",
                reason=result.reason,
                artifact_path=result.artifact_path,
                manifest_path=result.manifest_path,
                manifest=result.manifest or manifest,
            )
        return DashboardReplayArtifactRead(
            status="ready",
            reason="ok",
            bundle=result.bundle,
            artifact_path=result.artifact_path,
            manifest_path=result.manifest_path,
            manifest=result.manifest or manifest,
        )
    return DashboardReplayArtifactRead(status="unavailable", reason=last_reason)


def _dashboard_context_from_artifact_read(
    artifact_read: DashboardReplayArtifactRead,
    request: DashboardReplayRequest,
    *,
    event_annotations: pd.DataFrame,
    buy_sell_decisions: pd.DataFrame,
) -> DashboardReplayContext:
    """Adapt a valid saved replay artifact frame to DashboardReplayContext."""

    manifest = artifact_read.manifest or {}
    bundle = artifact_read.bundle
    if bundle is not None:
        daily = bundle.replay.copy()
        events = bundle.event_rows.copy()
        decisions = bundle.decision_rows.copy()
    else:
        frame = artifact_read.frame if isinstance(artifact_read.frame, pd.DataFrame) else pd.DataFrame()
        daily = pd.DataFrame()
        events = pd.DataFrame()
        decisions = pd.DataFrame()
        if not frame.empty and "row_type" in frame.columns:
            daily = frame[frame["row_type"] == "daily_portfolio"].copy()
            events = frame[frame["row_type"] == "event_annotation"].copy()
            decisions = frame[frame["row_type"] == "buy_sell_decision"].copy()
        elif not frame.empty:
            daily = frame.copy()
    events = _align_context_weights_to_replay(events, daily)
    decisions = _align_context_weights_to_replay(decisions, daily)
    if not daily.empty and "date" in daily.columns:
        actual_dates = set(pd.to_datetime(daily["date"], errors="coerce").dropna().dt.date.astype(str))
        required_dates = set(request.replay_dates)
        if required_dates and not required_dates.issubset(actual_dates):
            _clear_strategy_replay_session_cache(include_context=True)
            return DashboardReplayContext(
                method=request.method,
                max_weight=request.max_weight,
                controls=request.controls,
                cache_signature=request.cache_signature,
                source_label=_get_replay_source_label(request.method, request.max_weight, "saved_artifact:missing_requested_dates"),
                replay_df=pd.DataFrame(),
                latest_snapshot=pd.DataFrame(),
                event_annotations=event_annotations,
                buy_sell_decisions=buy_sell_decisions,
                replay_dates=request.replay_dates,
                sampling=request.sampling,
                status="stale",
                reason="saved_artifact_missing_requested_dates",
                source_mode="unavailable",
            )
    latest_snapshot = _strategy_replay_latest_snapshot(daily)
    run_metadata = manifest.get("run_metadata") if isinstance(manifest.get("run_metadata"), dict) else {}
    bundle_metadata = getattr(bundle, "run_metadata", None)
    bundle_date_window = getattr(bundle_metadata, "date_window", None) if bundle_metadata is not None else None
    date_window = (
        bundle_date_window
        if isinstance(bundle_date_window, dict)
        else manifest.get("date_window") if isinstance(manifest.get("date_window"), dict) else {}
    )
    source = str(manifest.get("source_id") or "saved_artifact")
    context = DashboardReplayContext(
        method=request.method,
        max_weight=request.max_weight,
        controls=request.controls,
        cache_signature=request.cache_signature,
        source_label=_get_replay_source_label(request.method, request.max_weight, source),
        replay_df=daily,
        latest_snapshot=latest_snapshot,
        event_annotations=events,
        buy_sell_decisions=decisions,
        replay_dates=request.replay_dates,
        sampling=request.sampling,
        status="ready" if not daily.empty else "failed",
        reason="" if not daily.empty else "saved artifact has no daily portfolio rows",
        source_mode="saved_artifact",
        input_coverage_start=str(run_metadata.get("input_coverage_start") or ""),
        run_id=str(getattr(bundle_metadata, "run_id", "") or manifest.get("run_id") or ""),
        source_id=str(getattr(bundle_metadata, "source_id", "") or manifest.get("source_id") or source),
        method_id=str(getattr(bundle_metadata, "method_id", "") or manifest.get("method_id") or request.method),
        date_window=dict(date_window),
    )
    return context


def _dashboard_context_from_backend_bundle(
    bundle,
    request: DashboardReplayRequest,
    *,
    event_annotations: pd.DataFrame,
    buy_sell_decisions: pd.DataFrame,
) -> DashboardReplayContext:
    """Adapt a backend selected-method replay bundle to DashboardReplayContext."""

    replay_df = bundle.replay
    bundle_events = bundle.event_rows
    bundle_decisions = bundle.decision_rows
    aligned_events = _align_context_weights_to_replay(bundle_events, replay_df)
    aligned_decisions = _align_context_weights_to_replay(bundle_decisions, replay_df)
    first_source = str(replay_df["source"].iloc[0]) if not replay_df.empty and "source" in replay_df.columns else "strategy_replay"
    latest_snapshot = _strategy_replay_latest_snapshot(replay_df)
    run_metadata = getattr(bundle, "run_metadata", None)
    _coverage_start = getattr(run_metadata, "input_coverage_start", "") or ""
    date_window = getattr(run_metadata, "date_window", {}) if run_metadata is not None else {}
    context = DashboardReplayContext(
        method=request.method,
        max_weight=request.max_weight,
        controls=request.controls,
        cache_signature=request.cache_signature,
        source_label=_get_replay_source_label(request.method, request.max_weight, first_source),
        replay_df=replay_df,
        latest_snapshot=latest_snapshot,
        event_annotations=aligned_events if isinstance(bundle_events, pd.DataFrame) else event_annotations,
        buy_sell_decisions=aligned_decisions if isinstance(bundle_decisions, pd.DataFrame) else buy_sell_decisions,
        replay_dates=request.replay_dates,
        sampling=request.sampling,
        status="ready" if not replay_df.empty else "failed",
        reason="" if not replay_df.empty else "No strategy replay data produced.",
        source_mode="transitional_build",
        input_coverage_start=_coverage_start,
        run_id=str(getattr(run_metadata, "run_id", "") or ""),
        source_id=str(getattr(run_metadata, "source_id", "") or first_source),
        method_id=str(getattr(run_metadata, "method_id", "") or request.method),
        date_window=dict(date_window) if isinstance(date_window, dict) else {},
    )
    return context


def _build_dashboard_strategy_replay_context(
    *,
    replay_dates_override: list[str] | None = None,
    include_replay: bool = True,
    horizon_start: pd.Timestamp | None = None,
    allow_transitional_fallback: bool = True,
) -> DashboardReplayContext:
    """Build the selected-method replay bundle consumed by dashboard replay surfaces.

    Saved selected-method artifacts are preferred when their dashboard cache signature
    exactly matches the current method, cap, assets, dates, and data signature.
    Transitional backend build is an explicit fallback while artifact coverage matures.
    """
    from strategies.strategy_replay import build_selected_method_replay

    request, event_annotations, buy_sell_decisions, unavailable_reason = _build_dashboard_replay_request(
        replay_dates_override=replay_dates_override,
        include_replay=include_replay,
        horizon_start=horizon_start,
    )
    if unavailable_reason.startswith("Rule100 history"):
        _clear_strategy_replay_session_cache(include_context=True)
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, "rule100_history_missing_required_columns"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=[],
            sampling=request.sampling,
            status="input_unavailable",
            reason=unavailable_reason,
            source_mode="unavailable",
        )
    if not include_replay:
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, "strategy_replay:not_built_yet"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=[],
            sampling=request.sampling,
            status="building",
            reason="replay_not_built_yet",
            source_mode="transitional_build",
        )
    if unavailable_reason == "price_data_unavailable":
        _clear_strategy_replay_session_cache(include_context=True)
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, "strategy_replay:no_price_data"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=[],
            sampling=request.sampling,
            status="input_unavailable",
            reason="price_data_unavailable",
            source_mode="unavailable",
        )
    if unavailable_reason == "no_assets_selected_for_replay":
        _clear_strategy_replay_session_cache(include_context=True)
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, "strategy_replay:no_assets"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=[],
            sampling=request.sampling,
            status="input_unavailable",
            reason="no_assets_selected_for_replay",
            source_mode="unavailable",
        )
    if unavailable_reason == "portfolio_replay_selection_unavailable":
        _clear_strategy_replay_session_cache(include_context=True)
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, "strategy_replay:no_selection"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=[],
            sampling=request.sampling,
            status="input_unavailable",
            reason="portfolio_replay_selection_unavailable",
            source_mode="unavailable",
        )

    artifact_read = _read_dashboard_saved_replay_artifact(request)
    if artifact_read.status == "ready":
        context = _dashboard_context_from_artifact_read(
            artifact_read,
            request,
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
        )
        _store_strategy_replay_context(context)
        return context
    if not allow_transitional_fallback:
        _clear_strategy_replay_session_cache(include_context=True)
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, f"saved_artifact:{artifact_read.reason}"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=request.replay_dates,
            sampling=request.sampling,
            status="stale",
            reason=f"saved_artifact_unavailable:{artifact_read.reason}",
            source_mode="unavailable",
        )

    if not _replay_signatures_match(request.cache_signature, st.session_state.get(STRATEGY_REPLAY_CACHE_SIGNATURE_KEY)):
        st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
    replay_start = request.replay_dates[0] if request.replay_dates else request.full_history_start
    replay_end = request.replay_dates[-1] if request.replay_dates else request.full_history_start
    try:
        batched_replay_data = _load_dashboard_batched_pit_replay_data_cached(
            start_date=replay_start,
            end_date=replay_end,
            selected_permnos=_numeric_replay_permnos(request.allocation_assets),
            data_signature=request.data_signature,
        )
        # Replaces the older per-date _load_dashboard_strategy_replay_inputs_cached(...) path.
    except Exception as exc:
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, f"strategy_replay:pit_batch_failed:{type(exc).__name__}"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=request.replay_dates,
            sampling=request.sampling,
            status="failed",
            reason=f"load_batched_pit_replay_data failed: {type(exc).__name__}: {exc}",
            source_mode="transitional_build",
        )
    batched_loader = build_batched_pit_input_loader(batched_replay_data)

    def _dashboard_input_loader(
        *,
        as_of_date: str,
        start_date: str,
        end_date: str,
        method: str,
        controls: dict | None = None,
        max_weight: float | None = None,
        **_kwargs,
    ):
        del start_date, end_date, method, controls, max_weight
        inputs = batched_loader(as_of_date=as_of_date)
        return _filter_dashboard_replay_inputs_to_assets(
            inputs,
            replay_assets=request.allocation_assets,
        )

    try:
        from strategies.strategy_replay import _coerce_method, _compute_coverage_plan

        coverage_plan = _compute_coverage_plan(
            _coerce_method(request.method),
            request.controls,
            [pd.Timestamp(value) for value in request.replay_dates],
            batched=batched_replay_data,
        )
        coverage_plan = _dashboard_filter_coverage_plan_to_assets(
            coverage_plan,
            request.allocation_assets,
        )
    except Exception:
        coverage_plan = None

    # Pass event/decision context so the bundle attaches them filtered to replay window
    request.controls["event_context_frame"] = event_annotations
    request.controls["decision_context_frame"] = buy_sell_decisions

    try:
        bundle = build_selected_method_replay(
            method=request.method,
            controls=request.controls,
            prices=None,
            input_loader=_dashboard_input_loader,
            start_date=request.full_history_start,
            end_date=request.replay_dates[-1] if request.replay_dates else None,
            as_of_range=request.replay_dates,
            coverage_plan=coverage_plan,
        )
    except Exception as exc:
        return DashboardReplayContext(
            method=request.method,
            max_weight=request.max_weight,
            controls=request.controls,
            cache_signature=request.cache_signature,
            source_label=_get_replay_source_label(request.method, request.max_weight, f"strategy_replay:failed:{type(exc).__name__}"),
            replay_df=pd.DataFrame(),
            latest_snapshot=pd.DataFrame(),
            event_annotations=event_annotations,
            buy_sell_decisions=buy_sell_decisions,
            replay_dates=request.replay_dates,
            sampling=request.sampling,
            status="failed",
            reason=f"build_selected_method_replay failed: {type(exc).__name__}: {exc}",
            source_mode="transitional_build",
        )

    context = _dashboard_context_from_backend_bundle(
        bundle,
        request,
        event_annotations=event_annotations,
        buy_sell_decisions=buy_sell_decisions,
    )
    if request.allocation_assets and tuple(request.allocation_assets) != tuple(request.replay_assets):
        replay_with_context_assets = _append_context_only_replay_rows(
            context.replay_df,
            replay_assets=request.replay_assets,
            allocation_assets=request.allocation_assets,
            ticker_map=ticker_map_parquet,
            method=request.method,
            max_weight=request.max_weight,
        )
        event_ctx = _normalize_dashboard_context_frame(
            event_annotations,
            context_type="event_annotations",
            method=request.method,
            replay=replay_with_context_assets,
        )
        decision_ctx = _normalize_dashboard_context_frame(
            buy_sell_decisions,
            context_type="decision_context",
            method=request.method,
            replay=replay_with_context_assets,
        )
        context = replace(
            context,
            replay_df=replay_with_context_assets,
            latest_snapshot=_strategy_replay_latest_snapshot(replay_with_context_assets),
            event_annotations=_align_context_weights_to_replay(event_ctx, replay_with_context_assets),
            buy_sell_decisions=_align_context_weights_to_replay(decision_ctx, replay_with_context_assets),
        )
    _store_strategy_replay_context(context)
    return context


def _ensure_daily_portfolio_replay_context(horizon_start: pd.Timestamp | None = None) -> DashboardReplayContext:
    """Build the one daily replay context used by Portfolio replay-facing surfaces."""
    if horizon_start is not None:
        cached_context = _valid_cached_ytd_replay_context(horizon_start)
        if cached_context is not None:
            return cached_context
    with st.spinner("Building daily portfolio replay source..."):
        context = _build_dashboard_strategy_replay_context(horizon_start=horizon_start)
    if context.status == "ready" and context.sampling == "daily" and len(context.replay_dates) >= 2:
        st.session_state[STRATEGY_REPLAY_YTD_CONTEXT_KEY] = context
    else:
        st.session_state.pop(STRATEGY_REPLAY_YTD_CONTEXT_KEY, None)
        st.session_state.pop(STRATEGY_REPLAY_LATEST_WEIGHTS_KEY, None)
        st.session_state.pop(STRATEGY_REPLAY_CACHE_SIGNATURE_KEY, None)
    return context


def _render_strategy_replay_section(full_context: DashboardReplayContext) -> None:
    """Strategy Replay: transitional bundle viewer for selected-method replay."""
    st.subheader("Strategy Replay")

    # Display which method/cap is being replayed (read-only from main controls)
    st.caption(f"Replaying: {full_context.method} | max_weight={full_context.max_weight:.0%} (from main optimizer controls)")

    if full_context.source_mode == "saved_artifact":
        st.caption("Replay source: saved artifact.")
    if full_context.source_mode == "transitional_build":
        st.caption("Replay source: transitional build (saved artifact unavailable or stale).")
    if full_context.source_mode == "unavailable":
        st.caption("Replay source: saved artifact unavailable.")

    if full_context.status == "input_unavailable" and full_context.reason == "price_data_unavailable":
        st.info("Strategy Replay requires price data. Load parquet data to enable.")
        return
    if full_context.status == "input_unavailable" and full_context.reason == "no_assets_selected_for_replay":
        st.info("No assets selected for replay. Select assets in the optimizer above.")
        return
    if full_context.status == "input_unavailable" and full_context.reason == "portfolio_replay_selection_unavailable":
        st.info("Replay selection unavailable. Use the optimizer controls above to select a valid replay universe.")
        return
    if full_context.status in ("input_unavailable", "failed"):
        st.warning(full_context.reason)
        return
    if full_context.status == "stale":
        st.warning(full_context.reason or "Strategy replay source is stale.")
        return
    replay_df = full_context.replay_df
    if replay_df.empty:
        st.info("No strategy replay data produced.")
        return

    source_label = full_context.source_label
    st.caption(f"Source: {source_label}")
    st.caption(f"Replay identity: {_replay_identity_caption(full_context)}")

    # Coverage-gap warning: if selected horizon starts before strategy input coverage
    horizon_start = st.session_state.get("_portfolio_horizon_start")
    coverage_start = full_context.input_coverage_start
    if horizon_start is not None and coverage_start:
        coverage_ts = pd.Timestamp(coverage_start)
        if pd.notna(coverage_ts) and pd.Timestamp(horizon_start) < coverage_ts:
            st.info(
                f"Strategy input coverage starts {coverage_ts.strftime('%Y-%m-%d')}; "
                f"earlier dates are cash/input unavailable."
            )

    # Show unsupported/failed status explicitly
    if "status" in replay_df.columns:
        failed = replay_df[replay_df["status"] == "cash_closed"]
        if not failed.empty:
            unique_reasons = failed["reason"].unique()
            for reason in unique_reasons[:3]:
                st.warning(f"Replay status: cash_closed - {reason}")

    # ── Strategy Replay Timeline ──
    timeline_df, timeline_sampling = _sample_replay_timeline_from_daily(replay_df)
    _sampling_tag = f" | display sample: {timeline_sampling}" if timeline_sampling != "daily" else ""
    st.markdown(f"**Strategy Replay Timeline** *(source: {source_label}{_sampling_tag})*")
    _render_replay_timeline_chart(timeline_df)

    # ── Latest Snapshot ──
    latest_rows = full_context.latest_snapshot.copy()
    latest_date = latest_rows["date"].max() if not latest_rows.empty else pd.NaT
    if not latest_rows.empty:
        required_snapshot_cols = {"date", "ticker", "target_weight"}
        if required_snapshot_cols.issubset(latest_rows.columns):
            optional_cols = [c for c in ["context_role", "cap_used", "cap_source", "source", "status"] if c in latest_rows.columns]
            snap_df = latest_rows[["ticker", "target_weight", *optional_cols]].copy()
            snap_df = snap_df.rename(
                columns={
                    "ticker": "Ticker",
                    "target_weight": "Replay Weight",
                    "context_role": "Context Role",
                }
            )
            snap_df["Replay Weight"] = pd.to_numeric(snap_df["Replay Weight"], errors="coerce").fillna(0.0)
            snap_df = snap_df[snap_df["Replay Weight"] > 0].sort_values("Replay Weight", ascending=False)
            title_date = pd.Timestamp(latest_date).strftime("%Y-%m-%d") if pd.notna(latest_date) else "unknown"
            st.markdown(f"**Latest Snapshot** ({title_date})")
            st.dataframe(snap_df.style.format({"Replay Weight": "{:.2%}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Latest replay snapshot unavailable for this source schema.")

    # Historical Replay Lifecycle Events (same bundle identity as daily replay rows)
    event_df = full_context.event_annotations.copy()
    required_event_cols = {"date", "ticker", "action"}
    if not event_df.empty and required_event_cols.issubset(event_df.columns):
        event_df = event_df[event_df["action"].isin(("ENTER", "EXIT", "ADJUST"))].copy()
        event_df["date"] = pd.to_datetime(event_df["date"], errors="coerce")
        horizon_start = st.session_state.get("_portfolio_horizon_start")
        if horizon_start is not None:
            event_df = event_df[event_df["date"] >= pd.Timestamp(horizon_start)]
        event_df = event_df[event_df["date"].notna()].sort_values("date", ascending=False)
    else:
        event_df = pd.DataFrame()
    if not event_df.empty:
        st.markdown(f"**Historical Replay Lifecycle Events** *(replay: {full_context.method}; source: {full_context.source_id or full_context.source_mode})*")
        _render_event_ledger_chart(event_df, list(event_df["ticker"].unique()))
    else:
        st.info("No replay lifecycle events in this replay window.")

    # Replay Decision-Code Audit Log (same bundle.decision_rows source)
    decision_df = full_context.buy_sell_decisions.copy()
    if not decision_df.empty:
        if "date" in decision_df.columns:
            decision_df["date"] = pd.to_datetime(decision_df["date"], errors="coerce")
            horizon_start = st.session_state.get("_portfolio_horizon_start")
            if horizon_start is not None:
                decision_df = decision_df[decision_df["date"] >= pd.Timestamp(horizon_start)]
            decision_df = decision_df.sort_values("date", ascending=False)
        dec_cols = [
            c for c in ["date", "ticker", "context_role", "action", "reason", "target_weight", "audit_weight"]
            if c in decision_df.columns
        ]
        latest_trades = decision_df[decision_df.get("action", pd.Series(dtype=object)).isin(("BUY", "SELL"))].head(9).copy()
        if not latest_trades.empty:
            st.markdown("**Latest Replay Decision-Code Changes**")
            latest_show = latest_trades[dec_cols].copy()
            if "date" in latest_show.columns:
                latest_show["date"] = latest_show["date"].dt.strftime("%Y-%m-%d")
            for weight_col in ["target_weight", "audit_weight"]:
                if weight_col in latest_show.columns:
                    latest_show[weight_col] = pd.to_numeric(latest_show[weight_col], errors="coerce").map("{:.1%}".format)
            latest_show = latest_show.rename(
                columns={
                    "context_role": "Context Role",
                    "target_weight": "Replay Target",
                    "audit_weight": "Aux Audit Wt",
                }
            )
            st.dataframe(latest_show, use_container_width=True, hide_index=True)
        with st.expander(f"**Replay Decision-Code Audit Log** ({len(decision_df)} rows)", expanded=False):
            st.caption("Bundle decision context (replay audit only - not live orders or trade signals).")
            dec_show = decision_df[dec_cols].copy()
            if "date" in dec_show.columns:
                dec_show["date"] = dec_show["date"].dt.strftime("%Y-%m-%d")
            for weight_col in ["target_weight", "audit_weight"]:
                if weight_col in dec_show.columns:
                    dec_show[weight_col] = pd.to_numeric(dec_show[weight_col], errors="coerce").map("{:.1%}".format)
            dec_show = dec_show.rename(
                columns={
                    "context_role": "Context Role",
                    "target_weight": "Replay Target",
                    "audit_weight": "Aux Audit Wt",
                }
            )
            st.dataframe(dec_show, use_container_width=True, hide_index=True)


def _render_replay_timeline_chart(replay_df: pd.DataFrame) -> None:
    """Render target weights as one stacked replay allocation timeline."""
    if replay_df.empty or "date" not in replay_df.columns or "ticker" not in replay_df.columns:
        st.info("No replay target weights available.")
        return
    if "target_weight" not in replay_df.columns:
        st.info("No replay target weights available.")
        return
    replay_df = replay_df.copy()
    replay_df["date"] = pd.to_datetime(replay_df["date"], errors="coerce")
    replay_df["ticker"] = replay_df["ticker"].astype(str).str.upper().str.strip()
    replay_df["target_weight"] = pd.to_numeric(replay_df.get("target_weight"), errors="coerce").fillna(0.0).clip(lower=0.0)
    replay_df = replay_df[(replay_df["date"].notna()) & (replay_df["ticker"] != "")]
    if replay_df.empty:
        st.info("No replay target weights available.")
        return
    weights = (
        replay_df.pivot_table(
            index="date",
            columns="ticker",
            values="target_weight",
            aggfunc="last",
        )
        .sort_index()
        .fillna(0.0)
    )
    if weights.empty:
        st.info("No replay target weights available.")
        return
    latest = weights.iloc[-1].drop(labels=["CASH"], errors="ignore")
    active_days = (weights.drop(columns=["CASH"], errors="ignore") > 0).sum()
    ordered_equities = sorted(
        latest.index,
        key=lambda ticker: (float(latest.get(ticker, 0.0)), int(active_days.get(ticker, 0)), str(ticker)),
        reverse=True,
    )
    tickers = [ticker for ticker in ordered_equities if float(weights[ticker].abs().max()) > 0.0]
    if "CASH" in weights.columns:
        tickers.append("CASH")
    fig = go.Figure()
    for ticker in tickers:
        if ticker not in weights.columns:
            continue
        is_cash = ticker == "CASH"
        fig.add_trace(go.Scatter(
            x=weights.index,
            y=weights[ticker],
            mode="lines",
            name=ticker,
            stackgroup="weights",
            line=dict(shape="hv", width=1.5, color="#8E8E8E") if is_cash else dict(shape="hv", width=1.6),
            fillcolor="rgba(142,142,142,0.28)" if is_cash else None,
            opacity=0.72 if is_cash else 0.92,
            hovertemplate=(
                f"<b>{ticker}</b><br>" + "%{x|%Y-%m-%d}"
                "<br>Replay Target: %{y:.1%}<extra></extra>"
            ),
        ))
    fig.update_layout(
        template="plotly_dark",
        height=340,
        yaxis_title="Target Weight",
        yaxis_tickformat=".0%",
        yaxis=dict(range=[0, 1], tickformat=".0%"),
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=30, b=30),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_policy_target_freshness() -> None:
    """Show freshness metadata for the policy target history artifact."""
    import datetime

    path = RULE100_SOFTMAX_V1_HISTORY_PATH
    if not path.exists() or path.stat().st_size == 0:
        st.warning(
            "⚠️ Policy target history artifact missing or empty. "
            f"Expected: {path}. Rebuild required."
        )
        return
    mtime = datetime.datetime.fromtimestamp(path.stat().st_mtime)
    age_hours = (datetime.datetime.now() - mtime).total_seconds() / 3600
    freshness_label = f"Generated: {mtime:%Y-%m-%d %H:%M} ({age_hours:.1f}h ago)"
    if age_hours > 48:
        st.warning(f"⚠️ Policy target history is stale. {freshness_label} | Path: {path}")
    else:
        st.caption(f"📄 {path.name} | {freshness_label}")


def _render_policy_target_timeline(hist: pd.DataFrame, selected_tickers: list, *, show_cash: bool = False, max_weight: float = 0.35) -> None:
    """Render daily policy target weight chart and table from v1 history CSV."""
    fig = go.Figure()
    for ticker in selected_tickers:
        tk = hist[hist["ticker"].str.upper().str.strip() == ticker]
        if tk.empty:
            continue
        target_wt = pd.to_numeric(tk["softmax_v1_target_weight"], errors="coerce").fillna(0.0)
        fig.add_trace(go.Scatter(
            x=tk["date"],
            y=target_wt,
            mode="lines+markers",
            name=ticker,
            marker=dict(size=4),
            hovertemplate=(
                "<b>" + ticker + "</b><br>%{x|%Y-%m-%d}"
                "<br>Policy Target: %{y:.1%}<extra></extra>"
            ),
        ))
    # CASH trace: residual weight per date
    if show_cash and "softmax_v1_cash_residual" in hist.columns:
        cash_by_date = hist.groupby("date")["softmax_v1_cash_residual"].first().reset_index()
        cash_wt = pd.to_numeric(cash_by_date["softmax_v1_cash_residual"], errors="coerce").fillna(1.0)
        fig.add_trace(go.Scatter(
            x=cash_by_date["date"],
            y=cash_wt,
            mode="lines",
            name="CASH",
            line=dict(dash="dot", color="#888888"),
            hovertemplate="<b>CASH</b><br>%{x|%Y-%m-%d}<br>Weight: %{y:.1%}<extra></extra>",
        ))
    fig.update_layout(
        template="plotly_dark",
        height=300,
        yaxis_title="Policy Target Weight",
        yaxis_tickformat=".0%",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=30, b=30),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Policy Target Table
    with st.expander("Policy Target History"):
        tbl = hist[["date", "ticker", "event_weight", "softmax_v1_target_weight",
                     "softmax_v1_cash_residual", "eligibility_reason"]].copy()
        tbl["event_weight"] = pd.to_numeric(tbl["event_weight"], errors="coerce")
        tbl["softmax_v1_target_weight"] = pd.to_numeric(tbl["softmax_v1_target_weight"], errors="coerce")
        tbl["softmax_v1_cash_residual"] = pd.to_numeric(tbl["softmax_v1_cash_residual"], errors="coerce")
        tbl["target_minus_event"] = tbl["softmax_v1_target_weight"] - tbl["event_weight"]
        tbl["date"] = tbl["date"].dt.strftime("%Y-%m-%d")
        tbl = tbl.rename(columns={
            "date": "Date",
            "ticker": "Ticker",
            "event_weight": "Lifecycle Event Wt",
            "softmax_v1_target_weight": "Policy Target Weight",
            "softmax_v1_cash_residual": "Cash Residual",
            "eligibility_reason": "Eligibility Reason",
            "target_minus_event": "Target - Event",
        })
        tbl = tbl[["Date", "Ticker", "Policy Target Weight", "Lifecycle Event Wt",
                    "Target - Event", "Cash Residual", "Eligibility Reason"]]
        st.dataframe(tbl, use_container_width=True, hide_index=True)


def _derive_replay_trade_events(replay_df: pd.DataFrame) -> pd.DataFrame:
    """Derive ENTER/EXIT trade events from replay_df target_weight transitions.

    Returns a DataFrame with columns: date, ticker, action, weight, reason
    compatible with _render_event_ledger_chart.
    """
    if replay_df.empty or "target_weight" not in replay_df.columns:
        return pd.DataFrame(columns=["date", "ticker", "action", "weight", "reason"])
    # Exclude CASH rows
    df = replay_df[replay_df["ticker"] != "CASH"].copy()
    if df.empty:
        return pd.DataFrame(columns=["date", "ticker", "action", "weight", "reason"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["ticker", "date"])
    # Pivot: for each ticker, get previous weight
    df["prev_weight"] = df.groupby("ticker")["target_weight"].shift(1).fillna(0.0)
    # ENTER: prev == 0 and current > 0
    enters = df[(df["prev_weight"] == 0) & (df["target_weight"] > 0)].copy()
    enters["action"] = "ENTER"
    enters["weight"] = enters["target_weight"]
    enters["reason"] = enters["target_weight"].map(lambda v: f"replay target_weight 0→{v:.1%}")
    # EXIT: prev > 0 and current == 0
    exits = df[(df["prev_weight"] > 0) & (df["target_weight"] == 0)].copy()
    exits["action"] = "EXIT"
    exits["weight"] = exits["prev_weight"]
    exits["reason"] = exits["prev_weight"].map(lambda v: f"replay target_weight {v:.1%}→0")
    events = pd.concat([enters, exits], ignore_index=True)
    if events.empty:
        return pd.DataFrame(columns=["date", "ticker", "action", "weight", "reason"])
    return events[["date", "ticker", "action", "weight", "reason"]].sort_values("date", ascending=False).reset_index(drop=True)


def _numeric_weight_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column in frame.columns:
        return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return pd.Series(0.0, index=frame.index, dtype="float64")


def _render_event_ledger_chart(df_filtered: pd.DataFrame, selected_tickers: list) -> None:
    """Render replay lifecycle-code markers from the event ledger."""
    fig = go.Figure()

    enters = df_filtered[df_filtered["action"] == "ENTER"]
    exits = df_filtered[df_filtered["action"] == "EXIT"]

    if not enters.empty:
        if "target_weight" in enters.columns:
            enter_target = _numeric_weight_series(enters, "target_weight")
        elif "rule100_softmax_v1_target_weight" in enters.columns:
            enter_target = _numeric_weight_series(enters, "rule100_softmax_v1_target_weight")
        else:
            enter_target = pd.Series(0.0, index=enters.index, dtype="float64")
        enter_audit_wt = _numeric_weight_series(enters, "audit_weight")
        enter_customdata = pd.DataFrame({
            "target": enter_target,
            "audit_wt": enter_audit_wt,
            "event_code": enters["action"].values,
            "reason": enters["reason"].values,
        }).values
        fig.add_trace(go.Scatter(
            x=enters["date"],
            y=enters["ticker"],
            mode="markers",
            name="ENTER",
            marker=dict(symbol="triangle-up", size=14, color="#00FFAA"),
            hovertemplate=(
                "<b>%{y}</b><br>Lifecycle open code %{x|%Y-%m-%d}"
                "<br>Policy Target: %{customdata[0]:.1%} (Replay Target)"
                "<br>Lifecycle Event Wt: %{customdata[1]:.1%} (Aux Audit Wt)"
                "<br>Decision Code: %{customdata[2]}"
                "<br>Reason: %{customdata[3]}<extra></extra>"
            ),
            customdata=enter_customdata,
        ))

    if not exits.empty:
        exit_reason = exits["reason"].values if "reason" in exits.columns else [""] * len(exits)
        exit_rating = exits["rating"].values if "rating" in exits.columns else ["—"] * len(exits)
        exit_target = _numeric_weight_series(exits, "target_weight")
        exit_audit_wt = _numeric_weight_series(exits, "audit_weight")
        fig.add_trace(go.Scatter(
            x=exits["date"],
            y=exits["ticker"],
            mode="markers",
            name="EXIT",
            marker=dict(symbol="triangle-down", size=14, color="#FF4444"),
            hovertemplate=(
                "<b>%{y}</b><br>Lifecycle close code %{x|%Y-%m-%d}"
                "<br>Decision Code: lifecycle close"
                "<br>Policy Target: %{customdata[2]:.1%} (Replay Target)"
                "<br>Lifecycle Event Wt: %{customdata[3]:.1%} (Aux Audit Wt)"
                "<br>Rating: %{customdata[0]}"
                "<br>Reason: %{customdata[1]}<extra></extra>"
            ),
            customdata=list(zip(exit_rating, exit_reason, exit_target, exit_audit_wt)),
        ))

    fig.update_layout(
        template="plotly_dark",
        height=max(200, 60 * len(selected_tickers)),
        yaxis_title="",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=80, r=20, t=30, b=30),
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)





def _render_portfolio_builder_placeholder():
    """Render optimizer fallback when fundamentals unavailable."""
    base_df = _ensure_modular_strategy_state()
    st.info(
        "Portfolio optimization requires fundamentals data. "
        "Run fundamentals updater to enable, or use Research Lab / Modular Strategies."
    )

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
        st.markdown(f"**Research filter expression:** {logic_str}")

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

        # --- 7. Rows Passing Research Filter Readout ---
        st.divider()
        st.subheader("Rows Passing Research Filter")
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


def _render_command_center_page() -> None:
    _render_placeholder_page("Command Center")


def _render_placeholder_page(title: str) -> None:
    st.header(title)
    st.info("DASH-1 shell placeholder. Content design is held for a later approved dashboard phase.")


def _render_portfolio_allocation_page() -> None:
    """Render the sole default certified portfolio authority (one active decision)."""

    st.header(PORTFOLIO_PAGE_TITLE)
    st.caption(
        "V2-B0A local-source abstention is the active product gate on this tip. "
        "One certified decision path. Default current is local research-card "
        "preflight HOLD_FOR_EVIDENCE mapped to paper NO_POSITION after a "
        "certified source-authority abstention (not real external admission). "
        "E0B G08 remains invalidated observation smoke (count 0). Score 39 frozen. "
        "Legacy replay/optimizer non-certifying; F1C dual bundle evidence-only."
    )
    try:
        render_gv_fs0_current_decision(st)
    except GvFs0PresentationError as exc:
        # Fail closed: explicit unavailable authority. Never fall back to F1C dual
        # bundle, replay, optimizer, or any non-certifying surface.
        st.error("Certified decision unavailable")
        st.caption(f"Authority refused: {exc}")
    # V2-B0 admission result surface (block/abstention is a valid functional outcome).
    render_v2_b0_surface(st)
    # Optional E0B surface; Attempt-1 invalidation keeps observed count at 0.
    render_e0b_dv1_surface(st)


def _render_discovery_page() -> None:
    st.header(DISCOVERY_PAGE_TITLE)
    render_discovery_page(
        render_opportunities=_render_opportunities_page,
        render_confluence_scan=_render_daily_scan_section,
    )


def _render_strategy_page() -> None:
    st.header(STRATEGY_PAGE_TITLE)
    render_strategy_page(
        render_modular_strategies=_render_modular_strategies_section,
        render_backtest_lab=_render_backtest_lab_section,
        render_pead_validation_evidence=render_pead_validation_evidence,
    )


def _render_research_lab_page() -> None:
    st.header("Research Lab")
    selected_section = st.radio(
        "Research workflow",
        ["Daily Scan", "Backtest Lab", "Modular Strategies"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_section == "Daily Scan":
        _render_daily_scan_section()
    elif selected_section == "Backtest Lab":
        _render_backtest_lab_section()
    else:
        _render_modular_strategies_section()


def _render_settings_ops_page() -> None:
    st.header("Settings & Ops")
    selected_section = st.radio(
        "Ops workflow",
        ["Data Health", "Drift Monitor"],
        horizontal=True,
        label_visibility="collapsed",
    )
    if selected_section == "Data Health":
        _render_data_health_section()
    else:
        _render_drift_monitor_section()


page = build_dashboard_navigation(
    {
        PORTFOLIO_PAGE_TITLE: _render_portfolio_allocation_page,
        DISCOVERY_PAGE_TITLE: _render_discovery_page,
        STRATEGY_PAGE_TITLE: _render_strategy_page,
    }
)
page.run()

