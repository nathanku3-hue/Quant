"""Pure GV-FS0 certified-bundle identity, schema, and byte validation.

This module consumes frozen schemas and canonical primitives. It owns no
portfolio accounting, verifier execution, publication lock, or UI rendering.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import copy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from core.gv_fs0_canonical import (
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "contracts" / "gv_fs0" / "v1" / "schemas"
PROTOCOL_ID = "GV_FS0_PROTOCOL_V1"
BUNDLE_SCHEMA_VERSION = "gv_fs0_certified_bundle_v1"
BUNDLE_DOMAIN = "GV-FS0:CERTIFIED_BUNDLE:V1"
COMPONENT_DOMAIN = "GV-FS0:CERTIFIED_DECISION_RESULT:V1"
DECISION_DOMAIN = "GV-FS0:DECISION_ENVELOPE:V1"
CERTIFICATION_DOMAIN = "GV-FS0:CERTIFICATION_ID:V1"
PRESENTATION_DOMAIN = "GV-FS0:PRESENTATION:V1"
EXPECTED_ROLES = ("OPEN", "NO_POSITION")

_COMPONENT_AUTHORITATIVE_KEYS = (
    "schema_version",
    "role",
    "decision",
    "book_id",
    "events",
    "snapshots",
    "economic_payload_hash",
    "verifier_attempts",
    "retained_verifier_results",
    "certification",
    "certification_reference_event",
)


class GvFs0BundleError(ValueError):
    """Fail-closed bundle validation error."""


def _load_schema(path: Path) -> dict[str, Any]:
    payload = parse_canonical_document_bytes(path.read_bytes())
    if not isinstance(payload, dict):
        raise GvFs0BundleError(f"SCHEMA_OBJECT_REQUIRED:{path.name}")
    return payload


def _schema_registry() -> Registry:
    registry = Registry()
    for path in sorted(SCHEMA_ROOT.glob("*.schema.json")):
        schema = _load_schema(path)
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def _validate_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    schema = _load_schema(SCHEMA_ROOT / schema_name)
    try:
        Draft202012Validator(schema, registry=_schema_registry()).validate(dict(payload))
    except Exception as exc:
        raise GvFs0BundleError(f"SCHEMA_INVALID:{schema_name}") from exc


def _validate_decision_identity(decision: Mapping[str, Any]) -> None:
    preimage = {key: value for key, value in decision.items() if key != "decision_hash"}
    expected_hash = domain_hash(DECISION_DOMAIN, preimage)
    if decision.get("decision_hash") != expected_hash:
        raise GvFs0BundleError("DECISION_HASH_INVALID")


def _validate_certification_identity(certification: Mapping[str, Any]) -> None:
    preimage = {
        "certification_schema_version": certification["schema_version"],
        **{
            key: value
            for key, value in certification.items()
            if key not in {"schema_version", "certification_id"}
        },
    }
    expected_id = "CERT_" + domain_hash(CERTIFICATION_DOMAIN, preimage)
    if certification.get("certification_id") != expected_id:
        raise GvFs0BundleError("CERTIFICATION_ID_INVALID")


def _validate_presentation_identity(presentation: Mapping[str, Any]) -> None:
    rows = presentation.get("rows")
    if not isinstance(rows, list):
        raise GvFs0BundleError("PRESENTATION_ROWS_INVALID")
    expected_hash = domain_hash(PRESENTATION_DOMAIN, {"rows": rows})
    if presentation.get("presentation_hash") != expected_hash:
        raise GvFs0BundleError("PRESENTATION_HASH_INVALID")


def validate_certified_component(
    component: Mapping[str, Any], *, expected_role: str
) -> dict[str, Any]:
    """Validate one complete certified result and return an isolated copy."""

    _validate_schema(component, "gv_fs0_certified_decision_result_v1.schema.json")
    if component.get("role") != expected_role:
        raise GvFs0BundleError("COMPONENT_ROLE_INVALID")
    decision = component["decision"]
    if decision.get("action") != expected_role:
        raise GvFs0BundleError("COMPONENT_ACTION_INVALID")
    if decision.get("protocol_id") != PROTOCOL_ID:
        raise GvFs0BundleError("COMPONENT_PROTOCOL_INVALID")
    _validate_decision_identity(decision)

    certification = component["certification"]
    if certification.get("certification_status") != "CERTIFIED":
        raise GvFs0BundleError("COMPONENT_NOT_CERTIFIED")
    if certification.get("protocol_id") != PROTOCOL_ID:
        raise GvFs0BundleError("CERTIFICATION_PROTOCOL_INVALID")
    if certification.get("decision_hash") != decision.get("decision_hash"):
        raise GvFs0BundleError("CERTIFICATION_DECISION_BINDING_INVALID")
    if certification.get("book_id") != component.get("book_id"):
        raise GvFs0BundleError("CERTIFICATION_BOOK_BINDING_INVALID")
    if certification.get("primary_economic_payload_hash") != component.get(
        "economic_payload_hash"
    ):
        raise GvFs0BundleError("CERTIFICATION_ECONOMIC_BINDING_INVALID")
    _validate_certification_identity(certification)

    snapshots = component["snapshots"]
    if not snapshots:
        raise GvFs0BundleError("COMPONENT_SNAPSHOTS_REQUIRED")
    terminal = snapshots[-1]
    if certification.get("terminal_snapshot_id") != terminal.get("snapshot_id"):
        raise GvFs0BundleError("CERTIFICATION_SNAPSHOT_BINDING_INVALID")
    if terminal.get("action") != expected_role:
        raise GvFs0BundleError("TERMINAL_ACTION_INVALID")

    reference = component["certification_reference_event"]
    events = component["events"]
    if not events or events[-1] != reference:
        raise GvFs0BundleError("CERTIFICATION_REFERENCE_ORDER_INVALID")
    if reference.get("payload", {}).get("certification_id") != certification.get(
        "certification_id"
    ):
        raise GvFs0BundleError("CERTIFICATION_REFERENCE_BINDING_INVALID")

    authoritative = {key: component[key] for key in _COMPONENT_AUTHORITATIVE_KEYS}
    expected_hash = domain_hash(COMPONENT_DOMAIN, authoritative)
    if component.get("certified_decision_result_hash") != expected_hash:
        raise GvFs0BundleError("COMPONENT_HASH_INVALID")
    if component.get("certified_decision_result_id") != "CDR_" + expected_hash:
        raise GvFs0BundleError("COMPONENT_ID_INVALID")
    _validate_presentation_identity(component["presentation"])
    return copy.deepcopy(dict(component))


def build_certified_bundle(
    components: Sequence[Mapping[str, Any]], *, currency: str = "USD"
) -> dict[str, Any]:
    """Build the exact two-role canonical bundle without publication side effects."""

    if len(components) != 2:
        raise GvFs0BundleError("BUNDLE_REQUIRES_TWO_COMPONENTS")
    validated = [
        validate_certified_component(component, expected_role=role)
        for component, role in zip(components, EXPECTED_ROLES, strict=True)
    ]
    preimage = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "currency": currency,
        "components": validated,
    }
    bundle_hash = domain_hash(BUNDLE_DOMAIN, preimage)
    bundle = {
        **preimage,
        "bundle_hash": bundle_hash,
        "bundle_id": "BUNDLE_" + bundle_hash,
    }
    return validate_certified_bundle(bundle)


def validate_certified_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Validate schema, component identities, role order, and bundle identity."""

    _validate_schema(bundle, "gv_fs0_certified_bundle_v1.schema.json")
    if bundle.get("protocol_id") != PROTOCOL_ID:
        raise GvFs0BundleError("BUNDLE_PROTOCOL_INVALID")
    components = bundle.get("components")
    if not isinstance(components, list) or len(components) != 2:
        raise GvFs0BundleError("BUNDLE_REQUIRES_TWO_COMPONENTS")
    validated = [
        validate_certified_component(component, expected_role=role)
        for component, role in zip(components, EXPECTED_ROLES, strict=True)
    ]
    preimage = {
        "schema_version": bundle["schema_version"],
        "protocol_id": bundle["protocol_id"],
        "currency": bundle["currency"],
        "components": validated,
    }
    expected_hash = domain_hash(BUNDLE_DOMAIN, preimage)
    if bundle.get("bundle_hash") != expected_hash:
        raise GvFs0BundleError("BUNDLE_HASH_INVALID")
    if bundle.get("bundle_id") != "BUNDLE_" + expected_hash:
        raise GvFs0BundleError("BUNDLE_ID_INVALID")
    return copy.deepcopy(dict(bundle))


