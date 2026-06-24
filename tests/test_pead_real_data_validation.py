from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import pytest

from scripts import pead_real_data_validation as validation


D1_COLUMNS = [
    "gvkey",
    "rdq",
    "datadate",
    "fyearq",
    "fqtr",
    "adj_eps",
    "adj_eps_t4",
    "surprise",
    "prccq_lag1",
    "cshoq_lag1",
    "liquidity_pass",
    "sue_price_scaled",
    "sue_std_scaled",
    "sue_price_scaled_clipped",
    "n_prior_quarters",
    "valid_sue",
]
D2B_COLUMNS = [
    "event_id",
    "issuer_id",
    "event_date",
    "sue",
    "sue_price_scaled_clipped",
    "security_id",
    "iid",
    "is_primary_security",
    "handoff_eligible",
    "selection_status",
    "selection_cutoff_date",
    "liquidity_observations",
    "trailing_mean_dollar_volume",
    "candidate_security_count",
    "event_day",
    "return_date",
    "return_row_present",
    "asset_return",
    "return_type",
    "guardrail_reason",
    "window_complete",
    "coverage_reason",
]
D3_COLUMNS = [
    "return_date",
    "mktrf",
    "rf",
    "benchmark_return",
    "source_name",
    "source_release",
    "source_url",
    "methodology_url",
]


@dataclass(frozen=True)
class Bundle:
    d1_manifest: Path
    d2b_manifest: Path
    d3_manifest: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _session_spine(sessions: pd.DatetimeIndex) -> dict[str, object]:
    serialised = "\n".join(sessions.strftime("%Y-%m-%d")) + "\n"
    return {
        "count": len(sessions),
        "date_min": sessions.min().strftime("%Y-%m-%d"),
        "date_max": sessions.max().strftime("%Y-%m-%d"),
        "sha256": hashlib.sha256(serialised.encode("utf-8")).hexdigest(),
        "hash_encoding": "UTF-8 YYYY-MM-DD lines with trailing newline",
    }


def _d1_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gvkey": "000001",
                "rdq": pd.Timestamp("2024-01-01"),
                "datadate": pd.Timestamp("2023-12-31"),
                "fyearq": 2023,
                "fqtr": 4,
                "adj_eps": 1.2,
                "adj_eps_t4": 1.0,
                "surprise": 0.2,
                "prccq_lag1": 20.0,
                "cshoq_lag1": 100.0,
                "liquidity_pass": True,
                "sue_price_scaled": 0.01,
                "sue_std_scaled": 1.0,
                "sue_price_scaled_clipped": 0.01,
                "n_prior_quarters": 8,
                "valid_sue": True,
            }
        ],
        columns=D1_COLUMNS,
    )


def _d2b_frame(sessions: pd.DatetimeIndex) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    cohorts = (
        (pd.Timestamp("2024-01-01"), sessions[:60]),
        (pd.Timestamp("2024-01-03"), sessions[2:62]),
    )
    for cohort_number, (event_date, return_dates) in enumerate(cohorts, start=1):
        for quantile_index, sue in enumerate((-2.0, -1.0, 0.0, 1.0, 2.0), start=1):
            issuer = f"{cohort_number}{quantile_index:05d}"
            security = f"{issuer}:01"
            event_id = f"PEAD:{issuer}:{event_date:%Y-%m-%d}"
            asset_return = 0.0005 + (sue * 0.0001)
            for event_day, return_date in enumerate(return_dates, start=1):
                rows.append(
                    {
                        "event_id": event_id,
                        "issuer_id": issuer,
                        "event_date": event_date,
                        "sue": sue,
                        "sue_price_scaled_clipped": sue,
                        "security_id": security,
                        "iid": "01",
                        "is_primary_security": True,
                        "handoff_eligible": True,
                        "selection_status": "selected",
                        "selection_cutoff_date": event_date,
                        "liquidity_observations": 20,
                        "trailing_mean_dollar_volume": 1_000_000.0,
                        "candidate_security_count": 1,
                        "event_day": event_day,
                        "return_date": return_date,
                        "return_row_present": True,
                        "asset_return": asset_return,
                        "return_type": "compustat_total_return_proxy",
                        "guardrail_reason": "none",
                        "window_complete": True,
                        "coverage_reason": "complete",
                    }
                )
    return pd.DataFrame(rows, columns=D2B_COLUMNS)


