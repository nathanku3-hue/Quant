from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from research.aov0.ciq_market import (
    ACCUMULATION_DIST_MAX,
    HARD_EXIT_DIST_SMA20,
    MIN_FACTOR_COVERAGE,
    MIN_HOLD_FACTOR_POSITIVES,
    RULE100_PRODUCT_MAX_WEIGHT,
    build_ciq_market_slice,
    normalize_primary_security_master,
)
from scripts.aov0_build_ciq_market import build_artifacts
from scripts.aov0_build_decision_cut import build_decision_cut
from scripts.aov0_fetch_nyfed_sofr import SOFR_URL, fetch_and_admit_sofr
from scripts.aov0_first_seal import promote_seal_candidate, run_first_seal
from research.aov0.experiment import reopen_prospective_seal, reopen_prospective_seal_full_chain
from scripts.pit_lifecycle_replay import (
    ACCUMULATION_DIST_MAX as OWNER_ACCUMULATION_DIST_MAX,
    HARD_EXIT_DIST_SMA20 as OWNER_HARD_EXIT_DIST_SMA20,
    MIN_FACTOR_COVERAGE as OWNER_MIN_FACTOR_COVERAGE,
    MIN_HOLD_FACTOR_POSITIVES as OWNER_MIN_HOLD_FACTOR_POSITIVES,
)


ADMITTED_AT = datetime(2026, 8, 7, 17, 30, tzinfo=UTC)
TARGET_DATE = "2026-08-07"


def _fundamentals() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "source_entity_id": ["1", "2", "3", "4"],
            "factor_present_count": [4, 3, 2, 4],
            "factor_positive_count": [4, 2, 2, 1],
            "known_at": ["2026-08-07T16:46:27Z"] * 4,
        }
    )


def _master() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "2", "3", "4"],
            "SP_SECURITY_ID": ["101", "202", "303", "404"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT101", "SPT202", "SPT303", "SPT404"],
            "Primary Security Flag": ["Yes", "Yes", "Yes", "Yes"],
            "Ticker": ["AAA", "BBB", "CCC", "DDD"],
            "Exchange": ["NASDAQ", "NYSE", "NYSE", "NASDAQ"],
            "Description": ["Common Stock"] * 4,
        }
    )


def _market_for(entity: str, security: str, trading: str, dates: pd.DatetimeIndex, slope: float) -> pd.DataFrame:
    x = np.arange(len(dates), dtype=float)
    close = 50.0 + slope * x + 0.15 * np.sin(x / 3.0)
    daily_pct = 0.35 + 0.18 * np.sin(x / 5.0) + (0.04 if entity == "1" else -0.02)
    volume = 1_000_000.0 + 15_000.0 * (x % 17) + (100_000.0 if entity == "1" else 0.0)
    return pd.DataFrame(
        {
            "SPT_DATE": dates,
            "SP_SECURITY_ID": security,
            "SPT_INSTRUMENT_ITEM_ID": trading,
            "SPT_CLOSE": close,
            "SPT_VOLUME": volume,
            "SPT_TOTAL_RETURN": daily_pct,
        }
    )


def _market(rows: int = 210) -> pd.DataFrame:
    dates = pd.bdate_range(end=TARGET_DATE, periods=rows)
    return pd.concat(
        [
            _market_for("1", "101", "SPT101", dates, slope=0.12),
            _market_for("2", "202", "SPT202", dates, slope=0.08),
            _market_for("3", "303", "SPT303", dates, slope=0.10),
            _market_for("4", "404", "SPT404", dates, slope=0.09),
        ],
        ignore_index=True,
    )


def test_market_slice_thresholds_are_bound_to_existing_rule100_owner() -> None:
    assert MIN_FACTOR_COVERAGE == OWNER_MIN_FACTOR_COVERAGE == 3
    assert MIN_HOLD_FACTOR_POSITIVES == OWNER_MIN_HOLD_FACTOR_POSITIVES == 2
    assert HARD_EXIT_DIST_SMA20 == OWNER_HARD_EXIT_DIST_SMA20 == pytest.approx(0.20)
    assert ACCUMULATION_DIST_MAX == OWNER_ACCUMULATION_DIST_MAX == pytest.approx(0.05)
    assert RULE100_PRODUCT_MAX_WEIGHT == pytest.approx(0.35)


