import io
import zipfile

import numpy as np
import pandas as pd
import pytest

from scripts import pead_m5a_multifactor_factors as factors
from scripts import pead_m5a_net_multifactor_alpha_test as runner


def _source_zip(rows: list[tuple[str, float, float, float, float]]) -> bytes:
    payload = [
        "This file was created by using the 202604 CRSP database.",
        "Synthetic test header line.",
        "",
        ",Mkt-RF,SMB,HML,RF",
    ]
    payload.extend(
        f"{date},{mktrf:.2f},{smb:.2f},{hml:.2f},{rf:.2f}"
        for date, mktrf, smb, hml, rf in rows
    )
    payload.append("")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("F-F_Research_Data_Factors_daily.csv", "\n".join(payload))
    return buffer.getvalue()


def test_m5a_factor_parser_keeps_smb_hml_and_decimalizes() -> None:
    source = factors.parse_ken_french_three_factor_daily_zip(
        _source_zip(
            [
                ("20240103", 1.20, 0.30, -0.40, 0.05),
                ("20240104", -0.50, 0.10, 0.20, 0.04),
            ]
        )
    )
    sessions = pd.to_datetime(["2024-01-03", "2024-01-04"])

    output = factors.build_multifactor_frame(source, sessions)

    assert output["mktrf"].tolist() == pytest.approx([0.012, -0.005])
    assert output["smb"].tolist() == pytest.approx([0.003, 0.001])
    assert output["hml"].tolist() == pytest.approx([-0.004, 0.002])
    assert output["rf"].tolist() == pytest.approx([0.0005, 0.0004])
    assert "benchmark_return" not in output.columns


def test_m5a_factor_frame_fails_without_fill() -> None:
    source = factors.parse_ken_french_three_factor_daily_zip(
        _source_zip([("20240103", 0.10, 0.20, 0.30, 0.01)])
    )
    sessions = pd.to_datetime(["2024-01-03", "2024-01-04"])

    with pytest.raises(ValueError, match="no fill or interpolation"):
        factors.build_multifactor_frame(source, sessions)


def test_ff3_hac_regression_recovers_known_intercept_and_betas() -> None:
    rng = np.random.default_rng(20260624)
    n = 90
    mktrf = rng.normal(0.0, 0.01, n)
    smb = rng.normal(0.0, 0.008, n)
    hml = rng.normal(0.0, 0.007, n)
    y = 0.001 + 1.5 * mktrf - 0.7 * smb + 0.25 * hml
    daily = pd.DataFrame({"y": y, "mktrf": mktrf, "smb": smb, "hml": hml})

    result = runner.fit_hac_regression(
        daily,
        dependent_variable="y",
        factors=["mktrf", "smb", "hml"],
        hac_maxlags=5,
    )

    assert result["status"] == "valid"
    assert result["intercept"] == pytest.approx(0.001, abs=1e-12)
    assert result["factor_betas"]["mktrf"] == pytest.approx(1.5, abs=1e-10)
    assert result["factor_betas"]["smb"] == pytest.approx(-0.7, abs=1e-10)
    assert result["factor_betas"]["hml"] == pytest.approx(0.25, abs=1e-10)


def test_m5a_evidence_remains_diagnostic_only(monkeypatch: pytest.MonkeyPatch) -> None:
    rng = np.random.default_rng(7)
    n = 80
    daily = pd.DataFrame(
        {
            "return_date": pd.bdate_range("2024-01-02", periods=n),
            "R_HL": 0.001 + rng.normal(0.0, 0.01, n),
            "mktrf": rng.normal(0.0, 0.01, n),
            "smb": rng.normal(0.0, 0.008, n),
            "hml": rng.normal(0.0, 0.007, n),
            "rf": 0.0001,
        }
    )

    def fake_prepare(**kwargs):
        return (
            daily.copy(),
            {
                "d1": {"rows": 1},
                "d2b": {"rows": 1},
                "d3_locked": {"rows": n},
                "d3m_multifactor": {"rows": n},
            },
            {
                "session_coverage": {"retained_sessions": n},
                "daily_summary": {"sessions": n},
                "source_m1b_primary_inference": {"status": "valid"},
            },
        )

    monkeypatch.setattr(runner, "_prepare_daily_portfolio", fake_prepare)

    evidence = runner.build_m5a_evidence(spread_cost_bps_per_day=2.5)

    assert evidence["data_validity_flags"]["diagnostic_only"] is True
    assert evidence["data_validity_flags"]["strict_pit_eps_vintage"] is False
    assert evidence["data_validity_flags"]["delisting_adjusted_returns"] is False
    assert evidence["cost_assumption"]["spread_cost_bps_per_day"] == 2.5
    assert evidence["results"]["gross"]["ff3"]["status"] == "valid"
    assert evidence["results"]["net"]["ff3"]["status"] == "valid"
    assert "alpha_claims" in evidence["evidence_policy"]["forbidden_use"]
    assert evidence["evidence_policy"]["ranking_or_scoring_authorized"] is False
