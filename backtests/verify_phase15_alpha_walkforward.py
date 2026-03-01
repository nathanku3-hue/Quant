"""
Phase 15 verifier: FR-070 alpha walk-forward backtest.

Outputs:
  - data/processed/phase15_walkforward.csv
  - data/processed/phase15_equity_curve.png
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine
from strategies.investor_cockpit import InvestorCockpitStrategy
from strategies.regime_manager import RegimeManager

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_MACRO_FALLBACK_PATH = PROCESSED_DIR / "macro.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"
DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "phase15_walkforward.csv"
DEFAULT_OUTPUT_PNG = PROCESSED_DIR / "phase15_equity_curve.png"

SPY_PERMNO = 84398
BIL_PERMNO = 92027


def _load_phase13_module():
    path = PROJECT_ROOT / "backtests" / "verify_phase13_walkforward.py"
    spec = importlib.util.spec_from_file_location("verify_phase13_walkforward", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module at {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolve_path(value: str | None, default_path: Path | None = None) -> Path | None:
    if value is None:
        return default_path
    p = Path(value)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def _to_ts(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date value: {value}")
    return pd.Timestamp(ts).normalize()


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _atomic_csv_write(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def _load_frame(path: Path, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing parquet: {path}")
    df = pd.read_parquet(path)
    if "date" not in df.columns:
        raise ValueError(f"Missing `date` column in {path}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"]).sort_values("date")
    df = df.drop_duplicates(subset=["date"], keep="last")
    df = df.set_index("date")
    if start is not None:
        df = df[df.index >= start]
    if end is not None:
        df = df[df.index <= end]
    return df.sort_index()


def _build_context(macro: pd.DataFrame, liquidity: pd.DataFrame | None) -> pd.DataFrame:
    if liquidity is None or liquidity.empty:
        return macro.copy()
    idx = macro.index.union(liquidity.index).sort_values()
    ctx = macro.reindex(idx).copy()
    liq = liquidity.reindex(idx)
    for col in liq.columns:
        if col not in ctx.columns:
            ctx[col] = liq[col]
        else:
            if col in {"us_net_liquidity_mm", "liquidity_impulse", "repo_spread_bps", "vix_level", "vrp"}:
                liq_col = pd.to_numeric(liq[col], errors="coerce")
                base_col = pd.to_numeric(ctx[col], errors="coerce")
                ctx[col] = liq_col.combine_first(base_col)
    return ctx


def _load_price_series(
    permno: int,
    prices_path: Path | None,
    patch_path: Path | None,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.Series:
    sources: list[str] = []
    if prices_path is not None and prices_path.exists():
        filters = [f"CAST(permno AS BIGINT) = {permno}"]
        if start is not None:
            filters.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
        if end is not None:
            filters.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(adj_close AS DOUBLE) AS adj_close, 0 AS priority
            FROM '{_sql_escape_path(prices_path)}'
            WHERE {' AND '.join(filters)}
            """
        )
    if patch_path is not None and patch_path.exists():
        filters = [f"CAST(permno AS BIGINT) = {permno}"]
        if start is not None:
            filters.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
        if end is not None:
            filters.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(adj_close AS DOUBLE) AS adj_close, 1 AS priority
            FROM '{_sql_escape_path(patch_path)}'
            WHERE {' AND '.join(filters)}
            """
        )
    if not sources:
        return pd.Series(dtype=float)

    q = f"""
    WITH src AS (
        {' UNION ALL '.join(sources)}
    ),
    ranked AS (
        SELECT date, adj_close, ROW_NUMBER() OVER (PARTITION BY date ORDER BY priority DESC) AS rn
        FROM src
    )
    SELECT date, adj_close FROM ranked WHERE rn=1 ORDER BY date
    """
    con = duckdb.connect()
    try:
        df = con.execute(q).df()
    finally:
        con.close()
    if df.empty:
        return pd.Series(dtype=float)
    idx = pd.to_datetime(df["date"], errors="coerce")
    vals = pd.to_numeric(df["adj_close"], errors="coerce")
    s = pd.Series(vals.values, index=idx, dtype=float)
    s = s[~s.index.isna()].sort_index()
    return s


def _load_feature_history(
    features_path: Path,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    top_n: int,
) -> pd.DataFrame:
    if not features_path.exists():
        raise FileNotFoundError(f"Missing feature store: {features_path}")
    df = pd.read_parquet(features_path)
    if "date" not in df.columns or "permno" not in df.columns:
        raise ValueError("features.parquet missing required columns `date` or `permno`.")
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    df["permno"] = pd.to_numeric(df["permno"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["date", "permno"])
    if start is not None:
        df = df[df["date"] >= start]
    if end is not None:
        df = df[df["date"] <= end]
    if df.empty:
        return df
    liq = pd.to_numeric(df["adj_close"], errors="coerce") * pd.to_numeric(df["volume"], errors="coerce")
    ranks = (
        pd.DataFrame({"permno": df["permno"], "liq": liq})
        .dropna(subset=["liq"])
        .groupby("permno", as_index=False)["liq"]
        .sum()
        .sort_values("liq", ascending=False)
        .head(int(max(1, top_n)))
    )
    keep = set(int(p) for p in ranks["permno"].tolist())
    out = df[df["permno"].astype(int).isin(keep)].copy()
    out["permno"] = out["permno"].astype(int)
    return out.sort_values(["date", "permno"])


def _load_prices_matrix(
    permnos: list[int],
    prices_path: Path | None,
    patch_path: Path | None,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not permnos:
        return pd.DataFrame(), pd.DataFrame()

    p_list = ",".join(str(int(p)) for p in sorted(set(int(x) for x in permnos)))
    filters = []
    if start is not None:
        filters.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
    if end is not None:
        filters.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
    date_clause = f" AND {' AND '.join(filters)}" if filters else ""

    sources = []
    if prices_path is not None and prices_path.exists():
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno,
                   CAST(adj_close AS DOUBLE) AS adj_close, CAST(total_ret AS DOUBLE) AS total_ret, 0 AS priority
            FROM '{_sql_escape_path(prices_path)}'
            WHERE CAST(permno AS BIGINT) IN ({p_list}) {date_clause}
            """
        )
    if patch_path is not None and patch_path.exists():
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(permno AS BIGINT) AS permno,
                   CAST(adj_close AS DOUBLE) AS adj_close, CAST(total_ret AS DOUBLE) AS total_ret, 1 AS priority
            FROM '{_sql_escape_path(patch_path)}'
            WHERE CAST(permno AS BIGINT) IN ({p_list}) {date_clause}
            """
        )
    if not sources:
        return pd.DataFrame(), pd.DataFrame()

    q = f"""
    WITH src AS (
        {' UNION ALL '.join(sources)}
    ),
    ranked AS (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY date, permno ORDER BY priority DESC) AS rn
        FROM src
    )
    SELECT date, permno, adj_close, total_ret
    FROM ranked WHERE rn=1
    ORDER BY date, permno
    """
    con = duckdb.connect()
    try:
        df = con.execute(q).df()
    finally:
        con.close()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "permno"])
    px = df.pivot(index="date", columns="permno", values="adj_close").sort_index()
    rets = df.pivot(index="date", columns="permno", values="total_ret").sort_index()
    rets = rets.where(rets.notna(), px.pct_change(fill_method=None))
    return px.astype(float), rets.astype(float)


def _save_equity_png(history: pd.DataFrame, png_path: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return False

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.plot(history.index, history["spy_curve"], color="#777777", linewidth=1.2, label="SPY")
    ax.plot(history.index, history["phase13_curve"], color="#ff9f1c", linewidth=1.2, label="Phase13 Governor")
    ax.plot(history.index, history["phase15_curve"], color="#1f77b4", linewidth=1.6, label="Phase15 Alpha")
    ax.set_title("FR-070 Walk-Forward Equity Curves")
    ax.set_ylabel("Equity (start=1.0)")
    ax.set_xlabel("Date")
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left")
    fig.tight_layout()
    temp_path = png_path.with_suffix(png_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        fig.savefig(temp_path, dpi=150)
        os.replace(temp_path, png_path)
    finally:
        plt.close(fig)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 15 FR-070 alpha walk-forward verifier")
    parser.add_argument("--start-date", default="2010-01-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--top-n-universe", type=int, default=300, help="Top liquid names from feature store")
    parser.add_argument("--alpha-top-n", type=int, default=5, help="Entry rank cutoff")
    parser.add_argument("--hysteresis-rank", type=int, default=20, help="Hold rank cutoff")
    parser.add_argument("--cost-bps", type=float, default=5.0, help="Transaction cost in bps")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--features-path", default=str(DEFAULT_FEATURES_PATH))
    parser.add_argument("--macro-path", default=None)
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH))
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH))
    parser.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-png", default=str(DEFAULT_OUTPUT_PNG))
    return parser.parse_args()


def _default_macro_path() -> Path:
    if DEFAULT_MACRO_FEATURES_PATH.exists():
        return DEFAULT_MACRO_FEATURES_PATH
    return DEFAULT_MACRO_FALLBACK_PATH


def _metrics(mod13, ret: pd.Series, curve: pd.Series) -> dict:
    return {
        "cagr": float(mod13.compute_cagr(curve)),
        "sharpe": float(mod13.compute_sharpe(ret)),
        "max_dd": float(mod13.compute_max_drawdown(curve)),
        "ulcer": float(mod13.compute_ulcer_index(curve)),
    }


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    mod13 = _load_phase13_module()
    features_path = _resolve_path(args.features_path, default_path=DEFAULT_FEATURES_PATH)
    macro_path = _resolve_path(args.macro_path, default_path=_default_macro_path())
    liquidity_path = _resolve_path(args.liquidity_path, default_path=DEFAULT_LIQUIDITY_PATH)
    prices_path = _resolve_path(args.prices_path, default_path=DEFAULT_PRICES_PATH)
    patch_path = _resolve_path(args.patch_path, default_path=DEFAULT_PATCH_PATH)
    output_csv = _resolve_path(args.output_csv, default_path=DEFAULT_OUTPUT_CSV)
    output_png = _resolve_path(args.output_png, default_path=DEFAULT_OUTPUT_PNG)

    if features_path is None or macro_path is None:
        raise RuntimeError("Failed to resolve input paths.")

    macro = _load_frame(macro_path, start=start, end=end)
    liquidity = _load_frame(liquidity_path, start=start, end=end) if liquidity_path is not None and liquidity_path.exists() else None
    context = _build_context(macro=macro, liquidity=liquidity)
    if context.empty:
        raise RuntimeError("No macro/liquidity context rows found for selected window.")

    idx = context.index.sort_values()
    mgr = RegimeManager()
    regime_result = mgr.evaluate(context, idx)

    spy_macro = pd.to_numeric(context.get("spy_close", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    spy_fallback = _load_price_series(
        permno=SPY_PERMNO,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    ).reindex(idx)
    spy_close = spy_macro.where(spy_macro.notna(), spy_fallback).ffill()
    if spy_close.notna().sum() == 0:
        raise RuntimeError("Unable to build SPY series.")

    bil_close = _load_price_series(
        permno=BIL_PERMNO,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    ).reindex(idx)
    bil_ret = bil_close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    effr_rate = pd.to_numeric(context.get("effr_rate", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    cash_ret, cash_source = mod13.build_cash_return(idx=idx, bil_ret=bil_ret, effr_rate=effr_rate)

    # Phase 13 baseline.
    phase13 = mod13.run_walkforward(
        governor_state=regime_result.governor_state.reindex(idx),
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=float(args.cost_bps),
    )

    # Phase 15 alpha strategy path.
    features = _load_feature_history(
        features_path=features_path,
        start=start,
        end=end,
        top_n=int(args.top_n_universe),
    )
    if features.empty:
        raise RuntimeError("Feature history is empty for requested period.")
    permnos = sorted(set(int(p) for p in features["permno"].tolist()))
    prices_wide, returns_wide = _load_prices_matrix(
        permnos=permnos,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    )
    if prices_wide.empty or returns_wide.empty:
        raise RuntimeError("Unable to load alpha universe prices/returns.")

    common_idx = prices_wide.index.intersection(idx)
    common_idx = pd.DatetimeIndex(pd.to_datetime(common_idx, errors="coerce", utc=True)).tz_convert(None).normalize()
    prices_wide = prices_wide.reindex(common_idx).sort_index()
    returns_wide = returns_wide.reindex(common_idx).sort_index().fillna(0.0)
    context = context.reindex(common_idx).ffill()
    features["date"] = pd.to_datetime(features["date"], errors="coerce", utc=True).dt.tz_convert(None).dt.normalize()
    features = features[features["date"].isin(common_idx)].copy()

    strat = InvestorCockpitStrategy(
        use_alpha_engine=True,
        alpha_top_n=int(args.alpha_top_n),
        hysteresis_exit_rank=int(args.hysteresis_rank),
        ratchet_stops=True,
    )
    alpha_weights, _, alpha_details = strat.generate_weights(
        prices=prices_wide,
        fundamentals={"feature_history": features},
        macro=context,
    )
    alpha_results = engine.run_simulation(
        target_weights=alpha_weights,
        returns_df=returns_wide,
        cost_bps=float(args.cost_bps) / 10000.0,
    )
    phase15_ret = pd.to_numeric(alpha_results["net_ret"], errors="coerce").reindex(common_idx).fillna(0.0)
    phase15_curve = (1.0 + phase15_ret).cumprod()

    # Benchmarks aligned to alpha index.
    phase13_aligned = phase13.reindex(common_idx).copy()
    spy_ret = pd.to_numeric(spy_close.reindex(common_idx), errors="coerce").pct_change(fill_method=None).fillna(0.0)
    spy_curve = (1.0 + spy_ret).cumprod()

    history = pd.DataFrame(
        {
            "governor_state": regime_result.governor_state.reindex(common_idx).astype(str),
            "cash_source": cash_source.reindex(common_idx).astype(str),
            "spy_ret": spy_ret.astype(float),
            "phase13_ret": pd.to_numeric(phase13_aligned["strategy_ret"], errors="coerce").fillna(0.0),
            "phase15_ret": phase15_ret.astype(float),
            "spy_curve": spy_curve.astype(float),
            "phase13_curve": pd.to_numeric(phase13_aligned["equity_curve"], errors="coerce").ffill(),
            "phase15_curve": phase15_curve.astype(float),
        },
        index=common_idx,
    )
    telem = alpha_details.get("alpha_telemetry")
    if isinstance(telem, pd.DataFrame) and not telem.empty:
        telem = telem.reindex(common_idx)
        for col in ["alpha_score", "entry_trigger", "stop_loss_level", "num_positions", "turnover", "exit_rank", "exit_stop"]:
            if col in telem.columns:
                history[col] = pd.to_numeric(telem[col], errors="coerce")

    m_spy = _metrics(mod13, history["spy_ret"], history["spy_curve"])
    m_p13 = _metrics(mod13, history["phase13_ret"], history["phase13_curve"])
    m_p15 = _metrics(mod13, history["phase15_ret"], history["phase15_curve"])

    table = pd.DataFrame(
        [
            {"Strategy": "SPY", **m_spy},
            {"Strategy": "Phase13_Governor", **m_p13},
            {"Strategy": "Phase15_Alpha", **m_p15},
        ]
    )
    print("\nMoment-of-Truth Comparison:")
    print(
        table.to_string(
            index=False,
            formatters={
                "cagr": lambda x: f"{x:.3%}",
                "sharpe": lambda x: f"{x:.3f}",
                "max_dd": lambda x: f"{x:.3%}",
                "ulcer": lambda x: f"{x:.3f}",
            },
        )
    )

    verdict = (
        np.isfinite(m_p15["cagr"])
        and np.isfinite(m_p13["cagr"])
        and np.isfinite(m_p15["max_dd"])
        and np.isfinite(m_p13["max_dd"])
        and (m_p15["cagr"] >= m_p13["cagr"])
        and (abs(m_p15["max_dd"]) <= abs(m_p13["max_dd"]) + 0.05)
    )
    print(f"\nFR-070 Verdict: {'PASS' if verdict else 'BLOCK'}")

    export = history.reset_index().rename(columns={"index": "date"})
    export["date"] = pd.to_datetime(export["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    _atomic_csv_write(export, output_csv)
    print(f"CSV written: {output_csv}")
    if output_png is not None:
        if _save_equity_png(history=history, png_path=output_png):
            print(f"Equity curve written: {output_png}")
        else:
            print(f"WARNING: could not write equity PNG at {output_png} (matplotlib unavailable).")

    if args.strict and not verdict:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
