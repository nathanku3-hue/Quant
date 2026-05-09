from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest
import requests

import execution.broker_api as broker_mod
from execution.confirmation import confirm_execution_intent
from execution.rebalancer import PortfolioRebalancer
from execution.risk_interceptor import RiskInterceptor
from execution.signed_envelope import SIGNED_EXECUTION_ENVELOPE_FIELD
from scripts.execution_bridge import MAX_ORDERS_PER_BATCH
from scripts.execution_bridge import generate_execution_payload
from scripts.execution_bridge import notify_pm


def _scan_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def _security_control_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-test-v1")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-02-28T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_KEY_LEGAL_HOLD", "YES")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_EXECUTION_ENVELOPE_SECRET", "test-envelope-secret")


def test_confirm_execution_non_tty_requires_explicit_override():
    assert confirm_execution_intent(is_tty=False, env={}) is False
    assert confirm_execution_intent(is_tty=False, env={"TZ_EXECUTION_CONFIRM": "YES"}) is True
    assert confirm_execution_intent(is_tty=False, env={"TZ_EXECUTION_CONFIRM": "true"}) is True


def test_confirm_execution_tty_uses_operator_prompt():
    assert confirm_execution_intent(is_tty=True, prompt_func=lambda _: "Y") is True
    assert confirm_execution_intent(is_tty=True, prompt_func=lambda _: "n") is False


def test_alpaca_broker_defaults_to_paper_base_url(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, str] = {}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            captured["base_url"] = str(base_url)

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker_mod.AlpacaBroker()

    assert captured["base_url"] == broker_mod.PAPER_BASE_URL


def test_alpaca_broker_blocks_non_paper_without_break_glass(monkeypatch: pytest.MonkeyPatch):
    rest_called = {"value": False}

    def _fake_rest(*args, **kwargs):
        rest_called["value"] = True
        raise AssertionError("REST client should not be created for blocked non-paper URL.")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _fake_rest)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://api.alpaca.markets")
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    with pytest.raises(
        EnvironmentError,
        match=f"{broker_mod.LIVE_TRADING_BREAK_GLASS_ENV}={broker_mod.LIVE_TRADING_BREAK_GLASS_VALUE}",
    ):
        broker_mod.AlpacaBroker()

    assert rest_called["value"] is False


def test_alpaca_broker_allows_non_paper_with_break_glass(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, str] = {}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            captured["base_url"] = str(base_url)

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://api.alpaca.markets/")
    monkeypatch.setenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, broker_mod.LIVE_TRADING_BREAK_GLASS_VALUE)
    monkeypatch.setenv("TZ_SIGNED_LIVE_TRADING_DECISION", "YES")

    broker_mod.AlpacaBroker()

    assert captured["base_url"] == "https://api.alpaca.markets"


def test_alpaca_broker_blocks_non_allowlisted_egress_host(monkeypatch: pytest.MonkeyPatch):
    rest_called = {"value": False}

    def _fake_rest(*args, **kwargs):
        rest_called["value"] = True
        raise AssertionError("REST client should not be created for blocked egress host.")

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _fake_rest)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://example.com")
    monkeypatch.setenv(
        broker_mod.LIVE_TRADING_BREAK_GLASS_ENV,
        broker_mod.LIVE_TRADING_BREAK_GLASS_VALUE,
    )

    with pytest.raises(PermissionError, match="Deny-by-default egress policy blocked host"):
        broker_mod.AlpacaBroker()

    assert rest_called["value"] is False


def test_alpaca_broker_blocks_http_even_for_allowlisted_host(monkeypatch: pytest.MonkeyPatch):
    rest_called = {"value": False}

    def _fake_rest(*args, **kwargs):
        rest_called["value"] = True
        raise AssertionError("REST client should not be created for blocked non-https URL.")

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _fake_rest)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "http://api.alpaca.markets")
    monkeypatch.setenv(
        broker_mod.LIVE_TRADING_BREAK_GLASS_ENV,
        broker_mod.LIVE_TRADING_BREAK_GLASS_VALUE,
    )

    with pytest.raises(PermissionError, match="non-https URL"):
        broker_mod.AlpacaBroker()

    assert rest_called["value"] is False


def test_alpaca_submit_order_passes_client_order_id(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="order-1",
                status="accepted",
                client_order_id=kwargs.get("client_order_id"),
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="aapl", qty=2, side="buy", client_order_id="cid-123")

    assert captured["client_order_id"] == "cid-123"
    assert captured["type"] == "market"
    assert result["ok"] is True
    assert result["client_order_id"] == "cid-123"


