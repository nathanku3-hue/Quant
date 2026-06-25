from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from data.provenance import compute_sha256
from data.provenance import SOURCE_QUALITY_NON_CANONICAL
from data.provenance import utc_now_iso
from v2_discovery.fast_sim.fixtures import load_synthetic_proxy_fixture
from v2_discovery.fast_sim.ledger import validate_synthetic_ledger_output
from v2_discovery.fast_sim.schemas import PROXY_ENGINE_NAME
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.simulator import SYNTHETIC_PROXY_ENGINE_VERSION
from v2_discovery.fast_sim.simulator import SyntheticFastProxySimulator
from v2_discovery.fast_sim.validation import validate_manifest_reconciles
from v2_discovery.registry import CandidateRegistry
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus


FIXTURE_DIR = Path("data/fixtures/v2_proxy")
MANIFEST_URI = FIXTURE_DIR / "synthetic_manifest.json"


def _copy_fixture_tree(tmp_path: Path) -> Path:
    fixture_copy = tmp_path / "data" / "fixtures" / "v2_proxy"
    fixture_copy.mkdir(parents=True)
    for path in FIXTURE_DIR.iterdir():
        if path.is_file():
            (fixture_copy / path.name).write_bytes(path.read_bytes())
    return fixture_copy


def _write_manifest(fixture_copy: Path, manifest: dict) -> None:
    (fixture_copy / "synthetic_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _run_fixture_copy(tmp_path: Path, fixture_copy: Path):
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(
        manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json",
        data_snapshot={"dataset": "synthetic_v2_proxy_fixture_copy", "asof": "2026-05-09"},
    )
    event = registry.register_candidate(candidate, actor="pytest")
    return SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)


def _prepare_mutated_fixture(
    tmp_path: Path,
    file_name: str,
    text: str,
    manifest_mutator=None,
) -> Path:
    fixture_copy = _copy_fixture_tree(tmp_path)
    target = fixture_copy / file_name
    target.write_text(text, encoding="utf-8")
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    if file_name == "synthetic_prices.csv":
        manifest["extra"]["prices"]["sha256"] = compute_sha256(target)
    elif file_name == "synthetic_weights.csv":
        new_hash = compute_sha256(target)
        manifest["artifact_path"] = "data/fixtures/v2_proxy/synthetic_weights.csv"
        manifest["sha256"] = new_hash
        manifest["extra"]["weights"]["sha256"] = new_hash
    if manifest_mutator is not None:
        manifest_mutator(manifest)
    _write_manifest(fixture_copy, manifest)
    return fixture_copy


def _registry(tmp_path: Path) -> CandidateRegistry:
    return CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=Path.cwd(),
    )


def _candidate(**overrides) -> CandidateSpec:
    payload = {
        "candidate_id": "PH65_G1_SYNTHETIC_PROXY_001",
        "family_id": "SYNTHETIC_FAST_PROXY_MECHANICS",
        "hypothesis": "Synthetic accounting mechanics fixture only; no alpha.",
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
        "code_ref": "phase65-g1-test-suite",
        "status": CandidateStatus.GENERATED,
    }
    payload.update(overrides)
    return CandidateSpec(**payload)


def _registered_spec(tmp_path: Path, **candidate_overrides) -> tuple[CandidateRegistry, ProxyRunSpec]:
    registry = _registry(tmp_path)
    candidate = _candidate(**candidate_overrides)
    event = registry.register_candidate(candidate, actor="pytest")
    return registry, _proxy_spec(candidate, event.event_id)


def _proxy_spec(candidate: CandidateSpec, registry_event_id: str, **overrides) -> ProxyRunSpec:
    payload = {
        "proxy_run_id": "PH65_G1_PROXY_RUN_001",
        "candidate_id": candidate.candidate_id,
        "registry_event_id": registry_event_id,
        "manifest_uri": candidate.manifest_uri,
        "source_quality": candidate.source_quality,
        "data_snapshot": dict(candidate.data_snapshot),
        "code_ref": "phase65-g1-test-suite",
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


def test_synthetic_fixture_manifest_required(tmp_path):
    with pytest.raises(ProxyBoundaryError, match="manifest"):
        load_synthetic_proxy_fixture("", repo_root=tmp_path)


def test_synthetic_fixture_hash_mismatch_fails(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["extra"]["prices"]["sha256"] = "0" * 64
    _write_manifest(fixture_copy, manifest)
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(
        manifest_uri="data/fixtures/v2_proxy/synthetic_manifest.json",
        data_snapshot={"dataset": "synthetic_v2_proxy_fixture_copy", "asof": "2026-05-09"},
    )
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="prices hash mismatch"):
        SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)


