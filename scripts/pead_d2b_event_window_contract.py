"""Build the D2B fixed-security PEAD event-window handoff contract.

The builder validates the canonical D1 and D2A manifest pointers before
reading either Parquet artifact.  For each valid D1 event it selects at most
one D2A security from the twenty explicit market sessions strictly before the
event date, then keeps that security fixed across a +1..+60 session skeleton.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent.parent
D1_MANIFEST_PATH = (
    ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet.manifest.json"
)
D2A_MANIFEST_PATH = (
    ROOT / "data" / "processed" / "pead_d2_daily_returns_sample.parquet.manifest.json"
)
D2A_FULL_MANIFEST_PATH = (
    ROOT / "data" / "processed" / "pead_d2_daily_returns.parquet.manifest.json"
)
OUT_SAMPLE_PATH = (
    ROOT / "data" / "processed" / "pead_d2b_event_windows_sample.parquet"
)
OUT_FULL_PATH = ROOT / "data" / "processed" / "pead_d2b_event_windows.parquet"

SAMPLE_N_GVKEYS = 500
LOOKBACK_SESSIONS = 20
MIN_LIQUIDITY_OBSERVATIONS = 15
WINDOW_SESSIONS = 60
HANDOFF_VALIDATION_CHUNK_ROWS = 100_000
FULL_BUILD_MEMORY_LIMIT = "512MB"
FULL_BUILD_ROW_GROUP_SIZE = 100_000
EVENT_ID_PREFIX = "PEAD"

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
D2A_COLUMNS = [
    "gvkey",
    "iid",
    "security_id",
    "date",
    "total_return",
    "return_type",
    "dollar_volume",
    "data_source",
    "tr_level",
    "price_level",
    "guardrail_reason",
]
OUTPUT_COLUMNS = [
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

_TIMEZONE_TOKEN_RE = re.compile(r"(?:z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)


@dataclass(frozen=True)
class InputArtifact:
    label: str
    manifest_path: Path
    parquet_path: Path
    manifest_sha256: str
    parquet_sha256: str
    row_count: int
    columns: tuple[str, ...]

    def manifest_record(self) -> dict[str, Any]:
        return {
            "manifest_path": _display_path(self.manifest_path),
            "manifest_sha256": self.manifest_sha256,
            "parquet_path": _display_path(self.parquet_path),
            "parquet_sha256": self.parquet_sha256,
            "rows": self.row_count,
            "schema": list(self.columns),
        }


@dataclass(frozen=True)
class InputSnapshot:
    """Validated immutable bytes used for both schema inspection and loading."""

    artifact: InputArtifact
    parquet_bytes: bytes


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _read_manifest(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} manifest is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} manifest must contain a JSON object")
    return value


def _read_manifest_snapshot(path: Path, label: str) -> tuple[dict[str, Any], str]:
    """Parse and hash one opened manifest byte snapshot."""
    try:
        manifest_bytes = path.read_bytes()
    except FileNotFoundError:
        raise
    try:
        value = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} manifest is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} manifest must contain a JSON object")
    return value, hashlib.sha256(manifest_bytes).hexdigest()


def _capture_input_snapshot(
    manifest_path: Path,
    expected_columns: list[str],
    label: str,
) -> InputSnapshot:
    """Bind manifest, hash, Arrow schema, and later pandas load to fixed bytes."""
    manifest_path = Path(manifest_path).resolve()
    manifest, manifest_sha256 = _read_manifest_snapshot(manifest_path, label)
    required = {"parquet_file", "sha256", "row_count", "columns"}
    missing = sorted(required.difference(manifest))
    if missing:
        raise ValueError(f"{label} manifest is missing required fields: {missing}")

    parquet_name = manifest["parquet_file"]
    if not isinstance(parquet_name, str) or not parquet_name.strip():
        raise ValueError(f"{label} manifest parquet_file must be a non-empty string")
    if Path(parquet_name).name != parquet_name or Path(parquet_name).suffix.lower() != ".parquet":
        raise ValueError(f"{label} manifest parquet_file must be a local .parquet filename")
    parquet_path = (manifest_path.parent / parquet_name).resolve()
    if parquet_path.parent != manifest_path.parent:
        raise ValueError(f"{label} manifest parquet_file escapes its manifest directory")
    try:
        parquet_bytes = parquet_path.read_bytes()
    except FileNotFoundError:
        raise

    manifest_columns = manifest["columns"]
    if manifest_columns != expected_columns:
        raise ValueError(
            f"{label} manifest schema drift: expected {expected_columns}, got {manifest_columns}"
        )
    parquet = pq.ParquetFile(io.BytesIO(parquet_bytes))
    actual_columns = parquet.schema_arrow.names
    if actual_columns != expected_columns:
        raise ValueError(
            f"{label} Parquet schema drift: expected {expected_columns}, got {actual_columns}"
        )
    metadata_rows = int(parquet.metadata.num_rows)
    try:
        manifest_rows = int(manifest["row_count"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} manifest row_count must be an integer") from exc
    if manifest_rows != metadata_rows:
        raise ValueError(
            f"{label} row-count drift: manifest={manifest_rows}, parquet={metadata_rows}"
        )

    expected_hash = manifest["sha256"]
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError(f"{label} manifest sha256 must be 64 lowercase hex characters")
    actual_hash = hashlib.sha256(parquet_bytes).hexdigest()
    if actual_hash != expected_hash:
        raise ValueError(
            f"{label} Parquet hash drift: expected {expected_hash}, got {actual_hash}"
        )
    return InputSnapshot(
        artifact=InputArtifact(
            label=label,
            manifest_path=manifest_path,
            parquet_path=parquet_path,
            manifest_sha256=manifest_sha256,
            parquet_sha256=actual_hash,
            row_count=metadata_rows,
            columns=tuple(actual_columns),
        ),
        parquet_bytes=parquet_bytes,
    )


def _resolve_input_artifact_bounded(
    manifest_path: Path,
    expected_columns: list[str],
    label: str,
) -> InputArtifact:
    """Validate one immutable artifact without materializing its Parquet bytes."""
    manifest_path = Path(manifest_path).resolve()
    manifest, manifest_sha256 = _read_manifest_snapshot(manifest_path, label)
    required = {"parquet_file", "sha256", "row_count", "columns"}
    missing = sorted(required.difference(manifest))
    if missing:
        raise ValueError(f"{label} manifest is missing required fields: {missing}")
    parquet_name = manifest["parquet_file"]
    if (
        not isinstance(parquet_name, str)
        or not parquet_name.strip()
        or Path(parquet_name).name != parquet_name
        or Path(parquet_name).suffix.lower() != ".parquet"
    ):
        raise ValueError(f"{label} manifest parquet_file must be a local .parquet filename")
    parquet_path = (manifest_path.parent / parquet_name).resolve()
    if parquet_path.parent != manifest_path.parent:
        raise ValueError(f"{label} manifest parquet_file escapes its manifest directory")
    if not parquet_path.is_file():
        raise FileNotFoundError(parquet_path)
    if manifest["columns"] != expected_columns:
        raise ValueError(
            f"{label} manifest schema drift: expected {expected_columns}, "
            f"got {manifest['columns']}"
        )
    parquet = pq.ParquetFile(parquet_path)
    actual_columns = parquet.schema_arrow.names
    if actual_columns != expected_columns:
        raise ValueError(
            f"{label} Parquet schema drift: expected {expected_columns}, "
            f"got {actual_columns}"
        )
    metadata_rows = int(parquet.metadata.num_rows)
    try:
        manifest_rows = int(manifest["row_count"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} manifest row_count must be an integer") from exc
    if manifest_rows != metadata_rows:
        raise ValueError(
            f"{label} row-count drift: manifest={manifest_rows}, parquet={metadata_rows}"
        )
    expected_hash = manifest["sha256"]
    if not isinstance(expected_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_hash
    ):
        raise ValueError(f"{label} manifest sha256 must be 64 lowercase hex characters")
    actual_hash = _sha256_file(parquet_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"{label} Parquet hash drift: expected {expected_hash}, got {actual_hash}"
        )
    return InputArtifact(
        label=label,
        manifest_path=manifest_path,
        parquet_path=parquet_path,
        manifest_sha256=manifest_sha256,
        parquet_sha256=actual_hash,
        row_count=metadata_rows,
        columns=tuple(actual_columns),
    )


def resolve_input_artifact(
    manifest_path: Path,
    expected_columns: list[str],
    label: str,
) -> InputArtifact:
    """Resolve and hash-validate one manifest-governed Parquet input."""
    return _capture_input_snapshot(manifest_path, expected_columns, label).artifact


def load_validated_inputs(
    d1_manifest_path: Path = D1_MANIFEST_PATH,
    d2a_manifest_path: Path = D2A_MANIFEST_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, dict[str, Any]]]:
    """Validate both inputs, then load from the same immutable byte snapshots."""
    d1_snapshot = _capture_input_snapshot(d1_manifest_path, D1_COLUMNS, "D1")
    d2a_snapshot = _capture_input_snapshot(d2a_manifest_path, D2A_COLUMNS, "D2A")
    frames = (
        pd.read_parquet(io.BytesIO(d1_snapshot.parquet_bytes), columns=D1_COLUMNS),
        pd.read_parquet(io.BytesIO(d2a_snapshot.parquet_bytes), columns=D2A_COLUMNS),
    )
    return frames[0], frames[1], {
        "d1": d1_snapshot.artifact.manifest_record(),
        "d2a": d2a_snapshot.artifact.manifest_record(),
    }


def _read_small_artifact_in_batches(
    artifact: InputArtifact,
    columns: list[str],
) -> pd.DataFrame:
    frames = [
        batch.to_pandas()
        for batch in pq.ParquetFile(artifact.parquet_path).iter_batches(
            columns=columns,
            batch_size=HANDOFF_VALIDATION_CHUNK_ROWS,
        )
    ]
    if not frames:
        return pd.DataFrame(columns=columns)
    return pd.concat(frames, ignore_index=True, copy=False)[columns]


def _bounded_connection(temp_directory: Path) -> tuple[duckdb.DuckDBPyConnection, Path]:
    import uuid
    db_path = temp_directory / f"duckdb_temp_{uuid.uuid4().hex}.db"
    connection = duckdb.connect(str(db_path.resolve()))
    connection.execute(f"SET memory_limit = {_sql_literal(FULL_BUILD_MEMORY_LIMIT)}")
    connection.execute("SET threads = 1")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(temp_directory.resolve())}"
    )
    return connection, db_path


def _validation_connection(temp_directory: Path) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute("SET memory_limit = '8GB'")
    connection.execute("SET threads = 1")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(temp_directory.resolve())}"
    )
    return connection


def _create_normalized_d2a_view(
    connection: duckdb.DuckDBPyConnection,
    parquet_path: Path,
) -> None:
    source = f"read_parquet({_sql_literal(parquet_path.resolve())})"
    connection.execute(
        f"""
        CREATE TEMP VIEW d2a_normalized AS
        SELECT
            gvkey AS issuer_id,
            iid,
            security_id,
            date,
            total_return,
            return_type,
            dollar_volume,
            guardrail_reason
        FROM {source}
        """
    )


def _validate_normalized_d2a_view(
    connection: duckdb.DuckDBPyConnection,
) -> pd.DatetimeIndex:
    row_count = int(connection.execute("SELECT count(*) FROM d2a_normalized").fetchone()[0])
    if row_count == 0:
        raise ValueError("D2A return input is empty")
    malformed = int(
        connection.execute(
            """
            SELECT count(*) FROM d2a_normalized
            WHERE issuer_id IS NULL OR issuer_id = ''
               OR iid IS NULL OR iid = ''
               OR security_id IS NULL OR security_id = ''
               OR date IS NULL
            """
        ).fetchone()[0]
    )
    if malformed:
        raise ValueError(f"D2A contains {malformed} malformed key/date row(s)")
    identity_mismatch = int(
        connection.execute(
            """
            SELECT count(*) FROM d2a_normalized
            WHERE security_id != issuer_id || '-' || iid
            """
        ).fetchone()[0]
    )
    if identity_mismatch:
        raise ValueError("D2A security_id identity does not match '<gvkey>-<iid>'")
    identity_collision = connection.execute(
        """
        SELECT security_id
        FROM (SELECT DISTINCT issuer_id, iid, security_id FROM d2a_normalized)
        GROUP BY security_id
        HAVING count(*) > 1
        LIMIT 1
        """
    ).fetchone()
    if identity_collision is not None:
        raise ValueError("D2A security_id is not one-to-one with (issuer_id, iid)")
    if row_count > 1_000_000:
        duplicate = connection.execute(
            """
            SELECT security_id, date
            FROM d2a_normalized
            WHERE issuer_id IN (
                SELECT DISTINCT issuer_id FROM d2a_normalized LIMIT 500
            )
            GROUP BY security_id, date
            HAVING count(*) > 1
            LIMIT 1
            """
        ).fetchone()
    else:
        duplicate = connection.execute(
            """
            SELECT security_id, date
            FROM d2a_normalized
            GROUP BY security_id, date
            HAVING count(*) > 1
            LIMIT 1
            """
        ).fetchone()
    if duplicate is not None:
        raise ValueError(
            "D2A contains duplicate normalized (security_id, date) rows; "
            f"example={duplicate}"
        )
    invalid_numeric = connection.execute(
        """
        SELECT
            count(*) FILTER (WHERE isinf(total_return)),
            count(*) FILTER (WHERE isinf(dollar_volume)),
            count(*) FILTER (WHERE dollar_volume < 0),
            count(*) FILTER (WHERE return_type IS NULL OR guardrail_reason IS NULL)
        FROM d2a_normalized
        """
    ).fetchone()
    if invalid_numeric[0]:
        raise ValueError("D2A.total_return contains infinite value(s)")
    if invalid_numeric[1]:
        raise ValueError("D2A.dollar_volume contains infinite value(s)")
    if invalid_numeric[2]:
        raise ValueError("D2A.dollar_volume contains negative value(s)")
    if invalid_numeric[3]:
        raise ValueError("D2A return_type and guardrail_reason must not be null")
    dates = connection.execute(
        "SELECT DISTINCT date FROM d2a_normalized ORDER BY date"
    ).fetchall()
    return pd.DatetimeIndex([value[0] for value in dates])


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{label} must be a pandas DataFrame")
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _normalise_identifier(values: pd.Series, label: str) -> pd.Series:
    out = values.astype("string").str.strip()
    invalid = out.isna() | out.eq("")
    if invalid.any():
        raise ValueError(f"{label} contains {int(invalid.sum())} malformed key(s)")
    return out


def _normalise_dates(values: pd.Series, label: str) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values):
        raise ValueError(f"{label} must be date-like, not numeric")
    raw = pd.Series(values, copy=False)
    nonnull = raw.dropna()
    numeric_objects = nonnull.map(
        lambda value: isinstance(value, (int, float, np.integer, np.floating))
        and not isinstance(value, bool)
    )
    timezone_objects = nonnull.map(
        lambda value: isinstance(value, pd.Timestamp) and value.tzinfo is not None
    )
    timezone_strings = nonnull.astype(str).str.strip().map(
        lambda value: bool(_TIMEZONE_TOKEN_RE.search(value))
    )
    if bool(numeric_objects.any()) or bool(timezone_objects.any()) or bool(timezone_strings.any()):
        raise ValueError(f"{label} contains malformed date value(s)")
    parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    if parsed.isna().any():
        raise ValueError(f"{label} contains {int(parsed.isna().sum())} malformed date(s)")
    normalised = parsed.dt.normalize()
    if not parsed.equals(normalised):
        raise ValueError(f"{label} must contain date-only values")
    return normalised


def _strict_boolean(values: pd.Series, label: str) -> pd.Series:
    if not (pd.api.types.is_bool_dtype(values) or str(values.dtype) == "boolean"):
        raise ValueError(f"{label} must contain strict boolean values")
    if values.isna().any():
        raise ValueError(f"{label} must not contain null values")
    return values.astype(bool)


def _normalise_d1_events(d1: pd.DataFrame) -> pd.DataFrame:
    _require_columns(
        d1,
        {"gvkey", "rdq", "valid_sue", "sue_price_scaled", "sue_price_scaled_clipped"},
        "D1",
    )
    work = d1.copy()
    work["valid_sue"] = _strict_boolean(work["valid_sue"], "D1.valid_sue")
    work = work.loc[work["valid_sue"]].copy()
    if work.empty:
        raise ValueError("D1 contains no valid_sue=True events")
    work["issuer_id"] = _normalise_identifier(work["gvkey"], "D1.gvkey")
    work["event_date"] = _normalise_dates(work["rdq"], "D1.rdq")
    work["sue"] = pd.to_numeric(work["sue_price_scaled"], errors="coerce")
    work["sue_price_scaled_clipped"] = pd.to_numeric(
        work["sue_price_scaled_clipped"], errors="coerce"
    )
    invalid_sue = ~np.isfinite(work["sue"]) | ~np.isfinite(work["sue_price_scaled_clipped"])
    if invalid_sue.any():
        raise ValueError(f"D1 valid events contain {int(invalid_sue.sum())} non-finite SUE value(s)")
    duplicate = work.duplicated(["issuer_id", "event_date"], keep=False)
    if duplicate.any():
        examples = work.loc[duplicate, ["issuer_id", "event_date"]].head(3).to_dict("records")
        raise ValueError(f"D1 contains duplicate (issuer_id, event_date) events; examples={examples}")
    work["event_id"] = (
        EVENT_ID_PREFIX
        + ":"
        + work["issuer_id"]
        + ":"
        + work["event_date"].dt.strftime("%Y-%m-%d")
    )
    if work["event_id"].duplicated().any():
        raise ValueError("deterministic event_id collision")
    return work[
        ["event_id", "issuer_id", "event_date", "sue", "sue_price_scaled_clipped"]
    ].sort_values(["issuer_id", "event_date"], kind="mergesort").reset_index(drop=True)


def _normalise_d2a(d2a: pd.DataFrame) -> pd.DataFrame:
    _require_columns(d2a, set(D2A_COLUMNS), "D2A")
    if d2a.empty:
        raise ValueError("D2A return input is empty")
    work = d2a.copy()
    work["issuer_id"] = _normalise_identifier(work["gvkey"], "D2A.gvkey")
    work["iid"] = _normalise_identifier(work["iid"], "D2A.iid")
    work["security_id"] = _normalise_identifier(work["security_id"], "D2A.security_id")
    expected_security_id = work["issuer_id"] + "-" + work["iid"]
    if not work["security_id"].equals(expected_security_id):
        raise ValueError("D2A security_id identity does not match '<gvkey>-<iid>'")
    identity_count = len(work[["issuer_id", "iid"]].drop_duplicates())
    if int(work["security_id"].nunique()) != identity_count:
        raise ValueError("D2A security_id is not one-to-one with (issuer_id, iid)")
    work["date"] = _normalise_dates(work["date"], "D2A.date")
    duplicate = work.duplicated(["security_id", "date"], keep=False)
    if duplicate.any():
        examples = work.loc[duplicate, ["security_id", "date"]].head(3).to_dict("records")
        raise ValueError(f"D2A contains duplicate (security_id, date) rows; examples={examples}")

    for column in ("total_return", "dollar_volume"):
        work[column] = pd.to_numeric(work[column], errors="coerce")
        if np.isinf(work[column]).any():
            raise ValueError(f"D2A.{column} contains infinite value(s)")
    if work["dollar_volume"].dropna().lt(0.0).any():
        raise ValueError("D2A.dollar_volume contains negative value(s)")
    work["return_type"] = work["return_type"].astype("string")
    work["guardrail_reason"] = work["guardrail_reason"].astype("string")
    if work["return_type"].isna().any() or work["guardrail_reason"].isna().any():
        raise ValueError("D2A return_type and guardrail_reason must not be null")
    work.sort_values(["issuer_id", "security_id", "date"], kind="mergesort", inplace=True)
    work.reset_index(drop=True, inplace=True)
    return work


def _prepare_selected_strategy_returns(
    d2a: pd.DataFrame,
    selected_security_ids: set[str],
) -> tuple[pd.DataFrame, pd.DatetimeIndex]:
    """Validate all D2A rows in bounded chunks and retain only selected returns."""
    _require_columns(d2a, set(D2A_COLUMNS), "D2A")
    if d2a.empty:
        raise ValueError("D2A return input is empty")

    selected_categories = sorted(selected_security_ids)
    security_dtype = pd.CategoricalDtype(categories=selected_categories)
    selected_frames: list[pd.DataFrame] = []
    session_parts: list[pd.DatetimeIndex] = []
    identity_pairs: set[tuple[str, str]] = set()
    identity_security_ids: set[str] = set()
    key_store = duckdb.connect()
    try:
        key_store.execute("SET memory_limit = '128MB'")
        key_store.execute("SET threads = 1")
        key_store.execute("SET preserve_insertion_order = false")
        key_store.execute(
            """
            CREATE TEMP TABLE normalized_keys (
                security_id VARCHAR NOT NULL,
                date DATE NOT NULL,
                PRIMARY KEY (security_id, date)
            )
            """
        )
        for start in range(0, len(d2a), HANDOFF_VALIDATION_CHUNK_ROWS):
            chunk = d2a.iloc[start : start + HANDOFF_VALIDATION_CHUNK_ROWS]
            issuer_id = _normalise_identifier(chunk["gvkey"], "D2A.gvkey")
            iid = _normalise_identifier(chunk["iid"], "D2A.iid")
            security_id = _normalise_identifier(chunk["security_id"], "D2A.security_id")
            expected_security_id = issuer_id + "-" + iid
            if not security_id.equals(expected_security_id):
                raise ValueError("D2A security_id identity does not match '<gvkey>-<iid>'")

            identities = pd.DataFrame(
                {"issuer_id": issuer_id, "iid": iid, "security_id": security_id}
            ).drop_duplicates()
            identity_pairs.update(zip(identities["issuer_id"], identities["iid"], strict=True))
            identity_security_ids.update(identities["security_id"])

            dates = _normalise_dates(chunk["date"], "D2A.date")
            session_parts.append(pd.DatetimeIndex(dates.unique()))
            normalized_keys = pd.DataFrame(
                {
                    "security_id": security_id.to_numpy(),
                    "date": dates.to_numpy(),
                }
            )
            key_store.register("normalized_key_chunk", normalized_keys)
            try:
                try:
                    key_store.execute(
                        """
                        INSERT INTO normalized_keys
                        SELECT security_id, date
                        FROM normalized_key_chunk
                        """
                    )
                except duckdb.ConstraintException as exc:
                    raise ValueError(
                        "D2A contains duplicate normalized (security_id, date) rows"
                    ) from exc
            finally:
                key_store.unregister("normalized_key_chunk")

            total_return = pd.to_numeric(chunk["total_return"], errors="coerce")
            dollar_volume = pd.to_numeric(chunk["dollar_volume"], errors="coerce")
            if np.isinf(total_return).any():
                raise ValueError("D2A.total_return contains infinite value(s)")
            if np.isinf(dollar_volume).any():
                raise ValueError("D2A.dollar_volume contains infinite value(s)")
            if dollar_volume.dropna().lt(0.0).any():
                raise ValueError("D2A.dollar_volume contains negative value(s)")
            if chunk["return_type"].isna().any() or chunk["guardrail_reason"].isna().any():
                raise ValueError("D2A return_type and guardrail_reason must not be null")

            selected = security_id.isin(selected_security_ids)
            if selected.any():
                selected_frames.append(
                    pd.DataFrame(
                        {
                            "security_id": pd.Categorical(
                                security_id.loc[selected], dtype=security_dtype
                            ),
                            "date": dates.loc[selected].to_numpy(),
                            "total_return": total_return.loc[selected].to_numpy(),
                        }
                    )
                )

    finally:
        key_store.close()

    if len(identity_pairs) != len(identity_security_ids):
        raise ValueError("D2A security_id is not one-to-one with (issuer_id, iid)")

    sessions = pd.DatetimeIndex(
        np.concatenate([part.to_numpy() for part in session_parts])
    ).drop_duplicates().sort_values()
    if selected_frames:
        canonical_returns = pd.concat(selected_frames, ignore_index=True, copy=False)
    else:
        canonical_returns = pd.DataFrame(
            {
                "security_id": pd.Series([], dtype=security_dtype),
                "date": pd.Series([], dtype="datetime64[ns]"),
                "total_return": pd.Series([], dtype="float64"),
            }
        )
    if canonical_returns.duplicated(["security_id", "date"]).any():
        raise ValueError("canonical strategy returns must be unique by security_id,date")
    canonical_returns.sort_values(["security_id", "date"], kind="mergesort", inplace=True)
    canonical_returns.reset_index(drop=True, inplace=True)
    return canonical_returns, sessions


def market_session_spine(
    d2a: pd.DataFrame,
    authoritative_sessions: pd.DatetimeIndex | None = None,
) -> pd.DatetimeIndex:
    d2a_dates = pd.DatetimeIndex(
        d2a["date"].drop_duplicates().sort_values(kind="mergesort")
    )
    if authoritative_sessions is None:
        sessions = d2a_dates
    else:
        reference = pd.DatetimeIndex(pd.to_datetime(authoritative_sessions))
        if reference.empty or not reference.is_monotonic_increasing or reference.has_duplicates:
            raise ValueError(
                "authoritative market-session spine must be non-empty, sorted, and unique"
            )
        if not reference.normalize().equals(reference):
            raise ValueError(
                "authoritative market-session spine must contain date-only values"
            )
        if reference.min() > d2a_dates.min() or reference.max() < d2a_dates.max():
            raise ValueError(
                "authoritative market-session spine does not cover the D2A date range"
            )
        sessions = reference[
            (reference >= d2a_dates.min()) & (reference <= d2a_dates.max())
        ]
    if sessions.empty or not sessions.is_monotonic_increasing or sessions.has_duplicates:
        raise ValueError("D2A market-session spine must be non-empty, sorted, and unique")
    return sessions


def _select_event_securities(
    events: pd.DataFrame,
    d2a: pd.DataFrame,
    sessions: pd.DatetimeIndex,
) -> pd.DataFrame:
    issuer_frames = {
        str(issuer): frame
        for issuer, frame in d2a.groupby("issuer_id", sort=False, observed=True)
    }
    selections: list[dict[str, Any]] = []
    for event in events.itertuples(index=False):
        event_date = pd.Timestamp(event.event_date)
        cutoff_position = int(sessions.searchsorted(event_date, side="left"))
        trailing = sessions[max(0, cutoff_position - LOOKBACK_SESSIONS) : cutoff_position]
        cutoff_date = trailing[-1] if len(trailing) else pd.NaT
        issuer_rows = issuer_frames.get(str(event.issuer_id))
        lookback = (
            issuer_rows.loc[issuer_rows["date"].isin(trailing)]
            if issuer_rows is not None and len(trailing)
            else d2a.iloc[0:0]
        )
        candidate_count = int(lookback["security_id"].nunique())
        eligible = pd.DataFrame()
        if not lookback.empty:
            stats = (
                lookback.assign(_finite_volume=lookback["dollar_volume"].where(np.isfinite(lookback["dollar_volume"])))
                .groupby(["security_id", "iid"], as_index=False, sort=False, observed=True)[
                    "_finite_volume"
                ]
                .agg(liquidity_observations="count", trailing_mean_dollar_volume="mean")
            )
            eligible = stats.loc[
                stats["liquidity_observations"].ge(MIN_LIQUIDITY_OBSERVATIONS)
            ].copy()
            if not eligible.empty:
                eligible["_iid_sort"] = eligible["iid"].astype("string").str.casefold()
                eligible = eligible.sort_values(
                    [
                        "trailing_mean_dollar_volume",
                        "liquidity_observations",
                        "_iid_sort",
                        "security_id",
                    ],
                    ascending=[False, False, True, True],
                    kind="mergesort",
                )
        if eligible.empty:
            selected_security = pd.NA
            selected_iid = pd.NA
            observations = pd.NA
            mean_volume = np.nan
            status = "no_eligible_candidate"
        else:
            winner = eligible.iloc[0]
            selected_security = str(winner["security_id"])
            selected_iid = str(winner["iid"])
            observations = int(winner["liquidity_observations"])
            mean_volume = float(winner["trailing_mean_dollar_volume"])
            status = "selected"
        selections.append(
            {
                "event_id": event.event_id,
                "security_id": selected_security,
                "iid": selected_iid,
                "selection_status": status,
                "selection_cutoff_date": cutoff_date,
                "liquidity_observations": observations,
                "trailing_mean_dollar_volume": mean_volume,
                "candidate_security_count": candidate_count,
            }
        )
    selected = pd.DataFrame(selections)
    selected["liquidity_observations"] = selected["liquidity_observations"].astype("Int64")
    selected["candidate_security_count"] = selected["candidate_security_count"].astype("int64")
    return selected


def _coverage_reason(frame: pd.DataFrame) -> str:
    if frame["security_id"].isna().all():
        return "no_eligible_security"
    if int(frame["return_date"].notna().sum()) != WINDOW_SESSIONS:
        return "insufficient_market_sessions"
    missing_rows = bool((~frame["return_row_present"]).any())
    nonfinite = bool((~np.isfinite(frame["asset_return"])).any())
    if missing_rows and nonfinite:
        return "missing_or_nonfinite_asset_returns"
    if missing_rows:
        return "missing_return_rows"
    if nonfinite:
        return "nonfinite_asset_returns"
    return "complete"


def _build_event_window_contract_from_normalised(
    d1: pd.DataFrame,
    returns: pd.DataFrame,
    sessions: pd.DatetimeIndex,
) -> pd.DataFrame:
    """Build D2B after the caller has normalized D2A exactly once."""
    events = _normalise_d1_events(d1)
    issuer_universe = set(returns["issuer_id"].unique())
    events = events.loc[events["issuer_id"].isin(issuer_universe)].reset_index(drop=True)
    if events.empty:
        raise ValueError("D1 and D2A have no overlapping valid-event issuer universe")
    selections = _select_event_securities(events, returns, sessions)
    event_base = events.merge(selections, on="event_id", how="left", validate="one_to_one")

    repeated = event_base.loc[event_base.index.repeat(WINDOW_SESSIONS)].reset_index(drop=True)
    repeated["event_day"] = np.tile(
        np.arange(1, WINDOW_SESSIONS + 1, dtype=np.int64), len(event_base)
    )
    event_starts = sessions.searchsorted(event_base["event_date"], side="right")
    session_positions = np.repeat(event_starts, WINDOW_SESSIONS) + repeated["event_day"].to_numpy() - 1
    valid_positions = session_positions < len(sessions)
    return_dates = np.full(len(repeated), np.datetime64("NaT"), dtype="datetime64[ns]")
    return_dates[valid_positions] = sessions.to_numpy()[session_positions[valid_positions]]
    repeated["return_date"] = pd.to_datetime(return_dates)

    observations = returns[
        ["security_id", "date", "total_return", "return_type", "guardrail_reason"]
    ].rename(columns={"date": "return_date", "total_return": "asset_return"})
    observations["return_row_present"] = True
    output = repeated.merge(
        observations,
        on=["security_id", "return_date"],
        how="left",
        validate="many_to_one",
    )
    output["return_row_present"] = output["return_row_present"].eq(True)
    output["is_primary_security"] = output["security_id"].notna().astype(bool)

    grouped = output.groupby("event_id", sort=False, observed=True)
    selected_exists = grouped["security_id"].transform(lambda values: values.notna().all())
    dates_complete = grouped["return_date"].transform("count").eq(WINDOW_SESSIONS)
    returns_complete = grouped["asset_return"].transform(
        lambda values: int(np.isfinite(values).sum())
    ).eq(WINDOW_SESSIONS)
    output["handoff_eligible"] = (selected_exists & dates_complete & returns_complete).astype(bool)
    output["window_complete"] = output["handoff_eligible"].astype(bool)
    reasons = grouped.apply(_coverage_reason, include_groups=False)
    output["coverage_reason"] = output["event_id"].map(reasons).astype("string")
    output["selection_status"] = output["selection_status"].astype("string")
    output["security_id"] = output["security_id"].astype("string")
    output["iid"] = output["iid"].astype("string")
    output["return_type"] = output["return_type"].astype("string")
    output["guardrail_reason"] = output["guardrail_reason"].astype("string")
    output = output[OUTPUT_COLUMNS]
    _validate_output(output, sessions)
    return output


def build_event_window_contract(
    d1: pd.DataFrame,
    d2a: pd.DataFrame,
    market_sessions: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    """Create the exact long-form D2B handoff schema from in-memory inputs."""
    returns = _normalise_d2a(d2a)
    sessions = market_session_spine(returns, market_sessions)
    return _build_event_window_contract_from_normalised(d1, returns, sessions)


def _full_output_sql() -> str:
    """Return the out-of-core SQL form of the canonical D2B event algorithm."""
    return f"""
        WITH event_positions AS (
            SELECT e.*,
                coalesce(s_cutoff.session_pos + 1, 0)::BIGINT AS cutoff_pos,
                coalesce(s_start.session_pos + 1, 0)::BIGINT AS event_start_pos,
                s_cutoff.session_date AS selection_cutoff_date
            FROM events e
            ASOF LEFT JOIN market_sessions s_cutoff
              ON s_cutoff.session_date < cast(e.event_date AS DATE)
            ASOF LEFT JOIN market_sessions s_start
              ON s_start.session_date <= cast(e.event_date AS DATE)
        ), lookback AS (
            SELECT e.event_id, d.security_id, d.iid, d.dollar_volume
            FROM event_positions e
            JOIN market_sessions s
              ON s.session_pos >= greatest(0, e.cutoff_pos - {LOOKBACK_SESSIONS})
             AND s.session_pos < e.cutoff_pos
            JOIN d2a_normalized d
              ON d.issuer_id = e.issuer_id
             AND d.date = s.session_date
        ), candidate_counts AS (
            SELECT event_id, count(DISTINCT security_id)::BIGINT
                AS candidate_security_count
            FROM lookback
            GROUP BY event_id
        ), liquidity AS (
            SELECT event_id, security_id, iid,
                count(*) FILTER (WHERE isfinite(dollar_volume))::BIGINT
                    AS liquidity_observations,
                avg(dollar_volume) FILTER (WHERE isfinite(dollar_volume))
                    AS trailing_mean_dollar_volume
            FROM lookback
            GROUP BY event_id, security_id, iid
        ), ranked AS (
            SELECT *, row_number() OVER (
                PARTITION BY event_id
                ORDER BY trailing_mean_dollar_volume DESC,
                         liquidity_observations DESC,
                         lower(iid) ASC,
                         security_id ASC
            ) AS candidate_rank
            FROM liquidity
            WHERE liquidity_observations >= {MIN_LIQUIDITY_OBSERVATIONS}
        ), selected AS (
            SELECT event_id, security_id, iid, liquidity_observations,
                   trailing_mean_dollar_volume
            FROM ranked
            WHERE candidate_rank = 1
        ), event_base AS (
            SELECT e.*,
                w.security_id,
                w.iid,
                CASE WHEN w.security_id IS NULL
                    THEN 'no_eligible_candidate' ELSE 'selected' END
                    AS selection_status,
                w.liquidity_observations,
                w.trailing_mean_dollar_volume,
                coalesce(c.candidate_security_count, 0)::BIGINT
                    AS candidate_security_count
            FROM event_positions e
            LEFT JOIN selected w USING (event_id)
            LEFT JOIN candidate_counts c USING (event_id)
        ), skeleton AS (
            SELECT e.*, days.event_day::BIGINT AS event_day,
                   e.event_start_pos + days.event_day - 1 AS return_session_pos
            FROM event_base e
            CROSS JOIN range(1, {WINDOW_SESSIONS + 1}) AS days(event_day)
        ), observations AS (
            SELECT sk.*, cast(s.session_date AS TIMESTAMP) AS return_date,
                d.security_id IS NOT NULL AS return_row_present,
                d.total_return AS asset_return,
                d.return_type,
                d.guardrail_reason
            FROM skeleton sk
            LEFT JOIN market_sessions s
              ON s.session_pos = sk.return_session_pos
            LEFT JOIN d2a_normalized d
              ON d.security_id = sk.security_id
             AND d.date = s.session_date
        ), coverage AS (
            SELECT *,
                count(return_date) OVER (PARTITION BY event_id) AS return_date_count,
                count(*) FILTER (
                    WHERE coalesce(isfinite(asset_return), false)
                ) OVER (PARTITION BY event_id) AS finite_return_count,
                bool_or(NOT return_row_present) OVER (PARTITION BY event_id)
                    AS has_missing_row,
                bool_or(NOT coalesce(isfinite(asset_return), false))
                    OVER (PARTITION BY event_id) AS has_nonfinite_return
            FROM observations
        )
        SELECT
            event_id,
            issuer_id,
            cast(event_date AS TIMESTAMP) AS event_date,
            sue,
            sue_price_scaled_clipped,
            security_id,
            iid,
            security_id IS NOT NULL AS is_primary_security,
            security_id IS NOT NULL
                AND return_date_count = {WINDOW_SESSIONS}
                AND finite_return_count = {WINDOW_SESSIONS} AS handoff_eligible,
            selection_status,
            cast(selection_cutoff_date AS TIMESTAMP) AS selection_cutoff_date,
            liquidity_observations,
            trailing_mean_dollar_volume,
            candidate_security_count,
            event_day,
            return_date,
            return_row_present,
            asset_return,
            return_type,
            guardrail_reason,
            security_id IS NOT NULL
                AND return_date_count = {WINDOW_SESSIONS}
                AND finite_return_count = {WINDOW_SESSIONS} AS window_complete,
            CASE
                WHEN security_id IS NULL THEN 'no_eligible_security'
                WHEN return_date_count != {WINDOW_SESSIONS}
                    THEN 'insufficient_market_sessions'
                WHEN has_missing_row AND has_nonfinite_return
                    THEN 'missing_or_nonfinite_asset_returns'
                WHEN has_missing_row THEN 'missing_return_rows'
                WHEN has_nonfinite_return THEN 'nonfinite_asset_returns'
                ELSE 'complete'
            END AS coverage_reason
        FROM coverage
        ORDER BY issuer_id, event_date, event_day
    """


def _validate_output(output: pd.DataFrame, sessions: pd.DatetimeIndex | None = None) -> None:
    if output.empty:
        raise ValueError("D2B output is empty")
    if list(output.columns) != OUTPUT_COLUMNS:
        raise ValueError(f"D2B output schema drift: {list(output.columns)}")
    duplicate = output.duplicated(["event_id", "event_day"], keep=False)
    if duplicate.any():
        raise ValueError("D2B output contains duplicate (event_id, event_day) rows")
    counts = output.groupby("event_id", sort=False, observed=True).size()
    if not counts.eq(WINDOW_SESSIONS).all():
        raise ValueError("D2B output must contain exactly 60 rows per event")
    expected_days = list(range(1, WINDOW_SESSIONS + 1))
    if not output.groupby("event_id", sort=False, observed=True)["event_day"].apply(list).map(
        lambda values: values == expected_days
    ).all():
        raise ValueError("D2B event_day must be exactly +1..+60 per event")
    security_counts = output.groupby("event_id", sort=False, observed=True)["security_id"].nunique(
        dropna=True
    )
    if security_counts.gt(1).any():
        raise ValueError("D2B selected security switched within an event window")
    event_groups = output.groupby("event_id", sort=False, observed=True)
    for column in ("issuer_id", "event_date", "sue", "is_primary_security"):
        if event_groups[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f"D2B {column} is inconsistent within event_id")
    invalid_timing = output["return_date"].notna() & (
        output["return_date"] <= output["event_date"]
    )
    if invalid_timing.any():
        raise ValueError("D2B return_date must be strictly after event_date")
    expected_eligible = output.groupby("event_id", sort=False, observed=True).apply(
        lambda frame: bool(
            frame["security_id"].notna().all()
            and frame["return_date"].notna().sum() == WINDOW_SESSIONS
            and np.isfinite(frame["asset_return"]).sum() == WINDOW_SESSIONS
        ),
        include_groups=False,
    )
    actual_eligible = output.groupby("event_id", sort=False, observed=True)[
        "handoff_eligible"
    ].first()
    if not actual_eligible.equals(expected_eligible.astype(bool)):
        raise ValueError("D2B handoff_eligible formula validation failed")
    if not output["window_complete"].equals(output["handoff_eligible"]):
        raise ValueError("D2B window_complete must equal handoff_eligible")
    if sessions is not None:
        session_values = set(pd.DatetimeIndex(sessions))
        observed_dates = set(output["return_date"].dropna())
        if not observed_dates.issubset(session_values):
            raise ValueError(
                "D2B return_date contains dates outside the authoritative market-session spine"
            )


def prepare_strategy_handoff(
    d2b: pd.DataFrame,
    d2a: pd.DataFrame,
    market_sessions: pd.DatetimeIndex | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
    """Derive eligible events and unique canonical D2A returns for the strategy layer."""
    event_columns = [
        "event_id",
        "issuer_id",
        "security_id",
        "event_date",
        "sue",
        "is_primary_security",
    ]
    event_rows = d2b.loc[
        d2b["handoff_eligible"] & d2b["event_day"].eq(1),
        event_columns,
    ].copy()
    if event_rows["event_id"].duplicated().any():
        raise ValueError("strategy handoff event metadata is inconsistent within event_id")
    events = event_rows.reset_index(drop=True)
    selected_security_ids = set(events["security_id"].dropna())
    canonical_returns, d2a_sessions = _prepare_selected_strategy_returns(
        d2a,
        selected_security_ids,
    )
    sessions = market_session_spine(
        pd.DataFrame({"date": d2a_sessions}),
        market_sessions,
    )
    _validate_output(d2b, sessions)
    return events, canonical_returns, sessions


def build_strategy_event_windows(
    d2b: pd.DataFrame,
    d2a: pd.DataFrame,
    market_sessions: pd.DatetimeIndex | None = None,
) -> pd.DataFrame:
    """Run the strategy's sole event-window algorithm on the canonical D2B handoff."""
    from strategies.pead_event_study import build_event_windows

    events, canonical_returns, sessions = prepare_strategy_handoff(
        d2b,
        d2a,
        market_sessions,
    )
    return build_event_windows(events, canonical_returns, sessions)


