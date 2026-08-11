from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from research.econphysics_prebreakout_v1.contracts import (
    build_structured_snapshots,
    deterministic_xs_holdout,
)
from research.econphysics_prebreakout_v1.dynamics_diagnostic import (
    DELTA_MEAN_REVERSION,
    M0_STATE_MEAN_REVERSION,
    M1_STATE_MEAN_REVERSION,
    OPERATOR_IDS,
    evaluate_economic_dynamics_diagnostic,
)
from research.econphysics_prebreakout_v1.transition_evaluator import CORE_TARGETS


RECEIPT = "e" * 64
PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")
QUARTERS = (
    date(2023, 3, 31),
    date(2023, 6, 30),
    date(2023, 9, 30),
    date(2023, 12, 31),
    date(2024, 3, 31),
    date(2024, 6, 30),
    date(2024, 9, 30),
    date(2024, 12, 31),
    date(2025, 3, 31),
)


def _development_securities(count: int) -> list[str]:
    output: list[str] = []
    number = 1000
    while len(output) < count:
        candidate = f"CIQSEC:IQ{number}"
        if not deterministic_xs_holdout(candidate):
            output.append(candidate)
        number += 1
    return output


def _rows_for_security(*, security_id: str, entity: str, phase: int) -> list[dict[str, object]]:
    revenue = [100.0 if (index + phase) % 2 == 0 else 120.0 for index in range(len(QUARTERS))]
    inventory_ratio = [0.30 if (index + phase) % 2 == 0 else 0.20 for index in range(len(QUARTERS))]
    operating_margin = [0.10 if (index + phase) % 2 == 0 else 0.20 for index in range(len(QUARTERS))]
    output: list[dict[str, object]] = []
    for fq0_index in range(4, 9):
        as_of = QUARTERS[fq0_index] + timedelta(days=45)
        for relative_index, relative_period in enumerate(PERIODS):
            source_index = fq0_index - relative_index
            rev = revenue[source_index]
            output.append(
                {
                    "security_id": security_id,
                    "source_entity_id": entity,
                    "as_of_date": as_of.isoformat(),
                    "available_at": as_of.isoformat() + "T23:59:59.999999Z",
                    "relative_period": relative_period,
                    "period_end": QUARTERS[source_index].isoformat(),
                    "IQ_TOTAL_REV": rev,
                    "IQ_INVENTORY": inventory_ratio[source_index] * rev,
                    "IQ_OPER_INC": operating_margin[source_index] * rev,
                    "IQ_CAPEX_BNK": 10.0 + source_index,
                    "filing_version": "Original",
                    "value_unit": "USD_THOUSANDS",
                    "source_receipt_sha256": RECEIPT,
                }
            )
    return output


def test_fixed_operator_family_routes_reversal_without_claiming_observable_insufficiency() -> None:
    rows: list[dict[str, object]] = []
    for index, security_id in enumerate(_development_securities(3)):
        rows.extend(
            _rows_for_security(
                security_id=security_id,
                entity=str(5000 + index),
                phase=index % 2,
            )
        )

    report = evaluate_economic_dynamics_diagnostic(
        build_structured_snapshots(rows),
        minimum_fold_n=1,
        minimum_fold_coverage=0.10,
    )

    assert report["routing"] == "NODE_SPECIFIC_DYNAMICS_SURVIVORS"
    assert report["observable_insufficiency_supported"] is False
    assert report["operator_selection_performed"] is False
    assert report["fit_or_tuning_performed"] is False
    assert set(report["fixed_operator_family"]) == set(OPERATOR_IDS)
    assert M0_STATE_MEAN_REVERSION in report["representation_conditioned_operator_ids"]
    assert M1_STATE_MEAN_REVERSION in report["representation_conditioned_operator_ids"]

    for target_id in CORE_TARGETS:
        target = report["targets"][target_id]
        assert set(target["operator_reports"]) == set(OPERATOR_IDS)
        assert DELTA_MEAN_REVERSION in target["surviving_operator_ids"]
        assert target["node_routing"] == "DYNAMICS_SIGNAL_PRESENT"
        assert [fold["reversal_rate"] for fold in target["lag1_transition"]["temporal_folds"]] == [
            1.0,
            1.0,
            1.0,
            1.0,
        ]
        reversal = target["operator_reports"][DELTA_MEAN_REVERSION]
        assert reversal["supporting_temporal_fold_count"] == 4
        assert all(fold["lift_vs_no_information_baseline"] > 1.0 for fold in reversal["temporal_folds"])
        assert all(fold["directional_association"] > 0.0 for fold in reversal["temporal_folds"])


def test_shootout_no_extraction_interpretation_routes_to_dynamics_before_observable_insufficiency() -> None:
    text = Path("scripts/econphysics_prebreakout_s0_shootout.py").read_text(encoding="utf-8")
    assert "structured fundamentals do not add transition information over M0" not in text
    assert "do not infer structured-information insufficiency" in text
    assert "dynamics-operator diagnostic" in text
