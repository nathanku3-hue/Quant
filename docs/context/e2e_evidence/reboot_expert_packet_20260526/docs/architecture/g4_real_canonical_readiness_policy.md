# G4 Real Canonical Dataset Readiness Policy

Status: Active for Phase 65 G4
Date: 2026-05-09
Scope: one tiny real Tier 0 canonical daily price slice checked for readiness only

## Purpose

G4 is the first controlled contact with real canonical data after the G3 replay proof.
It validates a tiny `prices_tri` slice for dataset readiness before any downstream replay,
strategy search, ranking, alert, broker action, or promotion packet is allowed.

Governance framing:

- Federal Reserve SR 26-2, published April 17, 2026, supersedes SR 11-7 and SR 21-8 and emphasizes risk-based model governance, documentation, controls, and validation: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
- NIST CSRC defines data integrity as protection against unauthorized alteration across storage, processing, and transit, supporting dataset integrity as a first-class pre-use control: https://csrc.nist.gov/glossary/term/data_integrity

## Allowed Flow

```text
data/processed/prices_tri.parquet
-> tiny canonical slice under data/fixtures/g4/
-> required Tier 0 manifest
-> manifest/hash/schema/date reconciliation
-> finite/domain/key/monotonicity/freshness checks
-> optional readiness report and report manifest
-> ready_for_g5 is readiness-only, not alpha evidence
```

## Canonical Slice

```text
artifact: data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet
manifest: data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet.manifest.json
source artifact: data/processed/prices_tri.parquet
dataset_name: prices_tri_real_canonical_tiny_slice
source_quality: canonical
source_tier: tier0
provider: terminal_zero
provider_feed: tri_repaired_prices
rows: 123
symbols: 3
date_range: 2024-01-02 -> 2024-02-29
primary_key: date, permno
schema: date, permno, ticker, tri, total_ret, legacy_adj_close, raw_close, volume
sidecar_required: false
```

## Readiness Gates

G4 must pass all of these before `ready_for_g5 = true`:

1. Tier 0 canonical source gate.
2. Required manifest gate.
3. Manifest SHA-256 reconciliation.
4. Manifest row-count reconciliation.
5. Manifest schema reconciliation.
6. Manifest date-range reconciliation.
7. Finite numeric value check.
8. Duplicate primary-key rejection.
9. Monotonic dates per `permno`.
10. Positive price-domain check for `tri`, `legacy_adj_close`, and `raw_close`.
11. Return-domain check for `total_ret`.
12. Freshness check.
13. Sidecar optional by default; stale required sidecars block readiness.

## Required Report Fields

```text
readiness_run_id
dataset_name
artifact_uri
manifest_uri
manifest_sha256
source_quality = "canonical"
provider
provider_feed
row_count
date_range
symbol_count
primary_key
schema_version
finite_numeric_check
duplicate_key_check
date_monotonicity_check
price_domain_check
return_domain_check
freshness_check
sidecar_required = false
ready_for_g5
blockers
warnings
created_at
code_ref
```

## Blocked Scope

Blocked in G4:

- strategy search;
- V2 discovery;
- PEAD, momentum, value, ML, or factor logic;
- candidate rankings;
- alpha, Sharpe, CAGR, drawdown, score, rank, or PnL metrics;
- alerts;
- broker calls;
- Alpaca, OpenClaw, notifier, MLflow, DVC, external-engine paths;
- promotion packets;
- yfinance, public web, OpenBB, or Tier 2 source promotion;
- S&P sidecar freshness repair except the explicit stale-sidecar negative test.

## Implementation Paths

```text
v2_discovery/readiness/__init__.py
v2_discovery/readiness/canonical_slice.py
v2_discovery/readiness/canonical_readiness.py
v2_discovery/readiness/schemas.py
tests/test_g4_real_canonical_readiness_fixture.py
data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet
data/fixtures/g4/prices_tri_real_canonical_tiny_slice.parquet.manifest.json
data/registry/g4_real_canonical_readiness_report.json
data/registry/g4_real_canonical_readiness_report.json.manifest.json
```

## Verification

Focused G4 tests:

```text
.venv\Scripts\python -m pytest tests\test_g4_real_canonical_readiness_fixture.py -q
```

Passing G4 readiness means the tiny canonical slice is fit for the next governed replay decision.
It does not authorize strategy search, alpha claims, alerts, broker actions, or promotion.
