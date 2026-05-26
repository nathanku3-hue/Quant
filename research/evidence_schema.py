"""Evidence packet schema helpers for research backtest v0."""

from __future__ import annotations

import json
import os
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

import pandas as pd

from research.status import ResearchStatus


EVIDENCE_SCHEMA_VERSION = "research_evidence_v0"


@dataclass(frozen=True)
class EvidencePacket:
    """In-memory representation of the mandatory v0 evidence packet."""

    run_id: str
    status: ResearchStatus
    output_dir: Path
    cartridge: Mapping[str, Any]
    run_metadata: Mapping[str, Any]
    gate_results: Mapping[str, Any]
    input_signatures: Mapping[str, Any]
    pit_membership_proof: Mapping[str, Any]
    leakage_checks: Mapping[str, Any]
    data_quality_report: Mapping[str, Any]
    metrics: Mapping[str, Any]
    benchmark_metrics: Mapping[str, Any]
    verdict: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": EVIDENCE_SCHEMA_VERSION,
            "run_id": self.run_id,
            "status": self.status.value,
            "output_dir": str(self.output_dir),
            "cartridge": dict(self.cartridge),
            "run_metadata": dict(self.run_metadata),
            "gate_results": dict(self.gate_results),
            "input_signatures": dict(self.input_signatures),
            "pit_membership_proof": dict(self.pit_membership_proof),
            "leakage_checks": dict(self.leakage_checks),
            "data_quality_report": dict(self.data_quality_report),
            "metrics": dict(self.metrics),
            "benchmark_metrics": dict(self.benchmark_metrics),
            "verdict": dict(self.verdict),
        }


def write_evidence_packet(
    packet: EvidencePacket,
    *,
    target_weights: pd.DataFrame | None = None,
    executed_weights: pd.DataFrame | None = None,
    equity_curve: pd.Series | None = None,
    benchmark_curves: Mapping[str, pd.Series] | None = None,
    simulation_result: pd.DataFrame | None = None,
) -> dict[str, str]:
    """Write a stable CSV/JSON evidence directory and return artifact paths."""

    output_dir = packet.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    _clear_previous_final_manifest(output_dir)
    artifacts: dict[str, str] = {}

    json_payloads: dict[str, Mapping[str, Any]] = {
        "cartridge.json": packet.cartridge,
        "run_metadata.json": packet.run_metadata,
        "verdict.json": packet.verdict,
        "gate_results.json": packet.gate_results,
        "input_signatures.json": packet.input_signatures,
        "pit_membership_proof.json": packet.pit_membership_proof,
        "leakage_checks.json": packet.leakage_checks,
        "metrics.json": packet.metrics,
        "benchmark_metrics.json": packet.benchmark_metrics,
        "data_quality_report.json": packet.data_quality_report,
    }
    for filename, payload in json_payloads.items():
        path = output_dir / filename
        _write_text_atomic(path, json.dumps(payload, indent=2, sort_keys=True, default=str))
        artifacts[filename] = str(path)

    if target_weights is not None:
        artifacts["target_weights.csv"] = _write_frame(output_dir / "target_weights.csv", target_weights)
    if executed_weights is not None:
        artifacts["executed_weights.csv"] = _write_frame(output_dir / "executed_weights.csv", executed_weights)
    if simulation_result is not None:
        artifacts["turnover.csv"] = _write_frame(output_dir / "turnover.csv", simulation_result[["turnover"]])
        artifacts["costs.csv"] = _write_frame(output_dir / "costs.csv", simulation_result[["cost"]])
    if equity_curve is not None:
        artifacts["equity_curve.csv"] = _write_frame(output_dir / "equity_curve.csv", equity_curve.to_frame("equity"))
    if benchmark_curves:
        benchmark_frame = pd.DataFrame({name: curve for name, curve in benchmark_curves.items()})
        artifacts["benchmark_curves.csv"] = _write_frame(output_dir / "benchmark_curves.csv", benchmark_frame)
    if executed_weights is not None:
        exposure = pd.DataFrame(
            {
                "gross_exposure": executed_weights.abs().sum(axis=1),
                "cash_residual": 1.0 - executed_weights.sum(axis=1),
            }
        )
        artifacts["exposure.csv"] = _write_frame(output_dir / "exposure.csv", exposure)

    packet_path = output_dir / "evidence_packet.json"
    _write_text_atomic(packet_path, json.dumps(packet.to_dict(), indent=2, sort_keys=True, default=str))
    artifacts["evidence_packet.json"] = str(packet_path)

    return artifacts


def _write_frame(path: Path, frame: pd.DataFrame) -> str:
    tmp_path = _tmp_path_for(path)
    try:
        frame.to_csv(tmp_path, index_label="date")
        os.replace(tmp_path, path)
    finally:
        with suppress(FileNotFoundError):
            tmp_path.unlink()
    return str(path)


def _write_text_atomic(path: Path, text: str) -> None:
    tmp_path = _tmp_path_for(path)
    try:
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        with suppress(FileNotFoundError):
            tmp_path.unlink()


def _tmp_path_for(path: Path) -> Path:
    return path.with_name(f".{path.name}.{uuid4().hex}.tmp")


def _clear_previous_final_manifest(output_dir: Path) -> None:
    with suppress(FileNotFoundError):
        (output_dir / "evidence_packet.json").unlink()
