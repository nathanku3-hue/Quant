"""Shared confined atomic persistence for all operated-portfolio scenarios."""

from __future__ import annotations

import hashlib
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
from gv_portfolio_v0.operated_scenarios import (
    DEFAULT_SCENARIO_ID,
    PORTFOLIO_25_SCENARIO_ID,
    get_scenario,
)

PERSISTED_SCHEMA = "gv_operated_portfolio_persisted_v3"


def selected_scenario_id(*, env: Mapping[str, str] | None = None) -> str:
    values = dict(os.environ if env is None else env)
    scenario_id = values.get("GV_OPERATED_SCENARIO_ID", DEFAULT_SCENARIO_ID)
    try:
        get_scenario(scenario_id)
    except ValueError as exc:
        raise OperatedPortfolioError(str(exc)) from exc
    return scenario_id


def _scenario_storage_key(scenario_id: str) -> str:
    try:
        get_scenario(scenario_id)
    except ValueError as exc:
        raise OperatedPortfolioError(str(exc)) from exc
    return hashlib.sha256(scenario_id.encode("utf-8")).hexdigest()


def _workspace_filename(scenario_id: str) -> str:
    if scenario_id == DEFAULT_SCENARIO_ID:
        return "operated_portfolio_10_workspace.json"
    if scenario_id == PORTFOLIO_25_SCENARIO_ID:
        return "operated_portfolio_25_workspace.json"
    storage_key = _scenario_storage_key(scenario_id)
    return f"operated_portfolio_scenario_{storage_key}.json"


def default_workspace_root(
    *,
    env: Mapping[str, str] | None = None,
    scenario_id: str | None = None,
) -> Path:
    values = dict(os.environ if env is None else env)
    override = values.get("GV_OPERATED_PORTFOLIO_HOME")
    if override:
        return Path(override).expanduser()
    selected = scenario_id or selected_scenario_id(env=values)
    if selected == DEFAULT_SCENARIO_ID:
        suffix = "10"
    elif selected == PORTFOLIO_25_SCENARIO_ID:
        suffix = "25"
    else:
        suffix = f"scenario_{_scenario_storage_key(selected)}"
    return Path.home() / ".terminal-zero" / f"gv_operated_portfolio_{suffix}"


def workspace_path(
    root: Path | None = None, *, scenario_id: str | None = None
) -> Path:
    selected = scenario_id or selected_scenario_id()
    base = (
        Path(root)
        if root is not None
        else default_workspace_root(scenario_id=selected)
    )
    return base / _workspace_filename(selected)


