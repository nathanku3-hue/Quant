from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from scripts import aov0_historical_pit_replay as replay


def _write_csv(path: Path, **columns: list[object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns).to_csv(path, index=False)
    return path


def _write_terminal_fixture(root: Path) -> tuple[Path, Path]:
    events = root / "terminal_events.csv"
    events.write_text(
        "source_entity_id,security_id,source_spt_item,last_trading_date,effective_date,cash_consideration,currency,event_type,source_authority,source_locator\n"
        "1,CIQSEC:101,SPT101,2025-08-15,2025-08-18,7.5,USD,CASH_MERGER_PREOPEN_TRADING_SUSPENSION,SEC:FIXTURE,https://www.sec.gov/fixture\n",
        encoding="utf-8",
    )
    receipt = root / "terminal_events.receipt.json"
    payload = {
        "schema_version": "aov0_historical_terminal_events_receipt_v1",
        "event_count": 1,
        "events_sha256": hashlib.sha256(events.read_bytes()).hexdigest(),
        "event_bindings": [
            {
                "source_entity_id": "1",
                "security_id": "CIQSEC:101",
                "source_spt_item": "SPT101",
                "last_trading_date": "2025-08-15",
                "effective_date": "2025-08-18",
                "cash_consideration": "7.5",
                "currency": "USD",
                "event_type": "CASH_MERGER_PREOPEN_TRADING_SUSPENSION",
                "source_authority": "SEC:FIXTURE",
                "source_locator": "https://www.sec.gov/fixture",
            }
        ],
        "current_screen_conditioned": False,
        "current_primary_security_conditioned": False,
        "financial_alpha_evidence": 0,
    }
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    return events, receipt


def _fake_a1_report(
    path: Path,
    *,
    admitted: bool = True,
    source_entity_ids: list[str] | None = None,
    security_master: Path | None = None,
) -> Path:
    source_entity_ids = source_entity_ids or ["1", "2"]
    if security_master is None:
        security_master = _write_csv(path.parent / "frozen_master.csv", SP_ENTITY_ID=source_entity_ids)
    membership = path.parent / "historical_membership.csv"
    membership.write_text("SP_ENTITY_ID\n" + "\n".join(source_entity_ids) + "\n", encoding="utf-8")
    receipt = path.parent / "historical_membership.receipt.json"
    receipt.write_text('{"fixture":true}\n', encoding="utf-8")
    historical_security_receipt = path.parent / "historical_security_master.receipt.json"
    historical_security_receipt.write_text('{"fixture":true}\n', encoding="utf-8")
    terminal_events, terminal_receipt = _write_terminal_fixture(path.parent)
    payload = {
        "schema_version": replay.REPORT_SCHEMA,
        "stage": "A1",
        "evidence_classification": (
            replay.A1_ADMITTED_CLASSIFICATION
            if admitted
            else replay.CURRENT_SCREEN_DIAGNOSTIC_CLASSIFICATION
        ),
        "source_cohort": {
            "frozen_company_count": len(source_entity_ids),
            "historical_screen_membership_reconstructed": admitted,
            "historical_primary_security_identity_reconstructed": admitted,
            "risk_set_mode": replay.HISTORICAL_SCREEN_FREEZE_MODE if admitted else None,
            "as_of_date": "2025-05-16" if admitted else None,
            "historical_primary_security_as_of_date": "2025-05-16" if admitted else None,
            "current_screen_conditioned": not admitted,
            "current_primary_security_conditioned": not admitted,
            "screen_law_hash": "fixture-screen-law" if admitted else None,
            "limitation": None if admitted else "CURRENT_FROZEN_109_COMPANY_SOURCE_COHORT",
        },
        "a1_minimum_gate": {
            "candidate_pass": admitted,
            "historical_universe_risk_set_pass": admitted,
            "historical_primary_security_identity_pass": admitted,
            "source_semantics_pass": True,
            "terminal_lifecycle_authority_pass": admitted,
        },
        "source_entity_ids": source_entity_ids,
        "security_ids": ["CIQSEC:101", "CIQSEC:202"],
        "input_sources": {
            "security_master": replay._source_manifest([security_master]),
            "historical_risk_set": {
                "membership": replay._source_manifest([membership]),
                "receipt": replay._source_manifest([receipt]),
            },
            "historical_security_master_receipt": (
                replay._source_manifest([historical_security_receipt]) if admitted else None
            ),
            "terminal_events": (
                {
                    "events": replay._source_manifest([terminal_events]),
                    "receipt": replay._source_manifest([terminal_receipt]),
                }
                if admitted
                else None
            ),
        },
        "financial_alpha_evidence": 0,
    }
    payload["report_content_hash"] = replay._canonical_json_hash(payload)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_cube_computed_at_is_derived_from_sealed_cube_bytes() -> None:
    cube = SimpleNamespace(
        frame=pd.DataFrame(
            {
                "computed_at": [
                    "2025-05-16T20:00:00Z",
                    "2025-05-19T20:00:00Z",
                ]
            }
        )
    )
    assert replay._cube_computed_at_iso(cube) == "2025-05-19T20:00:00+00:00"

    with pytest.raises(ValueError, match="historical_cube_computed_at_missing"):
        replay._cube_computed_at_iso(SimpleNamespace(frame=pd.DataFrame()))


def test_historical_ciq_capture_uses_original_filing_version_and_a2_freezes_query_producers() -> None:
    capture_paths = (
        replay.ROOT / "scripts/aov0_capture_ciq_historical_pit_fundamentals.ps1",
        replay.ROOT / "scripts/aov0_capture_ciq_historical_pit_fundamental_chunk.ps1",
        replay.ROOT / "scripts/aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1",
        replay.ROOT / "scripts/aov0_capture_ciq_historical_pit_transition_batch.ps1",
    )
    for path in capture_paths:
        text = path.read_text(encoding="utf-8")
        assert "FilingVer=Original" in text
        assert "FilingVer=Current/Restated" not in text

    for relative in (
        "scripts/aov0_capture_ciq_historical_market_chunk.ps1",
        "scripts/aov0_capture_ciq_historical_market_productquery.py",
        "scripts/aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1",
        "scripts/aov0_capture_ciq_historical_pit_transition_batch.ps1",
    ):
        assert relative in replay.FROZEN_IMPLEMENTATION_PATHS

    for relative in (
        "scripts/aov0_capture_ciq_historical_market_chunk.ps1",
        "scripts/aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1",
    ):
        text = (replay.ROOT / relative).read_text(encoding="utf-8")
        assert "Count-ne109" not in text
        assert "[Parameter(Mandatory=$true)][string]$Master" in text
    market_chunk_text = (replay.ROOT / "scripts/aov0_capture_ciq_historical_market_chunk.ps1").read_text(
        encoding="utf-8"
    )
    assert "[ValidateRange(1,20)][int]$ChunkDays=7" in market_chunk_text
    assert "historical_market_chunk_days_must_equal_frozen_7" not in market_chunk_text

    for driver_name in ("aov0_lane2_a1_driver.ps1", "aov0_lane2_a2_driver.ps1"):
        driver_text = (replay.ROOT / "scripts" / driver_name).read_text(encoding="utf-8")
        assert "& $py @args | Out-Host" in driver_text
        assert "-BootSeconds 10 | Out-Host" in driver_text

    productquery_path = replay.ROOT / "scripts/aov0_capture_ciq_historical_market_productquery.py"
    productquery_text = productquery_path.read_text(encoding="utf-8")
    assert "capitaliq.spglobal.com" in productquery_text
    assert "existing_session_reused" in productquery_text
    assert '"sign_in_performed": False' in productquery_text
    assert '"sign_out_performed": False' in productquery_text
    assert "temp_path.replace(path)" in productquery_text
    assert 'parser.add_argument("--resume", action="store_true")' in productquery_text
    assert "322797" in productquery_text
    assert "324251" in productquery_text
    assert "324277" in productquery_text


def test_current_screen_conditioned_diagnostic_cannot_freeze_a2(tmp_path: Path) -> None:
    diagnostic = _fake_a1_report(tmp_path / "diagnostic.json", admitted=False)
    with pytest.raises(ValueError, match="a1_not_admitted_historical_pit_cannot_freeze_a2"):
        replay.create_freeze(
            argparse.Namespace(
                a1_report=diagnostic,
                a2_start="2026-06-05",
                a2_end="2026-08-07",
                out=tmp_path / "a2" / "freeze.json",
            )
        )


def test_source_semantics_reject_current_restated_or_non_spg() -> None:
    period = pd.DataFrame(
        {
            "retrieved_at_utc": ["2026-08-08T20:00:00Z"],
            "provider_function": ["SPG"],
            "provider_metric": ["IQ_PERIOD_END"],
            "relative_period": ["FQ0"],
            "filing_version": ["Original"],
        }
    )
    transition = pd.DataFrame(
        {
            "retrieved_at_utc": ["2026-08-08T20:00:01Z"],
            "provider_function": ["SPG"],
            "filing_version": ["Original"],
        }
    )
    semantics = replay._validate_historical_pit_source_semantics(period, transition)
    assert semantics["filing_version"] == "Original"
    assert semantics["retrieval_timestamp_bound"] is True

    restated = transition.copy()
    restated["filing_version"] = "Current/Restated"
    with pytest.raises(ValueError, match="filing_version_not_original"):
        replay._validate_historical_pit_source_semantics(period, restated)

    non_spg = period.copy()
    non_spg["provider_function"] = "OTHER"
    with pytest.raises(ValueError, match="provider_function_not_spg"):
        replay._validate_historical_pit_source_semantics(non_spg, transition)


def test_transition_planner_uses_authoritative_missing_fq0_gate(tmp_path: Path) -> None:
    period = _write_csv(
        tmp_path / "period.csv",
        as_of_date=["2025-05-02", "2025-05-02"],
        source_entity_id=["1", "2"],
        fq0_period_end=["2025-03-31", ""],
    )
    out = tmp_path / "transitions.csv"
    with pytest.raises(ValueError, match="aov0_historical_period_matrix_fq0_missing"):
        replay.plan_transitions(
            argparse.Namespace(period_part=[period], out=out, refuse_existing=True)
        )
    assert not out.exists()


def test_transition_planner_matches_authoritative_plan(tmp_path: Path) -> None:
    period = _write_csv(
        tmp_path / "period.csv",
        as_of_date=["2025-05-02", "2025-05-09", "2025-05-02", "2025-05-09"],
        source_entity_id=["1", "1", "2", "2"],
        fq0_period_end=["2025-03-31", "2025-03-31", "2024-12-31", "2025-03-31"],
    )
    out = tmp_path / "transitions.csv"
    metadata = replay.plan_transitions(
        argparse.Namespace(period_part=[period], out=out, refuse_existing=True)
    )
    planned = pd.read_csv(out, dtype=str)
    assert metadata["transition_queries"] == 3
    assert set(planned["transition_reason"]) == {"INITIAL", "FQ0_PERIOD_CHANGE"}
    assert not planned["fq0_period_end"].isna().any()


def test_a2_fundamental_plan_inherits_frozen_104_source_cohort(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_entity_ids = [str(i) for i in range(104)]
    master = _write_csv(tmp_path / "master_104.csv", SP_ENTITY_ID=source_entity_ids)
    a1 = _fake_a1_report(
        tmp_path / "a1.json",
        source_entity_ids=source_entity_ids,
        security_master=master,
    )
    freeze_path = tmp_path / "a2" / "freeze.json"
    replay.create_freeze(
        argparse.Namespace(
            a1_report=a1,
            a2_start="2026-06-12",
            a2_end="2026-06-19",
            out=freeze_path,
        )
    )
    market_path = _write_csv(tmp_path / "market.csv", placeholder=[1])
    market_dates = pd.bdate_range("2026-06-12", "2026-06-19")
    monkeypatch.setattr(
        replay,
        "build_historical_market_panel",
        lambda **_kwargs: SimpleNamespace(frame=pd.DataFrame({"date": market_dates})),
    )
    out = tmp_path / "a2_plan.csv"
    metadata = replay.plan_fundamentals(
        argparse.Namespace(
            security_master=master,
            market_part=[market_path],
            start="2026-06-12",
            end="2026-06-19",
            risk_set_membership=None,
            risk_set_receipt=None,
            historical_security_master_receipt=None,
            freeze=freeze_path,
            out=out,
            refuse_existing=True,
        )
    )
    assert metadata["frozen_entity_count"] == 104
    assert metadata["historical_risk_set_admitted"] is True
    assert metadata["historical_primary_security_identity_admitted"] is True
    assert metadata["planner_mode"] == "A2_FROZEN_SOURCE_COHORT"
    assert pd.read_csv(out, dtype=str)["as_of_date"].tolist() == ["2026-06-12", "2026-06-19"]

    with pytest.raises(ValueError, match="a2_plan_window_does_not_match_freeze"):
        replay.plan_fundamentals(
            argparse.Namespace(
                security_master=master,
                market_part=[market_path],
                start="2026-06-12",
                end="2026-06-26",
                risk_set_membership=None,
                risk_set_receipt=None,
                historical_security_master_receipt=None,
                freeze=freeze_path,
                out=tmp_path / "bad_plan.csv",
                refuse_existing=True,
            )
        )


def test_a2_freeze_binds_result_evidence_and_query_meter_paths(tmp_path: Path) -> None:
    a1 = _fake_a1_report(tmp_path / "a1.json")
    freeze_path = tmp_path / "a2" / "freeze.json"
    args = argparse.Namespace(
        a1_report=a1,
        a2_start="2026-06-05",
        a2_end="2026-08-07",
        out=freeze_path,
    )
    payload = replay.create_freeze(args)

    assert payload["financial_alpha_evidence"] == 0
    assert payload["query_law"]["query_lock_written_before_outcome_evaluation"] is True
    assert payload["frozen_source_entity_ids"] == ["1", "2"]
    assert payload["a1_active_security_ids"] == ["CIQSEC:101", "CIQSEC:202"]
    assert payload["a2_paths"] == {
        "result": (freeze_path.parent.resolve() / "a2_result.json").as_posix(),
        "evidence_root": (freeze_path.parent.resolve() / "evidence").as_posix(),
        "query_lock": (freeze_path.parent.resolve() / "a2_query_lock.json").as_posix(),
        "query_receipt": (freeze_path.parent.resolve() / "a2_query_receipt.json").as_posix(),
    }
    verified = replay.verify_freeze(freeze_path)
    assert verified["freeze_content_hash"] == payload["freeze_content_hash"]

    tampered = json.loads(freeze_path.read_text(encoding="utf-8"))
    tampered["a2_window"]["end"] = "2026-08-08"
    freeze_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(ValueError, match="a2_freeze_content_hash_invalid"):
        replay.verify_freeze(freeze_path)


def test_a2_query_lock_is_written_before_outcome_evaluation_and_blocks_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_entity_ids = [str(i) for i in range(109)]
    master = _write_csv(tmp_path / "master.csv", SP_ENTITY_ID=source_entity_ids)
    a1 = _fake_a1_report(
        tmp_path / "a1.json",
        source_entity_ids=source_entity_ids,
        security_master=master,
    )
    freeze_path = tmp_path / "a2" / "freeze.json"
    freeze = replay.create_freeze(
        argparse.Namespace(
            a1_report=a1,
            a2_start="2026-06-05",
            a2_end="2026-08-07",
            out=freeze_path,
        )
    )
    freeze_ts = pd.Timestamp(freeze["created_at_utc"])
    retrieved = (freeze_ts + pd.Timedelta(seconds=1)).isoformat()

    market = _write_csv(tmp_path / "market.csv", placeholder=[1])
    period = _write_csv(
        tmp_path / "period.csv",
        as_of_date=["2026-06-05"],
        source_entity_id=["0"],
        fq0_period_end=["2026-03-31"],
        retrieved_at_utc=[retrieved],
    )
    transition = _write_csv(
        tmp_path / "transition.csv",
        as_of_date=["2026-06-05"],
        source_entity_id=["0"],
        relative_period=["FQ0"],
        period_end=["2026-03-31"],
        retrieved_at_utc=[retrieved],
    )
    sofr = tmp_path / "sofr.json"
    sofr.write_text('{"refRates":[{"effectiveDate":"2026-06-04","percentRate":3.5}]}', encoding="utf-8")

    observed_run_kwargs: dict[str, object] = {}

    def fail_after_lock(**kwargs):
        observed_run_kwargs.update(kwargs)
        raise RuntimeError("synthetic_outcome_evaluation_failure")

    monkeypatch.setattr(replay, "_run_window", fail_after_lock)
    args = argparse.Namespace(
        stage="A2",
        security_master=master,
        market_part=[market],
        period_part=[period],
        transition_part=[transition],
        sofr_raw=sofr,
        start="2026-06-05",
        end="2026-08-07",
        evidence_root=Path(freeze["a2_paths"]["evidence_root"]),
        out=Path(freeze["a2_paths"]["result"]),
        freeze=freeze_path,
        risk_set_membership=None,
        risk_set_receipt=None,
        historical_security_master_receipt=None,
        refuse_existing=False,
    )

    with pytest.raises(RuntimeError, match="synthetic_outcome_evaluation_failure"):
        replay.run_stage(args)

    query_lock = Path(freeze["a2_paths"]["query_lock"])
    assert query_lock.is_file()
    assert observed_run_kwargs["required_security_ids"] == ["CIQSEC:101", "CIQSEC:202"]
    assert observed_run_kwargs["expected_source_entity_ids"] == source_entity_ids
    lock_payload = json.loads(query_lock.read_text(encoding="utf-8"))
    assert lock_payload["schema_version"] == replay.QUERY_LOCK_SCHEMA
    assert lock_payload["evaluation_query_count_committed"] == 1
    assert lock_payload["second_evaluation_forbidden"] is True
    assert lock_payload["frozen_source_entity_count"] == 109
    assert lock_payload["frozen_active_security_count"] == 2
    assert lock_payload["frozen_security_ids"] == ["CIQSEC:101", "CIQSEC:202"]
    assert not args.out.exists()

    with pytest.raises(FileExistsError, match="a2_query_already_consumed"):
        replay.run_stage(args)


def test_a2_capture_must_be_strictly_after_freeze(tmp_path: Path) -> None:
    freeze_time = "2026-08-08T20:00:00Z"
    period = _write_csv(
        tmp_path / "period.csv",
        retrieved_at_utc=["2026-08-08T20:00:00Z"],
    )
    transition = _write_csv(
        tmp_path / "transition.csv",
        retrieved_at_utc=["2026-08-08T20:00:01Z"],
    )
    with pytest.raises(ValueError, match="a2_heldout_pit_capture_not_after_freeze"):
        replay._assert_a2_capture_after_freeze([period], [transition], freeze_time)
