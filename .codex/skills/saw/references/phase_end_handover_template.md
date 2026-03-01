# Phase <NN> Handover (PM-Friendly)

Date: <YYYY-MM-DD>
Phase Window: <start_date> to <end_date>
Status: <COMPLETE | ADVISORY_PASS | BLOCK>
Owner: <agent/user>

## 1) Executive Summary
- Objective completed: <one line>
- Business/user impact: <one line>
- Current readiness: <one line>

## 2) Delivered Scope vs Deferred Scope
- Delivered:
  - <item>
- Deferred:
  - <item + owner + target phase>

## 3) Derivation and Formula Register
| Formula ID | Formula | Variables | Why it matters | Source |
|---|---|---|---|---|
| F-01 | `<explicit equation>` | `<var definitions>` | `<impact>` | `<path.py:line or docs/notes.md>` |

## 4) Logic Chain
| Chain ID | Input | Transform | Decision Rule | Output |
|---|---|---|---|---|
| L-01 | `<data source>` | `<method>` | `<rule>` | `<artifact/behavior>` |

## 5) Validation Evidence Matrix
| Check ID | Command | Result | Artifact | Key Metrics |
|---|---|---|---|---|
| CHK-PH-01 | `<command>` | `<PASS/BLOCK + key numbers>` | `<path>` | `<tests passed/failed>` |
| CHK-PH-02 | `<command>` | `<PASS/BLOCK>` | `<path>` | `timeout_sec=180` |
| CHK-PH-03 | `<command>` | `<PASS/BLOCK>` | `<path>` | `<exit code + match criteria>` |
| CHK-PH-04 | `<command>` | `<PASS/BLOCK>` | `<path>` | `<row counts + freshness>` |

## 6) Open Risks / Assumptions / Rollback
- Open Risks:
  - <risk + owner + target phase>
- Assumptions:
  - <assumption>
- Rollback Note:
  - <how to revert safely>

## 6.1) Data Integrity Evidence (Required)
- Atomic write path proof:
  - `<temp path -> replace target path evidence>`
- Row-count sanity:
  - `<before count> -> <after count>`
- Runtime/performance sanity:
  - `<duration_sec and brief interpretation>`

## 7) Next Phase Roadmap
| Step | Scope | Acceptance Check | Owner |
|---|---|---|---|
| 1 | <item> | <check> | <owner> |

## 8) New Context Packet (for /new)
- What was done:
  - <bullet>
- What is locked:
  - <bullet>
- What remains:
  - <bullet>
- Next-phase roadmap summary:
  - <bullet>
- Immediate first step:
  - <bullet>

ConfirmationRequired: YES
NextPhaseApproval: PENDING
Prompt: Reply "approve next phase" to start execution.
