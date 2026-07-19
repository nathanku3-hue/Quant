import ast
import hashlib
import json
from pathlib import Path

import pytest

from scripts import pead_m6b_strict_path_a_data_gate as gate


VALIDATION_TIMESTAMP = "2026-06-29T12:00:00Z"
EVIDENCE_TIMESTAMP = "2026-06-29T11:00:00Z"
AS_OF_TIMESTAMP = "2026-06-28T20:00:00Z"
SOURCE_HASH = "a" * 64


def _coverage() -> dict:
    return {
        "numerator": 100,
        "denominator": 100,
        "definition": "all decision-date eligible security observations",
    }


def _component() -> dict:
    return {
        "valid_as_of_decision_date": True,
        "timestamp_utc": AS_OF_TIMESTAMP,
        "as_of_proof": "immutable snapshot timestamp precedes each decision date",
        "decision_timestamp_utc": "2026-06-29T00:00:00Z",
        "decision_timestamp_proof": "portfolio decision ledger timestamp",
        "coverage": _coverage(),
    }


def _gate_record(gate_id: str) -> dict:
    evidence_by_gate = {
        "A": {
            "eps_vintage": "first_public_unrestated",
            "strict_vintage_pit": True,
            "restated_vintage": False,
            "sue_as_of_decision_date": True,
            "release_timing_evidence": "first-public filing release timestamp",
        },
        "B": {
            "security_level_total_return_source": True,
            "tradable_return_source": True,
            "delisting_adjusted_returns": True,
            "delisting_treatment_verified": True,
            "security_date_coverage_verified": True,
            "delisting_treatment_method": "terminal_return_compounded_with_verified_delisting_return",
            "delisting_event_count": 7,
        },
        "C": {
            "decision_date_price": _component(),
            "adv_liquidity": _component(),
            "active_listing_trading_status": _component(),
            "corporate_action_delisting_eligibility": _component(),
            "full_m6_as_of_liquidity_screen": True,
            "screen_enforced_preformation": True,
            "screen_enforced_before_turnover_calculation": True,
            "ineligible_rows_excluded_preformation": True,
            "future_information_used": False,
            "post_event_inputs_used": False,
        },
        "D": {
            "short_availability": _component(),
            "borrow_cost": _component(),
            "testable_contract": True,
            "short_availability_tested": True,
            "borrow_cost_contract_tested": True,
            "daily_short_borrow_bps": 1.0,
            "borrow_fee_threshold_bps": 25.0,
            "borrow_fee_threshold_enforced": True,
            "borrow_fee_threshold_treatment": gate.BORROW_THRESHOLD_TREATMENT,
            "borrow_cost_treatment": gate.BORROW_COST_TREATMENT,
            "borrow_cost_units": "bps_per_day",
            "missing_borrow_fails_closed": True,
            "nonzero_borrow_cost_enforced": True,
            "net_turnover_and_borrow_cost_model_integrated": True,
        },
    }
    return {
        "authorized_in_scope": True,
        "source_hash": SOURCE_HASH,
        "source_identifier": f"verified-source-{gate_id.lower()}",
        "coverage": _coverage(),
        "evidence_timestamp_utc": EVIDENCE_TIMESTAMP,
        "as_of_timestamp_utc": AS_OF_TIMESTAMP,
        "as_of_proof": "source snapshot and decision-date lineage independently checked",
        "gate_specific_evidence": evidence_by_gate[gate_id],
        "validation_checks_performed": [
            "source hash verified",
            "coverage reconciled",
            "as-of lineage verified",
        ],
    }


def _synthetic_payload() -> dict:
    return {
        "validation_context": "synthetic_test",
        "authorized_current_evidence_invocation": False,
        "m6a_engine_ready": True,
        "gates": {gate_id: _gate_record(gate_id) for gate_id in gate.GATE_IDS},
    }


def _current_all_pass_payload() -> dict:
    payload = _synthetic_payload()
    payload["validation_context"] = "current_evidence"
    payload["authorized_current_evidence_invocation"] = True
    return payload


