from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from research.evidence_schema import EVIDENCE_SCHEMA_VERSION, EvidencePacket, write_evidence_packet
from research.status import ResearchStatus
from research.strategy_cartridge import StrategyCartridge


def test_evidence_schema_version_is_v0() -> None:
    assert EVIDENCE_SCHEMA_VERSION == "research_evidence_v0"


def test_strategy_cartridge_serializes_cost_and_benchmark_policy(tmp_path) -> None:
    cartridge = StrategyCartridge(
        strategy_id="fixture",
        strategy_version="0.1.0",
        strategy_role="signal_strategy",
        universe_mode="r3000_pit",
        input_loader_name="fixture_loader",
        rebalance_schedule="daily",
        execution_lag="one_bar",
        turnover_cost_rate=0.001,
        benchmark_policy={"required": ["cash"]},
        start_date="2026-01-02",
        end_date="2026-01-06",
        output_dir=tmp_path,
    )

    payload = cartridge.to_dict()

    assert payload["costs" if False else "turnover_cost_rate"] == 0.001
    assert payload["benchmark_policy"]["required"] == ["cash"]
    assert json.loads(json.dumps(payload, default=str))["portfolio"]["cash_policy"] == "implicit_residual_cash"


def test_write_evidence_packet_uses_atomic_replace_for_json_and_csv(monkeypatch, tmp_path: Path) -> None:
    packet = EvidencePacket(
        run_id="atomic_run",
        status=ResearchStatus.EXPLORATORY,
        output_dir=tmp_path / "atomic_run",
        cartridge={"strategy_id": "fixture"},
        run_metadata={"run_id": "atomic_run"},
        gate_results={"passed": True},
        input_signatures={"returns": "sig"},
        pit_membership_proof={"proof_type": "fixture"},
        leakage_checks={"pit_inputs_only": True},
        data_quality_report={"missing_executed_return_count": 0},
        metrics={"trading_days": 1},
        benchmark_metrics={},
        verdict={"status": "exploratory"},
    )
    replace_calls: list[tuple[Path, Path]] = []

    def fake_replace(src, dst):
        src_path = Path(src)
        dst_path = Path(dst)
        assert src_path.parent == dst_path.parent
        assert src_path.name.startswith(f".{dst_path.name}.")
        assert src_path.name.endswith(".tmp")
        replace_calls.append((src_path, dst_path))
        return original_replace(src, dst)

    original_replace = os.replace
    monkeypatch.setattr(os, "replace", fake_replace)

    artifacts = write_evidence_packet(
        packet,
        target_weights=pd.DataFrame({"101": [0.5]}, index=pd.to_datetime(["2026-01-02"])),
    )

    assert Path(artifacts["evidence_packet.json"]).exists()
    assert Path(artifacts["target_weights.csv"]).exists()
    assert replace_calls
    assert {dst.name for _, dst in replace_calls} >= {"evidence_packet.json", "target_weights.csv"}
    assert replace_calls[-1][1].name == "evidence_packet.json"
    assert not list((tmp_path / "atomic_run").glob("*.tmp"))


def test_write_evidence_packet_removes_stale_final_manifest_on_component_failure(monkeypatch, tmp_path: Path) -> None:
    packet = EvidencePacket(
        run_id="stale_run",
        status=ResearchStatus.EXPLORATORY,
        output_dir=tmp_path / "stale_run",
        cartridge={"strategy_id": "fixture"},
        run_metadata={"run_id": "stale_run"},
        gate_results={"passed": True},
        input_signatures={"returns": "sig"},
        pit_membership_proof={"proof_type": "fixture"},
        leakage_checks={"pit_inputs_only": True},
        data_quality_report={"missing_executed_return_count": 0},
        metrics={"trading_days": 1},
        benchmark_metrics={},
        verdict={"status": "exploratory"},
    )
    packet.output_dir.mkdir(parents=True)
    stale_manifest = packet.output_dir / "evidence_packet.json"
    stale_manifest.write_text('{"stale": true}', encoding="utf-8")

    original_replace = os.replace

    def fail_on_metrics(src, dst):
        if Path(dst).name == "metrics.json":
            raise OSError("simulated component write failure")
        return original_replace(src, dst)

    monkeypatch.setattr(os, "replace", fail_on_metrics)

    with pytest.raises(OSError, match="simulated component write failure"):
        write_evidence_packet(packet)

    assert not stale_manifest.exists()
    assert not list(packet.output_dir.glob("*.tmp"))
