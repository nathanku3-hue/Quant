"""Fail-closed, evidence-only validator for strict PEAD M6b Path A data gates.

The validator evaluates provenance records; it does not fetch data, transform
source rows, or emit research returns.  Synthetic fixtures can prove validator
logic, but only an explicitly authorized current-evidence invocation can ever
make a current-readiness decision.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = (
    ROOT
    / "docs"
    / "context"
    / "e2e_evidence"
    / "pead_m6b_strict_path_a_readiness.json"
)

ROUND_ID = "ROUND-20260629-V2-PEAD-M6B-STRICT-PATH-A-INFRA"
SCOPE_ID = "V2_PEAD_M6B_STRICT_PATH_A_DATA_GATE_INFRA"
ARTIFACT_NAME = "pead_m6b_strict_path_a_readiness"
GATE_IDS = ("A", "B", "C", "D")
VALID_STATUSES = ("PASS", "BLOCKED", "NOT_AUTHORIZED")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
AUTHORIZATION_MODE = "APPROVAL_GATE"
AUTHORIZATION_ACTION = "evaluate_strict_path_a_current_evidence"
DELISTING_TREATMENT_METHODS = {
    "security_level_total_return_includes_verified_delisting_adjustment",
    "terminal_return_compounded_with_verified_delisting_return",
}
BORROW_COST_TREATMENT = "deduct_daily_short_borrow_bps_from_short_exposure"
BORROW_THRESHOLD_TREATMENT = (
    "exclude_short_when_daily_borrow_bps_exceeds_threshold"
)


def _parse_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty ISO-8601 timestamp")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = f"{candidate[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{label} must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _canonical_timestamp(value: Any, label: str) -> str:
    parsed = _parse_timestamp(value, label)
    return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build one JSON object only when every member name is unambiguous."""

    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError(f"duplicate JSON key: {key!r}")
        parsed[key] = value
    return parsed


def _parse_unambiguous_json_object(raw_json: str | bytes, *, source: Path) -> dict[str, Any]:
    """Reject ambiguous object members before any evidence or authority evaluation."""

    try:
        parsed = json.loads(raw_json, object_pairs_hook=_reject_duplicate_json_keys)
    except ValueError as exc:
        raise ValueError(f"{source} contains invalid or ambiguous JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{source} must contain a JSON object")
    return parsed


