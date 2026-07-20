# Terminal SAW — E0B-DV1 Candidate Custody

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend/Product, Runtime/Ops, Data Integrity, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/gv-e0b-dv1-contradiction-brief.md

RoundID: `ROUND-20260721-E0B-DV1-CANDIDATE-TERMINAL`
ScopeID: `GV_E0B_DV1_CANDIDATE_CUSTODY_AND_RECOVERY`

## Scope and Ownership

Close the bounded E0B-DV1 code/custody candidate above hosted C0 without executing the separate real-human G08 experiment.

- Implementer: primary Codex agent.
- Reviewer A: strategy correctness and regression risk, distinct read-only agent.
- Reviewer B: runtime and operational resilience, distinct read-only agent.
- Reviewer C: data integrity and custody path, distinct read-only agent.
- Ownership check: PASS; implementer and A/B/C were distinct.

## Acceptance Checks

- CHK-01: exact committed candidate, tree, parent lineage, clean worktree, and live remote equality.
- CHK-02: SESSION_OPEN manifest/event/index/checkpoint interruption replay through core and CLI without duplicate authority.
- CHK-03: ACTIVE first-stage recovery before/after event persistence routes by checkpoint state.
- CHK-04: every mutating runner path checks sealed commit/tree/freeze; authoring descriptors use an exact field set.
- CHK-05: immutable local focused/product/protocol/combined, AppTest, context, freeze, and diff checks pass without HEAD/tree movement.
- CHK-06: hosted Ubuntu, Windows, and byte-parity workflow passes on the exact candidate.
- CHK-07: distinct Reviewer A/B/C return PASS with no unresolved Critical/High findings.
- CHK-08: current truth, generated context, reviewer artifacts, closure packet, and SAW report blocks validate.

## Evidence

- Code pin: `43dce24f806908f1a80f017f9d9b4125d908eb54`; tree: `9db1243e110015082216a7fa31fd56616c383d97`; C0 ancestor: `b7a24d3da65f78c673f7e08b5f719603f404282e`.
- Local: focused 98/98; product 191/191; frozen protocol 137/137; combined 329/329; E0B AppTest 2/2; context validation PASS; enforced freeze PASS; diff-check PASS.
- Hosted: [GV-FS0 Product run 29777518085](https://github.com/nathanku3-hue/Quant/actions/runs/29777518085) — Ubuntu PASS, Windows PASS, exact byte parity PASS.
- Review: A PASS, B PASS, C PASS; no final Critical/High/Medium findings.

## Findings Table

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High (closed) | Interrupted initialization could strand the session or duplicate authority. | Idempotent event/index/checkpoint reconstruction plus four-boundary CLI replay matrix. | Backend/Ops | Closed |
| High (closed) | Post-open mutations could retain stale source identity. | Revalidate commit/tree/freeze before every mutating command, including all recovery branches. | Runtime/Ops | Closed |
| High (closed) | One-event ACTIVE first-stage recovery was misrouted as SESSION_OPEN. | Route using checkpoint operation/state; add before/after-event recovery tests. | Runtime/Ops | Closed |
| Medium (closed) | Manifest template descriptors accepted extra fields. | Require the exact six-field descriptor set. | Data Integrity | Closed |
| Medium (closed) | Current truth cited mutable donor state and obsolete counts. | Reconcile live truth and regenerate context from the terminal candidate. | Docs/Ops | Closed |

## Scope Split Summary

- in-scope: exact candidate custody, initialization/recovery resilience, source identity, descriptor integrity, product/protocol/AppTest validation, hosted parity, independent review, and current-truth closure.
- inherited out-of-scope: real two-human G08, publication/result evidence, observed count 0→1, value disposition, merge, score/stage uplift, providers, FS1, PEAD, broker, alpha, and V2-B0 implementation.

## Document Changes Showing

- `docs/phase_brief/gv-e0b-dv1-contradiction-brief.md`: terminal candidate pin/evidence and real-G08 boundary.
- `docs/context/*_current.md`: candidate, hosted, review, counts, and next-gate truth.
- `docs/notes.md`: recovery invariants.
- `docs/lessonss.md`: authority-state recovery lesson.
- `docs/decision log.md`: terminal candidate decision and scope ceiling.
- `docs/saw_reports/reviewer_*_gv_e0b_dv1_candidate_43dce24_20260721.md`: independent review evidence.
- `docs/saw_reports/saw_gv_e0b_dv1_candidate_terminal_20260721.md`: this closure report.

## Document Sorting

GitHub order: architecture/phase brief; current context; notes; lessons; decision log; reviewer evidence; terminal SAW.

## Open Risks:

- Real G08 has not run; observed comparison count remains 0 and S-009X product PASS is not earned.
- GitHub Actions emits non-blocking Node 20 deprecation and checkout cleanup annotations while all jobs remain successful.

## Next action:

Prepare a fresh clean checkout of exact hosted-green code pin `43dce24`, then execute one real G08 with one operator and one different blinded reviewer; publish and retain either disposition without rerunning for sign.

ChecksTotal: 8
ChecksPassed: 8
ChecksFailed: 0

ClosurePacket: RoundID=ROUND-20260721-E0B-DV1-CANDIDATE-TERMINAL; ScopeID=GV_E0B_DV1_CANDIDATE_CUSTODY_AND_RECOVERY; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=real-g08-pending,node20-actions-annotation; NextAction=fresh-clean-43dce24-real-g08-human-handoff

ClosureValidation: PASS
SAWBlockValidation: PASS
