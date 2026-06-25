# SAW Report - source-stability-recovery-v0

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: source-stability-recovery-v0-20260526
ScopeID: boot-preflight-source-stability

## Scope

Recover boot-preflight source stability after root `scripts/boot_preflight.py` repeatedly reverted during verification.

Owned files changed in this round:

- `E:\Code\Quant_boot_preflight_stability\scripts\boot_preflight.py`
- `E:\Code\Quant_boot_preflight_stability\tests\test_boot_preflight.py`
- `docs/saw_reports/saw_source_stability_recovery_v0_20260526.md`

Root `E:\Code\Quant\scripts\boot_preflight.py` and `E:\Code\Quant\tests\test_boot_preflight.py` were inspected but not trusted after mutation recurred.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Root `scripts/boot_preflight.py` reverted from focused-contract opt-in back to `run_focused_contract = bool(args.run_focused_contract) or run_tests`, so root strict boot evidence is untrustworthy. | Stop using root as the boot-control writer until competing Codex/session writers are frozen; port the isolated two-file stable patch back with one writer. | Boot/Ops | Open |
| High | Root boot-control pytest failed and hash stayed stable only after the stale file had already returned, proving transient root green states are not reliable. | Require post-command hash sentinels and reject any root strict proof until the stale pattern stays absent through tests and 30-second post-run guard. | Boot/Ops | Open |
| Medium | Isolated `E:\Code\Quant_boot_preflight_stability` proved the two contested files can remain stable and pass local boot-preflight semantics, but it lacks the full local dirty context and must not be promoted as root safe boot. | Use isolated worktree as a staging lane only; do not claim full strict or safe boot from it. | Boot/Ops | Resolved for isolation |
| Medium | Two SAW reviewer passes timed out during closeout. | Carry reviewer unavailability as closure risk and require a fresh reviewer pass before any milestone close. | Parent coordinator | Open |

## Scope Split

In-scope findings/actions:

- Root source mutation for `scripts/boot_preflight.py`.
- Focused contract must remain opt-in.
- Governance `WARN` is advisory/pass and governance `FAIL` blocks.
- Two-file isolated source stability proof.

Inherited out-of-scope findings/actions:

- Broad dirty worktree across dashboard, data, optimizer, replay, docs, packet zips, and evidence outputs.
- Safe-boot tag/branch update.
- Full root strict preflight proof.
- Portfolio smoke and context validation in the isolated worktree.

## Reviewer Summary

- Explorer pass: found no definitive writer PID, but observed `scripts/boot_preflight.py` change during observation and identified active boot-preflight pytest processes earlier in the round.
- Implementer pass: root repair was stopped after mutation recurred; isolated worktree patch was applied only to `scripts/boot_preflight.py` and `tests/test_boot_preflight.py`.
- Reviewer A: Unavailable after timeout; carried as BLOCK risk.
- Reviewer B: Unavailable after timeout; carried as BLOCK risk.
- Reviewer C: BLOCK; found isolated v0 needed argv-bounded focused contract, atomic status write, and bounded gate timeouts. Parent reconciled these in the isolated two-file lane.
- Ownership check: Implementer and Reviewer C were separate agents; Reviewer A/B did not complete.

## Verification Evidence

- Root stale-pattern check after failed root test: `E:\Code\Quant\scripts\boot_preflight.py` contained `run_focused_contract = bool(args.run_focused_contract) or run_tests`.
- Root `.venv\Scripts\python -m pytest tests\test_boot_preflight.py -q` failed after source reverted; hash remained stable only for the reverted file.
- Isolated 10-second hash guard for `E:\Code\Quant_boot_preflight_stability\scripts\boot_preflight.py` and `tests\test_boot_preflight.py` -> PASS, no diff.
- Isolated stale-pattern guard `Select-String scripts\boot_preflight.py -Pattern "or run_tests|run_focused_contract.*run_tests|focused.*run_tests|shell=True"` -> PASS, no matches.
- Isolated compile: `E:\Code\Quant\.venv\Scripts\python.exe -m compileall -q scripts\boot_preflight.py tests\test_boot_preflight.py` -> PASS, hash stable.
- Isolated unit test: `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests\test_boot_preflight.py -q` -> PASS, `14 passed, 1 skipped`, hash stable.
- Isolated 30-second post-run hash sentinel -> PASS, `HASH_STABLE`.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_source_stability_recovery_v0_20260526.md` | Records source-stability recovery evidence and BLOCK outcome. | Current report |
| `E:\Code\Quant_boot_preflight_stability\scripts\boot_preflight.py` | Isolated two-file lane: focused contract opt-in, governance WARN/FAIL semantics, argv-bounded focused contract, atomic status write, bounded test gates. | Reviewer C finding reconciled |
| `E:\Code\Quant_boot_preflight_stability\tests\test_boot_preflight.py` | Isolated tests for default strict skip, explicit focused contract, governance WARN advisory, governance FAIL block, shell metacharacter rejection, no-shell timeout path. | Reviewer C finding reconciled |
| `E:\Code\Quant\scripts\boot_preflight.py` | Root file inspected and found stale after the failed root test, then changed again by final sanity check; current pattern is not trusted because the source did not remain stable during verification. | BLOCK |

## Document Sorting

GitHub-optimized order maintained for this report:

1. `docs/saw_reports/saw_source_stability_recovery_v0_20260526.md`

Open Risks:

- root_boot_preflight_source_reverted_during_verification
- root_strict_preflight_not_trustworthy
- reviewer_a_b_unavailable
- isolated_worktree_not_full_boot_context

Next action:

Freeze competing Codex/session writers, then port the isolated two-file stable patch back to `E:\Code\Quant` as the single writer and rerun the full mutation-aware root acceptance matrix.

ClosurePacket: RoundID=source-stability-recovery-v0-20260526; ScopeID=boot-preflight-source-stability; ChecksTotal=8; ChecksPassed=5; ChecksFailed=3; Verdict=BLOCK; OpenRisks=root_boot_preflight_source_reverted_during_verification,reviewer_a_b_unavailable,isolated_worktree_not_full_boot_context; NextAction=freeze_competing_writers_then_port_isolated_two_file_patch_to_root_and_rerun_hash_guard_matrix

ClosureValidation: PASS
SAWBlockValidation: PASS
