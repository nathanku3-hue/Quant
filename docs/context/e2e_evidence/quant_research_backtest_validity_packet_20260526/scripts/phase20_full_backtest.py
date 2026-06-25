from __future__ import annotations

import argparse
import gc
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    psutil = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine  # noqa: E402
from backtests.verify_phase13_walkforward import _build_context  # noqa: E402
from backtests.verify_phase13_walkforward import _load_frame  # noqa: E402
from backtests.verify_phase13_walkforward import _load_price_series_from_parquet  # noqa: E402
from backtests.verify_phase13_walkforward import build_cash_return  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _build_target_weights  # noqa: E402
from scripts.day5_ablation_report import _load_returns_subset  # noqa: E402
from scripts.day5_ablation_report import _resolve_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.company_scorecard import build_phase20_conviction_frame  # noqa: E402
from strategies.production_config import PRODUCTION_CONFIG_V1  # noqa: E402
from strategies.regime_manager import RegimeManager  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_SDM_FEATURES_PATH = PROCESSED_DIR / "features_sdm.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_MACRO_FALLBACK_PATH = PROCESSED_DIR / "macro.parquet"
DEFAULT_MACRO_GATES_PATH = PROCESSED_DIR / "macro_gates.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"

DEFAULT_DELTA_CSV = PROCESSED_DIR / "phase20_round3_delta_vs_c3.csv"
DEFAULT_EQUITY_PNG = PROCESSED_DIR / "phase20_round3_equity_curves.png"
DEFAULT_CASH_CSV = PROCESSED_DIR / "phase20_round3_cash_allocation.csv"
DEFAULT_EXPOSURE_CSV = PROCESSED_DIR / "phase20_round3_top20_exposure.csv"
DEFAULT_SUMMARY_JSON = PROCESSED_DIR / "phase20_round3_summary.json"
DEFAULT_SAMPLE_CSV = PROCESSED_DIR / "phase20_round3_sample_output.csv"
DEFAULT_CRISIS_CSV = PROCESSED_DIR / "phase20_round3_crisis_turnover.csv"

CASH_COL = "__CASH__"
BIL_PERMNO = 92027
CRISIS_WINDOWS = [
    ("COVID_CRASH", "2020-02-19", "2020-03-23"),
    ("COVID_VOLATILITY", "2020-03-01", "2020-04-30"),
    ("INFLATION_SPIKE", "2022-01-03", "2022-06-16"),
    ("BEAR_MARKET", "2022-01-03", "2022-12-31"),
]
DEFERRED_OPEN_RISK = (
    "hard-gate transitions do not include liquidity_air_pocket, "
    "credit_freeze, momentum_crowding"
)

SDM_CORE_COLUMNS: tuple[str, ...] = (
    "ticker",
    "published_at",
    "rev_accel",
    "inv_vel_traj",
    "gm_traj",
    "op_lev",
    "intang_intensity",
    "q_tot",
    "rmw",
    "cma",
    "yield_slope_10y2y",
    "CycleSetup",
    "cycle_setup",
    "ind_rev_accel",
    "ind_inv_vel_traj",
    "ind_gm_traj",
    "ind_op_lev",
    "sector",
    "industry",
)

MB = 1024.0 * 1024.0


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _apply_option_a_universe_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Option A universe: keep only Information Technology, Industrials, or Semiconductors."""
    if df.empty:
        return df

    work = df.copy()
    for col in ("sector", "industry", "industry_group"):
        if col not in work.columns:
            work[col] = ""

    sector = work["sector"].astype("string").str.lower()
    industry = work["industry"].astype("string").str.lower()
    industry_group = work["industry_group"].astype("string").str.lower()

    keep = (
        sector.str.contains(r"information technology|info(?:rmation)?\s*tech|^tech(?:nology)?$", regex=True, na=False)
        | sector.str.contains(r"industrials?", regex=True, na=False)
        | sector.str.contains(r"semiconductors?|semis?", regex=True, na=False)
        | industry.str.contains(r"semiconductors?|semis?", regex=True, na=False)
        | industry_group.str.contains(r"semiconductors?|semis?", regex=True, na=False)
    )

    before_rows = int(len(work))
    out = work.loc[keep].copy()
    after_rows = int(len(out))
    print(
        "[UNIVERSE] Option A filter active: "
        f"before_rows={before_rows:,} after_rows={after_rows:,} dropped_rows={before_rows - after_rows:,}"
    )
    return out


def _optimize_feature_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Prune memory footprint for feature frames before heavy joins/pivots."""
    if df.empty:
        return df
    out = df.copy()

    float_cols = out.select_dtypes(include=["float64"]).columns.tolist()
    for col in float_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")

    int_cols = out.select_dtypes(include=["int64"]).columns.tolist()
    for col in int_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce", downcast="integer")

    if "permno" in out.columns:
        perm = pd.to_numeric(out["permno"], errors="coerce")
        if bool(perm.notna().all()):
            out["permno"] = perm.astype("int32")
        else:
            out["permno"] = perm.astype("Int32")

    for col in ("ticker", "sector", "industry", "industry_group"):
        if col in out.columns:
            out[col] = out[col].astype("string").fillna("Unknown").astype("category")
    return out


def _record_memory(samples: list[dict[str, Any]], stage: str) -> None:
    """Capture and print process memory telemetry in MB."""
    current_mb: float
    peak_mb: float
    if psutil is not None:
        rss = float(psutil.Process(os.getpid()).memory_info().rss / MB)
        current_mb = rss
        peak_mb = rss
        source = "psutil_rss"
    else:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        current_mb = float(current / MB)
        peak_mb = float(peak / MB)
        source = "tracemalloc"

    sample = {
        "stage": str(stage),
        "current_mb": current_mb,
        "peak_mb": peak_mb,
        "source": source,
    }
    samples.append(sample)
    print(
        f"[MEM] stage={stage} source={source} current_mb={current_mb:.2f} peak_mb={peak_mb:.2f}"
    )


def _has_adj_close(path: Path | None) -> bool:
    if path is None or not path.exists():
        return False
    con = duckdb.connect()
    try:
        desc = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(path)}')"
        ).df()
        cols = set(desc["column_name"].astype(str).tolist())
        return "adj_close" in cols
    finally:
        con.close()


