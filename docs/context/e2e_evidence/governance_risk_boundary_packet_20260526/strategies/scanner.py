from __future__ import annotations

import math
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd


TECHNICAL_DEFAULT = {
    "price": 0.0,
    "ema21": 0.0,
    "sma50": 0.0,
    "sma200": 0.0,
    "atr": 0.0,
    "convexity": 1.0,
}


def _coerce_float(value: Any, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(default)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return float(parsed)


def _last_float(series: pd.Series, *, default: float = 0.0) -> float:
    if series.empty:
        return float(default)
    return _coerce_float(series.iloc[-1], default=default)


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return float(parsed)


def _finite_numeric_series(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.replace([np.inf, -np.inf], np.nan)


def _row_value(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    try:
        return row[key]
    except Exception:
        return default


def calculate_macro_score(close_data: pd.DataFrame) -> dict[str, int] | None:
    """Calculate dashboard macro score from already-fetched close series."""
    try:
        if close_data.empty or len(close_data) < 200:
            return None

        tnx_raw = _finite_numeric_series(close_data["^TNX"])
        vwehx_raw = _finite_numeric_series(close_data["VWEHX"])
        vfisx_raw = _finite_numeric_series(close_data["VFISX"])
        tnx = tnx_raw.dropna()
        vwehx = vwehx_raw.dropna()
        vfisx = vfisx_raw.dropna()

        rate_val = 50.0
        if len(tnx) >= 63:
            tnx_now = _finite_float(tnx_raw.iloc[-1])
            tnx_then = _finite_float(tnx.iloc[-63])
            if tnx_now is None or tnx_then is None:
                return None
            vel = tnx_now - tnx_then
            if vel <= 0.0:
                rate_val = 50.0
            elif vel >= 0.50:
                rate_val = 0.0
            else:
                rate_val = 50.0 * ((0.50 - vel) / 0.50)

        credit_val = 50.0
        common_idx = vwehx_raw.index.intersection(vfisx_raw.index)
        if len(common_idx) >= 200:
            credit_frame = pd.DataFrame(
                {"vwehx": vwehx_raw.loc[common_idx], "vfisx": vfisx_raw.loc[common_idx]}
            )
            latest_credit = credit_frame.iloc[-1]
            latest_vwehx = _finite_float(latest_credit["vwehx"])
            latest_vfisx = _finite_float(latest_credit["vfisx"])
            if latest_vwehx is None or latest_vfisx is None or latest_vfisx <= 0.0:
                return None
            credit_frame = credit_frame.dropna()
            credit_frame = credit_frame[credit_frame["vfisx"] > 0.0]
            if len(credit_frame) < 200:
                return None
            ratio = (credit_frame["vwehx"] / credit_frame["vfisx"]).replace([np.inf, -np.inf], np.nan).dropna()
            if len(ratio) < 200:
                return None
            sma200 = _finite_float(ratio.rolling(200).mean().iloc[-1])
            curr_ratio = _finite_float(ratio.iloc[-1])
            if sma200 is None or curr_ratio is None or sma200 == 0.0:
                return None
            cdist = ((curr_ratio - sma200) / sma200) * 100
            if not math.isfinite(cdist):
                return None
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
            "credit_score": round(credit_val),
        }
    except Exception:
        return None


def classify_breadth_status(close_data: pd.DataFrame) -> tuple[str, str]:
    """Classify RSP/SPY breadth from already-fetched close series."""
    try:
        if close_data.empty or len(close_data) < 50:
            return "UNKNOWN (No Data)", "#888"

        spy = _finite_numeric_series(close_data["SPY"])
        rsp = _finite_numeric_series(close_data["RSP"])

        spy_now = _finite_float(spy.iloc[-1])
        spy_sma50 = _finite_float(spy.rolling(window=50).mean().iloc[-1])
        rsp_now = _finite_float(rsp.iloc[-1])
        rsp_sma50 = _finite_float(rsp.rolling(window=50).mean().iloc[-1])
        if None in (spy_now, spy_sma50, rsp_now, rsp_sma50):
            return "UNKNOWN (No Data)", "#888"

        if rsp_now > rsp_sma50:
            return "HEALTHY (Broad)", "#00FFAA"
        if (spy_now > spy_sma50) and (rsp_now < rsp_sma50):
            return "DIVERGENCE (Thinning)", "#FFD700"
        return "WEAK (Correction)", "#ff4444"
    except Exception:
        return "UNKNOWN (Error)", "#888"


def calculate_price_technical(hist: pd.DataFrame) -> dict[str, float]:
    """Calculate one ticker's technical fields from OHLC history."""
    if hist is None or hist.empty:
        return dict(TECHNICAL_DEFAULT)

    try:
        clean_hist = hist.dropna()
        if len(clean_hist) >= 14:
            close = clean_hist["Close"]
            current = _last_float(close)
            ema21 = _last_float(close.ewm(span=21, adjust=False).mean())
            sma50 = _last_float(close.rolling(window=50, min_periods=10).mean())
            sma200 = _last_float(close.rolling(window=200, min_periods=10).mean())

            high_low = clean_hist["High"] - clean_hist["Low"]
            high_close = (clean_hist["High"] - close.shift(1)).abs()
            low_close = (clean_hist["Low"] - close.shift(1)).abs()
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = _last_float(true_range.ewm(alpha=1 / 14, adjust=False).mean())

            ema10 = close.ewm(span=10, adjust=False).mean()
            slope = ema10.diff()
            avg_slope = _last_float(slope.rolling(window=20).mean(), default=1.0)
            curr_slope = _last_float(slope, default=1.0)
            if avg_slope <= 0:
                convexity = 1.0
            else:
                convexity = curr_slope / avg_slope

            return {
                "price": current,
                "ema21": ema21,
                "sma50": sma50,
                "sma200": sma200,
                "atr": atr,
                "convexity": convexity,
            }

        current = _last_float(clean_hist["Close"]) if "Close" in clean_hist else 0.0
        return {
            "price": current,
            "ema21": current,
            "sma50": current,
            "sma200": current,
            "atr": 0.0,
            "convexity": 1.0,
        }
    except Exception:
        return dict(TECHNICAL_DEFAULT)


def _history_for_ticker(hist_all: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if isinstance(hist_all.columns, pd.MultiIndex):
        return hist_all.xs(ticker, level=1, axis=1).dropna()
    return hist_all.dropna()


def build_price_technicals(hist_all: pd.DataFrame, tickers: Sequence[str]) -> dict[str, dict[str, float]]:
    """Build ticker -> technical fields from a yfinance-style history frame."""
    data: dict[str, dict[str, float]] = {}
    for ticker in tickers:
        try:
            hist = _history_for_ticker(hist_all, str(ticker))
            data[str(ticker)] = calculate_price_technical(hist)
        except Exception:
            data[str(ticker)] = dict(TECHNICAL_DEFAULT)
    return data


def classify_cluster(current_price: float, atr: float) -> str:
    if current_price <= 0:
        return "Unknown"
    atr_ratio = atr / current_price
    if atr_ratio < 0.025:
        return "I. Heavy"
    if atr_ratio <= 0.045:
        return "II. Sprinter"
    return "III. Scout"


def calculate_sovereign_entry_price(row: Any, macro_score: float) -> pd.Series:
    curr = _coerce_float(_row_value(row, "Current_Price"))
    ema21 = _coerce_float(_row_value(row, "EMA21"))
    sma50 = _coerce_float(_row_value(row, "SMA50"))
    sma200 = _coerce_float(_row_value(row, "SMA200"))
    score = _coerce_float(_row_value(row, "Score"))
    convexity = _coerce_float(_row_value(row, "Convexity"), default=1.0)
    cluster = str(_row_value(row, "Cluster_Type", "")).upper()

    if curr <= 0:
        return pd.Series([0.0, "N/A", 0.0, 0.0, 0.0])

    base_support = sma50
    rationale = "50-SMA (Standard)"

    if macro_score >= 80 and score >= 95 and convexity <= 1.5:
        base_support = ema21
        rationale = "21-EMA (God Mode)"

    if convexity > 1.5:
        base_support = sma50
        rationale = "50-SMA (Mania Protection)"

    if macro_score < 50:
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
            return pd.Series([0.0, "NO SUPPORT", 0.0, 0.0, base_support])

    if "SCOUT" in cluster:
        max_flush = 0.16
    elif "SPRINTER" in cluster:
        max_flush = 0.11
    else:
        max_flush = 0.05

    if score >= 95:
        premium = 0.05
    elif score >= 90:
        premium = 0.03
    else:
        premium = 0.00

    net_buffer = max(0, max_flush - premium)
    final_entry_price = base_support * (1 - net_buffer)
    return pd.Series([final_entry_price, rationale, max_flush, premium, base_support])


def calculate_support_distance(row: Any) -> float:
    entry_price = _coerce_float(_row_value(row, "Entry_Price"))
    current_price = _coerce_float(_row_value(row, "Current_Price"))
    if entry_price <= 0:
        return 0.0
    return ((current_price / entry_price) - 1) * 100


def calculate_tactics(row: Any, macro_risk: bool) -> tuple[float, str, str, float]:
    atr = _coerce_float(_row_value(row, "ATR"))
    price = _coerce_float(_row_value(row, "Current_Price"))
    dist_pct = _coerce_float(_row_value(row, "Tech_Support_Dist"))
    entry = _coerce_float(_row_value(row, "Entry_Price"))
    score = _coerce_float(_row_value(row, "Score"))
    convexity = _coerce_float(_row_value(row, "Convexity"), default=1.0)
    cluster = str(_row_value(row, "Cluster_Type", ""))

    if atr <= 0 or price <= 0:
        return entry * 0.95, "N/A", cluster, 3.0

    if "I. HEAVY" in cluster.upper():
        limit = 8.2
    elif "II. SPRINTER" in cluster.upper():
        limit = 8.8
    else:
        limit = 12.3

    active_limit = 6.0 if macro_risk else limit

    if score >= 90:
        accel_factor = max(0, convexity - 1.0)
        stretch_factor = max(0, dist_pct) / limit if limit > 0 else 0
        penalty_weight = 0.5 * accel_factor * stretch_factor
        multiplier = 3.0 / (1.0 + penalty_weight)
        multiplier = max(1.5, min(3.0, multiplier))

        if dist_pct > active_limit and multiplier < 2.5:
            return (
                price - (multiplier * atr),
                f"🚀 SUPER CYCLE | ⚠️ PARABOLIC MANIA -> TRAIL ({multiplier:.1f}x)",
                cluster,
                multiplier,
            )
        return (
            entry - (multiplier * atr),
            f"🚀 SUPER CYCLE | LINEAR TREND -> KINETIC TRAIL ({multiplier:.1f}x)",
            cluster,
            multiplier,
        )

    return entry - (3.0 * atr), "🛡️ STANDARD TREND | WIDE STOP ONLY (3.0x)", cluster, 3.0


def generate_proxy_signal(
    row: Any,
    proxy_data: Mapping[str, Any],
    proxy_db: Mapping[str, Mapping[str, Any]],
) -> pd.Series:
    sector = _row_value(row, "Sector", "Software")
    score = _coerce_float(_row_value(row, "Score"))
    price_dist = _coerce_float(_row_value(row, "Tech_Support_Dist"))

    fallback_proxy = proxy_db.get("Software", {})
    proxy_info = proxy_db.get(str(sector), fallback_proxy)

    p_type = proxy_info.get("type") if proxy_info.get("type") != "None" else "[NO PROXY]"
    p_conf = proxy_info.get("conf") if proxy_info.get("type") != "None" else ""

    p_content = "[NO DATA]"
    actual_val = 0.0
    proxy_key = proxy_info.get("key")
    if proxy_key and proxy_key in proxy_data:
        proxy_val_data = proxy_data[proxy_key]
        raw_proxy_val = proxy_val_data.get("val") if isinstance(proxy_val_data, Mapping) else proxy_val_data
        actual_val = _coerce_float(raw_proxy_val, default=0.0)
        span = (
            proxy_val_data.get("span", proxy_info.get("span", ""))
            if isinstance(proxy_val_data, Mapping)
            else proxy_info.get("span", "")
        )
        p_content = f"{proxy_info.get('name')} ({span}): {actual_val * 100:+.1f}%"

        if proxy_info.get("type") == "Individual + Sector" and "sec_name" in proxy_info:
            sec_key = proxy_info.get("sec_key")
            if sec_key in proxy_data:
                sec_val_data = proxy_data[sec_key]
                raw_sec_val = sec_val_data.get("val") if isinstance(sec_val_data, Mapping) else sec_val_data
                sec_val = _coerce_float(raw_sec_val, default=0.0)
                sec_span = (
                    sec_val_data.get("span", proxy_info.get("sec_span", ""))
                    if isinstance(sec_val_data, Mapping)
                    else proxy_info.get("sec_span", "")
                )
                p_content += f" | {proxy_info.get('sec_name')} ({sec_span}): {sec_val * 100:+.1f}%"
            else:
                p_content += f" | {proxy_info.get('sec_name')} ({proxy_info.get('sec_span', '')}): Syncing"
    elif proxy_info.get("name") != "[NO PROXY]":
        p_content = f"{proxy_info.get('name')}: Awaiting Sync"

    p_signal = "N/A"
    if proxy_info.get("type") != "None":
        proxy_is_strong = actual_val > 0.02
        proxy_is_weak = actual_val <= 0.02
        price_is_strong = price_dist > 5.0
        price_is_weak = price_dist <= 5.0

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


def generate_rating(row: Any) -> str:
    action = str(_row_value(row, "Action", ""))
    score = _coerce_float(_row_value(row, "Score"))
    dist = _coerce_float(_row_value(row, "Tech_Support_Dist"))
    support = _coerce_float(_row_value(row, "Support_Price"))
    label = str(_row_value(row, "Support_Label", ""))
    proxy_type = str(_row_value(row, "Proxy_Type", ""))
    has_proxy = "[NO PROXY]" not in proxy_type
    warning = str(_row_value(row, "Tactical_Warning", ""))
    signal = str(_row_value(row, "Proxy_Signal", ""))

    if "KILL" in action:
        return "EXIT (Macro/Sector Rot)"

    if "PARABOLIC" in warning:
        return "EXIT / TRAIL TIGHT (Mania Top)"

    if "STRETCH" in warning:
        return "WAIT (Terminal Stretch)"

    if score == 100:
        if not has_proxy:
            return "WATCH (Miss Proxy Cap)"
        if dist > 5.0:
            label_short = label.split(" (")[0]
            return f"WATCH (Wait for {label_short}: ${support:.2f})"
        if signal == "COILED SPRING":
            return "ENTER: STRONG BUY (Coiled)"
        if dist >= -2.0:
            return "ENTER: BUY (Baseline)"
        return "ENTER: BUY"

    if score >= 90:
        return "WATCH / HOLD"

    return "IGNORE"


def calculate_leverage(row: Any, macro_score: float) -> str:
    rating = str(_row_value(row, "Rating", ""))
    convexity = _coerce_float(_row_value(row, "Convexity"), default=1.0)
    if "STRONG BUY" in rating:
        if macro_score >= 80 and convexity <= 1.5:
            return "LEAPs"
        return "Avoid"
    return ""


def enrich_scan_frame(
    df_scan: pd.DataFrame,
    *,
    technicals: Mapping[str, Mapping[str, float]],
    sector_map: Mapping[str, str],
    proxy_db: Mapping[str, Mapping[str, Any]],
    proxy_data: Mapping[str, Any],
    macro: Mapping[str, Any] | None,
) -> pd.DataFrame:
    """Apply deterministic dashboard scanner enrichment to an alpha scan frame."""
    result = df_scan.copy()

    result["Current_Price"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("price", 0.0))
    result["EMA21"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("ema21", 0.0))
    result["SMA50"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("sma50", 0.0))
    result["SMA200"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("sma200", 0.0))
    result["ATR"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("atr", 0.0))
    result["Convexity"] = result["Ticker"].apply(lambda x: technicals.get(x, {}).get("convexity", 1.0))

    result["Sector"] = result["Ticker"].map(sector_map).fillna("Unknown")

    macro_score = _coerce_float(macro.get("score") if macro else 50, default=50.0)
    macro_risk = macro_score < 50

    result["Cluster_Type"] = result.apply(
        lambda row: classify_cluster(row["Current_Price"], row["ATR"]),
        axis=1,
    )

    entries = result.apply(lambda row: calculate_sovereign_entry_price(row, macro_score), axis=1)
    result[["Entry_Price", "Support_Label", "Max_Flush", "Premium", "Base_Support"]] = entries
    result["Support_Price"] = result["Entry_Price"]

    result["Tech_Support_Dist"] = result.apply(calculate_support_distance, axis=1)

    tactics = result.apply(lambda row: calculate_tactics(row, macro_risk), axis=1)
    result["Stop_Loss"] = tactics.apply(lambda x: x[0])
    result["Tactical_Warning"] = tactics.apply(lambda x: x[1])
    result["Cluster"] = tactics.apply(lambda x: x[2])
    result["Multiplier"] = tactics.apply(lambda x: x[3])

    result["Risk_Dist"] = abs(result["Entry_Price"] - result["Stop_Loss"])
    result["Target_Price"] = result["Entry_Price"] + (3.0 * result["Risk_Dist"])

    proxy_columns = result.apply(
        lambda row: generate_proxy_signal(row, proxy_data=proxy_data, proxy_db=proxy_db),
        axis=1,
    )
    result[["Proxy_Type", "P_Value", "Proxy_Content", "Proxy_Signal"]] = proxy_columns

    result["Rating"] = result.apply(generate_rating, axis=1)
    result["Leverage"] = result.apply(lambda row: calculate_leverage(row, macro_score), axis=1)

    return result


__all__ = [
    "TECHNICAL_DEFAULT",
    "build_price_technicals",
    "calculate_leverage",
    "calculate_macro_score",
    "calculate_price_technical",
    "calculate_sovereign_entry_price",
    "calculate_support_distance",
    "calculate_tactics",
    "classify_breadth_status",
    "classify_cluster",
    "enrich_scan_frame",
    "generate_proxy_signal",
    "generate_rating",
]
