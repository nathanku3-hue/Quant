# SAW Report — GV Financial Cascade Four-Arm 1 — 2026-08-04

Mode: `CLOSURE_REPORT`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: explicit GO with six amendments | Domains: cascade research, existing regime attribution, canonical portfolio evidence, prospective receipt, experiment exit rule | FallbackSource: not used

RoundID: `GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804`
ScopeID: `GV-FINANCIAL-CASCADE-FOUR-ARM-1`
Parent candidate: `00481ac8803497d48e70451816524115ffb3ceaf`
Candidate status: banked and pushed at `2c318f17b8563e21cfe5cfbdf43b32a514fe0f79`; engineering-only four-arm implementation and evidence; no Command Center integration, paper confirmation, portfolio mutation, score uplift, or live authority.

## Verdict

SAW Verdict: BLOCK

The bounded engineering result is implemented, executable, tested, replayable, and honest. Terminal product closure remains blocked because independent Reviewer A/B/C capacity is unavailable and no governed PIT institutional-network observation exists. The candidate may be banked as `ENGINEERING_ONLY`; it cannot be promoted into the paper-decision bridge.

## Scope

In-scope: existing G5 nonzero canonical portfolio reuse; actual `RegimeManager` consumption; four same-engine arms; order-independent combined cap; D-versus-B vector attribution; ex-ante prospective receipt; frozen manual exit rule; exact replay; atomic CLI evidence; synthetic-evidence classification; documentation.

Inherited and out of scope: Command Center integration or card, real bilateral-exposure acquisition, market-snapshot admission, OVERLAY proposal, sell-only order/fill operation, confirmation/rejection, book mutation, certification, broker/live capital, score uplift, security selection, entry/exit signals, and Leningrad changes.

## SE execution tasks

| Task ID | Task | Artifact | Acceptance check | Status | Evidence ID |
|---|---|---|---|---|---|
| TSK-01 | Reuse an existing nonzero Quant portfolio | G5 canonical slice and loader | 41 sessions × 3 names, gross 1.0, artifact/manifest and frame identities bound | PASS | EVD-01 |
| TSK-02 | Freeze and execute four arms | `research/financial_cascade_four_arm.py` | A/B/C/D use the same engine; D uses `min(G,R,C)`, never scalar multiplication | PASS | EVD-02 |
| TSK-03 | Attribute cascade incrementally beyond existing regime | report `incremental_d_vs_b` | required net/MDD/ES/turnover/missed/avoided/reduced-days/re-entry vector exists | PASS | EVD-03 |
| TSK-04 | Emit prospective evidence before product integration | receipt in engineering evidence | PIT times, target digest, controls, incremental result, full exit rule, identity | PASS | EVD-04 |
| TSK-05 | Run one honest engineering episode | evidence JSON | synthetic Leningrad bundle remains `ENGINEERING_ONLY`; no alpha/score/capital authority | PASS | EVD-05 |
| TSK-06 | Preserve existing cascade and research behavior | focused/regression matrix | 78 tests pass; exact replay; compile and diff checks pass | PASS | EVD-06 |
| TSK-07 | Obtain terminal independent A/B/C and governed real PIT evidence | external review and source authority | distinct reviews plus real network/liability/shock/source-time/availability proof | BLOCK | EVD-07 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-02,TSK-03:EVD-03,TSK-04:EVD-04,TSK-05:EVD-05,TSK-06:EVD-06,TSK-07:EVD-07
EvidenceRows: EVD-01|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-02|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-03|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-04|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-05|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-06|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z;EVD-07|GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804|2026-08-04T10:19:00Z

EvidenceValidation: PASS

## Acceptance checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Existing portfolio is G5 Tier-0 canonical, nonzero, identity-bound, and not created for Leningrad | PASS | portfolio loader test and source identity |
| CHK-02 Existing regime path is `RegimeManager.evaluate().target_exposure` | PASS | implementation and regime tests |
| CHK-03 Combined gross equals the minimum of uncapped/regime/cascade caps | PASS | explicit 0.50 versus prohibited 0.375 test |
| CHK-04 All four arms use `core.engine.run_simulation` with the same cost and return matrix | PASS | implementation and replay digests |
| CHK-05 D-versus-B attribution is the frozen vector, not net return alone | PASS | evidence JSON and tests |
| CHK-06 Receipt binds PIT timestamps, target digest, controls, incremental information, and exit rule | PASS | receipt `e18509fc9e69…` |
| CHK-07 Exit rule binds effective date, horizon, max holding, review, terminal disposition, and reconciliation | PASS | restore-to-baseline test and evidence |
| CHK-08 Synthetic Leningrad observation is `ENGINEERING_ONLY` and cannot uplift score or authorize capital | PASS | report and negative authority assertions |
| CHK-09 Existing cascade, engine, regime, canonical readiness/replay, and research-runner regression remains green | PASS | 78 passed |
| CHK-10 Independent A/B/C and one governed PIT cascade observation exist | BLOCK | capabilities/evidence absent |

## Implementer pass

- PASS: the four-arm path consumes the existing nonzero canonical portfolio and actual regime output.
- PASS: combined-cap mathematics is order-independent and explicitly rejects implicit scalar multiplication.
- PASS: the first result is retained despite being economically negative/neutral versus regime-only.
- PASS: the receipt is the mandatory evidence; no UI or integration dependency was introduced.
- PASS: terminal restoration is explicit and re-entry delay is defined.
- PASS: the Pandas calendar-precision mismatch was repaired at the shared overlay boundary and covered by the G5 portfolio test.

## Reviewer perspectives

### Reviewer A — strategy correctness and regression risk

