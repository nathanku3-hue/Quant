from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from core import engine  # noqa: E402
from scripts import baseline_report  # noqa: E402
from strategies.cash_overlay import TrendFollowingOverlay  # noqa: E402
from strategies.cash_overlay import VolatilityTargetOverlay  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "phase18_day3_overlay_metrics.csv"
DEFAULT_OUTPUT_PLOT = PROCESSED_DIR / "phase18_day3_overlay_3panel.png"
DEFAULT_OUTPUT_STRESS_CSV = PROCESSED_DIR / "phase18_day3_overlay_stress_checks.csv"
DEFAULT_OUTPUT_CORR_CSV = PROCESSED_DIR / "phase18_day3_overlay_exposure_corr.csv"

DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_MACRO_TRI_PATH = PROCESSED_DIR / "macro_features_tri.parquet"
DEFAULT_MACRO_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"

SPY_PERMNO = 84398


@dataclass(frozen=True)
class Day3Inputs:
    spy_tri: pd.Series
    spy_ret: pd.Series
    cash_ret: pd.Series
    macro: pd.DataFrame


def _to_ts(value: str | None) -> pd.Timestamp | None:
    if value is None:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"Invalid date value: {value}")
    return pd.Timestamp(ts).normalize()


def _resolve_path(value: str | None, default_path: Path | None = None) -> Path | None:
    if value is None:
        return default_path
    p = Path(value)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def _sql_escape_path(path: Path) -> str:
    return str(path).replace("\\", "/").replace("'", "''")


def _atomic_csv_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        df.to_csv(tmp, index=False)
        for i in range(tries):
            try:
                os.replace(tmp, path)
                return
            except PermissionError:
                if i >= tries - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _load_macro_frame(path: Path, start: pd.Timestamp | None, end: pd.Timestamp | None) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    macro = pd.read_parquet(path)
    if macro.empty or "date" not in macro.columns:
        return pd.DataFrame()
    macro = macro.copy()
    macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
    macro = macro.dropna(subset=["date"]).sort_values("date")
    if start is not None:
        macro = macro[macro["date"] >= start]
    if end is not None:
        macro = macro[macro["date"] <= end]
    if macro.empty:
        return pd.DataFrame()
    return macro.set_index("date").sort_index()


