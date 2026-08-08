# AOV-0 `run_4.xlsx` Fundamental Slice — SAW Receipt

Mode: `IMPLEMENTATION_REVIEW`
Date: 2026-08-07
RoundID: `ROUND-20260807-AOV0-RUN4-FUNDAMENTALS`
ScopeID: `AOV0-CIQ-CURRENT-CUT-FUNDAMENTALS-V1`
Branch: `codex/pit-source-authority-1`
Base HEAD observed at round start: `fa20289673944dd1f2c5eabd10950c6546276cda`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-scope | Domains: Product, Data Provenance, Quant Research, Software Engineering, Governance | FallbackSource: `docs/spec.md` + `docs/phase_brief/alpha-organism-vertical-0-brief.md`; explicit reconfirmation is required before the next execution round

## Intent

Advance the first-real-seal critical path with the smallest functional slice that does not require Capital IQ security-level bytes:

```text
run_4.xlsx quarterly company fundamentals
→ normalize fixed fiscal quarters
→ derive current-cut quarterly fundamental metrics
→ reuse canonical factor algebra
→ materialize Rule100 V1.1 factor group state / factor_positive_count
→ freeze bounded intermediate artifacts + receipt
```

This round does not create permanent security identity, market-derived technical state, final Rule100 targets, risky-asset return authority, SOFR, a decision cut, a prospective seal, a commit, or a push.

## Ambiguity resolution before irreversible use

Two source ambiguities were surfaced and resolved fail-closed rather than guessed:

1. **Relative `FQ0` versus absolute `FQqYYYY`.** Real bytes showed same-period-end conflicts between relative and absolute cells. The historical panel therefore admits only absolute `FQ[1-4]YYYY` references and excludes relative `FQ0/IQ_FQ`.
2. **Historical PIT timestamps.** `run_4.xlsx` does not embed a complete per-quarter historical publication/filing timestamp series. Accounting `period_end` is retained separately, while `known_at` is conservatively bound to the local raw-object admission time. This supports current-cut factor construction only and explicitly does not prove historical PIT replay.

One source entity, Gyrodyne (`SP_ENTITY_ID=4096690`), is present in the frozen 109-company source set but has only relative `FQ0` data and no absolute-quarter history. It remains in the 109-row current state with `NO_ABSOLUTE_QUARTER_HISTORY`, `factor_present_count=0`, and `factor_positive_count=0`; no history is synthesized.

## Canonical factor contract

The round reuses existing repository formulas rather than introducing a parallel scoring model:

- quarterly accounting derivations follow the existing Compustat/fundamental updater algebra for ROIC, revenue growth, sales acceleration, operating-margin acceleration, revenue/inventory change, bloat, net investment, and asset growth;
- fundamental factor functions come from `data/feature_specs.py` and persisted `z_*` values use the existing FeatureStore robust cross-sectional scaling;
- Rule100 V1.1 group counting comes from `strategies/rule100_softmax_v1_1.py`.

Important contract correction retained in the implementation: the four approved Rule100 V1.1 groups are demand=`z_demand`, inventory/supply=`z_inventory_quality_proxy`, moat/pricing=`z_moat`, and capital discipline=`capital_cycle_score` with `quality_composite` fallback. `z_discipline_cond` feeds the capital-cycle composite; it is not itself the directly counted fourth group.

## Source and output custody

Raw objects:

- `run_4.xlsx`: SHA-256 `17f356e47c9e3ecf9600ad21db153338f4941272e0a1ffb9fd7b872c6636f056`, 215,249 bytes;
- frozen screen cross-check `run_2.xlsx`: SHA-256 `f610c43b336142b3366136fa71e1fbae82bf4eac301401ac9ef1d0c0ddbe3e0e`;
- source entity sets match exactly: 109 / 109.

Current generated artifacts:

- `data/aov0/intermediate/ciq_entity_quarterly_panel.parquet`: 1,203 rows, SHA-256 `3cabaa7cae6574848847930b53a12f316dc14a712d7f4cbf667dd708bc0a9c0b`;
- `data/aov0/intermediate/ciq_entity_fundamental_state.parquet`: 109 rows, SHA-256 `62f525ee23f50bd8371245f59441a71225aacfa54cc68200f287226541bca8fc`;
- `data/aov0/source_receipts/ciq_quarterly_fundamentals_run_4_20260807.json`: receipt SHA-256 `baa5fc38bdd22071b7aaa14323065e706171646cbd9d491bb1c47b91717a5345` at final local validation.

