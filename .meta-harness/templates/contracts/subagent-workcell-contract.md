# Subagent Workcell Contract

Status: Template
Purpose: delegate bounded noisy work to subagents without leaking context, secrets, raw logs, or broad repo state.

## Packet Shape

```json
{
  "goal": "Implement Dirty Work Autopilot v0",
  "decision_to_change": "<exact route/decision this work can change>",
  "pass_route": "<legal next state/action>",
  "fail_route": "<legal next state/action>",
  "unresolved_route": "<legal next state/action>",
  "cheapest_discriminating_test": "<test>",
  "why_no_cheaper_test_exists": "<one line>",
  "owned_paths": [
    "bin/meta-harness.js",
    "templates/skills/dirty-work-autopilot.md",
    "tests/meta-harness-cli.test.js"
  ],
  "forbidden_paths": [
    ".env",
    "provider-config/*",
    "user-worktree/*"
  ],
  "required_evidence": [
    "dirty state snapshot",
    "scope diff gate result",
    "test output",
    "PM brief"
  ],
  "stop_rule": "Stop if outside-scope or credential/provider/runtime dirt appears.",
  "return_schema": "PM brief + artifact paths + decision inbox entries only."
}
```

## Fanout Budget

- Default fanout budget is 2 subagents.
- Use 3 subagents only when the user explicitly asks.
- Invoke no broad expert board by default.

## Work Routing

- Reject the workcell before execution when PASS / FAIL / UNRESOLVED all route to the same next action.
- Prefer receipt-first work: terminal routes and required evidence are fixed before substantial implementation.
- Use subagents for read-heavy exploration, tests, logs, triage, and evidence collection.
- Avoid parallel write-heavy work unless owned paths are disjoint.
- Stop if a subagent needs outside-scope paths, credentials, provider access, runtime data, governed data, or broad repo dumps.

## Return Rule

Return only:
- PM brief;
- artifact paths;
- evidence hashes;
- decision inbox entries.

Exclude:
- raw chat logs;
- raw command logs unless promoted as a named evidence artifact;
- broad repo dumps;
- repeated context handovers;
- subagent private reasoning or conversation transcripts.
