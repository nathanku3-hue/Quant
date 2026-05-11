from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from core import engine as core_engine
from data.provenance import ManifestInput
from data.provenance import build_manifest
from data.provenance import compute_sha256
from data.provenance import load_manifest
from data.provenance import write_json_atomic
from data.provenance import write_manifest
from v2_discovery.fast_sim.cost_model import FastProxyCostModel
from v2_discovery.fast_sim.fixtures import SYNTHETIC_FIXTURE_SCOPE
from v2_discovery.fast_sim.fixtures import load_synthetic_proxy_fixture
from v2_discovery.fast_sim.ledger import build_synthetic_ledger
from v2_discovery.fast_sim.ledger import validate_synthetic_ledger_output
from v2_discovery.fast_sim.lineage import find_candidate_event
from v2_discovery.fast_sim.lineage import load_registry_events
from v2_discovery.fast_sim.run_candidate_proxy import G2_SYNTHETIC_FAMILY_ID
from v2_discovery.fast_sim.run_candidate_proxy import run_registered_candidate_proxy
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import V1_CANONICAL_ENGINE_NAME
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION
from v2_discovery.fast_sim.validation import validate_finite_numeric
from v2_discovery.fast_sim.validation import validate_no_nulls
from v2_discovery.fast_sim.validation import validate_positive_numeric
from v2_discovery.fast_sim.validation import validate_required_columns
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateEvent
from v2_discovery.schemas import CandidateSpec
from v2_discovery.replay.comparison import compare_allowed_mechanical_fields
from v2_discovery.replay.schemas import G3_BOUNDARY_VERDICT
from v2_discovery.replay.schemas import G3_REPORT_SCHEMA_VERSION
from v2_discovery.replay.schemas import G3_SCHEMA_VERSION
from v2_discovery.replay.schemas import G3_V1_ENGINE_VERSION
from v2_discovery.replay.schemas import G3_V1_REPLAY_ID
from v2_discovery.replay.schemas import G3MechanicalOutput
from v2_discovery.replay.schemas import G3ReplayError
from v2_discovery.replay.schemas import G3ReplayRun
from v2_discovery.replay.schemas import G3V1Replay
from v2_discovery.replay.schemas import G3V2ProxyReplay


G3_DEFAULT_REPORT_PATH = Path("data/registry/g3_canonical_replay_report.json")
G3_CODE_REF = "v2_discovery/replay/canonical_replay.py@phase65-g3"
G3_REPORT_PROVIDER_FEED = "g3_canonical_replay_report"


@dataclass(frozen=True)
class _AccountingOutput:
    positions: pd.DataFrame
    ledger: pd.DataFrame


def run_g3_canonical_replay_fixture(
    *,
    registry: CandidateRegistry | None = None,
    candidate_id: str | None = None,
    actor: str = "phase65_g3",
    report_path: str | Path | None = G3_DEFAULT_REPORT_PATH,
) -> G3ReplayRun:
    active_registry = registry or CandidateRegistry()
    candidate, candidate_event = require_exactly_one_registered_fixture_candidate(
        active_registry,
        candidate_id=candidate_id,
    )
    validate_g3_fixture_candidate(candidate, repo_root=active_registry.repo_root)

    try:
        proxy_run = run_registered_candidate_proxy(
            active_registry,
            candidate_id=candidate.candidate_id,
            actor=actor,
            report_path=None,
            candidate_event_id=candidate_event.event_id,
        )
    except ProxyBoundaryError as exc:
        raise G3ReplayError(str(exc)) from exc
    v2_replay = build_v2_proxy_mechanical_output(
        active_registry,
        candidate,
        proxy_run.proxy_result.registry_note_event_id,
        proxy_run.proxy_result.proxy_run_id,
    )
    v1_replay = run_v1_canonical_replay(active_registry, candidate)

    comparison = compare_allowed_mechanical_fields(
        v1_replay.output.to_allowed_fields(),
        v2_replay.output.to_allowed_fields(),
    )
    report = build_g3_replay_report(
        candidate=candidate,
        candidate_event=candidate_event,
        v1_replay=v1_replay,
        v2_replay=v2_replay,
        comparison=comparison,
        repo_root=active_registry.repo_root,
    )

    written_report_path: Path | None = None
    written_manifest_path: Path | None = None
    if report_path is not None:
        written_report_path, written_manifest_path = write_g3_replay_report(
            report,
            report_path,
            repo_root=active_registry.repo_root,
        )
    return G3ReplayRun(
        report=report,
        v1_replay=v1_replay,
        v2_replay=v2_replay,
        report_path=written_report_path,
        report_manifest_path=written_manifest_path,
    )