def _validate_coverage(
    coverage: Any,
    *,
    label: str,
    require_complete: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    normalized = coverage if isinstance(coverage, dict) else {}
    reasons: list[str] = []
    numerator = normalized.get("numerator")
    denominator = normalized.get("denominator")
    definition = normalized.get("definition")
    if not _is_int(numerator) or numerator < 0:
        reasons.append(f"{label}_coverage_numerator_invalid")
    if not _is_int(denominator) or denominator <= 0:
        reasons.append(f"{label}_coverage_denominator_invalid")
    if (
        require_complete
        and _is_int(numerator)
        and _is_int(denominator)
        and denominator > 0
        and numerator != denominator
    ):
        reasons.append(f"{label}_coverage_incomplete")
    if not _nonempty_string(definition):
        reasons.append(f"{label}_coverage_definition_missing")
    return {
        "numerator": numerator,
        "denominator": denominator,
        "definition": definition,
    }, reasons


def _validate_component(
    component: Any,
    *,
    label: str,
    evidence_timestamp: datetime | None,
    validation_timestamp: datetime,
    require_decision_timestamp: bool = False,
) -> list[str]:
    record = component if isinstance(component, dict) else {}
    reasons: list[str] = []
    if record.get("valid_as_of_decision_date") is not True:
        reasons.append(f"{label}_not_valid_as_of_decision_date")
    if not _nonempty_string(record.get("as_of_proof")):
        reasons.append(f"{label}_as_of_proof_missing")
    _, coverage_reasons = _validate_coverage(
        record.get("coverage"),
        label=label,
    )
    reasons.extend(coverage_reasons)
    try:
        timestamp = _parse_timestamp(record.get("timestamp_utc"), f"{label}.timestamp_utc")
    except ValueError:
        reasons.append(f"{label}_timestamp_missing_or_invalid")
        timestamp = None
    else:
        if timestamp > validation_timestamp:
            reasons.append(f"{label}_timestamp_future_dated")
        if evidence_timestamp is not None and timestamp > evidence_timestamp:
            reasons.append(f"{label}_timestamp_after_evidence")
    if require_decision_timestamp:
        try:
            decision_timestamp = _parse_timestamp(
                record.get("decision_timestamp_utc"),
                f"{label}.decision_timestamp_utc",
            )
        except ValueError:
            reasons.append(f"{label}_decision_timestamp_missing_or_invalid")
        else:
            if decision_timestamp > validation_timestamp:
                reasons.append(f"{label}_decision_timestamp_future_dated")
            if (
                evidence_timestamp is not None
                and decision_timestamp > evidence_timestamp
            ):
                reasons.append(f"{label}_decision_timestamp_after_evidence")
            if timestamp is not None and timestamp > decision_timestamp:
                reasons.append(f"{label}_as_of_timestamp_after_decision")
        if not _nonempty_string(record.get("decision_timestamp_proof")):
            reasons.append(f"{label}_decision_timestamp_proof_missing")
    return reasons


def _validate_gate_a(evidence: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if evidence.get("eps_vintage") != "first_public_unrestated":
        reasons.append("first_public_unrestated_eps_missing")
    if evidence.get("strict_vintage_pit") is not True:
        reasons.append("strict_vintage_pit_not_proven")
    if evidence.get("restated_vintage") is not False:
        reasons.append("restated_vintage_detected_or_unresolved")
    if evidence.get("sue_as_of_decision_date") is not True:
        reasons.append("sue_as_of_decision_date_not_proven")
    if not _nonempty_string(evidence.get("release_timing_evidence")):
        reasons.append("release_timing_evidence_missing")
    return reasons


def _validate_gate_b(evidence: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    required_true = {
        "security_level_total_return_source": "security_level_total_return_source_missing",
        "tradable_return_source": "tradable_return_source_missing",
        "delisting_adjusted_returns": "delisting_adjusted_returns_not_proven",
        "delisting_treatment_verified": "delisting_treatment_unverified",
        "security_date_coverage_verified": "security_date_coverage_unverified",
    }
    for field, reason in required_true.items():
        if evidence.get(field) is not True:
            reasons.append(reason)
    method = evidence.get("delisting_treatment_method")
    if not _nonempty_string(method):
        reasons.append("explicit_delisting_treatment_missing")
    elif method not in DELISTING_TREATMENT_METHODS:
        reasons.append("delisting_treatment_method_not_canonical")
    delisting_count = evidence.get("delisting_event_count")
    if not _is_int(delisting_count) or delisting_count < 0:
        reasons.append("delisting_event_count_invalid")
    return reasons


def _validate_gate_c(
    evidence: dict[str, Any],
    *,
    evidence_timestamp: datetime | None,
    validation_timestamp: datetime,
) -> list[str]:
    reasons: list[str] = []
    for component in (
        "decision_date_price",
        "adv_liquidity",
        "active_listing_trading_status",
        "corporate_action_delisting_eligibility",
    ):
        reasons.extend(
            _validate_component(
                evidence.get(component),
                label=f"gate_c_{component}",
                evidence_timestamp=evidence_timestamp,
                validation_timestamp=validation_timestamp,
                require_decision_timestamp=True,
            )
        )
    required_true = {
        "full_m6_as_of_liquidity_screen": "full_m6_as_of_liquidity_screen_missing",
        "screen_enforced_preformation": "preformation_screen_not_enforced",
        "screen_enforced_before_turnover_calculation": "pre_turnover_screen_not_enforced",
        "ineligible_rows_excluded_preformation": "ineligible_rows_not_excluded_preformation",
    }
    for field, reason in required_true.items():
        if evidence.get(field) is not True:
            reasons.append(reason)
    if evidence.get("future_information_used") is not False:
        reasons.append("future_information_exclusion_not_proven")
    if evidence.get("post_event_inputs_used") is not False:
        reasons.append("post_event_input_exclusion_not_proven")
    return reasons


def _validate_gate_d(
    evidence: dict[str, Any],
    *,
    evidence_timestamp: datetime | None,
    validation_timestamp: datetime,
) -> list[str]:
    reasons: list[str] = []
    for component in ("short_availability", "borrow_cost"):
        reasons.extend(
            _validate_component(
                evidence.get(component),
                label=f"gate_d_{component}",
                evidence_timestamp=evidence_timestamp,
                validation_timestamp=validation_timestamp,
            )
        )
    if evidence.get("testable_contract") is not True:
        reasons.append("short_borrow_contract_not_testable")
    if evidence.get("short_availability_tested") is not True:
        reasons.append("short_availability_not_explicitly_tested")
    if evidence.get("borrow_cost_contract_tested") is not True:
        reasons.append("borrow_cost_contract_not_tested")
    daily_short_borrow_bps = evidence.get("daily_short_borrow_bps")
    if not _is_finite_number(daily_short_borrow_bps):
        reasons.append("daily_short_borrow_bps_missing_or_nonfinite")
    elif daily_short_borrow_bps <= 0:
        reasons.append("daily_short_borrow_bps_not_positive")
    borrow_fee_threshold_bps = evidence.get("borrow_fee_threshold_bps")
    if not _is_finite_number(borrow_fee_threshold_bps):
        reasons.append("borrow_fee_threshold_bps_missing_or_nonfinite")
    elif borrow_fee_threshold_bps <= 0:
        reasons.append("borrow_fee_threshold_bps_not_positive")
    if evidence.get("borrow_fee_threshold_enforced") is not True:
        reasons.append("borrow_fee_threshold_not_enforced")
    if evidence.get("borrow_fee_threshold_treatment") != BORROW_THRESHOLD_TREATMENT:
        reasons.append("borrow_fee_threshold_treatment_invalid")
    if evidence.get("borrow_cost_treatment") != BORROW_COST_TREATMENT:
        reasons.append("borrow_cost_treatment_invalid")
    if evidence.get("borrow_cost_units") != "bps_per_day":
        reasons.append("borrow_cost_units_invalid")
    if evidence.get("missing_borrow_fails_closed") is not True:
        reasons.append("missing_borrow_fail_closed_not_proven")
    if evidence.get("nonzero_borrow_cost_enforced") is not True:
        reasons.append("nonzero_borrow_cost_not_enforced")
    if evidence.get("net_turnover_and_borrow_cost_model_integrated") is not True:
        reasons.append("net_turnover_and_borrow_cost_model_not_integrated")
    return reasons


GATE_VALIDATORS: dict[str, Callable[..., list[str]]] = {
    "A": _validate_gate_a,
    "B": _validate_gate_b,
    "C": _validate_gate_c,
    "D": _validate_gate_d,
}


def _validate_common_gate_record(
    record: Any,
    *,
    gate_id: str,
    validation_timestamp: datetime,
) -> tuple[dict[str, Any], list[str], datetime | None]:
    gate = record if isinstance(record, dict) else {}
    reasons: list[str] = []
    source_hash = gate.get("source_hash")
    if not isinstance(source_hash, str) or SHA256_PATTERN.fullmatch(source_hash) is None:
        reasons.append("source_hash_missing_or_invalid")
    source_identifier = gate.get("source_identifier")
    if not _nonempty_string(source_identifier):
        reasons.append("source_provenance_identifier_missing")
    source_artifact_path = gate.get("source_artifact_path")
    coverage, coverage_reasons = _validate_coverage(
        gate.get("coverage"),
        label=f"gate_{gate_id.lower()}",
    )
    reasons.extend(coverage_reasons)

    evidence_timestamp: datetime | None = None
    normalized_evidence_timestamp = gate.get("evidence_timestamp_utc")
    try:
        evidence_timestamp = _parse_timestamp(
            normalized_evidence_timestamp,
            f"gate_{gate_id}.evidence_timestamp_utc",
        )
    except ValueError:
        reasons.append("evidence_timestamp_missing_or_invalid")
    else:
        normalized_evidence_timestamp = _canonical_timestamp(
            normalized_evidence_timestamp,
            f"gate_{gate_id}.evidence_timestamp_utc",
        )
        if evidence_timestamp > validation_timestamp:
            reasons.append("evidence_timestamp_future_dated")

    normalized_as_of_timestamp = gate.get("as_of_timestamp_utc")
    try:
        as_of_timestamp = _parse_timestamp(
            normalized_as_of_timestamp,
            f"gate_{gate_id}.as_of_timestamp_utc",
        )
    except ValueError:
        reasons.append("as_of_timestamp_missing_or_invalid")
    else:
        normalized_as_of_timestamp = _canonical_timestamp(
            normalized_as_of_timestamp,
            f"gate_{gate_id}.as_of_timestamp_utc",
        )
        if as_of_timestamp > validation_timestamp:
            reasons.append("as_of_timestamp_future_dated")
        if evidence_timestamp is not None and as_of_timestamp > evidence_timestamp:
            reasons.append("as_of_timestamp_after_evidence")

    as_of_proof = gate.get("as_of_proof")
    if not _nonempty_string(as_of_proof):
        reasons.append("as_of_proof_missing")
    checks = gate.get("validation_checks_performed")
    if (
        not isinstance(checks, list)
        or not checks
        or any(not _nonempty_string(item) for item in checks)
    ):
        reasons.append("validation_checks_missing_or_invalid")
        checks = []
    elif len(checks) != len(set(checks)):
        reasons.append("validation_checks_not_unique")

    gate_specific_evidence = gate.get("gate_specific_evidence")
    if not isinstance(gate_specific_evidence, dict):
        reasons.append("gate_specific_evidence_missing")
        gate_specific_evidence = {}

    normalized = {
        "source_hash": source_hash,
        "source_identifier": source_identifier,
        "source_artifact_path": source_artifact_path,
        "source_bytes_sha256_verified": False,
        "coverage": coverage,
        "evidence_timestamp_utc": normalized_evidence_timestamp,
        "as_of_timestamp_utc": normalized_as_of_timestamp,
        "as_of_proof": as_of_proof,
        "gate_specific_evidence": gate_specific_evidence,
        "validation_checks_performed": checks,
    }
    return normalized, reasons, evidence_timestamp


def _restated_exception_status(
    approval: Any,
    *,
    validation_timestamp: datetime,
    authoritative_current_evidence: bool,
) -> dict[str, Any]:
    record = approval if isinstance(approval, dict) else {}
    reasons: list[str] = []
    if not authoritative_current_evidence:
        reasons.append("approval_requires_detached_authorization")
    if record.get("authorized") is not True:
        reasons.append("explicit_user_approval_missing")
    if not _nonempty_string(record.get("approval_reference")):
        reasons.append("approval_reference_missing")
    approved_at = record.get("approved_at_utc")
    try:
        approved_timestamp = _parse_timestamp(
            approved_at,
            "restated_eps_exception_approval.approved_at_utc",
        )
    except ValueError:
        reasons.append("approval_timestamp_missing_or_invalid")
    else:
        approved_at = _canonical_timestamp(
            approved_at,
            "restated_eps_exception_approval.approved_at_utc",
        )
        if approved_timestamp > validation_timestamp:
            reasons.append("approval_timestamp_future_dated")
    return {
        "status": "PASS" if not reasons else "NOT_AUTHORIZED",
        "approval_reference": record.get("approval_reference"),
        "approved_at_utc": approved_at,
        "reasons": sorted(set(reasons)),
        "strict_readiness_effect": "none; restated EPS remains non-strict and fail-closed",
    }


def _authorization_result(
    *,
    status: str,
    supplied: bool,
    reasons: list[str],
    record: dict[str, Any] | None = None,
    evidence_file_sha256_actual: str | None = None,
) -> dict[str, Any]:
    authorization = record if isinstance(record, dict) else {}
    return {
        "status": status,
        "supplied": supplied,
        "authorization_id": authorization.get("authorization_id"),
        "round_id": authorization.get("round_id"),
        "scope_id": authorization.get("scope_id"),
        "mode": authorization.get("mode"),
        "action": authorization.get("action"),
        "authorized_at_utc": authorization.get("authorized_at_utc"),
        "evidence_file_sha256_declared": authorization.get(
            "evidence_file_sha256"
        ),
        "evidence_file_sha256_actual": evidence_file_sha256_actual,
        "evidence_file_sha256_verified": bool(
            status == "AUTHORIZED"
            and evidence_file_sha256_actual is not None
        ),
        "reasons": sorted(set(reasons)),
    }


def _validate_authorization_schema(
    authorization: dict[str, Any],
) -> tuple[dict[str, Any], datetime]:
    normalized = dict(authorization)
    reasons: list[str] = []

    if not isinstance(normalized.get("authorized"), bool):
        reasons.append("authorized_must_be_boolean")
    for field in (
        "authorization_id",
        "round_id",
        "scope_id",
        "mode",
        "action",
    ):
        if not _nonempty_string(normalized.get(field)):
            reasons.append(f"{field}_must_be_nonempty_string")

    declared_hash = normalized.get("evidence_file_sha256")
    if (
        not isinstance(declared_hash, str)
        or SHA256_PATTERN.fullmatch(declared_hash) is None
    ):
        reasons.append("evidence_file_sha256_must_be_lowercase_sha256")

    try:
        authorized_timestamp = _parse_timestamp(
            normalized.get("authorized_at_utc"),
            "authorization.authorized_at_utc",
        )
    except ValueError:
        reasons.append("authorized_at_utc_must_be_timezone_qualified_iso8601")
        authorized_timestamp = datetime.min.replace(tzinfo=timezone.utc)

    if reasons:
        raise ValueError(
            "authorization artifact schema invalid: "
            + ", ".join(sorted(reasons))
        )

    normalized["authorized_at_utc"] = _canonical_timestamp(
        normalized["authorized_at_utc"],
        "authorization.authorized_at_utc",
    )
    return normalized, authorized_timestamp


def _validate_current_authorization(
    *,
    evidence_file_path: Path,
    evidence_file_sha256_actual: str,
    authorization_file_path: Path | None,
    validation_timestamp: datetime,
) -> dict[str, Any]:
    if authorization_file_path is None:
        return _authorization_result(
            status="NOT_AUTHORIZED",
            supplied=False,
            reasons=["separate_authorization_artifact_required"],
            evidence_file_sha256_actual=evidence_file_sha256_actual,
        )

    evidence_path = Path(evidence_file_path).resolve()
    authorization_path = Path(authorization_file_path).resolve()
    if evidence_path == authorization_path:
        return _authorization_result(
            status="NOT_AUTHORIZED",
            supplied=True,
            reasons=["authorization_artifact_must_be_distinct_from_evidence"],
            evidence_file_sha256_actual=evidence_file_sha256_actual,
        )

    authorization, authorized_timestamp = _validate_authorization_schema(
        _read_json_object(authorization_path)
    )

    reasons: list[str] = []
    if authorization.get("authorized") is not True:
        reasons.append("authorization_not_explicitly_granted")
    if authorization.get("round_id") != ROUND_ID:
        reasons.append("authorization_round_mismatch")
    if authorization.get("scope_id") != SCOPE_ID:
        reasons.append("authorization_scope_mismatch")
    if authorization.get("mode") != AUTHORIZATION_MODE:
        reasons.append("authorization_mode_mismatch")
    if authorization.get("action") != AUTHORIZATION_ACTION:
        reasons.append("authorization_action_mismatch")

    declared_hash = authorization.get("evidence_file_sha256")
    if declared_hash != evidence_file_sha256_actual:
        reasons.append("authorization_evidence_hash_mismatch")

    if authorized_timestamp > validation_timestamp:
        reasons.append("authorization_timestamp_future_dated")

    return _authorization_result(
        status="AUTHORIZED" if not reasons else "NOT_AUTHORIZED",
        supplied=True,
        reasons=reasons,
        record=authorization,
        evidence_file_sha256_actual=evidence_file_sha256_actual,
    )


def _verify_local_source_artifact(
    normalized_gate: dict[str, Any],
    *,
    source_root: Path,
) -> list[str]:
    reasons: list[str] = []
    source_artifact_path = normalized_gate.get("source_artifact_path")
    if not _nonempty_string(source_artifact_path):
        return ["source_artifact_path_missing"]

    relative_path = Path(source_artifact_path)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return ["source_artifact_path_not_repo_relative"]

    root = Path(source_root).resolve()
    unresolved_path = root / relative_path
    if unresolved_path.is_symlink():
        return ["source_artifact_symlink_not_allowed"]
    try:
        resolved_path = unresolved_path.resolve(strict=True)
        resolved_path.relative_to(root)
    except (OSError, ValueError):
        return ["source_artifact_missing_or_outside_root"]
    if not resolved_path.is_file():
        return ["source_artifact_not_regular_file"]

    actual_hash = _sha256_file(resolved_path)
    normalized_gate["source_artifact_path"] = relative_path.as_posix()
    normalized_gate["source_bytes_sha256_actual"] = actual_hash
    declared_hash = normalized_gate.get("source_hash")
    if (
        not isinstance(declared_hash, str)
        or SHA256_PATTERN.fullmatch(declared_hash) is None
        or actual_hash != declared_hash
    ):
        reasons.append("source_artifact_sha256_mismatch")
    else:
        normalized_gate["source_bytes_sha256_verified"] = True
    return reasons


def _validate_evidence(
    payload: dict[str, Any],
    *,
    validation_timestamp_utc: str,
    current_authorization: dict[str, Any],
    source_root: Path,
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("evidence payload must be a JSON object")
    validation_timestamp = _parse_timestamp(
        validation_timestamp_utc,
        "validation_timestamp_utc",
    )
    canonical_validation_timestamp = _canonical_timestamp(
        validation_timestamp_utc,
        "validation_timestamp_utc",
    )
    validation_context = payload.get("validation_context")
    if validation_context not in {"current_evidence", "synthetic_test"}:
        raise ValueError("validation_context must be current_evidence or synthetic_test")
    gates = payload.get("gates")
    if not isinstance(gates, dict):
        raise ValueError("gates must be a JSON object")
    authoritative_current_evidence = bool(
        validation_context == "current_evidence"
        and current_authorization.get("status") == "AUTHORIZED"
    )

    gate_results: dict[str, dict[str, Any]] = {}
    exception_status = _restated_exception_status(
        payload.get("restated_eps_exception_approval"),
        validation_timestamp=validation_timestamp,
        authoritative_current_evidence=authoritative_current_evidence,
    )
    for gate_id in GATE_IDS:
        raw_gate = gates.get(gate_id)
        gate = raw_gate if isinstance(raw_gate, dict) else {}
        gate_authorized_in_scope = gate.get("authorized_in_scope", True) is True
        if not gate_authorized_in_scope and validation_context == "synthetic_test":
            gate_results[gate_id] = {
                "status": "NOT_AUTHORIZED",
                "reasons": ["gate_action_not_authorized"],
                "strict_readiness_effect": "forces_false",
            }
            continue

        normalized, reasons, evidence_timestamp = _validate_common_gate_record(
            gate,
            gate_id=gate_id,
            validation_timestamp=validation_timestamp,
        )
        if not gate_authorized_in_scope:
            reasons.append("gate_action_not_authorized")
        if authoritative_current_evidence and gate_authorized_in_scope:
            reasons.extend(
                _verify_local_source_artifact(
                    normalized,
                    source_root=source_root,
                )
            )
        validator = GATE_VALIDATORS[gate_id]
        if gate_id in {"C", "D"}:
            reasons.extend(
                validator(
                    normalized["gate_specific_evidence"],
                    evidence_timestamp=evidence_timestamp,
                    validation_timestamp=validation_timestamp,
                )
            )
        else:
            reasons.extend(validator(normalized["gate_specific_evidence"]))

        if gate_id == "A":
            gate_a_evidence = normalized["gate_specific_evidence"]
            restated_vintage = gate_a_evidence.get("restated_vintage") is not False
            strict_vintage_pit = (
                gate_a_evidence.get("strict_vintage_pit") is True
                and not restated_vintage
            )
            normalized["strict_vintage_pit"] = strict_vintage_pit
            normalized["restated_vintage"] = restated_vintage
            normalized["usable_for_alpha_inference"] = False
            normalized["restated_eps_exception_authorization"] = exception_status
            normalized["hard_restatement_flags"] = (
                []
                if strict_vintage_pit
                else [
                    "restated_vintage",
                    "strict_vintage_pit_false",
                    "usable_for_alpha_inference_false",
                ]
            )

        status = "PASS" if not reasons else "BLOCKED"
        gate_results[gate_id] = {
            "status": status,
            "reasons": sorted(set(reasons)),
            "strict_readiness_effect": "eligible_to_contribute"
            if status == "PASS"
            else "forces_false",
            **normalized,
        }

    if validation_context == "current_evidence":
        all_source_bytes_verified = all(
            gate_results[gate_id].get("source_bytes_sha256_verified") is True
            for gate_id in GATE_IDS
        )
        for gate_id in GATE_IDS:
            gate_result = gate_results[gate_id]
            reasons = list(gate_result["reasons"])
            if not authoritative_current_evidence:
                reasons.append("current_evidence_authorization_not_authorized")
            if not all_source_bytes_verified:
                reasons.append(
                    "current_evidence_source_bytes_not_fully_verified"
                )
            status = "PASS" if not reasons else "BLOCKED"
            gate_result["status"] = status
            gate_result["reasons"] = sorted(set(reasons))
            gate_result["strict_readiness_effect"] = (
                "eligible_to_contribute"
                if status == "PASS"
                else "forces_false"
            )

    statuses = [gate_results[gate_id]["status"] for gate_id in GATE_IDS]
    all_gates_pass = all(status == "PASS" for status in statuses)
    gate_a_result = gate_results["A"]
    strict_vintage_pit = gate_a_result.get("strict_vintage_pit") is True
    m6b_data_contract_ready = bool(
        authoritative_current_evidence
        and all_gates_pass
        and strict_vintage_pit
    )
    workflow_status = (
        "synthetic_validation_only"
        if validation_context == "synthetic_test"
        else (
            "ready_current_evidence"
            if m6b_data_contract_ready
            else "blocked_fail_closed"
        )
    )
    status_counts = {
        status: sum(item == status for item in statuses)
        for status in VALID_STATUSES
    }

    return {
        "schema_version": "1.1",
        "artifact_name": ARTIFACT_NAME,
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "validation_timestamp_utc": canonical_validation_timestamp,
        "validation_context": validation_context,
        "authorized_current_evidence_invocation": authoritative_current_evidence,
        "authoritative_current_evidence": authoritative_current_evidence,
        "current_evidence_authorization": current_authorization,
        "hypothetical_all_gates_pass": bool(
            validation_context == "synthetic_test" and all_gates_pass
        ),
        "workflow_status": workflow_status,
        "m6a_engine_ready": payload.get("m6a_engine_ready") is True,
        "m6b_data_contract_ready": m6b_data_contract_ready,
        "gate_status_counts": status_counts,
        "gate_results": gate_results,
        "claim_boundary": {
            "allowed_claim": "strict Path A evidence-validator infrastructure only",
            "strict_data_ready_claim_allowed": m6b_data_contract_ready,
            "strategy_promotion_authorized": False,
            "tradable_research_authorized": False,
        },
        "output_isolation": {
            "evidence_only": True,
            "daily_return_parquet_emitted": False,
            "equity_curve_emitted": False,
            "cagr_emitted": False,
            "alpha_result_emitted": False,
            "tradable_status_emitted": False,
        },
    }


def validate_evidence(
    payload: dict[str, Any],
    *,
    validation_timestamp_utc: str,
) -> dict[str, Any]:
    """Validate content only; payload fields can never authorize current evidence."""

    validation_context = (
        payload.get("validation_context") if isinstance(payload, dict) else None
    )
    authorization = _authorization_result(
        status=(
            "NOT_APPLICABLE"
            if validation_context == "synthetic_test"
            else "NOT_AUTHORIZED"
        ),
        supplied=False,
        reasons=(
            []
            if validation_context == "synthetic_test"
            else ["separate_authorization_artifact_required"]
        ),
    )
    return _validate_evidence(
        payload,
        validation_timestamp_utc=validation_timestamp_utc,
        current_authorization=authorization,
        source_root=ROOT,
    )


def validate_evidence_file(
    evidence_file_path: Path,
    *,
    validation_timestamp_utc: str,
    authorization_file_path: Path | None = None,
    source_root: Path = ROOT,
) -> dict[str, Any]:
    """Validate exact evidence-file bytes and an optional distinct authorization."""

    evidence_path = Path(evidence_file_path).resolve()
    evidence_bytes = evidence_path.read_bytes()
    payload = _parse_unambiguous_json_object(evidence_bytes, source=evidence_path)
    if (
        payload.get("validation_context") == "synthetic_test"
        and authorization_file_path is not None
    ):
        raise ValueError(
            "--authorization-file is invalid when validation_context=synthetic_test"
        )
    evidence_hash = hashlib.sha256(evidence_bytes).hexdigest()
    validation_timestamp = _parse_timestamp(
        validation_timestamp_utc,
        "validation_timestamp_utc",
    )
    if payload.get("validation_context") == "current_evidence":
        authorization = _validate_current_authorization(
            evidence_file_path=evidence_path,
            evidence_file_sha256_actual=evidence_hash,
            authorization_file_path=authorization_file_path,
            validation_timestamp=validation_timestamp,
        )
    else:
        authorization = _authorization_result(
            status="NOT_APPLICABLE",
            supplied=authorization_file_path is not None,
            reasons=[],
            evidence_file_sha256_actual=evidence_hash,
        )
    return _validate_evidence(
        payload,
        validation_timestamp_utc=validation_timestamp_utc,
        current_authorization=authorization,
        source_root=source_root,
    )


def build_current_evidence_payload() -> dict[str, Any]:
    """Declare observed local gaps without treating them as positive evidence."""

    return {
        "validation_context": "current_evidence",
        "m6a_engine_ready": True,
        "restated_eps_exception_approval": {
            "authorized": False,
            "approval_reference": None,
            "approved_at_utc": None,
        },
        "gates": {
            "A": {
                "authorized_in_scope": True,
                "source_identifier": "current local release-date-aligned EPS evidence",
                "gate_specific_evidence": {
                    "eps_vintage": "release_date_aligned_but_restated",
                    "strict_vintage_pit": False,
                    "restated_vintage": True,
                    "sue_as_of_decision_date": False,
                    "release_timing_evidence": "release date alignment only; first-public vintage not established",
                },
            },
            "B": {
                "authorized_in_scope": True,
                "source_identifier": "current local return evidence",
                "gate_specific_evidence": {
                    "security_level_total_return_source": False,
                    "tradable_return_source": False,
                    "delisting_adjusted_returns": False,
                    "delisting_treatment_verified": False,
                    "security_date_coverage_verified": False,
                    "delisting_treatment_method": None,
                    "delisting_event_count": None,
                },
            },
            "C": {
                "authorized_in_scope": True,
                "source_identifier": "current local liquidity evidence",
                "gate_specific_evidence": {
                    "full_m6_as_of_liquidity_screen": False,
                    "screen_enforced_preformation": False,
                    "screen_enforced_before_turnover_calculation": False,
                    "ineligible_rows_excluded_preformation": False,
                    "future_information_used": False,
                    "post_event_inputs_used": False,
                },
            },
            "D": {
                "authorized_in_scope": True,
                "source_identifier": "current local cost-model assumption",
                "gate_specific_evidence": {
                    "testable_contract": False,
                    "short_availability_tested": False,
                    "borrow_cost_contract_tested": False,
                    "daily_short_borrow_bps": None,
                    "borrow_fee_threshold_bps": None,
                    "borrow_fee_threshold_enforced": False,
                    "borrow_fee_threshold_treatment": None,
                    "borrow_cost_treatment": None,
                    "borrow_cost_units": None,
                    "missing_borrow_fails_closed": True,
                    "nonzero_borrow_cost_enforced": False,
                    "net_turnover_and_borrow_cost_model_integrated": False,
                },
            },
        },
    }


def _read_json_object(path: Path) -> dict[str, Any]:
    resolved_path = Path(path).resolve()
    return _parse_unambiguous_json_object(
        resolved_path.read_bytes(),
        source=resolved_path,
    )


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def write_evidence_atomic(payload: dict[str, Any], output_path: Path) -> Path:
    output = Path(output_path).resolve()
    if output.suffix.lower() != ".json":
        raise ValueError("strict Path A validator output must be a .json evidence file")
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
    except BaseException:
        try:
            os.close(file_descriptor)
        except OSError:
            pass
        temporary_path.unlink(missing_ok=True)
        raise
    return output


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate strict PEAD M6b Path A evidence without emitting research data"
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--current-evidence",
        action="store_true",
        help="Evaluate the bounded current local evidence declaration",
    )
    source.add_argument(
        "--evidence-file",
        type=Path,
        help="Validate a current_evidence or synthetic_test JSON fixture",
    )
    parser.add_argument(
        "--validation-timestamp",
        required=True,
        help="Timezone-qualified ISO-8601 timestamp recorded in deterministic output",
    )
    parser.add_argument(
        "--authorization-file",
        type=Path,
        help=(
            "Distinct authorization JSON bound to the exact --evidence-file bytes; "
            "never valid with --current-evidence"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Explicit JSON output path; synthetic evidence may never target canonical readiness",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.current_evidence:
            if args.authorization_file is not None:
                raise ValueError(
                    "--authorization-file requires --evidence-file so its exact "
                    "bytes can be bound"
                )
            evidence = validate_evidence(
                build_current_evidence_payload(),
                validation_timestamp_utc=args.validation_timestamp,
            )
        else:
            evidence = validate_evidence_file(
                args.evidence_file,
                validation_timestamp_utc=args.validation_timestamp,
                authorization_file_path=args.authorization_file,
            )
        output_path = Path(args.output).resolve()
        if (
            evidence["validation_context"] == "synthetic_test"
            and output_path == OUTPUT_PATH.resolve()
        ):
            raise ValueError(
                "synthetic_test output must not target the canonical strict Path A "
                "readiness artifact"
            )
        output = write_evidence_atomic(evidence, output_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2
    print(f"[write] {output}")
    print(f"[status] {evidence['workflow_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
