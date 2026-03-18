# Phase 35 Repaired Rerun Report

**Date**: 2026-03-08
**Status**: COMPLETE - corrected baseline, W1, and W2 reruns finished on repaired `permno` path

---

## Scope

This report captures the governed rerun round that followed the Phase 35 contract repair:
- repaired runtime evidence path: `data/processed/features_phase35_repaired.parquet`
- same execution path: existing `permno` runtime
- same governed evidence windows:
  - Calibration: `2022-01-01` → `2023-06-30`
  - Validation: `2023-07-01` → `2024-03-31`
  - Holdout: `2024-04-01` → `2024-12-31`
- warmup only: `2020-2021`

---

## Contract Checks

### Repaired Runtime Path
- Canonical derived features were rebuilt locally on top of the runtime feature store.
- Null provenance was repaired and is now fail-closed.
- Repaired-window validation now uses raw-input eligibility for price-derived features.

### Wave Provenance
- W1 and W2 both resolved strictly to:
  - `mom_12m`
  - `quality_composite`
  - `realized_vol_21d`
  - `illiq_21d`
- Silent substitution to legacy proxy columns did not occur in the corrected reruns.

### Attribution Path
- `scripts/attribution_report.py` now excludes `*_source` and `score_valid` from numeric IC / attribution math.

---

## Coverage Snapshot

| Run | Coverage |
| --- | ---: |
| Corrected baseline calibration | 65.76% |
| Corrected baseline validation | 65.97% |
| Corrected baseline holdout | 66.35% |
| W1 calibration | 65.67% |
| W1 validation | 65.79% |
| W1 holdout | 66.03% |
| W2 calibration | 65.67% |
| W2 validation | 65.79% |
| W2 holdout | 66.03% |

---

## Delta vs Corrected Baseline

### Wave 1
- Calibration:
  - coverage delta: `-0.09 pp`
  - mean IC delta: `+0.82 bp`
  - R² delta: `-3.14`
- Validation:
  - coverage delta: `-0.18 pp`
  - mean IC delta: `-45.27 bp`
  - R² delta: `-117.45`
- Holdout:
  - coverage delta: `-0.32 pp`
  - mean IC delta: `-36.93 bp`
  - R² delta: `-7.49`

### Wave 2
- Calibration:
  - coverage delta: `-0.09 pp`
  - mean IC delta: `+0.28 bp`
  - R² delta: `-0.30`
- Validation:
  - coverage delta: `-0.18 pp`
  - mean IC delta: `-40.15 bp`
  - R² delta: `-29.33`
- Holdout:
  - coverage delta: `-0.32 pp`
  - mean IC delta: `-53.27 bp`
  - R² delta: `-272.54`

---

## Decision

### Outcome
- Corrected baseline: runnable and governed on the repaired path
- W1: no-go
- W2: no-go
- Wave 3: blocked

### Why
- Coverage does not improve meaningfully versus the corrected baseline.
- Validation and holdout mean IC deteriorate for both W1 and W2.
- Contribution R² remains severely negative and worsens materially in the wave variants.
- Regime hit-rate remains weak, especially outside GREEN.

### Governance Conclusion
The current Phase 35 wave branch stays closed / pivoted. The repaired contracts are now trustworthy enough to say the failure is not just measurement contamination. Under the corrected same-window path, W1 and W2 still do not justify advancement.

---

## Artifact Paths

### Repaired Features
- `data/processed/features_phase35_repaired.parquet`

### Corrected Baseline
- `data/processed/phase35_reruns/phase35_baseline_corrected_calibration_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_baseline_corrected_validation_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_baseline_corrected_holdout_factor_scores.parquet`

### Wave 1
- `data/processed/phase35_reruns/phase35_w1_calibration_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_w1_validation_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_w1_holdout_factor_scores.parquet`

### Wave 2
- `data/processed/phase35_reruns/phase35_w2_calibration_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_w2_validation_factor_scores.parquet`
- `data/processed/phase35_reruns/phase35_w2_holdout_factor_scores.parquet`

---

**Status**: corrected rerun evidence is complete; W1/W2 remain no-go; Wave 3 blocked
**Progress**: 100/100
**Critical Mission**: preserve the repaired runtime contract and close the current Phase 35 wave branch on corrected evidence rather than stale proxy-path assumptions.
