from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.alpha_pit_v1.adapters import (
    CiqCycleV1Adapter,
    CycleResonancePITBackendV1,
    SecAlphaClaimsV1Adapter,
)
from research.alpha_pit_v1.adapters.ciq_cycle_v1 import (
    RISK_SET_ELIGIBILITY_CONTRACT,
    RISK_SET_ELIGIBILITY_CONTRACT_ID,
    RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
)
from research.alpha_pit_v1.contracts import FAMILY_ID, ResearchMode
from research.alpha_pit_v1.session import open_alpha_pit_session
from research.cycle_resonance_v1.contracts import REAL_PIT_AUTHORITY_CLASS
from research.cycle_resonance_v1.pit_packet import build_cycle_resonance_input_packet


AS_OF = datetime(2026, 8, 8, 20, 0, tzinfo=UTC)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _landed_custody(
    tmp_path: Path,
    *,
    with_risk_set: bool = True,
    growth_screen: bool = False,
    drop_second_fundamental_history: bool = False,
) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    master = tmp_path / "master.csv"
    pd.DataFrame(
        [
            {
                "SP_ENTITY_ID": "1001",
                "SP_CIQ_ID": "IQ101",
                "SPT_INSTRUMENT_ITEM_ID": "SPT1001",
                "Exchange": "NYSE",
                "Description": "Common Stock",
                "Status": "Active",
            },
            {
                "SP_ENTITY_ID": "1002",
                "SP_CIQ_ID": "IQ202",
                "SPT_INSTRUMENT_ITEM_ID": "SPT1002",
                "Exchange": "NASDAQGS",
                "Description": "Common Stock",
                "Status": "Active",
            },
        ]
    ).to_csv(master, index=False)
    master_receipt = tmp_path / "master.receipt.json"
    _json(
        master_receipt,
        {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MASTER",
            "retrieved_at": "2026-08-08T16:23:22Z",
            "raw_object_sha256": _sha(master),
        },
    )

    dates = pd.bdate_range(end="2026-08-07", periods=201)
    market_rows = []
    for security, entity, trading, offset in (
        ("IQ101", "1001", "SPT1001", 0.0),
        ("IQ202", "1002", "SPT1002", 5.0),
    ):
        for index, date in enumerate(dates):
            market_rows.append(
                {
                    "SPT_DATE": date.date().isoformat(),
                    "SP_CIQ_ID": security,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SP_TOTAL_RETURN": 0.1 + index / 10000.0,
                    "SP_PRICE_CLOSE": 20.0 + offset + index / 10.0,
                    "SP_VOLUME": 100000 + index,
                    "SP_ENTITY_ID": entity,
                }
            )
    market = tmp_path / "market.csv"
    pd.DataFrame(market_rows).to_csv(market, index=False)
    market_receipt = tmp_path / "market.receipt.json"
    _json(
        market_receipt,
        {
            "source_id": "SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA",
            "retrieved_at": "2026-08-08T19:39:21Z",
            "decision_target_date": "2026-08-07",
            "raw_object_sha256": _sha(market),
        },
    )

    fundamentals = tmp_path / "fundamentals.parquet"
    fundamental_rows = [
        {
            "source_entity_id": "1001",
            "period_end": pd.Timestamp("2026-06-30"),
            "known_at": pd.Timestamp("2026-08-07T18:53:00Z"),
            "total_revenue_q": 1000.0,
            "inventory_q": 100.0,
            "capex_q": -50.0,
            "operating_margin_q": 0.2,
        },
        {
            "source_entity_id": "1002",
            "period_end": pd.Timestamp("2026-06-30"),
            "known_at": pd.Timestamp("2026-08-07T18:53:00Z"),
            "total_revenue_q": 2000.0,
            "inventory_q": 200.0,
            "capex_q": -70.0,
            "operating_margin_q": 0.3,
        },
    ]
    if drop_second_fundamental_history:
        fundamental_rows = fundamental_rows[:1]
    pd.DataFrame(fundamental_rows).to_parquet(fundamentals, index=False)
    fundamental_receipt = tmp_path / "fundamentals.receipt.json"
    _json(
        fundamental_receipt,
        {
            "source_id": "SPCIQPRO:QUARTERLY_FUNDAMENTALS",
            "retrieved_at": "2026-08-07T18:53:00Z",
            "quarter_min": "2026-06-30",
            "quarter_max": "2026-06-30",
            "outputs": {"quarterly_panel": {"sha256": _sha(fundamentals)}},
        },
    )

    paths = {
        "security_master_path": master,
        "security_master_receipt_path": master_receipt,
        "market_history_path": market,
        "market_receipt_path": market_receipt,
        "fundamental_panel_path": fundamentals,
        "fundamental_receipt_path": fundamental_receipt,
    }
    if with_risk_set:
        risk_identity_receipt = tmp_path / "risk_identity.receipt.json"
        _json(
            risk_identity_receipt,
            {
                "schema_version": "alpha_pit_ciq_crv1_identity_receipt_v1",
                "source_id": "SPCIQPRO:CRV1_PRIMARY_SECURITY_MASTER",
                "retrieved_at": "2026-08-08T19:30:00Z",
            },
        )
        identity_receipt_sha256 = _sha(risk_identity_receipt)
        risk_set = tmp_path / "risk_set.json"
        _json(
            risk_set,
            {
                "schema_version": "alpha_pit_ciq_crv1_risk_set_source_v1",
                "family_id": FAMILY_ID,
                "risk_set_spec_id": "CRV1_US_PRIMARY_COMMON_V1",
                "eligibility_contract_id": RISK_SET_ELIGIBILITY_CONTRACT_ID,
                "eligibility_contract_sha256": RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
                "eligibility_contract": RISK_SET_ELIGIBILITY_CONTRACT,
                "identity_receipt_sha256": identity_receipt_sha256,
                "as_of": "2026-08-08T20:00:00Z",
                "growth_screen_applied": growth_screen,
                "current_survivor_filter_applied": False,
                "future_membership_filter_applied": False,
                "exclusion_counts": {"INSUFFICIENT_200D_HISTORY": 0},
                "rows": [
                    {
                        "security_id": "CIQSEC:IQ101",
                        "company_id": "COMPANY:1001",
                        "trading_item_id": "SPT1001",
                        "primary_listing_id": "PRIMARY:IQ101",
                        "listing_country": "US",
                        "primary_listing": True,
                        "security_class": "COMMON_EQUITY",
                        "trading_status": "ACTIVE_TRADABLE",
                        "identity_status": "UNIQUE_PERMANENT_MAPPING",
                        "prior_market_observation_count": 201,
                        "membership_effective_at": "2026-08-08T19:00:00Z",
                        "observed_at": "2026-08-08T19:00:00Z",
                        "available_at": "2026-08-08T19:00:00Z",
                        "eligibility_status": "ELIGIBLE",
                    },
                    {
                        "security_id": "CIQSEC:IQ202",
                        "company_id": "COMPANY:1002",
                        "trading_item_id": "SPT1002",
                        "primary_listing_id": "PRIMARY:IQ202",
                        "listing_country": "US",
                        "primary_listing": True,
                        "security_class": "COMMON_EQUITY",
                        "trading_status": "ACTIVE_TRADABLE",
                        "identity_status": "UNIQUE_PERMANENT_MAPPING",
                        "prior_market_observation_count": 201,
                        "membership_effective_at": "2026-08-08T19:00:00Z",
                        "observed_at": "2026-08-08T19:00:00Z",
                        "available_at": "2026-08-08T19:00:00Z",
                        "eligibility_status": "ELIGIBLE",
                    },
                ],
            },
        )
        risk_receipt = tmp_path / "risk_set.receipt.json"
        _json(
            risk_receipt,
            {
                "schema_version": "alpha_pit_ciq_crv1_risk_set_source_receipt_v1",
                "source_id": "SPCIQPRO:CRV1_US_PRIMARY_COMMON_RISK_SET",
                "risk_set_spec_id": "CRV1_US_PRIMARY_COMMON_V1",
                "eligibility_contract_id": RISK_SET_ELIGIBILITY_CONTRACT_ID,
                "eligibility_contract_sha256": RISK_SET_ELIGIBILITY_CONTRACT_SHA256,
                "identity_receipt_path": risk_identity_receipt.name,
                "identity_receipt_sha256": identity_receipt_sha256,
                "growth_screen_applied": growth_screen,
                "current_survivor_filter_applied": False,
                "future_membership_filter_applied": False,
                "retrieved_at": "2026-08-08T19:31:00Z",
                "observed_range_start": "2026-08-08T20:00:00Z",
                "observed_range_end": "2026-08-08T20:00:00Z",
                "raw_object_sha256": _sha(risk_set),
            },
        )
        paths["risk_set_source_path"] = risk_set
        paths["risk_set_receipt_path"] = risk_receipt
    return paths


