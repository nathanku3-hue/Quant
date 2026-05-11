from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.fast_sim.fixtures import SYNTHETIC_FIXTURE_SCOPE
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateEvent
from v2_discovery.schemas import CandidateSpec


G2_LINEAGE_SCHEMA_VERSION = "1.0.0"
G2_LINEAGE_BOUNDARY_VERDICT = ProxyBoundaryVerdict.BLOCKED_FROM_PROMOTION.value
G2_REGISTRY_NOTE_MARKER = "candidate.proxy_run_recorded"
G2_REQUIRED_LINEAGE_FIELDS = (
    "candidate_id",
    "family_id",
    "candidate_event_id",
    "proxy_run_id",
    "registry_note_event_id",
    "registry_note_event_hash",
    "manifest_uri",
    "manifest_sha256",
    "fixture_sha256",
    "source_quality",
    "data_snapshot",
    "code_ref",
    "engine_name",
    "engine_version",
    "promotion_ready",
    "canonical_engine_required",
    "boundary_verdict",
)


def build_g2_lineage_report(
    *,
    registry: CandidateRegistry,
    proxy_result: ProxyRunResult,
    candidate_event_id: str,
) -> dict[str, Any]:
    candidate_event = require_hash_linked_event(
        registry,
        candidate_event_id,
        expected_candidate_id=proxy_result.candidate_id,
    )
    if candidate_event.event_type != "candidate.generated":
        raise ProxyBoundaryError("candidate_event_id must reference candidate.generated")

    registry_note_event = require_hash_linked_event(
        registry,
        proxy_result.registry_note_event_id,
        expected_candidate_id=proxy_result.candidate_id,
    )
    validate_proxy_registry_note(proxy_result, registry_note_event)

    snapshot = registry.rebuild_snapshot()
    if proxy_result.candidate_id not in snapshot:
        raise ProxyBoundaryError("lineage report requires a rebuildable candidate snapshot")
    candidate = snapshot[proxy_result.candidate_id].spec
    _validate_candidate_identity(candidate, proxy_result, repo_root=registry.repo_root)

    manifest_path = _resolve_path(registry.repo_root, proxy_result.manifest_uri)
    manifest = load_manifest(manifest_path)
    fixture_sha256 = _fixture_sha256(registry.repo_root, manifest)

    chain = registry.verify_hash_chain()
    if not chain.get("valid"):
        raise ProxyBoundaryError("lineage report requires a valid registry hash chain")

    report = {
        "schema_version": G2_LINEAGE_SCHEMA_VERSION,
        "candidate_id": proxy_result.candidate_id,
        "family_id": candidate.family_id,
        "candidate_event_id": candidate_event.event_id,
        "candidate_event_hash": candidate_event.event_hash,
        "proxy_run_id": proxy_result.proxy_run_id,
        "registry_note_event_id": registry_note_event.event_id,
        "registry_note_event_hash": registry_note_event.event_hash,
        "manifest_uri": proxy_result.manifest_uri,
        "manifest_sha256": compute_sha256(manifest_path),
        "fixture_sha256": fixture_sha256,
        "source_quality": proxy_result.source_quality,
        "data_snapshot": dict(proxy_result.data_snapshot),
        "code_ref": proxy_result.code_ref,
        "engine_name": proxy_result.engine_name,
        "engine_version": proxy_result.engine_version,
        "promotion_ready": False,
        "canonical_engine_required": True,
        "boundary_verdict": G2_LINEAGE_BOUNDARY_VERDICT,
        "proxy_boundary_verdict": proxy_result.boundary_verdict.value,
        "registry_event_type": registry_note_event.event_type,
        "registry_note_marker": G2_REGISTRY_NOTE_MARKER,
        "hash_chain_valid": True,
        "rebuilt_snapshot_event_count": snapshot[proxy_result.candidate_id].event_count,
        "rebuilt_snapshot_last_event_hash": snapshot[proxy_result.candidate_id].last_event_hash,
        "promotion_packet_blocked": True,
        "signal_packet_blocked": True,
        "order_action_blocked": True,
    }
    validate_g2_lineage_report(report)
    return report


def validate_g2_lineage_report(report: Mapping[str, Any]) -> None:
    missing = [
        field
        for field in G2_REQUIRED_LINEAGE_FIELDS
        if field not in report or report[field] in ("", None)
    ]
    if missing:
        raise ProxyBoundaryError(
            "G2 lineage report missing required field(s): " + ", ".join(missing)
        )
    if report["engine_name"] != PROXY_ENGINE_NAME:
        raise ProxyBoundaryError("G2 lineage engine_name must be v2_proxy")
    if report["promotion_ready"] is not False:
        raise ProxyBoundaryError("G2 lineage must keep promotion_ready=false")
    if report["canonical_engine_required"] is not True:
        raise ProxyBoundaryError("G2 lineage must require a canonical engine rerun")
    if report["boundary_verdict"] != G2_LINEAGE_BOUNDARY_VERDICT:
        raise ProxyBoundaryError("G2 lineage boundary_verdict must be blocked_from_promotion")


