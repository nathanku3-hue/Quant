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


def test_render_auto_backtest_view_calls_baseline_export_wrapper(
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Phase 33A Step 7: Verify UI backtest calls run_backtest_with_baseline_export.

    Contract: Dashboard-triggered backtests must update baseline pointer automatically.
    """
    class _SidebarStub:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    class _ColumnStub:
        def metric(self, *_args, **_kwargs):
            return None

    class _SpinnerStub:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    prices, returns, macro = _sample_market_frames()
    cache_state = view_mod.control_plane.create_default_state()
    engine_calls: list[str] = []

    # Mock strategy
    class _MockStrategy:
        def __init__(self, *args, **kwargs):
            pass
        def generate_weights(self, *args, **kwargs):
            idx = pd.to_datetime(["2026-03-05", "2026-03-06"])
            weights = pd.DataFrame({101: [0.5, 0.5]}, index=idx)
            regime = pd.Series([1, 1], index=idx)
            details = {
                "status": "ACTIVE",
                "multiplier": 1.0,
                "reason": "Test",
                "color": "#00ff00",
            }
            return weights, regime, details

    # Mock engine wrapper (Phase 33A Step 7 critical path)
    def _mock_baseline_export(*args, **kwargs):
        engine_calls.append("run_backtest_with_baseline_export")
        idx = pd.to_datetime(["2026-03-05", "2026-03-06"])
        results = pd.DataFrame({
            "gross_ret": [0.01, 0.01],
            "net_ret": [0.009, 0.009],
            "turnover": [0.1, 0.1],
            "cost": [0.001, 0.001],
        }, index=idx)
        from core.baseline_registry import BacktestBaseline
        baseline = BacktestBaseline(
            baseline_id="test123",
            strategy_name="test",
            strategy_version="1.0.0",
            config_hash="abc",
            data_snapshot_hash="def",
            calendar_version="NYSE_2026",
            execution_timestamp=pd.Timestamp("2026-03-05"),
            run_environment="dev",
            expected_allocation=pd.DataFrame({101: [0.5, 0.5]}, index=idx),
            rebalance_schedule=[idx[0]],
            full_config={},
        )
        return results, baseline

    monkeypatch.setattr(view_mod.control_plane, "load_cache",
        lambda *_args, **_kwargs: view_mod.control_plane.AutoBacktestCacheLoadResult(
            ok=True, reason=None, state=cache_state))
    monkeypatch.setattr(view_mod.st, "sidebar", _SidebarStub())
    monkeypatch.setattr(view_mod.st, "markdown", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "slider", lambda *_args, **kwargs: kwargs.get("value", _args[3]))
    monkeypatch.setattr(view_mod.st, "number_input", lambda *_args, **kwargs: kwargs.get("value", 0.0))
    monkeypatch.setattr(view_mod.st, "button", lambda label, **_kwargs: str(label).startswith("🚀 Run Simulation"))
    monkeypatch.setattr(view_mod.st, "columns", lambda n: [_ColumnStub() for _ in range(n)])
    monkeypatch.setattr(view_mod.st, "caption", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "info", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "spinner", lambda *_args, **_kwargs: _SpinnerStub())
    monkeypatch.setattr(view_mod.st, "success", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "plotly_chart", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod.st, "session_state", {})
    monkeypatch.setattr(view_mod.control_plane, "persist_cache_atomic", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(view_mod, "AdaptiveTrendStrategy", _MockStrategy)
    monkeypatch.setattr(view_mod.engine, "run_backtest_with_baseline_export", _mock_baseline_export)

    view_mod.render_auto_backtest_view(prices, returns, macro)

    # Critical assertion: UI must call baseline export wrapper, not raw run_simulation
    assert "run_backtest_with_baseline_export" in engine_calls, \
        "UI backtest must call run_backtest_with_baseline_export to update baseline pointer"
