# AOV-0 First-Seal Custody Re-audit Repair — SAW Receipt

Mode: `CLOSURE_REPORT`
Date: 2026-08-07
RoundID: `ROUND-20260807-AOV0-SEAL-CUSTODY-REAUDIT`
ScopeID: `AOV0-FIRST-SEAL-CUSTODY-V2`
Branch: `codex/pit-source-authority-1`
Working authority: `.worktrees/devspace-053ca7a4f582fb3e`; broken root checkout not repaired

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: owner-directed pre-close custody repair | Domains: Product, Data Provenance, Quant Research, Software Engineering, Governance

## Intent

Close exactly the four prospective-custody findings identified by the 2026-08-07 re-audit without delaying or widening the real CIQ data/seal path:

```text
distinct decision-cut build time + actual seal-write time
+ real next-session/core-open execution validation
+ exact executable-byte custody
+ fresh-process full-chain reopen
→ real Seal #1 can start the prospective clock once real CIQ mapping/market bytes arrive
```

No provider breadth, new research architecture, compatibility fallback, commit, push, real seal, outcome opening, or live-capital action is part of this round.

## Implementer pass

Implemented the bounded custody repair:

- `scripts/aov0_build_decision_cut.py` — destructive `aov0_ciq_decision_cut_v2`; binds `cut_built_at`, `execution_calendar_id=NYSE_2026_CORE_OPEN_0930_ET`, and the exact next 09:30 ET core-open execution timestamp.
- `scripts/aov0_first_seal.py` — independently system-stamps actual prospective `sealed_at`; enforces `knowledge_cutoff <= cut_built_at <= sealed_at < first_eligible_execution_bar`; emits `aov0_executable_byte_manifest_v1`; launches fresh-process reopen automatically.
- `research/aov0/experiment.py` — destructive `aov0_prospective_seal_v2`; binds executable manifest plus current target hashes and serialized target vectors; adds full-chain verifier.
- `scripts/aov0_reopen_seal.py` — separate-process verifier for exact executable/interpreter bytes, seal, decision cut, four Parquets, experiment manifest, run evidence manifests/files, and all five current target vectors.
- Adversarial regressions cover Saturday/wrong-open execution, cut-build-before-knowledge, late seal write, byte drift, target/return mismatch, seal tamper, and fresh-process closure.
- Current truth, PRD/Product Spec, notes, decision log, lessons, active brief/checklist, and generated context were synchronized.

No unrelated local changes were reverted, staged, committed, or pushed.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 scope remains first-seal custody only; no provider/architecture/research widening | PASS |
| CHK-02 `run_4.xlsx` remains sole active 109-company universe + current-cut fundamentals authority; `run_2` stays historical only | PASS |
| CHK-03 decision cut is destructively v2 and owns `cut_built_at`, not prospective seal time | PASS |
| CHK-04 prospective seal independently stamps actual `sealed_at` and requires knowledge <= cut build <= seal < first execution | PASS |
| CHK-05 first execution must equal frozen next `NYSE_2026_CORE_OPEN_0930_ET` bar; Saturday/wrong-open cases fail closed | PASS |
| CHK-06 `aov0_executable_byte_manifest_v1` binds required/loaded repo Python bytes plus exact interpreter bytes/version | PASS |
| CHK-07 experiment manifest retains hashes and canonical serialized values for all five current target vectors | PASS |
| CHK-08 fresh-process verifier closes executable → seal → cut → four Parquets → experiment/evidence manifests/files → target vectors | PASS |
| CHK-09 focused custody/CIQ matrix `36/36 PASS` and explicit separate-process integration returns `FULL_CHAIN_REOPEN_VERIFIED` | PASS |
| CHK-10 full AOV `61/61 PASS`; ZERO-COMPAT seven counters zero | PASS |
| CHK-11 context generation/validation, selected compile, `pip check`, and `git diff --check` | PASS |
| CHK-12 real direct NY Fed SOFR remains admitted; real first-seal probe misses only Rule100 targets, primitives, returns, and decision cut; prospective clock false / financial-alpha evidence zero | PASS |
| CHK-13 no new Capital IQ download exists after 19:00Z at final local probe; no CIQ mapping/market bytes were fabricated or substituted | PASS |
| CHK-14 independent terminal reviewer result exists for exact final custody candidate | BLOCKED — both bounded PRODUCT reviewer launches failed with `failureCode=launch_failed` before findings |

