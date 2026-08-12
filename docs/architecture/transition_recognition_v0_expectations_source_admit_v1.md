# TRANSITION_RECOGNITION_v0 — Expectations Source Admission v1

**Slice:** `TR-v0-L2B-EXPECTATIONS-SOURCE-ADMIT-1`
**Phase:** `L2B_SOURCE_ADMISSION`
**Role:** `SOURCE_CUSTODY_ONLY / OUTCOME_BLIND / NO_TRIAL`
**Terminal:** `HOLD_SOURCE`

## Golden gate

This slice asks only:

> Can we obtain an exact, PIT-correct, independently sourced consensus history for the already-frozen Recognition variables cheaply enough to justify continuing?

It does **not** ask whether Recognition predicts returns.

## Frozen source surface

Primary:

- `EPS_FY1`
- `EPS_FY1_REVISION_30D`

Secondary:

- `EPS_FY1_REVISION_90D`

No FY2, revenue estimates/revisions, forward P/E, momentum, price confirmation, guidance NLP, timing, returns, or economic trial enters this slice.

## Family authority boundary

The incumbent concrete Alpha-PIT expectation producer is CRV1-bound:

```text
source_id        = SPCIQPRO:CRV1_EXPECTATIONS
default family   = CYCLE_RESONANCE_v1
```

TR-v0 therefore may **not** consume or relabel the CRV1 expectation artifact as family authority.

Law:

```text
same lawful raw CIQ bytes
        ↓
may be reused if source semantics truly match
        ↓
TR-v0-specific receipt + source authority
```

The admission gate uses `SPCIQPRO:TR_V0_EXPECTATIONS` and an explicit `TRANSITION_RECOGNITION_v0` family contract. Raw custody may be shared; family authority may not.

## G-S0 — source semantics

PASS requires exact binding of:

- CIQ EPS FY1 provider field/function;
- FY1 forecast-period law and forecast-period-end field;
- historical/as-of vintage semantics;
- publication / `available_at` law;
- CIQSEC permanent security identity;
- 30d / 90d revision as either an exact provider-observed metric or one deterministic outcome-blind construction from lawful EPS FY1 history.

The bounded repository and local-custody scan found the canonical Alpha-PIT expectations schema and CRV1 mechanical adapter, but **did not find an authoritative landed CIQ capture mapping or raw consensus history for these three measures**. The proved CIQ provider runbook currently binds market and historical-fundamental surfaces, not these EPS-consensus semantics.

That is the hard velocity stop. Resolving provider field IDs/functions and historical-vintage interpretation would require another provider-semantic discovery round, so this slice does not continue into broad reverse engineering.

**G-S0 = HOLD → `HOLD_SOURCE`.**

## G-S1 — custody

Not run after the G-S0 fail-fast.

When a future exact semantic bind exists, G-S1 requires:

- local raw bytes;
- TR-v0-specific receipt;
- raw SHA-256 and semantic-manifest SHA-256;
- provider, retrieval time, license scope and retention class;
- explicit `crv1_artifact_authority_reused=false`.

No provider bytes or source receipt are fabricated for the current HOLD terminal.

## G-S2 — PIT validation

Not run after the G-S0 fail-fast.

The implemented gate fail-closes on:

- `available_at > decision_as_of`;
- `observed_at > available_at`;
- naive timestamps or future vintage;
- ticker/non-CIQSEC identity fallback;
- unknown/parked measures;
- duplicate `(security_id, measure, available_at)` keys;
- implicit missingness;
- non-`OBSERVED_CONSENSUS` epistemic class;
- raw bytes carrying family authority.

Canonical admitted rows are exactly:

```text
security_id
measure
value
forecast_period_end
observed_at
available_at
source_id
source_receipt_sha256
epistemic_class
coverage_status
missingness_reason
```

## Deterministic revision option

The gate supports one low-freedom, outcome-blind construction when a lawful EPS FY1 history is source-bound:

```text
construction = TR_V0_EPS_FY1_ABS_DELTA_SAME_FPE_LOOKBACK_V1
revision_Nd  = current EPS_FY1 - latest PRESENT EPS_FY1
               for the same forecast_period_end
               with available_at <= current.available_at - N calendar days
N            = 30 or 90
```

If no lawful same-period lookback exists, the revision is explicit `MISSING_HISTORY`; it is never filled from another forecast period. This option does not cure the current G-S0 failure because the underlying exact CIQ EPS FY1 source semantics are themselves unbound.

## Terminal

```text
HOLD_SOURCE
  failed_gate = G-S0 SOURCE_SEMANTICS
  bytes       = not landed
  receipt     = not landed
  debit       = 0
  returns     = not inspected
  timing      = not researched
  alpha       = 0

NEXT = park TR-v0
       spend research WIP on another independent family
```

If a future bounded owner slice supplies the exact CIQ semantic bind and lawful bytes, re-run this same gate. Only `PASS_SOURCE_ADMITTED` may open `TR-v0-L3-REPRESENTATION-SNR-1`.
