# SAW — GV-OPERATED-ROTATION-1

Date: 2026-08-05
RoundID: `ROUND-20260805-GV-OPERATED-ROTATION-1`
ScopeID: `GV-OPERATED-ROTATION-1`
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-native-task | Domains: Product, Backend, Frontend/UI, Accounting/Replay, Docs/Ops | FallbackSource: sealed task brief + AGENTS.md

## Scope

Operate one displayed-proposal-bound post-entry SELL+BUY paper rotation through the default Command Center, preserve reject-all and fail-closed behavior, prove persistence/certification/replay, update truth, and publish only the exact authorized paths.

## Checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Episode-one authority preserved | PASS | MU `7 @ 101.25`, cost `2`, residual `0` fixtures remain green |
| CHK-02 Mutation-free displayed-proposal preview | PASS | focused rotation test |
| CHK-03 PIT/book/certification/event/price binding | PASS | focused binding and tamper tests |
| CHK-04 Complete-fill SELL+BUY accounting | PASS | SELL `3 MU`, BUY `5 MERID`, residual `0` |
| CHK-05 Confirmation and atomic persistence | PASS | operated storage confirmation test |
| CHK-06 Certification and separate-process replay | PASS | byte-identical fresh-process receipt |
| CHK-07 Reject-all preserves economics | PASS | rejection test; companion not admitted |
| CHK-08 Stale and buy-only transitions fail closed | PASS | negative tests |
| CHK-09 Default Command Center journey | PASS | Streamlit AppTest |
| CHK-10 Declared regression matrix | PASS | sealed 31/31 pytest transaction |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Repricing retained MU to `102` created unexplained mark-to-market residual | Keep source mark at certified `101.25`; do not invent P&L authority | Implementer | RESOLVED |
| High | New rotation validation could mask the legacy post-entry sell-required error | Detect rotation only from explicit displayed-proposal/dual-market bindings | Implementer | RESOLVED |
| Medium | Funded Command Center stopped after entry | Add one bounded proposal-bound rotation action using the shared preview/disposition flow | Implementer | RESOLVED |
| Medium | Stale blocker truth remained after connector recovery | Reconcile brief, context packets, decision log, lessons, and this receipt | Docs/Ops | RESOLVED |

## Validation / evidence

Exact sealed validation:

```text
C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe -m pytest tests/test_gv_pit_operated_rotation.py tests/test_gv_pit_operated_capital.py tests/gv_portfolio_v0/test_prospective.py tests/gv_portfolio_v0/test_prospective_app.py -q
............................... [100%]
exitCode=0; tests=31; durationMs=203929
```

The retained native task outcome is `DONE` and explicitly authorizes one publication of the exact pre-authorized Git paths. Separate Reviewer A/B/C transcripts are not exposed by the retained native-task record; this report does not invent them. For this exact task, the sealed task authority explicitly outranks repository-source review ceremony.

## Document Changes Showing

- `gv_portfolio_v0/prospective.py` — companion derivation, displayed-proposal binding, dual-market rotation validation, SELL+BUY projection, legacy behavior preservation.
- `views/command_center.py` — shared preview/disposition flow and funded proposal-bound rotation surface.
- `tests/test_gv_pit_operated_rotation.py` — core, rejection, tamper, fresh-process, and Command Center AppTest acceptance.
- `docs/phase_brief/gv-operated-rotation-1-brief.md` — final product and claim boundary.
- `docs/context/*_current.md` — validated current truth and terminal next step.
- `docs/decision log.md` — rotation decision and score/claim boundary.
- `docs/lessonss.md` — mark-to-market residual and request-contract guardrail.

## Scope split

In scope: exact displayed-proposal-to-capital rotation, tests, truth, and publication.

Out of scope: provider acquisition, provider-quality claims, strategy-generated targets, optimizer/risk expansion, alpha, realized value, broker, live capital, or another authority system.

## Closure

ChecksTotal: 10
ChecksPassed: 10
ChecksFailed: 0
SAW Verdict: PASS — sealed native task authority
ClosureValidation: NOT_RUN — generic shell is denied on the sealed task; retained task outcome `DONE` is controlling.
SAWBlockValidation: NOT_RUN — generic shell is denied on the sealed task; retained task outcome `DONE` is controlling.

ClosurePacket: RoundID=ROUND-20260805-GV-OPERATED-ROTATION-1; ScopeID=GV-OPERATED-ROTATION-1; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=provider_quality_strategy_targets_alpha_realized_value_unproven; NextAction=publish_exact_pre_authorized_paths_once
