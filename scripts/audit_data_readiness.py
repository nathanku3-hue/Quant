from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from data.provenance import ManifestInput  # noqa: E402
from data.provenance import SOURCE_QUALITY_CANONICAL  # noqa: E402
from data.provenance import build_manifest  # noqa: E402
from data.provenance import utc_now_iso  # noqa: E402
from data.provenance import write_json_atomic  # noqa: E402
from data.provenance import write_manifest  # noqa: E402

DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "data_readiness_report.json"


@dataclass(frozen=True)
class ReadinessConfig:
    repo_root: Path = PROJECT_ROOT
    output_path: Path = DEFAULT_OUTPUT_PATH
    stale_after_date: pd.Timestamp = pd.Timestamp("2024-01-01")


ARTIFACT_GROUPS = {
    "prices_tri": ("data/processed/prices_tri.parquet",),
    "fundamentals": (
        "data/processed/fundamentals.parquet",
        "data/processed/fundamentals_pit.parquet",
        "data/processed/daily_fundamentals_panel.parquet",
    ),
    "ticker_map": (
        "data/processed/tickers.parquet",
        "data/static/instrument_mapping.parquet",
    ),
    "sector_map": ("data/static/sector_map.parquet",),
    "macro": (
        "data/processed/macro_features.parquet",
        "data/processed/macro.parquet",
    ),
    "liquidity": ("data/processed/liquidity_features.parquet",),
    "sidecars": (
        "data/processed/sidecar_sp500_pro_2023_2024.parquet",
        "data/processed/orbis_daily_aligned.parquet",
        "data/processed/sidecar_moodys_bd.parquet",
    ),
}


def _sql_escape(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _atomic_write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _inspect_parquet(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "row_count": 0,
        "date_range": {"start": None, "end": None},
        "null_key_rows": None,
        "duplicate_date_permno": None,
        "return_null_ratio": None,
        "price_null_ratio": None,
        "columns": [],
    }
    if not path.exists():
        return result

    con = duckdb.connect()
    try:
        columns = [
            str(row[0])
            for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape(path)}')").fetchall()
        ]
        result["columns"] = columns
        result["row_count"] = int(
            con.execute(f"SELECT COUNT(*) FROM read_parquet('{_sql_escape(path)}')").fetchone()[0]
        )
        if "date" in columns:
            min_date, max_date = con.execute(
                f"""
                SELECT MIN(CAST(date AS DATE)), MAX(CAST(date AS DATE))
                FROM read_parquet('{_sql_escape(path)}')
                """
            ).fetchone()
            result["date_range"] = {
                "start": str(min_date) if min_date is not None else None,
                "end": str(max_date) if max_date is not None else None,
            }
        if {"date", "permno"}.issubset(set(columns)):
            result["null_key_rows"] = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM read_parquet('{_sql_escape(path)}')
                    WHERE date IS NULL OR permno IS NULL
                    """
                ).fetchone()[0]
            )
            result["duplicate_date_permno"] = int(
                con.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM (
                      SELECT CAST(date AS DATE), CAST(permno AS BIGINT), COUNT(*) AS n
                      FROM read_parquet('{_sql_escape(path)}')
                      GROUP BY 1, 2
                      HAVING COUNT(*) > 1
                    )
                    """
                ).fetchone()[0]
            )
        for candidate in ("ret", "total_ret", "total_return"):
            if candidate in columns:
                result["return_null_ratio"] = float(
                    con.execute(
                        f"""
                        SELECT AVG(CASE WHEN {candidate} IS NULL THEN 1.0 ELSE 0.0 END)
                        FROM read_parquet('{_sql_escape(path)}')
                        """
                    ).fetchone()[0]
                    or 0.0
                )
                break
        for candidate in ("adj_close", "raw_close", "price", "close"):
            if candidate in columns:
                result["price_null_ratio"] = float(
                    con.execute(
                        f"""
                        SELECT AVG(CASE WHEN {candidate} IS NULL THEN 1.0 ELSE 0.0 END)
                        FROM read_parquet('{_sql_escape(path)}')
                        """
                    ).fetchone()[0]
                    or 0.0
                )
                break
    finally:
        con.close()
    return result