def require_exactly_one_registered_fixture_candidate(
    registry: CandidateRegistry,
    *,
    candidate_id: str | None = None,
) -> tuple[CandidateSpec, CandidateEvent]:
    snapshot = registry.rebuild_snapshot()
    fixture_ids = sorted(
        item.spec.candidate_id
        for item in snapshot.values()
        if item.spec.family_id == G2_SYNTHETIC_FAMILY_ID
    )
    if not fixture_ids:
        raise G3ReplayError("G3 requires existing registered candidate")
    if len(fixture_ids) != 1:
        raise G3ReplayError("G3 runs exactly one fixture candidate")
    if candidate_id is not None:
        if candidate_id not in snapshot:
            raise G3ReplayError("G3 requires existing registered candidate")
        if candidate_id != fixture_ids[0]:
            raise G3ReplayError("G3 requires a registered fixture candidate")

    candidate = snapshot[fixture_ids[0]].spec
    event = find_candidate_event(registry, candidate_id=candidate.candidate_id)
    return candidate, event


def validate_g3_fixture_candidate(
    candidate: CandidateSpec,
    *,
    repo_root: str | Path | None = None,
) -> None:
    if candidate.family_id != G2_SYNTHETIC_FAMILY_ID:
        raise G3ReplayError("G3 requires the registered G2 fixture family")
    if candidate.trial_count != 1:
        raise G3ReplayError("G3 requires exactly one registered fixture candidate")
    if not candidate.manifest_uri:
        raise G3ReplayError("G3 candidate manifest_uri is required")
    if not candidate.source_quality:
        raise G3ReplayError("G3 candidate source_quality is required")
    if not candidate.data_snapshot:
        raise G3ReplayError("G3 candidate data_snapshot is required")
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    manifest_path = _resolve_path(root, candidate.manifest_uri)
    if not manifest_path.exists():
        raise G3ReplayError(f"G3 candidate manifest_uri does not exist: {candidate.manifest_uri}")
    manifest = load_manifest(manifest_path)
    _validate_g3_fixture_manifest(manifest)
    if manifest.get("source_quality") != candidate.source_quality:
        raise G3ReplayError("G3 candidate source_quality must match manifest source_quality")
    expected_manifest_hash = compute_sha256(manifest_path)
    declared_manifest_hash = str(candidate.data_snapshot.get("manifest_sha256", "")).strip()
    if not declared_manifest_hash:
        raise G3ReplayError("G3 candidate data_snapshot.manifest_sha256 is required")
    if declared_manifest_hash != expected_manifest_hash:
        raise G3ReplayError("G3 candidate data_snapshot.manifest_sha256 mismatch")


def run_v1_canonical_replay(
    registry: CandidateRegistry,
    candidate: CandidateSpec,
) -> G3V1Replay:
    fixture = load_synthetic_proxy_fixture(candidate.manifest_uri, repo_root=registry.repo_root)
    cost_model = FastProxyCostModel.from_mapping(candidate.cost_model)
    target_weights = _weights_matrix(fixture.weights)
    returns = _returns_matrix(fixture.prices, target_weights)
    engine_output = core_engine.run_simulation(
        target_weights=target_weights,
        returns_df=returns,
        cost_bps=cost_model.total_cost_bps / 10000.0,
        strict_missing_returns=True,
    )
    _validate_engine_output(engine_output)
    accounting = _build_v1_accounting(fixture.prices, fixture.weights, cost_model)
    output = G3MechanicalOutput(
        candidate_id=candidate.candidate_id,
        manifest_uri=candidate.manifest_uri,
        source_quality=candidate.source_quality,
        positions=accounting.positions,
        ledger=accounting.ledger,
    )
    return G3V1Replay(
        replay_id=G3_V1_REPLAY_ID,
        engine_name=V1_CANONICAL_ENGINE_NAME,
        engine_version=G3_V1_ENGINE_VERSION,
        output=output,
        engine_rows=int(len(engine_output)),
    )


def build_v2_proxy_mechanical_output(
    registry: CandidateRegistry,
    candidate: CandidateSpec,
    registry_note_event_id: str,
    proxy_run_id: str,
) -> G3V2ProxyReplay:
    _require_registry_note(registry, registry_note_event_id, candidate_id=candidate.candidate_id)
    fixture = load_synthetic_proxy_fixture(candidate.manifest_uri, repo_root=registry.repo_root)
    cost_model = FastProxyCostModel.from_mapping(candidate.cost_model)
    proxy_accounting = build_synthetic_ledger(fixture.prices, fixture.weights, cost_model)
    validate_synthetic_ledger_output(proxy_accounting.positions, proxy_accounting.ledger)
    output = G3MechanicalOutput(
        candidate_id=candidate.candidate_id,
        manifest_uri=candidate.manifest_uri,
        source_quality=candidate.source_quality,
        positions=proxy_accounting.positions,
        ledger=proxy_accounting.ledger,
    )
    return G3V2ProxyReplay(
        proxy_run_id=proxy_run_id,
        engine_name=PROXY_ENGINE_NAME,
        engine_version=SYNTHETIC_PROXY_ENGINE_VERSION,
        registry_note_event_id=registry_note_event_id,
        output=output,
        promotion_ready=False,
        canonical_engine_required=True,
    )


