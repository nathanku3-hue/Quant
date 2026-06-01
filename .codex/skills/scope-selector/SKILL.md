---
name: scope-selector
description: Choose one bounded repo scope from current truth surfaces before execution. Use when a round has multiple plausible next steps, unclear ownership, handoff risk, or budget pressure.
---

# Scope Selector Skill

Use this skill to select one execution scope before planning or editing.

This repo-local adapter preserves Quant's mandatory `docs/context` entry sequence. The generic meta-harness template is installed under `.meta-harness/templates/skills/scope-selector.md` for reference, but this active skill is the Quant authority.

## Inputs
1. Load current truth in this order:
   - `docs/context/planner_packet_current.md`
   - `docs/context/impact_packet_current.md`
   - `docs/context/bridge_contract_current.md`
   - `docs/context/done_checklist_current.md`
2. Read wider briefs or `.meta-harness/status.md` only when those files conflict or do not name the bottleneck.

## Output Contract
Emit exactly these fields:

```text
Chosen Scope: <one bounded scope>
Why Now: <one line>
Why Not Alternatives: <one line per rejected alternative>
Low-Confidence Items: <item or none>
Out-of-Boundary Items: <item or none>
Stop Rules: <conditions that halt execution>
Demo Target: <smallest proof target>
File Budget: <max files and owned paths/categories>
```

## Selection Rules
1. Prefer the smallest scope that unlocks the active bottleneck.
2. Preserve current `DO_NOT_REDECIDE` boundaries.
3. Do not pick a scope that requires unapproved provider ingestion, canonical data writes, boot-readiness claims, ranking/scoring, alerts, broker paths, or product-authority expansion.
4. If no safe bounded scope exists, output `Chosen Scope: BLOCKED` and name the missing approval or evidence.

## Stop Rules
Stop before execution when:
- owned files cannot be named,
- acceptance checks cannot be named,
- required approval is absent,
- current truth surfaces disagree on the active bottleneck,
- the file budget would cross an explicit boundary.
