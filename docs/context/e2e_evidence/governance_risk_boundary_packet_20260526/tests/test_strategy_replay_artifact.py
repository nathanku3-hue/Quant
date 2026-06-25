from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from core import data_orchestrator as data_orch
from strategies.optimizer import OptimizationMethod


def _fake_replay_inputs(tmp_path: Path, monkeypatch) -> data_orch.StrategyReplayInputs:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()
    (processed / "prices_tri.parquet").write_bytes(b"signature-only")

    idx = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])
    returns = pd.DataFrame({101: [0.0, 0.01, 0.02], 202: [0.0, -0.01, 0.01]}, index=idx)
    prices = pd.DataFrame({101: [100.0, 101.0, 103.0], 202: [50.0, 49.5, 50.0]}, index=idx)
    macro = pd.DataFrame({"spy_close": [500.0, 501.0, 502.0]}, index=idx)

    monkeypatch.setattr(
        data_orch,
        "load_dashboard_data",
        lambda **kwargs: (
            returns,
            prices,
            macro,
            {101: "AAA", 202: "BBB"},
            {"sector_map": {101: "Technology", 202: "Industrials"}},
        ),
    )
    return data_orch.load_strategy_replay_inputs(
        as_of_date="2026-01-05",
        start_date="2026-01-02",
        end_date="2026-01-31",
        method="rule_of_100",
        controls={"sector_cap": False, "rebalance": "daily"},
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )


def test_write_strategy_replay_artifact_atomic_uses_temp_replace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    inputs = _fake_replay_inputs(tmp_path, monkeypatch)
    output_path = tmp_path / "strategy_replay.parquet"
    real_replace = data_orch.os.replace
    replace_calls: list[tuple[Path, Path]] = []

    def _recording_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(data_orch.os, "replace", _recording_replace)

    result = data_orch.write_strategy_replay_artifact_atomic(
        inputs,
        artifact_path=output_path,
    )

    manifest_path = Path(result["manifest_path"])
    assert Path(result["artifact_path"]) == output_path
    assert output_path.exists()
    assert manifest_path.exists()
    assert [dst for _src, dst in replace_calls] == [output_path, manifest_path]
    assert all(src.parent == dst.parent and src.name.startswith(".") for src, dst in replace_calls)
    assert not list(tmp_path.glob(".*.tmp"))

    artifact = pd.read_parquet(output_path)
    assert set(artifact["artifact_scope"]) == {"display_only_strategy_replay_input"}
    assert set(artifact["matrix"]) == {"price", "return"}
    assert pd.to_datetime(artifact["date"]).max() == pd.Timestamp("2026-01-05")
    assert "2026-01-06" not in set(pd.to_datetime(artifact["date"]).dt.strftime("%Y-%m-%d"))

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["display_only"] is True
    assert manifest["canonical_market_data_write"] is False
    assert manifest["cache_key"] == inputs.cache_key
    assert manifest["ticker_map"] == {"101": "AAA", "202": "BBB"}
    assert manifest["cache_signature"]["method"] == "rule_of_100"
    assert manifest["metadata"]["effective_date_range"]["end"] == "2026-01-05"


def test_strategy_replay_artifact_cache_path_changes_with_controls(
    tmp_path: Path,
) -> None:
    processed = tmp_path / "processed"
    static = tmp_path / "static"
    processed.mkdir()
    static.mkdir()
    (processed / "prices_tri.parquet").write_bytes(b"same-source")

    base = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": False},
        start_date="2026-01-02",
        end_date="2026-01-31",
        as_of_date="2026-01-05",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )
    changed = data_orch.build_strategy_replay_cache_signature(
        method="rule_of_100",
        controls={"sector_cap": True},
        start_date="2026-01-02",
        end_date="2026-01-31",
        as_of_date="2026-01-05",
        max_weight=0.35,
        processed_dir=processed,
        static_dir=static,
    )

    assert data_orch.strategy_replay_cache_path(base, cache_dir=tmp_path) != data_orch.strategy_replay_cache_path(
        changed,
        cache_dir=tmp_path,
    )


