from __future__ import annotations

import builtins
from datetime import datetime
from datetime import timezone
from pathlib import Path

import pandas as pd
import pytest

import execution.broker_api as broker_mod
import execution.rebalancer as rebalancer_mod
from execution.signed_envelope import attach_signed_execution_envelope
import main_bot_orchestrator as orchestrator_mod
import main_console as mod


class _StdinStub:
    def __init__(self, is_tty: bool) -> None:
        self._is_tty = bool(is_tty)

    def isatty(self) -> bool:
        return self._is_tty


class _AutoFetcherStub:
    def __init__(
        self,
        *,
        dram: float | None = None,
        tsmc: float | None = None,
        energy: float | None = None,
        cloud: float | None = None,
    ) -> None:
        self._dram = dram
        self._tsmc = tsmc
        self._energy = energy
        self._cloud = cloud

    def fetch_dram_trend(self):
        return self._dram

    def fetch_tsmc_yoy(self):
        return self._tsmc

    def fetch_energy_trend(self):
        return self._energy

    def fetch_cloud_growth(self):
        return self._cloud


def _scan_frame(*, score: float = 95.0) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Ticker": "AAPL", "Score": score, "Regime": "GREEN", "Action": "BUY"},
            {"Ticker": "MSFT", "Score": 85.0, "Regime": "GREEN", "Action": "WATCH"},
        ]
    )


def _payload_row(
    *,
    ticker: str,
    target_weight: float,
    client_order_id: str,
    action: str = "BUY",
    order_type: str = "MARKET",
    limit_price: object = "Market",
    trade_day: str = "20260228",
) -> dict[str, object]:
    return {
        "ticker": ticker,
        "target_weight": target_weight,
        "client_order_id": client_order_id,
        "action": action,
        "order_type": order_type,
        "limit_price": limit_price,
        "trade_day": trade_day,
    }


@pytest.fixture(autouse=True)
def _execution_envelope_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-test-v1")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-02-28T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_KEY_LEGAL_HOLD", "YES")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_EXECUTION_ENVELOPE_SECRET", "console-test-envelope-secret")
    monkeypatch.setenv("TZ_EXECUTION_REPLAY_LEDGER_PATH", str(tmp_path / "execution_replay_ledger.jsonl"))


def _signed_payload(
    payload: dict[str, object],
    *,
    signed_at_utc: datetime | None = None,
    key_version: str | None = None,
) -> dict[str, object]:
    signed = dict(payload)
    attach_signed_execution_envelope(signed, now_utc=signed_at_utc, key_version=key_version)
    return signed


def test_check_kill_switch_exits_when_stop_file_exists(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mod, "__file__", str(tmp_path / "main_console.py"))
    (tmp_path / "STOP_TRADING").write_text("1", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.check_kill_switch()
    assert int(exc.value.code) == 1


def test_get_manual_input_non_tty_returns_default(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(False))

    out = mod.get_manual_input("Enter Value", default=1.25)
    assert out == 1.25
    assert "[Auto-Default]" in capsys.readouterr().out


def test_get_manual_input_tty_blank_returns_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(builtins, "input", lambda _prompt: "")

    out = mod.get_manual_input("Enter Value", default=2.5)
    assert out == 2.5


def test_get_manual_input_tty_invalid_returns_default(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(builtins, "input", lambda _prompt: "invalid-float")

    out = mod.get_manual_input("Enter Value", default=3.0)
    assert out == 3.0
    assert "Invalid input. Using default." in capsys.readouterr().out


def test_main_returns_on_empty_scan(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod, "AutoFetcher", lambda: _AutoFetcherStub())
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: pd.DataFrame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("should not call")))

    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert "[ERROR] Engine failed to return data." in out


