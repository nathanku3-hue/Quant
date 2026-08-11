# AO-K0A — Denominator Alignment / Orthogonal Basis Preflight

**Date:** 2026-08-11
**Verdict:** `GO / FROZEN`
**Status:** `CLOSED_SOURCE_PREFLIGHT / NO_EMPIRICAL_RESULT`
**Contract:** `docs/architecture/orthogonalization_contract_v1.md`
**Machine freeze:** `docs/architecture/ao_k0a_orthogonal_basis_preflight_v1.json`
**financial_alpha_evidence:** `0`
**W6:** `UNTOUCHED`

## Objective

Replace the old coverage-failure treatment with a full-W3 persistent-abstention law and freeze the date-local Q/M orthogonalization geometry before any new Alpha result is opened.

## Frozen result

AO-K0A freezes:

- denominator=`PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1` directly;
- missingness as persistent `ABSTENTION`, never `PASS/FAIL` and never denominator deletion;
- basis states=`ELIGIBLE_COMPLETE / Q_UNOBSERVED / M_WARMUP / M_MISSING_HISTORY / Q_AND_M_MISSING`;
- Q rank over all Q-observed W3 names;
- Q and M re-ranked on Q∩M before `OLS rank(M) ~ 1 + rank(Q)`;
- `M_perp` as the date-local OLS residual with no temporal fit and no outcome input;
- Q arm observability independent from joint-arm observability;
- full-W3 right-tail and breadth denominators;
- missing names at `risky_weight=0`, residual capital in economic cash, and PIT equal-weight full W3 as the opportunity comparator;
- security-level/peer return imputation, complete-case denominator, observed-subset renormalization, and coverage PASS/FAIL gates as forbidden.

## First-principles source preflight

Only immutable W3, admitted S0, and exact W3 market custody were read. Historical test/feature artifacts were not used to define an observability boundary.

The in-memory, deterministically regenerable pre-W6 weekly `basis_status` matrix has:

```text
rows                         310,329
SHA-256                      bd36a6305f38ff68c57f6ccfb9d3481be6fd42d2288128ef9ec3eb3cc12df5cf
ELIGIBLE_COMPLETE            223,367
M_MISSING_HISTORY             17,767
M_WARMUP                      30,270
Q_AND_M_MISSING               36,068
Q_UNOBSERVED                   2,857
rows removed for missingness        0
W6 dates consumed                  0
winner/future-outcome reads        0
new provider requests              0
```

The W3 authority itself reproduces mean eligible count `4822.994219653179` over 346 sessions.

## Coverage reconciliation

The previously stated approximately `79.49%` common coverage is **not** promoted to AO-K0A authority. Under the newly restricted first-principles sources, the old Rule100 numeric-Q observability law cannot be exactly rebuilt from admitted S0 because the old Q factors require primitives not present in S0. AO-K0A therefore does not backsolve an observability definition to reproduce 79.49% and does not borrow a transient factor store.

The source preflight's post-M-warmup `ELIGIBLE_COMPLETE` rate is `0.8973228991748552`. This is source-observability accounting only, not Alpha evidence and not a gate.

## Stop line

AO-K0A opened no winner/future outcome, no Q/M-perp/Q+M-perp empirical result, no W6, no provider, no K tuning, no dislocation experiment, no peer-valuation acquisition, no portfolio optimization, and no capital authority.

`AO-K0B — DEVELOPMENT BASIS TEST` remains a separate charged/result-bearing slice. Before it can select names, the numeric Q representation and scalar Q+M-perp composition rule must be explicitly source-bound without violating `OrthogonalizationContractV1`.
