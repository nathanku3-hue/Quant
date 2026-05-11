from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import build_manifest
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.replay.real_slice_v1_v2_comparison import G6_CODE_REF
from v2_discovery.replay.real_slice_v1_v2_comparison import G6_COMPARISON_FIELDS
from v2_discovery.replay.real_slice_v1_v2_comparison import G6ComparisonError
from v2_discovery.replay.real_slice_v1_v2_comparison import G6MechanicalComparison


G6_REPORT_SCHEMA_VERSION = "1.0.0"
G6_REPORT_PROVIDER_FEED = "g6_v1_v2_real_slice_mechanical_report"

_REQUIRED_REPORT_FIELDS = (
    "report_schema_version",
    "comparison_run_id",
    "dataset_name",
    "artifact_uri",
    "manifest_uri",
    "manifest_sha256",
    "source_quality",
    "row_count",
    "symbol_count",
    "date_range",
    "engine_name",
    "engine_version",
    "positions",
    "cash",
    "turnover",
    "transaction_cost",
    "gross_exposure",
    "net_exposure",
    "comparison_fields",
    "field_results",
    "comparison_result",
    "mismatch_count",
    "mismatch_fields",
    "mechanical_comparison_result",
    "promotion_ready",
    "v2_promotion_ready",
    "canonical_engine_required",
    "alerts_emitted",
    "broker_calls",
    "blockers",
    "warnings",
    "code_ref",
)


def build_g6_mechanical_comparison_report(comparison: G6MechanicalComparison) -> dict[str, Any]:
    v1 = comparison.v1_output
    v2 = comparison.v2_output
    result = comparison.comparison
    report = {
        "report_schema_version": G6_REPORT_SCHEMA_VERSION,
        "comparison_run_id": comparison.comparison_run_id,
        "dataset_name": comparison.dataset_name,
        "artifact_uri": comparison.artifact_uri,
        "manifest_uri": comparison.manifest_uri,
        "manifest_sha256": comparison.manifest_sha256,
        "source_quality": comparison.source_quality,
        "row_count": comparison.row_count,
        "symbol_count": comparison.symbol_count,
        "date_range": dict(comparison.date_range),
        "engine_name": {"v1": v1.engine_name, "v2": v2.engine_name},
        "engine_version": {"v1": v1.engine_version, "v2": v2.engine_version},
        "positions": {"v1": _position_records(v1.positions), "v2": _position_records(v2.positions)},
        "cash": {"v1": _series_records(v1.ledger, "cash"), "v2": _series_records(v2.ledger, "cash")},
        "turnover": {
            "v1": _series_records(v1.ledger, "turnover"),
            "v2": _series_records(v2.ledger, "turnover"),
        },
        "transaction_cost": {
            "v1": _series_records(v1.ledger, "transaction_cost"),
            "v2": _series_records(v2.ledger, "transaction_cost"),
        },
        "gross_exposure": {
            "v1": _series_records(v1.ledger, "gross_exposure"),
            "v2": _series_records(v2.ledger, "gross_exposure"),
        },
        "net_exposure": {
            "v1": _series_records(v1.ledger, "net_exposure"),
            "v2": _series_records(v2.ledger, "net_exposure"),
        },
        "comparison_fields": list(result["comparison_fields"]),
        "equality_fields": list(result["equality_fields"]),
        "identity_fields": list(result["identity_fields"]),
        "field_results": dict(result["field_results"]),
        "comparison_result": result["comparison_result"],
        "mismatch_count": int(result["mismatch_count"]),
        "mismatch_fields": list(result["mismatch_fields"]),
        "mechanical_comparison_result": result["comparison_result"],
        "promotion_ready": False,
        "v2_promotion_ready": False,
        "canonical_engine_required": True,
        "alerts_emitted": False,
        "broker_calls": False,
        "blockers": [] if result["comparison_result"] == "match" else list(result["mismatch_fields"]),
        "warnings": [],
        "code_ref": G6_CODE_REF,
    }
    validate_g6_mechanical_comparison_report(report)
    return report


