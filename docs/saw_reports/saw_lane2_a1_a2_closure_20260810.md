# Lane 2 A1→A2 Closure — SAW Evidence

Mode: `CLOSURE_REPORT`

SAW Verdict: PASS

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init | Domains: Quantitative Research, Data, Docs/Ops | FallbackSource: `docs/spec.md` + `docs/phase_brief/lane2_historical_a1_a2_20260808.md`

RoundID: `LANE2-A1A2-CLOSE-20260810`
ScopeID: `LANE2-HISTORICAL-COMPRESSION`

## Scope and ownership

**in-scope:** close Lane 2 historical source authority, exact A1 replay, immutable A2 freeze, one untouched/query-metered A2 read, lifecycle custody, and current-truth synchronization. No Parent/Child mutation, no Clock #1 outcome open, and no financial-alpha uplift.

**inherited:** unrelated repository-wide failures, broad dirty-worktree state, Lane 1/CRV1/PAPER work, and other programme streams remain outside this closure. They may still block a repository phase-close claim, but they do not invalidate the owned Lane-2 evidence slice.

Implementer ownership: current Lane-2 worktree and local deterministic/provider-custody execution. Reviewer A/B/C are independent external review-return passes and do not own implementation bytes.

## Acceptance checks

| Check | Result | Evidence |
|---|---|---|
| CHK-01 Historical source/identity/lifecycle authority is fail-closed and not current-conditioned | PASS | 104-company final risk set; 104/104 exact dated CIQ Security/Trading Item identity; three hash-bound terminal events; no survivor filtering |
| CHK-02 A1 is legitimately admitted under exact frozen-AOV replay | PASS | `A1_ADMITTED_HISTORICAL_PIT`; 264 trading days; 94 active CIQ securities; canonical/source/identity/lifecycle gates pass |
| CHK-03 A2 is frozen before held-out PIT capture and evaluated exactly once | PASS | freeze `07:36:04Z`; held-out captures after freeze; query lock `07:43:15Z`; result/receipt `07:45:03Z`; query count=1; second evaluation forbidden |
| CHK-04 Owned Lane-2 regression is green | PASS | 58/58 focused pytest PASS across lifecycle/PIT/replay/risk-set/reconstruction/security/product-query capture/partial-candidate validation |
| CHK-05 Docs/current truth and whitespace are synchronized | PASS | Lane-2 brief, done checklist, planner packet, bridge contract, decision log, lessons; scoped `git diff --check` PASS |
| CHK-06 Independent Reviewer A/B/C closure review | PASS | Reviewer A PASS; Reviewer B PASS; Reviewer C PASS; no blocking/material findings |

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Advisory | Child reduces drawdown/CVaR/turnover but also reduces return/Sharpe versus Parent in both A1 and A2 | Keep Parent/Child frozen; use result only for diagnosis / separately frozen future challenger | Quant/PM | CLOSED AS BOUNDED INTERPRETATION |
| Advisory | Terminal securities can resemble data gaps and invite survivorship filtering | Use source-bound cash terminal-event lifecycle with fixed cash column; never substitute future-complete listings | Data/Quant | CLOSED |
| Advisory | External reviewer service initially launch-failed | Retry once per protocol; all three required independent reviews subsequently returned PASS | Ops | CLOSED |

## Independent review summary

- Reviewer A — strategy/regression: **PASS**. A1 admission and A2 one-shot chronology are supported; Child risk-reduction/return-dilution conclusion is appropriately diagnostic and does not create alpha authority.
- Reviewer B — runtime/operational resilience: **PASS**. Post-freeze PIT capture, immutable query lock, query count=1, terminal lifecycle, and no second A2 evaluation are supported.
- Reviewer C — data integrity/performance path: **PASS**. Exact identity/count/hash/timestamp custody and the final 58-test regression support closure; no silent imputation/substitution or survivorship repair is evidenced.

## Economic closure

A1: Parent cumulative return `+0.7145%`; Child `+0.3501%`. Child improves max drawdown by `1.5173pp` and CVaR loss by `0.3449pp`, while reducing cumulative return by `0.3644pp` and Sharpe by `0.0256`.

A2: Parent cumulative return `+6.7152%`; Child `+5.3701%`. Child improves max drawdown by `0.5529pp` and CVaR loss by `0.1945pp`, while reducing cumulative return by `1.3451pp` and Sharpe by `0.2527`.

Interpretation boundary: this is a consistent risk-reduction/return-dilution signature. It supports regime/loss/winner-miss diagnosis only. It does not authorize in-place Parent/Child tuning, a second A2 read, prospective-evidence uplift, or capital promotion.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `docs/phase_brief/lane2_status_20260809.md` | Superseded stale open gates with A1 admitted / A2 closed chronology and non-claims | A/B/C PASS |
| `docs/context/done_checklist_current.md` | Marked source, identity, lifecycle, A1, freeze and one-shot A2 gates complete | A/B/C PASS |
| `docs/context/planner_packet_current.md` | Recut Lane-2 bottleneck to post-A2 economic diagnosis and recorded Parent/Child deltas | A/B/C PASS |
| `docs/context/bridge_contract_current.md` | Updated Lane2 delta and next step; explicitly forbids A2 re-query | A/B/C PASS |
| `docs/context/impact_packet_current.md` | Added executable/data/evidence impact of closed A1→A2 slice and current changed surfaces | A/B/C PASS |
| `docs/context/observability_pack_current.md` | Replaced stale vintage/parity blockers with post-A2 custody/diagnosis sentinels | A/B/C PASS |
| `docs/context/post_phase_alignment_current.md` | Re-aligned multi-stream status from A1/A2 blocked to Lane-2 closed | A/B/C PASS |
| `docs/decision log.md` | Added immutable Lane-2 A1/A2 closure decision and claim boundary | A/B/C PASS |
| `docs/lessonss.md` | Added detailed Capital IQ Pro operating runbook: existing-session ProductQuery usage, exact field/perspective keys, identity/PIT semantics, Office fallback limits, unavailable/rejected paths, lifecycle/missing-data guardrails | A/B/C PASS |
| `docs/notes.md` | Added Lane-2 screen, identity, PIT, lifecycle cash-settlement, activation, A1 admission and one-shot A2 formula/authority registry | A/B/C PASS |
| `docs/saw_reports/saw_lane2_a1_a2_closure_20260810.md` | Closure review evidence | self-validated |

## Scope split summary

**in-scope findings/actions:** all source-semantic, identity, lifecycle, replay, freeze, one-shot query, scoped test, and current-truth closure checks pass. No in-scope Critical/High finding remains.

**inherited findings/actions:** repository-wide unrelated test/dependency/dirty-work issues remain outside Lane 2. No claim is made that the whole repository is phase-close clean.

Open Risks: None in the owned Lane-2 A1/A2 evidence closure. A2 is consumed and must not be re-run; any outcome-informed challenger must be a separately frozen trial.

Next action: Diagnose Parent/Child return dilution versus drawdown/CVaR benefit, regime dependence, costs, loss concentration, and missed/winner-clipping mechanisms without re-querying A2 or mutating the incumbent in place.

ClosurePacket: RoundID=LANE2-A1A2-CLOSE-20260810; ScopeID=LANE2-HISTORICAL-COMPRESSION; ChecksTotal=6; ChecksPassed=6; ChecksFailed=0; Verdict=PASS; OpenRisks=none; NextAction=Diagnose_Parent_Child_return_dilution_without_requerying_A2

ClosureValidation: PASS
SAWBlockValidation: PASS
