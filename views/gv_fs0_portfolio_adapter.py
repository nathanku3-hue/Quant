"""Read-only GV-FS0 / E0A portfolio adapter.

Injected component rendering remains the test seam. The default product path
loads one published current certified decision and renders a single component.
The F1C permanent two-role bundle loader remains available for evidence tests
only and is not the default product export path. The adapter owns no accounting,
verifier execution, certification aggregation, or publication.
"""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any, Protocol

from core.gv_fs0_bundle import (
    GvFs0BundleError,
    read_certified_bundle,
)
from core.gv_fs0_current_decision import (
    DEFAULT_CURRENT_DECISION_PATH,
    GvFs0CurrentDecisionError,
    parse_current_decision_bytes,
)

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
    """Load permanent F1C evidence bundle; missing or invalid bytes fail closed."""

    try:
        return read_certified_bundle(Path(bundle_path))
    except GvFs0BundleError as exc:
        raise GvFs0PresentationError(f"CERTIFIED_BUNDLE_INVALID:{exc}") from exc


def render_gv_fs0_certified_bundle(
    renderer: PortfolioRenderer,
    *,
    bundle_path: Path = DEFAULT_BUNDLE_PATH,
) -> list[dict[str, Any]]:
    """Evidence-only: render OPEN then NO_POSITION from the permanent bundle."""

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


def load_current_certified_decision(
    decision_path: Path | None = None,
) -> dict[str, Any]:
    """Load one current decision via the same canonical parser as publication.

    Object-only / non-canonical bytes that pass loose JSON schema checks but fail
    publisher identity are rejected here as well. Path is resolved at call time
    so tests can retarget the default product authority without reimport.
    """

    path = Path(
        decision_path if decision_path is not None else DEFAULT_CURRENT_DECISION_PATH
    )
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise GvFs0PresentationError("CURRENT_DECISION_UNAVAILABLE") from exc
    try:
        return parse_current_decision_bytes(raw)
    except GvFs0CurrentDecisionError as exc:
        raise GvFs0PresentationError(f"CURRENT_DECISION_INVALID:{exc}") from exc


def render_gv_fs0_current_decision(
    renderer: PortfolioRenderer,
    *,
    decision_path: Path | None = None,
) -> dict[str, Any]:
    """Default product path: render exactly one current certified decision."""

    component = load_current_certified_decision(decision_path)
    return render_gv_fs0_portfolio(
        renderer,
        presentation=component["presentation"],
        terminal_snapshot=component["snapshots"][-1],
        certification=component["certification"],
    )


def render_e0b_dv1_surface(
    renderer: PortfolioRenderer,
    *,
    result_json_path: Path | None = None,
) -> dict[str, Any] | None:
    """Optional E0B comparison surface. Missing artifact → count 0, no raise."""

    from core.gv_e0b_dv1_contradiction import (
        DEFAULT_RESULT_JSON,
        GvE0bDv1Error,
        observation_authority_from_disk,
        render_e0b_dv1_comparison,
    )

    path = Path(result_json_path) if result_json_path is not None else DEFAULT_RESULT_JSON
    authority = observation_authority_from_disk(path)
    count = int(authority["observed_comparison_count"])
    inv = authority.get("invalidation")
    if not path.is_file():
        renderer.caption(
            f"E0B observed-comparison count = {count} "
            "(no published comparison artifact; stage stays "
            "CERTIFIED_SINGLE_DECISION_OPERABLE; score 39 frozen)"
        )
        return None
    try:
        # Always render sealed product-smoke comparison; observation authority
        # is supersedable by append-only invalidation (count may remain 0).
        return dict(render_e0b_dv1_comparison(renderer, result_json_path=path))
    except GvE0bDv1Error as exc:
        inv_bit = ""
        if isinstance(inv, dict):
            inv_bit = f"; invalidation={inv.get('classification')}"
        renderer.caption(
            f"E0B observed-comparison count = {count} "
            f"(comparison artifact refused: {exc}{inv_bit})"
        )
        return None


def render_v2_b0_surface(
    renderer: PortfolioRenderer,
    *,
    result_json_path: Path | None = None,
) -> dict[str, Any] | None:
    """Optional V2-B0 admission surface. Missing artifact → quiet no-raise."""

    from core.gv_v2_b0_real_block_only import DEFAULT_RESULT_PATH, CASE_ID

    path = Path(result_json_path) if result_json_path is not None else DEFAULT_RESULT_PATH
    if not path.is_file():
        renderer.caption(
            "V2-B0A local source abstention: no result artifact "
            "(score 39 frozen; observed comparison count unchanged)"
        )
        return None
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        renderer.caption(f"V2-B0A local-source abstention artifact refused: {exc}")
        return None
    if not isinstance(result, dict):
        renderer.caption("V2-B0A local-source abstention artifact refused: not an object")
        return None
    renderer.subheader("GV-V2-B0A Local Source Abstention — MU G_supply")
    rows = [
        {
            "label": "slice_classification",
            "value": str(
                result.get("slice_classification", "GV-V2-B0A-LOCAL-SOURCE-ABSTENTION")
            ),
        },
        {"label": "case_id", "value": str(result.get("case_id", CASE_ID))},
        {"label": "admission_status", "value": str(result.get("admission_status"))},
        {
            "label": "primary_block_reason",
            "value": str(result.get("primary_block_reason")),
        },
        {"label": "research_action", "value": str(result.get("research_action"))},
        {"label": "portfolio_action", "value": str(result.get("portfolio_action"))},
        {"label": "decision_id", "value": str(result.get("decision_id"))},
        {"label": "rationale_ref", "value": str(result.get("rationale_ref"))},
        {
            "label": "certification_status",
            "value": str(result.get("certification_status")),
        },
        {
            "label": "observed_comparison_count",
            "value": str(result.get("observed_comparison_count", 0)),
        },
        {
            "label": "shipped_product_score",
            "value": str(result.get("shipped_product_score", 39)),
        },
    ]
    renderer.table(rows)
    renderer.caption(
        "V2-B0A · local research-card admission preflight · "
        "certified source-authority abstention · "
        "not a real external source admission · "
        "no alpha · score 39 frozen · not a G08 observation"
    )
    return dict(result)


__all__ = [
    "DEFAULT_BUNDLE_PATH",
    "DEFAULT_CURRENT_DECISION_PATH",
    "GvFs0PresentationError",
    "build_portfolio_view_model",
    "load_current_certified_decision",
    "load_default_certified_bundle",
    "render_e0b_dv1_surface",
    "render_gv_fs0_certified_bundle",
    "render_gv_fs0_current_decision",
    "render_v2_b0_surface",
    "render_gv_fs0_portfolio",
]
