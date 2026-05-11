from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import SOURCE_QUALITY_OPERATIONAL
from data.provenance import compute_sha256
from data.provenance import load_manifest
from v2_discovery.fast_sim.ledger import build_synthetic_ledger
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.replay import mechanical_comparison_report
from v2_discovery.replay import real_slice_v1_v2_comparison
from v2_discovery.replay.real_slice_v1_v2_comparison import G6_COMPARISON_FIELDS
from v2_discovery.replay.real_slice_v1_v2_comparison import G6_DEFAULT_REPORT_PATH
from v2_discovery.replay.real_slice_v1_v2_comparison import G6ComparisonError
from v2_discovery.replay.real_slice_v1_v2_comparison import compare_g6_mechanical_fields
from v2_discovery.replay.real_slice_v1_v2_comparison import run_g6_v1_v2_real_slice_mechanical_comparison


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
    return run_g6_v1_v2_real_slice_mechanical_comparison(
        artifact_uri=artifact_path,
        manifest_uri=manifest_path,
        repo_root=Path.cwd(),
        report_path=None,
        **kwargs,
    )


def _matched_run():
    return run_g6_v1_v2_real_slice_mechanical_comparison(report_path=None)


def test_g6_requires_canonical_source_quality(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_NON_CANONICAL
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_yfinance_or_tier2_source(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_CANONICAL
    manifest["provider"] = "yfinance"
    manifest["provider_feed"] = "public_api"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="non-canonical provider"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_alpaca_operational_source(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["source_quality"] = SOURCE_QUALITY_OPERATIONAL
    manifest["provider"] = "alpaca"
    manifest["provider_feed"] = "iex"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="Tier 0 canonical"):
        _run_tmp(artifact, manifest_path)


def test_g6_requires_manifest(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest_path.unlink()

    with pytest.raises(G6ComparisonError, match="requires a manifest"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_manifest_hash_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = "0" * 64
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="hash mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_row_count_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["row_count"] += 1
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="row_count mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_date_range_mismatch(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    manifest = _load_manifest_copy(manifest_path)
    manifest["date_range"]["end"] = "1999-01-01"
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="date_range mismatch"):
        _run_tmp(artifact, manifest_path)


def test_g6_rejects_nan_inf_values(tmp_path):
    artifact, manifest_path = _copy_fixture(tmp_path)
    _rewrite_data(artifact, lambda data: data.assign(total_ret=[float("nan")] + data["total_ret"].tolist()[1:]))
    manifest = _load_manifest_copy(manifest_path)
    manifest["sha256"] = compute_sha256(artifact)
    _rewrite_manifest(manifest_path, manifest)

    with pytest.raises(G6ComparisonError, match="finite_numeric_check"):
        _run_tmp(artifact, manifest_path)


def test_g6_uses_predeclared_weights_only():
    run = _matched_run()

    assert run.report["comparison_result"] == "match"
    assert run.report["field_results"]["positions"] == "match"

    with pytest.raises(G6ComparisonError, match="predeclared neutral"):
        run_g6_v1_v2_real_slice_mechanical_comparison(report_path=None, weight_mode="dynamic")

    with pytest.raises(G6ComparisonError, match="predeclared neutral"):
        run_g6_v1_v2_real_slice_mechanical_comparison(report_path=None, signal_function=lambda frame: frame)


def test_g6_calls_v1_core_engine(monkeypatch):
    original = real_slice_v1_v2_comparison.run_g5_single_canonical_replay
    calls = []

    def wrapped(*args, **kwargs):
        calls.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(real_slice_v1_v2_comparison, "run_g5_single_canonical_replay", wrapped)
    run = run_g6_v1_v2_real_slice_mechanical_comparison(report_path=None)

    assert calls
    assert calls[0]["report_path"] is None
    assert run.report["engine_name"]["v1"] == "core.engine.run_simulation"


def test_g6_calls_v2_proxy(monkeypatch):
    calls = []

    def wrapped(*args, **kwargs):
        calls.append((args, kwargs))
        return build_synthetic_ledger(*args, **kwargs)

    monkeypatch.setattr(real_slice_v1_v2_comparison, "build_synthetic_ledger", wrapped)
    run = run_g6_v1_v2_real_slice_mechanical_comparison(report_path=None)

    assert calls
    assert run.report["engine_name"]["v2"] == PROXY_ENGINE_NAME
    assert run.report["v2_promotion_ready"] is False


def test_g6_compares_only_mechanical_fields():
    run = _matched_run()

    assert run.report["comparison_fields"] == list(G6_COMPARISON_FIELDS)
    assert set(run.report["field_results"]) == set(G6_COMPARISON_FIELDS)
    assert run.report["field_results"]["engine_name"] == "recorded"
    assert run.report["field_results"]["engine_version"] == "recorded"
    assert "candidate_id" not in run.report["comparison_fields"]
    assert "alpha" not in run.report["comparison_fields"]
    assert "rank" not in run.report["comparison_fields"]


def test_g6_detects_position_mismatch():
    run = _matched_run()
    altered = deepcopy(run.comparison.v2_output)
    positions = altered.positions.copy()
    positions.loc[0, "quantity"] += 1.0
    altered = altered.__class__(**{**altered.__dict__, "positions": positions})

    comparison = compare_g6_mechanical_fields(run.comparison.v1_output, altered)

    assert comparison["comparison_result"] == "mismatch"
    assert comparison["mismatch_fields"] == ["positions"]
    assert comparison["mismatch_count"] == 1


def test_g6_detects_cash_mismatch():
    run = _matched_run()
    altered = deepcopy(run.comparison.v2_output)
    ledger = altered.ledger.copy()
    ledger.loc[0, "cash"] += 1.0
    altered = altered.__class__(**{**altered.__dict__, "ledger": ledger})

    comparison = compare_g6_mechanical_fields(run.comparison.v1_output, altered)

    assert comparison["mismatch_fields"] == ["cash"]
    assert comparison["mismatch_count"] == 1


def test_g6_detects_transaction_cost_mismatch():
    run = _matched_run()
    altered = deepcopy(run.comparison.v2_output)
    ledger = altered.ledger.copy()
    ledger.loc[0, "transaction_cost"] += 1.0
    altered = altered.__class__(**{**altered.__dict__, "ledger": ledger})

    comparison = compare_g6_mechanical_fields(run.comparison.v1_output, altered)

    assert comparison["mismatch_fields"] == ["transaction_cost"]
    assert comparison["mismatch_count"] == 1


def test_g6_v2_remains_promotion_ready_false_after_match():
    run = _matched_run()

    assert run.report["comparison_result"] == "match"
    assert run.report["promotion_ready"] is False
    assert run.report["v2_promotion_ready"] is False
    assert run.report["canonical_engine_required"] is True


def test_g6_no_alpha_or_performance_fields():
    run = _matched_run()
    forbidden = {
        "alpha",
        "cagr",
        "drawdown",
        "max_drawdown",
        "pnl",
        "rank",
        "score",
        "sharpe",
        "signal_strength",
        "buy_sell_decision",
        "promotion_verdict",
        "paper_alert",
        "gross_ret",
        "net_ret",
    }

    assert forbidden.isdisjoint(run.report)
    assert forbidden.isdisjoint(run.report["comparison_fields"])
    assert run.report["source_quality"] == "canonical"


def test_g6_no_alert_or_broker_action():
    source = "\n".join(
        [
            inspect.getsource(real_slice_v1_v2_comparison),
            inspect.getsource(mechanical_comparison_report),
        ]
    )
    run = _matched_run()

    assert run.report["alerts_emitted"] is False
    assert run.report["broker_calls"] is False
    assert "emit_alert" not in source
    assert "submit_order" not in source
    assert "BrokerPort" not in source
    assert "broker_api" not in source
    assert "OpenClaw" not in source
    assert "notifier" not in source


def test_g6_default_execution_does_not_refresh_report_artifact():
    report_path = Path(G6_DEFAULT_REPORT_PATH)
    before = report_path.read_bytes() if report_path.exists() else None

    run = run_g6_v1_v2_real_slice_mechanical_comparison()

    assert run.report_path is None
    assert run.report_manifest_path is None
    assert (report_path.read_bytes() if report_path.exists() else None) == before


def test_g6_optional_report_has_manifest_and_strict_frame_match(tmp_path):
    report_path = tmp_path / "g6_v1_v2_real_slice_mechanical_report.json"
    run = run_g6_v1_v2_real_slice_mechanical_comparison(report_path=report_path)
    report_manifest = load_manifest(run.report_manifest_path)

    assert run.report_path == report_path
    assert run.report_manifest_path == Path(f"{report_path}.manifest.json")
    assert report_manifest["sha256"] == compute_sha256(report_path)
    assert report_manifest["extra"]["comparison_run_id"] == "PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_001"
    assert run.report["manifest_sha256"] == compute_sha256(FIXTURE_MANIFEST)
    assert run.report["row_count"] == 123
    assert run.report["symbol_count"] == 3
    assert run.report["date_range"] == {"start": "2024-01-02", "end": "2024-02-29"}
    assert run.report["comparison_result"] == "match"
    assert run.report["mismatch_count"] == 0
    assert_frame_equal(run.comparison.v1_output.positions, run.comparison.v2_output.positions)
    assert_frame_equal(run.comparison.v1_output.ledger, run.comparison.v2_output.ledger)
