"""Current-cut Capital IQ security/market admission for the first AOV-0 seal.

This module is intentionally narrow. It maps the frozen company entities to one
canonical Capital IQ primary security/trading item, admits same-cut daily market
history, derives only the market features required by Rule100/AOV-0, and emits
current-decision inputs. Ambiguous identities and insufficient observations are
excluded rather than repaired through compatibility fallbacks.

The frozen ``run_4`` fundamental state is admission-time-only. Accordingly this
module does *not* manufacture historical PIT Rule100 targets from that current
fundamental state. It emits one current Rule100 target row and one matching
current total-return row; historical market rows are used only to construct the
current technical/AOV state (rolling volatility, liquidity, and trend).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
import re
from typing import Any, Iterable
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd

from research.aov0.contracts import normalize_security_id
from research.aov0.ciq_fundamentals import _xlsx_rows
from strategies.rule100_softmax import rule100_config_from_max_weight, softmax_v1_weights


SECURITY_MASTER_SOURCE_ID = "SPCIQPRO:PRIMARY_SECURITY_MASTER"
MARKET_DATA_SOURCE_ID = "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA"
SECURITY_MAP_SCHEMA = "aov0_ciq_primary_security_map_v1"
MARKET_FEATURE_SCHEMA = "aov0_ciq_current_market_features_v1"

# Canonical Rule100 v1 hold/sizing law, mirrored from pit_lifecycle_replay and
# rule100_softmax_v1_audit. Keep tests binding these values to their owner code.
MIN_FACTOR_COVERAGE = 3
MIN_HOLD_FACTOR_POSITIVES = 2
HARD_EXIT_DIST_SMA20 = 0.20
ACCUMULATION_DIST_MAX = 0.05
RULE100_PRODUCT_MAX_WEIGHT = 0.35

ADV_WINDOW = 20
VOL_WINDOW = 20
SMA_FAST_WINDOW = 20
SMA_SLOW_WINDOW = 200
MIN_MARKET_HISTORY_ROWS = SMA_SLOW_WINDOW


@dataclass(frozen=True)
class CiqMarketSlice:
    security_map: pd.DataFrame
    market_features: pd.DataFrame
    rule100_targets: pd.DataFrame
    total_returns: pd.DataFrame
    exclusions: pd.DataFrame
    metadata: dict[str, Any]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _token(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


ENTITY_ALIASES = {
    "SPENTITYID",
    "SOURCEENTITYID",
    "ENTITYID",
    "CAPITALIQENTITYID",
}
SECURITY_ID_ALIASES = {
    "SECURITYID",
    "SPSECURITYID",
    "IQSECURITYID",
    "CIQSECURITYID",
    "CAPITALIQSECURITYID",
}
TRADING_ITEM_ALIASES = {
    "TRADINGITEMID",
    "SPTRADINGITEMID",
    "INSTRUMENTITEMID",
    "SPTINSTRUMENTITEMID",
}
PRIMARY_ALIASES = {
    "PRIMARY",
    "ISPRIMARY",
    "PRIMARYFLAG",
    "PRIMARYSECURITY",
    "PRIMARYSECURITYFLAG",
    "PRIMARYTRADINGITEM",
    "PRIMARYTRADINGITEMFLAG",
}
TICKER_ALIASES = {"TICKER", "SPTICKER", "TRADINGITEMTICKER"}
EXCHANGE_ALIASES = {"EXCHANGE", "SPEXCHANGE", "PRIMARYEXCHANGE"}
TYPE_ALIASES = {"SECURITYTYPE", "INSTRUMENTTYPE", "DESCRIPTION", "SPTDESCRIPTION"}
STATUS_ALIASES = {"STATUS", "SECURITYSTATUS", "TRADINGSTATUS"}
DATE_ALIASES = {"DATE", "PRICEDATE", "MARKETDATE", "SPTDATE"}
RETURN_PERCENT_ALIASES = {
    "TOTALRETURNPERCENT",
    "TOTALRETURNPCT",
    "SPTTOTALRETURN",
}
RETURN_INDEX_ALIASES = {
    "TOTALRETURNINDEX",
    "TOTALRETURNIDX",
    "SPTTOTALRETURNINDEX",
}
RETURN_DECIMAL_ALIASES = {"TOTALRETURNDECIMAL", "DAILYTOTALRETURNDECIMAL"}
ADJ_CLOSE_ALIASES = {"ADJUSTEDCLOSE", "ADJCLOSE", "SPTADJUSTEDCLOSE"}
CLOSE_ALIASES = {"CLOSE", "CLOSINGPRICE", "PRICE", "SPTCLOSE", "SPTPRICE"}
VOLUME_ALIASES = {"VOLUME", "TRADINGVOLUME", "SPTVOLUME"}


def _first_column(frame: pd.DataFrame, aliases: set[str]) -> str | None:
    for column in frame.columns:
        if _token(column) in aliases:
            return str(column)
    return None


def _xlsx_sheet_names(path: Path) -> list[str]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets = workbook.find("m:sheets", ns)
        if sheets is None:
            return []
        return [str(node.attrib.get("name") or "") for node in sheets]


def _rows_to_frame(rows: list[dict[str, str]], alias_groups: Iterable[set[str]]) -> pd.DataFrame:
    groups = list(alias_groups)
    best_index: int | None = None
    best_score = -1
    for index, row in enumerate(rows):
        values = {_token(value) for key, value in row.items() if key != "__row__" and str(value).strip()}
        score = sum(bool(values & aliases) for aliases in groups)
        if score > best_score:
            best_score = score
            best_index = index
    if best_index is None or best_score <= 0:
        return pd.DataFrame()
    header = {column: str(value).strip() for column, value in rows[best_index].items() if column != "__row__"}
    records: list[dict[str, object]] = []
    for row in rows[best_index + 1 :]:
        record = {
            header[column]: value
            for column, value in row.items()
            if column != "__row__" and column in header and header[column]
        }
        if record and any(str(value).strip() for value in record.values()):
            records.append(record)
    return pd.DataFrame(records)


def read_tabular_export(path: str | Path, *, kind: str) -> pd.DataFrame:
    """Read a bounded CSV/Parquet/XLSX CIQ export without adding Excel deps."""
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(source)
    if suffix not in {".xlsx", ".xlsm"}:
        raise ValueError(f"aov0_ciq_export_type_unsupported:{suffix}")

    if kind == "security_master":
        groups = [ENTITY_ALIASES, SECURITY_ID_ALIASES, TRADING_ITEM_ALIASES]
    elif kind == "market":
        groups = [DATE_ALIASES, TRADING_ITEM_ALIASES, RETURN_PERCENT_ALIASES | RETURN_INDEX_ALIASES | RETURN_DECIMAL_ALIASES]
    else:
        raise ValueError(f"aov0_ciq_export_kind_invalid:{kind}")

    best = pd.DataFrame()
    best_score = -1
    for sheet_name in _xlsx_sheet_names(source):
        try:
            frame = _rows_to_frame(_xlsx_rows(source, sheet_name=sheet_name), groups)
        except (KeyError, ValueError, zipfile.BadZipFile):
            continue
        tokens = {_token(column) for column in frame.columns}
        score = sum(bool(tokens & aliases) for aliases in groups)
        if score > best_score:
            best = frame
            best_score = score
    if best.empty:
        raise ValueError(f"aov0_ciq_{kind}_xlsx_table_not_found")
    return best


def _text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _truthy(value: object) -> bool:
    return _token(value) in {"1", "Y", "YES", "TRUE", "PRIMARY", "P"}


def _canonical_security(value: object) -> str | None:
    text = str(value or "").strip()
    if not text or text.upper() in {"NA", "N/A", "NULL", "NONE", "NAN"}:
        return None
    if text.startswith("CIQSEC:"):
        try:
            return normalize_security_id(text)
        except ValueError:
            return None
    try:
        return normalize_security_id(f"CIQSEC:{text}")
    except ValueError:
        return None


def normalize_primary_security_master(
    raw: pd.DataFrame,
    *,
    frozen_entity_ids: set[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    entity_col = _first_column(raw, ENTITY_ALIASES)
    security_col = _first_column(raw, SECURITY_ID_ALIASES)
    trading_col = _first_column(raw, TRADING_ITEM_ALIASES)
    if entity_col is None or security_col is None or trading_col is None:
        raise ValueError("aov0_ciq_security_master_required_identity_columns_missing")

    primary_col = _first_column(raw, PRIMARY_ALIASES)
    optional = {
        "ticker": _first_column(raw, TICKER_ALIASES),
        "exchange": _first_column(raw, EXCHANGE_ALIASES),
        "security_type": _first_column(raw, TYPE_ALIASES),
        "status": _first_column(raw, STATUS_ALIASES),
    }
    work = pd.DataFrame(
        {
            "source_entity_id": _text(raw[entity_col]),
            "raw_security_id": _text(raw[security_col]),
            "trading_item_id": _text(raw[trading_col]),
        }
    )
    for name, column in optional.items():
        work[name] = _text(raw[column]) if column is not None else ""
    work["security_id"] = work["raw_security_id"].map(_canonical_security)
    work["primary_flag"] = raw[primary_col].map(_truthy) if primary_col is not None else False
    work["has_explicit_primary_flag"] = primary_col is not None

    exclusions: list[dict[str, str]] = []
    admitted: list[pd.Series] = []
    for entity_id in sorted(frozen_entity_ids):
        group = work.loc[work["source_entity_id"].eq(entity_id)].copy()
        if group.empty:
            exclusions.append({"source_entity_id": entity_id, "reason": "MISSING_PRIMARY_SECURITY_MAPPING"})
            continue
        if primary_col is not None:
            primary = group.loc[group["primary_flag"]]
            if len(primary) == 1:
                candidate = primary.iloc[0]
            elif len(primary) == 0 and len(group) == 1:
                candidate = group.iloc[0]
            else:
                exclusions.append({"source_entity_id": entity_id, "reason": "AMBIGUOUS_PRIMARY_SECURITY_MAPPING"})
                continue
        elif len(group) == 1:
            candidate = group.iloc[0]
        else:
            exclusions.append({"source_entity_id": entity_id, "reason": "AMBIGUOUS_PRIMARY_SECURITY_MAPPING"})
            continue
        if candidate["security_id"] is None:
            exclusions.append({"source_entity_id": entity_id, "reason": "MISSING_CANONICAL_CIQ_SECURITY_ID"})
            continue
        if not str(candidate["trading_item_id"]).strip():
            exclusions.append({"source_entity_id": entity_id, "reason": "MISSING_TRADING_ITEM_ID"})
            continue
        admitted.append(candidate)

    if admitted:
        result = pd.DataFrame(admitted).reset_index(drop=True)
    else:
        result = pd.DataFrame(columns=list(work.columns))

    # Cross-entity identity collisions are authority defects for the colliding
    # entities; exclude all colliders rather than guessing ownership.
    if not result.empty:
        collision_mask = (
            result.duplicated("security_id", keep=False)
            | result.duplicated("trading_item_id", keep=False)
        )
        if collision_mask.any():
            for entity_id in result.loc[collision_mask, "source_entity_id"].astype(str):
                exclusions.append({"source_entity_id": entity_id, "reason": "CROSS_ENTITY_SECURITY_ID_COLLISION"})
            result = result.loc[~collision_mask].copy()

    result = result[
        [
            "source_entity_id",
            "security_id",
            "trading_item_id",
            "ticker",
            "exchange",
            "security_type",
            "status",
        ]
    ].sort_values("source_entity_id").reset_index(drop=True)
    result["schema_version"] = SECURITY_MAP_SCHEMA
    result["source_id"] = SECURITY_MASTER_SOURCE_ID
    return result, pd.DataFrame(exclusions, columns=["source_entity_id", "reason"])


def _parse_market_raw(raw: pd.DataFrame, security_map: pd.DataFrame) -> pd.DataFrame:
    date_col = _first_column(raw, DATE_ALIASES)
    trading_col = _first_column(raw, TRADING_ITEM_ALIASES)
    security_col = _first_column(raw, SECURITY_ID_ALIASES)
    adj_close_col = _first_column(raw, ADJ_CLOSE_ALIASES)
    close_col = _first_column(raw, CLOSE_ALIASES)
    volume_col = _first_column(raw, VOLUME_ALIASES)
    pct_col = _first_column(raw, RETURN_PERCENT_ALIASES)
    index_col = _first_column(raw, RETURN_INDEX_ALIASES)
    decimal_col = _first_column(raw, RETURN_DECIMAL_ALIASES)

    if date_col is None or trading_col is None or volume_col is None or (adj_close_col is None and close_col is None):
        raise ValueError("aov0_ciq_market_required_columns_missing")
    if pct_col is None and index_col is None and decimal_col is None:
        raise ValueError("aov0_ciq_market_total_return_authority_missing")

    work = pd.DataFrame()
    work["date"] = pd.to_datetime(raw[date_col], errors="coerce").dt.normalize()
    work["trading_item_id"] = _text(raw[trading_col])
    if security_col is not None:
        work["security_id"] = raw[security_col].map(_canonical_security)
    else:
        work["security_id"] = None
    price_source = adj_close_col if adj_close_col is not None else close_col
    work["close"] = pd.to_numeric(raw[price_source], errors="coerce")
    work["volume"] = pd.to_numeric(raw[volume_col], errors="coerce")

    if decimal_col is not None:
        work["total_return"] = pd.to_numeric(raw[decimal_col], errors="coerce")
        return_mode = "EXPLICIT_DECIMAL_TOTAL_RETURN"
    elif pct_col is not None:
        work["total_return"] = pd.to_numeric(raw[pct_col], errors="coerce") / 100.0
        return_mode = "CAPITAL_IQ_PERCENT_TOTAL_RETURN_DIV100"
    else:
        work["total_return_index"] = pd.to_numeric(raw[index_col], errors="coerce")
        return_mode = "TOTAL_RETURN_INDEX_PCT_CHANGE"

    pair_map = security_map[["security_id", "trading_item_id", "source_entity_id"]].copy()
    by_trading = dict(zip(pair_map["trading_item_id"].astype(str), pair_map["security_id"].astype(str)))
    work["security_id"] = work["security_id"].where(
        work["security_id"].notna(), work["trading_item_id"].map(by_trading)
    )
    work = work.merge(pair_map, on=["security_id", "trading_item_id"], how="inner", validate="many_to_one")
    work = work.dropna(subset=["date"]).sort_values(["security_id", "date"]).reset_index(drop=True)
    if work.duplicated(["date", "security_id"]).any():
        raise ValueError("aov0_ciq_market_duplicate_date_security")
    if return_mode == "TOTAL_RETURN_INDEX_PCT_CHANGE":
        work["total_return"] = work.groupby("security_id", sort=False)["total_return_index"].pct_change(fill_method=None)
    work["return_mode"] = return_mode
    return work


def _derive_market_features(
    market: pd.DataFrame,
    fundamentals: pd.DataFrame,
    *,
    admission_time: datetime,
) -> pd.DataFrame:
    out = market.sort_values(["security_id", "date"]).copy()
    out["dollar_volume"] = out["close"] * out["volume"]
    grouped = out.groupby("security_id", sort=False)
    out["adv20"] = (
        grouped["dollar_volume"].rolling(ADV_WINDOW, min_periods=ADV_WINDOW).mean().reset_index(level=0, drop=True)
    )
    out["realized_vol"] = (
        grouped["total_return"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std().reset_index(level=0, drop=True)
        * np.sqrt(252.0)
    )
    out["sma20"] = grouped["close"].rolling(SMA_FAST_WINDOW, min_periods=SMA_FAST_WINDOW).mean().reset_index(level=0, drop=True)
    out["sma200"] = grouped["close"].rolling(SMA_SLOW_WINDOW, min_periods=SMA_SLOW_WINDOW).mean().reset_index(level=0, drop=True)
    out["dist_sma20"] = (out["close"] - out["sma20"]) / out["sma20"].replace(0.0, np.nan)
    out["trend_veto"] = out["close"].lt(out["sma200"]).where(out["sma200"].notna())
    out["trend_fast"] = np.where(out["sma20"].notna(), np.where(out["close"] >= out["sma20"], 1.0, -1.0), np.nan)
    out["trend_slow"] = np.where(out["sma200"].notna(), np.where(out["close"] >= out["sma200"], 1.0, -1.0), np.nan)

    fundamental_cols = [
        "source_entity_id",
        "factor_present_count",
        "factor_positive_count",
    ]
    factor = fundamentals[fundamental_cols].copy()
    out = out.merge(factor, on="source_entity_id", how="left", validate="many_to_one")
    present = pd.to_numeric(out["factor_present_count"], errors="coerce").fillna(0.0)
    positive = pd.to_numeric(out["factor_positive_count"], errors="coerce").fillna(0.0)
    strength = np.where(present > 0, positive / present, 0.0)
    # Q is deliberately a monotone transform of the already-frozen Rule100
    # group counts, avoiding a second quality model. cube.py later maps [-3,3]
    # to [-1,1].
    out["quality"] = np.clip(3.0 * (2.0 * strength - 1.0), -3.0, 3.0)
    out["uncertainty"] = np.clip(1.0 - present / 4.0, 0.0, 1.0)
    out["valid_at"] = pd.to_datetime(out["date"], errors="raise", utc=True)
    admitted = pd.Timestamp(admission_time)
    admitted = admitted.tz_localize("UTC") if admitted.tzinfo is None else admitted.tz_convert("UTC")
    out["known_at"] = admitted
    return out


def _append_exclusions(
    exclusions: list[dict[str, str]],
    entity_ids: Iterable[object],
    reason: str,
) -> None:
    for entity_id in sorted({str(value) for value in entity_ids}):
        exclusions.append({"source_entity_id": entity_id, "reason": reason})


def build_ciq_market_slice(
    *,
    security_master_raw: pd.DataFrame,
    market_raw: pd.DataFrame,
    fundamental_state: pd.DataFrame,
    admission_time: datetime | None = None,
    target_date: str | pd.Timestamp | None = None,
) -> CiqMarketSlice:
    admitted = (admission_time or datetime.now(UTC)).astimezone(UTC)
    fundamentals = fundamental_state.copy()
    fundamentals["source_entity_id"] = _text(fundamentals["source_entity_id"])
    frozen_ids = set(fundamentals["source_entity_id"])

    security_map, mapping_exclusions = normalize_primary_security_master(
        security_master_raw,
        frozen_entity_ids=frozen_ids,
    )
    exclusions: list[dict[str, str]] = mapping_exclusions.to_dict("records")

    coverage_ok = pd.to_numeric(fundamentals["factor_present_count"], errors="coerce").fillna(0).ge(MIN_FACTOR_COVERAGE)
    coverage_ids = set(fundamentals.loc[coverage_ok, "source_entity_id"].astype(str))
    insufficient = set(fundamentals.loc[~coverage_ok, "source_entity_id"].astype(str))
    _append_exclusions(exclusions, insufficient, "INSUFFICIENT_FACTOR_COVERAGE")
    security_map = security_map.loc[security_map["source_entity_id"].isin(coverage_ids)].copy()
    if security_map.empty:
        raise ValueError("aov0_ciq_no_entities_after_identity_and_factor_coverage")

    market = _parse_market_raw(market_raw, security_map)
    market_ids = set(market["source_entity_id"].astype(str))
    missing_market = set(security_map["source_entity_id"].astype(str)) - market_ids
    _append_exclusions(exclusions, missing_market, "MISSING_CANONICAL_MARKET_HISTORY")
    security_map = security_map.loc[security_map["source_entity_id"].isin(market_ids)].copy()
    market = market.loc[market["source_entity_id"].isin(set(security_map["source_entity_id"]))].copy()

    features = _derive_market_features(market, fundamentals, admission_time=admitted)
    if target_date is None:
        decision_date = pd.Timestamp(features["date"].max()).normalize()
    else:
        decision_date = pd.Timestamp(target_date).normalize()
    fundamental_known = pd.to_datetime(fundamentals["known_at"], utc=True, errors="coerce")
    if fundamental_known.notna().any():
        first_admissible_date = fundamental_known.max().tz_convert("UTC").tz_localize(None).normalize()
        if decision_date < first_admissible_date:
            raise ValueError("aov0_ciq_target_date_before_fundamental_admission")

    # The fundamental leg is current-cut-only. Historical market rows exist
    # solely to warm F/C, volatility, liquidity and trend state. They must not
    # carry today's factor state backward in time, even if those fields are not
    # used by the one-row current policy. Represent pre-target factor authority
    # explicitly as unknown: neutral Q, maximum U, no counts, no eligibility.
    warmup_mask = features["date"].lt(decision_date)
    features.loc[warmup_mask, "quality"] = 0.0
    features.loc[warmup_mask, "uncertainty"] = 1.0
    features.loc[warmup_mask, ["factor_present_count", "factor_positive_count"]] = np.nan

    # Require a current row and enough observations to support SMA200. Names
    # that fail are excluded rather than backfilled from alternate identities.
    counts = features.loc[features["date"].le(decision_date)].groupby("source_entity_id")["close"].count()
    current = features.loc[features["date"].eq(decision_date)].copy()
    current_ids = set(current["source_entity_id"].astype(str))
    insufficient_history = {
        entity_id
        for entity_id in set(security_map["source_entity_id"].astype(str))
        if int(counts.get(entity_id, 0)) < MIN_MARKET_HISTORY_ROWS or entity_id not in current_ids
    }
    _append_exclusions(exclusions, insufficient_history, "INSUFFICIENT_MARKET_HISTORY_OR_TARGET_ROW")
    final_ids = set(security_map["source_entity_id"].astype(str)) - insufficient_history
    security_map = security_map.loc[security_map["source_entity_id"].isin(final_ids)].copy()
    features = features.loc[features["source_entity_id"].isin(final_ids) & features["date"].le(decision_date)].copy()
    current = features.loc[features["date"].eq(decision_date)].copy()

    required_target_numeric = ["total_return", "close", "volume", "adv20", "realized_vol", "dist_sma20", "trend_fast", "trend_slow", "quality"]
    bad_target = current[required_target_numeric].apply(pd.to_numeric, errors="coerce").isna().any(axis=1)
    bad_target |= ~np.isfinite(current[required_target_numeric].apply(pd.to_numeric, errors="coerce").fillna(np.nan).to_numpy(dtype=float)).all(axis=1)
    bad_target |= pd.to_numeric(current["realized_vol"], errors="coerce").le(0)
    bad_target |= pd.to_numeric(current["adv20"], errors="coerce").le(0)
    bad_ids = set(current.loc[bad_target, "source_entity_id"].astype(str))
    _append_exclusions(exclusions, bad_ids, "NONFINITE_OR_INVALID_TARGET_MARKET_STATE")
    final_ids -= bad_ids
    if not final_ids:
        raise ValueError("aov0_ciq_no_entities_after_market_integrity_filters")
    security_map = security_map.loc[security_map["source_entity_id"].isin(final_ids)].copy()
    features = features.loc[features["source_entity_id"].isin(final_ids)].copy()

    # L and R are purely mechanical date-local market state. L is relative
    # exit capacity from ADV20 rank; R is the date-local slow-trend breadth.
    features["exit_capacity"] = features.groupby("date", sort=False)["adv20"].rank(pct=True, method="average")
    regime_by_date = features.groupby("date", sort=False)["trend_slow"].mean().clip(-1.0, 1.0)
    features["regime"] = features["date"].map(regime_by_date)

    present = pd.to_numeric(features["factor_present_count"], errors="coerce").fillna(0)
    positive = pd.to_numeric(features["factor_positive_count"], errors="coerce").fillna(0)
    hold_intact = present.ge(MIN_FACTOR_COVERAGE) & positive.ge(MIN_HOLD_FACTOR_POSITIVES)
    trend_veto = features["trend_veto"].astype("boolean").fillna(True).astype(bool)
    dist = pd.to_numeric(features["dist_sma20"], errors="coerce")
    hard_exit = trend_veto | dist.gt(HARD_EXIT_DIST_SMA20)
    proximity = (1.0 - dist.clip(lower=0.0) / ACCUMULATION_DIST_MAX).clip(0.0, 1.0)
    hold_confirmed = hold_intact & ~hard_exit
    features["technical_quality"] = np.where(
        hold_confirmed,
        1.0,
        proximity.where(~trend_veto & dist.notna(), 0.0),
    ).astype(float)
    features["sizing_eligible"] = hold_confirmed.astype(bool)

    # Keep only rows that can enter build_vertical_cube; early warmup rows are
    # source history but not vertical primitives.
    primitive_numeric = [
        "total_return",
        "realized_vol",
        "dollar_volume",
        "adv20",
        "quality",
        "trend_fast",
        "trend_slow",
        "exit_capacity",
        "regime",
        "uncertainty",
    ]
    numeric = features[primitive_numeric].apply(pd.to_numeric, errors="coerce")
    primitive_mask = numeric.notna().all(axis=1) & np.isfinite(numeric.fillna(np.nan).to_numpy(dtype=float)).all(axis=1)
    primitive_mask &= numeric["realized_vol"].gt(0) & numeric["adv20"].gt(0) & numeric["dollar_volume"].ge(0)
    primitives = features.loc[primitive_mask].copy()
    target_primitive_ids = set(primitives.loc[primitives["date"].eq(decision_date), "source_entity_id"].astype(str))
    missing_target_primitive = final_ids - target_primitive_ids
    if missing_target_primitive:
        _append_exclusions(exclusions, missing_target_primitive, "TARGET_VERTICAL_PRIMITIVE_UNAVAILABLE")
        final_ids -= missing_target_primitive
        security_map = security_map.loc[security_map["source_entity_id"].isin(final_ids)].copy()
        primitives = primitives.loc[primitives["source_entity_id"].isin(final_ids)].copy()
    if not final_ids:
        raise ValueError("aov0_ciq_no_entities_with_target_vertical_primitives")

    target = primitives.loc[primitives["date"].eq(decision_date)].copy().sort_values("security_id")
    target = target.drop_duplicates("security_id", keep="last")
    target_indexed = target.set_index("security_id", drop=False)
    target_weights = pd.Series(0.0, index=target_indexed.index, dtype=float)
    eligible = target_indexed.loc[target_indexed["sizing_eligible"].astype(bool)].copy()
    if not eligible.empty:
        cfg = rule100_config_from_max_weight(RULE100_PRODUCT_MAX_WEIGHT)
        target_weights.loc[eligible.index] = softmax_v1_weights(eligible, cfg).astype(float)

    rule100_targets = pd.DataFrame(
        [target_weights.to_dict()],
        index=pd.DatetimeIndex([decision_date]),
    ).sort_index(axis=1)
    rule100_targets.index.name = "date"

    current_returns = target_indexed["total_return"].astype(float).reindex(rule100_targets.columns)
    total_returns = pd.DataFrame(
        [current_returns.to_dict()],
        index=pd.DatetimeIndex([decision_date]),
    ).sort_index(axis=1)
    total_returns.index.name = "date"

    primitives = primitives[
        [
            "date",
            "security_id",
            "trading_item_id",
            "source_entity_id",
            "valid_at",
            "known_at",
            "total_return",
            "realized_vol",
            "dollar_volume",
            "adv20",
            "quality",
            "trend_fast",
            "trend_slow",
            "exit_capacity",
            "regime",
            "uncertainty",
            "close",
            "volume",
            "dist_sma20",
            "trend_veto",
            "technical_quality",
            "factor_present_count",
            "factor_positive_count",
            "sizing_eligible",
            "return_mode",
        ]
    ].sort_values(["date", "security_id"]).reset_index(drop=True)
    primitives["schema_version"] = MARKET_FEATURE_SCHEMA
    primitives["source_id"] = MARKET_DATA_SOURCE_ID

    security_map = security_map.loc[security_map["source_entity_id"].isin(final_ids)].sort_values("source_entity_id").reset_index(drop=True)
    exclusion_frame = pd.DataFrame(exclusions, columns=["source_entity_id", "reason"]).drop_duplicates().sort_values(["source_entity_id", "reason"]).reset_index(drop=True)
    metadata = {
        "decision_target_date": decision_date.date().isoformat(),
        "frozen_entity_count": int(len(frozen_ids)),
        "canonical_security_count": int(len(security_map)),
        "excluded_entity_count": int(len(frozen_ids - set(security_map["source_entity_id"].astype(str)))),
        "rule100_sizing_eligible_count": int(target["sizing_eligible"].astype(bool).sum()),
        "rule100_risky_gross": float(rule100_targets.iloc[0].sum()),
        "rule100_max_weight": float(rule100_targets.iloc[0].max()) if not rule100_targets.empty else 0.0,
        "primitive_rows": int(len(primitives)),
        "primitive_min_date": pd.Timestamp(primitives["date"].min()).date().isoformat(),
        "primitive_max_date": pd.Timestamp(primitives["date"].max()).date().isoformat(),
        "admission_time_utc": admitted.isoformat().replace("+00:00", "Z"),
        "formula_contract": {
            "factor_coverage": "factor_present_count>=3",
            "hold_intact": "factor_present_count>=3 and factor_positive_count>=2",
            "technical_quality": "1 if hold_intact and not trend_veto and dist_sma20<=0.20 else max(0,1-max(dist_sma20,0)/0.05) when not veto",
            "rule100_control": "strategies.rule100_softmax.softmax_v1_weights(rule100_config_from_max_weight(0.35))",
            "realized_vol": "rolling20_std(daily_total_return)*sqrt(252)",
            "dollar_volume": "close*volume",
            "adv20": "rolling20_mean(dollar_volume)",
            "trend_fast": "sign(close-sma20)",
            "trend_slow": "sign(close-sma200)",
            "quality": "target_date: clip(3*(2*(factor_positive_count/factor_present_count)-1),-3,3); warmup: 0",
            "exit_capacity": "date_local_percentile_rank(adv20)",
            "regime": "date_local_mean(trend_slow)",
            "uncertainty": "target_date: clip(1-factor_present_count/4,0,1); warmup: 1",
        },
        "historical_rule100_targets_emitted": False,
        "current_cut_only": True,
    }
    return CiqMarketSlice(
        security_map=security_map,
        market_features=primitives,
        rule100_targets=rule100_targets,
        total_returns=total_returns,
        exclusions=exclusion_frame,
        metadata=metadata,
    )
