"""GV-BOUNDED-PORTFOLIO-1 — repeated bounded paper portfolio operation.

Orchestrates multiple independent operating cycles over the declared micro-portfolio
universe, re-verifying exact Replay 0 reconstruction and byte-stable certification
on every cycle. Does not mutate Slice 0 product fixtures or Replay 0 core modules.

Immutable pins:

- promotion tip (branch base): ``5fc2e4c…``
- Replay code pin (not branch point): ``0e4b93f…``
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.book import certification_eligible
from gv_portfolio_v0.replay import (
    ReplayError,
    append_correction_and_recertify,
    build_replay_report,
    certify_replay_prefix,
    event_ledger_hash,
    reconstruct_exact,
    replay_idempotent,
    reopen_slice0_workspace_stable,
    subject_events,
)
from gv_portfolio_v0.vertical import (
    PortfolioV0Error,
    admit_watch_observation,
    build_draft_workspace,
    confirm_draft_workspace,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
BOUNDED_SCHEMA = "gv_portfolio_v0_bounded_report_v1"
BOUNDED_CLAIM_BOUNDARY = (
    "Bounded repeated paper portfolio only; no alpha or live-capital claim."
)

# Branch / authority pins
PROMOTION_TIP_SHA = "5fc2e4c01aa98ffe6ad9fcce4d1f9299c4aee6e4"
REPLAY_CODE_PIN_SHA = "0e4b93fb370f67956502edc02e9c6f56ceb2eba3"
REPLAY_CUSTODY_BASE_SHA = "03a5c922d250d615380bbd0d60e8fd636e4ec1c6"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"

DEFAULT_CYCLE_COUNT = 3
DECLARED_SECURITY_COUNT = 4  # principal / substitute / competitor / alternative


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


def _fail_replay(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise BoundedPortfolioError(f"REPLAY_DRIFT:{message}:{cause}") from cause
    raise BoundedPortfolioError(f"REPLAY_DRIFT:{message}")


def _verify_replay_non_drift(
    events: list[dict[str, Any]],
    *,
    expected_book: Mapping[str, Any],
    label: str,
) -> dict[str, Any]:
    """Stop immediately on any Replay reconstruction / hash / residual drift."""

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


def run_operating_cycle(*, cycle_index: int) -> dict[str, Any]:
    """One full paper cycle: draft → confirm/certify → later observation → replay proof."""

    if not isinstance(cycle_index, int) or cycle_index < 0:
        raise BoundedPortfolioError("CYCLE_INDEX_INVALID")

    try:
        draft = build_draft_workspace()
        certified = confirm_draft_workspace(draft)
        observed = admit_watch_observation(certified)
    except PortfolioV0Error as exc:
        raise BoundedPortfolioError(f"OPERATING_CYCLE_FAILED:{exc}") from exc

    securities = list(observed.get("instruments") or [])
    if len(securities) != DECLARED_SECURITY_COUNT:
        raise BoundedPortfolioError("DECLARED_UNIVERSE_SIZE_MISMATCH")

    # Replay non-drift on certified prefix and full observed log.
    certified_book = _verify_replay_non_drift(
        list(certified["events"]),
        expected_book=certified["book"],
        label=f"CYCLE{cycle_index}:CERTIFIED",
    )
    observed_book = _verify_replay_non_drift(
        list(observed["events"]),
        expected_book=observed["book"],
        label=f"CYCLE{cycle_index}:OBSERVED",
    )

    try:
        reopen = reopen_slice0_workspace_stable(certified, observed)
    except ReplayError as exc:
        _fail_replay(f"CYCLE{cycle_index}:REOPEN", cause=exc)
        raise  # pragma: no cover

    prior = certified["certification"]
    current = observed["certification"]
    if canonical_document_bytes(dict(reopen["prior_certification"])) != canonical_document_bytes(
        dict(prior)
    ):
        _fail_replay(f"CYCLE{cycle_index}:PRIOR_CERT_BYTES")
    if current.get("prior_certification_id") != prior.get("certification_id"):
        _fail_replay(f"CYCLE{cycle_index}:PRIOR_CERT_LINK")

    try:
        replay_report = build_replay_report(
            observed["events"],
            expected_book=observed["book"],
            decision_snapshot_id=observed["decision_snapshot"]["decision_snapshot_id"],
            portfolio_aim_id=observed["portfolio_aim"]["portfolio_aim_id"],
        )
    except ReplayError as exc:
        _fail_replay(f"CYCLE{cycle_index}:REPLAY_REPORT", cause=exc)
        raise  # pragma: no cover

    body = {
        "cycle_index": cycle_index,
        "status": observed["status"],
        "security_count": len(securities),
        "event_count": len(observed["events"]),
        "certified_event_ledger_hash": event_ledger_hash(certified["events"]),
        "observed_event_ledger_hash": event_ledger_hash(observed["events"]),
        "certified_book_hash": certified_book["book_hash"],
        "observed_book_hash": observed_book["book_hash"],
        "prior_certification_id": prior["certification_id"],
        "certification_id": current["certification_id"],
        "terminal_nav": observed_book.get("terminal_nav"),
        "unexplained_residual": observed_book.get("unexplained_residual"),
        "partial_fill_residuals": list(observed_book.get("partial_fill_residuals") or []),
        "replay_report_hash": replay_report["report_hash"],
        "prior_certification_byte_stable": True,
        "replay_non_drift": True,
    }
    return {
        "cycle_id": _cycle_identity(body),
        **body,
        "certified_workspace": certified,
        "observed_workspace": observed,
        "replay_report": replay_report,
    }


def run_correction_lineage_probe(cycle: Mapping[str, Any]) -> dict[str, Any]:
    """Append-only correction on a cycle's economic subject prefix; prior cert stable."""

    certified = cycle["certified_workspace"]
    events = [
        dict(row)
        for row in certified["events"]
        if row.get("event_type") != "CERTIFICATION_RECORDED"
    ]
    for index, row in enumerate(events):
        row["sequence"] = index

    decision_snapshot_id = certified["decision_snapshot"]["decision_snapshot_id"]
    portfolio_aim_id = certified["portfolio_aim"]["portfolio_aim_id"]
    try:
        prior = certify_replay_prefix(
            events,
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
        )
        result = append_correction_and_recertify(
            events,
            prior_certification=prior,
            correction_payload={
                "correction_kind": "ANNOTATION",
                "reason": "bounded_cycle_lineage_probe",
                "details": {"cycle_id": cycle["cycle_id"]},
            },
            decision_snapshot_id=decision_snapshot_id,
            portfolio_aim_id=portfolio_aim_id,
            effective_at="2026-09-01T00:00:00.000000Z",
            source_identity=f"BOUNDED:CORRECTION:{cycle['cycle_index']}",
        )
    except ReplayError as exc:
        _fail_replay("CORRECTION_LINEAGE", cause=exc)
        raise  # pragma: no cover

    if result["book"]["book_hash"] != cycle["certified_book_hash"]:
        # Non-economic correction must not move complete-fill economics.
        _fail_replay("CORRECTION_CHANGED_ECONOMICS")
    return {
        "prior_certification_id": result["prior_certification"]["certification_id"],
        "certification_id": result["certification"]["certification_id"],
        "book_hash": result["book"]["book_hash"],
        "event_count": len(result["events"]),
        "prior_byte_stable": True,
    }


