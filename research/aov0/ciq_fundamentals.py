"""Bounded Capital IQ quarterly-fundamental slice for AOV-0.

The output remains company-entity keyed. It MUST NOT be treated as permanent
security identity, market authority, historical PIT replay proof, or a final
first-seal input.
"""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
import pandas as pd

from data.feature_specs import build_default_feature_specs, compute_registry_hash
from data.feature_store import CS_SCALE_ROBUST, _cross_sectional_scale
from strategies.rule100_softmax_v1_1 import V1_1_FACTOR_GROUPS, compute_factor_group_counts

SOURCE_ID = "SPCIQPRO:QUARTERLY_FUNDAMENTALS"
PANEL_SCHEMA = "aov0_ciq_entity_quarterly_panel_v1"
STATE_SCHEMA = "aov0_ciq_entity_fundamental_state_v1"
IDENTITY_STATUS = "TEMPORARY_COMPANY_ENTITY_NOT_SECURITY"
PIT_MODE = "ADMISSION_TIME_ONLY_NO_HISTORICAL_PUBLICATION_TIMESTAMPS"

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

_METRICS = {
    "IQ_TOTAL_REV": "total_revenue_q",
    "IQ_TOTAL_ASSETS": "total_assets_q",
    "IQ_INVENTORY": "inventory_q",
    "IQ_DA_SUPPL_CF": "depreciation_q",
    "IQ_TOTAL_EQUITY": "equity_q",
    "IQ_CURRENT_DEBT_EXCL_OPER_LEASES": "current_debt_q",
    "IQ_TOTAL_LIAB": "total_liabilities_q",
    "IQ_TOTAL_DEBT": "total_debt_q",
    "IQ_CASH_ST_INVEST": "cash_q",
    "IQ_OPER_INC": "operating_income_q",
    "IQ_CAPEX_BNK": "capex_q",
}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _excel_date(value: object) -> pd.Timestamp:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return pd.NaT
    return (pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(numeric))).normalize()


def _xlsx_rows(path: str | Path, sheet_name: str = "Sheet1") -> list[dict[str, str]]:
    """Read an XLSX sheet without adding an Excel-engine dependency."""
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = [
                "".join(t.text or "" for t in item.findall(".//m:t", _NS))
                for item in root.findall("m:si", _NS)
            ]

        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {node.attrib["Id"]: node.attrib["Target"] for node in rels}
        target = None
        sheets = workbook.find("m:sheets", _NS)
        if sheets is None:
            raise ValueError("XLSX workbook has no sheets")
        for node in sheets:
            if node.attrib.get("name") != sheet_name:
                continue
            rel_id = node.attrib.get(f"{{{_REL_NS}}}id")
            if rel_id is None or rel_id not in rel_map:
                raise ValueError(f"sheet {sheet_name!r} has no relationship")
            target = rel_map[rel_id]
            break
        if target is None:
            raise ValueError(f"sheet {sheet_name!r} not found")
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        sheet = ET.fromstring(zf.read(target))

        def value(cell: ET.Element) -> str:
            kind = cell.attrib.get("t")
            if kind == "inlineStr":
                return "".join(t.text or "" for t in cell.findall(".//m:t", _NS))
            node = cell.find("m:v", _NS)
            raw = "" if node is None else (node.text or "")
            return shared[int(raw)] if kind == "s" and raw else raw

        rows: list[dict[str, str]] = []
        for row in sheet.findall(".//m:sheetData/m:row", _NS):
            record: dict[str, str] = {"__row__": row.attrib.get("r", "")}
            for cell in row.findall("m:c", _NS):
                match = re.match(r"([A-Z]+)", cell.attrib["r"])
                if match:
                    record[match.group(1)] = value(cell)
            rows.append(record)
        return rows


def _headers(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str], int]:
    for idx, row in enumerate(rows):
        if "SP_ENTITY_ID" in row.values():
            return row, rows[idx + 1], idx
    raise ValueError("SP_ENTITY_ID header not found")


def read_entity_ids(path: str | Path) -> set[str]:
    rows = _xlsx_rows(path)
    headers, _periods, idx = _headers(rows)
    entity_col = next(col for col, name in headers.items() if name == "SP_ENTITY_ID")
    return {
        str(row.get(entity_col, "")).strip()
        for row in rows[idx + 2 :]
        if str(row.get(entity_col, "")).strip()
        and str(row.get(entity_col, "")).strip().upper() != "NA"
    }


def _number(value: object) -> float:
    text = str(value).strip()
    if not text or text.upper() in {"NA", "N/A", "NAN", "NULL", "NONE"}:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _merge_value(old: float, new: float, context: str) -> float:
    if pd.isna(old):
        return new
    if pd.isna(new):
        return old
    if not np.isclose(old, new, rtol=1e-8, atol=1e-8):
        raise ValueError(f"conflicting duplicate metric {context}: {old} vs {new}")
    return old


