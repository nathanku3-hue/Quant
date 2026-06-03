# Worker PM Brief

Outcome: <DONE|PARTIAL_WITH_EXPLICIT_SCOPE|REJECTED>
Round:
Progress: <before>/100 -> <after>/100
Confidence: <0-10>/10
Worker:
Stream:
Task:
Phase:

## What I did

<One paragraph answering what actually changed, what artifact/result was produced, and practical effect.>

## PM-facing status

<One short paragraph: current top-level state, unblocked/blocked state, and whether execution-ready, docs-only, design-only, or rejected.>

## Ship-Fast Decision Gate

What is done:
What is blocked:
User order interpreted as:
Recommended next step:
Why this is correct:
Alternatives considered:
Decision needed from user: <approve|redirect|hold>
Scope limit:
Stop rule:

## Key decisions made

- <decision or none>

## Validation / evidence

Passed:

Skipped:

Evidence artifacts:

## What is still blocked

<blocker + exact reason, or none>

## Next round recommendation

Recommended next round:
Goal:
Allowed scope:
Forbidden scope:

## Worker accountability

requested_work_type: <docs|code|test|provider_probe|commit|validation|execution|data_output>
actual_work_type_performed: <docs|code|test|provider_probe|commit|validation|execution|data_output|none>
credentials_touched: false
provider_access_touched: false
data_output_created: false
commit_created: false
remaining_blocker:

Rules:
- The report must begin with the Ship-Fast PM Brief fields: Outcome, Round, Progress, Confidence.
- Do not use # Worker Report, numbered reviewer logs, command logs, SAW internals, or ClosurePacket lines as the primary report structure.
- SAW Verdict and ClosurePacket details belong only under Validation / evidence.
- Silent docs-only fallback from code, test, provider_probe, commit, validation, execution, or data_output work is forbidden.
