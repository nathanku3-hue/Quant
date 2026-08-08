# SAW — AOV-0 Non-Authoritative Economic Proxy — 2026-08-08

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: inherited-active-brief | Domains: quantitative-research, AOV-0 economics, runtime/data integrity | FallbackSource: `docs/spec.md` + `docs/phase_brief/alpha-organism-vertical-0-brief.md`

RoundID: `AOV0-ECON-PROXY-20260808`
ScopeID: `AOV0-NONAUTH-ECONOMIC-DIAGNOSTIC`

## Scope

Run a bounded, explicitly non-authoritative economic proxy for current AOV-v3 mechanics using archived Rule100 decisions, public adjusted OHLCV, official NY Fed SOFR, the canonical one-bar engine, current Parent/Child coefficients, and 10 bp turnover cost. Do not claim CIQ/PIT authority, real AOV-v3 historical evidence, financial alpha, or production admission.

Owned analysis file:

- `tmp/aov0_economic_proxy.py` — SHA-256 `14522ad15acecfb0df4f0fd579511ab642dcf094a4331ab5264427ae06c948e5`

Source bindings:

- archived Rule100 decision history SHA-256 `eff1d8526a11050cf2206e01b0e6f003883804c23c6c968efbc7ca50171c73b9`
- yfinance adjusted-close frame SHA-256 `b00a36ca7ac6b9bd0f63632fff745b4e6cfef8dfc9e7c90be796bac8ae844c72`
- yfinance volume frame SHA-256 `79f04033132716f314bf3b64ef1edb429275c1e81537f142a238f0a9fbe7b0ae`
- official NY Fed SOFR frame SHA-256 `c34bd47cfac506bbb50c989dfa12c3d8e6b5bcefe879605975106b9795b69973`

Period: `2025-01-06` through `2026-05-11`, 299 archived trading dates, 9 names (`AMAT, AMZN, AVGO, LRCX, MSFT, MU, TSLA, TSM, WDC`).

## Acceptance checks

- CHK-01 — hard scope label remains non-authoritative; no CIQ/PIT or financial-alpha claim: PASS.
- CHK-02 — proxy compiles and runs through canonical `core.engine.run_simulation`: PASS.
- CHK-03 — one-bar execution, 10 bp turnover cost, strict executed-return completeness; missing active return cells = 0: PASS.
- CHK-04 — weekly AOV-aligned Rule100 / Parent / Child / PIT-EW proxy / economic-cash metrics produced over 299 trading dates: PASS.
- CHK-05 — Parent/Child frozen CVaR-0.95 insurance economics evaluated against 5% materiality and 15 bp annual premium ceiling: PASS.
- CHK-06 — source snapshot hashes captured and PIT-EW/public-market limitations explicit: PASS.
- CHK-07 — independent strategy, runtime, and data/interpretation reviews completed: PASS.

## Economic result — primary weekly schedule

| Arm | Cumulative return | CAGR | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|
| Rule100 | 28.06% | 23.18% | 1.793 | -7.57% |
| Parent | 28.08% | 23.20% | 1.792 | -7.63% |
| Child | 24.79% | 20.52% | 1.749 | -7.06% |
| PIT-EW proxy | 43.54% | 35.61% | 0.954 | -43.44% |
| Economic cash | 5.26% | 4.41% | 8.959 | -0.09% |

Incremental economics:

- Parent minus Rule100 CAGR = `+0.00018104` = about **+1.8 bp/year**; economically negligible in this proxy.
- Child minus Parent CAGR = `-0.02674750` = about **-267 bp/year**.
- Parent ES95 = `0.01713560`; Child ES95 = `0.01567840`; ES improvement ratio = **8.50%**, exceeding the frozen 5% materiality floor.
- Child annualized return premium = **2.315%/year**, far above the frozen **0.15%/year** premium ceiling.
- Frozen insurance classification = `INSUFFICIENT_EVIDENCE`; the risk reduction is too expensive under the current contract.

Residual-cash economic sensitivity (not current engine authority): because the primary risky arms average roughly 26.5% gross, crediting residual cash with official SOFR−25 bp changes CAGR to Rule100 **27.41%**, Parent **27.43%**, Child **24.76%**. This is a sensitivity only; the canonical engine currently treats residual cash as zero-return while economic cash is a separate benchmark arm.

## Findings

