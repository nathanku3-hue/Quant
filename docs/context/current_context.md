## What Was Done
- Closed D-353 A-E provenance + validation gates.
- Closed R64.1 dependency hygiene with `alpaca-py==0.43.4` and a passing `pip check`.
- Closed Phase F Candidate Registry as registry-only work.
- Added frozen candidate/event/snapshot schemas, append-only JSONL event storage, a rebuildable snapshot projection, hash-chain verification, dummy lifecycle evidence, and invariant tests.

## What Is Locked
- No live trading, no broker automation, no paper alerts, no strategy factory, no V2 fast simulator, and no promotion packets.
- Candidate Registry is append-only and requires candidate metadata, `trial_count`, and a manifest pointer before results.
- yfinance remains non-canonical and quarantined.
- Phase F registry snapshots are not promotion authority; `promotion_ready` remains false.

## What Is Next
- Decide whether Phase G should be V2 Proxy Boundary or advanced registry accounting for trial families and multiple-testing metadata.
- Do not start strategy search until the next phase is explicitly approved.
- Phase G option A: V2 Proxy Boundary, no strategy factory.
- Phase G option B: advanced registry accounting, no simulation engine.
- Later only after approval: strategy search, V2 fast simulation, alert packets, promotion packets.

## First Command
`.venv\Scripts\python -m pytest tests/test_candidate_registry.py tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py -q`
