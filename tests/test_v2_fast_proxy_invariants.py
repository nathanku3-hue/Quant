from __future__ import annotations

import inspect
import json
from pathlib import Path

import pandas as pd
import pytest

from data.provenance import compute_sha256
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import utc_now_iso
from v2_discovery.fast_sim import cost_model
from v2_discovery.fast_sim import fixtures
from v2_discovery.fast_sim import ledger
from v2_discovery.fast_sim import simulator
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION
from v2_discovery.fast_sim.simulator import SyntheticFastProxySimulator
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


FIXTURE_DIR = Path("data/fixtures/v2_proxy")
MANIFEST_URI = FIXTURE_DIR / "synthetic_manifest.json"


def _registry(tmp_path: Path) -> CandidateRegistry:
    return CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=Path.cwd(),
    )


def _candidate(**overrides) -> CandidateSpec:
    payload = {
        "candidate_id": "PH65_G1_SYNTHETIC_INVARIANT_001",
        "family_id": "SYNTHETIC_FAST_PROXY_MECHANICS",
        "hypothesis": "Synthetic invariant fixture only; no alpha.",
        "universe": "SYNTHETIC_TWO_SYMBOL",
        "features": ["prebaked_target_weight"],
        "parameters_searched": {"prebaked_weights_only": [True]},
        "trial_count": 1,
        "train_window": {"start": "2020-01-02", "end": "2020-01-03"},
        "test_window": {"start": "2020-01-02", "end": "2020-01-03"},
        "cost_model": {
            "initial_cash": 100000.0,
            "total_cost_bps": 10.0,
            "max_gross_exposure": 1.0,
        },
        "data_snapshot": {"dataset": "synthetic_v2_proxy_fixture", "asof": "2026-05-09"},
        "manifest_uri": MANIFEST_URI.as_posix(),
        "source_quality": SOURCE_QUALITY_NON_CANONICAL,
        "created_at": utc_now_iso(),
        "created_by": "pytest",
        "code_ref": "phase65-g1-invariant-tests",
        "status": CandidateStatus.GENERATED,
    }
    payload.update(overrides)
    return CandidateSpec(**payload)


def _registered_spec(tmp_path: Path, **overrides) -> tuple[CandidateRegistry, ProxyRunSpec]:
    registry = _registry(tmp_path)
    candidate = _candidate(**overrides)
    event = registry.register_candidate(candidate, actor="pytest")
    return registry, _proxy_spec(candidate, event.event_id)


def _proxy_spec(candidate: CandidateSpec, registry_event_id: str, **overrides) -> ProxyRunSpec:
    payload = {
        "proxy_run_id": "PH65_G1_PROXY_INVARIANT_001",
        "candidate_id": candidate.candidate_id,
        "registry_event_id": registry_event_id,
        "manifest_uri": candidate.manifest_uri,
        "source_quality": candidate.source_quality,
        "data_snapshot": dict(candidate.data_snapshot),
        "code_ref": "phase65-g1-invariant-tests",
        "engine_name": PROXY_ENGINE_NAME,
        "engine_version": SYNTHETIC_PROXY_ENGINE_VERSION,
        "cost_model": dict(candidate.cost_model),
        "train_window": dict(candidate.train_window),
        "test_window": dict(candidate.test_window),
        "created_at": utc_now_iso(),
        "promotion_ready": False,
        "canonical_engine_required": True,
    }
    payload.update(overrides)
    return ProxyRunSpec(**payload)


def test_prebaked_weights_only_no_signal_function():
    source = "\n".join(
        inspect.getsource(module)
        for module in (cost_model, fixtures, ledger, simulator)
    ).lower()

    assert "generate_signal" not in source
    assert "signal_function" not in source
    assert "pead" not in source
    assert "momentum" not in source
    assert "value_strategy" not in source
    assert "ranking" not in source
    assert "sharpe" not in source
    assert "alpha" not in source
    assert "cagr" not in source
    assert "max_drawdown" not in source


def test_proxy_cannot_emit_alert():
    forbidden_methods = {"emit_alert", "alert_candidate", "build_alert_packet"}
    assert forbidden_methods.isdisjoint(set(dir(SyntheticFastProxySimulator)))


def test_proxy_cannot_call_broker():
    source = "\n".join(
        inspect.getsource(module)
        for module in (cost_model, fixtures, ledger, simulator)
    )
    assert "BrokerPort" not in source
    assert "submit_order" not in source
    assert "broker_api" not in source
    assert "alpaca" not in source.lower()


def test_output_contains_only_allowed_result_keys(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)

    assert set(output.result) == {
        "manifest_uri",
        "row_count",
        "date_range",
        "cash",
        "turnover",
        "transaction_cost",
        "gross_exposure",
        "net_exposure",
        "boundary_verdict",
        "promotion_ready",
        "canonical_engine_required",
    }


