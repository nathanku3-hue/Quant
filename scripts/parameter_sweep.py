from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from utils.statistics import (  # noqa: E402
    average_pairwise_correlation,
    cscv_analysis,
    deflated_sharpe_ratio,
    effective_number_of_trials,
)
from utils.process import pid_is_running  # noqa: E402


PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DEFAULT_OUTPUT_PREFIX = "phase17_2_parameter_sweep"
VARIANT_PARAM_KEYS = ("w_sales", "w_margin", "w_bloat", "w_netinv", "gate_threshold")
DEFAULT_SWEEP_LOCK_STALE_SECONDS = 6 * 60 * 60
DEFAULT_SWEEP_LOCK_RECOVERY_ATTEMPTS = 8


def _load_eval_api():
    # Lazy import keeps lock/checkpoint helpers testable without loading heavy econometrics stack.
    from scripts.evaluate_cross_section import EvalConfig, load_eval_frame, summarize_spread  # noqa: E402

    return EvalConfig, load_eval_frame, summarize_spread


@dataclass(frozen=True)
class SweepConfig:
    panel_path: str
    prices_path: str
    features_path: str
    sector_map_path: str
    start_date: str | None
    end_date: str | None
    horizon_days: int
    high_asset_growth_pct: float
    min_high_group_size: int
    nw_lags: int | None
    cscv_blocks: int
    seed: int
    coarse_sales_weights: tuple[float, ...]
    coarse_margin_weights: tuple[float, ...]
    coarse_bloat_weights: tuple[float, ...]
    coarse_netinv_weights: tuple[float, ...]
    coarse_gate_thresholds: tuple[float, ...]
    fine_step_sales: float
    fine_step_margin: float
    fine_step_bloat: float
    fine_step_netinv: float
    fine_step_gate: float
    max_coarse_combos: int
    max_fine_combos: int
    checkpoint_every: int
    resume: bool
    keep_checkpoint: bool
    output_dir: str
    output_prefix: str


def _sql_safe_float(v: float) -> float:
    return float(np.round(float(v), 8))