def build_g3_replay_report(
    *,
    candidate: CandidateSpec,
    candidate_event: CandidateEvent,
    v1_replay: G3V1Replay,
    v2_replay: G3V2ProxyReplay,
    comparison: Mapping[str, Any],
    repo_root: Path,
) -> dict[str, Any]:
    manifest_path = _resolve_path(repo_root, candidate.manifest_uri)
    report = {
        "schema_version": G3_REPORT_SCHEMA_VERSION,
        "candidate_id": candidate.candidate_id,
        "family_id": candidate.family_id,
        "candidate_event_id": candidate_event.event_id,
        "proxy_run_id": v2_replay.proxy_run_id,
        "registry_note_event_id": v2_replay.registry_note_event_id,
        "v1_replay_id": v1_replay.replay_id,
        "v1_engine_name": v1_replay.engine_name,
        "v1_engine_version": v1_replay.engine_version,
        "v2_engine_name": v2_replay.engine_name,
        "v2_engine_version": v2_replay.engine_version,
        "manifest_uri": candidate.manifest_uri,
        "manifest_sha256": compute_sha256(manifest_path),
        "source_quality": candidate.source_quality,
        "data_snapshot": dict(candidate.data_snapshot),
        "code_ref": G3_CODE_REF,
        "comparison_fields": list(comparison["comparison_fields"]),
        "comparison_result": comparison["comparison_result"],
        "mismatch_count": int(comparison["mismatch_count"]),
        "promotion_ready": False,
        "canonical_engine_required": True,
        "boundary_verdict": G3_BOUNDARY_VERDICT,
    }
    validate_g3_replay_report(report)
    return report


def validate_g3_replay_report(report: Mapping[str, Any]) -> None:
    required = (
        "candidate_id",
        "family_id",
        "candidate_event_id",
        "proxy_run_id",
        "registry_note_event_id",
        "v1_replay_id",
        "v1_engine_name",
        "v1_engine_version",
        "v2_engine_name",
        "v2_engine_version",
        "manifest_uri",
        "manifest_sha256",
        "source_quality",
        "data_snapshot",
        "code_ref",
        "comparison_fields",
        "comparison_result",
        "mismatch_count",
        "promotion_ready",
        "canonical_engine_required",
        "boundary_verdict",
    )
    missing = [field for field in required if field not in report or report[field] in ("", None)]
    if missing:
        raise G3ReplayError("G3 replay report missing required field(s): " + ", ".join(missing))
    if report["v1_engine_name"] != V1_CANONICAL_ENGINE_NAME:
        raise G3ReplayError("G3 replay report must name the V1 canonical engine")
    if report["v2_engine_name"] != PROXY_ENGINE_NAME:
        raise G3ReplayError("G3 replay report must name the V2 proxy engine")
    if report["promotion_ready"] is not False:
        raise G3ReplayError("G3 report must keep promotion_ready=false")
    if report["canonical_engine_required"] is not True:
        raise G3ReplayError("G3 report must keep canonical_engine_required=true")
    if report["boundary_verdict"] != G3_BOUNDARY_VERDICT:
        raise G3ReplayError("G3 report must keep V2 blocked from promotion")


