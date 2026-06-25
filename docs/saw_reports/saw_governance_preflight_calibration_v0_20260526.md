# SAW Report - governance-preflight-calibration-v0

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Backend, Frontend/UI, Data, Docs/Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md

RoundID: governance-preflight-calibration-v0-20260526
ScopeID: boot-governance-preflight-calibration-v0

## Scope

Calibrate boot governance so strict preflight remains fast, prints but does not run the focused replay/dashboard contract by default, and blocks any non-PASS governance result while allowing exact neutral research-console labels.

Owned files attempted in this round:

- `scripts/boot_preflight.py`
- `scripts/governance_preflight.py`
- `tests/test_boot_preflight.py`
- `tests/test_boot_preflight_governance.py`

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | `scripts/boot_preflight.py` repeatedly reverted during verification from `run_focused_contract = bool(args.run_focused_contract)` back to `bool(args.run_focused_contract) or run_tests`, so strict preflight can execute the focused contract by default. | Freeze competing writers or isolate this slice in a clean worktree, then reapply the focused-contract opt-in patch. | Boot/Ops | Open |
| High | `scripts/boot_preflight.py` repeatedly reverted boot-status readiness mapping for governance `WARN` to degraded semantics, while tests intermittently expected governance `WARN` to block. | Make governance non-PASS fail closed in both `build_status(...)` and `make_boot_status_from_preflight(...)`, then rerun mutation-aware checks. | Boot/Ops | Open |
| Medium | `tests/test_boot_preflight.py` and `scripts/boot_preflight.py` did not remain mutually consistent after delayed overwrites, so transient green pytest output is not trustworthy closure evidence. | Use hash-stability checks after tests and avoid parallel Codex/subagent/app-server writers during boot-control verification. | Boot/Ops | Open |
| Low | Governance label calibration itself passed targeted review: exact neutral labels are allowlisted and action-shaped appended copy remains covered by tests. | Keep `scripts/governance_preflight.py` exact-label policy and exact-only tests. | Governance | Resolved |

## Scope Split

In-scope findings/actions:

- Boot strict focused-contract gating.
- Governance non-PASS blocking semantics.
- Exact neutral research-console label allowlist.
- Mutation/stability proof for boot-control files.

Inherited out-of-scope findings/actions:

- Broad dirty worktree and unrelated untracked packet/evidence artifacts remain inherited.
- Safe-boot tag/branch update remains deferred.
- Full focused replay/dashboard contract remains explicit `--run-focused-contract` proof, not normal strict.

## Reviewer Summary

- Implementer pass: attempted focused patch and targeted verification; transient checks passed before delayed file overwrite.
- Reviewer A: BLOCK; found strict default still running focused contract and governance `WARN` not blocking in live file.
- Reviewer B: BLOCK; confirmed the same two High operational risks.
- Reviewer C: BLOCK; confirmed governance `WARN` remained a data-integrity fail-closed violation.
- Ownership check: Implementer and Reviewers A/B/C were separate agents.

## Verification Evidence

- `.venv\Scripts\python -m compileall -q scripts\boot_preflight.py scripts\governance_preflight.py tests\test_boot_preflight.py tests\test_boot_preflight_governance.py` -> PASS before later overwrite.
- `.venv\Scripts\python -m pytest tests\test_boot_preflight.py -q --cache-clear` -> PASS before later overwrite; hash check initially reported `NO_SOURCE_MUTATION`.
- `.venv\Scripts\python -m pytest tests\test_boot_preflight_governance.py -q --cache-clear` -> PASS before later overwrite.
- `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py -q --cache-clear` -> PASS before later overwrite.
- `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json` -> PASS with zero findings after label calibration.
- `.venv\Scripts\python -m pytest tests\test_dash_1_page_registry_shell.py::test_dash_1_portfolio_allocation_route_renders_without_overlay -q` -> PASS.
- `.venv\Scripts\python launch.py --preflight --strict` -> transient PASS with focused contract printed only, followed by delayed source reversion.
- Direct post-reversion probe showed `run_focused_contract=True` and focused contract called under default strict, so strict boot evidence is not trusted.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/saw_reports/saw_governance_preflight_calibration_v0_20260526.md` | Records SAW BLOCK for boot/governance source contention and reviewer findings. | Current report |
| `scripts/governance_preflight.py` | Exact neutral label allowlist was calibrated during the round. | Reviewed, no High/Critical issue |
| `tests/test_boot_preflight_governance.py` | Exact-label and exact-only tests were added during the round. | Reviewed, no High/Critical issue |
| `scripts/boot_preflight.py` | Attempted strict/focused/governance fixes reverted during verification. | BLOCK |
| `tests/test_boot_preflight.py` | Attempted regression updates did not remain stable with live source. | BLOCK |

## Document Sorting

GitHub-optimized order maintained for this report:

1. `docs/saw_reports/saw_governance_preflight_calibration_v0_20260526.md`

Open Risks:

- boot_preflight_source_reverted_during_verification
- strict_default_may_run_focused_contract_until_source_contention_is_resolved
- governance_WARN_blocking_contract_not_stably_applied_to_live_file

Next action:

Freeze or close competing Codex/subagent/app-server writers, reapply the two-line boot contract fix in an isolated pass, then rerun mutation-aware verification and strict preflight.

ClosurePacket: RoundID=governance-preflight-calibration-v0-20260526; ScopeID=boot-governance-preflight-calibration-v0; ChecksTotal=6; ChecksPassed=3; ChecksFailed=3; Verdict=BLOCK; OpenRisks=boot_preflight_source_reverted_during_verification; NextAction=freeze_competing_writers_then_reapply_boot_contract_patch

ClosureValidation: PASS
SAWBlockValidation: PASS
