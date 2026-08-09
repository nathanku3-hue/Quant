"""Historical point-in-time replay inputs for the frozen AOV-0 contract.

This module is intentionally narrow. It does not tune Rule100, Parent, Child,
or any AOV parameter. It turns provider-captured historical as-of Capital IQ
fundamentals plus primary-security market rows into the exact daily inputs
consumed by :mod:`research.aov0.experiment`.

Historical evidence never changes ``financial_alpha_evidence``; that counter is
reserved for future-unseen prospective evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from research.aov0.ciq_fundamentals import (
    IDENTITY_STATUS,
    _METRICS,
    build_current_state,
    derive_metrics,
)
from research.aov0.ciq_market import (
    ADV_WINDOW,
    SMA_FAST_WINDOW,
    SMA_SLOW_WINDOW,
    VOL_WINDOW,
    _parse_market_raw,
    build_ciq_market_slice,
    normalize_primary_security_master,
)
from research.aov0.contracts import AOV0Contract, DEFAULT_CONTRACT, validate_contract
from research.aov0.cube import VerticalCube, activate_decision_cube_states, build_vertical_cube


HISTORICAL_PIT_FUNDAMENTAL_SCHEMA = "aov0_ciq_historical_asof_fundamentals_v1"
HISTORICAL_REPLAY_SCHEMA = "aov0_historical_pit_replay_inputs_v1"
HISTORICAL_PIT_MODE = "CIQ_SPG_ASOF_FILINGVER_ORIGINAL"
REQUIRED_RELATIVE_PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")
# Only these raw provider fields are required by the frozen fundamental feature
# formulas. The two legacy fields in _METRICS that are not used by derive_metrics
# are synthesized as NaN before calling the shared implementation.
REQUIRED_PROVIDER_METRICS = (
    "IQ_TOTAL_REV",
    "IQ_TOTAL_ASSETS",
    "IQ_INVENTORY",
    "IQ_DA_SUPPL_CF",
    "IQ_TOTAL_EQUITY",
    "IQ_TOTAL_DEBT",
    "IQ_CASH_ST_INVEST",
    "IQ_OPER_INC",
    "IQ_CAPEX_BNK",
)
MAX_SESSION_GAP_CALENDAR_DAYS = 4


@dataclass(frozen=True)
class HistoricalFactorStates:
    frame: pd.DataFrame
    snapshot_dates: pd.DatetimeIndex
    frozen_entity_ids: tuple[str, ...]


@dataclass(frozen=True)
class HistoricalMarketPanel:
    security_map: pd.DataFrame
    frame: pd.DataFrame
    mapping_exclusions: pd.DataFrame


@dataclass(frozen=True)
class HistoricalReplayInputs:
    # ``decision_rule100_weights`` are computed from the completed-week data
    # cut. ``rule100_weights`` are the same vectors activated at the next
    # observed market close. The latter are the only targets allowed into the
    # backtest engine, whose one-bar lag then starts P&L on the following close.
    decision_rule100_weights: pd.DataFrame
    rule100_weights: pd.DataFrame
    total_returns: pd.DataFrame
    primitives: pd.DataFrame
    cube: VerticalCube
    eligible_by_date: dict[pd.Timestamp, tuple[str, ...]]
    decision_dates: pd.DatetimeIndex
    activation_dates: pd.DatetimeIndex
    decision_to_activation: dict[pd.Timestamp, pd.Timestamp]
    security_ids: tuple[str, ...]
    metadata: dict[str, object]


def _asof_known_at(as_of_date: object) -> pd.Timestamp:
    """Conservatively treat a CIQ historical as-of date as known after ET day-end."""

    day = pd.Timestamp(as_of_date).normalize()
    if day.tzinfo is not None:
        day = day.tz_convert("America/New_York").tz_localize(None).normalize()
    local = day.tz_localize("America/New_York") + pd.Timedelta(hours=23, minutes=59, seconds=59)
    return local.tz_convert("UTC")


def _market_known_at(date: object) -> pd.Timestamp:
    """Historical daily market state is admitted only after the U.S. close."""

    day = pd.Timestamp(date).normalize()
    if day.tzinfo is not None:
        day = day.tz_convert("America/New_York").tz_localize(None).normalize()
    local = day.tz_localize("America/New_York") + pd.Timedelta(hours=16)
    return local.tz_convert("UTC")


def normalize_historical_pit_fundamentals(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate provider-captured SPG as-of rows without weakening source semantics.

    Expected shape is one row per ``as_of_date`` / company / relative quarter.
    Values must have been captured with ``FilingVer=Original``. Provider query
    metadata is retained when present but does not enter the factor formulas.
    """

    required = {"as_of_date", "source_entity_id", "relative_period", "period_end"}
    required.update(REQUIRED_PROVIDER_METRICS)
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"aov0_historical_pit_fundamentals_missing:{','.join(missing)}")
    if raw.empty:
        raise ValueError("aov0_historical_pit_fundamentals_empty")

    out = raw.copy()
    out["as_of_date"] = pd.to_datetime(out["as_of_date"], errors="raise").dt.normalize()
    out["source_entity_id"] = out["source_entity_id"].astype(str).str.strip()
    out["relative_period"] = out["relative_period"].astype(str).str.upper().str.strip()
    out["period_end"] = pd.to_datetime(out["period_end"], errors="coerce").dt.normalize()
    if (out["source_entity_id"] == "").any():
        raise ValueError("aov0_historical_pit_entity_id_missing")
    if (~out["relative_period"].isin(REQUIRED_RELATIVE_PERIODS)).any():
        raise ValueError("aov0_historical_pit_relative_period_invalid")
    if out.duplicated(["as_of_date", "source_entity_id", "relative_period"]).any():
        raise ValueError("aov0_historical_pit_duplicate_snapshot_row")
    if "filing_version" in out.columns:
        versions = out["filing_version"].astype(str).str.upper().str.strip()
        if (~versions.eq("ORIGINAL")).any():
            raise ValueError("aov0_historical_pit_filing_version_not_original")
    if "provider_function" in out.columns:
        functions = out["provider_function"].astype(str).str.upper().str.strip()
        if (~functions.eq("SPG")).any():
            raise ValueError("aov0_historical_pit_provider_function_not_spg")

    for column in REQUIRED_PROVIDER_METRICS:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    future_period = out["period_end"].notna() & out["period_end"].gt(out["as_of_date"])
    if future_period.any():
        raise ValueError("aov0_historical_pit_future_period_end")

    # FQ0 must exist for every company/snapshot. Older quarters may legitimately
    # be missing for young listings and are retained as NaN rather than backfilled.
    counts = (
        out.loc[out["relative_period"].eq("FQ0")]
        .groupby("as_of_date", sort=False)["source_entity_id"]
        .nunique()
    )
    all_counts = out.groupby("as_of_date", sort=False)["source_entity_id"].nunique()
    if not counts.reindex(all_counts.index, fill_value=0).eq(all_counts).all():
        raise ValueError("aov0_historical_pit_fq0_missing")

    out["known_at"] = out["as_of_date"].map(_asof_known_at)
    out["schema_version"] = HISTORICAL_PIT_FUNDAMENTAL_SCHEMA
    out["pit_mode"] = HISTORICAL_PIT_MODE
    return out.sort_values(["as_of_date", "source_entity_id", "relative_period"]).reset_index(drop=True)


