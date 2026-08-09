# SAW — Lane 2 Excel/CIQ Recovery and Source-Blocker Return — 2026-08-09

SAW Verdict: BLOCK

RoundID: `ROUND-20260809-LANE2-EXCEL-CIQ-RECOVERY`
ScopeID: `LANE2_PROVIDER_HOST_RECOVERY_AND_SOURCE_BLOCKER_RETURN`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Financial, Quant Research, Data Engineering, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/lane2_status_20260809.md`

## Scope

Resume Lane 2 from the failed market-backfill host checkpoint, recover Excel/CIQ without broad process killing, attempt exactly bounded `part_001` recovery behind coverage gates, stop on repeated sparse host failure, preserve zero financial authority, and return the lane to its formal historical source-authority blockers.

### Acceptance checks

| Check | Requirement | Result |
|---|---|---|
| CHK-01 | Clean failed-trial Excel by exact ownership/PID and finish with no Excel process left | PASS |
| CHK-02 | Separate unstable `SPGMI.ExcelShell` from core CIQ and restore the core add-in only through exact backed-up Resiliency repair | PASS |
| CHK-03 | Land a new `part_001` with at least 40 entities and 200 rows before any wider backfill | FAIL — repeated one-row collapse; no file written |
| CHK-04 | Stop further SPGTable retries after repeated real sparse/non-pending one-row output | PASS |
| CHK-05 | Preserve backfill custody and reverify the last good part | PASS — 1/34; part_000 = 530 rows / 76 entities |
| CHK-06 | PowerShell parse and `git diff --check` for round-owned tooling edits | PASS |
| CHK-07 | Historical risk-set/reconstruction/Xpress/security-master admission tests remain green | PASS — 18 targeted tests |
| CHK-08 | Independent Reviewer A — strategy correctness/regression | FAIL — independent reviewer channel unavailable in this execution surface |
| CHK-09 | Independent Reviewer B — runtime/operational resilience | FAIL — independent reviewer channel unavailable in this execution surface |
| CHK-10 | Independent Reviewer C — data integrity/performance | FAIL — independent reviewer channel unavailable in this execution surface |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Material | The Office-Tools migration shell and the core CIQ formula add-in were treated as one health surface, so disabling/recovering one could accidentally remove the other. | Added a per-user `SPGMI.ExcelShell LoadBehavior=0` override and verified shell `Connect=False` while core SNL CIQ remained independently `Connect=True` with a live object. | Lane 2 worker | CLOSED |
| Material | Office Resiliency silently re-quarantined the core SNL CIQ add-in after a crash, producing fresh Excel hosts with `Object=null`. | Matched the new `DisabledItems` bytes to the existing backed-up SNL core payload, exported the current registry key, cleared only that exact core entry, and reverified `CIQ_READY`. | Lane 2 worker | CLOSED for current host; recurrence risk remains |
| Material | Real SPGTable capture can remain COM-live and non-pending while populating only one entity row, so smoke success or `pending=0` can falsely look healthy. | Kept fail-closed filled/coverage gates, verified individual cells equal bulk `Range.Value2`, added single-writer/date-batch hardening, and stopped after repeated one-row collapse. | Lane 2 worker | OPEN provider-host risk; capture quarantined |
| Material | The old 2023 market backfill could consume more provider time even though it is no longer the formal A1 first blocker. | Preserved 1/34 custody and moved active work back to historical risk-set then same-date primary-identity authority. | Lane 2 worker | CLOSED |
| Material | Historical high-growth membership cannot be acquired through the prepared Xpress path without provider authorization. | Verified fail-closed reconstruction code/tests and checked the execution environment; `SPGLOBAL_XPRESSAPI_TOKEN` is absent and no pre-landed Xpress artifacts exist. | Lane 2 / provider handoff | OPEN |
| Material | Mandatory independent Reviewer A/B/C evidence is unavailable, so terminal SAW PASS cannot be claimed. | Preserve deterministic evidence and rerun independent strategy/runtime/data review when a reviewer channel is available. | Closeout lane | OPEN |

## Scope split summary

**in-scope:** exact-PID host cleanup, Office-Tools/core-CIQ separation, exact SNL Resiliency recovery, bounded 10-name/5-name/date-subbatch capture attempts, cell-vs-range sparse verification, capture stop rule, provider-tool hardening, backfill custody verification, current-truth/lesson sync, and targeted historical-source admission tests are complete.

**inherited / next-scope:** a provider-verifiable historical high-growth risk set, then the same-date historical primary Security/Trading Item mapping, formal A1 economics, A2 freeze/query, prospective Clock outcomes, and any financial-alpha uplift remain outside this recovery slice. The older 2023 market backfill remains diagnostic/continuity work and is quarantined for this round.

## Ownership check

Implementer = current Lane-2 worker. Reviewer A/B/C cannot be instantiated as distinct independent agents through the available execution tools in this session. Implementer validation is not substituted for reviewer evidence; CHK-08..CHK-10 therefore fail and SAW remains BLOCK.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `tmp/aov0_backfill_quarantine_session.ps1` | Replace unstable `New-Object` boot with isolated `/x` + ROT custody; refuse pre-existing Excel; exact owned-PID cleanup; verify Office-Tools shell disconnected; bounded polling | Parse PASS; A/B/C unavailable |
| `tmp/aov0_backfill_attach_live.ps1` | Add single-writer mutex/transcript, bounded polling, and 2-day sub-batching while retaining fail-closed part coverage | Parse PASS; runtime attempt rejected sparse host output; A/B/C unavailable |
| `tmp/excel_spgtable_shape_probe.ps1` | New bounded shape diagnostic for entity/date SPGTable expansion | Parse PASS; A/B/C unavailable |
| `docs/phase_brief/lane2_status_20260809.md` | Record shell/core separation, Resiliency recovery, one-row collapse evidence, final host cleanup and stop rule | Local scope check PASS |
| `docs/lessonss.md` | Add operating law for exact CIQ Resiliency repair and repeated one-row collapse | Local scope check PASS |
| `docs/saw_reports/saw_lane2_excel_ciq_recovery_20260809.md` | Publish this terminal round evidence | Terminal SAW artifact |

## Validation evidence

- Failed-trial PID `23804` was ownership-checked and removed exactly; later residual `/automation -Embedding` / `/x` Excel processes were tied to this round before exact cleanup. Final state: `EXCEL_CLEAR`.
- Quark remains disabled. `SPGMI.ExcelShell` final per-user `LoadBehavior=0`; final `DisabledItems` count `0`.
- Core CIQ recovery: `CIQ_ADDIN connect=True objectNull=False`; shell verification: `SPGMI_CONNECT=False`.
- 5×2 diagnostic returned real values for 4/5 names. Shape diagnostics briefly returned 10×2=`54` cells / 9 entities, 20×2=`90` / 15, 25×2=`118` / 20.
- Real capture failures: 10×7=`21` filled vs 52 minimum; 5×7=`21` vs 26; 25×2 date-subbatch=`6` vs 37. Post-failure individual-cell count and bulk-range count were both exactly `6`, all on row 8.
- No `part_001` exists. `part_000_20230814_20230822.csv` reverified at 530 rows / 76 entities, SHA-256 `24d24848388a66d7183804c4ad1a5f932371563be04d92225c5e1dafba123c31`.
- PowerShell parser: zero errors for the two modified capture scripts and the new shape probe. `git diff --check` on round-owned tooling paths passed.
- Historical-source admission validation: `18` targeted tests green across `test_historical_risk_set.py`, `test_historical_screen_reconstruction.py`, `test_xpressapi_historical_screen.py`, and `test_historical_security_master.py`.
- Xpress acquisition environment: `SPGLOBAL_XPRESSAPI_TOKEN_PRESENT=False`; no pre-landed Xpress candidate/source artifacts found under `data/aov0`.
- No A1/A2 admission claimed; no prospective outcome opened; Parent/Child authority was not mutated; `financial_alpha_evidence=0` remains the operating law.
- No commit, stage, or push was performed.

## Open Risks:

1. Excel/CIQ can degrade to a COM-live, non-pending one-row SPGTable collapse after apparently healthy micro probes; unattended market backfill remains unsafe.
2. The first formal A1 source blocker is still external: no provider-verifiable historical high-growth membership is landed, and the prepared Xpress route lacks an authorization token in the current environment.
3. Independent Reviewer A/B/C evidence is unavailable, preventing terminal SAW PASS.

## Next action:

Obtain the provider-verifiable historical high-growth start risk set first — either by supplying/activating authorized XpressAPI access for the prepared historical-market/reconstruction path or by producing a direct CIQ historical screener snapshot with mechanically bound effective date and hash-bound membership. Only then acquire historical primary Security/Trading Item identity for exactly that admitted cohort.

ClosurePacket: RoundID=ROUND-20260809-LANE2-EXCEL-CIQ-RECOVERY; ScopeID=LANE2_PROVIDER_HOST_RECOVERY_AND_SOURCE_BLOCKER_RETURN; ChecksTotal=10; ChecksPassed=6; ChecksFailed=4; Verdict=BLOCK; OpenRisks=CIQ_one_row_collapse_historical_risk_set_source_missing_reviewers_unavailable; NextAction=Obtain_provider_verifiable_historical_start_risk_set_then_matching_primary_identity

ClosureValidation: PASS

SAWBlockValidation: PASS
