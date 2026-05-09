from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from alpaca.common.exceptions import APIError
from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestBarRequest
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide
from alpaca.trading.enums import OrderType
from alpaca.trading.enums import TimeInForce
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.requests import MarketOrderRequest
from core.security_policy import assert_egress_url_allowed


PAPER_BASE_URL = "https://paper-api.alpaca.markets"
LIVE_TRADING_BREAK_GLASS_ENV = "TZ_ALPACA_ALLOW_LIVE"
LIVE_TRADING_BREAK_GLASS_VALUE = "YES"
ALPACA_DATA_FEED_ENV = "TZ_ALPACA_DATA_FEED"
DEFAULT_ALPACA_DATA_FEED = "iex"
ALPACA_ALLOWED_DATA_FEEDS = frozenset({"iex", "delayed_sip", "sip"})
_ALPACA_PY_DATA_FEEDS = {
    "iex": DataFeed.IEX,
    "delayed_sip": DataFeed.DELAYED_SIP,
    "sip": DataFeed.SIP,
}


def _normalize_base_url(url: str) -> str:
    return str(url).strip().rstrip("/")


def _is_paper_base_url(url: str) -> bool:
    normalized = _normalize_base_url(url).lower()
    paper = PAPER_BASE_URL.lower()
    return normalized == paper or normalized.startswith(f"{paper}/")


def resolve_alpaca_data_feed(feed: Any | None = None) -> str:
    value = _clean_optional_text(feed or os.environ.get(ALPACA_DATA_FEED_ENV) or DEFAULT_ALPACA_DATA_FEED).lower()
    if value not in ALPACA_ALLOWED_DATA_FEEDS:
        allowed = ", ".join(sorted(ALPACA_ALLOWED_DATA_FEEDS))
        raise ValueError(f"Unsupported Alpaca data feed {value!r}; allowed feeds: {allowed}")
    return value


def _quote_quality_for_feed(feed: str) -> str:
    feed_l = str(feed).lower().strip()
    if feed_l == "iex":
        return "iex_only"
    if feed_l == "delayed_sip":
        return "delayed_sip_quality"
    if feed_l == "sip":
        return "sip_quality"
    return "unknown"


def _alpaca_py_feed(feed: str | None) -> DataFeed:
    return _ALPACA_PY_DATA_FEEDS[resolve_alpaca_data_feed(feed)]


def _alpaca_py_side(side: str) -> OrderSide:
    return OrderSide(str(side).lower().strip())


def _alpaca_py_order_type(order_type: str) -> OrderType:
    return OrderType(str(order_type).lower().strip())


def _alpaca_py_time_in_force(time_in_force: str) -> TimeInForce:
    return TimeInForce(str(time_in_force).lower().strip())


def _lookup_symbol_payload(payload: Any, symbol: str) -> Any:
    if not isinstance(payload, dict):
        return payload
    symbol_u = str(symbol).upper()
    return payload.get(symbol_u) or payload.get(str(symbol)) or payload.get(symbol_u.lower())


