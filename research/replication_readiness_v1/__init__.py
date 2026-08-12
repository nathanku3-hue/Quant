"""Quarantined independent-replication readiness contracts.

The package contains no outcome reader and no provider connector.  It records
lead-time feasibility only: entitlement, source, permanent identity, PIT/vintage,
license/retention, latency, and immutable quarantine storage.
"""

from research.replication_readiness_v1.contracts import (
    REPLICATION_OUTCOME_ACCESS_DENIED,
    REPLICATION_READINESS_SCHEMA,
    REPLICATION_RESEARCH_VISIBILITY,
    ReplicationReadinessError,
    ReplicationReadinessManifestV1,
    write_manifest_once,
)

__all__ = [
    "REPLICATION_OUTCOME_ACCESS_DENIED",
    "REPLICATION_READINESS_SCHEMA",
    "REPLICATION_RESEARCH_VISIBILITY",
    "ReplicationReadinessError",
    "ReplicationReadinessManifestV1",
    "write_manifest_once",
]
