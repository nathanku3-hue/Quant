# Local Factor Scout Baseline Policy

Status: G8.1B local artifact wrapper
Authority: Phase 65 G8.1B Pipeline-First Discovery Scout Baseline
Date: 2026-05-10

## Baseline Name

Approved label:

```text
4-Factor Equal-Weight Scout Baseline
```

Approved model id:

```text
LOCAL_FACTOR_EQUAL_WEIGHT_V0
```

Forbidden labels:

- alpha model;
- ranking engine;
- recommendation engine;
- buy/sell model.

## Source Artifact

The source artifact is:

```text
data/processed/phase34_factor_scores.parquet
```

G8.1B records the artifact as local governance input only:

```text
source_artifact_row_count = 2555730
source_artifact_date_range = 2000-01-03 to 2026-02-13
source_artifact_universe_count = 389
```

This artifact may contain internal numeric columns. G8.1B does not expose those numeric values in product output.

## Factor Contract

The baseline uses the four existing normalized factor columns:

```text
momentum_normalized
quality_normalized
volatility_normalized
illiquidity_normalized
```

The G8.1B wrapper assigns equal metadata weights:

```text
weight = 0.25 for each factor
sum(weights) = 1.0
```

This formula is a governance label for the existing artifact wrapper. It is not model optimization and is not validation evidence.

## Required Metadata

The baseline artifact must include:

- `scout_model_id`;
- `scout_model_name`;
- `scout_model_version`;
- `source_artifact`;
- `source_artifact_row_count`;
- `source_artifact_date_range`;
- `source_artifact_universe_count`;
- `factor_names`;
- `factor_weights`;
- `input_data_manifest`;
- `output_manifest`;
- `asof_date`;
- `universe`;
- `not_alpha_evidence = true`;
- `no_rank = true`;
- `no_score_display = true`;
- `no_buy_sell_signal = true`.

## Future Validation Gap

Before the local factor artifact can become a validated discovery model, a later expert review must assess factor definitions, normalization, weighting, universe construction, as-of dating, leakage, survivorship bias, turnover, costs, and rebalance schedule.

G8.1B deliberately does none of that work.