def build_factor_transition_plan(period_matrix: pd.DataFrame) -> pd.DataFrame:
    """Return the exact sparse dates that require a five-quarter Original pull.

    The cheap weekly FQ0 period-end matrix is authoritative for transition
    detection. Missing FQ0 values are not interpretable as a quarter change and
    therefore fail closed rather than triggering a speculative provider query.
    """

    required = {"as_of_date", "source_entity_id", "fq0_period_end"}
    missing = sorted(required - set(period_matrix.columns))
    if missing:
        raise ValueError(f"aov0_historical_period_matrix_missing:{','.join(missing)}")
    matrix = period_matrix.loc[:, sorted(required)].copy()
    matrix["as_of_date"] = pd.to_datetime(matrix["as_of_date"], errors="raise").dt.normalize()
    matrix["source_entity_id"] = matrix["source_entity_id"].astype(str).str.strip()
    matrix["fq0_period_end"] = pd.to_datetime(matrix["fq0_period_end"], errors="coerce").dt.normalize()
    if matrix["source_entity_id"].eq("").any():
        raise ValueError("aov0_historical_period_matrix_entity_blank")
    if matrix["fq0_period_end"].isna().any():
        raise ValueError("aov0_historical_period_matrix_fq0_missing")
    if matrix.duplicated(["as_of_date", "source_entity_id"]).any():
        raise ValueError("aov0_historical_period_matrix_duplicate")

    date_entity_counts = matrix.groupby("as_of_date", sort=True)["source_entity_id"].nunique()
    if date_entity_counts.nunique() != 1:
        raise ValueError("aov0_historical_period_matrix_entity_grid_drift")
    entity_date_counts = matrix.groupby("source_entity_id", sort=True)["as_of_date"].nunique()
    if entity_date_counts.nunique() != 1:
        raise ValueError("aov0_historical_period_matrix_date_grid_drift")

    planned: list[dict[str, object]] = []
    for entity, entity_rows in matrix.groupby("source_entity_id", sort=True):
        entity_rows = entity_rows.sort_values("as_of_date")
        previous_period: pd.Timestamp | None = None
        for row in entity_rows.itertuples(index=False):
            as_of = pd.Timestamp(row.as_of_date).normalize()
            period = pd.Timestamp(row.fq0_period_end).normalize()
            if previous_period is None or period != previous_period:
                planned.append(
                    {
                        "source_entity_id": str(entity),
                        "as_of_date": as_of.date().isoformat(),
                        "fq0_period_end": period.date().isoformat(),
                        "transition_reason": "INITIAL" if previous_period is None else "FQ0_PERIOD_CHANGE",
                    }
                )
            previous_period = period
    if not planned:
        raise ValueError("aov0_historical_transition_plan_empty")
    return pd.DataFrame(planned).sort_values(["as_of_date", "source_entity_id"]).reset_index(drop=True)