ChecksTotal: 14
ChecksPassed: 13
ChecksFailed: 1

## Reviewer capacity / ownership

The independent reviewer lane was attempted twice against identical candidate/evidence manifest digests:

- candidate manifest SHA-256 `977a1bb3a08d3fb47dc47bb67506718f224efdfb0289f778510aa7b1aff053bf`;
- evidence manifest SHA-256 `9477a6ca6a40e87e68b3eec9ce92878c60082f115b128f9212f67a55b56a0498`;
- attempt 1 → `failed`, `failureCode=launch_failed`, no findings;
- retry → `failed`, `failureCode=launch_failed`, no findings.

Ownership check: implementer and the external reviewer lane are distinct, but no independent Reviewer A/B/C findings can be claimed. Local deterministic evidence is not promoted to independent review. Per owner direction, reviewer availability remains a final-byte closure gate but does not delay the time-sensitive post-close capture/seal attempt.

## Findings

| Severity | Impact | Fix / disposition | Owner | Status |
|---|---|---|---|---|
| Blocking for terminal SAW PASS | No independent review result exists for the exact final custody candidate because both reviewer launches failed before findings. | Re-run independent terminal review against exact final bytes when reviewer capacity is available. | Reviewer lane | Open external |
| Blocking for first real seal, not a code defect | Real Capital IQ primary Security/Trading Item mapping is absent locally. | Export/locate the frozen-universe mapping with actual retrieval time/hash; do not substitute ticker/entity/PERMNO. | Data / Operator | Open live gate |
| Time/data gate for first real seal | Completed same-day CIQ daily total-return/price/volume bytes cannot be admitted before 16:00 America/New_York and are not yet present. | After 16:00 ET export completed market history, record actual retrieval time/hash, and run the ready admission/cut/seal path. | Data / Operator | Open live gate |
| Material inherited finding, resolved | Decision-cut construction time could masquerade as prospective seal time. | v2 cut owns `cut_built_at`; v2 seal independently stamps/validates actual `sealed_at`. | SE / Governance | Closed |
| Material inherited finding, resolved | Chronology-only execution validation could accept non-session timestamps. | Frozen 2026 NYSE next-session 09:30 ET core-open validation; weekend/holiday/wrong-open fail closed. | Quant / SE | Closed |
| Material inherited finding, resolved | Same-process seal self-hash did not prove full artifact closure. | Added automatic separate-process `FULL_CHAIN_REOPEN_VERIFIED` across the complete bound chain. | SE / Governance | Closed |
| Material inherited finding, resolved | Dirty Git SHA did not identify exact executable bytes. | Bind `aov0_executable_byte_manifest_v1` including required/loaded repo code and interpreter bytes. | SE / Governance | Closed |

## Scope split summary

in-scope findings/actions: the four prospective-custody defects, associated adversarial tests, exact current-truth/docs synchronization, and local validation are closed locally.

inherited out-of-scope findings/actions: independent reviewer availability and the external real CIQ mapping/post-close market exports remain open without weakening or substituting data authority.

## Validation / evidence

- `../../tmp/gv25env/Scripts/python.exe -m pytest -q tests/aov0` → `61/61 PASS`.
- focused decision-cut / first-seal / seal / CIQ matrix → `36/36 PASS`.
- explicit fresh-process current-cut integration → `FULL_CHAIN_REOPEN_VERIFIED`.
- ZERO-COMPAT → `0/0/0/0/0/0/0`.
- `scripts/build_context_packet.py` + `--validate` → PASS.
- selected `py_compile` → PASS.
- `python -m pip check` → `No broken requirements found`.
- `git diff --check` → PASS.
- real `scripts/aov0_first_seal.py` probe → `BLOCKED_MISSING_ADMITTED_INPUTS`; only `rule100_targets`, `vertical_primitives`, `total_returns`, `decision_cut` missing; direct SOFR already present; clock false; financial-alpha evidence `0`.
- Chrome download-history copy after `2026-08-07T19:00:00Z` → zero new downloads; no mapping/market export inferred from filesystem metadata.

