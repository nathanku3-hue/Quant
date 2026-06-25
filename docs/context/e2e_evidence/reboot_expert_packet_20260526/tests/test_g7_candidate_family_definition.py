from __future__ import annotations

import inspect
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import compute_sha256
from v2_discovery.families import registry as family_registry
from v2_discovery.families.registry import CandidateFamilyRegistry
from v2_discovery.families.registry import block_candidate_materialization
from v2_discovery.families.registry import block_result_path
from v2_discovery.families.registry import build_pead_daily_v0_definition
from v2_discovery.families.registry import build_registry_report
from v2_discovery.families.schemas import CandidateFamilyDefinition
from v2_discovery.families.schemas import CandidateFamilyError
from v2_discovery.families.schemas import G7_FAMILY_ID
from v2_discovery.families.schemas import outcome_field_names


def _definition(tmp_path: Path, **overrides) -> CandidateFamilyDefinition:
    manifest_uri = tmp_path / "data" / "registry" / "candidate_families" / "pead_daily_v0.json.manifest.json"
    payload = build_pead_daily_v0_definition(repo_root=tmp_path, manifest_uri=manifest_uri).to_dict()
    payload.update(overrides)
    return CandidateFamilyDefinition.from_dict(payload)


def _registry(tmp_path: Path) -> CandidateFamilyRegistry:
    return CandidateFamilyRegistry(
        tmp_path / "data" / "registry" / "candidate_families",
        repo_root=tmp_path,
    )


def _register(tmp_path: Path, **overrides) -> tuple[CandidateFamilyRegistry, CandidateFamilyDefinition]:
    registry = _registry(tmp_path)
    definition = _definition(tmp_path, **overrides)
    registry.register_family(definition)
    return registry, definition


def test_g7_family_requires_id_and_hypothesis(tmp_path):
    with pytest.raises(CandidateFamilyError, match="family_id is required"):
        _definition(tmp_path, family_id="")

    with pytest.raises(CandidateFamilyError, match="hypothesis is required"):
        _definition(tmp_path, hypothesis="")


def test_g7_family_requires_manifest(tmp_path):
    definition = _definition(tmp_path)
    registry = _registry(tmp_path)

    registry.register_family(definition)
    (tmp_path / definition.manifest_uri).unlink()
    with pytest.raises(CandidateFamilyError, match="requires manifest backing"):
        registry.load_family(definition.family_id)


def test_g7_family_requires_tier0_source_policy(tmp_path):
    with pytest.raises(CandidateFamilyError, match="Tier 0"):
        _definition(tmp_path, data_tier_required="tier2")

    with pytest.raises(CandidateFamilyError, match="canonical"):
        _definition(tmp_path, source_quality_required="non_canonical")

    _, definition = _register(tmp_path)
    assert definition.data_tier_required == "tier0"
    assert definition.source_quality_required == SOURCE_QUALITY_CANONICAL


def test_g7_family_requires_finite_parameter_space(tmp_path):
    definition = _definition(tmp_path)

    assert definition.finite_trial_count == 24
    assert definition.finite_trial_count <= definition.trial_budget_max

    with pytest.raises(CandidateFamilyError, match="parameter_space"):
        _definition(tmp_path, parameter_space={})


def test_g7_family_requires_trial_budget(tmp_path):
    with pytest.raises(CandidateFamilyError, match="trial_budget_max"):
        _definition(tmp_path, trial_budget_max=None)

    with pytest.raises(CandidateFamilyError, match="positive"):
        _definition(tmp_path, trial_budget_max=0)


def test_g7_family_rejects_unbounded_parameter_space(tmp_path):
    with pytest.raises(CandidateFamilyError, match="unbounded|finite"):
        _definition(tmp_path, parameter_space={"holding_days": ["*"]})

    with pytest.raises(CandidateFamilyError, match="finite option lists"):
        _definition(tmp_path, parameter_space={"holding_days": "any"})


def test_g7_family_rejects_tier2_promotion_policy(tmp_path):
    policy = {
        "promotion_ready": False,
        "candidate_generation_allowed": False,
        "allowed_promotion_data_tiers": ["tier2"],
        "allowed_promotion_source_quality": ["canonical"],
    }

    with pytest.raises(CandidateFamilyError, match="cannot be promotion evidence"):
        _definition(tmp_path, promotion_policy=policy)

    for value in ("Tier 2", "tier-2", "operational Alpaca"):
        spaced_policy = {**policy, "allowed_promotion_data_tiers": [value]}
        with pytest.raises(CandidateFamilyError, match="cannot be promotion evidence"):
            _definition(tmp_path, promotion_policy=spaced_policy)


def test_g7_family_definition_is_versioned_or_append_only(tmp_path):
    registry, definition = _register(tmp_path)
    path = registry.path_for(definition.family_id)
    manifest_path = Path(f"{path}.manifest.json")
    original = path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    same_path, same_manifest = registry.register_family(definition)

    assert same_path == path
    assert same_manifest == manifest_path
    assert path.read_text(encoding="utf-8") == original
    assert json.loads(manifest_path.read_text(encoding="utf-8")) == manifest
    assert definition.version == 1

    mutated = CandidateFamilyDefinition.from_dict(
        {**definition.to_dict(), "hypothesis": "mutated after registration"}
    )
    with pytest.raises(CandidateFamilyError, match="append-only"):
        registry.register_family(mutated)

    with pytest.raises(FrozenInstanceError):
        definition.family_id = "MUTATED"


