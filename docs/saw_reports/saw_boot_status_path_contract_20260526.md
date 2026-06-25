# SAW Boot Status Path Contract - 2026-05-26

SAW Verdict: BLOCK
Hierarchy Confirmation: Approved | Session: current-thread | Trigger: persisted-fallback | Domains: Terminal Zero / Backend, Frontend/UI, Data, Ops | FallbackSource: docs/spec.md + docs/phase_brief/phase65-brief.md
RoundID: ROUND-20260526-BOOT-STATUS-PATH-CONTRACT
ScopeID: SCOPE-CANONICAL-BOOT-STATUS-PATH-AND-WRITER

## Scope

In-scope: lock one canonical executable boot-status path, reconcile boot-status readers/writers/tests/docs to that path, preserve Governance Gate v0 integration, and report root boot readiness truthfully.

Inherited / out-of-scope: broad dirty-worktree staging, generated runtime boot-status publication, clean GitHub safe-boot proof, durable selected-asset freshness certification, durable PortfolioReplaySelection certification, rendered dataframe governance scan, and full broker/order inventory.

## Acceptance Checks

- CHK-01 All live executable path sentinels report `runtime/boot_status_current.json` as canonical.
- CHK-02 `docs/context/boot_status_current.json` is not a default reader fallback or allowed writer.
- CHK-03 Strict preflight writes boot status only with `--write-status`, only after PASS, and only to runtime.
- CHK-04 Boot/data/governance focused tests pass.
- CHK-05 Governance scanner remains PASS with GOV-000 root application proven.
- CHK-06 Data readiness strict has no blockers; WARN-only residuals are recorded.
- CHK-07 Stale docs/context path-authority language is removed from docs/context policy surfaces.
- CHK-08 Strict `--require-github` truth is recorded without claiming boot-ready.

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | Executable and test contracts were runtime-canonical, but docs/context policy surfaces still described `docs/context/boot_status_current.json` as canonical/allowed. | Patched BOOT.md, architecture docs, taxonomy, and route contract; reran focused tests, stale-authority grep, and import sentinel. | Boot/Ops owner | Fixed |
| High | BootReady cannot be claimed because strict `--require-github` fails on dirty source/test/runtime files. | Preserve blocker; classify/stage/commit or park inherited dirty files in a separate round before safe-boot proof. | Ops/release owner | Open / inherited |
| Medium | Data readiness strict remains WARN for durable selected assets and durable replay selection. | Keep WARN as non-blocking for this path-contract round; resolve in data-readiness certification slice. | Data/Ops owner | Open / inherited |
| Medium | Reviewer C initially returned BLOCK because docs-as-code was stale. | Reconciled docs and reran evidence after reviewer finding. | Parent reconciler | Fixed |

## Scope Split Summary

In-scope fixed: runtime-only canonical path in code/tests/docs, no docs/context fallback, runtime-only allowed boot write, governance scanner PASS preserved, data-readiness policy JSON aligned to runtime path.

Inherited out-of-scope findings/actions: dirty source/test/runtime worktree blocks strict GitHub proof; data readiness WARNs remain for durable selected assets and replay selection; rendered-output governance and execution-module broker/order inventory remain future hardening.

## Subagent Review Summary

Implementer pass: parent applied the path-contract reconciliation and preserved runtime-only writer/reader behavior without touching dashboard, optimizer, replay, or strategy semantics.

Reviewer A: Kant inventory pass confirmed runtime canonical executable state, no active docs/context fallback, and governance integration active. It identified stale tests/docs before reconciliation.

Reviewer B: Locke governance pass confirmed boot preflight imports/runs Governance Gate v0, boot-control tests include governance tests, GOV-000 has no missing root items, and scanner output is PASS.

Reviewer C: Tesla data-integrity pass initially BLOCKED on stale docs-as-code. Parent patched the docs/context contract surfaces and reran focused proof. Reviewer C's in-scope High finding is fixed.