Local non-independent review: PASS. The cascade changes gross exposure only; it does not alter names, ranks, entry, exit, or Leningrad intervention semantics. D-versus-B correctly isolates incremental value beyond the existing regime path.

Independent status: NOT RUN.

### Reviewer B — runtime and operational resilience

Local non-independent review: PASS. Inputs fail closed; evidence classification is explicit; exit dates are calendar-bound; output is atomic; exact replay passes; no Command Center, persistence, provider, broker, or network side effect is introduced.

Independent status: NOT RUN.

### Reviewer C — data integrity and performance path

Local non-independent review: PASS. G5 artifact/manifest identities are retained; no new portfolio is synthesized; frame and row digests bind inputs; PIT availability remains next-day; cap application is vectorized; the shared overlay now normalizes observation precision to the admitted calendar dtype.

Independent status: NOT RUN.

### Bounded PRODUCT review

REVIEW-RETURN-2: PASS for the explicitly bounded `ENGINEERING_ONLY` slice. Review ID `f6ef90e03b3affeb986c167f4027f52a6d724492c1e9fbcdeaba41fa65c44b5c`; candidate manifest digest `c2d60266aea7b010060f2f5f5c3d21eadbce8c5e6d89f1e3180b3ab343e4f730`; evidence manifest digest `96fca446843b16d3d148cc491d2abbf88edd917510e69272298e57b5bf743b9b`; conversation identity `6d67a3300bd1da326d2e98af63d4d8d251560a141eaf523389d82703554829b7`.

The reviewer accepted the scope clarity, deterministic replay, atomic CLI, tests, and identity custody. It independently confirmed that the negative economics provide no alpha, score, or capital basis and that governed PIT evidence plus independent A/B/C remain promotion blockers.

## Findings

| Severity | Finding | Impact | Fix | Owner | Status |
|---|---|---|---|---|---|
| High | No governed PIT institutional-network observation | Engineering result cannot become a score-bearing paper decision | Obtain exact network, liability, shock, source-time, and availability-time authority in a separate data round | Future data/research | OPEN; PRODUCT BLOCKER |
| High | Independent Reviewer A/B/C unavailable | Local evidence cannot establish terminal milestone acceptance | Run three distinct reviews against frozen candidate bytes before paper integration | Owner/integrator | OPEN; PROCEDURAL BLOCKER |
| Material | Current synthetic result shows no MDD/ES benefit and negative net benefit versus regime-only | Cascade hypothesis has not earned promotion | Retain result; do not tune or rerun for sign; test only when governed real observations exist | Future research | OPEN; EXPECTED EVIDENCE |
| Advisory | Managed DevSpace worktree allocation created empty directories | Separate child checkout could not be used | Continued from clean pushed checkout with immutable parent; repair allocator outside this product round | DevSpace tooling | OPEN; OUT OF SCOPE |

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `research/financial_cascade_four_arm.py` | four arms, min-cap law, attribution vector, receipt, governed-evidence gate, exit rule | local A/B/C PASS; independent pending |
| `scripts/run_financial_cascade_four_arm.py` | existing G5 portfolio CLI, regime steps, atomic evidence, governed-proof input | local B/C PASS; independent pending |
| `tests/test_financial_cascade_four_arm.py` | portfolio identity, min-cap, vector, receipt/exit, governed gate, CLI tests | local A/B/C PASS; independent pending |
| `strategies/financial_cascade.py` | bind observation timestamps to canonical calendar precision before `merge_asof` | local B/C PASS; independent pending |
| `docs/context/e2e_evidence/gv_financial_cascade_four_arm_engineering_20260804.json` | first immutable engineering-only result and receipt | local A/B/C PASS; independent pending |
| PRD/spec/brief/notes/decision/lessons | sequencing, formulas, result, authority boundary, and next blocker | local scope review PASS; independent pending |

## Validation / evidence

- Focused cascade + four-arm: `11 passed`.
- Broader matrix: `78 passed` across cascade, four-arm, RegimeManager, engine, G4 readiness, G5 replay, and research runner.
- Python compile: PASS.
- `git diff --check`: PASS.
- Leningrad v0.4 bundle generation and independent verification: PASS; bundle `88b9ff3…`, scenario `4415a158…`.
- Engineering evidence: report `357656049f7f…`; execution `e463d2f2a7aa…`; receipt `e18509fc9e69…`; exact replay PASS.
- Bounded PRODUCT review: PASS on exact candidate/evidence manifests; promotion blockers retained.
- Economic result versus regime-only: compounded net `-0.02185748`; MDD approximately unchanged; ES unchanged; turnover `+0.50`; missed upside `0.02051325`; avoided loss `0.00176342`; reduced sessions `9`; re-entry delay `0`.

## Rollback

Revert the four-arm candidate commit while retaining parent cascade custody commit `00481ac…`. No Command Center branch, Leningrad source, certified portfolio, provider, broker, or live-capital state is mutated.

## Open Risks

Open Risks: governed PIT network evidence is missing; independent A/B/C is missing; current engineering result does not demonstrate incremental economic value.

## Next action

Next action: bank this exact `ENGINEERING_ONLY` candidate, bank Command Center hardening independently, and stop before integration until a governed PIT cascade observation exists.

ClosurePacket: RoundID=GV-FINANCIAL-CASCADE-FOUR-ARM-1-20260804; ScopeID=GV-FINANCIAL-CASCADE-FOUR-ARM-1; ChecksTotal=10; ChecksPassed=9; ChecksFailed=1; Verdict=BLOCK; OpenRisks=governed_pit_observation_and_independent_A_B_C_missing; NextAction=bank_engineering_candidate_and_command_center_independently_then_obtain_governed_PIT_observation

ClosureValidation: PASS
SAWBlockValidation: PASS