def _calendar_d2b_frame(sessions: pd.DatetimeIndex) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for rank in range(1, 51):
        issuer = f"C{rank:05d}"
        security = f"{issuer}:01"
        event_date = pd.Timestamp("2024-01-01")
        event_id = f"PEAD:{issuer}:{event_date:%Y-%m-%d}"
        for event_day, return_date in enumerate(sessions[:60], start=1):
            mktrf = -0.001 + ((event_day - 1) * (0.002 / 59))
            if rank <= 10:
                asset_return = 0.001 + (0.2 * mktrf)
            elif rank > 40:
                asset_return = 0.003 + (0.7 * mktrf)
            else:
                asset_return = 0.002 + (0.4 * mktrf)
            rows.append(
                {
                    "event_id": event_id,
                    "issuer_id": issuer,
                    "event_date": event_date,
                    "sue": float(rank),
                    "sue_price_scaled_clipped": float(rank),
                    "security_id": security,
                    "iid": "01",
                    "is_primary_security": True,
                    "handoff_eligible": True,
                    "selection_status": "selected",
                    "selection_cutoff_date": event_date,
                    "liquidity_observations": 20,
                    "trailing_mean_dollar_volume": 1_000_000.0,
                    "candidate_security_count": 1,
                    "event_day": event_day,
                    "return_date": return_date,
                    "return_row_present": True,
                    "asset_return": asset_return,
                    "return_type": "compustat_total_return_proxy",
                    "guardrail_reason": "none",
                    "window_complete": True,
                    "coverage_reason": "complete",
                }
            )
    return pd.DataFrame(rows, columns=D2B_COLUMNS)


def _d3_frame(sessions: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "return_date": sessions,
            "mktrf": np.full(len(sessions), 0.00008),
            "rf": np.full(len(sessions), 0.00002),
            "benchmark_return": np.full(len(sessions), 0.00010),
            "source_name": "ken_french_fama_french_3_factors_daily",
            "source_release": "fixture release",
            "source_url": "https://example.test/source",
            "methodology_url": "https://example.test/methodology",
        },
        columns=D3_COLUMNS,
    )


def _write_bundle(tmp_path: Path) -> Bundle:
    sessions = pd.bdate_range("2024-01-02", periods=62)

    d1_path = tmp_path / "d1.parquet"
    _d1_frame().to_parquet(d1_path, index=False)
    d1_manifest_path = tmp_path / "d1.parquet.manifest.json"
    d1_manifest = {
        "schema_version": "1.0",
        "parquet_file": d1_path.name,
        "row_count": 1,
        "columns": D1_COLUMNS,
        "sha256": _sha256(d1_path),
    }
    _write_json(d1_manifest_path, d1_manifest)

    d2b_frame = _d2b_frame(sessions)
    d2b_staging = tmp_path / "d2b.staging.parquet"
    d2b_frame.to_parquet(d2b_staging, index=False)
    d2b_sha = _sha256(d2b_staging)
    d2b_path = tmp_path / f"d2b.{d2b_sha}.parquet"
    d2b_staging.replace(d2b_path)
    spine = _session_spine(sessions)
    d2b_manifest_path = tmp_path / "d2b.parquet.manifest.json"
    d2b_manifest = {
        "schema_version": "1.0",
        "label": "sample_500_gvkeys_fixed_event_security_plus_60",
        "inputs": {
            "d1": {
                "manifest_path": d1_manifest_path.as_posix(),
                "manifest_sha256": _sha256(d1_manifest_path),
                "parquet_path": d1_path.as_posix(),
                "parquet_sha256": d1_manifest["sha256"],
                "rows": 1,
                "schema": D1_COLUMNS,
            }
        },
        "session_spine": spine,
        "counts": {
            "rows": len(d2b_frame),
            "events": 10,
            "issuers": 10,
            "selected_events": 10,
            "handoff_eligible_events": 10,
            "coverage_reason": {"complete": 10},
        },
        "output": {
            "parquet_file": d2b_path.name,
            "logical_parquet_name": "d2b.parquet",
            "sha256": d2b_sha,
            "rows": len(d2b_frame),
            "schema": D2B_COLUMNS,
        },
    }
    _write_json(d2b_manifest_path, d2b_manifest)

    d3_frame = _d3_frame(sessions)
    d3_staging = tmp_path / "d3.staging.parquet"
    d3_frame.to_parquet(d3_staging, index=False)
    d3_sha = _sha256(d3_staging)
    d3_path = tmp_path / f"d3.{d3_sha}.parquet"
    d3_staging.replace(d3_path)
    d3_manifest_path = tmp_path / "d3.parquet.manifest.json"
    d3_manifest = {
        "artifact_name": "pead_d3_ken_french_daily_benchmark",
        "schema_version": "1.0",
        "mode": "EXECUTION_PACKET",
        "parquet_file": d3_path.name,
        "sha256": d3_sha,
        "row_count": len(d3_frame),
        "columns": D3_COLUMNS,
        "formula": "benchmark_return = mktrf + rf after percent-to-decimal conversion",
        "required_d2b_sessions": len(sessions),
        "matched_d2b_sessions": len(sessions),
        "missing_d2b_sessions": [],
        "failure_reasons": [],
        "d2b_input": {
            "manifest_path": d2b_manifest_path.as_posix(),
            "manifest_sha256": _sha256(d2b_manifest_path),
            "parquet_path": d2b_path.as_posix(),
            "parquet_sha256": d2b_sha,
            "rows": len(d2b_frame),
            "session_spine": spine,
        },
        "allowed_use": "benchmark_input_for_pead_d3_only",
    }
    _write_json(d3_manifest_path, d3_manifest)
    return Bundle(d1_manifest_path, d2b_manifest_path, d3_manifest_path)


