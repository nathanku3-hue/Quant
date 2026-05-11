from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from data.provenance import compute_sha256
from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import build_manifest
from data.provenance import load_manifest
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.fast_sim.boundary import V2ProxyBoundary
from v2_discovery.fast_sim.cost_model import FastProxyCostModel
from v2_discovery.fast_sim.fixtures import SYNTHETIC_FIXTURE_ROOT
from v2_discovery.fast_sim.fixtures import SYNTHETIC_FIXTURE_SCOPE
from v2_discovery.fast_sim.fixtures import load_synthetic_proxy_fixture
from v2_discovery.fast_sim.ledger import build_synthetic_ledger
from v2_discovery.fast_sim.ledger import validate_synthetic_ledger_output
from v2_discovery.fast_sim.lineage import G2_REGISTRY_NOTE_MARKER
from v2_discovery.fast_sim.lineage import build_g2_lineage_report
from v2_discovery.fast_sim.lineage import find_candidate_event
from v2_discovery.fast_sim.lineage import load_registry_events
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.schemas import ProxyRunStatus
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateEvent
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


G2_SYNTHETIC_CANDIDATE_ID = "PH65_G2_SYNTHETIC_FIXTURE_001"
G2_SYNTHETIC_FAMILY_ID = "PH65_G2_SINGLE_REGISTERED_FIXTURE"
G2_PROXY_RUN_ID = "PH65_G2_SINGLE_FIXTURE_PROXY_RUN_001"
G2_CODE_REF = "v2_discovery/fast_sim/run_candidate_proxy.py@phase65-g2"
G2_CREATED_AT = "2026-05-09T00:00:00Z"
G2_DEFAULT_REPORT_PATH = Path("data/registry/g2_single_fixture_candidate_report.json")
G2_SYNTHETIC_MANIFEST_URI = SYNTHETIC_FIXTURE_ROOT / "synthetic_manifest.json"


@dataclass(frozen=True)
class G2CandidateProxyRun:
    proxy_result: ProxyRunResult
    lineage_report: dict[str, Any]
    positions_rows: int
    ledger_rows: int
    snapshot_path: Path | None = None
    report_path: Path | None = None
    report_manifest_path: Path | None = None


def run_g2_single_fixture_candidate(
    *,
    registry: CandidateRegistry | None = None,
    actor: str = "phase65_g2",
    report_path: str | Path | None = G2_DEFAULT_REPORT_PATH,
) -> G2CandidateProxyRun:
    active_registry = registry or CandidateRegistry()
    candidate, candidate_event = register_or_load_g2_fixture_candidate(
        active_registry,
        actor=actor,
    )
    return run_registered_candidate_proxy(
        active_registry,
        candidate_id=candidate.candidate_id,
        actor=actor,
        report_path=report_path,
        candidate_event_id=candidate_event.event_id,
    )


def register_or_load_g2_fixture_candidate(
    registry: CandidateRegistry,
    *,
    actor: str,
) -> tuple[CandidateSpec, CandidateEvent]:
    fixture_candidates = _fixture_candidate_ids(registry)
    if len(fixture_candidates) > 1:
        raise ProxyBoundaryError("G2 requires exactly one synthetic fixture candidate")
    if fixture_candidates:
        candidate_id = fixture_candidates[0]
        snapshot = registry.rebuild_snapshot()[candidate_id]
        event = find_candidate_event(registry, candidate_id=candidate_id)
        validate_g2_fixture_candidate(snapshot.spec, repo_root=registry.repo_root)
        return snapshot.spec, event

    candidate = build_g2_fixture_candidate(repo_root=registry.repo_root)
    event = registry.register_candidate(candidate, actor=actor)
    return candidate, event