def _session_spine_record(
    sessions: pd.DatetimeIndex,
    *,
    d2a_dates: pd.DatetimeIndex | None = None,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    serialised = "\n".join(pd.DatetimeIndex(sessions).strftime("%Y-%m-%d")) + "\n"
    record: dict[str, Any] = {
        "count": int(len(sessions)),
        "date_min": sessions.min().strftime("%Y-%m-%d"),
        "date_max": sessions.max().strftime("%Y-%m-%d"),
        "sha256": hashlib.sha256(serialised.encode("utf-8")).hexdigest(),
        "hash_encoding": "UTF-8 YYYY-MM-DD lines with trailing newline",
    }
    if d2a_dates is not None:
        raw_dates = pd.DatetimeIndex(d2a_dates)
        excluded = raw_dates.difference(sessions)
        record["d2a_distinct_date_count"] = int(len(raw_dates))
        record["excluded_d2a_non_session_date_count"] = int(len(excluded))
        record["excluded_d2a_non_session_dates"] = [
            value.strftime("%Y-%m-%d") for value in excluded
        ]
    if source is not None:
        record["source"] = source
    return record


def _manifest_for(
    output: pd.DataFrame,
    logical_out_path: Path,
    versioned_path: Path,
    output_sha256: str,
    label: str,
    inputs: dict[str, dict[str, Any]],
    sessions: pd.DatetimeIndex,
    d2a_dates: pd.DatetimeIndex | None = None,
    session_source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event_level = output.groupby("event_id", sort=False, observed=True).first()
    return {
        "schema_version": "1.0",
        "builder": "scripts/pead_d2b_event_window_contract.py",
        "label": label,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "policy": {
            "d1_event_filter": "valid_sue == True",
            "event_identity": "PEAD:<issuer_id>:<YYYY-MM-DD>",
            "lookback_market_sessions": LOOKBACK_SESSIONS,
            "lookback_boundary": "strictly before event_date",
            "liquidity_score": "arithmetic mean of finite dollar_volume",
            "minimum_liquidity_observations": MIN_LIQUIDITY_OBSERVATIONS,
            "tie_break": [
                "score DESC",
                "observations DESC",
                "normalized iid ASC",
                "security_id ASC",
            ],
            "iid_preference_or_fallback": False,
            "selection_scope": "one fixed event-level security for all +1..+60 sessions",
            "window_market_sessions": WINDOW_SESSIONS,
            "day_plus_one": "first authoritative U.S. market session strictly after event_date",
        },
        "session_spine": _session_spine_record(
            sessions,
            d2a_dates=d2a_dates,
            source=session_source,
        ),
        "counts": {
            "rows": int(len(output)),
            "events": int(output["event_id"].nunique()),
            "issuers": int(output["issuer_id"].nunique()),
            "selected_events": int(event_level["security_id"].notna().sum()),
            "handoff_eligible_events": int(event_level["handoff_eligible"].sum()),
            "selection_status": {
                str(key): int(value)
                for key, value in event_level["selection_status"].value_counts(dropna=False).items()
            },
            "coverage_reason": {
                str(key): int(value)
                for key, value in event_level["coverage_reason"].value_counts(dropna=False).items()
            },
        },
        "assertions": {
            "unique_event_id_event_day": True,
            "exactly_60_rows_per_event": True,
            "selected_security_never_switches_within_event": True,
            "selection_uses_only_pre_event_liquidity": True,
        },
        "declarations": {
            "zero_return_imputation": False,
            "minus_100_percent_imputation": False,
            "delisting_imputation": False,
            "delisting_label": False,
            "d2a_distinct_dates_define_market_sessions": session_source is None,
        },
        "output": {
            "parquet_file": versioned_path.name,
            "logical_parquet_name": logical_out_path.name,
            "sha256": output_sha256,
            "rows": int(len(output)),
            "schema": OUTPUT_COLUMNS,
        },
        "publication": {
            "protocol": "immutable hash-named Parquet plus atomic manifest replace under writer lock",
            "commit_point": logical_out_path.with_suffix(".parquet.manifest.json").name,
            "reader_rule": "read and validate manifest first, then resolve output.parquet_file",
        },
    }


def _prebuilt_output_summary(
    connection: duckdb.DuckDBPyConnection,
    parquet_path: Path,
) -> dict[str, Any]:
    temp_dir = parquet_path.parent
    conn = _validation_connection(temp_dir)
    try:
        parquet = pq.ParquetFile(parquet_path)
        columns = parquet.schema_arrow.names
        if columns != OUTPUT_COLUMNS:
            raise ValueError(f"D2B output schema drift: {columns}")
        source = f"read_parquet({_sql_literal(parquet_path.resolve())})"
        violations = conn.execute(
            f"""
            WITH event_checks AS (
                SELECT event_id,
                    count(*) AS rows_per_event,
                    count(DISTINCT event_day) AS distinct_days,
                    min(event_day) AS min_day,
                    max(event_day) AS max_day,
                    count(DISTINCT security_id) FILTER (WHERE security_id IS NOT NULL)
                        AS selected_security_count,
                    count(DISTINCT issuer_id) AS issuer_count,
                    count(DISTINCT event_date) AS event_date_count,
                    count(DISTINCT sue) AS sue_count,
                    count(DISTINCT is_primary_security) AS primary_flag_count
                FROM {source}
                GROUP BY event_id
            )
            SELECT count(*) FROM event_checks
            WHERE rows_per_event != {WINDOW_SESSIONS}
               OR distinct_days != {WINDOW_SESSIONS}
               OR min_day != 1 OR max_day != {WINDOW_SESSIONS}
               OR selected_security_count > 1
               OR issuer_count != 1 OR event_date_count != 1
               OR sue_count != 1 OR primary_flag_count != 1
            """
        ).fetchone()[0]
        if violations:
            raise ValueError("D2B prebuilt output violates event-window invariants")
        duplicate = conn.execute(
            f"""
            SELECT event_id, event_day FROM {source}
            GROUP BY event_id, event_day HAVING count(*) > 1 LIMIT 1
            """
        ).fetchone()
        if duplicate is not None:
            raise ValueError("D2B output contains duplicate (event_id, event_day) rows")
        invalid_timing = conn.execute(
            f"""
            SELECT count(*) FROM {source}
            WHERE return_date IS NOT NULL AND return_date <= event_date
            """
        ).fetchone()[0]
        if invalid_timing:
            raise ValueError("D2B return_date must be strictly after event_date")
        invalid_eligibility = conn.execute(
            f"""
            WITH expected AS (
                SELECT event_id,
                    bool_and(security_id IS NOT NULL)
                      AND count(return_date) = {WINDOW_SESSIONS}
                      AND count(*) FILTER (
                          WHERE coalesce(isfinite(asset_return), false)
                      ) = {WINDOW_SESSIONS} AS eligible,
                    bool_and(handoff_eligible) AS actual_handoff,
                    bool_and(window_complete) AS actual_complete
                FROM {source}
                GROUP BY event_id
            )
            SELECT count(*) FROM expected
            WHERE eligible != actual_handoff OR actual_handoff != actual_complete
            """
        ).fetchone()[0]
        if invalid_eligibility:
            raise ValueError("D2B handoff_eligible formula validation failed")
        counts = conn.execute(
            f"""
            SELECT count(*), count(DISTINCT event_id), count(DISTINCT issuer_id),
                count(*) FILTER (WHERE event_day = 1 AND security_id IS NOT NULL),
                count(*) FILTER (WHERE event_day = 1 AND handoff_eligible)
            FROM {source}
            """
        ).fetchone()
        if not counts[0]:
            raise ValueError("D2B output is empty")
        selection_status = {
            str(key): int(value)
            for key, value in conn.execute(
                f"""
                SELECT selection_status, count(*) FROM {source}
                WHERE event_day = 1 GROUP BY selection_status
                """
            ).fetchall()
        }
        coverage_reason = {
            str(key): int(value)
            for key, value in conn.execute(
                f"""
                SELECT coverage_reason, count(*) FROM {source}
                WHERE event_day = 1 GROUP BY coverage_reason
                """
            ).fetchall()
        }
    finally:
        conn.close()
    return {
        "rows": int(counts[0]),
        "events": int(counts[1]),
        "issuers": int(counts[2]),
        "selected_events": int(counts[3]),
        "handoff_eligible_events": int(counts[4]),
        "selection_status": selection_status,
        "coverage_reason": coverage_reason,
    }


def _manifest_for_prebuilt(
    summary: dict[str, Any],
    logical_out_path: Path,
    versioned_path: Path,
    output_sha256: str,
    label: str,
    inputs: dict[str, dict[str, Any]],
    sessions: pd.DatetimeIndex,
    d2a_dates: pd.DatetimeIndex,
    session_source: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "builder": "scripts/pead_d2b_event_window_contract.py",
        "label": label,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": inputs,
        "policy": {
            "d1_event_filter": "valid_sue == True",
            "event_identity": "PEAD:<issuer_id>:<YYYY-MM-DD>",
            "lookback_market_sessions": LOOKBACK_SESSIONS,
            "lookback_boundary": "strictly before event_date",
            "liquidity_score": "arithmetic mean of finite dollar_volume",
            "minimum_liquidity_observations": MIN_LIQUIDITY_OBSERVATIONS,
            "tie_break": [
                "score DESC",
                "observations DESC",
                "normalized iid ASC",
                "security_id ASC",
            ],
            "iid_preference_or_fallback": False,
            "selection_scope": "one fixed event-level security for all +1..+60 sessions",
            "window_market_sessions": WINDOW_SESSIONS,
            "day_plus_one": "first authoritative U.S. market session strictly after event_date",
        },
        "session_spine": _session_spine_record(
            sessions, d2a_dates=d2a_dates, source=session_source
        ),
        "counts": summary,
        "assertions": {
            "unique_event_id_event_day": True,
            "exactly_60_rows_per_event": True,
            "selected_security_never_switches_within_event": True,
            "selection_uses_only_pre_event_liquidity": True,
        },
        "declarations": {
            "zero_return_imputation": False,
            "minus_100_percent_imputation": False,
            "delisting_imputation": False,
            "delisting_label": False,
            "d2a_distinct_dates_define_market_sessions": session_source is None,
        },
        "output": {
            "parquet_file": versioned_path.name,
            "logical_parquet_name": logical_out_path.name,
            "sha256": output_sha256,
            "rows": summary["rows"],
            "schema": OUTPUT_COLUMNS,
        },
        "publication": {
            "protocol": "immutable hash-named Parquet plus atomic manifest replace under writer lock",
            "commit_point": logical_out_path.with_suffix(
                ".parquet.manifest.json"
            ).name,
            "reader_rule": "read and validate manifest first, then resolve output.parquet_file",
        },
    }


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


@contextmanager
def _publication_lock(lock_path: Path):
    """Hold a non-blocking OS file lock and clean its path after release."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
    except OSError as exc:
        handle.close()
        raise RuntimeError(f"D2B publication lock is already held: {lock_path}") from exc
    try:
        yield
    finally:
        try:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            _safe_unlink(lock_path)


def _versioned_parquet_path(logical_out_path: Path, sha256: str) -> Path:
    return logical_out_path.with_name(f"{logical_out_path.stem}.{sha256}.parquet")


def _manifest_points_to(
    manifest_path: Path,
    versioned_path: Path | None,
    output_sha256: str | None,
) -> bool:
    """Detect an atomically completed pointer replace even if interrupted after return."""
    if versioned_path is None or output_sha256 is None or not manifest_path.is_file():
        return False
    try:
        manifest = _read_manifest(manifest_path, "D2B output")
        output = manifest["output"]
        return (
            output["parquet_file"] == versioned_path.name
            and output["sha256"] == output_sha256
        )
    except (KeyError, TypeError, ValueError):
        return False


def publish_contract(
    output: pd.DataFrame,
    out_path: Path,
    label: str,
    inputs: dict[str, dict[str, Any]],
    sessions: pd.DatetimeIndex,
    d2a_dates: pd.DatetimeIndex | None = None,
    session_source: dict[str, Any] | None = None,
) -> Path:
    """Publish immutable Parquet first, then atomically replace the manifest pointer."""
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    sessions = pd.DatetimeIndex(sessions)
    _validate_output(output, sessions)
    if set(inputs) != {"d1", "d2a"}:
        raise ValueError("publication inputs must contain exactly d1 and d2a provenance")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    lock_path = out_path.with_suffix(".parquet.lock")
    with _publication_lock(lock_path):
        token = uuid.uuid4().hex
        parquet_tmp = out_path.with_name(f".{out_path.name}.{token}.tmp")
        manifest_tmp = manifest_path.with_name(f".{manifest_path.name}.{token}.tmp")
        versioned_path: Path | None = None
        output_sha256: str | None = None
        created_version = False
        manifest_committed = False
        try:
            output.to_parquet(parquet_tmp, index=False)
            output_sha256 = _sha256_file(parquet_tmp)
            versioned_path = _versioned_parquet_path(out_path, output_sha256)
            manifest = _manifest_for(
                output,
                out_path,
                versioned_path,
                output_sha256,
                label,
                inputs,
                sessions,
                d2a_dates,
                session_source,
            )
            manifest_tmp.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            if versioned_path.exists():
                if _sha256_file(versioned_path) != output_sha256:
                    raise ValueError("versioned Parquet filename/hash collision")
                _safe_unlink(parquet_tmp)
            else:
                os.replace(parquet_tmp, versioned_path)
                created_version = True
            os.replace(manifest_tmp, manifest_path)
            manifest_committed = True

            committed = _read_manifest(manifest_path, "D2B output")
            committed_path = manifest_path.parent / committed["output"]["parquet_file"]
            if _sha256_file(committed_path) != committed["output"]["sha256"]:
                raise ValueError("committed D2B Parquet hash does not match manifest")
            if out_path.exists() and out_path != committed_path:
                _safe_unlink(out_path)
            return manifest_path
        except BaseException:
            commit_completed = manifest_committed or _manifest_points_to(
                manifest_path, versioned_path, output_sha256
            )
            if created_version and not commit_completed and versioned_path is not None:
                _safe_unlink(versioned_path)
            raise
        finally:
            _safe_unlink(parquet_tmp)
            _safe_unlink(manifest_tmp)


def _commit_prebuilt_contract(
    parquet_tmp: Path,
    out_path: Path,
    label: str,
    inputs: dict[str, dict[str, Any]],
    sessions: pd.DatetimeIndex,
    d2a_dates: pd.DatetimeIndex,
    session_source: dict[str, Any] | None,
    summary: dict[str, Any],
) -> Path:
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    token = uuid.uuid4().hex
    manifest_tmp = manifest_path.with_name(f".{manifest_path.name}.{token}.tmp")
    versioned_path: Path | None = None
    output_sha256: str | None = None
    created_version = False
    manifest_committed = False
    try:
        output_sha256 = _sha256_file(parquet_tmp)
        versioned_path = _versioned_parquet_path(out_path, output_sha256)
        manifest = _manifest_for_prebuilt(
            summary,
            out_path,
            versioned_path,
            output_sha256,
            label,
            inputs,
            sessions,
            d2a_dates,
            session_source,
        )
        manifest_tmp.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if versioned_path.exists():
            if _sha256_file(versioned_path) != output_sha256:
                raise ValueError("versioned Parquet filename/hash collision")
            _safe_unlink(parquet_tmp)
        else:
            os.replace(parquet_tmp, versioned_path)
            created_version = True
        os.replace(manifest_tmp, manifest_path)
        manifest_committed = True
        committed = _read_manifest(manifest_path, "D2B output")
        committed_path = manifest_path.parent / committed["output"]["parquet_file"]
        if _sha256_file(committed_path) != committed["output"]["sha256"]:
            raise ValueError("committed D2B Parquet hash does not match manifest")
        if out_path.exists() and out_path != committed_path:
            _safe_unlink(out_path)
        return manifest_path
    except BaseException:
        commit_completed = manifest_committed or _manifest_points_to(
            manifest_path, versioned_path, output_sha256
        )
        if created_version and not commit_completed and versioned_path is not None:
            _safe_unlink(versioned_path)
        raise
    finally:
        _safe_unlink(parquet_tmp)
        _safe_unlink(manifest_tmp)


def build_full_contract(
    d1_manifest_path: Path,
    d2a_manifest_path: Path,
    out_path: Path,
    authoritative_sessions: pd.DatetimeIndex,
    *,
    session_source: dict[str, Any] | None = None,
    label: str = "full_universe_fixed_event_security_plus_60",
) -> Path:
    """Build D2B out of core while preserving the canonical IID/window contract."""
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    d1_artifact = _resolve_input_artifact_bounded(
        d1_manifest_path, D1_COLUMNS, "D1"
    )
    d2a_artifact = _resolve_input_artifact_bounded(
        d2a_manifest_path, D2A_COLUMNS, "D2A"
    )
    d1 = _read_small_artifact_in_batches(d1_artifact, D1_COLUMNS)
    normalized_events = _normalise_d1_events(d1)
    inputs = {
        "d1": d1_artifact.manifest_record(),
        "d2a": d2a_artifact.manifest_record(),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = out_path.with_suffix(".parquet.lock")
    with _publication_lock(lock_path):
        token = uuid.uuid4().hex
        parquet_tmp = out_path.with_name(f".{out_path.name}.{token}.tmp")
        connection, db_path = _bounded_connection(out_path.parent)
        try:
            _create_normalized_d2a_view(connection, d2a_artifact.parquet_path)
            d2a_dates = _validate_normalized_d2a_view(connection)
            sessions = market_session_spine(
                pd.DataFrame({"date": d2a_dates}), authoritative_sessions
            )
            connection.register("events_input", normalized_events)
            try:
                events = connection.execute(
                    """
                    SELECT e.* FROM events_input e
                    WHERE EXISTS (
                        SELECT 1 FROM d2a_normalized d
                        WHERE d.issuer_id = e.issuer_id
                    )
                    ORDER BY issuer_id, event_date
                    """
                ).fetch_df()
            finally:
                connection.unregister("events_input")
            if events.empty:
                raise ValueError(
                    "D1 and D2A have no overlapping valid-event issuer universe"
                )
            session_frame = pd.DataFrame(
                {
                    "session_pos": np.arange(len(sessions), dtype=np.int64),
                    "session_date": sessions,
                }
            )
            connection.register("events", events)
            connection.register("market_sessions", session_frame)
            try:
                connection.execute(
                    f"""
                    CREATE TABLE event_selected_securities AS
                    WITH event_positions AS (
                        SELECT e.*,
                            coalesce(s_cutoff.session_pos + 1, 0)::BIGINT AS cutoff_pos,
                            coalesce(s_start.session_pos + 1, 0)::BIGINT AS event_start_pos,
                            s_cutoff.session_date AS selection_cutoff_date
                        FROM events e
                        ASOF LEFT JOIN market_sessions s_cutoff
                          ON s_cutoff.session_date < cast(e.event_date AS DATE)
                        ASOF LEFT JOIN market_sessions s_start
                          ON s_start.session_date <= cast(e.event_date AS DATE)
                        WHERE hash(e.event_id) % 10 = 0
                    ), lookback AS (
                        SELECT e.event_id, d.security_id, d.iid, d.dollar_volume
                        FROM event_positions e
                        JOIN market_sessions s
                          ON s.session_pos >= greatest(0, e.cutoff_pos - {LOOKBACK_SESSIONS})
                         AND s.session_pos < e.cutoff_pos
                        JOIN d2a_normalized d
                          ON d.issuer_id = e.issuer_id
                         AND d.date = s.session_date
                    ), candidate_counts AS (
                        SELECT event_id, count(DISTINCT security_id)::BIGINT
                            AS candidate_security_count
                        FROM lookback
                        GROUP BY event_id
                    ), liquidity AS (
                        SELECT event_id, security_id, iid,
                            count(*) FILTER (WHERE isfinite(dollar_volume))::BIGINT
                                AS liquidity_observations,
                            avg(dollar_volume) FILTER (WHERE isfinite(dollar_volume))
                                AS trailing_mean_dollar_volume
                        FROM lookback
                        GROUP BY event_id, security_id, iid
                    ), ranked AS (
                        SELECT *, row_number() OVER (
                            PARTITION BY event_id
                            ORDER BY trailing_mean_dollar_volume DESC,
                                     liquidity_observations DESC,
                                     lower(iid) ASC,
                                     security_id ASC
                        ) AS candidate_rank
                        FROM liquidity
                        WHERE liquidity_observations >= {MIN_LIQUIDITY_OBSERVATIONS}
                    ), selected AS (
                        SELECT event_id, security_id, iid, liquidity_observations,
                               trailing_mean_dollar_volume
                        FROM ranked
                        WHERE candidate_rank = 1
                    )
                    SELECT e.event_id, e.event_date, e.issuer_id, e.sue, e.sue_price_scaled_clipped,
                           ep.cutoff_pos, ep.event_start_pos, ep.selection_cutoff_date,
                           w.security_id, w.iid, w.liquidity_observations, w.trailing_mean_dollar_volume,
                           coalesce(c.candidate_security_count, 0)::BIGINT AS candidate_security_count
                    FROM events e
                    JOIN event_positions ep USING (event_id)
                    LEFT JOIN selected w USING (event_id)
                    LEFT JOIN candidate_counts c USING (event_id)
                    WHERE hash(e.event_id) % 10 = 0
                    """
                )
                for i in range(1, 10):
                    connection.execute(
                        f"""
                        INSERT INTO event_selected_securities
                        WITH event_positions AS (
                            SELECT e.*,
                                coalesce(s_cutoff.session_pos + 1, 0)::BIGINT AS cutoff_pos,
                                coalesce(s_start.session_pos + 1, 0)::BIGINT AS event_start_pos,
                                s_cutoff.session_date AS selection_cutoff_date
                            FROM events e
                            ASOF LEFT JOIN market_sessions s_cutoff
                              ON s_cutoff.session_date < cast(e.event_date AS DATE)
                            ASOF LEFT JOIN market_sessions s_start
                              ON s_start.session_date <= cast(e.event_date AS DATE)
                            WHERE hash(e.event_id) % 10 = {i}
                        ), lookback AS (
                            SELECT e.event_id, d.security_id, d.iid, d.dollar_volume
                            FROM event_positions e
                            JOIN market_sessions s
                              ON s.session_pos >= greatest(0, e.cutoff_pos - {LOOKBACK_SESSIONS})
                             AND s.session_pos < e.cutoff_pos
                            JOIN d2a_normalized d
                              ON d.issuer_id = e.issuer_id
                             AND d.date = s.session_date
                        ), candidate_counts AS (
                            SELECT event_id, count(DISTINCT security_id)::BIGINT
                                AS candidate_security_count
                            FROM lookback
                            GROUP BY event_id
                        ), liquidity AS (
                            SELECT event_id, security_id, iid,
                                count(*) FILTER (WHERE isfinite(dollar_volume))::BIGINT
                                    AS liquidity_observations,
                                avg(dollar_volume) FILTER (WHERE isfinite(dollar_volume))
                                    AS trailing_mean_dollar_volume
                            FROM lookback
                            GROUP BY event_id, security_id, iid
                        ), ranked AS (
                            SELECT *, row_number() OVER (
                                PARTITION BY event_id
                                ORDER BY trailing_mean_dollar_volume DESC,
                                         liquidity_observations DESC,
                                         lower(iid) ASC,
                                         security_id ASC
                            ) AS candidate_rank
                            FROM liquidity
                            WHERE liquidity_observations >= {MIN_LIQUIDITY_OBSERVATIONS}
                        ), selected AS (
                            SELECT event_id, security_id, iid, liquidity_observations,
                                   trailing_mean_dollar_volume
                            FROM ranked
                            WHERE candidate_rank = 1
                        )
                        SELECT e.event_id, e.event_date, e.issuer_id, e.sue, e.sue_price_scaled_clipped,
                               ep.cutoff_pos, ep.event_start_pos, ep.selection_cutoff_date,
                               w.security_id, w.iid, w.liquidity_observations, w.trailing_mean_dollar_volume,
                               coalesce(c.candidate_security_count, 0)::BIGINT AS candidate_security_count
                        FROM events e
                        JOIN event_positions ep USING (event_id)
                        LEFT JOIN selected w USING (event_id)
                        LEFT JOIN candidate_counts c USING (event_id)
                        WHERE hash(e.event_id) % 10 = {i}
                        """
                    )

                # Create the event coverage table
                connection.execute(
                    """
                    CREATE TABLE event_coverage AS
                    SELECT
                        event_id,
                        0::BIGINT AS return_date_count,
                        0::BIGINT AS finite_return_count,
                        false AS has_missing_row,
                        false AS has_nonfinite_return
                    FROM events
                    WHERE 1 = 0
                    """
                )
                
                # Populate event coverage sequentially in chunks
                for i in range(10):
                    connection.execute(
                        f"""
                        INSERT INTO event_coverage
                        WITH skeleton AS (
                            SELECT e.event_id, e.security_id,
                                   e.event_start_pos + days.event_day - 1 AS return_session_pos
                            FROM event_selected_securities e
                            CROSS JOIN range(1, {WINDOW_SESSIONS + 1}) AS days(event_day)
                            WHERE hash(e.event_id) % 10 = {i}
                              AND e.security_id IS NOT NULL
                        ), observations AS (
                            SELECT sk.event_id,
                                d.security_id IS NOT NULL AS return_row_present,
                                d.total_return AS asset_return
                            FROM skeleton sk
                            LEFT JOIN market_sessions s
                              ON s.session_pos = sk.return_session_pos
                            LEFT JOIN d2a_normalized d
                              ON d.security_id = sk.security_id
                             AND d.date = s.session_date
                        )
                        SELECT event_id,
                            count(asset_return) AS return_date_count,
                            count(asset_return) FILTER (WHERE isfinite(asset_return)) AS finite_return_count,
                            bool_or(NOT return_row_present) AS has_missing_row,
                            bool_or(NOT coalesce(isfinite(asset_return), false)) AS has_nonfinite_return
                        FROM observations
                        GROUP BY event_id
                        """
                    )

                connection.execute(
                    f"""
                    COPY (
                        WITH skeleton AS (
                            SELECT e.*, days.event_day::BIGINT AS event_day,
                                   e.event_start_pos + days.event_day - 1 AS return_session_pos,
                                   coalesce(c.return_date_count, 0)::BIGINT AS return_date_count,
                                   coalesce(c.finite_return_count, 0)::BIGINT AS finite_return_count,
                                   coalesce(c.has_missing_row, true) AS has_missing_row,
                                   coalesce(c.has_nonfinite_return, true) AS has_nonfinite_return
                            FROM event_selected_securities e
                            LEFT JOIN event_coverage c USING (event_id)
                            CROSS JOIN range(1, {WINDOW_SESSIONS + 1}) AS days(event_day)
                        ), observations AS (
                            SELECT sk.*, cast(s.session_date AS TIMESTAMP) AS return_date,
                                d.security_id IS NOT NULL AS return_row_present,
                                d.total_return AS asset_return,
                                d.return_type,
                                d.guardrail_reason
                            FROM skeleton sk
                            LEFT JOIN market_sessions s
                              ON s.session_pos = sk.return_session_pos
                            LEFT JOIN d2a_normalized d
                              ON d.security_id = sk.security_id
                             AND d.date = s.session_date
                        )
                        SELECT
                            event_id,
                            issuer_id,
                            cast(event_date AS TIMESTAMP) AS event_date,
                            sue,
                            sue_price_scaled_clipped,
                            security_id,
                            iid,
                            security_id IS NOT NULL AS is_primary_security,
                            security_id IS NOT NULL
                                AND return_date_count = {WINDOW_SESSIONS}
                                AND finite_return_count = {WINDOW_SESSIONS} AS handoff_eligible,
                            CASE WHEN security_id IS NULL THEN 'no_eligible_candidate' ELSE 'selected' END
                                AS selection_status,
                            cast(selection_cutoff_date AS TIMESTAMP) AS selection_cutoff_date,
                            liquidity_observations,
                            trailing_mean_dollar_volume,
                            candidate_security_count,
                            event_day,
                            return_date,
                            return_row_present,
                            asset_return,
                            return_type,
                            guardrail_reason,
                            security_id IS NOT NULL
                                AND return_date_count = {WINDOW_SESSIONS}
                                AND finite_return_count = {WINDOW_SESSIONS} AS window_complete,
                            CASE
                                WHEN security_id IS NULL THEN 'no_eligible_security'
                                WHEN return_date_count != {WINDOW_SESSIONS}
                                    THEN 'insufficient_market_sessions'
                                WHEN has_missing_row AND has_nonfinite_return
                                    THEN 'missing_or_nonfinite_asset_returns'
                                WHEN has_missing_row THEN 'missing_return_rows'
                                WHEN has_nonfinite_return THEN 'nonfinite_asset_returns'
                                ELSE 'complete'
                            END AS coverage_reason
                        FROM observations
                        ORDER BY issuer_id, event_date, event_day
                    ) TO {_sql_literal(parquet_tmp.resolve())}
                    (FORMAT PARQUET, COMPRESSION ZSTD,
                     ROW_GROUP_SIZE {FULL_BUILD_ROW_GROUP_SIZE})
                    """
                )
            finally:
                connection.execute("DROP TABLE IF EXISTS event_selected_securities")
                connection.execute("DROP TABLE IF EXISTS event_coverage")
                connection.unregister("events")
                connection.unregister("market_sessions")
            connection.close()
            summary = _prebuilt_output_summary(None, parquet_tmp)
            return _commit_prebuilt_contract(
                parquet_tmp,
                out_path,
                label,
                inputs,
                sessions,
                d2a_dates,
                session_source,
                summary,
            )
        finally:
            connection.close()
            if db_path and db_path.exists():
                _safe_unlink(db_path)
            _safe_unlink(parquet_tmp)


def schema_check() -> None:
    print("[schema] " + ", ".join(OUTPUT_COLUMNS))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PEAD D2B fixed-security +60 event windows")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Build the approved canonical 500-GVKEY sample (default)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build full-universe D2B from the full D2A manifest in bounded memory",
    )
    parser.add_argument(
        "--session-source-zip",
        type=Path,
        help="Optional local Ken French daily ZIP used only for the market-session spine",
    )
    parser.add_argument("--schema-check", action="store_true")
    return parser


def _load_authoritative_market_sessions(
    source_zip_path: Path | None,
) -> tuple[pd.DatetimeIndex, dict[str, Any]]:
    try:
        from scripts import pead_d3_benchmark_artifact as benchmark
    except ModuleNotFoundError:
        import pead_d3_benchmark_artifact as benchmark

    if source_zip_path is None:
        source_zip = benchmark.fetch_ken_french_daily_zip()
    else:
        source_zip = Path(source_zip_path).read_bytes()
    source = benchmark.parse_ken_french_daily_zip(source_zip)
    sessions = pd.DatetimeIndex(source.frame["return_date"])
    provenance = {
        "kind": "ken_french_daily_factor_dates",
        "source_name": benchmark.SOURCE_NAME,
        "source_release": source.source_release,
        "source_download_sha256": source.source_download_sha256,
        "source_member_name": source.source_member_name,
        "source_url": benchmark.SOURCE_URL,
        "methodology_url": benchmark.METHODOLOGY_URL,
        "use": "authoritative_us_market_session_spine_only",
    }
    return sessions, provenance


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.build and args.sample:
        parser.error("--build and --sample are mutually exclusive")
    if args.schema_check:
        schema_check()
        return

    if args.build:
        authoritative_sessions, session_source = _load_authoritative_market_sessions(
            args.session_source_zip
        )
        manifest_path = build_full_contract(
            D1_MANIFEST_PATH,
            D2A_FULL_MANIFEST_PATH,
            OUT_FULL_PATH,
            authoritative_sessions,
            session_source=session_source,
        )
        manifest = _read_manifest(manifest_path, "D2B output")
        print(f"[write] {manifest_path.parent / manifest['output']['parquet_file']}")
        print(f"[write] {manifest_path}")
        print(
            f"[done] events={manifest['counts']['events']:,} "
            f"rows={manifest['counts']['rows']:,} "
            f"handoff_eligible={manifest['counts']['handoff_eligible_events']:,}"
        )
        return

    d1, d2a, inputs = load_validated_inputs()
    d2a_gvkeys = _normalise_identifier(d2a["gvkey"], "D2A.gvkey")
    gvkey_count = int(d2a_gvkeys.nunique())
    if gvkey_count != SAMPLE_N_GVKEYS:
        sys.exit(
            f"[error] D2B sample requires exactly {SAMPLE_N_GVKEYS} D2A GVKEYs; found {gvkey_count}"
        )
    normalised_d2a = _normalise_d2a(d2a)
    authoritative_sessions, session_source = _load_authoritative_market_sessions(
        args.session_source_zip
    )
    d2a_dates = pd.DatetimeIndex(
        normalised_d2a["date"].drop_duplicates().sort_values(kind="mergesort")
    )
    sessions = market_session_spine(normalised_d2a, authoritative_sessions)
    output = _build_event_window_contract_from_normalised(d1, normalised_d2a, sessions)
    manifest_path = publish_contract(
        output,
        OUT_SAMPLE_PATH,
        f"sample_{SAMPLE_N_GVKEYS}_gvkeys_fixed_event_security_plus_{WINDOW_SESSIONS}",
        inputs,
        sessions,
        d2a_dates,
        session_source,
    )
    manifest = _read_manifest(manifest_path, "D2B output")
    print(f"[write] {manifest_path.parent / manifest['output']['parquet_file']}")
    print(f"[write] {manifest_path}")
    print(
        f"[done] events={output['event_id'].nunique():,} rows={len(output):,} "
        f"handoff_eligible={output.groupby('event_id')['handoff_eligible'].first().sum():,}"
    )


if __name__ == "__main__":
    main()
