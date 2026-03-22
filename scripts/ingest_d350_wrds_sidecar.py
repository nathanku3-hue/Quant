from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
import psycopg2.extras

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core.security_policy import assert_egress_host_allowed  # noqa: E402
from core.security_policy import get_required_env  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LOG = logging.getLogger("ingest_d350_wrds_sidecar")

WRDS_HOST = "wrds-pgdata.wharton.upenn.edu"
WRDS_PORT = 9737
WRDS_DBNAME = "wrds"
WRDS_USER_ENV = "WRDS_USER"
WRDS_PASS_ENV = "WRDS_PASS"

DEFAULT_PERMNO = 86544
DEFAULT_START_DATE = "2023-01-01"
DEFAULT_END_DATE = "2023-11-29"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "sidecar_sp500_pro_2023_2024.parquet"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "docs" / "context" / "e2e_evidence" / "phase61_d350_wrds_pivot_20260319_summary.json"
)

SIDECAR_COLUMNS = [
    "date",
    "permno",
    "sp_rating",
    "sp_score",
    "price",
    "total_return",
    "cusip",
    "isin",
    "ticker",
    "company_name",
    "issue_date",
    "source_as_of_date",
    "source_file",
    "source_sheet",
]


def _atomic_write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _atomic_write_json(payload: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _connect() -> psycopg2.extensions.connection:
    assert_egress_host_allowed(WRDS_HOST, context="ingest_d350_wrds_sidecar")
    wrds_user = get_required_env(WRDS_USER_ENV)
    wrds_pass = get_required_env(WRDS_PASS_ENV)
    LOG.info("Connecting to WRDS at %s:%s", WRDS_HOST, WRDS_PORT)
    return psycopg2.connect(
        host=WRDS_HOST,
        port=WRDS_PORT,
        dbname=WRDS_DBNAME,
        user=wrds_user,
        password=wrds_pass,
        sslmode="require",
        connect_timeout=30,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def _query_wrds_rows(
    conn: psycopg2.extensions.connection,
    permno: int,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    sql = """
    WITH issue_dates AS (
        SELECT permno, MIN(namedt) AS issue_date
        FROM crsp.stocknames
        WHERE permno = %(permno)s
        GROUP BY permno
    )
    SELECT
        d.date,
        d.permno,
        ABS(d.prc) AS price,
        d.ret AS total_return,
        COALESCE(n.ncusip, n.cusip) AS cusip,
        n.ticker,
        n.comnam AS company_name,
        issue.issue_date,
        n.namedt
    FROM crsp.dsf AS d
    LEFT JOIN crsp.stocknames AS n
        ON d.permno = n.permno
       AND d.date BETWEEN n.namedt AND COALESCE(n.nameendt, DATE '9999-12-31')
    LEFT JOIN issue_dates AS issue
        ON d.permno = issue.permno
    WHERE d.permno = %(permno)s
      AND d.date BETWEEN %(start_date)s AND %(end_date)s
    ORDER BY d.date, n.namedt
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "permno": int(permno),
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        rows = cur.fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _normalize_sidecar(
    raw_rows: pd.DataFrame,
    *,
    source_as_of_date: pd.Timestamp,
    source_file: str,
    source_sheet: str,
) -> pd.DataFrame:
    if raw_rows.empty:
        raise RuntimeError("WRDS query returned no CRSP daily rows for the requested permno/date window.")

    sidecar = raw_rows.copy()
    sidecar["date"] = pd.to_datetime(sidecar["date"], errors="coerce")
    sidecar["permno"] = pd.to_numeric(sidecar["permno"], errors="coerce")
    sidecar["price"] = pd.to_numeric(sidecar["price"], errors="coerce")
    sidecar["total_return"] = pd.to_numeric(sidecar["total_return"], errors="coerce")
    sidecar["issue_date"] = pd.to_datetime(sidecar["issue_date"], errors="coerce")
    sidecar["cusip"] = sidecar["cusip"].astype("string").str.strip().replace({"": pd.NA})
    sidecar["ticker"] = sidecar["ticker"].astype("string").str.strip().replace({"": pd.NA})
    sidecar["company_name"] = sidecar["company_name"].astype("string").str.strip().replace({"": pd.NA})
    sidecar["source_as_of_date"] = pd.Timestamp(source_as_of_date).normalize()
    sidecar["source_file"] = source_file
    sidecar["source_sheet"] = source_sheet
    sidecar["sp_rating"] = pd.NA
    sidecar["sp_score"] = pd.NA
    sidecar["isin"] = pd.NA
    sidecar = sidecar.sort_values(["date", "namedt"]).drop_duplicates(subset=["date", "permno"], keep="last")
    sidecar = sidecar.drop(columns=["namedt"], errors="ignore")
    sidecar = sidecar.dropna(subset=["date", "permno"]).copy()
    sidecar["permno"] = sidecar["permno"].astype(int)
    sidecar = sidecar.loc[:, SIDECAR_COLUMNS].sort_values(["date", "permno"]).reset_index(drop=True)
    return sidecar


def _build_summary(
    sidecar: pd.DataFrame,
    *,
    permno: int,
    start_date: str,
    end_date: str,
    output_path: Path,
    summary_path: Path,
    source_file: str,
    source_sheet: str,
) -> dict[str, object]:
    return {
        "packet_id": "PHASE61_D350_WRDS_PIVOT_V1",
        "status": "ok",
        "source": "WRDS CRSP dsf",
        "permno": int(permno),
        "query_start_date": start_date,
        "query_end_date": end_date,
        "rows_extracted": int(len(sidecar)),
        "date_min": str(sidecar["date"].min().date()) if not sidecar.empty else None,
        "date_max": str(sidecar["date"].max().date()) if not sidecar.empty else None,
        "null_price_count": int(pd.to_numeric(sidecar["price"], errors="coerce").isna().sum()),
        "null_total_return_count": int(pd.to_numeric(sidecar["total_return"], errors="coerce").isna().sum()),
        "output_parquet": str(output_path),
        "output_columns": list(sidecar.columns),
        "summary_path": str(summary_path),
        "source_file": source_file,
        "source_sheet": source_sheet,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract bounded D-350 WRDS CRSP sidecar rows for AVTA / PERMNO 86544.")
    parser.add_argument("--permno", type=int, default=DEFAULT_PERMNO)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--output-parquet", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--output-summary-json", default=str(DEFAULT_SUMMARY_PATH))
    parser.add_argument("--source-file", default="wrds:crsp.dsf")
    parser.add_argument("--source-sheet", default="crsp.dsf")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_parquet)
    summary_path = Path(args.output_summary_json)
    source_as_of_date = pd.Timestamp(args.end_date)

    conn = _connect()
    try:
        raw_rows = _query_wrds_rows(conn, args.permno, args.start_date, args.end_date)
    finally:
        conn.close()

    sidecar = _normalize_sidecar(
        raw_rows,
        source_as_of_date=source_as_of_date,
        source_file=str(args.source_file),
        source_sheet=str(args.source_sheet),
    )
    summary = _build_summary(
        sidecar,
        permno=args.permno,
        start_date=args.start_date,
        end_date=args.end_date,
        output_path=output_path,
        summary_path=summary_path,
        source_file=str(args.source_file),
        source_sheet=str(args.source_sheet),
    )

    if int(summary["null_price_count"]) > 0 or int(summary["null_total_return_count"]) > 0:
        raise RuntimeError(
            "WRDS sidecar contains null price/total_return rows; refusing to publish an incomplete D-350 sidecar."
        )

    _atomic_write_parquet(sidecar, output_path)
    _atomic_write_json(summary, summary_path)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