def run_registered_candidate_proxy(
    registry: CandidateRegistry,
    *,
    candidate_id: str = G2_SYNTHETIC_CANDIDATE_ID,
    actor: str = "phase65_g2",
    report_path: str | Path | None = None,
    candidate_event_id: str | None = None,
) -> G2CandidateProxyRun:
    snapshot = registry.rebuild_snapshot()
    if candidate_id not in snapshot:
        raise ProxyBoundaryError("G2 requires existing registered fixture candidate")
    fixture_candidates = _fixture_candidate_ids(registry)
    if len(fixture_candidates) != 1 or fixture_candidates[0] != candidate_id:
        raise ProxyBoundaryError("G2 runs exactly one synthetic fixture candidate only")

    candidate = snapshot[candidate_id].spec
    validate_g2_fixture_candidate(candidate, repo_root=registry.repo_root)
    candidate_event = (
        find_candidate_event(registry, candidate_id=candidate_id)
        if candidate_event_id is None
        else _candidate_event_from_id(registry, candidate_event_id, candidate_id)
    )
    spec = build_proxy_spec_for_registered_candidate(
        registry,
        candidate,
        candidate_event_id=candidate_event.event_id,
    )
    proxy_result, positions_rows, ledger_rows = _run_proxy_and_record_note(
        registry,
        spec,
        actor=actor,
    )
    lineage_report = build_g2_lineage_report(
        registry=registry,
        proxy_result=proxy_result,
        candidate_event_id=candidate_event.event_id,
    )
    snapshot_path = registry.write_snapshot()
    written_report_path: Path | None = None
    written_manifest_path: Path | None = None
    if report_path is not None:
        written_report_path, written_manifest_path = write_g2_lineage_artifact(
            lineage_report,
            report_path,
            repo_root=registry.repo_root,
        )
    return G2CandidateProxyRun(
        proxy_result=proxy_result,
        lineage_report=lineage_report,
        positions_rows=positions_rows,
        ledger_rows=ledger_rows,
        snapshot_path=snapshot_path,
        report_path=written_report_path,
        report_manifest_path=written_manifest_path,
    )


def build_g2_fixture_candidate(
    *,
    repo_root: str | Path | None = None,
    candidate_id: str = G2_SYNTHETIC_CANDIDATE_ID,
    manifest_uri: str | Path = G2_SYNTHETIC_MANIFEST_URI,
) -> CandidateSpec:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    manifest_path = _resolve_path(root, manifest_uri)
    manifest = load_manifest(manifest_path)
    _validate_synthetic_manifest_for_g2(manifest)
    return CandidateSpec(
        candidate_id=candidate_id,
        family_id=G2_SYNTHETIC_FAMILY_ID,
        hypothesis="Synthetic fixture lineage proof only; no edge claim.",
        universe="SYNTHETIC_TWO_SYMBOL",
        features=("prebaked_target_weight",),
        parameters_searched={"registered_fixture_only": [True]},
        trial_count=1,
        train_window={"start": "2020-01-02", "end": "2020-01-03"},
        test_window={"start": "2020-01-02", "end": "2020-01-03"},
        cost_model={
            "initial_cash": 100000.0,
            "total_cost_bps": 10.0,
            "max_gross_exposure": 1.0,
        },
        data_snapshot={
            "dataset": "g1_synthetic_v2_proxy_fixture",
            "asof": "2026-05-09",
            "manifest_sha256": _manifest_sha256(manifest_path),
        },
        manifest_uri=Path(manifest_uri).as_posix(),
        source_quality=SOURCE_QUALITY_NON_CANONICAL,
        created_at=G2_CREATED_AT,
        created_by="phase65_g2",
        code_ref=G2_CODE_REF,
        status=CandidateStatus.GENERATED,
    )


