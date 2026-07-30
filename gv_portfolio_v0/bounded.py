"""GV-BOUNDED-PORTFOLIO-1 — repeated bounded paper portfolio on persisted state.

Cycles chain through a content-addressed session ledger: each cycle loads the
prior persisted workspace, admits a later observation (explicit no-change or
authorized transition disposition), re-certifies with append-only lineage, and
re-verifies exact Replay reconstruction. Independent fixture re-runs alone are
not acceptance.

Immutable pins:

- promotion tip (branch base): ``5fc2e4c…``
- Replay code pin (not branch point): ``0e4b93f…``
"""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.book import certification_eligible
from gv_portfolio_v0.execution import ExecutionError, portfolio_book_event
from gv_portfolio_v0.replay import (
    ReplayError,
    append_correction_and_recertify,
    build_replay_report,
    certify_replay_prefix,
    event_ledger_hash,
    reconstruct_exact,
    replay_idempotent,
    reopen_slice0_workspace_stable,
)
from gv_portfolio_v0.thesis import StrategyThesisError, unchanged_aim_watch_observation
from gv_portfolio_v0.vertical import (
    PortfolioV0Error,
    admit_watch_observation,
    build_draft_workspace,
    certify_workspace,
    confirm_draft_workspace,
    evidence_reference,
    reduce_events,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
BOUNDED_SCHEMA = "gv_portfolio_v0_bounded_report_v1"
SESSION_SCHEMA = "gv_portfolio_v0_bounded_session_v1"
BOUNDED_CLAIM_BOUNDARY = (
    "Bounded repeated paper portfolio only; no alpha or live-capital claim."
)
SESSION_FILENAME = "bounded_session.json"

# Branch / authority pins
PROMOTION_TIP_SHA = "5fc2e4c01aa98ffe6ad9fcce4d1f9299c4aee6e4"
REPLAY_CODE_PIN_SHA = "0e4b93fb370f67956502edc02e9c6f56ceb2eba3"
REPLAY_CUSTODY_BASE_SHA = "03a5c922d250d615380bbd0d60e8fd636e4ec1c6"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"

DEFAULT_CYCLE_COUNT = 3
DECLARED_SECURITY_COUNT = 4

# Explicit observation dispositions (authorized transition reserved for later).
DISPOSITION_AIM_UNCHANGED = "AIM_UNCHANGED_NO_TRANSITION"
DISPOSITION_AUTHORIZED_TRANSITION = "AUTHORIZED_TRANSITION"  # reserved; fail-closed here


class BoundedPortfolioError(ValueError):
    """Fail-closed bounded portfolio error."""


def branch_pins() -> dict[str, str]:
    return {
        "promotion_tip_sha": PROMOTION_TIP_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "replay_custody_base_sha": REPLAY_CUSTODY_BASE_SHA,
        "slice0_terminal_sha": SLICE0_TERMINAL_SHA,
        "active_implementation_base": PROMOTION_TIP_SHA,
        "immutable_replay_code_pin": REPLAY_CODE_PIN_SHA,
    }


def session_path(root: Path) -> Path:
    return Path(root) / SESSION_FILENAME


def workspace_content_hash(workspace: Mapping[str, Any]) -> str:
    return domain_hash(f"{ID_DOMAIN}:BOUNDED_WORKSPACE:V1", dict(workspace))


def _fail_replay(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise BoundedPortfolioError(f"REPLAY_DRIFT:{message}:{cause}") from cause
    raise BoundedPortfolioError(f"REPLAY_DRIFT:{message}")


def _fail(message: str) -> None:
    raise BoundedPortfolioError(message)


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        _fail("SESSION_ROOT_SYMLINK_PROHIBITED")
    raw = canonical_document_bytes(dict(payload))
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def save_session(root: Path, session: Mapping[str, Any]) -> Path:
    body = dict(session)
    envelope = {
        "schema_version": SESSION_SCHEMA,
        "session_hash": domain_hash(f"{ID_DOMAIN}:BOUNDED_SESSION:V1", body),
        "session": body,
    }
    path = session_path(root)
    _atomic_write(path, envelope)
    return path


def load_session(root: Path) -> dict[str, Any]:
    path = session_path(root)
    if not path.is_file():
        _fail("BOUNDED_SESSION_NOT_FOUND")
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BoundedPortfolioError("BOUNDED_SESSION_READ_INVALID") from exc
    if envelope.get("schema_version") != SESSION_SCHEMA:
        _fail("BOUNDED_SESSION_SCHEMA_INVALID")
    session = envelope.get("session")
    if not isinstance(session, dict):
        _fail("BOUNDED_SESSION_OBJECT_REQUIRED")
    expected = domain_hash(f"{ID_DOMAIN}:BOUNDED_SESSION:V1", session)
    if envelope.get("session_hash") != expected:
        _fail("BOUNDED_SESSION_HASH_MISMATCH")
    workspace = session.get("workspace")
    if not isinstance(workspace, dict):
        _fail("BOUNDED_SESSION_WORKSPACE_REQUIRED")
    stored_ws_hash = session.get("workspace_content_hash")
    if stored_ws_hash != workspace_content_hash(workspace):
        _fail("BOUNDED_SESSION_WORKSPACE_HASH_MISMATCH")
    return session


def _verify_replay_non_drift(
    events: list[dict[str, Any]],
    *,
    expected_book: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
    try:
        book = reconstruct_exact(events, expected_book=expected_book)
    except ReplayError as exc:
        _fail_replay(f"{label}:RECONSTRUCTION", cause=exc)
        raise  # pragma: no cover
    try:
        idempotent = replay_idempotent(events)
    except ReplayError as exc:
        _fail_replay(f"{label}:IDEMPOTENCE", cause=exc)
        raise  # pragma: no cover
    if book["book_hash"] != idempotent["book_hash"]:
        _fail_replay(f"{label}:BOOK_HASH_MISMATCH")
    if book.get("unexplained_residual") != "0":
        _fail_replay(f"{label}:UNEXPLAINED_RESIDUAL:{book.get('unexplained_residual')}")
    if book.get("split_value_residual") != "0":
        _fail_replay(f"{label}:SPLIT_RESIDUAL:{book.get('split_value_residual')}")
    if book.get("valuation_status") == "COMPLETE" and not certification_eligible(book):
        _fail_replay(f"{label}:CERTIFICATION_INELIGIBLE")
    return book


def _cycle_identity(payload: Mapping[str, Any]) -> str:
    return "CYC_" + domain_hash(f"{ID_DOMAIN}:BOUNDED_CYCLE:V1", dict(payload))


def _event(
    sequence: int,
    event_type: str,
    effective_at: str,
    source_identity: str,
    *,
    instrument_id: str | None = None,
    cash_bucket: str | None = None,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return portfolio_book_event(
            sequence,
            event_type,
            effective_at,
            source_identity,
            instrument_id=instrument_id,
            cash_bucket=cash_bucket,
            payload=payload,
        )
    except ExecutionError as exc:
        raise BoundedPortfolioError(str(exc)) from exc


def _seal_cycle(
    *,
    cycle_index: int,
    workspace: Mapping[str, Any],
    prior_workspace_content_hash: str | None,
    prior_certification_id: str | None,
    observation_disposition: str,
    observation_record: Mapping[str, Any] | None,
    consumed_prior_persisted_state: bool,
) -> dict[str, Any]:
    securities = list(workspace.get("instruments") or [])
    if len(securities) != DECLARED_SECURITY_COUNT:
        _fail("DECLARED_UNIVERSE_SIZE_MISMATCH")
    events = list(workspace["events"])
    book = _verify_replay_non_drift(
        events, expected_book=workspace["book"], label=f"CYCLE{cycle_index}"
    )
    certification = workspace["certification"]
    if not isinstance(certification, Mapping):
        _fail("CYCLE_CERTIFICATION_REQUIRED")
    if prior_certification_id is not None:
        if certification.get("prior_certification_id") != prior_certification_id:
            _fail_replay(f"CYCLE{cycle_index}:PRIOR_CERT_LINK")
    try:
        replay_report = build_replay_report(
            events,
            expected_book=workspace["book"],
            decision_snapshot_id=workspace["decision_snapshot"]["decision_snapshot_id"],
            portfolio_aim_id=workspace["portfolio_aim"]["portfolio_aim_id"],
        )
    except ReplayError as exc:
        _fail_replay(f"CYCLE{cycle_index}:REPLAY_REPORT", cause=exc)
        raise  # pragma: no cover

    body = {
        "cycle_index": cycle_index,
        "status": workspace["status"],
        "security_count": len(securities),
        "event_count": len(events),
        "event_ledger_hash": event_ledger_hash(events),
        "book_hash": book["book_hash"],
        "workspace_content_hash": workspace_content_hash(workspace),
        "prior_workspace_content_hash": prior_workspace_content_hash,
        "prior_certification_id": certification.get("prior_certification_id"),
        "certification_id": certification["certification_id"],
        "terminal_nav": book.get("terminal_nav"),
        "unexplained_residual": book.get("unexplained_residual"),
        "partial_fill_residuals": list(book.get("partial_fill_residuals") or []),
        "observation_disposition": observation_disposition,
        "observation_record": dict(observation_record or {}),
        "consumed_prior_persisted_state": consumed_prior_persisted_state,
        "replay_report_hash": replay_report["report_hash"],
        "replay_non_drift": True,
    }
    return {"cycle_id": _cycle_identity(body), **body}


def bootstrap_certified_workspace() -> dict[str, Any]:
    """Product Slice 0 path: draft → confirm (single paper fill)."""

    try:
        draft = build_draft_workspace()
        return confirm_draft_workspace(draft)
    except PortfolioV0Error as exc:
        raise BoundedPortfolioError(f"BOOTSTRAP_FAILED:{exc}") from exc


def admit_first_observation(workspace: Mapping[str, Any]) -> dict[str, Any]:
    """Product first later-observation path (explicit aim-unchanged)."""

    try:
        return admit_watch_observation(workspace)
    except PortfolioV0Error as exc:
        raise BoundedPortfolioError(f"FIRST_OBSERVATION_FAILED:{exc}") from exc


def admit_follow_on_observation(
    workspace: Mapping[str, Any],
    *,
    cycle_index: int,
    observation_content: str,
    locator: str,
    observed_at: str,
    disposition: str = DISPOSITION_AIM_UNCHANGED,
) -> dict[str, Any]:
    """Append another later observation on persisted prior workspace.

    Product validate_workspace allows only one observation; multi-cycle authority
    lives here. Economics remain product book reduction; certification uses the
    product certifier with append-only prior linkage.
    """

    if disposition == DISPOSITION_AUTHORIZED_TRANSITION:
        _fail("AUTHORIZED_TRANSITION_NOT_ENABLED_IN_BOUNDED_V1")
    if disposition != DISPOSITION_AIM_UNCHANGED:
        _fail(f"UNKNOWN_OBSERVATION_DISPOSITION:{disposition}")

    status = workspace.get("status")
    if status not in {"CERTIFIED", "OBSERVED_WATCH_AIM_UNCHANGED"}:
        _fail(f"FOLLOW_ON_STATUS_INVALID:{status}")

    result = deepcopy(dict(workspace))
    original_aim_id = result["portfolio_aim"]["portfolio_aim_id"]
    original_snapshot = canonical_document_bytes(result["decision_snapshot"])
    prior = deepcopy(result["certification"])
    if not isinstance(prior, Mapping):
        _fail("PRIOR_CERTIFICATION_REQUIRED")

    # Recompute tip certification from current workspace; reject forged priors.
    try:
        recomputed_prior = certify_workspace(
            result,
            prior_certification_id=prior.get("prior_certification_id"),
        )
    except PortfolioV0Error as exc:
        raise BoundedPortfolioError(f"PRIOR_CERT_RECOMPUTE_FAILED:{exc}") from exc
    if canonical_document_bytes(recomputed_prior) != canonical_document_bytes(prior):
        _fail("FORGED_OR_STALE_PRIOR_CERTIFICATION")

    observation = evidence_reference(
        content=observation_content,
        locator=locator,
        observed_at=observed_at,
    )
    result["evidence_references"] = [*result["evidence_references"], observation]
    principal_review = next(
        row for row in result["reviews"] if row["relationship"] == "PRINCIPAL_THESIS"
    )
    try:
        observation_state = unchanged_aim_watch_observation(
            living_thesis=principal_review["living_thesis_lite"],
            available_evidence_reference_ids=[
                row["evidence_reference_id"] for row in result["evidence_references"]
            ],
            evidence_reference_id=observation["evidence_reference_id"],
            watch_condition_matches=["order_intake_softens_without_covenant_breach"],
            hard_falsifier_matches=[],
            portfolio_aim_id_before=original_aim_id,
            portfolio_aim_id_after=original_aim_id,
        )
    except StrategyThesisError as exc:
        raise BoundedPortfolioError(f"OBSERVATION_DISPOSITION_FAILED:{exc}") from exc

    # Explicit disposition envelope for Bounded acceptance (no silent no-op).
    disposition_record = {
        "disposition": DISPOSITION_AIM_UNCHANGED,
        "authorized_transition": False,
        "aim_changed": False,
        "classification": observation_state["classification"],
        "evidence_reference_id": observation["evidence_reference_id"],
        "cycle_index": cycle_index,
        "observation_state": observation_state,
    }

    result["events"] = [
        *result["events"],
        _event(
            len(result["events"]),
            "LATER_OBSERVATION_ADMITTED",
            observed_at,
            observation["evidence_reference_id"],
            instrument_id=principal_review["instrument_id"],
            payload={**observation_state, "bounded_disposition": disposition_record},
        ),
    ]
    result["later_observation"] = observation_state
    result["bounded_observation_disposition"] = disposition_record
    history = list(result.get("certification_history") or [])
    result["certification_history"] = [*history, prior]
    result["status"] = "OBSERVED_WATCH_AIM_UNCHANGED"
    result["explanation"] = (
        "Bounded multi-cycle later observation: explicit AIM_UNCHANGED_NO_TRANSITION; "
        "no authorized portfolio transition."
    )

    try:
        certification = certify_workspace(
            result, prior_certification_id=prior["certification_id"]
        )
    except PortfolioV0Error as exc:
        raise BoundedPortfolioError(f"FOLLOW_ON_CERTIFY_FAILED:{exc}") from exc
    result["certification"] = certification
    result["events"].append(
        _event(
            len(result["events"]),
            "CERTIFICATION_RECORDED",
            observed_at,
            certification["certification_id"],
            payload={"certification_id": certification["certification_id"]},
        )
    )
    result["book"] = reduce_events(result["events"])
    if result["portfolio_aim"]["portfolio_aim_id"] != original_aim_id:
        _fail("FOLLOW_ON_CHANGED_AIM")
    if canonical_document_bytes(result["decision_snapshot"]) != original_snapshot:
        _fail("FOLLOW_ON_MUTATED_SNAPSHOT")
    if certification.get("prior_certification_id") != prior["certification_id"]:
        _fail("FOLLOW_ON_PRIOR_LINK_MISMATCH")
    return result


def run_correction_lineage_probe(workspace: Mapping[str, Any]) -> dict[str, Any]:
    """Append-only non-economic correction; prior cert bytes must remain stable."""

    # Use certified prefix when available (strip observation/cert tails carefully).
    events = [
        dict(row)
        for row in workspace["events"]
        if row.get("event_type")
        not in {"CERTIFICATION_RECORDED", "LATER_OBSERVATION_ADMITTED"}
    ]
    # Keep through first fill only for economic stability probe.
    for index, row in enumerate(events):
        row["sequence"] = index
    decision_snapshot_id = workspace["decision_snapshot"]["decision_snapshot_id"]
    portfolio_aim_id = workspace["portfolio_aim"]["portfolio_aim_id"]
    try:
        prior = certify_replay_prefix(
            events,
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
        )
        prior_bytes = canonical_document_bytes(prior)
        result = append_correction_and_recertify(
            events,
            prior_certification=prior,
            correction_payload={
                "correction_kind": "ANNOTATION",
                "reason": "bounded_persisted_lineage_probe",
                "details": {"workspace_content_hash": workspace_content_hash(workspace)},
            },
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
            effective_at="2026-09-01T00:00:00.000000Z",
            source_identity="BOUNDED:CORRECTION:PROBE",
        )
    except ReplayError as exc:
        _fail_replay("CORRECTION_LINEAGE", cause=exc)
        raise  # pragma: no cover
    if canonical_document_bytes(result["prior_certification"]) != prior_bytes:
        _fail_replay("CORRECTION_PRIOR_MUTATED")
    # Tamper probe: forged prior must fail.
    forged = dict(prior)
    forged["terminal_book_hash"] = "0" * 64
    try:
        append_correction_and_recertify(
            events,
            prior_certification=forged,
            correction_payload={"reason": "tamper"},
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
            effective_at="2026-09-01T00:00:01.000000Z",
            source_identity="BOUNDED:CORRECTION:TAMPER",
        )
    except (ReplayError, BoundedPortfolioError):
        forged_rejected = True
    else:
        forged_rejected = False
    if not forged_rejected:
        _fail("FORGED_PRIOR_CERT_ACCEPTED")
    return {
        "prior_certification_id": result["prior_certification"]["certification_id"],
        "certification_id": result["certification"]["certification_id"],
        "book_hash": result["book"]["book_hash"],
        "event_count": len(result["events"]),
        "prior_byte_stable": True,
        "forged_prior_rejected": True,
    }


def run_bounded_portfolio(
    *,
    root: Path,
    cycles: int = DEFAULT_CYCLE_COUNT,
) -> dict[str, Any]:
    """Run N persisted cycles: each cycle consumes prior session state."""

    if not isinstance(cycles, int) or cycles < 2:
        _fail("BOUNDED_CYCLE_COUNT_MIN_2")
    if cycles > 8:
        _fail("BOUNDED_CYCLE_COUNT_CAP_8")

    root = Path(root)
    if session_path(root).exists():
        _fail("BOUNDED_SESSION_ALREADY_EXISTS")

    cycle_seals: list[dict[str, Any]] = []

    # --- Cycle 0: bootstrap certified paper book (no prior session) ---
    certified = bootstrap_certified_workspace()
    prior_ws_hash = None
    session = {
        "schema_version": SESSION_SCHEMA,
        "branch_pins": branch_pins(),
        "workspace": certified,
        "workspace_content_hash": workspace_content_hash(certified),
        "cycle_seals": [],
    }
    save_session(root, session)

    # Cycle 0 observation from freshly persisted certified state
    loaded = load_session(root)
    if loaded["workspace_content_hash"] != workspace_content_hash(certified):
        _fail("PERSIST_RELOAD_MISMATCH_CYCLE0")
    observed = admit_first_observation(loaded["workspace"])
    # Product reopen stability for first observation
    try:
        reopen_slice0_workspace_stable(loaded["workspace"], observed)
    except ReplayError as exc:
        _fail_replay("CYCLE0:REOPEN", cause=exc)
    seal0 = _seal_cycle(
        cycle_index=0,
        workspace=observed,
        prior_workspace_content_hash=loaded["workspace_content_hash"],
        prior_certification_id=loaded["workspace"]["certification"]["certification_id"],
        observation_disposition=DISPOSITION_AIM_UNCHANGED,
        observation_record={
            "disposition": DISPOSITION_AIM_UNCHANGED,
            "authorized_transition": False,
            "source": "product_admit_watch_observation",
            "later_observation": observed.get("later_observation"),
        },
        consumed_prior_persisted_state=True,
    )
    cycle_seals.append(seal0)
    session = {
        "schema_version": SESSION_SCHEMA,
        "branch_pins": branch_pins(),
        "workspace": observed,
        "workspace_content_hash": workspace_content_hash(observed),
        "cycle_seals": list(cycle_seals),
    }
    save_session(root, session)

    # --- Cycles 1..n-1: load prior session, follow-on observation ---
    for cycle_index in range(1, cycles):
        prior_session = load_session(root)
        prior_ws = prior_session["workspace"]
        prior_hash = prior_session["workspace_content_hash"]
        prior_cert_id = prior_ws["certification"]["certification_id"]
        month = 8 + cycle_index  # cycle 1 -> Sep, cycle 2 -> Oct, ...
        follow = admit_follow_on_observation(
            prior_ws,
            cycle_index=cycle_index,
            observation_content=(
                f"Bounded cycle {cycle_index}: renewal evidence remains inside WATCH; "
                f"explicit no portfolio transition (distinct observation bytes)."
            ),
            locator=f"fixture://bounded/cycle-{cycle_index}-watch",
            observed_at=f"2026-{month:02d}-15T12:00:00.000000Z",
            disposition=DISPOSITION_AIM_UNCHANGED,
        )
        if workspace_content_hash(follow) == prior_hash:
            _fail("FOLLOW_ON_DID_NOT_CHANGE_WORKSPACE")
        # Growing event log
        if len(follow["events"]) <= len(prior_ws["events"]):
            _fail("FOLLOW_ON_EVENT_LOG_DID_NOT_GROW")
        seal = _seal_cycle(
            cycle_index=cycle_index,
            workspace=follow,
            prior_workspace_content_hash=prior_hash,
            prior_certification_id=prior_cert_id,
            observation_disposition=DISPOSITION_AIM_UNCHANGED,
            observation_record=follow.get("bounded_observation_disposition"),
            consumed_prior_persisted_state=True,
        )
        cycle_seals.append(seal)
        session = {
            "schema_version": SESSION_SCHEMA,
            "branch_pins": branch_pins(),
            "workspace": follow,
            "workspace_content_hash": workspace_content_hash(follow),
            "cycle_seals": list(cycle_seals),
        }
        save_session(root, session)

    # Restart/reopen: reload final session and re-verify tip
    reopened_session = load_session(root)
    tip = reopened_session["workspace"]
    _verify_replay_non_drift(
        list(tip["events"]), expected_book=tip["book"], label="RESTART_REOPEN"
    )
    if len(reopened_session["cycle_seals"]) != cycles:
        _fail("RESTART_CYCLE_SEAL_COUNT_MISMATCH")

    # Reject duplicate cycle index seals
    indices = [row["cycle_index"] for row in cycle_seals]
    if len(indices) != len(set(indices)):
        _fail("DUPLICATE_CYCLE_INDEX")

    # Reject reordered seals: must be contiguous 0..n-1
    if indices != list(range(cycles)):
        _fail("CYCLE_ORDER_INVALID")

    # Event counts must strictly increase (persisted growth, not fixture reset)
    event_counts = [row["event_count"] for row in cycle_seals]
    for left, right in zip(event_counts, event_counts[1:], strict=False):
        if right <= left:
            _fail("EVENT_COUNT_DID_NOT_INCREASE_ACROSS_CYCLES")

    # Workspace hashes must change each cycle (new observation/cert)
    ws_hashes = [row["workspace_content_hash"] for row in cycle_seals]
    if len(set(ws_hashes)) != cycles:
        _fail("WORKSPACE_HASH_DID_NOT_CHANGE_ACROSS_CYCLES")

    # Cert chain: each cycle tip links prior
    for index in range(1, cycles):
        if cycle_seals[index]["prior_certification_id"] != cycle_seals[index - 1][
            "certification_id"
        ]:
            _fail(f"CERT_CHAIN_BREAK_AT_CYCLE_{index}")

    correction = run_correction_lineage_probe(tip)

    report_body = {
        "schema_version": BOUNDED_SCHEMA,
        "claim_boundary": BOUNDED_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "cycle_count": cycles,
        "declared_security_count": DECLARED_SECURITY_COUNT,
        "cycles": cycle_seals,
        "persisted_session_path": str(session_path(root)),
        "consumed_prior_persisted_state": all(
            row["consumed_prior_persisted_state"] for row in cycle_seals
        ),
        "event_counts_strictly_increasing": True,
        "certification_chain_intact": True,
        "restart_reopen_verified": True,
        "correction_lineage_probe": correction,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "terminal_nav": cycle_seals[-1]["terminal_nav"],
        "unexplained_residual": cycle_seals[-1]["unexplained_residual"],
        "final_workspace_content_hash": reopened_session["workspace_content_hash"],
    }
    report_body["report_hash"] = domain_hash(
        f"{ID_DOMAIN}:BOUNDED_REPORT:V1", report_body
    )
    return report_body


def assert_replay_baseline_pins() -> None:
    pins = branch_pins()
    if pins["replay_code_pin_sha"] != REPLAY_CODE_PIN_SHA:
        _fail("REPLAY_CODE_PIN_TAMPERED")
    if pins["promotion_tip_sha"] != PROMOTION_TIP_SHA:
        _fail("PROMOTION_TIP_PIN_TAMPERED")
    if pins["active_implementation_base"] == pins["replay_code_pin_sha"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
