from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from research.aov0.contracts import DEFAULT_CONTRACT
from scripts.aov0_build_decision_cut import _extract_receipt, build_decision_cut
from scripts.aov0_first_seal import (
    EXECUTION_CALENDAR_ID,
    _load_decision_cut,
    _universe_hash_from_primitives,
)


TARGET_DATE = pd.Timestamp("2026-08-07")
VALID_EVALUATION_START = "2026-08-10T20:00:00Z"


def _write_receipt(path: Path, source_id: str, raw_hash: str, retrieved_at: str | None) -> None:
    payload = {"source_id": source_id, "raw_object_sha256": raw_hash}
    if retrieved_at is not None:
        payload["retrieved_at"] = retrieved_at
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _inputs(tmp_path: Path) -> dict[str, Path]:
    rule = pd.DataFrame({"date": [TARGET_DATE], "CIQSEC:101": [0.35], "CIQSEC:202": [0.35]})
    returns = pd.DataFrame({"date": [TARGET_DATE], "CIQSEC:101": [0.003], "CIQSEC:202": [-0.001]})
    primitives = pd.DataFrame(
        {
            "date": [TARGET_DATE, TARGET_DATE],
            "security_id": ["CIQSEC:101", "CIQSEC:202"],
            "total_return": [0.003, -0.001],
            "known_at": ["2026-08-07T20:05:00Z", "2026-08-07T20:05:00Z"],
        }
    )
    sofr = pd.DataFrame(
        {
            "effective_date": [pd.Timestamp("2026-08-06")],
            "published_at": [pd.Timestamp("2026-08-07T19:05:00Z")],
            "sofr_percent": [5.30],
        }
    )
    paths = {
        "rule100_path": tmp_path / "rule100_targets.parquet",
        "returns_path": tmp_path / "total_returns.parquet",
        "primitives_path": tmp_path / "vertical_primitives.parquet",
        "sofr_path": tmp_path / "official_sofr.parquet",
    }
    rule.to_parquet(paths["rule100_path"], index=False)
    returns.to_parquet(paths["returns_path"], index=False)
    primitives.to_parquet(paths["primitives_path"], index=False)
    sofr.to_parquet(paths["sofr_path"], index=False)
    return paths


def _receipts(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "fundamentals_receipt_path": tmp_path / "fundamentals.json",
        "security_receipt_path": tmp_path / "security.json",
        "market_receipt_path": tmp_path / "market.json",
        "sofr_receipt_path": tmp_path / "sofr.json",
    }
    _write_receipt(paths["fundamentals_receipt_path"], "SPCIQPRO:QUARTERLY_FUNDAMENTALS", "b" * 64, "2026-08-07T16:46:27Z")
    _write_receipt(paths["security_receipt_path"], "SPCIQPRO:PRIMARY_SECURITY_MASTER", "c" * 64, "2026-08-07T17:10:00Z")
    _write_receipt(paths["market_receipt_path"], "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA", "d" * 64, "2026-08-07T20:05:00Z")
    _write_receipt(paths["sofr_receipt_path"], "NYFED:SOFR", "e" * 64, "2026-08-07T19:05:00Z")
    return paths


def _build(tmp_path: Path, **overrides):
    paths = {**_inputs(tmp_path), **_receipts(tmp_path)}
    kwargs = {
        **paths,
        "evaluation_start": VALID_EVALUATION_START,
        "output_path": tmp_path / "decision_cut.json",
        "cut_built_at": datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
    }
    kwargs.update(overrides)
    return build_decision_cut(**kwargs)


def test_fundamentals_receipt_requires_explicit_retrieval_authority(tmp_path: Path) -> None:
    receipt = tmp_path / "fundamentals.json"
    _write_receipt(receipt, "SPCIQPRO:QUARTERLY_FUNDAMENTALS", "b" * 64, None)
    with pytest.raises(ValueError, match="retrieved_at_required"):
        _extract_receipt(receipt, expected_source_id="SPCIQPRO:QUARTERLY_FUNDAMENTALS")


