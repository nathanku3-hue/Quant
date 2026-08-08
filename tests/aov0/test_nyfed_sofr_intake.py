from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.aov0_fetch_nyfed_sofr import (
    SOFR_URL,
    _ensure_after_gate,
    fetch_and_admit_sofr,
    parse_sofr_payload,
)


def _payload() -> bytes:
    return json.dumps(
        {
            "refRates": [
                {"effectiveDate": "2026-08-05", "percentRate": 5.31, "type": "SOFR"},
                {"effectiveDate": "2026-08-06", "percentRate": 5.30, "type": "SOFR"},
            ]
        }
    ).encode("utf-8")


def test_nyfed_gate_blocks_before_1500_et() -> None:
    # August is EDT, so 18:59 UTC is 14:59 New York.
    with pytest.raises(RuntimeError, match="before_1500_et"):
        _ensure_after_gate(datetime(2026, 8, 7, 18, 59, tzinfo=UTC))


def test_nyfed_gate_opens_at_1500_et() -> None:
    _ensure_after_gate(datetime(2026, 8, 7, 19, 0, tzinfo=UTC))


def test_parse_sofr_uses_retrieval_time_as_conservative_information_time() -> None:
    retrieved = datetime(2026, 8, 7, 19, 5, tzinfo=UTC)
    frame = parse_sofr_payload(_payload(), retrieved_at=retrieved)
    assert frame["effective_date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-08-05", "2026-08-06"]
    assert frame["sofr_percent"].tolist() == pytest.approx([5.31, 5.30])
    assert frame["published_at"].nunique() == 1
    assert str(frame["published_at"].iloc[0]) == "2026-08-07 19:05:00+00:00"


def test_sofr_intake_does_not_call_network_before_gate(tmp_path: Path) -> None:
    calls: list[str] = []

    def fetcher(url: str):
        calls.append(url)
        return _payload(), SOFR_URL

    with pytest.raises(RuntimeError, match="before_1500_et"):
        fetch_and_admit_sofr(
            now=datetime(2026, 8, 7, 18, 30, tzinfo=UTC),
            fetcher=fetcher,
            raw_path=tmp_path / "raw.json",
            parquet_path=tmp_path / "official_sofr.parquet",
            receipt_path=tmp_path / "receipt.json",
        )
    assert calls == []
    assert list(tmp_path.iterdir()) == []


def test_sofr_intake_writes_raw_parquet_and_receipt_after_gate(tmp_path: Path) -> None:
    raw_path = tmp_path / "raw.json"
    parquet_path = tmp_path / "official_sofr.parquet"
    receipt_path = tmp_path / "receipt.json"

    def fetcher(url: str):
        assert url == SOFR_URL
        return _payload(), SOFR_URL

    result = fetch_and_admit_sofr(
        now=datetime(2026, 8, 7, 19, 5, tzinfo=UTC),
        fetcher=fetcher,
        raw_path=raw_path,
        parquet_path=parquet_path,
        receipt_path=receipt_path,
    )
    assert result["status"] == "DIRECT_NYFED_SOFR_ADMITTED_AFTER_1500_ET"
    assert raw_path.read_bytes() == _payload()
    frame = pd.read_parquet(parquet_path)
    assert frame.columns.tolist() == ["effective_date", "published_at", "sofr_percent"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["source_id"] == "NYFED:SOFR"
    assert receipt["retrieved_at"] == "2026-08-07T19:05:00Z"
    assert receipt["published_at_semantics"] == "CONSERVATIVE_RETRIEVAL_TIME_AS_INFORMATION_AVAILABILITY"
    assert receipt["raw_object_sha256"] == result["raw_sha256"]


def test_sofr_intake_rejects_redirect_off_nyfed(tmp_path: Path) -> None:
    def fetcher(url: str):
        return _payload(), "https://example.com/not-nyfed.json"

    with pytest.raises(RuntimeError, match="untrusted_redirect_or_host"):
        fetch_and_admit_sofr(
            now=datetime(2026, 8, 7, 19, 5, tzinfo=UTC),
            fetcher=fetcher,
            raw_path=tmp_path / "raw.json",
            parquet_path=tmp_path / "official_sofr.parquet",
            receipt_path=tmp_path / "receipt.json",
        )
    assert list(tmp_path.iterdir()) == []
