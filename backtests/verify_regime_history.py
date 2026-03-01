"""
Phase 12 verifier: recompute FR-042 regime history and produce diagnostics.

Outputs:
  - CSV history (default: data/processed/regime_history.csv)
  - Optional overlay plot (default: data/processed/regime_overlay.png)
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

from strategies.regime_manager import RegimeManager


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_MACRO_FEATURES_PATH = PROCESSED_DIR / "macro_features.parquet"
DEFAULT_MACRO_FALLBACK_PATH = PROCESSED_DIR / "macro.parquet"
DEFAULT_LIQUIDITY_PATH = PROCESSED_DIR / "liquidity_features.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_PATCH_PATH = PROCESSED_DIR / "yahoo_patch.parquet"
DEFAULT_OUTPUT_CSV = PROCESSED_DIR / "regime_history.csv"
DEFAULT_OUTPUT_OVERLAY = PROCESSED_DIR / "regime_overlay.png"

SPY_PERMNO = 84398

WINDOWS = {
    "2008Q4": ("2008-10-01", "2008-12-31"),
    "2020-03": ("2020-03-01", "2020-03-31"),
    "2022H1": ("2022-01-01", "2022-06-30"),
    "2017": ("2017-01-01", "2017-12-31"),
    "2023-11": ("2023-11-01", "2023-11-30"),
}

WINDOW_EXPECTED = {
    "2008Q4": "RED >= 80% and GREEN == 0%",
    "2020-03": "RED >= 85% and GREEN == 0%",
    "2022H1": "(AMBER + RED) >= 75% and RED >= 15%",
    "2017": "GREEN >= 75% and RED <= 5%",
    "2023-11": "GREEN(last 10) > GREEN(first 10) and RED <= 20%",
}

CRISIS_WINDOWS = ("2008Q4", "2020-03", "2022H1")


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


def _load_spy_from_prices(
    prices_path: Path | None,
    patch_path: Path | None,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.Series:
    sources: list[str] = []
    if prices_path is not None and prices_path.exists():
        prices_filter = [f"CAST(permno AS BIGINT) = {SPY_PERMNO}"]
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
        patch_filter = [f"CAST(permno AS BIGINT) = {SPY_PERMNO}"]
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
        return pd.Series(dtype=float, name="spy_close")

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
        return pd.Series(dtype=float, name="spy_close")

    idx = pd.to_datetime(df["date"], errors="coerce")
    vals = pd.to_numeric(df["adj_close"], errors="coerce")
    out = pd.Series(vals.values, index=idx, name="spy_close")
    out = out[~out.index.isna()]
    return out.sort_index()


def _build_context(
    macro: pd.DataFrame,
    liquidity: pd.DataFrame | None,
) -> pd.DataFrame:
    if liquidity is None or liquidity.empty:
        return macro.copy()

    idx = macro.index.union(liquidity.index).sort_values()
    ctx = macro.reindex(idx).copy()
    liq = liquidity.reindex(idx)

    # Prefer FR-040 liquidity values for FR-042 numeric stress features.
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


def _equity_curves(spy_close: pd.Series, target_exposure: pd.Series) -> tuple[pd.Series, pd.Series]:
    spy = pd.to_numeric(spy_close, errors="coerce")
    spy_ret = spy.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    exposure = pd.to_numeric(target_exposure, errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    exposure = exposure.clip(lower=0.0)

    strat_ret = exposure * spy_ret
    equity = (1.0 + strat_ret).cumprod().astype(float)
    buyhold = (1.0 + spy_ret).cumprod().astype(float)
    return equity, buyhold


def compute_max_drawdown(equity_curve: pd.Series) -> float:
    eq = pd.to_numeric(equity_curve, errors="coerce").dropna()
    if eq.empty:
        return float("nan")
    peak = eq.cummax()
    dd = (eq / peak) - 1.0
    return float(dd.min())


def compute_recovery_days(equity_curve: pd.Series) -> float:
    eq = pd.to_numeric(equity_curve, errors="coerce").dropna()
    if eq.empty:
        return float("nan")
    peak = eq.cummax()
    dd = (eq / peak) - 1.0
    if float(dd.min()) >= 0.0:
        return 0.0

    trough_date = dd.idxmin()
    prior_peak = float(peak.loc[trough_date])
    after = eq.loc[trough_date:]
    recovered = after[after >= prior_peak]
    if recovered.empty:
        return float("nan")

    trough_pos = int(eq.index.get_loc(trough_date))
    rec_pos = int(eq.index.get_loc(recovered.index[0]))
    return float(rec_pos - trough_pos)


def evaluate_truth_table_windows(history: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for label, (start_s, end_s) in WINDOWS.items():
        start = pd.Timestamp(start_s)
        end = pd.Timestamp(end_s)
        w = history[(history.index >= start) & (history.index <= end)]
        n = len(w)

        if n == 0:
            rows.append(
                {
                    "truth_window": label,
                    "start_date": start.date().isoformat(),
                    "end_date": end.date().isoformat(),
                    "rows": 0,
                    "pct_green": float("nan"),
                    "pct_amber": float("nan"),
                    "pct_red": float("nan"),
                    "truth_expected": WINDOW_EXPECTED.get(label, ""),
                    "truth_pass": 0,
                }
            )
            continue

        g = w["governor_state"].astype(str)
        pct_green = float((g == "GREEN").mean())
        pct_amber = float((g == "AMBER").mean())
        pct_red = float((g == "RED").mean())

        if label == "2008Q4":
            truth_pass = (pct_red >= 0.80) and (pct_green == 0.0)
        elif label == "2020-03":
            truth_pass = (pct_red >= 0.85) and (pct_green == 0.0)
        elif label == "2022H1":
            truth_pass = ((pct_amber + pct_red) >= 0.75) and (pct_red >= 0.15)
        elif label == "2017":
            truth_pass = (pct_green >= 0.75) and (pct_red <= 0.05)
        elif label == "2023-11":
            first10 = g.head(10)
            last10 = g.tail(10)
            green_first = float((first10 == "GREEN").mean()) if len(first10) else 0.0
            green_last = float((last10 == "GREEN").mean()) if len(last10) else 0.0
            truth_pass = (green_last > green_first) and (pct_red <= 0.20)
        else:
            truth_pass = False

        rows.append(
            {
                "truth_window": label,
                "start_date": start.date().isoformat(),
                "end_date": end.date().isoformat(),
                "rows": int(n),
                "pct_green": pct_green,
                "pct_amber": pct_amber,
                "pct_red": pct_red,
                "truth_expected": WINDOW_EXPECTED.get(label, ""),
                "truth_pass": int(bool(truth_pass)),
            }
        )

    return pd.DataFrame(rows)


def compute_performance_summary(history: pd.DataFrame) -> dict:
    eq = pd.to_numeric(history["equity_curve"], errors="coerce")
    bh = pd.to_numeric(history["buyhold_curve"], errors="coerce")

    max_dd_strategy = compute_max_drawdown(eq)
    max_dd_buyhold = compute_max_drawdown(bh)
    if np.isfinite(max_dd_buyhold) and max_dd_buyhold != 0:
        dd_reduction_pct = ((abs(max_dd_buyhold) - abs(max_dd_strategy)) / abs(max_dd_buyhold)) * 100.0
    else:
        dd_reduction_pct = float("nan")

    rec_strategy = compute_recovery_days(eq)
    rec_buyhold = compute_recovery_days(bh)
    if np.isfinite(rec_strategy) and np.isfinite(rec_buyhold):
        recovery_gain_days = float(rec_buyhold - rec_strategy)
    else:
        recovery_gain_days = float("nan")

    return {
        "max_dd_strategy": float(max_dd_strategy),
        "max_dd_buyhold": float(max_dd_buyhold),
        "dd_reduction_pct": float(dd_reduction_pct),
        "recovery_days_strategy": float(rec_strategy),
        "recovery_days_buyhold": float(rec_buyhold),
        "recovery_gain_days": float(recovery_gain_days),
    }


def compute_window_performance(history: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for label, (start_s, end_s) in WINDOWS.items():
        start = pd.Timestamp(start_s)
        end = pd.Timestamp(end_s)
        w = history[(history.index >= start) & (history.index <= end)]
        if w.empty:
            rows.append(
                {
                    "truth_window": label,
                    "rows": 0,
                    "max_dd_strategy": float("nan"),
                    "max_dd_buyhold": float("nan"),
                    "dd_reduction_pct": float("nan"),
                    "recovery_days_strategy": float("nan"),
                    "recovery_days_buyhold": float("nan"),
                    "recovery_gain_days": float("nan"),
                }
            )
            continue
        p = compute_performance_summary(w)
        rows.append({"truth_window": label, "rows": int(len(w)), **p})
    return pd.DataFrame(rows)


def _contiguous_segments(series: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp, str]]:
    if series.empty:
        return []
    s = series.fillna("UNKNOWN").astype(str)
    idx = s.index
    segments: list[tuple[pd.Timestamp, pd.Timestamp, str]] = []
    start = idx[0]
    state = s.iloc[0]
    for i in range(1, len(s)):
        if s.iloc[i] != state:
            segments.append((start, idx[i - 1], state))
            start = idx[i]
            state = s.iloc[i]
    segments.append((start, idx[-1], state))
    return segments


def _save_overlay_png(history: pd.DataFrame, overlay_path: Path) -> bool:
    def _save_with_pillow() -> bool:
        from PIL import Image, ImageDraw

        overlay_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 1800, 900
        pad = 70
        split = int(height * 0.68)
        img = Image.new("RGB", (width, height), color=(248, 249, 251))
        draw = ImageDraw.Draw(img)

        if history.empty:
            draw.text((pad, pad), "FR-042 Regime Overlay: no data", fill=(40, 40, 40))
        else:
            idx = history.index
            n = len(idx)
            if n == 1:
                x_map = lambda i: pad
            else:
                x_map = lambda i: int(pad + i * (width - 2 * pad) / (n - 1))

            spy = pd.to_numeric(history["spy_close"], errors="coerce")
            spy_min = float(spy.min()) if spy.notna().any() else 0.0
            spy_max = float(spy.max()) if spy.notna().any() else 1.0
            if spy_max <= spy_min:
                spy_max = spy_min + 1.0

            th = pd.to_numeric(history["throttle_score"], errors="coerce").fillna(0.0)
            t_min, t_max = -2.0, 2.0

            colors = {"GREEN": (214, 245, 221), "AMBER": (255, 242, 198), "RED": (248, 212, 212)}
            segs = _contiguous_segments(history["governor_state"])
            for st, en, state in segs:
                i0 = int(np.searchsorted(idx.values, np.datetime64(st), side="left"))
                i1 = int(np.searchsorted(idx.values, np.datetime64(en), side="right")) - 1
                x0, x1 = x_map(max(0, i0)), x_map(min(n - 1, max(i1, i0)))
                c = colors.get(state, (235, 235, 235))
                draw.rectangle([x0, pad, x1, split - 20], fill=c, outline=None)

            draw.rectangle([pad, pad, width - pad, split - 20], outline=(120, 120, 120), width=1)
            draw.rectangle([pad, split + 30, width - pad, height - pad], outline=(120, 120, 120), width=1)

            spy_points = []
            for i, v in enumerate(spy):
                if pd.isna(v):
                    continue
                x = x_map(i)
                y = int((split - 20) - ((float(v) - spy_min) / (spy_max - spy_min)) * ((split - 20) - pad))
                spy_points.append((x, y))
            if len(spy_points) >= 2:
                draw.line(spy_points, fill=(25, 25, 25), width=2)

            zero_y = int((height - pad) - ((0.0 - t_min) / (t_max - t_min)) * ((height - pad) - (split + 30)))
            draw.line([(pad, zero_y), (width - pad, zero_y)], fill=(120, 120, 120), width=1)

            t_points = []
            for i, v in enumerate(th):
                x = x_map(i)
                y = int((height - pad) - ((float(v) - t_min) / (t_max - t_min)) * ((height - pad) - (split + 30)))
                t_points.append((x, y))
            if len(t_points) >= 2:
                draw.line(t_points, fill=(31, 119, 180), width=2)

            draw.text((pad, 20), "FR-042 Regime Overlay (Pillow fallback)", fill=(30, 30, 30))
            draw.text((pad, split + 8), "Throttle Score", fill=(30, 30, 30))
            draw.text((width - 280, 20), "GREEN / AMBER / RED bands", fill=(60, 60, 60))

        temp_path = overlay_path.with_suffix(overlay_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
        try:
            img.save(temp_path, format="PNG")
            os.replace(temp_path, overlay_path)
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
        return True

    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Patch
    except Exception:
        print(f"matplotlib unavailable; using Pillow fallback for {overlay_path}.")
        return _save_with_pillow()

    overlay_path.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax_price, ax_throttle) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    colors = {
        "GREEN": "#d7f5dd",
        "AMBER": "#fff2c6",
        "RED": "#f8d4d4",
    }
    for start, end, state in _contiguous_segments(history["governor_state"]):
        ax_price.axvspan(start, end + pd.Timedelta(days=1), color=colors.get(state, "#ececec"), alpha=0.35, linewidth=0)

    ax_price.plot(history.index, history["spy_close"], color="#1a1a1a", linewidth=1.2, label="SPY close")
    ax_price.set_title("FR-042 Regime Overlay")
    ax_price.set_ylabel("SPY")
    ax_price.grid(alpha=0.2)
    regime_handles = [
        Patch(facecolor=colors["GREEN"], edgecolor="none", alpha=0.35, label="GREEN"),
        Patch(facecolor=colors["AMBER"], edgecolor="none", alpha=0.35, label="AMBER"),
        Patch(facecolor=colors["RED"], edgecolor="none", alpha=0.35, label="RED"),
    ]
    ax_price.legend(handles=[ax_price.lines[0], *regime_handles], loc="upper left")

    ax_throttle.plot(history.index, history["throttle_score"], color="#1f77b4", linewidth=1.0, label="Throttle")
    ax_throttle.axhline(0.0, color="#666666", linewidth=1.0)
    ax_throttle.axhline(0.5, color="#9a9a9a", linewidth=0.9, linestyle="--")
    ax_throttle.axhline(-0.5, color="#9a9a9a", linewidth=0.9, linestyle="--")
    ax_throttle.set_ylabel("Throttle")
    ax_throttle.set_xlabel("Date")
    ax_throttle.grid(alpha=0.2)
    ax_throttle.legend(loc="upper left")

    fig.tight_layout()

    temp_path = overlay_path.with_suffix(overlay_path.suffix + f".{os.getpid()}.{int(time.time() * 1000)}.tmp")
    try:
        fig.savefig(temp_path, dpi=150)
        os.replace(temp_path, overlay_path)
    finally:
        plt.close(fig)
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
    return True


def _print_window_diagnostics(history: pd.DataFrame):
    gov_order = ["RED", "AMBER", "GREEN"]
    market_order = ["NEG", "NEUT", "POS"]
    print("\nTruth-table diagnostics:")
    verdicts = evaluate_truth_table_windows(history)
    print(verdicts.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))
    overall_pass = bool((verdicts["truth_pass"] == 1).all()) if not verdicts.empty else False
    print(f"\nTruth-table overall verdict: {'PASS' if overall_pass else 'BLOCK'}")
    for label, (start_s, end_s) in WINDOWS.items():
        start = pd.Timestamp(start_s)
        end = pd.Timestamp(end_s)
        window = history[(history.index >= start) & (history.index <= end)]

        print(f"\n[{label}] {start.date()} -> {end.date()} | rows={len(window)}")
        if window.empty:
            print("  no rows in window")
            continue

        counts = pd.crosstab(window["governor_state"], window["market_state"])
        counts = counts.reindex(index=gov_order, columns=market_order, fill_value=0)
        print("  Governor x Market counts:")
        print(counts.to_string())

        combo = (
            window.groupby(["governor_state", "market_state"], observed=False)
            .agg(
                days=("target_exposure", "size"),
                avg_target_exposure=("target_exposure", "mean"),
                avg_throttle=("throttle_score", "mean"),
                avg_bocpd=("bocpd_prob", "mean"),
            )
            .reset_index()
            .sort_values(["governor_state", "market_state"])
        )
        print("  Exposure truth table:")
        print(combo.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))

        cash_days = int((window["target_exposure"] <= 0.0).sum())
        print(
            "  cash days="
            f"{cash_days} ({cash_days / max(len(window), 1):.1%}), "
            f"mean exposure={window['target_exposure'].mean():0.3f}, "
            f"max bocpd={window['bocpd_prob'].max():0.3f}"
        )


def _default_macro_path() -> Path:
    if DEFAULT_MACRO_FEATURES_PATH.exists():
        return DEFAULT_MACRO_FEATURES_PATH
    return DEFAULT_MACRO_FALLBACK_PATH


def build_regime_history(
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    macro_path: Path,
    liquidity_path: Path | None,
    prices_path: Path | None,
    patch_path: Path | None,
) -> pd.DataFrame:
    macro = _load_frame(macro_path, start=start, end=end)
    liquidity = None
    if liquidity_path is not None and liquidity_path.exists():
        liquidity = _load_frame(liquidity_path, start=start, end=end)
    else:
        print(f"liquidity parquet missing at {liquidity_path}; proceeding with macro-only context.")

    context = _build_context(macro=macro, liquidity=liquidity)
    if context.empty:
        raise RuntimeError("No macro/liquidity context rows found for selected window.")

    spy_macro = pd.to_numeric(context.get("spy_close", pd.Series(index=context.index, dtype=float)), errors="coerce")
    spy_fallback = _load_spy_from_prices(prices_path=prices_path, patch_path=patch_path, start=start, end=end)
    spy_macro = spy_macro.reindex(context.index)
    if spy_fallback.empty:
        spy_fallback = pd.Series(np.nan, index=context.index, dtype=float, name="spy_close")
    else:
        spy_fallback = spy_fallback.reindex(context.index)
    spy_close = spy_macro.where(spy_macro.notna(), spy_fallback)
    spy_close = spy_close.ffill()
    if spy_close.notna().sum() == 0:
        raise RuntimeError("Unable to build SPY close series from macro and price fallbacks.")
    context["spy_close"] = spy_close

    idx = context.index.sort_values()
    manager = RegimeManager()
    result = manager.evaluate(context, idx)
    equity_curve, buyhold_curve = _equity_curves(spy_close=context["spy_close"], target_exposure=result.target_exposure)

    history = pd.DataFrame(
        {
            "governor_state": result.governor_state.reindex(idx).astype(str),
            "market_state": result.market_state.reindex(idx).astype(str),
            "target_exposure": pd.to_numeric(result.target_exposure.reindex(idx), errors="coerce"),
            "matrix_exposure": pd.to_numeric(result.matrix_exposure.reindex(idx), errors="coerce"),
            "throttle_score": pd.to_numeric(result.throttle_score.reindex(idx), errors="coerce"),
            "bocpd_prob": pd.to_numeric(result.bocpd_prob.reindex(idx), errors="coerce"),
            "reason": result.reason.reindex(idx).astype(str),
            "spy_close": pd.to_numeric(context["spy_close"].reindex(idx), errors="coerce"),
            "equity_curve": equity_curve.reindex(idx),
            "buyhold_curve": buyhold_curve.reindex(idx),
        },
        index=idx,
    )
    return history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 12 FR-042 regime history verifier")
    parser.add_argument("--start-date", default="2000-01-01", help="Inclusive start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="Inclusive end date (YYYY-MM-DD)")
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV), help="CSV output path")
    parser.add_argument("--overlay-path", default=str(DEFAULT_OUTPUT_OVERLAY), help="PNG overlay output path")
    parser.add_argument("--macro-path", default=None, help="Override macro parquet path")
    parser.add_argument("--liquidity-path", default=str(DEFAULT_LIQUIDITY_PATH), help="Liquidity parquet path")
    parser.add_argument("--prices-path", default=str(DEFAULT_PRICES_PATH), help="Prices parquet path")
    parser.add_argument("--patch-path", default=str(DEFAULT_PATCH_PATH), help="Yahoo patch parquet path")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any truth-table window fails.")
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
    overlay_path = _resolve_path(args.overlay_path, default_path=DEFAULT_OUTPUT_OVERLAY)

    if macro_path is None:
        raise RuntimeError("No macro path resolved.")

    history = build_regime_history(
        start=start,
        end=end,
        macro_path=macro_path,
        liquidity_path=liquidity_path,
        prices_path=prices_path,
        patch_path=patch_path,
    )

    verdicts = evaluate_truth_table_windows(history)
    performance = compute_performance_summary(history)
    window_perf = compute_window_performance(history)

    history = history.copy()
    history["truth_window"] = "OUT_OF_SCOPE"
    history["truth_expected"] = ""
    history["truth_pass"] = np.nan
    for _, v in verdicts.iterrows():
        wlabel = str(v["truth_window"])
        wstart = pd.Timestamp(v["start_date"])
        wend = pd.Timestamp(v["end_date"])
        mask = (history.index >= wstart) & (history.index <= wend)
        history.loc[mask, "truth_window"] = wlabel
        history.loc[mask, "truth_expected"] = str(v["truth_expected"])
        history.loc[mask, "truth_pass"] = int(v["truth_pass"])

    export = history.reset_index().rename(columns={"index": "date"})
    export["date"] = pd.to_datetime(export["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    _atomic_csv_write(export, output_csv)

    print(
        "Built regime history rows="
        f"{len(history):,}, range={history.index.min().date()} -> {history.index.max().date()}, "
        f"final target_exposure={history['target_exposure'].iloc[-1]:0.3f}, "
        f"final governor={history['governor_state'].iloc[-1]}"
    )
    print(f"CSV written: {output_csv}")

    _print_window_diagnostics(history)
    print("\nPerformance summary:")
    print(
        f"  max_dd_strategy={performance['max_dd_strategy']:.3%}, "
        f"max_dd_buyhold={performance['max_dd_buyhold']:.3%}, "
        f"dd_reduction_pct={performance['dd_reduction_pct']:.2f}%"
    )
    print(
        f"  recovery_days_strategy={performance['recovery_days_strategy']}, "
        f"recovery_days_buyhold={performance['recovery_days_buyhold']}, "
        f"recovery_gain_days={performance['recovery_gain_days']}"
    )
    print("\nWindow performance:")
    print(window_perf.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))

    crisis_perf = window_perf[window_perf["truth_window"].isin(CRISIS_WINDOWS)].copy()
    dd_nonneg_crisis = bool((crisis_perf["dd_reduction_pct"].fillna(-np.inf) >= 0.0).all()) if not crisis_perf.empty else False
    recovery_nonnull = crisis_perf["recovery_gain_days"].dropna() if not crisis_perf.empty else pd.Series(dtype=float)
    median_recovery_gain = float(recovery_nonnull.median()) if len(recovery_nonnull) else float("nan")
    global_recovery_gain = float(performance.get("recovery_gain_days", float("nan")))
    recovery_fallback_used = len(recovery_nonnull) == 0
    if recovery_fallback_used:
        # Crisis windows are intentionally short; recovery can be undefined in-window.
        recovery_nonneg = bool(np.isfinite(global_recovery_gain) and global_recovery_gain >= 0.0)
    else:
        recovery_nonneg = bool(np.isfinite(median_recovery_gain) and median_recovery_gain >= 0.0)
    dd_global_positive = bool(np.isfinite(performance["dd_reduction_pct"]) and performance["dd_reduction_pct"] > 0.0)
    truth_pass_all = bool((verdicts["truth_pass"] == 1).all()) if not verdicts.empty else False
    perf_pass = bool(dd_global_positive and dd_nonneg_crisis and recovery_nonneg)
    overall_pass = bool(truth_pass_all and perf_pass)
    print("\nFR-042 Acceptance:")
    print(
        f"  truth_table_pass={truth_pass_all}, "
        f"dd_global_positive={dd_global_positive}, "
        f"dd_nonneg_crisis={dd_nonneg_crisis}, "
        f"median_recovery_gain={median_recovery_gain}, "
        f"global_recovery_gain={global_recovery_gain}, "
        f"recovery_fallback_used={recovery_fallback_used}, "
        f"recovery_nonneg={recovery_nonneg}"
    )
    print(f"  overall_verdict={'PASS' if overall_pass else 'BLOCK'}")

    if overlay_path is not None:
        plotted = _save_overlay_png(history=history, overlay_path=overlay_path)
        if plotted:
            print(f"Overlay plot written: {overlay_path}")
    if args.strict and not overall_pass:
        print("Strict mode: FR-042 acceptance criteria not met.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
