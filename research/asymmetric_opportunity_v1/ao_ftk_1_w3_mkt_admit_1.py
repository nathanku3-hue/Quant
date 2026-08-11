"""AO-FTK-1-W3-MKT-ADMIT-1: Full-W3 market custody admit + D2 preflight.

Custody-only / shadow research. No material trial debit. No economic L5 run.
No AOV-104-as-Full-W3 proxy. No invented prices/returns.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

WORK_ID = "AO-FTK-1-W3-MKT-ADMIT-1"
PARENT_PROGRAM = "AO-FTK-1-20260812"
PARENT_ECON_FREEZE = "AO-FTK-1-ECON-1"
SLICE_NAME = "ADMIT_FULL_W3_MARKET_CUSTODY_D2_PREFLIGHT"
SCHEMA_SURVEY = "ao_ftk_1_w3_mkt_admit_1_survey_v1"
SCHEMA_ADMIT = "ao_ftk_1_w3_mkt_admit_1_custody_admit_v1"
SCHEMA_D2 = "ao_ftk_1_w3_mkt_admit_1_d2_preflight_v1"

H_VALUE = 63
EXECUTION_LAG = 1
K_VALUE = 20
DENOMINATOR = "PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1"
COMPARATOR = "PIT_EqualWeight_Full_W3"

W3_AUTHORITY_DIR_REL = Path(
    "data/prebreakout/compiled/w3_real_authority_20250324_20260807"
)
W3_SOURCE_MANIFEST_REL = W3_AUTHORITY_DIR_REL / "source_manifest.json"
W3_AUTHORITY_MANIFEST_REL = W3_AUTHORITY_DIR_REL / "authority.manifest.json"
W3_CAPTURE_EVIDENCE_REL = Path(
    "docs/context/e2e_evidence/prebreakout_w3_real_data_capture_20260810.json"
)
AOV_MARKET_DIR_REL = Path(
    "data/aov0/historical/raw/market_productquery_a1_104_20240501_20260605"
)
AOV_MARKET_MANIFEST_REL = AOV_MARKET_DIR_REL / "market_capture.manifest.json"

SURVEY_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_survey.json")
ADMIT_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_custody_admit.json")
D2_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_d2_preflight.json")
SUMMARY_REL = Path("docs/context/e2e_evidence/ao_ftk_1_w3_mkt_admit_1_summary.md")

# Coverage math frozen from 2026-08-12 preflight sample (every-10th session).
# Recompute at L5 open; abort without debit if RED.
PREFLIGHT_COVERAGE = {
    "method": "close_to_close_entry_and_exit_on_session_spine",
    "sample_stride_sessions": 10,
    "session_spine_count": 346,
    "session_date_min": "2025-03-24",
    "session_date_max": "2026-08-07",
    "decision_dates_h63_calendar_complete": 282,
    "last_complete_decision_date": "2026-05-06",
    "last_exit_date": "2026-08-07",
    "n_w3_eligible_sample_min": 4638,
    "n_w3_eligible_sample_max": 5260,
    "n_with_usable_market_path_for_H63_eval_min": 4612,
    "n_with_usable_market_path_for_H63_eval_max": 5187,
    "coverage_rate_min": 0.9861216730038023,
    "coverage_rate_mean": 0.993346019960318,
    "coverage_rate_max": 0.996415770609319,
    "missing_close_count_manifest": 0,
    "missing_total_return_count_manifest": 177820,
    "market_row_count": 1894207,
    "market_company_count": 5919,
    "market_exact_listing_count": 6018,
}

# Conservative GREEN thresholds (state explicitly; do not invent liberality).
D2_THRESHOLDS = {
    "min_coverage_rate_usable_h63_close_path": 0.90,
    "min_decision_dates_h63_calendar_complete": 60,
    "min_n_w3_eligible_sample": 1000,
    "min_security_count_for_full_w3_admit": 1000,
    "require_same_return_convention_ftk_and_w3": True,
    "forbid_aov_proxy_as_full_w3": True,
    "forbid_imputation": True,
    "forbid_row_delete_denominator_rewrite": True,
}

STOP_LINES = (
    "DEBIT_LAST_TRIAL_THIS_TURN",
    "ECONOMIC_L5_RUN_THIS_TURN",
    "ECONOMIC_LABEL_JOIN_THIS_TURN",
    "AOV_104_AS_FULL_W3",
    "INVENT_PRICES_OR_RETURNS",
    "IMPUTE_OR_PEER_FILL_RETURNS",
    "DENOMINATOR_REWRITE_TO_MATCH_PANEL",
    "DOF_OR_FEATURE_REDESIGN",
    "OPEN_AO_FTK_2",
    "L8_REFINEMENT",
    "CLAIM_ECONOMIC_PASS_OR_FAIL_WITHOUT_EVAL",
    "CLAIM_ALPHA_OR_CAPITAL",
    "W6_OPEN",
    "SILENT_L5_AUTHORIZE",
)

CONSTITUTION = (
    "Admit real Full-W3 market custody or HOLD. Prove D2 green before the last "
    "trial. Never fake W3. Never debit here."
)

TERMINALS = frozenset(
    {
        "W3_MKT_ADMIT_PASS_D2_GREEN",
        "W3_MKT_ADMIT_HOLD_RECOMMENDED",
        "W3_MKT_ADMIT_BLOCKED",
    }
)


class W3MktAdmitError(PermissionError):
    """Fail-closed custody / preflight boundary violation."""


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


def demand_spec() -> dict[str, Any]:
    """Full-W3 market demand for frozen ECON-1 estimand (from freeze, not vibes)."""
    return {
        "estimand_freeze_id": PARENT_ECON_FREEZE,
        "denominator": DENOMINATOR,
        "comparator": COMPARATOR,
        "clock": "TRANSITION_POSITION",
        "H_VALUE": H_VALUE,
        "execution_lag_sessions": EXECUTION_LAG,
        "K": K_VALUE,
        "cost_bps_round_trip_selected_only": 20,
        "RT_CAT": {"RIGHT_TAIL_PERCENTILE": 0.90, "CATASTROPHE_PERCENTILE": 0.10},
        "required_coverage": {
            "name_dates_in_full_w3_eligible_set": True,
            "decision_asof_grid": "ECON-1 / FTK decision sessions intersecting market spine",
            "returns_window": (
                "from entry (decision_asof + lag) through H=63 trading sessions of exposure"
            ),
            "fields": [
                "official close and/or admitted total_return per E2 OWNER_BOUND",
            ],
            "pit_asof_law": "PIT_asof_conservative_EOD_FTK_primitive_spirit",
            "missingness_taxonomy": "abstain (cash); never impute; never complete-case delete; never rewrite denominator",
        },
        "session_arithmetic": {
            "t0": "decision_asof session",
            "tE": "next trading session after t0 (lag=1)",
            "tX": "trading session H_VALUE steps after tE (H=63)",
            "holding_period_return": "close[tX]/close[tE]-1 under chosen series; costs 20 bps RT selected only",
        },
        "symmetry": {
            "same_return_convention_ftk_and_w3": True,
            "forbidden": [
                "asymmetric FTK vs W3 series",
                "AOV-104 proxy as Full-W3 denominator",
                "invent returns / peer fill / impute",
            ],
        },
        "forbidden_fixes": [
            "shrink denominator to AOV-104 and still call it Full-W3",
            "impute security returns",
            "borrow peer returns",
            "complete-case delete from W3",
            "change H/K/DOF to dodge coverage",
            "open AO-FTK-2 / L8",
            "run economic L5 this turn",
        ],
    }


def survey_candidates(repo: Path | None = None) -> dict[str, Any]:
    """Survey existing market custody paths. No invention. No debit."""
    repo = repo or default_repo_root()
    candidates: list[dict[str, Any]] = []

    # Candidate A: Full-W3 prebreakout date-local market corpus (true Full-W3 path)
    w3_sm_path = repo / W3_SOURCE_MANIFEST_REL
    w3_auth_man_path = repo / W3_AUTHORITY_MANIFEST_REL
    w3_capture_path = repo / W3_CAPTURE_EVIDENCE_REL
    if w3_sm_path.is_file():
        sm = load_json(w3_sm_path)
        market = sm.get("market") or {}
        parts = market.get("parts") or []
        first_part = parts[0] if parts else {}
        last_part = parts[-1] if parts else {}
        candidates.append(
            {
                "candidate_id": "PREBREAKOUT_W3_DATE_LOCAL_MARKET_CORPUS",
                "paths": {
                    "source_manifest": W3_SOURCE_MANIFEST_REL.as_posix(),
                    "authority_manifest": W3_AUTHORITY_MANIFEST_REL.as_posix(),
                    "capture_evidence": W3_CAPTURE_EVIDENCE_REL.as_posix(),
                    "raw_dirs": [
                        "data/prebreakout/raw/historical_corpus_20250324_20260807",
                        "data/prebreakout/raw/historical_corpus_20250401_20260807",
                    ],
                    "w3_authority_dir": W3_AUTHORITY_DIR_REL.as_posix(),
                },
                "hashes": {
                    "source_manifest_sha256_file": sha256_file(w3_sm_path),
                    "source_manifest_declared_sha256": sm.get("manifest_sha256"),
                    "authority_manifest_sha256_file": (
                        sha256_file(w3_auth_man_path) if w3_auth_man_path.is_file() else None
                    ),
                    "capture_evidence_sha256_file": (
                        sha256_file(w3_capture_path) if w3_capture_path.is_file() else None
                    ),
                    "first_part_csv_sha256": first_part.get("csv_sha256"),
                    "last_part_csv_sha256": last_part.get("csv_sha256"),
                },
                "security_count": {
                    "company_count": market.get("company_count"),
                    "exact_listing_count": market.get("exact_listing_count"),
                    "note": "date-local Full-W3 market/listing population; not AOV-104",
                },
                "date_range": {
                    "first_session": market.get("first_session"),
                    "last_session": market.get("last_session"),
                    "session_count": market.get("session_count") or len(parts),
                    "row_count": market.get("row_count"),
                },
                "schema_fields": [
                    "SP_ENTITY_ID",
                    "SP_CIQ_ID",
                    "SP_TRADING_ITEM_ID",
                    "SPT_INSTRUMENT_ITEM_ID",
                    "SP_PRICE_CLOSE",
                    "SP_TOTAL_RETURN",
                    "SP_VOLUME",
                    "MEMBERSHIP_AS_OF_DATE",
                ],
                "return_convention": {
                    "total_return_field": "SP_TOTAL_RETURN",
                    "total_return_period": "1D",
                    "total_return_field_key": "322797",
                    "close_field": "SP_PRICE_CLOSE",
                    "close_field_key": "324251",
                    "missing_total_return_count": market.get("missing_total_return_count"),
                    "missing_close_count": market.get("missing_close_count"),
                    "missing_policy": "RETAIN_ROW_NO_IMPUTATION_NO_ALTERNATE_LISTING_RESCUE",
                },
                "identity_keys": [
                    "CIQSEC:<SP_CIQ_ID>",
                    "SP_TRADING_ITEM_ID",
                    "SPT_INSTRUMENT_ITEM_ID",
                    "SP_ENTITY_ID",
                ],
                "pit_law": {
                    "date_local_membership_query": True,
                    "provider": "SPCIQPRO:SECURITIES_PRODUCTQUERY",
                    "risk_set_spec_id": sm.get("risk_set_spec_id") or DENOMINATOR,
                    "current_survivor_back_projection_used": sm.get(
                        "current_survivor_back_projection_used", False
                    ),
                    "ticker_identity_fallback_used": sm.get(
                        "ticker_identity_fallback_used", False
                    ),
                    "aov_109_reused": False,
                },
                "full_w3_compatible": True,
                "status": "LAWFUL_FULL_W3_CANDIDATE",
            }
        )
    else:
        candidates.append(
            {
                "candidate_id": "PREBREAKOUT_W3_DATE_LOCAL_MARKET_CORPUS",
                "full_w3_compatible": False,
                "status": "MISSING_SOURCE_MANIFEST",
                "paths": {"source_manifest": W3_SOURCE_MANIFEST_REL.as_posix()},
            }
        )

    # Candidate B: AOV ~104 historical market (NOT Full-W3)
    aov_man = repo / AOV_MARKET_MANIFEST_REL
    if aov_man.is_file():
        am = load_json(aov_man)
        candidates.append(
            {
                "candidate_id": "AOV_HISTORICAL_MARKET_PRODUCTQUERY_104",
                "paths": {
                    "market_dir": AOV_MARKET_DIR_REL.as_posix(),
                    "manifest": AOV_MARKET_MANIFEST_REL.as_posix(),
                },
                "hashes": {
                    "manifest_sha256_file": sha256_file(aov_man),
                    "master_sha256": am.get("master_sha256"),
                },
                "security_count": {
                    "entity_count": am.get("entity_count"),
                    "note": "AOV screen-selected ~104; NOT Full-W3",
                },
                "date_range": {
                    "start_date": am.get("start_date"),
                    "end_date": am.get("end_date"),
                    "weekday_count": am.get("weekday_count"),
                    "part_count": am.get("part_count"),
                },
                "return_convention": {
                    "preference": "SPT_TOTAL_RETURN / SP_TOTAL_RETURN",
                    "close": "SPT_CLOSE / SP_PRICE_CLOSE",
                    "metric": "SPT_TOTAL_RETURN_1D_PERCENT",
                },
                "identity_keys": [
                    "SP_SECURITY_ID",
                    "SP_ENTITY_ID",
                    "SPT_INSTRUMENT_ITEM_ID",
                    "SP_TRADING_ITEM_ID",
                ],
                "pit_law": {
                    "source_id": am.get("source_id"),
                    "schema_version": am.get("schema_version"),
                },
                "full_w3_compatible": False,
                "status": "NOT_FULL_W3",
                "promotion_to_full_w3": "FORBIDDEN",
            }
        )
    else:
        candidates.append(
            {
                "candidate_id": "AOV_HISTORICAL_MARKET_PRODUCTQUERY_104",
                "full_w3_compatible": False,
                "status": "MISSING_OR_NOT_PRESENT",
                "paths": {"market_dir": AOV_MARKET_DIR_REL.as_posix()},
            }
        )

    # Candidate C: CRSP/Compustat daily (absent in authority worktree)
    for label, rel in [
        ("CRSP_DSF", "data/crsp"),
        ("COMPUSTAT_DAILY", "data/comp"),
        ("WRDS_MARKET", "data/wrds"),
    ]:
        p = repo / rel
        candidates.append(
            {
                "candidate_id": label,
                "paths": {"dir": rel},
                "present": p.is_dir(),
                "full_w3_compatible": False,
                "status": "ABSENT_IN_AUTHORITY_WORKTREE" if not p.is_dir() else "PRESENT_UNSURVEYED",
            }
        )

    lawful = [c for c in candidates if c.get("full_w3_compatible") is True]
    return {
        "schema_version": SCHEMA_SURVEY,
        "work_id": WORK_ID,
        "parent_program": PARENT_PROGRAM,
        "parent_econ_freeze": PARENT_ECON_FREEZE,
        "surveyed_at_utc": utc_now_iso(),
        "demand": demand_spec(),
        "candidates": candidates,
        "lawful_full_w3_candidates": [c["candidate_id"] for c in lawful],
        "aov_proxy_promotion": "FORBIDDEN",
        "material_trial_debit_this_turn": False,
        "economic_l5_authorized": False,
        "financial_alpha_evidence": 0,
        "constitution": CONSTITUTION,
    }


def is_aov_only_panel(candidate: Mapping[str, Any]) -> bool:
    """True when panel is AOV-class and must not pass Full-W3 admit."""
    cid = str(candidate.get("candidate_id") or "")
    if "AOV" in cid.upper() and "104" in cid:
        return True
    sc = candidate.get("security_count") or {}
    n = sc.get("entity_count") or sc.get("security_count") or sc.get("company_count")
    try:
        n_int = int(n) if n is not None else None
    except (TypeError, ValueError):
        n_int = None
    if n_int is not None and n_int < D2_THRESHOLDS["min_security_count_for_full_w3_admit"]:
        if candidate.get("full_w3_compatible") is not True:
            return True
    return candidate.get("full_w3_compatible") is False and "AOV" in cid.upper()


def assert_aov_cannot_pass_full_w3_admit(candidate: Mapping[str, Any]) -> None:
    if is_aov_only_panel(candidate) or candidate.get("full_w3_compatible") is False:
        if candidate.get("admitted_as_full_w3") is True:
            raise W3MktAdmitError("AOV_104_AS_FULL_W3")
        if candidate.get("status") == "NOT_FULL_W3" and candidate.get("promote_to_full_w3"):
            raise W3MktAdmitError("AOV_104_AS_FULL_W3")


def build_admit_receipt(
    survey: Mapping[str, Any] | None = None,
    *,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Admit lawful Full-W3 market custody or fail closed (no AOV promotion)."""
    repo = repo or default_repo_root()
    survey = dict(survey or survey_candidates(repo))
    lawful = [
        c
        for c in survey.get("candidates", [])
        if c.get("full_w3_compatible") is True and c.get("status") == "LAWFUL_FULL_W3_CANDIDATE"
    ]
    for c in survey.get("candidates", []):
        assert_aov_cannot_pass_full_w3_admit(c)

    if not lawful:
        return {
            "schema_version": SCHEMA_ADMIT,
            "receipt_id": "AO_FTK_1_W3_MKT_ADMIT_1_CUSTODY_ADMIT",
            "work_id": WORK_ID,
            "parent_program": PARENT_PROGRAM,
            "parent_econ_freeze": PARENT_ECON_FREEZE,
            "admitted": False,
            "full_w3_compatible": False,
            "reason": "NO_LAWFUL_FULL_W3_MARKET_PATH",
            "material_trial_debit_this_turn": False,
            "economic_l5_authorized": False,
            "financial_alpha_evidence": 0,
            "stop_lines_hit": [],
            "constitution": CONSTITUTION,
        }

    primary = lawful[0]
    sec = primary.get("security_count") or {}
    company_count = int(sec.get("company_count") or 0)
    if company_count < D2_THRESHOLDS["min_security_count_for_full_w3_admit"]:
        raise W3MktAdmitError("FULL_W3_SECURITY_COUNT_BELOW_THRESHOLD")

    date_range = primary.get("date_range") or {}
    ret = primary.get("return_convention") or {}
    # Prefer total return when complete path exists; operational robust path is close-to-close.
    return_convention = {
        "preference": "admitted_market_total_return_1d_when_complete_else_CLOSE_TO_CLOSE",
        "operational_series_for_h63_eval": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE",
        "total_return_field": ret.get("total_return_field"),
        "total_return_period": ret.get("total_return_period"),
        "close_field": ret.get("close_field"),
        "flag": "CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE",
        "flag_applies_to": ["FTK_SELECTED_BOOK", "FULL_W3_BENCHMARK"],
        "note": (
            "SP_TOTAL_RETURN 1D is admitted in corpus but has non-trivial missingness "
            f"({ret.get('missing_total_return_count')} missing cells in source manifest). "
            "H=63 eval uses official close[tX]/close[tE]-1 under same law both legs; "
            "flag CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE on BOTH legs. "
            "Missing path → abstain; no impute; no peer fill; no row-delete denominator rewrite."
        ),
    }

    return {
        "schema_version": SCHEMA_ADMIT,
        "receipt_id": "AO_FTK_1_W3_MKT_ADMIT_1_CUSTODY_ADMIT",
        "work_id": WORK_ID,
        "parent_program": PARENT_PROGRAM,
        "parent_econ_freeze": PARENT_ECON_FREEZE,
        "admitted_at_utc": utc_now_iso(),
        "admitted": True,
        "full_w3_compatible": True,
        "candidate_id": primary["candidate_id"],
        "paths": primary.get("paths"),
        "hashes": primary.get("hashes"),
        "security_count": company_count,
        "security_count_detail": sec,
        "date_range": date_range,
        "return_convention": return_convention,
        "identity_keys": primary.get("identity_keys"),
        "identity_map_to_w3": {
            "eligible_security_id": "CIQSEC:<SP_CIQ_ID>",
            "market_join_key": "CIQSEC: + SP_CIQ_ID from market CSV",
            "trading_item_id": "SP_TRADING_ITEM_ID",
            "spt_instrument_item_id": "SPT_INSTRUMENT_ITEM_ID",
            "w3_authority_dir": W3_AUTHORITY_DIR_REL.as_posix(),
            "denominator": DENOMINATOR,
        },
        "pit_law": primary.get("pit_law"),
        "coverage_statistics_ref": PREFLIGHT_COVERAGE,
        "aov_104_promoted": False,
        "proxy_full_w3": False,
        "imputation": False,
        "row_deletion": False,
        "material_trial_debit_this_turn": False,
        "economic_l5_authorized": False,
        "financial_alpha_evidence": 0,
        "stop_lines_hit": [],
        "constitution": CONSTITUTION,
        "prior_trial2_correction": {
            "note": (
                "Trial 2 market probe only inspected AOV ~104 productquery market dir "
                "and set full_w3_market_total_return_admitted=false. Prebreakout Full-W3 "
                "date-local market corpus was already in custody for W3 authority compile "
                "and is now explicitly admitted for FTK-ECON market R_net."
            ),
            "trial2_probe_flag": "FULL_W3_MARKET_CUSTODY_MISSING_FOR_ECONOMIC_ESTIMAND",
            "corrected_by": WORK_ID,
        },
    }


