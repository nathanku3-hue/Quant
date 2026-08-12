from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from execution import broker_api as broker_mod
from execution.paper0 import (
    BrokerLifecycleEventV1,
    ExecutionIntentV1,
    ExecutionMapEntryV1,
    PAPER_EXECUTION_POLICY_ID,
    PAPER_TIME_IN_FORCE,
    Paper0AuthorityError,
    PaperExecutionMapV1,
    SessionCloseAuthorityV1,
    attach_signed_execution_intent,
    begin_paper_restart,
    build_paper_live_state,
    build_paper_order,
    paper_state_from_broker_snapshot,
    reconcile_paper_restart,
    verify_paper_live_state,
)
from execution.rebalancer import PortfolioRebalancer
from execution.risk_interceptor import RiskInterceptor


HASH_A = "a" * 64
HASH_B = "b" * 64


def _execution_map() -> PaperExecutionMapV1:
    return PaperExecutionMapV1(
        execution_map_id="PAPER_MAP_20260810",
        built_at="2026-08-10T12:00:00Z",
        entries=(
            ExecutionMapEntryV1(
                account_id="PAPER-ACCOUNT-1",
                instrument_id="CIQSEC:IQ1001",
                trading_item_id="SPT1001",
                broker_symbol="AAPL",
                broker_instrument_id="alpaca-asset-aapl",
                mapping_available_at="2026-08-10T11:55:00Z",
                source_receipt_hash=HASH_A,
            ),
        ),
    )


def _intent(execution_map: PaperExecutionMapV1, **overrides: object) -> ExecutionIntentV1:
    kwargs: dict[str, object] = {
        "account_id": "PAPER-ACCOUNT-1",
        "live_rebalance_id": "LRB-20260810-001",
        "promoted_policy_id": "POLICY-FROZEN-001",
        "promoted_seal_id": "SEAL-FROZEN-001",
        "execution_map_hash": execution_map.execution_map_hash,
        "instrument_id": "CIQSEC:IQ1001",
        "side": "buy",
        "quantity": 10,
        "execution_policy_id": PAPER_EXECUTION_POLICY_ID,
        "time_in_force": PAPER_TIME_IN_FORCE,
        "rebalance_epoch": 7,
    }
    kwargs.update(overrides)
    return ExecutionIntentV1(**kwargs)  # type: ignore[arg-type]


def _session_close() -> SessionCloseAuthorityV1:
    return SessionCloseAuthorityV1(
        session_date="2026-08-10",
        close_at="2026-08-10T16:00:00-04:00",
        verified_at="2026-08-10T16:01:00-04:00",
        calendar_id="XNYS-PRIMARY-CALENDAR-V1",
        verification_kind="ACTUAL_SESSION_CLOSE",
        source_receipt_hash=HASH_B,
    )


def _event(
    sequence: int,
    intent: ExecutionIntentV1,
    status: str,
    filled_quantity: int,
    *,
    observed_at: str,
) -> BrokerLifecycleEventV1:
    return BrokerLifecycleEventV1(
        sequence=sequence,
        client_order_id=intent.client_order_id,
        broker_order_id="broker-order-1",
        status=status,
        filled_quantity=filled_quantity,
        observed_at=observed_at,
    )


def test_execution_intent_identity_binds_all_mutable_authority_fields_or_fails_closed() -> None:
    execution_map = _execution_map()
    base = _intent(execution_map)

    mutations = [
        {"account_id": "PAPER-ACCOUNT-2"},
        {"live_rebalance_id": "LRB-20260810-002"},
        {"promoted_policy_id": "POLICY-FROZEN-002"},
        {"promoted_seal_id": "SEAL-FROZEN-002"},
        {"execution_map_hash": HASH_A},
        {"instrument_id": "CIQSEC:IQ1002"},
        {"side": "sell"},
        {"quantity": 11},
        {"rebalance_epoch": 8},
    ]
    for mutation in mutations:
        changed = replace(base, **mutation)
        assert changed.execution_intent_hash != base.execution_intent_hash
        assert changed.client_order_id != base.client_order_id

    with pytest.raises(Paper0AuthorityError, match="execution_policy_id"):
        replace(base, execution_policy_id="OTHER_POLICY")
    with pytest.raises(Paper0AuthorityError, match="time_in_force"):
        replace(base, time_in_force="day")


