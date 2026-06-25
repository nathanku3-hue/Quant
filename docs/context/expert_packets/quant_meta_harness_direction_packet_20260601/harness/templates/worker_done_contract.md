# Worker Done Contract

Status: Template
Purpose: capture worker proof before handoff or reconciliation.

## Identity

```text
RoundID: <round-id>
ScopeID: <scope-id>
WorkerID: <worker-id>
Stream: <Backend|Frontend/UI|Data|Docs/Ops|Other>
Owner: <name or role>
Date: <YYYY-MM-DD>
```

## Scope

```text
URL: <http://... or N/A with reason>
Route/Page: <route, page, Streamlit view, or artifact surface>
WhatToAudit: <specific behavior, contract, or document surface>
FilesChanged:
- <path>
```

## Proof

```text
ScreenshotOrAppTestProof: <screenshot path, AppTest name, or N/A with reason>
TestsRun:
- <command> -> <PASS|FAIL|NOT_RUN> <summary>
KnownLimits:
- <limit, blocked item, or none>
```

## Handoff

```text
WorkerVerdict: <PASS|BLOCK>
OpenQuestions:
- <question or none>
NextOwner: <orchestrator|reviewer|stream owner>
```

Rule: if URL, Route/Page, WhatToAudit, proof, tests, known limits, or files changed are missing, WorkerVerdict must be BLOCK.
