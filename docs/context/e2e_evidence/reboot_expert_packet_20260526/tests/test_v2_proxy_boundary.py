from __future__ import annotations

import inspect

import pytest

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import build_manifest
from data.provenance import utc_now_iso
from data.provenance import write_manifest
from v2_discovery.fast_sim.boundary import V2ProxyBoundary
from v2_discovery.fast_sim.noop_proxy import NOOP_PROXY_ENGINE_VERSION
from v2_discovery.fast_sim.noop_proxy import NoopProxy
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.fast_sim.schemas import PromotionPacketDraft
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.schemas import ProxyRunStatus
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


def _write_manifest(tmp_path, *, source_quality=SOURCE_QUALITY_CANONICAL) -> str:
    artifact = tmp_path / f"proxy_source_{source_quality}.csv"
    artifact.write_text("date,permno,net_ret\n2024-01-02,1,0.01\n", encoding="utf-8")
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=source_quality,
            provider="wrds" if source_quality == SOURCE_QUALITY_CANONICAL else "yahoo",
            provider_feed="crsp_daily"
            if source_quality == SOURCE_QUALITY_CANONICAL
            else "yahoo_public_api",
            license_scope="canonical_research"
            if source_quality == SOURCE_QUALITY_CANONICAL
            else "research_education",
            row_count=1,
            date_range={"start": "2024-01-02", "end": "2024-01-02"},
        )
    )
    return str(write_manifest(manifest, tmp_path / f"proxy_source_{source_quality}.csv.manifest.json"))


def _candidate(tmp_path, **overrides) -> CandidateSpec:
    payload = {
        "candidate_id": "G0_PROXY_CANDIDATE",
        "family_id": "PEAD_DAILY_RESEARCH",
        "hypothesis": "Proxy boundary placeholder, no alpha computation.",
        "universe": "US_EQUITIES_DAILY",
        "features": ["placeholder_feature"],
        "parameters_searched": {"noop": [True]},
        "trial_count": 1,
        "train_window": {"start": "2014-01-01", "end": "2021-12-31"},
        "test_window": {"start": "2022-01-01", "end": "2024-12-31"},
        "cost_model": {"commission_bps": 0, "slippage_bps": 10},
        "data_snapshot": {"dataset": "proxy_boundary_fixture", "asof": "2026-05-09"},
        "manifest_uri": _write_manifest(tmp_path),
        "source_quality": SOURCE_QUALITY_CANONICAL,
        "created_at": utc_now_iso(),
        "created_by": "pytest",
        "code_ref": "test-suite",
        "status": CandidateStatus.GENERATED,
    }
    payload.update(overrides)
    return CandidateSpec(**payload)


def _registry(tmp_path) -> CandidateRegistry:
    return CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )


def _registered_fixture(tmp_path, **candidate_overrides):
    registry = _registry(tmp_path)
    candidate = _candidate(tmp_path, **candidate_overrides)
    event = registry.register_candidate(candidate, actor="pytest")
    return registry, candidate, event


def _proxy_spec(candidate: CandidateSpec, registry_event_id: str, **overrides) -> ProxyRunSpec:
    payload = {
        "proxy_run_id": "PROXY_RUN_001",
        "candidate_id": candidate.candidate_id,
        "registry_event_id": registry_event_id,
        "manifest_uri": candidate.manifest_uri,
        "source_quality": candidate.source_quality,
        "data_snapshot": {"dataset": "proxy_boundary_fixture", "asof": "2026-05-09"},
        "code_ref": "test-suite",
        "engine_name": PROXY_ENGINE_NAME,
        "engine_version": NOOP_PROXY_ENGINE_VERSION,
        "cost_model": dict(candidate.cost_model),
        "train_window": dict(candidate.train_window),
        "test_window": dict(candidate.test_window),
        "created_at": utc_now_iso(),
        "promotion_ready": False,
        "canonical_engine_required": True,
    }
    payload.update(overrides)
    return ProxyRunSpec(**payload)


