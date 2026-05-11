"""Phase 6 portfolio optimizer utilities."""

from __future__ import annotations

from enum import StrEnum

import numpy as np
import pandas as pd

from strategies.optimizer_diagnostics import (
    OptimizerFeasibilityReport,
    OptimizerRunResult,
    OptimizerSolverDiagnostics,
    build_solver_diagnostics,
    check_optimizer_feasibility,
)

try:
    from scipy.optimize import minimize
except Exception:  # pragma: no cover - optional dependency guard
    minimize = None


class OptimizationMethod(StrEnum):
    """Supported portfolio optimizer methods exposed to UI callers."""

    HISTORICAL_BEST_CAGR = "Historical Best CAGR Strategy"
    HISTORICAL_MAX_SHARPE = "Historical Max Sharpe Strategy"
    INVERSE_VOLATILITY = "Inverse Volatility"
    THESIS_NEUTRAL_MAX_SHARPE = "Thesis-Neutral Max Sharpe"
    MEAN_VARIANCE_MIN_VOLATILITY = "Mean-Variance (Min Volatility)"
    MEAN_VARIANCE_MAX_RETURN = "Mean-Variance (Max Return)"

    @property
    def is_mean_variance(self) -> bool:
        return self in MEAN_VARIANCE_METHODS


OPTIMIZATION_METHOD_OPTIONS = (
    OptimizationMethod.HISTORICAL_BEST_CAGR,
    OptimizationMethod.HISTORICAL_MAX_SHARPE,
    OptimizationMethod.INVERSE_VOLATILITY,
    OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE,
    OptimizationMethod.MEAN_VARIANCE_MIN_VOLATILITY,
    OptimizationMethod.MEAN_VARIANCE_MAX_RETURN,
)
DEFAULT_OPTIMIZATION_METHOD = OptimizationMethod.INVERSE_VOLATILITY
MEAN_VARIANCE_METHODS = (
    OptimizationMethod.THESIS_NEUTRAL_MAX_SHARPE,
    OptimizationMethod.MEAN_VARIANCE_MIN_VOLATILITY,
    OptimizationMethod.MEAN_VARIANCE_MAX_RETURN,
)


