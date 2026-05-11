# GodView Source Eligibility Policy

Status: Phase 65 G7.3 policy-only
Date: 2026-05-09
Authority: source eligibility and forbidden influence policy

## Purpose

Define which source classes may influence opportunity states and which cannot.

## Eligibility Rules

| Source Class | Eligibility | Action-State Influence |
| --- | --- | --- |
| `OBSERVED_OFFICIAL` | official public/agency or research-library observations with manifest | context only unless paired with canonical behavior and future approval |
| `OBSERVED_CANONICAL` | Terminal Zero canonical Tier 0 lake with manifest | may influence behavior states after source checks |
| `OBSERVED_LICENSED` | licensed provider source with feed contract and manifest | held until provider/license decision |
| `ESTIMATED_MODEL` | model or classifier output from observed inputs | confidence/context only; cannot alone create action states |
| `INFERRED_RESEARCH` | human/Codex/research synthesis | thesis/risk context only; cannot alone create action states |
| `TIER2_DISCOVERY` | yfinance/OpenBB/public-web/convenience source | cannot move toward `BUYING_RANGE` or `LET_WINNER_RUN` |
| `REJECTED` | stale, unlicensed, unmanifested, or forbidden source | no state influence |

## Public Fixture Pillars

The four official/public fixture pillars are eligible as context:

```text
SEC        -> filings / ownership / thesis evidence
FINRA      -> short-interest / squeeze-base context
CFTC       -> futures positioning / systematic-regime context
FRED/KF    -> macro / liquidity / factor-regime context
```

They are not eligible for ranking, alerts, buy/sell orders, candidate generation, source-registry implementation, provider approval, or live ingestion.

## Tier 2 / yfinance Rule

Tier 2 and yfinance may support discovery convenience in separately approved research work, but in G7.3 they cannot:

- move any state toward `BUYING_RANGE`;
- move any state toward `LET_WINNER_RUN`;
- create action-state evidence;
- replace canonical/official/licensed source labels.

## Provider-Gap Rule

Options, IV, gamma, whales, ETF/passive flow, dark-pool/block, and microstructure signals remain held until a licensed provider decision and source policy exist.

## FRED / Ken French Rule

FRED still requires API-key handling for live API use. Ken French is a public research-data source for factor returns. Both remain context-only until provider and scoring decisions are explicitly approved.