def test_prices_nan_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,nan\n2020-01-02,BBB,50.00\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic prices.*close.*bad row count=1.*nan"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_prices_pos_inf_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,inf\n2020-01-02,BBB,50.00\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic prices.*close.*bad row count=1.*\+inf"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_prices_neg_inf_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,-inf\n2020-01-02,BBB,50.00\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic prices.*close.*bad row count=1.*-inf"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_weights_nan_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_weights.csv",
        "date,symbol,target_weight\n2020-01-02,AAA,nan\n2020-01-02,BBB,0.50\n",
        lambda manifest: manifest.update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        )
        or manifest["extra"]["weights"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic weights.*target_weight.*bad row count=1.*nan"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_weights_inf_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_weights.csv",
        "date,symbol,target_weight\n2020-01-02,AAA,inf\n2020-01-02,BBB,0.50\n",
        lambda manifest: manifest.update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        )
        or manifest["extra"]["weights"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic weights.*target_weight.*bad row count=1.*\+inf"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_prices_missing_symbol_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,,100.00\n2020-01-02,BBB,50.00\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic prices.*symbol.*bad row count=1.*nan"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_weights_missing_symbol_rejected(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_weights.csv",
        "date,symbol,target_weight\n2020-01-02,,0.50\n2020-01-02,BBB,0.50\n",
        lambda manifest: manifest.update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        )
        or manifest["extra"]["weights"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"synthetic weights.*symbol.*bad row count=1.*nan"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_cost_nan_rejected(tmp_path):
    registry = _registry(tmp_path)
    candidate = _candidate()
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match=r"cost_model.total_cost_bps.*bad value class: nan"):
        _proxy_spec(
            candidate,
            event.event_id,
            cost_model={
                "initial_cash": 100000.0,
                "total_cost_bps": float("nan"),
                "max_gross_exposure": 1.0,
            },
        )


def test_cost_inf_rejected(tmp_path):
    registry = _registry(tmp_path)
    candidate = _candidate()
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match=r"cost_model.initial_cash.*bad value class: \+inf"):
        _proxy_spec(
            candidate,
            event.event_id,
            cost_model={
                "initial_cash": float("inf"),
                "total_cost_bps": 10.0,
                "max_gross_exposure": 1.0,
            },
        )


def test_output_ledger_non_finite_rejected():
    positions = pd.DataFrame(
        [
            {"date": "2020-01-02", "symbol": "AAA", "quantity": 1.0, "market_value": 100.0},
        ]
    )
    ledger = pd.DataFrame(
        [
            {
                "date": "2020-01-02",
                "cash": 0.0,
                "turnover": 1.0,
                "transaction_cost": float("inf"),
                "gross_exposure": 1.0,
                "net_exposure": 1.0,
            }
        ]
    )

    with pytest.raises(
        ProxyBoundaryError,
        match=r"synthetic output ledger.*transaction_cost.*bad row count=1.*\+inf",
    ):
        validate_synthetic_ledger_output(positions, ledger)


