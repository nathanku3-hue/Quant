from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from utils.spa import BootstrapConfig, spa_wrc_pvalues
from utils.statistics import (
    build_cscv_splits,
    cscv_analysis,
    deflated_sharpe_ratio,
    effective_number_of_trials,
    safe_sharpe,
)
DEFAULT_SQL_PATH = PROJECT_ROOT / "allocator_cpcv.sql"
DEFAULT_SPLITS_ROOT = PROJECT_ROOT / "research_data" / "alloc_cpcv_splits"
DEFAULT_MAX_DATE = "2022-12-31"
RESEARCH_MAX_DATE = date(2022, 12, 31)
DEFAULT_EVIDENCE_PATH = PROJECT_ROOT / "data" / "processed" / "phase55_allocator_cpcv_evidence.json"
DEFAULT_SUMMARY_PATH = PROJECT_ROOT / "data" / "processed" / "phase55_allocator_cpcv_summary.json"
ATOMIC_REPLACE_MAX_RETRIES = 8
ATOMIC_REPLACE_BASE_SLEEP_SECONDS = 0.01


@dataclass(frozen=True)
class NestedCPCVConfig:
    n_blocks: int = 6
    periods_per_year: float = 252.0
    spa_min_obs: int = 20
    spa_bootstrap: BootstrapConfig | None = None


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _atomic_replace_with_retry(src: Path, dest: Path) -> None:
    last_exc: Exception | None = None
    for attempt in range(ATOMIC_REPLACE_MAX_RETRIES):
        try:
            os.replace(src, dest)
            return
        except PermissionError as exc:
            last_exc = exc
            time.sleep(ATOMIC_REPLACE_BASE_SLEEP_SECONDS * (attempt + 1))
    if last_exc is not None:
        raise last_exc


def _atomic_write_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.{os.getpid()}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _require_columns(frame: pd.DataFrame, required: list[str]) -> None:
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _validate_max_date(raw_value: str) -> str:
    parsed = date.fromisoformat(str(raw_value))
    if parsed > RESEARCH_MAX_DATE:
        raise ValueError(
            f"max_date must be <= {RESEARCH_MAX_DATE.isoformat()} for the research holdout guard"
        )
    return parsed.isoformat()


def _render_sql(template: str, splits_root: Path, max_date: str) -> str:
    rendered = template.replace("{splits_root}", splits_root.as_posix())
    rendered = rendered.replace("{max_date}", max_date)
    return rendered.strip().rstrip(";")


def _apply_guard(sql: str, max_date: str) -> str:
    guard = f"snapshot_date <= DATE '{max_date}'"
    return f"SELECT * FROM ({sql}) AS base WHERE {guard}"


def _coerce_fold_ids(values: pd.Series) -> pd.Series:
    parsed = pd.to_numeric(values, errors="coerce").astype(float)
    finite_mask = pd.Series(np.isfinite(parsed.to_numpy(dtype=float)), index=parsed.index)
    integral_mask = pd.Series(np.floor(parsed.to_numpy(dtype=float)) == parsed.to_numpy(dtype=float), index=parsed.index)
    invalid = parsed.isna() | ~finite_mask | ~integral_mask
    if bool(invalid.any()):
        raise ValueError("allocator_state contains malformed fold rows")
    return parsed.astype(int)


