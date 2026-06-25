"""Standalone 2015-2019 best-available PEAD diagnostic.

Option 1 only: read-only data gate first, then an isolated flagged diagnostic
curve. This file is not imported by the strict M6 runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import pead_m6_pit_walk_forward_equity_curve as m6

D1_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d1_sue_signal.parquet.manifest.json"
D2A_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d2_daily_returns.parquet.manifest.json"
D2B_MANIFEST_PATH = ROOT / "data" / "processed" / "pead_d2b_event_windows.parquet.manifest.json"
DATA_GATE_OUTPUT_PATH = ROOT / "docs" / "context" / "e2e_evidence" / "pead_m6b_data_gate_bestavail_policy_20260625.json"
BESTAVAIL_EVIDENCE_PATH = ROOT / "docs" / "context" / "e2e_evidence" / "pead_m6b_bestavail_illustrative_2015_2019.json"
BESTAVAIL_DAILY_RETURNS_PATH = ROOT / "data" / "processed" / "pead_m6b_bestavail_illustrative_2015_2019_daily_returns.parquet"
ROUND_ID = "ROUND-20260625-V2-PEAD-M6B-BESTAVAIL-OPTION1"
DATA_GATE_SCOPE_ID = "V2_PEAD_M6B_DATA_GATE_BESTAVAIL_POLICY_READ_ONLY"
RUN_SCOPE_ID = "V2_PEAD_M6B_RUN_BESTAVAIL_ILLUSTRATIVE_2015_2019_STANDALONE"
CLAIM_CEILING_FLAGS = ["illustrative_only", "restated_vintage", "no_delisting", "survivorship_biased", "coverage_2015_2019", "provider_limited", "not_alpha", "not_tradable_claim"]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _display_path(path: Path) -> str:
    return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _write_json_atomic(payload: dict[str, Any], output_path: Path) -> Path:
    return m6.write_evidence_atomic(payload, output_path)


def _write_json_temp(payload: dict[str, Any], output_path: Path) -> Path:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _write_parquet_temp(frame: pd.DataFrame, output_path: Path) -> Path:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        frame.to_parquet(temp_path, index=False)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return temp_path


def _write_parquet_atomic(frame: pd.DataFrame, output_path: Path) -> Path:
    temp_path = _write_parquet_temp(frame, output_path)
    output_path = output_path.resolve()
    try:
        os.replace(temp_path, output_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
    return output_path


def _commit_bestavail_outputs(
    daily: pd.DataFrame,
    evidence: dict[str, Any],
    *,
    daily_returns_path: Path = BESTAVAIL_DAILY_RETURNS_PATH,
    evidence_path: Path = BESTAVAIL_EVIDENCE_PATH,
) -> tuple[Path, Path]:
    """Commit B parquet+JSON as one rollback-protected package.

    Both outputs are fully staged before either public path is replaced.  If any
    replace step fails, already replaced paths are rolled back to their previous
    contents or removed if they did not previously exist.
    """

    daily_returns_path = Path(daily_returns_path).resolve()
    evidence_path = Path(evidence_path).resolve()
    staged_daily = _write_parquet_temp(daily, daily_returns_path)
    staged_evidence = _write_json_temp(evidence, evidence_path)
    staged_paths = [staged_daily, staged_evidence]
    commit_token = uuid.uuid4().hex
    committed: list[tuple[Path, Path | None]] = []
    try:
        for staged, final in ((staged_daily, daily_returns_path), (staged_evidence, evidence_path)):
            backup: Path | None = None
            if final.exists():
                backup = final.with_name(f".{final.name}.{commit_token}.rollback")
                os.replace(final, backup)
            committed.append((final, backup))
            os.replace(staged, final)
        return daily_returns_path, evidence_path
    except BaseException:
        for final, backup in reversed(committed):
            final.unlink(missing_ok=True)
            if backup is not None and backup.exists():
                os.replace(backup, final)
        for staged in staged_paths:
            staged.unlink(missing_ok=True)
        raise
    finally:
        for _, backup in committed:
            if backup is not None:
                backup.unlink(missing_ok=True)


def bestavail_validity_flags() -> dict[str, Any]:
    flags = {flag: True for flag in CLAIM_CEILING_FLAGS}
    flags.update({
        "no_delisting_adjustment": True,
        "single_source": True,
        "local_only": True,
        "provider_ingestion_performed": False,
        "restated_vintage_eps": True,
        "unrestated_eps_vintage_available": False,
        "delisting_adjusted_returns": False,
        "m6b_strict_readiness": False,
        "usable_for_alpha_inference": False,
        "coverage_start": "2015-01-01",
        "coverage_end": "2019-12-31",
    })
    return flags


def build_data_gate_evidence() -> dict[str, Any]:
    d1 = _read_json(D1_MANIFEST_PATH)
    d2a = _read_json(D2A_MANIFEST_PATH)
    d2b = _read_json(D2B_MANIFEST_PATH)
    flags = bestavail_validity_flags()
    flags.update({"curve_emitted": False, "daily_return_parquet_emitted": False})
    return {
        "schema_version": "1.0",
        "artifact_name": "pead_m6b_data_gate_bestavail_policy_20260625",
        "round_id": ROUND_ID,
        "scope_id": DATA_GATE_SCOPE_ID,
        "mode": "data_gate_read_only_policy_decision",
        "workflow_status": "policy_locked_best_available_with_flags_no_curve",
        "decision": {
            "eps_vintage_policy": "accept_best_available_restated_with_flags_only",
            "return_policy": "accept_local_compustat_no_delisting_with_flags_only",
            "provider_policy": "accept_single_source_local_compustat_with_flags_only",
            "gate_outputs_curve": False,
            "strict_m6b_data_contract_ready": False,
            "bestavail_run_authorized_after_gate": True,
        },
        "lineage_read_only": {
            "d1_rows": d1.get("row_count"),
            "d1_rdq_min": d1.get("rdq_min"),
            "d1_rdq_max": d1.get("rdq_max"),
            "d2a_rows": d2a.get("row_count"),
            "d2a_date_min": d2a.get("date_min"),
            "d2a_date_max": d2a.get("date_max"),
            "d2a_sources": d2a.get("data_sources", []),
            "d2b_rows": d2b.get("counts", {}).get("rows"),
            "d2b_events": d2b.get("counts", {}).get("events"),
        },
        "data_validity_flags": flags,
        "claim_ceiling_flags": CLAIM_CEILING_FLAGS,
        "claim_boundary": {
            "allowed_claim": "read-only policy gate only; no curve",
            "next_allowed_step": "standalone 2015-2019 illustrative diagnostic only",
            "not_allowed_claim": "strict readiness, alpha inference, or tradable claim",
        },
    }


def _parquet_from_d2a_manifest() -> Path:
    manifest = _read_json(D2A_MANIFEST_PATH)
    return D2A_MANIFEST_PATH.parent / str(manifest["parquet_file"])


def _parquet_from_d2b_manifest() -> Path:
    manifest = _read_json(D2B_MANIFEST_PATH)
    return D2B_MANIFEST_PATH.parent / str(manifest["output"]["parquet_file"])


def load_bestavail_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    d2a_parquet = _parquet_from_d2a_manifest()
    d2b_parquet = _parquet_from_d2b_manifest()
    con = duckdb.connect(database=":memory:", config={"memory_limit": m6.SPARSE_ENGINE_MEMORY_LIMIT})
    try:
        con.execute(f"SET threads = {m6.SPARSE_ENGINE_THREADS}")
        events = con.execute("""
            SELECT CAST(event_id AS VARCHAR) AS event_id,
                   CAST(first(security_id ORDER BY event_day) AS VARCHAR) AS security_id,
                   CAST(first(event_date ORDER BY event_day) AS DATE) AS decision_date,
                   CAST(first(sue_price_scaled_clipped ORDER BY event_day) AS DOUBLE) AS signal,
                   TRUE AS tradable, TRUE AS liquidity_pass
            FROM read_parquet(?)
            WHERE CAST(event_date AS DATE) BETWEEN DATE '2015-01-01' AND DATE '2019-12-31'
              AND handoff_eligible = TRUE AND window_complete = TRUE AND coverage_reason = 'complete'
            GROUP BY event_id HAVING signal IS NOT NULL
        """, [str(d2b_parquet)]).fetchdf()
        con.register("event_securities", events[["security_id"]].drop_duplicates())
        returns = con.execute("""
            SELECT CAST(ret.security_id AS VARCHAR) AS security_id,
                   CAST(ret.date AS DATE) AS return_date,
                   CAST(ret.total_return AS DOUBLE) AS tradable_total_return
            FROM read_parquet(?) AS ret
            JOIN event_securities AS ids ON CAST(ret.security_id AS VARCHAR) = ids.security_id
            WHERE CAST(ret.date AS DATE) BETWEEN DATE '2015-01-01' AND DATE '2019-12-31'
              AND ret.total_return IS NOT NULL AND isfinite(CAST(ret.total_return AS DOUBLE))
        """, [str(d2a_parquet)]).fetchdf()
    finally:
        con.close()
    if events.empty or returns.empty:
        raise ValueError("best-available 2015-2019 frames are empty")
    return events, returns


def filter_events_for_full_holding_window(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    portfolio_config: m6.PortfolioConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Remove events whose entry cannot complete the configured holding window."""

    portfolio_config.validate()
    required_events = {"event_id", "security_id", "decision_date", "signal", "tradable", "liquidity_pass"}
    m6._require_columns(events, required_events, "events")
    m6._require_columns(returns, {"return_date"}, "returns")
    calendar = pd.to_datetime(returns["return_date"], errors="coerce").dropna().drop_duplicates().sort_values().reset_index(drop=True)
    if calendar.empty:
        raise ValueError("best-available 2015-2019 return calendar is empty")
    holding_period_sessions = int(portfolio_config.holding_period_sessions)
    max_entry_idx = len(calendar) - holding_period_sessions
    if max_entry_idx < 0:
        raise ValueError("return calendar is shorter than the configured holding window")
    event_dates = pd.to_datetime(events["decision_date"], errors="coerce").dt.normalize()
    entry_idx = calendar.to_numpy(dtype="datetime64[ns]").searchsorted(event_dates.to_numpy(dtype="datetime64[ns]"), side="right")
    eligible = event_dates.notna().to_numpy() & (entry_idx <= max_entry_idx)
    filtered = events.loc[eligible].copy()
    if filtered.empty:
        raise ValueError("full-holding-window filter removed all best-available events")
    metadata = {
        "holding_period_sessions": holding_period_sessions,
        "return_calendar_sessions": int(len(calendar)),
        "return_calendar_start": calendar.iloc[0].strftime("%Y-%m-%d"),
        "return_calendar_end": calendar.iloc[-1].strftime("%Y-%m-%d"),
        "max_return_idx": int(len(calendar) - 1),
        "max_entry_idx_for_full_holding_window": int(max_entry_idx),
        "latest_eligible_entry_session": calendar.iloc[max_entry_idx].strftime("%Y-%m-%d"),
        "events_before_full_window_filter": int(len(events)),
        "events_after_full_window_filter": int(len(filtered)),
        "events_removed_by_full_window_filter": int(len(events) - len(filtered)),
    }
    return filtered, metadata


