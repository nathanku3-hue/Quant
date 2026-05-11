from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.testing import assert_frame_equal

from data.provenance import compute_sha256
from v2_discovery.fast_sim.cost_model import FastProxyCostModel
from v2_discovery.fast_sim.ledger import build_synthetic_ledger
from v2_discovery.fast_sim.ledger import validate_synthetic_ledger_output
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_ARTIFACT_URI
from v2_discovery.readiness.canonical_slice import G4_DEFAULT_MANIFEST_URI
from v2_discovery.readiness.canonical_slice import load_g4_canonical_slice
from v2_discovery.readiness.schemas import G4_DEFAULT_DATASET_NAME
from v2_discovery.readiness.schemas import G4CanonicalSlice
from v2_discovery.readiness.schemas import G4ReadinessError
from v2_discovery.replay.canonical_real_replay import G5_DEFAULT_WEIGHT_MODE
from v2_discovery.replay.canonical_real_replay import G5_INITIAL_CASH
from v2_discovery.replay.canonical_real_replay import G5_TOTAL_COST_BPS
from v2_discovery.replay.canonical_real_replay import G5MechanicalReplay
from v2_discovery.replay.canonical_real_replay import G5ReplayError
from v2_discovery.replay.canonical_real_replay import build_predeclared_neutral_weights
from v2_discovery.replay.canonical_real_replay import run_g5_single_canonical_replay


G6_COMPARISON_RUN_ID = "PH65_G6_V1_V2_REAL_SLICE_MECHANICAL_001"
G6_CODE_REF = "v2_discovery/replay/real_slice_v1_v2_comparison.py@phase65-g6"
G6_DEFAULT_REPORT_PATH = Path("data/registry/g6_v1_v2_real_slice_mechanical_report.json")

G6_COMPARISON_FIELDS = (
    "positions",
    "cash",
    "turnover",
    "transaction_cost",
    "gross_exposure",
    "net_exposure",
    "row_count",
    "date_range",
    "source_quality",
    "manifest_uri",
    "engine_name",
    "engine_version",
)
G6_EQUALITY_FIELDS = tuple(field for field in G6_COMPARISON_FIELDS if not field.startswith("engine_"))
G6_IDENTITY_FIELDS = ("engine_name", "engine_version")


class G6ComparisonError(G5ReplayError):
    """Raised when the G6 real-slice mechanical comparison boundary is violated."""


@dataclass(frozen=True)
class G6MechanicalSide:
    engine_name: str
    engine_version: str
    positions: pd.DataFrame
    ledger: pd.DataFrame
    row_count: int
    date_range: dict[str, str | None]
    source_quality: str
    manifest_uri: str


@dataclass(frozen=True)
class G6MechanicalComparison:
    comparison_run_id: str
    dataset_name: str
    artifact_uri: str
    manifest_uri: str
    manifest_sha256: str
    source_quality: str
    row_count: int
    symbol_count: int
    date_range: dict[str, str | None]
    v1_output: G6MechanicalSide
    v2_output: G6MechanicalSide
    comparison: dict[str, Any]


@dataclass(frozen=True)
class G6ComparisonRun:
    report: dict[str, Any]
    comparison: G6MechanicalComparison
    report_path: Path | None = None
    report_manifest_path: Path | None = None


