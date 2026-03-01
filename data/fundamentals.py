"""
Terminal Zero — PIT Fundamentals Broadcaster [FR-027]

Purpose:
  - Load sparse quarterly fundamentals keyed by release_date.
  - Provide a lightweight scanner snapshot path (schema-on-write).
  - Keep legacy sparse-to-dense broadcaster available for fallback.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Iterable

import numpy as np
import pandas as pd
from data import fundamentals_panel as fundamentals_panel_data

# Decision Log FR-027 (Minimum Viable Quality)
QUALITY_ROIC_MIN = 0.0
QUALITY_REVENUE_GROWTH_MIN = 0.0
QUALITY_MAX_AGE_DAYS = 183  # ~6 months

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
FUNDAMENTALS_PATH = os.path.join(PROCESSED_DIR, "fundamentals.parquet")
FUNDAMENTALS_SNAPSHOT_PATH = os.path.join(PROCESSED_DIR, "fundamentals_snapshot.parquet")
HOT_STALE_DAYS = 95
logger = logging.getLogger(__name__)
SIMULATION_TS_BINDING_SECRET_ENV = "T0_SIMULATION_TS_BINDING_SECRET"
SIMULATION_TS_BINDING_STRICT_ENV = "T0_STRICT_SIMULATION_TS_BINDING"

REQUIRED_COLUMNS = {
    "permno",
    "ticker",
    "fiscal_period_end",
    "release_date",
    "filing_date",
    "published_at",
    "fyearq",
    "fqtr",
    "revenue",
    "operating_income",
    "total_revenue_q",
    "operating_income_q",
    "total_assets_q",
    "inventory_q",
    "capex_q",
    "depreciation_q",
    "gross_profit_q",
    "cogs_q",
    "receivables_q",
    "deferred_revenue_q",
    "delta_deferred_revenue_q",
    "operating_margin_q",
    "operating_margin_delta_q",
    "gross_margin_q",
    "gm_accel_q",
    "capex_sales_q",
    "delta_capex_sales",
    "book_to_bill_proxy_q",
    "dso_q",
    "delta_dso_q",
    "revenue_inventory_q",
    "delta_revenue_inventory",
    "sales_growth_q",
    "sales_accel_q",
    "op_margin_accel_q",
    "bloat_q",
    "net_investment_q",
    "asset_growth_yoy",
    "net_income_q",
    "equity_q",
    "eps_basic_q",
    "eps_diluted_q",
    "eps_q",
    "eps_ttm",
    "eps_growth_yoy",
    "roe_q",
    "invested_capital",
    "roic",
    "revenue_growth_yoy",
    "oibdpq",
    "atq",
    "ltq",
    "xrdq",
    "oancfy",
    "oancf_q",
    "oancf_ttm",
    "ebitda_ttm",
    "revenue_ttm",
    "xrd_ttm",
    "dlttq",
    "dlcq",
    "cheq",
    "cshoq",
    "prcraq",
    "mv_q",
    "total_debt",
    "net_debt",
    "ev",
    "ev_ebitda",
    "leverage_ratio",
    "rd_intensity",
    "source",
    "ingested_at",
}
SNAPSHOT_REQUIRED_COLUMNS = {
    "permno",
    "ticker",
    "release_date",
    "published_at",
    "roic",
    "operating_margin_q",
    "operating_margin_delta_q",
    "gross_margin_q",
    "gm_accel_q",
    "capex_sales_q",
    "delta_capex_sales",
    "book_to_bill_proxy_q",
    "dso_q",
    "delta_dso_q",
    "revenue_inventory_q",
    "delta_revenue_inventory",
    "sales_growth_q",
    "sales_accel_q",
    "op_margin_accel_q",
    "bloat_q",
    "net_investment_q",
    "asset_growth_yoy",
    "roe_q",
    "eps_q",
    "eps_ttm",
    "eps_growth_yoy",
    "revenue_growth_yoy",
    "ev_ebitda",
    "leverage_ratio",
    "rd_intensity",
    "oancf_ttm",
    "ebitda_ttm",
    "quality_pass",
}


def _normalize_index(index_like) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(pd.to_datetime(index_like, errors="coerce"))
    idx = idx[~idx.isna()]
    if idx.tz is not None:
        idx = idx.tz_convert(None)
    return idx.sort_values()


def _normalize_permnos(permnos: Iterable | None) -> list[int]:
    if permnos is None:
        return []
    out: list[int] = []
    for p in permnos:
        try:
            out.append(int(p))
        except (TypeError, ValueError):
            continue
    # Preserve order from caller while removing duplicates
    return list(dict.fromkeys(out))


def _empty_matrix(
    index: pd.DatetimeIndex,
    columns: list[int],
    fill_value,
    dtype=None,
) -> pd.DataFrame:
    return pd.DataFrame(fill_value, index=index, columns=columns, dtype=dtype)


def _empty_latest_snapshot(index_permnos: list[int]) -> pd.DataFrame:
    latest = pd.DataFrame(
        {
            "ticker": pd.Series(index=index_permnos, dtype=str),
            "release_date": pd.Series(index=index_permnos, dtype="datetime64[ns]"),
            "published_at": pd.Series(index=index_permnos, dtype="datetime64[ns]"),
            "roic": pd.Series(index=index_permnos, dtype="float32"),
            "operating_margin_q": pd.Series(index=index_permnos, dtype="float32"),
            "operating_margin_delta_q": pd.Series(index=index_permnos, dtype="float32"),
            "gross_margin_q": pd.Series(index=index_permnos, dtype="float32"),
            "gm_accel_q": pd.Series(index=index_permnos, dtype="float32"),
            "capex_sales_q": pd.Series(index=index_permnos, dtype="float32"),
            "delta_capex_sales": pd.Series(index=index_permnos, dtype="float32"),
            "book_to_bill_proxy_q": pd.Series(index=index_permnos, dtype="float32"),
            "dso_q": pd.Series(index=index_permnos, dtype="float32"),
            "delta_dso_q": pd.Series(index=index_permnos, dtype="float32"),
            "revenue_inventory_q": pd.Series(index=index_permnos, dtype="float32"),
            "delta_revenue_inventory": pd.Series(index=index_permnos, dtype="float32"),
            "sales_growth_q": pd.Series(index=index_permnos, dtype="float32"),
            "sales_accel_q": pd.Series(index=index_permnos, dtype="float32"),
            "op_margin_accel_q": pd.Series(index=index_permnos, dtype="float32"),
            "bloat_q": pd.Series(index=index_permnos, dtype="float32"),
            "net_investment_q": pd.Series(index=index_permnos, dtype="float32"),
            "asset_growth_yoy": pd.Series(index=index_permnos, dtype="float32"),
            "roe_q": pd.Series(index=index_permnos, dtype="float32"),
            "eps_q": pd.Series(index=index_permnos, dtype="float32"),
            "eps_ttm": pd.Series(index=index_permnos, dtype="float32"),
            "eps_growth_yoy": pd.Series(index=index_permnos, dtype="float32"),
            "revenue_growth_yoy": pd.Series(index=index_permnos, dtype="float32"),
            "ev_ebitda": pd.Series(index=index_permnos, dtype="float32"),
            "leverage_ratio": pd.Series(index=index_permnos, dtype="float32"),
            "rd_intensity": pd.Series(index=index_permnos, dtype="float32"),
            "oancf_ttm": pd.Series(index=index_permnos, dtype="float32"),
            "ebitda_ttm": pd.Series(index=index_permnos, dtype="float32"),
            "quality_pass": pd.Series(index=index_permnos, dtype="int8"),
            "days_since_release": pd.Series(index=index_permnos, dtype="float32"),
            "is_stale": pd.Series(index=index_permnos, dtype=bool),
        }
    )
    latest.index.name = "permno"
    return latest


def _normalize_asof_date(as_of_date) -> pd.Timestamp | None:
    if as_of_date is None:
        return None
    ts = pd.to_datetime(as_of_date, errors="coerce")
    if pd.isna(ts):
        return None
    ts = pd.Timestamp(ts)
    if ts.tzinfo is not None:
        ts = ts.tz_convert(None)
    return ts


def _env_flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_simulation_ts_binding_secret(secret: str | None = None) -> str:
    if secret is not None and str(secret).strip():
        return str(secret).strip()
    env_secret = os.getenv(SIMULATION_TS_BINDING_SECRET_ENV, "").strip()
    if env_secret:
        return env_secret
    raise ValueError(
        "Simulation timestamp binding secret is missing. "
        f"Provide `simulation_ts_binding_secret` or set `{SIMULATION_TS_BINDING_SECRET_ENV}`."
    )


def create_simulation_ts_binding_token(
    simulation_ts,
    secret: str | None = None,
) -> str:
    """
    Create a deterministic HMAC token that binds requests to a specific simulation timestamp.
    """
    ts = _normalize_asof_date(simulation_ts)
    if ts is None:
        raise ValueError("Cannot create simulation timestamp binding token without a valid simulation_ts.")
    key = _resolve_simulation_ts_binding_secret(secret)
    payload = ts.isoformat()
    return hmac.new(
        key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def validate_simulation_ts_binding_token(
    simulation_ts,
    token: str,
    secret: str | None = None,
) -> bool:
    """
    Validate an HMAC token against the provided simulation timestamp.
    """
    token_text = str(token).strip() if token is not None else ""
    if not token_text:
        return False
    expected = create_simulation_ts_binding_token(simulation_ts=simulation_ts, secret=secret)
    return hmac.compare_digest(expected, token_text)


def _assert_simulation_ts_binding(
    simulation_ts: pd.Timestamp | None,
    simulation_ts_binding_token: str | None = None,
    simulation_ts_binding_secret: str | None = None,
) -> None:
    strict_mode = _env_flag_enabled(SIMULATION_TS_BINDING_STRICT_ENV)
    token_text = str(simulation_ts_binding_token).strip() if simulation_ts_binding_token is not None else ""

    if strict_mode and simulation_ts is not None and not token_text:
        raise ValueError(
            "Simulation timestamp binding token is required in strict mode "
            f"(`{SIMULATION_TS_BINDING_STRICT_ENV}=1`)."
        )
    if not token_text:
        return
    if simulation_ts is None:
        raise ValueError("Simulation timestamp binding token was provided without a valid simulation timestamp.")
    if not validate_simulation_ts_binding_token(
        simulation_ts=simulation_ts,
        token=token_text,
        secret=simulation_ts_binding_secret,
    ):
        raise ValueError("Simulation timestamp binding token mismatch (fail-closed).")


def _apply_simulation_ts_gate(df: pd.DataFrame, simulation_ts: pd.Timestamp | None) -> pd.DataFrame:
    if simulation_ts is None or df.empty:
        return df
    published_at = pd.to_datetime(df["published_at"], errors="coerce")
    release_date = pd.to_datetime(df["release_date"], errors="coerce")
    return df[(published_at <= simulation_ts) & (release_date <= simulation_ts)]


def _stable_row_hash(df: pd.DataFrame, *, exclude: set[str] | None = None) -> pd.Series:
    columns = sorted(c for c in df.columns if exclude is None or c not in exclude)
    if not columns:
        return pd.Series(np.zeros(len(df), dtype="uint64"), index=df.index)
    try:
        return pd.util.hash_pandas_object(df[columns], index=False).astype("uint64")
    except Exception:
        # Fallback path preserves deterministic ordering if pandas hashing fails on mixed dtypes.
        joined = df[columns].astype("string").fillna("<NA>").agg("|".join, axis=1)
        return pd.util.hash_pandas_object(joined, index=False).astype("uint64")


def _apply_published_at_fallback(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "fiscal_period_end" not in out.columns:
        out["fiscal_period_end"] = pd.NaT
    out["fiscal_period_end"] = pd.to_datetime(out["fiscal_period_end"], errors="coerce")
    if "release_date" not in out.columns:
        out["release_date"] = pd.NaT
    out["release_date"] = pd.to_datetime(out["release_date"], errors="coerce")
    if "filing_date" not in out.columns:
        out["filing_date"] = pd.NaT
    out["filing_date"] = pd.to_datetime(out["filing_date"], errors="coerce")
    out["filing_date"] = out["filing_date"].where(out["filing_date"].notna(), out["release_date"])
    if "published_at" not in out.columns:
        out["published_at"] = pd.NaT
    out["published_at"] = pd.to_datetime(out["published_at"], errors="coerce")
    fallback = out["filing_date"].where(
        out["filing_date"].notna(),
        out["fiscal_period_end"] + pd.Timedelta(days=90),
    )
    out["published_at"] = out["published_at"].where(out["published_at"].notna(), fallback)
    return out


def load_quarterly_fundamentals(
    permnos: Iterable | None = None,
    as_of_date=None,
    simulation_ts_binding_token: str | None = None,
    simulation_ts_binding_secret: str | None = None,
) -> pd.DataFrame:
    """
    Load and sanitize quarterly fundamentals keyed by release_date.
    Dedup key: (permno, release_date), latest ingested_at wins.
    """
    if not os.path.exists(FUNDAMENTALS_PATH):
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    raw = pd.read_parquet(FUNDAMENTALS_PATH)
    if raw.empty:
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    df = raw.copy()
    missing = REQUIRED_COLUMNS - set(df.columns)
    for col in missing:
        df[col] = np.nan
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce")
    df = df.dropna(subset=["permno"])
    df["permno"] = df["permno"].astype(int)
    df = _apply_published_at_fallback(df)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], errors="coerce")

    if permnos is not None:
        pset = set(_normalize_permnos(permnos))
        df = df[df["permno"].isin(pset)]

    if df.empty:
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    df = df.dropna(subset=["release_date"])
    df["release_date"] = df["release_date"].dt.normalize()
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

    asof_ts = _normalize_asof_date(as_of_date)
    _assert_simulation_ts_binding(
        simulation_ts=asof_ts,
        simulation_ts_binding_token=simulation_ts_binding_token,
        simulation_ts_binding_secret=simulation_ts_binding_secret,
    )
    df = _apply_simulation_ts_gate(df, simulation_ts=asof_ts)
    if df.empty:
        return pd.DataFrame(columns=sorted(REQUIRED_COLUMNS))

    for col in [
        "revenue",
        "operating_income",
        "total_revenue_q",
        "operating_income_q",
        "total_assets_q",
        "inventory_q",
        "capex_q",
        "depreciation_q",
        "gross_profit_q",
        "cogs_q",
        "receivables_q",
        "deferred_revenue_q",
        "delta_deferred_revenue_q",
        "operating_margin_q",
        "operating_margin_delta_q",
        "gross_margin_q",
        "gm_accel_q",
        "capex_sales_q",
        "delta_capex_sales",
        "book_to_bill_proxy_q",
        "dso_q",
        "delta_dso_q",
        "revenue_inventory_q",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "net_income_q",
        "equity_q",
        "eps_basic_q",
        "eps_diluted_q",
        "eps_q",
        "eps_ttm",
        "eps_growth_yoy",
        "roe_q",
        "invested_capital",
        "roic",
        "revenue_growth_yoy",
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["_row_hash"] = _stable_row_hash(df)
    df = df.sort_values(["permno", "release_date", "published_at", "ingested_at", "_row_hash"])
    df = df.drop_duplicates(subset=["permno", "release_date", "published_at"], keep="last")
    df = df.drop(columns=["_row_hash"])
    return df


def load_fundamentals_snapshot(
    permnos: Iterable | None = None,
    as_of_date=None,
    simulation_ts_binding_token: str | None = None,
    simulation_ts_binding_secret: str | None = None,
) -> pd.DataFrame:
    """
    Load scanner-ready latest fundamentals snapshot keyed by permno.
    Falls back to deriving latest rows from fundamentals.parquet if snapshot is missing.
    """
    def _empty_snapshot() -> pd.DataFrame:
        empty = pd.DataFrame(columns=sorted(SNAPSHOT_REQUIRED_COLUMNS - {"permno"}))
        empty.index = pd.Index([], name="permno")
        return empty

    asof_ts = _normalize_asof_date(as_of_date)
    _assert_simulation_ts_binding(
        simulation_ts=asof_ts,
        simulation_ts_binding_token=simulation_ts_binding_token,
        simulation_ts_binding_secret=simulation_ts_binding_secret,
    )
    if asof_ts is None and os.path.exists(FUNDAMENTALS_SNAPSHOT_PATH):
        snap = pd.read_parquet(FUNDAMENTALS_SNAPSHOT_PATH)
    else:
        qdf = load_quarterly_fundamentals(
            permnos=None,
            as_of_date=asof_ts,
            simulation_ts_binding_token=simulation_ts_binding_token,
            simulation_ts_binding_secret=simulation_ts_binding_secret,
        )
        if qdf.empty:
            return _empty_snapshot()
        qdf = qdf.dropna(subset=["release_date"])
        pit_cutoff = asof_ts if asof_ts is not None else pd.Timestamp.utcnow().tz_localize(None).normalize()
        known_qdf = _apply_simulation_ts_gate(qdf, simulation_ts=pit_cutoff)
        if known_qdf.empty:
            return _empty_snapshot()
        known_qdf = known_qdf.sort_values(["permno", "release_date", "published_at", "ingested_at"])
        latest = known_qdf.drop_duplicates(subset=["permno"], keep="last").copy()
        quality = latest["roic"].gt(QUALITY_ROIC_MIN) & latest["revenue_growth_yoy"].gt(QUALITY_REVENUE_GROWTH_MIN)
        latest["quality_pass"] = quality.fillna(False).astype("int8")
        for c in (
            "published_at",
            "operating_margin_q",
            "operating_margin_delta_q",
            "gross_margin_q",
            "gm_accel_q",
            "capex_sales_q",
            "delta_capex_sales",
            "book_to_bill_proxy_q",
            "dso_q",
            "delta_dso_q",
            "revenue_inventory_q",
            "delta_revenue_inventory",
            "sales_growth_q",
            "sales_accel_q",
            "op_margin_accel_q",
            "bloat_q",
            "net_investment_q",
            "asset_growth_yoy",
            "roe_q",
            "eps_q",
            "eps_ttm",
            "eps_growth_yoy",
            "ev_ebitda",
            "leverage_ratio",
            "rd_intensity",
            "oancf_ttm",
            "ebitda_ttm",
        ):
            if c not in latest.columns:
                latest[c] = np.nan
        snap = latest[
            [
                "permno",
                "ticker",
                "release_date",
                "published_at",
                "roic",
                "operating_margin_q",
                "operating_margin_delta_q",
                "gross_margin_q",
                "gm_accel_q",
                "capex_sales_q",
                "delta_capex_sales",
                "book_to_bill_proxy_q",
                "dso_q",
                "delta_dso_q",
                "revenue_inventory_q",
                "delta_revenue_inventory",
                "sales_growth_q",
                "sales_accel_q",
                "op_margin_accel_q",
                "bloat_q",
                "net_investment_q",
                "asset_growth_yoy",
                "roe_q",
                "eps_q",
                "eps_ttm",
                "eps_growth_yoy",
                "revenue_growth_yoy",
                "ev_ebitda",
                "leverage_ratio",
                "rd_intensity",
                "oancf_ttm",
                "ebitda_ttm",
                "quality_pass",
            ]
        ]

    if snap is None or snap.empty:
        return _empty_snapshot()

    cols = set(snap.columns)
    missing = SNAPSHOT_REQUIRED_COLUMNS - cols
    for c in missing:
        snap[c] = np.nan

    snap = _apply_published_at_fallback(snap)
    snap["permno"] = pd.to_numeric(snap["permno"], errors="coerce")
    snap = snap.dropna(subset=["permno"])
    if snap.empty:
        return _empty_snapshot()
    snap["permno"] = snap["permno"].astype(int)
    snap["ticker"] = snap["ticker"].astype(str).str.upper().str.strip()
    snap["release_date"] = pd.to_datetime(snap["release_date"], errors="coerce")
    snap["published_at"] = pd.to_datetime(snap["published_at"], errors="coerce")
    snap["roic"] = pd.to_numeric(snap["roic"], errors="coerce").astype("float32")
    for c in (
        "operating_margin_q",
        "operating_margin_delta_q",
        "gross_margin_q",
        "gm_accel_q",
        "capex_sales_q",
        "delta_capex_sales",
        "book_to_bill_proxy_q",
        "dso_q",
        "delta_dso_q",
        "revenue_inventory_q",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
    ):
        snap[c] = pd.to_numeric(snap[c], errors="coerce").astype("float32")
    snap["roe_q"] = pd.to_numeric(snap["roe_q"], errors="coerce").astype("float32")
    snap["eps_q"] = pd.to_numeric(snap["eps_q"], errors="coerce").astype("float32")
    snap["eps_ttm"] = pd.to_numeric(snap["eps_ttm"], errors="coerce").astype("float32")
    snap["eps_growth_yoy"] = pd.to_numeric(snap["eps_growth_yoy"], errors="coerce").astype("float32")
    snap["revenue_growth_yoy"] = pd.to_numeric(snap["revenue_growth_yoy"], errors="coerce").astype("float32")
    for c in ("ev_ebitda", "leverage_ratio", "rd_intensity", "oancf_ttm", "ebitda_ttm"):
        snap[c] = pd.to_numeric(snap[c], errors="coerce").astype("float32")
    snap["quality_pass"] = pd.to_numeric(snap["quality_pass"], errors="coerce").fillna(0).astype("int8")
    snap = _apply_simulation_ts_gate(snap, simulation_ts=asof_ts)
    snap = snap.sort_values(["permno", "release_date", "published_at"]).drop_duplicates(subset=["permno"], keep="last")
    snap = snap.set_index("permno").sort_index()

    if permnos is not None:
        cols = _normalize_permnos(permnos)
        snap = snap.reindex(cols)

    return snap


def build_fundamentals_snapshot_context(
    prices_index,
    permnos: Iterable | None = None,
    max_age_days: int = QUALITY_MAX_AGE_DAYS,
) -> dict[str, pd.DataFrame]:
    """
    Build lightweight fundamentals context for scanner/watchlist/detail.
    Uses one-row daily matrices derived from fundamentals_snapshot.parquet.
    """
    idx = _normalize_index(prices_index)
    permno_cols = _normalize_permnos(permnos)

    if len(idx) == 0:
        roic_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        op_margin_delta_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        gm_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        btb_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        dso_delta_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        delta_capex_sales_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        delta_rev_inv_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        sales_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        sales_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        op_margin_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        bloat_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        net_investment_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        asset_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        roe_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        eps_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        rev_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
        q_empty = _empty_matrix(idx, permno_cols, 0, dtype="int8")
        return {
            "roic": roic_empty,
            "operating_margin_delta_q": op_margin_delta_empty,
            "gm_accel_q": gm_accel_empty,
            "book_to_bill_proxy_q": btb_empty,
            "delta_dso_q": dso_delta_empty,
            "delta_capex_sales": delta_capex_sales_empty,
            "delta_revenue_inventory": delta_rev_inv_empty,
            "sales_growth_q": sales_growth_empty,
            "sales_accel_q": sales_accel_empty,
            "op_margin_accel_q": op_margin_accel_empty,
            "bloat_q": bloat_empty,
            "net_investment_q": net_investment_empty,
            "asset_growth_yoy": asset_growth_empty,
            "roe_q": roe_empty,
            "eps_growth_yoy": eps_growth_empty,
            "revenue_growth_yoy": rev_empty,
            "quality_pass": q_empty,
            "latest": _empty_latest_snapshot(permno_cols),
        }

    snapshot = load_fundamentals_snapshot(
        permnos=permno_cols if permno_cols else None,
        as_of_date=idx[-1],
    )
    if snapshot.empty and permno_cols:
        empty_latest = _empty_latest_snapshot(permno_cols)
        last_idx = pd.DatetimeIndex([idx[-1]])
        return {
            "roic": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "operating_margin_delta_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "gm_accel_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "book_to_bill_proxy_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "delta_dso_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "delta_capex_sales": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "delta_revenue_inventory": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "sales_growth_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "sales_accel_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "op_margin_accel_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "bloat_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "net_investment_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "asset_growth_yoy": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "roe_q": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "eps_growth_yoy": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "revenue_growth_yoy": _empty_matrix(last_idx, permno_cols, np.nan, dtype="float32"),
            "quality_pass": _empty_matrix(last_idx, permno_cols, 0, dtype="int8"),
            "latest": empty_latest,
        }

    if not permno_cols:
        permno_cols = snapshot.index.astype(int).tolist()
    snapshot = snapshot.reindex(permno_cols)

    asof_date = idx[-1]
    days_since = (asof_date - snapshot["release_date"]).dt.days.astype("float32")
    is_future = days_since.lt(0)
    is_stale = days_since.gt(max_age_days) | days_since.isna() | is_future
    quality = snapshot["quality_pass"].fillna(0).astype("int8")
    quality = quality.where(~is_stale, 0).astype("int8")

    latest = pd.DataFrame(
        {
            "ticker": snapshot["ticker"],
            "release_date": snapshot["release_date"],
            "published_at": snapshot["published_at"],
            "roic": snapshot["roic"].astype("float32"),
            "operating_margin_q": snapshot["operating_margin_q"].astype("float32"),
            "operating_margin_delta_q": snapshot["operating_margin_delta_q"].astype("float32"),
            "gross_margin_q": snapshot["gross_margin_q"].astype("float32"),
            "gm_accel_q": snapshot["gm_accel_q"].astype("float32"),
            "capex_sales_q": snapshot["capex_sales_q"].astype("float32"),
            "delta_capex_sales": snapshot["delta_capex_sales"].astype("float32"),
            "book_to_bill_proxy_q": snapshot["book_to_bill_proxy_q"].astype("float32"),
            "dso_q": snapshot["dso_q"].astype("float32"),
            "delta_dso_q": snapshot["delta_dso_q"].astype("float32"),
            "revenue_inventory_q": snapshot["revenue_inventory_q"].astype("float32"),
            "delta_revenue_inventory": snapshot["delta_revenue_inventory"].astype("float32"),
            "sales_growth_q": snapshot["sales_growth_q"].astype("float32"),
            "sales_accel_q": snapshot["sales_accel_q"].astype("float32"),
            "op_margin_accel_q": snapshot["op_margin_accel_q"].astype("float32"),
            "bloat_q": snapshot["bloat_q"].astype("float32"),
            "net_investment_q": snapshot["net_investment_q"].astype("float32"),
            "asset_growth_yoy": snapshot["asset_growth_yoy"].astype("float32"),
            "roe_q": snapshot["roe_q"].astype("float32"),
            "eps_q": snapshot["eps_q"].astype("float32"),
            "eps_ttm": snapshot["eps_ttm"].astype("float32"),
            "eps_growth_yoy": snapshot["eps_growth_yoy"].astype("float32"),
            "revenue_growth_yoy": snapshot["revenue_growth_yoy"].astype("float32"),
            "ev_ebitda": snapshot["ev_ebitda"].astype("float32"),
            "leverage_ratio": snapshot["leverage_ratio"].astype("float32"),
            "rd_intensity": snapshot["rd_intensity"].astype("float32"),
            "oancf_ttm": snapshot["oancf_ttm"].astype("float32"),
            "ebitda_ttm": snapshot["ebitda_ttm"].astype("float32"),
            "quality_pass": quality.astype("int8"),
            "days_since_release": days_since,
            "is_stale": is_stale.fillna(True).astype(bool),
        },
        index=snapshot.index,
    )
    latest.index.name = "permno"

    row_idx = pd.DatetimeIndex([asof_date])
    roic = pd.DataFrame([latest["roic"].to_numpy(dtype="float32")], index=row_idx, columns=permno_cols).astype("float32")
    op_margin_delta = pd.DataFrame(
        [latest["operating_margin_delta_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    gm_accel = pd.DataFrame(
        [latest["gm_accel_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    btb = pd.DataFrame(
        [latest["book_to_bill_proxy_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    dso_delta = pd.DataFrame(
        [latest["delta_dso_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    dcapex = pd.DataFrame(
        [latest["delta_capex_sales"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    drev_inv = pd.DataFrame(
        [latest["delta_revenue_inventory"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    sales_growth = pd.DataFrame(
        [latest["sales_growth_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    sales_accel = pd.DataFrame(
        [latest["sales_accel_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    op_margin_accel = pd.DataFrame(
        [latest["op_margin_accel_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    bloat = pd.DataFrame(
        [latest["bloat_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    net_investment = pd.DataFrame(
        [latest["net_investment_q"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    asset_growth = pd.DataFrame(
        [latest["asset_growth_yoy"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    roe = pd.DataFrame([latest["roe_q"].to_numpy(dtype="float32")], index=row_idx, columns=permno_cols).astype("float32")
    eps_growth = pd.DataFrame(
        [latest["eps_growth_yoy"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    rev = pd.DataFrame(
        [latest["revenue_growth_yoy"].to_numpy(dtype="float32")],
        index=row_idx,
        columns=permno_cols,
    ).astype("float32")
    q = pd.DataFrame([latest["quality_pass"].to_numpy(dtype="int8")], index=row_idx, columns=permno_cols).astype("int8")

    return {
        "roic": roic,
        "operating_margin_delta_q": op_margin_delta,
        "gm_accel_q": gm_accel,
        "book_to_bill_proxy_q": btb,
        "delta_dso_q": dso_delta,
        "delta_capex_sales": dcapex,
        "delta_revenue_inventory": drev_inv,
        "sales_growth_q": sales_growth,
        "sales_accel_q": sales_accel,
        "op_margin_accel_q": op_margin_accel,
        "bloat_q": bloat,
        "net_investment_q": net_investment,
        "asset_growth_yoy": asset_growth,
        "roe_q": roe,
        "eps_growth_yoy": eps_growth,
        "revenue_growth_yoy": rev,
        "quality_pass": q,
        "latest": latest,
    }


def get_stale_hot_tickers(
    latest_snapshot: pd.DataFrame | None,
    hot_tickers: Iterable[str],
    max_age_days: int = HOT_STALE_DAYS,
    skip_tickers: Iterable[str] | None = None,
) -> list[str]:
    """
    Return hot-list tickers whose fundamentals are missing or older than max_age_days.
    """
    if latest_snapshot is None or latest_snapshot.empty:
        return _normalize_ticker_list(hot_tickers)

    watch = _normalize_ticker_list(hot_tickers)
    if not watch:
        return []

    skip = set(_normalize_ticker_list(skip_tickers or []))
    frame = latest_snapshot.copy()
    if "ticker" not in frame.columns:
        return [t for t in watch if t not in skip]

    frame["ticker"] = frame["ticker"].astype(str).str.upper().str.strip()
    if "days_since_release" in frame.columns:
        age = pd.to_numeric(frame["days_since_release"], errors="coerce")
    else:
        rel = pd.to_datetime(frame.get("release_date"), errors="coerce")
        asof = pd.Timestamp.utcnow().normalize()
        age = (asof - rel).dt.days
    stale_flag = age.gt(max_age_days) | age.isna()
    stale_map = dict(zip(frame["ticker"], stale_flag.fillna(True)))

    out = []
    for t in watch:
        if t in skip:
            continue
        if bool(stale_map.get(t, True)):
            out.append(t)
    return out


def _normalize_ticker_list(values: Iterable[str]) -> list[str]:
    out: list[str] = []
    for v in values:
        if v is None:
            continue
        s = str(v).strip().upper()
        if s:
            out.append(s)
    return list(dict.fromkeys(out))


def _broadcast_metric(
    df: pd.DataFrame,
    metric: str,
    prices_index: pd.DatetimeIndex,
    permno_cols: list[int],
    event_col: str = "published_at",
) -> pd.DataFrame:
    if df.empty or metric not in df.columns or event_col not in df.columns:
        return _empty_matrix(prices_index, permno_cols, np.nan, dtype="float32")
    work = df[[event_col, "permno", metric]].copy()
    work[event_col] = pd.to_datetime(work[event_col], errors="coerce").dt.normalize()
    work["permno"] = pd.to_numeric(work["permno"], errors="coerce")
    work = work.dropna(subset=[event_col, "permno"])
    if work.empty:
        return _empty_matrix(prices_index, permno_cols, np.nan, dtype="float32")
    work["permno"] = work["permno"].astype(int)
    sparse = (
        work.pivot_table(index=event_col, columns="permno", values=metric, aggfunc="last")
        .sort_index()
    )
    dense = sparse.reindex(prices_index).ffill()
    dense = dense.reindex(columns=permno_cols)
    return dense


def _empty_daily_payload(idx: pd.DatetimeIndex, permno_cols: list[int]) -> dict[str, pd.DataFrame]:
    roic_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    op_margin_delta_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    gm_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    book_to_bill_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    delta_dso_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    delta_capex_sales_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    delta_rev_inv_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    sales_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    sales_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    op_margin_accel_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    bloat_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    net_investment_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    asset_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    rev_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    roe_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    eps_growth_empty = _empty_matrix(idx, permno_cols, np.nan, dtype="float32")
    q_empty = _empty_matrix(idx, permno_cols, False, dtype=bool)
    latest_empty = pd.DataFrame(
        {
            "roic": pd.Series(index=permno_cols, dtype="float32"),
            "operating_margin_delta_q": pd.Series(index=permno_cols, dtype="float32"),
            "gm_accel_q": pd.Series(index=permno_cols, dtype="float32"),
            "book_to_bill_proxy_q": pd.Series(index=permno_cols, dtype="float32"),
            "delta_dso_q": pd.Series(index=permno_cols, dtype="float32"),
            "delta_capex_sales": pd.Series(index=permno_cols, dtype="float32"),
            "delta_revenue_inventory": pd.Series(index=permno_cols, dtype="float32"),
            "sales_growth_q": pd.Series(index=permno_cols, dtype="float32"),
            "sales_accel_q": pd.Series(index=permno_cols, dtype="float32"),
            "op_margin_accel_q": pd.Series(index=permno_cols, dtype="float32"),
            "bloat_q": pd.Series(index=permno_cols, dtype="float32"),
            "net_investment_q": pd.Series(index=permno_cols, dtype="float32"),
            "asset_growth_yoy": pd.Series(index=permno_cols, dtype="float32"),
            "roe_q": pd.Series(index=permno_cols, dtype="float32"),
            "eps_growth_yoy": pd.Series(index=permno_cols, dtype="float32"),
            "revenue_growth_yoy": pd.Series(index=permno_cols, dtype="float32"),
            "age_days": pd.Series(index=permno_cols, dtype="float32"),
            "quality_pass": pd.Series(index=permno_cols, dtype="int8"),
        }
    )
    latest_empty.index.name = "permno"
    return {
        "roic": roic_empty,
        "operating_margin_delta_q": op_margin_delta_empty,
        "gm_accel_q": gm_accel_empty,
        "book_to_bill_proxy_q": book_to_bill_empty,
        "delta_dso_q": delta_dso_empty,
        "delta_capex_sales": delta_capex_sales_empty,
        "delta_revenue_inventory": delta_rev_inv_empty,
        "sales_growth_q": sales_growth_empty,
        "sales_accel_q": sales_accel_empty,
        "op_margin_accel_q": op_margin_accel_empty,
        "bloat_q": bloat_empty,
        "net_investment_q": net_investment_empty,
        "asset_growth_yoy": asset_growth_empty,
        "roe_q": roe_empty,
        "eps_growth_yoy": eps_growth_empty,
        "revenue_growth_yoy": rev_empty,
        "quality_pass": q_empty,
        "latest": latest_empty,
    }


def build_fundamentals_daily(
    prices_index,
    permnos: Iterable | None = None,
    max_age_days: int = QUALITY_MAX_AGE_DAYS,
    simulation_ts_binding_token: str | None = None,
    simulation_ts_binding_secret: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Build dense daily matrices aligned to prices index.

    Returns:
      - roic: daily ROIC matrix (float32)
      - revenue_growth_yoy: daily YoY revenue growth matrix (float32)
      - quality_pass: bool matrix applying FR-027 thresholds + staleness
      - latest: lightweight per-permno snapshot with latest roic/revenue_growth/age/quality
    """
    idx = _normalize_index(prices_index)
    permno_cols = _normalize_permnos(permnos)
    if len(idx) == 0:
        return _empty_daily_payload(idx, permno_cols)

    panel_cols = [
        "date",
        "permno",
        "release_date",
        "roic",
        "operating_margin_delta_q",
        "gm_accel_q",
        "book_to_bill_proxy_q",
        "delta_dso_q",
        "delta_capex_sales",
        "delta_revenue_inventory",
        "sales_growth_q",
        "sales_accel_q",
        "op_margin_accel_q",
        "bloat_q",
        "net_investment_q",
        "asset_growth_yoy",
        "roe_q",
        "eps_growth_yoy",
        "revenue_growth_yoy",
    ]
    panel = pd.DataFrame()
    panel_load_exception: Exception | None = None
    try:
        panel = fundamentals_panel_data.load_daily_fundamentals_panel(
            start_date=idx[0].strftime("%Y-%m-%d"),
            end_date=idx[-1].strftime("%Y-%m-%d"),
            permnos=permno_cols if permno_cols else None,
            columns=panel_cols,
        )
    except Exception as exc:
        panel_load_exception = exc
        logger.warning(
            "Daily fundamentals panel load failed; falling back to quarterly published_at broadcast "
            "(start=%s end=%s permno_scope=%s error=%s).",
            idx[0].strftime("%Y-%m-%d"),
            idx[-1].strftime("%Y-%m-%d"),
            len(permno_cols) if permno_cols else "all",
            exc.__class__.__name__,
        )
        panel = pd.DataFrame()

    if not panel.empty:
        panel = panel.copy()
        panel["date"] = pd.to_datetime(panel["date"], errors="coerce").dt.normalize()
        panel["permno"] = pd.to_numeric(panel["permno"], errors="coerce")
        panel = panel.dropna(subset=["date", "permno"])
        panel["permno"] = panel["permno"].astype(int)
        if not permno_cols:
            permno_cols = sorted(panel["permno"].unique().tolist())
        if permno_cols:
            panel = panel[panel["permno"].isin(set(permno_cols))]
    if panel.empty:
        qdf = load_quarterly_fundamentals(
            permno_cols if permno_cols else None,
            as_of_date=idx[-1],
            simulation_ts_binding_token=simulation_ts_binding_token,
            simulation_ts_binding_secret=simulation_ts_binding_secret,
        )
        if qdf.empty:
            return _empty_daily_payload(idx, permno_cols)
        if not permno_cols:
            permno_cols = sorted(qdf["permno"].unique().tolist())
        if panel_load_exception is not None:
            logger.warning(
                "Daily fundamentals fallback active mode=quarterly_published_at rows=%s dates=%s permnos=%s.",
                int(len(qdf)),
                int(len(idx)),
                int(len(permno_cols)),
            )
        roic_daily = _broadcast_metric(qdf, "roic", idx, permno_cols, event_col="published_at").astype("float32")
        op_margin_delta_daily = _broadcast_metric(qdf, "operating_margin_delta_q", idx, permno_cols, event_col="published_at").astype("float32")
        gm_accel_daily = _broadcast_metric(qdf, "gm_accel_q", idx, permno_cols, event_col="published_at").astype("float32")
        book_to_bill_daily = _broadcast_metric(qdf, "book_to_bill_proxy_q", idx, permno_cols, event_col="published_at").astype("float32")
        delta_dso_daily = _broadcast_metric(qdf, "delta_dso_q", idx, permno_cols, event_col="published_at").astype("float32")
        delta_capex_sales_daily = _broadcast_metric(qdf, "delta_capex_sales", idx, permno_cols, event_col="published_at").astype("float32")
        delta_revenue_inventory_daily = _broadcast_metric(qdf, "delta_revenue_inventory", idx, permno_cols, event_col="published_at").astype("float32")
        sales_growth_daily = _broadcast_metric(qdf, "sales_growth_q", idx, permno_cols, event_col="published_at").astype("float32")
        sales_accel_daily = _broadcast_metric(qdf, "sales_accel_q", idx, permno_cols, event_col="published_at").astype("float32")
        op_margin_accel_daily = _broadcast_metric(qdf, "op_margin_accel_q", idx, permno_cols, event_col="published_at").astype("float32")
        bloat_daily = _broadcast_metric(qdf, "bloat_q", idx, permno_cols, event_col="published_at").astype("float32")
        net_investment_daily = _broadcast_metric(qdf, "net_investment_q", idx, permno_cols, event_col="published_at").astype("float32")
        asset_growth_daily = _broadcast_metric(qdf, "asset_growth_yoy", idx, permno_cols, event_col="published_at").astype("float32")
        roe_daily = _broadcast_metric(qdf, "roe_q", idx, permno_cols, event_col="published_at").astype("float32")
        eps_growth_daily = _broadcast_metric(qdf, "eps_growth_yoy", idx, permno_cols, event_col="published_at").astype("float32")
        rev_growth_daily = _broadcast_metric(qdf, "revenue_growth_yoy", idx, permno_cols, event_col="published_at").astype("float32")
        release_work = qdf[["published_at", "permno", "release_date"]].copy()
        release_work["published_at"] = pd.to_datetime(release_work["published_at"], errors="coerce").dt.normalize()
        release_work["release_date"] = pd.to_datetime(release_work["release_date"], errors="coerce").dt.normalize()
        release_work = release_work.dropna(subset=["published_at", "permno"])
        release_sparse = (
            release_work.pivot_table(index="published_at", columns="permno", values="release_date", aggfunc="last")
            .sort_index()
        )
        release_daily = release_sparse.reindex(idx).ffill().reindex(columns=permno_cols)
        release_daily = release_daily.apply(pd.to_datetime, errors="coerce")
    else:
        roic_daily = (
            panel.pivot_table(index="date", columns="permno", values="roic", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        op_margin_delta_daily = (
            panel.pivot_table(index="date", columns="permno", values="operating_margin_delta_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        gm_accel_daily = (
            panel.pivot_table(index="date", columns="permno", values="gm_accel_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        book_to_bill_daily = (
            panel.pivot_table(index="date", columns="permno", values="book_to_bill_proxy_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        delta_dso_daily = (
            panel.pivot_table(index="date", columns="permno", values="delta_dso_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        delta_capex_sales_daily = (
            panel.pivot_table(index="date", columns="permno", values="delta_capex_sales", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        delta_revenue_inventory_daily = (
            panel.pivot_table(index="date", columns="permno", values="delta_revenue_inventory", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        sales_growth_daily = (
            panel.pivot_table(index="date", columns="permno", values="sales_growth_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        sales_accel_daily = (
            panel.pivot_table(index="date", columns="permno", values="sales_accel_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        op_margin_accel_daily = (
            panel.pivot_table(index="date", columns="permno", values="op_margin_accel_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        bloat_daily = (
            panel.pivot_table(index="date", columns="permno", values="bloat_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        net_investment_daily = (
            panel.pivot_table(index="date", columns="permno", values="net_investment_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        asset_growth_daily = (
            panel.pivot_table(index="date", columns="permno", values="asset_growth_yoy", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        roe_daily = (
            panel.pivot_table(index="date", columns="permno", values="roe_q", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        eps_growth_daily = (
            panel.pivot_table(index="date", columns="permno", values="eps_growth_yoy", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        rev_growth_daily = (
            panel.pivot_table(index="date", columns="permno", values="revenue_growth_yoy", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
            .astype("float32")
        )
        release_daily = (
            panel.assign(release_date=pd.to_datetime(panel["release_date"], errors="coerce").dt.normalize())
            .pivot_table(index="date", columns="permno", values="release_date", aggfunc="last")
            .reindex(index=idx, columns=permno_cols)
        )
        release_daily = release_daily.apply(pd.to_datetime, errors="coerce")

    if len(permno_cols) == 0:
        return _empty_daily_payload(idx, permno_cols)

    valid_time_mask = release_daily.notna() & release_daily.le(pd.Series(idx, index=idx), axis=0)
    release_daily = release_daily.where(valid_time_mask)

    def _apply_valid_time_mask(frame: pd.DataFrame) -> pd.DataFrame:
        return frame.where(valid_time_mask)

    roic_daily = _apply_valid_time_mask(roic_daily).astype("float32")
    op_margin_delta_daily = _apply_valid_time_mask(op_margin_delta_daily).astype("float32")
    gm_accel_daily = _apply_valid_time_mask(gm_accel_daily).astype("float32")
    book_to_bill_daily = _apply_valid_time_mask(book_to_bill_daily).astype("float32")
    delta_dso_daily = _apply_valid_time_mask(delta_dso_daily).astype("float32")
    delta_capex_sales_daily = _apply_valid_time_mask(delta_capex_sales_daily).astype("float32")
    delta_revenue_inventory_daily = _apply_valid_time_mask(delta_revenue_inventory_daily).astype("float32")
    sales_growth_daily = _apply_valid_time_mask(sales_growth_daily).astype("float32")
    sales_accel_daily = _apply_valid_time_mask(sales_accel_daily).astype("float32")
    op_margin_accel_daily = _apply_valid_time_mask(op_margin_accel_daily).astype("float32")
    bloat_daily = _apply_valid_time_mask(bloat_daily).astype("float32")
    net_investment_daily = _apply_valid_time_mask(net_investment_daily).astype("float32")
    asset_growth_daily = _apply_valid_time_mask(asset_growth_daily).astype("float32")
    roe_daily = _apply_valid_time_mask(roe_daily).astype("float32")
    eps_growth_daily = _apply_valid_time_mask(eps_growth_daily).astype("float32")
    rev_growth_daily = _apply_valid_time_mask(rev_growth_daily).astype("float32")

    price_series = pd.Series(idx, index=idx)
    age_days = release_daily.apply(lambda s: (price_series - s).dt.days)
    age_days = age_days.astype("float32")

    quality_pass = (
        roic_daily.gt(QUALITY_ROIC_MIN)
        & rev_growth_daily.gt(QUALITY_REVENUE_GROWTH_MIN)
        & age_days.le(max_age_days)
        & age_days.ge(0)
        & roic_daily.notna()
        & rev_growth_daily.notna()
    )
    quality_pass = quality_pass.astype(bool)

    latest = pd.DataFrame(
        {
            "roic": roic_daily.iloc[-1].astype("float32"),
            "operating_margin_delta_q": op_margin_delta_daily.iloc[-1].astype("float32"),
            "gm_accel_q": gm_accel_daily.iloc[-1].astype("float32"),
            "book_to_bill_proxy_q": book_to_bill_daily.iloc[-1].astype("float32"),
            "delta_dso_q": delta_dso_daily.iloc[-1].astype("float32"),
            "delta_capex_sales": delta_capex_sales_daily.iloc[-1].astype("float32"),
            "delta_revenue_inventory": delta_revenue_inventory_daily.iloc[-1].astype("float32"),
            "sales_growth_q": sales_growth_daily.iloc[-1].astype("float32"),
            "sales_accel_q": sales_accel_daily.iloc[-1].astype("float32"),
            "op_margin_accel_q": op_margin_accel_daily.iloc[-1].astype("float32"),
            "bloat_q": bloat_daily.iloc[-1].astype("float32"),
            "net_investment_q": net_investment_daily.iloc[-1].astype("float32"),
            "asset_growth_yoy": asset_growth_daily.iloc[-1].astype("float32"),
            "roe_q": roe_daily.iloc[-1].astype("float32"),
            "eps_growth_yoy": eps_growth_daily.iloc[-1].astype("float32"),
            "revenue_growth_yoy": rev_growth_daily.iloc[-1].astype("float32"),
            "age_days": age_days.iloc[-1].astype("float32"),
            "quality_pass": quality_pass.iloc[-1].astype("int8"),
        }
    )
    latest.index.name = "permno"

    return {
        "roic": roic_daily,
        "operating_margin_delta_q": op_margin_delta_daily,
        "gm_accel_q": gm_accel_daily,
        "book_to_bill_proxy_q": book_to_bill_daily,
        "delta_dso_q": delta_dso_daily,
        "delta_capex_sales": delta_capex_sales_daily,
        "delta_revenue_inventory": delta_revenue_inventory_daily,
        "sales_growth_q": sales_growth_daily,
        "sales_accel_q": sales_accel_daily,
        "op_margin_accel_q": op_margin_accel_daily,
        "bloat_q": bloat_daily,
        "net_investment_q": net_investment_daily,
        "asset_growth_yoy": asset_growth_daily,
        "roe_q": roe_daily,
        "eps_growth_yoy": eps_growth_daily,
        "revenue_growth_yoy": rev_growth_daily,
        "quality_pass": quality_pass,
        "latest": latest,
    }
