"""Fail-closed tests for TR-v0 L2 observation contract."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.transition_recognition_v0.l2_observation_contract import (
    L2_CONTRACT_PATH,
    L2_RECEIPT_PATH,
    assert_l2_contract_invariants,
    load_l2_contract,
)

ROOT = Path(__file__).resolve().parents[2]


def test_l2_contract_file_exists() -> None:
    assert L2_CONTRACT_PATH.is_file()
    assert L2_RECEIPT_PATH.is_file()


def test_l2_invariants() -> None:
    assert_l2_contract_invariants()


def test_receipt_matches_terminal() -> None:
    receipt = json.loads(L2_RECEIPT_PATH.read_text(encoding="utf-8"))
    contract = load_l2_contract()
    assert receipt["terminal_verdict"] == "L2_OBSERVATION_CONTRACT_FROZEN"
    assert receipt["recognition_bind"]["source_bytes_status"] == "MISSING_SOURCE"
    assert receipt["gates_honored"]["debit"] == 0
    assert receipt["gates_honored"]["timing_research"] is False
    assert receipt["gates_honored"]["ftk_rescue"] is False
    assert contract["status"] == receipt["status"]


def test_no_outcomes_or_wager_law_in_l2() -> None:
    contract = load_l2_contract()
    blob = json.dumps(contract)
    assert "CRV1_RIGHT_TAIL_252D" not in blob
    assert contract["family_data_contract"]["primary_label_spec_id"] == "UNSET_THIS_SLICE_NO_OUTCOMES"
    assert contract["family_data_contract"]["outcomes_api"] == "FORBIDDEN_THIS_SLICE"


def test_stop_close_still_ftk_stopped() -> None:
    stop = json.loads(
        (ROOT / "docs/context/e2e_evidence/ao_ftk_1_l7_stop_close.json").read_text(encoding="utf-8")
    )
    assert stop["L7_ROUTE"] == "STOP"
    assert stop["ftk_econ_primary"] == "STOPPED"
