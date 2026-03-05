import asyncio
import schedule
import time
import subprocess
import logging
import os
import signal
import math
import json
import hashlib
import threading
import inspect
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from execution.rebalancer import PortfolioRebalancer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

PYTHON_EXECUTABLE = '.venv/Scripts/python.exe'
SCANNER_TIMEOUT_SECONDS = 300
SCANNER_TERMINATION_GRACE_SECONDS = 5
EXECUTION_MAX_SUBMIT_ATTEMPTS = 3
EXECUTION_RETRY_SLEEP_SECONDS = 0.5
EXECUTION_RECONCILIATION_MAX_POLLS = 3
EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS = 0.25
EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS = 2.0
EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS = 0.01
EXECUTION_RECONCILIATION_LOOKUP_CANCEL_GRACE_SECONDS = 0.05
EXECUTION_RECONCILIATION_QUARANTINE_PATH = os.path.join(
    "docs",
    "context",
    "e2e_evidence",
    "reconciliation_quarantine.jsonl",
)
_RETRYABLE_ERROR_TOKENS = (
    "timeout",
    "timed out",
    "connection",
    "temporarily unavailable",
    "rate limit",
    "429",
    "transient",
)
_TERMINAL_UNFILLED_STATUSES = {
    "canceled",
    "cancelled",
    "rejected",
    "expired",
    "done_for_day",
    "stopped",
    "suspended",
}


class ScannerTerminationError(RuntimeError):
    """Raised when timed-out scanner processes cannot be confirmed terminated."""


class AmbiguousExecutionError(RuntimeError):
    """Raised when execution success cannot be definitively reconciled."""


class DescendantTerminationEvidence(TypedDict):
    pid: int
    ppid: int
    name: str
    alive_after_termination: bool


class TerminationReceipt(TypedDict):
    parent_pid: int
    descendant_evidence: list[DescendantTerminationEvidence]
    parent_alive_after_termination: bool
    sterilized: bool
    termination_errors: list[str]
    proof_algorithm: str
    proof_hash: str


def _clean_optional_str(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "null", "nan"}:
        return ""
    return text


