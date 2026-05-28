# SAW Report - Rendered Governance Boot Preflight Wiring

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited user-requested subagents | Domains: Frontend/UI, Backend, Data, Docs/Ops | FallbackSource: existing SAW stamp plus repo hierarchy docs.

RoundID: `ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING`
ScopeID: `SCOPE-RENDERED-APPTEST-GOVERNANCE-AS-STRICT-BOOT-GATE`

## Scope

Wire rendered AppTest governance into the existing strict Portfolio AppTest smoke gate, tighten the rendered-only label policy for the latest forbidden labels, and keep safe-boot derivation, replay-output state, execution inventory, and runtime status writes unchanged.

## Ownership

- Implementer: rendered policy update, optimizer header copy, boot-preflight smoke wiring, failure regression, SAW/lesson docs.
- Reviewer A: governance wording and label-policy overclaim risk.
- Reviewer B: runtime and operational mutation risk.
- Reviewer C: rendered dataframe/test robustness and performance path.
- Ownership check: implementer and reviewer roles are distinct in this report.

## Acceptance Checks

- CHK-01: Existing Portfolio AppTest smoke command includes `tests/test_rendered_apptest_governance.py`.
- CHK-02: Existing Portfolio AppTest smoke command includes the optimizer rendered-label governance companion test.
- CHK-03: Strict `--smoke --run-focused-contract --write-status` blocks status writing when the rendered smoke command fails.
- CHK-04: Rendered governance forbids `Entry/Exit Strategy`, `Portfolio Optimizer`, standalone `BUY`, standalone `SELL`, rank/score labels, and prior broker/action/recommendation terms.
- CHK-05: Exact research-only rendered labels still pass, and dangerous variants still fail.
- CHK-06: Optimizer rendered header uses `Research Optimizer - Simulation Only` and no longer renders `Portfolio Optimizer`.
- CHK-07: Focused rendered/AppTest tests pass.
- CHK-08: Boot/status/governance/data focused tests pass.
- CHK-09: Governance preflight and strict safe boot pass without `--write-status`.
- CHK-10: `git diff --check`, closure packet validation, SAW report validation, and SE evidence validation pass.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Rendered governance was test-owned but not part of strict boot smoke evidence. | Added the rendered suite and optimizer rendered-label test to `PORTFOLIO_APPTEST_SMOKE_COMMAND`; added a failure regression that blocks status writes. | Implementer | PASS |
| High | Latest rendered-label policy forbids `Entry/Exit Strategy` and `Portfolio Optimizer`, while prior rendered tests allowed them. | Removed `Entry/Exit Strategy` from rendered allow-list, added both labels to rendered forbidden phrases, and renamed the optimizer header to `Research Optimizer - Simulation Only`. | Implementer | PASS |
| High | Standalone `BUY`/`SELL` were not caught as bare rendered labels. | Added exact standalone forbidden labels for `BUY` and `SELL` to avoid substring false positives. | Implementer | PASS |
| None | Safe-boot semantics, write gate, GOV-009 execution inventory, and replay output status. | No changes made. | Implementer | PASS |

## Scope Split Summary

in-scope findings/actions: boot-smoke command wiring, rendered-only label policy tightening, optimizer rendered header copy, boot-preflight regression, SAW report, and lesson entry.

inherited out-of-scope findings/actions: replay output remains intentionally uncertified; manual execution scripts remain classified outside default boot; dashboard-wide AppTest remains deferred.

out-of-scope findings/actions: runtime boot-status regeneration, safe-boot derivation changes, execution inventory changes, replay-output certification, broker/order/recommendation/ranking/scoring/action-alert behavior, and provider refresh during boot.

## Document Changes Showing

| Path | Change Summary | Reviewer Status |
|---|---|---|
| `scripts/boot_preflight.py` | Added rendered governance suite and optimizer rendered-label companion test to existing Portfolio AppTest smoke command. | PASS |
| `tests/rendered_governance.py` | Tightened rendered policy for `Entry/Exit Strategy`, `Portfolio Optimizer`, standalone `BUY`/`SELL`, and preserved exact safe-label variant guard. | PASS |
| `tests/test_rendered_apptest_governance.py` | Added strict policy regressions for latest forbidden rendered labels and preserved allowed/variant behavior. | PASS |
| `tests/test_boot_preflight.py` | Added strict smoke failure regression proving rendered governance failure blocks status writing. | PASS |
| `views/optimizer_view.py` | Renamed rendered optimizer header to `Research Optimizer - Simulation Only`. | PASS |
| `tests/test_optimizer_view.py` | Updated optimizer AppTest expectations for research-only header and rendered governance safety. | PASS |
| `docs/lessonss.md` | Added guardrail for wiring rendered governance into boot evidence and resolving label policy conflicts before enforcement. | PASS |
| `docs/saw_reports/saw_rendered_governance_boot_preflight_wiring_20260528.md` | Published this SAW report. | PASS |

