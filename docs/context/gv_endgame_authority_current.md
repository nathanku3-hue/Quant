# GodView Endgame Authority — Current

Date: 2026-08-09
Active product state: `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`
Status: `STRATEGIC_DIRECTION_APPROVED_AND_LOCKED; MANDATORY_RECUTS_AUTHORIZED; BROAD_ARCHITECTURE_REOPEN_NO; PARALLEL_EVIDENCE_QUALIFICATION_YES; SINGLE_CURRENT_CAPITAL_POLICY_AUTHORITY; REAL CIQ ADMITTED; V3 CLOCK_RUNNING; FINANCIAL_ALPHA_EVIDENCE_0; LIVE CLOSED`
Canonical product maturity: `70/100`
Portfolio-alpha evidence: `0`
Limited Live: `CLOSED; NOT AUTHORIZED`

## Clock #1 authority update — 2026-08-08

The former real-CIQ pre-Seal blocker is closed. Final raw market authority is `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, SHA-256 `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`, 21,345 deterministic rows, zero duplicate-key conflicts. CIQ admission yields 99 canonical securities and 10 explicit exclusions; 26 names are Rule100 sizing-eligible at target `2026-08-07`.

The real decision cut is `AOV0_CIQ_20260807_ad2faf0533cec19c`. Seal Candidate `c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88` is immutable and clock-false by itself; fresh-process verification `55ba4e2f3670d4fc01839bd22bb164cfd0755efb1ce47f3641b9ca88d61c344c` succeeded; Clock-Start Receipt `eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78` started Clock #1 at `2026-08-08T19:48:52.440503Z`. Evaluation begins `2026-08-10T20:00:00Z`; outcome authority remains sealed until `2026-09-09T20:00:00Z`. `financial_alpha_evidence=0`; strategy live capital remains closed.

Any later statement in this document that describes real CIQ admission or Clock #1 as still open is historical and superseded by this authority update.

## Canonical product direction

GodView is one local-first PIT-certified portfolio operating system operated through `launch.py` → `dashboard.py` / Command Center. Deterministic systems own admitted data, permanent identity, formulas, target weights, accounting, evidence qualification, current portfolio/capital-policy authority, promotion commits, and risk authority. The strategic direction is locked by `docs/architecture/aov_strategic_direction_lock_20260809.md`: multiple independently owned Alpha-family prediction clocks/evidence streams may run and qualify in parallel, while the current portfolio/capital-policy commit chain remains singular. `CYCLE_RESONANCE_v1` remains the unchanged 252d slow business-cycle family; one fast multi-week family is authorized for immediate preregistration. Bounded AI tooling may support several family clocks but never owns truth/risk/capital. Real outcome-informed mutation still begins only from matured validated ReviewPackets. Roadmap/change authority is `docs/architecture/aov_endgame_generalization_spec_current.md`; current runtime meaning remains owned by the frozen executable contract + exact code bytes + admitted receipts.

```text
immutable PIT reality
→ deterministic model organism
→ real immutable prospective experiment
→ matured deterministic review
→ bounded AI mutation
→ model-portfolio research-capital allocation
→ genuinely independent replication
→ bounded long/cash authority
→ optional PIT-borrow-backed L/S extension
```

## Banked / local custody

- Published prior authority remains `9af5259`; unchanged.
- Episode 1 remains banked at `ab258c3`.
- Episode 2 local immutable candidate = `39f7be3894623c095994066b8f0ea2895b968643`.
- Exact `39f7be3` archived-byte selected matrix = `115/115 PASS`; `142/142` is superseded.
- Episode-2 push, hosted Windows/Linux, independent audit, FF/tag publication remain external/unperformed.

## AOV local executable authority

Local lineage:

```text
39f7be3 Episode-2 freeze
→ 4b14846 hard cut + AOV vertical
→ dca69fc explicit owner-insurance boundary
```

`dca69fc72dd3192913aa921323ff48f68610a925` is the current local AOV executable tip before documentation closure.

Current AOV path has one app/engine/permanent-ID/return/evidence/benchmark semantics and zero compatibility aliases under the machine scan. On 2026-08-07 the owner explicitly selected the Capital IQ authority family because the available WRDS account lacks CRSP entitlement; this is an intentional destructive contract-family change, not a provider fallback.

## Frozen executable contract

Frozen:

- permanent ID = S&P Capital IQ Security ID, canonical namespace `CIQSEC:<id>`;
- company `SP_ENTITY_ID`, ticker, legacy PERMNO, and dual-provider identity are invalid active aliases;
- date-local Rule100 universe;
- S&P Capital IQ Pro primary-security total-return matrix is the sole risky-asset P&L authority;
- corporate actions reconciliation-only;
- coherent `F_proxy/C_proxy` formulas;
- Rule100 equivalence + inherited gross-budget/cap/schedule/cash semantics;
- one frozen V0 engineering configuration;
- one risk-reducing Child mutation;
- one-bar execution, weekly attempts, 30-calendar-day horizon;
- paired weekly dependence-aware inference;
- official SOFR − 25 bp economic cash, ACT/360, no zero floor, after publication only, no proxy substitution;
- Expected Shortfall / CVaR insurance endpoint.

Insurance V0 is frozen in production:

- insurance materiality floor ratio = `0.05`;
- annual insurance-premium ceiling = `0.0015`.

These values require at least 5% relative CVaR/Expected-Shortfall improvement while permitting at most 15 bp/year expected net-return sacrifice. Changing either creates a new contract/model family; subsequent outcomes do not calibrate them in place.

## Mechanical capability

Implemented and locally validated:

- hardened canonical research spine;
- minimal PIT vertical cube;
- Rule100 / Parent / Child;
- hash DAG and selective recomputation;
- five-arm experiment/evidence machinery;
- immutable prospective seal/reopen machinery;
- deterministic review core;
- bounded CIQ primary-security/market admission builder that excludes ambiguous/missing identity, cross-entity collisions, `<3` factor coverage, insufficient 200-day market history, invalid target market state, same-day U.S. daily rows retrieved before 16:00 America/New_York, and future-stamped source retrieval times without ticker/entity/PERMNO/yfinance fallback;
- direct NY Fed SOFR intake with a hard pre-network 15:00 America/New_York gate and raw-byte receipt;
- deterministic `aov0_ciq_decision_cut_v3` builder requiring exact retrieval/admission times for the four active sources, distinct `cut_built_at`, and exact next `NYSE_2026_CORE_CLOSE_1600_ET` evaluation boundary; `run_2`/screen timing and v2/open execution are not active contracts;
- `aov0_prospective_seal_v3` with independently system-stamped actual seal write time, bound `aov0_executable_byte_manifest_v1`, serialized current target vectors, `evaluation_start`, and maturity derived from `evaluation_start + 30 calendar days`; the seal is a clock-false candidate only;
- fresh-process full-chain verification proof + separate immutable `aov0_prospective_clock_start_receipt_v1`; only the receipt can set `prospective_clock_started=true`;
- synthetic current-cut CIQ→SOFR→v3 cut→Seal Candidate→fresh-process proof→Clock-Start Receipt integration;
- ZERO-COMPAT seven-count all-zero gate, including no archived/release executable-source imports outside receipt integrity.

Mechanical/test seals are not empirical or prospective evidence.

## Roadmap re-audit status

`docs/architecture/aov_endgame_generalization_spec_current.md` is **ROADMAP / CHANGE AUTHORITY**, `docs/architecture/aov_strategic_direction_lock_20260809.md` is the final meeting record, `docs/architecture/paper_0_authority.md` is the PAPER-0 execution contract, and `docs/architecture/historical_fundamental_vintage_authority.md` is the A1/A2 vintage hard gate. Prior architecture/scientific-bar, strategic-reorder, sim-to-real and Winner/authority approvals remain valid on their scopes. Final re-audit=`PASS — STRATEGIC_DIRECTION_LOCKED`; broad architecture reopen=`NO`; operating objective=`EVIDENCE_VELOCITY × ECONOMIC_RELEVANCE`. Mandatory recuts are execution gates: preserve Clock #1; retain CRV1 252d; preregister one fast multi-week family; default active Alpha-family WIP=`2`, initial ceiling=`3`; allow parallel evidence qualification; serialize current portfolio/capital-policy commits; implement PAPER-0 behind minimum gates; start quarantined replication readiness; hard-block A1/A2 until historical-vintage + semantic parity close. One writer per mutable authority surface and immutable deterministic joins remain mandatory. Current execution state remains `CLOCK_1_RUNNING / PRE_EVALUATION / OUTCOME_SEALED`.

Arm 5 is closed from executable truth: `ECONOMIC_CASH = official SOFR - 25 bp, ACT/360, no proxy substitution`. PIT equal-weight remains the risky-asset performance comparator.

## First real seal blocker — CLOSED / historical

Real CIQ admission and the full destructive-v3 authority chain are complete. The current paths contain the admitted Rule100 targets, vertical primitives, total returns, official SOFR and `decision_cut_v3`. Final market custody is `data/aov0/raw/ciq_primary_security_market_history_20260808T193921Z.csv`, 21,345 rows, SHA-256 `897dfb12b383f3e8ed4765dfca21083f0129a1695cd1f432a4ebfb1ddbabbe48`; CIQ admission yielded 99 canonical securities and 10 explicit mechanical exclusions with no alternate-listing backfill.

The real decision cut is `AOV0_CIQ_20260807_ad2faf0533cec19c`; Seal Candidate `c78088ace7819170cd0064154fba138da4b4f8183dbd4ec48c347a942985ba88` remained clock-false; fresh-process verification `55ba4e2f3670d4fc01839bd22bb164cfd0755efb1ce47f3641b9ca88d61c344c` succeeded; immutable Clock-Start Receipt `eabd645382424f559286045a4980412db9a02a4ad0d594850f93675443cd1b78` started Clock #1 at `2026-08-08T19:48:52.440503Z`. Evaluation begins `2026-08-10T20:00:00Z`; outcome authority remains unavailable before `2026-09-09T20:00:00Z`. Existing v2 artifacts remain historical/mechanical evidence only; active authority is v3 with no compatibility reader/writer. Financial-alpha evidence remains `0`.

## Review / AI boundary

Deterministic review core exists. The pre-Clock v3 adversarial authority gate passes locally: byte mutation, target 1bp mutation, Security-ID authority mutation, SOFR substitution, fresh-process-only promotion, session/close chronology including legacy 09:30 rejection, pre-evaluation return, early maturity, and nothing-happened temporal availability all fail closed. After Clock #1 apply the multi-clock/domain WIP law. **Lane 1 Future Truth** keeps the weekly AOV tape + review/custody active while Alpha PIT, CRV1's unchanged 252d clock, and one separately preregistered fast multi-week family may advance under isolated family ownership; evidence qualification may occur in parallel and does not itself create capital authority. **Lane 2 Historical Compression** is currently hard-blocked from A1/A2 admission until one historical CIQ filing-vintage semantic wins destructively and current-vs-historical shared AOV economics pass same-input parity; Clock #1 outcomes remain inaccessible and Parent/Child remain frozen. One bounded AI Research Tooling vertical may support several family clocks under independent ownership, but real outcome-informed mutation cannot cross the matured-ReviewPacket gate early. `MARKET_TRANSITION_ALPHA_v1` remains discovery-only unless explicitly admitted into an active family WIP slot. The deeper Right-Tail Atlas remains discovery-only and episode-based. **Replication readiness starts now** in a quarantined domain; its outcomes are not research inputs. **PAPER-0 implementation is authorized now** using the smallest lineage-correct path: promoted target→`live_rebalance_id`→future `ExecutionIntentV1`→CIQSEC↔broker map→`market + cls`→broker canonical state→restart reconciliation/fencing→persistent `FREEZE_NEW_RISK`; unsupported states may fail closed and the first order must resolve the actual session close or be restricted to a verified regular full-session day. Existing broker/recovery/signed-replay/event-book primitives are reused; no second OMS. `RESONANCE_LEVERAGE_POLICY_v1` stays evidence/CRO-gated with leverage/short/options authority disabled.

AI activation is split:

```text
post-Clock engineering on immutable fixtures/source-bound packets
→ AIInvocationReceipt + role firewall + deterministic validator

