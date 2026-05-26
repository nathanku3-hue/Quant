from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data_readiness_gate import DEFAULT_STATUS_PATH
from core.data_readiness_gate import run_data_readiness_gate
from core.data_readiness_gate import status_json_text
from core.data_readiness_gate import write_boot_status


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Terminal Zero Data Readiness Gate v0.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--mode", choices=("planning", "strict"), default="strict")
    parser.add_argument("--planning", dest="mode", action="store_const", const="planning")
    parser.add_argument("--strict", dest="mode", action="store_const", const="strict")
    parser.add_argument("--write-status", action="store_true")
    parser.add_argument("--status-out", type=Path, default=DEFAULT_STATUS_PATH)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    status = run_data_readiness_gate(args.repo_root, mode=args.mode)
    if args.write_status:
        if status["overall_status"] != "PASS":
            status["status_write"] = "blocked-until-pass"
            print(status_json_text(status), end="")
            return 1
        status["status_write"] = write_boot_status(args.status_out, status, repo_root=args.repo_root)
    print(status_json_text(status), end="")
    return 1 if status["overall_status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
