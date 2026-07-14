"""Standalone dated-identifier authority gate for PEAD M7F5-ID0.

This module locks the complete pre-identity 2019 D1 event universe and inspects
one candidate Compustat identifier source only when an exact-byte semantics
envelope and a repository-authoritative committed approval blob bind its bytes,
owner, scope, and identifier-validity semantics. It does not import any
M7F4/portfolio code, fetch data, create a mapping artifact, or run a research
curve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_D1_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet"
DEFAULT_IDENTIFIER_SOURCE_PATH = (
    ROOT / "data" / "processed" / "security_master_compustat.parquet"
)
APPROVAL_REPOSITORY_ROOT = ROOT

ROUND_ID = "ROUND-20260714-M7F5-ID0-DATED-IDENTIFIER-AUTHORITY"
SCOPE_ID = "M7F5_ID0_DATED_IDENTIFIER_AUTHORITY_COMMIT_A"
SCHEMA_VERSION = "pead_m7f5_id0_dated_identifier_authority_v2"
PROVENANCE_SCHEMA_VERSION = "pead_m7f5_id0_source_semantics_v2"
PROVENANCE_DECLARATION_TYPE = "SOURCE_IDENTIFIER_VALIDITY_SEMANTICS"
APPROVAL_SCHEMA_VERSION = "pead_m7f5_id0_git_blob_approval_v1"
APPROVAL_AUTHORITY_TYPE = "DATA_OWNER_IDENTIFIER_VALIDITY_APPROVAL"
APPROVAL_SCOPE = "M7F5_ID0_DATED_IDENTIFIER_AUTHORITY"
APPROVAL_DECISION = "APPROVED"
APPROVAL_DATA_OWNER_ROLE = "DATA_OWNER"
APPROVAL_PATH_PREFIX = "docs/authorization/"
PROVENANCE_INTERVAL_MEANING = "IDENTIFIER_VALIDITY"
SUPPORTED_IDENTIFIER_TYPES = frozenset({"CUSIP", "CUSIP8", "NCUSIP"})
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
STATUS_BLOCKED_PROVENANCE = (
    "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_PROVENANCE_REQUIRED"
)
STATUS_BLOCKED_SCHEMA = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_SCHEMA_INVALID"
STATUS_BLOCKED_INTERVALS = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_INTERVAL_INVALID"
STATUS_BLOCKED_COVERAGE = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_EVENT_COVERAGE_INCOMPLETE"
STATUS_BLOCKED_AMBIGUITY = "BLOCKED_DATED_COMPUSTAT_IDENTIFIER_EVENT_IDENTITY_AMBIGUOUS"
STATUS_PASS = "PASS_DATED_COMPUSTAT_IDENTIFIER_SOURCE_CONTRACT"

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


def _duplicate_key_hook(label: str):
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        parsed: dict[str, Any] = {}
        for key, value in pairs:
            if key in parsed:
                raise M7F5ID0InputError(f"{label}_duplicate_key:{key}")
            parsed[key] = value
        return parsed

    return reject_duplicates


def _load_json_payload(payload: bytes, *, label: str) -> dict[str, Any]:
    try:
        decoded = payload.decode("utf-8")
        parsed = json.loads(decoded, object_pairs_hook=_duplicate_key_hook(label))
    except M7F5ID0InputError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise M7F5ID0InputError(f"{label}_invalid_json:{exc}") from exc
    if not isinstance(parsed, dict):
        raise M7F5ID0InputError(f"{label}_root_must_be_object")
    return parsed


def _read_json_file(path: Path, *, label: str) -> tuple[dict[str, Any], str]:
    """Read, hash, and parse the same exact JSON bytes."""
    if not path.is_file():
        raise M7F5ID0InputError(f"{label}_not_found:{path}")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise M7F5ID0InputError(f"{label}_unreadable:{path}:{exc}") from exc
    return _load_json_payload(payload, label=label), hashlib.sha256(payload).hexdigest()


def _require_mapping(value: Any, *, field: str, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise M7F5ID0InputError(f"{label}_field_must_be_object:{field}")
    return value


def _require_non_empty_string(value: Any, *, field: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise M7F5ID0InputError(
            f"{label}_field_must_be_non_empty_string:{field}"
        )
    return value.strip()


def _require_exact_keys(
    value: Mapping[str, Any], *, expected: set[str], field: str, label: str
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        raise M7F5ID0InputError(
            f"{label}_required_keys_missing:{field}:{','.join(missing)}"
        )
    if unexpected:
        raise M7F5ID0InputError(
            f"{label}_unexpected_keys:{field}:{','.join(unexpected)}"
        )


def _require_sha256(value: Any, *, field: str, label: str) -> str:
    normalized = _require_non_empty_string(value, field=field, label=label)
    if not re.fullmatch(r"[0-9a-f]{64}", normalized):
        raise M7F5ID0InputError(f"{label}_field_must_be_lowercase_hex64:{field}")
    return normalized


def _normalize_binding(
    raw: Mapping[str, Any], *, label: str, field_prefix: str = "binding"
) -> dict[str, Any]:
    _require_exact_keys(
        raw,
        expected={
            "gvkey_column",
            "identifier_column",
            "identifier_type",
            "effective_start_column",
            "effective_end_column",
            "effective_interval_semantics",
        },
        field=field_prefix,
        label=label,
    )
    semantics = _require_mapping(
        raw.get("effective_interval_semantics"),
        field=f"{field_prefix}.effective_interval_semantics",
        label=label,
    )
    _require_exact_keys(
        semantics,
        expected={
            "meaning",
            "start_inclusive",
            "end_inclusive",
            "null_end_means_open_ended",
        },
        field=f"{field_prefix}.effective_interval_semantics",
        label=label,
    )
    normalized = {
        "gvkey_column": _require_non_empty_string(
            raw.get("gvkey_column"), field=f"{field_prefix}.gvkey_column", label=label
        ),
        "identifier_column": _require_non_empty_string(
            raw.get("identifier_column"),
            field=f"{field_prefix}.identifier_column",
            label=label,
        ),
        "identifier_type": _require_non_empty_string(
            raw.get("identifier_type"),
            field=f"{field_prefix}.identifier_type",
            label=label,
        ).upper(),
        "effective_start_column": _require_non_empty_string(
            raw.get("effective_start_column"),
            field=f"{field_prefix}.effective_start_column",
            label=label,
        ),
        "effective_end_column": _require_non_empty_string(
            raw.get("effective_end_column"),
            field=f"{field_prefix}.effective_end_column",
            label=label,
        ),
        "interval_meaning": _require_non_empty_string(
            semantics.get("meaning"),
            field=f"{field_prefix}.effective_interval_semantics.meaning",
            label=label,
        ),
        "start_inclusive": semantics.get("start_inclusive"),
        "end_inclusive": semantics.get("end_inclusive"),
        "null_end_means_open_ended": semantics.get("null_end_means_open_ended"),
    }
    for boolean_field in (
        "start_inclusive",
        "end_inclusive",
        "null_end_means_open_ended",
    ):
        if not isinstance(normalized[boolean_field], bool):
            raise M7F5ID0InputError(
                f"{label}_field_must_be_boolean:{field_prefix}.{boolean_field}"
            )
    return normalized


def _parse_provenance_envelope(path: Path) -> tuple[dict[str, Any], str]:
    label = "provenance_envelope"
    raw, envelope_sha256 = _read_json_file(path, label=label)
    _require_exact_keys(
        raw,
        expected={
            "schema_version",
            "declaration_type",
            "dataset",
            "source_sha256",
            "binding",
        },
        field="root",
        label=label,
    )
    dataset = _require_mapping(raw.get("dataset"), field="dataset", label=label)
    _require_exact_keys(
        dataset,
        expected={"name", "version"},
        field="dataset",
        label=label,
    )
    binding = _require_mapping(raw.get("binding"), field="binding", label=label)
    normalized = {
        "schema_version": _require_non_empty_string(
            raw.get("schema_version"), field="schema_version", label=label
        ),
        "declaration_type": _require_non_empty_string(
            raw.get("declaration_type"), field="declaration_type", label=label
        ),
        "dataset_name": _require_non_empty_string(
            dataset.get("name"), field="dataset.name", label=label
        ),
        "dataset_version": _require_non_empty_string(
            dataset.get("version"), field="dataset.version", label=label
        ),
        "source_sha256": _require_sha256(
            raw.get("source_sha256"), field="source_sha256", label=label
        ),
        **_normalize_binding(binding, label=label),
    }
    return normalized, envelope_sha256


def _parse_approval_payload(payload: bytes) -> dict[str, Any]:
    label = "authority_approval"
    raw = _load_json_payload(payload, label=label)
    _require_exact_keys(
        raw,
        expected={
            "schema_version",
            "authority_type",
            "approval_scope",
            "decision",
            "owner",
            "approval_ref",
            "provenance_envelope_sha256",
            "source_sha256",
            "dataset",
            "binding",
        },
        field="root",
        label=label,
    )
    owner = _require_mapping(raw.get("owner"), field="owner", label=label)
    dataset = _require_mapping(raw.get("dataset"), field="dataset", label=label)
    binding = _require_mapping(raw.get("binding"), field="binding", label=label)
    _require_exact_keys(
        owner, expected={"identity", "role"}, field="owner", label=label
    )
    _require_exact_keys(
        dataset, expected={"name", "version"}, field="dataset", label=label
    )
    return {
        "schema_version": _require_non_empty_string(
            raw.get("schema_version"), field="schema_version", label=label
        ),
        "authority_type": _require_non_empty_string(
            raw.get("authority_type"), field="authority_type", label=label
        ),
        "approval_scope": _require_non_empty_string(
            raw.get("approval_scope"), field="approval_scope", label=label
        ),
        "decision": _require_non_empty_string(
            raw.get("decision"), field="decision", label=label
        ),
        "owner_identity": _require_non_empty_string(
            owner.get("identity"), field="owner.identity", label=label
        ),
        "owner_role": _require_non_empty_string(
            owner.get("role"), field="owner.role", label=label
        ),
        "approval_ref": _require_non_empty_string(
            raw.get("approval_ref"), field="approval_ref", label=label
        ),
        "provenance_envelope_sha256": _require_sha256(
            raw.get("provenance_envelope_sha256"),
            field="provenance_envelope_sha256",
            label=label,
        ),
        "source_sha256": _require_sha256(
            raw.get("source_sha256"), field="source_sha256", label=label
        ),
        "dataset_name": _require_non_empty_string(
            dataset.get("name"), field="dataset.name", label=label
        ),
        "dataset_version": _require_non_empty_string(
            dataset.get("version"), field="dataset.version", label=label
        ),
        **_normalize_binding(binding, label=label),
    }


def _git_environment() -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    env.update(
        {
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return env


def _run_git(
    repository_root: Path,
    arguments: Sequence[str],
    *,
    allowed_returncodes: set[int] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    allowed = allowed_returncodes or {0}
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_git_environment(),
        )
    except OSError as exc:
        raise M7F5ID0InputError(f"authority_git_unavailable:{exc}") from exc
    if completed.returncode not in allowed:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise M7F5ID0InputError(
            f"authority_git_command_failed:{arguments[0]}:{completed.returncode}:{detail}"
        )
    return completed


def _normalize_approval_commit(value: str) -> str:
    normalized = value.strip()
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", normalized):
        raise M7F5ID0InputError("approval_commit_must_be_full_lowercase_object_id")
    return normalized


def _normalize_approval_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise M7F5ID0InputError("approval_path_must_be_non_empty")
    candidate = value.strip()
    if "\\" in candidate or "\x00" in candidate:
        raise M7F5ID0InputError("approval_path_must_be_canonical_posix")
    path = PurePosixPath(candidate)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise M7F5ID0InputError("approval_path_must_be_canonical_relative")
    normalized = path.as_posix()
    if normalized != candidate:
        raise M7F5ID0InputError("approval_path_must_be_canonical_relative")
    if not normalized.startswith(APPROVAL_PATH_PREFIX) or not normalized.endswith(".json"):
        raise M7F5ID0InputError(
            "approval_path_must_be_json_under_docs_authorization"
        )
    return normalized


def _parse_ls_tree_blob(payload: bytes, *, expected_path: str, label: str) -> tuple[str, str]:
    entries = [entry for entry in payload.split(b"\x00") if entry]
    if len(entries) != 1 or b"\t" not in entries[0]:
        raise M7F5ID0InputError(f"{label}_blob_not_found:{expected_path}")
    header, raw_path = entries[0].split(b"\t", 1)
    try:
        mode, object_type, object_id = header.decode("ascii").split()
        actual_path = raw_path.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise M7F5ID0InputError(f"{label}_tree_entry_invalid") from exc
    if actual_path != expected_path or mode != "100644" or object_type != "blob":
        raise M7F5ID0InputError(f"{label}_must_be_regular_json_blob:{expected_path}")
    return object_id.lower(), mode


def _same_resolved_path(first: Path, second: Path) -> bool:
    return os.path.normcase(str(first.resolve())) == os.path.normcase(str(second.resolve()))


def _read_git_blob_approval(
    repository_root: Path, *, approval_commit: str, approval_path: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read authority only from an immutable, current, reachable Git blob."""
    root = repository_root.resolve()
    commit = _normalize_approval_commit(approval_commit)
    path = _normalize_approval_path(approval_path)

    top_level = _run_git(root, ["rev-parse", "--show-toplevel"]).stdout.decode(
        "utf-8", errors="strict"
    ).strip()
    if not _same_resolved_path(Path(top_level), root):
        raise M7F5ID0InputError("approval_repository_root_mismatch")

    resolved_commit = _run_git(
        root, ["rev-parse", "--verify", f"{commit}^{{commit}}"]
    ).stdout.decode("ascii").strip().lower()
    if resolved_commit != commit:
        raise M7F5ID0InputError("approval_commit_does_not_resolve_exactly")
    head_commit = _run_git(
        root, ["rev-parse", "--verify", "HEAD^{commit}"]
    ).stdout.decode("ascii").strip().lower()
    ancestry = _run_git(
        root,
        ["merge-base", "--is-ancestor", commit, head_commit],
        allowed_returncodes={0, 1},
    )
    if ancestry.returncode != 0:
        raise M7F5ID0InputError("approval_commit_not_reachable_from_head")

    committed_tree = _run_git(
        root, ["ls-tree", "-z", commit, "--", path]
    ).stdout
    blob_oid, mode = _parse_ls_tree_blob(
        committed_tree, expected_path=path, label="approval_commit"
    )
    head_tree = _run_git(
        root, ["ls-tree", "-z", head_commit, "--", path]
    ).stdout
    head_blob_oid, _ = _parse_ls_tree_blob(
        head_tree, expected_path=path, label="approval_head"
    )
    if head_blob_oid != blob_oid:
        raise M7F5ID0InputError("approval_blob_changed_or_revoked_at_head")

    payload = _run_git(root, ["cat-file", "blob", blob_oid]).stdout
    approval = _parse_approval_payload(payload)
    report = {
        "repository_root": root.as_posix(),
        "commit": commit,
        "head_commit": head_commit,
        "path": path,
        "blob_oid": blob_oid,
        "blob_mode": mode,
        "blob_sha256": hashlib.sha256(payload).hexdigest(),
        "reachable_from_head": True,
        "present_unchanged_at_head": True,
    }
    return approval, report


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


