"""Broker-free Alpha launcher.

Usage:
    python launch_alpha.py
    python launch_alpha.py --server.headless true --server.port 8502

Does not import dashboard, broker, or trading SDK. Does not load broker env vars.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from core.gv_alpha0_ship_runtime import (
    GvAlpha0ShipRuntimeError,
    RUNTIME_HOME_ENV,
    prepare_runtime_workspace,
)

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12
# Alpha surface needs Streamlit only — no alpaca/yfinance/broker.
REQUIRED_MODULES = ("streamlit",)

ROOT = Path(__file__).resolve().parent
APP = ROOT / "alpha_app.py"

# Broker env names (execution/broker_api.py) — never required for Alpha launch.
BROKER_ENV_KEYS = (
    "APCA_API_KEY_ID",
    "APCA_API_SECRET_KEY",
    "APCA_API_BASE_URL",
    "ALPACA_API_KEY",
    "ALPACA_API_SECRET",
    "ALPACA_BASE_URL",
)


def _check_python() -> None:
    if sys.version_info[:2] < (REQUIRED_MAJOR, REQUIRED_MINOR):
        raise SystemExit(
            f"Python {REQUIRED_MAJOR}.{REQUIRED_MINOR}+ required; "
            f"got {sys.version_info.major}.{sys.version_info.minor}"
        )


def _check_modules() -> None:
    missing = []
    for name in REQUIRED_MODULES:
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        raise SystemExit(f"Missing required modules for Alpha: {', '.join(missing)}")


def _extract_data_dir(args: list[str]) -> tuple[list[str], Path | None]:
    remaining: list[str] = []
    selected: Path | None = None
    index = 0
    while index < len(args):
        value = args[index]
        if value == "--data-dir":
            if selected is not None or index + 1 >= len(args):
                raise SystemExit("--data-dir must be provided exactly once with a path")
            selected = Path(args[index + 1]).expanduser()
            index += 2
            continue
        if value.startswith("--data-dir="):
            if selected is not None or not value.partition("=")[2].strip():
                raise SystemExit("--data-dir must be provided exactly once with a path")
            selected = Path(value.partition("=")[2]).expanduser()
            index += 1
            continue
        remaining.append(value)
        index += 1
    return remaining, selected


def main(argv: list[str] | None = None) -> int:
    _check_python()
    _check_modules()
    if not APP.is_file():
        raise SystemExit(f"alpha_app.py missing at {APP}")

    args, requested_data_dir = _extract_data_dir(
        list(argv if argv is not None else sys.argv[1:])
    )
    try:
        runtime = prepare_runtime_workspace(runtime_root=requested_data_dir)
    except GvAlpha0ShipRuntimeError as exc:
        raise SystemExit(f"GV-ALPHA0 startup diagnostics failed: {exc}") from exc

    # Strip broker env from child process so Alpha never depends on them.
    child_env = {
        k: v for k, v in os.environ.items() if k not in BROKER_ENV_KEYS
    }
    child_env[RUNTIME_HOME_ENV] = str(runtime.root)
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP),
        *args,
    ]
    state = "initialized" if runtime.initialized else "verified"
    print(
        f"launch_alpha: broker-free streamlit {APP.name}; "
        f"workspace={runtime.root}; state={state}",
        flush=True,
    )
    return subprocess.call(cmd, cwd=str(ROOT), env=child_env)


if __name__ == "__main__":
    raise SystemExit(main())
