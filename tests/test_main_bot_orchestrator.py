from __future__ import annotations

import subprocess
import time
from types import SimpleNamespace

import pytest

import main_bot_orchestrator as mod
from execution.rebalancer import PortfolioRebalancer


def test_run_scanners_runs_both_subprocesses_and_logs_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: list[tuple[list[str], dict[str, object]]] = []
    errors: list[str] = []

    class _FakeProc:
        def __init__(self, cmd, **kwargs):
            self.cmd = list(cmd)
            self.kwargs = dict(kwargs)
            calls.append((self.cmd, self.kwargs))
            self.returncode = 0

        def communicate(self, timeout):
            assert timeout == mod.SCANNER_TIMEOUT_SECONDS
            if "alpha_quad_scanner.py" in self.cmd[1]:
                return "alpha-ok\n", "alpha-warning"
            return "fourier-ok\n", "fourier-warning"

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(mod.subprocess, "Popen", _FakeProc)
    monkeypatch.setattr(mod.logging, "error", lambda msg: errors.append(str(msg)))

    mod.run_scanners()
    out = capsys.readouterr().out

    assert [call[0] for call in calls] == [
        [".venv/Scripts/python.exe", "scripts/alpha_quad_scanner.py"],
        [".venv/Scripts/python.exe", "scripts/fourier_opportunity_gate.py"],
    ]
    for _, kwargs in calls:
        assert kwargs.get("stdout") is mod.subprocess.PIPE
        assert kwargs.get("stderr") is mod.subprocess.PIPE
        assert kwargs.get("text") is True
        if mod.os.name == "nt":
            assert "creationflags" in kwargs
        else:
            assert kwargs.get("start_new_session") is True
    assert "alpha-ok" in out
    assert "fourier-ok" in out
    assert any("Alpha Quad Errors: alpha-warning" in e for e in errors)
    assert any("Fourier Scanner Errors: fourier-warning" in e for e in errors)


def test_run_scanners_fail_stops_on_non_zero_returncode(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []

    class _FakeProc:
        def __init__(self, cmd, **kwargs):
            self.cmd = list(cmd)
            self.kwargs = dict(kwargs)
            calls.append(self.cmd)
            self.returncode = 2 if "alpha_quad_scanner.py" in self.cmd[1] else 0

        def communicate(self, timeout):
            _ = timeout
            return "", "alpha failed" if self.returncode else ""

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            return self.returncode

    monkeypatch.setattr(mod.subprocess, "Popen", _FakeProc)

    with pytest.raises(RuntimeError, match="Alpha Quad Scanner failed with return code 2"):
        mod.run_scanners()

    assert calls == [[mod.PYTHON_EXECUTABLE, "scripts/alpha_quad_scanner.py"]]


def test_run_scanners_fail_stops_on_subprocess_timeout(monkeypatch: pytest.MonkeyPatch):
    calls: list[list[str]] = []
    terminated: list[int] = []

    class _TimeoutProc:
        def __init__(self, cmd, **kwargs):
            self.cmd = list(cmd)
            self.kwargs = dict(kwargs)
            self.pid = 4321
            self.returncode = None
            calls.append(self.cmd)

        def communicate(self, timeout):
            raise subprocess.TimeoutExpired(cmd=self.cmd, timeout=timeout)

        def poll(self):
            return self.returncode

        def wait(self, timeout=None):
            self.returncode = -9
            return self.returncode

    monkeypatch.setattr(mod.subprocess, "Popen", _TimeoutProc)
    monkeypatch.setattr(
        mod,
        "_terminate_process_tree",
        lambda proc: terminated.append(int(proc.pid))
        or {
            "parent_pid": int(proc.pid),
            "descendant_evidence": [],
            "parent_alive_after_termination": False,
            "sterilized": True,
            "termination_errors": [],
            "proof_algorithm": "sha256",
            "proof_hash": "proof",
        },
    )

    with pytest.raises(subprocess.TimeoutExpired):
        mod.run_scanners()

    assert calls == [[mod.PYTHON_EXECUTABLE, "scripts/alpha_quad_scanner.py"]]
    assert terminated == [4321]


def test_main_runs_diagnostic_then_schedules_and_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    calls: dict[str, object] = {
        "diagnostic_runs": 0,
        "every_called": 0,
        "friday_called": 0,
        "at": "",
        "do_fn": None,
        "run_pending_calls": 0,
    }

    class _FakeScheduleJob:
        def __init__(self, state: dict[str, object]) -> None:
            self._state = state

        @property
        def friday(self):
            self._state["friday_called"] = int(self._state["friday_called"]) + 1
            return self

        def at(self, when: str):
            self._state["at"] = when
            return self

        def do(self, fn):
            self._state["do_fn"] = fn
            return self

    monkeypatch.setattr(mod, "run_scanners", lambda: calls.__setitem__("diagnostic_runs", int(calls["diagnostic_runs"]) + 1))
    monkeypatch.setattr(
        mod.schedule,
        "every",
        lambda: calls.__setitem__("every_called", int(calls["every_called"]) + 1) or _FakeScheduleJob(calls),
    )

    def _run_pending():
        calls["run_pending_calls"] = int(calls["run_pending_calls"]) + 1
        raise KeyboardInterrupt

    monkeypatch.setattr(mod.schedule, "run_pending", _run_pending)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: None)

    mod.main()
    out = capsys.readouterr().out

    assert calls["diagnostic_runs"] == 1
    assert calls["every_called"] == 1
    assert calls["friday_called"] == 1
    assert calls["at"] == "15:55"
    assert calls["do_fn"] is mod.run_scanners
    assert calls["run_pending_calls"] == 1
    assert "Sovereign Orchestrator locally disarmed by user." in out