Current state coverage:

- `COMPLETE_FACTOR_STATE`: 56;
- `PARTIAL_FACTOR_STATE`: 52;
- `NO_ABSOLUTE_QUARTER_HISTORY`: 1;
- `z_demand`: 59 / 109 non-null;
- `z_inventory_quality_proxy`: 108 / 109 non-null;
- `z_moat`: 99 / 109 non-null;
- `z_discipline_cond`: 102 / 109 non-null;
- `capital_cycle_score`: 106 / 109 non-null.

The receipt separately reports raw input coverage so canonical factor-level missing-value behavior cannot be mistaken for complete raw evidence. The weakest raw legs are `bloat_q` and `delta_revenue_inventory`, each 59 / 109; `net_investment_q` is 77 / 109.

## Identity / market boundary

- `SP_ENTITY_ID` is retained only as `TEMPORARY_COMPANY_ENTITY_NOT_SECURITY`.
- No `security_id`, PERMNO, ticker alias, or fabricated `CIQSEC:` identity is emitted by the fundamental state.
- No yfinance/local substitute return path is introduced.
- No `technical_quality`, realized volatility, ADV20, trend state, primary-security total return, final Rule100 target weight, final vertical primitive, or seal input is manufactured from company-level bytes.

## Implemented paths

- `research/aov0/ciq_fundamentals.py`: bounded XLSX parser, absolute-quarter normalization, metric derivation, existing factor-spec execution, robust scaling, canonical Rule100 group count, identity/PIT guards.
- `scripts/aov0_build_ciq_fundamentals.py`: atomic intermediate Parquet + source-receipt builder with raw-object and output hashes; receipt output paths are repository-relative.
- `tests/aov0/test_ciq_fundamentals.py`: relative-quarter exclusion, locked quarterly formulas, no-history/identity fail-closed behavior, and Rule100 V1.1 group-count regression tests.
- active PRD/spec/architecture/current-context/decision/notes/lessons surfaces: synchronized to the new fundamental-leg truth without opening a new phase.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 `run_4` raw custody/hash | PASS |
| CHK-02 109-company source set equals frozen `run_2` set | PASS |
| CHK-03 Absolute `FQqYYYY` history only; relative `FQ0` excluded | PASS |
| CHK-04 No historical PIT overclaim; `known_at` uses conservative local admission time | PASS |
| CHK-05 Canonical quarterly/factor algebra reused | PASS |
| CHK-06 Canonical Rule100 V1.1 four-group count semantics | PASS |
| CHK-07 Temporary company identity only; no ticker/PERMNO/fabricated `CIQSEC:` | PASS |
| CHK-08 Real artifact build | PASS — 1,203 quarter rows / 109 current states |
| CHK-09 Focused + AOV + Rule100/adapter regression | PASS — `53/53` |
| CHK-10 ZERO-COMPAT | PASS — all seven counters `0` |
| CHK-11 Python compile + `git diff --check` | PASS |
| CHK-12 Current-context deterministic validator | PASS — `scripts/build_context_packet.py --validate` |
| CHK-13 First-seal boundary remains fail-closed | PASS — `BLOCKED_MISSING_ADMITTED_INPUTS`, clock false, financial evidence `0` |
| CHK-14 Independent reviewer return | BLOCKED — two bounded REVIEW-RETURN-2 attempts expired without a reviewer result |

ChecksTotal: 14
ChecksPassed: 13
ChecksFailed: 1

## Reviewer attempts

- Attempt 1 review ID: `c4708269136a3d709afdbee76c08f9a774216e84b52602e869b29a2bb19c3b49` — expired without result.
- Retry review ID: `fa6eb8c27eb203f0fe062cc5bb417feb35c17f68204c7227b94c52fbdc34f8ab` — expired without result.

The retry limit for this round is exhausted. Local deterministic validation is not promoted to independent review.

## Scope split summary

- in-scope: local `run_4.xlsx` normalization, current-cut fundamental derivation, canonical Rule100 V1.1 factor-state materialization, intermediate artifact custody, focused regression, current-truth synchronization, and fail-closed boundary checks.
- inherited / out-of-scope: Capital IQ primary-security mapping and market bytes, final `data/aov0/current/*` seal inputs, direct NY Fed SOFR retrieval, first real seal, Episode-2 hosted custody/publication, commit, and push.