def test_main_non_tty_without_override_skips_payload_generation(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, int] = {"generate": 0, "save": 0, "notify": 0, "confirm": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(False))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())

    def _confirm_execution_intent(**kwargs):
        calls["confirm"] += 1
        assert kwargs["is_tty"] is False
        return False

    def _generate(_df):
        calls["generate"] += 1
        return {"execution_orders": []}

    monkeypatch.setattr(mod, "confirm_execution_intent", _confirm_execution_intent)
    monkeypatch.setattr(mod, "generate_execution_payload", _generate)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: calls.__setitem__("save", calls["save"] + 1))
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert calls["confirm"] == 1
    assert calls["generate"] == 0
    assert calls["save"] == 0
    assert calls["notify"] == 0
    assert "TZ_EXECUTION_CONFIRM=YES" in out


def test_main_non_tty_handles_dict_auto_metrics_without_crash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, int] = {"generate": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(False))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(
            dram=0.1,
            tsmc={"val": 0.0, "span": "DEGRADED", "degraded": True, "reason": "egress_blocked"},
            energy={"val": 0.0, "span": "DEGRADED", "degraded": True, "reason": "egress_blocked"},
            cloud={"val": 0.0, "span": "DEGRADED", "degraded": True, "reason": "egress_blocked"},
        ),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: False)
    monkeypatch.setattr(
        mod,
        "generate_execution_payload",
        lambda _df: calls.__setitem__("generate", calls["generate"] + 1),
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["generate"] == 0
    assert "degraded/egress_blocked" in out


def test_main_confirmed_flow_generates_and_publishes_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, object] = {"generated": 0, "saved": None, "notified": None}
    payload = {"execution_orders": [{"ticker": "AAPL"}]}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.delenv(mod.LOCAL_SUBMIT_ENV, raising=False)

    def _generate(_df):
        calls["generated"] = int(calls["generated"]) + 1
        return payload

    monkeypatch.setattr(mod, "generate_execution_payload", _generate)
    monkeypatch.setattr(mod, "save_payload", lambda p: calls.__setitem__("saved", p))
    monkeypatch.setattr(mod, "notify_pm", lambda p: calls.__setitem__("notified", p))

    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 0
    assert calls["generated"] == 1
    assert calls["saved"] == payload
    assert calls["notified"] == payload
    assert "[SUCCESS] Orders Generated. Upload to Broker API." in out


def test_main_confirmed_flow_local_submit_executes_via_idempotent_helper(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, object] = {"saved": None, "notified": None, "executed": 0, "verified": 0}
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [{"ticker": "AAPL", "target_weight": 0.2, "trade_day": "20260228"}],
    })

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda p: calls.__setitem__("saved", p))
    monkeypatch.setattr(mod, "notify_pm", lambda p: calls.__setitem__("notified", p))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    def _verify_once(_payload):
        calls["verified"] = int(calls["verified"]) + 1
        return None

    monkeypatch.setattr(mod, "verify_local_submit_envelope_and_replay", _verify_once)

    def _execute(_payload):
        calls["executed"] = int(calls["executed"]) + 1
        assert _payload is payload
        return [{"result": {"ok": True}}]

    monkeypatch.setattr(mod, "_execute_payload_via_idempotent_helper", _execute)

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert calls["saved"] == payload
    assert calls["notified"] == {**payload, "_post_submit": True}
    assert calls["verified"] == 1
    assert calls["executed"] == 1
    assert "[SUCCESS] Local submit finished: 1/1 accepted." in out


