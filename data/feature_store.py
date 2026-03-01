"""
Terminal Zero — Feature Store Builder (FR-060)

Builds selector-ready, PIT-safe stock features:
  data/processed/features.parquet
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
from pandas.tseries.offsets import BDay

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402
from data import fundamentals as fundamentals_data  # noqa: E402
from data.feature_specs import (  # noqa: E402
    FeatureSpec,
    build_default_feature_specs,
    compute_registry_hash,
)
from utils.parallel import parallel_execute  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
PRICES_TRI_PATH = os.path.join(PROCESSED_DIR, "prices_tri.parquet")
TICKERS_PATH = os.path.join(PROCESSED_DIR, "tickers.parquet")
MACRO_FEATURES_PATH = os.path.join(PROCESSED_DIR, "macro_features.parquet")
MACRO_FEATURES_TRI_PATH = os.path.join(PROCESSED_DIR, "macro_features_tri.parquet")
FEATURES_PATH = os.path.join(PROCESSED_DIR, "features.parquet")
FUNDAMENTALS_PATH = os.path.join(PROCESSED_DIR, "fundamentals.parquet")
FUNDAMENTALS_SNAPSHOT_PATH = os.path.join(PROCESSED_DIR, "fundamentals_snapshot.parquet")

SPY_PERMNO = 84398
UNIVERSE_MODE_GLOBAL = "global"
UNIVERSE_MODE_YEARLY_UNION = "yearly_union"
UNIVERSE_MODES = {UNIVERSE_MODE_GLOBAL, UNIVERSE_MODE_YEARLY_UNION}
MEMORY_ENVELOPE_WARN_GB = 8.0
MEMORY_ENVELOPE_ABORT_GB = 24.0
CS_SCALE_STANDARD = "standard"
CS_SCALE_ROBUST = "robust"
CS_SCALE_MODES = {CS_SCALE_STANDARD, CS_SCALE_ROBUST}
CS_SCALE_DEFAULT_EPSILON_FLOOR = 1e-6
CS_SCALE_DEFAULT_MIN_WINDOW = 20

PERSISTED_FEATURE_COLUMNS = [
    "date",
    "permno",
    "ticker",
    "adj_close",
    "tri",
    "volume",
    "rolling_beta_63d",
    "resid_mom_60d",
    "rel_strength_60d",
    "amihud_20d",
    "illiq_21d",
    "yz_vol_20d",
    "realized_vol_21d",
    "atr_14d",
    "rsi_14d",
    "dist_sma20",
    "sma200",
    "trend_veto",
    "z_resid_mom",
    "z_flow_proxy",
    "z_vol_penalty",
    "composite_score",
    "z_moat",
    "z_inventory_quality_proxy",
    "z_discipline_cond",
    "z_demand",
    "capital_cycle_score",
    "quality_composite",
    "yz_mode",
    "atr_mode",
]
REQUIRED_PERSISTED_FACTOR_COLUMNS = ("z_inventory_quality_proxy", "z_discipline_cond")
FEATURE_PARTITION_YEAR_COL = "year"
FEATURE_PARTITION_MONTH_COL = "month"
FEATURE_PARTITION_COLUMNS = (FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL)
FEATURE_COMMIT_MANIFEST = "_commit_manifest.json"  # legacy v1 manifest path
FEATURE_MANIFESTS_DIR = "_manifests"
FEATURE_CURRENT_POINTER = "CURRENT"
FEATURE_VERSION_STORE_SUFFIX = ".__versions"
FEATURE_MANIFEST_VERSION_V2 = "v2"
FEATURE_GC_RETENTION_HOURS_MIN = 24
FEATURE_CACHE_POLICY = {
    "stale_while_revalidate_sec": 0,
    "tombstone_priority": "enforced",
}
logger = logging.getLogger(__name__)
_FILE_HASH_CACHE: dict[str, tuple[int, int, str]] = {}


class AmbiguousFeatureStoreStateError(RuntimeError):
    """Raised when feature-store state cannot be deterministically reconstructed."""


class FeatureSpecExecutionError(RuntimeError):
    """Raised when declarative feature spec execution fails and build must fail closed."""


@dataclass(frozen=True)
class FeatureStoreConfig:
    start_year: int = 2000
    top_n: int = 3000
    universe_mode: str = UNIVERSE_MODE_YEARLY_UNION
    yearly_top_n: int = 100
    beta_window: int = 63
    resid_mom_window: int = 60
    rel_strength_window: int = 60
    amihud_window: int = 20
    yz_window: int = 20
    atr_window: int = 14
    rsi_window: int = 14
    sma_short_window: int = 20
    sma_trend_window: int = 200
    cs_scale_mode: str = CS_SCALE_ROBUST
    cs_scale_epsilon_floor: float = CS_SCALE_DEFAULT_EPSILON_FLOOR
    cs_scale_min_window_size: int = CS_SCALE_DEFAULT_MIN_WINDOW


def _new_status() -> dict:
    return {
        "log": [],
        "warnings": [],
        "success": False,
        "rows_written": 0,
        "cache_hit": False,
        "cache_key": None,
        "fallback_rate": None,
        "fallback_rows": 0,
        "fallback_total_rows": 0,
        "cs_scale_mode": None,
        "feature_commit_id": None,
        "feature_touched_partitions": [],
    }


def _log(status: dict, msg: str):
    print(msg)
    status["log"].append(msg)


def _warn(status: dict, msg: str):
    _log(status, f"⚠ {msg}")
    status["warnings"].append(msg)


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _price_source_config() -> dict[str, str | None]:
    # Day 2 migration guardrail: if prices_tri exists, treat TRI as the signal-close source.
    if os.path.exists(PRICES_TRI_PATH):
        return {
            "mode": "tri",
            "base": PRICES_TRI_PATH,
            "patch": None,
            "price_col": "tri",
            "legacy_col": "legacy_adj_close",
        }
    return {
        "mode": "legacy",
        "base": PRICES_PATH,
        "patch": PATCH_PATH if os.path.exists(PATCH_PATH) else None,
        "price_col": "adj_close",
        "legacy_col": "adj_close",
    }


def _macro_source_path() -> str:
    if os.path.exists(MACRO_FEATURES_TRI_PATH):
        return MACRO_FEATURES_TRI_PATH
    return MACRO_FEATURES_PATH


def _feature_store_scan_glob(path: str) -> str:
    if os.path.isdir(path):
        return os.path.join(path, "**", "*.parquet")
    return path


def _feature_manifest_path(path: str) -> str:
    return os.path.join(path, FEATURE_COMMIT_MANIFEST)


def _feature_versions_root(path: str) -> str:
    return f"{path}{FEATURE_VERSION_STORE_SUFFIX}"


def _feature_manifests_dir(path: str) -> str:
    return os.path.join(path, FEATURE_MANIFESTS_DIR)


def _feature_current_pointer_path(path: str) -> str:
    return os.path.join(_feature_manifests_dir(path), FEATURE_CURRENT_POINTER)


def _feature_manifest_v2_path(path: str, commit_id: str) -> str:
    return os.path.join(_feature_manifests_dir(path), f"{commit_id}.json")


def _new_feature_commit_id(seed: str) -> str:
    return hashlib.sha256(
        f"{seed}|{time.time_ns()}|{os.getpid()}".encode("utf-8")
    ).hexdigest()[:16]


def _normalize_commit_id(commit_id: str) -> str:
    token = str(commit_id or "").strip()
    if token == "" or not token.replace("-", "").replace("_", "").isalnum():
        raise RuntimeError(f"Invalid feature commit id token: {commit_id}")
    return token


def _assert_same_filesystem_for_replace(src_path: str, dst_path: str) -> None:
    src_dir = os.path.dirname(src_path) or "."
    dst_dir = os.path.dirname(dst_path) or "."
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)
    src_dev = os.stat(src_dir).st_dev
    dst_dev = os.stat(dst_dir).st_dev
    if int(src_dev) != int(dst_dev):
        raise RuntimeError(
            "Atomic replace requires source and destination to share the same filesystem "
            f"(src={src_dir}, dst={dst_dir})."
        )


def _compute_file_sha256(path: str) -> str:
    abs_path = os.path.abspath(path)
    stat = os.stat(abs_path)
    cached = _FILE_HASH_CACHE.get(abs_path)
    if cached is not None and int(cached[0]) == int(stat.st_mtime_ns) and int(cached[1]) == int(stat.st_size):
        return str(cached[2])
    digest = hashlib.sha256()
    with open(abs_path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    out = digest.hexdigest()
    _FILE_HASH_CACHE[abs_path] = (int(stat.st_mtime_ns), int(stat.st_size), out)
    return out


def _build_manifest_partition_entry(abs_file_path: str) -> dict[str, object]:
    stat = os.stat(abs_file_path)
    return {
        "file": os.path.abspath(abs_file_path),
        "sha256": _compute_file_sha256(abs_file_path),
        "size_bytes": int(stat.st_size),
    }


def _versioned_partition_abs_path(dataset_root: str, commit_id: str, partition_relpath: str) -> str:
    rel = str(partition_relpath).replace("\\", "/").strip("/")
    return os.path.join(_feature_versions_root(dataset_root), commit_id, *rel.split("/"), "part-000.parquet")


def _write_json_atomic(path: str, obj: dict[str, object]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    _assert_same_filesystem_for_replace(temp_path, path)
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, sort_keys=True)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            _safe_remove_path(temp_path)


def _write_text_atomic(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    _assert_same_filesystem_for_replace(temp_path, path)
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(str(text))
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            _safe_remove_path(temp_path)


def _read_current_commit_id(path: str) -> str | None:
    pointer_candidates = [
        _feature_current_pointer_path(path),
        os.path.join(path, FEATURE_CURRENT_POINTER),  # legacy root pointer path
    ]
    for pointer_path in pointer_candidates:
        if not os.path.exists(pointer_path):
            continue
        try:
            with open(pointer_path, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except OSError:
            continue
        if token == "":
            continue
        return _normalize_commit_id(token)
    return None


def _set_feature_current_commit(
    path: str,
    commit_id: str,
    *,
    expected_lock_token: str | None = None,
) -> None:
    token = _normalize_commit_id(commit_id)
    manifest_path = _feature_manifest_v2_path(path, token)
    if not os.path.exists(manifest_path):
        raise RuntimeError(f"Cannot point CURRENT to missing manifest: {manifest_path}")
    _assert_feature_write_lock(expected_token=expected_lock_token)
    pointer_path = _feature_current_pointer_path(path)
    _write_text_atomic(pointer_path, f"{token}\n")
    legacy_pointer = os.path.join(path, FEATURE_CURRENT_POINTER)
    if os.path.exists(legacy_pointer):
        _safe_remove_path(legacy_pointer)


def _scan_current_partition_files(path: str) -> dict[str, str]:
    pattern = os.path.join(
        path,
        f"{FEATURE_PARTITION_YEAR_COL}=*",
        f"{FEATURE_PARTITION_MONTH_COL}=*",
        "*.parquet",
    )
    files_by_partition: dict[str, list[str]] = {}
    for file_path in glob.glob(pattern):
        rel = os.path.relpath(file_path, start=path).replace("\\", "/")
        parts = rel.split("/")
        if len(parts) < 3:
            continue
        year_token = str(parts[0]).strip()
        month_token = str(parts[1]).strip()
        if not year_token.startswith(f"{FEATURE_PARTITION_YEAR_COL}="):
            continue
        if not month_token.startswith(f"{FEATURE_PARTITION_MONTH_COL}="):
            continue
        partition = f"{year_token}/{month_token}"
        files_by_partition.setdefault(partition, []).append(str(file_path))
    if not files_by_partition:
        return {}
    ambiguous = {
        partition: sorted({str(item) for item in files})
        for partition, files in files_by_partition.items()
        if len({str(item) for item in files}) != 1
    }
    if ambiguous:
        details = "; ".join(
            f"{partition} -> {len(files)} files"
            for partition, files in sorted(ambiguous.items())
        )
        raise AmbiguousFeatureStoreStateError(
            "Ambiguous feature-store partition state detected; refusing non-deterministic bootstrap "
            f"({details})."
        )
    return {
        partition: str(sorted({str(item) for item in files})[0])
        for partition, files in sorted(files_by_partition.items())
    }


def _link_or_copy_atomic(src_path: str, dst_path: str) -> None:
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    stage_path = f"{dst_path}.{os.getpid()}.{int(time.time() * 1000)}.stage"
    _assert_same_filesystem_for_replace(stage_path, dst_path)
    try:
        try:
            os.link(src_path, stage_path)
        except OSError:
            shutil.copy2(src_path, stage_path)
        os.replace(stage_path, dst_path)
    finally:
        if os.path.exists(stage_path):
            _safe_remove_path(stage_path)


def _bootstrap_feature_manifest_v2(
    path: str,
    *,
    commit_mode: str = "bootstrap_v2",
    status: dict | None = None,
    expected_lock_token: str | None = None,
    allow_unsealed_bootstrap: bool = False,
) -> dict[str, object] | None:
    if not os.path.isdir(path):
        return None
    current_id = _read_current_commit_id(path)
    if current_id:
        manifest_path = _feature_manifest_v2_path(path, current_id)
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if isinstance(obj, dict):
                    return obj
            except (OSError, json.JSONDecodeError):
                pass
    if not bool(allow_unsealed_bootstrap):
        raise AmbiguousFeatureStoreStateError(
            "Feature manifest bootstrap blocked: missing CURRENT pointer/manifest lineage "
            "for existing partitioned dataset."
        )

    partition_files = _scan_current_partition_files(path)
    if not partition_files:
        return None

    commit_id = _new_feature_commit_id(f"{path}|{commit_mode}|bootstrap")
    partitions: dict[str, dict[str, object]] = {}
    touched = sorted(partition_files.keys())
    for partition, src_file in partition_files.items():
        immutable_path = _versioned_partition_abs_path(path, commit_id, partition)
        _link_or_copy_atomic(src_file, immutable_path)
        partitions[partition] = _build_manifest_partition_entry(immutable_path)
        _refresh_current_partition_cache(path, partition, immutable_path)

    manifest = {
        "version": FEATURE_MANIFEST_VERSION_V2,
        "commit_id": commit_id,
        "commit_mode": str(commit_mode),
        "committed_at_utc": pd.Timestamp.utcnow().isoformat(),
        "cache_policy": dict(FEATURE_CACHE_POLICY),
        "gc_policy": {"retention_hours_min": int(FEATURE_GC_RETENTION_HOURS_MIN)},
        "touched_partitions": touched,
        "tombstones": [],
        "partitions": partitions,
        "previous_commit_id": None,
    }
    _write_json_atomic(_feature_manifest_v2_path(path, commit_id), manifest)
    _set_feature_current_commit(path, commit_id, expected_lock_token=expected_lock_token)
    if status is not None:
        _warn(status, f"Initialized feature manifest v2 current={commit_id}.")
    return manifest


def _update_lock_owner_live(*, allow_self_owner: bool = False) -> bool:
    lock_path = str(getattr(updater, "UPDATE_LOCK_PATH", "")).strip()
    if not lock_path or not os.path.exists(lock_path):
        return False
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            payload_raw = f.read().strip()
        lock_pid, _lock_ts, _token = updater._parse_lock_payload(payload_raw)
    except Exception:
        # Conservative: do not perform read-side recovery while lock ownership is ambiguous.
        return True
    if int(lock_pid) <= 0:
        return True
    if allow_self_owner and int(lock_pid) == int(os.getpid()):
        return False
    return bool(updater._pid_is_running(int(lock_pid)))


def _assert_feature_write_lock(*, expected_token: str | None = None) -> None:
    lock_path = str(getattr(updater, "UPDATE_LOCK_PATH", "")).strip()
    token = str(expected_token or "").strip()
    if lock_path == "":
        if token:
            raise RuntimeError("Feature publish lock path is unavailable for token validation.")
        return
    if not os.path.exists(lock_path):
        if token:
            raise RuntimeError("Feature publish lock token provided but lock file is missing.")
        return
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            payload_raw = f.read().strip()
    except OSError as exc:
        raise RuntimeError("Feature publish lock file is unreadable.") from exc
    _lock_pid, _lock_ts, live_token = updater._parse_lock_payload(payload_raw)
    live_token = str(live_token or "").strip()
    if live_token == "":
        raise RuntimeError("Feature publish blocked: lock file has no ownership token.")
    if token == "":
        raise RuntimeError("Feature publish blocked: missing lock token.")
    if token != live_token:
        raise RuntimeError("Feature publish blocked: lock token mismatch.")


def _recover_atomic_replace_backups(path: str, status: dict | None = None) -> bool:
    backup_paths: list[tuple[float, str]] = []
    for candidate in glob.glob(f"{path}.bak.*"):
        try:
            backup_paths.append((float(os.path.getmtime(candidate)), candidate))
        except OSError:
            continue
    if not backup_paths:
        return False
    backup_paths.sort(key=lambda row: (row[0], row[1]), reverse=True)
    backups = [row[1] for row in backup_paths]
    if os.path.exists(path):
        for stale in backups:
            _safe_remove_path(stale)
        return True
    if _update_lock_owner_live(allow_self_owner=True):
        return False

    restore_from = backups[0]
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    os.replace(restore_from, path)
    for stale in backups[1:]:
        _safe_remove_path(stale)
    msg = f"Recovered interrupted feature-store atomic swap path={path} from backup={restore_from}"
    if status is not None:
        _warn(status, msg)
    else:
        logger.warning(msg)
    return True


def _read_feature_manifest(path: str) -> dict[str, object] | None:
    _recover_atomic_replace_backups(path)
    if not os.path.isdir(path):
        return None
    current_commit = _read_current_commit_id(path)
    if current_commit:
        v2_path = _feature_manifest_v2_path(path, current_commit)
        if not os.path.exists(v2_path):
            raise RuntimeError(f"Feature CURRENT pointer references missing manifest: {v2_path}")
        try:
            with open(v2_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Invalid feature commit manifest: {v2_path}") from exc
        if not isinstance(obj, dict):
            raise RuntimeError(f"Feature commit manifest must be a JSON object: {v2_path}")
        commit_id = str(obj.get("commit_id") or "").strip()
        if commit_id != current_commit:
            raise RuntimeError(
                "Feature CURRENT pointer/manifest mismatch "
                f"(pointer={current_commit}, manifest={commit_id or 'missing'})."
            )
        return obj

    manifest_path = _feature_manifest_path(path)
    if not os.path.exists(manifest_path):
        return None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return obj if isinstance(obj, dict) else None


def _validate_feature_manifest_policy(path: str, manifest: dict[str, object] | None = None) -> None:
    if manifest is None:
        manifest = _read_feature_manifest(path)
    if manifest is None:
        if os.path.isdir(path):
            raise RuntimeError("Feature manifest is required for partitioned dataset reads.")
        return
    cache_policy = manifest.get("cache_policy")
    if not isinstance(cache_policy, dict):
        raise RuntimeError("Feature commit manifest missing cache_policy contract.")
    swr = int(cache_policy.get("stale_while_revalidate_sec", -1))
    tombstone_priority = str(cache_policy.get("tombstone_priority", "")).strip().lower()
    if swr != 0:
        raise RuntimeError("Feature commit manifest must enforce stale_while_revalidate_sec=0.")
    if tombstone_priority != "enforced":
        raise RuntimeError("Feature commit manifest must enforce tombstone_priority='enforced'.")
    version = str(manifest.get("version") or "").strip().lower()
    if version == FEATURE_MANIFEST_VERSION_V2:
        gc_policy = manifest.get("gc_policy")
        if not isinstance(gc_policy, dict):
            raise RuntimeError("Feature manifest v2 missing gc_policy contract.")
        retention_h = int(gc_policy.get("retention_hours_min", -1))
        if retention_h < int(FEATURE_GC_RETENTION_HOURS_MIN):
            raise RuntimeError(
                f"Feature manifest v2 requires retention_hours_min >= {FEATURE_GC_RETENTION_HOURS_MIN}."
            )


def _manifest_active_files(path: str, manifest: dict[str, object]) -> list[str]:
    version = str(manifest.get("version") or "").strip().lower()
    if version != FEATURE_MANIFEST_VERSION_V2:
        return []
    raw_parts = manifest.get("partitions")
    if not isinstance(raw_parts, dict):
        raise RuntimeError("Feature manifest v2 missing partitions map.")
    files: list[str] = []
    for partition in sorted(raw_parts.keys()):
        entry = raw_parts.get(partition)
        if not isinstance(entry, dict):
            raise RuntimeError(f"Invalid manifest partition entry: {partition}")
        file_path = str(entry.get("file") or "").strip()
        if file_path == "":
            raise RuntimeError(f"Manifest partition entry missing file path: {partition}")
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(path, file_path)
        files.append(os.path.abspath(abs_path))
    return files


def _partition_relpath_from_file_path(file_path: str) -> str:
    parts = [p for p in str(file_path).replace("\\", "/").split("/") if p]
    year_idx = -1
    for idx, token in enumerate(parts):
        if str(token).startswith(f"{FEATURE_PARTITION_YEAR_COL}="):
            year_idx = idx
            break
    if year_idx < 0 or year_idx + 1 >= len(parts):
        raise RuntimeError(f"Unable to derive partition from file path: {file_path}")
    year_token = str(parts[year_idx]).split("=", 1)[1]
    month_full = str(parts[year_idx + 1])
    if not month_full.startswith(f"{FEATURE_PARTITION_MONTH_COL}="):
        raise RuntimeError(f"Unable to derive month partition from file path: {file_path}")
    month_token = month_full.split("=", 1)[1]
    return _partition_relpath(
        _normalize_feature_partition_value(year_token),
        _normalize_feature_partition_value(month_token),
    )


def _validate_feature_manifest_hashes(path: str, manifest: dict[str, object]) -> None:
    version = str(manifest.get("version") or "").strip().lower()
    if version != FEATURE_MANIFEST_VERSION_V2:
        return
    raw_parts = manifest.get("partitions")
    if not isinstance(raw_parts, dict):
        raise RuntimeError("Feature manifest v2 missing partitions map for hash verification.")
    for partition in sorted(raw_parts.keys()):
        entry = raw_parts.get(partition)
        if not isinstance(entry, dict):
            raise RuntimeError(f"Invalid manifest partition entry: {partition}")
        expected = str(entry.get("sha256") or "").strip().lower()
        if len(expected) != 64:
            raise RuntimeError(f"Manifest partition entry missing sha256 seal: {partition}")
        file_path = str(entry.get("file") or "").strip()
        if file_path == "":
            raise RuntimeError(f"Manifest partition entry missing file path: {partition}")
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(path, file_path)
        abs_path = os.path.abspath(abs_path)
        derived_partition = _partition_relpath_from_file_path(abs_path)
        if str(partition) != str(derived_partition):
            raise RuntimeError(
                "Manifest partition/file mismatch "
                f"(manifest={partition}, derived={derived_partition}, file={abs_path})."
            )
        if not os.path.exists(abs_path):
            raise RuntimeError(f"Manifest partition file missing: {abs_path}")
        actual = _compute_file_sha256(abs_path)
        if actual.lower() != expected:
            raise RuntimeError(
                "Manifest partition hash mismatch "
                f"(partition={partition}, expected={expected}, actual={actual})."
            )


def _validate_feature_manifest_tombstones(path: str, manifest: dict[str, object]) -> None:
    version = str(manifest.get("version") or "").strip().lower()
    if version != FEATURE_MANIFEST_VERSION_V2:
        return
    raw_parts = manifest.get("partitions")
    if not isinstance(raw_parts, dict):
        raise RuntimeError("Feature manifest v2 missing partitions map for tombstone checks.")
    tombstones_raw = manifest.get("tombstones")
    tombstones = tombstones_raw if isinstance(tombstones_raw, list) else []

    active_files: set[str] = set()
    for partition in sorted(raw_parts.keys()):
        entry = raw_parts.get(partition)
        if not isinstance(entry, dict):
            raise RuntimeError(f"Invalid manifest partition entry: {partition}")
        file_path = str(entry.get("file") or "").strip()
        if file_path == "":
            raise RuntimeError(f"Manifest partition entry missing file path: {partition}")
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(path, file_path)
        active_files.add(os.path.abspath(abs_path))

    tombstoned_files: set[str] = set()
    for idx, row in enumerate(tombstones):
        if not isinstance(row, dict):
            raise RuntimeError(f"Invalid tombstone entry at index={idx}.")
        file_path = str(row.get("file") or "").strip()
        retained = str(row.get("retained_until_utc") or "").strip()
        if file_path == "":
            raise RuntimeError(f"Manifest tombstone missing file path at index={idx}.")
        if retained == "":
            raise RuntimeError(f"Manifest tombstone missing retained_until_utc at index={idx}.")
        try:
            parsed_retained = pd.Timestamp(retained)
        except Exception as exc:
            raise RuntimeError(f"Manifest tombstone retained_until_utc invalid at index={idx}.") from exc
        if not isinstance(parsed_retained, pd.Timestamp) or pd.isna(parsed_retained):
            raise RuntimeError(f"Manifest tombstone retained_until_utc invalid at index={idx}.")
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(path, file_path)
        tombstoned_files.add(os.path.abspath(abs_path))

    overlap = sorted(active_files.intersection(tombstoned_files))
    if overlap:
        raise RuntimeError(
            "Feature manifest violates tombstone_priority='enforced': "
            "active partition file is tombstoned."
        )


def _partition_relpath(year_val: str, month_val: str) -> str:
    return os.path.join(
        f"{FEATURE_PARTITION_YEAR_COL}={year_val}",
        f"{FEATURE_PARTITION_MONTH_COL}={month_val}",
    ).replace("\\", "/")


def _write_feature_commit_manifest(
    dataset_root: str,
    *,
    commit_mode: str,
    touched_partitions: list[str],
    previous_commit_id: str | None = None,
) -> str:
    commit_id = hashlib.sha256(
        f"{dataset_root}|{commit_mode}|{time.time_ns()}|{os.getpid()}".encode("utf-8")
    ).hexdigest()[:16]
    tombstones = [
        {
            "partition": str(part),
            "reason": "replaced_partition",
            "cache_policy": "tombstone_over_cache",
        }
        for part in sorted({str(p) for p in touched_partitions if str(p).strip()})
    ]
    manifest = {
        "version": "v1",
        "commit_id": commit_id,
        "commit_mode": str(commit_mode),
        "committed_at_utc": pd.Timestamp.utcnow().isoformat(),
        "cache_policy": dict(FEATURE_CACHE_POLICY),
        "tombstones": tombstones,
        "touched_partitions": sorted({str(p) for p in touched_partitions if str(p).strip()}),
        "previous_commit_id": previous_commit_id,
    }
    manifest_path = _feature_manifest_path(dataset_root)
    temp_path = f"{manifest_path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        os.replace(temp_path, manifest_path)
    finally:
        if os.path.exists(temp_path):
            _safe_remove_path(temp_path)
    return commit_id


def _feature_store_scan_sql(path: str) -> str:
    _recover_atomic_replace_backups(path)
    if os.path.isdir(path):
        manifest = _read_feature_manifest(path)
        _validate_feature_manifest_policy(path, manifest=manifest)
        if not isinstance(manifest, dict):
            raise RuntimeError("Feature manifest is required for partitioned dataset reads.")
        version = str(manifest.get("version") or "").strip().lower()
        if version != FEATURE_MANIFEST_VERSION_V2:
            raise RuntimeError(
                f"Feature manifest v2 is required for partitioned dataset reads (got version={version or 'missing'})."
            )
        _validate_feature_manifest_hashes(path, manifest)
        _validate_feature_manifest_tombstones(path, manifest)
        files = _manifest_active_files(path, manifest)
        if not files:
            raise RuntimeError("Feature manifest v2 contains no active parquet files.")
        escaped_files = ", ".join(f"'{_sql_escape_path(file_path)}'" for file_path in files)
        return f"read_parquet([{escaped_files}], hive_partitioning=1)"
    return f"read_parquet('{_sql_escape_path(_feature_store_scan_glob(path))}', hive_partitioning=1)"


def _safe_remove_path(path: str) -> None:
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            os.remove(path)
        except OSError:
            pass


def _atomic_replace_path(src_path: str, dst_path: str) -> None:
    _recover_atomic_replace_backups(dst_path)
    _assert_same_filesystem_for_replace(src_path, dst_path)
    backup_path = f"{dst_path}.bak.{os.getpid()}.{int(time.time() * 1000)}"
    backup_created = False
    try:
        if os.path.exists(dst_path):
            os.replace(dst_path, backup_path)
            backup_created = True
        os.replace(src_path, dst_path)
        if backup_created:
            _safe_remove_path(backup_path)
    except Exception:
        if os.path.exists(src_path):
            _safe_remove_path(src_path)
        if backup_created and not os.path.exists(dst_path) and os.path.exists(backup_path):
            os.replace(backup_path, dst_path)
        raise


def _prepare_feature_rows_for_partitioning(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date", "permno"])
    out[FEATURE_PARTITION_YEAR_COL] = out["date"].dt.year.astype("Int64").astype(str)
    out[FEATURE_PARTITION_MONTH_COL] = out["date"].dt.month.astype("Int64").map(lambda x: f"{int(x):02d}")
    return out


def _write_partitioned_feature_dataset(
    df: pd.DataFrame,
    output_path: str,
    *,
    expected_lock_token: str | None = None,
) -> None:
    work = _prepare_feature_rows_for_partitioning(df)
    stage_dir = f"{output_path}.{os.getpid()}.{int(time.time() * 1000)}.partition_stage"
    previous_commit_id = None
    prior_manifest = _read_feature_manifest(output_path)
    if prior_manifest is not None:
        previous_commit_id = str(prior_manifest.get("commit_id") or "").strip() or None
    touched_partitions: list[str] = []
    if not work.empty:
        parts = (
            work[[FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL]]
            .drop_duplicates()
            .sort_values([FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL])
        )
        touched_partitions = [
            _partition_relpath(
                str(row[FEATURE_PARTITION_YEAR_COL]),
                str(row[FEATURE_PARTITION_MONTH_COL]),
            )
            for _, row in parts.iterrows()
        ]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    try:
        work.to_parquet(stage_dir, index=False, partition_cols=list(FEATURE_PARTITION_COLUMNS))
        _write_feature_commit_manifest(
            stage_dir,
            commit_mode="full_rebuild",
            touched_partitions=touched_partitions,
            previous_commit_id=previous_commit_id,
        )
        _atomic_replace_path(stage_dir, output_path)
        _bootstrap_feature_manifest_v2(
            output_path,
            commit_mode="full_rebuild",
            expected_lock_token=expected_lock_token,
            allow_unsealed_bootstrap=True,
        )
    finally:
        if os.path.exists(stage_dir):
            _safe_remove_path(stage_dir)


def _normalize_feature_partition_value(raw: str | int) -> str:
    text = str(raw).strip()
    if text == "":
        raise ValueError(f"Invalid partition value: {raw}")
    if len(text) <= 2:
        return f"{int(float(text)):02d}"
    return str(int(float(text)))


def _ensure_partitioned_feature_store(
    path: str,
    status: dict | None = None,
    *,
    expected_lock_token: str | None = None,
) -> None:
    _recover_atomic_replace_backups(path, status=status)
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        _bootstrap_feature_manifest_v2(
            path,
            commit_mode="upgrade_v2",
            status=status,
            expected_lock_token=expected_lock_token,
        )
        return
    if status is not None:
        _warn(status, "Migrating legacy single-file features.parquet to partitioned year/month dataset.")
    legacy_df = pd.read_parquet(path)
    _write_partitioned_feature_dataset(legacy_df, path, expected_lock_token=expected_lock_token)


def _load_feature_partition_slices(
    path: str,
    partition_pairs: pd.DataFrame,
    columns: list[str],
    con: duckdb.DuckDBPyConnection,
) -> dict[tuple[str, str], pd.DataFrame]:
    if not os.path.exists(path) or partition_pairs.empty:
        return {}
    keys = partition_pairs[[FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL]].copy()
    keys[FEATURE_PARTITION_YEAR_COL] = keys[FEATURE_PARTITION_YEAR_COL].map(_normalize_feature_partition_value)
    keys[FEATURE_PARTITION_MONTH_COL] = keys[FEATURE_PARTITION_MONTH_COL].map(_normalize_feature_partition_value)
    keys = keys.drop_duplicates().reset_index(drop=True)
    if keys.empty:
        return {}

    select_cols = ", ".join([f'fs."{c}"' for c in columns])
    con.register("feature_partition_keys", keys)
    try:
        df = con.execute(
            f"""
            SELECT
                {select_cols},
                CAST(fs.{FEATURE_PARTITION_YEAR_COL} AS VARCHAR) AS _part_year,
                LPAD(CAST(fs.{FEATURE_PARTITION_MONTH_COL} AS VARCHAR), 2, '0') AS _part_month
            FROM {_feature_store_scan_sql(path)} AS fs
            INNER JOIN feature_partition_keys AS fk
                ON CAST(fs.{FEATURE_PARTITION_YEAR_COL} AS VARCHAR) = fk.{FEATURE_PARTITION_YEAR_COL}
               AND LPAD(CAST(fs.{FEATURE_PARTITION_MONTH_COL} AS VARCHAR), 2, '0') = fk.{FEATURE_PARTITION_MONTH_COL}
            """
        ).df()
    finally:
        con.unregister("feature_partition_keys")

    if df.empty:
        return {}

    out: dict[tuple[str, str], pd.DataFrame] = {}
    for (year_val, month_val), grp in df.groupby(["_part_year", "_part_month"], sort=True):
        out[(str(year_val), str(month_val))] = grp.drop(columns=["_part_year", "_part_month"]).reset_index(drop=True)
    return out


def _iter_partition_pair_chunks(partition_pairs: pd.DataFrame, chunk_size: int):
    if partition_pairs.empty:
        return
    chunk = max(1, int(chunk_size))
    total = int(len(partition_pairs))
    for start in range(0, total, chunk):
        yield partition_pairs.iloc[start:start + chunk].reset_index(drop=True)


def _write_single_partition(path: str, year_val: str, month_val: str, partition_df: pd.DataFrame) -> None:
    year_dir = os.path.join(path, f"{FEATURE_PARTITION_YEAR_COL}={year_val}")
    target_partition_dir = os.path.join(year_dir, f"{FEATURE_PARTITION_MONTH_COL}={month_val}")
    stage_partition_dir = (
        f"{target_partition_dir}.stage.{os.getpid()}.{int(time.time() * 1000)}"
    )
    os.makedirs(stage_partition_dir, exist_ok=True)
    stage_file = os.path.join(stage_partition_dir, "part-000.parquet")
    try:
        partition_df.to_parquet(stage_file, index=False)
        os.makedirs(year_dir, exist_ok=True)
        _atomic_replace_path(stage_partition_dir, target_partition_dir)
    finally:
        if os.path.exists(stage_partition_dir):
            _safe_remove_path(stage_partition_dir)


def _write_partition_file_atomic(partition_df: pd.DataFrame, abs_file_path: str) -> None:
    os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
    stage_file = f"{abs_file_path}.{os.getpid()}.{int(time.time() * 1000)}.stage"
    _assert_same_filesystem_for_replace(stage_file, abs_file_path)
    try:
        partition_df.to_parquet(stage_file, index=False)
        os.replace(stage_file, abs_file_path)
    finally:
        if os.path.exists(stage_file):
            _safe_remove_path(stage_file)


def _atomic_replace_file(src_file: str, dst_file: str) -> None:
    _recover_atomic_replace_backups(dst_file)
    _assert_same_filesystem_for_replace(src_file, dst_file)
    backup_file = f"{dst_file}.bak.{os.getpid()}.{int(time.time() * 1000)}"
    backup_created = False
    try:
        if os.path.exists(dst_file):
            os.replace(dst_file, backup_file)
            backup_created = True
        os.replace(src_file, dst_file)
        if backup_created:
            _safe_remove_path(backup_file)
    except Exception:
        if os.path.exists(src_file):
            _safe_remove_path(src_file)
        if backup_created and not os.path.exists(dst_file) and os.path.exists(backup_file):
            os.replace(backup_file, dst_file)
        raise


def _refresh_current_partition_cache(
    dataset_root: str,
    partition_relpath: str,
    source_file_path: str,
) -> None:
    part = str(partition_relpath).replace("\\", "/").strip("/")
    target_dir = os.path.join(dataset_root, *part.split("/"))
    os.makedirs(target_dir, exist_ok=True)
    target_file = os.path.join(target_dir, "part-000.parquet")
    stage_file = f"{target_file}.{os.getpid()}.{int(time.time() * 1000)}.stage"
    _link_or_copy_atomic(source_file_path, stage_file)
    _atomic_replace_file(stage_file, target_file)
    for candidate in glob.glob(os.path.join(target_dir, "*.parquet")):
        if os.path.abspath(candidate) == os.path.abspath(target_file):
            continue
        _safe_remove_path(candidate)


def _build_feature_manifest_v2(
    *,
    commit_id: str,
    commit_mode: str,
    previous_commit_id: str | None,
    touched_partitions: list[str],
    tombstones: list[dict[str, object]],
    partitions: dict[str, dict[str, object]],
) -> dict[str, object]:
    return {
        "version": FEATURE_MANIFEST_VERSION_V2,
        "commit_id": str(commit_id),
        "commit_mode": str(commit_mode),
        "committed_at_utc": pd.Timestamp.utcnow().isoformat(),
        "cache_policy": dict(FEATURE_CACHE_POLICY),
        "gc_policy": {"retention_hours_min": int(FEATURE_GC_RETENTION_HOURS_MIN)},
        "touched_partitions": sorted({str(p) for p in touched_partitions if str(p).strip()}),
        "tombstones": list(tombstones),
        "partitions": dict(partitions),
        "previous_commit_id": previous_commit_id,
    }


def _normalize_universe_mode(universe_mode: str) -> str:
    mode = str(universe_mode or "").strip().lower()
    if mode not in UNIVERSE_MODES:
        raise ValueError(f"Unsupported universe mode: {universe_mode}")
    return mode


def _normalize_cs_scale_mode(mode: str) -> str:
    val = str(mode or "").strip().lower()
    if val not in CS_SCALE_MODES:
        raise ValueError(f"Unsupported cross-sectional scale mode: {mode}")
    return val


def _estimate_wide_matrix_gb(n_dates: int, n_assets: int) -> float:
    return (float(n_dates) * float(n_assets) * 8.0 * 16.0) / 1_000_000_000.0


def _default_incremental_warmup_bdays(cfg: FeatureStoreConfig) -> int:
    longest = max(
        int(cfg.beta_window),
        int(cfg.resid_mom_window),
        int(cfg.rel_strength_window),
        int(cfg.amihud_window),
        int(cfg.yz_window),
        int(cfg.atr_window),
        int(cfg.rsi_window),
        int(cfg.sma_short_window),
        int(cfg.sma_trend_window),
    )
    return max(20, int(longest + 10))


def _read_feature_date_bounds(path: str) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
    if not os.path.exists(path):
        return None, None
    con = duckdb.connect()
    try:
        row = con.execute(
            f"""
            SELECT
                MIN(CAST(date AS DATE)) AS min_date,
                MAX(CAST(date AS DATE)) AS max_date
            FROM {_feature_store_scan_sql(path)}
            """
        ).fetchone()
    finally:
        con.close()
    if not row:
        return None, None
    min_dt = pd.to_datetime(row[0], errors="coerce") if row[0] is not None else None
    max_dt = pd.to_datetime(row[1], errors="coerce") if row[1] is not None else None
    min_ts = min_dt.normalize() if isinstance(min_dt, pd.Timestamp) and not pd.isna(min_dt) else None
    max_ts = max_dt.normalize() if isinstance(max_dt, pd.Timestamp) and not pd.isna(max_dt) else None
    return min_ts, max_ts


def _count_rows(path: str) -> int:
    if not os.path.exists(path):
        return 0
    con = duckdb.connect()
    try:
        row = con.execute(f"SELECT COUNT(*) FROM {_feature_store_scan_sql(path)}").fetchone()
    finally:
        con.close()
    return int(row[0]) if row and row[0] is not None else 0


def _read_parquet_columns(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    con = duckdb.connect()
    try:
        df = con.execute(f"DESCRIBE SELECT * FROM {_feature_store_scan_sql(path)}").df()
    finally:
        con.close()
    if df.empty:
        return set()
    return {str(c) for c in df["column_name"].tolist()}


def _hash_permnos(permnos: list[int]) -> str:
    h = hashlib.sha256()
    for p in permnos:
        h.update(f"{int(p)},".encode("utf-8"))
    return h.hexdigest()


def _file_fingerprint(path: str) -> dict[str, int | bool]:
    if not os.path.exists(path):
        return {"exists": False, "size": 0, "mtime_ns": 0}
    st = os.stat(path)
    return {"exists": True, "size": int(st.st_size), "mtime_ns": int(st.st_mtime_ns)}


def _feature_spec_hash(specs: list[FeatureSpec]) -> str:
    return compute_registry_hash(specs)


def _build_cache_key(
    cfg: FeatureStoreConfig,
    specs: list[FeatureSpec],
    permnos: list[int],
    effective_start_ts: pd.Timestamp,
    end_ts: pd.Timestamp | None,
    incremental_active: bool,
    append_start_ts: pd.Timestamp,
) -> str:
    src_cfg = _price_source_config()
    macro_source = _macro_source_path()
    payload = {
        "cfg": {
            "start_year": int(cfg.start_year),
            "top_n": int(cfg.top_n),
            "universe_mode": str(cfg.universe_mode),
            "yearly_top_n": int(cfg.yearly_top_n),
            "beta_window": int(cfg.beta_window),
            "resid_mom_window": int(cfg.resid_mom_window),
            "rel_strength_window": int(cfg.rel_strength_window),
            "amihud_window": int(cfg.amihud_window),
            "yz_window": int(cfg.yz_window),
            "atr_window": int(cfg.atr_window),
            "rsi_window": int(cfg.rsi_window),
            "sma_short_window": int(cfg.sma_short_window),
            "sma_trend_window": int(cfg.sma_trend_window),
            "cs_scale_mode": str(cfg.cs_scale_mode),
            "cs_scale_epsilon_floor": float(cfg.cs_scale_epsilon_floor),
            "cs_scale_min_window_size": int(cfg.cs_scale_min_window_size),
        },
        "spec_hash": _feature_spec_hash(specs),
        "permno_count": int(len(permnos)),
        "permno_hash": _hash_permnos(permnos),
        "effective_start": pd.Timestamp(effective_start_ts).strftime("%Y-%m-%d"),
        "append_start": pd.Timestamp(append_start_ts).strftime("%Y-%m-%d"),
        "end": pd.Timestamp(end_ts).strftime("%Y-%m-%d") if end_ts is not None else None,
        "incremental_active": bool(incremental_active),
        "inputs": {
            "prices": _file_fingerprint(str(src_cfg["base"])),
            "patch": _file_fingerprint(str(src_cfg["patch"])) if src_cfg["patch"] else {"exists": False, "size": 0, "mtime_ns": 0},
            "prices_tri": _file_fingerprint(PRICES_TRI_PATH),
            "macro_features": _file_fingerprint(macro_source),
            "macro_features_tri": _file_fingerprint(MACRO_FEATURES_TRI_PATH),
            "fundamentals": _file_fingerprint(FUNDAMENTALS_PATH),
            "fundamentals_snapshot": _file_fingerprint(FUNDAMENTALS_SNAPSHOT_PATH),
            "tickers": _file_fingerprint(TICKERS_PATH),
        },
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def _load_existing_feature_permnos(path: str) -> list[int]:
    if not os.path.exists(path):
        return []
    con = duckdb.connect()
    try:
        df = con.execute(
            f"""
            SELECT DISTINCT CAST(permno AS BIGINT) AS permno
            FROM {_feature_store_scan_sql(path)}
            WHERE permno IS NOT NULL
            ORDER BY permno
            """
        ).df()
    finally:
        con.close()
    if df.empty:
        return []
    return [int(x) for x in df["permno"].tolist()]


def _atomic_upsert_features(
    existing_path: str,
    new_rows: pd.DataFrame,
    output_path: str,
    status: dict | None = None,
    upsert_chunk_size: int = 50,
    expected_lock_token: str | None = None,
):
    if new_rows.empty:
        return
    _assert_feature_write_lock(expected_token=expected_lock_token)
    _recover_atomic_replace_backups(existing_path, status=status)
    if existing_path != output_path:
        _recover_atomic_replace_backups(output_path, status=status)
    if os.path.abspath(existing_path) != os.path.abspath(output_path):
        raise RuntimeError("Manifest v2 upsert requires existing_path and output_path to be identical.")
    cols = [str(c) for c in new_rows.columns]
    work = _prepare_feature_rows_for_partitioning(new_rows[cols])
    if work.empty:
        return

    _ensure_partitioned_feature_store(
        existing_path,
        status=status,
        expected_lock_token=expected_lock_token,
    )
    if existing_path != output_path and os.path.exists(existing_path):
        _ensure_partitioned_feature_store(
            output_path,
            status=status,
            expected_lock_token=expected_lock_token,
        )

    if not os.path.exists(existing_path):
        _write_partitioned_feature_dataset(
            work[cols],
            output_path,
            expected_lock_token=expected_lock_token,
        )
        return

    manifest = _read_feature_manifest(output_path)
    if not isinstance(manifest, dict) or str(manifest.get("version") or "").strip().lower() != FEATURE_MANIFEST_VERSION_V2:
        manifest = _bootstrap_feature_manifest_v2(
            output_path,
            commit_mode="upgrade_v2",
            status=status,
            expected_lock_token=expected_lock_token,
        )
    if not isinstance(manifest, dict) or str(manifest.get("version") or "").strip().lower() != FEATURE_MANIFEST_VERSION_V2:
        raise RuntimeError("Feature manifest v2 initialization failed; cannot continue incremental commit.")

    pairs = (
        work[[FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL]]
        .drop_duplicates()
        .sort_values([FEATURE_PARTITION_YEAR_COL, FEATURE_PARTITION_MONTH_COL])
        .reset_index(drop=True)
    )
    pairs[FEATURE_PARTITION_YEAR_COL] = pairs[FEATURE_PARTITION_YEAR_COL].map(_normalize_feature_partition_value)
    pairs[FEATURE_PARTITION_MONTH_COL] = pairs[FEATURE_PARTITION_MONTH_COL].map(_normalize_feature_partition_value)

    touched_partitions = [
        _partition_relpath(str(row[FEATURE_PARTITION_YEAR_COL]), str(row[FEATURE_PARTITION_MONTH_COL]))
        for _, row in pairs.iterrows()
    ]
    previous_commit_id = str(manifest.get("commit_id") or "").strip() or None
    next_partitions = {
        str(part): dict(meta) if isinstance(meta, dict) else {}
        for part, meta in dict(manifest.get("partitions") or {}).items()
    }
    commit_id = _new_feature_commit_id(
        f"{output_path}|incremental_upsert|{previous_commit_id or 'none'}|{','.join(touched_partitions)}"
    )
    versions_root = _feature_versions_root(output_path)
    os.makedirs(versions_root, exist_ok=True)
    retained_until_utc = (
        pd.Timestamp.utcnow() + pd.Timedelta(hours=int(FEATURE_GC_RETENTION_HOURS_MIN))
    ).isoformat()
    tombstones: list[dict[str, object]] = []
    changed_partition_files: dict[str, str] = {}
    removed_partitions: list[str] = []
    con = duckdb.connect()
    try:
        for pair_chunk in _iter_partition_pair_chunks(pairs, chunk_size=int(upsert_chunk_size)):
            existing_parts = _load_feature_partition_slices(
                path=output_path,
                partition_pairs=pair_chunk,
                columns=cols,
                con=con,
            )
            for _, row in pair_chunk.iterrows():
                year_val = str(row[FEATURE_PARTITION_YEAR_COL])
                month_val = str(row[FEATURE_PARTITION_MONTH_COL])
                partition_relpath = _partition_relpath(year_val, month_val)
                new_part = work[
                    (work[FEATURE_PARTITION_YEAR_COL] == year_val)
                    & (work[FEATURE_PARTITION_MONTH_COL] == month_val)
                ][cols].copy()
                existing_part = existing_parts.get((year_val, month_val), pd.DataFrame(columns=cols))

                merged = pd.concat(
                    [
                        existing_part.assign(_priority=0),
                        new_part.assign(_priority=1),
                    ],
                    ignore_index=True,
                )
                merged["date"] = pd.to_datetime(merged["date"], errors="coerce")
                merged["permno"] = pd.to_numeric(merged["permno"], errors="coerce")
                merged = merged.dropna(subset=["date", "permno"])
                merged = (
                    merged.sort_values(["date", "permno", "_priority"])
                    .drop_duplicates(subset=["date", "permno"], keep="last")
                    .drop(columns=["_priority"])
                    .sort_values(["date", "permno"])
                    .reset_index(drop=True)
                )
                prev_entry = next_partitions.get(partition_relpath, {})
                if merged.empty:
                    if partition_relpath in next_partitions:
                        next_partitions.pop(partition_relpath, None)
                        removed_partitions.append(partition_relpath)
                        old_file = str(prev_entry.get("file") or "").strip() if isinstance(prev_entry, dict) else ""
                        if old_file:
                            tombstones.append(
                                {
                                    "partition": partition_relpath,
                                    "file": old_file,
                                    "reason": "removed_partition",
                                    "retained_until_utc": retained_until_utc,
                                }
                            )
                    continue
                immutable_file = _versioned_partition_abs_path(output_path, commit_id, partition_relpath)
                _write_partition_file_atomic(merged[cols], immutable_file)
                next_entry = _build_manifest_partition_entry(immutable_file)
                next_partitions[partition_relpath] = next_entry
                old_file = str(prev_entry.get("file") or "").strip() if isinstance(prev_entry, dict) else ""
                if old_file and old_file != str(next_entry.get("file") or ""):
                    tombstones.append(
                        {
                            "partition": partition_relpath,
                            "file": old_file,
                            "reason": "replaced_partition",
                            "retained_until_utc": retained_until_utc,
                        }
                    )
                changed_partition_files[partition_relpath] = immutable_file
        if not changed_partition_files and not removed_partitions:
            return

        next_manifest = _build_feature_manifest_v2(
            commit_id=commit_id,
            commit_mode="incremental_upsert",
            previous_commit_id=previous_commit_id,
            touched_partitions=touched_partitions,
            tombstones=tombstones,
            partitions=next_partitions,
        )
        _write_json_atomic(_feature_manifest_v2_path(output_path, commit_id), next_manifest)
        _set_feature_current_commit(
            output_path,
            commit_id,
            expected_lock_token=expected_lock_token,
        )
        for partition_relpath, source_path in changed_partition_files.items():
            _refresh_current_partition_cache(output_path, partition_relpath, source_path)
        for partition_relpath in removed_partitions:
            root_partition_dir = os.path.join(output_path, *partition_relpath.split("/"))
            root_partition_file = os.path.join(root_partition_dir, "part-000.parquet")
            _safe_remove_path(root_partition_file)
            if os.path.isdir(root_partition_dir):
                try:
                    if not os.listdir(root_partition_dir):
                        _safe_remove_path(root_partition_dir)
                except OSError:
                    pass
    finally:
        con.close()
    if status is not None:
        status["feature_commit_id"] = commit_id
        status["feature_touched_partitions"] = touched_partitions


def _top_liquid_permnos(top_n: int) -> list[int]:
    if top_n <= 0:
        return []
    src_cfg = _price_source_config()
    base_path = str(src_cfg["base"])
    patch_path = src_cfg["patch"]
    price_col = str(src_cfg["price_col"])
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Missing prices parquet: {base_path}")

    con = duckdb.connect()
    try:
        if patch_path is not None and os.path.exists(str(patch_path)):
            src = f"""
            (
                SELECT permno, {price_col} AS signal_price, volume FROM '{_sql_escape_path(base_path)}'
                UNION ALL
                SELECT permno, {price_col} AS signal_price, volume FROM '{_sql_escape_path(str(patch_path))}'
            )
            """
        else:
            src = f"(SELECT permno, {price_col} AS signal_price, volume FROM '{_sql_escape_path(base_path)}')"

        q = f"""
            SELECT CAST(permno AS BIGINT) AS permno
            FROM {src}
            WHERE volume > 0 AND signal_price > 0
            GROUP BY permno
            ORDER BY SUM(signal_price * volume) DESC
            LIMIT {int(top_n)}
        """
        df = con.execute(q).df()
    finally:
        con.close()
    if df.empty:
        return []
    return [int(x) for x in df["permno"].tolist()]


def _top_liquid_permnos_yearly_union(
    yearly_top_n: int,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None = None,
) -> list[int]:
    if yearly_top_n <= 0:
        return []
    src_cfg = _price_source_config()
    base_path = str(src_cfg["base"])
    patch_path = src_cfg["patch"]
    price_col = str(src_cfg["price_col"])
    if not os.path.exists(base_path):
        raise FileNotFoundError(f"Missing prices parquet: {base_path}")

    anchor_ts = pd.Timestamp(start_date)
    if anchor_ts.tzinfo is not None:
        anchor_ts = anchor_ts.tz_localize(None)
    if end_date is not None:
        end_ts = pd.Timestamp(end_date)
        if end_ts.tzinfo is not None:
            end_ts = end_ts.tz_localize(None)
        # Defensive clamp for direct helper calls with inconsistent inputs.
        if end_ts < anchor_ts:
            anchor_ts = end_ts
    # Strict PIT guardrail: selector can only consume liquidity observed strictly before start_date (t-1 anchor).
    anchor_ts = anchor_ts.normalize()
    anchor_str = anchor_ts.strftime("%Y-%m-%d")

    con = duckdb.connect()
    try:
        if patch_path is not None and os.path.exists(str(patch_path)):
            q = f"""
                WITH src AS (
                    SELECT CAST(date AS DATE) AS date,
                           CAST(permno AS BIGINT) AS permno,
                           CAST({price_col} AS DOUBLE) AS signal_price,
                           CAST(volume AS DOUBLE) AS volume,
                           0 AS priority
                    FROM '{_sql_escape_path(base_path)}'
                    WHERE CAST(date AS DATE) < DATE '{anchor_str}'
                    UNION ALL
                    SELECT CAST(date AS DATE) AS date,
                           CAST(permno AS BIGINT) AS permno,
                           CAST({price_col} AS DOUBLE) AS signal_price,
                           CAST(volume AS DOUBLE) AS volume,
                           1 AS priority
                    FROM '{_sql_escape_path(str(patch_path))}'
                    WHERE CAST(date AS DATE) < DATE '{anchor_str}'
                ),
                ranked_src AS (
                    SELECT date,
                           permno,
                           signal_price,
                           volume,
                           ROW_NUMBER() OVER (PARTITION BY date, permno ORDER BY priority DESC) AS rn
                    FROM src
                ),
                clean_src AS (
                    SELECT date, permno, signal_price, volume
                    FROM ranked_src
                    WHERE rn = 1
                      AND volume > 0
                      AND signal_price > 0
                ),
                last_tradable_date AS (
                    SELECT MAX(date) AS date
                    FROM clean_src
                )
                SELECT
                    clean_src.permno AS permno,
                    SUM(clean_src.signal_price * clean_src.volume) AS dollar_volume
                FROM clean_src
                JOIN last_tradable_date ltd
                  ON clean_src.date = ltd.date
                GROUP BY clean_src.permno
                ORDER BY dollar_volume DESC, permno ASC
                LIMIT {int(yearly_top_n)}
            """
        else:
            q = f"""
                WITH clean_src AS (
                    SELECT CAST(date AS DATE) AS date,
                           CAST(permno AS BIGINT) AS permno,
                           CAST({price_col} AS DOUBLE) AS signal_price,
                           CAST(volume AS DOUBLE) AS volume
                    FROM '{_sql_escape_path(base_path)}'
                    WHERE CAST(date AS DATE) < DATE '{anchor_str}'
                      AND CAST(volume AS DOUBLE) > 0
                      AND CAST({price_col} AS DOUBLE) > 0
                ),
                last_tradable_date AS (
                    SELECT MAX(date) AS date
                    FROM clean_src
                )
                SELECT
                    clean_src.permno AS permno,
                    SUM(clean_src.signal_price * clean_src.volume) AS dollar_volume
                FROM clean_src
                JOIN last_tradable_date ltd
                  ON clean_src.date = ltd.date
                GROUP BY clean_src.permno
                ORDER BY dollar_volume DESC, permno ASC
                LIMIT {int(yearly_top_n)}
            """
        df = con.execute(q).df()
    finally:
        con.close()

    if df.empty:
        return []
    return [int(x) for x in df["permno"].tolist()]


def _select_universe_permnos(
    cfg: FeatureStoreConfig,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None = None,
) -> list[int]:
    mode = _normalize_universe_mode(cfg.universe_mode)
    if mode == UNIVERSE_MODE_GLOBAL:
        return _top_liquid_permnos(cfg.top_n)
    return _top_liquid_permnos_yearly_union(
        yearly_top_n=cfg.yearly_top_n,
        start_date=start_date,
        end_date=end_date,
    )


def _load_prices_long(
    permnos: list[int],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    if not permnos:
        return pd.DataFrame(columns=["date", "permno", "adj_close", "tri", "total_ret", "volume"])

    src_cfg = _price_source_config()
    base_path = str(src_cfg["base"])
    patch_path = src_cfg["patch"]
    price_col = str(src_cfg["price_col"])
    legacy_col = str(src_cfg["legacy_col"])
    tri_mode = str(src_cfg["mode"]) == "tri"

    permno_list = ",".join(str(int(p)) for p in permnos)
    start_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    end_clause = ""
    if end_date is not None:
        end_str = pd.Timestamp(end_date).strftime("%Y-%m-%d")
        end_clause = f" AND CAST(date AS DATE) <= DATE '{end_str}'"

    con = duckdb.connect()
    try:
        if tri_mode:
            q = f"""
                SELECT
                    CAST(date AS DATE) AS date,
                    CAST(permno AS BIGINT) AS permno,
                    CAST({legacy_col} AS DOUBLE) AS adj_close,
                    CAST({price_col} AS DOUBLE) AS tri,
                    CAST(total_ret AS DOUBLE) AS total_ret,
                    CAST(volume AS DOUBLE) AS volume
                FROM '{_sql_escape_path(base_path)}'
                WHERE CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                  AND CAST(permno AS BIGINT) IN ({permno_list})
                ORDER BY date, permno
            """
        elif patch_path is not None and os.path.exists(str(patch_path)):
            q = f"""
                WITH src AS (
                    SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno,
                           CAST(adj_close AS DOUBLE) AS adj_close,
                           CAST(NULL AS DOUBLE) AS tri,
                           CAST(total_ret AS DOUBLE) AS total_ret,
                           CAST(volume AS DOUBLE) AS volume,
                           0 AS priority
                    FROM '{_sql_escape_path(base_path)}'
                    WHERE CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                      AND CAST(permno AS BIGINT) IN ({permno_list})
                    UNION ALL
                    SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno,
                           CAST(adj_close AS DOUBLE) AS adj_close,
                           CAST(NULL AS DOUBLE) AS tri,
                           CAST(total_ret AS DOUBLE) AS total_ret,
                           CAST(volume AS DOUBLE) AS volume,
                           1 AS priority
                    FROM '{_sql_escape_path(str(patch_path))}'
                    WHERE CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                      AND CAST(permno AS BIGINT) IN ({permno_list})
                ),
                ranked AS (
                    SELECT *,
                           ROW_NUMBER() OVER (PARTITION BY date, permno ORDER BY priority DESC) AS rn
                    FROM src
                )
                SELECT date, permno, adj_close, tri, total_ret, volume
                FROM ranked
                WHERE rn = 1
                ORDER BY date, permno
            """
        else:
            q = f"""
                SELECT CAST(date AS DATE) AS date,
                       CAST(permno AS BIGINT) AS permno,
                       CAST(adj_close AS DOUBLE) AS adj_close,
                       CAST(NULL AS DOUBLE) AS tri,
                       CAST(total_ret AS DOUBLE) AS total_ret,
                       CAST(volume AS DOUBLE) AS volume
                FROM '{_sql_escape_path(base_path)}'
                WHERE CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                  AND CAST(permno AS BIGINT) IN ({permno_list})
                ORDER BY date, permno
            """
        df = con.execute(q).df()
    finally:
        con.close()

    if df.empty:
        return pd.DataFrame(columns=["date", "permno", "adj_close", "tri", "total_ret", "volume"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    return df


def _load_market_close(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp | None = None,
) -> pd.Series:
    start_str = pd.Timestamp(start_date).strftime("%Y-%m-%d")
    end_clause = ""
    if end_date is not None:
        end_str = pd.Timestamp(end_date).strftime("%Y-%m-%d")
        end_clause = f" AND CAST(date AS DATE) <= DATE '{end_str}'"

    macro_path = _macro_source_path()
    if os.path.exists(macro_path):
        macro = pd.read_parquet(macro_path)
        spy_col = "spy_tri" if "spy_tri" in macro.columns else "spy_close"
        if "date" in macro.columns and spy_col in macro.columns:
            macro["date"] = pd.to_datetime(macro["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
            m = macro.dropna(subset=["date"]).set_index("date").sort_index()
            s = pd.to_numeric(m[spy_col], errors="coerce")
            s = s[s.index >= pd.Timestamp(start_date)]
            if end_date is not None:
                s = s[s.index <= pd.Timestamp(end_date)]
            if s.notna().sum() > 0:
                return s

    src_cfg = _price_source_config()
    base_path = str(src_cfg["base"])
    patch_path = src_cfg["patch"]
    price_col = str(src_cfg["price_col"])

    con = duckdb.connect()
    try:
        if patch_path is not None and os.path.exists(str(patch_path)):
            q = f"""
                WITH src AS (
                    SELECT CAST(date AS DATE) AS date, CAST({price_col} AS DOUBLE) AS adj_close, 0 AS priority
                    FROM '{_sql_escape_path(base_path)}'
                    WHERE CAST(permno AS BIGINT) = {SPY_PERMNO}
                      AND CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                    UNION ALL
                    SELECT CAST(date AS DATE) AS date, CAST({price_col} AS DOUBLE) AS adj_close, 1 AS priority
                    FROM '{_sql_escape_path(str(patch_path))}'
                    WHERE CAST(permno AS BIGINT) = {SPY_PERMNO}
                      AND CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                ),
                ranked AS (
                    SELECT date, adj_close,
                           ROW_NUMBER() OVER (PARTITION BY date ORDER BY priority DESC) AS rn
                    FROM src
                )
                SELECT date, adj_close
                FROM ranked
                WHERE rn = 1
                ORDER BY date
            """
        else:
            q = f"""
                SELECT CAST(date AS DATE) AS date, CAST({price_col} AS DOUBLE) AS adj_close
                FROM '{_sql_escape_path(base_path)}'
                WHERE CAST(permno AS BIGINT) = {SPY_PERMNO}
                  AND CAST(date AS DATE) >= DATE '{start_str}' {end_clause}
                ORDER BY date
            """
        df = con.execute(q).df()
    finally:
        con.close()

    if df.empty:
        return pd.Series(dtype=float, name="spy_close")
    idx = pd.to_datetime(df["date"], errors="coerce", utc=True).tz_convert(None).normalize()
    vals = pd.to_numeric(df["adj_close"], errors="coerce")
    out = pd.Series(vals.values, index=idx, name="spy_close")
    out = out[~out.index.isna()].sort_index()
    return out


def _cross_sectional_z(wide: pd.DataFrame) -> pd.DataFrame:
    mu = wide.mean(axis=1, skipna=True)
    sigma = wide.std(axis=1, skipna=True).replace(0.0, np.nan)
    return wide.sub(mu, axis=0).div(sigma, axis=0)


def _cross_sectional_percentile_fallback(wide: pd.DataFrame) -> pd.DataFrame:
    ranked = wide.rank(axis=1, method="average", pct=True, na_option="keep")
    return (ranked - 0.5) * 2.0


def _cross_sectional_scale(
    wide: pd.DataFrame,
    mode: str = CS_SCALE_ROBUST,
    epsilon_floor: float = CS_SCALE_DEFAULT_EPSILON_FLOOR,
    min_window_size: int = CS_SCALE_DEFAULT_MIN_WINDOW,
) -> tuple[pd.DataFrame, dict[str, float | int | str]]:
    if wide is None:
        empty = pd.DataFrame()
        return empty, {
            "mode": _normalize_cs_scale_mode(mode),
            "row_total": 0,
            "fallback_rows": 0,
            "fallback_rate": 0.0,
        }
    if wide.empty:
        return wide.copy(), {
            "mode": _normalize_cs_scale_mode(mode),
            "row_total": 0,
            "fallback_rows": 0,
            "fallback_rate": 0.0,
        }

    mode_val = _normalize_cs_scale_mode(mode)
    non_na_counts = wide.notna().sum(axis=1).astype(int)
    valid_rows = non_na_counts.gt(0)
    row_total = int(valid_rows.sum())
    fallback_rows = 0

    if mode_val == CS_SCALE_STANDARD:
        scaled = _cross_sectional_z(wide)
    else:
        eps = max(float(epsilon_floor), float(np.finfo(float).eps))
        min_window = max(1, int(min_window_size))
        median = wide.median(axis=1, skipna=True)
        mad = wide.sub(median, axis=0).abs().median(axis=1, skipna=True)
        robust_sigma = (1.4826 * mad).clip(lower=eps)
        scaled = wide.sub(median, axis=0).div(robust_sigma, axis=0)

        fallback_mask = valid_rows & non_na_counts.lt(min_window)
        fallback_rows = int(fallback_mask.sum())
        if fallback_rows:
            percentile_scaled = _cross_sectional_percentile_fallback(wide)
            scaled.loc[fallback_mask] = percentile_scaled.loc[fallback_mask]

    fallback_rate = float(fallback_rows) / float(row_total) if row_total > 0 else 0.0
    return scaled, {
        "mode": mode_val,
        "row_total": row_total,
        "fallback_rows": fallback_rows,
        "fallback_rate": fallback_rate,
    }


def _accumulate_cs_scale_stats(
    accumulator: dict[str, float | int | str],
    stats: dict[str, float | int | str],
) -> None:
    accumulator["row_total"] = int(accumulator.get("row_total", 0)) + int(stats.get("row_total", 0))
    accumulator["fallback_rows"] = int(accumulator.get("fallback_rows", 0)) + int(stats.get("fallback_rows", 0))
    if "mode" not in accumulator or accumulator.get("mode") is None:
        accumulator["mode"] = stats.get("mode")


def _stack_feature_series(wide: pd.DataFrame, name: str) -> pd.Series:
    try:
        return wide.stack(future_stack=True).rename(name)
    except TypeError:
        return wide.stack(dropna=False).rename(name)


def _compute_rsi(close_wide: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    delta = close_wide.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / float(window), adjust=False, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1.0 / float(window), adjust=False, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.clip(lower=0.0, upper=100.0)


def _compute_beta_and_residual_momentum(
    ret_wide: pd.DataFrame,
    market_ret: pd.Series,
    beta_window: int,
    resid_window: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    mr = pd.to_numeric(market_ret, errors="coerce")
    mr_var = mr.rolling(beta_window, min_periods=beta_window).var()
    cov = ret_wide.rolling(beta_window, min_periods=beta_window).cov(mr)
    beta = cov.div(mr_var, axis=0)
    resid_daily = ret_wide.sub(beta.mul(mr, axis=0), axis=0)
    resid_mom = resid_daily.rolling(resid_window, min_periods=resid_window).sum()
    return beta, resid_mom


def _compute_yang_zhang_vol(
    close_wide: pd.DataFrame,
    window: int,
) -> tuple[pd.DataFrame, str]:
    # Close-only fallback mode: derive pseudo OHLC from adjacent closes.
    open_wide = close_wide.shift(1).where(close_wide.shift(1).notna(), close_wide)
    high_wide = np.maximum(close_wide, open_wide)
    low_wide = np.minimum(close_wide, open_wide)

    prev_close = close_wide.shift(1)
    safe_close = close_wide.where(close_wide > 0.0)
    safe_open = open_wide.where(open_wide > 0.0)
    safe_high = high_wide.where(high_wide > 0.0)
    safe_low = low_wide.where(low_wide > 0.0)
    safe_prev_close = prev_close.where(prev_close > 0.0)

    log_oc = np.log(safe_open / safe_prev_close)
    log_cc = np.log(safe_close / safe_prev_close)
    log_ho = np.log(safe_high / safe_open)
    log_lo = np.log(safe_low / safe_open)
    log_co = np.log(safe_close / safe_open)

    rs = log_ho * (log_ho - log_co) + log_lo * (log_lo - log_co)
    k = 0.34 / (1.34 + ((window + 1.0) / (max(window - 1.0, 1.0))))

    sigma_oc2 = log_oc.rolling(window, min_periods=window).var()
    sigma_cc2 = log_cc.rolling(window, min_periods=window).var()
    sigma_rs = rs.rolling(window, min_periods=window).mean()
    yz_var = sigma_oc2 + (k * sigma_cc2) + ((1.0 - k) * sigma_rs)
    yz_vol = np.sqrt(yz_var.clip(lower=0.0)) * np.sqrt(252.0)
    return yz_vol, "proxy_close_only"


def _empty_like(reference: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(np.nan, index=reference.index, columns=reference.columns, dtype=float)


def _all_missing(wide: pd.DataFrame | None) -> bool:
    if wide is None or wide.empty:
        return True
    return bool(float(wide.count().sum()) == 0.0)


def _derive_capital_cycle_inputs(
    close_wide: pd.DataFrame,
    fundamentals_daily: dict[str, pd.DataFrame],
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    sales_accel = fundamentals_daily.get("sales_accel_q", _empty_like(close_wide))
    op_margin_accel = fundamentals_daily.get("op_margin_accel_q", _empty_like(close_wide))
    bloat = fundamentals_daily.get("bloat_q", _empty_like(close_wide))
    net_investment = fundamentals_daily.get("net_investment_q", _empty_like(close_wide))
    asset_growth = fundamentals_daily.get("asset_growth_yoy", _empty_like(close_wide))
    op_margin_delta = fundamentals_daily.get("operating_margin_delta_q", _empty_like(close_wide))
    delta_rev_inv = fundamentals_daily.get("delta_revenue_inventory", _empty_like(close_wide))
    revenue_inventory = fundamentals_daily.get("revenue_inventory_q", _empty_like(close_wide))

    fallback_tags: list[str] = []
    if _all_missing(sales_accel):
        sales_accel = delta_rev_inv.copy()
        fallback_tags.append("sales_accel_q<-delta_revenue_inventory")
    if _all_missing(op_margin_accel):
        op_margin_accel = op_margin_delta.diff()
        fallback_tags.append("op_margin_accel_q<-diff(operating_margin_delta_q)")
    if _all_missing(bloat):
        inv_to_rev = 1.0 / revenue_inventory.replace(0.0, np.nan)
        bloat = inv_to_rev.diff()
        fallback_tags.append("bloat_q<-diff(1/revenue_inventory_q)")
    if _all_missing(net_investment):
        net_investment = asset_growth.copy()
        fallback_tags.append("net_investment_q<-asset_growth_yoy")

    return (
        {
            "sales_accel_q": sales_accel,
            "op_margin_accel_q": op_margin_accel,
            "bloat_q": bloat,
            "net_investment_q": net_investment,
        },
        fallback_tags,
    )


def _execute_feature_specs(
    specs: list[FeatureSpec],
    feature_context: dict[str, pd.DataFrame],
    dependency_columns: set[str],
    status: dict | None = None,
) -> dict[str, pd.DataFrame]:
    outputs: dict[str, pd.DataFrame] = {}
    base = next((v for v in feature_context.values() if isinstance(v, pd.DataFrame)), pd.DataFrame())
    for spec in specs:
        missing_inputs = [name for name in spec.inputs if name not in feature_context]
        if missing_inputs:
            msg = f"Spec '{spec.name}' missing required context inputs: {missing_inputs}"
            if status is not None:
                _warn(status, msg)
            raise FeatureSpecExecutionError(msg)

        if spec.category == "fundamental":
            generated_dependencies = set(outputs.keys())
            missing_dep = [
                name
                for name in spec.inputs
                if name not in dependency_columns and name not in generated_dependencies
            ]
            if missing_dep:
                msg = (
                    f"Spec '{spec.name}' missing dependency columns in fundamental snapshot/derived outputs: "
                    f"{missing_dep}"
                )
                if status is not None:
                    _warn(status, msg)
                raise FeatureSpecExecutionError(msg)

        try:
            result = spec.func(feature_context, spec)
        except Exception as exc:
            msg = f"Spec '{spec.name}' failed: {exc}"
            if status is not None:
                _warn(status, msg)
            raise FeatureSpecExecutionError(msg) from exc

        if not isinstance(result, pd.DataFrame):
            msg = (
                f"Spec '{spec.name}' returned invalid type {type(result).__name__}; "
                "expected pandas.DataFrame."
            )
            if status is not None:
                _warn(status, msg)
            raise FeatureSpecExecutionError(msg)
        try:
            if not result.empty and not base.empty:
                result = result.reindex(index=base.index, columns=base.columns)
        except Exception as exc:
            msg = f"Spec '{spec.name}' post-processing failed: {exc}"
            if status is not None:
                _warn(status, msg)
            raise FeatureSpecExecutionError(msg) from exc
        outputs[spec.name] = result
        feature_context[spec.name] = result
    return outputs


def compute_feature_frame(
    prices_long: pd.DataFrame,
    market_close: pd.Series,
    ticker_map: pd.DataFrame | None,
    cfg: FeatureStoreConfig,
    specs: list[FeatureSpec] | None = None,
    status: dict | None = None,
    normalization_telemetry: dict | None = None,
) -> pd.DataFrame:
    if prices_long.empty:
        return pd.DataFrame(columns=PERSISTED_FEATURE_COLUMNS)

    p = prices_long.copy()
    p["date"] = pd.to_datetime(p["date"], errors="coerce")
    p = p.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    if "adj_close" not in p.columns:
        p["adj_close"] = np.nan
    if "tri" not in p.columns:
        p["tri"] = np.nan
    p["adj_close"] = pd.to_numeric(p["adj_close"], errors="coerce")
    p["tri"] = pd.to_numeric(p["tri"], errors="coerce")
    p["total_ret"] = pd.to_numeric(p["total_ret"], errors="coerce")
    p["volume"] = pd.to_numeric(p["volume"], errors="coerce")

    use_tri = bool(p["tri"].notna().sum() > 0)
    p["signal_close"] = p["tri"] if use_tri else p["adj_close"]
    p["adj_close"] = p["adj_close"].where(p["adj_close"].notna(), p["signal_close"])
    p["tri"] = p["signal_close"].where(p["signal_close"].notna(), p["tri"])

    close_wide = p.pivot(index="date", columns="permno", values="signal_close").sort_index()
    tri_wide = p.pivot(index="date", columns="permno", values="tri").sort_index()
    ret_wide = p.pivot(index="date", columns="permno", values="total_ret").sort_index()
    vol_wide = p.pivot(index="date", columns="permno", values="volume").sort_index()

    # Fallback return calc for sparse/empty total_ret values.
    ret_fallback = close_wide.pct_change(fill_method=None)
    ret_wide = ret_wide.where(ret_wide.notna(), ret_fallback)

    market_close = pd.to_numeric(market_close, errors="coerce").reindex(close_wide.index).ffill()
    market_ret = market_close.pct_change(fill_method=None).fillna(0.0)

    beta_wide, resid_mom_wide = _compute_beta_and_residual_momentum(
        ret_wide=ret_wide,
        market_ret=market_ret,
        beta_window=cfg.beta_window,
        resid_window=cfg.resid_mom_window,
    )

    stock_perf = close_wide / close_wide.shift(cfg.rel_strength_window) - 1.0
    market_perf = market_close / market_close.shift(cfg.rel_strength_window) - 1.0
    rel_strength_wide = stock_perf.sub(market_perf, axis=0)

    dollar_vol_wide = (close_wide * vol_wide).replace(0.0, np.nan)
    amihud_raw = ret_wide.abs() / dollar_vol_wide
    amihud_wide = amihud_raw.rolling(cfg.amihud_window, min_periods=cfg.amihud_window).mean()

    yz_vol_wide, yz_mode = _compute_yang_zhang_vol(close_wide=close_wide, window=cfg.yz_window)

    atr_wide = close_wide.diff().abs().rolling(cfg.atr_window, min_periods=cfg.atr_window).mean()
    atr_mode = "proxy_close_only"

    rsi_wide = _compute_rsi(close_wide, window=cfg.rsi_window)
    sma20 = close_wide.rolling(cfg.sma_short_window, min_periods=cfg.sma_short_window).mean()
    dist_sma20_wide = (close_wide - sma20) / sma20.replace(0.0, np.nan)
    sma200 = close_wide.rolling(cfg.sma_trend_window, min_periods=cfg.sma_trend_window).mean()
    trend_veto_wide = close_wide.lt(sma200)

    flow_proxy = -amihud_wide
    if specs is None:
        specs = build_default_feature_specs()

    permno_cols = [int(c) for c in close_wide.columns.tolist()]
    binding_token: str | None = None
    binding_secret: str | None = None
    strict_binding = str(os.getenv(fundamentals_data.SIMULATION_TS_BINDING_STRICT_ENV, "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if strict_binding:
        raw_secret = str(os.getenv(fundamentals_data.SIMULATION_TS_BINDING_SECRET_ENV, "")).strip()
        binding_secret = raw_secret or None
        binding_token = fundamentals_data.create_simulation_ts_binding_token(
            simulation_ts=close_wide.index[-1],
            secret=binding_secret,
        )
    fundamentals_daily = fundamentals_data.build_fundamentals_daily(
        prices_index=close_wide.index,
        permnos=permno_cols,
        simulation_ts_binding_token=binding_token,
        simulation_ts_binding_secret=binding_secret,
    )
    fundamentals_snapshot = fundamentals_data.load_fundamentals_snapshot(
        permnos=permno_cols,
        as_of_date=close_wide.index[-1],
        simulation_ts_binding_token=binding_token,
        simulation_ts_binding_secret=binding_secret,
    )
    dependency_columns = set(fundamentals_snapshot.columns) if not fundamentals_snapshot.empty else set()
    required_snapshot_inputs = {
        "roic",
        "asset_growth_yoy",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "operating_margin_delta_q",
        "delta_revenue_inventory",
    }
    missing_snapshot_inputs = sorted(required_snapshot_inputs - dependency_columns)
    if missing_snapshot_inputs and status is not None:
        _warn(
            status,
            f"Bitemporal snapshot missing expected fundamental inputs: {missing_snapshot_inputs}",
        )

    proxy_inputs, fallback_tags = _derive_capital_cycle_inputs(
        close_wide=close_wide,
        fundamentals_daily=fundamentals_daily,
    )
    if fallback_tags and status is not None:
        _warn(
            status,
            "Proxy input fallback applied: " + ", ".join(fallback_tags),
        )

    feature_context: dict[str, pd.DataFrame] = {
        "resid_mom_60d": resid_mom_wide,
        "flow_proxy": flow_proxy,
        "yz_vol_20d": yz_vol_wide,
        "roic": fundamentals_daily.get("roic", _empty_like(close_wide)),
        "asset_growth_yoy": fundamentals_daily.get("asset_growth_yoy", _empty_like(close_wide)),
        "sales_accel_q": proxy_inputs["sales_accel_q"],
        "op_margin_accel_q": proxy_inputs["op_margin_accel_q"],
        "bloat_q": proxy_inputs["bloat_q"],
        "net_investment_q": proxy_inputs["net_investment_q"],
        "operating_margin_delta_q": fundamentals_daily.get("operating_margin_delta_q", _empty_like(close_wide)),
        "delta_revenue_inventory": fundamentals_daily.get("delta_revenue_inventory", _empty_like(close_wide)),
    }
    spec_outputs = _execute_feature_specs(
        specs=specs,
        feature_context=feature_context,
        dependency_columns=dependency_columns,
        status=status,
    )
    cs_stats: dict[str, float | int | str] = {"mode": None, "row_total": 0, "fallback_rows": 0}

    def _scale_z_output(source: pd.DataFrame) -> pd.DataFrame:
        scaled, stats_row = _cross_sectional_scale(
            wide=source,
            mode=cfg.cs_scale_mode,
            epsilon_floor=cfg.cs_scale_epsilon_floor,
            min_window_size=cfg.cs_scale_min_window_size,
        )
        _accumulate_cs_scale_stats(cs_stats, stats_row)
        return scaled

    z_resid_source = spec_outputs.get("z_resid_mom", resid_mom_wide)
    z_flow_source = spec_outputs.get("z_flow_proxy", flow_proxy)
    z_vol_source = spec_outputs.get("z_vol_penalty", yz_vol_wide)
    z_resid_wide = _scale_z_output(z_resid_source)
    z_flow_wide = _scale_z_output(z_flow_source)
    z_vol_wide = _scale_z_output(z_vol_source)
    composite_wide = spec_outputs.get("composite_score", z_resid_wide + z_flow_wide - z_vol_wide)
    z_moat_wide = _scale_z_output(spec_outputs.get("z_moat", _empty_like(close_wide)))
    z_inventory_quality_proxy_wide = _scale_z_output(spec_outputs.get("z_inventory_quality_proxy", _empty_like(close_wide)))
    z_discipline_wide = _scale_z_output(spec_outputs.get("z_discipline_cond", _empty_like(close_wide)))
    z_demand_wide = _scale_z_output(spec_outputs.get("z_demand", _empty_like(close_wide)))
    capital_cycle_wide = spec_outputs.get("capital_cycle_score", _empty_like(close_wide))

    if normalization_telemetry is not None:
        fallback_rows = int(cs_stats.get("fallback_rows", 0))
        row_total = int(cs_stats.get("row_total", 0))
        normalization_telemetry["cs_scale_mode"] = str(cs_stats.get("mode") or _normalize_cs_scale_mode(cfg.cs_scale_mode))
        normalization_telemetry["fallback_rows"] = fallback_rows
        normalization_telemetry["fallback_total_rows"] = row_total
        normalization_telemetry["fallback_rate"] = (float(fallback_rows) / float(row_total)) if row_total > 0 else 0.0

    stack_tasks = [
        (close_wide, "adj_close"),
        (tri_wide, "tri"),
        (vol_wide, "volume"),
        (beta_wide, "rolling_beta_63d"),
        (resid_mom_wide, "resid_mom_60d"),
        (rel_strength_wide, "rel_strength_60d"),
        (amihud_wide, "amihud_20d"),
        (yz_vol_wide, "yz_vol_20d"),
        (atr_wide, "atr_14d"),
        (rsi_wide, "rsi_14d"),
        (dist_sma20_wide, "dist_sma20"),
        (sma200, "sma200"),
        (trend_veto_wide.astype("float64"), "trend_veto"),
        (z_resid_wide, "z_resid_mom"),
        (z_flow_wide, "z_flow_proxy"),
        (z_vol_wide, "z_vol_penalty"),
        (composite_wide, "composite_score"),
        (z_moat_wide, "z_moat"),
        (z_inventory_quality_proxy_wide, "z_inventory_quality_proxy"),
        (z_discipline_wide, "z_discipline_cond"),
        (z_demand_wide, "z_demand"),
        (capital_cycle_wide, "capital_cycle_score"),
    ]
    stack_series = parallel_execute(
        func=_stack_feature_series,
        tasks=stack_tasks,
        n_jobs=min(len(stack_tasks), 8),
        desc="feature_stack",
        backend="threading",
        fail_fast=True,
    )
    out = pd.concat(stack_series, axis=1).reset_index().rename(columns={"level_0": "date", "permno": "permno"})

    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["permno"] = pd.to_numeric(out["permno"], errors="coerce").astype("Int64")
    out["trend_veto"] = out["trend_veto"].fillna(0.0).astype(bool)
    # Day 4 scorecard aliases to align factor-spec candidate names with persisted feature schema.
    out["illiq_21d"] = pd.to_numeric(out.get("amihud_20d"), errors="coerce")
    out["realized_vol_21d"] = pd.to_numeric(out.get("yz_vol_20d"), errors="coerce")
    out["quality_composite"] = pd.to_numeric(out.get("capital_cycle_score"), errors="coerce")
    out["yz_mode"] = yz_mode
    out["atr_mode"] = atr_mode

    if ticker_map is not None and not ticker_map.empty:
        tmap = ticker_map.copy()
        tmap["permno"] = pd.to_numeric(tmap["permno"], errors="coerce").astype("Int64")
        out = out.merge(tmap[["permno", "ticker"]], on="permno", how="left")
    else:
        out["ticker"] = np.nan

    for col in REQUIRED_PERSISTED_FACTOR_COLUMNS:
        if col not in out.columns:
            out[col] = np.nan
    out = out[PERSISTED_FEATURE_COLUMNS].sort_values(["date", "permno"])
    return out


def run_build(
    start_year: int = 2000,
    top_n: int = 3000,
    end_date: str | None = None,
    universe_mode: str = UNIVERSE_MODE_YEARLY_UNION,
    yearly_top_n: int = 100,
    incremental: bool = True,
    incremental_warmup_bdays: int | None = None,
    upsert_chunk_size: int = 50,
    cs_scale_mode: str = CS_SCALE_ROBUST,
    cs_scale_epsilon_floor: float = CS_SCALE_DEFAULT_EPSILON_FLOOR,
    cs_scale_min_window_size: int = CS_SCALE_DEFAULT_MIN_WINDOW,
) -> dict:
    status = _new_status()
    try:
        scale_mode = _normalize_cs_scale_mode(cs_scale_mode)
    except ValueError as exc:
        _warn(status, str(exc))
        return status
    cfg = FeatureStoreConfig(
        start_year=int(start_year),
        top_n=int(top_n),
        universe_mode=str(universe_mode),
        yearly_top_n=int(yearly_top_n),
        cs_scale_mode=scale_mode,
        cs_scale_epsilon_floor=max(float(cs_scale_epsilon_floor), float(np.finfo(float).eps)),
        cs_scale_min_window_size=max(1, int(cs_scale_min_window_size)),
    )
    _log(status, "=" * 62)
    _log(status, "🧬 Feature Store Build (FR-060)")
    _log(status, "=" * 62)
    t0 = time.perf_counter()

    start_ts = pd.Timestamp(f"{int(cfg.start_year)}-01-01")
    end_ts = pd.Timestamp(end_date) if end_date else None
    if end_ts is not None and end_ts < start_ts:
        _warn(status, f"Invalid window: end_date {end_ts.date()} is before start date {start_ts.date()}.")
        return status

    lock_token: str | None = None
    try:
        lock_token = updater._acquire_update_lock()
    except TimeoutError as e:
        _warn(status, f"Build skipped: {e}")
        return status

    try:
        _ensure_partitioned_feature_store(
            FEATURES_PATH,
            status=status,
            expected_lock_token=lock_token,
        )
        mode = _normalize_universe_mode(cfg.universe_mode)
        if mode == UNIVERSE_MODE_GLOBAL:
            _log(status, f"🧭 Universe mode: {mode} (top_n={cfg.top_n:,})")
        else:
            end_label = end_ts.strftime("%Y-%m-%d") if end_ts is not None else "latest"
            _log(
                status,
                f"🧭 Universe mode: {mode} (yearly_top_n={cfg.yearly_top_n:,}, window={start_ts.strftime('%Y-%m-%d')}..{end_label})",
            )
        _log(
            status,
            f"⚖ Cross-sectional scale: {cfg.cs_scale_mode} "
            f"(min_window={cfg.cs_scale_min_window_size}, epsilon_floor={cfg.cs_scale_epsilon_floor:g})",
        )

        effective_start_ts = start_ts
        append_start_ts = start_ts
        incremental_active = False
        existing_min_ts, existing_max_ts = _read_feature_date_bounds(FEATURES_PATH)
        warmup_bdays = (
            int(incremental_warmup_bdays)
            if incremental_warmup_bdays is not None
            else _default_incremental_warmup_bdays(cfg)
        )

        if (
            bool(incremental)
            and end_ts is None
            and existing_max_ts is not None
            and existing_min_ts is not None
            and start_ts <= existing_min_ts
        ):
            append_start_ts = max(start_ts, (existing_max_ts + BDay(1)).normalize())
            effective_start_ts = max(start_ts, (append_start_ts - BDay(max(1, warmup_bdays))).normalize())
            incremental_active = True
            _log(
                status,
                f"⚙ Incremental mode: append_from={append_start_ts.strftime('%Y-%m-%d')} "
                f"(warmup={warmup_bdays} bdays, load_from={effective_start_ts.strftime('%Y-%m-%d')})",
            )
        elif bool(incremental) and existing_max_ts is not None:
            _warn(
                status,
                "Incremental mode bypassed for custom build window; running full rebuild to preserve window semantics.",
            )

        now_utc = pd.Timestamp.utcnow()
        today_ts = (now_utc.tz_localize(None) if now_utc.tzinfo is not None else now_utc).normalize()
        if incremental_active and append_start_ts > today_ts:
            status["success"] = True
            status["rows_written"] = 0
            _log(status, "✅ Feature store already up to date (no incremental rows pending).")
            return status

        pinned_permnos: list[int] = []
        if incremental_active:
            pinned_permnos = _load_existing_feature_permnos(FEATURES_PATH)
            if pinned_permnos:
                _log(
                    status,
                    f"📌 Incremental universe pinned to existing feature store: {len(pinned_permnos):,} permnos",
                )
        universe_anchor_ts = append_start_ts if incremental_active else start_ts
        if mode == UNIVERSE_MODE_YEARLY_UNION:
            _log(
                status,
                "🧷 Yearly-union selector as-of anchor: "
                f"{universe_anchor_ts.strftime('%Y-%m-%d')} (strict t-1 daily liquidity; full-year blocks disabled)",
            )
        fresh_permnos = _select_universe_permnos(cfg=cfg, start_date=universe_anchor_ts, end_date=end_ts)
        if pinned_permnos:
            permnos = sorted(set(int(p) for p in pinned_permnos) | set(int(p) for p in fresh_permnos))
            _log(status, f"🧩 Incremental universe unioned with fresh selector: {len(permnos):,} permnos")
        else:
            permnos = fresh_permnos
        if not permnos:
            _warn(status, "No liquid permnos found; cannot build feature store.")
            return status
        t_permnos = time.perf_counter()
        _log(status, f"🔍 Selected liquid universe: {len(permnos):,} permnos")

        if mode == UNIVERSE_MODE_YEARLY_UNION:
            if end_ts is not None:
                guard_end = pd.Timestamp(end_ts).tz_localize(None) if pd.Timestamp(end_ts).tzinfo is not None else pd.Timestamp(end_ts)
            else:
                now_utc = pd.Timestamp.utcnow()
                guard_end = now_utc.tz_localize(None) if now_utc.tzinfo is not None else now_utc
                guard_end = guard_end.normalize()
            est_dates = len(pd.bdate_range(start=start_ts, end=guard_end))
            est_union_gb = _estimate_wide_matrix_gb(n_dates=est_dates, n_assets=len(permnos))
            _log(status, f"🧮 Pre-load yearly-union memory envelope: ~{est_union_gb:.2f} GB")
            if est_union_gb > MEMORY_ENVELOPE_ABORT_GB:
                _warn(
                    status,
                    "Yearly-union universe is too large for safe build envelope. "
                    "Reduce --yearly-top-n, narrow date range, or switch to --universe-mode global.",
                )
                return status
            if est_union_gb > MEMORY_ENVELOPE_WARN_GB:
                _warn(status, "Yearly-union universe may be memory heavy on constrained environments.")

        prices = _load_prices_long(permnos=permnos, start_date=effective_start_ts, end_date=end_ts)
        if prices.empty:
            _warn(status, "No prices loaded for selected window/universe.")
            return status
        t_prices = time.perf_counter()
        _log(status, f"📦 Loaded price rows: {len(prices):,}")

        n_dates = int(prices["date"].nunique())
        n_assets = int(prices["permno"].nunique())
        # Rough memory envelope for wide matrices used in compute_feature_frame.
        est_gb = _estimate_wide_matrix_gb(n_dates=n_dates, n_assets=n_assets)
        _log(status, f"🧮 Estimated wide-matrix memory envelope: ~{est_gb:.2f} GB")
        if est_gb > MEMORY_ENVELOPE_ABORT_GB:
            _warn(status, "Estimated memory footprint too high for safe build. Reduce universe size or date range.")
            return status
        if est_gb > MEMORY_ENVELOPE_WARN_GB:
            _warn(status, "High memory build expected; consider smaller universe for constrained environments.")

        market_close = _load_market_close(start_date=effective_start_ts, end_date=end_ts)
        if market_close.empty or market_close.notna().sum() == 0:
            _warn(status, "Missing SPY market series; cannot compute market-relative features.")
            return status
        market_aligned = pd.to_numeric(market_close, errors="coerce").reindex(pd.DatetimeIndex(sorted(prices["date"].unique())))
        market_missing_ratio = float(market_aligned.isna().mean()) if len(market_aligned) else float("nan")
        if np.isfinite(market_missing_ratio) and market_missing_ratio > 0.05:
            _warn(
                status,
                f"SPY coverage gap too large ({market_missing_ratio:.2%}) for selected window; aborting build.",
            )
            return status
        if np.isfinite(market_missing_ratio) and market_missing_ratio > 0.0:
            _warn(status, f"SPY coverage has gaps ({market_missing_ratio:.2%}); forward-fill will be applied.")
        t_market = time.perf_counter()

        specs = build_default_feature_specs()
        cache_key = _build_cache_key(
            cfg=cfg,
            specs=specs,
            permnos=permnos,
            effective_start_ts=effective_start_ts,
            end_ts=end_ts,
            incremental_active=incremental_active,
            append_start_ts=append_start_ts,
        )
        cache_path = os.path.join(PROCESSED_DIR, f"features_{cache_key}.parquet")
        status["cache_key"] = cache_key
        _log(status, f"🧾 Spec hash: {_feature_spec_hash(specs)[:12]} | build cache key: {cache_key}")

        ticker_map = pd.read_parquet(TICKERS_PATH) if os.path.exists(TICKERS_PATH) else pd.DataFrame()
        normalization_telemetry: dict[str, float | int | str] = {}
        if os.path.exists(cache_path):
            features = pd.read_parquet(cache_path)
            missing_required_cache = [
                c for c in REQUIRED_PERSISTED_FACTOR_COLUMNS if c not in set(features.columns)
            ]
            if missing_required_cache:
                _warn(
                    status,
                    "Cache artifact schema stale; recomputing required factor columns: "
                    + ", ".join(missing_required_cache),
                )
                features = compute_feature_frame(
                    prices_long=prices,
                    market_close=market_close,
                    ticker_map=ticker_map,
                    cfg=cfg,
                    specs=specs,
                    status=status,
                    normalization_telemetry=normalization_telemetry,
                )
                if features.empty:
                    _warn(status, "Computed features are empty.")
                    return status
                updater.atomic_parquet_write(features, cache_path, index=False)
                _log(status, f"🧠 Cache refresh: {os.path.basename(cache_path)}")
            else:
                status["cache_hit"] = True
                _log(status, f"⚡ Cache hit: {os.path.basename(cache_path)}")
        else:
            features = compute_feature_frame(
                prices_long=prices,
                market_close=market_close,
                ticker_map=ticker_map,
                cfg=cfg,
                specs=specs,
                status=status,
                normalization_telemetry=normalization_telemetry,
            )
            if features.empty:
                _warn(status, "Computed features are empty.")
                return status
            updater.atomic_parquet_write(features, cache_path, index=False)
            _log(status, f"🧠 Cache write: {os.path.basename(cache_path)}")
        t_features = time.perf_counter()
        if normalization_telemetry:
            status["cs_scale_mode"] = str(normalization_telemetry.get("cs_scale_mode", cfg.cs_scale_mode))
            status["fallback_rows"] = int(normalization_telemetry.get("fallback_rows", 0))
            status["fallback_total_rows"] = int(normalization_telemetry.get("fallback_total_rows", 0))
            status["fallback_rate"] = float(normalization_telemetry.get("fallback_rate", 0.0))
        else:
            status["cs_scale_mode"] = cfg.cs_scale_mode

        missing_required = [c for c in REQUIRED_PERSISTED_FACTOR_COLUMNS if c not in set(features.columns)]
        if missing_required:
            _warn(
                status,
                "Build output missing required persisted factor columns: " + ", ".join(missing_required),
            )
            return status

        if incremental_active and os.path.exists(FEATURES_PATH):
            existing_cols = _read_parquet_columns(FEATURES_PATH)
            missing_existing = sorted(set(features.columns) - existing_cols)
            if missing_existing:
                _warn(
                    status,
                    "Incremental upsert bypassed due schema drift in existing features.parquet "
                    f"(missing: {missing_existing}); performing full rewrite.",
                )
                incremental_active = False

        rows_written = int(len(features))
        if incremental_active:
            features_new = (
                features[features["date"] >= append_start_ts]
                .sort_values(["date", "permno"])
                .drop_duplicates(subset=["date", "permno"], keep="last")
            )
            rows_written = int(len(features_new))
            if rows_written == 0:
                status["success"] = True
                status["rows_written"] = 0
                _log(status, "✅ Feature store already up to date (incremental build produced no new rows).")
                return status
            _atomic_upsert_features(
                existing_path=FEATURES_PATH,
                new_rows=features_new,
                output_path=FEATURES_PATH,
                status=status,
                upsert_chunk_size=max(1, int(upsert_chunk_size)),
                expected_lock_token=lock_token,
            )
            _log(status, f"➕ Incremental rows appended: {rows_written:,}")
        else:
            _write_partitioned_feature_dataset(
                features,
                FEATURES_PATH,
                expected_lock_token=lock_token,
            )
        t_write = time.perf_counter()

        if not status.get("feature_commit_id"):
            manifest = _read_feature_manifest(FEATURES_PATH)
            if isinstance(manifest, dict):
                status["feature_commit_id"] = str(manifest.get("commit_id") or "").strip() or None
                touched = manifest.get("touched_partitions")
                if isinstance(touched, list):
                    status["feature_touched_partitions"] = [str(x) for x in touched if str(x).strip()]

        status["success"] = True
        status["rows_written"] = rows_written
        total_rows = _count_rows(FEATURES_PATH)
        _log(status, f"💾 features.parquet rows written this run: {status['rows_written']:,}")
        _log(status, f"💾 features.parquet total rows: {total_rows:,}")
        if status.get("feature_commit_id"):
            touched_count = len(status.get("feature_touched_partitions", []))
            _log(
                status,
                f"🧾 Feature commit: {status['feature_commit_id']} (touched_partitions={touched_count})",
            )
        if status.get("fallback_rate") is None:
            _log(
                status,
                f"📉 Robust normalization fallback_rate: n/a "
                f"(cache artifact reused; mode={status.get('cs_scale_mode', cfg.cs_scale_mode)})",
            )
        else:
            _log(
                status,
                "📉 Robust normalization fallback_rate: "
                f"{float(status['fallback_rate']):.2%} "
                f"({int(status.get('fallback_rows', 0)):,}/{int(status.get('fallback_total_rows', 0)):,} date-rows, "
                f"mode={status.get('cs_scale_mode', cfg.cs_scale_mode)})",
            )
        _log(
            status,
            "⏱ Stage timings (s): "
            f"universe={t_permnos - t0:.3f}, "
            f"prices={t_prices - t_permnos:.3f}, "
            f"market={t_market - t_prices:.3f}, "
            f"features={t_features - t_market:.3f}, "
            f"write={t_write - t_features:.3f}, "
            f"total={t_write - t0:.3f}",
        )
        _log(status, "✅ Feature store build complete.")
        return status
    except Exception as e:
        _warn(status, f"Feature store build failed unexpectedly: {e}")
        return status
    finally:
        updater._release_update_lock(expected_token=lock_token)


def main():
    parser = argparse.ArgumentParser(description="Build feature_store features.parquet for FR-060")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument(
        "--top-n",
        type=int,
        default=3000,
        help="Legacy/global universe size (used when --universe-mode global).",
    )
    parser.add_argument(
        "--universe-mode",
        choices=sorted(UNIVERSE_MODES),
        default=UNIVERSE_MODE_YEARLY_UNION,
        help="Universe selector mode: legacy global top-N or PIT yearly union.",
    )
    parser.add_argument(
        "--yearly-top-n",
        type=int,
        default=100,
        help="Per-year top-N for --universe-mode yearly_union.",
    )
    parser.add_argument("--end-date", default=None, help="Optional end date (YYYY-MM-DD)")
    parser.add_argument(
        "--full-rebuild",
        action="store_true",
        help="Disable incremental mode and rebuild the configured window from scratch.",
    )
    parser.add_argument(
        "--incremental-warmup-bdays",
        type=int,
        default=None,
        help="Business-day warmup window used by incremental builds (default: auto from feature windows).",
    )
    parser.add_argument(
        "--upsert-chunk-size",
        type=int,
        default=50,
        help="Touched-partition read chunk size for incremental feature upsert (default: 50).",
    )
    parser.add_argument(
        "--cs-scale-mode",
        choices=sorted(CS_SCALE_MODES),
        default=CS_SCALE_ROBUST,
        help="Cross-sectional normalization mode for z-feature outputs.",
    )
    parser.add_argument(
        "--cs-scale-epsilon-floor",
        type=float,
        default=CS_SCALE_DEFAULT_EPSILON_FLOOR,
        help="Robust sigma epsilon floor used by robust cross-sectional scaling.",
    )
    parser.add_argument(
        "--cs-scale-min-window-size",
        type=int,
        default=CS_SCALE_DEFAULT_MIN_WINDOW,
        help="Minimum non-null cross-sectional window before percentile fallback is used.",
    )
    args = parser.parse_args()

    result = run_build(
        start_year=args.start_year,
        top_n=args.top_n,
        end_date=args.end_date,
        universe_mode=args.universe_mode,
        yearly_top_n=args.yearly_top_n,
        incremental=(not bool(args.full_rebuild)),
        incremental_warmup_bdays=args.incremental_warmup_bdays,
        upsert_chunk_size=args.upsert_chunk_size,
        cs_scale_mode=args.cs_scale_mode,
        cs_scale_epsilon_floor=args.cs_scale_epsilon_floor,
        cs_scale_min_window_size=args.cs_scale_min_window_size,
    )
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
