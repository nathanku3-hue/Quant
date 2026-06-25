# V2 Alpha Factory Immediate Todo Directive

Status: Idea/directive intake, not a decision
Date: 2026-06-01
Owner: PM / Architecture Office
RoundID: ROUND-20260601-V2-ALPHA-FACTORY-DIRECTIVE
ScopeID: SCOPE-DOCS-ONLY-IMMEDIATE-TODO-FIRSTS

## Authority

This document records immediate TODO-first direction only. It does not approve implementation, WRDS/provider access, data generation, candidate scoring, candidate ranking, promotion, boot readiness, live trading, broker/order execution, alerts, autonomous allocation, or any runtime behavior change.

Current locked truth remains in force:

- DataReadyStrict remains `BLOCKED_MISSING_GOVERNED_ARTIFACTS`.
- SafeBoot remains `false`.
- BootReady remains `BLOCKED`.
- Local dirty/ignored artifacts are not clean GitHub truth or BootReady evidence.
- V2 research outputs cannot directly touch capital or claim V1 promotion readiness.

## Immediate Todo Firsts

1. WRDS Permission + PIT Snapshot + Provenance Layer
   - Purpose: make WRDS permissions, PIT snapshots, source provenance, manifests, row counts, hashes, schemas, and extraction logs the foundation for all later alpha work.
   - Intended sandbox paths: `v2_discovery/data_lab/wrds_probe.py`, `v2_discovery/data_lab/wrds_snapshot_builder.py`, `v2_discovery/data_lab/manifest.py`, `v2_discovery/data_lab/schema_registry.py`, and `contracts/data_snapshot/wrds_snapshot_manifest.schema.json`.
   - Boundary: probe/snapshot work requires explicit approval before any provider access or snapshot generation.

2. PEAD Variant Factory
   - Purpose: extend the existing Phase 56 PEAD sleeve into a high-throughput research-only variant generator after PIT/provenance foundations are approved.
   - Candidate axes: surprise, announcement gap return, analyst revisions, volume shock, pre-event runup, short-interest pressure, accrual quality, sector/industry neutralization, liquidity buckets, entry delay, holding window, rebalance cadence, and universe choice.
   - Boundary: variant generation is research-only and cannot become candidate ranking/scoring or promotion without the research-validity and V1 evidence gates.

3. Corporate Actions / Capital Return Edge Lab
   - Purpose: extend Phase 57 with capital-return event logic that combines payout behavior, balance-sheet quality, issuance discipline, and liquidity regime.
   - Candidate axes: net payout yield, repurchase intensity, dividend change, issuance dilution, debt-financed buyback flags, capex-cut-plus-buyback flags, share-count change, profitability quality, accrual quality, and distress filters.
   - Boundary: V1 remains unchanged until V2 produces an approved promotion packet and official V1 review is requested.

4. Meta-labeling / Edge Survival Model
   - Purpose: support existing sleeves by estimating when a candidate or sleeve is likely to survive costs, slippage, regime pressure, crowding, and signal decay.
   - Candidate features: regime state, VIX/liquidity/credit proxies, breadth, earnings-season density, short-interest pressure, dispersion, crowding, turnover pressure, sector concentration, and signal freshness.
   - Boundary: output may be `incubating`, `reject`, or `send_to_v1`; it must not be a direct trade recommendation.

5. Orbis / BvD Private Company Network Edge
   - Purpose: explore a potentially differentiated data advantage from private-company and ownership/network information if access is approved.
   - Candidate graph concepts: public equities, private subsidiaries, private suppliers, banks, parents, regional peers, ownership, subsidiary, shareholder, industry, country, manager/director links if available, and identifier links.
   - Boundary: this is later than PEAD/corporate actions because entity resolution, PIT drift, and identifier linking are difficult; keep it read-only and sandboxed.

## Deferred / Do Not Lead With

- LLM market-news agents: defer because the near-term gap is auditable WRDS/PIT/candidate evidence, not more narrative generation.
- DRL portfolio allocator: defer as a bounded research spike only after the V2 evidence factory matures.
- Live trading or direct routing: blocked; V2 cannot touch capital and proxy evidence cannot claim promotion readiness.
- SQLite candidate storage: not approved. Repo constraints forbid SQLite without explicit approval; prefer Parquet/DuckDB-compatible registry design unless policy changes.

## Proposed Research-Only Shape

The directive proposes a V2 sandbox shape, not an approved implementation:

```text
v2_discovery/
  data_lab/
  feature_lab/
  generators/
  fast_sim/
  screening/
  robustness/
  registry/
```

Outputs should be candidate packets, robustness matrices, kill logs, and requested V1 actions, not direct buys or recommendations.

Example acceptable output shape:

```text
candidate_id: pead_v2_YYYYMMDD_003
economic_thesis: earnings underreaction survives in a liquid quality bucket
data_snapshot: <approved PIT snapshot id>
feature_hash: <hash>
proxy_sharpe: <research-only metric>
official_v1_ready: false
failure_modes:
  - dies above a cost threshold
  - concentrated in one sector/era
  - weak in a stressed regime
requested_v1_action: official_backtest
```

## Required Approval Gates Before Execution

- Approve WRDS/source access and the exact read-only probe scope.
- Approve any PIT snapshot generation, manifest policy, storage path, and rollback/removal rule.
- Approve any candidate-registry storage design; SQLite remains forbidden without explicit approval.
- Approve any candidate scoring/ranking/screening semantics separately from docs-only directive intake.
- Keep all outputs research-only until V1 official evidence gates review them.

## Logic Chain

Approved source access -> PIT/provenance snapshot -> V2 research-only feature families -> proxy/robustness evidence -> candidate packet -> requested V1 official backtest.

## Formula Summary

No formula changed in this docs-only directive. Future formulas for PEAD, payout, meta-labeling, network shocks, cost sensitivity, IC, PBO, capacity, or promotion packets must be recorded with source `.py` paths when implemented.
