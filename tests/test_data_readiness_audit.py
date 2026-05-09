from __future__ import annotations

import pandas as pd
import pytest

from scripts.audit_data_readiness import ReadinessConfig
from scripts.audit_data_readiness import run_audit
from scripts.audit_data_readiness import write_report_with_manifest


def _write_parquet(path, frame):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


def _seed_ready_repo(root):
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "permno": [1, 1, 2],
            "adj_close": [10.0, 10.1, 20.0],
            "total_ret": [0.0, 0.01, -0.01],
        }
    )
    simple = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-02"]),
            "permno": [1],
            "value": [1.0],
        }
    )
    _write_parquet(root / "data/processed/prices_tri.parquet", prices)
    _write_parquet(root / "data/processed/fundamentals.parquet", simple)
    _write_parquet(root / "data/processed/tickers.parquet", simple)
    _write_parquet(root / "data/static/sector_map.parquet", pd.DataFrame({"ticker": ["A"], "sector": ["TECH"]}))
    _write_parquet(root / "data/processed/macro_features.parquet", simple)
    _write_parquet(root / "data/processed/liquidity_features.parquet", simple)
    _write_parquet(root / "data/processed/sidecar_sp500_pro_2023_2024.parquet", simple)


def test_data_readiness_report_flags_missing_artifacts(tmp_path):
    report = run_audit(ReadinessConfig(repo_root=tmp_path, output_path=tmp_path / "report.json"))

    assert report["ready_for_paper_alerts"] is False
    assert "missing_prices_tri" in report["blockers"]
    assert "missing_fundamentals" in report["blockers"]


def test_data_readiness_report_passes_seeded_daily_lake_and_writes_manifest(tmp_path):
    _seed_ready_repo(tmp_path)
    output = tmp_path / "data/processed/data_readiness_report.json"

    report = run_audit(ReadinessConfig(repo_root=tmp_path, output_path=output))
    manifest_path = write_report_with_manifest(report, output)

    assert report["ready_for_paper_alerts"] is True
    assert report["blockers"] == []
    assert output.exists()
    assert manifest_path.exists()

