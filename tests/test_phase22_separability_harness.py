from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from scripts.phase22_separability_harness import _archetype_rank_metrics
from scripts.phase22_separability_harness import _compute_silhouette_metrics
from scripts.phase22_separability_harness import _jaccard_index


def test_jaccard_index_returns_expected_overlap():
    lhs = {"MU", "LRCX", "AMAT"}
    rhs = {"LRCX", "AMAT", "KLAC"}
    score = _jaccard_index(lhs, rhs)
    assert np.isclose(score, 2.0 / 4.0, atol=1e-12)


def test_jaccard_index_empty_union_is_nan():
    score = _jaccard_index(set(), set())
    assert np.isnan(score)


def test_compute_silhouette_metrics_one_effective_class_returns_nan():
    geometry = pd.DataFrame(
        {
            "f1": [0.0, 0.1, 0.2, 0.3],
            "f2": [1.0, 1.1, 1.2, 1.3],
        },
        index=[10, 11, 12, 13],
    )
    labels = pd.Series("cyclical", index=geometry.index, dtype="object")
    out = _compute_silhouette_metrics(geometry, labels)
    assert np.isnan(out["silhouette_score"])
    assert out["silhouette_reason"] == "one_effective_class"
    assert out["silhouette_label_rows"] == 4
    assert out["silhouette_effective_classes"] == 1
    assert out["silhouette_cyclical_n"] == 4
    assert out["silhouette_defensive_n"] == 0
    assert out["silhouette_junk_n"] == 0


def test_compute_silhouette_metrics_two_classes_returns_finite_when_available():
    geometry = pd.DataFrame(
        {
            "f1": [0.0, 0.0, 4.0, 4.0],
            "f2": [0.0, 1.0, 4.0, 5.0],
        },
        index=[10, 11, 12, 13],
    )
    labels = pd.Series(
        ["cyclical", "cyclical", "defensive", "defensive"],
        index=geometry.index,
        dtype="object",
    )
    out = _compute_silhouette_metrics(geometry, labels)
    assert out["silhouette_reason"] in {"ok", "ok_manual"}
    assert np.isfinite(out["silhouette_score"])
    assert out["silhouette_score"] > 0.0
    assert out["silhouette_effective_classes"] == 2


def test_archetype_rank_metrics_tracks_hits_with_fixed_topn_label():
    ranked = pd.DataFrame(
        {
            "ticker_u": ["MU", "NVDA", "LRCX", "AMAT", "AAPL"],
            "odds_score": [9.0, 8.0, 7.0, 6.0, 5.0],
        }
    )
    out = _archetype_rank_metrics(
        ranked_block=ranked,
        top_decile_n=1,
        top_n_label=30,
        top_n_eff=5,
    )
    assert bool(out["mu_present"]) is True
    assert float(out["mu_rank"]) == 1.0
    assert bool(out["mu_top_decile_hit"]) is True
    assert bool(out["mu_top_30_hit"]) is True
    assert bool(out["lrcx_top_30_hit"]) is True
    assert bool(out["amat_top_30_hit"]) is True
    assert bool(out["klac_present"]) is False
    assert np.isnan(out["klac_rank"])
    assert bool(out["klac_top_30_hit"]) is False
    assert out["archetype_top_decile_hits"] == 1
    assert out["archetype_top_30_hits"] == 3
