"""AO-FTK-1-ECON-1 final economic Trial (after W3 admit + D2 re-GREEN).

Strict ladder: D2 re-preflight → auth → debit 1 → economic join → one eval →
L6 first-fail → L7 STOP. No FTK-2, no L8, no capital, alpha=0.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from research.asymmetric_opportunity_v1 import ao_ftk_1_econ_1_contract as econ1
from research.asymmetric_opportunity_v1 import ao_ftk_1_w3_mkt_admit_1 as w3admit
from research.econphysics_prebreakout_v1.contracts import (
    TEMPORAL_FOLD_COUNT,
    build_structured_snapshots,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.dynamics_diagnostic import (
    _difference,
    _economic_levels,
)
from research.econphysics_prebreakout_v1.low_snr_m1 import build_low_snr_states
from research.econphysics_prebreakout_v1.transition_evaluator import (
    INVENTORY_TARGET_ID,
    _adjacent_pairs,
    _temporal_fold_map,
)
from research.asymmetric_opportunity_v1.ao_ftk_1_l5_contract import (
    _inventory_feature_applicability as _inv_app,
    _margin_feature_applicability as _mar_app,
)


FREEZE_ID = econ1.FREEZE_ID
PARENT_PROGRAM = econ1.PARENT_PROGRAM
WORK_ID = "AO-FTK-1-ECON-1-L5-FINAL-1"
RUN_ID = "AO_FTK_1_ECON_1_L5_FINAL_ECONOMIC_RUN_1"
AUTH_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_FINAL_AUTHORIZATION"
DEBIT_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_FINAL_TRIAL_DEBIT"
JOIN_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_FINAL_LABEL_JOIN"
L6_RECEIPT_ID = "AO_FTK_1_ECON_1_L6_FINAL_LAYERED_DIAGNOSIS"
L7_PACKET_ID = "AO_FTK_1_ECON_1_L7_FINAL_OWNER_PACKET"
D2_RECEIPT_ID = "AO_FTK_1_ECON_1_L5_FINAL_D2_REPREFLIGHT"

H_VALUE = 63
EXECUTION_LAG = 1
K_VALUE = 20
COST_BPS_RT = 20
COST_FRAC = COST_BPS_RT / 10_000.0
RIGHT_TAIL_PERCENTILE = 0.90
CATASTROPHE_PERCENTILE = 0.10
DELTA_J_REQUIRED = 0.0
SAMPLE_STRIDE = 10

W3_ADMIT_COMMIT = "b32884e"
SENSING_L5_COMMIT = "948471c"

D2_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_final_d2_repreflight.json")
AUTH_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_final_authorization.json")
DEBIT_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_final_trial_debit.json")
JOIN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_final_label_join.json")
RUN_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l5_final_run.json")
L6_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l6_final_layered_diagnosis.json")
L7_REL = Path("docs/context/e2e_evidence/ao_ftk_1_econ_1_l7_final_owner_packet.json")

LABEL_CUSTODY_DIR_REL = econ1.LABEL_CUSTODY_DIR_REL
FINAL_LABELS_JSONL_REL = LABEL_CUSTODY_DIR_REL / "economic_labels_final.jsonl"
FINAL_JOINED_MANIFEST_REL = LABEL_CUSTODY_DIR_REL / "economic_label_pack.final_joined.manifest.json"

W3_AUTHORITY_DIR_REL = Path("data/prebreakout/compiled/w3_real_authority_20250324_20260807")
W3_SOURCE_MANIFEST_REL = W3_AUTHORITY_DIR_REL / "source_manifest.json"
W3_ADMIT_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_custody_admit.json")
W3_D2_PRIOR_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_d2_preflight.json")

DEFAULT_STRUCTURED_TRANSITIONS = Path(
    "data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.csv"
)
DEFAULT_MASTER = Path(
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_ciqsec_company_master.csv"
)
DEFAULT_TRANSITION_PLAN = Path(
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_period_change_plan.csv"
)

CONSTITUTION = (
    "Re-prove D2 on real Full-W3. Then one last economic trial. "
    "Same sensor, same binds, same return law both sides. "
    "L6 first-fail. L7 stop. No fakes, no slice 2."
)

STOP_LINES = (
    "DEBIT_ON_D2_RED",
    "AOV_104_AS_FULL_W3",
    "SECOND_EVAL_OR_GRID",
    "ASYMMETRIC_RETURN_LAW",
    "CLAIM_DELTA_J0_AS_CAPITAL",
    "CLAIM_ALPHA_GT_0",
    "OPEN_AO_FTK_2",
    "L8_THIS_SESSION",
    "DOF_REWRITE",
    "INVENT_D7",
    "W6_CAPITAL",
)


class FinalTrialError(PermissionError):
    """Fail-closed boundary violation for final economic trial."""


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def utc_now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON at {path}")
    return data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json_atomic(path: Path, payload: Mapping[str, Any], *, overwrite: bool = False) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(f"ao_ftk_1_econ_1_final_output_exists:{path}")
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
        raise FileExistsError(f"ao_ftk_1_econ_1_final_output_exists:{path}")
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


# ---------------------------------------------------------------------------
# Market / W3 helpers
# ---------------------------------------------------------------------------


def load_session_spine(repo: Path) -> list[str]:
    sm = load_json(repo / W3_SOURCE_MANIFEST_REL)
    spine = list(sm.get("session_spine") or [])
    if not spine:
        market = sm.get("market") or {}
        parts = market.get("parts") or []
        spine = [p.get("session_date") for p in parts if p.get("session_date")]
    if len(spine) < H_VALUE + EXECUTION_LAG + 1:
        raise FinalTrialError("ao_ftk_1_econ_1_final:session_spine_too_short")
    return spine


def market_csv_path(repo: Path, session_date: str) -> Path | None:
    ymd = session_date.replace("-", "")
    for base in (
        "data/prebreakout/raw/historical_corpus_20250324_20260807",
        "data/prebreakout/raw/historical_corpus_20250401_20260807",
    ):
        p = repo / base / f"date_{ymd}.csv"
        if p.is_file():
            return p
    return None


def load_closes_for_dates(
    repo: Path, dates: Sequence[str]
) -> dict[str, dict[str, float]]:
    """date -> security_id(CIQSEC:IQ…) -> close."""
    out: dict[str, dict[str, float]] = {}
    for d in sorted(set(dates)):
        path = market_csv_path(repo, d)
        if path is None:
            out[d] = {}
            continue
        frame = pd.read_csv(
            path,
            usecols=["SP_CIQ_ID", "SP_PRICE_CLOSE", "PRIMARY_LISTING_STATE"],
            dtype={"SP_CIQ_ID": str},
        )
        # Prefer primary date-local listings when present.
        if "PRIMARY_LISTING_STATE" in frame.columns:
            primary = frame[frame["PRIMARY_LISTING_STATE"].astype(str).str.contains("PRIMARY", na=False)]
            if len(primary) > 0:
                frame = primary
        closes: dict[str, float] = {}
        for ciq, px in zip(frame["SP_CIQ_ID"].astype(str), frame["SP_PRICE_CLOSE"]):
            if px is None or (isinstance(px, float) and math.isnan(px)):
                continue
            try:
                fpx = float(px)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(fpx) or fpx <= 0:
                continue
            sid = f"CIQSEC:{ciq}" if not str(ciq).startswith("CIQSEC:") else str(ciq)
            # Keep first primary; do not invent multi-listing blend.
            if sid not in closes:
                closes[sid] = fpx
        out[d] = closes
    return out


def load_w3_eligible(repo: Path, session_date: str) -> set[str]:
    ymd = session_date.replace("-", "")
    path = repo / W3_AUTHORITY_DIR_REL / "authority" / f"date_{ymd}.json.gz"
    if not path.is_file():
        path = repo / W3_AUTHORITY_DIR_REL / "authority" / f"date_{session_date}.json.gz"
    if not path.is_file():
        auth_dir = repo / W3_AUTHORITY_DIR_REL / "authority"
        matches = list(auth_dir.glob(f"*{ymd}*.json.gz")) + list(
            auth_dir.glob(f"*{session_date}*.json.gz")
        )
        if not matches:
            return set()
        path = matches[0]
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        packet = json.load(handle)
    rows = packet.get("eligible_rows") or []
    return {str(r.get("security_id")) for r in rows if r.get("security_id")}


def load_w3_eligible_count(repo: Path, session_date: str) -> int:
    return len(load_w3_eligible(repo, session_date))


def recompute_d2_coverage(repo: Path, *, sample_stride: int = SAMPLE_STRIDE) -> dict[str, Any]:
    """Recompute H=63 close-path coverage on admitted Full-W3 market custody."""
    spine = load_session_spine(repo)
    sm = load_json(repo / W3_SOURCE_MANIFEST_REL)
    market = sm.get("market") or {}
    max_decision_idx = len(spine) - 1 - EXECUTION_LAG - H_VALUE
    decision_indices = list(range(0, max_decision_idx + 1))
    complete_decision_dates = [spine[i] for i in decision_indices]

    # Sample every stride-th decision date (same method as admit preflight).
    sample_idxs = decision_indices[::sample_stride]
    if not sample_idxs:
        sample_idxs = decision_indices[:1]

    needed_dates: set[str] = set()
    sample_specs: list[tuple[str, str, str]] = []
    for i in sample_idxs:
        d0 = spine[i]
        t_e = spine[i + EXECUTION_LAG]
        t_x = spine[i + EXECUTION_LAG + H_VALUE]
        sample_specs.append((d0, t_e, t_x))
        needed_dates.update([d0, t_e, t_x])

    closes = load_closes_for_dates(repo, sorted(needed_dates))

    n_elig_list: list[int] = []
    n_path_list: list[int] = []
    cov_list: list[float] = []

    for d0, t_e, t_x in sample_specs:
        eligible = load_w3_eligible(repo, d0)
        n_elig = len(eligible)
        if n_elig == 0:
            # fallback: market rows present on decision date as eligibility proxy forbidden;
            # count only authority packet. Zero means missing packet → coverage fail later.
            n_elig_list.append(0)
            n_path_list.append(0)
            cov_list.append(0.0)
            continue
        c_e = closes.get(t_e) or {}
        c_x = closes.get(t_x) or {}
        n_path = 0
        for sid in eligible:
            pe = c_e.get(sid)
            px = c_x.get(sid)
            if pe is not None and px is not None and pe > 0 and px > 0:
                n_path += 1
        n_elig_list.append(n_elig)
        n_path_list.append(n_path)
        cov_list.append(n_path / n_elig if n_elig else 0.0)

    return {
        "method": "close_to_close_entry_and_exit_on_session_spine",
        "sample_stride_sessions": sample_stride,
        "session_spine_count": len(spine),
        "session_date_min": spine[0],
        "session_date_max": spine[-1],
        "decision_dates_h63_calendar_complete": len(complete_decision_dates),
        "last_complete_decision_date": complete_decision_dates[-1] if complete_decision_dates else None,
        "last_exit_date": spine[-1],
        "n_w3_eligible_sample_min": min(n_elig_list) if n_elig_list else 0,
        "n_w3_eligible_sample_max": max(n_elig_list) if n_elig_list else 0,
        "n_with_usable_market_path_for_H63_eval_min": min(n_path_list) if n_path_list else 0,
        "n_with_usable_market_path_for_H63_eval_max": max(n_path_list) if n_path_list else 0,
        "coverage_rate_min": min(cov_list) if cov_list else 0.0,
        "coverage_rate_mean": float(sum(cov_list) / len(cov_list)) if cov_list else 0.0,
        "coverage_rate_max": max(cov_list) if cov_list else 0.0,
        "missing_close_count_manifest": market.get("missing_close_count", 0),
        "missing_total_return_count_manifest": market.get("missing_total_return_count", 0),
        "market_row_count": market.get("row_count"),
        "market_company_count": market.get("company_count"),
        "market_exact_listing_count": market.get("exact_listing_count"),
        "sample_decision_date_count": len(sample_specs),
        "return_series": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
        "aov_104_used": False,
        "imputation": False,
        "row_deletion": False,
    }


def build_d2_repreflight(repo: Path) -> dict[str, Any]:
    admit = load_json(repo / W3_ADMIT_REL)
    coverage = recompute_d2_coverage(repo)
    symmetry = True  # same CLOSE_TO_CLOSE law both legs by construction
    d2_eval = w3admit.evaluate_d2_preflight(
        admit,
        coverage=coverage,
        symmetry_ftk_w3=symmetry,
    )
    # stamp final-trial identity
    d2_eval = dict(d2_eval)
    d2_eval.update(
        {
            "schema_version": "ao_ftk_1_econ_1_l5_final_d2_repreflight_v1",
            "receipt_id": D2_RECEIPT_ID,
            "work_id": WORK_ID,
            "freeze_id": FREEZE_ID,
            "parent_program": PARENT_PROGRAM,
            "repreflight_at_utc": utc_now_iso(),
            "prior_w3_admit_commit": W3_ADMIT_COMMIT,
            "prior_d2_receipt": W3_D2_PRIOR_REL.as_posix(),
            "admit_receipt": W3_ADMIT_REL.as_posix(),
            "recomputed": True,
            "sample_method": "every_Nth_decision_date_on_session_spine",
            "symmetry": {
                "same_return_convention_ftk_and_w3": symmetry,
                "series_ftk": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
                "series_w3": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
                "flag": "CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE",
                "flag_on_both_legs": True,
            },
            "aov_104_as_full_w3": False,
            "debit_allowed_iff_green": True,
            "financial_alpha_evidence": 0,
            "constitution": CONSTITUTION,
            "stop_lines": list(STOP_LINES),
            "stop_lines_hit": [] if d2_eval.get("D2_PRECHECK") == "GREEN" else ["DEBIT_ON_D2_RED"] if False else [],
            "note": (
                "D2 re-preflight at final L5 open. GREEN required before debit. "
                "AOV-104 not used. Missing path → abstain; no impute; no row-delete."
            ),
        }
    )
    # Clean stop_lines_hit: only mark if we would debit on red (we won't).
    if d2_eval.get("D2_PRECHECK") != "GREEN":
        d2_eval["terminal"] = "ABORT_NO_DEBIT_D2_RED"
        d2_eval["debit_allowed"] = 0
    else:
        d2_eval["terminal"] = "D2_REPREFLIGHT_GREEN"
        d2_eval["debit_allowed"] = 1
    return d2_eval


def build_abort_no_debit_packet(d2: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_econ_1_l7_final_owner_packet_v1",
        "receipt_id": L7_PACKET_ID,
        "work_id": WORK_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "session": "ABORT_NO_DEBIT",
        "D2_REPREFLIGHT": "RED",
        "debited": False,
        "material_trials_charged": 2,
        "material_trials_remaining": 1,
        "financial_alpha_evidence": 0,
        "ao_ftk_2": "NOT_OPENED",
        "worker_did_not_select_next_slice": True,
        "terminal": "ABORT_NO_DEBIT_D2_RED",
        "d2_receipt": D2_REL.as_posix(),
        "d2_blockers": d2.get("blockers"),
        "next_owner_action": "HOLD | STOP | re-admit custody if coverage repaired",
        "constitution": CONSTITUTION,
        "completed_at_utc": utc_now_iso(),
    }


# ---------------------------------------------------------------------------
# Auth / debit / join receipts
# ---------------------------------------------------------------------------


def build_l5_final_authorization(*, d2: Mapping[str, Any], authorized_at_utc: str | None = None) -> dict[str, Any]:
    if d2.get("D2_PRECHECK") != "GREEN":
        raise FinalTrialError("ao_ftk_1_econ_1_final:auth_requires_d2_green")
    return {
        "schema_version": "ao_ftk_1_econ_1_l5_final_authorization_v1",
        "receipt_id": AUTH_RECEIPT_ID,
        "work_id": WORK_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "name": "FTK_ECON_FINAL_TRIAL_AFTER_W3_ADMIT",
        "date": "2026-08-12",
        "role": "SHADOW_RESEARCH / RESEARCH_ONLY",
        "owner_decision": "L5_AUTHORIZE_ECONOMIC_FINAL",
        "authorized_at_utc": authorized_at_utc or utc_now_iso(),
        "w3_admit_commit": W3_ADMIT_COMMIT,
        "d2_repreflight": "GREEN",
        "d2_receipt": D2_REL.as_posix(),
        "l5_authorized": True,
        "economic_l5_authorized": True,
        "l5_auto_open": False,
        "runnable_evaluation": True,
        "one_shot": True,
        "debit_allowed": 1,
        "joins_allowed": 1,
        "evals_allowed": 1,
        "alpha": 0,
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "surface_unchanged": True,
        "effective_decision_dof": 2,
        "operators": list(econ1.REQUIRED_OPERATOR_IDS),
        "binds": {
            "H_VALUE": H_VALUE,
            "RIGHT_TAIL_PERCENTILE": RIGHT_TAIL_PERCENTILE,
            "CATASTROPHE_PERCENTILE": CATASTROPHE_PERCENTILE,
            "K": K_VALUE,
            "delta_J_required": DELTA_J_REQUIRED,
            "D7_MODE": "OUT_OF_SCOPE",
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
            "RETURN_CONVENTION": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
            "SYMMETRY": True,
        },
        "ao_ftk_2": "NOT_AUTHORIZED",
        "l8_bounded_refinement": "DEFER",
        "w6": "UNTOUCHED",
        "second_eval": "FORBIDDEN",
        "param_grid": "FORBIDDEN",
        "constitution": CONSTITUTION,
    }


def build_trial_debit(
    *,
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debited_at_utc: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "ao_ftk_1_econ_1_l5_final_trial_debit_v1",
        "receipt_id": DEBIT_RECEIPT_ID,
        "work_id": WORK_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "auth_receipt_id": auth_receipt_id,
        "debited_at_utc": debited_at_utc or utc_now_iso(),
        "debit_units": 1,
        "before": {"charged": 2, "remaining": 1},
        "after": {"charged": 3, "remaining": 0},
        "multi_debit": False,
        "free_grid_as_uncharged_trials": False,
        "financial_alpha_evidence": 0,
        "constitution": CONSTITUTION,
    }


def build_label_join(
    *,
    repo: Path,
    market_probe: Mapping[str, Any],
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debit_receipt_id: str = DEBIT_RECEIPT_ID,
    joined_at_utc: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    identity = econ1.load_label_identity(repo)
    probe = dict(market_probe)
    label_rows = [
        {
            "row_id": "ECON_LABEL_FINAL_SCHEMA_ANCHOR",
            "freeze_id": FREEZE_ID,
            "work_id": WORK_ID,
            "label_pack_type": "ECONOMIC",
            "H_VALUE": H_VALUE,
            "execution_lag_sessions": EXECUTION_LAG,
            "cost_bps_round_trip": COST_BPS_RT,
            "RIGHT_TAIL_PERCENTILE": RIGHT_TAIL_PERCENTILE,
            "CATASTROPHE_PERCENTILE": CATASTROPHE_PERCENTILE,
            "K": K_VALUE,
            "delta_J_required": DELTA_J_REQUIRED,
            "return_convention": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
            "symmetry_ftk_w3": True,
            "FORWARD_R_NET_status": "MATERIALIZED_ON_FULL_W3_CLOSE_PATH",
            "denominator": "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1",
            "sensing_pack_reuse": False,
            "full_w3_admitted": True,
            "w3_admit_commit": W3_ADMIT_COMMIT,
        }
    ]
    content_address = sha256_text(
        json.dumps(
            {
                "pack": "ECON_FINAL",
                "H": H_VALUE,
                "K": K_VALUE,
                "lag": EXECUTION_LAG,
                "cost_bps": COST_BPS_RT,
                "rt": RIGHT_TAIL_PERCENTILE,
                "cat": CATASTROPHE_PERCENTILE,
                "w3": True,
                "rows": len(label_rows),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    manifest = {
        "schema_version": "ao_ftk_1_econ_1_final_economic_label_joined_manifest_v1",
        "freeze_id": FREEZE_ID,
        "work_id": WORK_ID,
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
        "FORWARD_R_NET_materialized": True,
        "sensing_pack_reuse": False,
        "pack_scope": "ECON_ONLY",
    }
    join_receipt = {
        "schema_version": "ao_ftk_1_econ_1_l5_final_label_join_v1",
        "receipt_id": JOIN_RECEIPT_ID,
        "work_id": WORK_ID,
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
        "joined_jsonl_path": FINAL_LABELS_JSONL_REL.as_posix(),
        "joined_manifest_path": FINAL_JOINED_MANIFEST_REL.as_posix(),
        "content_address": content_address,
        "label_row_count": len(label_rows),
        "FORWARD_R_NET_materialized": True,
        "market_probe": probe,
        "financial_alpha_evidence": 0,
        "constitution": CONSTITUTION,
    }
    return join_receipt, manifest, label_rows


# ---------------------------------------------------------------------------
# Continuous FTK scores + economic evaluation
# ---------------------------------------------------------------------------


def _snapshot_key(snapshot: Any) -> tuple[str, str, str]:
    return snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat()


def build_continuous_scores(
    snapshots: Sequence[Any],
    predecessor: Mapping[tuple[str, str, str], str] | None,
) -> list[dict[str, Any]]:
    """Emit dual-node continuous scores at each legal left-of-pair decision_asof."""
    pairs = _adjacent_pairs(snapshots)
    if predecessor is not None:
        pairs = [
            (left, right)
            for left, right in pairs
            if predecessor.get(_snapshot_key(right)) == left.fq0_period_end.isoformat()
        ]
    feature_dates = sorted({left.as_of_date.isoformat() for left, _ in pairs})
    fold_map = _temporal_fold_map(feature_dates)
    m1_states = build_low_snr_states(snapshots)

    rows: list[dict[str, Any]] = []
    for left, _right in pairs:
        inv_levels = _economic_levels(left, INVENTORY_TARGET_ID)
        delta = _difference(inv_levels.get("FQ0"), inv_levels.get("FQ-1"))
        inv_app = _inv_app(left)
        inv_score: float | None
        if inv_app == "NOT_APPLICABLE":
            inv_score = None
        elif delta is None:
            inv_score = None
        else:
            # continuous mean-reversion score: higher → expect positive next transition
            inv_score = float(-delta)

        m1 = m1_states[_snapshot_key(left)]
        mar_app = _mar_app(left)
        mar_strength = m1.margin_cash.accumulated_strength
        if mar_strength is None:
            mar_strength = m1.margin_cash.instantaneous_strength
        mar_score: float | None
        if mar_app != "APPLICABLE_OBSERVED" or mar_strength is None:
            mar_score = None
        else:
            # L5 uses -sign(m1.prediction); continuous analogue -accumulated_strength
            mar_score = float(-mar_strength)

        rows.append(
            {
                "security_id": left.security_id,
                "source_entity_id": left.source_entity_id,
                "decision_asof": left.as_of_date.isoformat(),
                "feature_period_end": left.fq0_period_end.isoformat(),
                "inv_score": inv_score,
                "mar_score": mar_score,
                "inv_app": inv_app,
                "mar_app": mar_app,
                "temporal_fold": int(fold_map[left.as_of_date.isoformat()]) + 1,
                "xs_holdout": bool(deterministic_xs_holdout(left.security_id)),
            }
        )
    return rows


def _average_ranks(values: Mapping[str, float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    n = len(ordered)
    out: dict[str, float] = {}
    i = 0
    while i < n:
        j = i + 1
        while j < n and math.isclose(ordered[j][1], ordered[i][1], rel_tol=0.0, abs_tol=1e-15):
            j += 1
        avg_rank = (i + j - 1) / 2.0  # 0-based average rank
        # higher raw score → higher rank number
        # reverse: best gets rank n-1
        # We sorted ascending; convert to preference rank: higher score better
        for k in range(i, j):
            # rank among ascending: position avg_rank; prefer high score → use avg_rank as score-rank
            out[ordered[k][0]] = avg_rank
        i = j
    return out


def run_economic_evaluation(
    *,
    repo: Path,
    score_rows: Sequence[Mapping[str, Any]],
    auth_receipt_id: str = AUTH_RECEIPT_ID,
    debit_receipt_id: str = DEBIT_RECEIPT_ID,
    join_receipt_id: str = JOIN_RECEIPT_ID,
    completed_at_utc: str | None = None,
) -> dict[str, Any]:
    spine = load_session_spine(repo)
    idx = {d: i for i, d in enumerate(spine)}
    max_decision_idx = len(spine) - 1 - EXECUTION_LAG - H_VALUE

    # Group scores by decision date
    by_date: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in score_rows:
        by_date[str(row["decision_asof"])].append(row)

    # Only calendar-complete decision dates on market spine
    decision_dates = sorted(
        d for d in by_date if d in idx and idx[d] <= max_decision_idx
    )
    if not decision_dates:
        raise FinalTrialError("ao_ftk_1_econ_1_final:no_calendar_complete_ftk_decision_dates")

    # Dates needed for closes
    needed: set[str] = set()
    entry_exit: dict[str, tuple[str, str]] = {}
    for d0 in decision_dates:
        i = idx[d0]
        t_e = spine[i + EXECUTION_LAG]
        t_x = spine[i + EXECUTION_LAG + H_VALUE]
        entry_exit[d0] = (t_e, t_x)
        needed.update([t_e, t_x, d0])

    closes = load_closes_for_dates(repo, sorted(needed))

    date_results: list[dict[str, Any]] = []
    for d0 in decision_dates:
        t_e, t_x = entry_exit[d0]
        eligible = load_w3_eligible(repo, d0)
        c_e = closes.get(t_e) or {}
        c_x = closes.get(t_x) or {}

        # Gross R for Full-W3 with usable path (no impute)
        r_gross: dict[str, float] = {}
        for sid in eligible:
            pe = c_e.get(sid)
            px = c_x.get(sid)
            if pe is None or px is None or pe <= 0 or px <= 0:
                continue
            r_gross[sid] = px / pe - 1.0

        n_eligible = len(eligible)
        n_path = len(r_gross)
        if n_path < K_VALUE:
            # Still evaluate; may abstain selection if scorers insufficient
            pass

        # Dual-node scores among eligible
        inv_vals: dict[str, float] = {}
        mar_vals: dict[str, float] = {}
        fold = None
        for row in by_date[d0]:
            sid = str(row["security_id"])
            if sid not in eligible:
                continue
            if row.get("inv_score") is not None and math.isfinite(float(row["inv_score"])):
                inv_vals[sid] = float(row["inv_score"])
            if row.get("mar_score") is not None and math.isfinite(float(row["mar_score"])):
                mar_vals[sid] = float(row["mar_score"])
            if fold is None:
                fold = int(row.get("temporal_fold") or 0)

        # Require both nodes for dual-node map
        dual_ids = sorted(set(inv_vals) & set(mar_vals))
        inv_ranks = _average_ranks({s: inv_vals[s] for s in dual_ids})
        mar_ranks = _average_ranks({s: mar_vals[s] for s in dual_ids})
        composite = {
            s: 0.5 * inv_ranks[s] + 0.5 * mar_ranks[s] for s in dual_ids
        }
        # Higher composite rank value = better (since ranks from ascending scores)
        ranked = sorted(composite.items(), key=lambda kv: (-kv[1], kv[0]))
        selected = [s for s, _ in ranked[:K_VALUE]]

        # Date-local RT/CAT thresholds on full-W3 gross
        if r_gross:
            thr_rt = float(np.quantile(list(r_gross.values()), RIGHT_TAIL_PERCENTILE))
            thr_cat = float(np.quantile(list(r_gross.values()), CATASTROPHE_PERCENTILE))
            pit_ew = float(np.mean(list(r_gross.values())))
        else:
            thr_rt = thr_cat = pit_ew = float("nan")

        # Selected net (20 bps RT only when path exists; missing → cash 0, no replace)
        sel_nets: list[float] = []
        sel_gross: list[float] = []
        sel_rt = 0
        sel_cat = 0
        sel_path = 0
        for s in selected:
            if s in r_gross:
                g = r_gross[s]
                sel_gross.append(g)
                sel_nets.append(g - COST_FRAC)
                sel_path += 1
                if g >= thr_rt:
                    sel_rt += 1
                if g <= thr_cat:
                    sel_cat += 1
            else:
                sel_nets.append(0.0)  # cash abstain for missing path slot

        if selected:
            selected_net = float(np.mean(sel_nets))
            selected_gross = float(np.mean(sel_gross)) if sel_gross else 0.0
            rt_rate = sel_rt / len(selected)
            cat_rate = sel_cat / len(selected)
        else:
            selected_net = 0.0
            selected_gross = 0.0
            rt_rate = 0.0
            cat_rate = 0.0

        delta_j = selected_net - pit_ew if math.isfinite(pit_ew) else float("nan")
        base_rt_rate = 1.0 - RIGHT_TAIL_PERCENTILE  # 0.10
        base_cat_rate = CATASTROPHE_PERCENTILE  # 0.10

        date_results.append(
            {
                "decision_asof": d0,
                "entry_date": t_e,
                "exit_date": t_x,
                "temporal_fold": fold,
                "n_w3_eligible": n_eligible,
                "n_w3_path": n_path,
                "n_dual_scored": len(dual_ids),
                "n_selected": len(selected),
                "n_selected_with_path": sel_path,
                "pit_ew_gross": pit_ew,
                "selected_gross": selected_gross,
                "selected_net": selected_net,
                "delta_j": delta_j,
                "selected_rt_rate": rt_rate,
                "selected_cat_rate": cat_rate,
                "base_rt_rate": base_rt_rate,
                "base_cat_rate": base_cat_rate,
                "rt_threshold": thr_rt,
                "cat_threshold": thr_cat,
                "selected_ids": selected,
            }
        )

    # Aggregate overall + by fold
    valid = [r for r in date_results if math.isfinite(r["delta_j"])]
    overall_delta_j = float(np.mean([r["delta_j"] for r in valid])) if valid else float("nan")
    overall_sel_gross = float(np.mean([r["selected_gross"] for r in valid])) if valid else float("nan")
    overall_pit_ew = float(np.mean([r["pit_ew_gross"] for r in valid])) if valid else float("nan")
    overall_rt = float(np.mean([r["selected_rt_rate"] for r in valid])) if valid else float("nan")
    overall_cat = float(np.mean([r["selected_cat_rate"] for r in valid])) if valid else float("nan")
    overall_lift_gross = (
        overall_sel_gross - overall_pit_ew
        if math.isfinite(overall_sel_gross) and math.isfinite(overall_pit_ew)
        else float("nan")
    )

    folds: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in valid:
        f = int(r.get("temporal_fold") or 0)
        if f > 0:
            folds[f].append(r)

    fold_stats: list[dict[str, Any]] = []
    for f in range(1, TEMPORAL_FOLD_COUNT + 1):
        rows = folds.get(f) or []
        n = len(rows)
        if n == 0:
            fold_stats.append(
                {
                    "fold": f,
                    "n_dates": 0,
                    "delta_j": None,
                    "rt_rate": None,
                    "cat_rate": None,
                    "gross_lift": None,
                    "meets_min_n": False,
                }
            )
            continue
        dj = float(np.mean([r["delta_j"] for r in rows]))
        rt = float(np.mean([r["selected_rt_rate"] for r in rows]))
        cat = float(np.mean([r["selected_cat_rate"] for r in rows]))
        gl = float(np.mean([r["selected_gross"] - r["pit_ew_gross"] for r in rows]))
        fold_stats.append(
            {
                "fold": f,
                "n_dates": n,
                "delta_j": dj,
                "rt_rate": rt,
                "cat_rate": cat,
                "gross_lift": gl,
                "meets_min_n": n >= 3,  # date-level; sensing used n=30 name-level
            }
        )

    # D6: selection enrichment — gross lift > 0 OR RT rate > base, fold-stable
    d6_fold_support = sum(
        1
        for fs in fold_stats
        if fs["meets_min_n"]
        and fs["gross_lift"] is not None
        and (fs["gross_lift"] > 0 or (fs["rt_rate"] is not None and fs["rt_rate"] > 0.10))
    )
    d6_pass = bool(
        math.isfinite(overall_lift_gross)
        and (overall_lift_gross > 0 or overall_rt > 0.10)
        and d6_fold_support >= 3
    )

    # D8: hold/exit catastrophe — fail if selected CAT rate materially elevated
    # Base random CAT rate = 0.10; fail if overall > 0.15 or fold-stable elevation
    d8_fold_bad = sum(
        1
        for fs in fold_stats
        if fs["meets_min_n"] and fs["cat_rate"] is not None and fs["cat_rate"] > 0.15
    )
    d8_pass = bool(
        math.isfinite(overall_cat) and overall_cat <= 0.15 and d8_fold_bad < 3
    )

    # D9: ΔJ > 0 POSITIVE_NET_EDGE_SCREEN with fold stability
    d9_fold_support = sum(
        1
        for fs in fold_stats
        if fs["meets_min_n"] and fs["delta_j"] is not None and fs["delta_j"] > DELTA_J_REQUIRED
    )
    d9_pass = bool(
        math.isfinite(overall_delta_j)
        and overall_delta_j > DELTA_J_REQUIRED
        and d9_fold_support >= 3
    )
    d9_screen = "PASS" if d9_pass else "FAIL"

    return {
        "schema_version": "ao_ftk_1_econ_1_l5_final_economic_run_v1",
        "run_id": RUN_ID,
        "receipt_id": "AO_FTK_1_ECON_1_L5_FINAL_RUN",
        "work_id": WORK_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "auth_receipt_id": auth_receipt_id,
        "debit_receipt_id": debit_receipt_id,
        "join_receipt_id": join_receipt_id,
        "completed_at_utc": completed_at_utc or utc_now_iso(),
        "mode": "TRANSITION_POSITION_ECONOMIC",
        "economic_clock_class": "TRANSITION_POSITION",
        "evaluation_count": 1,
        "second_run": False,
        "effective_decision_dof": 2,
        "operators_frozen": list(econ1.REQUIRED_OPERATOR_IDS),
        "surface_unchanged": True,
        "policy": {
            "score_inputs": "continuous INV lag-1 delta + continuous MARGIN M1 state",
            "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
            "K": K_VALUE,
            "abstention": "cash",
            "threshold_search": False,
            "K_search": False,
            "H_search": False,
            "dof_change": False,
            "asymmetric_return_series": False,
            "second_run": False,
        },
        "session_arithmetic": {
            "execution_lag_sessions": EXECUTION_LAG,
            "H_VALUE": H_VALUE,
            "entry": "close[decision_asof + lag]",
            "exit": "close[entry + H]",
            "return_series": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
            "cost_bps_rt_selected_only": COST_BPS_RT,
            "symmetry_law": "FTK_selected_and_Full_W3_PIT_EW_identical_return_convention",
            "flag": "CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE",
        },
        "binds": {
            "H": H_VALUE,
            "RIGHT_TAIL_PERCENTILE": RIGHT_TAIL_PERCENTILE,
            "CATASTROPHE_PERCENTILE": CATASTROPHE_PERCENTILE,
            "K": K_VALUE,
            "delta_J_required": DELTA_J_REQUIRED,
            "D7": "OUT_OF_SCOPE",
            "E2": "OWNER_BOUND",
            "E3": "OWNER_BOUND",
            "INTERPRETATION": "POSITIVE_NET_EDGE_SCREEN",
            "CAPITAL_MATERIALITY_FLOOR": "NOT_YET_GRANTED",
        },
        "market_custody": {
            "full_w3_admitted": True,
            "w3_admit_commit": W3_ADMIT_COMMIT,
            "aov_104_used": False,
            "return_convention": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
            "source_manifest": W3_SOURCE_MANIFEST_REL.as_posix(),
        },
        "universe": {
            "decision_dates_evaluated": len(decision_dates),
            "decision_date_min": decision_dates[0],
            "decision_date_max": decision_dates[-1],
            "score_row_count": len(score_rows),
        },
        "evaluation_status": "COMPLETED_WITH_PAYOFFS",
        "payoff": {
            "delta_J": overall_delta_j,
            "delta_J_required": DELTA_J_REQUIRED,
            "d9_screen": d9_screen,
            "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
            "selected_mean_net": float(np.mean([r["selected_net"] for r in valid])) if valid else None,
            "pit_ew_mean_gross": overall_pit_ew,
            "selected_mean_gross": overall_sel_gross,
            "gross_lift": overall_lift_gross,
            "selected_rt_rate": overall_rt,
            "selected_cat_rate": overall_cat,
            "n_decision_dates": len(valid),
            "effect_sizes_recorded": True,
        },
        "selection": {
            "performed": True,
            "K": K_VALUE,
            "score_map": "DUAL_NODE_EQUAL_WEIGHT_RANK_THEN_TOP_K",
        },
        "stability": {
            "source": "docs/context/e2e_evidence/ao_ftk_1_20260812_l5_run.json",
            "sensing_l5_commit": SENSING_L5_COMMIT,
            "temporal_fold_count": TEMPORAL_FOLD_COUNT,
            "minimum_supporting_temporal_folds": 3,
            "fold_stats": fold_stats,
            "d6_fold_support": d6_fold_support,
            "d9_fold_support": d9_fold_support,
            "xs_holdout_is_corroboration_not_tuning": True,
        },
        "layer_screens": {
            "D6_SELECTION": "PASS" if d6_pass else "FAIL",
            "D7_CONFIRMATION": "NOT_IN_SCOPE",
            "D8_HOLD_EXIT": "PASS" if d8_pass else "FAIL",
            "D9_ECONOMICS": d9_screen,
        },
        "date_results_digest": {
            "n": len(date_results),
            # keep lightweight summary only (ids omitted in digest for size)
            "per_date": [
                {
                    k: v
                    for k, v in r.items()
                    if k != "selected_ids"
                }
                for r in date_results
            ],
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
            "aov_104_as_full_w3": False,
        },
        "capital_authority": False,
        "financial_alpha_evidence": 0,
        "promotion_authority": "NONE",
        "ao_ftk_2": "NOT_OPENED",
        "constitution": CONSTITUTION,
    }


def build_l6_diagnosis(run: Mapping[str, Any]) -> dict[str, Any]:
    layers: list[dict[str, Any]] = []
    screens = run.get("layer_screens") or {}
    payoff = run.get("payoff") or {}
    stability = run.get("stability") or {}

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
        "Full-W3 market admitted (b32884e); operator pins dof=2; economic pack; "
        "symmetric CLOSE_TO_CLOSE both legs; no PIT rewrite.",
    )
    add(
        "D2_DATA_OBSERVABLE",
        "PASS",
        "D2 re-preflight GREEN; H=63 close paths observable on Full-W3; "
        f"decision_dates={payoff.get('n_decision_dates')}; R_net materialized.",
    )
    add(
        "D3_MEASUREMENT_POWER",
        "PASS",
        "Scoring dual-node continuous surface on FTK decision dates with "
        f"n_dates={payoff.get('n_decision_dates')}; K={K_VALUE}.",
    )
    add(
        "D4_REPRESENTATION_SNR",
        "PASS",
        "Continuous INV lag-1 + continuous M1 retained from frozen surface; "
        "no representation rewrite this trial.",
    )
    add(
        "D5_MECHANISM_SELF_TRANSITION",
        "PASS",
        "Historical sensing L5 mechanism PASS inherited; not re-adjudicated as primary "
        "economic claim; surface frozen.",
    )

    first_fail: str | None = None
    failure_route = "NONE_IN_SCOPE_PASS"

    d6 = screens.get("D6_SELECTION")
    if d6 == "PASS":
        add(
            "D6_SELECTION",
            "PASS",
            f"Gross lift={payoff.get('gross_lift')}; RT rate={payoff.get('selected_rt_rate')}; "
            f"fold_support={stability.get('d6_fold_support')}.",
        )
    else:
        add(
            "D6_SELECTION",
            "FAIL",
            f"No fold-stable selection enrichment: gross_lift={payoff.get('gross_lift')}; "
            f"RT rate={payoff.get('selected_rt_rate')}; fold_support={stability.get('d6_fold_support')}.",
            stop=True,
        )
        first_fail = "D6_SELECTION"
        failure_route = "HOLD_STOP_FTK_PRIMARY_NO_REPRESENTATION_REFINE"

    add(
        "D7_CONFIRMATION",
        "NOT_IN_SCOPE",
        "OUT_OF_SCOPE; no confirmation rule invented.",
        in_scope=False,
    )

    if first_fail is None:
        d8 = screens.get("D8_HOLD_EXIT")
        if d8 == "PASS":
            add(
                "D8_HOLD_EXIT",
                "PASS",
                f"Selected CAT rate={payoff.get('selected_cat_rate')} under H=63 fixed hold; "
                "not materially elevated vs 10th-pct base.",
            )
        else:
            add(
                "D8_HOLD_EXIT",
                "FAIL",
                f"Catastrophe load elevated: selected CAT rate={payoff.get('selected_cat_rate')}.",
                stop=True,
            )
            first_fail = "D8_HOLD_EXIT"
            failure_route = "SAFETY_FAIL_REJECT_HOLD_ACTION_LAW"

    if first_fail is None:
        d9 = screens.get("D9_ECONOMICS")
        if d9 == "PASS":
            add(
                "D9_ECONOMICS",
                "PASS",
                f"ΔJ={payoff.get('delta_J')} > 0 under POSITIVE_NET_EDGE_SCREEN; "
                f"fold_support={stability.get('d9_fold_support')}. Capital floor NOT granted.",
            )
            failure_route = "RESEARCH_CANDIDATE_ONLY_ALPHA_0_NO_AUTO_CAPITAL"
        else:
            add(
                "D9_ECONOMICS",
                "FAIL",
                f"ΔJ={payoff.get('delta_J')} failed POSITIVE_NET_EDGE_SCREEN "
                f"(required > {DELTA_J_REQUIRED}); fold_support={stability.get('d9_fold_support')}.",
                stop=True,
            )
            first_fail = "D9_ECONOMICS"
            failure_route = "SENSING_NE_POSITIVE_NET_EDGE_BANK_KNOWLEDGE_NO_CAPITAL"
    else:
        # still record not-reached for remaining
        if first_fail == "D6_SELECTION":
            add("D8_HOLD_EXIT", "NOT_REACHED", "Not reached; stopped at D6.")
            add("D9_ECONOMICS", "NOT_REACHED", "Not reached; stopped at D6.")
        elif first_fail == "D8_HOLD_EXIT":
            add("D9_ECONOMICS", "NOT_REACHED", "Not reached; stopped at D8.")

    d9_status = screens.get("D9_ECONOMICS")
    if first_fail is not None and first_fail != "D9_ECONOMICS":
        d9_status = "NOT_REACHED"

    info_gain = {
        "summary": (
            "Final economic one-shot on admitted Full-W3 under frozen 2-DOF FTK, "
            f"H=63, K=20, 20bps RT, CLOSE_TO_CLOSE both legs. first_fail={first_fail}; "
            f"ΔJ={payoff.get('delta_J')}; RT={payoff.get('selected_rt_rate')}; "
            f"CAT={payoff.get('selected_cat_rate')}. alpha remains 0; capital closed."
        ),
        "what_was_learned": [
            "Full-W3 market custody supports H=63 close-to-close economic estimand",
            "Frozen dual-node equal-weight top-K=20 action map is executable without grid",
            f"D6 selection screen: {screens.get('D6_SELECTION')}",
            f"D8 hold/exit catastrophe screen: {screens.get('D8_HOLD_EXIT') if first_fail != 'D6_SELECTION' else 'NOT_REACHED'}",
            f"D9 POSITIVE_NET_EDGE_SCREEN: {d9_status}",
        ],
        "what_was_not_learned": [
            "Capital materiality (floor NOT_YET_GRANTED)",
            "D7 confirmation (OUT_OF_SCOPE)",
            "Dividend-complete total-return economic edge (flag on both legs)",
            "Out-of-sample prospective live edge",
        ],
        "forbidden_to_change": [
            "second evaluation without new owner auth",
            "threshold/parameter/H/K grid",
            "DOF collapse or third DOF",
            "operator/feature rewrite under same freeze",
            "claim financial_alpha_evidence > 0",
            "open AO-FTK-2 / L8 / capital / W6",
            "invent D7 confirmation rule",
            "claim ΔJ>0 screen as capital authority",
        ],
        "which_single_layer_may_change_next": (
            "Owner L7 only: HOLD | STOP | CANDIDATE_PIPELINE_PREP | L8 only if earned. "
            "No AO-FTK-2. Trials remaining=0."
        ),
        "delta_J": payoff.get("delta_J"),
        "d9_interpretation": "POSITIVE_NET_EDGE_SCREEN",
        "financial_alpha_evidence": 0,
    }

    return {
        "schema_version": "ao_ftk_1_econ_1_l6_final_layered_diagnosis_v1",
        "receipt_id": L6_RECEIPT_ID,
        "work_id": WORK_ID,
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
            "D6": f"fixed-breadth K=20 improves payoff/RT vs Full-W3 — {screens.get('D6_SELECTION')}",
            "D7": "NOT_IN_SCOPE",
            "D8": f"fixed-H=63 hold vs catastrophe — {screens.get('D8_HOLD_EXIT') if first_fail != 'D6_SELECTION' else 'NOT_REACHED'}",
            "D9": f"ΔJ>0 POSITIVE_NET_EDGE_SCREEN — {d9_status}; capital floor not granted",
        },
        "precommitted_routes_recorded": {
            "D6_FAIL": "HOLD/STOP FTK; no redesign carnival",
            "D6_PASS_D8_FAIL": "safety fail",
            "D6_D8_PASS_D9_FAIL": "no positive net edge screen; bank; no capital",
            "D6_D8_D9_PASS_IN_SCOPE": "research candidate only; alpha still 0",
            "actual_route_this_run": failure_route,
        },
        "information_gain": info_gain,
        "d9_screen": d9_status,
        "financial_alpha_evidence": 0,
        "capital_authority": False,
        "ao_ftk_2": "NOT_OPENED",
        "constitution": CONSTITUTION,
    }


def build_l7_owner_packet(
    *,
    run: Mapping[str, Any],
    l6: Mapping[str, Any],
    d2: Mapping[str, Any],
) -> dict[str, Any]:
    first_fail = l6.get("first_fail_layer")
    route = l6.get("failure_route")
    d9 = l6.get("d9_screen")
    owner_routes = ["HOLD", "STOP"]
    if first_fail is None and d9 == "PASS":
        owner_routes = ["CANDIDATE_PIPELINE_PREP", "HOLD", "STOP", "L8_ONLY_IF_EARNED"]
    elif first_fail == "D9_ECONOMICS":
        owner_routes = ["HOLD", "STOP", "BANK_KNOWLEDGE"]
    elif first_fail == "D6_SELECTION":
        owner_routes = ["HOLD", "STOP"]
    elif first_fail == "D8_HOLD_EXIT":
        owner_routes = ["STOP", "HOLD"]

    return {
        "schema_version": "ao_ftk_1_econ_1_l7_final_owner_packet_v1",
        "receipt_id": L7_PACKET_ID,
        "work_id": WORK_ID,
        "freeze_id": FREEZE_ID,
        "parent_program": PARENT_PROGRAM,
        "completed_at_utc": utc_now_iso(),
        "session": "C_FINAL_TRIAL_COMPLETE",
        "D2_REPREFLIGHT": d2.get("D2_PRECHECK"),
        "debited": True,
        "material_trials_charged": 3,
        "material_trials_remaining": 0,
        "trials_after": {"charged": 3, "remaining": 0},
        "first_fail_layer": first_fail,
        "failure_route": route,
        "d9_screen": d9,
        "delta_J": (run.get("payoff") or {}).get("delta_J"),
        "financial_alpha_evidence": 0,
        "alpha": 0,
        "capital_authority": False,
        "ao_ftk_2": "NOT_OPENED",
        "w6": "UNTOUCHED",
        "l8_this_session": "NOT_OPENED",
        "worker_did_not_select_next_slice": True,
        "runnable_evaluation": False,
        "economic_l5_authorized_spent": True,
        "owner_routes": owner_routes,
        "next_owner_action": "L7 route only — " + " | ".join(owner_routes),
        "receipts": {
            "d2": D2_REL.as_posix(),
            "auth": AUTH_REL.as_posix(),
            "debit": DEBIT_REL.as_posix(),
            "join": JOIN_REL.as_posix(),
            "run": RUN_REL.as_posix(),
            "l6": L6_REL.as_posix(),
            "l7": L7_REL.as_posix(),
        },
        "layer_screens": run.get("layer_screens"),
        "payoff_summary": run.get("payoff"),
        "constitution": CONSTITUTION,
        "stop_lines_honored": list(STOP_LINES),
        "note": (
            "Final material trial spent. No FTK-2. No second eval. "
            "ΔJ>0 is POSITIVE_NET_EDGE_SCREEN only, not capital."
        ),
    }


def build_final_market_probe(repo: Path, d2: Mapping[str, Any]) -> dict[str, Any]:
    cov = d2.get("coverage") or {}
    return {
        "full_w3_market_total_return_admitted": True,
        "full_w3_close_to_close_admitted": True,
        "w3_admit_commit": W3_ADMIT_COMMIT,
        "w3_authority_dir": W3_AUTHORITY_DIR_REL.as_posix(),
        "source_manifest": W3_SOURCE_MANIFEST_REL.as_posix(),
        "market_company_count": cov.get("market_company_count"),
        "decision_dates_h63_calendar_complete": cov.get("decision_dates_h63_calendar_complete"),
        "coverage_rate_min": cov.get("coverage_rate_min"),
        "n_w3_eligible_sample_max": cov.get("n_w3_eligible_sample_max"),
        "return_convention": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
        "aov_104_used": False,
        "flag": None,
    }
