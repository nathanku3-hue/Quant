"""Confined atomic persistence and verified reopen for the operated portfolio."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.operated import (
    OperatedPortfolioError,
    STATUS_CORRECTED,
    STATUS_DRAFT,
    STATUS_FUNDED,
    STATUS_NO_CHANGE,
    STATUS_TRANSITION,
    admit_no_change_observation,
    append_non_economic_correction,
    authorize_portfolio_transition,
    build_draft_workspace,
    confirm_initial_portfolio,
    validate_workspace,
)

PERSISTED_SCHEMA = "gv_operated_portfolio_10_persisted_v2"
WORKSPACE_FILENAME = "operated_portfolio_10_workspace.json"


def default_workspace_root(*, env: Mapping[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("GV_OPERATED_PORTFOLIO_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".terminal-zero" / "gv_operated_portfolio_10"


def workspace_path(root: Path | None = None) -> Path:
    base = Path(root) if root is not None else default_workspace_root()
    return base / WORKSPACE_FILENAME


def _envelope(workspace: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(workspace)
    return {
        "schema_version": PERSISTED_SCHEMA,
        "workspace_hash": domain_hash(
            "GV-OPERATED-PORTFOLIO-10:WORKSPACE:V2", payload
        ),
        "workspace": payload,
    }


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _same_or_within(path: Path, root: Path) -> bool:
    try:
        path_text = os.path.normcase(os.path.abspath(os.fspath(path)))
        root_text = os.path.normcase(os.path.abspath(os.fspath(root)))
        return os.path.commonpath((path_text, root_text)) == root_text
    except ValueError:
        return False


def _is_link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _reject_linked_ancestors(path: Path) -> None:
    lexical = _absolute_lexical(path)
    chain: list[Path] = []
    cursor = lexical
    while True:
        chain.append(cursor)
        parent = cursor.parent
        if parent == cursor:
            break
        cursor = parent
    for candidate in reversed(chain):
        if os.path.lexists(candidate) and _is_link_like(candidate):
            raise OperatedPortfolioError("WORKSPACE_LINKED_ANCESTOR_PROHIBITED")


def _canonical_candidate(path: Path) -> Path:
    """Resolve every existing ancestor, including Windows junction targets."""

    lexical = _absolute_lexical(path)
    cursor = lexical
    missing: list[str] = []
    while not cursor.exists():
        if cursor.is_symlink():
            raise OperatedPortfolioError("WORKSPACE_BROKEN_LINK_PROHIBITED")
        parent = cursor.parent
        if parent == cursor:
            raise OperatedPortfolioError("WORKSPACE_PATH_UNRESOLVABLE")
        missing.append(cursor.name)
        cursor = parent
    try:
        canonical = cursor.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise OperatedPortfolioError("WORKSPACE_PATH_UNRESOLVABLE") from exc
    for name in reversed(missing):
        canonical = canonical / name
    return canonical


def _confined_paths(
    root: Path | None,
    *,
    require_workspace_file: bool = False,
) -> tuple[Path, Path]:
    lexical_root = _absolute_lexical(
        Path(root) if root is not None else default_workspace_root()
    )
    lexical_path = lexical_root / WORKSPACE_FILENAME
    if not _same_or_within(lexical_path, lexical_root):
        raise OperatedPortfolioError("WORKSPACE_PATH_ESCAPE")

    _reject_linked_ancestors(lexical_root)
    _reject_linked_ancestors(lexical_path)
    canonical_root = _canonical_candidate(lexical_root)
    canonical_path = _canonical_candidate(lexical_path)
    if not _same_or_within(canonical_path, canonical_root):
        raise OperatedPortfolioError("WORKSPACE_CANONICAL_PATH_ESCAPE")
    if not (
        _same_or_within(canonical_root, lexical_root)
        and _same_or_within(lexical_root, canonical_root)
    ):
        raise OperatedPortfolioError("WORKSPACE_ROOT_REDIRECTION_PROHIBITED")

    if lexical_root.exists() and not lexical_root.is_dir():
        raise OperatedPortfolioError("WORKSPACE_ROOT_DIRECTORY_REQUIRED")
    if lexical_path.exists() and not lexical_path.is_file():
        raise OperatedPortfolioError("WORKSPACE_FILE_REGULAR_REQUIRED")
    if require_workspace_file and not lexical_path.is_file():
        raise OperatedPortfolioError("WORKSPACE_NOT_INITIALIZED")
    return lexical_root, lexical_path


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    root = path.parent
    _confined_paths(root)
    root.mkdir(parents=True, exist_ok=True)
    confined_root, confined_path = _confined_paths(root)
    if confined_path != _absolute_lexical(path):
        raise OperatedPortfolioError("WORKSPACE_PATH_IDENTITY_MISMATCH")

    raw = canonical_document_bytes(dict(payload))
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=confined_root
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _confined_paths(root)
        if not _same_or_within(_canonical_candidate(temp_path), confined_root):
            raise OperatedPortfolioError("WORKSPACE_TEMP_PATH_ESCAPE")
        os.replace(temp_path, confined_path)
        _confined_paths(root, require_workspace_file=True)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def persist_workspace(
    workspace: Mapping[str, Any], *, root: Path | None = None
) -> Path:
    validate_workspace(workspace, allow_draft=workspace.get("status") == STATUS_DRAFT)
    _, path = _confined_paths(root)
    _atomic_write(path, _envelope(workspace))
    return path


def load_workspace(*, root: Path | None = None) -> dict[str, Any]:
    _, path = _confined_paths(root, require_workspace_file=True)
    try:
        with path.open("r", encoding="utf-8") as stream:
            envelope = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatedPortfolioError("WORKSPACE_READ_INVALID") from exc
    _confined_paths(root, require_workspace_file=True)
    if envelope.get("schema_version") != PERSISTED_SCHEMA:
        raise OperatedPortfolioError("PERSISTED_SCHEMA_INVALID")
    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        raise OperatedPortfolioError("PERSISTED_WORKSPACE_OBJECT_REQUIRED")
    expected_hash = domain_hash(
        "GV-OPERATED-PORTFOLIO-10:WORKSPACE:V2", workspace
    )
    if envelope.get("workspace_hash") != expected_hash:
        raise OperatedPortfolioError("WORKSPACE_HASH_MISMATCH")
    validate_workspace(workspace, allow_draft=workspace.get("status") == STATUS_DRAFT)
    return workspace


def ensure_workspace(*, root: Path | None = None) -> dict[str, Any]:
    _, path = _confined_paths(root)
    if path.exists():
        return load_workspace(root=root)
    draft = build_draft_workspace()
    persist_workspace(draft, root=root)
    return load_workspace(root=root)


def confirm_and_persist(*, root: Path | None = None) -> dict[str, Any]:
    workspace = ensure_workspace(root=root)
    if workspace["status"] != STATUS_DRAFT:
        return workspace
    result = confirm_initial_portfolio(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root)


def admit_no_change_and_persist(*, root: Path | None = None) -> dict[str, Any]:
    workspace = load_workspace(root=root)
    if workspace["status"] != STATUS_FUNDED:
        return workspace
    result = admit_no_change_observation(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root)


def authorize_transition_and_persist(
    *, root: Path | None = None
) -> dict[str, Any]:
    workspace = load_workspace(root=root)
    if workspace["status"] != STATUS_NO_CHANGE:
        return workspace
    result = authorize_portfolio_transition(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root)


def append_correction_and_persist(
    *, root: Path | None = None
) -> dict[str, Any]:
    workspace = load_workspace(root=root)
    if workspace["status"] == STATUS_CORRECTED:
        return workspace
    if workspace["status"] != STATUS_TRANSITION:
        return workspace
    result = append_non_economic_correction(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root)
