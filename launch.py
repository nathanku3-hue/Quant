"""
Terminal Zero launcher with runtime guardrails.

Usage:
    python launch.py
    python launch.py --server.headless true --server.port 8501
    python launch.py --preflight --strict
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys


REQUIRED_MAJOR = 3
REQUIRED_MINOR = 12
REQUIRED_MODULES = (
    "duckdb",
    "numpy",
    "pandas",
    "plotly",
    "pyarrow",
    "scipy",
    "streamlit",
    "yfinance",
)

USAGE = """Terminal Zero launcher

Usage:
    python launch.py
    python launch.py --server.headless true --server.port 8501
    python launch.py --preflight --strict
    python launch.py --preflight --mode planning
"""


def _project_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _venv_python_hint() -> str:
    root = _project_root()
    return os.path.join(root, ".venv", "Scripts", "python.exe")


def _is_in_project_venv() -> bool:
    root = _project_root()
    venv_prefix = os.path.join(root, ".venv")
    exe = os.path.abspath(sys.executable).lower()
    return exe.startswith(os.path.abspath(venv_prefix).lower())


def _check_python_version() -> list[str]:
    errors: list[str] = []
    if (sys.version_info.major, sys.version_info.minor) != (REQUIRED_MAJOR, REQUIRED_MINOR):
        errors.append(
            f"Unsupported Python runtime: {sys.version_info.major}.{sys.version_info.minor}. "
            f"Required: {REQUIRED_MAJOR}.{REQUIRED_MINOR}."
        )
    return errors


def _check_modules() -> list[str]:
    missing = [m for m in REQUIRED_MODULES if importlib.util.find_spec(m) is None]
    if not missing:
        return []
    return [f"Missing required modules: {', '.join(missing)}"]


def _check_venv() -> list[str]:
    if _is_in_project_venv():
        return []
    return [
        "Python executable is not from project .venv.",
        f"Expected launcher runtime: {_venv_python_hint()}",
    ]


def _print_errors(errors: list[str]) -> None:
    print("Environment check failed:")
    for err in errors:
        print(f"- {err}")
    print("")
    print("Fix:")
    print(f"- Use: {_venv_python_hint()} launch.py")
    print("- Or activate .venv before running.")


def _print_usage() -> None:
    print(USAGE.rstrip())


def _is_preflight_request(argv: list[str]) -> bool:
    return "--preflight" in argv or "--preflight-strict" in argv


def _run_preflight(argv: list[str]) -> int:
    from scripts.boot_preflight import main as boot_preflight_main

    preflight_args: list[str] = []
    has_repo_root = False
    strict_alias = False
    for arg in argv:
        if arg == "--preflight":
            continue
        if arg == "--preflight-strict":
            strict_alias = True
            continue
        if arg == "--repo-root" or arg.startswith("--repo-root="):
            has_repo_root = True
        preflight_args.append(arg)
    if not has_repo_root:
        preflight_args = ["--repo-root", _project_root(), *preflight_args]
    if strict_alias:
        preflight_args.extend(["--mode", "strict"])
    return boot_preflight_main(preflight_args)


def main() -> int:
    argv = sys.argv[1:]
    if argv in (["--help"], ["-h"]):
        _print_usage()
        return 0
    if _is_preflight_request(argv):
        checks = []
        checks.extend(_check_python_version())
        checks.extend(_check_venv())
        if checks:
            _print_errors(checks)
            return 1
        return _run_preflight(argv)

    checks = []
    checks.extend(_check_python_version())
    checks.extend(_check_venv())
    checks.extend(_check_modules())
    if checks:
        _print_errors(checks)
        return 1

    cmd = [sys.executable, "-m", "streamlit", "run", "dashboard.py", *argv]
    return subprocess.call(cmd, cwd=_project_root())


if __name__ == "__main__":
    raise SystemExit(main())
