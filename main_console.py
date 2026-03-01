import sys
import pandas as pd
import os
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from scripts.alpha_quad_scanner import run_alpha_sovereign_scan
from scripts.execution_bridge import (
    MAX_ORDERS_PER_BATCH,
    generate_execution_payload,
    notify_pm,
    save_payload,
)
from scripts.high_freq_data import AutoFetcher
from execution.signed_envelope import verify_local_submit_envelope_and_replay
from execution.confirmation import confirm_execution_intent

LOCAL_SUBMIT_ENV = "TZ_EXECUTE_LOCAL_SUBMIT"
LOCAL_SUBMIT_VALUE = "YES"
LOCAL_SUBMIT_TELEMETRY_DURABILITY_TIMEOUT_SECONDS = 2.0
_TERMINAL_UNFILLED_STATUSES = {
    "canceled",
    "cancelled",
    "rejected",
    "expired",
    "done_for_day",
    "stopped",
    "suspended",
}


def _is_local_submit_enabled(env: dict[str, str] | None = None) -> bool:
    env_map = env if isinstance(env, dict) else os.environ
    return str(env_map.get(LOCAL_SUBMIT_ENV, "")).strip().upper() == LOCAL_SUBMIT_VALUE


def _payload_trade_day(payload: dict) -> str:
    timestamp = str(payload.get("timestamp", "")).strip()
    if timestamp:
        normalized = timestamp.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.astimezone(timezone.utc).strftime("%Y%m%d")
        except ValueError:
            pass
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _clean_optional_str(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _strict_positive_float(value: Any, *, field_label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field_label} must be a positive float")
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} must be a positive float") from None
    if not math.isfinite(parsed) or parsed <= 0.0:
        raise ValueError(f"{field_label} must be a positive float")
    return parsed


def _strict_positive_int(value: Any, *, field_label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_label} must be a positive integer")
    try:
        parsed_float = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_label} must be a positive integer") from None
    if not math.isfinite(parsed_float) or parsed_float <= 0.0 or not float(parsed_float).is_integer():
        raise ValueError(f"{field_label} must be a positive integer")
    parsed = int(parsed_float)
    if parsed <= 0:
        raise ValueError(f"{field_label} must be a positive integer")
    return parsed


