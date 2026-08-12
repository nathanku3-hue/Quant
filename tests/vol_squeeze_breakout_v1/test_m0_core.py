from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta
import math
from pathlib import Path
import statistics

import pandas as pd
import pytest

from core.gv_fs0_canonical import domain_hash
from research.alpha_pit_v1.contracts import (
    AlphaPITBackendV1,
    ArtifactRef,
    ResearchMode,
    VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT,
)
from research.alpha_pit_v1.manifests import build_artifact_ref, canonical_value
from research.alpha_pit_v1.session import open_alpha_pit_session
from research.vol_squeeze_breakout_v1.contracts import (
    CONFIRMATION_ROLE_ID,
    FAMILY_DATA_CONTRACT,
    FAMILY_ID,
    GUARDIAN_CONTRACT_SHA256,
    IMPLEMENTATION_ID,
    MARKET_HISTORY_ARTIFACT_TYPE,
    MARKET_HISTORY_SCHEMA,
    RISK_SET_SPEC_ID,
    SEARCH_FAMILY_ID,
    TRIAL_BUDGET_MAX,
    validate_vsb_contract,
)
from research.vol_squeeze_breakout_v1.features import compute_m0_features
from research.vol_squeeze_breakout_v1.model import score_m0_features
from research.vol_squeeze_breakout_v1.pit_packet import build_vsb_input_packet, verify_vsb_input_packet
from research.vol_squeeze_breakout_v1.runner import (
    seal_m0_predictions,
    verify_prediction_batch,
)


AS_OF = datetime(2026, 8, 10, 21, 0, tzinfo=UTC)
DECISION_DATE = "2026-08-10"
RISK_SOURCE_RECEIPT = {
    "source_id": "FIXTURE:VSB:RISK_SET",
    "provider": "DETERMINISTIC_FIXTURE_ONLY",
    "retrieved_at": "2026-08-10T20:15:00.000000Z",
    "observed_range_start": DECISION_DATE,
    "observed_range_end": DECISION_DATE,
    "raw_receipt_path": "fixture://vsb/risk_set",
    "raw_receipt_sha256": domain_hash("VSB:TEST:RISK_RECEIPT", {"version": 1}),
    "parser_id": "vsb_test_risk_parser_v1",
    "parser_sha256": domain_hash("VSB:TEST:RISK_PARSER", {"version": 1}),
    "license_scope": "TEST_ONLY",
    "retention_class": "TEST_FIXTURE",
}
MARKET_SOURCE_RECEIPT = {
    "source_id": "FIXTURE:VSB:MARKET_HISTORY",
    "provider": "DETERMINISTIC_FIXTURE_ONLY",
    "retrieved_at": "2026-08-10T20:30:00.000000Z",
    "observed_range_start": "2026-05-19",
    "observed_range_end": DECISION_DATE,
    "raw_receipt_path": "fixture://vsb/market_history",
    "raw_receipt_sha256": domain_hash("VSB:TEST:MARKET_RECEIPT", {"version": 1}),
    "parser_id": "vsb_test_market_parser_v1",
    "parser_sha256": domain_hash("VSB:TEST:MARKET_PARSER", {"version": 1}),
    "license_scope": "TEST_ONLY",
    "retention_class": "TEST_FIXTURE",
}


class VSBFixtureBackend(AlphaPITBackendV1):
    def __init__(self, risk_set: ArtifactRef) -> None:
        self._risk_set = risk_set

    def risk_set(self, *, as_of: datetime, research_mode: ResearchMode) -> ArtifactRef:
        return self._risk_set

    def observations(self, *, ids, fields, as_of, research_mode):  # pragma: no cover - forbidden test seam
        raise AssertionError("vsb_fixture_observations_should_not_be_called")

    def source_claims(self, *, ids, as_of, research_mode):  # pragma: no cover - forbidden test seam
        raise AssertionError("vsb_fixture_claims_should_not_be_called")

    def expectations(self, *, ids, as_of, research_mode):  # pragma: no cover - forbidden test seam
        raise AssertionError("vsb_fixture_expectations_should_not_be_called")

    def outcomes(self, *, risk_set_id: str, label_spec_id: str):  # pragma: no cover - forbidden test seam
        raise AssertionError("vsb_fixture_outcomes_should_not_be_called")


