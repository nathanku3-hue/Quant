# GodView Build-vs-Borrow Decision

Status: Phase 65 G7.1C decision memo; audit wait
Date: 2026-05-09
Authority: planning only; no implementation approval

## Decision

Do not copy one open-source quant repo as the GodView data layer.

Build Terminal Zero provider ports and local governance around the existing canonical lake. Borrow architecture patterns from open-source projects, but keep source truth, observed/estimated/inferred policy, manifests, and state-machine inputs under Terminal Zero control.

## Build, Borrow, Or Defer

| Module | Best pattern | Decision |
| --- | --- | --- |
| Provider abstraction | OpenBB-style | Build our own provider ports after audit. |
| Canonical research data | LEAN/Qlib-style local data discipline | Keep existing Tier 0 lake and manifests. |
| Yahoo/public convenience | yfinance/vectorbt/FinRL pattern | Keep Tier 2 only; not canonical. |
| Options/IV/whales | OPRA/vendor/ORATS/ThetaData/Massive/OpenBB provider route | Defer until provider/license decision. |
| SEC filings | Direct SEC API/wrappers | Best early no-cost candidate after audit. |
| Short interest | FINRA public/API | Best early no-cost candidate after audit. |
| CFTC positioning | CFTC public/Socrata | Good early no-cost candidate after audit. |
| ETF/passive flows | Vendor/issuer/OpenBB provider | Needs source selection. |
| Dark pool/block | FINRA + vendor | Later; accumulation must be estimated/inferred. |
| Microstructure | TotalView/TAQ | Later; paid/licensed. |
| Crypto connectors | CCXT/Freqtrade/Hummingbot | Defer; not current product. |

## Immediate No-Cost Implementation Plan - Held For Audit

This plan is intentionally implementation-ready in shape, but not authorized for execution.

### Stage 1 - Source Audit

Artifact:

- audit notes for SEC, FINRA, CFTC, and macro/context sources;
- source terms and cost classification;
- as-of and freshness semantics;
- allowed/forbidden use.

Done when:

- every P1 source has a current official URL, terms/cost note, freshness note, raw locator, and observed/estimated/inferred classification.

### Stage 2 - Source Policy

Artifact:

- provider-specific source policy docs for SEC, FINRA, and CFTC;
- source-quality eligibility;
- source label rules;
- manifest fields.

Done when:

- policy states exactly what the source may and may not power.

### Stage 3 - Tiny Fixture Design

Artifact:

- fixture schema plan for one SEC filing dataset, one FINRA dataset, and one CFTC dataset;
- key fields, date fields, row-count sanity, duplicate checks, and raw locator rules.

Done when:

- no fixture is downloaded or generated yet, but every fixture has deterministic acceptance checks.

### Stage 4 - Adapter Proof After Explicit Approval

Artifact:

- one provider;
- one dataset;
- one tiny fixture;
- manifest/provenance proof;
- no dashboard runtime behavior.

Done when:

- source audit passes;
- explicit approval is recorded;
- adapter remains blocked from ranking, alerts, broker calls, and candidate generation.

## Recommended Next Decision

Given the user instruction to wait for audit:

```text
hold_g7_2_and_run_g7_1c_source_audit
```

G7.2 can still be the later state-machine phase, but it should consume only constraints that have survived source audit. G7.2 must not assume options, IV, gamma, whale, dark-pool, microstructure, SEC, FINRA, or CFTC signals are implemented.

## Rollback Note

If rejected, remove only G7.1C research/architecture/planning docs and related context/handover/SAW updates. Do not revert G7.1B source matrix, G7.1A product canon, G7 family artifacts, dashboard drift fix, or prior phase work.