def write_g3_replay_report(
    report: Mapping[str, Any],
    report_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> tuple[Path, Path]:
    root = Path(repo_root) if repo_root is not None else Path.cwd()
    target = _resolve_path(root, report_path)
    write_json_atomic(dict(report), target)
    artifact_path: str | Path = target
    try:
        artifact_path = target.relative_to(root)
    except ValueError:
        pass
    manifest = build_manifest(
        ManifestInput(
            artifact_path=artifact_path,
            source_quality=str(report["source_quality"]),
            provider="synthetic_fixture",
            provider_feed=G3_REPORT_PROVIDER_FEED,
            license_scope="synthetic_fixture_only",
            row_count=1,
            date_range={"start": "2026-05-09", "end": "2026-05-09"},
            extra={
                "candidate_id": report["candidate_id"],
                "v1_replay_id": report["v1_replay_id"],
                "proxy_run_id": report["proxy_run_id"],
                "boundary_verdict": report["boundary_verdict"],
            },
        )
    )
    manifest_path = Path(f"{target}.manifest.json")
    write_manifest(manifest, manifest_path)
    return target, manifest_path


def _build_v1_accounting(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_model: FastProxyCostModel,
) -> _AccountingOutput:
    _validate_accounting_inputs(prices, weights, cost_model)
    price_matrix = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    weight_matrix = weights.pivot(index="date", columns="symbol", values="target_weight").sort_index()
    symbols = sorted(weight_matrix.columns)
    price_matrix = price_matrix.reindex(index=weight_matrix.index, columns=symbols)
    if price_matrix.isna().any().any() or weight_matrix.isna().any().any():
        raise G3ReplayError("G3 V1 replay requires complete fixture price/weight matrices")

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
            raise G3ReplayError("G3 V1 replay equity must stay positive")
        current_weights = current_values / equity_before_cost
        turnover = float((targets - current_weights).abs().sum())
        transaction_cost = cost_model.transaction_cost(
            equity=equity_before_cost,
            turnover=turnover,
        )
        equity_after_cost = equity_before_cost - transaction_cost
        if equity_after_cost <= 0:
            raise G3ReplayError("G3 V1 replay costs exhausted equity")
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
    return _AccountingOutput(positions=positions, ledger=ledger)


def _weights_matrix(weights: pd.DataFrame) -> pd.DataFrame:
    matrix = weights.pivot(index="date", columns="symbol", values="target_weight").sort_index()
    if matrix.isna().any().any():
        raise G3ReplayError("G3 V1 target weights must be complete")
    return matrix.astype("float64")


def _returns_matrix(prices: pd.DataFrame, target_weights: pd.DataFrame) -> pd.DataFrame:
    price_matrix = prices.pivot(index="date", columns="symbol", values="close").sort_index()
    price_matrix = price_matrix.reindex(index=target_weights.index, columns=target_weights.columns)
    if price_matrix.isna().any().any():
        raise G3ReplayError("G3 V1 returns matrix requires complete fixture prices")
    returns = price_matrix.astype("float64").pct_change().fillna(0.0)
    return returns


def _validate_engine_output(output: pd.DataFrame) -> None:
    validate_required_columns(output.reset_index(drop=True), ("gross_ret", "net_ret", "turnover", "cost"), "G3 V1 engine output")
    validate_no_nulls(output.reset_index(drop=True), ("gross_ret", "net_ret", "turnover", "cost"), "G3 V1 engine output")
    validate_finite_numeric(output.reset_index(drop=True), ("gross_ret", "net_ret", "turnover", "cost"), "G3 V1 engine output")


def _validate_accounting_inputs(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_model: FastProxyCostModel,
) -> None:
    validate_required_columns(prices, ("date", "symbol", "close"), "G3 V1 prices")
    validate_no_nulls(prices, ("date", "symbol", "close"), "G3 V1 prices")
    validate_positive_numeric(prices, ("close",), "G3 V1 prices")
    validate_required_columns(weights, ("date", "symbol", "target_weight"), "G3 V1 target weights")
    validate_no_nulls(weights, ("date", "symbol", "target_weight"), "G3 V1 target weights")
    validate_finite_numeric(weights, ("target_weight",), "G3 V1 target weights")
    validate_positive_numeric(
        pd.DataFrame(
            {
                "initial_cash": [cost_model.initial_cash],
                "max_gross_exposure": [cost_model.max_gross_exposure],
            }
        ),
        ("initial_cash", "max_gross_exposure"),
        "G3 V1 cost assumptions",
    )


def _validate_g3_fixture_manifest(manifest: Mapping[str, Any]) -> None:
    extra = manifest.get("extra")
    if (
        manifest.get("provider") != "synthetic_fixture"
        or manifest.get("provider_feed") != "prebaked_target_weights"
        or manifest.get("license_scope") != "synthetic_fixture_only"
        or not isinstance(extra, Mapping)
        or extra.get("fixture_scope") != SYNTHETIC_FIXTURE_SCOPE
    ):
        raise G3ReplayError("G3 rejects Tier 2/non-fixture replay candidates")


def _require_registry_note(
    registry: CandidateRegistry,
    registry_note_event_id: str,
    *,
    candidate_id: str,
) -> None:
    for event in load_registry_events(registry):
        if event.event_id != registry_note_event_id:
            continue
        if event.candidate_id != candidate_id:
            raise G3ReplayError("G3 registry_note_event_id candidate mismatch")
        if event.event_type != "candidate.note_added":
            raise G3ReplayError("G3 registry_note_event_id must be a registry note")
        return
    raise G3ReplayError("G3 registry_note_event_id does not exist")


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _round(value: float) -> float:
    return round(float(value), 6)
