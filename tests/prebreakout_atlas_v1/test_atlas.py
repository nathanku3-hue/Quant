from __future__ import annotations

import copy
from pathlib import Path
import runpy

import pandas as pd
import pytest

from research.prebreakout_atlas_v1 import (
    AtlasError,
    EXCLUDED_WINNER,
    FALSE_WINNER,
    MATCHED_CONTROL,
    MISSED_WINNER,
    TRUE_WINNER,
    MatchedControlContract,
    PrebreakoutMethodologyBinding,
    assert_upstream_contract_alignment,
    build_discovery_atlas,
    upstream_contract_status,
    verify_discovery_atlas,
)
from research.prebreakout_pit_v1 import authority as w3


_REPO_ROOT = Path(__file__).resolve().parents[2]
_W2 = runpy.run_path(str(_REPO_ROOT / "research" / "prebreakout_discovery_v1" / "preregistration.py"))
_W2_SNAPSHOT = _W2["contract_snapshot"]()
_W2_CONTRACT_SHA256 = str(_W2["CONTRACT_SHA256"])
METHODOLOGY = PrebreakoutMethodologyBinding.from_preregistration_snapshot(
    _W2_SNAPSHOT,
    methodology_contract_sha256=_W2_CONTRACT_SHA256,
    breakout_contract_sha256=_W2_CONTRACT_SHA256,
)

B = "2026-01-07"
B1 = "2026-01-06"
D0 = "2026-01-05"
B_ORDINAL = 102
B1_ORDINAL = 101
D0_ORDINAL = 100
PIT_HASH = "a" * 64


def _match_contract(*, charged: bool = False) -> MatchedControlContract:
    return MatchedControlContract(
        methodology_contract_sha256=METHODOLOGY.methodology_contract_sha256,
        control_definition_id="FIXTURE_EXACT_SECTOR_SIZE_V1",
        match_columns=("sector", "size_bucket"),
        search_charge_receipt_sha256=("b" * 64) if charged else None,
        trial_ledger_snapshot_sha256=("d" * 64) if charged else None,
    )


def _row(
    *,
    day: str,
    ordinal: int,
    security_num: int,
    episode_id: str,
    winner: bool,
    flagged: bool,
    eligible: bool = True,
    exclusion_reason: str = "",
    sector: str = "TECH",
    size_bucket: str = "MID",
) -> dict[str, object]:
    return {
        "decision_session_date": day,
        "decision_session_ordinal": ordinal,
        "decision_listing_session_ordinal": ordinal,
        "security_id": f"CIQSEC:IQ{security_num}",
        "trading_item_id": str(security_num),
        "pit_authority_sha256": PIT_HASH,
        "pit_risk_set_spec_id": METHODOLOGY.risk_set_spec_id,
        "eligibility_status": w3.ELIGIBLE if eligible else "EXCLUDED",
        "exclusion_reason": "" if eligible else exclusion_reason,
        "flagged": flagged,
        "winner_label": winner,
        "outcome_status": "MATURED_OPEN",
        "effective_episode_id": episode_id,
        "breakout_session_date": B if winner else None,
        "breakout_session_ordinal": B_ORDINAL if winner else None,
        "breakout_listing_session_ordinal": B_ORDINAL if winner else None,
        "b_minus_1_session_date": B1 if winner else None,
        "b_minus_1_session_ordinal": B1_ORDINAL if winner else None,
        "b_minus_1_listing_session_ordinal": B1_ORDINAL if winner else None,
        "sector": sector,
        "size_bucket": size_bucket,
    }


def _smoke_proof(case_id: str, symbol: str, security_num: int) -> w3.BMinusOneEligibilityProof:
    return w3.build_b_minus_one_eligibility_proof(
        authority=None,
        case_id=case_id,
        display_symbol=symbol,
        breakout_contract_sha256=METHODOLOGY.breakout_contract_sha256,
        breakout_session=B,
        b_minus_1_session=B1,
        expected_security_id=f"CIQSEC:IQ{security_num}",
        expected_trading_item_id=str(security_num),
    )


