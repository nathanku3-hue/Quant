# OK-SBI-0 Release Hardening v1.2

**Slice:** `OK-SBI-0` / `AO-K0B-D`  
**Date:** 2026-08-11  
**Companion science doc:** `docs/architecture/ok_sbi_0_sparse_basis_identification_v1_2.md`  
**State:** `S0_DESIGN_LOCKED_RELEASE_BLOCKED`

## Machine law

```text
runnable_evaluation = (blocked_field_count == 0)
```

Any of the following tokens in a required release field forbids S0→S1:

```text
BLOCKED_UNSET | TBD | NULL | PLACEHOLDER | UNHASHED | UNLANDED
```

Do **not** invent owner-unapproved numbers. Leave `BLOCKED_UNSET` and list it.

## Required numeric / hash gates

```text
K_t schedule
right-tail definition Q_CLOCK
right-tail definition M_CLOCK
catastrophe definition Q_CLOCK
catastrophe definition M_CLOCK
execution lag
cost law
delta_economic
epsilon_catastrophe
coverage tolerances
confidence level
temporal block definition
stability rule
multiple-testing method
minimum effective episodes
random seed/repetition law
all code/source/contract/denominator hashes once sealed
Q_CLOCK_LABEL_PACK sha256 (fully sealed)
M_CLOCK_LABEL_PACK sha256 (fully sealed)
q_source_binding_hash
```

## Dual label packs (seal ≠ open)

```text
Q_CLOCK_LABEL_PACK
M_CLOCK_LABEL_PACK
```

Each pack binds: horizon(s), target functional, right-tail cut, catastrophe cut, maturity cutoff, eligible decision-date list, row-key set, label-source receipt, SHA-256.

Sealing does **not** authorize outcome inspection for science iteration.

## Claim receipt schema (mandatory tags)

Every future numeric claim must carry at least:

```text
claim_id, slice_id, evaluation_job_id, result_receipt_sha256
ledger_id, clock_id, arm_id, comparator_arm_id, metric_id
population_scope, population_sha256
applicability_scope, status_stratum
K_schedule_id, label_pack_sha256
numerator, denominator, estimate
uncertainty_method, confidence_interval
claim_authority
```

Canonical machine schema: `docs/context/e2e_evidence/ok_sbi_0_claim_receipt_schema_v1_2.json`

## Review bar

| Transition | Minimum review |
|---|---|
| S0→S1 | mechanical pre-open PASS + all hashes replay + PRODUCT_PREOPEN PASS + blockers zero |
| S1→S2 | owner/CRO signed carve-out `OK-SBI-0-DEV-OPEN-1`; SAW may be UNAVAILABLE |
| S2→S3 RESEARCH_ONLY | deterministic result receipt + PRODUCT_RESULT PASS; SAW_UNAVAILABLE recorded as coverage-limited |
| S3→S4 CANDIDATE | full SAW A/B/C or owner-approved triple independent reviews |

```text
SAW_UNAVAILABLE != research-only scientific failure
SAW_UNAVAILABLE == candidate-promotion blocker
```

## PRODUCT_PREOPEN packet (only when Steps 1–6 ready)

Must include:

```text
blocked_field_count
runnable_evaluation
Q feasibility verdict
applicability summary
status-stratum contract
arm formula hashes
C firewall allowlist
label pack hashes (sealed, unjoined)
custody commit + clean-tree proof for bound objects
```

Do **not** request outcome open in the same breath if any blocker remains.

## Carve-out (owner/CRO only)

After `blocked_field_count == 0` and PRODUCT_PREOPEN PASS, owner/CRO may sign:

```text
AUTHORIZATION_ID: OK-SBI-0-DEV-OPEN-1
```

One-shot exception only to:

```text
NEW_WINNER_OR_FUTURE_OUTCOME_OPEN
EMPIRICAL_Q_MPERP_QPLUSMPERP_RESULT
```

Self-expires on result receipt write or any hash mismatch.  
**Default S0 turn: do not draft a signed carve-out as if authorized.**

## Custody rule

Sandbox/chat drafts are **not** authority until:

```text
landed + tracked + commit-bound + hash replay PASS
```

## Forbidden this turn

```text
outcome join / label inspection for iteration
empirical Q / M / M_perp / composite results
cross-horizon leaderboard / overall winner
W6 / providers / K tuning / capital / production
second Q redesign after one amendment
silent field bridges
A5 treated as presumed scientific winner
```
