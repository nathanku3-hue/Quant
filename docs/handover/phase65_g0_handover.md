# Phase 65 G0 Handover

Date: 2026-05-09
Status: COMPLETE - V2 PROXY BOUNDARY ONLY
Audience: PM

## Executive Summary (PM-friendly)

Phase G0 is complete as a V2 proxy airlock. The repo now has a safe container for future fast simulations, but it still does not have a useful proxy simulator, strategy factory, parameter sweep, ranking system, alert packet, promotion packet, broker call, or external engine integration.

The boundary proves the key thing: a V2 proxy result cannot become official truth. Every proxy output is `promotion_ready = false`, requires a future canonical V1 rerun, carries a real registry note proof, and is blocked from promotion unless future evidence comes from `core.engine.run_simulation`.

## Delivered Scope vs Deferred Scope

Delivered:
- `ProxyRunSpec`
- `ProxyRunResult`
- `PromotionPacketDraft`
- `ProxyBoundaryVerdict`
- `ProxyRunStatus`
- `V2ProxyBoundary`
- no-op proxy runner
- tests proving registered candidate, manifest, source-quality, Tier 2 block, no alert/broker calls, V1 rerun requirement, code/data lineage, real registry note proof, and no-op round trip.

Deferred:
- real fast simulator;
- strategy generation;
- PEAD variant search;
- parameter sweeps;
- ranking candidates;
- promotion packets;
- alerts;
- broker calls;
- MLflow/DVC/vectorbt/Qlib/LEAN/Nautilus adapters.

## Derivation and Formula Register

See `docs/notes.md` for formula details.

Core predicates:
- `proxy_truth_official = false`
- `proxy_result_promotion_ready = false`
- `canonical_engine_required = true`
- `registry_note_event_valid = true` only when the note event exists for the same candidate, proxy run, and boundary verdict.
- `promotion_packet_draft_valid = 1` only when `canonical_engine_name = "core.engine.run_simulation"` and a future canonical result reference exists.

## Logic Chain

Input -> Transform -> Decision -> Output

Registered candidate + registry event + manifest -> no-op proxy boundary validation -> registry note append only -> proxy result note proof validated -> proxy result blocked from promotion and requiring V1 canonical rerun.

## Evidence Matrix

| Command / Artifact | Result |
|---|---|
| `.venv\Scripts\python -m pytest tests/test_v2_proxy_boundary.py -q` | PASS, `11 passed` |
| `.venv\Scripts\python -m compileall v2_discovery\fast_sim tests\test_v2_proxy_boundary.py` | PASS |
| `docs/architecture/v2_proxy_boundary_policy.md` | Policy published |
| `v2_discovery/fast_sim/` | Boundary-only harness present |

## Open Risks / Assumptions / Rollback

Open risks:
- yfinance legacy migration remains future debt.
- S&P sidecar freshness remains stale through `2023-11-27`.
- Future G1 work must stay inert/deterministic unless explicitly widened.

Assumptions:
- Phase G0 is boundary-only and does not generate research evidence.
- The no-op proxy is the only allowed demo.

Rollback:
- Revert only Phase G0 fast-sim boundary files, tests, policy/brief/context docs, and SAW report if this airlock is rejected. Do not revert Phase F Candidate Registry, D-353 provenance gates, or R64.1 dependency hygiene.

## Next Phase Roadmap

- Option A: approve Phase G1 minimal fast proxy simulator with one inert/deterministic fixture and no strategy family.
- Option B: hold for advanced registry accounting for trial families and multiple-testing metadata.
- Later only after explicit approval: real strategy families, useful fast simulation, alerts, promotion packets, and external engine integrations.

## New Context Packet

## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Closed Phase F Candidate Registry as registry-only work.
- Closed Phase G0 V2 Proxy Boundary Harness as boundary-only work with a no-op proxy, registry note proof validation, and a promotion-blocking airlock.

## What Is Locked
- No live trading, no broker automation, no paper alerts, no strategy factory, no V2 fast simulator, and no promotion packets.
- Candidate Registry is append-only and requires candidate metadata, `trial_count`, and a manifest pointer before results.
- V2 proxy outputs are not official truth; future promotion requires `core.engine.run_simulation`, and proxy result note IDs must resolve to real registry note events.
- yfinance remains non-canonical and quarantined.

## What Remains
- Decide whether to allow Phase G1 inert/deterministic proxy fixture or hold for advanced registry accounting.
- Do not start strategy search until explicitly approved.

## Next-phase Roadmap
- Phase G1 option: inert/deterministic fixture only, no strategy family.
- Alternative: advanced registry accounting, no simulation engine.
- Later only after approval: strategy search, useful V2 fast simulation, alert packets, promotion packets.

## Immediate First Step
```text
.venv\Scripts\python -m pytest tests/test_v2_proxy_boundary.py tests/test_candidate_registry.py tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py -q
```

ConfirmationRequired: YES
Prompt: Reply "approve next phase" to start execution.
NextPhaseApproval: PENDING