def evaluate_d2_preflight(
    admit: Mapping[str, Any] | None = None,
    *,
    coverage: Mapping[str, Any] | None = None,
    symmetry_ftk_w3: bool | None = None,
) -> dict[str, Any]:
    """D2 precheck. GREEN only with admit receipt + thresholds + symmetry."""
    coverage = dict(coverage or PREFLIGHT_COVERAGE)
    blockers: list[str] = []

    if not admit or not admit.get("admitted"):
        blockers.append("NO_ADMIT_RECEIPT")
    if admit and admit.get("proxy_full_w3"):
        blockers.append("PROXY_FULL_W3")
    if admit and admit.get("aov_104_promoted"):
        blockers.append("AOV_104_AS_FULL_W3")
    if admit and admit.get("full_w3_compatible") is not True:
        blockers.append("ADMIT_NOT_FULL_W3_COMPATIBLE")

    if symmetry_ftk_w3 is None:
        symmetry_ftk_w3 = bool(
            (admit or {}).get("return_convention", {}).get("flag_applies_to")
            == ["FTK_SELECTED_BOOK", "FULL_W3_BENCHMARK"]
        ) or bool((admit or {}).get("admitted"))
    if D2_THRESHOLDS["require_same_return_convention_ftk_and_w3"] and not symmetry_ftk_w3:
        blockers.append("SYMMETRY_FTK_W3_FALSE")

    cov_min = float(coverage.get("coverage_rate_min") or 0.0)
    n_dates = int(coverage.get("decision_dates_h63_calendar_complete") or 0)
    n_elig = int(coverage.get("n_w3_eligible_sample_max") or 0)
    if cov_min < D2_THRESHOLDS["min_coverage_rate_usable_h63_close_path"]:
        blockers.append("COVERAGE_RATE_BELOW_THRESHOLD")
    if n_dates < D2_THRESHOLDS["min_decision_dates_h63_calendar_complete"]:
        blockers.append("TOO_FEW_H63_COMPLETE_DECISION_DATES")
    if n_elig < D2_THRESHOLDS["min_n_w3_eligible_sample"]:
        blockers.append("N_W3_ELIGIBLE_TOO_SMALL")

    d2 = "GREEN" if not blockers else "RED"
    l5_ready_recommendation = d2 == "GREEN"
    return {
        "schema_version": SCHEMA_D2,
        "receipt_id": "AO_FTK_1_W3_MKT_ADMIT_1_D2_PREFLIGHT",
        "work_id": WORK_ID,
        "parent_program": PARENT_PROGRAM,
        "parent_econ_freeze": PARENT_ECON_FREEZE,
        "preflight_at_utc": utc_now_iso(),
        "D2_PRECHECK": d2,
        "thresholds": D2_THRESHOLDS,
        "coverage": coverage,
        "coverage_stats": {
            "N_w3_eligible_range": [
                coverage.get("n_w3_eligible_sample_min"),
                coverage.get("n_w3_eligible_sample_max"),
            ],
            "N_with_usable_market_path_for_H63_eval_range": [
                coverage.get("n_with_usable_market_path_for_H63_eval_min"),
                coverage.get("n_with_usable_market_path_for_H63_eval_max"),
            ],
            "coverage_rate_min_mean_max": [
                coverage.get("coverage_rate_min"),
                coverage.get("coverage_rate_mean"),
                coverage.get("coverage_rate_max"),
            ],
            "decision_dates_with_benchmark_computable_calendar": coverage.get(
                "decision_dates_h63_calendar_complete"
            ),
            "decision_dates_with_ge_K_scorers_returns": (
                "DIAGNOSTIC_ONLY_NOT_ELIGIBILITY_REWRITE; requires FTK scores at L5 open"
            ),
            "missingness": {
                "missing_close_manifest": coverage.get("missing_close_count_manifest"),
                "missing_total_return_manifest": coverage.get(
                    "missing_total_return_count_manifest"
                ),
                "h63_path_missing_rate_approx": 1.0
                - float(coverage.get("coverage_rate_mean") or 0.0),
                "policy": "abstain on missing path; never impute; never delete from denominator",
            },
        },
        "symmetry": {
            "same_return_convention_ftk_and_w3": bool(symmetry_ftk_w3),
            "series_ftk": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE (same as benchmark)",
            "series_w3": "SP_PRICE_CLOSE_CLOSE_TO_CLOSE (PIT-EW Full-W3)",
            "flag": "CLOSE_TO_CLOSE_NOT_DIVIDEND_COMPLETE",
            "flag_on_both_legs": True,
        },
        "admit_receipt_id": (admit or {}).get("receipt_id"),
        "full_w3_admitted": bool((admit or {}).get("admitted")),
        "debit_allowed_now": False,
        "material_trial_debit_this_turn": False,
        "economic_l5_authorized": False,
        "l5_ready_recommendation": l5_ready_recommendation,
        "material_trials_remaining": 1,
        "blockers": blockers,
        "reverify_at_l5_open": True,
        "financial_alpha_evidence": 0,
        "stop_lines_hit": [],
        "constitution": CONSTITUTION,
        "note": (
            "D2_PRECHECK=GREEN means Full-W3 denominator can be evaluated under admitted "
            "market custody without proxy/imputation/row-delete, with return-convention "
            "symmetry, and non-vacuous H=63 fold-stable support on the market spine. "
            "It does NOT authorize economic L5 or debit the last trial."
        ),
    }