def test_main_logs_scheduled_failure_and_continues_until_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: dict[str, int] = {
        "run_pending_calls": 0,
    }
    errors: list[str] = []

    class _FakeScheduleJob:
        @property
        def friday(self):
            return self

        def at(self, _when: str):
            return self

        def do(self, _fn):
            return self

    monkeypatch.setattr(mod, "run_scanners", lambda: None)
    monkeypatch.setattr(mod.schedule, "every", lambda: _FakeScheduleJob())

    def _run_pending():
        calls["run_pending_calls"] += 1
        if calls["run_pending_calls"] == 1:
            raise RuntimeError("scanner boom")
        raise KeyboardInterrupt

    monkeypatch.setattr(mod.schedule, "run_pending", _run_pending)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(mod.logging, "error", lambda msg: errors.append(str(msg)))

    mod.main()

    assert calls["run_pending_calls"] == 2
    assert any("Scheduled run failed: scanner boom" in msg for msg in errors)


def test_main_logs_startup_diagnostic_failure_and_continues_to_scheduler(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: dict[str, int] = {
        "startup_calls": 0,
        "run_pending_calls": 0,
    }
    errors: list[str] = []

    class _FakeScheduleJob:
        @property
        def friday(self):
            return self

        def at(self, _when: str):
            return self

        def do(self, _fn):
            return self

    def _run_scanners():
        calls["startup_calls"] += 1
        if calls["startup_calls"] == 1:
            raise RuntimeError("startup boom")

    def _run_pending():
        calls["run_pending_calls"] += 1
        raise KeyboardInterrupt

    monkeypatch.setattr(mod, "run_scanners", _run_scanners)
    monkeypatch.setattr(mod.schedule, "every", lambda: _FakeScheduleJob())
    monkeypatch.setattr(mod.schedule, "run_pending", _run_pending)
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(mod.logging, "error", lambda msg: errors.append(str(msg)))

    mod.main()

    assert calls["startup_calls"] == 1
    assert calls["run_pending_calls"] == 1
    assert any("Startup diagnostic scan failed: startup boom" in msg for msg in errors)


def test_main_raises_on_startup_terminal_scanner_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        mod,
        "run_scanners",
        lambda: (_ for _ in ()).throw(mod.ScannerTerminationError("tree still alive")),
    )

    with pytest.raises(mod.ScannerTerminationError, match="tree still alive"):
        mod.main()


def test_main_raises_on_scheduled_terminal_scanner_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    errors: list[str] = []

    class _FakeScheduleJob:
        @property
        def friday(self):
            return self

        def at(self, _when: str):
            return self

        def do(self, _fn):
            return self

    monkeypatch.setattr(mod, "run_scanners", lambda: None)
    monkeypatch.setattr(mod.schedule, "every", lambda: _FakeScheduleJob())
    monkeypatch.setattr(
        mod.schedule,
        "run_pending",
        lambda: (_ for _ in ()).throw(mod.ScannerTerminationError("kill not confirmed")),
    )
    monkeypatch.setattr(mod.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(mod.logging, "critical", lambda msg: errors.append(str(msg)))

    with pytest.raises(mod.ScannerTerminationError, match="kill not confirmed"):
        mod.main()

    assert any("Scheduled scanner failure requires orchestrator stop" in msg for msg in errors)


def test_terminate_process_tree_windows_logs_when_taskkill_nonzero_and_returns_receipt(
    monkeypatch: pytest.MonkeyPatch,
):
    errors: list[str] = []

    class _FakeProc:
        pid = 9999

        def __init__(self) -> None:
            self._alive = True

        def poll(self):
            return None if self._alive else 0

        def wait(self, timeout=None):
            _ = timeout
            return 0

        def kill(self):
            self._alive = False

    wait_calls = {"count": 0}

    def _fake_wait(_proc, _timeout):
        wait_calls["count"] += 1
        return wait_calls["count"] >= 2

    snapshots = [
        [
            {"pid": 9999, "ppid": 1, "name": "parent.exe"},
            {"pid": 1234, "ppid": 9999, "name": "child.exe"},
        ],
        [
            {"pid": 1234, "ppid": 1, "name": "child.exe"},
        ],
    ]

    monkeypatch.setattr(mod.os, "name", "nt", raising=False)
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr="access denied"),
    )
    monkeypatch.setattr(mod, "_collect_process_snapshot", lambda: snapshots.pop(0))
    monkeypatch.setattr(mod, "_wait_for_process_exit", _fake_wait)
    monkeypatch.setattr(mod.logging, "error", lambda msg: errors.append(str(msg)))

    receipt = mod._terminate_process_tree(_FakeProc())

    assert any("taskkill failed (rc=1): access denied" in msg for msg in errors)
    assert receipt["parent_pid"] == 9999
    assert receipt["sterilized"] is False
    assert receipt["descendant_evidence"] == [
        {
            "pid": 1234,
            "ppid": 9999,
            "name": "child.exe",
            "alive_after_termination": True,
        }
    ]
    assert "taskkill_nonzero_rc_1" in receipt["termination_errors"]
    assert len(receipt["proof_hash"]) == 64
    assert receipt["proof_algorithm"] == "sha256"