## Verification Evidence

| EvidenceID | Command | Result |
|---|---|---|
| EVD-01 | `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_rendered_apptest_governance.py tests/test_optimizer_view.py -q` | PASS, 11 passed |
| EVD-02 | `E:\Code\Quant\.venv\Scripts\python.exe -m pytest tests/test_boot_status_contract.py tests/test_boot_preflight.py tests/test_boot_preflight_governance.py tests/test_data_readiness_gate.py tests/test_data_readiness_gate_write_guard.py -q` | PASS |
| EVD-03 | `E:\Code\Quant\.venv\Scripts\python.exe scripts/governance_preflight.py --repo-root . --json` | PASS |
| EVD-04 | `E:\Code\Quant\.venv\Scripts\python.exe scripts/boot_preflight.py --repo-root . --mode strict --require-github --smoke --run-focused-contract` | PASS, runtime status not written |
| EVD-05 | `git diff --check` | PASS |
| EVD-06 | Closure packet, SAW report, and SE evidence validators | PASS |

## SE Task Evidence

| TaskID | Task | Artifact | Check | Status | EvidenceID |
|---|---|---|---|---|---|
| TSK-01 | Wire rendered governance into existing smoke gate | `scripts/boot_preflight.py` | strict smoke command includes rendered suite and optimizer rendered-label test | PASS | EVD-02 |
| TSK-02 | Add fail-closed boot regression | `tests/test_boot_preflight.py` | rendered smoke failure blocks `--write-status` artifact creation | PASS | EVD-02 |
| TSK-03 | Tighten rendered label policy | `tests/rendered_governance.py`, `tests/test_rendered_apptest_governance.py` | latest forbidden labels fail; research-only labels pass; variants fail | PASS | EVD-01 |
| TSK-04 | Rename optimizer rendered header | `views/optimizer_view.py`, `tests/test_optimizer_view.py` | optimizer AppTest renders research-only header and passes governance scan | PASS | EVD-01 |
| TSK-05 | Preserve strict governance/safe-boot baseline and publish closeout | docs and validation artifacts | governance preflight, strict safe boot, validators pass | PASS | EVD-03/EVD-04/EVD-06 |

TaskEvidenceMap: TSK-01:EVD-02,TSK-02:EVD-02,TSK-03:EVD-01,TSK-04:EVD-01,TSK-05:EVD-06
EvidenceRows: EVD-01|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z;EVD-02|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z;EVD-03|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z;EVD-04|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z;EVD-05|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z;EVD-06|ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING|2026-05-28T11:15:24Z

## Reviewer Passes

Implementer pass: PASS. Rendered governance is now part of strict Portfolio AppTest smoke evidence and latest rendered-label policy is enforced.

Reviewer A pass: PASS. The branch resolves the policy conflict by forbidding `Entry/Exit Strategy` and `Portfolio Optimizer` in rendered governance while keeping allowed research-only labels exact and variant-guarded.

Reviewer B pass: PASS. Runtime status was not regenerated, safe-boot derivation and write-status gate were not changed, and strict preflight stayed read-only.

Reviewer C pass: PASS. Dataframe/table coverage remains intact, bare `BUY`/`SELL` exact matching avoids substring false positives, and the added smoke command is bounded to the existing AppTest path.

Ownership check: PASS. Implementer and reviewer roles are distinct in the SAW reconciliation model for this round.

## Validation

ClosureValidation: PASS
SAWBlockValidation: PASS
EvidenceValidation: PASS

## Open Risks

Open Risks:

- Dashboard-wide AppTest remains intentionally deferred because `dashboard.py` has heavy top-level runtime/provider behavior.
- Replay output remains intentionally uncertified.
- Manual execution scripts remain classified outside default boot, not removed.
- The rendered governance helper remains a test helper; broader product UI surfaces need explicit AppTest expansion before broader claims.

Next action: review/merge `codex/rendered-governance-boot-preflight-wiring`, then either expand dashboard-wide AppTest coverage or start the next research-only feature.

## Rollback Note

Revert this branch's rendered governance boot-wiring commit if the strict smoke gate needs to return to the prior narrower optimizer AppTest suite.

ClosurePacket: RoundID=ROUND-20260528-RENDERED-GOVERNANCE-BOOT-PREFLIGHT-WIRING; ScopeID=SCOPE-RENDERED-APPTEST-GOVERNANCE-AS-STRICT-BOOT-GATE; ChecksTotal=10; ChecksPassed=10; ChecksFailed=0; Verdict=PASS; OpenRisks=dashboard-wide-apptest-deferred_replay-output-remains-intentionally-uncertified_manual-execution-scripts-remain-classified-outside-default-boot_rendered-helper-needs-explicit-expansion-for-broader-ui-surfaces; NextAction=review-merge-rendered-governance-boot-preflight-wiring-then-choose-dashboard-wide-apptest-or-next-research-feature
