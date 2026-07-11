"""M7F0-v4: 2019 RDQ PEAD Q5 long-only vertical on local CRSP (flagged research).

Contract (v4):
- Day +1 = first CRSP session strictly after RDQ; included in exact 60-session window.
- Map via current-snapshot CUSIP8; unique PERMNO only (ambiguous/unmapped dropped).
- Mapping + window + delist filters BEFORE ≥50 formation gate; then deterministic Q5;
  then earliest-event-wins overlap.
- ≥10 live names on every return-bearing day; final full liquidation exempt.
- Delist day: (1+RET)*(1+DLRET)-1, or DLRET if RET blank; then cash for remaining horizon.
- Unresolved selected delists block the run.
- Special/nonnumeric returns fail only when encountered in selected windows.
- cost_t = 0.00075 * sum_i |Δw_i,t| (security weights; includes liquidation).
- Claim ceiling: research_use_only; link_model=current_snapshot_cusip8; not alpha/tradable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import duckdb
import numpy as np
import pandas as pd

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

ONE_WAY_BPS = 7.5
ONE_WAY_COST = ONE_WAY_BPS / 10_000.0  # 0.00075
HOLDING_SESSIONS = 60
MIN_FORMATION_NAMES = 50
MIN_LIVE_NAMES = 10
COHORT_YEAR = 2019

DEFAULT_D1 = Path("data/processed/pead_d1_sue_signal.parquet")
DEFAULT_SEC = Path("data/processed/security_master_compustat.parquet")
DEFAULT_CRSP = Path("data/hkcj1itkyvfsmibz.csv")
DEFAULT_EVIDENCE = Path("docs/context/e2e_evidence/pead_m7f0_v4_2019_crsp_vertical.json")
DEFAULT_PARQUET = Path("data/processed/pead_m7f0_v4_2019_daily_returns.parquet")
DEFAULT_MANIFEST = Path("docs/context/e2e_evidence/pead_m7f0_v4_2019_daily_returns.parquet.manifest.json")
DEFAULT_CUSIP_MAP = Path("data/processed/pead_m7f0_v4_crsp_cusip8_permno_snapshot.parquet")


class M7F0BlockedError(RuntimeError):
    """Fail-closed research run blocker."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_cusip8(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype("string")
        .fillna("")
        .str.upper()
        .str.replace(r"[^0-9A-Z]", "", regex=True)
    )
    return cleaned.str.slice(0, 8)


def _is_numeric_return(value: object) -> bool:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return False
    if isinstance(value, (int, float, np.floating, np.integer)):
        return math.isfinite(float(value))
    text = str(value).strip()
    if text == "" or text.upper() in {"C", "B", "S", "A", "P", "T", "N"}:
        return False
    try:
        return math.isfinite(float(text))
    except ValueError:
        return False


def _to_float_or_none(value: object) -> float | None:
    if not _is_numeric_return(value):
        return None
    return float(value)