def build_proxy_spec_for_registered_candidate(
    registry: CandidateRegistry,
    candidate: CandidateSpec,
    *,
    candidate_event_id: str,
) -> ProxyRunSpec:
    snapshot = registry.rebuild_snapshot()
    if candidate.candidate_id not in snapshot:
        raise ProxyBoundaryError("G2 rejects unregistered candidate")
    if snapshot[candidate.candidate_id].spec != candidate:
        raise ProxyBoundaryError("G2 candidate spec must match the registry snapshot")
    validate_g2_fixture_candidate(candidate, repo_root=registry.repo_root)
    return ProxyRunSpec(
        proxy_run_id=G2_PROXY_RUN_ID,
        candidate_id=candidate.candidate_id,
        registry_event_id=candidate_event_id,
        manifest_uri=candidate.manifest_uri,
        source_quality=candidate.source_quality,
        data_snapshot=dict(candidate.data_snapshot),
        code_ref=candidate.code_ref,
        engine_name=PROXY_ENGINE_NAME,
        engine_version=SYNTHETIC_PROXY_ENGINE_VERSION,
        cost_model=dict(candidate.cost_model),
        train_window=dict(candidate.train_window),
        test_window=dict(candidate.test_window),
        created_at=G2_CREATED_AT,
        promotion_ready=False,
        canonical_engine_required=True,
    )


def validate_g2_fixture_candidate(
    candidate: CandidateSpec,
    *,
    repo_root: str | Path | None = None,
) -> None:
    if candidate.family_id != G2_SYNTHETIC_FAMILY_ID:
        raise ProxyBoundaryError("G2 requires the registered synthetic fixture family")
    if candidate.trial_count != 1:
        raise ProxyBoundaryError("G2 requires exactly one registered fixture trial")
    if not candidate.manifest_uri:
        raise ProxyBoundaryError("G2 candidate manifest_uri is required")
    if not candidate.source_quality:
        raise ProxyBoundaryError("G2 candidate source_quality is required")
    if not candidate.code_ref:
        raise ProxyBoundaryError("G2 candidate code_ref is required")
    if not candidate.data_snapshot:
        raise ProxyBoundaryError("G2 candidate data_snapshot is required")
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    manifest_path = _resolve_path(root, candidate.manifest_uri)
    if not manifest_path.exists():
        raise ProxyBoundaryError(f"G2 candidate manifest_uri does not exist: {candidate.manifest_uri}")
    manifest = load_manifest(manifest_path)
    _validate_synthetic_manifest_for_g2(manifest)
    if manifest.get("source_quality") != candidate.source_quality:
        raise ProxyBoundaryError("G2 candidate source_quality must match manifest source_quality")
    expected_manifest_hash = compute_sha256(manifest_path)
    declared_manifest_hash = str(candidate.data_snapshot.get("manifest_sha256", "")).strip()
    if not declared_manifest_hash:
        raise ProxyBoundaryError("G2 candidate data_snapshot.manifest_sha256 is required")
    if declared_manifest_hash != expected_manifest_hash:
        raise ProxyBoundaryError("G2 candidate data_snapshot.manifest_sha256 mismatch")


def write_g2_lineage_artifact(
    lineage_report: Mapping[str, Any],
    report_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> tuple[Path, Path]:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    target = _resolve_path(root, report_path)
    write_json_atomic(dict(lineage_report), target)
    artifact_path: str | Path = target
    try:
        if root.resolve() == Path.cwd().resolve():
            artifact_path = target.relative_to(root)
    except ValueError:
        artifact_path = target
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact_path,
            source_quality=str(lineage_report["source_quality"]),
            provider="synthetic_fixture",
            provider_feed="v2_proxy_lineage_report",
            license_scope="synthetic_fixture_only",
            row_count=1,
            date_range={"start": "2026-05-09", "end": "2026-05-09"},
            extra={
                "candidate_id": lineage_report["candidate_id"],
                "proxy_run_id": lineage_report["proxy_run_id"],
                "registry_note_event_id": lineage_report["registry_note_event_id"],
                "boundary_verdict": lineage_report["boundary_verdict"],
            },
        )
    )
    manifest_path = Path(f"{target}.manifest.json")
    write_manifest(manifest, manifest_path)
    return target, manifest_path


