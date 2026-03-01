from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import duckdb  # noqa: E402
from core import engine  # noqa: E402
from scripts.day5_ablation_report import _atomic_csv_write  # noqa: E402
from scripts.day5_ablation_report import _atomic_json_write  # noqa: E402
from scripts.day5_ablation_report import _build_target_weights  # noqa: E402
from scripts.day5_ablation_report import _load_features_subset  # noqa: E402
from scripts.day5_ablation_report import _load_returns_subset  # noqa: E402
from scripts.day5_ablation_report import _resolve_path  # noqa: E402
from scripts.day5_ablation_report import _sql_escape_path  # noqa: E402
from scripts.day5_ablation_report import _to_ts  # noqa: E402
from strategies.company_scorecard import CompanyScorecard  # noqa: E402
from strategies.factor_specs import FactorSpec  # noqa: E402
from strategies.factor_specs import build_default_factor_specs  # noqa: E402
from strategies.factor_specs import validate_factor_specs  # noqa: E402
from utils.metrics import compute_cagr  # noqa: E402
from utils.metrics import compute_max_drawdown  # noqa: E402
from utils.metrics import compute_sharpe  # noqa: E402
from utils.metrics import compute_ulcer_index  # noqa: E402


PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_FEATURES_PATH = PROCESSED_DIR / "features.parquet"
DEFAULT_PRICES_TRI_PATH = PROCESSED_DIR / "prices_tri.parquet"
DEFAULT_PRICES_PATH = PROCESSED_DIR / "prices.parquet"
DEFAULT_OUTPUT_DIR = PROCESSED_DIR
SPY_PERMNO = 84398


@dataclass(frozen=True)
class WalkForwardWindow:
    window_id: str
    train_start: str
    train_end: str
    test_start: str
    test_end: str
    regime: str
    stress_type: str


WALK_FORWARD_WINDOWS = [
    WalkForwardWindow(
        window_id="W1_COVID",
        train_start="2015-01-01",
        train_end="2019-12-31",
        test_start="2020-01-01",
        test_end="2020-12-31",
        regime="COVID crash + recovery",
        stress_type="sharp_drawdown",
    ),
    WalkForwardWindow(
        window_id="W2_INFLATION",
        train_start="2015-01-01",
        train_end="2020-12-31",
        test_start="2021-01-01",
        test_end="2021-12-31",
        regime="Inflation shock + Fed pivot",
        stress_type="regime_shift",
    ),
    WalkForwardWindow(
        window_id="W3_BEAR",
        train_start="2015-01-01",
        train_end="2021-12-31",
        test_start="2022-01-01",
        test_end="2022-12-31",
        regime="Bear market + rate hikes",
        stress_type="prolonged_drawdown",
    ),
    WalkForwardWindow(
        window_id="W4_RECOVERY",
        train_start="2015-01-01",
        train_end="2022-12-31",
        test_start="2023-01-01",
        test_end="2024-12-31",
        regime="AI boom + mega-cap rally",
        stress_type="momentum_surge",
    ),
]

DECAY_VALUES = [0.85, 0.90, 0.95, 0.98, 0.99]

CRISIS_WINDOWS = [
    ("COVID_CRASH", "2020-02-19", "2020-03-23"),
    ("COVID_VOLATILITY", "2020-03-01", "2020-04-30"),
    ("INFLATION_SPIKE", "2022-01-03", "2022-06-16"),
    ("BEAR_MARKET", "2022-01-03", "2022-12-31"),
]


def _slice_by_date(df: pd.DataFrame, start: str | pd.Timestamp, end: str | pd.Timestamp) -> pd.DataFrame:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    if df.empty:
        return df.copy()
    out = df.copy()
    if "date" in out.columns:
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        return out[(out["date"] >= start_ts) & (out["date"] <= end_ts)].copy()
    if isinstance(out.index, pd.DatetimeIndex):
        return out[(out.index >= start_ts) & (out.index <= end_ts)].copy()
    return out.copy()


def _compute_drawdown_duration(returns: pd.Series) -> int:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return 0
    eq = (1.0 + r).cumprod()
    dd = (eq / eq.cummax()) - 1.0
    under = dd < 0.0
    run = 0
    max_run = 0
    for flag in under.to_numpy():
        if flag:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 0
    return int(max_run)