def _write_calendar_bundle(tmp_path: Path) -> Bundle:
    sessions = pd.bdate_range("2024-01-02", periods=60)

    d1_path = tmp_path / "d1.parquet"
    _d1_frame().to_parquet(d1_path, index=False)
    d1_manifest_path = tmp_path / "d1.parquet.manifest.json"
    d1_manifest = {
        "schema_version": "1.0",
        "parquet_file": d1_path.name,
        "row_count": 1,
        "columns": D1_COLUMNS,
        "sha256": _sha256(d1_path),
    }
    _write_json(d1_manifest_path, d1_manifest)

    d2b_frame = _calendar_d2b_frame(sessions)
    d2b_staging = tmp_path / "d2b.calendar.staging.parquet"
    d2b_frame.to_parquet(d2b_staging, index=False)
    d2b_sha = _sha256(d2b_staging)
    d2b_path = tmp_path / f"d2b.calendar.{d2b_sha}.parquet"
    d2b_staging.replace(d2b_path)
    spine = _session_spine(sessions)
    d2b_manifest_path = tmp_path / "d2b.calendar.parquet.manifest.json"
    d2b_manifest = {
        "schema_version": "1.0",
        "label": "calendar_time_fixture",
        "inputs": {
            "d1": {
                "manifest_path": d1_manifest_path.as_posix(),
                "manifest_sha256": _sha256(d1_manifest_path),
                "parquet_path": d1_path.as_posix(),
                "parquet_sha256": d1_manifest["sha256"],
                "rows": 1,
                "schema": D1_COLUMNS,
            }
        },
        "session_spine": spine,
        "counts": {
            "rows": len(d2b_frame),
            "events": 50,
            "issuers": 50,
            "selected_events": 50,
            "handoff_eligible_events": 50,
            "coverage_reason": {"complete": 50},
        },
        "output": {
            "parquet_file": d2b_path.name,
            "logical_parquet_name": "d2b.calendar.parquet",
            "sha256": d2b_sha,
            "rows": len(d2b_frame),
            "schema": D2B_COLUMNS,
        },
    }
    _write_json(d2b_manifest_path, d2b_manifest)

    d3_frame = _d3_frame(sessions)
    d3_frame["mktrf"] = np.linspace(-0.001, 0.001, len(d3_frame))
    d3_frame["benchmark_return"] = d3_frame["mktrf"] + d3_frame["rf"]
    d3_staging = tmp_path / "d3.calendar.staging.parquet"
    d3_frame.to_parquet(d3_staging, index=False)
    d3_sha = _sha256(d3_staging)
    d3_path = tmp_path / f"d3.calendar.{d3_sha}.parquet"
    d3_staging.replace(d3_path)
    d3_manifest_path = tmp_path / "d3.calendar.parquet.manifest.json"
    d3_manifest = {
        "artifact_name": "pead_d3_ken_french_daily_benchmark",
        "schema_version": "1.0",
        "mode": "EXECUTION_PACKET",
        "parquet_file": d3_path.name,
        "sha256": d3_sha,
        "row_count": len(d3_frame),
        "columns": D3_COLUMNS,
        "formula": "benchmark_return = mktrf + rf after percent-to-decimal conversion",
        "required_d2b_sessions": len(sessions),
        "matched_d2b_sessions": len(sessions),
        "missing_d2b_sessions": [],
        "failure_reasons": [],
        "d2b_input": {
            "manifest_path": d2b_manifest_path.as_posix(),
            "manifest_sha256": _sha256(d2b_manifest_path),
            "parquet_path": d2b_path.as_posix(),
            "parquet_sha256": d2b_sha,
            "rows": len(d2b_frame),
            "session_spine": spine,
        },
        "allowed_use": "benchmark_input_for_pead_d3_only",
    }
    _write_json(d3_manifest_path, d3_manifest)
    return Bundle(d1_manifest_path, d2b_manifest_path, d3_manifest_path)