def test_decision_cut_builder_binds_v3_close_evaluation_and_four_actual_receipts(tmp_path: Path) -> None:
    out = tmp_path / "decision_cut.json"
    result = _build(tmp_path, output_path=out)
    assert result["status"] == "AOV0_CIQ_DECISION_CUT_READY"
    assert result["knowledge_cutoff"] == "2026-08-07T20:05:00Z"
    assert result["cut_built_at"] == "2026-08-07T20:10:00Z"
    assert result["evaluation_start"] == VALID_EVALUATION_START
    payload = _load_decision_cut(out)
    assert payload["schema_version"] == "aov0_ciq_decision_cut_v3"
    assert payload["execution_calendar_id"] == EXECUTION_CALENDAR_ID == "NYSE_2026_CORE_CLOSE_1600_ET"
    assert payload["evaluation_start"] == VALID_EVALUATION_START
    assert payload["contract_hash"] == DEFAULT_CONTRACT.contract_hash
    primitives = pd.read_parquet(tmp_path / "vertical_primitives.parquet")
    assert payload["universe_hash"] == _universe_hash_from_primitives(primitives)
    assert set(payload["input_sha256"]) == {
        "rule100_targets",
        "vertical_primitives",
        "total_returns",
        "official_sofr",
    }
    assert set(payload["source_receipts"]) == {
        "ciq_quarterly_fundamentals",
        "ciq_security_master",
        "ciq_market_data",
        "nyfed_sofr",
    }


def test_decision_cut_rejects_same_day_close_instead_of_next_eligible_close(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evaluation_start_not_expected_nyse_core_close"):
        _build(tmp_path, evaluation_start="2026-08-07T20:00:00Z")


def test_decision_cut_rejects_saturday_close(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evaluation_start_not_expected_nyse_core_close"):
        _build(tmp_path, evaluation_start="2026-08-08T20:00:00Z")


def test_decision_cut_rejects_legacy_0930_open_timestamp(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evaluation_start_not_expected_nyse_core_close"):
        _build(tmp_path, evaluation_start="2026-08-10T13:30:00Z")


def test_decision_cut_rejects_cut_build_before_latest_source_knowledge(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="built_before_knowledge_cutoff"):
        _build(tmp_path, cut_built_at=datetime(2026, 8, 7, 20, 0, tzinfo=UTC))


def test_decision_cut_rejects_evaluation_at_or_before_cut(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="evaluation_not_after_cut"):
        _build(tmp_path, cut_built_at=datetime(2026, 8, 10, 20, 0, tzinfo=UTC))


def test_decision_cut_rejects_target_total_return_mismatch_between_primitives_and_pnl(tmp_path: Path) -> None:
    paths = {**_inputs(tmp_path), **_receipts(tmp_path)}
    returns = pd.read_parquet(paths["returns_path"])
    returns.loc[0, "CIQSEC:101"] = 0.004
    returns.to_parquet(paths["returns_path"], index=False)
    with pytest.raises(ValueError, match="target_total_return_mismatch"):
        build_decision_cut(
            **paths,
            evaluation_start=VALID_EVALUATION_START,
            output_path=tmp_path / "decision_cut.json",
            cut_built_at=datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
        )


def test_decision_cut_rejects_target_asset_set_mismatch_between_rule100_and_returns(tmp_path: Path) -> None:
    paths = {**_inputs(tmp_path), **_receipts(tmp_path)}
    returns = pd.read_parquet(paths["returns_path"]).drop(columns=["CIQSEC:202"])
    returns.to_parquet(paths["returns_path"], index=False)
    with pytest.raises(ValueError, match="rule100_return_asset_set_mismatch"):
        build_decision_cut(
            **paths,
            evaluation_start=VALID_EVALUATION_START,
            output_path=tmp_path / "decision_cut.json",
            cut_built_at=datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
        )


def test_decision_cut_rejects_same_day_market_receipt_before_1600_et(tmp_path: Path) -> None:
    paths = {**_inputs(tmp_path), **_receipts(tmp_path)}
    _write_receipt(
        paths["market_receipt_path"],
        "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
        "d" * 64,
        "2026-08-07T17:20:00Z",
    )
    with pytest.raises(ValueError, match="current_daily_bar_not_complete_before_1600_et"):
        build_decision_cut(
            **paths,
            evaluation_start=VALID_EVALUATION_START,
            output_path=tmp_path / "decision_cut.json",
            cut_built_at=datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
        )


def test_v2_decision_cut_is_not_an_active_reader_compatibility_path(tmp_path: Path) -> None:
    out = tmp_path / "decision_cut.json"
    _build(tmp_path, output_path=out)
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["schema_version"] = "aov0_ciq_decision_cut_v2"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="decision_cut_schema_invalid"):
        _load_decision_cut(out)
