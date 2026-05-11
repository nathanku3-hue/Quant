from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from data.provenance import ManifestInput
from data.provenance import build_manifest
from data.provenance import compute_sha256
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import assert_can_promote
from data.provenance import validate_alert_record
from data.provenance import write_manifest
from v2_discovery.fast_sim import lineage
from v2_discovery.fast_sim import run_candidate_proxy
from v2_discovery.fast_sim.fixtures import load_synthetic_proxy_fixture
from v2_discovery.fast_sim.lineage import G2_REQUIRED_LINEAGE_FIELDS
from v2_discovery.fast_sim.lineage import build_g2_lineage_report
from v2_discovery.fast_sim.lineage import load_registry_events
from v2_discovery.fast_sim.run_candidate_proxy import G2_PROXY_RUN_ID
from v2_discovery.fast_sim.run_candidate_proxy import G2_SYNTHETIC_CANDIDATE_ID
from v2_discovery.fast_sim.run_candidate_proxy import build_g2_fixture_candidate
from v2_discovery.fast_sim.run_candidate_proxy import build_proxy_spec_for_registered_candidate
from v2_discovery.fast_sim.run_candidate_proxy import register_or_load_g2_fixture_candidate
from v2_discovery.fast_sim.run_candidate_proxy import run_g2_single_fixture_candidate
from v2_discovery.fast_sim.run_candidate_proxy import run_registered_candidate_proxy
from v2_discovery.fast_sim.run_candidate_proxy import validate_g2_fixture_candidate
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunStatus
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateEvent
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


FIXTURE_DIR = Path("data/fixtures/v2_proxy")
MANIFEST_URI = FIXTURE_DIR / "synthetic_manifest.json"


def _registry(tmp_path: Path, *, repo_root: Path | None = None) -> CandidateRegistry:
    return CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=repo_root or Path.cwd(),
    )


def _registered_g2_candidate(tmp_path: Path) -> tuple[CandidateRegistry, CandidateSpec, CandidateEvent]:
    registry = _registry(tmp_path)
    candidate = build_g2_fixture_candidate()
    event = registry.register_candidate(candidate, actor="pytest")
    return registry, candidate, event


def _copy_fixture_tree(tmp_path: Path) -> Path:
    fixture_copy = tmp_path / "data" / "fixtures" / "v2_proxy"
    fixture_copy.mkdir(parents=True)
    for path in FIXTURE_DIR.iterdir():
        if path.is_file():
            (fixture_copy / path.name).write_bytes(path.read_bytes())
    return fixture_copy


def _write_manifest(fixture_copy: Path, manifest: dict) -> None:
    (fixture_copy / "synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _mutated_fixture_candidate(tmp_path: Path, file_name: str, text: str, manifest_mutator=None):
    fixture_copy = _copy_fixture_tree(tmp_path)
    target = fixture_copy / file_name
    target.write_text(text, encoding="utf-8")
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    if file_name == "synthetic_prices.csv":
        manifest["extra"]["prices"]["sha256"] = compute_sha256(target)
    elif file_name == "synthetic_weights.csv":
        new_hash = compute_sha256(target)
        manifest["artifact_path"] = "data/fixtures/v2_proxy/synthetic_weights.csv"
        manifest["sha256"] = new_hash
        manifest["extra"]["weights"]["sha256"] = new_hash
    if manifest_mutator is not None:
        manifest_mutator(manifest)
    _write_manifest(fixture_copy, manifest)
    registry = _registry(tmp_path, repo_root=tmp_path)
    candidate = build_g2_fixture_candidate(
        repo_root=tmp_path,
        manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json",
    )
    event = registry.register_candidate(candidate, actor="pytest")
    return registry, candidate, event


def _candidate_from_g2(candidate: CandidateSpec, **overrides) -> CandidateSpec:
    payload = candidate.to_dict()
    payload.update(overrides)
    return CandidateSpec(**payload)


def _write_non_fixture_manifest(tmp_path: Path, *, source_quality=SOURCE_QUALITY_NON_CANONICAL) -> str:
    artifact = tmp_path / "tier2_source.csv"
    artifact.write_text("date,symbol,close\n2020-01-02,AAA,100.00\n", encoding="utf-8")
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=source_quality,
            provider="yahoo",
            provider_feed="yahoo_public_api",
            license_scope="research_education",
            row_count=1,
            date_range={"start": "2020-01-02", "end": "2020-01-02"},
        )
    )
    return str(write_manifest(manifest, tmp_path / "tier2_source.csv.manifest.json"))


