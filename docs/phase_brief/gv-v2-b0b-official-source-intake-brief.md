# GV-V2-B0B-OFFICIAL-SOURCE-INTAKE — Controlling Brief (REVISE_AND_GO + B0B-R1)

**Status:** ACTIVE PRODUCT GATE — REPAIR_CURRENT_SLICE (B0B-R1)  
**Base:** main `2cd3e858…` · B0A banked head `79c309b` · do **not** merge `21fa4de` un-repaired  
**Audit:** REVISE_AND_GO accepted custody; REPAIR_CURRENT_SLICE for authority/PIT/claim/product  
**Score / stage / observed (locked):** `39` / `CERTIFIED_SINGLE_DECISION_OPERABLE` / `0`

---

## B0B-R1 — mandatory repair (before merge)

Preserve package + pre-read authorization. Do **not** refetch SEC objects, change accession, reopen B0A, or start B0C.

1. **Complete-chain verification** — every boundary recomputes domain hash before consuming semantic fields; stale/tampered claim fields raise integrity errors; adapter loads verified result only.
2. **Source-derived PIT** — parse complete submission header + accession index; equalize auth ↔ header ↔ index ↔ package ↔ source.
3. **Evidence-dimension claim rule** — derive CLAIM_INSUFFICIENT from independent-corroboration/physical-telemetry FAIL; no hardcoded outcome without dimensions.
4. **No B0B ADVANCE path** — delete SUFFICIENT→ADVANCE; positive path belongs to B0C.
5. **Dashboard fail-closed** — missing/invalid current authority → `st.error` + `st.caption` + **return** (no result tables).
6. **Active-gate presentation** — caption/boundary tests name B0B; static adapter import expects verified B0B loader.

### Revised post-close sequence (audit recut)

```text
B0B-R1 authority repair
→ merge and bank first official-source intake
→ GV-V2-B0C-INDEPENDENT-SOURCE-RECONCILIATION
→ first valid independent comparison on that multi-source case
→ prospective paper economics
→ replication
```

**Revoked:** immediate independent human comparison on the one-source HOLD case (G08 failure mode risk).

---

## Product vertical (sole job)

```text
official external bytes
→ relational source authority
→ honest admission
→ separate claim evaluation
→ explicit research decision
→ certified portfolio consequence
```

Authority chain layers remain distinct:

| Layer | Artifact | Proves | Does not prove |
|---|---|---|---|
| Authorization | `access_authorization.json` | pre-read scope | admission or receipt |
| Retrieval | `package_manifest.json` (or receipt bound into it) | when/how bytes arrived | claim truth |
| Custody | three exact objects + relational binds | immutable package identity | multi-source corroboration |
| Admission | `admission_result.json` (+ certificate if earned) | package may enter decision evidence | ADVANCE |
| Claim eval | `claim_evaluation.json` | research-triage sufficiency | thesis truth / investability |
| Portfolio | DecisionEnvelope → book → cert → current | paper action | capital authority |

B0A remains immutable banked substrate.

---

## Mandatory delta 1 — pre-read authorization (remote before fetch)

Before the first SEC request, remotely retain an **authorization-only** commit or annotated tag that binds:

```text
accession, CIK, form, purpose,
permitted uses, forbidden uses,
accountable authorizer, expiry/one-shot boundary,
claim ceiling
```

Sequence:

```text
authorization object (remote)
→ SEC retrieval
→ package receipt
→ implementation
```

Forbidden: create authorization retrospectively in the same commit as downloaded package bytes.

This is the only extra custody step. Not an authorization framework.

Path: `data/gv_v2_b0b/mu_0000723125-26-000015/access_authorization.json`

---

## Mandatory delta 2 — authorization time ≠ receipt time

```text
access_authorization.json
  authorization_recorded_at   # pre-read wall time
  retrieval_or_receipt_time = null

package_manifest.json
  retrieved_at
  retrieval_method
  source_locator (per object)
  response_byte_length / response_sha256 (per object)
```

Authority ordering:

```text
authorization_recorded_at < retrieved_at
```

Tests reject reversed or equal ordering when exact ordering is required.

---

## Mandatory delta 3 — exact package objects (no equivalents)

Exactly three objects (no “archive or equivalent”):

```text
0000723125-26-000015-index.htm
0000723125-26-000015.txt
mu-20260528.htm
```

Official locators (SEC EDGAR):

```text
https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/0000723125-26-000015-index.htm
https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/0000723125-26-000015.txt
https://www.sec.gov/Archives/edgar/data/723125/000072312526000015/mu-20260528.htm
```

Each object binds:

```text
official SEC locator
accession
object role
sha256
byte_length
retrieved_at
```

Evidence deduplication (non-negotiable):

```text
source_family_id = SEC:0000723125-26-000015
independent_source_count = 1
```