def test_alpaca_submit_order_passes_limit_order_intent(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                id="order-limit-1",
                status="accepted",
                client_order_id=kwargs.get("client_order_id"),
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(
        symbol="MSFT",
        qty=1,
        side="buy",
        order_type="limit",
        limit_price=412.25,
        client_order_id="cid-limit-1",
    )

    assert captured["type"] == "limit"
    assert captured["limit_price"] == 412.25
    assert captured["client_order_id"] == "cid-limit-1"
    assert result["ok"] is True
    assert result["order_type"] == "limit"
    assert result["limit_price"] == 412.25


def test_alpaca_submit_order_rejects_limit_without_limit_price(monkeypatch: pytest.MonkeyPatch):
    submit_calls = {"count": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            submit_calls["count"] += 1
            return SimpleNamespace(id="ignored", status="accepted", client_order_id="ignored")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(
        symbol="MSFT",
        qty=1,
        side="buy",
        order_type="limit",
        client_order_id="cid-limit-missing",
    )

    assert submit_calls["count"] == 0
    assert result["ok"] is False
    assert "invalid_limit_price" in result["error"]


def test_alpaca_submit_order_rejects_bool_qty(monkeypatch: pytest.MonkeyPatch):
    submit_calls = {"count": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            submit_calls["count"] += 1
            return SimpleNamespace(id="ignored", status="accepted", client_order_id="ignored")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=True, side="buy", client_order_id="cid-bool-qty")

    assert submit_calls["count"] == 0
    assert result["ok"] is False
    assert "invalid_qty" in result["error"]


def test_alpaca_submit_order_requires_client_order_id(monkeypatch: pytest.MonkeyPatch):
    submit_calls = {"count": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            submit_calls["count"] += 1
            return SimpleNamespace(id="order-ignored", status="accepted", client_order_id="unused")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="AAPL", qty=1, side="buy", client_order_id="")

    assert submit_calls["count"] == 0
    assert result["ok"] is False
    assert result["error"] == "missing_client_order_id"


def test_alpaca_submit_order_recovers_via_client_order_lookup(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            return SimpleNamespace(
                id="recovered-1",
                status="accepted",
                client_order_id=client_order_id,
                symbol="MSFT",
                side="buy",
                qty=1,
                created_at="2026-03-01T15:30:00.100Z",
                submitted_at="2026-03-01T15:30:00.200Z",
                updated_at="2026-03-01T15:30:00.400Z",
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", client_order_id="cid-recover")

    assert calls["lookup"] == 1
    assert result["ok"] is True
    assert result["recovered"] is True
    assert result["order_id"] == "recovered-1"
    assert result["client_order_id"] == "cid-recover"
    assert result["submit_sent_ts"] == "2026-03-01T15:30:00.200Z"
    assert result["broker_ack_ts"] == "2026-03-01T15:30:00.400Z"


def test_alpaca_submit_order_recovery_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            return SimpleNamespace(
                id="recovered-mismatch",
                status="accepted",
                client_order_id=client_order_id,
                symbol="AAPL",
                side="buy",
                qty=1,
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", client_order_id="cid-recover")

    assert calls["lookup"] == 1
    assert result["ok"] is False
    assert result["error"] == "recovery_mismatch"
    assert result["client_order_id"] == "cid-recover"
    assert result["recovered_order_id"] == "recovered-mismatch"


def test_alpaca_submit_order_recovery_market_with_non_null_limit_fails_closed(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            return SimpleNamespace(
                id="recovered-market-limit",
                status="accepted",
                client_order_id=client_order_id,
                symbol="MSFT",
                side="buy",
                qty=1,
                type="market",
                limit_price=0,
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", order_type="market", client_order_id="cid-recover")

    assert calls["lookup"] == 1
    assert result["ok"] is False
    assert result["error"] == "recovery_mismatch"


def test_alpaca_submit_order_recovery_missing_client_order_id_fails_closed(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            return SimpleNamespace(
                id="recovered-missing-cid",
                status="accepted",
                client_order_id="",
                symbol="MSFT",
                side="buy",
                qty=1,
                type="market",
                limit_price=None,
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", order_type="market", client_order_id="cid-recover")

    assert calls["lookup"] == 1
    assert result["ok"] is False
    assert result["error"] == "recovery_mismatch"


def test_alpaca_submit_order_recovery_market_with_text_null_limit_recovers(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            return SimpleNamespace(
                id="recovered-text-null",
                status="accepted",
                client_order_id=client_order_id,
                symbol="MSFT",
                side="buy",
                qty=1,
                type="market",
                limit_price="null",
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", order_type="market", client_order_id="cid-recover")

    assert calls["lookup"] == 1
    assert result["ok"] is True
    assert result["recovered"] is True
    assert result["client_order_id"] == "cid-recover"


def test_alpaca_submit_order_fails_when_recovery_lookup_misses(monkeypatch: pytest.MonkeyPatch):
    calls = {"lookup": 0}

    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            pass

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            calls["lookup"] += 1
            raise RuntimeError("order not found")
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="MSFT", qty=1, side="buy", client_order_id="cid-miss")

    assert calls["lookup"] == 1
    assert result["ok"] is False
    assert "transient submit timeout" in result["error"]
    assert result["client_order_id"] == "cid-miss"


def test_generate_execution_payload_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing required scan columns"):
        generate_execution_payload(pd.DataFrame({"Ticker": ["AAPL"]}))


def test_generate_execution_payload_rejects_non_dataframe_input():
    with pytest.raises(TypeError, match="df_results must be a pandas DataFrame"):
        generate_execution_payload({"Ticker": ["AAPL"]})  # type: ignore[arg-type]


def test_generate_execution_payload_dedupes_ticker_and_builds_deterministic_batch():
    frame = _scan_frame(
        [
            {"Ticker": "aapl", "Score": 96, "Regime": "GREEN", "HF_Scalar": 1},
            {"Ticker": "AAPL", "Score": 92, "Regime": "GREEN", "HF_Scalar": 9},
            {"Ticker": "MSFT", "Score": 91, "Regime": "GREEN", "HF_Scalar": 2},
            {"Ticker": "DEAD", "Score": 99, "Regime": "[DEATH] COLLAPSE"},
        ]
    )

    p1 = generate_execution_payload(frame, portfolio_value=50000.0)
    p2 = generate_execution_payload(frame, portfolio_value=50000.0)

    orders = p1["execution_orders"]
    assert [o["ticker"] for o in orders] == ["AAPL", "MSFT"]
    assert len(orders) == 2
    assert all(isinstance(o.get("target_weight"), float) and o["target_weight"] > 0 for o in orders)
    assert all(str(o.get("trade_day", "")).isdigit() and len(str(o["trade_day"])) == 8 for o in orders)
    assert all(str(o.get("client_order_id", "")).startswith(f"{o['trade_day']}-{o['ticker']}-BUY") for o in orders)
    assert p1["batch_id"] == p2["batch_id"]
    assert p1["risk_checks"]["order_count"] == 2
    assert p1["risk_checks"]["total_weight_allocated"] <= 1.0
    assert p1["security_controls"]["hmac_key_version"] == "hmac-test-v1"
    assert p1["security_controls"]["hmac_legal_hold"] is True
    assert p1["security_controls"]["hmac_rotation_due"] is False
    envelope = p1[SIGNED_EXECUTION_ENVELOPE_FIELD]
    assert envelope["kid"] == "hmac-test-v1"
    assert envelope["key_version"] == "hmac-test-v1"
    assert isinstance(envelope["exp"], int) and envelope["exp"] > 0
    assert isinstance(envelope["payload_hash"], str) and len(envelope["payload_hash"]) == 64
    assert isinstance(envelope["signature"], str) and len(envelope["signature"]) == 64
    assert envelope["intent_id"] == p1["batch_id"]
    assert isinstance(envelope["nonce"], str) and envelope["nonce"] != ""


def test_generate_execution_payload_filters_blank_ticker_and_non_numeric_score_rows():
    frame = _scan_frame(
        [
            {"Ticker": "  ", "Score": 95, "Regime": "GREEN"},
            {"Ticker": "AAPL", "Score": "not-a-number", "Regime": "GREEN"},
            {"Ticker": "MSFT", "Score": 92, "Regime": "GREEN"},
        ]
    )

    payload = generate_execution_payload(frame)
    orders = payload["execution_orders"]
    assert len(orders) == 1
    assert orders[0]["ticker"] == "MSFT"


def test_generate_execution_payload_fails_closed_for_oversize_batch():
    rows = [
        {"Ticker": f"T{i:03d}", "Score": 95, "Regime": "GREEN"}
        for i in range(MAX_ORDERS_PER_BATCH + 1)
    ]
    frame = _scan_frame(rows)
    with pytest.raises(ValueError, match="exceeds max batch size"):
        generate_execution_payload(frame)


def test_generate_execution_payload_blocks_overdue_hmac_key_without_legal_hold(
    monkeypatch: pytest.MonkeyPatch,
):
    frame = _scan_frame([{"Ticker": "AAPL", "Score": 95, "Regime": "GREEN"}])
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-expired-v1")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-01-01T00:00:00Z")
    monkeypatch.delenv("TZ_HMAC_KEY_LEGAL_HOLD", raising=False)
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")

    with pytest.raises(EnvironmentError, match="HMAC signing key rotation overdue"):
        generate_execution_payload(frame)


def test_notify_pm_blocks_non_allowlisted_webhook(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "execution_orders": [{"ticker": "AAPL"}],
        "risk_checks": {"total_weight_allocated": 0.2},
    }
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/token")
    with pytest.raises(PermissionError, match="Deny-by-default egress policy blocked host"):
        notify_pm(payload)


def test_notify_pm_payload_only_mode_fails_closed_on_transport_error(
    monkeypatch: pytest.MonkeyPatch,
):
    payload = {
        "execution_orders": [{"ticker": "AAPL"}],
        "risk_checks": {"total_weight_allocated": 0.2},
    }
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/token")
    monkeypatch.setenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES", "discord.com")

    def _raise_timeout(*_args, **_kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr("scripts.execution_bridge.requests.post", _raise_timeout)
    with pytest.raises(RuntimeError, match="Discord webhook delivery failed"):
        notify_pm(payload)


def test_notify_pm_post_submit_mode_degrades_on_transport_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = {
        "execution_orders": [{"ticker": "AAPL"}],
        "risk_checks": {"total_weight_allocated": 0.2},
        "_post_submit": True,
    }
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/token")
    monkeypatch.setenv("TZ_ALLOWED_EGRESS_HOST_SUFFIXES", "discord.com")

    def _raise_timeout(*_args, **_kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr("scripts.execution_bridge.requests.post", _raise_timeout)
    notify_pm(payload)
    out = capsys.readouterr().out
    assert "[WATCHTOWER-DEGRADED]" in out


class _BrokerStub:
    def __init__(self) -> None:
        self.submitted: list[dict] = []

    def get_portfolio_state(self) -> dict:
        return {"equity": 1000.0, "positions": {"MSFT": 1}}

    def get_latest_price(self, symbol: str) -> float:
        prices = {"AAPL": 333.0, "MSFT": 100.0}
        return float(prices[symbol])

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        client_order_id: str | None = None,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> dict:
        self.submitted.append(
            {
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "client_order_id": client_order_id,
                "order_type": order_type,
                "limit_price": limit_price,
            }
        )
        return {
            "ok": True,
            "order_id": f"{symbol}-1",
            "status": "accepted",
            "client_order_id": client_order_id,
            "order_type": order_type,
            "limit_price": limit_price,
        }


def test_rebalancer_rejects_negative_target_weights():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker)
    with pytest.raises(ValueError, match="negative"):
        rebalancer.calculate_orders({"AAPL": -0.1})


def test_rebalancer_rounds_quantity_to_reduce_drift():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker, dust_filter_dollars=0.0)
    orders = rebalancer.calculate_orders({"AAPL": 0.55})
    assert len(orders) == 2  # Buy AAPL and sell existing MSFT.
    buy = [o for o in orders if o["symbol"] == "AAPL"][0]
    assert buy["qty"] == 2


def test_rebalancer_calculate_orders_trims_whitespace_padded_position_symbols():
    class _WhitespacePositionBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {" AAPL ": 1}}

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 100.0
            raise KeyError(symbol)

    broker = _WhitespacePositionBroker()
    rebalancer = PortfolioRebalancer(broker=broker, dust_filter_dollars=0.0)
    orders = rebalancer.calculate_orders({})

    assert len(orders) == 1
    assert orders[0]["symbol"] == "AAPL"
    assert orders[0]["side"] == "sell"
    assert orders[0]["qty"] == 1


def test_rebalancer_calculate_orders_rejects_non_finite_position_quantity():
    class _NonFinitePositionBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"AAPL": float("nan")}}

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 100.0
            raise KeyError(symbol)

    broker = _NonFinitePositionBroker()
    rebalancer = PortfolioRebalancer(broker=broker, dust_filter_dollars=0.0)

    with pytest.raises(ValueError, match="invalid current position quantity"):
        rebalancer.calculate_orders({})


def test_rebalancer_calculate_orders_prioritizes_sells_before_buys():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker, dust_filter_dollars=0.0)
    orders = rebalancer.calculate_orders({"AAPL": 0.55})
    assert len(orders) == 2
    assert orders[0]["side"] == "sell"
    assert orders[1]["side"] == "buy"


def test_rebalancer_execute_rejects_duplicate_symbols():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker)
    with pytest.raises(ValueError, match="Duplicate order symbol"):
        rebalancer.execute_orders(
            [
                {"symbol": "AAPL", "qty": 1, "side": "buy"},
                {"symbol": "AAPL", "qty": 2, "side": "sell"},
            ]
        )
    assert broker.submitted == []


def test_rebalancer_execute_rejects_duplicate_symbols_with_whitespace_variants():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker)
    with pytest.raises(ValueError, match="Duplicate order symbol"):
        rebalancer.execute_orders(
            [
                {"symbol": "AAPL", "qty": 1, "side": "buy"},
                {"symbol": " AAPL ", "qty": 1, "side": "sell"},
            ]
        )
    assert broker.submitted == []


def test_rebalancer_execute_rejects_duplicate_client_order_id():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker)
    with pytest.raises(ValueError, match="Duplicate client_order_id"):
        rebalancer.execute_orders(
            [
                {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-dup-1"},
                {"symbol": "MSFT", "qty": 1, "side": "sell", "client_order_id": "cid-dup-1"},
            ]
        )
    assert broker.submitted == []


def test_rebalancer_execute_passes_explicit_client_order_id():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(max_single_asset_weight=1.0, max_sector_weight=1.0, max_var_proxy=1.0),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "manual-cid-1"}]
    )

    assert broker.submitted[0]["client_order_id"] == "manual-cid-1"
    assert results[0]["result"]["client_order_id"] == "manual-cid-1"


