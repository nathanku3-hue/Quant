from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import textwrap

import pytest

from core.gv_fs0_canonical import canonical_document_bytes
from gv_portfolio_v0.operated_scenarios import (
    PORTFOLIO_25_SCENARIO_ID,
    PROSPECTIVE_25_SCENARIO_ID,
    SCENARIO_25,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    load_prospective_workspace,
    reject_prospective_observation_and_persist,
    workspace_path,
)
from gv_portfolio_v0.prospective import (
    ProspectiveOperationError,
    build_prospective_workspace,
    preview_runtime_observation,
    reconstruct_prospective_workspace,
    validate_prospective_workspace,
)

ROOT = Path(__file__).resolve().parents[2]
_FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import hashlib
    import json
    from pathlib import Path
    import sys

    from core.gv_fs0_canonical import canonical_document_bytes
    from gv_portfolio_v0.operated_scenarios import PROSPECTIVE_25_SCENARIO_ID
    from gv_portfolio_v0.operated_storage import load_prospective_workspace
    from gv_portfolio_v0.prospective import reconstruct_prospective_workspace

    root = Path(sys.argv[1])
    workspace = load_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    reconstructed = reconstruct_prospective_workspace(workspace["events"])
    print(
        json.dumps(
            {
                "workspace_hash": hashlib.sha256(
                    canonical_document_bytes(workspace)
                ).hexdigest(),
                "reconstructed_hash": hashlib.sha256(
                    canonical_document_bytes(reconstructed)
                ).hexdigest(),
                "evidence_hash": hashlib.sha256(
                    canonical_document_bytes(workspace["evidence_references"])
                ).hexdigest(),
                "reviews_hash": hashlib.sha256(
                    canonical_document_bytes(workspace["reviews"])
                ).hexdigest(),
                "observations_hash": hashlib.sha256(
                    canonical_document_bytes(workspace["observations"])
                ).hexdigest(),
                "snapshots_hash": hashlib.sha256(
                    canonical_document_bytes(workspace["decision_snapshots"])
                ).hexdigest(),
                "certification_id": workspace["certification"]["certification_id"],
                "book_hash": workspace["book"]["book_hash"],
                "episode_count": workspace["prospective_episode_count"],
            },
            sort_keys=True,
        )
    )
    """
)


def _target_review(workspace: dict[str, object]) -> dict[str, object]:
    return next(row for row in workspace["reviews"] if row["symbol"] == "NSTAR")


def _request(workspace: dict[str, object]) -> dict[str, object]:
    review = _target_review(workspace)
    return {
        "content": (
            "Northstar runtime renewal evidence remained inside the declared watch "
            "band after operator review."
        ),
        "locator": "operator://2026-10-01/nstar-renewal-review",
        "observed_at": "2026-10-01T12:00:00.000000Z",
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": review["outcome"],
                "net_score_bps": review["net_score_bps"],
                "target_quantity": review["target_quantity"],
                "principal_claim": (
                    "Renewal durability remains intact after the operator-supplied "
                    "runtime observation."
                ),
            }
        ],
        "operator_rationale": (
            "The new source remains inside the declared watch band, so preserve "
            "capital, cash, and target quantity."
        ),
    }


def _transition_request(workspace: dict[str, object]) -> dict[str, object]:
    harbor = next(row for row in workspace["reviews"] if row["symbol"] == "HARBOR")
    meridian = next(row for row in workspace["reviews"] if row["symbol"] == "MERID")
    return {
        "content": (
            "Harbor backlog quality weakened below its funding band while Meridian "
            "converted qualification into a firm operator-reviewed order."
        ),
        "locator": "operator://2026-10-15/harbor-meridian-review",
        "observed_at": "2026-10-15T12:00:00.000000Z",
        "review_updates": [
            {
                "instrument_id": harbor["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 260,
                "target_quantity": "6",
                "principal_claim": (
                    "Backlog quality weakened; retain only a reduced monitoring position."
                ),
            },
            {
                "instrument_id": meridian["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 590,
                "target_quantity": "5",
                "principal_claim": (
                    "A firm qualification order now supports bounded prospective funding."
                ),
            },
        ],
        "operator_rationale": (
            "Reduce Harbor and fund Meridian because the runtime evidence reverses "
            "their relative capital priority."
        ),
    }


def _rejection_request(workspace: dict[str, object]) -> dict[str, object]:
    orbit = next(row for row in workspace["reviews"] if row["symbol"] == "ORBIT")
    return {
        "content": (
            "Orbit runtime booking evidence improved, but concentration remained too "
            "uncertain for the operator to grant decision authority."
        ),
        "locator": "operator://2026-11-01/orbit-bookings-review",
        "observed_at": "2026-11-01T12:00:00.000000Z",
        "review_updates": [
            {
                "instrument_id": orbit["instrument_id"],
                "outcome": orbit["outcome"],
                "net_score_bps": orbit["net_score_bps"],
                "target_quantity": orbit["target_quantity"],
                "principal_claim": (
                    "Booking evidence improved, but concentration still blocks funding."
                ),
            }
        ],
        "operator_rationale": (
            "The proposal is internally consistent but the source is not yet strong "
            "enough to become portfolio decision authority."
        ),
    }


def _fresh_receipt(root: Path) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-c", _FRESH_PROCESS_SCRIPT, str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout)


def test_prospective_profile_derives_accepted_25_catalogue_without_authored_episodes() -> None:
    scenario = get_scenario(PROSPECTIVE_25_SCENARIO_ID)
    assert scenario["source_scenario_id"] == PORTFOLIO_25_SCENARIO_ID
    assert scenario["runtime_observation_mode"] is True
    assert canonical_document_bytes(scenario["instruments"]) == canonical_document_bytes(
        SCENARIO_25["instruments"]
    )
    assert scenario["portfolio_aim"]["effective_at"] == "2026-08-01T09:00:00.000000Z"
    assert scenario["timeline"]["initial_certified_at"] == "2026-08-01T09:20:00.000000Z"
    assert "no_change" not in scenario
    assert "transition" not in scenario
    assert "correction" not in scenario


def test_bootstrap_is_certified_funded_25_security_baseline() -> None:
    workspace = build_prospective_workspace()
    validate_prospective_workspace(workspace)
    assert workspace["status"] == "FUNDED_CERTIFIED"
    assert len(workspace["instruments"]) == 25
    assert workspace["prospective_episode_count"] == 0
    assert workspace["observations"] == []
    assert workspace["baseline_event_count"] == len(workspace["events"])
    assert workspace["book"]["unexplained_residual"] == "0"
    assert workspace["certification"]["certification_id"].startswith("CRT_")


def test_preview_is_mutation_free_and_non_authoritative(tmp_path: Path) -> None:
    root = tmp_path / "prospective"
    workspace = ensure_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    path = workspace_path(root, scenario_id=PROSPECTIVE_25_SCENARIO_ID)
    persisted_before = path.read_bytes()
    workspace_before = canonical_document_bytes(workspace)

    proposal = preview_runtime_observation(workspace, _request(workspace))

    assert path.read_bytes() == persisted_before
    assert canonical_document_bytes(workspace) == workspace_before
    assert proposal["economics_changed"] is False
    assert proposal["evidence"]["content_sha256"] == hashlib.sha256(
        proposal["request"]["content"].encode("utf-8")
    ).hexdigest()
    assert proposal["review_changes"][0]["after"]["living_thesis_lite"][
        "evidence_reference_ids"
    ][-1] == proposal["evidence"]["evidence_reference_id"]
    assert proposal["changed_why"]["holdings_changed"] is False
    assert proposal["changed_why"]["cash_changed"] is False
    assert proposal["changed_why"]["orders_created"] == 0
    assert proposal["prior_event_count"] == len(workspace["events"])


def test_cash_cannot_be_used_as_per_security_review_outcome() -> None:
    workspace = build_prospective_workspace()
    request = _request(workspace)
    request["review_updates"][0]["outcome"] = "CASH"
    with pytest.raises(ProspectiveOperationError, match="CASH_IS_PORTFOLIO_CANDIDATE"):
        preview_runtime_observation(workspace, request)


def test_non_admit_review_cannot_retain_funded_quantity() -> None:
    workspace = build_prospective_workspace()
    request = _request(workspace)
    request["review_updates"][0]["outcome"] = "REJECT"
    with pytest.raises(
        ProspectiveOperationError,
        match="NON_ADMIT_TARGET_QUANTITY_MUST_BE_ZERO",
    ):
        preview_runtime_observation(workspace, request)


def test_observation_timestamp_must_follow_current_authority() -> None:
    workspace = build_prospective_workspace()
    request = _request(workspace)
    request["observed_at"] = "2026-08-01T09:20:00.000000Z"
    with pytest.raises(
        ProspectiveOperationError, match="OBSERVATION_TIMESTAMP_NOT_AFTER_AUTHORITY"
    ):
        preview_runtime_observation(workspace, request)


def test_current_date_observation_can_follow_prospective_bootstrap() -> None:
    workspace = build_prospective_workspace()
    request = _request(workspace)
    request["observed_at"] = "2026-08-02T00:00:00.000000Z"

    proposal = preview_runtime_observation(workspace, request)

    assert proposal["request"]["observed_at"] == "2026-08-02T00:00:00.000000Z"
    assert proposal["economics_changed"] is False


def test_single_sided_transition_is_rejected() -> None:
    workspace = build_prospective_workspace()
    request = _request(workspace)
    request["review_updates"][0]["outcome"] = "ABSTAIN"
    request["review_updates"][0]["target_quantity"] = "0"
    with pytest.raises(
        ProspectiveOperationError, match="PROSPECTIVE_TRANSITION_BUY_REQUIRED"
    ):
        preview_runtime_observation(workspace, request)


def test_confirm_is_append_only_persists_and_reconstructs_full_state(
    tmp_path: Path,
) -> None:
    root = tmp_path / "prospective"
    baseline = ensure_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    proposal = preview_runtime_observation(baseline, _request(baseline))
    confirmed = confirm_prospective_observation_and_persist(
        proposal,
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )

    assert confirmed["events"][: baseline["baseline_event_count"]] == baseline["events"]
    assert len(confirmed["events"]) == len(baseline["events"]) + 2
    assert [row["event_type"] for row in confirmed["events"][-2:]] == [
        "LATER_OBSERVATION_ADMITTED",
        "CERTIFICATION_RECORDED",
    ]
    assert confirmed["prospective_episode_count"] == 1
    assert confirmed["operator_action_count"] == 2
    assert len(confirmed["evidence_references"]) == 26
    assert len(confirmed["reviews"]) == 25
    assert len(confirmed["observations"]) == 1
    assert len(confirmed["decision_snapshots"]) == 2
    assert len(confirmed["certification_history"]) == 1
    assert confirmed["book"]["book_hash"] == baseline["book"]["book_hash"]
    assert canonical_document_bytes(confirmed["book"]) == canonical_document_bytes(
        baseline["book"]
    )
    assert canonical_document_bytes(confirmed["orders"]) == canonical_document_bytes(
        baseline["orders"]
    )
    assert canonical_document_bytes(confirmed["fills"]) == canonical_document_bytes(
        baseline["fills"]
    )

    reconstructed = reconstruct_prospective_workspace(confirmed["events"])
    assert canonical_document_bytes(reconstructed) == canonical_document_bytes(confirmed)
    reopened = load_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    assert canonical_document_bytes(reopened) == canonical_document_bytes(confirmed)

    completed = subprocess.run(
        [sys.executable, "-c", _FRESH_PROCESS_SCRIPT, str(root)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    expected_hash = hashlib.sha256(canonical_document_bytes(confirmed)).hexdigest()
    assert receipt["workspace_hash"] == expected_hash
    assert receipt["reconstructed_hash"] == expected_hash
    assert receipt["episode_count"] == 1
    assert receipt["book_hash"] == baseline["book"]["book_hash"]
    assert receipt["certification_id"] == confirmed["certification"]["certification_id"]


def test_runtime_transition_previews_confirms_and_reconstructs_on_same_projector(
    tmp_path: Path,
) -> None:
    root = tmp_path / "prospective-transition"
    baseline = ensure_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    first = confirm_prospective_observation_and_persist(
        preview_runtime_observation(baseline, _request(baseline)),
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )
    persisted_before = workspace_path(
        root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    ).read_bytes()
    state_before = canonical_document_bytes(first)

    proposal = preview_runtime_observation(first, _transition_request(first))

    assert workspace_path(
        root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    ).read_bytes() == persisted_before
    assert canonical_document_bytes(first) == state_before
    assert proposal["economics_changed"] is True
    assert proposal["changed_why"]["change_type"] == "PROSPECTIVE_TRANSITION"
    assert [row["side"] for row in proposal["transition"]["legs"]] == [
        "SELL",
        "BUY",
    ]
    assert proposal["transition"]["order_count"] == 2
    assert proposal["transition"]["unexplained_residual"] == "0"
    assert proposal["transition"]["book_hash_after"] != first["book"]["book_hash"]

    transitioned = confirm_prospective_observation_and_persist(
        proposal,
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )
    assert transitioned["prospective_episode_count"] == 2
    assert transitioned["operator_action_count"] == 4
    assert transitioned["changed_why"]["change_type"] == "PROSPECTIVE_TRANSITION"
    assert transitioned["changed_why"]["orders_created"] == 2
    assert transitioned["book"]["unexplained_residual"] == "0"
    assert transitioned["book"]["book_hash"] == proposal["transition"][
        "book_hash_after"
    ]
    assert len(transitioned["orders"]) == len(first["orders"]) + 2
    assert len(transitioned["fills"]) == len(first["fills"]) + 2
    assert [row["side"] for row in transitioned["orders"][-2:]] == [
        "SELL",
        "BUY",
    ]
    assert canonical_document_bytes(
        reconstruct_prospective_workspace(transitioned["events"])
    ) == canonical_document_bytes(transitioned)
    assert canonical_document_bytes(
        load_prospective_workspace(
            root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
        )
    ) == canonical_document_bytes(transitioned)


def test_three_sequential_runtime_episodes_reopen_after_each_and_reject_without_authority(
    tmp_path: Path,
) -> None:
    root = tmp_path / "prospective-three-episodes"
    baseline = ensure_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )

    first = confirm_prospective_observation_and_persist(
        preview_runtime_observation(baseline, _request(baseline)),
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )
    first_receipt = _fresh_receipt(root)
    assert first_receipt["episode_count"] == 1
    assert first_receipt["workspace_hash"] == first_receipt["reconstructed_hash"]

    second = confirm_prospective_observation_and_persist(
        preview_runtime_observation(first, _transition_request(first)),
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )
    second_receipt = _fresh_receipt(root)
    assert second_receipt["episode_count"] == 2
    assert second_receipt["workspace_hash"] == second_receipt["reconstructed_hash"]
    book_after_transition = deepcopy(second["book"])
    evidence_after_transition = deepcopy(second["evidence_references"])
    reviews_after_transition = deepcopy(second["reviews"])
    observations_after_transition = deepcopy(second["observations"])
    snapshots_after_transition = deepcopy(second["decision_snapshots"])
    orders_after_transition = deepcopy(second["orders"])
    fills_after_transition = deepcopy(second["fills"])

    rejected_proposal = preview_runtime_observation(
        second, _rejection_request(second)
    )
    third = reject_prospective_observation_and_persist(
        rejected_proposal,
        "Source quality is insufficient for decision authority; retain as a rejected proposal.",
        root=root,
        scenario_id=PROSPECTIVE_25_SCENARIO_ID,
    )
    third_receipt = _fresh_receipt(root)
    assert third_receipt["episode_count"] == 3
    assert third_receipt["workspace_hash"] == third_receipt["reconstructed_hash"]

    assert third["prospective_episode_count"] == 3
    assert third["operator_action_count"] == 6
    assert [
        row["disposition"] for row in third["prospective_episode_history"]
    ] == ["CONFIRMED", "CONFIRMED", "REJECTED"]
    assert len(third["prospective_proposals"]) == 2
    assert len(third["rejected_proposals"]) == 1
    assert third["rejected_proposals"][0]["proposal_id"] == rejected_proposal[
        "proposal_id"
    ]
    assert canonical_document_bytes(third["book"]) == canonical_document_bytes(
        book_after_transition
    )
    assert canonical_document_bytes(
        third["evidence_references"]
    ) == canonical_document_bytes(evidence_after_transition)
    assert canonical_document_bytes(third["reviews"]) == canonical_document_bytes(
        reviews_after_transition
    )
    assert canonical_document_bytes(
        third["observations"]
    ) == canonical_document_bytes(observations_after_transition)
    assert canonical_document_bytes(
        third["decision_snapshots"]
    ) == canonical_document_bytes(snapshots_after_transition)
    assert canonical_document_bytes(third["orders"]) == canonical_document_bytes(
        orders_after_transition
    )
    assert canonical_document_bytes(third["fills"]) == canonical_document_bytes(
        fills_after_transition
    )
    assert len(third["certification_history"]) == 3
    assert [row["event_type"] for row in third["events"][-2:]] == [
        "PROSPECTIVE_PROPOSAL_REJECTED",
        "CERTIFICATION_RECORDED",
    ]
    assert canonical_document_bytes(
        reconstruct_prospective_workspace(third["events"])
    ) == canonical_document_bytes(third)


def test_mutated_or_stale_proposal_cannot_be_confirmed(tmp_path: Path) -> None:
    root = tmp_path / "prospective"
    workspace = ensure_prospective_workspace(
        root=root, scenario_id=PROSPECTIVE_25_SCENARIO_ID
    )
    proposal = preview_runtime_observation(workspace, _request(workspace))
    tampered = deepcopy(proposal)
    tampered["changed_why"]["reason"] = "silently changed"
    with pytest.raises(ProspectiveOperationError, match="STALE_OR_MUTATED_PROPOSAL"):
        confirm_prospective_observation_and_persist(
            tampered,
            root=root,
            scenario_id=PROSPECTIVE_25_SCENARIO_ID,
        )