def expand_transition_fundamentals(
    period_matrix: pd.DataFrame,
    transition_raw: pd.DataFrame,
) -> pd.DataFrame:
    """Expand sparse original-filing transition captures to weekly PIT snapshots.

    ``period_matrix`` is a cheap weekly SPG probe of ``IQ_PERIOD_END/FQ0`` for
    every frozen company. A full five-quarter raw capture is required only when
    that FQ0 period changes. Between transitions, ``FilingVer=Original`` keeps
    the original filing values invariant, so carrying the last captured state
    forward avoids redundant provider queries without introducing future data.
    """

    required_matrix = {"as_of_date", "source_entity_id", "fq0_period_end"}
    missing_matrix = sorted(required_matrix - set(period_matrix.columns))
    if missing_matrix:
        raise ValueError(f"aov0_historical_period_matrix_missing:{','.join(missing_matrix)}")
    matrix = period_matrix.loc[:, sorted(required_matrix)].copy()
    matrix["as_of_date"] = pd.to_datetime(matrix["as_of_date"], errors="raise").dt.normalize()
    matrix["source_entity_id"] = matrix["source_entity_id"].astype(str).str.strip()
    matrix["fq0_period_end"] = pd.to_datetime(matrix["fq0_period_end"], errors="coerce").dt.normalize()
    if matrix.duplicated(["as_of_date", "source_entity_id"]).any():
        raise ValueError("aov0_historical_period_matrix_duplicate")

    transition_plan = build_factor_transition_plan(matrix)
    required_transition_pairs = {
        (pd.Timestamp(row.as_of_date).normalize(), str(row.source_entity_id))
        for row in transition_plan.itertuples(index=False)
    }

    transitions = normalize_historical_pit_fundamentals(transition_raw)
    transition_keys = (
        transitions[["as_of_date", "source_entity_id"]]
        .drop_duplicates()
        .sort_values(["source_entity_id", "as_of_date"])
    )
    observed_transition_pairs = {
        (pd.Timestamp(row.as_of_date).normalize(), str(row.source_entity_id))
        for row in transition_keys.itertuples(index=False)
    }
    if observed_transition_pairs != required_transition_pairs:
        missing_pairs = sorted(required_transition_pairs - observed_transition_pairs)
        extra_pairs = sorted(observed_transition_pairs - required_transition_pairs)
        if missing_pairs:
            date, entity = missing_pairs[0]
            raise ValueError(
                f"aov0_historical_transition_capture_missing:{entity}:{date.date().isoformat()}"
            )
        date, entity = extra_pairs[0]
        raise ValueError(
            f"aov0_historical_transition_capture_unplanned:{entity}:{date.date().isoformat()}"
        )

    matrix_fq0 = {
        (pd.Timestamp(row.as_of_date).normalize(), str(row.source_entity_id)): pd.Timestamp(row.fq0_period_end).normalize()
        for row in matrix.itertuples(index=False)
    }
    transition_fq0 = transitions.loc[transitions["relative_period"].eq("FQ0")].copy()
    for row in transition_fq0.itertuples(index=False):
        key = (pd.Timestamp(row.as_of_date).normalize(), str(row.source_entity_id))
        if pd.isna(row.period_end) or pd.Timestamp(row.period_end).normalize() != matrix_fq0[key]:
            raise ValueError(
                f"aov0_historical_transition_fq0_mismatch:{row.source_entity_id}:{pd.Timestamp(row.as_of_date).date().isoformat()}"
            )

    by_key = {
        (pd.Timestamp(date), str(entity)): group.copy()
        for (date, entity), group in transitions.groupby(["as_of_date", "source_entity_id"], sort=False)
    }

    expanded: list[pd.DataFrame] = []
    for entity, entity_matrix in matrix.groupby("source_entity_id", sort=True):
        entity_matrix = entity_matrix.sort_values("as_of_date")
        entity_transition_dates = transition_keys.loc[
            transition_keys["source_entity_id"].eq(entity), "as_of_date"
        ].tolist()
        latest_transition: pd.Timestamp | None = None
        previous_period: pd.Timestamp | pd.NaT = pd.NaT
        for row in entity_matrix.itertuples(index=False):
            as_of = pd.Timestamp(row.as_of_date)
            period = pd.Timestamp(row.fq0_period_end) if not pd.isna(row.fq0_period_end) else pd.NaT
            changed = (
                latest_transition is None
                or (pd.isna(previous_period) != pd.isna(period))
                or (not pd.isna(previous_period) and not pd.isna(period) and previous_period != period)
            )
            if changed:
                candidates = [date for date in entity_transition_dates if pd.Timestamp(date) == as_of]
                if not candidates:
                    raise ValueError(
                        f"aov0_historical_transition_capture_missing:{entity}:{as_of.date().isoformat()}"
                    )
                latest_transition = as_of
            if latest_transition is None:
                raise ValueError("aov0_historical_transition_not_initialized")
            source = by_key[(latest_transition, entity)].copy()
            source["source_transition_as_of_date"] = latest_transition
            source["as_of_date"] = as_of
            source["known_at"] = _asof_known_at(as_of)
            expanded.append(source)
            previous_period = period

    if not expanded:
        raise ValueError("aov0_historical_transition_expansion_empty")
    out = pd.concat(expanded, ignore_index=True, sort=False)
    return normalize_historical_pit_fundamentals(out)


def build_historical_factor_states(
    raw: pd.DataFrame,
    *,
    frozen_entity_ids: Iterable[object],
) -> HistoricalFactorStates:
    """Recompute the frozen Rule100 fundamental state independently at each as-of."""

    normalized = normalize_historical_pit_fundamentals(raw)
    frozen = tuple(sorted({str(value).strip() for value in frozen_entity_ids if str(value).strip()}))
    if not frozen:
        raise ValueError("aov0_historical_pit_frozen_universe_empty")
    unknown = sorted(set(normalized["source_entity_id"]) - set(frozen))
    if unknown:
        raise ValueError(f"aov0_historical_pit_entity_outside_frozen_universe:{unknown[0]}")

    states: list[pd.DataFrame] = []
    for as_of_date, snapshot in normalized.groupby("as_of_date", sort=True):
        panel = pd.DataFrame(
            {
                "source_entity_id": snapshot["source_entity_id"].astype(str),
                "source_entity_name": "",
                "industry": "",
                "exchange": "",
                "period_end": snapshot["period_end"],
                "known_at": snapshot["known_at"],
                "pit_mode": HISTORICAL_PIT_MODE,
                "identity_status": IDENTITY_STATUS,
                "source_period_labels": snapshot["relative_period"].astype(str),
            }
        )
        for provider_name, internal_name in _METRICS.items():
            if provider_name in snapshot.columns:
                panel[internal_name] = pd.to_numeric(snapshot[provider_name], errors="coerce").to_numpy()
            else:
                panel[internal_name] = np.nan
        panel = panel.loc[panel["period_end"].notna()].copy()
        if panel.empty:
            raise ValueError(f"aov0_historical_pit_snapshot_no_periods:{pd.Timestamp(as_of_date).date()}")
        panel = derive_metrics(panel)
        panel["is_latest_known_quarter"] = panel["source_period_labels"].eq("FQ0")
        state, _metadata = build_current_state(panel, all_entity_ids=set(frozen))
        state["as_of_date"] = pd.Timestamp(as_of_date).normalize()
        state["known_at"] = _asof_known_at(as_of_date)
        state["pit_mode"] = HISTORICAL_PIT_MODE
        states.append(state)

    combined = pd.concat(states, ignore_index=True, sort=False)
    if combined.duplicated(["as_of_date", "source_entity_id"]).any():
        raise ValueError("aov0_historical_pit_duplicate_factor_state")
    return HistoricalFactorStates(
        frame=combined.sort_values(["as_of_date", "source_entity_id"]).reset_index(drop=True),
        snapshot_dates=pd.DatetimeIndex(sorted(combined["as_of_date"].unique())),
        frozen_entity_ids=frozen,
    )