def _envelope(workspace: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(workspace)
    scenario_id = payload.get("scenario_id")
    if not isinstance(scenario_id, str):
        raise OperatedPortfolioError("WORKSPACE_SCENARIO_REQUIRED")
    return {
        "schema_version": PERSISTED_SCHEMA,
        "scenario_id": scenario_id,
        "scenario_hash": payload.get("scenario_hash"),
        "workspace_hash": domain_hash(
            "GV-OPERATED-PORTFOLIO:WORKSPACE:V3", payload
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
    scenario_id: str,
    require_workspace_file: bool = False,
) -> tuple[Path, Path]:
    lexical_root = _absolute_lexical(
        Path(root)
        if root is not None
        else default_workspace_root(scenario_id=scenario_id)
    )
    lexical_path = lexical_root / _workspace_filename(scenario_id)
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


def _atomic_write(
    path: Path, payload: Mapping[str, Any], *, scenario_id: str
) -> None:
    root = path.parent
    _confined_paths(root, scenario_id=scenario_id)
    root.mkdir(parents=True, exist_ok=True)
    confined_root, confined_path = _confined_paths(
        root, scenario_id=scenario_id
    )
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
        _confined_paths(root, scenario_id=scenario_id)
        if not _same_or_within(_canonical_candidate(temp_path), confined_root):
            raise OperatedPortfolioError("WORKSPACE_TEMP_PATH_ESCAPE")
        os.replace(temp_path, confined_path)
        _confined_paths(
            root, scenario_id=scenario_id, require_workspace_file=True
        )
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def persist_workspace(
    workspace: Mapping[str, Any], *, root: Path | None = None
) -> Path:
    scenario_id = workspace.get("scenario_id")
    if not isinstance(scenario_id, str):
        raise OperatedPortfolioError("WORKSPACE_SCENARIO_REQUIRED")
    validate_workspace(
        workspace, allow_draft=workspace.get("status") == STATUS_DRAFT
    )
    _, path = _confined_paths(root, scenario_id=scenario_id)
    _atomic_write(path, _envelope(workspace), scenario_id=scenario_id)
    return path


def _read_persisted_workspace(
    *, root: Path | None, scenario_id: str
) -> dict[str, Any]:
    _, path = _confined_paths(
        root, scenario_id=scenario_id, require_workspace_file=True
    )
    try:
        with path.open("r", encoding="utf-8") as stream:
            envelope = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise OperatedPortfolioError("WORKSPACE_READ_INVALID") from exc
    _confined_paths(
        root, scenario_id=scenario_id, require_workspace_file=True
    )
    if envelope.get("schema_version") != PERSISTED_SCHEMA:
        raise OperatedPortfolioError("PERSISTED_SCHEMA_INVALID")
    if envelope.get("scenario_id") != scenario_id:
        raise OperatedPortfolioError("PERSISTED_SCENARIO_ID_MISMATCH")
    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        raise OperatedPortfolioError("PERSISTED_WORKSPACE_OBJECT_REQUIRED")
    if envelope.get("scenario_hash") != workspace.get("scenario_hash"):
        raise OperatedPortfolioError("PERSISTED_SCENARIO_HASH_MISMATCH")
    expected_hash = domain_hash(
        "GV-OPERATED-PORTFOLIO:WORKSPACE:V3", workspace
    )
    if envelope.get("workspace_hash") != expected_hash:
        raise OperatedPortfolioError("WORKSPACE_HASH_MISMATCH")
    return workspace


def load_workspace(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    workspace = _read_persisted_workspace(root=root, scenario_id=selected)
    validate_workspace(
        workspace, allow_draft=workspace.get("status") == STATUS_DRAFT
    )
    return workspace


def ensure_workspace(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    _, path = _confined_paths(root, scenario_id=selected)
    if path.exists():
        return load_workspace(root=root, scenario_id=selected)
    draft = build_draft_workspace(selected)
    persist_workspace(draft, root=root)
    return load_workspace(root=root, scenario_id=selected)


def confirm_and_persist(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    workspace = ensure_workspace(root=root, scenario_id=selected)
    if workspace["status"] != STATUS_DRAFT:
        return workspace
    result = confirm_initial_portfolio(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root, scenario_id=selected)


def admit_no_change_and_persist(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    workspace = load_workspace(root=root, scenario_id=selected)
    if workspace["status"] != STATUS_FUNDED:
        return workspace
    result = admit_no_change_observation(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root, scenario_id=selected)


def authorize_transition_and_persist(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    workspace = load_workspace(root=root, scenario_id=selected)
    if workspace["status"] != STATUS_NO_CHANGE:
        return workspace
    result = authorize_portfolio_transition(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root, scenario_id=selected)


def append_correction_and_persist(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    selected = scenario_id or selected_scenario_id()
    workspace = load_workspace(root=root, scenario_id=selected)
    if workspace["status"] == STATUS_CORRECTED:
        return workspace
    if workspace["status"] != STATUS_TRANSITION:
        return workspace
    result = append_non_economic_correction(workspace)
    persist_workspace(result, root=root)
    return load_workspace(root=root, scenario_id=selected)


def persist_prospective_workspace(
    workspace: Mapping[str, Any], *, root: Path | None = None
) -> Path:
    """Persist prospective state through the same confined atomic envelope."""

    from gv_portfolio_v0.prospective import validate_prospective_workspace

    scenario_id = workspace.get("scenario_id")
    if not isinstance(scenario_id, str):
        raise OperatedPortfolioError("WORKSPACE_SCENARIO_REQUIRED")
    validate_prospective_workspace(workspace)
    _, path = _confined_paths(root, scenario_id=scenario_id)
    _atomic_write(path, _envelope(workspace), scenario_id=scenario_id)
    return path


def load_prospective_workspace(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
    from gv_portfolio_v0.prospective import validate_prospective_workspace

    selected = scenario_id or PROSPECTIVE_25_SCENARIO_ID
    workspace = _read_persisted_workspace(root=root, scenario_id=selected)
    validate_prospective_workspace(workspace)
    return workspace


def ensure_prospective_workspace(
    *, root: Path | None = None, scenario_id: str | None = None
) -> dict[str, Any]:
    from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
    from gv_portfolio_v0.prospective import build_prospective_workspace

    selected = scenario_id or PROSPECTIVE_25_SCENARIO_ID
    _, path = _confined_paths(root, scenario_id=selected)
    if path.exists():
        return load_prospective_workspace(root=root, scenario_id=selected)
    workspace = build_prospective_workspace(selected)
    if workspace["scenario_id"] != selected:
        raise OperatedPortfolioError("PROSPECTIVE_SCENARIO_MISMATCH")
    persist_prospective_workspace(workspace, root=root)
    return load_prospective_workspace(root=root, scenario_id=selected)


def confirm_prospective_observation_and_persist(
    proposal: Mapping[str, Any],
    *,
    root: Path | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
    from gv_portfolio_v0.prospective import confirm_runtime_observation

    selected = scenario_id or PROSPECTIVE_25_SCENARIO_ID
    workspace = load_prospective_workspace(root=root, scenario_id=selected)
    result = confirm_runtime_observation(workspace, proposal)
    persist_prospective_workspace(result, root=root)
    return load_prospective_workspace(root=root, scenario_id=selected)


def reject_prospective_observation_and_persist(
    proposal: Mapping[str, Any],
    rejection_reason: str,
    *,
    root: Path | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
    from gv_portfolio_v0.prospective import reject_runtime_observation

    selected = scenario_id or PROSPECTIVE_25_SCENARIO_ID
    workspace = load_prospective_workspace(root=root, scenario_id=selected)
    result = reject_runtime_observation(
        workspace, proposal, rejection_reason
    )
    persist_prospective_workspace(result, root=root)
    return load_prospective_workspace(root=root, scenario_id=selected)
