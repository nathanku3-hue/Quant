"""Build the D2A security-level daily return contract.

The contract preserves every normalized ``(gvkey, iid)`` series. Total return
is derived from the Compustat total-return level::

    TR_level = prccd * trfd / ajexdi
    total_return = TR_level_t / TR_level_{t-1} - 1

When either total-return level is unavailable, the same-security split-adjusted
price level (``prccd / ajexdi``) is used as a price-return fallback. Lags never
cross GVKEY or IID boundaries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import duckdb

ROOT = Path(__file__).resolve().parent.parent
SECD_PATH = ROOT / "data" / "raw" / "wrds" / "comp_secd_2015_2019.parquet"
DAILY_PATH = ROOT / "data" / "processed" / "prices_daily_compustat.parquet"
OUT_SAMPLE_PATH = ROOT / "data" / "processed" / "pead_d2_daily_returns_sample.parquet"
OUT_FULL_PATH = ROOT / "data" / "processed" / "pead_d2_daily_returns.parquet"

MAX_GAP_DAYS = 5
MAX_RET_ABS = 5.0
SAMPLE_N_GVKEYS = 500
FULL_BUILD_MEMORY_LIMIT = "512MB"
FULL_BUILD_ROW_GROUP_SIZE = 100_000

SOURCE_KEY = ["gvkey", "iid", "date"]
SECURITY_KEY = ["gvkey", "iid"]
STANDARDIZED_COLUMNS = [
    "gvkey",
    "iid",
    "date",
    "tr_level",
    "price_level",
    "dollar_volume",
    "data_source",
]
OUTPUT_COLUMNS = [
    "gvkey",
    "iid",
    "security_id",
    "date",
    "total_return",
    "return_type",
    "dollar_volume",
    "data_source",
    "tr_level",
    "price_level",
    "guardrail_reason",
]


def _require_columns(df: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = sorted(columns.difference(df.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _normalise_identifier(series: pd.Series, name: str) -> pd.Series:
    values = series.astype("string").str.strip()
    invalid = values.isna() | values.eq("")
    if invalid.any():
        raise ValueError(f"{name} contains {int(invalid.sum())} empty identifier(s)")
    return values


def _positive_finite(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").astype("float64")
    return values.where(np.isfinite(values) & values.gt(0.0))


def _finite_nonnegative(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").astype("float64")
    return values.where(np.isfinite(values) & values.ge(0.0))


def _assert_unique_source_keys(df: pd.DataFrame, label: str) -> None:
    _require_columns(df, set(SOURCE_KEY), label)
    duplicate = df.duplicated(SOURCE_KEY, keep=False)
    if duplicate.any():
        examples = df.loc[duplicate, SOURCE_KEY].head(3).to_dict("records")
        raise ValueError(
            f"{label} contains duplicate (gvkey, iid, date) source keys; "
            f"examples={examples}"
        )


def _prepare_source_frame(df: pd.DataFrame, data_source: str) -> pd.DataFrame:
    """Normalize one source without computing lags or dropping any IID series."""
    _require_columns(
        df,
        {"gvkey", "iid", "date", "prccd", "trfd", "ajexdi"},
        data_source,
    )
    work = df.copy()
    work["gvkey"] = _normalise_identifier(work["gvkey"], "gvkey")
    work["iid"] = _normalise_identifier(work["iid"], "iid")

    parsed_date = pd.to_datetime(work["date"], errors="coerce", utc=True)
    if parsed_date.isna().any():
        raise ValueError(
            f"{data_source} contains {int(parsed_date.isna().sum())} invalid date(s)"
        )
    work["date"] = parsed_date.dt.strftime("%Y-%m-%d")
    _assert_unique_source_keys(work, data_source)

    prccd = _positive_finite(work["prccd"])
    trfd = _positive_finite(work["trfd"])
    ajexdi = _positive_finite(work["ajexdi"])
    work["tr_level"] = (prccd * trfd / ajexdi).where(
        prccd.notna() & trfd.notna() & ajexdi.notna()
    )
    work["price_level"] = (prccd / ajexdi).where(
        prccd.notna() & ajexdi.notna()
    )

    computed_dollar_volume = pd.Series(np.nan, index=work.index, dtype="float64")
    if "cshtrd" in work.columns:
        cshtrd = _finite_nonnegative(work["cshtrd"])
        computed_dollar_volume = (prccd * cshtrd).where(
            prccd.notna() & cshtrd.notna()
        )
    if "dollar_volume" in work.columns:
        supplied_dollar_volume = _finite_nonnegative(work["dollar_volume"])
        work["dollar_volume"] = supplied_dollar_volume.fillna(computed_dollar_volume)
    else:
        work["dollar_volume"] = computed_dollar_volume

    work["data_source"] = data_source
    return work[STANDARDIZED_COLUMNS].sort_values(SOURCE_KEY).reset_index(drop=True)


def _read_source(
    path: Path,
    data_source: str,
    gvkey_filter: list[str] | None,
) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    available = set(pq.ParquetFile(path).schema_arrow.names)
    required = {"gvkey", "iid", "date", "prccd", "trfd", "ajexdi"}
    missing = sorted(required.difference(available))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")
    columns = sorted(required.union({"cshtrd", "dollar_volume"}.intersection(available)))
    filters = None
    if gvkey_filter is not None:
        filters = [("gvkey", "in", [str(value) for value in gvkey_filter])]
    frame = pd.read_parquet(path, columns=columns, filters=filters)
    print(f"[{data_source}] rows loaded: {len(frame):,}")
    return _prepare_source_frame(frame, data_source)


def _sql_literal(value: str | Path) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _source_projection_sql(path: Path, data_source: str, priority: int) -> str:
    """Return a lazy DuckDB projection equivalent to ``_prepare_source_frame``."""
    if not path.is_file():
        raise FileNotFoundError(path)
    available = set(pq.ParquetFile(path).schema_arrow.names)
    required = {"gvkey", "iid", "date", "prccd", "trfd", "ajexdi"}
    missing = sorted(required.difference(available))
    if missing:
        raise ValueError(f"{path} is missing required columns: {missing}")

    prccd = (
        "CASE WHEN isfinite(try_cast(prccd AS DOUBLE)) "
        "AND try_cast(prccd AS DOUBLE) > 0 THEN try_cast(prccd AS DOUBLE) END"
    )
    trfd = (
        "CASE WHEN isfinite(try_cast(trfd AS DOUBLE)) "
        "AND try_cast(trfd AS DOUBLE) > 0 THEN try_cast(trfd AS DOUBLE) END"
    )
    ajexdi = (
        "CASE WHEN isfinite(try_cast(ajexdi AS DOUBLE)) "
        "AND try_cast(ajexdi AS DOUBLE) > 0 THEN try_cast(ajexdi AS DOUBLE) END"
    )
    if "cshtrd" in available:
        cshtrd = (
            "CASE WHEN isfinite(try_cast(cshtrd AS DOUBLE)) "
            "AND try_cast(cshtrd AS DOUBLE) >= 0 THEN try_cast(cshtrd AS DOUBLE) END"
        )
        computed_volume = f"({prccd}) * ({cshtrd})"
    else:
        computed_volume = "CAST(NULL AS DOUBLE)"
    if "dollar_volume" in available:
        supplied_volume = (
            "CASE WHEN isfinite(try_cast(dollar_volume AS DOUBLE)) "
            "AND try_cast(dollar_volume AS DOUBLE) >= 0 "
            "THEN try_cast(dollar_volume AS DOUBLE) END"
        )
        dollar_volume = f"coalesce(({supplied_volume}), ({computed_volume}))"
    else:
        dollar_volume = computed_volume

    return f"""
        SELECT
            trim(cast(gvkey AS VARCHAR)) AS gvkey,
            trim(cast(iid AS VARCHAR)) AS iid,
            try_cast(date AS DATE) AS date,
            ({prccd}) * ({trfd}) / ({ajexdi}) AS tr_level,
            ({prccd}) / ({ajexdi}) AS price_level,
            {dollar_volume} AS dollar_volume,
            {_sql_literal(data_source)} AS data_source,
            {priority}::INTEGER AS _source_priority
        FROM read_parquet({_sql_literal(path.resolve())})
    """


def _validate_raw_source_sql(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    data_source: str,
) -> None:
    """Fail closed on malformed or normalization-colliding source keys."""
    raw_path = _sql_literal(path.resolve())
    invalid = connection.execute(
        f"""
        SELECT count(*)
        FROM read_parquet({raw_path})
        WHERE gvkey IS NULL OR trim(cast(gvkey AS VARCHAR)) = ''
           OR iid IS NULL OR trim(cast(iid AS VARCHAR)) = ''
           OR try_cast(date AS DATE) IS NULL
        """
    ).fetchone()[0]
    if invalid:
        raise ValueError(f"{data_source} contains {int(invalid)} malformed source key(s)")
    duplicate = connection.execute(
        f"""
        SELECT trim(cast(gvkey AS VARCHAR)), trim(cast(iid AS VARCHAR)),
               try_cast(date AS DATE), count(*)
        FROM read_parquet({raw_path})
        GROUP BY 1, 2, 3
        HAVING count(*) > 1
        LIMIT 1
        """
    ).fetchone()
    if duplicate is not None:
        raise ValueError(
            f"{data_source} contains duplicate (gvkey, iid, date) source keys; "
            f"example={duplicate[:3]}"
        )


def _full_output_sql(secd_path: Path, daily_path: Path) -> str:
    secd = _source_projection_sql(secd_path, "comp_secd_2015_2019", 0)
    daily = _source_projection_sql(daily_path, "prices_daily_compustat", 1)
    return f"""
        WITH unioned AS (
            {secd}
            UNION ALL
            {daily}
        ), ranked AS (
            SELECT *, row_number() OVER (
                PARTITION BY gvkey, iid, date
                ORDER BY _source_priority DESC
            ) AS _source_rank
            FROM unioned
        ), merged AS (
            SELECT gvkey, iid, date, tr_level, price_level, dollar_volume, data_source
            FROM ranked
            WHERE _source_rank = 1
        ), lagged AS (
            SELECT *,
                lag(tr_level) OVER security_window AS prior_tr_level,
                lag(price_level) OVER security_window AS prior_price_level,
                lag(date) OVER security_window AS prior_date
            FROM merged
            WINDOW security_window AS (
                PARTITION BY gvkey, iid ORDER BY date
            )
        ), calculated AS (
            SELECT *,
                CASE
                    WHEN tr_level IS NOT NULL AND prior_tr_level IS NOT NULL
                        THEN tr_level / prior_tr_level - 1.0
                    WHEN price_level IS NOT NULL AND prior_price_level IS NOT NULL
                        THEN price_level / prior_price_level - 1.0
                END AS raw_return,
                CASE
                    WHEN tr_level IS NOT NULL AND prior_tr_level IS NOT NULL
                        THEN 'total_return'
                    WHEN price_level IS NOT NULL AND prior_price_level IS NOT NULL
                        THEN 'price_return_fallback'
                    ELSE 'unavailable'
                END AS return_type,
                coalesce(date_diff('day', prior_date, date) > {MAX_GAP_DAYS}, false)
                    AS gap_guardrail
            FROM lagged
        ), guarded AS (
            SELECT *, coalesce(abs(raw_return) > {MAX_RET_ABS}, false)
                AS extreme_guardrail
            FROM calculated
        )
        SELECT
            gvkey,
            iid,
            gvkey || '-' || iid AS security_id,
            strftime(date, '%Y-%m-%d') AS date,
            CASE WHEN gap_guardrail OR extreme_guardrail THEN NULL ELSE raw_return END
                AS total_return,
            return_type,
            dollar_volume,
            data_source,
            tr_level,
            price_level,
            CASE
                WHEN gap_guardrail AND extreme_guardrail
                    THEN 'date_gap_gt_5|abs_return_gt_5'
                WHEN gap_guardrail THEN 'date_gap_gt_5'
                WHEN extreme_guardrail THEN 'abs_return_gt_5'
                ELSE ''
            END AS guardrail_reason
        FROM guarded
        ORDER BY gvkey, iid, date
    """


def process_secd(path: Path, gvkey_filter: list[str] | None = None) -> pd.DataFrame:
    return _read_source(path, "comp_secd_2015_2019", gvkey_filter)


def process_daily(path: Path, gvkey_filter: list[str] | None = None) -> pd.DataFrame:
    return _read_source(path, "prices_daily_compustat", gvkey_filter)


def _guardrail_reasons(gap_mask: pd.Series, extreme_mask: pd.Series) -> pd.Series:
    reasons = pd.Series("", index=gap_mask.index, dtype="string")
    reasons.loc[gap_mask] = "date_gap_gt_5"
    reasons.loc[extreme_mask] = "abs_return_gt_5"
    both = gap_mask & extreme_mask
    reasons.loc[both] = "date_gap_gt_5|abs_return_gt_5"
    return reasons


def merge_and_validate(secd: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Merge exact source keys, then compute security-level returns chronologically."""
    for frame, label in ((secd, "comp_secd_2015_2019"), (daily, "prices_daily_compustat")):
        _require_columns(frame, set(STANDARDIZED_COLUMNS), label)
        _assert_unique_source_keys(frame, label)

    if secd.empty and daily.empty:
        raise ValueError("D2A return output is empty")

    ranked_frames: list[pd.DataFrame] = []
    if not secd.empty:
        secd_ranked = secd.copy()
        secd_ranked["_source_priority"] = 0
        ranked_frames.append(secd_ranked)
    if not daily.empty:
        daily_ranked = daily.copy()
        daily_ranked["_source_priority"] = 1
        ranked_frames.append(daily_ranked)
    merged = pd.concat(ranked_frames, ignore_index=True)
    merged = merged.sort_values(SOURCE_KEY + ["_source_priority"], kind="stable")

    # The daily source wins only on an exact (gvkey, iid, date) overlap.
    merged = merged.drop_duplicates(SOURCE_KEY, keep="last")
    merged = merged.drop(columns="_source_priority").sort_values(SOURCE_KEY).reset_index(drop=True)

    grouped = merged.groupby(SECURITY_KEY, sort=False, observed=True)
    prior_tr_level = grouped["tr_level"].shift(1)
    prior_price_level = grouped["price_level"].shift(1)

    tr_available = merged["tr_level"].notna() & prior_tr_level.notna()
    price_available = merged["price_level"].notna() & prior_price_level.notna()
    tr_return = merged["tr_level"] / prior_tr_level - 1.0
    price_return = merged["price_level"] / prior_price_level - 1.0

    merged["total_return"] = np.select(
        [tr_available, ~tr_available & price_available],
        [tr_return, price_return],
        default=np.nan,
    )
    merged["return_type"] = np.select(
        [tr_available, ~tr_available & price_available],
        ["total_return", "price_return_fallback"],
        default="unavailable",
    )

    dates = pd.to_datetime(merged["date"], errors="raise")
    prior_date = dates.groupby(
        [merged["gvkey"], merged["iid"]], sort=False, observed=True
    ).shift(1)
    gap_mask = (dates - prior_date).dt.days.gt(MAX_GAP_DAYS).fillna(False)
    extreme_mask = merged["total_return"].abs().gt(MAX_RET_ABS).fillna(False)
    merged["guardrail_reason"] = _guardrail_reasons(gap_mask, extreme_mask)
    merged.loc[gap_mask | extreme_mask, "total_return"] = np.nan

    merged["security_id"] = merged["gvkey"] + "-" + merged["iid"]
    output = merged[OUTPUT_COLUMNS].copy()
    _validate_output(output)
    return output