def test_rebalancer_execute_passes_order_type_and_limit_price():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(max_single_asset_weight=1.0, max_sector_weight=1.0, max_var_proxy=1.0),
    )
    results = rebalancer.execute_orders(
        [
            {
                "symbol": "AAPL",
                "qty": 1,
                "side": "buy",
                "client_order_id": "cid-limit-pass",
                "order_type": "limit",
                "limit_price": 123.45,
            }
        ]
    )

    assert broker.submitted[0]["client_order_id"] == "cid-limit-pass"
    assert broker.submitted[0]["order_type"] == "limit"
    assert broker.submitted[0]["limit_price"] == 123.45
    assert results[0]["result"]["order_type"] == "limit"
    assert results[0]["result"]["limit_price"] == 123.45


def test_rebalancer_execute_generates_deterministic_client_order_id_when_missing():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(max_single_asset_weight=1.0, max_sector_weight=1.0, max_var_proxy=1.0),
    )
    order = {"symbol": "AAPL", "qty": 1, "side": "buy", "trade_day": "20260228"}

    first = rebalancer.execute_orders([order])[0]["result"]["client_order_id"]
    second = rebalancer.execute_orders([order])[0]["result"]["client_order_id"]

    assert first == second
    assert broker.submitted[0]["client_order_id"] == first
    assert broker.submitted[1]["client_order_id"] == second


