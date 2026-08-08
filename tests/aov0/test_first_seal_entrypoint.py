from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.aov0.contracts import DEFAULT_CONTRACT
from research.aov0.experiment import reopen_prospective_seal_full_chain
from scripts.aov0_first_seal import (
    EXECUTION_CALENDAR_ID,
    FRESH_VERIFICATION_SCHEMA,
    _artifact_identity,
    _universe_hash_from_primitives,
    issue_clock_start_receipt,
    promote_seal_candidate,
    prospective_authority_state,
    run_first_seal as _run_first_seal,
)


KNOWLEDGE_CUTOFF = "2026-08-05T22:00:00Z"
CUT_BUILT_AT = "2026-08-05T22:05:00Z"
TARGET_DATE = "2026-08-05"
EVALUATION_START = "2026-08-06T20:00:00Z"
TEST_SEAL_TIME = datetime(2026, 8, 5, 22, 10, tzinfo=UTC)


def run_first_seal(*args, **kwargs):
    kwargs.setdefault("sealed_at", TEST_SEAL_TIME)
    return _run_first_seal(*args, **kwargs)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_cut(
    root: Path,
    *,
    target_date: str = TARGET_DATE,
    knowledge_cutoff: str = KNOWLEDGE_CUTOFF,
    cut_built_at: str = CUT_BUILT_AT,
    evaluation_start: str = EVALUATION_START,
    contract_hash: str | None = None,
    universe_hash: str | None = None,
    source_receipts: dict[str, dict[str, str]] | None = None,
) -> None:
    primitives = pd.read_parquet(root / "vertical_primitives.parquet")
    receipts = source_receipts or {
        "ciq_quarterly_fundamentals": {
            "source_id": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
            "retrieved_at": f"{target_date}T20:46:00Z",
            "raw_object_sha256": "b" * 64,
        },
        "ciq_security_master": {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MASTER",
            "retrieved_at": f"{target_date}T20:50:00Z",
            "raw_object_sha256": "c" * 64,
        },
        "ciq_market_data": {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
            "retrieved_at": f"{target_date}T21:02:00Z",
            "raw_object_sha256": "d" * 64,
        },
        "nyfed_sofr": {
            "source_id": "NYFED:SOFR",
            "retrieved_at": f"{target_date}T20:00:00Z",
            "raw_object_sha256": "e" * 64,
        },
    }
    payload = {
        "schema_version": "aov0_ciq_decision_cut_v3",
        "decision_cut_id": "AOV0_REAL_CUT_TEST",
        "knowledge_cutoff": knowledge_cutoff,
        "cut_built_at": cut_built_at,
        "decision_target_date": target_date,
        "evaluation_start": evaluation_start,
        "execution_calendar_id": EXECUTION_CALENDAR_ID,
        "contract_hash": contract_hash or DEFAULT_CONTRACT.contract_hash,
        "universe_hash": universe_hash or _universe_hash_from_primitives(primitives),
        "source_receipts": receipts,
        "input_sha256": {
            "rule100_targets": _sha256(root / "rule100_targets.parquet"),
            "vertical_primitives": _sha256(root / "vertical_primitives.parquet"),
            "total_returns": _sha256(root / "total_returns.parquet"),
            "official_sofr": _sha256(root / "official_sofr.parquet"),
        },
    }
    (root / "decision_cut.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_admitted_inputs(
    root: Path,
    *,
    aov_dates: pd.DatetimeIndex,
    aov_primitives: pd.DataFrame,
    rule100_weights: pd.DataFrame,
    aov_returns: pd.DataFrame,
    target_date: str = TARGET_DATE,
    knowledge_cutoff: str = KNOWLEDGE_CUTOFF,
    cut_built_at: str = CUT_BUILT_AT,
    evaluation_start: str = EVALUATION_START,
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    rule100_weights.rename_axis("date").reset_index().to_parquet(root / "rule100_targets.parquet", index=False)
    aligned_returns = (
        aov_returns.rename_axis(index="date", columns="security_id")
        .stack()
        .rename("aligned_total_return")
        .reset_index()
    )
    primitives = aov_primitives.copy()
    primitives["date"] = pd.to_datetime(primitives["date"], errors="raise").dt.normalize()
    primitives = primitives.drop(columns=["total_return"]).merge(
        aligned_returns,
        on=["date", "security_id"],
        how="left",
        validate="one_to_one",
    )
    primitives = primitives.rename(columns={"aligned_total_return": "total_return"})
    primitives.to_parquet(root / "vertical_primitives.parquet", index=False)
    aov_returns.rename_axis("date").reset_index().to_parquet(root / "total_returns.parquet", index=False)
    official_sofr = pd.DataFrame(
        {
            "effective_date": aov_dates,
            "published_at": [pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=12) for date in aov_dates],
            "sofr_percent": [5.0] * len(aov_dates),
        }
    )
    official_sofr.to_parquet(root / "official_sofr.parquet", index=False)
    _write_cut(
        root,
        target_date=target_date,
        knowledge_cutoff=knowledge_cutoff,
        cut_built_at=cut_built_at,
        evaluation_start=evaluation_start,
    )