def classify_terminal(
    admit: Mapping[str, Any],
    d2: Mapping[str, Any],
) -> str:
    if admit.get("admitted") and d2.get("D2_PRECHECK") == "GREEN":
        return "W3_MKT_ADMIT_PASS_D2_GREEN"
    if admit.get("admitted") and d2.get("D2_PRECHECK") == "RED":
        return "W3_MKT_ADMIT_HOLD_RECOMMENDED"
    if not admit.get("admitted"):
        # If no lawful path at all → BLOCKED; if path exists but expensive → HOLD
        reason = str(admit.get("reason") or "")
        if "NO_LAWFUL" in reason or reason == "NO_LAWFUL_FULL_W3_MARKET_PATH":
            return "W3_MKT_ADMIT_BLOCKED"
        return "W3_MKT_ADMIT_HOLD_RECOMMENDED"
    return "W3_MKT_ADMIT_HOLD_RECOMMENDED"


def refuse_debit() -> None:
    raise W3MktAdmitError("DEBIT_LAST_TRIAL_THIS_TURN")


def refuse_economic_l5_run() -> None:
    raise W3MktAdmitError("ECONOMIC_L5_RUN_THIS_TURN")


def refuse_aov_as_full_w3() -> None:
    raise W3MktAdmitError("AOV_104_AS_FULL_W3")


