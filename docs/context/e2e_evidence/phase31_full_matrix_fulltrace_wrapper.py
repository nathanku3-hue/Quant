from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"E:\code\quant")
LOG_PATH = ROOT / r"docs\context\e2e_evidence\phase31_full_matrix_fulltrace.log"
STATUS_PATH = ROOT / r"docs\context\e2e_evidence\phase31_full_matrix_fulltrace.status"
BASE_TEMP = ROOT / ".pytest_tmp_scheduler_fulltrace"
PYTHON_EXE = ROOT / r".venv\Scripts\python.exe"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def append_log(line: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")


def write_status(code: int) -> None:
    STATUS_PATH.write_text(f"{code}\n", encoding="ascii")


def main() -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASE_TEMP.mkdir(parents=True, exist_ok=True)

    if STATUS_PATH.exists():
        STATUS_PATH.unlink()

    LOG_PATH.write_text(f"[phase31_full_matrix_fulltrace] start {now_iso()}\n", encoding="utf-8")

    exit_code = 1
    try:
        cmd = [
            str(PYTHON_EXE),
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(BASE_TEMP),
            "--full-trace",
        ]
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as sink:
            completed = subprocess.run(
                cmd,
                cwd=ROOT,
                stdout=sink,
                stderr=sink,
                check=False,
                env=os.environ.copy(),
            )
        exit_code = int(completed.returncode)
    except Exception as exc:  # noqa: BLE001
        append_log(f"[wrapper_exception] {exc!r}")
        exit_code = 1
    finally:
        append_log(f"[phase31_full_matrix_fulltrace] end exit_code={exit_code} {now_iso()}")
        write_status(exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