def build_security_returns(secd: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Named D2A entry point retained separately from file loading/publication."""
    return merge_and_validate(secd, daily)


def _validate_output(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValueError("D2A return output is empty")
    _require_columns(df, set(OUTPUT_COLUMNS), "D2A return output")
    expected_security_id = df["gvkey"].astype("string") + "-" + df["iid"].astype("string")
    if not df["security_id"].astype("string").equals(expected_security_id):
        raise ValueError("security_id identity does not match '<gvkey>-<iid>'")
    identity_count = len(df[["gvkey", "iid"]].drop_duplicates())
    if int(df["security_id"].nunique()) != identity_count:
        raise ValueError("security_id is not one-to-one with (gvkey, iid)")
    duplicate = df.duplicated(["security_id", "date"], keep=False)
    if duplicate.any():
        examples = df.loc[duplicate, ["security_id", "date"]].head(3).to_dict("records")
        raise ValueError(f"duplicate (security_id, date) output keys; examples={examples}")

    ordered = df.sort_values(["gvkey", "iid", "date"]).copy()
    grouped = ordered.groupby(SECURITY_KEY, sort=False, observed=True)
    prior_tr = grouped["tr_level"].shift(1)
    prior_price = grouped["price_level"].shift(1)
    unguarded = ordered["guardrail_reason"].eq("") & ordered["total_return"].notna()
    total_mask = unguarded & ordered["return_type"].eq("total_return")
    fallback_mask = unguarded & ordered["return_type"].eq("price_return_fallback")

    if total_mask.any():
        expected = ordered.loc[total_mask, "tr_level"] / prior_tr.loc[total_mask] - 1.0
        if not np.allclose(
            ordered.loc[total_mask, "total_return"], expected, rtol=1e-12, atol=1e-12
        ):
            raise ValueError("total_return formula identity validation failed")
    if fallback_mask.any():
        expected = (
            ordered.loc[fallback_mask, "price_level"] / prior_price.loc[fallback_mask] - 1.0
        )
        if not np.allclose(
            ordered.loc[fallback_mask, "total_return"], expected, rtol=1e-12, atol=1e-12
        ):
            raise ValueError("price-return fallback identity validation failed")


def _return_quality_metrics(df: pd.DataFrame) -> dict[str, Any]:
    ordered = df.sort_values(["gvkey", "iid", "date"])
    prior_tr = ordered.groupby(SECURITY_KEY, sort=False, observed=True)["tr_level"].shift(1)
    changed_valid = (
        ordered["return_type"].eq("total_return")
        & ordered["guardrail_reason"].eq("")
        & ordered["total_return"].notna()
        & ordered["tr_level"].notna()
        & prior_tr.notna()
        & ordered["tr_level"].ne(prior_tr)
    )
    changed_count = int(changed_valid.sum())
    nonzero_count = int(
        (ordered.loc[changed_valid, "total_return"].abs() > np.finfo(float).eps).sum()
    )
    nonzero_pct = None if changed_count == 0 else nonzero_count / changed_count
    total_mask = (
        ordered["return_type"].eq("total_return")
        & ordered["guardrail_reason"].eq("")
        & ordered["total_return"].notna()
        & prior_tr.notna()
    )
    prior_price = ordered.groupby(SECURITY_KEY, sort=False, observed=True)[
        "price_level"
    ].shift(1)
    fallback_mask = (
        ordered["return_type"].eq("price_return_fallback")
        & ordered["guardrail_reason"].eq("")
        & ordered["total_return"].notna()
        & prior_price.notna()
    )
    total_errors = (
        ordered.loc[total_mask, "total_return"]
        - (ordered.loc[total_mask, "tr_level"] / prior_tr.loc[total_mask] - 1.0)
    ).abs()
    fallback_errors = (
        ordered.loc[fallback_mask, "total_return"]
        - (
            ordered.loc[fallback_mask, "price_level"]
            / prior_price.loc[fallback_mask]
            - 1.0
        )
    ).abs()

    def _max_error(errors: pd.Series) -> float:
        return 0.0 if errors.empty else float(errors.max())

    total_max_error = _max_error(total_errors)
    fallback_max_error = _max_error(fallback_errors)
    return {
        "non_null_return_count": int(df["total_return"].notna().sum()),
        "null_return_pct": float(df["total_return"].isna().mean()),
        "changed_valid_tr_level_count": changed_count,
        "changed_valid_tr_level_nonzero_return_count": nonzero_count,
        "changed_valid_tr_level_nonzero_return_pct": nonzero_pct,
        "guardrail_null_count": int(df["guardrail_reason"].ne("").sum()),
        "total_return_formula_max_abs_error": total_max_error,
        "fallback_formula_max_abs_error": fallback_max_error,
        "formula_identity_max_abs_error": max(total_max_error, fallback_max_error),
    }


def _manifest_for_summary(
    summary: dict[str, Any],
    logical_out_path: Path,
    versioned_parquet_path: Path,
    label: str,
    sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "2.0",
        "builder": "scripts/pead_d2_return_contract.py",
        "label": label,
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "parquet_file": versioned_parquet_path.name,
        "logical_parquet_name": logical_out_path.name,
        "row_count": int(summary["row_count"]),
        "gvkey_count": int(summary["gvkey_count"]),
        "security_count": int(summary["security_count"]),
        "iid_count": int(summary["iid_count"]),
        "date_min": str(summary["date_min"]),
        "date_max": str(summary["date_max"]),
        "columns": list(summary["columns"]),
        "unique_security_id_date": True,
        "sha256": sha256,
        "return_type_dist": summary["return_type_dist"],
        "return_quality": summary["return_quality"],
        "methodology": {
            "total_return_level": "TR_level = prccd * trfd / ajexdi",
            "canonical_total_return": "total_return = TR_level_t / TR_level_{t-1} - 1",
            "fallback_price_level": "price_level = prccd / ajexdi",
            "fallback_return": "price_return = price_level_t / price_level_{t-1} - 1",
            "lag_partition": "(gvkey, iid)",
            "source_overlap": (
                "prices_daily_compustat is preferred only on exact (gvkey, iid, date) overlap"
            ),
            "guardrails": {
                "date_gap_max_calendar_days": MAX_GAP_DAYS,
                "absolute_return_max": MAX_RET_ABS,
            },
            "supersedes": (
                "The prior trfd_t / trfd_{t-1} - 1 formula is invalid and is superseded."
            ),
        },
        "data_sources": ["comp_secd_2015_2019", "prices_daily_compustat"],
        "warnings": [
            "price_return_fallback excludes dividends when either total-return level is unavailable",
            "event-level primary-IID selection and +60 market-session extraction belong to D2B",
            "dollar_volume is daily dollar volume and is not ADV",
        ],
        "publication": {
            "protocol": "immutable versioned Parquet plus atomic manifest commit pointer",
            "commit_point": logical_out_path.with_suffix(
                ".parquet.manifest.json"
            ).name,
            "reader_rule": "read the manifest first, then read its parquet_file",
        },
    }


def _manifest_for(
    df: pd.DataFrame,
    logical_out_path: Path,
    versioned_parquet_path: Path,
    label: str,
    sha256: str,
) -> dict[str, Any]:
    summary = {
        "row_count": len(df),
        "gvkey_count": df["gvkey"].nunique(),
        "security_count": df["security_id"].nunique(),
        "iid_count": df["iid"].nunique(),
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "columns": list(df.columns),
        "return_type_dist": {
            str(key): int(value)
            for key, value in df["return_type"].value_counts().items()
        },
        "return_quality": _return_quality_metrics(df),
    }
    return _manifest_for_summary(
        summary, logical_out_path, versioned_parquet_path, label, sha256
    )


def _safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def _publication_lock(lock_path: Path):
    """Hold a process-scoped non-blocking file lock; OS releases it on crashes."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+b")
    handle.seek(0, os.SEEK_END)
    if handle.tell() == 0:
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    acquired = False
    try:
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        acquired = True
    except OSError as exc:
        handle.close()
        raise RuntimeError(f"D2A publication lock is already held: {lock_path}") from exc
    try:
        yield
    finally:
        try:
            if acquired:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()
            if acquired:
                _safe_unlink(lock_path)


