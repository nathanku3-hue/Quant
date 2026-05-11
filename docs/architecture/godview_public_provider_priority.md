# GodView Public Provider Priority

Status: Phase 65 G7.1G priority note updated after FRED / Ken French tiny fixture proof
Date: 2026-05-09
Authority: planning only; no provider implementation approval

## Priority Rule

Prefer official/public sources before paid vendors, but do not build providers until a separate approval explicitly authorizes one tiny provider proof.

```text
audit_pass != ingestion_approval
audit_pass != provider_code_approval
audit_pass != state_machine_approval
```

## Recommended Future Sequence

1. Hold G7.2.
2. G7.1D SEC one-company static fixture proof is complete.
3. G7.1E FINRA short-interest one-settlement static fixture proof is complete.
4. G7.1F CFTC COT/TFF one-report-date static fixture proof is complete.
5. G7.1G FRED / Ken French macro-factor static fixture proof is complete.
6. Next, approve G7.2 Unified Opportunity State Machine or hold.
7. Build provider proof only after source policy and fixture proof.
8. Re-run SAW and validation before any integration decision.

## Provider Priority

| Priority | Source | Why | Future proof shape | Hold conditions |
| --- | --- | --- | --- | --- |
| P1 | SEC EDGAR / data.sec.gov | No key, official, strong identifiers, clear fair-access guidance | G7.1D one CIK static companyfacts/submissions fixture complete | no SEC live provider or ingestion until approved; ownership parser scope must be explicit |
| P1 | FINRA Equity Short Interest | Official observed short-interest data, high GodView value for squeeze base | G7.1E one settlement date / three ticker static fixture complete | no FINRA live provider or ingestion until approved; Reg SHO not mixed in |
| P2 | CFTC COT / TFF | Official observed futures positioning and broad regime context | G7.1F one report date / two broad market static fixture complete | must remain broad futures/regime proxy, not single-name CTA evidence |
| P2 | FRED / ALFRED | Official macro/vintage API and strong regime context | G7.1G three-series static fixture complete | API key handling and series-level third-party rights must be solved first |
| P3 | FINRA Reg SHO Daily Short Sale Volume | Useful daily short-sale-volume context, but easily confused with short interest | One date, one market-center source, 3-10 tickers | labels must state short-sale volume, not short interest |
| P3 | FINRA OTC / ATS Transparency | Useful delayed aggregate market-structure context | One weekly/monthly report slice with issue/firm identifiers | no real-time dark-pool or whale-accumulation claims |
| P3 | Ken French Data Library | Useful public factor/regime context, no key | G7.1G one factor-dataset static fixture complete | citation/methodology boundary must be explicit |

## Why SEC Was First

SEC was the lowest operational-friction candidate because public API access requires no key and official docs define CIK/accession raw locators. FINRA short interest is high product value but has more interpretation and terms/API credential nuance, so it should follow SEC rather than precede it.

Completed:

```text
G7.1D: SEC data.sec.gov one-company tiny fixture proof.
G7.1E: FINRA short-interest one-settlement tiny fixture proof.
G7.1F: CFTC COT/TFF one-report-date tiny fixture proof.
G7.1G: FRED/Ken French macro/factor tiny fixture proof.
```

Preferred next approval candidate:

```text
G7.2: Unified Opportunity State Machine.
```

## Explicit Holds

Held until separate approval:

- SEC provider code.
- FINRA provider code.
- CFTC provider code.
- FRED provider code.
- Ken French provider code.
- Source registry implementation.
- Unified Opportunity state machine.
- Ranking/search/candidate generation.
- Alerts.
- Dashboard runtime behavior.
- Broker calls.