def _coverage(count: int) -> dict[str, object]:
    return {
        "requested_security_count": count,
        "returned_security_count": count,
        "requested_field_count": None,
        "present_count": count,
        "missing_count": 0,
        "not_entitled_count": 0,
        "stale_count": 0,
        "coverage_rate": "1",
        "missingness_by_reason": {},
    }


def _risk_set_ref(mode: ResearchMode = ResearchMode.CONFIRMATORY) -> ArtifactRef:
    rows = [
        {
            "security_id": "CIQSEC:IQ101",
            "company_id": "COMPANY:101",
            "trading_item_id": "SPT101",
            "primary_listing_id": "PRIMARY:IQ101",
            "membership_effective_at": "2026-08-10T20:00:00.000000Z",
            "observed_at": "2026-08-10T20:00:00.000000Z",
            "available_at": "2026-08-10T20:10:00.000000Z",
            "source_id": RISK_SOURCE_RECEIPT["source_id"],
            "source_receipt_sha256": RISK_SOURCE_RECEIPT["raw_receipt_sha256"],
            "identity_receipt_sha256": RISK_SOURCE_RECEIPT["raw_receipt_sha256"],
            "eligibility_status": "ELIGIBLE",
            "schema_version": "alpha_pit_risk_set_row_v1",
        },
        {
            "security_id": "CIQSEC:IQ202",
            "company_id": "COMPANY:202",
            "trading_item_id": "SPT202",
            "primary_listing_id": "PRIMARY:IQ202",
            "membership_effective_at": "2026-08-10T20:00:00.000000Z",
            "observed_at": "2026-08-10T20:00:00.000000Z",
            "available_at": "2026-08-10T20:10:00.000000Z",
            "source_id": RISK_SOURCE_RECEIPT["source_id"],
            "source_receipt_sha256": RISK_SOURCE_RECEIPT["raw_receipt_sha256"],
            "identity_receipt_sha256": RISK_SOURCE_RECEIPT["raw_receipt_sha256"],
            "eligibility_status": "ELIGIBLE",
            "schema_version": "alpha_pit_risk_set_row_v1",
        },
    ]
    risk_set_id = domain_hash("VSB:TEST:RISK_SET", {"as_of": AS_OF.isoformat(), "rows": rows})
    payload = {
        "risk_set_id": risk_set_id,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": RISK_SET_SPEC_ID,
        "as_of": "2026-08-10T21:00:00.000000Z",
        "rows": rows,
        "row_count": len(rows),
        "exclusion_counts": {},
    }
    return build_artifact_ref(
        artifact_type="RISK_SET",
        research_mode=mode,
        request={"as_of": "2026-08-10T21:00:00.000000Z"},
        payload=payload,
        as_of=AS_OF,
        created_at="2026-08-10T21:00:01.000000Z",
        risk_set_id=risk_set_id,
        source_receipts=[RISK_SOURCE_RECEIPT],
        coverage_summary=_coverage(2),
        family_contract=VOL_SQUEEZE_BREAKOUT_FAMILY_DATA_CONTRACT,
        fixture=True,
    )


def _return_path() -> list[float]:
    return [0.02 if index % 2 == 0 else -0.02 for index in range(40)] + [
        0.005 if index % 2 == 0 else -0.005 for index in range(20)
    ]


