from __future__ import annotations

from argparse import Namespace
from datetime import date
import gzip
import json
from pathlib import Path

import pandas as pd
import pytest

from research.econphysics_prebreakout_v1 import (
    NodeState,
    NodeTransition,
    StructuredStateContractError,
    build_structured_snapshots,
    build_structured_state,
    deterministic_xs_holdout,
    evaluate_structured_transitions,
)
from research.econphysics_prebreakout_v1.transition_evaluator import (
    TransitionObservation,
    _evaluate_target,
)
from scripts.aov0_capture_ciq_historical_pit_productquery import (
    S0_STRUCTURED_TRANSITION_METRICS,
    _period_probe_pairs,
    _requested_transition_metrics,
)
from scripts.econphysics_prebreakout_s0_request import (
    S0RequestError,
    compile_period_change_plan,
    compile_w3_request_rows,
)


RECEIPT = "a" * 64
PERIODS = ("FQ0", "FQ-1", "FQ-2", "FQ-3", "FQ-4")


def _security(*, holdout: bool = False) -> str:
    for number in range(1000, 10000):
        candidate = f"CIQSEC:IQ{number}"
        if deterministic_xs_holdout(candidate) is holdout:
            return candidate
    raise AssertionError("fixture security bucket not found")


def _snapshot_rows(
    *,
    security_id: str,
    entity: str,
    as_of: str,
    period_ends: tuple[str, str, str, str, str],
    revenue: tuple[object, object, object, object, object],
    inventory: tuple[object, object, object, object, object],
    operating_income: tuple[object, object, object, object, object],
    capex: tuple[object, object, object, object, object],
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


def _base_rows(*, security_id: str | None = None) -> list[dict[str, object]]:
    return _snapshot_rows(
        security_id=security_id or _security(),
        entity="12345",
        as_of="2025-05-15",
        period_ends=("2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31"),
        revenue=(120, 110, 108, 104, 100),
        inventory=(30, 32, 35, 38, 40),
        operating_income=(18, 15, 14, 13, 12),
        capex=(25, 20, 18, 17, 15),
    )


def test_structured_state_builds_only_frozen_directions_and_lawful_ratios() -> None:
    snapshot = build_structured_snapshots(_base_rows())[0]
    state = build_structured_state(snapshot)

    assert state.inventory_channel.state == NodeState.POSITIVE
    assert state.inventory_channel.transition == NodeTransition.IMPROVING
    assert state.inventory_channel.prediction_direction == 1
    assert state.demand_order.state == NodeState.POSITIVE
    assert state.demand_order.prediction_direction == 1
    assert state.margin_cash.state == NodeState.POSITIVE
    assert state.margin_cash.prediction_direction == 1

    assert state.supply_capacity.state == NodeState.UNOBSERVED
    assert state.supply_capacity.prediction_direction is None
    assert state.supply_capacity.reason == "CAPEX_IS_CYCLE_EVIDENCE_NOT_CAPACITY_STATE"
    assert state.capex_cycle_evidence.latest_vs_prior == 1


def test_inventory_conflict_is_explicit_mixed_not_fitted_away() -> None:
    rows = _snapshot_rows(
        security_id=_security(),
        entity="12345",
        as_of="2025-05-15",
        period_ends=("2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31"),
        revenue=(200, 100, 95, 90, 80),
        inventory=(40, 30, 29, 28, 25),
        operating_income=(20, 10, 9, 8, 7),
        capex=(10, 9, 8, 7, 6),
    )
    state = build_structured_state(build_structured_snapshots(rows)[0])
    assert state.inventory_channel.state == NodeState.MIXED
    assert state.inventory_channel.transition == NodeTransition.UNOBSERVED
    assert state.inventory_channel.prediction_direction is None
    assert state.inventory_channel.reason == "MATERIAL_DIRECTIONAL_CONFLICT"


def test_nonpositive_revenue_keeps_ratio_nodes_unobserved() -> None:
    rows = _base_rows()
    for row in rows:
        row["IQ_TOTAL_REV"] = 0
    state = build_structured_state(build_structured_snapshots(rows)[0])
    assert state.margin_cash.state == NodeState.UNOBSERVED
    assert state.margin_cash.prediction_direction is None


def test_contract_fails_closed_on_future_period_or_non_original_filing() -> None:
    rows = _base_rows()
    rows[0]["period_end"] = "2025-06-30"
    with pytest.raises(StructuredStateContractError, match="future_period_end"):
        build_structured_snapshots(rows)

    rows = _base_rows()
    rows[0]["filing_version"] = "Current"
    with pytest.raises(StructuredStateContractError, match="original_filing_required"):
        build_structured_snapshots(rows)


def test_next_pit_targets_are_economic_self_referential_falsifiers() -> None:
    security_id = _security(holdout=False)
    first = _base_rows(security_id=security_id)
    second = _snapshot_rows(
        security_id=security_id,
        entity="12345",
        as_of="2025-08-15",
        period_ends=("2025-06-30", "2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30"),
        revenue=(130, 120, 110, 108, 104),
        inventory=(29, 30, 32, 35, 38),
        operating_income=(21, 18, 15, 14, 13),
        capex=(27, 25, 20, 18, 17),
    )
    report = evaluate_structured_transitions(build_structured_snapshots([*first, *second]))
    assert report["adjacent_transition_pair_count"] == 1
    assert report["pit_violations"] == 0
    assert report["fit_or_tuning_performed"] is False
    assert report["market_data_access_performed"] is False
    assert report["equity_outcome_access_performed"] is False
    assert report["w6_access_performed"] is False
    assert report["selection_performed"] is False
    for target in report["targets"].values():
        assert target["overall_development"]["N"] == 1
        assert target["mechanism_status"] == "UNOBSERVED"


def _fold_observations(*, perfect: bool) -> list[TransitionObservation]:
    rows: list[TransitionObservation] = []
    for fold in range(4):
        actuals = (1, 1, -1)
        predictions = actuals if perfect else (1, 1, 1)
        for index, (actual, prediction) in enumerate(zip(actuals, predictions)):
            rows.append(
                TransitionObservation(
                    target_id="FIXTURE_TARGET",
                    node_id="FIXTURE_NODE",
                    security_id=f"CIQSEC:IQ{10000 + fold * 10 + index}",
                    source_entity_id=str(20000 + fold * 10 + index),
                    feature_as_of_date=f"2025-{fold + 1:02d}-15",
                    feature_period_end=f"2024-{fold + 1:02d}-28",
                    target_as_of_date=f"2025-{fold + 2:02d}-15",
                    target_period_end=f"2025-{fold + 1:02d}-28",
                    prediction_direction=prediction,
                    actual_direction=actual,
                    xs_holdout=False,
                    temporal_fold=fold,
                )
            )
    return rows


def test_majority_temporal_fold_gate_passes_only_with_lift_above_one_and_stable_direction() -> None:
    report = _evaluate_target(_fold_observations(perfect=True))
    assert report["informative_temporal_fold_count"] == 4
    assert report["supporting_temporal_fold_count"] == 4
    assert report["mechanism_status"] == "PASS"
    for fold in report["temporal_folds"]:
        assert fold["N"] == 3
        assert fold["no_information_baseline_hit_rate"] == pytest.approx(2 / 3)
        assert fold["directional_hit_rate"] == pytest.approx(1.0)
        assert fold["lift_vs_no_information_baseline"] == pytest.approx(1.5)
        assert fold["contradiction_count"] == 0
        assert fold["directional_association"] == pytest.approx(1.0)
        assert fold["supports_mechanism"] is True

    failed = _evaluate_target(_fold_observations(perfect=False))
    assert failed["mechanism_status"] == "FAILED"
    assert failed["supporting_temporal_fold_count"] == 0
    for fold in failed["temporal_folds"]:
        assert fold["lift_vs_no_information_baseline"] == pytest.approx(1.0)


def test_fewer_than_three_informative_temporal_folds_is_unobserved() -> None:
    rows = [row for row in _fold_observations(perfect=True) if row.temporal_fold < 2]
    report = _evaluate_target(rows)
    assert report["informative_temporal_fold_count"] == 2
    assert report["mechanism_status"] == "UNOBSERVED"


def test_w3_compiler_excludes_w6_and_builds_date_local_probe_pairs(tmp_path: Path) -> None:
    root = tmp_path / "w3"
    (root / "authority").mkdir(parents=True)
    pre_w6 = ["2025-03-24", "2025-03-25", "2025-03-28", "2025-03-31", "2025-04-01", "2025-04-04"]
    partition = {
        "family_id": "PREBREAKOUT_DISCOVERY_v1",
        "feature_warmup": pre_w6[:3],
        "w5_development": pre_w6[3:5],
        "post_development_embargo": pre_w6[5:],
        "w6_lockbox_decisions": ["2025-04-07"],
        "lockbox_label_maturity_tail": ["2025-04-08"],
        "w6_labels_opened": False,
        "development_labels_overlap_w6_lockbox": False,
        "partition_sha256": "fixture-domain-hash",
    }
    (root / "session_partition.json").write_text(json.dumps(partition), encoding="utf-8")
    (root / "authority.manifest.json").write_text("{}", encoding="utf-8")
    for index, session in enumerate(pre_w6):
        eligible = [
            {"security_id": "CIQSEC:IQ101", "company_id": "101"},
        ]
        if index >= 3:
            eligible.append({"security_id": "CIQSEC:IQ202", "company_id": "202"})
        packet = {
            "decision_session_date": session,
            "financial_alpha_evidence": 0,
            "source_authority": {
                "historical_as_of_mechanically_bound": True,
                "ticker_fallback_used": False,
                "permno_fallback_used": False,
                "company_entity_fallback_used": False,
                "current_primary_back_projection_used": False,
                "current_survivor_back_projection_used": False,
            },
            "eligible_rows": eligible,
        }
        path = root / "authority" / f"date_{session.replace('-', '')}.json.gz"
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            json.dump(packet, handle)

    master, spine, probe, metadata = compile_w3_request_rows(root)
    assert metadata["pre_w6_session_count"] == 6
    assert metadata["pre_w6_last_session"] == "2025-04-04"
    assert metadata["weekly_as_of_count"] == 2
    assert metadata["master_pair_count"] == 2
    assert metadata["eligible_row_count"] == 9
    assert metadata["period_probe_pair_count"] == 3
    assert metadata["w6_decision_count_excluded"] == 1
    assert metadata["maturity_tail_count_excluded"] == 1
    assert [row["as_of_date"] for row in spine] == ["2025-03-28", "2025-04-04"]
    assert [(row["source_entity_id"], row["as_of_date"]) for row in probe] == [
        ("101", "2025-03-28"),
        ("101", "2025-04-04"),
        ("202", "2025-04-04"),
    ]
    assert {row["SP_ENTITY_ID"] for row in master} == {"101", "202"}


def test_transition_plan_has_no_initial_pull_and_does_not_bridge_missing_probe() -> None:
    master = [{"SP_ENTITY_ID": "123", "security_id": "CIQSEC:IQ123"}]
    matrix = [
        {"source_entity_id": "123", "as_of_date": "2025-01-03", "fq0_period_end": "2024-09-30"},
        {"source_entity_id": "123", "as_of_date": "2025-01-10", "fq0_period_end": "2024-09-30"},
        {"source_entity_id": "123", "as_of_date": "2025-02-07", "fq0_period_end": "2024-12-31"},
        {"source_entity_id": "123", "as_of_date": "2025-03-28", "fq0_period_end": ""},
        {"source_entity_id": "123", "as_of_date": "2025-04-04", "fq0_period_end": "2025-03-31"},
        {"source_entity_id": "123", "as_of_date": "2025-04-11", "fq0_period_end": "2025-03-31"},
    ]
    plan = compile_period_change_plan(matrix, master)
    assert plan == [
        {
            "source_entity_id": "123",
            "security_id": "CIQSEC:IQ123",
            "as_of_date": "2025-02-07",
            "fq0_period_end": "2024-12-31",
            "prior_probe_as_of_date": "2025-01-10",
            "prior_fq0_period_end": "2024-09-30",
            "transition_reason": "FQ0_PERIOD_CHANGE",
        }
    ]

    regression = [
        *matrix[:2],
        {"source_entity_id": "123", "as_of_date": "2025-02-07", "fq0_period_end": "2024-06-30"},
        {"source_entity_id": "123", "as_of_date": "2025-02-14", "fq0_period_end": "2024-09-30"},
        {"source_entity_id": "123", "as_of_date": "2025-02-21", "fq0_period_end": "2024-12-31"},
    ]
    assert compile_period_change_plan(regression, master) == [
        {
            "source_entity_id": "123",
            "security_id": "CIQSEC:IQ123",
            "as_of_date": "2025-02-21",
            "fq0_period_end": "2024-12-31",
            "prior_probe_as_of_date": "2025-02-14",
            "prior_fq0_period_end": "2024-09-30",
            "transition_reason": "FQ0_PERIOD_CHANGE",
        }
    ]


def test_productquery_path_supports_exact_pair_probes_and_exact_s0_metric_subset() -> None:
    master = pd.DataFrame({"SP_ENTITY_ID": ["123", "456"], "security_id": ["CIQSEC:IQ123", "CIQSEC:IQ456"]})
    plan = pd.DataFrame(
        {
            "source_entity_id": ["123", "456"],
            "security_id": ["CIQSEC:IQ123", "CIQSEC:IQ456"],
            "as_of_date": ["2025-01-03", "2025-01-10"],
        }
    )
    pairs, mode = _period_probe_pairs(plan, master)
    assert mode == "EXACT_ENTITY_DATE_PAIRS"
    assert [(stamp.date().isoformat(), entity) for stamp, entity in pairs] == [
        ("2025-01-03", "123"),
        ("2025-01-10", "456"),
    ]

    args = Namespace(metric=list(S0_STRUCTURED_TRANSITION_METRICS))
    assert _requested_transition_metrics(args) == S0_STRUCTURED_TRANSITION_METRICS
    with pytest.raises(ValueError, match="period_metric_required"):
        _requested_transition_metrics(Namespace(metric=["IQ_TOTAL_REV"]))
    with pytest.raises(ValueError, match="metric_not_allowed"):
        _requested_transition_metrics(Namespace(metric=["IQ_PERIOD_END", "IQ_FAKE"]))


def test_s0_runtime_contains_no_fit_or_equity_label_dependency() -> None:
    root = Path("research/econphysics_prebreakout_v1")
    text = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = (
        "sklearn",
        ".fit(",
        ".train(",
        "winner_label",
        "realized_total_return",
        "right_tail_wealth",
        "prebreakout_untouched_evaluator_v1",
        "discovery_outcomes",
        "submit_order",
    )
    assert not any(token in text for token in forbidden)
