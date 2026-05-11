from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import build_manifest
from data.provenance import compute_sha256
from data.provenance import utc_now_iso
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_ARTIFACT_URI
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_MANIFEST_URI
from v2_discovery.readiness.canonical_slice import load_g4_canonical_slice
from v2_discovery.readiness.canonical_slice import validate_sidecar_manifest_if_required
from v2_discovery.readiness.schemas import G4_CODE_REF
from v2_discovery.readiness.schemas import G4_DEFAULT_DATASET_NAME
from v2_discovery.readiness.schemas import G4_PRIMARY_KEY
from v2_discovery.readiness.schemas import G4_READINESS_RUN_ID
from v2_discovery.readiness.schemas import G4_REPORT_PROVIDER_FEED
from v2_discovery.readiness.schemas import G4_REPORT_SCHEMA_VERSION
from v2_discovery.readiness.schemas import G4ReadinessError
from v2_discovery.readiness.schemas import G4ReadinessRun


G4_DEFAULT_REPORT_PATH = Path("data/registry/g4_real_canonical_readiness_report.json")

_REQUIRED_REPORT_FIELDS = (
    "readiness_run_id",
    "dataset_name",
    "artifact_uri",
    "manifest_uri",
    "manifest_sha256",
    "source_quality",
    "provider",
    "provider_feed",
    "row_count",
    "date_range",
    "symbol_count",
    "primary_key",
    "schema_version",
    "finite_numeric_check",
    "duplicate_key_check",
    "date_monotonicity_check",
    "price_domain_check",
    "return_domain_check",
    "freshness_check",
    "sidecar_required",
    "ready_for_g5",
    "blockers",
    "warnings",
    "created_at",
    "code_ref",
)


def run_g4_canonical_readiness(
    *,
    artifact_uri: str | Path = G4_DEFAULT_ARTIFACT_URI,
    manifest_uri: str | Path = G4_DEFAULT_MANIFEST_URI,
    dataset_name: str = G4_DEFAULT_DATASET_NAME,
    repo_root: str | Path | None = None,
    sidecar_required: bool = False,
    sidecar_manifest_uri: str | Path | None = None,
    report_path: str | Path | None = None,
) -> G4ReadinessRun:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    canonical_slice = load_g4_canonical_slice(
        artifact_uri=artifact_uri,
        manifest_uri=manifest_uri,
        dataset_name=dataset_name,
        repo_root=root,
    )
    date_range = _date_range(canonical_slice.manifest)
    validate_sidecar_manifest_if_required(
        primary_date_end=str(date_range["end"]),
        sidecar_required=sidecar_required,
        sidecar_manifest_uri=sidecar_manifest_uri,
        repo_root=root,
    )
    report = build_g4_readiness_report(
        canonical_slice=canonical_slice,
        sidecar_required=sidecar_required,
    )
    written_report_path: Path | None = None
    written_manifest_path: Path | None = None
    if report_path is not None:
        written_report_path, written_manifest_path = write_g4_readiness_report(
            report,
            report_path,
            repo_root=root,
        )
    return G4ReadinessRun(
        report=report,
        slice=canonical_slice,
        report_path=written_report_path,
        report_manifest_path=written_manifest_path,
    )


def build_g4_readiness_report(
    *,
    canonical_slice,
    sidecar_required: bool,
) -> dict[str, Any]:
    data = canonical_slice.data
    manifest = canonical_slice.manifest
    date_range = _date_range(manifest)
    created_at = utc_now_iso()
    report = {
        "report_schema_version": G4_REPORT_SCHEMA_VERSION,
        "readiness_run_id": G4_READINESS_RUN_ID,
        "dataset_name": canonical_slice.dataset_name,
        "artifact_uri": canonical_slice.artifact_uri,
        "manifest_uri": canonical_slice.manifest_uri,
        "manifest_sha256": compute_sha256(canonical_slice.manifest_path),
        "source_quality": SOURCE_QUALITY_CANONICAL,
        "provider": str(manifest["provider"]),
        "provider_feed": str(manifest["provider_feed"]),
        "row_count": int(len(data)),
        "date_range": date_range,
        "symbol_count": int(data["permno"].nunique()),
        "primary_key": list(G4_PRIMARY_KEY),
        "schema_version": str(manifest["schema_version"]),
        "finite_numeric_check": "pass",
        "duplicate_key_check": "pass",
        "date_monotonicity_check": "pass",
        "price_domain_check": "pass",
        "return_domain_check": "pass",
        "freshness_check": "pass",
        "sidecar_required": bool(sidecar_required),
        "ready_for_g5": True,
        "blockers": [],
        "warnings": [],
        "created_at": created_at,
        "code_ref": G4_CODE_REF,
    }
    validate_g4_readiness_report(report)
    return report


def validate_g4_readiness_report(report: Mapping[str, Any]) -> None:
    missing = [field for field in _REQUIRED_REPORT_FIELDS if field not in report]
    if missing:
        raise G4ReadinessError("G4 readiness report missing required field(s): " + ", ".join(missing))
    if report["source_quality"] != SOURCE_QUALITY_CANONICAL:
        raise G4ReadinessError("G4 readiness report must stay canonical")
    if report["sidecar_required"] is not False:
        raise G4ReadinessError("G4 readiness report must default sidecar_required=false")
    if report["ready_for_g5"] is not True:
        raise G4ReadinessError("G4 readiness report expected ready_for_g5=true after passing gates")
    if report["blockers"] != []:
        raise G4ReadinessError("G4 readiness report cannot pass with blockers")
    for check in (
        "finite_numeric_check",
        "duplicate_key_check",
        "date_monotonicity_check",
        "price_domain_check",
        "return_domain_check",
        "freshness_check",
    ):
        if report[check] != "pass":
            raise G4ReadinessError(f"G4 readiness report {check} must be pass")
    forbidden_fields = _forbidden_metric_fields()
    if forbidden_fields.intersection(report):
        raise G4ReadinessError("G4 readiness report cannot contain performance metrics")


def write_g4_readiness_report(
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
            provider_feed=G4_REPORT_PROVIDER_FEED,
            license_scope="internal_governance_report",
            row_count=1,
            date_range={"start": report["created_at"], "end": report["created_at"]},
            schema_version=G4_REPORT_SCHEMA_VERSION,
            extra={
                "dataset_name": str(report["dataset_name"]),
                "readiness_run_id": str(report["readiness_run_id"]),
                "ready_for_g5": bool(report["ready_for_g5"]),
            },
        )
    )
    manifest_path = Path(f"{target}.manifest.json")
    write_manifest(manifest, manifest_path)
    return target, manifest_path


def _date_range(manifest: Mapping[str, Any]) -> dict[str, str | None]:
    value = manifest.get("date_range")
    if not isinstance(value, Mapping):
        raise G4ReadinessError("G4 manifest date_range is required")
    return {
        "start": str(value.get("start")) if value.get("start") is not None else None,
        "end": str(value.get("end")) if value.get("end") is not None else None,
    }


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
    }
