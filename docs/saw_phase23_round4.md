SAW Round Report

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Data, Strategy, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase23-brief.md

RoundID: R23_D1_20260222_R4
ScopeID: phase23_step2_1_tolerance_gate
Scope: Enforce strict 14-day asof tolerance in SDM assembler and publish tolerance-null warning telemetry.

Acceptance Checks
- CHK-01: Replace configurable tolerance with strict `14d` for macro asof join -> PASS
- CHK-02: Replace configurable tolerance with strict `14d` for FF asof join -> PASS
- CHK-03: Add explicit warning count for rows nulled due to tolerance -> PASS
- CHK-04: Add/adjust tests for strict tolerance behavior and stale-null counting -> PASS
- CHK-05: Run targeted pytest and dry-run/write verification -> PASS
- CHK-06: Docs-as-code updates for runbook/notes/decision/lessons/phase brief -> PASS

Ownership Check
- Implementer: Codex-main
- Reviewer A: explorer `019c84c6-af77-74a2-a82d-c4044fb6bb21`
- Reviewer B: explorer `019c84c6-af8a-7070-b7ab-59d73a903b4b`
- Reviewer C: explorer `019c84c6-af9f-7941-a2ca-2d7a66953d9d`
- Independence check: PASS

Findings Table
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Info | Need explicit stale-null telemetry per run | Added `_count_rows_nulled_by_tolerance` and warning logger with macro/FF counts | Codex-main | Resolved |
| Info | Prior assembler CLI docs still referenced `--tolerance-days` | Updated runbook and brief commands for fixed tolerance mode | Codex-main | Resolved |
| Info | Runtime feed horizons still create nulls even with strict gate | Kept as open operational risk with explicit warning counts | Data Ops | Open |

Scope Split Summary
- in-scope: all implementation checks for strict tolerance and warning telemetry are complete and verified.
- inherited: none.

Document Changes Showing
| Path | Change Summary | Reviewer Status |
|---|---|---|
| scripts/assemble_sdm_features.py | Fixed tolerance to 14d; added stale-null audit counter and warning telemetry; removed tolerance CLI override | Reviewed |
| tests/test_assemble_sdm_features.py | Updated tests for fixed tolerance path and stale-null counter behavior | Reviewed |
| docs/runbook_ops.md | Updated assembler commands to fixed-tolerance CLI | Reviewed |
| docs/phase_brief/phase23-brief.md | Updated tolerance references and assembler command evidence | Reviewed |
| docs/notes.md | Updated explicit formula section for strict `14d` tolerance + nulling audit math | Reviewed |
| docs/decision log.md | Added D-109 decision entry for strict feed-horizon gate | Reviewed |
| docs/lessonss.md | Added lesson entry for tolerance-policy hard lock and telemetry guardrail | Reviewed |

Open Risks:
- Upstream feed horizons remain capped in current environment (`frb` through 2025-02-13, `ff` through 2025-12-31), so newer fundamentals rows still null under strict tolerance by design.

Next action:
- Proceed to Action 2 planning and user review before changing BGM geometry.

SAW Verdict: PASS
ClosurePacket: RoundID=R23_D1_20260222_R4; ScopeID=phase23_step2_1_tolerance_gate; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=Upstream macro/factor feed horizons remain capped and produce expected nulls under 14d gate; NextAction=Proceed to Action 2 implementation plan review before any BGM geometry change
ClosureValidation: PASS
SAWBlockValidation: PASS