def test_execution_map_rejects_ambiguous_identity_and_ticker_only_instrument() -> None:
    row = _execution_map().entries[0]
    with pytest.raises(Paper0AuthorityError, match="ambiguous duplicate broker_symbol"):
        PaperExecutionMapV1(
            execution_map_id="AMBIGUOUS",
            built_at="2026-08-10T12:00:00Z",
            entries=(
                row,
                replace(
                    row,
                    instrument_id="CIQSEC:IQ1002",
                    trading_item_id="SPT1002",
                    broker_instrument_id="alpaca-asset-other",
                ),
            ),
        )
    with pytest.raises(Paper0AuthorityError, match="CIQSEC"):
        replace(row, instrument_id="AAPL")


def test_build_paper_order_requires_exact_map_epoch_session_and_explicit_cls() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    order = build_paper_order(
        intent,
        execution_map,
        _session_close(),
        current_rebalance_epoch=7,
        freeze_new_risk=False,
    )

    assert order["symbol"] == "AAPL"
    assert order["qty"] == 10
    assert order["order_type"] == "market"
    assert order["time_in_force"] == "cls"
    assert order["client_order_id"] == intent.client_order_id
    assert order["execution_intent_hash"] == intent.execution_intent_hash
    assert order["execution_map_hash"] == execution_map.execution_map_hash
    assert order["instrument_id"] == "CIQSEC:IQ1001"
    assert order["trading_item_id"] == "SPT1001"

    with pytest.raises(Paper0AuthorityError, match="STALE_REBALANCE_EPOCH"):
        build_paper_order(
            intent,
            execution_map,
            _session_close(),
            current_rebalance_epoch=8,
            freeze_new_risk=False,
        )
    with pytest.raises(Paper0AuthorityError, match="FREEZE_NEW_RISK_ACTIVE"):
        build_paper_order(
            intent,
            execution_map,
            _session_close(),
            current_rebalance_epoch=7,
            freeze_new_risk=True,
        )
    with pytest.raises(Paper0AuthorityError, match="EXECUTION_MAP_HASH_MISMATCH"):
        build_paper_order(
            replace(intent, execution_map_hash=HASH_A),
            execution_map,
            _session_close(),
            current_rebalance_epoch=7,
            freeze_new_risk=False,
        )


def test_freeze_new_risk_allows_only_risk_reducing_side_to_reach_existing_risk_gate() -> None:
    execution_map = _execution_map()
    sell_intent = _intent(execution_map, side="sell")
    order = build_paper_order(
        sell_intent,
        execution_map,
        _session_close(),
        current_rebalance_epoch=7,
        freeze_new_risk=True,
    )
    assert order["side"] == "sell"
    assert order["time_in_force"] == "cls"


def test_session_close_authority_rejects_assumption_or_preclose_verification() -> None:
    with pytest.raises(Paper0AuthorityError, match="unverified or assumed"):
        replace(_session_close(), verification_kind="ASSUME_1600")
    with pytest.raises(Paper0AuthorityError, match="verified before"):
        replace(_session_close(), verified_at="2026-08-10T15:59:00-04:00")