def _full_fixture_grid() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=1, episode_id="EP_TRUE", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=1, episode_id="EP_TRUE", winner=True, flagged=True),
    ]
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=2, episode_id="EP_MISSED", winner=True, flagged=False),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=2, episode_id="EP_MISSED", winner=True, flagged=False),
    ]
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=3, episode_id="NW_FALSE", winner=False, flagged=False),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=3, episode_id="NW_FALSE", winner=False, flagged=True),
    ]
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=4, episode_id="EP_MU", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=4, episode_id="EP_MU", winner=True, flagged=True),
    ]
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=5, episode_id="EP_EXCLUDED", winner=True, flagged=False),
        _row(
            day=B1,
            ordinal=B1_ORDINAL,
            security_num=5,
            episode_id="EP_EXCLUDED",
            winner=True,
            flagged=False,
            eligible=False,
            exclusion_reason="NOT_ACTIVE_TRADABLE",
        ),
    ]
    rows += [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=6, episode_id="EP_SNDK", winner=True, flagged=False),
        _row(
            day=B1,
            ordinal=B1_ORDINAL,
            security_num=6,
            episode_id="EP_SNDK",
            winner=True,
            flagged=False,
            eligible=False,
            exclusion_reason="REQUIRED_FEATURE_UNAVAILABLE_AT_CUT",
        ),
    ]
    for security_num in (7, 8):
        rows += [
            _row(
                day=D0,
                ordinal=D0_ORDINAL,
                security_num=security_num,
                episode_id=f"NW_CONTROL_{security_num}",
                winner=False,
                flagged=False,
            ),
            _row(
                day=B1,
                ordinal=B1_ORDINAL,
                security_num=security_num,
                episode_id=f"NW_CONTROL_{security_num}",
                winner=False,
                flagged=False,
            ),
        ]
    rows.append(
        _row(
            day=B1,
            ordinal=B1_ORDINAL,
            security_num=9,
            episode_id="NW_OTHER",
            winner=False,
            flagged=False,
            sector="HEALTH",
            size_bucket="SMALL",
        )
    )
    return pd.DataFrame(rows)


def test_methodology_snapshot_hash_mismatch_fails_closed() -> None:
    poisoned = copy.deepcopy(_W2_SNAPSHOT)
    poisoned["horizons"]["primary_sessions"] = 21
    with pytest.raises(AtlasError, match="methodology_snapshot_hash_mismatch"):
        PrebreakoutMethodologyBinding.from_preregistration_snapshot(
            poisoned,
            methodology_contract_sha256=_W2_CONTRACT_SHA256,
            breakout_contract_sha256=_W2_CONTRACT_SHA256,
        )


def test_binding_consumes_current_w2_preregistration_without_importing_w5_package_init() -> None:
    assert METHODOLOGY.family_id == "PREBREAKOUT_DISCOVERY_v1"
    assert METHODOLOGY.primary_horizon_sessions == 20
    assert METHODOLOGY.lead_lookback_sessions == 20
    assert METHODOLOGY.min_legitimate_lead_sessions == 1
    assert METHODOLOGY.trial_budget_max == 8
    assert METHODOLOGY.methodology_contract_sha256 == _W2_CONTRACT_SHA256
    assert METHODOLOGY.breakout_contract_sha256 == _W2_CONTRACT_SHA256


def test_breakout_binding_cannot_diverge_from_single_w2_scientific_seal() -> None:
    with pytest.raises(AtlasError, match="breakout_contract_must_equal_w2_methodology_contract"):
        PrebreakoutMethodologyBinding.from_preregistration_snapshot(
            _W2_SNAPSHOT,
            methodology_contract_sha256=_W2_CONTRACT_SHA256,
            breakout_contract_sha256="f" * 64,
        )


def test_upstream_w2_w3_risk_set_contract_is_explicit_and_aligned() -> None:
    status = upstream_contract_status(METHODOLOGY)
    assert status["methodology_family_id"] == "PREBREAKOUT_DISCOVERY_v1"
    assert status["w3_family_id"] == "PREBREAKOUT_DISCOVERY_v1"
    assert status["risk_set_spec_aligned"] is True
    assert status["methodology_risk_set_spec_id"] == status["w3_risk_set_spec_id"]
    assert_upstream_contract_alignment(METHODOLOGY)


def test_upstream_risk_set_drift_fails_real_integration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(w3, "RISK_SET_SPEC_ID", "DRIFTED_W3_RISK_SET")
    with pytest.raises(AtlasError, match="w2_w3_risk_set_spec_mismatch"):
        assert_upstream_contract_alignment(METHODOLOGY)