class PortfolioOptimizer:
    """Compute portfolio weights with bounded long-only constraints."""

    def __init__(self, annualization_factor: int = 252):
        self.annualization_factor = int(annualization_factor)

    @staticmethod
    def has_slsqp() -> bool:
        return minimize is not None

    @staticmethod
    def _as_prices(prices_df: pd.DataFrame) -> pd.DataFrame:
        """Return a numeric price matrix with invalid values coerced to NaN."""
        if not isinstance(prices_df, pd.DataFrame) or prices_df.empty:
            return pd.DataFrame()

        prices = prices_df.copy()
        prices = prices.apply(pd.to_numeric, errors="coerce")
        prices = prices.replace([np.inf, -np.inf], np.nan)
        prices = prices.sort_index()
        return prices.dropna(axis=1, how="all")

    def _prepare_returns(self, prices_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Build daily returns and keep only columns with enough usable observations."""
        prices = self._as_prices(prices_df)
        if prices.empty:
            return prices, pd.DataFrame()

        returns = prices.pct_change(fill_method=None)
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna(how="all")
        if returns.empty:
            return prices.iloc[:, 0:0], pd.DataFrame()

        valid_cols = returns.columns[returns.notna().sum() >= 2]
        if len(valid_cols) == 0:
            return prices.iloc[:, 0:0], pd.DataFrame()

        prices = prices.loc[:, valid_cols]
        returns = returns.loc[:, valid_cols]
        return prices, returns

    @staticmethod
    def _equal_weight(index: pd.Index) -> pd.Series:
        """Return equal-weight series for the provided index."""
        if len(index) == 0:
            return pd.Series(dtype=float)
        return pd.Series(1.0 / len(index), index=index, dtype=float)

    @staticmethod
    def _is_feasible(n_assets: int, max_weight: float, tol: float = 1e-9) -> bool:
        """Check if bounded long-only fully-invested constraints are feasible."""
        return n_assets > 0 and max_weight > 0 and (max_weight * n_assets) >= (1.0 - tol)

    @staticmethod
    def _validate_solution(weights: np.ndarray, max_weight: float, tol: float = 1e-4) -> bool:
        """Validate solver output against long-only, fully-invested, bounded rules."""
        if weights.ndim != 1 or len(weights) == 0:
            return False
        if not np.all(np.isfinite(weights)):
            return False
        if np.any(weights < -tol):
            return False
        if np.any(weights > (max_weight + tol)):
            return False
        return abs(float(weights.sum()) - 1.0) <= tol

    @staticmethod
    def _expand_to_all_assets(
        all_assets: pd.Index,
        optimized_weights: pd.Series,
    ) -> pd.Series:
        """Expand optimized weights to the original asset set with zero for dropped assets."""
        if len(all_assets) == 0:
            return pd.Series(dtype=float)
        expanded = pd.Series(0.0, index=all_assets, dtype=float)
        if not optimized_weights.empty:
            expanded.loc[optimized_weights.index] = optimized_weights.astype(float).values
        total = float(expanded.sum())
        if total > 0:
            expanded = expanded / total
        return expanded

    def _safe_equal_fallback(
        self,
        all_assets: pd.Index,
        investable_assets: pd.Index | None = None,
    ) -> pd.Series:
        """Fallback to equal weights, preferring only investable assets when available."""
        if investable_assets is None or len(investable_assets) == 0:
            return self._equal_weight(all_assets)
        eq = self._equal_weight(investable_assets)
        return self._expand_to_all_assets(all_assets, eq)

    @staticmethod
    def _attach_diagnostics(
        weights: pd.Series,
        diagnostics: OptimizerSolverDiagnostics,
    ) -> pd.Series:
        """Attach structured diagnostics without changing the public Series API."""
        result = weights.copy()
        result.attrs["optimizer_diagnostics"] = diagnostics.to_dict()
        result.attrs["optimizer_diagnostics_object"] = diagnostics
        return result

    def _diagnostic_result(
        self,
        weights: pd.Series,
        diagnostics: OptimizerSolverDiagnostics,
    ) -> OptimizerRunResult:
        return OptimizerRunResult(
            weights=self._attach_diagnostics(weights, diagnostics),
            diagnostics=diagnostics,
        )

    def _build_empty_diagnostic_result(
        self,
        *,
        objective_name: str,
        n_assets: int,
        max_weight: float,
        feasibility_report: OptimizerFeasibilityReport,
        solver_status: int | str | None,
        solver_message: str,
    ) -> OptimizerRunResult:
        weights = pd.Series(dtype=float)
        diagnostics = build_solver_diagnostics(
            solver_success=False,
            solver_status=solver_status,
            solver_message=solver_message,
            objective_name=objective_name,
            n_assets=n_assets,
            max_weight=max_weight,
            weights=weights,
            feasibility_report=feasibility_report,
            fallback_used=False,
            result_is_optimized=False,
        )
        return self._diagnostic_result(weights, diagnostics)

    def _build_fallback_diagnostic_result(
        self,
        *,
        all_assets: pd.Index,
        investable_assets: pd.Index,
        objective_name: str,
        n_assets: int,
        max_weight: float,
        feasibility_report: OptimizerFeasibilityReport,
        solver_status: int | str | None,
        solver_message: str,
        fallback_reason: str,
    ) -> OptimizerRunResult:
        weights = self._safe_equal_fallback(all_assets, investable_assets)
        diagnostics = build_solver_diagnostics(
            solver_success=False,
            solver_status=solver_status,
            solver_message=solver_message,
            objective_name=objective_name,
            n_assets=n_assets,
            max_weight=max_weight,
            weights=weights.reindex(investable_assets).fillna(0.0),
            feasibility_report=feasibility_report,
            fallback_used=True,
            fallback_reason=fallback_reason,
            result_is_optimized=False,
        )
        return self._diagnostic_result(weights, diagnostics)

    @staticmethod
    def _lookup_sector(asset, sector_map: dict | None, default: str = "Unknown") -> str:
        if not isinstance(sector_map, dict):
            return default
        if asset in sector_map and pd.notna(sector_map.get(asset)):
            return str(sector_map.get(asset))
        key = str(asset)
        if key in sector_map and pd.notna(sector_map.get(key)):
            return str(sector_map.get(key))
        try:
            key_int = int(asset)
            if key_int in sector_map and pd.notna(sector_map.get(key_int)):
                return str(sector_map.get(key_int))
            key_int_s = str(key_int)
            if key_int_s in sector_map and pd.notna(sector_map.get(key_int_s)):
                return str(sector_map.get(key_int_s))
        except Exception:
            pass
        return default

    def apply_sector_cap(
        self,
        weights: pd.Series,
        sector_map: dict | None,
        max_sector_weight: float = 0.30,
        max_iter: int = 12,
    ) -> pd.Series:
        """
        Soft sector constraint:
          1) identify violating sectors
          2) scale violating sector weights down to cap
          3) redistribute excess to non-violating sectors proportionally
        """
        if not isinstance(weights, pd.Series) or weights.empty:
            return pd.Series(dtype=float)

        try:
            cap = float(max_sector_weight)
        except Exception:
            cap = 0.30
        cap = max(0.01, min(1.0, cap))

        w = pd.to_numeric(weights, errors="coerce").fillna(0.0).clip(lower=0.0)
        if float(w.sum()) <= 0:
            return w
        w = w / float(w.sum())

        sectors = pd.Series(
            [self._lookup_sector(a, sector_map, default="Unknown") for a in w.index],
            index=w.index,
            dtype="object",
        )

        for _ in range(max_iter):
            sector_sum = w.groupby(sectors).sum().sort_values(ascending=False)
            violating = sector_sum[sector_sum > (cap + 1e-9)]
            if violating.empty:
                break

            excess_total = 0.0
            violating_set = set(violating.index.tolist())
            for sec, sec_weight in violating.items():
                idx = sectors[sectors == sec].index
                if len(idx) == 0:
                    continue
                current = float(w.loc[idx].sum())
                if current <= 0:
                    continue
                scale = cap / current
                w.loc[idx] = w.loc[idx] * scale
                excess_total += max(0.0, current - float(w.loc[idx].sum()))

            if excess_total <= 0:
                break

            eligible = sectors[~sectors.isin(violating_set)].index
            if len(eligible) == 0:
                # No place to reallocate excess; normalize and exit.
                total_now = float(w.sum())
                if total_now > 0:
                    w = w / total_now
                break

            eligible_sum = float(w.loc[eligible].sum())
            if eligible_sum <= 0:
                w.loc[eligible] = w.loc[eligible] + (excess_total / len(eligible))
            else:
                w.loc[eligible] = w.loc[eligible] + (w.loc[eligible] / eligible_sum) * excess_total

            total_now = float(w.sum())
            if total_now > 0:
                w = w / total_now

        # Final clamp/normalize for numerical safety.
        w = w.clip(lower=0.0)
        total = float(w.sum())
        if total > 0:
            w = w / total
        return w

    def _run_slsqp(
        self,
        objective_fn,
        n_assets: int,
        max_weight: float,
        x0: np.ndarray | None = None,
    ) -> np.ndarray | None:
        """Solve bounded long-only allocation with full-investment constraint."""
        if minimize is None:
            return None
        if x0 is None:
            x0 = np.full(n_assets, 1.0 / max(1, n_assets), dtype=float)

        constraints = ({"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},)
        bounds = tuple((0.0, max_weight) for _ in range(n_assets))

        try:
            result = minimize(
                objective_fn,
                x0=x0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 500, "ftol": 1e-9},
            )
        except Exception:
            return None

        if not result.success or result.x is None:
            return None

        weights = np.asarray(result.x, dtype=float)
        if not self._validate_solution(weights, max_weight=max_weight):
            return None

        clipped = np.clip(weights, 0.0, max_weight)
        total = float(clipped.sum())
        if total <= 0:
            return None
        clipped = clipped / total
        if np.any(clipped > (max_weight + 1e-4)):
            return None
        return clipped

    def _run_slsqp_with_status(
        self,
        objective_fn,
        n_assets: int,
        max_weight: float,
        x0: np.ndarray | None = None,
    ) -> tuple[np.ndarray | None, bool, int | str | None, str]:
        """Solve with SLSQP and preserve status details for diagnostics."""
        if minimize is None:
            return None, False, "scipy_unavailable", "SciPy unavailable; SLSQP could not run."
        if x0 is None:
            x0 = np.full(n_assets, 1.0 / max(1, n_assets), dtype=float)

        constraints = ({"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},)
        bounds = tuple((0.0, max_weight) for _ in range(n_assets))

        try:
            result = minimize(
                objective_fn,
                x0=x0,
                method="SLSQP",
                bounds=bounds,
                constraints=constraints,
                options={"maxiter": 500, "ftol": 1e-9},
            )
        except Exception as exc:
            return None, False, "exception", f"SLSQP failed: {exc}"

        status = getattr(result, "status", None)
        message = str(getattr(result, "message", "") or "")

        if not bool(getattr(result, "success", False)) or getattr(result, "x", None) is None:
            return None, False, status, message or "SLSQP did not produce a successful solution."

        weights = np.asarray(result.x, dtype=float)
        if not self._validate_solution(weights, max_weight=max_weight):
            return None, False, status, message or "SLSQP returned an invalid bounded solution."

        clipped = np.clip(weights, 0.0, max_weight)
        total = float(clipped.sum())
        if total <= 0:
            return None, False, status, message or "SLSQP returned zero total allocation."
        clipped = clipped / total
        if np.any(clipped > (max_weight + 1e-4)):
            return None, False, status, message or "SLSQP clipped solution exceeded max-weight cap."
        return clipped, True, status, message or "SLSQP optimization succeeded."

    def calculate_covariance(self, prices_df: pd.DataFrame) -> pd.DataFrame:
        """Return annualized covariance matrix from price history with NaN-safe handling."""
        prices, returns = self._prepare_returns(prices_df)
        if returns.empty:
            return pd.DataFrame()

        cov = returns.cov(min_periods=2)
        cov = cov.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        cov = cov * float(self.annualization_factor)
        cov = (cov + cov.T) / 2.0

        diag = np.diag(cov.to_numpy(dtype=float))
        diag = np.clip(diag, a_min=0.0, a_max=None)
        np.fill_diagonal(cov.values, diag)
        return cov

    def optimize_inverse_volatility_with_diagnostics(
        self,
        prices_df: pd.DataFrame,
        max_weight: float = 0.2,
    ) -> OptimizerRunResult:
        """Optimize inverse-volatility weights and return structured diagnostics."""
        all_assets = pd.Index(prices_df.columns) if isinstance(prices_df, pd.DataFrame) else pd.Index([])

        try:
            max_weight = float(max_weight)
        except Exception:
            max_weight = 0.2

        feasibility = check_optimizer_feasibility(
            n_assets=len(all_assets),
            max_weight=max_weight,
        )
        if len(all_assets) == 0 or not feasibility.is_feasible:
            return self._build_empty_diagnostic_result(
                objective_name="inverse_volatility",
                n_assets=len(all_assets),
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Pre-solver feasibility failed.",
            )

        prices, returns = self._prepare_returns(prices_df)
        if returns.empty:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=all_assets,
                objective_name="inverse_volatility",
                n_assets=len(all_assets),
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Insufficient return history for inverse-volatility optimization.",
                fallback_reason="insufficient return history",
            )

        investable_assets = returns.columns
        n_assets = len(investable_assets)
        feasibility = check_optimizer_feasibility(
            n_assets=n_assets,
            max_weight=max_weight,
        )
        if not feasibility.is_feasible:
            return self._build_empty_diagnostic_result(
                objective_name="inverse_volatility",
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Pre-solver feasibility failed.",
            )

        if n_assets == 1:
            single = pd.Series([1.0], index=investable_assets, dtype=float)
            weights = self._expand_to_all_assets(all_assets, single)
            diagnostics = build_solver_diagnostics(
                solver_success=True,
                solver_status="deterministic_single_asset",
                solver_message="Single investable asset receives full allocation without SLSQP.",
                objective_name="inverse_volatility",
                n_assets=n_assets,
                max_weight=max_weight,
                weights=single,
                feasibility_report=feasibility,
                fallback_used=False,
                result_is_optimized=True,
            )
            return self._diagnostic_result(weights, diagnostics)

        volatility = returns.std(skipna=True) * np.sqrt(float(self.annualization_factor))
        volatility = volatility.replace([np.inf, -np.inf], np.nan)
        inv_vol = 1.0 / volatility.where(volatility > 0)
        inv_vol = inv_vol.replace([np.inf, -np.inf], np.nan).fillna(0.0)

        if float(inv_vol.sum()) <= 0:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=investable_assets,
                objective_name="inverse_volatility",
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Inverse-volatility target could not be formed from positive volatility.",
                fallback_reason="invalid inverse-volatility target",
            )

        target = (inv_vol / inv_vol.sum()).to_numpy(dtype=float)
        objective = lambda w: float(np.dot(w - target, w - target))
        x0 = np.full(n_assets, 1.0 / n_assets, dtype=float)

        solved, solver_success, solver_status, solver_message = self._run_slsqp_with_status(
            objective,
            n_assets=n_assets,
            max_weight=max_weight,
            x0=x0,
        )
        if solved is None:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=investable_assets,
                objective_name="inverse_volatility",
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status=solver_status,
                solver_message=solver_message,
                fallback_reason=solver_message or "SLSQP failed",
            )

        optimized = pd.Series(solved, index=investable_assets, dtype=float)
        weights = self._expand_to_all_assets(all_assets, optimized)
        diagnostics = build_solver_diagnostics(
            solver_success=solver_success,
            solver_status=solver_status,
            solver_message=solver_message,
            objective_name="inverse_volatility",
            n_assets=n_assets,
            max_weight=max_weight,
            weights=optimized,
            feasibility_report=feasibility,
            fallback_used=False,
            result_is_optimized=True,
        )
        return self._diagnostic_result(weights, diagnostics)

    def optimize_inverse_volatility(self, prices_df: pd.DataFrame, max_weight: float = 0.2) -> pd.Series:
        """Optimize weights from inverse annualized volatility with bounded constraints."""
        return self.optimize_inverse_volatility_with_diagnostics(
            prices_df=prices_df,
            max_weight=max_weight,
        ).weights

    def optimize_mean_variance_with_diagnostics(
        self,
        prices_df: pd.DataFrame,
        objective: str = "max_sharpe",
        max_weight: float = 0.2,
        risk_free_rate: float = 0.0,
    ) -> OptimizerRunResult:
        """Optimize mean-variance weights and return structured diagnostics."""
        all_assets = pd.Index(prices_df.columns) if isinstance(prices_df, pd.DataFrame) else pd.Index([])

        try:
            max_weight = float(max_weight)
        except Exception:
            max_weight = 0.2
        objective = (objective or "max_sharpe").strip().lower()

        feasibility = check_optimizer_feasibility(
            n_assets=len(all_assets),
            max_weight=max_weight,
        )
        if len(all_assets) == 0 or not feasibility.is_feasible:
            return self._build_empty_diagnostic_result(
                objective_name=objective,
                n_assets=len(all_assets),
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Pre-solver feasibility failed.",
            )

        try:
            risk_free_rate = float(risk_free_rate)
        except Exception:
            risk_free_rate = 0.0

        prices, returns = self._prepare_returns(prices_df)
        if returns.empty:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=all_assets,
                objective_name=objective,
                n_assets=len(all_assets),
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Insufficient return history for mean-variance optimization.",
                fallback_reason="insufficient return history",
            )

        investable_assets = returns.columns
        n_assets = len(investable_assets)
        feasibility = check_optimizer_feasibility(
            n_assets=n_assets,
            max_weight=max_weight,
        )
        if not feasibility.is_feasible:
            return self._build_empty_diagnostic_result(
                objective_name=objective,
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Pre-solver feasibility failed.",
            )

        if n_assets == 1:
            single = pd.Series([1.0], index=investable_assets, dtype=float)
            weights = self._expand_to_all_assets(all_assets, single)
            diagnostics = build_solver_diagnostics(
                solver_success=True,
                solver_status="deterministic_single_asset",
                solver_message="Single investable asset receives full allocation without SLSQP.",
                objective_name=objective,
                n_assets=n_assets,
                max_weight=max_weight,
                weights=single,
                feasibility_report=feasibility,
                fallback_used=False,
                result_is_optimized=True,
            )
            return self._diagnostic_result(weights, diagnostics)

        exp_returns = (returns.mean(skipna=True) * float(self.annualization_factor)).reindex(investable_assets)
        exp_returns = exp_returns.fillna(0.0)

        cov = self.calculate_covariance(prices.loc[:, investable_assets])
        if cov.empty:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=investable_assets,
                objective_name=objective,
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status="not_started",
                solver_message="Covariance matrix could not be formed.",
                fallback_reason="missing covariance matrix",
            )
        cov = cov.reindex(index=investable_assets, columns=investable_assets).fillna(0.0)

        cov_matrix = cov.to_numpy(dtype=float)
        cov_matrix = (cov_matrix + cov_matrix.T) / 2.0
        cov_matrix = cov_matrix + np.eye(n_assets) * 1e-8

        mu = exp_returns.to_numpy(dtype=float)

        def port_return(w: np.ndarray) -> float:
            return float(np.dot(w, mu))

        def port_vol(w: np.ndarray) -> float:
            variance = float(np.dot(w, np.dot(cov_matrix, w)))
            return float(np.sqrt(max(variance, 1e-12)))

        if objective == "min_volatility":
            objective_fn = lambda w: port_vol(w)
        elif objective == "max_return":
            objective_fn = lambda w: -port_return(w)
        else:
            objective_fn = lambda w: -((port_return(w) - risk_free_rate) / (port_vol(w) + 1e-12))

        x0 = np.full(n_assets, 1.0 / n_assets, dtype=float)
        solved, solver_success, solver_status, solver_message = self._run_slsqp_with_status(
            objective_fn,
            n_assets=n_assets,
            max_weight=max_weight,
            x0=x0,
        )
        if solved is None:
            return self._build_fallback_diagnostic_result(
                all_assets=all_assets,
                investable_assets=investable_assets,
                objective_name=objective,
                n_assets=n_assets,
                max_weight=max_weight,
                feasibility_report=feasibility,
                solver_status=solver_status,
                solver_message=solver_message,
                fallback_reason=solver_message or "SLSQP failed",
            )

        optimized = pd.Series(solved, index=investable_assets, dtype=float)
        weights = self._expand_to_all_assets(all_assets, optimized)
        diagnostics = build_solver_diagnostics(
            solver_success=solver_success,
            solver_status=solver_status,
            solver_message=solver_message,
            objective_name=objective,
            n_assets=n_assets,
            max_weight=max_weight,
            weights=optimized,
            feasibility_report=feasibility,
            fallback_used=False,
            result_is_optimized=True,
        )
        return self._diagnostic_result(weights, diagnostics)

    def optimize_mean_variance(
        self,
        prices_df: pd.DataFrame,
        objective: str = "max_sharpe",
        max_weight: float = 0.2,
        risk_free_rate: float = 0.0,
    ) -> pd.Series:
        """Optimize mean-variance weights with scipy and constrained long-only bounds."""
        return self.optimize_mean_variance_with_diagnostics(
            prices_df=prices_df,
            objective=objective,
            max_weight=max_weight,
            risk_free_rate=risk_free_rate,
        ).weights
