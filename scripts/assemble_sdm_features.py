"""
assemble_sdm_features.py — Phase 23 SDM feature assembler
==========================================================
Joins quarterly fundamentals_sdm with daily macro and factor panels using
PIT-safe backward asof joins on published_at and writes
data/processed/features_sdm.parquet.

Usage
-----
  python scripts/assemble_sdm_features.py
  python scripts/assemble_sdm_features.py --dry-run
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger("assemble_sdm_features")

FUNDAMENTALS_PATH = Path("data/processed/fundamentals_sdm.parquet")
MACRO_PATH = Path("data/processed/macro_rates.parquet")
FF_PATH = Path("data/processed/ff_factors.parquet")
SECTOR_MAP_PATH = Path("data/static/sector_map.parquet")
OUT_PATH = Path("data/processed/features_sdm.parquet")
ASOF_TOLERANCE = pd.Timedelta("14d")
FUNDAMENTALS_KEEP_COLS = [
    "permno",
    "gvkey",
    "ticker",
    "published_at",
    "fiscal_date",
    "fyearq",
    "fqtr",
    "rev_accel",
    "inv_vel_traj",
    "gm_traj",
    "op_lev",
    "intang_intensity",
    "q_tot",
]
MACRO_KEEP_COLS = [
    "date",
    "yield_slope_10y2y",
    "credit_spread_hy",
    "real_yield_10y",
    "baa_aaa_spread",
]
FF_KEEP_COLS = [
    "date",
    "mktrf",
    "smb",
    "hml",
    "rmw",
    "cma",
    "umd",
    "rf",
]


def _atomic_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp.parquet")
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
        LOG.info("Written → %s  (%d rows, %d cols)", path, len(df), df.shape[1])
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _normalize_datetime(series: pd.Series) -> pd.Series:
    """Normalize mixed tz/naive datetimes to naive UTC timestamps."""
    return pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None)


def _to_float32(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    for col in cols:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")
    return out


def _assert_asof_sorted(df: pd.DataFrame, key_col: str, side: str) -> None:
    key = _normalize_datetime(df[key_col])
    if key.isna().any():
        raise ValueError(f"{side} asof key {key_col} contains null/invalid datetime values.")
    if not key.is_monotonic_increasing:
        raise ValueError(f"{side} asof key {key_col} must be globally sorted.")


def _build_daily_calendar(
    fundamentals_dates: pd.Series,
    macro_dates: pd.Series,
    ff_dates: pd.Series,
) -> pd.DatetimeIndex:
    """Build a normalized daily calendar for SDM forward-fill expansion."""
    date_candidates = pd.concat(
        [
            _normalize_datetime(fundamentals_dates),
            _normalize_datetime(macro_dates),
            _normalize_datetime(ff_dates),
        ],
        ignore_index=True,
    ).dropna()
    if date_candidates.empty:
        raise ValueError("No valid dates available to build daily SDM calendar.")
    start = pd.Timestamp(date_candidates.min()).normalize()
    end = pd.Timestamp(date_candidates.max()).normalize()
    return pd.date_range(start=start, end=end, freq="D")


def _expand_fundamentals_daily(
    fundamentals: pd.DataFrame,
    calendar: pd.DatetimeIndex,
) -> pd.DataFrame:
    """
    Expand sparse quarterly fundamentals to daily cadence with entity-wise ffill.

    Method A requirement: every entity/date row carries the latest published SDM snapshot.
    """
    work = fundamentals.copy()
    work["date"] = _normalize_datetime(work["published_at"]).dt.normalize()
    work = work.dropna(subset=["date"]).sort_values(["gvkey", "date", "published_at"])
    work = work.drop_duplicates(subset=["gvkey", "date"], keep="last")

    parts: list[pd.DataFrame] = []
    n_entities = int(work["gvkey"].nunique())
    for i, (gvkey, grp) in enumerate(work.groupby("gvkey", sort=False), start=1):
        first_obs = pd.Timestamp(grp["date"].min()).normalize()
        entity_calendar = calendar[calendar >= first_obs]
        if len(entity_calendar) == 0:
            continue
        block = grp.set_index("date").reindex(entity_calendar).ffill()
        block["date"] = entity_calendar
        block["gvkey"] = gvkey
        block = block.reset_index(drop=True)
        parts.append(block)
        if i % 500 == 0:
            LOG.info("Daily SDM expansion progress: %d/%d entities", i, n_entities)

    if not parts:
        raise ValueError("Daily SDM expansion produced no rows.")
    expanded = pd.concat(parts, ignore_index=True)
    expanded = expanded.dropna(subset=["published_at"])
    expanded["date_dt"] = _normalize_datetime(expanded["date"])
    expanded = expanded.sort_values(["date_dt", "gvkey"]).reset_index(drop=True)
    _assert_asof_sorted(expanded, "date_dt", "left-daily")
    return expanded


def _add_industry_medians(frame: pd.DataFrame) -> pd.DataFrame:
    """Precompute industry median context columns (Method B)."""
    out = frame.copy()
    if "industry" not in out.columns:
        out["industry"] = pd.NA
    med_cols = [
        "rev_accel",
        "inv_vel_traj",
        "gm_traj",
        "op_lev",
        "intang_intensity",
        "q_tot",
    ]
    available = [c for c in med_cols if c in out.columns]
    if not available:
        LOG.warning("No SDM columns available for industry median precompute.")
        return out
    if "date" not in out.columns:
        LOG.warning("date column missing; skipping industry median precompute.")
        return out

    for col in available:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out[f"ind_{col}"] = (
            out.groupby(["date", "industry"], dropna=False, sort=False)[col]
            .transform("median")
        )
    return out


def _add_cycle_setup(frame: pd.DataFrame) -> pd.DataFrame:
    """Precompute macro-cycle interaction used by BGM manifold routing."""
    out = frame.copy()
    required = ["yield_slope_10y2y", "rmw", "cma"]
    for col in required:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["CycleSetup"] = out["yield_slope_10y2y"] * out["rmw"] * out["cma"]
    out["cycle_setup"] = out["CycleSetup"]
    return out


def _load_required(path: Path, required_cols: list[str], label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    df = pd.read_parquet(path)
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")
    if df.empty:
        raise ValueError(f"{label} is empty: {path}")
    return df


def _attach_sector_context(df: pd.DataFrame, sector_map_path: Path) -> pd.DataFrame:
    """Attach sector/industry by permno first, then ticker fallback."""
    out = df.copy()
    if "ticker" in out.columns:
        out["ticker"] = out["ticker"].astype(str).str.upper()
    if not sector_map_path.exists():
        LOG.warning("sector_map missing (%s) — sector/industry columns left null.", sector_map_path)
        out["sector"] = pd.NA
        out["industry"] = pd.NA
        return out

    sm = pd.read_parquet(sector_map_path)
    if "ticker" not in sm.columns:
        out["sector"] = pd.NA
        out["industry"] = pd.NA
        LOG.warning("sector_map has no ticker column — sector/industry columns left null.")
        return out

    sm = sm.copy()
    sm["ticker"] = sm["ticker"].astype(str).str.upper()
    has_sector = "sector" in sm.columns
    has_industry = "industry" in sm.columns
    if not has_sector:
        sm["sector"] = pd.NA
    if not has_industry:
        sm["industry"] = pd.NA

    out["sector"] = pd.NA
    out["industry"] = pd.NA
    if "permno" in out.columns and "permno" in sm.columns:
        perm_map = sm.dropna(subset=["permno"]).drop_duplicates("permno")[["permno", "sector", "industry"]]
        out = out.merge(perm_map, on="permno", how="left", suffixes=("", "_perm"))
        out["sector"] = out["sector_perm"]
        out["industry"] = out["industry_perm"]
        out = out.drop(columns=["sector_perm", "industry_perm"], errors="ignore")

    missing_mask = out["sector"].isna()
    if missing_mask.any():
        tic_map = sm.drop_duplicates("ticker")[["ticker", "sector", "industry"]]
        fallback = out.loc[missing_mask, ["ticker"]].merge(tic_map, on="ticker", how="left")
        out.loc[missing_mask, "sector"] = fallback["sector"].to_numpy()
        out.loc[missing_mask, "industry"] = fallback["industry"].to_numpy()

    return out


def _count_rows_nulled_by_tolerance(
    left_keys: pd.Series,
    right_keys: pd.Series,
    tolerance: pd.Timedelta,
) -> dict[str, int]:
    """Count rows that lose a prior match only because of tolerance cutoff."""
    left = pd.DataFrame({"left_key": _normalize_datetime(left_keys)})
    if left["left_key"].isna().any():
        raise ValueError("left asof keys contain null/invalid datetimes for tolerance audit.")
    left = left.sort_values("left_key").reset_index(drop=True)

    right = pd.DataFrame({"right_key": _normalize_datetime(right_keys)})
    right = right.dropna(subset=["right_key"]).sort_values("right_key").reset_index(drop=True)

    if right.empty:
        return {
            "nulled_by_tolerance": 0,
            "no_prior_match": int(len(left)),
            "matched_with_tolerance": 0,
        }

    baseline = pd.merge_asof(
        left,
        right,
        left_on="left_key",
        right_on="right_key",
        direction="backward",
    )
    strict = pd.merge_asof(
        left,
        right,
        left_on="left_key",
        right_on="right_key",
        direction="backward",
        tolerance=tolerance,
    )
    nulled = int((baseline["right_key"].notna() & strict["right_key"].isna()).sum())
    no_prior = int(baseline["right_key"].isna().sum())
    matched = int(strict["right_key"].notna().sum())
    return {
        "nulled_by_tolerance": nulled,
        "no_prior_match": no_prior,
        "matched_with_tolerance": matched,
    }


def assemble_features(
    fundamentals_path: Path = FUNDAMENTALS_PATH,
    macro_path: Path = MACRO_PATH,
    ff_path: Path = FF_PATH,
    sector_map_path: Path = SECTOR_MAP_PATH,
) -> pd.DataFrame:
    fundamentals = _load_required(
        fundamentals_path,
        required_cols=["gvkey", "ticker", "published_at"],
        label="fundamentals_sdm",
    ).copy()
    fund_keep = [c for c in FUNDAMENTALS_KEEP_COLS if c in fundamentals.columns]
    fundamentals = fundamentals[fund_keep].copy()
    fundamentals["ticker"] = fundamentals["ticker"].astype(str).str.upper()
    fundamentals = _to_float32(
        fundamentals,
        cols=["rev_accel", "inv_vel_traj", "gm_traj", "op_lev", "intang_intensity", "q_tot"],
    )
    fundamentals["published_at_dt"] = _normalize_datetime(fundamentals["published_at"])
    fundamentals = fundamentals.sort_values(["published_at_dt", "gvkey"]).reset_index(drop=True)
    _assert_asof_sorted(fundamentals, "published_at_dt", "left-quarterly")

    macro = _load_required(macro_path, required_cols=["date"], label="macro_rates").copy()
    macro_keep = [c for c in MACRO_KEEP_COLS if c in macro.columns]
    macro = macro[macro_keep].copy()
    macro = _to_float32(macro, cols=[c for c in macro.columns if c != "date"])
    macro["macro_at"] = _normalize_datetime(macro["date"])
    macro = macro.rename(columns={"date": "macro_date"})
    macro = macro.sort_values("macro_at").reset_index(drop=True)
    _assert_asof_sorted(macro, "macro_at", "right")

    ff = _load_required(
        ff_path,
        required_cols=["date", "mktrf", "smb", "hml", "rmw", "cma", "umd"],
        label="ff_factors",
    ).copy()
    ff_keep = [c for c in FF_KEEP_COLS if c in ff.columns]
    ff = ff[ff_keep].copy()
    ff = _to_float32(ff, cols=[c for c in ff.columns if c != "date"])
    ff["ff_at"] = _normalize_datetime(ff["date"])
    ff = ff.rename(columns={"date": "ff_date"})
    ff = ff.sort_values("ff_at").reset_index(drop=True)
    _assert_asof_sorted(ff, "ff_at", "right")

    calendar = _build_daily_calendar(
        fundamentals_dates=fundamentals["published_at_dt"],
        macro_dates=macro["macro_at"],
        ff_dates=ff["ff_at"],
    )
    fundamentals_daily = _expand_fundamentals_daily(fundamentals, calendar)
    LOG.info(
        "Expanded fundamentals to daily cadence: %d -> %d rows",
        len(fundamentals),
        len(fundamentals_daily),
    )

    macro_tolerance_stats = _count_rows_nulled_by_tolerance(
        left_keys=fundamentals_daily["date_dt"],
        right_keys=macro["macro_at"],
        tolerance=ASOF_TOLERANCE,
    )
    ff_tolerance_stats = _count_rows_nulled_by_tolerance(
        left_keys=fundamentals_daily["date_dt"],
        right_keys=ff["ff_at"],
        tolerance=ASOF_TOLERANCE,
    )
    LOG.warning(
        "Asof tolerance gate (%s): macro nulled=%d (no_prior=%d, matched=%d); "
        "ff nulled=%d (no_prior=%d, matched=%d)",
        ASOF_TOLERANCE,
        macro_tolerance_stats["nulled_by_tolerance"],
        macro_tolerance_stats["no_prior_match"],
        macro_tolerance_stats["matched_with_tolerance"],
        ff_tolerance_stats["nulled_by_tolerance"],
        ff_tolerance_stats["no_prior_match"],
        ff_tolerance_stats["matched_with_tolerance"],
    )

    merged = pd.merge_asof(
        fundamentals_daily,
        macro,
        left_on="date_dt",
        right_on="macro_at",
        direction="backward",
        tolerance=ASOF_TOLERANCE,
    )
    # merge_asof preserves left order; avoid resorting this large frame to reduce memory pressure.
    _assert_asof_sorted(merged, "date_dt", "left-post-macro")

    merged = pd.merge_asof(
        merged,
        ff,
        left_on="date_dt",
        right_on="ff_at",
        direction="backward",
        tolerance=ASOF_TOLERANCE,
    )
    _assert_asof_sorted(merged, "date_dt", "left-post-ff")

    merged = _attach_sector_context(merged, sector_map_path=sector_map_path)
    merged["date"] = pd.to_datetime(merged["date"], errors="coerce").dt.normalize()
    merged = _add_industry_medians(merged)
    merged = _add_cycle_setup(merged)
    merged = merged.drop(columns=["published_at_dt", "date_dt", "macro_at", "ff_at"], errors="ignore")
    # Preserve PIT-safe asof ordering without materializing another full-frame sort.
    merged = merged.reset_index(drop=True)
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble SDM feature matrix.")
    parser.add_argument("--fundamentals-path", default=str(FUNDAMENTALS_PATH))
    parser.add_argument("--macro-path", default=str(MACRO_PATH))
    parser.add_argument("--ff-path", default=str(FF_PATH))
    parser.add_argument("--sector-map-path", default=str(SECTOR_MAP_PATH))
    parser.add_argument("--output-path", default=str(OUT_PATH))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING"])
    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)
    out = assemble_features(
        fundamentals_path=Path(args.fundamentals_path),
        macro_path=Path(args.macro_path),
        ff_path=Path(args.ff_path),
        sector_map_path=Path(args.sector_map_path),
    )

    LOG.info("Output shape: %d rows × %d cols", *out.shape)
    LOG.info("Date range: %s → %s", out["date"].min(), out["date"].max())
    macro_missing = float(out["yield_slope_10y2y"].isna().mean() * 100) if "yield_slope_10y2y" in out.columns else 100.0
    ff_missing = float(out["mktrf"].isna().mean() * 100) if "mktrf" in out.columns else 100.0
    LOG.info("Null pct — macro signal: %.1f%%, ff mktrf: %.1f%%", macro_missing, ff_missing)

    if args.dry_run:
        preview_cols = [
            "date",
            "ticker",
            "published_at",
            "rev_accel",
            "op_lev",
            "ind_rev_accel",
            "yield_slope_10y2y",
            "credit_spread_hy",
            "mktrf",
            "smb",
            "hml",
            "rmw",
            "cma",
            "CycleSetup",
            "umd",
            "sector",
            "industry",
        ]
        preview_cols = [c for c in preview_cols if c in out.columns]
        print(out[preview_cols].tail(20).to_string(index=False))
        LOG.info("DRY-RUN complete. Row count: %d", len(out))
        return

    _atomic_write(out, Path(args.output_path))


if __name__ == "__main__":
    main()
