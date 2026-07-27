# Operator Instructions — One-Case Evidence-Gap Triage

Observation class: `EVIDENCE_GAP_TRIAGE_ONLY`.

This is not a test of full E0 economics, investment value, portfolio value, or alpha. The task is to choose the next research action and explain which evidence gaps, contradictions, falsifiers, and claim boundaries matter.

## Eligibility

Before any evidence is shown, the operator must separately attest all of the following:

- no prior exposure to the Alpha claim, adjudication, result, or selected action;
- no participation in Alpha implementation, dogfood, audit, or review;
- no material MU/NVDA information after the frozen cutoff;
- no current-price or subsequent-event use;
- no outside research during either arm;
- no access to the answer-free projection before the baseline is sealed.

Any false or uncertain answer blocks eligibility. The current project owner and prior Alpha auditors are therefore not eligible operators.

## Identity evidence

Use the frozen `OPENSSH_SSHSIG_V1` adapter. The operator credential signs the role-specific session challenge. A separately pinned issuer must sign the verified-human-subject/credential binding at `IN_PERSON_OR_LIVE_VIDEO_GOVERNMENT_ID_MATCH` level. A username, GitHub account, email address, or unequal principal string is insufficient.

## Arm procedure

Each arm has an equal **maximum** budget of 60 minutes. Early submission is allowed. Actual elapsed times may differ and are not an endpoint; no latency improvement may be inferred.

For each arm submit:

- `current_research_action`: `ADVANCE_TO_FULL_RESEARCH`, `HOLD_FOR_EVIDENCE`, or `REJECT_THESIS`;
- rationale;
- indispensable missing evidence;
- falsifiers or contradictions;
- supply/demand/business/shareholder/valuation claim-separation statements;
- cited neutral source locator IDs.

The baseline receives only the sealed admissible-evidence bundle. The post arm receives exactly the same evidence bytes plus the answer-free projection.

## One-shot boundary

A technical or availability abort before `BASELINE_OPEN`, with no evidence or projection exposure, is a non-consuming `PRE_EXPOSURE_ABORT`. `BASELINE_OPEN` irrevocably consumes the one-shot authorization. Any later withdrawal, timeout, contamination, identity failure, protocol violation, or incomplete submission is retained as a terminal ineligible consumed run. There is no replacement run on the same case.

Do not use current prices, subsequent events, outside research, prior Alpha outputs, portfolio actions, or certification outputs.