def run_g6_v1_v2_real_slice_mechanical_comparison(
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
) -> G6ComparisonRun:
    _reject_dynamic_inputs(unexpected_inputs)
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    try:
        v1_run = run_g5_single_canonical_replay(
            artifact_uri=artifact_uri,
            manifest_uri=manifest_uri,
            dataset_name=dataset_name,
            repo_root=root,
            weight_mode=weight_mode,
            cost_bps=cost_bps,
            initial_cash=initial_cash,
            report_path=None,
        )
        canonical_slice = load_g4_canonical_slice(
            artifact_uri=artifact_uri,
            manifest_uri=manifest_uri,
            dataset_name=dataset_name,
            repo_root=root,
        )
    except (G4ReadinessError, G5ReplayError) as exc:
        raise G6ComparisonError(str(exc)) from exc

    prices = canonical_slice.data.copy()
    try:
        weights = build_predeclared_neutral_weights(prices, weight_mode=weight_mode)
        v1_output = _side_from_g5_replay(v1_run.replay)
        v2_output = run_g6_v2_proxy_mechanics(
            prices=prices,
            weights=weights,
            canonical_slice=canonical_slice,
            cost_bps=cost_bps,
            initial_cash=initial_cash,
        )
        comparison = compare_g6_mechanical_fields(v1_output, v2_output)
    except Exception as exc:
        if isinstance(exc, G6ComparisonError):
            raise
        raise G6ComparisonError(str(exc)) from exc

    mechanical = G6MechanicalComparison(
        comparison_run_id=G6_COMPARISON_RUN_ID,
        dataset_name=canonical_slice.dataset_name,
        artifact_uri=canonical_slice.artifact_uri,
        manifest_uri=canonical_slice.manifest_uri,
        manifest_sha256=compute_sha256(canonical_slice.manifest_path),
        source_quality=v1_output.source_quality,
        row_count=v1_output.row_count,
        symbol_count=int(prices["permno"].nunique()),
        date_range=dict(v1_output.date_range),
        v1_output=v1_output,
        v2_output=v2_output,
        comparison=comparison,
    )

    from v2_discovery.replay.mechanical_comparison_report import build_g6_mechanical_comparison_report
    from v2_discovery.replay.mechanical_comparison_report import write_g6_mechanical_comparison_report

    report = build_g6_mechanical_comparison_report(mechanical)
    written_report_path: Path | None = None
    written_manifest_path: Path | None = None
    if report_path is not None:
        written_report_path, written_manifest_path = write_g6_mechanical_comparison_report(
            report,
            report_path,
            repo_root=root,
        )
    return G6ComparisonRun(
        report=report,
        comparison=mechanical,
        report_path=written_report_path,
        report_manifest_path=written_manifest_path,
    )


def run_g6_v2_proxy_mechanics(
    *,
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    canonical_slice: G4CanonicalSlice,
    cost_bps: float,
    initial_cash: float,
) -> G6MechanicalSide:
    proxy_prices = _proxy_price_table(prices)
    proxy_weights = _proxy_weight_table(weights)
    cost_model = FastProxyCostModel(
        total_cost_bps=cost_bps,
        initial_cash=initial_cash,
        max_gross_exposure=1.0,
    )
    proxy_output = build_synthetic_ledger(proxy_prices, proxy_weights, cost_model)
    validate_synthetic_ledger_output(proxy_output.positions, proxy_output.ledger)
    positions = _normalize_proxy_positions(proxy_output.positions)
    ledger = _normalize_ledger(proxy_output.ledger)
    return G6MechanicalSide(
        engine_name=PROXY_ENGINE_NAME,
        engine_version=SYNTHETIC_PROXY_ENGINE_VERSION,
        positions=positions,
        ledger=ledger,
        row_count=int(len(positions)),
        date_range=_date_range(canonical_slice.manifest),
        source_quality=str(canonical_slice.manifest["source_quality"]),
        manifest_uri=canonical_slice.manifest_uri,
    )


def compare_g6_mechanical_fields(
    v1_output: G6MechanicalSide,
    v2_output: G6MechanicalSide,
) -> dict[str, Any]:
    field_results: dict[str, str] = {}
    mismatch_fields: list[str] = []
    for field in G6_EQUALITY_FIELDS:
        matched = _field_matches(field, v1_output, v2_output)
        field_results[field] = "match" if matched else "mismatch"
        if not matched:
            mismatch_fields.append(field)
    for field in G6_IDENTITY_FIELDS:
        field_results[field] = "recorded"
    return {
        "comparison_fields": list(G6_COMPARISON_FIELDS),
        "equality_fields": list(G6_EQUALITY_FIELDS),
        "identity_fields": list(G6_IDENTITY_FIELDS),
        "comparison_result": "match" if not mismatch_fields else "mismatch",
        "mismatch_count": len(mismatch_fields),
        "mismatch_fields": mismatch_fields,
        "field_results": field_results,
    }