def test_accounting_invariants_hold(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)

    assert (output.ledger["cash"] >= 0).all()
    assert (output.ledger["turnover"] >= 0).all()
    assert (output.ledger["transaction_cost"] >= 0).all()
    assert (output.ledger["gross_exposure"] >= output.ledger["net_exposure"].abs()).all()


def test_accounting_property_equity_reconciles_after_costs(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)
    prices = pd.read_csv(FIXTURE_DIR / "synthetic_prices.csv")
    price_matrix = prices.pivot(index="date", columns="symbol", values="close")
    positions = output.positions
    previous_quantities = pd.Series({"AAA": 0.0, "BBB": 0.0})
    previous_cash = float(spec.cost_model["initial_cash"])

    for row in output.ledger.itertuples(index=False):
        current_prices = price_matrix.loc[row.date]
        equity_before_cost = float(previous_cash + (previous_quantities * current_prices).sum())
        expected_after_cost = round(equity_before_cost - row.transaction_cost, 6)
        current_positions = positions[positions["date"] == row.date].set_index("symbol")
        actual_after_cost = round(float(row.cash + current_positions["market_value"].sum()), 6)

        assert actual_after_cost == expected_after_cost
        previous_cash = float(row.cash)
        previous_quantities = current_positions["quantity"]


def test_weights_over_leverage_limit_fail_closed(tmp_path):
    fixture_copy = tmp_path / "data" / "fixtures" / "v2_proxy"
    fixture_copy.mkdir(parents=True)
    for path in FIXTURE_DIR.iterdir():
        if path.is_file():
            (fixture_copy / path.name).write_bytes(path.read_bytes())
    weights = fixture_copy / "synthetic_weights.csv"
    weights.write_text(
        "date,symbol,target_weight\n"
        "2020-01-02,AAA,0.90\n"
        "2020-01-02,BBB,0.90\n",
        encoding="utf-8",
    )
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["artifact_path"] = "data/fixtures/v2_proxy/synthetic_weights.csv"
    manifest["sha256"] = compute_sha256(weights)
    manifest["extra"]["weights"]["sha256"] = manifest["sha256"]
    manifest["row_count"] = 2
    manifest["date_range"] = {"start": "2020-01-02", "end": "2020-01-02"}
    manifest["extra"]["weights"]["row_count"] = 2
    manifest["extra"]["weights"]["date_range"] = {"start": "2020-01-02", "end": "2020-01-02"}
    (fixture_copy / "synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json")
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="max_gross_exposure"):
        SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)


def test_missing_price_rows_fail_closed(tmp_path):
    fixture_copy = tmp_path / "data" / "fixtures" / "v2_proxy"
    fixture_copy.mkdir(parents=True)
    for path in FIXTURE_DIR.iterdir():
        if path.is_file():
            (fixture_copy / path.name).write_bytes(path.read_bytes())
    prices = fixture_copy / "synthetic_prices.csv"
    prices.write_text(
        "date,symbol,close\n"
        "2020-01-02,AAA,100.00\n"
        "2020-01-02,BBB,50.00\n",
        encoding="utf-8",
    )
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["extra"]["prices"]["sha256"] = compute_sha256(prices)
    manifest["extra"]["prices"]["row_count"] = 2
    manifest["extra"]["prices"]["date_range"] = {"start": "2020-01-02", "end": "2020-01-02"}
    (fixture_copy / "synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json")
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="missing row"):
        SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)


def test_sparse_target_weights_fail_closed(tmp_path):
    fixture_copy = tmp_path / "data" / "fixtures" / "v2_proxy"
    fixture_copy.mkdir(parents=True)
    for path in FIXTURE_DIR.iterdir():
        if path.is_file():
            (fixture_copy / path.name).write_bytes(path.read_bytes())
    weights = fixture_copy / "synthetic_weights.csv"
    weights.write_text(
        "date,symbol,target_weight\n"
        "2020-01-02,AAA,0.50\n"
        "2020-01-02,BBB,0.50\n"
        "2020-01-03,AAA,0.40\n",
        encoding="utf-8",
    )
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    new_hash = compute_sha256(weights)
    manifest["artifact_path"] = "data/fixtures/v2_proxy/synthetic_weights.csv"
    manifest["sha256"] = new_hash
    manifest["extra"]["weights"]["sha256"] = new_hash
    manifest["row_count"] = 3
    manifest["extra"]["weights"]["row_count"] = 3
    (fixture_copy / "synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json")
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="target weights missing required date/symbol rows"):
        SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)
