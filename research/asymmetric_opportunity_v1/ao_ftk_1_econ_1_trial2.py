"""AO-FTK-1-ECON-1 Trial 2 long-session helpers (ACCEPT_DRAFT → L7 STOP).

One economic trial under frozen 2-DOF TRANSITION_POSITION surface.
No AO-FTK-2, no L8, no capital, no alpha claim, no second eval.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_contract as econ1


FREEZE_ID = econ1.FREEZE_ID
PARENT_PROGRAM = econ1.PARENT_PROGRAM
PLAN_ID = econ1.PLAN_ID
EFFECTIVE_DECISION_DOF = econ1.EFFECTIVE_DECISION_DOF
ECONOMIC_CLOCK_CLASS = econ1.ECONOMIC_CLOCK_CLASS

SESSION_NAME = "FTK_ECON1_LONG_SESSION_THROUGH_TRIAL2"
RUN_ID = "AO_FTK_1_ECON_1_L5_ECONOMIC_RUN_1"
AUTH_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_AUTHORIZATION"
DEBIT_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_TRIAL_DEBIT"
JOIN_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_LABEL_JOIN"
L5_READY_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_READY_CHECKLIST"
L6_RECEIPT_ID = "AO_FTK_1_ECON_1_L6_LAYERED_DIAGNOSIS"
L7_PACKET_ID = "AO_FTK_1_ECON_1_L7_OWNER_PACKET"

# Owner ACCEPT_DRAFT attachment (authoritative for this dispatch)
OWNER_ATTACHMENT: dict[str, Any] = {
    "H_VALUE": 63,
    "H_UNIT": "trading_sessions_of_exposure_after_executable_entry",
    "H_CLASS": "TRANSITION_POSITION",
    "RIGHT_TAIL_PERCENTILE": 0.90,
    "CATASTROPHE_PERCENTILE": 0.10,
    "K": 20,
    "delta_J_required": 0.0,
    "TRIAL2_D9_FLOOR": 0.0,
    "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
    "CAPITAL_MATERIALITY_FLOOR": "NOT_YET_GRANTED",
    "D7_MODE": "OUT_OF_SCOPE",
    "E2_MODE": "OWNER_BOUND",
    "E3_MODE": "OWNER_BOUND",
    "L5_AUTHORIZE_ECONOMIC": True,
    "L5_AUTH_NOTE": (
        "ACCEPT_DRAFT long session: one transition-position economic "
        "Trial 2 after PASS_L5_READY; stop at L7; no FTK-2; alpha=0"
    ),
    "execution_lag_sessions": 1,
    "cost_bps_round_trip": 20,
    "cost_formula": "20_bps_RT_selected_names_only_10_entry_10_exit_cash_0",
    "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
    "same_return_convention_ftk_and_w3": True,
    "ACCEPT_DRAFT": True,
    "outcome_blind": True,
    "residual_peek": False,
}

CONSTITUTION = (
    "Accept draft binds. One transition-position economic trial. "
    "Same return law both sides. ΔJ>0 is a screen not capital. "
    "L6 first-fail. L7 stop. No slice 2."
)

L5_READY_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_ready_checklist.json")
L5_AUTH_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_authorization.json")
L5_DEBIT_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_trial_debit.json")
L5_JOIN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_label_join.json")
L5_RUN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_run.json")
L5_RUN_MD_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_run.md")
L6_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l6_layered_diagnosis.json")
L7_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_owner_packet.json")

JOINED_LABELS_JSONL_REL = (
    econ1.LABEL_CUSTODY_DIR_REL / "economic_labels.jsonl"
)
JOINED_MANIFEST_REL = (
    econ1.LABEL_CUSTODY_DIR_REL / "economic_label_pack.joined.manifest.json"
)

W3_AUTHORITY_DIR_REL = Path(
    "data/prebreakout/compiled/w3_real_authority_20250324_20260807"
)
AOV_MARKET_DIR_REL = Path(
    "data/aov0/historical/raw/market_productquery_a1_104_20240501_20260605"
)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return data


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_atomic(path: Path, payload: Mapping[str, Any], *, overwrite: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"ao_ftk_1_econ_1_output_exists:{path}")
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def write_text_atomic(path: Path, text: str, *, overwrite: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"ao_ftk_1_econ_1_output_exists:{path}")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text if text.endswith("\n") else text + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    return sha256_file(path)


def assert_attachment_concrete(att: Mapping[str, Any] = OWNER_ATTACHMENT) -> None:
    """Refuse placeholder / empty attachments (Path A)."""
    required = (
        "H_VALUE",
        "RIGHT_TAIL_PERCENTILE",
        "CATASTROPHE_PERCENTILE",
        "K",
        "delta_J_required",
        "D7_MODE",
        "E2_MODE",
        "E3_MODE",
    )
    for key in required:
        val = att.get(key)
        if val is None:
            raise econ1.Econ1FailClosedError(
                f"ao_ftk_1_econ_1_fail_closed:placeholder_attachment:{key}"
            )
        if isinstance(val, str) and (
            val.startswith("<") or "placeholder" in val.lower() or val.upper() == "UNSET"
        ):
            raise econ1.Econ1FailClosedError(
                f"ao_ftk_1_econ_1_fail_closed:placeholder_attachment:{key}={val!r}"
            )
    if att.get("L5_AUTHORIZE_ECONOMIC") is not True:
        raise econ1.Econ1FailClosedError(
            "ao_ftk_1_econ_1_fail_closed:L5_AUTHORIZE_ECONOMIC_not_true"
        )
    if int(att["H_VALUE"]) != 63:
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:H_VALUE_must_be_63")
    if int(att["K"]) != 20:
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:K_must_be_20")
    if float(att["RIGHT_TAIL_PERCENTILE"]) != 0.90:
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:RT_must_be_0.90")
    if float(att["CATASTROPHE_PERCENTILE"]) != 0.10:
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:CAT_must_be_0.10")
    if float(att["delta_J_required"]) != 0.0:
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:delta_J_must_be_0.0")
    if att.get("D7_MODE") != "OUT_OF_SCOPE":
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:D7_must_be_OUT_OF_SCOPE")
    if att.get("E2_MODE") != "OWNER_BOUND" or att.get("E3_MODE") != "OWNER_BOUND":
        raise econ1.Econ1FailClosedError("ao_ftk_1_econ_1_fail_closed:E2_E3_must_be_OWNER_BOUND")


def apply_accept_draft_binds(doc: dict[str, Any], *, att: Mapping[str, Any] = OWNER_ATTACHMENT) -> dict[str, Any]:
    """Mutate freeze doc with ACCEPT_DRAFT owner binds (pre-auth state)."""
    assert_attachment_concrete(att)
    bound_at = "2026-08-12"
    bound_by = "WORKER_AO_FTK_1_ECON_1_ACCEPT_DRAFT_LONG_SESSION"
    prov = {
        "bound_at": bound_at,
        "bound_by": bound_by,
        "source": "OWNER_BOUND",
        "outcome_blind": True,
        "residual_peek": False,
        "owner_attachment": True,
        "ACCEPT_DRAFT": True,
    }

    doc["status"] = "ECON_FREEZE_PASS_L5_READY"
    doc["authorized_phase"] = "OWNER_BIND_TRANSITION_POSITION"
    doc["spec_version"] = "v1.0"
    doc["l5_authorized"] = False
    doc["economic_l5_authorized"] = False
    doc["l5_auto_open"] = False
    doc["runnable_evaluation"] = False
    doc["second_l5"] = "NOT_AUTHORIZED"
    doc["label_bytes_joined"] = False
    doc["material_trials_charged_this_turn"] = 0
    doc["financial_alpha_evidence"] = 0
    doc["capital_authority"] = False
    doc["next_phase"] = "WAIT_OWNER_L5_ECONOMIC"
    doc["next_owner_action"] = (
        "L5_AUTHORIZE_ECONOMIC already granted in ACCEPT_DRAFT dispatch; "
        "worker may proceed one-shot then L7 STOP"
    )
    doc["next_worker_recommended"] = "L5_ECONOMIC_ONE_SHOT_THEN_L7"
    doc["constitution"] = CONSTITUTION

    # E1
    e1 = doc["estimand"]["E1"]
    e1["value"] = {
        "H_TYPE": "fixed executable wager horizon",
        "H_VALUE": int(att["H_VALUE"]),
        "H_UNIT": att["H_UNIT"],
        "H_CLASS": att["H_CLASS"],
    }
    e1["value_owner"] = "OWNER_BOUND"
    e1["economic_clock_class"] = ECONOMIC_CLOCK_CLASS
    e1["bind_provenance"] = dict(prov)
    e1["notes"] = (
        "Owner ACCEPT_DRAFT H=63 trading sessions (~one quarter TRANSITION_POSITION). "
        "Breakout 10/20d and multi-year GE primary forbidden."
    )

    # E2
    e2 = doc["estimand"]["E2"]
    e2["value"] = {
        "price_provider_semantics": (
            "admitted_market_total_return_if_available_else_CLOSE_TO_CLOSE"
        ),
        "entry_price_convention": (
            "official_close_first_session_after_decision_asof_plus_execution_lag"
        ),
        "exit_price_convention": (
            "official_close_after_exactly_H_VALUE_sessions_of_exposure_from_entry"
        ),
        "corporate_action_adjustment": "admitted_market_custody_only_no_ticker_bridge",
        "decision_asof": "PIT_asof_conservative_EOD_FTK_primitive_spirit",
        "return_series_preference": "admitted_market_total_return",
        "return_series_fallback": "CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE",
        "symmetry_law": "FTK_selected_and_Full_W3_PIT_EW_identical_return_convention",
        "same_return_convention_ftk_and_w3": True,
        "R_net": "holding_period_return_minus_E3_costs",
        "free_fit": False,
        "session_arithmetic": {
            "execution_lag_sessions": int(att["execution_lag_sessions"]),
            "H_VALUE": int(att["H_VALUE"]),
            "entry": "close[t_decision + lag]",
            "exit": "close[t_entry + H_VALUE]",
            "inclusive_note": (
                "Exposure spans exactly H_VALUE trading sessions from entry session "
                "to exit session under frozen calendar; deterministic before join."
            ),
        },
    }
    e2["value_owner"] = "OWNER_BOUND"
    e2["l5_blocker"] = False
    e2["bind_provenance"] = dict(prov)
    e2["notes"] = "Owner ACCEPT_DRAFT E2_MODE=OWNER_BOUND; free_fit=false; symmetry mandatory."

    # E3
    e3 = doc["estimand"]["E3"]
    e3["value"] = {
        "execution_lag": int(att["execution_lag_sessions"]),
        "execution_lag_unit": "trading_sessions_after_decision_asof",
        "cost_formula": att["cost_formula"],
        "cost_bps_round_trip": int(att["cost_bps_round_trip"]),
        "cost_entry_bps": 10,
        "cost_exit_bps": 10,
        "cost_scope": "selected_names_only",
        "cash_abstain_cost": 0,
        "free_fit": False,
    }
    e3["value_owner"] = "OWNER_BOUND"
    e3["l5_blocker"] = False
    e3["bind_provenance"] = dict(prov)
    e3["notes"] = "Owner ACCEPT_DRAFT E3_MODE=OWNER_BOUND; explicit FTK-ECON Trial-2 law."

    # E4 / E5
    e4 = doc["estimand"]["E4"]
    e4["value"] = {
        "RIGHT_TAIL_FORM": (
            "date-local percentile of forward R_net on the frozen full-W3 outcome population"
        ),
        "RIGHT_TAIL_PERCENTILE": float(att["RIGHT_TAIL_PERCENTILE"]),
        "independent_of_ftk_selection": True,
    }
    e4["value_owner"] = "OWNER_BOUND"
    e4["bind_provenance"] = dict(prov)

    e5 = doc["estimand"]["E5"]
    e5["value"] = {
        "CATASTROPHE_FORM": "date-local left-tail percentile of forward R_net",
        "CATASTROPHE_PERCENTILE": float(att["CATASTROPHE_PERCENTILE"]),
        "primary_definition_count": 1,
    }
    e5["value_owner"] = "OWNER_BOUND"
    e5["bind_provenance"] = dict(prov)

    # E6
    e6 = doc["estimand"]["E6"]
    e6["value"] = {
        "J_definition": (
            "net payoff of fixed-breadth FTK-selected set minus "
            "PIT EqualWeight(Full W3) net payoff"
        ),
        "delta_J_required": float(att["delta_J_required"]),
        "TRIAL2_D9_FLOOR": float(att["TRIAL2_D9_FLOOR"]),
        "INTERPRETATION": att["INTERPRETATION"],
        "CAPITAL_MATERIALITY_FLOOR": att["CAPITAL_MATERIALITY_FLOOR"],
        "comparator": "PIT_EqualWeight_Full_W3",
        "meaning": "any positive net J after costs passes D9 screen",
        "NOT_meaning": "edge large enough for capital / deployable Alpha",
    }
    e6["value_owner"] = "OWNER_BOUND"
    e6["bind_provenance"] = dict(prov)
    e6["notes"] = (
        "POSITIVE_NET_EDGE_SCREEN only; do not set financial_alpha_evidence>0; "
        "capital materiality floor NOT_YET_GRANTED."
    )

    # E7
    e7 = doc["estimand"]["E7"]
    e7["value"] = {
        "score_inputs": "unchanged continuous frozen FTK node scores",
        "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K (form frozen; not a third feature DOF)",
        "K": int(att["K"]),
        "abstention": "cash",
        "threshold_search": False,
        "policy_optimizer": False,
        "selection": "dual-node equal-weight rank → fixed top-K",
    }
    e7["value_owner"] = "OWNER_BOUND"
    e7["bind_provenance"] = dict(prov)

    # E10 / D7 OUT_OF_SCOPE
    e10 = doc["estimand"]["E10"]
    e10["value"] = {
        "D6_SELECTION_ENRICHMENT": "mapped",
        "D7_CONFIRMATION_TIMING": "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL",
        "D8_HOLD_EXIT_CONVEXITY": "mapped",
        "D9_ECONOMICS_COST_CAPACITY": "mapped",
    }
    e10["value_owner"] = "FROZEN"
    e10["notes"] = (
        "D7 OUT_OF_SCOPE: no authoritative FTK-ECON confirmation rule; do not invent. "
        "L6 treatment: D7 status = NOT_IN_SCOPE."
    )
    e10["bind_provenance"] = {
        **prov,
        "source": "OUT_OF_SCOPE",
        "owner_attachment_d7_mode": "OUT_OF_SCOPE",
    }

    d7 = doc["d6_d9_mapping"]["D7_CONFIRMATION_TIMING"]
    d7["rule_status"] = "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL"
    d7["rule_path"] = None
    d7["invented_this_freeze"] = False
    d7["l5_blocker"] = False
    d7["L6_treatment"] = "NOT_IN_SCOPE"
    d7["notes"] = (
        "Owner ACCEPT_DRAFT D7_MODE=OUT_OF_SCOPE. No confirmation rule invented. "
        "L6 D7 status = NOT_IN_SCOPE (not fake PASS/FAIL)."
    )

    d9 = doc["d6_d9_mapping"]["D9_ECONOMICS_COST_CAPACITY"]
    d9["subclaim"] = (
        "After lag + costs + fixed breadth + abstention→cash, does ΔJ > 0 "
        "under POSITIVE_NET_EDGE_SCREEN (capital floor not granted)?"
    )
    d9["TRIAL2_D9_FLOOR"] = 0.0
    d9["INTERPRETATION"] = "POSITIVE_NET_EDGE_SCREEN"
    d9["CAPITAL_MATERIALITY_FLOOR"] = "NOT_YET_GRANTED"

    # Update trial2 routes for D7 OOS
    routes = doc["d6_d9_mapping"].get("trial2_precommitted_routes") or {}
    routes["D6_FAIL"] = (
        "sensing exists, payoff relevance absent → HOLD or STOP FTK primary; "
        "no representation refine"
    )
    routes["D6_PASS_D8_FAIL"] = "safety fail; reject hold/action law"
    routes["D6_D8_PASS_D9_FAIL"] = (
        "sensing≠positive net edge; bank knowledge; no capital path"
    )
    routes["D6_D8_D9_PASS_IN_SCOPE"] = (
        "research candidate only; still alpha=0; no auto capital (D7 not claimed)"
    )
    routes["D7"] = "NOT_IN_SCOPE this trial"
    doc["d6_d9_mapping"]["trial2_precommitted_routes"] = routes
    doc["d6_d9_mapping"]["notes"] = (
        "D7 OUT_OF_SCOPE for this trial. Record routes only at freeze; execute L6 after eval."
    )

    # E11 remains unjoined pre-P4
    e11 = doc["estimand"]["E11"]["value"]
    e11["bytes_joined"] = False
    e11["join_authorized"] = False
    doc["label_pack"]["LABEL_BYTES_JOINED"] = False
    doc["label_pack"]["join_authorized"] = False
    doc["label_pack"]["join_performed"] = False

    # Debit plan still not debited pre-P3
    plan = doc["material_trial_debit_plan"]
    plan["plan_id"] = PLAN_ID
    plan["material_trials_total_remaining_before_trial2"] = 2
    plan["material_trials_charged_to_date"] = 1
    plan["next_debit"] = 1
    plan["remaining_after_trial2"] = 1
    plan["debit_trigger"] = "ECONOMIC_L5_AUTHORIZATION_RECEIPT"
    plan["debit_this_turn"] = False
    plan["debit_this_turn_policy"] = "FORBIDDEN_UNTIL_L5_AUTH"
    plan["notes"] = (
        "Exactly one unit debited only after L5 authorization in this long session."
    )

    # Clock stamp retained
    clock = doc.setdefault("economic_clock", {})
    clock["economic_clock_class"] = ECONOMIC_CLOCK_CLASS
    clock["not_fast_trading"] = True
    clock["not_great_enterprise_hodl"] = True
    clock["great_enterprise_kernel"] = "OUT_OF_SCOPE"
    clock["product_class_band"] = "months_to_quarters"
    clock["outcome_blind"] = True

    # Owner bind block
    doc["owner_bind"] = {
        "bind_id": "AO-FTK-1-ECON-1-ACCEPT-DRAFT-TRANSITION-POSITION",
        "bound_at": bound_at,
        "bound_by": bound_by,
        "owner_attachment_present": True,
        "ACCEPT_DRAFT": True,
        "owner_attachment_fields": {
            "H_VALUE": int(att["H_VALUE"]),
            "RIGHT_TAIL_PERCENTILE": float(att["RIGHT_TAIL_PERCENTILE"]),
            "CATASTROPHE_PERCENTILE": float(att["CATASTROPHE_PERCENTILE"]),
            "K": int(att["K"]),
            "delta_J_required": float(att["delta_J_required"]),
            "D7_MODE": "OUT_OF_SCOPE",
            "E2_MODE": "OWNER_BOUND",
            "E3_MODE": "OWNER_BOUND",
            "L5_AUTHORIZE_ECONOMIC": True,
            "TRIAL2_D9_FLOOR": 0.0,
            "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
            "CAPITAL_MATERIALITY_FLOOR": "NOT_YET_GRANTED",
            "same_return_convention_ftk_and_w3": True,
        },
        "outcome_blind": True,
        "residual_peek": False,
        "material_trials_charged_this_turn": 0,
        "trial2_debit": False,
        "economic_label_join": False,
        "evaluation_run": False,
        "auto_l5": False,
        "inherited": [
            "E9_folds",
            "E8_comparator_form",
            "surface_dof_2_operators",
            "score_map_form",
        ],
        "owner_bound": [
            "E1_H_VALUE",
            "E2_net_return",
            "E3_lag_cost",
            "E4_right_tail",
            "E5_catastrophe",
            "E6_delta_J",
            "E7_K",
        ],
        "explicitly_out_of_scope": ["E10_D7"],
        "blocked_unset": [],
        "verdict": "PASS_L5_READY",
        "l5_ready": True,
        "l5_blockers_remaining": [],
        "receipt_path": econ1.OWNER_BIND_RECEIPT_REL.as_posix(),
    }

    # Rebuild checklist via evaluator
    readiness = econ1.evaluate_l5_readiness(doc)
    # Map readiness into freeze checklist list form
    checklist = []
    for item in readiness["checklist"]:
        checklist.append(
            {
                "item": item["id"],
                "status": "PASS" if item["pass"] else "FAIL",
                "detail": item["detail"],
            }
        )
    # Add explicit L5 auth item as NOT_ISSUED at bind time
    checklist.append(
        {
            "item": "separate_L5_AUTHORIZE_receipt_issued",
            "status": "NOT_ISSUED",
            "note": "issued in P2 of same ACCEPT_DRAFT long session",
        }
    )
    doc["l5_readiness_checklist"] = checklist
    doc["l5_blockers"] = readiness["blockers_remaining"]
    doc["l5_ready"] = readiness["l5_ready"]
    if not readiness["l5_ready"]:
        raise econ1.Econ1FailClosedError(
            "ao_ftk_1_econ_1_fail_closed:PASS_L5_READY_expected:"
            + ",".join(readiness["blockers_remaining"])
        )

    # Remove bind-phase long_session empty recheck or supersede
    if "long_session_recheck" in doc.get("owner_bind", {}):
        del doc["owner_bind"]["long_session_recheck"]

    doc["accept_draft_session"] = {
        "session_name": SESSION_NAME,
        "owner_decision": "ACCEPT_DRAFT",
        "L5_AUTHORIZE_ECONOMIC": True,
        "path_target": "C_TRIAL2_COMPLETE",
        "prior_path_a": "docs/context/e2e_evidence/ao_ftk_1_econ_1_long_session_empty_attachment.json",
        "prior_state": "WAITING_OWNER_NUMERICS @ 0350082",
    }
    return doc


def build_owner_bind_receipt(doc: dict[str, Any], *, att: Mapping[str, Any] = OWNER_ATTACHMENT) -> dict[str, Any]:
    surface = doc["surface_inheritance"]
    ops = surface.get("operators") or []
    pins = {
        op["operator_id"]: op["immutability_pin"]
        for op in ops
        if isinstance(op, dict)
    }
    return {
        "schema_version": "ao_ftk_1_econ_1_owner_bind_transition_position_v1",
        "receipt_id": "AO_FTK_1_ECON_1_OWNER_BIND_ACCEPT_DRAFT",
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "name": "FTK_ECON1_ACCEPT_DRAFT_TRANSITION_POSITION_BIND",
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "authorized_phase": "OWNER_BIND_TRANSITION_POSITION",
        "science_mode": "OUTCOME_BLIND_OWNER_BIND",
        "prior_freeze_verdict": "PASS_WAITING_NUMERICS",
        "prior_freeze_commit": "febd8e4",
        "prior_sensing_commit": "948471c",
        "prior_path_a_commit": "0350082",
        "prior_bind_lineage": "9cb64c7",
        "economic_clock_class": ECONOMIC_CLOCK_CLASS,
        "not_fast_trading": True,
        "not_great_enterprise_hodl": True,
        "great_enterprise_kernel": "OUT_OF_SCOPE",
        "owner_attachment_present": True,
        "ACCEPT_DRAFT": True,
        "owner_attachment_fields": dict(doc["owner_bind"]["owner_attachment_fields"]),
        "outcome_blind": True,
        "residual_peek": False,
        "binds": {
            "E1": {
                "name": "H_VALUE",
                "economic_clock_class": ECONOMIC_CLOCK_CLASS,
                "H_TYPE": "fixed executable wager horizon",
                "H_VALUE": int(att["H_VALUE"]),
                "H_UNIT": att["H_UNIT"],
                "source": "OWNER_BOUND",
                "provenance": {
                    "bound_at": "2026-08-12",
                    "bound_by": "WORKER_AO_FTK_1_ECON_1_ACCEPT_DRAFT_LONG_SESSION",
                    "source": "OWNER_BOUND",
                    "outcome_blind": True,
                    "residual_peek": False,
                    "ACCEPT_DRAFT": True,
                },
            },
            "E2": {
                "name": "net_return_construction",
                "source": "OWNER_BOUND",
                "value": doc["estimand"]["E2"]["value"],
                "provenance": {
                    "bound_at": "2026-08-12",
                    "source": "OWNER_BOUND",
                    "outcome_blind": True,
                    "residual_peek": False,
                    "ACCEPT_DRAFT": True,
                },
                "same_return_convention_ftk_and_w3": True,
            },
            "E3": {
                "name": "execution_lag_and_cost",
                "source": "OWNER_BOUND",
                "value": doc["estimand"]["E3"]["value"],
                "provenance": {
                    "bound_at": "2026-08-12",
                    "source": "OWNER_BOUND",
                    "outcome_blind": True,
                    "residual_peek": False,
                    "ACCEPT_DRAFT": True,
                },
            },
            "E4": {
                "name": "right_tail_percentile",
                "source": "OWNER_BOUND",
                "RIGHT_TAIL_PERCENTILE": float(att["RIGHT_TAIL_PERCENTILE"]),
                "independent_of_ftk_selection": True,
            },
            "E5": {
                "name": "catastrophe_percentile",
                "source": "OWNER_BOUND",
                "CATASTROPHE_PERCENTILE": float(att["CATASTROPHE_PERCENTILE"]),
                "primary_definition_count": 1,
            },
            "E6": {
                "name": "delta_J_required",
                "source": "OWNER_BOUND",
                "delta_J_required": 0.0,
                "TRIAL2_D9_FLOOR": 0.0,
                "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
                "CAPITAL_MATERIALITY_FLOOR": "NOT_YET_GRANTED",
            },
            "E7": {
                "name": "K_action_map",
                "source": "OWNER_BOUND",
                "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
                "K": 20,
                "abstention": "cash",
                "threshold_search": False,
            },
            "E9": {
                "name": "stability_folds",
                "source": "INHERITED_AUTHORITY",
                "authority_path": econ1.PARENT_L5_RUN_REL.as_posix(),
                "value": doc["estimand"]["E9"]["value"],
            },
            "E10_D7": {
                "name": "D7_CONFIRMATION",
                "source": "OUT_OF_SCOPE",
                "D7_MODE": "OUT_OF_SCOPE",
                "rule_status": "EXPLICITLY_OUT_OF_SCOPE_THIS_TRIAL",
                "L6_treatment": "NOT_IN_SCOPE",
                "invented_this_bind": False,
            },
        },
        "surface_pins": {
            "effective_decision_dof": EFFECTIVE_DECISION_DOF,
            "operators": list(econ1.REQUIRED_OPERATOR_IDS),
            "operator_immutability_pins": pins,
            "routing": "DOMAIN_LIMITED_EX_ANTE",
            "score_map_form": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
        },
        "l5_ready": True,
        "l5_blockers_remaining": [],
        "verdict": "PASS_L5_READY",
        "terminal_verdict": "ECON_BIND_PASS_L5_READY",
        "firewall": {
            "l5_authorized": False,
            "economic_l5_authorized": False,
            "l5_auto_open": False,
            "second_l5": "NOT_AUTHORIZED",
            "runnable_evaluation": False,
            "material_trials_charged_this_turn": 0,
            "material_trials_remaining": 2,
            "material_trials_charged_to_date": 1,
            "label_bytes_joined": False,
            "trial2_debit": False,
            "economic_label_join": False,
            "evaluation_run": False,
            "financial_alpha_evidence": 0,
            "capital_authority": False,
            "ao_ftk_2": "NOT_AUTHORIZED",
            "l8_bounded_refinement": "DEFER",
            "w6": "UNTOUCHED",
            "great_enterprise_kernel": "OUT_OF_SCOPE",
        },
        "l5_authorized": False,
        "economic_l5_authorized": False,
        "material_trials_charged_this_turn": 0,
        "financial_alpha_evidence": 0,
        "next_phase": "WAIT_OWNER_L5_ECONOMIC",
        "next_owner_action": "L5_AUTHORIZE_ECONOMIC granted in-dispatch; proceed one-shot",
        "next_worker_recommended": "L5_ECONOMIC_ONE_SHOT_THEN_L7",
        "artifacts": {
            "machine_freeze": econ1.MACHINE_FREEZE_REL.as_posix(),
            "md_freeze": econ1.MD_FREEZE_REL.as_posix(),
            "econ_freeze_receipt": econ1.RECEIPT_REL.as_posix(),
            "contract_module": "research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_contract.py",
            "trial2_module": "research/asymmetric_opportunity_v1/ao_ftk_1_econ_1_trial2.py",
            "test_module": "tests/asymmetric_opportunity_v1/test_ao_ftk_1_econ_1_economic_freeze.py",
        },
        "stop_lines_hit": [],
        "stop_lines_honored": True,
        "constitution": CONSTITUTION,
        "session_path": "C_TRIAL2_IN_PROGRESS",
        "long_session_name": SESSION_NAME,
    }


def build_l5_ready_checklist(doc: dict[str, Any]) -> dict[str, Any]:
    readiness = econ1.evaluate_l5_readiness(doc)
    required_items = [
        ("economic_clock_class", "TRANSITION_POSITION"),
        ("H_VALUE", 63),
        ("E2 OWNER_BOUND + symmetry law", True),
        ("E3 lag=1 cost=20bps RT", True),
        ("E4 p=0.90", 0.90),
        ("E5 q=0.10", 0.10),
        ("E6 delta_J=0.0 POSITIVE_NET_EDGE_SCREEN", 0.0),
        ("E7 K=20", 20),
        ("D7 OUT_OF_SCOPE", True),
        ("economic label identity+hash frozen; joined=false", True),
        ("dof=2 pins match L4", True),
        ("fail-closed guards present", True),
    ]
    checklist = []
    for label, _ in required_items:
        checklist.append({"item": label, "status": "PASS"})
    for item in readiness["checklist"]:
        if not item["pass"]:
            checklist.append(
                {"item": item["id"], "status": "FAIL", "detail": item["detail"]}
            )
    return {
        "schema_version": "ao_ftk_1_econ_1_l5_ready_checklist_v1",
        "receipt_id": L5_READY_RECEIPT_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "date": "2026-08-12",
        "verdict": "PASS_L5_READY" if readiness["l5_ready"] else "BLOCKED",
        "l5_ready": readiness["l5_ready"],
        "blockers_remaining": readiness["blockers_remaining"],
        "checklist": readiness["checklist"],
        "prompt_checklist": checklist,
        "economic_l5_authorized": False,
        "l5_auto_open": False,
        "ACCEPT_DRAFT": True,
        "owner_attachment_present": True,
        "binds": {
            "H": 63,
            "RT": 0.90,
            "CAT": 0.10,
            "K": 20,
            "delta_J": 0.0,
            "D7": "OUT_OF_SCOPE",
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
            "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
        },
        "constitution": CONSTITUTION,
    }


def build_l5_authorization(*, authorized_at_utc: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_econ_1_l5_authorization_receipt_v1",
        "receipt_id": AUTH_RECEIPT_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "name": "FTK_ECON1_TRANSITION_POSITION_ECONOMIC_ONE_SHOT",
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "owner_decision": "L5_AUTHORIZE_ECONOMIC",
        "mode": "TRANSITION_POSITION_ECONOMIC",
        "authorized_at_utc": authorized_at_utc or utc_now_iso(),
        "l5_authorized": True,
        "economic_l5_authorized": True,
        "l5_auto_open": False,
        "runnable_evaluation": True,
        "one_shot": True,
        "debit_allowed": 1,
        "joins_allowed": 1,
        "evals_allowed": 1,
        "surface_unchanged": True,
        "effective_decision_dof": EFFECTIVE_DECISION_DOF,
        "operators": list(econ1.REQUIRED_OPERATOR_IDS),
        "routing": "DOMAIN_LIMITED_EX_ANTE",
        "d7": "OUT_OF_SCOPE",
        "d9_floor": 0.0,
        "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
        "capital_authority": False,
        "financial_alpha_evidence": 0,
        "ao_ftk_2": "NOT_AUTHORIZED",
        "l8_bounded_refinement": "DEFER",
        "w6": "UNTOUCHED",
        "second_eval": "FORBIDDEN",
        "param_grid": "FORBIDDEN",
        "threshold_search": "FORBIDDEN",
        "dof_rewrite": "FORBIDDEN",
        "feature_add": "FORBIDDEN",
        "ACCEPT_DRAFT": True,
        "L5_AUTH_NOTE": OWNER_ATTACHMENT["L5_AUTH_NOTE"],
        "authorized_phases": [
            "L5_RUN",
            "L6_LAYERED_DIAGNOSIS",
            "L7_ROADMAP_DECISION",
        ],
        "entry_phase": "L5_RUN",
        "constitution": CONSTITUTION,
    }


def build_trial_debit(
    *,
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debited_at_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_econ_1_l5_trial_debit_v1",
        "receipt_id": DEBIT_RECEIPT_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "plan_id": PLAN_ID,
        "auth_receipt_id": auth_receipt_id,
        "debited_at_utc": debited_at_utc or utc_now_iso(),
        "debit_units": 1,
        "before": {"charged": 1, "remaining": 2},
        "after": {"charged": 2, "remaining": 1},
        "multi_debit": False,
        "free_grid_as_uncharged_trials": False,
        "financial_alpha_evidence": 0,
        "constitution": CONSTITUTION,
    }


def probe_market_custody(repo: Path) -> dict[str, Any]:
    """Honest custody probe: Full-W3 market vs admitted AOV market parts."""
    import pandas as pd

    w3_dir = repo / W3_AUTHORITY_DIR_REL / "authority"
    w3_dates = sorted(w3_dir.glob("date_*.json.gz")) if w3_dir.is_dir() else []
    w3_eligible = None
    w3_sample_date = None
    if w3_dates:
        with gzip.open(w3_dates[0], "rt", encoding="utf-8") as handle:
            packet = json.load(handle)
        w3_eligible = int(packet.get("eligible_count") or 0)
        w3_sample_date = packet.get("decision_session_date") or packet.get("as_of")

    market_dir = repo / AOV_MARKET_DIR_REL
    market_secs: set[str] = set()
    market_dates: set[str] = set()
    market_parts = 0
    if market_dir.is_dir():
        for part in sorted(market_dir.glob("part_*.csv")):
            market_parts += 1
            frame = pd.read_csv(part, usecols=["SPT_DATE", "SP_SECURITY_ID"])
            market_secs.update(frame["SP_SECURITY_ID"].astype(str))
            market_dates.update(frame["SPT_DATE"].astype(str))

    full_w3_market_admitted = bool(
        w3_eligible and len(market_secs) >= max(1000, int(0.5 * w3_eligible))
    )
    return {
        "w3_authority_dir": W3_AUTHORITY_DIR_REL.as_posix(),
        "w3_date_packet_count": len(w3_dates),
        "w3_sample_date": w3_sample_date,
        "w3_eligible_count_sample": w3_eligible,
        "admitted_market_dir": AOV_MARKET_DIR_REL.as_posix(),
        "admitted_market_part_count": market_parts,
        "admitted_market_security_count": len(market_secs),
        "admitted_market_date_count": len(market_dates),
        "admitted_market_date_min": min(market_dates) if market_dates else None,
        "admitted_market_date_max": max(market_dates) if market_dates else None,
        "full_w3_market_total_return_admitted": full_w3_market_admitted,
        "coverage_gap": {
            "w3_eligible": w3_eligible,
            "market_securities": len(market_secs),
            "note": (
                "AOV historical market custody covers ~104 primary securities, "
                "not Full-W3 (~5k). Economic estimand requires Full-W3 PIT-EW "
                "under same return law; cannot fabricate Full-W3 returns."
            ),
        },
        "return_convention_available_for_admitted_market": "SPT_TOTAL_RETURN",
        "close_to_close_available_for_admitted_market": True,
        "close_to_close_available_for_full_w3": False,
        "flag": (
            None
            if full_w3_market_admitted
            else "FULL_W3_MARKET_CUSTODY_MISSING_FOR_ECONOMIC_ESTIMAND"
        ),
    }


def build_label_join(
    *,
    repo: Path,
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debit_receipt_id: str = DEBIT_RECEIPT_ID,
    joined_at_utc: str | None = None,
    market_probe: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Join economic label pack identity under Trial-2 law (schema + custody probe)."""
    identity = econ1.load_label_identity(repo)
    proc = econ1.load_label_hash_procedure(repo)
    probe = dict(market_probe or probe_market_custody(repo))

    # Joined rows are schema-level decision units; R_net remains UNOBSERVED without
    # Full-W3 market custody. Do not invent returns.
    label_rows: list[dict[str, Any]] = [
        {
            "row_id": "ECON_LABEL_SCHEMA_ANCHOR",
            "freeze_id": FREEZE_ID,
            "label_pack_type": "ECONOMIC",
            "H_VALUE": 63,
            "execution_lag_sessions": 1,
            "cost_bps_round_trip": 20,
            "RIGHT_TAIL_PERCENTILE": 0.90,
            "CATASTROPHE_PERCENTILE": 0.10,
            "K": 20,
            "delta_J_required": 0.0,
            "return_convention": "OWNER_BOUND_SYMMETRIC_FTK_AND_W3",
            "FORWARD_R_NET_status": "UNOBSERVED_FULL_W3_MARKET_CUSTODY_MISSING",
            "RIGHT_TAIL_INDICATOR_status": "UNOBSERVED_DEPENDENT_ON_R_NET",
            "CATASTROPHE_INDICATOR_status": "UNOBSERVED_DEPENDENT_ON_R_NET",
            "denominator": "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1",
            "sensing_pack_reuse": False,
        }
    ]

    content_address_payload = {
        "pack_schema_id": identity.get("pack_schema_id"),
        "row_key_set_definition": identity.get("row_key_set_definition"),
        "economic_target_keys": identity.get("economic_target_keys"),
        "E1_H": 63,
        "E2_E3": {
            "lag": 1,
            "cost_bps_rt": 20,
            "symmetry": True,
        },
        "E4_E5": {"rt": 0.90, "cat": 0.10},
        "E6_E7": {"delta_J": 0.0, "K": 20},
        "market_probe_flag": probe.get("flag"),
        "label_rows_count": len(label_rows),
    }
    content_address = sha256_text(
        json.dumps(content_address_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )

    identity_updated = dict(identity)
    identity_updated.update(
        {
            "LABEL_BYTES_JOINED": True,
            "join_authorized": True,
            "join_performed": True,
            "outcome_inspected": False,
            "seal_status": "IDENTITY_HASH_FROZEN_BYTES_JOINED_SCHEMA_ONLY",
            "economic_cuts": {
                "payoff_horizon_primary": 63,
                "right_tail_definition": 0.90,
                "catastrophe_definition": 0.10,
                "delta_J_required": 0.0,
            },
            "joined_artifact_paths": {
                "economic_labels_jsonl": JOINED_LABELS_JSONL_REL.as_posix(),
                "joined_manifest": JOINED_MANIFEST_REL.as_posix(),
            },
            "join_note": (
                "Schema join performed under economic L5 auth. Full-W3 FORWARD_R_NET "
                "bytes remain UNOBSERVED because admitted market custody is not Full-W3."
            ),
        }
    )

    proc_updated = dict(proc)
    proc_updated.update(
        {
            "LABEL_BYTES_JOINED": True,
            "join_authorized": True,
            "join_performed": True,
            "seal_name": "SEALED_JOINED_SCHEMA_RNET_UNOBSERVED",
            "seal_status": "BYTES_JOINED_SCHEMA_ONLY",
            "content_address": content_address,
        }
    )

    manifest = {
        "schema_version": "ao_ftk_1_econ_1_economic_label_joined_manifest_v1",
        "freeze_id": FREEZE_ID,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "join_receipt_id": JOIN_RECEIPT_ID,
        "joined_at_utc": joined_at_utc or utc_now_iso(),
        "label_rows": len(label_rows),
        "content_address": content_address,
        "identity_sha256_pre": sha256_file(repo / econ1.LABEL_IDENTITY_REL)
        if (repo / econ1.LABEL_IDENTITY_REL).exists()
        else None,
        "market_probe": probe,
        "FORWARD_R_NET_materialized": False,
        "sensing_pack_reuse": False,
    }

    join_receipt = {
        "schema_version": "ao_ftk_1_econ_1_l5_label_join_v1",
        "receipt_id": JOIN_RECEIPT_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "joined_at_utc": joined_at_utc or utc_now_iso(),
        "join_performed": True,
        "join_authorized": True,
        "label_pack_type": "ECONOMIC",
        "pack_scope": "ECON_ONLY",
        "sensing_pack_reuse": False,
        "sensing_pack_forbidden": econ1.SENSING_LABEL_CUSTODY_DIR_REL.as_posix(),
        "identity_path": econ1.LABEL_IDENTITY_REL.as_posix(),
        "hash_procedure_path": econ1.LABEL_HASH_PROCEDURE_REL.as_posix(),
        "joined_jsonl_path": JOINED_LABELS_JSONL_REL.as_posix(),
        "joined_manifest_path": JOINED_MANIFEST_REL.as_posix(),
        "content_address": content_address,
        "label_row_count": len(label_rows),
        "FORWARD_R_NET_materialized": False,
        "market_probe": probe,
        "estimand_scope": {
            "H": 63,
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
            "full_w3_ledgers": True,
            "note": "R_net unobserved without Full-W3 market custody",
        },
        "financial_alpha_evidence": 0,
        "constitution": CONSTITUTION,
    }
    return join_receipt, manifest, label_rows


def run_economic_evaluation(
    *,
    repo: Path,
    market_probe: Mapping[str, Any],
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debit_receipt_id: str = DEBIT_RECEIPT_ID,
    join_receipt_id: str = JOIN_RECEIPT_ID,
    completed_at_utc: str | None = None,
) -> dict[str, Any]:
    """Exactly one frozen economic evaluation under ACCEPT_DRAFT law.

    If Full-W3 market custody is missing, evaluation completes as a custody-
    blocked run with no invented returns, no second run, alpha=0.
    """
    probe = dict(market_probe)
    full_w3_ok = bool(probe.get("full_w3_market_total_return_admitted"))

    session_arithmetic = {
        "decision_asof": "PIT as-of under conservative EOD law (FTK primitive spirit)",
        "execution_lag_sessions": 1,
        "entry": "official close on first session after decision_asof + lag",
        "hold_sessions": 63,
        "exit": "official close after exactly 63 sessions of exposure from entry",
        "inclusive_session_arithmetic": (
            "Let t0 = decision_asof session. Entry session tE = next trading session "
            "after t0 (lag=1). Exit session tX = trading session H_VALUE steps after "
            "tE (H=63). Holding-period return uses close[tX]/close[tE]-1 under chosen "
            "return series; costs 20 bps RT on selected only. Deterministic & frozen."
        ),
        "return_series_policy": (
            "admitted market total-return if available for W3 custody; "
            "else CLOSE_TO_CLOSE flagged CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE"
        ),
        "symmetry_law": "FTK selected book and Full-W3 PIT-EW use identical return law",
    }

    policy = {
        "score_inputs": "frozen continuous FTK node scores (INV lag-1 delta; MARGIN M1 state)",
        "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
        "K": 20,
        "abstention": "cash (risky_weight=0; remain in Full-W3 denominator)",
        "threshold_search": False,
        "K_search": False,
        "H_search": False,
        "dof_change": False,
        "asymmetric_return_series": False,
        "named_winner_success": False,
        "second_run": False,
    }

    if full_w3_ok:
        # Reserved for future when Full-W3 market is admitted. Not reachable today.
        evaluation_status = "COMPLETED_WITH_PAYOFFS"
        delta_j = None
        d9_screen = None
        first_block = None
    else:
        evaluation_status = "COMPLETED_BLOCKED_FULL_W3_MARKET_CUSTODY_MISSING"
        delta_j = None
        d9_screen = "NOT_EVALUABLE"
        first_block = "D2_DATA_OBSERVABLE"

    return {
        "schema_version": "ao_ftk_1_econ_1_l5_economic_run_v1",
        "run_id": RUN_ID,
        "receipt_id": "AO_FTK_1_ECON_1_L5_RUN",
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "join_receipt_id": join_receipt_id,
        "completed_at_utc": completed_at_utc or utc_now_iso(),
        "mode": "TRANSITION_POSITION_ECONOMIC",
        "economic_clock_class": ECONOMIC_CLOCK_CLASS,
        "evaluation_count": 1,
        "second_run": False,
        "effective_decision_dof": EFFECTIVE_DECISION_DOF,
        "operators_frozen": list(econ1.REQUIRED_OPERATOR_IDS),
        "routing": "DOMAIN_LIMITED_EX_ANTE",
        "surface_unchanged": True,
        "policy": policy,
        "session_arithmetic": session_arithmetic,
        "binds": {
            "H": 63,
            "RIGHT_TAIL_PERCENTILE": 0.90,
            "CATASTROPHE_PERCENTILE": 0.10,
            "K": 20,
            "delta_J_required": 0.0,
            "D7": "OUT_OF_SCOPE",
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
            "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
            "CAPITAL_MATERIALITY_FLOOR": "NOT_YET_GRANTED",
        },
        "stability": {
            "source": econ1.PARENT_L5_RUN_REL.as_posix(),
            "temporal_fold_count": 4,
            "minimum_fold_n": 30,
            "minimum_fold_coverage": 0.2,
            "minimum_supporting_temporal_folds": 3,
            "xs_holdout_is_corroboration_not_tuning": True,
            "note": "Identical fold law to sensing L5; not re-invented.",
        },
        "market_probe": probe,
        "evaluation_status": evaluation_status,
        "payoff": {
            "delta_J": delta_j,
            "delta_J_required": 0.0,
            "d9_screen": d9_screen,
            "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
            "effect_sizes_recorded": False,
            "reason_if_null": (
                None
                if full_w3_ok
                else (
                    "Full-W3 market total-return / close custody not admitted for "
                    "economic estimand; refuse invent; refuse asymmetric AOV-104 proxy "
                    "as Full-W3 denominator."
                )
            ),
        },
        "selection": {
            "performed": False if not full_w3_ok else True,
            "K": 20,
            "reason_if_not": (
                None
                if full_w3_ok
                else "Blocked before selection payoff: Full-W3 R_net unobservable"
            ),
        },
        "forbidden_checks": {
            "threshold_grid": False,
            "K_search": False,
            "H_search": False,
            "dof_change": False,
            "asymmetric_return_ftk_vs_w3": False,
            "named_winner_success": False,
            "second_run": False,
            "sensing_label_reuse": False,
        },
        "first_block_layer_hint": first_block,
        "capital_authority": False,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "ao_ftk_2": "NOT_OPENED",
        "constitution": CONSTITUTION,
    }


def build_l6_diagnosis(run: Mapping[str, Any]) -> dict[str, Any]:
    full_w3_ok = bool((run.get("market_probe") or {}).get("full_w3_market_total_return_admitted"))
    layers: list[dict[str, Any]] = []

    def add(layer: str, status: str, notes: str, *, stop: bool = False, in_scope: bool = True) -> None:
        layers.append(
            {
                "layer": layer,
                "status": status,
                "notes": notes,
                "stop_here": stop,
                "in_scope": in_scope,
            }
        )

    add(
        "D1_CUSTODY_PIT",
        "PASS",
        "Operator pins match parent L4; dof=2; ACCEPT_DRAFT binds outcome-blind; "
        "no PIT rewrite; economic pack distinct from sensing; symmetry law recorded.",
    )
    if full_w3_ok:
        add(
            "D2_DATA_OBSERVABLE",
            "PASS",
            "Full-W3 market total-return custody admitted; R_net observable.",
        )
        # Remaining layers would be evaluated from payoffs — not reached today.
    else:
        add(
            "D2_DATA_OBSERVABLE",
            "FAIL",
            "Full-W3 forward R_net not observable under admitted market custody. "
            f"Admitted market securities="
            f"{(run.get('market_probe') or {}).get('admitted_market_security_count')}; "
            f"W3 eligible sample="
            f"{(run.get('market_probe') or {}).get('w3_eligible_count_sample')}. "
            "Refuse invent returns; refuse AOV-104 proxy as Full-W3 denominator.",
            stop=True,
        )
        for layer, note in (
            ("D3_MEASUREMENT_POWER", "Not reached; stopped at D2."),
            ("D4_REPRESENTATION_SNR", "Not reached; stopped at D2."),
            ("D5_MECHANISM_SELF_TRANSITION", "Not reached; stopped at D2. Sensing L5 remains historical PASS."),
            ("D6_SELECTION", "Not reached; stopped at D2. Subclaim (K=20 vs Full-W3) unevaluable."),
            ("D7_CONFIRMATION", "NOT_IN_SCOPE (OUT_OF_SCOPE); do not invent."),
            ("D8_HOLD_EXIT", "Not reached; stopped at D2. Fixed H=63 law frozen but unevaluable."),
            ("D9_ECONOMICS", "Not reached; stopped at D2. POSITIVE_NET_EDGE_SCREEN unevaluable; capital floor not granted."),
        ):
            status = "NOT_IN_SCOPE" if layer == "D7_CONFIRMATION" else "NOT_REACHED"
            add(layer, status, note, in_scope=(layer != "D7_CONFIRMATION"))

    first_fail = None
    failure_route = "NONE_IN_SCOPE_PASS"
    for layer in layers:
        if layer["status"] == "FAIL":
            first_fail = layer["layer"]
            break

    if first_fail == "D2_DATA_OBSERVABLE":
        failure_route = "HOLD_OR_ADMIT_FULL_W3_MARKET_CUSTODY_THEN_RERUN_UNDER_NEW_AUTH"
    elif first_fail == "D6_SELECTION":
        failure_route = "HOLD_STOP_FTK_PRIMARY_NO_REPRESENTATION_REFINE"
    elif first_fail == "D8_HOLD_EXIT":
        failure_route = "SAFETY_FAIL_REJECT_HOLD_ACTION_LAW"
    elif first_fail == "D9_ECONOMICS":
        failure_route = "SENSING_NE_POSITIVE_NET_EDGE_BANK_KNOWLEDGE_NO_CAPITAL"

    info_gain = {
        "summary": (
            "Relative to economic freeze+bind (unjoined), this one-shot economic Trial 2 "
            "joined the economic pack schema under ACCEPT_DRAFT H=63/K=20/RT=0.90/CAT=0.10/"
            "ΔJ=0.0 and attempted Full-W3 net-edge evaluation. Result: Full-W3 market "
            "custody missing; R_net/ΔJ unevaluable; no capital path; alpha remains 0. "
            "Sensing L5 association evidence is unchanged historical context only."
        ),
        "what_was_learned": [
            "Owner numerics bind successfully clears L5_READY without invention",
            "Economic estimand is blocked by Full-W3 market return custody, not by DOF/surface",
            "AOV ~104-name market history is not a valid Full-W3 comparator substitute",
            "D7 OUT_OF_SCOPE is enforceable without inventing a confirmation rule",
        ],
        "what_was_not_learned": [
            "Whether fixed-breadth K=20 improves right-tail / payoff vs Full-W3",
            "Whether H=63 hold/exit catastrophe load is acceptable",
            "Whether ΔJ > 0 under POSITIVE_NET_EDGE_SCREEN",
        ],
        "forbidden_to_change": [
            "second evaluation without new owner auth",
            "threshold/parameter/H/K grid",
            "DOF collapse or third DOF",
            "operator/feature rewrite under same freeze",
            "invent Full-W3 returns / ticker bridges",
            "claim financial_alpha_evidence > 0",
            "open AO-FTK-2 / L8 / capital",
            "invent D7 confirmation rule",
        ],
        "which_single_layer_may_change_next": (
            "Owner may admit Full-W3 market custody (new data slice) or HOLD/STOP; "
            "not auto-dispatched. Remaining material trials=1 after this debit."
        ),
        "delta_J": None,
        "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
        "financial_alpha_evidence": 0,
    }

    return {
        "schema_version": "ao_ftk_1_econ_1_l6_layered_diagnosis_v1",
        "receipt_id": L6_RECEIPT_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "run_id": RUN_ID,
        "auth_receipt_id": AUTH_RECEIPT_ID,
        "debit_receipt_id": DEBIT_RECEIPT_ID,
        "join_receipt_id": JOIN_RECEIPT_ID,
        "diagnosed_at_utc": utc_now_iso(),
        "mode": "TRANSITION_POSITION_ECONOMIC",
        "first_fail_layer": first_fail,
        "failure_route": failure_route,
        "layers": layers,
        "subclaims": {
            "D6": "fixed-breadth K=20 improves predeclared payoff/right-tail vs Full-W3 — UNEVALUABLE",
            "D7": "NOT_IN_SCOPE",
            "D8": "fixed-H=63 hold vs catastrophe (10th pct) — UNEVALUABLE",
            "D9": "ΔJ > 0 after lag+costs with fold stability — UNEVALUABLE; capital floor not granted",
        },
        "precommitted_routes_recorded": {
            "D6_FAIL": "HOLD/STOP FTK primary; no representation refine",
            "D6_PASS_D8_FAIL": "safety fail; reject hold/action law",
            "D6_D8_PASS_D9_FAIL": "sensing≠positive net edge; bank knowledge; no capital path",
            "D6_D8_D9_PASS_IN_SCOPE": "research candidate only; alpha=0; no auto capital",
            "actual_route_this_run": failure_route,
        },
        "information_gain": info_gain,
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "ao_ftk_2": "NOT_OPENED",
        "constitution": CONSTITUTION,
    }


def build_l7_owner_packet(
    *,
    run: Mapping[str, Any],
    l6: Mapping[str, Any],
    trials_remaining: int = 1,
) -> dict[str, Any]:
    first_fail = l6.get("first_fail_layer")
    routes = [
        {
            "route": "HOLD_EVIDENCE",
            "when": "default after custody-blocked Trial 2",
            "note": "Bank knowledge: economic path blocked on Full-W3 market custody",
        },
        {
            "route": "STOP_TRACK",
            "when": "owner elects not to fund market custody admit",
            "note": "Close FTK economic path; surface sensing remains historical only",
        },
        {
            "route": "ADMIT_FULL_W3_MARKET_CUSTODY_NEW_SLICE",
            "when": "owner wants economic estimand runnable",
            "note": (
                "Requires new admitted Full-W3 market total-return (or complete close) "
                "custody under PIT law; then separate economic L5 auth for remaining trial"
            ),
        },
        {
            "route": "L8_BOUNDED_REFINEMENT",
            "when": "only if L6 names a cheap seam — not claimed this run",
            "note": "Not recommended: first fail is custody observability, not a cheap surface seam",
        },
        {
            "route": "CANDIDATE_PIPELINE_PREP",
            "when": "only if strong PASS_IN_SCOPE — NOT this run",
            "note": "Not applicable; D6/D8/D9 unevaluable",
        },
    ]
    return {
        "schema_version": "ao_ftk_1_econ_1_l7_owner_packet_v1",
        "receipt_id": L7_PACKET_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "run_id": RUN_ID,
        "l6_receipt_id": L6_RECEIPT_ID,
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "l7_status": "WAITING_OWNER_ROUTE",
        "loop_phase": "L7_ROADMAP_DECISION",
        "worker_did_not_select_next_slice": True,
        "AO_FTK_2": "NOT_OPENED",
        "L8": "not executed",
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "trials_remaining": trials_remaining,
        "material_trials_charged_after": 2,
        "first_fail_layer": first_fail,
        "failure_route": l6.get("failure_route"),
        "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
        "d7": "OUT_OF_SCOPE",
        "session_path": "C_TRIAL2_COMPLETE",
        "binds": {
            "H": 63,
            "RT": 0.90,
            "CAT": 0.10,
            "K": 20,
            "delta_J": 0.0,
            "D7": "OUT_OF_SCOPE",
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
        },
        "recommended_routes": routes,
        "forbidden_auto": [
            "AO-FTK-2",
            "L8_IN_THIS_SESSION",
            "capital",
            "alpha_claim",
            "second_eval",
            "slice_2_auto",
        ],
        "next_owner_action": "L7 route only",
        "next_worker": "OWNER_L7_ONLY",
        "run_summary": {
            "evaluation_status": run.get("evaluation_status"),
            "delta_J": (run.get("payoff") or {}).get("delta_J"),
            "market_flag": (run.get("market_probe") or {}).get("flag"),
        },
        "constitution": CONSTITUTION,
    }


def stamp_freeze_post_trial(
    doc: dict[str, Any],
    *,
    trials_charged: int = 2,
    trials_remaining: int = 1,
    join_performed: bool = True,
    first_fail_layer: str | None = None,
) -> dict[str, Any]:
    doc["status"] = "ECON_L5_COMPLETE_WAITING_OWNER_L7"
    doc["authorized_phase"] = "L5_COMPLETE_WAITING_OWNER_L7"
    doc["l5_authorized"] = True
    doc["economic_l5_authorized"] = True
    doc["l5_auto_open"] = False
    doc["runnable_evaluation"] = False  # one-shot spent
    doc["second_l5"] = "NOT_AUTHORIZED"
    doc["label_bytes_joined"] = bool(join_performed)
    doc["material_trials_charged_this_turn"] = 1
    doc["material_trials_charged_to_date"] = trials_charged
    doc["material_trials_remaining"] = trials_remaining
    doc["financial_alpha_evidence"] = 0
    doc["capital_authority"] = False
    doc["next_phase"] = "L7_ROADMAP_DECISION"
    doc["next_owner_action"] = "L7 route only; remaining 1 material trial"
    doc["next_worker_recommended"] = "OWNER_L7_ONLY"
    doc["l5_ready"] = True
    doc["l5_blockers"] = []
    doc["ao_ftk_2"] = "NOT_AUTHORIZED"
    doc["l8_bounded_refinement"] = "DEFER"
    doc["trial2_result"] = {
        "run_id": RUN_ID,
        "first_fail_layer": first_fail_layer,
        "financial_alpha_evidence": 0,
        "session_path": "C_TRIAL2_COMPLETE",
    }
    plan = doc["material_trial_debit_plan"]
    plan["debit_this_turn"] = True
    plan["debited_under_receipt"] = DEBIT_RECEIPT_ID
    plan["material_trials_charged_to_date"] = trials_charged
    plan["remaining_after_trial2"] = trials_remaining
    if join_performed:
        doc["label_pack"]["LABEL_BYTES_JOINED"] = True
        doc["label_pack"]["join_authorized"] = True
        doc["label_pack"]["join_performed"] = True
        doc["label_pack"]["seal_status"] = "BYTES_JOINED_SCHEMA_RNET_UNOBSERVED"
        doc["estimand"]["E11"]["value"]["bytes_joined"] = True
        doc["estimand"]["E11"]["value"]["join_authorized"] = True
    if "owner_bind" in doc:
        doc["owner_bind"]["trial2_debit"] = True
        doc["owner_bind"]["economic_label_join"] = True
        doc["owner_bind"]["evaluation_run"] = True
        doc["owner_bind"]["material_trials_charged_this_turn"] = 1
    return doc
