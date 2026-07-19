from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from core.gv_fs0_canonical import domain_hash

ROOT = Path(__file__).resolve().parents[1]
REGISTRIES = ROOT / "contracts/gv_fs0/v1/registries"
CONTRACT = ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md"

CHECK_ORDER = [
    "decision_authority_valid",
    "timestamp_causality_valid",
    "price_freshness_valid",
    "cash_conserved",
    "holdings_valid",
    "nav_reconciled",
    "receivables_reconciled",
    "unsupported_events_absent",
    "independent_reconstruction_passed",
    "canonical_hash_reproduced",
]
OUTCOME_RANK = {"FALSE": 10, "UNKNOWN": 20}


def _load(name: str) -> dict:
    return json.loads((REGISTRIES / name).read_text(encoding="utf-8"))


def _validate_bindings(checks: dict[str, str], bindings: list[dict], emitter: str) -> None:
    registry = _load("gv_fs0_certification_failure_registry_v1.json")
    entries = {entry["code"]: entry for entry in registry["entries"]}
    seen: set[tuple[str, str, str]] = set()
    bound_checks: dict[tuple[str, str], int] = {}
    for binding in bindings:
        key = (binding["check"], binding["outcome"], binding["code"])
        if key in seen:
            raise ValueError("DUPLICATE_FAILURE_BINDING")
        seen.add(key)
        if checks[binding["check"]] == "TRUE":
            raise ValueError("TRUE_CHECK_HAS_BINDING")
        entry = entries.get(binding["code"])
        if entry is None:
            raise ValueError("UNKNOWN_FAILURE_CODE")
        if binding["check"] not in entry["applicable_checks"]:
            raise ValueError("FAILURE_CODE_CHECK_INCOMPATIBLE")
        if binding["outcome"] not in entry["applicable_outcomes"]:
            raise ValueError("FAILURE_CODE_OUTCOME_INCOMPATIBLE")
        if emitter not in entry["applicable_emitters"]:
            raise ValueError("FAILURE_CODE_EMITTER_INCOMPATIBLE")
        if checks[binding["check"]] != binding["outcome"]:
            raise ValueError("FAILURE_BINDING_CHECK_MISMATCH")
        bound_checks[(binding["check"], binding["outcome"])] = bound_checks.get((binding["check"], binding["outcome"]), 0) + 1
    for check, outcome in checks.items():
        count = bound_checks.get((check, outcome), 0)
        if outcome == "TRUE" and count:
            raise ValueError("TRUE_CHECK_HAS_BINDING")
        if outcome in {"FALSE", "UNKNOWN"} and count == 0:
            raise ValueError("NONTRUE_CHECK_MISSING_BINDING")


def test_registry_entries_are_canonically_sorted_and_unique() -> None:
    for filename in [
        "gv_fs0_certification_failure_registry_v1.json",
        "gv_fs0_operational_error_registry_v1.json",
    ]:
        registry = _load(filename)
        codes = [entry["code"] for entry in registry["entries"]]
        assert codes == sorted(codes)
        assert len(codes) == len(set(codes))


def test_certification_registry_outcomes_never_include_true() -> None:
    registry = _load("gv_fs0_certification_failure_registry_v1.json")
    for entry in registry["entries"]:
        assert set(entry["applicable_outcomes"]) <= {"FALSE", "UNKNOWN"}
        assert "TRUE" not in entry["applicable_outcomes"]
        assert set(entry["applicable_emitters"]) <= {"PRIMARY", "VERIFIER", "CONTROLLER"}


def test_all_true_certification_permits_no_bindings() -> None:
    checks = {check: "TRUE" for check in CHECK_ORDER}
    _validate_bindings(checks, [], "PRIMARY")


def test_false_and_unknown_require_compatible_bindings() -> None:
    checks = {check: "TRUE" for check in CHECK_ORDER}
    checks["timestamp_causality_valid"] = "FALSE"
    checks["price_freshness_valid"] = "UNKNOWN"
    bindings = [
        {"check": "timestamp_causality_valid", "outcome": "FALSE", "code": "DUPLICATE_ORIGIN_ORDER_KEY"},
        {"check": "price_freshness_valid", "outcome": "UNKNOWN", "code": "PRICE_VALIDATION_UNAVAILABLE"},
    ]
    _validate_bindings(checks, bindings, "PRIMARY")