def _load_spy_tri_from_prices_tri(
    prices_tri_path: Path,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> tuple[pd.Series, pd.Series] | None:
    if not prices_tri_path.exists():
        return None
    con = duckdb.connect()
    try:
        where = [f"CAST(permno AS BIGINT) = {SPY_PERMNO}"]
        if start is not None:
            where.append(f"CAST(date AS DATE) >= DATE '{start.strftime('%Y-%m-%d')}'")
        if end is not None:
            where.append(f"CAST(date AS DATE) <= DATE '{end.strftime('%Y-%m-%d')}'")
        where_sql = " AND ".join(where)
        df = con.execute(
            f"""
            SELECT
                CAST(date AS DATE) AS date,
                CAST(tri AS DOUBLE) AS tri,
                CAST(total_ret AS DOUBLE) AS total_ret
            FROM '{_sql_escape_path(prices_tri_path)}'
            WHERE {where_sql}
            ORDER BY date
            """
        ).df()
    finally:
        con.close()
    if df.empty:
        return None
    idx = pd.to_datetime(df["date"], errors="coerce")
    tri = pd.to_numeric(df["tri"], errors="coerce")
    ret = pd.to_numeric(df["total_ret"], errors="coerce")
    out_tri = pd.Series(tri.values, index=idx, name="spy_tri").dropna().sort_index()
    out_ret = pd.Series(ret.values, index=idx, name="spy_ret").reindex(out_tri.index).fillna(0.0)
    return out_tri.astype(float), out_ret.astype(float)


def _load_inputs(
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    prices_tri_path: Path,
    macro_tri_path: Path,
    macro_path: Path,
    liquidity_path: Path,
    prices_path: Path,
    patch_path: Path | None,
) -> Day3Inputs:
    macro = _load_macro_frame(macro_tri_path if macro_tri_path.exists() else macro_path, start=start, end=end)

    spy_pair = _load_spy_tri_from_prices_tri(prices_tri_path, start=start, end=end)
    if spy_pair is None:
        if macro.empty or ("spy_tri" not in macro.columns and "spy_close" not in macro.columns):
            raise RuntimeError("Unable to load SPY TRI inputs from prices_tri.parquet or macro features.")
        spy_col = "spy_tri" if "spy_tri" in macro.columns else "spy_close"
        spy_tri = pd.to_numeric(macro[spy_col], errors="coerce").dropna().sort_index()
        spy_ret = spy_tri.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    else:
        spy_tri, spy_ret = spy_pair

    idx = pd.DatetimeIndex(spy_tri.index).sort_values()
    if len(idx) == 0:
        raise RuntimeError("No SPY TRI rows available in requested window.")

    fr050 = baseline_report._load_fr050_module()
    liq = None
    if liquidity_path.exists():
        liq = fr050._load_frame(liquidity_path, start=start, end=end)
    if macro.empty:
        macro_for_ctx = pd.DataFrame(index=idx)
    else:
        macro_for_ctx = macro.copy()
        if not isinstance(macro_for_ctx.index, pd.DatetimeIndex):
            macro_for_ctx.index = pd.to_datetime(macro_for_ctx.index, errors="coerce")
            macro_for_ctx = macro_for_ctx[~macro_for_ctx.index.isna()].sort_index()
    context = fr050._build_context(macro=macro_for_ctx, liquidity=liq)
    context = context.reindex(idx)

    bil_permno = int(getattr(fr050, "BIL_PERMNO", 92027))
    bil_close = fr050._load_price_series_from_parquet(
        permno=bil_permno,
        prices_path=prices_path,
        patch_path=patch_path,
        start=start,
        end=end,
    ).reindex(idx)
    bil_ret = pd.to_numeric(bil_close, errors="coerce").pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)

    effr_rate = pd.to_numeric(context.get("effr_rate", pd.Series(index=idx, dtype=float)), errors="coerce").reindex(idx)
    if effr_rate.notna().sum() == 0 and liq is not None and "effr_rate" in liq.columns:
        effr_rate = pd.to_numeric(liq["effr_rate"], errors="coerce").reindex(idx)

    cash_ret, _ = fr050.build_cash_return(
        idx=idx,
        bil_ret=bil_ret,
        effr_rate=effr_rate,
        flat_annual_rate=0.02,
    )
    cash_ret = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0).astype(float)

    macro_aligned = macro.reindex(idx).ffill() if not macro.empty else pd.DataFrame(index=idx)
    return Day3Inputs(
        spy_tri=spy_tri.reindex(idx).ffill().astype(float),
        spy_ret=spy_ret.reindex(idx).fillna(0.0).astype(float),
        cash_ret=cash_ret,
        macro=macro_aligned,
    )


def simulate_overlay_strategy(
    name: str,
    target_exposure: pd.Series,
    spy_ret: pd.Series,
    cash_ret: pd.Series,
    cost_bps: float = 5.0,
) -> pd.DataFrame:
    idx = pd.DatetimeIndex(target_exposure.index).intersection(pd.DatetimeIndex(spy_ret.index)).intersection(
        pd.DatetimeIndex(cash_ret.index)
    )
    idx = idx.sort_values()
    if len(idx) == 0:
        return pd.DataFrame(
            columns=[
                "date",
                "scenario",
                "exposure_target",
                "exposure_executed",
                "spy_ret",
                "cash_ret",
                "risk_component",
                "cash_component",
                "turnover",
                "cost",
                "net_return",
                "equity",
            ]
        )

    target = pd.to_numeric(target_exposure, errors="coerce").reindex(idx).ffill().fillna(0.0).clip(lower=0.0, upper=1.0)
    spy = pd.to_numeric(spy_ret, errors="coerce").reindex(idx).fillna(0.0)
    cash = pd.to_numeric(cash_ret, errors="coerce").reindex(idx).fillna(0.0)

    target_df = pd.DataFrame({"spy_alloc": target}, index=idx)
    ret_df = pd.DataFrame({"spy_alloc": spy - cash}, index=idx)
    sim = engine.run_simulation(
        target_weights=target_df,
        returns_df=ret_df,
        cost_bps=float(cost_bps) / 10000.0,
    )
    executed = target_df["spy_alloc"].shift(1).fillna(0.0)
    risk_component = executed * spy
    cash_component = (1.0 - executed) * cash
    net_ret = cash + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
    equity = (1.0 + net_ret).cumprod()

    out = pd.DataFrame(
        {
            "date": idx,
            "scenario": name,
            "exposure_target": target.astype(float),
            "exposure_executed": executed.astype(float),
            "spy_ret": spy.astype(float),
            "cash_ret": cash.astype(float),
            "risk_component": risk_component.astype(float),
            "cash_component": cash_component.astype(float),
            "turnover": pd.to_numeric(sim["turnover"], errors="coerce").fillna(0.0).astype(float),
            "cost": pd.to_numeric(sim["cost"], errors="coerce").fillna(0.0).astype(float),
            "net_return": net_ret.astype(float),
            "equity": equity.astype(float),
        }
    )
    return out


