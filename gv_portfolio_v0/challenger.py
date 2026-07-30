"""GV-CHALLENGER-PROMOTION-1 — shadow-first challenger promotion.

Shadow-only prospective challenger evidence against certified custody.
Embeds frozen Universe control (which re-runs Scale + Bounded + Replay) and
proves the challenger path cannot mutate certified sessions without an
explicit disposition. Live capital and production promotion are fail-closed.

Immutable pins:

- promotion tip (branch base): ``cf77110…``
- Universe terminal pin: ``dca67e3…``
- Scale terminal pin: ``c37abf0…``
- Bounded terminal pin: ``abaa814…``
- Replay terminal pin: ``0e4b93f…``
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from gv_portfolio_v0.bounded import BoundedPortfolioError, load_session, session_path
from gv_portfolio_v0.replay import ReplayError, reconstruct_exact, replay_idempotent
from gv_portfolio_v0.universe import (
    DEFAULT_UNIVERSE_CELLS,
    UniverseScaleError,
    run_universe_scale,
)

ID_DOMAIN = "GV-PORTFOLIO-V0"
CHALLENGER_SCHEMA = "gv_portfolio_v0_challenger_shadow_report_v1"
CHALLENGER_CLAIM_BOUNDARY = (
    "Shadow-first challenger promotion only; no alpha claim, no live capital, "
    "no production capital mutation."
)

# Branch / authority pins
PROMOTION_TIP_SHA = "cf771107d726458df6fc956a05337583407c6091"
UNIVERSE_TERMINAL_SHA = "dca67e36edc02dddf8c7ba446ac34f22562ee165"
SCALE_TERMINAL_SHA = "c37abf00293937b9b99eb6e560f6b5b77a92ea1f"
BOUNDED_TERMINAL_SHA = "abaa814ce99ea78afadc33dd40506f4e13a742ef"
REPLAY_CODE_PIN_SHA = "0e4b93fb370f67956502edc02e9c6f56ceb2eba3"
SLICE0_TERMINAL_SHA = "85e6601742710f03e6cced7377b4be426cd4892f"

# Explicit dispositions
DISPOSITION_SHADOW_ONLY = "SHADOW_ONLY_NO_PRODUCTION_MUTATION"
DISPOSITION_LIVE = "LIVE_CAPITAL"  # forbidden; fail-closed
DISPOSITION_PRODUCTION_PROMOTE = "PRODUCTION_PROMOTE"  # forbidden; fail-closed

# Reduced but valid layered controls for challenger acceptance runtime
UNIVERSE_CONTROL_CELLS = 4  # 16 slots > Scale 12
UNIVERSE_CONTROL_CYCLES = 2
SCALE_CONTROL_PORTFOLIOS = 2
SCALE_CONTROL_CYCLES = 2

SHADOW_EVIDENCE_FILENAME = "challenger_shadow_evidence.json"


class ChallengerPromotionError(ValueError):
    """Fail-closed challenger promotion error."""


def branch_pins() -> dict[str, str]:
    return {
        "promotion_tip_sha": PROMOTION_TIP_SHA,
        "universe_terminal_sha": UNIVERSE_TERMINAL_SHA,
        "scale_terminal_sha": SCALE_TERMINAL_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "slice0_terminal_sha": SLICE0_TERMINAL_SHA,
        "active_implementation_base": PROMOTION_TIP_SHA,
        "immutable_universe_code_pin": UNIVERSE_TERMINAL_SHA,
        "immutable_scale_code_pin": SCALE_TERMINAL_SHA,
        "immutable_bounded_code_pin": BOUNDED_TERMINAL_SHA,
        "immutable_replay_code_pin": REPLAY_CODE_PIN_SHA,
    }


def _fail(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise ChallengerPromotionError(f"CHALLENGER_FAIL:{message}:{cause}") from cause
    raise ChallengerPromotionError(f"CHALLENGER_FAIL:{message}")


def _fail_drift(message: str, *, cause: Exception | None = None) -> None:
    if cause is not None:
        raise ChallengerPromotionError(f"DRIFT:{message}:{cause}") from cause
    raise ChallengerPromotionError(f"DRIFT:{message}")


def assert_challenger_pins() -> None:
    pins = branch_pins()
    if pins["promotion_tip_sha"] != PROMOTION_TIP_SHA:
        _fail("PROMOTION_TIP_PIN_TAMPERED")
    if pins["universe_terminal_sha"] != UNIVERSE_TERMINAL_SHA:
        _fail("UNIVERSE_TERMINAL_PIN_TAMPERED")
    if pins["scale_terminal_sha"] != SCALE_TERMINAL_SHA:
        _fail("SCALE_TERMINAL_PIN_TAMPERED")
    if pins["bounded_terminal_sha"] != BOUNDED_TERMINAL_SHA:
        _fail("BOUNDED_TERMINAL_PIN_TAMPERED")
    if pins["replay_code_pin_sha"] != REPLAY_CODE_PIN_SHA:
        _fail("REPLAY_CODE_PIN_TAMPERED")
    if pins["active_implementation_base"] == pins["immutable_universe_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_scale_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_bounded_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")
    if pins["active_implementation_base"] == pins["immutable_replay_code_pin"]:
        _fail("BRANCH_POINT_MUST_BE_PROMOTION_TIP")


def _custody_root(root: Path) -> Path:
    return Path(root) / "custody_control"


def _shadow_root(root: Path) -> Path:
    return Path(root) / "shadow"


def _shadow_evidence_path(root: Path) -> Path:
    return _shadow_root(root) / SHADOW_EVIDENCE_FILENAME


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


def _reject_live_disposition(disposition: str) -> None:
    if disposition in (DISPOSITION_LIVE, DISPOSITION_PRODUCTION_PROMOTE):
        _fail(f"LIVE_PATH_FORBIDDEN:{disposition}")
    if disposition != DISPOSITION_SHADOW_ONLY:
        _fail(f"DISPOSITION_NOT_SHADOW_ONLY:{disposition}")


def _write_shadow_evidence(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_document_bytes(dict(payload))
    path.write_bytes(raw)


def _assert_certified_sessions_unmutated(
    custody_root: Path,
    cell_seals: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Reload every certified cell session; hashes must match pre-shadow seals."""

    proofs: list[dict[str, Any]] = []
    for seal in cell_seals:
        index = int(seal["cell_index"])
        session_root = Path(seal["session_root"])
        try:
            session_root.resolve().relative_to(custody_root.resolve())
        except ValueError:
            _fail(f"CELL{index}:SESSION_OUTSIDE_CUSTODY")
        try:
            reloaded = load_session(session_root)
        except BoundedPortfolioError as exc:
            _fail_drift(f"POST_SHADOW_RELOAD_CELL{index}", cause=exc)
            raise  # pragma: no cover
        expected = seal["final_workspace_content_hash"]
        if reloaded.get("workspace_content_hash") != expected:
            _fail_drift(f"CERTIFIED_CUSTODY_MUTATED_CELL{index}")
        _verify_session_replay_non_drift(
            reloaded, label=f"POST_SHADOW_CELL{index}"
        )
        # Session file must still exist at sealed path identity
        if not session_path(session_root).is_file():
            _fail_drift(f"SESSION_FILE_MISSING_CELL{index}")
        proofs.append(
            {
                "cell_index": index,
                "workspace_content_hash": reloaded["workspace_content_hash"],
                "session_path": str(session_path(session_root)),
                "certified_unmutated": True,
                "replay_non_drift": True,
            }
        )
    return proofs


