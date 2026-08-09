from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

from research.aov0.ciq_historical_pit import (
    PIT_MODE,
    REQUIRED_RELATIVE_PERIODS,
    normalize_historical_pit_fundamentals,
)


AS_OF_DATE = "2025-06-29"
AVAILABLE_AT = "2025-06-30T12:00:00Z"
RETRIEVED_AT = "2026-08-08T20:30:00Z"


def _raw() -> pd.DataFrame:
    period_ends = [
        "2025-04-27",
        "2025-01-26",
        "2024-10-27",
        "2024-07-28",
        "2024-04-28",
        "2024-01-28",
        "2023-10-29",
        "2023-07-30",
    ]
    rows = []
    for entity_index, entity_id in enumerate(("1001", "1002"), start=1):
        for period_index, (relative_period, period_end) in enumerate(
            zip(REQUIRED_RELATIVE_PERIODS, period_ends, strict=True)
        ):
            scale = entity_index * 100 + (8 - period_index) * 5
            rows.append(
                {
                    "SP_ENTITY_ID": entity_id,
                    "relative_period": relative_period,
                    "IQ_PERIOD_END": period_end,
                    "IQ_TOTAL_REV": str(scale * 10),
                    "IQ_TOTAL_ASSETS": str(scale * 20),
                    "IQ_INVENTORY": str(scale * 2),
                    "IQ_DA_SUPPL_CF": str(scale / 5),
                    "IQ_TOTAL_EQUITY": str(scale * 8),
                    "IQ_TOTAL_DEBT": str(scale * 3),
                    "IQ_CASH_ST_INVEST": str(scale),
                    "IQ_OPER_INC": str(scale * 2),
                    "IQ_CAPEX_BNK": str(scale / 2),
                    "as_of_date": AS_OF_DATE,
                    "pit_available_at_utc": AVAILABLE_AT,
                    "retrieved_at_utc": RETRIEVED_AT,
                }
            )
    return pd.DataFrame(rows)


def test_historical_pit_admission_builds_eight_quarter_factor_state_without_future_authority() -> None:
    panel, state, metadata = normalize_historical_pit_fundamentals(
        _raw(),
        frozen_entity_ids={"1001", "1002"},
        expected_as_of_date=AS_OF_DATE,
    )
    assert len(panel) == 16
    assert len(state) == 2
    assert set(state["source_entity_id"]) == {"1001", "1002"}
    assert state["pit_mode"].eq(PIT_MODE).all()
    assert pd.to_datetime(state["pit_available_at_utc"], utc=True).eq(
        pd.Timestamp(AVAILABLE_AT)
    ).all()
    assert metadata["historical_as_of_date"] == AS_OF_DATE
    assert metadata["financial_alpha_evidence"] == 0
    assert metadata["evidence_authority"] == "LEGACY_DIAGNOSTIC_ONLY_NOT_A1_A2_AUTHORITY"
    assert metadata["entities_with_period_history"] == 2
    assert state["factor_present_count"].ge(0).all()


def test_historical_pit_admission_requires_exact_entity_period_grid() -> None:
    raw = _raw().iloc[:-1].copy()
    with pytest.raises(ValueError, match="entity_period_grid_invalid"):
        normalize_historical_pit_fundamentals(
            raw,
            frozen_entity_ids={"1001", "1002"},
            expected_as_of_date=AS_OF_DATE,
        )


def test_historical_pit_admission_rejects_future_period_end() -> None:
    raw = _raw()
    raw.loc[0, "IQ_PERIOD_END"] = "2025-07-01"
    with pytest.raises(ValueError, match="future_period_end"):
        normalize_historical_pit_fundamentals(
            raw,
            frozen_entity_ids={"1001", "1002"},
            expected_as_of_date=AS_OF_DATE,
        )


def test_historical_pit_admission_rejects_current_retrieval_as_historical_availability() -> None:
    raw = _raw()
    raw["retrieved_at_utc"] = "2025-06-30T11:00:00Z"
    with pytest.raises(ValueError, match="retrieval_boundary_order_invalid"):
        normalize_historical_pit_fundamentals(
            raw,
            frozen_entity_ids={"1001", "1002"},
            expected_as_of_date=AS_OF_DATE,
        )


def test_historical_pit_excel_cverr_hresult_is_missing_not_economic_data() -> None:
    raw = _raw()
    raw.loc[0, "IQ_TOTAL_REV"] = "-2146826246"
    panel, state, metadata = normalize_historical_pit_fundamentals(
        raw,
        frozen_entity_ids={"1001", "1002"},
        expected_as_of_date=AS_OF_DATE,
    )
    row = panel.loc[
        panel["source_entity_id"].eq("1001")
        & panel["source_period_labels"].eq("FQ0")
    ].iloc[0]
    assert pd.isna(row["total_revenue_q"])
    assert not (panel.select_dtypes(include="number") == -2146826246).any().any()
    assert metadata["financial_alpha_evidence"] == 0


def test_historical_pit_restartable_chunks_preserve_retrieval_window() -> None:
    raw = _raw()
    raw.loc[raw["SP_ENTITY_ID"].eq("1002"), "retrieved_at_utc"] = "2026-08-08T20:45:00Z"
    _, state, metadata = normalize_historical_pit_fundamentals(
        raw,
        frozen_entity_ids={"1001", "1002"},
        expected_as_of_date=AS_OF_DATE,
    )
    assert metadata["retrieval_window_start_utc"] == "2026-08-08T20:30:00Z"
    assert metadata["retrieval_window_end_utc"] == "2026-08-08T20:45:00Z"
    assert pd.to_datetime(state["retrieved_at_utc"], utc=True).eq(
        pd.Timestamp("2026-08-08T20:45:00Z")
    ).all()