real outcome-informed activation only after
matured + reconciled + validated ReviewPacket
→ one MutationManifestDraft → deterministic compile → development Trial
```

## Model portfolio direction

As soon as the first evidence-backed mutation exists, establish only the minimum research-capital roles:

- Safety Parent;
- Incumbent;
- Challenger;
- Negative Control.

Add additional Challengers and Sentinel only when real evidence creates the need; do not build the full model-governance system ahead of evidence.

## Claim boundary

- Canonical maturity remains `70/100`.
- Portfolio-alpha evidence remains `0`.
- No admitted real A1 result, no A2 result, and no real prospective A3 evidence is claimed. A1/A2 is explicitly blocked until the `Original` versus `Current/Restated` historical-vintage contradiction is resolved under one provider-semantic authority and current-vs-historical AOV parity passes. The Lane-2 roadmap authorization and any uncommitted historical-PIT prototype do not themselves earn evidence.
- Before Clock #1: no AI/source pipeline implementation, Market Transition implementation, provider programme, AOV-2/event authority, optimizer/RL-first path, compatibility restoration, broker/order execution work, live capital, leverage, shorting, options/derivatives, or alpha claim. After Clock #1, domain-parallel research engineering and the thin PAPER Capitalization Vertical are roadmap-approved only within their frozen authority boundaries; strategy live capital remains closed.
- Limited Live remains closed.

## Next action

Preserve and reverify Clock #1 and keep the frozen-109 weekly tape alive. Resolve the historical CIQ filing-vintage truth and AOV parity gate before admitting A1/A2; only then accelerate restartable provider chunks. Continue CRV1 without changing its 252d primary horizon and immediately preregister one fast multi-week family under the active WIP law. Implement PAPER-0's minimum execution identity/TIF/broker-state/restart/calendar gates before the first paper order. Start independent-replication entitlement/identity/PIT/license quarantine now. Bounded AI and Market discovery remain supporting lanes; evidence may qualify in parallel, but current portfolio/capital-policy authority remains singular. Parent/Child remain frozen; `financial_alpha_evidence=0`; strategy live capital remains closed.