def run_challenger_shadow(
    *,
    root: Path,
    disposition: str = DISPOSITION_SHADOW_ONLY,
    challenger_label: str = "challenger_shadow_v1",
    universe_cells: int = UNIVERSE_CONTROL_CELLS,
    universe_cycles: int = UNIVERSE_CONTROL_CYCLES,
    scale_control_portfolios: int = SCALE_CONTROL_PORTFOLIOS,
    scale_control_cycles: int = SCALE_CONTROL_CYCLES,
) -> dict[str, Any]:
    """Run shadow-first challenger promotion against certified custody."""

    assert_challenger_pins()
    root = Path(root)
    _reject_live_disposition(disposition)

    if not isinstance(challenger_label, str) or not challenger_label.strip():
        _fail("CHALLENGER_LABEL_REQUIRED")
    if any(ch in challenger_label for ch in ("/", "\\", "..")):
        _fail("CHALLENGER_LABEL_PATH_CHARS_FORBIDDEN")

    if _custody_root(root).exists() or _shadow_root(root).exists():
        _fail("CHALLENGER_ROOT_ALREADY_POPULATED")

    # --- Layered non-drift: frozen Universe (Scale + Bounded + Replay) ---
    custody = _custody_root(root)
    custody.mkdir(parents=True, exist_ok=False)
    try:
        universe_report = run_universe_scale(
            root=custody,
            cells=universe_cells,
            cycles_per_cell=universe_cycles,
            scale_control_portfolios=scale_control_portfolios,
            scale_control_cycles=scale_control_cycles,
        )
    except UniverseScaleError as exc:
        _fail("UNIVERSE_CONTROL_FAILED", cause=exc)
        raise  # pragma: no cover

    if universe_report.get("unexplained_residual") != "0":
        _fail_drift("UNIVERSE_CONTROL_RESIDUAL")
    if universe_report.get("terminal_nav") != "1499":
        _fail_drift("UNIVERSE_CONTROL_NAV")
    if not universe_report.get("cross_cell_economic_determinism"):
        _fail_drift("UNIVERSE_CONTROL_CROSS_CELL")
    if not universe_report.get("scale_non_drift"):
        _fail_drift("UNIVERSE_CONTROL_SCALE_DRIFT")
    if not universe_report.get("restart_reopen_verified_at_universe"):
        _fail_drift("UNIVERSE_CONTROL_RESTART")

    certified_cell_seals = list(universe_report.get("cells") or [])
    if len(certified_cell_seals) != universe_cells:
        _fail("UNIVERSE_CELL_COUNT_MISMATCH")

    pre_shadow_hashes = [
        {
            "cell_index": row["cell_index"],
            "final_workspace_content_hash": row["final_workspace_content_hash"],
            "certification_ids": list(row["certification_ids"]),
            "cycle_ids": list(row["cycle_ids"]),
        }
        for row in certified_cell_seals
    ]

    # --- Shadow evidence (prospective; no production mutation) ---
    shadow = _shadow_root(root)
    shadow.mkdir(parents=True, exist_ok=False)

    evidence_body = {
        "schema_version": "gv_portfolio_v0_challenger_shadow_evidence_v1",
        "challenger_label": challenger_label,
        "disposition": DISPOSITION_SHADOW_ONLY,
        "live_capital": False,
        "production_mutation": False,
        "broker_path": False,
        "alpha_claim": False,
        "claim_boundary": CHALLENGER_CLAIM_BOUNDARY,
        "certified_universe_report_hash": universe_report["report_hash"],
        "certified_terminal_nav": universe_report["terminal_nav"],
        "certified_unexplained_residual": universe_report["unexplained_residual"],
        "certified_cell_count": universe_report["cell_count"],
        "certified_cell_hashes": pre_shadow_hashes,
        "scale_control_report_hash": universe_report["scale_control"]["report_hash"],
        "prospective_comparison": {
            "mode": "SHADOW_ONLY",
            "notes": (
                "Prospective shadow comparison markers only; not product alpha, "
                "not calibrated score uplift, not live capital authorization."
            ),
            "baseline_nav": universe_report["terminal_nav"],
            "baseline_residual": universe_report["unexplained_residual"],
        },
        "universe_terminal_sha": UNIVERSE_TERMINAL_SHA,
        "scale_terminal_sha": SCALE_TERMINAL_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
    }
    evidence_body["evidence_id"] = "CSE_" + domain_hash(
        f"{ID_DOMAIN}:CHALLENGER_SHADOW_EVIDENCE:V1", evidence_body
    )
    evidence_path = _shadow_evidence_path(root)
    _write_shadow_evidence(evidence_path, evidence_body)

    # --- Prove certified custody unchanged after shadow write ---
    custody_proofs = _assert_certified_sessions_unmutated(
        custody, certified_cell_seals
    )

    # Shadow evidence must not live under certified cell session paths
    for seal in certified_cell_seals:
        certified_session = session_path(Path(seal["session_root"]))
        if evidence_path.resolve() == certified_session.resolve():
            _fail("SHADOW_OVERWROTE_CERTIFIED_SESSION")

    # Re-read shadow evidence and verify integrity
    loaded_evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    if loaded_evidence.get("evidence_id") != evidence_body["evidence_id"]:
        _fail_drift("SHADOW_EVIDENCE_ID_MISMATCH")
    if loaded_evidence.get("disposition") != DISPOSITION_SHADOW_ONLY:
        _fail_drift("SHADOW_EVIDENCE_DISPOSITION_TAMPERED")
    if loaded_evidence.get("live_capital") is not False:
        _fail("LIVE_CAPITAL_FLAG_SET")
    if loaded_evidence.get("production_mutation") is not False:
        _fail("PRODUCTION_MUTATION_FLAG_SET")

    report = {
        "schema_version": CHALLENGER_SCHEMA,
        "claim_boundary": CHALLENGER_CLAIM_BOUNDARY,
        "branch_pins": branch_pins(),
        "disposition": DISPOSITION_SHADOW_ONLY,
        "shadow_first": True,
        "live_capital_authorized": False,
        "limited_live_slice_closed": True,
        "production_mutation": False,
        "challenger_label": challenger_label,
        "shadow_evidence_path": str(evidence_path),
        "shadow_evidence_id": evidence_body["evidence_id"],
        "universe_control": {
            "report_hash": universe_report["report_hash"],
            "cell_count": universe_report["cell_count"],
            "declared_universe_security_slots": universe_report[
                "declared_universe_security_slots"
            ],
            "exceeds_scale_multi_session_slots": universe_report[
                "exceeds_scale_multi_session_slots"
            ],
            "cross_cell_economic_determinism": True,
            "scale_non_drift": True,
            "restart_reopen_verified_at_universe": True,
            "terminal_nav": universe_report["terminal_nav"],
            "unexplained_residual": universe_report["unexplained_residual"],
        },
        "certified_custody_unmutated": True,
        "certified_custody_proofs": custody_proofs,
        "append_only_shadow_evidence": True,
        "universe_non_drift": True,
        "scale_non_drift": True,
        "bounded_non_drift": True,
        "replay_non_drift": True,
        "universe_terminal_sha": UNIVERSE_TERMINAL_SHA,
        "scale_terminal_sha": SCALE_TERMINAL_SHA,
        "bounded_terminal_sha": BOUNDED_TERMINAL_SHA,
        "replay_code_pin_sha": REPLAY_CODE_PIN_SHA,
        "terminal_nav": universe_report["terminal_nav"],
        "unexplained_residual": universe_report["unexplained_residual"],
    }
    report["report_hash"] = domain_hash(
        f"{ID_DOMAIN}:CHALLENGER_SHADOW_REPORT:V1", report
    )
    return report


def reject_live_promotion(*, disposition: str) -> None:
    """Public fail-closed helper: any live/production disposition is rejected."""

    _reject_live_disposition(disposition)