def _backend(tmp_path: Path, *, with_risk_set: bool = True) -> CycleResonancePITBackendV1:
    ciq = CiqCycleV1Adapter(**_landed_custody(tmp_path, with_risk_set=with_risk_set))
    sec = SecAlphaClaimsV1Adapter(custody_verified_at=ciq.custody_verified_at)
    return CycleResonancePITBackendV1(ciq=ciq, sec_claims=sec)


def test_current_ciq_structured_custody_closes_real_input_packet_with_explicit_missing_optional_sources(tmp_path: Path) -> None:
    backend = _backend(tmp_path)
    api = open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="crv1-current-custody-test",
        backend=backend,
    )
    risk_set = api.risk_set(as_of=AS_OF)
    assert risk_set.payload["row_count"] == 2
    ids = [row["security_id"] for row in risk_set.payload["rows"]]

    observations = api.observations(
        ids=ids,
        fields=(
            "market.close",
            "market.adv20",
            "market.realized_vol20",
            "market.sma200",
            "fund.revenue_q",
            "fund.gross_margin_q",
            "fund.operating_margin_q",
            "fund.cash_from_ops_q",
        ),
        as_of=AS_OF,
    )
    assert observations.manifest["authority_class"] == "PIT_ARTIFACT"
    rows = observations.payload["rows"]
    assert sum(row["coverage_status"] == "PRESENT" for row in rows) == 12
    assert sum(row["coverage_status"] == "MISSING_SOURCE" for row in rows) == 4

    expectations = api.expectations(ids=ids, as_of=AS_OF)
    assert expectations.payload["row_count"] == 18
    assert {row["coverage_status"] for row in expectations.payload["rows"]} == {"MISSING_SOURCE"}
    claims = api.source_claims(ids=ids, as_of=AS_OF)
    assert claims.payload["rows"] == []
    assert claims.manifest["coverage_summary"]["missingness_by_reason"] == {
        "SEC_CLAIMS_CAPTURE_NOT_LANDED": 2
    }

    packet = build_cycle_resonance_input_packet(
        api=api,
        implementation_id="CRV1_MECHANICAL_CURRENT_CUSTODY_TEST",
        decision_context_id="crv1-current-custody-test",
        as_of=AS_OF,
        coverage_policy_id="CRV1_TEST_COVERAGE_POLICY_ONLY",
    )
    assert packet["authority_class"] == REAL_PIT_AUTHORITY_CLASS
    assert packet["financial_alpha_evidence"] == 0