def test_strategy_replay_artifact_frame_handles_one_sided_matrix() -> None:
    idx = pd.to_datetime(["2026-01-02"])
    returns = pd.DataFrame({101: [0.01]}, index=idx)
    inputs = data_orch.StrategyReplayInputs(
        as_of_date=pd.Timestamp("2026-01-02"),
        prices=pd.DataFrame(),
        returns=returns,
        ticker_map={101: "AAA"},
        cache_signature={"method": "unit"},
        cache_key="unit-key",
        metadata={},
    )

    artifact = data_orch.strategy_replay_inputs_to_frame(inputs)

    assert list(artifact.columns[: len(data_orch.STRATEGY_REPLAY_ARTIFACT_COLUMNS)]) == data_orch.STRATEGY_REPLAY_ARTIFACT_COLUMNS
    assert artifact.loc[0, "matrix"] == "return"
    assert float(artifact.loc[0, "101"]) == 0.01


def test_write_strategy_replay_artifact_rejects_canonical_data_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    inputs = _fake_replay_inputs(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="display-only"):
        data_orch.write_strategy_replay_artifact_atomic(
            inputs,
            artifact_path=Path("data/processed/strategy_replay.parquet"),
        )


def test_write_strategy_replay_artifact_rejects_canonical_cache_dir_escape(
    tmp_path: Path,
    monkeypatch,
) -> None:
    inputs = _fake_replay_inputs(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="cache_dir"):
        data_orch.write_strategy_replay_artifact_atomic(
            inputs,
            cache_dir=Path("data/processed"),
        )


def test_write_strategy_replay_artifact_allows_nested_runtime_cache_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    inputs = _fake_replay_inputs(tmp_path, monkeypatch)

    result = data_orch.write_strategy_replay_artifact_atomic(
        inputs,
        cache_dir=Path("data/runtime_cache/strategy_replay/test_nested"),
    )

    artifact_path = Path(result["artifact_path"])
    assert artifact_path.exists()
    assert "data\\runtime_cache\\strategy_replay" in str(artifact_path) or "data/runtime_cache/strategy_replay" in str(artifact_path)


def test_nonfinite_manifest_payload_leaves_no_half_bundle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    inputs = _fake_replay_inputs(tmp_path, monkeypatch)
    inputs.metadata["bad_control"] = float("nan")
    output_path = tmp_path / "bad.parquet"

    with pytest.raises(ValueError):
        data_orch.write_strategy_replay_artifact_atomic(
            inputs,
            artifact_path=output_path,
        )

    assert not output_path.exists()
    assert not output_path.with_suffix(output_path.suffix + ".manifest.json").exists()


def test_strategy_replay_signature_rejects_nonfinite_controls(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="max_weight"):
        data_orch.build_strategy_replay_cache_signature(
            method="rule_of_100",
            controls={},
            start_date="2026-01-02",
            end_date="2026-01-31",
            as_of_date="2026-01-05",
            max_weight=float("nan"),
            processed_dir=tmp_path,
            static_dir=tmp_path,
        )

    with pytest.raises(ValueError, match="controls"):
        data_orch.build_strategy_replay_cache_signature(
            method="rule_of_100",
            controls={"bad": float("nan")},
            start_date="2026-01-02",
            end_date="2026-01-31",
            as_of_date="2026-01-05",
            max_weight=0.35,
            processed_dir=tmp_path,
            static_dir=tmp_path,
        )


def test_build_strategy_replay_artifact_script_has_no_provider_dependency() -> None:
    script_source = Path("scripts/build_strategy_replay_artifact.py").read_text(encoding="utf-8")

    assert "download_recent_close_prices" not in script_source
    assert "build_market_data_provider" not in script_source
    assert "yfinance" not in script_source.lower()


def test_build_strategy_replay_artifact_script_defaults_to_pit_universe() -> None:
    from scripts import build_strategy_replay_artifact as builder

    args = builder.build_parser().parse_args(["--as-of-date", "2026-01-05"])

    assert args.universe_mode == "r3000_pit"



# ---------------------------------------------------------------------------
# Selected-method-output artifact tests (strategies/strategy_replay writer)
# ---------------------------------------------------------------------------

