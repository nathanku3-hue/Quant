# SAW — AOV-v3 NON-PIT Diagnostic Backtest — 2026-08-08

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: project-init-fallback | Domains: quantitative-research, AOV-v3 runtime, data-authority | FallbackSource: `docs/spec.md` + `docs/phase_brief/alpha-organism-vertical-0-brief.md`

RoundID: `AOV0-V3-NONPIT-BT-20260808-R1`
ScopeID: `SCOPE-AOV0-V3-NONPIT-DIAGNOSTIC-BACKTEST`

## Scope and ownership

Work round scope: run the strongest honest multi-year AOV-v3 diagnostic possible without historical PIT CIQ inputs, preserve active engine/model mechanics, and prevent the result from escalating into CIQ/PIT/alpha authority.

Owned files changed this round:

- `tmp/aov0_v3_nonpit_backtest.py`
- `docs/saw_reports/saw_aov0_v3_nonpit_backtest_20260808.md`

Acceptance checks:

- CHK-01 — Diagnostic harness is quarantined, syntax-valid, and writes no production-current data.
- CHK-02 — Active AOV mechanics are retained: weekly decisions, one-bar lag, 10 bp turnover cost, current Rule100/Parent/Child parameters.
- CHK-03 — Multi-year diagnostic executes to completion with strict missing executed-return checks and reports all requested arms/references.
- CHK-04 — Independent Reviewer A/B/C passes are completed and reconciled without suppressing quantitative-bias findings.
- CHK-05 — Output remains explicitly non-PIT/non-authoritative with `financial_alpha_evidence=0` and no prospective-authority effect.

## Method boundary

This is deliberately non-authoritative. It freezes the current 2026 `run_4` factor snapshot through history, selects a static subset of current 2026 survivors, uses yfinance adjusted-close/volume as the risky-asset market source, and uses `CIQSEC:DIAG_<entity_id>` identities rather than real Capital IQ Security IDs. Official New York Fed SOFR values are used for economic cash, with a conservative diagnostic rule that only a SOFR effective date strictly before the return-interval start may be used.

Active AOV mechanics retained: weekly decisions, one-bar execution lag, 10 bp turnover cost, Rule100 max weight `0.35`, Parent strength `0.35`, Child eta `0.50`, Child hazard cap `0.50`, canonical cube/Parent/Child formulas, and strict missing executed-return checks.

## Evidence snapshot

- Script SHA-256: `75b01be43851b8a65484a525d6dceff8a5d5f0e85349ecf73fc3e07a4676700b`
- Contract hash: `782411b86101993e4d4ee9e07588d2f559f30c5206e87e34649fce597872b155`
- Start: `2021-01-04`
- End: `2026-08-06`
- Trading days: `1,404`
- Current fundamental rows: `109`
- Parsed current tickers: `108`
- Static diagnostic names surviving history/coverage gates: `34`
- Production-current writes: none; `data/aov0/current/` remains `official_sofr.parquet` only.

## Results

| Arm | Cumulative P&L | CAGR | Sharpe | Max DD |
|---|---:|---:|---:|---:|
| Rule100 | `+391.20%` | `33.07%` | `1.08` | `-31.82%` |
| Parent | `+379.19%` | `32.48%` | `1.06` | `-31.89%` |
| Child | `+322.00%` | `29.49%` | `1.05` | `-29.85%` |
| Static current-survivor equal weight | `+499.37%` | `37.91%` | `1.08` | `-53.78%` |
| SPY reference | `+124.44%` | `15.62%` | `0.95` | `-24.50%` |
| Economic cash | `+18.62%` | `3.11%` | diagnostic-only | `-0.25%` |

Incremental:

- Parent minus Rule100 cumulative return: `-12.02 percentage points`.
- Child minus Parent cumulative return: `-57.19 percentage points`.
- Child minus Rule100 cumulative return: `-69.20 percentage points`.
- Child reduces max drawdown versus Parent by about `2.04 percentage points`, but CAGR is about `2.99 percentage points` lower than Parent and `3.58 percentage points` lower than Rule100.

## Findings table

