from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from strategies.optimizer import OptimizationMethod, PortfolioOptimizer
from strategies.optimizer_diagnostics import (
    OptimizerBoundDiagnostics,
    OptimizerConstraintDiagnostics,
    OptimizerDiagnosticSeverity,
    OptimizerFeasibilityReport,
    OptimizerSolverDiagnostics,
    build_solver_diagnostics,
    check_optimizer_feasibility,
    diagnose_bound_activity,
    diagnose_constraint_residuals,
)
from views.optimizer_view import OptimizerControls, _run_optimizer


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DOC = ROOT / "docs" / "architecture" / "optimizer_core_policy_audit.md"
CONSTRAINTS_DOC = ROOT / "docs" / "architecture" / "optimizer_constraints_policy.md"
SLSQP_DOC = ROOT / "docs" / "architecture" / "optimizer_lower_bound_slsqp_policy.md"
QUARANTINE_PATCH = (
    ROOT / "docs" / "quarantine" / "optimizer_core_lower_bounds_slsqp_diff_20260510.patch"
)


def _prices(columns: list[str] | None = None) -> pd.DataFrame:
    cols = columns or ["A", "B", "C", "D"]
    base = np.linspace(100.0, 120.0, 8)
    return pd.DataFrame(
        {col: base * (1.0 + idx * 0.01) for idx, col in enumerate(cols)},
        index=pd.date_range("2026-01-01", periods=8, freq="D"),
    )


def _doc_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8") for path in (AUDIT_DOC, CONSTRAINTS_DOC, SLSQP_DOC)
    )


def test_optimizer_rejects_infeasible_lower_bounds() -> None:
    report = check_optimizer_feasibility(
        n_assets=2,
        max_weight=0.8,
        min_weight=0.7,
    )

    assert isinstance(report, OptimizerFeasibilityReport)
    assert report.is_feasible is False
    assert report.severity == OptimizerDiagnosticSeverity.ERROR
    assert "min_weight=70.0% across 2 assets requires 140.0% allocation" in " ".join(report.messages)


def test_optimizer_rejects_infeasible_upper_bounds() -> None:
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_mean_variance_with_diagnostics(
        _prices(["A", "B", "C"]),
        max_weight=0.2,
    )

    assert result.weights.empty
    assert result.diagnostics.feasibility_report.is_feasible is False
    assert result.diagnostics.fallback_used is False
    assert result.diagnostics.result_is_optimized is False
    assert "max_weight=20.0% across 3 assets only allows 60.0%" in " ".join(result.diagnostics.messages)


def test_optimizer_detects_min_weight_sum_exceeds_one() -> None:
    report = check_optimizer_feasibility(
        n_assets=2,
        max_weight=0.8,
        required_min_weights=[0.6, 0.6],
    )

    assert report.is_feasible is False
    assert "required minimum weights sum to 120.0%" in " ".join(report.messages)


def test_optimizer_detects_max_weight_sum_below_one() -> None:
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_inverse_volatility_with_diagnostics(
        _prices(["A", "B", "C"]),
        max_weight=0.2,
    )

    assert result.weights.empty
    assert result.diagnostics.feasibility_report.is_feasible is False
    assert result.diagnostics.solver_status == "not_started"
    assert result.diagnostics.fallback_used is False


def test_optimizer_reports_active_lower_bound() -> None:
    diagnostics = diagnose_bound_activity(
        pd.Series({"A": 0.0, "B": 0.4, "C": 0.6}),
        lower_bound=0.0,
        upper_bound=0.6,
    )

    assert isinstance(diagnostics, OptimizerBoundDiagnostics)
    assert diagnostics.lower_bound_count == 1
    assert diagnostics.assets_at_lower_bound == ("A",)


def test_optimizer_reports_active_upper_bound() -> None:
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_mean_variance_with_diagnostics(
        _prices(["A", "B", "C", "D", "E"]),
        max_weight=0.2,
    )

    assert result.diagnostics.feasibility_report.is_equal_weight_forced is True
    assert result.diagnostics.bound_diagnostics.upper_bound_count == 5
    assert result.diagnostics.bound_diagnostics.assets_at_upper_bound


def test_optimizer_does_not_silently_fallback_to_equal_weight(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*args, **kwargs):
        raise RuntimeError("forced slsqp failure")

    monkeypatch.setattr("strategies.optimizer.minimize", _fail)
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_mean_variance_with_diagnostics(
        _prices(["A", "B", "C", "D", "E"]),
        max_weight=0.4,
    )

    assert result.weights.empty is False
    assert result.diagnostics.fallback_used is True
    assert result.diagnostics.result_is_optimized is False
    assert "Fallback allocation used: equal weight" in " ".join(result.diagnostics.messages)
    assert "This is not an optimized result" in " ".join(result.diagnostics.messages)


def test_optimizer_slsqp_failure_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*args, **kwargs):
        raise RuntimeError("forced slsqp failure")

    monkeypatch.setattr("strategies.optimizer.minimize", _fail)
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_mean_variance_with_diagnostics(
        _prices(["A", "B", "C", "D", "E"]),
        max_weight=0.4,
    )

    assert isinstance(result.diagnostics, OptimizerSolverDiagnostics)
    assert result.diagnostics.solver_success is False
    assert result.diagnostics.solver_status == "exception"
    assert "forced slsqp failure" in result.diagnostics.solver_message
    assert result.diagnostics.bounds_summary == "0.0 <= weight_i <= 0.400000"
    assert result.diagnostics.constraints_summary == "sum(weights) == 1.0"
    assert result.diagnostics.feasibility_report.is_feasible is True