def _selected_terminal_window_completeness(
    events: pd.DataFrame,
    returns: pd.DataFrame,
    portfolio_config: m6.PortfolioConfig,
) -> dict[str, Any]:
    selected, _input_returns, calendar = m6._prepare_sparse_engine_relations(events, returns, portfolio_config)
    if selected.empty or calendar.empty:
        raise ValueError("full-window completeness check has no selected events or calendar")
    max_return_idx = int(calendar["return_idx"].max())
    incomplete = int((selected["exit_idx"] > max_return_idx).sum())
    return {
        "selected_events_after_signal_filter": int(len(selected)),
        "selected_events_with_incomplete_60_session_window": incomplete,
        "selected_max_exit_idx": int(selected["exit_idx"].max()),
        "return_calendar_max_idx": max_return_idx,
        "full_60_session_eligibility_enforced": incomplete == 0,
    }


def _build_bestavail_daily_and_metadata() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any], dict[str, Any]]:
    gate = build_data_gate_evidence()
    events, returns = load_bestavail_frames()
    cfg = m6.PortfolioConfig(holding_period_sessions=60, min_leg_count=10)
    events, eligibility = filter_events_for_full_holding_window(events, returns, cfg)
    completeness = _selected_terminal_window_completeness(events, returns, cfg)
    if completeness["selected_events_with_incomplete_60_session_window"] != 0:
        raise ValueError("best-available selected events still include terminal-incomplete holding windows")
    daily = m6.build_daily_portfolio_returns(events, returns, portfolio_config=cfg)
    daily = daily[(daily["return_date"] >= "2015-01-01") & (daily["return_date"] <= "2019-12-31")].copy()
    if daily.empty:
        raise ValueError("standalone best-available run emitted no 2015-2019 daily rows")
    return daily, gate, eligibility, completeness


