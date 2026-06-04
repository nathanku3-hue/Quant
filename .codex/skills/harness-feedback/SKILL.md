---
name: harness-feedback
description: Record tiny SAW feedback only for repeated execution friction. Use after a SAW or harness round when the same blocker, reviewer miss, validation gap, or workflow drag recurs.
---

# Harness Feedback Skill

Use this skill to capture repeated friction without turning every round into process work.

## Trigger
Emit feedback only when the same friction appears at least twice in the same milestone/session or blocks closure once after a prior guardrail already existed.

## Tiny Feedback Block
Append or report this block where the parent round asks for SAW feedback:

```text
Harness Feedback:
- Friction: <repeated blocker or drag>
- Root Cause: <one line>
- Guardrail: <one next-time rule>
- Evidence: <path or command>
```

## Rules
1. Do not emit feedback for one-off noise.
2. Do not create new process docs from this skill alone.
3. Keep the block to four bullets.
4. If the friction is Critical/High and unresolved, surface it as a SAW finding instead of only feedback.
5. If no repeated friction exists, output `Harness Feedback: none`.
