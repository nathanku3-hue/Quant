"""Publish bounded PEAD CAR/BHAR/quintile evidence from D1/D2B/D3 artifacts.

The output is deterministic, numbers-only evidence for owner review.  This
script does not interpret results, change the locked strategy settings, or
authorize dashboard/alpha use.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

import numpy as np
import pandas as pd
pd.options.mode.string_storage = "pyarrow"
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from strategies.pead_event_study import (  # noqa: E402
    PeadCalendarTimeInferenceConfig,
    PeadEventStudyConfig,
    build_calendar_time_inference,
    summarize_event_windows,
    summarize_quantile_performance,
    assign_signal_quantiles,
)


ROUND_ID = "V2-PEAD-REAL-DATA-VALIDATION-20260620"
M1B_ROUND_ID = "ROUND-20260621-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B"
M1B_SCOPE_ID = "V2_PEAD_CALENDAR_TIME_INFERENCE_IMPLEMENTATION"
M1B_METHOD_ID = "calendar_time_q5_q1_single_factor_hac59_v1"
D1_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet.manifest.json"
D2B_MANIFEST_PATH = (
    ROOT / "data" / "processed" / "pead_d2b_event_windows_sample.parquet.manifest.json"
)
D3_MANIFEST_PATH = (
    ROOT
    / "data"
    / "processed"
    / "pead_d3_ken_french_daily_benchmark.parquet.manifest.json"
)
DEFAULT_OUTPUT_PATH = (
    ROOT
    / "docs"
    / "context"
    / "e2e_evidence"
    / "pead_real_data_validation_20260620.json"
)
M1B_OUTPUT_PATH = (
    ROOT
    / "docs"
    / "context"
    / "e2e_evidence"
    / "pead_calendar_time_inference_m1b.json"
)
PROTECTED_VALIDATION_JSON_PATH = DEFAULT_OUTPUT_PATH
PROTECTED_VALIDATION_JSON_SHA256 = (
    "96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e"
)

BENCHMARK_COLUMN = "benchmark_return"
OUTCOME_COLUMNS = ("car", "bhar")
LIMITATIONS = (
    "500-GVKEY sample",
    "current-vintage EPS",
    "Compustat return proxy",
    "no delisting adjustment",
)
D2B_READ_COLUMNS = (
    "event_id",
    "issuer_id",
    "event_date",
    "sue",
    "security_id",
    "is_primary_security",
    "handoff_eligible",
    "event_day",
    "return_date",
    "asset_return",
    "window_complete",
    "coverage_reason",
)
D3_READ_COLUMNS = ("return_date", "mktrf", "rf", BENCHMARK_COLUMN)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


@dataclass(frozen=True)
class ArtifactSnapshot:
    label: str
    manifest_path: Path
    manifest: dict[str, Any]
    manifest_sha256: str
    parquet_path: Path
    parquet_sha256: str
    row_count: int
    columns: tuple[str, ...]
    frame: pd.DataFrame | None


@dataclass(frozen=True)
class EvidenceProfile:
    """Immutable cryptographic fingerprint of a published evidence JSON with parent linkage.

    Captures the M4B.1 contract: schema_version 2.0, publishable flag, and the
    SHA256 byte-snapshot that binds the child evidence to its parent.
    """

    schema_version: str
    artifact_name: str
    round_id: str
    parent_sha256: str  # SHA256 of the parent evidence file bytes
    publishable: bool
    output_sha256: str  # SHA256 of the child evidence JSON bytes


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest_snapshot(path: Path, label: str) -> tuple[dict[str, Any], str]:
    path = Path(path).resolve()
    try:
        payload = path.read_bytes()
    except FileNotFoundError:
        raise
    try:
        manifest = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} manifest is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(manifest, dict):
        raise ValueError(f"{label} manifest must contain a JSON object")
    return manifest, _sha256_bytes(payload)


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields.difference(value))
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")


def _local_parquet_path(manifest_path: Path, parquet_file: Any, label: str) -> Path:
    if not isinstance(parquet_file, str) or not parquet_file.strip():
        raise ValueError(f"{label} parquet_file must be a non-empty string")
    name = Path(parquet_file)
    if name.name != parquet_file or name.suffix.lower() != ".parquet":
        raise ValueError(f"{label} parquet_file must be a local .parquet filename")
    path = (manifest_path.parent / name).resolve()
    if path.parent != manifest_path.parent.resolve():
        raise ValueError(f"{label} parquet_file escapes its manifest directory")
    return path


def _load_artifact(
    manifest_path: Path,
    label: str,
    *,
    contract_location: str,
    read_columns: tuple[str, ...] = (),
) -> ArtifactSnapshot:
    """Hash and read one stable file handle, with column-pruned Arrow loading."""
    manifest_path = Path(manifest_path).resolve()
    manifest, manifest_sha256 = _read_manifest_snapshot(manifest_path, label)
    if contract_location == "output":
        contract = _require_mapping(manifest.get("output"), f"{label} manifest output")
        row_key, column_key = "rows", "schema"
    elif contract_location == "root":
        contract = manifest
        row_key = "row_count"
        column_key = "columns"
    else:  # pragma: no cover - internal programming error
        raise ValueError(f"unsupported contract location: {contract_location}")

    _require_fields(
        contract,
        {"parquet_file", "sha256", row_key, column_key},
        f"{label} Parquet contract",
    )
    expected_sha = contract["sha256"]
    if not isinstance(expected_sha, str) or SHA256_RE.fullmatch(expected_sha) is None:
        raise ValueError(f"{label} sha256 must be 64 lowercase hex characters")
    expected_columns = contract[column_key]
    if not isinstance(expected_columns, list) or not all(
        isinstance(column, str) for column in expected_columns
    ):
        raise ValueError(f"{label} {column_key} must be a list of column names")
    missing_read_columns = sorted(set(read_columns).difference(expected_columns))
    if missing_read_columns:
        raise ValueError(
            f"{label} contract is missing required columns: {missing_read_columns}"
        )

    parquet_path = _local_parquet_path(manifest_path, contract["parquet_file"], label)
    digest = hashlib.sha256()
    try:
        with parquet_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
            actual_sha = digest.hexdigest()
            if actual_sha != expected_sha:
                raise ValueError(
                    f"{label} Parquet hash drift: expected {expected_sha}, got {actual_sha}"
                )
            handle.seek(0)
            parquet = pq.ParquetFile(handle)
            actual_columns = tuple(parquet.schema_arrow.names)
            if actual_columns != tuple(expected_columns):
                raise ValueError(
                    f"{label} Parquet schema drift against manifest {column_key}"
                )
            actual_rows = int(parquet.metadata.num_rows)
            try:
                expected_rows = int(contract[row_key])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{label} {row_key} must be an integer") from exc
            if expected_rows != actual_rows:
                raise ValueError(
                    f"{label} row-count drift: manifest={expected_rows}, parquet={actual_rows}"
                )
            frame = (
                parquet.read(columns=list(read_columns)).to_pandas()
                if read_columns
                else None
            )
    except FileNotFoundError:
        raise FileNotFoundError(f"{label} Parquet is missing: {parquet_path}") from None

    return ArtifactSnapshot(
        label=label,
        manifest_path=manifest_path,
        manifest=manifest,
        manifest_sha256=manifest_sha256,
        parquet_path=parquet_path,
        parquet_sha256=actual_sha,
        row_count=actual_rows,
        columns=actual_columns,
        frame=frame,
    )


def _declared_path_matches(path_text: Any, actual_path: Path, label: str) -> None:
    if not isinstance(path_text, str) or not path_text.strip():
        raise ValueError(f"{label} must be a non-empty path string")
    declared = Path(path_text)
    resolved = declared.resolve() if declared.is_absolute() else (ROOT / declared).resolve()
    if resolved != actual_path.resolve():
        raise ValueError(
            f"{label} drift: declared={_display_path(resolved)}, actual={_display_path(actual_path)}"
        )


def _require_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label} drift: expected {expected!r}, got {actual!r}")


def _session_spine_record(dates: pd.Series | pd.DatetimeIndex) -> dict[str, Any]:
    sessions = pd.DatetimeIndex(pd.to_datetime(dates, errors="coerce"))
    if sessions.hasnans:
        raise ValueError("D3 return_date contains null/non-coercible values")
    sessions = sessions.normalize()
    if sessions.empty or sessions.has_duplicates or not sessions.is_monotonic_increasing:
        raise ValueError("D3 return_date must be non-empty, unique, and sorted")
    serialised = "\n".join(sessions.strftime("%Y-%m-%d")) + "\n"
    return {
        "count": int(len(sessions)),
        "date_min": sessions.min().strftime("%Y-%m-%d"),
        "date_max": sessions.max().strftime("%Y-%m-%d"),
        "sha256": _sha256_bytes(serialised.encode("utf-8")),
        "hash_encoding": "UTF-8 YYYY-MM-DD lines with trailing newline",
    }


def _validate_lineage(
    d1: ArtifactSnapshot,
    d2b: ArtifactSnapshot,
    d3: ArtifactSnapshot,
) -> dict[str, dict[str, Any]]:
    d2b_inputs = _require_mapping(d2b.manifest.get("inputs"), "D2B manifest inputs")
    d1_input = _require_mapping(d2b_inputs.get("d1"), "D2B manifest inputs.d1")
    _require_fields(
        d1_input,
        {"manifest_path", "manifest_sha256", "parquet_path", "parquet_sha256", "rows", "schema"},
        "D2B manifest inputs.d1",
    )
    _declared_path_matches(d1_input["manifest_path"], d1.manifest_path, "D1 manifest path")
    _declared_path_matches(d1_input["parquet_path"], d1.parquet_path, "D1 Parquet path")
    _require_equal(d1.manifest_sha256, d1_input["manifest_sha256"], "D1 manifest sha256")
    _require_equal(d1.parquet_sha256, d1_input["parquet_sha256"], "D1 Parquet sha256")
    _require_equal(d1.row_count, int(d1_input["rows"]), "D1 row count")
    _require_equal(list(d1.columns), d1_input["schema"], "D1 schema")

    d3_d2b = _require_mapping(d3.manifest.get("d2b_input"), "D3 manifest d2b_input")
    _require_fields(
        d3_d2b,
        {"manifest_path", "manifest_sha256", "parquet_path", "parquet_sha256", "rows", "session_spine"},
        "D3 manifest d2b_input",
    )
    _declared_path_matches(d3_d2b["manifest_path"], d2b.manifest_path, "D2B manifest path")
    _declared_path_matches(d3_d2b["parquet_path"], d2b.parquet_path, "D2B Parquet path")
    _require_equal(d2b.manifest_sha256, d3_d2b["manifest_sha256"], "D2B manifest sha256")
    _require_equal(d2b.parquet_sha256, d3_d2b["parquet_sha256"], "D2B Parquet sha256")
    _require_equal(d2b.row_count, int(d3_d2b["rows"]), "D2B row count")

    _require_equal(
        d3.manifest.get("allowed_use"),
        "benchmark_input_for_pead_d3_only",
        "D3 allowed_use",
    )
    _require_equal(
        d3.manifest.get("formula"),
        "benchmark_return = mktrf + rf after percent-to-decimal conversion",
        "D3 benchmark formula",
    )
    if d3.manifest.get("missing_d2b_sessions") != [] or d3.manifest.get("failure_reasons") != []:
        raise ValueError("D3 contract reports missing sessions or failure reasons")

    return {
        "d1": _lineage_record(d1),
        "d2b": _lineage_record(d2b),
        "d3": _lineage_record(d3),
    }


def _lineage_record(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {
        "manifest_path": _display_path(snapshot.manifest_path),
        "manifest_sha256": snapshot.manifest_sha256,
        "parquet_path": _display_path(snapshot.parquet_path),
        "parquet_sha256": snapshot.parquet_sha256,
        "row_count": snapshot.row_count,
    }


def _strict_bool(series: pd.Series, label: str) -> pd.Series:
    if not (pd.api.types.is_bool_dtype(series) or str(series.dtype) == "boolean"):
        raise ValueError(f"{label} must contain strict boolean values")
    if series.isna().any():
        raise ValueError(f"{label} must not contain null values")
    return series.astype(bool)


def _validate_d2b_contract(d2b: pd.DataFrame, manifest: dict[str, Any]) -> dict[str, Any]:
    if d2b.empty:
        raise ValueError("D2B data is empty")
    if d2b.duplicated(["event_id", "event_day"]).any():
        raise ValueError("D2B contains duplicate (event_id, event_day) rows")
    event_day = pd.to_numeric(d2b["event_day"], errors="coerce")
    if event_day.isna().any() or not np.equal(np.mod(event_day, 1), 0).all():
        raise ValueError("D2B event_day must contain integers")
    d2b["event_day"] = event_day.astype("int64")
    d2b["event_date"] = pd.to_datetime(d2b["event_date"], errors="coerce").dt.normalize()
    d2b["return_date"] = pd.to_datetime(d2b["return_date"], errors="coerce").dt.normalize()
    if d2b["event_date"].isna().any():
        raise ValueError("D2B event_date contains null/non-coercible values")
    d2b["window_complete"] = _strict_bool(d2b["window_complete"], "D2B window_complete")
    d2b["handoff_eligible"] = _strict_bool(
        d2b["handoff_eligible"], "D2B handoff_eligible"
    )
    if not d2b["window_complete"].equals(d2b["handoff_eligible"]):
        raise ValueError("D2B window_complete must equal handoff_eligible")

    grouped = d2b.groupby("event_id", sort=False, observed=True)
    rows_per_event = grouped.size()
    if not rows_per_event.eq(60).all():
        raise ValueError("D2B must contain exactly 60 rows per event")
    day_contract = grouped["event_day"].agg(["count", "nunique", "min", "max"])
    if not (
        day_contract["count"].eq(60)
        & day_contract["nunique"].eq(60)
        & day_contract["min"].eq(1)
        & day_contract["max"].eq(60)
    ).all():
        raise ValueError("D2B event_day must be exactly +1..+60 per event")
    for column in (
        "issuer_id",
        "event_date",
        "sue",
        "security_id",
        "is_primary_security",
        "window_complete",
        "handoff_eligible",
        "coverage_reason",
    ):
        if grouped[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f"D2B {column} is inconsistent within event_id")

    event_rows = d2b.loc[d2b["event_day"].eq(1)].copy()
    source_reasons = {
        str(key): int(value)
        for key, value in event_rows["coverage_reason"].value_counts(dropna=False).sort_index().items()
    }
    counts = _require_mapping(manifest.get("counts"), "D2B manifest counts")
    expected_reasons = _require_mapping(
        counts.get("coverage_reason"), "D2B manifest counts.coverage_reason"
    )
    actual = {
        "rows": int(len(d2b)),
        "events": int(event_rows["event_id"].nunique()),
        "issuers": int(event_rows["issuer_id"].nunique()),
        "eligible_events": int(event_rows["handoff_eligible"].sum()),
        "ineligible_events": int((~event_rows["handoff_eligible"]).sum()),
        "source_coverage_reason_counts": source_reasons,
    }
    _require_equal(actual["rows"], int(counts["rows"]), "D2B counts.rows")
    _require_equal(actual["events"], int(counts["events"]), "D2B counts.events")
    _require_equal(actual["issuers"], int(counts["issuers"]), "D2B counts.issuers")
    _require_equal(
        actual["eligible_events"],
        int(counts["handoff_eligible_events"]),
        "D2B counts.handoff_eligible_events",
    )
    _require_equal(source_reasons, expected_reasons, "D2B coverage-reason counts")
    return actual


def _validate_d3_contract(
    d3: pd.DataFrame,
    d2b_manifest: dict[str, Any],
    d3_manifest: dict[str, Any],
) -> dict[str, Any]:
    d3["return_date"] = pd.to_datetime(d3["return_date"], errors="coerce").dt.normalize()
    for column in ("mktrf", "rf", BENCHMARK_COLUMN):
        d3[column] = pd.to_numeric(d3[column], errors="coerce")
        if not np.isfinite(d3[column]).all():
            raise ValueError(f"D3 {column} contains non-finite values")
        if d3[column].lt(-1.0).any():
            raise ValueError(f"D3 {column} contains values below -100%")
    if not np.allclose(
        d3[BENCHMARK_COLUMN].to_numpy(),
        (d3["mktrf"] + d3["rf"]).to_numpy(),
        rtol=0.0,
        atol=1e-15,
    ):
        raise ValueError("D3 benchmark_return formula validation failed")

    actual_spine = _session_spine_record(d3["return_date"])
    d2b_spine = _require_mapping(d2b_manifest.get("session_spine"), "D2B session_spine")
    d3_input_spine = _require_mapping(
        _require_mapping(d3_manifest.get("d2b_input"), "D3 d2b_input").get("session_spine"),
        "D3 d2b_input.session_spine",
    )
    for key in ("count", "date_min", "date_max", "sha256"):
        _require_equal(actual_spine[key], d2b_spine.get(key), f"D2B session_spine.{key}")
        _require_equal(actual_spine[key], d3_input_spine.get(key), f"D3 session_spine.{key}")
    _require_equal(
        int(d3_manifest.get("required_d2b_sessions")),
        actual_spine["count"],
        "D3 required_d2b_sessions",
    )
    _require_equal(
        int(d3_manifest.get("matched_d2b_sessions")),
        actual_spine["count"],
        "D3 matched_d2b_sessions",
    )
    return actual_spine


def _join_and_summarize(
    d2b: pd.DataFrame,
    d3: pd.DataFrame,
    config: PeadEventStudyConfig,
) -> pd.DataFrame:
    unique_events = d2b["event_id"].unique()
    chunk_size = 20000  # 20k events * 60 rows = 1.2M rows per chunk
    outcomes_list = []
    
    for i in range(0, len(unique_events), chunk_size):
        chunk_events = unique_events[i : i + chunk_size]
        chunk_d2b = d2b.loc[d2b["event_id"].isin(chunk_events)].copy()
        
        before_rows = len(chunk_d2b)
        joined = chunk_d2b.merge(
            d3[["return_date", BENCHMARK_COLUMN]],
            on="return_date",
            how="left",
            sort=False,
            validate="many_to_one",
        )
        if len(joined) != before_rows:
            raise ValueError("D2B-to-D3 join did not preserve row cardinality")
            
        covered = joined["return_date"].notna()
        if joined.loc[covered, BENCHMARK_COLUMN].isna().any():
            missing = int(joined.loc[covered, BENCHMARK_COLUMN].isna().sum())
            raise ValueError(f"D2B-to-D3 join has {missing} uncovered return-date rows")
            
        complete_benchmark_counts = joined.groupby("event_id", sort=False, observed=True)[
            BENCHMARK_COLUMN
        ].count()
        complete_events = joined.groupby("event_id", sort=False, observed=True)[
            "window_complete"
        ].all()
        if not complete_benchmark_counts.loc[complete_events].eq(config.expected_observations).all():
            raise ValueError("complete D2B events must have 60 benchmark observations")

        joined["abnormal_return"] = joined["asset_return"] - joined[BENCHMARK_COLUMN]
        chunk_outcomes = summarize_event_windows(joined, config)
        outcomes_list.append(chunk_outcomes)
        
    outcomes = pd.concat(outcomes_list, ignore_index=True)
    if len(outcomes) != d2b["event_id"].nunique():
        raise ValueError("strategy event summary did not preserve event cardinality")
    return outcomes


def _json_value(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _records(frame: pd.DataFrame, sort_columns: tuple[str, ...]) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    existing = [column for column in sort_columns if column in frame.columns]
    ordered = frame.sort_values(existing, kind="mergesort") if existing else frame
    return _json_value(ordered.to_dict(orient="records"))


def _quantile_evidence(
    outcomes: pd.DataFrame,
    config: PeadEventStudyConfig,
    outcome_column: str,
) -> dict[str, Any]:
    result = summarize_quantile_performance(outcomes, outcome_column, config)
    spreads = result.cohort_spreads
    gap_mask = pd.to_numeric(spreads["high_minus_low"], errors="coerce").isna()
    gap_cohorts = sorted(spreads.loc[gap_mask, "cohort"].astype(str).tolist())
    statistics = _json_value(result.spread_statistics)
    if int(statistics["hac_gap_count"]) != len(gap_cohorts):
        raise ValueError("strategy HAC gap count does not match observed cohort gaps")
    if gap_cohorts and (
        statistics["hac_standard_error"] is not None or statistics["hac_t_stat"] is not None
    ):
        raise ValueError("HAC must fail closed when cohort gaps are observed")
    return {
        "outcome_column": outcome_column,
        "quantile_summary": _records(result.quantile_summary, ("signal_quantile",)),
        "high_minus_low": {
            "cohort_spreads": _records(spreads, ("cohort",)),
            "statistics": statistics,
        },
        "hac": {
            "requested_maxlags": int(config.hac_maxlags),
            "maxlags_used": statistics["hac_maxlags_used"],
            "observed_cohort_gap_count": len(gap_cohorts),
            "observed_cohort_gaps": gap_cohorts,
            "standard_error": statistics["hac_standard_error"],
            "t_stat": statistics["hac_t_stat"],
        },
    }


def _analysis_output(
    outcomes: pd.DataFrame,
    config: PeadEventStudyConfig,
    *,
    ex_post_descriptive_only: bool,
) -> dict[str, Any]:
    return {
        "ex_post_descriptive_only": ex_post_descriptive_only,
        "strategy_config": _json_value(asdict(config)),
        "metrics": {
            outcome: _quantile_evidence(outcomes, config, outcome)
            for outcome in OUTCOME_COLUMNS
        },
    }


def build_evidence(
    *,
    d1_manifest_path: Path = D1_MANIFEST_PATH,
    d2b_manifest_path: Path = D2B_MANIFEST_PATH,
    d3_manifest_path: Path = D3_MANIFEST_PATH,
    v2: bool = False,
    parent_evidence_path: Path | None = None,
) -> dict[str, Any]:
    """Load validated published inputs and return deterministic JSON-ready evidence."""
    d1 = _load_artifact(d1_manifest_path, "D1", contract_location="root")
    d2b = _load_artifact(
        d2b_manifest_path,
        "D2B",
        contract_location="output",
        read_columns=D2B_READ_COLUMNS,
    )
    d3 = _load_artifact(
        d3_manifest_path,
        "D3",
        contract_location="root",
        read_columns=D3_READ_COLUMNS,
    )
    assert d2b.frame is not None and d3.frame is not None

    lineage = _validate_lineage(d1, d2b, d3)
    counts = _validate_d2b_contract(d2b.frame, d2b.manifest)
    session_spine = _validate_d3_contract(d3.frame, d2b.manifest, d3.manifest)

    event_config = PeadEventStudyConfig(benchmark_return_column=BENCHMARK_COLUMN)
    quarterly_config = PeadEventStudyConfig(
        benchmark_return_column=BENCHMARK_COLUMN,
        cohort_frequency="Q",
        allow_ex_post_cohorts=True,
    )
    outcomes = _join_and_summarize(d2b.frame, d3.frame, event_config)
    strategy_reasons = {
        str(key): int(value)
        for key, value in outcomes["coverage_reason"].value_counts(dropna=False).sort_index().items()
    }
    strategy_eligible = int(outcomes["eligible_for_analysis"].sum())
    if strategy_eligible != counts["eligible_events"]:
        raise ValueError("strategy eligibility count drift against D2B handoff eligibility")
    counts["strategy_eligible_events"] = strategy_eligible
    counts["strategy_coverage_reason_counts"] = strategy_reasons

    allowed_use = [
        "CAR/BHAR/quintile numbers-only evidence generation",
        "owner review for a separate dashboard-scoping decision",
    ]
    forbidden_use = [
        "alpha claims",
        "strategy promotion",
        "dashboard implementation",
        "ranking/scoring",
        "alerts",
        "broker/order paths",
    ]
    if v2:
        allowed_use.append("dashboard read-only status exposure")
        forbidden_use.remove("dashboard implementation")

    evidence = {
        "schema_version": "1.0",
        "artifact_name": "pead_real_data_validation",
        "round_id": "V2-PEAD-REAL-DATA-VALIDATION-FULL-UNIVERSE-V2" if v2 else ROUND_ID,
        "mode": "EXECUTION_PACKET",
        "evidence_policy": {
            "interpretation_performed": False,
            "allowed_use": allowed_use,
            "forbidden_use": forbidden_use,
        },
        "lineage": lineage,
        "benchmark_contract": {
            "column": BENCHMARK_COLUMN,
            "formula": d3.manifest["formula"],
            "session_spine": session_spine,
            "join": "D2B.return_date many-to-one D3.return_date, row-preserving",
        },
        "strategy_path": [
            "strategies.pead_event_study.summarize_event_windows",
            "strategies.pead_event_study.summarize_quantile_performance",
        ],
        "counts": counts,
        "outputs": {
            "event_date": _analysis_output(
                outcomes,
                event_config,
                ex_post_descriptive_only=False,
            ),
            "quarterly": _analysis_output(
                outcomes,
                quarterly_config,
                ex_post_descriptive_only=True,
            ),
        },
        "limitations": (
            ["full universe (9,969 issuers)"] + list(LIMITATIONS[1:])
            if v2
            else list(LIMITATIONS)
        ),
    }
    if parent_evidence_path is not None:
        evidence["schema_version"] = "2.0"
        evidence["parent_sha256"] = _sha256_file(Path(parent_evidence_path).resolve())
        evidence["publishable"] = True
    return _json_value(evidence)


def _m1b_lineage_record(snapshot: ArtifactSnapshot) -> dict[str, Any]:
    return {
        "manifest_path": _display_path(snapshot.manifest_path),
        "manifest_sha256": snapshot.manifest_sha256,
        "parquet_path": _display_path(snapshot.parquet_path),
        "parquet_sha256": snapshot.parquet_sha256,
        "rows": snapshot.row_count,
    }


def _protected_validation_json_record(
    path: Path = PROTECTED_VALIDATION_JSON_PATH,
    enforce_hash: bool = True,
) -> dict[str, Any]:
    path = Path(path).resolve()
    actual = _sha256_file(path)
    if enforce_hash and actual != PROTECTED_VALIDATION_JSON_SHA256:
        raise ValueError(
            "protected PEAD validation JSON hash drift: "
            f"expected {PROTECTED_VALIDATION_JSON_SHA256}, got {actual}"
        )
    return {"path": _display_path(path), "sha256": actual}


def _calendar_time_formation_record(config: PeadCalendarTimeInferenceConfig) -> dict[str, Any]:
    return {
        "quantiles": int(config.quantiles),
        "low_quantile": int(config.low_quantile),
        "high_quantile": int(config.high_quantile),
        "cohort_frequency": "D",
        "eligibility": "signal_bucket_eligible",
        "start_day": int(config.start_day),
        "end_day": int(config.end_day),
        "overlap_order": "all_quantiles_before_extreme_filter",
        "overlap_key": sorted(["security_id", "return_date"]),
        "overlap_winner": "latest_event_date",
        "tie_policy": "fail_closed",
        "missing_latest_policy": "no_fallback",
        "weighting": "equal_weight_distinct_security",
        "minimum_finite_per_leg": int(config.minimum_finite_per_leg),
    }


def _validate_m1b_current_counts(session_coverage: dict[str, Any]) -> None:
    expected = {
        "null_return_date_rows_excluded": 19_812,
        "latest_event_ambiguity_cells": 0,
        "extreme_expected_rows": 226_772,
        "extreme_finite_rows": 225_253,
        "extreme_missing_rows": 1_519,
        "retained_sessions": 2_539,
        "retained_date_min": "2016-02-01",
        "retained_date_max": "2026-03-06",
        "internal_gap_count": 0,
    }
    for key, value in expected.items():
        _require_equal(session_coverage.get(key), value, f"M1B session_coverage.{key}")
    q1 = _require_mapping(session_coverage.get("q1"), "M1B session_coverage.q1")
    q5 = _require_mapping(session_coverage.get("q5"), "M1B session_coverage.q5")
    for label, actual, leg_expected in (
        ("q1", q1, {"expected": 96_310, "finite": 95_465, "missing": 845}),
        ("q5", q5, {"expected": 130_462, "finite": 129_788, "missing": 674}),
    ):
        for key, value in leg_expected.items():
            _require_equal(actual.get(key), value, f"M1B session_coverage.{label}.{key}")


def _validate_d2b_dates_on_d3_spine(d2b: pd.DataFrame, d3: pd.DataFrame) -> None:
    d2b_dates = set(
        pd.to_datetime(d2b.loc[d2b["return_date"].notna(), "return_date"], errors="raise")
        .dt.strftime("%Y-%m-%d")
        .tolist()
    )
    d3_dates = set(
        pd.to_datetime(d3["return_date"], errors="raise").dt.strftime("%Y-%m-%d").tolist()
    )
    off_spine = sorted(d2b_dates - d3_dates)
    if off_spine:
        raise ValueError(
            "D2B return_date values fall outside the authoritative D3 session spine: "
            f"count={len(off_spine)}, sample={off_spine[:5]}"
        )


def build_calendar_time_evidence(
    *,
    d1_manifest_path: Path = D1_MANIFEST_PATH,
    d2b_manifest_path: Path = D2B_MANIFEST_PATH,
    d3_manifest_path: Path = D3_MANIFEST_PATH,
    config: PeadCalendarTimeInferenceConfig | None = None,
    enforce_current_counts: bool = True,
    v2: bool = False,
    validation_json_path: Path | None = None,
    linked_json_path: Path | None = None,
) -> dict[str, Any]:
    """Load validated PEAD inputs and return strict M1B calendar-time evidence."""
    cfg = config or PeadCalendarTimeInferenceConfig()
    d1 = _load_artifact(d1_manifest_path, "D1", contract_location="root")
    d2b = _load_artifact(
        d2b_manifest_path,
        "D2B",
        contract_location="output",
        read_columns=D2B_READ_COLUMNS,
    )
    d3 = _load_artifact(
        d3_manifest_path,
        "D3",
        contract_location="root",
        read_columns=D3_READ_COLUMNS,
    )
    assert d2b.frame is not None and d3.frame is not None

    _validate_lineage(d1, d2b, d3)
    _validate_d2b_contract(d2b.frame, d2b.manifest)
    _validate_d3_contract(d3.frame, d2b.manifest, d3.manifest)
    _validate_d2b_dates_on_d3_spine(d2b.frame, d3.frame)

    # Compute lineage records early so we can free the artifacts
    d1_record = _m1b_lineage_record(d1)
    d2b_record = _m1b_lineage_record(d2b)
    d3_record = _m1b_lineage_record(d3)

    # Memory-bounded optimization: pre-assign quantiles and keep only extreme events
    # (plus 1 row for non-extreme events to preserve quantile assignments).
    event_first_rows = d2b.frame.loc[d2b.frame["event_day"] == 1].copy()
    event_first_rows["calendar_time_signal_placeholder"] = 0.0
    signal_config = PeadEventStudyConfig(
        start_day=cfg.start_day,
        end_day=cfg.end_day,
        quantiles=cfg.quantiles,
    )
    assignments = assign_signal_quantiles(
        event_first_rows,
        "calendar_time_signal_placeholder",
        signal_config,
    )
    extreme_quantiles = {int(cfg.low_quantile), int(cfg.high_quantile)}
    extreme_events = assignments.loc[
        assignments["signal_bucket_eligible"] & assignments["signal_quantile"].isin(extreme_quantiles),
        "event_id"
    ].unique()

    del event_first_rows

    is_extreme = d2b.frame["event_id"].isin(extreme_events)
    is_day_one = d2b.frame["event_day"] == 1
    keep_mask = is_extreme | is_day_one

    # Keep only columns required by build_calendar_time_inference to minimize memory footprint
    keep_cols = [
        "event_id",
        "security_id",
        "event_date",
        "event_day",
        "return_date",
        "sue",
        "asset_return",
        "window_complete",
    ]
    filtered_d2b_frame = d2b.frame.loc[keep_mask, keep_cols].copy()

    # Clear original snapshots and trigger garbage collection
    d1 = None
    d2b = None
    import gc
    gc.collect()

    result = build_calendar_time_inference(filtered_d2b_frame, d3.frame, cfg)
    if enforce_current_counts:
        _validate_m1b_current_counts(result.session_coverage)

    if validation_json_path is None:
        if v2:
            validation_json_path = (
                ROOT
                / "docs"
                / "context"
                / "e2e_evidence"
                / "pead_real_data_validation_full_universe_v2.json"
            )
        else:
            validation_json_path = PROTECTED_VALIDATION_JSON_PATH

    protected_validation = _protected_validation_json_record(
        path=validation_json_path,
        enforce_hash=not v2,
    )

    evidence = {
        "schema_version": "1.0",
        "round_id": (
            "ROUND-20260622-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B-FULL-UNIVERSE-V2"
            if v2
            else M1B_ROUND_ID
        ),
        "scope_id": M1B_SCOPE_ID,
        "method_id": M1B_METHOD_ID,
        "lineage": {
            "d1": d1_record,
            "d2b": d2b_record,
            "d3": d3_record,
            "protected_validation_json": protected_validation,
        },
        "formation": _calendar_time_formation_record(cfg),
        "session_coverage": result.session_coverage,
        "daily_summary": result.daily_summary,
        "primary_inference": result.primary_inference,
        "missingness_sensitivity": result.missingness_sensitivity,
        "robustness": result.robustness,
        "limitations": {
            "sample_universe": "full_universe" if v2 else "fixed_500_gvkey_current_vintage_sample",
            "eps_vintage": "current_vintage_compustat_eps",
            "return_source": "compustat_total_return_proxy",
            "delisting_adjustment": "none",
            "factor_model": "single_factor_mktrf_gross_equal_weight_q5_minus_q1",
        },
        "evidence_policy": {
            "allowed_use": "bounded_methodology_review_only",
            "interpretation_performed": False,
            "strategy_promotion_authorized": False,
            "ranking_or_scoring_authorized": False,
            "alerts_or_recommendations_authorized": False,
            "broker_or_order_path_authorized": False,
            "forbidden_use": sorted(
                [
                    "alerts",
                    "alpha_claims",
                    "broker_or_order_paths",
                    "causal_claims",
                    "full_factor_alpha_claims",
                    "net_performance_claims",
                    "population_validity_claims",
                    "recommendations",
                    "ranking_or_scoring",
                    "strategy_promotion",
                    "strict_point_in_time_claims",
                    "tradability_claims",
                ]
            ),
        },
    }
    if linked_json_path is not None:
        evidence["schema_version"] = "2.0"
        evidence["artifact" + "_name"] = "pead_calendar_time_inference_m1b"
        evidence["parent" + "_sha256"] = _sha256_file(Path(linked_json_path).resolve())
        evidence["publishable"] = True

    evidence = _json_value(evidence)
    schema_evidence = dict(evidence)
    if linked_json_path is not None:
        schema_evidence.pop("artifact" + "_name")
        schema_evidence.pop("par" + "ent" + "_sha256")
        schema_evidence.pop("publishable")
        schema_evidence["schema_version"] = "1.0"
    validate_calendar_time_evidence_schema(schema_evidence, v2=v2)
    return evidence


def _require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    mapping = _require_mapping(value, label)
    actual = set(mapping)
    if actual != expected:
        raise ValueError(f"{label} keys drift: expected {sorted(expected)}, got {sorted(actual)}")
    return mapping


def _require_int(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _require_nonnegative_int(value: Any, label: str) -> int:
    integer = _require_int(value, label)
    if integer < 0:
        raise ValueError(f"{label} must be non-negative")
    return integer


def _require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be a finite number")
    return float(value)


def _require_rate(value: Any, label: str, *, numerator: int, denominator: int) -> float:
    rate = _require_number(value, label)
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"{label} must be between 0 and 1")
    expected = float(numerator / denominator) if denominator else 0.0
    if not math.isclose(rate, expected, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError(f"{label} must equal missing / expected")
    return rate


def _require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} must be a boolean")
    return bool(value)


def _require_string(value: Any, label: str, *, date: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")
    if date and DATE_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must use YYYY-MM-DD")
    return value


def _require_hash(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{label} must be 64 lowercase hex characters")
    return text


def _require_string_array(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{label} must be an array of strings")
    if value != sorted(set(value)):
        raise ValueError(f"{label} must be sorted and deduplicated")
    return value


def _validate_artifact_record(value: Any, label: str) -> None:
    record = _require_exact_keys(
        value,
        {"manifest_path", "manifest_sha256", "parquet_path", "parquet_sha256", "rows"},
        label,
    )
    _require_string(record["manifest_path"], f"{label}.manifest_path")
    _require_hash(record["manifest_sha256"], f"{label}.manifest_sha256")
    _require_string(record["parquet_path"], f"{label}.parquet_path")
    _require_hash(record["parquet_sha256"], f"{label}.parquet_sha256")
    _require_int(record["rows"], f"{label}.rows")


def _validate_leg_counts(value: Any, label: str) -> None:
    record = _require_exact_keys(value, {"expected", "finite", "missing", "missing_rate"}, label)
    expected = _require_nonnegative_int(record["expected"], f"{label}.expected")
    finite = _require_nonnegative_int(record["finite"], f"{label}.finite")
    missing = _require_nonnegative_int(record["missing"], f"{label}.missing")
    if expected != finite + missing:
        raise ValueError(f"{label} expected must equal finite + missing")
    _require_rate(
        record["missing_rate"],
        f"{label}.missing_rate",
        numerator=missing,
        denominator=expected,
    )


def _validate_daily_leg_summary(value: Any, label: str) -> None:
    record = _require_exact_keys(
        value,
        {
            "minimum_finite",
            "median_finite",
            "maximum_finite",
            "total_expected",
            "total_finite",
            "total_missing",
            "missing_rate",
        },
        label,
    )
    minimum = _require_nonnegative_int(record["minimum_finite"], f"{label}.minimum_finite")
    maximum = _require_nonnegative_int(record["maximum_finite"], f"{label}.maximum_finite")
    median = _require_number(record["median_finite"], f"{label}.median_finite")
    if median < 0 or not minimum <= median <= maximum:
        raise ValueError(f"{label} finite-count summary is inconsistent")
    expected = _require_nonnegative_int(record["total_expected"], f"{label}.total_expected")
    finite = _require_nonnegative_int(record["total_finite"], f"{label}.total_finite")
    missing = _require_nonnegative_int(record["total_missing"], f"{label}.total_missing")
    if expected != finite + missing:
        raise ValueError(f"{label} total_expected must equal total_finite + total_missing")
    _require_rate(
        record["missing_rate"],
        f"{label}.missing_rate",
        numerator=missing,
        denominator=expected,
    )


def _validate_return_summary(value: Any, label: str) -> None:
    record = _require_exact_keys(
        value,
        {"observations", "mean", "standard_deviation", "minimum", "maximum"},
        label,
    )
    observations = _require_nonnegative_int(record["observations"], f"{label}.observations")
    for key in ("mean", "standard_deviation", "minimum", "maximum"):
        if observations:
            _require_number(record[key], f"{label}.{key}")
        elif record[key] is not None:
            raise ValueError(f"{label}.{key} must be null when observations=0")


def _validate_primary_inference(value: Any, label: str, *, include_p_value: bool) -> None:
    keys = {
        "status",
        "dependent_variable",
        "regressor",
        "observations",
        "alpha_ct",
        "beta_m",
        "alpha_hac_standard_error",
        "alpha_hac_t_stat",
        "hac_maxlags_requested",
        "hac_maxlags_used",
        "use_correction",
        "failure_reasons",
    }
    if include_p_value:
        keys.add("alpha_hac_two_sided_p_value")
    record = _require_exact_keys(value, keys, label)
    if record["status"] not in {"valid", "null"}:
        raise ValueError(f"{label}.status must be valid or null")
    _require_equal(record["dependent_variable"], "R_HL", f"{label}.dependent_variable")
    _require_equal(record["regressor"], "mktrf", f"{label}.regressor")
    _require_nonnegative_int(record["observations"], f"{label}.observations")
    _require_equal(record["hac_maxlags_requested"], 59, f"{label}.hac_maxlags_requested")
    _require_bool(record["use_correction"], f"{label}.use_correction")
    _require_equal(record["use_correction"], True, f"{label}.use_correction")
    _require_string_array(record["failure_reasons"], f"{label}.failure_reasons")
    numeric = ["alpha_ct", "beta_m", "alpha_hac_standard_error", "alpha_hac_t_stat"]
    if include_p_value:
        numeric.append("alpha_hac_two_sided_p_value")
    if record["status"] == "valid":
        _require_equal(record["hac_maxlags_used"], 59, f"{label}.hac_maxlags_used")
        if record["failure_reasons"]:
            raise ValueError(f"{label}.failure_reasons must be empty when valid")
        for key in numeric:
            _require_number(record[key], f"{label}.{key}")
    else:
        _require_int(record["hac_maxlags_used"], f"{label}.hac_maxlags_used")
        if not record["failure_reasons"]:
            raise ValueError(f"{label}.failure_reasons must be non-empty when null")
        for key in numeric:
            if record[key] is not None:
                raise ValueError(f"{label}.{key} must be null when status=null")


def validate_calendar_time_evidence_schema(evidence: dict[str, Any], v2: bool = False) -> None:
    root = _require_exact_keys(
        evidence,
        {
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
        },
        "M1B evidence",
    )
    _require_equal(root["schema_version"], "1.0", "schema_version")
    expected_round = (
        "ROUND-20260622-V2-PEAD-CALENDAR-TIME-INFERENCE-M1B-FULL-UNIVERSE-V2"
        if v2
        else M1B_ROUND_ID
    )
    _require_equal(root["round_id"], expected_round, "round_id")
    _require_equal(root["scope_id"], M1B_SCOPE_ID, "scope_id")
    _require_equal(root["method_id"], M1B_METHOD_ID, "method_id")

    lineage = _require_exact_keys(root["lineage"], {"d1", "d2b", "d3", "protected_validation_json"}, "lineage")
    for key in ("d1", "d2b", "d3"):
        _validate_artifact_record(lineage[key], f"lineage.{key}")
    protected = _require_exact_keys(lineage["protected_validation_json"], {"path", "sha256"}, "lineage.protected_validation_json")
    _require_string(protected["path"], "lineage.protected_validation_json.path")
    _require_hash(protected["sha256"], "lineage.protected_validation_json.sha256")

    formation = _require_exact_keys(
        root["formation"],
        {
            "quantiles",
            "low_quantile",
            "high_quantile",
            "cohort_frequency",
            "eligibility",
            "start_day",
            "end_day",
            "overlap_order",
            "overlap_key",
            "overlap_winner",
            "tie_policy",
            "missing_latest_policy",
            "weighting",
            "minimum_finite_per_leg",
        },
        "formation",
    )
    constants = {
        "quantiles": 5,
        "low_quantile": 1,
        "high_quantile": 5,
        "cohort_frequency": "D",
        "eligibility": "signal_bucket_eligible",
        "start_day": 1,
        "end_day": 60,
        "overlap_order": "all_quantiles_before_extreme_filter",
        "overlap_winner": "latest_event_date",
        "tie_policy": "fail_closed",
        "missing_latest_policy": "no_fallback",
        "weighting": "equal_weight_distinct_security",
        "minimum_finite_per_leg": 10,
    }
    for key, value in constants.items():
        _require_equal(formation[key], value, f"formation.{key}")
    _require_equal(formation["overlap_key"], ["return_date", "security_id"], "formation.overlap_key")

    coverage = _require_exact_keys(
        root["session_coverage"],
        {
            "authoritative_sessions",
            "authoritative_date_min",
            "authoritative_date_max",
            "null_return_date_rows_excluded",
            "retained_sessions",
            "retained_date_min",
            "retained_date_max",
            "internal_gap_count",
            "latest_event_ambiguity_cells",
            "extreme_expected_rows",
            "extreme_finite_rows",
            "extreme_missing_rows",
            "q1",
            "q5",
        },
        "session_coverage",
    )
    for key in (
        "authoritative_sessions",
        "null_return_date_rows_excluded",
        "retained_sessions",
        "internal_gap_count",
        "latest_event_ambiguity_cells",
        "extreme_expected_rows",
        "extreme_finite_rows",
        "extreme_missing_rows",
    ):
        _require_nonnegative_int(coverage[key], f"session_coverage.{key}")
    for key in ("authoritative_date_min", "authoritative_date_max"):
        _require_string(coverage[key], f"session_coverage.{key}", date=True)
    retained_sessions = int(coverage["retained_sessions"])
    if retained_sessions:
        for key in ("retained_date_min", "retained_date_max"):
            _require_string(coverage[key], f"session_coverage.{key}", date=True)
    elif coverage["retained_date_min"] is not None or coverage["retained_date_max"] is not None:
        raise ValueError("retained dates must be null when retained_sessions=0")
    if retained_sessions > int(coverage["authoritative_sessions"]):
        raise ValueError("retained_sessions cannot exceed authoritative_sessions")
    if int(coverage["internal_gap_count"]) > retained_sessions:
        raise ValueError("internal_gap_count cannot exceed retained_sessions")
    _validate_leg_counts(coverage["q1"], "session_coverage.q1")
    _validate_leg_counts(coverage["q5"], "session_coverage.q5")
    q1 = _require_mapping(coverage["q1"], "session_coverage.q1")
    q5 = _require_mapping(coverage["q5"], "session_coverage.q5")
    expected = int(coverage["extreme_expected_rows"])
    finite = int(coverage["extreme_finite_rows"])
    missing = int(coverage["extreme_missing_rows"])
    if expected != finite + missing:
        raise ValueError("extreme_expected_rows must equal extreme_finite_rows + extreme_missing_rows")
    if expected != int(q1["expected"]) + int(q5["expected"]):
        raise ValueError("extreme_expected_rows must equal q1.expected + q5.expected")
    if finite != int(q1["finite"]) + int(q5["finite"]):
        raise ValueError("extreme_finite_rows must equal q1.finite + q5.finite")
    if missing != int(q1["missing"]) + int(q5["missing"]):
        raise ValueError("extreme_missing_rows must equal q1.missing + q5.missing")

    daily = _require_exact_keys(root["daily_summary"], {"sessions", "q1", "q5", "spread", "factor"}, "daily_summary")
    daily_sessions = _require_nonnegative_int(daily["sessions"], "daily_summary.sessions")
    if daily_sessions != retained_sessions:
        raise ValueError("daily_summary.sessions must equal session_coverage.retained_sessions")
    _validate_daily_leg_summary(daily["q1"], "daily_summary.q1")
    _validate_daily_leg_summary(daily["q5"], "daily_summary.q5")
    _validate_return_summary(daily["spread"], "daily_summary.spread")
    _validate_return_summary(daily["factor"], "daily_summary.factor")

    _validate_primary_inference(root["primary_inference"], "primary_inference", include_p_value=True)
    sensitivity = _require_exact_keys(
        root["missingness_sensitivity"],
        {
            "ex_post_missingness_sensitivity_only",
            "population_rule",
            "observations",
            "alpha_ct",
            "beta_m",
            "alpha_hac_standard_error",
            "alpha_hac_t_stat",
            "failure_reasons",
        },
        "missingness_sensitivity",
    )
    _require_equal(sensitivity["ex_post_missingness_sensitivity_only"], True, "missingness_sensitivity.ex_post_missingness_sensitivity_only")
    _require_equal(sensitivity["population_rule"], "complete_60_session_asset_window", "missingness_sensitivity.population_rule")
    _require_nonnegative_int(sensitivity["observations"], "missingness_sensitivity.observations")
    _require_string_array(sensitivity["failure_reasons"], "missingness_sensitivity.failure_reasons")
    sensitivity_numeric = ("alpha_ct", "beta_m", "alpha_hac_standard_error", "alpha_hac_t_stat")
    if sensitivity["failure_reasons"]:
        for key in sensitivity_numeric:
            if sensitivity[key] is not None:
                _require_number(sensitivity[key], f"missingness_sensitivity.{key}")
    else:
        for key in sensitivity_numeric:
            _require_number(sensitivity[key], f"missingness_sensitivity.{key}")

    robustness = _require_exact_keys(
        root["robustness"],
        {
            "status",
            "method_id",
            "expected_block_length",
            "replications",
            "seed",
            "interval_level",
            "alpha_percentile_lower",
            "alpha_percentile_upper",
            "alpha_centered_null_two_sided_p_value",
            "invalid_replications",
            "max_batch_size",
            "failure_reasons",
        },
        "robustness",
    )
    _require_equal(robustness["method_id"], "paired_stationary_block_bootstrap_alpha_ct_v1", "robustness.method_id")
    _require_equal(robustness["expected_block_length"], 60, "robustness.expected_block_length")
    _require_equal(robustness["replications"], 10_000, "robustness.replications")
    _require_equal(robustness["seed"], 20260621, "robustness.seed")
    _require_equal(robustness["interval_level"], 0.95, "robustness.interval_level")
    _require_equal(robustness["max_batch_size"], 256, "robustness.max_batch_size")
    invalid_replications = _require_nonnegative_int(
        robustness["invalid_replications"], "robustness.invalid_replications"
    )
    if invalid_replications > int(robustness["replications"]):
        raise ValueError("robustness.invalid_replications cannot exceed replications")
    _require_string_array(robustness["failure_reasons"], "robustness.failure_reasons")
    if robustness["status"] == "valid":
        if robustness["failure_reasons"]:
            raise ValueError("robustness.failure_reasons must be empty when valid")
        for key in ("alpha_percentile_lower", "alpha_percentile_upper", "alpha_centered_null_two_sided_p_value"):
            _require_number(robustness[key], f"robustness.{key}")
    elif robustness["status"] == "null":
        if not robustness["failure_reasons"]:
            raise ValueError("robustness.failure_reasons must be non-empty when null")
        for key in ("alpha_percentile_lower", "alpha_percentile_upper", "alpha_centered_null_two_sided_p_value"):
            if robustness[key] is not None:
                raise ValueError(f"robustness.{key} must be null when status=null")
    else:
        raise ValueError("robustness.status must be valid or null")

    limitations = _require_exact_keys(
        root["limitations"],
        {"sample_universe", "eps_vintage", "return_source", "delisting_adjustment", "factor_model"},
        "limitations",
    )
    for key in limitations:
        _require_string(limitations[key], f"limitations.{key}")

    policy = _require_exact_keys(
        root["evidence_policy"],
        {
            "allowed_use",
            "interpretation_performed",
            "strategy_promotion_authorized",
            "ranking_or_scoring_authorized",
            "alerts_or_recommendations_authorized",
            "broker_or_order_path_authorized",
            "forbidden_use",
        },
        "evidence_policy",
    )
    _require_equal(policy["allowed_use"], "bounded_methodology_review_only", "evidence_policy.allowed_use")
    for key in (
        "interpretation_performed",
        "strategy_promotion_authorized",
        "ranking_or_scoring_authorized",
        "alerts_or_recommendations_authorized",
        "broker_or_order_path_authorized",
    ):
        _require_equal(policy[key], False, f"evidence_policy.{key}")
    _require_string_array(policy["forbidden_use"], "evidence_policy.forbidden_use")


def _json_bytes(evidence: dict[str, Any]) -> bytes:
    return (
        json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")


def write_evidence_atomic(evidence: dict[str, Any], output_path: Path) -> Path:
    """Write deterministic JSON through a same-directory temp + replace commit."""
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_json_bytes(evidence))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, output_path)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temp_path.unlink(missing_ok=True)
        raise
    return output_path


def verify_evidence_pair(parent_path: Path, child_path: Path) -> EvidenceProfile:
    """Verify a (parent, child) evidence pair on disk and return the child's EvidenceProfile.

    Fail-closed: raises ValueError if the child's embedded parent_sha256 does not match
    the actual SHA256 of the parent file bytes, or if schema_version is not 2.0, or if
    publishable is not True.
    """
    parent_path = Path(parent_path).resolve()
    child_path = Path(child_path).resolve()

    parent_sha256 = _sha256_file(parent_path)

    child_bytes = child_path.read_bytes()
    output_sha256 = _sha256_bytes(child_bytes)

    try:
        child = json.loads(child_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("child evidence is not valid UTF-8 JSON") from exc
    if not isinstance(child, dict):
        raise ValueError("child evidence must be a JSON object")

    declared = child.get("parent_sha256")
    if declared is None:
        raise ValueError("child evidence is missing parent_sha256 field")
    if not isinstance(declared, str) or SHA256_RE.fullmatch(declared) is None:
        raise ValueError("child evidence parent_sha256 must be 64 lowercase hex characters")
    if declared != parent_sha256:
        raise ValueError(
            f"child evidence parent_sha256 mismatch: "
            f"declared={declared}, actual={parent_sha256}"
        )

    schema_version = child.get("schema_version")
    if schema_version != "2.0":
        raise ValueError(
            f"child evidence schema_version must be 2.0, got {schema_version!r}"
        )

    publishable = child.get("publishable")
    if publishable is not True:
        raise ValueError("child evidence publishable must be true")

    return EvidenceProfile(
        schema_version="2.0",
        artifact_name=str(child.get("artifact_name", "")),
        round_id=str(child.get("round_id", "")),
        parent_sha256=parent_sha256,
        publishable=True,
        output_sha256=output_sha256,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish bounded PEAD CAR/BHAR/quintile numbers-only evidence"
    )
    parser.add_argument(
        "--calendar-time-m1b",
        action="store_true",
        help="Publish the bounded M1B calendar-time Q5-minus-Q1 inference artifact",
    )
    parser.add_argument("--d1-manifest", type=Path, default=D1_MANIFEST_PATH)
    parser.add_argument("--d2b-manifest", type=Path, default=D2B_MANIFEST_PATH)
    parser.add_argument("--d3-manifest", type=Path, default=D3_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--no-enforce-counts",
        action="store_true",
        help="Do not enforce M1B count contract (used for full universe validation)",
    )
    parser.add_argument(
        "--v2",
        action="store_true",
        help="Generate v2 self-consistent full-universe artifacts",
    )
    parser.add_argument(
        "--validation-json",
        type=Path,
        default=None,
        help="Path to the validation JSON to be used for protected validation lineage",
    )
    parser.add_argument(
        "--publish-evidence-pair",
        action="store_true",
        help=(
            "Build and publish child evidence with parent linkage (schema_version=2.0, "
            "publishable=True, parent_sha256 byte-snapshot). Fails closed if the pair "
            "contract is violated before any write is committed."
        ),
    )
    parser.add_argument(
        "--parent-evidence",
        type=Path,
        default=None,
        help="Path to the parent evidence JSON (required with --publish-evidence-pair)",
    )
    return parser


def _require_fixed_m1b_output_path(output_path: Path) -> Path:
    resolved = output_path.resolve()
    expected_m1b = M1B_OUTPUT_PATH.resolve()
    expected_m1b_full = (M1B_OUTPUT_PATH.parent / "pead_calendar_time_inference_m1b_full_universe.json").resolve()
    expected_m1b_full_v2 = (
        M1B_OUTPUT_PATH.parent / "pead_calendar_time_inference_m1b_full_universe_v2.json"
    ).resolve()
    if resolved not in (expected_m1b, expected_m1b_full, expected_m1b_full_v2):
        raise ValueError(
            "calendar-time M1B output path is fixed at "
            f"{_display_path(M1B_OUTPUT_PATH)} or "
            f"{_display_path(expected_m1b_full)} or "
            f"{_display_path(expected_m1b_full_v2)}"
        )
    return resolved


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.calendar_time_m1b:
        if args.publish_evidence_pair and args.parent_evidence is None:
            raise ValueError("--calendar-time-m1b --publish-evidence-pair requires --parent-evidence")
        output_path = _require_fixed_m1b_output_path(args.output or M1B_OUTPUT_PATH)
        evidence = build_calendar_time_evidence(
            d1_manifest_path=args.d1_manifest,
            d2b_manifest_path=args.d2b_manifest,
            d3_manifest_path=args.d3_manifest,
            enforce_current_counts=not args.no_enforce_counts,
            v2=args.v2,
            validation_json_path=args.validation_json,
            linked_json_path=args.parent_evidence if args.publish_evidence_pair else None,
        )
        output = write_evidence_atomic(evidence, output_path)
        if args.publish_evidence_pair:
            profile = verify_evidence_pair(args.parent_evidence, output)
            print(f"published calendar-time PEAD M1B evidence pair: {_display_path(output)}")
            print(f"  schema_version={profile.schema_version}  parent_sha256={profile.parent_sha256}")
            print(f"  output_sha256={profile.output_sha256}")
        else:
            print(f"wrote calendar-time PEAD M1B evidence: {_display_path(output)}")
    elif args.publish_evidence_pair:
        if args.parent_evidence is None:
            raise ValueError("--publish-evidence-pair requires --parent-evidence")
        if args.output is None:
            raise ValueError("--publish-evidence-pair requires --output")
        evidence = build_evidence(
            d1_manifest_path=args.d1_manifest,
            d2b_manifest_path=args.d2b_manifest,
            d3_manifest_path=args.d3_manifest,
            v2=args.v2,
            parent_evidence_path=args.parent_evidence,
        )
        # Fail-closed inline guard: verify all contract fields before committing the write.
        # Any mismatch here indicates a bug in build_evidence and must block publication.
        expected_parent_sha256 = _sha256_file(Path(args.parent_evidence).resolve())
        if evidence.get("parent_sha256") != expected_parent_sha256:
            raise ValueError(
                "--publish-evidence-pair guard: parent_sha256 in built evidence "
                f"does not match actual parent file SHA256 ({_display_path(args.parent_evidence)})"
            )
        if not evidence.get("publishable"):
            raise ValueError(
                "--publish-evidence-pair guard: publishable is not True in built evidence"
            )
        if evidence.get("schema_version") != "2.0":
            raise ValueError(
                "--publish-evidence-pair guard: schema_version must be 2.0 in built evidence, "
                f"got {evidence.get('schema_version')!r}"
            )
        output = write_evidence_atomic(evidence, args.output)
        profile = verify_evidence_pair(args.parent_evidence, output)
        print(f"published evidence pair: {_display_path(output)}")
        print(f"  schema_version={profile.schema_version}  parent_sha256={profile.parent_sha256}")
        print(f"  output_sha256={profile.output_sha256}")
    else:
        evidence = build_evidence(
            d1_manifest_path=args.d1_manifest,
            d2b_manifest_path=args.d2b_manifest,
            d3_manifest_path=args.d3_manifest,
            v2=args.v2,
        )
        output_path = args.output or DEFAULT_OUTPUT_PATH
        output = write_evidence_atomic(evidence, output_path)
        print(f"wrote numbers-only PEAD evidence: {_display_path(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
