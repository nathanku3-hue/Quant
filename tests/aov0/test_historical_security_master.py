from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.aov0.historical_security_master import (
    HISTORICAL_SECURITY_MASTER_CAPTURE_MODE,
    HISTORICAL_SECURITY_MASTER_FREEZE_MODE,
    HISTORICAL_SECURITY_MASTER_RECEIPT_SCHEMA,
    HISTORICAL_SECURITY_MASTER_SELECTION,
    HISTORICAL_SECURITY_MASTER_SOURCE_ID,
    HistoricalSecurityMasterError,
    load_historical_start_security_master,
)


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    master = tmp_path / "historical_primary_20250516.csv"
    pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "2"],
            "SP_SECURITY_ID": ["IQ101", "IQ202"],
            "SP_CIQ_ID": ["IQ101", "IQ202"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT1001", "SPT2002"],
            "SP_TRADING_ITEM_ID": ["1001", "2002"],
            "Ticker": ["AAA", "BBB"],
            "Exchange": ["NYSE", "NASDAQGS"],
        }
    ).to_csv(master, index=False)
    digest = hashlib.sha256(master.read_bytes()).hexdigest()
    receipt: dict[str, object] = {
        "schema_version": HISTORICAL_SECURITY_MASTER_RECEIPT_SCHEMA,
        "source_id": HISTORICAL_SECURITY_MASTER_SOURCE_ID,
        "capture_mode": HISTORICAL_SECURITY_MASTER_CAPTURE_MODE,
        "identity_freeze_mode": HISTORICAL_SECURITY_MASTER_FREEZE_MODE,
        "primary_security_selection": HISTORICAL_SECURITY_MASTER_SELECTION,
        "market_perspective": "321247",
        "mi_key_field_key": "322517",
        "price_field_key": "324251",
        "price_date_secondary_key": "sk_557",
        "exchange_group_field_key": "406718",
        "exchange_group_value": "-1,-4",
        "funding_type_field_key": "321268",
        "funding_type_values": ["1", "16"],
        "primary_issue_field_requested": False,
        "exactly_one_screen_security_per_entity": True,
        "historical_as_of_mechanically_bound": True,
        "current_primary_conditioned": False,
        "requested_cutoff_date": "2025-05-16",
        "provider_effective_as_of_date": "2025-05-16",
        "security_id_source_metric": "SP_CIQ_ID",
        "trading_item_source_metric": "SP_TRADING_ITEM_ID",
        "raw_object_name": master.name,
        "raw_object_sha256": digest,
        "raw_object_bytes": master.stat().st_size,
        "result_count": 2,
        "observed_identity_columns": [
            "SP_ENTITY_ID",
            "SP_SECURITY_ID",
            "SP_CIQ_ID",
            "SPT_INSTRUMENT_ITEM_ID",
            "SP_TRADING_ITEM_ID",
        ],
        "financial_alpha_evidence": 0,
        "prospective_clock_authority": "NONE",
        "parent_child_mutation_authority": "NONE",
    }
    receipt_path = tmp_path / "historical_primary_20250516.receipt.json"
    receipt_path.write_text(json.dumps(receipt, sort_keys=True), encoding="utf-8")
    return master, receipt_path, receipt


def test_historical_security_master_admits_exact_asof_primary_identity(tmp_path: Path) -> None:
    master, receipt, _ = _write_fixture(tmp_path)
    admitted = load_historical_start_security_master(
        master,
        receipt,
        expected_as_of_date="2025-05-16",
        expected_entity_ids=("1", "2"),
    )
    assert admitted.entity_ids == ("1", "2")
    assert admitted.security_ids == ("CIQSEC:IQ101", "CIQSEC:IQ202")
    assert admitted.trading_item_ids == ("1001", "2002")
    assert admitted.metadata["historical_primary_security_identity_reconstructed"] is True
    assert admitted.metadata["historical_screen_security_identity_reconstructed"] is True
    assert admitted.metadata["current_primary_conditioned"] is False
    assert admitted.metadata["financial_alpha_evidence"] == 0


def test_historical_security_master_rejects_current_conditioning_or_asof_drift(tmp_path: Path) -> None:
    master, receipt_path, receipt = _write_fixture(tmp_path)
    receipt["current_primary_conditioned"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalSecurityMasterError, match="current_primary_conditioning_forbidden"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "2"),
        )

    _, receipt_path, receipt = _write_fixture(tmp_path)
    receipt["provider_effective_as_of_date"] = "2026-08-08"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalSecurityMasterError, match="provider_effective_as_of_date_mismatch"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "2"),
        )

    master, receipt_path, receipt = _write_fixture(tmp_path)
    receipt["primary_issue_field_requested"] = True
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalSecurityMasterError, match="current_primary_field_forbidden"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "2"),
        )


def test_historical_security_master_rejects_tamper_membership_or_identity_alias_drift(tmp_path: Path) -> None:
    master, receipt_path, _ = _write_fixture(tmp_path)
    with master.open("a", encoding="utf-8") as handle:
        handle.write("3,IQ303,IQ303,SPT3003,3003,CCC,NYSE\n")
    with pytest.raises(HistoricalSecurityMasterError, match="hash_mismatch"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "2"),
        )

    master, receipt_path, receipt = _write_fixture(tmp_path)
    frame = pd.read_csv(master, dtype=str)
    frame.loc[0, "SP_SECURITY_ID"] = "IQ999"
    frame.to_csv(master, index=False)
    receipt["raw_object_sha256"] = hashlib.sha256(master.read_bytes()).hexdigest()
    receipt["raw_object_bytes"] = master.stat().st_size
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(HistoricalSecurityMasterError, match="security_id_alias_mismatch"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "2"),
        )

    master, receipt_path, _ = _write_fixture(tmp_path)
    with pytest.raises(HistoricalSecurityMasterError, match="entity_membership_mismatch"):
        load_historical_start_security_master(
            master,
            receipt_path,
            expected_as_of_date="2025-05-16",
            expected_entity_ids=("1", "3"),
        )