def run_scenarios(
    data: Day3Inputs,
    target_vol: float,
    vol_lookbacks: list[int],
    cost_bps: float,
) -> dict[str, pd.DataFrame]:
    spy_tri = data.spy_tri
    spy_ret = data.spy_ret
    cash_ret = data.cash_ret
    macro = data.macro

    scenarios: dict[str, pd.DataFrame] = {}

    exp_buy_hold = pd.Series(1.0, index=spy_tri.index, dtype=float)
    scenarios["Buy & Hold"] = simulate_overlay_strategy(
        name="Buy & Hold",
        target_exposure=exp_buy_hold,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=cost_bps,
    )

    exp_trend_sma200 = baseline_report.build_trend_target_weight(
        spy_close=spy_tri,
        risk_off_weight=0.5,
        sma_window=200,
    )
    scenarios["Trend SMA200"] = simulate_overlay_strategy(
        name="Trend SMA200",
        target_exposure=exp_trend_sma200,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=cost_bps,
    )

    for lookback in vol_lookbacks:
        overlay = VolatilityTargetOverlay(
            target_vol=float(target_vol),
            lookback_window=int(lookback),
            max_leverage=1.0,
        )
        exp = overlay.compute_exposure(
            spy_tri=spy_tri,
            spy_returns=spy_ret,
            macro=macro,
        )
        name = overlay.get_name()
        scenarios[name] = simulate_overlay_strategy(
            name=name,
            target_exposure=exp,
            spy_ret=spy_ret,
            cash_ret=cash_ret,
            cost_bps=cost_bps,
        )

    trend_multi = TrendFollowingOverlay(
        ma_windows=[50, 100, 200],
        ma_weights=[0.5, 0.3, 0.2],
    )
    exp_multi = trend_multi.compute_exposure(
        spy_tri=spy_tri,
        spy_returns=spy_ret,
        macro=macro,
    )
    name_multi = "Trend Multi-Horizon"
    scenarios[name_multi] = simulate_overlay_strategy(
        name=name_multi,
        target_exposure=exp_multi,
        spy_ret=spy_ret,
        cash_ret=cash_ret,
        cost_bps=cost_bps,
    )
    return scenarios


def compute_metrics_summary(scenarios: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict[str, float | str | int]] = []
    for name, df in scenarios.items():
        if df.empty:
            continue
        r = pd.to_numeric(df["net_return"], errors="coerce").fillna(0.0)
        eq = pd.to_numeric(df["equity"], errors="coerce").fillna(1.0)
        turnover = pd.to_numeric(df["turnover"], errors="coerce").fillna(0.0)
        ann_vol = float(r.std(ddof=0) * np.sqrt(252.0)) if len(r) else np.nan
        rows.append(
            {
                "scenario": name,
                "cagr": float(compute_cagr(eq)),
                "ann_vol": ann_vol,
                "sharpe": float(compute_sharpe(r)),
                "max_dd": float(compute_max_drawdown(eq)),
                "ulcer": float(compute_ulcer_index(eq)),
                "turnover_annual": float(turnover.mean() * 252.0),
                "turnover_total": float(turnover.sum()),
                "exposure_time": float((pd.to_numeric(df["exposure_executed"], errors="coerce").fillna(0.0) > 0.0).mean()),
                "start_date": pd.Timestamp(df["date"].min()).strftime("%Y-%m-%d"),
                "end_date": pd.Timestamp(df["date"].max()).strftime("%Y-%m-%d"),
                "n_days": int(len(df)),
            }
        )
    return pd.DataFrame(rows)