def test_fixture_atlas_builds_full_episode_and_control_census_with_zero_weight_smokes() -> None:
    report = build_discovery_atlas(
        _full_fixture_grid(),
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        smoke_proofs=(
            _smoke_proof("SMOKE_MU", "MU", 4),
            _smoke_proof("SMOKE_SNDK", "SNDK", 6),
        ),
        fixture=True,
    )
    verify_discovery_atlas(report)

    assert report["authority_class"] == "MECHANICAL_FIXTURE_ZERO_EVIDENCE"
    assert report["authority_boundary"]["promotion_metrics"] == "OUT_OF_SCOPE_W6"
    assert report["authority_boundary"]["financial_alpha_evidence"] == 0
    assert report["summary"]["true_winner_count_statistical"] == 1
    assert report["summary"]["missed_winner_count_statistical"] == 1
    assert report["summary"]["false_winner_decision_count_statistical"] == 1
    assert report["summary"]["matched_control_pair_count"] == 6
    assert report["summary"]["smoke_trace_count"] == 2

    winners = {row["effective_episode_id"]: row for row in report["winner_episode_census"]}
    assert winners["EP_TRUE"]["census_class"] == TRUE_WINNER
    assert winners["EP_TRUE"]["first_legitimate_flag_session_date"] == D0
    assert winners["EP_TRUE"]["first_legitimate_flag_session_ordinal"] == D0_ORDINAL
    assert winners["EP_TRUE"]["matched_control_count"] == 2

    assert winners["EP_MISSED"]["census_class"] == MISSED_WINNER
    assert winners["EP_MISSED"]["first_legitimate_flag_session_date"] is None
    assert winners["EP_MISSED"]["matched_control_count"] == 2

    assert winners["EP_EXCLUDED"]["census_class"] == EXCLUDED_WINNER
    assert winners["EP_EXCLUDED"]["statistical_weight"] == 0
    assert winners["EP_EXCLUDED"]["b_minus_1_exclusion_reason"] == "NOT_ACTIVE_TRADABLE"

    assert winners["EP_MU"]["census_class"] == TRUE_WINNER
    assert winners["EP_MU"]["statistical_weight"] == 0
    assert winners["EP_MU"]["matched_control_count"] == 0
    assert winners["EP_SNDK"]["census_class"] == EXCLUDED_WINNER
    assert winners["EP_SNDK"]["statistical_weight"] == 0

    false_rows = report["false_winner_census"]
    assert len(false_rows) == 1
    assert false_rows[0]["census_class"] == FALSE_WINNER
    assert false_rows[0]["matched_control_count"] == 2

    matched = report["matched_controls"]
    assert len(matched) == 3
    assert report["summary"]["matched_control_group_count"] == 3
    assert sum(int(row["matched_control_count"]) for row in matched) == 6
    assert {row["census_class"] for row in matched} == {MATCHED_CONTROL}
    assert {int(row["matched_control_count"]) for row in matched} == {2}
    assert all(len(row["matched_control_identity_set_sha256"]) == 64 for row in matched)
    assert all(row["statistical_weight"] == 1 for row in matched)

    traces = {row["case_id"]: row for row in report["smoke_traces"]}
    assert traces["SMOKE_MU"]["display_symbol"] == "MU"
    assert traces["SMOKE_MU"]["any_legitimate_prebreakout_flag"] is True
    assert traces["SMOKE_SNDK"]["display_symbol"] == "SNDK"
    assert all(row["display_symbol_used_for_logic"] is False for row in traces.values())
    assert all(row["statistical_weight"] == 0 for row in traces.values())
    assert all(row["promotion_denominator_weight"] == 0 for row in traces.values())


def test_smoke_trace_uses_pit_eligible_breakout_episode_not_winner_label() -> None:
    grid = _full_fixture_grid()
    smoke_rows = pd.DataFrame(
        [
            _row(
                day=D0,
                ordinal=D0_ORDINAL,
                security_num=12,
                episode_id="NW_SMOKE_BREAKOUT",
                winner=False,
                flagged=True,
            ),
            _row(
                day=B1,
                ordinal=B1_ORDINAL,
                security_num=12,
                episode_id="NW_SMOKE_BREAKOUT",
                winner=False,
                flagged=False,
            ),
        ]
    )
    combined = pd.DataFrame(grid.to_dict("records") + smoke_rows.to_dict("records"))
    report = build_discovery_atlas(
        combined,
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        smoke_proofs=(_smoke_proof("SMOKE_NONWINNER_BREAKOUT", "TRACE_ONLY", 12),),
        fixture=True,
    )

    trace = report["smoke_traces"][0]
    assert trace["any_legitimate_prebreakout_flag"] is True
    assert trace["statistical_weight"] == 0
    assert trace["promotion_denominator_weight"] == 0


