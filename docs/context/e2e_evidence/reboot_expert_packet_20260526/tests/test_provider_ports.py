from __future__ import annotations

from types import SimpleNamespace

import pytest

from data.providers.legacy_allowlist import YFINANCE_DIRECT_USE_ALLOWLIST
from data.providers.legacy_allowlist import scan_direct_yfinance_uses
from data.providers.registry import build_market_data_provider
from data.providers.yahoo_provider import YahooMarketDataProvider
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import SOURCE_QUALITY_OPERATIONAL
import execution.broker_api as broker_mod


def test_registry_selects_yahoo_provider_by_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TZ_MARKET_DATA_PROVIDER", raising=False)

    provider = build_market_data_provider()

    assert isinstance(provider, YahooMarketDataProvider)


def test_alpaca_quote_snapshot_tags_feed_and_quality(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def get_latest_quote(self, symbol):
            assert str(symbol).upper() == "AAPL"
            return SimpleNamespace(
                bid_price=100.0,
                ask_price=100.2,
                t="2026-05-09T12:00:00Z",
            )

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)

    broker = broker_mod.AlpacaBroker()
    quote = broker.get_latest_quote_snapshot("AAPL", feed="iex")

    assert quote["source_quality"] == SOURCE_QUALITY_OPERATIONAL
    assert quote["provider"] == "alpaca"
    assert quote["provider_feed"] == "iex"
    assert quote["quote_quality"] == "iex_only"


def test_live_alpaca_requires_signed_decision_even_with_break_glass(monkeypatch: pytest.MonkeyPatch):
    rest_called = {"value": False}

    def _fake_rest(*args, **kwargs):
        rest_called["value"] = True
        raise AssertionError("REST client should not be created for unsigned live endpoint.")

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _fake_rest)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://api.alpaca.markets")
    monkeypatch.setenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, broker_mod.LIVE_TRADING_BREAK_GLASS_VALUE)
    monkeypatch.delenv("TZ_SIGNED_LIVE_TRADING_DECISION", raising=False)

    with pytest.raises(EnvironmentError, match="outside the current milestone"):
        broker_mod.AlpacaBroker()

    assert rest_called["value"] is False


def test_direct_yfinance_uses_stay_within_migration_allowlist():
    direct_uses = scan_direct_yfinance_uses(__import__("pathlib").Path(__file__).resolve().parents[1])
    unexpected = sorted(set(direct_uses) - set(YFINANCE_DIRECT_USE_ALLOWLIST))
    missing = sorted(set(YFINANCE_DIRECT_USE_ALLOWLIST) - set(direct_uses))

    assert unexpected == []
    assert missing == []
