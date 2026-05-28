from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from core import data_readiness_gate as gate


def _write_contracts(repo: Path) -> None:
    context = repo / "docs/context"
    context.mkdir(parents=True, exist_ok=True)
    (context / "data_artifact_taxonomy_current.json").write_text(
        json.dumps(
            {
                "schema_version": "data_artifact_taxonomy.v0",
                "allowed_boot_writes": [
                    gate.BOOT_STATUS_CURRENT_PATH.as_posix(),
                ],
                "artifacts": [
                    {
                        "path_glob": "data/processed/prices_tri.parquet",
                        "taxonomy": "canonical",
                        "required_for": ["portfolio_allocation.optimizer_current"],
                        "strict_missing_status": "FAIL",
                        "alternative_group": "local_price_source",
                    },
                    {
                        "path_glob": "data/processed/prices.parquet",
                        "taxonomy": "canonical",
                        "required_for": ["portfolio_allocation.optimizer_current"],
                        "strict_missing_status": "FAIL",
                        "alternative_group": "local_price_source",
                    },
                    {
                        "path_glob": "data/processed/tickers.parquet",
                        "taxonomy": "canonical",
                        "required_for": ["portfolio_allocation.optimizer_current"],
                        "strict_missing_status": "FAIL",
                    },
                    {
                        "path_glob": "data/processed/universe_r3000_daily.parquet",
                        "taxonomy": "canonical",
                        "required_for": ["portfolio_allocation.daily_replay"],
                        "strict_missing_status": "FAIL",
                    },
                    {
                        "path_glob": "data/universe/pinned_thesis_universe.yml",
                        "taxonomy": "canonical",
                        "required_for": ["portfolio_allocation.daily_replay"],
                        "strict_missing_status": "FAIL",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    (context / "portfolio_allocation_route_contract_v0.json").write_text(
        json.dumps(
            {
                "schema_version": "route_contract.v0",
                "route_id": "portfolio_allocation.strict.v0",
                "strict_invariants": {
                    "read_only": True,
                    "provider_calls_allowed": False,
                    "canonical_writes_allowed": False,
                    "broker_calls_allowed": False,
                    "allowed_boot_writes": [
                        gate.BOOT_STATUS_CURRENT_PATH.as_posix(),
                    ],
                },
                "subroutes": [],
            }
        ),
        encoding="utf-8",
    )


def _write_minimal_data(repo: Path, *, price_file: str = "prices_tri.parquet") -> None:
    processed = repo / "data/processed"
    processed.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-05", "2026-01-05"]),
            "permno": [101, 202, 101, 202],
            "ticker": ["AAA", "BBB", "AAA", "BBB"],
            "tri": [100.0, 50.0, 101.0, 49.5],
            "total_ret": [0.0, 0.0, 0.01, -0.01],
        }
    ).to_parquet(processed / price_file, index=False)
    pd.DataFrame({"permno": [101, 202], "ticker": ["AAA", "BBB"]}).to_parquet(
        processed / "tickers.parquet",
        index=False,
    )
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-02", "2026-01-05", "2026-01-05"]),
            "permno": [101, 202, 101, 202],
            "ticker": ["AAA", "BBB", "AAA", "BBB"],
        }
    ).to_parquet(processed / "universe_r3000_daily.parquet", index=False)
    universe = repo / "data/universe"
    universe.mkdir(parents=True, exist_ok=True)
    (universe / "pinned_thesis_universe.yml").write_text("tickers:\n  - AAA\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _registry(repo: Path) -> Path:
    path = repo / "data/registry"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _certified_artifact(path: str, repo: Path) -> dict[str, object]:
    artifact_path = repo / path
    return {
        "path": path,
        "sha256": _sha256(artifact_path),
        "size_bytes": artifact_path.stat().st_size,
    }


def _write_selected_endpoint_cert(
    repo: Path,
    *,
    expires_at_utc: str = "2099-01-01T00:00:00Z",
    artifacts: list[dict[str, object]] | None = None,
    selected_assets: list[str] | None = None,
    no_yahoo_patch: bool = False,
) -> Path:
    certified_artifacts = artifacts or [
        _certified_artifact("data/processed/prices_tri.parquet", repo),
        _certified_artifact("data/processed/tickers.parquet", repo),
    ]
    payload: dict[str, object] = {
        "schema_version": gate.SELECTED_ENDPOINT_CERT_SCHEMA_VERSION,
        "certification_id": "selected-endpoint-test-cert",
        "review_scope_id": "ROUND-20260527-DATA-READINESS-CERTIFICATION",
        "route_id": "portfolio_allocation.strict.v0",
        "issued_at_utc": "2026-05-27T00:00:00Z",
        "expires_at_utc": expires_at_utc,
        "origin": "durable_registry_certificate",
        "not_from_streamlit_session_state": True,
        "provider_calls_allowed": False,
        "repair_during_boot_allowed": False,
        "rebuild_during_boot_allowed": False,
        "selected_assets": selected_assets or ["AAA", "BBB"],
        "selected_endpoint_id": "portfolio-allocation-test-selected-assets",
        "latest_price_date": "2026-01-05",
        "artifacts": certified_artifacts,
    }
    if no_yahoo_patch:
        payload["yahoo_patch_policy"] = {
            "patch_required": False,
            "no_patch_certified": True,
            "reason": "test route uses local prices_tri/tickers only",
        }
    path = _registry(repo) / gate.SELECTED_ENDPOINT_CERT_PATH.name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_replay_selection_cert(
    repo: Path,
    *,
    origin: str = "durable_registry_certificate",
    not_from_streamlit_session_state: bool = True,
    expires_at_utc: str = "2099-01-01T00:00:00Z",
) -> Path:
    payload = {
        "schema_version": gate.REPLAY_SELECTION_CERT_SCHEMA_VERSION,
        "certification_id": "replay-selection-test-cert",
        "review_scope_id": "ROUND-20260527-DATA-READINESS-CERTIFICATION",
        "route_id": "portfolio_allocation.strict.v0",
        "issued_at_utc": "2026-05-27T00:00:00Z",
        "expires_at_utc": expires_at_utc,
        "origin": origin,
        "not_from_streamlit_session_state": not_from_streamlit_session_state,
        "provider_calls_allowed": False,
        "repair_during_boot_allowed": False,
        "rebuild_during_boot_allowed": False,
        "replay_selection_id": "portfolio-replay-test-selection",
        "method": "equal_weight",
        "selected_assets": ["AAA", "BBB"],
        "date_window": {"start": "2026-01-02", "end": "2026-01-05"},
        "artifacts": [
            _certified_artifact("data/processed/prices_tri.parquet", repo),
            _certified_artifact("data/processed/universe_r3000_daily.parquet", repo),
        ],
    }
    path = _registry(repo) / gate.REPLAY_SELECTION_CERT_PATH.name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _check_by_id(status: dict[str, object], check_id: str) -> dict[str, object]:
    checks = status["checks"]
    assert isinstance(checks, list)
    return next(check for check in checks if check["id"] == check_id)


def test_gate_reports_contracts_missing_as_fail(tmp_path: Path) -> None:
    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    assert status["overall_status"] == "FAIL"
    assert any("missing:" in blocker for blocker in status["summary"]["blockers"])


def test_gate_accepts_prices_parquet_as_local_price_source_fallback(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path, price_file="prices.parquet")

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    canonical = next(
        check for check in status["checks"] if check["id"] == "canonical_presence.portfolio_allocation"
    )
    price = next(
        check for check in status["checks"] if check["id"] == "price_return_integrity.selected_sample"
    )
    assert canonical["status"] != "FAIL"
    assert price["status"] == "PASS"
    assert price["metrics"]["price_source"] == "data/processed/prices.parquet"


def test_gate_fails_on_price_return_slot_swap(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-02", "2026-01-05"]),
            "permno": [101, 101],
            "tri": [0.01, -0.02],
            "total_ret": [100.0, 101.0],
        }
    ).to_parquet(tmp_path / "data/processed/prices_tri.parquet", index=False)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")
    price = next(
        check for check in status["checks"] if check["id"] == "price_return_integrity.selected_sample"
    )

    assert status["overall_status"] == "FAIL"
    assert price["status"] == "FAIL"
    assert "price_levels_median_below_one" in price["reason"]
    assert "return_values_outside_unit_bound" in price["reason"]


def test_provider_boundary_uses_ast_not_policy_literal_substrings(tmp_path: Path) -> None:
    module = tmp_path / "gate_policy.py"
    module.write_text(
        'TOKENS = ("import yfinance", "build_market_data_provider(")\n'
        "def ok():\n"
        "    return TOKENS\n",
        encoding="utf-8",
    )

    check = gate._check_provider_boundary(tmp_path, [module], mode="strict")

    assert check.status == "PASS"
    assert check.metrics == {"forbidden_hits": []}


def test_provider_boundary_rejects_forbidden_imports_and_calls(tmp_path: Path) -> None:
    module = tmp_path / "bad_gate.py"
    module.write_text(
        "import yfinance\n"
        "def bad():\n"
        "    return build_market_data_provider()\n",
        encoding="utf-8",
    )

    check = gate._check_provider_boundary(tmp_path, [module], mode="strict")

    assert check.status == "FAIL"
    assert any("import:yfinance" in hit for hit in check.metrics["forbidden_hits"])
    assert any("call:build_market_data_provider" in hit for hit in check.metrics["forbidden_hits"])


def test_data_readiness_gate_modules_do_not_import_provider_or_app_surfaces() -> None:
    repo = Path(__file__).resolve().parents[1]
    guarded = [
        repo / "core/data_readiness_gate.py",
        repo / "scripts/run_data_readiness_gate.py",
    ]
    forbidden_import_roots = {
        "dashboard",
        "streamlit",
        "strategies",
        "research",
        "yfinance",
        "alpaca",
        "data.providers.registry",
        "data.providers.yahoo_provider",
        "data.providers.alpaca_provider",
        "execution.broker_api",
        "scripts.audit_data_readiness",
    }
    forbidden_calls = {
        "build_market_data_provider",
        "download_recent_close_prices",
        "repair_stale_price_endpoints_with_live_overlay",
        "run_and_save_scan",
        "write_report_with_manifest",
        "run_audit",
    }
    hits: list[str] = []
    for path in guarded:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(repo).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    if any(imported == root or imported.startswith(f"{root}.") for root in forbidden_import_roots):
                        hits.append(f"{rel}:import:{imported}")
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if any(imported == root or imported.startswith(f"{root}.") for root in forbidden_import_roots):
                    hits.append(f"{rel}:from:{imported}")
            elif isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
                if name in forbidden_calls:
                    hits.append(f"{rel}:call:{name}")

    assert hits == []


def test_replay_output_stays_uncertified_without_durable_selection(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    assert status["route_readiness"]["portfolio_replay_selection_status"] == "UNCERTIFIED"
    assert status["route_readiness"]["portfolio_replay_output_status"] == "UNCERTIFIED_OUTPUT_NOT_CLAIMED"
    replay = next(
        check for check in status["checks"] if check["id"] == "replay_artifact.durable_selection_v0"
    )
    assert replay["status"] == "WARN"
    assert "outside Streamlit session state" in replay["reason"]


def test_missing_selected_endpoint_cert_warns_in_strict_mode(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    selected = _check_by_id(status, "freshness.selected_assets_v0")
    assert selected["status"] == "WARN"
    assert "missing" in selected["reason"]


def test_valid_selected_endpoint_cert_passes_selected_endpoint_check(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_selected_endpoint_cert(tmp_path, no_yahoo_patch=True)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    selected = _check_by_id(status, "freshness.selected_assets_v0")
    assert selected["status"] == "PASS"
    assert selected["metrics"]["selected_asset_endpoint_status"] == "CERTIFIED"


def test_stale_selected_endpoint_cert_warns_in_strict_mode(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_selected_endpoint_cert(tmp_path, expires_at_utc="2020-01-01T00:00:00Z")

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    selected = _check_by_id(status, "freshness.selected_assets_v0")
    assert selected["status"] == "WARN"
    assert "expired_cert" in selected["reason"]


def test_selected_endpoint_cert_bad_hash_fails_strict_mode(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    artifact = _certified_artifact("data/processed/prices_tri.parquet", tmp_path)
    artifact["sha256"] = "0" * 64
    _write_selected_endpoint_cert(tmp_path, artifacts=[artifact])

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    selected = _check_by_id(status, "freshness.selected_assets_v0")
    assert status["overall_status"] == "FAIL"
    assert selected["status"] == "FAIL"
    assert "sha256_mismatch" in selected["reason"]


def test_missing_replay_cert_warns_in_strict_mode(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    replay = _check_by_id(status, "replay_artifact.durable_selection_v0")
    assert replay["status"] == "WARN"
    assert "missing" in replay["reason"]


def test_valid_replay_cert_passes_replay_certification(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_replay_selection_cert(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    replay = _check_by_id(status, "replay_artifact.durable_selection_v0")
    assert replay["status"] == "PASS"
    assert replay["metrics"]["portfolio_replay_selection_status"] == "CERTIFIED"
    assert replay["metrics"]["portfolio_replay_output_status"] == "UNCERTIFIED_OUTPUT_NOT_CLAIMED"
    assert status["route_readiness"]["portfolio_replay_selection_status"] == "CERTIFIED"
    assert status["route_readiness"]["portfolio_replay_output_status"] == "UNCERTIFIED_OUTPUT_NOT_CLAIMED"


def test_replay_cert_sourced_from_streamlit_session_state_fails(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_replay_selection_cert(
        tmp_path,
        origin="streamlit.session_state",
        not_from_streamlit_session_state=False,
    )

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    replay = _check_by_id(status, "replay_artifact.durable_selection_v0")
    assert status["overall_status"] == "FAIL"
    assert replay["status"] == "FAIL"
    assert "streamlit_session_state_origin" in replay["reason"]


def test_missing_yahoo_patch_without_no_patch_cert_warns(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_selected_endpoint_cert(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    yahoo_patch = _check_by_id(status, "patch_policy.yahoo_patch_v0")
    assert yahoo_patch["status"] == "WARN"
    assert "no_patch_cert_missing" in yahoo_patch["reason"]


def test_missing_yahoo_patch_with_valid_no_patch_cert_has_no_yahoo_patch_warning(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_selected_endpoint_cert(tmp_path, no_yahoo_patch=True)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    yahoo_patch = _check_by_id(status, "patch_policy.yahoo_patch_v0")
    assert yahoo_patch["status"] == "PASS"
    assert "no_patch_certified" in yahoo_patch["reason"]
    assert not any("yahoo_patch" in warning for warning in status["summary"]["warnings"])


def test_certification_validation_is_read_only_and_leaves_no_tmp_residue(tmp_path: Path) -> None:
    _write_contracts(tmp_path)
    _write_minimal_data(tmp_path)
    _write_selected_endpoint_cert(tmp_path, no_yahoo_patch=True)
    _write_replay_selection_cert(tmp_path)
    before = gate.capture_boot_write_snapshot(tmp_path)

    status = gate.run_data_readiness_gate(tmp_path, mode="strict")

    after = gate.capture_boot_write_snapshot(tmp_path)
    diff = gate.diff_boot_write_snapshot(before, after, repo_root=tmp_path)
    assert status["overall_status"] == "PASS"
    assert diff["status"] == "PASS"
    assert diff["changed"] == []
    assert list((tmp_path / "data/registry").glob("*.tmp")) == []


def test_canonical_context_files_are_the_only_contract_locations() -> None:
    repo = Path(__file__).resolve().parents[1]

    assert (repo / "docs/architecture/data_readiness_gate_v0.md").exists()
    assert (repo / "docs/context/data_artifact_taxonomy_current.json").exists()
    assert (repo / "docs/context/portfolio_allocation_route_contract_v0.json").exists()
    assert not (repo / "data_readiness_gate_v0_implementation_brief.md").exists()
    assert not (repo / "data_artifact_taxonomy_current.json").exists()
    assert not (repo / "portfolio_allocation_route_contract_v0.json").exists()
