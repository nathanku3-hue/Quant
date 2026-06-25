# G3 Canonical Replay Fixture Policy

Status: Active for Phase 65 G3
Date: 2026-05-09
Scope: one registered fixture candidate replayed through the V1 canonical path and compared with V2 proxy output

## Purpose

G3 proves one controlled truth-alignment path:

```text
registered G2 fixture candidate
-> deterministic fixture manifest
-> V1 canonical replay call to core.engine.run_simulation
-> V2 proxy mechanical output
-> allowed accounting comparison
-> V2 remains blocked from promotion
```

This is inventory and replay governance, not strategy research. The model-risk framing is consistent with SR 26-2, which the Federal Reserve published on April 17, 2026 as revised model-risk guidance superseding SR 11-7 and emphasizing risk-based model inventory, documentation, and validation: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm.

## Allowed Flow

1. Load the existing Candidate Registry.
2. Require exactly one registered fixture candidate in the G2 fixture family.
3. Require the candidate manifest, source-quality field, data snapshot, and manifest hash.
4. Reject Tier 2 or non-fixture market-data manifests.
5. Run the deterministic fixture through `core.engine.run_simulation`.
6. Build V1 mechanical replay output from the same bounded fixture.
7. Build V2 proxy mechanical output from the quarantined proxy path.
8. Compare only the allowed mechanical fields.
9. Emit an optional replay report and report manifest.
10. Keep `promotion_ready = false`, `canonical_engine_required = true`, and `boundary_verdict = "v2_blocked_from_promotion"`.

## Allowed Comparison Fields

```text
positions
cash
turnover
transaction_cost
gross_exposure
net_exposure
row_count
date_range
manifest_uri
source_quality
candidate_id
```

## Blocked Scope

Blocked in G3:

- strategy search;
- real market data expansion;
- candidate ranking;
- edge or performance metrics;
- alerts;
- broker, Alpaca, OpenClaw, or notifier paths;
- external engines;
- promotion packets;
- any path where a V2 result can become `promotion_ready = true`;
- any interpretation of a V1 match as trading permission.

## Required Report Fields

```text
candidate_id
family_id
candidate_event_id
proxy_run_id
registry_note_event_id
v1_replay_id
v1_engine_name
v1_engine_version
v2_engine_name
v2_engine_version
manifest_uri
manifest_sha256
source_quality
data_snapshot
code_ref
comparison_fields
comparison_result
mismatch_count
promotion_ready = false
canonical_engine_required = true
boundary_verdict = "v2_blocked_from_promotion"
```

## Implementation Paths

```text
v2_discovery/replay/__init__.py
v2_discovery/replay/canonical_replay.py
v2_discovery/replay/comparison.py
v2_discovery/replay/schemas.py
tests/test_v2_canonical_replay_fixture.py
data/registry/g3_canonical_replay_report.json
data/registry/g3_canonical_replay_report.json.manifest.json
```

## Verification

Required focused tests:

```text
tests/test_v2_canonical_replay_fixture.py
tests/test_v2_proxy_registered_candidate_flow.py
tests/test_v2_fast_proxy_synthetic.py
tests/test_v2_fast_proxy_invariants.py
tests/test_v2_proxy_boundary.py
tests/test_candidate_registry.py
```

G3 can pass only when the report states:

```text
comparison_result = "match"
mismatch_count = 0
promotion_ready = false
canonical_engine_required = true
boundary_verdict = "v2_blocked_from_promotion"
```