def build_stress_checks(scenarios: dict[str, pd.DataFrame]) -> pd.DataFrame:
    windows = [
        ("covid_crash", "2020-02-19", "2020-03-23"),
        ("inflation_shock", "2022-01-03", "2022-06-16"),
        ("low_vol_meltup", "2017-01-03", "2017-12-29"),
        ("rate_hikes_q4", "2018-10-01", "2018-12-24"),
    ]
    rows: list[dict[str, object]] = []
    for name, df in scenarios.items():
        if df.empty:
            continue
        for label, s, e in windows:
            mask = (df["date"] >= pd.Timestamp(s)) & (df["date"] <= pd.Timestamp(e))
            sub = df.loc[mask].copy()
            if sub.empty:
                continue
            exp = pd.to_numeric(sub["exposure_executed"], errors="coerce").fillna(0.0)
            eq = pd.to_numeric(sub["equity"], errors="coerce")
            max_dd = np.nan
            if eq.notna().any():
                peak = eq.cummax()
                dd = (eq / peak) - 1.0
                max_dd = float(dd.min())
            rows.append(
                {
                    "scenario": name,
                    "window": label,
                    "start": s,
                    "end": e,
                    "exposure_min": float(exp.min()),
                    "exposure_mean": float(exp.mean()),
                    "exposure_max": float(exp.max()),
                    "window_max_dd": max_dd,
                }
            )
    return pd.DataFrame(rows)


def build_exposure_corr(scenarios: dict[str, pd.DataFrame]) -> pd.DataFrame:
    frame = pd.DataFrame()
    for name, df in scenarios.items():
        if df.empty:
            continue
        s = pd.to_numeric(df.set_index("date")["exposure_executed"], errors="coerce")
        frame[name] = s
    if frame.empty:
        return pd.DataFrame()
    corr = frame.corr(min_periods=30)
    return corr


def _draw_panel_lines(
    draw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    series_map: dict[str, pd.Series],
    color_map: dict[str, tuple[int, int, int]],
    value_min: float | None = None,
    value_max: float | None = None,
) -> None:
    draw.rectangle([x0, y0, x1, y1], outline=(145, 145, 145), width=1)
    if not series_map:
        return
    vals = []
    for s in series_map.values():
        vals.extend(pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna().tolist())
    if not vals:
        return
    y_min = float(np.min(vals)) if value_min is None else float(value_min)
    y_max = float(np.max(vals)) if value_max is None else float(value_max)
    if y_max <= y_min:
        y_max = y_min + 1.0

    # Common x-axis uses the union date index length.
    base_idx = None
    for s in series_map.values():
        if base_idx is None or len(s.index) > len(base_idx):
            base_idx = pd.DatetimeIndex(s.index)
    if base_idx is None or len(base_idx) == 0:
        return
    n = len(base_idx)

    def _x(i: int) -> int:
        if n <= 1:
            return x0 + 6
        return int((x0 + 6) + (i / (n - 1)) * ((x1 - 6) - (x0 + 6)))

    def _y(v: float) -> int:
        return int((y1 - 6) - ((v - y_min) / (y_max - y_min)) * ((y1 - 6) - (y0 + 6)))

    for name, s in series_map.items():
        color = color_map.get(name, (35, 99, 168))
        aligned = pd.to_numeric(s.reindex(base_idx), errors="coerce")
        pts = []
        for i in range(n):
            v = aligned.iloc[i]
            if not np.isfinite(v):
                continue
            pts.append((_x(i), _y(float(v))))
        if len(pts) >= 2:
            draw.line(pts, fill=color, width=2)