def test_current_aov_custody_without_independent_crv1_risk_set_fails_closed(tmp_path: Path) -> None:
    backend = _backend(tmp_path, with_risk_set=False)
    api = open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="crv1-no-risk-set",
        backend=backend,
    )
    with pytest.raises(ValueError, match="crv1_risk_set_source_not_landed"):
        api.risk_set(as_of=AS_OF)


def test_growth_screen_source_cannot_be_relabelled_as_crv1_risk_set(tmp_path: Path) -> None:
    paths = _landed_custody(tmp_path, growth_screen=True)
    with pytest.raises(ValueError, match="growth_screen_risk_set_forbidden"):
        CiqCycleV1Adapter(**paths)


def test_current_cut_market_bytes_cannot_be_backdated_into_historical_pit(tmp_path: Path) -> None:
    ciq = CiqCycleV1Adapter(**_landed_custody(tmp_path))
    with pytest.raises(ValueError, match="current_market_not_available_at_as_of"):
        ciq.observations(
            ids=["CIQSEC:IQ101"],
            fields=["market.close"],
            as_of=datetime(2026, 8, 8, 19, 0, tzinfo=UTC),
            research_mode=ResearchMode.CONFIRMATORY,
        )


def test_source_level_missing_fundamental_fields_do_not_degrade_to_missing_history(tmp_path: Path) -> None:
    ciq = CiqCycleV1Adapter(
        **_landed_custody(tmp_path, drop_second_fundamental_history=True)
    )
    artifact = ciq.observations(
        ids=["CIQSEC:IQ101", "CIQSEC:IQ202"],
        fields=["fund.gross_margin_q", "fund.cash_from_ops_q"],
        as_of=AS_OF,
        research_mode=ResearchMode.CONFIRMATORY,
    )
    assert {row["coverage_status"] for row in artifact.payload["rows"]} == {"MISSING_SOURCE"}
    assert artifact.manifest["coverage_summary"]["missing_count"] == 4


def test_risk_set_receipt_must_bind_eligibility_contract_and_independent_identity_receipt(tmp_path: Path) -> None:
    paths = _landed_custody(tmp_path)
    receipt_path = paths["risk_set_receipt_path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["eligibility_contract_sha256"] = "0" * 64
    _json(receipt_path, receipt)
    with pytest.raises(ValueError, match="receipt_eligibility_contract_hash_invalid"):
        CiqCycleV1Adapter(**paths)

    paths = _landed_custody(tmp_path / "identity-mismatch")
    receipt_path = paths["risk_set_receipt_path"]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["identity_receipt_sha256"] = "1" * 64
    _json(receipt_path, receipt)
    with pytest.raises(ValueError, match="identity_receipt_hash_mismatch"):
        CiqCycleV1Adapter(**paths)
