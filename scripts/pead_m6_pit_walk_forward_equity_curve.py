"""M6a PEAD PIT walk-forward tradable equity-curve framework.

This is an evidence-only backend runner.  M6a deliberately separates a
fail-closed input-contract gate from the portfolio/equity-curve engine so the
repo can prove it will not silently fall back to current-vintage EPS or
non-tradable/no-delisting return streams.

The current local PEAD artifacts are expected to fail the strict M6 contract:
D1 records current-vintage Compustat EPS limitations, D2/D2B do not establish a
tradable delisting-adjusted return stream, and the liquidity screen is not yet a
full as-of tradability contract.  A correct M6a run therefore writes blocked
JSON evidence rather than a fake CAGR.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import duckdb
import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ROOT = _REPO_ROOT
D1_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet.manifest.json"
D2A_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d2_daily_returns.parquet.manifest.json"
D2B_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d2b_event_windows.parquet.manifest.json"
M5A_EVIDENCE_PATH = ROOT / "docs" / "context" / "e2e_evidence" / "pead_m5a_net_multifactor_alpha_test.json"
OUTPUT_PATH = ROOT / "docs" / "context" / "e2e_evidence" / "pead_m6_pit_walk_forward_equity_curve.json"
DAILY_RETURNS_OUTPUT_PATH = ROOT / "data" / "processed" / "pead_m6_daily_portfolio_returns.parquet"
SPARSE_ENGINE_MEMORY_LIMIT = "1024MB"
SPARSE_ENGINE_THREADS = 1
SPARSE_ENGINE_INDEX_DTYPE = np.dtype("int32")

ROUND_ID = "ROUND-20260625-V2-PEAD-M6A-SCALE-SPARSE-PORTFOLIO-ENGINE"
SCOPE_ID = "V2_PEAD_M6A_SCALE_SPARSE_PORTFOLIO_ENGINE"
ARTIFACT_NAME = "pead_m6_pit_walk_forward_equity_curve"
METHOD_ID = "pit_contract_then_walk_forward_dollar_neutral_q5_q1_sparse_v2"

FORBIDDEN_USE = sorted(
    [
        "alpha_claims",
        "alerts",
        "broker_or_order_paths",
        "causal_claims",
        "capacity_claims",
        "current_vintage_eps_fallback",
        "live_alpha",
        "ranking_or_scoring",
        "recommendations",
        "strategy_promotion",
    ]
)


@dataclass(frozen=True)
class CostModel:
    """Explicit nonzero cost model for a future tradable M6 run."""

    entry_cost_bps: float = 5.0
    exit_cost_bps: float = 5.0
    slippage_bps: float = 2.5
    daily_short_borrow_bps: float = 1.0

    def validate(self) -> None:
        values = asdict(self)
        for label, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
                raise ValueError(f"{label} must be numeric")
            if not math.isfinite(float(value)) or float(value) < 0.0:
                raise ValueError(f"{label} must be finite and non-negative")
        if sum(float(value) for value in values.values()) <= 0.0:
            raise ValueError("cost model must be nonzero and explicit")

    @property
    def one_way_turnover_cost_bps(self) -> float:
        # Turnover is one-way absolute weight change.  Entry/exit bps are averaged
        # into a one-way estimate and slippage is charged on every traded dollar.
        return (float(self.entry_cost_bps) + float(self.exit_cost_bps)) / 2.0 + float(self.slippage_bps)

    def to_evidence(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["one_way_turnover_cost_bps"] = self.one_way_turnover_cost_bps
        payload["turnover_cost_formula"] = "turnover_cost = turnover * one_way_turnover_cost_bps / 10000"
        payload["short_borrow_cost_formula"] = "short_borrow_cost = short_exposure * daily_short_borrow_bps / 10000"
        payload["net_return_formula"] = "daily_net_return = daily_gross_return - turnover_cost - short_borrow_cost"
        payload["nonzero_explicit_costs"] = True
        return _json_value(payload)


@dataclass(frozen=True)
class PortfolioConfig:
    holding_period_sessions: int = 60
    quantiles: int = 5
    long_quantile: int = 5
    short_quantile: int = 1
    min_leg_count: int = 10
    gross_exposure_target: float = 1.0

    def validate(self) -> None:
        if self.holding_period_sessions <= 0:
            raise ValueError("holding_period_sessions must be positive")
        if self.quantiles < 2:
            raise ValueError("quantiles must be at least 2")
        if not (1 <= self.short_quantile <= self.quantiles and 1 <= self.long_quantile <= self.quantiles):
            raise ValueError("long/short quantiles must be inside quantile count")
        if self.long_quantile == self.short_quantile:
            raise ValueError("long and short quantiles must differ")
        if self.min_leg_count <= 0:
            raise ValueError("min_leg_count must be positive")
        if not math.isfinite(float(self.gross_exposure_target)) or self.gross_exposure_target <= 0.0:
            raise ValueError("gross_exposure_target must be positive")

    def to_evidence(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload.update(
            {
                "entry_rule": "first market session strictly after decision_date",
                "exit_rule": "drop after holding_period_sessions global trading-calendar return sessions",
                "signal_rule": "sort by SUE/signal into event-date quantiles; long Q5 and short Q1",
                "overlap_rule": "overlapping cohorts allowed; active names are renormalized daily to target gross exposure",
                "weight_rule": "+0.5 gross exposure across active long names and -0.5 across active short names",
                "missing_return_rule": "missing or non-finite tradable return rows are excluded before active-weight construction",
                "delisting_rule": "must be handled upstream by a delisting-adjusted tradable return column or fail closed",
            }
        )
        return _json_value(payload)


@dataclass(frozen=True)
class WalkForwardConfig:
    initial_train_years: int = 3
    min_test_days: int = 1
    fold_frequency: str = "annual_expanding_train"

    def validate(self) -> None:
        if self.initial_train_years < 1:
            raise ValueError("initial_train_years must be positive")
        if self.min_test_days < 1:
            raise ValueError("min_test_days must be positive")

    def to_evidence(self) -> dict[str, Any]:
        self.validate()
        payload = asdict(self)
        payload["split_key"] = "decision_date/event_date, never hindsight return dates"
        payload["parameter_freeze_rule"] = "holding period, quantiles, leg definitions, min leg count, liquidity filters, and cost assumptions are fixed before each test period"
        return _json_value(payload)


def _display_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return number if math.isfinite(number) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _read_json(path: Path) -> dict[str, Any]:
    payload = Path(path).read_text(encoding="utf-8")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError(f"{_display_path(path)} must contain a JSON object")
    return parsed


def _manifest_record(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "path": _display_path(Path(path)),
        "exists": Path(path).exists(),
        "schema_version": payload.get("schema_version"),
        "artifact_name": payload.get("artifact_name") or payload.get("label") or payload.get("builder"),
        "row_count": payload.get("row_count") or payload.get("counts", {}).get("rows"),
    }


def _contains_current_vintage_limitation(d1_manifest: dict[str, Any]) -> bool:
    text_parts: list[str] = []
    for key in ("limitations", "guardrails"):
        value = d1_manifest.get(key)
        if isinstance(value, list):
            text_parts.extend(str(item) for item in value)
    methodology = d1_manifest.get("methodology")
    if isinstance(methodology, dict):
        text_parts.extend(str(value) for value in methodology.values())
    joined = "\n".join(text_parts).lower()
    return "current-vintage" in joined or "restatement" in joined or "restated" in joined


def validate_input_contract(
    *,
    d1_manifest: dict[str, Any],
    d2a_manifest: dict[str, Any],
    d2b_manifest: dict[str, Any],
    allow_release_date_aligned_but_restated: bool = False,
) -> dict[str, Any]:
    """Validate whether current artifacts are allowed to feed a real M6 curve."""

    d1_columns = set(d1_manifest.get("columns", []))
    d2a_sources = [str(item).lower() for item in d2a_manifest.get("data_sources", [])]
    d2a_return_type = d2a_manifest.get("return_type_dist", {})
    d2a_warnings = "\n".join(str(item).lower() for item in d2a_manifest.get("warnings", []))
    d2b_declarations = d2b_manifest.get("declarations", {}) if isinstance(d2b_manifest.get("declarations"), dict) else {}
    d2b_policy = d2b_manifest.get("policy", {}) if isinstance(d2b_manifest.get("policy"), dict) else {}

    timing_pit_available = "rdq" in d1_columns or "release_date" in d1_columns
    current_vintage_detected = _contains_current_vintage_limitation(d1_manifest)
    strict_pit_eps_vintage = bool(timing_pit_available and not current_vintage_detected)
    eps_vintage = "strict_unrestated_vintage" if strict_pit_eps_vintage else "release_date_aligned_but_restated"

    d2a_has_compustat_source = any("compustat" in item or "comp" in item for item in d2a_sources)
    d2a_has_crsp_source = any("crsp" in item for item in d2a_sources)
    price_fallback_count = int(d2a_return_type.get("price_return_fallback", 0) or 0)
    tradable_return_source = bool(d2a_has_crsp_source and price_fallback_count == 0 and "fallback excludes dividends" not in d2a_warnings)

    delisting_adjusted_returns = bool(
        d2b_declarations.get("delisting_imputation") is True or d2b_declarations.get("delisting_label") is True
    )
    liquidity_selection_available = bool(d2b_policy.get("lookback_market_sessions") and d2b_policy.get("liquidity_score"))
    m6_full_liquidity_screen = False

    failure_reasons: list[str] = []
    if not timing_pit_available:
        failure_reasons.append("timing_pit_missing")
    if not strict_pit_eps_vintage and not allow_release_date_aligned_but_restated:
        failure_reasons.append("pit_vintage_blocked")
    if not tradable_return_source:
        failure_reasons.append("tradable_return_missing")
    if not delisting_adjusted_returns:
        failure_reasons.append("delisting_missing")
    if not m6_full_liquidity_screen:
        failure_reasons.append("tradability_liquidity_screen_missing")

    blocked = bool(failure_reasons)
    return _json_value(
        {
            "blocked": blocked,
            "failure_reasons": sorted(set(failure_reasons)),
            "flags": {
                "timing_pit_release_date_or_rdq_aligned": bool(timing_pit_available),
                "strict_pit_eps_vintage": bool(strict_pit_eps_vintage),
                "current_vintage_compustat_eps_detected": bool(current_vintage_detected),
                "eps_vintage": eps_vintage,
                "allow_release_date_aligned_but_restated": bool(allow_release_date_aligned_but_restated),
                "tradable_return_source": bool(tradable_return_source),
                "compustat_return_proxy_detected": bool(d2a_has_compustat_source),
                "price_return_fallback_count": price_fallback_count,
                "delisting_adjusted_returns": bool(delisting_adjusted_returns),
                "liquidity_selection_available": bool(liquidity_selection_available),
                "m6_full_asof_liquidity_screen": bool(m6_full_liquidity_screen),
            },
            "required_fields": [
                "event_id",
                "gvkey/permno/security_id",
                "announcement_date",
                "decision_date",
                "PIT EPS/SUE value as of decision_date",
                "security tradability flag as of decision_date",
                "daily tradable total return",
                "delisting return if applicable",
                "price/liquidity screen",
            ],
            "available_now": {
                "timing_pit_layer": bool(timing_pit_available),
                "vintage_unrestated_layer": bool(strict_pit_eps_vintage),
                "best_available_eps_vintage_label": eps_vintage,
                "return_source_basis": "Compustat total-return proxy with price-return fallback" if d2a_has_compustat_source else "unknown",
                "d2b_liquidity_basis": d2b_policy.get("liquidity_score"),
            },
        }
    )


def build_walk_forward_folds(
    decision_dates: Iterable[Any],
    config: WalkForwardConfig = WalkForwardConfig(),
) -> list[dict[str, Any]]:
    config.validate()
    dates = pd.to_datetime(pd.Series(list(decision_dates)), errors="coerce").dropna().dt.normalize()
    if dates.empty:
        return []
    years = sorted(int(year) for year in dates.dt.year.unique())
    if len(years) <= config.initial_train_years:
        return []
    folds: list[dict[str, Any]] = []
    first_year = min(years)
    for index, test_year in enumerate(years[config.initial_train_years :], start=1):
        train_start = pd.Timestamp(year=first_year, month=1, day=1)
        train_end = pd.Timestamp(year=test_year - 1, month=12, day=31)
        test_start = pd.Timestamp(year=test_year, month=1, day=1)
        test_end = pd.Timestamp(year=test_year, month=12, day=31)
        test_days = int(((dates >= test_start) & (dates <= test_end)).sum())
        if test_days < config.min_test_days:
            continue
        folds.append(
            {
                "fold_id": f"fold_{index:02d}_{test_year}",
                "train_start": train_start.strftime("%Y-%m-%d"),
                "train_end": train_end.strftime("%Y-%m-%d"),
                "test_start": test_start.strftime("%Y-%m-%d"),
                "test_end": test_end.strftime("%Y-%m-%d"),
                "test_decision_events": test_days,
                "split_key": "decision_date",
            }
        )
    return folds


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _assign_signal_quantiles(events: pd.DataFrame, config: PortfolioConfig) -> pd.DataFrame:
    config.validate()
    required = {"event_id", "security_id", "decision_date", "signal", "tradable", "liquidity_pass"}
    _require_columns(events, required, "events")
    out = events.copy()
    out["decision_date"] = pd.to_datetime(out["decision_date"], errors="coerce").dt.normalize()
    out["signal"] = pd.to_numeric(out["signal"], errors="coerce")
    out = out.dropna(subset=["event_id", "security_id", "decision_date", "signal"])
    out = out[out["tradable"].astype(bool) & out["liquidity_pass"].astype(bool)].copy()
    if out.empty:
        out["signal_quantile"] = pd.Series(dtype="Int64")
        out["side"] = pd.Series(dtype=float)
        return out

    def assign_group(group: pd.DataFrame) -> pd.DataFrame:
        group = group.sort_values(["signal", "event_id", "security_id"]).copy()
        if len(group) < config.min_leg_count * 2:
            group["signal_quantile"] = pd.NA
            return group
        ranks = group["signal"].rank(method="first")
        quantiles = np.ceil(ranks / float(len(group)) * float(config.quantiles)).astype(int)
        group["signal_quantile"] = np.clip(quantiles, 1, config.quantiles)
        return group

    assigned_groups = [assign_group(group) for _, group in out.groupby("decision_date", sort=True)]
    out = pd.concat(assigned_groups, ignore_index=True) if assigned_groups else out.iloc[0:0].copy()
    out["side"] = np.where(
        out["signal_quantile"].eq(config.long_quantile),
        1.0,
        np.where(out["signal_quantile"].eq(config.short_quantile), -1.0, 0.0),
    )
    return out[out["side"].ne(0.0)].copy()


_DAILY_PORTFOLIO_OUTPUT_COLUMNS = [
    "return_date",
    "daily_gross_return",
    "long_leg_contribution",
    "short_leg_contribution",
    "average_gross_exposure",
    "average_net_exposure",
    "short_exposure",
    "active_names",
    "turnover",
    "turnover_cost",
    "short_borrow_cost",
    "daily_net_return",
]


def _assert_no_object_dtypes(frame: pd.DataFrame, label: str) -> None:
    object_columns = [str(column) for column, dtype in frame.dtypes.items() if pd.api.types.is_object_dtype(dtype)]
    if object_columns:
        raise ValueError(f"{label} must not carry object-dtype columns into DuckDB: {object_columns}")


def _require_int32_capacity(label: str, size: int) -> None:
    if size > np.iinfo(SPARSE_ENGINE_INDEX_DTYPE).max:
        raise ValueError(f"{label} exceeds the sparse engine int32 index capacity")


def _prepare_sparse_engine_relations(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    portfolio_config: PortfolioConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Project inputs into numeric-only sparse relations and a global session index.

    The calendar relation is the one authoritative sorted session spine.  Events
    receive ``entry_idx``/``exit_idx`` and returns receive ``return_idx`` so the
    sparse interval predicate is explicit and avoids date-range ambiguity.
    """

    selected = _assign_signal_quantiles(events, portfolio_config)
    if selected.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    selected = selected.loc[:, ["event_id", "security_id", "decision_date", "side"]].copy()
    selected["decision_date"] = pd.to_datetime(selected["decision_date"], errors="coerce").dt.normalize()
    selected = selected.dropna(subset=["event_id", "security_id", "decision_date", "side"])
    if selected.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    ret = returns.loc[:, ["security_id", "return_date", "tradable_total_return"]].copy()
    ret["return_date"] = pd.to_datetime(ret["return_date"], errors="coerce").dt.normalize()
    ret["tradable_total_return"] = pd.to_numeric(ret["tradable_total_return"], errors="coerce")
    ret = ret.dropna(subset=["security_id", "return_date", "tradable_total_return"])
    ret = ret[np.isfinite(ret["tradable_total_return"].to_numpy(dtype=np.float64))].copy()
    if ret.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    selected["_event_token"] = selected["event_id"].astype("string")
    selected["_security_token"] = selected["security_id"].astype("string")
    ret["_security_token"] = ret["security_id"].astype("string")
    if selected["_event_token"].duplicated().any():
        raise ValueError("selected event_id values must be unique for deterministic sparse aggregation")

    security_tokens = pd.concat([selected["_security_token"], ret["_security_token"]], ignore_index=True).dropna()
    security_categories = pd.Index(security_tokens.unique()).sort_values()
    _require_int32_capacity("security identifier cardinality", len(security_categories))
    selected["_security_idx"] = pd.Categorical(
        selected["_security_token"], categories=security_categories, ordered=True
    ).codes.astype(SPARSE_ENGINE_INDEX_DTYPE, copy=False)
    ret["_security_idx"] = pd.Categorical(
        ret["_security_token"], categories=security_categories, ordered=True
    ).codes.astype(SPARSE_ENGINE_INDEX_DTYPE, copy=False)

    calendar = pd.DataFrame({"return_date": ret["return_date"].drop_duplicates().sort_values().to_numpy()})
    _require_int32_capacity("trading-calendar session count", len(calendar))
    calendar["return_idx"] = np.arange(len(calendar), dtype=SPARSE_ENGINE_INDEX_DTYPE)
    calendar_dates = calendar["return_date"].to_numpy(dtype="datetime64[ns]")
    selected["entry_idx"] = calendar_dates.searchsorted(
        selected["decision_date"].to_numpy(dtype="datetime64[ns]"), side="right"
    )
    selected = selected[selected["entry_idx"] < len(calendar)].copy()
    if selected.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if int(selected["entry_idx"].max()) + int(portfolio_config.holding_period_sessions) > np.iinfo(SPARSE_ENGINE_INDEX_DTYPE).max:
        raise ValueError("entry/exit indices exceed the sparse engine int32 index capacity")
    selected["entry_idx"] = selected["entry_idx"].astype(SPARSE_ENGINE_INDEX_DTYPE, copy=False)
    selected["exit_idx"] = (
        selected["entry_idx"].to_numpy(dtype=np.int64) + int(portfolio_config.holding_period_sessions) - 1
    ).astype(SPARSE_ENGINE_INDEX_DTYPE, copy=False)

    return_idx_lookup = pd.Series(calendar["return_idx"].to_numpy(), index=calendar["return_date"])
    ret["return_idx"] = ret["return_date"].map(return_idx_lookup).astype(SPARSE_ENGINE_INDEX_DTYPE, copy=False)
    return_relation = ret.loc[:, ["_security_idx", "return_idx", "tradable_total_return"]].rename(
        columns={"_security_idx": "security_idx"}
    )
    return_relation = return_relation.sort_values(["security_idx", "return_idx"], kind="mergesort").reset_index(drop=True)
    if return_relation.duplicated(["security_idx", "return_idx"]).any():
        raise ValueError("returns must contain at most one finite row per security_id and return_date")

    selected = selected.sort_values(["decision_date", "_event_token", "_security_token"], kind="mergesort").reset_index(drop=True)
    _require_int32_capacity("selected event count", len(selected))
    event_relation = pd.DataFrame(
        {
            "event_idx": np.arange(len(selected), dtype=SPARSE_ENGINE_INDEX_DTYPE),
            "security_idx": selected["_security_idx"].to_numpy(dtype=SPARSE_ENGINE_INDEX_DTYPE),
            "entry_idx": selected["entry_idx"].to_numpy(dtype=SPARSE_ENGINE_INDEX_DTYPE),
            "exit_idx": selected["exit_idx"].to_numpy(dtype=SPARSE_ENGINE_INDEX_DTYPE),
            "side": selected["side"].to_numpy(dtype=np.float64),
        }
    )
    calendar_relation = calendar.loc[:, ["return_idx", "return_date"]]
    _assert_no_object_dtypes(event_relation, "selected_events")
    _assert_no_object_dtypes(return_relation, "input_returns")
    _assert_no_object_dtypes(calendar_relation, "trading_calendar")
    return event_relation, return_relation, calendar_relation


def daily_portfolio_output_hash(daily: pd.DataFrame) -> str:
    """Return a canonical SHA-256 hash for reproducibility checks and evidence."""

    _require_columns(daily, set(_DAILY_PORTFOLIO_OUTPUT_COLUMNS), "daily")
    out = daily.loc[:, _DAILY_PORTFOLIO_OUTPUT_COLUMNS].copy()
    out["return_date"] = pd.to_datetime(out["return_date"], errors="raise").dt.normalize()
    if out["return_date"].duplicated().any():
        raise ValueError("daily output must contain at most one row per return_date")
    out = out.sort_values("return_date", kind="mergesort").reset_index(drop=True)
    numeric_columns = [column for column in _DAILY_PORTFOLIO_OUTPUT_COLUMNS if column != "return_date"]
    for column in numeric_columns:
        out[column] = pd.to_numeric(out[column], errors="raise").astype(np.float64)
    if not np.isfinite(out[numeric_columns].to_numpy(dtype=np.float64)).all():
        raise ValueError("daily output hash requires finite numeric values")
    payload = out.to_csv(
        index=False,
        lineterminator="\n",
        date_format="%Y-%m-%d",
        float_format="%.17g",
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def engine_runtime_contract(portfolio_config: PortfolioConfig = PortfolioConfig()) -> dict[str, Any]:
    """Describe the M6a engine's scale boundary without asserting data readiness."""

    portfolio_config.validate()
    return {
        "engine_architecture": "duckdb_sparse_interval_window_join_direct_daily_aggregate_v2",
        "position_day_upper_bound_formula": "eligible_selected_events * holding_period_sessions",
        "holding_period_sessions": int(portfolio_config.holding_period_sessions),
        "duckdb_memory_limit": SPARSE_ENGINE_MEMORY_LIMIT,
        "duckdb_threads": SPARSE_ENGINE_THREADS,
        "calendar_index": {
            "index_name": "return_idx",
            "index_dtype": str(SPARSE_ENGINE_INDEX_DTYPE),
            "entry_exit_predicate": "entry_idx <= return_idx <= exit_idx",
            "calendar_source": "projected distinct return_date sorted ascending",
        },
        "input_projection": {
            "event_columns": ["event_id", "security_id", "decision_date", "signal", "tradable", "liquidity_pass"],
            "return_columns": ["security_id", "return_date", "tradable_total_return"],
            "duckdb_identifier_dtype": str(SPARSE_ENGINE_INDEX_DTYPE),
            "duckdb_object_dtype_relations_forbidden": True,
        },
        "determinism": {
            "compensated_fsum_aggregates": True,
            "single_duckdb_thread": True,
            "canonical_daily_output_sha256": True,
        },
        "python_event_row_loop": False,
        "dense_return_date_by_security_matrix_materialized": False,
        "position_day_output_persisted": False,
        "turnover_rule": "sparse union of previous and current security weights, plus final trade-to-zero exit",
        "m6a_scale_engine_ready": True,
        "m6b_real_run_wiring_allowed": True,
        "m6b_real_run_wiring_allowed_semantics": "engine scale only; strict PIT vintage, delisting-adjusted returns, and as-of tradability/liquidity data gates remain independent and fail closed",
    }


def build_daily_portfolio_returns(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    portfolio_config: PortfolioConfig = PortfolioConfig(),
    cost_model: CostModel = CostModel(),
) -> pd.DataFrame:
    """Build daily gross/net Q5-Q1 returns through a deterministic sparse DuckDB plan.

    A sorted global trading-calendar relation provides integer session indices.
    Events use explicit ``entry_idx <= return_idx <= exit_idx`` bounds; returns
    and event identifiers are projected to int32 before registration.  DuckDB
    aggregates directly to daily returns with ordered compensated sums, so no
    event-level Python loop, dataframe-list accumulation, or wide matrix exists.
    """

    portfolio_config.validate()
    cost_model.validate()
    _require_columns(returns, {"security_id", "return_date", "tradable_total_return"}, "returns")
    selected_events, input_returns, trading_calendar = _prepare_sparse_engine_relations(events, returns, portfolio_config)
    if selected_events.empty or input_returns.empty:
        return _empty_daily_portfolio_frame()

    connection = duckdb.connect(database=":memory:", config={"memory_limit": SPARSE_ENGINE_MEMORY_LIMIT})
    try:
        connection.execute("SET preserve_insertion_order = false")
        connection.execute(f"SET threads = {SPARSE_ENGINE_THREADS}")
        connection.register("selected_events", selected_events)
        connection.register("input_returns", input_returns)
        connection.register("trading_calendar", trading_calendar)
        daily = connection.execute(
            """
            WITH sparse_positions AS (
                SELECT
                    event.event_idx,
                    event.security_idx,
                    event.side,
                    ret.return_idx,
                    ret.tradable_total_return
                FROM selected_events AS event
                JOIN input_returns AS ret
                    ON event.security_idx = ret.security_idx
                    AND ret.return_idx BETWEEN event.entry_idx AND event.exit_idx
            ),
            leg_counts AS (
                SELECT
                    return_idx,
                    COUNT(CASE WHEN side = 1.0 THEN event_idx END) AS long_event_count,
                    COUNT(CASE WHEN side = -1.0 THEN event_idx END) AS short_event_count
                FROM sparse_positions
                GROUP BY return_idx
            ),
            weighted_positions AS (
                SELECT
                    position.event_idx,
                    position.return_idx,
                    position.security_idx,
                    position.tradable_total_return,
                    position.side * ? / CASE
                        WHEN position.side = 1.0 THEN counts.long_event_count
                        ELSE counts.short_event_count
                    END AS position_weight
                FROM sparse_positions AS position
                JOIN leg_counts AS counts USING (return_idx)
                WHERE counts.long_event_count >= ?
                    AND counts.short_event_count >= ?
            ),
            by_security AS (
                SELECT
                    return_idx,
                    security_idx,
                    fsum(position_weight) AS position_weight,
                    MAX(tradable_total_return) AS tradable_total_return
                FROM weighted_positions
                GROUP BY return_idx, security_idx
            ),
            daily_base AS (
                SELECT
                    return_idx,
                    fsum(position_weight * tradable_total_return) AS daily_gross_return,
                    fsum(CASE WHEN position_weight > 0.0 THEN position_weight * tradable_total_return ELSE 0.0 END) AS long_leg_contribution,
                    fsum(CASE WHEN position_weight < 0.0 THEN position_weight * tradable_total_return ELSE 0.0 END) AS short_leg_contribution,
                    fsum(ABS(position_weight)) AS average_gross_exposure,
                    fsum(position_weight) AS average_net_exposure,
                    fsum(CASE WHEN position_weight < 0.0 THEN ABS(position_weight) ELSE 0.0 END) AS short_exposure,
                    COUNT(*) AS active_names
                FROM by_security
                GROUP BY return_idx
            ),
            daily_dates AS (
                SELECT
                    return_idx,
                    LAG(return_idx) OVER (ORDER BY return_idx) AS previous_return_idx
                FROM daily_base
            ),
            current_weight_change AS (
                SELECT
                    dates.return_idx,
                    fsum(ABS(current.position_weight - COALESCE(previous.position_weight, 0.0))) AS turnover
                FROM daily_dates AS dates
                JOIN by_security AS current
                    ON current.return_idx = dates.return_idx
                LEFT JOIN by_security AS previous
                    ON previous.return_idx = dates.previous_return_idx
                    AND previous.security_idx = current.security_idx
                GROUP BY dates.return_idx
            ),
            previous_only_weight_change AS (
                SELECT
                    dates.return_idx,
                    fsum(ABS(previous.position_weight)) AS turnover
                FROM daily_dates AS dates
                JOIN by_security AS previous
                    ON previous.return_idx = dates.previous_return_idx
                LEFT JOIN by_security AS current
                    ON current.return_idx = dates.return_idx
                    AND current.security_idx = previous.security_idx
                WHERE current.security_idx IS NULL
                GROUP BY dates.return_idx
            ),
            final_trade_to_zero AS (
                SELECT
                    by_security.return_idx,
                    fsum(ABS(by_security.position_weight)) AS turnover
                FROM by_security
                WHERE by_security.return_idx = (SELECT MAX(return_idx) FROM daily_base)
                GROUP BY by_security.return_idx
            )
            SELECT
                calendar.return_date,
                daily.daily_gross_return,
                daily.long_leg_contribution,
                daily.short_leg_contribution,
                daily.average_gross_exposure,
                daily.average_net_exposure,
                daily.short_exposure,
                daily.active_names,
                COALESCE(current_turnover.turnover, 0.0)
                    + COALESCE(previous_only_turnover.turnover, 0.0)
                    + COALESCE(final_exit.turnover, 0.0) AS turnover
            FROM daily_base AS daily
            JOIN trading_calendar AS calendar USING (return_idx)
            LEFT JOIN current_weight_change AS current_turnover USING (return_idx)
            LEFT JOIN previous_only_weight_change AS previous_only_turnover USING (return_idx)
            LEFT JOIN final_trade_to_zero AS final_exit USING (return_idx)
            ORDER BY daily.return_idx
            """,
            [
                float(portfolio_config.gross_exposure_target / 2.0),
                int(portfolio_config.min_leg_count),
                int(portfolio_config.min_leg_count),
            ],
        ).fetchdf()
    finally:
        connection.close()

    if daily.empty:
        return _empty_daily_portfolio_frame()
    daily["return_date"] = pd.to_datetime(daily["return_date"], errors="raise").dt.normalize()
    daily["turnover"] = pd.to_numeric(daily["turnover"], errors="raise").astype(float)
    daily["turnover_cost"] = daily["turnover"] * cost_model.one_way_turnover_cost_bps / 10_000.0
    daily["short_borrow_cost"] = daily["short_exposure"] * cost_model.daily_short_borrow_bps / 10_000.0
    daily["daily_net_return"] = daily["daily_gross_return"] - daily["turnover_cost"] - daily["short_borrow_cost"]
    return daily


def _empty_daily_portfolio_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "return_date",
            "daily_gross_return",
            "long_leg_contribution",
            "short_leg_contribution",
            "average_gross_exposure",
            "average_net_exposure",
            "short_exposure",
            "active_names",
            "turnover",
            "turnover_cost",
            "short_borrow_cost",
            "daily_net_return",
        ]
    )


