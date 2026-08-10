from __future__ import annotations

import hashlib
import json

import pandas as pd
import pytest

from research.aov0.historical_lifecycle import (
    CASH_MERGER_EVENT,
    DEFAULT_CASH_ELECTION_EVENT,
    TERMINAL_EVENTS_RECEIPT_SCHEMA,
    load_historical_terminal_events,
)


def _write_packet(tmp_path, *, event_type: str = CASH_MERGER_EVENT):
    tmp_path.mkdir(parents=True, exist_ok=True)
    events = tmp_path / "terminal_events.csv"
    frame = pd.DataFrame(
        [
            {
                "source_entity_id": "1",
                "security_id": "CIQSEC:101",
                "source_spt_item": "SPT101",
                "last_trading_date": "2025-08-15",
                "effective_date": "2025-08-18",
                "cash_consideration": "7.50",
                "currency": "USD",
                "event_type": event_type,
                "source_authority": "SEC:PRIMARY_FILING",
                "source_locator": "https://www.sec.gov/example",
            }
        ]
    )
    frame.to_csv(events, index=False, lineterminator="\n")
    binding = {
        "source_entity_id": "1",
        "security_id": "CIQSEC:101",
        "source_spt_item": "SPT101",
        "last_trading_date": "2025-08-15",
        "effective_date": "2025-08-18",
        "cash_consideration": "7.5",
        "currency": "USD",
        "event_type": event_type,
        "source_authority": "SEC:PRIMARY_FILING",
        "source_locator": "https://www.sec.gov/example",
    }
    receipt = tmp_path / "terminal_events.receipt.json"
    payload = {
        "schema_version": TERMINAL_EVENTS_RECEIPT_SCHEMA,
        "event_count": 1,
        "events_sha256": hashlib.sha256(events.read_bytes()).hexdigest(),
        "event_bindings": [binding],
        "current_screen_conditioned": False,
        "current_primary_security_conditioned": False,
        "financial_alpha_evidence": 0,
    }
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    return events, receipt


@pytest.mark.parametrize("event_type", [CASH_MERGER_EVENT, DEFAULT_CASH_ELECTION_EVENT])
def test_terminal_event_loader_accepts_source_bound_cash_settlement_types(tmp_path, event_type: str) -> None:
    events, receipt = _write_packet(tmp_path, event_type=event_type)
    loaded = load_historical_terminal_events(events, receipt)

    assert len(loaded.frame) == 1
    assert loaded.frame.iloc[0]["event_type"] == event_type
    assert float(loaded.frame.iloc[0]["cash_consideration"]) == pytest.approx(7.5)
    assert loaded.metadata["financial_alpha_evidence"] == 0


def test_terminal_event_loader_rejects_hash_or_current_conditioning_drift(tmp_path) -> None:
    events, receipt = _write_packet(tmp_path)
    events.write_text(events.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash_mismatch"):
        load_historical_terminal_events(events, receipt)

    events, receipt = _write_packet(tmp_path / "conditioned")
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["current_screen_conditioned"] = True
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="current_screen_conditioned"):
        load_historical_terminal_events(events, receipt)
