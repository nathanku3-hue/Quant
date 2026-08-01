from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import textwrap
from typing import Any

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated import (
    OperatedPortfolioError,
    STATUS_CORRECTED,
    STATUS_DRAFT,
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
    ENGINE_SCALE_100_SCENARIO_ID,
    ENGINE_SCALE_50_SCENARIO_ID,
    PORTFOLIO_25_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    admit_no_change_and_persist,
    authorize_transition_and_persist,
    confirm_and_persist,
    default_workspace_root,
    ensure_workspace,
    load_workspace,
    workspace_path,
)

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = (
    (ENGINE_SCALE_50_SCENARIO_ID, 50),
    (ENGINE_SCALE_100_SCENARIO_ID, 100),
)

_FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import hashlib
    import json
    from pathlib import Path
    import sys

    from core.gv_fs0_canonical import canonical_document_bytes
    from gv_portfolio_v0.operated import (
        STATUS_CORRECTED,
        STATUS_TRANSITION,
        validate_workspace,
    )
    from gv_portfolio_v0.operated_storage import (
        append_correction_and_persist,
        load_workspace,
    )
    from gv_portfolio_v0.replay import reconstruct_exact, replay_idempotent

    root = Path(sys.argv[1])
    scenario_id = sys.argv[2]
    action = sys.argv[3]
    workspace = load_workspace(root=root, scenario_id=scenario_id)
    if action == "correct":
        if workspace["status"] != STATUS_TRANSITION:
            raise AssertionError(workspace["status"])
        workspace = append_correction_and_persist(
            root=root, scenario_id=scenario_id
        )
    elif action == "verify":
        if workspace["status"] != STATUS_CORRECTED:
            raise AssertionError(workspace["status"])
    else:
        raise AssertionError(action)

    validate_workspace(workspace)
    reconstructed = reconstruct_exact(
        workspace["events"], expected_book=workspace["book"]
    )
    replayed = replay_idempotent(workspace["events"])
    print(
        json.dumps(
            {
                "status": workspace["status"],
                "residual": workspace["book"]["unexplained_residual"],
                "book_hash": workspace["book"]["book_hash"],
                "reconstructed_book_hash": reconstructed["book_hash"],
                "replayed_book_hash": replayed["book_hash"],
                "workspace_hash": hashlib.sha256(
                    canonical_document_bytes(workspace)
                ).hexdigest(),
            },
            sort_keys=True,
        )
    )
    """
)


def _full_flow(scenario_id: str) -> dict[str, object]:
    workspace = build_draft_workspace(scenario_id)
    workspace = confirm_initial_portfolio(workspace)
    workspace = admit_no_change_observation(workspace)
    workspace = authorize_portfolio_transition(workspace)
    workspace = append_non_economic_correction(workspace)
    validate_workspace(workspace)
    return workspace


def _run_fresh_process(
    root: Path, scenario_id: str, action: str
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            _FRESH_PROCESS_SCRIPT,
            str(root),
            scenario_id,
            action,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def _timestamp_values(value: Any, path: str = "root") -> list[tuple[str, datetime]]:
    rows: list[tuple[str, datetime]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(child, str) and key.endswith("_at"):
                rows.append(
                    (
                        child_path,
                        datetime.fromisoformat(child.replace("Z", "+00:00")),
                    )
                )
            else:
                rows.extend(_timestamp_values(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_timestamp_values(child, f"{path}[{index}]"))
    return rows


def _assert_monotonic(
    workspace: dict[str, Any], collection: str, timestamp_key: str
) -> None:
    timestamps = [
        datetime.fromisoformat(row[timestamp_key].replace("Z", "+00:00"))
        for row in workspace[collection]
    ]
    assert timestamps == sorted(timestamps), collection


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_characterization_scenarios_are_declarative_and_unique(
    scenario_id: str, size: int
) -> None:
    scenario = get_scenario(scenario_id)
    assert len(scenario["instruments"]) == size
    assert len({row["permanent_key"] for row in scenario["instruments"]}) == size
    assert len({row["symbol"] for row in scenario["instruments"]}) == size
    assert "Synthetic" in scenario["claim_boundary"]
    assert "not Universe acceptance" in scenario["claim_boundary"]


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_existing_engine_completes_characterization_in_memory(
    scenario_id: str, size: int
) -> None:
    workspace = _full_flow(scenario_id)
    assert workspace["status"] == STATUS_CORRECTED
    assert len(workspace["instruments"]) == size
    assert workspace["book"]["unexplained_residual"] == "0"
    assert [row["side"] for row in workspace["orders"][-2:]] == ["SELL", "BUY"]
    assert len(workspace["certification_history"]) == 3

    repeated = _full_flow(scenario_id)
    assert canonical_document_bytes(repeated) == canonical_document_bytes(workspace)


def test_legacy_storage_paths_remain_exact() -> None:
    root = Path("legacy-root")
    assert workspace_path(
        root, scenario_id=DEFAULT_SCENARIO_ID
    ) == root / "operated_portfolio_10_workspace.json"
    assert workspace_path(
        root, scenario_id=PORTFOLIO_25_SCENARIO_ID
    ) == root / "operated_portfolio_25_workspace.json"
    assert default_workspace_root(scenario_id=DEFAULT_SCENARIO_ID).name == (
        "gv_operated_portfolio_10"
    )
    assert default_workspace_root(scenario_id=PORTFOLIO_25_SCENARIO_ID).name == (
        "gv_operated_portfolio_25"
    )


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_registered_scale_scenarios_use_collision_safe_storage_paths(
    tmp_path: Path, scenario_id: str, size: int
) -> None:
    digest = hashlib.sha256(scenario_id.encode("utf-8")).hexdigest()
    root = tmp_path / "shared-operated-root"
    path = workspace_path(root, scenario_id=scenario_id)
    assert path.name == f"operated_portfolio_scenario_{digest}.json"
    assert default_workspace_root(scenario_id=scenario_id).name == (
        f"gv_operated_portfolio_scenario_{digest}"
    )

    draft = ensure_workspace(root=root, scenario_id=scenario_id)
    assert draft["status"] == STATUS_DRAFT
    assert len(draft["instruments"]) == size
    assert path.is_file()
    assert load_workspace(root=root, scenario_id=scenario_id) == draft

    other_scenario_id = (
        ENGINE_SCALE_100_SCENARIO_ID
        if scenario_id == ENGINE_SCALE_50_SCENARIO_ID
        else ENGINE_SCALE_50_SCENARIO_ID
    )
    assert path != workspace_path(root, scenario_id=other_scenario_id)


def test_unregistered_scenario_still_fails_closed() -> None:
    with pytest.raises(
        OperatedPortfolioError, match="UNKNOWN_OPERATED_SCENARIO:UNREGISTERED"
    ):
        workspace_path(Path("root"), scenario_id="UNREGISTERED")


@pytest.mark.parametrize(("scenario_id", "size"), SCENARIOS)
def test_scale_persistence_fresh_reopen_correction_and_replay(
    tmp_path: Path, scenario_id: str, size: int
) -> None:
    root = tmp_path / f"scale-{size}"
    draft = ensure_workspace(root=root, scenario_id=scenario_id)
    assert draft["status"] == STATUS_DRAFT

    confirm_and_persist(root=root, scenario_id=scenario_id)
    admit_no_change_and_persist(root=root, scenario_id=scenario_id)
    transitioned = authorize_transition_and_persist(
        root=root, scenario_id=scenario_id
    )
    assert transitioned["status"] == STATUS_TRANSITION
    assert transitioned["book"]["unexplained_residual"] == "0"

    corrected_process = _run_fresh_process(root, scenario_id, "correct")
    assert corrected_process["status"] == STATUS_CORRECTED
    assert corrected_process["residual"] == "0"
    assert corrected_process["book_hash"] == corrected_process[
        "reconstructed_book_hash"
    ]
    assert corrected_process["book_hash"] == corrected_process[
        "replayed_book_hash"
    ]

    verification_process = _run_fresh_process(root, scenario_id, "verify")
    assert verification_process == corrected_process

    corrected = load_workspace(root=root, scenario_id=scenario_id)
    assert corrected["status"] == STATUS_CORRECTED
    assert len(corrected["instruments"]) == size
    assert corrected["book"]["unexplained_residual"] == "0"
    assert hashlib.sha256(canonical_document_bytes(corrected)).hexdigest() == (
        corrected_process["workspace_hash"]
    )

    timestamps = _timestamp_values(corrected)
    assert timestamps
    _assert_monotonic(corrected, "evidence_references", "observed_at")
    _assert_monotonic(corrected, "events", "effective_at")
    _assert_monotonic(corrected, "orders", "created_at")
    _assert_monotonic(corrected, "fills", "filled_at")


@pytest.mark.parametrize(
    ("scenario_id", "size", "expected_last"),
    (
        (ENGINE_SCALE_50_SCENARIO_ID, 50, "2026-09-01T12:49:00.000000Z"),
        (ENGINE_SCALE_100_SCENARIO_ID, 100, "2026-09-01T13:39:00.000000Z"),
    ),
)
def test_initial_evidence_timestamps_are_valid_and_roll_over_monotonically(
    scenario_id: str, size: int, expected_last: str
) -> None:
    workspace = build_draft_workspace(scenario_id)
    observed = [
        row["observed_at"] for row in workspace["evidence_references"][:size]
    ]
    parsed = [
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        for value in observed
    ]
    assert observed[0] == "2026-09-01T12:00:00.000000Z"
    assert observed[min(size - 1, 24)] == "2026-09-01T12:24:00.000000Z"
    assert observed[-1] == expected_last
    assert parsed == sorted(parsed)
    assert len(set(parsed)) == size
    if size == 100:
        assert observed[59] == "2026-09-01T12:59:00.000000Z"
        assert observed[60] == "2026-09-01T13:00:00.000000Z"


def test_characterization_does_not_mutate_accepted_25_scenario() -> None:
    from gv_portfolio_v0.operated_scenarios import SCENARIO_25

    accepted = deepcopy(SCENARIO_25)
    get_scenario(ENGINE_SCALE_50_SCENARIO_ID)
    get_scenario(ENGINE_SCALE_100_SCENARIO_ID)
    assert get_scenario(PORTFOLIO_25_SCENARIO_ID) == accepted
