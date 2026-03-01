from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_regime_fidelity_allow_missing_returns_default_false(monkeypatch):
    mod = _load_module(ROOT / "scripts" / "regime_fidelity_sprint.py", "regime_fidelity_sprint_cli")
    monkeypatch.setattr(sys, "argv", ["regime_fidelity_sprint.py"])
    args = mod.parse_args()
    assert args.allow_missing_returns is False


def test_phase21_stop_impact_allow_missing_returns_default_false(monkeypatch):
    mod = _load_module(ROOT / "scripts" / "phase21_day1_stop_impact.py", "phase21_day1_stop_impact_cli")
    monkeypatch.setattr(sys, "argv", ["phase21_day1_stop_impact.py"])
    args = mod.parse_args()
    assert args.allow_missing_returns is False


def test_phase20_full_backtest_allow_missing_returns_default_false(monkeypatch):
    mod = _load_module(ROOT / "scripts" / "phase20_full_backtest.py", "phase20_full_backtest_cli")
    monkeypatch.setattr(sys, "argv", ["phase20_full_backtest.py"])
    args = mod.parse_args()
    assert args.allow_missing_returns is False
