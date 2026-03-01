from __future__ import annotations

import pandas as pd
import pytest

from views import auto_backtest_view as view_mod
from views.auto_backtest_view import _cost_bps_input_to_decimal


def test_cost_bps_input_to_decimal_handles_fractional_and_integer_bps():
    assert _cost_bps_input_to_decimal(0.5) == 0.00005
    assert _cost_bps_input_to_decimal(10) == 0.001
    assert _cost_bps_input_to_decimal(10000) == 1.0
    assert _cost_bps_input_to_decimal(-1) == 0.0


def _sample_market_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    idx = pd.to_datetime(["2026-03-05", "2026-03-06"])
    prices = pd.DataFrame({101: [100.0, 101.0]}, index=idx)
    returns = pd.DataFrame({101: [0.0, 0.01]}, index=idx)
    macro = pd.DataFrame({"spy_close": [500.0, 505.0]}, index=idx)
    return prices, returns, macro


def test_render_auto_backtest_view_blocks_on_corrupted_cache_without_reset(
    monkeypatch: pytest.MonkeyPatch,
):
    prices, returns, macro = _sample_market_frames()
    errors: list[str] = []
    persist_calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        view_mod.control_plane,
        "load_cache",
        lambda *_args, **_kwargs: view_mod.control_plane.AutoBacktestCacheLoadResult(
            ok=False,
            reason="invalid_payload",
            state=None,
        ),
    )
    monkeypatch.setattr(view_mod.control_plane, "persist_cache_atomic", lambda *a, **k: persist_calls.append((a[0], a[1])))
    monkeypatch.setattr(view_mod.st, "error", lambda msg: errors.append(str(msg)))
    monkeypatch.setattr(view_mod.st, "button", lambda *a, **k: False)
    monkeypatch.setattr(view_mod.st, "success", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("success should not be called")))
    monkeypatch.setattr(view_mod.st, "rerun", lambda: (_ for _ in ()).throw(AssertionError("rerun should not be called")))

    view_mod.render_auto_backtest_view(prices, returns, macro)

    assert any("invalid or unreadable" in msg for msg in errors)
    assert persist_calls == []


def test_render_auto_backtest_view_reset_button_recovers_corrupted_cache(
    monkeypatch: pytest.MonkeyPatch,
):
    prices, returns, macro = _sample_market_frames()
    errors: list[str] = []
    success: list[str] = []
    persist_calls: list[tuple[str, object]] = []
    default_state = view_mod.control_plane.create_default_state()

    monkeypatch.setattr(
        view_mod.control_plane,
        "load_cache",
        lambda *_args, **_kwargs: view_mod.control_plane.AutoBacktestCacheLoadResult(
            ok=False,
            reason="invalid_json",
            state=None,
        ),
    )
    monkeypatch.setattr(view_mod.control_plane, "create_default_state", lambda: default_state)
    monkeypatch.setattr(
        view_mod.control_plane,
        "persist_cache_atomic",
        lambda *a, **k: persist_calls.append((a[0], a[1])),
    )
    monkeypatch.setattr(view_mod.st, "error", lambda msg: errors.append(str(msg)))
    monkeypatch.setattr(view_mod.st, "success", lambda msg: success.append(str(msg)))
    monkeypatch.setattr(view_mod.st, "button", lambda label, **_kwargs: str(label).startswith("Reset Auto-Backtest Cache"))
    monkeypatch.setattr(view_mod.st, "rerun", lambda: (_ for _ in ()).throw(RuntimeError("rerun-triggered")))

    with pytest.raises(RuntimeError, match="rerun-triggered"):
        view_mod.render_auto_backtest_view(prices, returns, macro)

    assert any("invalid or unreadable" in msg for msg in errors)
    assert success == ["Auto-backtest cache reset complete."]
    assert len(persist_calls) == 1
    assert persist_calls[0][1] == default_state


def test_render_auto_backtest_view_aborts_on_start_state_write_failure(
    monkeypatch: pytest.MonkeyPatch,
):
    class _SidebarStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    class _ColumnStub:
        def metric(self, *_args, **_kwargs):
            return None

    prices, returns, macro = _sample_market_frames()
    cache_state = view_mod.control_plane.create_default_state()
    errors: list[str] = []

    monkeypatch.setattr(
        view_mod.control_plane,
        "load_cache",
        lambda *_args, **_kwargs: view_mod.control_plane.AutoBacktestCacheLoadResult(
            ok=True,
            reason=None,
            state=cache_state,
        ),
    )
    monkeypatch.setattr(view_mod.st, "sidebar", _SidebarStub())
    monkeypatch.setattr(view_mod.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "slider", lambda *_args, **kwargs: kwargs.get("value", _args[3]))
    monkeypatch.setattr(view_mod.st, "number_input", lambda *_args, **kwargs: kwargs.get("value", 0.0))
    monkeypatch.setattr(view_mod.st, "button", lambda label, **_kwargs: str(label).startswith("🚀 Run Simulation"))
    monkeypatch.setattr(view_mod.st, "columns", lambda _n: [_ColumnStub(), _ColumnStub(), _ColumnStub()])
    monkeypatch.setattr(view_mod.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "error", lambda msg: errors.append(str(msg)))
    monkeypatch.setattr(view_mod.st, "info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        view_mod.control_plane,
        "persist_cache_atomic",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk busy")),
    )

    class _ShouldNotRunStrategy:
        def __init__(self, *args, **kwargs):
            raise AssertionError("strategy should not execute when start-state write fails")

    monkeypatch.setattr(view_mod, "AdaptiveTrendStrategy", _ShouldNotRunStrategy)

    view_mod.render_auto_backtest_view(prices, returns, macro)

    assert any("start-state write failed" in msg for msg in errors)
