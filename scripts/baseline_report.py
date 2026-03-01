from __future__ import annotations

import argparse
import importlib.util
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine  # noqa: E402
from utils.metrics import compute_cagr
from utils.metrics import compute_max_drawdown
from utils.metrics import compute_sharpe
from utils.metrics import compute_ulcer_index


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_MACRO_FALLBACK_PATH = PROCESSED_DIR / "macro.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"

DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "phase18_day1_baselines.csv"
DEFAULT_OUTPUT_PLOT = PROCESSED_DIR / "phase18_day1_equity_curves.png"

_FR050_MODULE: ModuleType | None = None
BASELINE_LABELS = {
    "buy_hold_spy": "Buy & Hold SPY",
    "static_50_50": "Static 50/50",
    "trend_sma200": "Trend SMA200",
}


@dataclass(frozen=True)
class BaselineArtifacts:
    equity_curves: pd.DataFrame
    metrics: pd.DataFrame
    details: dict[str, pd.DataFrame]


def _load_fr050_module() -> ModuleType:
    global _FR050_MODULE
    if _FR050_MODULE is not None:
        return _FR050_MODULE

    path = PROJECT_ROOT / "backtests" / "verify_phase13_walkforward.py"
    spec = importlib.util.spec_from_file_location("verify_phase13_walkforward", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load FR-050 helper module at {path}")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _FR050_MODULE = mod
    return mod


def _default_macro_path() -> Path:
    if DEFAULT_MACRO_FEATURES_PATH.exists():
        return DEFAULT_MACRO_FEATURES_PATH
    return DEFAULT_MACRO_FALLBACK_PATH


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


def _atomic_csv_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        df.to_csv(tmp, index=False)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def build_trend_target_weight(
    spy_close: pd.Series,
    risk_off_weight: float = 0.5,
    sma_window: int = 200,
) -> pd.Series:
    if not 0.0 <= float(risk_off_weight) <= 1.0:
        raise ValueError(f"trend risk-off weight must be in [0, 1], got {risk_off_weight}")
    window = max(int(sma_window), 1)

    close = pd.to_numeric(spy_close, errors="coerce")
    sma = close.rolling(window=window, min_periods=window).mean()
    risk_on = close > sma

    out = pd.Series(float(risk_off_weight), index=close.index, dtype=float)
    out.loc[risk_on.fillna(False)] = 1.0
    return out.clip(lower=0.0, upper=1.0)


def simulate_single_baseline(
    name: str,
    target_weight_spy: pd.Series,
    spy_ret: pd.Series,
    cash_ret: pd.Series,
    cost_bps: float,
) -> tuple[pd.DataFrame, dict[str, float | str | int]]:
    idx = pd.DatetimeIndex(pd.to_datetime(target_weight_spy.index, errors="coerce"))
    idx = idx[~idx.isna()]
    idx = idx.sort_values()

    target_spy = pd.to_numeric(target_weight_spy, errors="coerce").reindex(idx).fillna(0.0).clip(lower=0.0, upper=1.0)
    spy = pd.to_numeric(spy_ret, errors="coerce").reindex(idx).fillna(0.0)
    cash = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0)

    # Model only the risky sleeve in the engine so turnover/cost applies to SPY
    # reallocations without charging synthetic "cash trades".
    target_weights = pd.DataFrame({"spy_alloc": target_spy}, index=idx)
    returns_df = pd.DataFrame({"spy_alloc": spy - cash}, index=idx)

    sim = engine.run_simulation(
        target_weights=target_weights,
        returns_df=returns_df,
        cost_bps=float(cost_bps) / 10000.0,
    )
    net_excess_ret = pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    net_ret = cash + net_excess_ret
    equity_curve = (1.0 + net_ret).cumprod()
    executed_weight_spy = target_weights["spy_alloc"].shift(1).fillna(0.0)

    turnover = pd.to_numeric(sim["turnover"], errors="coerce").fillna(0.0)
    start_date = idx.min().strftime("%Y-%m-%d") if len(idx) else ""
    end_date = idx.max().strftime("%Y-%m-%d") if len(idx) else ""
    metrics = {
        "cagr": float(compute_cagr(equity_curve)),
        "sharpe": float(compute_sharpe(net_ret)),
        "max_dd": float(compute_max_drawdown(equity_curve)),
        "ulcer": float(compute_ulcer_index(equity_curve)),
        "turnover_annual": float(turnover.mean() * 252.0),
        "turnover_total": float(turnover.sum()),
        "start_date": start_date,
        "end_date": end_date,
        "n_days": int(len(idx)),
    }

    detail = pd.DataFrame(
        {
            "target_weight_spy": target_weights["spy_alloc"].astype(float),
            "executed_weight_spy": executed_weight_spy.astype(float),
            "spy_ret": spy.astype(float),
            "cash_ret": cash.astype(float),
            "gross_ret": (cash + pd.to_numeric(sim["gross_ret"], errors="coerce").fillna(0.0)).astype(float),
            "net_ret": net_ret.astype(float),
            "turnover": pd.to_numeric(sim["turnover"], errors="coerce").fillna(0.0).astype(float),
            "cost": pd.to_numeric(sim["cost"], errors="coerce").fillna(0.0).astype(float),
            "equity_curve": equity_curve.astype(float),
        },
        index=idx,
    )
    detail.attrs["baseline_name"] = name
    return detail, metrics


