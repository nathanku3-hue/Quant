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
- Add candidate registry schema and persistence.
- Add append-only lifecycle transition API.
- Add dummy candidate lifecycle regression.

## First Command
`.venv\Scripts\python -m pytest tests/test_dependency_hygiene.py tests/test_provider_ports.py tests/test_provenance_policy.py -q`
