# V2 Proxy Boundary Policy

Status: Active for Phase 65 / Phase G0
Date: 2026-05-09
Scope: Boundary harness only

## Boundary

Phase G0 creates an airlock for future fast simulations. It does not create a useful simulator, strategy factory, parameter sweep, candidate ranking, alert packet, promotion packet, broker path, provider integration, or external engine adapter.

V1 canonical truth remains:

```text
core.engine.run_simulation
```

Any future V2 proxy result is advisory containment evidence only. It is not official research truth and cannot become promotion authority without a future V1 canonical rerun.

Allowed:
- proxy run schema;
- proxy result schema;
- boundary verdict schema;
- no-op proxy runner;
- registry note append for boundary audit;
- tests proving proxy results remain blocked from promotion.

Blocked:
- strategy factory;
- PEAD variant search;
- parameter sweeps;
- ranking candidates;
- promotion packets;
- alerts;
- broker calls;
- new external engines;
- MLflow, DVC, vectorbt, Qlib, LEAN, or Nautilus integration.

## Required Proxy Fields

Every proxy run/result must carry:

- `proxy_run_id`
- `candidate_id`
- `registry_event_id`
- `manifest_uri`
- `source_quality`
- `data_snapshot`
- `code_ref`
- `engine_name = "v2_proxy"`
- `engine_version`
- `cost_model`
- `train_window`
- `test_window`
- `created_at`
- `promotion_ready = false`
- `canonical_engine_required = true`

## Hard Invariants

1. Every V2 proxy result has `promotion_ready = false`.
2. Every V2 proxy result references a registered candidate.
3. Every V2 proxy result references an existing manifest.
4. Every V2 proxy result carries `source_quality`.
5. Tier 2 / non-canonical data cannot produce a promotion draft.
6. Proxy results cannot emit alerts.
7. Proxy results cannot call BrokerPort or broker APIs.
8. Proxy results cannot modify candidate history except by appending registry notes/events; proxy result `registry_note_event_id` must resolve to a real `candidate.note_added` event for the same candidate, proxy run, and boundary verdict.
9. Promotion requires a future V1 canonical rerun.
10. `core.engine.run_simulation` remains the only official truth path.

## No-Op Demo

The only Phase G0 demo is:

```text
registered dummy candidate
-> noop proxy run
-> proxy result emitted
-> promotion_ready = false
-> canonical_engine_required = true
-> boundary verdict = blocked_from_promotion
-> registry note event resolves back to the proxy run
-> registry hash-chain still passes
```

The no-op proxy computes no alpha, no Sharpe, no return curve, no ranking, and no best candidate.

## Promotion Boundary

`PromotionPacketDraft` exists only to encode the future requirement that promotion needs V1 canonical evidence. It requires:

```text
canonical_engine_name = "core.engine.run_simulation"
canonical_result_ref != ""
source_quality = "canonical"
promotion_ready = false
canonical_engine_required = true
```

A V2 proxy result without a future V1 canonical result reference is blocked with:

```text
Promotion requires a future V1 canonical rerun
```

Non-canonical proxy results are blocked from draft creation even if a future reference is supplied.

## Implementation Paths

- `v2_discovery/fast_sim/schemas.py`
- `v2_discovery/fast_sim/boundary.py`
- `v2_discovery/fast_sim/noop_proxy.py`
- `tests/test_v2_proxy_boundary.py`

The boundary deliberately avoids imports from `core.engine`, `execution.broker_api`, provider adapters, or external simulation/tracking packages.

## Audit Note Proof

`V2ProxyBoundary.validate_result()` must validate the registry note proof for every proxy result. A result is invalid unless `registry_note_event_id` exists in the Candidate Registry event log, belongs to the same `candidate_id`, has `event_type = "candidate.note_added"`, and its note text references both the `proxy_run_id` and `boundary_verdict`.

## Phase G1 Synthetic Fast-Proxy Mechanics

Status: Active for Phase G1 only.

G1 adds one deterministic synthetic simulator to prove mechanical replayability and accounting. It still does not create a useful strategy engine. The simulator accepts only manifest-backed fixture files under:

```text
data/fixtures/v2_proxy/
```

Allowed input:
- `synthetic_prices.csv`
- `synthetic_weights.csv`
- `synthetic_manifest.json`

The weights file must be prebaked target weights with strict columns:

```text
date,symbol,target_weight
```

The simulator rejects signal functions, strategy logic, real market-data providers, non-fixture data paths, missing fixture hashes, and tampered fixture files before simulation.

Allowed output:
- positions;
- cash;
- turnover;
- transaction_cost;
- gross_exposure;
- net_exposure;
- row_count;
- date_range;
- boundary_verdict;
- `promotion_ready = false`;
- `canonical_engine_required = true`.

Blocked output:
- Sharpe;
- alpha;
- CAGR;
- max drawdown;
- rank;
- score;
- buy/sell alert;
- promotion packet.

G1 implementation paths:

```text
v2_discovery/fast_sim/cost_model.py
v2_discovery/fast_sim/fixtures.py
v2_discovery/fast_sim/ledger.py
v2_discovery/fast_sim/simulator.py
tests/test_v2_fast_proxy_synthetic.py
tests/test_v2_fast_proxy_invariants.py
data/fixtures/v2_proxy/*
```

G1 keeps the G0 result boundary intact: every simulator run still passes through `V2ProxyBoundary`, appends only a registry note, and validates that note against the append-only registry event log.
