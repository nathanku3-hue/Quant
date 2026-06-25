"""Structured diagnostics for portfolio optimizer runs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Mapping, Sequence

import numpy as np
import pandas as pd


class OptimizerDiagnosticSeverity(str, Enum):
    """Severity for optimizer diagnostic reports."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class OptimizerFeasibilityReport:
    """Pre-solver feasibility report for long-only fully invested bounds."""

    n_assets: int
    max_weight: float
    min_weight: float
    required_min_weights: tuple[float, ...]
    tolerance: float
    min_feasible_max_weight: float
    is_feasible: bool
    is_equal_weight_forced: bool
    messages: tuple[str, ...]
    severity: OptimizerDiagnosticSeverity

    @property
    def status(self) -> str:
        return "feasible" if self.is_feasible else "infeasible"

    def to_dict(self) -> dict[str, object]:
        return {
            "n_assets": self.n_assets,
            "max_weight": self.max_weight,
            "min_weight": self.min_weight,
            "required_min_weights": list(self.required_min_weights),
            "tolerance": self.tolerance,
            "min_feasible_max_weight": self.min_feasible_max_weight,
            "is_feasible": self.is_feasible,
            "is_equal_weight_forced": self.is_equal_weight_forced,
            "messages": list(self.messages),
            "severity": self.severity.value,
            "status": self.status,
        }