def test_rebalancer_execute_dry_run_includes_client_order_id_and_skips_submit():
    broker = _BrokerStub()
    rebalancer = PortfolioRebalancer(broker=broker)
    results = rebalancer.execute_orders(
        [{"symbol": "MSFT", "qty": 1, "side": "sell", "trade_day": "20260228"}],
        dry_run=True,
    )

    assert broker.submitted == []
    result = results[0]["result"]
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["client_order_id"].startswith("20260228-MSFT-SELL-1-")


def test_rebalancer_risk_interceptor_blocks_vix_buy_and_allows_sell(tmp_path):
    class _BrokerWithVix(_BrokerStub):
        def get_vix(self) -> float:
            return 50.0

    broker = _BrokerWithVix()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk")),
    )
    results = rebalancer.execute_orders(
        [
            {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-vix-buy"},
            {"symbol": "MSFT", "qty": 1, "side": "sell", "client_order_id": "cid-risk-vix-sell"},
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "vix_kill_switch"
    assert results[1]["result"]["ok"] is True
    assert len(broker.submitted) == 1
    assert broker.submitted[0]["symbol"] == "MSFT"
    assert broker.submitted[0]["side"] == "sell"
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_blocks_single_asset_weight(tmp_path):
    class _SingleAssetBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {}}

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 500.0
            raise KeyError(symbol)

    broker = _SingleAssetBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=0.30,
            max_sector_weight=1.00,
            max_var_proxy=1.00,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-single"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "max_single_asset_weight"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_blocks_sector_weight(tmp_path):
    class _SectorBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"MSFT": 4}}

        def get_latest_price(self, symbol: str) -> float:
            prices = {"AAPL": 250.0, "MSFT": 100.0}
            return float(prices[str(symbol).upper()])

        def get_sector_map(self, _symbols: list[str]) -> dict[str, str]:
            return {"AAPL": "TECH", "MSFT": "TECH"}

    broker = _SectorBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=0.80,
            max_sector_weight=0.60,
            max_var_proxy=1.00,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-sector"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "max_sector_weight"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_blocks_var_proxy(tmp_path):
    class _VarBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {}}

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 100.0
            raise KeyError(symbol)

        def get_symbol_volatility(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 0.50
            return 0.02

    broker = _VarBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=1.00,
            max_sector_weight=1.00,
            max_var_proxy=0.10,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 2, "side": "buy", "client_order_id": "cid-risk-var"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "var_proxy"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_fail_closed_when_risk_check_errors(tmp_path):
    class _BrokenRiskBroker(_BrokerStub):
        def get_latest_price(self, symbol: str) -> float:
            raise RuntimeError(f"no pricing for {symbol}")

    broker = _BrokenRiskBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk")),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-fail-closed"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "risk_check_error"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_fail_closed_on_malformed_position_quantities(tmp_path):
    class _MalformedPositionBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"MSFT": "bad-qty"}}

    broker = _MalformedPositionBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk")),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-malformed-position"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "risk_check_error"
    assert "invalid position quantity" in str(results[0]["result"]["reason"])
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_batch_halt_blocks_remaining_orders(tmp_path):
    class _BrokerWithVix(_BrokerStub):
        def get_vix(self) -> float:
            return 55.0

    broker = _BrokerWithVix()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk")),
        halt_on_risk_block=True,
    )
    results = rebalancer.execute_orders(
        [
            {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-halt-aapl"},
            {"symbol": "MSFT", "qty": 1, "side": "sell", "client_order_id": "cid-risk-halt-msft"},
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "vix_kill_switch"
    assert results[1]["result"]["ok"] is False
    assert results[1]["result"]["reason_code"] == "risk_batch_halt"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 2


def test_rebalancer_missing_risk_context_fails_closed_by_default():
    class _NoRiskContextBroker:
        def __init__(self) -> None:
            self.submitted: list[dict[str, object]] = []

        def submit_order(
            self,
            symbol: str,
            qty: int,
            side: str,
            client_order_id: str | None = None,
            order_type: str = "market",
            limit_price: float | None = None,
        ) -> dict:
            self.submitted.append(
                {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "client_order_id": client_order_id,
                    "order_type": order_type,
                    "limit_price": limit_price,
                }
            )
            return {"ok": True, "status": "accepted", "client_order_id": client_order_id}

    broker = _NoRiskContextBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    blocked = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-no-risk-context-block"}]
    )

    assert blocked[0]["result"]["ok"] is False
    assert blocked[0]["result"]["reason_code"] == "risk_check_error"
    assert broker.submitted == []


def test_rebalancer_commits_risk_projection_only_after_submit_success():
    class _IntermittentSubmitBroker(_BrokerStub):
        def __init__(self) -> None:
            super().__init__()
            self._submit_count = 0

        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {}}

        def get_latest_price(self, symbol: str) -> float:
            _ = symbol
            return 100.0

        def get_sector_map(self, _symbols: list[str]) -> dict[str, str]:
            return {"AAPL": "TECH", "MSFT": "TECH"}

        def submit_order(
            self,
            symbol: str,
            qty: int,
            side: str,
            client_order_id: str | None = None,
            order_type: str = "market",
            limit_price: float | None = None,
        ) -> dict:
            self._submit_count += 1
            self.submitted.append(
                {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "client_order_id": client_order_id,
                    "order_type": order_type,
                    "limit_price": limit_price,
                }
            )
            if self._submit_count == 1:
                return {"ok": False, "error": "exchange_reject", "client_order_id": client_order_id}
            return {
                "ok": True,
                "order_id": f"{symbol}-accepted",
                "status": "accepted",
                "client_order_id": client_order_id,
                "order_type": order_type,
                "limit_price": limit_price,
            }

    broker = _IntermittentSubmitBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=1.00,
            max_sector_weight=0.15,
            max_var_proxy=1.00,
        ),
    )
    results = rebalancer.execute_orders(
        [
            {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-submit-fail-first"},
            {"symbol": "MSFT", "qty": 1, "side": "buy", "client_order_id": "cid-submit-second"},
        ]
    )

    assert len(broker.submitted) == 2
    assert results[0]["result"]["ok"] is False
    assert results[1]["result"]["ok"] is True


def test_rebalancer_does_not_credit_pending_sells_for_follow_on_risk_checks(tmp_path):
    class _PendingSellBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"MSFT": 4}}

        def get_latest_price(self, symbol: str) -> float:
            prices = {"AAPL": 250.0, "MSFT": 100.0}
            return float(prices[str(symbol).upper()])

        def get_sector_map(self, _symbols: list[str]) -> dict[str, str]:
            return {"AAPL": "TECH", "MSFT": "TECH"}

        def submit_order(
            self,
            symbol: str,
            qty: int,
            side: str,
            client_order_id: str | None = None,
            order_type: str = "market",
            limit_price: float | None = None,
        ) -> dict:
            self.submitted.append(
                {
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "client_order_id": client_order_id,
                    "order_type": order_type,
                    "limit_price": limit_price,
                }
            )
            return {
                "ok": True,
                "order_id": f"{symbol}-accepted",
                "status": "accepted",
                "client_order_id": client_order_id,
                "order_type": order_type,
                "limit_price": limit_price,
            }

    broker = _PendingSellBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=0.80,
            max_sector_weight=0.60,
            max_var_proxy=1.00,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [
            {"symbol": "MSFT", "qty": 4, "side": "sell", "client_order_id": "cid-pending-sell"},
            {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-follow-on-buy"},
        ]
    )

    assert results[0]["result"]["ok"] is True
    assert results[1]["result"]["ok"] is False
    assert results[1]["result"]["reason_code"] == "max_sector_weight"
    assert len(broker.submitted) == 1