def _result_fill_qty_or_none(result: dict[str, Any]) -> float | None:
    fill_summary = result.get("fill_summary", {})
    fill_summary_map = fill_summary if isinstance(fill_summary, dict) else {}
    fill_qty_raw = fill_summary_map.get("fill_qty")
    if fill_qty_raw is None:
        fill_qty_raw = result.get("filled_qty")
    if isinstance(fill_qty_raw, bool):
        return None
    try:
        fill_qty = float(fill_qty_raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(fill_qty):
        return None
    return fill_qty


def _is_terminal_unfilled_local_result(result: dict[str, Any]) -> bool:
    status = _clean_optional_str(result.get("status", "")).lower()
    if status not in _TERMINAL_UNFILLED_STATUSES:
        return False
    fill_qty = _result_fill_qty_or_none(result)
    return fill_qty is None or fill_qty <= 0.0


def _is_local_submit_accepted_result(result: dict[str, Any]) -> bool:
    if result.get("ok") is not True:
        return False
    return not _is_terminal_unfilled_local_result(result)


def _normalize_payload_side(row: dict[str, Any], *, row_index: int) -> str:
    side_raw = _clean_optional_str(row.get("side", ""))
    action_raw = _clean_optional_str(row.get("action", ""))
    side = (side_raw or action_raw).lower()
    if side not in {"buy", "sell"}:
        raise ValueError(
            f"payload execution_orders[{row_index}] side/action must resolve to buy|sell"
        )
    return side


def _normalize_payload_order_type(row: dict[str, Any], *, row_index: int) -> str:
    order_type = _clean_optional_str(row.get("order_type", "")).lower()
    if order_type not in {"market", "limit"}:
        raise ValueError(
            f"payload execution_orders[{row_index}] order_type must be MARKET or LIMIT"
        )
    return order_type


def _normalize_payload_limit_policy(
    row: dict[str, Any],
    *,
    row_index: int,
    order_type: str,
) -> dict[str, Any]:
    raw = row.get("limit_price", None)
    text = _clean_optional_str(raw).lower()

    if order_type == "market":
        if text and text not in {"market", "mkt"}:
            raise ValueError(
                f"payload execution_orders[{row_index}] market orders cannot carry non-market limit_price"
            )
        return {"policy": "market", "value": None}

    # order_type == "limit"
    if isinstance(raw, bool):
        raise ValueError(f"payload execution_orders[{row_index}] limit_price must be numeric or policy token")
    if text == "":
        raise ValueError(f"payload execution_orders[{row_index}] limit orders require limit_price")
    try:
        numeric = float(raw)
    except (TypeError, ValueError):
        token = text.replace(" ", "_")
        if token in {"bid_ask_mid", "mid", "midpoint"}:
            return {"policy": "bid_ask_mid", "value": None}
        raise ValueError(
            f"payload execution_orders[{row_index}] limit_price must be numeric or Bid_Ask_Mid policy"
        ) from None
    if (not math.isfinite(numeric)) or numeric <= 0.0:
        raise ValueError(f"payload execution_orders[{row_index}] limit_price must be > 0")
    return {"policy": "fixed", "value": float(numeric)}


def _validate_payload_execution_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows_raw = payload.get("execution_orders", [])
    if not isinstance(rows_raw, list):
        raise ValueError("payload execution_orders must be a list")
    if not rows_raw:
        raise ValueError("payload contains no execution_orders rows")
    if len(rows_raw) > int(MAX_ORDERS_PER_BATCH):
        raise ValueError(
            f"payload execution_orders count {len(rows_raw)} exceeds max batch size {MAX_ORDERS_PER_BATCH}"
        )

    validated: list[dict[str, Any]] = []
    seen_symbols: set[str] = set()
    seen_client_order_ids: set[str] = set()
    for idx, row_raw in enumerate(rows_raw):
        if not isinstance(row_raw, dict):
            raise ValueError(f"payload execution_orders[{idx}] must be a dict")
        row = dict(row_raw)

        symbol = _clean_optional_str(row.get("ticker", "") or row.get("symbol", "")).upper()
        if not symbol:
            raise ValueError(f"payload execution_orders[{idx}] missing ticker")
        if symbol in seen_symbols:
            raise ValueError(f"duplicate ticker in payload execution_orders: {symbol}")
        seen_symbols.add(symbol)

        target_weight = _strict_positive_float(
            row.get("target_weight"),
            field_label=f"payload execution_orders[{idx}].target_weight",
        )
        side = _normalize_payload_side(row, row_index=idx)
        order_type = _normalize_payload_order_type(row, row_index=idx)
        limit_policy = _normalize_payload_limit_policy(
            row,
            row_index=idx,
            order_type=order_type,
        )
        client_order_id = _clean_optional_str(row.get("client_order_id", ""))
        if not client_order_id:
            raise ValueError(f"payload execution_orders[{idx}] missing client_order_id")
        if client_order_id in seen_client_order_ids:
            raise ValueError(f"duplicate client_order_id in payload execution_orders: {client_order_id}")
        seen_client_order_ids.add(client_order_id)

        trade_day = _clean_optional_str(row.get("trade_day", ""))
        if not trade_day:
            raise ValueError(f"payload execution_orders[{idx}] missing trade_day")
        if not trade_day.isdigit() or len(trade_day) != 8:
            raise ValueError(f"payload execution_orders[{idx}] trade_day must be YYYYMMDD")
        try:
            datetime.strptime(trade_day, "%Y%m%d")
        except ValueError:
            raise ValueError(
                f"payload execution_orders[{idx}] trade_day must be a valid calendar date"
            ) from None

        validated.append(
            {
                "symbol": symbol,
                "target_weight": target_weight,
                "side": side,
                "order_type": order_type,
                "limit_policy": limit_policy,
                "client_order_id": client_order_id,
                "trade_day": trade_day,
            }
        )
    return validated


def _resolve_seeded_limit_price(
    *,
    symbol: str,
    order_type: str,
    limit_policy: dict[str, Any],
    calculated_order: dict[str, Any],
) -> float | None:
    if order_type == "market":
        return None

    policy = str(limit_policy.get("policy", "")).strip().lower()
    if policy == "fixed":
        return float(limit_policy.get("value"))
    if policy == "bid_ask_mid":
        return _strict_positive_float(
            calculated_order.get("price"),
            field_label=f"calculated order price for {symbol}",
        )
    raise ValueError(f"Unsupported limit policy for {symbol}: {policy}")


def _assert_seeded_order_parity(
    *,
    symbol: str,
    order: dict[str, Any],
    expected_side: str,
    expected_order_type: str,
    expected_limit_price: float | None,
    expected_client_order_id: str,
) -> None:
    symbol_actual = _clean_optional_str(order.get("symbol", "")).upper()
    side_actual = _clean_optional_str(order.get("side", "")).lower()
    qty_actual = _strict_positive_int(order.get("qty"), field_label=f"calculated qty for {symbol}")
    order_type_actual = _clean_optional_str(order.get("order_type", "")).lower()
    client_order_id_actual = _clean_optional_str(order.get("client_order_id", ""))
    limit_price_actual_raw = order.get("limit_price")
    limit_price_actual = None if limit_price_actual_raw is None else float(limit_price_actual_raw)

    if symbol_actual != symbol:
        raise ValueError(f"intent parity mismatch for {symbol}: calculated symbol={symbol_actual}")
    if side_actual != expected_side:
        raise ValueError(f"intent parity mismatch for {symbol}: calculated side={side_actual}, payload side={expected_side}")
    if qty_actual <= 0:
        raise ValueError(f"intent parity mismatch for {symbol}: qty must be positive")
    if order_type_actual != expected_order_type:
        raise ValueError(
            f"intent parity mismatch for {symbol}: calculated order_type={order_type_actual}, "
            f"payload order_type={expected_order_type}"
        )
    if client_order_id_actual != expected_client_order_id:
        raise ValueError(
            f"intent parity mismatch for {symbol}: calculated client_order_id={client_order_id_actual}, "
            f"payload client_order_id={expected_client_order_id}"
        )

    if expected_order_type == "market":
        if limit_price_actual is not None:
            raise ValueError(f"intent parity mismatch for {symbol}: market order must not carry limit_price")
    else:
        if limit_price_actual is None:
            raise ValueError(f"intent parity mismatch for {symbol}: limit order missing limit_price")
        if not math.isfinite(limit_price_actual) or limit_price_actual <= 0.0:
            raise ValueError(f"intent parity mismatch for {symbol}: invalid limit_price={limit_price_actual}")
        if expected_limit_price is None or abs(limit_price_actual - float(expected_limit_price)) > 1e-9:
            raise ValueError(
                f"intent parity mismatch for {symbol}: calculated limit_price={limit_price_actual}, "
                f"payload limit_price={expected_limit_price}"
            )


def _execute_payload_via_idempotent_helper(payload: dict) -> list[dict]:
    from execution.broker_api import AlpacaBroker
    from execution.rebalancer import PortfolioRebalancer
    from main_bot_orchestrator import execute_orders_with_idempotent_retry

    validated_rows = _validate_payload_execution_rows(payload)
    targets: dict[str, float] = {row["symbol"]: float(row["target_weight"]) for row in validated_rows}

    broker = AlpacaBroker()
    rebalancer = PortfolioRebalancer(broker)
    calculated_orders = rebalancer.calculate_orders(targets)
    if not calculated_orders:
        raise ValueError("payload targets produced no executable orders")

    calculated_by_symbol: dict[str, dict[str, Any]] = {}
    for idx, calculated_raw in enumerate(calculated_orders):
        if not isinstance(calculated_raw, dict):
            raise ValueError(f"calculated order row {idx} must be a dict")
        calculated = dict(calculated_raw)
        symbol = _clean_optional_str(calculated.get("symbol", "")).upper()
        if not symbol:
            raise ValueError(f"calculated order row {idx} missing symbol")
        if symbol in calculated_by_symbol:
            raise ValueError(f"duplicate symbol in calculated orders: {symbol}")
        calculated_by_symbol[symbol] = calculated

    payload_symbols = {row["symbol"] for row in validated_rows}
    calculated_symbols = set(calculated_by_symbol.keys())
    if payload_symbols != calculated_symbols:
        missing = sorted(payload_symbols - calculated_symbols)
        extra = sorted(calculated_symbols - payload_symbols)
        raise ValueError(
            f"payload/calculated symbol drift detected: missing={missing}, extra={extra}"
        )

    fallback_trade_day = _payload_trade_day(payload)
    seeded_orders: list[dict[str, Any]] = []
    for row in validated_rows:
        symbol = row["symbol"]
        calculated = calculated_by_symbol[symbol]
        seeded = dict(calculated)
        seeded["symbol"] = symbol
        seeded["trade_day"] = row["trade_day"] or fallback_trade_day
        seeded["client_order_id"] = row["client_order_id"]
        seeded["order_type"] = row["order_type"]
        seeded["side"] = _clean_optional_str(seeded.get("side", "")).lower()
        seeded["qty"] = _strict_positive_int(
            seeded.get("qty"),
            field_label=f"calculated qty for {symbol}",
        )
        # Microstructure anchor: capture Sovereign_Command generation timestamp
        # and the prevailing bid/ask midpoint snapshot at that moment.
        command_ts = _utc_now_iso_ms()
        if hasattr(broker, "get_latest_quote_snapshot"):
            quote_snapshot = broker.get_latest_quote_snapshot(symbol)
        else:
            fallback_mid_raw = calculated.get("price")
            if fallback_mid_raw is None:
                # Test/dry harness fallback when quote API is unavailable.
                fallback_mid_raw = 1.0
            fallback_mid = _strict_positive_float(
                fallback_mid_raw,
                field_label=f"fallback arrival midpoint for {symbol}",
            )
            quote_snapshot = {
                "bid_price": fallback_mid,
                "ask_price": fallback_mid,
                "quote_ts": command_ts,
            }
        bid_price = _strict_positive_float(
            quote_snapshot.get("bid_price"),
            field_label=f"arrival bid price for {symbol}",
        )
        ask_price = _strict_positive_float(
            quote_snapshot.get("ask_price"),
            field_label=f"arrival ask price for {symbol}",
        )
        seeded["arrival_ts"] = command_ts
        seeded["arrival_quote_ts"] = _clean_optional_str(quote_snapshot.get("quote_ts", "")) or command_ts
        seeded["arrival_bid_price"] = bid_price
        seeded["arrival_ask_price"] = ask_price
        seeded["arrival_price"] = float((bid_price + ask_price) / 2.0)
        seeded["limit_price"] = _resolve_seeded_limit_price(
            symbol=symbol,
            order_type=row["order_type"],
            limit_policy=row["limit_policy"],
            calculated_order=calculated,
        )
        _assert_seeded_order_parity(
            symbol=symbol,
            order=seeded,
            expected_side=row["side"],
            expected_order_type=row["order_type"],
            expected_limit_price=seeded["limit_price"],
            expected_client_order_id=row["client_order_id"],
        )
        seeded_orders.append(seeded)

    execute_results = execute_orders_with_idempotent_retry(rebalancer, seeded_orders)
    if not execute_results:
        raise ValueError("idempotent helper returned no execution results")

    expected_cids = {row["client_order_id"] for row in validated_rows}
    observed_cids: set[str] = set()
    for idx, row in enumerate(execute_results):
        if not isinstance(row, dict):
            raise ValueError(f"idempotent helper row {idx} must be a dict")
        order_map = row.get("order", {})
        if not isinstance(order_map, dict):
            raise ValueError(f"idempotent helper row {idx} missing order map")
        cid = _clean_optional_str(order_map.get("client_order_id", ""))
        if cid not in expected_cids:
            raise ValueError(f"idempotent helper row {idx} returned unknown client_order_id={cid}")
        if cid in observed_cids:
            raise ValueError(f"idempotent helper returned duplicate client_order_id={cid}")
        observed_cids.add(cid)

    if observed_cids != expected_cids:
        missing = sorted(expected_cids - observed_cids)
        raise ValueError(f"idempotent helper missing result rows for client_order_ids={missing}")
    return execute_results


def _persist_execution_microstructure(execute_results: list[dict], payload: dict) -> dict[str, Any]:
    from execution.microstructure import append_execution_microstructure

    batch_id = _clean_optional_str(payload.get("batch_id", "")) or f"{_payload_trade_day(payload)}-local-submit"
    strategy = _clean_optional_str(payload.get("strategy", "")) or "ALPHA_SOVEREIGN_V1"
    return append_execution_microstructure(
        execute_results,
        batch_id=batch_id,
        strategy=strategy,
    )


def _enforce_local_submit_durability_gate(
    telemetry_summary: dict[str, Any],
    *,
    timeout_seconds: float = LOCAL_SUBMIT_TELEMETRY_DURABILITY_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if bool(telemetry_summary.get("async_flush_scheduled")) is not True:
        return telemetry_summary

    from execution.microstructure import get_execution_microstructure_spool_status
    from execution.microstructure import wait_for_execution_microstructure_flush

    required_fields = (
        "spool_path",
        "parquet_path",
        "fills_parquet_path",
        "duckdb_path",
        "duckdb_table",
    )
    missing_fields = [field for field in required_fields if not _clean_optional_str(telemetry_summary.get(field))]
    if missing_fields:
        raise RuntimeError(
            "telemetry durability gate missing required fields: "
            f"{','.join(sorted(missing_fields))}"
        )

    spool_path = Path(str(telemetry_summary["spool_path"]))
    parquet_path = Path(str(telemetry_summary["parquet_path"]))
    fills_parquet_path = Path(str(telemetry_summary["fills_parquet_path"]))
    duckdb_path = Path(str(telemetry_summary["duckdb_path"]))
    table_name = str(telemetry_summary["duckdb_table"])
    drained = wait_for_execution_microstructure_flush(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
        timeout_seconds=max(float(timeout_seconds), 0.0),
    )
    status = get_execution_microstructure_spool_status(
        spool_path=spool_path,
        parquet_path=parquet_path,
        fills_parquet_path=fills_parquet_path,
        duckdb_path=duckdb_path,
        table_name=table_name,
    )
    pending_bytes = int(status.get("pending_bytes", 0))
    last_flush_error = _clean_optional_str(status.get("last_flush_error"))
    if (not drained) or pending_bytes > 0 or bool(last_flush_error):
        raise RuntimeError(
            "async telemetry flush durability gate failed "
            f"(drained={drained}, pending_bytes={pending_bytes}, "
            f"last_flush_error={last_flush_error or 'none'})"
        )
    return {**telemetry_summary, "durability_gate_passed": True, "flush_pending_bytes": pending_bytes}


def print_header():
    print("\n========================================")
    print("   THE ALPHA SOVEREIGN - PM CONSOLE     ")
    print("========================================")
    print("   Phase 43: Cyborg Execution Mode      ")
    print("========================================\n")

def check_kill_switch():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    stop_file = os.path.join(script_dir, "STOP_TRADING")
    if os.path.exists(stop_file):
        print("\n[EMERGENCY] KILL SWITCH ACTIVE. 'STOP_TRADING' file detected. Aborting all operations.")
        sys.exit(1)

def get_manual_input(prompt, default=0.0):
    try:
        if not sys.stdin.isatty():
            print(f"{prompt} [Auto-Default]: {default}")
            return default
            
        val = input(f"{prompt} [Default: {default}]: ")
        if val.strip() == "":
            return default
        return float(val)
    except ValueError:
        print("Invalid input. Using default.")
        return default


def _normalize_auto_metric(raw: Any) -> tuple[float | None, str]:
    if raw is None:
        return None, ""
    if isinstance(raw, dict):
        val_raw = raw.get("val")
        try:
            val = float(val_raw) if val_raw is not None else None
        except (TypeError, ValueError):
            val = None
        span = str(raw.get("span", "")).strip()
        degraded = bool(raw.get("degraded", False))
        reason = str(raw.get("reason", "")).strip()
        status_parts: list[str] = []
        if span:
            status_parts.append(span)
        status_parts.append("degraded" if degraded else "found")
        if reason:
            status_parts.append(reason)
        return val, "/".join(status_parts)
    try:
        return float(raw), "found"
    except (TypeError, ValueError):
        return None, ""


def main() -> int:
    check_kill_switch()
    print_header()
    
    # 1. The Cyborg Data Entry (The "Eyes")
    print("--- STEP 1: HIGH-FREQUENCY MANUAL INPUTS ---")
    inputs = {}
    auto = AutoFetcher()
    
    # MEMORY PHYSICS
    auto_dram = auto.fetch_dram_trend()
    if auto_dram is not None:
        print(f"[AUTO] DRAM Spot Trend: {auto_dram}% (Found)")
        inputs['dram_spot_trend'] = auto_dram
    else:
        print("[MANUAL] DRAM Trend: (Scrape Failed) -> Enter Value")
        inputs['dram_spot_trend'] = get_manual_input("Enter DRAM Spot Trend % (e.g. 0.05)", 0.0)
        
    inputs['nand_spot_trend'] = get_manual_input("Enter NAND Spot Trend % (e.g. 0.02)", 0.0)
    
    # COMPUTE PHYSICS
    auto_tsmc_val, auto_tsmc_status = _normalize_auto_metric(auto.fetch_tsmc_yoy())
    if auto_tsmc_val is not None:
        print(f"[AUTO] TSMC Revenue YoY: {auto_tsmc_val:+.4f} ({auto_tsmc_status})")
        inputs['tsmc_monthly_yoy'] = auto_tsmc_val
    else:
        inputs['tsmc_monthly_yoy'] = get_manual_input("Enter TSMC Monthly YoY % (e.g. 24.5)", 20.0)
    
    # INFRA / ENERGY PHYSICS
    auto_energy_val, auto_energy_status = _normalize_auto_metric(auto.fetch_energy_trend())
    if auto_energy_val is not None:
        print(f"[AUTO] Energy/Uranium Trend: {auto_energy_val*100:+.2f}% ({auto_energy_status})")
        inputs['energy_price_trend'] = auto_energy_val
    else:
        inputs['energy_price_trend'] = get_manual_input("Enter Energy/Uranium Trend % (e.g. 0.03)", 0.0)
    
    # SOFTWARE PHYSICS (RBRK Support)
    auto_cloud_val, auto_cloud_status = _normalize_auto_metric(auto.fetch_cloud_growth())
    if auto_cloud_val is not None:
        print(f"[AUTO] AWS/Azure Cloud Growth YoY: {auto_cloud_val*100:+.2f}% ({auto_cloud_status})")
        inputs['cloud_growth_yoy'] = auto_cloud_val
    else:
        inputs['cloud_growth_yoy'] = get_manual_input("Enter AWS/Azure YoY Growth Rate (e.g. 0.30)", 0.30)
    
    # BIOTECH PHYSICS (NBIS Support)
    inputs['xbi_funding_trend'] = get_manual_input("Enter XBI Funding Trend Rate (e.g. 0.10)", 0.10)

    print("\n[SYSTEM] Inputs Locked. Initializing Physics Engine...")
    
    # 2. Run The Engine (The "Brain")
    # We pass the 'inputs' dict to the scanner
    results_df = run_alpha_sovereign_scan(manual_inputs=inputs)
    
    if results_df is None or results_df.empty:
        print("[ERROR] Engine failed to return data.")
        return 1
        
    # Display the "Club of 100"
    print("\n--- STEP 2: SCAN RESULTS (The Elite) ---")
    elite_df = results_df[results_df['Score'] >= 90]
    if elite_df.empty:
        print("[ALERT] No Assets passed the Opportunity Gate. Cash is King.")
    else:
        print(elite_df[['Ticker', 'Score', 'Regime', 'Action']])

    # 3. Generate Orders (The "Hands")
    if not elite_df.empty:
        confirmed = confirm_execution_intent(
            is_tty=bool(sys.stdin.isatty()),
            env=os.environ,
        )

        if not confirmed:
            if sys.stdin.isatty():
                print("[ABORT] Manual Override. No orders generated.")
            else:
                print(
                    "[ABORT] Non-interactive session requires explicit override: "
                    "set TZ_EXECUTION_CONFIRM=YES to generate broker payload."
                )
            return 1
        else:
            try:
                payload = generate_execution_payload(results_df)
            except Exception as exc:
                print(f"[ABORT] Payload generation blocked by guardrail: {exc}")
                return 1

            try:
                save_payload(payload)
            except Exception as exc:
                print(f"[ABORT] Payload persistence failed under guardrails: {exc}")
                return 1

            if _is_local_submit_enabled():
                try:
                    verify_local_submit_envelope_and_replay(payload)
                    execute_results = _execute_payload_via_idempotent_helper(payload)
                except Exception as exc:
                    print(f"[ABORT] Local submit path failed under guardrails: {exc}")
                    return 1
                try:
                    telemetry_summary = _persist_execution_microstructure(execute_results, payload)
                    telemetry_summary = _enforce_local_submit_durability_gate(telemetry_summary)
                except Exception as exc:
                    print(f"[ABORT] Microstructure telemetry persistence failed: {exc}")
                    return 1
                print(
                    "[TELEMETRY] Microstructure sink updated: "
                    f"orders={telemetry_summary.get('orders_written', 0)}, "
                    f"fills={telemetry_summary.get('fills_written', 0)}"
                )
                ok_count = sum(
                    1
                    for row in execute_results
                    if _is_local_submit_accepted_result(
                        row.get("result", {}) if isinstance(row.get("result", {}), dict) else {}
                    )
                )
                print(f"[SUCCESS] Local submit finished: {ok_count}/{len(execute_results)} accepted.")
                if ok_count != len(execute_results):
                    print("[ABORT] Local submit encountered failed orders; inspect execution logs.")
                    return 1
                try:
                    notify_pm({**payload, "_post_submit": True})
                except Exception as exc:
                    print(f"[ABORT] Post-submit notification failed under guardrails: {exc}")
                    return 1
            else:
                try:
                    notify_pm(payload)
                except Exception as exc:
                    print(f"[ABORT] Payload notification failed under guardrails: {exc}")
                    return 1
                print("[SUCCESS] Orders Generated. Upload to Broker API.")
    
    print("\n[SYSTEM] Session Closed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