def test_primary_security_master_excludes_ambiguous_and_never_uses_ticker_identity() -> None:
    raw = pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "1", "2"],
            "SP_SECURITY_ID": ["101", "102", "202"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT101", "SPT102", "SPT202"],
            "Ticker": ["AAA", "AAA2", "BBB"],
        }
    )
    admitted, excluded = normalize_primary_security_master(raw, frozen_entity_ids={"1", "2"})
    assert admitted["source_entity_id"].tolist() == ["2"]
    assert admitted["security_id"].tolist() == ["CIQSEC:202"]
    assert admitted["trading_item_id"].tolist() == ["SPT202"]
    assert excluded.set_index("source_entity_id").loc["1", "reason"] == "AMBIGUOUS_PRIMARY_SECURITY_MAPPING"


def test_primary_security_master_excludes_cross_entity_identity_collision() -> None:
    raw = pd.DataFrame(
        {
            "SP_ENTITY_ID": ["1", "2"],
            "SP_SECURITY_ID": ["101", "101"],
            "SPT_INSTRUMENT_ITEM_ID": ["SPT101", "SPT202"],
        }
    )
    admitted, excluded = normalize_primary_security_master(raw, frozen_entity_ids={"1", "2"})
    assert admitted.empty
    assert set(excluded["reason"]) == {"CROSS_ENTITY_SECURITY_ID_COLLISION"}


def test_build_ciq_market_slice_emits_current_targets_only_and_canonical_market_primitives() -> None:
    result = build_ciq_market_slice(
        security_master_raw=_master(),
        market_raw=_market(),
        fundamental_state=_fundamentals(),
        admission_time=ADMITTED_AT,
        target_date=TARGET_DATE,
    )

    # Entity 3 fails the existing >=3 factor-coverage law; entity 4 has enough
    # coverage but only one positive group and therefore remains in the market
    # universe with zero Rule100 target weight.
    assert set(result.security_map["source_entity_id"]) == {"1", "2", "4"}
    assert "INSUFFICIENT_FACTOR_COVERAGE" in set(result.exclusions["reason"])
    assert set(result.rule100_targets.columns) == {"CIQSEC:101", "CIQSEC:202", "CIQSEC:404"}
    assert result.rule100_targets.index.tolist() == [pd.Timestamp(TARGET_DATE)]
    assert result.total_returns.index.equals(result.rule100_targets.index)
    assert result.total_returns.columns.equals(result.rule100_targets.columns)

    # Product/AOV Rule100 semantics use the current 0.35 max-weight path. Two
    # eligible names consume 0.70 gross; the low-positive name stays zero.
    weights = result.rule100_targets.iloc[0]
    assert weights["CIQSEC:101"] == pytest.approx(0.35)
    assert weights["CIQSEC:202"] == pytest.approx(0.35)
    assert weights["CIQSEC:404"] == pytest.approx(0.0)
    assert float(weights.sum()) == pytest.approx(0.70)

    warmup = result.market_features.loc[result.market_features["date"].lt(pd.Timestamp(TARGET_DATE))]
    assert (warmup["quality"] == 0.0).all()
    assert (warmup["uncertainty"] == 1.0).all()
    assert warmup["factor_present_count"].isna().all()
    assert warmup["factor_positive_count"].isna().all()
    assert not warmup["sizing_eligible"].astype(bool).any()

    target_primitives = result.market_features.loc[result.market_features["date"].eq(pd.Timestamp(TARGET_DATE))]
    assert set(target_primitives["security_id"]) == set(result.rule100_targets.columns)
    assert target_primitives["trading_item_id"].str.startswith("SPT").all()
    assert np.isfinite(target_primitives[["realized_vol", "adv20", "quality", "exit_capacity", "regime", "uncertainty"]].to_numpy(dtype=float)).all()
    assert (target_primitives["realized_vol"] > 0).all()
    assert (target_primitives["adv20"] > 0).all()
    assert target_primitives["known_at"].nunique() == 1
    assert str(target_primitives["known_at"].iloc[0]) == "2026-08-07 17:30:00+00:00"
    assert result.metadata["historical_rule100_targets_emitted"] is False
    assert result.metadata["current_cut_only"] is True