def _normalize_order_for_retry(order: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(order, dict):
        raise TypeError("order must be a dict")
    symbol = str(order.get("symbol", "")).upper().strip()
    side = str(order.get("side", "")).lower().strip()
    qty_raw = order.get("qty", 0)
    if isinstance(qty_raw, bool):
        raise ValueError(f"order has invalid qty: {qty_raw}")
    try:
        qty = int(qty_raw)
    except (TypeError, ValueError):
        raise ValueError(f"order has invalid qty: {order.get('qty')}") from None
    if not symbol:
        raise ValueError("order missing symbol")
    if side not in {"buy", "sell"}:
        raise ValueError(f"order has invalid side: {order.get('side')}")
    if qty <= 0:
        raise ValueError(f"order has invalid qty: {order.get('qty')}")

    normalized = dict(order)
    normalized["symbol"] = symbol
    normalized["side"] = side
    normalized["qty"] = qty
    order_type = _clean_optional_str(normalized.get("order_type", "")).lower() or "market"
    if order_type not in {"market", "limit"}:
        raise ValueError(f"order has invalid order_type: {order.get('order_type')}")
    normalized["order_type"] = order_type
    if order_type == "limit":
        limit_raw = normalized.get("limit_price", None)
        if isinstance(limit_raw, bool):
            raise ValueError(f"order has invalid limit_price: {limit_raw}")
        try:
            limit_price = float(limit_raw)
        except (TypeError, ValueError):
            raise ValueError(f"order has invalid limit_price: {limit_raw}") from None
        if (not math.isfinite(limit_price)) or limit_price <= 0.0:
            raise ValueError(f"order has invalid limit_price: {limit_raw}")
        normalized["limit_price"] = float(limit_price)
    else:
        normalized["limit_price"] = None
    client_order_id = _clean_optional_str(normalized.get("client_order_id", ""))
    if not client_order_id:
        client_order_id = PortfolioRebalancer._generate_client_order_id(
            symbol=symbol,
            side=side,
            qty=qty,
            order=normalized,
        )
    normalized["client_order_id"] = client_order_id
    return normalized


def _is_retryable_execution_error(error: str) -> bool:
    text = str(error).lower()
    return any(token in text for token in _RETRYABLE_ERROR_TOKENS)


def _terminal_execution_status(result: dict[str, Any]) -> str:
    status = _clean_optional_str(result.get("status", "")).lower()
    if status in _TERMINAL_UNFILLED_STATUSES:
        return status
    return ""


def _is_terminal_unfilled_execution_result(result: dict[str, Any]) -> bool:
    status = _terminal_execution_status(result)
    if not status:
        return False
    fill_summary = result.get("fill_summary", {})
    fill_summary_map = fill_summary if isinstance(fill_summary, dict) else {}
    fill_qty_raw = fill_summary_map.get("fill_qty")
    if fill_qty_raw is None:
        fill_qty_raw = result.get("filled_qty")
    if isinstance(fill_qty_raw, bool):
        return True
    try:
        fill_qty = float(fill_qty_raw)
    except (TypeError, ValueError):
        return True
    return (not math.isfinite(fill_qty)) or fill_qty <= 0.0


def _normalize_terminal_execution_result(result: dict[str, Any]) -> dict[str, Any]:
    terminal_status = _terminal_execution_status(result)
    if terminal_status == "":
        return dict(result)

    terminal_result = dict(result)
    broker_error = _clean_optional_str(terminal_result.get("error", ""))
    terminal_reason = (
        "terminal_unfilled" if _is_terminal_unfilled_execution_result(terminal_result) else "terminal_partial_fill"
    )
    terminal_result["ok"] = False
    terminal_result["status"] = terminal_status
    terminal_result["terminal_reason"] = terminal_reason
    terminal_result["error"] = f"{terminal_reason}:{terminal_status}"
    if broker_error:
        terminal_result["broker_error_raw"] = broker_error
    return terminal_result


def _recovery_result_matches_intent(
    order: dict[str, Any],
    result: dict[str, Any],
    *,
    fallback: dict[str, Any] | None = None,
    require_broker_client_order_id: bool = False,
) -> bool:
    fallback_map = fallback if isinstance(fallback, dict) else {}
    symbol = str(order.get("symbol", "")).upper().strip()
    side = str(order.get("side", "")).lower().strip()
    qty = int(order.get("qty", 0))
    expected_cid = _clean_optional_str(order.get("client_order_id", ""))
    expected_order_type = _clean_optional_str(order.get("order_type", "")).lower() or "market"
    expected_limit_raw = order.get("limit_price", None)
    expected_limit: float | None = None
    if expected_order_type == "limit":
        if isinstance(expected_limit_raw, bool):
            return False
        try:
            expected_limit = float(expected_limit_raw)
        except (TypeError, ValueError):
            return False
        if (not math.isfinite(expected_limit)) or expected_limit <= 0.0:
            return False

    recovered_symbol = str(
        _clean_optional_str(result.get("symbol", "")) or fallback_map.get("symbol", "")
    ).upper().strip()
    recovered_side = str(
        _clean_optional_str(result.get("side", "")) or fallback_map.get("side", "")
    ).lower().strip()
    broker_client_order_id = _clean_optional_str(result.get("client_order_id", ""))
    recovered_cid = _clean_optional_str(broker_client_order_id or fallback_map.get("client_order_id", ""))
    recovered_order_type = _clean_optional_str(
        _clean_optional_str(result.get("order_type", "")) or result.get("type", "") or fallback_map.get("order_type", "")
    ).lower() or "market"
    recovered_qty_raw = result.get("qty")
    if recovered_qty_raw is None:
        recovered_qty_raw = fallback_map.get("qty")
    if isinstance(recovered_qty_raw, bool):
        return False
    try:
        recovered_qty = float(recovered_qty_raw)
    except (TypeError, ValueError):
        return False
    recovered_limit_raw = result.get("limit_price", None)
    if recovered_limit_raw is None:
        recovered_limit_raw = fallback_map.get("limit_price", None)
    recovered_limit: float | None = None
    if recovered_limit_raw is not None:
        recovered_limit_text = _clean_optional_str(recovered_limit_raw).lower()
        if expected_order_type == "market" and recovered_limit_text in {"", "none", "null"}:
            recovered_limit = None
        else:
            if isinstance(recovered_limit_raw, bool):
                return False
            try:
                recovered_limit = float(recovered_limit_raw)
            except (TypeError, ValueError):
                return False
            if (not math.isfinite(recovered_limit)) or recovered_limit <= 0.0:
                return False

    base_match = recovered_symbol == symbol and recovered_side == side and abs(recovered_qty - float(qty)) <= 1e-9
    if not base_match:
        return False
    if recovered_order_type != expected_order_type:
        return False
    if expected_cid and recovered_cid and recovered_cid != expected_cid:
        return False
    if require_broker_client_order_id:
        if broker_client_order_id == "":
            return False
        if expected_cid and broker_client_order_id != expected_cid:
            return False
    if expected_order_type == "market":
        return recovered_limit is None
    return recovered_limit is not None and expected_limit is not None and abs(recovered_limit - expected_limit) <= 1e-9


def _to_positive_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0.0:
        return None
    return number


def _to_utc_execution_ts_or_none(value: Any) -> str | None:
    ts = _clean_optional_str(value)
    if ts == "":
        return None
    normalized = ts.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _normalize_execution_receipt_fields(result: dict[str, Any]) -> None:
    filled_qty = _to_positive_float_or_none(result.get("filled_qty"))
    if filled_qty is not None:
        result["filled_qty"] = filled_qty
    else:
        result.pop("filled_qty", None)

    filled_avg_price = _to_positive_float_or_none(result.get("filled_avg_price"))
    if filled_avg_price is not None:
        result["filled_avg_price"] = filled_avg_price
    else:
        result.pop("filled_avg_price", None)

    execution_ts = _to_utc_execution_ts_or_none(result.get("execution_ts", ""))
    if execution_ts is not None:
        result["execution_ts"] = execution_ts
    else:
        result.pop("execution_ts", None)


def _execution_fill_qty_within_order_bounds(order: dict[str, Any], result: dict[str, Any]) -> bool:
    intended_qty = _to_positive_float_or_none(order.get("qty"))
    filled_qty = _to_positive_float_or_none(result.get("filled_qty"))
    if intended_qty is None or filled_qty is None:
        return False
    return filled_qty <= intended_qty + 1e-9


def _ok_true_result_missing_required_broker_fields(order: dict[str, Any], result: dict[str, Any]) -> bool:
    candidate = dict(result)

    if "client_order_id" not in candidate:
        return True
    if _clean_optional_str(candidate.get("client_order_id", "")) == "":
        return True
    if "symbol" not in candidate:
        return True
    if _clean_optional_str(candidate.get("symbol", "")) == "":
        return True
    if "side" not in candidate:
        return True
    if _clean_optional_str(candidate.get("side", "")) == "":
        return True
    if "qty" not in candidate:
        return True

    expected_order_type = _clean_optional_str(order.get("order_type", "")).lower() or "market"
    if expected_order_type == "limit":
        if "order_type" not in candidate and "type" not in candidate:
            return True
        result_order_type = _clean_optional_str(candidate.get("order_type", "") or candidate.get("type", "")).lower()
        if result_order_type == "":
            return True
        if "limit_price" not in candidate:
            return True

    _normalize_execution_receipt_fields(candidate)
    if _to_positive_float_or_none(candidate.get("filled_qty")) is None:
        return True
    if _to_positive_float_or_none(candidate.get("filled_avg_price")) is None:
        return True
    if _clean_optional_str(candidate.get("execution_ts", "")) == "":
        return True
    if not _execution_fill_qty_within_order_bounds(order, candidate):
        return True
    return False


def _poll_lookup_with_timeout(
    lookup: Any,
    *,
    client_order_id: str,
    timeout_seconds: float,
) -> tuple[Any, str]:
    supports_cancel_event = False
    try:
        signature = inspect.signature(lookup)
        if any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        ):
            supports_cancel_event = True
        else:
            cancel_parameter = signature.parameters.get("cancel_event")
            supports_cancel_event = cancel_parameter is not None and cancel_parameter.kind in {
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            }
    except (TypeError, ValueError):
        supports_cancel_event = False

    cancel_event = threading.Event()

    def _call_lookup() -> Any:
        if supports_cancel_event:
            return lookup(client_order_id, cancel_event=cancel_event)
        return lookup(client_order_id)

    effective_timeout = max(float(timeout_seconds), float(EXECUTION_RECONCILIATION_LOOKUP_MIN_TIMEOUT_SECONDS))

    state: dict[str, Any] = {}

    def _invoke_lookup() -> None:
        try:
            state["result"] = _call_lookup()
        except asyncio.CancelledError:
            state["error"] = "lookup_cancelled"
        except Exception as exc:
            state["error"] = f"lookup_exception:{exc.__class__.__name__}:{exc}"

    thread = threading.Thread(target=_invoke_lookup, daemon=True)
    thread.start()
    thread.join(effective_timeout)

    if thread.is_alive():
        if supports_cancel_event:
            cancel_event.set()
            thread.join(max(float(EXECUTION_RECONCILIATION_LOOKUP_CANCEL_GRACE_SECONDS), 0.0))
        if "error" in state and not thread.is_alive():
            return None, str(state["error"])
        if thread.is_alive():
            return None, f"lookup_timeout:{effective_timeout:.3f}s:uncooperative"
        return None, f"lookup_timeout:{effective_timeout:.3f}s"
    if "error" in state:
        return None, str(state["error"])
    return state.get("result"), ""