def validate_proxy_registry_note(
    proxy_result: ProxyRunResult,
    event: CandidateEvent,
) -> None:
    if event.candidate_id != proxy_result.candidate_id:
        raise ProxyBoundaryError("registry_note_event_id must belong to the same candidate")
    if event.event_type != "candidate.note_added":
        raise ProxyBoundaryError("registry_note_event_id must reference a candidate note")
    note = str(event.payload.get("note", ""))
    required_tokens = (
        G2_REGISTRY_NOTE_MARKER,
        proxy_result.proxy_run_id,
        proxy_result.boundary_verdict.value,
        "promotion_ready=false",
        "canonical_engine_required=true",
    )
    missing = [token for token in required_tokens if token not in note]
    if missing:
        raise ProxyBoundaryError(
            "registry note missing required lineage token(s): " + ", ".join(missing)
        )


def require_hash_linked_event(
    registry: CandidateRegistry,
    event_id: str,
    *,
    expected_candidate_id: str,
) -> CandidateEvent:
    previous_hash = "GENESIS"
    for event in load_registry_events(registry):
        if event.previous_event_hash != previous_hash:
            raise ProxyBoundaryError("registry event hash chain is broken")
        if event.recompute_hash() != event.event_hash:
            raise ProxyBoundaryError("registry event hash does not match event body")
        if event.event_id == event_id:
            if event.candidate_id != expected_candidate_id:
                raise ProxyBoundaryError("registry event candidate_id does not match")
            return event
        previous_hash = event.event_hash
    raise ProxyBoundaryError(f"registry event does not exist: {event_id}")


def find_candidate_event(
    registry: CandidateRegistry,
    *,
    candidate_id: str,
    event_type: str = "candidate.generated",
) -> CandidateEvent:
    for event in load_registry_events(registry):
        if event.candidate_id == candidate_id and event.event_type == event_type:
            return event
    raise ProxyBoundaryError(f"{event_type} event does not exist for candidate_id={candidate_id}")


def load_registry_events(registry: CandidateRegistry) -> tuple[CandidateEvent, ...]:
    if not registry.event_log_path.exists():
        return ()
    events: list[CandidateEvent] = []
    with registry.event_log_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            clean = line.strip()
            if not clean:
                continue
            try:
                events.append(CandidateEvent.from_dict(json.loads(clean)))
            except (TypeError, json.JSONDecodeError) as exc:
                raise ProxyBoundaryError(
                    f"Invalid registry event at line {line_number}: {exc}"
                ) from exc
    return tuple(events)


def _validate_candidate_identity(
    candidate: CandidateSpec,
    proxy_result: ProxyRunResult,
    *,
    repo_root: Path,
) -> None:
    if candidate.candidate_id != proxy_result.candidate_id:
        raise ProxyBoundaryError("candidate snapshot does not match proxy result")
    if candidate.manifest_uri != proxy_result.manifest_uri:
        raise ProxyBoundaryError("candidate manifest_uri does not match proxy result")
    if candidate.source_quality != proxy_result.source_quality:
        raise ProxyBoundaryError("candidate source_quality does not match proxy result")
    if not candidate.code_ref:
        raise ProxyBoundaryError("candidate code_ref is required")
    if not candidate.data_snapshot:
        raise ProxyBoundaryError("candidate data_snapshot is required")
    manifest_path = _resolve_path(repo_root, candidate.manifest_uri)
    declared_manifest_hash = str(candidate.data_snapshot.get("manifest_sha256", "")).strip()
    if not declared_manifest_hash:
        raise ProxyBoundaryError("candidate data_snapshot.manifest_sha256 is required")
    if not manifest_path.exists():
        raise ProxyBoundaryError("candidate manifest_uri does not exist")
    if declared_manifest_hash != compute_sha256(manifest_path):
        raise ProxyBoundaryError("candidate data_snapshot.manifest_sha256 mismatch")
    if candidate.trial_count != 1:
        raise ProxyBoundaryError("G2 requires exactly one registered fixture trial")


def _fixture_sha256(repo_root: Path, manifest: Mapping[str, Any]) -> str:
    extra = manifest.get("extra")
    if not isinstance(extra, Mapping) or extra.get("fixture_scope") != SYNTHETIC_FIXTURE_SCOPE:
        raise ProxyBoundaryError("G2 lineage requires the G1 synthetic fixture manifest")
    artifact_path = str(manifest.get("artifact_path", "")).strip()
    if not artifact_path:
        raise ProxyBoundaryError("G2 lineage manifest requires artifact_path")
    return compute_sha256(_resolve_path(repo_root, artifact_path))


def _resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path
