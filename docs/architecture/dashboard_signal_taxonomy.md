# Dashboard Proposal, Event, and Diagnostic Taxonomy

Status: `ACTIVE — FINAL PLANNING ROUND`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Primary Slice 1 objects

The active dashboard projects governed objects, not loose signal tiles:

```text
PointInTimeIdentity
EvidenceReference
CapitalProposal
SubmitProposalCommand
Accepted / Identity-Rejected Governance Event
ProposalRecordReadModel
DecisionEpisodeReadModel
EventStreamHealth
ProjectionReplayReceipt
```

`TransitionCandidate`, `TransitionPreview`, authorization, application, and certification objects are later-slice types and are not simulated in Slice 1.

## Proposal-facing categories

Every proposal row exposes:

- module, version, sleeve, and proposal identity;
- exact certified book/head, evidence set, market snapshot, and as-of identity;
- typed outcome;
- target intent and unit;
- normalization summary;
- principal claim;
- supporting and contradicting evidence references;
- missing discriminator and reason not to act;
- extension schema ID/version/digests;
- governance status: eligible or identity rejected.

## Evidence categories

Evidence references are content-addressed. Dashboard categories may include:

- supporting evidence;
- contradicting evidence;
- missing discriminator;
- stale/unavailable source field;
- source identity mismatch;
- extension schema or payload digest mismatch.

No loose text string becomes replay authority without a typed evidence reference.

## Target categories

### Intent

```text
TARGET_FINAL
DELTA
OVERLAY
```

### Instrument unit

```text
QUANTITY
NOTIONAL
WEIGHT
```

### Risk measure and unit

```text
measure: VAR | VOL | GROSS | MARGIN | DELTA
unit:    BPS | PERCENT | USD | NOTIONAL
```

`RISK_BPS` is neither an instrument unit nor a risk measure.

## Governance event categories in Slice 1

- episode opened;
- proposal submitted/ingested with complete proposal;
- proposal accepted;
- proposal rejected for PIT identity mismatch;
- episode aborted.

The exact class names may align with repository conventions. Every visible status must be reconstructable from the implemented event vocabulary.

## Operational diagnostic categories

- source adapter health;
- missing/unavailable field receipt;
- stream sequence and digest-chain health;
- duplicate/gap/idempotence failure;
- projector replay equality;
- canonical row-order status;
- session-state authority scan;
- production mock-row scan;
- negative-authority proof.

## Forbidden taxonomy drift

- no standalone signal strength becomes capital authority;
- no UI-only status becomes lifecycle truth;
- no unsupported stale/boundary/selected state appears without its events;
- no pipeline-health metric implies alpha, recommendation, or live readiness;
- no future risk model is presented as solitary truth.
