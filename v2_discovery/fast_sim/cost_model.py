from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.validation import validate_finite_numeric


@dataclass(frozen=True)
class FastProxyCostModel:
    total_cost_bps: float = 10.0
    initial_cash: float = 100_000.0
    max_gross_exposure: float = 1.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "total_cost_bps",
            _non_negative_float(self.total_cost_bps, "total_cost_bps"),
        )
        object.__setattr__(
            self,
            "initial_cash",
            _positive_float(self.initial_cash, "initial_cash"),
        )
        object.__setattr__(
            self,
            "max_gross_exposure",
            _positive_float(self.max_gross_exposure, "max_gross_exposure"),
        )

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "FastProxyCostModel":
        if not isinstance(payload, Mapping):
            raise ProxyBoundaryError("cost_model must be a mapping")
        return cls(
            total_cost_bps=_non_negative_float(
                payload.get("total_cost_bps", payload.get("cost_bps", 10.0)),
                "total_cost_bps",
            ),
            initial_cash=_positive_float(payload.get("initial_cash", 100_000.0), "initial_cash"),
            max_gross_exposure=_positive_float(
                payload.get("max_gross_exposure", 1.0),
                "max_gross_exposure",
            ),
        )

    @property
    def cost_rate(self) -> float:
        return self.total_cost_bps / 10_000.0

    def transaction_cost(self, *, equity: float, turnover: float) -> float:
        equity_value = _non_negative_float(equity, "equity")
        turnover_value = _non_negative_float(turnover, "turnover")
        return equity_value * turnover_value * self.cost_rate


def _non_negative_float(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ProxyBoundaryError(f"{field} must be numeric") from exc
    validate_finite_numeric(
        pd.DataFrame({field: [parsed]}),
        (field,),
        "synthetic cost_model",
    )
    if parsed < 0:
        raise ProxyBoundaryError(f"{field} must be non-negative")
    return parsed


def _positive_float(value: Any, field: str) -> float:
    parsed = _non_negative_float(value, field)
    if parsed <= 0:
        raise ProxyBoundaryError(f"{field} must be positive")
    return parsed
