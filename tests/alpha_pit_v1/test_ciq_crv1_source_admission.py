from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.alpha_pit_v1.adapters.ciq_crv1_source_v1 import (
    CAPTURE_SCOPE,
    IDENTITY_CAPTURE_RECEIPT_SCHEMA,
    MARKET_CAPTURE_RECEIPT_SCHEMA,
    build_crv1_structured_source_admission,
    canonical_json_bytes,
)
from research.alpha_pit_v1.adapters.backend_v1 import CycleResonancePITBackendV1
from research.alpha_pit_v1.adapters.ciq_cycle_v1 import CiqCycleV1Adapter
from research.alpha_pit_v1.adapters.sec_claims_v1 import SecAlphaClaimsV1Adapter
from research.alpha_pit_v1.contracts import FAMILY_ID, ResearchMode
from research.alpha_pit_v1.session import open_alpha_pit_session
from research.cycle_resonance_v1.contracts import REAL_PIT_AUTHORITY_CLASS
from research.cycle_resonance_v1.pit_packet import build_cycle_resonance_input_packet


AS_OF = datetime(2026, 8, 8, 20, 0, tzinfo=UTC)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.write_bytes(canonical_json_bytes(payload))


def _capture_receipt(*, schema: str, raw: Path, retrieved_at: str, **extra: object) -> dict:
    return {
        "schema_version": schema,
        "family_id": FAMILY_ID,
        "risk_set_spec_id": "CRV1_US_PRIMARY_COMMON_V1",
        "capture_scope": CAPTURE_SCOPE,
        "provider": "S&P Capital IQ Pro",
        "retrieved_at": retrieved_at,
        "raw_object_sha256": _sha(raw),
        "growth_screen_applied": False,
        "current_survivor_filter_applied": False,
        "future_membership_filter_applied": False,
        "aov_109_reused": False,
        "legacy_identity_fallback_used": False,
        **extra,
    }