def test_main_confirmed_flow_local_submit_blocks_on_failed_orders(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [{"ticker": "AAPL", "target_weight": 0.2, "trade_day": "20260228"}],
    })

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    calls: dict[str, int] = {"notify": 0}
    monkeypatch.setattr(mod, "save_payload", lambda _p: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _p: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: [{"result": {"ok": False, "error": "blocked"}}],
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[SUCCESS] Local submit finished: 0/1 accepted." in out
    assert "[ABORT] Local submit encountered failed orders; inspect execution logs." in out


def test_main_confirmed_flow_local_submit_blocks_on_risk_blocked_orders(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [{"ticker": "AAPL", "target_weight": 0.2, "trade_day": "20260228"}],
    })

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    calls: dict[str, int] = {"notify": 0}
    monkeypatch.setattr(mod, "save_payload", lambda _p: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _p: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: [
            {
                "result": {
                    "ok": False,
                    "error": "risk_blocked",
                    "reason_code": "max_sector_weight",
                }
            }
        ],
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[SUCCESS] Local submit finished: 0/1 accepted." in out
    assert "[ABORT] Local submit encountered failed orders; inspect execution logs." in out


def test_main_confirmed_flow_local_submit_treats_terminal_unfilled_as_not_accepted(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [{"ticker": "AAPL", "target_weight": 0.2, "trade_day": "20260228"}],
    })

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    calls: dict[str, int] = {"notify": 0}
    monkeypatch.setattr(mod, "save_payload", lambda _p: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _p: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: [
            {
                "result": {
                    "ok": True,
                    "status": "canceled",
                    "filled_qty": 0,
                    "error": "terminal_unfilled:canceled",
                }
            }
        ],
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[SUCCESS] Local submit finished: 0/1 accepted." in out
    assert "[ABORT] Local submit encountered failed orders; inspect execution logs." in out


def test_main_local_submit_rejects_tampered_signed_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
    })
    payload["execution_orders"][0]["target_weight"] = 0.25  # type: ignore[index]
    calls: dict[str, int] = {"executed": 0, "notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(mod, "AutoFetcher", lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3))
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: calls.__setitem__("executed", calls["executed"] + 1),
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["executed"] == 0
    assert calls["notify"] == 0
    assert "execution envelope payload hash mismatch" in out


def test_main_local_submit_rejects_expired_signed_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload(
        {
            "timestamp": "2026-02-28T15:55:00Z",
            "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
        },
        signed_at_utc=datetime(2020, 1, 1, tzinfo=timezone.utc),
        key_version="hmac-test-v1",
    )
    calls: dict[str, int] = {"executed": 0, "notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(mod, "AutoFetcher", lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3))
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: calls.__setitem__("executed", calls["executed"] + 1),
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["executed"] == 0
    assert calls["notify"] == 0
    assert "execution envelope expired" in out


def test_main_local_submit_rejects_replay_envelope(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
    })
    calls: dict[str, int] = {"executed": 0, "notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(mod, "AutoFetcher", lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3))
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )

    def _execute(_payload):
        calls["executed"] += 1
        return [{"result": {"ok": True}}]

    monkeypatch.setattr(mod, "_execute_payload_via_idempotent_helper", _execute)

    rc_first = mod.main()
    out_first = capsys.readouterr().out
    rc_second = mod.main()
    out_second = capsys.readouterr().out

    assert rc_first == 0
    assert "[SUCCESS] Local submit finished: 1/1 accepted." in out_first
    assert rc_second == 1
    assert "replay detected for intent_id" in out_second
    assert calls["executed"] == 1
    assert calls["notify"] == 1


def test_execute_payload_via_idempotent_helper_maps_targets_and_seeds_trade_day(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {"targets": None, "seeded_orders": None}

    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            self._broker = _broker

        def calculate_orders(self, targets):
            captured["targets"] = dict(targets)
            return [
                {"symbol": "AAPL", "qty": 1, "side": "buy", "price": 110.0},
                {"symbol": "MSFT", "qty": 2, "side": "buy", "price": 210.0},
            ]

    def _fake_execute(_rebalancer, orders):
        captured["seeded_orders"] = list(orders)
        rows = []
        for order in orders:
            rows.append(
                {
                    "order": dict(order),
                    "result": {"ok": True, "client_order_id": str(order["client_order_id"])},
                }
            )
        return rows

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", _fake_execute)

    payload = {
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [
            _payload_row(
                ticker="AAPL",
                target_weight=0.2,
                client_order_id="cid-aapl-1",
                order_type="MARKET",
                limit_price="Market",
            ),
            _payload_row(
                ticker="MSFT",
                target_weight=0.15,
                client_order_id="cid-msft-1",
                order_type="LIMIT",
                limit_price="Bid_Ask_Mid",
            ),
        ],
    }

    results = mod._execute_payload_via_idempotent_helper(payload)

    assert isinstance(results, list)
    assert captured["targets"] == {"AAPL": 0.2, "MSFT": 0.15}
    seeded_orders = captured["seeded_orders"]
    assert isinstance(seeded_orders, list)
    assert len(seeded_orders) == 2
    assert seeded_orders[0]["trade_day"] == "20260228"
    assert seeded_orders[0]["client_order_id"] == "cid-aapl-1"
    assert seeded_orders[0]["order_type"] == "market"
    assert seeded_orders[0]["limit_price"] is None
    assert seeded_orders[0]["arrival_price"] == 110.0
    assert seeded_orders[1]["client_order_id"] == "cid-msft-1"
    assert seeded_orders[1]["order_type"] == "limit"
    assert seeded_orders[1]["limit_price"] == 210.0
    assert seeded_orders[1]["arrival_price"] == 210.0
    assert isinstance(seeded_orders[1]["arrival_ts"], str)


def test_execute_payload_via_idempotent_helper_rejects_duplicate_payload_tickers(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [
            _payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1"),
            _payload_row(ticker="AAPL", target_weight=0.1, client_order_id="cid-aapl-2"),
        ],
    }

    with pytest.raises(ValueError, match="duplicate ticker in payload execution_orders"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_duplicate_payload_client_order_id(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            _payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-dup-1"),
            _payload_row(ticker="MSFT", target_weight=0.1, client_order_id="cid-dup-1"),
        ]
    }

    with pytest.raises(ValueError, match="duplicate client_order_id in payload execution_orders"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_non_list_execution_orders():
    with pytest.raises(ValueError, match="payload execution_orders must be a list"):
        mod._execute_payload_via_idempotent_helper({"execution_orders": "bad-shape"})


def test_execute_payload_via_idempotent_helper_rejects_malformed_row_atomically(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            _payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1"),
            {"ticker": "MSFT", "target_weight": 0.1, "action": "BUY", "order_type": "MARKET", "limit_price": "Market"},
        ]
    }

    with pytest.raises(ValueError, match="missing client_order_id"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_invalid_order_type(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            _payload_row(
                ticker="AAPL",
                target_weight=0.2,
                client_order_id="cid-aapl-1",
                order_type="STOP",
                limit_price="Market",
            )
        ]
    }

    with pytest.raises(ValueError, match="order_type must be MARKET or LIMIT"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_missing_trade_day(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            {
                "ticker": "AAPL",
                "target_weight": 0.2,
                "client_order_id": "cid-aapl-1",
                "action": "BUY",
                "order_type": "MARKET",
                "limit_price": "Market",
            }
        ]
    }

    with pytest.raises(ValueError, match="missing trade_day"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_non_calendar_trade_day(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            _payload_row(
                ticker="AAPL",
                target_weight=0.2,
                client_order_id="cid-aapl-1",
                trade_day="20260231",
            )
        ]
    }

    with pytest.raises(ValueError, match="valid calendar date"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_non_integral_calculated_qty(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            _ = targets
            return [{"symbol": "AAPL", "qty": 1.2, "side": "buy", "price": 110.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {
        "execution_orders": [
            _payload_row(
                ticker="AAPL",
                target_weight=0.2,
                client_order_id="cid-aapl-1",
            )
        ]
    }

    with pytest.raises(ValueError, match="must be a positive integer"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_when_calculated_orders_empty(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            _ = targets
            return []

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [{"result": {"ok": True}}])

    payload = {"execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")]}

    with pytest.raises(ValueError, match="payload targets produced no executable orders"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_rejects_when_helper_returns_empty(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            _ = targets
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [])

    payload = {"execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")]}

    with pytest.raises(ValueError, match="idempotent helper returned no execution results"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_execute_payload_via_idempotent_helper_prefers_row_level_trade_day(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {"seeded_orders": None}

    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            _ = targets
            return [{"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0}]

    def _fake_execute(_rebalancer, orders):
        captured["seeded_orders"] = list(orders)
        return [
            {
                "order": dict(orders[0]),
                "result": {"ok": True, "client_order_id": str(orders[0]["client_order_id"])},
            }
        ]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", _fake_execute)

    payload = {
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [
            _payload_row(
                ticker="AAPL",
                target_weight=0.2,
                client_order_id="cid-aapl-td",
                trade_day="20260303",
            )
        ],
    }

    mod._execute_payload_via_idempotent_helper(payload)
    seeded_orders = captured["seeded_orders"]
    assert isinstance(seeded_orders, list)
    assert seeded_orders[0]["trade_day"] == "20260303"


def test_execute_payload_via_idempotent_helper_rejects_symbol_drift_between_payload_and_calculated(monkeypatch: pytest.MonkeyPatch):
    class _FakeBroker:
        pass

    class _FakeRebalancer:
        def __init__(self, _broker):
            pass

        def calculate_orders(self, targets):
            _ = targets
            return [
                {"symbol": "AAPL", "qty": 1, "side": "buy", "price": 101.0},
                {"symbol": "NVDA", "qty": 1, "side": "buy", "price": 201.0},
            ]

    monkeypatch.setattr(broker_mod, "AlpacaBroker", _FakeBroker)
    monkeypatch.setattr(rebalancer_mod, "PortfolioRebalancer", _FakeRebalancer)
    monkeypatch.setattr(orchestrator_mod, "execute_orders_with_idempotent_retry", lambda _r, _o: [])

    payload = {
        "execution_orders": [
            _payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1"),
            _payload_row(ticker="MSFT", target_weight=0.2, client_order_id="cid-msft-1"),
        ]
    }

    with pytest.raises(ValueError, match="payload/calculated symbol drift detected"):
        mod._execute_payload_via_idempotent_helper(payload)


def test_main_payload_guardrail_exception_aborts_cleanly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, int] = {"save": 0, "notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: (_ for _ in ()).throw(ValueError("bad payload")))
    monkeypatch.setattr(mod, "save_payload", lambda _payload: calls.__setitem__("save", calls["save"] + 1))
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out
    assert rc == 1
    assert calls["save"] == 0
    assert calls["notify"] == 0
    assert "[ABORT] Payload generation blocked by guardrail: bad payload" in out


def test_main_save_payload_exception_aborts_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = {"execution_orders": [{"ticker": "AAPL"}]}
    calls: dict[str, int] = {"notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: (_ for _ in ()).throw(RuntimeError("disk full")))
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[ABORT] Payload persistence failed under guardrails: disk full" in out


def test_main_notify_exception_aborts_nonzero_payload_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = {"execution_orders": [{"ticker": "AAPL"}]}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.delenv(mod.LOCAL_SUBMIT_ENV, raising=False)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: (_ for _ in ()).throw(RuntimeError("webhook down")))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert "[ABORT] Payload notification failed under guardrails: webhook down" in out


def test_main_local_submit_helper_exception_aborts_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [{"ticker": "AAPL", "target_weight": 0.2, "trade_day": "20260228"}],
    })
    calls: dict[str, int] = {"notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    monkeypatch.setattr(
        mod,
        "_execute_payload_via_idempotent_helper",
        lambda _payload: (_ for _ in ()).throw(RuntimeError("broker init blocked")),
    )

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[ABORT] Local submit path failed under guardrails: broker init blocked" in out


def test_main_local_submit_sink_write_failure_aborts_without_notify(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
    })
    calls: dict[str, int] = {"notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "_execute_payload_via_idempotent_helper", lambda _payload: [{"result": {"ok": True}}])
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: (_ for _ in ()).throw(RuntimeError("duckdb locked")),
    )
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "Microstructure telemetry persistence failed" in out
    assert "duckdb locked" in out


def test_main_local_submit_async_flush_failure_aborts_without_notify(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
    })
    calls: dict[str, int] = {"notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "_execute_payload_via_idempotent_helper", lambda _payload: [{"result": {"ok": True}}])
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {
            "orders_written": len(_results),
            "fills_written": 0,
            "parquet_path": str(tmp_path / "execution_microstructure.parquet"),
            "fills_parquet_path": str(tmp_path / "execution_microstructure_fills.parquet"),
            "duckdb_path": str(tmp_path / "execution_microstructure.duckdb"),
            "duckdb_table": "execution_microstructure",
            "spool_path": str(tmp_path / "execution_microstructure_spool.jsonl"),
            "async_flush_scheduled": True,
        },
    )
    monkeypatch.setattr(
        "execution.microstructure.wait_for_execution_microstructure_flush",
        lambda **_kwargs: False,
    )
    monkeypatch.setattr(
        "execution.microstructure.get_execution_microstructure_spool_status",
        lambda **_kwargs: {"pending_bytes": 128, "last_flush_error": "forced async failure"},
    )
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "Microstructure telemetry persistence failed" in out
    assert "async telemetry flush durability gate failed" in out
    assert "[TELEMETRY] Microstructure sink updated" not in out
    assert "[SUCCESS] Local submit finished:" not in out


def test_main_local_submit_notify_exception_aborts_nonzero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [_payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1")],
    })

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "_execute_payload_via_idempotent_helper", lambda _payload: [{"result": {"ok": True}}])
    monkeypatch.setattr(
        mod,
        "_persist_execution_microstructure",
        lambda _results, _payload: {"orders_written": len(_results), "fills_written": 0},
    )
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: (_ for _ in ()).throw(RuntimeError("webhook down")))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert "[ABORT] Post-submit notification failed under guardrails: webhook down" in out


def test_main_local_submit_malformed_payload_fails_closed_without_notify(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    payload = _signed_payload({
        "timestamp": "2026-02-28T15:55:00Z",
        "execution_orders": [
            _payload_row(ticker="AAPL", target_weight=0.2, client_order_id="cid-aapl-1"),
            {"ticker": "MSFT", "target_weight": 0.2, "action": "BUY", "order_type": "MARKET", "limit_price": "Market"},
        ],
    })
    calls: dict[str, int] = {"notify": 0}

    monkeypatch.setattr(mod, "check_kill_switch", lambda: None)
    monkeypatch.setattr(mod.sys, "stdin", _StdinStub(True))
    monkeypatch.setattr(
        mod,
        "AutoFetcher",
        lambda: _AutoFetcherStub(dram=0.1, tsmc=20.0, energy=0.02, cloud=0.3),
    )
    monkeypatch.setattr(mod, "get_manual_input", lambda _p, d=0.0: d)
    monkeypatch.setattr(mod, "run_alpha_sovereign_scan", lambda manual_inputs: _scan_frame())
    monkeypatch.setattr(mod, "confirm_execution_intent", lambda **_kwargs: True)
    monkeypatch.setenv(mod.LOCAL_SUBMIT_ENV, mod.LOCAL_SUBMIT_VALUE)
    monkeypatch.setattr(mod, "generate_execution_payload", lambda _df: payload)
    monkeypatch.setattr(mod, "save_payload", lambda _payload: None)
    monkeypatch.setattr(mod, "notify_pm", lambda _payload: calls.__setitem__("notify", calls["notify"] + 1))

    rc = mod.main()
    out = capsys.readouterr().out

    assert rc == 1
    assert calls["notify"] == 0
    assert "[ABORT] Local submit path failed under guardrails:" in out
    assert "missing client_order_id" in out