def validate_g6_mechanical_comparison_report(report: Mapping[str, Any]) -> None:
    missing = [field for field in _REQUIRED_REPORT_FIELDS if field not in report]
    if missing:
        raise G6ComparisonError("G6 comparison report missing required field(s): " + ", ".join(missing))
    if report["source_quality"] != SOURCE_QUALITY_CANONICAL:
        raise G6ComparisonError("G6 comparison report requires canonical source_quality")
    engine_name = report["engine_name"]
    if not isinstance(engine_name, Mapping):
        raise G6ComparisonError("G6 comparison report requires engine_name mapping")
    if engine_name.get("v1") != V1_CANONICAL_ENGINE_NAME:
        raise G6ComparisonError("G6 comparison report requires V1 canonical engine")
    if engine_name.get("v2") != PROXY_ENGINE_NAME:
        raise G6ComparisonError("G6 comparison report requires V2 proxy engine")
    if tuple(report["comparison_fields"]) != G6_COMPARISON_FIELDS:
        raise G6ComparisonError("G6 comparison report contains unapproved comparison fields")
    if report["promotion_ready"] is not False or report["v2_promotion_ready"] is not False:
        raise G6ComparisonError("G6 comparison report cannot be promotion ready")
    if report["canonical_engine_required"] is not True:
        raise G6ComparisonError("G6 comparison report must keep canonical engine required")
    if report["alerts_emitted"] is not False:
        raise G6ComparisonError("G6 comparison report cannot emit alerts")
    if report["broker_calls"] is not False:
        raise G6ComparisonError("G6 comparison report cannot contain broker calls")
    if report["comparison_result"] == "match" and report["mismatch_count"] != 0:
        raise G6ComparisonError("G6 comparison match cannot contain mismatches")
    forbidden = _forbidden_output_fields()
    if forbidden.intersection(_all_keys(report)):
        raise G6ComparisonError("G6 comparison report cannot contain forbidden output fields")


def write_g6_mechanical_comparison_report(
    report: Mapping[str, Any],
    report_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> tuple[Path, Path]:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    target = _resolve_path(root, report_path)
    write_json_atomic(dict(report), target)
    artifact_path: str | Path = target
    try:
        artifact_path = target.relative_to(root)
    except ValueError:
        pass
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact_path,
            source_quality=SOURCE_QUALITY_CANONICAL,
            provider="terminal_zero",
            provider_feed=G6_REPORT_PROVIDER_FEED,
            license_scope="internal_governance_report",
            row_count=1,
            date_range=report["date_range"],
            schema_version=G6_REPORT_SCHEMA_VERSION,
            extra={
                "dataset_name": str(report["dataset_name"]),
                "comparison_run_id": str(report["comparison_run_id"]),
                "comparison_result": str(report["comparison_result"]),
                "v2_promotion_ready": False,
            },
        )
    )
    manifest_path = Path(f"{target}.manifest.json")
    write_manifest(manifest, manifest_path)
    return target, manifest_path


def _position_records(positions) -> list[dict[str, Any]]:
    ordered = positions.sort_values(["date", "permno"], kind="mergesort")
    return [
        {
            "date": str(row.date),
            "permno": int(row.permno),
            "quantity": _round_float(row.quantity),
            "market_value": _round_float(row.market_value),
        }
        for row in ordered[["date", "permno", "quantity", "market_value"]].itertuples(index=False)
    ]


def _series_records(ledger, column: str) -> list[dict[str, Any]]:
    return [
        {"date": str(row.date), "value": _round_float(getattr(row, column))}
        for row in ledger[["date", column]].itertuples(index=False)
    ]


def _all_keys(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        keys = {str(key) for key in value}
        for item in value.values():
            keys.update(_all_keys(item))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_all_keys(item))
        return keys
    return set()


def _forbidden_output_fields() -> set[str]:
    return {
        "al" "pha",
        "ca" "gr",
        "draw" "down",
        "max_" "draw" "down",
        "p" "nl",
        "ra" "nk",
        "sco" "re",
        "sha" "rpe",
        "signal_" "strength",
        "buy_" "sell_decision",
        "paper_" "alert",
        "promotion_" "verdict",
        "gross_" "ret",
        "net_" "ret",
    }


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _round_float(value: Any) -> float:
    return round(float(value), 6)
