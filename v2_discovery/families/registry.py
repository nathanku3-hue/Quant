from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import build_manifest
from data.provenance import utc_now_iso
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.families.schemas import CandidateFamilyDefinition
from v2_discovery.families.schemas import CandidateFamilyError
from v2_discovery.families.schemas import FAMILY_REPORT_SCHEMA_VERSION
from v2_discovery.families.schemas import FAMILY_SCHEMA_VERSION
from v2_discovery.families.schemas import FAMILY_STATUS_DEFINED
from v2_discovery.families.schemas import G7_CODE_REF
from v2_discovery.families.schemas import G7_CREATED_BY
from v2_discovery.families.schemas import G7_DATA_TIER_REQUIRED
from v2_discovery.families.schemas import G7_DEFAULT_FAMILY_PATH
from v2_discovery.families.schemas import G7_DEFAULT_REPORT_PATH
from v2_discovery.families.schemas import G7_FAMILY_ID
from v2_discovery.families.schemas import G7_FAMILY_NAME
from v2_discovery.families.schemas import G7_REGISTRY_REPORT_ID
from v2_discovery.families.schemas import G7_SOURCE_QUALITY_REQUIRED
from v2_discovery.families.validation import validate_family_definition
from v2_discovery.families.validation import validate_manifest_backing
from v2_discovery.families.validation import validate_registry_report


DEFAULT_FAMILY_ROOT = Path("data/registry/candidate_families")


@dataclass(frozen=True)
class FamilyArtifactWrite:
    definition_path: Path
    manifest_path: Path
    report_path: Path | None = None