def _days_to_new_high(returns: pd.Series, recovery_start: str) -> float:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return float("nan")
    eq = (1.0 + r).cumprod()
    start_ts = pd.Timestamp(recovery_start)
    pre = eq.loc[eq.index <= start_ts]
    if pre.empty:
        return float("nan")
    peak = float(pre.max())
    post = eq.loc[eq.index >= start_ts]
    if post.empty:
        return float("nan")
    hit = post[post >= peak]
    if hit.empty:
        return float("nan")
    hit_idx = hit.index[0]
    return float(post.index.get_loc(hit_idx))


def _compute_beta(port_ret: pd.Series, spy_ret: pd.Series) -> float:
    p = pd.to_numeric(port_ret, errors="coerce")
    b = pd.to_numeric(spy_ret, errors="coerce")
    aligned = pd.concat([p, b], axis=1, join="inner").dropna()
    if len(aligned) < 10:
        return float("nan")
    cov = float(np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1], ddof=1)[0, 1])
    var = float(np.var(aligned.iloc[:, 1], ddof=1))
    if not np.isfinite(var) or var <= 0.0:
        return float("nan")
    return cov / var


def _adjacent_rank_corr(scores: pd.DataFrame) -> float:
    if scores.empty:
        return float("nan")
    work = scores.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date", "permno", "score"])
    if work.empty:
        return float("nan")

    rows: list[float] = []
    dates = sorted(work["date"].unique())
    for i in range(1, len(dates)):
        d0 = dates[i - 1]
        d1 = dates[i]
        g0 = work[work["date"] == d0][["permno", "score"]].copy()
        g1 = work[work["date"] == d1][["permno", "score"]].copy()
        if g0.empty or g1.empty:
            continue
        g0["r0"] = g0["score"].rank(method="average")
        g1["r1"] = g1["score"].rank(method="average")
        merged = g0[["permno", "r0"]].merge(g1[["permno", "r1"]], on="permno", how="inner")
        if len(merged) < 5:
            continue
        corr = merged["r0"].corr(merged["r1"], method="spearman")
        if np.isfinite(corr):
            rows.append(float(corr))
    return float(np.mean(rows)) if rows else float("nan")


def _build_c3_specs(decay: float) -> list[FactorSpec]:
    if not (0.0 < float(decay) < 1.0):
        raise ValueError(f"Decay must be in (0,1), got {decay}")
    alpha = 1.0 - float(decay)
    specs = build_default_factor_specs()
    out = [
        replace(
            s,
            use_sigmoid_blend=False,
            use_dirty_derivative=False,
            use_leaky_integrator=True,
            leaky_alpha=alpha,
        )
        for s in specs
    ]
    validate_factor_specs(out)
    return out


def _load_spy_returns(
    prices_path: Path,
    start_date: pd.Timestamp | None,
    end_date: pd.Timestamp | None,
) -> pd.Series:
    con = duckdb.connect()
    try:
        schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{_sql_escape_path(prices_path)}')").df()
        cols = set(schema["column_name"].astype(str).tolist())
        has_total_ret = "total_ret" in cols

        where = [f"CAST(permno AS BIGINT) = {SPY_PERMNO}"]
        if start_date is not None:
            where.append(f"CAST(date AS DATE) >= DATE '{start_date.strftime('%Y-%m-%d')}'")
        if end_date is not None:
            where.append(f"CAST(date AS DATE) <= DATE '{end_date.strftime('%Y-%m-%d')}'")
        where_sql = " AND ".join(where)

        if has_total_ret:
            q = f"""
            SELECT CAST(date AS DATE) AS date, CAST(total_ret AS DOUBLE) AS ret
            FROM read_parquet('{_sql_escape_path(prices_path)}')
            WHERE {where_sql}
            ORDER BY date
            """
            df = con.execute(q).df()
            df["ret"] = pd.to_numeric(df["ret"], errors="coerce")
        else:
            q = f"""
            SELECT CAST(date AS DATE) AS date, CAST(adj_close AS DOUBLE) AS px
            FROM read_parquet('{_sql_escape_path(prices_path)}')
            WHERE {where_sql}
            ORDER BY date
            """
            df = con.execute(q).df()
            df["px"] = pd.to_numeric(df["px"], errors="coerce")
            df["ret"] = df["px"].pct_change(fill_method=None)
    finally:
        con.close()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    out = pd.Series(pd.to_numeric(df["ret"], errors="coerce").values, index=df["date"], name="spy_ret")
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float).sort_index()