def _lookup_issue_requires_quarantine(lookup_issue: str) -> bool:
    issue = _clean_optional_str(lookup_issue)
    if issue == "lookup_cancelled":
        return True
    return issue.startswith("lookup_timeout:") or issue.startswith("lookup_exception:")


def _lookup_issue_priority(lookup_issue: str) -> int:
    issue = _clean_optional_str(lookup_issue)
    if issue.startswith("lookup_timeout:") and issue.endswith(":uncooperative"):
        return 4
    if issue == "lookup_cancelled":
        return 3
    if issue.startswith("lookup_timeout:"):
        return 2
    if issue.startswith("lookup_exception:"):
        return 1
    return 0


def _prefer_lookup_issue(current_issue: str, candidate_issue: str) -> str:
    if _lookup_issue_priority(candidate_issue) >= _lookup_issue_priority(current_issue):
        return candidate_issue
    return current_issue


def _lookup_issue_is_uncooperative_timeout(lookup_issue: str) -> bool:
    issue = _clean_optional_str(lookup_issue)
    return issue.startswith("lookup_timeout:") and issue.endswith(":uncooperative")


def _fsync_parent_dir_if_possible(path: Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _acquire_quarantine_lock(lock_handle: Any, *, timeout_seconds: float = 2.0) -> None:
    deadline = time.monotonic() + max(float(timeout_seconds), 0.0)
    while True:
        try:
            if os.name == "nt":
                lock_handle.seek(0)
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise TimeoutError("reconciliation_quarantine_lock_timeout")
            time.sleep(0.01)


def _release_quarantine_lock(lock_handle: Any) -> None:
    try:
        if os.name == "nt":
            lock_handle.seek(0)
            msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        return


def _append_reconciliation_quarantine_entry(
    *,
    client_order_id: str,
    order: dict[str, Any],
    reconciliation_issue: str,
    attempt: int,
    source: str,
) -> str:
    path = Path(str(EXECUTION_RECONCILIATION_QUARANTINE_PATH))
    lock_path = path.with_suffix(f"{path.suffix}.lock")
    path_preexists = path.exists()
    payload = {
        "schema_version": 1,
        "quarantined_at_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "client_order_id": _clean_optional_str(client_order_id),
        "reconciliation_issue": _clean_optional_str(reconciliation_issue),
        "reconciliation_issue_family": _clean_optional_str(reconciliation_issue).split(":", 1)[0],
        "attempt": int(attempt),
        "source": _clean_optional_str(source),
        "order": {
            "symbol": _clean_optional_str(order.get("symbol", "")).upper(),
            "side": _clean_optional_str(order.get("side", "")).lower(),
            "qty": order.get("qty"),
            "order_type": _clean_optional_str(order.get("order_type", "")).lower() or "market",
            "limit_price": order.get("limit_price"),
        },
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8") + b"\n"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as lock_handle:
            _acquire_quarantine_lock(lock_handle)
            try:
                fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY)
                try:
                    os.write(fd, encoded)
                    os.fsync(fd)
                finally:
                    os.close(fd)
            finally:
                _release_quarantine_lock(lock_handle)
        if not path_preexists:
            _fsync_parent_dir_if_possible(path.parent)
        return ""
    except Exception as exc:
        logging.error(
            "Failed to append reconciliation quarantine entry for client_order_id=%s: %s",
            client_order_id,
            exc,
        )
        return f"quarantine_write_exception:{exc.__class__.__name__}:{exc}"


def _read_quarantine_jsonl_safe(path: Path) -> list[dict[str, Any]]:
    """
    Read quarantine JSONL file with fail-closed UTF-8 decode error handling.

    Uses errors='replace' to convert malformed UTF-8 bytes to U+FFFD replacement
    character instead of wedging with UnicodeDecodeError. This ensures that
    ingestion/replay boundaries remain operational even when external sources
    (broker responses, process snapshots) introduce corrupted data.

    Returns:
        List of parsed JSON rows. Rows with invalid JSON are skipped with logging.
    """
    if not path.exists():
        return []
    try:
        raw_text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        logging.error(
            "Failed to read quarantine file at %s: %s",
            path,
            exc,
        )
        return []
    rows: list[dict[str, Any]] = []
    for line_num, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError as exc:
            logging.warning(
                "Skipping malformed JSON at %s line %d: %s",
                path,
                line_num,
                exc,
            )
            continue
    return rows


def _augment_reconciliation_issue_with_quarantine(
    *,
    client_order_id: str,
    order: dict[str, Any],
    reconciliation_issue: str,
    attempt: int,
    source: str,
) -> str:
    if not _lookup_issue_requires_quarantine(reconciliation_issue):
        return reconciliation_issue
    quarantine_issue = _append_reconciliation_quarantine_entry(
        client_order_id=client_order_id,
        order=order,
        reconciliation_issue=reconciliation_issue,
        attempt=attempt,
        source=source,
    )
    if quarantine_issue == "":
        return reconciliation_issue
    if reconciliation_issue:
        return f"{reconciliation_issue}|{quarantine_issue}"
    return quarantine_issue


def _poll_reconciliation_receipt(
    rebalancer: PortfolioRebalancer,
    *,
    order: dict[str, Any],
    client_order_id: str,
    max_polls: int | None = None,
    poll_sleep_seconds: float | None = None,
    lookup_timeout_seconds: float | None = None,
) -> tuple[dict[str, Any] | None, str]:
    broker = getattr(rebalancer, "broker", None)
    lookup = getattr(broker, "get_order_by_client_order_id", None)
    if not callable(lookup):
        return None, "lookup_unavailable"

    max_polls_value = EXECUTION_RECONCILIATION_MAX_POLLS if max_polls is None else max_polls
    try:
        budget = int(max_polls_value)
    except (TypeError, ValueError):
        budget = 1
    budget = max(0, budget)
    if budget == 0:
        return None, "reconciliation_poll_budget_zero"

    poll_sleep_value = (
        EXECUTION_RECONCILIATION_POLL_SLEEP_SECONDS if poll_sleep_seconds is None else poll_sleep_seconds
    )
    try:
        sleep_seconds = float(poll_sleep_value)
    except (TypeError, ValueError):
        sleep_seconds = 0.0

    lookup_timeout_value = (
        EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS
        if lookup_timeout_seconds is None
        else lookup_timeout_seconds
    )
    try:
        timeout_seconds = float(lookup_timeout_value)
    except (TypeError, ValueError):
        timeout_seconds = float(EXECUTION_RECONCILIATION_LOOKUP_TIMEOUT_SECONDS)
    timeout_seconds = max(0.0, timeout_seconds)

    last_issue = ""
    lookup_issue_sticky = ""
    for poll_idx in range(budget):
        recovered, lookup_issue = _poll_lookup_with_timeout(
            lookup,
            client_order_id=client_order_id,
            timeout_seconds=timeout_seconds,
        )
        if lookup_issue:
            if _lookup_issue_requires_quarantine(lookup_issue):
                lookup_issue_sticky = _prefer_lookup_issue(lookup_issue_sticky, lookup_issue)
            last_issue = lookup_issue
            logging.warning(
                "Reconciliation lookup issue for client_order_id=%s poll=%d/%d: %s",
                client_order_id,
                poll_idx + 1,
                budget,
                lookup_issue,
            )
            if _lookup_issue_is_uncooperative_timeout(lookup_issue):
                return None, (lookup_issue_sticky or lookup_issue)
        if isinstance(recovered, dict):
            receipt = dict(recovered)
            receipt["ok"] = True
            broker_client_order_id = _clean_optional_str(receipt.get("client_order_id", ""))
            if broker_client_order_id:
                receipt["client_order_id"] = broker_client_order_id
            _normalize_execution_receipt_fields(receipt)
            terminal_status = _terminal_execution_status(receipt)
            if terminal_status:
                return _normalize_terminal_execution_result(receipt), ""
            if not _ok_true_result_missing_required_broker_fields(order, receipt):
                return receipt, ""
            if lookup_issue_sticky == "":
                last_issue = "non_authoritative_reconciliation_receipt"
        elif lookup_issue == "":
            if lookup_issue_sticky == "":
                last_issue = "reconciliation_receipt_unavailable"
        if poll_idx + 1 < budget and sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return None, (lookup_issue_sticky or last_issue or "reconciliation_receipt_unavailable")


def _classify_broker_exception(exc: Exception) -> str:
    """
    Phase 32 Step 4: Binary exception taxonomy for broker execution failures.

    Classifies broker exceptions into two canonical categories:
    - TRANSIENT: Retryable network/infrastructure failures (retry with backoff)
    - TERMINAL: Hard rejections that will never succeed on retry (fail-closed immediately)

    Returns:
        "TRANSIENT" or "TERMINAL"
    """
    exc_type = type(exc).__name__
    exc_message = str(exc).lower()

    # TERMINAL: Validation and business logic rejections (infinite retry is catastrophic)
    terminal_indicators = [
        # Validation errors
        "valueerror",
        "typeerror",
        "keyerror",
        # Broker rejections
        "insufficient buying power",
        "insufficient funds",
        "insufficient margin",
        "invalid symbol",
        "invalid ticker",
        "symbol not found",
        "not tradable",
        "market closed",
        "outside market hours",
        "invalid order type",
        "invalid side",
        "invalid quantity",
        "qty must be positive",
        "price must be positive",
        # Authorization/authentication errors
        "unauthorized",
        "forbidden",
        "authentication failed",
        "invalid api key",
        "access denied",
        # HTTP 4xx client errors (except 429 rate limit which is transient)
        "400 bad request",
        "401 unauthorized",
        "403 forbidden",
        "404 not found",
    ]

    for indicator in terminal_indicators:
        if indicator in exc_type.lower() or indicator in exc_message:
            return "TERMINAL"

    # TRANSIENT: Network/infrastructure failures (retry is safe and expected)
    transient_indicators = [
        # Connection errors
        "connectionerror",
        "connectionreseterror",
        "brokenpipeerror",
        "connectionrefusederror",
        "connectionabortederror",
        # Timeout errors
        "timeouterror",
        "timeout",
        "timed out",
        # HTTP 5xx server errors
        "500 internal server error",
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",
        # Rate limiting (transient, back off and retry)
        "429 too many requests",
        "rate limit exceeded",
        "throttled",
        # Network issues
        "network unreachable",
        "host unreachable",
        "connection reset by peer",
        "broken pipe",
    ]

    for indicator in transient_indicators:
        if indicator in exc_type.lower() or indicator in exc_message:
            return "TRANSIENT"

    # Default: treat unknown exceptions as TRANSIENT to preserve existing retry behavior
    # (fail-safe: retry unknown errors rather than dropping them)
    return "TRANSIENT"


def _build_retry_exhausted_result(
    *,
    client_order_id: str,
    attempt: int,
    last_error: str,
    canonical_reason: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "error": "retry_exhausted",
        "canonical_reason": _clean_optional_str(canonical_reason) or "transient_error:retry_exhausted",
        "exception_class": "TRANSIENT",
        "client_order_id": str(client_order_id),
        "attempt": int(attempt),
    }
    cleaned_last_error = _clean_optional_str(last_error)
    if cleaned_last_error:
        result["last_error"] = cleaned_last_error
    return result


def _build_failed_rejected_result(
    *,
    client_order_id: str,
    attempt: int,
    rejection_reason: str,
    canonical_reason: str,
    last_error: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "error": "FAILED_REJECTED",
        "rejection_reason": _clean_optional_str(rejection_reason),
        "canonical_reason": _clean_optional_str(canonical_reason) or "terminal_exception:unknown",
        "exception_class": "TERMINAL",
        "client_order_id": str(client_order_id),
        "attempt": int(attempt),
    }
    cleaned_last_error = _clean_optional_str(last_error)
    if cleaned_last_error:
        result["last_error"] = cleaned_last_error
    return result


def execute_orders_with_idempotent_retry(
    rebalancer: PortfolioRebalancer,
    orders: list[dict[str, Any]],
    *,
    max_attempts: int = EXECUTION_MAX_SUBMIT_ATTEMPTS,
    retry_sleep_seconds: float = EXECUTION_RETRY_SLEEP_SECONDS,
) -> list[dict[str, Any]]:
    """
    Orchestrator-level order execution with retry semantics and static client_order_id.

    Contract:
      - keep client_order_id stable across retries for each order intent.
      - retry only retryable submission errors.
      - accept "already exists" recovery as success only when payload parity matches
        symbol/side/qty intent.
    """
    if int(max_attempts) < 1:
        raise ValueError("max_attempts must be >= 1")
    if not orders:
        return []

    ordered_cids: list[str] = []
    pending_by_cid: dict[str, dict[str, Any]] = {}
    seen_symbols: set[str] = set()
    for raw in orders:
        if not isinstance(raw, dict):
            raise TypeError("order must be a dict")
        seed_cid = _clean_optional_str(raw.get("client_order_id", ""))
        seed_trade_day = _clean_optional_str(raw.get("trade_day", ""))
        if not seed_cid and not seed_trade_day:
            raise ValueError("order missing id seed: provide client_order_id or trade_day")
        normalized = _normalize_order_for_retry(raw)
        cid = str(normalized["client_order_id"])
        if cid in pending_by_cid:
            raise ValueError(f"Duplicate client_order_id in initial order set: {cid}")
        symbol = str(normalized["symbol"]).upper().strip()
        if symbol in seen_symbols:
            raise ValueError(f"Duplicate symbol in initial order set: {symbol}")
        seen_symbols.add(symbol)
        pending_by_cid[cid] = normalized
        ordered_cids.append(cid)

    final_by_cid: dict[str, dict[str, Any]] = {}
    attempt = 0
    while pending_by_cid and attempt < int(max_attempts):
        attempt += 1
        batch_orders = list(pending_by_cid.values())
        try:
            raw_batch_results = rebalancer.execute_orders(batch_orders, dry_run=False)
        except Exception as exc:
            # Phase 32 Step 4: Binary exception taxonomy (TRANSIENT vs TERMINAL)
            exception_class = _classify_broker_exception(exc)
            batch_exception = f"batch_exception:{exc.__class__.__name__}"
            exception_message = str(exc)
            canonical_exception_reason = f"{exception_class.lower()}_exception:{exc.__class__.__name__}"

            if exception_class == "TERMINAL":
                # TERMINAL errors: Instant bypass of retry loop, fail-closed immediately
                # Examples: "Insufficient Buying Power", "Invalid Symbol", validation errors
                # Retrying these would freeze capital allocation loop
                logging.error(
                    "Execution batch classified TERMINAL (%s): %s",
                    canonical_exception_reason,
                    exception_message,
                )
                for cid, order in pending_by_cid.items():
                    final_by_cid[cid] = {
                        "order": order,
                        "result": _build_failed_rejected_result(
                            client_order_id=cid,
                            attempt=attempt,
                            rejection_reason=exception_message,
                            canonical_reason=canonical_exception_reason,
                            last_error=batch_exception,
                        ),
                    }
                # Release orchestrator lock immediately - other orders can process
                pending_by_cid = {}
                break

            # TRANSIENT errors: Bounded retry loop (existing behavior)
            # Examples: "Connection Reset by Peer", "503 Service Unavailable"
            if attempt < int(max_attempts):
                if float(retry_sleep_seconds) > 0:
                    time.sleep(float(retry_sleep_seconds))
                continue

            # Retry exhausted for TRANSIENT error
            for cid, order in pending_by_cid.items():
                final_by_cid[cid] = {
                    "order": order,
                    "result": _build_retry_exhausted_result(
                        client_order_id=cid,
                        attempt=attempt,
                        last_error=batch_exception,
                        canonical_reason=canonical_exception_reason,
                    ),
                }
            pending_by_cid = {}
            break
        batch_results = raw_batch_results if isinstance(raw_batch_results, list) else []
        expected_cids = set(pending_by_cid.keys())
        observed_cids: set[str] = set()
        cid_counts: dict[str, int] = {}
        for row in batch_results:
            if not isinstance(row, dict):
                continue
            raw_order = row.get("order", {})
            raw_result = row.get("result", {})
            if not isinstance(raw_result, dict):
                continue
            order_map = raw_order if isinstance(raw_order, dict) else {}
            candidate_cid = (
                _clean_optional_str(raw_result.get("client_order_id", ""))
                or _clean_optional_str(order_map.get("client_order_id", ""))
            )
            if candidate_cid in expected_cids:
                cid_counts[candidate_cid] = cid_counts.get(candidate_cid, 0) + 1
        duplicate_output_cids: set[str] = {cid for cid, count in cid_counts.items() if count > 1}

        next_pending: dict[str, dict[str, Any]] = {}
        for row in batch_results:
            if not isinstance(row, dict):
                continue
            raw_order = row.get("order", {})
            raw_result = row.get("result", {})
            if not isinstance(raw_result, dict):
                continue
            order_map = raw_order if isinstance(raw_order, dict) else {}
            result = dict(raw_result)
            raw_ok = raw_result.get("ok")

            candidate_cid = (
                _clean_optional_str(result.get("client_order_id", ""))
                or _clean_optional_str(order_map.get("client_order_id", ""))
            )
            if candidate_cid not in expected_cids:
                # Ignore malformed/unknown rows and reconcile via missing CID guard below.
                continue
            if candidate_cid in duplicate_output_cids:
                observed_cids.add(candidate_cid)
                continue
            if candidate_cid in observed_cids:
                duplicate_output_cids.add(candidate_cid)
                continue
            observed_cids.add(candidate_cid)
            cid = candidate_cid
            order = pending_by_cid[cid]
            result["attempt"] = attempt
            broker_client_order_id = _clean_optional_str(result.get("client_order_id", ""))
            if broker_client_order_id:
                result["client_order_id"] = broker_client_order_id
            else:
                result.pop("client_order_id", None)

            terminal_status = _terminal_execution_status(result)
            if terminal_status:
                terminal_result = _normalize_terminal_execution_result(result)
                terminal_result.setdefault("client_order_id", cid)
                final_by_cid[cid] = {"order": order, "result": terminal_result}
                continue

            if not isinstance(raw_ok, bool):
                final_by_cid[cid] = {
                    "order": order,
                    "result": {
                        "ok": False,
                        "error": "malformed_ok_flag",
                        "client_order_id": cid,
                        "attempt": attempt,
                    },
                }
                continue

            if raw_ok is True:
                result_for_match = result
                require_broker_client_order_id = bool(result.get("recovered"))
                _normalize_execution_receipt_fields(result_for_match)
                if _ok_true_result_missing_required_broker_fields(order, raw_result):
                    reconciled, reconciliation_issue = _poll_reconciliation_receipt(
                        rebalancer,
                        order=order,
                        client_order_id=cid,
                    )
                    if reconciled is None:
                        reconciliation_issue = _augment_reconciliation_issue_with_quarantine(
                            client_order_id=cid,
                            order=order,
                            reconciliation_issue=reconciliation_issue,
                            attempt=attempt,
                            source="ok_true_missing_required_fields",
                        )
                        raise AmbiguousExecutionError(
                            f"ambiguous execution receipt for client_order_id={cid}: "
                            "ok=True response missing required fields "
                            "(filled_qty, filled_avg_price, execution_ts); "
                            f"reconciliation_issue={reconciliation_issue}"
                        )
                    reconciled["attempt"] = attempt
                    result_for_match = reconciled
                    require_broker_client_order_id = True

                if not _recovery_result_matches_intent(
                    order,
                    result_for_match,
                    require_broker_client_order_id=require_broker_client_order_id,
                ):
                    mismatch_error = "recovery_mismatch" if bool(result_for_match.get("recovered")) else "intent_mismatch"
                    final_by_cid[cid] = {
                        "order": order,
                        "result": {
                            "ok": False,
                            "error": mismatch_error,
                            "client_order_id": cid,
                            "attempt": attempt,
                        },
                    }
                    continue
                final_result = dict(result_for_match)
                final_result.setdefault("client_order_id", cid)
                final_by_cid[cid] = {"order": order, "result": final_result}
                continue

            raw_error_text = _clean_optional_str(result.get("error", ""))
            error_text = raw_error_text.lower()
            row_exception_class = _classify_broker_exception(RuntimeError(raw_error_text))
            if "already exists" in error_text:
                if _recovery_result_matches_intent(
                    order,
                    result,
                    fallback=order_map,
                    require_broker_client_order_id=True,
                ):
                    recovered = dict(result)
                    recovered["ok"] = True
                    recovered["recovered"] = True
                    recovered.setdefault("status", "accepted")
                    _normalize_execution_receipt_fields(recovered)
                    if _ok_true_result_missing_required_broker_fields(order, recovered):
                        reconciled, reconciliation_issue = _poll_reconciliation_receipt(
                            rebalancer,
                            order=order,
                            client_order_id=cid,
                        )
                        if reconciled is None:
                            reconciliation_issue = _augment_reconciliation_issue_with_quarantine(
                                client_order_id=cid,
                                order=order,
                                reconciliation_issue=reconciliation_issue,
                                attempt=attempt,
                                source="already_exists_missing_required_fields",
                            )
                            raise AmbiguousExecutionError(
                                f"ambiguous execution receipt for client_order_id={cid}: "
                                "already-exists recovery missing required fields "
                                "(filled_qty, filled_avg_price, execution_ts); "
                                f"reconciliation_issue={reconciliation_issue}"
                            )
                        reconciled["attempt"] = attempt
                        if not _recovery_result_matches_intent(
                            order,
                            reconciled,
                            require_broker_client_order_id=True,
                        ):
                            final_by_cid[cid] = {
                                "order": order,
                                "result": {
                                    "ok": False,
                                    "error": "recovery_mismatch",
                                    "client_order_id": cid,
                                    "attempt": attempt,
                                },
                            }
                            continue
                        reconciled_result = dict(reconciled)
                        reconciled_result.setdefault("client_order_id", cid)
                        final_by_cid[cid] = {"order": order, "result": reconciled_result}
                        continue
                    recovered_result = dict(recovered)
                    recovered_result.setdefault("client_order_id", cid)
                    final_by_cid[cid] = {"order": order, "result": recovered_result}
                else:
                    final_by_cid[cid] = {
                        "order": order,
                        "result": {
                            "ok": False,
                            "error": "recovery_mismatch",
                            "client_order_id": cid,
                            "attempt": attempt,
                        },
                    }
                continue

            if row_exception_class == "TERMINAL":
                canonical_exception_reason = "terminal_error:non_retryable_broker_result"
                final_by_cid[cid] = {
                    "order": order,
                    "result": _build_failed_rejected_result(
                        client_order_id=cid,
                        attempt=attempt,
                        rejection_reason=raw_error_text or "non_retryable_broker_result",
                        canonical_reason=canonical_exception_reason,
                        last_error=raw_error_text,
                    ),
                }
                continue

            if _is_retryable_execution_error(error_text):
                if attempt < int(max_attempts):
                    next_pending[cid] = order
                else:
                    final_by_cid[cid] = {
                        "order": order,
                        "result": _build_retry_exhausted_result(
                            client_order_id=cid,
                            attempt=attempt,
                            last_error=raw_error_text or error_text,
                            canonical_reason="transient_error:retryable_broker_result",
                        ),
                    }
                continue

            final_result = dict(result)
            final_result.setdefault("client_order_id", cid)
            final_by_cid[cid] = {"order": order, "result": final_result}

        for cid in duplicate_output_cids:
            if cid not in pending_by_cid:
                continue
            order = pending_by_cid[cid]
            next_pending.pop(cid, None)
            final_by_cid[cid] = {
                "order": order,
                "result": {
                    "ok": False,
                    "error": "duplicate_batch_result_cid",
                    "client_order_id": cid,
                    "attempt": attempt,
                },
            }

        missing_cids = expected_cids - observed_cids
        for cid in missing_cids:
            order = pending_by_cid[cid]
            if attempt < int(max_attempts):
                next_pending[cid] = order
            else:
                final_by_cid[cid] = {
                    "order": order,
                    "result": {
                        "ok": False,
                        "error": "batch_result_missing",
                        "client_order_id": cid,
                        "attempt": attempt,
                    },
                }

        pending_by_cid = next_pending
        if pending_by_cid and float(retry_sleep_seconds) > 0:
            time.sleep(float(retry_sleep_seconds))

    for cid, order in pending_by_cid.items():
        final_by_cid[cid] = {
            "order": order,
            "result": _build_retry_exhausted_result(
                client_order_id=cid,
                attempt=int(max_attempts),
                last_error="pending_orders_after_max_attempts",
                canonical_reason="transient_error:pending_orders_after_max_attempts",
            ),
        }

    return [final_by_cid[cid] for cid in ordered_cids if cid in final_by_cid]


def _spawn_scanner_process(script_path: str) -> subprocess.Popen[str]:
    popen_kwargs: dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
    }
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    else:
        popen_kwargs["start_new_session"] = True
    return subprocess.Popen([PYTHON_EXECUTABLE, script_path], **popen_kwargs)


