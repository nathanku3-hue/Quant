# Macro / Factor Context Usage Policy

Status: Phase 65 G7.1G context-use policy
Date: 2026-05-09
Authority: source-labeling and usage policy only; no score or runtime behavior

## Purpose

This policy locks how macro and factor fixtures may be described after G7.1G.

Macro and factor data may improve the future GodView context surface, but static fixture proof does not create a macro score, factor score, candidate ranker, alert, state-machine input, or trading action.

## Allowed Context

Allowed:

- liquidity / money-supply context from FRED series such as `M2SL`;
- rates / yield context from FRED series such as `DGS10`;
- credit-spread context from FRED series such as `BAA10Y`;
- factor-return / benchmark context from Ken French factors such as `Mkt-RF`, `SMB`, and `HML`;
- future regime-panel source validation after separate approval.

## Forbidden Context

Forbidden:

- macro regime score;
- factor regime score;
- standalone alpha proof;
- signal ranking;
- buy/sell/hold state-machine input;
- candidate generation;
- alert emission;
- broker calls;
- live provider ingestion;
- API key handling.

## Labeling Rules

Use this language:

```text
Observed macro/factor context exists for the fixture rows.
```

Do not use this language:

```text
Macro regime is bullish.
Factor regime ranks candidate X above candidate Y.
This fixture proves alpha.
This fixture triggers an alert.
```

## Hindsight Guardrail

Future live FRED / ALFRED provider work must handle vintages and real-time periods before any backtest or state-machine consumption is allowed. G7.1G includes `realtime_start`, `realtime_end`, and `asof_ts` fields only as schema discipline. It does not prove live-vintage ingestion.

## Fixture-Only Rule

```text
FRED fixture = observed macro context only.
Ken French fixture = observed factor-return context only.
Neither fixture = score, rank, alert, or trade.
```
