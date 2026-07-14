"""Standalone dated-identifier authority gate for PEAD M7F5-ID0.

This module locks the complete pre-identity 2019 D1 event universe and inspects
one candidate Compustat identifier source for genuine effective-date intervals.
It does not import any M7F4/portfolio code, fetch data, create a mapping artifact,
or run a research curve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_D1_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet"
DEFAULT_IDENTIFIER_SOURCE_PATH = (
    ROOT / "data" / "processed" / "security_master_compustat.parquet"
)

ROUND_ID = "ROUND-20260714-M7F5-ID0-DATED-IDENTIFIER-AUTHORITY"
SCOPE_ID = "M7F5_ID0_DATED_IDENTIFIER_AUTHORITY_COMMIT_A"
SCHEMA_VERSION = "pead_m7f5_id0_dated_identifier_authority_v1"
COHORT_YEAR = 2019

LOCKED_D1_SHA256 = (
    "81b2689b48943373f58586ddc382fb609dbce022cde93d4d502333cae5541855"
)
LOCKED_PRE_IDENTITY_EVENT_COUNT = 21_882
LOCKED_PRE_IDENTITY_EVENT_SET_SHA256 = (
    "2922192aba299a7ab741e2ff1183f033291312614fbb4b3dce60f760fe7e06a5"
)
LOCKED_PRE_IDENTITY_CANONICAL_ROWS_SHA256 = (
    "3592137066ad74290e988ac06f4b6e29ccce64fc29ce8be4e864a3d0b7a882bd"
)

STATUS_BLOCKED_D1_LOCK = "BLOCKED_D1_PRE_IDENTITY_LOCK_MISMATCH"
STATUS_BLOCKED_SOURCE_ABSENT = (
    "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SOURCE_ABSENT"
)
STATUS_BLOCKED_SCHEMA = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SCHEMA_INVALID"
STATUS_BLOCKED_INTERVALS = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_INTERVAL_INVALID"
STATUS_BLOCKED_COVERAGE = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_EVENT_COVERAGE_INCOMPLETE"
STATUS_BLOCKED_AMBIGUITY = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_EVENT_IDENTITY_AMBIGUOUS"
STATUS_PASS = "PASS_DATED_COMPUSTAT_IDENTIFIER_SOURCE_CONTRACT"

IDENTIFIER_COLUMN_CANDIDATES: tuple[str, ...] = (
    "cusip8",
    "cusip",
    "ncusip",
)
EFFECTIVE_DATE_COLUMN_PAIRS: tuple[tuple[str, str], ...] = (
    ("effective_start", "effective_end"),
    ("effective_from", "effective_to"),
    ("start_date", "end_date"),
    ("from_date", "thru_date"),
    ("linkdt", "linkenddt"),
    ("namedt", "nameendt"),
    ("effdate", "thrudate"),
)


class M7F5ID0InputError(ValueError):
    """Invalid invocation or unreadable input."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_lines(lines: Iterable[str]) -> str:
    ordered = sorted(lines)
    payload = "\n".join(ordered) + ("\n" if ordered else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_line(record: Mapping[str, Any]) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _path_text(path: Path) -> str:
    return path.resolve().as_posix()


def _read_parquet_with_stable_sha256(
    path: Path, *, label: str
) -> tuple[pd.DataFrame, str]:
    """Bind parsing and hashing to one private immutable byte snapshot."""
    if not path.is_file():
        raise M7F5ID0InputError(f"{label}_not_found:{path}")
    digest = hashlib.sha256()
    snapshot_path: Path | None = None
    try:
        with path.open("rb") as source, tempfile.NamedTemporaryFile(
            suffix=".parquet", delete=False
        ) as snapshot:
            snapshot_path = Path(snapshot.name)
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
                snapshot.write(chunk)
            snapshot.flush()
            os.fsync(snapshot.fileno())
        frame = pd.read_parquet(snapshot_path)
    except M7F5ID0InputError:
        raise
    except OSError as exc:
        raise M7F5ID0InputError(
            f"{label}_changed_or_unreadable_during_read:{path}:{exc}"
        ) from exc
    except Exception as exc:  # pragma: no cover - backend-specific detail
        raise M7F5ID0InputError(f"{label}_unreadable:{path}:{exc}") from exc
    finally:
        if snapshot_path is not None:
            snapshot_path.unlink(missing_ok=True)
    return frame, digest.hexdigest()


def _normalize_timestamp_series(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.dt.tz_convert(None).dt.normalize()


def _normalize_gvkey(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def _cusip_check_digit(cusip8: pd.Series) -> pd.Series:
    values_by_character = {
        **{str(value): value for value in range(10)},
        **{chr(ord("A") + value): 10 + value for value in range(26)},
    }
    total = pd.Series(0, index=cusip8.index, dtype="Int64")
    for position in range(8):
        value = cusip8.str[position].map(values_by_character).astype("Int64")
        weighted = value * (2 if position % 2 else 1)
        total = total + weighted.floordiv(10) + weighted.mod(10)
    return ((10 - total.mod(10)).mod(10)).astype("string")


def _lexical_identifier_mask(series: pd.Series) -> pd.Series:
    if isinstance(series.dtype, pd.CategoricalDtype):
        return pd.Series(False, index=series.index, dtype=bool)
    if pd.api.types.is_object_dtype(series.dtype):
        def is_lexical_or_missing(value: Any) -> bool:
            if isinstance(value, str):
                return True
            if not pd.api.types.is_scalar(value):
                return False
            return bool(pd.isna(value))

        return series.map(is_lexical_or_missing).astype(bool)
    if pd.api.types.is_string_dtype(series.dtype):
        return pd.Series(True, index=series.index, dtype=bool)
    return pd.Series(False, index=series.index, dtype=bool)


def _normalize_identifier8(series: pd.Series, *, source_column: str) -> pd.Series:
    lexical = _lexical_identifier_mask(series)
    trimmed = series.where(lexical).astype("string").str.strip()
    ascii_shape = trimmed.str.fullmatch(r"[0-9A-Za-z]{8,9}", na=False)
    cleaned = trimmed.where(ascii_shape).str.upper()
    source_name = source_column.casefold()
    if source_name == "cusip":
        identifier8 = cleaned.str.slice(0, 8)
        valid8 = cleaned.str.fullmatch(r"[0-9A-Z]{8}", na=False)
        valid9_shape = cleaned.str.fullmatch(r"[0-9A-Z]{8}[0-9]", na=False)
        valid9_checksum = cleaned.str[8].eq(_cusip_check_digit(identifier8))
        return identifier8.where(valid8 | (valid9_shape & valid9_checksum))
    valid = cleaned.str.fullmatch(r"[0-9A-Z]{8}", na=False)
    return cleaned.where(valid)


def build_pre_identity_events(d1_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reconstruct the complete 2019 D1 event universe before any identity join."""
    required = {"gvkey", "rdq", "sue_price_scaled_clipped", "valid_sue"}
    missing = sorted(required - set(d1_frame.columns))
    if missing:
        raise M7F5ID0InputError(f"d1_required_columns_missing:{','.join(missing)}")

    frame = d1_frame.loc[:, sorted(required)].copy()
    frame["gvkey"] = _normalize_gvkey(frame["gvkey"])
    frame["rdq"] = _normalize_timestamp_series(frame["rdq"])
    frame["sue"] = pd.to_numeric(frame["sue_price_scaled_clipped"], errors="coerce")
    valid_flag = frame["valid_sue"].fillna(False).astype(bool)
    eligible = frame.loc[
        valid_flag
        & frame["gvkey"].notna()
        & frame["gvkey"].ne("")
        & frame["rdq"].notna()
        & frame["rdq"].dt.year.eq(COHORT_YEAR)
        & frame["sue"].notna()
        & frame["sue"].abs().lt(float("inf")),
        ["gvkey", "rdq", "sue"],
    ].copy()

    raw_eligible_rows = int(len(eligible))
    duplicate_rows = int(eligible.duplicated(["gvkey", "rdq"], keep=False).sum())
    events = (
        eligible.groupby(["gvkey", "rdq"], as_index=False, sort=True)["sue"]
        .max()
        .sort_values(["gvkey", "rdq"], kind="mergesort")
        .reset_index(drop=True)
    )
    events["event_id"] = (
        events["gvkey"].astype(str)
        + "|"
        + events["rdq"].dt.strftime("%Y-%m-%d")
    )

    event_set_sha256 = _sha256_lines(events["event_id"].astype(str).tolist())
    canonical_rows_sha256 = _sha256_lines(
        _json_line(
            {
                "gvkey": str(row.gvkey),
                "rdq": row.rdq.strftime("%Y-%m-%d"),
                "sue": float(row.sue),
            }
        )
        for row in events.itertuples(index=False)
    )
    contract = {
        "cohort_year": COHORT_YEAR,
        "raw_eligible_rows": raw_eligible_rows,
        "duplicate_eligible_rows": duplicate_rows,
        "unique_pre_identity_events": int(len(events)),
        "pre_identity_event_set_sha256": event_set_sha256,
        "pre_identity_canonical_rows_sha256": canonical_rows_sha256,
    }
    return events.loc[:, ["event_id", "gvkey", "rdq", "sue"]], contract


def inspect_d1_lock(
    d1_path: Path,
    *,
    expected_sha256: str = LOCKED_D1_SHA256,
    expected_event_count: int = LOCKED_PRE_IDENTITY_EVENT_COUNT,
    expected_event_set_sha256: str = LOCKED_PRE_IDENTITY_EVENT_SET_SHA256,
    expected_canonical_rows_sha256: str = LOCKED_PRE_IDENTITY_CANONICAL_ROWS_SHA256,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    d1_frame, actual_sha256 = _read_parquet_with_stable_sha256(
        d1_path, label="d1"
    )
    events, contract = build_pre_identity_events(d1_frame)
    mismatches: list[str] = []
    if actual_sha256 != expected_sha256:
        mismatches.append("d1_sha256")
    if contract["unique_pre_identity_events"] != expected_event_count:
        mismatches.append("pre_identity_event_count")
    if contract["pre_identity_event_set_sha256"] != expected_event_set_sha256:
        mismatches.append("pre_identity_event_set_sha256")
    if contract["pre_identity_canonical_rows_sha256"] != expected_canonical_rows_sha256:
        mismatches.append("pre_identity_canonical_rows_sha256")

    report = {
        "path": _path_text(d1_path),
        "sha256": actual_sha256,
        "expected_sha256": expected_sha256,
        **contract,
        "expected_unique_pre_identity_events": expected_event_count,
        "expected_pre_identity_event_set_sha256": expected_event_set_sha256,
        "expected_pre_identity_canonical_rows_sha256": expected_canonical_rows_sha256,
        "mismatches": mismatches,
        "verified": not mismatches,
    }
    return events, report


def _casefold_columns(columns: Sequence[str]) -> dict[str, str]:
    return {str(column).casefold(): str(column) for column in columns}


def _resolve_named_column(
    columns: Sequence[str], requested: str | None, candidates: Sequence[str]
) -> str | None:
    index = _casefold_columns(columns)
    if requested:
        return index.get(requested.casefold())
    for candidate in candidates:
        resolved = index.get(candidate.casefold())
        if resolved is not None:
            return resolved
    return None


def _resolve_effective_pair(
    columns: Sequence[str],
    *,
    requested_start: str | None,
    requested_end: str | None,
) -> tuple[str, str] | None:
    explicitly_requested = requested_start is not None or requested_end is not None
    if explicitly_requested and (
        requested_start is None
        or requested_end is None
        or not requested_start.strip()
        or not requested_end.strip()
    ):
        raise M7F5ID0InputError(
            "effective_start_and_end_columns_must_be_non_empty_and_supplied_together"
        )
    index = _casefold_columns(columns)
    if explicitly_requested:
        start = index.get(requested_start.strip().casefold())
        end = index.get(requested_end.strip().casefold())
        return (start, end) if start and end else None
    for start_candidate, end_candidate in EFFECTIVE_DATE_COLUMN_PAIRS:
        start = index.get(start_candidate.casefold())
        end = index.get(end_candidate.casefold())
        if start and end:
            return start, end
    return None


def _profile_updated_at(frame: pd.DataFrame) -> dict[str, Any]:
    column = _resolve_named_column(frame.columns.tolist(), "updated_at", ())
    if column is None:
        return {"column": None, "unique_non_null_values": 0, "values": []}
    values = (
        pd.to_datetime(frame[column], errors="coerce", utc=True)
        .dropna()
        .drop_duplicates()
        .sort_values()
    )
    return {
        "column": column,
        "unique_non_null_values": int(len(values)),
        "values": [value.isoformat().replace("+00:00", "Z") for value in values.tolist()],
        "authoritative_effective_date": False,
    }


def _canonical_mapping_sha256(frame: pd.DataFrame) -> str | None:
    if frame.empty:
        return None
    return _sha256_lines(
        _json_line(
            {
                "event_id": str(row.event_id),
                "identifier8": str(row.identifier8),
            }
        )
        for row in frame.sort_values("event_id", kind="mergesort").itertuples(index=False)
    )


def inspect_identifier_source(
    source_path: Path,
    events: pd.DataFrame,
    *,
    identifier_column: str | None = None,
    effective_start_column: str | None = None,
    effective_end_column: str | None = None,
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "path": _path_text(source_path),
        "exists": source_path.is_file(),
        "strict_pit_identifier_authority": False,
    }
    if not source_path.is_file():
        return {
            **base,
            "status": STATUS_BLOCKED_SOURCE_ABSENT,
            "reason_codes": ["identifier_source_file_missing"],
            "sha256": None,
            "row_count": 0,
            "columns": [],
            "effective_date_columns": None,
            "updated_at_profile": {
                "column": None,
                "unique_non_null_values": 0,
                "values": [],
            },
        }

    frame, source_sha256 = _read_parquet_with_stable_sha256(
        source_path, label="identifier_source"
    )
    columns = [str(column) for column in frame.columns]
    updated_at_profile = _profile_updated_at(frame)
    requested = (
        identifier_column,
        effective_start_column,
        effective_end_column,
    )
    if any(value is not None for value in requested) and not all(
        value is not None and bool(value.strip()) for value in requested
    ):
        raise M7F5ID0InputError(
            "identifier_start_and_end_columns_must_be_non_empty_and_supplied_together"
        )
    identifier_column = identifier_column.strip() if identifier_column else None
    effective_start_column = (
        effective_start_column.strip() if effective_start_column else None
    )
    effective_end_column = (
        effective_end_column.strip() if effective_end_column else None
    )

    detected_pair = _resolve_effective_pair(
        columns, requested_start=None, requested_end=None
    )
    explicitly_bound = all(value is not None for value in requested)
    pair = (
        _resolve_effective_pair(
            columns,
            requested_start=effective_start_column,
            requested_end=effective_end_column,
        )
        if explicitly_bound
        else None
    )
    identifier = _resolve_named_column(
        columns,
        identifier_column if explicitly_bound else None,
        () if explicitly_bound else IDENTIFIER_COLUMN_CANDIDATES,
    )
    gvkey_column = _resolve_named_column(columns, "gvkey", ())

    source_report: dict[str, Any] = {
        **base,
        "sha256": source_sha256,
        "row_count": int(len(frame)),
        "columns": sorted(columns),
        "identifier_column": identifier,
        "gvkey_column": gvkey_column,
        "effective_date_columns": (
            {"start": pair[0], "end": pair[1]} if pair is not None else None
        ),
        "detected_unbound_effective_date_columns": (
            {"start": detected_pair[0], "end": detected_pair[1]}
            if detected_pair is not None and not explicitly_bound
            else None
        ),
        "effective_date_semantics_explicitly_bound": explicitly_bound,
        "updated_at_profile": updated_at_profile,
    }

    if not explicitly_bound:
        if detected_pair is not None:
            return {
                **source_report,
                "status": STATUS_BLOCKED_SCHEMA,
                "reason_codes": [
                    "identifier_validity_columns_must_be_explicitly_bound"
                ],
                "coverage": None,
            }
        return {
            **source_report,
            "status": STATUS_BLOCKED_SOURCE_ABSENT,
            "reason_codes": [
                "effective_date_intervals_absent",
                "updated_at_is_load_timestamp_not_effective_date",
            ],
            "coverage": None,
        }
    if pair is None or gvkey_column is None or identifier is None:
        reasons = []
        if pair is None:
            reasons.append("requested_effective_date_column_missing")
        if gvkey_column is None:
            reasons.append("gvkey_column_missing")
        if identifier is None:
            reasons.append("requested_identifier_column_missing")
        return {
            **source_report,
            "status": STATUS_BLOCKED_SCHEMA,
            "reason_codes": reasons,
            "coverage": None,
        }

    start_column, end_column = pair
    normalized = pd.DataFrame(
        {
            "gvkey": _normalize_gvkey(frame[gvkey_column]),
            "identifier8": _normalize_identifier8(
                frame[identifier], source_column=identifier
            ),
            "effective_start": _normalize_timestamp_series(frame[start_column]),
            "effective_end": _normalize_timestamp_series(frame[end_column]),
            "effective_end_raw_null": frame[end_column].isna(),
        }
    )
    relevant_gvkeys = set(events["gvkey"].astype(str))
    relevant = normalized.loc[normalized["gvkey"].isin(relevant_gvkeys)].copy()
    invalid_mask = (
        relevant["gvkey"].isna()
        | relevant["gvkey"].eq("")
        | relevant["identifier8"].isna()
        | relevant["effective_start"].isna()
        | (
            relevant["effective_end"].isna()
            & ~relevant["effective_end_raw_null"]
        )
        | (
            relevant["effective_end"].notna()
            & relevant["effective_end"].lt(relevant["effective_start"])
        )
    )
    invalid_relevant_rows = int(invalid_mask.sum())
    valid_intervals = relevant.loc[~invalid_mask].copy()

    if invalid_relevant_rows:
        return {
            **source_report,
            "status": STATUS_BLOCKED_INTERVALS,
            "reason_codes": ["invalid_relevant_identifier_intervals"],
            "relevant_source_rows": int(len(relevant)),
            "invalid_relevant_rows": invalid_relevant_rows,
            "coverage": None,
        }

    joined = events.loc[:, ["event_id", "gvkey", "rdq"]].merge(
        valid_intervals,
        on="gvkey",
        how="left",
        sort=False,
    )
    active_mask = (
        joined["identifier8"].notna()
        & joined["effective_start"].notna()
        & joined["effective_start"].le(joined["rdq"])
        & (joined["effective_end"].isna() | joined["effective_end"].ge(joined["rdq"]))
    )
    active = joined.loc[active_mask, ["event_id", "identifier8"]].copy()
    grouped = active.groupby("event_id", sort=True).agg(
        active_rows=("identifier8", "size"),
        distinct_identifiers=("identifier8", "nunique"),
        identifier8=("identifier8", "first"),
    )
    coverage = events.loc[:, ["event_id"]].merge(
        grouped,
        left_on="event_id",
        right_index=True,
        how="left",
        sort=False,
    )
    coverage["active_rows"] = coverage["active_rows"].fillna(0).astype(int)
    coverage["distinct_identifiers"] = (
        coverage["distinct_identifiers"].fillna(0).astype(int)
    )
    missing_events = int(coverage["distinct_identifiers"].eq(0).sum())
    overlapping_events = int(coverage["active_rows"].gt(1).sum())
    ambiguous_events = int(coverage["distinct_identifiers"].gt(1).sum())
    uniquely_covered_events = int(
        (
            coverage["active_rows"].eq(1)
            & coverage["distinct_identifiers"].eq(1)
        ).sum()
    )
    mapping = coverage.loc[
        coverage["active_rows"].eq(1)
        & coverage["distinct_identifiers"].eq(1),
        ["event_id", "identifier8"],
    ].copy()
    coverage_report = {
        "total_pre_identity_events": int(len(events)),
        "uniquely_covered_events": uniquely_covered_events,
        "missing_events": missing_events,
        "overlapping_interval_events": overlapping_events,
        "ambiguous_identifier_events": ambiguous_events,
        "canonical_event_identifier_mapping_sha256": _canonical_mapping_sha256(mapping),
    }

    reasons = []
    if missing_events:
        reasons.append("one_or_more_events_have_no_effective_identifier")
    if overlapping_events or ambiguous_events:
        reasons.append("one_or_more_events_have_multiple_active_identifier_rows")

    if overlapping_events or ambiguous_events:
        status = STATUS_BLOCKED_AMBIGUITY
    elif missing_events:
        status = STATUS_BLOCKED_COVERAGE
    else:
        status = STATUS_PASS

    return {
        **source_report,
        "status": status,
        "reason_codes": reasons,
        "relevant_source_rows": int(len(relevant)),
        "invalid_relevant_rows": 0,
        "coverage": coverage_report,
        "strict_pit_identifier_authority": status == STATUS_PASS,
    }


def evaluate_authority(
    *,
    d1_path: Path,
    identifier_source_path: Path,
    identifier_column: str | None = None,
    effective_start_column: str | None = None,
    effective_end_column: str | None = None,
    expected_d1_sha256: str = LOCKED_D1_SHA256,
    expected_event_count: int = LOCKED_PRE_IDENTITY_EVENT_COUNT,
    expected_event_set_sha256: str = LOCKED_PRE_IDENTITY_EVENT_SET_SHA256,
    expected_canonical_rows_sha256: str = LOCKED_PRE_IDENTITY_CANONICAL_ROWS_SHA256,
) -> dict[str, Any]:
    events, d1_report = inspect_d1_lock(
        d1_path,
        expected_sha256=expected_d1_sha256,
        expected_event_count=expected_event_count,
        expected_event_set_sha256=expected_event_set_sha256,
        expected_canonical_rows_sha256=expected_canonical_rows_sha256,
    )
    if not d1_report["verified"]:
        source_report: dict[str, Any] = {
            "path": _path_text(identifier_source_path),
            "evaluation_skipped": True,
            "reason": "d1_lock_failed",
            "strict_pit_identifier_authority": False,
        }
        status = STATUS_BLOCKED_D1_LOCK
        reason_codes = list(d1_report["mismatches"])
    else:
        source_report = inspect_identifier_source(
            identifier_source_path,
            events,
            identifier_column=identifier_column,
            effective_start_column=effective_start_column,
            effective_end_column=effective_end_column,
        )
        status = str(source_report["status"])
        reason_codes = list(source_report.get("reason_codes", []))

    return {
        "schema_version": SCHEMA_VERSION,
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "mode": "EXECUTION_PACKET",
        "status": status,
        "reason_codes": reason_codes,
        "strict_pit_identifier_authority": status == STATUS_PASS,
        "d1_pre_identity_lock": d1_report,
        "dated_identifier_source": source_report,
        "operational_authority": {
            "historical_identifier_acquisition_authorized": False,
            "provider_access_authorized": False,
            "mapping_artifact_generation_authorized": False,
            "portfolio_or_curve_execution_authorized": False,
            "readiness_promotion_authorized": False,
        },
        "next_decision": (
            "AUTHORIZE_HISTORICAL_IDENTIFIER_ACQUISITION_OR_TERMINATE_PEAD_STRICT_PIT"
            if status == STATUS_BLOCKED_SOURCE_ABSENT
            else "HOLD_UNTIL_SEPARATELY_AUTHORIZED_NEXT_SCOPE"
        ),
        "forbidden_scope": [
            "v8_or_portfolio_imports",
            "provider_or_wrds_access",
            "historical_identifier_acquisition",
            "identifier_mapping_artifact_output",
            "curve_or_return_rerun",
            "strategy_or_ui_work",
            "readiness_alpha_or_tradability_promotion",
            "remote_push_merge_or_publication",
        ],
    }


def _serialize_evidence(evidence: Mapping[str, Any]) -> str:
    return json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        tmp_path.replace(path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def _paths_alias(first: Path, second: Path) -> bool:
    if first.resolve(strict=False) == second.resolve(strict=False):
        return True
    if first.exists() and second.exists():
        try:
            return os.path.samefile(first, second)
        except OSError:
            return False
    return False


def _validate_output_path(output: Path | None, inputs: Sequence[Path]) -> None:
    if output is None:
        return
    for input_path in inputs:
        if _paths_alias(output, input_path):
            raise M7F5ID0InputError(f"output_path_aliases_input:{input_path}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate dated Compustat identifier authority for locked 2019 D1 events."
    )
    parser.add_argument("--d1", type=Path, default=DEFAULT_D1_PATH)
    parser.add_argument(
        "--identifier-source", type=Path, default=DEFAULT_IDENTIFIER_SOURCE_PATH
    )
    parser.add_argument("--identifier-column")
    parser.add_argument("--effective-start-column")
    parser.add_argument("--effective-end-column")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        _validate_output_path(
            args.output, (args.d1, args.identifier_source)
        )
        evidence = evaluate_authority(
            d1_path=args.d1,
            identifier_source_path=args.identifier_source,
            identifier_column=args.identifier_column,
            effective_start_column=args.effective_start_column,
            effective_end_column=args.effective_end_column,
        )
        payload = _serialize_evidence(evidence)
        if args.output is not None:
            _atomic_write_text(args.output, payload)
        sys.stdout.write(payload)
        return 0
    except M7F5ID0InputError as exc:
        print(f"M7F5_ID0_INPUT_ERROR:{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"M7F5_ID0_OUTPUT_ERROR:{exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