def test_terminate_process_tree_receipt_is_stable_ordered_and_hash_deterministic(
    monkeypatch: pytest.MonkeyPatch,
):
    class _FakeProc:
        pid = 9000

        def poll(self):
            return None

    monkeypatch.setattr(mod.os, "name", "nt", raising=False)
    monkeypatch.setattr(
        mod.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr=""),
    )
    monkeypatch.setattr(mod, "_wait_for_process_exit", lambda _proc, _timeout: True)

    snapshots_a = [
        [
            {"pid": 9000, "ppid": 1, "name": "parent.exe"},
            {"pid": 4200, "ppid": 9000, "name": "zeta.exe"},
            {"pid": 5100, "ppid": 4100, "name": "grand.exe"},
            {"pid": 4100, "ppid": 9000, "name": "alpha.exe"},
        ],
        [],
    ]
    monkeypatch.setattr(mod, "_collect_process_snapshot", lambda: snapshots_a.pop(0))
    receipt_a = mod._terminate_process_tree(_FakeProc())

    snapshots_b = [
        [
            {"pid": 9000, "ppid": 1, "name": "parent.exe"},
            {"pid": 5100, "ppid": 4100, "name": "grand.exe"},
            {"pid": 4100, "ppid": 9000, "name": "alpha.exe"},
            {"pid": 4200, "ppid": 9000, "name": "zeta.exe"},
        ],
        [],
    ]
    monkeypatch.setattr(mod, "_collect_process_snapshot", lambda: snapshots_b.pop(0))
    receipt_b = mod._terminate_process_tree(_FakeProc())

    assert receipt_a["sterilized"] is True
    assert receipt_b["sterilized"] is True
    assert [row["pid"] for row in receipt_a["descendant_evidence"]] == [4100, 4200, 5100]
    assert [row["pid"] for row in receipt_b["descendant_evidence"]] == [4100, 4200, 5100]
    assert receipt_a["descendant_evidence"] == receipt_b["descendant_evidence"]
    assert receipt_a["proof_hash"] == receipt_b["proof_hash"]
    assert len(receipt_a["proof_hash"]) == 64


def test_run_scanner_step_timeout_fails_closed_when_sterilization_proof_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    class _TimeoutProc:
        pid = 4321

        def communicate(self, timeout):
            raise subprocess.TimeoutExpired(cmd=["x"], timeout=timeout)

        def poll(self):
            return None

    monkeypatch.setattr(mod, "_spawn_scanner_process", lambda _path: _TimeoutProc())
    monkeypatch.setattr(
        mod,
        "_terminate_process_tree",
        lambda _proc: {
            "parent_pid": 4321,
            "descendant_evidence": [{"pid": 5000, "ppid": 4321, "name": "child.exe", "alive_after_termination": True}],
            "parent_alive_after_termination": False,
            "sterilized": False,
            "termination_errors": ["post_snapshot_unavailable"],
            "proof_algorithm": "sha256",
            "proof_hash": "deadbeef",
        },
    )

    with pytest.raises(mod.ScannerTerminationError, match="sterilization proof failed"):
        mod._run_scanner_step("Scanner", "scripts/alpha_quad_scanner.py", "err")


class _RiskContextMixin:
    def get_portfolio_state(self) -> dict:
        # Minimal deterministic context so idempotent retry tests do not bypass risk gates.
        return {
            "equity": 1_000_000.0,
            "positions": {"AAPL": 1000, "MSFT": 1000, "NVDA": 1000},
        }

    def get_latest_price(self, symbol: str) -> float:
        _ = symbol
        return 100.0


class _PhantomFillBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": True,
            "order_id": "recovered-ord-1",
            "status": "accepted",
            "recovered": True,
            "recovery_reason": "Order already exists",
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 101.25,
            "execution_ts": "2026-03-06T15:30:01.250Z",
        }


def test_execute_orders_with_idempotent_retry_recovers_phantom_fill_with_static_cid():
    broker = _PhantomFillBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 2, "side": "buy", "trade_day": "20260306"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert broker.submit_calls[0]["client_order_id"] == broker.submit_calls[1]["client_order_id"]
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["recovered"] is True
    assert results[0]["result"]["client_order_id"] == broker.submit_calls[0]["client_order_id"]
    assert results[0]["result"]["attempt"] == 2


class _AlreadyExistsMatchingBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": False,
            "error": "Order already exists",
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 100.10,
            "execution_ts": "2026-03-01T15:32:00.100Z",
        }


def test_execute_orders_with_idempotent_retry_accepts_already_exists_on_strict_match():
    broker = _AlreadyExistsMatchingBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "MSFT", "qty": 1, "side": "buy", "client_order_id": "cid-static-1"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert broker.submit_calls[0]["client_order_id"] == "cid-static-1"
    assert broker.submit_calls[1]["client_order_id"] == "cid-static-1"
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["recovered"] is True
    assert results[0]["result"]["attempt"] == 2


class _AlreadyExistsMarketNullLimitBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": False,
            "error": "Order already exists",
            "status": "accepted",
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            "order_type": "market",
            "limit_price": "null",
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 100.20,
            "execution_ts": "2026-03-01T15:33:00.100Z",
        }


def test_execute_orders_with_idempotent_retry_accepts_market_recovery_with_text_null_limit():
    broker = _AlreadyExistsMarketNullLimitBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-market-null-limit"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["recovered"] is True
    assert results[0]["result"]["attempt"] == 2


class _RecoveryMismatchBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": True,
            "order_id": "mismatch-ord-1",
            "status": "accepted",
            "recovered": True,
            "client_order_id": str(client_order_id),
            "symbol": "NVDA",
            "side": payload["side"],
            "qty": payload["qty"],
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 100.30,
            "execution_ts": "2026-03-01T15:34:00.100Z",
        }


def test_execute_orders_with_idempotent_retry_rejects_recovery_payload_mismatch():
    broker = _RecoveryMismatchBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 2, "side": "buy", "client_order_id": "cid-static-2"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert broker.submit_calls[0]["client_order_id"] == "cid-static-2"
    assert broker.submit_calls[1]["client_order_id"] == "cid-static-2"
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "recovery_mismatch"
    assert results[0]["result"]["attempt"] == 2


class _AlreadyExistsMismatchBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": False,
            "error": "Order already exists",
            "client_order_id": str(client_order_id),
            "symbol": "NVDA",
            "side": payload["side"],
            "qty": payload["qty"],
        }


def test_execute_orders_with_idempotent_retry_rejects_already_exists_payload_mismatch_without_retrying():
    broker = _AlreadyExistsMismatchBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 2, "side": "buy", "client_order_id": "cid-static-3"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=3,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "recovery_mismatch"
    assert results[0]["result"]["attempt"] == 2


class _AlreadyExistsMissingBrokerCidRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        return [
            {
                "order": order,
                "result": {
                    "ok": False,
                    "error": "Order already exists",
                    # Missing client_order_id in result must not pass via order-map fallback.
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": float(order["qty"]),
                    "filled_avg_price": 100.40,
                    "execution_ts": "2026-03-01T15:39:00.100Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_rejects_already_exists_without_broker_client_order_id():
    rebalancer = _AlreadyExistsMissingBrokerCidRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-no-broker-cid"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "recovery_mismatch"
    assert results[0]["result"]["attempt"] == 1


class _AlreadyExistsSparseBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []
        self.lookup_calls: list[str] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": False,
            "error": "Order already exists",
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
        }

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        return None


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_sparse_already_exists_recovery(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _AlreadyExistsSparseBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-already-exists-sparse"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-already-exists-sparse"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert len(broker.submit_calls) == 2
    assert broker.lookup_calls == ["cid-already-exists-sparse", "cid-already-exists-sparse"]


class _AlreadyExistsFillSummaryFallbackBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []
        self.lookup_calls: list[str] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": False,
            "error": "Order already exists",
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            # Non-authoritative fallback data must not satisfy strict-success.
            "fill_summary": {
                "fill_qty": float(payload["qty"]),
                "fill_vwap": 100.55,
                "first_fill_ts": "2026-03-01T15:39:59.000Z",
            },
            "filled_at": "2026-03-01T15:40:00.000Z",
        }

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        return None


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_already_exists_with_non_authoritative_fill_summary(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _AlreadyExistsFillSummaryFallbackBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-already-exists-fill-summary"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-already-exists-fill-summary"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert len(broker.submit_calls) == 2
    assert broker.lookup_calls == ["cid-already-exists-fill-summary", "cid-already-exists-fill-summary"]


class _AlwaysTimeoutBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}


def test_execute_orders_with_idempotent_retry_marks_retry_exhausted_after_max_attempts():
    broker = _AlwaysTimeoutBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-retry-exhausted"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "retry_exhausted"
    assert results[0]["result"]["attempt"] == 2


class _BatchExceptionThenSuccessRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("submit transport timeout")
        order = dict(orders[0])
        return [
            {
                "order": order,
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": str(order["client_order_id"]),
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": float(order["qty"]),
                    "filled_avg_price": 100.80,
                    "execution_ts": "2026-03-01T15:44:00.100Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_recovers_after_transient_batch_exception():
    rebalancer = _BatchExceptionThenSuccessRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-batch-exc-retry"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 1
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["attempt"] == 2


class _AlwaysBatchExceptionRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = orders, dry_run
        self.calls += 1
        raise RuntimeError("broker offline")


def test_execute_orders_with_idempotent_retry_fails_closed_when_batch_raises_until_exhausted():
    rebalancer = _AlwaysBatchExceptionRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-batch-exc-exhausted"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "retry_exhausted"
    assert results[0]["result"]["last_error"] == "batch_exception:RuntimeError"
    assert results[0]["result"]["attempt"] == 2


class _NonRetryableBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(self, symbol: str, qty: int, side: str, client_order_id: str | None = None) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
        }
        self.submit_calls.append(payload)
        return {"ok": False, "error": "insufficient buying power", "client_order_id": str(client_order_id)}


def test_execute_orders_with_idempotent_retry_fails_non_retryable_error_without_retries():
    broker = _NonRetryableBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [{"symbol": "MSFT", "qty": 1, "side": "buy", "client_order_id": "cid-no-retry"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=3,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "insufficient buying power"
    assert results[0]["result"]["attempt"] == 1


class _TerminalUnfilledNoRetryRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        cid = str(order["client_order_id"])
        return [
            {
                "order": order,
                "result": {
                    "ok": True,
                    "status": "canceled",
                    "error": "transient submit timeout",
                    "client_order_id": cid,
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": 0,
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_terminal_unfilled_fails_closed_without_retry_thrash():
    rebalancer = _TerminalUnfilledNoRetryRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-terminal-unfilled"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=5,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["status"] == "canceled"
    assert results[0]["result"]["terminal_reason"] == "terminal_unfilled"
    assert results[0]["result"]["error"] == "terminal_unfilled:canceled"
    assert results[0]["result"]["broker_error_raw"] == "transient submit timeout"
    assert results[0]["result"]["attempt"] == 1


class _TerminalPartialFillNoRetryRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        cid = str(order["client_order_id"])
        return [
            {
                "order": order,
                "result": {
                    "ok": False,
                    "status": "canceled",
                    "error": "transient submit timeout",
                    "client_order_id": cid,
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": 1,
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_terminal_partial_fill_fails_closed_without_retry_thrash():
    rebalancer = _TerminalPartialFillNoRetryRebalancer()
    orders = [{"symbol": "AAPL", "qty": 2, "side": "buy", "client_order_id": "cid-terminal-partial"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=5,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["status"] == "canceled"
    assert results[0]["result"]["terminal_reason"] == "terminal_partial_fill"
    assert results[0]["result"]["error"] == "terminal_partial_fill:canceled"
    assert results[0]["result"]["broker_error_raw"] == "transient submit timeout"
    assert results[0]["result"]["attempt"] == 1


class _TerminalStatusNormalizationRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        cid = str(order["client_order_id"])
        return [
            {
                "order": order,
                "result": {
                    "ok": True,
                    "status": "  CANCELED  ",
                    "error": "  broker text  ",
                    "client_order_id": cid,
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": 0,
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_normalizes_terminal_status_and_preserves_broker_error():
    rebalancer = _TerminalStatusNormalizationRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-terminal-status-normalized"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["status"] == "canceled"
    assert results[0]["result"]["terminal_reason"] == "terminal_unfilled"
    assert results[0]["result"]["error"] == "terminal_unfilled:canceled"
    assert results[0]["result"]["broker_error_raw"] == "broker text"
    assert results[0]["result"]["attempt"] == 1


class _PartialBatchResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        self.calls += 1
        if self.calls == 1:
            order = dict(orders[0])
            return [
                {
                    "order": order,
                    "result": {
                        "ok": True,
                        "status": "accepted",
                        "client_order_id": str(order["client_order_id"]),
                        "symbol": str(order["symbol"]),
                        "side": str(order["side"]),
                        "qty": int(order["qty"]),
                        "filled_qty": float(order["qty"]),
                        "filled_avg_price": 100.10,
                        "execution_ts": "2026-03-01T15:35:00.100Z",
                    },
                }
            ]
        order = dict(orders[0])
        return [
            {
                "order": order,
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": str(order["client_order_id"]),
                    "symbol": str(order["symbol"]),
                    "side": str(order["side"]),
                    "qty": int(order["qty"]),
                    "filled_qty": float(order["qty"]),
                    "filled_avg_price": 100.20,
                    "execution_ts": "2026-03-01T15:35:01.100Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_retries_missing_batch_cid_without_silent_drop():
    rebalancer = _PartialBatchResultRebalancer()
    orders = [
        {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-a"},
        {"symbol": "MSFT", "qty": 1, "side": "buy", "client_order_id": "cid-b"},
    ]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 2
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["attempt"] == 1
    assert results[1]["result"]["ok"] is True
    assert results[1]["result"]["attempt"] == 2


class _AlwaysMissingBatchResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        self.calls += 1
        return []


def test_execute_orders_with_idempotent_retry_fails_closed_when_batch_result_row_missing_after_retries():
    rebalancer = _AlwaysMissingBatchResultRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-missing"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "batch_result_missing"
    assert results[0]["result"]["attempt"] == 2


class _NoCallRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        self.calls += 1
        return []


def test_execute_orders_with_idempotent_retry_rejects_duplicate_symbols_before_submit():
    rebalancer = _NoCallRebalancer()
    orders = [
        {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-a-1"},
        {"symbol": "AAPL", "qty": 2, "side": "sell", "client_order_id": "cid-a-2"},
    ]

    with pytest.raises(ValueError, match="Duplicate symbol in initial order set: AAPL"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 0


def test_execute_orders_with_idempotent_retry_rejects_duplicate_client_order_ids_before_submit():
    rebalancer = _NoCallRebalancer()
    orders = [
        {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "dup-cid"},
        {"symbol": "MSFT", "qty": 1, "side": "buy", "client_order_id": "dup-cid"},
    ]

    with pytest.raises(ValueError, match="Duplicate client_order_id in initial order set: dup-cid"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 0


def test_execute_orders_with_idempotent_retry_rejects_invalid_max_attempts():
    rebalancer = _NoCallRebalancer()
    with pytest.raises(ValueError, match="max_attempts must be >= 1"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-a"}],
            max_attempts=0,
            retry_sleep_seconds=0.0,
        )


def test_execute_orders_with_idempotent_retry_rejects_non_dict_order_input():
    rebalancer = _NoCallRebalancer()
    with pytest.raises(TypeError, match="order must be a dict"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            ["bad-order"],  # type: ignore[list-item]
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )


def test_execute_orders_with_idempotent_retry_rejects_bool_qty_in_input():
    rebalancer = _NoCallRebalancer()
    with pytest.raises(ValueError, match="order has invalid qty: True"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            [{"symbol": "AAPL", "qty": True, "side": "buy", "client_order_id": "cid-bool-qty"}],  # type: ignore[list-item]
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )


def test_execute_orders_with_idempotent_retry_returns_empty_list_without_submit_calls():
    rebalancer = _NoCallRebalancer()
    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        [],
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )
    assert results == []
    assert rebalancer.calls == 0


def test_execute_orders_with_idempotent_retry_requires_client_order_id_or_trade_day_seed():
    rebalancer = _NoCallRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy"}]

    with pytest.raises(ValueError, match="order missing id seed"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 0


def test_execute_orders_with_idempotent_retry_treats_none_client_order_id_as_missing_seed():
    rebalancer = _NoCallRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": None}]

    with pytest.raises(ValueError, match="order missing id seed"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=2,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 0


class _MalformedRowRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[object]:
        self.calls += 1
        return [
            {"order": "not-a-dict", "result": "not-a-dict"},
            "bad-row-shape",
        ]


def test_execute_orders_with_idempotent_retry_ignores_malformed_rows_and_fails_closed():
    rebalancer = _MalformedRowRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-malformed"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "batch_result_missing"
    assert results[0]["result"]["attempt"] == 2


class _NoneBatchResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False):
        _ = orders, dry_run
        self.calls += 1
        return None


def test_execute_orders_with_idempotent_retry_handles_none_batch_results_fail_closed():
    rebalancer = _NoneBatchResultRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-none-batch"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "batch_result_missing"
    assert results[0]["result"]["attempt"] == 2


class _StringOkResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": "false",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_ignores_non_boolean_ok_and_fails_closed():
    rebalancer = _StringOkResultRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-string-ok"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "malformed_ok_flag"
    assert results[0]["result"]["attempt"] == 1


class _MissingOkResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": cid},
                "result": {"client_order_id": cid},
            }
        ]


def test_execute_orders_with_idempotent_retry_ignores_dict_result_missing_ok_and_fails_closed():
    rebalancer = _MissingOkResultRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-missing-ok"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "malformed_ok_flag"
    assert results[0]["result"]["attempt"] == 1


class _OkTrueIntentMismatchRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": "NVDA",
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                    "filled_qty": float(orders[0]["qty"]),
                    "filled_avg_price": 100.40,
                    "execution_ts": "2026-03-01T15:36:00.100Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_rejects_ok_true_payload_intent_mismatch():
    rebalancer = _OkTrueIntentMismatchRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-ok-true-mismatch"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "intent_mismatch"
    assert results[0]["result"]["attempt"] == 1


class _OkTrueSparsePayloadRebalancer:
    def __init__(self, broker: object) -> None:
        self.calls = 0
        self.broker = broker

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                },
            }
        ]


class _OkTrueFillSummaryFallbackPayloadRebalancer:
    def __init__(self, broker: object) -> None:
        self.calls = 0
        self.broker = broker

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                    # Non-authoritative fallback data must not satisfy strict-success.
                    "fill_summary": {
                        "fill_qty": float(orders[0]["qty"]),
                        "fill_vwap": 101.55,
                        "first_fill_ts": "2026-03-01T15:39:59.000Z",
                    },
                    "filled_at": "2026-03-01T15:40:00.000Z",
                },
            }
        ]


class _OkTrueMissingCidPayloadRebalancer:
    def __init__(self, broker: object) -> None:
        self.calls = 0
        self.broker = broker

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    # Missing broker client_order_id must force reconciliation for authoritative identity.
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                    "filled_qty": float(orders[0]["qty"]),
                    "filled_avg_price": 101.80,
                    "execution_ts": "2026-03-01T15:40:00.250Z",
                },
            }
        ]


class _SparseOkReconciliationBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.lookup_calls: list[str] = []

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        return None


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_sparse_ok_true_and_polls_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueSparsePayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-sparse-ok"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 3)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-sparse-ok"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-sparse-ok", "cid-sparse-ok", "cid-sparse-ok"]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_ok_true_non_authoritative_fill_summary_payload(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueFillSummaryFallbackPayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-sparse-fill-summary"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-sparse-fill-summary"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-sparse-fill-summary", "cid-sparse-fill-summary"]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_ok_true_missing_broker_client_order_id(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueMissingCidPayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-sparse-missing-cid"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-sparse-missing-cid"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-sparse-missing-cid", "cid-sparse-missing-cid"]


class _SparseOkReconciliationResolvedBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.lookup_calls: list[str] = []

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        return {
            "ok": True,
            "status": "filled",
            "client_order_id": str(client_order_id),
            "symbol": "AAPL",
            "side": "buy",
            "qty": 1,
            "filled_qty": 1.0,
            "filled_avg_price": 101.75,
            "execution_ts": "2026-03-01T15:40:00.250Z",
        }


def test_execute_orders_with_idempotent_retry_reconciles_sparse_ok_true_with_authoritative_receipt(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationResolvedBroker()
    rebalancer = _OkTrueSparsePayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-sparse-ok-recovered"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-sparse-ok-recovered"]
    assert len(results) == 1
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["filled_qty"] == pytest.approx(1.0)
    assert results[0]["result"]["filled_avg_price"] == pytest.approx(101.75)
    assert results[0]["result"]["execution_ts"] == "2026-03-01T15:40:00.250Z"


class _OkTrueAuthoritativeFillEdgeRebalancer:
    def __init__(self, broker: object, *, filled_qty: object, filled_avg_price: object) -> None:
        self.calls = 0
        self.broker = broker
        self._filled_qty = filled_qty
        self._filled_avg_price = filled_avg_price

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                    "filled_qty": self._filled_qty,
                    "filled_avg_price": self._filled_avg_price,
                    "execution_ts": "2026-03-01T15:40:00.250Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_ok_true_with_non_positive_filled_qty(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueAuthoritativeFillEdgeRebalancer(
        broker=broker,
        filled_qty=0.0,
        filled_avg_price=101.75,
    )
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-filled-qty-zero"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-filled-qty-zero"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-filled-qty-zero", "cid-filled-qty-zero"]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_ok_true_with_non_positive_filled_avg_price(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueAuthoritativeFillEdgeRebalancer(
        broker=broker,
        filled_qty=1.0,
        filled_avg_price=0.0,
    )
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-filled-avg-zero"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-filled-avg-zero"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-filled-avg-zero", "cid-filled-avg-zero"]


def test_execute_orders_with_idempotent_retry_accepts_ok_true_with_positive_authoritative_fill_boundaries():
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueAuthoritativeFillEdgeRebalancer(
        broker=broker,
        filled_qty=0.000000001,
        filled_avg_price=0.01,
    )
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-fill-boundary-positive"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == []
    assert len(results) == 1
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["filled_qty"] == pytest.approx(0.000000001)
    assert results[0]["result"]["filled_avg_price"] == pytest.approx(0.01)
    assert results[0]["result"]["attempt"] == 1


class _SparseOkReconciliationTerminalUnfilledBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.lookup_calls: list[str] = []

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        return {
            "status": "canceled",
            "client_order_id": str(client_order_id),
            "symbol": "AAPL",
            "side": "buy",
            "qty": 1,
            "filled_qty": 0.0,
        }


def test_execute_orders_with_idempotent_retry_reconciles_sparse_ok_true_to_terminal_unfilled_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationTerminalUnfilledBroker()
    rebalancer = _OkTrueSparsePayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-sparse-ok-terminal"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-sparse-ok-terminal"]
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["status"] == "canceled"
    assert results[0]["result"]["error"] == "terminal_unfilled:canceled"
    assert results[0]["result"]["attempt"] == 1


class _OkTrueBoolQtyRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": True,
                    "filled_qty": 1.0,
                    "filled_avg_price": 101.00,
                    "execution_ts": "2026-03-01T15:41:00.250Z",
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_rejects_ok_true_with_boolean_qty_payload():
    rebalancer = _OkTrueBoolQtyRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-bool-qty-payload"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "intent_mismatch"
    assert results[0]["result"]["attempt"] == 1


class _RowOrderDriftRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": {
                    "symbol": "NVDA",
                    "qty": 1,
                    "side": "buy",
                    "client_order_id": cid,
                },
                "result": {
                    "ok": False,
                    "error": "Order already exists",
                    "client_order_id": cid,
                    "symbol": "NVDA",
                    "side": "buy",
                    "qty": 1,
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_anchors_recovery_to_original_pending_intent():
    rebalancer = _RowOrderDriftRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-intent-anchor"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "recovery_mismatch"
    assert results[0]["result"]["attempt"] == 1


class _NonDictResultWithCidRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": {"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": cid},
                "result": "malformed-result",
            }
        ]


def test_execute_orders_with_idempotent_retry_ignores_non_dict_result_even_with_valid_cid():
    rebalancer = _NonDictResultWithCidRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-malformed-result"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 2
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "batch_result_missing"
    assert results[0]["result"]["attempt"] == 2


class _LimitRecoveryMatchBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        client_order_id: str | None = None,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
            "order_type": str(order_type).lower(),
            "limit_price": limit_price,
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": True,
            "order_id": "recovered-limit-1",
            "status": "accepted",
            "recovered": True,
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            "order_type": payload["order_type"],
            "limit_price": payload["limit_price"],
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 123.45,
            "execution_ts": "2026-03-01T15:42:00.250Z",
        }


def test_execute_orders_with_idempotent_retry_accepts_limit_recovery_with_full_parity():
    broker = _LimitRecoveryMatchBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [
        {
            "symbol": "AAPL",
            "qty": 1,
            "side": "buy",
            "client_order_id": "cid-limit-parity",
            "order_type": "limit",
            "limit_price": 123.45,
        }
    ]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert broker.submit_calls[0]["client_order_id"] == "cid-limit-parity"
    assert broker.submit_calls[1]["client_order_id"] == "cid-limit-parity"
    assert results[0]["result"]["ok"] is True
    assert results[0]["result"]["recovered"] is True
    assert results[0]["result"]["attempt"] == 2


class _LimitRecoveryMismatchBroker(_RiskContextMixin):
    def __init__(self) -> None:
        self.submit_calls: list[dict[str, object]] = []

    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        client_order_id: str | None = None,
        order_type: str = "market",
        limit_price: float | None = None,
    ) -> dict:
        payload = {
            "symbol": str(symbol).upper(),
            "qty": int(qty),
            "side": str(side).lower(),
            "client_order_id": str(client_order_id),
            "order_type": str(order_type).lower(),
            "limit_price": limit_price,
        }
        self.submit_calls.append(payload)
        if len(self.submit_calls) == 1:
            return {"ok": False, "error": "transient submit timeout", "client_order_id": str(client_order_id)}
        return {
            "ok": True,
            "order_id": "recovered-limit-mismatch",
            "status": "accepted",
            "recovered": True,
            "client_order_id": str(client_order_id),
            "symbol": payload["symbol"],
            "side": payload["side"],
            "qty": payload["qty"],
            "order_type": "market",
            "limit_price": None,
            "filled_qty": float(payload["qty"]),
            "filled_avg_price": 123.40,
            "execution_ts": "2026-03-01T15:43:00.250Z",
        }


def test_execute_orders_with_idempotent_retry_rejects_limit_recovery_when_order_type_drifts():
    broker = _LimitRecoveryMismatchBroker()
    rebalancer = PortfolioRebalancer(broker=broker)
    orders = [
        {
            "symbol": "AAPL",
            "qty": 1,
            "side": "buy",
            "client_order_id": "cid-limit-drift",
            "order_type": "limit",
            "limit_price": 111.25,
        }
    ]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,
        orders,
        max_attempts=2,
        retry_sleep_seconds=0.0,
    )

    assert len(broker.submit_calls) == 2
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "recovery_mismatch"
    assert results[0]["result"]["attempt"] == 2


class _OkTrueMalformedExecutionTsRebalancer:
    def __init__(self, broker: object, *, execution_ts: str) -> None:
        self.calls = 0
        self.broker = broker
        self._execution_ts = execution_ts

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        cid = str(orders[0]["client_order_id"])
        return [
            {
                "order": dict(orders[0]),
                "result": {
                    "ok": True,
                    "status": "accepted",
                    "client_order_id": cid,
                    "symbol": str(orders[0]["symbol"]),
                    "side": str(orders[0]["side"]),
                    "qty": int(orders[0]["qty"]),
                    "filled_qty": float(orders[0]["qty"]),
                    "filled_avg_price": 101.25,
                    "execution_ts": self._execution_ts,
                },
            }
        ]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_malformed_execution_ts(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueMalformedExecutionTsRebalancer(
        broker=broker,
        execution_ts="not-an-iso-ts",
    )
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-malformed-execution-ts"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-malformed-execution-ts"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-malformed-execution-ts", "cid-malformed-execution-ts"]


def test_execute_orders_with_idempotent_retry_raises_ambiguous_for_overfilled_qty_vs_order_bound(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueAuthoritativeFillEdgeRebalancer(
        broker=broker,
        filled_qty=2.0,
        filled_avg_price=101.75,
    )
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-overfilled-qty"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="cid-overfilled-qty"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-overfilled-qty", "cid-overfilled-qty"]


class _DuplicateCidBatchResultRebalancer:
    def __init__(self) -> None:
        self.calls = 0

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        cid = str(order["client_order_id"])
        success_row = {
            "order": order,
            "result": {
                "ok": True,
                "status": "accepted",
                "client_order_id": cid,
                "symbol": str(order["symbol"]),
                "side": str(order["side"]),
                "qty": int(order["qty"]),
                "filled_qty": float(order["qty"]),
                "filled_avg_price": 100.25,
                "execution_ts": "2026-03-01T15:45:00.250Z",
            },
        }
        conflicting_row = {
            "order": order,
            "result": {
                "ok": False,
                "error": "Order rejected late",
                "client_order_id": cid,
                "symbol": str(order["symbol"]),
                "side": str(order["side"]),
                "qty": int(order["qty"]),
            },
        }
        return [success_row, conflicting_row]


class _DuplicateCidAmbiguousPermutationRebalancer:
    def __init__(self, *, sparse_first: bool) -> None:
        self.calls = 0
        self.sparse_first = bool(sparse_first)

    def execute_orders(self, orders: list[dict[str, object]], dry_run: bool = False) -> list[dict[str, object]]:
        _ = dry_run
        self.calls += 1
        order = dict(orders[0])
        cid = str(order["client_order_id"])
        sparse_ok_row = {
            "order": order,
            "result": {
                "ok": True,
                "status": "accepted",
                "client_order_id": cid,
                "symbol": str(order["symbol"]),
                "side": str(order["side"]),
                "qty": int(order["qty"]),
                # Missing authoritative receipt fields on purpose.
            },
        }
        authoritative_ok_row = {
            "order": order,
            "result": {
                "ok": True,
                "status": "accepted",
                "client_order_id": cid,
                "symbol": str(order["symbol"]),
                "side": str(order["side"]),
                "qty": int(order["qty"]),
                "filled_qty": float(order["qty"]),
                "filled_avg_price": 100.55,
                "execution_ts": "2026-03-01T15:45:20.250Z",
            },
        }
        if self.sparse_first:
            return [sparse_ok_row, authoritative_ok_row]
        return [authoritative_ok_row, sparse_ok_row]


def test_execute_orders_with_idempotent_retry_fails_closed_on_duplicate_output_rows_for_same_client_order_id():
    rebalancer = _DuplicateCidBatchResultRebalancer()
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-duplicate-output"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "duplicate_batch_result_cid"
    assert results[0]["result"]["attempt"] == 1


@pytest.mark.parametrize("sparse_first", [True, False])
def test_execute_orders_with_idempotent_retry_fails_closed_on_duplicate_output_rows_regardless_of_row_order(
    sparse_first: bool,
):
    rebalancer = _DuplicateCidAmbiguousPermutationRebalancer(sparse_first=sparse_first)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-duplicate-row-order"}]

    results = mod.execute_orders_with_idempotent_retry(
        rebalancer,  # type: ignore[arg-type]
        orders,
        max_attempts=1,
        retry_sleep_seconds=0.0,
    )

    assert rebalancer.calls == 1
    assert len(results) == 1
    assert results[0]["result"]["ok"] is False
    assert results[0]["result"]["error"] == "duplicate_batch_result_cid"
    assert results[0]["result"]["attempt"] == 1


class _SlowLookupBroker(_RiskContextMixin):
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = float(delay_seconds)
        self.lookup_calls: list[str] = []

    def get_order_by_client_order_id(self, client_order_id: str) -> dict[str, object] | None:
        self.lookup_calls.append(str(client_order_id))
        time.sleep(self.delay_seconds)
        return None


def test_execute_orders_with_idempotent_retry_times_out_reconciliation_lookup_and_surfaces_issue(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SlowLookupBroker(delay_seconds=0.05)
    rebalancer = _OkTrueSparsePayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-lookup-timeout"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 2)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(mod.AmbiguousExecutionError, match="lookup_timeout"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == ["cid-lookup-timeout", "cid-lookup-timeout"]


def test_execute_orders_with_idempotent_retry_skips_lookup_when_reconciliation_budget_is_zero(
    monkeypatch: pytest.MonkeyPatch,
):
    broker = _SparseOkReconciliationBroker()
    rebalancer = _OkTrueSparsePayloadRebalancer(broker=broker)
    orders = [{"symbol": "AAPL", "qty": 1, "side": "buy", "client_order_id": "cid-zero-poll-budget"}]

    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_MAX_POLLS", 0)
    monkeypatch.setattr(mod, "EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS", 0.0)

    with pytest.raises(mod.AmbiguousExecutionError, match="reconciliation_poll_budget_zero"):
        mod.execute_orders_with_idempotent_retry(
            rebalancer,  # type: ignore[arg-type]
            orders,
            max_attempts=1,
            retry_sleep_seconds=0.0,
        )

    assert rebalancer.calls == 1
    assert broker.lookup_calls == []
