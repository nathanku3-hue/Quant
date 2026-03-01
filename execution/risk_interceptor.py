from __future__ import annotations

import datetime
import json
import math
import os
import uuid
from dataclasses import dataclass
from typing import Any, Iterable


def _clean_optional_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(parsed):
        return None
    return float(parsed)


def _sanitize_token(value: str, fallback: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in str(value))
    cleaned = cleaned.strip("_")
    return cleaned or fallback


@dataclass(frozen=True)
class RiskDecision:
    action: str
    reason_code: str
    reason: str
    metrics: dict[str, Any]


@dataclass(frozen=True)
class RiskInterceptor:
    max_single_asset_weight: float = 0.25
    max_sector_weight: float = 0.60
    vix_kill_switch: float = 45.0
    var_confidence_z: float = 1.65
    max_var_proxy: float = 0.08
    default_symbol_volatility: float = 0.02
    long_only: bool = True
    audit_dir: str = "logs/risk"

    def allow(self, *, metrics: dict[str, Any] | None = None) -> RiskDecision:
        return RiskDecision(
            action="ALLOW",
            reason_code="ok",
            reason="risk checks passed",
            metrics=dict(metrics or {}),
        )

    def block(self, *, reason_code: str, reason: str, metrics: dict[str, Any] | None = None) -> RiskDecision:
        return RiskDecision(
            action="BLOCK",
            reason_code=str(reason_code),
            reason=str(reason),
            metrics=dict(metrics or {}),
        )

    def capture_portfolio_state(self, broker: Any) -> dict[str, Any]:
        getter = getattr(broker, "get_portfolio_state", None)
        if not callable(getter):
            raise RuntimeError("broker missing get_portfolio_state() required for risk checks")
        state_raw = getter()
        if not isinstance(state_raw, dict):
            raise RuntimeError("broker.get_portfolio_state() returned invalid payload")

        equity = _coerce_float(state_raw.get("equity"))
        if equity is None or equity <= 0.0:
            raise RuntimeError(f"invalid portfolio equity for risk checks: {state_raw.get('equity')}")

        positions_raw = state_raw.get("positions", {})
        if not isinstance(positions_raw, dict):
            raise RuntimeError("broker.get_portfolio_state().positions must be a dictionary")
        positions: dict[str, float] = {}
        for symbol_raw, qty_raw in positions_raw.items():
            symbol = _clean_optional_text(symbol_raw).upper()
            if not symbol:
                continue
            qty = _coerce_float(qty_raw)
            if qty is None:
                raise RuntimeError(f"invalid position quantity for {symbol}: {qty_raw}")
            positions[symbol] = float(qty)

        state: dict[str, Any] = {
            "equity": float(equity),
            "positions": positions,
        }
        for key in ("sector_map", "sectors", "vix", "vix_level"):
            if key in state_raw:
                state[key] = state_raw.get(key)
        for key in ("volatility_by_symbol", "symbol_volatility"):
            source = state_raw.get(key, {})
            if not isinstance(source, dict):
                continue
            normalized_vol: dict[str, Any] = {}
            for sym_raw, vol_raw in source.items():
                sym = _clean_optional_text(sym_raw).upper()
                if sym:
                    normalized_vol[sym] = vol_raw
            state[key] = normalized_vol
        return state

    def project_state(self, *, order: dict[str, Any], portfolio_state: dict[str, Any]) -> dict[str, Any]:
        symbol = _clean_optional_text(order.get("symbol", "")).upper()
        side = _clean_optional_text(order.get("side", "")).lower()
        qty_raw = order.get("qty", 0)
        if isinstance(qty_raw, bool):
            raise ValueError("order qty must be numeric")
        qty = _coerce_float(qty_raw)
        if qty is None:
            raise ValueError(f"order qty must be integral, got {qty_raw}") from None
        qty_integral = int(round(qty))
        if abs(qty - float(qty_integral)) > 1e-9:
            raise ValueError(f"order qty must be integral, got {qty_raw}")
        qty = qty_integral
        if qty <= 0:
            raise ValueError(f"order qty must be positive, got {qty_raw}")
        if not symbol:
            raise ValueError("order symbol is required")
        if side not in {"buy", "sell"}:
            raise ValueError(f"order side must be buy/sell, got {order.get('side')}")

        positions_raw = portfolio_state.get("positions", {})
        if not isinstance(positions_raw, dict):
            raise ValueError("portfolio_state.positions must be a dictionary")
        positions = {str(sym).upper(): float(q) for sym, q in positions_raw.items()}
        current_qty = float(positions.get(symbol, 0.0))
        projected_qty = current_qty + float(qty) if side == "buy" else current_qty - float(qty)
        if self.long_only and projected_qty < -1e-12:
            raise ValueError(
                f"long_only projection breach for {symbol}: projected_qty={projected_qty:.6f}"
            )
        positions[symbol] = projected_qty

        projected = dict(portfolio_state)
        projected["positions"] = positions
        return projected

    def evaluate(
        self,
        *,
        order: dict[str, Any],
        broker: Any,
        portfolio_state: dict[str, Any],
    ) -> RiskDecision:
        symbol = _clean_optional_text(order.get("symbol", "")).upper()
        side = _clean_optional_text(order.get("side", "")).lower()
        try:
            projected_state = self.project_state(order=order, portfolio_state=portfolio_state)
        except ValueError as exc:
            return self.block(
                reason_code="invalid_order_projection",
                reason=f"projected state rejected: {exc}",
                metrics={
                    "symbol": symbol,
                    "side": side,
                    "qty": order.get("qty"),
                    "long_only": bool(self.long_only),
                },
            )

        equity = _coerce_float(projected_state.get("equity"))
        if equity is None or equity <= 0.0:
            raise RuntimeError(f"invalid equity during risk evaluation: {projected_state.get('equity')}")

        vix_value = self._resolve_vix(order=order, portfolio_state=projected_state, broker=broker)
        if side == "buy" and vix_value is not None and vix_value > float(self.vix_kill_switch):
            return self.block(
                reason_code="vix_kill_switch",
                reason=f"buy entries blocked while VIX={vix_value:.2f} exceeds {self.vix_kill_switch:.2f}",
                metrics={"vix": float(vix_value), "vix_kill_switch": float(self.vix_kill_switch)},
            )

        positions = projected_state.get("positions", {})
        if not isinstance(positions, dict):
            raise RuntimeError("portfolio positions unavailable for risk evaluation")
        active_symbols = {str(sym).upper() for sym, qty in positions.items() if abs(float(qty)) > 1e-12}
        if symbol:
            active_symbols.add(symbol)

        prices = self._resolve_prices(symbols=active_symbols, order=order, broker=broker)
        exposure_by_symbol: dict[str, float] = {}
        for sym, qty_raw in positions.items():
            qty = float(qty_raw)
            price = prices.get(sym)
            if price is None or abs(qty) <= 1e-12:
                continue
            exposure_by_symbol[sym] = abs(qty) * float(price)

        if not exposure_by_symbol:
            return self.allow(metrics={"equity": float(equity), "vix": vix_value})

        weight_by_symbol = {
            sym: (notional / float(equity)) for sym, notional in exposure_by_symbol.items()
        }
        max_symbol = max(weight_by_symbol, key=weight_by_symbol.get)
        max_single_weight = float(weight_by_symbol[max_symbol])
        if max_single_weight > float(self.max_single_asset_weight) + 1e-9:
            return self.block(
                reason_code="max_single_asset_weight",
                reason=(
                    f"single-asset weight breach {max_symbol}={max_single_weight:.4f} "
                    f"> {self.max_single_asset_weight:.4f}"
                ),
                metrics={
                    "symbol": max_symbol,
                    "weight": max_single_weight,
                    "limit": float(self.max_single_asset_weight),
                },
            )

        sector_by_symbol = self._resolve_sector_map(
            symbols=active_symbols,
            order=order,
            portfolio_state=projected_state,
            broker=broker,
        )
        sector_weights: dict[str, float] = {}
        for sym, weight in weight_by_symbol.items():
            sector = sector_by_symbol.get(sym, "UNKNOWN")
            sector_weights[sector] = float(sector_weights.get(sector, 0.0) + float(weight))

        max_sector = max(sector_weights, key=sector_weights.get)
        max_sector_weight = float(sector_weights[max_sector])
        if max_sector_weight > float(self.max_sector_weight) + 1e-9:
            return self.block(
                reason_code="max_sector_weight",
                reason=(
                    f"sector weight breach {max_sector}={max_sector_weight:.4f} "
                    f"> {self.max_sector_weight:.4f}"
                ),
                metrics={
                    "sector": max_sector,
                    "weight": max_sector_weight,
                    "limit": float(self.max_sector_weight),
                },
            )

        var_proxy = self._compute_var_proxy(
            weight_by_symbol=weight_by_symbol,
            order=order,
            portfolio_state=projected_state,
            broker=broker,
        )
        if var_proxy > float(self.max_var_proxy) + 1e-9:
            return self.block(
                reason_code="var_proxy",
                reason=f"VaR proxy breach {var_proxy:.4f} > {self.max_var_proxy:.4f}",
                metrics={"var_proxy": float(var_proxy), "limit": float(self.max_var_proxy)},
            )

        return self.allow(
            metrics={
                "equity": float(equity),
                "vix": float(vix_value) if vix_value is not None else None,
                "max_single_asset_weight": max_single_weight,
                "max_sector_weight": max_sector_weight,
                "var_proxy": float(var_proxy),
            }
        )

    def persist_block_decision(
        self,
        *,
        decision: RiskDecision,
        order: dict[str, Any],
        portfolio_state: dict[str, Any] | None,
    ) -> str:
        os.makedirs(self.audit_dir, exist_ok=True)
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        stamp = now_utc.strftime("%Y%m%dT%H%M%S%fZ")
        symbol = _sanitize_token(_clean_optional_text(order.get("symbol", "")).upper(), "UNKNOWN")
        cid = _sanitize_token(_clean_optional_text(order.get("client_order_id", "")), "NO_CID")
        nonce = uuid.uuid4().hex[:10]
        filename = f"risk_block_{stamp}_{symbol}_{cid}_{nonce}.json"
        target_path = os.path.join(self.audit_dir, filename)
        temp_path = f"{target_path}.{os.getpid()}.{int(now_utc.timestamp() * 1000)}.tmp"

        payload = {
            "timestamp_utc": now_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "decision": {
                "action": decision.action,
                "reason_code": decision.reason_code,
                "reason": decision.reason,
                "metrics": decision.metrics,
            },
            "order": dict(order),
            "portfolio_state": dict(portfolio_state or {}),
        }

        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
            os.replace(temp_path, target_path)
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
        return target_path

    def _resolve_prices(self, *, symbols: Iterable[str], order: dict[str, Any], broker: Any) -> dict[str, float]:
        _ = order
        prices: dict[str, float] = {}
        getter = getattr(broker, "get_latest_price", None)
        if not callable(getter):
            raise RuntimeError("broker missing get_latest_price required for risk checks")
        for sym in sorted({str(s).upper() for s in symbols if str(s).strip()}):
            raw_price = getter(sym)
            price = _coerce_float(raw_price)
            if price is None or price <= 0.0:
                raise RuntimeError(f"invalid latest price for risk checks {sym}: {raw_price}")
            prices[sym] = float(price)
        return prices

    def _resolve_sector_map(
        self,
        *,
        symbols: Iterable[str],
        order: dict[str, Any],
        portfolio_state: dict[str, Any],
        broker: Any,
    ) -> dict[str, str]:
        normalized_symbols = sorted({str(sym).upper() for sym in symbols if str(sym).strip()})
        sector_map: dict[str, str] = {}

        batch_getter = getattr(broker, "get_sector_map", None)
        if callable(batch_getter):
            try:
                source = batch_getter(normalized_symbols)
            except TypeError:
                source = batch_getter()
            except Exception:
                source = {}
            if isinstance(source, dict):
                for sym_raw, sector_raw in source.items():
                    sym = _clean_optional_text(sym_raw).upper()
                    if sym:
                        sector_map[sym] = self._normalize_sector(sector_raw)

        one_getter = getattr(broker, "get_sector_for_symbol", None)
        if callable(one_getter):
            for sym in normalized_symbols:
                existing = sector_map.get(sym, "")
                if existing and existing != "UNKNOWN":
                    continue
                try:
                    resolved = self._normalize_sector(one_getter(sym))
                    if resolved != "UNKNOWN" or not existing:
                        sector_map[sym] = resolved
                except Exception:
                    pass

        # Fall back to portfolio snapshot metadata if broker cannot classify every symbol.
        for key in ("sector_map", "sectors"):
            source = portfolio_state.get(key, {})
            if not isinstance(source, dict):
                continue
            for sym_raw, sector_raw in source.items():
                sym = _clean_optional_text(sym_raw).upper()
                if not sym:
                    continue
                resolved = self._normalize_sector(sector_raw)
                if sym not in sector_map or sector_map.get(sym) == "UNKNOWN":
                    sector_map[sym] = resolved

        order_symbol = _clean_optional_text(order.get("symbol", "")).upper()
        order_sector_raw = _clean_optional_text(order.get("sector"))
        if order_symbol and order_sector_raw and (
            order_symbol not in sector_map or sector_map.get(order_symbol) == "UNKNOWN"
        ):
            sector_map[order_symbol] = self._normalize_sector(order_sector_raw)

        for sym in normalized_symbols:
            if not sector_map.get(sym):
                sector_map[sym] = "UNKNOWN"
        return sector_map

    @staticmethod
    def _normalize_sector(value: Any) -> str:
        normalized = _clean_optional_text(value).upper()
        return normalized or "UNKNOWN"

    def _resolve_vix(self, *, order: dict[str, Any], portfolio_state: dict[str, Any], broker: Any) -> float | None:
        candidates: list[Any] = []

        for method_name in ("get_vix_level", "get_vix"):
            getter = getattr(broker, method_name, None)
            if callable(getter):
                try:
                    candidates.append(getter())
                except Exception:
                    continue
        candidates.extend(
            [
                portfolio_state.get("vix"),
                portfolio_state.get("vix_level"),
                order.get("vix"),
                order.get("vix_level"),
            ]
        )

        for value in candidates:
            parsed = _coerce_float(value)
            if parsed is not None and parsed >= 0.0:
                return float(parsed)
        return None

    def _resolve_symbol_volatility(
        self,
        *,
        symbol: str,
        order: dict[str, Any],
        portfolio_state: dict[str, Any],
        broker: Any,
    ) -> float:
        symbol_u = str(symbol).upper()
        getter = getattr(broker, "get_symbol_volatility", None)
        if callable(getter):
            try:
                parsed = _coerce_float(getter(symbol_u))
                if parsed is not None and parsed > 0.0:
                    return float(parsed)
            except Exception:
                pass

        for key in ("volatility_by_symbol", "symbol_volatility"):
            source = portfolio_state.get(key, {})
            if not isinstance(source, dict):
                continue
            parsed = _coerce_float(source.get(symbol_u))
            if parsed is not None and parsed > 0.0:
                return float(parsed)

        order_symbol = _clean_optional_text(order.get("symbol", "")).upper()
        if symbol_u == order_symbol:
            for key in ("volatility", "volatility_1d", "vol"):
                parsed = _coerce_float(order.get(key))
                if parsed is not None and parsed > 0.0:
                    return float(parsed)

        return float(self.default_symbol_volatility)

    def _compute_var_proxy(
        self,
        *,
        weight_by_symbol: dict[str, float],
        order: dict[str, Any],
        portfolio_state: dict[str, Any],
        broker: Any,
    ) -> float:
        variance = 0.0
        for symbol, weight in weight_by_symbol.items():
            vol = self._resolve_symbol_volatility(
                symbol=symbol,
                order=order,
                portfolio_state=portfolio_state,
                broker=broker,
            )
            variance += float(weight) * float(weight) * float(vol) * float(vol)
        variance = max(variance, 0.0)
        return float(self.var_confidence_z) * math.sqrt(variance)
