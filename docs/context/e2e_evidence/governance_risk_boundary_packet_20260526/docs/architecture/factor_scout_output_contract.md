# Factor Scout Output Contract

Status: G8.1B output schema contract
Authority: Phase 65 G8.1B Pipeline-First Discovery Scout Baseline
Date: 2026-05-10

## Output Shape

The G8.1B output is a tiny intake-only scout fixture:

```text
data/discovery/local_factor_scout_output_tiny_v0.json
```

It must contain exactly one item. It is not a list, screen, dashboard feed, candidate card, score table, or recommendation artifact.

## Allowed Item Fields

The item may expose:

- `ticker`;
- `company_name`;
- `discovery_origin = LOCAL_FACTOR_SCOUT`;
- `scout_model_id`;
- `asof_date`;
- `reason_bucket`;
- `factor_exposures_available = true`;
- `evidence_needed`;
- `thesis_breakers_to_check`;
- `provider_gaps`;
- `status = intake_only`;
- `not_alpha_evidence = true`;
- `is_user_seeded = false`;
- `is_system_scouted = true`;
- `is_validated = false`;
- `is_actionable = false`.

## Forbidden Output Fields

The item must not expose:

- raw score values;
- raw rank values;
- `factor_score`;
- `alpha`;
- `expected_return`;
- recommendation language;
- action language;
- `best`;
- `top_pick`;
- validation claims;
- actionability claims;
- candidate-card creation fields.

## Manifest Rule

The output must have a sidecar manifest:

```text
data/discovery/local_factor_scout_output_tiny_v0.manifest.json
```

The manifest must reconcile:

- artifact URI;
- artifact SHA-256;
- row count = 1;
- model id and version;
- baseline manifest URI;
- source artifact URI;
- no yfinance canonical source;
- allowed and forbidden use.

## Product Meaning

`LOCAL_FACTOR_SCOUT` is a provenance origin, not a promotion state.

`system_scouted` means only that a governed deterministic local pipeline surfaced the name for research intake. It does not mean validated, actionable, recommended, or alpha-backed.
