from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from research.evidence_schema import (
    EVIDENCE_MANIFEST_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    EvidencePacket,
    write_evidence_packet,
)
from research.status import ResearchStatus


def _packet(tmp_path: Path, run_id: str = "sealed_run") -> EvidencePacket:
    return EvidencePacket(
        run_id=run_id,
        status=ResearchStatus.EXPLORATORY,
        output_dir=tmp_path / run_id,
        cartridge={"strategy_id": "fixture"},
        run_metadata={"run_id": run_id},
        gate_results={"passed": True},
        input_signatures={"returns": "sig"},
        pit_membership_proof={"proof_type": "fixture"},
        leakage_checks={"pit_inputs_only": True},
        data_quality_report={"missing_executed_return_count": 0},
        metrics={"trading_days": 1},
        benchmark_metrics={},
        verdict={"status": "exploratory"},
    )


def test_evidence_schema_is_v1_with_hash_manifest() -> None:
    assert EVIDENCE_SCHEMA_VERSION == "research_evidence_v1"
    assert EVIDENCE_MANIFEST_VERSION == "research_evidence_manifest_v1"


def test_write_evidence_packet_seals_every_component_by_hash(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    artifacts = write_evidence_packet(
        packet,
        target_weights=pd.DataFrame({"101": [0.5]}, index=pd.to_datetime(["2026-01-02"])),
    )
    manifest_path = Path(artifacts["evidence_manifest.json"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == EVIDENCE_MANIFEST_VERSION
    assert "evidence_manifest.json" not in manifest["files"]
    assert "evidence_packet.json" in manifest["files"]
    assert "target_weights.csv" in manifest["files"]
    for name, metadata in manifest["files"].items():
        path = packet.output_dir / name
        assert metadata["bytes"] == path.stat().st_size
        assert metadata["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_existing_run_directory_is_immutable_and_cannot_be_reused(tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    write_evidence_packet(packet)
    with pytest.raises(FileExistsError, match="evidence_run_directory_already_exists"):
        write_evidence_packet(packet)


def test_manifest_is_written_last_and_component_failure_leaves_no_false_manifest(monkeypatch, tmp_path: Path) -> None:
    packet = _packet(tmp_path)
    import research.evidence_schema as schema

    original = schema._write_text_atomic

    def fail_metrics(path: Path, text: str) -> None:
        if path.name == "metrics.json":
            raise OSError("simulated component failure")
        original(path, text)

    monkeypatch.setattr(schema, "_write_text_atomic", fail_metrics)
    with pytest.raises(OSError, match="simulated component failure"):
        write_evidence_packet(packet)
    assert not (packet.output_dir / "evidence_manifest.json").exists()