def certified_bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    return canonical_document_bytes(validate_certified_bundle(bundle))


def parse_certified_bundle_bytes(raw: bytes) -> dict[str, Any]:
    """Require canonical bytes and return a fully validated bundle."""

    try:
        payload = parse_canonical_document_bytes(raw)
    except Exception as exc:
        raise GvFs0BundleError("BUNDLE_BYTES_INVALID") from exc
    if not isinstance(payload, dict):
        raise GvFs0BundleError("BUNDLE_OBJECT_REQUIRED")
    validated = validate_certified_bundle(payload)
    if canonical_document_bytes(validated) != raw:
        raise GvFs0BundleError("BUNDLE_BYTES_NOT_CANONICAL")
    return validated


def read_certified_bundle(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GvFs0BundleError("BUNDLE_FILE_UNAVAILABLE") from exc
    return parse_certified_bundle_bytes(raw)


__all__ = [
    "BUNDLE_DOMAIN",
    "BUNDLE_SCHEMA_VERSION",
    "EXPECTED_ROLES",
    "GvFs0BundleError",
    "PROTOCOL_ID",
    "build_certified_bundle",
    "certified_bundle_bytes",
    "parse_certified_bundle_bytes",
    "read_certified_bundle",
    "validate_certified_bundle",
    "validate_certified_component",
]
