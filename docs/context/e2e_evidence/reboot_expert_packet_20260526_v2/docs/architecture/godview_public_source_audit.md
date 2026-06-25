# GodView Public Source Audit

Status: Phase 65 G7.1C source audit complete
Date: 2026-05-09
Authority: source-rights and availability audit only; no ingestion approval
RoundID: PH65_G7_1C_PUBLIC_SOURCE_AUDIT_20260509
ScopeID: PH65_G7_1C_AUDIT_ONLY

## Purpose

Audit the first low-cost GodView public-source candidates before any provider implementation. This document verifies source availability, rights posture, freshness, identifiers, raw locators, and safe downstream use boundaries.

This audit is not provider approval. It does not authorize data download, ingestion, canonical writes, state-machine work, ranking, search, alerts, dashboard runtime behavior, broker calls, or alpha evidence.

## Sources Reviewed

Official/public sources reviewed first:

1. SEC EDGAR / data.sec.gov
2. FINRA Equity Short Interest
3. FINRA Reg SHO Daily Short Sale Volume
4. FINRA OTC / ATS Transparency
5. CFTC COT / TFF
6. FRED / ALFRED
7. Ken French Data Library

## Source Notes

### SEC EDGAR / data.sec.gov

Official docs confirm that `data.sec.gov` hosts RESTful JSON APIs for EDGAR submissions and XBRL financial-statement data, with no authentication or API keys required. The SEC API documentation says JSON structures update throughout the day as submissions are disseminated, while bulk ZIP files are recompiled nightly.

Audited fit:

- Strong fit for observed filings, submissions metadata, company facts, 13F, Form 4, and 13D/G raw locator planning.
- Companyfacts is structured XBRL financial-statement data. Ownership/activist/insider forms should be treated as filing records via submissions and EDGAR archives unless a later parser is explicitly approved.
- Entity key is CIK first; ticker mapping is available from SEC files but SEC warns ticker/CIK association files are periodically updated and not guaranteed for full accuracy or scope.
- Fair-access posture requires efficient scripting, declared user agent, and a maximum guideline of 10 requests per second.

Allowed audit conclusion:

```text
SEC can support GodView public-source modules after provider-specific source policy and tiny fixture approval.
```

Forbidden conclusion:

```text
SEC audit approval does not authorize SEC ingestion, filing parsing, provider code, ranking, alerts, or state-machine work.
```

### FINRA Equity Short Interest

FINRA publishes short interest reports collected from broker-dealers for exchange-listed and OTC equity securities. FINRA states short interest is a position snapshot for specific settlement dates and is not the same thing as daily short-sale volume.

Audited fit:

- Strong fit for observed short-interest context and later squeeze-base fixtures.
- Publication is delayed around the official short-interest calendar.
- Online data is public/no fee, but website terms are non-commercial and restrict bulk copying/database creation unless another FINRA term permits it.
- Query API access requires API credentials and acceptance of FINRA API terms; public/manual/download access remains separate from future API-provider implementation.

Allowed audit conclusion:

```text
FINRA short interest can support public-source GodView context after source policy and non-bulk fixture approval.
```

Forbidden conclusion:

```text
Do not call Reg SHO daily short-sale volume "short interest"; do not infer squeeze pressure as observed fact.
```

### FINRA Reg SHO Daily Short Sale Volume

FINRA daily short-sale-volume files provide aggregated short-sale volume by security for trades executed and reported to FINRA TRF/ADF/ORF facilities. FINRA posts daily files by 6:00 p.m. ET for the relevant trade date, with possible later updates.

Audited fit:

- Good fit for observed daily short-sale-volume context.
- Not consolidated with exchange data and excludes trading activity that is not publicly disseminated.
- Explicitly not equivalent to bi-monthly short-interest position information.

Allowed audit conclusion:

```text
Reg SHO daily files can support context data and data-quality checks.
```

Forbidden conclusion:

```text
Reg SHO volume must not be used as direct short-interest, squeeze, or borrow-stress evidence.
```

### FINRA OTC / ATS Transparency

FINRA publishes OTC trading information on a delayed basis for ATSs and member firms. The website/user guide says weekly and monthly data are viewable by users and include issue data, firm data, statistics, filters, and download reports.

Audited fit:

- Fit for delayed observed aggregate OTC/ATS context.
- Any "dark-pool accumulation" label is estimated, not observed, because public FINRA data is aggregate and delayed.
- Website terms and API credentials must be handled before any automated provider proof.

Allowed audit conclusion:

```text
FINRA OTC/ATS transparency can support delayed aggregate context after source policy.
```

Forbidden conclusion:

```text
Do not describe delayed aggregate OTC/ATS prints as real-time dark-pool accumulation or whale evidence.
```

### CFTC COT / TFF

CFTC publishes Commitments of Traders reports as a breakdown of Tuesday open interest for markets where enough traders meet reporting thresholds. CFTC states COT is released Fridays at 3:30 p.m. EST. Historical COT data is available on CFTC.gov, including futures-only files back to 1986, futures/options combined files back to 1995, supplemental reports back to 2006, and TFF combined reports by year from September 2009.

Audited fit:

- Strong fit for observed futures positioning and broad futures/CTA regime context.
- TFF leveraged-funds category includes hedge funds, money managers, registered CTAs, CPOs, and unregistered funds identified by CFTC.
- CFTC classifications are trader classifications, not direct equity-single-name demand.

