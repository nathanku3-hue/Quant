"""AO-FTK-1 L5 sensing-first one-shot — fail-closed + post-run custody tests."""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from research.asymmetric_opportunity_v1 import ao_ftk_1_l4_contract as l4
from research.asymmetric_opportunity_v1 import ao_ftk_1_l5_contract as l5
from research.econphysics_prebreakout_v1.contracts import (
    build_structured_snapshots,
    deterministic_xs_holdout,
)


REPO = Path(__file__).resolve().parents[2]
RECEIPT = "e" * 64
PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")
QUARTERS = (
    date(2023, 3, 31),
    date(2023, 6, 30),
    date(2023, 9, 30),
    date(2023, 12, 31),
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
)


def _development_securities(count: int) -> list[str]:
    output: list[str] = []
    number = 1000
    while len(output) < count:
        candidate = f"CIQSEC:IQ{number}"
        if not deterministic_xs_holdout(candidate):
            output.append(candidate)
        number += 1
    return output


def _rows_for_security(*, security_id: str, entity: str, phase: int) -> list[dict[str, object]]:
    revenue = [100.0 if (index + phase) % 2 == 0 else 120.0 for index in range(len(QUARTERS))]
    inventory_ratio = [0.30 if (index + phase) % 2 == 0 else 0.20 for index in range(len(QUARTERS))]
    operating_margin = [0.10 if (index + phase) % 2 == 0 else 0.20 for index in range(len(QUARTERS))]
    output: list[dict[str, object]] = []
    for fq0_index in range(4, 9):
        as_of = QUARTERS[fq0_index] + timedelta(days=45)
        for relative_index, relative_period in enumerate(PERIODS):
            source_index = fq0_index - relative_index
            rev = revenue[source_index]
            output.append(
                {
                    "security_id": security_id,
                    "source_entity_id": entity,
                    "as_of_date": as_of.isoformat(),
                    "available_at": as_of.isoformat() + "T23:59:59.999999Z",
                    "relative_period": relative_period,
                    "period_end": QUARTERS[source_index].isoformat(),
                    "IQ_TOTAL_REV": rev,
                    "IQ_INVENTORY": inventory_ratio[source_index] * rev,
                    "IQ_OPER_INC": operating_margin[source_index] * rev,
                    "IQ_CAPEX_BNK": 10.0 + source_index,
                    "filing_version": "Original",
                    "value_unit": "USD_THOUSANDS",
                    "source_receipt_sha256": RECEIPT,
                }
            )
    return output


def test_auth_required_for_join_debit_run() -> None:
    with pytest.raises(l5.L5FailClosedError, match="l5_authorized=false"):
        l5.trial_debit(l5_authorized=False)
    with pytest.raises(l5.L5FailClosedError, match="l5_authorized=false"):
        l5.label_join(l5_authorized=False, join_authorized=True)
    with pytest.raises(l5.L5FailClosedError, match="l5_authorized=false"):
        l5.evaluator_run(l5_authorized=False, runnable_evaluation=True)


def test_exactly_one_debit_enforced() -> None:
    with pytest.raises(l5.L5FailClosedError, match="debit_units_must_be_1"):
        l5.trial_debit(l5_authorized=True, debit_units=2)
    receipt = l5.trial_debit(l5_authorized=True, debit_units=1)
    l5.assert_debit_exactly_one(receipt)
    assert receipt["charged_after"] == 1
    assert receipt["remaining_after"] == 2
    with pytest.raises(l5.L5FailClosedError, match="already_debited"):
        l5.trial_debit(l5_authorized=True, debit_units=1, already_debited=True)


def test_exactly_one_join_enforced() -> None:
    l5.label_join(l5_authorized=True, join_authorized=True, already_joined=False)
    with pytest.raises(l5.L5FailClosedError, match="second_join"):
        l5.label_join(l5_authorized=True, join_authorized=True, already_joined=True)
    with pytest.raises(l5.L5FailClosedError, match="join_authorized=false"):
        l5.label_join(l5_authorized=True, join_authorized=False)


def test_second_run_fails_closed() -> None:
    run_id = "TEST_L5_SECOND_RUN_GUARD"
    # Clear any prior test pollution for this id.
    l5._SPENT_RUN_IDS.discard(run_id)
    l5.evaluator_run(
        l5_authorized=True, runnable_evaluation=True, run_id=run_id, already_run=False
    )
    l5.mark_eval_spent(run_id)
    with pytest.raises(l5.L5FailClosedError, match="second_evaluation"):
        l5.evaluator_run(
            l5_authorized=True, runnable_evaluation=True, run_id=run_id, already_run=False
        )
    with pytest.raises(l5.L5FailClosedError, match="second_evaluation"):
        l5.mark_eval_spent(run_id)
    l5._SPENT_RUN_IDS.discard(run_id)


def test_dof_remains_two_on_l4_freeze() -> None:
    freeze = l4.load_machine_freeze(REPO)
    assert freeze["effective_decision_dof"] == 2
    assert freeze["max_effective_decision_dof"] == 2
    assert freeze["silent_one_dof_collapse"] == "FORBIDDEN"
    assert freeze["third_decision_dof"] == "FORBIDDEN"
    assert {op["operator_id"] for op in freeze["operators"]} == {
        "INV_DELTA_MEAN_REVERSION",
        "MARGIN_M1_STATE_MEAN_REVERSION",
    }