@dataclass(frozen=True)
class OptimizerBoundDiagnostics:
    """Post-solver bound activity diagnosed directly from final weights."""

    lower_bound: float
    upper_bound: float
    tolerance: float
    assets_at_lower_bound: tuple[str, ...]
    assets_at_upper_bound: tuple[str, ...]
    lower_bound_count: int
    upper_bound_count: int
    messages: tuple[str, ...]
    severity: OptimizerDiagnosticSeverity

    def to_dict(self) -> dict[str, object]:
        return {
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "tolerance": self.tolerance,
            "assets_at_lower_bound": list(self.assets_at_lower_bound),
            "assets_at_upper_bound": list(self.assets_at_upper_bound),
            "lower_bound_count": self.lower_bound_count,
            "upper_bound_count": self.upper_bound_count,
            "messages": list(self.messages),
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class OptimizerConstraintDiagnostics:
    """Post-solver equality constraint diagnostics."""

    cash_residual: float
    full_investment_residual: float
    constraint_residuals: Mapping[str, float]
    constraints_satisfied: bool
    messages: tuple[str, ...]
    severity: OptimizerDiagnosticSeverity

    def to_dict(self) -> dict[str, object]:
        return {
            "cash_residual": self.cash_residual,
            "full_investment_residual": self.full_investment_residual,
            "constraint_residuals": dict(self.constraint_residuals),
            "constraints_satisfied": self.constraints_satisfied,
            "messages": list(self.messages),
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class OptimizerSolverDiagnostics:
    """Full diagnostic envelope for one optimizer attempt."""

    solver_success: bool
    solver_status: int | str | None
    solver_message: str
    objective_name: str
    n_assets: int
    bounds_summary: str
    constraints_summary: str
    feasibility_report: OptimizerFeasibilityReport
    bound_diagnostics: OptimizerBoundDiagnostics
    constraint_diagnostics: OptimizerConstraintDiagnostics
    fallback_used: bool
    fallback_reason: str
    result_is_optimized: bool
    messages: tuple[str, ...]
    severity: OptimizerDiagnosticSeverity

    @property
    def active_constraints(self) -> tuple[str, ...]:
        active: list[str] = []
        if self.bound_diagnostics.lower_bound_count:
            active.append("lower_bound")
        if self.bound_diagnostics.upper_bound_count:
            active.append("upper_bound")
        if self.constraint_diagnostics.constraints_satisfied:
            active.append("fully_invested")
        return tuple(active)

    def to_dict(self) -> dict[str, object]:
        return {
            "solver_success": self.solver_success,
            "solver_status": self.solver_status,
            "solver_message": self.solver_message,
            "objective_name": self.objective_name,
            "n_assets": self.n_assets,
            "bounds_summary": self.bounds_summary,
            "constraints_summary": self.constraints_summary,
            "feasibility_report": self.feasibility_report.to_dict(),
            "bound_diagnostics": self.bound_diagnostics.to_dict(),
            "constraint_diagnostics": self.constraint_diagnostics.to_dict(),
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
            "result_is_optimized": self.result_is_optimized,
            "active_constraints": list(self.active_constraints),
            "messages": list(self.messages),
            "severity": self.severity.value,
        }


@dataclass(frozen=True)
class OptimizerRunResult:
    """Optimizer weights plus the diagnostics needed to explain them safely."""

    weights: pd.Series
    diagnostics: OptimizerSolverDiagnostics


def _as_float(value: object, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return parsed


def _format_pct(value: float) -> str:
    return f"{float(value):.1%}"


def _severity(has_error: bool, has_warning: bool = False) -> OptimizerDiagnosticSeverity:
    if has_error:
        return OptimizerDiagnosticSeverity.ERROR
    if has_warning:
        return OptimizerDiagnosticSeverity.WARNING
    return OptimizerDiagnosticSeverity.INFO


def check_optimizer_feasibility(
    n_assets: int,
    max_weight: float,
    min_weight: float = 0.0,
    required_min_weights: Sequence[float] | None = None,
    tolerance: float = 1e-9,
) -> OptimizerFeasibilityReport:
    """Diagnose whether fully invested long-only bounds are feasible before SLSQP."""

    try:
        n = int(n_assets)
    except Exception:
        n = 0
    cap = _as_float(max_weight, default=0.0)
    floor = _as_float(min_weight, default=0.0)
    tol = abs(_as_float(tolerance, default=1e-9))
    required = tuple(_as_float(value, default=0.0) for value in (required_min_weights or ()))

    errors: list[str] = []
    warnings: list[str] = []

    min_feasible = (1.0 / n) if n > 0 else math.nan

    if n <= 0:
        errors.append("Infeasible: n_assets=0 leaves no assets available for allocation.")

    for label, bound in (("min_weight", floor), ("max_weight", cap)):
        if bound < -tol or bound > 1.0 + tol:
            errors.append(f"Infeasible: {label}={_format_pct(bound)} is outside [0, 1].")

    for idx, bound in enumerate(required, start=1):
        if bound < -tol or bound > 1.0 + tol:
            errors.append(
                f"Infeasible: required_min_weights[{idx}]={_format_pct(bound)} is outside [0, 1]."
            )
        if bound > cap + tol:
            errors.append(
                f"Infeasible: required_min_weights[{idx}]={_format_pct(bound)} exceeds "
                f"max_weight={_format_pct(cap)}."
            )

    if floor > cap + tol:
        errors.append(
            f"Infeasible: min_weight={_format_pct(floor)} exceeds max_weight={_format_pct(cap)}."
        )

    if n > 0 and cap * n < 1.0 - tol:
        errors.append(
            "Infeasible: "
            f"max_weight={_format_pct(cap)} across {n} assets only allows "
            f"{_format_pct(cap * n)} total allocation."
        )

    if n > 0 and floor * n > 1.0 + tol:
        errors.append(
            "Infeasible: "
            f"min_weight={_format_pct(floor)} across {n} assets requires "
            f"{_format_pct(floor * n)} allocation."
        )

    required_sum = float(sum(required))
    if required and required_sum > 1.0 + tol:
        errors.append(
            "Infeasible: "
            f"required minimum weights sum to {_format_pct(required_sum)}, above 100.0%."
        )

    if errors:
        errors.append("Infeasible: fully invested constraint cannot be satisfied with these bounds.")

    equal_weight_forced = bool(n > 0 and not errors and cap <= min_feasible + tol)
    if equal_weight_forced:
        warnings.append(
            "The optimizer has effectively no allocation freedom. "
            "The max-weight cap is at the minimum feasible boundary, so the result is forced toward equal weight."
        )

    messages = tuple(errors + warnings) or ("Feasible: optimizer bounds can satisfy full investment.",)
    return OptimizerFeasibilityReport(
        n_assets=n,
        max_weight=cap,
        min_weight=floor,
        required_min_weights=required,
        tolerance=tol,
        min_feasible_max_weight=min_feasible,
        is_feasible=not errors,
        is_equal_weight_forced=equal_weight_forced,
        messages=messages,
        severity=_severity(has_error=bool(errors), has_warning=bool(warnings)),
    )


def diagnose_bound_activity(
    weights: pd.Series | np.ndarray | Sequence[float],
    lower_bound: float = 0.0,
    upper_bound: float = 1.0,
    tolerance: float = 1e-6,
) -> OptimizerBoundDiagnostics:
    """Detect active bounds directly from final weights."""

    tol = abs(_as_float(tolerance, default=1e-6))
    lower = _as_float(lower_bound, default=0.0)
    upper = _as_float(upper_bound, default=1.0)

    if isinstance(weights, pd.Series):
        series = pd.to_numeric(weights, errors="coerce").replace([np.inf, -np.inf], np.nan)
        labels = [str(label) for label in series.index]
    else:
        values = np.asarray(weights, dtype=float).reshape(-1)
        series = pd.Series(values, index=[str(i) for i in range(len(values))], dtype=float)
        labels = [str(label) for label in series.index]

    if series.empty:
        return OptimizerBoundDiagnostics(
            lower_bound=lower,
            upper_bound=upper,
            tolerance=tol,
            assets_at_lower_bound=tuple(),
            assets_at_upper_bound=tuple(),
            lower_bound_count=0,
            upper_bound_count=0,
            messages=("No weights available for bound diagnostics.",),
            severity=OptimizerDiagnosticSeverity.WARNING,
        )

    non_finite_labels = tuple(
        label for label, value in zip(labels, series.to_numpy()) if not np.isfinite(value)
    )
    finite = series.dropna()
    lower_labels = tuple(label for label, value in zip(labels, series.to_numpy()) if np.isfinite(value) and value <= lower + tol)
    upper_labels = tuple(label for label, value in zip(labels, series.to_numpy()) if np.isfinite(value) and value >= upper - tol)

    messages: list[str] = []
    if non_finite_labels:
        messages.append(f"{len(non_finite_labels)} asset weights are non-finite.")
    if lower_labels:
        messages.append(f"{len(lower_labels)} assets are active at the lower bound.")
    if upper_labels:
        messages.append(f"{len(upper_labels)} assets are active at the max-weight cap.")
    if not messages and not finite.empty:
        messages.append("No asset weights are active at configured bounds.")

    return OptimizerBoundDiagnostics(
        lower_bound=lower,
        upper_bound=upper,
        tolerance=tol,
        assets_at_lower_bound=lower_labels,
        assets_at_upper_bound=upper_labels,
        lower_bound_count=len(lower_labels),
        upper_bound_count=len(upper_labels),
        messages=tuple(messages),
        severity=_severity(bool(non_finite_labels), bool(lower_labels or upper_labels)),
    )


def diagnose_constraint_residuals(
    weights: pd.Series | np.ndarray | Sequence[float],
    tolerance: float = 1e-6,
) -> OptimizerConstraintDiagnostics:
    """Diagnose full-investment residuals after an optimizer run."""

    tol = abs(_as_float(tolerance, default=1e-6))
    if isinstance(weights, pd.Series):
        raw_values = pd.to_numeric(weights, errors="coerce").replace([np.inf, -np.inf], np.nan)
        has_non_finite = bool(raw_values.isna().any())
        values = raw_values.fillna(0.0)
        total = float(values.sum())
    else:
        raw_array = np.asarray(weights, dtype=float).reshape(-1)
        has_non_finite = bool(np.any(~np.isfinite(raw_array)))
        array = np.where(np.isfinite(raw_array), raw_array, 0.0)
        total = float(array.sum())

    cash_residual = 1.0 - total
    signed_full_investment_residual = total - 1.0
    abs_residual = abs(signed_full_investment_residual)
    satisfied = (abs_residual <= tol) and not has_non_finite
    if has_non_finite:
        messages = "Fully invested constraint is unsatisfied because one or more weights are non-finite."
    elif satisfied:
        messages = "Fully invested constraint is satisfied."
    else:
        messages = f"Fully invested constraint residual is {signed_full_investment_residual:.6f}."
    return OptimizerConstraintDiagnostics(
        cash_residual=cash_residual,
        full_investment_residual=abs_residual,
        constraint_residuals={"fully_invested": signed_full_investment_residual},
        constraints_satisfied=satisfied,
        messages=(messages,),
        severity=_severity(has_error=not satisfied),
    )


def build_solver_diagnostics(
    *,
    solver_success: bool,
    solver_status: int | str | None,
    solver_message: str,
    objective_name: str,
    n_assets: int,
    max_weight: float,
    weights: pd.Series | np.ndarray | Sequence[float],
    feasibility_report: OptimizerFeasibilityReport,
    fallback_used: bool = False,
    fallback_reason: str = "",
    result_is_optimized: bool = False,
    tolerance: float = 1e-6,
) -> OptimizerSolverDiagnostics:
    """Build a complete diagnostics object for an optimizer result."""

    bound_diagnostics = diagnose_bound_activity(
        weights=weights,
        lower_bound=0.0,
        upper_bound=max_weight,
        tolerance=tolerance,
    )
    constraint_diagnostics = diagnose_constraint_residuals(weights=weights, tolerance=tolerance)

    messages: list[str] = list(feasibility_report.messages)
    if solver_message:
        messages.append(str(solver_message))
    messages.extend(bound_diagnostics.messages)
    messages.extend(constraint_diagnostics.messages)
    if fallback_used:
        reason = fallback_reason or solver_message or "optimizer did not produce usable weights"
        messages.append(f"Fallback allocation used: equal weight. Reason: {reason}.")
        messages.append("This is not an optimized result.")

    has_error = (
        not feasibility_report.is_feasible
        or bound_diagnostics.severity == OptimizerDiagnosticSeverity.ERROR
        or (not solver_success and not fallback_used)
        or not constraint_diagnostics.constraints_satisfied
    )
    has_warning = (
        fallback_used
        or feasibility_report.severity == OptimizerDiagnosticSeverity.WARNING
        or bound_diagnostics.severity == OptimizerDiagnosticSeverity.WARNING
    )

    return OptimizerSolverDiagnostics(
        solver_success=bool(solver_success),
        solver_status=solver_status,
        solver_message=str(solver_message or ""),
        objective_name=str(objective_name or "unknown"),
        n_assets=int(n_assets),
        bounds_summary=f"0.0 <= weight_i <= {float(max_weight):.6f}",
        constraints_summary="sum(weights) == 1.0",
        feasibility_report=feasibility_report,
        bound_diagnostics=bound_diagnostics,
        constraint_diagnostics=constraint_diagnostics,
        fallback_used=bool(fallback_used),
        fallback_reason=str(fallback_reason or ""),
        result_is_optimized=bool(result_is_optimized and solver_success and not fallback_used and not has_error),
        messages=tuple(messages),
        severity=_severity(has_error=has_error, has_warning=has_warning),
    )