def _read_feature_window(
    path: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    requested_columns: set[str],
    *,
    date_candidates: tuple[str, ...] = ("date",),
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    con = duckdb.connect()
    try:
        desc = con.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(path)}')"
        ).df()
        available = set(desc["column_name"].astype(str).tolist())
    finally:
        con.close()

    date_col = next((c for c in date_candidates if c in available), None)
    if date_col is None or "permno" not in available:
        return pd.DataFrame()

    selected = [
        c for c in sorted(requested_columns)
        if c in available and c not in {date_col, "permno"}
    ]
    select_cols = [date_col, "permno", *selected]
    filters = [
        (date_col, ">=", pd.Timestamp(start_date).date()),
        (date_col, "<=", pd.Timestamp(end_date).date()),
    ]

    try:
        df = pd.read_parquet(path, columns=select_cols, filters=filters)
    except Exception:
        # Fallback when parquet engine cannot push date predicates for this dtype.
        df = pd.read_parquet(path, columns=select_cols)

    if df.empty:
        return df
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    in_window = (
        df[date_col].notna()
        & (df[date_col].dt.date >= pd.Timestamp(start_date).date())
        & (df[date_col].dt.date <= pd.Timestamp(end_date).date())
    )
    df = df.loc[in_window].copy()
    if df.empty:
        return df

    if date_col != "date":
        df["date"] = df[date_col]
        df = df.drop(columns=[date_col], errors="ignore")
    df = df.sort_values(["date", "permno"]).reset_index(drop=True)
    return _optimize_feature_dtypes(df)


def _load_features_window(
    features_path: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    extra_columns: list[str],
    sdm_features_path: Path = DEFAULT_SDM_FEATURES_PATH,
) -> pd.DataFrame:
    if not features_path.exists():
        raise FileNotFoundError(f"Missing features parquet: {features_path}")

    candidate_cols = {
        c
        for spec in PRODUCTION_CONFIG_V1.factor_specs
        for c in spec.candidate_columns
    }.union(set(extra_columns))
    base_requested = set(candidate_cols).union({"ticker", "sector", "industry", "industry_group"})
    base = _read_feature_window(
        path=features_path,
        start_date=start_date,
        end_date=end_date,
        requested_columns=base_requested,
        date_candidates=("date",),
    )
    if base.empty:
        return base

    sdm_requested = set(SDM_CORE_COLUMNS).union(set(extra_columns))
    sdm = _read_feature_window(
        path=sdm_features_path,
        start_date=start_date,
        end_date=end_date,
        requested_columns=sdm_requested,
        date_candidates=("date", "published_at"),
    )
    base["date"] = pd.to_datetime(base["date"], errors="coerce", utc=True).dt.tz_convert(None)
    base["permno"] = pd.to_numeric(base["permno"], errors="coerce")
    base = (
        base.sort_values(["date", "permno"])
        .drop_duplicates(subset=["date", "permno"], keep="last")
        .reset_index(drop=True)
    )
    base = _optimize_feature_dtypes(base)

    if not sdm.empty:
        sdm["date"] = pd.to_datetime(sdm["date"], errors="coerce", utc=True).dt.tz_convert(None)
        sdm["permno"] = pd.to_numeric(sdm["permno"], errors="coerce")
        sdm = (
            sdm.sort_values(["date", "permno"])
            .drop_duplicates(subset=["date", "permno"], keep="last")
            .reset_index(drop=True)
        )
        sdm = _optimize_feature_dtypes(sdm)
        # Adapter contract: keep base universe via LEFT overlay, then append SDM-only keys.
        merged = base.merge(sdm, on=["date", "permno"], how="left", suffixes=("", "_sdm"))
        sdm_suffix_cols = [c for c in merged.columns if c.endswith("_sdm")]
        for c_sfx in sdm_suffix_cols:
            c = c_sfx[:-4]
            if c in merged.columns:
                # SDM overlay takes precedence when both sources provide the same field.
                merged[c] = merged[c_sfx].combine_first(merged[c])
            else:
                merged[c] = merged[c_sfx]
        overlay = merged.drop(columns=sdm_suffix_cols, errors="ignore")

        base_keys = base[["date", "permno"]].dropna().drop_duplicates()
        sdm_keys = sdm[["date", "permno"]].dropna().drop_duplicates()
        sdm_only_keys = (
            sdm_keys.merge(base_keys, on=["date", "permno"], how="left", indicator=True)
            .loc[lambda d: d["_merge"] == "left_only", ["date", "permno"]]
            .reset_index(drop=True)
        )
        # Keep evaluation on tradable dates present in the base feature panel.
        trading_dates = base[["date"]].dropna().drop_duplicates()
        sdm_only_keys = sdm_only_keys.merge(trading_dates, on="date", how="inner")
        if not sdm_only_keys.empty:
            sdm_only = sdm_only_keys.merge(sdm, on=["date", "permno"], how="left")
            for col in overlay.columns:
                if col not in sdm_only.columns:
                    sdm_only[col] = np.nan
            sdm_only = sdm_only.loc[:, overlay.columns]
            df = pd.concat([overlay, sdm_only], ignore_index=True)
            del sdm_only
        else:
            df = overlay
        del merged, overlay, sdm_keys, base_keys, sdm_only_keys, sdm
        gc.collect()
    else:
        df = base

    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce")
    df = (
        df.dropna(subset=["date", "permno"])
        .sort_values(["date", "permno"])
        .drop_duplicates(subset=["date", "permno"], keep="last")
        .reset_index(drop=True)
    )
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce").astype("int32")
    df = _optimize_feature_dtypes(df)
    del base
    gc.collect()
    return df