def _atomic_write_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        df.to_csv(tmp, index=False)
        _atomic_replace_with_retry(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _atomic_write_json(payload: dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        _atomic_replace_with_retry(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _safe_remove(path: str) -> None:
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


def _atomic_replace_with_retry(src: str, dst: str, max_retries: int = 12, base_sleep_seconds: float = 0.1) -> None:
    for attempt in range(max_retries):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt >= max_retries - 1:
                raise
            time.sleep(base_sleep_seconds * float(attempt + 1))


def _parse_float_list(raw: str) -> tuple[float, ...]:
    parts = [x.strip() for x in str(raw).split(",") if str(x).strip() != ""]
    if not parts:
        raise ValueError(f"Expected comma-separated float list, got: {raw}")
    return tuple(float(x) for x in parts)


def _variant_id_from_params(params: dict[str, float]) -> str:
    canonical = {k: _sql_safe_float(params[k]) for k in VARIANT_PARAM_KEYS if k in params}
    missing = [k for k in VARIANT_PARAM_KEYS if k not in canonical]
    if missing:
        raise ValueError(f"Missing variant parameters for hashing: {missing}")
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    digest = hashlib.md5(payload.encode("utf-8")).hexdigest()[:12]
    return f"v_{digest}"


def _dedupe_grid_by_variant_id(grid: list[dict[str, float]]) -> list[dict[str, float]]:
    seen: set[str] = set()
    out: list[dict[str, float]] = []
    for params in grid:
        vid = _variant_id_from_params(params)
        if vid in seen:
            continue
        seen.add(vid)
        out.append({"variant_id": vid, **params})
    return out


def _merge_results(base: pd.DataFrame, update: pd.DataFrame) -> pd.DataFrame:
    if base is None or base.empty:
        return update.copy().reset_index(drop=True) if update is not None else pd.DataFrame()
    if update is None or update.empty:
        return base.copy().reset_index(drop=True)
    merged = pd.concat([base, update], ignore_index=True)
    if "variant_id" in merged.columns:
        merged["variant_id"] = merged["variant_id"].astype(str)
        merged = merged.drop_duplicates(subset=["variant_id"], keep="last")
    return merged.reset_index(drop=True)


def _merge_streams(base: pd.DataFrame, update: pd.DataFrame) -> pd.DataFrame:
    if (base is None or base.empty) and (update is None or update.empty):
        return pd.DataFrame()
    if base is None or base.empty:
        out = update.copy()
    elif update is None or update.empty:
        out = base.copy()
    else:
        out = pd.concat([base, update], axis=1)
        out = out.loc[:, ~out.columns.duplicated(keep="last")]
    out.index = pd.to_datetime(out.index, errors="coerce")
    out = out[~out.index.isna()].sort_index()
    return out


def _checkpoint_paths(output_dir: str, output_prefix: str) -> dict[str, str]:
    base = os.path.join(output_dir, f".checkpoint_{output_prefix}")
    return {
        "meta_json": f"{base}.json",
        "results_csv": f"{base}_results.csv",
        "streams_csv": f"{base}_streams.csv",
    }


def _sweep_lock_path(output_dir: str, output_prefix: str) -> str:
    return os.path.join(output_dir, f".sweep_{output_prefix}.lock")


def _read_json_file(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, dict):
            return obj
        return {}
    except Exception:
        return {}


def _pid_is_running(pid: int) -> bool:
    return pid_is_running(pid)


def _lock_age_seconds(payload: dict[str, Any]) -> float | None:
    created = pd.to_datetime(payload.get("created_at_utc"), errors="coerce")
    if not isinstance(created, pd.Timestamp) or pd.isna(created):
        return None
    if created.tzinfo is None:
        created = created.tz_localize("UTC")
    now = pd.Timestamp.utcnow()
    if now.tzinfo is None:
        now = now.tz_localize("UTC")
    return max(0.0, float((now - created).total_seconds()))


def _lock_file_age_seconds(lock_path: str) -> float | None:
    try:
        st = os.stat(lock_path)
    except OSError:
        return None
    now = pd.Timestamp.utcnow()
    if now.tzinfo is not None:
        now = now.tz_localize(None)
    modified = pd.Timestamp.fromtimestamp(st.st_mtime)
    return max(0.0, float((now - modified).total_seconds()))


def _recover_stale_lock(lock_path: str, reason: str) -> None:
    max_attempts = int(DEFAULT_SWEEP_LOCK_RECOVERY_ATTEMPTS)
    for attempt in range(1, max_attempts + 1):
        print(f"Recovering stale sweep lock ({reason}) [{attempt}/{max_attempts}]: {lock_path}")
        _safe_remove(lock_path)
        if not os.path.exists(lock_path):
            return
        time.sleep(min(0.05 * float(attempt), 0.5))
    raise RuntimeError(
        "Unable to remove stale sweep lock after "
        f"{max_attempts} attempts: {lock_path}. "
        "If no sweep is running, delete the lock manually and retry."
    )


def _acquire_sweep_lock(output_dir: str, output_prefix: str, stale_lock_seconds: int) -> str:
    os.makedirs(output_dir, exist_ok=True)
    lock_path = _sweep_lock_path(output_dir=output_dir, output_prefix=output_prefix)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    payload = {
        "pid": int(os.getpid()),
        "created_at_utc": pd.Timestamp.utcnow().isoformat(),
        "output_prefix": str(output_prefix),
    }
    attempts = 0
    max_attempts = 32
    while attempts < max_attempts:
        attempts += 1
        try:
            fd = os.open(lock_path, flags)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, sort_keys=True)
            return lock_path
        except FileExistsError:
            existing = _read_json_file(lock_path)
            raw_pid = existing.get("pid")
            lock_pid: int | None = None
            try:
                lock_pid = int(raw_pid)
            except (TypeError, ValueError):
                lock_pid = None

            if lock_pid is not None and _pid_is_running(lock_pid):
                raise RuntimeError(
                    f"Sweep lock is active for --output-prefix '{output_prefix}' "
                    f"(pid={lock_pid}): {lock_path}"
                )

            if lock_pid is not None and not _pid_is_running(lock_pid):
                _recover_stale_lock(lock_path=lock_path, reason=f"dead pid={lock_pid}")
                continue

            age_seconds = _lock_age_seconds(existing)
            age_source = "created_at_utc"
            if age_seconds is None:
                age_seconds = _lock_file_age_seconds(lock_path)
                age_source = "file_mtime"
            if age_seconds is not None and age_seconds >= float(max(1, int(stale_lock_seconds))):
                _recover_stale_lock(
                    lock_path=lock_path,
                    reason=f"{age_source} ttl {age_seconds:.1f}s >= {int(stale_lock_seconds)}s",
                )
                continue

            raise RuntimeError(
                f"Sweep lock exists and cannot be recovered yet for --output-prefix '{output_prefix}': "
                f"{lock_path}"
            )
    raise RuntimeError(
        f"Failed to acquire sweep lock after {max_attempts} attempts for --output-prefix '{output_prefix}': {lock_path}"
    )


def _release_sweep_lock(lock_path: str | None) -> None:
    if not lock_path:
        return
    payload = _read_json_file(lock_path)
    raw_pid = payload.get("pid")
    try:
        owner_pid = int(raw_pid)
    except (TypeError, ValueError):
        owner_pid = None
    if owner_pid is None or owner_pid == int(os.getpid()):
        _safe_remove(lock_path)


def _save_checkpoint(
    paths: dict[str, str],
    results: pd.DataFrame,
    streams: pd.DataFrame,
    meta: dict[str, Any],
) -> None:
    _atomic_write_csv(results, paths["results_csv"])
    _atomic_write_csv(
        streams.reset_index().rename(columns={"index": "date"}),
        paths["streams_csv"],
    )
    _atomic_write_json(meta, paths["meta_json"])


def _load_checkpoint(paths: dict[str, str]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    needed = [paths["meta_json"], paths["results_csv"], paths["streams_csv"]]
    if not all(os.path.exists(p) for p in needed):
        return pd.DataFrame(), pd.DataFrame(), {}
    try:
        with open(paths["meta_json"], "r", encoding="utf-8") as f:
            meta = json.load(f)
        results = pd.read_csv(paths["results_csv"])
        if "variant_id" in results.columns:
            results["variant_id"] = results["variant_id"].astype(str)
        streams_raw = pd.read_csv(paths["streams_csv"])
        if streams_raw.empty:
            streams = pd.DataFrame()
        else:
            if "date" not in streams_raw.columns:
                return pd.DataFrame(), pd.DataFrame(), {}
            streams_raw["date"] = pd.to_datetime(streams_raw["date"], errors="coerce")
            streams = streams_raw.dropna(subset=["date"]).set_index("date").sort_index()
            for c in streams.columns:
                streams[c] = pd.to_numeric(streams[c], errors="coerce")
        return results, streams, meta
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), {}

def _clear_checkpoint(paths: dict[str, str]) -> None:
    _safe_remove(paths["meta_json"])
    _safe_remove(paths["results_csv"])
    _safe_remove(paths["streams_csv"])


def _resolve_checkpoint_every(total_variants: int, requested: int) -> int:
    req = int(requested)
    if req > 0:
        return req
    if total_variants <= 80:
        return 10
    if total_variants <= 250:
        return 20
    return 50


def _rank_to_decile(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    valid = s.dropna().sort_values(kind="mergesort")
    n = len(valid)
    if n == 0:
        return out
    if n == 1:
        out.loc[valid.index] = 10.0
        return out
    positions = np.arange(n, dtype=float)
    deciles = np.floor(positions * 9.0 / float(n - 1)) + 1.0
    out.loc[valid.index] = deciles
    return out


def _cross_sectional_z_by_date(values: pd.Series, dates: pd.Series) -> pd.Series:
    x = pd.to_numeric(values, errors="coerce")
    d = pd.to_datetime(dates, errors="coerce")
    grouped = pd.DataFrame({"date": d, "x": x})
    mu = grouped.groupby("date")["x"].transform("mean")
    sigma = grouped.groupby("date")["x"].transform("std").replace(0.0, np.nan)
    return (x - mu) / sigma


def _prepare_proxy_components(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce").astype("Int64")
    work = work.dropna(subset=["date", "permno"]).sort_values(["permno", "date"]).reset_index(drop=True)

    sales_raw = pd.to_numeric(work["delta_revenue_inventory"], errors="coerce")
    margin_delta = pd.to_numeric(work["operating_margin_delta_q"], errors="coerce")
    margin_raw = margin_delta.groupby(work["permno"]).diff()
    inv_to_rev = 1.0 / pd.to_numeric(work["revenue_inventory_q"], errors="coerce").replace(0.0, np.nan)
    bloat_raw = inv_to_rev.groupby(work["permno"]).diff()
    net_raw = pd.to_numeric(work["asset_growth_yoy"], errors="coerce")

    out = pd.DataFrame(index=work.index)
    out["sales_z"] = _cross_sectional_z_by_date(sales_raw, work["date"])
    out["margin_z"] = _cross_sectional_z_by_date(margin_raw, work["date"])
    out["bloat_z"] = _cross_sectional_z_by_date(bloat_raw, work["date"])
    out["netinv_z"] = _cross_sectional_z_by_date(net_raw, work["date"])
    out["date"] = work["date"].values
    out["permno"] = work["permno"].astype(int).values
    return out


def _prepare_high_growth_base(
    frame: pd.DataFrame,
    components: pd.DataFrame,
    high_asset_growth_pct: float,
    min_high_group_size: int,
) -> pd.DataFrame:
    base = frame.copy()
    base["date"] = pd.to_datetime(base["date"], errors="coerce")
    base["permno"] = pd.to_numeric(base["permno"], errors="coerce").astype("Int64")
    base = base.dropna(subset=["date", "permno", "industry", "asset_growth_yoy", "fwd_return"])
    base["permno"] = base["permno"].astype(int)
    merged = base.merge(
        components[["date", "permno", "sales_z", "margin_z", "bloat_z", "netinv_z"]],
        on=["date", "permno"],
        how="left",
    )
    high_threshold = 1.0 - float(high_asset_growth_pct)
    merged["ag_rank_pct"] = merged.groupby(["date", "industry"])["asset_growth_yoy"].rank(method="first", pct=True)
    high = merged[merged["ag_rank_pct"] >= high_threshold].copy()
    if high.empty:
        return high
    high["high_group_size"] = high.groupby(["date", "industry"])["permno"].transform("size")
    if int(min_high_group_size) > 0:
        high = high[high["high_group_size"] >= int(min_high_group_size)].copy()
    return high.reset_index(drop=True)

def _variant_spread_timeseries(
    high_base: pd.DataFrame,
    w_sales: float,
    w_margin: float,
    w_bloat: float,
    w_netinv: float,
    gate_threshold: float,
    min_high_group_size: int,
) -> pd.DataFrame:
    if high_base.empty:
        return pd.DataFrame(columns=["date", "spread"])
    proxy = (
        (float(w_sales) * pd.to_numeric(high_base["sales_z"], errors="coerce"))
        + (float(w_margin) * pd.to_numeric(high_base["margin_z"], errors="coerce"))
        + (float(w_bloat) * pd.to_numeric(high_base["bloat_z"], errors="coerce"))
        + (float(w_netinv) * pd.to_numeric(high_base["netinv_z"], errors="coerce"))
    )
    work = high_base[["date", "industry", "permno", "fwd_return"]].copy()
    work["proxy_score"] = proxy
    work = work[work["proxy_score"] > float(gate_threshold)].copy()
    if work.empty:
        return pd.DataFrame(columns=["date", "spread"])

    if int(min_high_group_size) > 0:
        work["group_size_after_gate"] = work.groupby(["date", "industry"])["permno"].transform("size")
        work = work[work["group_size_after_gate"] >= int(min_high_group_size)].copy()
    if work.empty:
        return pd.DataFrame(columns=["date", "spread"])

    work["proxy_decile"] = (
        work.groupby(["date", "industry"], group_keys=False)["proxy_score"]
        .transform(_rank_to_decile)
        .astype("Int64")
    )
    work = work.dropna(subset=["proxy_decile"]).copy()
    if work.empty:
        return pd.DataFrame(columns=["date", "spread"])
    work["proxy_decile"] = work["proxy_decile"].astype(int)

    dec = (
        work.groupby(["date", "proxy_decile"])["fwd_return"]
        .mean()
        .unstack("proxy_decile")
        .sort_index()
    )
    if 1 not in dec.columns:
        dec[1] = np.nan
    if 10 not in dec.columns:
        dec[10] = np.nan
    spread = (dec[10] - dec[1]).rename("spread")
    out = spread.reset_index()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    return out.sort_values("date").reset_index(drop=True)


def _build_coarse_grid(cfg: SweepConfig) -> list[dict[str, float]]:
    grid: list[dict[str, float]] = []
    for ws, wm, wb, wn, gt in itertools.product(
        cfg.coarse_sales_weights,
        cfg.coarse_margin_weights,
        cfg.coarse_bloat_weights,
        cfg.coarse_netinv_weights,
        cfg.coarse_gate_thresholds,
    ):
        grid.append(
            {
                "w_sales": _sql_safe_float(ws),
                "w_margin": _sql_safe_float(wm),
                "w_bloat": _sql_safe_float(wb),
                "w_netinv": _sql_safe_float(wn),
                "gate_threshold": _sql_safe_float(gt),
            }
        )
    return grid


def _build_fine_grid(best: dict[str, float], cfg: SweepConfig) -> list[dict[str, float]]:
    sales = sorted(set([best["w_sales"] - cfg.fine_step_sales, best["w_sales"], best["w_sales"] + cfg.fine_step_sales]))
    margin = sorted(set([best["w_margin"] - cfg.fine_step_margin, best["w_margin"], best["w_margin"] + cfg.fine_step_margin]))
    bloat = sorted(set([best["w_bloat"] - cfg.fine_step_bloat, best["w_bloat"], best["w_bloat"] + cfg.fine_step_bloat]))
    netinv = sorted(set([best["w_netinv"] - cfg.fine_step_netinv, best["w_netinv"], best["w_netinv"] + cfg.fine_step_netinv]))
    gate = sorted(set([best["gate_threshold"] - cfg.fine_step_gate, best["gate_threshold"], best["gate_threshold"] + cfg.fine_step_gate]))
    out: list[dict[str, float]] = []
    for ws, wm, wb, wn, gt in itertools.product(sales, margin, bloat, netinv, gate):
        out.append(
            {
                "w_sales": _sql_safe_float(ws),
                "w_margin": _sql_safe_float(wm),
                "w_bloat": _sql_safe_float(wb),
                "w_netinv": _sql_safe_float(wn),
                "gate_threshold": _sql_safe_float(gt),
            }
        )
    return out


def _sample_grid(grid: list[dict[str, float]], max_count: int, seed: int) -> list[dict[str, float]]:
    if len(grid) <= int(max_count):
        return grid
    rng = np.random.default_rng(int(seed))
    picked = rng.choice(len(grid), size=int(max_count), replace=False)
    selected = [grid[int(i)] for i in sorted(picked.tolist())]
    return selected


def _attach_dsr_metrics(
    results: pd.DataFrame,
    streams: pd.DataFrame,
    horizon_days: int,
) -> tuple[pd.DataFrame, float, float]:
    if results.empty:
        return results.copy(), 0.0, 1.0
    annual_factor = 252.0 / max(float(horizon_days), 1.0)
    avg_corr = average_pairwise_correlation(streams)
    n_eff = effective_number_of_trials(streams)
    sr_estimates = pd.to_numeric(results["annualized_sharpe"], errors="coerce")

    dsr_rows: list[dict[str, float]] = []
    for _, row in results.iterrows():
        vid = str(row["variant_id"])
        ret = streams[vid] if vid in streams.columns else pd.Series(dtype=float)
        ds = deflated_sharpe_ratio(
            returns=ret,
            sr_estimates=sr_estimates,
            n_trials_eff=n_eff,
            periods_per_year=annual_factor,
        )
        dsr_rows.append(
            {
                "variant_id": vid,
                "dsr": float(ds["dsr"]),
                "psr": float(ds["psr"]),
                "sr_hat": float(ds["sr_hat"]),
                "sr_benchmark": float(ds["sr_benchmark"]),
                "n_obs_returns": float(ds["n_obs"]),
                "skewness": float(ds["skewness"]),
                "kurtosis": float(ds["kurtosis"]),
            }
        )
    dsr_df = pd.DataFrame(dsr_rows)

    out = results.copy()
    drop_cols = [c for c in ["dsr", "psr", "sr_hat", "sr_benchmark", "n_obs_returns", "skewness", "kurtosis"] if c in out.columns]
    if drop_cols:
        out = out.drop(columns=drop_cols)
    out = out.merge(dsr_df, on="variant_id", how="left")
    return out, float(avg_corr), float(n_eff)

def _evaluate_grid(
    stage: str,
    grid: list[dict[str, float]],
    high_base: pd.DataFrame,
    horizon_days: int,
    nw_lags: int | None,
    min_high_group_size: int,
    existing_results: pd.DataFrame | None = None,
    existing_streams: pd.DataFrame | None = None,
    checkpoint_every: int = 0,
    checkpoint_callback: Callable[[str, pd.DataFrame, pd.DataFrame, int, int, bool], None] | None = None,
    summarize_spread_fn: Callable[..., dict[str, Any]] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if summarize_spread_fn is None:
        _, _, summarize_spread_fn = _load_eval_api()

    grid_items = _dedupe_grid_by_variant_id(grid)
    total = len(grid_items)
    if total == 0:
        return pd.DataFrame(), pd.DataFrame()

    existing_results = existing_results.copy() if existing_results is not None else pd.DataFrame()
    existing_streams = existing_streams.copy() if existing_streams is not None else pd.DataFrame()
    if "variant_id" in existing_results.columns:
        existing_results["variant_id"] = existing_results["variant_id"].astype(str)

    stage_ids = [str(item["variant_id"]) for item in grid_items]
    existing_result_ids = set(existing_results["variant_id"].tolist()) if "variant_id" in existing_results.columns else set()
    existing_stream_ids = set(existing_streams.columns.tolist()) if not existing_streams.empty else set()
    completed_ids = set([vid for vid in stage_ids if vid in existing_result_ids and vid in existing_stream_ids])

    stage_existing_results = (
        existing_results[existing_results["variant_id"].isin(completed_ids)].copy()
        if "variant_id" in existing_results.columns
        else pd.DataFrame()
    )
    stage_existing_results = stage_existing_results.drop_duplicates(subset=["variant_id"], keep="last")

    rows: list[dict[str, Any]] = stage_existing_results.to_dict(orient="records")
    spread_streams: dict[str, pd.Series] = {}
    if not existing_streams.empty:
        for vid in sorted(completed_ids):
            spread_streams[vid] = pd.to_numeric(existing_streams[vid], errors="coerce").astype(float).rename(vid)

    pending = [item for item in grid_items if str(item["variant_id"]) not in completed_ids]
    completed_initial = len(completed_ids)

    if completed_initial > 0:
        print(f"[{stage}] resume hit {completed_initial}/{total}")

    pending_total = len(pending)
    for i, item in enumerate(pending, start=1):
        variant_id = str(item["variant_id"])
        params = {k: float(item[k]) for k in ["w_sales", "w_margin", "w_bloat", "w_netinv", "gate_threshold"]}
        spread_df = _variant_spread_timeseries(
            high_base=high_base,
            w_sales=params["w_sales"],
            w_margin=params["w_margin"],
            w_bloat=params["w_bloat"],
            w_netinv=params["w_netinv"],
            gate_threshold=params["gate_threshold"],
            min_high_group_size=min_high_group_size,
        )
        summary = summarize_spread_fn(spread_df=spread_df, horizon_days=horizon_days, nw_lags=nw_lags)
        spread_series = (
            spread_df.set_index("date")["spread"]
            if not spread_df.empty
            else pd.Series(dtype=float, name="spread")
        )
        spread_streams[variant_id] = spread_series.astype(float).rename(variant_id)
        rows.append(
            {
                "variant_id": variant_id,
                "stage": stage,
                **params,
                **summary,
            }
        )
        completed_now = completed_initial + i
        if i % 20 == 0 or i == pending_total:
            print(f"[{stage}] evaluated {completed_now}/{total}")
        if checkpoint_callback and checkpoint_every > 0 and ((i % checkpoint_every == 0) or (i == pending_total)):
            partial_results = pd.DataFrame(rows).drop_duplicates(subset=["variant_id"], keep="last")
            partial_streams = pd.concat(spread_streams.values(), axis=1) if spread_streams else pd.DataFrame()
            partial_streams.index = pd.to_datetime(partial_streams.index, errors="coerce")
            partial_streams = partial_streams[~partial_streams.index.isna()].sort_index()
            checkpoint_callback(stage, partial_results, partial_streams, completed_now, total, i == pending_total)

    if pending_total == 0 and checkpoint_callback:
        partial_results = pd.DataFrame(rows).drop_duplicates(subset=["variant_id"], keep="last")
        partial_streams = pd.concat(spread_streams.values(), axis=1) if spread_streams else pd.DataFrame()
        partial_streams.index = pd.to_datetime(partial_streams.index, errors="coerce")
        partial_streams = partial_streams[~partial_streams.index.isna()].sort_index()
        checkpoint_callback(stage, partial_results, partial_streams, completed_initial, total, True)

    results_df = pd.DataFrame(rows)
    if not results_df.empty:
        results_df = results_df.drop_duplicates(subset=["variant_id"], keep="last").reset_index(drop=True)
    stream_df = pd.concat(spread_streams.values(), axis=1) if spread_streams else pd.DataFrame()
    stream_df.index = pd.to_datetime(stream_df.index, errors="coerce")
    stream_df = stream_df[~stream_df.index.isna()].sort_index()
    return results_df, stream_df


def _best_row(df: pd.DataFrame, primary_metric: str = "t_stat_nw") -> pd.Series:
    if df.empty:
        raise ValueError("No sweep results available.")
    ranked = df.copy()
    ranked["dsr_sort"] = pd.to_numeric(ranked.get("dsr", np.nan), errors="coerce").fillna(-np.inf)
    ranked["t_stat_nw_sort"] = pd.to_numeric(ranked["t_stat_nw"], errors="coerce").fillna(-np.inf)
    ranked["period_mean_sort"] = pd.to_numeric(ranked["period_mean"], errors="coerce").fillna(-np.inf)
    ranked["variant_id_sort"] = ranked["variant_id"].astype(str)
    if str(primary_metric).strip().lower() == "dsr":
        ranked = ranked.sort_values(
            ["dsr_sort", "t_stat_nw_sort", "period_mean_sort", "variant_id_sort"],
            ascending=[False, False, False, True],
            kind="mergesort",
        )
    else:
        ranked = ranked.sort_values(
            ["t_stat_nw_sort", "period_mean_sort", "variant_id_sort"],
            ascending=[False, False, True],
            kind="mergesort",
        )
    return ranked.iloc[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 17.2 parameter sweep with CSCV + DSR.")
    parser.add_argument("--panel-path", default=os.path.join(PROCESSED_DIR, "daily_fundamentals_panel.parquet"))
    parser.add_argument("--prices-path", default=os.path.join(PROCESSED_DIR, "prices.parquet"))
    parser.add_argument("--features-path", default=os.path.join(PROCESSED_DIR, "features.parquet"))
    parser.add_argument("--sector-map-path", default=os.path.join(PROJECT_ROOT, "data", "static", "sector_map.parquet"))
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--horizon-days", type=int, default=21)
    parser.add_argument("--high-asset-growth-pct", type=float, default=0.30)
    parser.add_argument("--min-high-group-size", type=int, default=2)
    parser.add_argument("--nw-lags", type=int, default=None)
    parser.add_argument("--cscv-blocks", type=int, default=6, help="Even number of CSCV blocks (e.g., 6, 8, 10).")
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--coarse-sales-weights", default="0,1")
    parser.add_argument("--coarse-margin-weights", default="0,1")
    parser.add_argument("--coarse-bloat-weights", default="-1,0")
    parser.add_argument("--coarse-netinv-weights", default="-1,-0.5,0")
    parser.add_argument("--coarse-gate-thresholds", default="-0.5,0,0.5")
    parser.add_argument("--max-coarse-combos", type=int, default=200)

    parser.add_argument("--fine-step-sales", type=float, default=0.25)
    parser.add_argument("--fine-step-margin", type=float, default=0.25)
    parser.add_argument("--fine-step-bloat", type=float, default=0.25)
    parser.add_argument("--fine-step-netinv", type=float, default=0.25)
    parser.add_argument("--fine-step-gate", type=float, default=0.10)
    parser.add_argument("--max-fine-combos", type=int, default=96)

    parser.add_argument("--checkpoint-every", type=int, default=0, help="Checkpoint every N evaluated variants (0=auto by grid size).")
    parser.add_argument("--no-resume", action="store_true", help="Ignore checkpoint files and run sweep from scratch.")
    parser.add_argument("--keep-checkpoint", action="store_true", help="Keep checkpoint files after successful completion.")
    parser.add_argument(
        "--lock-stale-seconds",
        type=int,
        default=DEFAULT_SWEEP_LOCK_STALE_SECONDS,
        help="Stale sweep-lock fallback TTL in seconds when lock PID is unavailable/invalid (default: 21600).",
    )
    parser.add_argument("--output-dir", default=PROCESSED_DIR)
    parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX)
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    cfg = SweepConfig(
        panel_path=str(args.panel_path),
        prices_path=str(args.prices_path),
        features_path=str(args.features_path),
        sector_map_path=str(args.sector_map_path),
        start_date=str(args.start_date) if args.start_date else None,
        end_date=str(args.end_date) if args.end_date else None,
        horizon_days=int(args.horizon_days),
        high_asset_growth_pct=float(args.high_asset_growth_pct),
        min_high_group_size=int(args.min_high_group_size),
        nw_lags=int(args.nw_lags) if args.nw_lags is not None else None,
        cscv_blocks=int(args.cscv_blocks),
        seed=int(args.seed),
        coarse_sales_weights=_parse_float_list(args.coarse_sales_weights),
        coarse_margin_weights=_parse_float_list(args.coarse_margin_weights),
        coarse_bloat_weights=_parse_float_list(args.coarse_bloat_weights),
        coarse_netinv_weights=_parse_float_list(args.coarse_netinv_weights),
        coarse_gate_thresholds=_parse_float_list(args.coarse_gate_thresholds),
        fine_step_sales=float(args.fine_step_sales),
        fine_step_margin=float(args.fine_step_margin),
        fine_step_bloat=float(args.fine_step_bloat),
        fine_step_netinv=float(args.fine_step_netinv),
        fine_step_gate=float(args.fine_step_gate),
        max_coarse_combos=int(args.max_coarse_combos),
        max_fine_combos=int(args.max_fine_combos),
        checkpoint_every=int(args.checkpoint_every),
        resume=(not bool(args.no_resume)),
        keep_checkpoint=bool(args.keep_checkpoint),
        output_dir=str(args.output_dir),
        output_prefix=str(args.output_prefix),
    )
    if cfg.cscv_blocks % 2 != 0:
        raise ValueError("--cscv-blocks must be even.")

    os.makedirs(cfg.output_dir, exist_ok=True)
    lock_path = _acquire_sweep_lock(
        output_dir=cfg.output_dir,
        output_prefix=cfg.output_prefix,
        stale_lock_seconds=max(1, int(args.lock_stale_seconds)),
    )
    t0 = time.perf_counter()
    EvalConfig, load_eval_frame, summarize_spread = _load_eval_api()

    eval_cfg = EvalConfig(
        panel_path=cfg.panel_path,
        prices_path=cfg.prices_path,
        features_path=cfg.features_path,
        sector_map_path=cfg.sector_map_path,
        start_date=cfg.start_date,
        end_date=cfg.end_date,
        horizon_days=cfg.horizon_days,
        high_asset_growth_pct=cfg.high_asset_growth_pct,
        min_high_group_size=cfg.min_high_group_size,
        nw_lags=cfg.nw_lags,
        run_fama_macbeth=False,
        output_dir=cfg.output_dir,
        output_prefix=cfg.output_prefix,
    )

    try:
        frame = load_eval_frame(eval_cfg)
        if frame.empty:
            raise RuntimeError("No eligible rows loaded for parameter sweep.")

        components = _prepare_proxy_components(frame)
        high_base = _prepare_high_growth_base(
            frame=frame,
            components=components,
            high_asset_growth_pct=cfg.high_asset_growth_pct,
            min_high_group_size=cfg.min_high_group_size,
        )
        if high_base.empty:
            raise RuntimeError("High asset growth base universe is empty after preprocessing.")

        checkpoint_paths = _checkpoint_paths(cfg.output_dir, cfg.output_prefix)
        checkpoint_results = pd.DataFrame()
        checkpoint_streams = pd.DataFrame()
        checkpoint_meta: dict[str, Any] = {}
        if cfg.resume:
            checkpoint_results, checkpoint_streams, checkpoint_meta = _load_checkpoint(checkpoint_paths)
            if not checkpoint_results.empty:
                print(
                    f"Loaded checkpoint: variants={len(checkpoint_results)}, "
                    f"last_stage={checkpoint_meta.get('stage')}, stage_completed={checkpoint_meta.get('stage_completed')}"
                )

        state: dict[str, Any] = {
            "results": checkpoint_results.copy(),
            "streams": checkpoint_streams.copy(),
        }

        def _checkpoint_callback(
            stage: str,
            stage_results: pd.DataFrame,
            stage_streams: pd.DataFrame,
            completed: int,
            total: int,
            stage_completed: bool,
        ) -> None:
            state["results"] = _merge_results(state["results"], stage_results)
            state["streams"] = _merge_streams(state["streams"], stage_streams)
            meta = {
                "stage": stage,
                "stage_completed": bool(stage_completed),
                "completed_variants": int(completed),
                "total_variants_stage": int(total),
                "updated_at_utc": pd.Timestamp.utcnow().isoformat(),
                "output_prefix": cfg.output_prefix,
            }
            _save_checkpoint(
                paths=checkpoint_paths,
                results=state["results"],
                streams=state["streams"],
                meta=meta,
            )

        coarse_grid = _build_coarse_grid(cfg)
        coarse_grid = _sample_grid(coarse_grid, max_count=cfg.max_coarse_combos, seed=cfg.seed)
        print(f"Coarse grid size: {len(coarse_grid)}")
        coarse_checkpoint_every = _resolve_checkpoint_every(len(coarse_grid), cfg.checkpoint_every)
        coarse_results, coarse_streams = _evaluate_grid(
            stage="coarse",
            grid=coarse_grid,
            high_base=high_base,
            horizon_days=cfg.horizon_days,
            nw_lags=cfg.nw_lags,
            min_high_group_size=cfg.min_high_group_size,
            existing_results=state["results"],
            existing_streams=state["streams"],
            checkpoint_every=coarse_checkpoint_every,
            checkpoint_callback=_checkpoint_callback,
            summarize_spread_fn=summarize_spread,
        )
        coarse_results, _, _ = _attach_dsr_metrics(
            results=coarse_results,
            streams=coarse_streams,
            horizon_days=cfg.horizon_days,
        )
        _checkpoint_callback(
            stage="coarse",
            stage_results=coarse_results,
            stage_streams=coarse_streams,
            completed=int(len(coarse_results)),
            total=int(len(_dedupe_grid_by_variant_id(coarse_grid))),
            stage_completed=True,
        )

        coarse_best = _best_row(coarse_results, primary_metric="dsr")
        fine_seed = cfg.seed + 17
        fine_grid = _build_fine_grid(
            best={
                "w_sales": float(coarse_best["w_sales"]),
                "w_margin": float(coarse_best["w_margin"]),
                "w_bloat": float(coarse_best["w_bloat"]),
                "w_netinv": float(coarse_best["w_netinv"]),
                "gate_threshold": float(coarse_best["gate_threshold"]),
            },
            cfg=cfg,
        )
        fine_grid = _sample_grid(fine_grid, max_count=cfg.max_fine_combos, seed=fine_seed)
        print(f"Fine grid size: {len(fine_grid)}")
        fine_checkpoint_every = _resolve_checkpoint_every(len(fine_grid), cfg.checkpoint_every)
        fine_results, fine_streams = _evaluate_grid(
            stage="fine",
            grid=fine_grid,
            high_base=high_base,
            horizon_days=cfg.horizon_days,
            nw_lags=cfg.nw_lags,
            min_high_group_size=cfg.min_high_group_size,
            existing_results=state["results"],
            existing_streams=state["streams"],
            checkpoint_every=fine_checkpoint_every,
            checkpoint_callback=_checkpoint_callback,
            summarize_spread_fn=summarize_spread,
        )
        _checkpoint_callback(
            stage="fine",
            stage_results=fine_results,
            stage_streams=fine_streams,
            completed=int(len(fine_results)),
            total=int(len(_dedupe_grid_by_variant_id(fine_grid))),
            stage_completed=True,
        )

        active_variant_ids = sorted(
            {
                str(item["variant_id"])
                for item in (_dedupe_grid_by_variant_id(coarse_grid) + _dedupe_grid_by_variant_id(fine_grid))
            }
        )
        results = state["results"].copy()
        if "variant_id" in results.columns:
            results["variant_id"] = results["variant_id"].astype(str)
            results = results[results["variant_id"].isin(active_variant_ids)].copy()
        results = results.drop_duplicates(subset=["variant_id"], keep="last").reset_index(drop=True)
        streams = state["streams"].copy()
        keep_cols = [c for c in streams.columns if c in set(active_variant_ids)]
        streams = streams[keep_cols].copy().sort_index()

        results, avg_corr, n_eff = _attach_dsr_metrics(
            results=results,
            streams=streams,
            horizon_days=cfg.horizon_days,
        )

        annual_factor = 252.0 / max(float(cfg.horizon_days), 1.0)
        cscv = cscv_analysis(
            return_matrix=streams,
            n_blocks=cfg.cscv_blocks,
            periods_per_year=annual_factor,
        )

        ranked = results.copy()
        ranked["dsr_sort"] = pd.to_numeric(ranked["dsr"], errors="coerce").fillna(-np.inf)
        ranked["t_stat_sort"] = pd.to_numeric(ranked["t_stat_nw"], errors="coerce").fillna(-np.inf)
        ranked["mean_sort"] = pd.to_numeric(ranked["period_mean"], errors="coerce").fillna(-np.inf)
        ranked["variant_id_sort"] = ranked["variant_id"].astype(str)
        ranked = ranked.sort_values(
            ["dsr_sort", "t_stat_sort", "mean_sort", "variant_id_sort"],
            ascending=[False, False, False, True],
            kind="mergesort",
        )
        best = ranked.iloc[0]

        results_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_grid_results.csv")
        streams_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_return_streams.csv")
        cscv_splits_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_cscv_splits.csv")
        cscv_summary_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_cscv_summary.json")
        best_path = os.path.join(cfg.output_dir, f"{cfg.output_prefix}_best_variant.json")

        _atomic_write_csv(results, results_path)
        _atomic_write_csv(streams.reset_index().rename(columns={"index": "date"}), streams_path)
        _atomic_write_csv(cscv.split_results, cscv_splits_path)

        runtime_seconds = float(time.perf_counter() - t0)
        cscv_summary = {
            "summary": cscv.summary,
            "n_variants": int(results.shape[0]),
            "avg_pairwise_correlation": float(avg_corr),
            "effective_trials": float(n_eff),
            "coarse_grid_size": int(len(coarse_grid)),
            "fine_grid_size": int(len(fine_grid)),
            "runtime_seconds": runtime_seconds,
        }
        _atomic_write_json(cscv_summary, cscv_summary_path)

        best_payload = {
            "variant_id": str(best["variant_id"]),
            "stage": str(best["stage"]),
            "params": {
                "w_sales": float(best["w_sales"]),
                "w_margin": float(best["w_margin"]),
                "w_bloat": float(best["w_bloat"]),
                "w_netinv": float(best["w_netinv"]),
                "gate_threshold": float(best["gate_threshold"]),
            },
            "metrics": {
                "period_mean": float(best["period_mean"]),
                "period_vol": float(best["period_vol"]),
                "annualized_sharpe": float(best["annualized_sharpe"]),
                "t_stat_nw": float(best["t_stat_nw"]),
                "dsr": float(best["dsr"]),
                "psr": float(best["psr"]),
            },
            "cscv": cscv.summary,
            "effective_trials": float(n_eff),
            "avg_pairwise_correlation": float(avg_corr),
        }
        _atomic_write_json(best_payload, best_path)

        if not cfg.keep_checkpoint:
            _clear_checkpoint(checkpoint_paths)

        print("Sweep complete")
        print(
            f"  variants={len(results)}, coarse={len(coarse_grid)}, fine={len(fine_grid)}, "
            f"pbo={cscv.summary.get('pbo')}, neff={n_eff:.2f}, runtime={runtime_seconds:.1f}s"
        )
        print(
            f"  best={best_payload['variant_id']} "
            f"(dsr={best_payload['metrics']['dsr']:.4f}, t={best_payload['metrics']['t_stat_nw']:.3f}, "
            f"mean={best_payload['metrics']['period_mean']:.6f})"
        )
        print(f"Wrote: {results_path}")
        print(f"Wrote: {streams_path}")
        print(f"Wrote: {cscv_splits_path}")
        print(f"Wrote: {cscv_summary_path}")
        print(f"Wrote: {best_path}")
    finally:
        _release_sweep_lock(lock_path)


if __name__ == "__main__":
    main()