def test_g7_family_cannot_generate_candidate():
    with pytest.raises(CandidateFamilyError, match="cannot materialize a candidate"):
        block_candidate_materialization(family_id=G7_FAMILY_ID)

    assert not hasattr(CandidateFamilyRegistry, "generate_candidate")
    assert not hasattr(CandidateFamilyRegistry, "run_strategy_search")


def test_g7_family_cannot_run_backtest_or_proxy():
    with pytest.raises(CandidateFamilyError, match="definition only"):
        block_result_path(family_id=G7_FAMILY_ID, action="back" "test")

    with pytest.raises(CandidateFamilyError, match="definition only"):
        block_result_path(family_id=G7_FAMILY_ID, action="pro" "xy")

    forbidden_methods = {"run_backtest", "run_proxy", "run_replay"}
    assert forbidden_methods.isdisjoint(set(dir(CandidateFamilyRegistry)))


def test_g7_family_cannot_emit_metrics_or_rankings(tmp_path):
    definition = _definition(tmp_path)
    payload = definition.to_dict()

    assert outcome_field_names().isdisjoint(payload)
    assert "best_parameter" not in json.dumps(payload).lower()
    assert "candidate_rank" not in json.dumps(payload).lower()


def test_g7_family_cannot_emit_alert_or_broker_action(tmp_path):
    registry, definition = _register(tmp_path)
    report_path = registry.write_registry_report(definitions=[definition])
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["alerts_emitted"] is False
    assert report["broker_calls"] is False
    assert report["promotion_packet_created"] is False
    assert not hasattr(CandidateFamilyRegistry, "emit_alert")
    assert not hasattr(CandidateFamilyRegistry, "call_broker")
    assert not hasattr(CandidateFamilyRegistry, "openclaw_message")


def test_g7_candidate_creation_blocked_without_family_definition(tmp_path):
    registry = _registry(tmp_path)

    with pytest.raises(CandidateFamilyError, match="must exist before candidate creation"):
        registry.require_family_for_candidate(G7_FAMILY_ID)


def test_g7_candidate_creation_blocked_if_trial_budget_missing(tmp_path):
    with pytest.raises(CandidateFamilyError, match="trial_budget_max"):
        _definition(tmp_path, trial_budget_max=None)


def test_g7_report_contains_no_alpha_or_performance_fields(tmp_path):
    registry, definition = _register(tmp_path)
    report_path = registry.write_registry_report(definitions=[definition])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    text = json.dumps(report, sort_keys=True).lower()

    assert report["defined_only"] is True
    assert report["candidate_generation_enabled"] is False
    assert report["result_generation_enabled"] is False
    assert outcome_field_names().isdisjoint(report)
    for word in ("sharpe", "cagr", "alpha", "drawdown", "score", "rank"):
        assert word not in text


def test_g7_direct_report_builder_requires_verified_manifest_backing(tmp_path):
    definition = _definition(tmp_path)

    with pytest.raises(CandidateFamilyError, match="verified manifest backing"):
        build_registry_report([definition])


def test_g7_registry_report_requires_fresh_family_manifest(tmp_path):
    missing_root = tmp_path / "missing_manifest"
    missing_registry, missing_definition = _register(missing_root)
    missing_manifest = Path(f"{missing_registry.path_for(missing_definition.family_id)}.manifest.json")
    missing_manifest.unlink()

    with pytest.raises(CandidateFamilyError, match="requires manifest backing"):
        missing_registry.write_registry_report(definitions=[missing_definition])

    corrupt_root = tmp_path / "corrupt_manifest"
    corrupt_registry, corrupt_definition = _register(corrupt_root)
    corrupt_manifest = Path(f"{corrupt_registry.path_for(corrupt_definition.family_id)}.manifest.json")
    payload = json.loads(corrupt_manifest.read_text(encoding="utf-8"))
    payload["sha256"] = "0" * 64
    corrupt_manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    with pytest.raises(CandidateFamilyError, match="hash mismatch"):
        corrupt_registry.write_registry_report(definitions=[corrupt_definition])


def test_g7_manifest_reconciles_family_hash_row_and_budget(tmp_path):
    registry, definition = _register(tmp_path)
    path = registry.path_for(definition.family_id)
    manifest_path = Path(f"{path}.manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["sha256"] == compute_sha256(path)
    assert manifest["row_count"] == 1
    assert manifest["source_quality"] == SOURCE_QUALITY_CANONICAL
    assert manifest["extra"]["family_id"] == G7_FAMILY_ID
    assert manifest["extra"]["trial_budget_max"] == 24

    loaded = registry.load_family(definition.family_id)
    assert loaded.to_dict() == definition.to_dict()


def test_g7_implementation_source_exposes_no_result_execution_surface():
    source = inspect.getsource(family_registry)
    forbidden = (
        "submit_order",
        "BrokerPort",
        "OpenClaw",
        "notifier",
        "promote_candidate",
        "generate_strategy",
    )

    assert all(token not in source for token in forbidden)