def _build(bundle: Bundle) -> dict[str, object]:
    return validation.build_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
    )


def _rewrite_d3(
    bundle: Bundle,
    mutate: Callable[[pd.DataFrame], pd.DataFrame],
) -> None:
    manifest = json.loads(bundle.d3_manifest.read_text(encoding="utf-8"))
    old_path = bundle.d3_manifest.parent / manifest["parquet_file"]
    frame = pd.read_parquet(old_path)
    frame = mutate(frame)
    staging = bundle.d3_manifest.parent / "d3.rewrite.parquet"
    frame.to_parquet(staging, index=False)
    sha = _sha256(staging)
    final = bundle.d3_manifest.parent / f"d3.{sha}.parquet"
    staging.replace(final)
    manifest["parquet_file"] = final.name
    manifest["sha256"] = sha
    manifest["row_count"] = len(frame)
    _write_json(bundle.d3_manifest, manifest)


def _rewrite_d2b(
    bundle: Bundle,
    mutate: Callable[[pd.DataFrame], pd.DataFrame],
) -> None:
    manifest = json.loads(bundle.d2b_manifest.read_text(encoding="utf-8"))
    old_path = bundle.d2b_manifest.parent / manifest["output"]["parquet_file"]
    frame = mutate(pd.read_parquet(old_path)).reset_index(drop=True)
    staging = bundle.d2b_manifest.parent / "d2b.rewrite.parquet"
    frame.to_parquet(staging, index=False)
    sha = _sha256(staging)
    final = bundle.d2b_manifest.parent / f"d2b.rewrite.{sha}.parquet"
    staging.replace(final)
    manifest["output"]["parquet_file"] = final.name
    manifest["output"]["sha256"] = sha
    manifest["output"]["rows"] = len(frame)
    manifest["counts"]["rows"] = len(frame)
    manifest["counts"]["events"] = int(frame["event_id"].nunique())
    manifest["counts"]["issuers"] = int(frame["issuer_id"].nunique())
    manifest["counts"]["selected_events"] = int(frame["event_id"].nunique())
    manifest["counts"]["handoff_eligible_events"] = int(
        frame.loc[frame["handoff_eligible"], "event_id"].nunique()
    )
    manifest["counts"]["coverage_reason"] = {
        str(key): int(value)
        for key, value in frame.groupby("event_id", observed=True)["coverage_reason"]
        .first()
        .value_counts()
        .sort_index()
        .items()
    }
    _write_json(bundle.d2b_manifest, manifest)

    d3_manifest = json.loads(bundle.d3_manifest.read_text(encoding="utf-8"))
    d3_manifest["d2b_input"]["manifest_sha256"] = _sha256(bundle.d2b_manifest)
    d3_manifest["d2b_input"]["parquet_path"] = final.as_posix()
    d3_manifest["d2b_input"]["parquet_sha256"] = sha
    d3_manifest["d2b_input"]["rows"] = len(frame)
    _write_json(bundle.d3_manifest, d3_manifest)


def test_deterministic_schema_complete_json_and_cli_write(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path)
    first = _build(bundle)
    second = _build(bundle)

    assert validation._json_bytes(first) == validation._json_bytes(second)
    assert set(first) == {
        "artifact_name",
        "benchmark_contract",
        "counts",
        "evidence_policy",
        "limitations",
        "lineage",
        "mode",
        "outputs",
        "round_id",
        "schema_version",
        "strategy_path",
    }
    assert set(first["lineage"]) == {"d1", "d2b", "d3"}
    assert first["limitations"] == list(validation.LIMITATIONS)
    assert first["evidence_policy"]["interpretation_performed"] is False
    assert first["counts"]["events"] == 10
    assert first["counts"]["issuers"] == 10
    assert first["counts"]["eligible_events"] == 10

    output = tmp_path / "evidence.json"
    assert validation.main(
        [
            "--d1-manifest",
            str(bundle.d1_manifest),
            "--d2b-manifest",
            str(bundle.d2b_manifest),
            "--d3-manifest",
            str(bundle.d3_manifest),
            "--output",
            str(output),
        ]
    ) == 0
    assert output.read_bytes() == validation._json_bytes(first)
    json.loads(output.read_text(encoding="utf-8"), parse_constant=lambda value: pytest.fail(value))


