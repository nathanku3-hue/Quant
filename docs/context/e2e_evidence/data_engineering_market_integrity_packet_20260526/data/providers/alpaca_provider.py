from __future__ import annotations

from typing import Any

from execution.broker_api import AlpacaBroker
from execution.broker_api import DEFAULT_ALPACA_DATA_FEED
from execution.broker_api import resolve_alpaca_data_feed


class AlpacaMarketDataProvider:
    provider_name = "alpaca"

    def __init__(self, *, feed: str | None = None, broker: Any | None = None) -> None:
        self.feed = resolve_alpaca_data_feed(feed or DEFAULT_ALPACA_DATA_FEED)
        self.broker = broker if broker is not None else AlpacaBroker()

    def latest_quote(self, symbol: str) -> dict[str, Any]:
        getter = getattr(self.broker, "get_latest_quote_snapshot", None)
        if not callable(getter):
            raise RuntimeError("broker missing get_latest_quote_snapshot()")
        try:
            return getter(symbol, feed=self.feed)
        except TypeError:
            return getter(symbol)

