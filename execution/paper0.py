"""PAPER-0 execution authority primitives.

This module is deliberately provider/broker-call free.  It constructs and verifies
immutable PAPER execution identity, projects already-observed broker lifecycle
rows into a committed PAPER state, and performs restart reconciliation.  Broker
submission remains outside this module.

PAPER-0 is operational evidence only.  Nothing here creates financial-alpha or
strategy-live-capital authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
import re
from typing import Any, Iterable, Mapping


EXECUTION_INTENT_SCHEMA = "execution_intent_v1"
EXECUTION_MAP_SCHEMA = "paper_execution_map_v1"
SESSION_CLOSE_SCHEMA = "paper_session_close_authority_v1"
PAPER_STATE_SCHEMA = "paper_live_state_v1"
PAPER_EXECUTION_POLICY_ID = "MOC_CLOSE_AUCTION_V1"
PAPER_ORDER_TYPE = "market"
PAPER_TIME_IN_FORCE = "cls"
PAPER_CLIENT_ORDER_PREFIX = "P0-"

_SUPPORTED_BROKER_STATUSES = {
    "accepted",
    "new",
    "pending_new",
    "open",
    "partially_filled",
    "filled",
    "canceled",
    "rejected",
}
_OPEN_BROKER_STATUSES = {"accepted", "new", "pending_new", "open", "partially_filled"}
_TERMINAL_BROKER_STATUSES = {"filled", "canceled", "rejected"}
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_CIQSEC_RE = re.compile(r"^CIQSEC:[A-Za-z0-9._:-]+$")


class Paper0AuthorityError(ValueError):
    """Fail-closed PAPER-0 authority error."""


def _required_text(value: Any, *, field: str) -> str:
    text = str(value).strip()
    if not text:
        raise Paper0AuthorityError(f"{field} is required")
    return text


def _positive_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise Paper0AuthorityError(f"{field} must be a positive integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise Paper0AuthorityError(f"{field} must be a positive integer") from None
    if parsed <= 0:
        raise Paper0AuthorityError(f"{field} must be a positive integer")
    if isinstance(value, float) and not math.isclose(value, float(parsed), abs_tol=0.0):
        raise Paper0AuthorityError(f"{field} must be a positive integer")
    return parsed


def _nonnegative_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool):
        raise Paper0AuthorityError(f"{field} must be a nonnegative integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise Paper0AuthorityError(f"{field} must be a nonnegative integer") from None
    if parsed < 0:
        raise Paper0AuthorityError(f"{field} must be a nonnegative integer")
    if isinstance(value, float) and not math.isclose(value, float(parsed), abs_tol=0.0):
        raise Paper0AuthorityError(f"{field} must be a nonnegative integer")
    return parsed


def _sha256_hex(value: str, *, field: str) -> str:
    text = _required_text(value, field=field).lower()
    if not _HASH_RE.fullmatch(text):
        raise Paper0AuthorityError(f"{field} must be a lowercase SHA-256 hex digest")
    return text


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _content_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _aware_timestamp(value: Any, *, field: str) -> datetime:
    text = _required_text(value, field=field)
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        raise Paper0AuthorityError(f"{field} must be an ISO-8601 timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise Paper0AuthorityError(f"{field} must include a UTC offset")
    return parsed


def _canonical_decimal(value: Any, *, field: str, nonnegative: bool = False) -> str:
    if isinstance(value, (bool, float)):
        raise Paper0AuthorityError(f"{field} forbids bool/binary-float values")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise Paper0AuthorityError(f"{field} must be a finite decimal") from None
    if not parsed.is_finite():
        raise Paper0AuthorityError(f"{field} must be a finite decimal")
    if nonnegative and parsed < 0:
        raise Paper0AuthorityError(f"{field} must be nonnegative")
    if parsed == 0:
        return "0"
    text = format(parsed.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _canonical_positions(raw: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for instrument_id, quantity in sorted(raw.items(), key=lambda item: str(item[0])):
        instrument = _required_text(instrument_id, field="positions.instrument_id")
        if not _CIQSEC_RE.fullmatch(instrument):
            raise Paper0AuthorityError("PAPER positions require canonical CIQSEC:<id> identity")
        rows.append(
            {
                "instrument_id": instrument,
                "quantity": _canonical_decimal(
                    quantity,
                    field=f"positions[{instrument}].quantity",
                    nonnegative=True,
                ),
            }
        )
    return rows


@dataclass(frozen=True, slots=True)
class ExecutionMapEntryV1:
    """One exact CIQ Security/Trading Item to broker-instrument mapping."""

    account_id: str
    instrument_id: str
    trading_item_id: str
    broker_symbol: str
    broker_instrument_id: str
    mapping_available_at: str
    source_receipt_hash: str

    def __post_init__(self) -> None:
        account_id = _required_text(self.account_id, field="account_id")
        instrument_id = _required_text(self.instrument_id, field="instrument_id")
        if not _CIQSEC_RE.fullmatch(instrument_id):
            raise Paper0AuthorityError("instrument_id must use canonical CIQSEC:<id> identity")
        trading_item_id = _required_text(self.trading_item_id, field="trading_item_id")
        if not trading_item_id.upper().startswith("SPT"):
            raise Paper0AuthorityError("trading_item_id must bind the exact SPT trading-item identity")
        broker_symbol = _required_text(self.broker_symbol, field="broker_symbol").upper()
        broker_instrument_id = _required_text(self.broker_instrument_id, field="broker_instrument_id")
        _aware_timestamp(self.mapping_available_at, field="mapping_available_at")
        source_receipt_hash = _sha256_hex(self.source_receipt_hash, field="source_receipt_hash")
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "instrument_id", instrument_id)
        object.__setattr__(self, "trading_item_id", trading_item_id)
        object.__setattr__(self, "broker_symbol", broker_symbol)
        object.__setattr__(self, "broker_instrument_id", broker_instrument_id)
        object.__setattr__(self, "source_receipt_hash", source_receipt_hash)

    def to_dict(self) -> dict[str, Any]:
        return {
            "account_id": self.account_id,
            "instrument_id": self.instrument_id,
            "trading_item_id": self.trading_item_id,
            "broker_symbol": self.broker_symbol,
            "broker_instrument_id": self.broker_instrument_id,
            "mapping_available_at": self.mapping_available_at,
            "source_receipt_hash": self.source_receipt_hash,
        }


@dataclass(frozen=True, slots=True)
class PaperExecutionMapV1:
    """Content-addressed, single-account PAPER execution map."""

    execution_map_id: str
    built_at: str
    entries: tuple[ExecutionMapEntryV1, ...]

    def __post_init__(self) -> None:
        execution_map_id = _required_text(self.execution_map_id, field="execution_map_id")
        built_at = _aware_timestamp(self.built_at, field="built_at")
        if not self.entries:
            raise Paper0AuthorityError("execution map requires at least one entry")
        if not all(isinstance(row, ExecutionMapEntryV1) for row in self.entries):
            raise Paper0AuthorityError("execution map entries must be ExecutionMapEntryV1")
        account_ids = {row.account_id for row in self.entries}
        if len(account_ids) != 1:
            raise Paper0AuthorityError("PAPER execution map must bind exactly one broker account")
        for field_name, values in {
            "instrument_id": [row.instrument_id for row in self.entries],
            "trading_item_id": [row.trading_item_id for row in self.entries],
            "broker_symbol": [row.broker_symbol for row in self.entries],
            "broker_instrument_id": [row.broker_instrument_id for row in self.entries],
        }.items():
            if len(values) != len(set(values)):
                raise Paper0AuthorityError(f"execution map contains ambiguous duplicate {field_name}")
        for row in self.entries:
            if _aware_timestamp(row.mapping_available_at, field="mapping_available_at") > built_at:
                raise Paper0AuthorityError("execution map cannot predate a mapping availability timestamp")
        object.__setattr__(self, "execution_map_id", execution_map_id)
        object.__setattr__(self, "entries", tuple(sorted(self.entries, key=lambda row: row.instrument_id)))

    @property
    def account_id(self) -> str:
        return self.entries[0].account_id

    def authority_body(self) -> dict[str, Any]:
        return {
            "schema": EXECUTION_MAP_SCHEMA,
            "execution_map_id": self.execution_map_id,
            "built_at": self.built_at,
            "entries": [row.to_dict() for row in self.entries],
        }

    @property
    def execution_map_hash(self) -> str:
        return _content_hash(self.authority_body())

    def to_dict(self) -> dict[str, Any]:
        return {**self.authority_body(), "execution_map_hash": self.execution_map_hash}

    def resolve(self, *, account_id: str, instrument_id: str) -> ExecutionMapEntryV1:
        account = _required_text(account_id, field="account_id")
        instrument = _required_text(instrument_id, field="instrument_id")
        if account != self.account_id:
            raise Paper0AuthorityError("execution intent account_id does not match execution map account")
        matches = [row for row in self.entries if row.instrument_id == instrument]
        if len(matches) != 1:
            raise Paper0AuthorityError("execution map must resolve exactly one broker instrument")
        return matches[0]


@dataclass(frozen=True, slots=True)
class ExecutionIntentV1:
    """Immutable authority-bearing PAPER order intent."""

    account_id: str
    live_rebalance_id: str
    promoted_policy_id: str
    promoted_seal_id: str
    execution_map_hash: str
    instrument_id: str
    side: str
    quantity: int
    execution_policy_id: str
    time_in_force: str
    rebalance_epoch: int

    def __post_init__(self) -> None:
        account_id = _required_text(self.account_id, field="account_id")
        live_rebalance_id = _required_text(self.live_rebalance_id, field="live_rebalance_id")
        promoted_policy_id = _required_text(self.promoted_policy_id, field="promoted_policy_id")
        promoted_seal_id = _required_text(self.promoted_seal_id, field="promoted_seal_id")
        execution_map_hash = _sha256_hex(self.execution_map_hash, field="execution_map_hash")
        instrument_id = _required_text(self.instrument_id, field="instrument_id")
        if not _CIQSEC_RE.fullmatch(instrument_id):
            raise Paper0AuthorityError("ExecutionIntentV1 instrument_id must use canonical CIQSEC:<id>")
        side = _required_text(self.side, field="side").lower()
        if side not in {"buy", "sell"}:
            raise Paper0AuthorityError("ExecutionIntentV1 side must be buy or sell")
        quantity = _positive_int(self.quantity, field="quantity")
        execution_policy_id = _required_text(self.execution_policy_id, field="execution_policy_id")
        if execution_policy_id != PAPER_EXECUTION_POLICY_ID:
            raise Paper0AuthorityError(
                f"PAPER-0 requires execution_policy_id={PAPER_EXECUTION_POLICY_ID}"
            )
        time_in_force = _required_text(self.time_in_force, field="time_in_force").lower()
        if time_in_force != PAPER_TIME_IN_FORCE:
            raise Paper0AuthorityError(f"PAPER-0 requires time_in_force={PAPER_TIME_IN_FORCE}")
        rebalance_epoch = _positive_int(self.rebalance_epoch, field="rebalance_epoch")
        object.__setattr__(self, "account_id", account_id)
        object.__setattr__(self, "live_rebalance_id", live_rebalance_id)
        object.__setattr__(self, "promoted_policy_id", promoted_policy_id)
        object.__setattr__(self, "promoted_seal_id", promoted_seal_id)
        object.__setattr__(self, "execution_map_hash", execution_map_hash)
        object.__setattr__(self, "instrument_id", instrument_id)
        object.__setattr__(self, "side", side)
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "execution_policy_id", execution_policy_id)
        object.__setattr__(self, "time_in_force", time_in_force)
        object.__setattr__(self, "rebalance_epoch", rebalance_epoch)

    def authority_body(self) -> dict[str, Any]:
        return {
            "schema": EXECUTION_INTENT_SCHEMA,
            "account_id": self.account_id,
            "live_rebalance_id": self.live_rebalance_id,
            "promoted_policy_id": self.promoted_policy_id,
            "promoted_seal_id": self.promoted_seal_id,
            "execution_map_hash": self.execution_map_hash,
            "instrument_id": self.instrument_id,
            "side": self.side,
            "quantity": self.quantity,
            "execution_policy_id": self.execution_policy_id,
            "time_in_force": self.time_in_force,
            "rebalance_epoch": self.rebalance_epoch,
        }

    @property
    def execution_intent_hash(self) -> str:
        return _content_hash(self.authority_body())

    @property
    def client_order_id(self) -> str:
        # Compact deterministic identity derived only from the full authority object.
        return f"{PAPER_CLIENT_ORDER_PREFIX}{self.execution_intent_hash[:32]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.authority_body(),
            "execution_intent_hash": self.execution_intent_hash,
            "client_order_id": self.client_order_id,
        }


@dataclass(frozen=True, slots=True)
class SessionCloseAuthorityV1:
    """Externally resolved session-close truth; never assumes a fixed 16:00 close."""

    session_date: str
    close_at: str
    verified_at: str
    calendar_id: str
    verification_kind: str
    source_receipt_hash: str

    def __post_init__(self) -> None:
        session_date_text = _required_text(self.session_date, field="session_date")
        try:
            parsed_date = date.fromisoformat(session_date_text)
        except ValueError:
            raise Paper0AuthorityError("session_date must be YYYY-MM-DD") from None
        close_at = _aware_timestamp(self.close_at, field="close_at")
        verified_at = _aware_timestamp(self.verified_at, field="verified_at")
        if close_at.date() != parsed_date:
            raise Paper0AuthorityError("session_date must match the offset-local date of close_at")
        if verified_at < close_at:
            raise Paper0AuthorityError("session close cannot be verified before the resolved close")
        calendar_id = _required_text(self.calendar_id, field="calendar_id")
        verification_kind = _required_text(self.verification_kind, field="verification_kind").upper()
        if verification_kind not in {"ACTUAL_SESSION_CLOSE", "VERIFIED_REGULAR_FULL_SESSION"}:
            raise Paper0AuthorityError("unverified or assumed session-close authority is forbidden")
        source_receipt_hash = _sha256_hex(self.source_receipt_hash, field="source_receipt_hash")
        object.__setattr__(self, "calendar_id", calendar_id)
        object.__setattr__(self, "verification_kind", verification_kind)
        object.__setattr__(self, "source_receipt_hash", source_receipt_hash)

    def authority_body(self) -> dict[str, Any]:
        return {
            "schema": SESSION_CLOSE_SCHEMA,
            "session_date": self.session_date,
            "close_at": self.close_at,
            "verified_at": self.verified_at,
            "calendar_id": self.calendar_id,
            "verification_kind": self.verification_kind,
            "source_receipt_hash": self.source_receipt_hash,
        }

    @property
    def session_close_hash(self) -> str:
        return _content_hash(self.authority_body())


def build_paper_order(
    intent: ExecutionIntentV1,
    execution_map: PaperExecutionMapV1,
    session_close: SessionCloseAuthorityV1,
    *,
    current_rebalance_epoch: int,
    freeze_new_risk: bool,
) -> dict[str, Any]:
    """Resolve one immutable intent into a broker-ready order dictionary.

    No broker call occurs.  The returned dictionary carries an explicit ``cls``
    TIF so the generic rebalancer cannot silently default the PAPER path to day.
    """

    if not isinstance(intent, ExecutionIntentV1):
        raise Paper0AuthorityError("intent must be ExecutionIntentV1")
    if not isinstance(execution_map, PaperExecutionMapV1):
        raise Paper0AuthorityError("execution_map must be PaperExecutionMapV1")
    if not isinstance(session_close, SessionCloseAuthorityV1):
        raise Paper0AuthorityError("session_close must be SessionCloseAuthorityV1")
    epoch = _positive_int(current_rebalance_epoch, field="current_rebalance_epoch")
    if intent.rebalance_epoch != epoch:
        raise Paper0AuthorityError("STALE_REBALANCE_EPOCH")
    if intent.execution_map_hash != execution_map.execution_map_hash:
        raise Paper0AuthorityError("EXECUTION_MAP_HASH_MISMATCH")
    if bool(freeze_new_risk) and intent.side == "buy":
        raise Paper0AuthorityError("FREEZE_NEW_RISK_ACTIVE")
    entry = execution_map.resolve(account_id=intent.account_id, instrument_id=intent.instrument_id)
    if _aware_timestamp(entry.mapping_available_at, field="mapping_available_at") > _aware_timestamp(
        session_close.verified_at,
        field="verified_at",
    ):
        raise Paper0AuthorityError("EXECUTION_MAPPING_NOT_AVAILABLE_AT_SESSION_VERIFICATION")
    return {
        "symbol": entry.broker_symbol,
        "qty": intent.quantity,
        "side": intent.side,
        "order_type": PAPER_ORDER_TYPE,
        "time_in_force": intent.time_in_force,
        "client_order_id": intent.client_order_id,
        "execution_intent_hash": intent.execution_intent_hash,
        "execution_intent": intent.to_dict(),
        "execution_map_hash": execution_map.execution_map_hash,
        "broker_instrument_id": entry.broker_instrument_id,
        "instrument_id": intent.instrument_id,
        "trading_item_id": entry.trading_item_id,
        "paper_session_close_hash": session_close.session_close_hash,
        "live_rebalance_id": intent.live_rebalance_id,
        "rebalance_epoch": intent.rebalance_epoch,
    }


def attach_signed_execution_intent(
    intent: ExecutionIntentV1,
    *,
    now_utc: datetime | None = None,
    key_version: str | None = None,
    ttl_seconds: int | None = None,
) -> dict[str, Any]:
    """Reuse the existing signed-envelope authority over the exact intent body."""

    from execution.signed_envelope import attach_signed_execution_envelope

    payload = {"execution_intent": intent.authority_body()}
    return attach_signed_execution_envelope(
        payload,
        now_utc=now_utc,
        key_version=key_version,
        ttl_seconds=ttl_seconds,
    )


@dataclass(frozen=True, slots=True)
class BrokerLifecycleEventV1:
    sequence: int
    client_order_id: str
    broker_order_id: str
    status: str
    filled_quantity: int
    observed_at: str

    def __post_init__(self) -> None:
        sequence = _nonnegative_int(self.sequence, field="sequence")
        client_order_id = _required_text(self.client_order_id, field="client_order_id")
        broker_order_id = _required_text(self.broker_order_id, field="broker_order_id")
        status = _required_text(self.status, field="status").lower()
        if status == "cancelled":
            status = "canceled"
        if status not in _SUPPORTED_BROKER_STATUSES:
            raise Paper0AuthorityError(f"UNSUPPORTED_PAPER_BROKER_STATUS:{status}")
        filled_quantity = _nonnegative_int(self.filled_quantity, field="filled_quantity")
        _aware_timestamp(self.observed_at, field="observed_at")
        object.__setattr__(self, "sequence", sequence)
        object.__setattr__(self, "client_order_id", client_order_id)
        object.__setattr__(self, "broker_order_id", broker_order_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "filled_quantity", filled_quantity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "client_order_id": self.client_order_id,
            "broker_order_id": self.broker_order_id,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "observed_at": self.observed_at,
        }


def _project_order_states(
    intents: Iterable[ExecutionIntentV1],
    lifecycle_events: Iterable[BrokerLifecycleEventV1],
) -> list[dict[str, Any]]:
    intent_rows = list(intents)
    if not intent_rows:
        raise Paper0AuthorityError("at least one ExecutionIntentV1 is required")
    if not all(isinstance(row, ExecutionIntentV1) for row in intent_rows):
        raise Paper0AuthorityError("intents must contain only ExecutionIntentV1 rows")
    by_cid = {row.client_order_id: row for row in intent_rows}
    if len(by_cid) != len(intent_rows):
        raise Paper0AuthorityError("duplicate ExecutionIntentV1 client_order_id")

    events = list(lifecycle_events)
    if not all(isinstance(row, BrokerLifecycleEventV1) for row in events):
        raise Paper0AuthorityError("lifecycle_events must contain BrokerLifecycleEventV1 rows")
    if [row.sequence for row in events] != list(range(len(events))):
        raise Paper0AuthorityError("broker lifecycle sequence must be contiguous from zero")

    state: dict[str, dict[str, Any]] = {}
    for event in events:
        intent = by_cid.get(event.client_order_id)
        if intent is None:
            raise Paper0AuthorityError("broker lifecycle event references unknown client_order_id")
        prior = state.get(event.client_order_id)
        if event.filled_quantity > intent.quantity:
            raise Paper0AuthorityError("BROKER_FILL_EXCEEDS_INTENT_QUANTITY")
        if prior is not None:
            if event.broker_order_id != prior["broker_order_id"]:
                raise Paper0AuthorityError("BROKER_ORDER_ID_CHANGED_FOR_INTENT")
            if event.filled_quantity < int(prior["filled_quantity"]):
                raise Paper0AuthorityError("BROKER_FILLED_QUANTITY_REGRESSED")
            if str(prior["status"]) in _TERMINAL_BROKER_STATUSES:
                raise Paper0AuthorityError("BROKER_EVENT_AFTER_TERMINAL_STATE")
        if event.status == "partially_filled" and not (0 < event.filled_quantity < intent.quantity):
            raise Paper0AuthorityError("PARTIAL_FILL_REQUIRES_STRICT_PARTIAL_QUANTITY")
        if event.status == "filled" and event.filled_quantity != intent.quantity:
            raise Paper0AuthorityError("FILLED_STATUS_REQUIRES_FULL_INTENT_QUANTITY")
        if event.status == "rejected" and event.filled_quantity != 0:
            raise Paper0AuthorityError("REJECTED_STATUS_CANNOT_HAVE_FILLED_QUANTITY")
        if event.status == "canceled" and event.filled_quantity >= intent.quantity:
            raise Paper0AuthorityError("CANCELED_STATUS_REQUIRES_UNFILLED_RESIDUAL")
        state[event.client_order_id] = {
            "client_order_id": event.client_order_id,
            "execution_intent_hash": intent.execution_intent_hash,
            "instrument_id": intent.instrument_id,
            "side": intent.side,
            "ordered_quantity": intent.quantity,
            "broker_order_id": event.broker_order_id,
            "status": event.status,
            "filled_quantity": event.filled_quantity,
            "residual_quantity": intent.quantity - event.filled_quantity,
            "observed_at": event.observed_at,
            "is_open": event.status in _OPEN_BROKER_STATUSES,
        }

    rows: list[dict[str, Any]] = []
    for intent in sorted(intent_rows, key=lambda row: row.client_order_id):
        projected = state.get(intent.client_order_id)
        if projected is None:
            rows.append(
                {
                    "client_order_id": intent.client_order_id,
                    "execution_intent_hash": intent.execution_intent_hash,
                    "instrument_id": intent.instrument_id,
                    "side": intent.side,
                    "ordered_quantity": intent.quantity,
                    "broker_order_id": None,
                    "status": "INTENT_NOT_ACKNOWLEDGED",
                    "filled_quantity": 0,
                    "residual_quantity": intent.quantity,
                    "observed_at": None,
                    "is_open": False,
                }
            )
        else:
            rows.append(projected)
    return rows


def build_paper_live_state(
    intents: Iterable[ExecutionIntentV1],
    lifecycle_events: Iterable[BrokerLifecycleEventV1],
    *,
    positions: Mapping[str, Any],
    cash: Any,
    equity: Any,
    freeze_new_risk: bool,
    reconciliation_status: str,
) -> dict[str, Any]:
    """Project canonical PAPER state from already-observed broker truth.

    The state commitment intentionally includes open orders and partial-fill
    residuals, unlike the historical Portfolio V0 book hash.
    """

    intent_rows = list(intents)
    if not intent_rows:
        raise Paper0AuthorityError("at least one ExecutionIntentV1 is required")
    account_ids = {row.account_id for row in intent_rows}
    live_rebalance_ids = {row.live_rebalance_id for row in intent_rows}
    promoted_policy_ids = {row.promoted_policy_id for row in intent_rows}
    promoted_seal_ids = {row.promoted_seal_id for row in intent_rows}
    epochs = {row.rebalance_epoch for row in intent_rows}
    map_hashes = {row.execution_map_hash for row in intent_rows}
    if any(
        len(values) != 1
        for values in (
            account_ids,
            live_rebalance_ids,
            promoted_policy_ids,
            promoted_seal_ids,
            epochs,
            map_hashes,
        )
    ):
        raise Paper0AuthorityError(
            "one PAPER live state must bind one account/rebalance/policy/seal/epoch/execution-map"
        )
    order_states = _project_order_states(intent_rows, lifecycle_events)
    open_orders = [dict(row) for row in order_states if bool(row["is_open"]) and int(row["residual_quantity"]) > 0]
    partial_fill_residuals = [
        {
            "client_order_id": row["client_order_id"],
            "execution_intent_hash": row["execution_intent_hash"],
            "instrument_id": row["instrument_id"],
            "status": row["status"],
            "filled_quantity": row["filled_quantity"],
            "residual_quantity": row["residual_quantity"],
            "is_open": row["is_open"],
        }
        for row in order_states
        if int(row["filled_quantity"]) > 0 and int(row["residual_quantity"]) > 0
    ]
    reconciliation = _required_text(reconciliation_status, field="reconciliation_status").upper()
    body = {
        "schema": PAPER_STATE_SCHEMA,
        "account_id": next(iter(account_ids)),
        "live_rebalance_id": next(iter(live_rebalance_ids)),
        "rebalance_epoch": next(iter(epochs)),
        "execution_map_hash": next(iter(map_hashes)),
        "freeze_new_risk": bool(freeze_new_risk),
        "reconciliation_status": reconciliation,
        "positions": _canonical_positions(positions),
        "cash": _canonical_decimal(cash, field="cash", nonnegative=True),
        "equity": _canonical_decimal(equity, field="equity", nonnegative=True),
        "order_states": order_states,
        "open_orders": open_orders,
        "partial_fill_residuals": partial_fill_residuals,
        "latest_broker_lifecycle_state": [
            {
                "client_order_id": row["client_order_id"],
                "status": row["status"],
                "observed_at": row["observed_at"],
            }
            for row in order_states
        ],
    }
    return {**body, "paper_state_hash": _content_hash(body)}


def paper_state_from_broker_snapshot(
    intents: Iterable[ExecutionIntentV1],
    execution_map: PaperExecutionMapV1,
    broker_snapshot: Mapping[str, Any],
    *,
    freeze_new_risk: bool = True,
    reconciliation_status: str = "BROKER_SNAPSHOT",
) -> dict[str, Any]:
    """Translate one read-only Alpaca reconciliation snapshot into PAPER state.

    Broker positions must match both broker asset identity and symbol in the
    frozen execution map.  Unknown open orders fail closed because they are
    residual account risk; unrelated historical closed orders may remain in the
    broker's recent-order window without becoming current rebalance authority.
    """

    intent_rows = list(intents)
    if not intent_rows:
        raise Paper0AuthorityError("at least one ExecutionIntentV1 is required")
    if str(broker_snapshot.get("schema", "")) != "alpaca_paper_reconciliation_snapshot_v1":
        raise Paper0AuthorityError("unsupported broker reconciliation snapshot schema")
    snapshot_account_id = _required_text(broker_snapshot.get("account_id"), field="broker.account_id")
    if snapshot_account_id != execution_map.account_id:
        raise Paper0AuthorityError("BROKER_ACCOUNT_ID_MISMATCH")
    if any(row.account_id != snapshot_account_id for row in intent_rows):
        raise Paper0AuthorityError("ExecutionIntentV1 account does not match broker reconciliation account")
    if any(row.execution_map_hash != execution_map.execution_map_hash for row in intent_rows):
        raise Paper0AuthorityError("EXECUTION_MAP_HASH_MISMATCH")

    positions_raw = broker_snapshot.get("positions", [])
    if not isinstance(positions_raw, list):
        raise Paper0AuthorityError("broker positions must be a list")
    canonical_positions: dict[str, str] = {}
    for raw in positions_raw:
        if not isinstance(raw, Mapping):
            raise Paper0AuthorityError("broker position row must be a mapping")
        symbol = _required_text(raw.get("symbol"), field="broker.position.symbol").upper()
        broker_instrument_id = _required_text(
            raw.get("broker_instrument_id"),
            field="broker.position.broker_instrument_id",
        )
        matches = [
            row
            for row in execution_map.entries
            if row.broker_symbol == symbol and row.broker_instrument_id == broker_instrument_id
        ]
        if len(matches) != 1:
            raise Paper0AuthorityError("BROKER_POSITION_IDENTITY_NOT_IN_EXECUTION_MAP")
        instrument_id = matches[0].instrument_id
        if instrument_id in canonical_positions:
            raise Paper0AuthorityError("duplicate canonical position after broker identity translation")
        canonical_positions[instrument_id] = _canonical_decimal(
            raw.get("quantity"),
            field=f"broker.position[{instrument_id}].quantity",
            nonnegative=True,
        )

    open_rows = broker_snapshot.get("open_orders", [])
    recent_rows = broker_snapshot.get("recent_orders", [])
    if not isinstance(open_rows, list) or not isinstance(recent_rows, list):
        raise Paper0AuthorityError("broker open_orders/recent_orders must be lists")
    intent_by_cid = {row.client_order_id: row for row in intent_rows}
    if len(intent_by_cid) != len(intent_rows):
        raise Paper0AuthorityError("duplicate ExecutionIntentV1 client_order_id")

    open_by_cid: dict[str, Mapping[str, Any]] = {}
    for raw in open_rows:
        if not isinstance(raw, Mapping):
            raise Paper0AuthorityError("broker open order row must be a mapping")
        cid = _required_text(raw.get("client_order_id"), field="broker.open_order.client_order_id")
        if cid not in intent_by_cid:
            raise Paper0AuthorityError("UNKNOWN_OPEN_ORDER_PRESERVES_FREEZE")
        if cid in open_by_cid:
            raise Paper0AuthorityError("duplicate broker open order client_order_id")
        open_by_cid[cid] = raw

    recent_by_cid: dict[str, Mapping[str, Any]] = {}
    for raw in recent_rows:
        if not isinstance(raw, Mapping):
            raise Paper0AuthorityError("broker recent order row must be a mapping")
        cid = _required_text(raw.get("client_order_id"), field="broker.recent_order.client_order_id")
        if cid in intent_by_cid:
            if cid in recent_by_cid:
                raise Paper0AuthorityError("duplicate current broker recent order client_order_id")
            recent_by_cid[cid] = raw

    for cid, open_row in open_by_cid.items():
        recent_row = recent_by_cid.get(cid)
        if recent_row is None:
            continue
        if _required_text(open_row.get("order_id"), field="broker.open_order.order_id") != _required_text(
            recent_row.get("order_id"),
            field="broker.recent_order.order_id",
        ):
            raise Paper0AuthorityError("BROKER_OPEN_RECENT_ORDER_ID_MISMATCH")
        recent_status = _required_text(recent_row.get("status"), field="broker.recent_order.status").lower()
        if recent_status == "cancelled":
            recent_status = "canceled"
        if recent_status not in _OPEN_BROKER_STATUSES:
            raise Paper0AuthorityError("BROKER_OPEN_RECENT_STATUS_MISMATCH")

    lifecycle_events: list[BrokerLifecycleEventV1] = []
    for cid in sorted(intent_by_cid):
        intent = intent_by_cid[cid]
        raw = open_by_cid.get(cid) or recent_by_cid.get(cid)
        if raw is None:
            continue
        entry = execution_map.resolve(account_id=intent.account_id, instrument_id=intent.instrument_id)
        broker_symbol = _required_text(raw.get("symbol"), field="broker.order.symbol").upper()
        if broker_symbol != entry.broker_symbol:
            raise Paper0AuthorityError("BROKER_ORDER_SYMBOL_MISMATCH")
        broker_side = _required_text(raw.get("side"), field="broker.order.side").lower()
        if broker_side != intent.side:
            raise Paper0AuthorityError("BROKER_ORDER_SIDE_MISMATCH")
        broker_qty = _positive_int(raw.get("qty"), field="broker.order.qty")
        if broker_qty != intent.quantity:
            raise Paper0AuthorityError("BROKER_ORDER_QUANTITY_MISMATCH")
        broker_order_type = _required_text(raw.get("order_type"), field="broker.order.order_type").lower()
        if broker_order_type != PAPER_ORDER_TYPE:
            raise Paper0AuthorityError("BROKER_ORDER_TYPE_MISMATCH")
        broker_tif = _required_text(raw.get("time_in_force"), field="broker.order.time_in_force").lower()
        if broker_tif != intent.time_in_force:
            raise Paper0AuthorityError("BROKER_ORDER_TIF_MISMATCH")
        filled_quantity = _nonnegative_int(raw.get("filled_qty", 0), field="broker.order.filled_qty")
        observed_at = (
            raw.get("updated_at")
            or raw.get("submitted_at")
            or raw.get("created_at")
            or broker_snapshot.get("captured_at_utc")
        )
        lifecycle_events.append(
            BrokerLifecycleEventV1(
                sequence=len(lifecycle_events),
                client_order_id=cid,
                broker_order_id=_required_text(raw.get("order_id"), field="broker.order.order_id"),
                status=_required_text(raw.get("status"), field="broker.order.status"),
                filled_quantity=filled_quantity,
                observed_at=_required_text(observed_at, field="broker.order.observed_at"),
            )
        )

    return build_paper_live_state(
        intent_rows,
        lifecycle_events,
        positions=canonical_positions,
        cash=_required_text(broker_snapshot.get("cash"), field="broker.cash"),
        equity=_required_text(broker_snapshot.get("equity"), field="broker.equity"),
        freeze_new_risk=bool(freeze_new_risk),
        reconciliation_status=reconciliation_status,
    )


def verify_paper_live_state(state: Mapping[str, Any]) -> None:
    if str(state.get("schema", "")) != PAPER_STATE_SCHEMA:
        raise Paper0AuthorityError("invalid PAPER live-state schema")
    supplied = _sha256_hex(state.get("paper_state_hash"), field="paper_state_hash")
    body = {key: value for key, value in state.items() if key != "paper_state_hash"}
    if supplied != _content_hash(body):
        raise Paper0AuthorityError("PAPER_STATE_HASH_MISMATCH")


def _with_reconciliation_state(
    state: Mapping[str, Any],
    *,
    freeze_new_risk: bool,
    reconciliation_status: str,
    mismatches: list[str] | None = None,
) -> dict[str, Any]:
    body = {key: value for key, value in state.items() if key not in {"paper_state_hash", "reconciliation_mismatches"}}
    body["freeze_new_risk"] = bool(freeze_new_risk)
    body["reconciliation_status"] = str(reconciliation_status).upper()
    if mismatches:
        body["reconciliation_mismatches"] = list(mismatches)
    return {**body, "paper_state_hash": _content_hash(body)}


def begin_paper_restart(local_state: Mapping[str, Any]) -> dict[str, Any]:
    """Every process restart enters a frozen reconciliation-required state."""

    verify_paper_live_state(local_state)
    return _with_reconciliation_state(
        local_state,
        freeze_new_risk=True,
        reconciliation_status="RESTART_RECONCILIATION_REQUIRED",
    )


def reconcile_paper_restart(
    local_state: Mapping[str, Any],
    broker_state: Mapping[str, Any],
) -> dict[str, Any]:
    """Broker-first exact restart reconciliation; ambiguity keeps risk frozen."""

    frozen_local = begin_paper_restart(local_state)
    verify_paper_live_state(broker_state)
    comparable_keys = (
        "account_id",
        "live_rebalance_id",
        "rebalance_epoch",
        "execution_map_hash",
        "positions",
        "cash",
        "equity",
        "order_states",
        "open_orders",
        "partial_fill_residuals",
        "latest_broker_lifecycle_state",
    )
    mismatches = [
        key
        for key in comparable_keys
        if _canonical_bytes(frozen_local.get(key)) != _canonical_bytes(broker_state.get(key))
    ]
    if mismatches:
        return _with_reconciliation_state(
            broker_state,
            freeze_new_risk=True,
            reconciliation_status="RECONCILIATION_MISMATCH",
            mismatches=mismatches,
        )
    return _with_reconciliation_state(
        broker_state,
        freeze_new_risk=False,
        reconciliation_status="RECONCILED",
    )