def test_atomic_write_preserves_existing_file_and_cleans_temp_on_replace_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "evidence.json"
    output.write_bytes(b"existing\n")

    def fail_replace(source: Path, destination: Path) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(validation.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        validation.write_evidence_atomic({"value": 1}, output)

    assert output.read_bytes() == b"existing\n"
    assert list(tmp_path.glob(".evidence.json.*.tmp")) == []


def test_lineage_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path)
    d1_manifest = json.loads(bundle.d1_manifest.read_text(encoding="utf-8"))
    d1_path = bundle.d1_manifest.parent / d1_manifest["parquet_file"]
    with d1_path.open("ab") as handle:
        handle.write(b"tamper")

    with pytest.raises(ValueError, match="D1 Parquet hash drift"):
        _build(bundle)


@pytest.mark.parametrize("failure", ["corrupt_manifest", "missing_parquet"])
def test_corrupt_or_partial_bundle_fails_closed(tmp_path: Path, failure: str) -> None:
    bundle = _write_bundle(tmp_path)
    if failure == "corrupt_manifest":
        bundle.d3_manifest.write_text("{not-json", encoding="utf-8")
        match = "not valid UTF-8 JSON"
    else:
        manifest = json.loads(bundle.d3_manifest.read_text(encoding="utf-8"))
        (bundle.d3_manifest.parent / manifest["parquet_file"]).unlink()
        match = "D3 Parquet is missing"

    with pytest.raises((ValueError, FileNotFoundError), match=match):
        _build(bundle)


def test_manifest_cardinality_drift_fails_closed(tmp_path: Path) -> None:
    bundle = _write_bundle(tmp_path)
    d2b_manifest = json.loads(bundle.d2b_manifest.read_text(encoding="utf-8"))
    d2b_manifest["counts"]["events"] = 11
    _write_json(bundle.d2b_manifest, d2b_manifest)
    d3_manifest = json.loads(bundle.d3_manifest.read_text(encoding="utf-8"))
    d3_manifest["d2b_input"]["manifest_sha256"] = _sha256(bundle.d2b_manifest)
    _write_json(bundle.d3_manifest, d3_manifest)

    with pytest.raises(ValueError, match="D2B counts.events drift"):
        _build(bundle)


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda frame: pd.concat([frame, frame.iloc[[0]]], ignore_index=True), "unique, and sorted"),
        (lambda frame: frame.iloc[1:].reset_index(drop=True), "session_spine.count drift"),
    ],
)
def test_d3_cardinality_or_coverage_failure_is_rejected(
    tmp_path: Path,
    mutation: Callable[[pd.DataFrame], pd.DataFrame],
    match: str,
) -> None:
    bundle = _write_bundle(tmp_path)
    _rewrite_d3(bundle, mutation)

    with pytest.raises(ValueError, match=match):
        _build(bundle)


def test_event_date_hac_gaps_fail_closed_without_changing_locked_settings(
    tmp_path: Path,
) -> None:
    evidence = _build(_write_bundle(tmp_path))
    event_output = evidence["outputs"]["event_date"]

    assert event_output["ex_post_descriptive_only"] is False
    assert event_output["strategy_config"]["cohort_frequency"] == "D"
    assert event_output["strategy_config"]["hac_maxlags"] == 4
    assert event_output["strategy_config"]["quantiles"] == 5
    for metric in ("car", "bhar"):
        hac = event_output["metrics"][metric]["hac"]
        assert hac["observed_cohort_gap_count"] == 1
        assert hac["observed_cohort_gaps"] == ["2024-01-02"]
        assert hac["standard_error"] is None
        assert hac["t_stat"] is None


def test_quarterly_output_is_explicitly_ex_post_descriptive_only(tmp_path: Path) -> None:
    evidence = _build(_write_bundle(tmp_path))
    quarterly = evidence["outputs"]["quarterly"]

    assert quarterly["ex_post_descriptive_only"] is True
    assert quarterly["strategy_config"]["cohort_frequency"] == "Q"
    assert quarterly["strategy_config"]["allow_ex_post_cohorts"] is True
    assert quarterly["strategy_config"]["hac_maxlags"] == 4
    assert set(quarterly["metrics"]) == {"car", "bhar"}