def _build_bestavail_run_payload(
    *,
    daily: pd.DataFrame,
    daily_path: Path,
    daily_sha256: str,
    gate: dict[str, Any],
    eligibility: dict[str, Any],
    completeness: dict[str, Any],
) -> dict[str, Any]:
    metrics = m6.compute_equity_curve_metrics(daily)
    flags = bestavail_validity_flags()
    flags.update({"curve_emitted": True, "daily_return_parquet_emitted": True, "m6b_strict_readiness": False, "usable_for_alpha_inference": False})
    return {
        "schema_version": "1.0",
        "artifact_name": "pead_m6b_bestavail_illustrative_2015_2019",
        "round_id": ROUND_ID,
        "scope_id": RUN_SCOPE_ID,
        "mode": "standalone_best_available_illustrative_run",
        "workflow_status": "illustrative_curve_emitted_with_hard_limitations",
        "data_gate_reference": {"scope_id": gate["scope_id"], "curve_emitted_by_gate": False},
        "commit_protocol": {
            "command": "--commit-bestavail-run",
            "gate_precedes_run_commit": True,
            "run_outputs_staged_before_public_replace": True,
            "rollback_protected_package": [
                _display_path(BESTAVAIL_DAILY_RETURNS_PATH),
                _display_path(BESTAVAIL_EVIDENCE_PATH),
            ],
        },
        "terminal_window_eligibility": {**eligibility, **completeness},
        "daily_returns_output": {"path": _display_path(daily_path), "sha256": daily_sha256, "rows": len(daily)},
        "daily_return_summary": metrics["daily_return_summary"],
        "equity_curve_summary": metrics["equity_curve_summary"],
        "risk_metrics": metrics["risk_metrics"],
        "claim_ceiling_flags": CLAIM_CEILING_FLAGS,
        "data_validity_flags": flags,
        "claim_boundary": {"allowed_claim": "standalone engine sanity diagnostic only", "not_allowed_claim": "strict readiness, alpha inference, or tradable claim"},
    }


