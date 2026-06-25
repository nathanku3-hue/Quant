# Product Roadmap: Discretionary Augmentation

Status: Phase 65 G7.1 product charter
Authority: D-365 Phase G7.1 roadmap realignment / product charter
Date: 2026-05-09

## Purpose

Terminal Zero is now framed as discretionary augmentation for de-risked asymmetric upside, not generic alpha search and not a trading bot.

The product mission is:

```text
90% supercycle gem discovery + 10% buying-range / hold-discipline prompting
```

The system should help a human investor:

- wait longer before entering left-side setups;
- avoid selling too early when thesis health and momentum remain constructive;
- monitor whether market behavior confirms or invalidates the thesis;
- keep all search, ranking, alerting, broker, and promotion behavior behind explicit later approvals.

## Roadmap Language

| Retired framing | Current framing |
| --- | --- |
| Alpha search | De-risked upside discovery |
| Strategy candidate | Thesis / signal candidate |
| Buy/sell signal | Decision-support state |
| Backtest result | Evidence layer |
| Alert | Buying-range / hold-discipline prompt |
| V2 discovery | Research sandbox |
| Promotion | Human-reviewed thesis approval |

These labels are product-governance language. They do not rename existing code packages during G7.1 and do not authorize implementation.

## Product Model

The cockpit serves discretionary judgment. It does not replace the human decision layer.

The primary product family becomes:

```text
SUPERCYCLE_GEM_DAILY_V0
```

`PEAD_DAILY_V0` remains valid, but it is reclassified as a tactical signal family. It is one possible evidence module inside the cockpit, not the core product family, not the dashboard mission, and not the roadmap center.

## Phase Sequence

| Phase | Scope | Boundary |
| --- | --- | --- |
| G7.1 | Roadmap realignment: discretionary augmentation + supercycle gem framing | Docs/context only |
| G7.2 | Define Supercycle Gem Family, no search | Definition only |
| G8 | Create one thesis candidate card, no search | No ranking or result selection |
| G9 | Build dashboard signal map, no alpha search | UI taxonomy only unless separately approved |
| G10 | Begin bounded discovery inside one approved family | Trial-budgeted and preregistered |
| G11 | Entry/hold discipline monitor | Decision-support state only |
| G12 | Paper-only buying-range prompts | Requires source-quality and risk controls |

## Governance Interpretation

G7.1 is product charter work. It creates no candidate, no backtest, no replay, no result artifact, no alert, no broker path, and no promotion packet.

The governance posture remains model-risk-first:

- SR 26-2, dated 2026-04-17, supersedes SR 11-7 and SR 21-8 and emphasizes risk-based model governance, documentation, validation, and controls.
- NIST data-integrity guidance supports treating dataset integrity as a first-class control before downstream use.
- Behavioral-finance references on the disposition effect support building entry discipline and hold discipline as decision-support problems, not automatic trading instructions.

## External Reference Anchors

- Federal Reserve SR 26-2: https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm
- NIST CSRC data integrity glossary: https://csrc.nist.gov/glossary/term/data_integrity
- Odean disposition-effect paper page: https://faculty.haas.berkeley.edu/odean/papers/disposition/disposition.html
- Shefrin and Statman paper reference: https://people.bath.ac.uk/mnsrf/Teaching%202011/Shefrin-Statman.pdf

## Acceptance Lock

G7.1 is valid only if:

- the roadmap states that the system is discretionary augmentation, not a trading bot;
- the 90/10 model is documented;
- `PEAD_DAILY_V0` is classified as tactical, not primary;
- `SUPERCYCLE_GEM_DAILY_V0` is named as the primary product family for the next definition phase;
- dashboard taxonomy includes entry discipline and hold discipline;
- no search, backtest, replay, ranking, alert, broker, or promotion code is added;
- G7 artifacts remain valid and untouched except for classification/context.
