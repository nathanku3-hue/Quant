"""Build the D3 Ken French daily benchmark artifact for PEAD.

The artifact is intentionally narrow: it converts the official Ken French daily
3-factor source from percent returns to decimal returns, computes
``benchmark_return = mktrf + rf``, and publishes only the dates required by the
validated D2B event-window session spine.
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
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parent.parent
D2B_MANIFEST_PATH = (
    ROOT / "data" / "processed" / "pead_d2b_event_windows_sample.parquet.manifest.json"
)
OUT_BENCHMARK_PATH = (
    ROOT / "data" / "processed" / "pead_d3_ken_french_daily_benchmark.parquet"
)

DATA_LIBRARY_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html"
METHODOLOGY_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/f-f_factors.html"
)
SOURCE_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_daily_CSV.zip"
)
SOURCE_NAME = "ken_french_fama_french_3_factors_daily"
SOURCE_LABEL = "Kenneth French Data Library Fama/French 3 Factors [Daily]"
SOURCE_REGIME_NOTE = (
    "Ken French Data Library notes CRSP FIZ files were discontinued after the "
    "December 2024 data release and current U.S. research returns use CRSP CIZ "
    "beginning with the January 2025 release."
)

OUTPUT_COLUMNS = [
    "return_date",
    "mktrf",
    "rf",
    "benchmark_return",
    "source_name",
    "source_release",
    "source_url",
    "methodology_url",
]

FORBIDDEN_USE = [
    "provider authorization claims",
    "alpha interpretation",
    "dashboard integration",
    "candidate ranking",
    "candidate scoring",
    "alerts",
    "broker/order paths",
    "mktrf-alone total market return",
    "missing-date fill or interpolation",
]


@dataclass(frozen=True)
class D2BSessionInput:
    sessions: pd.DatetimeIndex
    provenance: dict[str, Any]


@dataclass(frozen=True)
class KenFrenchSource:
    frame: pd.DataFrame
    source_release: str
    source_download_sha256: str
    source_member_name: str
    source_metadata_lines: tuple[str, ...]


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _read_manifest_snapshot(path: Path, label: str) -> tuple[dict[str, Any], str]:
    try:
        payload = path.read_bytes()
    except FileNotFoundError:
        raise
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} manifest is not valid UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} manifest must contain a JSON object")
    return value, _sha256_bytes(payload)


def _read_manifest(path: Path, label: str) -> dict[str, Any]:
    value, _ = _read_manifest_snapshot(path, label)
    return value


def _session_spine_record(sessions: pd.DatetimeIndex) -> dict[str, Any]:
    sessions = pd.DatetimeIndex(sessions)
    serialised = "\n".join(sessions.strftime("%Y-%m-%d")) + "\n"
    return {
        "count": int(len(sessions)),
        "date_min": sessions.min().strftime("%Y-%m-%d"),
        "date_max": sessions.max().strftime("%Y-%m-%d"),
        "sha256": _sha256_bytes(serialised.encode("utf-8")),
        "hash_encoding": "UTF-8 YYYY-MM-DD lines with trailing newline",
    }


def _local_parquet_from_manifest(manifest_path: Path, parquet_file: str, label: str) -> Path:
    if not isinstance(parquet_file, str) or not parquet_file.strip():
        raise ValueError(f"{label} parquet_file must be a non-empty string")
    name = Path(parquet_file)
    if name.name != parquet_file or name.suffix.lower() != ".parquet":
        raise ValueError(f"{label} parquet_file must be a local .parquet filename")
    parquet_path = (manifest_path.parent / parquet_file).resolve()
    if parquet_path.parent != manifest_path.parent.resolve():
        raise ValueError(f"{label} parquet_file escapes its manifest directory")
    return parquet_path


def _root_relative_path(path_text: str, label: str) -> Path:
    if not isinstance(path_text, str) or not path_text.strip():
        raise ValueError(f"{label} path must be a non-empty string")
    path = Path(path_text)
    resolved = path.resolve() if path.is_absolute() else (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} path escapes the repository root") from exc
    return resolved


def _sessions_from_date_column(parquet_bytes: bytes, date_column: str, label: str) -> pd.DatetimeIndex:
    frame = pd.read_parquet(io.BytesIO(parquet_bytes), columns=[date_column])
    dates = pd.to_datetime(frame[date_column].dropna())
    sessions = pd.DatetimeIndex(dates.drop_duplicates().sort_values())
    if sessions.empty or not sessions.is_monotonic_increasing or sessions.has_duplicates:
        raise ValueError(f"{label} session spine must be non-empty, sorted, and unique")
    if not sessions.normalize().equals(sessions):
        raise ValueError(f"{label} session spine must contain date-only values")
    return sessions


def _sessions_from_d2a_input(manifest: dict[str, Any]) -> tuple[pd.DatetimeIndex, dict[str, Any]] | None:
    inputs = manifest.get("inputs")
    if not isinstance(inputs, dict):
        return None
    d2a = inputs.get("d2a")
    if not isinstance(d2a, dict):
        return None
    for key in ("parquet_path", "parquet_sha256", "rows", "schema"):
        if key not in d2a:
            raise ValueError(f"D2B manifest inputs.d2a is missing required field: {key}")
    parquet_path = _root_relative_path(str(d2a["parquet_path"]), "D2A input")
    parquet_bytes = parquet_path.read_bytes()
    expected_sha = str(d2a["parquet_sha256"])
    actual_sha = _sha256_bytes(parquet_bytes)
    if actual_sha != expected_sha:
        raise ValueError(f"D2A input Parquet hash drift: expected {expected_sha}, got {actual_sha}")
    parquet = pq.ParquetFile(io.BytesIO(parquet_bytes))
    actual_columns = parquet.schema_arrow.names
    if list(d2a["schema"]) != actual_columns:
        raise ValueError("D2A input Parquet schema drift against D2B manifest provenance")
    if "date" not in actual_columns:
        raise ValueError("D2A input schema must include date")
    if int(d2a["rows"]) != int(parquet.metadata.num_rows):
        raise ValueError("D2A input row-count drift against D2B manifest provenance")
    sessions = _sessions_from_date_column(parquet_bytes, "date", "D2A input")
    provenance = {
        "source": "d2b_manifest_inputs_d2a",
        "parquet_path": _display_path(parquet_path),
        "parquet_sha256": actual_sha,
        "rows": int(d2a["rows"]),
    }
    return sessions, provenance


def _sessions_from_authoritative_source(
    expected_spine: dict[str, Any],
    source: KenFrenchSource,
) -> tuple[pd.DatetimeIndex, dict[str, Any]] | None:
    source_record = expected_spine.get("source")
    if not isinstance(source_record, dict):
        return None
    if source_record.get("kind") != "ken_french_daily_factor_dates":
        raise ValueError("D2B session_spine source kind is unsupported")
    expected_source = {
        "source_name": SOURCE_NAME,
        "source_release": source.source_release,
        "source_download_sha256": source.source_download_sha256,
        "source_member_name": source.source_member_name,
        "source_url": SOURCE_URL,
        "methodology_url": METHODOLOGY_URL,
    }
    for key, expected in expected_source.items():
        if source_record.get(key) != expected:
            raise ValueError(f"D2B session_spine source {key} drift")
    start = pd.Timestamp(expected_spine["date_min"])
    end = pd.Timestamp(expected_spine["date_max"])
    dates = pd.DatetimeIndex(source.frame["return_date"])
    sessions = dates[(dates >= start) & (dates <= end)]
    provenance = {
        "source": "d2b_authoritative_ken_french_session_spine",
        **expected_source,
    }
    return sessions, provenance


def load_d2b_required_sessions(
    manifest_path: Path = D2B_MANIFEST_PATH,
    source: KenFrenchSource | None = None,
) -> D2BSessionInput:
    """Validate the D2B manifest/Parquet pair and return its unique session spine."""
    manifest_path = Path(manifest_path).resolve()
    manifest, manifest_sha256 = _read_manifest_snapshot(manifest_path, "D2B")
    output = manifest.get("output")
    if not isinstance(output, dict):
        raise ValueError("D2B manifest is missing output object")
    for key in ("parquet_file", "sha256", "rows", "schema"):
        if key not in output:
            raise ValueError(f"D2B manifest output is missing required field: {key}")
    parquet_path = _local_parquet_from_manifest(
        manifest_path, str(output["parquet_file"]), "D2B"
    )
    parquet_bytes = parquet_path.read_bytes()
    expected_sha = output["sha256"]
    actual_sha = _sha256_bytes(parquet_bytes)
    if expected_sha != actual_sha:
        raise ValueError(f"D2B Parquet hash drift: expected {expected_sha}, got {actual_sha}")
    parquet = pq.ParquetFile(io.BytesIO(parquet_bytes))
    actual_columns = parquet.schema_arrow.names
    if list(output["schema"]) != actual_columns:
        raise ValueError("D2B Parquet schema drift against manifest output.schema")
    if "return_date" not in actual_columns:
        raise ValueError("D2B output schema must include return_date")
    if int(output["rows"]) != int(parquet.metadata.num_rows):
        raise ValueError("D2B row-count drift against manifest output.rows")

    expected_spine = manifest.get("session_spine")
    if not isinstance(expected_spine, dict):
        raise ValueError("D2B manifest is missing session_spine")
    authoritative_sessions = (
        _sessions_from_authoritative_source(expected_spine, source)
        if source is not None
        else None
    )
    if expected_spine.get("source") is not None and authoritative_sessions is None:
        raise ValueError(
            "D2B authoritative session_spine requires the matching Ken French source"
        )
    d2a_sessions = (
        None if authoritative_sessions is not None else _sessions_from_d2a_input(manifest)
    )
    if authoritative_sessions is not None:
        sessions, session_source = authoritative_sessions
    elif d2a_sessions is None:
        sessions = _sessions_from_date_column(parquet_bytes, "return_date", "D2B output")
        session_source = {
            "source": "d2b_output_return_date_fallback",
            "note": "Used only when D2B manifest does not expose inputs.d2a provenance.",
        }
    else:
        sessions, session_source = d2a_sessions
    actual_spine = _session_spine_record(sessions)
    for key in ("count", "date_min", "date_max", "sha256"):
        if expected_spine.get(key) != actual_spine[key]:
            raise ValueError(f"D2B session_spine {key} drift")
    provenance = {
        "manifest_path": _display_path(manifest_path),
        "manifest_sha256": manifest_sha256,
        "parquet_path": _display_path(parquet_path),
        "parquet_sha256": actual_sha,
        "rows": int(output["rows"]),
        "session_spine": actual_spine,
        "session_source": session_source,
    }
    return D2BSessionInput(sessions=sessions, provenance=provenance)


def fetch_ken_french_daily_zip(source_url: str = SOURCE_URL, timeout: int = 60) -> bytes:
    parsed = urlparse(source_url)
    if parsed.scheme != "https" or parsed.netloc.lower() != "mba.tuck.dartmouth.edu":
        raise ValueError("Ken French source URL must be the approved official HTTPS host")
    request = Request(source_url, headers={"User-Agent": "Quant-D3-benchmark-artifact/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _decode_text(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Ken French CSV payload is not decodable as UTF-8 or Latin-1")


def parse_ken_french_daily_zip(zip_bytes: bytes) -> KenFrenchSource:
    """Parse the official daily ZIP and convert source percent returns to decimals."""
    source_download_sha256 = _sha256_bytes(zip_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            csv_entries = [
                entry for entry in archive.infolist()
                if not entry.is_dir() and entry.filename.lower().endswith(".csv")
            ]
            if len(csv_entries) != 1:
                raise ValueError("Ken French daily ZIP must contain exactly one CSV file")
            entry = csv_entries[0]
            text = _decode_text(archive.read(entry))
            source_member_name = entry.filename
    except zipfile.BadZipFile as exc:
        raise ValueError("Ken French source file is not a valid ZIP archive") from exc

    lines = text.splitlines()
    header_index = None
    for index, line in enumerate(lines):
        parts = [part.strip() for part in line.split(",")]
        if len(parts) >= 5 and parts[1:5] == ["Mkt-RF", "SMB", "HML", "RF"]:
            header_index = index
            break
    if header_index is None:
        raise ValueError("Ken French daily CSV header not found")

    metadata_lines = tuple(line.strip() for line in lines[:header_index] if line.strip())
    release_candidates = [
        line for line in metadata_lines if re.search(r"\bCRSP database\b", line, re.IGNORECASE)
    ]
    if not release_candidates:
        raise ValueError("Ken French source release line is missing")
    source_release = release_candidates[0]

    rows: list[dict[str, Any]] = []
    for line in lines[header_index + 1:]:
        if not line.strip():
            break
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5 or not re.fullmatch(r"\d{8}", parts[0]):
            break
        rows.append(
            {
                "return_date": parts[0],
                "mktrf": parts[1],
                "rf": parts[4],
            }
        )
    if not rows:
        raise ValueError("Ken French daily CSV contains no daily factor rows")

    frame = pd.DataFrame(rows)
    frame["return_date"] = pd.to_datetime(frame["return_date"], format="%Y%m%d")
    for column in ("mktrf", "rf"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce") / 100.0
    frame["benchmark_return"] = frame["mktrf"] + frame["rf"]
    frame = frame[["return_date", "mktrf", "rf", "benchmark_return"]]
    _validate_source_frame(frame)
    return KenFrenchSource(
        frame=frame,
        source_release=source_release,
        source_download_sha256=source_download_sha256,
        source_member_name=source_member_name,
        source_metadata_lines=metadata_lines,
    )


def _validate_source_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != ["return_date", "mktrf", "rf", "benchmark_return"]:
        raise ValueError("Ken French source schema drift")
    if frame.empty:
        raise ValueError("Ken French source frame is empty")
    if frame["return_date"].duplicated().any():
        raise ValueError("Ken French source contains duplicate return_date rows")
    if not frame["return_date"].is_monotonic_increasing:
        raise ValueError("Ken French source dates must be strictly sorted")
    if not frame["return_date"].dt.normalize().equals(frame["return_date"]):
        raise ValueError("Ken French source dates must be date-only")
    numeric = frame[["mktrf", "rf", "benchmark_return"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Ken French source contains non-finite numeric return(s)")
    if numeric.lt(-1.0).any().any():
        raise ValueError("Ken French source contains return(s) below -100%")
    if numeric.abs().gt(1.0).any().any():
        raise ValueError("Ken French source appears to still be in percent units")
    if not np.allclose(
        frame["benchmark_return"], frame["mktrf"] + frame["rf"], rtol=0.0, atol=1e-12
    ):
        raise ValueError("benchmark_return must equal mktrf + rf after decimal conversion")


def build_benchmark_frame(source: KenFrenchSource, required_sessions: pd.DatetimeIndex) -> pd.DataFrame:
    sessions = pd.DatetimeIndex(required_sessions)
    if sessions.empty or not sessions.is_monotonic_increasing or sessions.has_duplicates:
        raise ValueError("required D2B sessions must be non-empty, sorted, and unique")
    if not sessions.normalize().equals(sessions):
        raise ValueError("required D2B sessions must contain date-only values")

    indexed = source.frame.set_index("return_date", verify_integrity=True)
    missing = sessions.difference(indexed.index)
    if len(missing):
        examples = [ts.strftime("%Y-%m-%d") for ts in missing[:10]]
        raise ValueError(
            "missing required D2B benchmark sessions; no fill or interpolation allowed: "
            f"{examples}"
        )
    output = indexed.loc[sessions, ["mktrf", "rf", "benchmark_return"]].reset_index()
    output = output.rename(columns={"index": "return_date"})
    output["source_name"] = SOURCE_NAME
    output["source_release"] = source.source_release
    output["source_url"] = SOURCE_URL
    output["methodology_url"] = METHODOLOGY_URL
    output = output[OUTPUT_COLUMNS]
    validate_benchmark_frame(output, sessions)
    return output


def validate_benchmark_frame(frame: pd.DataFrame, required_sessions: pd.DatetimeIndex) -> None:
    if list(frame.columns) != OUTPUT_COLUMNS:
        raise ValueError(f"D3 benchmark output schema drift: {list(frame.columns)}")
    if frame.empty:
        raise ValueError("D3 benchmark output is empty")
    sessions = pd.DatetimeIndex(required_sessions)
    dates = pd.DatetimeIndex(pd.to_datetime(frame["return_date"]))
    if not dates.equals(sessions):
        raise ValueError("D3 benchmark output dates must exactly equal required D2B sessions")
    if dates.has_duplicates:
        raise ValueError("D3 benchmark output contains duplicate return_date rows")
    numeric = frame[["mktrf", "rf", "benchmark_return"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("D3 benchmark output contains non-finite numeric return(s)")
    if numeric.lt(-1.0).any().any():
        raise ValueError("D3 benchmark output contains return(s) below -100%")
    if numeric.abs().gt(1.0).any().any():
        raise ValueError("D3 benchmark output appears to still be in percent units")
    if not np.allclose(
        frame["benchmark_return"], frame["mktrf"] + frame["rf"], rtol=0.0, atol=1e-12
    ):
        raise ValueError("benchmark_return must equal mktrf + rf after decimal conversion")
    for column in ("source_name", "source_release", "source_url", "methodology_url"):
        if frame[column].astype("string").str.strip().eq("").any() or frame[column].isna().any():
            raise ValueError(f"D3 benchmark output {column} must not be blank")


def _versioned_parquet_path(logical_out_path: Path, sha256: str) -> Path:
    return logical_out_path.with_name(f"{logical_out_path.stem}.{sha256}.parquet")


def _manifest_for(
    output: pd.DataFrame,
    logical_out_path: Path,
    versioned_path: Path,
    output_sha256: str,
    source: KenFrenchSource,
    d2b_input: D2BSessionInput,
) -> dict[str, Any]:
    sessions = d2b_input.sessions
    return {
        "artifact_name": "pead_d3_ken_french_daily_benchmark",
        "schema_version": "1.0",
        "mode": "EXECUTION_PACKET",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "builder": "scripts/pead_d3_benchmark_artifact.py",
        "parquet_file": versioned_path.name,
        "logical_parquet_name": logical_out_path.name,
        "sha256": output_sha256,
        "row_count": int(len(output)),
        "columns": OUTPUT_COLUMNS,
        "min_return_date": output["return_date"].min().strftime("%Y-%m-%d"),
        "max_return_date": output["return_date"].max().strftime("%Y-%m-%d"),
        "source_name": SOURCE_NAME,
        "source_label": SOURCE_LABEL,
        "source_url": SOURCE_URL,
        "data_library_url": DATA_LIBRARY_URL,
        "methodology_url": METHODOLOGY_URL,
        "source_release": source.source_release,
        "source_download_sha256": source.source_download_sha256,
        "source_member_name": source.source_member_name,
        "source_metadata_lines": list(source.source_metadata_lines),
        "source_regime_note": SOURCE_REGIME_NOTE,
        "units": {
            "source_file": "percent_returns",
            "mktrf": "decimal_return",
            "rf": "decimal_return",
            "benchmark_return": "decimal_return",
        },
        "formula": "benchmark_return = mktrf + rf after percent-to-decimal conversion",
        "required_d2b_sessions": int(len(sessions)),
        "matched_d2b_sessions": int(len(output)),
        "missing_d2b_sessions": [],
        "failure_reasons": [],
        "d2b_input": d2b_input.provenance,
        "allowed_use": "benchmark_input_for_pead_d3_only",
        "forbidden_use": FORBIDDEN_USE,
        "publication": {
            "protocol": "immutable hash-named Parquet plus atomic manifest replace under writer lock",
            "commit_point": logical_out_path.with_suffix(".parquet.manifest.json").name,
            "reader_rule": "read and validate manifest first, then resolve parquet_file",
        },
    }


@contextmanager
def _publication_lock(lock_path: Path):
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
        raise RuntimeError(f"D3 benchmark publication lock is already held: {lock_path}") from exc
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


def _manifest_points_to(
    manifest_path: Path,
    versioned_path: Path | None,
    output_sha256: str | None,
) -> bool:
    if versioned_path is None or output_sha256 is None or not manifest_path.is_file():
        return False
    try:
        manifest = _read_manifest(manifest_path, "D3 benchmark output")
        return (
            manifest["parquet_file"] == versioned_path.name
            and manifest["sha256"] == output_sha256
        )
    except (KeyError, TypeError, ValueError):
        return False


def publish_benchmark_artifact(
    output: pd.DataFrame,
    out_path: Path,
    source: KenFrenchSource,
    d2b_input: D2BSessionInput,
) -> Path:
    """Publish immutable Parquet first, then atomically replace the manifest pointer."""
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    validate_benchmark_frame(output, d2b_input.sessions)

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
                source,
                d2b_input,
            )
            manifest_tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            if versioned_path.exists():
                if _sha256_file(versioned_path) != output_sha256:
                    raise ValueError("versioned Parquet filename/hash collision")
                _safe_unlink(parquet_tmp)
            else:
                os.replace(parquet_tmp, versioned_path)
                created_version = True
            os.replace(manifest_tmp, manifest_path)
            manifest_committed = True

            committed = _read_manifest(manifest_path, "D3 benchmark output")
            committed_path = manifest_path.parent / committed["parquet_file"]
            if _sha256_file(committed_path) != committed["sha256"]:
                raise ValueError("committed D3 benchmark Parquet hash does not match manifest")
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


def schema_check() -> None:
    print("[schema] " + ", ".join(OUTPUT_COLUMNS))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PEAD D3 Ken French benchmark artifact")
    parser.add_argument("--build", action="store_true", help="Build and publish the D3 artifact")
    parser.add_argument("--schema-check", action="store_true")
    parser.add_argument("--source-zip", type=Path, help="Optional local Ken French daily ZIP")
    parser.add_argument("--d2b-manifest", type=Path, default=D2B_MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUT_BENCHMARK_PATH)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.schema_check:
        schema_check()
        return
    if not args.build:
        parser.error("--build is required; this script has no interpretation-only mode")

    if args.source_zip is not None:
        source_zip = Path(args.source_zip).read_bytes()
    else:
        source_zip = fetch_ken_french_daily_zip()
    source = parse_ken_french_daily_zip(source_zip)
    d2b_input = load_d2b_required_sessions(args.d2b_manifest, source)
    output = build_benchmark_frame(source, d2b_input.sessions)
    manifest_path = publish_benchmark_artifact(output, args.out, source, d2b_input)
    manifest = _read_manifest(manifest_path, "D3 benchmark output")
    print(f"[write] {manifest_path.parent / manifest['parquet_file']}")
    print(f"[write] {manifest_path}")
    print(
        "[coverage] "
        f"{manifest['matched_d2b_sessions']}/{manifest['required_d2b_sessions']} "
        f"{manifest['min_return_date']}..{manifest['max_return_date']}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise
