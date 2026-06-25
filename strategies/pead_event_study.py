"""Fail-closed PEAD event-window and cross-sectional statistics contracts.

This module is intentionally data-source agnostic.  It consumes already-selected
security returns and never reads providers, Parquet files, or data-layer builders.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import re
import numpy as np
import pandas as pd
import statsmodels.api as sm


EVENT_REQUIRED_COLUMNS = frozenset(
    {"event_id", "issuer_id", "security_id", "event_date", "sue", "is_primary_security"}
)
RETURN_REQUIRED_COLUMNS = frozenset({"security_id", "date", "total_return"})
RESERVED_BENCHMARK_COLUMNS = frozenset(
    {
        *EVENT_REQUIRED_COLUMNS,
        *RETURN_REQUIRED_COLUMNS,
        "abnormal_return",
        "asset_return",
        "return_date",
        "event_day",
        "window_complete",
    }
)
TIMEZONE_TOKEN_RE = re.compile(r"(?:z|[+-]\d{2}:?\d{2})$", re.IGNORECASE)


@dataclass(frozen=True)
class PeadEventStudyConfig:
    """Configuration for one explicitly bounded PEAD research contract."""

    start_day: int = 1
    end_day: int = 60
    benchmark_return_column: str | None = None
    cohort_frequency: str = "D"
    allow_ex_post_cohorts: bool = False
    quantiles: int = 5
    min_events_per_cohort: int | None = None
    hac_maxlags: int = 4
    require_complete_window: bool = True

    @property
    def expected_observations(self) -> int:
        return int(self.end_day - self.start_day + 1)


@dataclass(frozen=True)
class QuantileAnalysisResult:
    assignments: pd.DataFrame
    quantile_summary: pd.DataFrame
    cohort_spreads: pd.DataFrame
    spread_statistics: dict[str, float | int]


@dataclass(frozen=True)
class PeadEventStudyResult:
    windows: pd.DataFrame
    event_outcomes: pd.DataFrame
    quantiles: QuantileAnalysisResult
    outcome_column: str


@dataclass(frozen=True)
class PeadCalendarTimeInferenceConfig:
    """Configuration for the bounded M1B calendar-time PEAD estimator."""

    quantiles: int = 5
    low_quantile: int = 1
    high_quantile: int = 5
    start_day: int = 1
    end_day: int = 60
    minimum_finite_per_leg: int = 10
    hac_maxlags: int = 59
    bootstrap_expected_block_length: int = 60
    bootstrap_replications: int = 10_000
    bootstrap_seed: int = 20260621
    bootstrap_max_batch_size: int = 256


@dataclass(frozen=True)
class PeadCalendarTimeInferenceResult:
    assignments: pd.DataFrame
    exposures: pd.DataFrame
    daily_portfolio: pd.DataFrame
    session_coverage: dict[str, object]
    daily_summary: dict[str, object]
    primary_inference: dict[str, object]
    missingness_sensitivity: dict[str, object]
    robustness: dict[str, object]


def _validate_config(config: PeadEventStudyConfig) -> None:
    integer_fields = {
        "start_day": config.start_day,
        "end_day": config.end_day,
        "quantiles": config.quantiles,
        "hac_maxlags": config.hac_maxlags,
    }
    if config.min_events_per_cohort is not None:
        integer_fields["min_events_per_cohort"] = config.min_events_per_cohort
    for field, value in integer_fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{field} must be an integer")
    if not isinstance(config.require_complete_window, bool):
        raise TypeError("require_complete_window must be a boolean")
    if config.require_complete_window is not True:
        raise ValueError("Partial-window event analysis is not implemented; require_complete_window must be True")
    if not isinstance(config.allow_ex_post_cohorts, bool):
        raise TypeError("allow_ex_post_cohorts must be a boolean")
    if config.start_day < 1:
        raise ValueError("start_day must be >= 1 so the event date is never included")
    if config.end_day < config.start_day:
        raise ValueError("end_day must be >= start_day")
    if config.quantiles < 2:
        raise ValueError("quantiles must be >= 2")
    if config.min_events_per_cohort is not None and config.min_events_per_cohort < config.quantiles:
        raise ValueError("min_events_per_cohort must be >= quantiles")
    if config.hac_maxlags < 0:
        raise ValueError("hac_maxlags must be >= 0")
    frequency = str(config.cohort_frequency).upper()
    if frequency != "D" and not config.allow_ex_post_cohorts:
        raise ValueError("cohort_frequency must be 'D' unless allow_ex_post_cohorts=True")
    if config.benchmark_return_column is not None:
        benchmark = str(config.benchmark_return_column).strip()
        if not benchmark:
            raise ValueError("benchmark_return_column must be a non-empty column name or None")
        if benchmark in RESERVED_BENCHMARK_COLUMNS:
            raise ValueError(f"benchmark_return_column collides with reserved column: {benchmark}")


def _require_columns(frame: pd.DataFrame, required: frozenset[str], frame_name: str) -> None:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"{frame_name} must be a pandas DataFrame")
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{frame_name} missing required columns: {missing}")


def _normalize_dates(values: pd.Series, column_name: str) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values):
        raise ValueError(f"{column_name} must be date-like, not numeric epoch values")
    raw = pd.Series(values)
    numeric_like = raw.dropna().map(lambda value: isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool))
    if bool(numeric_like.any()):
        raise ValueError(f"{column_name} must be date-like, not numeric epoch values")
    timezone_aware = raw.dropna().map(lambda value: isinstance(value, pd.Timestamp) and value.tzinfo is not None)
    timezone_strings = raw.dropna().astype(str).str.strip().str.lower().map(
        lambda value: bool(TIMEZONE_TOKEN_RE.search(value))
    )
    if bool(timezone_aware.any()) or bool(timezone_strings.any()):
        raise ValueError(f"{column_name} must use date-only values without timezone offsets")

    parsed = pd.to_datetime(values, errors="coerce")
    bad = int(parsed.isna().sum())
    if bad:
        raise ValueError(f"{column_name} contains {bad} non-coercible/null date values")
    return parsed.dt.normalize()


def _require_strict_bool_series(values: pd.Series, column_name: str) -> pd.Series:
    if not (pd.api.types.is_bool_dtype(values) or str(values.dtype) == "boolean"):
        raise ValueError(f"{column_name} must contain strict boolean values")
    if values.isna().any():
        raise ValueError(f"{column_name} must not contain null boolean values")
    return values.astype(bool)


def _normalize_events(events: pd.DataFrame) -> pd.DataFrame:
    _require_columns(events, EVENT_REQUIRED_COLUMNS, "events")
    out = events.copy()
    if out["event_id"].isna().any():
        raise ValueError("events.event_id must be non-null")
    if out["issuer_id"].isna().any():
        raise ValueError("events.issuer_id must be non-null")
    if out["security_id"].isna().any():
        raise ValueError("events.security_id must be non-null")

    out["event_id"] = out["event_id"].astype("string")
    out["issuer_id"] = out["issuer_id"].astype("string")
    out["security_id"] = out["security_id"].astype("string")
    out["event_date"] = _normalize_dates(out["event_date"], "events.event_date")
    out["is_primary_security"] = _require_strict_bool_series(
        out["is_primary_security"], "events.is_primary_security"
    )
    if not out["is_primary_security"].all():
        raise ValueError("events must contain only upstream-selected primary securities")
    out["sue"] = pd.to_numeric(out["sue"], errors="coerce")
    invalid_sue = out["sue"].isna() | ~np.isfinite(out["sue"])
    if invalid_sue.any():
        raise ValueError(f"events.sue contains {int(invalid_sue.sum())} non-finite values")
    if out["event_id"].duplicated().any():
        raise ValueError("events.event_id must be unique")
    if out.duplicated(["issuer_id", "event_date"]).any():
        raise ValueError("events must be unique by issuer_id,event_date after primary-security handoff")

    out["_event_order"] = np.arange(len(out), dtype=np.int64)
    return out


def _normalize_returns(
    returns: pd.DataFrame,
    config: PeadEventStudyConfig,
) -> pd.DataFrame:
    required = set(RETURN_REQUIRED_COLUMNS)
    if config.benchmark_return_column is not None:
        required.add(config.benchmark_return_column)
    _require_columns(returns, frozenset(required), "returns")

    out = returns.copy()
    if out["security_id"].isna().any():
        raise ValueError("returns.security_id must be non-null")
    out["security_id"] = out["security_id"].astype("string")
    out["date"] = _normalize_dates(out["date"], "returns.date")
    if out.duplicated(["security_id", "date"]).any():
        raise ValueError("returns must be unique by security_id,date")

    numeric_columns = ["total_return"]
    if config.benchmark_return_column is not None:
        numeric_columns.append(config.benchmark_return_column)
    for column in numeric_columns:
        out[column] = pd.to_numeric(out[column], errors="coerce")
        infinite = out[column].map(np.isinf)
        if infinite.any():
            raise ValueError(f"returns.{column} contains {int(infinite.sum())} infinite values")
        below_floor = out[column] < -1.0
        if below_floor.any():
            raise ValueError(f"returns.{column} contains values below -100%")

    out = out.sort_values(["security_id", "date"], kind="mergesort").reset_index(drop=True)
    return out


def _normalize_market_sessions(market_sessions: Iterable[object] | pd.DataFrame | pd.Series) -> pd.DataFrame:
    if market_sessions is None:
        raise ValueError("market_sessions is required for exact event-day semantics")
    if isinstance(market_sessions, pd.DataFrame):
        if "date" not in market_sessions.columns:
            raise ValueError("market_sessions DataFrame must contain a date column")
        raw = market_sessions["date"]
    else:
        raw = pd.Series(list(market_sessions) if not isinstance(market_sessions, pd.Series) else market_sessions)
    sessions = pd.DataFrame({"return_date": _normalize_dates(raw, "market_sessions.date")})
    sessions = sessions.drop_duplicates().sort_values("return_date", kind="mergesort").reset_index(drop=True)
    if sessions.empty:
        raise ValueError("market_sessions must contain at least one date")
    sessions["_session_seq"] = np.arange(len(sessions), dtype=np.int64).astype("int64")
    return sessions


def build_event_windows(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    market_sessions: Iterable[object] | pd.DataFrame | pd.Series,
    config: PeadEventStudyConfig | None = None,
) -> pd.DataFrame:
    """Build strict post-event trading-day windows without including event day.

    Day ``+1`` is the first market session strictly after ``event_date``.  The
    returned frame always contains one skeleton row per requested market-session
    day, so security-specific missing rows remain visible and force
    ``window_complete=False``.
    """

    cfg = config or PeadEventStudyConfig()
    _validate_config(cfg)
    event_frame = _normalize_events(events)
    return_frame = _normalize_returns(returns, cfg)
    session_frame = _normalize_market_sessions(market_sessions)

    if event_frame.empty:
        return pd.DataFrame(
            columns=[
                *events.columns,
                "event_day",
                "return_date",
                "asset_return",
                "benchmark_return",
                "abnormal_return",
                "return_observations",
                "benchmark_observations",
                "window_complete",
            ]
        )

    left = event_frame.sort_values(["event_date", "issuer_id", "security_id"], kind="mergesort")
    right = session_frame.sort_values("return_date", kind="mergesort")
    starts = pd.merge_asof(
        left,
        right,
        left_on="event_date",
        right_on="return_date",
        direction="forward",
        allow_exact_matches=False,
    ).rename(columns={"return_date": "first_return_date", "_session_seq": "_start_session_seq"})

    horizon = pd.DataFrame(
        {"event_day": np.arange(cfg.start_day, cfg.end_day + 1, dtype=np.int64)}
    )
    expanded = starts.merge(horizon, how="cross")
    expanded["_session_seq"] = (
        expanded["_start_session_seq"] + expanded["event_day"] - 1
    ).astype("Int64")
    expanded = expanded.merge(
        session_frame,
        on="_session_seq",
        how="left",
        validate="many_to_one",
    )

    return_columns = ["security_id", "date", "total_return"]
    if cfg.benchmark_return_column is not None:
        return_columns.append(cfg.benchmark_return_column)
    observations = return_frame[return_columns].rename(
        columns={
            "date": "return_date",
            "total_return": "asset_return",
            **(
                {cfg.benchmark_return_column: "benchmark_return"}
                if cfg.benchmark_return_column is not None
                else {}
            ),
        }
    )
    out = expanded.merge(
        observations,
        on=["security_id", "return_date"],
        how="left",
        validate="many_to_one",
    )
    if "benchmark_return" not in out.columns:
        out["benchmark_return"] = np.nan
    out["abnormal_return"] = (
        out["asset_return"] - out["benchmark_return"]
        if cfg.benchmark_return_column is not None
        else np.nan
    )

    grouped = out.groupby("event_id", sort=False)
    out["return_observations"] = grouped["asset_return"].transform("count").astype("int64")
    out["calendar_observations"] = grouped["return_date"].transform("count").astype("int64")
    if cfg.benchmark_return_column is not None:
        out["benchmark_observations"] = grouped["benchmark_return"].transform("count").astype("int64")
    else:
        out["benchmark_observations"] = 0

    complete = (
        out["calendar_observations"].eq(cfg.expected_observations)
        & out["return_observations"].eq(cfg.expected_observations)
    )
    if cfg.benchmark_return_column is not None:
        complete &= out["benchmark_observations"].eq(cfg.expected_observations)
    out["window_complete"] = complete.astype(bool)

    out = out.sort_values(["_event_order", "event_day"], kind="mergesort").reset_index(drop=True)
    return out.drop(columns=["_event_order", "_start_session_seq", "_session_seq"])


def summarize_event_windows(
    windows: pd.DataFrame,
    config: PeadEventStudyConfig | None = None,
) -> pd.DataFrame:
    """Collapse event-day observations into complete-window return outcomes."""

    cfg = config or PeadEventStudyConfig()
    _validate_config(cfg)
    required = frozenset(
        {
            "event_id",
            "issuer_id",
            "security_id",
            "event_date",
            "event_day",
            "sue",
            "asset_return",
            "benchmark_return",
            "abnormal_return",
            "return_date",
            "window_complete",
        }
    )
    _require_columns(windows, required, "windows")
    if windows.empty:
        return pd.DataFrame(
            columns=[
                "event_id",
                "issuer_id",
                "security_id",
                "event_date",
                "sue",
                "window_complete",
                "cumulative_total_return",
                "car",
                "bhar",
                "eligible_for_analysis",
                "coverage_reason",
            ]
        )

    window_frame = windows.copy()
    window_frame["window_complete"] = _require_strict_bool_series(
        window_frame["window_complete"], "windows.window_complete"
    )
    numeric_day = pd.to_numeric(window_frame["event_day"], errors="coerce")
    if numeric_day.isna().any() or not np.all(np.mod(numeric_day.to_numpy(dtype=float), 1.0) == 0.0):
        raise ValueError("windows.event_day must contain integer event-day values")
    window_frame["event_day"] = numeric_day.astype("int64")
    if window_frame.duplicated(["event_id", "event_day"]).any():
        raise ValueError("windows must be unique by event_id,event_day")

    grouped_days = window_frame.groupby("event_id", sort=False)["event_day"]
    malformed = (
        grouped_days.count().ne(cfg.expected_observations)
        | grouped_days.nunique().ne(cfg.expected_observations)
        | grouped_days.min().ne(cfg.start_day)
        | grouped_days.max().ne(cfg.end_day)
    )
    if malformed.any():
        raise ValueError("windows must contain the exact configured event-day skeleton per event")

    grouped = window_frame.groupby("event_id", sort=False)
    base = grouped[["issuer_id", "security_id", "event_date", "sue"]].first()
    base["return_observations"] = grouped["asset_return"].count().astype("int64")
    base["calendar_observations"] = grouped["return_date"].count().astype("int64")
    base["benchmark_observations"] = grouped["benchmark_return"].count().astype("int64")
    base["window_complete"] = grouped["window_complete"].all().astype(bool)

    asset_growth = (1.0 + window_frame["asset_return"]).groupby(window_frame["event_id"], sort=False)
    base["cumulative_total_return"] = asset_growth.prod(
        min_count=cfg.expected_observations
    ) - 1.0

    if cfg.benchmark_return_column is not None:
        benchmark_growth = (1.0 + window_frame["benchmark_return"]).groupby(
            window_frame["event_id"], sort=False
        )
        base["cumulative_benchmark_return"] = benchmark_growth.prod(
            min_count=cfg.expected_observations
        ) - 1.0
        base["car"] = window_frame["abnormal_return"].groupby(
            window_frame["event_id"], sort=False
        ).sum(min_count=cfg.expected_observations)
        base["bhar"] = base["cumulative_total_return"] - base["cumulative_benchmark_return"]
    else:
        base["cumulative_benchmark_return"] = np.nan
        base["car"] = np.nan
        base["bhar"] = np.nan

    asset_window_complete = (
        base["calendar_observations"].eq(cfg.expected_observations)
        & base["return_observations"].eq(cfg.expected_observations)
    )
    benchmark_window_complete = (
        base["benchmark_observations"].eq(cfg.expected_observations)
        if cfg.benchmark_return_column is not None
        else pd.Series(False, index=base.index)
    )
    if cfg.require_complete_window:
        base.loc[~asset_window_complete, "cumulative_total_return"] = np.nan
        benchmark_metric_columns = ["cumulative_benchmark_return", "car", "bhar"]
        base.loc[
            ~(asset_window_complete & benchmark_window_complete),
            benchmark_metric_columns,
        ] = np.nan

    base["eligible_for_analysis"] = (
        base["window_complete"]
        & base["sue"].map(np.isfinite)
        & base["cumulative_total_return"].map(np.isfinite)
    )
    base["coverage_reason"] = np.select(
        [
            base["calendar_observations"].lt(cfg.expected_observations),
            base["return_observations"].lt(cfg.expected_observations),
            (
                base["benchmark_observations"].lt(cfg.expected_observations)
                if cfg.benchmark_return_column is not None
                else pd.Series(False, index=base.index)
            ),
        ],
        ["insufficient_future_sessions", "missing_asset_return", "missing_benchmark_return"],
        default="complete",
    )
    return base.reset_index()


def assign_signal_quantiles(
    event_outcomes: pd.DataFrame,
    outcome_column: str,
    config: PeadEventStudyConfig | None = None,
) -> pd.DataFrame:
    """Assign SUE quantiles inside explicit event-date cohorts.

    Tied SUE values receive the same percentile rank and therefore the same
    quantile.  Cohorts smaller than the configured minimum remain unassigned.
    """

    cfg = config or PeadEventStudyConfig()
    _validate_config(cfg)
    required = frozenset(
        {"event_id", "event_date", "sue", "window_complete", outcome_column}
    )
    _require_columns(event_outcomes, required, "event_outcomes")
    out = event_outcomes.copy()
    out["event_date"] = _normalize_dates(out["event_date"], "event_outcomes.event_date")
    out["window_complete"] = _require_strict_bool_series(
        out["window_complete"], "event_outcomes.window_complete"
    )
    out[outcome_column] = pd.to_numeric(out[outcome_column], errors="coerce")
    out["sue"] = pd.to_numeric(out["sue"], errors="coerce")
    out["cohort"] = out["event_date"].dt.to_period(cfg.cohort_frequency).astype("string")

    signal_eligible = out["sue"].map(np.isfinite)
    cohort_size = signal_eligible.groupby(out["cohort"], sort=False).transform("sum").astype("int64")
    minimum = cfg.min_events_per_cohort or cfg.quantiles
    bucket_eligible = signal_eligible & cohort_size.ge(minimum)

    percentile = out.loc[bucket_eligible].groupby("cohort", sort=False)["sue"].rank(
        method="average", pct=True
    )
    assigned = np.ceil(percentile * cfg.quantiles).clip(1, cfg.quantiles).astype("Int64")
    out["signal_quantile"] = pd.Series(pd.NA, index=out.index, dtype="Int64")
    out.loc[bucket_eligible, "signal_quantile"] = assigned
    out["cohort_event_count"] = cohort_size
    outcome_eligible = out["window_complete"] & out[outcome_column].map(np.isfinite)
    out["signal_bucket_eligible"] = bucket_eligible
    out["quantile_eligible"] = bucket_eligible & outcome_eligible
    return out


def _hac_mean_statistics(values: pd.Series, maxlags: int) -> dict[str, float | int]:
    clean = pd.to_numeric(values, errors="coerce")
    gap_count = int(clean.isna().sum())
    if gap_count:
        finite = clean[np.isfinite(clean)].astype(float)
        return {
            "n_cohorts": int(len(finite)),
            "mean_high_minus_low": float(finite.mean()) if len(finite) else float("nan"),
            "hac_standard_error": float("nan"),
            "hac_t_stat": float("nan"),
            "hac_maxlags_used": 0,
            "hac_gap_count": gap_count,
        }
    clean = clean[np.isfinite(clean)].astype(float)
    n = int(len(clean))
    mean = float(clean.mean()) if n else float("nan")
    if n < 2:
        return {
            "n_cohorts": n,
            "mean_high_minus_low": mean,
            "hac_standard_error": float("nan"),
            "hac_t_stat": float("nan"),
            "hac_maxlags_used": 0,
            "hac_gap_count": 0,
        }

    lags = min(int(maxlags), n - 1)
    fit = sm.OLS(clean.to_numpy(), np.ones((n, 1), dtype=float)).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": lags, "use_correction": True},
    )
    standard_error = float(fit.bse[0])
    t_stat = float(fit.tvalues[0]) if standard_error > 0.0 else float("nan")
    return {
        "n_cohorts": n,
        "mean_high_minus_low": mean,
        "hac_standard_error": standard_error,
        "hac_t_stat": t_stat,
        "hac_maxlags_used": lags,
        "hac_gap_count": 0,
    }


def _validate_calendar_time_config(config: PeadCalendarTimeInferenceConfig) -> None:
    integer_fields = {
        "quantiles": config.quantiles,
        "low_quantile": config.low_quantile,
        "high_quantile": config.high_quantile,
        "start_day": config.start_day,
        "end_day": config.end_day,
        "minimum_finite_per_leg": config.minimum_finite_per_leg,
        "hac_maxlags": config.hac_maxlags,
        "bootstrap_expected_block_length": config.bootstrap_expected_block_length,
        "bootstrap_replications": config.bootstrap_replications,
        "bootstrap_seed": config.bootstrap_seed,
        "bootstrap_max_batch_size": config.bootstrap_max_batch_size,
    }
    for field, value in integer_fields.items():
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{field} must be an integer")
    if config.quantiles < 2:
        raise ValueError("quantiles must be >= 2")
    if not (1 <= config.low_quantile < config.high_quantile <= config.quantiles):
        raise ValueError("low/high quantiles must be ordered within quantiles")
    if config.start_day != 1 or config.end_day != 60:
        raise ValueError("calendar-time PEAD inference requires the locked +1..+60 window")
    if config.minimum_finite_per_leg < 1:
        raise ValueError("minimum_finite_per_leg must be positive")
    if config.hac_maxlags != 59:
        raise ValueError("calendar-time PEAD inference requires HAC maxlags=59")
    if config.bootstrap_expected_block_length < 1:
        raise ValueError("bootstrap_expected_block_length must be positive")
    if config.bootstrap_replications < 1:
        raise ValueError("bootstrap_replications must be positive")
    if config.bootstrap_max_batch_size < 1:
        raise ValueError("bootstrap_max_batch_size must be positive")


def _calendar_time_null_regression(
    observations: int,
    failure_reasons: list[str],
    *,
    include_p_value: bool,
    hac_maxlags: int,
) -> dict[str, object]:
    output: dict[str, object] = {
        "status": "null",
        "dependent_variable": "R_HL",
        "regressor": "mktrf",
        "observations": int(observations),
        "alpha_ct": None,
        "beta_m": None,
        "alpha_hac_standard_error": None,
        "alpha_hac_t_stat": None,
        "hac_maxlags_requested": int(hac_maxlags),
        "hac_maxlags_used": 0,
        "use_correction": True,
        "failure_reasons": sorted(set(failure_reasons)),
    }
    if include_p_value:
        output["alpha_hac_two_sided_p_value"] = None
    return output


def _calendar_time_regression(
    daily: pd.DataFrame,
    config: PeadCalendarTimeInferenceConfig,
    *,
    internal_gap_count: int,
    include_p_value: bool,
) -> dict[str, object]:
    required = frozenset({"R_HL", "mktrf"})
    _require_columns(daily, required, "daily calendar-time portfolio")
    clean = daily[["R_HL", "mktrf"]].copy()
    clean["R_HL"] = pd.to_numeric(clean["R_HL"], errors="coerce")
    clean["mktrf"] = pd.to_numeric(clean["mktrf"], errors="coerce")
    complete = clean[np.isfinite(clean["R_HL"]) & np.isfinite(clean["mktrf"])]
    reasons: list[str] = []
    if internal_gap_count:
        reasons.append("internal_minimum_leg_count_gap")
    if len(clean) < 60:
        reasons.append("fewer_than_60_retained_sessions")
    if len(complete) != len(clean):
        reasons.append("non_finite_daily_regression_pair")
    if reasons:
        return _calendar_time_null_regression(
            len(complete),
            reasons,
            include_p_value=include_p_value,
            hac_maxlags=config.hac_maxlags,
        )

    y = complete["R_HL"].to_numpy(dtype=float)
    x = complete["mktrf"].to_numpy(dtype=float)
    design = sm.add_constant(x, has_constant="add")
    if np.linalg.matrix_rank(design) != 2:
        return _calendar_time_null_regression(
            len(complete),
            ["rank_deficient_regression"],
            include_p_value=include_p_value,
            hac_maxlags=config.hac_maxlags,
        )
    fit = sm.OLS(y, design).fit(
        cov_type="HAC",
        cov_kwds={"maxlags": int(config.hac_maxlags), "use_correction": True},
    )
    output = {
        "status": "valid",
        "dependent_variable": "R_HL",
        "regressor": "mktrf",
        "observations": int(len(complete)),
        "alpha_ct": float(fit.params[0]),
        "beta_m": float(fit.params[1]),
        "alpha_hac_standard_error": float(fit.bse[0]),
        "alpha_hac_t_stat": float(fit.tvalues[0]),
        "hac_maxlags_requested": int(config.hac_maxlags),
        "hac_maxlags_used": int(config.hac_maxlags),
        "use_correction": True,
        "failure_reasons": [],
    }
    if include_p_value:
        output["alpha_hac_two_sided_p_value"] = float(fit.pvalues[0])
    return output


def _return_summary(values: pd.Series) -> dict[str, object]:
    clean = pd.to_numeric(values, errors="coerce")
    clean = clean[np.isfinite(clean)]
    standard_deviation = (
        float(clean.std(ddof=1)) if len(clean) > 1 else (0.0 if len(clean) == 1 else None)
    )
    return {
        "observations": int(len(clean)),
        "mean": float(clean.mean()) if len(clean) else None,
        "standard_deviation": standard_deviation,
        "minimum": float(clean.min()) if len(clean) else None,
        "maximum": float(clean.max()) if len(clean) else None,
    }


def _leg_count_record(expected: int, finite: int) -> dict[str, object]:
    missing = int(expected - finite)
    return {
        "expected": int(expected),
        "finite": int(finite),
        "missing": missing,
        "missing_rate": float(missing / expected) if expected else 0.0,
    }


def _daily_leg_summary(daily: pd.DataFrame, prefix: str) -> dict[str, object]:
    expected = int(daily[f"{prefix}_expected"].sum())
    finite = int(daily[f"{prefix}_finite"].sum())
    missing = int(daily[f"{prefix}_missing"].sum())
    return {
        "minimum_finite": int(daily[f"{prefix}_finite"].min()) if len(daily) else 0,
        "median_finite": float(daily[f"{prefix}_finite"].median()) if len(daily) else 0.0,
        "maximum_finite": int(daily[f"{prefix}_finite"].max()) if len(daily) else 0,
        "total_expected": expected,
        "total_finite": finite,
        "total_missing": missing,
        "missing_rate": float(missing / expected) if expected else 0.0,
    }


def _ols_alpha_from_arrays(y: np.ndarray, x: np.ndarray) -> float:
    n = int(len(y))
    if n < 2:
        return float("nan")
    sx = float(x.sum())
    sy = float(y.sum())
    sxx = float(np.dot(x, x))
    sxy = float(np.dot(x, y))
    denominator = (n * sxx) - (sx * sx)
    if not np.isfinite(denominator) or denominator <= 0.0:
        return float("nan")
    beta = ((n * sxy) - (sx * sy)) / denominator
    alpha = (sy - (beta * sx)) / n
    return float(alpha) if np.isfinite(alpha) else float("nan")


def _stationary_bootstrap_indices(
    n: int,
    rng: np.random.Generator,
    expected_block_length: int,
) -> np.ndarray:
    indices = np.empty(n, dtype=np.int64)
    position = 0
    restart_probability = 1.0 / float(expected_block_length)
    while position < n:
        start = int(rng.integers(0, n))
        block = int(rng.geometric(restart_probability))
        take = min(block, n - position)
        indices[position : position + take] = (start + np.arange(take, dtype=np.int64)) % n
        position += take
    return indices


def _bootstrap_alpha_samples(
    y: np.ndarray,
    x: np.ndarray,
    config: PeadCalendarTimeInferenceConfig,
    rng: np.random.Generator,
) -> tuple[np.ndarray, int]:
    samples = np.empty(int(config.bootstrap_replications), dtype=float)
    invalid = 0
    offset = 0
    while offset < int(config.bootstrap_replications):
        batch = min(int(config.bootstrap_max_batch_size), int(config.bootstrap_replications) - offset)
        for index in range(batch):
            sample_indices = _stationary_bootstrap_indices(
                len(y),
                rng,
                int(config.bootstrap_expected_block_length),
            )
            alpha = _ols_alpha_from_arrays(y[sample_indices], x[sample_indices])
            if not np.isfinite(alpha):
                invalid += 1
            samples[offset + index] = alpha
        offset += batch
    return samples, invalid


def _calendar_time_robustness(
    daily: pd.DataFrame,
    primary: dict[str, object],
    config: PeadCalendarTimeInferenceConfig,
) -> dict[str, object]:
    base = {
        "method_id": "paired_stationary_block_bootstrap_alpha_ct_v1",
        "expected_block_length": int(config.bootstrap_expected_block_length),
        "replications": int(config.bootstrap_replications),
        "seed": int(config.bootstrap_seed),
        "interval_level": 0.95,
        "max_batch_size": int(config.bootstrap_max_batch_size),
    }
    if primary.get("status") != "valid":
        return {
            "status": "null",
            **base,
            "alpha_percentile_lower": None,
            "alpha_percentile_upper": None,
            "alpha_centered_null_two_sided_p_value": None,
            "invalid_replications": 0,
            "failure_reasons": ["primary_inference_null"],
        }
    clean = daily[["R_HL", "mktrf"]].copy()
    clean["R_HL"] = pd.to_numeric(clean["R_HL"], errors="coerce")
    clean["mktrf"] = pd.to_numeric(clean["mktrf"], errors="coerce")
    clean = clean[np.isfinite(clean["R_HL"]) & np.isfinite(clean["mktrf"])]
    y = clean["R_HL"].to_numpy(dtype=float)
    x = clean["mktrf"].to_numpy(dtype=float)
    rng = np.random.default_rng(int(config.bootstrap_seed))
    alpha_samples, invalid = _bootstrap_alpha_samples(y, x, config, rng)
    observed_alpha = float(primary["alpha_ct"])
    centered_y = y - observed_alpha
    null_samples, null_invalid = _bootstrap_alpha_samples(centered_y, x, config, rng)
    invalid_total = int(invalid + null_invalid)
    if invalid_total:
        return {
            "status": "null",
            **base,
            "alpha_percentile_lower": None,
            "alpha_percentile_upper": None,
            "alpha_centered_null_two_sided_p_value": None,
            "invalid_replications": invalid_total,
            "failure_reasons": ["invalid_bootstrap_replication"],
        }
    p_value = (1 + int((np.abs(null_samples) >= abs(observed_alpha)).sum())) / (
        int(config.bootstrap_replications) + 1
    )
    return {
        "status": "valid",
        **base,
        "alpha_percentile_lower": float(np.percentile(alpha_samples, 2.5)),
        "alpha_percentile_upper": float(np.percentile(alpha_samples, 97.5)),
        "alpha_centered_null_two_sided_p_value": float(p_value),
        "invalid_replications": 0,
        "failure_reasons": [],
    }


def build_calendar_time_inference(
    windows: pd.DataFrame,
    factors: pd.DataFrame,
    config: PeadCalendarTimeInferenceConfig | None = None,
    *,
    _include_sensitivity: bool = True,
    _include_robustness: bool = True,
) -> PeadCalendarTimeInferenceResult:
    """Build the bounded daily calendar-time Q5-minus-Q1 PEAD inference result."""

    cfg = config or PeadCalendarTimeInferenceConfig()
    _validate_calendar_time_config(cfg)
    required_windows = frozenset(
        {
            "event_id",
            "security_id",
            "event_date",
            "event_day",
            "return_date",
            "sue",
            "asset_return",
            "window_complete",
        }
    )
    _require_columns(windows, required_windows, "calendar-time windows")
    _require_columns(factors, frozenset({"return_date", "mktrf"}), "calendar-time factors")

    frame = windows.copy()
    frame["event_id"] = frame["event_id"].astype("string")
    frame["security_id"] = frame["security_id"].astype("string")
    frame["event_date"] = _normalize_dates(frame["event_date"], "windows.event_date")
    nullable_return_dates = pd.to_datetime(frame["return_date"], errors="coerce")
    frame["return_date"] = nullable_return_dates.dt.normalize()
    frame["sue"] = pd.to_numeric(frame["sue"], errors="coerce")
    frame["asset_return"] = pd.to_numeric(frame["asset_return"], errors="coerce")
    frame["window_complete"] = _require_strict_bool_series(
        frame["window_complete"], "windows.window_complete"
    )
    frame["event_day"] = pd.to_numeric(frame["event_day"], errors="coerce").astype("Int64")

    event_inputs = (
        frame.sort_values(["event_id", "event_day"], kind="mergesort")
        .groupby("event_id", sort=False, observed=True)
        .first()
        .reset_index()[["event_id", "event_date", "sue", "window_complete"]]
    )
    event_inputs["calendar_time_signal_placeholder"] = 0.0
    signal_config = PeadEventStudyConfig(
        start_day=cfg.start_day,
        end_day=cfg.end_day,
        quantiles=cfg.quantiles,
    )
    assignments = assign_signal_quantiles(
        event_inputs,
        "calendar_time_signal_placeholder",
        signal_config,
    )[["event_id", "signal_bucket_eligible", "signal_quantile"]]

    active = frame.merge(assignments, on="event_id", how="left", validate="many_to_one")
    active["signal_bucket_eligible"] = active["signal_bucket_eligible"].fillna(False).astype(bool)
    active = active.loc[active["signal_bucket_eligible"]].copy()
    null_return_date_rows_excluded = int(active["return_date"].isna().sum())
    active = active.loc[active["return_date"].notna()].copy()

    with_security = active.loc[active["security_id"].notna()].copy()
    no_security = active.loc[active["security_id"].isna()].copy()
    key = ["security_id", "return_date"]
    latest_event_ambiguity_cells = 0
    if with_security.empty:
        latest = with_security.copy()
    else:
        with_security["_latest_event_date"] = with_security.groupby(
            key, sort=False, observed=True
        )["event_date"].transform("max")
        latest = with_security.loc[
            with_security["event_date"].eq(with_security["_latest_event_date"])
        ].copy()
        ambiguity = (
            latest.groupby(key, sort=False, observed=True)["event_id"]
            .nunique()
            .reset_index(name="event_ids")
        )
        ambiguous_keys = ambiguity.loc[ambiguity["event_ids"].gt(1), key]
        latest_event_ambiguity_cells = int(len(ambiguous_keys))
        if latest_event_ambiguity_cells:
            latest = latest.merge(
                ambiguous_keys.assign(_ambiguous_latest=True),
                on=key,
                how="left",
            )
            latest = latest.loc[latest["_ambiguous_latest"].ne(True)].copy()
        if latest.duplicated(key).any():
            raise ValueError("latest-event overlap resolution did not produce unique security/date rows")

    extreme_quantiles = {int(cfg.low_quantile), int(cfg.high_quantile)}
    resolved_extreme = latest.loc[latest["signal_quantile"].isin(extreme_quantiles)].copy()
    unresolved_extreme = no_security.loc[no_security["signal_quantile"].isin(extreme_quantiles)].copy()
    exposures = pd.concat([resolved_extreme, unresolved_extreme], ignore_index=True, sort=False)
    exposures["finite_asset_return"] = (
        exposures["security_id"].notna() & np.isfinite(exposures["asset_return"])
    )
    exposures["leg"] = np.where(
        exposures["signal_quantile"].astype("int64").eq(int(cfg.low_quantile)),
        "q1",
        "q5",
    )

    factor_frame = factors[["return_date", "mktrf"]].copy()
    factor_frame["return_date"] = _normalize_dates(factor_frame["return_date"], "factors.return_date")
    factor_frame["mktrf"] = pd.to_numeric(factor_frame["mktrf"], errors="coerce")
    if factor_frame["return_date"].duplicated().any():
        raise ValueError("factors.return_date must be unique")
    if not np.isfinite(factor_frame["mktrf"]).all():
        raise ValueError("factors.mktrf must be finite")
    factor_frame = factor_frame.sort_values("return_date", kind="mergesort").reset_index(drop=True)

    daily = factor_frame.copy()
    for leg_name, quantile in (("q1", cfg.low_quantile), ("q5", cfg.high_quantile)):
        leg_rows = exposures.loc[exposures["signal_quantile"].eq(int(quantile))].copy()
        if leg_rows.empty:
            leg_daily = pd.DataFrame(
                columns=[
                    "return_date",
                    f"{leg_name}_expected",
                    f"{leg_name}_finite",
                    f"{leg_name}_missing",
                    f"{leg_name}_return",
                ]
            )
        else:
            finite_rows = leg_rows.loc[leg_rows["finite_asset_return"]].copy()
            counts = leg_rows.groupby("return_date", sort=False, observed=True).size().rename(
                f"{leg_name}_expected"
            )
            finite_counts = (
                finite_rows.groupby("return_date", sort=False, observed=True)["security_id"]
                .nunique()
                .rename(f"{leg_name}_finite")
            )
            returns = (
                finite_rows.groupby("return_date", sort=False, observed=True)["asset_return"]
                .mean()
                .rename(f"{leg_name}_return")
            )
            leg_daily = pd.concat([counts, finite_counts, returns], axis=1).reset_index()
            leg_daily[f"{leg_name}_finite"] = leg_daily[f"{leg_name}_finite"].fillna(0)
            leg_daily[f"{leg_name}_missing"] = (
                leg_daily[f"{leg_name}_expected"] - leg_daily[f"{leg_name}_finite"]
            )
        daily = daily.merge(leg_daily, on="return_date", how="left", validate="one_to_one")
        for column in (f"{leg_name}_expected", f"{leg_name}_finite", f"{leg_name}_missing"):
            daily[column] = daily[column].fillna(0).astype("int64")

    q1_valid = daily["q1_finite"].ge(int(cfg.minimum_finite_per_leg))
    q5_valid = daily["q5_finite"].ge(int(cfg.minimum_finite_per_leg))
    count_valid = q1_valid & q5_valid
    if bool(count_valid.any()):
        first_retained = daily.loc[count_valid, "return_date"].iloc[0]
        last_retained = daily.loc[count_valid, "return_date"].iloc[-1]
        retained_mask = daily["return_date"].between(first_retained, last_retained)
        retained = daily.loc[retained_mask].copy()
    else:
        first_retained = pd.NaT
        last_retained = pd.NaT
        retained = daily.iloc[0:0].copy()
    internal_valid = retained["q1_finite"].ge(int(cfg.minimum_finite_per_leg)) & retained[
        "q5_finite"
    ].ge(int(cfg.minimum_finite_per_leg))
    internal_gap_count = int((~internal_valid).sum())
    retained["R_HL"] = retained["q5_return"] - retained["q1_return"]

    q1_expected = int(exposures.loc[exposures["signal_quantile"].eq(int(cfg.low_quantile))].shape[0])
    q1_finite = int(
        exposures.loc[
            exposures["signal_quantile"].eq(int(cfg.low_quantile)) & exposures["finite_asset_return"]
        ].shape[0]
    )
    q5_expected = int(exposures.loc[exposures["signal_quantile"].eq(int(cfg.high_quantile))].shape[0])
    q5_finite = int(
        exposures.loc[
            exposures["signal_quantile"].eq(int(cfg.high_quantile)) & exposures["finite_asset_return"]
        ].shape[0]
    )
    session_coverage = {
        "authoritative_sessions": int(len(factor_frame)),
        "authoritative_date_min": factor_frame["return_date"].min().strftime("%Y-%m-%d"),
        "authoritative_date_max": factor_frame["return_date"].max().strftime("%Y-%m-%d"),
        "null_return_date_rows_excluded": null_return_date_rows_excluded,
        "retained_sessions": int(len(retained)),
        "retained_date_min": first_retained.strftime("%Y-%m-%d") if pd.notna(first_retained) else None,
        "retained_date_max": last_retained.strftime("%Y-%m-%d") if pd.notna(last_retained) else None,
        "internal_gap_count": internal_gap_count,
        "latest_event_ambiguity_cells": latest_event_ambiguity_cells,
        "extreme_expected_rows": int(q1_expected + q5_expected),
        "extreme_finite_rows": int(q1_finite + q5_finite),
        "extreme_missing_rows": int((q1_expected - q1_finite) + (q5_expected - q5_finite)),
        "q1": _leg_count_record(q1_expected, q1_finite),
        "q5": _leg_count_record(q5_expected, q5_finite),
    }
    daily_summary = {
        "sessions": int(len(retained)),
        "q1": _daily_leg_summary(retained, "q1"),
        "q5": _daily_leg_summary(retained, "q5"),
        "spread": _return_summary(retained["R_HL"] if "R_HL" in retained else pd.Series(dtype=float)),
        "factor": _return_summary(retained["mktrf"] if "mktrf" in retained else pd.Series(dtype=float)),
    }

    primary = _calendar_time_regression(
        retained,
        cfg,
        internal_gap_count=internal_gap_count,
        include_p_value=True,
    )
    complete_event_ids = set(
        event_inputs.loc[event_inputs["window_complete"], "event_id"].astype("string")
    )
    sensitivity_result = (
        build_calendar_time_inference(
            frame.loc[frame["event_id"].isin(complete_event_ids)].copy(),
            factor_frame,
            cfg,
            _include_sensitivity=False,
            _include_robustness=False,
        )
        if _include_sensitivity and len(complete_event_ids) < frame["event_id"].nunique()
        else None
    )
    if sensitivity_result is None:
        sensitivity_regression = primary.copy()
    else:
        sensitivity_regression = sensitivity_result.primary_inference.copy()
    missingness_sensitivity = {
        "ex_post_missingness_sensitivity_only": True,
        "population_rule": "complete_60_session_asset_window",
        "observations": int(sensitivity_regression["observations"]),
        "alpha_ct": sensitivity_regression["alpha_ct"],
        "beta_m": sensitivity_regression["beta_m"],
        "alpha_hac_standard_error": sensitivity_regression["alpha_hac_standard_error"],
        "alpha_hac_t_stat": sensitivity_regression["alpha_hac_t_stat"],
        "failure_reasons": list(sensitivity_regression["failure_reasons"]),
    }
    robustness = (
        _calendar_time_robustness(retained, primary, cfg)
        if _include_robustness
        else {
            "status": "null",
            "method_id": "paired_stationary_block_bootstrap_alpha_ct_v1",
            "expected_block_length": int(cfg.bootstrap_expected_block_length),
            "replications": int(cfg.bootstrap_replications),
            "seed": int(cfg.bootstrap_seed),
            "interval_level": 0.95,
            "alpha_percentile_lower": None,
            "alpha_percentile_upper": None,
            "alpha_centered_null_two_sided_p_value": None,
            "invalid_replications": 0,
            "max_batch_size": int(cfg.bootstrap_max_batch_size),
            "failure_reasons": ["robustness_not_requested"],
        }
    )

    return PeadCalendarTimeInferenceResult(
        assignments=assignments,
        exposures=exposures.sort_values(
            ["return_date", "leg", "security_id", "event_id"],
            kind="mergesort",
            na_position="last",
        ).reset_index(drop=True),
        daily_portfolio=retained.reset_index(drop=True),
        session_coverage=session_coverage,
        daily_summary=daily_summary,
        primary_inference=primary,
        missingness_sensitivity=missingness_sensitivity,
        robustness=robustness,
    )


def summarize_quantile_performance(
    event_outcomes: pd.DataFrame,
    outcome_column: str,
    config: PeadEventStudyConfig | None = None,
) -> QuantileAnalysisResult:
    """Summarize quantile outcomes and cohort-level high-minus-low HAC evidence."""

    cfg = config or PeadEventStudyConfig()
    assignments = assign_signal_quantiles(event_outcomes, outcome_column, cfg)
    eligible = assignments.loc[assignments["quantile_eligible"]].copy()

    if eligible.empty:
        quantile_summary = pd.DataFrame(
            columns=["signal_quantile", "events", "mean", "median", "std"]
        )
        cohort_spreads = pd.DataFrame(
            columns=["cohort", "low_quantile_return", "high_quantile_return", "high_minus_low"]
        )
    else:
        quantile_summary = (
            eligible.groupby("signal_quantile", observed=True)[outcome_column]
            .agg(events="count", mean="mean", median="median", std="std")
            .reset_index()
        )
        cohort_quantiles = (
            eligible.groupby(["cohort", "signal_quantile"], observed=True)[outcome_column]
            .mean()
            .unstack("signal_quantile")
        )
        period_index = pd.PeriodIndex(cohort_quantiles.index.astype(str), freq=cfg.cohort_frequency)
        full_period_index = pd.period_range(period_index.min(), period_index.max(), freq=cfg.cohort_frequency)
        cohort_quantiles.index = period_index
        cohort_quantiles = cohort_quantiles.reindex(full_period_index)
        low = cohort_quantiles.get(1, pd.Series(np.nan, index=cohort_quantiles.index))
        high = cohort_quantiles.get(
            cfg.quantiles, pd.Series(np.nan, index=cohort_quantiles.index)
        )
        cohort_spreads = pd.DataFrame(
            {
                "cohort": cohort_quantiles.index.astype(str),
                "low_quantile_return": low.to_numpy(),
                "high_quantile_return": high.to_numpy(),
            }
        )
        cohort_spreads["high_minus_low"] = (
            cohort_spreads["high_quantile_return"] - cohort_spreads["low_quantile_return"]
        )

    statistics = _hac_mean_statistics(cohort_spreads["high_minus_low"], cfg.hac_maxlags)
    statistics.update(
        {
            "outcome_column": outcome_column,
            "quantiles": int(cfg.quantiles),
            "eligible_events": int(len(eligible)),
        }
    )
    return QuantileAnalysisResult(
        assignments=assignments,
        quantile_summary=quantile_summary,
        cohort_spreads=cohort_spreads,
        spread_statistics=statistics,
    )


def run_pead_event_study(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    market_sessions: Iterable[object] | pd.DataFrame | pd.Series,
    config: PeadEventStudyConfig | None = None,
) -> PeadEventStudyResult:
    """Run the in-memory strategy contract without reading or writing data artifacts."""

    cfg = config or PeadEventStudyConfig()
    windows = build_event_windows(events, returns, market_sessions, cfg)
    outcomes = summarize_event_windows(windows, cfg)
    outcome_column = "car" if cfg.benchmark_return_column is not None else "cumulative_total_return"
    quantiles = summarize_quantile_performance(outcomes, outcome_column, cfg)
    return PeadEventStudyResult(
        windows=windows,
        event_outcomes=outcomes,
        quantiles=quantiles,
        outcome_column=outcome_column,
    )


def summarize_event_outcomes_from_inputs(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    market_sessions: Iterable[object] | pd.DataFrame | pd.Series,
    config: PeadEventStudyConfig | None = None,
    *,
    batch_size: int = 10_000,
) -> pd.DataFrame:
    """Summarize event outcomes in bounded batches without retaining all windows.

    This is the preferred large-sample path for a future 235k-event handoff.  It
    still performs no filesystem writes and does not read data artifacts.
    """

    if isinstance(batch_size, bool) or not isinstance(batch_size, (int, np.integer)):
        raise TypeError("batch_size must be an integer")
    if int(batch_size) <= 0:
        raise ValueError("batch_size must be positive")
    cfg = config or PeadEventStudyConfig()
    event_frame = _normalize_events(events)
    if event_frame.empty:
        return summarize_event_windows(
            build_event_windows(events, returns, market_sessions, cfg), cfg
        )

    outputs: list[pd.DataFrame] = []
    for start in range(0, len(event_frame), int(batch_size)):
        event_ids = event_frame.iloc[start : start + int(batch_size)]["event_id"]
        batch_events = events.loc[events["event_id"].astype("string").isin(set(event_ids))]
        windows = build_event_windows(batch_events, returns, market_sessions, cfg)
        outputs.append(summarize_event_windows(windows, cfg))
    return pd.concat(outputs, ignore_index=True) if outputs else pd.DataFrame()


__all__ = [
    "EVENT_REQUIRED_COLUMNS",
    "RETURN_REQUIRED_COLUMNS",
    "PeadEventStudyConfig",
    "PeadEventStudyResult",
    "PeadCalendarTimeInferenceConfig",
    "PeadCalendarTimeInferenceResult",
    "QuantileAnalysisResult",
    "assign_signal_quantiles",
    "build_event_windows",
    "build_calendar_time_inference",
    "run_pead_event_study",
    "summarize_event_outcomes_from_inputs",
    "summarize_event_windows",
    "summarize_quantile_performance",
]

