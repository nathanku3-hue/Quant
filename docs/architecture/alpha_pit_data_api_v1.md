# Alpha PIT Data API v1 — Narrow Internal Research Contract

**Date:** 2026-08-09
**Status:** `BUILD_SPEC / CLOCK_1_RELEASED / MECHANICS_IMPLEMENTED / CRV1_RISK_SET_BLOCKED`
**Authority:** implementation contract for the first post-Clock Alpha Discovery Lane only
**First consumer:** `CYCLE_RESONANCE_v1`
**Current execution effect:** **MECHANICAL PRODUCER ACTIVE / NO CRV1 EMPIRICAL AUTHORITY YET** — the capability firewall, content-addressed artifacts, concrete CIQ structured adapter, SEC-claims adapter boundary, explicit missingness, and current-CIQ custody validation are implemented; the independent non-growth `CRV1_US_PRIMARY_COMMON_V1` risk-set source is not landed, CIQ expectations are not landed, and SEC claim bytes are not landed
**Schema family:** `alpha_pit_data_api_v1`
**2026-08-09 strategic lock:** current v1 remains deliberately CRV1-first; when the second real Alpha Family opens, extract only a tiny immutable `FamilyDataContract` rather than cloning a platform or preserving CRV1 globals as shared authority (`docs/architecture/aov_strategic_direction_lock_20260809.md`)

---

# 0. Purpose

Define one narrow, point-in-time internal research API that supplies exactly the information surfaces required by `CYCLE_RESONANCE_v1` without inheriting older planning/readiness APIs and without creating a generic provider platform.

The API answers five questions:

```text
risk_set(as_of)
observations(ids, fields, as_of)
source_claims(ids, as_of)
expectations(ids, as_of)
discovery-only outcomes(risk_set_id, label_spec)
```

Every response is content-addressed and binds permanent identity, time availability, source receipts, schema, coverage/missingness, and artifact hashes.

The API SHALL NOT expose a generic provider registry, feature store, scraping platform, universal document-intelligence layer, or compatibility bridge.

---

# 1. Authority boundary — destructive, no compatibility

The following historical documents remain audit/planning evidence only and SHALL NOT become runtime dependencies of this API:

- `docs/architecture/godview_api_availability_matrix.md` — explicitly planning-only;
- `docs/architecture/data_readiness_gate_v0.md` — older boot/route readiness contract;
- `docs/architecture/governed_data_source_provenance_intake_20260528.md` — older governed-source intake packet.

No `permno`, ticker, legacy route contract, dashboard loader, provider-port fallback, or old readiness artifact is accepted as Alpha PIT v1 authority merely because it exists.

When `alpha_pit_data_api_v1` becomes current authority for this research lane, the System-wide Destructive Authority Replacement Law applies to any competing current research-data path: no dual reader, dual writer, fallback, alias, feature flag, or compatibility adapter.

Historical artifacts remain immutable evidence only.

## 1.1 Second-consumer / FamilyDataContract recut

The final strategic lock authorizes multiple independent Alpha-family prediction clocks and parallel evidence qualification. This does **not** justify a generic data platform.

When Family #2 actually opens, extract only the smallest shared family binding justified by real reuse:

```text
FamilyDataContract
- family_id
- risk_set_spec_id
- primary_label_spec_id
- allowed observation surface
- allowed expectation surface
- allowed claim surface
```

Inject that immutable contract into session construction, artifact manifests and outcome binding. Add cross-family artifact/label/risk-set rejection and concurrent-session isolation tests. No dynamic registry, plugin system, feature store, provider ranking or universal schema platform is authorized.

Until Family #2 exists, CRV1-specific constants remain valid v1 authority rather than being generalized speculatively.

---

# 2. Package seam

Target implementation seam after Clock #1:

```text
research/alpha_pit_v1/
  contracts.py
  session.py
  canonicalize.py
  manifests.py
  discovery_outcomes.py
  adapters/
    ciq_cycle_v1.py
    sec_claims_v1.py
```

This is **not** a provider framework.

Adapters are explicit family-needed implementations. There is no dynamic registry, plugin discovery, provider priority list, or fallback chain.

Provider-specific bytes terminate at the adapter/canonicalizer boundary. Downstream Alpha code consumes only the canonical API objects in this specification.

---

# 3. Research modes and capability firewall