def _market_rows() -> list[dict[str, object]]:
    dates = pd.bdate_range(end=DECISION_DATE, periods=60)
    returns = _return_path()
    rows: list[dict[str, object]] = []
    for security_id, base, breakout in (
        ("CIQSEC:IQ101", 100.0, True),
        ("CIQSEC:IQ202", 80.0, False),
    ):
        closes = [base + index * 0.1 for index in range(59)]
        prior_high = max(closes[-20:])
        closes.append(prior_high * (1.05 if breakout else 0.99))
        volumes = [100_000.0] * 59 + [200_000.0]
        for index, stamp in enumerate(dates):
            day = stamp.date().isoformat()
            rows.append(
                {
                    "security_id": security_id,
                    "session_date": day,
                    "close": closes[index],
                    "total_return_1d": returns[index],
                    "volume": volumes[index],
                    "observed_at": f"{day}T20:00:00.000000Z",
                    "available_at": f"{day}T20:05:00.000000Z",
                    "coverage_status": "PRESENT",
                }
            )
    return rows


def _market_history_ref(
    *,
    risk_set_id: str,
    rows: list[dict[str, object]] | None = None,
    mode: ResearchMode = ResearchMode.CONFIRMATORY,
) -> ArtifactRef:
    materialized = _market_rows() if rows is None else rows
    payload = {
        "schema_version": MARKET_HISTORY_SCHEMA,
        "family_id": FAMILY_ID,
        "risk_set_id": risk_set_id,
        "decision_session_date": DECISION_DATE,
        "rows": materialized,
        "row_count": len(materialized),
    }
    return build_artifact_ref(
        artifact_type=MARKET_HISTORY_ARTIFACT_TYPE,
        research_mode=mode,
        request={"risk_set_id": risk_set_id, "decision_session_date": DECISION_DATE},
        payload=payload,
        as_of=AS_OF,
        created_at="2026-08-10T21:00:01.000000Z",
        risk_set_id=risk_set_id,
        source_receipts=[MARKET_SOURCE_RECEIPT],
        coverage_summary=_coverage(2),
        family_contract=FAMILY_DATA_CONTRACT,
        fixture=True,
    )


def _api_and_history(
    *,
    rows: list[dict[str, object]] | None = None,
    mode: ResearchMode = ResearchMode.CONFIRMATORY,
):
    risk_ref = _risk_set_ref(mode)
    api = open_alpha_pit_session(
        mode=mode,
        family_id=FAMILY_ID,
        decision_context_id="vsb-test-decision-1",
        backend=VSBFixtureBackend(risk_ref),
        family_contract=FAMILY_DATA_CONTRACT,
    )
    history = _market_history_ref(risk_set_id=str(risk_ref.payload["risk_set_id"]), rows=rows, mode=mode)
    return api, history


def _packet(*, rows: list[dict[str, object]] | None = None):
    api, history = _api_and_history(rows=rows)
    return build_vsb_input_packet(
        api=api,
        market_history=history,
        implementation_id=IMPLEMENTATION_ID,
        as_of=AS_OF,
    )


def test_contract_and_packet_are_family_bound_source_bound_and_one_trial() -> None:
    validate_vsb_contract()
    assert FAMILY_DATA_CONTRACT.allowed_observation_surface == (
        "market.close",
        "market.total_return_1d",
        "market.volume",
    )
    assert TRIAL_BUDGET_MAX == 1
    packet = _packet()
    verify_vsb_input_packet(packet)
    assert packet["family_id"] == FAMILY_ID
    assert packet["risk_set_spec_id"] == RISK_SET_SPEC_ID
    assert packet["history_session_counts"] == {"CIQSEC:IQ101": 60, "CIQSEC:IQ202": 60}
    assert len(packet["source_receipt_sha256s"]) == 2
    assert packet["financial_alpha_evidence"] == 0
    assert packet["capital_authority"] == "NONE"


