from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path

import pytest

import execution.signed_envelope as signed_envelope_mod
from execution.signed_envelope import SIGNED_EXECUTION_ENVELOPE_FIELD
from execution.signed_envelope import attach_signed_execution_envelope
from execution.signed_envelope import verify_local_submit_envelope_and_replay

_NOW_UTC = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def _envelope_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    ledger_path = tmp_path / "execution_replay_ledger.jsonl"
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-test-v1")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-02-28T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_KEY_LEGAL_HOLD", "YES")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_EXECUTION_ENVELOPE_SECRET", "signed-envelope-replay-test-secret")
    monkeypatch.setenv("TZ_EXECUTION_REPLAY_LEDGER_PATH", str(ledger_path))
    return ledger_path


def _build_signed_payload(*, batch_id: str, client_order_id: str) -> dict[str, object]:
    payload: dict[str, object] = {
        "batch_id": batch_id,
        "timestamp": "2026-03-01T00:00:00Z",
        "execution_orders": [
            {
                "ticker": "AAPL",
                "target_weight": 0.2,
                "client_order_id": client_order_id,
                "action": "BUY",
                "order_type": "MARKET",
                "limit_price": "Market",
                "trade_day": "2026-03-01",
            }
        ],
    }
    attach_signed_execution_envelope(payload, now_utc=_NOW_UTC, key_version="hmac-test-v1")
    return payload


def test_verify_local_submit_rejects_duplicate_replay(_envelope_env: Path):
    payload = _build_signed_payload(batch_id="batch-dup", client_order_id="cid-dup")

    verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)

    with pytest.raises(ValueError, match="replay detected for intent_id=batch-dup"):
        verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)

    ledger_lines = [line for line in _envelope_env.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(ledger_lines) == 1


def test_verify_local_submit_quarantines_malformed_ledger_line(_envelope_env: Path):
    _envelope_env.write_text('{"replay_key":"existing:nonce"}\n{malformed\n', encoding="utf-8")
    payload = _build_signed_payload(batch_id="batch-malformed", client_order_id="cid-malformed")

    with pytest.raises(ValueError, match="replay ledger malformed rows detected; submit rejected fail-closed"):
        verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)

    sidecar_path = _envelope_env.with_name(f"{_envelope_env.name}.malformed.jsonl")
    assert sidecar_path.exists()
    quarantine_rows = [json.loads(line) for line in sidecar_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(quarantine_rows) == 1
    assert quarantine_rows[0]["reason"] == "json_decode_error"
    assert "raw_line" in quarantine_rows[0]

    ledger_rows = [json.loads(line) for line in _envelope_env.read_text(encoding="utf-8").splitlines() if line]
    assert len(ledger_rows) == 1
    assert ledger_rows[0]["replay_key"] == "existing:nonce"

    verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)
    ledger_rows = [json.loads(line) for line in _envelope_env.read_text(encoding="utf-8").splitlines() if line]
    assert len(ledger_rows) == 2
    envelope = payload[SIGNED_EXECUTION_ENVELOPE_FIELD]
    assert isinstance(envelope, dict)
    expected_replay_key = f"batch-malformed:{envelope['nonce']}"
    assert {row["replay_key"] for row in ledger_rows} == {"existing:nonce", expected_replay_key}


def test_verify_local_submit_fsyncs_parent_dir_after_rewrite(
    _envelope_env: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    _envelope_env.write_text('{"replay_key":"existing:nonce"}\n{malformed\n', encoding="utf-8")
    payload = _build_signed_payload(batch_id="batch-fsync-parent", client_order_id="cid-fsync-parent")
    fsync_parent_calls: list[Path] = []

    def _record_fsync_parent(path: Path) -> None:
        fsync_parent_calls.append(Path(path))

    monkeypatch.setattr(signed_envelope_mod, "_fsync_parent_dir_if_possible", _record_fsync_parent)

    with pytest.raises(ValueError, match="replay ledger malformed rows detected; submit rejected fail-closed"):
        verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)

    assert fsync_parent_calls
    assert fsync_parent_calls[-1] == _envelope_env.parent


def test_verify_local_submit_atomic_append_under_rapid_sequential_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
):
    ledger_path = tmp_path / "nested" / "replay" / "execution_replay_ledger.jsonl"
    monkeypatch.setenv("TZ_HMAC_KEY_VERSION", "hmac-test-v1")
    monkeypatch.setenv("TZ_HMAC_KEY_ACTIVATED_AT_UTC", "2026-02-28T00:00:00Z")
    monkeypatch.setenv("TZ_HMAC_KEY_LEGAL_HOLD", "YES")
    monkeypatch.setenv("TZ_HMAC_ROTATION_DAYS", "1")
    monkeypatch.setenv("TZ_EXECUTION_ENVELOPE_SECRET", "signed-envelope-replay-test-secret")
    monkeypatch.setenv("TZ_EXECUTION_REPLAY_LEDGER_PATH", str(ledger_path))

    payload = _build_signed_payload(batch_id="batch-rapid", client_order_id="cid-rapid")
    accepted = 0
    rejected = 0
    for _ in range(50):
        try:
            verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)
            accepted += 1
        except ValueError as exc:
            assert "replay detected for intent_id=batch-rapid" in str(exc)
            rejected += 1

    assert accepted == 1
    assert rejected == 49
    assert ledger_path.exists()
    ledger_rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines() if line]
    assert len(ledger_rows) == 1


def test_verify_local_submit_fail_closed_on_replay_lock_timeout_and_logs_quality_debt(
    _envelope_env: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    payload = _build_signed_payload(batch_id="batch-lock-timeout", client_order_id="cid-lock-timeout")

    def _raise_timeout(_handle, *, timeout_ms: int) -> None:
        assert timeout_ms == signed_envelope_mod.DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS
        raise TimeoutError("synthetic replay lock timeout")

    monkeypatch.setattr(signed_envelope_mod, "_acquire_exclusive_lock", _raise_timeout)
    caplog.clear()
    with caplog.at_level("WARNING", logger=signed_envelope_mod.__name__):
        with pytest.raises(TimeoutError, match="synthetic replay lock timeout"):
            verify_local_submit_envelope_and_replay(payload, now_utc=_NOW_UTC)

    assert not _envelope_env.exists()
    quality_debt_events: list[dict[str, object]] = []
    for record in caplog.records:
        payload_text = record.getMessage()
        try:
            payload_map = json.loads(payload_text)
        except json.JSONDecodeError:
            continue
        if payload_map.get("event_key") == signed_envelope_mod.QUALITY_DEBT_EVENT_KEY_REPLAY_LOCK_TIMEOUT:
            quality_debt_events.append(payload_map)
    assert len(quality_debt_events) == 1
    quality_debt_event = quality_debt_events[0]
    assert isinstance(quality_debt_event.get("timestamp_utc"), str)
    detail = quality_debt_event.get("detail")
    assert isinstance(detail, dict)
    assert detail["timeout_ms"] == signed_envelope_mod.DEFAULT_EXECUTION_REPLAY_LOCK_TIMEOUT_MS
    assert detail["error"] == "synthetic replay lock timeout"
