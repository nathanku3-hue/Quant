"""One bounded non-zero paper-capital operation through existing authority."""

from __future__ import annotations

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from decimal import localcontext
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import textwrap

import pytest

from core.gv_fs0_canonical import (
    canonical_decimal,
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
)
from core.gv_pit.adapters import build_real_pit_source_bundle
from core.gv_pit.contracts import canonical_value
from gv_portfolio_v0.operated_scenarios import (
    OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    REAL_MU_PROSPECTIVE_SCENARIO_ID,
    get_scenario,
)
from gv_portfolio_v0.operated_storage import (
    confirm_prospective_observation_and_persist,
    ensure_prospective_workspace,
    load_prospective_workspace,
    reject_prospective_observation_and_persist,
    workspace_path,
)
from gv_portfolio_v0.operated import OperatedPortfolioError
from gv_portfolio_v0.prospective import (
    MAX_PROSPECTIVE_EVENT_COUNT,
    ProspectiveOperationError,
    _positive_decimal_text,
    preview_runtime_observation,
    reconstruct_prospective_workspace,
)

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def _pit_identity() -> dict[str, object]:
    return canonical_value(build_real_pit_source_bundle().pit_identity)  # type: ignore[return-value]

_FRESH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import hashlib
    import json
    from pathlib import Path
    import sys

    from core.gv_fs0_canonical import canonical_document_bytes
    from gv_portfolio_v0.operated_scenarios import OPERATED_PAPER_CAPITAL_SCENARIO_ID
    from gv_portfolio_v0.operated_storage import load_prospective_workspace
    from gv_portfolio_v0.prospective import reconstruct_prospective_workspace

    root = Path(sys.argv[1])
    workspace = load_prospective_workspace(
        root=root,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    reconstructed = reconstruct_prospective_workspace(
        workspace["events"],
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    print(
        json.dumps(
            {
                "workspace_hash": hashlib.sha256(
                    canonical_document_bytes(workspace)
                ).hexdigest(),
                "reconstructed_hash": hashlib.sha256(
                    canonical_document_bytes(reconstructed)
                ).hexdigest(),
                "certification_id": workspace["certification"]["certification_id"],
                "book_hash": workspace["book"]["book_hash"],
                "positions": workspace["book"]["positions"],
                "classified_cash": workspace["book"]["classified_cash"],
                "costs": workspace["book"]["classified_costs"],
                "residual": workspace["book"]["unexplained_residual"],
            },
            sort_keys=True,
        )
    )
    """
)


def _request(
    workspace: dict[str, object],
    *,
    quantity: str = "10",
    price: str = "100",
    observed_at: str = "2026-08-04T12:01:00.000000Z",
    market_observed_at: str = "2026-08-04T12:00:00.000000Z",
) -> dict[str, object]:
    review = workspace["reviews"][0]
    return {
        "content": (
            "Owner-reviewed evidence establishes a bounded Micron-specific supply "
            "persistence claim for this paper episode."
        ),
        "locator": "operator://2026-08-04/mu/supply-persistence-1",
        "observed_at": observed_at,
        "pit_identity": _pit_identity(),
        "market_instrument_id": review["instrument_id"],
        "market_price": price,
        "market_observed_at": market_observed_at,
        "market_source_identity": "operator://2026-08-04/mu/market-observation-1",
        "review_updates": [
            {
                "instrument_id": review["instrument_id"],
                "outcome": "ADMIT",
                "net_score_bps": 500,
                "target_quantity": quantity,
                "principal_claim": (
                    "The admitted evidence supports one bounded paper position in MU."
                ),
            }
        ],
        "operator_rationale": (
            "Fund the explicit paper target from AVAILABLE certified cash at the "
            "identified owner-supplied market observation."
        ),
    }


def _available_cash(workspace_or_transition: dict[str, object], key: str) -> str:
    rows = workspace_or_transition[key]
    return next(row["amount"] for row in rows if row["bucket"] == "AVAILABLE")


def _app_blob(app: object) -> str:
    parts: list[str] = []
    for collection_name in (
        "header",
        "subheader",
        "caption",
        "info",
        "warning",
        "success",
        "error",
        "table",
    ):
        for element in getattr(app, collection_name):
            parts.append(str(getattr(element, "value", element)))
    return "\n".join(parts)


def _element_by_key(collection: object, key: str) -> object:
    return next(
        element for element in collection if getattr(element, "key", None) == key
    )


def test_forward_profile_is_distinct_from_banked_real_mu_specimen(tmp_path: Path) -> None:
    historical = get_scenario(REAL_MU_PROSPECTIVE_SCENARIO_ID)
    forward = get_scenario(OPERATED_PAPER_CAPITAL_SCENARIO_ID)

    assert historical["portfolio_aim"]["allowed_actions"] == ["HOLD", "CASH"]
    assert historical.get("forward_operated_market_packet") is None
    assert forward["portfolio_aim"]["allowed_actions"] == ["BUY", "HOLD", "CASH"]
    assert forward["forward_operated_market_packet"] is True
    assert forward["source_scenario_id"] == REAL_MU_PROSPECTIVE_SCENARIO_ID

    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    assert workspace["book"]["positions"] == []
    assert workspace["book"]["total_cash"] == "11000"
    assert workspace["book"]["unexplained_residual"] == "0"
    assert workspace["pit_identity"] == _pit_identity()


def test_persisted_workspace_requires_canonical_json_bytes(tmp_path: Path) -> None:
    ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    path = workspace_path(tmp_path, scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID)
    original = path.read_bytes()
    path.write_bytes(original.replace(b"\n", b" \n", 1))
    try:
        with pytest.raises(OperatedPortfolioError, match="WORKSPACE_CANONICAL_INVALID"):
            load_prospective_workspace(
                root=tmp_path,
                scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
            )
    finally:
        path.write_bytes(original)

    envelope = parse_canonical_document_bytes(original)
    envelope["workspace"]["scenario_id"] = "GV_PROSPECTIVE_PAPER_BASELINE_1"
    envelope["workspace_hash"] = domain_hash(
        "GV-OPERATED-PORTFOLIO:WORKSPACE:V3", envelope["workspace"]
    )
    path.write_bytes(canonical_document_bytes(envelope))
    try:
        with pytest.raises(
            OperatedPortfolioError,
            match="PERSISTED_WORKSPACE_SCENARIO_ID_MISMATCH",
        ):
            load_prospective_workspace(
                root=tmp_path,
                scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
            )
    finally:
        path.write_bytes(original)


def test_forward_pit_identity_is_source_bound_and_fails_closed(tmp_path: Path) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    request = _request(workspace)
    forged = deepcopy(request)
    forged_identity = forged["pit_identity"]
    forged_identity["certified_book_id"] = "0" * 64
    forged_identity["evidence_set_id"] = "0" * 64
    forged_identity["market_snapshot_id"]["certified_book_id"] = "0" * 64
    forged_identity["market_snapshot_id"]["certified_book_hash"] = "0" * 64
    forged_identity["market_snapshot_id"]["validation_digest"] = "0" * 64

    with pytest.raises(
        ProspectiveOperationError,
        match="FORWARD_OPERATED_PIT_IDENTITY_(?:WORKSPACE_)?MISMATCH",
    ):
        preview_runtime_observation(workspace, forged)


def test_cash_funded_buy_preview_is_mutation_free_and_fully_reconciled(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    path = workspace_path(
        tmp_path, scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID
    )
    persisted_before = path.read_bytes()
    memory_before = canonical_document_bytes(workspace)

    proposal = preview_runtime_observation(workspace, _request(workspace))

    assert path.read_bytes() == persisted_before
    assert canonical_document_bytes(workspace) == memory_before
    assert proposal["economics_changed"] is True
    assert proposal["changed_why"]["change_type"] == (
        "PROSPECTIVE_CASH_FUNDED_ENTRY"
    )
    assert proposal["transition"]["transition_kind"] == (
        "PROSPECTIVE_CASH_FUNDED_ENTRY"
    )
    assert proposal["transition"]["order_count"] == 1
    assert proposal["transition"]["legs"] == [
        {
            "instrument_id": workspace["reviews"][0]["instrument_id"],
            "side": "BUY",
            "quantity": "10",
            "reference_price": "100",
        }
    ]
    assert _available_cash(proposal["transition"], "classified_cash_after") == "8998"
    assert proposal["transition"]["cash_after"] == "9998"
    assert proposal["transition"]["costs_after"] == "2"
    assert proposal["transition"]["unexplained_residual"] == "0"
    assert proposal["transition"]["positions_after"] == [
        {
            "instrument_id": workspace["reviews"][0]["instrument_id"],
            "quantity": "10",
            "valuation_price": "100",
            "market_value": "1000",
        }
    ]
    packet = proposal["request"]["forward_operated_packet"]
    assert packet["market_price"] == "100"
    assert packet["market_source_identity"].startswith("operator://")
    assert packet["target_quantity"] == "10"
    assert packet["pit_identity"] == _pit_identity()


def test_cash_funded_buy_confirm_persists_certifies_and_reopens_exactly(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    prior_certification = workspace["certification"]["certification_id"]
    proposal = preview_runtime_observation(workspace, _request(workspace))

    confirmed = confirm_prospective_observation_and_persist(
        proposal,
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    assert confirmed["prospective_episode_count"] == 1
    assert confirmed["operator_action_count"] == 2
    assert confirmed["certification"]["certification_id"] != prior_certification
    assert confirmed["certification"]["prior_certification_id"] == prior_certification
    assert len(confirmed["orders"]) == 1
    assert len(confirmed["fills"]) == 1
    assert confirmed["orders"][0]["side"] == "BUY"
    assert confirmed["orders"][0]["reference_price"] == "100"
    assert confirmed["fills"][0]["price"] == "100"
    assert confirmed["book"]["positions"][0]["quantity"] == "10"
    assert _available_cash(confirmed["book"], "classified_cash") == "8998"
    assert confirmed["book"]["total_costs"] == "2"
    assert confirmed["book"]["unexplained_residual"] == "0"
    assert confirmed["book"]["book_hash"] == proposal["transition"][
        "book_hash_after"
    ]

    reopened = load_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    reconstructed = reconstruct_prospective_workspace(
        reopened["events"],
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
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
    assert receipt["positions"][0]["quantity"] == "10"
    assert next(
        row["amount"]
        for row in receipt["classified_cash"]
        if row["bucket"] == "AVAILABLE"
    ) == "8998"
    assert receipt["costs"][0]["amount"] == "2"
    assert receipt["residual"] == "0"


def test_rejection_certifies_without_changing_economic_authority(tmp_path: Path) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    proposal = preview_runtime_observation(workspace, _request(workspace))

    rejected = reject_prospective_observation_and_persist(
        proposal,
        "The evidence is identified but not strong enough for capital authority.",
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    assert rejected["prospective_episode_history"][-1]["disposition"] == "REJECTED"
    assert canonical_document_bytes(rejected["book"]) == canonical_document_bytes(
        workspace["book"]
    )
    assert rejected["orders"] == []
    assert rejected["fills"] == []
    assert rejected["book"]["positions"] == []
    assert rejected["certification"]["certification_id"] != workspace[
        "certification"
    ]["certification_id"]


def test_cash_funded_entry_fails_closed_on_cash_market_or_stale_drift(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    with pytest.raises(Exception, match="INSUFFICIENT_CLASSIFIED_CASH"):
        preview_runtime_observation(
            workspace,
            _request(workspace, quantity="1000", price="100"),
        )

    with pytest.raises(
        ProspectiveOperationError,
        match="MARKET_PRICE_OUT_OF_BOUNDS",
    ):
        preview_runtime_observation(
            workspace,
            _request(workspace, price="1e5000"),
        )

    wrong_instrument = _request(workspace)
    wrong_instrument["market_instrument_id"] = "SEC_CIK:WRONG"
    with pytest.raises(
        ProspectiveOperationError,
        match="FORWARD_OPERATED_MARKET_INSTRUMENT_MISMATCH",
    ):
        preview_runtime_observation(workspace, wrong_instrument)

    after_evidence = _request(
        workspace,
        observed_at="2026-08-04T12:00:00.000000Z",
        market_observed_at="2026-08-04T12:01:00.000000Z",
    )
    with pytest.raises(
        ProspectiveOperationError,
        match="MARKET_OBSERVATION_AFTER_EVIDENCE_DECISION",
    ):
        preview_runtime_observation(workspace, after_evidence)

    proposal = preview_runtime_observation(workspace, _request(workspace))
    tampered = deepcopy(proposal)
    tampered["request"]["forward_operated_packet"]["market_price"] = "101"
    with pytest.raises(ProspectiveOperationError, match="STALE_OR_MUTATED_PROPOSAL"):
        confirm_prospective_observation_and_persist(
            tampered,
            root=tmp_path,
            scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
        )

    binding_tampered = deepcopy(proposal)
    binding_tampered["request"]["forward_operated_packet"]["principal_claim"] = (
        "A different claim that is not bound to the reviewed update."
    )
    with pytest.raises(
        ProspectiveOperationError,
        match="FORWARD_OPERATED_PACKET_BINDING_MISMATCH",
    ):
        confirm_prospective_observation_and_persist(
            binding_tampered,
            root=tmp_path,
            scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
        )


def test_forward_request_and_replay_bounds_fail_closed(tmp_path: Path) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )

    oversized = _request(workspace)
    oversized["content"] = "x" * 4097
    with pytest.raises(ProspectiveOperationError, match="CONTENT_TOO_LONG"):
        preview_runtime_observation(workspace, oversized)

    too_many_updates = _request(workspace)
    too_many_updates["review_updates"] = [
        too_many_updates["review_updates"][0]
    ] * 65
    with pytest.raises(ProspectiveOperationError, match="REVIEW_UPDATES_TOO_MANY"):
        preview_runtime_observation(workspace, too_many_updates)

    too_many_quantity_digits = _request(workspace, quantity="1" * 19)
    with pytest.raises(
        ProspectiveOperationError, match="TARGET_QUANTITY_OUT_OF_BOUNDS"
    ):
        preview_runtime_observation(workspace, too_many_quantity_digits)

    with pytest.raises(
        ProspectiveOperationError,
        match="PROSPECTIVE_EVENT_LIMIT_EXCEEDED",
    ):
        reconstruct_prospective_workspace([{}] * (MAX_PROSPECTIVE_EVENT_COUNT + 1))
    with pytest.raises(
        ProspectiveOperationError, match="PROSPECTIVE_EVENT_MAPPING_REQUIRED"
    ):
        reconstruct_prospective_workspace([object()])  # type: ignore[list-item]


def test_market_price_and_book_replay_are_context_independent(tmp_path: Path) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    request = _request(workspace, quantity="7", price="101.25")
    with localcontext() as context:
        context.prec = 2
        context.Emin = -2
        context.Emax = 2
        for signal in context.traps:
            context.traps[signal] = True
        low_precision = _positive_decimal_text("101.25", field="market_price")
        low_precision_canonical = canonical_decimal("101.25")
        low_precision_proposal = preview_runtime_observation(workspace, request)
    with localcontext() as context:
        context.prec = 28
        normal_precision = _positive_decimal_text("101.25", field="market_price")
        normal_precision_proposal = preview_runtime_observation(workspace, request)
    assert low_precision == normal_precision == low_precision_canonical == "101.25"
    assert canonical_document_bytes(low_precision_proposal) == canonical_document_bytes(
        normal_precision_proposal
    )


def test_command_center_operates_and_reopens_the_changed_certified_book(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    def _denied(*_args: object, **_kwargs: object) -> None:
        raise OSError("GV_COMMAND_CENTER_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setenv("GV_OPERATED_PORTFOLIO_HOME", str(tmp_path / "workspace"))
    monkeypatch.chdir(ROOT)

    app = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
    assert not app.exception, app.exception
    initial = _app_blob(app)
    assert "Active certified paper workspace" in initial
    assert "CASH_ONLY" in initial
    assert "Banked no-market comparison baseline" in initial

    _element_by_key(
        app.text_area, "gv_command_center_evidence_content"
    ).set_value(
        "Owner-reviewed evidence establishes a bounded Micron-specific supply persistence claim."
    )
    _element_by_key(
        app.text_input, "gv_command_center_source_locator"
    ).set_value("operator://2026-08-04/mu/supply-persistence-1")
    _element_by_key(
        app.text_input, "gv_command_center_evidence_observed_at"
    ).set_value("2026-08-04T12:01:00.000000Z")
    _element_by_key(app.text_input, "gv_command_center_market_price").set_value(
        "100"
    )
    _element_by_key(
        app.text_input, "gv_command_center_market_observed_at"
    ).set_value("2026-08-04T12:00:00.000000Z")
    _element_by_key(
        app.text_input, "gv_command_center_market_source_identity"
    ).set_value("operator://2026-08-04/mu/market-observation-1")
    _element_by_key(
        app.number_input, "gv_command_center_target_quantity"
    ).set_value(10)
    _element_by_key(
        app.number_input, "gv_command_center_net_score_bps"
    ).set_value(500)
    _element_by_key(
        app.text_area, "gv_command_center_principal_claim"
    ).set_value("The admitted evidence supports one bounded paper position in MU.")
    _element_by_key(
        app.text_area, "gv_command_center_operator_rationale"
    ).set_value(
        "Fund the explicit target from AVAILABLE certified cash at the identified market observation."
    )
    _element_by_key(app.button, "gv_command_center_preview").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    preview = _app_blob(app)
    assert "Mutation-free paper-capital preview" in preview
    preview_tables = [element.value for element in app.table]
    preview_summary = next(
        table for table in preview_tables if "transition_kind" in table.columns
    )
    assert preview_summary.loc[0, "transition_kind"] == (
        "PROSPECTIVE_CASH_FUNDED_ENTRY"
    )
    assert bool(preview_summary.loc[0, "authoritative"]) is False
    assert any(
        "bucket" in table.columns
        and "8998" in set(table["amount"].astype(str))
        for table in preview_tables
    )
    assert "residual=0" in preview

    _element_by_key(app.button, "gv_command_center_confirm").click()
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    confirmed = _app_blob(app)
    assert "bounded cash-funded entry has been operated" in confirmed
    assert "Certified paper fills" in confirmed
    assert "BUY" in confirmed
    assert "8998" in confirmed
    confirmed_tables = [element.value for element in app.table]
    authority = next(
        table
        for table in confirmed_tables
        if "certification_lineage_depth" in table.columns
    )
    assert int(authority.loc[0, "certification_lineage_depth"]) == 1
    assert int(authority.loc[0, "prospective_episode_count"]) == 1

    fresh = AppTest.from_file(str(ROOT / "dashboard.py")).run(timeout=120)
    assert not fresh.exception, fresh.exception
    reopened = _app_blob(fresh)
    assert "bounded cash-funded entry has been operated" in reopened
    assert "Certified paper fills" in reopened
    assert "BUY" in reopened
    assert "8998" in reopened
    assert "CASH_ONLY" not in reopened


def test_forward_profile_does_not_weaken_rebalance_rules_after_entry(
    tmp_path: Path,
) -> None:
    workspace = ensure_prospective_workspace(
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    confirmed = confirm_prospective_observation_and_persist(
        preview_runtime_observation(workspace, _request(workspace)),
        root=tmp_path,
        scenario_id=OPERATED_PAPER_CAPITAL_SCENARIO_ID,
    )
    later = _request(
        confirmed,
        quantity="11",
        observed_at="2026-08-04T13:01:00.000000Z",
        market_observed_at="2026-08-04T13:00:00.000000Z",
    )

    with pytest.raises(
        ProspectiveOperationError,
        match="PROSPECTIVE_TRANSITION_SELL_REQUIRED",
    ):
        preview_runtime_observation(confirmed, later)
