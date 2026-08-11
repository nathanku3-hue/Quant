from __future__ import annotations

import pandas as pd
import pytest

from research.asymmetric_opportunity_v1.orthogonalization import (
    ELIGIBLE_COMPLETE,
    M_MISSING_HISTORY,
    M_OBSERVED,
    M_WARMUP,
    Q_AND_M_MISSING,
    Q_UNOBSERVED,
)
from research.asymmetric_opportunity_v1.status_strata import (
    MANDATORY_STATUS_STRATA,
    M_NOT_APPLICABLE,
    OTHER_EXPLICIT_STATUS,
    Q_NOT_APPLICABLE,
    W3_DENOMINATOR_ID,
    assign_extended_status,
    build_status_strata_frame,
    contract_semantics,
    coverage_cube,
    refuse_mixed_unobserved_language,
)


def test_mandatory_strata_include_k0a_and_applicability() -> None:
    for name in (
        ELIGIBLE_COMPLETE,
        Q_UNOBSERVED,
        M_WARMUP,
        M_MISSING_HISTORY,
        Q_AND_M_MISSING,
        Q_NOT_APPLICABLE,
        M_NOT_APPLICABLE,
        OTHER_EXPLICIT_STATUS,
    ):
        assert name in MANDATORY_STATUS_STRATA
    semantics = contract_semantics()
    assert semantics["denominator"] == W3_DENOMINATOR_ID
    assert semantics["denominator_rewrite"] == "FORBIDDEN"
    assert semantics["mixed_unobserved_mashup_language"] == "FORBIDDEN"
    assert semantics["coverage_cube_label_join"] == "FORBIDDEN_THIS_TURN"


def test_extended_status_precedence() -> None:
    assert (
        assign_extended_status(q_observed=True, m_state=M_OBSERVED, q_applicable=False)
        == Q_NOT_APPLICABLE
    )
    assert (
        assign_extended_status(q_observed=True, m_state=M_OBSERVED, m_applicable=False)
        == M_NOT_APPLICABLE
    )
    assert (
        assign_extended_status(
            q_observed=True,
            m_state=M_OBSERVED,
            other_explicit_status=OTHER_EXPLICIT_STATUS,
        )
        == OTHER_EXPLICIT_STATUS
    )
    assert (
        assign_extended_status(q_observed=False, m_state=M_WARMUP)
        == Q_AND_M_MISSING
    )


def test_frame_preserves_denominator_rows() -> None:
    w3 = pd.DataFrame(
        [
            ("2026-01-02", "CIQSEC:1", "101"),
            ("2026-01-02", "CIQSEC:2", "102"),
            ("2026-01-02", "CIQSEC:3", "103"),
            ("2026-01-02", "CIQSEC:4", "104"),
        ],
        columns=["decision_date", "security_id", "trading_item_id"],
    )
    out = build_status_strata_frame(
        w3,
        q_observed_keys={
            ("2026-01-02", "CIQSEC:1"),
            ("2026-01-02", "CIQSEC:2"),
        },
        m_state_by_key={
            ("2026-01-02", "CIQSEC:1", "101"): M_OBSERVED,
            ("2026-01-02", "CIQSEC:2", "102"): M_MISSING_HISTORY,
            ("2026-01-02", "CIQSEC:3", "103"): M_OBSERVED,
            ("2026-01-02", "CIQSEC:4", "104"): M_WARMUP,
        },
        q_not_applicable_keys={("2026-01-02", "CIQSEC:3")},
    )
    assert len(out) == 4
    assert out["status_stratum"].tolist() == [
        ELIGIBLE_COMPLETE,
        M_MISSING_HISTORY,
        Q_NOT_APPLICABLE,
        Q_AND_M_MISSING,
    ]
    cube = coverage_cube(out)
    assert cube["rows_removed"] == 0
    assert cube["label_join"] is False
    assert cube["by_stratum"][Q_NOT_APPLICABLE] == 1
    assert cube["mixed_unobserved_mashup"] is None


def test_refuse_mixed_unobserved_language() -> None:
    with pytest.raises(ValueError, match="mixed_unobserved_language"):
        refuse_mixed_unobserved_language("coverage is ~20% unobserved overall")