def _shift_fixture_to_target(
    *,
    target_date: str,
    aov_primitives: pd.DataFrame,
    rule100_weights: pd.DataFrame,
    aov_returns: pd.DataFrame,
) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range(end=target_date, periods=len(rule100_weights))
    old_dates = list(pd.DatetimeIndex(rule100_weights.index).normalize())
    mapping = dict(zip(old_dates, dates))
    shifted_rule = rule100_weights.copy()
    shifted_rule.index = dates
    shifted_returns = aov_returns.copy()
    shifted_returns.index = dates
    shifted_primitives = aov_primitives.copy()
    shifted_primitives["date"] = pd.to_datetime(shifted_primitives["date"]).dt.normalize().map(mapping)
    shifted_primitives["valid_at"] = [
        (pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=20)).isoformat()
        for date in shifted_primitives["date"]
    ]
    shifted_primitives["known_at"] = [
        (pd.Timestamp(date, tz="UTC") + pd.Timedelta(hours=21)).isoformat()
        for date in shifted_primitives["date"]
    ]
    return dates, shifted_primitives, shifted_rule, shifted_returns


def test_first_real_seal_blocks_on_missing_admitted_inputs(tmp_path: Path) -> None:
    result = run_first_seal(input_root=tmp_path / "missing", output_root=tmp_path / "out")
    assert result["status"] == "BLOCKED_MISSING_ADMITTED_INPUTS"
    assert result["prospective_clock_started"] is False
    assert result["financial_alpha_evidence"] == 0
    assert not (tmp_path / "out").exists()


