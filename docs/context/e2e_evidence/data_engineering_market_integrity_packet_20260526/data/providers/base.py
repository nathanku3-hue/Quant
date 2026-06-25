from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    bid_price: float | None
    ask_price: float | None
    mid_price: float | None
    quote_ts: str | None
    snapshot_ts: str
    provider: str
    provider_feed: str
    source_quality: str
    quote_quality: str
    license_scope: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "mid_price": self.mid_price,
            "quote_ts": self.quote_ts,
            "snapshot_ts": self.snapshot_ts,
            "asof_ts": self.snapshot_ts,
            "provider": self.provider,
            "provider_feed": self.provider_feed,
            "source_quality": self.source_quality,
            "quote_quality": self.quote_quality,
            "license_scope": self.license_scope,
        }


class MarketDataPort(Protocol):
    provider_name: str

    def latest_quote(self, symbol: str) -> dict[str, Any]:
        ...