def _load_regime_states(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    feature_dates: pd.DatetimeIndex,
    macro_path: Path,
    liquidity_path: Path,
    macro_gates_path: Path | None = None,
    return_controls: bool = False,
) -> tuple[pd.Series, pd.Series] | tuple[pd.Series, pd.Series, pd.DataFrame]:
    idx = pd.DatetimeIndex(feature_dates)

    def _as_bool_series(values: pd.Series | None, *, default: bool) -> pd.Series:
        if values is None:
            return pd.Series(default, index=idx, dtype=bool)
        return (
            values.reindex(idx)
            .astype("boolean")
            .ffill()
            .fillna(default)
            .astype(bool)
        )

    def _normalize_controls(
        regime: pd.Series,
        reason: pd.Series,
        gate_scalar: pd.Series,
        cash_pct: pd.Series,
        momentum_entry: pd.Series,
        *,
        source: str,
        source_exists: bool,
    ) -> pd.DataFrame:
        controls = pd.DataFrame(index=idx)
        controls["regime"] = (
            regime.reindex(idx)
            .ffill()
            .fillna("AMBER")
            .astype(str)
            .str.upper()
        )
        controls["reason"] = (
            reason.reindex(idx)
            .ffill()
            .fillna("Fallback: no reason")
            .astype(str)
        )
        controls["gate_scalar"] = (
            pd.to_numeric(gate_scalar.reindex(idx), errors="coerce")
            .ffill()
            .fillna(0.5)
            .clip(lower=0.0, upper=1.0)
            .astype(float)
        )
        controls["cash_pct"] = (
            pd.to_numeric(cash_pct.reindex(idx), errors="coerce")
            .ffill()
            .fillna(0.25)
            .clip(lower=0.0, upper=1.0)
            .astype(float)
        )
        controls["momentum_entry"] = _as_bool_series(momentum_entry, default=False)

        # Strict PIT rule: shift every control field as one bundle.
        controls["regime"] = controls["regime"].shift(1).fillna("AMBER").astype(str).str.upper()
        controls["reason"] = controls["reason"].shift(1).fillna("Fallback: shifted warmup").astype(str)
        controls["gate_scalar"] = controls["gate_scalar"].shift(1).fillna(0.5).astype(float)
        controls["cash_pct"] = controls["cash_pct"].shift(1).fillna(0.25).astype(float)
        controls["momentum_entry"] = (
            controls["momentum_entry"]
            .astype("boolean")
            .shift(1)
            .fillna(False)
            .astype(bool)
        )
        controls["gate_source"] = str(source)
        controls["gate_source_exists"] = bool(source_exists)
        return controls

    gates_path = macro_gates_path if macro_gates_path is not None else DEFAULT_MACRO_GATES_PATH
    if isinstance(gates_path, Path) and gates_path.exists():
        try:
            gates = _load_frame(gates_path, start=start_date, end=end_date)
            if not gates.empty:
                regime = (
                    gates.get("state", pd.Series("AMBER", index=gates.index))
                    .astype(str)
                    .str.upper()
                )
                reason = gates.get("reasons", pd.Series("macro_gates:risk_normalized", index=gates.index)).astype(str)
                gate_scalar = pd.to_numeric(gates.get("scalar", pd.Series(np.nan, index=gates.index)), errors="coerce")
                cash_pct = pd.to_numeric(gates.get("cash_buffer", pd.Series(np.nan, index=gates.index)), errors="coerce")
                momentum_entry = (
                    gates.get("momentum_entry", pd.Series(False, index=gates.index))
                    .astype("boolean")
                    .fillna(False)
                    .astype(bool)
                )
                controls = _normalize_controls(
                    regime=regime,
                    reason=reason,
                    gate_scalar=gate_scalar,
                    cash_pct=cash_pct,
                    momentum_entry=momentum_entry,
                    source="macro_gates.parquet",
                    source_exists=True,
                )
                if return_controls:
                    return controls["regime"], controls["reason"], controls
                return controls["regime"], controls["reason"]
        except Exception:
            # Fall back to RegimeManager path below.
            pass

    if not macro_path.exists():
        fallback = pd.Series("AMBER", index=idx, dtype="object")
        reason = pd.Series("Fallback: missing macro artifact", index=idx, dtype="object")
        controls = _normalize_controls(
            regime=fallback,
            reason=reason,
            gate_scalar=pd.Series(0.5, index=idx, dtype=float),
            cash_pct=pd.Series(0.25, index=idx, dtype=float),
            momentum_entry=pd.Series(True, index=idx, dtype=bool),
            source="fallback_missing_macro",
            source_exists=False,
        )
        if return_controls:
            return controls["regime"], controls["reason"], controls
        return controls["regime"], controls["reason"]

    macro = _load_frame(macro_path, start=start_date, end=end_date)
    liq = _load_frame(liquidity_path, start=start_date, end=end_date) if liquidity_path.exists() else None
    ctx = _build_context(macro=macro, liquidity=liq)
    if ctx.empty:
        fallback = pd.Series("AMBER", index=idx, dtype="object")
        reason = pd.Series("Fallback: empty context", index=idx, dtype="object")
        controls = _normalize_controls(
            regime=fallback,
            reason=reason,
            gate_scalar=pd.Series(0.5, index=idx, dtype=float),
            cash_pct=pd.Series(0.25, index=idx, dtype=float),
            momentum_entry=pd.Series(True, index=idx, dtype=bool),
            source="regime_manager_empty_context",
            source_exists=bool(macro_path.exists()),
        )
        if return_controls:
            return controls["regime"], controls["reason"], controls
        return controls["regime"], controls["reason"]

    regime_result = RegimeManager().evaluate(ctx, ctx.index)
    regime = regime_result.governor_state.reindex(idx).ffill().fillna("AMBER")
    reason = regime_result.reason.reindex(idx).ffill().fillna("Fallback: no reason")
    gate_scalar = regime.astype(str).str.upper().map({"GREEN": 1.0, "AMBER": 0.5, "RED": 0.0}).fillna(0.5)
    cash_pct = regime.astype(str).str.upper().map({"GREEN": 0.20, "AMBER": 0.25, "RED": 0.50}).fillna(0.25)
    momentum_entry = regime.astype(str).str.upper().ne("RED")

    controls = _normalize_controls(
        regime=regime,
        reason=reason,
        gate_scalar=pd.to_numeric(gate_scalar, errors="coerce"),
        cash_pct=pd.to_numeric(cash_pct, errors="coerce"),
        momentum_entry=momentum_entry,
        source="regime_manager",
        source_exists=bool(macro_path.exists()),
    )
    if return_controls:
        return controls["regime"], controls["reason"], controls
    return controls["regime"], controls["reason"]