def _compound_return(values: pd.Series) -> float | None:
    clean = pd.to_numeric(values, errors="coerce")
    clean = clean[np.isfinite(clean)]
    if clean.empty:
        return None
    return float((1.0 + clean).prod() - 1.0)


def _max_drawdown(equity: pd.Series) -> float | None:
    if equity.empty:
        return None
    running_max = equity.cummax()
    drawdown = equity / running_max - 1.0
    return float(drawdown.min())


def compute_equity_curve_metrics(daily: pd.DataFrame) -> dict[str, Any]:
    if daily.empty:
        return _json_value(
            {
                "daily_return_summary": {"sessions": 0},
                "equity_curve_summary": {"status": "null", "failure_reasons": ["no_daily_returns"]},
                "risk_metrics": {},
                "monthly_return_table": {},
                "yearly_return_table": {},
            }
        )
    required = {"return_date", "daily_gross_return", "daily_net_return", "turnover", "average_gross_exposure", "average_net_exposure"}
    _require_columns(daily, required, "daily")
    out = daily.copy().sort_values("return_date").reset_index(drop=True)
    out["return_date"] = pd.to_datetime(out["return_date"], errors="raise").dt.normalize()
    out["daily_net_return"] = pd.to_numeric(out["daily_net_return"], errors="coerce")
    out["daily_gross_return"] = pd.to_numeric(out["daily_gross_return"], errors="coerce")
    if not np.isfinite(out[["daily_net_return", "daily_gross_return"]].to_numpy(dtype=float)).all():
        raise ValueError("daily returns must be finite")

    net_equity = (1.0 + out["daily_net_return"]).cumprod()
    gross_equity = (1.0 + out["daily_gross_return"]).cumprod()
    out["equity_curve"] = net_equity
    calendar_days = max(1, int((out["return_date"].max() - out["return_date"].min()).days))
    gross_cagr = float(gross_equity.iloc[-1] ** (365.25 / calendar_days) - 1.0) if calendar_days > 0 else None
    net_cagr = float(net_equity.iloc[-1] ** (365.25 / calendar_days) - 1.0) if calendar_days > 0 else None
    daily_std = float(out["daily_net_return"].std(ddof=1)) if len(out) > 1 else 0.0
    annualized_vol = daily_std * math.sqrt(252.0)
    sharpe = None if annualized_vol == 0.0 else float(out["daily_net_return"].mean() / daily_std * math.sqrt(252.0))

    monthly = out.set_index("return_date")["daily_net_return"].resample("ME").apply(lambda s: (1.0 + s).prod() - 1.0)
    yearly = out.set_index("return_date")["daily_net_return"].resample("YE").apply(lambda s: (1.0 + s).prod() - 1.0)
    return _json_value(
        {
            "daily_return_summary": {
                "sessions": int(len(out)),
                "start_date": out["return_date"].min().strftime("%Y-%m-%d"),
                "end_date": out["return_date"].max().strftime("%Y-%m-%d"),
                "mean_gross_return": float(out["daily_gross_return"].mean()),
                "mean_net_return": float(out["daily_net_return"].mean()),
                "hit_rate_by_day": float((out["daily_net_return"] > 0.0).mean()),
            },
            "equity_curve_summary": {
                "status": "valid",
                "starting_equity": 1.0,
                "ending_equity": float(net_equity.iloc[-1]),
                "gross_ending_equity": float(gross_equity.iloc[-1]),
                "calendar_days": calendar_days,
                "gross_CAGR": gross_cagr,
                "net_CAGR": net_cagr,
                "max_drawdown": _max_drawdown(net_equity),
                "equity_reproducible_from_daily_net_returns": bool(
                    np.isclose(net_equity.iloc[-1], (1.0 + out["daily_net_return"]).prod(), rtol=0.0, atol=1e-15)
                ),
            },
            "risk_metrics": {
                "annualized_volatility": annualized_vol,
                "Sharpe": sharpe,
                "average_turnover": float(out["turnover"].mean()),
                "average_gross_exposure": float(out["average_gross_exposure"].mean()),
                "average_net_exposure": float(out["average_net_exposure"].mean()),
                "long_leg_contribution": float(out.get("long_leg_contribution", pd.Series(dtype=float)).sum()),
                "short_leg_contribution": float(out.get("short_leg_contribution", pd.Series(dtype=float)).sum()),
            },
            "monthly_return_table": {idx.strftime("%Y-%m"): float(value) for idx, value in monthly.items()},
            "yearly_return_table": {idx.strftime("%Y"): float(value) for idx, value in yearly.items()},
        }
    )


