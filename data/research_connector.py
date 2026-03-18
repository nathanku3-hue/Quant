from __future__ import annotations

import errno
import os
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def _is_within_root(path: str | os.PathLike[str], root: str | os.PathLike[str]) -> bool:
    path_norm = os.path.normcase(os.path.abspath(os.fspath(path)))
    root_norm = os.path.normcase(os.path.abspath(os.fspath(root)))
    if path_norm == root_norm:
        return True
    return path_norm.startswith(root_norm + os.sep)


def _probe_write_access(
    root: Path,
    *,
    open_fn=open,
    probe_name: str | None = None,
) -> None:
    probe = probe_name or f".research_write_probe_{os.getpid()}"
    probe_path = root / probe
    try:
        with open_fn(os.fspath(probe_path), "w", encoding="utf-8") as handle:
            handle.write("probe")
    except PermissionError:
        return
    except OSError as exc:
        if exc.errno in (errno.EACCES, errno.EPERM):
            return
        raise
    else:
        try:
            os.remove(probe_path)
        except FileNotFoundError:
            pass
        raise RuntimeError("Quarantine violation: research_data is writable")


def _scan_symlinks(
    root: Path,
    *,
    walk=os.walk,
    islink=os.path.islink,
    realpath=os.path.realpath,
) -> None:
    root_real = realpath(root)
    for dirpath, dirnames, filenames in walk(root):
        entries = list(dirnames) + list(filenames)
        for name in entries:
            full = os.path.join(dirpath, name)
            if islink(full):
                target = realpath(full)
                if not _is_within_root(target, root_real):
                    raise RuntimeError(f"Unsafe symlink: {full} -> {target}")


def _resolve_root(root: str | Path) -> Path:
    root_path = Path(root)
    if root_path.is_absolute():
        return root_path
    return PROJECT_ROOT / root_path


def _register_session_views(conn: duckdb.DuckDBPyConnection, root_path: Path) -> None:
    cube_root = root_path / "allocator_state_cube"
    if not cube_root.exists():
        raise FileNotFoundError(f"Missing allocator_state cube: {cube_root}")
    view_path = f"{_sql_path(cube_root.resolve())}/variant_id=*/*.parquet"
    conn.execute(
        "CREATE OR REPLACE TEMP VIEW allocator_state AS "
        f"SELECT * FROM read_parquet('{view_path}', hive_partitioning=true)"
    )


def connect_research(
    root: str | Path = "research_data",
    *,
    threads: int = 8,
    memory_limit: str = "2GB",
) -> duckdb.DuckDBPyConnection:
    root_path = _resolve_root(root)
    if os.path.islink(root_path):
        raise RuntimeError("research_data cannot be a symlink")
    if not root_path.exists():
        raise FileNotFoundError(f"Missing research_data directory: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"research_data is not a directory: {root_path}")

    _probe_write_access(root_path)
    _scan_symlinks(root_path)

    catalog_path = root_path / "catalog.duckdb"
    if not catalog_path.exists():
        raise FileNotFoundError(f"Missing research catalog: {catalog_path}")

    conn = duckdb.connect(
        os.fspath(catalog_path),
        read_only=True,
        config={"threads": threads, "memory_limit": memory_limit},
    )
    _register_session_views(conn, root_path)
    return conn