def test_signed_execution_envelope_payload_hash_changes_when_intent_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TZ_EXECUTION_ENVELOPE_SECRET", "paper0-unit-test-secret")
    execution_map = _execution_map()
    base = _intent(execution_map)
    changed = replace(base, quantity=11)

    signed_base = attach_signed_execution_intent(
        base,
        key_version="unit-test-key-v1",
        ttl_seconds=60,
    )
    signed_changed = attach_signed_execution_intent(
        changed,
        key_version="unit-test-key-v1",
        ttl_seconds=60,
    )

    assert signed_base["execution_intent"] == base.authority_body()
    assert signed_changed["execution_intent"] == changed.authority_body()
    assert (
        signed_base["signed_execution_envelope"]["payload_hash"]
        != signed_changed["signed_execution_envelope"]["payload_hash"]
    )


def test_paper_live_state_projects_partial_open_residual_then_final_fill_idempotently() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    partial_events = [
        _event(0, intent, "accepted", 0, observed_at="2026-08-10T19:59:50Z"),
        _event(1, intent, "partially_filled", 4, observed_at="2026-08-10T20:00:01Z"),
        _event(2, intent, "open", 4, observed_at="2026-08-10T20:00:02Z"),
    ]
    state = build_paper_live_state(
        [intent],
        partial_events,
        positions={"CIQSEC:IQ1001": "4"},
        cash="600.00",
        equity="1000.00",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )
    repeated = build_paper_live_state(
        [intent],
        partial_events,
        positions={"CIQSEC:IQ1001": "4"},
        cash="600",
        equity="1000",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )

    verify_paper_live_state(state)
    assert repeated["paper_state_hash"] == state["paper_state_hash"]
    assert state["open_orders"][0]["residual_quantity"] == 6
    assert state["partial_fill_residuals"][0]["residual_quantity"] == 6
    assert state["partial_fill_residuals"][0]["is_open"] is True

    final_state = build_paper_live_state(
        [intent],
        [
            *partial_events,
            _event(3, intent, "filled", 10, observed_at="2026-08-10T20:00:03Z"),
        ],
        positions={"CIQSEC:IQ1001": "10"},
        cash="0",
        equity="1000",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )
    assert final_state["open_orders"] == []
    assert final_state["partial_fill_residuals"] == []
    assert final_state["paper_state_hash"] != state["paper_state_hash"]


def test_paper_live_state_preserves_partial_cancel_residual_without_open_order() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    state = build_paper_live_state(
        [intent],
        [
            _event(0, intent, "accepted", 0, observed_at="2026-08-10T19:59:50Z"),
            _event(1, intent, "partially_filled", 4, observed_at="2026-08-10T20:00:01Z"),
            _event(2, intent, "canceled", 4, observed_at="2026-08-10T20:00:02Z"),
        ],
        positions={"CIQSEC:IQ1001": "4"},
        cash="600",
        equity="1000",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )

    assert state["open_orders"] == []
    assert state["partial_fill_residuals"] == [
        {
            "client_order_id": intent.client_order_id,
            "execution_intent_hash": intent.execution_intent_hash,
            "instrument_id": "CIQSEC:IQ1001",
            "status": "canceled",
            "filled_quantity": 4,
            "residual_quantity": 6,
            "is_open": False,
        }
    ]


def test_paper_live_state_fails_closed_on_unsupported_or_post_terminal_lifecycle() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    with pytest.raises(Paper0AuthorityError, match="UNSUPPORTED_PAPER_BROKER_STATUS"):
        _event(0, intent, "replaced", 0, observed_at="2026-08-10T20:00:00Z")
    with pytest.raises(Paper0AuthorityError, match="BROKER_EVENT_AFTER_TERMINAL_STATE"):
        build_paper_live_state(
            [intent],
            [
                _event(0, intent, "filled", 10, observed_at="2026-08-10T20:00:00Z"),
                _event(1, intent, "open", 10, observed_at="2026-08-10T20:00:01Z"),
            ],
            positions={"CIQSEC:IQ1001": "10"},
            cash="0",
            equity="1000",
            freeze_new_risk=True,
            reconciliation_status="BROKER_SNAPSHOT",
        )


