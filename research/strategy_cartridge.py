"""Minimal strategy cartridge validation for canonical research runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class StrategyCartridge:
    """Declarative inputs required before a strategy can enter the runner."""

    strategy_id: str
    strategy_version: str
    strategy_role: str
    universe_mode: str
    input_loader_name: str
    rebalance_schedule: str
    execution_lag: str
    turnover_cost_rate: float | None
    benchmark_policy: Mapping[str, Any] | None
    start_date: str
    end_date: str
    output_dir: str | Path
    long_only: bool = True
    source_signatures_required: bool = True
    min_required_trading_days: int = 252
    hypothesis: str = ""
    owner: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the cartridge into JSON-friendly evidence metadata."""

        return {
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "strategy_role": self.strategy_role,
            "universe_mode": self.universe_mode,
            "input_loader_name": self.input_loader_name,
            "rebalance_schedule": self.rebalance_schedule,
            "execution_lag": self.execution_lag,
            "turnover_cost_rate": self.turnover_cost_rate,
            "benchmark_policy": dict(self.benchmark_policy or {}),
            "window": {
                "start_date": self.start_date,
                "end_date": self.end_date,
                "min_required_trading_days": self.min_required_trading_days,
            },
            "output_dir": str(self.output_dir),
            "portfolio": {
                "long_only": self.long_only,
                "cash_policy": "implicit_residual_cash",
            },
            "source_signatures_required": self.source_signatures_required,
            "hypothesis": self.hypothesis,
            "owner": self.owner,
            "metadata": dict(self.metadata),
        }


def cartridge_from_mapping(data: Mapping[str, Any]) -> StrategyCartridge:
    """Build a cartridge from a flat mapping without adding a heavy dependency."""

    window = data.get("window") or {}
    costs = data.get("costs") or {}
    inputs = data.get("inputs") or {}
    universe = data.get("universe") or {}
    portfolio = data.get("portfolio") or {}
    return StrategyCartridge(
        strategy_id=data.get("strategy_id", ""),
        strategy_version=data.get("strategy_version", ""),
        strategy_role=data.get("strategy_role", ""),
        universe_mode=data.get("universe_mode") or universe.get("universe_mode", ""),
        input_loader_name=(
            data.get("input_loader_name")
            or inputs.get("input_loader")
            or data.get("input_source_id")
            or ""
        ),
        rebalance_schedule=data.get("rebalance_schedule") or data.get("signal", {}).get("rebalance_schedule", ""),
        execution_lag=data.get("execution_lag") or data.get("signal", {}).get("execution_lag", ""),
        turnover_cost_rate=(
            data.get("turnover_cost_rate")
            if "turnover_cost_rate" in data
            else costs.get("turnover_cost_rate")
        ),
        benchmark_policy=data.get("benchmark_policy") or data.get("benchmarks"),
        start_date=data.get("start_date") or window.get("start_date", ""),
        end_date=data.get("end_date") or window.get("end_date", ""),
        output_dir=data.get("output_dir") or data.get("outputs", {}).get("output_dir", ""),
        long_only=bool(portfolio.get("long_only", data.get("long_only", True))),
        source_signatures_required=bool(
            inputs.get("source_signatures_required", data.get("source_signatures_required", True))
        ),
        min_required_trading_days=int(window.get("min_required_trading_days", data.get("min_required_trading_days", 252))),
        hypothesis=data.get("hypothesis", ""),
        owner=data.get("owner", ""),
        metadata=data.get("metadata") or {},
    )


def validate_cartridge(cartridge: StrategyCartridge | Mapping[str, Any]) -> list[str]:
    """Return gate failures for required cartridge fields."""

    if not isinstance(cartridge, StrategyCartridge):
        cartridge = cartridge_from_mapping(cartridge)

    failures: list[str] = []
    required_string_fields = (
        "strategy_id",
        "strategy_version",
        "strategy_role",
        "universe_mode",
        "input_loader_name",
        "rebalance_schedule",
        "execution_lag",
        "start_date",
        "end_date",
        "output_dir",
    )
    for field_name in required_string_fields:
        if not str(getattr(cartridge, field_name, "")).strip():
            failures.append(f"missing_{field_name}")

    if cartridge.turnover_cost_rate is None:
        failures.append("missing_cost_policy")
    else:
        try:
            cost_rate = float(cartridge.turnover_cost_rate)
        except (TypeError, ValueError):
            failures.append("invalid_cost_policy")
        else:
            if cost_rate < 0:
                failures.append("invalid_cost_policy")

    if not cartridge.benchmark_policy:
        failures.append("missing_benchmark_policy")
    else:
        required = tuple(cartridge.benchmark_policy.get("required") or ())
        if not required:
            failures.append("missing_benchmark_policy")

    if cartridge.execution_lag != "one_bar":
        failures.append("unsupported_execution_lag")
    if not cartridge.long_only:
        failures.append("unsupported_shorting_v0")

    return failures
