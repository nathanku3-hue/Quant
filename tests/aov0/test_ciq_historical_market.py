from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.aov0.ciq_historical_market import admit_historical_market_parts


def _raw() -> tuple[pd.DataFrame, str, str, str]:
    pre = pd.bdate_range(end="2025-06-30", periods=205)
    post = pd.bdate_range(start="2025-07-01", periods=5)
    dates = pre.append(post)
    rows = []
    for entity_id, security_id, ciq_id, trading in (
        ("1", "101", "IQ101", "SPT101"),
        ("2", "202", "IQ202", "SPT202"),
    ):
        for index, day in enumerate(dates):
            rows.append(
                {
                    "SPT_DATE": day.date().isoformat(),
                    "SP_ENTITY_ID": entity_id,
                    "SP_SECURITY_ID": security_id,
                    "SP_CIQ_ID": ciq_id,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SP_TRADING_ITEM_ID": trading.removeprefix("SPT"),
                    "SPT_TOTAL_RETURN": str(0.1 + 0.01 * np.sin(index / 5.0)),
                    "SPT_CLOSE": str(100.0 + index),
                    "SPT_VOLUME": str(1_000_000 + index),
                }
            )
    frame = pd.DataFrame(rows)
    return frame, dates[0].date().isoformat(), dates[-1].date().isoformat(), "2025-06-30"


def test_historical_market_parts_merge_to_exact_primary_grid_and_200_close_gate() -> None:
    raw, start, end, target = _raw()
    split_day = pd.Timestamp("2025-03-31")
    dates = pd.to_datetime(raw["SPT_DATE"])
    admitted = admit_historical_market_parts(
        [raw.loc[dates.le(split_day)], raw.loc[dates.gt(split_day)]],
        frozen_entity_ids={"1", "2"},
        expected_start_date=start,
        expected_end_date=end,
        decision_target_date=target,
    )
    assert admitted.metadata["duplicate_key_conflicts"] == 0
    assert admitted.metadata["ge200_with_target_count"] == 2
    assert admitted.metadata["exact_primary_spt_query"] is True
    assert admitted.metadata["query_identity_key"] == "SPT_INSTRUMENT_ITEM_ID_FROM_INPUT_SECURITY_MASTER"
    assert admitted.metadata["identity_columns_source"] == "EXTERNAL_INPUT_SECURITY_MASTER"
    assert admitted.metadata["historical_primary_identity_reconstructed"] is False
    assert admitted.metadata["historical_primary_identity_authority"] == (
        "NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT"
    )
    assert admitted.metadata["alternate_listing_backfill_used"] is False
    assert admitted.metadata["financial_alpha_evidence"] == 0
    assert admitted.counts["completed_pre_target"].tolist() == [205, 205]
    assert admitted.counts["target_date_present"].all()
    assert admitted.counts["completed_post_target"].tolist() == [5, 5]


def test_historical_market_parts_reject_overlap_or_missing_weekday_grid() -> None:
    raw, start, end, target = _raw()
    with pytest.raises(ValueError, match="duplicate_key"):
        admit_historical_market_parts(
            [raw, raw.iloc[:2]],
            frozen_entity_ids={"1", "2"},
            expected_start_date=start,
            expected_end_date=end,
            decision_target_date=target,
        )

    missing_day = pd.Timestamp(raw["SPT_DATE"].iloc[10])
    missing = raw.loc[pd.to_datetime(raw["SPT_DATE"]).ne(missing_day)]
    with pytest.raises(ValueError, match="weekday_grid_invalid"):
        admit_historical_market_parts(
            [missing],
            frozen_entity_ids={"1", "2"},
            expected_start_date=start,
            expected_end_date=end,
            decision_target_date=target,
        )


def test_historical_market_parts_fail_closed_on_identity_drift() -> None:
    raw, start, end, target = _raw()
    raw = raw.copy()
    mask = raw["SP_ENTITY_ID"].eq("2") & raw["SPT_DATE"].eq(target)
    raw.loc[mask, "SP_CIQ_ID"] = "IQ999"
    with pytest.raises(ValueError, match="date_local_frozen_entity_grid_invalid|entity_identity_not_one_to_one"):
        admit_historical_market_parts(
            [raw],
            frozen_entity_ids={"1", "2"},
            expected_start_date=start,
            expected_end_date=end,
            decision_target_date=target,
        )


def test_historical_market_excel_cverr_hresult_is_explicitly_incomplete() -> None:
    raw, start, end, target = _raw()
    raw = raw.copy()
    mask = raw["SP_ENTITY_ID"].eq("1") & raw["SPT_DATE"].eq(target)
    raw.loc[mask, "SPT_CLOSE"] = "-2146826246"
    admitted = admit_historical_market_parts(
        [raw],
        frozen_entity_ids={"1", "2"},
        expected_start_date=start,
        expected_end_date=end,
        decision_target_date=target,
    )
    first = admitted.counts.loc[admitted.counts["SP_ENTITY_ID"].eq("1")].iloc[0]
    assert int(first["completed_pre_target"]) == 204
    assert bool(first["target_date_present"]) is False
    assert admitted.metadata["ge200_with_target_count"] == 1
