from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import SOURCE_QUALITY_OPERATIONAL
from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.fast_sim.simulator import SyntheticFastProxySimulator
from v2_discovery.replay import canonical_real_replay
from v2_discovery.replay import canonical_replay_report
from v2_discovery.replay.canonical_real_replay import G5_DEFAULT_REPORT_PATH
from v2_discovery.replay.canonical_real_replay import G5ReplayError
from v2_discovery.replay.canonical_real_replay import build_predeclared_neutral_weights
from v2_discovery.replay.canonical_real_replay import run_g5_single_canonical_replay


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


def _load_manifest_copy(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _rewrite_manifest(manifest_path: Path, manifest: dict) -> None:
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _rewrite_data(artifact_path: Path, mutator) -> None:
    data = pd.read_parquet(artifact_path)
    mutated = mutator(data.copy())
    mutated.to_parquet(artifact_path, index=False)


def _run_tmp(artifact_path: Path, manifest_path: Path, **kwargs):
    return run_g5_single_canonical_replay(
        artifact_uri=artifact_path,
        manifest_uri=manifest_path,
        repo_root=Path.cwd(),
        report_path=None,
        **kwargs,
    )


def test_g5_requires_canonical_source_quality(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_NON_CANONICAL
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_yfinance_or_tier2_source(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_CANONICAL
    manifest["provider"] = "yfinance"
    manifest["provider_feed"] = "public_api"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="non-canonical provider"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_alpaca_operational_source(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_OPERATIONAL
    manifest["provider"] = "alpaca"
    manifest["provider_feed"] = "iex"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g5_requires_manifest(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest_path.unlink()

    with pytest.raises(G5ReplayError, match="requires a manifest"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_manifest_hash_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = "0" * 64
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="hash mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_row_count_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["row_count"] += 1
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="row_count mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_date_range_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["date_range"]["end"] = "1999-01-01"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="date_range mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g5_rejects_nan_inf_prices(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    _rewrite_data(artifact, lambda data: data.assign(tri=[float("inf")] + data["tri"].tolist()[1:]))
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G5ReplayError, match="finite_numeric_check"):
        _run_tmp(artifact, manifest_path)


def test_g5_uses_predeclared_weights_only():
    data = pd.read_parquet(FIXTURE_ARTIFACT)
    weights = build_predeclared_neutral_weights(data)

    assert weights.shape == (41, 3)
    assert (weights.sum(axis=1).round(12) == 1.0).all()
    assert set(weights.columns) == set(data["permno"].unique())

    with pytest.raises(G5ReplayError, match="predeclared neutral"):
        build_predeclared_neutral_weights(data, weight_mode="dynamic")


def test_g5_rejects_signal_function_or_ranker():
    with pytest.raises(G5ReplayError, match="predeclared neutral"):
        run_g5_single_canonical_replay(report_path=None, signal_function=lambda frame: frame)

    with pytest.raises(G5ReplayError, match="predeclared neutral"):
        run_g5_single_canonical_replay(report_path=None, ranker=lambda frame: frame)


def test_g5_calls_core_engine_replay_path(monkeypatch):
    original = canonical_real_replay.core_engine.run_simulation
    calls = []

    def wrapped(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(canonical_real_replay.core_engine, "run_simulation", wrapped)
    run = run_g5_single_canonical_replay(report_path=None)

    assert calls
    assert calls[0]["strict_missing_returns"] is True
    assert run.replay.engine_name == "core.engine.run_simulation"
    assert run.replay.engine_rows == 41


def test_g5_does_not_call_v2_proxy(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("V2 proxy must not run in G5")

    monkeypatch.setattr(SyntheticFastProxySimulator, "run", fail_if_called)
    run = run_g5_single_canonical_replay(report_path=None)

    assert run.report["mechanical_replay_result"] == "completed"
    assert "v2_engine_name" not in run.report
    assert "proxy_run_id" not in run.report


def test_g5_report_contains_no_alpha_or_performance_metrics():
    run = run_g5_single_canonical_replay(report_path=None)
    forbidden = {
        "alpha",
        "cagr",
        "drawdown",
        "max_drawdown",
        "pnl",
        "rank",
        "score",
        "sharpe",
        "gross_ret",
        "net_ret",
    }

    assert forbidden.isdisjoint(run.report)
    assert run.report["source_quality"] == "canonical"
    assert run.report["mechanical_replay_result"] == "completed"


def test_g5_report_has_promotion_ready_false():
    run = run_g5_single_canonical_replay(report_path=None)

    assert run.report["promotion_ready"] is False
    assert run.report["alerts_emitted"] is False
    assert run.report["broker_calls"] is False


def test_g5_does_not_emit_alert_or_broker_action():
    source = "\n".join(
        [
            inspect.getsource(canonical_real_replay),
            inspect.getsource(canonical_replay_report),
        ]
    )
    run = run_g5_single_canonical_replay(report_path=None)

    assert run.report["alerts_emitted"] is False
    assert run.report["broker_calls"] is False
    assert "emit_alert" not in source
    assert "submit_order" not in source
    assert "BrokerPort" not in source
    assert "broker_api" not in source
    assert "OpenClaw" not in source
    assert "notifier" not in source


def test_g5_default_execution_does_not_refresh_report_artifact():
    report_path = Path(G5_DEFAULT_REPORT_PATH)
    before = report_path.read_bytes() if report_path.exists() else None

    run = run_g5_single_canonical_replay()

    assert run.report_path is None
    assert run.report_manifest_path is None
    assert (report_path.read_bytes() if report_path.exists() else None) == before


def test_g5_optional_report_has_manifest_and_required_fields(tmp_path):
    report_path = tmp_path / "g5_single_canonical_replay_report.json"
    run = run_g5_single_canonical_replay(report_path=report_path)
    report_manifest = load_manifest(run.report_manifest_path)

    assert run.report_path == report_path
    assert run.report_manifest_path == Path(f"{report_path}.manifest.json")
    assert report_manifest["sha256"] == compute_sha256(report_path)
    assert report_manifest["extra"]["replay_run_id"] == "PH65_G5_SINGLE_CANONICAL_REPLAY_001"
    assert run.report["manifest_sha256"] == compute_sha256(FIXTURE_MANIFEST)
    assert run.report["row_count"] == 123
    assert run.report["symbol_count"] == 3
    assert run.report["date_range"] == {"start": "2024-01-02", "end": "2024-02-29"}
    assert run.report["engine_name"] == "core.engine.run_simulation"
    assert run.report["promotion_ready"] is False
    assert run.report["alerts_emitted"] is False
    assert run.report["broker_calls"] is False


def test_g5_mechanical_outputs_match_golden_frames():
    run = run_g5_single_canonical_replay(report_path=None)
    expected_ledger = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "cash": 0.0,
                "turnover": 1.0,
                "transaction_cost": 100.0,
                "gross_exposure": 1.0,
                "net_exposure": 1.0,
            },
            {
                "date": "2024-01-03",
                "cash": 0.0,
                "turnover": 0.005913,
                "transaction_cost": 0.585106,
                "gross_exposure": 1.0,
                "net_exposure": 1.0,
            },
            {
                "date": "2024-01-04",
                "cash": 0.0,
                "turnover": 0.005471,
                "transaction_cost": 0.541869,
                "gross_exposure": 1.0,
                "net_exposure": 1.0,
            },
        ],
        columns=[
            "date",
            "cash",
            "turnover",
            "transaction_cost",
            "gross_exposure",
            "net_exposure",
        ],
    )
    expected_positions = pd.DataFrame(
        [
            {
                "date": "2024-01-02",
                "permno": 10104,
                "quantity": 124.790475,
                "market_value": 33300.0,
            },
            {
                "date": "2024-01-02",
                "permno": 10107,
                "quantity": 36.079507,
                "market_value": 33300.0,
            },
            {
                "date": "2024-01-02",
                "permno": 86580,
                "quantity": 3.328444,
                "market_value": 33300.0,
            },
        ],
        columns=["date", "permno", "quantity", "market_value"],
    )

    assert_frame_equal(run.replay.ledger.head(3).reset_index(drop=True), expected_ledger)
    assert_frame_equal(run.replay.positions.head(3).reset_index(drop=True), expected_positions)
