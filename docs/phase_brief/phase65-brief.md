# Phase 65 Brief

Status: CLOSED - REGISTRY ONLY
Authority: D-355 Phase 65 Candidate Registry closeout
Date: 2026-05-09
Owner: PM / Architecture Office

## Goal

Implement Phase F Candidate Registry as a narrow append-only metadata and lifecycle ledger before any strategy search, alert packet, paper portfolio loop, or promotion packet work.

## Boundary

Approved:
- registry-only implementation;
- append-only candidate state transitions;
- candidate metadata before results;
- required `trial_count`;
- required manifest pointer;
- lifecycle proof with a dummy candidate.

Blocked:
- strategy factory;
- V2 fast simulator;
- promotion packets;
- paper alerts;
- paper portfolio loop;
- live Alpaca orders;
- broker automation;
- yfinance canonical promotion.

## Acceptance Checks

- [x] CHK-P65-01: Candidate registry persists candidate metadata before any result payload.
- [x] CHK-P65-02: Candidate state transitions are append-only and preserve prior state history.
- [x] CHK-P65-03: `trial_count` is required and non-negative.
- [x] CHK-P65-04: Manifest pointer is required and must reference an existing manifest.
- [x] CHK-P65-05: Dummy candidate lifecycle passes: `generated -> incubating -> rejected`.
- [x] CHK-P65-06: Prior candidate state cannot be mutated in place.
- [x] CHK-P65-07: No strategy generation, promotion packet, alert emission, or live/broker path is introduced.

## Delivered Artifacts

- `docs/architecture/candidate_registry_policy.md`
- `v2_discovery/schemas.py`
- `v2_discovery/registry.py`
- `scripts/run_candidate_registry_demo.py`
- `tests/test_candidate_registry.py`
- `data/registry/candidate_events.jsonl`
- `data/registry/candidate_snapshot.json`
- `data/registry/candidate_registry_rebuild_report.json`

## Executable Invariants

- candidate specs are frozen dataclasses;
- every candidate requires `manifest_uri`, `source_quality`, `trial_count`, and `parameters_searched`;
- `manifest_uri` must exist and the manifest `source_quality` must match the candidate;
- events are chained by `previous_event_hash` and `event_hash`;
- projections rebuild from JSONL and do not rewrite the event log;
- duplicate candidate IDs are rejected;
- `promoted`, `alerted`, and `executed` statuses are forbidden in Phase F;
- non-canonical candidates are never promotion-ready.

## First Test

```text
dummy candidate -> generated -> incubating -> rejected -> audit log preserved -> manifest pointer required -> cannot mutate prior state
```

Result:

```text
PH65_PEAD_DUMMY_001 -> generated -> incubating -> rejected
hash_chain_valid = true
manifest_exists = true
forbidden_paths_present = false
```

## Preconditions Satisfied By R64.1

- `pip check` passes.
- Main Alpaca dependency is `alpaca-py==0.43.4`.
- Legacy `alpaca-trade-api` is excluded from the main dependency set.
- yfinance quarantine tests pass.
- Data readiness and minimal validation lab pass.
- R64.1 surgical commits separate milestone files from unrelated dirty files.

## Verification Evidence

- `.venv\Scripts\python -m pytest tests/test_candidate_registry.py -q` -> PASS (`12 passed`).
- `.venv\Scripts\python scripts\run_candidate_registry_demo.py` -> PASS (`event_count = 3`, `demo_status = rejected`, `hash_chain_valid = true`).
- `.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py tests/test_data_readiness_audit.py tests/test_minimal_validation_lab.py tests/test_candidate_registry.py -q` -> PASS.
- `.venv\Scripts\python -m pip check` -> PASS (`No broken requirements found.`).
- `.venv\Scripts\python scripts\audit_data_readiness.py` -> PASS (`ready_for_paper_alerts = true`; warning `stale_sidecars_max_date_2023-11-27`).
- `.venv\Scripts\python scripts\run_minimal_validation_lab.py --create-input-manifest --promotion-intent` -> PASS.
- `.venv\Scripts\python -m pytest -q` -> PASS with existing skips/warnings.
- `.venv\Scripts\python launch.py --server.headless true --server.port 8599` -> PASS (headless smoke reached local URL; smoke process stopped).

## Open Risks

- yfinance legacy migration remains future debt.
- Primary S&P sidecar is stale through `2023-11-27`.
- Future phases must keep Candidate Registry separate from strategy-search and simulation entry points.

## New Context Packet

## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Closed Phase F Candidate Registry as registry-only work.
- Added frozen candidate/event/snapshot schemas, append-only JSONL event storage, a rebuildable snapshot projection, hash-chain verification, dummy lifecycle evidence, and invariant tests.

## What Is Locked
- No live trading, no broker automation, no paper alerts, no strategy factory, no V2 fast simulator, and no promotion packets.
- Candidate Registry must be append-only and must require candidate metadata, `trial_count`, and a manifest pointer before results.
- yfinance remains non-canonical and quarantined.
- Phase F registry snapshots are not promotion authority; `promotion_ready` remains false.

## What Is Next
- Decide whether Phase G should be V2 Proxy Boundary or advanced registry accounting for trial families and multiple-testing metadata.
- Do not start strategy search until the next phase is explicitly approved.

## First Command
```text
.venv\Scripts\python -m pytest tests/test_candidate_registry.py tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py -q
```

## Next Todos
- Choose Phase G V2 Proxy Boundary or advanced registry accounting.
- Keep Candidate Registry separate from strategy factories and simulation engines.
- Preserve yfinance quarantine and stale-sidecar risk as carried debt.
