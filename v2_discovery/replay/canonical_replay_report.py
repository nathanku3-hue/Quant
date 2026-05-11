from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import build_manifest
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.replay.canonical_real_replay import G5_CODE_REF
from v2_discovery.replay.canonical_real_replay import G5MechanicalReplay
from v2_discovery.replay.canonical_real_replay import G5ReplayError


G5_REPORT_SCHEMA_VERSION = "1.0.0"
G5_REPORT_PROVIDER_FEED = "g5_single_canonical_replay_report"

_REQUIRED_REPORT_FIELDS = (
    "replay_run_id",
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
    "mechanical_replay_result",
    "blockers",
    "warnings",
    "promotion_ready",
    "alerts_emitted",
    "broker_calls",
    "code_ref",
)


def build_g5_replay_report(replay: G5MechanicalReplay) -> dict[str, Any]:
    ledger = replay.ledger
    report = {
        "report_schema_version": G5_REPORT_SCHEMA_VERSION,
        "replay_run_id": replay.replay_run_id,
        "dataset_name": replay.dataset_name,
        "artifact_uri": replay.artifact_uri,
        "manifest_uri": replay.manifest_uri,
        "manifest_sha256": replay.manifest_sha256,
        "source_quality": replay.source_quality,
        "row_count": replay.row_count,
        "symbol_count": replay.symbol_count,
        "date_range": dict(replay.date_range),
        "engine_name": replay.engine_name,
        "engine_version": replay.engine_version,
        "positions": _position_records(replay.positions),
        "cash": _series_records(ledger, "cash"),
        "turnover": _series_records(ledger, "turnover"),
        "transaction_cost": _series_records(ledger, "transaction_cost"),
        "gross_exposure": _series_records(ledger, "gross_exposure"),
        "net_exposure": _series_records(ledger, "net_exposure"),
        "mechanical_replay_result": "completed",
        "blockers": [],
        "warnings": [],
        "promotion_ready": False,
        "alerts_emitted": False,
        "broker_calls": False,
        "code_ref": G5_CODE_REF,
    }
    validate_g5_replay_report(report)
    return report


def validate_g5_replay_report(report: Mapping[str, Any]) -> None:
    missing = [field for field in _REQUIRED_REPORT_FIELDS if field not in report]
    if missing:
        raise G5ReplayError("G5 replay report missing required field(s): " + ", ".join(missing))
    if report["source_quality"] != SOURCE_QUALITY_CANONICAL:
        raise G5ReplayError("G5 replay report requires canonical source_quality")
    if report["engine_name"] != V1_CANONICAL_ENGINE_NAME:
        raise G5ReplayError("G5 replay report requires core engine output")
    if report["mechanical_replay_result"] != "completed":
        raise G5ReplayError("G5 replay report did not complete")
    if report["blockers"] != []:
        raise G5ReplayError("G5 replay report cannot pass with blockers")
    if report["promotion_ready"] is not False:
        raise G5ReplayError("G5 replay report cannot be promotion ready")
    if report["alerts_emitted"] is not False:
        raise G5ReplayError("G5 replay report cannot emit alerts")
    if report["broker_calls"] is not False:
        raise G5ReplayError("G5 replay report cannot contain broker calls")
    forbidden_fields = _forbidden_metric_fields()
    if forbidden_fields.intersection(report):
        raise G5ReplayError("G5 replay report cannot contain performance metrics")


def write_g5_replay_report(
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
            provider_feed=G5_REPORT_PROVIDER_FEED,
            license_scope="internal_governance_report",
            row_count=1,
            date_range=report["date_range"],
            schema_version=G5_REPORT_SCHEMA_VERSION,
            extra={
                "dataset_name": str(report["dataset_name"]),
                "replay_run_id": str(report["replay_run_id"]),
                "mechanical_replay_result": str(report["mechanical_replay_result"]),
                "promotion_ready": False,
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


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _forbidden_metric_fields() -> set[str]:
    return {
        "al" "pha",
        "ca" "gr",
        "draw" "down",
        "max_" "draw" "down",
        "p" "nl",
        "ra" "nk",
        "sco" "re",
        "sha" "rpe",
        "gross_ret",
        "net_ret",
    }


def _round_float(value: Any) -> float:
    return round(float(value), 6)