class CandidateFamilyRegistry:
    def __init__(
        self,
        root_path: str | Path = DEFAULT_FAMILY_ROOT,
        *,
        repo_root: str | Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else Path.cwd()
        self.root_path = self._resolve_path(root_path)

    def register_family(self, definition: CandidateFamilyDefinition) -> tuple[Path, Path]:
        validate_family_definition(definition)
        target = self.path_for(definition.family_id)
        manifest_path = Path(f"{target}.manifest.json")
        self._validate_manifest_uri(definition, manifest_path)
        payload = definition.to_dict()
        if target.exists():
            existing = self._load_json(target)
            if existing != payload:
                raise CandidateFamilyError("G7 family definitions are append-only; create a new version")
            validate_manifest_backing(
                artifact_path=target,
                manifest_path=manifest_path,
                definition=definition,
            )
            return target, manifest_path

        target.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(payload, target)
        manifest = build_manifest(
            ManifestInput(
                artifact_path=target,
                source_quality=SOURCE_QUALITY_CANONICAL,
                provider="terminal_zero",
                provider_feed="candidate_family_definition",
                license_scope="internal_research_governance",
                row_count=1,
                date_range={"start": definition.created_at, "end": definition.created_at},
                schema_version=FAMILY_SCHEMA_VERSION,
                extra={
                    "family_id": definition.family_id,
                    "version": definition.version,
                    "status": definition.status,
                    "data_tier_required": definition.data_tier_required,
                    "source_quality_required": definition.source_quality_required,
                    "trial_budget_max": definition.trial_budget_max,
                    "finite_trial_count": definition.finite_trial_count,
                    "primary_key": ["family_id", "version"],
                },
            )
        )
        write_manifest(manifest, manifest_path)
        validate_manifest_backing(
            artifact_path=target,
            manifest_path=manifest_path,
            definition=definition,
        )
        return target, manifest_path

    def load_family(self, family_id: str) -> CandidateFamilyDefinition:
        target = self.path_for(family_id)
        if not target.exists():
            raise CandidateFamilyError("Family definition must exist before candidate creation")
        payload = self._load_json(target)
        definition = CandidateFamilyDefinition.from_dict(payload)
        manifest_path = Path(f"{target}.manifest.json")
        self._validate_manifest_uri(definition, manifest_path)
        validate_manifest_backing(
            artifact_path=target,
            manifest_path=manifest_path,
            definition=definition,
        )
        return definition

    def require_family_for_candidate(self, family_id: str) -> CandidateFamilyDefinition:
        definition = self.load_family(family_id)
        if definition.trial_budget_max <= 0:
            raise CandidateFamilyError("trial_budget_max is required before candidate creation")
        return definition

    def path_for(self, family_id: str) -> Path:
        if family_id == G7_FAMILY_ID:
            return self.root_path / G7_DEFAULT_FAMILY_PATH.name
        safe_name = str(family_id).strip().lower()
        if not safe_name:
            raise CandidateFamilyError("family_id is required")
        return self.root_path / f"{safe_name}.json"

    def list_families(self) -> list[CandidateFamilyDefinition]:
        if not self.root_path.exists():
            return []
        definitions = []
        for path in sorted(self.root_path.glob("*.json")):
            if path.name.endswith(".manifest.json"):
                continue
            try:
                definitions.append(CandidateFamilyDefinition.from_dict(self._load_json(path)))
            except CandidateFamilyError:
                raise
        return definitions

    def write_registry_report(
        self,
        path: str | Path = G7_DEFAULT_REPORT_PATH,
        *,
        definitions: Iterable[CandidateFamilyDefinition] | None = None,
    ) -> Path:
        target = self._resolve_path(path)
        families = list(definitions) if definitions is not None else self.list_families()
        for definition in families:
            self._validate_definition_manifest(definition)
        report = build_registry_report(families, manifest_backed_verified=True)
        write_json_atomic(report, target)
        return target

    def _validate_manifest_uri(self, definition: CandidateFamilyDefinition, manifest_path: Path) -> None:
        expected = self._relative_or_absolute(manifest_path)
        actual = Path(definition.manifest_uri)
        if actual.is_absolute():
            actual_text = str(actual)
        else:
            actual_text = actual.as_posix()
        expected_text = str(expected) if isinstance(expected, Path) else expected
        if actual_text != expected_text:
            raise CandidateFamilyError("G7 family manifest_uri mismatch")

    def _validate_definition_manifest(self, definition: CandidateFamilyDefinition) -> None:
        target = self.path_for(definition.family_id)
        manifest_path = Path(f"{target}.manifest.json")
        self._validate_manifest_uri(definition, manifest_path)
        validate_manifest_backing(
            artifact_path=target,
            manifest_path=manifest_path,
            definition=definition,
        )

    def _resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.repo_root / path

    def _relative_or_absolute(self, value: Path) -> str:
        try:
            return value.relative_to(self.repo_root).as_posix()
        except ValueError:
            return str(value)

    def _load_json(self, path: Path) -> dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise CandidateFamilyError(f"G7 family artifact must be a JSON object: {path}")
        return payload


def build_pead_daily_v0_definition(
    *,
    repo_root: str | Path | None = None,
    created_at: str | None = None,
    manifest_uri: str | Path = Path(f"{G7_DEFAULT_FAMILY_PATH}.manifest.json"),
) -> CandidateFamilyDefinition:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    manifest_text = _relative_or_absolute(root, Path(manifest_uri))
    parameter_space = {
        "holding_days": [1, 3, 5, 10],
        "liquidity_floor": ["adv_usd_5m", "adv_usd_20m", "adv_usd_50m"],
        "event_window_lag": [1, 2],
    }
    return CandidateFamilyDefinition(
        family_id=G7_FAMILY_ID,
        family_name=G7_FAMILY_NAME,
        research_question=(
            "Can post-earnings announcement drift persist after liquidity, cost, "
            "and canonical-data controls?"
        ),
        hypothesis=(
            "Post-earnings announcement drift may persist after controlling for "
            "liquidity, cost, and survivorship-safe canonical data."
        ),
        universe="US_EQUITIES_DAILY_CANONICAL",
        asset_class="us_equities",
        bar_frequency="daily",
        data_tier_required=G7_DATA_TIER_REQUIRED,
        source_quality_required=G7_SOURCE_QUALITY_REQUIRED,
        sidecar_required=False,
        allowed_features=(
            "earnings_event_flag",
            "earnings_surprise_bucket",
            "liquidity_filter",
            "price_return_window",
        ),
        forbidden_features=(
            "future_return",
            "forward_label",
            "survivorship_unsafe_universe",
            "post_result_parameter_pick",
        ),
        parameter_space=parameter_space,
        trial_budget_max=24,
        cost_model={
            "commission_bps": 0,
            "slippage_bps": 10,
            "borrow_cost_policy": "not_applicable_for_definition",
        },
        validation_gates_required=(
            "OOS",
            "walk_forward",
            "regime_tests",
            "permutation",
            "bootstrap",
        ),
        multiple_testing_policy={
            "procedure": "benjamini_hochberg_fdr",
            "planned_tests_only": True,
            "family_scope": G7_FAMILY_ID,
            "trial_budget_max": 24,
            "future_required": [
                "multiple_testing",
                "PSR_or_DSR",
                "reality_check_or_SPA",
            ],
        },
        promotion_policy={
            "promotion_ready": False,
            "candidate_generation_allowed": False,
            "allowed_promotion_data_tiers": ["tier0"],
            "allowed_promotion_source_quality": ["canonical"],
            "forbidden_promotion_sources": [
                "tier2",
                "yfinance",
                "openbb",
                "operational_market_data",
            ],
            "future_decision_required": "G8_or_hold",
        },
        created_at=created_at or utc_now_iso(),
        created_by=G7_CREATED_BY,
        code_ref=G7_CODE_REF,
        manifest_uri=manifest_text,
        status=FAMILY_STATUS_DEFINED,
    )


def write_g7_default_artifacts(
    *,
    repo_root: str | Path | None = None,
    report_path: str | Path = G7_DEFAULT_REPORT_PATH,
) -> FamilyArtifactWrite:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    registry = CandidateFamilyRegistry(repo_root=root)
    definition_path = registry.path_for(G7_FAMILY_ID)
    if definition_path.exists():
        definition = registry.load_family(G7_FAMILY_ID)
        manifest_path = Path(f"{definition_path}.manifest.json")
    else:
        definition = build_pead_daily_v0_definition(repo_root=root)
        definition_path, manifest_path = registry.register_family(definition)
    written_report = registry.write_registry_report(report_path, definitions=[definition])
    return FamilyArtifactWrite(
        definition_path=definition_path,
        manifest_path=manifest_path,
        report_path=written_report,
    )


def build_registry_report(
    definitions: Iterable[CandidateFamilyDefinition],
    *,
    manifest_backed_verified: bool = False,
) -> dict[str, Any]:
    if not manifest_backed_verified:
        raise CandidateFamilyError("G7 registry report requires verified manifest backing")
    families = sorted(definitions, key=lambda item: item.family_id)
    report = {
        "report_schema_version": FAMILY_REPORT_SCHEMA_VERSION,
        "registry_report_id": G7_REGISTRY_REPORT_ID,
        "family_count": len(families),
        "family_ids": [item.family_id for item in families],
        "families": [
            {
                "family_id": item.family_id,
                "version": item.version,
                "status": item.status,
                "manifest_uri": item.manifest_uri,
                "trial_budget_max": item.trial_budget_max,
                "finite_trial_count": item.finite_trial_count,
                "data_tier_required": item.data_tier_required,
                "source_quality_required": item.source_quality_required,
                "sidecar_required": item.sidecar_required,
            }
            for item in families
        ],
        "manifest_backed": manifest_backed_verified,
        "defined_only": True,
        "candidate_generation_enabled": False,
        "result_generation_enabled": False,
        "promotion_ready": False,
        "alerts_emitted": False,
        "bro" "ker_calls": False,
        "promotion_packet_created": False,
        "blockers": [],
        "warnings": [],
        "created_at": utc_now_iso(),
        "code_ref": G7_CODE_REF,
    }
    validate_registry_report(report)
    return report


def block_candidate_materialization(*, family_id: str, reason: str = "phase_g7_definition_only") -> None:
    if not family_id:
        raise CandidateFamilyError("family_id is required")
    raise CandidateFamilyError(f"G7 cannot materialize a candidate: {reason}")


def block_result_path(*, family_id: str, action: str) -> None:
    if not family_id:
        raise CandidateFamilyError("family_id is required")
    clean_action = str(action).strip() or "result_path"
    raise CandidateFamilyError(f"G7 cannot execute {clean_action}; family definition only")


def _relative_or_absolute(root: Path, value: Path) -> str:
    target = value if value.is_absolute() else root / value
    try:
        return target.relative_to(root).as_posix()
    except ValueError:
        return str(target)
