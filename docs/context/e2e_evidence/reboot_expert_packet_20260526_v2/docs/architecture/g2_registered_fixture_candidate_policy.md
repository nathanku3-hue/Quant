# G2 Registered Fixture Candidate Policy

Status: Active for Phase 65 G2
Date: 2026-05-09
Scope: one synthetic registered fixture candidate lineage proof

## Purpose

G2 proves one boring end-to-end lineage path:

```text
Candidate Registry
-> manifest-backed synthetic fixture
-> deterministic V2 proxy run
-> append-only registry note
-> proxy result quarantined from promotion
-> rebuildable audit evidence
```

It does not create an investable result, strategy search, ranking surface, alert, broker action, or promotion packet.

## Allowed Flow

1. Load the existing Candidate Registry.
2. Register or load exactly one synthetic fixture candidate.
3. Require `manifest_uri`, `source_quality`, `trial_count`, `code_ref`, and `data_snapshot`.
4. Run the deterministic proxy using only the G1 synthetic fixture under `data/fixtures/v2_proxy/`.
5. Append a registry note event with marker `candidate.proxy_run_recorded`.
6. Validate the note event exists, is hash-linked, and belongs to the same candidate.
7. Emit a proxy result with `promotion_ready = false`.
8. Emit a lineage report.
9. Rebuild the snapshot projection from events.
10. Prove no promotion packet, alert, or broker action can be emitted by this path.

## Hard Boundary

Blocked in G2:

- real market data;
- strategy search;
- PEAD variants;
- candidate ranking;
- edge or performance metric claims;
- alerts;
- broker or Alpaca calls;
- promotion packets;
- new registry event types.

The append-only event log remains the source of truth. Snapshot and report artifacts are rebuildable projections.

## Required Lineage Fields

```text
candidate_id
family_id
candidate_event_id
proxy_run_id
registry_note_event_id
registry_note_event_hash
manifest_uri
manifest_sha256
fixture_sha256
source_quality
data_snapshot
code_ref
engine_name = "v2_proxy"
engine_version
promotion_ready = false
canonical_engine_required = true
boundary_verdict = "blocked_from_promotion"
```

## Implementation Paths

```text
v2_discovery/fast_sim/run_candidate_proxy.py
v2_discovery/fast_sim/lineage.py
tests/test_v2_proxy_registered_candidate_flow.py
data/registry/g2_single_fixture_candidate_report.json
data/registry/g2_single_fixture_candidate_report.json.manifest.json
```

## Verification

Required focused tests:

```text
tests/test_v2_proxy_registered_candidate_flow.py
tests/test_v2_fast_proxy_synthetic.py
tests/test_v2_fast_proxy_invariants.py
tests/test_v2_proxy_boundary.py
tests/test_candidate_registry.py
```

G2 can pass only when proxy output remains quarantined:

```text
promotion_ready = false
canonical_engine_required = true
boundary_verdict = "blocked_from_promotion"
```