## Findings

| Severity | Impact | Fix / disposition | Status |
|---|---|---|---|
| Blocking for terminal SAW PASS | Required independent reviewer return is unavailable after one retry. | Re-run independent review against these exact candidate/evidence bytes when the reviewer lane is available. | Open external |
| Material / data coverage | Only 59 / 109 current states have `z_demand`; `bloat_q` is also 59 / 109 and `net_investment_q` 77 / 109. | Preserve missingness and raw-input coverage in receipt; do not silently impute a complete four-factor state. | Mitigated / visible |
| Material / PIT scope | Complete historical publication timestamps are absent. | Current-cut admission only; historical PIT replay remains unauthorized. | Mitigated / explicit |
| Advisory | One source entity has no absolute-quarter history. | Keep it in custody with explicit no-history state and zero present/positive counts. | Closed by design |
| Blocking for first real seal, out of this slice | Security-level identity and market bytes are still absent. | Next leg is primary `CIQSEC:<id>` mapping + same-cut primary-security market/total-return history. | Open next gate |

## Score / claim boundary

Canonical accepted product maturity remains `70/100`. This fundamental slice improves local readiness and operator/data flow but does not itself earn a canonical score uplift because no real seal or independent SAW PASS exists. `prospective_clock_started=false`, `financial_alpha_evidence=0`, and Limited Live remains closed.

Planning-only forecast after this slice:

- product capability: `80–84`;
- user/operator flow: `75–80`;
- portfolio completeness: `78–82`;
- integrity/deterministic replay: `94–97`;
- prospective evidence: `0–10` unchanged;
- shipping/custody: `83–89`;
- expected audit readiness: roughly `71–73`, not earned canonical maturity.

The prior successful-seal forecast remains approximately `73–76` audit maturity; seal #1 still carries financial-alpha evidence `0`.

## Remaining critical path

```text
FROZEN LOCAL FUNDAMENTAL LEG
run_4 current-cut factor state

NEXT SECURITY / MARKET LEG
109 company entities
→ Capital IQ primary Security ID + Trading Item mapping
→ canonical CIQSEC:<id> universe
→ same-cut primary-security daily market / total-return history
→ technical_quality + realized_vol + ADV20 + trend + AOV market primitives
→ final Rule100 targets + vertical_primitives + total_returns

THEN
→ direct NY Fed SOFR after the existing publication/retrieval gate
→ aov0_ciq_decision_cut_v1
→ scripts/aov0_first_seal.py
→ exact reopen
→ prospective_clock_started = true
→ financial_alpha_evidence = 0
```

## Open Risks:

- Independent reviewer output is unavailable after the allowed retry; terminal SAW PASS is not claimed.
- The fundamental artifact is current-cut only, not historical PIT replay proof.
- Fundamental raw-input coverage is uneven, especially the demand/bloat leg.
- Security/master/market capability has not been demonstrated by admitted bytes in this round.
- The repository contains inherited/pre-existing working-tree modifications outside this slice; this round did not revert, stage, commit, or push them.
- The root `E:\Code\Quant` checkout has a stale/broken Git worktree metadata pointer; work was performed in the valid authoritative worktree `E:\Code\Quant\.worktrees\devspace-053ca7a4f582fb3e`.

## Next action:

Do not stop for a second fundamentals redesign and do not fabricate security identity. Keep the `run_4` intermediate state frozen, obtain the same 109 companies' Capital IQ primary Security IDs and same-cut primary-security market/total-return bytes, join the fundamental leg onto canonical `CIQSEC:<id>` identity, derive `technical_quality` and the market/AOV primitives, materialize final Rule100 targets plus returns, retrieve direct NY Fed SOFR after the existing gate, construct `aov0_ciq_decision_cut_v1`, and seal immediately.

ClosurePacket: RoundID=ROUND-20260807-AOV0-RUN4-FUNDAMENTALS; ScopeID=AOV0-CIQ-CURRENT-CUT-FUNDAMENTALS-V1; ChecksTotal=14; ChecksPassed=13; ChecksFailed=1; Verdict=BLOCK; OpenRisks=independent reviewer unavailable, historical PIT replay not proven, sparse demand/raw factor coverage, security-market bytes still open; NextAction=primary CIQ security mapping + same-cut market bytes then final targets/primitives/returns then SOFR then decision cut then first seal
ClosureValidation: PASS
SAWBlockValidation: PASS