def build_bestavail_run_evidence() -> dict[str, Any]:
    """Build B evidence and its daily parquet through the safe local writer."""

    daily, gate, eligibility, completeness = _build_bestavail_daily_and_metadata()
    daily_path = _write_parquet_atomic(daily, BESTAVAIL_DAILY_RETURNS_PATH)
    return _build_bestavail_run_payload(
        daily=daily,
        daily_path=daily_path,
        daily_sha256=_sha256_file(daily_path),
        gate=gate,
        eligibility=eligibility,
        completeness=completeness,
    )


def commit_bestavail_run() -> Path:
    """Run the read-only gate first, then commit B JSON/parquet together."""

    gate = build_data_gate_evidence()
    gate_path = _write_json_atomic(gate, DATA_GATE_OUTPUT_PATH)
    daily, _gate, eligibility, completeness = _build_bestavail_daily_and_metadata()
    staged_daily = _write_parquet_temp(daily, BESTAVAIL_DAILY_RETURNS_PATH)
    try:
        daily_sha = _sha256_file(staged_daily)
        payload = _build_bestavail_run_payload(
            daily=daily,
            daily_path=BESTAVAIL_DAILY_RETURNS_PATH,
            daily_sha256=daily_sha,
            gate=gate,
            eligibility=eligibility,
            completeness=completeness,
        )
    finally:
        staged_daily.unlink(missing_ok=True)
    committed_daily_path, committed_evidence_path = _commit_bestavail_outputs(
        daily,
        payload,
        daily_returns_path=BESTAVAIL_DAILY_RETURNS_PATH,
        evidence_path=BESTAVAIL_EVIDENCE_PATH,
    )
    print(f"[write] {_display_path(gate_path)}")
    print(f"[write] {_display_path(committed_daily_path)}")
    return committed_evidence_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--data-gate", action="store_true")
    mode.add_argument("--run-bestavail", action="store_true", help="Alias for --commit-bestavail-run; kept for replay compatibility")
    mode.add_argument("--commit-bestavail-run", action="store_true", help="Run data gate first, then rollback-protected B JSON/parquet commit")
    args = parser.parse_args(argv)
    if args.data_gate:
        path = _write_json_atomic(build_data_gate_evidence(), DATA_GATE_OUTPUT_PATH)
        print(f"[write] {_display_path(path)}")
        return 0
    path = commit_bestavail_run()
    print(f"[write] {_display_path(path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