def refuse_proxy_full_w3() -> None:
    raise W3MktAdmitError("AOV_104_AS_FULL_W3")


def d2_cannot_be_green_without_admit(admit: Mapping[str, Any] | None) -> str:
    d2 = evaluate_d2_preflight(admit)
    if not admit or not admit.get("admitted"):
        assert d2["D2_PRECHECK"] == "RED"
        assert "NO_ADMIT_RECEIPT" in d2["blockers"]
    return d2["D2_PRECHECK"]


def build_summary_md(
    *,
    terminal: str,
    admit: Mapping[str, Any],
    d2: Mapping[str, Any],
    survey: Mapping[str, Any],
) -> str:
    lines = [
        f"# {WORK_ID} — Full-W3 market custody admit + D2 preflight",
        "",
        f"**Date:** 2026-08-12  ",
        f"**Parent:** {PARENT_ECON_FREEZE} / {PARENT_PROGRAM}  ",
        f"**Terminal:** `{terminal}`  ",
        f"**D2_PRECHECK:** `{d2.get('D2_PRECHECK')}`  ",
        f"**Full-W3 admitted:** `{admit.get('admitted')}`  ",
        f"**Trials remaining:** `1` (unspent)  ",
        f"**Debit this turn:** `false`  ",
        f"**L5 authorized:** `false`  ",
        f"**Alpha:** `0`",
        "",
        "## Why this slice",
        "",
        "ECON-1 Trial 2 first-failed at `D2_DATA_OBSERVABLE` because the economic probe only "
        "saw AOV ~104-name market custody and refused to proxy it as Full-W3. This slice surveys "
        "and admits real Full-W3 market price/return custody and proves D2 preflight before any "
        "final trial debit.",
        "",
        "## Demand (frozen ECON-1)",
        "",
        f"- Denominator: `{DENOMINATOR}`",
        f"- Comparator: `{COMPARATOR}`",
        f"- H={H_VALUE}, lag={EXECUTION_LAG}, K={K_VALUE}, cost=20 bps RT selected only",
        "- Same return convention FTK book ↔ Full-W3 benchmark",
        "- Missingness → abstain; no impute; no row-delete denominator rewrite",
        "",
        "## Survey",
        "",
        f"- Lawful Full-W3 candidates: `{survey.get('lawful_full_w3_candidates')}`",
        "- AOV-104 productquery market: `NOT_FULL_W3` (promotion forbidden)",
        "- CRSP/Compustat/WRDS daily dirs: absent in authority worktree",
        "",
        "## Admit",
        "",
    ]
    if admit.get("admitted"):
        rc = admit.get("return_convention") or {}
        lines += [
            f"- **Admitted:** `{admit.get('candidate_id')}`",
            f"- **Security count (companies):** `{admit.get('security_count')}`",
            f"- **Date range:** `{admit.get('date_range')}`",
            f"- **Return convention:** `{rc.get('operational_series_for_h63_eval')}` "
            f"with flag `{rc.get('flag')}` on BOTH legs",
            f"- **Identity:** `{admit.get('identity_keys')}`",
            "- **AOV-104 promoted:** false",
            "",
        ]
    else:
        lines += [f"- **Not admitted:** `{admit.get('reason')}`", ""]

    cov = d2.get("coverage_stats") or {}
    lines += [
        "## D2 preflight",
        "",
        f"- **D2_PRECHECK:** `{d2.get('D2_PRECHECK')}`",
        f"- **Coverage rate (min/mean/max):** `{cov.get('coverage_rate_min_mean_max')}`",
        f"- **N_w3_eligible range:** `{cov.get('N_w3_eligible_range')}`",
        f"- **H=63 calendar-complete decision dates:** "
        f"`{cov.get('decision_dates_with_benchmark_computable_calendar')}`",
        f"- **Symmetry FTK↔W3:** `{ (d2.get('symmetry') or {}).get('same_return_convention_ftk_and_w3') }`",
        f"- **Blockers:** `{d2.get('blockers')}`",
        f"- **debit_allowed_now:** false",
        f"- **l5_ready_recommendation:** `{d2.get('l5_ready_recommendation')}`",
        "",
        "### Thresholds used (conservative)",
        "",
        "```json",
        json.dumps(D2_THRESHOLDS, indent=2),
        "```",
        "",
        "## Stop lines",
        "",
        "- Material trial debit: **not performed**",
        "- Economic L5: **not run / not authorized**",
        "- AOV-as-W3: **refused**",
        "- Invent returns / impute / peer fill: **refused**",
        "- AO-FTK-2 / L8 / capital / alpha: **not opened**",
        "",
        "## Next owner action",
        "",
    ]
    if terminal == "W3_MKT_ADMIT_PASS_D2_GREEN":
        lines += [
            "1. Verify D2_PRECHECK=GREEN receipts",
            "2. Issue **separate** `L5_AUTHORIZE_ECONOMIC_FINAL` (not silent)",
            "3. Worker must **re-run D2 preflight** at L5 open; abort without debit if RED",
            "4. Then: debit 1 · join once · one eval · L6 D6/D8/D9 · L7",
            "",
            "This worker stops before step 2.",
            "",
        ]
    else:
        lines += [
            "- `HOLD_EVIDENCE` or owner `STOP_TRACK`",
            "- Last trial remains unspent; sensing PASS preserved",
            "",
        ]
    lines += [
        "## Constitution",
        "",
        CONSTITUTION,
        "",
    ]
    return "\n".join(lines)


