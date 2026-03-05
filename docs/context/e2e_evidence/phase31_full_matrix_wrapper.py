from __future__ import annotations

import contextlib
import os
import signal
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(r"E:\code\quant")
LOG_PATH = ROOT / r"docs\context\e2e_evidence\phase31_full_matrix_final.log"
STATUS_PATH = ROOT / r"docs\context\e2e_evidence\phase31_full_matrix_final.status"
BASE_TEMP_ROOT = Path(tempfile.gettempdir()) / "quant_pytest_runs"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_log(line: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def write_status(code: int) -> None:
    STATUS_PATH.write_text(f"{code}\n", encoding="ascii")


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASE_TEMP_ROOT.mkdir(parents=True, exist_ok=True)

    if STATUS_PATH.exists():
        STATUS_PATH.unlink()

    LOG_PATH.write_text(f"[phase31_full_matrix] start {now_iso()}\n", encoding="utf-8")

    exit_code = 1
    try:
        # Ignore Ctrl+C-style interrupts so external orchestration signals do
        # not abort the in-process pytest run.
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        pytest_args = [
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(BASE_TEMP_ROOT / f"run_{os.getpid()}_{int(time.time() * 1000)}"),
        ]
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as sink:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                os.chdir(ROOT)
                exit_code = int(pytest.main(pytest_args))
    except Exception as exc:  # noqa: BLE001
        append_log(f"[wrapper_exception] {exc!r}")
        exit_code = 1
    finally:
        append_log(f"[phase31_full_matrix] end exit_code={exit_code} {now_iso()}")
        write_status(exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