Ownership check: PASS. Implementer/reconciler and Reviewer A/B/C were separate agents or passes; parent performed final reconciliation.

## Verification Evidence

- EVD-01: runtime sentinel -> `core.boot_status.DEFAULT_BOOT_STATUS_PATH=runtime\boot_status_current.json`, `scripts.boot_preflight.DEFAULT_STATUS_JSON=runtime\boot_status_current.json`, `core.data_readiness_gate.ALLOWED_BOOT_WRITES=['runtime/boot_status_current.json']`, no `LEGACY_BOOT_STATUS_PATH`.
- EVD-02: `.venv\Scripts\python -m pytest tests\test_boot_status_contract.py tests\test_boot_preflight.py tests\test_data_readiness_gate_write_guard.py -q` -> PASS, 40 passed.
- EVD-03: `.venv\Scripts\python -m pytest tests\test_boot_preflight.py tests\test_boot_preflight_governance.py tests\test_boot_status_contract.py tests\test_data_readiness_gate.py tests\test_data_readiness_gate_write_guard.py -q` -> PASS, 92 passed.
- EVD-04: `.venv\Scripts\python scripts\governance_preflight.py --repo-root . --json` -> PASS, finding_count=0.
- EVD-05: `.venv\Scripts\python scripts\run_data_readiness_gate.py --strict` -> exit 0, `overall_status=WARN`, no blockers, allowed write path runtime.
- EVD-06: `.venv\Scripts\python scripts\boot_preflight.py --repo-root . --mode strict --require-github --no-tests --json` -> FAIL because unclassified source/test/runtime dirty files are present and `--require-github` requires a clean worktree; governance PASS, boot_core PASS, HEAD aligned.
- EVD-07: `.venv\Scripts\python -m py_compile core\boot_status.py core\data_readiness_gate.py scripts\boot_preflight.py scripts\governance_preflight.py scripts\run_data_readiness_gate.py tests\test_boot_status_contract.py tests\test_data_readiness_gate_write_guard.py tests\test_boot_preflight.py tests\test_boot_preflight_governance.py` -> PASS.
- EVD-08: stale-authority grep over BOOT.md, docs/architecture, docs/context policy JSON, tests, core, and scripts -> no stale docs/context canonical/write/fallback authority remains; remaining docs/context hits label it noncanonical.

## Document Changes Showing

- `docs/architecture/boot_preflight_contract.md` - runtime is the only durable v0 boot-status output; docs/context is snapshot-only; reviewer status: fixed after Reviewer C.
- `docs/architecture/data_readiness_gate_v0.md` - allowed boot write and canonical payload changed to runtime path; reviewer status: fixed after Reviewer C.
- `docs/context/data_artifact_taxonomy_current.json` - allowed boot writes and boot artifact entry changed to runtime path; reviewer status: fixed.
- `docs/context/portfolio_allocation_route_contract_v0.json` - allowed boot writes changed to runtime path; reviewer status: fixed.
- `BOOT.md` - operator landing page points generated status to runtime path; reviewer status: fixed.
- `docs/lessonss.md` - appended docs-as-code path-contract guardrail; reviewer status: updated.
- `docs/decision log.md` - added path-contract SAW reconciliation record; reviewer status: updated.
- `docs/saw_reports/saw_boot_status_path_contract_20260526.md` - this SAW closure report; reviewer status: generated.

## Document Sorting

GitHub-optimized order maintained for reported docs: operator/architecture contracts first, context policy JSON next, then lessons, decision log, and SAW report. No formulas or strategy derivations changed.

## High-Value Follow-Ups

1. Freeze or finish the inherited dirty source/test/runtime buckets before rerunning `--require-github`.
2. Resolve data-readiness WARNs for durable selected-asset freshness and durable PortfolioReplaySelection certification.
3. Generate `runtime/boot_status_current.json` only after strict PASS, then commit/push and run read-only GitHub proof.
4. Add rendered dataframe/AppTest governance scan after runtime stability.
5. Add full execution-module broker/order inventory gate after rendered scan.