def test_manifest_row_count_mismatch_rejected(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["extra"]["prices"]["row_count"] = 999
    _write_manifest(fixture_copy, manifest)

    with pytest.raises(ProxyBoundaryError, match="synthetic prices: manifest row_count mismatch"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_manifest_date_range_start_mismatch_rejected(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["extra"]["prices"]["date_range"]["start"] = "1999-01-01"
    _write_manifest(fixture_copy, manifest)

    with pytest.raises(ProxyBoundaryError, match="synthetic prices: manifest date_range.start mismatch"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_manifest_date_range_end_mismatch_rejected(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    manifest = json.loads((fixture_copy / "synthetic_manifest.json").read_text(encoding="utf-8"))
    manifest["extra"]["weights"]["date_range"]["end"] = "1999-01-01"
    _write_manifest(fixture_copy, manifest)

    with pytest.raises(ProxyBoundaryError, match="synthetic weights: manifest date_range.end mismatch"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_manifest_hash_mismatch_still_rejected(tmp_path):
    fixture_copy = _copy_fixture_tree(tmp_path)
    prices = fixture_copy / "synthetic_prices.csv"
    prices.write_text(
        "date,symbol,close\n"
        "2020-01-02,AAA,100.00\n"
        "2020-01-02,BBB,50.00\n"
        "2020-01-03,AAA,111.00\n"
        "2020-01-03,BBB,55.00\n",
        encoding="utf-8",
    )

    with pytest.raises(ProxyBoundaryError, match="prices hash mismatch"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_proxy_metadata_non_finite_rejected(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    payload = spec.to_dict()
    payload["data_snapshot"] = {"dataset": "synthetic_fixture", "asof": float("nan")}

    with pytest.raises(ProxyBoundaryError, match=r"data_snapshot.asof.*bad value class: nan"):
        ProxyRunSpec(**payload)


def test_reviewer_c_non_finite_fixture_block_regression(tmp_path):
    fixture_copy = _prepare_mutated_fixture(
        tmp_path,
        "synthetic_prices.csv",
        "date,symbol,close\n2020-01-02,AAA,100.00\n2020-01-02,BBB,-inf\n",
        lambda manifest: manifest["extra"]["prices"].update(
            {"row_count": 2, "date_range": {"start": "2020-01-02", "end": "2020-01-02"}}
        ),
    )

    with pytest.raises(ProxyBoundaryError, match=r"bad value class: -inf"):
        _run_fixture_copy(tmp_path, fixture_copy)


def test_real_market_data_path_rejected(tmp_path):
    real_dir = tmp_path / "real_market"
    real_dir.mkdir()
    weights = real_dir / "weights.csv"
    weights.write_bytes(FIXTURE_DIR.joinpath("synthetic_weights.csv").read_bytes())
    manifest = json.loads(MANIFEST_URI.read_text(encoding="utf-8"))
    manifest["artifact_path"] = str(weights)
    manifest["provider"] = "wrds"
    manifest["provider_feed"] = "crsp_daily"
    manifest["license_scope"] = "canonical_research"
    manifest["sha256"] = compute_sha256(weights)
    manifest_path = real_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    registry = CandidateRegistry(
        tmp_path / "candidate_events.jsonl",
        snapshot_path=tmp_path / "candidate_snapshot.json",
        repo_root=tmp_path,
    )
    candidate = _candidate(manifest_uri=str(manifest_path))
    event = registry.register_candidate(candidate, actor="pytest")

    with pytest.raises(ProxyBoundaryError, match="non-fixture data paths|real market data providers"):
        SyntheticFastProxySimulator().run(_proxy_spec(candidate, event.event_id), registry=registry)


def test_proxy_requires_registered_candidate(tmp_path):
    registry = _registry(tmp_path)
    candidate = _candidate()
    spec = _proxy_spec(candidate, "missing-registry-event")

    with pytest.raises(ProxyBoundaryError, match="registered candidate"):
        SyntheticFastProxySimulator().run(spec, registry=registry)


def test_transaction_cost_applied(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)

    assert output.ledger["transaction_cost"].tolist() == [100.0, 21.978]
    assert output.ledger["turnover"].tolist() == [1.0, 0.2]


def test_positions_cash_ledger_match_golden_file(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)
    expected_ledger = pd.read_csv(FIXTURE_DIR / "expected_ledger.csv")
    expected_positions = pd.read_csv(FIXTURE_DIR / "expected_positions.csv")

    assert_frame_equal(output.ledger, expected_ledger, check_exact=False, atol=0.000001)
    assert_frame_equal(output.positions, expected_positions, check_exact=False, atol=0.000001)


def test_golden_fixture_metadata_reconciles():
    manifest = json.loads(MANIFEST_URI.read_text(encoding="utf-8"))
    extra = manifest["extra"]
    validate_manifest_reconciles(
        pd.read_csv(FIXTURE_DIR / "expected_ledger.csv"),
        extra["expected_ledger"],
        "expected ledger",
        file_path=FIXTURE_DIR / "expected_ledger.csv",
    )
    validate_manifest_reconciles(
        pd.read_csv(FIXTURE_DIR / "expected_positions.csv"),
        extra["expected_positions"],
        "expected positions",
        file_path=FIXTURE_DIR / "expected_positions.csv",
    )
    expected_result = json.loads((FIXTURE_DIR / "expected_result.json").read_text(encoding="utf-8"))
    assert extra["expected_result"]["row_count"] == expected_result["row_count"]
    assert extra["expected_result"]["date_range"] == expected_result["date_range"]
    assert extra["expected_result"]["sha256"] == compute_sha256(FIXTURE_DIR / "expected_result.json")


def test_proxy_result_still_not_promotion_ready(tmp_path):
    registry, spec = _registered_spec(tmp_path)
    output = SyntheticFastProxySimulator().run(spec, registry=registry)

    assert output.proxy_result.boundary_verdict == ProxyBoundaryVerdict.TIER2_BLOCKED
    assert output.proxy_result.promotion_ready is False
    assert output.proxy_result.canonical_engine_required is True
    assert output.result["promotion_ready"] is False
    assert output.result["canonical_engine_required"] is True


def test_repeated_run_is_deterministic(tmp_path):
    registry_one, spec_one = _registered_spec(tmp_path / "one")
    registry_two, spec_two = _registered_spec(tmp_path / "two")

    first = SyntheticFastProxySimulator().run(spec_one, registry=registry_one)
    second = SyntheticFastProxySimulator().run(spec_two, registry=registry_two)

    assert_frame_equal(first.ledger, second.ledger, check_exact=True)
    assert_frame_equal(first.positions, second.positions, check_exact=True)
    expected_result = json.loads((FIXTURE_DIR / "expected_result.json").read_text(encoding="utf-8"))
    result_without_event = {
        key: value for key, value in first.result.items() if key != "registry_event_id"
    }
    assert result_without_event == expected_result