def normalize_run4(
    path: str | Path,
    *,
    admission_time: datetime,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normalize run_4's wide quarter columns into an entity-quarter panel."""
    admission = pd.Timestamp(admission_time)
    admission = admission.tz_localize("UTC") if admission.tzinfo is None else admission.tz_convert("UTC")
    rows = _xlsx_rows(path)
    headers, periods, idx = _headers(rows)

    def header_col(name: str) -> str | None:
        return next((col for col, value in headers.items() if value == name), None)

    entity_col = header_col("SP_ENTITY_ID")
    name_col = header_col("SP_ENTITY_NAME")
    industry_col = header_col("MI_PRIMARY_INDUSTRY")
    exchange_col = header_col("SP_EXCHANGE")
    if entity_col is None or name_col is None:
        raise ValueError("run_4 must include SP_ENTITY_ID and SP_ENTITY_NAME")

    metric_cols: dict[str, list[tuple[str, str]]] = {}
    period_end_cols: dict[str, list[str]] = {}
    for col, header in headers.items():
        period = str(periods.get(col, "")).strip()
        # Historical panel authority uses absolute FQqYYYY references only.
        # Relative FQ0/IQ_FQ drifts with the as-of date and can disagree with
        # the fixed-quarter cells in the same exported workbook.
        if not re.fullmatch(r"FQ[1-4]\d{4}", period):
            continue
        if header in _METRICS:
            metric_cols.setdefault(_METRICS[header], []).append((period, col))
        elif header == "IQ_PERIOD_END":
            period_end_cols.setdefault(period, []).append(col)
    missing = sorted(set(_METRICS.values()) - set(metric_cols))
    if missing:
        raise ValueError(f"run_4 missing required metric families: {missing}")

    records: list[dict[str, Any]] = []
    collapsed = 0
    for row in rows[idx + 2 :]:
        entity_id = str(row.get(entity_col, "")).strip()
        if not entity_id or entity_id.upper() == "NA":
            continue
        period_dates: dict[str, pd.Timestamp] = {}
        for label, cols in period_end_cols.items():
            dates = [_excel_date(row.get(col, "")) for col in cols]
            dates = [date for date in dates if not pd.isna(date)]
            if dates and any(date != dates[0] for date in dates[1:]):
                raise ValueError(f"conflicting IQ_PERIOD_END for entity={entity_id} period={label}")
            if dates:
                period_dates[label] = dates[0]

        by_date: dict[pd.Timestamp, dict[str, Any]] = {}
        for metric, columns in metric_cols.items():
            for label, col in columns:
                period_end = period_dates.get(label)
                if period_end is None:
                    continue
                if period_end.date() > admission.date():
                    raise ValueError(f"future quarter {period_end.date()} for entity={entity_id}")
                record = by_date.setdefault(
                    period_end,
                    {
                        "source_entity_id": entity_id,
                        "source_entity_name": str(row.get(name_col, "")).strip(),
                        "industry": str(row.get(industry_col, "")).strip() if industry_col else "",
                        "exchange": str(row.get(exchange_col, "")).strip() if exchange_col else "",
                        "period_end": period_end,
                        "known_at": admission,
                        "pit_mode": PIT_MODE,
                        "identity_status": IDENTITY_STATUS,
                        "source_period_labels": set(),
                    },
                )
                record["source_period_labels"].add(label)
                old = float(record.get(metric, float("nan")))
                new = _number(row.get(col, ""))
                if not pd.isna(old) and not pd.isna(new):
                    collapsed += 1
                record[metric] = _merge_value(old, new, f"entity={entity_id} date={period_end.date()} metric={metric}")
        for record in by_date.values():
            record["source_period_labels"] = ",".join(sorted(record["source_period_labels"]))
            for metric in _METRICS.values():
                record.setdefault(metric, float("nan"))
            records.append(record)

    panel = pd.DataFrame(records)
    if panel.empty:
        raise ValueError("run_4 produced no quarterly rows")
    panel = panel.sort_values(["source_entity_id", "period_end"]).reset_index(drop=True)
    panel = derive_metrics(panel)
    panel["is_latest_known_quarter"] = False
    latest_idx = panel.groupby("source_entity_id", sort=False)["period_end"].idxmax()
    panel.loc[latest_idx, "is_latest_known_quarter"] = True
    panel["schema_version"] = PANEL_SCHEMA
    panel["source_id"] = SOURCE_ID
    return panel, {
        "absolute_history_entity_count": int(panel["source_entity_id"].nunique()),
        "quarter_row_count": int(len(panel)),
        "quarter_min": panel["period_end"].min().date().isoformat(),
        "quarter_max": panel["period_end"].max().date().isoformat(),
        "duplicate_period_labels_collapsed": int(collapsed),
        "historical_publication_timestamps_embedded": False,
        "relative_fq0_excluded": True,
        "quarter_reference_mode": "ABSOLUTE_FQqYYYY_ONLY",
        "pit_mode": PIT_MODE,
    }


def derive_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.sort_values(["source_entity_id", "period_end"]).copy()
    for col in _METRICS.values():
        out[col] = pd.to_numeric(out[col], errors="coerce")
    g = out.groupby("source_entity_id", sort=False, group_keys=False)
    out["invested_capital_q"] = (out["equity_q"] + out["total_debt_q"] - out["cash_q"]).where(lambda s: s > 0)
    out["revenue_ttm"] = g["total_revenue_q"].transform(lambda s: s.rolling(4, min_periods=4).sum())
    out["operating_income_ttm"] = g["operating_income_q"].transform(lambda s: s.rolling(4, min_periods=4).sum())
    out["invested_capital_avg"] = g["invested_capital_q"].transform(lambda s: s.rolling(4, min_periods=1).mean())
    out["roic"] = out["operating_income_ttm"] / out["invested_capital_avg"].replace(0.0, np.nan)
    out["revenue_growth_q"] = g["total_revenue_q"].pct_change(fill_method=None)
    out["revenue_growth_yoy"] = g["revenue_ttm"].pct_change(4, fill_method=None)
    out["revenue_growth_yoy"] = out["revenue_growth_yoy"].fillna(g["total_revenue_q"].pct_change(4, fill_method=None))
    out["sales_growth_q"] = out["revenue_growth_q"]
    out["sales_accel_q"] = g["sales_growth_q"].diff()
    out["operating_margin_q"] = np.where(out["total_revenue_q"] > 0, out["operating_income_q"] / out["total_revenue_q"], np.nan)
    out["operating_margin_delta_q"] = g["operating_margin_q"].diff()
    out["op_margin_accel_q"] = g["operating_margin_delta_q"].diff()
    out["revenue_inventory_q"] = np.where(out["inventory_q"] > 0, out["total_revenue_q"] / out["inventory_q"], np.nan)
    out["delta_revenue_inventory"] = g["revenue_inventory_q"].diff()
    asset_ex_inventory = out["total_assets_q"] - out["inventory_q"]
    log_assets = np.log(asset_ex_inventory.where(asset_ex_inventory > 0, np.nan))
    log_sales = np.log(out["total_revenue_q"].where(out["total_revenue_q"] > 0, np.nan))
    out["bloat_q"] = log_assets.groupby(out["source_entity_id"]).diff() - log_sales.groupby(out["source_entity_id"]).diff()
    assets_lag1 = g["total_assets_q"].shift(1)
    out["net_investment_q"] = (out["capex_q"].abs() - out["depreciation_q"]) / assets_lag1.replace(0.0, np.nan)
    out["asset_growth_yoy"] = g["total_assets_q"].pct_change(4, fill_method=None)
    for col in (
        "roic", "revenue_growth_q", "revenue_growth_yoy", "sales_accel_q",
        "operating_margin_q", "operating_margin_delta_q", "op_margin_accel_q",
        "revenue_inventory_q", "delta_revenue_inventory", "bloat_q",
        "net_investment_q", "asset_growth_yoy",
    ):
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return out


def _wide(latest: pd.DataFrame, column: str) -> pd.DataFrame:
    index = [pd.Timestamp(latest["known_at"].max()).tz_convert("UTC")]
    return pd.DataFrame(
        [pd.to_numeric(latest[column], errors="coerce").to_numpy(dtype=float)],
        index=index,
        columns=latest["source_entity_id"].astype(str).tolist(),
    )


def build_current_state(
    panel: pd.DataFrame,
    *,
    all_entity_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    latest = panel.loc[panel["is_latest_known_quarter"]].sort_values("source_entity_id").copy()
    context = {
        name: _wide(latest, name)
        for name in (
            "roic", "asset_growth_yoy", "sales_accel_q", "op_margin_accel_q",
            "bloat_q", "net_investment_q", "operating_margin_delta_q",
            "delta_revenue_inventory",
        )
    }
    specs = [spec for spec in build_default_feature_specs() if spec.category == "fundamental"]
    for spec in specs:
        context[spec.name] = spec.func(context, spec)

    scale_stats: dict[str, Any] = {}
    for name in ("z_moat", "z_inventory_quality_proxy", "z_discipline_cond", "z_demand"):
        scaled, stats = _cross_sectional_scale(context[name], mode=CS_SCALE_ROBUST)
        latest[name] = latest["source_entity_id"].map(scaled.iloc[0].to_dict())
        scale_stats[name] = stats
    latest["capital_cycle_score"] = latest["source_entity_id"].map(context["capital_cycle_score"].iloc[0].to_dict())
    latest["quality_composite"] = latest["capital_cycle_score"]
    counts = compute_factor_group_counts(latest)
    latest["factor_present_count"] = counts["factor_present_count"].astype(int)
    latest["factor_positive_count"] = counts["factor_positive_count"].astype(int)

    registry_hash = compute_registry_hash(specs)
    group_hash = hashlib.sha256(json.dumps(V1_1_FACTOR_GROUPS, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    latest["fundamental_spec_registry_hash"] = registry_hash
    latest["rule100_factor_group_contract_hash"] = group_hash
    latest["schema_version"] = STATE_SCHEMA
    latest["source_id"] = SOURCE_ID
    latest["fundamental_state_status"] = np.select(
        [latest["factor_present_count"].eq(4), latest["factor_present_count"].gt(0)],
        ["COMPLETE_FACTOR_STATE", "PARTIAL_FACTOR_STATE"],
        default="NO_FACTOR_STATE",
    )

    missing_ids = sorted((all_entity_ids or set()) - set(latest["source_entity_id"].astype(str)))
    if missing_ids:
        placeholders = pd.DataFrame({"source_entity_id": missing_ids})
        placeholders["known_at"] = pd.Timestamp(panel["known_at"].max()).tz_convert("UTC")
        placeholders["pit_mode"] = PIT_MODE
        placeholders["identity_status"] = IDENTITY_STATUS
        placeholders["fundamental_spec_registry_hash"] = registry_hash
        placeholders["rule100_factor_group_contract_hash"] = group_hash
        placeholders["schema_version"] = STATE_SCHEMA
        placeholders["source_id"] = SOURCE_ID
        placeholders["factor_present_count"] = 0
        placeholders["factor_positive_count"] = 0
        placeholders["fundamental_state_status"] = "NO_ABSOLUTE_QUARTER_HISTORY"
        latest = pd.concat([latest, placeholders], ignore_index=True, sort=False)
        latest = latest.sort_values("source_entity_id").reset_index(drop=True)
    if {"security_id", "permno"} & set(latest.columns):
        raise AssertionError("company fundamental state contains forbidden security identity")
    if latest["identity_status"].ne(IDENTITY_STATUS).any():
        raise AssertionError("company identity status drift")

    factor_cols = [
        "z_demand", "z_inventory_quality_proxy", "z_moat", "z_discipline_cond",
        "capital_cycle_score", "factor_present_count", "factor_positive_count",
    ]
    raw_input_cols = [
        "roic", "sales_accel_q", "op_margin_accel_q", "bloat_q",
        "net_investment_q", "asset_growth_yoy", "operating_margin_delta_q",
        "delta_revenue_inventory",
    ]
    return latest.reset_index(drop=True), {
        "fundamental_spec_registry_hash": registry_hash,
        "rule100_factor_group_contract_hash": group_hash,
        "robust_scale_stats": scale_stats,
        "factor_coverage": {
            col: {"non_null": int(latest[col].notna().sum()), "rate": float(latest[col].notna().mean())}
            for col in factor_cols
        },
        "raw_factor_input_coverage": {
            col: {"non_null": int(latest[col].notna().sum()), "rate": float(latest[col].notna().mean())}
            for col in raw_input_cols
        },
        "factor_state_status_counts": {
            str(key): int(value)
            for key, value in latest["fundamental_state_status"].value_counts(dropna=False).items()
        },
    }


def build_run4_slice(
    run4_path: str | Path,
    *,
    admission_time: datetime | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    admitted = (admission_time or datetime.now(UTC)).astimezone(UTC)
    before = sha256_file(run4_path)
    run4_ids = read_entity_ids(run4_path)
    panel, metadata = normalize_run4(run4_path, admission_time=admitted)
    after = sha256_file(run4_path)
    if before != after:
        raise RuntimeError("run_4.xlsx changed during admission")

    state, factor_meta = build_current_state(panel, all_entity_ids=run4_ids)
    metadata.update(factor_meta)
    metadata.update(
        source_entity_count=len(run4_ids),
        no_absolute_history_entity_ids=sorted(run4_ids - set(panel["source_entity_id"].astype(str))),
    )
    metadata.update(
        source_id=SOURCE_ID,
        authority_roles=["COMPANY_UNIVERSE", "QUARTERLY_FUNDAMENTALS"],
        company_universe_entity_count=len(run4_ids),
        company_universe_raw_object_sha256=before,
        raw_object_sha256=before,
        raw_object_bytes=Path(run4_path).stat().st_size,
        admission_time_utc=admitted.isoformat().replace("+00:00", "Z"),
        panel_schema_version=PANEL_SCHEMA,
        state_schema_version=STATE_SCHEMA,
        identity_status=IDENTITY_STATUS,
    )
    return panel, state, metadata