def test_g2_requires_existing_registered_candidate(tmp_path):
    registry = _registry(tmp_path)

    with pytest.raises(ProxyBoundaryError, match="existing registered fixture candidate"):
        run_registered_candidate_proxy(registry, report_path=None)


def test_g2_rejects_unregistered_candidate(tmp_path):
    registry = _registry(tmp_path)
    candidate = build_g2_fixture_candidate()

    with pytest.raises(ProxyBoundaryError, match="unregistered candidate"):
        build_proxy_spec_for_registered_candidate(
            registry,
            candidate,
            candidate_event_id="missing-event",
        )


def test_g2_requires_candidate_manifest(tmp_path):
    candidate = build_g2_fixture_candidate(manifest_uri=MANIFEST_URI)
    bad = _candidate_from_g2(candidate, manifest_uri="data/fixtures/v2_proxy/missing.json")

    with pytest.raises(ProxyBoundaryError, match="manifest_uri does not exist"):
        validate_g2_fixture_candidate(bad)


def test_g2_requires_candidate_data_snapshot_manifest_hash(tmp_path):
    registry = _registry(tmp_path)
    candidate = build_g2_fixture_candidate()
    bad = _candidate_from_g2(
        candidate,
        data_snapshot={
            **dict(candidate.data_snapshot),
            "manifest_sha256": "0" * 64,
        },
    )
    registry.register_candidate(bad, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="manifest_sha256 mismatch"):
        run_registered_candidate_proxy(registry, report_path=None)


def test_g2_rejects_tier2_candidate_for_proxy_lineage(tmp_path):
    registry = _registry(tmp_path)
    manifest_uri = _write_non_fixture_manifest(tmp_path)
    candidate = build_g2_fixture_candidate()
    bad = _candidate_from_g2(
        candidate,
        candidate_id="PH65_G2_TIER2_NON_FIXTURE",
        manifest_uri=manifest_uri,
    )
    registry.register_candidate(bad, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="Tier 2/non-fixture"):
        run_registered_candidate_proxy(
            registry,
            candidate_id=bad.candidate_id,
            report_path=None,
        )


def test_g2_runs_single_synthetic_candidate_only(tmp_path):
    registry, candidate, _ = _registered_g2_candidate(tmp_path)
    duplicate = build_g2_fixture_candidate(candidate_id="PH65_G2_SYNTHETIC_FIXTURE_002")
    registry.register_candidate(duplicate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="exactly one synthetic fixture candidate"):
        run_registered_candidate_proxy(
            registry,
            candidate_id=candidate.candidate_id,
            report_path=None,
        )


def test_g2_appends_real_registry_note_event(tmp_path):
    registry, _, _ = _registered_g2_candidate(tmp_path)
    before = len(load_registry_events(registry))
    output = run_registered_candidate_proxy(registry, report_path=None)
    events = load_registry_events(registry)
    note = events[-1]

    assert len(events) == before + 1
    assert note.event_id == output.proxy_result.registry_note_event_id
    assert note.event_hash == output.lineage_report["registry_note_event_hash"]
    assert note.recompute_hash() == note.event_hash
    assert note.previous_event_hash == events[-2].event_hash
    assert note.event_type == "candidate.note_added"
    assert "candidate.proxy_run_recorded" in note.payload["note"]


def test_g2_rejects_forged_registry_note_event_id(tmp_path):
    registry, candidate, event = _registered_g2_candidate(tmp_path)
    spec = build_proxy_spec_for_registered_candidate(
        registry,
        candidate,
        candidate_event_id=event.event_id,
    )
    forged = ProxyRunResult.from_spec(
        spec,
        status=ProxyRunStatus.COMPLETED,
        boundary_verdict=ProxyBoundaryVerdict.TIER2_BLOCKED,
        registry_note_event_id=event.event_id,
    )

    with pytest.raises(ProxyBoundaryError, match="candidate note"):
        build_g2_lineage_report(
            registry=registry,
            proxy_result=forged,
            candidate_event_id=event.event_id,
        )


