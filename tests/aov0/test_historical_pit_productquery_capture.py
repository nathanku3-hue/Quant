from __future__ import annotations

import pytest

from scripts.aov0_capture_ciq_historical_market_productquery import _js as market_js
from scripts.aov0_capture_ciq_historical_pit_productquery import (
    OPTIONS,
    _extract_data,
    _period_end,
    _request_body,
    _scalar_request,
)
from scripts.aov0_historical_pit_replay import FROZEN_IMPLEMENTATION_PATHS


def test_market_productquery_transport_is_raw_existing_session_contract() -> None:
    expression = market_js(["SPT123"], ["05/16/2025"])
    assert "requirejs" not in expression
    assert "/SNL.Services.Data.Service/v1/ProductQuery.svc/productQueryRequests" in expression
    assert "credentials:'include'" in expression
    assert "322797" in expression
    assert "324251" in expression
    assert "324277" in expression


def test_scalar_spg_request_preserves_original_asof_contract() -> None:
    request = _scalar_request(
        7,
        entity="4142027",
        metric="IQ_TOTAL_REV",
        period="FQ0",
        as_of="2025-05-16",
    )
    assert request["id"] == 7
    assert request["dispid"] == 12
    assert request["parameters"][:5] == [
        "4142027",
        "IQ_TOTAL_REV",
        "FQ0",
        "05/16/2025",
        OPTIONS,
    ]
    body = _request_body([request])
    assert body["conversionInformation"]["reportingBasis"] == "Original"
    assert body["conversionInformation"]["dateComparison"] == "Filing Date"


def test_spg_result_and_period_end_normalization() -> None:
    assert _extract_data(
        {
            "id": 1,
            "result": [[[{"Data": "2025-03-31T00:00:00"}]]],
            "error": None,
            "responseException": None,
        }
    ) == "2025-03-31T00:00:00"
    assert _period_end("2025-03-31T00:00:00") == "2025-03-31"
    assert _period_end(None) == ""

    with pytest.raises(ValueError, match="provider_error"):
        _extract_data(
            {
                "id": 2,
                "result": [],
                "error": "provider failure",
                "responseException": None,
            }
        )


def test_a2_freeze_binds_productquery_pit_capture_implementation() -> None:
    assert "scripts/aov0_capture_ciq_historical_pit_productquery.py" in FROZEN_IMPLEMENTATION_PATHS
