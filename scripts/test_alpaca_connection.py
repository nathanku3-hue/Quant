from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from execution.broker_api import AlpacaBroker


def _mask_key(value: str | None) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def main() -> None:
    raw_apca_key = os.environ.get("APCA_API_KEY_ID")
    raw_apca_base = os.environ.get("APCA_API_BASE_URL")

    print(f"Using Key ID: {_mask_key(raw_apca_key)}")
    print(f"Using Base URL: {raw_apca_base or '<missing>'}")

    # Backward-compatible debug lines for alternative env naming.
    if not raw_apca_key and os.environ.get("ALPACA_API_KEY"):
        print(f"Fallback ALPACA_API_KEY: {_mask_key(os.environ.get('ALPACA_API_KEY'))}")
    if not raw_apca_base and os.environ.get("ALPACA_BASE_URL"):
        print(f"Fallback ALPACA_BASE_URL: {os.environ.get('ALPACA_BASE_URL')}")

    try:
        broker = AlpacaBroker()
        state = broker.get_portfolio_state()
        market_status = "OPEN" if broker.get_market_status() else "CLOSED"
    except Exception as exc:
        print(f"Alpaca connection failed: {exc}")
        return

    print("Connected to Alpaca Paper Trading.")
    print(f"Current Equity: ${float(state['equity']):,.2f}")
    print(f"Market Status: {market_status}")


if __name__ == "__main__":
    main()
