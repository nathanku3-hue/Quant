from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
import re
from pathlib import Path
import time
from typing import Any

import duckdb
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_PARQUET = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.parquet"
DEFAULT_SOURCE_DUCKDB = PROJECT_ROOT / "data" / "processed" / "execution_microstructure.duckdb"
DEFAULT_SOURCE_TABLE = "execution_microstructure"
DEFAULT_OUTPUT_SUMMARY_JSON = PROJECT_ROOT / "data" / "processed" / "execution_slippage_baseline_summary.json"
DEFAULT_OUTPUT_BY_SIDE_CSV = PROJECT_ROOT / "data" / "processed" / "execution_slippage_baseline_by_side.csv"
DEFAULT_OUTPUT_BY_SYMBOL_CSV = PROJECT_ROOT / "data" / "processed" / "execution_slippage_baseline_by_symbol.csv"
SOURCE_MODE_DUCKDB_STRICT = "duckdb_strict"
SOURCE_MODE_PARQUET_OVERRIDE = "parquet_override"
SOURCE_MODE_CHOICES = (SOURCE_MODE_DUCKDB_STRICT, SOURCE_MODE_PARQUET_OVERRIDE)
SOURCE_MODE_ENV = "TZ_EXEC_TELEMETRY_SOURCE_MODE"
_TABLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
ATOMIC_REPLACE_MAX_RETRIES = 8
ATOMIC_REPLACE_BASE_SLEEP_SECONDS = 0.01


class PrimarySinkUnavailableError(RuntimeError):
    """Raised when strict-mode DuckDB source cannot be loaded."""


def _utc_now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_table_name(table_name: str) -> str:
    candidate = str(table_name).strip()
    if not candidate:
        raise ValueError("table_name must be non-empty")
    if _TABLE_NAME_PATTERN.fullmatch(candidate) is None:
        raise ValueError(f"unsafe table_name: {table_name}")
    return candidate