def _wait_for_process_exit(proc: subprocess.Popen[str], timeout_seconds: float) -> bool:
    deadline = time.time() + max(0.0, float(timeout_seconds))
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.05)
    return proc.poll() is not None


def _collect_process_snapshot() -> list[dict[str, Any]]:
    if os.name == "nt":
        query = (
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,ParentProcessId,Name | "
            "ConvertTo-Json -Compress"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", query],
            capture_output=True,
            text=True,
            timeout=max(1, int(SCANNER_TERMINATION_GRACE_SECONDS)),
        )
        if int(getattr(result, "returncode", 1)) != 0:
            stderr = _clean_optional_str(getattr(result, "stderr", ""))
            raise RuntimeError(f"process snapshot query failed (rc={result.returncode}): {stderr}")
        raw = _clean_optional_str(getattr(result, "stdout", ""))
        if not raw:
            return []
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid process snapshot payload: {exc}") from exc
        rows = payload if isinstance(payload, list) else [payload]
        snapshot: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            try:
                pid = int(row.get("ProcessId"))
                ppid = int(row.get("ParentProcessId", 0))
            except (TypeError, ValueError):
                continue
            if pid <= 0:
                continue
            snapshot.append(
                {
                    "pid": pid,
                    "ppid": ppid,
                    "name": _clean_optional_str(row.get("Name", "")),
                }
            )
        return snapshot

    result = subprocess.run(
        ["ps", "-eo", "pid=,ppid=,comm="],
        capture_output=True,
        text=True,
        timeout=max(1, int(SCANNER_TERMINATION_GRACE_SECONDS)),
    )
    if int(getattr(result, "returncode", 1)) != 0:
        stderr = _clean_optional_str(getattr(result, "stderr", ""))
        raise RuntimeError(f"process snapshot query failed (rc={result.returncode}): {stderr}")
    snapshot = []
    for line in str(getattr(result, "stdout", "")).splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        name = parts[2] if len(parts) >= 3 else ""
        snapshot.append({"pid": pid, "ppid": ppid, "name": _clean_optional_str(name)})
    return snapshot


