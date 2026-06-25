from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _project_dependencies() -> list[str]:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return [str(dep).lower() for dep in data["project"]["dependencies"]]


def test_main_dependencies_use_alpaca_py_not_legacy_trade_api():
    deps = _project_dependencies()

    assert "alpaca-py==0.43.4" in deps
    assert not any(dep.startswith("alpaca-trade-api") for dep in deps)


def test_requirements_lock_excludes_legacy_alpaca_trade_api():
    lock_text = (ROOT / "requirements.lock").read_text(encoding="utf-8").lower()

    assert "alpaca-py==0.43.4" in lock_text
    assert "alpaca-trade-api" not in lock_text


def test_broker_boundary_does_not_import_legacy_alpaca_sdk():
    broker_source = (ROOT / "execution" / "broker_api.py").read_text(encoding="utf-8").lower()

    assert "alpaca_trade_api" not in broker_source