def run_baselines(
    spy_close: pd.Series,
    cash_ret: pd.Series,
    cost_bps: float = 5.0,
    trend_risk_off_weight: float = 0.5,
    trend_sma_window: int = 200,
) -> BaselineArtifacts:
    if not 0.0 <= float(trend_risk_off_weight) <= 1.0:
        raise ValueError(f"--trend-risk-off-weight must be in [0, 1], got {trend_risk_off_weight}")

    idx = pd.DatetimeIndex(pd.to_datetime(spy_close.index, errors="coerce"))
    idx = idx[~idx.isna()].sort_values()
    if len(idx) == 0:
        raise RuntimeError("No valid datetime index found in SPY close series.")

    close = pd.to_numeric(spy_close, errors="coerce").reindex(idx).ffill()
    if close.notna().sum() == 0:
        raise RuntimeError("SPY close series is fully empty after alignment.")

    spy_ret = close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    cash = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0)

    targets = {
        "buy_hold_spy": pd.Series(1.0, index=idx, dtype=float),
        "static_50_50": pd.Series(0.5, index=idx, dtype=float),
        "trend_sma200": build_trend_target_weight(
            spy_close=close,
            risk_off_weight=float(trend_risk_off_weight),
            sma_window=int(trend_sma_window),
        ),
    }

    equity_curves = pd.DataFrame(index=idx)
    metrics_rows: list[dict[str, float | str | int]] = []
    details: dict[str, pd.DataFrame] = {}

    for baseline_name, target in targets.items():
        detail, metrics = simulate_single_baseline(
            name=baseline_name,
            target_weight_spy=target,
            spy_ret=spy_ret,
            cash_ret=cash,
            cost_bps=float(cost_bps),
        )
        details[baseline_name] = detail
        equity_curves[baseline_name] = detail["equity_curve"].astype(float)
        metrics_rows.append({"baseline": BASELINE_LABELS.get(baseline_name, baseline_name), **metrics})

    metrics_df = pd.DataFrame(metrics_rows)
    return BaselineArtifacts(
        equity_curves=equity_curves.sort_index(),
        metrics=metrics_df,
        details=details,
    )


