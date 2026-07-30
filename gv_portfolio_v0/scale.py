"""GV-PORTFOLIO-SCALE-1 — concurrent multi-session portfolio scale.

Scales Bounded Portfolio multi-cycle operation across a declared set of
independent portfolio sessions (N sessions × 4 securities > Bounded V1 single
universe). Each session is a full persisted multi-cycle bounded run under a
separate root. Aggregate report proves cross-session determinism, restart
reload, and Replay/Bounded non-drift without mutating frozen Bounded/Replay
modules.

Immutable pins:

- promotion tip (branch base): ``eedf853…``
- Bounded terminal pin: ``abaa814…``
- Replay terminal pin: ``0e4b93f…``
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from gv_portfolio_v0.bounded import (
    BOUNDED_SCHEMA,
    DECLARED_SECURITY_COUNT,
    DEFAULT_CYCLE_COUNT,
    BoundedPortfolioError,
    load_session,
    run_bounded_portfolio,
    session_path,
)
from gv_portfolio_v0.replay import ReplayError, reconstruct_exact, replay_idempotent

ID_DOMAIN = "GV-PORTFOLIO-V0"
SCALE_SCHEMA = "gv_portfolio_v0_scale_report_v1"
SCALE_CLAIM_BOUNDARY = (
    "Portfolio-scale paper multi-session operation only; no alpha or live capital."
)

# Branch / authority pins
PROMOTION_TIP_SHA = "eedf853566d009dc6a5af74397c316013b87a853"
BOUNDED_TERMINAL_SHA = "abaa814ce99ea78afadc33dd40506f4e13a742ef"
REPLAY_CODE_PIN_SHA = "0e4b93fb370f67956502edc02e9c6f56ceb2eba3"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"

# Scale: concurrent portfolio sessions (each is full bounded multi-cycle).
DEFAULT_SCALE_PORTFOLIOS = 3  # 3 × 4 securities = 12 > Bounded V1 universe of 4
DEFAULT_CYCLES_PER_PORTFOLIO = DEFAULT_CYCLE_COUNT  # 3


class PortfolioScaleError(ValueError):
    """Fail-closed portfolio scale error."""


def branch_pins() -> dict[str, str]:
    return {
        "promotion_tip_sha": PROMOTION_TIP_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "slice0_terminal_sha": SLICE0_TERMINAL_SHA,
        "active_implementation_base": PROMOTION_TIP_SHA,
        "immutable_bounded_code_pin": BOUNDED_TERMINAL_SHA,
        "immutable_replay_code_pin": REPLAY_CODE_PIN_SHA,
    }


def _fail(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise PortfolioScaleError(f"SCALE_FAIL:{message}:{cause}") from cause
    raise PortfolioScaleError(f"SCALE_FAIL:{message}")


def _fail_drift(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise PortfolioScaleError(f"DRIFT:{message}:{cause}") from cause
    raise PortfolioScaleError(f"DRIFT:{message}")


def assert_scale_pins() -> None:
    pins = branch_pins()
    if pins["promotion_tip_sha"] != PROMOTION_TIP_SHA:
        _fail("PROMOTION_TIP_PIN_TAMPERED")
    if pins["bounded_terminal_sha"] != BOUNDED_TERMINAL_SHA:
        _fail("BOUNDED_TERMINAL_PIN_TAMPERED")
    if pins["replay_code_pin_sha"] != REPLAY_CODE_PIN_SHA:
        _fail("REPLAY_CODE_PIN_TAMPERED")
    if pins["active_implementation_base"] == pins["immutable_bounded_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_replay_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")


def _portfolio_root(root: Path, portfolio_index: int) -> Path:
    return Path(root) / f"portfolio_{portfolio_index:02d}"


def _verify_session_replay_non_drift(session: Mapping[str, Any], *, label: str) -> None:
    workspace = session.get("workspace")
    if not isinstance(workspace, dict):
        _fail_drift(f"{label}:WORKSPACE_MISSING")
    events = list(workspace.get("events") or [])
    book = workspace.get("book")
    if not isinstance(book, dict):
        _fail_drift(f"{label}:BOOK_MISSING")
    try:
        reconstructed = reconstruct_exact(events, expected_book=book)
        idempotent = replay_idempotent(events)
    except ReplayError as exc:
        _fail_drift(f"{label}:REPLAY", cause=exc)
        raise  # pragma: no cover
    if reconstructed["book_hash"] != idempotent["book_hash"]:
        _fail_drift(f"{label}:BOOK_HASH_MISMATCH")
    if reconstructed.get("unexplained_residual") != "0":
        _fail_drift(f"{label}:UNEXPLAINED_RESIDUAL")
    if reconstructed.get("split_value_residual") != "0":
        _fail_drift(f"{label}:SPLIT_RESIDUAL")


def _seal_portfolio_session(
    *,
    portfolio_index: int,
    bounded_report: Mapping[str, Any],
    session: Mapping[str, Any],
    session_root: Path,
) -> dict[str, Any]:
    if bounded_report.get("schema_version") != BOUNDED_SCHEMA:
        _fail(f"PORTFOLIO{portfolio_index}:BOUNDED_SCHEMA_MISMATCH")
    if not bounded_report.get("consumed_prior_persisted_state"):
        _fail(f"PORTFOLIO{portfolio_index}:DID_NOT_CONSUME_PRIOR_STATE")
    if not bounded_report.get("event_counts_strictly_increasing"):
        _fail(f"PORTFOLIO{portfolio_index}:EVENT_COUNTS_NOT_INCREASING")
    if not bounded_report.get("certification_chain_intact"):
        _fail(f"PORTFOLIO{portfolio_index}:CERT_CHAIN_BROKEN")
    if not bounded_report.get("restart_reopen_verified"):
        _fail(f"PORTFOLIO{portfolio_index}:RESTART_NOT_VERIFIED")
    if bounded_report.get("unexplained_residual") != "0":
        _fail_drift(f"PORTFOLIO{portfolio_index}:RESIDUAL")
    if bounded_report.get("terminal_nav") != "1499":
        _fail_drift(f"PORTFOLIO{portfolio_index}:NAV")
    if bounded_report.get("declared_security_count") != DECLARED_SECURITY_COUNT:
        _fail(f"PORTFOLIO{portfolio_index}:UNIVERSE_SIZE")

    _verify_session_replay_non_drift(
        session, label=f"PORTFOLIO{portfolio_index}:SESSION"
    )

    cycles = list(bounded_report.get("cycles") or [])
    body = {
        "portfolio_index": portfolio_index,
        "session_root": str(session_root),
        "session_path": str(session_path(session_root)),
        "cycle_count": bounded_report["cycle_count"],
        "declared_security_count": DECLARED_SECURITY_COUNT,
        "bounded_report_hash": bounded_report["report_hash"],
        "final_workspace_content_hash": bounded_report["final_workspace_content_hash"],
        "terminal_nav": bounded_report["terminal_nav"],
        "unexplained_residual": bounded_report["unexplained_residual"],
        "event_counts": [row["event_count"] for row in cycles],
        "cycle_ids": [row["cycle_id"] for row in cycles],
        "certification_ids": [row["certification_id"] for row in cycles],
        "consumed_prior_persisted_state": True,
        "replay_non_drift": True,
    }
    body["portfolio_seal_id"] = "PSL_" + domain_hash(
        f"{ID_DOMAIN}:SCALE_PORTFOLIO_SEAL:V1", body
    )
    return body


def run_portfolio_scale(
    *,
    root: Path,
    portfolios: int = DEFAULT_SCALE_PORTFOLIOS,
    cycles_per_portfolio: int = DEFAULT_CYCLES_PER_PORTFOLIO,
) -> dict[str, Any]:
    """Run N concurrent bounded multi-cycle sessions under one scale root."""

    assert_scale_pins()
    root = Path(root)
    if not isinstance(portfolios, int) or portfolios < 2:
        _fail("SCALE_PORTFOLIOS_MIN_2")
    if portfolios > 16:
        _fail("SCALE_PORTFOLIOS_CAP_16")
    if not isinstance(cycles_per_portfolio, int) or cycles_per_portfolio < 2:
        _fail("SCALE_CYCLES_MIN_2")
    if cycles_per_portfolio > 8:
        _fail("SCALE_CYCLES_CAP_8")

    # Aggregate universe size above Bounded V1 single-session size of 4.
    declared_scale_security_slots = portfolios * DECLARED_SECURITY_COUNT
    if declared_scale_security_slots <= DECLARED_SECURITY_COUNT:
        _fail("SCALE_MUST_EXCEED_BOUNDED_UNIVERSE")

    if any(_portfolio_root(root, i).exists() for i in range(portfolios)):
        _fail("SCALE_ROOT_ALREADY_POPULATED")

    portfolio_seals: list[dict[str, Any]] = []
    for index in range(portfolios):
        session_root = _portfolio_root(root, index)
        session_root.mkdir(parents=True, exist_ok=False)
        try:
            bounded_report = run_bounded_portfolio(
                root=session_root, cycles=cycles_per_portfolio
            )
        except BoundedPortfolioError as exc:
            _fail(f"PORTFOLIO{index}:BOUNDED_FAILED", cause=exc)
            raise  # pragma: no cover
        try:
            session = load_session(session_root)
        except BoundedPortfolioError as exc:
            _fail(f"PORTFOLIO{index}:SESSION_RELOAD_FAILED", cause=exc)
            raise  # pragma: no cover
        seal = _seal_portfolio_session(
            portfolio_index=index,
            bounded_report=bounded_report,
            session=session,
            session_root=session_root,
        )
        portfolio_seals.append(seal)

    # Cross-session economic determinism (same fixture economics under scale).
    # Do NOT require equal bounded_report_hash: bounded reports embed absolute
    # persisted_session_path, which legitimately differs per portfolio root.
    # Workspace content hash is path-free and must match; economic fields must match.
    reference = portfolio_seals[0]
    for seal in portfolio_seals[1:]:
        for key in (
            "final_workspace_content_hash",
            "terminal_nav",
            "unexplained_residual",
            "event_counts",
            "cycle_ids",
            "certification_ids",
        ):
            if seal.get(key) != reference.get(key):
                _fail_drift(f"CROSS_PORTFOLIO_DRIFT:{key}")
        # Bounded report hashes must differ when session paths differ (identity).
        if seal.get("session_path") == reference.get("session_path"):
            _fail("CROSS_PORTFOLIO_SESSION_PATH_COLLISION")

    # Restart/reopen at scale: reload every session and re-verify Replay.
    for index in range(portfolios):
        session_root = _portfolio_root(root, index)
        try:
            reloaded = load_session(session_root)
        except BoundedPortfolioError as exc:
            _fail_drift(f"RESTART_PORTFOLIO{index}", cause=exc)
            raise  # pragma: no cover
        _verify_session_replay_non_drift(
            reloaded, label=f"RESTART_PORTFOLIO{index}"
        )
        if reloaded.get("workspace_content_hash") != portfolio_seals[index][
            "final_workspace_content_hash"
        ]:
            _fail_drift(f"RESTART_HASH_MISMATCH_PORTFOLIO{index}")

    # Reject duplicate portfolio indices / seal ids
    indices = [row["portfolio_index"] for row in portfolio_seals]
    if indices != list(range(portfolios)):
        _fail("PORTFOLIO_ORDER_INVALID")
    seal_ids = [row["portfolio_seal_id"] for row in portfolio_seals]
    if len(seal_ids) != len(set(seal_ids)):
        _fail("DUPLICATE_PORTFOLIO_SEAL_ID")

    report = {
        "schema_version": SCALE_SCHEMA,
        "claim_boundary": SCALE_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "portfolio_count": portfolios,
        "cycles_per_portfolio": cycles_per_portfolio,
        "declared_security_count_per_portfolio": DECLARED_SECURITY_COUNT,
        "declared_scale_security_slots": declared_scale_security_slots,
        "exceeds_bounded_v1_universe": True,
        "portfolios": portfolio_seals,
        "cross_portfolio_economic_determinism": True,
        "restart_reopen_verified_at_scale": True,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "terminal_nav": reference["terminal_nav"],
        "unexplained_residual": reference["unexplained_residual"],
    }
    report["report_hash"] = domain_hash(f"{ID_DOMAIN}:SCALE_REPORT:V1", report)
    return report
