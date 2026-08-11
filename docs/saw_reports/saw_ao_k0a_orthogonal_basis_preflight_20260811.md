# SAW — AO-K0A Denominator Alignment / Orthogonal Basis Preflight — 2026-08-11

Mode: `CLOSURE_REPORT_NON_PHASE_END`

RoundID: `AO_K0A_ORTHOGONAL_BASIS_PREFLIGHT_20260811`
ScopeID: `AO-K0A-DENOMINATOR-ALIGNMENT-ORTHOGONAL-BASIS`

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: explicit owner `GO AO-K0A` | Domains: Alpha Management, Quant Research, Data/PIT, CRO/Risk, Architecture/Engineering | Canonical contract: `docs/architecture/orthogonalization_contract_v1.md`

## Scope

Freeze the full-W3 denominator, persistent missingness/ABSTENTION law, source-only observability preflight, date-local Q/M rank bases, and `M_perp` OLS geometry without opening any new winner/future outcome, W6, provider request, K tuning, dislocation result, peer valuation, portfolio optimization, broker action, or capital authority.

Owned implementation and freeze artifacts:

- `research/asymmetric_opportunity_v1/__init__.py`
- `research/asymmetric_opportunity_v1/orthogonalization.py`
- `scripts/ao_k0a_orthogonal_basis_preflight.py`
- `tests/asymmetric_opportunity_v1/test_orthogonalization_contract.py`
- `docs/architecture/orthogonalization_contract_v1.md`
- `docs/architecture/ao_k0a_orthogonal_basis_preflight_v1.json`
- `docs/phase_brief/ao_k0a_orthogonal_basis_preflight_20260811.md`
- current-truth alignment packets and docs-as-code notes/decision/lessons
- this SAW report

Historical AO-K0 constitution bytes remain evidence and were not rewritten retroactively; an explicit active amendment marks conflicting separate-denominator, raw-QxM and coverage-failure semantics as superseded.

## Acceptance checks

| Check | Result | Evidence |
| --- | --- | --- |
| CHK-01 — Immutable denominator and no coverage gate | PASS | denominator=`PREBREAKOUT_US_PRIMARY_COMMON_DATE_LOCAL_V1`; `coverage_pass_fail_gate=FORBIDDEN`; missingness row deletion=`0` |
| CHK-02 — Persistent basis-status / arm-specific ABSTENTION | PASS | `ELIGIBLE_COMPLETE / Q_UNOBSERVED / M_WARMUP / M_MISSING_HISTORY / Q_AND_M_MISSING`; Q keeps Q-only observability; residual/joint arms require Q&M |
| CHK-03 — Orthogonal rank geometry | PASS | Q ranks on all Q-observed W3; Q/M re-ranked on Q∩M; within-date OLS with intercept; residual numerically orthogonal to intercept and Q; no temporal fit/outcome input |
| CHK-04 — Full-W3 opportunity/capital semantics | PASS | right-tail and breadth denominators are full W3; abstention risky weight=`0`; residual capital=`economic cash`; opportunity comparator=`PIT equal-weight full W3`; security/peer return imputation and observed-subset renormalization forbidden |
| CHK-05 — First-principles source boundary | PASS | implementation reads immutable W3 + admitted S0 + exact W3 market only; no transient/test feature artifact path; exact-listing 60-session M history; S0 admission/quarantine reused for Q source state |
| CHK-06 — Deterministic source preflight | PASS | `310329` pre-W6 weekly rows; matrix SHA-256=`bd36a6305f38ff68c57f6ccfb9d3481be6fd42d2288128ef9ec3eb3cc12df5cf`; replay reproduced exact hash; W6/outcome/provider reads=`0` |
| CHK-07 — Focused final-byte validation | PASS | orthogonalization tests=`7/7`; compile=`PASS`; machine JSON parse=`PASS`; stale active-authority sweep leaves only explicitly historical/superseded old-AO references |
| CHK-08 — Final bounded PRODUCT review | PASS | reviewId=`5a45cf70cd50a84488d0503cb5da2260cba40d2064e41283e6f687ced887fb3a`; result=`pass`; candidate digest=`5c0f6fd693e27333678d79ed9bcc719caf2e6aa4bc459d798f979d7df334018e`; evidence digest=`b6fbc5b00ad372292b444e97250455d80d978d76d940b30c470eaa3e52432248` |
| CHK-09 — Distinct mandatory SAW Reviewer A/B/C passes | FAIL / UNAVAILABLE | current tool surface exposes no three distinct strategy/runtime/data reviewer roles; PRODUCT reviewer is supplemental and is not relabeled as A/B/C |

ChecksTotal: 9
ChecksPassed: 8
ChecksFailed: 1

## PRODUCT review findings

Final bounded PRODUCT review returned `PASS` with advisory-only findings:

