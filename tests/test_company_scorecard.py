from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.scorecard_validation import build_validation_table
from strategies.company_scorecard import build_phase20_conviction_frame
from strategies.company_scorecard import CompanyScorecard
from strategies.factor_specs import FactorSpec
from strategies.factor_specs import build_default_factor_specs
from strategies.factor_specs import build_phase19_5_candidate_factor_sets
from strategies.factor_specs import correlation_audit
from strategies.factor_specs import per_regime_audit
from strategies.factor_specs import regime_adaptive_norm
from strategies.factor_specs import regime_veto
from strategies.factor_specs import validate_factor_specs


def _make_features(n_days: int = 15) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=n_days, freq="B")
    permnos = [101, 202, 303, 404]
    rows = []
    for d_i, dt in enumerate(idx):
        for p_i, permno in enumerate(permnos):
            rows.append(
                {
                    "date": dt,
                    "permno": permno,
                    "resid_mom_60d": 0.10 * p_i + 0.001 * d_i,
                    "capital_cycle_score": 0.20 * p_i - 0.002 * d_i,
                    "yz_vol_20d": 0.05 + 0.01 * (3 - p_i),
                    "amihud_20d": 1e-6 * (1 + p_i),
                }
            )
    return pd.DataFrame(rows)


def test_default_factor_specs_validate_and_toggles_default_off():
    specs = build_default_factor_specs()
    validate_factor_specs(specs)
    assert len(specs) == 4
    assert all(not s.use_sigmoid_blend for s in specs)
    assert all(not s.use_dirty_derivative for s in specs)
    assert all(not s.use_leaky_integrator for s in specs)


def test_validate_factor_specs_rejects_bad_weight_sum():
    specs = [
        FactorSpec("a", ("x",), "positive", 0.4),
        FactorSpec("b", ("y",), "negative", 0.5),
    ]
    with pytest.raises(ValueError):
        validate_factor_specs(specs)


def test_company_scorecard_resolves_fallback_columns():
    df = _make_features()
    specs = [
        FactorSpec("quality", ("quality_composite", "capital_cycle_score"), "positive", 1.0),
    ]
    scorecard = CompanyScorecard(factor_specs=specs)
    scored, summary = scorecard.compute_scores(df)

    assert "quality_source" in scored.columns
    assert set(scored["quality_source"].dropna().unique()) == {"capital_cycle_score"}
    assert summary.missing_factor_columns == tuple()
    assert summary.coverage > 0.95


def test_company_scorecard_missing_factor_family_sets_invalid_score_rows():
    df = _make_features()[["date", "permno"]].copy()
    specs = [
        FactorSpec("quality", ("quality_composite",), "positive", 1.0),
    ]
    scorecard = CompanyScorecard(factor_specs=specs)
    scored, summary = scorecard.compute_scores(df)

    assert summary.missing_factor_columns == ("quality",)
    assert summary.coverage == 0.0
    assert scored["score_valid"].eq(False).all()
    assert scored["score"].isna().all()


def test_company_scorecard_directionality_signs():
    df = _make_features()
    specs = [
        FactorSpec("mom", ("resid_mom_60d",), "positive", 0.5),
        FactorSpec("risk", ("yz_vol_20d",), "negative", 0.5),
    ]
    scorecard = CompanyScorecard(factor_specs=specs)
    scored, _ = scorecard.compute_scores(df)

    last_date = scored["date"].max()
    last = scored[scored["date"] == last_date].sort_values("permno")
    # permno=404 has highest momentum and lowest volatility in synthetic setup.
    assert float(last[last["permno"] == 404]["score"].iloc[0]) > float(last[last["permno"] == 101]["score"].iloc[0])


def test_company_scorecard_control_toggles_execute():
    df = _make_features(n_days=30)
    specs_plain = [
        FactorSpec("mom", ("resid_mom_60d",), "positive", 1.0),
    ]
    specs_toggled = [
        FactorSpec(
            "mom",
            ("resid_mom_60d",),
            "positive",
            1.0,
            use_sigmoid_blend=True,
            use_dirty_derivative=True,
            use_leaky_integrator=True,
        ),
    ]

    score_plain, _ = CompanyScorecard(factor_specs=specs_plain).compute_scores(df)
    score_toggled, _ = CompanyScorecard(factor_specs=specs_toggled).compute_scores(df)
    assert score_plain["score"].notna().all()
    assert score_toggled["score"].notna().all()
    assert not np.allclose(score_plain["score"].to_numpy(), score_toggled["score"].to_numpy())


