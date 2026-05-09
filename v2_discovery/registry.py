from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Iterable, Mapping

from data.provenance import load_manifest
from data.provenance import utc_now_iso
from data.provenance import write_json_atomic
from v2_discovery.schemas import ALLOWED_STATUS_TRANSITIONS
from v2_discovery.schemas import CandidateEvent
from v2_discovery.schemas import CandidateRegistryError
from v2_discovery.schemas import CandidateSnapshot
from v2_discovery.schemas import CandidateSpec
from v2_discovery.schemas import CandidateStatus
from v2_discovery.schemas import FORBIDDEN_PHASE_F_STATUSES
from v2_discovery.schemas import GENESIS_EVENT_HASH


DEFAULT_EVENT_LOG_PATH = Path("data/registry/candidate_events.jsonl")
DEFAULT_SNAPSHOT_PATH = Path("data/registry/candidate_snapshot.json")
DEFAULT_REBUILD_REPORT_PATH = Path("data/registry/candidate_registry_rebuild_report.json")


class CandidateRegistry:
    def __init__(
        self,
        event_log_path: str | Path = DEFAULT_EVENT_LOG_PATH,
        *,
        snapshot_path: str | Path = DEFAULT_SNAPSHOT_PATH,
        repo_root: str | Path | None = None,
    ) -> None:
        self.repo_root = Path(repo_root) if repo_root is not None else Path.cwd()
        self.event_log_path = self._resolve_path(event_log_path)
        self.snapshot_path = self._resolve_path(snapshot_path)
        self.event_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)

    def register_candidate(self, spec: CandidateSpec, *, actor: str) -> CandidateEvent:
        if spec.status != CandidateStatus.GENERATED:
            raise CandidateRegistryError("new candidates must start with status=generated")
        self._validate_manifest_pointer(spec)
        if spec.candidate_id in self.rebuild_snapshot():
            raise CandidateRegistryError(f"Duplicate candidate_id: {spec.candidate_id}")
        return self._append_event(
            spec.candidate_id,
            "candidate.generated",
            actor=actor,
            payload={"spec": spec.to_dict()},
        )

    def change_status(
        self,
        candidate_id: str,
        to_status: CandidateStatus | str,
        *,
        actor: str,
        reason: str | None = None,
    ) -> CandidateEvent:
        snapshot = self.rebuild_snapshot()
        if candidate_id not in snapshot:
            raise CandidateRegistryError(f"Unknown candidate_id: {candidate_id}")
        destination = CandidateStatus(str(to_status))
        if destination in FORBIDDEN_PHASE_F_STATUSES:
            raise CandidateRegistryError(f"status {destination.value!r} is forbidden in Phase F")
        current = snapshot[candidate_id].status
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, frozenset())
        if destination not in allowed:
            raise CandidateRegistryError(
                f"Invalid status transition: {current.value} -> {destination.value}"
            )
        event_type = "candidate.status_changed"
        if destination == CandidateStatus.REJECTED:
            event_type = "candidate.rejected"
        elif destination == CandidateStatus.RETIRED:
            event_type = "candidate.retired"
        return self._append_event(
            candidate_id,
            event_type,
            actor=actor,
            payload={
                "from_status": current.value,
                "to_status": destination.value,
                "reason": reason or "",
            },
        )

    def reject_candidate(self, candidate_id: str, *, actor: str, reason: str) -> CandidateEvent:
        return self.change_status(
            candidate_id,
            CandidateStatus.REJECTED,
            actor=actor,
            reason=reason,
        )

    def retire_candidate(self, candidate_id: str, *, actor: str, reason: str) -> CandidateEvent:
        return self.change_status(
            candidate_id,
            CandidateStatus.RETIRED,
            actor=actor,
            reason=reason,
        )

    def add_note(self, candidate_id: str, *, actor: str, note: str) -> CandidateEvent:
        snapshot = self.rebuild_snapshot()
        if candidate_id not in snapshot:
            raise CandidateRegistryError(f"Unknown candidate_id: {candidate_id}")
        return self._append_event(
            candidate_id,
            "candidate.note_added",
            actor=actor,
            payload={"note": note, "status": snapshot[candidate_id].status.value},
        )

    def rebuild_snapshot(self) -> dict[str, CandidateSnapshot]:
        states: dict[str, dict[str, Any]] = {}
        for event in self._load_events():
            if event.event_type == "candidate.generated":
                spec = CandidateSpec.from_dict(event.payload["spec"])
                if spec.candidate_id in states:
                    raise CandidateRegistryError(f"Duplicate candidate_id: {spec.candidate_id}")
                states[spec.candidate_id] = {
                    "spec": spec,
                    "status": spec.status,
                    "event_count": 1,
                    "last_event_hash": event.event_hash,
                    "notes": [],
                }
                continue

            if event.candidate_id not in states:
                raise CandidateRegistryError(
                    f"Event references unknown candidate_id: {event.candidate_id}"
                )
            state = states[event.candidate_id]
            state["event_count"] += 1
            state["last_event_hash"] = event.event_hash
            if event.event_type in {
                "candidate.status_changed",
                "candidate.retired",
                "candidate.rejected",
            }:
                state["status"] = CandidateStatus(event.payload["to_status"])
            elif event.event_type == "candidate.note_added":
                state["notes"].append(
                    {
                        "created_at": event.created_at,
                        "actor": event.actor,
                        "note": event.payload["note"],
                    }
                )
            else:
                raise CandidateRegistryError(f"Unknown event_type: {event.event_type}")

        return {
            candidate_id: CandidateSnapshot(
                candidate_id=candidate_id,
                spec=state["spec"],
                status=state["status"],
                event_count=state["event_count"],
                last_event_hash=state["last_event_hash"],
                notes=tuple(state["notes"]),
            )
            for candidate_id, state in sorted(states.items())
        }

    def write_snapshot(self) -> Path:
        payload = {
            "schema_version": "1.0.0",
            "generated_at": utc_now_iso(),
            "source_event_log": self._relative_or_absolute(self.event_log_path),
            "candidates": {
                candidate_id: snapshot.to_dict()
                for candidate_id, snapshot in self.rebuild_snapshot().items()
            },
        }
        write_json_atomic(payload, self.snapshot_path)
        return self.snapshot_path

    def write_rebuild_report(
        self,
        path: str | Path = DEFAULT_REBUILD_REPORT_PATH,
        *,
        demo_candidate_id: str | None = None,
    ) -> Path:
        target = self._resolve_path(path)
        snapshot = self.rebuild_snapshot()
        chain = self.verify_hash_chain()
        forbidden_paths_present = any(
            getattr(self, name, None) is not None
            for name in ("promote_candidate", "emit_alert", "execute_candidate")
        )
        payload = {
            "schema_version": "1.0.0",
            "generated_at": utc_now_iso(),
            "event_log": self._relative_or_absolute(self.event_log_path),
            "snapshot": self._relative_or_absolute(self.snapshot_path),
            "hash_chain_valid": chain["valid"],
            "hash_chain": chain,
            "candidate_count": len(snapshot),
            "event_count": chain["event_count"],
            "demo_candidate_id": demo_candidate_id,
            "demo_status": snapshot[demo_candidate_id].status.value
            if demo_candidate_id and demo_candidate_id in snapshot
            else None,
            "forbidden_paths_present": forbidden_paths_present,
            "manifest_pointers": {
                candidate_id: item.spec.manifest_uri for candidate_id, item in snapshot.items()
            },
            "manifest_exists": {
                candidate_id: self._resolve_path(item.spec.manifest_uri).exists()
                for candidate_id, item in snapshot.items()
            },
        }
        write_json_atomic(payload, target)
        return target

    def verify_hash_chain(self) -> dict[str, Any]:
        previous = GENESIS_EVENT_HASH
        event_count = 0
        last_hash = previous
        try:
            for event in self._load_events():
                event_count += 1
                if event.previous_event_hash != previous:
                    return {
                        "valid": False,
                        "event_count": event_count,
                        "last_event_hash": last_hash,
                        "error": "previous_event_hash_mismatch",
                    }
                recomputed = event.recompute_hash()
                if event.event_hash != recomputed:
                    return {
                        "valid": False,
                        "event_count": event_count,
                        "last_event_hash": last_hash,
                        "error": "event_hash_mismatch",
                    }
                previous = event.event_hash
                last_hash = event.event_hash
        except (CandidateRegistryError, KeyError, json.JSONDecodeError) as exc:
            return {
                "valid": False,
                "event_count": event_count,
                "last_event_hash": last_hash,
                "error": str(exc),
            }
        return {
            "valid": True,
            "event_count": event_count,
            "last_event_hash": last_hash,
            "error": None,
        }

    def _append_event(
        self,
        candidate_id: str,
        event_type: str,
        *,
        actor: str,
        payload: Mapping[str, Any],
    ) -> CandidateEvent:
        previous_hash = self._last_event_hash()
        event = CandidateEvent.create(
            event_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            event_type=event_type,
            actor=actor,
            payload=payload,
            previous_event_hash=previous_hash,
        )
        with self.event_log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")))
            handle.write("\n")
        return event

    def _load_events(self) -> Iterable[CandidateEvent]:
        if not self.event_log_path.exists():
            return []
        events = []
        with self.event_log_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                clean = line.strip()
                if not clean:
                    continue
                try:
                    events.append(CandidateEvent.from_dict(json.loads(clean)))
                except (TypeError, CandidateRegistryError) as exc:
                    raise CandidateRegistryError(
                        f"Invalid candidate event at line {line_number}: {exc}"
                    ) from exc
        return events

    def _last_event_hash(self) -> str:
        events = list(self._load_events())
        if not events:
            return GENESIS_EVENT_HASH
        return events[-1].event_hash

    def _validate_manifest_pointer(self, spec: CandidateSpec) -> None:
        manifest_path = self._resolve_path(spec.manifest_uri)
        if not manifest_path.exists():
            raise CandidateRegistryError(f"manifest_uri does not exist: {spec.manifest_uri}")
        manifest = load_manifest(manifest_path)
        if manifest.get("source_quality") != spec.source_quality:
            raise CandidateRegistryError(
                "candidate source_quality must match manifest source_quality"
            )

    def _resolve_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.repo_root / path

    def _relative_or_absolute(self, value: Path) -> str:
        try:
            return value.relative_to(self.repo_root).as_posix()
        except ValueError:
            return str(value)
