from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from research.transition_recognition_v0.expectations_source_admit import (
    CANONICAL_ROW_KEYS,
    CIQ_PROVIDER,
    CRV1_EXPECTATIONS_SOURCE_ID,
    FAMILY_ID,
    HOLD_TERMINAL,
    NEXT_ON_HOLD,
    NEXT_ON_PASS,
    PASS_TERMINAL,
    RAW_CAPTURE_SCHEMA,
    REVISION_CONSTRUCTION_ID,
    REVISION_ORIGIN_DERIVED,
    REVISION_ORIGIN_DIRECT,
    SEMANTICS_SCHEMA,
    SLICE_ID,
    SOURCE_RECEIPT_SCHEMA,
    TR_EXPECTATIONS_SOURCE_ID,
    TR_FAMILY_AUTHORITY,
    TR_V0_FAMILY_DATA_CONTRACT,
    evaluate_source_admission,
    semantics_sha256,
    sha256_file,
)

AS_OF = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "docs/architecture/transition_recognition_v0_expectations_source_admit_v1.json"
EVIDENCE = ROOT / "docs/context/e2e_evidence/tr_v0_expectations_source_admit_1.json"


def _direct_semantics() -> dict:
    return {
        "schema_version": SEMANTICS_SCHEMA,
        "status": "EXACT_BOUND",
        "provider": CIQ_PROVIDER,
        "provider_transport": "BOUND_PROVIDER_TRANSPORT_TEST_CONTRACT",
        "identity": {
            "namespace": "CIQSEC",
            "provider_identity_field": "BOUND_PROVIDER_SECURITY_ID_FIELD",
            "law": "provider security identity maps deterministically to one CIQSEC identity; ticker is never authority",
        },
        "historical_as_of": {
            "provider_function_or_endpoint": "BOUND_PROVIDER_HISTORICAL_ESTIMATE_FUNCTION",
            "law": "request binds an explicit historical knowledge timestamp and never returns a later vintage",
        },
        "publication_availability": {
            "law": "available_at is the provider-observable publication/availability timestamp; available_at <= decision_as_of",
        },
        "forecast_period": {
            "eps_fy1_law": "FY1 is the provider-designated first forward fiscal-year consensus at the observation vintage",
            "forecast_period_end_field": "BOUND_PROVIDER_FORECAST_PERIOD_END_FIELD",
        },
        "source_independence": {
            "recognition_source_is_not_reality_artifact": True,
            "family_authority_is_tr_specific": True,
        },
        "measures": {
            "EPS_FY1": {
                "origin": REVISION_ORIGIN_DIRECT,
                "provider_field_or_function": "BOUND_PROVIDER_EPS_FY1_FIELD",
                "provider_period_argument": "BOUND_PROVIDER_FY1_ARGUMENT",
            },
            "EPS_FY1_REVISION_30D": {
                "origin": REVISION_ORIGIN_DIRECT,
                "provider_field_or_function": "BOUND_PROVIDER_EPS_REV_30D_FIELD",
                "provider_period_argument": "BOUND_PROVIDER_FY1_ARGUMENT",
            },
            "EPS_FY1_REVISION_90D": {
                "origin": REVISION_ORIGIN_DIRECT,
                "provider_field_or_function": "BOUND_PROVIDER_EPS_REV_90D_FIELD",
                "provider_period_argument": "BOUND_PROVIDER_FY1_ARGUMENT",
            },
        },
    }


def _derived_semantics() -> dict:
    semantics = _direct_semantics()
    for measure, lookback in (
        ("EPS_FY1_REVISION_30D", 30),
        ("EPS_FY1_REVISION_90D", 90),
    ):
        semantics["measures"][measure] = {
            "origin": REVISION_ORIGIN_DERIVED,
            "construction_id": REVISION_CONSTRUCTION_ID,
            "lookback_calendar_days": lookback,
            "base_measure": "EPS_FY1",
            "forecast_period_alignment": "SAME_FORECAST_PERIOD_END",
            "vintage_selection_law": "LATEST_PRESENT_AVAILABLE_AT_OR_BEFORE_LOOKBACK_CUTOFF",
            "formula": "CURRENT_EPS_FY1_MINUS_LOOKBACK_EPS_FY1",
        }
    return semantics


