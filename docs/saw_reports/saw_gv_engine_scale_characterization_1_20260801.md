# SAW Report — GV Engine Scale Characterization 1 — 2026-08-01

Mode: `CLOSURE_REPORT`

Hierarchy Confirmation: BLOCKED | Session: current-thread | Trigger: new-domain | Domains: engine scaling, persistence custody, timestamp/data integrity, product workload, Australian custody/legal boundary | FallbackSource: `docs/spec.md` + `docs/phase_brief/gv-engine-scale-characterization-1-brief.md` | Reason: the persisted hierarchy is stale PEAD context and does not confirm this scale/custody scope

RoundID: `GV-P1-SCALE-CHAR-20260801`
ScopeID: `GV-ENGINE-SCALE-CHARACTERIZATION-1`
Base: `e564cd9dfa45eb02ef8d7eb94b662543fb3776c9`
Diagnostic candidate: `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`
Diagnostic tree: `e048f2483c64fcf7a9cae58e8454b70d7e993e78`
Branch: `codex/gv-engine-scale-characterization-1`

## Verdict

SAW Verdict: BLOCK

The diagnostic candidate is frozen, remote-equal, and locally validated. The spike correctly stopped on two design-constraint findings rather than repairing them. Closure as independently reviewed evidence is blocked because Reviewer A/B/C cannot be run through the exposed execution surface and the persisted hierarchy fallback is stale for this new scale/custody domain. No product acceptance, score uplift, Universe claim, Challenger opening, or Limited Live authority is inferred.

## Acceptance checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 P0 terminal closure and terminal tag remain immutable | PASS | base and peeled terminal tag remain `e564cd9` |
| CHK-02 50-security scenario completes twice in fresh processes with equal scenario/state/event/book hashes and residual `0` | PASS | characterization evidence packet |
| CHK-03 100-security scenario completes twice in fresh processes with equal hashes and residual `0` | PASS | characterization evidence packet |
| CHK-04 Existing persistence is probed unchanged and both scenario-ID rejections are retained as findings | PASS | characterization script/tests and evidence packet |
| CHK-05 Forty malformed 100-security timestamps beginning at `12:60` are retained as a finding | PASS | characterization script/tests and evidence packet |
| CHK-06 No engine, storage, application, view, workflow, dependency, provider, broker, or live repair is included | PASS | candidate diff and changed-path audit |
| CHK-07 Custody decision records options, discriminator, selected provisional model, legal questions, and stop rules | PASS | `docs/context/gv_p1_custody_model_decision.md` |
| CHK-08 Diagnostic candidate is immutable and remote-equal | PASS | `origin/codex/gv-engine-scale-characterization-1 = f9d271d` |
| CHK-09 Independent Reviewer A/B/C complete against exact candidate | BLOCK | reviewer-agent capability unavailable in current tool surface |
| CHK-10 Current hierarchy confirmation covers scale, custody, legal, and product-workload domains | BLOCK | persisted fallback is stale and no explicit hierarchy approval exists |

## Implementer pass

- PASS: diagnostic declarations contain exactly 50 and 100 unique symbols and permanent keys.
- PASS: the same accepted engine executes draft, confirmation, no-change, transition, correction, accounting, replay, certification, and validation.
- PASS: fresh-process canonical equality is exact at both sizes.
- PASS: the persistence probe calls the existing storage path unchanged and records rejection before write.
- PASS: timestamp parsing distinguishes deterministic bytes from valid temporal data.
- PASS: accepted 10/25 behavior, FS0 authority, and generated context remain green in split retained runs.
- PASS: the 100-security result is explicitly diagnostic and does not claim Universe acceptance.
- PASS: the provisional custody record preserves human submission and no system-held broker credentials.

## Reviewer status

### Reviewer A — product result and decision usefulness

Local non-independent review: PASS.

- The spike answers the immediate decision: engine core scales in memory, but the product path does not.
- Workload is not falsely accepted because persistence prevents executable save/reopen/UI operation.
- The accepted score remains `62/100`; P2 and P3 remain closed.

Independent status: NOT RUN.

### Reviewer B — runtime, persistence, and operational resilience

Local non-independent review: PASS.

- Both sizes complete in separate processes with exact hash equality.
- Persistence rejects both diagnostic IDs before write, so no partial state or misleading reopen evidence exists.
- DevSpace HTTP 502 calls are classified as transport-invalid and excluded from evidence.

Independent status: NOT RUN.

### Reviewer C — data integrity and performance path

Local non-independent review: PASS.

- Residual is `0` at both sizes and event/order/fill counts are stable across repeats.
- Peak working set is externally observed from the child process.
- The 100-security timestamp defect is deterministic but invalid and therefore remains a blocking finding.

