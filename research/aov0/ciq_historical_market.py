"""Admission rules for restartable historical CIQ primary-security market custody."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

import numpy as np
import pandas as pd


HISTORICAL_MARKET_SOURCE_ID = "SPCIQPRO:HISTORICAL_PRIMARY_SECURITY_MARKET_DATA"
HISTORICAL_MARKET_SCHEMA = "aov0_ciq_historical_primary_market_v1"

REQUIRED_COLUMNS = {
    "SPT_DATE",
    "SP_ENTITY_ID",
    "SP_SECURITY_ID",
    "SP_CIQ_ID",
    "SPT_INSTRUMENT_ITEM_ID",
    "SP_TRADING_ITEM_ID",
    "SPT_TOTAL_RETURN",
    "SPT_CLOSE",
    "SPT_VOLUME",
}

EXCEL_CVERR_HRESULTS = frozenset(
    {
        -2146826288,
        -2146826281,
        -2146826273,
        -2146826265,
        -2146826259,
        -2146826252,
        -2146826246,
        -2146826245,
    }
)


@dataclass(frozen=True)
class HistoricalMarketAdmission:
    raw: pd.DataFrame
    counts: pd.DataFrame
    metadata: dict[str, Any]


class HistoricalMarketError(ValueError):
    """Fail-closed historical market custody error."""


def admit_historical_market_parts(
    parts: Iterable[pd.DataFrame],
    *,
    frozen_entity_ids: Iterable[object],
    expected_start_date: str | date,
    expected_end_date: str | date,
    decision_target_date: str | date,
    min_pre_target_completed_closes: int = 200,
) -> HistoricalMarketAdmission:
    frames = [frame.copy() for frame in parts]
    if not frames or any(not isinstance(frame, pd.DataFrame) or frame.empty for frame in frames):
        raise HistoricalMarketError("aov0_historical_market_parts_required")
    for frame in frames:
        missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
        if missing:
            raise HistoricalMarketError("aov0_historical_market_columns_missing:" + ",".join(missing))

    frozen = tuple(sorted(str(value).strip() for value in frozen_entity_ids))
    if not frozen or any(not value for value in frozen) or len(frozen) != len(set(frozen)):
        raise HistoricalMarketError("aov0_historical_market_frozen_entities_invalid")
    start = pd.Timestamp(expected_start_date).normalize()
    end = pd.Timestamp(expected_end_date).normalize()
    target = pd.Timestamp(decision_target_date).normalize()
    if end < start or target < start or target > end:
        raise HistoricalMarketError("aov0_historical_market_date_contract_invalid")
    if int(min_pre_target_completed_closes) < 200:
        raise HistoricalMarketError("aov0_historical_market_min_history_below_frozen_200")

    raw = pd.concat(frames, ignore_index=True)
    raw["SPT_DATE"] = pd.to_datetime(raw["SPT_DATE"], errors="raise").dt.normalize()
    for column in (
        "SP_ENTITY_ID",
        "SP_SECURITY_ID",
        "SP_CIQ_ID",
        "SPT_INSTRUMENT_ITEM_ID",
        "SP_TRADING_ITEM_ID",
    ):
        raw[column] = raw[column].fillna("").astype(str).str.strip()
        if raw[column].eq("").any():
            raise HistoricalMarketError(f"aov0_historical_market_identity_missing:{column}")

    if raw["SPT_DATE"].lt(start).any() or raw["SPT_DATE"].gt(end).any():
        raise HistoricalMarketError("aov0_historical_market_row_outside_expected_range")
    expected_weekdays = pd.bdate_range(start=start, end=end)
    actual_dates = pd.DatetimeIndex(sorted(raw["SPT_DATE"].unique())).normalize()
    if not actual_dates.equals(expected_weekdays):
        missing = sorted(set(expected_weekdays) - set(actual_dates))
        extra = sorted(set(actual_dates) - set(expected_weekdays))
        raise HistoricalMarketError(
            "aov0_historical_market_weekday_grid_invalid:"
            f"missing={','.join(day.date().isoformat() for day in missing[:10])};"
            f"extra={','.join(day.date().isoformat() for day in extra[:10])}"
        )

    key = ["SPT_DATE", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID"]
    if raw.duplicated(key).any():
        raise HistoricalMarketError("aov0_historical_market_duplicate_key")

    entity_sets = raw.groupby("SPT_DATE", sort=False)["SP_ENTITY_ID"].agg(lambda series: tuple(sorted(set(series))))
    if any(value != frozen for value in entity_sets):
        raise HistoricalMarketError("aov0_historical_market_date_local_frozen_entity_grid_invalid")
    counts_per_date = raw.groupby("SPT_DATE", sort=False).size()
    if not counts_per_date.eq(len(frozen)).all():
        raise HistoricalMarketError("aov0_historical_market_date_local_row_count_invalid")

    identity = raw[
        ["SP_ENTITY_ID", "SP_SECURITY_ID", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID", "SP_TRADING_ITEM_ID"]
    ].drop_duplicates()
    if identity["SP_ENTITY_ID"].duplicated().any():
        raise HistoricalMarketError("aov0_historical_market_entity_identity_not_one_to_one")
    if set(identity["SP_ENTITY_ID"]) != set(frozen):
        raise HistoricalMarketError("aov0_historical_market_identity_membership_mismatch")
    for column in ("SP_SECURITY_ID", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID", "SP_TRADING_ITEM_ID"):
        if identity[column].duplicated().any():
            raise HistoricalMarketError(f"aov0_historical_market_identity_collision:{column}")

    completed = pd.DataFrame(
        {
            "SPT_DATE": raw["SPT_DATE"],
            "SP_ENTITY_ID": raw["SP_ENTITY_ID"],
            "SP_CIQ_ID": raw["SP_CIQ_ID"],
            "SPT_INSTRUMENT_ITEM_ID": raw["SPT_INSTRUMENT_ITEM_ID"],
            "close": _numeric(raw["SPT_CLOSE"]),
            "total_return": _numeric(raw["SPT_TOTAL_RETURN"]),
            "volume": _numeric(raw["SPT_VOLUME"]),
        }
    )
    completed["complete"] = (
        completed[["close", "total_return", "volume"]].notna().all(axis=1)
        & np.isfinite(completed[["close", "total_return", "volume"]].fillna(np.nan).to_numpy(dtype=float)).all(axis=1)
        & completed["close"].gt(0.0)
        & completed["volume"].gt(0.0)
    )
    count_rows = []
    for _, identity_row in identity.sort_values("SP_CIQ_ID").iterrows():
        entity_id = str(identity_row["SP_ENTITY_ID"])
        subset = completed.loc[completed["SP_ENTITY_ID"].eq(entity_id)]
        pre = subset.loc[subset["SPT_DATE"].le(target) & subset["complete"]]
        post = subset.loc[subset["SPT_DATE"].gt(target) & subset["complete"]]
        target_present = bool(subset.loc[subset["SPT_DATE"].eq(target), "complete"].any())
        count_rows.append(
            {
                "SP_ENTITY_ID": entity_id,
                "SP_CIQ_ID": str(identity_row["SP_CIQ_ID"]),
                "SPT_INSTRUMENT_ITEM_ID": str(identity_row["SPT_INSTRUMENT_ITEM_ID"]),
                "completed_pre_target": int(len(pre)),
                "target_date_present": target_present,
                "completed_post_target": int(len(post)),
            }
        )
    counts = pd.DataFrame(count_rows).sort_values("SP_CIQ_ID").reset_index(drop=True)
    eligible = counts["completed_pre_target"].ge(int(min_pre_target_completed_closes)) & counts["target_date_present"]

    raw = raw.sort_values(["SPT_DATE", "SP_CIQ_ID", "SPT_INSTRUMENT_ITEM_ID"]).reset_index(drop=True)
    raw["schema_version"] = HISTORICAL_MARKET_SCHEMA
    metadata = {
        "schema_version": "aov0_ciq_historical_market_admission_metadata_v1",
        "source_id": HISTORICAL_MARKET_SOURCE_ID,
        "expected_start_date": start.date().isoformat(),
        "expected_end_date": end.date().isoformat(),
        "decision_target_date": target.date().isoformat(),
        "frozen_entity_count": len(frozen),
        "weekday_count": int(len(expected_weekdays)),
        "raw_grid_row_count": int(len(raw)),
        "duplicate_key_conflicts": 0,
        "min_pre_target_completed_closes": int(min_pre_target_completed_closes),
        "ge200_with_target_count": int(eligible.sum()),
        # Legacy field name retained for receipt compatibility.  It means the
        # provider query used exactly the SPT instrument supplied by the input
        # security master; it does *not* prove that SPT was provider-primary at
        # the historical decision date.
        "exact_primary_spt_query": True,
        "query_identity_key": "SPT_INSTRUMENT_ITEM_ID_FROM_INPUT_SECURITY_MASTER",
        "identity_columns_source": "EXTERNAL_INPUT_SECURITY_MASTER",
        "historical_primary_identity_reconstructed": False,
        "historical_primary_identity_authority": "NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT",
        "alternate_listing_backfill_used": False,
        "financial_alpha_evidence": 0,
        "evidence_authority": "HISTORICAL_MARKET_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY",
    }
    return HistoricalMarketAdmission(raw=raw, counts=counts, metadata=metadata)


def _numeric(series: pd.Series) -> pd.Series:
    text = series.astype(str).str.strip()
    upper = text.str.upper()
    text = text.mask(
        upper.isin({"", "NA", "N/A", "NAN", "NULL", "NONE"})
        | text.str.startswith("#")
    )
    numeric = pd.to_numeric(text, errors="coerce")
    return numeric.mask(numeric.isin(EXCEL_CVERR_HRESULTS))