def test_proxy_result_requires_registered_candidate(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    spec = _proxy_spec(candidate, event.event_id, candidate_id="MISSING_CANDIDATE")

    with pytest.raises(ProxyBoundaryError, match="registered candidate"):
        NoopProxy().run(spec, registry=registry)


def test_proxy_result_requires_manifest(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    spec = _proxy_spec(candidate, event.event_id, manifest_uri=str(tmp_path / "missing.manifest.json"))

    with pytest.raises(ProxyBoundaryError, match="manifest"):
        NoopProxy().run(spec, registry=registry)


def test_proxy_result_requires_source_quality(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)

    with pytest.raises(ProxyBoundaryError, match="source_quality is required"):
        _proxy_spec(candidate, event.event_id, source_quality="")
    assert registry.rebuild_snapshot()[candidate.candidate_id].event_count == 1


def test_proxy_result_always_promotion_ready_false(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    spec = _proxy_spec(candidate, event.event_id)
    result = NoopProxy().run(spec, registry=registry)

    assert result.promotion_ready is False
    assert result.canonical_engine_required is True
    with pytest.raises(ProxyBoundaryError, match="promotion_ready"):
        ProxyRunResult(
            **{
                **spec.to_dict(),
                "status": ProxyRunStatus.COMPLETED,
                "boundary_verdict": ProxyBoundaryVerdict.BLOCKED_FROM_PROMOTION,
                "registry_note_event_id": result.registry_note_event_id,
                "promotion_ready": True,
            }
        )


def test_proxy_result_cannot_emit_alert():
    forbidden_methods = {"emit_alert", "alert_candidate", "build_alert_packet"}
    assert forbidden_methods.isdisjoint(set(dir(NoopProxy)))
    assert forbidden_methods.isdisjoint(set(dir(V2ProxyBoundary)))


def test_proxy_result_cannot_call_broker():
    source = "\n".join(
        [
            inspect.getsource(NoopProxy),
            inspect.getsource(V2ProxyBoundary),
        ]
    )
    assert "BrokerPort" not in source
    assert "submit_order" not in source
    assert "broker_api" not in source
    assert "alpaca" not in source.lower()


def test_tier2_proxy_result_blocked(tmp_path):
    manifest_uri = _write_manifest(tmp_path, source_quality=SOURCE_QUALITY_NON_CANONICAL)
    registry, candidate, event = _registered_fixture(
        tmp_path,
        candidate_id="TIER2_PROXY_CANDIDATE",
        source_quality=SOURCE_QUALITY_NON_CANONICAL,
        manifest_uri=manifest_uri,
    )
    result = NoopProxy().run(_proxy_spec(candidate, event.event_id), registry=registry)

    assert result.boundary_verdict == ProxyBoundaryVerdict.TIER2_BLOCKED
    with pytest.raises(ProxyBoundaryError, match="canonical source_quality"):
        V2ProxyBoundary(registry).build_promotion_packet_draft_from_proxy(
            result,
            canonical_result_ref="future_v1_result.json",
        )


def test_promotion_packet_requires_v1_canonical_engine(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    result = NoopProxy().run(_proxy_spec(candidate, event.event_id), registry=registry)

    with pytest.raises(ProxyBoundaryError, match="future V1 canonical rerun"):
        V2ProxyBoundary(registry).build_promotion_packet_draft_from_proxy(result)

    with pytest.raises(ProxyBoundaryError, match="V1 canonical engine"):
        PromotionPacketDraft(
            candidate_id=candidate.candidate_id,
            source_quality=SOURCE_QUALITY_CANONICAL,
            manifest_uri=candidate.manifest_uri,
            canonical_engine_name=PROXY_ENGINE_NAME,
            canonical_result_ref="proxy_result.json",
            created_at=utc_now_iso(),
        )

    draft = PromotionPacketDraft(
        candidate_id=candidate.candidate_id,
        source_quality=SOURCE_QUALITY_CANONICAL,
        manifest_uri=candidate.manifest_uri,
        canonical_engine_name=V1_CANONICAL_ENGINE_NAME,
        canonical_result_ref="future_v1_result.json",
        created_at=utc_now_iso(),
    )
    assert draft.promotion_ready is False


def test_proxy_output_has_code_ref_and_data_snapshot(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    result = NoopProxy().run(_proxy_spec(candidate, event.event_id), registry=registry)

    assert result.code_ref == "test-suite"
    assert dict(result.data_snapshot) == {"dataset": "proxy_boundary_fixture", "asof": "2026-05-09"}


def test_noop_proxy_round_trip(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    before = registry.rebuild_snapshot()[candidate.candidate_id]
    result = NoopProxy().run(_proxy_spec(candidate, event.event_id), registry=registry)
    after = registry.rebuild_snapshot()[candidate.candidate_id]

    assert result.engine_name == "v2_proxy"
    assert result.boundary_verdict == ProxyBoundaryVerdict.BLOCKED_FROM_PROMOTION
    assert result.promotion_ready is False
    assert result.canonical_engine_required is True
    assert after.status == before.status
    assert after.event_count == before.event_count + 1
    assert after.notes[-1]["note"].startswith("noop proxy run")
    assert registry.verify_hash_chain()["valid"] is True


def test_proxy_result_requires_real_registry_note_event(tmp_path):
    registry, candidate, event = _registered_fixture(tmp_path)
    spec = _proxy_spec(candidate, event.event_id)
    forged = ProxyRunResult.from_spec(
        spec,
        status=ProxyRunStatus.COMPLETED,
        boundary_verdict=ProxyBoundaryVerdict.BLOCKED_FROM_PROMOTION,
        registry_note_event_id=event.event_id,
    )

    with pytest.raises(ProxyBoundaryError, match="candidate note"):
        V2ProxyBoundary(registry).validate_result(forged)