Independent status: NOT RUN.

## Findings

| Severity | Finding | Impact | Fix | Owner | Status |
|---|---|---|---|---|---|
| High | Shared persistence hard-codes only accepted 10/25 scenario IDs | 50/100 cannot save, reopen, correct after reopen, or execute the product UI path | Separate bounded repair for scenario-safe shared naming/root selection; preserve one storage implementation | Future repair round | OPEN; OUT OF SCOPE |
| High | Initial evidence timestamp formatter uses instrument index as minute | 100-security records contain 40 malformed timestamps and invalid data identities | Separate bounded repair using real monotonic timestamp arithmetic; decide identity impact explicitly | Future repair round | OPEN; OUT OF SCOPE |
| High | Independent Reviewer A/B/C unavailable | Local self-review cannot establish independent closure | Run distinct reviewers against exact `f9d271d`, or explicitly accept the procedural risk | Integrator / owner | OPEN |
| Medium | Persisted hierarchy fallback is stale | Hierarchy audit stamp cannot pass for scale/custody/legal scope | Confirm a current project hierarchy covering the active domains | Owner / integrator | OPEN |

## Scope split

### In-scope findings and actions

Declare synthetic 50/100 diagnostic inputs, execute the existing engine in fresh processes, measure timing/memory/counts/hashes, probe unchanged persistence, validate timestamps, preserve retained product regressions, record custody options and stop rules, freeze exact candidate custody, and stop on required repair.

### Inherited and out-of-scope findings and actions

Storage redesign, timestamp repair, 50/100 product UI operation, prospective paper episodes, Universe membership/corporate-action custody, Challenger comparison, broker integration, legal clearance, Limited Live, full terminal publication, and score uplift remain outside this round.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `gv_portfolio_v0/operated_scenarios.py` | declarative synthetic 50/100 stress scenarios | local A/B/C PASS; independent pending |
| `scripts/characterize_gv_engine_scale.py` | fresh-process measurement, memory polling, unchanged persistence and timestamp probes | local B/C PASS; independent pending |
| `tests/gv_portfolio_v0/test_engine_scale_characterization.py` | locks uniqueness, deterministic completion, persistence stop, timestamp stop, and retained-25 identity | local A/B/C PASS; independent pending |
| `docs/context/gv_p1_custody_model_decision.md` | provisional owner-controlled proprietary custody/handoff decision | local A/B review PASS; legal review open |
| roadmap, active brief, current truth, evidence, handover, decision and lesson logs | classify candidate as frozen finding with score and downstream boundaries unchanged | local scope review PASS |

## Validation / evidence

- Exact candidate and remote equality: PASS at `f9d271d2a67eca9d08bcc01fb3a5bf342bd8d283`.
- Characterization script: 50 and 100 each run twice; expected verdict `FINDING` reproduced.
- Operated product focused tests: PASS in split runs.
- Accounting, replay, execution, strategy, and vertical regressions: PASS in split runs.
- Legacy app, bounded, scale, universe, and challenger regressions: PASS in split runs.
- FS0 authority, context hygiene, and context-builder tests: PASS.
- Context generation and `--validate`: PASS.
- Python compile for changed modules/tests: PASS.
- `git diff --check`: PASS before candidate freeze.
- Combined commands lost to DevSpace HTTP 502 are transport-invalid and not counted.
- Evidence packet: `docs/context/e2e_evidence/gv_engine_scale_characterization_1_20260801.md`.

## Open Risks

Open Risks: independent Reviewer A/B/C and current hierarchy confirmation remain missing; the two product findings remain intentionally unresolved outside this spike.

1. Independent review must run against exact candidate `f9d271d`, or the owner must explicitly accept proceeding without it.
2. A current hierarchy covering engine scale, persistence/data integrity, custody/legal exposure, and product workload must be confirmed.
3. Any repair must be a new bounded round and must not amend or recut the diagnostic candidate.

## Next action

Next action: preserve `f9d271d` and its documentation evidence commit; do not move `main` or the terminal tag. Run independent A/B/C plus hierarchy confirmation when capability is available, then select one bounded repair for scenario-safe shared persistence and valid monotonic timestamps.

ClosurePacket: RoundID=GV-P1-SCALE-CHAR-20260801; ScopeID=GV-ENGINE-SCALE-CHARACTERIZATION-1; ChecksTotal=10; ChecksPassed=8; ChecksFailed=2; Verdict=BLOCK; OpenRisks=independent_review_and_current_hierarchy_confirmation_missing; NextAction=preserve_f9d271d_then_complete_review_before_bounded_persistence_timestamp_repair

ClosureValidation: PASS
SAWBlockValidation: PASS
