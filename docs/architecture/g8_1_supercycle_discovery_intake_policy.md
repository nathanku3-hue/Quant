# G8.1 Supercycle Discovery Intake Policy

Status: G8.1 intake-only contract
Authority: Phase 65 G8.1
Date: 2026-05-10

## Purpose

G8 proved that Terminal Zero can represent one human-spotted supercycle candidate, `MU`, as a structured research object.

G8.1 answers the next product question:

```text
Can the system surface plausible names the user does not already know well without claiming alpha?
```

The approved answer is a controlled discovery intake layer:

```text
Theme -> candidate universe -> candidate intake cards -> evidence needed -> missing data -> next research questions
```

G8.1A adds the required drift correction: the six-name queue is user-seeded, not pure system-scouted output. Origin labels must make that distinction explicit before any later factor scout or system scout work.

## Scope

Approved:

- define a small supercycle theme taxonomy;
- seed one static candidate intake queue with `MU`, `DELL`, `INTC`, `AMD`, `LRCX`, and `ALB`;
- mark `MU` as `candidate_card_exists`;
- mark all other names as `intake_only`;
- attach evidence requirements, source leads, thesis breakers, provider gaps, and relevant market-behavior modules;
- validate that the queue is non-ranking, non-scoring, non-promotional, and manifest-backed.
- require discovery-origin fields that distinguish user seeding, theme adjacency, supply-chain adjacency, local factor scout, and system-scouted paths.

Blocked:

- alpha search;
- candidate ranking;
- candidate scoring;
- candidate validation;
- buy/sell/hold calls;
- buying-range or winner-run state promotion;
- backtests;
- replay;
- provider ingestion;
- live scraping;
- dashboard runtime behavior;
- alerts;
- broker behavior;
- creating another full candidate card.

## Object Distinctions

| Object | Meaning | G8.1 Authority |
| --- | --- | --- |
| Candidate intake item | This name may belong in the discovery universe. | Allowed |
| Candidate card | This name has one structured thesis object. | Existing only for `MU` |
| Validated thesis | This name passed evidence gates. | Blocked |
| Buying range | This name passed thesis, behavior, and risk checks. | Blocked |

## Hard Invariants

1. Intake queue cannot rank candidates.
2. Intake queue cannot contain score fields.
3. Intake queue cannot contain buy/sell/hold calls.
4. Intake queue cannot mark any name as validated.
5. Intake queue cannot promote any name to `BUYING_RANGE` or `LET_WINNER_RUN`.
6. Intake queue cannot use yfinance as canonical evidence.
7. Intake queue must include `evidence_needed`.
8. Intake queue must include `thesis_breakers_to_check`.
9. Intake queue must include `provider_gaps`.
10. `MU` remains the only full candidate card unless a later phase approves another card.
11. Current six names cannot be labeled pure `SYSTEM_SCOUTED`.
12. `LOCAL_FACTOR_SCOUT` is defined but held until G8.1B.
13. `is_validated` and `is_actionable` must remain false for every current intake item.

## Implementation Anchors

- `opportunity_engine/discovery_intake_schema.py`
- `opportunity_engine/discovery_intake.py`
- `data/discovery/supercycle_discovery_themes_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.json`
- `data/discovery/supercycle_candidate_intake_queue_v0.manifest.json`
- `tests/test_g8_1_supercycle_discovery_intake.py`

## Next Allowed Decisions

After G8.1, the next PM choice is one of:

- `G8.2`: create one additional candidate card from the intake queue;
- `G9`: create one market-behavior signal card;
- hold.

The queue itself does not choose among those paths.