def _normalize_identifier8(series: pd.Series, *, identifier_type: str) -> pd.Series:
    lexical = _lexical_identifier_mask(series)
    trimmed = series.where(lexical).astype("string").str.strip()
    ascii_shape = trimmed.str.fullmatch(r"[0-9A-Za-z]{8,9}", na=False)
    cleaned = trimmed.where(ascii_shape).str.upper()
    normalized_type = identifier_type.upper()
    if normalized_type == "CUSIP":
        identifier8 = cleaned.str.slice(0, 8)
        valid8 = cleaned.str.fullmatch(r"[0-9A-Z]{8}", na=False)
        valid9_shape = cleaned.str.fullmatch(r"[0-9A-Z]{8}[0-9]", na=False)
        valid9_checksum = cleaned.str[8].eq(_cusip_check_digit(identifier8))
        return identifier8.where(valid8 | (valid9_shape & valid9_checksum))
    if normalized_type in {"CUSIP8", "NCUSIP"}:
        valid = cleaned.str.fullmatch(r"[0-9A-Z]{8}", na=False)
        return cleaned.where(valid)
    return pd.Series(pd.NA, index=series.index, dtype="string")


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


def _detect_effective_pair(columns: Sequence[str]) -> tuple[str, str] | None:
    """Detect familiar date pairs for diagnostics only; never authorize them."""
    index = _casefold_columns(columns)
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


