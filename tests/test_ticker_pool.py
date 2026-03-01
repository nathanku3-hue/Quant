from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategies.ticker_pool import CYCLICAL_ANCHORS
from strategies.ticker_pool import TickerPoolConfig
from strategies.ticker_pool import _build_weighted_zmat_with_imputation
from strategies.ticker_pool import _normalize_boolean_series
from strategies.ticker_pool import _path1_sector_projection_residualize
from strategies.ticker_pool import _robust_zscore
from strategies.ticker_pool import rank_ticker_pool


def _make_pool_frame(n: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    tickers = [f"T{idx:03d}" for idx in range(n)]
    base = pd.DataFrame(
        {
            "date": pd.Timestamp("2024-12-31"),
            "permno": np.arange(10000, 10000 + n),
            "ticker": tickers,
            "score": np.linspace(0.2, 0.9, n),
            "rev_accel": np.linspace(-0.3, 1.0, n),
            "inv_vel_traj": rng.normal(0.05, 0.2, size=n),
            "gm_traj": rng.normal(0.03, 0.15, size=n),
            "op_lev": rng.normal(0.00, 0.2, size=n),
            "intang_intensity": rng.uniform(0.05, 0.95, size=n),
            "q_tot": rng.normal(1.20, 0.3, size=n),
            "rmw": rng.normal(0.01, 0.03, size=n),
            "cma": rng.normal(0.00, 0.02, size=n),
            "yield_slope_10y2y": rng.normal(0.50, 0.25, size=n),
            "CycleSetup": rng.normal(0.00, 0.3, size=n),
            # Diagnostics for junk/quality path.
            "revenue_growth_q": rng.normal(0.08, 0.2, size=n),
            "ebitda_accel": rng.normal(0.02, 0.2, size=n),
            "roic_accel": rng.normal(0.01, 0.2, size=n),
            "gm_accel_q": rng.normal(0.00, 0.2, size=n),
            "operating_margin_delta_q": rng.normal(0.00, 0.1, size=n),
            "style_compounder_gate": False,
            "weak_quality_liquidity": False,
        }
    )
    base.loc[:7, "style_compounder_gate"] = True
    base.loc[:1, "ticker"] = ["MU", "CIEN"]
    return base


def _raw_geometry_score(frame: pd.DataFrame) -> pd.Series:
    return (
        (2.0 * pd.to_numeric(frame["CycleSetup"], errors="coerce"))
        + pd.to_numeric(frame["op_lev"], errors="coerce")
        + pd.to_numeric(frame["rev_accel"], errors="coerce")
        + pd.to_numeric(frame["inv_vel_traj"], errors="coerce")
        - pd.to_numeric(frame["q_tot"], errors="coerce")
    )


def test_rank_ticker_pool_emits_raw_geometry_contract_columns():
    frame = _make_pool_frame()
    out = rank_ticker_pool(frame)

    required = {
        "mahalanobis_distance",
        "compounder_prob",
        "pool_long_candidate",
        "pool_short_candidate",
        "pool_action",
        "shrinkage_method",
        "shrinkage_coeff",
        "centroid_source",
        "centroid_quarter",
        "centroid_knn_count",
        "centroid_seed_used",
        "centroid_seed_missing",
        "dictatorship_mode",
        "path1_feature_allow",
        "path1_feature_deny",
        "path1_residualization",
        "path1_sector_count",
        "path1_cov_resample",
        "path1_cov_resample_n",
        "path1_cov_resample_per_sector",
        "path1_cov_resample_seed",
    }
    assert required.issubset(set(out.columns))
    assert out["mahalanobis_distance"].notna().any()
    assert out["compounder_prob"].between(0.0, 1.0).dropna().all()
    assert out["shrinkage_method"].astype(str).eq("golden_master_raw_geometry").all()
    assert out["centroid_source"].astype(str).eq("legacy_topk_raw_geometry").all()
    assert (~out["dictatorship_mode"].astype(bool)).all()
    assert out["path1_residualization"].astype(str).eq("not_run_raw_geometry").all()
    assert out["path1_cov_resample"].astype(str).eq("not_run_raw_geometry").all()
    assert out["path1_cov_resample_per_sector"].astype(int).eq(0).all()
    assert out["geometry_industry_impute_cells"].astype(int).eq(0).all()
    assert out["geometry_sector_impute_cells"].astype(int).eq(0).all()
    assert out["geometry_zero_impute_cells"].astype(int).eq(0).all()


def test_rank_ticker_pool_odds_score_matches_raw_formula():
    frame = _make_pool_frame()
    out = rank_ticker_pool(frame)

    expected = _raw_geometry_score(frame)
    valid_mask = out["odds_score"].notna()
    assert np.allclose(
        out.loc[valid_mask, "odds_score"].to_numpy(dtype=float),
        expected.loc[valid_mask].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
        equal_nan=False,
    )


def test_rank_ticker_pool_long_candidates_use_raw_score_percentile_cut():
    frame = _make_pool_frame()
    frame["style_compounder_gate"] = False
    frame["weak_quality_liquidity"] = False
    cfg = TickerPoolConfig(min_universe=12, long_prob_threshold=1.10)
    out = rank_ticker_pool(frame, config=cfg)

    score = _raw_geometry_score(frame)
    pct_rank_desc = score.rank(method="average", ascending=False, pct=True)
    expected_mask = pct_rank_desc <= 0.05

    got = out["pool_long_candidate"].fillna(False).astype(bool)
    assert int(got.sum()) == int(expected_mask.sum())
    assert got.equals(expected_mask.reindex(got.index).fillna(False))
    assert set(out.loc[got, "pool_action"].unique()).issubset({"LONG"})


def test_rank_ticker_pool_short_marks_far_tail_weak_quality():
    frame = _make_pool_frame()
    outlier_idx = frame.index[-1]
    frame.loc[
        outlier_idx,
        [
            "rev_accel",
            "inv_vel_traj",
            "gm_traj",
            "op_lev",
            "intang_intensity",
            "q_tot",
            "CycleSetup",
            "revenue_growth_q",
            "ebitda_accel",
            "roic_accel",
        ],
    ] = [-4.0, -4.0, -3.0, -3.0, -2.5, -2.0, -4.0, -3.0, -3.0, -3.0]
    frame["weak_quality_liquidity"] = False
    frame.loc[outlier_idx, "weak_quality_liquidity"] = True

    out = rank_ticker_pool(frame)

    assert bool(out.loc[outlier_idx, "pool_short_candidate"])
    assert out.loc[outlier_idx, "pool_action"] == "SHORT"


def test_rank_ticker_pool_parses_string_weak_quality_tokens_deterministically():
    frame = _make_pool_frame()
    true_idx = frame.index[-1]
    unknown_idx = frame.index[-2]
    degrade_cols = [
        "rev_accel",
        "inv_vel_traj",
        "gm_traj",
        "op_lev",
        "intang_intensity",
        "q_tot",
        "CycleSetup",
        "revenue_growth_q",
        "ebitda_accel",
        "roic_accel",
    ]
    frame.loc[true_idx, degrade_cols] = [-4.0, -4.0, -3.0, -3.0, -2.5, -2.0, -4.0, -3.0, -3.0, -3.0]
    frame.loc[unknown_idx, degrade_cols] = [-4.0, -4.0, -3.0, -3.0, -2.5, -2.0, -4.0, -3.0, -3.0, -3.0]

    frame["style_compounder_gate"] = "false"
    frame.loc[true_idx, "style_compounder_gate"] = "YES"
    frame["weak_quality_liquidity"] = "false"
    frame.loc[true_idx, "weak_quality_liquidity"] = "  TRUE  "
    frame.loc[unknown_idx, "weak_quality_liquidity"] = "MAYBE"

    out = rank_ticker_pool(frame)

    assert bool(out.loc[true_idx, "pool_short_candidate"])
    assert not bool(out.loc[unknown_idx, "pool_short_candidate"])


def test_rank_ticker_pool_compounder_prob_monotonic_with_raw_score():
    frame = _make_pool_frame()
    out = rank_ticker_pool(frame)
    scored = out.loc[out["odds_score"].notna(), ["odds_score", "compounder_prob"]]
    scored = scored.sort_values("odds_score", ascending=True)
    probs = scored["compounder_prob"].to_numpy()
    assert len(probs) > 5
    assert np.all(np.diff(probs) >= -1e-12)


def test_normalize_boolean_series_accepts_string_and_numeric_boolean_tokens():
    values = pd.Series(
        ["true", "False", "YES", "off", "1", "0", 1, 0, True, False, "unknown", np.nan],
        dtype="object",
    )
    got = _normalize_boolean_series(values, default=False)
    expected = pd.Series(
        [True, False, True, False, True, False, True, False, True, False, False, False],
        index=values.index,
        dtype=bool,
    )
    assert got.equals(expected)


def test_rank_ticker_pool_dynamic_centroid_metadata_present():
    day1 = _make_pool_frame()
    day1["date"] = pd.Timestamp("2024-03-29")
    day2 = _make_pool_frame()
    day2["date"] = pd.Timestamp("2024-04-01")
    frame = pd.concat([day1, day2], ignore_index=True)

    out = rank_ticker_pool(frame)
    q1 = out.loc[out["centroid_quarter"] == "2024Q1"]
    q2 = out.loc[out["centroid_quarter"] == "2024Q2"]
    assert not q1.empty
    assert not q2.empty
    assert q1["centroid_source"].astype(str).str.len().gt(0).all()
    assert q2["centroid_source"].astype(str).str.len().gt(0).all()


def test_rank_ticker_pool_rejects_post_pool_score_col():
    frame = _make_pool_frame()
    frame["odds_score"] = frame["score"]
    try:
        rank_ticker_pool(frame, score_col="odds_score")
        assert False, "Expected ValueError for pool-derived score_col"
    except ValueError as exc:
        assert "pre-pool metric" in str(exc)


def test_rank_ticker_pool_allows_prepool_score_name_with_odds_token():
    frame = _make_pool_frame()
    frame["odds_adjusted_prepool"] = frame["score"]
    out = rank_ticker_pool(frame, score_col="odds_adjusted_prepool")
    assert out["mahalanobis_distance"].notna().any()


def test_rank_ticker_pool_anchor_seed_metadata_reports_present_and_missing():
    frame = _make_pool_frame()
    anchors_present = ["MU", "LRCX", "AMAT", "KLAC"]
    frame.loc[:3, "ticker"] = anchors_present

    out = rank_ticker_pool(frame)
    used_raw = out["centroid_seed_used"].astype(str).replace({"": np.nan}).dropna()
    missing_raw = out["centroid_seed_missing"].astype(str).replace({"": np.nan}).dropna()
    assert not used_raw.empty
    assert not missing_raw.empty

    used = set(used_raw.iloc[0].split(","))
    missing = set(missing_raw.iloc[0].split(","))
    assert set(anchors_present).issubset(used)
    assert used.issubset(set(CYCLICAL_ANCHORS))
    assert "STX" in missing
    assert "WDC" in missing


def test_rank_ticker_pool_path1_partition_guard_rejects_overlap():
    frame = _make_pool_frame()
    cfg = TickerPoolConfig(
        path1_allow_features=("rev_accel", "inv_vel_traj"),
        path1_deny_features=("inv_vel_traj", "gm_traj"),
    )
    with pytest.raises(ValueError, match="allow/deny overlap"):
        rank_ticker_pool(frame, config=cfg)


def test_rank_ticker_pool_rejects_risk_feature_in_geometry():
    frame = _make_pool_frame()
    cfg = TickerPoolConfig(
        feature_columns=("rev_accel", "asset_beta_lag"),
        path1_allow_features=("rev_accel", "asset_beta_lag"),
        path1_deny_features=(),
    )
    with pytest.raises(ValueError, match="forbidden in BGM geometry"):
        rank_ticker_pool(frame, config=cfg)


def test_rank_ticker_pool_rejects_non_coercible_dates_with_count():
    frame = _make_pool_frame()
    frame.loc[frame.index[0], "date"] = "not-a-date"
    frame.loc[frame.index[1], "date"] = "also-not-a-date"

    with pytest.raises(ValueError, match=r"date contains 2 non-coercible rows"):
        rank_ticker_pool(frame)


def test_rank_ticker_pool_dictatorship_flag_does_not_change_raw_geometry_mode():
    frame = _make_pool_frame()
    frame.loc[:3, "ticker"] = ["MU", "LRCX", "AMAT", "KLAC"]
    cfg = TickerPoolConfig(dictatorship_mode=False)
    out = rank_ticker_pool(frame, config=cfg)
    assert out["centroid_source"].astype(str).eq("legacy_topk_raw_geometry").all()
    assert (~out["dictatorship_mode"].astype(bool)).all()


def test_rank_ticker_pool_path1_telemetry_emits_raw_geometry_constants_and_seed():
    frame = _make_pool_frame()
    frame["sector"] = np.select(
        [frame.index < 8, frame.index < 16],
        ["Semis", "Retail"],
        default="Utilities",
    )
    out = rank_ticker_pool(frame)
    active = out.loc[out["mahalanobis_distance"].notna()].copy()
    assert not active.empty
    assert active["path1_residualization"].eq("not_run_raw_geometry").all()
    assert active["path1_cov_resample"].eq("not_run_raw_geometry").all()
    assert set(active["path1_cov_resample_seed"].astype(int).unique()) == {20241231}
    assert set(active["path1_cov_resample_n"].astype(int).unique()) == {24}
    assert set(active["path1_cov_resample_per_sector"].astype(int).unique()) == {0}
    assert set(active["path1_sector_count"].astype(int).unique()) == {3}


def test_rank_ticker_pool_raw_geometry_is_deterministic_under_row_shuffle():
    frame = _make_pool_frame()
    frame["sector"] = np.select(
        [frame.index < 12, frame.index < 20],
        ["Semis", "Retail"],
        default="Utilities",
    )
    out1 = rank_ticker_pool(frame)

    shuffled = frame.sample(frac=1.0, random_state=123).reset_index(drop=True)
    out2 = rank_ticker_pool(shuffled)

    cols = ["mahalanobis_distance", "odds_score", "path1_cov_resample_seed", "path1_cov_resample_n", "compounder_prob"]
    lhs = frame[["permno"]].join(out1[cols]).sort_values("permno").reset_index(drop=True)
    rhs = shuffled[["permno"]].join(out2[cols]).sort_values("permno").reset_index(drop=True)

    assert lhs["permno"].tolist() == rhs["permno"].tolist()
    assert np.allclose(
        lhs["mahalanobis_distance"].to_numpy(dtype=float),
        rhs["mahalanobis_distance"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
        equal_nan=True,
    )
    assert np.allclose(
        lhs["odds_score"].to_numpy(dtype=float),
        rhs["odds_score"].to_numpy(dtype=float),
        rtol=0.0,
        atol=1e-12,
        equal_nan=True,
    )
    assert lhs["path1_cov_resample_seed"].astype(int).tolist() == rhs["path1_cov_resample_seed"].astype(int).tolist()
    assert lhs["path1_cov_resample_n"].astype(int).tolist() == rhs["path1_cov_resample_n"].astype(int).tolist()


def test_rank_ticker_pool_marks_rows_without_any_geometry_features_invalid():
    frame = _make_pool_frame()
    raw_cols = ["rev_accel", "inv_vel_traj", "op_lev", "q_tot", "CycleSetup"]
    zero_rows = frame.index[::3]
    frame.loc[zero_rows, raw_cols] = np.nan

    cfg = TickerPoolConfig(min_universe=8)
    out = rank_ticker_pool(frame, config=cfg)
    active = out.loc[out["mahalanobis_distance"].notna()].copy()

    expected_valid = int((~frame[raw_cols].isna().all(axis=1)).sum())
    assert len(active) == expected_valid
    assert set(active["geometry_universe_before_imputation"].astype(int).unique()) == {expected_valid}
    assert set(active["geometry_universe_after_imputation"].astype(int).unique()) == {expected_valid}
    assert out["geometry_industry_impute_cells"].astype(int).eq(0).all()
    assert out["geometry_sector_impute_cells"].astype(int).eq(0).all()
    assert out["geometry_zero_impute_cells"].astype(int).eq(0).all()


def test_robust_zscore_uses_locked_sigma_formula_without_std_fallback():
    values = pd.Series([1.0, 2.0, 4.0, 7.0], dtype=float)
    got, telemetry = _robust_zscore(
        values,
        epsilon_floor=1e-6,
        min_window_size=2,
        return_telemetry=True,
    )

    median = float(values.median())
    mad = float((values - median).abs().median())
    robust_sigma = max(1.4826 * mad, 1e-6)
    expected = (values - median) / robust_sigma
    np.testing.assert_allclose(got.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=0.0, atol=1e-12)
    assert telemetry["fallback_rows"] == 0
    assert telemetry["row_total"] == 1
    assert telemetry["fallback_rate"] == 0.0


def test_robust_zscore_insufficient_window_routes_to_percentile_fallback():
    values = pd.Series([10.0, 20.0, 30.0], dtype=float)
    got, telemetry = _robust_zscore(
        values,
        epsilon_floor=1e-6,
        min_window_size=5,
        return_telemetry=True,
    )
    expected = ((values.rank(method="average", pct=True) - 0.5) * 2.0).astype(float)
    np.testing.assert_allclose(got.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=0.0, atol=1e-12)
    assert telemetry["fallback_rows"] == 1
    assert telemetry["row_total"] == 1
    assert telemetry["fallback_rate"] == 1.0


def test_build_weighted_zmat_reports_fallback_rate_arithmetic():
    n = 24
    block = pd.DataFrame(
        {
            "rev_accel": np.linspace(-1.0, 1.0, n),
            "inv_vel_traj": np.linspace(1.0, 2.0, n),
            "op_lev": np.linspace(-0.5, 0.5, n),
            "q_tot": np.linspace(0.2, 0.9, n),
            "CycleSetup": np.linspace(-0.3, 0.3, n),
            "sector": ["Semis"] * n,
        }
    )
    cfg = TickerPoolConfig()
    _, stats = _build_weighted_zmat_with_imputation(block, cfg)
    assert int(stats["scale_row_total"]) == len(cfg.feature_columns)
    assert int(stats["scale_fallback_rows"]) == 0
    assert float(stats["scale_fallback_rate"]) == 0.0

    small_block = block.iloc[:8].copy()
    _, small_stats = _build_weighted_zmat_with_imputation(small_block, cfg)
    expected_rate = float(small_stats["scale_fallback_rows"]) / float(small_stats["scale_row_total"])
    assert float(small_stats["scale_fallback_rate"]) == expected_rate
    assert float(small_stats["scale_fallback_rate"]) == 1.0


def test_sector_projection_residualize_matches_vectorized_sector_demeaning():
    x = pd.DataFrame(
        {
            "f1": [1.0, 3.0, 10.0, 14.0],
            "f2": [2.0, 6.0, 8.0, 12.0],
        },
        index=[100, 101, 200, 201],
    )
    sectors = pd.Series(["A", "A", "B", "B"], index=x.index, dtype="string")
    got, mode, sector_count = _path1_sector_projection_residualize(x, sectors)

    expected = x - x.groupby(sectors, sort=False).transform("mean")
    np.testing.assert_allclose(got.to_numpy(dtype=float), expected.to_numpy(dtype=float), rtol=0.0, atol=1e-12)
    assert mode == "sector_projection_residualized"
    assert sector_count == 2
    assert np.allclose(
        got.groupby(sectors, sort=False).mean().to_numpy(dtype=float),
        np.zeros((2, 2), dtype=float),
        rtol=0.0,
        atol=1e-12,
    )
