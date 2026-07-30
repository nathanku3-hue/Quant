"""GV-UNIVERSE-SCALE-1 — declared security universe above Portfolio Scale slots.

Expands paper portfolio operation across a declared universe whose security
slot count exceeds Portfolio Scale 1's multi-session fixture slots
(DEFAULT_SCALE_PORTFOLIOS × 4). Each universe cell is a full persisted
Bounded multi-cycle session. An embedded Scale control re-runs frozen
``run_portfolio_scale`` for non-drift. Does not mutate Scale/Bounded/Replay.

Immutable pins:

- promotion tip (branch base): ``133b632…``
- Scale terminal pin: ``c37abf0…``
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
from gv_portfolio_v0.scale import (
    DEFAULT_SCALE_PORTFOLIOS,
    PortfolioScaleError,
    run_portfolio_scale,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
UNIVERSE_SCHEMA = "gv_portfolio_v0_universe_report_v1"
UNIVERSE_CLAIM_BOUNDARY = (
    "Universe-scale paper multi-cell operation only; no alpha or live capital."
)

# Branch / authority pins
PROMOTION_TIP_SHA = "133b6326b74af35388730662206a6495125d4474"
SCALE_TERMINAL_SHA = "c37abf00293937b9b99eb6e560f6b5b77a92ea1f"
BOUNDED_TERMINAL_SHA = "abaa814ce99ea78afadc33dd40506f4e13a742ef"
REPLAY_CODE_PIN_SHA = "0e4b93fb370f67956502edc02e9c6f56ceb2eba3"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"

# Portfolio Scale 1 multi-session fixture slot baseline (3 × 4 = 12).
SCALE_MULTI_SESSION_SECURITY_SLOTS = (
    DEFAULT_SCALE_PORTFOLIOS * DECLARED_SECURITY_COUNT
)

# Universe: cells × 4 securities must exceed Scale multi-session slots.
DEFAULT_UNIVERSE_CELLS = 4  # 4 × 4 = 16 > 12
DEFAULT_CYCLES_PER_CELL = DEFAULT_CYCLE_COUNT  # 3

# Embedded Scale control (frozen scale path) — reduced for runtime, still valid.
SCALE_CONTROL_PORTFOLIOS = 2  # min valid scale
SCALE_CONTROL_CYCLES = 2


class UniverseScaleError(ValueError):
    """Fail-closed universe scale error."""


def branch_pins() -> dict[str, str]:
    return {
        "promotion_tip_sha": PROMOTION_TIP_SHA,
        "scale_terminal_sha": SCALE_TERMINAL_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "slice0_terminal_sha": SLICE0_TERMINAL_SHA,
        "active_implementation_base": PROMOTION_TIP_SHA,
        "immutable_scale_code_pin": SCALE_TERMINAL_SHA,
        "immutable_bounded_code_pin": BOUNDED_TERMINAL_SHA,
        "immutable_replay_code_pin": REPLAY_CODE_PIN_SHA,
    }


def _fail(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise UniverseScaleError(f"UNIVERSE_FAIL:{message}:{cause}") from cause
    raise UniverseScaleError(f"UNIVERSE_FAIL:{message}")


def _fail_drift(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise UniverseScaleError(f"DRIFT:{message}:{cause}") from cause
    raise UniverseScaleError(f"DRIFT:{message}")


def assert_universe_pins() -> None:
    pins = branch_pins()
    if pins["promotion_tip_sha"] != PROMOTION_TIP_SHA:
        _fail("PROMOTION_TIP_PIN_TAMPERED")
    if pins["scale_terminal_sha"] != SCALE_TERMINAL_SHA:
        _fail("SCALE_TERMINAL_PIN_TAMPERED")
    if pins["bounded_terminal_sha"] != BOUNDED_TERMINAL_SHA:
        _fail("BOUNDED_TERMINAL_PIN_TAMPERED")
    if pins["replay_code_pin_sha"] != REPLAY_CODE_PIN_SHA:
        _fail("REPLAY_CODE_PIN_TAMPERED")
    if pins["active_implementation_base"] == pins["immutable_scale_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_bounded_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_replay_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if SCALE_MULTI_SESSION_SECURITY_SLOTS != (
        DEFAULT_SCALE_PORTFOLIOS * DECLARED_SECURITY_COUNT
    ):
        _fail("SCALE_SLOT_BASELINE_TAMPERED")


def _cell_root(root: Path, cell_index: int) -> Path:
    return Path(root) / f"cell_{cell_index:02d}"


def _scale_control_root(root: Path) -> Path:
    return Path(root) / "scale_control"


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


def _seal_universe_cell(
    *,
    cell_index: int,
    bounded_report: Mapping[str, Any],
    session: Mapping[str, Any],
    session_root: Path,
) -> dict[str, Any]:
    if bounded_report.get("schema_version") != BOUNDED_SCHEMA:
        _fail(f"CELL{cell_index}:BOUNDED_SCHEMA_MISMATCH")
    if not bounded_report.get("consumed_prior_persisted_state"):
        _fail(f"CELL{cell_index}:DID_NOT_CONSUME_PRIOR_STATE")
    if not bounded_report.get("event_counts_strictly_increasing"):
        _fail(f"CELL{cell_index}:EVENT_COUNTS_NOT_INCREASING")
    if not bounded_report.get("certification_chain_intact"):
        _fail(f"CELL{cell_index}:CERT_CHAIN_BROKEN")
    if not bounded_report.get("restart_reopen_verified"):
        _fail(f"CELL{cell_index}:RESTART_NOT_VERIFIED")
    if bounded_report.get("unexplained_residual") != "0":
        _fail_drift(f"CELL{cell_index}:RESIDUAL")
    if bounded_report.get("terminal_nav") != "1499":
        _fail_drift(f"CELL{cell_index}:NAV")
    if bounded_report.get("declared_security_count") != DECLARED_SECURITY_COUNT:
        _fail(f"CELL{cell_index}:CELL_SECURITY_COUNT")

    _verify_session_replay_non_drift(session, label=f"CELL{cell_index}:SESSION")

    cycles = list(bounded_report.get("cycles") or [])
    body = {
        "cell_index": cell_index,
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
    body["cell_seal_id"] = "UCL_" + domain_hash(
        f"{ID_DOMAIN}:UNIVERSE_CELL_SEAL:V1", body
    )
    return body


def run_universe_scale(
    *,
    root: Path,
    cells: int = DEFAULT_UNIVERSE_CELLS,
    cycles_per_cell: int = DEFAULT_CYCLES_PER_CELL,
    scale_control_portfolios: int = SCALE_CONTROL_PORTFOLIOS,
    scale_control_cycles: int = SCALE_CONTROL_CYCLES,
) -> dict[str, Any]:
    """Run declared-universe multi-cell operation above Scale multi-session slots."""

    assert_universe_pins()
    root = Path(root)
    if not isinstance(cells, int) or cells < 2:
        _fail("UNIVERSE_CELLS_MIN_2")
    if cells > 32:
        _fail("UNIVERSE_CELLS_CAP_32")
    if not isinstance(cycles_per_cell, int) or cycles_per_cell < 2:
        _fail("UNIVERSE_CYCLES_MIN_2")
    if cycles_per_cell > 8:
        _fail("UNIVERSE_CYCLES_CAP_8")

    declared_universe_security_slots = cells * DECLARED_SECURITY_COUNT
    if declared_universe_security_slots <= SCALE_MULTI_SESSION_SECURITY_SLOTS:
        _fail("UNIVERSE_MUST_EXCEED_SCALE_SLOTS")

    if any(_cell_root(root, i).exists() for i in range(cells)):
        _fail("UNIVERSE_ROOT_ALREADY_POPULATED")
    if _scale_control_root(root).exists():
        _fail("UNIVERSE_ROOT_ALREADY_POPULATED")

    # --- Embedded Scale non-drift control (frozen scale.py path) ---
    scale_root = _scale_control_root(root)
    scale_root.mkdir(parents=True, exist_ok=False)
    try:
        scale_report = run_portfolio_scale(
            root=scale_root,
            portfolios=scale_control_portfolios,
            cycles_per_portfolio=scale_control_cycles,
        )
    except PortfolioScaleError as exc:
        _fail("SCALE_CONTROL_FAILED", cause=exc)
        raise  # pragma: no cover
    if scale_report.get("unexplained_residual") != "0":
        _fail_drift("SCALE_CONTROL_RESIDUAL")
    if scale_report.get("terminal_nav") != "1499":
        _fail_drift("SCALE_CONTROL_NAV")
    if not scale_report.get("cross_portfolio_economic_determinism"):
        _fail_drift("SCALE_CONTROL_CROSS_PORTFOLIO")
    if not scale_report.get("restart_reopen_verified_at_scale"):
        _fail_drift("SCALE_CONTROL_RESTART")

    # --- Universe cells (declared slots > Scale multi-session baseline) ---
    cell_seals: list[dict[str, Any]] = []
    for index in range(cells):
        session_root = _cell_root(root, index)
        session_root.mkdir(parents=True, exist_ok=False)
        try:
            bounded_report = run_bounded_portfolio(
                root=session_root, cycles=cycles_per_cell
            )
        except BoundedPortfolioError as exc:
            _fail(f"CELL{index}:BOUNDED_FAILED", cause=exc)
            raise  # pragma: no cover
        try:
            session = load_session(session_root)
        except BoundedPortfolioError as exc:
            _fail(f"CELL{index}:SESSION_RELOAD_FAILED", cause=exc)
            raise  # pragma: no cover
        seal = _seal_universe_cell(
            cell_index=index,
            bounded_report=bounded_report,
            session=session,
            session_root=session_root,
        )
        cell_seals.append(seal)

    # Cross-cell path-free economic determinism.
    reference = cell_seals[0]
    for seal in cell_seals[1:]:
        for key in (
            "final_workspace_content_hash",
            "terminal_nav",
            "unexplained_residual",
            "event_counts",
            "cycle_ids",
            "certification_ids",
        ):
            if seal.get(key) != reference.get(key):
                _fail_drift(f"CROSS_CELL_DRIFT:{key}")
        if seal.get("session_path") == reference.get("session_path"):
            _fail("CROSS_CELL_SESSION_PATH_COLLISION")

    # Restart/reopen at universe: reload every cell and re-verify Replay.
    for index in range(cells):
        session_root = _cell_root(root, index)
        try:
            reloaded = load_session(session_root)
        except BoundedPortfolioError as exc:
            _fail_drift(f"RESTART_CELL{index}", cause=exc)
            raise  # pragma: no cover
        _verify_session_replay_non_drift(reloaded, label=f"RESTART_CELL{index}")
        if reloaded.get("workspace_content_hash") != cell_seals[index][
            "final_workspace_content_hash"
        ]:
            _fail_drift(f"RESTART_HASH_MISMATCH_CELL{index}")

    indices = [row["cell_index"] for row in cell_seals]
    if indices != list(range(cells)):
        _fail("CELL_ORDER_INVALID")
    seal_ids = [row["cell_seal_id"] for row in cell_seals]
    if len(seal_ids) != len(set(seal_ids)):
        _fail("DUPLICATE_CELL_SEAL_ID")

    report = {
        "schema_version": UNIVERSE_SCHEMA,
        "claim_boundary": UNIVERSE_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "cell_count": cells,
        "cycles_per_cell": cycles_per_cell,
        "declared_security_count_per_cell": DECLARED_SECURITY_COUNT,
        "declared_universe_security_slots": declared_universe_security_slots,
        "scale_multi_session_security_slots": SCALE_MULTI_SESSION_SECURITY_SLOTS,
        "exceeds_scale_multi_session_slots": True,
        "exceeds_bounded_v1_universe": True,
        "cells": cell_seals,
        "cross_cell_economic_determinism": True,
        "restart_reopen_verified_at_universe": True,
        "scale_control": {
            "portfolio_count": scale_report["portfolio_count"],
            "cycles_per_portfolio": scale_report["cycles_per_portfolio"],
            "declared_scale_security_slots": scale_report[
                "declared_scale_security_slots"
            ],
            "report_hash": scale_report["report_hash"],
            "cross_portfolio_economic_determinism": True,
            "restart_reopen_verified_at_scale": True,
            "terminal_nav": scale_report["terminal_nav"],
            "unexplained_residual": scale_report["unexplained_residual"],
        },
        "scale_non_drift": True,
        "scale_terminal_sha": SCALE_TERMINAL_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "terminal_nav": reference["terminal_nav"],
        "unexplained_residual": reference["unexplained_residual"],
    }
    report["report_hash"] = domain_hash(f"{ID_DOMAIN}:UNIVERSE_REPORT:V1", report)
    return report
