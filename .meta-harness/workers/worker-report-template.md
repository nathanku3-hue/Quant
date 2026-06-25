Outcome: <DONE|PARTIAL_WITH_EXPLICIT_SCOPE|REJECTED>
Round: not recorded
Progress: not recorded
Confidence: not recorded
Worker:
Stream:
Task:
Phase:
Updated:
Ship gate tier: <FAST|REVIEW|SLOW|BLOCK>
Task resolution: <ship|blocked|decision-needed|follow-up-queued>

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

## Validation / evidence

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
ship_gate_tier: <FAST|REVIEW|SLOW|BLOCK>
task_resolution: <ship|blocked|decision-needed|follow-up-queued>

Rules:
- The first non-empty line must be Outcome: <DONE|PARTIAL_WITH_EXPLICIT_SCOPE|REJECTED>.
- The first visible fields must be Outcome, Round, Progress, and Confidence, with no title before them.
- Ship gate tier and Task resolution must appear immediately after Updated.
- The Ship-Fast Decision Gate concept is visible in top metadata and folded into What decision is needed.
- This template is an artifact, not the default final chat answer.
- Final chat answers must compress this report into Status, Why, Next, and Decision needed, at most four short lines, unless the user asks for evidence.
- Hide internal labels, hashes, absolute paths, allowlists, command logs, and accountability booleans from final chat unless the user asks for them.
- If the user asks for approval text, emit only the pasteable approval block and do not add an audit recap.
- Do not use # Worker PM Brief, # Worker Report, numbered reviewer logs, command logs, SAW internals, or ClosurePacket lines as the primary report structure.
- SAW Verdict and ClosurePacket details belong only under Validation / evidence.
- Missing requested_work_type or actual_work_type_performed fails closed.
- PARTIAL_WITH_EXPLICIT_SCOPE and REJECTED require an explicit blocker.
- actual_work_type_performed=none requires PARTIAL_WITH_EXPLICIT_SCOPE or REJECTED and an explicit blocker.
- Silent docs-only fallback from code, test, provider_probe, commit, validation, execution, or data_output work is forbidden.
