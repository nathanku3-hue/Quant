from __future__ import annotations

import os
from pathlib import Path

from utils.process import pid_is_running


def test_pid_is_running_rejects_invalid_values() -> None:
    assert not pid_is_running(0)
    assert not pid_is_running(-1)
    assert not pid_is_running("not-a-pid")


def test_pid_is_running_detects_current_process() -> None:
    assert pid_is_running(os.getpid())


def test_runtime_lock_callers_do_not_use_unsafe_pid_probe() -> None:
    targets = [
        Path("dashboard.py"),
        Path("data/updater.py"),
        Path("scripts/parameter_sweep.py"),
        Path("scripts/release_controller.py"),
        Path("backtests/optimize_phase16_parameters.py"),
    ]
    forbidden = ("os.kill(pid, 0)", "os.kill(int(pid), 0)")
    for target in targets:
        source = target.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{target} still uses unsafe PID probe: {token}"


def test_dashboard_backtest_spawn_does_not_terminate_pid_file_owner() -> None:
    source = Path("dashboard.py").read_text(encoding="utf-8")
    start = source.index("def spawn_backtest(")
    next_def = source.index("\ndef ", start + 1)
    spawn_source = source[start:next_def]

    assert "os.kill(" not in spawn_source
    assert "signal.SIGTERM" not in spawn_source
    assert "Backtest already running" in spawn_source
    assert "refusing to spawn another" in spawn_source