def test_company_scorecard_scoring_methods_have_expected_validity_order():
    df = _make_features(n_days=20)
    # Introduce missingness in one factor family only.
    mask = (df["permno"] == 101) | (df["permno"] == 202)
    df.loc[mask, "capital_cycle_score"] = np.nan

    specs = build_default_factor_specs()
    scored_complete, summary_complete = CompanyScorecard(
        factor_specs=specs,
        scoring_method="complete_case",
    ).compute_scores(df)
    scored_partial, summary_partial = CompanyScorecard(
        factor_specs=specs,
        scoring_method="partial",
    ).compute_scores(df)
    scored_impute, summary_impute = CompanyScorecard(
        factor_specs=specs,
        scoring_method="impute_neutral",
    ).compute_scores(df)

    cov_complete = float(scored_complete["score_valid"].mean())
    cov_partial = float(scored_partial["score_valid"].mean())
    cov_impute = float(scored_impute["score_valid"].mean())

    assert cov_complete < cov_partial
    assert cov_partial == cov_impute
    assert summary_complete.scoring_method == "complete_case"
    assert summary_partial.scoring_method == "partial"
    assert summary_impute.scoring_method == "impute_neutral"


def test_validation_table_contract():
    df = _make_features(n_days=25)
    scorecard = CompanyScorecard()
    scored, _ = scorecard.compute_scores(df)
    checks = build_validation_table(scored, factor_names=[s.name for s in build_default_factor_specs()])

    required = {"check", "target", "value", "pass"}
    assert required.issubset(set(checks.columns))
    assert len(checks) >= 5


def test_validation_table_flags_low_score_coverage():
    dates = pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03"])
    scores = pd.DataFrame(
        {
            "date": dates,
            "permno": [101, 202, 101, 202],
            "score": [1.0, np.nan, 0.5, np.nan],
            "score_valid": [True, False, True, False],
            "momentum_contrib": [0.2, 0.0, 0.1, 0.0],
            "quality_contrib": [0.1, 0.0, 0.2, 0.0],
            "volatility_contrib": [-0.1, 0.0, -0.2, 0.0],
            "illiquidity_contrib": [-0.2, 0.0, -0.1, 0.0],
        }
    )
    checks = build_validation_table(
        scores=scores,
        factor_names=["momentum", "quality", "volatility", "illiquidity"],
    )
    row = checks[checks["check"] == "score_coverage"].iloc[0]
    assert float(row["value"]) == 0.5
    assert bool(row["pass"]) is False


def test_phase19_5_candidate_sets_validate():
    sets = build_phase19_5_candidate_factor_sets()
    assert "P195_SIGNAL_STRENGTH_4F" in sets
    assert "P195_SIGNAL_STRENGTH_5F" in sets
    assert "P195_SIGNAL_STRENGTH_4F_RANK" in sets
    for specs in sets.values():
        validate_factor_specs(specs)


def test_company_scorecard_from_factor_preset_builds():
    df = _make_features(n_days=30)
    # add phase19.5 candidate columns expected by presets
    df["composite_score"] = 0.1 * df["permno"] + 0.001
    df["rsi_14d"] = 40.0 + (df["permno"] % 10)
    df["z_inventory_quality_proxy"] = 0.2
    df["z_flow_proxy"] = 0.01
    df["z_discipline_cond"] = 0.1
    df["z_demand"] = 0.2
    df["atr_14d"] = 0.03

    scorecard = CompanyScorecard.from_factor_preset(
        "P195_SIGNAL_STRENGTH_4F",
        scoring_method="partial",
    )
    scored, summary = scorecard.compute_scores(df)
    assert len(scored) == len(df)
    assert summary.coverage > 0.9


def test_company_scorecard_from_factor_preset_rejects_unknown():
    with pytest.raises(ValueError, match="Unsupported preset_name"):
        CompanyScorecard.from_factor_preset("UNKNOWN_PRESET")


def test_regime_adaptive_norm_switches_behavior():
    dates = pd.to_datetime(["2024-01-01"] * 4 + ["2024-01-02"] * 4)
    vals = pd.Series([1.0, 2.0, 3.0, 4.0, 1.0, 2.0, 3.0, 4.0])
    regime_map = pd.Series(
        ["GREEN", "RED"],
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )
    out = regime_adaptive_norm(values=vals, date_index=pd.Series(dates), regime_by_date=regime_map)
    # GREEN day behaves like zscore (mean ~0)
    green = out[:4]
    assert abs(float(green.mean())) < 1e-6
    # RED day uses centered rank range [-1,1]
    red = out[4:]
    assert float(red.min()) >= -1.0
    assert float(red.max()) <= 1.0


def test_company_scorecard_regime_adaptive_normalization():
    df = _make_features(n_days=20)
    df["z_inventory_quality_proxy"] = 0.1
    specs = [
        FactorSpec(
            "mom",
            ("resid_mom_60d",),
            "positive",
            1.0,
            normalization="regime_adaptive",
        )
    ]
    regime_map = pd.Series(
        ["GREEN"] * 10 + ["RED"] * 10,
        index=sorted(df["date"].unique()),
    )
    scored, summary = CompanyScorecard(
        factor_specs=specs,
        scoring_method="partial",
        regime_by_date=regime_map,
    ).compute_scores(df)
    assert summary.coverage > 0.9
    assert scored["score"].notna().any()