def _simulate_from_scores(
    scores: pd.DataFrame,
    returns_long: pd.DataFrame,
    top_quantile: float,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> tuple[pd.DataFrame, int]:
    target_weights = _build_target_weights(scores=scores, top_quantile=top_quantile).sort_index()
    if target_weights.empty and len(target_weights.index) == 0:
        sim = pd.DataFrame(columns=["gross_ret", "net_ret", "turnover", "cost", "equity"])
        return sim, 0

    ret = returns_long.copy()
    ret["date"] = pd.to_datetime(ret["date"], errors="coerce")
    ret["permno"] = pd.to_numeric(ret["permno"], errors="coerce")
    ret["ret"] = pd.to_numeric(ret["ret"], errors="coerce")
    ret = ret.dropna(subset=["date", "permno"]).sort_values(["date", "permno"])
    returns_wide = ret.pivot(index="date", columns="permno", values="ret").sort_index()

    matrix_cells = int(len(target_weights.index) * max(1, target_weights.shape[1]))
    if matrix_cells > int(max_matrix_cells):
        raise RuntimeError(
            f"Target matrix too large ({matrix_cells:,} cells > {int(max_matrix_cells):,}). "
            "Lower universe size or raise --max-matrix-cells."
        )

    if target_weights.shape[1] == 0:
        returns_aligned = pd.DataFrame(index=target_weights.index)
        missing_active = 0
    else:
        returns_reindexed = returns_wide.reindex(index=target_weights.index, columns=target_weights.columns)
        executed_positions = target_weights.shift(1).fillna(0.0).ne(0.0)
        missing_active = int((returns_reindexed.isna() & executed_positions).sum().sum())
        if missing_active > 0 and not allow_missing_returns:
            raise RuntimeError(
                f"Missing {missing_active:,} return cells on executed exposures. "
                "Use --allow-missing-returns to impute as zero."
            )
        if missing_active > 0 and allow_missing_returns:
            print(f"WARNING: Missing executed-exposure return cells treated as zero: {missing_active:,}")
        returns_aligned = returns_reindexed

    sim = engine.run_simulation(
        target_weights=target_weights,
        returns_df=returns_aligned,
        cost_bps=float(cost_bps) / 10000.0,
        strict_missing_returns=not allow_missing_returns,
    ).copy()
    sim.index = pd.DatetimeIndex(sim.index)
    sim.index.name = "date"
    sim["equity"] = (1.0 + pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)).cumprod()
    return sim, missing_active


def _period_metrics(
    sim: pd.DataFrame,
    scores: pd.DataFrame,
    spy_returns: pd.Series,
    start: str,
    end: str,
) -> dict[str, float]:
    s = _slice_by_date(sim, start, end)
    if s.empty:
        return {
            "sharpe": float("nan"),
            "cagr": float("nan"),
            "max_dd": float("nan"),
            "ulcer": float("nan"),
            "turnover_annual": float("nan"),
            "turnover_total": float("nan"),
            "rank_stability": float("nan"),
            "beta": float("nan"),
            "drawdown_duration": float("nan"),
            "return_sum": float("nan"),
            "n_days": 0.0,
        }

    ret = pd.to_numeric(s["net_ret"], errors="coerce").fillna(0.0)
    eq = (1.0 + ret).cumprod()
    turnover = pd.to_numeric(s["turnover"], errors="coerce").fillna(0.0)
    sc = _slice_by_date(scores, start, end)
    if "score_valid" in sc.columns:
        sc = sc[sc["score_valid"].astype(bool)]
    sc = sc[["date", "permno", "score"]].copy() if not sc.empty else pd.DataFrame(columns=["date", "permno", "score"])
    spy = spy_returns.reindex(s.index)

    return {
        "sharpe": float(compute_sharpe(ret)),
        "cagr": float(compute_cagr(eq)),
        "max_dd": float(compute_max_drawdown(eq)),
        "ulcer": float(compute_ulcer_index(eq)),
        "turnover_annual": float(turnover.mean() * 252.0),
        "turnover_total": float(turnover.sum()),
        "rank_stability": float(_adjacent_rank_corr(sc)),
        "beta": float(_compute_beta(ret, spy)),
        "drawdown_duration": float(_compute_drawdown_duration(ret)),
        "return_sum": float(ret.sum()),
        "n_days": float(len(ret)),
    }