def test_false_precedence_over_unknown_is_frozen() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "FALSE takes precedence over UNKNOWN" in contract
    assert "conclusive evidence of violation produces FALSE" in contract


@pytest.mark.parametrize(
    ("mutator", "error"),
    [
        (lambda checks, bindings: bindings.append({"check": "cash_conserved", "outcome": "FALSE", "code": "CASH_CONSERVATION_FAILED"}), "TRUE_CHECK_HAS_BINDING"),
        (lambda checks, bindings: checks.__setitem__("cash_conserved", "FALSE"), "NONTRUE_CHECK_MISSING_BINDING"),
        (lambda checks, bindings: (checks.__setitem__("cash_conserved", "FALSE"), bindings.append({"check": "cash_conserved", "outcome": "FALSE", "code": "NAV_RECONCILIATION_FAILED"})), "FAILURE_CODE_CHECK_INCOMPATIBLE"),
        (lambda checks, bindings: (checks.__setitem__("canonical_hash_reproduced", "FALSE"), bindings.append({"check": "canonical_hash_reproduced", "outcome": "FALSE", "code": "CANONICAL_HASH_UNAVAILABLE"})), "FAILURE_CODE_OUTCOME_INCOMPATIBLE"),
    ],
)
def test_incompatible_or_missing_bindings_block(mutator, error: str) -> None:
    checks = {check: "TRUE" for check in CHECK_ORDER}
    bindings: list[dict] = []
    mutator(checks, bindings)
    with pytest.raises(ValueError, match=error):
        _validate_bindings(checks, bindings, "PRIMARY")


def test_controller_only_code_rejects_primary_emitter() -> None:
    checks = {check: "TRUE" for check in CHECK_ORDER}
    checks["independent_reconstruction_passed"] = "UNKNOWN"
    bindings = [
        {
            "check": "independent_reconstruction_passed",
            "outcome": "UNKNOWN",
            "code": "VERIFIER_TIMEOUT",
        }
    ]
    with pytest.raises(ValueError, match="FAILURE_CODE_EMITTER_INCOMPATIBLE"):
        _validate_bindings(checks, bindings, "PRIMARY")
    _validate_bindings(checks, bindings, "CONTROLLER")


def test_failure_binding_canonical_order_is_check_outcome_code() -> None:
    bindings = [
        {"check": "canonical_hash_reproduced", "outcome": "UNKNOWN", "code": "CANONICAL_HASH_UNAVAILABLE"},
        {"check": "timestamp_causality_valid", "outcome": "FALSE", "code": "DUPLICATE_ORIGIN_ORDER_KEY"},
    ]
    ordered = sorted(
        bindings,
        key=lambda item: (CHECK_ORDER.index(item["check"]), OUTCOME_RANK[item["outcome"]], item["code"]),
    )
    assert [item["check"] for item in ordered] == ["timestamp_causality_valid", "canonical_hash_reproduced"]


def test_certification_registry_hash_changes_identity_but_operational_registry_does_not() -> None:
    certification_registry = _load("gv_fs0_certification_failure_registry_v1.json")
    operational_registry = _load("gv_fs0_operational_error_registry_v1.json")
    preimage = {
        "certification_failure_registry_version": certification_registry["registry_version"],
        "certification_failure_registry_hash": domain_hash(
            "GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1", certification_registry
        ),
        "checks": {check: "TRUE" for check in CHECK_ORDER},
    }
    identity = domain_hash("GV-FS0:CERTIFICATION_ID:V1", preimage)

    changed_cert = copy.deepcopy(certification_registry)
    changed_cert["entries"][0]["stable_user_message"] += " changed"
    changed_preimage = dict(
        preimage,
        certification_failure_registry_hash=domain_hash(
            "GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1", changed_cert
        ),
    )
    assert domain_hash("GV-FS0:CERTIFICATION_ID:V1", changed_preimage) != identity

    changed_operational = copy.deepcopy(operational_registry)
    changed_operational["entries"][0]["stable_user_message"] += " changed"
    assert domain_hash("GV-FS0:CERTIFICATION_ID:V1", preimage) == identity
