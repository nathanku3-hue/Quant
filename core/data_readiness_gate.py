from __future__ import annotations

import ast
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd
import pyarrow.parquet as pq

from core.boot_status import (
    BOOT_STATUS_CURRENT_PATH,
    BootContextFlags,
    BootStatus,
    BootStatusValidationError,
    ReadinessCheck,
    make_boot_status,
)


SCHEMA_VERSION = "data_readiness_gate.v0"
DEFAULT_TAXONOMY_PATH = Path("docs/context/data_artifact_taxonomy_current.json")
DEFAULT_ROUTE_CONTRACT_PATH = Path("docs/context/portfolio_allocation_route_contract_v0.json")
DEFAULT_STATUS_PATH = BOOT_STATUS_CURRENT_PATH
ALLOWED_BOOT_WRITES = {DEFAULT_STATUS_PATH.as_posix()}
BOOT_WRITE_GUARD_ROOTS = (
    "app.py",
    "launch.py",
    "core",
    "scripts",
    "strategies",
    "views",
    "tests",
    "runtime",
    "docs/architecture",
    "docs/context",
    "docs/saw_reports",
    "data/processed",
    "data/runtime_cache",
    "data/candidate_cards",
    "data/discovery",
    "data/registry",
)

PROVIDER_FORBIDDEN_IMPORT_ROOTS = (
    "yfinance",
    "alpaca",
    "data.providers.registry",
    "data.providers.yahoo_provider",
    "data.providers.alpaca_provider",
    "execution.broker_api",
)
PROVIDER_FORBIDDEN_CALLS = (
    "build_market_data_provider",
    "download_recent_close_prices",
    "repair_stale_price_endpoints_with_live_overlay",
    "run_and_save_scan",
)