Required CFTC rule:

```text
CFTC data may support broad regime / futures positioning.
It must not be used as direct single-name CTA buying evidence.
```

Allowed audit conclusion:

```text
CFTC COT/TFF can support broad futures positioning and regime modules after fixture/schema approval.
```

Forbidden conclusion:

```text
Do not convert COT/TFF into observed single-stock CTA pressure.
```

### FRED / ALFRED

FRED/ALFRED docs confirm REST-style web services for economic data and vintage data. FRED API Version 2 docs state that all web service requests require an API key, and the legal terms warn that many data series are third-party owned and subject to their own restrictions.

Audited fit:

- Good fit for macro liquidity, rates, credit, dollar, money supply, and revision-aware macro context.
- API key is required, so future implementation must use env-only secrets and cannot place keys in docs, fixtures, manifests, URLs, logs, or repo files.
- Series-level third-party source terms must be checked before redistribution or long-lived caching.

Allowed audit conclusion:

```text
FRED/ALFRED can support macro/regime context after key handling and series-level rights review.
```

Forbidden conclusion:

```text
Do not bulk mirror FRED or ignore third-party source restrictions.
```

### Ken French Data Library

The Ken French Data Library provides public downloadable research returns, factors, portfolios, breakpoints, details, and historical archives. The page includes TXT/CSV links and identifies the factor methodology and data-source change notes.

Audited fit:

- Good fit for public factor/regime context and factor-return fixtures.
- No API key is required for public files, but the library is copyrighted by Eugene F. Fama and Kenneth R. French; downstream use should cite source and avoid republishing full mirrors.
- The January 2025 methodology/source-format change must be carried in any later fixture metadata when U.S. factor returns cross that boundary.

Allowed audit conclusion:

```text
Ken French data can support factor/regime context after citation and tiny-fixture approval.
```

Forbidden conclusion:

```text
Do not treat factor context as thesis health, entry discipline, or single-name alpha evidence.
```

## Allowed Use Policy

```text
SEC / FINRA / CFTC / FRED / Ken French can support GodView public-source modules,
but audit approval does not authorize ingestion.

Audit now.
Tiny fixture schema later.
Provider code only after explicit approval.
```

In this G7.1C source-audit round, "schema later" means no physical fixture files, no data downloads, no data writes, and no provider implementations. The schema plan is documented separately as a design artifact only.

## Observed / Estimated / Inferred Policy

Observed in this audit:

- official SEC filings;
- official FINRA short interest;
- FINRA Reg SHO short-sale volume;
- CFTC reported positioning;
- FRED macro series;
- Ken French factor returns.

Estimated in any later derived layer:

- CTA pressure;
- squeeze pressure;
- whale intent;
- dark-pool accumulation;
- dealer/gamma pressure.

Inferred in any later product/state layer:

- thesis health;
- market regime state;
- entry discipline;
- hold discipline.

Rule:

```text
Observed source records can be stored only after explicit provider/fixture approval.
Estimated and inferred labels must never masquerade as observed facts.
```

## Explicit Out Of Scope

- OPRA/options/IV/gamma/whale flow.
- Dark pool vendor feeds.
- TotalView / TAQ.
- ETF/passive-flow vendor.
- News vendor.
- Provider implementation.
- State machine.
- Candidate generation.
- Search.
- Ranking.
- Alerts.
- Broker calls.
- Dashboard runtime changes.

## Source Evidence

- SEC EDGAR API documentation: `https://www.sec.gov/search-filings/edgar-application-programming-interfaces`
- SEC developer/fair access guidance: `https://www.sec.gov/about/developer-resources`
- SEC EDGAR access and CIK/ticker files: `https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data`
- FINRA Equity Short Interest: `https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data`
- FINRA Daily Short Sale Volume Files: `https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files`
- FINRA Short Sale Volume notes: `https://www.finra.org/finra-data/browse-catalog/short-sale-volume`
- FINRA OTC Transparency: `https://www.finra.org/filing-reporting/otc-transparency`
- FINRA Developer Query API docs: `https://developer.finra.org/products/query-api`
- FINRA website terms: `https://www.finra.org/terms-of-use`
- FINRA API terms: `https://developer.finra.org/finra-api-terms-service`
- CFTC Market Reports: `https://www.cftc.gov/MarketReports/index.htm`
- CFTC COT About: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports/index.htm`
- CFTC COT Explanatory Notes: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/ExplanatoryNotes/index.htm`
- CFTC Historical Compressed: `https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm`
- CFTC Web Policy: `https://www.cftc.gov/WebPolicy/index.htm`
- FRED API docs: `https://fred.stlouisfed.org/docs/api/fred/`
- FRED API key docs: `https://fred.stlouisfed.org/docs/api/fred/v2/api_key.html`
- FRED legal terms: `https://fred.stlouisfed.org/legal/terms/`
- Ken French Data Library: `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html`

## Audit Verdict

G7.1C source audit passes as a documentation and rights/availability audit. The no-cost public path remains plausible, but only as a future, explicitly approved provider/fixture sequence.

Next action:

```text
approve_g7_1d_one_tiny_public_provider_fixture_or_hold
```