def _row(
    *,
    measure: str,
    value: float | None,
    available_at: str,
    observed_at: str | None = None,
    security_id: str = "CIQSEC:IQ101",
    forecast_period_end: str | None = "2027-12-31",
    coverage_status: str = "PRESENT",
    missingness_reason: str | None = None,
    **extra: object,
) -> dict:
    return {
        "security_id": security_id,
        "measure": measure,
        "value": value,
        "forecast_period_end": forecast_period_end,
        "observed_at": observed_at or available_at,
        "available_at": available_at,
        "epistemic_class": "OBSERVED_CONSENSUS",
        "coverage_status": coverage_status,
        "missingness_reason": missingness_reason,
        **extra,
    }


def _direct_rows() -> list[dict]:
    at = "2026-08-11T20:00:00Z"
    return [
        _row(measure="EPS_FY1", value=5.25, available_at=at),
        _row(measure="EPS_FY1_REVISION_30D", value=0.20, available_at=at),
        _row(measure="EPS_FY1_REVISION_90D", value=0.45, available_at=at),
    ]


def _write_custody(tmp_path: Path, *, semantics: dict, rows: list[dict]) -> tuple[Path, Path]:
    raw_path = tmp_path / "ciq_expectations_raw.json"
    raw_path.write_text(
        json.dumps(
            {
                "schema_version": RAW_CAPTURE_SCHEMA,
                "provider": CIQ_PROVIDER,
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    receipt_path = tmp_path / "tr_v0_expectations.receipt.json"
    receipt = {
        "schema_version": SOURCE_RECEIPT_SCHEMA,
        "slice_id": SLICE_ID,
        "family_id": FAMILY_ID,
        "source_id": TR_EXPECTATIONS_SOURCE_ID,
        "provider": CIQ_PROVIDER,
        "retrieved_at": "2026-08-11T21:00:00Z",
        "raw_object_path": raw_path.name,
        "raw_object_sha256": sha256_file(raw_path),
        "semantics_sha256": semantics_sha256(semantics),
        "license_scope": "LOCAL_LICENSED_PROVIDER_BYTES_NO_REDISTRIBUTION",
        "retention_class": "LOCAL_PROVIDER_EVIDENCE",
        "family_authority": TR_FAMILY_AUTHORITY,
        "crv1_artifact_authority_reused": False,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return raw_path, receipt_path


def test_current_live_slice_holds_at_gs0_without_inventing_source_bytes() -> None:
    architecture = json.loads(ARCHITECTURE.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert architecture["slice_id"] == SLICE_ID
    assert architecture["terminal"] == HOLD_TERMINAL
    assert architecture["gate_results"]["G-S0"]["status"] == "HOLD"
    assert architecture["source_semantics"]["status"] == "UNBOUND"
    assert architecture["provider_bytes_landed"] is False
    assert architecture["returns_join"] is False
    assert architecture["debit"] == 0
    assert evidence["terminal"] == HOLD_TERMINAL
    assert evidence["failed_gate"] == "G-S0"
    assert evidence["financial_alpha_evidence"] == 0


def test_family_contract_and_source_authority_are_tr_specific_not_crv1() -> None:
    assert TR_V0_FAMILY_DATA_CONTRACT.family_id == FAMILY_ID
    assert set(TR_V0_FAMILY_DATA_CONTRACT.allowed_expectation_surface) == {
        "EPS_FY1",
        "EPS_FY1_REVISION_30D",
        "EPS_FY1_REVISION_90D",
    }
    assert TR_EXPECTATIONS_SOURCE_ID != CRV1_EXPECTATIONS_SOURCE_ID
    assert TR_V0_FAMILY_DATA_CONTRACT.primary_label_spec_id == "UNSET_THIS_SLICE_NO_OUTCOMES"


def test_exact_direct_source_semantics_custody_and_pit_rows_can_pass(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=_direct_rows())
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == PASS_TERMINAL
    assert decision.failed_gate is None
    assert decision.next == NEXT_ON_PASS
    assert len(decision.admitted_rows) == 3
    assert {row["measure"] for row in decision.admitted_rows} == {
        "EPS_FY1",
        "EPS_FY1_REVISION_30D",
        "EPS_FY1_REVISION_90D",
    }
    assert all(set(row) == CANONICAL_ROW_KEYS for row in decision.admitted_rows)
    assert all(row["source_id"] == TR_EXPECTATIONS_SOURCE_ID for row in decision.admitted_rows)
    assert all(row["source_receipt_sha256"] == sha256_file(receipt_path) for row in decision.admitted_rows)


def test_deterministic_revision_construction_is_same_fpe_outcome_blind_and_explicit_missing(tmp_path: Path) -> None:
    semantics = _derived_semantics()
    rows = [
        _row(measure="EPS_FY1", value=4.0, available_at="2026-01-31T20:00:00Z"),
        _row(measure="EPS_FY1", value=4.5, available_at="2026-04-01T20:00:00Z"),
        _row(measure="EPS_FY1", value=5.0, available_at="2026-05-10T20:00:00Z"),
    ]
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == PASS_TERMINAL
    keyed = {(row["measure"], row["available_at"]): row for row in decision.admitted_rows}
    current_30 = keyed[("EPS_FY1_REVISION_30D", "2026-05-10T20:00:00.000000Z")]
    current_90 = keyed[("EPS_FY1_REVISION_90D", "2026-05-10T20:00:00.000000Z")]
    assert current_30["value"] == pytest.approx(0.5)
    assert current_30["coverage_status"] == "PRESENT"
    assert current_90["value"] == pytest.approx(1.0)
    assert current_90["coverage_status"] == "PRESENT"
    first_30 = keyed[("EPS_FY1_REVISION_30D", "2026-01-31T20:00:00.000000Z")]
    assert first_30["coverage_status"] == "MISSING_HISTORY"
    assert first_30["value"] is None
    assert "NO_SAME_FPE_PRESENT_EPS_FY1" in first_30["missingness_reason"]


def test_unbound_semantics_fail_fast_at_gs0_before_custody() -> None:
    semantics = _direct_semantics()
    semantics["status"] = "UNBOUND"
    decision = evaluate_source_admission(decision_as_of=AS_OF, semantics=semantics)
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S0"
    assert decision.reason == "EXACT_CIQ_SOURCE_SEMANTICS_UNBOUND"
    assert decision.next == NEXT_ON_HOLD


def test_crv1_receipt_cannot_be_relabelled_as_tr_authority(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=_direct_rows())
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["source_id"] = CRV1_EXPECTATIONS_SOURCE_ID
    receipt["crv1_artifact_authority_reused"] = True
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S1"
    assert decision.reason == "CRV1_ARTIFACT_AS_TR_AUTHORITY_FORBIDDEN"


def test_raw_byte_hash_mutation_fails_custody(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=_direct_rows())
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw["rows"][0]["value"] = 999.0
    raw_path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S1"
    assert decision.reason == "RAW_OBJECT_SHA256_MISMATCH"


def test_future_available_at_fails_pit_validation(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    rows = _direct_rows()
    rows[0]["available_at"] = "2026-08-13T20:00:00Z"
    rows[0]["observed_at"] = "2026-08-13T20:00:00Z"
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S2"
    assert decision.reason == "AVAILABLE_AT_AFTER_DECISION_AS_OF"


def test_ticker_fallback_or_extra_identity_field_fails_closed(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    rows = _direct_rows()
    rows[0]["ticker"] = "TEST"
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S2"
    assert decision.reason == "RAW_EXPECTATION_ROW_FIELDS_INVALID_NO_TICKER_FALLBACK"


def test_duplicate_security_measure_available_at_fails_closed(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    rows = _direct_rows()
    rows.append(dict(rows[0]))
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S2"
    assert decision.reason == "DUPLICATE_SECURITY_MEASURE_AVAILABLE_AT_KEY"


def test_parked_or_unknown_measure_cannot_enter_source_slice(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    rows = _direct_rows()
    rows[0]["measure"] = "EPS_FY2"
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S2"
    assert decision.reason == "UNKNOWN_OR_PARKED_EXPECTATION_MEASURE:EPS_FY2"


def test_observed_at_after_available_at_fails_pit_validation(tmp_path: Path) -> None:
    semantics = _direct_semantics()
    rows = _direct_rows()
    rows[0]["observed_at"] = "2026-08-11T21:00:00Z"
    rows[0]["available_at"] = "2026-08-11T20:00:00Z"
    raw_path, receipt_path = _write_custody(tmp_path, semantics=semantics, rows=rows)
    decision = evaluate_source_admission(
        decision_as_of=AS_OF,
        semantics=semantics,
        raw_path=raw_path,
        source_receipt_path=receipt_path,
    )
    assert decision.terminal == HOLD_TERMINAL
    assert decision.failed_gate == "G-S2"
    assert decision.reason == "OBSERVED_AT_AFTER_AVAILABLE_AT"
