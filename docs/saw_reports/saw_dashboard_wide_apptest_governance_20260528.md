# SAW Report - Dashboard-Wide AppTest Governance Expansion

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited user-requested repair worker | Domains: Frontend/UI, Backend, Data, Docs/Ops | FallbackSource: existing SAW stamp plus repo hierarchy docs.

RoundID: `ROUND-20260528-DASHBOARD-WIDE-APPTEST-GOVERNANCE-EXPANSION`
ScopeID: `SCOPE-DASHBOARD-WIDE-RENDERED-UI-GOVERNANCE-APPTEST`

## Scope

Repair the Reviewer A/C High finding that rendered dataframe/table governance scanned columns and cells but missed visible pandas index names and index values in Streamlit AppTest `st.dataframe` and `st.table` nodes.

## Ownership

- Implementer: `tests/rendered_governance.py`, `tests/test_dashboard_wide_apptest_governance.py`, this SAW report, and `docs/lessonss.md`.
- Reviewer A: inherited parent blocker on rendered dataframe/table index semantics.
- Reviewer B: runtime/operational boundary recheck through focused boot/governance tests and no write-status path.
- Reviewer C: inherited parent blocker on dataframe/table index data collection.
- Ownership check: PASS. Implementer and reviewer roles are distinct.

## Acceptance Checks

- CHK-01: Rendered table/dataframe collector includes visible pandas index names.
- CHK-02: Rendered table/dataframe collector includes visible pandas index values.
- CHK-03: Regression tests prove forbidden index name `Rank` fails.
- CHK-04: Regression tests prove forbidden index values `Strong Buy`, `BUY`, and `SELL` fail across dataframe/table coverage.
- CHK-05: Existing exact allowed labels and allowed-variant failure behavior remain unchanged.
- CHK-06: Requested focused dashboard-wide/rendered/optimizer AppTest suite passes.
- CHK-07: Requested boot/status/governance/data focused suite passes.
- CHK-08: Governance preflight, runtime-status absence check, `git diff --check`, and `git status --short` are captured without running `--write-status`.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Forbidden action-shaped labels in dataframe/table index names or index values were invisible to rendered governance scans. | Added visible index-name/index-value collection for AppTest dataframe/table pandas values and regression coverage for `Rank`, `Strong Buy`, `BUY`, and `SELL`. | Implementer | RESOLVED |
| None | Existing allowed-label and variant behavior could regress while adding index scanning. | Reused existing scanner path and kept exact allow-list/variant policy unchanged; focused rendered tests pass. | Implementer | PASS |

## Scope Split Summary

in-scope findings/actions: dataframe/table index-name and index-value collection, focused regression tests, verification evidence, SAW report update, and lesson update.

inherited out-of-scope findings/actions: full `dashboard.py` AppTest remains intentionally out of scope; replay output remains uncertified; manual execution scripts remain classified outside default boot.

out-of-scope findings/actions: safe-boot derivation, `SAFE_BOOT_REQUIRED_GATES`, boot write-status logic, broker/order/execution behavior, replay-output certification, provider refresh, ranking/scoring/recommendation semantics, manual execution scripts, and runtime boot-status generation.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `tests/rendered_governance.py` | Added visible dataframe/table index-name and index-value collection, while respecting hidden dataframe index config when AppTest exposes it. | REPAIR_PASS |
| `tests/test_dashboard_wide_apptest_governance.py` | Added synthetic AppTest regression covering forbidden dataframe/table index name/value text. | REPAIR_PASS |
| `docs/lessonss.md` | Updated dashboard-wide rendered-governance lesson with the index-name/index-value miss and guardrail. | REPAIR_PASS |
| `docs/saw_reports/saw_dashboard_wide_apptest_governance_20260528.md` | Reconciled Reviewer A/C High blocker and published repair evidence. | REPAIR_PASS |

## Document Sorting

GitHub-optimized order maintained: tests first for behavior proof, then lesson/report governance artifacts.

## Verification Evidence