def test_g2_registry_note_candidate_id_must_match(tmp_path):
    registry, candidate, event = _registered_g2_candidate(tmp_path)
    other = build_g2_fixture_candidate(candidate_id="PH65_G2_OTHER_FAMILY_MEMBER")
    registry.register_candidate(other, actor="pytest")
    note = registry.add_note(
        other.candidate_id,
        actor="pytest",
        note=(
            f"candidate.proxy_run_recorded; proxy_run_id={G2_PROXY_RUN_ID}; "
            "boundary_verdict=tier2_blocked; promotion_ready=false; "
            "canonical_engine_required=true"
        ),
    )
    spec = build_proxy_spec_for_registered_candidate(
        registry,
        candidate,
        candidate_event_id=event.event_id,
    )
    forged = ProxyRunResult.from_spec(
        spec,
        status=ProxyRunStatus.COMPLETED,
        boundary_verdict=ProxyBoundaryVerdict.TIER2_BLOCKED,
        registry_note_event_id=note.event_id,
    )

    with pytest.raises(ProxyBoundaryError, match="candidate_id does not match"):
        build_g2_lineage_report(
            registry=registry,
            proxy_result=forged,
            candidate_event_id=event.event_id,
        )


def test_g2_proxy_result_still_promotion_ready_false(tmp_path):
    registry, _, _ = _registered_g2_candidate(tmp_path)
    output = run_registered_candidate_proxy(registry, report_path=None)

    assert output.proxy_result.promotion_ready is False
    assert output.lineage_report["promotion_ready"] is False
    with pytest.raises(ProxyBoundaryError, match="promotion_ready"):
        ProxyRunResult(
            **{
                **output.proxy_result.to_dict(),
                "promotion_ready": True,
            }
        )


def test_g2_proxy_result_requires_v1_canonical_engine(tmp_path):
    registry, _, _ = _registered_g2_candidate(tmp_path)
    output = run_registered_candidate_proxy(registry, report_path=None)

    assert output.proxy_result.canonical_engine_required is True
    assert output.lineage_report["canonical_engine_required"] is True
    assert output.lineage_report["engine_name"] == PROXY_ENGINE_NAME
    assert V1_CANONICAL_ENGINE_NAME == "core.engine.run_simulation"


def test_g2_lineage_report_rebuilds_from_event_log(tmp_path):
    registry, _, _ = _registered_g2_candidate(tmp_path)
    output = run_registered_candidate_proxy(
        registry,
        report_path=tmp_path / "g2_single_fixture_candidate_report.json",
    )
    rebuilt = registry.rebuild_snapshot()[G2_SYNTHETIC_CANDIDATE_ID]
    report = output.lineage_report

    assert output.report_path is not None and output.report_path.exists()
    assert output.report_manifest_path is not None and output.report_manifest_path.exists()
    assert output.snapshot_path is not None and output.snapshot_path.exists()
    assert set(G2_REQUIRED_LINEAGE_FIELDS).issubset(report)
    assert report["candidate_id"] == rebuilt.candidate_id
    assert report["family_id"] == rebuilt.spec.family_id
    assert report["rebuilt_snapshot_last_event_hash"] == rebuilt.last_event_hash
    assert report["registry_note_event_hash"] == rebuilt.last_event_hash
    assert report["manifest_sha256"] == compute_sha256(MANIFEST_URI)
    assert report["fixture_sha256"] == compute_sha256(FIXTURE_DIR / "synthetic_weights.csv")
    assert report["boundary_verdict"] == "blocked_from_promotion"
    assert report["proxy_boundary_verdict"] == "tier2_blocked"


