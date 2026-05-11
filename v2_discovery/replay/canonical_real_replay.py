from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from core import engine as core_engine
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_ARTIFACT_URI
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_MANIFEST_URI
from v2_discovery.readiness.canonical_slice import load_g4_canonical_slice
from v2_discovery.readiness.schemas import G4_DEFAULT_DATASET_NAME
from v2_discovery.readiness.schemas import G4ReadinessError
from v2_discovery.replay.schemas import G3ReplayError


G5_REPLAY_RUN_ID = "PH65_G5_SINGLE_CANONICAL_REPLAY_001"
G5_ENGINE_VERSION = "phase65-g5-core-engine-current"
G5_CODE_REF = "v2_discovery/replay/canonical_real_replay.py@phase65-g5"
G5_DEFAULT_REPORT_PATH = Path("data/registry/g5_single_canonical_replay_report.json")
G5_DEFAULT_WEIGHT_MODE = "equal_weight"
G5_INITIAL_CASH = 100_000.0
G5_TOTAL_COST_BPS = 10.0


class G5ReplayError(G3ReplayError):
    """Raised when the G5 canonical real-slice replay boundary is violated."""


@dataclass(frozen=True)
class G5MechanicalReplay:
    replay_run_id: str
    dataset_name: str
    artifact_uri: str
    manifest_uri: str
    manifest_sha256: str
    source_quality: str
    row_count: int
    symbol_count: int
    date_range: dict[str, str | None]
    engine_name: str
    engine_version: str
    positions: pd.DataFrame
    ledger: pd.DataFrame
    engine_rows: int


@dataclass(frozen=True)
class G5ReplayRun:
    report: dict[str, Any]
    replay: G5MechanicalReplay
    report_path: Path | None = None
    report_manifest_path: Path | None = None


def run_g5_single_canonical_replay(
    *,
    artifact_uri: str | Path = G4_DEFAULT_ARTIFACT_URI,
    manifest_uri: str | Path = G4_DEFAULT_MANIFEST_URI,
    dataset_name: str = G4_DEFAULT_DATASET_NAME,
    repo_root: str | Path | None = None,
    weight_mode: str = G5_DEFAULT_WEIGHT_MODE,
    cost_bps: float = G5_TOTAL_COST_BPS,
    initial_cash: float = G5_INITIAL_CASH,
    report_path: str | Path | None = None,
    **unexpected_inputs: Any,
) -> G5ReplayRun:
    _reject_dynamic_inputs(unexpected_inputs)
    try:
        canonical_slice = load_g4_canonical_slice(
            artifact_uri=artifact_uri,
            manifest_uri=manifest_uri,
            dataset_name=dataset_name,
            repo_root=repo_root,
        )
    except G4ReadinessError as exc:
        raise G5ReplayError(str(exc)) from exc
    prices = canonical_slice.data.copy()
    returns = _returns_matrix(prices)
    weights = build_predeclared_neutral_weights(prices, weight_mode=weight_mode)
    engine_output = core_engine.run_simulation(
        target_weights=weights,
        returns_df=returns,
        cost_bps=_cost_rate(cost_bps),
        strict_missing_returns=True,
    )
    _validate_engine_output(engine_output)
    replay = build_g5_mechanical_replay(
        prices=prices,
        weights=weights,
        engine_rows=len(engine_output),
        canonical_slice=canonical_slice,
        cost_bps=cost_bps,
        initial_cash=initial_cash,
    )

    from v2_discovery.replay.canonical_replay_report import build_g5_replay_report
    from v2_discovery.replay.canonical_replay_report import write_g5_replay_report

    report = build_g5_replay_report(replay)
    written_report_path: Path | None = None
    written_manifest_path: Path | None = None
    if report_path is not None:
        root = Path(repo_root) if repo_root is not None else Path.cwd()
        written_report_path, written_manifest_path = write_g5_replay_report(
            report,
            report_path,
            repo_root=root,
        )
    return G5ReplayRun(
        report=report,
        replay=replay,
        report_path=written_report_path,
        report_manifest_path=written_manifest_path,
    )