def run_walk_forward_validation(
    baseline_sim: pd.DataFrame,
    c3_sim: pd.DataFrame,
    baseline_scores: pd.DataFrame,
    c3_scores: pd.DataFrame,
    spy_returns: pd.Series,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for w in WALK_FORWARD_WINDOWS:
        train_base = _period_metrics(baseline_sim, baseline_scores, spy_returns, w.train_start, w.train_end)
        train_c3 = _period_metrics(c3_sim, c3_scores, spy_returns, w.train_start, w.train_end)
        test_base = _period_metrics(baseline_sim, baseline_scores, spy_returns, w.test_start, w.test_end)
        test_c3 = _period_metrics(c3_sim, c3_scores, spy_returns, w.test_start, w.test_end)

        row: dict[str, float | str] = {
            "window_id": w.window_id,
            "regime": w.regime,
            "stress_type": w.stress_type,
            "train_sharpe_baseline": train_base["sharpe"],
            "train_sharpe_c3": train_c3["sharpe"],
            "train_sharpe_delta": train_c3["sharpe"] - train_base["sharpe"],
            "test_sharpe_baseline": test_base["sharpe"],
            "test_sharpe_c3": test_c3["sharpe"],
            "test_sharpe_delta": test_c3["sharpe"] - test_base["sharpe"],
            "delta_consistency": abs((test_c3["sharpe"] - test_base["sharpe"]) - (train_c3["sharpe"] - train_base["sharpe"])),
            "test_maxdd_baseline": test_base["max_dd"],
            "test_maxdd_c3": test_c3["max_dd"],
            "test_turnover_baseline": test_base["turnover_annual"],
            "test_turnover_c3": test_c3["turnover_annual"],
            "test_turnover_reduction": (
                (test_base["turnover_annual"] - test_c3["turnover_annual"]) / test_base["turnover_annual"]
                if np.isfinite(test_base["turnover_annual"]) and abs(test_base["turnover_annual"]) > 1e-12
                else float("nan")
            ),
            "test_rank_stability_baseline": test_base["rank_stability"],
            "test_rank_stability_c3": test_c3["rank_stability"],
            "test_beta_baseline": test_base["beta"],
            "test_beta_c3": test_c3["beta"],
            "test_drawdown_duration_baseline": test_base["drawdown_duration"],
            "test_drawdown_duration_c3": test_c3["drawdown_duration"],
        }

        if w.window_id == "W1_COVID":
            base_rec = _period_metrics(baseline_sim, baseline_scores, spy_returns, "2020-04-01", "2020-12-31")
            c3_rec = _period_metrics(c3_sim, c3_scores, spy_returns, "2020-04-01", "2020-12-31")
            row["covid_recovery_capture"] = (
                c3_rec["return_sum"] / base_rec["return_sum"]
                if np.isfinite(base_rec["return_sum"]) and abs(base_rec["return_sum"]) > 1e-12
                else float("nan")
            )

        if w.window_id == "W2_INFLATION":
            base_rot = _period_metrics(baseline_sim, baseline_scores, spy_returns, "2021-09-01", "2021-12-31")
            c3_rot = _period_metrics(c3_sim, c3_scores, spy_returns, "2021-09-01", "2021-12-31")
            row["rotation_rank_stability_baseline"] = base_rot["rank_stability"]
            row["rotation_rank_stability_c3"] = c3_rot["rank_stability"]
            row["rotation_turnover_baseline"] = base_rot["turnover_annual"]
            row["rotation_turnover_c3"] = c3_rot["turnover_annual"]

        if w.window_id == "W3_BEAR":
            base_bear = _period_metrics(baseline_sim, baseline_scores, spy_returns, "2022-01-01", "2022-09-30")
            c3_bear = _period_metrics(c3_sim, c3_scores, spy_returns, "2022-01-01", "2022-09-30")
            row["bear_beta_baseline"] = base_bear["beta"]
            row["bear_beta_c3"] = c3_bear["beta"]
            # Recovery speed is measured from 2022-10 onward and may complete after 2022.
            base_test_ret = pd.to_numeric(
                baseline_sim.loc[baseline_sim.index >= pd.Timestamp(w.test_start), "net_ret"],
                errors="coerce",
            ).fillna(0.0)
            c3_test_ret = pd.to_numeric(
                c3_sim.loc[c3_sim.index >= pd.Timestamp(w.test_start), "net_ret"],
                errors="coerce",
            ).fillna(0.0)
            row["bear_recovery_days_baseline"] = _days_to_new_high(base_test_ret, "2022-10-01")
            row["bear_recovery_days_c3"] = _days_to_new_high(c3_test_ret, "2022-10-01")

        if w.window_id == "W4_RECOVERY":
            base_rally = _period_metrics(baseline_sim, baseline_scores, spy_returns, "2023-01-01", "2024-12-31")
            c3_rally = _period_metrics(c3_sim, c3_scores, spy_returns, "2023-01-01", "2024-12-31")
            spy_rally = spy_returns.loc[(spy_returns.index >= pd.Timestamp("2023-01-01")) & (spy_returns.index <= pd.Timestamp("2024-12-31"))]
            spy_sum = float(pd.to_numeric(spy_rally, errors="coerce").fillna(0.0).sum())
            row["upside_capture_baseline"] = base_rally["return_sum"] / spy_sum if np.isfinite(spy_sum) and abs(spy_sum) > 1e-12 else float("nan")
            row["upside_capture_c3"] = c3_rally["return_sum"] / spy_sum if np.isfinite(spy_sum) and abs(spy_sum) > 1e-12 else float("nan")

        rows.append(row)
    return pd.DataFrame(rows)


def analyze_decay_sensitivity(
    features: pd.DataFrame,
    returns: pd.DataFrame,
    spy_returns: pd.Series,
    top_quantile: float,
    cost_bps: float,
    allow_missing_returns: bool,
    max_matrix_cells: int,
) -> pd.DataFrame:
    _ = spy_returns
    rows: list[dict[str, float]] = []
    for decay in DECAY_VALUES:
        specs = _build_c3_specs(decay)
        scores, summary = CompanyScorecard(factor_specs=specs, scoring_method="complete_case").compute_scores(features)
        sim, missing = _simulate_from_scores(
            scores=scores,
            returns_long=returns,
            top_quantile=top_quantile,
            cost_bps=cost_bps,
            allow_missing_returns=allow_missing_returns,
            max_matrix_cells=max_matrix_cells,
        )
        ret = pd.to_numeric(sim["net_ret"], errors="coerce").fillna(0.0)
        eq = (1.0 + ret).cumprod()
        valid_scores = scores[scores["score_valid"].astype(bool)][["date", "permno", "score"]]
        rows.append(
            {
                "decay": float(decay),
                "alpha": float(1.0 - decay),
                "coverage": float(summary.coverage),
                "sharpe": float(compute_sharpe(ret)),
                "cagr": float(compute_cagr(eq)),
                "max_dd": float(compute_max_drawdown(eq)),
                "ulcer": float(compute_ulcer_index(eq)),
                "turnover_annual": float(pd.to_numeric(sim["turnover"], errors="coerce").mean() * 252.0),
                "rank_stability": float(_adjacent_rank_corr(valid_scores)),
                "missing_active_return_cells": float(missing),
            }
        )

    out = pd.DataFrame(rows).sort_values("decay").reset_index(drop=True)
    base = out[np.isclose(out["decay"], 0.95)]
    base_sh = float(base["sharpe"].iloc[0]) if not base.empty else float("nan")
    base_to = float(base["turnover_annual"].iloc[0]) if not base.empty else float("nan")
    out["sharpe_delta_vs_0_95"] = pd.to_numeric(out["sharpe"], errors="coerce") - base_sh
    out["turnover_delta_vs_0_95"] = pd.to_numeric(out["turnover_annual"], errors="coerce") - base_to
    return out


def validate_crisis_turnover(baseline_sim: pd.DataFrame, c3_sim: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str | float | bool]] = []
    for name, start, end in CRISIS_WINDOWS:
        base = _slice_by_date(baseline_sim, start, end)
        c3 = _slice_by_date(c3_sim, start, end)
        base_turn = float(pd.to_numeric(base.get("turnover"), errors="coerce").fillna(0.0).mean() * 252.0)
        c3_turn = float(pd.to_numeric(c3.get("turnover"), errors="coerce").fillna(0.0).mean() * 252.0)
        reduction = (base_turn - c3_turn) / base_turn if np.isfinite(base_turn) and abs(base_turn) > 1e-12 else float("nan")
        passed = bool(np.isfinite(reduction) and reduction >= 0.15 and c3_turn < base_turn)
        rows.append(
            {
                "window": name,
                "start_date": start,
                "end_date": end,
                "baseline_turnover_annual": base_turn,
                "c3_turnover_annual": c3_turn,
                "reduction_pct": reduction * 100.0 if np.isfinite(reduction) else float("nan"),
                "pass": passed,
            }
        )
    return pd.DataFrame(rows)


