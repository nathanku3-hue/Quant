"""Characterize the existing operated-portfolio engine at 50 and 100 securities.

This is a diagnostic harness, not a new engine or a Universe acceptance path. It
runs the existing domain flow in fresh child processes, measures externally
where practical, probes the existing persistence boundary, and reports findings
without repairing them.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated import (
    admit_no_change_observation,
    append_non_economic_correction,
    authorize_portfolio_transition,
    build_draft_workspace,
    confirm_initial_portfolio,
    validate_workspace,
)
from gv_portfolio_v0.operated_scenarios import (
    ENGINE_SCALE_100_SCENARIO_ID,
    ENGINE_SCALE_50_SCENARIO_ID,
    get_scenario,
    scenario_hash,
)
from gv_portfolio_v0.operated_storage import ensure_workspace

SCENARIO_IDS = {
    50: ENGINE_SCALE_50_SCENARIO_ID,
    100: ENGINE_SCALE_100_SCENARIO_ID,
}


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_document_bytes(value)).hexdigest()


def _timestamp_issues(value: Any, path: str = "root") -> list[str]:
    from datetime import datetime

    issues: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str) and (
                key.endswith("_at")
                or key in {"observed_at", "effective_at", "created_at"}
            ):
                try:
                    datetime.fromisoformat(child.replace("Z", "+00:00"))
                except ValueError:
                    issues.append(f"{child_path}={child}")
            else:
                issues.extend(_timestamp_issues(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_timestamp_issues(child, f"{path}[{index}]"))
    return issues


def _run_domain_flow(size: int, output_path: Path) -> None:
    scenario_id = SCENARIO_IDS[size]
    started = time.perf_counter()
    stage_seconds: dict[str, float] = {}
    result: dict[str, Any] = {
        "size": size,
        "scenario_id": scenario_id,
        "exceptions": [],
    }
    try:
        stage_started = time.perf_counter()
        draft = build_draft_workspace(scenario_id)
        stage_seconds["draft"] = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        funded = confirm_initial_portfolio(draft)
        stage_seconds["confirm"] = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        observed = admit_no_change_observation(funded)
        stage_seconds["no_change"] = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        transitioned = authorize_portfolio_transition(observed)
        stage_seconds["transition"] = time.perf_counter() - stage_started

        stage_started = time.perf_counter()
        corrected = append_non_economic_correction(transitioned)
        stage_seconds["correction"] = time.perf_counter() - stage_started
        validate_workspace(corrected)

        persistence_root = (
            Path(tempfile.gettempdir())
            / f"gv-p1-scale-{size}-{uuid.uuid4().hex}"
        )
        persistence_started = time.perf_counter()
        persistence_error: str | None = None
        try:
            ensure_workspace(root=persistence_root, scenario_id=scenario_id)
        except Exception as exc:  # diagnostic boundary capture
            persistence_error = f"{type(exc).__name__}:{exc}"
        persistence_seconds = time.perf_counter() - persistence_started

        result.update(
            {
                "status": corrected["status"],
                "instrument_count": len(corrected["instruments"]),
                "funded_position_count": len(
                    [
                        row
                        for row in corrected["book"]["positions"]
                        if int(row["quantity"])
                    ]
                ),
                "event_count": len(corrected["events"]),
                "order_count": len(corrected["orders"]),
                "fill_count": len(corrected["fills"]),
                "unexplained_residual": corrected["book"][
                    "unexplained_residual"
                ],
                "nav": corrected["book"]["nav"],
                "book_hash": corrected["book"]["book_hash"],
                "canonical_state_hash": _canonical_sha(corrected),
                "canonical_event_hash": _canonical_sha(corrected["events"]),
                "scenario_hash": scenario_hash(get_scenario(scenario_id)),
                "certification_history_depth": len(
                    corrected["certification_history"]
                ),
                "timestamp_issues": _timestamp_issues(corrected),
                "stage_seconds": stage_seconds,
                "persistence_probe_seconds": persistence_seconds,
                "persistence_error": persistence_error,
                "persistence_supported": persistence_error is None,
                "domain_transition_steps": 4,
                "operator_path_executable": persistence_error is None,
                "per_security_confirmation_contract": 0,
            }
        )
    except Exception as exc:  # diagnostic evidence, not repair
        result["exceptions"].append(f"{type(exc).__name__}:{exc}")
    result["wall_clock_seconds"] = time.perf_counter() - started
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True), encoding="utf-8"
    )


class _ProcessMemoryCounters(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def _windows_peak_working_set(pid: int) -> int:
    if sys.platform != "win32":
        return 0
    handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return 0
    try:
        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            handle, ctypes.byref(counters), counters.cb
        )
        return int(counters.PeakWorkingSetSize) if ok else 0
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _linux_peak_working_set(pid: int) -> int:
    status_path = Path(f"/proc/{pid}/status")
    if not status_path.is_file():
        return 0
    for line in status_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmHWM:"):
            return int(line.split()[1]) * 1024
    return 0


def _peak_working_set(pid: int) -> int:
    if sys.platform == "win32":
        return _windows_peak_working_set(pid)
    if sys.platform.startswith("linux"):
        return _linux_peak_working_set(pid)
    return 0


def _run_fresh_process(size: int) -> dict[str, Any]:
    output_path = (
        Path(tempfile.gettempdir())
        / f"gv-p1-characterization-{size}-{uuid.uuid4().hex}.json"
    )
    process = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child-size",
            str(size),
            "--child-output",
            str(output_path),
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    observed_peak = 0
    while process.poll() is None:
        observed_peak = max(observed_peak, _peak_working_set(process.pid))
        time.sleep(0.01)
    stdout, stderr = process.communicate()
    if not output_path.is_file():
        return {
            "size": size,
            "returncode": process.returncode,
            "peak_working_set_bytes": observed_peak,
            "exceptions": ["RESULT_FILE_MISSING"],
            "stdout_tail": stdout[-2000:],
            "stderr_tail": stderr[-2000:],
        }
    result = json.loads(output_path.read_text(encoding="utf-8"))
    output_path.unlink(missing_ok=True)
    result.update(
        {
            "returncode": process.returncode,
            "peak_working_set_bytes": observed_peak,
            "stdout_tail": stdout[-2000:],
            "stderr_tail": stderr[-2000:],
        }
    )
    return result


def characterize(size: int, runs: int = 2) -> dict[str, Any]:
    observations = [_run_fresh_process(size) for _ in range(runs)]
    first = observations[0]
    repeat_equality = {
        "canonical_state_hash_equal": all(
            row.get("canonical_state_hash")
            == first.get("canonical_state_hash")
            for row in observations
        ),
        "canonical_event_hash_equal": all(
            row.get("canonical_event_hash")
            == first.get("canonical_event_hash")
            for row in observations
        ),
        "book_hash_equal": all(
            row.get("book_hash") == first.get("book_hash")
            for row in observations
        ),
        "scenario_hash_equal": all(
            row.get("scenario_hash") == first.get("scenario_hash")
            for row in observations
        ),
    }
    acceptance = {
        "in_memory_operation_complete": all(
            row.get("status") == "CORRECTED_CERTIFIED"
            for row in observations
        ),
        "fresh_process_hash_equality": all(repeat_equality.values()),
        "zero_unexplained_residual": all(
            row.get("unexplained_residual") == "0"
            for row in observations
        ),
        "valid_timestamps": all(
            not row.get("timestamp_issues") for row in observations
        ),
        "persistence_and_reopen_supported": all(
            row.get("persistence_supported") for row in observations
        ),
        "operator_path_executable": all(
            row.get("operator_path_executable") for row in observations
        ),
        "no_exceptions": all(
            not row.get("exceptions") and row.get("returncode") == 0
            for row in observations
        ),
    }
    return {
        "characterization": f"{size}-security synthetic existing-engine stress",
        "claim_boundary": (
            "Diagnostic only; not Universe acceptance, historical membership "
            "custody, challenger evidence, or live authority."
        ),
        "runs": observations,
        "repeat_equality": repeat_equality,
        "acceptance": acceptance,
        "verdict": "PASS" if all(acceptance.values()) else "FINDING",
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="+", type=int, default=[50, 100])
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child-size", type=int)
    parser.add_argument("--child-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.child_size is not None:
        if args.child_output is None:
            raise SystemExit("--child-output is required with --child-size")
        _run_domain_flow(args.child_size, args.child_output)
        return 0

    invalid_sizes = sorted(set(args.sizes) - set(SCENARIO_IDS))
    if invalid_sizes:
        raise SystemExit(f"unsupported sizes: {invalid_sizes}")
    report = {
        "schema_version": "gv_engine_scale_characterization_v1",
        "results": [characterize(size, runs=args.runs) for size in args.sizes],
    }
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