| Severity | Impact | Fix / disposition | Owner | Status |
|---|---|---|---|---|
| Material diagnostic | Parent adds ~1.8 bp/year versus Rule100 and slightly worsens Sharpe/MDD; no meaningful economic lift in this proxy. | Do not claim Parent alpha from proxy. Require real PIT/independent replication before changing the frozen contract. | AOV research | OPEN-RISK / NOT A BLOCKER TO PROXY |
| Material diagnostic | Child improves ES95 by ~8.5% but costs ~231.5 bp/year, >15x the 15 bp premium ceiling. | Keep `INSUFFICIENT_EVIDENCE`; do not promote Child as economically justified. Do not recalibrate V0 from this proxy. | AOV research | CLOSED CLASSIFICATION |
| Advisory | PIT-EW eligibility is reconstructed only from archived rows with `factor_present_count>=3`, not a full CIQ universe snapshot. | Treat PIT-EW magnitude as context only. | Data authority | OPEN-RISK |
| Advisory | yfinance is a public adjusted-OHLCV proxy, not CIQ total-return authority. | Keep `authority=false`; replace with historical CIQ bytes when available. | Data authority | OPEN-RISK |
| Advisory | Residual cash earns zero in the canonical risky-arm engine, while SOFR−25 bp is a separate benchmark. | Preserve current contract; use cash-accrual result only as economic sensitivity unless separately authorized. | Product/quant | OPEN-RISK |

## Reviewer passes

- Reviewer A / strategy economics — `ad69c84186058f16e6f397d51f73514b5bd8658740d0f35d1209b1b6b2751257` — PASS. Advisory: proxy only; Parent essentially no CAGR lift; Child lowers CAGR materially.
- Reviewer B / runtime and fail-closed behavior — initial run `b928a5f5f1c4024c85fc1700ac9ec3435c1d49ca51bcce366f199f7d27fce9b0` expired; mandated retry `90fab168ea0ef48c7782e5ea03c81b43f0fd09689a73f3b0f433a30fceddcec6` — PASS. Advisory: diagnostic scope only.
- Reviewer C / data and interpretation integrity — `111f62bed9df1f9422094c11e75433452d4bafeab78f5b758f58ba9a0d535c2c` — PASS. Advisories: public market proxy and incomplete PIT-EW authority remain explicit.

## Scope split

In-scope: economic diagnostic, source bindings, canonical-engine execution, current Parent/Child formula economics, cash benchmark, residual-cash sensitivity, non-authoritative interpretation.

Inherited out-of-scope: real historical CIQ Security/Trading Item identity, full historical PIT fundamentals/publication times, authoritative CIQ total-return history, production current writes, prospective-clock authority, financial-alpha claims, V0 recalibration.

Open Risks:

- Real historical CIQ/PIT authority remains unproven.
- PIT-EW eligibility is reconstructed from the archived history and is not a full historical CIQ universe proof.
- Market P&L uses a public yfinance adjusted-OHLCV proxy rather than CIQ total-return authority.
- Residual cash is zero-return in the canonical risky-arm engine; SOFR−25 bp cash accrual is sensitivity only.

Next action: use this proxy to prioritize true historical CIQ/PIT replication; do not recalibrate frozen V0 parameters from proxy outcomes.

## Document Changes Showing

| Path | What changed | Reviewer status |
|---|---|---|
| `tmp/aov0_economic_proxy.py` | Added bounded non-authoritative economic proxy analysis only. | A/B/C PASS |
| `docs/saw_reports/saw_aov0_economic_proxy_20260808.md` | Terminal SAW evidence for this proxy round. | terminal evidence artifact |

ChecksTotal: 7
ChecksPassed: 7
ChecksFailed: 0
SAW Verdict: PASS

ClosurePacket: RoundID=AOV0-ECON-PROXY-20260808; ScopeID=AOV0-NONAUTH-ECONOMIC-DIAGNOSTIC; ChecksTotal=7; ChecksPassed=7; ChecksFailed=0; Verdict=PASS; OpenRisks=REAL_CIQ_PIT_NOT_PROVEN|PIT_EW_PROXY_LIMITED|PUBLIC_MARKET_PROXY|RESIDUAL_CASH_ZERO_RETURN_PRIMARY_CONTRACT; NextAction=USE_PROXY_TO_PRIORITIZE_TRUE_PIT_REPLICATION_NOT_V0_RECALIBRATION

ClosureValidation: PASS
SAWBlockValidation: PASS