def _coerce_snapshot_dates(values: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce", utc=True, format="mixed")
    invalid = parsed.isna()
    if bool(invalid.any()):
        raise ValueError("allocator_state contains malformed snapshot_date rows")
    return parsed.dt.tz_convert(None).dt.normalize()


def _normalize_variant_ids(values: pd.Series) -> pd.Series:
    parsed = values.astype("string")
    invalid = parsed.isna() | parsed.str.strip().eq("")
    if bool(invalid.any()):
        raise ValueError("allocator_state contains malformed variant_id rows")
    return parsed.str.strip().astype(str)


def _coerce_period_returns(values: pd.Series) -> pd.Series:
    parsed = pd.to_numeric(values, errors="coerce").astype(float)
    finite_mask = pd.Series(np.isfinite(parsed.to_numpy(dtype=float)), index=parsed.index)
    invalid = parsed.isna() | ~finite_mask
    if bool(invalid.any()):
        raise ValueError("allocator_state contains malformed period_return rows")
    return parsed


def _build_return_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    duplicate_rows = frame.duplicated(subset=["snapshot_date", "variant_id"], keep=False)
    if bool(duplicate_rows.any()):
        raise ValueError(
            "allocator_state contains duplicate (snapshot_date, variant_id) rows within the same fold slice"
        )
    pivot = frame.pivot(
        index="snapshot_date",
        columns="variant_id",
        values="period_return",
    )
    pivot = pivot.sort_index()
    pivot = pivot.dropna(axis=0, how="all")
    pivot = pivot.dropna(axis=1, how="all")
    return pivot


def _select_variant_from_cscv(split_results: pd.DataFrame) -> str | None:
    if split_results is None or split_results.empty:
        return None
    grouped = split_results.groupby("selected_variant", as_index=False).agg(
        selection_count=("selected_variant", "size"),
        median_test_sharpe=("selected_test_sharpe", "median"),
        median_train_sharpe=("selected_train_sharpe", "median"),
    )
    grouped = grouped.sort_values(
        by=["selection_count", "median_test_sharpe", "median_train_sharpe", "selected_variant"],
        ascending=[False, False, False, True],
    )
    return str(grouped.iloc[0]["selected_variant"])


def _parse_max_date(max_date: str | date) -> date:
    if isinstance(max_date, date):
        return max_date
    return date.fromisoformat(str(max_date))


def _validate_outer_fold_contract(frame: pd.DataFrame) -> list[int]:
    folds = sorted({int(x) for x in frame["fold"].dropna().unique()})
    if len(folds) < 2 or len(folds) % 2 != 0:
        raise ValueError("outer CPCV requires an even number of folds >= 2")

    same_fold_dupes = frame.duplicated(subset=["fold", "snapshot_date", "variant_id"], keep=False)
    if bool(same_fold_dupes.any()):
        raise ValueError(
            "allocator_state contains duplicate (fold, snapshot_date, variant_id) rows"
        )

    cross_fold_dupes = (
        frame.groupby(["snapshot_date", "variant_id"])["fold"].nunique().reset_index(name="n_folds")
    )
    if (cross_fold_dupes["n_folds"] > 1).any():
        raise ValueError(
            "allocator_state contains duplicate (snapshot_date, variant_id) rows across multiple folds"
        )

    date_fold_map = frame.groupby("snapshot_date")["fold"].nunique().reset_index(name="n_folds")
    if (date_fold_map["n_folds"] > 1).any():
        raise ValueError("allocator_state violates snapshot_date -> single fold contract")
    return folds


def _build_outer_cpcv_splits(folds: list[int]) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    mapped_splits: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    for train_idx, test_idx in build_cscv_splits(len(folds)):
        mapped_splits.append(
            (
                tuple(folds[idx] for idx in train_idx),
                tuple(folds[idx] for idx in test_idx),
            )
        )
    return mapped_splits


def _aggregate(values: list[float], method: str) -> float:
    arr = np.array(values, dtype=float)
    if arr.size == 0 or not np.isfinite(arr).all():
        return float("nan")
    if method == "mean":
        return float(np.mean(arr))
    if method == "median":
        return float(np.median(arr))
    raise ValueError(f"Unknown aggregation method: {method}")


def compute_nested_cpcv(
    frame: pd.DataFrame,
    config: NestedCPCVConfig,
    max_date: str | date = DEFAULT_MAX_DATE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    required = ["fold", "snapshot_date", "variant_id", "period_return"]
    _require_columns(frame, required)
    if config.n_blocks < 2 or config.n_blocks % 2 != 0:
        raise ValueError("config.n_blocks must be an even integer >= 2")

    parsed_max_date = date.fromisoformat(_validate_max_date(_parse_max_date(max_date).isoformat()))
    snapshot_dates = _coerce_snapshot_dates(frame["snapshot_date"])
    frame = frame.copy()
    frame["fold"] = _coerce_fold_ids(frame["fold"])
    frame["snapshot_date"] = snapshot_dates
    frame["variant_id"] = _normalize_variant_ids(frame["variant_id"])
    frame["period_return"] = _coerce_period_returns(frame["period_return"])
    if not frame.empty:
        max_snapshot = frame["snapshot_date"].max().date()
        if max_snapshot > parsed_max_date:
            raise ValueError(
                f"snapshot_date exceeds max_date guard: {max_snapshot} > {parsed_max_date}"
            )

    folds = _validate_outer_fold_contract(frame)
    outer_splits = _build_outer_cpcv_splits(folds)
    split_results: list[dict[str, Any]] = []

    for split_id, (outer_train_blocks, outer_test_blocks) in enumerate(outer_splits, start=1):
        outer_train = frame[frame["fold"].isin(outer_train_blocks)]
        outer_test = frame[frame["fold"].isin(outer_test_blocks)]

        train_matrix = _build_return_matrix(outer_train)
        test_matrix = _build_return_matrix(outer_test)

        if train_matrix.empty or test_matrix.empty:
            raise ValueError(
                f"outer CPCV split {split_id} produced an empty train/test matrix; evidence surface is incomplete"
            )

        inner = cscv_analysis(
            train_matrix,
            n_blocks=config.n_blocks,
            periods_per_year=config.periods_per_year,
        )
        selected_variant = _select_variant_from_cscv(inner.split_results)
        pbo = float(inner.summary.get("pbo", float("nan")))
        if not selected_variant or not np.isfinite(pbo):
            raise ValueError(
                f"inner CPCV failed to select a variant with finite PBO on outer split {split_id}"
            )

        sr_estimates = train_matrix.apply(
            lambda col: safe_sharpe(col, periods_per_year=config.periods_per_year)
        ).replace([np.inf, -np.inf], np.nan)
        n_trials_eff = effective_number_of_trials(train_matrix)

        if selected_variant not in test_matrix.columns:
            raise ValueError(
                f"selected allocator {selected_variant} has no untouched outer-test series on split {split_id}"
            )
        outer_series = test_matrix[selected_variant].dropna()
        if outer_series.empty:
            raise ValueError(
                f"selected allocator {selected_variant} has an empty untouched outer-test series on split {split_id}"
            )

        dsr_info = deflated_sharpe_ratio(
            returns=outer_series,
            sr_estimates=sr_estimates,
            n_trials_eff=n_trials_eff,
            periods_per_year=config.periods_per_year,
        )
        dsr = float(dsr_info.get("dsr", float("nan")))
        if not np.isfinite(dsr):
            dsr = 0.0

        if not test_matrix.empty:
            spa_wrc = spa_wrc_pvalues(
                returns=test_matrix,
                benchmark=None,
                config=config.spa_bootstrap,
                min_obs=config.spa_min_obs,
            )
            spa_p = float(spa_wrc.get("spa_p", float("nan")))
            wrc_p = float(spa_wrc.get("wrc_p", float("nan")))
        else:
            raise ValueError(f"outer CPCV split {split_id} produced an empty test matrix")
        if not np.isfinite(spa_p):
            spa_p = 1.0
        if not np.isfinite(wrc_p):
            wrc_p = 1.0

        outer_mean = float(outer_series.mean())
        outer_sharpe = safe_sharpe(outer_series, periods_per_year=config.periods_per_year)
        outer_n = int(len(outer_series))
        if not np.isfinite(outer_sharpe):
            outer_sharpe = 0.0

        split_results.append(
            {
                "outer_split_id": int(split_id),
                "outer_train_blocks": ",".join(str(x) for x in outer_train_blocks),
                "outer_test_blocks": ",".join(str(x) for x in outer_test_blocks),
                "selected_variant": selected_variant,
                "pbo": pbo,
                "dsr": dsr,
                "spa_p": spa_p,
                "wrc_p": wrc_p,
                "outer_test_mean": outer_mean,
                "outer_test_sharpe": outer_sharpe,
                "outer_test_n_obs": outer_n,
                "positive_outer_fold": bool(np.isfinite(outer_mean) and outer_mean > 0.0),
            }
        )

    positive_flags = [r["positive_outer_fold"] for r in split_results]
    valid_positive = [flag for flag in positive_flags if isinstance(flag, bool)]
    positive_outer_fold_share = (
        float(sum(1 for flag in valid_positive if flag)) / float(len(valid_positive))
        if valid_positive
        else 0.0
    )

    pbo_agg = _aggregate([r["pbo"] for r in split_results], method="mean")
    dsr_agg = _aggregate([r["dsr"] for r in split_results], method="median")
    spa_p_agg = _aggregate([r["spa_p"] for r in split_results], method="median")
    wrc_p_agg = _aggregate([r["wrc_p"] for r in split_results], method="median")

    def _gate_pass() -> bool:
        metrics = [pbo_agg, dsr_agg, spa_p_agg, positive_outer_fold_share]
        if not all(np.isfinite(m) for m in metrics):
            return False
        return (
            pbo_agg < 0.05
            and dsr_agg > 0.95
            and positive_outer_fold_share >= 0.60
            and spa_p_agg < 0.05
        )

    summary = {
        "created_at": _utc_now_iso_ms(),
        "max_date": parsed_max_date.isoformat(),
        "research_max_date": RESEARCH_MAX_DATE.isoformat(),
        "outer_folds": folds,
        "outer_splits": [
            {
                "outer_train_blocks": ",".join(str(x) for x in train_blocks),
                "outer_test_blocks": ",".join(str(x) for x in test_blocks),
            }
            for train_blocks, test_blocks in outer_splits
        ],
        "n_outer_folds": int(len(folds)),
        "n_outer_splits": int(len(outer_splits)),
        "n_blocks": int(config.n_blocks),
        "periods_per_year": float(config.periods_per_year),
        "aggregation": {
            "pbo": "mean",
            "dsr": "median",
            "spa_p": "median",
            "wrc_p": "median",
        },
        "selection_policy": (
            "selected_variant = argmax(selection_count, median_test_sharpe, "
            "median_train_sharpe, variant_id_ascending)"
        ),
        "pbo": pbo_agg,
        "dsr": dsr_agg,
        "spa_p": spa_p_agg,
        "wrc_p": wrc_p_agg,
        "positive_outer_fold_share": positive_outer_fold_share,
        "allocator_gate_pass": _gate_pass(),
        "allocator_gate_formula": (
            "allocator_gate_pass = 1[(PBO < 0.05) and (DSR > 0.95) and "
            "(positive_outer_fold_share >= 0.60) and (SPA_p < 0.05)]"
        ),
    }

    evidence = {
        "created_at": _utc_now_iso_ms(),
        "max_date": parsed_max_date.isoformat(),
        "outer_folds": folds,
        "outer_splits": [
            {
                "outer_train_blocks": ",".join(str(x) for x in train_blocks),
                "outer_test_blocks": ",".join(str(x) for x in test_blocks),
            }
            for train_blocks, test_blocks in outer_splits
        ],
        "fold_results": split_results,
        "nested_cpcv_definition": (
            "Nested CPCV = each outer CPCV split is the sole source of final allocator evidence, "
            "while allocator ranking/selection is performed only inside an inner CPCV loop built "
            "from that outer-train partition. The selected allocator is then executed exactly once "
            "on the untouched outer-test fold"
        ),
        "guard_predicate": f"snapshot_date <= DATE '{parsed_max_date.isoformat()}'",
        "spa_config": {
            "n_boot": int(config.spa_bootstrap.n_boot) if config.spa_bootstrap else None,
            "seed": int(config.spa_bootstrap.seed) if config.spa_bootstrap and config.spa_bootstrap.seed is not None else None,
            "block_size": int(config.spa_bootstrap.block_size)
            if config.spa_bootstrap and config.spa_bootstrap.block_size is not None
            else None,
            "min_obs": int(config.spa_min_obs),
        },
    }

    return summary, evidence


def _load_cpcv_frame(sql_path: Path, splits_root: Path, max_date: str) -> pd.DataFrame:
    from data.research_connector import connect_research

    template = sql_path.read_text(encoding="utf-8")
    rendered = _render_sql(template, splits_root, max_date)
    guarded = _apply_guard(rendered, max_date)
    with connect_research(root=PROJECT_ROOT / "research_data", threads=8, memory_limit="2GB") as conn:
        return conn.execute(guarded).fetchdf()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 55 nested CPCV allocator governance runner"
    )
    parser.add_argument("--sql", default=None)
    parser.add_argument("--splits-root", default="research_data/alloc_cpcv_splits")
    parser.add_argument("--max-date", default="2022-12-31")
    parser.add_argument("--n-blocks", type=int, default=6)
    parser.add_argument("--periods-per-year", type=int, default=252)
    parser.add_argument("--spa-min-obs", type=int, default=30)
    parser.add_argument("--spa-n-boot", type=int, default=1000)
    parser.add_argument("--spa-seed", type=int, default=42)
    parser.add_argument("--spa-block-size", type=int, default=5)
    parser.add_argument("--summary-path", default="data/processed/phase55_allocator_cpcv_summary.json")
    parser.add_argument("--evidence-path", default="data/processed/phase55_allocator_cpcv_evidence.json")
    # NEW CONTRACT FLAGS (D-310 locked)
    parser.add_argument("--strict", action="store_true", default=False)
    parser.add_argument("--evidence", action="store_true", default=False)
    parser.add_argument("--n-outer", type=int, default=5)
    parser.add_argument("--n-inner", type=int, default=4)
    parser.add_argument("--cost-bps", type=float, default=5.0)
    args = parser.parse_args()
    if args.n_blocks < 2 or args.n_blocks % 2 != 0:
        parser.error("--n-blocks must be an even integer >= 2.")

    sql_path = DEFAULT_SQL_PATH if args.sql is None else Path(args.sql)
    splits_root = Path(args.splits_root)
    summary_path = Path(args.summary_path)
    evidence_path = Path(args.evidence_path)

    max_date = _validate_max_date(str(args.max_date))

    if not sql_path.exists():
        raise FileNotFoundError(f"Missing SQL template: {sql_path}")
    if not splits_root.exists():
        raise FileNotFoundError(f"Missing CPCV shard root: {splits_root}")

    frame = _load_cpcv_frame(sql_path=sql_path, splits_root=splits_root, max_date=max_date)

    spa_config = BootstrapConfig(
        n_boot=max(args.spa_n_boot, 1),
        seed=args.spa_seed,
        block_size=args.spa_block_size if args.spa_block_size > 1 else None,
    )
    config = NestedCPCVConfig(
        n_blocks=args.n_blocks,
        periods_per_year=args.periods_per_year,
        spa_min_obs=args.spa_min_obs,
        spa_bootstrap=spa_config,
    )

    summary, evidence = compute_nested_cpcv(frame=frame, config=config, max_date=max_date)
    summary.update(
        {
            "sql_path": str(sql_path),
            "splits_root": str(splits_root),
        }
    )
    evidence.update(
        {
            "sql_path": str(sql_path),
            "splits_root": str(splits_root),
        }
    )

    _atomic_write_json(summary, summary_path)
    _atomic_write_json(evidence, evidence_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