def test_packet_rejects_short_future_and_nonpermanent_history() -> None:
    short = _market_rows()
    short.pop(0)
    api, history = _api_and_history(rows=short)
    with pytest.raises(ValueError, match="insufficient_60_session_history"):
        build_vsb_input_packet(api=api, market_history=history, implementation_id=IMPLEMENTATION_ID, as_of=AS_OF)

    future = _market_rows()
    future[-1] = {**future[-1], "session_date": "2026-08-11"}
    api, history = _api_and_history(rows=future)
    with pytest.raises(ValueError, match="after_decision_session"):
        build_vsb_input_packet(api=api, market_history=history, implementation_id=IMPLEMENTATION_ID, as_of=AS_OF)

    ticker = _market_rows()
    ticker[0] = {**ticker[0], "security_id": "AAPL"}
    api, history = _api_and_history(rows=ticker)
    with pytest.raises(ValueError, match="ciq_security_id_namespace_required"):
        build_vsb_input_packet(api=api, market_history=history, implementation_id=IMPLEMENTATION_ID, as_of=AS_OF)


def test_discovery_mode_cannot_build_prediction_packet() -> None:
    api, history = _api_and_history(mode=ResearchMode.DISCOVERY)
    with pytest.raises(ValueError, match="prediction_packet_discovery_mode_forbidden"):
        build_vsb_input_packet(api=api, market_history=history, implementation_id=IMPLEMENTATION_ID, as_of=AS_OF)


def test_feature_transform_matches_frozen_20_60_20_formulas() -> None:
    features = compute_m0_features(_packet())
    by_security = {row["security_id"]: row for row in features["rows"]}
    winner = by_security["CIQSEC:IQ101"]
    nonbreakout = by_security["CIQSEC:IQ202"]
    assert winner["feature_status"] == "READY"
    assert nonbreakout["feature_status"] == "READY"

    returns = _return_path()
    expected_compression = math.log(statistics.stdev(returns[-60:]) / statistics.stdev(returns[-20:]))
    assert float(winner["compression"]) == pytest.approx(expected_compression)
    assert float(winner["breakout"]) == pytest.approx(math.log(1.05))
    assert float(winner["volume_expansion"]) == pytest.approx(math.log(2.0))
    assert float(nonbreakout["breakout"]) == pytest.approx(math.log(0.99))


def test_zero_decision_volume_is_invalid_not_repaired() -> None:
    rows = _market_rows()
    for row in rows:
        if row["security_id"] == "CIQSEC:IQ101" and row["session_date"] == DECISION_DATE:
            row["volume"] = 0.0
    features = compute_m0_features(_packet(rows=rows))
    invalid = next(row for row in features["rows"] if row["security_id"] == "CIQSEC:IQ101")
    assert invalid["feature_status"] == "INSUFFICIENT_OR_INVALID_M0_HISTORY"
    assert invalid["compression"] is None
    assert "NONPOSITIVE_VOLUME_T" in invalid["invalid_reasons"]
    output = score_m0_features(features)
    scored = next(row for row in output["rows"] if row["security_id"] == "CIQSEC:IQ101")
    assert float(scored["forecast_score"]) == 0.0
    assert "INSUFFICIENT_OR_INVALID_M0_HISTORY" in scored["reason_codes"]


def test_m0_uses_average_tie_percentiles_equal_weights_and_zero_threshold_trigger() -> None:
    output = score_m0_features(compute_m0_features(_packet()))
    by_security = {row["security_id"]: row for row in output["rows"]}
    winner = by_security["CIQSEC:IQ101"]
    nonbreakout = by_security["CIQSEC:IQ202"]

    expected_winner_raw = (0.75 + 1.0 + 0.75) / 3.0
    expected_nonbreakout_raw = (0.75 + 0.5 + 0.75) / 3.0
    assert output["percentile_rank_rule"] == "AVERAGE_ONE_BASED_RANK_DIVIDED_BY_FINITE_CROSS_SECTION_COUNT"
    assert float(winner["raw_score"]) == pytest.approx(expected_winner_raw)
    assert float(nonbreakout["raw_score"]) == pytest.approx(expected_nonbreakout_raw)
    assert winner["trigger"] is True
    assert float(winner["forecast_score"]) == pytest.approx(expected_winner_raw)
    assert nonbreakout["trigger"] is False
    assert float(nonbreakout["forecast_score"]) == 0.0
    assert "NO_BREAKOUT" in nonbreakout["reason_codes"]
    assert output["support_count"] == 1