def _resolve_group(repo_root: Path, candidates: tuple[str, ...]) -> dict[str, Any]:
    inspected = [_inspect_parquet(repo_root / rel) for rel in candidates]
    existing = [row for row in inspected if row["exists"]]
    primary = existing[0] if existing else inspected[0]
    return {
        "present": bool(existing),
        "primary_path": primary["path"],
        "candidates": inspected,
    }


def run_audit(config: ReadinessConfig) -> dict[str, Any]:
    groups = {
        name: _resolve_group(config.repo_root, candidates)
        for name, candidates in ARTIFACT_GROUPS.items()
    }
    blockers: list[str] = []
    warnings: list[str] = []
    for name, group in groups.items():
        if not group["present"]:
            blockers.append(f"missing_{name}")
            continue
        primary = next(row for row in group["candidates"] if row["exists"])
        if int(primary.get("row_count") or 0) <= 0:
            blockers.append(f"empty_{name}")
        if primary.get("null_key_rows") not in (None, 0):
            blockers.append(f"null_keys_{name}")
        if primary.get("duplicate_date_permno") not in (None, 0):
            blockers.append(f"duplicate_date_permno_{name}")
        max_date = pd.to_datetime(primary.get("date_range", {}).get("end"), errors="coerce")
        if pd.notna(max_date) and max_date < config.stale_after_date:
            warnings.append(f"stale_{name}_max_date_{max_date.date()}")

    price_group = groups["prices_tri"]
    if price_group["present"]:
        price_primary = next(row for row in price_group["candidates"] if row["exists"])
        if (price_primary.get("return_null_ratio") or 0.0) > 0.10:
            blockers.append("prices_tri_return_null_ratio_gt_10pct")
        if (price_primary.get("price_null_ratio") or 0.0) > 0.10:
            blockers.append("prices_tri_price_null_ratio_gt_10pct")

    report = {
        "schema_version": "1.0.0",
        "generated_at_utc": utc_now_iso(),
        "scope": "US equities daily bars paper-alert readiness",
        "ready_for_paper_alerts": bool(not blockers),
        "blockers": blockers,
        "warnings": warnings,
        "artifact_groups": groups,
    }
    return report


def write_report_with_manifest(report: dict[str, Any], output_path: Path) -> Path:
    write_json_atomic(report, output_path)
    manifest = build_manifest(
        ManifestInput(
            artifact_path=output_path,
            source_quality=SOURCE_QUALITY_CANONICAL,
            provider="terminal_zero",
            provider_feed="data_readiness_audit",
            license_scope="internal_governance_report",
            row_count=1,
            date_range={"start": report["generated_at_utc"], "end": report["generated_at_utc"]},
            schema_version=str(report.get("schema_version") or "1.0.0"),
        )
    )
    return write_manifest(manifest, artifact_path=output_path)


def parse_args() -> ReadinessConfig:
    parser = argparse.ArgumentParser(description="Audit local data readiness for daily paper alerts.")
    parser.add_argument("--repo-root", default=str(PROJECT_ROOT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--stale-after-date", default="2024-01-01")
    args = parser.parse_args()
    return ReadinessConfig(
        repo_root=Path(args.repo_root),
        output_path=Path(args.output),
        stale_after_date=pd.Timestamp(args.stale_after_date),
    )


def main() -> None:
    cfg = parse_args()
    report = run_audit(cfg)
    manifest_path = write_report_with_manifest(report, cfg.output_path)
    print(json.dumps(report, indent=2, sort_keys=True))
    print(f"Report: {cfg.output_path}")
    print(f"Manifest: {manifest_path}")
    if not report["ready_for_paper_alerts"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
