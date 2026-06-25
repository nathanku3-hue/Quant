from __future__ import annotations

import json
from pathlib import Path

from v2_discovery.data_lab.permission_matrix import build_default_wrds_permission_matrix
from v2_discovery.data_lab.snapshot_manifest import build_wrds_snapshot_manifest


def _source_text() -> str:
    package_dir = Path("v2_discovery/data_lab")
    return "\n".join(path.read_text(encoding="utf-8") for path in sorted(package_dir.glob("*.py")))


def test_v2_d0_data_lab_has_no_provider_connection_or_runtime_surface():
    source = _source_text()
    forbidden_tokens = (
        "import wrds",
        "wrds.Connection",
        "yfinance",
        "build_market_data_provider",
        "BrokerPort",
        "submit_order",
        "emit_alert",
        "OpenClaw",
        "notifier",
        "streamlit",
        "CandidateRegistry",
        "promote_candidate",
        "sqlite3",
        "sqlalchemy",
    )

    assert all(token not in source for token in forbidden_tokens)


def test_v2_d0_data_lab_has_no_v1_canonical_write_primitives():
    source = _source_text()
    forbidden_tokens = (
        "to_parquet",
        "to_csv",
        "os.replace",
        "write_manifest",
        "write_json_atomic",
    )

    assert all(token not in source for token in forbidden_tokens)


def test_v2_d0_builders_do_not_modify_existing_v1_artifacts():
    watched = [
        Path("data/processed/prices.parquet"),
        Path("data/processed/prices_tri.parquet"),
        Path("data/processed/tickers.parquet"),
        Path("data/processed/universe_r3000_daily.parquet"),
        Path("runtime/boot_status_current.json"),
    ]
    before = {path: path.read_bytes() for path in watched if path.exists()}

    matrix = build_default_wrds_permission_matrix(created_at_utc="2026-06-01T00:00:00Z")
    manifest = build_wrds_snapshot_manifest(matrix, created_at_utc="2026-06-01T00:00:00Z")

    assert json.dumps(matrix.to_dict(), sort_keys=True)
    assert json.dumps(manifest.to_dict(), sort_keys=True)
    assert before == {path: path.read_bytes() for path in before}
