"""PAIR-DECISION-SERIES-1 temporal pair product operation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import textwrap

import pytest

from core.gv_fs0_canonical import canonical_document_bytes, parse_canonical_document_bytes, domain_hash
from gv_portfolio_v0.market_packet import content_sha256_for_market_packet
from gv_portfolio_v0.operated import OperatedPortfolioError
from gv_portfolio_v0.operated_scenarios import (
    PAIR_DECISION_SERIES_SCENARIO_ID,
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
    build_pair_episode_request,
    preview_runtime_observation,
    reconstruct_prospective_workspace,
)

ROOT = Path(__file__).resolve().parents[1]

_FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import hashlib
    import json
    from pathlib import Path
    import sys
    from core.gv_fs0_canonical import canonical_document_bytes
    from gv_portfolio_v0.operated_scenarios import PAIR_DECISION_SERIES_SCENARIO_ID
    from gv_portfolio_v0.operated_storage import load_prospective_workspace
    from gv_portfolio_v0.prospective import reconstruct_prospective_workspace

    root = Path(sys.argv[1])
    workspace = load_prospective_workspace(
        root=root, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    reconstructed = reconstruct_prospective_workspace(
        workspace["events"], scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    print(json.dumps({
        "workspace_hash": hashlib.sha256(canonical_document_bytes(workspace)).hexdigest(),
        "reconstructed_hash": hashlib.sha256(canonical_document_bytes(reconstructed)).hexdigest(),
        "certification_id": workspace["certification"]["certification_id"],
        "series": workspace["decision_series_contract"]["decision_series_id"],
        "next_episode": workspace.get("next_series_episode_number"),
        "last_sealed_episode": (
            workspace["prospective_episode_history"][-1]["episode_number"]
            if workspace["prospective_episode_history"]
            else None
        ),
        "sealed": workspace["sealed_series_episode_count"],
        "opened": workspace["opened_outcome_episode_count"],
        "positions": workspace["book"]["positions"],
        "cash": workspace["book"]["total_cash"],
        "costs": workspace["book"]["total_costs"],
        "residual": workspace["book"]["unexplained_residual"],
    }, sort_keys=True))
    """
)


def _workspace(tmp_path: Path) -> dict[str, object]:
    return ensure_prospective_workspace(
        root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )


def _request(workspace: dict[str, object]) -> dict[str, object]:
    return build_pair_episode_request(
        workspace,
        operator_rationale=(
            "The common source cut is valid, but banked evidence does not establish a "
            "cost-aware expected-return edge for either security. Retain certified cash."
        ),
    )


def _element_by_key(collection: object, key: str) -> object:
    return next(element for element in collection if getattr(element, "key", None) == key)


def _app_blob(app: object) -> str:
    values: list[str] = []
    for name in ("header", "subheader", "caption", "info", "warning", "success", "error", "table"):
        for element in getattr(app, name):
            values.append(str(getattr(element, "value", element)))
    return "\n".join(values)


def test_pair_profile_has_two_real_identities_and_cash_only_baseline(tmp_path: Path) -> None:
    scenario = get_scenario(PAIR_DECISION_SERIES_SCENARIO_ID)
    assert [row["symbol"] for row in scenario["instruments"]] == ["MU", "NVDA"]
    assert len({row["permanent_key"] for row in scenario["instruments"]}) == 2
    assert len({row["economic_cluster"] for row in scenario["instruments"]}) == 2
    assert all(row["target_quantity"] == "0" for row in scenario["instruments"])
    assert all(row["outcome"] == "ABSTAIN" for row in scenario["instruments"])
    workspace = _workspace(tmp_path)
    assert workspace["book"]["positions"] == []
    assert workspace["book"]["total_cash"] == "11000"
    assert workspace["book"]["total_costs"] == "0"
    assert workspace["book"]["unexplained_residual"] == "0"
    assert workspace["sealed_series_episode_count"] == 0
    assert workspace["opened_outcome_episode_count"] == 0


