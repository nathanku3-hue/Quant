from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import utc_now_iso
from data.providers.base import QuoteSnapshot


class YahooMarketDataProvider:
    provider_name = "yahoo"
    provider_feed = "yahoo_public_api"
    source_quality = SOURCE_QUALITY_NON_CANONICAL
    license_scope = "research_education_convenience_only"

    def latest_quote(self, symbol: str) -> dict[str, Any]:
        symbol_u = str(symbol).upper().strip()
        if not symbol_u:
            raise ValueError("symbol is required")
        ticker = yf.Ticker(symbol_u)
        price = None
        quote_ts = None

        fast_info = getattr(ticker, "fast_info", {}) or {}
        for key in ("last_price", "lastPrice", "regular_market_price"):
            try:
                raw = fast_info.get(key) if hasattr(fast_info, "get") else getattr(fast_info, key, None)
            except Exception:
                raw = None
            if raw is not None:
                price = float(raw)
                break

        if price is None:
            hist = ticker.history(period="1d")
            if hist is not None and not hist.empty and "Close" in hist.columns:
                price = float(pd.to_numeric(hist["Close"], errors="coerce").dropna().iloc[-1])
                quote_ts = str(pd.Timestamp(hist.index[-1]).isoformat())

        if price is None or price <= 0:
            raise RuntimeError(f"Unable to resolve Yahoo quote for {symbol_u}")

        snapshot = QuoteSnapshot(
            symbol=symbol_u,
            bid_price=None,
            ask_price=None,
            mid_price=float(price),
            quote_ts=quote_ts,
            snapshot_ts=utc_now_iso(),
            provider=self.provider_name,
            provider_feed=self.provider_feed,
            source_quality=self.source_quality,
            quote_quality="non_canonical_convenience",
            license_scope=self.license_scope,
        )
        return snapshot.to_dict()

    def download_daily_bars(
        self,
        symbols: list[str] | tuple[str, ...] | str,
        *,
        start: str | None = None,
        end: str | None = None,
        period: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        raw = yf.download(
            symbols,
            start=start,
            end=end,
            period=period,
            progress=False,
            auto_adjust=False,
            **kwargs,
        )
        if isinstance(raw, pd.DataFrame):
            raw.attrs["source_quality"] = self.source_quality
            raw.attrs["provider"] = self.provider_name
            raw.attrs["provider_feed"] = self.provider_feed
            raw.attrs["license_scope"] = self.license_scope
        return raw

