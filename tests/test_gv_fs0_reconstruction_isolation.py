from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from core.gv_fs0_canonical import (
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "validation/gv_fs0_reconstruction.py").resolve()


def _intent(
    intent_type: str,
    sequence: int,
    *,
    session: str,
    security_id: str = "SEC_1",
    quantity: int | None = None,
    execution_price: str | None = None,
    fee: str | None = None,
    dividend_amount_per_share: str | None = None,
    referenced_entitlement_source_intent_id: str | None = None,
    valuation_timestamp: str | None = None,
    effective_timestamp: str | None = None,
) -> dict:
    stamp = effective_timestamp or f"{session}T14:30:00.000000Z"
    return {
        "schema_version": "gv_fs0_source_intent_v1",
        "source_intent_id": f"{intent_type}:{sequence}",
        "source_sequence": sequence,
        "intent_type": intent_type,
        "effective_timestamp": stamp,
        "session": session,
        "security_id": security_id,
        "quantity": quantity,
        "execution_price": execution_price,
        "fee": fee,
        "dividend_amount_per_share": dividend_amount_per_share,
        "referenced_entitlement_source_intent_id": referenced_entitlement_source_intent_id,
        "valuation_timestamp": valuation_timestamp,
    }


def _prices() -> list[dict]:
    rows = [
        ("2026-07-13", "10", 0),
        ("2026-07-14", "11", 1),
        ("2026-07-15", "12", 2),
        ("2026-07-16", "13", 3),
        ("2026-07-17", "14", 4),
    ]
    return [
        {
            "security_id": "SEC_1",
            "session": session,
            "price_timestamp": f"{session}T20:00:00.000000Z",
            "close_price": close,
            "source_sequence": sequence,
        }
        for session, close, sequence in rows
    ]


def _payload(action: str = "OPEN") -> dict:
    if action == "OPEN":
        intents = [
            _intent(
                "EXECUTION_INTENT",
                0,
                session="2026-07-14",
                quantity=10,
                execution_price="10",
            ),
            _intent("EXPLICIT_FEE", 1, session="2026-07-14", fee="1"),
            _intent(
                "DIVIDEND_DECLARATION",
                2,
                session="2026-07-15",
                dividend_amount_per_share="0.5",
            ),
            _intent(
                "DIVIDEND_PAYMENT_INSTRUCTION",
                3,
                session="2026-07-16",
                referenced_entitlement_source_intent_id="DIVIDEND_DECLARATION:2",
            ),
            _intent(
                "VALUATION_INSTRUCTION",
                4,
                session="2026-07-17",
                valuation_timestamp="2026-07-17T20:00:00.000000Z",
                effective_timestamp="2026-07-17T20:00:00.000000Z",
            ),
        ]
    else:
        intents = [
            _intent(
                "VALUATION_INSTRUCTION",
                sequence,
                session=session,
                valuation_timestamp=f"{session}T20:00:00.000000Z",
                effective_timestamp=f"{session}T20:00:00.000000Z",
            )
            for sequence, session in enumerate(
                ["2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17"]
            )
        ]
    return {
        "schema_version": "gv_fs0_verifier_input_v1",
        "protocol": {
            "protocol_id": "GV_FS0_PROTOCOL_V1",
            "fixture_id": f"FIXTURE_{action}",
            "fixture_hash": "a" * 64,
            "currency": "USD",
            "initial_cash": "1000",
        },
        "decision": {
            "decision_id": f"DECISION_{action}",
            "decision_hash": "b" * 64,
            "authority": "MANUAL_OWNER_PAPER",
            "action": action,
            "decision_timestamp": "2026-07-12T00:00:00.000000Z",
            "effective_timestamp": "2026-07-12T00:00:00.000000Z",
            "security_id": "SEC_1",
            "requested_sizing": {"quantity": 10 if action == "OPEN" else None},
            "rationale_reference": f"RATIONALE:{action}",
        },
        "source_prices": _prices(),
        "source_intents": intents,
    }


