# G8.2 System-Scouted Candidate Card Policy

Status: G8.2 candidate-card-only
Authority: Phase 65 G8.2, one governed `LOCAL_FACTOR_SCOUT` item
Date: 2026-05-10

## Purpose

G8.2 proves that a governed system-scouted intake item can become a structured research object without becoming validated alpha, a rank, a score, a buying range, an alert, or a dashboard action.

The only approved source intake item is:

```text
data/discovery/local_factor_scout_output_tiny_v0.json -> MSFT
```

No other ticker is eligible in G8.2 because `MSFT` is the sole governed `LOCAL_FACTOR_SCOUT` output from G8.1B.

## Scope

Approved:

- create one `MSFT` candidate card;
- reuse the existing candidate-card schema and validator;
- reference the existing scout output and manifest;
- add light official/public evidence pointers for research orientation only;
- record missing evidence, thesis breakers, provider gaps, and forbidden state jumps;
- validate no factor score, rank, buy/sell/hold output, validation claim, actionability, buying range, alert, broker action, provider ingestion, or dashboard runtime behavior.

Blocked:

- new scout output;
- cards for `DELL`, `AMD`, `LRCX`, `ALB`, or any other ticker;
- factor score display;
- candidate ranking;
- thesis validation;
- buying range;
- dashboard merge;
- runtime page content changes;
- provider ingestion;
- alert or broker behavior.

## Required Artifact Contract

```text
data/candidate_cards/MSFT_supercycle_candidate_card_v0.json
data/candidate_cards/MSFT_supercycle_candidate_card_v0.manifest.json
```

The card must include:

- `ticker = MSFT`;
- `candidate_status = candidate_card_only`;
- `discovery_origin = LOCAL_FACTOR_SCOUT`;
- `scout_model_id = LOCAL_FACTOR_EQUAL_WEIGHT_V0`;
- `source_intake_item_id`;
- `source_intake_manifest_uri`;
- `candidate_card_manifest_uri`;
- `governance.not_validated = true`;
- `governance.not_actionable = true`;
- `governance.no_score = true`;
- `governance.no_rank = true`;
- `governance.no_buy_sell_signal = true`;
- `governance.no_alert = true`;
- `governance.no_broker_action = true`.

## Dashboard Boundary

The existing dashboard may already show `MSFT` in legacy ticker-list or scan rows.

That runtime row is not the G8.2 candidate card.

G8.2 does not merge the card into the dashboard. A future approved dashboard lane should read candidate cards as status objects only, with labels such as:

```text
MSFT | LOCAL_FACTOR_SCOUT | candidate_card_only | THESIS_CANDIDATE | evidence missing
```

It must not combine the G8.2 card with legacy action-shaped labels such as tactical entry price, target price, `COILED SPRING`, `IGNORE`, score, rank, buy/sell/hold, alert, or broker action.

## Evidence Pointer Policy

Allowed official/public evidence pointers are used lightly:

- Microsoft annual report / investor materials for AI and cloud infrastructure context;
- Microsoft public blog context for AI-enabled datacenter investment;
- SEC Form 13F FAQ for delayed ownership-filing timing.

These sources do not validate the thesis. They only define later evidence categories and timing constraints.

## Closure Rule

G8.2 is complete only when focused tests prove:

- the card points to the existing `MSFT` scout item;
- the card ticker matches the scout output;
- the scout output still contains only `MSFT`;
- exactly two candidate cards exist: `MU` and `MSFT`;
- no score, rank, factor score, buy/sell/hold, buying range, alert, broker action, validation, or actionability field leaks through.
