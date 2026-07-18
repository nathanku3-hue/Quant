"""GV-FS0 verifier supervision and synthetic component certification.

The controller invokes the process-only V1.1 reconstruction engine exactly two
times from original verifier input, wraps each successful reconstruction into
the frozen V1 verifier-result schema, compares it with the primary book, and
emits an in-memory certified OPEN or NO_POSITION result. It never publishes a
bundle.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
from typing import Any, BinaryIO

from core.gv_fs0_book import (
    OpenBookBuild,
    PROTOCOL_ID,
    PROTOCOL_VERSION,
    build_no_position_book,
    build_open_book,
    validate_schema,
    verifier_rows_to_economic_payload,
)
from core.gv_fs0_canonical import (
    canonical_document_bytes,
    domain_hash,
    parse_canonical_document_bytes,
)

ROOT = Path(__file__).resolve().parents[1]
VERIFIER_SCRIPT = (ROOT / "validation" / "gv_fs0_reconstruction.py").resolve()
REGISTRY_PATH = (
    ROOT
    / "contracts"
    / "gv_fs0"
    / "v1"
    / "registries"
    / "gv_fs0_certification_failure_registry_v1.json"
)

EXECUTION_DEADLINE_SECONDS = 30.0
SHUTDOWN_OBSERVATION_SECONDS = 2.0
STDOUT_LIMIT = 1_048_576
STDERR_LIMIT = 65_536

CHECK_NAMES = (
    "decision_authority_valid",
    "timestamp_causality_valid",
    "price_freshness_valid",
    "cash_conserved",
    "holdings_valid",
    "nav_reconciled",
    "receivables_reconciled",
    "unsupported_events_absent",
    "independent_reconstruction_passed",
    "canonical_hash_reproduced",
)


class GvFs0CertificationError(RuntimeError):
    """Fail-closed certification controller error."""


VerifierRunner = Callable[[Mapping[str, Any]], dict[str, Any]]


@dataclass
class _StreamCapture:
    validity_limit: int
    observation_cap: int
    retained: bytearray = field(default_factory=bytearray)
    total_observed: int = 0
    overflow_at: float | None = None
    eof: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    def observe(self, chunk: bytes, observed_at: float) -> None:
        with self.lock:
            previous = self.total_observed
            self.total_observed = min(
                self.observation_cap, self.total_observed + len(chunk)
            )
            remaining = self.observation_cap - len(self.retained)
            if remaining > 0:
                self.retained.extend(chunk[:remaining])
            if self.overflow_at is None and previous + len(chunk) > self.validity_limit:
                self.overflow_at = observed_at

    def mark_eof(self) -> None:
        with self.lock:
            self.eof = True


def _capture_stream(stream: BinaryIO, capture: _StreamCapture) -> None:
    try:
        while True:
            chunk = stream.read(65_536)
            if not chunk:
                capture.mark_eof()
                return
            capture.observe(chunk, time.monotonic())
    finally:
        stream.close()


def _supervise_process(
    command: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    deadline_seconds: float = EXECUTION_DEADLINE_SECONDS,
    shutdown_seconds: float = SHUTDOWN_OBSERVATION_SECONDS,
    stdout_limit: int = STDOUT_LIMIT,
    stderr_limit: int = STDERR_LIMIT,
) -> tuple[int, bytes, bytes]:
    try:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=dict(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        raise GvFs0CertificationError("VERIFIER_PROCESS_FAILED") from exc
    if process.stdout is None or process.stderr is None:
        process.kill()
        raise GvFs0CertificationError("VERIFIER_SUPERVISION_INCOMPLETE")

    started_at = time.monotonic()
    stdout_capture = _StreamCapture(stdout_limit, stdout_limit + 1)
    stderr_capture = _StreamCapture(stderr_limit, stderr_limit + 1)
    readers = [
        threading.Thread(
            target=_capture_stream,
            args=(process.stdout, stdout_capture),
            daemon=True,
        ),
        threading.Thread(
            target=_capture_stream,
            args=(process.stderr, stderr_capture),
            daemon=True,
        ),
    ]
    for reader in readers:
        reader.start()

    hard_boundary: str | None = None
    deadline_at = started_at + deadline_seconds
    while True:
        now = time.monotonic()
        overflow_times = [
            value
            for value in (stdout_capture.overflow_at, stderr_capture.overflow_at)
            if value is not None
        ]
        first_overflow = min(overflow_times) if overflow_times else None
        running = process.poll() is None
        if now >= deadline_at and (running or not (stdout_capture.eof and stderr_capture.eof)):
            hard_boundary = (
                "VERIFIER_OUTPUT_LIMIT_EXCEEDED"
                if first_overflow is not None and first_overflow < deadline_at
                else "VERIFIER_TIMEOUT"
            )
            break
        if first_overflow is not None:
            hard_boundary = "VERIFIER_OUTPUT_LIMIT_EXCEEDED"
            break
        if not running and stdout_capture.eof and stderr_capture.eof:
            break
        time.sleep(0.005)

    if hard_boundary is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=shutdown_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            try:
                process.wait(timeout=shutdown_seconds)
            except subprocess.TimeoutExpired as exc:
                raise GvFs0CertificationError(
                    "VERIFIER_SUPERVISION_INCOMPLETE"
                ) from exc
    elif process.poll() is None:
        process.wait()

    for reader in readers:
        reader.join(timeout=shutdown_seconds)
    if hard_boundary is not None:
        raise GvFs0CertificationError(hard_boundary)
    if any(reader.is_alive() for reader in readers):
        raise GvFs0CertificationError("VERIFIER_SUPERVISION_INCOMPLETE")
    if not stdout_capture.eof or not stderr_capture.eof:
        raise GvFs0CertificationError("VERIFIER_SUPERVISION_INCOMPLETE")
    return (
        int(process.returncode),
        bytes(stdout_capture.retained),
        bytes(stderr_capture.retained),
    )


def _subprocess_environment(temp_root: str) -> dict[str, str]:
    if os.name == "nt":
        allowed = {
            key: os.environ[key]
            for key in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT")
            if key in os.environ
        }
        allowed.update({"TEMP": temp_root, "TMP": temp_root, "TZ": "UTC"})
        return allowed
    return {
        "HOME": temp_root,
        "TMPDIR": temp_root,
        "TZ": "UTC",
        "LC_ALL": "C",
        "LANG": "C",
    }


def run_isolated_verifier(verifier_input: Mapping[str, Any]) -> dict[str, Any]:
    """Run one bounded V1.1 verifier attempt and return canonical output."""

    with TemporaryDirectory(prefix="gv-fs0-verifier-") as temp_root:
        input_path = (Path(temp_root) / "verifier-input.json").resolve()
        input_path.write_bytes(canonical_document_bytes(dict(verifier_input)))
        command = [
            str(Path(sys.executable).resolve()),
            "-I",
            "-X",
            "utf8",
            str(VERIFIER_SCRIPT),
            "--input",
            str(input_path),
        ]
        returncode, stdout, stderr = _supervise_process(
            command,
            cwd=temp_root,
            env=_subprocess_environment(temp_root),
        )
        if returncode != 0:
            raise GvFs0CertificationError("VERIFIER_PROCESS_FAILED")
        if stderr:
            raise GvFs0CertificationError("VERIFIER_STDERR_NONEMPTY")
        try:
            output = parse_canonical_document_bytes(stdout)
        except Exception as exc:
            raise GvFs0CertificationError("VERIFIER_OUTPUT_NOT_CANONICAL") from exc
        if not isinstance(output, dict):
            raise GvFs0CertificationError("VERIFIER_OUTPUT_SCHEMA_INVALID")
        expected_keys = {
            "canonical_payload_hash",
            "economic_payload",
            "input_hash",
            "isolation",
            "protocol_compat_version",
            "reconstruction_engine",
            "schema_version",
            "verifier_result_hash",
        }
        if set(output) != expected_keys:
            raise GvFs0CertificationError("VERIFIER_OUTPUT_SCHEMA_INVALID")
        if output["schema_version"] != "GV_FS0_RECONSTRUCTION_RESULT_V1_1":
            raise GvFs0CertificationError("VERIFIER_OUTPUT_SCHEMA_INVALID")
        if output["protocol_compat_version"] != "GV_FS0_PROTOCOL_V1_1_VERIFIER_IO":
            raise GvFs0CertificationError("VERIFIER_RESULT_BINDING_INVALID")
        expected_input_hash = domain_hash("GV-FS0:VERIFIER_INPUT:V1", dict(verifier_input))
        if output["input_hash"] != expected_input_hash:
            raise GvFs0CertificationError("VERIFIER_RESULT_BINDING_INVALID")
        expected_payload_hash = domain_hash(
            "GV-FS0:ECONOMIC_PAYLOAD:V1", output["economic_payload"]
        )
        if output["canonical_payload_hash"] != expected_payload_hash:
            raise GvFs0CertificationError("VERIFIER_RESULT_BINDING_INVALID")
        result_without_hash = {
            key: value for key, value in output.items() if key != "verifier_result_hash"
        }
        if output["verifier_result_hash"] != domain_hash(
            "GV-FS0:VERIFIER_RESULT:V1", result_without_hash
        ):
            raise GvFs0CertificationError("VERIFIER_RESULT_BINDING_INVALID")
        return output


def _formal_verifier_result(
    build: OpenBookBuild, raw_result: Mapping[str, Any]
) -> dict[str, Any]:
    economic = raw_result["economic_payload"]
    expected_sessions = [
        {
            "cash": snapshot["cash"],
            "contribution": snapshot["session_contribution"],
            "market_value": snapshot["market_value"],
            "nav": snapshot["nav"],
            "receivables": snapshot["receivables"],
            "session": snapshot["session"],
            "shares": snapshot["shares"],
        }
        for snapshot in build.book.snapshots
    ]
    terminal = expected_sessions[-1]
    expected_economic = {
        "action": build.decision.action,
        "authority": build.decision.authority_tier,
        "currency": build.source_fixture["currency"],
        "decision_id": build.decision.decision_id,
        "final_state": dict(terminal),
        "fixture_id": build.decision.fixture_id,
        "protocol_id": PROTOCOL_ID,
        "rationale_reference": build.decision.rationale_ref,
        "schema_version": "GV_FS0_ECONOMIC_PAYLOAD_V1",
        "security_id": build.decision.security_id,
        "sessions": expected_sessions,
        "total_costs": str(
            sum(
                (
                    Decimal(event["payload"]["fee"])
                    for event in build.book.events
                    if event["event_type"] == "FEE_OR_COST"
                ),
                Decimal("0"),
            )
        ),
    }
    expected_raw_hash = domain_hash(
        "GV-FS0:ECONOMIC_PAYLOAD:V1", expected_economic
    )
    if (
        economic != expected_economic
        or raw_result.get("canonical_payload_hash") != expected_raw_hash
    ):
        raise GvFs0CertificationError("VERIFIER_RESULT_BINDING_INVALID")
    reconstructed_payload = verifier_rows_to_economic_payload(build, economic["sessions"])
    formal = {
        "schema_version": "gv_fs0_verifier_result_v1",
        "protocol_binding": PROTOCOL_ID,
        "fixture_binding": build.fixture_hash,
        "decision_binding": build.decision.decision_hash,
        "verifier_input_hash": domain_hash(
            "GV-FS0:VERIFIER_INPUT:V1", build.verifier_input
        ),
        "verifier_status": "RECONSTRUCTED",
        "reconstructed_economic_payload": reconstructed_payload,
        "reconstructed_economic_payload_hash": domain_hash(
            "GV-FS0:ECONOMIC_PAYLOAD:V1", reconstructed_payload
        ),
        "failure_codes": [],
    }
    validate_schema(formal, "gv_fs0_verifier_result_v1.schema.json")
    return formal


def _price_freshness_valid(build: OpenBookBuild) -> bool:
    prices = {row["session"]: row for row in build.source_fixture["source_prices"]}
    valuation_events = [
        event
        for event in build.book.events
        if event["event_type"] == "SESSION_VALUATION"
    ]
    return len(valuation_events) == len(prices) and all(
        event["session"] in prices
        and event["payload"]["valuation_price"] == prices[event["session"]]["close_price"]
        and prices[event["session"]]["price_timestamp"] <= event["effective_timestamp"]
        for event in valuation_events
    )


def _primary_invariants_valid(build: OpenBookBuild) -> dict[str, bool]:
    snapshots = build.book.snapshots
    cash = Decimal(build.source_fixture["initial_cash"])
    shares = 0
    receivables: dict[str, Decimal] = {}
    paid: set[str] = set()
    snapshot_index = 0
    cash_conserved = True
    holdings_valid = True
    receivables_reconciled = True
    supported = {
        "DECISION_ACCEPTED",
        "EXECUTION",
        "FEE_OR_COST",
        "CASH_MOVEMENT",
        "POSITION_MOVEMENT",
        "DIVIDEND_ENTITLEMENT",
        "DIVIDEND_PAYMENT",
        "SESSION_VALUATION",
    }
    unsupported_events_absent = True

    for event in build.book.events:
        event_type = event["event_type"]
        payload = event["payload"]
        if event_type not in supported:
            unsupported_events_absent = False
            continue
        if event_type == "CASH_MOVEMENT":
            cash += Decimal(payload["cash_delta"])
        elif event_type == "POSITION_MOVEMENT":
            shares += int(payload["position_delta"])
        elif event_type == "DIVIDEND_ENTITLEMENT":
            if event["event_id"] in receivables:
                receivables_reconciled = False
            receivables[event["event_id"]] = Decimal(payload["receivable_amount"])
        elif event_type == "DIVIDEND_PAYMENT":
            entitlement_id = payload["referenced_entitlement_id"]
            amount = receivables.get(entitlement_id)
            if amount is None or entitlement_id in paid:
                receivables_reconciled = False
            else:
                if amount != Decimal(payload["payment_amount"]):
                    receivables_reconciled = False
                cash += amount
                paid.add(entitlement_id)
                del receivables[entitlement_id]
        elif event_type == "SESSION_VALUATION":
            if snapshot_index >= len(snapshots):
                return {
                    "cash_conserved": False,
                    "holdings_valid": False,
                    "nav_reconciled": False,
                    "receivables_reconciled": False,
                    "unsupported_events_absent": unsupported_events_absent,
                }
            snapshot = snapshots[snapshot_index]
            snapshot_index += 1
            receivable_total = sum(receivables.values(), Decimal("0"))
            cash_conserved &= Decimal(snapshot["cash"]) == cash and cash >= 0
            holdings_valid &= snapshot["shares"] == shares and shares >= 0
            receivables_reconciled &= Decimal(snapshot["receivables"]) == receivable_total

    cash_conserved &= snapshot_index == len(snapshots)
    holdings_valid &= snapshot_index == len(snapshots)
    receivables_reconciled &= not receivables and snapshots[-1]["receivables"] == "0"
    nav_reconciled = all(
        Decimal(row["nav"])
        == Decimal(row["cash"])
        + Decimal(row["market_value"])
        + Decimal(row["receivables"])
        for row in snapshots
    )
    return {
        "cash_conserved": cash_conserved,
        "holdings_valid": holdings_valid,
        "nav_reconciled": nav_reconciled,
        "receivables_reconciled": receivables_reconciled,
        "unsupported_events_absent": unsupported_events_absent,
    }


def _decision_semantics_valid(build: OpenBookBuild) -> bool:
    if build.decision.authority_tier != "MANUAL_OWNER_PAPER":
        return False
    if build.decision.action == "OPEN":
        return build.decision.requested_quantity == 10
    if build.decision.action == "NO_POSITION":
        return (
            build.decision.requested_quantity is None
            and all(
                intent["intent_type"] == "VALUATION_INSTRUCTION"
                for intent in build.source_fixture["source_intents"]
            )
            and all(
                event["event_type"] in {"DECISION_ACCEPTED", "SESSION_VALUATION"}
                for event in build.book.events
            )
        )
    return False


def _certification_checks(
    build: OpenBookBuild,
    formal_results: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    invariant_checks = _primary_invariants_valid(build)
    reconstructed_hashes = [
        result["reconstructed_economic_payload_hash"] for result in formal_results
    ]
    primary_hash = build.book.economic_payload_hash
    independent_pass = (
        len(formal_results) == 2
        and formal_results[0] == formal_results[1]
        and all(
            result["reconstructed_economic_payload"] == build.book.economic_payload
            for result in formal_results
        )
    )
    hash_pass = len(reconstructed_hashes) == 2 and all(
        value == primary_hash for value in reconstructed_hashes
    )
    checks = {
        "decision_authority_valid": _decision_semantics_valid(build),
        "timestamp_causality_valid": (
            build.decision.decision_timestamp < build.decision.effective_timestamp
            and all(
                event["semantic_sequence"] == index
                for index, event in enumerate(build.book.events)
            )
        ),
        "price_freshness_valid": _price_freshness_valid(build),
        **invariant_checks,
        "independent_reconstruction_passed": independent_pass,
        "canonical_hash_reproduced": hash_pass,
    }
    if set(checks) != set(CHECK_NAMES):
        raise GvFs0CertificationError("CERTIFICATION_CHECK_SET_INVALID")
    return {name: "TRUE" if checks[name] else "FALSE" for name in CHECK_NAMES}


def _certification_id_preimage(
    *,
    build: OpenBookBuild,
    verifier_input_hash: str,
    attempts: Sequence[Mapping[str, Any]],
    checks: Mapping[str, str],
    registry_hash: str,
) -> dict[str, Any]:
    return {
        "certification_schema_version": "gv_fs0_certification_v1",
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "fixture_id": build.decision.fixture_id,
        "fixture_hash": build.fixture_hash,
        "decision_id": build.decision.decision_id,
        "decision_hash": build.decision.decision_hash,
        "book_id": build.book.book_id,
        "terminal_snapshot_id": build.book.snapshots[-1]["snapshot_id"],
        "primary_economic_payload_hash": build.book.economic_payload_hash,
        "verifier_input_hash": verifier_input_hash,
        "verifier_attempts": [dict(attempt) for attempt in attempts],
        "checks": dict(checks),
        "certification_status": "CERTIFIED",
        "certification_failure_registry_version": "gv_fs0_certification_failure_registry_v1",
        "certification_failure_registry_hash": registry_hash,
        "failure_bindings": [],
    }


def _certification_reference_event(
    build: OpenBookBuild, certification_id: str
) -> dict[str, Any]:
    terminal = build.book.snapshots[-1]
    source_sequence = max(
        intent["source_sequence"] for intent in build.source_fixture["source_intents"]
    ) + 1
    source_intent_id = f"CERTIFICATION:{certification_id}"
    preimage = {
        "schema_version": "gv_fs0_portfolio_event_v1",
        "book_id": build.book.book_id,
        "decision_id": build.decision.decision_id,
        "terminal_snapshot_id": terminal["snapshot_id"],
        "certification_id": certification_id,
        "event_type": "CERTIFICATION_REFERENCE",
        "event_type_rank": 90,
        "effective_timestamp": terminal["valuation_timestamp"],
        "session": terminal["session"],
        "source_sequence": source_sequence,
        "source_intent_id": source_intent_id,
        "generated_event_slot": 10,
        "intra_rank_sequence": 0,
    }
    event_id = "EVT_" + domain_hash(
        "GV-FS0:CERTIFICATION_REFERENCE_EVENT_ID:V1", preimage
    )
    payload = {
        "quantity": None,
        "execution_price": None,
        "fee": None,
        "cash_delta": None,
        "position_delta": None,
        "dividend_amount_per_share": None,
        "entitled_quantity": None,
        "receivable_amount": None,
        "payment_amount": None,
        "referenced_entitlement_id": None,
        "valuation_price": None,
        "terminal_snapshot_id": terminal["snapshot_id"],
        "certification_id": certification_id,
    }
    event = {
        "schema_version": "gv_fs0_portfolio_event_v1",
        "event_id": event_id,
        "book_id": build.book.book_id,
        "decision_id": build.decision.decision_id,
        "source_sequence": source_sequence,
        "source_intent_id": source_intent_id,
        "generated_event_slot": 10,
        "event_type": "CERTIFICATION_REFERENCE",
        "effective_timestamp": terminal["valuation_timestamp"],
        "session": terminal["session"],
        "event_type_rank": 90,
        "intra_rank_sequence": 0,
        "semantic_sequence": len(build.book.events),
        "security_id": build.decision.security_id,
        "payload": payload,
    }
    validate_schema(event, "gv_fs0_portfolio_event_v1.schema.json")
    return event


def _presentation(
    build: OpenBookBuild, certification: Mapping[str, Any]
) -> dict[str, Any]:
    terminal = build.book.snapshots[-1]
    rows = [
        {"label": "Authority", "value": build.decision.authority_tier},
        {"label": "Action", "value": build.decision.action},
        {"label": "Rationale", "value": build.decision.rationale_ref},
        {"label": "Shares", "value": str(terminal["shares"])},
        {"label": "Cash", "value": terminal["cash"]},
        {"label": "Receivables", "value": terminal["receivables"]},
        {"label": "NAV", "value": terminal["nav"]},
        {"label": "SessionContribution", "value": terminal["session_contribution"]},
        {"label": "CumulativeContribution", "value": terminal["cumulative_contribution"]},
        {"label": "BookId", "value": build.book.book_id},
        {"label": "DecisionHash", "value": build.decision.decision_hash},
        {"label": "SnapshotId", "value": terminal["snapshot_id"]},
        {"label": "CertificationId", "value": certification["certification_id"]},
        {"label": "CertificationStatus", "value": certification["certification_status"]},
    ]
    return {
        "presentation_hash": domain_hash("GV-FS0:PRESENTATION:V1", {"rows": rows}),
        "rows": rows,
    }


def _build_certified_result(
    build: OpenBookBuild,
    verifier_runner: VerifierRunner,
) -> dict[str, Any]:
    """Build one in-memory certified synthetic component through the shared path."""
    raw_results: list[dict[str, Any]] = []
    attempt_failures: list[str] = []
    for _ordinal in (1, 2):
        try:
            raw_results.append(verifier_runner(build.verifier_input))
        except GvFs0CertificationError as exc:
            attempt_failures.append(str(exc))
        except Exception:
            attempt_failures.append("VERIFIER_PROCESS_FAILED")
    if attempt_failures:
        raise GvFs0CertificationError(
            "CERTIFICATION_BLOCKED:" + ",".join(attempt_failures)
        )
    try:
        formal_results = [_formal_verifier_result(build, raw) for raw in raw_results]
    except GvFs0CertificationError as exc:
        raise GvFs0CertificationError(f"CERTIFICATION_BLOCKED:{exc}") from exc
    formal_hashes = [
        domain_hash("GV-FS0:VERIFIER_RESULT:V1", result) for result in formal_results
    ]
    attempts = [
        {
            "schema_version": "gv_fs0_verifier_attempt_v1",
            "ordinal": ordinal,
            "outcome": "RESULT",
            "verifier_result_hash": result_hash,
            "controller_failure_code": None,
        }
        for ordinal, result_hash in enumerate(formal_hashes, start=1)
    ]
    for attempt in attempts:
        validate_schema(attempt, "gv_fs0_verifier_attempt_v1.schema.json")

    retained_by_hash = {
        result_hash: {
            "verifier_result_hash": result_hash,
            "verifier_result": result,
        }
        for result_hash, result in zip(formal_hashes, formal_results, strict=True)
    }
    retained_results = [retained_by_hash[key] for key in sorted(retained_by_hash)]
    checks = _certification_checks(build, formal_results)
    if any(value != "TRUE" for value in checks.values()):
        raise GvFs0CertificationError("CERTIFICATION_BLOCKED")

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry_hash = domain_hash("GV-FS0:CERTIFICATION_FAILURE_REGISTRY:V1", registry)
    verifier_input_hash = domain_hash("GV-FS0:VERIFIER_INPUT:V1", build.verifier_input)
    certification_preimage = _certification_id_preimage(
        build=build,
        verifier_input_hash=verifier_input_hash,
        attempts=attempts,
        checks=checks,
        registry_hash=registry_hash,
    )
    certification_id = "CERT_" + domain_hash(
        "GV-FS0:CERTIFICATION_ID:V1", certification_preimage
    )
    certification = {
        "schema_version": "gv_fs0_certification_v1",
        "certification_id": certification_id,
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "fixture_id": build.decision.fixture_id,
        "fixture_hash": build.fixture_hash,
        "decision_id": build.decision.decision_id,
        "decision_hash": build.decision.decision_hash,
        "book_id": build.book.book_id,
        "terminal_snapshot_id": build.book.snapshots[-1]["snapshot_id"],
        "primary_economic_payload_hash": build.book.economic_payload_hash,
        "verifier_input_hash": verifier_input_hash,
        "verifier_attempts": attempts,
        "checks": checks,
        "certification_status": "CERTIFIED",
        "certification_failure_registry_version": "gv_fs0_certification_failure_registry_v1",
        "certification_failure_registry_hash": registry_hash,
        "failure_bindings": [],
    }
    validate_schema(certification, "gv_fs0_certification_v1.schema.json")
    reference_event = _certification_reference_event(build, certification_id)
    all_events = [*build.book.events, reference_event]
    authoritative = {
        "schema_version": "gv_fs0_certified_decision_result_v1",
        "role": build.decision.action,
        "decision": build.decision.to_dict(),
        "book_id": build.book.book_id,
        "events": all_events,
        "snapshots": list(build.book.snapshots),
        "economic_payload_hash": build.book.economic_payload_hash,
        "verifier_attempts": attempts,
        "retained_verifier_results": retained_results,
        "certification": certification,
        "certification_reference_event": reference_event,
    }
    result_hash = domain_hash("GV-FS0:CERTIFIED_DECISION_RESULT:V1", authoritative)
    presentation = _presentation(build, certification)
    result = {
        **authoritative,
        "certified_decision_result_id": "CDR_" + result_hash,
        "certified_decision_result_hash": result_hash,
        "presentation": presentation,
    }
    validate_schema(result, "gv_fs0_certified_decision_result_v1.schema.json")
    return result


def build_certified_result_from_book(
    build: OpenBookBuild,
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Build one certified result from an arbitrary primary book build."""

    return _build_certified_result(build, verifier_runner)


def build_open_certified_result(
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Build the complete in-memory certified OPEN component for F1A."""

    return _build_certified_result(build_open_book(), verifier_runner)


def build_no_position_certified_result(
    verifier_runner: VerifierRunner = run_isolated_verifier,
) -> dict[str, Any]:
    """Build the complete in-memory certified NO_POSITION component for F1B."""

    return _build_certified_result(build_no_position_book(), verifier_runner)


__all__ = [
    "GvFs0CertificationError",
    "build_certified_result_from_book",
    "build_no_position_certified_result",
    "build_open_certified_result",
    "run_isolated_verifier",
]