def _run_proxy_and_record_note(
    registry: CandidateRegistry,
    spec: ProxyRunSpec,
    *,
    actor: str,
) -> tuple[ProxyRunResult, int, int]:
    boundary = V2ProxyBoundary(registry)
    proxy_boundary_verdict = boundary.verdict_for(spec)
    fixture = load_synthetic_proxy_fixture(spec.manifest_uri, repo_root=registry.repo_root)
    cost_model = FastProxyCostModel.from_mapping(spec.cost_model)
    ledger_output = build_synthetic_ledger(fixture.prices, fixture.weights, cost_model)
    validate_synthetic_ledger_output(ledger_output.positions, ledger_output.ledger)
    note = _find_existing_proxy_note(
        registry,
        candidate_id=spec.candidate_id,
        proxy_run_id=spec.proxy_run_id,
        boundary_verdict=proxy_boundary_verdict.value,
    )
    if note is None:
        note = registry.add_note(
            spec.candidate_id,
            actor=actor,
            note=(
                f"{G2_REGISTRY_NOTE_MARKER}; proxy_run_id={spec.proxy_run_id}; "
                f"boundary_verdict={proxy_boundary_verdict.value}; "
                "promotion_ready=false; canonical_engine_required=true"
            ),
        )
    proxy_result = ProxyRunResult.from_spec(
        spec,
        status=ProxyRunStatus.COMPLETED,
        boundary_verdict=proxy_boundary_verdict,
        registry_note_event_id=note.event_id,
    )
    boundary.validate_result(proxy_result)
    return proxy_result, len(ledger_output.positions), len(ledger_output.ledger)


def _find_existing_proxy_note(
    registry: CandidateRegistry,
    *,
    candidate_id: str,
    proxy_run_id: str,
    boundary_verdict: str,
) -> CandidateEvent | None:
    required_tokens = (
        G2_REGISTRY_NOTE_MARKER,
        proxy_run_id,
        f"boundary_verdict={boundary_verdict}",
        "promotion_ready=false",
        "canonical_engine_required=true",
    )
    for event in load_registry_events(registry):
        if event.candidate_id != candidate_id or event.event_type != "candidate.note_added":
            continue
        note = str(event.payload.get("note", ""))
        if all(token in note for token in required_tokens):
            return event
    return None


def _fixture_candidate_ids(registry: CandidateRegistry) -> list[str]:
    ids = []
    for candidate_id, snapshot in registry.rebuild_snapshot().items():
        spec = snapshot.spec
        if spec.family_id == G2_SYNTHETIC_FAMILY_ID:
            ids.append(candidate_id)
    return sorted(ids)


def _candidate_event_from_id(
    registry: CandidateRegistry,
    event_id: str,
    candidate_id: str,
) -> CandidateEvent:
    event = find_candidate_event(registry, candidate_id=candidate_id)
    if event.event_id != event_id:
        raise ProxyBoundaryError("candidate_event_id does not match registered candidate")
    return event


def _validate_synthetic_manifest_for_g2(manifest: Mapping[str, Any]) -> None:
    extra = manifest.get("extra")
    if (
        manifest.get("provider") != "synthetic_fixture"
        or manifest.get("provider_feed") != "prebaked_target_weights"
        or manifest.get("license_scope") != "synthetic_fixture_only"
        or not isinstance(extra, Mapping)
        or extra.get("fixture_scope") != SYNTHETIC_FIXTURE_SCOPE
    ):
        raise ProxyBoundaryError("G2 rejects Tier 2/non-fixture candidates for proxy lineage")
    if manifest.get("source_quality") != SOURCE_QUALITY_NON_CANONICAL:
        raise ProxyBoundaryError("G2 synthetic fixture candidate must be non_canonical")


def _manifest_sha256(path: Path) -> str:
    return compute_sha256(path)


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def main() -> None:
    run = run_g2_single_fixture_candidate()
    print(
        "G2 single registered fixture candidate complete: "
        f"candidate_id={run.lineage_report['candidate_id']} "
        f"proxy_run_id={run.lineage_report['proxy_run_id']} "
        f"promotion_ready={run.lineage_report['promotion_ready']} "
        f"boundary_verdict={run.lineage_report['boundary_verdict']}"
    )


if __name__ == "__main__":
    main()