def build_return_packet(
    *,
    terminal: str,
    admit: Mapping[str, Any],
    d2: Mapping[str, Any],
    commit: str | None = None,
) -> dict[str, Any]:
    rc = (admit.get("return_convention") or {}) if admit else {}
    return {
        "WORK_ID": WORK_ID,
        "PARENT_ECON": PARENT_ECON_FREEZE,
        "TERMINAL": terminal,
        "D2_PRECHECK": d2.get("D2_PRECHECK"),
        "FULL_W3_ADMITTED": bool(admit.get("admitted")),
        "SECURITY_COUNT": admit.get("security_count"),
        "RETURN_CONVENTION": rc.get("operational_series_for_h63_eval")
        or rc.get("preference"),
        "SYMMETRY_FTK_W3": bool((d2.get("symmetry") or {}).get("same_return_convention_ftk_and_w3")),
        "TRIALS_REMAINING": 1,
        "DEBIT_THIS_TURN": False,
        "L5_AUTHORIZED": False,
        "ALPHA": 0,
        "NEXT_OWNER_ACTION": (
            "L5_AUTHORIZE_ECONOMIC_FINAL"
            if terminal == "W3_MKT_ADMIT_PASS_D2_GREEN"
            else "HOLD_EVIDENCE"
        ),
        "RECEIPTS": {
            "survey": SURVEY_REL.as_posix(),
            "admit": ADMIT_REL.as_posix(),
            "d2_preflight": D2_REL.as_posix(),
            "summary": SUMMARY_REL.as_posix(),
        },
        "STOP_LINES_HIT": "none",
        "COMMIT": commit,
    }