def test_restart_begins_frozen_clears_only_on_exact_broker_reconciliation() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    events = [
        _event(0, intent, "accepted", 0, observed_at="2026-08-10T19:59:50Z"),
        _event(1, intent, "partially_filled", 4, observed_at="2026-08-10T20:00:01Z"),
        _event(2, intent, "open", 4, observed_at="2026-08-10T20:00:02Z"),
    ]
    local_state = build_paper_live_state(
        [intent],
        events,
        positions={"CIQSEC:IQ1001": "4"},
        cash="600",
        equity="1000",
        freeze_new_risk=False,
        reconciliation_status="COMMITTED",
    )
    broker_state = build_paper_live_state(
        [intent],
        events,
        positions={"CIQSEC:IQ1001": "4"},
        cash="600",
        equity="1000",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )

    restart_state = begin_paper_restart(local_state)
    assert restart_state["freeze_new_risk"] is True
    assert restart_state["reconciliation_status"] == "RESTART_RECONCILIATION_REQUIRED"

    reconciled = reconcile_paper_restart(local_state, broker_state)
    assert reconciled["freeze_new_risk"] is False
    assert reconciled["reconciliation_status"] == "RECONCILED"
    verify_paper_live_state(reconciled)

    mismatched_broker_state = build_paper_live_state(
        [intent],
        events,
        positions={"CIQSEC:IQ1001": "5"},
        cash="600",
        equity="1000",
        freeze_new_risk=True,
        reconciliation_status="BROKER_SNAPSHOT",
    )
    mismatch = reconcile_paper_restart(local_state, mismatched_broker_state)
    assert mismatch["freeze_new_risk"] is True
    assert mismatch["reconciliation_status"] == "RECONCILIATION_MISMATCH"
    assert "positions" in mismatch["reconciliation_mismatches"]
    verify_paper_live_state(mismatch)


class _TifBrokerStub:
    def __init__(self) -> None:
        self.submitted: list[dict[str, object]] = []

    def get_portfolio_state(self) -> dict[str, object]:
        return {"equity": 1000.0, "positions": {}}

    def get_latest_price(self, symbol: str) -> float:
        _ = symbol
        return 100.0

    def submit_order(
        self,
        *,
        symbol: str,
        qty: int,
        side: str,
        client_order_id: str,
        time_in_force: str,
    ) -> dict[str, object]:
        row = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "client_order_id": client_order_id,
            "time_in_force": time_in_force,
        }
        self.submitted.append(row)
        return {"ok": True, "status": "accepted", "order_id": "fake-1", **row}


def test_rebalancer_propagates_explicit_cls_without_silent_default() -> None:
    broker = _TifBrokerStub()
    rebalancer = PortfolioRebalancer(
        broker=broker,  # type: ignore[arg-type]
        risk_interceptor=RiskInterceptor(
            max_single_asset_weight=1.0,
            max_sector_weight=1.0,
            max_var_proxy=1.0,
        ),
    )
    execution_map = _execution_map()
    order = build_paper_order(
        _intent(execution_map),
        execution_map,
        _session_close(),
        current_rebalance_epoch=7,
        freeze_new_risk=False,
    )

    result = rebalancer.execute_orders([order])[0]["result"]
    assert broker.submitted[0]["time_in_force"] == "cls"
    assert result["time_in_force"] == "cls"


