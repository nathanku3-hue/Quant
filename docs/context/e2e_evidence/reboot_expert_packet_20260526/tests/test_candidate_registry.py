from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import build_manifest
from data.provenance import utc_now_iso
from data.provenance import write_manifest
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateRegistryError
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


def _write_manifest(tmp_path, *, source_quality=SOURCE_QUALITY_CANONICAL) -> str:
    artifact = tmp_path / f"candidate_source_{source_quality}.csv"
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
    return str(write_manifest(manifest, tmp_path / f"candidate_source_{source_quality}.csv.manifest.json"))


def _spec(tmp_path, **overrides) -> CandidateSpec:
    payload = {
        "candidate_id": "CANDIDATE_TEST_001",
        "family_id": "PEAD_DAILY_RESEARCH",
        "hypothesis": "Post-earnings drift candidate placeholder for registry test only.",
        "universe": "US_EQUITIES_DAILY",
        "features": ["earnings_surprise_placeholder", "liquidity_filter_placeholder"],
        "parameters_searched": {"holding_days": [1, 5, 10], "liquidity_floor": ["placeholder"]},
        "trial_count": 6,
        "train_window": {"start": "2014-01-01", "end": "2021-12-31"},
        "test_window": {"start": "2022-01-01", "end": "2024-12-31"},
        "cost_model": {"commission_bps": 0, "slippage_bps": 10},
        "data_snapshot": {"dataset": "phase56_pead_evidence", "asof": "2026-05-09"},
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


def test_candidate_requires_manifest_uri(tmp_path):
    with pytest.raises(CandidateRegistryError, match="manifest_uri is required"):
        _spec(tmp_path, manifest_uri="")


def test_candidate_requires_source_quality(tmp_path):
    with pytest.raises(CandidateRegistryError, match="source_quality is required"):
        _spec(tmp_path, source_quality="")


def test_candidate_requires_trial_count(tmp_path):
    with pytest.raises(CandidateRegistryError, match="trial_count must be an integer"):
        _spec(tmp_path, trial_count=None)


def test_candidate_requires_parameters_searched(tmp_path):
    with pytest.raises(CandidateRegistryError, match="parameters_searched"):
        _spec(tmp_path, parameters_searched={})


def test_candidate_event_log_is_append_only(tmp_path):
    registry = _registry(tmp_path)
    spec = _spec(tmp_path)

    registry.register_candidate(spec, actor="pytest")
    original = registry.event_log_path.read_text(encoding="utf-8")
    registry.write_snapshot()
    after_projection = registry.event_log_path.read_text(encoding="utf-8")
    registry.change_status(spec.candidate_id, CandidateStatus.INCUBATING, actor="pytest")
    after_transition = registry.event_log_path.read_text(encoding="utf-8")

    assert after_projection == original
    assert after_transition.startswith(original)
    assert len(after_transition.splitlines()) == len(original.splitlines()) + 1


def test_snapshot_rebuilds_from_events(tmp_path):
    registry = _registry(tmp_path)
    spec = _spec(tmp_path)

    registry.register_candidate(spec, actor="pytest")
    registry.change_status(spec.candidate_id, CandidateStatus.INCUBATING, actor="pytest")
    registry.reject_candidate(spec.candidate_id, actor="pytest", reason="boring lifecycle proof")
    snapshot_path = registry.write_snapshot()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    rebuilt = registry.rebuild_snapshot()[spec.candidate_id]
    assert rebuilt.status == CandidateStatus.REJECTED
    assert snapshot["candidates"][spec.candidate_id]["status"] == "rejected"
    assert snapshot["candidates"][spec.candidate_id]["event_count"] == 3
    assert snapshot["candidates"][spec.candidate_id]["spec"]["manifest_uri"]


def test_invalid_status_transition_fails(tmp_path):
    registry = _registry(tmp_path)
    spec = _spec(tmp_path)
    registry.register_candidate(spec, actor="pytest")

    with pytest.raises(CandidateRegistryError, match="forbidden in Phase F"):
        registry.change_status(spec.candidate_id, CandidateStatus.PROMOTED, actor="pytest")

    with pytest.raises(CandidateRegistryError, match="forbidden in Phase F"):
        registry.change_status(spec.candidate_id, CandidateStatus.ALERTED, actor="pytest")

    with pytest.raises(CandidateRegistryError, match="forbidden in Phase F"):
        registry.change_status(spec.candidate_id, CandidateStatus.EXECUTED, actor="pytest")


def test_tier2_candidate_cannot_be_promotion_ready(tmp_path):
    manifest_uri = _write_manifest(tmp_path, source_quality=SOURCE_QUALITY_NON_CANONICAL)
    spec = _spec(
        tmp_path,
        candidate_id="TIER2_CANDIDATE",
        source_quality=SOURCE_QUALITY_NON_CANONICAL,
        manifest_uri=manifest_uri,
    )
    registry = _registry(tmp_path)
    registry.register_candidate(spec, actor="pytest")

    snapshot = registry.rebuild_snapshot()[spec.candidate_id]
    assert snapshot.promotion_ready is False
    assert snapshot.promotion_block_reason == "non_canonical_source_quality"


def test_duplicate_candidate_id_rejected_or_idempotent(tmp_path):
    registry = _registry(tmp_path)
    spec = _spec(tmp_path)
    registry.register_candidate(spec, actor="pytest")

    with pytest.raises(CandidateRegistryError, match="Duplicate candidate_id"):
        registry.register_candidate(spec, actor="pytest")


def test_event_hash_chain_detects_tamper(tmp_path):
    registry = _registry(tmp_path)
    spec = _spec(tmp_path)
    registry.register_candidate(spec, actor="pytest")
    registry.change_status(spec.candidate_id, CandidateStatus.INCUBATING, actor="pytest")
    assert registry.verify_hash_chain()["valid"] is True

    lines = registry.event_log_path.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    first["payload"]["spec"]["hypothesis"] = "tampered after the fact"
    lines[0] = json.dumps(first, sort_keys=True, separators=(",", ":"))
    registry.event_log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert registry.verify_hash_chain()["valid"] is False
    assert registry.verify_hash_chain()["error"] == "event_hash_mismatch"


def test_registry_exposes_no_alert_promotion_execution_or_search_methods():
    forbidden_methods = {
        "promote_candidate",
        "emit_alert",
        "execute_candidate",
        "run_strategy_search",
        "generate_strategy",
        "run_backtest",
    }

    assert forbidden_methods.isdisjoint(set(dir(CandidateRegistry)))


def test_candidate_spec_is_frozen(tmp_path):
    spec = _spec(tmp_path)
    with pytest.raises(FrozenInstanceError):
        spec.candidate_id = "MUTATED"
