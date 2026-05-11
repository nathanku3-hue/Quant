# Supercycle Scout Protocol

Status: G8.1A protocol with G8.1B preview held
Authority: Phase 65 G8.1A Discovery Drift Correction
Date: 2026-05-10

## G8.1A Scope

G8.1A is product-governance and schema discipline. It labels where a discovery intake item came from and keeps the user-seeded queue distinct from system-scouted output.

No math/modeling expert is required for G8.1A because no factor model is designed, changed, optimized, or consumed.

## Scout Path Rule

`scout_path` must describe the provenance path that placed the name in the intake queue.

Examples:

```text
manual_user_seed
theme_adjacency:AI_SERVER_SUPPLY_CHAIN
supply_chain_adjacency:MEMORY_STORAGE_SUPERCYCLE
```

If `is_system_scouted = true`, `scout_path` must be non-empty and must point to a governed scout artifact. G8.1A has no governed system-scout artifact.

## G8.1B Preview

G8.1B may inspect:

```text
data/processed/phase34_factor_scores.parquet
```

But it must wrap that artifact in a new scout contract before using it:

```text
scout_model_id
scout_model_version
factor_names
factor_weights
input_data_manifest
output_manifest
asof_date
universe
artifact_row_count
date_range
not_alpha_evidence = true
no_rank = true
no_score_display = true
no_buy_sell_signal = true
```

The G8.1B label should be:

```text
4-Factor Equal-Weight Scout Baseline
```

It must not be labeled:

```text
Alpha model
Recommendation engine
Ranker
```

## Held Until Approval

G8.1A does not read, wrap, expose, rank, or display factor scores. `LOCAL_FACTOR_SCOUT` is defined only so G8.1B has a governed label available later.
