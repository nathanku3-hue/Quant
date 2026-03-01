from __future__ import annotations

import datetime
import hashlib
import math
from typing import Any

from execution.broker_api import AlpacaBroker
from execution.risk_interceptor import RiskDecision
from execution.risk_interceptor import RiskInterceptor


class PortfolioRebalancer:
    def __init__(
        self,
        broker: AlpacaBroker,
        dust_filter_dollars: float = 10.0,
        max_orders_per_run: int = 64,
        max_target_gross: float = 1.0,
        risk_interceptor: RiskInterceptor | None = None,
        halt_on_risk_block: bool = False,
    ) -> None:
        self.broker = broker
        self.dust_filter_dollars = float(dust_filter_dollars)
        self.max_orders_per_run = int(max_orders_per_run)
        self.max_target_gross = float(max_target_gross)
        self.risk_interceptor = risk_interceptor if risk_interceptor is not None else RiskInterceptor()
        self.halt_on_risk_block = bool(halt_on_risk_block)

    @staticmethod
    def _broker_supports_risk_context(broker: Any) -> bool:
        """Risk checks require position/equity snapshot + latest price lookup."""
        return callable(getattr(broker, "get_portfolio_state", None)) and callable(
            getattr(broker, "get_latest_price", None)
        )

    @staticmethod
    def _generate_client_order_id(symbol: str, side: str, qty: int, order: dict[str, Any]) -> str:
        trade_day = str(order.get("trade_day", "")).strip()
        if not trade_day:
            trade_day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        digest_source = f"{symbol}|{side}|{qty}"
        digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()[:12].upper()
        return f"{trade_day}-{symbol}-{side.upper()}-{qty}-{digest}"

    def calculate_orders(self, target_weights: dict[str, float]) -> list[dict[str, Any]]:
        if not isinstance(target_weights, dict):
            raise TypeError("target_weights must be a dictionary of {symbol: weight}")

        normalized_targets: dict[str, float] = {}
        for symbol, weight in target_weights.items():
            sym = str(symbol).upper().strip()
            w = float(weight)
            if not sym:
                raise ValueError("target_weights contains an empty symbol")
            if not math.isfinite(w):
                raise ValueError(f"target_weights[{sym}] is non-finite")
            if w < 0.0:
                raise ValueError(f"target_weights[{sym}] is negative ({w}); short targets are not supported")
            normalized_targets[sym] = w

        gross_target = float(sum(normalized_targets.values()))
        if gross_target > self.max_target_gross + 1e-9:
            raise ValueError(
                f"Target gross exposure {gross_target:.6f} exceeds max_target_gross={self.max_target_gross:.6f}"
            )

        state = self.broker.get_portfolio_state()
        total_equity = float(state.get("equity", 0.0))
        current_positions: dict[str, float] = {}
        positions_raw = state.get("positions", {})
        if isinstance(positions_raw, dict):
            for symbol, qty in positions_raw.items():
                sym = str(symbol).upper().strip()
                if not sym:
                    continue
                qty_float = float(qty)
                if not math.isfinite(qty_float):
                    raise ValueError(f"invalid current position quantity for {sym}: {qty}")
                current_positions[sym] = qty_float

        symbols = set(current_positions.keys()) | set(normalized_targets.keys())
        orders: list[dict[str, Any]] = []

        for symbol in sorted(symbols):
            target_weight = normalized_targets.get(symbol, 0.0)
            current_qty = current_positions.get(symbol, 0.0)

            if total_equity <= 0:
                continue

            try:
                current_price = float(self.broker.get_latest_price(symbol))
            except Exception as exc:
                print(f"[WARN] Skipping {symbol}: cannot resolve price ({exc})")
                continue

            if current_price <= 0:
                print(f"[WARN] Skipping {symbol}: non-positive price {current_price}")
                continue

            target_value = total_equity * target_weight
            current_value = current_qty * current_price
            delta_value = target_value - current_value

            # Ignore tiny notional adjustments.
            if abs(delta_value) < self.dust_filter_dollars:
                continue

            # Round-to-nearest reduces persistent under-allocation drift from truncation.
            qty_to_trade = int(round(delta_value / current_price))
            if qty_to_trade == 0:
                continue

            side = "buy" if qty_to_trade > 0 else "sell"
            qty_abs = abs(qty_to_trade)
            if side == "sell":
                # Guard against accidental flip into short due rounding or stale inventory state.
                max_sell = int(math.floor(abs(current_qty) + 1e-12))
                qty_abs = min(qty_abs, max_sell)
                if qty_abs <= 0:
                    continue

            orders.append(
                {
                    "symbol": symbol,
                    "qty": qty_abs,
                    "side": side,
                    "price": current_price,
                    "delta_value": delta_value,
                    "target_weight": target_weight,
                    "current_qty": current_qty,
                }
            )

        # Sell-first execution reduces avoidable buy rejects under cash constraints.
        orders.sort(key=lambda row: (0 if str(row.get("side", "")).lower() == "sell" else 1, str(row["symbol"])))

        if len(orders) > self.max_orders_per_run:
            raise ValueError(
                f"Calculated {len(orders)} orders which exceeds max_orders_per_run={self.max_orders_per_run}"
            )
        return orders

    def execute_orders(self, orders: list[dict[str, Any]], dry_run: bool = False) -> list[dict[str, Any]]:
        if not orders:
            print("No executable orders after dust/quantity filters.")
            return []
        if len(orders) > self.max_orders_per_run:
            raise ValueError(
                f"Order list size {len(orders)} exceeds max_orders_per_run={self.max_orders_per_run}"
            )

        results: list[dict[str, Any]] = []
        total = len(orders)
        seen: set[str] = set()
        seen_client_order_ids: set[str] = set()
        prepared_orders: list[tuple[dict[str, Any], dict[str, Any]]] = []
        risk_state: dict[str, Any] | None = None
        risk_bootstrap_error: str | None = None
        batch_halted = False
        batch_halt_reason = ""

        def _persist_risk_block(
            decision: RiskDecision, normalized_order: dict[str, Any]
        ) -> tuple[str | None, str | None]:
            try:
                path = self.risk_interceptor.persist_block_decision(
                    decision=decision,
                    order=normalized_order,
                    portfolio_state=risk_state,
                )
                return path, None
            except Exception as audit_exc:
                return None, str(audit_exc)

        # Normalize and validate the full batch before any submit side effects.
        for order in orders:
            symbol = str(order["symbol"]).upper().strip()
            if not symbol:
                raise ValueError("Invalid order symbol: empty")
            qty_raw = order["qty"]
            if isinstance(qty_raw, bool):
                raise ValueError(f"Invalid order quantity for {symbol}: {qty_raw}")
            try:
                qty_float = float(qty_raw)
            except (TypeError, ValueError):
                raise ValueError(f"Invalid order quantity for {symbol}: {qty_raw}") from None
            if not math.isfinite(qty_float):
                raise ValueError(f"Invalid order quantity for {symbol}: {qty_raw}")
            qty = int(round(qty_float))
            if abs(qty_float - float(qty)) > 1e-9:
                raise ValueError(f"Invalid order quantity for {symbol}: {qty_raw} (must be an integer)")
            side = str(order["side"]).lower()
            order_type = str(order.get("order_type", "market")).lower().strip()
            client_order_id = str(order.get("client_order_id", "")).strip()
            limit_price: float | None = None
            if not client_order_id:
                client_order_id = self._generate_client_order_id(
                    symbol=symbol,
                    side=side,
                    qty=qty,
                    order=order,
                )
            if symbol in seen:
                raise ValueError(f"Duplicate order symbol detected in batch: {symbol}")
            seen.add(symbol)
            if client_order_id in seen_client_order_ids:
                raise ValueError(f"Duplicate client_order_id detected in batch: {client_order_id}")
            seen_client_order_ids.add(client_order_id)
            if qty <= 0:
                raise ValueError(f"Invalid order quantity for {symbol}: {qty}")
            if side not in {"buy", "sell"}:
                raise ValueError(f"Invalid order side for {symbol}: {side}")
            if order_type not in {"market", "limit"}:
                raise ValueError(f"Invalid order type for {symbol}: {order_type}")
            if order_type == "limit":
                limit_price_raw = order.get("limit_price", None)
                if isinstance(limit_price_raw, bool):
                    raise ValueError(f"Invalid limit price for {symbol}: {limit_price_raw}")
                try:
                    limit_price = float(limit_price_raw)
                except (TypeError, ValueError):
                    raise ValueError(f"Invalid limit price for {symbol}: {limit_price_raw}") from None
                if not math.isfinite(limit_price) or limit_price <= 0.0:
                    raise ValueError(f"Invalid limit price for {symbol}: {limit_price_raw}")

            normalized_order = dict(order)
            normalized_order["symbol"] = symbol
            normalized_order["qty"] = qty
            normalized_order["side"] = side
            normalized_order["order_type"] = order_type
            normalized_order["client_order_id"] = client_order_id
            normalized_order["limit_price"] = limit_price
            prepared_orders.append((order, normalized_order))

        risk_checks_enabled = self._broker_supports_risk_context(self.broker)
        if not risk_checks_enabled:
            risk_bootstrap_error = "risk context unavailable (missing broker get_portfolio_state/get_latest_price)"
            risk_checks_enabled = True
        if risk_checks_enabled and risk_bootstrap_error is None:
            try:
                risk_state = self.risk_interceptor.capture_portfolio_state(self.broker)
            except Exception as exc:
                risk_bootstrap_error = str(exc)

        for idx, (order, normalized_order) in enumerate(prepared_orders, start=1):
            symbol = str(normalized_order["symbol"]).upper()
            qty = int(normalized_order["qty"])
            side = str(normalized_order["side"]).lower()
            order_type = str(normalized_order["order_type"]).lower().strip()
            client_order_id = str(normalized_order["client_order_id"]).strip()
            limit_price_value = normalized_order.get("limit_price", None)
            limit_price: float | None = None if limit_price_value is None else float(limit_price_value)

            decision: RiskDecision
            if batch_halted:
                decision = self.risk_interceptor.block(
                    reason_code="risk_batch_halt",
                    reason=f"batch halted after prior risk block ({batch_halt_reason})",
                )
            elif risk_bootstrap_error:
                decision = self.risk_interceptor.block(
                    reason_code="risk_check_error",
                    reason=f"risk bootstrap failed: {risk_bootstrap_error}",
                )
            else:
                try:
                    decision = self.risk_interceptor.evaluate(
                        order=normalized_order,
                        broker=self.broker,
                        portfolio_state=dict(risk_state or {}),
                    )
                except Exception as exc:
                    decision = self.risk_interceptor.block(
                        reason_code="risk_check_error",
                        reason=f"risk interceptor error: {exc}",
                    )

            if decision.action == "BLOCK":
                audit_path, audit_error = _persist_risk_block(decision, normalized_order)
                reason_code = decision.reason_code
                reason = decision.reason
                if audit_error:
                    reason_code = "risk_blocked_audit_failed"
                    reason = f"{decision.reason}; audit persistence failed: {audit_error}"
                result = {
                    "ok": False,
                    "status": "blocked",
                    "error": "risk_blocked",
                    "reason_code": reason_code,
                    "reason": reason,
                    "risk_metrics": decision.metrics,
                    "risk_audit_path": audit_path,
                    "risk_audit_error": audit_error,
                    "client_order_id": client_order_id,
                    "order_type": order_type,
                    "limit_price": limit_price,
                }
                print(
                    f"[{idx}/{total}] BLOCKED {side.upper()} {qty} {symbol}: {reason} "
                    f"(client_order_id={client_order_id})"
                )
                results.append({"order": order, "result": result})
                if (
                    decision.reason_code != "risk_batch_halt"
                    and (self.halt_on_risk_block or bool(order.get("halt_batch_on_block", False)))
                ):
                    batch_halted = True
                    batch_halt_reason = decision.reason_code
                if audit_error:
                    batch_halted = True
                    batch_halt_reason = "risk_audit_persist_failed"
                continue

            print(f"[{idx}/{total}] Submitting {side.upper()} {qty} {symbol} ...")
            if dry_run:
                result = {
                    "ok": True,
                    "dry_run": True,
                    "status": "simulated",
                    "client_order_id": client_order_id,
                    "order_type": order_type,
                    "limit_price": limit_price,
                }
            else:
                submit_kwargs: dict[str, Any] = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "client_order_id": client_order_id,
                }
                # Preserve optional order intent fields without breaking legacy callers.
                if order_type != "market":
                    submit_kwargs["order_type"] = order_type
                if order_type == "limit":
                    submit_kwargs["limit_price"] = limit_price
                try:
                    result = self.broker.submit_order(**submit_kwargs)
                except Exception as exc:
                    result = {
                        "ok": False,
                        "error": f"submit_exception:{exc}",
                        "client_order_id": client_order_id,
                    }
                if not result.get("client_order_id"):
                    result["client_order_id"] = client_order_id
                result.setdefault("order_type", order_type)
                if order_type == "limit":
                    result.setdefault("limit_price", limit_price)
            if result.get("ok") is True:
                print(
                    f"[{idx}/{total}] ACCEPTED {side.upper()} {qty} {symbol} "
                    f"(order_id={result.get('order_id')}, "
                    f"client_order_id={result.get('client_order_id')}, "
                    f"status={result.get('status')})"
                )
            else:
                print(
                    f"[{idx}/{total}] FAILED {side.upper()} {qty} {symbol}: {result.get('error')} "
                    f"(client_order_id={result.get('client_order_id')})"
                )
            results.append({"order": order, "result": result})
            # Conservative projection policy for pending acknowledgements:
            # credit buy exposure immediately, but do not credit risk-reducing sells
            # until downstream fill telemetry confirms execution.
            if risk_checks_enabled and result.get("ok") is True and side == "buy":
                try:
                    risk_state = self.risk_interceptor.project_state(
                        order=normalized_order,
                        portfolio_state=dict(risk_state or {}),
                    )
                except Exception as exc:
                    decision = self.risk_interceptor.block(
                        reason_code="risk_state_update_error",
                        reason=f"risk state update failed post-submit: {exc}",
                    )
                    _persist_risk_block(decision, normalized_order)
                    batch_halted = True
                    batch_halt_reason = decision.reason_code
        return results