def test_market_slice_rejects_target_before_fundamental_admission() -> None:
    with pytest.raises(ValueError, match="target_date_before_fundamental_admission"):
        build_ciq_market_slice(
            security_master_raw=_master(),
            market_raw=_market(),
            fundamental_state=_fundamentals(),
            admission_time=ADMITTED_AT,
            target_date="2026-08-06",
        )


def test_market_slice_excludes_names_without_sma200_history() -> None:
    short_market = _market(rows=199)
    with pytest.raises(ValueError, match="no_entities_after_market_integrity_filters|no_entities_with_target_vertical_primitives"):
        build_ciq_market_slice(
            security_master_raw=_master(),
            market_raw=short_market,
            fundamental_state=_fundamentals(),
            admission_time=ADMITTED_AT,
            target_date=TARGET_DATE,
        )


def test_market_slice_accepts_total_return_index_as_the_return_authority() -> None:
    market = _market().drop(columns=["SPT_TOTAL_RETURN"]).copy()
    market = market.sort_values(["SP_SECURITY_ID", "SPT_DATE"]).reset_index(drop=True)
    pct = 0.002 + 0.001 * np.sin(np.arange(len(market), dtype=float) / 7.0)
    market["SPT_TOTAL_RETURN_INDEX"] = 100.0 * (1.0 + pd.Series(pct)).groupby(market["SP_SECURITY_ID"]).cumprod()
    result = build_ciq_market_slice(
        security_master_raw=_master(),
        market_raw=market,
        fundamental_state=_fundamentals(),
        admission_time=ADMITTED_AT,
        target_date=TARGET_DATE,
    )
    assert set(result.market_features["return_mode"]) == {"TOTAL_RETURN_INDEX_PCT_CHANGE"}
    assert np.isfinite(result.total_returns.to_numpy(dtype=float)).all()


def test_market_builder_atomically_writes_three_risky_inputs_and_source_receipts(tmp_path: Path) -> None:
    master_path = tmp_path / "security_master.csv"
    market_path = tmp_path / "market.csv"
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _master().to_csv(master_path, index=False)
    _market().to_csv(market_path, index=False)
    _fundamentals().to_parquet(fundamentals_path, index=False)

    outputs = {
        "security_map_path": tmp_path / "intermediate/security_map.parquet",
        "exclusions_path": tmp_path / "intermediate/exclusions.parquet",
        "rule100_path": tmp_path / "current/rule100_targets.parquet",
        "primitives_path": tmp_path / "current/vertical_primitives.parquet",
        "returns_path": tmp_path / "current/total_returns.parquet",
        "security_receipt_path": tmp_path / "receipts/security.json",
        "market_receipt_path": tmp_path / "receipts/market.json",
    }
    summary = build_artifacts(
        security_master_path=master_path,
        market_history_path=market_path,
        fundamental_state_path=fundamentals_path,
        security_retrieved_at="2026-08-07T17:10:00Z",
        market_retrieved_at="2026-08-07T20:05:00Z",
        target_date=TARGET_DATE,
        now=datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
        **outputs,
    )
    assert summary["status"] == "THREE_RISKY_ASSET_FIRST_SEAL_INPUTS_ADMITTED"
    assert summary["canonical_security_count"] == 3
    assert all(path.exists() for path in outputs.values())

    rule100 = pd.read_parquet(outputs["rule100_path"])
    returns = pd.read_parquet(outputs["returns_path"])
    primitives = pd.read_parquet(outputs["primitives_path"])
    assert rule100["date"].astype(str).str.startswith(TARGET_DATE).all()
    assert returns.columns.equals(rule100.columns)
    assert {"security_id", "trading_item_id", "known_at", "technical_quality"}.issubset(primitives.columns)

    security_receipt = json.loads(outputs["security_receipt_path"].read_text(encoding="utf-8"))
    market_receipt = json.loads(outputs["market_receipt_path"].read_text(encoding="utf-8"))
    assert security_receipt["source_id"] == "SPCIQPRO:PRIMARY_SECURITY_MASTER"
    assert market_receipt["source_id"] == "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA"
    assert security_receipt["retrieved_at"] == "2026-08-07T17:10:00Z"
    assert market_receipt["retrieved_at"] == "2026-08-07T20:05:00Z"
    assert market_receipt["outputs"]["vertical_primitives"]["sha256"]


def test_current_cut_market_outputs_flow_through_actual_first_seal_and_reopen(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    raw_root.mkdir()
    master_path = raw_root / "security_master.csv"
    market_path = raw_root / "market.csv"
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _master().to_csv(master_path, index=False)
    _market().to_csv(market_path, index=False)
    _fundamentals().to_parquet(fundamentals_path, index=False)

    input_root = tmp_path / "current"
    receipt_root = tmp_path / "receipts"
    intermediate = tmp_path / "intermediate"
    security_receipt = receipt_root / "security.json"
    market_receipt = receipt_root / "market.json"
    build_artifacts(
        security_master_path=master_path,
        market_history_path=market_path,
        fundamental_state_path=fundamentals_path,
        security_retrieved_at="2026-08-07T17:10:00Z",
        market_retrieved_at="2026-08-07T20:05:00Z",
        target_date=TARGET_DATE,
        now=datetime(2026, 8, 7, 20, 10, tzinfo=UTC),
        security_map_path=intermediate / "security_map.parquet",
        exclusions_path=intermediate / "exclusions.parquet",
        rule100_path=input_root / "rule100_targets.parquet",
        primitives_path=input_root / "vertical_primitives.parquet",
        returns_path=input_root / "total_returns.parquet",
        security_receipt_path=security_receipt,
        market_receipt_path=market_receipt,
    )

    def fake_nyfed_fetch(url: str):
        assert url == SOFR_URL
        raw = json.dumps(
            {
                "refRates": [
                    {"effectiveDate": "2026-08-06", "percentRate": 5.30, "type": "SOFR"}
                ]
            }
        ).encode("utf-8")
        return raw, SOFR_URL

    sofr_receipt = receipt_root / "sofr.json"
    fetch_and_admit_sofr(
        now=datetime(2026, 8, 7, 19, 5, tzinfo=UTC),
        fetcher=fake_nyfed_fetch,
        raw_path=raw_root / "sofr.json",
        parquet_path=input_root / "official_sofr.parquet",
        receipt_path=sofr_receipt,
    )

    fundamentals_receipt = receipt_root / "fundamentals.json"
    receipt_root.mkdir(parents=True, exist_ok=True)
    fundamentals_receipt.write_text(
        json.dumps(
            {
                "source_id": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
                "retrieved_at": "2026-08-07T16:46:27Z",
                "raw_object_sha256": "b" * 64,
            }
        ) + "\n",
        encoding="utf-8",
    )
    build_decision_cut(
        rule100_path=input_root / "rule100_targets.parquet",
        primitives_path=input_root / "vertical_primitives.parquet",
        returns_path=input_root / "total_returns.parquet",
        sofr_path=input_root / "official_sofr.parquet",
        fundamentals_receipt_path=fundamentals_receipt,
        security_receipt_path=security_receipt,
        market_receipt_path=market_receipt,
        sofr_receipt_path=sofr_receipt,
        evaluation_start="2026-08-10T20:00:00Z",
        output_path=input_root / "decision_cut.json",
        cut_built_at=datetime(2026, 8, 7, 20, 15, tzinfo=UTC),
    )

    seal_result = run_first_seal(
        input_root=input_root,
        output_root=tmp_path / "aov0",
        sealed_at=datetime(2026, 8, 7, 20, 20, tzinfo=UTC),
    )
    assert seal_result["status"] == "SEAL_CANDIDATE_WRITTEN"
    assert seal_result["prospective_clock_started"] is False
    assert seal_result["financial_alpha_evidence"] == 0
    promoted = promote_seal_candidate(seal_result, output_root=tmp_path / "aov0")
    assert promoted["status"] == "PROSPECTIVE_CLOCK_STARTED"
    assert promoted["prospective_clock_started"] is True
    seal_path = Path(seal_result["seal_path"])
    reopened = reopen_prospective_seal(seal_path)
    assert reopened["seal_id"] == seal_result["seal_id"]
    assert reopened["outcome_status"] == "SEALED_NOT_OPENED"
    assert reopened["financial_alpha_evidence"] == 0
    repo_root = Path(__file__).resolve().parents[2]
    full_chain = reopen_prospective_seal_full_chain(seal_path, repo_root=repo_root)
    assert full_chain["status"] == "FULL_CHAIN_REOPEN_VERIFIED"
    completed = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts/aov0_reopen_seal.py"),
            "--seal",
            str(seal_path.resolve()),
            "--repo-root",
            str(repo_root),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    fresh = json.loads(completed.stdout)
    assert fresh["status"] == "FULL_CHAIN_REOPEN_VERIFIED"
    assert fresh["seal_id"] == seal_result["seal_id"]
    assert promoted["clock_start_receipt"]["seal_id"] == seal_result["seal_id"]


def test_market_builder_blocks_same_day_daily_bar_before_1600_et_without_outputs(tmp_path: Path) -> None:
    master_path = tmp_path / "security_master.csv"
    market_path = tmp_path / "market.csv"
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _master().to_csv(master_path, index=False)
    _market().to_csv(market_path, index=False)
    _fundamentals().to_parquet(fundamentals_path, index=False)
    outputs = {
        "security_map_path": tmp_path / "intermediate/security_map.parquet",
        "exclusions_path": tmp_path / "intermediate/exclusions.parquet",
        "rule100_path": tmp_path / "current/rule100_targets.parquet",
        "primitives_path": tmp_path / "current/vertical_primitives.parquet",
        "returns_path": tmp_path / "current/total_returns.parquet",
        "security_receipt_path": tmp_path / "receipts/security.json",
        "market_receipt_path": tmp_path / "receipts/market.json",
    }
    with pytest.raises(ValueError, match="current_daily_bar_not_complete_before_1600_et"):
        build_artifacts(
            security_master_path=master_path,
            market_history_path=market_path,
            fundamental_state_path=fundamentals_path,
            security_retrieved_at="2026-08-07T17:10:00Z",
            market_retrieved_at="2026-08-07T17:20:00Z",
            target_date=TARGET_DATE,
            now=datetime(2026, 8, 7, 18, 0, tzinfo=UTC),
            **outputs,
        )
    assert not any(path.exists() for path in outputs.values())


def test_market_builder_rejects_future_source_retrieval_time_without_outputs(tmp_path: Path) -> None:
    master_path = tmp_path / "security_master.csv"
    market_path = tmp_path / "market.csv"
    fundamentals_path = tmp_path / "fundamentals.parquet"
    _master().to_csv(master_path, index=False)
    _market().to_csv(market_path, index=False)
    _fundamentals().to_parquet(fundamentals_path, index=False)
    outputs = {
        "security_map_path": tmp_path / "intermediate/security_map.parquet",
        "exclusions_path": tmp_path / "intermediate/exclusions.parquet",
        "rule100_path": tmp_path / "current/rule100_targets.parquet",
        "primitives_path": tmp_path / "current/vertical_primitives.parquet",
        "returns_path": tmp_path / "current/total_returns.parquet",
        "security_receipt_path": tmp_path / "receipts/security.json",
        "market_receipt_path": tmp_path / "receipts/market.json",
    }
    with pytest.raises(ValueError, match="source_retrieval_time_in_future"):
        build_artifacts(
            security_master_path=master_path,
            market_history_path=market_path,
            fundamental_state_path=fundamentals_path,
            security_retrieved_at="2026-08-07T17:10:00Z",
            market_retrieved_at="2026-08-07T20:05:00Z",
            target_date=TARGET_DATE,
            now=datetime(2026, 8, 7, 20, 0, tzinfo=UTC),
            **outputs,
        )
    assert not any(path.exists() for path in outputs.values())