def _install_fake_alpaca(
    monkeypatch: pytest.MonkeyPatch,
    *,
    recovered_time_in_force: str,
) -> None:
    class _FakeREST:
        def __init__(self, api_key: str, api_secret: str, base_url: str, api_version: str) -> None:
            _ = api_key, api_secret, base_url, api_version

        def get_account(self) -> SimpleNamespace:
            return SimpleNamespace(cash="1000", equity="1000")

        def submit_order(self, **kwargs: object) -> object:
            _ = kwargs
            raise RuntimeError("transient submit timeout")

        def get_order_by_client_order_id(self, client_order_id: str) -> SimpleNamespace:
            return SimpleNamespace(
                id="recovered-1",
                status="accepted",
                client_order_id=client_order_id,
                symbol="AAPL",
                side="buy",
                qty="1",
                type="market",
                time_in_force=recovered_time_in_force,
                limit_price=None,
                created_at="2026-08-10T19:59:59Z",
                submitted_at="2026-08-10T20:00:00Z",
                updated_at="2026-08-10T20:00:00Z",
                filled_at=None,
                filled_qty="0",
                filled_avg_price=None,
            )

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)


def test_alpaca_recovery_requires_exact_cls_tif_for_paper_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_alpaca(monkeypatch, recovered_time_in_force="day")
    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(
        symbol="AAPL",
        qty=1,
        side="buy",
        time_in_force="cls",
        client_order_id="P0-recovery-tif-mismatch",
    )
    assert result["ok"] is False
    assert result["error"] == "recovery_mismatch"


def test_alpaca_recovery_accepts_exact_cls_tif_for_paper_intent(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_alpaca(monkeypatch, recovered_time_in_force="cls")
    broker = broker_mod.AlpacaBroker()
    result = broker.submit_order(
        symbol="AAPL",
        qty=1,
        side="buy",
        time_in_force="cls",
        client_order_id="P0-recovery-tif-match",
    )
    assert result["ok"] is True
    assert result["recovered"] is True
    assert result["time_in_force"] == "cls"


def test_read_only_broker_reconciliation_snapshot_projects_exact_open_residual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)

    class _FakeREST:
        def __init__(self, api_key: str, api_secret: str, base_url: str, api_version: str) -> None:
            _ = api_key, api_secret, base_url, api_version

        def get_account(self) -> SimpleNamespace:
            return SimpleNamespace(id="PAPER-ACCOUNT-1", cash="600.00", equity="1000.00")

        def list_positions(self) -> list[SimpleNamespace]:
            return [
                SimpleNamespace(
                    symbol="AAPL",
                    asset_id="alpaca-asset-aapl",
                    qty="4",
                )
            ]

        def list_orders(self, *, status: str, limit: int) -> list[SimpleNamespace]:
            _ = limit
            current = SimpleNamespace(
                id="broker-order-1",
                status="open",
                client_order_id=intent.client_order_id,
                symbol="AAPL",
                side="buy",
                qty="10",
                type="market",
                time_in_force="cls",
                limit_price=None,
                created_at="2026-08-10T19:59:50Z",
                submitted_at="2026-08-10T19:59:51Z",
                updated_at="2026-08-10T20:00:02Z",
                filled_at=None,
                filled_qty="4",
                filled_avg_price="100.00",
            )
            if status in {"open", "all"}:
                return [current]
            raise AssertionError(status)

    monkeypatch.setattr(broker_mod.tradeapi, "REST", _FakeREST)
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)
    monkeypatch.delenv("ALPACA_BASE_URL", raising=False)
    monkeypatch.delenv(broker_mod.LIVE_TRADING_BREAK_GLASS_ENV, raising=False)

    broker = broker_mod.AlpacaBroker()
    snapshot = broker.get_reconciliation_snapshot()
    assert snapshot["account_id"] == "PAPER-ACCOUNT-1"
    assert snapshot["positions"] == [
        {
            "symbol": "AAPL",
            "broker_instrument_id": "alpaca-asset-aapl",
            "quantity": "4",
        }
    ]
    assert snapshot["open_orders"][0]["time_in_force"] == "cls"
    assert snapshot["open_orders"][0]["filled_qty"] == 4

    state = paper_state_from_broker_snapshot(
        [intent],
        execution_map,
        snapshot,
        freeze_new_risk=True,
    )
    assert state["positions"] == [{"instrument_id": "CIQSEC:IQ1001", "quantity": "4"}]
    assert state["cash"] == "600"
    assert state["equity"] == "1000"
    assert state["open_orders"][0]["residual_quantity"] == 6
    assert state["partial_fill_residuals"][0]["residual_quantity"] == 6
    verify_paper_live_state(state)


