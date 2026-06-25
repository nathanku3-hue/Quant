from __future__ import annotations

import os
from typing import Any

from data.providers.alpaca_provider import AlpacaMarketDataProvider
from data.providers.yahoo_provider import YahooMarketDataProvider


PROVIDER_ENV = "TZ_MARKET_DATA_PROVIDER"


def build_market_data_provider(name: str | None = None, **kwargs: Any):
    provider = (name or os.environ.get(PROVIDER_ENV) or "yahoo").strip().lower()
    if provider == "yahoo":
        return YahooMarketDataProvider(**kwargs)
    if provider == "alpaca":
        return AlpacaMarketDataProvider(**kwargs)
    raise ValueError(f"Unsupported market data provider: {provider}")