def test_economic_cuts_still_blocked_unset() -> None:
    freeze = l4.load_machine_freeze(REPO)
    assert freeze["payoff_horizon"] == "BLOCKED_UNSET"
    assert freeze["right_tail_cut"] == "BLOCKED_UNSET"
    assert freeze["catastrophe_cut"] == "BLOCKED_UNSET"
    run_path = REPO / l5.RUN_REL
    if run_path.is_file():
        run = json.loads(run_path.read_text(encoding="utf-8"))
        assert run["payoff_horizon"] == "BLOCKED_UNSET"
        assert run["right_tail_cut"] == "BLOCKED_UNSET"
        assert run["catastrophe_cut"] == "BLOCKED_UNSET"
        assert run["financial_alpha_evidence"] == 0


def test_qm_terms_absent_and_alpha_zero() -> None:
    freeze = l4.load_machine_freeze(REPO)
    l4.assert_no_qm_terms_in_l4_surface(freeze)
    assert freeze["financial_alpha_evidence"] == 0
    for rel in (l5.AUTH_REL, l5.DEBIT_REL, l5.RUN_REL, l5.L6_REL, l5.L7_REL):
        path = REPO / rel
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc.get("financial_alpha_evidence", 0) == 0
        blob = json.dumps(doc)
        assert "Rule100" not in blob
        assert "Q_GF" not in blob


def test_frozen_sensing_eval_toy_corpus_no_grid() -> None:
    rows: list[dict[str, object]] = []
    for index, security_id in enumerate(_development_securities(3)):
        rows.extend(
            _rows_for_security(
                security_id=security_id,
                entity=str(7000 + index),
                phase=index % 2,
            )
        )
    report = l5.evaluate_frozen_sensing(
        build_structured_snapshots(rows),
        minimum_fold_n=1,
        minimum_fold_coverage=0.10,
    )
    assert report["evaluation_count"] == 1
    assert report["effective_decision_dof"] == 2
    assert report["threshold_grid_performed"] is False
    assert report["operator_fit_performed"] is False
    assert report["dof_rewrite_performed"] is False
    assert report["feature_add_performed"] is False
    assert report["qm_terms_present"] is False
    assert report["financial_alpha_evidence"] == 0
    assert set(report["operators_frozen"]) == {
        "INV_DELTA_MEAN_REVERSION",
        "MARGIN_M1_STATE_MEAN_REVERSION",
    }
    assert l5.INVENTORY_TARGET_ID in report["targets"]
    assert l5.MARGIN_TARGET_ID in report["targets"]
    # Only two sensing targets — demand is not a DOF this turn.
    assert "NEXT_PIT_REVENUE_DIRECTION" not in report["targets"]


def test_post_run_receipts_if_present() -> None:
    """When the real L5 one-shot has landed, assert custody invariants."""
    auth_path = REPO / l5.AUTH_REL
    if not auth_path.is_file():
        pytest.skip("L5 one-shot receipts not yet landed")

    auth = json.loads(auth_path.read_text(encoding="utf-8"))
    debit = json.loads((REPO / l5.DEBIT_REL).read_text(encoding="utf-8"))
    join = json.loads((REPO / l5.JOIN_REL).read_text(encoding="utf-8"))
    run = json.loads((REPO / l5.RUN_REL).read_text(encoding="utf-8"))
    l6 = json.loads((REPO / l5.L6_REL).read_text(encoding="utf-8"))
    l7 = json.loads((REPO / l5.L7_REL).read_text(encoding="utf-8"))

    assert auth["owner_decision"] == "L5_AUTHORIZE"
    assert auth["mode"] == "SENSING_FIRST"
    assert auth["debit_allowed"] == 1
    assert auth["joins_allowed"] == 1
    assert auth["evals_allowed"] == 1
    assert auth["financial_alpha_evidence"] == 0
    assert auth["payoff_horizon"] == "BLOCKED_UNSET"

    assert debit["debit"] == 1
    assert debit["charged_after"] == 1
    assert debit["remaining_after"] == 2

    assert join["join_count"] == 1
    assert join["LABEL_BYTES_JOINED"] is True
    assert join["product_clock_join"] is False
    assert join["w6_join"] is False

    assert run["evaluation_count"] == 1
    assert run["effective_decision_dof"] == 2
    assert run["financial_alpha_evidence"] == 0
    assert run["evaluation"]["threshold_grid_performed"] is False

    assert "layers" in l6
    assert l6["financial_alpha_evidence"] == 0
    assert l6["falsifiers"]["F6_ASYMMETRY_CATASTROPHE"] == "NOT_IN_SCOPE_SENSING_FIRST"

    assert l7["l7_status"] == "WAITING_OWNER"
    assert l7["worker_did_not_select_next_slice"] is True
    assert l7["l5_auth_spent"] is True
    assert l7["material_trials_remaining"] == 2
    assert l7["financial_alpha_evidence"] == 0

    # L4 freeze document must remain historically unjoined / uncharged.
    freeze = l4.load_machine_freeze(REPO)
    assert freeze["l5_authorized"] is False
    assert freeze["material_trial_debit"]["current_charged"] == 0
    assert freeze["label_pack"]["LABEL_BYTES_JOINED"] is False

    sot = json.loads(
        (REPO / "docs/context/research_loop_state_current.json").read_text(encoding="utf-8")
    )
    assert sot["process"]["loop_phase"] == "L7_ROADMAP_DECISION"
    assert sot["product"]["financial_alpha_evidence"] == 0
    track = next(t for t in sot["active_tracks"] if t["track_id"] == "AO-FTK-1")
    assert track["material_trials_charged_this_slice"] == 1
    assert track["material_trials_remaining"] == 2
    assert track["label_bytes_joined"] is True
    assert track["l5_auth_spent"] is True
