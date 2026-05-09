# Bridge Contract - Current

Status: Current integration bridge
Authority: advisory-only PM/planner bridge. This file reflects D-353, the accelerated provenance + validation + paper-alert gate milestone A-E. It does not authorize live trading, broker automation, promotion, allocator carry-forward, core inclusion, or widening beyond daily US-equity paper-alert validation gates.
Purpose: connect Quant's current technical state back to planner truth and product/system truth after Phase 65.

## Header
- `BRIDGE_ID`: `20260509-d355-phase65-closeout-bridge`
- `DATE_UTC`: `2026-05-09`
- `SCOPE`: `D-353 A-E COMPLETE + R64.1 dependency hygiene CLOSED + Phase F Candidate Registry CLOSED`
- `STATUS`: `phase65-closed-registry-only`
- `OWNER`: `PM / Architecture Office`

## Why This File Exists
- The repo now has executable source-quality, validation, and candidate-identity gates. The planner needs to treat provenance and candidate lineage as runtime gates, not paragraphs in a plan.

## Static Truth Inputs
- `top_level_PM.md`
- `docs/decision log.md`
- `docs/phase_brief/phase64-brief.md`
- `docs/phase_brief/phase65-brief.md`
- `docs/architecture/data_source_policy.md`
- `docs/architecture/candidate_registry_policy.md`
- `docs/handover/phase65_handover.md`

## Live Truth Now
- `SYSTEM_NOW`: `Quant has manifest-backed provenance gates, provider ports, yfinance quarantine, data readiness audit, minimal validation lab, a clean main Alpaca dependency path via alpaca-py, and an append-only Candidate Registry.`
- `ACTIVE_SCOPE`: `D-353 A-E, R64.1 hygiene, and Phase F Candidate Registry are complete; next work requires a new explicit phase decision.`
- `BLOCKED_SCOPE`: `Live Alpaca orders, broker automation, strategy search, V2 fast simulation, paper alerts, options/futures, Tier 2 promotion packets, yfinance canonical truth, and credential material in source/docs/logs/artifacts remain blocked.`

## What Changed This Round
- `SYSTEM_DELTA`: `Candidate intent is now recorded in an append-only registry before results exist. Validation reports still require manifests, promotion intent still requires canonical source quality, and alerts/quotes still require source-quality metadata.`
- `EXECUTION_DELTA`: `Added v2_discovery schemas/registry, JSONL event log, snapshot projection, rebuild report, dummy lifecycle script, policy, handover, and invariant tests.`
- `NO_CHANGE`: `No live trading authority, no broker automation, no core/engine.py mutation, no research_data mutation, no yfinance canonical upgrade, no strategy search, no simulator, no alert packet, and no promotion path were introduced.`

## PM / Product Delta
- `STRONGER_NOW`: `The system can now refuse missing-manifest validation, Tier 2 promotion attempts, source-quality-free alerts, untagged Alpaca IEX quotes, missing candidate manifests, missing trial counts, duplicate candidate IDs, invalid lifecycle transitions, and tampered registry event chains.`
- `WEAKER_NOW`: `The actual yfinance legacy surface is larger than the plan list and remains quarantined rather than removed.`
- `STILL_UNKNOWN`: `Whether Alpaca account entitlements support SIP/delayed SIP for higher-quality operational marking.`

## Planner Bridge
- `OPEN_DECISION`: `Choose Phase G V2 Proxy Boundary or advanced registry accounting.`
- `RECOMMENDED_NEXT_STEP`: `Make the Phase G boundary decision; do not start strategy search by default.`
- `WHY_THIS_NEXT`: `Candidate metadata now exists before results; the next bottleneck is whether to formalize V2 boundaries or deepen multiple-testing registry metadata.`
- `NOT_RECOMMENDED_NEXT`: `Do not use live Alpaca credentials, do not place live orders, do not delete yfinance blindly, and do not treat readiness or validation reports as promotion authority.`

## Locked Boundaries
- `DO_NOT_REDECIDE`:
  - `yfinance is Tier 2 discovery/convenience data only.`
  - `Alpaca is operational/paper market data only for this milestone.`
  - `Promotion-intent validation requires canonical source quality and a manifest.`
- `No live trading without a later signed decision-log packet.`
- `Candidate Registry is registry-only and not promotion authority.`
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
- `docs/architecture/candidate_registry_policy.md`
- `docs/handover/phase65_handover.md`
- `v2_discovery/schemas.py`
- `v2_discovery/registry.py`
- `tests/test_candidate_registry.py`
- `data/registry/candidate_registry_rebuild_report.json`

## Open Risks
- `yfinance quarantine surface is broad and should be migrated gradually behind provider ports.`
- `Primary S&P sidecar is stale through 2023-11-27.`
- `Unrelated pre-existing dirty files must remain excluded from R64/R65 commits.`