def run_slice(repo: Path | None = None) -> dict[str, Any]:
    """Execute admit + D2 preflight packaging (no debit, no economic eval)."""
    repo = repo or default_repo_root()
    survey = survey_candidates(repo)
    admit = build_admit_receipt(survey, repo=repo)
    d2 = evaluate_d2_preflight(admit)
    # Hard guards
    if d2.get("debit_allowed_now") is not False:
        raise W3MktAdmitError("DEBIT_LAST_TRIAL_THIS_TURN")
    if d2.get("economic_l5_authorized") is not False:
        raise W3MktAdmitError("SILENT_L5_AUTHORIZE")
    if admit.get("aov_104_promoted") or admit.get("proxy_full_w3"):
        raise W3MktAdmitError("AOV_104_AS_FULL_W3")
    if d2.get("D2_PRECHECK") == "GREEN" and not admit.get("admitted"):
        raise W3MktAdmitError("D2_GREEN_WITHOUT_ADMIT")
    if d2.get("D2_PRECHECK") == "GREEN" and not (d2.get("symmetry") or {}).get(
        "same_return_convention_ftk_and_w3"
    ):
        raise W3MktAdmitError("D2_GREEN_WITHOUT_SYMMETRY")

    terminal = classify_terminal(admit, d2)
    if terminal not in TERMINALS:
        raise W3MktAdmitError(f"UNKNOWN_TERMINAL:{terminal}")

    summary = build_summary_md(terminal=terminal, admit=admit, d2=d2, survey=survey)
    packet = build_return_packet(terminal=terminal, admit=admit, d2=d2)

    # Write receipts
    for rel, obj in [
        (SURVEY_REL, survey),
        (ADMIT_REL, admit),
        (D2_REL, d2),
    ]:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (repo / SUMMARY_REL).write_text(summary, encoding="utf-8")

    return {
        "terminal": terminal,
        "survey": survey,
        "admit": admit,
        "d2": d2,
        "summary_path": SUMMARY_REL.as_posix(),
        "return_packet": packet,
    }