def test_rebalancer_risk_interceptor_uses_broker_sector_over_order_sector(tmp_path):
    class _SectorSpoofBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"MSFT": 4}}

        def get_latest_price(self, symbol: str) -> float:
            prices = {"AAPL": 250.0, "MSFT": 100.0}
            return float(prices[str(symbol).upper()])

        def get_sector_map(self, _symbols: list[str]) -> dict[str, str]:
            return {"AAPL": "TECH", "MSFT": "TECH"}

    broker = _SectorSpoofBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=0.80,
            max_sector_weight=0.60,
            max_var_proxy=1.00,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [
            {
                "symbol": "AAPL",
                "qty": 1,
                "side": "buy",
                "sector": "HEALTHCARE",
                "client_order_id": "cid-risk-sector-spoof",
            }
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "max_sector_weight"
    assert broker.submitted == []


def test_rebalancer_risk_interceptor_does_not_downgrade_known_sector_to_unknown(tmp_path):
    class _SectorDowngradeBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"MSFT": 4}}

        def get_latest_price(self, symbol: str) -> float:
            prices = {"AAPL": 250.0, "MSFT": 100.0}
            return float(prices[str(symbol).upper()])

        def get_sector_map(self, _symbols: list[str]) -> dict[str, str]:
            return {"AAPL": "TECH", "MSFT": "TECH"}

        def get_sector_for_symbol(self, symbol: str) -> str:
            return "UNKNOWN" if str(symbol).upper() == "AAPL" else "TECH"

    broker = _SectorDowngradeBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=0.80,
            max_sector_weight=0.60,
            max_var_proxy=1.00,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-risk-sector-downgrade"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "max_sector_weight"
    assert broker.submitted == []


