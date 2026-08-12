# Outcome-First Ship-Fast Decision Gate

Status: Meta-Harness 0.4 distributable contract
Scope: planner and artifact behavior.

## Truth precedence

Read and reconcile in this order:

1. locked product intent and explicit owner authority;
2. immutable product, mechanics, package, proof, publication, and closure evidence;
3. Git facts;
4. status, roadmap prose, worker reports, and summaries.

Lower-precedence text cannot create a slice, reopen a passed gate, or weaken owner-authorized acceptance.

## Select the nearest product action

Before planning, state:

```text
Product result: <observable user outcome>
Current journey state: <not run|partially run|complete>
Primary action: <one nearest action>
Decision to change: <exact decision this work can change>
Pass route: <legal next state/action>
Fail route: <legal next state/action>
Unresolved route: <legal next state/action>
Cheapest discriminating test: <test>
Why no cheaper test exists: <one line>
```

### Result-first killer rule

If PASS / FAIL / UNRESOLVED all lead to the same next action, return `NO_BUILD` / `DO_NOT_RUN`. Completing a deliverable is not a result unless it changes a route. Receipt/terminal shape should be known before substantial engineering.

When the complete user journey has not run, permit at most one pre-execution audit/repair round, then execute the journey now **only when the next forward gate is authorized and decision-useful**. Do not split implementation, validation, integration, packaging, review, or closure into successor product slices merely because they are separate lifecycle stages. Phase or gate completion never self-authorizes a later outcome-bearing or capital-bearing action.

## Blocking test

A finding blocks only when retained evidence demonstrates one of:

- journey prevention;
- material conclusion invalidation;
- credible irreversible loss;
- supported-platform unusability.

Preferences, optional improvements, stale status, extra review, cleanliness that does not threaten the authorized journey, and unchanged passed gates are non-blocking. Keep them as residue without delaying the primary action.

## Evidence reuse

Reuse a passed gate when none of its declared input bytes changed. Rerun only the affected gate unless new concrete evidence demonstrates a product-relevant defect. Reviewer preference alone is insufficient.

## Terminal continuation

When shipping is complete, value is confirmed, maintenance is active, or no active slice exists:

- default: `NO_BUILD` and `USE_PRODUCT`;
- explicit owner scope change: `OWNER_DECISION_REQUIRED` and `REQUEST_OWNER_AUTHORIZATION`;
- complete observed supported-use defect warrant: `BUILD_RECOMMENDED` and `SELECT_SMALLEST_REPAIR`.

A defect warrant must name the observed behavior, supported environment, user impact, retained evidence, and smallest repair. Incomplete warrants return `NO_BUILD`. Never claim post-closure successor activation, queue a follow-up after `NO_BUILD`, or invent a new review/evidence gate.

## Output

Return the primary action first, followed only by demonstrated blockers and one executable next step. Status and audit detail are supporting evidence, not the work.
