from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from data.provenance import ManifestInput
from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import SOURCE_QUALITY_OPERATIONAL
from data.provenance import build_manifest
from data.provenance import compute_sha256
from data.provenance import load_manifest
from data.provenance import write_manifest
from v2_discovery.readiness import canonical_readiness
from v2_discovery.readiness import canonical_slice
from v2_discovery.readiness.canonical_readiness import G4_DEFAULT_REPORT_PATH
from v2_discovery.readiness.canonical_readiness import run_g4_canonical_readiness
from v2_discovery.readiness.schemas import G4_DEFAULT_DATASET_NAME
from v2_discovery.readiness.schemas import G4_PRIMARY_KEY
from v2_discovery.readiness.schemas import G4_REQUIRED_COLUMNS
from v2_discovery.readiness.schemas import G4ReadinessError


FIXTURE_ARTIFACT = Path("data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet")
FIXTURE_MANIFEST = Path(f"{FIXTURE_ARTIFACT}.manifest.json")


def _copy_fixture(tmp_path: Path) -> tuple[Path, Path]:
    target = tmp_path / "data" / "fixtures" / "g4" / FIXTURE_ARTIFACT.name
    target.parent.mkdir(parents=True)
    target.write_bytes(FIXTURE_ARTIFACT.read_bytes())
    manifest = json.loads(FIXTURE_MANIFEST.read_text(encoding="utf-8"))
    manifest["artifact_path"] = str(target)
    manifest["sha256"] = compute_sha256(target)
    manifest_path = target.with_suffix(target.suffix + ".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return target, manifest_path


def _rewrite_manifest(manifest_path: Path, manifest: dict) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _load_manifest_copy(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _rewrite_data(artifact_path: Path, mutator) -> None:
    data = pd.read_parquet(artifact_path)
    mutated = mutator(data.copy())
    mutated.to_parquet(artifact_path, index=False)


def _run_tmp(artifact_path: Path, manifest_path: Path, **kwargs):
    return run_g4_canonical_readiness(
        artifact_uri=artifact_path,
        manifest_uri=manifest_path,
        repo_root=Path.cwd(),
        report_path=None,
        **kwargs,
    )


def _write_sidecar_manifest(tmp_path: Path, *, end: str) -> Path:
    sidecar = tmp_path / "sidecar.parquet"
    data = pd.DataFrame(
        {
            "date": [pd.Timestamp("2023-01-03")],
            "permno": [10107],
            "price": [100.0],
            "total_return": [0.0],
        }
    )
    data.to_parquet(sidecar, index=False)
    manifest = build_manifest(
        ManifestInput(
            artifact_path=sidecar,
            source_quality=SOURCE_QUALITY_CANONICAL,
            provider="terminal_zero",
            provider_feed="sp500_pro_sidecar",
            license_scope="internal_research_validation",
            row_count=1,
            date_range={"start": "2023-01-03", "end": end},
            schema_version="1.0.0",
            extra={
                "dataset_name": "stale_sidecar_negative_test",
                "source_tier": "tier0",
                "primary_key": ["date", "permno"],
            },
        )
    )
    manifest["schema"] = {"columns": ["date", "permno", "price", "total_return"]}
    return write_manifest(manifest, sidecar.with_suffix(sidecar.suffix + ".manifest.json"))


def test_g4_requires_tier0_canonical_source(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["extra"]["source_tier"] = "tier2"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="source_tier=tier0"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_tier2_yfinance_artifact(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_NON_CANONICAL
    manifest["provider"] = "yfinance"
    manifest["provider_feed"] = "public_api"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_operational_alpaca_artifact(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_OPERATIONAL
    manifest["provider"] = "alpaca"
    manifest["provider_feed"] = "iex"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g4_requires_manifest(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest_path.unlink()

    with pytest.raises(G4ReadinessError, match="requires a manifest"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_manifest_hash_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = "0" * 64
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="hash mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_row_count_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["row_count"] += 1
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="row_count mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_date_range_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["date_range"]["start"] = "1999-01-01"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="date_range mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_schema_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["schema"]["columns"] = list(reversed(manifest["schema"]["columns"]))
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="schema mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_nan_inf_prices(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    _rewrite_data(artifact, lambda data: data.assign(raw_close=[float("inf")] + data["raw_close"].tolist()[1:]))
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="finite_numeric_check"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_duplicate_date_symbol_keys(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)

    def mutate(data: pd.DataFrame) -> pd.DataFrame:
        return pd.concat([data, data.iloc[[0]]], ignore_index=True)

    _rewrite_data(artifact, mutate)
    manifest = _load_manifest_copy(manifest_path)
    manifest["row_count"] += 1
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="duplicate_key_check"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_non_monotonic_dates(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)

    def mutate(data: pd.DataFrame) -> pd.DataFrame:
        first_permno = data["permno"].iloc[0]
        mask = data["permno"] == first_permno
        group = data.loc[mask].copy().iloc[::-1]
        data.loc[mask, :] = group.to_numpy()
        return data

    _rewrite_data(artifact, mutate)
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="date_monotonicity_check"):
        _run_tmp(artifact, manifest_path)


def test_g4_rejects_negative_or_zero_prices(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    _rewrite_data(artifact, lambda data: data.assign(raw_close=[0.0] + data["raw_close"].tolist()[1:]))
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G4ReadinessError, match="price_domain_check"):
        _run_tmp(artifact, manifest_path)


def test_g4_warns_or_blocks_stale_sidecar_when_required(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    sidecar_manifest = _write_sidecar_manifest(tmp_path, end="2023-11-27")

    with pytest.raises(G4ReadinessError, match="sidecar is stale"):
        _run_tmp(
            artifact,
            manifest_path,
            sidecar_required=True,
            sidecar_manifest_uri=sidecar_manifest,
        )


def test_g4_report_contains_no_alpha_or_performance_metrics():
    run = run_g4_canonical_readiness(report_path=None)

    forbidden = {
        "alpha",
        "cagr",
        "drawdown",
        "max_drawdown",
        "pnl",
        "rank",
        "score",
        "sharpe",
    }
    assert forbidden.isdisjoint(run.report)
    assert run.report["source_quality"] == "canonical"
    assert run.report["sidecar_required"] is False
    assert run.report["ready_for_g5"] is True


def test_g4_does_not_touch_registry_candidate_status():
    registry_events = Path("data/registry/candidate_events.jsonl")
    registry_snapshot = Path("data/registry/candidate_snapshot.json")
    before = {
        path: path.read_bytes()
        for path in (registry_events, registry_snapshot)
        if path.exists()
    }
    source = "\n".join(
        [
            inspect.getsource(canonical_readiness),
            inspect.getsource(canonical_slice),
        ]
    )

    run_g4_canonical_readiness(report_path=None)

    assert "CandidateRegistry" not in source
    assert "register_candidate" not in source
    assert "change_status" not in source
    assert "add_note" not in source
    assert before == {
        path: path.read_bytes()
        for path in before
    }


def test_g4_does_not_emit_alert_or_broker_action():
    source = "\n".join(
        [
            inspect.getsource(canonical_readiness),
            inspect.getsource(canonical_slice),
        ]
    )

    run = run_g4_canonical_readiness(report_path=None)

    assert run.report["ready_for_g5"] is True
    assert "emit_alert" not in source
    assert "submit_order" not in source
    assert "BrokerPort" not in source
    assert "broker_api" not in source
    assert "alpaca" not in source.lower()
    assert "OpenClaw" not in source
    assert "notifier" not in source


def test_g4_default_execution_does_not_refresh_report_artifact():
    report_path = Path(G4_DEFAULT_REPORT_PATH)
    before = report_path.read_bytes() if report_path.exists() else None

    run = run_g4_canonical_readiness()

    assert run.report_path is None
    assert run.report_manifest_path is None
    assert (report_path.read_bytes() if report_path.exists() else None) == before


def test_g4_optional_report_has_manifest_and_required_fields(tmp_path):
    report_path = tmp_path / "g4_real_canonical_readiness_report.json"
    run = run_g4_canonical_readiness(report_path=report_path)
    report_manifest = load_manifest(run.report_manifest_path)

    assert run.report_path == report_path
    assert run.report_manifest_path == Path(f"{report_path}.manifest.json")
    assert report_manifest["sha256"] == compute_sha256(report_path)
    assert run.report["readiness_run_id"] == "PH65_G4_REAL_CANONICAL_READINESS_001"
    assert run.report["dataset_name"] == G4_DEFAULT_DATASET_NAME
    assert run.report["manifest_sha256"] == compute_sha256(FIXTURE_MANIFEST)
    assert run.report["row_count"] == 123
    assert run.report["date_range"] == {"start": "2024-01-02", "end": "2024-02-29"}
    assert run.report["symbol_count"] == 3
    assert run.report["primary_key"] == list(G4_PRIMARY_KEY)
    assert tuple(run.slice.data.columns) == G4_REQUIRED_COLUMNS
