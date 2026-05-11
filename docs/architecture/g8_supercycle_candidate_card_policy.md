# G8 Supercycle Candidate Card Policy

Status: G8 definition/evidence-card only
Authority: Phase 65 G8, one human-nominated ticker
Date: 2026-05-10

## Policy

A Supercycle Gem Candidate Card is not an investment recommendation.
It is a structured research object.

It records:
- what the thesis is,
- what evidence is present,
- what evidence is missing,
- what would break the thesis,
- which GodView signals are unavailable,
- which state transitions are forbidden.

It does not produce:
- alpha score,
- ranking,
- buying range,
- alert,
- trade,
- promotion packet.

## G8 Scope

G8 creates exactly one card: `MU_SUPERCYCLE_CANDIDATE_CARD_V0`.

The card is allowed to store:
- ticker and company identity for the nominated object;
- a thesis placeholder;
- source-quality labels;
- evidence-present and evidence-missing lists;
- state-machine mapping;
- forbidden jumps;
- provider-gap labels.

The card is forbidden from storing:
- scores or ranks;
- buy/sell signals;
- buying-range claims;
- alert or broker metadata;
- provider-ingested evidence;
- backtest, replay, or search output.

## Source Policy

Allowed source categories:
- existing static fixtures;
- official/public source notes;
- SEC fixture-style source references;
- manual research notes.

Forbidden source categories:
- live provider calls;
- new ingestion;
- yfinance as canonical evidence;
- ranked screen results;
- paid options/IV/gamma data;
- unmanifested sources.

If later web or source review is performed, it must be research capture only, not alpha evidence. Any such notes must be labeled as `observed`, `estimated`, `inferred`, `research_only`, or `not_canonical`.

## State Boundary

G8 may initialize a card only as:
- `THESIS_CANDIDATE`; or
- `EVIDENCE_BUILDING`.

G8 must not allow:
- `BUYING_RANGE`;
- `ADD_ON_SETUP`;
- `LET_WINNER_RUN`;
- `TRIM_OPTIONAL`.

Those states require future market-behavior evidence and separate approval.
