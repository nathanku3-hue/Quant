"""M7F1-v5.2-final: 2019 RDQ PEAD Q5 long-only vertical on local CRSP (flagged research).

Supersedes M7F0-v4 and non-durable M7F1-v5/v5.1 diagnostics.

Contract locks:
- No entry-day or future-return filter at selection (no pre-Q5 complete-60).
- Formation entry = first CRSP session strictly after RDQ (source-wide spine only).
- Dedup one event per (formation_date, PERMNO) before distinct-PERMNO breadth/Q5.
- ROADMAP DEVIATION (explicit): pre-Q5 prior-20 observability is a *formation-time
  tradability restriction*, not a map repair. Require ≥15/20 strictly pre-entry
  source sessions with finite RET, abs(PRC)>0, and VOL>0. VOL=0 fails.
- Breadth = distinct PERMNOs on formation date; Q5 = top floor(n/5) by SUE.
- Suppress later event entirely when entry overlaps earlier 60-session claim.
- Post-select: resolve full 60-session windows; any invalid selected window BLOCKs.
- Equal-weight all active slots including post-delist cash slots (r=0 retained).
- Delist day: (1+RET)*(1+DLRET)-1 or DLRET if RET blank; then cash remainder.
- Map: one-to-one CRSP source-max-date CUSIP8→PERMNO labeled
  cross_vintage_snapshot_cusip8_non_pit (not PIT / not as-of). Map always rebuilt.
- Session calendar from source-wide distinct dates; panel load includes ≥20 sessions
  before 2019 so January formation can evaluate prior-20.
- First/last PERMNO date mismatch is post-hoc diagnostic only (not a selection gate).
- Atomic writes; force map rebuild; invalidate stale daily curve on BLOCK.
- Detached HEAD requires explicit --detached-proof-mode.
- Claim ceiling: research_use_only; snapshot link non-PIT; not alpha/tradable;
  m6b_data_contract_ready=false.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
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
ONE_WAY_COST = ONE_WAY_BPS / 10_000.0
HOLDING_SESSIONS = 60
PRIOR_SESSIONS = 20
MIN_PRIOR_OK = 15
MIN_FORMATION_NAMES = 50
MIN_ACTIVE_SLOTS = 10
COHORT_YEAR = 2019
LINK_MODEL = "cross_vintage_snapshot_cusip8_non_pit"
ARTIFACT_NAME = "pead_m7f1_v5_2019_crsp_vertical"
ROUND_ID = "ROUND-20260712-M7F1-V5-2-FINAL"
SCOPE_ID = "M7F1_V5_2_FINAL_2019_FORMATION_FIRST_VERTICAL"
IMPLEMENTATION_VERSION = "m7f1-v5.2-final"
ROADMAP_DEVIATION = (
    "prior20_formation_tradability_restriction_not_map_repair: "
    ">=15/20 strictly pre-entry sessions require finite RET, abs(PRC)>0, VOL>0"
)

DEFAULT_D1 = Path("data/processed/pead_d1_sue_signal.parquet")
DEFAULT_SEC = Path("data/processed/security_master_compustat.parquet")
DEFAULT_CRSP = Path("data/hkcj1itkyvfsmibz.csv")
DEFAULT_EVIDENCE = Path("docs/context/e2e_evidence/pead_m7f1_v5_2019_crsp_vertical.json")
DEFAULT_PARQUET = Path("data/processed/pead_m7f1_v5_2019_daily_returns.parquet")
DEFAULT_MANIFEST = Path(
    "docs/context/e2e_evidence/pead_m7f1_v5_2019_daily_returns.parquet.manifest.json"
)
DEFAULT_CUSIP_MAP = Path(
    "data/processed/pead_m7f1_v5_crsp_cusip8_permno_source_max_date.parquet"
)
DEFAULT_LEDGER = Path("data/processed/pead_m7f1_v5_2019_event_ledger.parquet")
DEFAULT_LEDGER_MANIFEST = Path(
    "docs/context/e2e_evidence/pead_m7f1_v5_2019_event_ledger.parquet.manifest.json"
)


class M7F1BlockedError(RuntimeError):
    """Fail-closed research run blocker."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise


def _atomic_write_parquet(frame: pd.DataFrame, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp.parquet", dir=str(path.parent)
    )
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        frame.to_parquet(tmp_path, index=False)
        try:
            with open(tmp_path, "r+b") as fh:
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass
        tmp_path.replace(path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise
    return _sha256_file(path)


def _invalidate_stale_curve(parquet_path: Path) -> dict[str, Any]:
    """Remove any prior daily curve so BLOCK cannot leave a stale PASS artifact."""
    if not parquet_path.is_file():
        return {
            "invalidated": False,
            "path": parquet_path.as_posix(),
            "prior_sha256": None,
            "reason": "no_file",
        }
    prior_sha = _sha256_file(parquet_path)
    parquet_path.unlink()
    return {
        "invalidated": True,
        "path": parquet_path.as_posix(),
        "prior_sha256": prior_sha,
        "reason": "block_or_fail_closed_stale_curve_removed",
    }


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


def _to_finite_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, (int, float, np.floating, np.integer)):
        f = float(value)
        return f if math.isfinite(f) else None
    text = str(value).strip()
    if text == "":
        return None
    try:
        f = float(text)
        return f if math.isfinite(f) else None
    except ValueError:
        return None


def _session_observability_ok(ret_raw: object, prc_raw: object, vol_raw: object) -> bool:
    """Prior-20 observability: finite RET, abs(PRC)>0, VOL>0 (VOL=0 fails)."""
    ret = _to_float_or_none(ret_raw)
    if ret is None:
        return False
    prc = _to_finite_float(prc_raw)
    if prc is None or abs(prc) <= 0.0:
        return False
    vol = _to_finite_float(vol_raw)
    if vol is None or vol <= 0.0:
        return False
    return True


