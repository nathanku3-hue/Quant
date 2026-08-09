# SAW — Lane 2 Historical PIT Takeover — 2026-08-09

SAW Verdict: BLOCK

RoundID: `ROUND-20260809-LANE2-HISTORICAL-TAKEOVER`
ScopeID: `LANE2_A1_SOURCE_AUTHORITY_PARITY_HARDENING`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Financial, Quant Research, Data Engineering, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/lane2_status_20260809.md`

## Scope

Advance Lane 2 toward admitted historical A1 without weakening the historical/prospective authority boundary: close fundamental-vintage and current↔historical replay parity, harden historical primary-identity admission and restartable CIQ acquisition, bank bounded diagnostic provider evidence, and leave A1/A2 fail-closed until exact historical source authority exists.

### Acceptance checks

| Check | Requirement | Result |
|---|---|---|
| CHK-01 | Preserve `financial_alpha_evidence=0`, sealed Clock #1, and unchanged Parent/Child authority | PASS |
| CHK-02 | Freeze one active historical fundamental vintage and demote competing legacy semantics | PASS — `CIQ SPG historical as-of + FilingVer=Original` |
| CHK-03 | Formal A1 requires hash-bound historical primary Security/Trading Item identity for exact historical risk-set membership | PASS |
| CHK-04 | Transition planning and provider driver fail closed before partial/invalid acquisition advances | PASS |
| CHK-05 | Historical weekly decisions use exact current-cut AOV builder with same-input parity | PASS |
| CHK-06 | Decision-cut cube activates next observed close and canonical five-arm experiment runs | PASS |
| CHK-07 | Current-109 provider captures remain explicitly diagnostic; invalid identity/screen shortcuts rejected | PASS |
| CHK-08 | Full `tests/aov0` regression | PASS — 120 tests collected and green |
| CHK-09 | PowerShell parse, selected Python compile, and `git diff --check` | PASS |
| CHK-10 | Independent Reviewer A — strategy correctness/regression | FAIL — fresh reviewer launch failed twice (`launch_failed`) |
| CHK-11 | Independent Reviewer B — runtime/operational resilience | FAIL — fresh reviewer launch failed twice (`launch_failed`) |
| CHK-12 | Independent Reviewer C — data integrity/performance | FAIL — fresh reviewer launch failed twice (`launch_failed`) |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Material | A historical company cohort could otherwise be mapped through a later/current primary security, creating identity hindsight. | Added fail-closed historical-primary receipt contract and bound it into A1 admission/A2 freeze. | Lane 2 worker | CLOSED |
| Material | Historical replay duplicated current Q/U, eligibility, technical, sizing and softmax logic and left cube state on decision dates while weights activated next session. | Route each historical decision through the exact current-cut builder and freeze the resulting cube state onto next-session activation. | Lane 2 worker | CLOSED |
| Material | CLI transition planner admitted missing FQ0 states that the authoritative replay engine later rejected, risking wasted CIQ queries. | Delegate CLI planning to the authoritative transition planner; missing FQ0 now stops before provider spend. | Lane 2 worker | CLOSED |
| Material | Provider COM/transport failure can occur after a valid atomic output lands, while the old driver could also advance from partial capture assumptions. | Default to one-date/one-transition chunks and verify exact expected file/row custody before any advance. | Lane 2 worker | CLOSED |
| Material | Terminal independent A/B/C review evidence is unavailable, so this code/provider/data round cannot claim terminal SAW PASS. | Preserve deterministic validation evidence and rerun fresh A/B/C review when review launch capacity is available; do not substitute implementer tests for independent review. | Closeout lane | OPEN |
| Material (next-scope blocker) | Exact historical high-growth screener membership at A1 start is not yet provider-verifiable. | Obtain a hash-bound historical screen criteria/membership receipt; current 109 cannot substitute. | Lane 2 | OPEN |
| Material (next-scope blocker) | Exact historical provider-primary Security/Trading Item identity at the same start date is not yet provider-verifiable. | Obtain the historical-primary mapping for exactly the admitted historical risk set and satisfy the new receipt contract. | Lane 2 | OPEN |

## Scope split summary

**in-scope:** historical-vintage authority, replay parity, next-session cube activation, historical-primary admission contract, transition-planner fail-closed behavior, restartable CIQ driver semantics, bounded provider diagnostics, full AOV regression, and current-truth documentation are implemented and locally green. No in-scope Critical/High defect remains from local deterministic checks.

**inherited / next-scope:** provider-verifiable historical screen membership, provider-verifiable historical primary identity, formal A1 economics, A2 freeze/query, prospective Clock outcomes, and any financial-alpha uplift remain outside this completed implementation slice. Independent reviewer service availability is external to the candidate but blocks terminal SAW PASS.

## Ownership check

Implementer = current Lane-2 worker. Reviewer A/B/C were launched as distinct fresh review conversations with separate strategy/runtime/data focus manifests. Each initial launch and its one permitted retry failed at the review service boundary with `launch_failed`; no reviewer output was captured. Ownership separation therefore cannot be satisfied in this round and SAW remains BLOCK.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `research/aov0/historical_security_master.py` | New historical-start primary security/trading-item receipt admission contract | Local tests PASS; A/B/C unavailable |
| `research/aov0/historical_pit.py` | Historical decisions routed through exact current-cut builder; date-local eligibility + activated cube output | Local tests PASS; A/B/C unavailable |
| `research/aov0/cube.py` | Deterministic next-session decision-cube activation helper | Local tests PASS; A/B/C unavailable |
| `research/aov0/ciq_historical_pit.py` | Legacy generic normalizer explicitly demoted to diagnostic-only / not A1_A2 authority | Local tests PASS; A/B/C unavailable |
| `scripts/aov0_historical_pit_replay.py` | Historical-primary gate, authoritative transition planner, A2 receipt inheritance/freeze checks, activated cube consumption | Local tests PASS; A/B/C unavailable |
| `scripts/aov0_lane2_a1_driver.ps1` | Historical-primary receipt requirement, one-unit defaults, exact part/row custody checks | Parse PASS; A/B/C unavailable |
| `tests/aov0/test_historical_security_master.py` | Tamper/as-of/current-conditioning/membership/alias regressions | PASS |
| `tests/aov0/test_historical_pit.py` | Same-input technical/policy parity, ineligible-name behavior, activated cube, canonical five-arm regression | PASS |
| `tests/aov0/test_historical_pit_replay.py` | New source-authority/freeze and authoritative transition planner regressions | PASS |
| `tests/aov0/test_ciq_historical_pit.py` | Legacy diagnostic authority label regression | PASS |
| `docs/architecture/historical_fundamental_vintage_authority.md` | Vintage Option A frozen and parity gate closed; remaining source blockers made explicit | Local scope check PASS |
| `docs/architecture/aov_strategic_direction_lock_20260809.md` | Lane-2 hard block moved from vintage/parity to historical risk set + primary identity | Local scope check PASS |
| `docs/spec.md` | Canonical active-contract Lane-2 truth reconciled | Local scope check PASS |
| `docs/context/planner_packet_current.md`, `docs/context/done_checklist_current.md` | Critical-path/checklist reconciliation | Local scope check PASS |
| `docs/phase_brief/lane2_status_20260809.md`, `docs/lessonss.md` | Live custody, provider findings, parity result, blockers and guardrails | Local scope check PASS |

## Validation evidence

- Full AOV suite: `120` tests collected; `tests/aov0` run is green.
- Historical parity test proves exact same-input identity/ADV20/volatility/SMA/trend/Q-U inputs/technical state/exit-capacity/regime/sizing/Rule100 behavior and active-name cube state.
- Canonical five-arm experiment passes on the activated historical cube.
- PowerShell parser: `POWERSHELL_PARSE_OK` for `scripts/aov0_lane2_a1_driver.ps1`.
- Selected Python modules: `PY_COMPILE_OK`.
- `git diff --check`: PASS.
- Four diagnostic period objects are atomically landed at 109 rows each; missing FQ0 counts are 87, 87, 52, 19 and the corrected transition planner refuses the matrix before transition capture.
- Diagnostic period SHA-256: `93831f437cba2c5f4ce3c52e93d4f8a0e5aca41f3225e4d5faa32c958f344e0a`, `35cdbfe02fe998eefccfce3a2de466a5657a49831b07575da1c4487cd889449b`, `fa45651f5dca3205e183c6ff59b1c60994b52c7c56690c27d9eb8575619b429d`, `99238064c131ef41a5e1cf0303b9745d9ceb49edf00725a7b14d0062d01dfd98`.
- Scalar/SPGTable historical-primary shortcuts were rejected and produced no formal receipt.
- No commit, stage, or push was performed.
- No prospective outcome was opened; Parent/Child were not mutated; `financial_alpha_evidence` remains `0`.

## Open Risks:

1. Independent Reviewer A/B/C service launches are unavailable after the required retry, so terminal SAW PASS is not claimable.
2. Historical high-growth screen membership at A1 start is not yet provider-verifiable.
3. Historical primary Security/Trading Item identity for that same historical cohort/date is not yet provider-verifiable.

## Next action:

Obtain the provider-verifiable historical high-growth start risk set first, because it defines the exact company membership the historical-primary identity receipt must bind; then acquire the matching primary Security/Trading Item mapping and rerun independent A/B/C review when review launch capacity is available.

ClosurePacket: RoundID=ROUND-20260809-LANE2-HISTORICAL-TAKEOVER; ScopeID=LANE2_A1_SOURCE_AUTHORITY_PARITY_HARDENING; ChecksTotal=12; ChecksPassed=9; ChecksFailed=3; Verdict=BLOCK; OpenRisks=Reviewer_A_B_C_unavailable_and_A1_source_authority_open; NextAction=Obtain_historical_start_risk_set_then_matching_primary_identity_and_rerun_independent_review

ClosureValidation: PASS

SAWBlockValidation: PASS