def test_seal_construction_is_candidate_only_and_binds_v3_close_authority(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(
        input_root,
        aov_dates=aov_dates,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
    )
    result = run_first_seal(input_root=input_root, output_root=tmp_path / "out")
    assert result["status"] == "SEAL_CANDIDATE_WRITTEN"
    assert result["prospective_clock_started"] is False
    assert result["decision_target_date"] == TARGET_DATE
    assert result["evaluation_start"] == EVALUATION_START
    seal = json.loads(Path(result["seal_path"]).read_text(encoding="utf-8"))
    assert seal["schema_version"] == "aov0_prospective_seal_v3"
    assert seal["decision_cut_binding"]["knowledge_cutoff"] == KNOWLEDGE_CUTOFF
    assert seal["decision_cut_binding"]["cut_built_at"] == CUT_BUILT_AT
    assert seal["decision_cut_binding"]["evaluation_start"] == EVALUATION_START
    assert seal["decision_cut_binding"]["execution_calendar_id"] == "NYSE_2026_CORE_CLOSE_1600_ET"
    assert seal["sealed_at"] == "2026-08-05T22:10:00Z"
    assert seal["outcome_open_not_before"] == "2026-09-05T20:00:00Z"
    assert seal["financial_alpha_evidence"] == 0
    assert "prospective_clock_started" not in seal


def test_first_real_seal_rejects_input_byte_tamper(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    tampered = pd.read_parquet(input_root / "total_returns.parquet")
    asset_column = next(column for column in tampered.columns if column != "date")
    tampered.loc[0, asset_column] = float(tampered.loc[0, asset_column]) + 0.001
    tampered.to_parquet(input_root / "total_returns.parquet", index=False)
    with pytest.raises(ValueError, match="aov0_first_seal_input_hash_mismatch:total_returns"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_target_return_mismatch_between_primitive_and_pnl(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    primitives = pd.read_parquet(input_root / "vertical_primitives.parquet")
    target_mask = pd.to_datetime(primitives["date"]).dt.normalize().eq(pd.Timestamp(TARGET_DATE))
    row_index = primitives.loc[target_mask].index[0]
    primitives.loc[row_index, "total_return"] = float(primitives.loc[row_index, "total_return"]) + 0.001
    primitives.to_parquet(input_root / "vertical_primitives.parquet", index=False)
    _write_cut(input_root)
    with pytest.raises(ValueError, match="aov0_first_seal_target_total_return_mismatch"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_target_primitive_asset_set_mismatch(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    primitives = pd.read_parquet(input_root / "vertical_primitives.parquet")
    target_mask = pd.to_datetime(primitives["date"]).dt.normalize().eq(pd.Timestamp(TARGET_DATE))
    primitives = primitives.drop(index=primitives.loc[target_mask].index[0]).reset_index(drop=True)
    primitives.to_parquet(input_root / "vertical_primitives.parquet", index=False)
    _write_cut(input_root)
    with pytest.raises(ValueError, match="aov0_first_seal_target_primitive_asset_set_mismatch"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_post_cut_return_history(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    returns = pd.read_parquet(input_root / "total_returns.parquet")
    future = returns.iloc[[-1]].copy()
    future["date"] = pd.Timestamp(TARGET_DATE) + pd.Timedelta(days=1)
    pd.concat([returns, future], ignore_index=True).to_parquet(input_root / "total_returns.parquet", index=False)
    _write_cut(input_root)
    with pytest.raises(ValueError, match="aov0_first_seal_returns_post_cut_history"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_primitive_knowledge_after_cut(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    primitives = pd.read_parquet(input_root / "vertical_primitives.parquet")
    primitives.loc[primitives.index[-1], "known_at"] = "2026-08-05T22:00:00.000001Z"
    primitives.to_parquet(input_root / "vertical_primitives.parquet", index=False)
    _write_cut(input_root)
    with pytest.raises(ValueError, match="aov0_first_seal_primitives_future_knowledge"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_target_date_not_bound_to_current_history(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    _write_cut(input_root, target_date="2026-08-06", knowledge_cutoff="2026-08-06T22:00:00Z", cut_built_at="2026-08-06T22:05:00Z", evaluation_start="2026-08-07T20:00:00Z")
    with pytest.raises(ValueError, match="aov0_first_seal_rule100_target_date_mismatch"):
        _run_first_seal(input_root=input_root, output_root=tmp_path / "out", sealed_at=datetime(2026, 8, 6, 22, 10, tzinfo=UTC))


def test_first_real_seal_rejects_evaluation_start_not_after_cut(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    _write_cut(input_root, cut_built_at="2026-08-06T20:00:00Z", evaluation_start="2026-08-06T20:00:00Z")
    with pytest.raises(ValueError, match="aov0_first_seal_evaluation_start_not_after_cut"):
        _run_first_seal(input_root=input_root, output_root=tmp_path / "out", sealed_at=datetime(2026, 8, 6, 19, 0, tzinfo=UTC))


def test_first_real_seal_rejects_contract_hash_drift(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    _write_cut(input_root, contract_hash="d" * 64)
    with pytest.raises(ValueError, match="aov0_first_seal_contract_hash_mismatch"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_universe_hash_drift(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    _write_cut(input_root, universe_hash="e" * 64)
    with pytest.raises(ValueError, match="aov0_first_seal_universe_hash_mismatch"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_missing_ciq_quarterly_fundamentals_receipt(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    cut_path = input_root / "decision_cut.json"
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    del cut["source_receipts"]["ciq_quarterly_fundamentals"]
    cut_path.write_text(json.dumps(cut, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_first_seal_source_receipts_invalid"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_source_receipt_after_knowledge_cutoff(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    cut_path = input_root / "decision_cut.json"
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    cut["source_receipts"]["ciq_market_data"]["retrieved_at"] = "2026-08-05T22:00:00.000001Z"
    cut_path.write_text(json.dumps(cut, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="source_receipt_after_knowledge_cutoff:ciq_market_data"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_first_real_seal_rejects_nyfed_sofr_retrieval_before_1500_et(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    cut_path = input_root / "decision_cut.json"
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    cut["source_receipts"]["nyfed_sofr"]["retrieved_at"] = "2026-08-05T18:59:59Z"
    cut_path.write_text(json.dumps(cut, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_first_seal_nyfed_sofr_retrieved_before_1500_et"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_sofr_authority_substitution_is_rejected_fail_closed(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    cut_path = input_root / "decision_cut.json"
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    cut["source_receipts"]["nyfed_sofr"]["source_id"] = "ETF:SHV_PROXY_CASH"
    cut_path.write_text(json.dumps(cut, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_first_seal_source_receipt_id_invalid:nyfed_sofr"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_security_id_mutation_to_ticker_is_rejected_fail_closed(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    rule = pd.read_parquet(input_root / "rule100_targets.parquet").rename(columns={"CIQSEC:101": "AAA"})
    rule.to_parquet(input_root / "rule100_targets.parquet", index=False)
    _write_cut(input_root)
    with pytest.raises(ValueError, match="aov0_first_seal_ciq_security_id_columns_required"):
        run_first_seal(input_root=input_root, output_root=tmp_path / "out")


def test_full_chain_blocks_bound_market_artifact_one_byte_mutation(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    candidate = run_first_seal(input_root=input_root, output_root=tmp_path / "out")
    market_path = input_root / "total_returns.parquet"
    raw = bytearray(market_path.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    market_path.write_bytes(bytes(raw))
    with pytest.raises(ValueError, match="artifact_hash_mismatch|input_hash_mismatch"):
        reopen_prospective_seal_full_chain(Path(candidate["seal_path"]), repo_root=Path(__file__).resolve().parents[2])


def test_full_chain_blocks_target_vector_one_bp_serialized_mutation(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    candidate = run_first_seal(input_root=input_root, output_root=tmp_path / "out")
    seal = json.loads(Path(candidate["seal_path"]).read_text(encoding="utf-8"))
    manifest_path = Path(seal["experiment_manifest"]["path"])
    if not manifest_path.is_absolute():
        manifest_path = Path(__file__).resolve().parents[2] / manifest_path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    values = manifest["current_decision_targets"]["arm_target_vectors"]["rule100"]["values"]
    values[0] = format(float(values[0]) + 0.0001, ".17g")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="artifact_(size|hash)_mismatch|target_vector_hash_mismatch"):
        reopen_prospective_seal_full_chain(Path(candidate["seal_path"]), repo_root=Path(__file__).resolve().parents[2])


def test_same_process_only_proof_cannot_issue_clock_start_receipt(
    tmp_path: Path,
    aov_dates,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    input_root = tmp_path / "current"
    _write_admitted_inputs(input_root, aov_dates=aov_dates, aov_primitives=aov_primitives, rule100_weights=rule100_weights, aov_returns=aov_returns)
    candidate = run_first_seal(input_root=input_root, output_root=tmp_path / "out")
    seal_path = Path(candidate["seal_path"]).resolve()
    body = {
        "schema_version": FRESH_VERIFICATION_SCHEMA,
        "status": "FULL_CHAIN_REOPEN_VERIFIED",
        "verified_at": "2026-08-05T22:11:00Z",
        "parent_pid": os.getpid(),
        "verifier_pid": os.getpid(),
        "fresh_process": False,
        "seal_id": candidate["seal_id"],
        "seal_artifact": _artifact_identity(seal_path),
        "verifier_executable": _artifact_identity(Path(__file__).resolve().parents[2] / "scripts/aov0_reopen_seal.py"),
        "evaluation_start": candidate["evaluation_start"],
        "outcome_open_not_before": candidate["outcome_open_not_before"],
    }
    proof = {**body, "verification_id": domain_hash("AOV0:FRESH_PROCESS_VERIFICATION:V1", body)}
    proof_path = tmp_path / "same_process_proof.json"
    proof_path.write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="aov0_clock_start_fresh_process_required"):
        issue_clock_start_receipt(
            seal_path=seal_path,
            verification_proof_path=proof_path,
            output_root=tmp_path / "out",
            expected_parent_pid=os.getpid(),
        )


def test_fresh_process_promotion_writes_separate_clock_receipt_and_temporal_state_stays_closed_until_due(
    tmp_path: Path,
    aov_primitives,
    rule100_weights,
    aov_returns,
) -> None:
    target = "2026-08-07"
    dates, primitives, weights, returns = _shift_fixture_to_target(
        target_date=target,
        aov_primitives=aov_primitives,
        rule100_weights=rule100_weights,
        aov_returns=aov_returns,
    )
    input_root = tmp_path / "current"
    _write_admitted_inputs(
        input_root,
        aov_dates=dates,
        aov_primitives=primitives,
        rule100_weights=weights,
        aov_returns=returns,
        target_date=target,
        knowledge_cutoff="2026-08-07T22:00:00Z",
        cut_built_at="2026-08-07T22:05:00Z",
        evaluation_start="2026-08-10T20:00:00Z",
    )
    candidate = _run_first_seal(
        input_root=input_root,
        output_root=tmp_path / "out",
        sealed_at=datetime(2026, 8, 7, 22, 10, tzinfo=UTC),
    )
    seal_path = Path(candidate["seal_path"])
    before_receipt = prospective_authority_state(
        seal_path=seal_path,
        clock_start_receipt_path=None,
        now=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
    )
    assert before_receipt == {
        "prospective_clock_started": False,
        "evaluation_started": False,
        "outcome_open_authorized": False,
        "future_outcome_authority_available": False,
    }

    promoted = promote_seal_candidate(candidate, output_root=tmp_path / "out")
    assert promoted["status"] == "PROSPECTIVE_CLOCK_STARTED", json.dumps(promoted, indent=2, sort_keys=True, default=str)
    assert promoted["prospective_clock_started"] is True
    assert promoted["fresh_process_reopen"]["status"] == "FULL_CHAIN_REOPEN_VERIFIED"
    receipt_path = Path(promoted["clock_start_receipt"]["path"])
    assert receipt_path.is_file()
    assert receipt_path != seal_path

    receipt = promoted["clock_start_receipt"]
    clock_started_at = pd.Timestamp(receipt["clock_started_at"])
    evaluation_start = pd.Timestamp(receipt["evaluation_start"])
    maturity = pd.Timestamp(receipt["outcome_open_not_before"])
    post_receipt = prospective_authority_state(
        seal_path=seal_path,
        clock_start_receipt_path=receipt_path,
        now=clock_started_at + pd.Timedelta(seconds=1),
    )
    assert post_receipt["prospective_clock_started"] is True
    assert post_receipt["evaluation_started"] is False
    assert post_receipt["outcome_open_authorized"] is False
    pre_maturity = prospective_authority_state(
        seal_path=seal_path,
        clock_start_receipt_path=receipt_path,
        now=maturity - pd.Timedelta(seconds=1),
    )
    assert pre_maturity["evaluation_started"] is True
    assert pre_maturity["outcome_open_authorized"] is False
    at_maturity = prospective_authority_state(
        seal_path=seal_path,
        clock_start_receipt_path=receipt_path,
        now=maturity,
    )
    assert evaluation_start < maturity
    assert at_maturity["outcome_open_authorized"] is True
    assert at_maturity["future_outcome_authority_available"] is True