| EvidenceID | Command | Result |
|---|---|---|
| EVD-01 | `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_dashboard_wide_apptest_governance.py tests/test_rendered_apptest_governance.py tests/test_optimizer_view.py -q` | PASS, 15 passed, 1 dependency deprecation warning |
| EVD-02 | `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_boot_status_contract.py tests/test_boot_preflight.py tests/test_boot_preflight_governance.py tests/test_data_readiness_gate.py tests/test_data_readiness_gate_write_guard.py -q` | PASS, 122 passed |
| EVD-03 | `E:\Code\Quant\.venv\Scripts\python.exe scripts/governance_preflight.py --repo-root . --json` | PASS, `status=PASS`, `finding_count=0`, GOV-009 PASS |
| EVD-04 | `Test-Path runtime/boot_status_current.json` plus `git status --short -- runtime/boot_status_current.json` | PASS, `runtime/boot_status_current.json` absent and not dirty |
| EVD-05 | `git diff --check` | PASS |
| EVD-06 | `git status --short` | Captured dirty repair files only |
| EVD-07 | Closure packet and SAW report validators | PASS |

## Implementer Task Evidence

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Collect visible dataframe/table index text | `tests/rendered_governance.py` | index names and values enter normal scanner path | PASS | EVD-01 |
| TSK-02 | Add forbidden index regression coverage | `tests/test_dashboard_wide_apptest_governance.py` | `Rank`, `Strong Buy`, `BUY`, `SELL` fail | PASS | EVD-01 |
| TSK-03 | Preserve prior rendered governance behavior | existing rendered tests | allowed labels and dangerous variants still pass/fail as before | PASS | EVD-01 |
| TSK-04 | Preserve boot/governance/runtime boundaries | no runtime status write; no forbidden scope touched | focused boot/data suite and governance preflight pass | PASS | EVD-02/EVD-03/EVD-04 |
| TSK-05 | Capture final hygiene checks | repo diff/status | whitespace and dirty-file inventory captured | PASS | EVD-05/EVD-06 |

TaskEvidenceMap: TSK-01:EVD-01,TSK-02:EVD-01,TSK-03:EVD-01,TSK-04:EVD-02/EVD-03/EVD-04,TSK-05:EVD-05/EVD-06

## Implementer Pass

Implementer pass: PASS. The index collection gap is fixed, focused regressions pass, and runtime status was not generated.

Reviewer A pass: PASS. Strategy/governance semantics are unchanged; the scanner now sees the blocked index text.

Reviewer B pass: PASS. Repair is test-helper/test-only plus docs; boot/status/governance/data focused tests pass and no write-status path ran.

Reviewer C pass: PASS. Dataframe/table text coverage now includes index names and index values without changing dataframe contents or production data paths.

Ownership check: PASS. Implementer and reviewer roles are distinct.

## Validation

ClosureValidation: PASS
SAWBlockValidation: PASS

## Open Risks

Open Risks:

- None for the in-scope index repair.
- Inherited dirty worktree remains expected until the branch is staged/committed; strict `--require-github` boot may still block only on Git cleanliness before commit.
- Full `dashboard.py` AppTest remains intentionally out of scope because prior exploration found top-level side effects.
- Replay output remains intentionally uncertified and was not changed.

Next action: stage/commit the repair after review, then rerun strict `--require-github` boot only from a clean GitHub-aligned state if milestone closure requires it.

## Rollback Note

Revert this branch's changes to `tests/rendered_governance.py`, `tests/test_dashboard_wide_apptest_governance.py`, `docs/lessonss.md`, and this SAW report to return to the prior rendered-governance scope.

ClosurePacket: RoundID=ROUND-20260528-DASHBOARD-WIDE-APPTEST-GOVERNANCE-EXPANSION; ScopeID=SCOPE-DASHBOARD-WIDE-RENDERED-UI-GOVERNANCE-APPTEST; ChecksTotal=8; ChecksPassed=8; ChecksFailed=0; Verdict=PASS; OpenRisks=None; NextAction=stage-commit-repair-after-review
