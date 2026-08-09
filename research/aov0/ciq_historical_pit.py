"""Legacy diagnostic historical-as-of normalizer; not A1/A2 authority.

The authoritative Lane-2 historical-fundamental path is
:mod:`research.aov0.historical_pit`, which requires provider-captured
``FilingVer=Original`` semantics and feeds the exact frozen current-cut AOV
builder.  This older eight-quarter normalizer is retained only for diagnostic
fixture compatibility; its caller-supplied availability boundary is not
sufficient to admit A1 or A2 evidence.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

from research.aov0.ciq_fundamentals import (
    IDENTITY_STATUS,
    build_current_state,
    derive_metrics,
)


SOURCE_ID = "SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS"
PANEL_SCHEMA = "aov0_ciq_historical_pit_entity_quarterly_panel_v1"
STATE_SCHEMA = "aov0_ciq_historical_pit_fundamental_state_v1"
PIT_MODE = "CIQ_VENDOR_HISTORICAL_ASOF_DATE_CONSERVATIVE_BOUNDARY"
REQUIRED_RELATIVE_PERIODS = tuple(f"FQ-{offset}" if offset else "FQ0" for offset in range(8))

RAW_METRIC_TO_COLUMN: Mapping[str, str] = {
    "IQ_TOTAL_REV": "total_revenue_q",
    "IQ_TOTAL_ASSETS": "total_assets_q",
    "IQ_INVENTORY": "inventory_q",
    "IQ_DA_SUPPL_CF": "depreciation_q",
    "IQ_TOTAL_EQUITY": "equity_q",
    "IQ_TOTAL_DEBT": "total_debt_q",
    "IQ_CASH_ST_INVEST": "cash_q",
    "IQ_OPER_INC": "operating_income_q",
    "IQ_CAPEX_BNK": "capex_q",
}

REQUIRED_RAW_COLUMNS = {
    "SP_ENTITY_ID",
    "relative_period",
    "IQ_PERIOD_END",
    "as_of_date",
    "pit_available_at_utc",
    "retrieved_at_utc",
    *RAW_METRIC_TO_COLUMN.keys(),
}

# Excel/COM may surface worksheet error values as HRESULT-like negative
# integers instead of '#N/A' text.  These exact values correspond to the
# standard Excel CVErr family (NULL through GETTING_DATA).  They are never
# admissible economic observations.
EXCEL_CVERR_HRESULTS = frozenset(
    {
        -2146826288,  # xlErrNull
        -2146826281,  # xlErrDiv0
        -2146826273,  # xlErrValue
        -2146826265,  # xlErrRef
        -2146826259,  # xlErrName
        -2146826252,  # xlErrNum
        -2146826246,  # xlErrNA
        -2146826245,  # xlErrGettingData
    }
)


class HistoricalPITError(ValueError):
    """Fail-closed historical PIT admission error."""


def normalize_historical_pit_fundamentals(
    raw: pd.DataFrame,
    *,
    frozen_entity_ids: Iterable[object],
    expected_as_of_date: str | date,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Normalize one eight-quarter CIQ historical-as-of snapshot.

    The raw capture must contain exactly one row for every
    ``frozen_entity_id × FQ0..FQ-7`` pair.  Individual metric values may be
    missing; missingness remains explicit and drives the existing Rule100
    factor-coverage exclusions.
    """

    if not isinstance(raw, pd.DataFrame) or raw.empty:
        raise HistoricalPITError("aov0_historical_pit_raw_required")
    missing_columns = sorted(REQUIRED_RAW_COLUMNS - set(raw.columns))
    if missing_columns:
        raise HistoricalPITError(
            "aov0_historical_pit_columns_missing:" + ",".join(missing_columns)
        )

    frozen = tuple(sorted(str(value).strip() for value in frozen_entity_ids))
    if not frozen or any(not value for value in frozen) or len(frozen) != len(set(frozen)):
        raise HistoricalPITError("aov0_historical_pit_frozen_entity_ids_invalid")

    expected_date = pd.Timestamp(expected_as_of_date).date()
    work = raw.copy()
    work["source_entity_id"] = work["SP_ENTITY_ID"].fillna("").astype(str).str.strip()
    work["relative_period"] = work["relative_period"].fillna("").astype(str).str.strip().str.upper()
    actual_entities = set(work["source_entity_id"])
    if actual_entities != set(frozen):
        raise HistoricalPITError("aov0_historical_pit_frozen_entity_membership_mismatch")

    expected_pairs = {
        (entity_id, period)
        for entity_id in frozen
        for period in REQUIRED_RELATIVE_PERIODS
    }
    actual_pairs = list(zip(work["source_entity_id"], work["relative_period"], strict=True))
    if len(actual_pairs) != len(expected_pairs) or set(actual_pairs) != expected_pairs:
        raise HistoricalPITError("aov0_historical_pit_entity_period_grid_invalid")
    if len(actual_pairs) != len(set(actual_pairs)):
        raise HistoricalPITError("aov0_historical_pit_duplicate_entity_period")

    as_of_dates = pd.to_datetime(work["as_of_date"], errors="coerce").dt.date
    if as_of_dates.isna().any() or set(as_of_dates) != {expected_date}:
        raise HistoricalPITError("aov0_historical_pit_as_of_date_mismatch")

    available = pd.to_datetime(work["pit_available_at_utc"], errors="coerce", utc=True)
    retrieved = pd.to_datetime(work["retrieved_at_utc"], errors="coerce", utc=True)
    if available.isna().any() or retrieved.isna().any():
        raise HistoricalPITError("aov0_historical_pit_timestamp_invalid")
    if available.nunique() != 1:
        raise HistoricalPITError("aov0_historical_pit_availability_boundary_not_singleton")
    availability_boundary = available.iloc[0]
    retrieval_start = retrieved.min()
    retrieval_end = retrieved.max()
    if (retrieved <= availability_boundary).any():
        # The intended operating mode is retrospective retrieval.  Rejecting
        # earlier retrieval also catches accidental timestamp-field swaps.
        raise HistoricalPITError("aov0_historical_pit_retrieval_boundary_order_invalid")

    period_end = pd.to_datetime(work["IQ_PERIOD_END"], errors="coerce").dt.normalize()
    future_period = period_end.notna() & period_end.dt.date.gt(expected_date)
    if future_period.any():
        raise HistoricalPITError("aov0_historical_pit_future_period_end")

    panel = pd.DataFrame(
        {
            "source_entity_id": work["source_entity_id"],
            "period_end": period_end,
            "known_at": availability_boundary,
            "pit_mode": PIT_MODE,
            "identity_status": IDENTITY_STATUS,
            "source_period_labels": work["relative_period"],
        }
    )
    for raw_name, normalized_name in RAW_METRIC_TO_COLUMN.items():
        panel[normalized_name] = _numeric(work[raw_name])

    # ``derive_metrics`` expects these current-panel columns even though they
    # do not enter the frozen four Rule100 factor groups.  Preserve them as
    # explicit missing values rather than querying unnecessary provider fields.
    panel["current_debt_q"] = np.nan
    panel["total_liabilities_q"] = np.nan

    panel = panel.loc[panel["period_end"].notna()].copy()
    if panel.empty:
        raise HistoricalPITError("aov0_historical_pit_no_period_rows")
    if panel.duplicated(["source_entity_id", "period_end"]).any():
        raise HistoricalPITError("aov0_historical_pit_duplicate_period_end")

    panel = panel.sort_values(["source_entity_id", "period_end"]).reset_index(drop=True)
    panel = derive_metrics(panel)
    panel["is_latest_known_quarter"] = False
    latest_idx = panel.groupby("source_entity_id", sort=False)["period_end"].idxmax()
    panel.loc[latest_idx, "is_latest_known_quarter"] = True
    panel["schema_version"] = PANEL_SCHEMA
    panel["source_id"] = SOURCE_ID

    state, factor_meta = build_current_state(panel, all_entity_ids=set(frozen))
    state["pit_mode"] = PIT_MODE
    state["identity_status"] = IDENTITY_STATUS
    state["schema_version"] = STATE_SCHEMA
    state["source_id"] = SOURCE_ID
    state["historical_as_of_date"] = expected_date.isoformat()
    state["pit_available_at_utc"] = availability_boundary
    state["retrieved_at_utc"] = retrieval_end

    metadata: dict[str, Any] = {
        "schema_version": "aov0_ciq_historical_pit_admission_metadata_v1",
        "source_id": SOURCE_ID,
        "pit_mode": PIT_MODE,
        "historical_as_of_date": expected_date.isoformat(),
        "pit_available_at_utc": _iso_utc(availability_boundary),
        "retrieved_at_utc": _iso_utc(retrieval_end),
        "retrieval_window_start_utc": _iso_utc(retrieval_start),
        "retrieval_window_end_utc": _iso_utc(retrieval_end),
        "frozen_entity_count": len(frozen),
        "relative_periods": list(REQUIRED_RELATIVE_PERIODS),
        "raw_grid_row_count": int(len(work)),
        "admitted_quarter_row_count": int(len(panel)),
        "entities_with_period_history": int(panel["source_entity_id"].nunique()),
        "entities_without_period_history": sorted(set(frozen) - set(panel["source_entity_id"])),
        "financial_alpha_evidence": 0,
        "evidence_authority": "LEGACY_DIAGNOSTIC_ONLY_NOT_A1_A2_AUTHORITY",
        **factor_meta,
    }
    return panel, state.reset_index(drop=True), metadata


def _numeric(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    upper = text.str.upper()
    text = text.mask(
        upper.isin({"", "NA", "N/A", "NAN", "NULL", "NONE"})
        | text.str.startswith("#")
    )
    numeric = pd.to_numeric(text, errors="coerce")
    return numeric.mask(numeric.isin(EXCEL_CVERR_HRESULTS))


def _iso_utc(value: pd.Timestamp | datetime) -> str:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize(timezone.utc)
    else:
        stamp = stamp.tz_convert(timezone.utc)
    return stamp.isoformat().replace("+00:00", "Z")
