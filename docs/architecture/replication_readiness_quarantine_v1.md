# Independent Replication Readiness Quarantine v1

**Date:** 2026-08-10  
**Status:** `IMPLEMENTED_METADATA_CUSTODY / IDENTITY_AND_PIT_CONTRACTS_FROZEN / CURRENT_CANDIDATE_NOT_READY / OUTCOMES_DENIED`  
**Authority:** `docs/architecture/aov_strategic_direction_lock_20260809.md` §11  
**Runtime/provider effect:** `NONE` — no credential use, provider query, raw-data acquisition, replication outcome, or family-specific replication authority  
**financial_alpha_evidence:** `0`

## 1. Purpose

Start the independent-replication lead-time clock before a Challenger needs the data while keeping the replication surface unusable for discovery or confirmatory outcome inspection.

The readiness surface records only:

```text
entitlement feasibility
source/provider feasibility
permanent identity feasibility
PIT/vintage semantics readiness
license/retention feasibility
expected acquisition latency
immutable quarantine custody
```

It is not an independent replication and cannot satisfy any capital gate.

## 2. Code authority

`research/replication_readiness_v1/contracts.py` defines `ReplicationReadinessManifestV1` and immutable write-once custody.

Hard boundaries:

- `research_visibility = READINESS_METADATA_ONLY`;
- `replication_outcome_access = DENIED`;
- `family_specific_acquisition_authority = NOT_AUTHORIZED`;
- `financial_alpha_evidence = 0`;
- ticker/name-only permanent identity is rejected;
- `FEASIBLE` entitlement/source/identity/PIT/license claims require hash-bound evidence or contracts;
- storage must live under a `replication_quarantine` path;
- an existing manifest cannot be overwritten.

There is deliberately no provider connector, credential reader, result/outcome payload, label reader, or performance-statistics surface in this package.

## 3. Current quarantined candidate

Initial custody receipt:

`data/replication_quarantine/readiness_v1/wrds_5table_readiness_20260810.json`

Current evidence-refined receipt:

`data/replication_quarantine/readiness_v1/wrds_5table_readiness_20260810_v2.json`

Candidate surface:

```text
provider = WRDS
source = CRSP + Compustat + IBES five-table candidate
permanent identity candidate = CRSP PERMNO/PERMCO
readiness = NOT_READY
```

The current v2 receipt is intentionally still `NOT_READY`. Two internal contracts are now frozen and hash-bound:

- `data/replication_quarantine/contracts_v1/wrds_5table_permanent_identity_contract_v1.json` — CRSP PERMNO is risky-security identity; PERMCO is grouping only; ticker/name/CUSIP fallback is forbidden; I/B/E/S ticker requires a separately authorized date-effective crosswalk before it can join a PERMNO-keyed replication.
- `data/replication_quarantine/contracts_v1/wrds_5table_pit_vintage_contract_v1.json` — decision-time availability controls over economic dates; date-effective stock-name/CCM links are mandatory; current/restated Compustat values cannot be relabeled original-vintage; I/B/E/S revision chronology cannot be collapsed to latest.

Therefore `permanent_identity_status=FEASIBLE` and `pit_vintage_status=FEASIBLE` in v2. This is contract readiness only, not data/source admission.

The remaining blockers are evidence, not architecture:

1. obtain non-secret, dated, attributable exact-table entitlement evidence;
2. obtain source-feasibility evidence for the intended replication access route;
3. obtain license and retention evidence suitable for immutable internal replication custody;
4. measure/record expected acquisition latency without broad speculative acquisition.

`data/replication_quarantine/evidence_status/wrds_entitlement_license_retention_status_20260810.json` records the current honest state: no qualifying local evidence landed, no credential/secret contents were inspected, no WRDS query occurred, and family-specific acquisition remains forbidden.

## 4. Demand-pulled join

A future family may use this readiness surface only after a separate preregistered replication demand identifies the exact family, sample, identity/PIT contract, acquisition scope, and untouched evaluation boundary.

At that join:

```text
readiness manifest
+ family-specific preregistration
+ qualifying entitlement/license evidence
+ independent source/implementation identity
→ narrowly authorized acquisition
```

Until that separate authority exists, `NOT_AUTHORIZED` is controlling even if all readiness statuses later become feasible. W10 is expressly low-priority and may not delay PREBREAKOUT stock-data evidence or Clock #1 custody.

## 5. Forbidden scope

This v1 does not authorize:

```text
replication outcomes
winner/loser labels
returns or P&L
precision/recall/lift/PR-AUC
family tuning or search
provider login/query
credential inspection
raw replication dataset acquisition
broad speculative vendor purchase
capital promotion
```

Any such material belongs to a later, separately sealed replication run and must not be written into readiness custody.