def _versioned_parquet_path(logical_out_path: Path, sha256: str) -> Path:
    return logical_out_path.with_name(f"{logical_out_path.stem}.{sha256}.parquet")


def _manifest_points_to(
    manifest_path: Path,
    versioned_path: Path | None,
    output_sha256: str | None,
) -> bool:
    if versioned_path is None or output_sha256 is None or not manifest_path.is_file():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return (
            manifest["parquet_file"] == versioned_path.name
            and manifest["sha256"] == output_sha256
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def _bounded_connection(temp_directory: Path) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute(f"SET memory_limit = {_sql_literal(FULL_BUILD_MEMORY_LIMIT)}")
    connection.execute("SET threads = 1")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(temp_directory.resolve())}"
    )
    return connection


def _validation_connection(temp_directory: Path) -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect()
    connection.execute("SET memory_limit = '8GB'")
    connection.execute("SET threads = 1")
    connection.execute("SET preserve_insertion_order = false")
    connection.execute(
        f"SET temp_directory = {_sql_literal(temp_directory.resolve())}"
    )
    return connection


def _prebuilt_output_summary(
    connection: duckdb.DuckDBPyConnection,
    parquet_path: Path,
) -> dict[str, Any]:
    """Validate and summarize a prebuilt D2A Parquet without loading it as a frame."""
    parquet = pq.ParquetFile(parquet_path)
    columns = parquet.schema_arrow.names
    if columns != OUTPUT_COLUMNS:
        raise ValueError(f"D2A output schema drift: {columns}")
    source = f"read_parquet({_sql_literal(parquet_path.resolve())})"
    temp_dir = parquet_path.parent

    # Run queries on fresh connections to avoid buffer-pool contamination from COPY
    # and keep memory consumption bounded.
    
    # 1. Duplicate check
    conn = _validation_connection(temp_dir)
    try:
        duplicate = conn.execute(
            f"""
            SELECT security_id, date
            FROM {source}
            GROUP BY security_id, date
            HAVING count(*) > 1
            LIMIT 1
            """
        ).fetchone()
        if duplicate is not None:
            raise ValueError(f"duplicate (security_id, date) output keys; example={duplicate}")
    finally:
        conn.close()

    # 2. Identity collision check
    conn = _validation_connection(temp_dir)
    try:
        identity_collision = conn.execute(
            f"""
            SELECT security_id
            FROM (
                SELECT DISTINCT gvkey, iid, security_id
                FROM {source}
            )
            GROUP BY security_id
            HAVING count(*) > 1
            LIMIT 1
            """
        ).fetchone()
        if identity_collision is not None:
            raise ValueError("security_id is not one-to-one with (gvkey, iid)")
        
        identity_mismatch = conn.execute(
            f"SELECT count(*) FROM {source} WHERE security_id != gvkey || '-' || iid"
        ).fetchone()[0]
        if identity_mismatch:
            raise ValueError("security_id identity does not match '<gvkey>-<iid>'")
    finally:
        conn.close()

    # 3. Metrics calculation (Split into Basic Counts and Formula Verification on a sample of 500 GVKEYs)
    conn = _validation_connection(temp_dir)
    try:
        row_basic = conn.execute(
            f"""
            SELECT
                count(*) AS row_count,
                count(DISTINCT gvkey) AS gvkey_count,
                count(DISTINCT security_id) AS security_count,
                count(DISTINCT iid) AS iid_count,
                min(date) AS date_min,
                max(date) AS date_max,
                count(total_return) AS non_null_return_count,
                count(*) FILTER (WHERE guardrail_reason != '') AS guardrail_count
            FROM {source}
            """
        ).fetchone()

        return_type_dist = {
            str(key): int(value)
            for key, value in conn.execute(
                f"SELECT return_type, count(*) FROM {source} GROUP BY return_type"
            ).fetchall()
        }
    finally:
        conn.close()

    row_count = int(row_basic[0])
    if row_count == 0:
        raise ValueError("D2A return output is empty")

    conn = _validation_connection(temp_dir)
    try:
        row_formula = conn.execute(
            f"""
            WITH sampled AS (
                SELECT *
                FROM {source}
                WHERE gvkey IN (
                    SELECT DISTINCT gvkey FROM {source} LIMIT 500
                )
            ), ordered AS (
                SELECT *,
                    lag(tr_level) OVER (
                        PARTITION BY gvkey, iid ORDER BY date
                    ) AS prior_tr,
                    lag(price_level) OVER (
                        PARTITION BY gvkey, iid ORDER BY date
                    ) AS prior_price
                FROM sampled
            ), metrics AS (
                SELECT *,
                    return_type = 'total_return'
                        AND guardrail_reason = ''
                        AND total_return IS NOT NULL
                        AND tr_level IS NOT NULL
                        AND prior_tr IS NOT NULL AS valid_total,
                    return_type = 'price_return_fallback'
                        AND guardrail_reason = ''
                        AND total_return IS NOT NULL
                        AND price_level IS NOT NULL
                        AND prior_price IS NOT NULL AS valid_fallback
                FROM ordered
            )
            SELECT
                count(*) FILTER (
                    WHERE valid_total AND tr_level != prior_tr
                ) AS changed_count,
                count(*) FILTER (
                    WHERE valid_total AND tr_level != prior_tr
                      AND abs(total_return) > {np.finfo(float).eps}
                ) AS changed_nonzero_count,
                coalesce(max(abs(total_return - (tr_level / prior_tr - 1.0)))
                    FILTER (WHERE valid_total), 0.0) AS total_max_error,
                coalesce(max(abs(total_return - (price_level / prior_price - 1.0)))
                    FILTER (WHERE valid_fallback), 0.0) AS fallback_max_error
            FROM metrics
            """
        ).fetchone()
    finally:
        conn.close()

    changed_count = int(row_formula[0])
    changed_nonzero_count = int(row_formula[1])
    nonzero_pct = (
        None if changed_count == 0 else changed_nonzero_count / changed_count
    )
    if changed_count <= 0 or nonzero_pct is None or nonzero_pct <= 0.99:
        raise ValueError(
            "changed valid total-return levels must produce nonzero returns above 99%"
        )

    total_max_error = float(row_formula[2])
    fallback_max_error = float(row_formula[3])

    return {
        "row_count": row_count,
        "gvkey_count": int(row_basic[1]),
        "security_count": int(row_basic[2]),
        "iid_count": int(row_basic[3]),
        "date_min": str(row_basic[4]),
        "date_max": str(row_basic[5]),
        "columns": columns,
        "return_type_dist": return_type_dist,
        "return_quality": {
            "non_null_return_count": int(row_basic[6]),
            "null_return_pct": 1.0 - int(row_basic[6]) / row_count,
            "changed_valid_tr_level_count": changed_count,
            "changed_valid_tr_level_nonzero_return_count": changed_nonzero_count,
            "changed_valid_tr_level_nonzero_return_pct": nonzero_pct,
            "guardrail_null_count": int(row_basic[7]),
            "total_return_formula_max_abs_error": total_max_error,
            "fallback_formula_max_abs_error": fallback_max_error,
            "formula_identity_max_abs_error": max(
                total_max_error, fallback_max_error
            ),
        },
    }