def test_unknown_broker_open_order_preserves_freeze_by_failing_closed() -> None:
    execution_map = _execution_map()
    intent = _intent(execution_map)
    broker_snapshot = {
        "schema": "alpaca_paper_reconciliation_snapshot_v1",
        "captured_at_utc": "2026-08-10T20:00:05Z",
        "account_id": "PAPER-ACCOUNT-1",
        "cash": "1000",
        "equity": "1000",
        "positions": [],
        "open_orders": [
            {
                "order_id": "unknown-1",
                "client_order_id": "unknown-cid",
                "symbol": "AAPL",
                "side": "buy",
                "qty": 1,
                "order_type": "market",
                "time_in_force": "cls",
                "status": "open",
                "filled_qty": 0,
                "updated_at": "2026-08-10T20:00:02Z",
            }
        ],
        "recent_orders": [],
    }
    with pytest.raises(Paper0AuthorityError, match="UNKNOWN_OPEN_ORDER_PRESERVES_FREEZE"):
        paper_state_from_broker_snapshot([intent], execution_map, broker_snapshot)


def test_real_readiness_session_close_receipt_is_source_hash_bound_and_keeps_freeze() -> None:
    root = Path(__file__).resolve().parents[1]
    source_path = root / "data/paper0/readiness/session_close/nyse_regular_full_session_20260807.source.json"
    receipt_path = root / "data/paper0/readiness/session_close/nyse_regular_full_session_20260807.receipt.json"

    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    assert source_hash == "092eb09f1ec9bad099d01702978f92c2d7cce26e3fba6e555e85a8051a4401f4"
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    authority_raw = payload["authority"]
    authority = SessionCloseAuthorityV1(
        session_date=authority_raw["session_date"],
        close_at=authority_raw["close_at"],
        verified_at=authority_raw["verified_at"],
        calendar_id=authority_raw["calendar_id"],
        verification_kind=authority_raw["verification_kind"],
        source_receipt_hash=authority_raw["source_receipt_hash"],
    )
    assert authority.session_close_hash == authority_raw["session_close_hash"]
    assert payload["source_receipt_file_sha256"] == source_hash
    assert payload["future_order_date_specific_close_receipt_required"] is True
    assert payload["freeze_new_risk"] is True
    assert payload["broker_order_count"] == 0
    assert payload["financial_alpha_evidence"] == 0


def test_paper0_activity_surface_is_deferred_and_execution_map_preflight_remains_blocked() -> None:
    root = Path(__file__).resolve().parents[1]
    activity = json.loads(
        (root / "data/paper0/readiness/activity_surface/paper0_account_activity_decision_20260810.json").read_text(
            encoding="utf-8"
        )
    )
    map_preflight = json.loads(
        (root / "data/paper0/readiness/execution_map/paper_execution_map_preflight_20260810.json").read_text(
            encoding="utf-8"
        )
    )

    assert activity["decision"] == "NOT_REQUIRED_FOR_PAPER0_FIRST_REBALANCE"
    assert activity["freeze_new_risk"] is True
    assert activity["broker_order_count"] == 0
    assert "trade bust/correction normalization" in activity["paper1_deferred_scope"]

    assert map_preflight["status"] == "BLOCKED_NO_REAL_BROKER_ACCOUNT_ASSET_EVIDENCE"
    assert map_preflight["real_execution_map_receipt_admitted"] is False
    assert map_preflight["broker_asset_lookup_performed"] is False
    assert map_preflight["broker_order_endpoint_called"] is False
    assert map_preflight["freeze_new_risk"] is True
    assert map_preflight["financial_alpha_evidence"] == 0
