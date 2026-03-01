"""
Phase 13 verifier: FR-050 walk-forward regime backtest.

Outputs:
  - data/processed/phase13_walkforward.csv
  - data/processed/phase13_equity_curve.png
"""

from __future__ import annotations

import argparse
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

from utils.metrics import compute_cagr as _metrics_compute_cagr
from utils.metrics import compute_max_drawdown as _metrics_compute_max_drawdown
from utils.metrics import compute_sharpe as _metrics_compute_sharpe
from utils.metrics import compute_turnover as _metrics_compute_turnover
from utils.metrics import compute_ulcer_index as _metrics_compute_ulcer_index

from strategies.regime_manager import RegimeManager


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_MACRO_FALLBACK_PATH = PROCESSED_DIR / "macro.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"
DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "phase13_walkforward.csv"
DEFAULT_OUTPUT_PNG = PROCESSED_DIR / "phase13_equity_curve.png"

SPY_PERMNO = 84398
BIL_PERMNO = 92027


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


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


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


def _load_price_series_from_parquet(
    permno: int,
    prices_path: Path | None,
    patch_path: Path | None,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.Series:
    sources: list[str] = []
    if prices_path is not None and prices_path.exists():
        prices_filter = [f"CAST(permno AS BIGINT) = {permno}"]
        if start is not None:
            prices_filter.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
        if end is not None:
            prices_filter.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(adj_close AS DOUBLE) AS adj_close, 0 AS priority
            FROM '{_sql_escape_path(prices_path)}'
            WHERE {' AND '.join(prices_filter)}
            """
        )
    if patch_path is not None and patch_path.exists():
        patch_filter = [f"CAST(permno AS BIGINT) = {permno}"]
        if start is not None:
            patch_filter.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
        if end is not None:
            patch_filter.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
        sources.append(
            f"""
            SELECT CAST(date AS DATE) AS date, CAST(adj_close AS DOUBLE) AS adj_close, 1 AS priority
            FROM '{_sql_escape_path(patch_path)}'
            WHERE {' AND '.join(patch_filter)}
            """
        )
    if not sources:
        return pd.Series(dtype=float)

    query = f"""
    WITH src AS (
        {' UNION ALL '.join(sources)}
    ),
    ranked AS (
        SELECT date, adj_close, ROW_NUMBER() OVER (PARTITION BY date ORDER BY priority DESC) AS rn
        FROM src
    )
    SELECT date, adj_close
    FROM ranked
    WHERE rn = 1
    ORDER BY date
    """

    con = duckdb.connect()
    try:
        df = con.execute(query).df()
    finally:
        con.close()

    if df.empty:
        return pd.Series(dtype=float)
    idx = pd.to_datetime(df["date"], errors="coerce")
    vals = pd.to_numeric(df["adj_close"], errors="coerce")
    out = pd.Series(vals.values, index=idx, dtype=float)
    out = out[~out.index.isna()]
    return out.sort_index()


def _build_context(macro: pd.DataFrame, liquidity: pd.DataFrame | None) -> pd.DataFrame:
    if liquidity is None or liquidity.empty:
        return macro.copy()

    idx = macro.index.union(liquidity.index).sort_values()
    ctx = macro.reindex(idx).copy()
    liq = liquidity.reindex(idx)
    priority_cols = {"us_net_liquidity_mm", "liquidity_impulse", "repo_spread_bps", "vix_level", "vrp"}
    for col in priority_cols:
        if col in liq.columns:
            liq_col = pd.to_numeric(liq[col], errors="coerce")
            if col in ctx.columns:
                base_col = pd.to_numeric(ctx[col], errors="coerce")
                ctx[col] = liq_col.combine_first(base_col)
            else:
                ctx[col] = liq_col
    for col in liq.columns:
        if col not in ctx.columns:
            ctx[col] = liq[col]
    return ctx


def map_governor_to_signal_weight(governor_state: pd.Series) -> pd.Series:
    g = governor_state.astype(str).str.upper()
    out = pd.Series(0.5, index=g.index, dtype=float)
    out.loc[g == "GREEN"] = 1.0
    out.loc[g == "AMBER"] = 0.5
    out.loc[g == "RED"] = 0.0
    return out


def build_cash_return(
    idx: pd.Index,
    bil_ret: pd.Series | None,
    effr_rate: pd.Series | None,
    flat_annual_rate: float = 0.02,
) -> tuple[pd.Series, pd.Series]:
    bil = pd.Series(np.nan, index=idx, dtype=float)
    if isinstance(bil_ret, pd.Series) and not bil_ret.empty:
        bil = pd.to_numeric(bil_ret, errors="coerce").reindex(idx)

    effr_daily = pd.Series(np.nan, index=idx, dtype=float)
    if isinstance(effr_rate, pd.Series) and not effr_rate.empty:
        er = pd.to_numeric(effr_rate, errors="coerce").reindex(idx).ffill()
        effr_daily = (er / 100.0) / 252.0

    flat_daily = pd.Series(float(flat_annual_rate) / 252.0, index=idx, dtype=float)
    cash_ret = bil.where(bil.notna(), effr_daily)
    cash_ret = cash_ret.where(cash_ret.notna(), flat_daily)

    source = pd.Series("FLAT", index=idx, dtype=object)
    source.loc[effr_daily.notna()] = "EFFR"
    source.loc[bil.notna()] = "BIL"
    return cash_ret.astype(float), source.astype(str)


def compute_drawdown(equity_curve: pd.Series) -> pd.Series:
    eq = pd.to_numeric(equity_curve, errors="coerce")
    peak = eq.cummax()
    dd = (eq / peak) - 1.0
    return dd.astype(float)


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    return float(_metrics_compute_max_drawdown(equity_curve))


def compute_ulcer_index(equity_curve: pd.Series) -> float:
    return float(_metrics_compute_ulcer_index(equity_curve))


def compute_sharpe(daily_ret: pd.Series) -> float:
    return float(_metrics_compute_sharpe(daily_ret, rf_returns=None, periods_per_year=252.0))


def compute_cagr(equity_curve: pd.Series) -> float:
    return float(_metrics_compute_cagr(equity_curve))


def run_walkforward(
    governor_state: pd.Series,
    spy_close: pd.Series,
    cash_ret: pd.Series,
    cost_bps: float,
) -> pd.DataFrame:
    idx = spy_close.index
    signal_weight = map_governor_to_signal_weight(governor_state.reindex(idx).ffill().fillna("AMBER"))
    executed_weight = signal_weight.shift(1).fillna(0.0).clip(lower=0.0, upper=1.0)
    spy_ret = pd.to_numeric(spy_close, errors="coerce").pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
    spy_ret = spy_ret.fillna(0.0)
    cash_ret = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0)

    turnover = _metrics_compute_turnover(executed_weight)
    cost = turnover * float(cost_bps) / 10000.0
    strategy_ret = executed_weight * spy_ret + (1.0 - executed_weight) * cash_ret - cost
    buyhold_ret = spy_ret.copy()

    equity_curve = (1.0 + strategy_ret).cumprod()
    buyhold_curve = (1.0 + buyhold_ret).cumprod()
    drawdown = compute_drawdown(equity_curve)
    buyhold_drawdown = compute_drawdown(buyhold_curve)

    return pd.DataFrame(
        {
            "signal_weight": signal_weight.astype(float),
            "executed_weight": executed_weight.astype(float),
            "spy_ret": spy_ret.astype(float),
            "cash_ret": cash_ret.astype(float),
            "turnover": turnover.astype(float),
            "cost": cost.astype(float),
            "strategy_ret": strategy_ret.astype(float),
            "buyhold_ret": buyhold_ret.astype(float),
            "equity_curve": equity_curve.astype(float),
            "buyhold_curve": buyhold_curve.astype(float),
            "drawdown": drawdown.astype(float),
            "buyhold_drawdown": buyhold_drawdown.astype(float),
        },
        index=idx,
    )


def _save_equity_png(history: pd.DataFrame, png_path: Path) -> bool:
    def _save_with_pillow() -> bool:
        from PIL import Image, ImageDraw

        png_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 1800, 900
        pad = 70
        img = Image.new("RGB", (width, height), color=(248, 249, 251))
        draw = ImageDraw.Draw(img)

        if history.empty:
            draw.text((pad, pad), "FR-050 Equity Curve: no data", fill=(40, 40, 40))
        else:
            idx = history.index
            n = len(idx)
            if n == 1:
                x_map = lambda i: pad
            else:
                x_map = lambda i: int(pad + i * (width - 2 * pad) / (n - 1))
            s = pd.to_numeric(history["equity_curve"], errors="coerce")
            b = pd.to_numeric(history["buyhold_curve"], errors="coerce")
            y_all = pd.concat([s, b], axis=1).stack()
            y_min = float(y_all.min()) if len(y_all) else 0.0
            y_max = float(y_all.max()) if len(y_all) else 1.0
            if y_max <= y_min:
                y_max = y_min + 1.0

            draw.rectangle([pad, pad, width - pad, height - pad], outline=(120, 120, 120), width=1)

            spy_points = []
            strat_points = []
            for i in range(n):
                x = x_map(i)
                sv = s.iloc[i]
                bv = b.iloc[i]
                if not pd.isna(sv):
                    y = int((height - pad) - ((float(sv) - y_min) / (y_max - y_min)) * (height - 2 * pad))
                    strat_points.append((x, y))
                if not pd.isna(bv):
                    y = int((height - pad) - ((float(bv) - y_min) / (y_max - y_min)) * (height - 2 * pad))
                    spy_points.append((x, y))
            if len(spy_points) >= 2:
                draw.line(spy_points, fill=(90, 90, 90), width=2)
            if len(strat_points) >= 2:
                draw.line(strat_points, fill=(31, 119, 180), width=3)

            draw.text((pad, 20), "FR-050 Walk-Forward Equity Curves (Pillow fallback)", fill=(30, 30, 30))
            draw.text((pad, 45), "Blue=Strategy | Gray=SPY Buy&Hold", fill=(60, 60, 60))

        temp_path = png_path.with_suffix(png_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
        try:
            img.save(temp_path, format="PNG")
            os.replace(temp_path, png_path)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
        return True

    try:
        import matplotlib.pyplot as plt
    except Exception:
        print(f"matplotlib unavailable; using Pillow fallback for {png_path}.")
        return _save_with_pillow()

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    ax.plot(history.index, history["buyhold_curve"], color="#666666", linewidth=1.2, label="SPY Buy&Hold")
    ax.plot(history.index, history["equity_curve"], color="#1f77b4", linewidth=1.6, label="FR-050 Strategy")
    ax.set_title("FR-050 Walk-Forward Equity Curves")
    ax.set_ylabel("Equity (start = 1.0)")
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


def _default_macro_path() -> Path:
    if DEFAULT_MACRO_FEATURES_PATH.exists():
        return DEFAULT_MACRO_FEATURES_PATH
    return DEFAULT_MACRO_FALLBACK_PATH


def build_history(
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    macro_path: Path,
    liquidity_path: Path | None,
    prices_path: Path | None,
    patch_path: Path | None,
    cost_bps: float,
) -> pd.DataFrame:
    macro = _load_frame(macro_path, start=start, end=end)
    liquidity = None
    if liquidity_path is not None and liquidity_path.exists():
        liquidity = _load_frame(liquidity_path, start=start, end=end)
    context = _build_context(macro=macro, liquidity=liquidity)
    if context.empty:
        raise RuntimeError("No macro/liquidity context rows found for selected window.")

    idx = context.index.sort_values()
    manager = RegimeManager()
    result = manager.evaluate(context, idx)

    spy_from_macro = pd.to_numeric(context.get("spy_close", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    spy_from_parquet = _load_price_series_from_parquet(
        permno=SPY_PERMNO, prices_path=prices_path, patch_path=patch_path, start=start, end=end
    ).reindex(idx)
    spy_close = spy_from_macro.where(spy_from_macro.notna(), spy_from_parquet).ffill()
    if spy_close.notna().sum() == 0:
        raise RuntimeError("Unable to build SPY close series from macro and price fallbacks.")

    bil_close = _load_price_series_from_parquet(
        permno=BIL_PERMNO, prices_path=prices_path, patch_path=patch_path, start=start, end=end
    ).reindex(idx)
    bil_ret = bil_close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    effr_rate = pd.to_numeric(context.get("effr_rate", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    if effr_rate.notna().sum() == 0 and liquidity is not None and "effr_rate" in liquidity.columns:
        effr_rate = pd.to_numeric(liquidity["effr_rate"], errors="coerce").reindex(idx)
    cash_ret, cash_source = build_cash_return(idx=idx, bil_ret=bil_ret, effr_rate=effr_rate)

    sim = run_walkforward(
        governor_state=result.governor_state.reindex(idx),
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=cost_bps,
    )

    history = pd.DataFrame(
        {
            "governor_state": result.governor_state.reindex(idx).astype(str),
            "reason": result.reason.reindex(idx).astype(str),
            "spy_close": spy_close.astype(float),
            "bil_close": pd.to_numeric(bil_close, errors="coerce"),
            "effr_rate": pd.to_numeric(effr_rate, errors="coerce"),
            "cash_source": cash_source.astype(str),
        },
        index=idx,
    )
    history = pd.concat([history, sim], axis=1)
    return history


def compute_summary(history: pd.DataFrame) -> dict:
    eq = pd.to_numeric(history["equity_curve"], errors="coerce")
    bh = pd.to_numeric(history["buyhold_curve"], errors="coerce")
    strategy_ret = pd.to_numeric(history["strategy_ret"], errors="coerce")
    buyhold_ret = pd.to_numeric(history["buyhold_ret"], errors="coerce")

    total_return_strategy = float(eq.iloc[-1] - 1.0) if len(eq) else float("nan")
    total_return_buyhold = float(bh.iloc[-1] - 1.0) if len(bh) else float("nan")

    summary = {
        "cagr_strategy": compute_cagr(eq),
        "cagr_buyhold": compute_cagr(bh),
        "sharpe_strategy": compute_sharpe(strategy_ret),
        "sharpe_buyhold": compute_sharpe(buyhold_ret),
        "max_dd_strategy": compute_max_drawdown(eq),
        "max_dd_buyhold": compute_max_drawdown(bh),
        "ulcer_strategy": compute_ulcer_index(eq),
        "ulcer_buyhold": compute_ulcer_index(bh),
        "total_return_strategy": total_return_strategy,
        "total_return_buyhold": total_return_buyhold,
    }

    dd_half_bound = abs(summary["max_dd_buyhold"]) * 0.5 if np.isfinite(summary["max_dd_buyhold"]) else float("nan")
    pass_ulcer = bool(np.isfinite(summary["ulcer_strategy"]) and np.isfinite(summary["ulcer_buyhold"]) and summary["ulcer_strategy"] < summary["ulcer_buyhold"])
    pass_dd = bool(np.isfinite(dd_half_bound) and abs(summary["max_dd_strategy"]) < dd_half_bound)
    pass_sharpe = bool(np.isfinite(summary["sharpe_strategy"]) and np.isfinite(summary["sharpe_buyhold"]) and summary["sharpe_strategy"] > summary["sharpe_buyhold"])
    pass_total_return = bool(
        np.isfinite(summary["total_return_strategy"])
        and np.isfinite(summary["total_return_buyhold"])
        and summary["total_return_strategy"] >= summary["total_return_buyhold"]
    )
    overall_pass = bool(pass_ulcer and pass_dd and pass_sharpe)
    summary.update(
        {
            "pass_ulcer": pass_ulcer,
            "pass_maxdd": pass_dd,
            "pass_sharpe": pass_sharpe,
            "pass_total_return": pass_total_return,
            "overall_pass": overall_pass,
        }
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 13 FR-050 walk-forward verifier")
    parser.add_argument("--start-date", default="2000-01-01", help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="Inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--macro-path", default=None, help="Override macro parquet path")
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH), help="Liquidity parquet path")
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH), help="Prices parquet path")
    parser.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH), help="Patch parquet path")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV), help="CSV output path")
    parser.add_argument("--output-png", default=str(DEFAULT_OUTPUT_PNG), help="PNG output path")
    parser.add_argument("--cost-bps", type=float, default=5.0, help="Turnover cost in basis points")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when core FR-050 checks fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    macro_path = _resolve_path(args.macro_path, default_path=_default_macro_path())
    liquidity_path = _resolve_path(args.liquidity_path, default_path=DEFAULT_LIQUIDITY_PATH)
    prices_path = _resolve_path(args.prices_path, default_path=DEFAULT_PRICES_PATH)
    patch_path = _resolve_path(args.patch_path, default_path=DEFAULT_PATCH_PATH)
    output_csv = _resolve_path(args.output_csv, default_path=DEFAULT_OUTPUT_CSV)
    output_png = _resolve_path(args.output_png, default_path=DEFAULT_OUTPUT_PNG)
    if macro_path is None:
        raise RuntimeError("No macro path resolved.")

    history = build_history(
        start=start,
        end=end,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        prices_path=prices_path,
        patch_path=patch_path,
        cost_bps=float(args.cost_bps),
    )
    summary = compute_summary(history)
    fallback_mask = history["reason"].astype(str).str.startswith("Fallback:")
    fallback_ratio = float(fallback_mask.mean()) if len(history) else float("nan")

    print(
        "Built FR-050 history rows="
        f"{len(history):,}, range={history.index.min().date()} -> {history.index.max().date()}, "
        f"final_equity={history['equity_curve'].iloc[-1]:.4f}, "
        f"final_buyhold={history['buyhold_curve'].iloc[-1]:.4f}"
    )

    print("\nFR-050 Summary:")
    print(
        f"  CAGR strategy={summary['cagr_strategy']:.3%}, buyhold={summary['cagr_buyhold']:.3%}\n"
        f"  Sharpe strategy={summary['sharpe_strategy']:.3f}, buyhold={summary['sharpe_buyhold']:.3f}\n"
        f"  MaxDD strategy={summary['max_dd_strategy']:.3%}, buyhold={summary['max_dd_buyhold']:.3%}\n"
        f"  Ulcer strategy={summary['ulcer_strategy']:.3f}, buyhold={summary['ulcer_buyhold']:.3f}\n"
        f"  TotalReturn strategy={summary['total_return_strategy']:.3%}, buyhold={summary['total_return_buyhold']:.3%}"
    )
    print(
        "  Checks: "
        f"ulcer={summary['pass_ulcer']}, maxdd={summary['pass_maxdd']}, "
        f"sharpe={summary['pass_sharpe']}, total_return={summary['pass_total_return']}, "
        f"overall_pass={summary['overall_pass']}"
    )
    print(f"  fallback_ratio={fallback_ratio:.2%}")
    if np.isfinite(fallback_ratio) and fallback_ratio > 0.05:
        print("  WARNING: fallback ratio > 5%; FR-041 input coverage is degraded.")

    if args.strict and not summary["overall_pass"]:
        print("Strict mode: FR-050 core checks not met. Canonical outputs not overwritten.")
        return 2

    export = history.reset_index().rename(columns={"index": "date"})
    export["date"] = pd.to_datetime(export["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    _atomic_csv_write(export, output_csv)
    print(f"CSV written: {output_csv}")

    if output_png is not None:
        try:
            plotted = _save_equity_png(history=history, png_path=output_png)
            if plotted:
                print(f"Equity curve written: {output_png}")
        except Exception as exc:  # defensive: PNG is optional observability artifact
            print(f"WARNING: failed to write equity PNG at {output_png}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
