from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd
import pytest

from research.aov0.historical_checkpoint import (
    DECISION_AUTHORITY,
    build_historical_aov_decision_checkpoint,
    split_historical_market_custody,
    verify_historical_aov_decision_checkpoint,
)


TARGET_DATE = "2025-06-30"
CUT_TIME = "2025-06-30T20:05:00Z"
FROZEN = {"1", "2", "3", "4"}
BINDINGS = {
    "historical_fundamentals": "a" * 64,
    "primary_security_master": "b" * 64,
    "decision_market": "c" * 64,
}


def _fundamentals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_entity_id": ["1", "2", "3", "4"],
            "factor_present_count": [4, 3, 2, 4],
            "factor_positive_count": [4, 2, 2, 1],
            "known_at": ["2025-06-30T12:00:00Z"] * 4,
            "pit_mode": ["CIQ_VENDOR_HISTORICAL_ASOF_DATE_CONSERVATIVE_BOUNDARY"] * 4,
        }
    )


def _master() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "2", "3", "4"],
            "SP_SECURITY_ID": ["101", "202", "303", "404"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT101", "SPT202", "SPT303", "SPT404"],
            "Primary Security Flag": ["Yes"] * 4,
            "Ticker": ["AAA", "BBB", "CCC", "DDD"],
            "Exchange": ["NASDAQ", "NYSE", "NYSE", "NASDAQ"],
            "Description": ["Common Stock"] * 4,
        }
    )


def _market(rows: int = 210, *, include_future: bool = False) -> pd.DataFrame:
    dates = pd.bdate_range(end=TARGET_DATE, periods=rows)
    if include_future:
        dates = dates.append(pd.bdate_range(start="2025-07-01", periods=5))
    frames = []
    for entity, security, trading, slope in (
        ("1", "101", "SPT101", 0.12),
        ("2", "202", "SPT202", 0.08),
        ("3", "303", "SPT303", 0.10),
        ("4", "404", "SPT404", 0.09),
    ):
        x = np.arange(len(dates), dtype=float)
        frames.append(
            pd.DataFrame(
                {
                    "SPT_DATE": dates,
                    "SP_SECURITY_ID": security,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SPT_CLOSE": 50.0 + slope * x + 0.15 * np.sin(x / 3.0),
                    "SPT_VOLUME": 1_000_000.0 + 15_000.0 * (x % 17),
                    "SPT_TOTAL_RETURN": 0.35 + 0.18 * np.sin(x / 5.0),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def _build(market: pd.DataFrame):
    return build_historical_aov_decision_checkpoint(
        security_master_raw=_master(),
        decision_market_raw=market,
        fundamental_state=_fundamentals(),
        frozen_entity_ids=FROZEN,
        target_date=TARGET_DATE,
        decision_cut_time=CUT_TIME,
        source_bindings=BINDINGS,
    )


def test_historical_checkpoint_reuses_frozen_aov_path_and_has_no_outcome_authority() -> None:
    checkpoint = _build(_market())
    verify_historical_aov_decision_checkpoint(checkpoint)

    assert checkpoint.manifest["decision_authority"] == DECISION_AUTHORITY
    assert checkpoint.manifest["outcome_data_loaded"] is False
    assert checkpoint.manifest["outcome_authority"] == "NONE"
    assert checkpoint.manifest["parent_child_mutation_authority"] == "NONE"
    assert checkpoint.manifest["financial_alpha_evidence"] == 0
    assert checkpoint.manifest["frozen_candidate_entity_count"] == 4
    assert checkpoint.manifest["admitted_security_count"] == 3
    assert checkpoint.manifest["mechanical_exclusion_reasons"] == {"INSUFFICIENT_FACTOR_COVERAGE": 1}
    assert checkpoint.dag.rule100.index.tolist() == [pd.Timestamp(TARGET_DATE)]
    assert checkpoint.dag.rule100.columns.equals(checkpoint.dag.parent.columns)
    assert checkpoint.dag.parent.columns.equals(checkpoint.dag.child.columns)
    assert (checkpoint.dag.child <= checkpoint.dag.parent + 1e-12).all().all()


def test_historical_checkpoint_rejects_post_target_rows_at_decision_boundary() -> None:
    with pytest.raises(ValueError, match="post_target_market_forbidden"):
        _build(_market(include_future=True))


def test_market_custody_split_keeps_future_bytes_out_of_decision_identity() -> None:
    full_a = _market(include_future=True)
    full_b = full_a.copy()
    future_mask = pd.to_datetime(full_b["SPT_DATE"]).gt(pd.Timestamp(TARGET_DATE))
    full_b.loc[future_mask, "SPT_TOTAL_RETURN"] = 999.0
    full_b.loc[future_mask, "SPT_CLOSE"] = 99999.0

    decision_a, outcome_a = split_historical_market_custody(full_a, target_date=TARGET_DATE)
    decision_b, outcome_b = split_historical_market_custody(full_b, target_date=TARGET_DATE)
    assert decision_a.equals(decision_b)
    assert not outcome_a.equals(outcome_b)

    checkpoint_a = _build(decision_a)
    checkpoint_b = _build(decision_b)
    assert checkpoint_a.checkpoint_id == checkpoint_b.checkpoint_id
    assert checkpoint_a.manifest["target_vector_hashes"] == checkpoint_b.manifest["target_vector_hashes"]


def test_historical_checkpoint_rejects_current_or_late_fundamental_authority() -> None:
    current = _fundamentals()
    current["pit_mode"] = "CIQ_CURRENT_CUT_ASOF_ADMISSION_V1"
    with pytest.raises(ValueError, match="current_fundamentals_forbidden"):
        build_historical_aov_decision_checkpoint(
            security_master_raw=_master(),
            decision_market_raw=_market(),
            fundamental_state=current,
            frozen_entity_ids=FROZEN,
            target_date=TARGET_DATE,
            decision_cut_time=CUT_TIME,
            source_bindings=BINDINGS,
        )

    late = _fundamentals()
    late["known_at"] = "2025-07-01T12:00:00Z"
    with pytest.raises(ValueError, match="future_fundamental_knowledge|available_after_target_date"):
        build_historical_aov_decision_checkpoint(
            security_master_raw=_master(),
            decision_market_raw=_market(),
            fundamental_state=late,
            frozen_entity_ids=FROZEN,
            target_date=TARGET_DATE,
            decision_cut_time=CUT_TIME,
            source_bindings=BINDINGS,
        )


def test_checkpoint_hash_tamper_fails_closed() -> None:
    checkpoint = _build(_market())
    tampered_manifest = dict(checkpoint.manifest)
    tampered_manifest["rule100_risky_gross"] = "0"
    tampered = type(checkpoint)(
        checkpoint_id=checkpoint.checkpoint_id,
        manifest=tampered_manifest,
        market_slice=checkpoint.market_slice,
        cube=checkpoint.cube,
        dag=checkpoint.dag,
    )
    with pytest.raises(ValueError, match="hash_mismatch"):
        verify_historical_aov_decision_checkpoint(tampered)