Index, primary, and complete submission are **custody redundancy**, not three corroborators. Claim evaluation must not count them as independent sources.

---

## Mandatory delta 4 — narrow claim outcomes

Claim evaluation outcomes:

```text
SUFFICIENT_FOR_RESEARCH_TRIAGE
CLAIM_INSUFFICIENT
CLAIM_CONTRADICTED
NOT_EVALUABLE
```

Research mapping:

```text
ADMITTED + SUFFICIENT_FOR_RESEARCH_TRIAGE → may ADVANCE_TO_FULL_RESEARCH
ADMITTED + CLAIM_INSUFFICIENT             → HOLD_FOR_EVIDENCE
ADMITTED + CLAIM_CONTRADICTED             → REJECT_THESIS
BLOCKED or NOT_EVALUABLE                  → HOLD_FOR_EVIDENCE
```

`SUFFICIENT_FOR_RESEARCH_TRIAGE` means only that the official filing contains enough relevant evidence to justify deeper research. It does **not** mean: thesis true, physical supply independently identified, issuer claims corroborated, investment justified, or a position may open.

Every extracted statement binds:

```text
source object hash
document or byte locator
section or element locator
exact excerpt hash
statement class ∈ {
  FINANCIAL_FACT,
  CONTRACTUAL_DISCLOSURE,
  ISSUER_ASSERTION,
  FORWARD_LOOKING_STATEMENT,
  RISK_DISCLOSURE
}
```

---

## Contradiction semantics (B0B only; B0A untouched)

Explicit enum (not nullable bool):

```text
PASS | FAIL | NOT_EVALUATED
```

```text
facts absent   → NOT_EVALUATED
facts conflict → FAIL + CONTRADICTORY_INDISPENSABLE_EVIDENCE
facts cohere   → PASS with non-vacuous evidence
```

---

## Portfolio semantics

```text
ADMITTED ≠ claim support
ADMITTED ≠ ADVANCE
ADVANCE ≠ portfolio position
```

All B0B research outcomes map to paper `NO_POSITION` (no sizing / capital authority).

Certified result binds both:

```text
admission_hash
claim_evaluation_hash
```

`DecisionEnvelope.rationale_ref` resolves to claim evaluation and transitively binds admission certificate or block — not merely the source package.

---

## Pinned package identity

| Field | Value |
|---|---|
| Issuer | Micron Technology, Inc. |
| CIK | 0000723125 |
| Form | 10-Q |
| Accession | 0000723125-26-000015 |
| Period ended | 2026-05-28 |
| Accepted | 2026-06-24 18:59:46 |
| Filed | 2026-06-25 |
| Primary | mu-20260528.htm |
| Submission | 0000723125-26-000015.txt |
| Index | 0000723125-26-000015-index.htm |
| Module | G_supply |
| Classification | GV-V2-B0B-OFFICIAL-SOURCE-INTAKE |

One issuer source; not independent corroboration.

---

## Execution gates

### B0B-0 — authority

1. Clean worktree from `2cd3e858…`
2. Branch `codex/gv-v2-b0b-official-source-intake`
3. Remotely retain authorization-only commit/tag
4. No product code required before this point

### B0B-1 — exact package

Fetch only the three named objects. Bank immutable bytes + relational package manifest.  
Do not fetch XBRL linkbases, exhibits, IR material, prices, providers, or a second filing.

### B0B-2 — one product vertical

```text
authorization → receipt → package_manifest → source_manifest
→ ADMITTED | BLOCKED
→ separate claim evaluation
→ research action
→ DecisionEnvelope → PortfolioBook → Fs0Certification
→ atomic current publication → visible operator result
```

### B0B-3 — ship

Focused tests → product suite → protocol freeze → Ubuntu/Windows parity → narrow audit → merge → truth cutover → **stop**.

---

## Metrics

| Measure | Now | After valid B0B close |
|---|---:|---:|
| SHIPPED_PRODUCT_SCORE | 39 | 39 (no uplift) |
| FUNCTIONAL_STAGE | CERTIFIED_SINGLE_DECISION_OPERABLE | unchanged |
| OBSERVED_COMPARISON_COUNT | 0 | 0 |
| Local abstention verticals | 1 | 1 |
| External source packages processed | 0 | 1 |
| Admission certificates earned | 0 | 1 if ADMITTED else 0 |

---

## Post-B0B (precommitted, not this PR)

- Package admitted (any research action): bank B0B → first valid independent comparison on this fresh real case
- Package blocked by implementation/custody defect: repair narrowly on same accession
- ADMITTED + CLAIM_INSUFFICIENT + HOLD + NO_POSITION is a valid B0B close

---

## Closed / forbidden this round

G08 Attempt-2 as product gate · FS1 · providers platform · PEAD · optimizer · rankings · broker · alpha · score uplift · live capital · generic evidence platform · reopen B0A · multi-source fabrication · equivalent package substitution
