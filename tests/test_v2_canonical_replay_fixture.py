from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import build_manifest
from data.provenance import compute_sha256
from data.provenance import load_manifest
from data.provenance import write_manifest
from v2_discovery.fast_sim.run_candidate_proxy import G2_SYNTHETIC_CANDIDATE_ID
from v2_discovery.fast_sim.run_candidate_proxy import build_g2_fixture_candidate
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.registry import CandidateRegistry
from v2_discovery.replay import canonical_replay
from v2_discovery.replay.comparison import ALLOWED_COMPARISON_FIELDS
from v2_discovery.replay.comparison import compare_allowed_mechanical_fields
from v2_discovery.replay.schemas import G3ReplayError
from v2_discovery.schemas import CandidateSpec


FIXTURE_DIR = Path("data/fixtures/v2_proxy")
MANIFEST_URI = FIXTURE_DIR / "synthetic_manifest.json"


def _registry(tmp_path: Path, *, repo_root: Path | None = None) -> CandidateRegistry:
    return CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=repo_root or Path.cwd(),
    )


def _registered_g2_candidate(
    tmp_path: Path,
    *,
    repo_root: Path | None = None,
) -> tuple[CandidateRegistry, CandidateSpec]:
    registry = _registry(tmp_path, repo_root=repo_root)
    candidate = build_g2_fixture_candidate(repo_root=repo_root or Path.cwd())
    registry.register_candidate(candidate, actor="pytest")
    return registry, candidate


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


def _candidate_from_g2(candidate: CandidateSpec, **overrides) -> CandidateSpec:
    payload = candidate.to_dict()
    payload.update(overrides)
    return CandidateSpec(**payload)


def _write_tier2_manifest(tmp_path: Path) -> str:
    artifact = tmp_path / "tier2_source.csv"
    artifact.write_text("date,symbol,close\n2020-01-02,AAA,100.00\n", encoding="utf-8")
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact,
            source_quality=SOURCE_QUALITY_NON_CANONICAL,
            provider="yahoo",
            provider_feed="public_api",
            license_scope="research_education",
            row_count=1,
            date_range={"start": "2020-01-02", "end": "2020-01-02"},
        )
    )
    return str(write_manifest(manifest, tmp_path / "tier2_source.csv.manifest.json"))


def _registered_mutated_fixture(
    tmp_path: Path,
    file_name: str,
    text: str,
    manifest_mutator,
) -> tuple[CandidateRegistry, CandidateSpec]:
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
    manifest_mutator(manifest)
    _write_manifest(fixture_copy, manifest)

    registry = _registry(tmp_path, repo_root=tmp_path)
    candidate = build_g2_fixture_candidate(
        repo_root=tmp_path,
        manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json",
    )
    registry.register_candidate(candidate, actor="pytest")
    return registry, candidate


def _run_match(tmp_path: Path):
    registry, _ = _registered_g2_candidate(tmp_path)
    return canonical_replay.run_g3_canonical_replay_fixture(
        registry=registry,
        report_path=None,
    )


def _matched_fields(tmp_path: Path):
    run = _run_match(tmp_path)
    return (
        run.v1_replay.output.to_allowed_fields(),
        run.v2_replay.output.to_allowed_fields(),
    )


def test_g3_requires_registered_candidate(tmp_path):
    registry = _registry(tmp_path)

    with pytest.raises(G3ReplayError, match="existing registered candidate"):
        canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)


def test_g3_requires_manifest(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    registry, _ = _registered_g2_candidate(tmp_path, repo_root=tmp_path)
    (fixture_copy / "synthetic_manifest.json").unlink()

    with pytest.raises(G3ReplayError, match="manifest_uri does not exist"):
        canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)


def test_g3_rejects_tier2_candidate(tmp_path):
    registry = _registry(tmp_path)
    base = build_g2_fixture_candidate()
    manifest_uri = _write_tier2_manifest(tmp_path)
    bad = _candidate_from_g2(
        base,
        manifest_uri=manifest_uri,
        data_snapshot={
            "dataset": "tier2_fixture_rejected",
            "asof": "2026-05-09",
            "manifest_sha256": compute_sha256(manifest_uri),
        },
    )
    registry.register_candidate(bad, actor="pytest")

    with pytest.raises(G3ReplayError, match="Tier 2/non-fixture"):
        canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)


def test_g3_runs_exactly_one_fixture_candidate(tmp_path):
    registry, candidate = _registered_g2_candidate(tmp_path)
    duplicate = build_g2_fixture_candidate(candidate_id="PH65_G2_SYNTHETIC_FIXTURE_002")
    registry.register_candidate(duplicate, actor="pytest")

    with pytest.raises(G3ReplayError, match="exactly one fixture candidate"):
        canonical_replay.run_g3_canonical_replay_fixture(
            registry=registry,
            candidate_id=candidate.candidate_id,
            report_path=None,
        )


