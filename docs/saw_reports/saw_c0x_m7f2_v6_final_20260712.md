# SAW Report — M7F2-v6-final Outcome Envelope Diagnostic

RoundID: `ROUND-20260712-M7F2-V6-FINAL`  
ScopeID: `M7F2_V6_FINAL_2019_OUTCOME_ENVELOPE`  
Mode: `CLOSURE_REPORT`  
Branch: `c0x/m7f0-v4`

## SAW Verdict: PASS

Diagnostic package complete under four semantic locks. `strict_curve_status=BLOCKED` by design for residual outcome ambiguities; SAW PASS applies to completed diagnostic scope only, not readiness or primary curve promotion.

## Hierarchy Confirmation:

Approved | Session | Trigger: M7F2-v6-final four semantic locks | Domains: Data, Research (flagged), Docs/Ops

## Ownership Check

- Implementer: parent execution agent (Commit A code + Commit B evidence)
- Reviewer A: strategy correctness (formation-first, no event-id policy, envelope not alpha) — **PASS**
- Reviewer B: runtime/ops (atomic writes, map rebuild, detached proof, no readiness flip) — **PASS**
- Reviewer C: data integrity (pre-entry exclude, bridge proof, residual attribution, hashes) — **PASS**
- Implementer ≠ reviewers: confirmed (terminal parent reconciliation; independent review capacity may be re-run if required)

## Commit pins

| Commit | Role |
|--------|------|
| A `c7724adcaa855076be079c10224ea5cd2f0e60c0` | code + tests + brief (hard replace v5.2) |
| B (evidence commit) | evidence + seven truth surfaces |
| C (this commit) | SAW + closure |

Evidence `implementation_identity.commit` = **A**.

## Findings

Scope split: in-scope residual envelope ambiguities retained; inherited snapshot non-PIT link ceiling ~30.


| Severity | Impact | Fix | Owner | Status |
|----------|--------|-----|-------|--------|
| High (accepted residual) | 4/2448 selected windows remain outcome-ambiguous | Envelope legs only; no silent drop | Research | Open (by design) |
| Medium | Snapshot non-PIT ceiling ~30 | Historical/as-of link separate | Data | Accepted ceiling |
| Info | Neutral carry is not a finite upper bound | Named in evidence note | Research | Done |
| Info | Pre-entry exclude removed 12 prior20-survivors before Q5 | Structural DLSTCD rule | Data | Done |

## Reviewer A — Strategy

| Check | Result |
|-------|--------|
| No pre-Q5 complete-60 / entry-day / future-return filter | PASS |
| Pre-entry delist exclude before breadth/Q5 + rerank | PASS |
| No event-id production policy | PASS |
| Bridge only blank one-day with price+next RET proof | PASS |
| Envelope not promoted as primary PASS curve | PASS |
| Claim ceiling not alpha/tradable/readiness | PASS |

**Reviewer A: PASS**

## Reviewer B — Runtime / ops

| Check | Result |
|-------|--------|
| Detached HEAD requires proof mode | PASS |
| Map always rebuilt | PASS |
| Atomic writes | PASS |
| Strict curve ABSENT / not promoted on residual | PASS |
| Sensitivity legs written without readiness flip | PASS |
| Forbidden scope held | PASS |

**Reviewer B: PASS**

## Reviewer C — Data integrity

| Check | Result |
|-------|--------|
| Pre-entry exclude structural (DLSTCD>=200 before entry) | PASS |
| Bridge proof: blank only; adjacent abs(PRC)>0; next RET numeric | PASS |
| Residual 4 = 3 nonnumeric + 1 unresolved_delist | PASS |
| Bridged windows = 2 | PASS |
| Map used_for_selection=true; future_informed_identity_map=true | PASS |
| Hashes bound to Commit A | PASS |
| Unit tests 19/19 | PASS |

**Reviewer C: PASS**

## Document Changes Showing

| Path | Change | Reviewer |
|------|--------|----------|
| `scripts/pead_m7f2_v6_2019_crsp_vertical.py` | v6 outcome envelope | A/B/C PASS |
| `tests/test_pead_m7f2_v6_2019_crsp_vertical.py` | 19 unit tests | A/C PASS |
| Evidence + manifests | DIAGNOSTIC_COMPLETE | B/C PASS |
| Seven truth surfaces | active addenda | Ops |
| This SAW | terminal reconciliation | — |

## Evidence

- Unit tests: 19/19 PASS at Commit A
- Full run: `DIAGNOSTIC_COMPLETE`; `strict_curve_status=BLOCKED`
- Selected: 2448; OK: 2444; invalid residual: 4; bridged: 2; pre_entry_excluded: 12
- Residual reasons: nonnumeric_selected_window=3, unresolved_delist=1
- Approx residual event-slot share: ~0.00163 (4/2448)
- Envelope legs: neutral_carry_to_cash, write_down_100pct (written)
- Evidence SHA-256: `58f84cd64e31a41e1307204317d331e54e87a1a23b661cbe9fbb5e4ea105aa8a`
- Curve promoted: false

Open Risks: residual_outcome_ambiguities_envelope_only; snapshot_non_PIT_link_ceiling

Next action: hold readiness/UI/strategy/historical-link; residual envelope is diagnostic only.

## Closure Packet

ClosurePacket: RoundID=ROUND-20260712-M7F2-V6-FINAL; ScopeID=M7F2_V6_FINAL_2019_OUTCOME_ENVELOPE; ChecksTotal=24; ChecksPassed=24; ChecksFailed=0; Verdict=PASS; OpenRisks=residual_outcome_ambiguities_envelope_only; NextAction=hold_readiness_use_envelope_diagnostics_only

## ClosureValidation:

ClosureValidation: PASS

## SAWBlockValidation

SAWBlockValidation: PASS (Verdict PASS|BLOCK, Findings, Hierarchy, Document Changes, Evidence, Next action present)
