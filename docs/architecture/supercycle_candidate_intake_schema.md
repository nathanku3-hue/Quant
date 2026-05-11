# Supercycle Candidate Intake Schema

Status: G8.1 schema contract
Authority: Phase 65 G8.1
Date: 2026-05-10

## Required Intake Item Fields

Each intake item must include:

- `ticker`
- `company_name`
- `theme_candidates`
- `why_it_might_belong`
- `evidence_needed`
- `known_source_candidates`
- `official_sources_needed`
- `market_behavior_modules_relevant`
- `thesis_breakers_to_check`
- `provider_gaps`
- `current_status`
- `discovery_origin`
- `origin_evidence`
- `scout_path`
- `is_user_seeded`
- `is_system_scouted`
- `is_validated`
- `is_actionable`
- `not_alpha_evidence = true`
- `no_score = true`
- `no_rank = true`
- `no_buy_sell_signal = true`

## Discovery Origin Fields

Allowed `discovery_origin` values:

- `USER_SEEDED`
- `THEME_ADJACENT`
- `SUPPLY_CHAIN_ADJACENT`
- `PEER_CLUSTER`
- `CUSTOMER_SUPPLIER_LINK`
- `ETF_HOLDING_LINK`
- `SEC_INDUSTRY_LINK`
- `NEWS_RESEARCH_CAPTURE`
- `LOCAL_FACTOR_SCOUT`
- `SYSTEM_SCOUTED`

G8.1A origin map:

```text
MU   -> USER_SEEDED
DELL -> USER_SEEDED + THEME_ADJACENT
INTC -> USER_SEEDED + THEME_ADJACENT
AMD  -> USER_SEEDED + THEME_ADJACENT
LRCX -> USER_SEEDED + SUPPLY_CHAIN_ADJACENT
ALB  -> USER_SEEDED + THEME_ADJACENT
```

All six current names must keep:

```text
is_system_scouted = false
is_validated = false
is_actionable = false
```

`LOCAL_FACTOR_SCOUT` is defined for G8.1B but is not used by the G8.1A queue.

## Status Values

Allowed statuses:

- `candidate_card_exists`
- `intake_only`

G8.1 seed status map:

```text
MU   -> candidate_card_exists
DELL -> intake_only
INTC -> intake_only
AMD  -> intake_only
LRCX -> intake_only
ALB  -> intake_only
```

`MU` must remain the only `candidate_card_exists` item in G8.1.

## Queue-Level Fields

The queue must include:

- `queue_id`
- `created_at`
- `scope`
- `authority`
- `candidate_intake_items`
- `forbidden_outputs`

The queue manifest must include:

- `artifact_uri`
- `artifact_sha256`
- `scope`
- `queue_id`
- `row_count`
- `seed_tickers`
- `status_policy`
- `source_policy`
- `allowed_use`
- `forbidden_use`

## Validation Rules

The validator rejects:

- missing ticker;
- missing theme candidates;
- missing evidence requirements;
- missing thesis breakers;
- missing provider gaps;
- missing discovery origin;
- missing origin evidence;
- missing scout path;
- a current six-name seed marked `SYSTEM_SCOUTED`;
- `LOCAL_FACTOR_SCOUT` usage before G8.1B;
- `is_validated = true`;
- `is_actionable = true`;
- score or rank fields;
- buy/sell/hold calls;
- validated-thesis status;
- action-state promotion to `BUYING_RANGE`, `LET_WINNER_RUN`, `ADD_ON_SETUP`, or `TRIM_OPTIONAL`;
- yfinance as canonical evidence;
- manifests without hash or matching row count.

## Static Artifacts

- `data/discovery/supercycle_discovery_themes_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json`

These are static planning artifacts. They do not authorize provider code or live data access.
