from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from v2_discovery.fast_sim.cost_model import FastProxyCostModel
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.validation import validate_finite_numeric
from v2_discovery.fast_sim.validation import validate_no_nulls
from v2_discovery.fast_sim.validation import validate_positive_numeric
from v2_discovery.fast_sim.validation import validate_required_columns


PRICE_COLUMNS = ("date", "symbol", "close")
WEIGHT_COLUMNS = ("date", "symbol", "target_weight")


@dataclass(frozen=True)
class SyntheticLedgerOutput:
    positions: pd.DataFrame
    ledger: pd.DataFrame


def build_synthetic_ledger(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_model: FastProxyCostModel,
) -> SyntheticLedgerOutput:
    _validate_pre_ledger_inputs(prices, weights, cost_model)
    _validate_weight_limits(weights, cost_model.max_gross_exposure)
    price_matrix = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    weight_matrix = (
        weights.pivot(index="date", columns="symbol", values="target_weight")
        .sort_index()
    )
    symbols = sorted(weight_matrix.columns)
    price_matrix = price_matrix.reindex(index=weight_matrix.index, columns=symbols)
    if weight_matrix.isna().any().any():
        raise ProxyBoundaryError("Synthetic target weights missing required date/symbol rows")
    if price_matrix.isna().any().any():
        raise ProxyBoundaryError("Synthetic prices missing required target-weight rows")

    quantities = pd.Series(0.0, index=symbols, dtype="float64")
    cash = float(cost_model.initial_cash)
    position_rows: list[dict[str, object]] = []
    ledger_rows: list[dict[str, object]] = []

    for date in weight_matrix.index:
        prices_today = price_matrix.loc[date].astype("float64")
        targets = weight_matrix.loc[date].astype("float64")
        current_values = quantities * prices_today
        equity_before_cost = float(cash + current_values.sum())
        if equity_before_cost <= 0:
            raise ProxyBoundaryError("Synthetic proxy equity must stay positive")

        current_weights = current_values / equity_before_cost
        turnover = float((targets - current_weights).abs().sum())
        transaction_cost = cost_model.transaction_cost(
            equity=equity_before_cost,
            turnover=turnover,
        )
        equity_after_cost = equity_before_cost - transaction_cost
        if equity_after_cost <= 0:
            raise ProxyBoundaryError("Synthetic proxy costs exhausted equity")

        target_values = targets * equity_after_cost
        quantities = target_values / prices_today
        cash = float(equity_after_cost - target_values.sum())
        if abs(cash) < 0.0000005:
            cash = 0.0

        gross_exposure = float(target_values.abs().sum() / equity_after_cost)
        net_exposure = float(target_values.sum() / equity_after_cost)
        ledger_rows.append(
            {
                "date": date,
                "cash": _round(cash),
                "turnover": _round(turnover),
                "transaction_cost": _round(transaction_cost),
                "gross_exposure": _round(gross_exposure),
                "net_exposure": _round(net_exposure),
            }
        )
        for symbol in symbols:
            position_rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "quantity": _round(float(quantities[symbol])),
                    "market_value": _round(float(target_values[symbol])),
                }
            )

    positions = pd.DataFrame(
        position_rows,
        columns=["date", "symbol", "quantity", "market_value"],
    )
    ledger = pd.DataFrame(
        ledger_rows,
        columns=[
            "date",
            "cash",
            "turnover",
            "transaction_cost",
            "gross_exposure",
            "net_exposure",
        ],
    )
    validate_synthetic_ledger_output(positions, ledger)
    return SyntheticLedgerOutput(positions=positions, ledger=ledger)


def validate_synthetic_ledger_output(positions: pd.DataFrame, ledger: pd.DataFrame) -> None:
    validate_required_columns(
        positions,
        ("date", "symbol", "quantity", "market_value"),
        "synthetic output positions",
    )
    validate_no_nulls(positions, ("date", "symbol", "quantity", "market_value"), "synthetic output positions")
    validate_finite_numeric(
        positions,
        ("quantity", "market_value"),
        "synthetic output positions",
    )
    validate_required_columns(
        ledger,
        ("date", "cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"),
        "synthetic output ledger",
    )
    validate_no_nulls(
        ledger,
        ("date", "cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"),
        "synthetic output ledger",
    )
    validate_finite_numeric(
        ledger,
        ("cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"),
        "synthetic output ledger",
    )


def _validate_pre_ledger_inputs(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_model: FastProxyCostModel,
) -> None:
    validate_required_columns(prices, PRICE_COLUMNS, "synthetic pre-ledger prices")
    validate_no_nulls(prices, PRICE_COLUMNS, "synthetic pre-ledger prices")
    validate_positive_numeric(prices, ("close",), "synthetic pre-ledger prices")
    validate_required_columns(weights, WEIGHT_COLUMNS, "synthetic pre-ledger target weights")
    validate_no_nulls(weights, WEIGHT_COLUMNS, "synthetic pre-ledger target weights")
    validate_finite_numeric(
        weights,
        ("target_weight",),
        "synthetic pre-ledger target weights",
    )
    cost_df = pd.DataFrame(
        {
            "initial_cash": [cost_model.initial_cash],
            "total_cost_bps": [cost_model.total_cost_bps],
            "max_gross_exposure": [cost_model.max_gross_exposure],
        }
    )
    validate_positive_numeric(
        cost_df,
        ("initial_cash", "max_gross_exposure"),
        "synthetic pre-ledger cost assumptions",
    )
    validate_finite_numeric(
        cost_df,
        ("total_cost_bps",),
        "synthetic pre-ledger cost assumptions",
    )
    if cost_model.total_cost_bps < 0:
        raise ProxyBoundaryError("Synthetic cost assumptions require non-negative total_cost_bps")


def _validate_weight_limits(weights: pd.DataFrame, max_gross_exposure: float) -> None:
    gross = weights.groupby("date", sort=True)["target_weight"].apply(lambda item: item.abs().sum())
    if (gross > max_gross_exposure + 1e-12).any():
        raise ProxyBoundaryError("Synthetic target weights exceed max_gross_exposure")


def _round(value: float) -> float:
    return round(float(value), 6)
