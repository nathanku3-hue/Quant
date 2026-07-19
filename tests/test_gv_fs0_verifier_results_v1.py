from __future__ import annotations

import copy

import pytest

from core.gv_fs0_canonical import domain_hash

DOMAIN = "GV-FS0:VERIFIER_RESULT:V1"


def _result(status: str = "RECONSTRUCTED", marker: str = "a") -> dict:
    payload = {
        "protocol_id": "GV_FS0_PROTOCOL_V1",
        "fixture_id": "FIXTURE_1",
        "fixture_hash": "f" * 64,
        "decision_id": "DECISION_1",
        "decision_hash": "d" * 64,
        "book_id": "BOOK_" + "b" * 64,
        "ordered_economic_event_ids": ["EVT_" + marker * 64],
        "snapshots": [],
        "terminal_snapshot_id": "SNAP_" + "s" * 64,
    }
    if status == "RECONSTRUCTED":
        return {
            "schema_version": "gv_fs0_verifier_result_v1",
            "protocol_binding": "GV_FS0_PROTOCOL_V1",
            "fixture_binding": "f" * 64,
            "decision_binding": "d" * 64,
            "verifier_input_hash": "i" * 64,
            "verifier_status": status,
            "reconstructed_economic_payload": payload,
            "reconstructed_economic_payload_hash": domain_hash("GV-FS0:ECONOMIC_PAYLOAD:V1", payload),
            "failure_codes": [],
        }
    return {
        "schema_version": "gv_fs0_verifier_result_v1",
        "protocol_binding": "GV_FS0_PROTOCOL_V1",
        "fixture_binding": "f" * 64,
        "decision_binding": "d" * 64,
        "verifier_input_hash": "i" * 64,
        "verifier_status": status,
        "reconstructed_economic_payload": None,
        "reconstructed_economic_payload_hash": None,
        "failure_codes": ["INDEPENDENT_RECONSTRUCTION_FAILED"],
    }


def _result_hash(result: dict) -> str:
    return domain_hash(DOMAIN, result)


def _validate_retention(attempts: list[dict], retained: list[dict]) -> None:
    if len(attempts) != 2 or [attempt["ordinal"] for attempt in attempts] != [1, 2]:
        raise ValueError("ATTEMPT_ORDER_INVALID")
    by_hash: dict[str, dict] = {}
    for entry in retained:
        digest = entry["verifier_result_hash"]
        if digest in by_hash:
            raise ValueError("DUPLICATE_RETAINED_HASH")
        if _result_hash(entry["verifier_result"]) != digest:
            raise ValueError("FORGED_RETAINED_HASH")
        by_hash[digest] = entry["verifier_result"]
    referenced: set[str] = set()
    for attempt in attempts:
        if attempt["outcome"] == "RESULT":
            digest = attempt["verifier_result_hash"]
            if digest not in by_hash:
                raise ValueError("MISSING_RETAINED_RESULT")
            if attempt["controller_failure_code"] is not None:
                raise ValueError("RESULT_CONTROLLER_CODE_NON_NULL")
            referenced.add(digest)
        else:
            if attempt["verifier_result_hash"] is not None:
                raise ValueError("INFRASTRUCTURE_HASH_NON_NULL")
            if attempt["controller_failure_code"] is None:
                raise ValueError("INFRASTRUCTURE_CODE_NULL")
    if set(by_hash) != referenced:
        raise ValueError("UNREFERENCED_RETAINED_RESULT")


def _attempt(ordinal: int, result: dict | None = None) -> dict:
    if result is None:
        return {
            "schema_version": "gv_fs0_verifier_attempt_v1",
            "ordinal": ordinal,
            "outcome": "INFRASTRUCTURE_FAILURE",
            "verifier_result_hash": None,
            "controller_failure_code": "VERIFIER_TIMEOUT",
        }
    return {
        "schema_version": "gv_fs0_verifier_attempt_v1",
        "ordinal": ordinal,
        "outcome": "RESULT",
        "verifier_result_hash": _result_hash(result),
        "controller_failure_code": None,
    }


def _retained(result: dict) -> dict:
    return {"verifier_result_hash": _result_hash(result), "verifier_result": result}


def test_identical_attempts_reference_one_unique_retained_result() -> None:
    result = _result()
    attempts = [_attempt(1, result), _attempt(2, result)]
    retained = [_retained(result)]
    _validate_retention(attempts, retained)
    assert attempts[0]["verifier_result_hash"] == attempts[1]["verifier_result_hash"]


def test_differing_valid_attempts_reference_two_sorted_retained_results() -> None:
    first = _result(marker="a")
    second = _result(marker="b")
    retained = sorted([_retained(first), _retained(second)], key=lambda item: item["verifier_result_hash"])
    _validate_retention([_attempt(1, first), _attempt(2, second)], retained)
    assert len(retained) == 2


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("duplicate", "DUPLICATE_RETAINED_HASH"),
        ("missing", "MISSING_RETAINED_RESULT"),
        ("unreferenced", "UNREFERENCED_RETAINED_RESULT"),
        ("forged", "FORGED_RETAINED_HASH"),
    ],
)
def test_invalid_retained_result_graph_blocks(mutation: str, error: str) -> None:
    result = _result()
    other = _result(marker="b")
    attempts = [_attempt(1, result), _attempt(2, result)]
    retained = [_retained(result)]
    if mutation == "duplicate":
        retained.append(copy.deepcopy(retained[0]))
    elif mutation == "missing":
        retained.clear()
    elif mutation == "unreferenced":
        retained.append(_retained(other))
    elif mutation == "forged":
        retained[0]["verifier_result_hash"] = "0" * 64
    with pytest.raises(ValueError, match=error):
        _validate_retention(attempts, retained)


def test_infrastructure_attempt_references_no_retained_result() -> None:
    result = _result()
    attempts = [_attempt(1, result), _attempt(2, None)]
    _validate_retention(attempts, [_retained(result)])


def test_attempt_order_is_authoritative_not_retained_collection_order() -> None:
    first = _result(marker="a")
    second = _result(marker="b")
    attempts = [_attempt(1, second), _attempt(2, first)]
    retained = sorted([_retained(first), _retained(second)], key=lambda item: item["verifier_result_hash"])
    _validate_retention(attempts, retained)
    assert [attempt["ordinal"] for attempt in attempts] == [1, 2]