def _capture_process_snapshot(
    stage: str,
    termination_errors: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    try:
        return _collect_process_snapshot(), True
    except Exception as exc:
        logging.error(f"Failed to capture process snapshot ({stage}): {exc}")
        termination_errors.append(f"{stage}_snapshot_unavailable")
        return [], False


def _find_descendant_process_rows(parent_pid: int, process_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    children_by_parent: dict[int, list[dict[str, Any]]] = {}
    for row in process_rows:
        try:
            pid = int(row.get("pid", -1))
            ppid = int(row.get("ppid", -1))
        except (TypeError, ValueError):
            continue
        if pid <= 0:
            continue
        children_by_parent.setdefault(ppid, []).append(
            {
                "pid": pid,
                "ppid": ppid,
                "name": _clean_optional_str(row.get("name", "")),
            }
        )
    for children in children_by_parent.values():
        children.sort(key=lambda item: (int(item["pid"]), int(item["ppid"]), str(item["name"])))
    descendants: list[dict[str, Any]] = []
    frontier: list[int] = [int(parent_pid)]
    seen: set[int] = set()
    while frontier:
        current = frontier.pop(0)
        for child in children_by_parent.get(current, []):
            pid = int(child["pid"])
            if pid in seen:
                continue
            seen.add(pid)
            descendants.append(child)
            frontier.append(pid)
    descendants.sort(key=lambda item: (int(item["pid"]), int(item["ppid"]), str(item["name"])))
    return descendants


def _build_termination_receipt(
    *,
    parent_pid: int,
    descendant_evidence: list[DescendantTerminationEvidence],
    parent_alive_after_termination: bool,
    sterilized: bool,
    termination_errors: list[str],
) -> TerminationReceipt:
    stable_descendant_evidence = sorted(
        descendant_evidence,
        key=lambda item: (int(item["pid"]), int(item["ppid"]), str(item["name"])),
    )
    stable_errors = sorted({_clean_optional_str(err) for err in termination_errors if _clean_optional_str(err)})
    canonical_payload: dict[str, Any] = {
        "parent_pid": int(parent_pid),
        "descendant_evidence": stable_descendant_evidence,
        "parent_alive_after_termination": bool(parent_alive_after_termination),
        "sterilized": bool(sterilized),
        "termination_errors": stable_errors,
    }
    proof_hash = hashlib.sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return {
        **canonical_payload,
        "proof_algorithm": "sha256",
        "proof_hash": proof_hash,
    }


def _terminate_process_tree(proc: subprocess.Popen[str]) -> TerminationReceipt:
    parent_pid = int(getattr(proc, "pid", -1))
    termination_errors: list[str] = []
    pre_snapshot, pre_snapshot_ok = _capture_process_snapshot("pre", termination_errors)
    parent_seen_pre = pre_snapshot_ok and any(int(row.get("pid", -1)) == parent_pid for row in pre_snapshot)
    if not parent_seen_pre:
        termination_errors.append("parent_not_observed_pre_termination")
    pre_descendants = _find_descendant_process_rows(parent_pid, pre_snapshot) if parent_seen_pre else []

    if proc.poll() is None:
        if os.name == "nt":
            try:
                kill_result = subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    capture_output=True,
                    text=True,
                    timeout=max(1, int(SCANNER_TERMINATION_GRACE_SECONDS)),
                )
                if int(getattr(kill_result, "returncode", 1)) != 0:
                    stderr = _clean_optional_str(getattr(kill_result, "stderr", ""))
                    message = f"taskkill failed (rc={kill_result.returncode}): {stderr}"
                    logging.error(message)
                    termination_errors.append(f"taskkill_nonzero_rc_{int(kill_result.returncode)}")
            except Exception as exc:
                message = f"Failed to execute taskkill for pid={proc.pid}: {exc}"
                logging.error(message)
                termination_errors.append("taskkill_execution_failed")

            if proc.poll() is None and not _wait_for_process_exit(proc, SCANNER_TERMINATION_GRACE_SECONDS):
                try:
                    proc.kill()
                except Exception as exc:
                    message = f"Process pid={proc.pid} still alive after taskkill; fallback kill failed: {exc}"
                    logging.error(message)
                    termination_errors.append("fallback_kill_failed")
                else:
                    if not _wait_for_process_exit(proc, 1.0):
                        message = f"Process pid={proc.pid} still alive after taskkill fallback kill"
                        logging.error(message)
                        termination_errors.append("fallback_kill_no_exit")
        else:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except Exception as exc:
                message = f"Failed to send SIGTERM to process group {proc.pid}: {exc}"
                logging.error(message)
                termination_errors.append("sigterm_failed")

            if proc.poll() is None and not _wait_for_process_exit(proc, SCANNER_TERMINATION_GRACE_SECONDS):
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except Exception as exc:
                    message = f"Failed to send SIGKILL to process group {proc.pid}: {exc}"
                    logging.error(message)
                    termination_errors.append("sigkill_failed")
                if proc.poll() is None and not _wait_for_process_exit(proc, 1.0):
                    message = f"Process group {proc.pid} still alive after SIGKILL"
                    logging.error(message)
                    termination_errors.append("sigkill_no_exit")

    post_snapshot, post_snapshot_ok = _capture_process_snapshot("post", termination_errors)
    post_pids = {int(row.get("pid", -1)) for row in post_snapshot if int(row.get("pid", -1)) > 0}
    parent_alive_after = (parent_pid in post_pids) if post_snapshot_ok else (proc.poll() is None)
    descendant_evidence: list[DescendantTerminationEvidence] = []
    for row in pre_descendants:
        pid = int(row["pid"])
        descendant_evidence.append(
            {
                "pid": pid,
                "ppid": int(row["ppid"]),
                "name": _clean_optional_str(row.get("name", "")),
                "alive_after_termination": (pid in post_pids) if post_snapshot_ok else True,
            }
        )
    proof_ready = pre_snapshot_ok and post_snapshot_ok and parent_seen_pre
    descendants_cleared = proof_ready and all(not row["alive_after_termination"] for row in descendant_evidence)
    sterilized = proof_ready and (not parent_alive_after) and descendants_cleared
    return _build_termination_receipt(
        parent_pid=parent_pid,
        descendant_evidence=descendant_evidence,
        parent_alive_after_termination=parent_alive_after,
        sterilized=sterilized,
        termination_errors=termination_errors,
    )


def _run_scanner_step(step_name: str, script_path: str, stderr_label: str) -> None:
    proc = _spawn_scanner_process(script_path)
    try:
        stdout, stderr = proc.communicate(timeout=SCANNER_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        try:
            receipt = _terminate_process_tree(proc)
        except Exception as term_exc:
            raise ScannerTerminationError(
                f"{step_name} timed out and process tree termination could not be confirmed: {term_exc}"
            ) from term_exc
        if not bool(receipt.get("sterilized", False)):
            raise ScannerTerminationError(
                f"{step_name} timed out and process tree sterilization proof failed "
                f"(parent_pid={receipt.get('parent_pid')}, proof={receipt.get('proof_hash')})"
            )
        raise subprocess.TimeoutExpired(cmd=[PYTHON_EXECUTABLE, script_path], timeout=SCANNER_TIMEOUT_SECONDS) from exc

    if stdout:
        print(stdout)
    if stderr:
        logging.error(f"{stderr_label}: {stderr}")
    if int(proc.returncode or 0) != 0:
        raise RuntimeError(f"{step_name} failed with return code {proc.returncode}")

def run_scanners():
    logging.info("Initiating The Alpha Sovereign End-of-Week Scan...")
    
    logging.info("--- Step 1: Running Alpha Quad Scanner ---")
    _run_scanner_step(
        step_name="Alpha Quad Scanner",
        script_path='scripts/alpha_quad_scanner.py',
        stderr_label="Alpha Quad Errors",
    )
        
    logging.info("--- Step 2: Running Fourier Expected Yield Barrier ---")
    _run_scanner_step(
        step_name="Fourier Expected Yield Barrier",
        script_path='scripts/fourier_opportunity_gate.py',
        stderr_label="Fourier Scanner Errors",
    )
        
    logging.info("--- Squeeze/Hold Action Plan Generated. See stdout for full report. ---")
    
def main():
    print("======================================================")
    print("           THE ALPHA SOVEREIGN ORCHESTRATOR           ")
    print("======================================================")
    print("Bot is Armed. Waiting for Friday 15:55 (Market Close).")
    
    # Run a test scan immediately to ensure pipelines are clear
    print("\nRunning immediate diagnostic scan to verify modules...")
    startup_ok = True
    try:
        run_scanners()
    except ScannerTerminationError as exc:
        logging.critical(f"Startup diagnostic hit terminal scanner failure: {exc}")
        raise
    except Exception as exc:
        startup_ok = False
        logging.error(f"Startup diagnostic scan failed: {exc}")

    if startup_ok:
        print("\nDiagnostic complete. Entering armed sleep mode...\n")
    else:
        print("\nDiagnostic failed. Entering armed sleep mode with scheduled retries...\n")
    
    # Production schedule: run at 3:55 PM every Friday, right before the bell.
    schedule.every().friday.at("15:55").do(run_scanners)
    
    try:
        while True:
            try:
                schedule.run_pending()
            except ScannerTerminationError as exc:
                logging.critical(f"Scheduled scanner failure requires orchestrator stop: {exc}")
                raise
            except Exception as exc:
                logging.error(f"Scheduled run failed: {exc}")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nSovereign Orchestrator locally disarmed by user.")

if __name__ == "__main__":
    main()