from strategies import strategy_replay as strat_replay


def _fake_selected_method_bundle(tmp_path: Path) -> strat_replay.StrategyReplayBundle:
    """Build a minimal StrategyReplayBundle for testing the output artifact writer."""
    idx = pd.to_datetime(["2026-01-02", "2026-01-03"])
    replay = pd.DataFrame(
        {
            "date": ["2026-01-02", "2026-01-03"],
            "method": ["inverse_volatility", "inverse_volatility"],
            "ticker": ["AAA", "CASH"],
            "permno": ["101", "CASH"],
            "target_weight": [0.6, 0.4],
            "cash_residual": [0.4, 0.4],
            "asset_return": [0.01, 0.0],
            "weight_for_return": [0.6, 0.0],
            "return_contribution": [0.006, 0.0],
            "portfolio_return": [0.006, 0.006],
            "portfolio_equity": [1.006, 1.006],
            "cap_used": [0.35, 0.35],
            "cap_source": ["controls.max_weight"] * 2,
            "source": ["strategy_replay:inverse_volatility"] * 2,
            "status": ["ok", "ok"],
            "reason": ["method_replayed_directly"] * 2,
        }
    )
    event_ctx = strat_replay.StrategyReplayContext(
        context_type="event_annotations",
        frame=pd.DataFrame(columns=strat_replay.REPLAY_CONTEXT_COLUMNS),
        status="empty",
        reason="no_event_annotations_context_provided",
        source="test",
    )
    decision_ctx = strat_replay.StrategyReplayContext(
        context_type="decision_context",
        frame=pd.DataFrame(columns=strat_replay.REPLAY_CONTEXT_COLUMNS),
        status="empty",
        reason="no_decision_context_provided",
        source="test",
    )
    metadata = strat_replay.StrategyReplayRunMetadata(
        run_id="test_run_abc123",
        method_id="inverse_volatility",
        source_id="selected_method_replay:inverse_volatility:test_run_abc123",
        input_signatures=({"type": "test", "as_of_date": "2026-01-03"},),
        date_window={
            "requested_start": "2026-01-02",
            "requested_end": "2026-01-03",
            "replay_start": "2026-01-02",
            "replay_end": "2026-01-03",
        },
        row_counts={"daily_portfolio": 2, "event_annotations": 0, "buy_sell_decisions": 0, "total": 2},
        status_counts={"daily_portfolio": {"ok": 2}, "event_annotations": {"empty": 0}, "buy_sell_decisions": {"empty": 0}},
        timing={"started_at_utc": "2026-01-03T00:00:00Z", "completed_at_utc": "2026-01-03T00:00:01Z", "elapsed_ms": 1000.0},
    )
    return strat_replay.StrategyReplayBundle(
        replay=replay,
        event_context=event_ctx,
        decision_context=decision_ctx,
        run_metadata=metadata,
    )


def test_selected_method_replay_artifact_uses_temp_replace(tmp_path: Path) -> None:
    bundle = _fake_selected_method_bundle(tmp_path)
    output_path = tmp_path / "selected.parquet"
    real_replace = strat_replay.os.replace
    replace_calls: list[tuple[Path, Path]] = []

    def _recording_replace(src, dst):
        replace_calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    import unittest.mock
    with unittest.mock.patch.object(strat_replay.os, "replace", side_effect=_recording_replace):
        result = strat_replay.write_selected_method_replay_artifact_atomic(
            bundle, artifact_path=output_path,
        )

    manifest_path = Path(result["manifest_path"])
    assert output_path.exists()
    assert manifest_path.exists()
    assert [dst for _src, dst in replace_calls] == [output_path, manifest_path]
    assert all(src.name.startswith(".") for src, _dst in replace_calls)


def test_selected_method_replay_artifact_path_confinement(tmp_path: Path) -> None:
    bundle = _fake_selected_method_bundle(tmp_path)

    with pytest.raises(ValueError, match="data/runtime_cache/strategy_replay"):
        strat_replay.write_selected_method_replay_artifact_atomic(
            bundle, artifact_path=Path("data/processed/bad.parquet"),
        )

    with pytest.raises(ValueError, match="cache_dir"):
        strat_replay.write_selected_method_replay_artifact_atomic(
            bundle, cache_dir=Path("data/processed"),
        )