1. historical ~79.49% coverage is explicitly not recertified as authority and must not be treated as an accepted product result;
2. `financial_alpha_evidence=0`, so acceptance is limited to contract/preflight scope, not economic performance;
3. AO-K0B remains blocked because numeric Q and scalar `Q+M_perp` composition are not yet source-bound.

These advisories match the frozen AO-K0A stop line; none requires an AO-K0A code or contract change.

## Reviewer passes

| Pass | Role | Status | Evidence |
| --- | --- | --- | --- |
| Implementer | current execution agent | PASS | code/tests/source replay/current-truth/evidence reconciled; no forbidden result-bearing action |
| Supplemental PRODUCT | independent bounded PRODUCT reviewer | PASS | reviewId `5a45cf70cd50a84488d0503cb5da2260cba40d2064e41283e6f687ced887fb3a`; result `pass` |
| Reviewer A | strategy correctness / regression risk | UNAVAILABLE | no distinct A-role surface exposed |
| Reviewer B | runtime / operational resilience | UNAVAILABLE | no distinct B-role surface exposed |
| Reviewer C | data integrity / performance path | UNAVAILABLE | no distinct C-role surface exposed |

Ownership check: the successful PRODUCT reviewer is independent, but PRODUCT review is not substituted for mandatory A/B/C role coverage.

## Findings

| Severity | Impact | Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| High (governance closure only) | Full SAW PASS cannot be claimed without distinct Reviewer A/B/C coverage | Run independent A/B/C on the frozen AO-K0A final bytes if/when role-specific tooling is available, or obtain explicit owner review-risk acceptance | Review tooling / Owner | OPEN / BLOCKING FULL SAW PASS ONLY |
| Advisory | Historical ~79.49% cannot be recertified from the permitted first-principles source law | Keep it historical/non-authoritative; never tune observability to recover it | AO-K0A contract | CLOSED BY CONTRACT |
| Advisory | Admitted S0 does not exactly reconstruct the old Rule100 numeric-Q primitives | Do not invent/borrow Q; source-bind numeric Q before AO-K0B | AO-K0B prerequisite | OPEN / EXPECTED |
| Advisory | Scalar `Q+M_perp` composition is not specified by AO-K0A | Freeze an explicit source-bound scalar composition law before AO-K0B selection/outcome read | AO-K0B prerequisite | OPEN / EXPECTED |

No unresolved in-scope product/runtime/data defect was found by deterministic validation or PRODUCT review. The open High item is independent-review coverage only and does not alter the mechanically frozen AO-K0A contract.

## Validation / evidence

- Focused deterministic orthogonalization suite: `7/7 PASS`.
- Selected AO-K0A module compile: `PASS`.
- Machine freeze JSON parse: `PASS`.
- Source preflight replay: `PASS`, exact matrix hash reproduced.
- W3 authority mean eligible count over 346 sessions: `4822.994219653179`.
- Pre-W6 source-status matrix: `310329` rows.
- Status counts: `223367 ELIGIBLE_COMPLETE / 17767 M_MISSING_HISTORY / 30270 M_WARMUP / 36068 Q_AND_M_MISSING / 2857 Q_UNOBSERVED`.
- Rows removed due missingness: `0`.
- W6 dates consumed: `0`.
- Winner/future outcome reads: `0`.
- New provider requests: `0`.
- Final PRODUCT review: `PASS`.
- Distinct Reviewer A/B/C: unavailable on current tool surface.
- No commit or push was requested or performed.

## Scope split summary

In scope: denominator alignment, persistent abstention, source-observability matrix generation, exact-listing M history state, rank-basis separation, date-local orthogonal projection, full-W3 evaluation/capital semantics, deterministic tests, current-truth sync, and evidence hashing.

Out of scope: numeric Q redesign, scalar Q+M-perp selection composition, development winner/right-tail results, AO-K0B, W6, new provider capture, K tuning, dislocation experiment, peer valuation, portfolio optimizer, broker/capital promotion.

## Next action

Mechanically, AO-K0A is frozen. Do not reopen coverage thresholds or borrow legacy feature artifacts. The only lawful PREBREAKOUT continuation is a separately authorized AO-K0B preparation that first source-binds numeric Q and scalar Q+M-perp composition, then hash-binds exact development inputs and still-uninspected labels before one charged full-W3 result read.

SAW Verdict: BLOCK
ClosurePacket: RoundID=AO_K0A_ORTHOGONAL_BASIS_PREFLIGHT_20260811; ScopeID=AO-K0A-DENOMINATOR-ALIGNMENT-ORTHOGONAL-BASIS; ChecksTotal=9; ChecksPassed=8; ChecksFailed=1; Verdict=BLOCK; OpenRisks=Distinct_SAW_Reviewer_A_B_C_unavailable; ProductReview=PASS; MechanicalFreeze=PASS; NextAction=Preserve_AO_K0A_and_source_bind_Q_plus_composition_before_AO_K0B
ClosureValidation: PASS
SAWBlockValidation: PASS