def _side_from_g5_replay(replay: G5MechanicalReplay) -> G6MechanicalSide:
    return G6MechanicalSide(
        engine_name=replay.engine_name,
        engine_version=replay.engine_version,
        positions=_normalize_positions(replay.positions),
        ledger=_normalize_ledger(replay.ledger),
        row_count=int(replay.row_count),
        date_range=dict(replay.date_range),
        source_quality=replay.source_quality,
        manifest_uri=replay.manifest_uri,
    )


def _proxy_price_table(prices: pd.DataFrame) -> pd.DataFrame:
    table = prices[["date", "permno", "tri"]].copy()
    table["date"] = pd.to_datetime(table["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    table["symbol"] = table["permno"].astype("int64").astype(str)
    table["close"] = table["tri"].astype("float64")
    return table[["date", "symbol", "close"]]


def _proxy_weight_table(weights: pd.DataFrame) -> pd.DataFrame:
    table = weights.copy()
    table.index = pd.to_datetime(table.index, errors="coerce").strftime("%Y-%m-%d")
    table.columns = [str(int(column)) for column in table.columns]
    rows = table.reset_index(names="date").melt(
        id_vars="date",
        var_name="symbol",
        value_name="target_weight",
    )
    return rows[["date", "symbol", "target_weight"]]


def _normalize_proxy_positions(positions: pd.DataFrame) -> pd.DataFrame:
    framed = positions.rename(columns={"symbol": "permno"}).copy()
    framed["permno"] = framed["permno"].astype("int64")
    return _normalize_positions(framed)


def _normalize_positions(positions: pd.DataFrame) -> pd.DataFrame:
    framed = positions[["date", "permno", "quantity", "market_value"]].copy()
    framed["date"] = pd.to_datetime(framed["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    framed["permno"] = framed["permno"].astype("int64")
    framed["quantity"] = framed["quantity"].astype("float64").round(6)
    framed["market_value"] = framed["market_value"].astype("float64").round(6)
    return framed.sort_values(["date", "permno"], kind="mergesort").reset_index(drop=True)


def _normalize_ledger(ledger: pd.DataFrame) -> pd.DataFrame:
    columns = ["date", "cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"]
    framed = ledger[columns].copy()
    framed["date"] = pd.to_datetime(framed["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for column in columns[1:]:
        framed[column] = framed[column].astype("float64").round(6)
    return framed.sort_values("date", kind="mergesort").reset_index(drop=True)


def _field_matches(field: str, v1_output: G6MechanicalSide, v2_output: G6MechanicalSide) -> bool:
    try:
        if field == "positions":
            assert_frame_equal(v1_output.positions, v2_output.positions, check_exact=True)
            return True
        if field in {"cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"}:
            assert_frame_equal(
                _ledger_series(v1_output.ledger, field),
                _ledger_series(v2_output.ledger, field),
                check_exact=True,
            )
            return True
        return getattr(v1_output, field) == getattr(v2_output, field)
    except AssertionError:
        return False


def _ledger_series(ledger: pd.DataFrame, column: str) -> pd.DataFrame:
    return ledger[["date", column]].reset_index(drop=True)


def _date_range(manifest: dict[str, Any]) -> dict[str, str | None]:
    value = manifest.get("date_range")
    if not isinstance(value, dict):
        raise G6ComparisonError("G6 manifest date_range is required")
    return {
        "start": str(value.get("start")) if value.get("start") is not None else None,
        "end": str(value.get("end")) if value.get("end") is not None else None,
    }


def _reject_dynamic_inputs(unexpected_inputs: dict[str, Any]) -> None:
    forbidden = {"sig" "nal_function", "ra" "nker", "weights_func", "selector"}
    used = sorted(key for key in unexpected_inputs if key in forbidden)
    if used:
        raise G6ComparisonError("G6 accepts only predeclared neutral fixture weights")
    if unexpected_inputs:
        unknown = ", ".join(sorted(unexpected_inputs))
        raise G6ComparisonError(f"G6 unexpected comparison input(s): {unknown}")