class _AlpacaPyREST:
    """Compatibility wrapper for the legacy REST surface used inside this module."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        base_url: str,
        api_version: str | None = None,
    ) -> None:
        _ = api_version
        base_url_s = _normalize_base_url(base_url)
        paper = _is_paper_base_url(base_url_s)
        self._trading = TradingClient(
            api_key=api_key,
            secret_key=api_secret,
            paper=paper,
            raw_data=False,
            url_override=base_url_s,
        )
        self._data = StockHistoricalDataClient(
            api_key=api_key,
            secret_key=api_secret,
            raw_data=False,
        )

    def get_account(self) -> Any:
        return self._trading.get_account()

    def list_positions(self) -> list[Any]:
        return list(self._trading.get_all_positions())

    def submit_order(self, **kwargs: Any) -> Any:
        order_type = _alpaca_py_order_type(str(kwargs.get("type", "")))
        base_payload = {
            "symbol": kwargs.get("symbol"),
            "qty": kwargs.get("qty"),
            "side": _alpaca_py_side(str(kwargs.get("side", ""))),
            "type": order_type,
            "time_in_force": _alpaca_py_time_in_force(str(kwargs.get("time_in_force", ""))),
            "client_order_id": kwargs.get("client_order_id"),
        }
        if order_type == OrderType.LIMIT:
            order_request = LimitOrderRequest(
                **base_payload,
                limit_price=kwargs.get("limit_price"),
            )
        else:
            order_request = MarketOrderRequest(**base_payload)
        return self._trading.submit_order(order_request)

    def get_order_by_client_order_id(self, client_order_id: str) -> Any:
        return self._trading.get_order_by_client_id(client_order_id)

    def close_all_positions(self) -> Any:
        return self._trading.close_all_positions(cancel_orders=True)

    def get_clock(self) -> Any:
        return self._trading.get_clock()

    def get_latest_quote(self, symbol: str, feed: str | None = None) -> Any:
        symbol_u = str(symbol).upper()
        request = StockLatestQuoteRequest(
            symbol_or_symbols=symbol_u,
            feed=_alpaca_py_feed(feed),
        )
        return _lookup_symbol_payload(self._data.get_stock_latest_quote(request), symbol_u)

    def get_latest_trade(self, symbol: str, feed: str | None = None) -> Any:
        symbol_u = str(symbol).upper()
        request = StockLatestTradeRequest(
            symbol_or_symbols=symbol_u,
            feed=_alpaca_py_feed(feed),
        )
        return _lookup_symbol_payload(self._data.get_stock_latest_trade(request), symbol_u)

    def get_latest_bar(self, symbol: str, feed: str | None = None) -> Any:
        symbol_u = str(symbol).upper()
        request = StockLatestBarRequest(
            symbol_or_symbols=symbol_u,
            feed=_alpaca_py_feed(feed),
        )
        bar = _lookup_symbol_payload(self._data.get_stock_latest_bar(request), symbol_u)
        if hasattr(bar, "c"):
            return bar
        return SimpleNamespace(
            c=getattr(bar, "close", None),
            timestamp=getattr(bar, "timestamp", None),
        )


tradeapi = SimpleNamespace(REST=_AlpacaPyREST)


def _to_number(value: Any) -> int | float:
    """Normalize Alpaca string/Decimal numeric fields into Python numbers."""
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, (int, float)):
        return int(value) if float(value).is_integer() else float(value)
    try:
        parsed = float(value)
        return int(parsed) if parsed.is_integer() else parsed
    except (TypeError, ValueError):
        return 0.0


def _clean_optional_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _to_positive_float_or_none(value: Any) -> float | None:
    try:
        parsed = float(_to_number(value))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed) or parsed <= 0.0:
        return None
    return parsed


def _to_iso_utc_ms(value: Any) -> str | None:
    if value is None:
        return None

    if hasattr(value, "to_pydatetime"):
        try:
            value = value.to_pydatetime()
        except Exception:
            pass

    if isinstance(value, datetime):
        dt = value
    else:
        text = _clean_optional_text(value)
        if not text:
            return None
        normalized = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


_TERMINAL_UNFILLED_STATUSES = {
    "canceled",
    "cancelled",
    "rejected",
    "expired",
    "done_for_day",
    "stopped",
    "suspended",
}


def _is_terminal_unfilled_result(result: dict[str, Any]) -> bool:
    status = _clean_optional_text(result.get("status", "")).lower()
    if status not in _TERMINAL_UNFILLED_STATUSES:
        return False
    fill_summary = result.get("fill_summary", {})
    summary_map = fill_summary if isinstance(fill_summary, dict) else {}
    fill_qty = _to_positive_float_or_none(summary_map.get("fill_qty"))
    if fill_qty is None:
        fill_qty = _to_positive_float_or_none(result.get("filled_qty"))
    return fill_qty is None


def _backfill_latency_anchors(result: dict[str, Any]) -> None:
    submit_sent_ts = _clean_optional_text(result.get("submit_sent_ts"))
    if not submit_sent_ts:
        submit_sent_ts = (
            _clean_optional_text(result.get("submitted_at"))
            or _clean_optional_text(result.get("created_at"))
            or _clean_optional_text(result.get("updated_at"))
        )
        if submit_sent_ts:
            result["submit_sent_ts"] = submit_sent_ts

    broker_ack_ts = _clean_optional_text(result.get("broker_ack_ts"))
    if not broker_ack_ts:
        broker_ack_ts = (
            _clean_optional_text(result.get("updated_at"))
            or _clean_optional_text(result.get("submitted_at"))
            or _clean_optional_text(result.get("created_at"))
        )
        if broker_ack_ts:
            result["broker_ack_ts"] = broker_ack_ts


def _resolve_execution_ts(result: dict[str, Any]) -> str | None:
    execution_ts = _clean_optional_text(result.get("execution_ts"))
    if execution_ts:
        return execution_ts

    fill_summary = result.get("fill_summary", {})
    summary_map = fill_summary if isinstance(fill_summary, dict) else {}
    first_fill_ts = _clean_optional_text(summary_map.get("first_fill_ts"))
    if first_fill_ts:
        return first_fill_ts

    partial_fills = result.get("partial_fills", [])
    if isinstance(partial_fills, list):
        fill_timestamps: list[str] = []
        for row in partial_fills:
            if not isinstance(row, dict):
                continue
            ts = _clean_optional_text(row.get("fill_ts"))
            if ts:
                fill_timestamps.append(ts)
        if fill_timestamps:
            return min(fill_timestamps)

    filled_at = _clean_optional_text(result.get("filled_at"))
    if filled_at:
        return filled_at
    return None


def _normalize_submit_acceptance(result: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(result)
    _backfill_latency_anchors(normalized)
    execution_ts = _resolve_execution_ts(normalized)
    if execution_ts:
        normalized["execution_ts"] = execution_ts
    if _is_terminal_unfilled_result(normalized):
        status = _clean_optional_text(normalized.get("status", "")).lower() or "terminal"
        normalized["ok"] = False
        normalized["error"] = f"terminal_unfilled:{status}"
    return normalized


class AlpacaBroker:
    def __init__(self) -> None:
        api_key = os.environ.get("ALPACA_API_KEY") or os.environ.get("APCA_API_KEY_ID")
        api_secret = os.environ.get("ALPACA_API_SECRET") or os.environ.get("APCA_API_SECRET_KEY")
        base_url = (
            os.environ.get("APCA_API_BASE_URL")
            or os.environ.get("ALPACA_BASE_URL")
            or PAPER_BASE_URL
        )
        base_url = _normalize_base_url(base_url)
        assert_egress_url_allowed(base_url, context="alpaca_broker_base_url")

        missing = []
        if not api_key:
            missing.append("ALPACA_API_KEY/APCA_API_KEY_ID")
        if not api_secret:
            missing.append("ALPACA_API_SECRET/APCA_API_SECRET_KEY")
        if missing:
            raise EnvironmentError(
                "Missing required Alpaca credentials: " + ", ".join(missing)
            )

        break_glass = str(os.environ.get(LIVE_TRADING_BREAK_GLASS_ENV, "")).strip().upper()
        if not _is_paper_base_url(base_url):
            if break_glass != LIVE_TRADING_BREAK_GLASS_VALUE:
                raise EnvironmentError(
                    "Refusing non-paper Alpaca base URL. "
                    f"Set {LIVE_TRADING_BREAK_GLASS_ENV}={LIVE_TRADING_BREAK_GLASS_VALUE} "
                    "to explicitly allow live trading."
                )
            signed_live_decision = str(
                os.environ.get("TZ_SIGNED_LIVE_TRADING_DECISION", "")
            ).strip().upper()
            if signed_live_decision != "YES":
                raise EnvironmentError(
                    "Live Alpaca trading is outside the current milestone. "
                    "Set TZ_SIGNED_LIVE_TRADING_DECISION=YES only after a signed decision-log packet."
                )

        self.api = tradeapi.REST(api_key, api_secret, base_url=base_url, api_version="v2")

        # Authenticate early so failures are explicit during startup.
        try:
            self.api.get_account()
        except Exception as exc:
            raise ConnectionError(f"Failed to initialize Alpaca REST client: {exc}") from exc

    def get_portfolio_state(self) -> dict[str, Any]:
        account = self.api.get_account()
        positions_raw = self.api.list_positions()
        positions = {p.symbol: _to_number(p.qty) for p in positions_raw}
        return {
            "cash": _to_number(account.cash),
            "equity": _to_number(account.equity),
            "positions": positions,
        }

    @staticmethod
    def _build_order_snapshot(order: Any, *, fallback_client_order_id: str) -> dict[str, Any]:
        order_type = _clean_optional_text(getattr(order, "type", "")).lower() or None
        limit_price_raw = getattr(order, "limit_price", None)
        raw_client_order_id = getattr(order, "client_order_id", None)
        if raw_client_order_id is None:
            client_order_id = fallback_client_order_id
        else:
            client_order_id = _clean_optional_text(raw_client_order_id)
        return {
            "order_id": getattr(order, "id", None),
            "status": _clean_optional_text(getattr(order, "status", "")) or "new",
            "client_order_id": client_order_id,
            "symbol": _clean_optional_text(getattr(order, "symbol", "")).upper() or None,
            "side": _clean_optional_text(getattr(order, "side", "")).lower() or None,
            "qty": _to_number(getattr(order, "qty", None)),
            "order_type": order_type,
            "limit_price": limit_price_raw,
            "time_in_force": _clean_optional_text(getattr(order, "time_in_force", "")).lower() or None,
            "created_at": _to_iso_utc_ms(getattr(order, "created_at", None)),
            "submitted_at": _to_iso_utc_ms(getattr(order, "submitted_at", None)),
            "updated_at": _to_iso_utc_ms(getattr(order, "updated_at", None)),
            "filled_at": _to_iso_utc_ms(getattr(order, "filled_at", None)),
            "filled_qty": _to_number(getattr(order, "filled_qty", None)),
            "filled_avg_price": _to_positive_float_or_none(getattr(order, "filled_avg_price", None)),
        }

    def _list_fill_activities(
        self,
        *,
        order_id: str,
        symbol: str,
        side: str,
    ) -> list[dict[str, Any]]:
        if not hasattr(self.api, "get_activities"):
            return []

        activities: list[Any] = []
        candidate_calls = (
            {"activity_types": "FILL", "direction": "desc", "page_size": 200},
            {"activity_types": "FILL", "direction": "desc"},
            {"activity_types": "FILL"},
        )

        for kwargs in candidate_calls:
            try:
                raw = self.api.get_activities(**kwargs)
                activities = list(raw)
                break
            except TypeError:
                continue
            except Exception:
                return []

        partial_fills: list[dict[str, Any]] = []
        for activity in activities:
            activity_order_id = _clean_optional_text(getattr(activity, "order_id", ""))
            if order_id and activity_order_id != order_id:
                continue

            activity_symbol = _clean_optional_text(getattr(activity, "symbol", "")).upper()
            if symbol and activity_symbol and activity_symbol != symbol:
                continue

            activity_side = _clean_optional_text(getattr(activity, "side", "")).lower()
            if side and activity_side and activity_side != side:
                continue

            fill_qty = _to_positive_float_or_none(getattr(activity, "qty", None))
            fill_price = _to_positive_float_or_none(getattr(activity, "price", None))
            if fill_qty is None or fill_price is None:
                continue

            partial_fills.append(
                {
                    "fill_qty": fill_qty,
                    "fill_price": fill_price,
                    "fill_ts": _to_iso_utc_ms(
                        getattr(activity, "transaction_time", None)
                        or getattr(activity, "transaction_time_utc", None)
                        or getattr(activity, "date", None)
                    ),
                    "fill_venue": _clean_optional_text(getattr(activity, "exchange", "")) or None,
                    "source": "broker_activity",
                }
            )

        partial_fills.sort(key=lambda row: row.get("fill_ts") or "")
        for idx, row in enumerate(partial_fills, start=1):
            row["fill_index"] = idx
        return partial_fills

    @staticmethod
    def _summarize_partial_fills(partial_fills: list[dict[str, Any]]) -> dict[str, Any]:
        if not partial_fills:
            return {
                "fill_count": 0,
                "fill_qty": 0.0,
                "fill_notional": 0.0,
                "fill_vwap": None,
                "first_fill_ts": None,
                "last_fill_ts": None,
            }

        total_qty = 0.0
        total_notional = 0.0
        fill_timestamps: list[str] = []
        for row in partial_fills:
            qty = float(row.get("fill_qty", 0.0) or 0.0)
            price = float(row.get("fill_price", 0.0) or 0.0)
            if qty > 0.0 and price > 0.0:
                total_qty += qty
                total_notional += qty * price
            ts = _clean_optional_text(row.get("fill_ts", ""))
            if ts:
                fill_timestamps.append(ts)

        fill_vwap = (total_notional / total_qty) if total_qty > 0.0 else None
        first_fill_ts = min(fill_timestamps) if fill_timestamps else None
        last_fill_ts = max(fill_timestamps) if fill_timestamps else None
        return {
            "fill_count": int(len(partial_fills)),
            "fill_qty": float(total_qty),
            "fill_notional": float(total_notional),
            "fill_vwap": float(fill_vwap) if fill_vwap is not None else None,
            "first_fill_ts": first_fill_ts,
            "last_fill_ts": last_fill_ts,
        }

    def _extract_fill_telemetry(self, *, snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        order_id = _clean_optional_text(snapshot.get("order_id", ""))
        symbol = _clean_optional_text(snapshot.get("symbol", "")).upper()
        side = _clean_optional_text(snapshot.get("side", "")).lower()
        partial_fills = self._list_fill_activities(order_id=order_id, symbol=symbol, side=side)

        if not partial_fills:
            filled_qty = _to_positive_float_or_none(snapshot.get("filled_qty", None))
            filled_avg_price = _to_positive_float_or_none(snapshot.get("filled_avg_price", None))
            if filled_qty is not None and filled_avg_price is not None:
                partial_fills = [
                    {
                        "fill_index": 1,
                        "fill_qty": filled_qty,
                        "fill_price": filled_avg_price,
                        "fill_ts": snapshot.get("filled_at") or snapshot.get("updated_at"),
                        "fill_venue": None,
                        "source": "order_snapshot",
                    }
                ]

        return partial_fills, self._summarize_partial_fills(partial_fills)

    def submit_order(
        self,
        symbol: str,
        qty: float | int,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        client_order_id: str | None = None,
        limit_price: float | int | None = None,
    ) -> dict[str, Any]:
        symbol_u = str(symbol).upper().strip()
        side_l = str(side).lower().strip()
        order_type_l = str(order_type).lower().strip()
        client_order_id_s = str(client_order_id).strip() if client_order_id is not None else ""
        if isinstance(qty, bool):
            return {"ok": False, "error": f"invalid_qty:{qty}"}
        qty_n = _to_number(qty)
        qty_f = float(qty_n)
        limit_price_f: float | None = None

        if not symbol_u:
            return {"ok": False, "error": "invalid_symbol"}
        if side_l not in {"buy", "sell"}:
            return {"ok": False, "error": f"invalid_side:{side}"}
        if order_type_l not in {"market", "limit"}:
            return {"ok": False, "error": f"invalid_order_type:{order_type}"}
        if (not math.isfinite(qty_f)) or qty_f <= 0.0:
            return {"ok": False, "error": f"invalid_qty:{qty}"}
        if order_type_l == "limit":
            if isinstance(limit_price, bool):
                return {"ok": False, "error": f"invalid_limit_price:{limit_price}"}
            try:
                limit_price_f = float(_to_number(limit_price))
            except (TypeError, ValueError):
                return {"ok": False, "error": f"invalid_limit_price:{limit_price}"}
            if (not math.isfinite(limit_price_f)) or limit_price_f <= 0.0:
                return {"ok": False, "error": f"invalid_limit_price:{limit_price}"}
        if not client_order_id_s:
            return {"ok": False, "error": "missing_client_order_id", "client_order_id": None}
        order_payload: dict[str, Any] = {
            "symbol": symbol_u,
            "qty": qty_f,
            "side": side_l,
            "type": order_type_l,
            "time_in_force": str(time_in_force).lower().strip(),
        }
        order_payload["client_order_id"] = client_order_id_s
        if order_type_l == "limit":
            order_payload["limit_price"] = limit_price_f

        submit_sent_ts = _utc_now_iso_ms()
        try:
            order = self.api.submit_order(**order_payload)
            broker_ack_ts = _utc_now_iso_ms()
            snapshot = self._build_order_snapshot(order, fallback_client_order_id=client_order_id_s)
            if not snapshot.get("order_type"):
                snapshot["order_type"] = order_type_l
            if order_type_l == "limit" and snapshot.get("limit_price") is None:
                snapshot["limit_price"] = limit_price_f
            partial_fills, fill_summary = self._extract_fill_telemetry(snapshot=snapshot)
            result: dict[str, Any] = {
                "ok": True,
                "submit_sent_ts": submit_sent_ts,
                "broker_ack_ts": broker_ack_ts,
                **snapshot,
                "partial_fills": partial_fills,
                "fill_summary": fill_summary,
            }
            return _normalize_submit_acceptance(result)
        except APIError as exc:
            print(f"Order rejected for {symbol_u}: {exc}")
            recovered = self.get_order_by_client_order_id(client_order_id_s) if client_order_id_s else None
            if recovered is not None:
                if not self._recovery_matches_intent(
                    recovered=recovered,
                    symbol=symbol_u,
                    side=side_l,
                    qty=qty_f,
                    order_type=order_type_l,
                    limit_price=limit_price_f,
                    client_order_id=client_order_id_s,
                ):
                    return {
                        "ok": False,
                        "error": "recovery_mismatch",
                        "client_order_id": client_order_id_s,
                        "recovered_order_id": recovered.get("order_id"),
                    }
                recovered["recovered"] = True
                recovered["recovery_reason"] = str(exc)
                recovered.setdefault("order_type", order_type_l)
                if order_type_l == "limit":
                    recovered.setdefault("limit_price", limit_price_f)
                return _normalize_submit_acceptance(recovered)
            return {"ok": False, "error": str(exc), "client_order_id": client_order_id_s or None}
        except Exception as exc:
            print(f"Order failed for {symbol_u}: {exc}")
            recovered = self.get_order_by_client_order_id(client_order_id_s) if client_order_id_s else None
            if recovered is not None:
                if not self._recovery_matches_intent(
                    recovered=recovered,
                    symbol=symbol_u,
                    side=side_l,
                    qty=qty_f,
                    order_type=order_type_l,
                    limit_price=limit_price_f,
                    client_order_id=client_order_id_s,
                ):
                    return {
                        "ok": False,
                        "error": "recovery_mismatch",
                        "client_order_id": client_order_id_s,
                        "recovered_order_id": recovered.get("order_id"),
                    }
                recovered["recovered"] = True
                recovered["recovery_reason"] = str(exc)
                recovered.setdefault("order_type", order_type_l)
                if order_type_l == "limit":
                    recovered.setdefault("limit_price", limit_price_f)
                return _normalize_submit_acceptance(recovered)
            return {"ok": False, "error": str(exc), "client_order_id": client_order_id_s or None}

    @staticmethod
    def _recovery_matches_intent(
        recovered: dict[str, Any],
        *,
        symbol: str,
        side: str,
        qty: float,
        order_type: str,
        limit_price: float | None,
        client_order_id: str,
    ) -> bool:
        recovered_symbol = str(recovered.get("symbol", "")).upper().strip()
        recovered_side = str(recovered.get("side", "")).lower().strip()
        recovered_client_order_id = str(recovered.get("client_order_id", "")).strip()
        recovered_order_type = str(
            recovered.get("order_type", "") or recovered.get("type", "")
        ).lower().strip() or "market"
        recovered_qty = float(_to_number(recovered.get("qty")))
        if (
            recovered_symbol != symbol
            or recovered_side != side
            or (not math.isfinite(recovered_qty))
            or abs(recovered_qty - float(qty)) > 1e-9
            or recovered_order_type != str(order_type).lower().strip()
        ):
            return False
        if not recovered_client_order_id or recovered_client_order_id != str(client_order_id).strip():
            return False
        if str(order_type).lower().strip() == "market":
            recovered_limit_raw = recovered.get("limit_price", None)
            if recovered_limit_raw is None:
                return True
            recovered_limit_text = str(recovered_limit_raw).strip().lower()
            return recovered_limit_text in {"", "none", "null"}
        if limit_price is None:
            return False
        recovered_limit_raw = recovered.get("limit_price", None)
        if isinstance(recovered_limit_raw, bool):
            return False
        recovered_limit = float(_to_number(recovered_limit_raw))
        return math.isfinite(recovered_limit) and recovered_limit > 0.0 and abs(recovered_limit - float(limit_price)) <= 1e-9

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, Any] | None:
        client_order_id_s = str(client_order_id).strip()
        if not client_order_id_s:
            return None
        try:
            order = self.api.get_order_by_client_order_id(client_order_id_s)
            snapshot = self._build_order_snapshot(order, fallback_client_order_id="")
            partial_fills, fill_summary = self._extract_fill_telemetry(snapshot=snapshot)
            return _normalize_submit_acceptance({
                "ok": True,
                **snapshot,
                "partial_fills": partial_fills,
                "fill_summary": fill_summary,
            })
        except APIError as exc:
            print(f"Recovery lookup failed for client_order_id={client_order_id_s}: {exc}")
            return None
        except Exception as exc:
            print(f"Recovery lookup failed for client_order_id={client_order_id_s}: {exc}")
            return None

    def close_all_positions(self) -> bool:
        try:
            self.api.close_all_positions()
            return True
        except APIError as exc:
            print(f"Failed to close all positions: {exc}")
            return False
        except Exception as exc:
            print(f"Failed to close all positions: {exc}")
            return False

    def get_market_status(self) -> bool:
        clock = self.api.get_clock()
        return bool(clock.is_open)

    def get_latest_quote_snapshot(self, symbol: str, feed: str | None = None) -> dict[str, Any]:
        symbol_u = _clean_optional_text(symbol).upper()
        if not symbol_u:
            raise RuntimeError("symbol is required for quote snapshot")
        feed_s = resolve_alpaca_data_feed(feed)
        try:
            quote = self.api.get_latest_quote(symbol_u, feed=feed_s)
        except TypeError:
            quote = self.api.get_latest_quote(symbol_u)
        bid_price = _to_positive_float_or_none(
            getattr(quote, "bid_price", None) or getattr(quote, "bidprice", None)
        )
        ask_price = _to_positive_float_or_none(
            getattr(quote, "ask_price", None) or getattr(quote, "askprice", None)
        )
        if bid_price is None or ask_price is None:
            raise RuntimeError(f"Unable to resolve bid/ask midpoint for {symbol_u}")
        mid_price = float((bid_price + ask_price) / 2.0)
        return {
            "symbol": symbol_u,
            "bid_price": float(bid_price),
            "ask_price": float(ask_price),
            "mid_price": mid_price,
            "quote_ts": _to_iso_utc_ms(getattr(quote, "timestamp", None) or getattr(quote, "t", None)),
            "snapshot_ts": _utc_now_iso_ms(),
            "source": "alpaca_latest_quote",
            "provider": "alpaca",
            "provider_feed": feed_s,
            "source_quality": "operational",
            "quote_quality": _quote_quality_for_feed(feed_s),
            "license_scope": "paper_operational_market_data",
        }

    def get_latest_price(self, symbol: str) -> float:
        """Best-effort latest price lookup for order sizing."""
        try:
            trade = self.api.get_latest_trade(symbol)
            px = _to_number(getattr(trade, "price", None))
            if px > 0:
                return float(px)
        except Exception:
            pass

        try:
            quote = self.get_latest_quote_snapshot(symbol)
            return float(quote["mid_price"])
        except Exception:
            pass

        try:
            bar = self.api.get_latest_bar(symbol)
            close_px = _to_number(getattr(bar, "c", None))
            if close_px > 0:
                return float(close_px)
        except Exception:
            pass

        raise RuntimeError(f"Unable to fetch latest price for {symbol}")
