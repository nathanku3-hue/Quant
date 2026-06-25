from __future__ import annotations

import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts import pead_d3_benchmark_artifact as artifact
from strategies.pead_event_study import PeadEventStudyConfig
from strategies.pead_event_study import build_event_windows
from strategies.pead_event_study import summarize_event_windows


def _source_zip(rows: list[tuple[str, float, float, float, float]]) -> bytes:
    payload = [
        "This file was created by using the 202604 CRSP database.",
        "Synthetic test header line.",
        "",
        ",Mkt-RF,SMB,HML,RF",
    ]
    payload.extend(
        f"{date},{mktrf:.2f},{smb:.2f},{hml:.2f},{rf:.2f}"
        for date, mktrf, smb, hml, rf in rows
    )
    payload.append("")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("F-F_Research_Data_Factors_daily.csv", "\n".join(payload))
    return buffer.getvalue()


def _d2b_bundle(tmp_path: Path, sessions: pd.DatetimeIndex) -> Path:
    frame = pd.DataFrame({"return_date": sessions})
    parquet_path = tmp_path / "d2b.parquet"
    frame.to_parquet(parquet_path, index=False)
    serialised = "\n".join(sessions.strftime("%Y-%m-%d")) + "\n"
    manifest = {
        "output": {
            "parquet_file": parquet_path.name,
            "sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
            "rows": len(frame),
            "schema": ["return_date"],
        },
        "session_spine": {
            "count": len(sessions),
            "date_min": sessions.min().strftime("%Y-%m-%d"),
            "date_max": sessions.max().strftime("%Y-%m-%d"),
            "sha256": hashlib.sha256(serialised.encode("utf-8")).hexdigest(),
        },
    }
    manifest_path = tmp_path / "d2b.parquet.manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_percent_returns_are_decimalized_and_total_benchmark_is_mktrf_plus_rf() -> None:
    source = artifact.parse_ken_french_daily_zip(
        _source_zip(
            [
                ("20240103", 1.23, 0.10, -0.20, 0.05),
                ("20240104", -0.40, 0.20, 0.30, 0.04),
            ]
        )
    )
    sessions = pd.to_datetime(["2024-01-03", "2024-01-04"])

    output = artifact.build_benchmark_frame(source, sessions)

    assert output["mktrf"].tolist() == pytest.approx([0.0123, -0.0040])
    assert output["rf"].tolist() == pytest.approx([0.0005, 0.0004])
    assert output["benchmark_return"].tolist() == pytest.approx([0.0128, -0.0036])
    assert not np.allclose(output["benchmark_return"], output["mktrf"])

    bad = output.copy()
    bad["benchmark_return"] = bad["mktrf"]
    with pytest.raises(ValueError, match=r"mktrf \+ rf"):
        artifact.validate_benchmark_frame(bad, sessions)


def test_missing_required_d2b_session_fails_without_fill() -> None:
    source = artifact.parse_ken_french_daily_zip(
        _source_zip([("20240103", 0.10, 0.0, 0.0, 0.01)])
    )
    sessions = pd.to_datetime(["2024-01-03", "2024-01-04"])

    with pytest.raises(ValueError, match="no fill or interpolation"):
        artifact.build_benchmark_frame(source, sessions)


def test_duplicate_source_dates_fail_closed() -> None:
    with pytest.raises(ValueError, match="duplicate return_date"):
        artifact.parse_ken_french_daily_zip(
            _source_zip(
                [
                    ("20240103", 0.10, 0.0, 0.0, 0.01),
                    ("20240103", 0.11, 0.0, 0.0, 0.01),
                ]
            )
        )


def test_d2b_manifest_sessions_are_hash_validated(tmp_path: Path) -> None:
    sessions = pd.bdate_range("2024-01-03", periods=3)
    manifest_path = _d2b_bundle(tmp_path, sessions)

    loaded = artifact.load_d2b_required_sessions(manifest_path)

    assert loaded.sessions.equals(sessions)
    assert loaded.provenance["session_spine"]["count"] == 3

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["output"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="hash drift"):
        artifact.load_d2b_required_sessions(manifest_path)