def test_pair_preview_is_mutation_free_and_seals_cash_abstention(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    before = canonical_document_bytes(workspace)
    proposal = preview_runtime_observation(workspace, _request(workspace))
    assert canonical_document_bytes(workspace) == before
    assert proposal["economics_changed"] is False
    assert proposal["transition"] is None
    assert proposal["changed_why"]["change_type"] == (
        "PAIR_DECISION_SERIES_CASH_ABSTAIN"
    )
    assert proposal["request"]["selected_disposition"] == "CASH_ABSTAIN"
    assert len(proposal["request"]["source_derived_market_packets"]) == 2
    contract = proposal["request"]["decision_series_contract"]
    assert contract["episode_number"] == 1
    assert contract["outcome_status"] == "SEALED_NOT_OPENED"
    assert contract["outcome_data_loaded"] is False


def test_confirm_persists_certifies_and_reopens_exactly(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    prior_certification = workspace["certification"]["certification_id"]
    proposal = preview_runtime_observation(workspace, _request(workspace))
    confirmed = confirm_prospective_observation_and_persist(
        proposal, root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    assert confirmed["prospective_episode_count"] == 1
    assert confirmed["sealed_series_episode_count"] == 1
    assert confirmed["opened_outcome_episode_count"] == 0
    assert confirmed["next_series_episode_number"] == 2
    assert confirmed["decision_series_contract"]["episode_number"] == 2
    assert confirmed["certification"]["prior_certification_id"] == prior_certification
    assert confirmed["book"]["positions"] == []
    assert confirmed["orders"] == []
    assert confirmed["fills"] == []
    assert confirmed["book"]["total_cash"] == "11000"
    assert confirmed["book"]["total_costs"] == "0"
    assert confirmed["book"]["unexplained_residual"] == "0"
    history = confirmed["prospective_episode_history"][0]
    assert history["decision_series_id"] == "PAIR_DECISION_SERIES_1"
    assert history["episode_number"] == 1
    assert history["outcome_status"] == "SEALED_NOT_OPENED"

    reopened = load_prospective_workspace(
        root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    reconstructed = reconstruct_prospective_workspace(
        reopened["events"], scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    assert canonical_document_bytes(reopened) == canonical_document_bytes(reconstructed)

    expected_hash = hashlib.sha256(canonical_document_bytes(confirmed)).hexdigest()
    completed = subprocess.run(
        [sys.executable, "-c", _FRESH_PROCESS_SCRIPT, str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    receipt = json.loads(completed.stdout)
    assert receipt["workspace_hash"] == expected_hash
    assert receipt["reconstructed_hash"] == expected_hash
    assert receipt["series"] == "PAIR_DECISION_SERIES_1"
    assert receipt["last_sealed_episode"] == 1
    assert receipt["next_episode"] == 2
    assert receipt["sealed"] == 1
    assert receipt["opened"] == 0
    assert receipt["positions"] == []
    assert receipt["cash"] == "11000"
    assert receipt["costs"] == "0"
    assert receipt["residual"] == "0"


def test_reject_all_certifies_without_granting_subject_or_capital_authority(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    proposal = preview_runtime_observation(workspace, _request(workspace))
    rejected = reject_prospective_observation_and_persist(
        proposal,
        "The pair cut is valid but the combined package remains insufficient for capital authority.",
        root=tmp_path,
        scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
    )
    assert rejected["prospective_episode_count"] == 1
    assert rejected["prospective_episode_history"][0]["disposition"] == "REJECTED"
    assert rejected["prospective_episode_history"][0]["episode_number"] == 1
    assert rejected["book"]["positions"] == []
    assert rejected["orders"] == []
    assert rejected["fills"] == []
    assert rejected["book"]["total_cash"] == "11000"
    assert rejected["book"]["unexplained_residual"] == "0"


def test_manual_market_authority_fields_are_rejected(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    request["market_price"] = "999"
    with pytest.raises(ProspectiveOperationError, match="MANUAL_MARKET_AUTHORITY_PROHIBITED"):
        preview_runtime_observation(workspace, request)


def test_packet_substitution_fails_even_with_recomputed_packet_hash(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    packet = request["source_derived_market_packets"][0]
    packet["value"] = "1"
    packet["content_sha256"] = content_sha256_for_market_packet(packet)
    with pytest.raises(ProspectiveOperationError, match="NOT_SOURCE_DERIVED"):
        preview_runtime_observation(workspace, request)


def test_series_contract_and_outcome_opening_tamper_fail_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    request["decision_series_contract"]["outcome_data_loaded"] = True
    with pytest.raises(ProspectiveOperationError, match="SERIES_CONTRACT_MISMATCH"):
        preview_runtime_observation(workspace, request)
    request = _request(workspace)
    request["decision_series_contract"]["comparator_spec"]["primary"] = "AFTER_THE_FACT"
    with pytest.raises(ProspectiveOperationError, match="SERIES_CONTRACT_MISMATCH"):
        preview_runtime_observation(workspace, request)


def test_pit_identity_and_subject_decision_drift_fail_closed(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    request = _request(workspace)
    request["pit_identity"]["certified_book_id"] = "0" * 64
    request["pit_identity"]["market_snapshot_id"]["certified_book_id"] = "0" * 64
    with pytest.raises(ProspectiveOperationError, match="PIT_IDENTITY"):
        preview_runtime_observation(workspace, request)
    request = _request(workspace)
    request["review_updates"][1]["outcome"] = "ADMIT"
    request["review_updates"][1]["target_quantity"] = "1"
    with pytest.raises(ProspectiveOperationError, match="SUBJECT_DECISION_DRIFT"):
        preview_runtime_observation(workspace, request)


def test_episode_two_seals_later_cut_and_exact_reopen(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    first = confirm_prospective_observation_and_persist(
        preview_runtime_observation(workspace, _request(workspace)),
        root=tmp_path,
        scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
    )
    second_request = build_pair_episode_request(
        first,
        operator_rationale=(
            "A later common market cut is verified under unchanged series contracts; "
            "banked subject evidence still does not authorize capital. Retain cash."
        ),
    )
    assert second_request["decision_series_contract"]["episode_number"] == 2
    assert second_request["observed_at"] == "2026-08-06T12:00:00.000000Z"
    values = {
        packet["value"] for packet in second_request["source_derived_market_packets"]
    }
    assert values == {"852.19", "221.71"}
    second = confirm_prospective_observation_and_persist(
        preview_runtime_observation(first, second_request),
        root=tmp_path,
        scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
    )
    assert second["sealed_series_episode_count"] == 2
    assert second["next_series_episode_number"] is None
    assert [row["episode_number"] for row in second["prospective_episode_history"]] == [
        1,
        2,
    ]
    assert second["book"]["positions"] == []
    assert second["book"]["total_cash"] == "11000"
    assert second["book"]["total_costs"] == "0"
    assert second["book"]["unexplained_residual"] == "0"
    reopened = load_prospective_workspace(
        root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    reconstructed = reconstruct_prospective_workspace(
        reopened["events"], scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    assert canonical_document_bytes(reopened) == canonical_document_bytes(reconstructed)
    with pytest.raises(ProspectiveOperationError, match="PAIR_SERIES_NO_OPEN_EPISODE"):
        build_pair_episode_request(
            second, operator_rationale="No third registered episode."
        )


def test_episode_one_contract_cannot_be_resealed_after_episode_one(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    first_request = _request(workspace)
    confirmed = confirm_prospective_observation_and_persist(
        preview_runtime_observation(workspace, first_request),
        root=tmp_path,
        scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID,
    )
    with pytest.raises(
        ProspectiveOperationError,
        match=(
            "OBSERVATION_TIMESTAMP_NOT_AFTER_AUTHORITY|"
            "PAIR_DECISION_SERIES_CONTRACT_MISMATCH|"
            "PAIR_EPISODE_SEQUENCE_MISMATCH"
        ),
    ):
        preview_runtime_observation(confirmed, first_request)


def test_concurrent_confirm_allows_one_episode_only(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    proposal = preview_runtime_observation(workspace, _request(workspace))

    def confirm() -> str:
        try:
            result = confirm_prospective_observation_and_persist(
                proposal, root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
            )
            return f"ok:{result['prospective_episode_count']}"
        except Exception as exc:  # noqa: BLE001 - assertion captures fail-closed result
            return f"error:{type(exc).__name__}:{exc}"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: confirm(), range(2)))
    assert outcomes.count("ok:1") == 1
    assert sum(value.startswith("error:ProspectiveOperationError") for value in outcomes) == 1
    reopened = load_prospective_workspace(
        root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
    )
    assert reopened["prospective_episode_count"] == 1


def test_persisted_workspace_tamper_fails_closed(tmp_path: Path) -> None:
    _workspace(tmp_path)
    path = workspace_path(tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID)
    original = path.read_bytes()
    envelope = parse_canonical_document_bytes(original)
    envelope["workspace"]["decision_series_contract"]["episode_number"] = 2
    envelope["workspace_hash"] = domain_hash(
        "GV-OPERATED-PORTFOLIO:WORKSPACE:V3", envelope["workspace"]
    )
    path.write_bytes(canonical_document_bytes(envelope))
    try:
        with pytest.raises(
            (OperatedPortfolioError, ProspectiveOperationError),
            match="WORKSPACE_PROJECTION_MISMATCH|EPISODE",
        ):
            load_prospective_workspace(
                root=tmp_path, scenario_id=PAIR_DECISION_SERIES_SCENARIO_ID
            )
    finally:
        path.write_bytes(original)


def test_command_center_operates_and_reopens_episode_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_COMMAND_CENTER_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
    assert not app.exception, app.exception
    initial = _app_blob(app)
    assert "Active certified pair-series workspace" in initial
    assert "Seal real MU / NVDA / cash episode 1" in initial
    assert "CASH_ONLY" in initial
    source_table = next(
        element.value
        for element in app.table
        if "source_value" in element.value.columns
    )
    assert set(source_table["symbol"]) == {"MU", "NVDA"}
    assert set(source_table["source_value"].astype(str)) == {"866.15", "219.77"}
    all_keys = {
        getattr(element, "key", None)
        for collection in (app.text_input, app.number_input, app.text_area)
        for element in collection
    }
    assert "gv_command_center_market_price" not in all_keys
    assert "gv_command_center_market_source_identity" not in all_keys
    assert "gv_command_center_market_receipt" not in all_keys

    _element_by_key(app.button, "gv_command_center_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    preview = _app_blob(app)
    assert "Mutation-free PAIR-DECISION-SERIES-1 episode 1 preview" in preview
    preview_summary = next(
        element.value
        for element in app.table
        if "outcome_status" in element.value.columns
    )
    assert preview_summary.loc[0, "outcome_status"] == "SEALED_NOT_OPENED"
    assert bool(preview_summary.loc[0, "economics_changed"]) is False
    assert "residual=0" in preview

    _element_by_key(app.button, "gv_command_center_confirm").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    confirmed = _app_blob(app)
    assert "1 sealed episode" in confirmed
    assert "episode 2 is open" in confirmed
    assert "Seal real MU / NVDA / cash episode 2" in confirmed
    assert "CASH_ONLY" in confirmed
    source_table_e2 = next(
        element.value
        for element in app.table
        if "source_value" in element.value.columns
    )
    assert set(source_table_e2["source_value"].astype(str)) == {"852.19", "221.71"}

    fresh = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
    assert not fresh.exception, fresh.exception
    reopened = _app_blob(fresh)
    assert "1 sealed episode" in reopened
    assert "episode 2 is open" in reopened
    assert "CASH_ONLY" in reopened