def test_rebalancer_risk_interceptor_uses_broker_vix_over_order_vix(tmp_path):
    class _VixSpoofBroker(_BrokerStub):
        def get_vix(self) -> float:
            return 50.0

    broker = _VixSpoofBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk")),
    )
    results = rebalancer.execute_orders(
        [
            {
                "symbol": "AAPL",
                "qty": 1,
                "side": "buy",
                "vix": 10.0,
                "client_order_id": "cid-risk-vix-spoof",
            }
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "vix_kill_switch"
    assert broker.submitted == []


def test_rebalancer_risk_interceptor_uses_broker_volatility_over_order_volatility(tmp_path):
    class _VolSpoofBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {}}

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 100.0
            raise KeyError(symbol)

        def get_symbol_volatility(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 0.50
            return 0.02

    broker = _VolSpoofBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=1.00,
            max_sector_weight=1.00,
            max_var_proxy=0.10,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [
            {
                "symbol": "AAPL",
                "qty": 2,
                "side": "buy",
                "volatility": 0.01,
                "client_order_id": "cid-risk-vol-spoof",
            }
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "var_proxy"
    assert broker.submitted == []


def test_rebalancer_risk_interceptor_uses_case_insensitive_portfolio_volatility_map(tmp_path):
    class _LowercaseVolMapBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {
                "equity": 1000.0,
                "positions": {},
                "symbol_volatility": {"aapl": 0.50},
            }

        def get_latest_price(self, symbol: str) -> float:
            if str(symbol).upper() == "AAPL":
                return 100.0
            raise KeyError(symbol)

    broker = _LowercaseVolMapBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=1.00,
            max_sector_weight=1.00,
            max_var_proxy=0.10,
            audit_dir=str(tmp_path / "risk"),
        ),
    )
    results = rebalancer.execute_orders(
        [
            {
                "symbol": "AAPL",
                "qty": 2,
                "side": "buy",
                "volatility": 0.01,
                "client_order_id": "cid-risk-vol-lowercase-map",
            }
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "var_proxy"
    assert broker.submitted == []


def test_rebalancer_risk_interceptor_blocks_long_only_negative_projection(tmp_path):
    class _LongOnlyBroker(_BrokerStub):
        def get_portfolio_state(self) -> dict:
            return {"equity": 1000.0, "positions": {"AAPL": 1}}

        def get_latest_price(self, symbol: str) -> float:
            _ = symbol
            return 100.0

    broker = _LongOnlyBroker()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=RiskInterceptor(audit_dir=str(tmp_path / "risk"), long_only=True),
    )
    results = rebalancer.execute_orders(
        [{"symbol": "AAPL", "qty": 2, "side": "sell", "client_order_id": "cid-risk-long-only"}]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "invalid_order_projection"
    assert broker.submitted == []
    assert len(list((tmp_path / "risk").glob("risk_block_*.json"))) == 1


def test_rebalancer_risk_interceptor_audit_persist_failure_halts_batch(tmp_path):
    class _AuditFailRiskInterceptor(RiskInterceptor):
        def persist_block_decision(self, *, decision, order, portfolio_state) -> str:  # type: ignore[override]
            _ = decision, order, portfolio_state
            raise RuntimeError("audit disk unavailable")

    class _BrokerWithVix(_BrokerStub):
        def get_vix(self) -> float:
            return 55.0

    broker = _BrokerWithVix()
    rebalancer = PortfolioRebalancer(
        broker=broker,
        risk_interceptor=_AuditFailRiskInterceptor(audit_dir=str(tmp_path / "risk")),
    )
    results = rebalancer.execute_orders(
        [
            {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-audit-fail-aapl"},
            {"symbol": "MSFT", "qty": 1, "side": "sell", "client_order_id": "cid-audit-fail-msft"},
        ]
    )

    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["reason_code"] == "risk_blocked_audit_failed"
    assert "audit disk unavailable" in str(results[0]["result"]["risk_audit_error"])
    assert results[1]["result"]["ok"] is False
    assert results[1]["result"]["reason_code"] == "risk_blocked_audit_failed"
    assert "batch halted after prior risk block" in str(results[1]["result"]["reason"])
    assert "audit persistence failed" in str(results[1]["result"]["reason"])
    assert broker.submitted == []


def test_alpaca_get_latest_quote_snapshot_returns_midpoint(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def get_latest_quote(self, symbol):
            assert str(symbol).upper() == "AAPL"
            return SimpleNamespace(
                bidprice="100.00",
                askprice="100.20",
                timestamp="2026-03-01T15:30:00Z",
            )
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    quote = broker.get_latest_quote_snapshot("AAPL")

    assert quote["bid_price"] == 100.0
    assert quote["ask_price"] == 100.2
    assert quote["mid_price"] == 100.1
    assert str(quote["quote_ts"]).startswith("2026-03-01T15:30:00")


def test_alpaca_get_latest_quote_snapshot_accepts_v2_snake_case_fields(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def get_latest_quote(self, symbol):
            assert str(symbol).upper() == "AAPL"
            return SimpleNamespace(
                bid_price=200.10,
                ask_price=200.30,
                t="2026-03-01T16:00:00Z",
            )

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    quote = broker.get_latest_quote_snapshot("AAPL")

    assert quote["bid_price"] == pytest.approx(200.10, abs=1e-12)
    assert quote["ask_price"] == pytest.approx(200.30, abs=1e-12)
    assert quote["mid_price"] == pytest.approx(200.20, abs=1e-12)
    assert str(quote["quote_ts"]).startswith("2026-03-01T16:00:00")


def test_alpaca_submit_order_aggregates_partial_fills_into_vwap(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            return SimpleNamespace(
                id="ord-fill-1",
                status="filled",
                client_order_id=kwargs.get("client_order_id"),
                symbol=kwargs.get("symbol"),
                side=kwargs.get("side"),
                qty=kwargs.get("qty"),
                type=kwargs.get("type"),
                time_in_force=kwargs.get("time_in_force"),
                created_at="2026-03-01T15:30:00.150Z",
                submitted_at="2026-03-01T15:30:00.200Z",
                updated_at="2026-03-01T15:30:01.000Z",
                filled_at="2026-03-01T15:30:01.000Z",
                filled_qty="3",
                filled_avg_price="100.6666666667",
            )

        def get_activities(self, **kwargs):
            _ = kwargs
            return [
                SimpleNamespace(
                    order_id="ord-fill-1",
                    symbol="AAPL",
                    side="buy",
                    qty="1",
                    price="100.0",
                    transaction_time="2026-03-01T15:30:00.700Z",
                    exchange="XNAS",
                ),
                SimpleNamespace(
                    order_id="ord-fill-1",
                    symbol="AAPL",
                    side="buy",
                    qty="2",
                    price="101.0",
                    transaction_time="2026-03-01T15:30:01.000Z",
                    exchange="XNAS",
                ),
                SimpleNamespace(
                    order_id="ord-other",
                    symbol="MSFT",
                    side="buy",
                    qty="5",
                    price="200.0",
                    transaction_time="2026-03-01T15:31:00.000Z",
                    exchange="XNAS",
                ),
            ]
    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="AAPL", qty=3, side="buy", client_order_id="cid-fill-1")

    assert result["ok"] is True
    assert len(result["partial_fills"]) == 2
    assert result["fill_summary"]["fill_count"] == 2
    assert result["fill_summary"]["fill_qty"] == pytest.approx(3.0, abs=1e-12)
    assert result["fill_summary"]["fill_vwap"] == pytest.approx((100.0 + 2.0 * 101.0) / 3.0, abs=1e-12)
    assert result["execution_ts"] == "2026-03-01T15:30:00.700Z"
    assert isinstance(result["submit_sent_ts"], str) and result["submit_sent_ts"]
    assert isinstance(result["broker_ack_ts"], str) and result["broker_ack_ts"]


def test_alpaca_submit_order_uses_snapshot_fill_fallback_when_activity_feed_is_empty(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            return SimpleNamespace(
                id="ord-fill-fallback-1",
                status="filled",
                client_order_id=kwargs.get("client_order_id"),
                symbol=kwargs.get("symbol"),
                side=kwargs.get("side"),
                qty=kwargs.get("qty"),
                type=kwargs.get("type"),
                time_in_force=kwargs.get("time_in_force"),
                created_at="2026-03-01T15:35:00.150Z",
                submitted_at="2026-03-01T15:35:00.200Z",
                updated_at="2026-03-01T15:35:00.800Z",
                filled_at="2026-03-01T15:35:00.800Z",
                filled_qty="2",
                filled_avg_price="101.5",
            )

        def get_activities(self, **kwargs):
            _ = kwargs
            return []

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="AAPL", qty=2, side="buy", client_order_id="cid-fill-fallback-1")

    assert result["ok"] is True
    assert len(result["partial_fills"]) == 1
    fill = result["partial_fills"][0]
    assert fill["fill_qty"] == pytest.approx(2.0, abs=1e-12)
    assert fill["fill_price"] == pytest.approx(101.5, abs=1e-12)
    assert fill["source"] == "order_snapshot"
    assert result["fill_summary"]["fill_count"] == 1
    assert result["fill_summary"]["fill_qty"] == pytest.approx(2.0, abs=1e-12)
    assert result["fill_summary"]["fill_vwap"] == pytest.approx(101.5, abs=1e-12)
    assert result["execution_ts"] == "2026-03-01T15:35:00.800Z"


def test_alpaca_submit_order_zero_fill_fallback_when_activity_feed_is_empty(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            return SimpleNamespace(
                id="ord-cancel-1",
                status="canceled",
                client_order_id=kwargs.get("client_order_id"),
                symbol=kwargs.get("symbol"),
                side=kwargs.get("side"),
                qty=kwargs.get("qty"),
                type=kwargs.get("type"),
                time_in_force=kwargs.get("time_in_force"),
                created_at="2026-03-01T15:30:00.150Z",
                submitted_at="2026-03-01T15:30:00.200Z",
                updated_at="2026-03-01T15:30:00.800Z",
                filled_at=None,
                filled_qty="0",
                filled_avg_price=None,
            )

        def get_activities(self, **kwargs):
            _ = kwargs
            return []

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="AAPL", qty=3, side="buy", client_order_id="cid-cancel-no-fill-1")

    assert result["ok"] is False
    assert result["error"] == "terminal_unfilled:canceled"
    assert result["status"] == "canceled"
    assert result["partial_fills"] == []
    assert result["fill_summary"]["fill_count"] == 0
    assert result["fill_summary"]["fill_qty"] == pytest.approx(0.0, abs=1e-12)
    assert result["fill_summary"]["fill_vwap"] is None


def test_alpaca_submit_order_recovery_terminal_unfilled_fails_closed(monkeypatch: pytest.MonkeyPatch):
    class _FakeREST:
        def __init__(self, api_key, api_secret, base_url, api_version):
            _ = api_key, api_secret, base_url, api_version

        def get_account(self):
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs):
            _ = kwargs
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id):
            return SimpleNamespace(
                id="ord-cancel-recover-1",
                status="canceled",
                client_order_id=client_order_id,
                symbol="AAPL",
                side="buy",
                qty=1,
                type="market",
                created_at="2026-03-01T15:40:00.100Z",
                submitted_at="2026-03-01T15:40:00.200Z",
                updated_at="2026-03-01T15:40:00.500Z",
                filled_qty="0",
                filled_avg_price=None,
            )

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(symbol="AAPL", qty=1, side="buy", client_order_id="cid-recover-canceled")

    assert result["ok"] is False
    assert result["status"] == "canceled"
    assert result["error"] == "terminal_unfilled:canceled"
    assert result["submit_sent_ts"] == "2026-03-01T15:40:00.200Z"
    assert result["broker_ack_ts"] == "2026-03-01T15:40:00.500Z"



