"""M5a PEAD net multi-factor diagnostic runner.

Evidence-only backend runner. It compares the existing PEAD Q5-Q1 calendar-time
spread under MKT-only and Fama/French 3-factor adjustment, with an explicit
constant spread-cost diagnostic. It intentionally remains diagnostic-only while
EPS vintage, return source, and delisting adjustments are not alpha-grade.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.pead_m5a_multifactor_factors import OUTPUT_COLUMNS as D3M_COLUMNS
from scripts.pead_real_data_validation import (
    D1_MANIFEST_PATH,
    D2B_MANIFEST_PATH,
    D2B_READ_COLUMNS,
    D3_MANIFEST_PATH,
    D3_READ_COLUMNS,
    ROOT,
    _display_path,
    _json_value,
    _load_artifact,
    _m1b_lineage_record,
    _sha256_bytes,
    _sha256_file,
    _validate_d2b_contract,
    _validate_d2b_dates_on_d3_spine,
    _validate_d3_contract,
    _validate_lineage,
    _validate_m1b_current_counts,
)
from strategies.pead_event_study import (
    PeadCalendarTimeInferenceConfig,
    PeadEventStudyConfig,
    assign_signal_quantiles,
    build_calendar_time_inference,
)

D3M_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d3m_ken_french_daily_multifactor.parquet.manifest.json"
OUTPUT_PATH = ROOT / "docs" / "context" / "e2e_evidence" / "pead_m5a_net_multifactor_alpha_test.json"

ROUND_ID = "ROUND-20260624-V2-PEAD-M5A-NET-MULTIFACTOR-DIAGNOSTIC"
SCOPE_ID = "V2_PEAD_M5A_NET_MULTIFACTOR_DIAGNOSTIC_ONLY"
METHOD_ID = "calendar_time_q5_q1_ff3_net_cost_diagnostic_v1"

FORBIDDEN_USE = sorted(
    [
        "alpha_claims",
        "alerts",
        "broker_or_order_paths",
        "causal_claims",
        "full_factor_alpha_claims",
        "net_performance_claims",
        "population_validity_claims",
        "ranking_or_scoring",
        "recommendations",
        "strategy_promotion",
        "strict_point_in_time_claims",
        "tradability_claims",
    ]
)


class MultifactorArtifact(tuple):
    __slots__ = ()

    @property
    def frame(self) -> pd.DataFrame:
        return self[0]

    @property
    def manifest(self) -> dict[str, Any]:
        return self[1]

    @property
    def manifest_path(self) -> Path:
        return self[2]

    @property
    def manifest_sha256(self) -> str:
        return self[3]

    @property
    def parquet_path(self) -> Path:
        return self[4]

    @property
    def parquet_sha256(self) -> str:
        return self[5]


def _require_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _load_multifactor_artifact(manifest_path: Path = D3M_MANIFEST_PATH) -> MultifactorArtifact:
    manifest_path = Path(manifest_path).resolve()
    payload = manifest_path.read_bytes()
    manifest_sha256 = _sha256_bytes(payload)
    manifest = json.loads(payload.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("D3M manifest must be a JSON object")
    if manifest.get("artifact_name") != "pead_d3m_ken_french_daily_multifactor":
        raise ValueError("D3M manifest artifact_name drift")
    if manifest.get("allowed_use") != "diagnostic_pead_m5a_multifactor_input_only":
        raise ValueError("D3M allowed_use drift")
    if manifest.get("locked_d3_policy", {}).get("does_not_rewrite_d3") is not True:
        raise ValueError("D3M manifest must assert it does not rewrite locked D3")
    parquet_file = manifest.get("parquet_file")
    if not isinstance(parquet_file, str) or Path(parquet_file).name != parquet_file:
        raise ValueError("D3M parquet_file must be a local filename")
    parquet_path = (manifest_path.parent / parquet_file).resolve()
    parquet_sha256 = _sha256_file(parquet_path)
    if parquet_sha256 != manifest.get("sha256"):
        raise ValueError("D3M Parquet hash drift against manifest")
    frame = pd.read_parquet(parquet_path, columns=["return_date", "mktrf", "smb", "hml", "rf"])
    _validate_multifactor_frame(frame, manifest)
    return MultifactorArtifact((frame, manifest, manifest_path, manifest_sha256, parquet_path, parquet_sha256))


def _validate_multifactor_frame(frame: pd.DataFrame, manifest: dict[str, Any]) -> None:
    expected_columns = ["return_date", "mktrf", "smb", "hml", "rf"]
    if list(frame.columns) != expected_columns:
        raise ValueError(f"D3M read schema drift: {list(frame.columns)}")
    if list(manifest.get("columns", [])) != D3M_COLUMNS:
        raise ValueError("D3M manifest columns drift")
    frame["return_date"] = pd.to_datetime(frame["return_date"], errors="coerce").dt.normalize()
    if frame["return_date"].isna().any() or frame["return_date"].duplicated().any():
        raise ValueError("D3M return_date must be non-null and unique")
    if not frame["return_date"].is_monotonic_increasing:
        raise ValueError("D3M return_date must be sorted")
    for column in ("mktrf", "smb", "hml", "rf"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if not np.isfinite(frame[column]).all():
            raise ValueError(f"D3M {column} must be finite")
        if frame[column].lt(-1.0).any() or frame[column].abs().gt(1.0).any():
            raise ValueError(f"D3M {column} must be decimal return units")
    if int(manifest.get("row_count")) != int(len(frame)):
        raise ValueError("D3M manifest row_count drift")


def _lineage_record_from_d3m(d3m: MultifactorArtifact) -> dict[str, Any]:
    return {
        "manifest_path": _display_path(d3m.manifest_path),
        "manifest_sha256": d3m.manifest_sha256,
        "parquet_path": _display_path(d3m.parquet_path),
        "parquet_sha256": d3m.parquet_sha256,
        "rows": int(len(d3m.frame)),
    }


def _prepare_daily_portfolio(
    *,
    d1_manifest_path: Path,
    d2b_manifest_path: Path,
    d3_manifest_path: Path,
    d3m_manifest_path: Path,
    enforce_current_counts: bool,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    cfg = PeadCalendarTimeInferenceConfig()
    d1 = _load_artifact(d1_manifest_path, "D1", contract_location="root")
    d2b = _load_artifact(
        d2b_manifest_path,
        "D2B",
        contract_location="output",
        read_columns=D2B_READ_COLUMNS,
    )
    d3 = _load_artifact(
        d3_manifest_path,
        "D3",
        contract_location="root",
        read_columns=D3_READ_COLUMNS,
    )
    d3m = _load_multifactor_artifact(d3m_manifest_path)
    assert d2b.frame is not None and d3.frame is not None

    _validate_lineage(d1, d2b, d3)
    _validate_d2b_contract(d2b.frame, d2b.manifest)
    _validate_d3_contract(d3.frame, d2b.manifest, d3.manifest)
    _validate_d2b_dates_on_d3_spine(d2b.frame, d3.frame)
    _validate_d3m_against_d2b_and_d3(d3m.frame, d2b.manifest, d3.frame)

    event_first_rows = d2b.frame.loc[d2b.frame["event_day"] == 1].copy()
    event_first_rows["calendar_time_signal_placeholder"] = 0.0
    assignments = assign_signal_quantiles(
        event_first_rows,
        "calendar_time_signal_placeholder",
        PeadEventStudyConfig(start_day=cfg.start_day, end_day=cfg.end_day, quantiles=cfg.quantiles),
    )
    extreme_events = assignments.loc[
        assignments["signal_bucket_eligible"]
        & assignments["signal_quantile"].isin({int(cfg.low_quantile), int(cfg.high_quantile)}),
        "event_id",
    ].unique()
    keep_cols = [
        "event_id",
        "security_id",
        "event_date",
        "event_day",
        "return_date",
        "sue",
        "asset_return",
        "window_complete",
    ]
    filtered_d2b = d2b.frame.loc[
        d2b.frame["event_id"].isin(extreme_events) | d2b.frame["event_day"].eq(1),
        keep_cols,
    ].copy()

    result = build_calendar_time_inference(filtered_d2b, d3.frame, cfg)
    if enforce_current_counts:
        _validate_m1b_current_counts(result.session_coverage)

    daily = result.daily_portfolio.copy()
    daily["return_date"] = pd.to_datetime(daily["return_date"], errors="raise").dt.normalize()
    factors = d3m.frame[["return_date", "mktrf", "smb", "hml", "rf"]].copy()
    factors["return_date"] = pd.to_datetime(factors["return_date"], errors="raise").dt.normalize()
    merged = daily.merge(
        factors,
        on="return_date",
        how="left",
        suffixes=("_d3", ""),
        validate="one_to_one",
    )
    if merged[["mktrf", "smb", "hml", "rf"]].isna().any().any():
        raise ValueError("D3M factors do not cover retained daily portfolio dates")
    if not np.allclose(merged["mktrf_d3"], merged["mktrf"], rtol=0.0, atol=1e-15):
        raise ValueError("D3M mktrf does not match locked D3 mktrf on retained dates")
    merged = merged.drop(columns=["mktrf_d3"])

    lineage = {
        "d1": _m1b_lineage_record(d1),
        "d2b": _m1b_lineage_record(d2b),
        "d3_locked": _m1b_lineage_record(d3),
        "d3m_multifactor": _lineage_record_from_d3m(d3m),
    }
    diagnostics = {
        "session_coverage": result.session_coverage,
        "daily_summary": result.daily_summary,
        "source_m1b_primary_inference": result.primary_inference,
    }
    return merged, lineage, diagnostics


def _validate_d3m_against_d2b_and_d3(d3m: pd.DataFrame, d2b_manifest: dict[str, Any], d3: pd.DataFrame) -> None:
    d3m_spine = _session_spine_record(d3m["return_date"])
    d2b_spine = d2b_manifest.get("session_spine")
    if not isinstance(d2b_spine, dict):
        raise ValueError("D2B manifest missing session_spine")
    for key in ("count", "date_min", "date_max", "sha256"):
        if d3m_spine[key] != d2b_spine.get(key):
            raise ValueError(f"D3M session spine drift against D2B: {key}")
    d3_dates = pd.DatetimeIndex(pd.to_datetime(d3["return_date"], errors="raise").dt.normalize())
    d3m_dates = pd.DatetimeIndex(d3m["return_date"])
    if not d3m_dates.equals(d3_dates):
        raise ValueError("D3M dates must match locked D3 dates")
    if not np.allclose(d3m["mktrf"], pd.to_numeric(d3["mktrf"], errors="raise"), rtol=0.0, atol=1e-15):
        raise ValueError("D3M mktrf must match locked D3 mktrf")
    if not np.allclose(d3m["rf"], pd.to_numeric(d3["rf"], errors="raise"), rtol=0.0, atol=1e-15):
        raise ValueError("D3M rf must match locked D3 rf")


def _session_spine_record(dates: pd.Series | pd.DatetimeIndex) -> dict[str, Any]:
    sessions = pd.DatetimeIndex(pd.to_datetime(dates, errors="raise")).normalize()
    if sessions.empty or sessions.has_duplicates or not sessions.is_monotonic_increasing:
        raise ValueError("session spine must be non-empty, unique, and sorted")
    serialised = "\n".join(sessions.strftime("%Y-%m-%d")) + "\n"
    return {
        "count": int(len(sessions)),
        "date_min": sessions.min().strftime("%Y-%m-%d"),
        "date_max": sessions.max().strftime("%Y-%m-%d"),
        "sha256": _sha256_bytes(serialised.encode("utf-8")),
    }


def _null_regression(
    dependent_variable: str,
    factors: list[str],
    observations: int,
    failure_reasons: list[str],
    hac_maxlags: int,
) -> dict[str, Any]:
    return {
        "status": "null",
        "dependent_variable": dependent_variable,
        "factors": factors,
        "observations": int(observations),
        "intercept": None,
        "intercept_hac_standard_error": None,
        "intercept_hac_t_stat": None,
        "intercept_hac_two_sided_p_value": None,
        "factor_betas": {factor: None for factor in factors},
        "factor_hac_t_stats": {factor: None for factor in factors},
        "hac_maxlags_requested": int(hac_maxlags),
        "hac_maxlags_used": 0,
        "use_correction": True,
        "failure_reasons": sorted(set(failure_reasons)),
    }


def fit_hac_regression(
    daily: pd.DataFrame,
    *,
    dependent_variable: str,
    factors: list[str],
    hac_maxlags: int = 59,
) -> dict[str, Any]:
    required = [dependent_variable, *factors]
    missing = [column for column in required if column not in daily.columns]
    if missing:
        raise ValueError(f"daily regression input missing columns: {missing}")
    clean = daily[required].copy()
    for column in required:
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    finite = np.isfinite(clean.to_numpy(dtype=float)).all(axis=1)
    complete = clean.loc[finite].copy()
    reasons: list[str] = []
    if len(complete) != len(clean):
        reasons.append("non_finite_regression_row")
    if len(complete) < 60:
        reasons.append("fewer_than_60_observations")
    if reasons:
        return _null_regression(dependent_variable, factors, len(complete), reasons, hac_maxlags)

    y = complete[dependent_variable].to_numpy(dtype=float)
    x = complete[factors].to_numpy(dtype=float)
    design = sm.add_constant(x, has_constant="add")
    expected_rank = len(factors) + 1
    if np.linalg.matrix_rank(design) != expected_rank:
        return _null_regression(
            dependent_variable,
            factors,
            len(complete),
            ["rank_deficient_regression"],
            hac_maxlags,
        )
    fit = sm.OLS(y, design).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": int(hac_maxlags), "use_correction": True},
    )
    params = [float(value) for value in fit.params]
    tvalues = [float(value) for value in fit.tvalues]
    bse = [float(value) for value in fit.bse]
    pvalues = [float(value) for value in fit.pvalues]
    return {
        "status": "valid",
        "dependent_variable": dependent_variable,
        "factors": factors,
        "observations": int(len(complete)),
        "intercept": params[0],
        "intercept_hac_standard_error": bse[0],
        "intercept_hac_t_stat": tvalues[0],
        "intercept_hac_two_sided_p_value": pvalues[0],
        "factor_betas": {factor: params[index + 1] for index, factor in enumerate(factors)},
        "factor_hac_t_stats": {factor: tvalues[index + 1] for index, factor in enumerate(factors)},
        "hac_maxlags_requested": int(hac_maxlags),
        "hac_maxlags_used": int(hac_maxlags),
        "use_correction": True,
        "failure_reasons": [],
    }


def _return_summary(values: pd.Series) -> dict[str, Any]:
    clean = pd.to_numeric(values, errors="coerce")
    clean = clean[np.isfinite(clean)]
    return {
        "observations": int(len(clean)),
        "mean": float(clean.mean()) if len(clean) else None,
        "standard_deviation": float(clean.std(ddof=1)) if len(clean) > 1 else (0.0 if len(clean) == 1 else None),
        "minimum": float(clean.min()) if len(clean) else None,
        "maximum": float(clean.max()) if len(clean) else None,
    }


def build_m5a_evidence(
    *,
    d1_manifest_path: Path = D1_MANIFEST_PATH,
    d2b_manifest_path: Path = D2B_MANIFEST_PATH,
    d3_manifest_path: Path = D3_MANIFEST_PATH,
    d3m_manifest_path: Path = D3M_MANIFEST_PATH,
    spread_cost_bps_per_day: float = 0.0,
    enforce_current_counts: bool = True,
) -> dict[str, Any]:
    cost_bps = _require_number(spread_cost_bps_per_day, "spread_cost_bps_per_day")
    if cost_bps < 0.0:
        raise ValueError("spread_cost_bps_per_day must be non-negative")
    daily, lineage, diagnostics = _prepare_daily_portfolio(
        d1_manifest_path=d1_manifest_path,
        d2b_manifest_path=d2b_manifest_path,
        d3_manifest_path=d3_manifest_path,
        d3m_manifest_path=d3m_manifest_path,
        enforce_current_counts=enforce_current_counts,
    )
    daily["gross_R_HL"] = pd.to_numeric(daily["R_HL"], errors="coerce")
    daily["spread_cost"] = float(cost_bps) / 10_000.0
    daily["net_R_HL"] = daily["gross_R_HL"] - daily["spread_cost"]

    models = {
        "mkt_only": ["mktrf"],
        "ff3": ["mktrf", "smb", "hml"],
    }
    results: dict[str, Any] = {}
    for label, dependent in (("gross", "gross_R_HL"), ("net", "net_R_HL")):
        results[label] = {
            model_name: fit_hac_regression(daily, dependent_variable=dependent, factors=factors)
            for model_name, factors in models.items()
        }

    evidence = {
        "schema_version": "1.0",
        "artifact_name": "pead_m5a_net_multifactor_alpha_test",
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "method_id": METHOD_ID,
        "lineage": lineage,
        "model_spec": {
            "daily_spread": "R_HL = equal_weight(Q5 asset_return) - equal_weight(Q1 asset_return)",
            "gross_dependent_variable": "gross_R_HL",
            "net_dependent_variable": "net_R_HL",
            "net_formula": "net_R_HL = gross_R_HL - spread_cost_bps_per_day / 10000",
            "models": models,
            "hac_maxlags": 59,
            "covariance": "HAC with finite-sample correction",
        },
        "cost_assumption": {
            "method": "constant_daily_spread_cost_bps_diagnostic",
            "spread_cost_bps_per_day": cost_bps,
            "exact_turnover_model": False,
        },
        "data_validity_flags": {
            "strict_pit_eps_vintage": False,
            "delisting_adjusted_returns": False,
            "tradable_return_source": False,
            "exact_turnover_cost_model": False,
            "m5a_preserves_smb_hml_from_existing_ken_french_source": True,
            "mom_factor_ingested": False,
            "ff5_factors_ingested": False,
            "locked_d3_rewritten": False,
            "diagnostic_only": True,
        },
        "daily_summary": {
            "sessions": int(len(daily)),
            "gross_spread": _return_summary(daily["gross_R_HL"]),
            "net_spread": _return_summary(daily["net_R_HL"]),
            "mktrf": _return_summary(daily["mktrf"]),
            "smb": _return_summary(daily["smb"]),
            "hml": _return_summary(daily["hml"]),
        },
        "m1b_reference": diagnostics,
        "results": results,
        "claim_boundary": {
            "allowed_claim": "diagnostic-only multi-factor and net-cost filter over current-vintage EPS/proxy-return/no-delisting PEAD evidence",
            "not_allowed_claim": "alpha, tradeable alpha, PIT alpha, net performance, strategy promotion, rank, recommendation, alert, or order readiness",
            "next_if_survives": "PIT EPS vintage plus delisting-adjusted tradable returns before any alpha assertion",
        },
        "evidence_policy": {
            "allowed_use": "diagnostic_methodology_review_only",
            "interpretation_performed": False,
            "strategy_promotion_authorized": False,
            "ranking_or_scoring_authorized": False,
            "alerts_or_recommendations_authorized": False,
            "broker_or_order_path_authorized": False,
            "forbidden_use": FORBIDDEN_USE,
        },
    }
    return _json_value(evidence)


def _json_bytes(evidence: dict[str, Any]) -> bytes:
    return (json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def write_evidence_atomic(evidence: dict[str, Any], output_path: Path) -> Path:
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=output_path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_json_bytes(evidence))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, output_path)
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temp_path.unlink(missing_ok=True)
        raise
    return output_path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PEAD M5a net multi-factor diagnostic runner")
    parser.add_argument("--run", action="store_true", help="Build and write M5a diagnostic evidence")
    parser.add_argument("--d1-manifest", type=Path, default=D1_MANIFEST_PATH)
    parser.add_argument("--d2b-manifest", type=Path, default=D2B_MANIFEST_PATH)
    parser.add_argument("--d3-manifest", type=Path, default=D3_MANIFEST_PATH)
    parser.add_argument("--d3m-manifest", type=Path, default=D3M_MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--spread-cost-bps-per-day", type=float, default=0.0)
    parser.add_argument("--no-enforce-counts", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.run:
        raise SystemExit("--run is required")
    evidence = build_m5a_evidence(
        d1_manifest_path=args.d1_manifest,
        d2b_manifest_path=args.d2b_manifest,
        d3_manifest_path=args.d3_manifest,
        d3m_manifest_path=args.d3m_manifest,
        spread_cost_bps_per_day=args.spread_cost_bps_per_day,
        enforce_current_counts=not args.no_enforce_counts,
    )
    output = write_evidence_atomic(evidence, args.output)
    print(f"[write] {_display_path(output)}")
    print(f"[scope] {SCOPE_ID}")
    print(f"[policy] diagnostic_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
