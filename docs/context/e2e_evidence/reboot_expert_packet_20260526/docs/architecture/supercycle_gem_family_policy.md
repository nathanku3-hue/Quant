# Supercycle Gem Family Policy

Status: Phase 65 G7.1 product-family policy
Authority: D-365 Phase G7.1 roadmap realignment / product charter
Date: 2026-05-09

## Purpose

`SUPERCYCLE_GEM_DAILY_V0` is the primary product family for the next roadmap step. It is intended to define evidence-backed asymmetric upside thesis candidates and the decision-support states needed to monitor thesis health, entry discipline, hold discipline, flow/positioning, and regime.

G7.1 does not create this family artifact. It names and scopes the primary family so G7.2 can define it before any candidate card or discovery work.

## Family Role

```text
family_id: SUPERCYCLE_GEM_DAILY_V0
family_role: primary_product_family
current_status: planned_for_definition
```

The family should support:

- de-risked upside discovery;
- thesis evidence collection;
- entry-range discipline;
- hold-discipline monitoring;
- dashboard state mapping.

It must not support automatic trading, live orders, search-by-result, candidate ranking, or promotion without human review.

## Relationship To PEAD

`PEAD_DAILY_V0` remains valid as a G7-defined family, but its product role is tactical:

```text
PEAD_DAILY_V0 = tactical_signal_family
SUPERCYCLE_GEM_DAILY_V0 = primary_product_family
```

PEAD may later become one evidence module inside the broader cockpit. It must not become the roadmap center by inertia.

## Future G7.2 Definition Requirements

Before any Supercycle Gem thesis candidate card exists, G7.2 must define:

- family ID and version;
- research question and hypothesis;
- universe and source-quality policy;
- allowed evidence categories;
- forbidden evidence categories;
- finite parameter/state space;
- trial budget;
- validation gates;
- multiple-testing or family-accounting policy;
- promotion policy;
- dashboard state mapping;
- manifest-backed artifact and append-only/versioned behavior.

## Provisional Evidence Dimensions

Future allowed categories may include:

- thesis-health evidence;
- entry-discipline evidence;
- hold-discipline evidence;
- flow and positioning context;
- regime context;
- source-quality and freshness metadata.

These are categories only. G7.1 does not approve specific signals, formulas, parameters, sources, or thresholds.

## Blocked Scope

- No candidate generation.
- No backtest.
- No replay.
- No V2 proxy run.
- No strategy search.
- No parameter selection from results.
- No alpha/performance/ranking metrics.
- No buying-range prompt emission.
- No alert, notifier, OpenClaw, Alpaca, BrokerPort, or broker call.
- No promotion packet.

## Acceptance Lock

`SUPERCYCLE_GEM_DAILY_V0` may become executable only after a later phase publishes a manifest-backed family definition and passes review. Until then, it is a roadmap label and product-family contract target only.