```text
DISCOVERY
CONFIRMATORY
PROSPECTIVE
```

The session is mode-bound when created; callers cannot change mode per request.

Recommended constructor seam:

```python
open_alpha_pit_session(
    *,
    mode: Literal["DISCOVERY", "CONFIRMATORY", "PROSPECTIVE"],
    family_id: Literal["CYCLE_RESONANCE_v1"],
    decision_context_id: str,
) -> AlphaPITReadAPIv1 | AlphaPITDiscoveryAPIv1
```

Capability rule:

```text
DISCOVERY
→ AlphaPITDiscoveryAPIv1
→ read API + outcomes(...)

CONFIRMATORY / PROSPECTIVE
→ AlphaPITReadAPIv1 only
→ outcomes capability is absent, not merely discouraged
```

`CONFIRMATORY` and `PROSPECTIVE` code must not import `discovery_outcomes.py`.

A runtime `if mode != DISCOVERY` check is insufficient as the only protection. The outcome capability must be absent from the returned interface and excluded from the confirmatory/prospective dependency manifest.

Historical confirmatory evaluation is performed by a separate evaluator **after** prediction artifacts are immutable. The model/prediction process itself never receives future labels.

---

# 4. Canonical method signatures

## 4.1 `risk_set(as_of)`

```python
def risk_set(*, as_of: datetime) -> ArtifactRef[RiskSetPayload]: ...
```

Semantics:

- `as_of` is a timezone-aware decision knowledge cutoff;
- membership uses only information with `available_at <= as_of`;
- output uses permanent research security identity;
- current v1 permanent identity namespace is `CIQSEC:<Capital IQ Security ID>` where CIQ is the approved identity source for the slice;
- no ticker or company-entity fallback;
- risk-set membership does not require future outcome availability;
- missing optional qualitative/expectation coverage does not remove a security from the risk set;
- every exclusion is counted and reason-coded in the manifest.

Initial family risk-set spec:

```text
risk_set_spec_id = CRV1_US_PRIMARY_COMMON_V1

required at as_of:
- U.S.-listed primary common-equity security/trading identity;
- active/tradable research eligibility under the family contract;
- unique permanent security mapping;
- sufficient prior market history for the declared baseline transforms;
- no future-membership or current-survivor condition.
```

Family-specific liquidity/capacity thresholds, if introduced, must be preregistered in a new risk-set-spec version. They may not be chosen after outcome inspection.

### `RiskSetRowV1`

```text
security_id                  str  # CIQSEC:<id>
company_id                   str|null
trading_item_id              str|null
primary_listing_id           str|null
membership_effective_at      timestamp
observed_at                  timestamp
available_at                 timestamp
source_id                    str
source_receipt_sha256        sha256
identity_receipt_sha256      sha256
eligibility_status           ELIGIBLE
schema_version               alpha_pit_risk_set_row_v1
```

### `RiskSetPayload`

```text
risk_set_id                  content-addressed id
family_id                    CYCLE_RESONANCE_v1
risk_set_spec_id             CRV1_US_PRIMARY_COMMON_V1
as_of                        timestamp
rows                         sorted RiskSetRowV1[]
row_count                    int
exclusion_counts             map[reason_code,int]
coverage_summary             CoverageSummaryV1
```

`risk_set_id` binds the canonical payload bytes, family, risk-set spec, and `as_of`.

---

## 4.2 `observations(ids, fields, as_of)`

```python
def observations(
    *,
    ids: Sequence[str],
    fields: Sequence[FieldIdV1],
    as_of: datetime,
) -> ArtifactRef[ObservationPayload]: ...
```

The v1 field namespace is closed to the first consumer. New logical fields require an explicit schema-version change; providers may not inject arbitrary columns.

### `FieldIdV1`

Market state:

```text
market.close
market.total_return_1d
market.volume
market.adv20
market.realized_vol20
market.sma20
market.sma200
```

Structured company state:

```text
fund.revenue_q
fund.inventory_q
fund.capex_q
fund.gross_margin_q
fund.operating_margin_q
fund.cash_from_ops_q
```

These are canonical logical fields. Adapter-native names remain internal to adapters.

### `ObservationRowV1`

