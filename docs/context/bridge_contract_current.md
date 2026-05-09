# Bridge Contract - Current

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file reflects D-353, the accelerated provenance + validation + paper-alert gate milestone A-E. It does not authorize live trading, broker automation, promotion, allocator carry-forward, core inclusion, or widening beyond daily US-equity paper-alert validation gates.
Purpose: connect Quant's current technical state back to planner truth and product/system truth after R64.1 hygiene.

## Header
- `BRIDGE_ID`: `20260509-d354-r64-1-closeout-bridge`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E COMPLETE + R64.1 dependency hygiene CLOSED + Phase F approved/not started`
- `STATUS`: `phase65-approved-registry-only`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- The repo now has executable source-quality and validation gates. The planner needs to treat provenance as a runtime gate, not a paragraph in a plan.

## Static Truth Inputs
- `top_level_PM.md`
- `docs/decision log.md`
- `docs/phase_brief/phase64-brief.md`
- `docs/architecture/data_source_policy.md`
- `docs/handover/phase64_handover.md`

## Live Truth Now
- `SYSTEM_NOW`: `Quant has manifest-backed provenance gates, provider ports, yfinance quarantine, data readiness audit, minimal validation lab, and a clean main Alpaca dependency path via alpaca-py.`
- `ACTIVE_SCOPE`: `D-353 A-E and R64.1 hygiene are complete; Phase F Candidate Registry is approved but not started.`
- `BLOCKED_SCOPE`: `Live Alpaca orders, broker automation, strategy search, V2 fast simulation, paper alerts, options/futures, Tier 2 promotion packets, yfinance canonical truth, and credential material in source/docs/logs/artifacts remain blocked.`

## What Changed This Round
- `SYSTEM_DELTA`: `Provenance became the first executable gate: validation reports require manifests, promotion intent requires canonical source quality, and alerts/quotes require source-quality metadata.`
- `EXECUTION_DELTA`: `Added data/provenance.py, data/providers/*, scripts/audit_data_readiness.py, validation/*, scripts/run_minimal_validation_lab.py, focused tests, and R64.1 Alpaca SDK hygiene. Alpaca quote snapshots now carry feed-quality tags and non-paper endpoint initialization requires a signed decision env gate.`
- `NO_CHANGE`: `No live trading authority, no broker automation, no core/engine.py mutation, no research_data mutation, no yfinance canonical upgrade, and no promotion path were introduced.`

## PM / Product Delta
- `STRONGER_NOW`: `The system can now refuse missing-manifest validation, Tier 2 promotion attempts, source-quality-free alerts, and untagged Alpaca IEX quotes in tests/runtime helpers.`
- `WEAKER_NOW`: `The actual yfinance legacy surface is larger than the plan list and remains quarantined rather than removed.`
- `STILL_UNKNOWN`: `Whether Alpaca account entitlements support SIP/delayed SIP for higher-quality operational marking.`

## Planner Bridge
- `OPEN_DECISION`: `None for R64.1. Phase F Candidate Registry is approved as registry-only work.`
- `RECOMMENDED_NEXT_STEP`: `Implement Phase F candidate registry with append-only lifecycle, required trial_count, and required manifest pointer.`
- `WHY_THIS_NEXT`: `Candidate metadata must exist before multiple-testing correction, strategy search, and paper-alert packets can claim controlled discovery lineage.`
- `NOT_RECOMMENDED_NEXT`: `Do not use live Alpaca credentials, do not place live orders, do not delete yfinance blindly, and do not treat readiness or validation reports as promotion authority.`

## Locked Boundaries
- `DO_NOT_REDECIDE`:
  - `yfinance is Tier 2 discovery/convenience data only.`
  - `Alpaca is operational/paper market data only for this milestone.`
  - `Promotion-intent validation requires canonical source quality and a manifest.`
  - `No live trading without a later signed decision-log packet.`
- `BLOCKED_UNTIL`:
  - `Live Alpaca orders remain blocked until explicit signed decision-log approval.`
  - `Broker automation remains blocked until BrokerPort and risk/alert packet contracts are complete.`
  - `Tier 2 promotion packets remain blocked permanently unless source quality is corrected by canonical evidence.`

## Evidence Used
- `docs/architecture/data_source_policy.md`
- `docs/phase_brief/phase64-brief.md`
- `docs/handover/phase64_handover.md`
- `data/processed/data_readiness_report.json`
- `data/processed/data_readiness_report.json.manifest.json`
- `data/processed/minimal_validation_report.json`
- `data/processed/minimal_validation_report.json.manifest.json`
- `data/processed/phase56_pead_evidence.csv.manifest.json`
- `requirements.txt`
- `requirements.lock`
- `pyproject.toml`
- `.venv\Scripts\python -m pip check` -> PASS
- `tests/test_dependency_hygiene.py`
- `tests/test_provenance_policy.py`
- `tests/test_provider_ports.py`
- `tests/test_data_readiness_audit.py`
- `tests/test_minimal_validation_lab.py`

## Open Risks
- `yfinance quarantine surface is broad and should be migrated gradually behind provider ports.`
- `Primary S&P sidecar is stale through 2023-11-27.`
- `Unrelated pre-existing dirty files must remain excluded from R64/R65 commits.`
