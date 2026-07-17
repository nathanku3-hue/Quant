# SAW — GV-FS0 Repair Rerun

RoundID: `ROUND-20260718-GV-FS0-REPAIR-RERUN`
ScopeID: `GV_FS0_PROTOCOL_V1_LINEAGE_CI_AND_TERMINAL_AUDIT`
Work round scope: publish the reviewed GV-FS0 candidate on the canonical lineage, repair only CI checkout/dependency portability blockers, and complete the terminal audit without authorizing reducer or product work.

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: L1 Terminal Zero quantitative research console; L2 active stream Docs/Ops protocol freeze; L2 deferred streams Backend accounting, Frontend/UI, Data admission, Research integration; L3 Consolidation -> Machine Artifacts -> Golden Tests -> Freeze Audit -> Reducer Authorization (FallbackSource: `docs/spec.md` + `docs/phase_brief/phase-E0-brief.md`).

## Reviewer ownership

Implementer: primary agent. Reviewer A, Reviewer B, and Reviewer C were independent agents with no file edits. Ownership check: PASS.

## Findings

| finding_id | severity | impact | fix | owner | status |
|---|---|---|---|---|---|
| F-01 | Medium | GitHub checkout aborted on inherited malformed snapshot gitlinks | Custom no-submodule fetch checkout; remove the single stale gitlink encountered on the branch | CI | CLOSED |
| F-02 | Medium | Ubuntu protocol tests loaded repository `conftest.py` without pandas | Pin `pandas==2.2.3` with protocol test dependencies | CI | CLOSED |
| F-03 | Medium | Windows byte-exact freeze check saw CRLF checkout bytes | Set `core.autocrlf=false` before checkout | CI | CLOSED |
| F-04 | Low | POSIX test treated a Windows path string as absolute | Use `os.name == "nt"` platform guard | Test owner | CLOSED |

## Scope split

In-scope: lineage publication, LF/canonical fixture integrity, protocol validators, focused GV-FS0/V2 tests, CI checkout portability, dependency pinning, and terminal A/B/C review.

Inherited out-of-scope: reducer implementation, economic transitions, FS0 event generation, snapshots, certification execution, certified decisions, permanent bundle publication, Streamlit integration, provider access, real-data admission, and downstream research/product work remain blocked and untouched.

## Document Changes Showing

| path | change | reviewer status |
|---|---|---|
| `.github/workflows/gv-fs0-protocol-v1.yml` | no-submodule authenticated checkout; LF preservation; pandas pin | Reviewer B PASS; CI PASS |
| `tests/test_gv_fs0_protocol_supervision.py` | platform-correct absolute executable fixture | Reviewer A PASS; Ubuntu/Windows PASS |
| `root repo/Quant_2a13724_clean` | stale gitlink removed to unblock checkout | Reviewer B PASS; CI PASS |
| `docs/saw_reports/saw_gv_fs0_repair_rerun_20260718.md` | terminal SAW evidence and closure | Reviewer A/B/C PASS |

## Acceptance checks

- CHK-01 Required ancestry `6a8bb6c9410bc91940d53ca727b561aa86776ec -> 94c3ea4 -> a9531d6`: PASS.
- CHK-02 Freeze and immutability validators: PASS.
- CHK-03 Focused GV-FS0/V2 tests: PASS locally; 69 focused cases collected (54 GV-FS0 + 15 V2).
- CHK-04 LF-only canonical fixtures and manifest/hash integrity: PASS.
- CHK-05 Independent Reviewer A/B/C passes and ownership check: PASS.
- CHK-06 Ubuntu GitHub Actions matrix job: PASS.
- CHK-07 Windows GitHub Actions matrix job: PASS.
- CHK-08 Reducer boundary and forbidden-action scan: PASS; reducer remains blocked.

SAW Verdict: PASS
Open Risks: reducer authorization remains false by design; broader repository test suite is out of scope for this protocol round.
Next action: retain the draft PR for human review; do not begin reducer work until explicit authorization.

ClosurePacket: RoundID=ROUND-20260718-GV-FS0-REPAIR-RERUN; ScopeID=GV_FS0_PROTOCOL_V1_LINEAGE_CI_AND_TERMINAL_AUDIT; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=reducer_authorization_remains_false; NextAction=retain_draft_pr_for_human_review
ClosureValidation: PASS
SAWBlockValidation: PASS