def test_calendar_time_m1b_evidence_schema_and_atomic_write(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    evidence = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
    )

    assert set(evidence) == {
        "schema_version",
        "round_id",
        "scope_id",
        "method_id",
        "lineage",
        "formation",
        "session_coverage",
        "daily_summary",
        "primary_inference",
        "missingness_sensitivity",
        "robustness",
        "limitations",
        "evidence_policy",
    }
    assert evidence["round_id"] == validation.M1B_ROUND_ID
    assert evidence["method_id"] == validation.M1B_METHOD_ID
    assert evidence["formation"]["minimum_finite_per_leg"] == 10
    assert evidence["session_coverage"]["retained_sessions"] == 60
    assert evidence["primary_inference"]["status"] == "valid"
    assert evidence["primary_inference"]["hac_maxlags_used"] == 59
    assert evidence["primary_inference"]["alpha_ct"] == pytest.approx(0.002)
    assert evidence["primary_inference"]["beta_m"] == pytest.approx(0.5)
    assert evidence["robustness"]["status"] == "valid"
    assert evidence["lineage"]["protected_validation_json"]["sha256"] == (
        validation.PROTECTED_VALIDATION_JSON_SHA256
    )
    assert evidence["evidence_policy"]["interpretation_performed"] is False
    assert evidence["evidence_policy"]["strategy_promotion_authorized"] is False
    assert evidence["evidence_policy"]["forbidden_use"] == sorted(
        set(evidence["evidence_policy"]["forbidden_use"])
    )

    output = tmp_path / "calendar_time_m1b.json"
    validation.write_evidence_atomic(evidence, output)
    assert output.read_bytes() == validation._json_bytes(evidence)


def test_calendar_time_m1b_schema_rejects_unknown_nested_fields(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    evidence = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
    )
    bad = copy.deepcopy(evidence)
    bad["lineage"]["d1"]["unexpected"] = True

    with pytest.raises(ValueError, match="lineage.d1 keys drift"):
        validation.validate_calendar_time_evidence_schema(bad)


def test_calendar_time_m1b_schema_requires_hac_small_sample_correction(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    evidence = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
    )
    bad = copy.deepcopy(evidence)
    bad["primary_inference"]["use_correction"] = False

    with pytest.raises(ValueError, match="primary_inference.use_correction drift"):
        validation.validate_calendar_time_evidence_schema(bad)


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda evidence: evidence["session_coverage"]["q1"].__setitem__("expected", -1),
            "session_coverage.q1.expected must be non-negative",
        ),
        (
            lambda evidence: evidence["daily_summary"]["q1"].__setitem__("missing_rate", 7.0),
            "daily_summary.q1.missing_rate must be between 0 and 1",
        ),
        (
            lambda evidence: evidence["daily_summary"]["q5"].__setitem__("total_missing", 1),
            r"daily_summary.q5 total_expected must equal total_finite \+ total_missing",
        ),
    ],
)
def test_calendar_time_m1b_schema_rejects_count_invariant_drift(
    tmp_path: Path,
    mutate: Callable[[dict[str, object]], None],
    match: str,
) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    evidence = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
    )
    bad = copy.deepcopy(evidence)
    mutate(bad)

    with pytest.raises(ValueError, match=match):
        validation.validate_calendar_time_evidence_schema(bad)


def test_calendar_time_m1b_rejects_d2b_return_dates_outside_d3_spine(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)

    def add_off_spine_date(frame: pd.DataFrame) -> pd.DataFrame:
        frame = frame.copy()
        frame.loc[0, "return_date"] = pd.Timestamp("2030-01-02")
        return frame

    _rewrite_d2b(bundle, add_off_spine_date)

    with pytest.raises(ValueError, match="outside the authoritative D3 session spine"):
        validation.build_calendar_time_evidence(
            d1_manifest_path=bundle.d1_manifest,
            d2b_manifest_path=bundle.d2b_manifest,
            d3_manifest_path=bundle.d3_manifest,
            enforce_current_counts=False,
        )


def test_calendar_time_m1b_zero_retained_sessions_is_schema_valid(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    _rewrite_d2b(
        bundle,
        lambda frame: frame.loc[frame["issuer_id"].isin([f"C{rank:05d}" for rank in range(1, 6)])],
    )

    evidence = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
    )

    assert evidence["session_coverage"]["retained_sessions"] == 0
    assert evidence["session_coverage"]["retained_date_min"] is None
    assert evidence["session_coverage"]["retained_date_max"] is None
    assert evidence["primary_inference"]["status"] == "null"
    validation.validate_calendar_time_evidence_schema(evidence)