def build_crsp_cusip_permno_map(con: duckdb.DuckDBPyConnection, crsp_path: Path, out_path: Path) -> pd.DataFrame:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""
        COPY (
          SELECT cusip8, permno
          FROM (
            SELECT
              upper(left(regexp_replace(cast(CUSIP AS VARCHAR), '[^0-9A-Za-z]', ''), 8)) AS cusip8,
              PERMNO AS permno,
              count(*) OVER (
                PARTITION BY upper(left(regexp_replace(cast(CUSIP AS VARCHAR), '[^0-9A-Za-z]', ''), 8))
              ) AS n_perm
            FROM (
              SELECT DISTINCT CUSIP, PERMNO
              FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
              WHERE CUSIP IS NOT NULL AND PERMNO IS NOT NULL
            )
          ) t
          WHERE n_perm = 1 AND length(cusip8) = 8
        ) TO '{out_path.as_posix()}' (FORMAT PARQUET)
        """
    )
    return con.execute(f"SELECT * FROM read_parquet('{out_path.as_posix()}')").df()


def load_mapped_events(
    con: duckdb.DuckDBPyConnection,
    *,
    d1_path: Path,
    sec_path: Path,
    cusip_map_path: Path,
) -> tuple[pd.DataFrame, dict[str, int]]:
    q = f"""
    WITH d1 AS (
      SELECT
        gvkey,
        CAST(rdq AS DATE) AS rdq,
        CAST(sue_price_scaled_clipped AS DOUBLE) AS sue
      FROM read_parquet('{d1_path.as_posix()}')
      WHERE COALESCE(valid_sue, false)
        AND CAST(rdq AS DATE) >= DATE '{COHORT_YEAR}-01-01'
        AND CAST(rdq AS DATE) < DATE '{COHORT_YEAR + 1}-01-01'
        AND sue_price_scaled_clipped IS NOT NULL
    ),
    sec AS (
      SELECT DISTINCT
        gvkey,
        upper(left(regexp_replace(cast(cusip AS VARCHAR), '[^0-9A-Za-z]', ''), 8)) AS cusip8
      FROM read_parquet('{sec_path.as_posix()}')
      WHERE cusip IS NOT NULL
        AND length(upper(left(regexp_replace(cast(cusip AS VARCHAR), '[^0-9A-Za-z]', ''), 8))) = 8
    ),
    joined AS (
      SELECT d1.gvkey, d1.rdq, d1.sue, s.cusip8, m.permno
      FROM d1
      LEFT JOIN sec s ON d1.gvkey = s.gvkey
      LEFT JOIN read_parquet('{cusip_map_path.as_posix()}') m ON s.cusip8 = m.cusip8
    ),
    per_event AS (
      SELECT
        gvkey,
        rdq,
        max(sue) AS sue,
        count(DISTINCT permno) FILTER (WHERE permno IS NOT NULL) AS n_perm,
        max(permno) AS permno
      FROM joined
      GROUP BY 1, 2
    )
    SELECT * FROM per_event
    """
    frame = con.execute(q).df()
    frame["rdq"] = pd.to_datetime(frame["rdq"]).dt.normalize()
    counts = {
        "d1_valid_2019_events": int(len(frame)),
        "unique_mapped": int((frame["n_perm"] == 1).sum()),
        "ambiguous": int((frame["n_perm"] > 1).sum()),
        "unmapped": int((frame["n_perm"] == 0).sum()),
    }
    mapped = frame.loc[frame["n_perm"] == 1, ["gvkey", "rdq", "sue", "permno"]].copy()
    mapped["permno"] = mapped["permno"].astype(np.int64)
    mapped["event_id"] = (
        mapped["gvkey"].astype(str)
        + "|"
        + mapped["rdq"].dt.strftime("%Y-%m-%d")
        + "|"
        + mapped["permno"].astype(str)
    )
    return mapped.reset_index(drop=True), counts


def load_crsp_panel(
    con: duckdb.DuckDBPyConnection,
    *,
    crsp_path: Path,
    permnos: Sequence[int],
    start: str,
    end: str,
) -> pd.DataFrame:
    if not permnos:
        return pd.DataFrame(columns=["permno", "date", "ret", "dlret", "dlstcd"])
    permno_list = ",".join(str(int(p)) for p in sorted(set(int(p) for p in permnos)))
    q = f"""
    SELECT
      CAST(PERMNO AS BIGINT) AS permno,
      CAST(date AS DATE) AS date,
      RET AS ret_raw,
      DLRET AS dlret_raw,
      DLSTCD AS dlstcd_raw
    FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
    WHERE CAST(PERMNO AS BIGINT) IN ({permno_list})
      AND CAST(date AS DATE) >= DATE '{start}'
      AND CAST(date AS DATE) <= DATE '{end}'
    ORDER BY 1, 2
    """
    return con.execute(q).df()


def build_session_spine(crsp_panel: pd.DataFrame) -> pd.DatetimeIndex:
    if crsp_panel.empty:
        return pd.DatetimeIndex([])
    dates = pd.to_datetime(crsp_panel["date"]).dt.normalize().drop_duplicates().sort_values()
    return pd.DatetimeIndex(dates)


def resolve_event_window(
    *,
    event: Mapping[str, Any],
    sessions: pd.DatetimeIndex,
    panel_by_permno: Mapping[int, pd.DataFrame],
) -> dict[str, Any]:
    rdq = pd.Timestamp(event["rdq"]).normalize()
    permno = int(event["permno"])
    # Day +1 = first session strictly after RDQ (included in 60-day window).
    after = sessions[sessions > rdq]
    if len(after) < HOLDING_SESSIONS:
        return {"status": "incomplete_calendar", "entry": None, "rows": None}
    window_dates = after[:HOLDING_SESSIONS]
    entry = window_dates[0]
    stock = panel_by_permno.get(permno)
    if stock is None or stock.empty:
        return {"status": "missing_permno_panel", "entry": entry, "rows": None}
    stock = stock.set_index("date").sort_index()
    rows: list[dict[str, Any]] = []
    liquidated = False
    for offset, session in enumerate(window_dates, start=1):
        session = pd.Timestamp(session).normalize()
        if liquidated:
            rows.append(
                {
                    "session_offset": offset,
                    "return_date": session,
                    "r": 0.0,
                    "live": False,
                    "delist_day": False,
                }
            )
            continue
        if session not in stock.index:
            return {"status": "missing_session", "entry": entry, "rows": None}
        rec = stock.loc[session]
        ret = _to_float_or_none(rec["ret_raw"])
        dlret = _to_float_or_none(rec["dlret_raw"])
        dlstcd_raw = rec["dlstcd_raw"]
        try:
            dlstcd = int(float(dlstcd_raw)) if pd.notna(dlstcd_raw) and str(dlstcd_raw).strip() != "" else None
        except (TypeError, ValueError):
            dlstcd = None
        delist_event = dlstcd is not None and dlstcd >= 200
        if delist_event:
            if dlret is None:
                return {"status": "unresolved_delist", "entry": entry, "rows": None}
            if ret is None:
                r = dlret
            else:
                r = (1.0 + ret) * (1.0 + dlret) - 1.0
            if not math.isfinite(r):
                return {"status": "nonnumeric_selected_window", "entry": entry, "rows": None}
            rows.append(
                {
                    "session_offset": offset,
                    "return_date": session,
                    "r": float(r),
                    "live": True,
                    "delist_day": True,
                }
            )
            liquidated = True
            continue
        # Non-delist day: special/nonnumeric RET in selected window blocks this event window.
        if ret is None:
            # Blank RET without delist is nonnumeric in selected window.
            return {"status": "nonnumeric_selected_window", "entry": entry, "rows": None}
        rows.append(
            {
                "session_offset": offset,
                "return_date": session,
                "r": float(ret),
                "live": True,
                "delist_day": False,
            }
        )
    return {
        "status": "ok",
        "entry": entry,
        "rows": rows,
        "event_id": event["event_id"],
        "gvkey": event["gvkey"],
        "permno": permno,
        "rdq": rdq,
        "sue": float(event["sue"]),
    }


def apply_formation_q5_and_overlap(resolved: list[dict[str, Any]]) -> tuple[pd.DataFrame, dict[str, int]]:
    ok = [r for r in resolved if r["status"] == "ok"]
    if not ok:
        return pd.DataFrame(), {
            "resolved_ok": 0,
            "formation_dates_ge_50": 0,
            "q5_events_before_overlap": 0,
            "q5_events_after_overlap": 0,
        }
    events = []
    for r in ok:
        events.append(
            {
                "event_id": r["event_id"],
                "gvkey": r["gvkey"],
                "permno": int(r["permno"]),
                "rdq": pd.Timestamp(r["rdq"]),
                "entry": pd.Timestamp(r["entry"]),
                "sue": float(r["sue"]),
                "rows": r["rows"],
            }
        )
    ev = pd.DataFrame(events)
    # Formation breadth after mapping/window/delist filters.
    counts = ev.groupby("entry")["event_id"].transform("count")
    ev = ev.loc[counts >= MIN_FORMATION_NAMES].copy()
    formation_dates = int(ev["entry"].nunique()) if not ev.empty else 0
    if ev.empty:
        return ev, {
            "resolved_ok": len(ok),
            "formation_dates_ge_50": 0,
            "q5_events_before_overlap": 0,
            "q5_events_after_overlap": 0,
        }

    def _q5(group: pd.DataFrame) -> pd.DataFrame:
        g = group.sort_values(["sue", "permno", "event_id"], ascending=[False, True, True]).copy()
        n = len(g)
        # Deterministic quintile: top floor(n/5) at least 1 when n>=5; use rank pct.
        g["rank"] = np.arange(1, n + 1)
        # Highest SUE → Q5. Assign quintile by equal count from top.
        q = int(math.floor(n / 5))
        if q < 1:
            return g.iloc[0:0]
        return g.iloc[:q]

    q5 = (
        ev.groupby("entry", group_keys=False)
        .apply(_q5, include_groups=False)
        .reset_index(drop=True)
    )
    before = int(len(q5))
    # Earliest-event-wins for overlapping PERMNOs on live sessions.
    # Expand to position-days for live equity days only for conflict resolution of claim ownership.
    claim_rows: list[dict[str, Any]] = []
    for row in q5.itertuples(index=False):
        for cell in row.rows:
            if not cell["live"]:
                continue
            claim_rows.append(
                {
                    "event_id": row.event_id,
                    "permno": int(row.permno),
                    "rdq": row.rdq,
                    "entry": row.entry,
                    "return_date": pd.Timestamp(cell["return_date"]),
                    "session_offset": int(cell["session_offset"]),
                    "r": float(cell["r"]),
                    "delist_day": bool(cell["delist_day"]),
                    "sue": float(row.sue),
                }
            )
    claims = pd.DataFrame(claim_rows)
    if claims.empty:
        return pd.DataFrame(), {
            "resolved_ok": len(ok),
            "formation_dates_ge_50": formation_dates,
            "q5_events_before_overlap": before,
            "q5_events_after_overlap": 0,
        }
    claims = claims.sort_values(
        ["permno", "return_date", "rdq", "entry", "event_id"],
        ascending=[True, True, True, True, True],
        kind="mergesort",
    )
    # On each (permno, return_date), earliest rdq/entry/event_id wins.
    winners = claims.drop_duplicates(subset=["permno", "return_date"], keep="first")
    active_event_ids = set(winners["event_id"].unique())
    q5_after = q5.loc[q5["event_id"].isin(active_event_ids)].copy()
    stats = {
        "resolved_ok": len(ok),
        "formation_dates_ge_50": formation_dates,
        "q5_events_before_overlap": before,
        "q5_events_after_overlap": int(len(q5_after)),
    }
    return winners.reset_index(drop=True), stats


def build_daily_portfolio(winners: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    if winners.empty:
        raise M7F0BlockedError("no_winner_position_days")
    winners = winners.copy()
    winners["return_date"] = pd.to_datetime(winners["return_date"]).dt.normalize()
    dates = sorted(winners["return_date"].unique())
    # Final liquidation date = last date with any live claim, next day flat is exempt concept:
    # we charge liquidation on the day after last holdings via terminal flat weights.
    records: list[dict[str, Any]] = []
    prev_w: dict[int, float] = {}
    final_date = dates[-1]
    for dt in dates:
        day = winners.loc[winners["return_date"] == dt]
        live = day.drop_duplicates("permno")
        n_live = int(len(live))
        is_final = dt == final_date
        if n_live > 0 and n_live < MIN_LIVE_NAMES and not is_final:
            raise M7F0BlockedError(f"live_names_below_min:{n_live}_on_{pd.Timestamp(dt).date()}")
        if n_live == 0:
            weights = {}
            gross = 0.0
        else:
            w = 1.0 / n_live
            weights = {int(p): w for p in live["permno"].tolist()}
            ret_map = {int(r.permno): float(r.r) for r in live.itertuples(index=False)}
            gross = float(sum(weights[p] * ret_map[p] for p in weights))
        all_permnos = set(prev_w) | set(weights)
        turnover = float(sum(abs(weights.get(p, 0.0) - prev_w.get(p, 0.0)) for p in all_permnos))
        cost = ONE_WAY_COST * turnover
        net = gross - cost
        records.append(
            {
                "return_date": pd.Timestamp(dt),
                "n_live": n_live,
                "daily_gross_return": gross,
                "turnover_l1": turnover,
                "daily_cost": cost,
                "daily_net_return": net,
            }
        )
        prev_w = weights
    # Final liquidation to cash after last date (exempt from min-live gate).
    if prev_w:
        turnover = float(sum(abs(0.0 - w) for w in prev_w.values()))
        cost = ONE_WAY_COST * turnover
        liq_date = pd.Timestamp(final_date)  # attribute liquidation cost on final day additively?
        # Contract: include liquidation in cost path. Add terminal liquidation as extra row next calendar
        # is wrong; fold into final day cost instead so equity path is contiguous.
        records[-1]["turnover_l1"] = float(records[-1]["turnover_l1"] + turnover)
        records[-1]["daily_cost"] = float(records[-1]["daily_cost"] + cost)
        records[-1]["daily_net_return"] = float(records[-1]["daily_gross_return"] - records[-1]["daily_cost"])
        records[-1]["includes_terminal_liquidation"] = True
    daily = pd.DataFrame.from_records(records)
    daily = daily.sort_values("return_date").reset_index(drop=True)
    equity = (1.0 + daily["daily_net_return"]).cumprod()
    daily["equity_net"] = equity
    stats = {
        "n_days": int(len(daily)),
        "start": str(daily["return_date"].iloc[0].date()) if len(daily) else None,
        "end": str(daily["return_date"].iloc[-1].date()) if len(daily) else None,
        "total_net_return": float(equity.iloc[-1] - 1.0) if len(daily) else None,
        "min_live_names": int(daily["n_live"].min()) if len(daily) else None,
        "mean_live_names": float(daily["n_live"].mean()) if len(daily) else None,
    }
    return daily, stats


def run_vertical(
    *,
    repo_root: Path,
    d1_path: Path,
    sec_path: Path,
    crsp_path: Path,
    evidence_path: Path,
    parquet_path: Path,
    manifest_path: Path,
    cusip_map_path: Path,
) -> dict[str, Any]:
    con = duckdb.connect()
    # Ensure CUSIP map
    if not cusip_map_path.is_file():
        build_crsp_cusip_permno_map(con, crsp_path, cusip_map_path)
    mapped, map_counts = load_mapped_events(
        con, d1_path=d1_path, sec_path=sec_path, cusip_map_path=cusip_map_path
    )
    if mapped.empty:
        raise M7F0BlockedError("no_unique_mapped_events")

    # CRSP panel for mapped permnos, RDQ year through next year+buffer
    start = f"{COHORT_YEAR}-01-01"
    end = f"{COHORT_YEAR + 1}-12-31"
    panel = load_crsp_panel(
        con,
        crsp_path=crsp_path,
        permnos=mapped["permno"].tolist(),
        start=start,
        end=end,
    )
    if panel.empty:
        raise M7F0BlockedError("empty_crsp_panel")
    panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()
    sessions = build_session_spine(panel)
    panel_by = {int(p): g.copy() for p, g in panel.groupby("permno")}

    resolved: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for event in mapped.to_dict(orient="records"):
        result = resolve_event_window(event=event, sessions=sessions, panel_by_permno=panel_by)
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
        resolved.append(result)

    # Unresolved delists fail the event window (pre-formation filter). A selected
    # Q5 event must never carry unresolved delist status — if any do, block run.
    winners, form_stats = apply_formation_q5_and_overlap(resolved)
    if winners.empty:
        raise M7F0BlockedError("no_q5_events_after_filters")
    selected_ids = set(winners["event_id"].unique())
    selected_unresolved = [
        r for r in resolved if r.get("event_id") in selected_ids and r["status"] == "unresolved_delist"
    ]
    # selected events are only status==ok; defensive check for contract language
    if selected_unresolved or any(
        r["status"] == "unresolved_delist" and r.get("event_id") in selected_ids for r in resolved
    ):
        raise M7F0BlockedError(
            f"unresolved_selected_delist_count={len(selected_unresolved)}"
        )
    daily, port_stats = build_daily_portfolio(winners)

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    daily_out = daily.copy()
    daily_out["return_date"] = daily_out["return_date"].dt.strftime("%Y-%m-%d")
    daily_out.to_parquet(parquet_path, index=False)
    parquet_sha = _sha256_file(parquet_path)

    source_hashes = {
        "d1_sha256": _sha256_file(d1_path) if d1_path.is_file() else None,
        "security_master_sha256": _sha256_file(sec_path) if sec_path.is_file() else None,
        "crsp_sha256": _sha256_file(crsp_path) if crsp_path.is_file() else None,
        "cusip_permno_map_sha256": _sha256_file(cusip_map_path) if cusip_map_path.is_file() else None,
        "daily_parquet_sha256": parquet_sha,
    }

    evidence = {
        "artifact_name": "pead_m7f0_v4_2019_crsp_vertical",
        "round_id": "ROUND-20260712-C0X-M7F0-V4",
        "scope_id": "C0X_BOOTSTRAP_TO_M7F0_V4",
        "generated_at_utc": _utc_now(),
        "authority": (
            "flagged research mechanical vertical only; not strict M6b readiness; "
            "not alpha; not tradable; not as-of CUSIP link"
        ),
        "claim_ceiling": {
            "evidence_tier": "M6B_FLAGGED_BEST_AVAILABLE_RESEARCH",
            "link_model": "current_snapshot_cusip8",
            "as_of_link": False,
            "research_use_only": True,
            "usable_for_alpha_inference": False,
            "usable_for_strategy_promotion": False,
            "m6b_data_contract_ready": False,
            "not_alpha": True,
            "not_tradable_claim": True,
        },
        "contract": {
            "cohort": "RDQ calendar year 2019",
            "day_plus_1": "first_crsp_session_strictly_after_rdq",
            "holding_sessions": HOLDING_SESSIONS,
            "day_plus_1_included_in_window": True,
            "formation_min_names": MIN_FORMATION_NAMES,
            "min_live_names": MIN_LIVE_NAMES,
            "min_live_final_liquidation_exempt": True,
            "overlap": "earliest_event_wins",
            "weights": "equal_weight_live_equity_permnos",
            "one_way_cost": ONE_WAY_COST,
            "cost_formula": "0.00075 * sum_i abs(delta_w_i) including terminal liquidation",
            "delist_day_return": "(1+RET)*(1+DLRET)-1 or DLRET if RET blank; then cash for remainder",
            "nonnumeric_scope": "selected_windows_only",
            "filter_order": [
                "unique_permno_map",
                "complete_60_session_window_with_delist_rules",
                "formation_breadth_ge_50",
                "deterministic_q5",
                "earliest_event_wins",
                "min_live_names_ge_10_except_final_liquidation",
            ],
        },
        "counts": {
            **map_counts,
            **form_stats,
            "window_status_counts": status_counts,
            "portfolio": port_stats,
        },
        "lineage": {
            "d1_path": d1_path.as_posix(),
            "security_master_path": sec_path.as_posix(),
            "crsp_path": crsp_path.as_posix(),
            "cusip_map_path": cusip_map_path.as_posix(),
            "daily_parquet_path": parquet_path.as_posix(),
            "manifest_path": manifest_path.as_posix(),
            "hashes": source_hashes,
            "n_daily_rows": int(len(daily_out)),
        },
        "status": "PASS",
    }

    tmp = evidence_path.with_suffix(evidence_path.suffix + ".tmp")
    tmp.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(evidence_path)

    manifest = {
        "artifact": parquet_path.as_posix(),
        "sha256": parquet_sha,
        "rows": int(len(daily_out)),
        "columns": list(daily_out.columns),
        "evidence_json": evidence_path.as_posix(),
        "evidence_sha256": _sha256_file(evidence_path),
        "generated_at_utc": _utc_now(),
        "ignored_data_processed": True,
        "binding": "tracked_manifest_points_at_ignored_parquet_cache",
    }
    mtmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    mtmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mtmp.replace(manifest_path)
    return evidence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="M7F0-v4 2019 CRSP PEAD vertical")
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--d1", type=Path, default=None)
    p.add_argument("--security-master", type=Path, default=None)
    p.add_argument("--crsp", type=Path, default=None)
    p.add_argument("--evidence-out", type=Path, default=None)
    p.add_argument("--parquet-out", type=Path, default=None)
    p.add_argument("--manifest-out", type=Path, default=None)
    p.add_argument("--cusip-map", type=Path, default=None)
    p.add_argument("--data-root", type=Path, default=None, help="Absolute data root if not repo-local")
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo = args.repo_root.resolve()
    data_root = (args.data_root.resolve() if args.data_root else repo)
    d1 = (args.d1 or (data_root / DEFAULT_D1)).resolve()
    sec = (args.security_master or (data_root / DEFAULT_SEC)).resolve()
    crsp = (args.crsp or (data_root / DEFAULT_CRSP)).resolve()
    evidence = (args.evidence_out or (repo / DEFAULT_EVIDENCE)).resolve()
    parquet = (args.parquet_out or (data_root / DEFAULT_PARQUET)).resolve()
    manifest = (args.manifest_out or (repo / DEFAULT_MANIFEST)).resolve()
    cusip_map = (args.cusip_map or (data_root / DEFAULT_CUSIP_MAP)).resolve()
    try:
        evidence_doc = run_vertical(
            repo_root=repo,
            d1_path=d1,
            sec_path=sec,
            crsp_path=crsp,
            evidence_path=evidence,
            parquet_path=parquet,
            manifest_path=manifest,
            cusip_map_path=cusip_map,
        )
    except M7F0BlockedError as exc:
        print(f"M7F0 BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": evidence_doc["status"], "counts": evidence_doc["counts"]}, indent=2))
    print(f"evidence={evidence}")
    print(f"parquet={parquet}")
    print(f"manifest={manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