def _write_authorized_current_fixture(
    tmp_path: Path,
    payload: dict | None = None,
) -> tuple[Path, Path, dict[str, Path]]:
    current_payload = payload or _current_all_pass_payload()
    source_paths: dict[str, Path] = {}
    source_dir = tmp_path / "sources"
    source_dir.mkdir()
    for gate_id in gate.GATE_IDS:
        source_path = source_dir / f"gate-{gate_id.lower()}.txt"
        source_path.write_bytes(f"verified gate {gate_id} source\n".encode("utf-8"))
        source_paths[gate_id] = source_path
        current_payload["gates"][gate_id]["source_artifact_path"] = (
            source_path.relative_to(tmp_path).as_posix()
        )
        current_payload["gates"][gate_id]["source_hash"] = hashlib.sha256(
            source_path.read_bytes()
        ).hexdigest()

    evidence_path = tmp_path / "current-evidence.json"
    evidence_path.write_text(
        json.dumps(current_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    authorization = {
        "authorized": True,
        "authorization_id": "AUTH-STRICT-PATH-A-001",
        "round_id": gate.ROUND_ID,
        "scope_id": gate.SCOPE_ID,
        "mode": gate.AUTHORIZATION_MODE,
        "action": gate.AUTHORIZATION_ACTION,
        "authorized_at_utc": "2026-06-29T11:30:00Z",
        "evidence_file_sha256": hashlib.sha256(
            evidence_path.read_bytes()
        ).hexdigest(),
    }
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text(
        json.dumps(authorization, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return evidence_path, authorization_path, source_paths


@pytest.mark.parametrize(
    ("label", "raw_json"),
    [
        ("authorized", '{"authorized": true, "authorized": false}'),
        ("round_id", '{"round_id": "first", "round_id": "second"}'),
        ("scope_id", '{"scope_id": "first", "scope_id": "second"}'),
        (
            "evidence_file_sha256",
            '{"evidence_file_sha256": "a", "evidence_file_sha256": "b"}',
        ),
        ("nested gate", '{"gates": {"A": {}, "A": {}}}'),
        (
            "nested source_hash",
            '{"gates": {"A": {"source_hash": "a", "source_hash": "b"}}}',
        ),
        (
            "nested source_artifact_path",
            (
                '{"gates": {"A": {'
                '"source_artifact_path": "a", '
                '"source_artifact_path": "b"}}}'
            ),
        ),
        (
            "nested gate-specific evidence",
            (
                '{"gates": {"A": {"gate_specific_evidence": {'
                '"eps_vintage": "first", "eps_vintage": "second"}}}}'
            ),
        ),
    ],
)
def test_unambiguous_json_loader_rejects_duplicate_authority_and_evidence_keys(
    tmp_path: Path,
    label: str,
    raw_json: str,
) -> None:
    path = tmp_path / f"duplicate-{label.replace(' ', '-')}.json"
    path.write_text(raw_json, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate JSON key"):
        gate._read_json_object(path)


@pytest.mark.parametrize("duplicate_in", ["evidence", "authorization"])
def test_duplicate_json_cli_input_fails_before_output_or_temp(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    duplicate_in: str,
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(tmp_path)
    output = tmp_path / "readiness.json"
    if duplicate_in == "evidence":
        evidence_path.write_text(
            '{"validation_context": "current_evidence", '
            '"validation_context": "synthetic_test"}',
            encoding="utf-8",
        )
    else:
        authorization_path.write_text(
            '{"authorized": true, "authorized": false}',
            encoding="utf-8",
        )

    rc = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--authorization-file",
            str(authorization_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "duplicate JSON key" in captured.err
    assert not output.exists()
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))


def test_current_local_evidence_is_explicitly_fail_closed() -> None:
    result = gate.validate_evidence(
        gate.build_current_evidence_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert [result["gate_results"][item]["status"] for item in gate.GATE_IDS] == [
        "BLOCKED",
        "BLOCKED",
        "BLOCKED",
        "BLOCKED",
    ]
    assert result["gate_results"]["A"]["restated_eps_exception_authorization"]["status"] == "NOT_AUTHORIZED"
    assert result["workflow_status"] == "blocked_fail_closed"
    assert result["authoritative_current_evidence"] is False
    assert result["current_evidence_authorization"]["status"] == "NOT_AUTHORIZED"
    assert result["m6a_engine_ready"] is True
    assert result["m6b_data_contract_ready"] is False


def test_synthetic_all_pass_proves_logic_without_promoting_readiness() -> None:
    result = gate.validate_evidence(
        _synthetic_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert all(result["gate_results"][item]["status"] == "PASS" for item in gate.GATE_IDS)
    assert result["validation_context"] == "synthetic_test"
    assert result["hypothetical_all_gates_pass"] is True
    assert result["authoritative_current_evidence"] is False
    assert result["m6b_data_contract_ready"] is False
    assert result["workflow_status"] == "synthetic_validation_only"
    for gate_id in gate.GATE_IDS:
        record = result["gate_results"][gate_id]
        for key in (
            "source_hash",
            "source_identifier",
            "coverage",
            "evidence_timestamp_utc",
            "as_of_timestamp_utc",
            "as_of_proof",
            "gate_specific_evidence",
            "validation_checks_performed",
        ):
            assert key in record


def test_synthetic_cli_rejects_authorization_without_output_or_temp(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_path = tmp_path / "synthetic.json"
    evidence_path.write_text(
        json.dumps(_synthetic_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text("{}", encoding="utf-8")
    rejected_output = tmp_path / "rejected.json"

    rejected_rc = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--authorization-file",
            str(authorization_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(rejected_output),
        ]
    )
    rejected_capture = capsys.readouterr()

    assert rejected_rc == 2
    assert rejected_capture.out == ""
    assert "validation_context=synthetic_test" in rejected_capture.err
    assert not rejected_output.exists()
    assert not list(tmp_path.glob(f".{rejected_output.name}.*.tmp"))

    allowed_output = tmp_path / "allowed.json"
    allowed_rc = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(allowed_output),
        ]
    )
    allowed_capture = capsys.readouterr()

    assert allowed_rc == 0
    assert allowed_capture.out.endswith("[status] synthetic_validation_only\n")
    assert allowed_capture.err == ""
    allowed = json.loads(allowed_output.read_text(encoding="utf-8"))
    assert allowed["hypothetical_all_gates_pass"] is True
    assert allowed["m6b_data_contract_ready"] is False
    assert not list(tmp_path.glob(f".{allowed_output.name}.*.tmp"))


def test_synthetic_cli_requires_explicit_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_path = tmp_path / "synthetic.json"
    evidence_path.write_text(
        json.dumps(_synthetic_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    canonical_bytes = gate.OUTPUT_PATH.read_bytes()

    with pytest.raises(SystemExit) as exc_info:
        gate.main(
            [
                "--evidence-file",
                str(evidence_path),
                "--validation-timestamp",
                VALIDATION_TIMESTAMP,
            ]
        )
    missing_capture = capsys.readouterr()

    assert exc_info.value.code == 2
    assert missing_capture.out == ""
    assert "--output" in missing_capture.err
    assert gate.OUTPUT_PATH.read_bytes() == canonical_bytes


def test_synthetic_run_rejects_canonical_output_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_path = tmp_path / "synthetic.json"
    evidence_path.write_text(
        json.dumps(_synthetic_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    canonical_bytes = gate.OUTPUT_PATH.read_bytes()

    rc = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(gate.OUTPUT_PATH),
        ]
    )
    rejected_capture = capsys.readouterr()

    assert rc == 2
    assert rejected_capture.out == ""
    assert "synthetic_test output must not target the canonical" in rejected_capture.err
    assert gate.OUTPUT_PATH.read_bytes() == canonical_bytes


def test_evidence_payload_cannot_self_authorize() -> None:
    payload = _current_all_pass_payload()
    payload.update(
        {
            "authorized_current_evidence_invocation": True,
            "authoritative_current_evidence": True,
            "current_evidence_authorization": {
                "status": "AUTHORIZED",
                "evidence_file_sha256_verified": True,
            },
        }
    )

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["authoritative_current_evidence"] is False
    assert result["authorized_current_evidence_invocation"] is False
    assert result["current_evidence_authorization"]["status"] == "NOT_AUTHORIZED"
    assert result["m6b_data_contract_ready"] is False


def test_unauthorized_structurally_all_pass_current_blocks_every_gate() -> None:
    result = gate.validate_evidence(
        _current_all_pass_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert all(
        result["gate_results"][gate_id]["status"] == "BLOCKED"
        for gate_id in gate.GATE_IDS
    )
    assert all(
        result["gate_results"][gate_id]["source_bytes_sha256_verified"] is False
        for gate_id in gate.GATE_IDS
    )
    for gate_id in gate.GATE_IDS:
        reasons = result["gate_results"][gate_id]["reasons"]
        assert "current_evidence_authorization_not_authorized" in reasons
        assert "current_evidence_source_bytes_not_fully_verified" in reasons
    assert result["m6b_data_contract_ready"] is False


def test_distinct_bound_authorization_and_verified_source_bytes_can_pass(
    tmp_path: Path,
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path
    )

    result = gate.validate_evidence_file(
        evidence_path,
        authorization_file_path=authorization_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )

    assert result["current_evidence_authorization"]["status"] == "AUTHORIZED"
    assert result["authoritative_current_evidence"] is True
    assert all(
        result["gate_results"][gate_id]["source_bytes_sha256_verified"] is True
        for gate_id in gate.GATE_IDS
    )
    assert all(
        result["gate_results"][gate_id]["status"] == "PASS"
        for gate_id in gate.GATE_IDS
    )
    assert result["m6b_data_contract_ready"] is True


def test_authorization_hash_must_bind_exact_evidence_file_bytes(
    tmp_path: Path,
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["evidence_file_sha256"] = "f" * 64
    authorization_path.write_text(
        json.dumps(authorization, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = gate.validate_evidence_file(
        evidence_path,
        authorization_file_path=authorization_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )

    assert result["authoritative_current_evidence"] is False
    assert "authorization_evidence_hash_mismatch" in result[
        "current_evidence_authorization"
    ]["reasons"]
    assert all(
        result["gate_results"][gate_id]["status"] == "BLOCKED"
        for gate_id in gate.GATE_IDS
    )
    assert all(
        result["gate_results"][gate_id]["source_bytes_sha256_verified"] is False
        for gate_id in gate.GATE_IDS
    )
    assert result["m6b_data_contract_ready"] is False


@pytest.mark.parametrize(
    "authorization_text",
    [
        "{",
        json.dumps({"authorized": True}),
    ],
)
def test_malformed_authorization_artifact_or_schema_is_cli_input_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    authorization_text: str,
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path
    )
    authorization_path.write_text(authorization_text, encoding="utf-8")
    output = tmp_path / "readiness.json"

    return_code = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--authorization-file",
            str(authorization_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()

    assert return_code == 2
    assert captured.out == ""
    assert captured.err.startswith("[error] ")
    assert not output.exists()
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))


def test_well_formed_authorization_sha_mismatch_cli_blocks_all_gates(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization["evidence_file_sha256"] = "f" * 64
    authorization_path.write_text(
        json.dumps(authorization, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "readiness.json"

    return_code = gate.main(
        [
            "--evidence-file",
            str(evidence_path),
            "--authorization-file",
            str(authorization_path),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(output),
        ]
    )
    captured = capsys.readouterr()
    result = json.loads(output.read_text(encoding="utf-8"))

    assert return_code == 0
    assert captured.out.endswith("[status] blocked_fail_closed\n")
    assert result["current_evidence_authorization"]["status"] == "NOT_AUTHORIZED"
    assert "authorization_evidence_hash_mismatch" in result[
        "current_evidence_authorization"
    ]["reasons"]
    assert all(
        result["gate_results"][gate_id]["status"] == "BLOCKED"
        for gate_id in gate.GATE_IDS
    )
    assert all(
        result["gate_results"][gate_id]["source_bytes_sha256_verified"] is False
        for gate_id in gate.GATE_IDS
    )
    assert result["m6b_data_contract_ready"] is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("scope_id", "wrong-scope", "authorization_scope_mismatch"),
        ("mode", "wrong-mode", "authorization_mode_mismatch"),
        ("action", "wrong-action", "authorization_action_mismatch"),
    ],
)
def test_authorization_requires_exact_scope_mode_and_action(
    tmp_path: Path,
    field: str,
    value: str,
    reason: str,
) -> None:
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path
    )
    authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
    authorization[field] = value
    authorization_path.write_text(
        json.dumps(authorization, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = gate.validate_evidence_file(
        evidence_path,
        authorization_file_path=authorization_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )

    assert result["authoritative_current_evidence"] is False
    assert reason in result["current_evidence_authorization"]["reasons"]
    assert result["m6b_data_contract_ready"] is False


def test_authorized_current_gate_blocks_when_source_bytes_do_not_match(
    tmp_path: Path,
) -> None:
    evidence_path, authorization_path, source_paths = (
        _write_authorized_current_fixture(tmp_path)
    )
    source_paths["B"].write_bytes(b"tampered after evidence declaration\n")

    result = gate.validate_evidence_file(
        evidence_path,
        authorization_file_path=authorization_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )

    assert result["authoritative_current_evidence"] is True
    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert "source_artifact_sha256_mismatch" in result["gate_results"]["B"][
        "reasons"
    ]
    assert result["gate_results"]["B"]["source_bytes_sha256_verified"] is False
    assert all(
        result["gate_results"][gate_id]["status"] == "BLOCKED"
        for gate_id in gate.GATE_IDS
    )
    assert all(
        "current_evidence_source_bytes_not_fully_verified"
        in result["gate_results"][gate_id]["reasons"]
        for gate_id in gate.GATE_IDS
    )
    assert result["m6b_data_contract_ready"] is False


@pytest.mark.parametrize("gate_id", gate.GATE_IDS)
def test_each_missing_gate_independently_blocks(gate_id: str) -> None:
    payload = _current_all_pass_payload()
    payload["gates"].pop(gate_id)

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"][gate_id]["status"] == "BLOCKED"
    assert result["m6b_data_contract_ready"] is False


@pytest.mark.parametrize("source_hash", [None, "", "not-a-hash", "A" * 64])
def test_missing_or_invalid_source_hash_blocks(source_hash: object) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["B"]["source_hash"] = source_hash

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert "source_hash_missing_or_invalid" in result["gate_results"]["B"]["reasons"]


@pytest.mark.parametrize(
    ("numerator", "denominator", "reason"),
    [
        (99, 100, "gate_b_coverage_incomplete"),
        (101, 100, "gate_b_coverage_incomplete"),
        (100, 0, "gate_b_coverage_denominator_invalid"),
    ],
)
def test_coverage_mismatch_or_incomplete_coverage_blocks(
    numerator: int,
    denominator: int,
    reason: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["B"]["coverage"].update(
        {"numerator": numerator, "denominator": denominator}
    )

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["B"]["reasons"]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("as_of_timestamp_utc", None, "as_of_timestamp_missing_or_invalid"),
        (
            "as_of_timestamp_utc",
            "2026-06-30T00:00:00Z",
            "as_of_timestamp_future_dated",
        ),
        (
            "evidence_timestamp_utc",
            "2026-06-30T00:00:00Z",
            "evidence_timestamp_future_dated",
        ),
    ],
)
def test_missing_or_future_as_of_evidence_blocks(
    field: str,
    value: object,
    reason: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["C"][field] = value

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["C"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["C"]["reasons"]


def test_restated_eps_without_explicit_approval_is_blocked_and_not_authorized() -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["A"]["gate_specific_evidence"].update(
        {
            "eps_vintage": "release_date_aligned_but_restated",
            "strict_vintage_pit": False,
            "restated_vintage": True,
        }
    )

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )
    gate_a = result["gate_results"]["A"]

    assert gate_a["status"] == "BLOCKED"
    assert gate_a["restated_eps_exception_authorization"]["status"] == "NOT_AUTHORIZED"
    assert gate_a["strict_vintage_pit"] is False
    assert gate_a["restated_vintage"] is True
    assert gate_a["usable_for_alpha_inference"] is False
    assert result["m6b_data_contract_ready"] is False


def test_payload_embedded_restated_approval_without_detached_auth_is_not_authorized(
    tmp_path: Path,
) -> None:
    payload = _current_all_pass_payload()
    payload["restated_eps_exception_approval"] = {
        "authorized": True,
        "approval_reference": "payload-only-approval",
        "approved_at_utc": "2026-06-29T10:00:00Z",
    }
    payload["gates"]["A"]["gate_specific_evidence"].update(
        {
            "eps_vintage": "release_date_aligned_but_restated",
            "strict_vintage_pit": False,
            "restated_vintage": True,
        }
    )
    evidence_path = tmp_path / "payload-only-current-evidence.json"
    evidence_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = gate.validate_evidence_file(
        evidence_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )
    exception_status = result["gate_results"]["A"][
        "restated_eps_exception_authorization"
    ]

    assert result["current_evidence_authorization"]["status"] == "NOT_AUTHORIZED"
    assert exception_status["status"] == "NOT_AUTHORIZED"
    assert "approval_requires_detached_authorization" in exception_status["reasons"]
    assert result["gate_results"]["A"]["status"] == "BLOCKED"
    assert result["m6b_data_contract_ready"] is False


def test_approved_restated_exception_keeps_hard_flags_and_strict_readiness_false(
    tmp_path: Path,
) -> None:
    payload = _current_all_pass_payload()
    payload["restated_eps_exception_approval"] = {
        "authorized": True,
        "approval_reference": "explicit-user-decision-001",
        "approved_at_utc": "2026-06-29T10:00:00Z",
    }
    payload["gates"]["A"]["gate_specific_evidence"].update(
        {
            "eps_vintage": "release_date_aligned_but_restated",
            "strict_vintage_pit": False,
            "restated_vintage": True,
        }
    )
    evidence_path, authorization_path, _ = _write_authorized_current_fixture(
        tmp_path,
        payload,
    )

    result = gate.validate_evidence_file(
        evidence_path,
        authorization_file_path=authorization_path,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
        source_root=tmp_path,
    )
    gate_a = result["gate_results"]["A"]

    assert result["current_evidence_authorization"]["status"] == "AUTHORIZED"
    assert gate_a["restated_eps_exception_authorization"]["status"] == "PASS"
    assert gate_a["status"] == "BLOCKED"
    assert gate_a["strict_vintage_pit"] is False
    assert gate_a["hard_restatement_flags"] == [
        "restated_vintage",
        "strict_vintage_pit_false",
        "usable_for_alpha_inference_false",
    ]
    assert all(
        result["gate_results"][gate_id]["status"] == "PASS"
        for gate_id in ("B", "C", "D")
    )
    assert result["m6b_data_contract_ready"] is False


def test_missing_explicit_delisting_evidence_blocks_gate_b() -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["B"]["gate_specific_evidence"].update(
        {
            "delisting_treatment_verified": False,
            "delisting_treatment_method": None,
        }
    )

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert "explicit_delisting_treatment_missing" in result["gate_results"]["B"]["reasons"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("security_level_total_return_source", "security_level_total_return_source_missing"),
        ("delisting_adjusted_returns", "delisting_adjusted_returns_not_proven"),
        ("delisting_treatment_verified", "delisting_treatment_unverified"),
    ],
)
def test_missing_required_gate_b_flags_block(field: str, reason: str) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["B"]["gate_specific_evidence"].pop(field)

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["B"]["reasons"]


def test_generic_delisting_treatment_text_is_not_canonical_evidence() -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["B"]["gate_specific_evidence"][
        "delisting_treatment_method"
    ] = "generic text saying delistings were handled"

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["B"]["status"] == "BLOCKED"
    assert "delisting_treatment_method_not_canonical" in result[
        "gate_results"
    ]["B"]["reasons"]


@pytest.mark.parametrize("missing_component", ["short_availability", "borrow_cost"])
def test_missing_short_or_borrow_evidence_blocks_gate_d(
    missing_component: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["D"]["gate_specific_evidence"].pop(missing_component)

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["D"]["status"] == "BLOCKED"
    assert any(missing_component in reason for reason in result["gate_results"]["D"]["reasons"])


@pytest.mark.parametrize(
    "missing_component",
    [
        "decision_date_price",
        "adv_liquidity",
        "active_listing_trading_status",
        "corporate_action_delisting_eligibility",
    ],
)
def test_each_as_of_tradability_component_is_required(
    missing_component: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["C"]["gate_specific_evidence"].pop(missing_component)

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["C"]["status"] == "BLOCKED"
    assert any(missing_component in reason for reason in result["gate_results"]["C"]["reasons"])


@pytest.mark.parametrize(
    "component",
    [
        "decision_date_price",
        "adv_liquidity",
        "active_listing_trading_status",
        "corporate_action_delisting_eligibility",
    ],
)
def test_gate_c_component_as_of_must_not_be_after_actual_decision(
    component: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["C"]["gate_specific_evidence"][component].update(
        {
            "timestamp_utc": "2026-06-29T00:00:01Z",
            "decision_timestamp_utc": "2026-06-29T00:00:00Z",
        }
    )

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    reason = f"gate_c_{component}_as_of_timestamp_after_decision"
    assert result["gate_results"]["C"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["C"]["reasons"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        (
            "full_m6_as_of_liquidity_screen",
            "full_m6_as_of_liquidity_screen_missing",
        ),
        ("screen_enforced_preformation", "preformation_screen_not_enforced"),
        (
            "screen_enforced_before_turnover_calculation",
            "pre_turnover_screen_not_enforced",
        ),
        (
            "ineligible_rows_excluded_preformation",
            "ineligible_rows_not_excluded_preformation",
        ),
    ],
)
def test_gate_c_requires_full_m6_preformation_and_turnover_contract(
    field: str,
    reason: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["C"]["gate_specific_evidence"].pop(field)

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["C"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["C"]["reasons"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("future_information_used", "future_information_exclusion_not_proven"),
        ("post_event_inputs_used", "post_event_input_exclusion_not_proven"),
    ],
)
def test_gate_c_future_or_post_event_inputs_block(
    field: str,
    reason: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["C"]["gate_specific_evidence"][field] = True

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["C"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["C"]["reasons"]


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        (
            "daily_short_borrow_bps",
            None,
            "daily_short_borrow_bps_missing_or_nonfinite",
        ),
        (
            "daily_short_borrow_bps",
            float("nan"),
            "daily_short_borrow_bps_missing_or_nonfinite",
        ),
        (
            "daily_short_borrow_bps",
            0.0,
            "daily_short_borrow_bps_not_positive",
        ),
        (
            "borrow_fee_threshold_bps",
            None,
            "borrow_fee_threshold_bps_missing_or_nonfinite",
        ),
        (
            "borrow_fee_threshold_enforced",
            False,
            "borrow_fee_threshold_not_enforced",
        ),
        (
            "borrow_cost_treatment",
            "generic cost text",
            "borrow_cost_treatment_invalid",
        ),
        (
            "nonzero_borrow_cost_enforced",
            False,
            "nonzero_borrow_cost_not_enforced",
        ),
        (
            "net_turnover_and_borrow_cost_model_integrated",
            False,
            "net_turnover_and_borrow_cost_model_not_integrated",
        ),
    ],
)
def test_gate_d_requires_numeric_threshold_cost_and_nonzero_contract(
    field: str,
    value: object,
    reason: str,
) -> None:
    payload = _current_all_pass_payload()
    payload["gates"]["D"]["gate_specific_evidence"][field] = value

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["D"]["status"] == "BLOCKED"
    assert reason in result["gate_results"]["D"]["reasons"]


def test_unauthorized_gate_uses_not_authorized_semantics() -> None:
    payload = _synthetic_payload()
    payload["gates"]["D"] = {"authorized_in_scope": False}

    result = gate.validate_evidence(
        payload,
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["gate_results"]["D"]["status"] == "NOT_AUTHORIZED"
    assert result["m6b_data_contract_ready"] is False


def test_validator_is_evidence_only_and_rejects_non_json_output(tmp_path: Path) -> None:
    result = gate.validate_evidence(
        _synthetic_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    assert result["output_isolation"] == {
        "evidence_only": True,
        "daily_return_parquet_emitted": False,
        "equity_curve_emitted": False,
        "cagr_emitted": False,
        "alpha_result_emitted": False,
        "tradable_status_emitted": False,
    }
    with pytest.raises(ValueError, match=r"\.json evidence"):
        gate.write_evidence_atomic(result, tmp_path / "forbidden.parquet")
    assert list(tmp_path.iterdir()) == []


def test_strict_validator_has_standard_library_imports_only() -> None:
    source_path = Path(gate.__file__)
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )

    assert imported_roots <= {
        "__future__",
        "argparse",
        "hashlib",
        "json",
        "math",
        "os",
        "re",
        "sys",
        "tempfile",
        "datetime",
        "pathlib",
        "typing",
    }


def test_json_output_is_deterministic_and_atomically_replaced(tmp_path: Path) -> None:
    output = tmp_path / "readiness.json"
    result = gate.validate_evidence(
        _synthetic_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    gate.write_evidence_atomic(result, output)
    first_bytes = output.read_bytes()
    output.write_text('{"stale": true}\n', encoding="utf-8")
    gate.write_evidence_atomic(result, output)

    assert output.read_bytes() == first_bytes
    assert not list(tmp_path.glob(".*.tmp"))
    assert json.loads(first_bytes)["workflow_status"] == "synthetic_validation_only"


def test_atomic_write_failure_preserves_target_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "readiness.json"
    output.write_bytes(b'{"original": true}\n')
    result = gate.validate_evidence(
        _synthetic_payload(),
        validation_timestamp_utc=VALIDATION_TIMESTAMP,
    )

    def _fail_replace(source: Path, destination: Path) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(gate.os, "replace", _fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        gate.write_evidence_atomic(result, output)

    assert output.read_bytes() == b'{"original": true}\n'
    assert not list(tmp_path.glob(".*.tmp"))


def test_cli_malformed_and_current_authorization_inputs_fail_without_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="utf-8")
    malformed_output = tmp_path / "malformed-output.json"

    malformed_rc = gate.main(
        [
            "--evidence-file",
            str(malformed),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(malformed_output),
        ]
    )
    malformed_capture = capsys.readouterr()
    authorization = tmp_path / "authorization.json"
    authorization.write_text("{}", encoding="utf-8")
    current_auth_output = tmp_path / "current-auth-output.json"
    current_auth_rc = gate.main(
        [
            "--current-evidence",
            "--authorization-file",
            str(authorization),
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(current_auth_output),
        ]
    )
    current_auth_capture = capsys.readouterr()
    current_output = tmp_path / "current.json"
    current_rc = gate.main(
        [
            "--current-evidence",
            "--validation-timestamp",
            VALIDATION_TIMESTAMP,
            "--output",
            str(current_output),
        ]
    )
    current_capture = capsys.readouterr()

    assert malformed_rc == 2
    assert malformed_capture.out == ""
    assert malformed_capture.err.startswith("[error] ")
    assert not malformed_output.exists()
    assert not list(tmp_path.glob(f".{malformed_output.name}.*.tmp"))
    assert current_auth_rc == 2
    assert current_auth_capture.out == ""
    assert "--authorization-file requires --evidence-file" in current_auth_capture.err
    assert not current_auth_output.exists()
    assert not list(tmp_path.glob(f".{current_auth_output.name}.*.tmp"))
    assert current_rc == 0
    assert current_capture.out.endswith("[status] blocked_fail_closed\n")
    assert current_capture.err == ""
    assert json.loads(current_output.read_text(encoding="utf-8"))["workflow_status"] == "blocked_fail_closed"