def _atomic_write_text(text: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.{os.getpid()}.tmp")
    try:
        with tmp_path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_write_csv(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(f"{output_path.suffix}.{os.getpid()}.tmp")
    try:
        df.to_csv(tmp_path, index=False)
        with tmp_path.open("r+b") as handle:
            os.fsync(handle.fileno())
        _atomic_replace_with_retry(tmp_path, output_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def _atomic_replace_with_retry(
    src: Path,
    dst: Path,
    *,
    max_retries: int = ATOMIC_REPLACE_MAX_RETRIES,
    base_sleep_seconds: float = ATOMIC_REPLACE_BASE_SLEEP_SECONDS,
) -> None:
    attempts = max(int(max_retries), 1)
    for attempt in range(attempts):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            if attempt >= attempts - 1:
                raise
            time.sleep(max(float(base_sleep_seconds), 0.001) * float(attempt + 1))


def _load_source_rows(
    *,
    duckdb_path: Path,
    parquet_path: Path,
    table_name: str,
    source_mode: str | None = None,
) -> pd.DataFrame:
    mode = _resolve_source_mode(source_mode)
    if mode == SOURCE_MODE_PARQUET_OVERRIDE:
        if not parquet_path.exists():
            raise FileNotFoundError(
                "Parquet override requested but source parquet is missing. "
                f"parquet={parquet_path}"
            )
        return pd.read_parquet(parquet_path)

    if not duckdb_path.exists():
        raise PrimarySinkUnavailableError(
            "DuckDB strict mode requires primary sink availability. "
            f"missing duckdb={duckdb_path}"
        )

    table = _validate_table_name(table_name)
    try:
        with duckdb.connect(str(duckdb_path)) as conn:
            return conn.execute(f"SELECT * FROM {table}").df()
    except duckdb.Error as exc:
        raise PrimarySinkUnavailableError(
            "DuckDB strict mode failed to read primary sink. "
            f"duckdb={duckdb_path}, table={table}"
        ) from exc


def _resolve_source_mode(source_mode: str | None) -> str:
    if source_mode is None:
        candidate = str(os.getenv(SOURCE_MODE_ENV, "")).strip().lower()
    else:
        candidate = str(source_mode).strip().lower()
    if not candidate:
        return SOURCE_MODE_DUCKDB_STRICT
    if candidate not in SOURCE_MODE_CHOICES:
        raise ValueError(
            f"Unsupported source mode: {candidate}. "
            f"choices={SOURCE_MODE_CHOICES}, env={SOURCE_MODE_ENV}"
        )
    return candidate


def _sanitize_finite_numeric(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    finite_mask = numeric.apply(lambda value: math.isfinite(float(value)) if pd.notna(value) else False)
    return numeric.mask(~finite_mask)


def compute_slippage_baseline(frame: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    if frame.empty:
        empty = pd.DataFrame()
        return {
            "generated_at_utc": _utc_now_iso_ms(),
            "rows": 0,
            "cohort_rows": 0,
            "observed_rows": 0,
            "zero_imputed_rows": 0,
            "favorable_rows": 0,
            "adverse_rows": 0,
            "neutral_rows": 0,
            "mean_slippage_bps": None,
            "median_slippage_bps": None,
            "total_implementation_shortfall_dollars": 0.0,
            "buy_rows": 0,
            "sell_rows": 0,
        }, empty, empty

    work = frame.copy()
    if "side" not in work.columns:
        work["side"] = ""
    if "symbol" not in work.columns:
        work["symbol"] = ""
    work["side"] = work["side"].astype(str).str.strip().str.lower()
    work["symbol"] = work["symbol"].astype(str).str.strip().str.upper()

    slippage_source = work.get("slippage_bps")
    if slippage_source is None:
        slippage_source = pd.Series([None] * len(work), index=work.index)
    work["slippage_bps"] = _sanitize_finite_numeric(slippage_source)
    work["cohort_slippage_bps"] = work["slippage_bps"].fillna(0.0)
    is_source = work.get("implementation_shortfall_dollars")
    if is_source is None:
        is_source = pd.Series([0.0] * len(work), index=work.index)
    work["implementation_shortfall_dollars"] = _sanitize_finite_numeric(is_source).fillna(0.0)

    observed = work[work["slippage_bps"].notna()].copy()

    summary = {
        "generated_at_utc": _utc_now_iso_ms(),
        "rows": int(len(work)),
        "cohort_rows": int(len(work)),
        "observed_rows": int(len(observed)),
        "zero_imputed_rows": int((~work["slippage_bps"].notna()).sum()),
        "favorable_rows": int((work["cohort_slippage_bps"] < 0.0).sum()),
        "adverse_rows": int((work["cohort_slippage_bps"] > 0.0).sum()),
        "neutral_rows": int((work["cohort_slippage_bps"] == 0.0).sum()),
        "mean_slippage_bps": float(work["cohort_slippage_bps"].mean()),
        "median_slippage_bps": float(work["cohort_slippage_bps"].median()),
        "total_implementation_shortfall_dollars": float(work["implementation_shortfall_dollars"].sum()),
        "buy_rows": int((work["side"] == "buy").sum()),
        "sell_rows": int((work["side"] == "sell").sum()),
    }

    by_side = pd.DataFrame(
        columns=[
            "side",
            "rows",
            "observed_rows",
            "favorable_rows",
            "adverse_rows",
            "neutral_rows",
            "mean_slippage_bps",
            "median_slippage_bps",
            "implementation_shortfall_dollars_sum",
        ]
    )
    if not work.empty:
        by_side = (
            work.groupby("side", dropna=False, as_index=False)
            .agg(
                rows=("cohort_slippage_bps", "size"),
                observed_rows=("slippage_bps", lambda s: int(s.notna().sum())),
                favorable_rows=("cohort_slippage_bps", lambda s: int((s < 0.0).sum())),
                adverse_rows=("cohort_slippage_bps", lambda s: int((s > 0.0).sum())),
                neutral_rows=("cohort_slippage_bps", lambda s: int((s == 0.0).sum())),
                mean_slippage_bps=("cohort_slippage_bps", "mean"),
                median_slippage_bps=("cohort_slippage_bps", "median"),
                implementation_shortfall_dollars_sum=("implementation_shortfall_dollars", "sum"),
            )
            .sort_values(["side"], kind="mergesort")
            .reset_index(drop=True)
        )

    by_symbol = pd.DataFrame(
        columns=[
            "symbol",
            "rows",
            "observed_rows",
            "mean_slippage_bps",
            "median_slippage_bps",
            "implementation_shortfall_dollars_sum",
        ]
    )
    if not work.empty:
        by_symbol = (
            work.groupby("symbol", dropna=False, as_index=False)
            .agg(
                rows=("cohort_slippage_bps", "size"),
                observed_rows=("slippage_bps", lambda s: int(s.notna().sum())),
                mean_slippage_bps=("cohort_slippage_bps", "mean"),
                median_slippage_bps=("cohort_slippage_bps", "median"),
                implementation_shortfall_dollars_sum=("implementation_shortfall_dollars", "sum"),
            )
            .sort_values(["rows", "symbol"], ascending=[False, True], kind="mergesort")
            .reset_index(drop=True)
        )
    return summary, by_side, by_symbol


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate baseline signed slippage metrics from execution telemetry.")
    parser.add_argument("--source-duckdb", default=str(DEFAULT_SOURCE_DUCKDB))
    parser.add_argument("--source-parquet", default=str(DEFAULT_SOURCE_PARQUET))
    parser.add_argument("--source-mode", choices=SOURCE_MODE_CHOICES, default=None)
    parser.add_argument("--table-name", default=DEFAULT_SOURCE_TABLE)
    parser.add_argument("--summary-json", default=str(DEFAULT_OUTPUT_SUMMARY_JSON))
    parser.add_argument("--by-side-csv", default=str(DEFAULT_OUTPUT_BY_SIDE_CSV))
    parser.add_argument("--by-symbol-csv", default=str(DEFAULT_OUTPUT_BY_SYMBOL_CSV))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_df = _load_source_rows(
        duckdb_path=Path(args.source_duckdb),
        parquet_path=Path(args.source_parquet),
        table_name=str(args.table_name),
        source_mode=args.source_mode,
    )
    summary, by_side, by_symbol = compute_slippage_baseline(source_df)

    _atomic_write_text(json.dumps(summary, indent=2, ensure_ascii=True), Path(args.summary_json))
    _atomic_write_csv(by_side, Path(args.by_side_csv))
    _atomic_write_csv(by_symbol, Path(args.by_symbol_csv))

    print(
        "slippage baseline complete | "
        f"rows={summary['rows']} observed={summary['observed_rows']} "
        f"favorable={summary['favorable_rows']} adverse={summary['adverse_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