def test_incomplete_horizon_rows_are_custodied_but_not_imputed_as_nonwinners() -> None:
    grid = _full_fixture_grid()
    mask = grid["security_id"].eq("CIQSEC:IQ7") & grid["decision_session_date"].eq(B1)
    assert mask.sum() == 1
    grid["winner_label"] = grid["winner_label"].astype(object)
    grid.loc[mask, "winner_label"] = None
    grid.loc[mask, "outcome_status"] = "INCOMPLETE_HORIZON"
    report = build_discovery_atlas(
        grid,
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        fixture=True,
    )
    assert report["summary"]["incomplete_outcome_row_count"] == 1
    incomplete = report["incomplete_outcome_census"]
    assert len(incomplete) == 1
    assert incomplete[0]["security_id"] == "CIQSEC:IQ7"
    assert incomplete[0]["census_class"] == "INCOMPLETE_OUTCOME"
    assert sum(
        int(row["ordinary_control_count"])
        for row in report["ordinary_control_pool"]
    ) == report["summary"]["ordinary_control_pool_row_count_statistical"]
    assert all(
        not (row["security_id"] == "CIQSEC:IQ7" and row["decision_session_date"] == B1)
        for row in report["false_winner_census"]
    )


def test_prehistory_flags_extend_early_winner_lead_without_entering_false_winner_census() -> None:
    prehistory = pd.DataFrame(
        [
            {
                "decision_session_date": "2026-01-02",
                "decision_session_ordinal": 99,
                "decision_listing_session_ordinal": 99,
                "security_id": "CIQSEC:IQ2",
                "trading_item_id": "2",
                "pit_authority_sha256": PIT_HASH,
                "pit_risk_set_spec_id": METHODOLOGY.risk_set_spec_id,
                "eligibility_status": w3.ELIGIBLE,
                "exclusion_reason": "",
                "flagged": True,
            }
        ]
    )
    report = build_discovery_atlas(
        _full_fixture_grid(),
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        prehistory_flags=prehistory,
        fixture=True,
    )
    winners = {row["effective_episode_id"]: row for row in report["winner_episode_census"]}
    assert winners["EP_MISSED"]["census_class"] == TRUE_WINNER
    assert winners["EP_MISSED"]["first_legitimate_flag_session_date"] == "2026-01-02"
    assert report["summary"]["prehistory_flag_row_count"] == 1
    assert report["summary"]["false_winner_decision_count_statistical"] == 1


def test_winner_census_counts_one_effective_episode_not_repeated_daily_rows() -> None:
    grid = _full_fixture_grid()
    extra = _row(
        day="2026-01-02",
        ordinal=99,
        security_num=1,
        episode_id="EP_TRUE",
        winner=True,
        flagged=False,
    )
    grid = pd.concat([pd.DataFrame([extra]), grid], ignore_index=True)
    report = build_discovery_atlas(
        grid,
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        fixture=True,
    )
    assert sum(row["effective_episode_id"] == "EP_TRUE" for row in report["winner_episode_census"]) == 1


def test_post_b_minus_one_flag_does_not_rescue_a_missed_winner_or_smoke_trace() -> None:
    rows = [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=10, episode_id="EP_LATE", winner=True, flagged=False),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=10, episode_id="EP_LATE", winner=True, flagged=False),
        _row(day=B, ordinal=B_ORDINAL, security_num=10, episode_id="EP_LATE", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=11, episode_id="CTRL", winner=False, flagged=False),
    ]
    report = build_discovery_atlas(
        pd.DataFrame(rows),
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        smoke_proofs=(_smoke_proof("SMOKE_LATE", "TRACE_ONLY", 10),),
        fixture=True,
    )
    winner = report["winner_episode_census"][0]
    assert winner["census_class"] == MISSED_WINNER
    assert winner["first_legitimate_flag_session_date"] is None
    assert report["smoke_traces"][0]["any_legitimate_prebreakout_flag"] is False