def generate_3panel_plot(
    scenarios: dict[str, pd.DataFrame],
    spy_tri: pd.Series,
    output_path: Path,
) -> bool:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        plt = None

    palette_hex = {
        "Buy & Hold": "#4E79A7",
        "Trend SMA200": "#F28E2B",
        "Vol Target 15% (20d)": "#59A14F",
        "Vol Target 15% (60d)": "#E15759",
        "Vol Target 15% (120d)": "#76B7B2",
        "Trend Multi-Horizon": "#EDC948",
    }

    if plt is not None:
        fig = None
        tmp = None
        try:
            fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)

            ax1 = axes[0]
            for name, df in scenarios.items():
                s = pd.to_numeric(df.set_index("date")["equity"], errors="coerce")
                s = s.where(s > 0.0)
                ax1.plot(s.index, s.values, label=name, linewidth=1.4, color=palette_hex.get(name))
            ax1.set_yscale("log")
            ax1.set_ylabel("Equity (log)")
            ax1.set_title("Phase 18 Day 3: Cash Overlay Comparison (2015-2024)")
            ax1.grid(alpha=0.25)
            ax1.legend(loc="upper left", fontsize=8)

            ax2 = axes[1]
            for name, df in scenarios.items():
                eq = pd.to_numeric(df.set_index("date")["equity"], errors="coerce")
                peak = eq.cummax()
                dd = (eq / peak) - 1.0
                ax2.plot(dd.index, dd.values * 100.0, label=name, linewidth=1.2, color=palette_hex.get(name))
            ax2.axhline(0.0, color="#333333", linewidth=0.9)
            ax2.set_ylabel("Drawdown (%)")
            ax2.grid(alpha=0.25)

            ax3 = axes[2]
            ax3r = ax3.twinx()
            for name, df in scenarios.items():
                if name == "Buy & Hold":
                    continue
                ex = pd.to_numeric(df.set_index("date")["exposure_executed"], errors="coerce")
                ax3.plot(ex.index, ex.values, label=name, linewidth=1.2, color=palette_hex.get(name))
            spy = pd.to_numeric(spy_tri, errors="coerce")
            ax3r.plot(spy.index, spy.values, label="SPY TRI", color="#808080", linewidth=1.4, alpha=0.6)
            ax3.set_ylim(0.0, 1.05)
            ax3.set_ylabel("Executed Exposure")
            ax3r.set_ylabel("SPY TRI", color="#808080")
            ax3r.tick_params(axis="y", colors="#808080")
            ax3.grid(alpha=0.25)
            ax3.set_xlabel("Date")
            ax3.legend(loc="upper left", fontsize=8)
            ax3r.legend(loc="upper right", fontsize=8)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = output_path.with_suffix(output_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
            fig.tight_layout()
            fig.savefig(tmp, dpi=150)
            os.replace(tmp, output_path)
            return True
        except Exception:
            # Fall through to Pillow fallback if matplotlib runtime fails.
            pass
        finally:
            if fig is not None:
                plt.close(fig)
            if tmp is not None and tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return False

    color_map = {
        k: tuple(int(palette_hex[k].lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        for k in palette_hex
    }

    width, height = 1700, 1200
    pad = 28
    panel_gap = 16
    panel_h = int((height - (2 * pad) - (2 * panel_gap)) / 3)
    img = Image.new("RGB", (width, height), color=(248, 249, 251))
    draw = ImageDraw.Draw(img)
    draw.text((pad, 6), "Phase 18 Day 3: Cash Overlay Comparison (Pillow fallback)", fill=(20, 20, 20))

    p1 = (pad, pad + 18, width - pad, pad + 18 + panel_h)
    p2 = (pad, p1[3] + panel_gap, width - pad, p1[3] + panel_gap + panel_h)
    p3 = (pad, p2[3] + panel_gap, width - pad, p2[3] + panel_gap + panel_h)

    eq_map = {k: pd.to_numeric(v.set_index("date")["equity"], errors="coerce") for k, v in scenarios.items()}
    eq_log_map = {k: np.log(s.where(s > 0.0)) for k, s in eq_map.items()}
    _draw_panel_lines(draw, *p1, eq_log_map, color_map)
    draw.text((p1[0] + 8, p1[1] + 6), "Panel 1: Equity (log)", fill=(30, 30, 30))

    dd_map = {}
    for k, s in eq_map.items():
        peak = s.cummax()
        dd_map[k] = ((s / peak) - 1.0) * 100.0
    _draw_panel_lines(draw, *p2, dd_map, color_map)
    draw.text((p2[0] + 8, p2[1] + 6), "Panel 2: Underwater (drawdown %)", fill=(30, 30, 30))

    ex_map = {}
    for k, v in scenarios.items():
        if k == "Buy & Hold":
            continue
        ex_map[k] = pd.to_numeric(v.set_index("date")["exposure_executed"], errors="coerce")
    ex_map["SPY TRI"] = pd.to_numeric(spy_tri, errors="coerce")
    color_map["SPY TRI"] = (120, 120, 120)
    _draw_panel_lines(draw, *p3, ex_map, color_map)
    draw.text((p3[0] + 8, p3[1] + 6), "Panel 3: Executed Exposure + SPY TRI", fill=(30, 30, 30))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_suffix(output_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    tries = 8
    try:
        img.save(tmp, format="PNG")
        for i in range(tries):
            try:
                os.replace(tmp, output_path)
                return True
            except PermissionError:
                if i >= tries - 1:
                    raise
                time.sleep(0.15 * (i + 1))
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass


def _fmt_pct(v: float, d: int = 2) -> str:
    if not np.isfinite(v):
        return "nan"
    return f"{100.0 * v:.{d}f}%"


def _fmt_num(v: float, d: int = 3) -> str:
    if not np.isfinite(v):
        return "nan"
    return f"{v:.{d}f}"


def _build_ascii_metrics_table(metrics_df: pd.DataFrame) -> str:
    cols = [
        ("Scenario", "scenario"),
        ("CAGR", "cagr"),
        ("Sharpe", "sharpe"),
        ("MaxDD", "max_dd"),
        ("Ulcer", "ulcer"),
        ("Turn/Yr", "turnover_annual"),
        ("TotalTurn", "turnover_total"),
    ]
    rows = []
    for _, r in metrics_df.iterrows():
        rows.append(
            [
                str(r.get("scenario", "")),
                _fmt_pct(float(r.get("cagr", np.nan)), 2),
                _fmt_num(float(r.get("sharpe", np.nan)), 3),
                _fmt_pct(float(r.get("max_dd", np.nan)), 2),
                _fmt_num(float(r.get("ulcer", np.nan)), 3),
                _fmt_num(float(r.get("turnover_annual", np.nan)), 3),
                _fmt_num(float(r.get("turnover_total", np.nan)), 3),
            ]
        )
    widths = [len(c[0]) for c in cols]
    for row in rows:
        for i, v in enumerate(row):
            widths[i] = max(widths[i], len(v))

    border = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header = "| " + " | ".join(cols[i][0].ljust(widths[i]) for i in range(len(cols))) + " |"
    lines = [border, header, border]
    for row in rows:
        lines.append("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(cols))) + " |")
    lines.append(border)
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 18 Day 3 cash overlay report")
    p.add_argument("--start-date", default="2015-01-01", help="Inclusive start date (YYYY-MM-DD)")
    p.add_argument("--end-date", default="2024-12-31", help="Inclusive end date (YYYY-MM-DD)")
    p.add_argument("--cost-bps", type=float, default=5.0, help="Turnover cost in basis points")
    p.add_argument("--target-vol", type=float, default=0.15, help="Volatility target (annualized decimal)")
    p.add_argument("--vol-lookbacks", default="20,60,120", help="Comma-separated vol lookbacks")
    p.add_argument("--prices-tri-path", default=str(DEFAULT_PRICES_TRI_PATH), help="prices_tri parquet path")
    p.add_argument("--macro-tri-path", default=str(DEFAULT_MACRO_TRI_PATH), help="macro_features_tri parquet path")
    p.add_argument("--macro-path", default=str(DEFAULT_MACRO_PATH), help="macro_features parquet fallback")
    p.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH), help="liquidity features path")
    p.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH), help="base prices path for cash hierarchy support")
    p.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH), help="patch prices path for cash hierarchy support")
    p.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV), help="Metrics CSV output")
    p.add_argument("--output-plot", default=str(DEFAULT_OUTPUT_PLOT), help="3-panel plot output")
    p.add_argument("--output-stress-csv", default=str(DEFAULT_OUTPUT_STRESS_CSV), help="Stress checks CSV output")
    p.add_argument("--output-corr-csv", default=str(DEFAULT_OUTPUT_CORR_CSV), help="Exposure correlation CSV output")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")

    lookbacks = [int(x.strip()) for x in str(args.vol_lookbacks).split(",") if str(x).strip()]
    if not lookbacks:
        raise ValueError("No vol lookbacks provided")

    prices_tri_path = _resolve_path(args.prices_tri_path, DEFAULT_PRICES_TRI_PATH)
    macro_tri_path = _resolve_path(args.macro_tri_path, DEFAULT_MACRO_TRI_PATH)
    macro_path = _resolve_path(args.macro_path, DEFAULT_MACRO_PATH)
    liquidity_path = _resolve_path(args.liquidity_path, DEFAULT_LIQUIDITY_PATH)
    prices_path = _resolve_path(args.prices_path, DEFAULT_PRICES_PATH)
    patch_path = _resolve_path(args.patch_path, DEFAULT_PATCH_PATH)
    output_csv = _resolve_path(args.output_csv, DEFAULT_OUTPUT_CSV)
    output_plot = _resolve_path(args.output_plot, DEFAULT_OUTPUT_PLOT)
    output_stress_csv = _resolve_path(args.output_stress_csv, DEFAULT_OUTPUT_STRESS_CSV)
    output_corr_csv = _resolve_path(args.output_corr_csv, DEFAULT_OUTPUT_CORR_CSV)

    if prices_path is None or not prices_path.exists():
        raise FileNotFoundError(f"Missing prices path: {prices_path}")
    if macro_path is None:
        raise RuntimeError("Failed to resolve macro path")
    if prices_tri_path is None:
        raise RuntimeError("Failed to resolve prices_tri path")
    if macro_tri_path is None:
        raise RuntimeError("Failed to resolve macro_tri path")
    if output_csv is None or output_plot is None:
        raise RuntimeError("Failed to resolve output paths")

    print("=" * 80)
    print("PHASE 18 DAY 3: CASH OVERLAY ANALYSIS")
    print("=" * 80)
    print(
        f"Window: {start.strftime('%Y-%m-%d') if start is not None else 'min'} -> "
        f"{end.strftime('%Y-%m-%d') if end is not None else 'max'}"
    )
    print(f"Vol target: {float(args.target_vol):.2%} | Lookbacks: {lookbacks} | Cost: {float(args.cost_bps):.2f} bps")

    inputs = _load_inputs(
        start=start,
        end=end,
        prices_tri_path=prices_tri_path,
        macro_tri_path=macro_tri_path,
        macro_path=macro_path,
        liquidity_path=liquidity_path if liquidity_path is not None else DEFAULT_LIQUIDITY_PATH,
        prices_path=prices_path,
        patch_path=patch_path,
    )

    scenarios = run_scenarios(
        data=inputs,
        target_vol=float(args.target_vol),
        vol_lookbacks=lookbacks,
        cost_bps=float(args.cost_bps),
    )
    metrics = compute_metrics_summary(scenarios)
    if metrics.empty:
        raise RuntimeError("No scenario metrics generated")
    _atomic_csv_write(metrics, output_csv)

    stress = build_stress_checks(scenarios)
    if output_stress_csv is not None:
        _atomic_csv_write(stress, output_stress_csv)

    corr = build_exposure_corr(scenarios)
    if output_corr_csv is not None:
        corr_out = corr.reset_index().rename(columns={"index": "scenario"})
        _atomic_csv_write(corr_out, output_corr_csv)

    ok_plot = generate_3panel_plot(scenarios=scenarios, spy_tri=inputs.spy_tri, output_path=output_plot)

    print("\n" + _build_ascii_metrics_table(metrics))
    if not stress.empty:
        covid = stress[stress["window"] == "covid_crash"].copy()
        if not covid.empty:
            print("\nCOVID window min exposure by scenario:")
            for _, r in covid.sort_values("scenario").iterrows():
                print(f"  - {r['scenario']}: min={float(r['exposure_min']):.3f}, mean={float(r['exposure_mean']):.3f}")

    if not corr.empty and "Trend Multi-Horizon" in corr.columns:
        for col in corr.columns:
            if col.startswith("Vol Target"):
                val = corr.loc["Trend Multi-Horizon", col] if "Trend Multi-Horizon" in corr.index else np.nan
                if np.isfinite(val):
                    print(f"Exposure corr(Trend Multi-Horizon, {col}) = {float(val):.3f}")

    print(f"\nMetrics CSV written: {output_csv}")
    if output_stress_csv is not None:
        print(f"Stress CSV written:  {output_stress_csv}")
    if output_corr_csv is not None:
        print(f"Corr CSV written:    {output_corr_csv}")
    if ok_plot:
        print(f"3-panel plot written: {output_plot}")
    else:
        print(f"3-panel plot skipped (matplotlib/Pillow unavailable): {output_plot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
