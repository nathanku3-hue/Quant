from __future__ import annotations

import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd
import requests
from core.security_policy import assert_egress_url_allowed
from core.security_policy import get_allowed_egress_host_suffixes
from core.security_policy import require_hmac_rotation_compliance
from execution.signed_envelope import attach_signed_execution_envelope

# --- RISK CONSTANTS ---
MAX_SINGLE_POS_WEIGHT = 0.20  # Max 20% in one stock
MAX_PORTFOLIO_LEVERAGE = 1.00  # No margin
MAX_ORDERS_PER_BATCH = 20
MIN_SCORE_AGGRESSIVE = 95
MIN_SCORE_STANDARD = 90
_REQUIRED_SCAN_COLS = ("Ticker", "Score", "Regime")


def _prepare_actionable_universe(df_results: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df_results, pd.DataFrame):
        raise TypeError("df_results must be a pandas DataFrame")

    missing = [c for c in _REQUIRED_SCAN_COLS if c not in df_results.columns]
    if missing:
        raise ValueError(f"Missing required scan columns: {missing}")

    work = df_results.copy()
    work["Ticker"] = work["Ticker"].astype(str).str.upper().str.strip()
    work["Score"] = pd.to_numeric(work["Score"], errors="coerce")
    work["Regime"] = work["Regime"].astype(str)
    hf_scalar_series = work["HF_Scalar"] if "HF_Scalar" in work.columns else pd.Series(0, index=work.index)
    work["HF_Scalar"] = pd.to_numeric(hf_scalar_series, errors="coerce").fillna(0)
    work = work[(work["Ticker"] != "") & work["Score"].notna()]

    actionable = work[
        (~work["Regime"].str.startswith("[DEATH", na=False))
        & (work["Score"] >= float(MIN_SCORE_STANDARD))
    ].copy()
    if actionable.empty:
        return actionable

    # Idempotency guard: keep one row per symbol, deterministic winner by highest score.
    actionable = actionable.sort_values(["Ticker", "Score"], ascending=[True, False]).drop_duplicates(
        subset=["Ticker"], keep="first"
    )
    actionable = actionable.sort_values(["Score", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    return actionable


def _build_batch_id(trade_day: str, orders: list[dict[str, Any]]) -> str:
    digest_source = json.dumps(
        [
            {
                "ticker": o.get("ticker"),
                "action": o.get("action"),
                "order_type": o.get("order_type"),
                "score": o.get("strategy_metadata", {}).get("score"),
            }
            for o in orders
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:16]
    return f"{trade_day}-{digest}"


def generate_execution_payload(df_results: pd.DataFrame, portfolio_value: float = 100000.00) -> dict[str, Any]:
    """
    Takes scanner output and returns a broker-agnostic JSON payload.

    Fail-closed policy:
      - reject malformed scanner rows,
      - reject oversize batches,
      - reject leverage breaches with explicit exceptions.
    """
    actionable_df = _prepare_actionable_universe(df_results)
    hmac_status = require_hmac_rotation_compliance()
    if len(actionable_df) > int(MAX_ORDERS_PER_BATCH):
        raise ValueError(
            f"Actionable order count {len(actionable_df)} exceeds max batch size {MAX_ORDERS_PER_BATCH}."
        )

    if len(actionable_df) > 0:
        calculated_weight = min(float(MAX_SINGLE_POS_WEIGHT), 1.0 / float(len(actionable_df)))
    else:
        calculated_weight = 0.0

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    trade_day = now_utc.strftime("%Y%m%d")

    print(f"\n--- EXECUTION BRIDGE: Generating Orders for {len(actionable_df)} Assets ---")
    print(f"--- Target Weight per Asset: {calculated_weight:.1%} ---")

    orders: list[dict[str, Any]] = []
    for _, row in actionable_df.iterrows():
        ticker = str(row["Ticker"]).upper().strip()
        score = float(row["Score"])
        regime = str(row["Regime"])
        urgency = "HIGH" if score >= float(MIN_SCORE_AGGRESSIVE) else "MEDIUM"

        orders.append(
            {
                "client_order_id": f"{trade_day}-{ticker}-BUY",
                "trade_day": trade_day,
                "ticker": ticker,
                "action": "BUY",
                "target_weight": float(calculated_weight),
                "order_type": "MARKET" if urgency == "HIGH" else "LIMIT",
                "quantity_calc": f"PORTFOLIO_VALUE * {calculated_weight:.8f}",
                "limit_price": "Market" if urgency == "HIGH" else "Bid_Ask_Mid",
                "strategy_metadata": {
                    "score": int(round(score)),
                    "urgency": urgency,
                    "hf_scalar": int(round(float(row.get("HF_Scalar", 0)))),
                    "physics_regime": regime,
                },
            }
        )

    total_portfolio_weight = float(calculated_weight * len(orders))
    if total_portfolio_weight > float(MAX_PORTFOLIO_LEVERAGE) + 1e-9:
        raise ValueError(
            "Allocation exceeds leverage budget: "
            f"calculated={total_portfolio_weight:.6f}, max={MAX_PORTFOLIO_LEVERAGE:.6f}"
        )

    batch_id = _build_batch_id(trade_day=trade_day, orders=orders)
    payload = {
        "timestamp": timestamp,
        "batch_id": batch_id,
        "strategy": "ALPHA_SOVEREIGN_V1",
        "portfolio_value_basis": float(portfolio_value),
        "execution_orders": orders,
        "risk_checks": {
            "max_single_position": float(MAX_SINGLE_POS_WEIGHT),
            "total_weight_allocated": total_portfolio_weight,
            "order_count": int(len(orders)),
            "buying_power_check": "NOT_EVALUATED",
        },
        "security_controls": {
            "egress_allowlist_suffixes": list(get_allowed_egress_host_suffixes()),
            "hmac_key_version": str(hmac_status.get("hmac_key_version", "")),
            "hmac_key_activated_at_utc": str(hmac_status.get("hmac_key_activated_at_utc", "")),
            "hmac_rotation_days": int(hmac_status.get("hmac_rotation_days", 1)),
            "hmac_legal_hold": bool(hmac_status.get("hmac_legal_hold", False)),
            "hmac_rotation_due": bool(hmac_status.get("hmac_rotation_due", False)),
        },
    }
    return attach_signed_execution_envelope(
        payload,
        now_utc=now_utc,
        key_version=str(hmac_status.get("hmac_key_version", "")).strip(),
    )


def save_payload(payload: dict[str, Any]) -> Path:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    logs_dir = project_root / "execution"
    logs_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    batch = str(payload.get("batch_id", "na")).replace("/", "_")
    filename = logs_dir / f"execution_payload_{ts}_{batch}.json"

    fd, tmp_name = tempfile.mkstemp(prefix=f"{filename.name}.", suffix=".tmp", dir=str(logs_dir))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4)
        os.replace(tmp_name, filename)
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

    print(f"[BRIDGE] Payload saved to {filename}")
    return filename


def notify_pm(payload: dict[str, Any]) -> None:
    """The Watchtower: sends Discord notification when configured."""
    webhook_url = str(os.environ.get("DISCORD_WEBHOOK_URL", "")).strip()
    post_submit_mode = bool(payload.get("_post_submit"))
    orders = payload.get("execution_orders", [])
    tickers = [str(o.get("ticker", "")).upper() for o in orders]
    weight = float(payload.get("risk_checks", {}).get("total_weight_allocated", 0.0))

    msg = f"🚀 **ALPHA SOVEREIGN EXECUTED** 🚀\nBuys: {', '.join(tickers)}\nTotal Risk: {weight:.1%}\n[Check Logs]"

    if not webhook_url:
        print(f"\n[WATCHTOWER - DRY RUN] Discord Webhook not configured.\nMessage content:\n{msg}\n")
        return

    parsed = urlparse(webhook_url)
    webhook_host = parsed.hostname or "<invalid-host>"
    try:
        assert_egress_url_allowed(webhook_url, context="execution_bridge_notify_pm")
        resp = requests.post(webhook_url, json={"content": msg}, timeout=10)
        resp.raise_for_status()
        print("[WATCHTOWER] Discord notification sent.")
    except requests.RequestException as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        detail = f"status={status_code}" if status_code is not None else type(exc).__name__
        if post_submit_mode:
            print(f"[WATCHTOWER-DEGRADED] Discord webhook delivery failed ({detail}) for host={webhook_host}")
            return
        raise RuntimeError(
            f"Discord webhook delivery failed ({detail}) for host={webhook_host}"
        ) from exc
