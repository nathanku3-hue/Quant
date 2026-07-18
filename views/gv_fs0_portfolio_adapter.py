"""Read-only GV-FS0 certified portfolio adapter.

Injected component rendering remains the test seam. The default product path
loads one permanent, canonical, schema-valid two-role bundle and injects each
component through the same display function. The adapter owns no accounting,
verifier execution, certification aggregation, or publication.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from core.gv_fs0_bundle import GvFs0BundleError, read_certified_bundle

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE_PATH = ROOT / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"


class PortfolioRenderer(Protocol):
    def subheader(self, body: str) -> Any: ...

    def table(self, data: Any) -> Any: ...

    def caption(self, body: str) -> Any: ...


class GvFs0PresentationError(ValueError):
    """Raised when injected certified presentation artifacts do not bind."""


def _expected_rows(
    terminal_snapshot: Mapping[str, Any], certification: Mapping[str, Any]
) -> list[dict[str, str]]:
    return [
        {"label": "Authority", "value": terminal_snapshot["authority_tier"]},
        {"label": "Action", "value": terminal_snapshot["action"]},
        {"label": "Rationale", "value": terminal_snapshot["rationale_ref"]},
        {"label": "Shares", "value": str(terminal_snapshot["shares"])},
        {"label": "Cash", "value": terminal_snapshot["cash"]},
        {"label": "Receivables", "value": terminal_snapshot["receivables"]},
        {"label": "NAV", "value": terminal_snapshot["nav"]},
        {"label": "SessionContribution", "value": terminal_snapshot["session_contribution"]},
        {"label": "CumulativeContribution", "value": terminal_snapshot["cumulative_contribution"]},
        {"label": "BookId", "value": terminal_snapshot["book_id"]},
        {"label": "DecisionHash", "value": certification["decision_hash"]},
        {"label": "SnapshotId", "value": terminal_snapshot["snapshot_id"]},
        {"label": "CertificationId", "value": certification["certification_id"]},
        {"label": "CertificationStatus", "value": certification["certification_status"]},
    ]


def _presentation_hash(rows: list[dict[str, str]]) -> str:
    payload = json.dumps(
        {"rows": rows}, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    preimage = b"GV-FS0:PRESENTATION:V1\n" + payload + b"\n"
    return hashlib.sha256(preimage).hexdigest()


def build_portfolio_view_model(
    *,
    presentation: Mapping[str, Any],
    terminal_snapshot: Mapping[str, Any],
    certification: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate bindings and return a display-only model without calculations."""

    if certification.get("certification_status") != "CERTIFIED":
        raise GvFs0PresentationError("CERTIFIED_INPUT_REQUIRED")
    action = terminal_snapshot.get("action")
    if action not in {"OPEN", "NO_POSITION"}:
        raise GvFs0PresentationError("PRESENTATION_ACTION_INVALID")
    if certification.get("terminal_snapshot_id") != terminal_snapshot.get("snapshot_id"):
        raise GvFs0PresentationError("TERMINAL_SNAPSHOT_BINDING_INVALID")
    if certification.get("book_id") != terminal_snapshot.get("book_id"):
        raise GvFs0PresentationError("BOOK_BINDING_INVALID")
    rows = presentation.get("rows")
    if not isinstance(rows, list) or not rows:
        raise GvFs0PresentationError("PRESENTATION_ROWS_REQUIRED")
    normalized_rows: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"label", "value"}:
            raise GvFs0PresentationError("PRESENTATION_ROW_INVALID")
        label = row["label"]
        value = row["value"]
        if not isinstance(label, str) or not isinstance(value, str):
            raise GvFs0PresentationError("PRESENTATION_ROW_TEXT_REQUIRED")
        normalized_rows.append({"label": label, "value": value})
    expected_rows = _expected_rows(terminal_snapshot, certification)
    if normalized_rows != expected_rows:
        raise GvFs0PresentationError("PRESENTATION_BINDING_INVALID")
    if presentation.get("presentation_hash") != _presentation_hash(expected_rows):
        raise GvFs0PresentationError("PRESENTATION_HASH_INVALID")
    return {
        "title": f"GV-FS0 Certified Paper Portfolio — {action}",
        "status": certification["certification_status"],
        "rows": normalized_rows,
        "presentation_hash": presentation.get("presentation_hash"),
        "snapshot_id": terminal_snapshot["snapshot_id"],
        "certification_id": certification["certification_id"],
    }


def render_gv_fs0_portfolio(
    renderer: PortfolioRenderer,
    *,
    presentation: Mapping[str, Any],
    terminal_snapshot: Mapping[str, Any],
    certification: Mapping[str, Any],
) -> dict[str, Any]:
    """Render one injected certified component and return the displayed model."""

    model = build_portfolio_view_model(
        presentation=presentation,
        terminal_snapshot=terminal_snapshot,
        certification=certification,
    )
    renderer.subheader(model["title"])
    renderer.table(model["rows"])
    renderer.caption(
        f"{model['status']} · snapshot {model['snapshot_id']} · certification {model['certification_id']}"
    )
    return model


def load_default_certified_bundle(
    bundle_path: Path = DEFAULT_BUNDLE_PATH,
) -> dict[str, Any]:
    """Load permanent product truth; missing or invalid bytes fail closed."""

    try:
        return read_certified_bundle(Path(bundle_path))
    except GvFs0BundleError as exc:
        raise GvFs0PresentationError(f"CERTIFIED_BUNDLE_INVALID:{exc}") from exc


def render_gv_fs0_certified_bundle(
    renderer: PortfolioRenderer,
    *,
    bundle_path: Path = DEFAULT_BUNDLE_PATH,
) -> list[dict[str, Any]]:
    """Render OPEN then NO_POSITION from the permanent validated bundle."""

    bundle = load_default_certified_bundle(bundle_path)
    models: list[dict[str, Any]] = []
    for component in bundle["components"]:
        models.append(
            render_gv_fs0_portfolio(
                renderer,
                presentation=component["presentation"],
                terminal_snapshot=component["snapshots"][-1],
                certification=component["certification"],
            )
        )
    return models


__all__ = [
    "DEFAULT_BUNDLE_PATH",
    "GvFs0PresentationError",
    "build_portfolio_view_model",
    "load_default_certified_bundle",
    "render_gv_fs0_certified_bundle",
    "render_gv_fs0_portfolio",
]