def test_calendar_time_m1b_cli_rejects_noncanonical_output_before_build(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def unexpected_build(**_: object) -> dict[str, object]:
        nonlocal called
        called = True
        return {}

    monkeypatch.setattr(validation, "build_calendar_time_evidence", unexpected_build)

    with pytest.raises(ValueError, match="M1B output path is fixed"):
        validation.main(
            [
                "--calendar-time-m1b",
                "--output",
                str(tmp_path / "not-the-canonical-artifact.json"),
            ]
        )

    assert called is False


def test_calendar_time_m1b_current_count_contract_is_enforced(tmp_path: Path) -> None:
    bundle = _write_calendar_bundle(tmp_path)

    with pytest.raises(ValueError, match="M1B session_coverage.null_return_date_rows_excluded"):
        validation.build_calendar_time_evidence(
            d1_manifest_path=bundle.d1_manifest,
            d2b_manifest_path=bundle.d2b_manifest,
            d3_manifest_path=bundle.d3_manifest,
        )


def test_v2_artifacts_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bundle = _write_calendar_bundle(tmp_path)
    
    # 1. Test build_evidence in v2 mode
    validation_ev = validation.build_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        v2=True,
    )
    assert validation_ev["round_id"] == "V2-PEAD-REAL-DATA-VALIDATION-FULL-UNIVERSE-V2"
    assert "dashboard read-only status exposure" in validation_ev["evidence_policy"]["allowed_use"]
    assert "dashboard implementation" not in validation_ev["evidence_policy"]["forbidden_use"]
    assert "full universe (9,969 issuers)" in validation_ev["limitations"]
    
    # Write the validation JSON so we can reference it in lineage check
    validation_json = tmp_path / "pead_real_data_validation_full_universe_v2.json"
    validation.write_evidence_atomic(validation_ev, validation_json)
    
    # 2. Test build_calendar_time_evidence in v2 mode
    m1b_ev = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
        v2=True,
        validation_json_path=validation_json,
    )
    assert m1b_ev["round_id"] == "ROUND-20260622-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B-FULL-UNIVERSE-V2"
    assert m1b_ev["limitations"]["sample_universe"] == "full_universe"
    
    protected = m1b_ev["lineage"]["protected_validation_json"]
    assert protected["path"] == validation._display_path(validation_json)
    assert protected["sha256"] == validation._sha256_file(validation_json)
    
    # 3. Test CLI main function in v2 mode
    monkeypatch.setattr(
        validation,
        "_require_fixed_m1b_output_path",
        lambda p: p,
    )
    output_m1b = tmp_path / "pead_calendar_time_inference_m1b_full_universe_v2.json"
    assert validation.main([
        "--calendar-time-m1b",
        "--v2",
        "--d1-manifest", str(bundle.d1_manifest),
        "--d2b-manifest", str(bundle.d2b_manifest),
        "--d3-manifest", str(bundle.d3_manifest),
        "--no-enforce-counts",
        "--validation-json", str(validation_json),
        "--output", str(output_m1b)
    ]) == 0
    
    loaded_m1b = json.loads(output_m1b.read_text(encoding="utf-8"))
    assert loaded_m1b["round_id"] == "ROUND-20260622-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B-FULL-UNIVERSE-V2"

    linked_m1b = validation.build_calendar_time_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        enforce_current_counts=False,
        v2=True,
        validation_json_path=validation_json,
        linked_json_path=validation_json,
    )
    assert linked_m1b["schema_version"] == "2.0"
    assert linked_m1b["publishable"] is True
    assert linked_m1b["artifact" + "_name"] == "pead_calendar_time_inference_m1b"
    assert linked_m1b["par" + "ent" + "_sha256"] == validation._sha256_file(validation_json)

    linked_output = tmp_path / "pead_calendar_time_inference_m1b_full_universe_v2.linked.json"
    validation.write_evidence_atomic(linked_m1b, linked_output)
    profile = validation.verify_evidence_pair(validation_json, linked_output)
    assert profile.schema_version == "2.0"
    assert profile.publishable is True
    assert profile.output_sha256 == validation._sha256_file(linked_output)


# ---------------------------------------------------------------------------
# M4B.1 Evidence Contract: EvidenceProfile / verify_evidence_pair / CLI guard
# ---------------------------------------------------------------------------


def test_evidence_profile_is_frozen() -> None:
    """EvidenceProfile must be immutable (frozen=True)."""
    profile = validation.EvidenceProfile(
        schema_version="2.0",
        artifact_name="pead_real_data_validation",
        round_id="TEST-ROUND",
        parent_sha256="a" * 64,
        publishable=True,
        output_sha256="b" * 64,
    )
    with pytest.raises(FrozenInstanceError):
        profile.publishable = False  # type: ignore[misc]


