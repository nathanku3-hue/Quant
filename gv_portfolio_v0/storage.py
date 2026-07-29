"""Atomic local persistence and verified reopen for GV Portfolio V0."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.vertical import (
    PortfolioV0Error,
    admit_watch_observation,
    build_draft_workspace,
    confirm_draft_workspace,
    validate_workspace,
)

PERSISTED_SCHEMA = "gv_portfolio_v0_persisted_v1"
WORKSPACE_FILENAME = "micro_portfolio_workspace.json"


def default_workspace_root(*, env: Mapping[str, str] | None = None) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("GV_PORTFOLIO_V0_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".terminal-zero" / "gv_portfolio_v0"


def workspace_path(root: Path | None = None) -> Path:
    base = Path(root) if root is not None else default_workspace_root()
    return base / WORKSPACE_FILENAME


def _envelope(workspace: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(workspace)
    return {
        "schema_version": PERSISTED_SCHEMA,
        "workspace_hash": domain_hash("GV-PORTFOLIO-V0:WORKSPACE:V1", payload),
        "workspace": payload,
    }


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise PortfolioV0Error("WORKSPACE_ROOT_SYMLINK_PROHIBITED")
    raw = canonical_document_bytes(dict(payload))
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def persist_workspace(workspace: Mapping[str, Any], *, root: Path | None = None) -> Path:
    allow_uncertified = workspace.get("status") == "DRAFT_REVIEW"
    validate_workspace(workspace, allow_uncertified=allow_uncertified)
    path = workspace_path(root)
    _atomic_write(path, _envelope(workspace))
    return path


def load_workspace(*, root: Path | None = None) -> dict[str, Any]:
    path = workspace_path(root)
    if not path.is_file():
        raise PortfolioV0Error("WORKSPACE_NOT_INITIALIZED")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PortfolioV0Error("WORKSPACE_READ_INVALID") from exc
    if envelope.get("schema_version") != PERSISTED_SCHEMA:
        raise PortfolioV0Error("PERSISTED_SCHEMA_INVALID")
    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        raise PortfolioV0Error("PERSISTED_WORKSPACE_OBJECT_REQUIRED")
    expected_hash = domain_hash("GV-PORTFOLIO-V0:WORKSPACE:V1", workspace)
    if envelope.get("workspace_hash") != expected_hash:
        raise PortfolioV0Error("WORKSPACE_HASH_MISMATCH")
    validate_workspace(
        workspace, allow_uncertified=workspace.get("status") == "DRAFT_REVIEW"
    )
    return workspace


def ensure_workspace(*, root: Path | None = None) -> dict[str, Any]:
    path = workspace_path(root)
    if path.exists():
        return load_workspace(root=root)
    draft = build_draft_workspace()
    persist_workspace(draft, root=root)
    return load_workspace(root=root)


def confirm_and_certify(*, root: Path | None = None) -> dict[str, Any]:
    workspace = ensure_workspace(root=root)
    if workspace["status"] in {"CERTIFIED", "OBSERVED_WATCH_AIM_UNCHANGED"}:
        return workspace
    certified = confirm_draft_workspace(workspace)
    persist_workspace(certified, root=root)
    return load_workspace(root=root)


def admit_later_watch_observation(*, root: Path | None = None) -> dict[str, Any]:
    workspace = load_workspace(root=root)
    if workspace["status"] == "OBSERVED_WATCH_AIM_UNCHANGED":
        return workspace
    observed = admit_watch_observation(workspace)
    persist_workspace(observed, root=root)
    return load_workspace(root=root)