AUTHORITY_BINDING_FIELDS = (
    "gvkey_column",
    "identifier_column",
    "identifier_type",
    "effective_start_column",
    "effective_end_column",
    "interval_meaning",
    "start_inclusive",
    "end_inclusive",
    "null_end_means_open_ended",
)


def _authority_reason_codes(
    provenance: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    source_sha256: str,
    envelope_sha256: str,
) -> list[str]:
    reasons: list[str] = []
    if provenance["schema_version"] != PROVENANCE_SCHEMA_VERSION:
        reasons.append("unsupported_provenance_schema_version")
    if provenance["declaration_type"] != PROVENANCE_DECLARATION_TYPE:
        reasons.append("unsupported_provenance_declaration_type")
    if provenance["source_sha256"] != source_sha256:
        reasons.append("provenance_source_sha256_mismatch")
    if provenance["identifier_type"] not in SUPPORTED_IDENTIFIER_TYPES:
        reasons.append("unsupported_provenance_identifier_type")
    if provenance["interval_meaning"] != PROVENANCE_INTERVAL_MEANING:
        reasons.append("effective_interval_semantics_are_not_identifier_validity")
    if provenance["start_inclusive"] is not True:
        reasons.append("effective_start_must_be_inclusive")
    if provenance["end_inclusive"] is not True:
        reasons.append("effective_end_must_be_inclusive")
    if provenance["null_end_means_open_ended"] is not True:
        reasons.append("null_effective_end_must_mean_open_ended")

    if approval["schema_version"] != APPROVAL_SCHEMA_VERSION:
        reasons.append("unsupported_approval_schema_version")
    if approval["authority_type"] != APPROVAL_AUTHORITY_TYPE:
        reasons.append("unsupported_approval_authority_type")
    if approval["approval_scope"] != APPROVAL_SCOPE:
        reasons.append("approval_scope_mismatch")
    if approval["decision"] != APPROVAL_DECISION:
        reasons.append("approval_decision_is_not_approved")
    if approval["owner_role"] != APPROVAL_DATA_OWNER_ROLE:
        reasons.append("approval_owner_role_is_not_data_owner")
    if approval["provenance_envelope_sha256"] != envelope_sha256:
        reasons.append("approval_provenance_envelope_sha256_mismatch")
    if approval["source_sha256"] != source_sha256:
        reasons.append("approval_source_sha256_mismatch")
    if approval["source_sha256"] != provenance["source_sha256"]:
        reasons.append("approval_and_provenance_source_sha256_mismatch")
    if approval["dataset_name"] != provenance["dataset_name"]:
        reasons.append("approval_dataset_name_mismatch")
    if approval["dataset_version"] != provenance["dataset_version"]:
        reasons.append("approval_dataset_version_mismatch")
    for field in AUTHORITY_BINDING_FIELDS:
        if approval[field] != provenance[field]:
            reasons.append(f"approval_binding_mismatch:{field}")
    return reasons