def test_prediction_seal_is_deterministic_strictly_post_cut_and_zero_authority() -> None:
    packet = _packet()
    made_at = AS_OF + timedelta(seconds=1)
    first = seal_m0_predictions(input_packet=packet, prediction_made_at=made_at)
    second = seal_m0_predictions(input_packet=packet, prediction_made_at=made_at)
    assert first == second
    verify_prediction_batch(first)
    assert first["search_family_id"] == SEARCH_FAMILY_ID
    assert first["confirmation_role_id"] == CONFIRMATION_ROLE_ID
    assert first["guardian_contract_sha256"] == GUARDIAN_CONTRACT_SHA256
    assert first["trial_budget_max"] == TRIAL_BUDGET_MAX == 1
    assert first["material_trials_consumed"] == 1
    assert first["financial_alpha_evidence"] == 0
    assert first["capital_authority"] == "NONE"
    assert first["broker_orders"] == "FORBIDDEN"
    assert first["parent_child_mutation"] == "FORBIDDEN"
    assert first["retune_authority"] == "NONE"
    assert first["prebreakout_authority"] == "NONE"
    assert all(len(row["prediction_id"]) == 64 for row in first["rows"])

    expected_batch_id = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:PREDICTION_ID",
        canonical_value(
            {
                "family_id": FAMILY_ID,
                "implementation_id": IMPLEMENTATION_ID,
                "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
                "decision_context_id": packet["decision_context_id"],
                "decision_date": packet["decision_session_date"],
                "risk_set_id": packet["risk_set_id"],
                "input_packet_sha256": packet["input_packet_sha256"],
                "prediction_made_at": first["prediction_made_at"],
            }
        ),
    )
    assert first["prediction_id"] == expected_batch_id
    first_row = first["rows"][0]
    expected_row_id = domain_hash(
        "VOL_SQUEEZE_BREAKOUT_V1:SECURITY_PREDICTION_ID",
        canonical_value(
            {
                "family_id": FAMILY_ID,
                "implementation_id": IMPLEMENTATION_ID,
                "guardian_contract_sha256": GUARDIAN_CONTRACT_SHA256,
                "input_packet_sha256": packet["input_packet_sha256"],
                "security_id": first_row["security_id"],
                "prediction_made_at": first["prediction_made_at"],
            }
        ),
    )
    assert first_row["prediction_id"] == expected_row_id

    with pytest.raises(ValueError, match="prediction_must_be_after_knowledge_cutoff"):
        seal_m0_predictions(input_packet=packet, prediction_made_at=AS_OF)

    tampered = deepcopy(first)
    tampered["rows"][0]["forecast_score"] = "999"
    with pytest.raises(ValueError, match="prediction_batch_hash_mismatch"):
        verify_prediction_batch(tampered)


def test_vsb_core_contains_no_provider_discovery_or_literal_smoke_ticker_branch() -> None:
    root = Path("research/vol_squeeze_breakout_v1")
    core_files = ("contracts.py", "pit_packet.py", "features.py", "model.py", "runner.py", "guardian.py")
    text = "\n".join((root / name).read_text(encoding="utf-8") for name in core_files)
    forbidden = (
        "yfinance",
        "CiqCycleV1Adapter",
        "discovery_outcomes",
        "permno",
        '"SNDK"',
        '"MU"',
        "submit_order",
    )
    assert not any(token in text for token in forbidden)