def _commit_prebuilt_contract(
    parquet_tmp: Path,
    out_path: Path,
    label: str,
    summary: dict[str, Any],
) -> Path:
    """Commit a bounded prebuilt Parquet using the normal atomic pointer protocol."""
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    token = uuid.uuid4().hex
    manifest_tmp = manifest_path.with_name(f".{manifest_path.name}.{token}.tmp")
    versioned_path: Path | None = None
    output_sha256: str | None = None
    created_version = False
    manifest_committed = False
    try:
        output_sha256 = _sha256_file(parquet_tmp)
        versioned_path = _versioned_parquet_path(out_path, output_sha256)
        manifest = _manifest_for_summary(
            summary, out_path, versioned_path, label, output_sha256
        )
        manifest_tmp.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if versioned_path.exists():
            if _sha256_file(versioned_path) != output_sha256:
                raise ValueError("versioned Parquet filename/hash collision")
            _safe_unlink(parquet_tmp)
        else:
            os.replace(parquet_tmp, versioned_path)
            created_version = True
        os.replace(manifest_tmp, manifest_path)
        manifest_committed = True
        committed = json.loads(manifest_path.read_text(encoding="utf-8"))
        committed_path = manifest_path.parent / committed["parquet_file"]
        if _sha256_file(committed_path) != committed["sha256"]:
            raise ValueError("committed Parquet hash does not match manifest")
        if out_path.exists() and out_path != committed_path:
            _safe_unlink(out_path)
        return manifest_path
    except BaseException:
        commit_completed = manifest_committed or _manifest_points_to(
            manifest_path, versioned_path, output_sha256
        )
        if created_version and not commit_completed and versioned_path is not None:
            _safe_unlink(versioned_path)
        raise
    finally:
        _safe_unlink(parquet_tmp)
        _safe_unlink(manifest_tmp)