def load_market_inputs(
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    macro_path: Path,
    liquidity_path: Path | None,
    prices_path: Path | None,
    patch_path: Path | None,
) -> tuple[pd.Series, pd.Series]:
    fr050 = _load_fr050_module()

    macro = fr050._load_frame(macro_path, start=start, end=end)
    liquidity = None
    if liquidity_path is not None and liquidity_path.exists():
        liquidity = fr050._load_frame(liquidity_path, start=start, end=end)
    context = fr050._build_context(macro=macro, liquidity=liquidity)
    if context.empty:
        raise RuntimeError("No macro/liquidity context rows found for selected window.")

    idx = context.index.sort_values()
    spy_permno = int(getattr(fr050, "SPY_PERMNO", 84398))
    bil_permno = int(getattr(fr050, "BIL_PERMNO", 92027))

    spy_from_macro = pd.to_numeric(context.get("spy_close", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    spy_from_parquet = fr050._load_price_series_from_parquet(
        permno=spy_permno,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    ).reindex(idx)
    spy_close = spy_from_macro.where(spy_from_macro.notna(), spy_from_parquet).ffill()
    if spy_close.notna().sum() == 0:
        raise RuntimeError("Unable to build SPY close series from macro and price fallbacks.")

    bil_close = fr050._load_price_series_from_parquet(
        permno=bil_permno,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    ).reindex(idx)
    bil_ret = pd.to_numeric(bil_close, errors="coerce").pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    effr_rate = pd.to_numeric(context.get("effr_rate", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    if effr_rate.notna().sum() == 0 and liquidity is not None and "effr_rate" in liquidity.columns:
        effr_rate = pd.to_numeric(liquidity["effr_rate"], errors="coerce").reindex(idx)

    cash_ret, _ = fr050.build_cash_return(
        idx=idx,
        bil_ret=bil_ret,
        effr_rate=effr_rate,
        flat_annual_rate=0.02,
    )
    cash_ret = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0)
    return spy_close.astype(float), cash_ret.astype(float)


def _save_equity_overlay_png(equity_curves: pd.DataFrame, png_path: Path) -> bool:
    def _save_with_pillow() -> bool:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            print(f"WARNING: matplotlib and Pillow unavailable; skipping plot output at {png_path}")
            return False

        png_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 1800, 900
        pad = 70
        img = Image.new("RGB", (width, height), color=(248, 249, 251))
        draw = ImageDraw.Draw(img)

        if equity_curves.empty:
            draw.text((pad, pad), "Phase 18 Day 1 Baseline Equity Curves: no data", fill=(40, 40, 40))
        else:
            idx = equity_curves.index
            n = len(idx)
            x_map = (lambda i: pad) if n == 1 else (lambda i: int(pad + i * (width - 2 * pad) / (n - 1)))

            # Approximate log-scale by plotting transformed values.
            safe_curves = equity_curves.apply(pd.to_numeric, errors="coerce").where(lambda f: f > 0.0)
            log_curves = np.log(safe_curves)
            y_all = log_curves.stack()
            y_min = float(y_all.min()) if len(y_all) else 0.0
            y_max = float(y_all.max()) if len(y_all) else 1.0
            if y_max <= y_min:
                y_max = y_min + 1.0

            draw.rectangle([pad, pad, width - pad, height - pad], outline=(120, 120, 120), width=1)
            palette = {
                "buy_hold_spy": (78, 121, 167),
                "static_50_50": (242, 142, 43),
                "trend_sma200": (89, 161, 79),
            }

            for col in equity_curves.columns:
                points = []
                series = log_curves[col] if col in log_curves.columns else pd.Series(dtype=float)
                for i in range(n):
                    v = series.iloc[i]
                    if pd.isna(v):
                        continue
                    x = x_map(i)
                    y = int((height - pad) - ((float(v) - y_min) / (y_max - y_min)) * (height - 2 * pad))
                    points.append((x, y))
                if len(points) >= 2:
                    draw.line(points, fill=palette.get(col, (31, 119, 180)), width=3)

            draw.text((pad, 20), "Phase 18 Day 1 Baseline Equity Curves (log-scale, Pillow fallback)", fill=(30, 30, 30))

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
    except ImportError:
        print(f"matplotlib unavailable; using Pillow fallback for {png_path}.")
        return _save_with_pillow()

    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(14, 7))
    palette = {
        "buy_hold_spy": "#4E79A7",
        "static_50_50": "#F28E2B",
        "trend_sma200": "#59A14F",
    }
    for col in equity_curves.columns:
        series = pd.to_numeric(equity_curves[col], errors="coerce")
        series = series.where(series > 0.0)
        ax.plot(
            equity_curves.index,
            series,
            label=col,
            linewidth=1.6,
            color=palette.get(col),
        )

    ax.set_title("Phase 18 Day 1 Baseline Equity Curves")
    ax.set_ylabel("Equity (start = 1.0)")
    ax.set_xlabel("Date")
    ax.set_yscale("log")
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


def _fmt_pct(value: float, digits: int = 2) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value * 100.0:.{digits}f}%"


def _fmt_num(value: float, digits: int = 3) -> str:
    if not np.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _build_ascii_metrics_table(metrics_df: pd.DataFrame) -> str:
    columns = [
        ("Baseline", "baseline"),
        ("CAGR", "cagr"),
        ("Sharpe", "sharpe"),
        ("MaxDD", "max_dd"),
        ("Ulcer", "ulcer"),
        ("Turnover/yr", "turnover_annual"),
        ("TurnoverTotal", "turnover_total"),
    ]
    rows: list[list[str]] = []
    for _, row in metrics_df.iterrows():
        rows.append(
            [
                str(row.get("baseline", "")),
                _fmt_pct(float(row.get("cagr", np.nan))),
                _fmt_num(float(row.get("sharpe", np.nan)), digits=3),
                _fmt_pct(float(row.get("max_dd", np.nan))),
                _fmt_num(float(row.get("ulcer", np.nan)), digits=3),
                _fmt_num(float(row.get("turnover_annual", np.nan)), digits=4),
                _fmt_num(float(row.get("turnover_total", np.nan)), digits=4),
            ]
        )

    widths = []
    for idx, (title, _) in enumerate(columns):
        cell_width = max([len(title), *[len(r[idx]) for r in rows]] if rows else [len(title)])
        widths.append(cell_width)

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header = "| " + " | ".join(columns[i][0].ljust(widths[i]) for i in range(len(columns))) + " |"
    lines = [border, header, border]
    for row in rows:
        lines.append("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(columns))) + " |")
    lines.append(border)
    return "\n".join(lines)


def _print_institutional_console_report(metrics_df: pd.DataFrame, cost_bps: float, trend_risk_off_weight: float) -> None:
    if metrics_df.empty:
        print("No baseline metrics produced.")
        return
    start_date = str(metrics_df["start_date"].iloc[0])
    end_date = str(metrics_df["end_date"].iloc[0])
    n_days = int(metrics_df["n_days"].iloc[0])
    line = "=" * 78
    print(line)
    print("PHASE 18 DAY 1: INSTITUTIONAL BASELINES")
    print(line)
    print(f"Period: {start_date} to {end_date} ({n_days} trading days)")
    print(f"Transaction Costs: {float(cost_bps):.2f} bps | Execution Lag: T+1 (shift=1)")
    print(line)
    print(_build_ascii_metrics_table(metrics_df))
    print(line)
    print("Risk-Free Hierarchy: BIL -> EFFR/252 -> 2%/252")
    print(f"Trend SMA200 Risk-Off Weight: {float(trend_risk_off_weight) * 100:.1f}%")
    print(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 18 Day 1 baseline benchmarking report")
    parser.add_argument("--start-date", default="2015-01-01", help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default="2024-12-31", help="Inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--cost-bps", type=float, default=5.0, help="Turnover cost in basis points")
    parser.add_argument(
        "--trend-risk-off-weight",
        type=float,
        default=0.5,
        help="Trend baseline SPY weight when SPY <= SMA200 (default: 0.5)",
    )
    parser.add_argument("--trend-sma-window", type=int, default=200, help="Trend filter SMA window")
    parser.add_argument("--macro-path", default=None, help="Override macro parquet path")
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH), help="Liquidity parquet path")
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH), help="Prices parquet path")
    parser.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH), help="Patch parquet path")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV), help="Output metrics CSV path")
    parser.add_argument("--output-plot", default=str(DEFAULT_OUTPUT_PLOT), help="Output equity curve plot path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    if not 0.0 <= float(args.trend_risk_off_weight) <= 1.0:
        raise ValueError("--trend-risk-off-weight must be in [0, 1].")

    macro_path = _resolve_path(args.macro_path, default_path=_default_macro_path())
    liquidity_path = _resolve_path(args.liquidity_path, default_path=DEFAULT_LIQUIDITY_PATH)
    prices_path = _resolve_path(args.prices_path, default_path=DEFAULT_PRICES_PATH)
    patch_path = _resolve_path(args.patch_path, default_path=DEFAULT_PATCH_PATH)
    output_csv = _resolve_path(args.output_csv, default_path=DEFAULT_OUTPUT_CSV)
    output_plot = _resolve_path(args.output_plot, default_path=DEFAULT_OUTPUT_PLOT) if args.output_plot else None

    if macro_path is None or output_csv is None:
        raise RuntimeError("Failed to resolve required file paths.")
    if not macro_path.exists():
        raise FileNotFoundError(f"Missing --macro-path parquet: {macro_path}")
    if prices_path is None or not prices_path.exists():
        raise FileNotFoundError(f"Missing --prices-path parquet: {prices_path}")

    spy_close, cash_ret = load_market_inputs(
        start=start,
        end=end,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        prices_path=prices_path,
        patch_path=patch_path,
    )

    artifacts = run_baselines(
        spy_close=spy_close,
        cash_ret=cash_ret,
        cost_bps=float(args.cost_bps),
        trend_risk_off_weight=float(args.trend_risk_off_weight),
        trend_sma_window=int(args.trend_sma_window),
    )

    metrics_export = artifacts.metrics.copy()
    metrics_export = metrics_export[
        [
            "baseline",
            "cagr",
            "sharpe",
            "max_dd",
            "ulcer",
            "turnover_annual",
            "turnover_total",
            "start_date",
            "end_date",
            "n_days",
        ]
    ]
    _atomic_csv_write(metrics_export, output_csv)

    print(
        "Built baseline report rows="
        f"{len(artifacts.equity_curves):,}, "
        f"range={artifacts.equity_curves.index.min().date()} -> {artifacts.equity_curves.index.max().date()}"
    )
    print()
    _print_institutional_console_report(
        metrics_df=metrics_export,
        cost_bps=float(args.cost_bps),
        trend_risk_off_weight=float(args.trend_risk_off_weight),
    )
    print(f"\nMetrics CSV written: {output_csv}")

    if output_plot is not None:
        if _save_equity_overlay_png(artifacts.equity_curves, output_plot):
            print(f"Plot written: {output_plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