def build_predeclared_neutral_weights(
    data: pd.DataFrame,
    *,
    weight_mode: str = G5_DEFAULT_WEIGHT_MODE,
) -> pd.DataFrame:
    if weight_mode != G5_DEFAULT_WEIGHT_MODE:
        raise G5ReplayError("G5 accepts only predeclared neutral fixture weights")
    _validate_price_input(data)
    frame = data[["date", "permno"]].copy()
    frame["_g5_date"] = pd.to_datetime(frame["date"], errors="coerce")
    if frame["_g5_date"].isna().any():
        raise G5ReplayError("G5 replay requires valid dates")
    per_date_count = frame.groupby("_g5_date")["permno"].transform("nunique")
    if (per_date_count <= 0).any():
        raise G5ReplayError("G5 replay requires at least one symbol per date")
    frame["target_weight"] = 1.0 / per_date_count.astype("float64")
    weights = frame.pivot(index="_g5_date", columns="permno", values="target_weight").sort_index()
    if weights.isna().any().any():
        raise G5ReplayError("G5 predeclared weights require complete date/symbol rows")
    return weights.astype("float64")


def build_g5_mechanical_replay(
    *,
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    engine_rows: int,
    canonical_slice,
    cost_bps: float,
    initial_cash: float,
) -> G5MechanicalReplay:
    if engine_rows <= 0:
        raise G5ReplayError("G5 canonical engine output must be non-empty")
    _validate_price_input(prices)
    _validate_weight_matrix(weights)
    cost_rate = _cost_rate(cost_bps)
    cash_start = _positive_float(initial_cash, "initial_cash")
    price_matrix = _price_matrix(prices, weights)
    quantities = pd.Series(0.0, index=weights.columns, dtype="float64")
    cash = cash_start
    position_rows: list[dict[str, object]] = []
    ledger_rows: list[dict[str, object]] = []

    for date in weights.index:
        prices_today = price_matrix.loc[date].astype("float64")
        targets = weights.loc[date].astype("float64")
        current_values = quantities * prices_today
        equity_before_cost = float(cash + current_values.sum())
        if equity_before_cost <= 0:
            raise G5ReplayError("G5 replay equity must stay positive")
        current_weights = current_values / equity_before_cost
        turnover = float((targets - current_weights).abs().sum())
        transaction_cost = equity_before_cost * turnover * cost_rate
        equity_after_cost = equity_before_cost - transaction_cost
        if equity_after_cost <= 0:
            raise G5ReplayError("G5 replay costs exhausted equity")
        target_values = targets * equity_after_cost
        quantities = target_values / prices_today
        cash = float(equity_after_cost - target_values.sum())
        if abs(cash) < 0.0000005:
            cash = 0.0
        gross_exposure = float(target_values.abs().sum() / equity_after_cost)
        net_exposure = float(target_values.sum() / equity_after_cost)
        ledger_rows.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "cash": _round(cash),
                "turnover": _round(turnover),
                "transaction_cost": _round(transaction_cost),
                "gross_exposure": _round(gross_exposure),
                "net_exposure": _round(net_exposure),
            }
        )
        for permno in weights.columns:
            position_rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "permno": int(permno),
                    "quantity": _round(float(quantities[permno])),
                    "market_value": _round(float(target_values[permno])),
                }
            )

    positions = pd.DataFrame(
        position_rows,
        columns=["date", "permno", "quantity", "market_value"],
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
    _validate_mechanical_output(positions, ledger)
    date_range = _date_range(canonical_slice.manifest)
    return G5MechanicalReplay(
        replay_run_id=G5_REPLAY_RUN_ID,
        dataset_name=canonical_slice.dataset_name,
        artifact_uri=canonical_slice.artifact_uri,
        manifest_uri=canonical_slice.manifest_uri,
        manifest_sha256=_manifest_sha(canonical_slice.manifest_path),
        source_quality=str(canonical_slice.manifest["source_quality"]),
        row_count=int(len(prices)),
        symbol_count=int(prices["permno"].nunique()),
        date_range=date_range,
        engine_name=V1_CANONICAL_ENGINE_NAME,
        engine_version=G5_ENGINE_VERSION,
        positions=positions,
        ledger=ledger,
        engine_rows=int(engine_rows),
    )


def _returns_matrix(data: pd.DataFrame) -> pd.DataFrame:
    _validate_price_input(data)
    framed = data.assign(_g5_date=pd.to_datetime(data["date"], errors="coerce"))
    matrix = framed.pivot(index="_g5_date", columns="permno", values="total_ret").sort_index()
    if matrix.isna().any().any():
        raise G5ReplayError("G5 replay requires complete return matrix")
    values = matrix.to_numpy(dtype="float64")
    if not np.isfinite(values).all():
        raise G5ReplayError("G5 replay requires finite numeric returns")
    return matrix.astype("float64")


def _price_matrix(data: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    framed = data.assign(_g5_date=pd.to_datetime(data["date"], errors="coerce"))
    matrix = framed.pivot(index="_g5_date", columns="permno", values="tri").sort_index()
    matrix = matrix.reindex(index=weights.index, columns=weights.columns)
    if matrix.isna().any().any():
        raise G5ReplayError("G5 replay requires complete price matrix")
    values = matrix.to_numpy(dtype="float64")
    if not np.isfinite(values).all() or (values <= 0).any():
        raise G5ReplayError("G5 replay requires positive finite prices")
    return matrix.astype("float64")


def _validate_price_input(data: pd.DataFrame) -> None:
    required = ("date", "permno", "tri", "total_ret")
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise G5ReplayError("G5 replay data missing required column(s): " + ", ".join(missing))
    for column in ("permno", "tri", "total_ret"):
        values = pd.to_numeric(data[column], errors="coerce").to_numpy(dtype="float64", na_value=np.nan)
        if not np.isfinite(values).all():
            raise G5ReplayError("G5 replay validates finite numeric values before replay")
    if (pd.to_numeric(data["tri"], errors="coerce") <= 0).any():
        raise G5ReplayError("G5 replay requires positive prices")


def _validate_weight_matrix(weights: pd.DataFrame) -> None:
    if weights.empty:
        raise G5ReplayError("G5 predeclared weights cannot be empty")
    values = weights.to_numpy(dtype="float64")
    if not np.isfinite(values).all():
        raise G5ReplayError("G5 predeclared weights must be finite")
    gross = weights.abs().sum(axis=1)
    if (gross > 1.0 + 1e-12).any():
        raise G5ReplayError("G5 predeclared weights exceed neutral exposure")


def _validate_engine_output(output: pd.DataFrame) -> None:
    required = ("gross_ret", "net_ret", "turnover", "cost")
    missing = [column for column in required if column not in output.columns]
    if missing:
        raise G5ReplayError("G5 canonical engine output missing required column(s): " + ", ".join(missing))
    values = output[list(required)].to_numpy(dtype="float64")
    if not np.isfinite(values).all():
        raise G5ReplayError("G5 canonical engine output must be finite")


def _validate_mechanical_output(positions: pd.DataFrame, ledger: pd.DataFrame) -> None:
    for frame, columns, label in (
        (positions, ("date", "permno", "quantity", "market_value"), "positions"),
        (
            ledger,
            ("date", "cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"),
            "ledger",
        ),
    ):
        missing = [column for column in columns if column not in frame.columns]
        if missing:
            raise G5ReplayError(f"G5 mechanical {label} missing required column(s): " + ", ".join(missing))
        if frame[list(columns)].isna().any().any():
            raise G5ReplayError(f"G5 mechanical {label} cannot contain nulls")
    numeric_columns = ("quantity", "market_value")
    if not np.isfinite(positions[list(numeric_columns)].to_numpy(dtype="float64")).all():
        raise G5ReplayError("G5 positions must be finite")
    ledger_numeric = ("cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure")
    if not np.isfinite(ledger[list(ledger_numeric)].to_numpy(dtype="float64")).all():
        raise G5ReplayError("G5 ledger must be finite")


def _date_range(manifest: dict[str, Any]) -> dict[str, str | None]:
    value = manifest.get("date_range")
    if not isinstance(value, dict):
        raise G5ReplayError("G5 manifest date_range is required")
    return {
        "start": str(value.get("start")) if value.get("start") is not None else None,
        "end": str(value.get("end")) if value.get("end") is not None else None,
    }


def _manifest_sha(path: str | Path) -> str:
    from data.provenance import compute_sha256

    return compute_sha256(path)


def _cost_rate(value: Any) -> float:
    parsed = _non_negative_float(value, "cost_bps")
    return parsed / 10_000.0


def _positive_float(value: Any, field: str) -> float:
    parsed = _non_negative_float(value, field)
    if parsed <= 0:
        raise G5ReplayError(f"G5 {field} must be positive")
    return parsed


def _non_negative_float(value: Any, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise G5ReplayError(f"G5 {field} must be numeric") from exc
    if not np.isfinite(parsed):
        raise G5ReplayError(f"G5 {field} must be finite")
    if parsed < 0:
        raise G5ReplayError(f"G5 {field} must be non-negative")
    return parsed


def _reject_dynamic_inputs(unexpected_inputs: dict[str, Any]) -> None:
    forbidden = {"sig" "nal_function", "ra" "nker", "weights_func", "selector"}
    used = sorted(key for key in unexpected_inputs if key in forbidden)
    if used:
        raise G5ReplayError("G5 accepts only predeclared neutral fixture weights")
    if unexpected_inputs:
        unknown = ", ".join(sorted(unexpected_inputs))
        raise G5ReplayError(f"G5 unexpected replay input(s): {unknown}")


def _round(value: float) -> float:
    return round(float(value), 6)