def _build_cash_returns(
    idx: pd.DatetimeIndex,
    prices_path: Path,
    patch_path: Path,
    macro_path: Path,
    liquidity_path: Path,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.Series:
    effr_rate = pd.Series(np.nan, index=idx, dtype=float)
    if macro_path.exists():
        macro = _load_frame(macro_path, start=start_date, end=end_date)
        if "effr_rate" in macro.columns:
            effr_rate = pd.to_numeric(macro["effr_rate"], errors="coerce").reindex(idx)
    if effr_rate.notna().sum() == 0 and liquidity_path.exists():
        liq = _load_frame(liquidity_path, start=start_date, end=end_date)
        if "effr_rate" in liq.columns:
            effr_rate = pd.to_numeric(liq["effr_rate"], errors="coerce").reindex(idx)

    bil_prices_path = prices_path if _has_adj_close(prices_path) else (DEFAULT_PRICES_PATH if _has_adj_close(DEFAULT_PRICES_PATH) else None)
    bil_close = _load_price_series_from_parquet(
        permno=BIL_PERMNO,
        prices_path=bil_prices_path,
        patch_path=patch_path if patch_path.exists() else None,
        start=start_date,
        end=end_date,
    ).reindex(idx)
    bil_ret = bil_close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    cash_ret, _ = build_cash_return(idx=idx, bil_ret=bil_ret, effr_rate=effr_rate)
    return pd.to_numeric(cash_ret, errors="coerce").fillna(0.0).astype(float)


def _build_phase20_plan(
    conviction_df: pd.DataFrame,
    *,
    top_n_green: int,
    top_n_amber: int,
    max_gross_exposure: float,
    softmax_temperature: float,
    gate_controls: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if not np.isfinite(float(softmax_temperature)) or float(softmax_temperature) <= 0.0:
        raise ValueError(f"softmax_temperature must be > 0, got {softmax_temperature}")

    min_eligible_names = 4
    max_single_position = 0.25

    def _stable_softmax(values: np.ndarray, temperature: float) -> np.ndarray:
        x = np.asarray(values, dtype=float)
        if x.size == 0:
            return np.asarray([], dtype=float)
        scaled = x / float(temperature)
        finite_scaled = scaled[np.isfinite(scaled)]
        if finite_scaled.size == 0:
            return np.full(x.shape, 1.0 / float(x.size), dtype=float)
        max_v = float(np.max(finite_scaled))
        exp_v = np.exp(np.clip(scaled - max_v, -60.0, 60.0))
        exp_v = np.where(np.isfinite(exp_v), exp_v, 0.0)
        denom = float(exp_v.sum())
        if not np.isfinite(denom) or denom <= 0.0:
            return np.full(x.shape, 1.0 / float(x.size), dtype=float)
        return exp_v / denom

    def _cap_and_redistribute(weights: np.ndarray, cap: float) -> np.ndarray:
        w = np.asarray(weights, dtype=float)
        if w.size == 0:
            return np.asarray([], dtype=float)
        total = float(np.nansum(w))
        if not np.isfinite(total) or total <= 0.0:
            return np.zeros_like(w, dtype=float)
        cap_v = float(max(cap, 0.0))
        if cap_v <= 0.0:
            return np.zeros_like(w, dtype=float)

        out = np.zeros_like(w, dtype=float)
        free_mask = np.ones(w.shape[0], dtype=bool)
        remaining = total
        base = np.where(np.isfinite(w) & (w > 0.0), w, 0.0)

        for _ in range(int(w.size) + 2):
            if remaining <= 1e-12 or not free_mask.any():
                break
            free_base = base[free_mask]
            free_sum = float(np.sum(free_base))
            if not np.isfinite(free_sum) or free_sum <= 0.0:
                candidate = np.full(int(free_mask.sum()), remaining / float(max(1, int(free_mask.sum()))), dtype=float)
            else:
                candidate = remaining * (free_base / free_sum)

            over = candidate > (cap_v + 1e-12)
            free_idx = np.where(free_mask)[0]
            if not over.any():
                out[free_idx] = candidate
                remaining = 0.0
                break

            over_idx = free_idx[over]
            out[over_idx] = cap_v
            remaining -= cap_v * float(over_idx.size)
            free_mask[over_idx] = False
            base[over_idx] = 0.0

        if remaining > 1e-10:
            under_idx = np.where(out < (cap_v - 1e-12))[0]
            if under_idx.size > 0:
                room = cap_v - out[under_idx]
                room_sum = float(np.sum(room))
                if room_sum > 0.0 and np.isfinite(room_sum):
                    out[under_idx] += remaining * (room / room_sum)

        out = np.clip(out, 0.0, cap_v)
        total_after = float(np.sum(out))
        if total_after > 0.0:
            scale = min(1.0, total / total_after)
            out = out * scale
        return out

    plan = conviction_df.copy().sort_values(["date", "conviction_score", "score"], ascending=[True, False, False])
    plan["rank"] = plan.groupby("date", sort=False).cumcount() + 1

    n_map = {"GREEN": int(top_n_green), "AMBER": int(top_n_amber), "RED": 0}
    cash_map = {"GREEN": 0.20, "AMBER": 0.25, "RED": 0.50}
    scalar_map = {"GREEN": 1.0, "AMBER": 0.5, "RED": 0.0}

    plan["n_target"] = plan["regime"].map(n_map).fillna(int(top_n_amber)).astype(int)
    plan["cash_pct"] = plan["regime"].map(cash_map).fillna(0.25).astype(float)
    plan["gate_scalar"] = plan["regime"].map(scalar_map).fillna(0.5).astype(float)
    plan["macro_momentum_entry"] = plan["regime"].astype(str).str.upper().ne("RED")

    if isinstance(gate_controls, pd.DataFrame) and not gate_controls.empty:
        gc = gate_controls.copy()
        if "date" in gc.columns:
            gc["date"] = pd.to_datetime(gc["date"], errors="coerce")
            gc = gc.dropna(subset=["date"]).set_index("date")
        gc.index = pd.to_datetime(gc.index, errors="coerce")
        gc = gc[~gc.index.isna()].sort_index()
        gc = gc[~gc.index.duplicated(keep="last")]

        if "cash_pct" in gc.columns:
            cash_by_date = pd.to_numeric(gc["cash_pct"], errors="coerce")
            plan["cash_pct"] = (
                pd.to_numeric(plan["date"].map(cash_by_date), errors="coerce")
                .fillna(plan["cash_pct"])
                .clip(lower=0.0, upper=1.0)
            )
        if "gate_scalar" in gc.columns:
            scalar_by_date = pd.to_numeric(gc["gate_scalar"], errors="coerce")
            plan["gate_scalar"] = (
                pd.to_numeric(plan["date"].map(scalar_by_date), errors="coerce")
                .fillna(plan["gate_scalar"])
                .clip(lower=0.0, upper=1.0)
            )
        if "momentum_entry" in gc.columns:
            mom_by_date = (
                gc["momentum_entry"].astype("boolean").fillna(False).astype(bool)
            )
            plan["macro_momentum_entry"] = (
                plan["date"].map(mom_by_date)
                .astype("boolean")
                .fillna(plan["macro_momentum_entry"])
                .astype(bool)
            )

    plan["selected"] = plan["entry_gate"] & plan["macro_momentum_entry"] & (plan["rank"] <= plan["n_target"])

    plan["base_weight"] = 0.0
    for _, block in plan.groupby("date", sort=False):
        block_idx = block.index
        selected_idx = block_idx[block["selected"].to_numpy(dtype=bool)]
        if len(selected_idx) == 0:
            continue

        if len(selected_idx) < int(min_eligible_names):
            # Institutional concentration guard: if breadth is too narrow, stand down to cash.
            plan.loc[block_idx, "selected"] = False
            plan.loc[block_idx, "base_weight"] = 0.0
            plan.loc[block_idx, "cash_pct"] = 1.0
            continue

        regime = str(block["regime"].iloc[0]).upper()
        cash_budget = float(np.clip(1.0 - float(block["cash_pct"].iloc[0]), 0.0, 1.0))
        gate_scalar = float(np.clip(float(block["gate_scalar"].iloc[0]), 0.0, 1.0))
        risk_budget = float(np.clip(min(cash_budget, gate_scalar), 0.0, 1.0))
        if regime == "GREEN":
            scores = (
                pd.to_numeric(plan.loc[selected_idx, "conviction_score"], errors="coerce")
                .fillna(0.0)
                .to_numpy(dtype=float)
            )
            probs = _stable_softmax(scores, temperature=float(softmax_temperature))
            raw_w = risk_budget * probs
            capped = _cap_and_redistribute(raw_w, cap=float(max_single_position))
            plan.loc[selected_idx, "base_weight"] = capped
        else:
            plan.loc[selected_idx, "base_weight"] = risk_budget / float(len(selected_idx))

    # Minimal Viable lock: no leverage in Round 3.
    plan["leverage_mult"] = 1.0
    plan["effective_weight"] = np.where(plan["selected"], plan["base_weight"], 0.0)

    gross_before = plan.groupby("date", sort=False)["effective_weight"].transform("sum")
    green_gross_cap = 0.80
    gross_cap = np.where(plan["regime"].astype(str).str.upper().eq("GREEN"), green_gross_cap, float(max_gross_exposure))
    scale = np.where(gross_before > gross_cap, gross_cap / gross_before, 1.0)
    plan["effective_weight"] = plan["effective_weight"] * scale

    plan["state"] = np.where(plan["selected"], "LONG", np.where(plan["avoid_or_short_flag"], "AVOID_SHORT", "WATCH"))

    eq_weights = (
        plan.pivot(index="date", columns="permno", values="effective_weight")
        .sort_index()
        .fillna(0.0)
    )

    cash_alloc = (
        plan.groupby("date", sort=False)
        .agg(
            regime=("regime", "first"),
            cash_pct=("cash_pct", "first"),
            gate_scalar=("gate_scalar", "first"),
            momentum_entry=("macro_momentum_entry", "first"),
            n_selected=("selected", "sum"),
            n_levered=("state", lambda s: int((pd.Series(s) == "LONG_1p5x").sum())),
        )
        .sort_index()
    )
    cash_alloc["n_selected"] = pd.to_numeric(cash_alloc["n_selected"], errors="coerce").fillna(0).astype(int)
    cash_alloc["n_levered"] = pd.to_numeric(cash_alloc["n_levered"], errors="coerce").fillna(0).astype(int)
    cash_alloc["gate_scalar"] = pd.to_numeric(cash_alloc["gate_scalar"], errors="coerce").fillna(0.5).clip(lower=0.0, upper=1.0)
    cash_alloc["momentum_entry"] = cash_alloc["momentum_entry"].astype("boolean").fillna(False).astype(bool)

    exposure = pd.DataFrame(index=eq_weights.index)
    if eq_weights.shape[1] == 0:
        exposure["gross_exposure"] = 0.0
        exposure["max_name_weight"] = 0.0
        exposure["herfindahl"] = 0.0
    else:
        exposure["gross_exposure"] = eq_weights.sum(axis=1)
        exposure["max_name_weight"] = eq_weights.max(axis=1)
        exposure["herfindahl"] = (eq_weights ** 2.0).sum(axis=1)
    exposure = exposure.join(
        cash_alloc[["cash_pct", "gate_scalar", "momentum_entry", "regime", "n_selected", "n_levered"]],
        how="left",
    )
    exposure = exposure.reset_index().rename(columns={"index": "date"})

    return plan, eq_weights, exposure


def _simulate(
    weights: pd.DataFrame,
    returns_wide: pd.DataFrame,
    cost_bps: float,
    allow_missing_returns: bool,
) -> tuple[pd.DataFrame, int]:
    cols_no_cash = [c for c in weights.columns if c != CASH_COL]
    missing_active = 0
    if cols_no_cash:
        aligned = returns_wide.reindex(index=weights.index, columns=cols_no_cash)
        executed = weights[cols_no_cash].shift(1).fillna(0.0).ne(0.0)
        missing_active = int((aligned.isna() & executed).sum().sum())
        if missing_active > 0 and not allow_missing_returns:
            raise RuntimeError(
                f"Missing {missing_active:,} executed-exposure return cells. Use --allow-missing-returns to proceed."
            )
        if missing_active > 0 and allow_missing_returns:
            print(f"WARNING: Missing executed-exposure return cells treated as zero: {missing_active:,}")

    aligned_returns = returns_wide.reindex(index=weights.index, columns=weights.columns)
    sim = engine.run_simulation(
        target_weights=weights,
        returns_df=aligned_returns,
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=not allow_missing_returns,
    ).copy()
    sim.index = pd.DatetimeIndex(sim.index)
    sim.index.name = "date"
    sim["equity"] = (1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    return sim, missing_active


def _metrics(sim: pd.DataFrame) -> dict[str, float]:
    ret = pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    eq = pd.to_numeric(sim["equity"], errors="coerce")
    return {
        "sharpe": float(compute_sharpe(ret)),
        "cagr": float(compute_cagr(eq)),
        "max_dd": float(compute_max_drawdown(eq)),
        "ulcer": float(compute_ulcer_index(eq)),
        "turnover_annual": float(pd.to_numeric(sim["turnover"], errors="coerce").mean() * 252.0),
        "turnover_total": float(pd.to_numeric(sim["turnover"], errors="coerce").sum()),
    }


def _slice_sim(sim: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    idx = pd.DatetimeIndex(sim.index)
    return sim[(idx >= pd.Timestamp(start)) & (idx <= pd.Timestamp(end))].copy()


def _crisis_turnover_table(c3_sim: pd.DataFrame, p20_sim: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for name, start, end in CRISIS_WINDOWS:
        c3 = _slice_sim(c3_sim, start, end)
        p20 = _slice_sim(p20_sim, start, end)
        c3_turn = float(pd.to_numeric(c3["turnover"], errors="coerce").fillna(0.0).mean() * 252.0)
        p20_turn = float(pd.to_numeric(p20["turnover"], errors="coerce").fillna(0.0).mean() * 252.0)
        reduction = ((c3_turn - p20_turn) / c3_turn * 100.0) if np.isfinite(c3_turn) and abs(c3_turn) > 1e-12 else float("nan")
        rows.append(
            {
                "window": name,
                "start_date": start,
                "end_date": end,
                "c3_turnover_annual": c3_turn,
                "phase20_turnover_annual": p20_turn,
                "reduction_pct": reduction,
                # Locked method A: gate truth is derived directly from reduction_pct.
                "pass": bool(np.isfinite(reduction) and reduction >= 75.0),
            }
        )
    return pd.DataFrame(rows)


def _save_equity_png(c3_sim: pd.DataFrame, p20_sim: pd.DataFrame, png_path: Path) -> None:
    png_path.parent.mkdir(parents=True, exist_ok=True)
    idx = c3_sim.index.union(p20_sim.index).sort_values()
    c3_eq = pd.to_numeric(c3_sim["equity"], errors="coerce").reindex(idx).ffill()
    p20_eq = pd.to_numeric(p20_sim["equity"], errors="coerce").reindex(idx).ffill()

    try:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 1, figsize=(14, 7))
        ax.plot(idx, c3_eq, color="#666666", linewidth=1.3, label="C3 Baseline")
        ax.plot(idx, p20_eq, color="#1f77b4", linewidth=1.6, label="Phase 20")
        ax.set_yscale("log")
        ax.set_title("Phase 20 vs C3 Equity Curves (Log Scale)")
        ax.set_xlabel("Date")
        ax.set_ylabel("Equity")
        ax.grid(alpha=0.2)
        ax.legend(loc="upper left")
        fig.tight_layout()

        temp_path = png_path.with_suffix(png_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
        try:
            fig.savefig(temp_path, dpi=150)
            os.replace(temp_path, png_path)
        finally:
            plt.close(fig)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
    except Exception:
        from PIL import Image, ImageDraw

        width, height = 1800, 900
        pad = 70
        img = Image.new("RGB", (width, height), color=(248, 249, 251))
        draw = ImageDraw.Draw(img)
        draw.rectangle([pad, pad, width - pad, height - pad], outline=(120, 120, 120), width=1)
        draw.text((pad, 20), "Phase 20 vs C3 Equity Curves (fallback)", fill=(30, 30, 30))
        draw.text((pad, 45), "matplotlib unavailable; fallback render", fill=(60, 60, 60))
        temp_path = png_path.with_suffix(png_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
        try:
            img.save(temp_path, format="PNG")
            os.replace(temp_path, png_path)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass


def _write_sample_output(plan: pd.DataFrame, sample_path: Path) -> tuple[str, pd.Timestamp]:
    if plan.empty:
        empty = pd.DataFrame(
            columns=[
                "date",
                "ticker",
                "permno",
                "regime",
                "score",
                "conviction_score",
                "entry_gate",
                "support_proximity",
                "mom_ok",
                "quality_ok",
                "leverage_mult",
                "selected",
                "state",
            ]
        )
        _atomic_csv_write(empty, sample_path)
        return "AMBER", pd.Timestamp("1970-01-01")

    work = plan.copy()
    green_dates = pd.DatetimeIndex(sorted(work.loc[work["regime"].eq("GREEN"), "date"].unique()))
    if len(green_dates) > 0:
        sample_date = green_dates[-1]
    else:
        sample_date = pd.Timestamp(work["date"].max())

    block = work[work["date"] == sample_date].copy()
    block = block.sort_values(["selected", "conviction_score", "score"], ascending=[False, False, False])
    out_cols = [
        "date",
        "ticker",
        "permno",
        "regime",
        "score",
        "conviction_score",
        "entry_gate",
        "support_proximity",
        "mom_ok",
        "quality_ok",
        "leverage_mult",
        "selected",
        "state",
    ]
    out = block[out_cols].head(40).copy()
    _atomic_csv_write(out, sample_path)
    regime = str(out["regime"].iloc[0]) if not out.empty else "AMBER"
    return regime, pd.Timestamp(sample_date)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 20 full validation run against locked C3 baseline")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--input-sdm-features", default=str(DEFAULT_SDM_FEATURES_PATH))
    p.add_argument("--input-prices", default=None)
    p.add_argument("--macro-path", default=None)
    p.add_argument("--macro-gates-path", default=str(DEFAULT_MACRO_GATES_PATH))
    p.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    p.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH))
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--top-n-green", type=int, default=8)
    p.add_argument("--top-n-amber", type=int, default=4)
    p.add_argument("--max-gross-exposure", type=float, default=1.0)
    p.add_argument("--softmax-temperature", type=float, default=1.0)
    p.add_argument("--support-sma-window", type=int, default=200)
    p.add_argument("--momentum-lookback", type=int, default=60)
    p.add_argument("--option-a-sector-specialist", action="store_true")
    p.add_argument("--allow-missing-returns", action="store_true")
    p.add_argument("--output-delta-csv", default=str(DEFAULT_DELTA_CSV))
    p.add_argument("--output-equity-png", default=str(DEFAULT_EQUITY_PNG))
    p.add_argument("--output-cash-csv", default=str(DEFAULT_CASH_CSV))
    p.add_argument("--output-top20-csv", default=str(DEFAULT_EXPOSURE_CSV))
    p.add_argument("--output-summary-json", default=str(DEFAULT_SUMMARY_JSON))
    p.add_argument("--output-sample-csv", default=str(DEFAULT_SAMPLE_CSV))
    p.add_argument("--output-crisis-csv", default=str(DEFAULT_CRISIS_CSV))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    memory_samples: list[dict[str, Any]] = []
    _record_memory(memory_samples, "start_main")

    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is None or end is None:
        raise ValueError("start-date and end-date are required")
    if end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    sdm_features_path = Path(args.input_sdm_features)
    default_prices = DEFAULT_PRICES_TRI_PATH if DEFAULT_PRICES_TRI_PATH.exists() else DEFAULT_PRICES_PATH
    prices_path = _resolve_path(args.input_prices, default_prices)
    macro_path = _resolve_path(args.macro_path, DEFAULT_MACRO_FEATURES_PATH if DEFAULT_MACRO_FEATURES_PATH.exists() else DEFAULT_MACRO_FALLBACK_PATH)
    macro_gates_path = _resolve_path(args.macro_gates_path, DEFAULT_MACRO_GATES_PATH)
    liquidity_path = _resolve_path(args.liquidity_path, DEFAULT_LIQUIDITY_PATH)
    patch_path = _resolve_path(args.patch_path, DEFAULT_PATCH_PATH)

    out_delta = _resolve_path(args.output_delta_csv, DEFAULT_DELTA_CSV)
    out_equity = _resolve_path(args.output_equity_png, DEFAULT_EQUITY_PNG)
    out_cash = _resolve_path(args.output_cash_csv, DEFAULT_CASH_CSV)
    out_top20 = _resolve_path(args.output_top20_csv, DEFAULT_EXPOSURE_CSV)
    out_summary = _resolve_path(args.output_summary_json, DEFAULT_SUMMARY_JSON)
    out_sample = _resolve_path(args.output_sample_csv, DEFAULT_SAMPLE_CSV)
    out_crisis = _resolve_path(args.output_crisis_csv, DEFAULT_CRISIS_CSV)

    print("=" * 80)
    print("PHASE 20 FULL VALIDATION RUN")
    print("=" * 80)
    print(f"Features: {features_path}")
    print(f"SDM Overlay: {sdm_features_path} (exists={sdm_features_path.exists()})")
    print(f"Returns:  {prices_path}")
    print(f"Macro gates: {macro_gates_path} (exists={macro_gates_path.exists()})")
    print(f"Window:   {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")
    print(f"Cost:     {float(args.cost_bps):.2f} bps")
    print(f"Option A Sector Specialist Filter: {bool(args.option_a_sector_specialist)}")
    print(f"GREEN Softmax Temperature: {float(args.softmax_temperature):.3f}")
    print(f"Support SMA Window: {int(args.support_sma_window)}")
    print(f"Momentum Lookback: {int(args.momentum_lookback)}")

    extra_cols = [
        "ticker",
        "adj_close",
        "dist_sma20",
        "sma200",
        "resid_mom_60d",
        "z_inventory_quality_proxy",
        "capital_cycle_score",
        "amihud_20d",
    ]
    features = _load_features_window(
        features_path,
        start,
        end,
        extra_columns=extra_cols,
        sdm_features_path=sdm_features_path,
    )
    if bool(args.option_a_sector_specialist):
        features = _apply_option_a_universe_filter(features)
    _record_memory(memory_samples, "after_feature_load")
    if features.empty:
        raise RuntimeError("No feature rows found for Phase 20 window")

    feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
    regime, regime_reason, gate_controls = _load_regime_states(
        start_date=start,
        end_date=end,
        feature_dates=feature_dates,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        macro_gates_path=macro_gates_path,
        return_controls=True,
    )

    scorecard = CompanyScorecard(
        factor_specs=list(PRODUCTION_CONFIG_V1.factor_specs),
        scoring_method=PRODUCTION_CONFIG_V1.scoring_method,
    )
    scores, score_summary = scorecard.compute_scores(features)
    conviction = build_phase20_conviction_frame(
        scores_df=scores,
        features_df=features,
        regime_by_date=regime,
        support_sma_window=int(args.support_sma_window),
        momentum_lookback=int(args.momentum_lookback),
    )
    _record_memory(memory_samples, "after_conviction_build")

    plan, phase20_eq_weights, exposure = _build_phase20_plan(
        conviction_df=conviction,
        top_n_green=int(args.top_n_green),
        top_n_amber=int(args.top_n_amber),
        max_gross_exposure=float(args.max_gross_exposure),
        softmax_temperature=float(args.softmax_temperature),
        gate_controls=gate_controls,
    )
    _record_memory(memory_samples, "after_plan_build")

    regime_map = pd.DataFrame(
        {
            "date": feature_dates,
            "regime": regime.reindex(feature_dates).values,
            "reason": regime_reason.reindex(feature_dates).values,
        }
    )
    cash_alloc = (
        exposure[["date", "regime", "cash_pct", "gate_scalar", "momentum_entry", "n_selected", "n_levered"]]
        .merge(regime_map[["date", "reason"]], on="date", how="left")
        .sort_values("date")
    )
    _atomic_csv_write(cash_alloc, out_cash)

    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    returns_long = _load_returns_subset(prices_path=prices_path, permnos=permnos, start_date=start, end_date=end)
    if returns_long.empty:
        raise RuntimeError("No return rows found for Phase 20 window")

    returns_wide = (
        returns_long.assign(
            date=pd.to_datetime(returns_long["date"], errors="coerce"),
            permno=pd.to_numeric(returns_long["permno"], errors="coerce"),
            ret=pd.to_numeric(returns_long["ret"], errors="coerce"),
        )
        .dropna(subset=["date", "permno"]) 
        .pivot(index="date", columns="permno", values="ret")
        .sort_index()
    )

    cash_ret = _build_cash_returns(
        idx=feature_dates,
        prices_path=prices_path,
        patch_path=patch_path,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        start_date=start,
        end_date=end,
    )

    baseline_weights = _build_target_weights(scores=scores, top_quantile=float(PRODUCTION_CONFIG_V1.top_quantile)).reindex(feature_dates).fillna(0.0)

    phase20_weights = phase20_eq_weights.reindex(feature_dates).fillna(0.0)

    baseline_weights[CASH_COL] = 0.0
    phase20_weights[CASH_COL] = pd.to_numeric(cash_alloc.set_index("date")["cash_pct"], errors="coerce").reindex(feature_dates).fillna(0.0)

    stock_cols = sorted(
        {
            int(c)
            for c in list(baseline_weights.columns) + list(phase20_weights.columns)
            if c != CASH_COL and pd.notna(c)
        }
    )
    all_cols = stock_cols + [CASH_COL]
    baseline_weights = baseline_weights.reindex(index=feature_dates, columns=all_cols).fillna(0.0)
    phase20_weights = phase20_weights.reindex(index=feature_dates, columns=all_cols).fillna(0.0)

    returns_all = returns_wide.reindex(index=feature_dates, columns=[c for c in all_cols if c != CASH_COL])
    returns_all[CASH_COL] = cash_ret.reindex(feature_dates).fillna(0.0)
    returns_all = returns_all.reindex(index=feature_dates, columns=all_cols)

    # Explicit memory telemetry checkpoint before the heavy simulation loop.
    _record_memory(memory_samples, "start_backtest_loop")
    c3_sim, c3_missing = _simulate(
        weights=baseline_weights,
        returns_wide=returns_all,
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
    )
    p20_sim, p20_missing = _simulate(
        weights=phase20_weights,
        returns_wide=returns_all,
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
    )
    _record_memory(memory_samples, "after_backtest_loop")

    c3_metrics = _metrics(c3_sim)
    p20_metrics = _metrics(p20_sim)

    crisis = _crisis_turnover_table(c3_sim=c3_sim, p20_sim=p20_sim)
    _atomic_csv_write(crisis, out_crisis)

    max_name_weight = float(pd.to_numeric(exposure["max_name_weight"], errors="coerce").max()) if not exposure.empty else 0.0
    herfindahl = float(pd.to_numeric(exposure["herfindahl"], errors="coerce").max()) if not exposure.empty else 0.0
    avg_daily_gross_exposure = float(pd.to_numeric(exposure["gross_exposure"], errors="coerce").mean()) if not exposure.empty else 0.0
    mean_cash_red = float(
        pd.to_numeric(cash_alloc.loc[cash_alloc["regime"].astype(str).str.upper() == "RED", "cash_pct"], errors="coerce").mean()
    ) if not cash_alloc.empty else float("nan")
    macro_gate_source = "regime_manager"
    macro_gate_source_exists = bool(macro_gates_path.exists())
    if isinstance(gate_controls, pd.DataFrame) and not gate_controls.empty:
        source_col = gate_controls.get("gate_source")
        if isinstance(source_col, pd.Series) and source_col.dropna().size > 0:
            macro_gate_source = str(source_col.dropna().iloc[-1])
        exists_col = gate_controls.get("gate_source_exists")
        if isinstance(exists_col, pd.Series) and exists_col.notna().any():
            macro_gate_source_exists = bool(
                exists_col.astype("boolean").fillna(False).iloc[-1]
            )

    gates = {
        "gate_sharpe": bool(np.isfinite(p20_metrics["sharpe"]) and np.isfinite(c3_metrics["sharpe"]) and p20_metrics["sharpe"] >= (c3_metrics["sharpe"] - 0.05)),
        "gate_turnover": bool(np.isfinite(p20_metrics["turnover_annual"]) and np.isfinite(c3_metrics["turnover_annual"]) and p20_metrics["turnover_annual"] <= (c3_metrics["turnover_annual"] * 1.20)),
        "gate_crisis": bool(crisis["pass"].all()) if not crisis.empty else False,
        "gate_max_name_weight": bool(np.isfinite(max_name_weight) and max_name_weight <= 0.15),
        "gate_ulcer": bool(np.isfinite(p20_metrics["ulcer"]) and np.isfinite(c3_metrics["ulcer"]) and p20_metrics["ulcer"] <= (c3_metrics["ulcer"] + 0.02)),
        "gate_cash_red": bool(np.isfinite(mean_cash_red) and mean_cash_red >= 0.40),
    }
    gates_total = len(gates)
    gates_passed = int(sum(bool(v) for v in gates.values()))
    decision = "PROMOTE" if gates_passed == gates_total else "ABORT_PIVOT"

    delta_row = {
        "window_start": start.strftime("%Y-%m-%d"),
        "window_end": end.strftime("%Y-%m-%d"),
        "cost_bps": float(args.cost_bps),
        "baseline_config_id": PRODUCTION_CONFIG_V1.config_id,
        "phase20_variant_id": "PHASE20_MIN_VIABLE_TOP20_NO_LEVERAGE",
        "coverage": float(score_summary.coverage),
        "sharpe_c3": c3_metrics["sharpe"],
        "sharpe_phase20": p20_metrics["sharpe"],
        "sharpe_delta": p20_metrics["sharpe"] - c3_metrics["sharpe"],
        "turnover_annual_c3": c3_metrics["turnover_annual"],
        "turnover_annual_phase20": p20_metrics["turnover_annual"],
        "turnover_ratio_phase20_vs_c3": p20_metrics["turnover_annual"] / c3_metrics["turnover_annual"] if np.isfinite(c3_metrics["turnover_annual"]) and abs(c3_metrics["turnover_annual"]) > 1e-12 else float("nan"),
        "max_dd_c3": c3_metrics["max_dd"],
        "max_dd_phase20": p20_metrics["max_dd"],
        "ulcer_c3": c3_metrics["ulcer"],
        "ulcer_phase20": p20_metrics["ulcer"],
        "max_name_weight": max_name_weight,
        "herfindahl": herfindahl,
        "mean_cash_pct_red": mean_cash_red,
        "gate_sharpe": bool(gates["gate_sharpe"]),
        "gate_turnover": bool(gates["gate_turnover"]),
        "gate_crisis": bool(gates["gate_crisis"]),
        "gate_max_name_weight": bool(gates["gate_max_name_weight"]),
        "gate_ulcer": bool(gates["gate_ulcer"]),
        "gate_cash_red": bool(gates["gate_cash_red"]),
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "decision": decision,
        "macro_gate_source": macro_gate_source,
        "macro_gate_source_exists": bool(macro_gate_source_exists),
        "deferred_open_risk": DEFERRED_OPEN_RISK,
    }

    crisis_map = {str(r["window"]): float(r["reduction_pct"]) for _, r in crisis.iterrows()} if not crisis.empty else {}
    for key, val in crisis_map.items():
        delta_row[f"crisis_reduction_{key.lower()}"] = val

    delta_df = pd.DataFrame([delta_row])
    _atomic_csv_write(delta_df, out_delta)

    _atomic_csv_write(exposure.sort_values("date"), out_top20)
    _save_equity_png(c3_sim=c3_sim, p20_sim=p20_sim, png_path=out_equity)

    sample_regime, sample_date = _write_sample_output(plan=plan, sample_path=out_sample)

    summary = {
        "status": "ok" if decision == "PROMOTE" else "blocked",
        "exit_code": 0 if decision == "PROMOTE" else 1,
        "decision": decision,
        "gates": gates,
        "gates_passed": gates_passed,
        "gates_total": gates_total,
        "window": {"start_date": start.strftime("%Y-%m-%d"), "end_date": end.strftime("%Y-%m-%d")},
        "cost_bps": float(args.cost_bps),
        "baseline_config_id": PRODUCTION_CONFIG_V1.config_id,
        "phase20_variant_id": "PHASE20_MIN_VIABLE_TOP20_NO_LEVERAGE",
        "green_softmax_temperature": float(args.softmax_temperature),
        "macro_gate_source": macro_gate_source,
        "macro_gate_source_exists": bool(macro_gate_source_exists),
        "deferred_open_risk": DEFERRED_OPEN_RISK,
        "metrics": {
            "c3": c3_metrics,
            "phase20": p20_metrics,
            "max_name_weight": max_name_weight,
            "herfindahl": herfindahl,
            "avg_daily_gross_exposure": avg_daily_gross_exposure,
            "mean_cash_pct_red": mean_cash_red,
        },
        "missing_active_return_cells": {"c3": int(c3_missing), "phase20": int(p20_missing)},
        "allow_missing_returns": bool(args.allow_missing_returns),
        "sample_output": {"date": str(sample_date.date()), "regime": sample_regime, "path": str(out_sample)},
        "artifacts": {
            "delta_csv": str(out_delta),
            "equity_png": str(out_equity),
            "cash_csv": str(out_cash),
            "top20_csv": str(out_top20),
            "crisis_csv": str(out_crisis),
            "summary_json": str(out_summary),
            "sample_csv": str(out_sample),
        },
        "memory_telemetry": {
            "samples": memory_samples,
            "max_observed_mb": float(
                max(
                    (float(s.get("peak_mb", s.get("current_mb", 0.0))) for s in memory_samples),
                    default=0.0,
                )
            ),
        },
    }
    _atomic_json_write(summary, out_summary)

    print("\nPhase 20 Full Run Complete")
    print(f"Decision: {decision} ({gates_passed}/{gates_total} gates)")
    print(f"Sample output date/regime: {sample_date.date()} / {sample_regime}")
    print(f"Macro gate source: {macro_gate_source} (exists={bool(macro_gate_source_exists)})")
    print(f"Average Daily Gross Exposure: {avg_daily_gross_exposure:.4f}")
    print(f"Delta CSV: {out_delta}")
    print(f"Crisis CSV: {out_crisis}")
    print(f"Summary:   {out_summary}")
    if decision != "PROMOTE":
        print("Gate failed: returning non-zero exit code for CI enforcement.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
