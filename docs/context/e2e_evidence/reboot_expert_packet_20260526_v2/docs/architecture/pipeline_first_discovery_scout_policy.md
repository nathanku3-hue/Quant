# Pipeline-First Discovery Scout Policy

Status: G8.1B backend/governance policy
Authority: Phase 65 G8.1B Pipeline-First Discovery Scout Baseline
Date: 2026-05-10

## Purpose

G8.1B proves one governed scout pipeline before any broader discovery surface exists.

The pipeline starts from the existing local Phase 34 artifact:

```text
data/processed/phase34_factor_scores.parquet
```

It wraps that artifact as `LOCAL_FACTOR_SCOUT`, emits exactly one tiny intake-only item, and prevents rank, score, recommendation, validation, candidate-card, dashboard, provider, alert, or broker leakage.

## Scope

Approved:

- inspect local Phase 34 factor-score metadata;
- define the `4-Factor Equal-Weight Scout Baseline`;
- record source artifact row count, date range, and universe count;
- define equal factor weights for the four existing normalized factor columns;
- choose one deterministic fixture row by latest as-of date, local metadata eligibility, and ascending `permno`;
- emit one `LOCAL_FACTOR_SCOUT` intake-only output item;
- validate no score, no rank, no trading language, no candidate card, and no yfinance canonical evidence.

Blocked:

- factor optimization;
- model validation;
- alpha claims;
- ranking;
- score display;
- recommendation language;
- broader screen generation;
- dashboard runtime behavior;
- provider calls;
- alerts;
- broker behavior.

## Deterministic Selection Rule

G8.1B uses a deterministic fixture rule:

```text
eligible_rows =
  rows where date = max(date)
  and score_valid = true
  and all four normalized factor columns are non-null
  and local ticker/company metadata is available

selected_row = first eligible row ordered by asof_date descending, permno ascending
```

This is not a ranking rule. It does not use raw score ordering and does not imply that the selected name is better than any other name.

## System-Scouted Meaning

`is_system_scouted = true` means only this:

```text
The deterministic governed scout pipeline surfaced the name for research intake.
```

It does not mean:

- validated;
- actionable;
- recommended;
- promoted to a candidate card;
- proven as alpha evidence.

## Artifact Contract

Required artifacts:

- `data/discovery/local_factor_scout_baseline_v0.json`
- `data/discovery/local_factor_scout_baseline_v0.manifest.json`
- `data/discovery/local_factor_scout_output_tiny_v0.json`
- `data/discovery/local_factor_scout_output_tiny_v0.manifest.json`

The output artifact must contain exactly one item with:

```text
discovery_origin = LOCAL_FACTOR_SCOUT
status = intake_only
is_user_seeded = false
is_system_scouted = true
is_validated = false
is_actionable = false
not_alpha_evidence = true
```

## Closure Rule

G8.1B is complete only when focused tests validate the baseline contract, output contract, manifests, deterministic selection, and forbidden-output guardrails.