def inspect_identifier_source(
    source_path: Path,
    events: pd.DataFrame,
    *,
    provenance_envelope_path: Path | None = None,
    approval_commit: str | None = None,
    approval_path: str | None = None,
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
            "provenance_envelope": None,
            "authority_approval": None,
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
    detected_pair = _detect_effective_pair(columns)
    source_report: dict[str, Any] = {
        **base,
        "sha256": source_sha256,
        "row_count": int(len(frame)),
        "columns": sorted(columns),
        "identifier_column": None,
        "identifier_type": None,
        "gvkey_column": None,
        "effective_date_columns": None,
        "detected_unbound_effective_date_columns": (
            {"start": detected_pair[0], "end": detected_pair[1]}
            if detected_pair is not None
            else None
        ),
        "effective_date_semantics_explicitly_bound": False,
        "provenance_envelope": None,
        "authority_approval": None,
        "updated_at_profile": updated_at_profile,
    }

    authority_values = (
        provenance_envelope_path,
        approval_commit,
        approval_path,
    )
    if not any(value is not None for value in authority_values):
        return {
            **source_report,
            "status": STATUS_BLOCKED_PROVENANCE,
            "reason_codes": ["committed_git_blob_data_owner_approval_required"],
            "coverage": None,
        }
    if not all(value is not None for value in authority_values):
        raise M7F5ID0InputError(
            "provenance_envelope_approval_commit_and_path_required_together"
        )

    assert provenance_envelope_path is not None
    assert approval_commit is not None
    assert approval_path is not None
    provenance, envelope_sha256 = _parse_provenance_envelope(
        provenance_envelope_path
    )
    approval, approval_git_report = _read_git_blob_approval(
        APPROVAL_REPOSITORY_ROOT,
        approval_commit=approval_commit,
        approval_path=approval_path,
    )
    provenance_report = {
        "path": _path_text(provenance_envelope_path),
        "sha256": envelope_sha256,
        "schema_version": provenance["schema_version"],
        "declaration_type": provenance["declaration_type"],
        "dataset": {
            "name": provenance["dataset_name"],
            "version": provenance["dataset_version"],
        },
        "source_sha256": provenance["source_sha256"],
        "binding": {
            "gvkey_column": provenance["gvkey_column"],
            "identifier_column": provenance["identifier_column"],
            "identifier_type": provenance["identifier_type"],
            "effective_start_column": provenance["effective_start_column"],
            "effective_end_column": provenance["effective_end_column"],
            "effective_interval_semantics": {
                "meaning": provenance["interval_meaning"],
                "start_inclusive": provenance["start_inclusive"],
                "end_inclusive": provenance["end_inclusive"],
                "null_end_means_open_ended": provenance[
                    "null_end_means_open_ended"
                ],
            },
        },
        "verified": False,
    }
    approval_report = {
        **approval_git_report,
        "schema_version": approval["schema_version"],
        "authority_type": approval["authority_type"],
        "approval_scope": approval["approval_scope"],
        "decision": approval["decision"],
        "owner": {
            "identity": approval["owner_identity"],
            "role": approval["owner_role"],
        },
        "approval_ref": approval["approval_ref"],
        "provenance_envelope_sha256": approval[
            "provenance_envelope_sha256"
        ],
        "source_sha256": approval["source_sha256"],
        "dataset": {
            "name": approval["dataset_name"],
            "version": approval["dataset_version"],
        },
        "binding": {
            "gvkey_column": approval["gvkey_column"],
            "identifier_column": approval["identifier_column"],
            "identifier_type": approval["identifier_type"],
            "effective_start_column": approval["effective_start_column"],
            "effective_end_column": approval["effective_end_column"],
            "effective_interval_semantics": {
                "meaning": approval["interval_meaning"],
                "start_inclusive": approval["start_inclusive"],
                "end_inclusive": approval["end_inclusive"],
                "null_end_means_open_ended": approval[
                    "null_end_means_open_ended"
                ],
            },
        },
        "verified": False,
    }
    authority_reasons = _authority_reason_codes(
        provenance,
        approval,
        source_sha256=source_sha256,
        envelope_sha256=envelope_sha256,
    )
    if authority_reasons:
        return {
            **source_report,
            "provenance_envelope": provenance_report,
            "authority_approval": approval_report,
            "status": STATUS_BLOCKED_PROVENANCE,
            "reason_codes": authority_reasons,
            "coverage": None,
        }

    identifier = _resolve_named_column(
        columns, provenance["identifier_column"], ()
    )
    gvkey_column = _resolve_named_column(columns, provenance["gvkey_column"], ())
    start_column = _resolve_named_column(
        columns, provenance["effective_start_column"], ()
    )
    end_column = _resolve_named_column(
        columns, provenance["effective_end_column"], ()
    )
    source_report = {
        **source_report,
        "identifier_column": identifier,
        "identifier_type": provenance["identifier_type"],
        "gvkey_column": gvkey_column,
        "effective_date_columns": (
            {"start": start_column, "end": end_column}
            if start_column is not None and end_column is not None
            else None
        ),
        "effective_date_semantics_explicitly_bound": True,
        "provenance_envelope": {**provenance_report, "verified": True},
        "authority_approval": {**approval_report, "verified": True},
    }
    missing_bound_columns: list[str] = []
    if gvkey_column is None:
        missing_bound_columns.append("provenance_bound_gvkey_column_missing")
    if identifier is None:
        missing_bound_columns.append("provenance_bound_identifier_column_missing")
    if start_column is None:
        missing_bound_columns.append("provenance_bound_effective_start_column_missing")
    if end_column is None:
        missing_bound_columns.append("provenance_bound_effective_end_column_missing")
    if missing_bound_columns:
        return {
            **source_report,
            "status": STATUS_BLOCKED_SCHEMA,
            "reason_codes": missing_bound_columns,
            "coverage": None,
        }

    assert gvkey_column is not None
    assert identifier is not None
    assert start_column is not None
    assert end_column is not None
    normalized = pd.DataFrame(
        {
            "gvkey": _normalize_gvkey(frame[gvkey_column]),
            "identifier8": _normalize_identifier8(
                frame[identifier], identifier_type=provenance["identifier_type"]
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
    provenance_envelope_path: Path | None = None,
    approval_commit: str | None = None,
    approval_path: str | None = None,
    expected_d1_sha256: str = LOCKED_D1_SHA256,
    expected_event_count: int = LOCKED_PRE_IDENTITY_EVENT_COUNT,
    expected_event_set_sha256: str = LOCKED_PRE_IDENTITY_EVENT_SET_SHA256,
    expected_canonical_rows_sha256: str = LOCKED_PRE_IDENTITY_CANONICAL_ROWS_SHA256,
) -> dict[str, Any]:
    authority_values = (provenance_envelope_path, approval_commit, approval_path)
    if provenance_envelope_path is not None:
        for input_path in (d1_path, identifier_source_path):
            if _paths_alias(provenance_envelope_path, input_path):
                raise M7F5ID0InputError(
                    f"provenance_envelope_must_be_detached_from_input:{input_path}"
                )
    if any(value is not None for value in authority_values) and not all(
        value is not None for value in authority_values
    ):
        raise M7F5ID0InputError(
            "provenance_envelope_approval_commit_and_path_required_together"
        )

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
            provenance_envelope_path=provenance_envelope_path,
            approval_commit=approval_commit,
            approval_path=approval_path,
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
            "OBTAIN_COMMITTED_DATA_OWNER_APPROVAL_OR_HOLD"
            if status == STATUS_BLOCKED_PROVENANCE
            else (
                "AUTHORIZE_HISTORICAL_IDENTIFIER_ACQUISITION_OR_TERMINATE_PEAD_STRICT_PIT"
                if status == STATUS_BLOCKED_SOURCE_ABSENT
                else "HOLD_UNTIL_SEPARATELY_AUTHORIZED_NEXT_SCOPE"
            )
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
    parser.add_argument(
        "--provenance-envelope",
        type=Path,
        help="Detached source-semantics JSON bound to the exact source bytes.",
    )
    parser.add_argument(
        "--approval-commit",
        help="Full commit ID containing the repository-authoritative approval blob.",
    )
    parser.add_argument(
        "--approval-path",
        help="Canonical docs/authorization/*.json path at the approval commit.",
    )
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        input_paths = [args.d1, args.identifier_source]
        if args.provenance_envelope is not None:
            input_paths.append(args.provenance_envelope)
        _validate_output_path(args.output, input_paths)
        evidence = evaluate_authority(
            d1_path=args.d1,
            identifier_source_path=args.identifier_source,
            provenance_envelope_path=args.provenance_envelope,
            approval_commit=args.approval_commit,
            approval_path=args.approval_path,
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
