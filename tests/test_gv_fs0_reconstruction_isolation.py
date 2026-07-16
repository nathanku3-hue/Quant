from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from core.gv_fs0_canonical import (
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "validation/gv_fs0_reconstruction.py").resolve()


def _payload(action: str = "OPEN") -> dict:
    events = []
    if action == "OPEN":
        events = [
            {
                "event_id": "EXECUTION:1",
                "event_type": "EXECUTION",
                "fee": "1",
                "price": "10",
                "security_id": "SEC_1",
                "session": "2026-07-14",
                "shares": 10,
            },
            {
                "amount_per_share": "0.5",
                "event_id": "DIVIDEND:EX_1",
                "event_type": "DIVIDEND_EX",
                "pay_session": "2026-07-16",
                "security_id": "SEC_1",
                "session": "2026-07-15",
            },
            {
                "entitlement_event_id": "DIVIDEND:EX_1",
                "event_id": "DIVIDEND:PAY_1",
                "event_type": "DIVIDEND_PAY",
                "security_id": "SEC_1",
                "session": "2026-07-16",
            },
        ]
    return {
        "decision": {
            "action": action,
            "authority": "MANUAL_OWNER_PAPER",
            "decision_id": f"DECISION_{action}",
            "decision_timestamp": "2026-07-12T00:00:00.000000Z",
            "rationale_reference": f"RATIONALE:{action}",
            "security_id": "SEC_1",
        },
        "events": events,
        "prices": [
            {"close": "10", "security_id": "SEC_1", "session": "2026-07-13"},
            {"close": "11", "security_id": "SEC_1", "session": "2026-07-14"},
            {"close": "12", "security_id": "SEC_1", "session": "2026-07-15"},
            {"close": "13", "security_id": "SEC_1", "session": "2026-07-16"},
            {"close": "14", "security_id": "SEC_1", "session": "2026-07-17"},
        ],
        "protocol": {
            "currency": "USD",
            "fixture_id": f"FIXTURE_{action}",
            "initial_cash": "1000",
            "protocol_id": "GV_FS0_PROTOCOL_V1",
        },
        "schema_version": "GV_FS0_RECON_INPUT_V1",
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


def test_exact_duplicate_events_are_idempotent(tmp_path: Path) -> None:
    payload = _payload()
    payload["events"].insert(1, copy.deepcopy(payload["events"][0]))
    duplicate = _success(_run(tmp_path, payload))
    baseline = _success(_run(tmp_path, _payload()))
    assert duplicate["economic_payload"] == baseline["economic_payload"]


def test_conflicting_duplicate_event_blocks(tmp_path: Path) -> None:
    payload = _payload()
    conflict = copy.deepcopy(payload["events"][0])
    conflict["shares"] = 11
    payload["events"].insert(1, conflict)
    failure = _failure(_run(tmp_path, payload))
    assert failure["failure_reasons"] == ["CONFLICTING_DUPLICATE_EVENT"]


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
    payload["events"][0]["shares"] = 1000
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