def evaluate_checks(walkforward_df: pd.DataFrame, decay_df: pd.DataFrame, crisis_df: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, str | float | bool]] = []
    wf = {r["window_id"]: r for _, r in walkforward_df.iterrows()}

    w1 = wf.get("W1_COVID", {})
    checks.append({"check_id": "CHK-39", "pass": bool(w1.get("test_maxdd_c3", np.nan) < w1.get("test_maxdd_baseline", np.nan)), "value": float(w1.get("test_maxdd_c3", np.nan)), "target": "< baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-40", "pass": bool(w1.get("test_turnover_c3", np.nan) < w1.get("test_turnover_baseline", np.nan)), "value": float(w1.get("test_turnover_c3", np.nan)), "target": "< baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-41", "pass": bool(w1.get("covid_recovery_capture", np.nan) >= 0.90), "value": float(w1.get("covid_recovery_capture", np.nan)), "target": ">= 0.90", "evidence_file": "phase18_day6_walkforward.csv"})

    w2 = wf.get("W2_INFLATION", {})
    checks.append({"check_id": "CHK-42", "pass": bool(w2.get("rotation_rank_stability_c3", np.nan) > w2.get("rotation_rank_stability_baseline", np.nan)), "value": float(w2.get("rotation_rank_stability_c3", np.nan)), "target": "> baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-43", "pass": bool(w2.get("rotation_turnover_c3", np.nan) < w2.get("rotation_turnover_baseline", np.nan)), "value": float(w2.get("rotation_turnover_c3", np.nan)), "target": "< baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-44", "pass": bool(w2.get("test_sharpe_c3", np.nan) >= w2.get("test_sharpe_baseline", np.nan)), "value": float(w2.get("test_sharpe_c3", np.nan)), "target": ">= baseline", "evidence_file": "phase18_day6_walkforward.csv"})

    w3 = wf.get("W3_BEAR", {})
    checks.append({"check_id": "CHK-45", "pass": bool(w3.get("test_drawdown_duration_c3", np.nan) <= w3.get("test_drawdown_duration_baseline", np.nan)), "value": float(w3.get("test_drawdown_duration_c3", np.nan)), "target": "<= baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-46", "pass": bool(w3.get("bear_beta_c3", np.nan) <= w3.get("bear_beta_baseline", np.nan)), "value": float(w3.get("bear_beta_c3", np.nan)), "target": "<= baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    rec_base = float(w3.get("bear_recovery_days_baseline", np.nan))
    rec_c3 = float(w3.get("bear_recovery_days_c3", np.nan))
    checks.append({"check_id": "CHK-47", "pass": bool(np.isfinite(rec_base) and np.isfinite(rec_c3) and rec_c3 <= rec_base * 1.10), "value": rec_c3, "target": "<= 110% baseline", "evidence_file": "phase18_day6_walkforward.csv"})

    w4 = wf.get("W4_RECOVERY", {})
    cap_base = float(w4.get("upside_capture_baseline", np.nan))
    cap_c3 = float(w4.get("upside_capture_c3", np.nan))
    checks.append({"check_id": "CHK-48", "pass": bool(np.isfinite(cap_base) and np.isfinite(cap_c3) and cap_c3 >= cap_base * 0.95), "value": cap_c3, "target": ">= 95% baseline capture", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-49", "pass": bool(w4.get("test_turnover_c3", np.nan) < w4.get("test_turnover_baseline", np.nan)), "value": float(w4.get("test_turnover_c3", np.nan)), "target": "< baseline", "evidence_file": "phase18_day6_walkforward.csv"})
    checks.append({"check_id": "CHK-50", "pass": bool(w4.get("test_sharpe_c3", np.nan) >= w4.get("test_sharpe_baseline", np.nan)), "value": float(w4.get("test_sharpe_c3", np.nan)), "target": ">= baseline", "evidence_file": "phase18_day6_walkforward.csv"})

    sharpe_vals = pd.to_numeric(decay_df.get("sharpe", pd.Series(dtype=float)), errors="coerce").to_numpy(dtype=float)
    if len(sharpe_vals) >= 2 and np.isfinite(sharpe_vals).all():
        grad = np.gradient(sharpe_vals)
        grad_max = float(np.max(np.abs(grad)))
        chk51 = bool(grad_max < 0.05)
    else:
        grad_max = float("nan")
        chk51 = False
    checks.append({"check_id": "CHK-51", "pass": chk51, "value": grad_max, "target": "< 0.05", "evidence_file": "phase18_day6_decay_sensitivity.csv"})

    max_sh = float(np.nanmax(sharpe_vals)) if len(sharpe_vals) else float("nan")
    near_cnt = int(np.sum(sharpe_vals >= (max_sh - 0.03))) if np.isfinite(max_sh) else 0
    checks.append({"check_id": "CHK-52", "pass": bool(near_cnt >= 3), "value": float(near_cnt), "target": ">= 3 values within 0.03", "evidence_file": "phase18_day6_decay_sensitivity.csv"})

    s95 = decay_df.loc[np.isclose(decay_df["decay"], 0.95), "sharpe"]
    s90 = decay_df.loc[np.isclose(decay_df["decay"], 0.90), "sharpe"]
    s98 = decay_df.loc[np.isclose(decay_df["decay"], 0.98), "sharpe"]
    if not s95.empty and not s90.empty and not s98.empty:
        left = float(s95.iloc[0] - s90.iloc[0])
        right = float(s95.iloc[0] - s98.iloc[0])
        sym = abs(left - right)
        chk53 = bool(sym < 0.05)
    else:
        sym = float("nan")
        chk53 = False
    checks.append({"check_id": "CHK-53", "pass": chk53, "value": sym, "target": "< 0.05", "evidence_file": "phase18_day6_decay_sensitivity.csv"})

    chk54 = bool(crisis_df["pass"].all()) if not crisis_df.empty else False
    min_red = float(pd.to_numeric(crisis_df.get("reduction_pct"), errors="coerce").min()) if not crisis_df.empty else float("nan")
    checks.append({"check_id": "CHK-54", "pass": chk54, "value": min_red, "target": ">= 15% all crisis windows", "evidence_file": "phase18_day6_crisis_turnover.csv"})
    return pd.DataFrame(checks)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 18 Day 6: Walk-forward robustness validation")
    p.add_argument("--input-features", default=str(DEFAULT_FEATURES_PATH))
    p.add_argument("--input-prices", default=None, help="Optional prices parquet override.")
    p.add_argument("--start-date", default="2015-01-01")
    p.add_argument("--end-date", default="2024-12-31")
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--cost-bps", type=float, default=5.0)
    p.add_argument("--top-quantile", type=float, default=0.10)
    p.add_argument("--c3-decay", type=float, default=0.95)
    p.add_argument("--max-matrix-cells", type=int, default=25_000_000)
    p.add_argument("--allow-missing-returns", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    start = _to_ts(args.start_date)
    end = _to_ts(args.end_date)
    if start is not None and end is not None and end < start:
        raise ValueError(f"end-date {end.date()} is earlier than start-date {start.date()}")
    if not (0.0 < float(args.top_quantile) < 1.0):
        raise ValueError("--top-quantile must be in (0, 1)")

    features_path = _resolve_path(args.input_features, DEFAULT_FEATURES_PATH)
    default_prices = DEFAULT_PRICES_TRI_PATH if DEFAULT_PRICES_TRI_PATH.exists() else DEFAULT_PRICES_PATH
    prices_path = _resolve_path(args.input_prices, default_prices)
    output_dir = _resolve_path(args.output_dir, DEFAULT_OUTPUT_DIR)
    if not prices_path.exists():
        raise FileNotFoundError(f"Returns artifact not found: {prices_path}")

    walkforward_path = output_dir / "phase18_day6_walkforward.csv"
    decay_path = output_dir / "phase18_day6_decay_sensitivity.csv"
    crisis_path = output_dir / "phase18_day6_crisis_turnover.csv"
    checks_path = output_dir / "phase18_day6_checks.csv"
    summary_path = output_dir / "phase18_day6_summary.json"

    baseline_specs = build_default_factor_specs()
    c3_specs = _build_c3_specs(float(args.c3_decay))
    all_candidates = sorted({c for s in (baseline_specs + c3_specs) for c in s.candidate_columns})

    print("=" * 80)
    print("PHASE 18 DAY 6: WALK-FORWARD ROBUSTNESS VALIDATION")
    print("=" * 80)
    print(f"Features: {features_path}")
    print(f"Returns:  {prices_path}")
    print(f"Window:   {start.strftime('%Y-%m-%d')} -> {end.strftime('%Y-%m-%d')}")
    print(f"C3 decay: {float(args.c3_decay):.2f}")

    features = _load_features_subset(features_path, all_candidates, start, end)
    if features.empty:
        raise RuntimeError("No feature rows found for selected Day 6 window.")
    permnos = sorted(pd.to_numeric(features["permno"], errors="coerce").dropna().astype(int).unique().tolist())
    returns = _load_returns_subset(prices_path, permnos, start, end)
    if returns.empty:
        raise RuntimeError("No return rows found for selected Day 6 window.")
    spy_returns = _load_spy_returns(prices_path, start, end)

    print("\n[1/3] Running walk-forward validation...")
    baseline_scores, baseline_summary = CompanyScorecard(
        factor_specs=baseline_specs,
        scoring_method="complete_case",
    ).compute_scores(features)
    c3_scores, c3_summary = CompanyScorecard(
        factor_specs=c3_specs,
        scoring_method="complete_case",
    ).compute_scores(features)

    baseline_sim, baseline_missing = _simulate_from_scores(
        scores=baseline_scores,
        returns_long=returns,
        top_quantile=float(args.top_quantile),
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )
    c3_sim, c3_missing = _simulate_from_scores(
        scores=c3_scores,
        returns_long=returns,
        top_quantile=float(args.top_quantile),
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )

    walkforward = run_walk_forward_validation(
        baseline_sim=baseline_sim,
        c3_sim=c3_sim,
        baseline_scores=baseline_scores,
        c3_scores=c3_scores,
        spy_returns=spy_returns,
    )
    _atomic_csv_write(walkforward, walkforward_path)

    print("[2/3] Analyzing decay parameter sensitivity...")
    decay = analyze_decay_sensitivity(
        features=features,
        returns=returns,
        spy_returns=spy_returns,
        top_quantile=float(args.top_quantile),
        cost_bps=float(args.cost_bps),
        allow_missing_returns=bool(args.allow_missing_returns),
        max_matrix_cells=int(args.max_matrix_cells),
    )
    _atomic_csv_write(decay, decay_path)

    print("[3/3] Validating crisis turnover behavior...")
    crisis = validate_crisis_turnover(baseline_sim, c3_sim)
    _atomic_csv_write(crisis, crisis_path)

    checks = evaluate_checks(walkforward, decay, crisis)
    _atomic_csv_write(checks, checks_path)

    total = int(len(checks))
    passed = int(pd.to_numeric(checks["pass"], errors="coerce").fillna(False).astype(bool).sum())
    failed = int(total - passed)
    all_pass = bool(failed == 0)

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    for _, row in checks.iterrows():
        status = "PASS" if bool(row["pass"]) else "FAIL"
        print(f"{status} {row['check_id']}: value={row['value']} target={row['target']}")
    if all_pass:
        print("\nALL DAY 6 CHECKS PASSED")
    else:
        print("\nDAY 6 HAS CHECK FAILURES (see checks CSV)")

    _atomic_json_write(
        {
            "status": "ok",
            "all_pass": all_pass,
            "checks_total": total,
            "checks_passed": passed,
            "checks_failed": failed,
            "c3_decay": float(args.c3_decay),
            "coverage": {
                "baseline_complete_case": float(baseline_summary.coverage),
                "c3_complete_case": float(c3_summary.coverage),
            },
            "missing_active_return_cells": {
                "baseline": int(baseline_missing),
                "c3": int(c3_missing),
            },
            "artifacts": {
                "walkforward_csv": str(walkforward_path),
                "decay_csv": str(decay_path),
                "crisis_csv": str(crisis_path),
                "checks_csv": str(checks_path),
            },
        },
        summary_path,
    )

    print(f"\nWalk-forward CSV: {walkforward_path}")
    print(f"Decay CSV:        {decay_path}")
    print(f"Crisis CSV:       {crisis_path}")
    print(f"Checks CSV:       {checks_path}")
    print(f"Summary JSON:     {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