| Finding | Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|---|
| Frozen 2026 factor state is projected backward through history | Blocking for alpha authority | Lookahead bias invalidates unbiased performance interpretation | Obtain historical PIT fundamentals with date-correct availability | Data/Research | Open |
| Static 2026 survivor subset defines the backtest universe | Blocking for alpha authority | Survivorship bias materially inflates/warps historical performance | Reconstruct date-local historical candidate/universe membership | Data/Research | Open |
| Risky-asset source is yfinance with diagnostic identities, not CIQ Security/Trading Item authority | Material | Cannot qualify as AOV-v3 CIQ evidence | Admit historical CIQ identity + primary-security market data | Data | Open |
| Child reduces max drawdown modestly but materially sacrifices return in this biased replay | Advisory | Current insurance mutation shows weak economic tradeoff in diagnostic | Re-evaluate only after unbiased PIT replay; do not tune from this result | Research | Open / no tuning authorized |
| Quarantine and production-current boundary held | Advisory positive | Prevents false authority escalation | Keep diagnostic under `tmp/`; no current-data write | Implementer | Closed |

## Scope split summary

In-scope findings/actions:

- Multi-year mechanical/economic diagnostic completed.
- Bias and data-authority limitations explicitly surfaced.
- No production-current data or prospective-authority artifact changed.

Inherited out-of-scope findings/actions:

- Historical PIT CIQ fundamentals availability, Security/Trading Item history, date-local universe membership, and primary-security total-return/price/volume history remain external data dependencies.
- Real prospective Clock-Start authority remains governed by the separate admitted-current path and is not changed by this diagnostic.

## Independent reviews

### Reviewer A — strategy/mechanical correctness

- Review ID: `fe6324f4fa3f54de532f8b8c60e70c58ca21940e8ed0bf50c071dbce56ca7cf9`
- Result: `PASS`
- Summary: mechanically coherent diagnostic; one-bar/cost/strict-return semantics and non-authoritative boundary are explicit.

### Reviewer B — quantitative validity / bias

- Review ID: `caa3ca6e6ca1af5cc2b24c6cc32bc74c360edb5b66efe60647ea311d501ef269`
- Result: `FAIL`
- Blocking findings: survivorship bias and lookahead bias prevent the reported historical performance from serving as an unbiased estimate of tradable strategy performance; static survivor equal-weight outperforming AOV is a direct bias warning.

### Reviewer C — data integrity / custody

- Review ID: `c7f74533e451da5958e0f07d425b79ea1cae69db89c6f4e03736524e486f98dc`
- Result: `PASS`
- Summary: quarantine and scope boundary are correct; no real CIQ admission or production-authority escalation occurred.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `tmp/aov0_v3_nonpit_backtest.py` | Added quarantined non-PIT diagnostic harness using active AOV cube/Parent/Child/engine semantics | A PASS / B FAIL-for-alpha / C PASS |
| `docs/saw_reports/saw_aov0_v3_nonpit_backtest_20260808.md` | Added terminal evidence and explicit quantitative-validity block | Evidence artifact |

## Document Sorting

1. Runtime diagnostic harness under `tmp/`.
2. SAW evidence under `docs/saw_reports/`.
3. No active product/context authority document changed by this diagnostic round.

## Closure

ChecksTotal: 5
ChecksPassed: 4
ChecksFailed: 1
SAW Verdict: BLOCK

Open Risks: `PIT_LOOKAHEAD_AND_SURVIVORSHIP_BIAS; HISTORICAL_CIQ_AUTHORITY_MISSING`
Next Action: `Build a historical PIT CIQ replay with date-correct universe, Security/Trading Item identity, fundamentals availability, and primary-security total-return/price/volume data; rerun the same fixed AOV-v3 contract without tuning.`

ClosurePacket: RoundID=AOV0-V3-NONPIT-BT-20260808-R1; ScopeID=SCOPE-AOV0-V3-NONPIT-DIAGNOSTIC-BACKTEST; ChecksTotal=5; ChecksPassed=4; ChecksFailed=1; Verdict=BLOCK; OpenRisks=PIT_LOOKAHEAD_AND_SURVIVORSHIP_BIAS,HISTORICAL_CIQ_AUTHORITY_MISSING; NextAction=BUILD_HISTORICAL_PIT_CIQ_REPLAY

ClosureValidation: PASS
SAWBlockValidation: PASS

## Final disposition

`BLOCK_FOR_ALPHA_AUTHORITY / PASS_FOR_NON_PIT_DIAGNOSTIC_OPERABILITY`

The backtest answers the mechanical/economic question: the current AOV-v3 formulas can run over a multi-year market history. It does **not** answer the scientific/PIT question. The headline returns must not be used as alpha evidence, model-selection authority, or a reason to tune the Parent/Child contract.