def build_historical_market_panel(
    *,
    security_master_raw: pd.DataFrame,
    market_parts: Sequence[pd.DataFrame],
    frozen_entity_ids: Iterable[object],
) -> HistoricalMarketPanel:
    """Normalize and reconcile real primary-security market parts.

    Overlap is allowed only when every economic value and identity agrees.
    Alternate listings and ticker fallbacks are never introduced.
    """

    frozen = {str(value).strip() for value in frozen_entity_ids if str(value).strip()}
    security_map, mapping_exclusions = normalize_primary_security_master(
        security_master_raw,
        frozen_entity_ids=frozen,
    )
    if security_map.empty:
        raise ValueError("aov0_historical_market_security_map_empty")
    if not market_parts:
        raise ValueError("aov0_historical_market_parts_empty")

    normalized_parts: list[pd.DataFrame] = []
    for part_index, raw in enumerate(market_parts):
        parsed = _parse_market_raw(raw, security_map)
        parsed["_part_index"] = int(part_index)
        normalized_parts.append(parsed)
    market = pd.concat(normalized_parts, ignore_index=True, sort=False)

    records: list[pd.Series] = []
    for (_date, _security), group in market.groupby(["date", "security_id"], sort=False):
        first = group.iloc[0]
        for column in ("trading_item_id", "source_entity_id"):
            if group[column].astype(str).nunique(dropna=False) != 1:
                raise ValueError(f"aov0_historical_market_overlap_identity_conflict:{column}")
        for column in ("total_return", "close", "volume"):
            values = pd.to_numeric(group[column], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            if finite.size == 0:
                continue
            if not np.allclose(finite, finite[0], rtol=1e-10, atol=1e-12):
                raise ValueError(f"aov0_historical_market_overlap_value_conflict:{column}")
        records.append(first)
    market = pd.DataFrame(records).drop(columns=["_part_index"], errors="ignore")
    market = market.sort_values(["security_id", "date"]).reset_index(drop=True)

    market["dollar_volume"] = pd.to_numeric(market["close"], errors="coerce") * pd.to_numeric(
        market["volume"], errors="coerce"
    )
    grouped = market.groupby("security_id", sort=False)
    market["adv20"] = grouped["dollar_volume"].rolling(ADV_WINDOW, min_periods=ADV_WINDOW).mean().reset_index(level=0, drop=True)
    market["realized_vol"] = (
        grouped["total_return"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std().reset_index(level=0, drop=True)
        * np.sqrt(252.0)
    )
    market["sma20"] = grouped["close"].rolling(SMA_FAST_WINDOW, min_periods=SMA_FAST_WINDOW).mean().reset_index(level=0, drop=True)
    market["sma200"] = grouped["close"].rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean().reset_index(level=0, drop=True)
    market["dist_sma20"] = (market["close"] - market["sma20"]) / market["sma20"].replace(0.0, np.nan)
    market["trend_veto"] = market["close"].lt(market["sma200"]).where(market["sma200"].notna())
    market["trend_fast"] = np.where(
        market["sma20"].notna(), np.where(market["close"] >= market["sma20"], 1.0, -1.0), np.nan
    )
    market["trend_slow"] = np.where(
        market["sma200"].notna(), np.where(market["close"] >= market["sma200"], 1.0, -1.0), np.nan
    )
    market["exit_capacity"] = market.groupby("date", sort=False)["adv20"].rank(pct=True, method="average")
    regime = market.groupby("date", sort=False)["trend_slow"].mean().clip(-1.0, 1.0)
    market["regime"] = market["date"].map(regime)
    market["valid_at"] = market["date"].map(_market_known_at)
    market["known_at"] = market["valid_at"]
    return HistoricalMarketPanel(
        security_map=security_map.sort_values("source_entity_id").reset_index(drop=True),
        frame=market.sort_values(["date", "security_id"]).reset_index(drop=True),
        mapping_exclusions=mapping_exclusions,
    )


def validate_historical_session_continuity(calendar: Sequence[object]) -> pd.DatetimeIndex:
    """Reject a supplied market tape that silently omits multiple sessions."""

    dates = pd.DatetimeIndex(pd.to_datetime(list(calendar))).normalize().sort_values().unique()
    if len(dates) < 2:
        return dates
    gap_days = pd.Series(dates[1:] - dates[:-1]).dt.days.to_numpy(dtype=int)
    bad = np.flatnonzero(gap_days > MAX_SESSION_GAP_CALENDAR_DAYS)
    if bad.size:
        position = int(bad[0])
        raise ValueError(
            "aov0_historical_market_calendar_gap:"
            f"{dates[position].date().isoformat()}:{dates[position + 1].date().isoformat()}"
        )
    return dates


def completed_week_decision_dates(calendar: Sequence[object]) -> pd.DatetimeIndex:
    """Return the last observed session of each completed ISO week.

    The final partial week is excluded unless its final session is a Friday.
    This prevents a truncated evaluation window from manufacturing a mid-week
    decision that would not exist in the frozen weekly attempt schedule.
    """

    dates = pd.DatetimeIndex(pd.to_datetime(list(calendar))).normalize().sort_values().unique()
    if dates.empty:
        return pd.DatetimeIndex([])
    frame = pd.DataFrame({"date": dates})
    iso = frame["date"].dt.isocalendar()
    frame["iso_year"] = iso.year.to_numpy()
    frame["iso_week"] = iso.week.to_numpy()
    decisions = frame.groupby(["iso_year", "iso_week"], sort=True)["date"].max()
    values = list(pd.DatetimeIndex(decisions.to_numpy()))
    if values and values[-1] == dates[-1] and dates[-1].weekday() < 4:
        values = values[:-1]
    return pd.DatetimeIndex(values)


def _current_cut_master_from_historical_panel(market_panel: HistoricalMarketPanel) -> pd.DataFrame:
    """Re-express admitted historical identities in the frozen current-cut schema."""

    security_map = market_panel.security_map.copy()
    if security_map.empty:
        raise ValueError("aov0_historical_current_cut_security_map_empty")
    out = pd.DataFrame(
        {
            "SP_ENTITY_ID": security_map["source_entity_id"].astype(str),
            "SP_SECURITY_ID": security_map["security_id"].astype(str).str.replace(
                r"^CIQSEC:", "", regex=True
            ),
            "SPT_INSTRUMENT_ITEM_ID": security_map["trading_item_id"].astype(str),
            "Primary Security Flag": "Yes",
            "Ticker": security_map.get("ticker", pd.Series("", index=security_map.index)).astype(str),
            "Exchange": security_map.get("exchange", pd.Series("", index=security_map.index)).astype(str),
            "Description": security_map.get(
                "security_type", pd.Series("", index=security_map.index)
            ).astype(str),
        }
    )
    return out.reset_index(drop=True)


def _current_cut_market_from_historical_panel(
    market_panel: HistoricalMarketPanel,
    *,
    decision_date: pd.Timestamp,
) -> pd.DataFrame:
    """Re-express normalized market rows without changing their economic values."""

    market = market_panel.frame.loc[
        pd.to_datetime(market_panel.frame["date"], errors="raise").dt.normalize().le(decision_date)
    ].copy()
    if market.empty:
        raise ValueError("aov0_historical_current_cut_market_empty")
    return pd.DataFrame(
        {
            "SPT_DATE": market["date"],
            "SP_SECURITY_ID": market["security_id"].astype(str).str.replace(
                r"^CIQSEC:", "", regex=True
            ),
            "SPT_INSTRUMENT_ITEM_ID": market["trading_item_id"].astype(str),
            "SPT_CLOSE": pd.to_numeric(market["close"], errors="coerce"),
            "SPT_VOLUME": pd.to_numeric(market["volume"], errors="coerce"),
            "DAILY_TOTAL_RETURN_DECIMAL": pd.to_numeric(
                market["total_return"], errors="coerce"
            ),
        }
    )


def _build_historical_current_cut(
    *,
    market_panel: HistoricalMarketPanel,
    factor_state: pd.DataFrame,
    decision_date: pd.Timestamp,
    activation_date: pd.Timestamp,
) -> tuple[object, VerticalCube]:
    """Run one historical weekly cut through the exact frozen current builder.

    Historical SPG rows are conservatively known after the as-of day.  Their
    target is not active until the next observed close, so we prove the true
    factor knowledge time precedes that activation.  The current-cut builder's
    same-calendar-day guard is then supplied a gate-only timestamp on the
    decision date; emitted ``known_at`` remains the true historical timestamp
    via ``admission_time``.
    """

    state = factor_state.copy().reset_index(drop=True)
    if state.empty or state["source_entity_id"].astype(str).duplicated().any():
        raise ValueError("aov0_historical_current_cut_factor_state_invalid")
    actual_known = pd.to_datetime(state["known_at"], utc=True, errors="raise").max()
    activation_close = _market_known_at(activation_date)
    if actual_known > activation_close:
        raise ValueError("aov0_historical_factor_not_known_before_activation")

    gate_state = state.copy()
    gate_state["known_at"] = decision_date.tz_localize("UTC") + pd.Timedelta(
        hours=23, minutes=59, seconds=59
    )
    current_cut = build_ciq_market_slice(
        security_master_raw=_current_cut_master_from_historical_panel(market_panel),
        market_raw=_current_cut_market_from_historical_panel(
            market_panel, decision_date=decision_date
        ),
        fundamental_state=gate_state,
        admission_time=actual_known.to_pydatetime(),
        target_date=decision_date,
    )
    computed_at = pd.to_datetime(
        current_cut.market_features["known_at"], utc=True, errors="raise"
    ).max()
    cube = build_vertical_cube(
        current_cut.market_features,
        computed_at=computed_at.isoformat(),
        contract=DEFAULT_CONTRACT,
    )
    return current_cut, cube


def build_historical_replay_inputs(
    *,
    market_panel: HistoricalMarketPanel,
    factor_states: HistoricalFactorStates,
    evaluation_start: str | pd.Timestamp,
    evaluation_end: str | pd.Timestamp,
    contract: AOV0Contract = DEFAULT_CONTRACT,
    required_security_ids: Sequence[str] | None = None,
) -> HistoricalReplayInputs:
    """Build frozen-AOV decision states with Clock-v3 activation semantics.

    ``evaluation_start`` is the first completed-week *decision* date retained by
    the historical planner.  The decision uses that close plus its historical
    PIT factor snapshot.  Its target becomes active only at the next observed
    market close; because the canonical engine applies the frozen one-bar lag,
    the first credited return begins after that activation close.  Thus no
    return interval whose left endpoint predates Clock-v3 evaluation start can
    enter historical evidence.
    """

    validate_contract(contract)
    decision_start = pd.Timestamp(evaluation_start).normalize()
    end = pd.Timestamp(evaluation_end).normalize()
    if end <= decision_start:
        raise ValueError("aov0_historical_replay_window_invalid")

    market = market_panel.frame.copy()
    market["date"] = pd.to_datetime(market["date"], errors="raise").dt.normalize()
    required_market = (
        "total_return",
        "realized_vol",
        "dollar_volume",
        "adv20",
        "trend_fast",
        "trend_slow",
        "exit_capacity",
        "regime",
        "dist_sma20",
    )
    finite = market[list(required_market)].apply(pd.to_numeric, errors="coerce")
    market["_valid"] = (
        finite.notna().all(axis=1)
        & np.isfinite(finite.fillna(np.nan).to_numpy(dtype=float)).all(axis=1)
        & finite["realized_vol"].gt(0.0)
        & finite["adv20"].gt(0.0)
        & finite["dollar_volume"].ge(0.0)
    )

    start_rows = market.loc[market["date"].eq(decision_start) & market["_valid"]].copy()
    start_ids = sorted(start_rows["security_id"].astype(str).unique().tolist())
    if required_security_ids is None:
        selected_ids = start_ids
    else:
        selected_ids = sorted({str(value) for value in required_security_ids})
        unavailable_at_start = sorted(set(selected_ids) - set(start_ids))
        if unavailable_at_start:
            raise ValueError(
                "aov0_historical_replay_frozen_security_unavailable_at_start:"
                + unavailable_at_start[0]
            )
    if not selected_ids:
        raise ValueError("aov0_historical_replay_no_primary_security_history_at_start")

    selected_market = market.loc[market["security_id"].isin(selected_ids)].copy()
    session_valid_counts = (
        selected_market.loc[selected_market["date"].between(decision_start, end) & selected_market["_valid"]]
        .groupby("date", sort=True)["security_id"]
        .nunique()
    )
    session_calendar = pd.DatetimeIndex(
        session_valid_counts.loc[session_valid_counts.eq(len(selected_ids))].index
    ).normalize()
    session_calendar = validate_historical_session_continuity(session_calendar)
    if len(session_calendar) < 2 or decision_start not in session_calendar:
        raise ValueError("aov0_historical_replay_calendar_too_short")

    # A date with any real market observation but an incomplete frozen security
    # set is a data failure, not a non-trading holiday and never a survivor
    # filter. Dates on which every frozen security is incomplete are omitted as
    # closed-market rows from the observed session calendar.
    any_valid_counts = (
        selected_market.loc[selected_market["date"].between(decision_start, end) & selected_market["_valid"]]
        .groupby("date", sort=True)["security_id"]
        .nunique()
    )
    partial_dates = any_valid_counts.loc[any_valid_counts.between(1, len(selected_ids) - 1)].index
    if len(partial_dates):
        raise ValueError(
            "aov0_historical_replay_partial_market_session:"
            + pd.Timestamp(partial_dates[0]).date().isoformat()
        )

    decision_candidates = completed_week_decision_dates(session_calendar)
    decision_candidates = decision_candidates[
        (decision_candidates >= decision_start) & (decision_candidates <= end)
    ]
    if len(decision_candidates) == 0 or decision_candidates[0] != decision_start:
        raise ValueError("aov0_historical_replay_start_must_be_completed_week_decision")

    decision_to_activation: dict[pd.Timestamp, pd.Timestamp] = {}
    for decision_date in decision_candidates:
        later = session_calendar[session_calendar > pd.Timestamp(decision_date)]
        if len(later):
            decision_to_activation[pd.Timestamp(decision_date)] = pd.Timestamp(later[0])
    if not decision_to_activation:
        raise ValueError("aov0_historical_replay_no_activatable_decision")
    decision_dates = pd.DatetimeIndex(list(decision_to_activation)).normalize()
    activation_dates = pd.DatetimeIndex(list(decision_to_activation.values())).normalize()
    first_activation = pd.Timestamp(activation_dates[0])
    evaluation_calendar = session_calendar[session_calendar >= first_activation]
    if len(evaluation_calendar) < 2:
        raise ValueError("aov0_historical_replay_evaluation_calendar_too_short")

    available_snapshots = set(pd.DatetimeIndex(factor_states.snapshot_dates).normalize())
    missing_snapshots = [date for date in decision_dates if date not in available_snapshots]
    if missing_snapshots:
        raise ValueError(
            "aov0_historical_replay_missing_weekly_pit_snapshot:"
            + missing_snapshots[0].date().isoformat()
        )

    # Never choose the security set using future completeness. The A1 set is
    # fixed from information available on the first decision date; A2 receives
    # that frozen set explicitly. Any later incomplete observed session blocks.
    in_evaluation = selected_market.loc[selected_market["date"].isin(evaluation_calendar)].copy()
    full_counts = in_evaluation.groupby("security_id")["date"].nunique()
    valid_counts = in_evaluation.loc[in_evaluation["_valid"]].groupby("security_id")["date"].nunique()
    for security_id in selected_ids:
        if (
            int(full_counts.get(security_id, 0)) != len(evaluation_calendar)
            or int(valid_counts.get(security_id, 0)) != len(evaluation_calendar)
        ):
            raise ValueError(f"aov0_historical_replay_post_start_market_gap:{security_id}")
    complete_ids = selected_ids

    security_map = market_panel.security_map.loc[
        market_panel.security_map["security_id"].isin(complete_ids)
    ].copy()
    entity_by_security = dict(
        zip(security_map["security_id"].astype(str), security_map["source_entity_id"].astype(str))
    )
    if len(entity_by_security) != len(complete_ids):
        raise ValueError("aov0_historical_replay_security_entity_map_incomplete")

    factor = factor_states.frame.copy()
    factor["as_of_date"] = pd.to_datetime(factor["as_of_date"], errors="raise").dt.normalize()
    factor_by_date = {
        date: group.set_index("source_entity_id", drop=False)
        for date, group in factor.groupby("as_of_date", sort=True)
    }

    # Every historical decision is rebuilt through the exact current-cut market
    # path.  This eliminates a second implementation of Q/U, technical state,
    # date-local eligibility, exit capacity, regime, and Rule100 softmax sizing.
    # Each resulting cube target is then frozen until its next-session activation.
    target_rows: dict[pd.Timestamp, pd.Series] = {}
    primitive_rows: list[pd.DataFrame] = []
    decision_cube_rows: list[pd.DataFrame] = []
    decision_eligible: dict[pd.Timestamp, tuple[str, ...]] = {}
    selected_market = selected_market.sort_values(["date", "security_id"]).reset_index(drop=True)

    for date in decision_dates:
        decision = pd.Timestamp(date).normalize()
        activation = pd.Timestamp(decision_to_activation[decision]).normalize()
        state = factor_by_date[decision].reset_index(drop=True)
        current_cut, decision_cube = _build_historical_current_cut(
            market_panel=HistoricalMarketPanel(
                security_map=security_map,
                frame=selected_market.drop(columns=["_valid"], errors="ignore"),
                mapping_exclusions=market_panel.mapping_exclusions,
            ),
            factor_state=state,
            decision_date=decision,
            activation_date=activation,
        )
        active_security_ids = tuple(sorted(current_cut.rule100_targets.columns.astype(str).tolist()))
        if not active_security_ids:
            raise ValueError("aov0_historical_replay_date_local_eligible_universe_empty")
        unknown_active = sorted(set(active_security_ids) - set(complete_ids))
        if unknown_active:
            raise ValueError(
                "aov0_historical_replay_current_cut_security_outside_frozen_set:"
                + unknown_active[0]
            )
        decision_eligible[decision] = active_security_ids

        row = pd.Series(0.0, index=complete_ids, dtype=float)
        source_weights = current_cut.rule100_targets.loc[decision].astype(float)
        row.loc[source_weights.index.astype(str)] = source_weights.to_numpy(dtype=float)
        target_rows[decision] = row

        target_primitives = current_cut.market_features.loc[
            pd.to_datetime(current_cut.market_features["date"]).dt.normalize().eq(decision)
        ].copy()
        if set(target_primitives["security_id"].astype(str)) != set(active_security_ids):
            raise ValueError("aov0_historical_replay_current_cut_primitive_identity_drift")
        target_primitives["decision_date"] = decision
        target_primitives["activation_date"] = activation
        primitive_rows.append(target_primitives)

        target_cube = decision_cube.frame.loc[
            pd.to_datetime(decision_cube.frame["date"]).dt.normalize().eq(decision)
        ].copy()
        if set(target_cube["security_id"].astype(str)) != set(active_security_ids):
            raise ValueError("aov0_historical_replay_current_cut_cube_identity_drift")
        decision_cube_rows.append(target_cube)

    decisions = pd.DataFrame(target_rows).T.reindex(index=decision_dates, columns=complete_ids).astype(float)
    if decisions.isna().any().any():
        raise ValueError("aov0_historical_replay_decision_target_missing")
    decisions.index.name = "date"

    activation_rows = pd.DataFrame(
        [decisions.loc[decision_date].to_dict() for decision_date in decision_dates],
        index=activation_dates,
        columns=complete_ids,
        dtype=float,
    )
    activation_rows.index.name = "date"
    targets = activation_rows.reindex(evaluation_calendar).ffill()
    if targets.iloc[0].isna().any():
        raise ValueError("aov0_historical_replay_initial_target_missing")
    targets = targets.fillna(0.0)
    targets.index.name = "date"

    primitives = pd.concat(primitive_rows, ignore_index=True, sort=False)
    primitives = primitives.sort_values(["date", "security_id"]).reset_index(drop=True)
    cube = activate_decision_cube_states(
        pd.concat(decision_cube_rows, ignore_index=True, sort=False),
        decision_to_activation=decision_to_activation,
        evaluation_calendar=evaluation_calendar,
        security_ids=complete_ids,
        contract=contract,
    )

    evaluation_market = selected_market.loc[selected_market["date"].isin(evaluation_calendar)].copy()
    returns = evaluation_market.pivot(
        index="date", columns="security_id", values="total_return"
    ).reindex(index=evaluation_calendar, columns=complete_ids)
    returns.index.name = "date"
    if returns.isna().any().any() or not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("aov0_historical_replay_returns_not_complete")

    activation_to_decision = {
        pd.Timestamp(activation).normalize(): pd.Timestamp(decision).normalize()
        for decision, activation in decision_to_activation.items()
    }
    eligible: dict[pd.Timestamp, tuple[str, ...]] = {}
    active_decision: pd.Timestamp | None = None
    for date in evaluation_calendar:
        day = pd.Timestamp(date).normalize()
        if day in activation_to_decision:
            active_decision = activation_to_decision[day]
        if active_decision is None:
            raise ValueError("aov0_historical_replay_eligibility_not_active")
        eligible[day] = decision_eligible[active_decision]
    metadata: dict[str, object] = {
        "schema_version": HISTORICAL_REPLAY_SCHEMA,
        "evidence_authority": "HISTORICAL_ONLY_FINANCIAL_ALPHA_EVIDENCE_ZERO",
        "contract_hash": contract.contract_hash,
        "decision_start": decision_start.date().isoformat(),
        "evaluation_start": first_activation.date().isoformat(),
        "evaluation_end": end.date().isoformat(),
        "clock_v3_activation_policy": "DECISION_CLOSE_TO_NEXT_OBSERVED_CLOSE_THEN_ENGINE_ONE_BAR_LAG",
        "first_credited_return_left_endpoint": first_activation.date().isoformat(),
        "trading_days": int(len(evaluation_calendar)),
        "weekly_decision_count": int(len(decision_dates)),
        "primary_security_count": int(len(complete_ids)),
        "primitive_start": pd.Timestamp(decision_dates[0]).date().isoformat(),
        "primitive_end": pd.Timestamp(decision_dates[-1]).date().isoformat(),
        "decision_state_builder": "research.aov0.ciq_market.build_ciq_market_slice",
        "decision_cube_activation": "DECISION_CUT_STATE_FROZEN_TO_NEXT_OBSERVED_CLOSE",
        "date_local_eligible_universe": True,
        "fixed_source_cohort": True,
        "fixed_source_cohort_limitation": "CURRENT_FROZEN_109_COMPANY_SOURCE_COHORT_NOT_HISTORICAL_SCREEN_MEMBERSHIP",
        "factor_pit_mode": HISTORICAL_PIT_MODE,
        "market_authority": "SPCIQPRO_PRIMARY_SECURITY_MARKET_DATA",
        "financial_alpha_evidence": 0,
    }
    return HistoricalReplayInputs(
        decision_rule100_weights=decisions,
        rule100_weights=targets,
        total_returns=returns,
        primitives=primitives,
        cube=cube,
        eligible_by_date=eligible,
        decision_dates=decision_dates,
        activation_dates=activation_dates,
        decision_to_activation=decision_to_activation,
        security_ids=tuple(complete_ids),
        metadata=metadata,
    )


def activate_decision_targets(
    decision_targets: pd.DataFrame,
    replay: HistoricalReplayInputs,
) -> pd.DataFrame:
    """Map sealed decision-date target vectors to Clock-v3 activation closes."""

    if not isinstance(decision_targets, pd.DataFrame) or decision_targets.empty:
        raise ValueError("aov0_historical_activation_targets_required")
    source = decision_targets.copy().astype(float)
    source.index = pd.DatetimeIndex(source.index).normalize()
    expected_dates = pd.DatetimeIndex(replay.decision_dates).normalize()
    expected_columns = list(replay.security_ids)
    if not source.index.equals(expected_dates):
        raise ValueError("aov0_historical_activation_decision_calendar_mismatch")
    if list(source.columns.astype(str)) != expected_columns:
        raise ValueError("aov0_historical_activation_security_set_mismatch")
    if source.isna().any().any() or not np.isfinite(source.to_numpy(dtype=float)).all():
        raise ValueError("aov0_historical_activation_target_nonfinite")

    activation_rows = pd.DataFrame(
        [source.loc[decision_date].to_dict() for decision_date in expected_dates],
        index=pd.DatetimeIndex(replay.activation_dates).normalize(),
        columns=expected_columns,
        dtype=float,
    )
    activation_rows.index.name = "date"
    evaluation_calendar = pd.DatetimeIndex(replay.total_returns.index).normalize()
    activated = activation_rows.reindex(evaluation_calendar).ffill()
    if activated.empty or activated.iloc[0].isna().any():
        raise ValueError("aov0_historical_activation_initial_target_missing")
    if activated.isna().any().any() or not np.isfinite(activated.to_numpy(dtype=float)).all():
        raise ValueError("aov0_historical_activation_target_nonfinite")
    activated.index.name = "date"
    return activated


def historical_cash_from_official_sofr_rows(
    target_dates: Sequence[object],
    official_sofr_rows: pd.DataFrame,
) -> pd.Series:
    """Conservative historical official-SOFR cash comparator.

    NY Fed historical search rows expose the effective date but not a retained
    per-row publication timestamp. To prevent any look-ahead, this historical
    comparator uses only an official SOFR whose *effective date strictly
    precedes* the return interval start. This is deliberately more conservative
    than same-day use and never substitutes a proxy.
    """

    dates = pd.DatetimeIndex(pd.to_datetime(list(target_dates))).normalize()
    rows = official_sofr_rows.copy()
    effective_col = "effective_date" if "effective_date" in rows.columns else "effectiveDate"
    rate_col = "sofr_percent" if "sofr_percent" in rows.columns else "percentRate"
    if effective_col not in rows.columns or rate_col not in rows.columns:
        raise ValueError("aov0_historical_sofr_required_columns_missing")
    rows["effective_date"] = pd.to_datetime(rows[effective_col], errors="raise").dt.normalize()
    rows["sofr_percent"] = pd.to_numeric(rows[rate_col], errors="coerce")
    rows = rows.dropna(subset=["effective_date", "sofr_percent"]).sort_values("effective_date")
    rows = rows.drop_duplicates("effective_date", keep="last")
    if rows.empty:
        raise ValueError("aov0_historical_sofr_empty")
    out = pd.Series(0.0, index=dates, name="economic_cash", dtype=float)
    for index in range(1, len(dates)):
        interval_start = dates[index - 1]
        interval_end = dates[index]
        eligible = rows.loc[rows["effective_date"] < interval_start]
        if eligible.empty:
            raise ValueError(f"aov0_historical_sofr_unavailable:{interval_start.date().isoformat()}")
        annual_rate = float(eligible.iloc[-1]["sofr_percent"]) / 100.0 - 0.0025
        out.iloc[index] = annual_rate * float((interval_end - interval_start).days) / 360.0
    return out


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
