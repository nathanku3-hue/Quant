from __future__ import annotations

import pytest

from strategies.production_config import CONFIG_VERSION_HISTORY
from strategies.production_config import PRODUCTION_CONFIG_V1
from strategies.production_config import build_c3_production_config


def test_c3_production_config_locks_integrator_toggles() -> None:
    config = build_c3_production_config(decay=0.95, top_quantile=0.10, cost_bps=5.0)

    assert config.config_id == "C3_LEAKY_INTEGRATOR_V1"
    assert config.scoring_method == "complete_case"
    assert config.leaky_alpha == pytest.approx(0.05)
    assert config.top_quantile == pytest.approx(0.10)
    assert config.cost_bps == pytest.approx(5.0)
    assert config.factor_specs
    assert all(spec.use_leaky_integrator for spec in config.factor_specs)
    assert all(not spec.use_sigmoid_blend for spec in config.factor_specs)
    assert all(not spec.use_dirty_derivative for spec in config.factor_specs)
    assert all(spec.leaky_alpha == pytest.approx(0.05) for spec in config.factor_specs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"decay": 0.0},
        {"decay": 1.0},
        {"top_quantile": 0.0},
        {"top_quantile": 1.0},
        {"cost_bps": -0.01},
    ],
)
def test_c3_production_config_rejects_invalid_bounds(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        build_c3_production_config(**kwargs)


def test_production_config_version_history_matches_locked_config() -> None:
    history = CONFIG_VERSION_HISTORY["v1"]

    assert history["config_id"] == PRODUCTION_CONFIG_V1.config_id
    assert history["lock_date"] == PRODUCTION_CONFIG_V1.lock_date
    assert history["round_id"] == PRODUCTION_CONFIG_V1.lock_round_id
    assert history["c3_decay"] == PRODUCTION_CONFIG_V1.c3_decay
    assert history["scoring_method"] == PRODUCTION_CONFIG_V1.scoring_method