def test_d2b_authoritative_session_source_is_reconstructed_and_hash_validated(
    tmp_path: Path,
) -> None:
    source = artifact.parse_ken_french_daily_zip(
        _source_zip(
            [
                ("20240103", 0.10, 0.0, 0.0, 0.01),
                ("20240104", 0.20, 0.0, 0.0, 0.01),
                ("20240105", 0.30, 0.0, 0.0, 0.01),
            ]
        )
    )
    sessions = pd.DatetimeIndex(source.frame["return_date"])
    manifest_path = _d2b_bundle(tmp_path, sessions)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["session_spine"]["source"] = {
        "kind": "ken_french_daily_factor_dates",
        "source_name": artifact.SOURCE_NAME,
        "source_release": source.source_release,
        "source_download_sha256": source.source_download_sha256,
        "source_member_name": source.source_member_name,
        "source_url": artifact.SOURCE_URL,
        "methodology_url": artifact.METHODOLOGY_URL,
        "use": "authoritative_us_market_session_spine_only",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    loaded = artifact.load_d2b_required_sessions(manifest_path, source)

    assert loaded.sessions.equals(sessions)
    assert (
        loaded.provenance["session_source"]["source"]
        == "d2b_authoritative_ken_french_session_spine"
    )

    manifest["session_spine"]["source"]["source_download_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="source source_download_sha256 drift"):
        artifact.load_d2b_required_sessions(manifest_path, source)


def test_atomic_publication_manifest_integrity_and_cleanup(tmp_path: Path) -> None:
    sessions = pd.bdate_range("2024-01-03", periods=2)
    d2b_input = artifact.load_d2b_required_sessions(_d2b_bundle(tmp_path, sessions))
    source = artifact.parse_ken_french_daily_zip(
        _source_zip(
            [
                ("20240103", 0.10, 0.0, 0.0, 0.01),
                ("20240104", 0.20, 0.0, 0.0, 0.01),
            ]
        )
    )
    output = artifact.build_benchmark_frame(source, sessions)
    out_path = tmp_path / "benchmark.parquet"

    manifest_path = artifact.publish_benchmark_artifact(output, out_path, source, d2b_input)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    versioned_path = manifest_path.parent / manifest["parquet_file"]

    assert not out_path.exists()
    assert versioned_path.exists()
    assert manifest["sha256"] == hashlib.sha256(versioned_path.read_bytes()).hexdigest()
    assert manifest["row_count"] == 2
    assert manifest["required_d2b_sessions"] == 2
    assert manifest["matched_d2b_sessions"] == 2
    assert manifest["missing_d2b_sessions"] == []
    assert manifest["allowed_use"] == "benchmark_input_for_pead_d3_only"
    assert "mktrf-alone total market return" in manifest["forbidden_use"]
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_manifest_replace_interruption_preserves_old_pointer_and_cleans_new_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sessions = pd.bdate_range("2024-01-03", periods=2)
    d2b_input = artifact.load_d2b_required_sessions(_d2b_bundle(tmp_path, sessions))
    old_source = artifact.parse_ken_french_daily_zip(
        _source_zip(
            [
                ("20240103", 0.10, 0.0, 0.0, 0.01),
                ("20240104", 0.20, 0.0, 0.0, 0.01),
            ]
        )
    )
    new_source = artifact.parse_ken_french_daily_zip(
        _source_zip(
            [
                ("20240103", 0.30, 0.0, 0.0, 0.01),
                ("20240104", 0.40, 0.0, 0.0, 0.01),
            ]
        )
    )
    out_path = tmp_path / "benchmark.parquet"
    manifest_path = artifact.publish_benchmark_artifact(
        artifact.build_benchmark_frame(old_source, sessions), out_path, old_source, d2b_input
    )
    old_manifest_bytes = manifest_path.read_bytes()
    old_manifest = json.loads(old_manifest_bytes.decode("utf-8"))
    old_versioned = manifest_path.parent / old_manifest["parquet_file"]
    real_replace = os.replace

    def fail_manifest_replace(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == manifest_path:
            raise OSError("synthetic manifest interruption")
        real_replace(source, destination)

    monkeypatch.setattr(artifact.os, "replace", fail_manifest_replace)
    with pytest.raises(OSError, match="synthetic manifest interruption"):
        artifact.publish_benchmark_artifact(
            artifact.build_benchmark_frame(new_source, sessions),
            out_path,
            new_source,
            d2b_input,
        )

    assert manifest_path.read_bytes() == old_manifest_bytes
    assert old_versioned.exists()
    assert len(list(tmp_path.glob("benchmark.*.parquet"))) == 1
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.lock"))


def test_missing_benchmark_blocks_car_bhar_and_analysis_eligibility() -> None:
    config = PeadEventStudyConfig(
        start_day=1,
        end_day=2,
        benchmark_return_column="benchmark_return",
    )
    sessions = pd.to_datetime(["2024-01-03", "2024-01-04"])
    events = pd.DataFrame(
        {
            "event_id": ["E1"],
            "issuer_id": ["1001"],
            "security_id": ["1001-01"],
            "event_date": ["2024-01-02"],
            "sue": [1.0],
            "is_primary_security": [True],
        }
    )
    returns = pd.DataFrame(
        {
            "security_id": ["1001-01", "1001-01"],
            "date": sessions,
            "total_return": [0.10, -0.05],
            "benchmark_return": [0.02, np.nan],
        }
    )

    windows = build_event_windows(events, returns, sessions, config)
    outcome = summarize_event_windows(windows, config).iloc[0]

    assert outcome["coverage_reason"] == "missing_benchmark_return"
    assert not outcome["window_complete"]
    assert not outcome["eligible_for_analysis"]
    assert outcome["cumulative_total_return"] == pytest.approx((1.10 * 0.95) - 1.0)
    assert np.isnan(outcome["car"])
    assert np.isnan(outcome["bhar"])
