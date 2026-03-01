from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main_bot_orchestrator import execute_orders_with_idempotent_retry
from execution.broker_api import AlpacaBroker
from execution.rebalancer import PortfolioRebalancer


def _print_state(label: str, state: dict) -> None:
    print(f"\n{label}")
    print(f"Cash:   ${float(state['cash']):,.2f}")
    print(f"Equity: ${float(state['equity']):,.2f}")
    print(f"Positions: {state['positions']}")


def main() -> int:
    broker = AlpacaBroker()
    rebalancer = PortfolioRebalancer(broker)

    targets = {"SPY": 0.05}
    print(f"Target weights: {targets}")

    before = broker.get_portfolio_state()
    _print_state("Portfolio before rebalance:", before)

    orders = rebalancer.calculate_orders(targets)
    print(f"\nCalculated {len(orders)} order(s).")
    for order in orders:
        print(
            " - {side} {qty} {symbol} at ~${price:.2f} "
            "(delta=${delta_value:.2f}, target_w={target_weight:.4f}, current_qty={current_qty})".format(
                **order
            )
        )

    trade_day = datetime.now(timezone.utc).strftime("%Y%m%d")
    seeded_orders = []
    for order in orders:
        seeded = dict(order)
        seeded.setdefault("trade_day", trade_day)
        seeded_orders.append(seeded)

    execute_results = execute_orders_with_idempotent_retry(rebalancer, seeded_orders)
    ok_count = sum(1 for row in execute_results if row.get("result", {}).get("ok") is True)
    print(f"\nExecution results: {ok_count}/{len(execute_results)} accepted.")
    if ok_count != len(execute_results):
        print("[ERROR] One or more orders failed; exiting non-zero.")
        return 1

    after = broker.get_portfolio_state()
    _print_state("Portfolio after rebalance:", after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
