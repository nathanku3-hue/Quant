"""Patch A diagnostic — understand R_anchor saturation on 2024-12-24."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.phase20_full_backtest import (
    DEFAULT_FEATURES_PATH, DEFAULT_LIQUIDITY_PATH,
    DEFAULT_MACRO_FALLBACK_PATH, DEFAULT_MACRO_FEATURES_PATH,
    _load_features_window, _load_regime_states,
)
from strategies.company_scorecard import CompanyScorecard, build_phase20_conviction_frame
from strategies.production_config import PRODUCTION_CONFIG_V1
from scripts.day5_ablation_report import _to_ts

start = _to_ts("2024-01-01")
as_of = _to_ts("2024-12-24")
extra_cols = [
    "ticker", "adj_close", "dist_sma20", "sma200", "yz_vol_20d", "atr_14d",
    "revenue_growth_q", "resid_mom_60d", "z_inventory_quality_proxy",
    "capital_cycle_score", "amihud_20d", "z_discipline_cond", "z_moat", "z_demand",
]
features = _load_features_window(
    features_path=DEFAULT_FEATURES_PATH, start_date=start, end_date=as_of,
    extra_columns=extra_cols,
)
feature_dates = pd.DatetimeIndex(sorted(features["date"].dropna().unique()))
macro_path = (
    DEFAULT_MACRO_FEATURES_PATH
    if DEFAULT_MACRO_FEATURES_PATH.exists()
    else DEFAULT_MACRO_FALLBACK_PATH
)
regime, _ = _load_regime_states(
    start_date=start, end_date=as_of, feature_dates=feature_dates,
    macro_path=macro_path, liquidity_path=DEFAULT_LIQUIDITY_PATH,
)
scorecard = CompanyScorecard(
    factor_specs=list(PRODUCTION_CONFIG_V1.factor_specs),
    scoring_method=PRODUCTION_CONFIG_V1.scoring_method,
)
scores, _ = scorecard.compute_scores(features)
conviction = build_phase20_conviction_frame(
    scores_df=scores, features_df=features, regime_by_date=regime,
)

date_block = conviction[conviction["date"] == pd.Timestamp("2024-12-24")].copy()
print(f"Universe size on 2024-12-24: {len(date_block)}")

SEED = ["MU", "CIEN", "COHR", "TER"]
seed_rows = date_block[date_block["ticker"].isin(SEED)]
print(f"\nSeed tickers present: {sorted(seed_rows['ticker'].tolist())}")

cols = ["ticker", "pool_action", "posterior_cyclical", "posterior_defensive",
        "posterior_junk", "odds_score", "odds_ratio", "mahalanobis_k_cyc"]
avail = [c for c in cols if c in seed_rows.columns]
print(seed_rows[avail].to_string())

if not seed_rows.empty:
    r_anchor = seed_rows[["posterior_cyclical", "posterior_defensive", "posterior_junk"]].values.astype(float)
    mean_anchor = r_anchor.mean(axis=0)
    print(f"\nR_anchor.mean(axis=0): cyc={mean_anchor[0]:.4f}, def={mean_anchor[1]:.4f}, junk={mean_anchor[2]:.4f}")
    print(f"k_cyc (argmax): {int(np.argmax(mean_anchor))}")
    print(f"k_cyc_components (>0.05): {np.flatnonzero(mean_anchor > 0.05).tolist()}")
    print(f"k_cyc_components (>0.33): {np.flatnonzero(mean_anchor > 0.33).tolist()}")
    print(f"k_cyc_components (>max*0.5): {np.flatnonzero(mean_anchor > mean_anchor.max()*0.5).tolist()}")
    print(f"\nIf k_cyc_components=[0]: r_cyc_multi = R[:,0].sum => posterior_cyclical only")
    print(f"If k_cyc_components=[0,1,2]: r_cyc_multi = sum of all 3 = 1.0 (SATURATION)")

print("\n--- Top-8 LONG rows ---")
longs = date_block[date_block["pool_action"] == "LONG"].sort_values("odds_score", ascending=False)
avail2 = [c for c in cols if c in longs.columns]
print(longs.head(8)[avail2].to_string())