def _source_inputs(tmp_path: Path) -> dict[str, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    identity = tmp_path / "broad_identity.csv"
    pd.DataFrame(
        [
            {
                "SP_ENTITY_ID": "1001",
                "SP_CIQ_ID": "IQ101",
                "SPT_INSTRUMENT_ITEM_ID": "SPT1001",
                "Exchange": "NYSE",
                "Description": "Common Stock",
                "Status": "Active",
                "PRIMARY_LISTING_ID": "PRIMARY:IQ101",
                "LISTING_COUNTRY": "US",
                "PRIMARY_LISTING": "true",
                "SECURITY_CLASS": "COMMON_EQUITY",
                "TRADING_STATUS": "ACTIVE_TRADABLE",
                "IDENTITY_STATUS": "UNIQUE_PERMANENT_MAPPING",
            },
            {
                "SP_ENTITY_ID": "1002",
                "SP_CIQ_ID": "IQ202",
                "SPT_INSTRUMENT_ITEM_ID": "SPT1002",
                "Exchange": "NASDAQGS",
                "Description": "Common Stock",
                "Status": "Active",
                "PRIMARY_LISTING_ID": "PRIMARY:IQ202",
                "LISTING_COUNTRY": "US",
                "PRIMARY_LISTING": "true",
                "SECURITY_CLASS": "COMMON_EQUITY",
                "TRADING_STATUS": "ACTIVE_TRADABLE",
                "IDENTITY_STATUS": "UNIQUE_PERMANENT_MAPPING",
            },
        ]
    ).to_csv(identity, index=False)

    dates = pd.bdate_range(end="2026-08-07", periods=201)
    market_rows: list[dict[str, object]] = []
    for security, trading, keep in (
        ("IQ101", "SPT1001", 201),
        ("IQ202", "SPT1002", 199),
    ):
        for index, date in enumerate(dates[-keep:]):
            market_rows.append(
                {
                    "SPT_DATE": date.date().isoformat(),
                    "SP_CIQ_ID": security,
                    "SPT_INSTRUMENT_ITEM_ID": trading,
                    "SP_TOTAL_RETURN": 0.1 + index / 10000.0,
                    "SP_PRICE_CLOSE": 20.0 + index / 10.0,
                    "SP_VOLUME": 100000 + index,
                }
            )
    market = tmp_path / "broad_market.csv"
    pd.DataFrame(market_rows).to_csv(market, index=False)

    identity_capture = tmp_path / "identity.capture.json"
    _write_json(
        identity_capture,
        _capture_receipt(
            schema=IDENTITY_CAPTURE_RECEIPT_SCHEMA,
            raw=identity,
            retrieved_at="2026-08-08T19:30:00Z",
        ),
    )
    market_capture = tmp_path / "market.capture.json"
    _write_json(
        market_capture,
        _capture_receipt(
            schema=MARKET_CAPTURE_RECEIPT_SCHEMA,
            raw=market,
            retrieved_at="2026-08-08T19:40:00Z",
            identity_raw_object_sha256=_sha(identity),
        ),
    )
    return {
        "identity": identity,
        "identity_capture": identity_capture,
        "market": market,
        "market_capture": market_capture,
    }


def _admit(tmp_path: Path):
    paths = _source_inputs(tmp_path)
    admission = build_crv1_structured_source_admission(
        as_of=AS_OF,
        identity_path=paths["identity"],
        identity_capture_receipt_path=paths["identity_capture"],
        market_path=paths["market"],
        market_capture_receipt_path=paths["market_capture"],
        identity_receipt_path_for_binding="identity.receipt.json",
    )
    identity_receipt = tmp_path / "identity.receipt.json"
    market_receipt = tmp_path / "market.receipt.json"
    risk_source = tmp_path / "risk_set.source.json"
    risk_receipt = tmp_path / "risk_set.receipt.json"
    _write_json(identity_receipt, dict(admission.identity_receipt))
    _write_json(market_receipt, dict(admission.market_receipt))
    _write_json(risk_source, dict(admission.risk_set_source))
    _write_json(risk_receipt, dict(admission.risk_set_receipt))
    return paths, admission, identity_receipt, market_receipt, risk_source, risk_receipt


def test_independent_non_growth_admission_derives_history_and_closes_market_risk_set_without_aov_fundamentals(tmp_path: Path) -> None:
    paths, admission, identity_receipt, market_receipt, risk_source, risk_receipt = _admit(tmp_path)
    assert admission.eligible_security_count == 1
    assert admission.risk_set_source["rows"][0]["security_id"] == "CIQSEC:IQ101"
    assert admission.risk_set_source["rows"][0]["prior_market_observation_count"] == 201
    assert admission.risk_set_source["exclusion_counts"] == {"INSUFFICIENT_200D_HISTORY": 1}
    assert admission.risk_set_source["aov_109_reused"] is False

    ciq = CiqCycleV1Adapter(
        security_master_path=paths["identity"],
        security_master_receipt_path=identity_receipt,
        market_history_path=paths["market"],
        market_receipt_path=market_receipt,
        risk_set_source_path=risk_source,
        risk_set_receipt_path=risk_receipt,
    )
    risk_set = ciq.risk_set(as_of=AS_OF, research_mode=ResearchMode.CONFIRMATORY)
    assert risk_set.payload["row_count"] == 1
    artifact = ciq.observations(
        ids=["CIQSEC:IQ101"],
        fields=["market.sma200", "fund.revenue_q"],
        as_of=AS_OF,
        research_mode=ResearchMode.CONFIRMATORY,
    )
    rows = {row["field_id"]: row for row in artifact.payload["rows"]}
    assert rows["market.sma200"]["coverage_status"] == "PRESENT"
    assert rows["fund.revenue_q"]["coverage_status"] == "MISSING_SOURCE"
    assert rows["fund.revenue_q"]["missingness_reason"] == "CIQ_CRV1_FUNDAMENTALS_CAPTURE_NOT_LANDED"
    bound_hashes = {row["raw_receipt_sha256"] for row in artifact.manifest["source_receipts"]}
    assert rows["fund.revenue_q"]["source_receipt_sha256"] in bound_hashes

    backend = CycleResonancePITBackendV1(
        ciq=ciq,
        sec_claims=SecAlphaClaimsV1Adapter(custody_verified_at=ciq.custody_verified_at),
    )
    api = open_alpha_pit_session(
        mode=ResearchMode.CONFIRMATORY,
        family_id=FAMILY_ID,
        decision_context_id="crv1-independent-non-growth-source-test",
        backend=backend,
    )
    packet = build_cycle_resonance_input_packet(
        api=api,
        implementation_id="CRV1_W9_SOURCE_BOUNDARY_TEST",
        decision_context_id="crv1-independent-non-growth-source-test",
        as_of=AS_OF,
        coverage_policy_id="CRV1_W9_EXPLICIT_MISSINGNESS_TEST_ONLY",
    )
    assert packet["authority_class"] == REAL_PIT_AUTHORITY_CLASS
    assert packet["financial_alpha_evidence"] == 0
    assert not hasattr(api, "outcomes")

    expectations = api.expectations(ids=["CIQSEC:IQ101"], as_of=AS_OF)
    assert {row["coverage_status"] for row in expectations.payload["rows"]} == {"MISSING_SOURCE"}
    claims = api.source_claims(ids=["CIQSEC:IQ101"], as_of=AS_OF)
    assert claims.payload["rows"] == []
    assert claims.manifest["coverage_summary"]["missingness_by_reason"] == {
        "SEC_CLAIMS_CAPTURE_NOT_LANDED": 1
    }


def test_admission_rejects_aov_109_reuse_flag(tmp_path: Path) -> None:
    paths = _source_inputs(tmp_path)
    receipt = json.loads(paths["identity_capture"].read_text(encoding="utf-8"))
    receipt["aov_109_reused"] = True
    _write_json(paths["identity_capture"], receipt)
    with pytest.raises(ValueError, match="identity_capture_forbidden_flag:aov_109_reused"):
        build_crv1_structured_source_admission(
            as_of=AS_OF,
            identity_path=paths["identity"],
            identity_capture_receipt_path=paths["identity_capture"],
            market_path=paths["market"],
            market_capture_receipt_path=paths["market_capture"],
            identity_receipt_path_for_binding="identity.receipt.json",
        )


def test_admission_rejects_growth_screen_and_survivor_backprojection(tmp_path: Path) -> None:
    paths = _source_inputs(tmp_path)
    receipt = json.loads(paths["identity_capture"].read_text(encoding="utf-8"))
    receipt["growth_screen_applied"] = True
    _write_json(paths["identity_capture"], receipt)
    with pytest.raises(ValueError, match="identity_capture_forbidden_flag:growth_screen_applied"):
        build_crv1_structured_source_admission(
            as_of=AS_OF,
            identity_path=paths["identity"],
            identity_capture_receipt_path=paths["identity_capture"],
            market_path=paths["market"],
            market_capture_receipt_path=paths["market_capture"],
            identity_receipt_path_for_binding="identity.receipt.json",
        )

    paths = _source_inputs(tmp_path / "survivor")
    receipt = json.loads(paths["identity_capture"].read_text(encoding="utf-8"))
    receipt["current_survivor_filter_applied"] = True
    _write_json(paths["identity_capture"], receipt)
    with pytest.raises(ValueError, match="identity_capture_forbidden_flag:current_survivor_filter_applied"):
        build_crv1_structured_source_admission(
            as_of=AS_OF,
            identity_path=paths["identity"],
            identity_capture_receipt_path=paths["identity_capture"],
            market_path=paths["market"],
            market_capture_receipt_path=paths["market_capture"],
            identity_receipt_path_for_binding="identity.receipt.json",
        )


def test_adapter_rejects_risk_set_identity_receipt_not_used_by_structured_observations(tmp_path: Path) -> None:
    paths, _, identity_receipt, market_receipt, risk_source, risk_receipt = _admit(tmp_path)
    alien = tmp_path / "alien_identity.receipt.json"
    alien.write_text("{}\n", encoding="utf-8")
    receipt = json.loads(risk_receipt.read_text(encoding="utf-8"))
    receipt["identity_receipt_path"] = alien.name
    receipt["identity_receipt_sha256"] = _sha(alien)
    _write_json(risk_receipt, receipt)
    source = json.loads(risk_source.read_text(encoding="utf-8"))
    source["identity_receipt_sha256"] = _sha(alien)
    _write_json(risk_source, source)
    receipt["raw_object_sha256"] = _sha(risk_source)
    _write_json(risk_receipt, receipt)

    ciq = CiqCycleV1Adapter(
        security_master_path=paths["identity"],
        security_master_receipt_path=identity_receipt,
        market_history_path=paths["market"],
        market_receipt_path=market_receipt,
        risk_set_source_path=risk_source,
        risk_set_receipt_path=risk_receipt,
    )
    with pytest.raises(ValueError, match="risk_set_not_bound_to_structured_identity_receipt"):
        ciq.risk_set(as_of=AS_OF, research_mode=ResearchMode.CONFIRMATORY)
