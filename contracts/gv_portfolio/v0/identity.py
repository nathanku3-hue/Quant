"""Custody-owned identity and evidence contracts for GV Portfolio V0.

Only permanent identity fields participate in instrument identity. Display labels,
roles, prices, decisions, and portfolio state are deliberately outside this
contract. Evidence references bind exact UTF-8 content bytes to canonical source
metadata.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

from core.gv_fs0_canonical import (
    CanonicalizationError,
    assert_sha256,
    canonical_timestamp,
    domain_hash,
    prepare_identity_string,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
INSTRUMENT_NAMESPACE = "GV_SYNTHETIC_PERMANENT_V0"


class CustodyContractError(ValueError):
    """Raised when identity or evidence custody validation fails closed."""


def _identity_text(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CustodyContractError(f"{field.upper()}_REQUIRED")
    try:
        return prepare_identity_string(value)
    except CanonicalizationError as exc:
        raise CustodyContractError(f"{field.upper()}_INVALID:{exc}") from exc


def _canonical_observed_at(value: Any) -> str:
    if not isinstance(value, str):
        raise CustodyContractError("OBSERVED_AT_REQUIRED")
    try:
        normalized = canonical_timestamp(value)
    except CanonicalizationError as exc:
        raise CustodyContractError(f"OBSERVED_AT_INVALID:{exc}") from exc
    if normalized != value:
        raise CustodyContractError("OBSERVED_AT_NOT_CANONICAL")
    return normalized


def identifier(kind: str, payload: Mapping[str, Any]) -> str:
    """Return a domain-separated, content-derived identifier."""

    canonical_kind = _identity_text(kind, field="kind")
    if not isinstance(payload, Mapping):
        raise CustodyContractError("IDENTITY_PAYLOAD_MAPPING_REQUIRED")
    return f"{canonical_kind}_" + domain_hash(
        f"{ID_DOMAIN}:{canonical_kind}:V1", dict(payload)
    )


def record_with_id(
    kind: str, id_key: str, payload: Mapping[str, Any]
) -> dict[str, Any]:
    """Return a record whose identifier binds every supplied payload field."""

    canonical_id_key = _identity_text(id_key, field="id_key")
    body = dict(payload)
    if canonical_id_key in body:
        raise CustodyContractError("IDENTITY_FIELD_ALREADY_PRESENT")
    return {canonical_id_key: identifier(kind, body), **body}


def instrument_identity(
    permanent_key: str,
    *,
    namespace: str = INSTRUMENT_NAMESPACE,
    security_class: str = "COMMON_STOCK",
) -> dict[str, str]:
    """Create stable instrument identity independent of mutable display data."""

    body = {
        "namespace": _identity_text(namespace, field="namespace"),
        "permanent_key": _identity_text(permanent_key, field="permanent_key"),
        "security_class": _identity_text(security_class, field="security_class"),
    }
    return {"instrument_id": identifier("INS", body), **body}


def verify_instrument_identity(record: Mapping[str, Any]) -> None:
    if not isinstance(record, Mapping):
        raise CustodyContractError("INSTRUMENT_MAPPING_REQUIRED")
    required = {"instrument_id", "namespace", "permanent_key", "security_class"}
    if not required.issubset(record):
        raise CustodyContractError("INSTRUMENT_IDENTITY_FIELDS_MISSING")
    expected = instrument_identity(
        record["permanent_key"],
        namespace=record["namespace"],
        security_class=record["security_class"],
    )
    if record["instrument_id"] != expected["instrument_id"]:
        raise CustodyContractError("INSTRUMENT_ID_MISMATCH")


def evidence_reference(
    *,
    content: str,
    locator: str,
    observed_at: str,
    media_type: str = "text/plain",
) -> dict[str, str]:
    """Create a content-addressed evidence reference with exact source metadata."""

    if not isinstance(content, str):
        raise CustodyContractError("EVIDENCE_CONTENT_TEXT_REQUIRED")
    raw = content.encode("utf-8")
    content_sha256 = hashlib.sha256(raw).hexdigest()
    identity = {
        "content_sha256": content_sha256,
        "media_type": _identity_text(media_type, field="media_type"),
        "locator": _identity_text(locator, field="locator"),
        "observed_at": _canonical_observed_at(observed_at),
    }
    return {
        "evidence_reference_id": identifier("EVD", identity),
        **identity,
        "content": content,
    }


def verify_evidence_reference(record: Mapping[str, Any]) -> None:
    """Verify exact content hash, canonical metadata, and derived evidence ID."""

    if not isinstance(record, Mapping):
        raise CustodyContractError("EVIDENCE_REFERENCE_MAPPING_REQUIRED")
    required = {
        "evidence_reference_id",
        "content_sha256",
        "media_type",
        "locator",
        "observed_at",
        "content",
    }
    actual_fields = set(record)
    if actual_fields != required:
        missing = sorted(required - actual_fields)
        extra = sorted(actual_fields - required)
        raise CustodyContractError(
            f"EVIDENCE_REFERENCE_FIELDS_INVALID:missing={missing}:extra={extra}"
        )
    if not isinstance(record["content"], str):
        raise CustodyContractError("EVIDENCE_CONTENT_TEXT_REQUIRED")
    actual_hash = hashlib.sha256(record["content"].encode("utf-8")).hexdigest()
    try:
        declared_hash = assert_sha256(record["content_sha256"])
    except CanonicalizationError as exc:
        raise CustodyContractError(f"EVIDENCE_SHA256_INVALID:{exc}") from exc
    if actual_hash != declared_hash:
        raise CustodyContractError("EVIDENCE_CONTENT_HASH_MISMATCH")
    expected = evidence_reference(
        content=record["content"],
        locator=record["locator"],
        observed_at=record["observed_at"],
        media_type=record["media_type"],
    )
    if record["evidence_reference_id"] != expected["evidence_reference_id"]:
        raise CustodyContractError("EVIDENCE_REFERENCE_ID_MISMATCH")


def verify_record_id(
    record: Mapping[str, Any], *, kind: str, id_key: str
) -> None:
    """Verify a generic content-derived record identifier."""

    if not isinstance(record, Mapping):
        raise CustodyContractError("IDENTIFIED_RECORD_MAPPING_REQUIRED")
    if id_key not in record:
        raise CustodyContractError(f"IDENTITY_FIELD_MISSING:{id_key}")
    body = {key: value for key, value in record.items() if key != id_key}
    if record[id_key] != identifier(kind, body):
        raise CustodyContractError(f"IDENTITY_MISMATCH:{id_key}")
