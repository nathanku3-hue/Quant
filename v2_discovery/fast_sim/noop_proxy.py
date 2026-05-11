from __future__ import annotations

from v2_discovery.fast_sim.boundary import V2ProxyBoundary
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.fast_sim.schemas import ProxyRunStatus
from v2_discovery.registry import CandidateRegistry


NOOP_PROXY_ENGINE_VERSION = "0.0.1"


class NoopProxy:
    """Boundary-only proxy runner that intentionally computes no alpha."""

    engine_version = NOOP_PROXY_ENGINE_VERSION

    def run(
        self,
        spec: ProxyRunSpec,
        *,
        registry: CandidateRegistry,
        actor: str = "v2_noop_proxy",
    ) -> ProxyRunResult:
        boundary = V2ProxyBoundary(registry)
        verdict = boundary.verdict_for(spec)
        note = registry.add_note(
            spec.candidate_id,
            actor=actor,
            note=(
                f"noop proxy run {spec.proxy_run_id} recorded; "
                f"boundary_verdict={verdict.value}; promotion_ready=false"
            ),
        )
        result = ProxyRunResult.from_spec(
            spec,
            status=ProxyRunStatus.COMPLETED,
            boundary_verdict=verdict,
            registry_note_event_id=note.event_id,
        )
        boundary.validate_result(result)
        return result