## Critical executable hashes

- `research/aov0/experiment.py` — `80d9d0d23b9d9314d22446b1e167c7e1cd7c86daa90505be747211216c5f310c`
- `scripts/aov0_build_decision_cut.py` — `645f2eb97103ca8e2ca083a3e5ecbc5c33f1389be0db392a0ddb3791783cf9c0`
- `scripts/aov0_first_seal.py` — `53586c1e851b038bbe2a43fa2593e81ffa7638562aec92a8f8ed3eed18705aab`
- `scripts/aov0_reopen_seal.py` — `b3246244b70b0d6313da7372d3f838c8994e31d1cb35125dc52c27829d27732f`
- `tests/aov0/test_decision_cut_builder.py` — `5c970e524f2eb4419e04ee73c0011f0a93fc83d80b7b2e873a9cc6582a1c26f6`
- `tests/aov0/test_first_seal_entrypoint.py` — `8b24144e3627dc39503a1fcc1ebd81cad3ac8f369cd510543cb0f68b1128d752`
- `tests/aov0/test_experiment_seal.py` — `0c1208145aaca9b8de2ec1839eb3286844fce818e8ac0fb269016fe0762f545f`
- `tests/aov0/test_ciq_market.py` — `3a3fec082dd18eae8be4c715d46c5a41c598e630d115ab723a590d90bef46105`

## Document Changes Showing

| Path group | Change summary | Reviewer status |
|---|---|---|
| `scripts/aov0_build_decision_cut.py`, `scripts/aov0_first_seal.py`, `scripts/aov0_reopen_seal.py`, `research/aov0/experiment.py` | v2 timing/calendar/executable/full-chain prospective custody | local PASS; independent reviewer unavailable |
| four focused AOV test files | adversarial timing/calendar/byte/fresh-process regressions | local PASS; independent reviewer unavailable |
| PRD / PRODUCT_SPEC / current context / active brief / checklist / notes / lessons / decision log | synchronize closed local custody findings and remaining real-data-only blocker | context validator PASS; independent reviewer unavailable |
| `docs/saw_reports/saw_aov0_seal_custody_reaudit_20260807.md` | terminal evidence receipt for this round | terminal artifact; no recursive SAW |

## Score / claim boundary

Canonical accepted product maturity remains `70/100`. `prospective_clock_started=false`, `financial_alpha_evidence=0`, and Limited Live remains closed. The custody repair improves prospective integrity/readiness but creates no empirical alpha evidence and no real seal.

## Open Risks

Open Risks: independent terminal reviewer unavailable for exact final custody bytes; real Capital IQ primary Security/Trading Item mapping absent; completed post-16:00 ET primary-security market export absent; external Episode-2 push/hosted/publication custody remains separate.

## Next action

Next action: do not add architecture. At/after the live gate, admit only real CIQ Security/Trading Item mapping + completed post-16:00 ET market bytes with explicit retrieval times/hashes; run the ready CIQ builder; build `aov0_ciq_decision_cut_v2` with first execution `2026-08-10T13:30:00Z`; run Seal #1; require actual seal-write timestamp, executable-byte binding, `SEALED_NOT_OPENED`, and automatic fresh-process `FULL_CHAIN_REOPEN_VERIFIED`. Re-run independent review when capacity returns without delaying the data capture/seal.

ClosurePacket: RoundID=ROUND-20260807-AOV0-SEAL-CUSTODY-REAUDIT; ScopeID=AOV0-FIRST-SEAL-CUSTODY-V2; ChecksTotal=14; ChecksPassed=13; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent reviewer launch failed twice | real CIQ primary-security mapping and post-16:00 market bytes remain external; NextAction=admit only real CIQ mapping and completed market bytes then build v2 cut run Seal1 and require fresh-process full-chain reopen
ClosureValidation: PASS
SAWBlockValidation: PASS