```text
security_id                  str
field_id                     FieldIdV1
value_type                   FLOAT|INT|STRING|BOOL|NULL
value                        typed|null
unit                         str|null
period_end                   date|null
effective_at                 timestamp|null
observed_at                  timestamp
available_at                 timestamp
source_id                    str
source_receipt_sha256        sha256
schema_version               alpha_pit_observation_row_v1
coverage_status              PRESENT|MISSING_HISTORY|MISSING_SOURCE|NOT_ENTITLED|NOT_APPLICABLE|STALE
missingness_reason           str|null
artifact_row_hash            sha256
```

Contract:

- `available_at > as_of` is forbidden;
- ambiguous identity is a hard error, not a missing row;
- requested `(security_id, field_id)` pairs are never silently dropped;
- each requested pair returns exactly one canonical row, including explicit missingness;
- no forward fill across a publication boundary unless the field contract explicitly defines carry-forward semantics;
- no provider fallback is permitted inside one field authority.

---

## 4.3 `source_claims(ids, as_of)`

```python
def source_claims(
    *,
    ids: Sequence[str],
    as_of: datetime,
) -> ArtifactRef[SourceClaimPayload]: ...
```

Purpose: expose source-bound atomic claims from original company/competitor public disclosures without turning AI inference into observed fact.

Initial source boundary:

```text
official public company filings / exhibits / company disclosures
first explicit adapter = SECAlphaClaimsV1
```

No generic web/news scraper is in v1.

### `ClaimTopicV1`

```text
SUPPLY_CAPACITY
INVENTORY_CHANNEL
PRICING
DEMAND
UTILIZATION
MARGIN
GUIDANCE
COMPETITION
OTHER_RELEVANT_CYCLE
```

### `SourceClaimRowV1`

```text
claim_id                     content-addressed id
security_id                  str
related_security_id          str|null
claim_topic                  ClaimTopicV1
claim_normalized             str
claim_direction              UP|DOWN|FLAT|MIXED|UNKNOWN
claim_horizon                CURRENT|NEXT_QUARTER|NEXT_YEAR|MULTIYEAR|UNKNOWN
source_document_id           str
source_document_type         str
source_locator               str  # accession/section/item/page/span locator; not a generic URL key
source_published_at          timestamp|null
source_accepted_at           timestamp|null
observed_at                  timestamp
available_at                 timestamp
source_receipt_sha256        sha256
extraction_procedure_id      str
extraction_procedure_sha256  sha256
schema_version               alpha_pit_source_claim_row_v1
epistemic_class              OBSERVED_SOURCE_CLAIM
coverage_status              PRESENT
artifact_row_hash            sha256
```

`claim_normalized` is a source-grounded canonical statement. It is not a prediction, thesis, or causal conclusion.

If an AI model is used to extract/normalize claims, its model/procedure/prompt identity is hash-bound. The raw source locator remains mandatory.

AI-generated mechanism interpretations belong in the Alpha implementation layer, not `source_claims()`.

---

## 4.4 `expectations(ids, as_of)`

```python
def expectations(
    *,
    ids: Sequence[str],
    as_of: datetime,
) -> ArtifactRef[ExpectationPayload]: ...
```

Purpose: represent what the market/consensus is believed to expect so the Alpha Family can test an expectation gap rather than company quality alone.

### `ExpectationMeasureV1`

```text
EPS_FY1
EPS_FY2
REVENUE_FY1
REVENUE_FY2
EPS_FY1_REVISION_30D
EPS_FY1_REVISION_90D
REVENUE_FY1_REVISION_30D
REVENUE_FY1_REVISION_90D
FORWARD_PE
```

### `ExpectationRowV1`

```text
expectation_id               content-addressed id
security_id                  str
measure                      ExpectationMeasureV1
value                        float|null
unit                         str|null
forecast_period_end          date|null
observed_at                  timestamp
available_at                 timestamp
source_id                    str
source_receipt_sha256        sha256
method_id                    str|null
method_sha256                sha256|null
epistemic_class              OBSERVED_CONSENSUS|INFERRED_MARKET_IMPLIED
schema_version               alpha_pit_expectation_row_v1
coverage_status              PRESENT|MISSING_HISTORY|MISSING_SOURCE|NOT_ENTITLED|NOT_APPLICABLE|STALE
missingness_reason           str|null
artifact_row_hash            sha256
```

Observed consensus and inferred market-implied expectations may coexist only when explicitly labeled. An inferred expectation may never masquerade as provider-observed consensus.

---