## Top-Down Snapshot

L1: Terminal Zero Boot/Governance Control Plane
L2 Active Streams: Ops, Backend, Data
L2 Deferred Streams: Frontend/UI rendered scan, execution broker/order inventory, strategy feature staging
L3 Stage Flow: Planning -> Executing -> Iterate Loop -> Final Verification -> CI/CD
Active Stream: Ops
Active Stage Level: L3

+--------------------+----------------------+--------+--------------------------------------------------------------+
| Stage              | Current Scope        | Rating | Next Scope                                                   |
+--------------------+----------------------+--------+--------------------------------------------------------------+
| Planning           | B:path/OH:single/AC  | 95/100 | Dirty bucket closure [95/100]: required for GitHub proof     |
| Executing          | Path contract fixed  | 90/100 | Preserve runtime-only path [92/100]: prevents snapback       |
| Iterate Loop       | Focused tests pass   | 88/100 | Data WARN certification [82/100]: reduces degraded status    |
| Final Verification | Strict dirty BLOCK   | 55/100 | Clean worktree proof [95/100]: gates boot-ready              |
| CI/CD              | Not attempted        | 20/100 | Stage clean boot bucket [85/100]: required before safe boot  |
+--------------------+----------------------+--------+--------------------------------------------------------------+

## Open Risks

Open Risks: dirty-source-test-runtime-worktree-blocks-require-github; data-readiness-selected-assets-and-replay-certification-WARN; canonical-runtime-status-not-generated-from-strict-PASS; rendered-governance-scan-missing; execution-module-broker-order-inventory-missing.

Next action: classify and close the dirty source/test/runtime worktree bucket, rerun strict preflight, resolve data-readiness WARNs if strict boot policy requires them, then generate canonical `runtime/boot_status_current.json` only after strict PASS.

Evidence:
- Runtime path sentinels, focused tests, governance scanner, data-readiness strict, py_compile, stale-authority grep, and strict preflight truth check were run.

Assumptions:
- Dirty files are inherited local context and must not be reverted in this round.
- Data readiness WARN-only state is acceptable evidence for this narrow path-contract round but not a boot-ready claim.

Open Risks:
- Strict `--require-github` remains blocked by dirty worktree.
- Canonical runtime boot status was intentionally not generated because strict preflight did not pass.

Rollback Note:
- Revert only this round's path-contract edits if needed: `core/boot_status.py`, `core/data_readiness_gate.py`, `scripts/boot_preflight.py`, `tests/test_boot_status_contract.py`, `tests/test_boot_preflight.py`, `tests/test_data_readiness_gate_write_guard.py`, `BOOT.md`, `docs/architecture/boot_preflight_contract.md`, `docs/architecture/data_readiness_gate_v0.md`, `docs/context/data_artifact_taxonomy_current.json`, `docs/context/portfolio_allocation_route_contract_v0.json`, `docs/lessonss.md`, `docs/decision log.md`, and this SAW report. Do not revert unrelated dirty worktree context.

ClosurePacket: RoundID=ROUND-20260526-BOOT-STATUS-PATH-CONTRACT; ScopeID=SCOPE-CANONICAL-BOOT-STATUS-PATH-AND-WRITER; ChecksTotal=8; ChecksPassed=7; ChecksFailed=1; Verdict=BLOCK; OpenRisks=dirty-source-test-runtime-worktree-blocks-require-github,data-readiness-WARN,canonical-runtime-status-not-generated,rendered-governance-scan-missing,execution-broker-order-inventory-missing; NextAction=classify-close-dirty-worktree-rerun-strict-preflight-then-generate-runtime-status-after-pass
ClosureValidation: PASS
SAWBlockValidation: PASS