def compute_fold_results(daily: pd.DataFrame, folds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if daily.empty:
        return []
    out = daily.copy()
    out["return_date"] = pd.to_datetime(out["return_date"], errors="raise").dt.normalize()
    results: list[dict[str, Any]] = []
    for fold in folds:
        start = pd.Timestamp(fold["test_start"])
        end = pd.Timestamp(fold["test_end"])
        subset = out[(out["return_date"] >= start) & (out["return_date"] <= end)].copy()
        metrics = compute_equity_curve_metrics(subset)
        summary = metrics["equity_curve_summary"]
        risk = metrics["risk_metrics"]
        results.append(
            _json_value(
                {
                    "fold_id": fold["fold_id"],
                    "train_start": fold["train_start"],
                    "train_end": fold["train_end"],
                    "test_start": fold["test_start"],
                    "test_end": fold["test_end"],
                    "test_days": metrics["daily_return_summary"].get("sessions", 0),
                    "gross_CAGR": summary.get("gross_CAGR"),
                    "net_CAGR": summary.get("net_CAGR"),
                    "max_drawdown": summary.get("max_drawdown"),
                    "Sharpe": risk.get("Sharpe"),
                    "turnover": risk.get("average_turnover"),
                    "average_names_long": None,
                    "average_names_short": None,
                    "coverage_rate": None,
                }
            )
        )
    return results


def build_validate_inputs_evidence(
    *,
    d1_manifest_path: Path = D1_MANIFEST_PATH,
    d2a_manifest_path: Path = D2A_MANIFEST_PATH,
    d2b_manifest_path: Path = D2B_MANIFEST_PATH,
    m5a_evidence_path: Path = M5A_EVIDENCE_PATH,
    allow_release_date_aligned_but_restated: bool = False,
    mode: str = "validate_inputs",
) -> dict[str, Any]:
    d1_manifest = _read_json(d1_manifest_path)
    d2a_manifest = _read_json(d2a_manifest_path)
    d2b_manifest = _read_json(d2b_manifest_path)
    m5a_evidence = _read_json(m5a_evidence_path) if Path(m5a_evidence_path).exists() else {}
    contract = validate_input_contract(
        d1_manifest=d1_manifest,
        d2a_manifest=d2a_manifest,
        d2b_manifest=d2b_manifest,
        allow_release_date_aligned_but_restated=allow_release_date_aligned_but_restated,
    )
    cost_model = CostModel()
    portfolio_config = PortfolioConfig()
    walk_forward_config = WalkForwardConfig()
    data_flags = dict(contract["flags"])
    runtime_contract = engine_runtime_contract(portfolio_config)
    data_flags.update(
        {
            "evidence_only": True,
            "validate_inputs_fail_closed": bool(contract["blocked"]),
            "daily_returns_emitted": False,
            "equity_curve_emitted": False,
            "m6a_scale_engine_ready": bool(runtime_contract["m6a_scale_engine_ready"]),
            "m6b_real_run_wiring_allowed": bool(runtime_contract["m6b_real_run_wiring_allowed"]),
            "m6b_data_contract_ready": not bool(contract["blocked"]),
            "m6b_data_dependency_required": bool(contract["blocked"]),
        }
    )
    blocked = bool(contract["blocked"])
    evidence = {
        "schema_version": "1.0",
        "artifact_name": ARTIFACT_NAME,
        "round_id": ROUND_ID,
        "scope_id": SCOPE_ID,
        "method_id": METHOD_ID,
        "mode": mode,
        "workflow_status": "blocked_fail_closed" if blocked else "ready_for_strict_run",
        "lineage": {
            "d1_sue_signal": _manifest_record(d1_manifest_path, d1_manifest),
            "d2a_daily_returns": _manifest_record(d2a_manifest_path, d2a_manifest),
            "d2b_event_windows": _manifest_record(d2b_manifest_path, d2b_manifest),
            "m5a_reference": {
                "path": _display_path(m5a_evidence_path),
                "artifact_name": m5a_evidence.get("artifact_name"),
                "scope_id": m5a_evidence.get("scope_id"),
                "diagnostic_only": m5a_evidence.get("data_validity_flags", {}).get("diagnostic_only"),
            },
        },
        "pit_data_contract": contract,
        "walk_forward_config": walk_forward_config.to_evidence(),
        "portfolio_construction": portfolio_config.to_evidence(),
        "cost_model": cost_model.to_evidence(),
        "engine_runtime": _json_value(runtime_contract),
        "daily_return_summary": {"status": "not_emitted", "reason": "input_contract_blocked" if blocked else "validate_inputs_only"},
        "equity_curve_summary": {"status": "not_emitted", "reason": "input_contract_blocked" if blocked else "validate_inputs_only"},
        "fold_results": [],
        "risk_metrics": {},
        "coverage": {
            "d1_rows": d1_manifest.get("row_count"),
            "d2a_rows": d2a_manifest.get("row_count"),
            "d2b_rows": d2b_manifest.get("counts", {}).get("rows"),
            "d2b_events": d2b_manifest.get("counts", {}).get("events"),
        },
        "failure_reasons": contract["failure_reasons"],
        "data_validity_flags": data_flags,
        "claim_boundary": {
            "allowed_claim": "M6a input-contract and walk-forward equity-curve framework evidence only; no tradable curve is emitted while strict data inputs are missing.",
            "timing_pit_status": "available" if contract["flags"]["timing_pit_release_date_or_rdq_aligned"] else "missing",
            "eps_vintage_status": contract["flags"]["eps_vintage"],
            "not_allowed_claim": "strict vintage-PIT, delisting-adjusted tradable net CAGR, live alpha, strategy promotion, ranking/scoring, alerts, recommendations, or orders",
            "next_if_blocked": "M6b data-prep round: add unrestated/first-public EPS vintage or explicitly accept best-available restated flag, plus delisting-adjusted tradable daily returns and full as-of liquidity/tradability screen. The engine-scale flag does not waive these independent data gates.",
        },
        "evidence_policy": {
            "allowed_use": "m6a_framework_and_input_contract_review_only",
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
    fd, temp_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
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
    parser = argparse.ArgumentParser(description="PEAD M6a PIT walk-forward equity-curve framework")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true", help="Write strict input-contract evidence and fail closed when M6 data is missing")
    mode.add_argument("--run", action="store_true", help="Run only if strict M6 data contract passes; otherwise write blocked evidence and return non-zero")
    parser.add_argument("--d1-manifest", type=Path, default=D1_MANIFEST_PATH)
    parser.add_argument("--d2a-manifest", type=Path, default=D2A_MANIFEST_PATH)
    parser.add_argument("--d2b-manifest", type=Path, default=D2B_MANIFEST_PATH)
    parser.add_argument("--m5a-evidence", type=Path, default=M5A_EVIDENCE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--daily-returns-output", type=Path, default=DAILY_RETURNS_OUTPUT_PATH)
    parser.add_argument(
        "--allow-release-date-aligned-but-restated",
        action="store_true",
        help="Do not block solely on EPS restatement/vintage limitations; still labels eps_vintage as release_date_aligned_but_restated.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    mode = "run" if args.run else "validate_inputs"
    evidence = build_validate_inputs_evidence(
        d1_manifest_path=args.d1_manifest,
        d2a_manifest_path=args.d2a_manifest,
        d2b_manifest_path=args.d2b_manifest,
        m5a_evidence_path=args.m5a_evidence,
        allow_release_date_aligned_but_restated=args.allow_release_date_aligned_but_restated,
        mode=mode,
    )
    output = write_evidence_atomic(evidence, args.output)
    print(f"[write] {_display_path(output)}")
    print(f"[scope] {SCOPE_ID}")
    print(f"[status] {evidence['workflow_status']}")
    if args.run and evidence["workflow_status"] == "blocked_fail_closed":
        print("[blocked] strict M6 inputs are missing; daily returns/equity curve not emitted")
        return 2
    if args.run:
        # The current repo has no strict input path that can reach this branch.  The
        # dataframe engine above is covered by unit tests and will be wired to real
        # strict inputs only after M6b data-prep closes the contract.
        print("[ready] strict contract passed; production data wiring is reserved for M6b")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