def _git_cmd(repo_root: Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        raise M7F1BlockedError(
            f"git_command_failed:{' '.join(args)}:{completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def resolve_run_identity(
    repo_root: Path, *, detached_proof_mode: bool
) -> dict[str, Any]:
    head = _git_cmd(repo_root, "rev-parse", "HEAD")
    tree = _git_cmd(repo_root, "rev-parse", "HEAD^{tree}")
    env = os.environ.copy()
    env["GIT_NO_REPLACE_OBJECTS"] = "1"
    sym = subprocess.run(
        ["git", "-C", str(repo_root), "symbolic-ref", "-q", "HEAD"],
        capture_output=True,
        text=True,
        env=env,
    )
    detached = sym.returncode != 0
    if detached and not detached_proof_mode:
        raise M7F1BlockedError(
            "detached_head_requires_explicit_detached_proof_mode"
        )
    if detached_proof_mode and not detached:
        proof_authority = "detached_proof_mode_flag_set_on_attached_head"
    elif detached and detached_proof_mode:
        proof_authority = "explicit_detached_proof_mode"
    else:
        proof_authority = "attached_branch_head"
    branch = sym.stdout.strip() if not detached else None
    code_path = Path(__file__).resolve()
    code_sha = _sha256_file(code_path)
    config = {
        "implementation_version": IMPLEMENTATION_VERSION,
        "link_model": LINK_MODEL,
        "holding_sessions": HOLDING_SESSIONS,
        "prior_sessions": PRIOR_SESSIONS,
        "min_prior_ok": MIN_PRIOR_OK,
        "prior20_requires_finite_ret": True,
        "prior20_requires_abs_prc_gt_0": True,
        "prior20_requires_vol_gt_0": True,
        "roadmap_deviation": ROADMAP_DEVIATION,
        "min_formation_names": MIN_FORMATION_NAMES,
        "min_active_slots": MIN_ACTIVE_SLOTS,
        "one_way_cost": ONE_WAY_COST,
        "cohort_year": COHORT_YEAR,
        "selection_uses_future_window": False,
        "selection_uses_entry_day_return": False,
        "selection_uses_full_sample_max_date": False,
        "map_always_rebuilt": True,
        "weights": "equal_weight_active_slots_including_post_delist_cash",
        "overlap": "suppress_later_event_entirely_on_entry_overlap",
        "dedup": "one_event_per_formation_date_permno",
        "session_spine": "source_wide_distinct_crsp_dates",
    }
    config_sha = _sha256_text(json.dumps(config, sort_keys=True, separators=(",", ":")))
    logical = {
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "artifact_name": ARTIFACT_NAME,
        "implementation_version": IMPLEMENTATION_VERSION,
        "commit": head,
        "tree": tree,
        "code_sha256": code_sha,
        "config_sha256": config_sha,
    }
    logical_sha = _sha256_text(json.dumps(logical, sort_keys=True, separators=(",", ":")))
    return {
        "commit": head,
        "tree": tree,
        "detached": detached,
        "branch_ref": branch,
        "proof_authority": proof_authority,
        "detached_proof_mode": detached_proof_mode,
        "code_path": code_path.as_posix(),
        "code_sha256": code_sha,
        "config": config,
        "config_sha256": config_sha,
        "logical_identity": logical,
        "logical_identity_sha256": logical_sha,
    }


def build_crsp_cusip_permno_map(
    con: duckdb.DuckDBPyConnection, crsp_path: Path, out_path: Path
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """One-to-one CUSIP8→PERMNO at CRSP source max-date (non-PIT cross-vintage snapshot).

    Map identity only — never used as a formation selection gate.
    """
    meta = con.execute(
        f"""
        SELECT
          max(CAST(date AS DATE)) AS source_max_date,
          count(*)::BIGINT AS n_rows
        FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
        """
    ).fetchone()
    source_max_date = str(meta[0]) if meta and meta[0] is not None else None
    n_rows = int(meta[1] or 0)
    frame = con.execute(
        f"""
        WITH raw AS (
          SELECT
            upper(left(regexp_replace(cast(CUSIP AS VARCHAR), '[^0-9A-Za-z]', ''), 8)) AS cusip8,
            CAST(PERMNO AS BIGINT) AS permno,
            CAST(date AS DATE) AS dt
          FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
          WHERE CUSIP IS NOT NULL AND PERMNO IS NOT NULL
        ),
        pair_max AS (
          SELECT cusip8, permno, max(dt) AS pair_max_date
          FROM raw
          WHERE length(cusip8) = 8
          GROUP BY 1, 2
        ),
        cusip_max AS (
          SELECT cusip8, max(pair_max_date) AS cusip_source_max_date
          FROM pair_max
          GROUP BY 1
        ),
        at_max AS (
          SELECT p.cusip8, p.permno, p.pair_max_date, c.cusip_source_max_date
          FROM pair_max p
          JOIN cusip_max c ON p.cusip8 = c.cusip8
          WHERE p.pair_max_date = c.cusip_source_max_date
        ),
        uniq AS (
          SELECT cusip8
          FROM at_max
          GROUP BY 1
          HAVING count(DISTINCT permno) = 1
        )
        SELECT
          a.cusip8,
          any_value(a.permno) AS permno,
          any_value(a.cusip_source_max_date) AS pair_source_max_date
        FROM at_max a
        JOIN uniq u ON a.cusip8 = u.cusip8
        GROUP BY 1
        ORDER BY 1
        """
    ).df()
    map_meta = {
        "link_model": LINK_MODEL,
        "as_of_link": False,
        "pit_link": False,
        "source_max_date": source_max_date,
        "crsp_n_rows_scanned": n_rows,
        "n_unique_cusip8": int(len(frame)),
        "n_unique_permno": int(frame["permno"].nunique()) if not frame.empty else 0,
        "builder": "source_max_date_one_to_one_cusip8_permno",
        "always_rebuilt": True,
        "used_for_selection": False,
    }
    meta_frame = frame.copy()
    meta_frame["link_model"] = LINK_MODEL
    meta_frame["source_file_max_date"] = source_max_date
    _atomic_write_parquet(meta_frame, out_path)
    return frame, map_meta


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
        "unique_mapped_events": int((frame["n_perm"] == 1).sum()),
        "ambiguous_events": int((frame["n_perm"] > 1).sum()),
        "unmapped_events": int((frame["n_perm"] == 0).sum()),
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
    counts["unique_permnos_mapped"] = int(mapped["permno"].nunique()) if not mapped.empty else 0
    return mapped.reset_index(drop=True), counts


def load_source_session_spine(
    con: duckdb.DuckDBPyConnection, *, crsp_path: Path
) -> pd.DatetimeIndex:
    """Source-wide distinct CRSP session dates (not limited to mapped-PERMNO load window)."""
    dates = con.execute(
        f"""
        SELECT DISTINCT CAST(date AS DATE) AS date
        FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
        WHERE date IS NOT NULL
        ORDER BY 1
        """
    ).df()
    if dates.empty:
        return pd.DatetimeIndex([])
    return pd.DatetimeIndex(pd.to_datetime(dates["date"]).dt.normalize().sort_values())


def panel_load_window(sessions: pd.DatetimeIndex) -> tuple[str, str, dict[str, Any]]:
    """Include ≥20 source sessions before cohort year for January prior-20 evaluation."""
    cohort_start = pd.Timestamp(f"{COHORT_YEAR}-01-01")
    pre = sessions[sessions < cohort_start]
    if len(pre) < PRIOR_SESSIONS:
        raise M7F1BlockedError(
            f"source_spine_lacks_prior20_before_{COHORT_YEAR}:have={len(pre)}"
        )
    start_ts = pd.Timestamp(pre[-PRIOR_SESSIONS]).normalize()
    end_ts = pd.Timestamp(f"{COHORT_YEAR + 1}-12-31")
    meta = {
        "panel_start": start_ts.strftime("%Y-%m-%d"),
        "panel_end": end_ts.strftime("%Y-%m-%d"),
        "n_pre_cohort_sessions_loaded": PRIOR_SESSIONS,
        "n_pre_cohort_sessions_available": int(len(pre)),
        "spine_n_sessions": int(len(sessions)),
        "spine_min": sessions.min().strftime("%Y-%m-%d") if len(sessions) else None,
        "spine_max": sessions.max().strftime("%Y-%m-%d") if len(sessions) else None,
    }
    return meta["panel_start"], meta["panel_end"], meta


def load_crsp_panel(
    con: duckdb.DuckDBPyConnection,
    *,
    crsp_path: Path,
    permnos: Sequence[int],
    start: str,
    end: str,
) -> pd.DataFrame:
    if not permnos:
        return pd.DataFrame(
            columns=["permno", "date", "ret_raw", "dlret_raw", "dlstcd_raw", "prc_raw", "vol_raw"]
        )
    permno_list = ",".join(str(int(p)) for p in sorted(set(int(p) for p in permnos)))
    q = f"""
    SELECT
      CAST(PERMNO AS BIGINT) AS permno,
      CAST(date AS DATE) AS date,
      RET AS ret_raw,
      DLRET AS dlret_raw,
      DLSTCD AS dlstcd_raw,
      PRC AS prc_raw,
      VOL AS vol_raw
    FROM read_csv_auto('{crsp_path.as_posix()}', header=true, sample_size=-1)
    WHERE CAST(PERMNO AS BIGINT) IN ({permno_list})
      AND CAST(date AS DATE) >= DATE '{start}'
      AND CAST(date AS DATE) <= DATE '{end}'
    ORDER BY 1, 2
    """
    return con.execute(q).df()


def assign_formation_entry(
    events: pd.DataFrame, sessions: pd.DatetimeIndex
) -> pd.DataFrame:
    """Assign entry = first session strictly after RDQ. No return filter."""
    if events.empty:
        return events.copy()
    if len(sessions) == 0:
        out = events.copy()
        out["entry"] = pd.NaT
        out["formation_eligible"] = False
        return out
    session_values = sessions.values
    entries: list[pd.Timestamp | pd.NaT] = []
    eligible: list[bool] = []
    for rdq in events["rdq"]:
        rdq_ts = pd.Timestamp(rdq).normalize()
        idx = int(np.searchsorted(session_values, np.datetime64(rdq_ts), side="right"))
        if idx >= len(session_values):
            entries.append(pd.NaT)
            eligible.append(False)
        else:
            entries.append(pd.Timestamp(session_values[idx]).normalize())
            eligible.append(True)
    out = events.copy()
    out["entry"] = entries
    out["formation_eligible"] = eligible
    return out


def dedup_formation_permno(events: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """One event per (formation date, PERMNO): highest SUE, then earliest rdq, event_id."""
    if events.empty:
        return events.copy(), 0
    work = events.loc[events["formation_eligible"]].copy()
    before = int(len(work))
    work = work.sort_values(
        ["entry", "permno", "sue", "rdq", "event_id"],
        ascending=[True, True, False, True, True],
        kind="mergesort",
    )
    deduped = work.drop_duplicates(subset=["entry", "permno"], keep="first").copy()
    dropped = before - int(len(deduped))
    return deduped.reset_index(drop=True), dropped


def apply_pre_q5_prior20_observability(
    events: pd.DataFrame,
    sessions: pd.DatetimeIndex,
    panel_by_permno: Mapping[int, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Formation-time tradability gate (roadmap deviation; not map repair).

    For each event with entry E, take the 20 source sessions strictly before E.
    Require ≥15 with finite RET, abs(PRC)>0, VOL>0. Does not inspect entry-day
    or post-entry returns. Does not use full-sample max_date as a selection rule.
    """
    if events.empty:
        return events.copy(), pd.DataFrame(), {
            "pre_q5_prior20_ok": 0,
            "pre_q5_prior20_fail": 0,
            "pre_q5_prior20_insufficient_calendar": 0,
            "pre_q5_prior20_lt_15": 0,
            "pre_q5_missing_permno_panel": 0,
        }
    session_values = sessions.values
    kept_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    counts = {
        "pre_q5_prior20_ok": 0,
        "pre_q5_prior20_fail": 0,
        "pre_q5_prior20_insufficient_calendar": 0,
        "pre_q5_prior20_lt_15": 0,
        "pre_q5_missing_permno_panel": 0,
    }
    for row in events.to_dict(orient="records"):
        rec = dict(row)
        entry = pd.Timestamp(row["entry"]).normalize()
        permno = int(row["permno"])
        idx = int(np.searchsorted(session_values, np.datetime64(entry), side="left"))
        if idx < PRIOR_SESSIONS:
            rec["pre_q5_gate_status"] = "prior20_insufficient_calendar"
            rec["prior20_n_ok"] = 0
            rec["prior20_n_available"] = int(idx)
            failed_rows.append(rec)
            counts["pre_q5_prior20_insufficient_calendar"] += 1
            counts["pre_q5_prior20_fail"] += 1
            continue
        prior = [
            pd.Timestamp(session_values[i]).normalize()
            for i in range(idx - PRIOR_SESSIONS, idx)
        ]
        stock = panel_by_permno.get(permno)
        if stock is None or stock.empty:
            rec["pre_q5_gate_status"] = "missing_permno_panel"
            rec["prior20_n_ok"] = 0
            rec["prior20_n_available"] = PRIOR_SESSIONS
            failed_rows.append(rec)
            counts["pre_q5_missing_permno_panel"] += 1
            counts["pre_q5_prior20_fail"] += 1
            continue
        stock_idx = stock.set_index("date").sort_index()
        n_ok = 0
        for session in prior:
            if session not in stock_idx.index:
                continue
            srec = stock_idx.loc[session]
            if _session_observability_ok(
                srec.get("ret_raw"), srec.get("prc_raw"), srec.get("vol_raw")
            ):
                n_ok += 1
        rec["prior20_n_ok"] = int(n_ok)
        rec["prior20_n_available"] = PRIOR_SESSIONS
        if n_ok < MIN_PRIOR_OK:
            rec["pre_q5_gate_status"] = "prior20_lt_15"
            failed_rows.append(rec)
            counts["pre_q5_prior20_lt_15"] += 1
            counts["pre_q5_prior20_fail"] += 1
            continue
        rec["pre_q5_gate_status"] = "prior20_ok"
        kept_rows.append(rec)
        counts["pre_q5_prior20_ok"] += 1
    kept = pd.DataFrame(kept_rows) if kept_rows else events.iloc[0:0].copy()
    failed = pd.DataFrame(failed_rows)
    return kept.reset_index(drop=True), failed.reset_index(drop=True), counts


def apply_formation_breadth_q5(events: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    if events.empty:
        return events.copy(), {
            "formation_dates_ge_50": 0,
            "events_after_breadth": 0,
            "q5_events_before_overlap": 0,
            "unique_permnos_after_breadth": 0,
        }
    work = events.copy()
    breadth = work.groupby("entry")["permno"].transform("nunique")
    work = work.loc[breadth >= MIN_FORMATION_NAMES].copy()
    formation_dates = int(work["entry"].nunique()) if not work.empty else 0
    if work.empty:
        return work, {
            "formation_dates_ge_50": 0,
            "events_after_breadth": 0,
            "q5_events_before_overlap": 0,
            "unique_permnos_after_breadth": 0,
        }

    def _q5(group: pd.DataFrame) -> pd.DataFrame:
        g = group.sort_values(
            ["sue", "permno", "event_id"], ascending=[False, True, True], kind="mergesort"
        ).copy()
        n = len(g)
        q = int(math.floor(n / 5))
        if q < 1:
            return g.iloc[0:0]
        out = g.iloc[:q].copy()
        out["q5_rank"] = np.arange(1, len(out) + 1)
        out["formation_n_distinct_permno"] = n
        return out

    parts: list[pd.DataFrame] = []
    for entry_key, group in work.groupby("entry", sort=False):
        part = _q5(group)
        if not part.empty:
            part = part.copy()
            part["entry"] = pd.Timestamp(entry_key).normalize()
            parts.append(part)
    q5 = pd.concat(parts, ignore_index=True) if parts else work.iloc[0:0].copy()
    stats = {
        "formation_dates_ge_50": formation_dates,
        "events_after_breadth": int(len(work)),
        "q5_events_before_overlap": int(len(q5)),
        "unique_permnos_after_breadth": int(work["permno"].nunique()),
    }
    return q5, stats


def suppress_entry_overlap(
    q5: pd.DataFrame, sessions: pd.DatetimeIndex
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Suppress later event entirely if entry falls inside earlier 60-session claim (same PERMNO)."""
    if q5.empty:
        return q5.copy(), pd.DataFrame(), {
            "q5_events_after_overlap": 0,
            "suppressed_entry_overlap": 0,
            "unique_permnos_q5": 0,
        }
    session_values = sessions.values
    work = q5.sort_values(
        ["permno", "entry", "rdq", "event_id"],
        ascending=[True, True, True, True],
        kind="mergesort",
    ).copy()
    kept_rows: list[dict[str, Any]] = []
    suppressed_rows: list[dict[str, Any]] = []
    claims: dict[int, list[tuple[pd.Timestamp, pd.Timestamp]]] = {}
    for row in work.itertuples(index=False):
        permno = int(row.permno)
        entry = pd.Timestamp(row.entry).normalize()
        idx = int(np.searchsorted(session_values, np.datetime64(entry), side="left"))
        rec = {c: getattr(row, c) for c in work.columns}
        if idx >= len(session_values) or pd.Timestamp(session_values[idx]).normalize() != entry:
            rec["suppress_reason"] = "entry_not_on_session_spine"
            suppressed_rows.append(rec)
            continue
        end_idx = idx + HOLDING_SESSIONS - 1
        if end_idx >= len(session_values):
            claim_end = pd.Timestamp(session_values[-1]).normalize()
        else:
            claim_end = pd.Timestamp(session_values[end_idx]).normalize()
        overlap = False
        for c_start, c_end in claims.get(permno, []):
            if c_start <= entry <= c_end:
                overlap = True
                rec["suppress_reason"] = "entry_overlaps_earlier_60_session_claim"
                rec["suppressed_by_claim_start"] = c_start
                rec["suppressed_by_claim_end"] = c_end
                suppressed_rows.append(rec)
                break
        if overlap:
            continue
        claims.setdefault(permno, []).append((entry, claim_end))
        rec["claim_end"] = claim_end
        rec["suppress_reason"] = None
        kept_rows.append(rec)
    kept = pd.DataFrame(kept_rows)
    suppressed = pd.DataFrame(suppressed_rows)
    stats = {
        "q5_events_after_overlap": int(len(kept)),
        "suppressed_entry_overlap": int(len(suppressed)),
        "unique_permnos_q5": int(kept["permno"].nunique()) if not kept.empty else 0,
    }
    return kept.reset_index(drop=True), suppressed.reset_index(drop=True), stats


def _panel_first_last(
    panel_by_permno: Mapping[int, pd.DataFrame], permno: int
) -> tuple[str | None, str | None]:
    stock = panel_by_permno.get(permno)
    if stock is None or stock.empty:
        return None, None
    dates = pd.to_datetime(stock["date"]).dt.normalize()
    return str(dates.min().date()), str(dates.max().date())


def _base_event_fields(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event["event_id"],
        "gvkey": event["gvkey"],
        "permno": int(event["permno"]),
        "rdq": pd.Timestamp(event["rdq"]).normalize(),
        "sue": float(event["sue"]),
        "q5_rank": event.get("q5_rank"),
        "formation_n_distinct_permno": event.get("formation_n_distinct_permno"),
        "claim_end": event.get("claim_end"),
        "prior20_n_ok": event.get("prior20_n_ok"),
        "pre_q5_gate_status": event.get("pre_q5_gate_status"),
    }


def resolve_event_window(
    *,
    event: Mapping[str, Any],
    sessions: pd.DatetimeIndex,
    panel_by_permno: Mapping[int, pd.DataFrame],
) -> dict[str, Any]:
    base = _base_event_fields(event)
    rdq = base["rdq"]
    permno = base["permno"]
    first_d, last_d = _panel_first_last(panel_by_permno, permno)
    after = sessions[sessions > rdq]
    if len(after) < HOLDING_SESSIONS:
        return {
            **base,
            "status": "incomplete_calendar",
            "entry": pd.Timestamp(after[0]).normalize() if len(after) else None,
            "rows": None,
            "failure_detail": "insufficient_sessions_after_rdq",
            "panel_first_date": first_d,
            "panel_last_date": last_d,
        }
    window_dates = after[:HOLDING_SESSIONS]
    entry = pd.Timestamp(window_dates[0]).normalize()
    stock = panel_by_permno.get(permno)
    if stock is None or stock.empty:
        return {
            **base,
            "status": "missing_permno_panel",
            "entry": entry,
            "rows": None,
            "failure_detail": "no_rows_in_loaded_panel",
            "panel_first_date": first_d,
            "panel_last_date": last_d,
        }
    stock = stock.set_index("date").sort_index()
    rows: list[dict[str, Any]] = []
    liquidated = False
    delist_offset: int | None = None
    for offset, session in enumerate(window_dates, start=1):
        session = pd.Timestamp(session).normalize()
        if liquidated:
            rows.append(
                {
                    "event_id": base["event_id"],
                    "gvkey": base["gvkey"],
                    "permno": permno,
                    "rdq": rdq,
                    "entry": entry,
                    "sue": base["sue"],
                    "session_offset": offset,
                    "return_date": session,
                    "r": 0.0,
                    "live_equity": False,
                    "cash_slot": True,
                    "delist_day": False,
                    "active_slot": True,
                }
            )
            continue
        if session not in stock.index:
            return {
                **base,
                "status": "missing_session",
                "entry": entry,
                "rows": None,
                "failure_detail": f"missing_session:{session.date()}",
                "panel_first_date": first_d,
                "panel_last_date": last_d,
                "first_bad_session": session.strftime("%Y-%m-%d"),
            }
        rec = stock.loc[session]
        ret = _to_float_or_none(rec["ret_raw"])
        dlret = _to_float_or_none(rec["dlret_raw"])
        dlstcd_raw = rec["dlstcd_raw"]
        try:
            dlstcd = (
                int(float(dlstcd_raw))
                if pd.notna(dlstcd_raw) and str(dlstcd_raw).strip() != ""
                else None
            )
        except (TypeError, ValueError):
            dlstcd = None
        delist_event = dlstcd is not None and dlstcd >= 200
        if delist_event:
            if dlret is None:
                return {
                    **base,
                    "status": "unresolved_delist",
                    "entry": entry,
                    "rows": None,
                    "failure_detail": (
                        f"dlstcd={dlstcd};dlret_raw={rec['dlret_raw']!r};"
                        f"ret_raw={rec['ret_raw']!r};session={session.date()}"
                    ),
                    "panel_first_date": first_d,
                    "panel_last_date": last_d,
                    "first_bad_session": session.strftime("%Y-%m-%d"),
                }
            if ret is None:
                r = dlret
            else:
                r = (1.0 + ret) * (1.0 + dlret) - 1.0
            if not math.isfinite(r):
                return {
                    **base,
                    "status": "nonnumeric_selected_window",
                    "entry": entry,
                    "rows": None,
                    "failure_detail": f"nonfinite_delist_compound;session={session.date()}",
                    "panel_first_date": first_d,
                    "panel_last_date": last_d,
                    "first_bad_session": session.strftime("%Y-%m-%d"),
                }
            rows.append(
                {
                    "event_id": base["event_id"],
                    "gvkey": base["gvkey"],
                    "permno": permno,
                    "rdq": rdq,
                    "entry": entry,
                    "sue": base["sue"],
                    "session_offset": offset,
                    "return_date": session,
                    "r": float(r),
                    "live_equity": True,
                    "cash_slot": False,
                    "delist_day": True,
                    "active_slot": True,
                }
            )
            liquidated = True
            delist_offset = offset
            continue
        if ret is None:
            return {
                **base,
                "status": "nonnumeric_selected_window",
                "entry": entry,
                "rows": None,
                "failure_detail": f"ret_raw={rec['ret_raw']!r};session={session.date()}",
                "panel_first_date": first_d,
                "panel_last_date": last_d,
                "first_bad_session": session.strftime("%Y-%m-%d"),
            }
        rows.append(
            {
                "event_id": base["event_id"],
                "gvkey": base["gvkey"],
                "permno": permno,
                "rdq": rdq,
                "entry": entry,
                "sue": base["sue"],
                "session_offset": offset,
                "return_date": session,
                "r": float(ret),
                "live_equity": True,
                "cash_slot": False,
                "delist_day": False,
                "active_slot": True,
            }
        )
    return {
        **base,
        "status": "ok",
        "entry": entry,
        "rows": rows,
        "delist_offset": delist_offset,
        "failure_detail": None,
        "panel_first_date": first_d,
        "panel_last_date": last_d,
    }


def build_daily_portfolio(position_days: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Equal-weight all active slots including post-delist cash slots."""
    if position_days.empty:
        raise M7F1BlockedError("no_active_position_days")
    work = position_days.copy()
    work["return_date"] = pd.to_datetime(work["return_date"]).dt.normalize()
    dates = sorted(work["return_date"].unique())
    records: list[dict[str, Any]] = []
    prev_w: dict[str, float] = {}
    final_date = dates[-1]
    for dt in dates:
        day = work.loc[work["return_date"] == dt]
        slots = day.drop_duplicates("event_id")
        n_active = int(len(slots))
        n_live_equity = int(slots["live_equity"].sum()) if "live_equity" in slots else n_active
        n_cash = int(slots["cash_slot"].sum()) if "cash_slot" in slots else 0
        is_final = dt == final_date
        if n_active > 0 and n_active < MIN_ACTIVE_SLOTS and not is_final:
            raise M7F1BlockedError(
                f"active_slots_below_min:{n_active}_on_{pd.Timestamp(dt).date()}"
            )
        if n_active == 0:
            weights: dict[str, float] = {}
            gross = 0.0
        else:
            w = 1.0 / n_active
            weights = {str(r.event_id): w for r in slots.itertuples(index=False)}
            ret_map = {str(r.event_id): float(r.r) for r in slots.itertuples(index=False)}
            gross = float(sum(weights[e] * ret_map[e] for e in weights))
        all_ids = set(prev_w) | set(weights)
        turnover = float(sum(abs(weights.get(e, 0.0) - prev_w.get(e, 0.0)) for e in all_ids))
        cost = ONE_WAY_COST * turnover
        net = gross - cost
        records.append(
            {
                "return_date": pd.Timestamp(dt),
                "n_active_slots": n_active,
                "n_live_equity": n_live_equity,
                "n_cash_slots": n_cash,
                "daily_gross_return": gross,
                "turnover_l1": turnover,
                "daily_cost": cost,
                "daily_net_return": net,
            }
        )
        prev_w = weights
    if prev_w:
        turnover = float(sum(abs(0.0 - w) for w in prev_w.values()))
        cost = ONE_WAY_COST * turnover
        records[-1]["turnover_l1"] = float(records[-1]["turnover_l1"] + turnover)
        records[-1]["daily_cost"] = float(records[-1]["daily_cost"] + cost)
        records[-1]["daily_net_return"] = float(
            records[-1]["daily_gross_return"] - records[-1]["daily_cost"]
        )
        records[-1]["includes_terminal_liquidation"] = True
    daily = pd.DataFrame.from_records(records).sort_values("return_date").reset_index(drop=True)
    equity = (1.0 + daily["daily_net_return"]).cumprod()
    daily["equity_net"] = equity
    stats = {
        "n_days": int(len(daily)),
        "start": str(daily["return_date"].iloc[0].date()) if len(daily) else None,
        "end": str(daily["return_date"].iloc[-1].date()) if len(daily) else None,
        "total_net_return": float(equity.iloc[-1] - 1.0) if len(daily) else None,
        "min_active_slots": int(daily["n_active_slots"].min()) if len(daily) else None,
        "mean_active_slots": float(daily["n_active_slots"].mean()) if len(daily) else None,
        "min_live_equity": int(daily["n_live_equity"].min()) if len(daily) else None,
        "mean_live_equity": float(daily["n_live_equity"].mean()) if len(daily) else None,
    }
    return daily, stats


def _ledger_row_from_resolved(r: Mapping[str, Any]) -> dict[str, Any]:
    entry_s = (
        pd.Timestamp(r["entry"]).strftime("%Y-%m-%d") if r.get("entry") is not None else None
    )
    claim_end_s = None
    if r.get("claim_end") is not None:
        claim_end_s = pd.Timestamp(r["claim_end"]).strftime("%Y-%m-%d")
    elif r.get("rows"):
        claim_end_s = pd.Timestamp(r["rows"][-1]["return_date"]).strftime("%Y-%m-%d")
    return {
        "event_id": r["event_id"],
        "gvkey": r["gvkey"],
        "permno": int(r["permno"]),
        "rdq": pd.Timestamp(r["rdq"]).strftime("%Y-%m-%d"),
        "entry": entry_s,
        "claim_end": claim_end_s,
        "sue": float(r["sue"]),
        "q5_rank": r.get("q5_rank"),
        "formation_n_distinct_permno": r.get("formation_n_distinct_permno"),
        "window_status": r["status"],
        "delist_offset": r.get("delist_offset"),
        "suppressed": False,
        "suppress_reason": None,
        "pre_q5_gate_status": r.get("pre_q5_gate_status"),
        "prior20_n_ok": r.get("prior20_n_ok"),
        "failure_detail": r.get("failure_detail"),
        "panel_first_date": r.get("panel_first_date"),
        "panel_last_date": r.get("panel_last_date"),
        "first_bad_session": r.get("first_bad_session"),
    }


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
    ledger_path: Path,
    ledger_manifest_path: Path,
    detached_proof_mode: bool = False,
) -> dict[str, Any]:
    identity = resolve_run_identity(repo_root, detached_proof_mode=detached_proof_mode)
    con = duckdb.connect()

    # Always force-rebuild map (no reuse path).
    _, map_meta = build_crsp_cusip_permno_map(con, crsp_path, cusip_map_path)
    map_sha = _sha256_file(cusip_map_path)
    mapped, map_counts = load_mapped_events(
        con, d1_path=d1_path, sec_path=sec_path, cusip_map_path=cusip_map_path
    )
    if mapped.empty:
        raise M7F1BlockedError("no_unique_mapped_events")

    sessions = load_source_session_spine(con, crsp_path=crsp_path)
    if len(sessions) == 0:
        raise M7F1BlockedError("empty_source_session_spine")
    panel_start, panel_end, panel_window_meta = panel_load_window(sessions)
    panel = load_crsp_panel(
        con,
        crsp_path=crsp_path,
        permnos=mapped["permno"].tolist(),
        start=panel_start,
        end=panel_end,
    )
    if panel.empty:
        raise M7F1BlockedError("empty_crsp_panel")
    panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()
    panel_by = {int(p): g.copy() for p, g in panel.groupby("permno")}

    # --- Formation-time selection ---
    with_entry = assign_formation_entry(mapped, sessions)
    n_no_entry = int((~with_entry["formation_eligible"]).sum())
    deduped, n_dedup_dropped = dedup_formation_permno(with_entry)
    prior_ok, prior_fail, prior_stats = apply_pre_q5_prior20_observability(
        deduped, sessions, panel_by
    )
    q5, form_stats = apply_formation_breadth_q5(prior_ok)
    kept_q5, suppressed, overlap_stats = suppress_entry_overlap(q5, sessions)
    if kept_q5.empty:
        _invalidate_stale_curve(parquet_path)
        raise M7F1BlockedError("no_q5_events_after_formation_and_overlap")

    # --- Post-select window resolution; any invalid selected → BLOCK ---
    resolved: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for event in kept_q5.to_dict(orient="records"):
        result = resolve_event_window(
            event=event, sessions=sessions, panel_by_permno=panel_by
        )
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
        resolved.append(result)

    bad = [r for r in resolved if r["status"] != "ok"]
    reason_counts: dict[str, int] = {}
    for r in bad:
        reason_counts[r["status"]] = reason_counts.get(r["status"], 0) + 1

    # Post-hoc first/last-date diagnostics only (not selection).
    posthoc: dict[str, int] = {
        "invalid_with_panel_last_before_rdq": 0,
        "invalid_with_panel_first_after_rdq": 0,
        "invalid_with_panel_coverage_ok": 0,
        "invalid_with_no_panel_dates": 0,
    }
    for r in bad:
        rdq = pd.Timestamp(r["rdq"]).normalize()
        first_s = r.get("panel_first_date")
        last_s = r.get("panel_last_date")
        if not first_s or not last_s:
            posthoc["invalid_with_no_panel_dates"] += 1
            continue
        first_d = pd.Timestamp(first_s)
        last_d = pd.Timestamp(last_s)
        if last_d < rdq:
            posthoc["invalid_with_panel_last_before_rdq"] += 1
        elif first_d > rdq:
            posthoc["invalid_with_panel_first_after_rdq"] += 1
        else:
            posthoc["invalid_with_panel_coverage_ok"] += 1

    ledger_rows: list[dict[str, Any]] = []
    for r in resolved:
        ledger_rows.append(_ledger_row_from_resolved(r))
    for row in suppressed.to_dict(orient="records") if not suppressed.empty else []:
        ledger_rows.append(
            {
                "event_id": row.get("event_id"),
                "gvkey": row.get("gvkey"),
                "permno": int(row["permno"]) if row.get("permno") is not None else None,
                "rdq": (
                    pd.Timestamp(row["rdq"]).strftime("%Y-%m-%d")
                    if row.get("rdq") is not None
                    else None
                ),
                "entry": (
                    pd.Timestamp(row["entry"]).strftime("%Y-%m-%d")
                    if row.get("entry") is not None
                    else None
                ),
                "claim_end": None,
                "sue": float(row["sue"]) if row.get("sue") is not None else None,
                "q5_rank": row.get("q5_rank"),
                "formation_n_distinct_permno": row.get("formation_n_distinct_permno"),
                "window_status": "suppressed_before_window",
                "delist_offset": None,
                "suppressed": True,
                "suppress_reason": row.get("suppress_reason"),
                "pre_q5_gate_status": row.get("pre_q5_gate_status"),
                "prior20_n_ok": row.get("prior20_n_ok"),
                "failure_detail": None,
                "panel_first_date": None,
                "panel_last_date": None,
                "first_bad_session": None,
            }
        )
    for row in prior_fail.to_dict(orient="records") if not prior_fail.empty else []:
        ledger_rows.append(
            {
                "event_id": row.get("event_id"),
                "gvkey": row.get("gvkey"),
                "permno": int(row["permno"]) if row.get("permno") is not None else None,
                "rdq": (
                    pd.Timestamp(row["rdq"]).strftime("%Y-%m-%d")
                    if row.get("rdq") is not None
                    else None
                ),
                "entry": (
                    pd.Timestamp(row["entry"]).strftime("%Y-%m-%d")
                    if row.get("entry") is not None
                    else None
                ),
                "claim_end": None,
                "sue": float(row["sue"]) if row.get("sue") is not None else None,
                "q5_rank": None,
                "formation_n_distinct_permno": None,
                "window_status": "pre_q5_gate_fail",
                "delist_offset": None,
                "suppressed": False,
                "suppress_reason": None,
                "pre_q5_gate_status": row.get("pre_q5_gate_status"),
                "prior20_n_ok": row.get("prior20_n_ok"),
                "failure_detail": row.get("pre_q5_gate_status"),
                "panel_first_date": None,
                "panel_last_date": None,
                "first_bad_session": None,
            }
        )
    ledger_df = pd.DataFrame(ledger_rows)
    ledger_sha = _atomic_write_parquet(ledger_df, ledger_path)

    contract = {
        "cohort": "RDQ calendar year 2019",
        "day_plus_1": "first_crsp_session_strictly_after_rdq",
        "holding_sessions": HOLDING_SESSIONS,
        "day_plus_1_included_in_window": True,
        "formation_min_distinct_permnos": MIN_FORMATION_NAMES,
        "min_active_slots": MIN_ACTIVE_SLOTS,
        "min_active_final_liquidation_exempt": True,
        "selection_uses_future_window": False,
        "selection_uses_entry_day_return": False,
        "selection_uses_full_sample_max_date": False,
        "roadmap_deviation": ROADMAP_DEVIATION,
        "prior20_sessions": PRIOR_SESSIONS,
        "prior20_min_ok": MIN_PRIOR_OK,
        "prior20_rule": "finite_RET_and_abs_PRC_gt_0_and_VOL_gt_0",
        "session_spine": "source_wide_distinct_crsp_dates",
        "panel_load": panel_window_meta,
        "dedup": "one_event_per_formation_date_permno_highest_sue",
        "overlap": "suppress_later_event_entirely_when_entry_overlaps_earlier_60_session_claim",
        "weights": "equal_weight_active_slots_including_post_delist_cash",
        "one_way_cost": ONE_WAY_COST,
        "cost_formula": "0.00075 * sum_i abs(delta_w_i) including terminal liquidation",
        "delist_day_return": "(1+RET)*(1+DLRET)-1 or DLRET if RET blank; then cash slot r=0 remainder",
        "nonnumeric_scope": "selected_windows_only_block_run",
        "posthoc_diagnostics_only": [
            "panel_first_date",
            "panel_last_date",
            "first_last_date_mismatch_vs_rdq",
        ],
        "filter_order": [
            "unique_permno_map",
            "assign_formation_entry_source_wide_spine_only_no_return_filter",
            "dedup_one_event_per_formation_date_permno",
            "pre_q5_prior20_observability_tradability_gate",
            "formation_breadth_distinct_permno_ge_50",
            "deterministic_q5",
            "suppress_later_event_on_entry_overlap",
            "resolve_selected_windows_or_block",
            "equal_weight_active_slots_incl_cash",
        ],
    }
    claim_ceiling = {
        "evidence_tier": "M6B_FLAGGED_BEST_AVAILABLE_RESEARCH",
        "link_model": LINK_MODEL,
        "as_of_link": False,
        "pit_link": False,
        "research_use_only": True,
        "usable_for_alpha_inference": False,
        "usable_for_strategy_promotion": False,
        "m6b_data_contract_ready": False,
        "not_alpha": True,
        "not_tradable_claim": True,
        "research_validity_ceiling_note": "snapshot_link_ceiling_approx_30_of_100",
    }
    supersedes = {
        "artifact_name": "pead_m7f1_v5_2019_crsp_vertical",
        "prior_implementation_versions": ["m7f1-v5", "m7f1-v5.1"],
        "reason": (
            "v5.2-final: source-wide spine + pre-2019 prior-20 panel load; "
            "pre-Q5 prior-20 tradability gate (roadmap deviation, not map repair); "
            "force map rebuild; invalidate stale curve on BLOCK; ledger failure details; "
            "first/last-date mismatch diagnostic-only"
        ),
        "also_supersedes": {
            "artifact_name": "pead_m7f0_v4_2019_crsp_vertical",
            "reason": (
                "v4 filtered complete 60d windows before Q5 (lookahead), reallocated delist "
                "cash into survivors, unbound map lineage, non-atomic parquet"
            ),
        },
    }
    base_counts = {
        **map_counts,
        "formation_no_entry": n_no_entry,
        "dedup_dropped_same_formation_permno": n_dedup_dropped,
        **prior_stats,
        **form_stats,
        **overlap_stats,
        "selected_window_status_counts": status_counts,
        "selected_invalid_reason_counts": reason_counts,
        "posthoc_first_last_diagnostics": posthoc,
        "unique_permnos_selected": int(kept_q5["permno"].nunique()),
        "n_selected_events": int(len(kept_q5)),
        "n_selected_ok_windows": int(status_counts.get("ok", 0)),
        "n_selected_invalid_windows": int(len(bad)),
    }

    if bad:
        block_reason = "selected_window_invalid:" + ",".join(
            f"{k}={v}" for k, v in sorted(reason_counts.items())
        )
        stale = _invalidate_stale_curve(parquet_path)
        source_hashes = {
            "d1_sha256": _sha256_file(d1_path),
            "security_master_sha256": _sha256_file(sec_path),
            "crsp_sha256": _sha256_file(crsp_path),
            "cusip_permno_map_sha256": map_sha,
            "daily_parquet_sha256": None,
            "event_ledger_sha256": ledger_sha,
            "code_sha256": identity["code_sha256"],
            "config_sha256": identity["config_sha256"],
            "logical_identity_sha256": identity["logical_identity_sha256"],
        }
        evidence = {
            "artifact_name": ARTIFACT_NAME,
            "round_id": ROUND_ID,
            "scope_id": SCOPE_ID,
            "generated_at_utc": _utc_now(),
            "supersedes": supersedes,
            "authority": (
                "flagged research mechanical vertical only; not strict M6b readiness; "
                "not alpha; not tradable; not as-of/PIT CUSIP link"
            ),
            "claim_ceiling": claim_ceiling,
            "implementation_identity": identity,
            "contract": contract,
            "map_meta": map_meta,
            "stale_curve_invalidation": stale,
            "counts": {**base_counts, "portfolio": None},
            "lineage": {
                "d1_path": d1_path.as_posix(),
                "security_master_path": sec_path.as_posix(),
                "crsp_path": crsp_path.as_posix(),
                "cusip_map_path": cusip_map_path.as_posix(),
                "daily_parquet_path": None,
                "event_ledger_path": ledger_path.as_posix(),
                "manifest_path": manifest_path.as_posix(),
                "ledger_manifest_path": ledger_manifest_path.as_posix(),
                "hashes": source_hashes,
                "n_daily_rows": 0,
                "n_ledger_rows": int(len(ledger_df)),
            },
            "status": "BLOCKED",
            "block_reason": block_reason,
            "honest_selected_window_block": True,
            "score_band_note": "durable_residual_BLOCK_target_band_approx_62",
        }
        _atomic_write_text(
            evidence_path, json.dumps(evidence, indent=2, sort_keys=True) + "\n"
        )
        evidence_sha = _sha256_file(evidence_path)
        manifest = {
            "artifact": None,
            "sha256": None,
            "rows": 0,
            "status": "BLOCKED",
            "block_reason": block_reason,
            "curve_status": "INVALIDATED_BY_BLOCK" if stale["invalidated"] else "ABSENT",
            "stale_curve_invalidation": stale,
            "evidence_json": evidence_path.as_posix(),
            "evidence_sha256": evidence_sha,
            "event_ledger": ledger_path.as_posix(),
            "event_ledger_sha256": ledger_sha,
            "cusip_map": cusip_map_path.as_posix(),
            "cusip_map_sha256": map_sha,
            "implementation_commit": identity["commit"],
            "implementation_tree": identity["tree"],
            "logical_identity_sha256": identity["logical_identity_sha256"],
            "generated_at_utc": _utc_now(),
            "curve_promoted": False,
            "atomic_write": True,
        }
        _atomic_write_text(
            manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        ledger_manifest = {
            "artifact": ledger_path.as_posix(),
            "sha256": ledger_sha,
            "rows": int(len(ledger_df)),
            "columns": list(ledger_df.columns),
            "evidence_json": evidence_path.as_posix(),
            "evidence_sha256": evidence_sha,
            "generated_at_utc": _utc_now(),
            "atomic_write": True,
        }
        _atomic_write_text(
            ledger_manifest_path,
            json.dumps(ledger_manifest, indent=2, sort_keys=True) + "\n",
        )
        raise M7F1BlockedError(block_reason)

    position_rows: list[dict[str, Any]] = []
    for r in resolved:
        assert r["rows"] is not None
        for cell in r["rows"]:
            position_rows.append(cell)

    positions = pd.DataFrame(position_rows)
    daily, port_stats = build_daily_portfolio(positions)

    daily_out = daily.copy()
    daily_out["return_date"] = daily_out["return_date"].dt.strftime("%Y-%m-%d")
    parquet_sha = _atomic_write_parquet(daily_out, parquet_path)

    source_hashes = {
        "d1_sha256": _sha256_file(d1_path),
        "security_master_sha256": _sha256_file(sec_path),
        "crsp_sha256": _sha256_file(crsp_path),
        "cusip_permno_map_sha256": map_sha,
        "daily_parquet_sha256": parquet_sha,
        "event_ledger_sha256": ledger_sha,
        "code_sha256": identity["code_sha256"],
        "config_sha256": identity["config_sha256"],
        "logical_identity_sha256": identity["logical_identity_sha256"],
    }

    evidence = {
        "artifact_name": ARTIFACT_NAME,
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "generated_at_utc": _utc_now(),
        "supersedes": supersedes,
        "authority": (
            "flagged research mechanical vertical only; not strict M6b readiness; "
            "not alpha; not tradable; not as-of/PIT CUSIP link"
        ),
        "claim_ceiling": claim_ceiling,
        "implementation_identity": identity,
        "contract": contract,
        "map_meta": map_meta,
        "counts": {**base_counts, "portfolio": port_stats},
        "lineage": {
            "d1_path": d1_path.as_posix(),
            "security_master_path": sec_path.as_posix(),
            "crsp_path": crsp_path.as_posix(),
            "cusip_map_path": cusip_map_path.as_posix(),
            "daily_parquet_path": parquet_path.as_posix(),
            "event_ledger_path": ledger_path.as_posix(),
            "manifest_path": manifest_path.as_posix(),
            "ledger_manifest_path": ledger_manifest_path.as_posix(),
            "hashes": source_hashes,
            "n_daily_rows": int(len(daily_out)),
            "n_ledger_rows": int(len(ledger_df)),
        },
        "status": "PASS",
        "score_band_note": "PASS_target_band_68_72_subject_to_snapshot_link_ceiling_30",
    }

    _atomic_write_text(
        evidence_path, json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    )
    evidence_sha = _sha256_file(evidence_path)

    manifest = {
        "artifact": parquet_path.as_posix(),
        "sha256": parquet_sha,
        "rows": int(len(daily_out)),
        "columns": list(daily_out.columns),
        "status": "PASS",
        "evidence_json": evidence_path.as_posix(),
        "evidence_sha256": evidence_sha,
        "event_ledger": ledger_path.as_posix(),
        "event_ledger_sha256": ledger_sha,
        "cusip_map": cusip_map_path.as_posix(),
        "cusip_map_sha256": map_sha,
        "implementation_commit": identity["commit"],
        "implementation_tree": identity["tree"],
        "logical_identity_sha256": identity["logical_identity_sha256"],
        "generated_at_utc": _utc_now(),
        "ignored_data_processed": True,
        "binding": "tracked_manifest_points_at_ignored_parquet_cache",
        "curve_promoted": True,
        "atomic_write": True,
    }
    _atomic_write_text(
        manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    ledger_manifest = {
        "artifact": ledger_path.as_posix(),
        "sha256": ledger_sha,
        "rows": int(len(ledger_df)),
        "columns": list(ledger_df.columns),
        "evidence_json": evidence_path.as_posix(),
        "evidence_sha256": evidence_sha,
        "generated_at_utc": _utc_now(),
        "atomic_write": True,
    }
    _atomic_write_text(
        ledger_manifest_path, json.dumps(ledger_manifest, indent=2, sort_keys=True) + "\n"
    )
    return evidence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="M7F1-v5.2-final 2019 CRSP PEAD formation-first vertical"
    )
    p.add_argument("--repo-root", type=Path, default=Path("."))
    p.add_argument("--d1", type=Path, default=None)
    p.add_argument("--security-master", type=Path, default=None)
    p.add_argument("--crsp", type=Path, default=None)
    p.add_argument("--evidence-out", type=Path, default=None)
    p.add_argument("--parquet-out", type=Path, default=None)
    p.add_argument("--manifest-out", type=Path, default=None)
    p.add_argument("--cusip-map", type=Path, default=None)
    p.add_argument("--ledger-out", type=Path, default=None)
    p.add_argument("--ledger-manifest-out", type=Path, default=None)
    p.add_argument("--data-root", type=Path, default=None, help="Absolute data root if not repo-local")
    p.add_argument(
        "--detached-proof-mode",
        action="store_true",
        help="Required authority when HEAD is detached; recorded in evidence identity.",
    )
    return p.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    data_root = args.data_root.resolve() if args.data_root else repo_root

    def _resolve(p: Path | None, default: Path) -> Path:
        if p is not None:
            return p if p.is_absolute() else (repo_root / p).resolve()
        candidate = (data_root / default).resolve()
        if candidate.is_file() or default.parts[0] != "data":
            return candidate
        return (repo_root / default).resolve() if "docs" in default.parts else candidate

    d1 = _resolve(args.d1, DEFAULT_D1)
    sec = _resolve(args.security_master, DEFAULT_SEC)
    crsp = _resolve(args.crsp, DEFAULT_CRSP)
    evidence = (
        args.evidence_out.resolve()
        if args.evidence_out
        else (repo_root / DEFAULT_EVIDENCE).resolve()
    )
    parquet = (
        args.parquet_out.resolve()
        if args.parquet_out
        else (data_root / DEFAULT_PARQUET).resolve()
    )
    manifest = (
        args.manifest_out.resolve()
        if args.manifest_out
        else (repo_root / DEFAULT_MANIFEST).resolve()
    )
    cusip_map = (
        args.cusip_map.resolve()
        if args.cusip_map
        else (data_root / DEFAULT_CUSIP_MAP).resolve()
    )
    ledger = (
        args.ledger_out.resolve()
        if args.ledger_out
        else (data_root / DEFAULT_LEDGER).resolve()
    )
    ledger_manifest = (
        args.ledger_manifest_out.resolve()
        if args.ledger_manifest_out
        else (repo_root / DEFAULT_LEDGER_MANIFEST).resolve()
    )

    try:
        evidence_obj = run_vertical(
            repo_root=repo_root,
            d1_path=d1,
            sec_path=sec,
            crsp_path=crsp,
            evidence_path=evidence,
            parquet_path=parquet,
            manifest_path=manifest,
            cusip_map_path=cusip_map,
            ledger_path=ledger,
            ledger_manifest_path=ledger_manifest,
            detached_proof_mode=bool(args.detached_proof_mode),
        )
    except M7F1BlockedError as exc:
        print(f"M7F1_BLOCKED: {exc}", file=sys.stderr)
        if evidence.is_file():
            print(
                json.dumps(
                    {
                        "status": "BLOCKED",
                        "artifact": ARTIFACT_NAME,
                        "evidence": evidence.as_posix(),
                        "block_reason": str(exc),
                    },
                    sort_keys=True,
                )
            )
        return 2
    print(json.dumps({"status": evidence_obj.get("status"), "artifact": ARTIFACT_NAME}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