## 4.5 `outcomes(risk_set_id, label_spec)` — DISCOVERY ONLY

```python
def outcomes(
    *,
    risk_set_id: str,
    label_spec: RightTailLabelSpecV1,
) -> ArtifactRef[OutcomePayload]: ...
```

This method exists only on `AlphaPITDiscoveryAPIv1`.

It is absent from confirmatory/prospective sessions.

### Initial frozen primary label

```text
label_spec_id = CRV1_RIGHT_TAIL_252D_TOP5_V1
family_id = CYCLE_RESONANCE_v1
horizon = 252 trading days from the legitimate execution boundary
measure = primary-security total return
cross_section = exact risk_set_id
winner_rule = top 5% date-local cross-sectional outcome
```

Sensitivity labels may exist only as explicitly diagnostic label specs. They cannot replace the primary label after inspection without a new family/version/search-budget charge.

### `OutcomeRowV1`

```text
risk_set_id                  str
security_id                  str
label_spec_id                str
execution_boundary           timestamp
horizon_end                  date|null
realized_total_return        float|null
cross_section_percentile     float|null
winner_label                 bool|null
observed_at                  timestamp
available_at                 timestamp
source_id                    str
source_receipt_sha256        sha256
schema_version               alpha_pit_outcome_row_v1
coverage_status              PRESENT|INCOMPLETE_HORIZON|MISSING_SOURCE|DELISTING_UNRESOLVED|OTHER_MISSING
missingness_reason           str|null
artifact_row_hash            sha256
```

Outcome manifests report the complete risk-set denominator, finite-label count, missing-label count, and missingness reasons. Missing outcomes may not disappear from the denominator silently.

The label spec must freeze its minimum acceptable cross-sectional outcome coverage before confirmatory use.

---

# 5. Common content-addressed response envelope

Every method returns an `ArtifactRef` whose manifest includes:

```text
api_schema_id                alpha_pit_data_api_v1
artifact_type                RISK_SET|OBSERVATIONS|SOURCE_CLAIMS|EXPECTATIONS|OUTCOMES
family_id                    CYCLE_RESONANCE_v1
research_mode                DISCOVERY|CONFIRMATORY|PROSPECTIVE
request_canonical_json       object
request_sha256               sha256
as_of                        timestamp|null
risk_set_id                  str|null
created_at                   timestamp
source_receipts              SourceReceiptBindingV1[]
coverage_summary             CoverageSummaryV1
payload_path                 content-addressed local path
payload_sha256               sha256
manifest_sha256              sha256
schema_version               str
```

### `SourceReceiptBindingV1`

```text
source_id
provider
retrieved_at
observed_range_start
observed_range_end
raw_receipt_path
raw_receipt_sha256
parser_id
parser_sha256
license_scope
retention_class
```

### `CoverageSummaryV1`

```text
requested_security_count
returned_security_count
requested_field_count|null
present_count
missing_count
not_entitled_count
stale_count
coverage_rate
missingness_by_reason
```

All payloads use deterministic row ordering and canonical serialization before hashing.

---

# 6. Fail-closed rules

The API fails closed on:

```text
naive / timezone-less as_of
future available_at relative to as_of
ambiguous or conflicting permanent identity
source-receipt hash mismatch
payload/manifest hash mismatch
schema drift / unknown required field
provider row that cannot map to the declared canonical logical field
multiple competing authorities for one canonical field without an explicit contract
confirmatory/prospective outcome access
hidden fallback to ticker / permno / old dashboard/readiness loaders / yfinance
silent row drops
implicit missing-value imputation
provider time later than canonical build time
manifest that omits coverage/missingness
```

Provider unavailability is represented explicitly. The adapter may not silently switch sources.

---

# 7. Provider adapter boundary

Initial explicit adapters:

```text
CIQCycleV1Adapter
→ permanent identity
→ structured observations
→ consensus/estimate expectations

SECAlphaClaimsV1Adapter
→ original public filing/exhibit source receipts
→ source-bound atomic claims
```

No provider interface registry is introduced.

A future second genuine consumer may justify extraction of shared adapter primitives under the Rule of Two. Until then, adapters remain concrete and narrow.

Provider bytes are evidence, not source-code assets. Retention/redistribution constraints are manifest fields and must be enforced independently of research convenience.

---

# 8. Discovery/confirmation data-firewall tests

