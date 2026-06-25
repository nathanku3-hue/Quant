"""
Phase 18 production configuration lock.

This module freezes the accepted C3 integrator configuration so downstream
runtime paths can import a canonical, immutable config object.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from typing import Literal

from strategies.factor_specs import FactorSpec
from strategies.factor_specs import build_default_factor_specs
from strategies.factor_specs import validate_factor_specs


ScoringMethod = Literal["complete_case"]


@dataclass(frozen=True)
class ProductionConfig:
    config_id: str
    phase: str
    lock_round_id: str
    lock_date: str
    rationale: str
    scoring_method: ScoringMethod
    top_quantile: float
    cost_bps: float
    c3_decay: float
    factor_specs: tuple[FactorSpec, ...]

    @property
    def leaky_alpha(self) -> float:
        return 1.0 - float(self.c3_decay)


def build_c3_production_config(
    *,
    decay: float = 0.95,
    top_quantile: float = 0.10,
    cost_bps: float = 5.0,
) -> ProductionConfig:
    if not 0.0 < float(decay) < 1.0:
        raise ValueError(f"decay must be in (0,1), got {decay}")
    if not 0.0 < float(top_quantile) < 1.0:
        raise ValueError(f"top_quantile must be in (0,1), got {top_quantile}")
    if float(cost_bps) < 0.0:
        raise ValueError(f"cost_bps must be >= 0, got {cost_bps}")

    alpha = 1.0 - float(decay)
    specs = tuple(
        replace(
            spec,
            use_sigmoid_blend=False,
            use_dirty_derivative=False,
            use_leaky_integrator=True,
            leaky_alpha=alpha,
        )
        for spec in build_default_factor_specs()
    )
    validate_factor_specs(list(specs))

    return ProductionConfig(
        config_id="C3_LEAKY_INTEGRATOR_V1",
        phase="Phase 18",
        lock_round_id="R18_D6_WALKFWD_20260220",
        lock_date="2026-02-20",
        rationale=(
            "Accepted as-is after Day 5/Day 6 advisory closure; preserve simple "
            "integrator-only design with complete-case scoring."
        ),
        scoring_method="complete_case",
        top_quantile=float(top_quantile),
        cost_bps=float(cost_bps),
        c3_decay=float(decay),
        factor_specs=specs,
    )


PRODUCTION_CONFIG_V1 = build_c3_production_config()


CONFIG_VERSION_HISTORY = {
    "v1": {
        "lock_date": PRODUCTION_CONFIG_V1.lock_date,
        "round_id": PRODUCTION_CONFIG_V1.lock_round_id,
        "config_id": PRODUCTION_CONFIG_V1.config_id,
        "c3_decay": PRODUCTION_CONFIG_V1.c3_decay,
        "scoring_method": PRODUCTION_CONFIG_V1.scoring_method,
        "top_quantile": PRODUCTION_CONFIG_V1.top_quantile,
        "cost_bps": PRODUCTION_CONFIG_V1.cost_bps,
        "day5_best_config": "ABLATION_C3_INTEGRATOR",
        "day6_critical_gate": "CHK-54 PASS",
    }
}

