# Stream Contract

Status: Template
Purpose: define a bounded stream before parallel or delegated work begins.

## Contract

```text
RoundID: <round-id>
ScopeID: <scope-id>
StreamID: <optional stable stream id or N/A>
Stream: <Backend|Frontend/UI|Data|Docs/Ops|Other>
Goal: <one-line outcome>
Owner: <worker/subagent/role>
OwnedFiles:
- <path>
BlockedFiles:
- <path or none>
Dependencies:
- <stream/file/decision or none>
AcceptanceChecks:
- <check id>: <command, proof, or review condition>
DemoTarget: <URL, route/page, artifact path, AppTest, or N/A with reason>
StopRules:
- <condition that requires stop/handoff>
```

## Boundary

```text
AllowedChanges: <files and behavior inside scope>
ForbiddenChanges: <files, actions, or claims outside scope>
HandoffTo: <orchestrator|stream owner|reviewer>
RollbackNote: <how to revert or quarantine this stream's work>
```

Rule: if owned_files overlap blocked_files or another active stream, stop and escalate before editing.
