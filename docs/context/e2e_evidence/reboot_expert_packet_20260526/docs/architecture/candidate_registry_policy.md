# Candidate Registry Policy

Status: Active for Phase 65 / Phase F
Date: 2026-05-09
Scope: Registry-only candidate intent ledger

## Boundary

Phase F implements only the candidate registry memory and audit layer. It does not implement candidate generation, strategy search, simulation, ranking, promotion packets, alerts, broker calls, live execution, or provider integrations.

Allowed:
- append-only candidate intent registration;
- append-only status transitions;
- manifest-backed candidate metadata before results exist;
- disposable snapshot projection rebuilt from the event log;
- dummy lifecycle proof for one placeholder candidate.

Blocked:
- strategy factory;
- parameter sweep runner;
- V2 fast simulator;
- validation result ingestion;
- promotion packet generation;
- alert emission;
- paper portfolio loop;
- broker or Alpaca behavior;
- new provider integrations.

## Candidate Intent Contract

Every candidate must be registered before any result payload exists. Required fields are:

- `candidate_id`
- `family_id`
- `hypothesis`
- `universe`
- `features`
- `parameters_searched`
- `trial_count`
- `train_window`
- `test_window`
- `cost_model`
- `data_snapshot`
- `manifest_uri`
- `source_quality`
- `created_at`
- `created_by`
- `code_ref`
- `status`

The implementation uses frozen dataclasses for `CandidateSpec`, `CandidateEvent`, and `CandidateSnapshot` so prior candidate intent cannot be mutated by normal object assignment. Status history is changed only by appending events.

## Event Log

Source of truth:

```text
data/registry/candidate_events.jsonl
```

Supported Phase F events:

- `candidate.generated`
- `candidate.status_changed`
- `candidate.note_added`
- `candidate.retired`
- `candidate.rejected`

Every event includes:

- `event_id`
- `candidate_id`
- `event_type`
- `created_at`
- `actor`
- `payload`
- `previous_event_hash`
- `event_hash`

Event hashes are computed from canonical JSON over all event fields except `event_hash`. Each event stores the previous event hash, with the first event anchored to `GENESIS`.

## Snapshot Projection

Derived projection:

```text
data/registry/candidate_snapshot.json
```

The event log is authoritative. The snapshot is disposable and can be rebuilt from JSONL by replaying events.

## Status Machine

Allowed now:

```text
generated -> incubating
incubating -> rejected
generated -> rejected
generated -> retired
generated -> quarantined
```

Forbidden in Phase F:

```text
incubating -> promoted
any -> alerted
any -> executed
```

Promotion readiness is always false in Phase F. Non-canonical candidates are additionally marked with `promotion_block_reason = non_canonical_source_quality`.

## Dummy Lifecycle Proof

The only demo supported by Phase F is:

```text
create dummy candidate
-> generated
-> incubating
-> rejected
-> rebuild snapshot
-> verify hash chain
-> verify manifest pointer exists
-> verify no alert/promotion/execution path exists
```

Dummy candidate:

```text
candidate_id: PH65_PEAD_DUMMY_001
family_id: PEAD_DAILY_RESEARCH
hypothesis: Post-earnings drift candidate placeholder for registry test only.
universe: US_EQUITIES_DAILY
features: ["earnings_surprise_placeholder", "liquidity_filter_placeholder"]
parameters_searched: {"holding_days": [1, 5, 10], "liquidity_floor": ["placeholder"]}
trial_count: 6
source_quality: canonical
manifest_uri: data/processed/phase56_pead_evidence.csv.manifest.json
status: generated
```

No performance metrics, Sharpe ratios, backtest results, or rankings are valid registry fields in Phase F.

## Invariants

- no candidate without `manifest_uri`;
- no candidate without `source_quality`;
- no candidate without `trial_count`;
- no candidate without `parameters_searched`;
- no duplicate `candidate_id`;
- no status mutation outside the append-only event log;
- no snapshot treated as source of truth;
- no Tier 2 or non-canonical candidate can be promotion-ready;
- no alert, promotion, execution, broker, or strategy-search method exists on `CandidateRegistry`.