def test_optimizer_policy_change_not_allowed_without_contract_update() -> None:
    text = _doc_text()
    optimizer_source = inspect.getsource(PortfolioOptimizer._run_slsqp)

    assert QUARANTINE_PATCH.exists()
    assert "lower-bound/SLSQP diff is not accepted" in text
    assert "MU hard floor" in text
    assert "WATCH investability" in text
    assert "Black-Litterman" in text
    assert "bounds = tuple((0.0, max_weight)" in optimizer_source


def test_optimizer_ui_shows_feasibility_failure() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "Optimization status: infeasible." in source
    assert "Feasibility status" in source


def test_optimizer_ui_shows_forced_equal_weight_warning() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "The optimizer has effectively no allocation freedom." in source
    assert "Equal weight forced" in source


def test_optimizer_ui_labels_fallback_allocation() -> None:
    source = Path("views/optimizer_view.py").read_text(encoding="utf-8")

    assert "Fallback allocation used: equal weight." in source
    assert "This is not an optimized result." in source


def test_optimizer_diagnostics_objects_are_separate_from_ui_code() -> None:
    diagnostics_source = Path("strategies/optimizer_diagnostics.py").read_text(encoding="utf-8")

    assert "class OptimizerFeasibilityReport" in diagnostics_source
    assert "class OptimizerBoundDiagnostics" in diagnostics_source
    assert "class OptimizerConstraintDiagnostics" in diagnostics_source
    assert "class OptimizerSolverDiagnostics" in diagnostics_source
    assert "class OptimizerDiagnosticSeverity" in diagnostics_source
    assert "streamlit" not in diagnostics_source.lower()


def test_optimizer_reports_constraint_residuals() -> None:
    optimizer = PortfolioOptimizer()
    result = optimizer.optimize_inverse_volatility_with_diagnostics(
        _prices(["A", "B", "C", "D", "E"]),
        max_weight=0.4,
    )

    assert isinstance(result.diagnostics.constraint_diagnostics, OptimizerConstraintDiagnostics)
    assert abs(result.diagnostics.constraint_diagnostics.cash_residual) <= 1e-6
    assert result.diagnostics.constraint_diagnostics.constraints_satisfied is True


def test_optimizer_diagnostics_fail_closed_on_non_finite_weights() -> None:
    feasibility = check_optimizer_feasibility(n_assets=3, max_weight=0.5)

    report = build_solver_diagnostics(
        solver_success=True,
        solver_status=0,
        solver_message="synthetic success with bad weights",
        objective_name="diagnostic_probe",
        n_assets=3,
        max_weight=0.5,
        weights=pd.Series({"A": 0.5, "B": 0.5, "C": np.nan}),
        feasibility_report=feasibility,
        result_is_optimized=True,
    )

    assert isinstance(report, OptimizerSolverDiagnostics)
    assert report.severity == OptimizerDiagnosticSeverity.ERROR
    assert report.result_is_optimized is False
    assert report.constraint_diagnostics.constraints_satisfied is False
    assert "non-finite" in " ".join(report.messages)


def test_optimizer_constraint_diagnostics_reject_inf_weights() -> None:
    diagnostics = diagnose_constraint_residuals([0.5, 0.5, np.inf])

    assert diagnostics.severity == OptimizerDiagnosticSeverity.ERROR
    assert diagnostics.constraints_satisfied is False
    assert "non-finite" in " ".join(diagnostics.messages)


def test_optimizer_view_controls_pipe_bounds_to_real_slsqp_and_sector_cap() -> None:
    if not PortfolioOptimizer.has_slsqp():
        pytest.skip("SciPy SLSQP is unavailable")

    controls = OptimizerControls(
        method=OptimizationMethod.MEAN_VARIANCE_MAX_RETURN,
        max_weight=0.34,
        portfolio_value=10_000.0,
        enable_sector_cap=True,
        max_sector_weight=0.50,
        risk_free_rate=0.01,
    )
    prices = _prices(["A", "B", "C", "D"])
    optimizer = PortfolioOptimizer()

    result = _run_optimizer(
        optimizer=optimizer,
        method=controls.method,
        prices_selected=prices,
        max_weight=controls.max_weight,
        risk_free_rate=controls.risk_free_rate,
    )

    assert result.diagnostics.solver_success is True
    assert result.weights.max() <= controls.max_weight + 1e-6
    assert abs(float(result.weights.sum()) - 1.0) <= 1e-6

    sector_map = {"A": "Tech", "B": "Tech", "C": "Health", "D": "Energy"}
    capped = optimizer.apply_sector_cap(
        weights=result.weights,
        sector_map=sector_map,
        max_sector_weight=controls.max_sector_weight,
    )
    sectors = pd.Series(sector_map)

    assert abs(float(capped.sum()) - 1.0) <= 1e-6
    assert capped.groupby(sectors).sum().max() <= controls.max_sector_weight + 1e-6