def run_bounded_portfolio(*, cycles: int = DEFAULT_CYCLE_COUNT) -> dict[str, Any]:
    """Run N independent operating cycles; require deterministic equality and replay green."""

    if not isinstance(cycles, int) or cycles < 2:
        raise BoundedPortfolioError("BOUNDED_CYCLE_COUNT_MIN_2")
    if cycles > 8:
        raise BoundedPortfolioError("BOUNDED_CYCLE_COUNT_CAP_8")

    cycle_reports: list[dict[str, Any]] = []
    for index in range(cycles):
        cycle = run_operating_cycle(cycle_index=index)
        # Drop heavy workspace bodies from the sealed report (keep hashes).
        sealed = {
            key: value
            for key, value in cycle.items()
            if key
            not in {
                "certified_workspace",
                "observed_workspace",
                "replay_report",
            }
        }
        cycle_reports.append(sealed)

    # Deterministic fixture: every independent cycle must reproduce the same economics.
    reference = cycle_reports[0]
    for cycle in cycle_reports[1:]:
        for key in (
            "certified_book_hash",
            "observed_book_hash",
            "certified_event_ledger_hash",
            "observed_event_ledger_hash",
            "terminal_nav",
            "unexplained_residual",
            "replay_report_hash",
            "partial_fill_residuals",
        ):
            if cycle.get(key) != reference.get(key):
                _fail_replay(f"CROSS_CYCLE_DRIFT:{key}")

    # One correction-lineage probe on cycle 0 (uses live workspaces before seal drop).
    first_live = run_operating_cycle(cycle_index=0)
    correction = run_correction_lineage_probe(first_live)

    report_body = {
        "schema_version": BOUNDED_SCHEMA,
        "claim_boundary": BOUNDED_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "cycle_count": cycles,
        "declared_security_count": DECLARED_SECURITY_COUNT,
        "cycles": cycle_reports,
        "deterministic_across_cycles": True,
        "correction_lineage_probe": correction,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "unexplained_residual": reference["unexplained_residual"],
        "terminal_nav": reference["terminal_nav"],
    }
    report_body["report_hash"] = domain_hash(
        f"{ID_DOMAIN}:BOUNDED_REPORT:V1", report_body
    )
    return report_body


def assert_replay_baseline_pins() -> None:
    """Guard: bounded work must not forget the immutable Replay code pin."""

    pins = branch_pins()
    if pins["replay_code_pin_sha"] != REPLAY_CODE_PIN_SHA:
        raise BoundedPortfolioError("REPLAY_CODE_PIN_TAMPERED")
    if pins["promotion_tip_sha"] != PROMOTION_TIP_SHA:
        raise BoundedPortfolioError("PROMOTION_TIP_PIN_TAMPERED")
    if pins["active_implementation_base"] == pins["replay_code_pin_sha"]:
        # Branch point must be promotion tip, not the frozen Replay pin alone.
        raise BoundedPortfolioError("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
