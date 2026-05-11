from __future__ import annotations

import json
from pathlib import Path

from data.provenance import SOURCE_QUALITY_CANONICAL
from data.provenance import load_manifest
from data.provenance import utc_now_iso
from v2_discovery.fast_sim.schemas import PromotionPacketDraft
from v2_discovery.fast_sim.schemas import ProxyBoundaryError
from v2_discovery.fast_sim.schemas import ProxyBoundaryVerdict
from v2_discovery.fast_sim.schemas import ProxyRunResult
from v2_discovery.fast_sim.schemas import ProxyRunSpec
from v2_discovery.schemas import CandidateEvent
from v2_discovery.registry import CandidateRegistry


class V2ProxyBoundary:
    """Airlock between future fast proxy runs and canonical V1 truth."""

    def __init__(self, registry: CandidateRegistry) -> None:
        self.registry = registry

    def validate_run_spec(self, spec: ProxyRunSpec) -> None:
        snapshot = self.registry.rebuild_snapshot()
        if spec.candidate_id not in snapshot:
            raise ProxyBoundaryError("V2 proxy result requires a registered candidate")

        candidate = snapshot[spec.candidate_id].spec
        if candidate.manifest_uri != spec.manifest_uri:
            raise ProxyBoundaryError("Proxy manifest_uri must match registered candidate manifest")
        if candidate.source_quality != spec.source_quality:
            raise ProxyBoundaryError("Proxy source_quality must match registered candidate source_quality")

        event = self._find_registry_event(spec.registry_event_id)
        if event.candidate_id != spec.candidate_id:
            raise ProxyBoundaryError("registry_event_id must reference the candidate_id")

        manifest_path = self._resolve_path(spec.manifest_uri)
        if not manifest_path.exists():
            raise ProxyBoundaryError(f"manifest_uri does not exist: {spec.manifest_uri}")
        manifest = load_manifest(manifest_path)
        if manifest.get("source_quality") != spec.source_quality:
            raise ProxyBoundaryError("Proxy source_quality must match manifest source_quality")

    def verdict_for(self, spec: ProxyRunSpec) -> ProxyBoundaryVerdict:
        self.validate_run_spec(spec)
        if spec.source_quality != SOURCE_QUALITY_CANONICAL:
            return ProxyBoundaryVerdict.TIER2_BLOCKED
        return ProxyBoundaryVerdict.BLOCKED_FROM_PROMOTION

    def validate_result(self, result: ProxyRunResult) -> ProxyBoundaryVerdict:
        spec = ProxyRunSpec(
            proxy_run_id=result.proxy_run_id,
            candidate_id=result.candidate_id,
            registry_event_id=result.registry_event_id,
            manifest_uri=result.manifest_uri,
            source_quality=result.source_quality,
            data_snapshot=result.data_snapshot,
            code_ref=result.code_ref,
            engine_name=result.engine_name,
            engine_version=result.engine_version,
            cost_model=result.cost_model,
            train_window=result.train_window,
            test_window=result.test_window,
            created_at=result.created_at,
            promotion_ready=result.promotion_ready,
            canonical_engine_required=result.canonical_engine_required,
            status=result.status,
        )
        expected = self.verdict_for(spec)
        if result.boundary_verdict != expected:
            raise ProxyBoundaryError("Proxy result boundary_verdict does not match policy")
        if result.promotion_ready:
            raise ProxyBoundaryError("V2 proxy result cannot be promotion_ready")
        if not result.canonical_engine_required:
            raise ProxyBoundaryError("V2 proxy result must require canonical V1 rerun")
        self._validate_registry_note_event(result)
        return expected

    def build_promotion_packet_draft_from_proxy(
        self,
        result: ProxyRunResult,
        *,
        canonical_result_ref: str | None = None,
    ) -> PromotionPacketDraft:
        self.validate_result(result)
        if not canonical_result_ref:
            raise ProxyBoundaryError("Promotion requires a future V1 canonical rerun")
        return PromotionPacketDraft(
            candidate_id=result.candidate_id,
            source_quality=result.source_quality,
            manifest_uri=result.manifest_uri,
            canonical_engine_name="core.engine.run_simulation",
            canonical_result_ref=canonical_result_ref,
            created_at=utc_now_iso(),
        )

    def _find_registry_event(self, event_id: str, *, field: str = "registry_event_id") -> CandidateEvent:
        for event in self._load_events():
            if event.event_id == event_id:
                return event
        raise ProxyBoundaryError(f"{field} does not exist: {event_id}")

    def _validate_registry_note_event(self, result: ProxyRunResult) -> None:
        event = self._find_registry_event(
            result.registry_note_event_id,
            field="registry_note_event_id",
        )
        if event.candidate_id != result.candidate_id:
            raise ProxyBoundaryError("registry_note_event_id must reference the candidate_id")
        if event.event_type != "candidate.note_added":
            raise ProxyBoundaryError("registry_note_event_id must reference a candidate note")
        note = str(event.payload.get("note", ""))
        if result.proxy_run_id not in note:
            raise ProxyBoundaryError("registry note must reference the proxy_run_id")
        if result.boundary_verdict.value not in note:
            raise ProxyBoundaryError("registry note must reference the boundary_verdict")

    def _load_events(self) -> tuple[CandidateEvent, ...]:
        events = []
        with self.registry.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                clean = line.strip()
                if not clean:
                    continue
                try:
                    events.append(CandidateEvent.from_dict(json.loads(clean)))
                except (TypeError, json.JSONDecodeError) as exc:
                    raise ProxyBoundaryError(
                        f"Invalid registry event at line {line_number}: {exc}"
                    ) from exc
        return tuple(events)

    def _resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.registry.repo_root / path
