# Phase 65 Brief

Status: APPROVED - NOT STARTED
Authority: D-354 R64.1 closeout approval
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

- [ ] CHK-P65-01: Candidate registry persists candidate metadata before any result payload.
- [ ] CHK-P65-02: Candidate state transitions are append-only and preserve prior state history.
- [ ] CHK-P65-03: `trial_count` is required and non-negative.
- [ ] CHK-P65-04: Manifest pointer is required and must reference an existing manifest.
- [ ] CHK-P65-05: Dummy candidate lifecycle passes: `generated -> incubating -> rejected`.
- [ ] CHK-P65-06: Prior candidate state cannot be mutated in place.
- [ ] CHK-P65-07: No strategy generation, promotion packet, alert emission, or live/broker path is introduced.

## First Test

```text
dummy candidate -> generated -> incubating -> rejected -> audit log preserved -> manifest pointer required -> cannot mutate prior state
```

## Preconditions Satisfied By R64.1

- `pip check` passes.
- Main Alpaca dependency is `alpaca-py==0.43.4`.
- Legacy `alpaca-trade-api` is excluded from the main dependency set.
- yfinance quarantine tests pass.
- Data readiness and minimal validation lab pass.
- R64.1 surgical commits separate milestone files from unrelated dirty files.

## Open Risks

- yfinance legacy migration remains future debt.
- Primary S&P sidecar is stale through `2023-11-27`.
- Candidate Registry must avoid becoming a strategy-search entry point in this phase.

## New Context Packet

## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Approved Phase F Candidate Registry as registry-only work.

## What Is Locked
- No live trading, no broker automation, no paper alerts, no strategy factory, no V2 fast simulator, and no promotion packets.
- Candidate Registry must be append-only and must require candidate metadata, `trial_count`, and a manifest pointer before results.
- yfinance remains non-canonical and quarantined.

## What Is Next
- Implement the Candidate Registry data model, append-only transition log, validation helpers, and dummy lifecycle test.
- Keep Phase F boring: identity, lineage, and audit trail before experiments.

## First Command
```text
.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py -q
```

## Next Todos
- Add candidate registry schema and persistence.
- Add append-only lifecycle transition API.
- Add dummy candidate lifecycle regression.