def test_g3_calls_v1_canonical_replay_path(tmp_path, monkeypatch):
    registry, _ = _registered_g2_candidate(tmp_path)
    original = canonical_replay.core_engine.run_simulation
    calls = []

    def wrapped(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(canonical_replay.core_engine, "run_simulation", wrapped)
    run = canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)

    assert calls
    assert calls[0]["strict_missing_returns"] is True
    assert run.v1_replay.engine_name == V1_CANONICAL_ENGINE_NAME
    assert run.v1_replay.engine_rows == 2


def test_g3_compares_only_allowed_mechanical_fields(tmp_path):
    v1_fields, v2_fields = _matched_fields(tmp_path)
    v1_fields["not_allowed"] = "ignored"
    v2_fields["score"] = 999
    comparison = compare_allowed_mechanical_fields(v1_fields, v2_fields)

    assert comparison["comparison_fields"] == list(ALLOWED_COMPARISON_FIELDS)
    assert set(comparison["field_results"]) == set(ALLOWED_COMPARISON_FIELDS)
    assert "not_allowed" not in comparison["field_results"]
    assert "score" not in comparison["field_results"]


def test_g3_detects_v1_v2_position_mismatch(tmp_path):
    v1_fields, v2_fields = _matched_fields(tmp_path)
    altered = deepcopy(v2_fields)
    altered["positions"][0]["quantity"] += 1.0

    comparison = compare_allowed_mechanical_fields(v1_fields, altered)

    assert comparison["comparison_result"] == "mismatch"
    assert comparison["mismatch_fields"] == ["positions"]
    assert comparison["mismatch_count"] == 1


def test_g3_detects_v1_v2_cash_mismatch(tmp_path):
    v1_fields, v2_fields = _matched_fields(tmp_path)
    altered = deepcopy(v2_fields)
    altered["cash"][0]["value"] += 1.0

    comparison = compare_allowed_mechanical_fields(v1_fields, altered)

    assert comparison["mismatch_fields"] == ["cash"]
    assert comparison["mismatch_count"] == 1


def test_g3_detects_v1_v2_cost_mismatch(tmp_path):
    v1_fields, v2_fields = _matched_fields(tmp_path)
    altered = deepcopy(v2_fields)
    altered["transaction_cost"][0]["value"] += 1.0

    comparison = compare_allowed_mechanical_fields(v1_fields, altered)

    assert comparison["mismatch_fields"] == ["transaction_cost"]
    assert comparison["mismatch_count"] == 1


def test_g3_v2_still_promotion_ready_false_after_match(tmp_path):
    run = _run_match(tmp_path)

    assert run.report["comparison_result"] == "match"
    assert run.report["mismatch_count"] == 0
    assert run.report["promotion_ready"] is False
    assert run.report["canonical_engine_required"] is True
    assert run.v2_replay.promotion_ready is False


def test_g3_match_does_not_create_promotion_packet(tmp_path):
    run = _run_match(tmp_path)

    assert run.report["comparison_result"] == "match"
    assert "promotion_packet" not in run.report
    assert not list(tmp_path.rglob("*promotion*"))


def test_g3_cannot_emit_alert_or_broker_action(tmp_path):
    run = _run_match(tmp_path)
    source = "\n".join(
        [
            inspect.getsource(canonical_replay),
            inspect.getsource(compare_allowed_mechanical_fields),
        ]
    )

    assert run.report["boundary_verdict"] == "v2_blocked_from_promotion"
    assert "emit_alert" not in source
    assert "submit_order" not in source
    assert "BrokerPort" not in source
    assert "broker_api" not in source
    assert "alpaca" not in source.lower()
    assert "OpenClaw" not in source
    assert "notifier" not in source


def test_g3_replay_report_has_manifest_and_hash(tmp_path):
    registry, _ = _registered_g2_candidate(tmp_path)
    report_path = tmp_path / "g3_canonical_replay_report.json"
    run = canonical_replay.run_g3_canonical_replay_fixture(
        registry=registry,
        report_path=report_path,
    )
    manifest = load_manifest(run.report_manifest_path)

    assert run.report_path == report_path
    assert run.report_manifest_path == Path(f"{report_path}.manifest.json")
    assert manifest["sha256"] == compute_sha256(report_path)
    assert manifest["extra"]["candidate_id"] == G2_SYNTHETIC_CANDIDATE_ID
    assert run.report["manifest_sha256"] == compute_sha256(MANIFEST_URI)


def test_g3_non_finite_fixture_still_fails_closed(tmp_path):
    registry, _ = _registered_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,100.00\n2020-01-02,BBB,-inf\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(G3ReplayError, match=r"bad value class: -inf"):
        canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)


def test_g3_manifest_row_count_and_date_range_reconciled(tmp_path):
    registry, _ = _registered_mutated_fixture(
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

    with pytest.raises(G3ReplayError, match="manifest row_count mismatch"):
        canonical_replay.run_g3_canonical_replay_fixture(registry=registry, report_path=None)
