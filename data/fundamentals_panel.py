"""
Terminal Zero — Daily Fundamentals Panel Builder (Phase 17.3)

Builds a dense, PIT-safe daily fundamentals panel from sparse bitemporal rows.
Output artifact:
  data/processed/daily_fundamentals_panel.parquet
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from data import updater  # noqa: E402

PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
DEFAULT_FUNDAMENTALS_PATH = os.path.join(PROCESSED_DIR, "fundamentals.parquet")
FUNDAMENTALS_PATH = DEFAULT_FUNDAMENTALS_PATH
PRICES_PATH = os.path.join(PROCESSED_DIR, "prices.parquet")
PATCH_PATH = os.path.join(PROCESSED_DIR, "yahoo_patch.parquet")
PANEL_PATH = os.path.join(PROCESSED_DIR, "daily_fundamentals_panel.parquet")
MANIFEST_PATH = os.path.join(PROCESSED_DIR, "daily_fundamentals_panel.manifest.json")
PHASE16_OPTIMIZER_LOCK_PATH = os.path.join(PROCESSED_DIR, "phase16_optimizer.lock")
PHASE16_REQUIRED_ARTIFACTS = [
    os.path.join(PROCESSED_DIR, "phase16_optimizer_results.csv"),
    os.path.join(PROCESSED_DIR, "phase16_best_params.json"),
    os.path.join(PROCESSED_DIR, "phase16_oos_summary.csv"),
]

PANEL_COLUMNS = [
    "date",
    "permno",
    "ticker",
    "release_date",
    "published_at",
    "roic",
    "operating_margin_q",
    "operating_margin_delta_q",
    "gross_margin_q",
    "gm_accel_q",
    "capex_sales_q",
    "delta_capex_sales",
    "book_to_bill_proxy_q",
    "dso_q",
    "delta_dso_q",
    "revenue_inventory_q",
    "delta_revenue_inventory",
    "sales_growth_q",
    "sales_accel_q",
    "op_margin_accel_q",
    "bloat_q",
    "net_investment_q",
    "cogs_q",
    "receivables_q",
    "deferred_revenue_q",
    "delta_deferred_revenue_q",
    "asset_growth_yoy",
    "roe_q",
    "eps_q",
    "eps_ttm",
    "eps_growth_yoy",
    "revenue_growth_yoy",
    "ev_ebitda",
    "leverage_ratio",
    "rd_intensity",
    "oancf_ttm",
    "ebitda_ttm",
    "quality_pass",
]


def _phase17_writer_gate() -> tuple[bool, str | None]:
    if os.path.exists(PHASE16_OPTIMIZER_LOCK_PATH):
        return (
            False,
            f"Phase 17 writer blocked: optimizer lock present at {PHASE16_OPTIMIZER_LOCK_PATH}.",
        )
    missing = [p for p in PHASE16_REQUIRED_ARTIFACTS if not os.path.exists(p)]
    if missing:
        return (
            False,
            "Phase 17 writer blocked: required Phase 16 artifacts missing: "
            + ", ".join(missing),
        )
    return True, None


def _sql_escape_path(path: str) -> str:
    return path.replace("\\", "/").replace("'", "''")


def _file_fingerprint(path: str) -> dict[str, int | bool]:
    if not os.path.exists(path):
        return {"exists": False, "size": 0, "mtime_ns": 0}
    stat = os.stat(path)
    return {
        "exists": True,
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _atomic_write_json(payload: dict[str, Any], path: str):
    temp_path = f"{path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _read_manifest(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _calendar_sql(min_date: str | None, max_date: str | None) -> str:
    date_filters: list[str] = []
    if min_date:
        date_filters.append(f"date >= DATE '{min_date}'")
    if max_date:
        date_filters.append(f"date <= DATE '{max_date}'")
    where_clause = f"WHERE {' AND '.join(date_filters)}" if date_filters else ""

    if os.path.exists(PRICES_PATH):
        prices_sql = f"""
            SELECT DISTINCT CAST(date AS DATE) AS date
            FROM read_parquet('{_sql_escape_path(PRICES_PATH)}')
            {where_clause}
        """
        if os.path.exists(PATCH_PATH):
            patch_sql = f"""
                SELECT DISTINCT CAST(date AS DATE) AS date
                FROM read_parquet('{_sql_escape_path(PATCH_PATH)}')
                {where_clause}
            """
            return f"{prices_sql} UNION {patch_sql}"
        return prices_sql

    start_expr = (
        f"DATE '{min_date}'"
        if min_date
        else "(SELECT COALESCE(MIN(CAST(published_at AS DATE)), DATE '2000-01-01') FROM clean_fund)"
    )
    end_expr = (
        f"DATE '{max_date}'"
        if max_date
        else "(SELECT COALESCE(MAX(CAST(published_at AS DATE)), CURRENT_DATE) FROM clean_fund)"
    )
    return (
        f"SELECT * FROM generate_series({start_expr}, {end_expr}, INTERVAL 1 DAY) AS t(date) "
        "WHERE EXTRACT(DAYOFWEEK FROM date) BETWEEN 1 AND 5"
    )


def _collect_source_signature(min_date: str | None, max_date: str | None) -> dict[str, Any]:
    signature: dict[str, Any] = {
        "fundamentals_file": _file_fingerprint(FUNDAMENTALS_PATH),
        "prices_file": _file_fingerprint(PRICES_PATH),
        "patch_file": _file_fingerprint(PATCH_PATH),
        "min_date": min_date,
        "max_date": max_date,
    }
    if not os.path.exists(FUNDAMENTALS_PATH):
        signature["fundamentals_stats"] = {
            "row_count": 0,
            "permno_count": 0,
            "max_published_at": None,
            "max_ingested_at": None,
        }
        return signature

    con = duckdb.connect()
    try:
        row = con.execute(
            f"""
            SELECT
                COUNT(*) AS row_count,
                COUNT(DISTINCT CAST(permno AS BIGINT)) AS permno_count,
                MAX(CAST(COALESCE(
                    CAST(published_at AS DATE),
                    CAST(filing_date AS DATE),
                    CAST(fiscal_period_end AS DATE) + INTERVAL 90 DAY
                ) AS DATE)) AS max_published_at,
                MAX(CAST(ingested_at AS TIMESTAMP)) AS max_ingested_at
            FROM read_parquet('{_sql_escape_path(FUNDAMENTALS_PATH)}')
            """
        ).fetchone()
    finally:
        con.close()

    signature["fundamentals_stats"] = {
        "row_count": int(row[0]) if row and row[0] is not None else 0,
        "permno_count": int(row[1]) if row and row[1] is not None else 0,
        "max_published_at": str(row[2]) if row and row[2] is not None else None,
        "max_ingested_at": str(row[3]) if row and row[3] is not None else None,
    }
    return signature


def _build_panel_sql(stage_path: str, min_date: str | None, max_date: str | None) -> str:
    calendar_sql = _calendar_sql(min_date=min_date, max_date=max_date)
    min_filter = f"AND published_at >= DATE '{min_date}'" if min_date else ""
    max_filter = f"AND published_at <= DATE '{max_date}'" if max_date else ""
    return f"""
    COPY (
        WITH raw_fund AS (
            SELECT
                CAST(permno AS BIGINT) AS permno,
                UPPER(TRIM(CAST(ticker AS VARCHAR))) AS ticker,
                CAST(release_date AS DATE) AS release_date,
                CAST(COALESCE(
                    CAST(published_at AS DATE),
                    CAST(filing_date AS DATE),
                    CAST(fiscal_period_end AS DATE) + INTERVAL 90 DAY
                ) AS DATE) AS published_at,
                CAST(roic AS DOUBLE) AS roic,
                CAST(operating_margin_q AS DOUBLE) AS operating_margin_q,
                CAST(operating_margin_delta_q AS DOUBLE) AS operating_margin_delta_q,
                CAST(gross_margin_q AS DOUBLE) AS gross_margin_q,
                CAST(gm_accel_q AS DOUBLE) AS gm_accel_q,
                CAST(capex_sales_q AS DOUBLE) AS capex_sales_q,
                CAST(delta_capex_sales AS DOUBLE) AS delta_capex_sales,
                CAST(book_to_bill_proxy_q AS DOUBLE) AS book_to_bill_proxy_q,
                CAST(dso_q AS DOUBLE) AS dso_q,
                CAST(delta_dso_q AS DOUBLE) AS delta_dso_q,
                CAST(revenue_inventory_q AS DOUBLE) AS revenue_inventory_q,
                CAST(delta_revenue_inventory AS DOUBLE) AS delta_revenue_inventory,
                CAST(sales_growth_q AS DOUBLE) AS sales_growth_q,
                CAST(sales_accel_q AS DOUBLE) AS sales_accel_q,
                CAST(op_margin_accel_q AS DOUBLE) AS op_margin_accel_q,
                CAST(bloat_q AS DOUBLE) AS bloat_q,
                CAST(net_investment_q AS DOUBLE) AS net_investment_q,
                CAST(cogs_q AS DOUBLE) AS cogs_q,
                CAST(receivables_q AS DOUBLE) AS receivables_q,
                CAST(deferred_revenue_q AS DOUBLE) AS deferred_revenue_q,
                CAST(delta_deferred_revenue_q AS DOUBLE) AS delta_deferred_revenue_q,
                CAST(asset_growth_yoy AS DOUBLE) AS asset_growth_yoy,
                CAST(roe_q AS DOUBLE) AS roe_q,
                CAST(eps_q AS DOUBLE) AS eps_q,
                CAST(eps_ttm AS DOUBLE) AS eps_ttm,
                CAST(eps_growth_yoy AS DOUBLE) AS eps_growth_yoy,
                CAST(revenue_growth_yoy AS DOUBLE) AS revenue_growth_yoy,
                CAST(ev_ebitda AS DOUBLE) AS ev_ebitda,
                CAST(leverage_ratio AS DOUBLE) AS leverage_ratio,
                CAST(rd_intensity AS DOUBLE) AS rd_intensity,
                CAST(oancf_ttm AS DOUBLE) AS oancf_ttm,
                CAST(ebitda_ttm AS DOUBLE) AS ebitda_ttm,
                CAST(ingested_at AS TIMESTAMP) AS ingested_at
            FROM read_parquet('{_sql_escape_path(FUNDAMENTALS_PATH)}')
            WHERE permno IS NOT NULL
        ),
        clean_fund AS (
            SELECT *
            FROM raw_fund
            WHERE published_at IS NOT NULL
            {min_filter}
            {max_filter}
        ),
        dedup_fund AS (
            SELECT * EXCLUDE (rn)
            FROM (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY permno, published_at
                        ORDER BY release_date DESC NULLS LAST, ingested_at DESC NULLS LAST
                    ) AS rn
                FROM clean_fund
            ) s
            WHERE rn = 1
        ),
        fund_intervals AS (
            SELECT
                *,
                LEAD(published_at) OVER (
                    PARTITION BY permno
                    ORDER BY published_at
                ) AS next_published_at
            FROM dedup_fund
        ),
        calendar_dates AS (
            {calendar_sql}
        )
        SELECT
            CAST(c.date AS DATE) AS date,
            f.permno,
            f.ticker,
            f.release_date,
            f.published_at,
            f.roic,
            f.operating_margin_q,
            f.operating_margin_delta_q,
            f.gross_margin_q,
            f.gm_accel_q,
            f.capex_sales_q,
            f.delta_capex_sales,
            f.book_to_bill_proxy_q,
            f.dso_q,
            f.delta_dso_q,
            f.revenue_inventory_q,
            f.delta_revenue_inventory,
            f.sales_growth_q,
            f.sales_accel_q,
            f.op_margin_accel_q,
            f.bloat_q,
            f.net_investment_q,
            f.cogs_q,
            f.receivables_q,
            f.deferred_revenue_q,
            f.delta_deferred_revenue_q,
            f.asset_growth_yoy,
            f.roe_q,
            f.eps_q,
            f.eps_ttm,
            f.eps_growth_yoy,
            f.revenue_growth_yoy,
            f.ev_ebitda,
            f.leverage_ratio,
            f.rd_intensity,
            f.oancf_ttm,
            f.ebitda_ttm,
            CAST(
                CASE
                    WHEN f.roic > 0 AND f.revenue_growth_yoy > 0 THEN 1
                    ELSE 0
                END AS TINYINT
            ) AS quality_pass
        FROM fund_intervals f
        JOIN calendar_dates c
          ON c.date >= f.published_at
         AND (f.next_published_at IS NULL OR c.date < f.next_published_at)
        ORDER BY date, permno
    ) TO '{_sql_escape_path(stage_path)}' (FORMAT PARQUET);
    """


def build_daily_fundamentals_panel(
    output_path: str = PANEL_PATH,
    manifest_path: str = MANIFEST_PATH,
    force_rebuild: bool = False,
    min_date: str | None = None,
    max_date: str | None = None,
) -> dict[str, Any]:
    status: dict[str, Any] = {
        "success": False,
        "cache_hit": False,
        "rows_written": 0,
        "row_count": 0,
        "output_path": output_path,
        "manifest_path": manifest_path,
        "min_date": min_date,
        "max_date": max_date,
        "source_signature": None,
    }
    if not os.path.exists(FUNDAMENTALS_PATH):
        status["error"] = f"Missing fundamentals parquet: {FUNDAMENTALS_PATH}"
        return status

    use_update_lock = os.path.abspath(FUNDAMENTALS_PATH) == os.path.abspath(DEFAULT_FUNDAMENTALS_PATH)
    if use_update_lock:
        gate_ok, gate_msg = _phase17_writer_gate()
        if not gate_ok:
            status["error"] = gate_msg or "Phase 17 writer gate rejected panel build."
            return status

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    source_signature = _collect_source_signature(min_date=min_date, max_date=max_date)
    status["source_signature"] = source_signature
    prior_manifest = _read_manifest(manifest_path)
    if (
        not bool(force_rebuild)
        and os.path.exists(output_path)
        and prior_manifest is not None
        and prior_manifest.get("source_signature") == source_signature
    ):
        status["success"] = True
        status["cache_hit"] = True
        status["row_count"] = int(prior_manifest.get("row_count", 0))
        return status

    lock_acquired = False
    if use_update_lock:
        try:
            updater._acquire_update_lock()
            lock_acquired = True
        except TimeoutError:
            status["error"] = "Another update/build process is running. Try again after it completes."
            return status

    stage_path = f"{output_path}.{os.getpid()}.{int(time.time() * 1000)}.tmp"
    t0 = time.perf_counter()
    try:
        con = duckdb.connect()
        try:
            con.execute(_build_panel_sql(stage_path=stage_path, min_date=min_date, max_date=max_date))
        finally:
            con.close()
        if not os.path.exists(stage_path):
            raise RuntimeError("Daily panel build did not produce a stage parquet.")

        con = duckdb.connect()
        try:
            row = con.execute(
                f"""
                SELECT
                    COUNT(*) AS n_rows,
                    MIN(CAST(date AS DATE)) AS min_date,
                    MAX(CAST(date AS DATE)) AS max_date
                FROM read_parquet('{_sql_escape_path(stage_path)}')
                """
            ).fetchone()
        finally:
            con.close()

        row_count = int(row[0]) if row and row[0] is not None else 0
        min_panel_date = str(row[1]) if row and row[1] is not None else None
        max_panel_date = str(row[2]) if row and row[2] is not None else None

        os.replace(stage_path, output_path)
        build_seconds = time.perf_counter() - t0
        manifest = {
            "version": "v1",
            "built_at_utc": pd.Timestamp.utcnow().isoformat(),
            "build_seconds": float(build_seconds),
            "output_path": output_path,
            "row_count": int(row_count),
            "panel_min_date": min_panel_date,
            "panel_max_date": max_panel_date,
            "source_signature": source_signature,
            "columns": PANEL_COLUMNS,
        }
        _atomic_write_json(manifest, manifest_path)

        status["success"] = True
        status["rows_written"] = int(row_count)
        status["row_count"] = int(row_count)
        status["panel_min_date"] = min_panel_date
        status["panel_max_date"] = max_panel_date
        status["build_seconds"] = float(build_seconds)
        return status
    except Exception as exc:
        status["error"] = str(exc)
        status["success"] = False
        return status
    finally:
        if os.path.exists(stage_path):
            try:
                os.remove(stage_path)
            except OSError:
                pass
        if lock_acquired:
            updater._release_update_lock()


def load_daily_fundamentals_panel(
    panel_path: str = PANEL_PATH,
    start_date: str | None = None,
    end_date: str | None = None,
    permnos: list[int] | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    if not os.path.exists(panel_path):
        return pd.DataFrame(columns=PANEL_COLUMNS)

    select_cols = columns if columns else PANEL_COLUMNS
    escaped_cols = ", ".join([f'"{str(c)}"' for c in select_cols])
    where_parts: list[str] = []
    if start_date:
        where_parts.append(f"CAST(date AS DATE) >= DATE '{start_date}'")
    if end_date:
        where_parts.append(f"CAST(date AS DATE) <= DATE '{end_date}'")
    if permnos:
        permno_csv = ",".join(str(int(p)) for p in sorted(set(int(x) for x in permnos)))
        where_parts.append(f"CAST(permno AS BIGINT) IN ({permno_csv})")
    where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

    con = duckdb.connect()
    try:
        df = con.execute(
            f"""
            SELECT {escaped_cols}
            FROM read_parquet('{_sql_escape_path(panel_path)}')
            {where_clause}
            ORDER BY date, permno
            """
        ).df()
    finally:
        con.close()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def join_prices_with_daily_fundamentals(
    prices: pd.DataFrame,
    panel_path: str = PANEL_PATH,
    panel_columns: list[str] | None = None,
) -> pd.DataFrame:
    if prices is None or prices.empty:
        return prices.copy() if isinstance(prices, pd.DataFrame) else pd.DataFrame()
    if not os.path.exists(panel_path):
        return prices.copy()
    if "date" not in prices.columns:
        raise ValueError("prices frame must include a 'date' column for panel join.")

    cols = panel_columns or [
        "roic",
        "operating_margin_delta_q",
        "gm_accel_q",
        "book_to_bill_proxy_q",
        "delta_dso_q",
        "delta_capex_sales",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "eps_growth_yoy",
        "quality_pass",
    ]

    price_keys = prices.copy()
    price_keys["date"] = pd.to_datetime(price_keys["date"], errors="coerce")
    join_on_permno = "permno" in price_keys.columns
    join_on_ticker = "ticker" in price_keys.columns

    if not join_on_permno and not join_on_ticker:
        raise ValueError("prices frame must include either 'permno' or 'ticker' for panel join.")

    con = duckdb.connect()
    try:
        con.register("prices_df", price_keys)
        if join_on_permno:
            panel_cols_sql = ", ".join([f"f.{c}" for c in cols])
            joined = con.execute(
                f"""
                SELECT p.*, {panel_cols_sql}
                FROM prices_df p
                LEFT JOIN read_parquet('{_sql_escape_path(panel_path)}') f
                  ON CAST(p.date AS DATE) = CAST(f.date AS DATE)
                 AND CAST(p.permno AS BIGINT) = CAST(f.permno AS BIGINT)
                """
            ).df()
        else:
            panel_cols_sql = ", ".join([f"f.{c}" for c in cols])
            joined = con.execute(
                f"""
                SELECT p.*, {panel_cols_sql}
                FROM prices_df p
                LEFT JOIN read_parquet('{_sql_escape_path(panel_path)}') f
                  ON CAST(p.date AS DATE) = CAST(f.date AS DATE)
                 AND UPPER(TRIM(CAST(p.ticker AS VARCHAR))) = UPPER(TRIM(CAST(f.ticker AS VARCHAR)))
                """
            ).df()
    finally:
        con.close()

    joined["date"] = pd.to_datetime(joined["date"], errors="coerce")
    return joined


def main():
    parser = argparse.ArgumentParser(description="Build daily PIT fundamentals panel.")
    parser.add_argument("--force", action="store_true", help="Force rebuild even if signature unchanged.")
    parser.add_argument("--min-date", default=None, help="Optional lower calendar bound (YYYY-MM-DD).")
    parser.add_argument("--max-date", default=None, help="Optional upper calendar bound (YYYY-MM-DD).")
    args = parser.parse_args()

    status = build_daily_fundamentals_panel(
        force_rebuild=bool(args.force),
        min_date=args.min_date,
        max_date=args.max_date,
    )
    if status.get("cache_hit"):
        print(
            f"✅ Daily panel up to date (cache hit). rows={status.get('row_count', 0):,} "
            f"path={status['output_path']}"
        )
        return
    if not status.get("success"):
        print(f"✗ Failed: {status.get('error', 'unknown error')}")
        raise SystemExit(1)
    print(
        f"✅ Daily panel built. rows={status.get('rows_written', 0):,} "
        f"range={status.get('panel_min_date')}..{status.get('panel_max_date')} "
        f"path={status['output_path']}"
    )


if __name__ == "__main__":
    main()