def test_selected_method_replay_artifact_manifest_shape(tmp_path: Path) -> None:
    bundle = _fake_selected_method_bundle(tmp_path)
    output_path = tmp_path / "manifest_check.parquet"

    result = strat_replay.write_selected_method_replay_artifact_atomic(
        bundle, artifact_path=output_path,
    )

    manifest = json.loads(Path(result["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest["artifact_type"] == "selected_method_replay_output"
    assert manifest["display_only"] is True
    assert manifest["canonical_market_data_write"] is False
    assert manifest["run_id"] == "test_run_abc123"
    assert manifest["source_id"] == "selected_method_replay:inverse_volatility:test_run_abc123"
    assert manifest["method_id"] == "inverse_volatility"
    assert manifest["date_window"]["replay_start"] == "2026-01-02"
    assert manifest["date_window"]["replay_end"] == "2026-01-03"
    assert manifest["row_counts"]["daily_portfolio"] == 2
    assert manifest["status_counts"]["daily_portfolio"] == {"ok": 2}
    run_meta = manifest["run_metadata"]
    assert run_meta["timing"]["elapsed_ms"] == 1000.0
    assert run_meta["timing"]["started_at_utc"] is not None


def test_selected_method_replay_artifact_cli_path() -> None:
    from scripts import build_strategy_replay_artifact as builder

    args = builder.build_parser().parse_args([
        "--as-of-date", "2026-01-05",
        "--artifact-kind", "selected-method-output",
    ])
    assert args.artifact_kind == "selected-method-output"
    assert args.universe_mode == "r3000_pit"


def test_selected_method_replay_artifact_no_temp_files_on_failure(tmp_path: Path) -> None:
    """On serialization failure, no .tmp files should remain.

    NOTE: full bundle atomicity (parquet + manifest as one unit) is a Strategy-owned
    concern. This test only asserts temp file cleanup.
    """
    bundle = _fake_selected_method_bundle(tmp_path)
    output_path = tmp_path / "fail_test.parquet"

    import unittest.mock
    with unittest.mock.patch.object(
        strat_replay.os, "replace", side_effect=OSError("disk full"),
    ):
        with pytest.raises(OSError):
            strat_replay.write_selected_method_replay_artifact_atomic(
                bundle, artifact_path=output_path,
            )

    tmp_files = list(tmp_path.glob(".*tmp*")) + list(tmp_path.glob(".*.tmp"))
    assert tmp_files == [], f"Temp files remain after failure: {tmp_files}"


def test_selected_method_replay_artifact_rolls_back_if_manifest_replace_fails(tmp_path: Path) -> None:
    """A manifest promotion failure must not leave an orphan parquet artifact."""
    bundle = _fake_selected_method_bundle(tmp_path)
    output_path = tmp_path / "bundle_atomic.parquet"
    manifest_path = output_path.with_suffix(output_path.suffix + ".manifest.json")
    real_replace = strat_replay.os.replace
    replaced_artifact = False

    def _fail_on_manifest_replace(src, dst):
        nonlocal replaced_artifact
        dst_path = Path(dst)
        if dst_path == output_path:
            replaced_artifact = True
        if replaced_artifact and dst_path == manifest_path:
            raise OSError("manifest write failed after parquet promotion")
        return real_replace(src, dst)

    import unittest.mock
    with unittest.mock.patch.object(strat_replay.os, "replace", side_effect=_fail_on_manifest_replace):
        with pytest.raises(OSError, match="manifest write failed"):
            strat_replay.write_selected_method_replay_artifact_atomic(
                bundle,
                artifact_path=output_path,
            )

    assert not output_path.exists()
    assert not manifest_path.exists()
    assert list(tmp_path.glob(".*.tmp")) == []


def _write_selected_artifact_for_reader(tmp_path: Path) -> tuple[Path, Path, strat_replay.StrategyReplayBundle]:
    bundle = _fake_selected_method_bundle(tmp_path)
    output_path = tmp_path / "reader.parquet"
    result = strat_replay.write_selected_method_replay_artifact_atomic(
        bundle,
        artifact_path=output_path,
    )
    return Path(result["artifact_path"]), Path(result["manifest_path"]), bundle


def _sync_manifest_run_metadata(manifest: dict) -> None:
    run_metadata = manifest.get("run_metadata")
    if not isinstance(run_metadata, dict):
        return
    for key in (
        "run_id",
        "source_id",
        "method_id",
        "input_signatures",
        "date_window",
        "row_counts",
        "status_counts",
        "timing",
        "controls_signature",
    ):
        if key in manifest:
            run_metadata[key] = manifest[key]


def _rewrite_manifest(path: Path, mutator, *, sync_run_metadata: bool = False) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mutator(manifest)
    if sync_run_metadata:
        _sync_manifest_run_metadata(manifest)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def test_read_selected_method_replay_artifact_accepts_valid_bundle(tmp_path: Path) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is True
    assert result.status == "ok"
    assert result.bundle is not None
    assert result.bundle.run_id == bundle.run_id
    assert list(result.bundle.replay.columns) == strat_replay.REPLAY_COLUMNS
    assert "context_role" in result.bundle.replay.columns
    assert "row_role" in result.bundle.replay.columns
    assert result.bundle.replay["context_role"].tolist() == ["current_holding", "cash"]
    assert result.bundle.replay["row_role"].unique().tolist() == ["daily_portfolio"]
    assert result.bundle.replay[["date", "ticker", "target_weight"]].to_dict("records") == bundle.replay[[
        "date",
        "ticker",
        "target_weight",
    ]].to_dict("records")


def test_read_selected_method_replay_artifact_hydrates_legacy_role_columns(tmp_path: Path) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    legacy = pd.read_parquet(artifact_path).drop(columns=["context_role", "row_role"])
    legacy.to_parquet(artifact_path, index=False)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is True
    assert result.bundle is not None
    assert result.bundle.replay["context_role"].tolist() == ["current_holding", "cash"]
    assert result.bundle.replay["row_role"].unique().tolist() == ["daily_portfolio"]


def test_read_selected_method_replay_artifact_rejects_legacy_plus_unrelated_missing_column(tmp_path: Path) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    malformed_legacy = pd.read_parquet(artifact_path).drop(columns=["context_role", "row_role", "artifact_scope"])
    malformed_legacy.to_parquet(artifact_path, index=False)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == "schema_mismatch"


@pytest.mark.parametrize(
    ("label", "mutator", "expected_reason"),
    [
        ("method", lambda m: m.__setitem__("method_id", OptimizationMethod.RULE_OF_100.value), "method_mismatch"),
        ("controls", lambda m: m.__setitem__("controls_signature", {"max_weight": 0.25}), "controls_signature_mismatch"),
        ("date", lambda m: m["date_window"].__setitem__("replay_end", "2026-01-04"), "date_window_mismatch:replay_end"),
        ("signature", lambda m: m.__setitem__("input_signatures", [{"type": "other"}]), "input_signature_mismatch"),
        ("schema", lambda m: m.__setitem__("artifact_type", "other"), "artifact_type_mismatch"),
        ("manifest", lambda m: m.pop("timing"), "manifest_field_missing:timing"),
    ],
)
def test_read_selected_method_replay_artifact_rejects_stale_manifest_context(
    tmp_path: Path,
    label: str,
    mutator,
    expected_reason: str,
) -> None:
    artifact_path, manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    _rewrite_manifest(manifest_path, mutator, sync_run_metadata=label != "manifest")
    expected_date_window = None
    if label == "date":
        expected_date_window = {
            "requested_start": "2026-01-02",
            "requested_end": "2026-01-03",
            "replay_start": "2026-01-02",
            "replay_end": "2026-01-03",
        }

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        expected_date_window=expected_date_window,
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False, label
    assert result.replay.empty
    assert result.reason == expected_reason


def test_read_selected_method_replay_artifact_rejects_source_file_signature_mismatch(tmp_path: Path) -> None:
    artifact_path, manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    source_signature = [str(tmp_path / "prices_tri.parquet"), 111, 222]

    def _add_source_signature(manifest: dict) -> None:
        signatures = list(manifest["input_signatures"])
        signatures[0] = {
            **signatures[0],
            "cache_signature": {"source_files": [source_signature]},
        }
        manifest["input_signatures"] = signatures
        manifest["run_metadata"]["input_signatures"] = signatures

    _rewrite_manifest(manifest_path, _add_source_signature)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        source_file_signatures=[[source_signature[0], 999, 222]],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == "source_file_signature_mismatch"


def test_read_selected_method_replay_artifact_rejects_rule100_candidate_content_drift(tmp_path: Path) -> None:
    prices = pd.DataFrame(
        {
            101: [100.0, 101.0],
            202: [50.0, 52.0],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-03"]),
    )
    original_candidates = pd.DataFrame(
        [
            {
                "date": "2026-01-03",
                "ticker": "AAA",
                "permno": 101,
                "factor_positive_count": 20,
                "technical_quality": 1.0,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
            {
                "date": "2026-01-03",
                "ticker": "BBB",
                "permno": 202,
                "factor_positive_count": 3,
                "technical_quality": 0.3,
                "sizing_eligible": True,
                "eligibility_reason": "eligible_buy_or_hold",
            },
        ]
    )
    changed_candidates = original_candidates.copy()
    changed_candidates.loc[0, "factor_positive_count"] = 3
    changed_candidates.loc[1, "factor_positive_count"] = 20
    changed_candidates.loc[0, "technical_quality"] = 0.2
    changed_candidates.loc[1, "technical_quality"] = 1.0

    bundle = strat_replay.build_selected_method_replay(
        method=OptimizationMethod.RULE_OF_100,
        controls={"max_weight": 0.35, "rule100_candidate_frame": original_candidates},
        prices=prices,
        ticker_map={101: "AAA", 202: "BBB"},
        as_of_range=["2026-01-03"],
    )
    assert bundle.run_metadata.controls_signature != strat_replay._controls_signature_payload(
        {"max_weight": 0.35, "rule100_candidate_frame": changed_candidates}
    )
    artifact_path = tmp_path / "rule100_reader.parquet"
    result = strat_replay.write_selected_method_replay_artifact_atomic(
        bundle,
        artifact_path=artifact_path,
    )
    written = pd.read_parquet(result["artifact_path"])
    assert set(written["permno"].astype(str)) == {"101", "202", "CASH"}

    read_result = strat_replay.read_selected_method_replay_artifact(
        result["artifact_path"],
        method=OptimizationMethod.RULE_OF_100,
        controls={"max_weight": 0.35, "rule100_candidate_frame": changed_candidates},
        as_of_range=["2026-01-03"],
        input_signatures=bundle.input_signatures,
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert read_result.available is False
    assert read_result.reason == "controls_signature_mismatch"


def test_read_selected_method_replay_artifact_rejects_parquet_manifest_row_mismatch(tmp_path: Path) -> None:
    artifact_path, manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    _rewrite_manifest(manifest_path, lambda m: m.__setitem__("row_count", m["row_count"] + 1))

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == "manifest_parquet_mismatch:row_count"


def test_read_selected_method_replay_artifact_rejects_parquet_schema_mismatch(tmp_path: Path) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    artifact = pd.read_parquet(artifact_path)
    artifact.drop(columns=["artifact_scope"]).to_parquet(artifact_path, index=False)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == "schema_mismatch"


@pytest.mark.parametrize(
    ("field_name", "parquet_column"),
    [
        ("run_id", "run_id"),
        ("source_id", "source_id"),
        ("method_id", "method"),
    ],
)
def test_read_selected_method_replay_artifact_rejects_blank_manifest_identity_without_expected_ids(
    tmp_path: Path,
    field_name: str,
    parquet_column: str,
) -> None:
    artifact_path, manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    artifact = pd.read_parquet(artifact_path)
    artifact[parquet_column] = ""
    artifact.to_parquet(artifact_path, index=False)

    def _blank_identity(manifest: dict) -> None:
        manifest[field_name] = "   "

    _rewrite_manifest(manifest_path, _blank_identity, sync_run_metadata=True)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
    )

    assert result.available is False
    assert result.replay.empty
    assert result.reason == f"manifest_identity_blank:{field_name}"


@pytest.mark.parametrize(
    ("column", "value", "expected_reason"),
    [
        ("run_id", pd.NA, "manifest_parquet_mismatch:run_id"),
        ("source_id", pd.NA, "manifest_parquet_mismatch:source_id"),
        ("artifact_scope", "", "manifest_parquet_mismatch:artifact_scope"),
        ("artifact_scope", "wrong_scope", "manifest_parquet_mismatch:artifact_scope"),
        ("method", "", "manifest_parquet_mismatch:method_id"),
        ("method", "wrong_method", "manifest_parquet_mismatch:method_id"),
    ],
)
def test_read_selected_method_replay_artifact_rejects_parquet_identity_drift(
    tmp_path: Path,
    column: str,
    value,
    expected_reason: str,
) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)
    artifact = pd.read_parquet(artifact_path)
    artifact.loc[0, column] = value
    artifact.to_parquet(artifact_path, index=False)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == expected_reason


@pytest.mark.parametrize("timing_payload", [{}, "bad", {"elapsed_ms": "bad"}, {"elapsed_ms": float("inf")}, {"elapsed_ms": -1.0}])
def test_read_selected_method_replay_artifact_rejects_malformed_timing(
    tmp_path: Path,
    timing_payload,
) -> None:
    artifact_path, manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)

    def _mutate_timing(manifest: dict) -> None:
        manifest["timing"] = timing_payload
        manifest["run_metadata"]["timing"] = timing_payload

    _rewrite_manifest(manifest_path, _mutate_timing)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
    )

    assert result.available is False
    assert result.reason == "manifest_timing_invalid"


@pytest.mark.parametrize(
    ("policy", "expected_reason"),
    [
        (strat_replay.ReplayBudgetPolicy(max_rows=1), "budget_exceeded:max_rows"),
        (strat_replay.ReplayBudgetPolicy(max_dates=1), "budget_exceeded:max_dates"),
        (strat_replay.ReplayBudgetPolicy(max_elapsed_ms=1.0), "budget_exceeded:max_elapsed_ms"),
        (strat_replay.ReplayBudgetPolicy(rerun_cache_max_seconds=-1.0), "budget_exceeded:rerun_cache_seconds"),
    ],
)
def test_read_selected_method_replay_artifact_rejects_over_budget_manifest(
    tmp_path: Path,
    policy: strat_replay.ReplayBudgetPolicy,
    expected_reason: str,
) -> None:
    artifact_path, _manifest_path, bundle = _write_selected_artifact_for_reader(tmp_path)

    result = strat_replay.read_selected_method_replay_artifact(
        artifact_path,
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={},
        start_date="2026-01-02",
        end_date="2026-01-03",
        input_signatures=bundle.input_signatures,
        source_file_signatures=[],
        run_id=bundle.run_id,
        source_id=bundle.run_metadata.source_id,
        budget_policy=policy,
    )

    assert result.available is False
    assert result.replay.empty
    assert result.reason == expected_reason


def test_build_selected_method_replay_with_budget_fails_closed_on_over_budget_rows(tmp_path: Path) -> None:
    prices = pd.DataFrame(
        {
            101: [100.0, 101.0],
            202: [50.0, 52.0],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-03"]),
    )

    result = strat_replay.build_selected_method_replay_with_budget(
        method=OptimizationMethod.INVERSE_VOLATILITY,
        controls={"max_weight": 0.60},
        prices=prices,
        ticker_map={101: "AAA", 202: "BBB"},
        start_date="2026-01-02",
        end_date="2026-01-03",
        budget_policy=strat_replay.ReplayBudgetPolicy(max_rows=1),
    )

    assert result.available is False
    assert result.replay.empty
    assert result.reason == "budget_exceeded:max_rows"