def test_correlation_audit_outputs_pairs():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2024-01-01"] * 4 + ["2024-01-02"] * 4),
            "a": [1, 2, 3, 4, 2, 3, 4, 5],
            "b": [2, 3, 4, 5, 3, 4, 5, 6],
            "c": [4, 3, 2, 1, 1, 2, 3, 4],
        }
    )
    regime = pd.Series(["GREEN", "RED"], index=pd.to_datetime(["2024-01-01", "2024-01-02"]))
    audit = correlation_audit(frame=frame, factor_columns=["a", "b", "c"], regime_by_date=regime)
    assert not audit.empty
    assert {"regime", "factor_a", "factor_b", "pearson_corr", "orthogonal_pass"}.issubset(set(audit.columns))


def test_regime_veto_marks_red_rows():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    regime = pd.Series(
        ["GREEN", "RED", "AMBER"],
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )
    veto = regime_veto(date_index=pd.Series(dates), regime_by_date=regime, blocked_regimes=("RED",))
    assert veto.tolist() == [False, True, False]


def test_company_scorecard_strict_red_veto_blocks_scores():
    df = _make_features(n_days=10)
    specs = [FactorSpec("mom", ("resid_mom_60d",), "positive", 1.0)]
    unique_dates = sorted(pd.to_datetime(df["date"]).unique())
    regime = pd.Series(
        ["GREEN"] * 5 + ["RED"] * 5,
        index=unique_dates,
    )
    scored, _ = CompanyScorecard(
        factor_specs=specs,
        scoring_method="partial",
        regime_by_date=regime,
        strict_red_veto=True,
    ).compute_scores(df)
    red_dates = set(unique_dates[5:])
    is_red = scored["date"].isin(red_dates)
    assert scored.loc[is_red, "score_valid"].eq(False).all()
    assert scored.loc[is_red, "score"].isna().all()


def test_per_regime_audit_has_spread_rows():
    df = _make_features(n_days=10)
    specs = [FactorSpec("mom", ("resid_mom_60d",), "positive", 1.0)]
    regime = pd.Series(
        ["GREEN"] * 5 + ["RED"] * 5,
        index=sorted(pd.to_datetime(df["date"]).unique()),
    )
    scored, _ = CompanyScorecard(
        factor_specs=specs,
        scoring_method="partial",
        regime_by_date=regime,
    ).compute_scores(df)
    audit = per_regime_audit(scores=scored, factor_names=["mom"], regime_by_date=regime)
    assert not audit.empty
    spread_rows = audit[audit["metric"] == "quartile_spread_sigma"]
    assert not spread_rows.empty


def test_phase20_conviction_support_proximity_is_lagged():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
    scores = pd.DataFrame(
        {
            "date": dates,
            "permno": [101, 101, 101],
            "score": [1.0, 1.0, 1.0],
            "score_valid": [True, True, True],
        }
    )
    features = pd.DataFrame(
        {
            "date": dates,
            "permno": [101, 101, 101],
            "ticker": ["AAA", "AAA", "AAA"],
            "adj_close": [100.0, 98.0, 97.0],
            "sma200": [99.0, 99.0, 99.0],
            "dist_sma20": [0.01, -0.10, -0.20],
            "resid_mom_60d": [0.10, 0.10, 0.10],
            "z_inventory_quality_proxy": [0.20, 0.20, 0.20],
            "capital_cycle_score": [0.10, 0.10, 0.10],
            "amihud_20d": [1e-6, 1e-6, 1e-6],
        }
    )
    out = build_phase20_conviction_frame(scores_df=scores, features_df=features)
    # Day 2 uses day-1 support state due shift(1), so still True here.
    day2 = out[out["date"] == pd.Timestamp("2024-01-02")].iloc[0]
    assert bool(day2["support_proximity"]) is True
    # Day 3 reflects day-2 broken support and should be False.
    day3 = out[out["date"] == pd.Timestamp("2024-01-03")].iloc[0]
    assert bool(day3["support_proximity"]) is False


def test_phase20_conviction_frame_produces_expected_columns():
    df = _make_features(n_days=8)
    df["ticker"] = np.where(df["permno"] == 101, "AAA", "BBB")
    df["adj_close"] = 100.0 + np.arange(len(df)) * 0.1
    df["dist_sma20"] = 0.02
    df["sma200"] = 99.0
    df["z_inventory_quality_proxy"] = 0.1
    df["amihud_20d"] = 1e-6

    scored, _ = CompanyScorecard(
        factor_specs=[FactorSpec("mom", ("resid_mom_60d",), "positive", 1.0)],
        scoring_method="partial",
    ).compute_scores(df)
    out = build_phase20_conviction_frame(scores_df=scored, features_df=df)
    required = {
        "conviction_score",
        "support_proximity",
        "entry_gate",
        "leverage_mult",
        "leverage_multiplier",
        "portfolio_beta",
        "gross_exposure",
        "net_exposure",
        "borrow_cost_daily",
        "avoid_or_short_flag",
    }
    assert required.issubset(set(out.columns))
    assert out["conviction_score"].between(0.0, 10.0).all()
    assert out["leverage_multiplier"].between(1.0, 1.5).all()
    assert (out["gross_exposure"] + 1e-12 >= out["net_exposure"].abs()).all()
    assert (out["borrow_cost_daily"] >= -1e-12).all()