Required tests before `CYCLE_RESONANCE_v1` can use this API:

1. same request + same source receipts → identical payload and manifest hashes;
2. `available_at > as_of` row → hard reject;
3. ticker-only or ambiguous identity → hard reject;
4. requested missing observation → explicit missing row, never silent drop;
5. source-receipt byte/hash mutation → hard reject;
6. unknown provider field → hard reject unless canonicalizer version explicitly supports it;
7. confirmatory session object has no `outcomes` method/capability;
8. confirmatory/prospective dependency scan rejects `discovery_outcomes.py` import;
9. discovery outcome request with mismatched `risk_set_id`/family/label spec → hard reject;
10. outcome payload reports denominator and missingness exactly;
11. observed source claim cannot carry `epistemic_class=INFERRED`;
12. inferred expectation cannot carry `OBSERVED_CONSENSUS`;
13. manifest without source/license/retention metadata → hard reject;
14. no legacy readiness/API file is imported by the new package;
15. no direct provider dependency exists in `research/cycle_resonance_v1/`.

---

# 9. Non-goals

Not part of v1:

```text
generic provider framework
provider ranking / auto-fallback
feature store
web scraping platform
news platform
vector database / generic RAG
universal document intelligence
cross-family schema registry
broker/execution API
live data overlay
backward-compatibility reader
current pre-Clock CIQ admission replacement
```

---

# 10. Build order after Clock #1 — contract-first parallelism

The Alpha PIT lane and `CYCLE_RESONANCE_v1` lane may build concurrently against this already-frozen contract. CRV1 uses deterministic contract fixtures until real PIT artifacts pass the integration join; fixture success is engineering evidence only.

```text
J1 CONTRACT ALREADY FROZEN
1. contracts + session capability firewall
2. deterministic contract fixtures for risk_set / observations / expectations / source_claims / discovery outcomes

PARALLEL PRODUCER WORK
3. CIQCycleV1Adapter for exact first-family structured surfaces
4. risk_set + observations + expectations
5. SECAlphaClaimsV1Adapter + source_claims
6. discovery-only outcome capability
7. content-addressed manifests / coverage
8. failure-injection tests

PARALLEL CONSUMER WORK
CYCLE_RESONANCE_v1 may implement packet/clock/resonance/model logic against fixtures
without importing a provider or claiming real PIT integration

J3 REAL PIT INTEGRATION
9. replace fixture inputs with real content-addressed API artifacts
10. run producer/consumer closure and failure tests together
```

No consumer may bypass the API because its adapter is unfinished. Historical breadth expands only as required by the Minimum Viable Atlas. The API is not permission to reconstruct every possible source before the first prospective seal. A future fast family may require a different data grain; richer intraday/trade/quote/LOB authority remains demand-pulled by the family mechanism and may not be acquired merely because a model can consume it.

---

# 11. Acceptance state

This document is **module/API design authority only**.

```text
ACTIVE_PRODUCT_STATE = CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED
CLOCK_1_STARTED = TRUE
ALPHA_PIT_DATA_API_V1 = MECHANICS_IMPLEMENTED / CURRENT_CIQ_STRUCTURED_CUSTODY_VERIFIED / CRV1_RISK_SET_BLOCKED
CYCLE_RESONANCE_v1 = PREREGISTERED / INPUT_PACKET_AND_MANIFEST_MECHANICS_IMPLEMENTED / EMPIRICAL_CANDIDATE_NOT_FROZEN
financial_alpha_evidence = 0
LIVE = CLOSED
```

Clock #1 released implementation of this API under the post-Clock domain-WIP law. The read/session firewall and concrete first-family producer adapters are now implemented mechanically. Real current CIQ custody verifies through the adapter without being backdated into historical PIT: 109 current identities are readable, five names explicitly lack 200-day history, `fund.gross_margin_q` and `fund.cash_from_ops_q` are source-level missing for all 109, all 981 requested expectation rows are source-level missing, and SEC claims are explicitly unlanded. The AOV growth-screen 109 is forbidden as a CRV1 risk set. A future CRV1 risk-set source must bind the frozen eligibility contract, prove no growth/current-survivor/future-membership filter, and bind an independent identity receipt. No empirical CRV1 candidate or financial-alpha evidence is created until the legitimate broad risk set and remaining required source surfaces cross the deterministic join.