def build_full_contract(
    secd_path: Path | None = None,
    daily_path: Path | None = None,
    out_path: Path | None = None,
    label: str = "full_universe_security_level",
) -> Path:
    """Build full-universe D2A via bounded DuckDB operators and disk spill."""
    secd_path = SECD_PATH if secd_path is None else Path(secd_path)
    daily_path = DAILY_PATH if daily_path is None else Path(daily_path)
    out_path = OUT_FULL_PATH if out_path is None else Path(out_path)
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    # Schema checks happen before acquiring a publication lock or creating output.
    output_sql = _full_output_sql(secd_path, daily_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = out_path.with_suffix(".parquet.lock")
    with _publication_lock(lock_path):
        token = uuid.uuid4().hex
        parquet_tmp = out_path.with_name(f".{out_path.name}.{token}.tmp")
        connection = _bounded_connection(out_path.parent)
        try:
            _validate_raw_source_sql(
                connection, secd_path, "comp_secd_2015_2019"
            )
            _validate_raw_source_sql(
                connection, daily_path, "prices_daily_compustat"
            )
            connection.execute(
                f"""
                COPY ({output_sql}) TO {_sql_literal(parquet_tmp.resolve())}
                (FORMAT PARQUET, COMPRESSION ZSTD,
                 ROW_GROUP_SIZE {FULL_BUILD_ROW_GROUP_SIZE})
                """
            )
            connection.close()
            summary = _prebuilt_output_summary(None, parquet_tmp)
            return _commit_prebuilt_contract(parquet_tmp, out_path, label, summary)
        finally:
            connection.close()
            _safe_unlink(parquet_tmp)


def publish_contract(df: pd.DataFrame, out_path: Path, label: str) -> Path:
    """Publish immutable Parquet, then atomically commit its manifest pointer."""
    out_path = Path(out_path)
    if not out_path.name or out_path.suffix.lower() != ".parquet":
        raise ValueError("output path must be a non-empty .parquet path")
    _validate_output(df)
    quality = _return_quality_metrics(df)
    changed_count = quality["changed_valid_tr_level_count"]
    nonzero_pct = quality["changed_valid_tr_level_nonzero_return_pct"]
    if changed_count <= 0 or nonzero_pct is None or nonzero_pct <= 0.99:
        raise ValueError(
            "changed valid total-return levels must produce nonzero returns above 99%"
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = out_path.with_suffix(".parquet.manifest.json")
    lock_path = out_path.with_suffix(".parquet.lock")
    with _publication_lock(lock_path):
        token = uuid.uuid4().hex
        parquet_tmp = out_path.with_name(f".{out_path.name}.{token}.tmp")
        manifest_tmp = manifest_path.with_name(f".{manifest_path.name}.{token}.tmp")
        versioned_path: Path | None = None
        output_sha256: str | None = None
        created_version = False
        manifest_committed = False
        try:
            df.to_parquet(parquet_tmp, index=False)
            output_sha256 = _sha256_file(parquet_tmp)
            versioned_path = _versioned_parquet_path(out_path, output_sha256)
            manifest = _manifest_for(
                df, out_path, versioned_path, label, output_sha256
            )
            manifest_tmp.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

            if versioned_path.exists():
                if _sha256_file(versioned_path) != output_sha256:
                    raise ValueError("versioned Parquet filename/hash collision")
                _safe_unlink(parquet_tmp)
            else:
                os.replace(parquet_tmp, versioned_path)
                created_version = True

            # The manifest is the sole commit point. It always references an already
            # durable immutable Parquet, so interruption cannot expose a mixed pair.
            os.replace(manifest_tmp, manifest_path)
            manifest_committed = True

            committed = json.loads(manifest_path.read_text(encoding="utf-8"))
            committed_path = manifest_path.parent / committed["parquet_file"]
            if _sha256_file(committed_path) != committed["sha256"]:
                raise ValueError("committed Parquet hash does not match manifest")

            # Remove a pre-pointer fixed-name alias only after the manifest commit.
            # A crash before this cleanup leaves a harmless non-canonical extra file.
            if out_path.exists() and out_path != committed_path:
                _safe_unlink(out_path)
            return manifest_path
        except BaseException:
            commit_completed = manifest_committed or _manifest_points_to(
                manifest_path, versioned_path, output_sha256
            )
            if created_version and not commit_completed and versioned_path is not None:
                _safe_unlink(versioned_path)
            raise
        finally:
            _safe_unlink(parquet_tmp)
            _safe_unlink(manifest_tmp)


def write_parquet(df: pd.DataFrame, out_path: Path, label: str) -> None:
    manifest_path = publish_contract(df, out_path, label)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"[write] {manifest_path.parent / manifest['parquet_file']}")
    print(f"[write] {manifest_path}")


def schema_check() -> None:
    print(
        """
[schema] D2A security-level return contract
  key:             gvkey, iid, security_id='<gvkey>-<iid>', date
  total-return:    TR_level = prccd * trfd / ajexdi
                   total_return = TR_level_t / TR_level_{t-1} - 1
  fallback:        price_level = prccd / ajexdi, lagged within (gvkey, iid)
  source overlap:  prices_daily_compustat wins exact (gvkey, iid, date) overlap
  guardrails:      date gap > 5 calendar days or abs(return) > 5 => NaN
  volume:          dollar_volume is daily dollar volume, not ADV
""".strip()
    )


def _sample_gvkeys(path: Path, sample_size: int) -> list[str]:
    values: set[str] = set()
    parquet = pq.ParquetFile(path)
    for batch in parquet.iter_batches(columns=["gvkey"], batch_size=1_000_000):
        values.update(str(value).strip() for value in batch.column(0).unique().to_pylist() if value)
    return sorted(values)[:sample_size]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PEAD D2A security-level return builder")
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build the memory-bounded full-universe D2A artifact",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Build the 500-GVKEY sample (default)",
    )
    parser.add_argument(
        "--event-window-only",
        action="store_true",
        help="Disabled: D2B owns fixed-IID +60 market-session extraction",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.event_window_only:
        parser.error(
            "--event-window-only is disabled in D2A; D2B must select one fixed IID "
            "per event and extract +60 market sessions"
        )
    if args.build and args.sample:
        parser.error("--build and --sample are mutually exclusive")

    if not SECD_PATH.is_file():
        sys.exit(f"[error] source not found: {SECD_PATH}")
    if not DAILY_PATH.is_file():
        sys.exit(f"[error] source not found: {DAILY_PATH}")

    schema_check()
    if args.build:
        manifest_path = build_full_contract()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"[write] {manifest_path.parent / manifest['parquet_file']}")
        print(f"[write] {manifest_path}")
        print(
            f"[done] rows={manifest['row_count']:,} "
            f"securities={manifest['security_count']:,} manifest={manifest_path}"
        )
        print("[next] D2B owns fixed event-level IID selection and +60 market sessions")
        return

    gvkey_filter = _sample_gvkeys(SECD_PATH, SAMPLE_N_GVKEYS)
    if len(gvkey_filter) != SAMPLE_N_GVKEYS:
        sys.exit(
            f"[error] D2A sample requires exactly {SAMPLE_N_GVKEYS} GVKEYs; "
            f"found {len(gvkey_filter)}"
        )
    out_path = OUT_SAMPLE_PATH
    label = f"sample_{SAMPLE_N_GVKEYS}_gvkeys_security_level"

    secd = process_secd(SECD_PATH, gvkey_filter)
    daily = process_daily(DAILY_PATH, gvkey_filter)
    output = build_security_returns(secd, daily)
    write_parquet(output, out_path, label)
    print(
        f"[done] rows={len(output):,} securities={output['security_id'].nunique():,} "
        f"manifest={out_path.with_suffix('.parquet.manifest.json')}"
    )
    print("[next] D2B owns fixed event-level IID selection and +60 market sessions")


if __name__ == "__main__":
    main()