def test_verify_evidence_pair_happy_path(tmp_path: Path) -> None:
    """verify_evidence_pair returns a correct EvidenceProfile when pair is valid."""
    parent = tmp_path / "parent.json"
    parent_content = b'{"schema_version": "1.0"}\n'
    parent.write_bytes(parent_content)
    parent_sha256 = hashlib.sha256(parent_content).hexdigest()

    child_data = {
        "artifact_name": "pead_real_data_validation",
        "parent_sha256": parent_sha256,
        "publishable": True,
        "round_id": "TEST-ROUND",
        "schema_version": "2.0",
    }
    child = tmp_path / "child.json"
    child_bytes = (json.dumps(child_data, indent=2, sort_keys=True) + "\n").encode("utf-8")
    child.write_bytes(child_bytes)
    expected_output_sha256 = hashlib.sha256(child_bytes).hexdigest()

    profile = validation.verify_evidence_pair(parent, child)

    assert profile.schema_version == "2.0"
    assert profile.artifact_name == "pead_real_data_validation"
    assert profile.round_id == "TEST-ROUND"
    assert profile.parent_sha256 == parent_sha256
    assert profile.publishable is True
    assert profile.output_sha256 == expected_output_sha256


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (
            lambda d, _: d.__setitem__("parent_sha256", "a" * 64),
            "parent_sha256 mismatch",
        ),
        (
            lambda d, _: d.pop("parent_sha256"),
            "missing parent_sha256",
        ),
        (
            lambda d, _: d.__setitem__("schema_version", "1.0"),
            "schema_version must be 2.0",
        ),
        (
            lambda d, _: d.__setitem__("publishable", False),
            "publishable must be true",
        ),
    ],
)
def test_verify_evidence_pair_fails_closed(
    tmp_path: Path,
    mutation: Callable[[dict[str, object], str], None],
    match: str,
) -> None:
    """verify_evidence_pair raises ValueError on any contract violation."""
    parent = tmp_path / "parent.json"
    parent_content = b'{"schema_version": "1.0"}\n'
    parent.write_bytes(parent_content)
    parent_sha256 = hashlib.sha256(parent_content).hexdigest()

    child_data: dict[str, object] = {
        "artifact_name": "pead_real_data_validation",
        "parent_sha256": parent_sha256,
        "publishable": True,
        "round_id": "TEST-ROUND",
        "schema_version": "2.0",
    }
    mutation(child_data, parent_sha256)

    child = tmp_path / "child.json"
    child.write_text(
        json.dumps(child_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=match):
        validation.verify_evidence_pair(parent, child)


def test_build_evidence_with_parent_linkage_embeds_correct_fields(tmp_path: Path) -> None:
    """build_evidence with parent_evidence_path sets schema_version=2.0, publishable, parent_sha256."""
    bundle = _write_bundle(tmp_path)
    parent = tmp_path / "parent.json"
    parent_content = b'{"schema_version": "1.0"}\n'
    parent.write_bytes(parent_content)
    expected_parent_sha256 = hashlib.sha256(parent_content).hexdigest()

    evidence = validation.build_evidence(
        d1_manifest_path=bundle.d1_manifest,
        d2b_manifest_path=bundle.d2b_manifest,
        d3_manifest_path=bundle.d3_manifest,
        parent_evidence_path=parent,
    )

    assert evidence["schema_version"] == "2.0"
    assert evidence["publishable"] is True
    assert evidence["parent_sha256"] == expected_parent_sha256


def test_publish_evidence_pair_cli_guard_fails_closed_without_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--publish-evidence-pair raises before any write when built evidence violates the contract."""
    parent = tmp_path / "parent.json"
    parent.write_bytes(b'{"schema_version": "1.0"}\n')
    output = tmp_path / "child.json"

    def fake_build(**_: object) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "publishable": False,
            "parent_sha256": "a" * 64,
        }

    monkeypatch.setattr(validation, "build_evidence", fake_build)

    with pytest.raises(ValueError, match="guard"):
        validation.main([
            "--publish-evidence-pair",
            "--parent-evidence", str(parent),
            "--output", str(output),
        ])

    assert not output.exists()


def test_publish_evidence_pair_cli_end_to_end(tmp_path: Path) -> None:
    """--publish-evidence-pair builds, verifies, and writes a schema_version=2.0 evidence file."""
    bundle = _write_bundle(tmp_path)
    parent = tmp_path / "parent.json"
    parent_content = b'{"schema_version": "1.0"}\n'
    parent.write_bytes(parent_content)
    expected_parent_sha256 = hashlib.sha256(parent_content).hexdigest()
    output = tmp_path / "child.json"

    rc = validation.main([
        "--publish-evidence-pair",
        "--parent-evidence", str(parent),
        "--d1-manifest", str(bundle.d1_manifest),
        "--d2b-manifest", str(bundle.d2b_manifest),
        "--d3-manifest", str(bundle.d3_manifest),
        "--output", str(output),
    ])

    assert rc == 0
    assert output.exists()
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "2.0"
    assert loaded["publishable"] is True
    assert loaded["parent_sha256"] == expected_parent_sha256
    # Post-write pair verification must also pass
    profile = validation.verify_evidence_pair(parent, output)
    assert profile.publishable is True
    assert profile.parent_sha256 == expected_parent_sha256
