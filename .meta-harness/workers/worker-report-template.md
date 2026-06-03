Outcome: <DONE|PARTIAL_WITH_EXPLICIT_SCOPE|REJECTED>
Round:
Progress: <before>/100 -> <after>/100
Confidence: <0-10>/10
Worker:
Stream:
Task:
Phase:

## What changed

<One paragraph answering what actually changed, what artifact/result was produced, and practical effect.>

## Why it matters

<One short paragraph: current top-level state, unblocked/blocked state, and whether execution-ready, docs-only, design-only, or rejected.>

## What is blocked

<blocker + exact reason, or none>

## What decision is needed

Decision needed from user: <approve|redirect|hold>
Options considered:
Scope limit:
Stop rule:

## Next action

Recommended next action:
Goal:
Allowed scope:
Forbidden scope:

## Evidence

Passed:

Skipped:

Evidence artifacts:

## Accountability

requested_work_type: <docs|code|test|provider_probe|commit|validation|execution|data_output>
actual_work_type_performed: <docs|code|test|provider_probe|commit|validation|execution|data_output|none>
credentials_touched: false
provider_access_touched: false
data_output_created: false
commit_created: false
remaining_blocker:

Rules:
- The first non-empty line must be Outcome, followed by Round, Progress, and Confidence.
- The Ship-Fast Decision Gate concept is folded into What decision is needed.
- Do not add any title before Outcome, and do not use # Worker Report, numbered reviewer logs, command logs, SAW internals, or ClosurePacket lines as the primary report structure.
- SAW Verdict and ClosurePacket details belong only under Evidence.
- Silent docs-only fallback from code, test, provider_probe, commit, validation, execution, or data_output work is forbidden.
