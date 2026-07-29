"""Launch the GV Portfolio V0 Streamlit workspace."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def main() -> int:
    app = Path(__file__).resolve().with_name("portfolio_app.py")
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app),
        "--server.headless=false",
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