@dataclass(frozen=True)
class GateCheck:
    id: str
    category: str
    status: str
    planning: str
    strict: str
    repair_policy: str
    inputs: tuple[str, ...]
    evidence: tuple[str, ...]
    reason: str
    metrics: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "category": self.category,
            "status": self.status,
            "mode_effect": {"planning": self.planning, "strict": self.strict},
            "repair_policy": self.repair_policy,
            "inputs": list(self.inputs),
            "evidence": list(self.evidence),
            "reason": self.reason,
        }
        if self.metrics is not None:
            payload["metrics"] = dict(self.metrics)
        return payload


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_path(repo_root: Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return repo_root / candidate


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"missing:{path.as_posix()}"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"json_decode_error:{exc}"
    if not isinstance(payload, dict):
        return None, "json_payload_not_object"
    return payload, None


def _status_from_effect(mode: str, planning: str, strict: str) -> str:
    return strict if mode == "strict" else planning


def _check_contract_json(
    repo_root: Path,
    *,
    path: Path,
    expected_schema_version: str,
    check_id: str,
    mode: str,
) -> GateCheck:
    payload, error = _load_json(path)
    rel = _rel(path, repo_root)
    if error:
        return GateCheck(
            id=check_id,
            category="taxonomy" if "taxonomy" in rel else "route_contract",
            status="FAIL",
            planning="FAIL",
            strict="FAIL",
            repair_policy="manual_approval",
            inputs=(rel,),
            evidence=(),
            reason=error,
        )
    schema_version = str(payload.get("schema_version", ""))
    if schema_version != expected_schema_version:
        return GateCheck(
            id=check_id,
            category="taxonomy" if "taxonomy" in rel else "route_contract",
            status="FAIL",
            planning="FAIL",
            strict="FAIL",
            repair_policy="manual_approval",
            inputs=(rel,),
            evidence=(),
            reason=f"schema_version_mismatch:{schema_version}",
        )
    return GateCheck(
        id=check_id,
        category="taxonomy" if "taxonomy" in rel else "route_contract",
        status="PASS",
        planning="PASS",
        strict="PASS",
        repair_policy="manual_approval",
        inputs=(rel,),
        evidence=(rel,),
        reason="contract JSON exists and schema_version matches",
        metrics={"mode_status": _status_from_effect(mode, "PASS", "PASS")},
    )


def _taxonomy_artifacts(repo_root: Path, taxonomy_path: Path) -> list[dict[str, Any]]:
    payload, error = _load_json(taxonomy_path)
    if error or not payload:
        return []
    artifacts = payload.get("artifacts", [])
    return [item for item in artifacts if isinstance(item, dict)]


def _artifact_exists(repo_root: Path, path_glob: str) -> bool:
    if "*" in path_glob:
        return any(repo_root.glob(path_glob))
    return _repo_path(repo_root, path_glob).exists()


def _check_canonical_presence(repo_root: Path, artifacts: Sequence[Mapping[str, Any]], mode: str) -> GateCheck:
    required_missing: list[str] = []
    optional_missing: list[str] = []
    checked: list[str] = []
    alternative_groups: dict[str, list[Mapping[str, Any]]] = {}
    for artifact in artifacts:
        taxonomy = str(artifact.get("taxonomy", ""))
        path_glob = str(artifact.get("path_glob", ""))
        if not path_glob or taxonomy not in {"canonical", "derived"}:
            continue
        required_for = artifact.get("required_for", [])
        if not isinstance(required_for, list) or not any(str(item).startswith("portfolio_allocation") for item in required_for):
            continue
        alternative_group = str(artifact.get("alternative_group", "")).strip()
        if alternative_group:
            alternative_groups.setdefault(alternative_group, []).append(artifact)
            continue
        exists = _artifact_exists(repo_root, path_glob)
        checked.append(path_glob)
        strict_missing = str(artifact.get("strict_missing_status", "WARN")).upper()
        if not exists and strict_missing == "FAIL":
            required_missing.append(path_glob)
        elif not exists:
            optional_missing.append(path_glob)
    for group_name, group_artifacts in sorted(alternative_groups.items()):
        group_paths = [str(item.get("path_glob", "")) for item in group_artifacts if item.get("path_glob")]
        checked.extend(group_paths)
        if any(_artifact_exists(repo_root, path_glob) for path_glob in group_paths):
            continue
        strict_missing = "FAIL" if any(str(item.get("strict_missing_status", "WARN")).upper() == "FAIL" for item in group_artifacts) else "WARN"
        missing_label = f"{group_name}:one_of({','.join(group_paths)})"
        if strict_missing == "FAIL":
            required_missing.append(missing_label)
        else:
            optional_missing.append(missing_label)
    planning = "WARN" if required_missing or optional_missing else "PASS"
    strict = "FAIL" if required_missing else "WARN" if optional_missing else "PASS"
    status = _status_from_effect(mode, planning, strict)
    reason = "canonical route artifacts present"
    if required_missing:
        reason = "missing strict-required artifacts"
    elif optional_missing:
        reason = "missing optional or route-conditional artifacts"
    return GateCheck(
        id="canonical_presence.portfolio_allocation",
        category="canonical_presence",
        status=status,
        planning=planning,
        strict=strict,
        repair_policy="manual_approval",
        inputs=tuple(checked),
        evidence=(),
        reason=reason,
        metrics={
            "required_missing": required_missing,
            "optional_missing": optional_missing,
            "checked_count": len(checked),
        },
    )


def _read_parquet_head(path: Path, columns: Sequence[str] | None = None, limit: int = 2000) -> pd.DataFrame:
    try:
        parquet = pq.ParquetFile(path)
        batch = next(parquet.iter_batches(batch_size=limit, columns=list(columns) if columns else None))
        return batch.to_pandas()
    except StopIteration:
        return pd.DataFrame()
    except Exception:
        return pd.read_parquet(path, columns=list(columns) if columns else None).head(limit)


def _resolve_price_source(repo_root: Path) -> tuple[Path | None, str]:
    for relative in ("data/processed/prices_tri.parquet", "data/processed/prices.parquet"):
        candidate = repo_root / relative
        if candidate.exists():
            return candidate, relative
    return None, "data/processed/prices_tri.parquet OR data/processed/prices.parquet"


def _check_price_return_sanity(repo_root: Path, mode: str) -> GateCheck:
    price_path, price_rel = _resolve_price_source(repo_root)
    if price_path is None:
        price_rel = "data/processed/prices_tri.parquet OR data/processed/prices.parquet"
        missing_inputs = ("data/processed/prices_tri.parquet", "data/processed/prices.parquet")
    else:
        missing_inputs = (price_rel,)
    if price_path is None:
        return GateCheck(
            id="price_return_integrity.selected_sample",
            category="price_return_integrity",
            status=_status_from_effect(mode, "WARN", "FAIL"),
            planning="WARN",
            strict="FAIL",
            repair_policy="manual_approval",
            inputs=missing_inputs,
            evidence=(),
            reason=f"price source missing:{price_rel}",
        )
    try:
        sample = _read_parquet_head(price_path, limit=2000)
    except Exception as exc:
        return GateCheck(
            id="price_return_integrity.selected_sample",
            category="price_return_integrity",
            status=_status_from_effect(mode, "WARN", "FAIL"),
            planning="WARN",
            strict="FAIL",
            repair_policy="manual_approval",
            inputs=(price_rel,),
            evidence=(),
            reason=f"price source unreadable:{exc}",
        )
    failures: list[str] = []
    if sample.empty:
        failures.append("empty_price_sample")
    if sample.columns.duplicated().any():
        failures.append("duplicate_columns")
    date_col = "date" if "date" in sample.columns else None
    if date_col:
        dates = pd.to_datetime(sample[date_col], errors="coerce")
        if dates.isna().all():
            failures.append("date_column_unparseable")
        elif "permno" in sample.columns:
            if sample[[date_col, "permno"]].duplicated().any():
                failures.append("duplicate_date_permno_in_sample")
        elif dates.dropna().duplicated().any():
            failures.append("duplicate_dates_in_sample")
    price_like_columns = [
        column
        for column in sample.select_dtypes(include="number").columns
        if str(column) in {"tri", "adj_close", "legacy_adj_close", "raw_close"}
        or str(column).lower().endswith(("price", "_close"))
    ]
    return_like_columns = [
        column
        for column in sample.select_dtypes(include="number").columns
        if str(column) in {"total_ret", "return", "asset_return", "portfolio_return"}
        or str(column).lower().endswith(("_ret", "_return"))
    ]
    if price_like_columns:
        numeric = sample[price_like_columns]
    else:
        numeric = sample.select_dtypes(include="number").drop(columns=["permno"], errors="ignore")
    if numeric.empty:
        failures.append("no_numeric_price_columns")
    else:
        values = numeric.to_numpy()
        finite_ratio = float(pd.notna(numeric).sum().sum()) / float(numeric.size) if numeric.size else 0.0
        if finite_ratio <= 0.0:
            failures.append("no_finite_numeric_values")
        numeric_stack = pd.Series(numeric.to_numpy().ravel()).dropna()
        if not numeric_stack.empty and (numeric_stack < 0).mean() > 0.25:
            failures.append("price_values_look_return_like_or_negative")
        if values.size and pd.Series(values.ravel()).dropna().abs().median() < 1:
            failures.append("price_levels_median_below_one")
    if return_like_columns:
        returns = pd.Series(sample[return_like_columns].to_numpy().ravel()).dropna()
        if not returns.empty and (returns.abs() > 1.0).any():
            failures.append("return_values_outside_unit_bound")
    planning = "WARN" if failures else "PASS"
    strict = "FAIL" if failures else "PASS"
    return GateCheck(
        id="price_return_integrity.selected_sample",
        category="price_return_integrity",
        status=_status_from_effect(mode, planning, strict),
        planning=planning,
        strict=strict,
        repair_policy="manual_approval",
        inputs=(price_rel,),
        evidence=(),
        reason=";".join(failures) if failures else "price sample passes v0 level sanity",
        metrics={
            "price_source": price_rel,
            "rows_sampled": int(len(sample)),
            "columns_sampled": int(len(sample.columns)),
        },
    )


def _check_pit_and_pinned(repo_root: Path, mode: str) -> GateCheck:
    pit_path = repo_root / "data/processed/universe_r3000_daily.parquet"
    pinned_path = repo_root / "data/universe/pinned_thesis_universe.yml"
    failures: list[str] = []
    warnings: list[str] = []
    if not pit_path.exists():
        failures.append("missing_pit_universe")
    else:
        try:
            pit = _read_parquet_head(pit_path, limit=5000)
            if pit.empty:
                failures.append("empty_pit_universe")
            required_cols = {"date", "permno"}
            missing_cols = sorted(required_cols - set(str(col) for col in pit.columns))
            if missing_cols:
                failures.append(f"pit_missing_columns:{','.join(missing_cols)}")
            elif pit[["date", "permno"]].duplicated().any():
                failures.append("duplicate_pit_date_permno_sample")
        except Exception as exc:
            failures.append(f"pit_unreadable:{exc}")
    if not pinned_path.exists():
        failures.append("missing_pinned_manifest")
    elif pinned_path.stat().st_size <= 0:
        failures.append("empty_pinned_manifest")
    planning = "WARN" if failures or warnings else "PASS"
    strict = "FAIL" if failures else "WARN" if warnings else "PASS"
    return GateCheck(
        id="pit.pinned_universe_v0",
        category="pit",
        status=_status_from_effect(mode, planning, strict),
        planning=planning,
        strict=strict,
        repair_policy="manual_approval",
        inputs=("data/processed/universe_r3000_daily.parquet", "data/universe/pinned_thesis_universe.yml"),
        evidence=(),
        reason=";".join(failures or warnings) if failures or warnings else "PIT and pinned manifest probes pass",
    )


def _provider_boundary_hits(repo_root: Path, module_paths: Sequence[Path]) -> list[str]:
    hits: list[str] = []
    for path in module_paths:
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            hits.append(f"{_rel(path, repo_root)}:syntax_error:{exc.lineno}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name
                    if any(imported == root or imported.startswith(f"{root}.") for root in PROVIDER_FORBIDDEN_IMPORT_ROOTS):
                        hits.append(f"{_rel(path, repo_root)}:import:{imported}")
            elif isinstance(node, ast.ImportFrom):
                imported = node.module or ""
                if any(imported == root or imported.startswith(f"{root}.") for root in PROVIDER_FORBIDDEN_IMPORT_ROOTS):
                    hits.append(f"{_rel(path, repo_root)}:from:{imported}")
            elif isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in PROVIDER_FORBIDDEN_CALLS:
                    hits.append(f"{_rel(path, repo_root)}:call:{name}")
    return sorted(set(hits))


def _check_provider_boundary(repo_root: Path, module_paths: Sequence[Path], mode: str) -> GateCheck:
    hits = _provider_boundary_hits(repo_root, module_paths)
    status = "FAIL" if hits else "PASS"
    return GateCheck(
        id="provider_boundary.boot_gate_no_live_imports",
        category="provider_boundary",
        status=status,
        planning=status,
        strict=status,
        repair_policy="never_during_boot",
        inputs=tuple(_rel(path, repo_root) for path in module_paths),
        evidence=(),
        reason="forbidden provider/live tokens found" if hits else "boot gate modules avoid provider/live calls",
        metrics={"forbidden_hits": hits},
    )


def _check_replay_certification(mode: str) -> GateCheck:
    return GateCheck(
        id="replay_artifact.durable_selection_v0",
        category="replay_artifact",
        status="WARN",
        planning="WARN",
        strict="WARN",
        repair_policy="never_during_boot",
        inputs=("PortfolioReplaySelection",),
        evidence=(),
        reason="No durable PortfolioReplaySelection is certified outside Streamlit session state in v0; replay output remains UNCERTIFIED.",
        metrics={"portfolio_replay_output_status": "UNCERTIFIED"},
    )


def _check_selected_endpoint_freshness_v0(mode: str) -> GateCheck:
    return GateCheck(
        id="freshness.selected_assets_v0",
        category="freshness",
        status="WARN",
        planning="WARN",
        strict="WARN",
        repair_policy="never_during_boot",
        inputs=("durable PortfolioAllocation route request",),
        evidence=(),
        reason=(
            "No durable selected-asset request is available to the v0 gate; selected endpoint freshness "
            "remains UNCERTIFIED rather than repaired or inferred from Streamlit session state."
        ),
        metrics={"selected_asset_endpoint_status": "UNCERTIFIED"},
    )


def _status_weight(status: str) -> int:
    return {"PASS": 0, "WARN": 1, "DEFER": 1, "FAIL": 2}.get(str(status).upper(), 2)


def _combine_statuses(statuses: Iterable[str]) -> str:
    normalized = [str(status).upper() for status in statuses]
    if not normalized:
        return "PASS"
    return max(normalized, key=_status_weight)


def _mode_effect(check: GateCheck, mode: str) -> str:
    return check.strict if mode == "strict" else check.planning


def _route_readiness(checks: Sequence[GateCheck], mode: str) -> dict[str, Any]:
    by_id = {check.id: check for check in checks}

    def combine(ids: Sequence[str]) -> str:
        return _combine_statuses(_mode_effect(by_id[item], mode) for item in ids if item in by_id)

    local_ids = (
        "taxonomy.data_artifact_taxonomy_current",
        "route_contract.portfolio_allocation_strict_v0",
        "canonical_presence.portfolio_allocation",
        "price_return_integrity.selected_sample",
        "pit.pinned_universe_v0",
        "provider_boundary.boot_gate_no_live_imports",
    )
    optimizer_ids = (
        "taxonomy.data_artifact_taxonomy_current",
        "route_contract.portfolio_allocation_strict_v0",
        "canonical_presence.portfolio_allocation",
        "price_return_integrity.selected_sample",
        "freshness.selected_assets_v0",
        "provider_boundary.boot_gate_no_live_imports",
    )
    replay_ids = (
        "taxonomy.data_artifact_taxonomy_current",
        "route_contract.portfolio_allocation_strict_v0",
        "canonical_presence.portfolio_allocation",
        "price_return_integrity.selected_sample",
        "pit.pinned_universe_v0",
        "replay_artifact.durable_selection_v0",
        "provider_boundary.boot_gate_no_live_imports",
    )
    return {
        "portfolio_allocation.local_data_prerequisites": combine(local_ids),
        "portfolio_allocation.optimizer_current": combine(optimizer_ids),
        "portfolio_allocation.daily_replay": combine(replay_ids),
        "portfolio_allocation.benchmarks": "WARN",
        "portfolio_replay_output_status": "UNCERTIFIED",
        "notes": [
            "Optimizer/replay output certification is route-conditional.",
            "No durable PortfolioReplaySelection is inspected in v0.",
        ],
    }


def run_data_readiness_gate(
    repo_root: str | Path = ".",
    *,
    mode: str = "strict",
    taxonomy_path: str | Path = DEFAULT_TAXONOMY_PATH,
    route_contract_path: str | Path = DEFAULT_ROUTE_CONTRACT_PATH,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    mode = "planning" if mode == "planning" else "strict"
    taxonomy = _repo_path(repo, taxonomy_path)
    route = _repo_path(repo, route_contract_path)
    checks: list[GateCheck] = [
        _check_contract_json(
            repo,
            path=taxonomy,
            expected_schema_version="data_artifact_taxonomy.v0",
            check_id="taxonomy.data_artifact_taxonomy_current",
            mode=mode,
        ),
        _check_contract_json(
            repo,
            path=route,
            expected_schema_version="route_contract.v0",
            check_id="route_contract.portfolio_allocation_strict_v0",
            mode=mode,
        ),
    ]
    artifacts = _taxonomy_artifacts(repo, taxonomy)
    checks.extend(
        [
            _check_canonical_presence(repo, artifacts, mode),
            _check_price_return_sanity(repo, mode),
            _check_pit_and_pinned(repo, mode),
            _check_selected_endpoint_freshness_v0(mode),
            _check_provider_boundary(
                repo,
                (
                    repo / "core/boot_status.py",
                    repo / "core/data_readiness_gate.py",
                    repo / "scripts/boot_preflight.py",
                    repo / "scripts/run_data_readiness_gate.py",
                ),
                mode,
            ),
            _check_replay_certification(mode),
        ]
    )
    check_payload = [check.to_dict() for check in checks]
    failures = [check.reason for check in checks if check.status == "FAIL"]
    warnings = [check.reason for check in checks if check.status == "WARN"]
    strict_failures = [check.reason for check in checks if check.strict == "FAIL"]
    planning_failures = [check.reason for check in checks if check.planning == "FAIL"]
    strict_status = "FAIL" if strict_failures else "WARN" if any(check.strict == "WARN" for check in checks) else "PASS"
    planning_status = "FAIL" if planning_failures else "WARN" if any(check.planning == "WARN" for check in checks) else "PASS"
    overall_status = strict_status if mode == "strict" else planning_status
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "mode": mode,
        "overall_status": overall_status,
        "planning_status": planning_status,
        "strict_status": strict_status,
        "route_id": "portfolio_allocation.strict.v0",
        "boot_contract": {
            "read_only": True,
            "provider_calls_allowed": False,
            "canonical_writes_allowed": False,
            "broker_calls_allowed": False,
            "replay_rebuild_allowed": False,
            "repairs_performed": [],
            "allowed_boot_writes": sorted(ALLOWED_BOOT_WRITES),
            "canonical_boot_status_path": DEFAULT_STATUS_PATH.as_posix(),
        },
        "checks": check_payload,
        "route_readiness": _route_readiness(checks, mode),
        "summary": {
            "blockers": failures,
            "warnings": warnings,
            "next_actions": _next_actions(overall_status, strict_status),
        },
    }


def _next_actions(overall_status: str, strict_status: str) -> list[str]:
    if overall_status == "FAIL":
        return ["Fix failed local data-readiness checks before trusting research output."]
    if strict_status != "PASS":
        return ["Planning may proceed; strict trusted output remains degraded or uncertified."]
    return ["Data readiness gate passed for strict local research trust."]


def status_json_text(status: Mapping[str, Any]) -> str:
    return json.dumps(status, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _readiness_check_from_status(status: Mapping[str, Any]) -> ReadinessCheck:
    raw_status = str(status.get("overall_status", "FAIL")).strip().upper()
    if raw_status == "PASS":
        check_status = "pass"
        severity = "ready"
        summary = "Data readiness gate passed."
    elif raw_status in {"WARN", "DEFER", "DEFERRED"}:
        check_status = "warn" if raw_status == "WARN" else "deferred"
        severity = "degraded"
        summary = "Data readiness gate is degraded or uncertified."
    else:
        check_status = "fail"
        severity = "blocked"
        summary = "Data readiness gate failed."

    details: dict[str, Any] = {
        "overall_status": raw_status,
        "planning_status": status.get("planning_status"),
        "strict_status": status.get("strict_status"),
        "mode": status.get("mode"),
        "route_id": status.get("route_id"),
        "route_readiness": status.get("route_readiness"),
    }
    summary_payload = status.get("summary")
    if isinstance(summary_payload, Mapping):
        details["summary"] = dict(summary_payload)
        blockers = summary_payload.get("blockers")
        warnings = summary_payload.get("warnings")
        if raw_status == "FAIL" and blockers:
            summary = f"Data readiness gate failed: {len(blockers)} blocker(s)."
        elif raw_status == "WARN" and warnings:
            summary = f"Data readiness gate warned: {len(warnings)} warning(s)."

    return ReadinessCheck(
        id="data_readiness_gate",
        label="Data readiness gate",
        status=check_status,
        severity=severity,
        summary=summary,
        destination="Boot Status",
        details=details,
    )


def write_boot_status(path: str | Path, status: Mapping[str, Any], *, repo_root: str | Path = ".") -> str:
    repo = Path(repo_root).resolve()
    target = _repo_path(repo, path)
    rel = _rel(target, repo)
    if rel not in ALLOWED_BOOT_WRITES:
        raise ValueError(f"boot status write not allowed: {rel}")
    boot_status = make_boot_status(
        source="core.data_readiness_gate",
        flags=BootContextFlags(safe_boot=False),
        checks=(_readiness_check_from_status(status),),
        generated_at=str(status.get("generated_at_utc") or _utc_now()),
        warnings=tuple(str(item) for item in status.get("summary", {}).get("warnings", []))
        if isinstance(status.get("summary"), Mapping)
        else (),
        metadata={
            "data_readiness": dict(status),
            "data_readiness_schema_version": status.get("schema_version"),
            "data_readiness_mode": status.get("mode"),
        },
    )
    text = boot_status.to_json_text()
    existing = target.read_text(encoding="utf-8") if target.exists() else None
    if existing == text:
        return "unchanged"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return "written"


def capture_boot_write_snapshot(
    repo_root: str | Path = ".",
    *,
    roots: Sequence[str | Path] = BOOT_WRITE_GUARD_ROOTS,
) -> dict[str, tuple[int, int] | tuple[int, int, bool]]:
    repo = Path(repo_root).resolve()
    snapshot: dict[str, tuple[int, int]] = {}
    for root_item in roots:
        root = _repo_path(repo, root_item)
        if not root.exists():
            continue
        paths = [root] if root.is_file() else (path for path in root.rglob("*") if path.is_file())
        for path in paths:
            rel = _rel(path, repo)
            if _is_snapshot_ignored(rel):
                continue
            stat = path.stat()
            normalized = _normalize_allowed_path(rel)
            snapshot[rel] = (
                int(stat.st_size),
                int(stat.st_mtime_ns),
                _is_valid_boot_status_artifact(path) if normalized in ALLOWED_BOOT_WRITES else False,
            )
    for allowed in ALLOWED_BOOT_WRITES:
        path = _repo_path(repo, allowed)
        if path.exists():
            stat = path.stat()
            snapshot[_normalize_allowed_path(allowed)] = (
                int(stat.st_size),
                int(stat.st_mtime_ns),
                _is_valid_boot_status_artifact(path),
            )
    return snapshot


def diff_boot_write_snapshot(
    before: Mapping[str, tuple[int, int] | tuple[int, int, bool]],
    after: Mapping[str, tuple[int, int] | tuple[int, int, bool]],
    *,
    allowed_writes: Iterable[str] = ALLOWED_BOOT_WRITES,
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    allowed = {_normalize_allowed_path(path) for path in allowed_writes}
    before_keys = set(before)
    after_keys = set(after)
    changed = sorted(
        (before_keys ^ after_keys)
        | {path for path in before_keys & after_keys if before[path] != after[path]}
    )
    allowed_changed: list[str] = []
    disallowed_changed: list[str] = []
    invalid_allowed_writes: list[str] = []
    for path in changed:
        normalized = _normalize_allowed_path(path)
        after_entry = after.get(path)
        valid_allowed = (
            len(after_entry) >= 3 and bool(after_entry[2])
            if isinstance(after_entry, tuple)
            else False
        )
        if normalized in allowed and valid_allowed:
            allowed_changed.append(path)
        else:
            disallowed_changed.append(path)
            if normalized in allowed:
                invalid_allowed_writes.append(path)
    return {
        "status": "FAIL" if disallowed_changed else "PASS",
        "changed": changed,
        "allowed_changed": allowed_changed,
        "disallowed_changed": disallowed_changed,
        "invalid_allowed_writes": invalid_allowed_writes,
        "post_boot_only_allowed_delta": not disallowed_changed,
    }


def _is_valid_boot_status_artifact(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            return False
        BootStatus.from_json_dict(payload)
    except (OSError, json.JSONDecodeError, BootStatusValidationError, TypeError, ValueError):
        return False
    return True


def _normalize_allowed_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def _is_snapshot_ignored(rel_path: str) -> bool:
    normalized = _normalize_allowed_path(rel_path)
    parts = set(normalized.split("/"))
    if "__pycache__" in parts or ".pytest_cache" in parts:
        return True
    return normalized.endswith((".pyc", ".pyo"))
