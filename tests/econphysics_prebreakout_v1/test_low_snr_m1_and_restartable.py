from __future__ import annotations

from argparse import Namespace
import asyncio
import csv
from pathlib import Path

import pandas as pd
import pytest

from research.econphysics_prebreakout_v1.contracts import build_structured_snapshots
from research.econphysics_prebreakout_v1.low_snr_m1 import (
    REVENUE_EVIDENCE,
    build_low_snr_states,
)
from research.econphysics_prebreakout_v1.structured_state import build_structured_state
from research.econphysics_prebreakout_v1.shootout_evaluator import (
    _compare_target,
    _integrated_status,
)
from scripts.econphysics_prebreakout_s0_shootout import _admit_rows
from scripts.econphysics_prebreakout_s0_restartable_capture import (
    _ensure_manifest,
    _period_batch_spec,
    _request_key_period,
    _shard_paths,
    _stable_manifest,
    _verify_period_shard,
    _write_shard,
    capture_period_matrix,
)


RECEIPT = "b" * 64
PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")


def _snapshot_rows(
    *,
    security_id: str,
    entity: str,
    as_of: str,
    period_ends: tuple[str, str, str, str, str],
    revenue: tuple[float, float, float, float, float],
    inventory: tuple[float, float, float, float, float],
    operating_income: tuple[float, float, float, float, float],
    capex: tuple[float, float, float, float, float] = (10, 9, 8, 7, 6),
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, period in enumerate(PERIODS):
        rows.append(
            {
                "security_id": security_id,
                "source_entity_id": entity,
                "as_of_date": as_of,
                "available_at": as_of + "T23:59:59.999999Z",
                "relative_period": period,
                "period_end": period_ends[index],
                "IQ_TOTAL_REV": revenue[index],
                "IQ_INVENTORY": inventory[index],
                "IQ_OPER_INC": operating_income[index],
                "IQ_CAPEX_BNK": capex[index],
                "filing_version": "Original",
                "value_unit": "USD_THOUSANDS",
                "source_receipt_sha256": RECEIPT,
            }
        )
    return rows


def _single_date_peer_rows() -> list[dict[str, object]]:
    period_ends = ("2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31")
    rows: list[dict[str, object]] = []
    rows += _snapshot_rows(
        security_id="CIQSEC:IQ1001",
        entity="1001",
        as_of="2025-05-15",
        period_ends=period_ends,
        revenue=(200, 100, 95, 90, 85),
        inventory=(40, 30, 29, 28, 27),
        operating_income=(30, 14, 13, 12, 11),
    )
    rows += _snapshot_rows(
        security_id="CIQSEC:IQ1002",
        entity="1002",
        as_of="2025-05-15",
        period_ends=period_ends,
        revenue=(110, 100, 95, 90, 85),
        inventory=(31, 30, 29, 28, 27),
        operating_income=(16, 14, 13, 12, 11),
    )
    rows += _snapshot_rows(
        security_id="CIQSEC:IQ1003",
        entity="1003",
        as_of="2025-05-15",
        period_ends=period_ends,
        revenue=(101, 100, 95, 90, 85),
        inventory=(30.2, 30, 29, 28, 27),
        operating_income=(14.2, 14, 13, 12, 11),
    )
    return rows


def test_m1_keeps_mixed_evidence_as_nonzero_information() -> None:
    snapshots = build_structured_snapshots(_single_date_peer_rows())
    target = next(snapshot for snapshot in snapshots if snapshot.security_id == "CIQSEC:IQ1001")
    m0 = build_structured_state(target)
    assert m0.inventory_channel.state.value == "MIXED"
    assert m0.inventory_channel.prediction_direction is None

    m1 = build_low_snr_states(snapshots)[
        (target.security_id, target.source_entity_id, target.as_of_date.isoformat())
    ]
    assert m1.inventory_channel.state.value == "MIXED"
    assert m1.inventory_channel.disagreement > 0
    assert m1.inventory_channel.accumulated_strength is not None
    assert m1.inventory_channel.prediction_direction in {-1, 0, 1}
    assert m1.inventory_channel.prediction_direction is not None
    assert m1.inventory_channel.reason == "MIXED_EVIDENCE_RETAINED_WITH_CONTINUOUS_STRENGTH"


def test_m1_continuous_revenue_measurement_does_not_collapse_magnitude_to_sign() -> None:
    snapshots = build_structured_snapshots(_single_date_peer_rows())
    states = build_low_snr_states(snapshots)
    evidence_by_security = {}
    for snapshot in snapshots:
        state = states[(snapshot.security_id, snapshot.source_entity_id, snapshot.as_of_date.isoformat())]
        evidence = next(item for item in state.demand_order.evidence if item.evidence_id == REVENUE_EVIDENCE)
        evidence_by_security[snapshot.security_id] = evidence

    large = evidence_by_security["CIQSEC:IQ1001"]
    medium = evidence_by_security["CIQSEC:IQ1002"]
    small = evidence_by_security["CIQSEC:IQ1003"]
    assert large.log_delta is not None and medium.log_delta is not None and small.log_delta is not None
    assert large.log_delta > medium.log_delta > small.log_delta > 0
    assert large.own_history_robust_z != medium.own_history_robust_z
    assert medium.own_history_robust_z != small.own_history_robust_z
    assert large.economic_strength != medium.economic_strength
    assert medium.economic_strength != small.economic_strength


def test_m1_temporal_accumulation_retains_async_evidence_without_same_snapshot_and() -> None:
    dates = ("2025-05-15", "2025-08-15", "2025-11-15")
    period_grid = (
        ("2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31"),
        ("2025-06-30", "2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30"),
        ("2025-09-30", "2025-06-30", "2025-03-31", "2024-12-31", "2024-09-30"),
    )
    rows: list[dict[str, object]] = []
    for peer in range(3):
        entity = str(2001 + peer)
        security = f"CIQSEC:IQ{2001 + peer}"
        for index, as_of in enumerate(dates):
            base = 100 + 10 * index
            if peer == 0:
                latest_revenue = (120, 132, 130)[index]
            elif peer == 1:
                latest_revenue = (110, 121, 133)[index]
            else:
                latest_revenue = (105, 115, 126)[index]
            revenue = (
                latest_revenue,
                base,
                base * 0.95,
                base * 0.90,
                base * 0.85,
            )
            rows += _snapshot_rows(
                security_id=security,
                entity=entity,
                as_of=as_of,
                period_ends=period_grid[index],
                revenue=revenue,
                inventory=(30, 31, 32, 33, 34),
                operating_income=(15, 14, 13, 12, 11),
            )

    snapshots = build_structured_snapshots(rows)
    states = build_low_snr_states(snapshots)
    latest = states[("CIQSEC:IQ2001", "2001", dates[-1])]
    assert latest.demand_order.temporal_observation_count == 3
    assert latest.demand_order.instantaneous_strength is not None
    assert latest.demand_order.accumulated_strength is not None
    assert latest.demand_order.latest_observation_steps_ago == 0
    # The latest quarter need not agree with both earlier quarters; the signal is
    # accumulated rather than requiring all evidence on one snapshot.
    assert latest.demand_order.prediction_direction is not None


def _model_report(lifts: tuple[float, float, float, float], associations: tuple[float, float, float, float]) -> dict[str, object]:
    return {
        "temporal_folds": [
            {
                "fold": index + 1,
                "N": 100,
                "coverage_rate": 0.8,
                "lift_vs_no_information_baseline": lift,
                "directional_association": association,
                "meets_minimum_n_and_coverage": True,
                "supports_mechanism": lift > 1.0 and association > 0.0,
            }
            for index, (lift, association) in enumerate(zip(lifts, associations))
        ]
    }


def test_shootout_requires_stable_fold_lift_and_has_no_any_target_pass_boolean() -> None:
    m0 = _model_report((1.00, 1.01, 0.99, 1.00), (0.1, 0.1, 0.1, 0.1))
    m1 = _model_report((1.10, 1.12, 1.08, 0.98), (0.4, 0.4, 0.3, 0.2))
    comparison = _compare_target(m0, m1)
    assert comparison["status"] == "M1_STABLE_LIFT"
    assert comparison["m1_better_fold_count"] == 3

    targets = {
        "a": {"comparison": {"status": "M1_STABLE_LIFT"}},
        "b": {"comparison": {"status": "M1_STABLE_LIFT"}},
        "c": {"comparison": {"status": "NO_CLEAR_M1_LIFT"}},
    }
    assert _integrated_status(targets) == "M1_STABLE_EXTRACTION_LIFT"
    targets["b"] = {"comparison": {"status": "NO_CLEAR_M1_LIFT"}}
    assert _integrated_status(targets) == "PARTIAL_SUPPORT"


def test_shootout_does_not_call_less_wrong_below_baseline_partial_support() -> None:
    m0 = _model_report((0.60, 0.70, 0.65, 0.55), (-0.3, -0.2, -0.3, -0.4))
    m1 = _model_report((0.68, 0.78, 0.72, 0.64), (-0.2, -0.1, -0.2, -0.2))
    comparison = _compare_target(m0, m1)
    assert comparison["median_lift_delta_m1_minus_m0"] > 0
    assert comparison["m1_better_fold_count"] == 0
    assert comparison["status"] == "NO_CLEAR_M1_LIFT"


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_real_corpus_admission_quarantines_missing_period_and_older_duplicate_alias() -> None:
    raw_rows: list[dict[str, str]] = []
    period_ends = ("2025-03-31", "2025-03-31", "2024-09-30", "2024-06-30", "")
    for index, relative_period in enumerate(PERIODS):
        raw_rows.append(
            {
                "as_of_date": "2025-05-15",
                "source_entity_id": "123",
                "relative_period": relative_period,
                "period_end": period_ends[index],
                "IQ_TOTAL_REV": str(100 - index),
                "IQ_INVENTORY": str(20 - index),
                "IQ_OPER_INC": str(10 - index),
                "IQ_CAPEX_BNK": str(5 - index),
                "provider_function": "SPG",
                "filing_version": "Original",
            }
        )

    admitted, report = _admit_rows(
        raw_rows,
        entity_to_security={"123": "CIQSEC:IQ123"},
        receipt_sha256="c" * 64,
        expected_fq0_by_snapshot={("123", "2025-05-15"): "2025-03-31"},
    )
    by_period = {str(row["relative_period"]): row for row in admitted}
    assert by_period["FQ0"]["period_end"] == "2025-03-31"
    assert by_period["FQ0"]["IQ_TOTAL_REV"] == "100"
    assert by_period["FQ-1"]["period_end"] == ""
    assert all(by_period["FQ-1"][field] == "" for field in ("IQ_TOTAL_REV", "IQ_INVENTORY", "IQ_OPER_INC", "IQ_CAPEX_BNK"))
    assert by_period["FQ-4"]["period_end"] == ""
    assert all(by_period["FQ-4"][field] == "" for field in ("IQ_TOTAL_REV", "IQ_INVENTORY", "IQ_OPER_INC", "IQ_CAPEX_BNK"))
    assert report["duplicate_period_end_snapshot_count"] == 1
    assert report["duplicate_alias_row_count"] == 1
    assert report["missing_period_end_rows_quarantined"] == 1
    assert report["measurement_cells_cleared_due_duplicate_period_end"] == 4
    assert report["measurement_cells_cleared_due_missing_period_end"] == 4
    # The shared admitted bytes are lawful for both M0 and M1 consumers.
    snapshots = build_structured_snapshots(admitted)
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.by_period()["FQ-1"].total_revenue is None
    assert snapshot.by_period()["FQ-4"].inventory is None


def test_real_corpus_admission_quarantines_whole_snapshot_on_stage1_stage3_fq0_mismatch() -> None:
    raw_rows = [
        {
            "as_of_date": "2025-05-15",
            "source_entity_id": "123",
            "relative_period": relative_period,
            "period_end": period_end,
            "IQ_TOTAL_REV": "100",
            "IQ_INVENTORY": "20",
            "IQ_OPER_INC": "10",
            "IQ_CAPEX_BNK": "5",
            "provider_function": "SPG",
            "filing_version": "Original",
        }
        for relative_period, period_end in zip(
            PERIODS,
            ("2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31", "2023-12-31"),
        )
    ]
    admitted, report = _admit_rows(
        raw_rows,
        entity_to_security={"123": "CIQSEC:IQ123"},
        receipt_sha256="d" * 64,
        expected_fq0_by_snapshot={("123", "2025-05-15"): "2025-03-31"},
    )
    assert admitted == []
    assert report["fq0_plan_capture_mismatch_snapshot_count"] == 1
    assert report["fq0_plan_capture_mismatch_rows_quarantined"] == 5


def test_restartable_period_transport_validates_and_skips_complete_shards(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = tmp_path / "plan.csv"
    master = tmp_path / "master.csv"
    out = tmp_path / "final" / "fq0_period_matrix.csv"
    transport = tmp_path / "transport"
    _write_csv(
        plan,
        [
            {"source_entity_id": "101", "security_id": "CIQSEC:IQ101", "as_of_date": "2025-05-02"},
            {"source_entity_id": "202", "security_id": "CIQSEC:IQ202", "as_of_date": "2025-05-09"},
        ],
    )
    _write_csv(
        master,
        [
            {"SP_ENTITY_ID": "101", "security_id": "CIQSEC:IQ101"},
            {"SP_ENTITY_ID": "202", "security_id": "CIQSEC:IQ202"},
        ],
    )
    pairs = [
        (pd.Timestamp("2025-05-02"), "101"),
        (pd.Timestamp("2025-05-09"), "202"),
    ]
    manifest = _stable_manifest(
        mode="PERIOD_MATRIX",
        plan_path=plan,
        master_path=master,
        batch_requests=200,
        total_units=2,
        total_provider_requests=2,
        total_batches=1,
        metrics=["IQ_PERIOD_END"],
    )
    _ensure_manifest(transport, manifest)
    start, end, batch = _period_batch_spec(pairs, 200, 0)
    data_path, receipt_path = _shard_paths(transport, mode="PERIOD_MATRIX", batch_index=0)
    rows = [
        {
            "as_of_date": "2025-05-02",
            "source_entity_id": "101",
            "fq0_period_end": "2025-03-31",
            "retrieved_at_utc": "2026-08-11T00:00:00+00:00",
            "provider_function": "SPG",
            "provider_metric": "IQ_PERIOD_END",
            "relative_period": "FQ0",
            "filing_version": "Original",
        },
        {
            "as_of_date": "2025-05-09",
            "source_entity_id": "202",
            "fq0_period_end": "2025-03-31",
            "retrieved_at_utc": "2026-08-11T00:00:00+00:00",
            "provider_function": "SPG",
            "provider_metric": "IQ_PERIOD_END",
            "relative_period": "FQ0",
            "filing_version": "Original",
        },
    ]
    _write_shard(
        data_path=data_path,
        receipt_path=receipt_path,
        rows=rows,
        manifest=manifest,
        batch_index=0,
        unit_start=start,
        unit_end=end,
        provider_request_count=2,
        first_request_key=_request_key_period(*batch[0]),
        last_request_key=_request_key_period(*batch[-1]),
        retrieved_at="2026-08-11T00:00:00+00:00",
    )
    assert len(
        _verify_period_shard(
            data_path=data_path,
            receipt_path=receipt_path,
            manifest=manifest,
            batch_index=0,
            unit_start=start,
            unit_end=end,
            batch=batch,
        )
    ) == 2

    async def _provider_must_not_run(*args, **kwargs):
        raise AssertionError("provider should not be called for a complete valid shard")

    monkeypatch.setattr(
        "scripts.econphysics_prebreakout_s0_restartable_capture._fetch_provider_batch",
        _provider_must_not_run,
    )
    args = Namespace(
        plan=str(plan),
        master=str(master),
        out=str(out),
        transport_dir=str(transport),
        batch_requests=200,
        max_batches=1,
        allow_missing_period_end=True,
        port=9230,
    )
    asyncio.run(capture_period_matrix(args))
    assert out.exists()
    assert out.with_suffix(".receipt.json").exists()
    assert len(list(csv.DictReader(out.open("r", encoding="utf-8", newline="")))) == 2
