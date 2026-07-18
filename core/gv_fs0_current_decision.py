"""Read-only GV-FS0 current-decision identity (single active certified result).

Shared by publication and the Streamlit adapter so both enforce the same
canonical-byte gate. This module owns no locks, atomic replace, accounting,
or UI rendering.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from core.gv_fs0_bundle import validate_certified_component
from core.gv_fs0_canonical import (
    canonical_document_bytes,
    parse_canonical_document_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CURRENT_DECISION_PATH = ROOT / "data" / "gv_fs0" / "gv_fs0_current_decision.json"


class GvFs0CurrentDecisionError(ValueError):
    """Fail-closed current-decision identity error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def certified_decision_result_bytes(result: Mapping[str, Any]) -> bytes:
    """Canonical bytes for one certified decision result (single-current path)."""

    role = result.get("role")
    if role not in {"OPEN", "NO_POSITION"}:
        raise GvFs0CurrentDecisionError(f"CURRENT_DECISION_ROLE_INVALID:{role!r}")
    validated = validate_certified_component(result, expected_role=str(role))
    return canonical_document_bytes(validated)


def parse_current_decision_bytes(raw: bytes) -> dict[str, Any]:
    """Require canonical bytes and return one fully validated certified result."""

    try:
        payload = parse_canonical_document_bytes(raw)
    except Exception as exc:
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_BYTES_INVALID") from exc
    if not isinstance(payload, dict):
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_OBJECT_REQUIRED")
    role = payload.get("role")
    if role not in {"OPEN", "NO_POSITION"}:
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_ROLE_INVALID")
    try:
        validated = validate_certified_component(payload, expected_role=str(role))
    except Exception as exc:
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_COMPONENT_INVALID") from exc
    if canonical_document_bytes(validated) != raw:
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_BYTES_NOT_CANONICAL")
    return validated


def read_current_decision(path: Path = DEFAULT_CURRENT_DECISION_PATH) -> dict[str, Any]:
    """Read and parse current decision bytes; missing path fails closed."""

    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise GvFs0CurrentDecisionError("CURRENT_DECISION_UNAVAILABLE") from exc
    return parse_current_decision_bytes(raw)


__all__ = [
    "DEFAULT_CURRENT_DECISION_PATH",
    "GvFs0CurrentDecisionError",
    "certified_decision_result_bytes",
    "parse_current_decision_bytes",
    "read_current_decision",
]