def test_winner_episode_uses_exact_listing_ordinals_when_global_session_spine_has_gap() -> None:
    rows = [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=20, episode_id="EP_GAP", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=20, episode_id="EP_GAP", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=21, episode_id="CTRL_GAP", winner=False, flagged=False),
    ]
    for row in rows[:2]:
        row["breakout_session_date"] = "2026-01-09"
        row["breakout_session_ordinal"] = 104
        row["breakout_listing_session_ordinal"] = 52
        row["b_minus_1_session_date"] = B1
        row["b_minus_1_session_ordinal"] = B1_ORDINAL
        row["b_minus_1_listing_session_ordinal"] = 51
    rows[0]["decision_listing_session_ordinal"] = 50
    rows[1]["decision_listing_session_ordinal"] = 51

    report = build_discovery_atlas(
        pd.DataFrame(rows),
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        fixture=True,
    )
    winner = report["winner_episode_census"][0]
    assert winner["census_class"] == TRUE_WINNER
    assert winner["b_minus_1_session_ordinal"] == B1_ORDINAL
    assert winner["first_legitimate_flag_session_date"] == D0


def test_exact_b_minus_one_winner_row_is_required_for_full_census() -> None:
    rows = [
        _row(day=D0, ordinal=D0_ORDINAL, security_num=12, episode_id="EP_NO_B1", winner=True, flagged=True),
        _row(day=B1, ordinal=B1_ORDINAL, security_num=13, episode_id="CTRL", winner=False, flagged=False),
    ]
    with pytest.raises(AtlasError, match="exact_bminus1_row_required"):
        build_discovery_atlas(
            pd.DataFrame(rows),
            methodology=METHODOLOGY,
            matched_control_contract=_match_contract(),
            fixture=True,
        )


def test_control_charge_and_trial_ledger_must_bind_together() -> None:
    with pytest.raises(AtlasError, match="charge_and_ledger_must_bind_together"):
        MatchedControlContract(
            methodology_contract_sha256=METHODOLOGY.methodology_contract_sha256,
            control_definition_id="INCOMPLETE_CHARGE_BINDING",
            match_columns=("sector", "size_bucket"),
            search_charge_receipt_sha256="b" * 64,
            trial_ledger_snapshot_sha256=None,
        )


def test_real_mode_requires_charged_control_definition_before_pit_integration() -> None:
    with pytest.raises(AtlasError, match="real_control_definition_charge_required"):
        build_discovery_atlas(
            _full_fixture_grid(),
            methodology=METHODOLOGY,
            matched_control_contract=_match_contract(),
            fixture=False,
        )


def test_control_definition_must_bind_same_frozen_methodology_hash() -> None:
    bad = MatchedControlContract(
        methodology_contract_sha256="c" * 64,
        control_definition_id="BAD_BINDING",
        match_columns=("sector", "size_bucket"),
        search_charge_receipt_sha256=None,
        trial_ledger_snapshot_sha256=None,
    )
    with pytest.raises(AtlasError, match="control_methodology_binding_mismatch"):
        build_discovery_atlas(
            _full_fixture_grid(),
            methodology=METHODOLOGY,
            matched_control_contract=bad,
            fixture=True,
        )


def test_noncanonical_identity_unmatured_labels_and_excluded_flags_fail_closed() -> None:
    grid = _full_fixture_grid()
    grid.loc[0, "security_id"] = "CIQSEC:1"
    with pytest.raises(AtlasError, match="canonical_ciqsec_required"):
        build_discovery_atlas(
            grid,
            methodology=METHODOLOGY,
            matched_control_contract=_match_contract(),
            fixture=True,
        )

    grid = _full_fixture_grid()
    grid.loc[0, "outcome_status"] = "UNMATURED_NOT_OPEN"
    with pytest.raises(AtlasError, match="outcome_status_invalid"):
        build_discovery_atlas(
            grid,
            methodology=METHODOLOGY,
            matched_control_contract=_match_contract(),
            fixture=True,
        )

    grid = _full_fixture_grid()
    excluded_index = grid.index[grid["eligibility_status"].eq("EXCLUDED")][0]
    grid.loc[excluded_index, "flagged"] = True
    with pytest.raises(AtlasError, match="excluded_row_cannot_be_flagged"):
        build_discovery_atlas(
            grid,
            methodology=METHODOLOGY,
            matched_control_contract=_match_contract(),
            fixture=True,
        )


def test_report_hash_tamper_fails_verification() -> None:
    report = build_discovery_atlas(
        _full_fixture_grid(),
        methodology=METHODOLOGY,
        matched_control_contract=_match_contract(),
        fixture=True,
    )
    tampered = copy.deepcopy(report)
    tampered["summary"]["true_winner_count_statistical"] = 999
    with pytest.raises(AtlasError, match="hash_mismatch"):
        verify_discovery_atlas(tampered)
