from __future__ import annotations

import re

import scripts.test_rebalance as mod


class _FakeBroker:
    def get_portfolio_state(self):
        return {"cash": 1000.0, "equity": 1000.0, "positions": {}}


class _FakeRebalancer:
    def __init__(self, _broker):
        self._orders = [
            {
                "symbol": "SPY",
                "qty": 1,
                "side": "buy",
                "price": 100.0,
                "delta_value": 100.0,
                "target_weight": 0.1,
                "current_qty": 0.0,
            }
        ]

    def calculate_orders(self, _targets):
        return list(self._orders)


def test_test_rebalance_main_returns_nonzero_on_failed_execution(monkeypatch):
    monkeypatch.setattr(mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(
        mod,
        "execute_orders_with_idempotent_retry",
        lambda _rebalancer, _orders: [{"result": {"ok": False, "error": "blocked"}}],
    )

    rc = mod.main()

    assert rc == 1


def test_test_rebalance_main_treats_non_boolean_ok_as_failure(monkeypatch):
    monkeypatch.setattr(mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(
        mod,
        "execute_orders_with_idempotent_retry",
        lambda _rebalancer, _orders: [{"result": {"ok": "false", "error": "adapter-drift"}}],
    )

    rc = mod.main()

    assert rc == 1


def test_test_rebalance_main_seeds_trade_day_before_helper_call(monkeypatch):
    captured: dict[str, object] = {}

    monkeypatch.setattr(mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(mod, "PortfolioRebalancer", _FakeRebalancer)

    def _fake_execute(_rebalancer, orders):
        captured["orders"] = list(orders)
        return [{"result": {"ok": True}}]

    monkeypatch.setattr(mod, "execute_orders_with_idempotent_retry", _fake_execute)

    rc = mod.main()

    assert rc == 0
    seeded_orders = captured["orders"]
    assert isinstance(seeded_orders, list)
    assert len(seeded_orders) == 1
    seed = seeded_orders[0].get("trade_day")
    assert isinstance(seed, str)
    assert re.fullmatch(r"\d{8}", seed) is not None


def test_test_rebalance_main_preserves_preseeded_trade_day(monkeypatch):
    captured: dict[str, object] = {}

    class _PreSeededRebalancer(_FakeRebalancer):
        def __init__(self, _broker):
            super().__init__(_broker)
            self._orders[0]["trade_day"] = "20240229"

    monkeypatch.setattr(mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(mod, "PortfolioRebalancer", _PreSeededRebalancer)

    def _fake_execute(_rebalancer, orders):
        captured["orders"] = list(orders)
        return [{"result": {"ok": True}}]

    monkeypatch.setattr(mod, "execute_orders_with_idempotent_retry", _fake_execute)

    rc = mod.main()

    assert rc == 0
    seeded_orders = captured["orders"]
    assert isinstance(seeded_orders, list)
    assert len(seeded_orders) == 1
    assert seeded_orders[0].get("trade_day") == "20240229"