def test_g2_cannot_emit_alert_or_broker_action(tmp_path):
    registry, _, _ = _registered_g2_candidate(tmp_path)
    output = run_registered_candidate_proxy(registry, report_path=None)
    source = "\n".join(
        [
            inspect.getsource(run_candidate_proxy),
            inspect.getsource(lineage),
        ]
    )

    assert output.lineage_report["promotion_packet_blocked"] is True
    assert output.lineage_report["signal_packet_blocked"] is True
    assert output.lineage_report["order_action_blocked"] is True
    assert "emit_alert" not in source
    assert "submit_order" not in source
    assert "BrokerPort" not in source
    assert "broker_api" not in source
    assert "alpaca" not in source.lower()
    with pytest.raises(Exception):
        assert_can_promote({"source_quality": SOURCE_QUALITY_NON_CANONICAL})
    with pytest.raises(Exception):
        validate_alert_record({"source_quality": "rejected", "provider": "synthetic_fixture", "provider_feed": "fixture"})
    assert not hasattr(run_candidate_proxy, "emit_alert")
    assert not hasattr(run_candidate_proxy, "submit_order")


def test_g2_non_finite_fixture_still_fails_closed(tmp_path):
    registry, candidate, event = _mutated_fixture_candidate(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,100.00\n2020-01-02,BBB,-inf\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"bad value class: -inf"):
        run_registered_candidate_proxy(
            registry,
            candidate_id=candidate.candidate_id,
            candidate_event_id=event.event_id,
            report_path=None,
        )


def test_g2_manifest_row_count_and_date_range_reconciled(tmp_path):
    registry, candidate, event = _mutated_fixture_candidate(
        tmp_path,
        "synthetic_weights.csv",
        "date,symbol,target_weight\n2020-01-02,AAA,0.50\n2020-01-02,BBB,0.50\n",
        lambda manifest: manifest.update(
            {"row_count": 4, "date_range": {"start": "1999-01-01", "end": "2020-01-02"}}
        )
        or manifest["extra"]["weights"].update(
            {"row_count": 4, "date_range": {"start": "1999-01-01", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match="manifest row_count mismatch"):
        run_registered_candidate_proxy(
            registry,
            candidate_id=candidate.candidate_id,
            candidate_event_id=event.event_id,
            report_path=None,
        )


def test_g2_register_or_loads_exactly_one_candidate(tmp_path):
    registry = _registry(tmp_path)
    candidate, event = register_or_load_g2_fixture_candidate(registry, actor="pytest")
    loaded, loaded_event = register_or_load_g2_fixture_candidate(registry, actor="pytest")

    assert candidate.candidate_id == G2_SYNTHETIC_CANDIDATE_ID
    assert loaded == candidate
    assert loaded_event.event_id == event.event_id
    assert registry.rebuild_snapshot()[candidate.candidate_id].event_count == 1


def test_g2_repeated_run_reuses_existing_proxy_note(tmp_path):
    registry = _registry(tmp_path)
    first = run_g2_single_fixture_candidate(registry=registry, actor="pytest", report_path=None)
    event_count_after_first = len(load_registry_events(registry))
    second = run_g2_single_fixture_candidate(registry=registry, actor="pytest", report_path=None)

    assert len(load_registry_events(registry)) == event_count_after_first
    assert second.proxy_result.registry_note_event_id == first.proxy_result.registry_note_event_id
    assert second.lineage_report["registry_note_event_hash"] == first.lineage_report["registry_note_event_hash"]


def test_g2_end_to_end_optional_artifact_uses_registered_candidate(tmp_path):
    registry = _registry(tmp_path)
    output = run_g2_single_fixture_candidate(
        registry=registry,
        actor="pytest",
        report_path=tmp_path / "report.json",
    )

    assert output.proxy_result.proxy_run_id == G2_PROXY_RUN_ID
    assert output.positions_rows == 4
    assert output.ledger_rows == 2
    assert output.report_path is not None and output.report_path.exists()
    assert output.report_manifest_path is not None and output.report_manifest_path.exists()
    assert registry.verify_hash_chain()["valid"] is True
    assert registry.rebuild_snapshot()[G2_SYNTHETIC_CANDIDATE_ID].event_count == 2


def test_g2_fixture_loader_still_reconciles_g1_manifest():
    fixture = load_synthetic_proxy_fixture(MANIFEST_URI)

    assert len(fixture.prices) == 4
    assert len(fixture.weights) == 4
    assert fixture.manifest["extra"]["prices"]["date_range"] == {
        "start": "2020-01-02",
        "end": "2020-01-03",
    }
