from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from v2_discovery.fast_sim.boundary import V2ProxyBoundary
from v2_discovery.fast_sim.cost_model import FastProxyCostModel
from v2_discovery.fast_sim.fixtures import load_synthetic_proxy_fixture
from v2_discovery.fast_sim.ledger import build_synthetic_ledger
from v2_discovery.fast_sim.ledger import validate_synthetic_ledger_output
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.schemas import ProxyRunStatus
from v2_discovery.fast_sim.validation import validate_finite_numeric
from v2_discovery.fast_sim.validation import validate_no_nulls
from v2_discovery.fast_sim.validation import validate_positive_numeric
from v2_discovery.fast_sim.validation import validate_required_columns
from v2_discovery.registry import CandidateRegistry


SYNTHETIC_PROXY_ENGINE_VERSION = "0.1.0"


@dataclass(frozen=True)
class SyntheticProxyRunOutput:
    proxy_result: ProxyRunResult
    positions: pd.DataFrame
    ledger: pd.DataFrame
    result: dict[str, Any]


class SyntheticFastProxySimulator:
    engine_version = SYNTHETIC_PROXY_ENGINE_VERSION

    def run(
        self,
        spec: ProxyRunSpec,
        *,
        registry: CandidateRegistry,
        actor: str = "v2_synthetic_fast_proxy",
    ) -> SyntheticProxyRunOutput:
        boundary = V2ProxyBoundary(registry)
        verdict = boundary.verdict_for(spec)
        fixture = load_synthetic_proxy_fixture(spec.manifest_uri, repo_root=registry.repo_root)
        cost_model = FastProxyCostModel.from_mapping(spec.cost_model)
        ledger_output = build_synthetic_ledger(fixture.prices, fixture.weights, cost_model)
        validate_synthetic_ledger_output(ledger_output.positions, ledger_output.ledger)
        result_summary = _build_result_summary(
            manifest_uri=spec.manifest_uri,
            boundary_verdict=verdict,
            ledger=ledger_output.ledger,
        )
        _validate_result_summary(result_summary)
        note = registry.add_note(
            spec.candidate_id,
            actor=actor,
            note=(
                f"synthetic proxy run {spec.proxy_run_id} recorded; "
                f"boundary_verdict={verdict.value}; promotion_ready=false"
            ),
        )
        proxy_result = ProxyRunResult.from_spec(
            spec,
            status=ProxyRunStatus.COMPLETED,
            boundary_verdict=verdict,
            registry_note_event_id=note.event_id,
        )
        boundary.validate_result(proxy_result)
        return SyntheticProxyRunOutput(
            proxy_result=proxy_result,
            positions=ledger_output.positions,
            ledger=ledger_output.ledger,
            result=result_summary,
        )


def _build_result_summary(
    *,
    manifest_uri: str,
    boundary_verdict: ProxyBoundaryVerdict | str,
    ledger: pd.DataFrame,
) -> dict[str, Any]:
    date_values = ledger["date"].tolist()
    return {
        "manifest_uri": manifest_uri,
        "row_count": int(len(ledger)),
        "date_range": {
            "start": str(date_values[0]) if date_values else None,
            "end": str(date_values[-1]) if date_values else None,
        },
        "cash": _series_records(ledger, "cash"),
        "turnover": _series_records(ledger, "turnover"),
        "transaction_cost": _series_records(ledger, "transaction_cost"),
        "gross_exposure": _series_records(ledger, "gross_exposure"),
        "net_exposure": _series_records(ledger, "net_exposure"),
        "boundary_verdict": _verdict_value(boundary_verdict),
        "promotion_ready": False,
        "canonical_engine_required": True,
    }


def _validate_result_summary(summary: dict[str, Any]) -> None:
    row_count = pd.DataFrame({"row_count": [summary.get("row_count")]})
    validate_positive_numeric(row_count, ("row_count",), "synthetic output result")
    for key in ("cash", "turnover", "transaction_cost", "gross_exposure", "net_exposure"):
        records = pd.DataFrame(summary.get(key, []))
        validate_required_columns(records, ("date", "value"), f"synthetic output result.{key}")
        validate_no_nulls(records, ("date", "value"), f"synthetic output result.{key}")
        validate_finite_numeric(records, ("value",), f"synthetic output result.{key}")


def _series_records(ledger: pd.DataFrame, column: str) -> list[dict[str, object]]:
    return [
        {"date": str(row.date), "value": float(getattr(row, column))}
        for row in ledger[["date", column]].itertuples(index=False)
    ]


def _verdict_value(value: ProxyBoundaryVerdict | str) -> str:
    return value.value if isinstance(value, ProxyBoundaryVerdict) else str(value)
