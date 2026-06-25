"""Build the M5a PEAD daily Fama/French 3-factor table.

This is a new artifact lane. It preserves SMB/HML from the same Ken French
3-factor daily source used by D3, and it does not rewrite or repoint the locked
D3 benchmark artifact.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.pead_d3_benchmark_artifact import (
    DATA_LIBRARY_URL,
    D2B_MANIFEST_PATH,
    METHODOLOGY_URL,
    SOURCE_LABEL,
    SOURCE_NAME,
    SOURCE_REGIME_NOTE,
    SOURCE_URL,
    _decode_text,
    _display_path,
    _publication_lock,
    _safe_unlink,
    _sha256_bytes,
    _sha256_file,
    fetch_ken_french_daily_zip,
    load_d2b_required_sessions,
)

ROOT = Path(__file__).resolve().parent.parent
OUT_FACTOR_PATH = ROOT / "data" / "processed" / "pead_d3m_ken_french_daily_multifactor.parquet"

OUTPUT_COLUMNS = [
    "return_date",
    "mktrf",
    "smb",
    "hml",
    "rf",
    "source_name",
    "source_release",
    "source_url",
    "methodology_url",
]

FORBIDDEN_USE = [
    "alpha_claims",
    "alerts",
    "broker_or_order_paths",
    "candidate_ranking",
    "candidate_scoring",
    "dashboard_integration",
    "provider_authorization_claims",
    "recommendations",
    "strict_point_in_time_claims",
    "tradability_claims",
]


@dataclass(frozen=True)
class KenFrenchThreeFactorSource:
    frame: pd.DataFrame
    source_release: str
    source_download_sha256: str
    source_member_name: str
    source_metadata_lines: tuple[str, ...]


def parse_ken_french_three_factor_daily_zip(zip_bytes: bytes) -> KenFrenchThreeFactorSource:
    """Parse official Ken French daily 3-factor ZIP, keeping MKT-RF/SMB/HML/RF."""
    source_download_sha256 = _sha256_bytes(zip_bytes)
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
            csv_entries = [
                entry
                for entry in archive.infolist()
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
    for line in lines[header_index + 1 :]:
        if not line.strip():
            break
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 5 or not re.fullmatch(r"\d{8}", parts[0]):
            break
        rows.append(
            {
                "return_date": parts[0],
                "mktrf": parts[1],
                "smb": parts[2],
                "hml": parts[3],
                "rf": parts[4],
            }
        )
    if not rows:
        raise ValueError("Ken French daily CSV contains no daily factor rows")

    frame = pd.DataFrame(rows)
    frame["return_date"] = pd.to_datetime(frame["return_date"], format="%Y%m%d")
    for column in ("mktrf", "smb", "hml", "rf"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce") / 100.0
    frame = frame[["return_date", "mktrf", "smb", "hml", "rf"]]
    validate_source_frame(frame)
    return KenFrenchThreeFactorSource(
        frame=frame,
        source_release=source_release,
        source_download_sha256=source_download_sha256,
        source_member_name=source_member_name,
        source_metadata_lines=metadata_lines,
    )


def validate_source_frame(frame: pd.DataFrame) -> None:
    if list(frame.columns) != ["return_date", "mktrf", "smb", "hml", "rf"]:
        raise ValueError("Ken French 3-factor source schema drift")
    if frame.empty:
        raise ValueError("Ken French 3-factor source frame is empty")
    if frame["return_date"].duplicated().any():
        raise ValueError("Ken French 3-factor source contains duplicate return_date rows")
    if not frame["return_date"].is_monotonic_increasing:
        raise ValueError("Ken French 3-factor source dates must be strictly sorted")
    if not frame["return_date"].dt.normalize().equals(frame["return_date"]):
        raise ValueError("Ken French 3-factor source dates must be date-only")
    numeric = frame[["mktrf", "smb", "hml", "rf"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("Ken French 3-factor source contains non-finite numeric return(s)")
    if numeric.lt(-1.0).any().any():
        raise ValueError("Ken French 3-factor source contains return(s) below -100%")
    if numeric.abs().gt(1.0).any().any():
        raise ValueError("Ken French 3-factor source appears to still be in percent units")


def build_multifactor_frame(
    source: KenFrenchThreeFactorSource,
    required_sessions: pd.DatetimeIndex,
) -> pd.DataFrame:
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
            "missing required D2B factor sessions; no fill or interpolation allowed: "
            f"{examples}"
        )
    output = indexed.loc[sessions, ["mktrf", "smb", "hml", "rf"]].reset_index()
    output = output.rename(columns={"index": "return_date"})
    output["source_name"] = SOURCE_NAME
    output["source_release"] = source.source_release
    output["source_url"] = SOURCE_URL
    output["methodology_url"] = METHODOLOGY_URL
    output = output[OUTPUT_COLUMNS]
    validate_multifactor_frame(output, sessions)
    return output


def validate_multifactor_frame(frame: pd.DataFrame, required_sessions: pd.DatetimeIndex) -> None:
    if list(frame.columns) != OUTPUT_COLUMNS:
        raise ValueError(f"M5a factor output schema drift: {list(frame.columns)}")
    if frame.empty:
        raise ValueError("M5a factor output is empty")
    sessions = pd.DatetimeIndex(required_sessions)
    dates = pd.DatetimeIndex(pd.to_datetime(frame["return_date"]))
    if not dates.equals(sessions):
        raise ValueError("M5a factor output dates must exactly equal required D2B sessions")
    if dates.has_duplicates:
        raise ValueError("M5a factor output contains duplicate return_date rows")
    numeric = frame[["mktrf", "smb", "hml", "rf"]]
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError("M5a factor output contains non-finite numeric return(s)")
    if numeric.lt(-1.0).any().any():
        raise ValueError("M5a factor output contains return(s) below -100%")
    if numeric.abs().gt(1.0).any().any():
        raise ValueError("M5a factor output appears to still be in percent units")
    for column in ("source_name", "source_release", "source_url", "methodology_url"):
        if frame[column].astype("string").str.strip().eq("").any() or frame[column].isna().any():
            raise ValueError(f"M5a factor output {column} must not be blank")


def _versioned_parquet_path(logical_out_path: Path, sha256: str) -> Path:
    return logical_out_path.with_name(f"{logical_out_path.stem}.{sha256}.parquet")


def _manifest_for(
    output: pd.DataFrame,
    logical_out_path: Path,
    versioned_path: Path,
    output_sha256: str,
    source: KenFrenchThreeFactorSource,
    d2b_input: Any,
) -> dict[str, Any]:
    sessions = d2b_input.sessions
    return {
        "artifact_name": "pead_d3m_ken_french_daily_multifactor",
        "schema_version": "1.0",
        "mode": "EXECUTION_PACKET",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "builder": "scripts/pead_m5a_multifactor_factors.py",
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
            "smb": "decimal_return",
            "hml": "decimal_return",
            "rf": "decimal_return",
        },
        "formula": "Mkt-RF, SMB, HML, RF are percent-to-decimal conversions from the Ken French daily 3-factor source",
        "required_d2b_sessions": int(len(sessions)),
        "matched_d2b_sessions": int(len(output)),
        "missing_d2b_sessions": [],
        "failure_reasons": [],
        "d2b_input": d2b_input.provenance,
        "allowed_use": "diagnostic_pead_m5a_multifactor_input_only",
        "forbidden_use": FORBIDDEN_USE,
        "locked_d3_policy": {
            "does_not_rewrite_d3": True,
            "does_not_repoint_d3_manifest": True,
            "separate_artifact_lane": True,
        },
        "publication": {
            "protocol": "immutable hash-named Parquet plus atomic manifest replace under writer lock",
            "commit_point": logical_out_path.with_suffix(".parquet.manifest.json").name,
            "reader_rule": "read and validate manifest first, then resolve parquet_file",
        },
    }


def publish_multifactor_artifact(
    output: pd.DataFrame,
    out_path: Path,
    source: KenFrenchThreeFactorSource,
    d2b_input: Any,
) -> Path:
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    validate_multifactor_frame(output, d2b_input.sessions)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    lock_path = out_path.with_suffix(".parquet.lock")
    with _publication_lock(lock_path):
        token = uuid.uuid4().hex
        parquet_tmp = out_path.with_name(f".{out_path.name}.{token}.tmp")
        manifest_tmp = manifest_path.with_name(f".{manifest_path.name}.{token}.tmp")
        versioned_path: Path | None = None
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
            manifest_tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            if versioned_path.exists():
                if _sha256_file(versioned_path) != output_sha256:
                    raise ValueError("versioned Parquet filename/hash collision")
                _safe_unlink(parquet_tmp)
            else:
                os.replace(parquet_tmp, versioned_path)
                created_version = True
            os.replace(manifest_tmp, manifest_path)
            manifest_committed = True
            committed = json.loads(manifest_path.read_text(encoding="utf-8"))
            committed_path = manifest_path.parent / committed["parquet_file"]
            if _sha256_file(committed_path) != committed["sha256"]:
                raise ValueError("committed M5a factor Parquet hash does not match manifest")
            if out_path.exists() and out_path != committed_path:
                _safe_unlink(out_path)
            return manifest_path
        except BaseException:
            if created_version and not manifest_committed and versioned_path is not None:
                _safe_unlink(versioned_path)
            raise
        finally:
            _safe_unlink(parquet_tmp)
            _safe_unlink(manifest_tmp)


def schema_check() -> None:
    print("[schema] " + ", ".join(OUTPUT_COLUMNS))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PEAD M5a Ken French 3-factor artifact")
    parser.add_argument("--build", action="store_true", help="Build and publish the M5a factor artifact")
    parser.add_argument("--schema-check", action="store_true")
    parser.add_argument("--source-zip", type=Path, help="Optional local Ken French daily 3-factor ZIP")
    parser.add_argument("--d2b-manifest", type=Path, default=D2B_MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=OUT_FACTOR_PATH)
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
    source = parse_ken_french_three_factor_daily_zip(source_zip)
    d2b_input = load_d2b_required_sessions(args.d2b_manifest, source)
    output = build_multifactor_frame(source, d2b_input.sessions)
    manifest_path = publish_multifactor_artifact(output, args.out, source, d2b_input)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
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