def _run(tmp_path: Path, payload: dict, *, raw: bytes | None = None, isolated: bool = True, env: dict[str, str] | None = None):
    input_path = (tmp_path / "input.json").resolve()
    input_path.write_bytes(canonical_document_bytes(payload) if raw is None else raw)
    command = [sys.executable]
    if isolated:
        command += ["-I", "-X", "utf8"]
    command += [str(SCRIPT), "--input", str(input_path)]
    return subprocess.run(command, capture_output=True, check=False, env=env)


def _success(result: subprocess.CompletedProcess[bytes]) -> dict:
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stderr == b""
    return parse_canonical_document_bytes(result.stdout)


def _failure(result: subprocess.CompletedProcess[bytes]) -> dict:
    assert result.returncode == 2
    assert result.stdout == b""
    return parse_canonical_document_bytes(result.stderr)


def test_open_reconstruction_preserves_reviewed_synthetic_economics(tmp_path: Path) -> None:
    output = _success(_run(tmp_path, _payload("OPEN")))
    economic = output["economic_payload"]
    assert economic["total_costs"] == "1"
    assert economic["sessions"][1] == {
        "cash": "899",
        "contribution": "9",
        "market_value": "110",
        "nav": "1009",
        "receivables": "0",
        "session": "2026-07-14",
        "shares": 10,
    }
    assert economic["sessions"][2]["receivables"] == "5"
    assert economic["sessions"][3]["cash"] == "904"
    assert economic["final_state"]["nav"] == "1044"
    assert output["protocol_compat_version"] == "GV_FS0_PROTOCOL_V1_1_VERIFIER_IO"
    assert output["reconstruction_engine"] == "GV_FS0_STDLIB_ISOLATED_V1_1"


def test_no_position_preserves_all_cash_with_zero_events(tmp_path: Path) -> None:
    output = _success(_run(tmp_path, _payload("NO_POSITION")))
    economic = output["economic_payload"]
    assert economic["action"] == "NO_POSITION"
    assert all(row["shares"] == 0 for row in economic["sessions"])
    assert all(row["cash"] == "1000" for row in economic["sessions"])
    assert all(row["nav"] == "1000" for row in economic["sessions"])


def test_hashes_use_v1_domain_separation_and_terminal_lf_input(tmp_path: Path) -> None:
    payload = _payload()
    output = _success(_run(tmp_path, payload))
    assert output["input_hash"] == domain_hash("GV-FS0:VERIFIER_INPUT:V1", payload)
    assert output["canonical_payload_hash"] == domain_hash(
        "GV-FS0:ECONOMIC_PAYLOAD:V1", output["economic_payload"]
    )
    result_without_hash = {key: value for key, value in output.items() if key != "verifier_result_hash"}
    assert output["verifier_result_hash"] == domain_hash("GV-FS0:VERIFIER_RESULT:V1", result_without_hash)


def test_two_runs_produce_identical_stdout_bytes(tmp_path: Path) -> None:
    payload = _payload()
    first = _run(tmp_path, payload)
    second = _run(tmp_path, payload)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_exact_duplicate_intents_are_idempotent(tmp_path: Path) -> None:
    payload = _payload()
    payload["source_intents"].insert(1, copy.deepcopy(payload["source_intents"][0]))
    duplicate = _success(_run(tmp_path, payload))
    baseline = _success(_run(tmp_path, _payload()))
    assert duplicate["economic_payload"] == baseline["economic_payload"]


def test_conflicting_duplicate_intent_blocks(tmp_path: Path) -> None:
    payload = _payload()
    conflict = copy.deepcopy(payload["source_intents"][0])
    conflict["quantity"] = 11
    payload["source_intents"].insert(1, conflict)
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["CONFLICTING_DUPLICATE_EVENT"]


def test_legacy_prices_events_input_is_rejected(tmp_path: Path) -> None:
    payload = {
        "schema_version": "GV_FS0_RECON_INPUT_V1",
        "protocol": {
            "protocol_id": "GV_FS0_PROTOCOL_V1",
            "fixture_id": "FIXTURE_OPEN",
            "currency": "USD",
            "initial_cash": "1000",
        },
        "decision": {
            "decision_id": "DECISION_OPEN",
            "authority": "MANUAL_OWNER_PAPER",
            "action": "OPEN",
            "security_id": "SEC_1",
            "decision_timestamp": "2026-07-12T00:00:00.000000Z",
            "rationale_reference": "RATIONALE:OPEN",
        },
        "prices": [{"close": "10", "security_id": "SEC_1", "session": "2026-07-13"}],
        "events": [],
    }
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["LEGACY_VERIFIER_INPUT_PROHIBITED"]


def test_noncanonical_input_whitespace_blocks(tmp_path: Path) -> None:
    payload = _payload()
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    failure = _failure(_run(tmp_path, payload, raw=raw))
    assert failure["failure_reasons"] == ["INPUT_NOT_CANONICAL"]


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b'{"schema_version":1.0}\n', "JSON_FLOAT_PROHIBITED"),
        (b'{"schema_version":01}\n', "INTEGER_TOKEN_INVALID"),
        (b'{"a":0,"a":1}\n', "DUPLICATE_JSON_KEY"),
        (b'\xef\xbb\xbf{}\n', "UTF8_BOM_PROHIBITED"),
        (b'{}\r\n', "TERMINAL_NEWLINE_COUNT_INVALID"),
        (b'{}\n\n', "TERMINAL_NEWLINE_COUNT_INVALID"),
    ],
)
def test_invalid_input_bytes_block_before_economics(tmp_path: Path, raw: bytes, code: str) -> None:
    failure = _failure(_run(tmp_path, _payload(), raw=raw))
    assert failure["failure_reasons"] == [code]


def test_unknown_input_field_blocks_fail_closed(tmp_path: Path) -> None:
    payload = _payload()
    payload["unknown"] = "forbidden"
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["SCHEMA_KEYS_INVALID"]


def test_negative_cash_blocks(tmp_path: Path) -> None:
    payload = _payload()
    payload["source_intents"][0]["quantity"] = 1000
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["NEGATIVE_CASH_BLOCKED"]


def test_nonisolated_execution_refuses_to_run(tmp_path: Path) -> None:
    failure = _failure(_run(tmp_path, _payload(), isolated=False))
    assert failure["failure_reasons"] == ["ISOLATED_UTF8_MODE_REQUIRED"]


def test_module_cannot_be_imported_in_process() -> None:
    result = subprocess.run(
        [sys.executable, "-c", f"import runpy; runpy.run_path({str(SCRIPT)!r})"],
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert b"GV_FS0_RECONSTRUCTION_PROCESS_ONLY" in result.stderr


def test_isolated_process_ignores_hostile_pythonpath(tmp_path: Path) -> None:
    hostile = tmp_path / "hostile"
    hostile.mkdir()
    (hostile / "sitecustomize.py").write_text("raise RuntimeError('loaded hostile sitecustomize')", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(hostile)
    output = _success(_run(tmp_path, _payload(), env=env))
    assert output["isolation"]["python_isolated_mode"] is True
    assert output["isolation"]["legacy_prices_events"] == "PROHIBITED"


def test_ast_is_standard_library_only_and_has_no_import_escape_hatches() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed = {
        "argparse",
        "datetime",
        "decimal",
        "hashlib",
        "json",
        "pathlib",
        "re",
        "sys",
        "unicodedata",
        "typing",
        "__future__",
    }
    imports: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                calls.add(node.func.attr)
    assert imports <= allowed
    assert not ({"__import__", "import_module", "exec", "eval", "compile"} & calls)
    assert "sys.path" not in source
    assert "strategies" not in source
    assert "core.gv_fs0" not in source


def test_stdout_is_exactly_one_canonical_json_document(tmp_path: Path) -> None:
    result = _run(tmp_path, _payload())
    assert result.stdout.endswith(b"\n")
    assert not result.stdout.endswith(b"\n\n")
    assert b"\r" not in result.stdout
    assert canonical_document_bytes(parse_canonical_document_bytes(result.stdout)) == result.stdout


@pytest.mark.parametrize(
    ("field_path", "value", "code"),
    [
        (("decision", "decision_timestamp"), "2026-07-12T00:00:00Z", "TIMESTAMP_SHAPE_INVALID"),
        (("decision", "effective_timestamp"), "2026-07-12T00:00:00.000000+00:00", "TIMESTAMP_SHAPE_INVALID"),
        (("source_prices", 0, "session"), "20260713", "SESSION_DATE_INVALID"),
        (("decision", "decision_id"), "A" * 193, "IDENTITY_TOKEN_INVALID"),
        (("decision", "decision_id"), "e\u0301", "IDENTITY_TOKEN_INVALID"),
        (("protocol", "initial_cash"), "1000.0000001", "DECIMAL_EXCESS_PRECISION"),
    ],
)
def test_exact_contract_shapes_reject_permissive_variants(
    tmp_path: Path,
    field_path: tuple[object, ...],
    value: object,
    code: str,
) -> None:
    payload = _payload()
    cursor: object = payload
    for part in field_path[:-1]:
        cursor = cursor[part]  # type: ignore[index]
    cursor[field_path[-1]] = value  # type: ignore[index]
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == [code]


def test_input_byte_limit_blocks_before_json_parse(tmp_path: Path) -> None:
    raw = b"{" + (b" " * 1_048_576) + b"}\n"
    failure = _failure(_run(tmp_path, _payload(), raw=raw))
    assert failure["failure_reasons"] == ["INPUT_BYTE_LIMIT_EXCEEDED"]


def test_json_depth_limit_blocks_before_host_parser(tmp_path: Path) -> None:
    raw = (b"[" * 33) + b"0" + (b"]" * 33) + b"\n"
    failure = _failure(_run(tmp_path, _payload(), raw=raw))
    assert failure["failure_reasons"] == ["JSON_DEPTH_LIMIT_EXCEEDED"]


def test_source_intent_count_limit_blocks(tmp_path: Path) -> None:
    payload = _payload("NO_POSITION")
    payload["source_intents"] = [
        _intent(
            "VALUATION_INSTRUCTION",
            index,
            session="2026-07-13",
            valuation_timestamp="2026-07-13T20:00:00.000000Z",
            effective_timestamp="2026-07-13T20:00:00.000000Z",
        )
        for index in range(65)
    ]
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["SOURCE_INTENT_COUNT_LIMIT_EXCEEDED"]


def _process_rss_bytes(pid: int) -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessMemoryCounters(ctypes.Structure):
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

        handle = ctypes.windll.kernel32.OpenProcess(0x1010, False, pid)
        if not handle:
            return None
        try:
            counters = ProcessMemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            ok = ctypes.windll.psapi.GetProcessMemoryInfo(
                handle,
                ctypes.byref(counters),
                counters.cb,
            )
            return int(counters.PeakWorkingSetSize) if ok else None
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    status = Path(f"/proc/{pid}/status")
    try:
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


def test_fs0_process_budgets_and_repeatability(tmp_path: Path) -> None:
    input_path = (tmp_path / "budget-input.json").resolve()
    input_bytes = canonical_document_bytes(_payload())
    input_path.write_bytes(input_bytes)
    command = [sys.executable, "-I", "-X", "utf8", str(SCRIPT), "--input", str(input_path)]
    started = time.perf_counter()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    peak_rss = 0
    while process.poll() is None:
        observed = _process_rss_bytes(process.pid)
        if observed is not None:
            peak_rss = max(peak_rss, observed)
        time.sleep(0.002)
    stdout, stderr = process.communicate()
    elapsed = time.perf_counter() - started
    assert process.returncode == 0, stderr.decode("utf-8", errors="replace")
    assert elapsed < 5.0
    assert len(input_bytes) <= 1_048_576
    assert len(stdout) <= 1_048_576
    if peak_rss:
        assert peak_rss <= 134_217_728
    second = subprocess.run(command, capture_output=True, check=False)
    assert second.returncode == 0
    assert second.stdout == stdout
