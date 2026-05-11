from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.families.schemas import CandidateFamilyDefinition
from v2_discovery.families.schemas import CandidateFamilyError
from v2_discovery.families.schemas import FAMILY_REPORT_SCHEMA_VERSION
from v2_discovery.families.schemas import FAMILY_STATUS_DEFINED
from v2_discovery.families.schemas import G7_CODE_REF
from v2_discovery.families.schemas import G7_DATA_TIER_REQUIRED
from v2_discovery.families.schemas import G7_REGISTRY_REPORT_ID
from v2_discovery.families.schemas import outcome_field_names
from v2_discovery.families.trial_budget import validate_trial_budget


G7_REQUIRED_REPORT_FIELDS = (
    "report_schema_version",
    "registry_report_id",
    "family_count",
    "family_ids",
    "manifest_backed",
    "defined_only",
    "candidate_generation_enabled",
    "result_generation_enabled",
    "promotion_ready",
    "alerts_emitted",
    "bro" "ker_calls",
    "promotion_packet_created",
    "blockers",
    "warnings",
    "created_at",
    "code_ref",
)


def validate_family_definition(definition: CandidateFamilyDefinition) -> None:
    if definition.status != FAMILY_STATUS_DEFINED:
        raise CandidateFamilyError("G7 accepts only defined family contracts")
    if definition.data_tier_required != G7_DATA_TIER_REQUIRED:
        raise CandidateFamilyError("G7 family definitions require Tier 0 data policy")
    if definition.source_quality_required != SOURCE_QUALITY_CANONICAL:
        raise CandidateFamilyError("G7 family definitions require canonical source quality")
    if not definition.manifest_uri:
        raise CandidateFamilyError("manifest_uri is required")
    validate_trial_budget(definition)


def validate_manifest_backing(
    *,
    artifact_path: str | Path,
    manifest_path: str | Path,
    definition: CandidateFamilyDefinition,
) -> dict[str, Any]:
    artifact = Path(artifact_path)
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        raise CandidateFamilyError("G7 family definition requires manifest backing")
    if not artifact.exists():
        raise CandidateFamilyError("G7 family artifact does not exist")
    try:
        manifest = load_manifest(manifest_file)
    except Exception as exc:
        raise CandidateFamilyError(f"G7 family manifest failed validation: {exc}") from exc
    declared_path = str(manifest.get("artifact_path") or "").strip()
    if declared_path and Path(declared_path) != artifact:
        raise CandidateFamilyError("G7 family manifest artifact_path mismatch")
    if str(manifest.get("sha256") or "").strip() != compute_sha256(artifact):
        raise CandidateFamilyError("G7 family manifest hash mismatch")
    if manifest.get("source_quality") != SOURCE_QUALITY_CANONICAL:
        raise CandidateFamilyError("G7 family manifest must be canonical")
    if int(manifest.get("row_count")) != 1:
        raise CandidateFamilyError("G7 family manifest row_count mismatch")
    extra = manifest.get("extra") if isinstance(manifest.get("extra"), Mapping) else {}
    if str(extra.get("family_id") or "") != definition.family_id:
        raise CandidateFamilyError("G7 family manifest family_id mismatch")
    if int(extra.get("version") or 0) != definition.version:
        raise CandidateFamilyError("G7 family manifest version mismatch")
    if int(extra.get("trial_budget_max") or 0) != definition.trial_budget_max:
        raise CandidateFamilyError("G7 family manifest trial_budget_max mismatch")
    return dict(manifest)


def validate_registry_report(report: Mapping[str, Any]) -> None:
    missing = [field for field in G7_REQUIRED_REPORT_FIELDS if field not in report]
    if missing:
        raise CandidateFamilyError("G7 registry report missing required field(s): " + ", ".join(missing))
    if report["report_schema_version"] != FAMILY_REPORT_SCHEMA_VERSION:
        raise CandidateFamilyError("G7 registry report schema mismatch")
    if report["registry_report_id"] != G7_REGISTRY_REPORT_ID:
        raise CandidateFamilyError("G7 registry report id mismatch")
    if report["manifest_backed"] is not True:
        raise CandidateFamilyError("G7 registry report requires manifest-backed families")
    if report["defined_only"] is not True:
        raise CandidateFamilyError("G7 registry report must stay definition-only")
    for field in (
        "candidate_generation_enabled",
        "result_generation_enabled",
        "promotion_ready",
        "alerts_emitted",
        "bro" "ker_calls",
        "promotion_packet_created",
    ):
        if report[field] is not False:
            raise CandidateFamilyError(f"G7 registry report field {field} must be false")
    if report["blockers"] != []:
        raise CandidateFamilyError("G7 registry report cannot pass with blockers")
    if report["code_ref"] != G7_CODE_REF:
        raise CandidateFamilyError("G7 registry report code_ref mismatch")
    forbidden = outcome_field_names().intersection(report)
    if forbidden:
        raise CandidateFamilyError("G7 registry report cannot contain outcome fields")
